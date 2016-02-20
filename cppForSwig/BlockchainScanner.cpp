////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BlockchainScanner.h"
#include "log.h"

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::scan(uint32_t scanFrom)
{
   //sanity check
   auto topBlock = blockchain_->top();
   if (topBlock.getBlockHeight() < scanFrom)
   {
      LOGWARN << "tried to scan the chain from a height beyond current top,"
         " aborting";
      return;
   }

   preloadUtxos();

   //lambdas
   auto readBlockDataLambda = [&](shared_ptr<BlockDataBatch> batch)
   { readBlockData(batch); };

   auto scanBlockDataLambda = [&](shared_ptr<BlockDataBatch> batch)
   { scanBlockData(batch); };

   auto writeBlockDataLambda = [&](
      shared_future<shared_ptr<BatchLink>> batchLink)
   { writeBlockData(batchLink); };

   auto startHeight = scanFrom;
   unsigned endHeight = 0;

   //start write thread
   shared_ptr<promise<shared_ptr<BatchLink>>> batchLinkPromise = 
      make_shared<promise<shared_ptr<BatchLink>>>();
   thread writeThreadID;
   
   {
      shared_future<shared_ptr<BatchLink>> batchLinkFuture;
      batchLinkFuture = batchLinkPromise->get_future();

      writeThreadID = thread(writeBlockDataLambda, batchLinkFuture);
   }

   //loop until there are no more blocks available
   try
   {
      while (startHeight <= topBlock.getBlockHeight())
      {
         //figure out how many blocks to pull for this batch
         //batches try to grab up nBlockFilesPerBatch_ worth of block data
         unsigned targetHeight = 0;
         try
         {
            BlockHeader* currentHeader =
               &(blockchain_->getHeaderByHeight(startHeight));
            auto currentBlkFileNum = currentHeader->getBlockFileNum();

            auto targetBlkFileNum = currentBlkFileNum + nBlockFilesPerBatch_;
            targetHeight = startHeight;

            while (currentHeader->getBlockFileNum() < targetBlkFileNum)
               currentHeader = &(blockchain_->getHeaderByHeight(++targetHeight));
         }
         catch (range_error& e)
         {
            //if getHeaderByHeight throws before targetHeight is topBlock's height,
            //something went wrong. Otherwise we just hit the end of the chain.
            if (targetHeight < topBlock.getBlockHeight())
               throw e;
            else
               targetHeight = topBlock.getBlockHeight();
         }

         endHeight = targetHeight;

         //start batch reader threads
         vector<thread> tIDs;
         vector<shared_ptr<BlockDataBatch>> batchVec;

         for (unsigned i = 0; i < totalThreadCount_; i++)
         {
            shared_ptr<BlockDataBatch> batch
               = make_shared<BlockDataBatch>(startHeight + i, endHeight);
            batchVec.push_back(batch);

            auto tID = thread(readBlockDataLambda, batch);
            if (tID.joinable())
               tID.detach();
         }

         //start batch scanner threads
         vector<unique_lock<mutex>> lockVec;
         for (unsigned i = 0; i < totalThreadCount_; i++)
         {
            //lock each batch mutex before start scan thread
            lockVec.push_back(unique_lock<mutex>(batchVec[i]->parseTxinMutex_));
            tIDs.push_back(thread(scanBlockDataLambda, batchVec[i]));
         }

         //wait for utxo scan to complete
         for (unsigned i = 0; i < totalThreadCount_; i++)
         {
            auto utxoScanFlag = batchVec[i]->doneScanningUtxos_;
            utxoScanFlag.get();
         }

         //update utxoMap_
         for (auto& batch : batchVec)
         {
            for (auto& txidMap : batch->utxos_)
            {
               utxoMap_[txidMap.first].insert(
                  txidMap.second.begin(), txidMap.second.end());
            }
         }

         //signal txin scan by releasing all mutexes
         lockVec.clear();

         //wait until txins are scanned
         for (auto& tID : tIDs)
         {
            if (tID.joinable())
               tID.join();
         }

         //push scanned batch to write thread
         accumulateDataBeforeBatchWrite(batchVec);
         auto currentPromise = batchLinkPromise;
         batchLinkPromise = make_shared<promise<shared_ptr<BatchLink>>>();
         
         shared_ptr<BatchLink> batchLinkPtr = make_shared<BatchLink>();
         batchLinkPtr->topScannedBlockHash_ = topScannedBlockHash_;
         batchLinkPtr->batchVec_ = batchVec;
         batchLinkPtr->next_ = batchLinkPromise->get_future();

         currentPromise->set_value(batchLinkPtr);
         

         //TODO: add a mechanism to wait on the write thread so as to not
         //exhaust RAM with batches queued for writing

         //increment startBlock
         startHeight = endHeight + 1;
      }
   }
   catch (range_error&)
   {
      LOGERR << "failed to grab block data starting height: " << startHeight;
      if (startHeight == scanFrom)
         LOGERR << "no block data was scanned";
   }

   //push termination batch to write thread and wait till it exits
   batchLinkPromise->set_value(nullptr);

   if (writeThreadID.joinable())
      writeThreadID.join();
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::readBlockData(shared_ptr<BlockDataBatch> batch)
{
   unique_lock<mutex> parseTxoutLock(batch->parseTxOutMutex_);
   
   auto currentBlock = batch->start_;

   mutex mu;
   unique_lock<mutex> lock(mu);

   //setup promise
   shared_ptr<promise<BlockDataLink>> blockPromisePtr = 
      make_shared<promise<BlockDataLink>>();
   batch->first_ = blockPromisePtr->get_future();

   parseTxoutLock.unlock();

   while (currentBlock <= batch->end_)
   {
      //stay within nBlocksLookAhead of the scan thread
      while (currentBlock > 
         batch->highestProcessedHeight_.load(memory_order_relaxed) +
         nBlocksLookAhead_ * totalThreadCount_)
      {
         batch->readThreadCV_.wait(lock);
      }

      //TODO: encapsulate in try block to catch deser errors and signal pull thread
      //termination before exiting scope. cant have the scan thread hanging if this
      //one fails. Also update batch->end_ if we didn't go as far as that block height

      //grab block file map
      BlockHeader* blockheader = nullptr;
      try
      {
         blockheader = &blockchain_->getHeaderByHeight(currentBlock);
      }
      catch(range_error&)
      {
         break;
      }

      auto filenum = blockheader->getBlockFileNum();
      
      auto mapIter = batch->fileMaps_.find(filenum);
      if (mapIter == batch->fileMaps_.end())
      {
         //we haven't grabbed that file map yet
         auto insertPair = batch->fileMaps_.insert(
            make_pair(filenum, move(blockDataLoader_.get(filenum, true))));

         mapIter = insertPair.first;
      }

      auto filemap = mapIter->second.get();

      //find block and deserialize it
      BlockDataLink blockfuture;
      blockfuture.blockdata_.deserialize(
         filemap->getPtr() + blockheader->getOffset(), 
         blockheader->getBlockSize(),
         blockheader, false);

      //prepare next iteration
      auto currentPromisePtr = blockPromisePtr;
      blockPromisePtr =
         make_shared<promise<BlockDataLink>>();
      blockfuture.next_ = blockPromisePtr->get_future();

      //fill promise
      currentPromisePtr->set_value(blockfuture);

      currentBlock += totalThreadCount_;
   }

   //we're done, fill the block future with the termination block
   blockPromisePtr->set_value(BlockDataLink());
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::scanBlockData(shared_ptr<BlockDataBatch> batch)
{
   //parser lambda
   auto blockDataLoop = [&](function<void(const BlockData&)> callback)
   {
      auto blockFuture = batch->first_;
      while (1)
      {
         if (!blockFuture.valid())
         {
            LOGWARN << "exited scanBlockData loop on invalid future";
            break;
         }

         auto blocklink = blockFuture.get();

         if (!blocklink.blockdata_.isInitialized())
            break;

         //callback
         callback(blocklink.blockdata_);

         blockFuture = blocklink.next_;
      }
   };

   //txout lambda
   auto txoutParser = [&](const BlockData& blockdata)->void
   {
      //TODO: flag isMultisig

      const BlockHeader* header = blockdata.header();

      //update processed height
      auto topHeight = header->getBlockHeight();
      batch->highestProcessedHeight_.store(topHeight, memory_order_relaxed);

      auto& txns = blockdata.getTxns();
      for (unsigned i = 0; i < txns.size(); i++)
      {
         const BCTX& txn = *(txns[i].get());
         for (unsigned y = 0; y < txn.txouts_.size(); y++)
         {
            auto& txout = txn.txouts_[y];

            BinaryRefReader brr(txn.data_ + txout.first);
            brr.advance(8);
            unsigned scriptSize = (unsigned)brr.get_var_int();
            auto&& scrAddr = BtcUtils::getTxOutScrAddr(
               brr.get_BinaryDataRef(scriptSize));

            if (!scrAddrFilter_->hasScrAddress(scrAddr))
               continue;

            //if we got this far, this txout is ours
            //get tx hash
            auto& txHash = txn.getHash();

            //construct StoredTxOut
            StoredTxOut stxo;
            stxo.dataCopy_ = BinaryData(
               txn.data_ + txout.first, txout.second);
            stxo.parentHash_ = txHash;
            stxo.blockHeight_ = header->getBlockHeight();
            stxo.duplicateID_ = header->getDuplicateID();
            stxo.txIndex_ = i;
            stxo.txOutIndex_ = y;
            stxo.scrAddr_ = scrAddr;
            stxo.spentness_ = TXOUT_UNSPENT;
            stxo.parentTxOutCount_ = txn.txouts_.size();
            stxo.isCoinbase_ = txn.isCoinbase_;
            auto value = stxo.getValue();

            auto&& hgtx = DBUtils::heightAndDupToHgtx(
               stxo.blockHeight_, stxo.duplicateID_);
            
            auto&& txioKey = DBUtils::getBlkDataKeyNoPrefix(
               stxo.blockHeight_, stxo.duplicateID_,
               i, y);

            //update utxos_
            auto& stxoHashMap = batch->utxos_[txHash];
            stxoHashMap.insert(make_pair(y, move(stxo)));

            //update ssh_
            auto& ssh = batch->ssh_[scrAddr];
            auto& subssh = ssh.subHistMap_[hgtx];
            
            //deal with txio count in subssh at serialization
            TxIOPair txio;
            txio.setValue(value);
            txio.setTxOut(txioKey);
            txio.setFromCoinbase(txn.isCoinbase_);
            subssh.txioMap_.insert(make_pair(txioKey, txio));
         }
      }

      batch->readThreadCV_.notify_all();
   };

   //txin lambda
   auto txinParser = [&](const BlockData& blockdata)->void
   {
      const BlockHeader* header = blockdata.header();
      auto& txns = blockdata.getTxns();

      for (unsigned i = 0; i < txns.size(); i++)
      {
         const BCTX& txn = *(txns[i].get());

         for (unsigned y = 0; y < txn.txins_.size(); y++)
         {
            auto& txin = txn.txins_[y];
            BinaryDataRef outHash(
               txn.data_ + txin.first, 32);

            auto utxoIter = utxoMap_.find(outHash);
            if (utxoIter == utxoMap_.end())
               continue;

            unsigned txOutId = READ_UINT32_LE(
               txn.data_ + txin.first + 32);

            auto idIter = utxoIter->second.find(txOutId);
            if (idIter == utxoIter->second.end())
               continue;

            //if we got this far, this txins consumes one of our utxos

            //create spent txout
            auto&& hgtx = DBUtils::getBlkDataKeyNoPrefix(
               header->getBlockHeight(), header->getDuplicateID());

            auto&& txinkey = DBUtils::getBlkDataKeyNoPrefix(
               header->getBlockHeight(), header->getDuplicateID(),
               i, y);

            StoredTxOut stxo = idIter->second;
            stxo.spentness_ = TXOUT_SPENT;
            stxo.spentByTxInKey_ = txinkey;

            //add to ssh_
            auto& ssh = batch->ssh_[stxo.getScrAddress()];
            auto& subssh = ssh.subHistMap_[hgtx];

            //deal with txio count in subssh at serialization
            TxIOPair txio;
            auto&& txoutkey = stxo.getDBKey(false);
            txio.setTxOut(txoutkey);
            txio.setTxIn(txinkey);
            txio.setValue(stxo.getValue());
            subssh.txioMap_[txoutkey] = move(txio);
            
            //add to spentTxOuts_
            batch->spentTxOuts_.push_back(move(stxo));
         }
      }
   };

   //txout loop
   unique_lock<mutex> txoutLock(batch->parseTxOutMutex_);
   blockDataLoop(txoutParser);

   //done with txouts, fill the future flag and wait on the mutex 
   //to move to txins processing
   batch->flagUtxoScanDone();
   unique_lock<mutex> txinLock(batch->parseTxinMutex_);

   //txins loop
   blockDataLoop(txinParser);
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::accumulateDataBeforeBatchWrite(
   vector<shared_ptr<BlockDataBatch>>& batchVec)
{
   //build list of all spent txouts
   vector<StoredTxOut> spentTxOuts;
   
   for (auto& batch : batchVec)
   {
      spentTxOuts.insert(spentTxOuts.end(),
         batch->spentTxOuts_.begin(), batch->spentTxOuts_.end());
   }

   //prune spent txouts from utxoMap_
   for (auto& spentTxOut : spentTxOuts)
   {
      auto utxoIter = utxoMap_.find(spentTxOut.parentHash_);
      if (utxoIter == utxoMap_.end())
         continue;

      auto idIter = utxoIter->second.find(spentTxOut.txOutIndex_);
      if (idIter == utxoIter->second.end())
         continue;

      utxoIter->second.erase(idIter);
      if (utxoIter->second.size() == 0)
         utxoMap_.erase(utxoIter);
   }

   //figure out top scanned block hash
   unsigned topScannedBlockHeight = 0;
   for (auto& batch : batchVec)
   {
      if (batch->end_ > topScannedBlockHeight)
         topScannedBlockHeight = batch->end_;
   }

   auto& header = blockchain_->getHeaderByHeight(topScannedBlockHeight);
   topScannedBlockHash_ = header.getThisHash();
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::writeBlockData(
   shared_future<shared_ptr<BatchLink>> batchFuture)
{
   auto writeHintsLambda = 
      [&](const vector<shared_ptr<BlockDataBatch>>& batchVec)->void
   { processAndCommitTxHints(batchVec); };

   while (1)
   {
      if (!batchFuture.valid())
      {
         LOGWARN << "exited writeBlockDataLoop on invalid future";
         break;
      }

      auto batchLink = batchFuture.get();

      //check for termination marker
      if (batchLink == nullptr)
         break;

      //start txhint writer thread
      thread writeHintsThreadId = thread(writeHintsLambda, batchLink->batchVec_);

      auto& topheader = 
         blockchain_->getHeaderByHash(batchLink->topScannedBlockHash_);
      auto topHeight = topheader.getBlockHeight();
      
      //serialize data
      map<BinaryData, BinaryWriter> serializedSubSSH;
      map<BinaryData, BinaryWriter> serializedStxo;
      map<BinaryData, BinaryWriter> serializedTxHints;
      map<BinaryData, StoredTxHints> txHints;

      {
         for (auto& batchPtr : batchLink->batchVec_)
         {
            for (auto& ssh : batchPtr->ssh_)
            {
               for (auto& subssh : ssh.second.subHistMap_)
               {
                  //TODO: modify subssh serialization to fit our needs

                  BinaryWriter subsshkey;
                  subsshkey.put_uint8_t(DB_PREFIX_SCRIPT);
                  subsshkey.put_BinaryData(ssh.first);
                  subsshkey.put_BinaryData(subssh.first);

                  auto& bw = serializedSubSSH[subsshkey.getDataRef()];
                  subssh.second.serializeDBValue(
                     bw, db_, ARMORY_DB_BARE, DB_PRUNE_NONE);
               }
            }

            for (auto& utxomap : batchPtr->utxos_)
            {
               auto&& txHashPrefix = utxomap.first.getSliceCopy(0, 4);
               StoredTxHints& stxh = txHints[txHashPrefix];
               if (stxh.txHashPrefix_.getSize() == 0)
                  stxh.txHashPrefix_ = txHashPrefix;


               for (auto& utxo : utxomap.second)
               {
                  stxh.dbKeyList_.push_back(utxo.second.getDBKeyOfParentTx());

                  auto& bw = serializedStxo[utxo.second.getDBKey()];
                  utxo.second.serializeDBValue(
                     bw, ARMORY_DB_BARE, DB_PRUNE_NONE, true);
               }
               
               stxh.preferredDBKey_ = stxh.dbKeyList_.front();
            }
         }
      }

      //we've serialized utxos, now let's do another pass for spent txouts
      //to make sure they overwrite utxos that were found and spent within
      //the same batch
      for (auto& batchPtr : batchLink->batchVec_)
      {
         for (auto& stxo : batchPtr->spentTxOuts_)
         {
            auto& bw = serializedStxo[stxo.getDBKey()];
            if (bw.getSize() > 0)
               bw.reset();
            stxo.serializeDBValue(
               bw, ARMORY_DB_BARE, DB_PRUNE_NONE, true);
         }
      }

      //write data
      {
         //txouts
         LMDBEnv::Transaction tx;
         db_->beginDBTransaction(&tx, STXO, LMDB::ReadWrite);

         for (auto& stxo : serializedStxo)
         { 
            //TODO: dont rewrite utxos, check if they are already in DB first
            db_->putValue(STXO,
               stxo.first.getRef(),
               stxo.second.getDataRef());
         }
      }

      {
         //subssh
         LMDBEnv::Transaction tx;
         db_->beginDBTransaction(&tx, SSH, LMDB::ReadWrite);

         for (auto& subssh : serializedSubSSH)
         {
            db_->putValue(
               SSH,
               subssh.first.getRef(),
               subssh.second.getDataRef());
         }
      }

      //wait on writeHintsThreadId
      if (writeHintsThreadId.joinable())
         writeHintsThreadId.join();

      LOGINFO << "scanned from height #" << batchLink->batchVec_[0]->start_
         << " to #" << batchLink->batchVec_[0]->end_;

      batchFuture = batchLink->next_;
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::processAndCommitTxHints(
   const vector<shared_ptr<BlockDataBatch>>& batchVec)
{
   map<BinaryData, StoredTxHints> txHints;

   {
      map<BinaryData, BinaryWriter> countAndHash;

      {
         LMDBEnv::Transaction hintdbtx;
         db_->beginDBTransaction(&hintdbtx, TXHINTS, LMDB::ReadOnly);

         for (auto& batchPtr : batchVec)
         {
            for (auto& utxomap : batchPtr->utxos_)
            {
               auto&& txHashPrefix = utxomap.first.getSliceCopy(0, 4);
               StoredTxHints& stxh = txHints[txHashPrefix];

               //pull txHint from DB first, don't want to override 
               //existing hints
               db_->getStoredTxHints(stxh, txHashPrefix);

               for (auto& utxo : utxomap.second)
                  stxh.dbKeyList_.push_back(
                     utxo.second.getDBKeyOfParentTx(false));

               stxh.preferredDBKey_ = stxh.dbKeyList_.front();

               //count and hash
               auto& stxo = utxomap.second.begin()->second;
               auto& bw = countAndHash[stxo.getDBKeyOfParentTx(true)];
               bw.put_uint32_t(stxo.parentTxOutCount_);
               bw.put_BinaryData(utxomap.first);
            }
         }
      }

      //TODO: deal with spender txhint
      /*for (auto& batchPtr : batchVec)
      {
      for (auto& stxo : batchPtr->spentTxOuts_)
      {
      auto&& txHashPrefix = stxo.
      StoredTxHints& stxh = txHints[txHashPrefix];
      }
      }*/

      map<BinaryData, BinaryWriter> serializedHints;

      //serialize
      for (auto& txhint : txHints)
      {
         auto& bw = serializedHints[txhint.second.getDBKey()];
         txhint.second.serializeDBValue(bw);
      }

      //write
      {
         LMDBEnv::Transaction hintdbtx;
         db_->beginDBTransaction(&hintdbtx, TXHINTS, LMDB::ReadWrite);

         for (auto& txhint : serializedHints)
         {
            db_->putValue(TXHINTS,
               txhint.first.getRef(),
               txhint.second.getDataRef());
         }

         for (auto& cah : countAndHash)
         {
            db_->putValue(TXHINTS,
               cah.first.getRef(),
               cah.second.getDataRef());
         }
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::updateSSH(void)
{
   //loop over all subssh entiers in SSH db, 
   //compile balance, txio count and summary map for each address

   map<BinaryData, StoredScriptHistory> sshMap_;
   
   {
      StoredScriptHistory* sshPtr = nullptr;

      LMDBEnv::Transaction historyTx, sshTx;
      db_->beginDBTransaction(&historyTx, HISTORY, LMDB::ReadOnly);
      db_->beginDBTransaction(&sshTx, SSH, LMDB::ReadOnly);

      auto sshIter = db_->getIterator(SSH);
      sshIter.seekToFirst();

      while (sshIter.advanceAndRead())
      {
         while (sshIter.isValid())
         {
            if (sshPtr != nullptr &&
               sshIter.getKeyRef().contains(sshPtr->uniqueKey_))
               break;

            //new address
            auto&& subsshkey = sshIter.getKey();
            auto sshKey = subsshkey.getSliceRef(1, subsshkey.getSize() - 5);
            sshPtr = &sshMap_[sshKey];

            //get what's already in the db
            db_->getStoredScriptHistorySummary(*sshPtr, sshKey);
            if (sshPtr->isInitialized())
            {
               //set iterator at unscanned height
               auto hgtx = sshIter.getKeyRef().getSliceRef(-4, 4);
               auto height = DBUtils::hgtxToHeight(hgtx);
               if (sshPtr->alreadyScannedUpToBlk_ >= height)
               {
                  //this ssh has already been scanned beyond the height sshIter is at,
                  //let's set the iterator to the correct height (or the next key)
                  auto&& newKey = sshIter.getKey().getSliceCopy(0, subsshkey.getSize() - 4);
                  auto&& newHgtx = DBUtils::heightAndDupToHgtx(
                     sshPtr->alreadyScannedUpToBlk_ + 1, 0);

                  newKey.append(newHgtx);
                  sshIter.seekTo(newKey);
                  continue;
               }
            }
            else
            {
               sshPtr->uniqueKey_ = sshKey;
               break;
            }
         }

         //sanity check
         if (!sshIter.isValid())
            break;

         //deser subssh
         StoredSubHistory subssh;
         subssh.unserializeDBKey(sshIter.getKeyRef());
         
         //check dupID
         if (db_->getValidDupIDForHeight(subssh.height_) != subssh.dupID_)
            continue;

         subssh.unserializeDBValue(sshIter.getValueRef());

         for (auto& txioPair : subssh.txioMap_)
         {
            if (!txioPair.second.isMultisig())
            {
               //add up balance
               if (txioPair.second.hasTxIn())
               {
                  //check for same block fund&spend
                  auto&& keyOfOutput = txioPair.second.getDBKeyOfOutput();
                  auto&& keyOfInput = txioPair.second.getDBKeyOfInput();

                  if (keyOfOutput.startsWith(keyOfInput.getSliceRef(0, 4)))
                  {
                     //both output and input are part of the same block, skip
                     continue;
                  }

                  sshPtr->totalUnspent_ -= txioPair.second.getValue();
               }
               else
               {
                  sshPtr->totalUnspent_ += txioPair.second.getValue();
               }
            }
         }

         //txio count
         sshPtr->totalTxioCount_ += subssh.txioCount_;

         //build subssh summary
         sshPtr->subsshSummary_[subssh.height_] = subssh.txioCount_;
      }
   }
   
   //write it
   auto& topheader = blockchain_->getHeaderByHash(topScannedBlockHash_);
   auto topheight = topheader.getBlockHeight();

   LMDBEnv::Transaction putsshtx;
   db_->beginDBTransaction(&putsshtx, HISTORY, LMDB::ReadWrite);

   auto& scrAddrMap = scrAddrFilter_->getScrAddrMap();
   for (auto& scrAddr : scrAddrMap)
   {
      auto& ssh = sshMap_[scrAddr.first];

      if (!ssh.isInitialized())
      {
         ssh.uniqueKey_ = scrAddr.first;
      }

      BinaryData&& sshKey = ssh.getDBKey();
      ssh.alreadyScannedUpToBlk_ = topheight;

      BinaryWriter bw;
      ssh.serializeDBValue(bw, ARMORY_DB_BARE, DB_PRUNE_NONE);
      
      db_->putValue(HISTORY, sshKey.getRef(), bw.getDataRef());
   }

   //update sdbi
   StoredDBInfo sdbi;
   db_->getStoredDBInfo(HISTORY, sdbi);

   sdbi.topScannedBlkHash_ = topScannedBlockHash_;
   sdbi.topBlkHgt_ = topheight;

   db_->putStoredDBInfo(HISTORY, sdbi);
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::preloadUtxos()
{
   LMDBEnv::Transaction tx;
   db_->beginDBTransaction(&tx, STXO, LMDB::ReadOnly);
   auto dbIter = db_->getIterator(STXO);
   dbIter.seekToFirst();

   while (dbIter.advanceAndRead())
   {
      StoredTxOut stxo;
      stxo.unserializeDBKey(dbIter.getKeyRef());
      stxo.unserializeDBValue(dbIter.getValueRef());

      if (stxo.spentness_ == TXOUT_SPENT)
         continue;

      stxo.parentHash_ = move(db_->getTxHashForLdbKey(
         stxo.getDBKeyOfParentTx(false)));
      auto& idMap = utxoMap_[stxo.parentHash_];
      idMap.insert(make_pair(stxo.txOutIndex_, move(stxo)));
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::undo(Blockchain::ReorganizationState& reorgState)
{
   //dont undo subssh, these are skipped by dupID when loading history

   BlockHeader* blockPtr = reorgState.prevTopBlock;
   map<uint32_t, BlockFileMapPointer> fileMaps_;

   map<DB_SELECT, set<BinaryData>> keysToDelete;
   map<BinaryData, StoredScriptHistory> sshMap;
   set<BinaryData> undoSpentness; //TODO: add spentness DB

   //TODO: sanity checks on header ptrs from reorgState
   if (reorgState.prevTopBlock->getBlockHeight() <=
       reorgState.reorgBranchPoint->getBlockHeight())
      throw runtime_error("invalid reorg state");

   while (blockPtr != reorgState.reorgBranchPoint)
   {
      auto currentHeight = blockPtr->getBlockHeight();
      auto currentDupId  = blockPtr->getDuplicateID();

      //create tx to pull subssh data
      LMDBEnv::Transaction sshTx;
      db_->beginDBTransaction(&sshTx, SSH, LMDB::ReadOnly);

      //grab blocks from previous top until branch point
      if (blockPtr == nullptr)
         throw runtime_error("reorg failed while tracing back to "
         "branch point");

      auto filenum = blockPtr->getBlockFileNum();
      auto fileIter = fileMaps_.find(filenum);
      if (fileIter == fileMaps_.end())
      {
         fileIter = fileMaps_.insert(make_pair(
            filenum,
            move(blockDataLoader_.get(filenum, false)))).first;
      }

      auto& filemap = fileIter->second;

      BlockData bdata;
      bdata.deserialize(filemap.get()->getPtr() + blockPtr->getOffset(),
         blockPtr->getBlockSize(), blockPtr);

      auto& txns = bdata.getTxns();
      for (unsigned i = 0; i < txns.size(); i++)
      {
         auto& txn = txns[i];

         //undo tx outs added by this block
         for (unsigned y = 0; y < txn->txouts_.size(); y++)
         {
            auto& txout = txn->txouts_[y];

            BinaryRefReader brr(txn->data_ + txout.first);
            brr.advance(8);
            unsigned scriptSize = (unsigned)brr.get_var_int();
            auto&& scrAddr = BtcUtils::getTxOutScrAddr(
               brr.get_BinaryDataRef(scriptSize));

            if (!scrAddrFilter_->hasScrAddress(scrAddr))
               continue;

            //update ssh value and txio count
            auto& ssh = sshMap[scrAddr];
            if (!ssh.isInitialized())
               db_->getStoredScriptHistorySummary(ssh, scrAddr);

            if (ssh.alreadyScannedUpToBlk_ < currentHeight)
               continue;
            
            brr.resetPosition();
            uint64_t value = brr.get_uint64_t();
            ssh.totalUnspent_ -= value;
            ssh.totalTxioCount_--;
            
            //mark stxo key for deletion
            auto&& txoutKey = DBUtils::getBlkDataKey(
               currentHeight, currentDupId,
               i, y);
            keysToDelete[STXO].insert(txoutKey);

            //decrement summary count at height, remove entry if necessary
            auto& sum = ssh.subsshSummary_[currentHeight];
            sum--;
            if (sum <= 0)
               ssh.subsshSummary_.erase(currentHeight);
         }

         //undo spends from this block
         for (unsigned y = 0; y < txn->txins_.size(); y++)
         {
            auto& txin = txn->txins_[y];

            BinaryDataRef outHash(
               txn->data_ + txin.first, 32);

            auto&& txKey = db_->getDBKeyForHash(outHash, currentDupId);
            if (txKey.getSize() != 6)
               continue;

            uint16_t txOutId = (uint16_t)READ_UINT32_LE(
               txn->data_ + txin.first + 32);
            txKey.append(WRITE_UINT16_BE(txOutId));

            StoredTxOut stxo;
            if (!db_->getStoredTxOut(stxo, txKey))
               continue;

            //update ssh value and txio count
            auto& scrAddr = stxo.getScrAddress();
            auto& ssh = sshMap[scrAddr];
            if (!ssh.isInitialized())
               db_->getStoredScriptHistorySummary(ssh, scrAddr);

            if (ssh.alreadyScannedUpToBlk_ < currentHeight)
               continue;

            ssh.totalUnspent_ += stxo.getValue();
            ssh.totalTxioCount_--;

            //mark txout key for undoing spentness
            undoSpentness.insert(txKey);

            //decrement summary count at height, remove entry if necessary
            auto& sum = ssh.subsshSummary_[currentHeight];
            sum--;
            if (sum <= 0)
               ssh.subsshSummary_.erase(currentHeight);
         }
      }

      //set blockPtr to prev block
      blockPtr = &blockchain_->getHeaderByHash(blockPtr->getPrevHashRef());
   }

   //at this point we have a map of updated ssh, as well as a 
   //set of keys to delete from the DB and spentness to undo by stxo key

   //stxo
   {
      LMDBEnv::Transaction tx;
      db_->beginDBTransaction(&tx, STXO, LMDB::ReadWrite);

      //grab stxos and revert spentness
      map<BinaryData, StoredTxOut> stxos;
      for (auto& stxoKey : undoSpentness)
      {
         auto& stxo = stxos[stxoKey];
         if (!db_->getStoredTxOut(stxo, stxoKey))
            continue;

         stxo.spentByTxInKey_.clear();
         stxo.spentness_ = TXOUT_UNSPENT;
      }

      //put updated stxos
      for (auto& stxo : stxos)
      {
         if (stxo.second.isInitialized())
            db_->putStoredTxOut(stxo.second);
      }

      //delete invalidated stxos
      auto& stxoKeysToDelete = keysToDelete[STXO];
      for (auto& key : stxoKeysToDelete)
         db_->deleteValue(STXO, key);
   }

   auto branchPointHeight = 
      reorgState.reorgBranchPoint->getBlockHeight();

   //ssh
   {
      LMDBEnv::Transaction tx;
      db_->beginDBTransaction(&tx, HISTORY, LMDB::ReadWrite);

      //go thourgh all ssh in scrAddrFilter
      auto& scrAddrMap = scrAddrFilter_->getScrAddrMap();
      for (auto& scrAddr : scrAddrMap)
      {
         auto& ssh = sshMap[scrAddr.first];
         
         //if the ssh isn't in our map, pull it from DB
         if (!ssh.isInitialized())
         {
            db_->getStoredScriptHistorySummary(ssh, scrAddr.first);
            if (ssh.uniqueKey_.getSize() == 0)
            {
               sshMap.erase(scrAddr.first);
               continue;
            }
         }

         //update alreadyScannedUpToBlk_ to branch point height
         if (ssh.alreadyScannedUpToBlk_ > branchPointHeight)
            ssh.alreadyScannedUpToBlk_ = branchPointHeight;
      }

      //write it all up
      for (auto& ssh : sshMap)
      {
         BinaryWriter bw;
         ssh.second.serializeDBValue(bw, ARMORY_DB_BARE, DB_PRUNE_NONE);
         db_->putValue(HISTORY,
            ssh.second.getDBKey().getRef(),
            bw.getDataRef());
      }

      //update HISTORY sdbi      
      StoredDBInfo sdbi;
      db_->getStoredDBInfo(HISTORY, sdbi);
      sdbi.topScannedBlkHash_ = reorgState.reorgBranchPoint->getThisHash();
      sdbi.topBlkHgt_ = branchPointHeight;
      db_->putStoredDBInfo(HISTORY, sdbi);
   }
}
