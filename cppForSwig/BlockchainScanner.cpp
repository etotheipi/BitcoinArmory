////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016-17, goatpig.                                           //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BlockchainScanner.h"
#include "log.h"

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::scan(int32_t scanFrom)
{
   scanFrom = check_merkle(scanFrom);
   if (scanFrom == INT32_MIN)
      return;

   scan_nocheck(scanFrom);
}

////////////////////////////////////////////////////////////////////////////////
int32_t BlockchainScanner::check_merkle(int32_t scanFrom)
{
   auto topBlock = blockchain_->top();

   scrAddrFilter_->updateAddressMerkleInDB();
   auto&& subsshSdbi = scrAddrFilter_->getSubSshSDBI();

   shared_ptr<BlockHeader> sdbiblock;

   //check if we need to scan anything
   try
   {
      sdbiblock =
         blockchain_->getHeaderByHash(subsshSdbi.topScannedBlkHash_);
   }
   catch (...)
   {
      sdbiblock = blockchain_->getHeaderByHeight(0);
   }

   if (sdbiblock->isMainBranch())
   {
      //this will set scanFrom to 0 before an initial scan
      if ((int)sdbiblock->getBlockHeight() > scanFrom)
         scanFrom = sdbiblock->getBlockHeight();

      if (scanFrom > (int)topBlock->getBlockHeight() || 
          scrAddrFilter_->getScrAddrMap()->size() == 0)
      {
         LOGINFO << "no history to scan";
         topScannedBlockHash_ = topBlock->getThisHash();
         return INT32_MIN;
      }
   }

   return scanFrom;
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::scan_nocheck(int32_t scanFrom)
{
   TIMER_RESTART("scan_nocheck");

   startAt_ = scanFrom;
   auto topBlock = blockchain_->top();

   preloadUtxos();

   auto scrRefMap = scrAddrFilter_->getOutScrRefMap();

   //lambdas
   auto commitLambda = [this](void)
   { writeBlockData(); };

   auto outputsLambda = [this](void)
   { processOutputs(); };

   auto inputsLambda = [this](void)
   { processInputs(); };

   //start threads
   auto commit_tID = thread(commitLambda);
   auto outputs_tID = thread(outputsLambda);
   auto inputs_tID = thread(inputsLambda);

   auto startHeight = scanFrom;
   unsigned endHeight = 0;

   vector<future<bool>> completedFutures;
   unsigned _count = 0;
   completedBatches_.store(0, memory_order_relaxed);

   //loop until there are no more blocks available
   try
   {
      unsigned firstBlockFileID = UINT32_MAX;
      unsigned targetBlockFileID = UINT32_MAX;

      while (startHeight <= topBlock->getBlockHeight())
      {
         //figure out how many blocks to pull for this batch
         //batches try to grab up nBlockFilesPerBatch_ worth of block data
         unsigned targetHeight = 0;
         size_t targetSize = BATCH_SIZE;
         size_t tallySize;
         try
         {
            shared_ptr<BlockHeader> currentHeader =
               blockchain_->getHeaderByHeight(startHeight);
            firstBlockFileID = currentHeader->getBlockFileNum();

            targetBlockFileID = 0;
            targetHeight = startHeight;

            tallySize = currentHeader->getBlockSize();

            while (tallySize < targetSize)
            {
               currentHeader = blockchain_->getHeaderByHeight(++targetHeight);
               tallySize += currentHeader->getBlockSize();

               if (currentHeader->getBlockFileNum() < firstBlockFileID)
                  firstBlockFileID = currentHeader->getBlockFileNum();

               if (currentHeader->getBlockFileNum() > targetBlockFileID)
                  targetBlockFileID = currentHeader->getBlockFileNum();
            }

         }
         catch (range_error& e)
         {
            //if getHeaderByHeight throws before targetHeight is topBlock's height,
            //something went wrong. Otherwise we just hit the end of the chain.

            if (targetHeight < topBlock->getBlockHeight())
            {
               LOGERR << e.what();
               throw e;
            }
            else
            {
               targetHeight = topBlock->getBlockHeight();
               if (targetBlockFileID < topBlock->getBlockFileNum())
                  targetBlockFileID = topBlock->getBlockFileNum();
            }
         }

         endHeight = targetHeight;

         //create batch
         auto&& batch = make_unique<ParserBatch>(
            startHeight, endHeight, 
            firstBlockFileID, targetBlockFileID,
            scrRefMap);


         completedFutures.push_back(batch->completedPromise_.get_future());
         batch->count_ = _count;
         
         //post for txout parsing
         outputQueue_.push_back(move(batch));
         if (_count - completedBatches_.load(memory_order_relaxed) >= 
            writeQueueDepth_)
         {
            try
            {
               auto futIter = completedFutures.begin() + 
                  (_count - writeQueueDepth_);
               futIter->wait();
            }
            catch (future_error &e)
            {
               LOGERR << "future error";
               throw e;
            }
         }

         ++_count;
         startHeight = endHeight + 1;
      }
   }
   catch (range_error&)
   {
      LOGERR << "failed to grab block data starting height: " << startHeight;
      if (startHeight == scanFrom)
         LOGERR << "no block data was scanned";
   }
   catch (...)
   {
      LOGWARN << "scanning halted unexpectedly";
      //let the scan terminate
   }

   //mark all queues complete
   outputQueue_.completed();

   if (outputs_tID.joinable())
      outputs_tID.join();
   
   if (inputs_tID.joinable())
      inputs_tID.join();

   if (commit_tID.joinable())
      commit_tID.join();

   topScannedBlockHash_ = topBlock->getThisHash();

   TIMER_STOP("scan_nocheck");
   if (topBlock->getBlockHeight() - scanFrom > 100)
   {
      auto timeSpent = TIMER_READ_SEC("scan_nocheck");
      LOGINFO << "scanned transaction history in " << timeSpent << "s";
   }

   auto timeSpent = TIMER_READ_SEC("throttling");
   if (timeSpent > 5)
      LOGINFO << "throttling for " << timeSpent << "s";

   /*timeSpent = TIMER_READ_SEC("outputs");
   LOGINFO << "outputs: " << timeSpent << "s";
   
   timeSpent = TIMER_READ_SEC("inputs");
   LOGINFO << "inputs: " << timeSpent << "s";
   
   timeSpent = TIMER_READ_SEC("write");
   LOGINFO << "write: " << timeSpent << "s";
   
   timeSpent = TIMER_READ_SEC("preload");
   LOGINFO << "preload: " << timeSpent << "s";*/
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::processOutputs()
{
   TIMER_RESET("throttling");
   TIMER_RESET("preload");
   TIMER_RESET("outputs");

   auto process_thread = [this](ParserBatch* batch)->void
   {
      this->processOutputsThread(batch);
   };

   map<unsigned, shared_ptr<BlockDataFileMap>> localFileMap;

   auto preloadBlockDataFiles = [&](ParserBatch* batch)->void
   {
      if (batch == nullptr)
         return;

      TIMER_START("preload");

      auto file_id = batch->startBlockFileID_;
      while (file_id <= batch->targetBlockFileID_)
      {
         auto local_iter = localFileMap.find(file_id);
         if (local_iter != localFileMap.end())
         {
            batch->fileMaps_.insert(
               make_pair(file_id, local_iter->second));
         }
         else
         {
            batch->fileMaps_.insert(
               make_pair(file_id, blockDataLoader_.get(file_id)));
         }

         ++file_id;
      }

      localFileMap = batch->fileMaps_;

      TIMER_STOP("preload");
   };

   //init batch
   unique_ptr<ParserBatch> batch;
   while (1)
   {
      try
      {
         batch = move(outputQueue_.pop_front());
         break;
      }
      catch (StopBlockingLoop&)
      {}
   }

   preloadBlockDataFiles(batch.get());

   while (1)
   {
      //start processing threads
      vector<thread> thr_vec;
      for (unsigned i = 0; i < totalThreadCount_; i++)
         thr_vec.push_back(thread(process_thread, batch.get()));

      unique_ptr<ParserBatch> nextBatch;

      TIMER_START("throttling");
      try
      {
         nextBatch = move(outputQueue_.pop_front());
      }
      catch (StopBlockingLoop&)
      {}
      TIMER_STOP("throttling");

      TIMER_START("outputs");

      //populate the next batch's file map while the first
      //batch is being processed
      preloadBlockDataFiles(nextBatch.get());

      //wait on threads
      for (auto& thr : thr_vec)
      {
         if (thr.joinable())
            thr.join();
      }
      
      //push first batch for input processing
      inputQueue_.push_back(move(batch));

      //exit loop condition
      if (nextBatch == nullptr)
      {
         TIMER_STOP("outputs");
         break;
      }

      //set batch for next iteration
      batch = move(nextBatch);

      TIMER_STOP("outputs");
   }

   //done with processing ouputs, there won't be anymore batches to push 
   //to the input queue, we can mark it complete
   inputQueue_.completed();
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::processInputs()
{
   TIMER_RESET("inputs");

   auto process_thread = [this](ParserBatch* batch)->void
   {
      this->processInputsThread(batch);
   };

   while (1)
   {
      unique_ptr<ParserBatch> batch;
      try
      {
         batch = move(inputQueue_.pop_front());
      }
      catch (StopBlockingLoop&)
      {
         //end condition
         break;
      }

      TIMER_START("inputs");

      //reset counter
      batch->blockCounter_.store(batch->start_, memory_order_relaxed);

      //merge utxo map from batch with global one
      //this data needs copied because we still have use for the original map
      for (auto& hash_map : batch->outputMap_)
      {
         auto hash_iter = utxoMap_.find(hash_map.first);
         if (hash_iter == utxoMap_.end())
         {
            utxoMap_.insert(hash_map);
            continue;
         }

         hash_iter->second.insert(
            hash_map.second.begin(), hash_map.second.end());
      }

      //start processing threads
      vector<thread> thr_vec;
      for (unsigned i = 1; i < totalThreadCount_; i++)
         thr_vec.push_back(thread(process_thread, batch.get()));
      process_thread(batch.get());

      //wait on threads
      for (auto& thr : thr_vec)
      {
         if (thr.joinable())
            thr.join();
      }

      //purge spent outputs from global map
      for (auto& spent_txout : batch->spentOutputs_)
      {
         auto hash_iter = utxoMap_.find(spent_txout.parentHash_);
         if (hash_iter == utxoMap_.end())
         {
            LOGERR << "missing utxo";
            continue;
         }

         auto utxo_iter = hash_iter->second.find(spent_txout.txOutIndex_);
         if (utxo_iter == hash_iter->second.end())
         {
            LOGERR << "missing utxo";
            continue;
         }

         hash_iter->second.erase(utxo_iter);
         if (hash_iter->second.size() == 0)
            utxoMap_.erase(hash_iter);
      }

      //push for commit
      commitQueue_.push_back(move(batch));

      TIMER_STOP("inputs");
   }

   //done with processing inputs, there won't be anymore batches to push 
   //to the commit queue, we can mark it complete
   commitQueue_.completed();
}


////////////////////////////////////////////////////////////////////////////////
shared_ptr<BlockData> BlockchainScanner::getBlockData(
   ParserBatch* batch, unsigned height)
{
   //grab block file map
   auto blockheader = blockchain_->getHeaderByHeight(height);
   auto filenum = blockheader->getBlockFileNum();
   auto mapIter = batch->fileMaps_.find(filenum);
   if (mapIter == batch->fileMaps_.end())
   {
      LOGERR << "Missing file map for output scan, this is unexpected";

      LOGERR << "Has the following block files:";
      for (auto& file_pair : batch->fileMaps_)
         LOGERR << " --- #" << file_pair.first;

      LOGERR << "Was looking for id #" << filenum;

      throw runtime_error("missing file map");
   }

   auto filemap = mapIter->second.get();

   //find block and deserialize it
   auto getID = [blockheader](const BinaryData&)->unsigned int
   {
      return blockheader->getThisID();
   };

   auto bdata = make_shared<BlockData>();
   bdata->deserialize(
      filemap->getPtr() + blockheader->getOffset(),
      blockheader->getBlockSize(),
      blockheader, getID, false, false);

   return bdata;
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::processOutputsThread(ParserBatch* batch)
{
   map<unsigned, shared_ptr<BlockData>> blockMap;
   map<BinaryData, map<unsigned, StoredTxOut>> outputMap;
   map<BinaryData, map<BinaryData, StoredSubHistory>> sshMap;

   while (1)
   {
      auto currentBlock =
         batch->blockCounter_.fetch_add(1, memory_order_relaxed);

      if (currentBlock > batch->end_)
         break;

      auto blockdata = getBlockData(batch, currentBlock);
      if (!blockdata->isInitialized())
      {
         LOGERR << "Could not get block data for height #" << currentBlock;
         return;
      }

      blockMap.insert(make_pair(currentBlock, blockdata));

      //TODO: flag isMultisig
      const auto header = blockdata->header();

      //update processed height
      auto topHeight = header->getBlockHeight();

      auto& txns = blockdata->getTxns();
      for (unsigned i = 0; i < txns.size(); i++)
      {
         const BCTX& txn = *(txns[i].get());
         for (unsigned y = 0; y < txn.txouts_.size(); y++)
         {
            auto& txout = txn.txouts_[y];

            BinaryRefReader brr(
               txn.data_ + txout.first, txout.second);
            brr.advance(8);
            unsigned scriptSize = (unsigned)brr.get_var_int();
            auto&& scrRef = BtcUtils::getTxOutScrAddrNoCopy(
               brr.get_BinaryDataRef(scriptSize));

            auto saIter = batch->scriptRefMap_->find(scrRef);
            if (saIter == batch->scriptRefMap_->end())
               continue;

            if (saIter->second >= (int)blockdata->header()->getBlockHeight())
               continue;

            //if we got this far, this txout is ours
            //get tx hash
            auto& txHash = txn.getHash();

            auto&& scrAddr = scrRef.getScrAddr();

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
            auto& stxoHashMap = outputMap[txHash];
            stxoHashMap.insert(make_pair(y, move(stxo)));

            //update ssh_
            auto& ssh = sshMap[scrAddr];
            auto& subssh = ssh[hgtx];

            //deal with txio count in subssh at serialization
            TxIOPair txio;
            txio.setValue(value);
            txio.setTxOut(txioKey);
            txio.setFromCoinbase(txn.isCoinbase_);
            subssh.txioMap_.insert(make_pair(txioKey, move(txio)));
         }
      }
   }

   //grab batch mutex and merge processed data in
   unique_lock<mutex> lock(batch->mergeMutex_);

   batch->blockMap_.insert(blockMap.begin(), blockMap.end());
   batch->outputMap_.insert(outputMap.begin(), outputMap.end());

   for (auto& ssh_pair : sshMap)
   {
      auto ssh_iter = batch->sshMap_.find(ssh_pair.first);
      if (ssh_iter == batch->sshMap_.end())
      {
         batch->sshMap_.insert(move(ssh_pair));
         continue;
      }

      for (auto& subssh_pair : ssh_pair.second)
         ssh_iter->second.insert(move(subssh_pair));
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::processInputsThread(ParserBatch* batch)
{
   map<BinaryData, map<BinaryData, StoredSubHistory>> sshMap;
   vector<StoredTxOut> spentOutputs;

   while (1)
   {
      auto currentBlock =
         batch->blockCounter_.fetch_add(1, memory_order_relaxed);

      if (currentBlock > batch->end_)
         break;

      auto blockdata_iter = batch->blockMap_.find(currentBlock);
      if (blockdata_iter == batch->blockMap_.end())
      {
         LOGERR << "can't find block #" << currentBlock << " in batch";
         throw runtime_error("missing block");
      }

      auto blockdata = blockdata_iter->second;

      const auto header = blockdata->header();
      auto& txns = blockdata->getTxns();

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

            //set spenderHash and parentTxOutCount to count and hash tallying
            //of spent txouts
            stxo.spenderHash_ = txn.getHash();
            stxo.parentTxOutCount_ = txn.txouts_.size();

            //add to ssh_
            auto& ssh = sshMap[stxo.getScrAddress()];
            auto& subssh = ssh[hgtx];

            //deal with txio count in subssh at serialization
            TxIOPair txio;
            auto&& txoutkey = stxo.getDBKey(false);
            txio.setTxOut(txoutkey);
            txio.setTxIn(txinkey);
            txio.setValue(stxo.getValue());
            subssh.txioMap_[txoutkey] = move(txio);

            //add to spentTxOuts_
            spentOutputs.push_back(move(stxo));
         }
      }
   }

   //merge process data into batch
   unique_lock<mutex> lock(batch->mergeMutex_);

   for (auto& ssh_pair : sshMap)
   {
      auto ssh_iter = batch->sshMap_.find(ssh_pair.first);
      if (ssh_iter == batch->sshMap_.end())
      {
         batch->sshMap_.insert(move(ssh_pair));
         continue;
      }

      for (auto& subssh_pair : ssh_pair.second)
      {
         auto txio_iter = ssh_iter->second.find(subssh_pair.first);
         if (txio_iter == ssh_iter->second.end())
         {
            ssh_iter->second.insert(move(subssh_pair));
            continue;
         }
         
         for (auto& txio_pair : subssh_pair.second.txioMap_)
         {
            txio_iter->second.txioMap_[txio_pair.first] = 
               move(txio_pair.second);
         }
      }
   }

   batch->spentOutputs_.insert(batch->spentOutputs_.end(),
      spentOutputs.begin(), spentOutputs.end());
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::writeBlockData()
{
   auto getGlobalOffsetForBlock = [&](unsigned height)->size_t
   {
      auto header = blockchain_->getHeaderByHeight(height);
      size_t val = header->getBlockFileNum();
      val *= 128 * 1024 * 1024;
      val += header->getOffset();
      return val;
   };

   ProgressCalculator calc(getGlobalOffsetForBlock(
      blockchain_->top()->getBlockHeight()));
   auto initVal = getGlobalOffsetForBlock(startAt_);
   calc.init(initVal);
   if (reportProgress_)
      progress_(BDMPhase_Rescan,
      calc.fractionCompleted(), UINT32_MAX,
      initVal);

   auto writeHintsLambda = 
      [&](ParserBatch* batch_ref)->void
   { processAndCommitTxHints(batch_ref); };

   TIMER_RESET("write");

   while (1)
   {
      unique_ptr<ParserBatch> batch;
      try
      {
         batch = move(commitQueue_.pop_front());
      }
      catch (StopBlockingLoop&)
      { 
         break;
      }

      TIMER_START("write");

      //start txhint writer thread
      thread writeHintsThreadId = 
         thread(writeHintsLambda, batch.get());

      //sanity check
      if (batch->blockMap_.size() == 0)
         continue;

      //serialize data
      auto topheader = batch->blockMap_.rbegin()->second->getHeaderPtr();
      if (topheader == nullptr)
      {
         LOGERR << "empty top block header ptr, aborting scan";
         throw runtime_error("nullptr header");
      }

      auto topHeight = topheader->getBlockHeight();
      
      map<BinaryData, BinaryWriter> serializedSubSSH;
      map<BinaryData, BinaryWriter> serializedStxo;

      {
         for (auto& ssh : batch->sshMap_)
         {
            for (auto& subssh : ssh.second)
            {
               //TODO: modify subssh serialization to fit our needs

               BinaryWriter subsshkey;
               subsshkey.put_uint8_t(DB_PREFIX_SCRIPT);
               subsshkey.put_BinaryData(ssh.first);
               subsshkey.put_BinaryData(subssh.first);

               auto& bw = serializedSubSSH[subsshkey.getDataRef()];
               subssh.second.serializeDBValue(
                  bw, db_, ARMORY_DB_BARE);
            }
         }

         for (auto& utxomap : batch->outputMap_)
         {
            for (auto& utxo : utxomap.second)
            {
               auto& bw = serializedStxo[utxo.second.getDBKey()];
               utxo.second.serializeDBValue(
                  bw, ARMORY_DB_BARE, true);
            }
         }
      }

      //we've serialized utxos, now let's do another pass for spent txouts
      //to make sure they overwrite utxos that were found and spent within
      //the same batch
      for (auto& stxo : batch->spentOutputs_)
      {
         auto& bw = serializedStxo[stxo.getDBKey()];
         if (bw.getSize() > 0)
            bw.reset();
         stxo.serializeDBValue(
            bw, ARMORY_DB_BARE, true);
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
         db_->beginDBTransaction(&tx, SUBSSH, LMDB::ReadWrite);

         for (auto& subssh : serializedSubSSH)
         {
            db_->putValue(
               SUBSSH,
               subssh.first.getRef(),
               subssh.second.getDataRef());
         }

         //update SUBSSH sdbi
         auto&& sdbi = scrAddrFilter_->getSubSshSDBI();
         sdbi.topBlkHgt_ = topheader->getBlockHeight();
         sdbi.topScannedBlkHash_ = topheader->getThisHash();
         scrAddrFilter_->putSubSshSDBI(sdbi);
      }

      //wait on writeHintsThreadId
      if (writeHintsThreadId.joinable())
         writeHintsThreadId.join();

      if (batch->start_ != batch->end_)
      {
         LOGINFO << "scanned from block #" << batch->start_
            << " to #" << batch->end_;
      }
      else
      {
         LOGINFO << "scanned block #" << batch->start_;
      }

      size_t progVal = getGlobalOffsetForBlock(batch->end_);
      calc.advance(progVal);
      if (reportProgress_)
         progress_(BDMPhase_Rescan,
         calc.fractionCompleted(), calc.remainingSeconds(),
         progVal);

      topScannedBlockHash_ = topheader->getThisHash();

      completedBatches_.fetch_add(1, memory_order_relaxed);
      batch->completedPromise_.set_value(true);

      TIMER_STOP("write");
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::processAndCommitTxHints(ParserBatch* batch)
{
   map<BinaryData, StoredTxHints> txHints;
   map<BinaryData, BinaryWriter> countAndHash;

   auto addTxHint = 
      [&](StoredTxHints& stxh, const StoredTxOut& utxo)->void
   {
      auto&& utxokey = utxo.getDBKeyOfParentTx(false);

      //make sure key isn't already in there
      for (auto& key : stxh.dbKeyList_)
      {
         if (key == utxokey)
            return;
      }

      stxh.dbKeyList_.push_back(move(utxokey));
   };

   auto addTxHintMap = 
      [&](const pair<BinaryData, map<unsigned, StoredTxOut>>& utxomap)->void
   {
      auto&& txHashPrefix = utxomap.first.getSliceCopy(0, 4);
      StoredTxHints& stxh = txHints[txHashPrefix];

      //pull txHint from DB first, don't want to override 
      //existing hints
      if (stxh.isNull())
         db_->getStoredTxHints(stxh, txHashPrefix);

      for (auto& utxo : utxomap.second)
      {
         addTxHint(stxh, utxo.second);
      }

      stxh.preferredDBKey_ = stxh.dbKeyList_.front();

      //count and hash
      auto& stxo = utxomap.second.begin()->second;
      auto& bw = countAndHash[stxo.getDBKeyOfParentTx(true)];
      if (bw.getSize() != 0)
         return;

      bw.put_uint32_t(stxo.parentTxOutCount_);
      bw.put_BinaryData(utxomap.first);
   };

   {
      LMDBEnv::Transaction hintdbtx;
      db_->beginDBTransaction(&hintdbtx, TXHINTS, LMDB::ReadOnly);

      for (auto& utxomap : batch->outputMap_)
      {
         addTxHintMap(utxomap);
      }

      map<BinaryData, map<unsigned, StoredTxOut>> spentTxOutMap;
      for (auto& stxo : batch->spentOutputs_)
      {
         auto& stxomap = spentTxOutMap[stxo.spenderHash_];
         StoredTxOut spentstxo;
         spentstxo.parentHash_ = stxo.spenderHash_;
         spentstxo.blockHeight_ =
            DBUtils::hgtxToHeight(stxo.spentByTxInKey_.getSliceRef(0, 4));
         spentstxo.duplicateID_ =
            DBUtils::hgtxToDupID(stxo.spentByTxInKey_.getSliceRef(0, 4));

         spentstxo.txIndex_ =
            READ_UINT16_BE(stxo.spentByTxInKey_.getSliceRef(4, 2));
         spentstxo.txOutIndex_ =
            READ_UINT16_BE(stxo.spentByTxInKey_.getSliceRef(6, 2));

         spentstxo.parentTxOutCount_ = stxo.parentTxOutCount_;

         stxomap.insert(move(
            make_pair(spentstxo.txOutIndex_, move(spentstxo))));
      }

      for (auto& stxomap : spentTxOutMap)
         addTxHintMap(stxomap);
   }

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

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::updateSSH(bool force)
{
   //loop over all subssh entiers in SUBSSH db, 
   //compile balance, txio count and summary map for each address
   //now also resolves unhinted tx hashes

   if (reportProgress_)
      progress_(BDMPhase_Balance, 0, 0, 0);

   StoredDBInfo sdbi = scrAddrFilter_->getSshSDBI();

   {
      shared_ptr<BlockHeader> sdbiblock;

      try
      {
         sdbiblock = blockchain_->getHeaderByHash(sdbi.topScannedBlkHash_);
      }
      catch (...)
      {
         sdbiblock = blockchain_->getHeaderByHeight(0);
      }

      if (sdbiblock->isMainBranch())
      {
         if (sdbi.topBlkHgt_ != 0 && 
             sdbi.topBlkHgt_ >= blockchain_->top()->getBlockHeight())
         {
            if (!force)
            {
               LOGINFO << "no SSH to scan";
               return;
            }
         }
      }
   }

   bool resolveHashes = false;
   {
      //check for db mode against HEADERS db since it the only one that 
      //doesn't change through rescans
      auto headersSdbi = db_->getStoredDBInfo(HEADERS, 0);

      if (headersSdbi.armoryType_ == ARMORY_DB_FULL)
         resolveHashes = true;
   }

   set<BinaryData> txnsToResolve;

   //process ssh, list missing hashes for hash resolver
   map<BinaryData, StoredScriptHistory> sshMap_;
   auto scrAddrMap = scrAddrFilter_->getScrAddrMap();

   {
      StoredScriptHistory* sshPtr = nullptr;

      LMDBEnv::Transaction historyTx, sshTx;
      db_->beginDBTransaction(&historyTx, SSH, LMDB::ReadOnly);
      db_->beginDBTransaction(&sshTx, SUBSSH, LMDB::ReadOnly);

      auto sshIter = db_->getIterator(SUBSSH);
      sshIter.seekToStartsWith(DB_PREFIX_SCRIPT);

      do
      {
         while (sshIter.isValid())
         {
            if (sshPtr != nullptr &&
               sshIter.getKeyRef().contains(sshPtr->uniqueKey_))
               break;

            //new address
            auto&& subsshkey = sshIter.getKey();
            if (subsshkey.getSize() < 5)
            { 
               LOGWARN << "invalid scrAddr in SUBSSH db";
               sshIter.advanceAndRead();
               continue;
            }

            auto sshKey = subsshkey.getSliceRef(1, subsshkey.getSize() - 5);

            auto saIter = scrAddrMap->find(sshKey);
            if (saIter == scrAddrMap->end())
            {
               sshPtr = nullptr;
               sshIter.advanceAndRead();
               continue;
            }

            //get what's already in the db
            sshPtr = &sshMap_[sshKey];
            db_->getStoredScriptHistorySummary(*sshPtr, sshKey);

            if (sshPtr->isInitialized())
            {
               //set iterator at unscanned height
               auto hgtx = sshIter.getKeyRef().getSliceRef(-4, 4);
               int height = DBUtils::hgtxToHeight(hgtx);
               if (sshPtr->tallyHeight_ >= height)
               {
                  //this ssh has already been scanned beyond the height sshIter is at,
                  //let's set the iterator to the correct height (or the next key)
                  auto&& newKey = sshIter.getKey().getSliceCopy(0, subsshkey.getSize() - 4);
                  auto&& newHgtx = DBUtils::heightAndDupToHgtx(
                     sshPtr->tallyHeight_ + 1, 0);

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

         //sanity checks
         if (!sshIter.isValid())
            break;

         //deser subssh
         StoredSubHistory subssh;
         subssh.unserializeDBKey(sshIter.getKeyRef());

         //check dupID
         if (db_->getValidDupIDForHeight(subssh.height_) != subssh.dupID_)
            continue;

         subssh.unserializeDBValue(sshIter.getValueRef());

         set<BinaryData> txSet;
         for (auto& txioPair : subssh.txioMap_)
         {
            auto&& keyOfOutput = txioPair.second.getDBKeyOfOutput();
            
            if (resolveHashes)
            {
               auto&& txKey = keyOfOutput.getSliceRef(0, 6);

               txnsToResolve.insert(txKey);
            }

            if (!txioPair.second.isMultisig())
            {
               //add up balance
               if (txioPair.second.hasTxIn())
               {
                  //check for same block fund&spend
                  auto&& keyOfInput = txioPair.second.getDBKeyOfInput();

                  if (keyOfOutput.startsWith(keyOfInput.getSliceRef(0, 4)))
                  {
                     //both output and input are part of the same block, skip
                     continue;
                  }

                  if (resolveHashes)
                  {
                     //this is to resolve output references in transaction build from
                     //multiple wallets (i.ei coinjoin)
                     txnsToResolve.insert(keyOfInput.getSliceRef(0, 6));
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
      while (sshIter.advanceAndRead(DB_PREFIX_SCRIPT));
   }


   //build txHash refs from listed txins
   if (resolveHashes && txnsToResolve.size() > 0)
   {
      set<BinaryData> allMissingTxHashes;
      try
      {
         allMissingTxHashes = move(scrAddrFilter_->getMissingHashes());
      }
      catch (runtime_error&)
      {
         //no missing hashes entry yet, move on
      }

      for (auto& txid : txnsToResolve)
      {
         //grab tx
         Tx tx;
         try
         {
            tx = move(db_->getFullTxCopy(txid));
         }
         catch (exception&)
         {
            LOGERR << "failed to grab tx by key";
            continue;
         }

         //build list of all referred hashes in txins
         auto txinCount = tx.getNumTxIn();
         auto dataPtr = tx.getPtr();

         for (auto i = 0; i < txinCount; i++)
         {
            auto offset = tx.getTxInOffset(i);
            BinaryDataRef bdr(dataPtr + offset, 32);

            //skip coinbase txns
            if (bdr == BtcUtils::EmptyHash_)
               continue;

            allMissingTxHashes.insert(bdr);
         }
      }

      scrAddrFilter_->putMissingHashes(allMissingTxHashes);
   }
   
   //write ssh data
   shared_ptr<BlockHeader> topheader;
   try
   {
      topheader = blockchain_->getHeaderByHash(topScannedBlockHash_);
   }
   catch (exception &e)
   {
      LOGERR << e.what();
      throw e;
   }

   auto topheight = topheader->getBlockHeight();

   LMDBEnv::Transaction putsshtx;
   db_->beginDBTransaction(&putsshtx, SSH, LMDB::ReadWrite);

   for (auto& scrAddr : *scrAddrMap)
   {
      auto& ssh = sshMap_[scrAddr.first.scrAddr_];

      if (!ssh.isInitialized())
      {
         ssh.uniqueKey_ = scrAddr.first.scrAddr_;
      }

      BinaryData&& sshKey = ssh.getDBKey();
      ssh.scanHeight_ = topheight;
      ssh.tallyHeight_ = topheight;

      BinaryWriter bw;
      ssh.serializeDBValue(bw, ARMORY_DB_BARE);
      
      db_->putValue(SSH, sshKey.getRef(), bw.getDataRef());
   }

   //update sdbi
   sdbi.topScannedBlkHash_ = topScannedBlockHash_;
   sdbi.topBlkHgt_ = topheight;

   scrAddrFilter_->putSshSDBI(sdbi);
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::preloadUtxos()
{
   //TODO: check utxos pulled vs scraddrfilter (to reduce dataset for side scans)
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

   auto blockPtr = reorgState.prevTop_;
   map<uint32_t, shared_ptr<BlockDataFileMap>> fileMaps_;

   map<DB_SELECT, set<BinaryData>> keysToDelete;
   map<BinaryData, StoredScriptHistory> sshMap;
   set<BinaryData> undoSpentness; //TODO: add spentness DB

   //TODO: sanity checks on header ptrs from reorgState
   if (reorgState.prevTop_->getBlockHeight() <=
       reorgState.reorgBranchPoint_->getBlockHeight())
      throw runtime_error("invalid reorg state");

   auto scrAddrMap = scrAddrFilter_->getScrAddrMap();

   while (blockPtr != reorgState.reorgBranchPoint_)
   {
      int currentHeight = blockPtr->getBlockHeight();
      auto currentDupId  = blockPtr->getDuplicateID();

      //create tx to pull subssh data
      LMDBEnv::Transaction sshTx;
      db_->beginDBTransaction(&sshTx, SUBSSH, LMDB::ReadOnly);

      //grab blocks from previous top until branch point
      if (blockPtr == nullptr)
         throw runtime_error("reorg failed while tracing back to "
         "branch point");

      auto filenum = blockPtr->getBlockFileNum();
      auto fileIter = fileMaps_.find(filenum);
      if (fileIter == fileMaps_.end())
      {
         fileIter = fileMaps_.insert(make_pair(
            filenum, blockDataLoader_.get(filenum))).first;
      }

      auto filemap = fileIter->second;

      auto getID = [blockPtr]
         (const BinaryData&)->uint32_t {return blockPtr->getThisID(); };

      BlockData bdata;
      bdata.deserialize(filemap.get()->getPtr() + blockPtr->getOffset(),
         blockPtr->getBlockSize(), blockPtr, getID, false, false);

      auto& txns = bdata.getTxns();
      for (unsigned i = 0; i < txns.size(); i++)
      {
         auto& txn = txns[i];

         //undo tx outs added by this block
         for (unsigned y = 0; y < txn->txouts_.size(); y++)
         {
            auto& txout = txn->txouts_[y];

            BinaryRefReader brr(
               txn->data_ + txout.first, txout.second);
            brr.advance(8);
            unsigned scriptSize = (unsigned)brr.get_var_int();
            auto&& scrAddr = BtcUtils::getTxOutScrAddr(
               brr.get_BinaryDataRef(scriptSize));

            auto saIter = scrAddrMap->find(scrAddr);
            if (saIter == scrAddrMap->end())
               continue;

            //update ssh value and txio count
            auto& ssh = sshMap[scrAddr];
            if (!ssh.isInitialized())
               db_->getStoredScriptHistorySummary(ssh, scrAddr);

            if (ssh.scanHeight_ < currentHeight)
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

            if (ssh.scanHeight_ < currentHeight)
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
      try
      {
         blockPtr = blockchain_->getHeaderByHash(blockPtr->getPrevHashRef());
      }
      catch (exception &e)
      {
         LOGERR << e.what();
         throw e;
      }
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

   int branchPointHeight = 
      reorgState.reorgBranchPoint_->getBlockHeight();

   //ssh
   {
      LMDBEnv::Transaction tx;
      db_->beginDBTransaction(&tx, SSH, LMDB::ReadWrite);

      //go thourgh all ssh in scrAddrFilter
      for (auto& scrAddr : *scrAddrMap)
      {
         auto& ssh = sshMap[scrAddr.first.scrAddr_];
         
         //if the ssh isn't in our map, pull it from DB
         if (!ssh.isInitialized())
         {
            db_->getStoredScriptHistorySummary(ssh, scrAddr.first.scrAddr_);
            if (ssh.uniqueKey_.getSize() == 0)
            {
               sshMap.erase(scrAddr.first.scrAddr_);
               continue;
            }
         }

         //update alreadyScannedUpToBlk_ to branch point height
         if (ssh.scanHeight_ > branchPointHeight)
            ssh.scanHeight_ = branchPointHeight;

         if (ssh.tallyHeight_ > branchPointHeight)
            ssh.tallyHeight_ = branchPointHeight;
      }

      //write it all up
      for (auto& ssh : sshMap)
      {
         auto saIter = scrAddrMap->find(ssh.second.uniqueKey_);
         if (saIter == scrAddrMap->end())
         {
            LOGWARN << "invalid scrAddr during undo";
            continue;
         }

         BinaryWriter bw;
         ssh.second.serializeDBValue(bw, ARMORY_DB_BARE);
         db_->putValue(SSH,
            ssh.second.getDBKey().getRef(),
            bw.getDataRef());
      }

      //update SSH sdbi      
      StoredDBInfo sdbi = scrAddrFilter_->getSshSDBI();
      sdbi.topScannedBlkHash_ = reorgState.reorgBranchPoint_->getThisHash();
      sdbi.topBlkHgt_ = branchPointHeight;
      scrAddrFilter_->putSshSDBI(sdbi);
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::getFilterHitsThread(
   const set<BinaryData>& hashSet,
   atomic<int>& counter,
   map<uint32_t, set<TxFilterResults>>& resultMap)
{
   map<uint32_t, set<TxFilterResults>> localResults;

   {
      LMDBEnv::Transaction tx;
      db_->beginDBTransaction(&tx, TXFILTERS, LMDB::ReadOnly);

      while (1)
      {
         auto&& fileNum = counter.fetch_sub(1, memory_order_relaxed);

         if (fileNum < 0)
            break;

         try
         {
            auto&& pool = db_->getFilterPoolRefForFileNum<TxFilterType>(fileNum);
            for (auto& hash : hashSet)
            {
               auto&& blockKeys = pool.compare(hash);
               if (blockKeys.size() > 0)
               {
                  auto& fileNumEntry = localResults[fileNum];

                  TxFilterResults filterResult;
                  filterResult.hash_ = hash;
                  filterResult.filterHits_ = move(blockKeys);

                  fileNumEntry.insert(move(filterResult));
               }
            }
         }
         catch (runtime_error&)
         {
            LOGWARN << "couldnt get filter pool for file: " << fileNum;
            continue;
         }
      }
   }

   //merge results
   unique_lock<mutex> lock(resolverMutex_);
   resultMap.insert(localResults.begin(), localResults.end());
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::processFilterHitsThread(
   map<uint32_t, map<uint32_t, set<const TxFilterResults*>>>& filtersResultMap,
   TransactionalSet<BinaryData>& missingHashes,
   atomic<int>& counter, map<BinaryData, BinaryData>& results,
   function<void(size_t)> prog)
{
   map<BinaryData, BinaryData> result;

   uint32_t missedBlocks = 0;

   auto resolveHashes = 
      [&](uint32_t fileNum,
      map<uint32_t, set<const TxFilterResults*>> filterHit,
      set<BinaryData>& hashSet)->void
   {
      auto fileptr = blockDataLoader_.get(fileNum);
      
      for (auto& blockkey : filterHit)
      {
         shared_ptr<BlockHeader> headerPtr;
         try
         {
            headerPtr = blockchain_->getHeaderById(blockkey.first);
         }
         catch (range_error&)
         {
            //no block for this id, this is an orphan
            missedBlocks++;
            continue;
         }

         auto& filterSet = blockkey.second;

         auto getID = [headerPtr](const BinaryData&)->unsigned int
         { return headerPtr->getThisID(); };

         //search the block
         BlockData bdata;
         try
         {
            bdata.deserialize(
               fileptr->getPtr() + headerPtr->getOffset(),
               headerPtr->getBlockSize(),
               headerPtr, getID, false, false);
         }
         catch (BlockDeserializingException& e)
         {
            LOGERR << "Block deser error while processing tx filters: ";
            LOGERR << "  " << e.what();
            LOGERR << "Skipping this block";
            continue;
         }
            
         auto txns = bdata.getTxns();

         for (auto& filterhit : filterSet)
         {
            auto iditer = filterhit->filterHits_.find(blockkey.first);
            if (iditer == filterhit->filterHits_.end())
               continue;

            auto& txids = iditer->second;

            for (auto& txid : txids)
            {
               if (txid >= txns.size())
                  continue;

               auto& txn = txns[txid];
               auto& txnHash = txn->getHash();

               auto hashIter = hashSet.begin();

               while (hashIter != hashSet.end())
               {
                  if (txnHash == *hashIter)
                  {
                     auto&& countAndHash = WRITE_UINT32_LE(txids.size());
                     countAndHash.append(txnHash);
                     result[countAndHash] = move(
                        DBUtils::getBlkDataKeyNoPrefix(
                        headerPtr->getBlockHeight(),
                        headerPtr->getDuplicateID(),
                        txid));

                     missingHashes.erase(txnHash);
                     auto count = missingHashes.size();
                     prog(count);

                     hashSet.erase(hashIter++);
                     continue;
                  }

                  ++hashIter;
               }

            }
         }
      }
   };

   vector<uint32_t> blkFileNums;
   for (auto& hitsPair : filtersResultMap)
      blkFileNums.push_back(hitsPair.first);

   while (1)
   {
      auto&& index = counter.fetch_sub(1, memory_order_relaxed);
      if (index < 0)
         break;

      auto& fileNum = blkFileNums[index];
      auto filterIter = filtersResultMap.find(fileNum);

      auto& blkHitsMap = filterIter->second;
      auto hashSet = missingHashes.get();

      auto hitsPairIter = blkHitsMap.begin();

      while (hitsPairIter != blkHitsMap.end())
      {
         auto& txFilterSet = hitsPairIter->second;

         auto hitsIter = txFilterSet.begin();
         while (hitsIter != txFilterSet.end())
         {
            auto hashIter = hashSet->find((*hitsIter)->hash_);
            if (hashIter != hashSet->end())
            {
               ++hitsIter;
               continue;
            }

            txFilterSet.erase(hitsIter++);
         }

         if (txFilterSet.size() > 0)
         {
            ++hitsPairIter;
            continue;
         }

         blkHitsMap.erase(hitsPairIter++);
      }

      if (blkHitsMap.size() == 0)
         continue;

      resolveHashes(filterIter->first, filterIter->second, *hashSet);
   }

   //merge results
   unique_lock<mutex> lock(resolverMutex_);
   results.insert(result.begin(), result.end());
}

////////////////////////////////////////////////////////////////////////////////
bool BlockchainScanner::resolveTxHashes()
{
   /***
   the missing hashes entry will always be empty if the db is not set
   to ARMORY_DB_FULL, no need to check dbType here
   ***/

   TIMER_RESTART("resolveHashes");

   if (reportProgress_)
      progress_(BDMPhase_SearchHashes, 0, UINT32_MAX, 0);

   set<BinaryData> missingHashes;
   try
   {
      missingHashes = move(scrAddrFilter_->getMissingHashes());
   }
   catch (runtime_error&)
   {
      //no missing hashes entry, return
      TIMER_STOP("resolveHashes");
      return true;
   }
   
   if (missingHashes.size() == 0)
      return true;

   set<BinaryData> resolvedHashes;
   auto originalMissingSet = missingHashes;

   auto hashIter = missingHashes.begin();
   while (hashIter != missingHashes.end())
   {
      auto&& dbkey = db_->getDBKeyForHash(*hashIter);
      if (dbkey.getSize() == 0)
      {
         ++hashIter;
         continue;
      }

      resolvedHashes.insert(*hashIter);
      missingHashes.erase(hashIter++);
   }

   TransactionalSet<BinaryData> missingHashSet;
   map<BinaryData, TxFilter<TxFilterType>> relevantFilters;
   missingHashSet.insert(missingHashes);

   LOGINFO << "resolving txhashes";

   //check filters
   atomic<int> counter;
   counter.store((int)totalBlockFileCount_ - 1, memory_order_relaxed);

   vector<thread> filterThreads;
   map<uint32_t, set<TxFilterResults>> resultMap;

   auto filterThr = [&](void)->void
   {
      getFilterHitsThread(missingHashes, counter, resultMap);
   };

   for (unsigned i = 1; i < totalThreadCount_; i++)
      filterThreads.push_back(thread(filterThr));

   filterThr();

   for (auto& thr : filterThreads)
   {
      if (thr.joinable())
         thr.join();
   }

   set<uint32_t> heights;
   map<uint32_t, map<uint32_t, set<const TxFilterResults*>>> resultsByHash;
   unsigned missingIDs = 0;
   for (auto& fileNumPair : resultMap)
   {
      auto& block_result_pair = resultsByHash[fileNumPair.first];

      for (auto& filterHits : fileNumPair.second)
      {
         for (auto& filterHit : filterHits.filterHits_)
         {
            try
            {
               auto header = 
                  blockchain_->getHeaderById(filterHit.first);
               auto height = header->getBlockHeight();
         
               heights.insert(height);
               block_result_pair[filterHit.first].insert(&filterHits);
            }
            catch (...)
            {
               ++missingIDs;
            }
         }
      }
   }

   /*if (missingIDs > 0)
   {
      LOGINFO << missingIDs << " missing block IDs";
      return false;
   }*/

   LOGINFO << heights.size() << " blocks hit by tx filters";

   //process filter hits
   counter.store(resultMap.size() - 1, memory_order_relaxed);
   map<BinaryData, BinaryData> resolverResults;
   vector<thread> resolverThreads;

   auto hashCount = missingHashSet.size();
   ProgressCalculator calc(hashCount);
   mutex progressMutex;
   uint64_t topCount = hashCount;

   auto resolveProgress = [&](size_t count)->void
   {
      if (!reportProgress_)
         return;

      unique_lock<mutex> lock(progressMutex, defer_lock);
      if (!lock.try_lock())
         return;

      if (count > topCount)
         return;

      topCount = count;
      auto intprog = hashCount - count;
      calc.advance(intprog);
      this->progress_(BDMPhase_ResolveHashes, 
         calc.fractionCompleted(), calc.remainingSeconds(), count);
   };

   auto resolverThr = [&](void)->void
   {
      processFilterHitsThread(resultsByHash,
         missingHashSet,
         counter, resolverResults, resolveProgress);
   };

   if (reportProgress_)
      progress_(BDMPhase_ResolveHashes, 0, UINT32_MAX, 0);


   for (unsigned i = 1; i < totalThreadCount_; i++)
      resolverThreads.push_back(thread(resolverThr));

   resolverThr();

   for (auto& thr : resolverThreads)
   {
      if (thr.joinable())
         thr.join();
   }

   //write the resolved hashes
   {
      map<BinaryData, StoredTxHints> txHints;
      map<BinaryData, BinaryWriter> serializedHints;
      map<BinaryData, BinaryWriter> countAndHash;

      {
         LMDBEnv::Transaction hintTx;
         db_->beginDBTransaction(&hintTx, TXHINTS, LMDB::ReadOnly);

         for (auto& result : resolverResults)
         {
            resolvedHashes.insert(result.first);

            //get hashPrefix
            auto hashPrefix = result.first.getSliceRef(4, 4);

            auto& hintObj = txHints[hashPrefix];

            //pull hint if it's fresh
            if (hintObj.getNumHints() == 0)
               db_->getStoredTxHints(hintObj, hashPrefix);

            //append new key
            hintObj.dbKeyList_.push_back(result.second);

            //save hash and count under dbkey
            BinaryData dbkey;
            dbkey.append(WRITE_UINT8_LE(DB_PREFIX_TXDATA));
            dbkey.append(result.second);

            auto& bw = countAndHash[dbkey];
            bw.put_BinaryData(result.first);
         }
      }

      LOGINFO << "found " << resolverResults.size() << " missing hashes";

      for (auto& hint : txHints)
      {
         BinaryData hintKey(1);
         hintKey.getPtr()[0] = DB_PREFIX_TXHINTS;
         hintKey.append(hint.first);
         auto& bw = serializedHints[hintKey];
         hint.second.serializeDBValue(bw);
      }

      //write it
      {
         LMDBEnv::Transaction hintTx;
         db_->beginDBTransaction(&hintTx, TXHINTS, LMDB::ReadWrite);

         for (auto& toWrite : serializedHints)
         {
            db_->putValue(TXHINTS,
               toWrite.first.getRef(),
               toWrite.second.getDataRef());
         }

         for (auto& toWrite : countAndHash)
         {
            db_->putValue(TXHINTS,
               toWrite.first.getRef(),
               toWrite.second.getDataRef());
         }
      }
   }

   //clean up missing hashes in db
   missingHashes.clear();
   for (auto& hash : originalMissingSet)
   {
      auto resolvedIter = resolvedHashes.find(hash);
      if (resolvedIter == resolvedHashes.end())
         missingHashes.insert(hash);
   }

   scrAddrFilter_->putMissingHashes(missingHashes);

   TIMER_STOP("resolveHashes");
   auto timeElapsed = TIMER_READ_SEC("resolveHashes");
   LOGINFO << "Resolved missing hashes in " << timeElapsed << "s";

   if (missingHashes.size() > 0)
      return false;

   return true;
}
