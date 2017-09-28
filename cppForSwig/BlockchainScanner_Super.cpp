////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2017, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BlockchainScanner_Super.h"
#include "EncryptionUtils.h"

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner_Super::scan()
{
   TIMER_RESTART("scan");

   unsigned scanFrom = 0;

   auto&& subsshSdbi = db_->getStoredDBInfo(SUBSSH, 0);

   try
   {
      auto topScannedBlock =
         blockchain_->getHeaderByHash(subsshSdbi.topScannedBlkHash_);

      while (!topScannedBlock->isMainBranch())
      {
         topScannedBlock = blockchain_->getHeaderByHash(
            topScannedBlock->getPrevHash());
      }

      scanFrom = topScannedBlock->getBlockHeight() + 1;
   }
   catch (range_error&)
   { }

   auto topBlock = blockchain_->top();

   if (scanFrom > topBlock->getBlockHeight())
   {
      topScannedBlockHash_ = topBlock->getThisHash();
      return;
   }

   startAt_ = scanFrom;

   heightAndDupMap_ = move(blockchain_->getHeightAndDupMap());

   vector<future<bool>> completedFutures;
   unsigned _count = 0;

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
         size_t targetSize = BATCH_SIZE_SUPER;
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

               if (_count == 0)
                  withUpdateSshHints_ = true;
            }
         }

         endHeight = targetHeight;

         //create batch
         auto&& batch = make_unique<ParserBatch_Super>(
            startHeight, endHeight,
            firstBlockFileID, targetBlockFileID);

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

   TIMER_STOP("scan");
   if (topBlock->getBlockHeight() - scanFrom > 100)
   {
      auto timeSpent = TIMER_READ_SEC("scan");
      LOGINFO << "scanned transaction history in " << timeSpent << "s";
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner_Super::processOutputs()
{
   auto process_thread = [this](ParserBatch_Super* batch)->void
   {
      this->processOutputsThread(batch);
   };

   auto preloadBlockDataFiles = [this](ParserBatch_Super* batch)->void
   {
      if (batch == nullptr)
         return;

      auto file_id = batch->startBlockFileID_;
      while (file_id <= batch->targetBlockFileID_)
      {
         batch->fileMaps_.insert(
            make_pair(file_id, blockDataLoader_.get(file_id)));
         ++file_id;
      }
   };

   //init batch
   unique_ptr<ParserBatch_Super> batch;
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

      unique_ptr<ParserBatch_Super> nextBatch;
      try
      {
         nextBatch = move(outputQueue_.pop_front());
      }
      catch (StopBlockingLoop&)
      {
      }

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
         break;

      //set batch for next iteration
      batch = move(nextBatch);
   }

   //done with processing ouputs, there won't be anymore batches to push 
   //to the input queue, we can mark it complete
   inputQueue_.completed();
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner_Super::processInputs()
{
   auto process_thread = [this](ParserBatch_Super* batch)->void
   {
      this->processInputsThread(batch);
   };

   while (1)
   {
      unique_ptr<ParserBatch_Super> batch;
      try
      {
         batch = move(inputQueue_.pop_front());
      }
      catch (StopBlockingLoop&)
      {
         //end condition
         break;
      }

      //reset counter
      batch->blockCounter_.store(batch->start_, memory_order_relaxed);

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

      //clear helper map
      batch->hashToDbKey_.clear();

      //serialize subssh
      size_t subsshCount = 0;
      for (auto& ssh : batch->sshMap_)
         subsshCount += ssh.second.size();
      
      batch->serializedSubSsh_.resize(subsshCount);

      subsshCount = 0;
      {
         for (auto& ssh : batch->sshMap_)
         {
            for (auto& subssh : ssh.second)
            {
               //TODO: modify subssh serialization to fit our needs
               auto& bw_pair = batch->serializedSubSsh_[subsshCount];

               bw_pair.first.put_uint8_t(DB_PREFIX_SCRIPT);
               bw_pair.first.put_BinaryData(ssh.first);
               bw_pair.first.put_BinaryData(subssh.first);

               subssh.second.serializeDBValue(
                  bw_pair.second, db_, ARMORY_DB_SUPER);

               ++subsshCount;
            }
         }
      }

      if (withUpdateSshHints_)
      {
         for (auto& ssh : batch->sshMap_)
            updateSshHints_.insert(ssh.first);
      }

      batch->sshMap_.clear();

      //push for commit
      commitQueue_.push_back(move(batch));
   }

   //done with processing inputs, there won't be anymore batches to push 
   //to the commit queue, we can mark it complete
   commitQueue_.completed();
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<BlockData> BlockchainScanner_Super::getBlockData(
   ParserBatch_Super* batch, unsigned height)
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
StoredTxOut BlockchainScanner_Super::getStxoByHash(
   BinaryDataRef& hash, uint16_t txoId,
   ParserBatch_Super* batch,
   map<unsigned, shared_ptr<BlockDataFileMap>>& filemap)
{
   StoredTxOut stxo;

   /*#1: resolve dbkey*/
   BinaryData txoKey;
   uint32_t block_id;
   uint8_t fakedup;
   uint16_t txid;


   //check batch map first
   auto hash_iter = batch->hashToDbKey_.find(hash);
   if (hash_iter != batch->hashToDbKey_.end())
      txoKey = hash_iter->second;

   if (txoKey.getSize() == 0)
   {
      //next, fetch and resolve hints
      StoredTxHints sths;
      if (!db_->getStoredTxHints(sths, hash.getSliceRef(0, 4)))
      {
         LOGERR << "missing hints for hash";
         throw runtime_error("missing hints for hash");
      }

      for (auto& hintkey : sths.dbKeyList_)
      {
         BinaryWriter bw_key;
         bw_key.put_BinaryData(hintkey);
         bw_key.put_uint16_t(txoId, BE);

         BinaryRefReader brr(hintkey);
         DBUtils::readBlkDataKeyNoPrefix(brr, block_id, fakedup, txid);

         auto hd_iter = heightAndDupMap_.find(block_id);
         if (hd_iter == heightAndDupMap_.end())
            continue;
         if (hd_iter->second.dup_ == 0xFF)
            continue;

         auto data = db_->getValueNoCopy(STXO, bw_key.getDataRef());
         if (data.getSize() == 0)
            continue;

         stxo.unserializeDBValue(data);
         if (stxo.parentHash_ == hash)
         {
            txoKey = hintkey;
            break;
         }

         stxo.dataCopy_.clear();
      }
   }

   /*#2: create stxo*/

   if (!stxo.isInitialized())
   {
      if (txoKey.getSize() == 0)
      {
         LOGERR << "could not get stxo by hash";
         throw runtime_error("could not get stxo by hash");
      }

      BinaryRefReader brr(txoKey);
      DBUtils::readBlkDataKeyNoPrefix(brr, block_id, fakedup, txid);

      //create stxo key
      BinaryWriter bw_key;
      bw_key.put_BinaryData(txoKey);
      bw_key.put_uint16_t(txoId, BE);

      auto data = db_->getValueNoCopy(STXO, bw_key.getDataRef());
      if (data.getSize() == 0)
      {
         LOGERR << "failed to grab stxo by key";
         LOGERR << "key is: " << bw_key.toHex();
         throw runtime_error("failed to grab stxo by key");
      }

      stxo.unserializeDBValue(data);
   }

   //fill in key
   auto hd_iter = heightAndDupMap_.find(block_id);
   if (hd_iter == heightAndDupMap_.end())
   {
      LOGERR << "invalid block id: " << block_id;
      LOGERR << "heightAndDupMap has " << heightAndDupMap_.size() << " entries";
      throw runtime_error("invalid block id");
   }

   stxo.blockHeight_ = hd_iter->second.height_;
   stxo.duplicateID_ = hd_iter->second.dup_;
   stxo.txIndex_     = txid;
   stxo.txOutIndex_  = txoId;

   return stxo;
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner_Super::processOutputsThread(ParserBatch_Super* batch)
{
   map<unsigned, shared_ptr<BlockData>> blockMap;
   map<BinaryData, BinaryData> hashToKey;
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
      auto&& hgtx = DBUtils::heightAndDupToHgtx(
         header->getBlockHeight(), header->getDuplicateID());

      auto& txns = blockdata->getTxns();
      for (unsigned i = 0; i < txns.size(); i++)
      {
         const BCTX& txn = *(txns[i].get());
         auto& txHash = txn.getHash();

         auto&& txkey = 
            DBUtils::getBlkDataKeyNoPrefix(header->getThisID(), 0xFF, i);
         hashToKey.insert(make_pair(txHash, move(txkey)));

         for (unsigned y = 0; y < txn.txouts_.size(); y++)
         {
            auto& txout = txn.txouts_[y];

            BinaryRefReader brr(
               txn.data_ + txout.first, txout.second);
            auto value = brr.get_uint64_t();
            unsigned scriptSize = (unsigned)brr.get_var_int();
            auto&& scrRef = BtcUtils::getTxOutScrAddrNoCopy(
               brr.get_BinaryDataRef(scriptSize));


            auto&& scrAddr = scrRef.getScrAddr();
            auto&& txioKey = DBUtils::getBlkDataKeyNoPrefix(
               header->getBlockHeight(), header->getDuplicateID(),
               i, y);

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
   batch->hashToDbKey_.insert(hashToKey.begin(), hashToKey.end());

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
void BlockchainScanner_Super::processInputsThread(ParserBatch_Super* batch)
{
   map<BinaryData, map<BinaryData, StoredSubHistory>> sshMap;
   map<BinaryData, BinaryData> spentness;

   map<unsigned, shared_ptr<BlockDataFileMap>> temp_filemap;

   LMDBEnv::Transaction stxo_tx;
   db_->beginDBTransaction(&stxo_tx, STXO, LMDB::ReadOnly);
   LMDBEnv::Transaction hints_tx;
   db_->beginDBTransaction(&hints_tx, TXHINTS, LMDB::ReadOnly);

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
      auto&& hgtx = DBUtils::getBlkDataKeyNoPrefix(
         header->getBlockHeight(), header->getDuplicateID());

      auto& txns = blockdata->getTxns();
      for (unsigned i = 0; i < txns.size(); i++)
      {
         const BCTX& txn = *(txns[i].get());

         for (unsigned y = 0; y < txn.txins_.size(); y++)
         {
            auto& txin = txn.txins_[y];
            BinaryDataRef outHash(
               txn.data_ + txin.first, 32);
            
            if (outHash == BtcUtils::EmptyHash_)
               continue;

            unsigned txOutId = READ_UINT32_LE(
               txn.data_ + txin.first + 32);

            auto&& stxo = getStxoByHash(
               outHash, txOutId,
               batch, temp_filemap);

            auto&& txinkey = DBUtils::getBlkDataKeyNoPrefix(
               header->getBlockHeight(), header->getDuplicateID(),
               i, y);

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
            spentness[stxo.getDBKey(false)] = txinkey;
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

   batch->spentness_.insert(spentness.begin(), spentness.end());
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner_Super::writeBlockData()
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

   auto putSpentnessLbd = [this](ParserBatch_Super* batchPtr)->void
   {
      putSpentness(batchPtr);
   };

   while (1)
   {
      unique_ptr<ParserBatch_Super> batch;
      try
      {
         batch = move(commitQueue_.pop_front());
      }
      catch (StopBlockingLoop&)
      {
         break;
      }

      //sanity check
      if (batch->blockMap_.size() == 0)
         continue;

      thread spentnessThr(putSpentnessLbd, batch.get());

      //serialize data
      auto topheader = batch->blockMap_.rbegin()->second->getHeaderPtr();
      if (topheader == nullptr)
      {
         LOGERR << "empty top block header ptr, aborting scan";
         throw runtime_error("nullptr header");
      }

      {
         //subssh
         LMDBEnv::Transaction tx;
         db_->beginDBTransaction(&tx, SUBSSH, LMDB::ReadWrite);

         for (auto& bw_pair : batch->serializedSubSsh_)
         {
            db_->putValue(
               SUBSSH,
               bw_pair.first.getDataRef(),
               bw_pair.second.getDataRef());
         }

         //sdbi
         auto&& subssh_sdbi = db_->getStoredDBInfo(SUBSSH, 0);
         subssh_sdbi.topBlkHgt_ = topheader->getBlockHeight();
         subssh_sdbi.topScannedBlkHash_ = topheader->getThisHash();
         db_->putStoredDBInfo(SUBSSH, subssh_sdbi, 0);
      }

      if (spentnessThr.joinable())
         spentnessThr.join();

      if (batch->start_ != batch->end_)
      {
         LOGINFO << "scanned from height #" << batch->start_
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
      batch->completedPromise_.set_value(true);
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner_Super::putSpentness(ParserBatch_Super* batch)
{
   LMDBEnv::Transaction tx;
   db_->beginDBTransaction(&tx, SPENTNESS, LMDB::ReadWrite);

   for (auto& spent_pair : batch->spentness_)
      db_->putValue(SPENTNESS, spent_pair.first, spent_pair.second);
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner_Super::updateSSH(bool force)
{
   //loop over all subssh entiers in SUBSSH db, 
   //compile balance, txio count and summary map for each address
   unsigned scanFrom = 0;

   auto&& sshSdbi = db_->getStoredDBInfo(SSH, 0);

   try
   {
      auto topScannedBlock =
         blockchain_->getHeaderByHash(sshSdbi.topScannedBlkHash_);

      while (!topScannedBlock->isMainBranch())
      {
         topScannedBlock = blockchain_->getHeaderByHash(
            topScannedBlock->getPrevHash());
      }

      scanFrom = topScannedBlock->getBlockHeight() + 1;
   }
   catch (range_error&)
   {
   }

   auto topBlock = blockchain_->top();

   if (force)
      scanFrom = 0;

   if (scanFrom > topBlock->getBlockHeight())
      return;

   TIMER_RESTART("updateSSH");

   if (!withUpdateSshHints_)
      LOGINFO << "updating SSH";

   auto processSshLambda = [this, scanFrom](void)->void
   {
      updateSSHThread(scanFrom);
   };

   auto temp_db = SecureBinaryData().GenerateRandom(8).toHexStr();
   auto writeLambda = [this, &temp_db](void)->void
   {
      putSSH(temp_db);
   };

   if (reportProgress_)
      progress_(BDMPhase_Balance, 0, 0, 0);

   thread writeThr = thread(writeLambda);

   vector<thread> processSshVec;
   if (!withUpdateSshHints_)
   {
      for (unsigned i = 0; i < totalThreadCount_; i++)
         processSshVec.push_back(thread(processSshLambda));

      set<uint8_t> special_bytes;
      special_bytes.insert(BlockDataManagerConfig::getPubkeyHashPrefix());
      special_bytes.insert(BlockDataManagerConfig::getScriptHashPrefix());

      for (uint16_t i = 0; i < 256; i++)
      {
         auto byte_iter = special_bytes.find(i);
         if (byte_iter != special_bytes.end())
         {
            for (uint16_t y = 0; y < 256; y++)
            {
               BinaryWriter bw_first;
               bw_first.put_uint8_t(DB_PREFIX_SCRIPT);
               bw_first.put_uint8_t(i);
               bw_first.put_uint8_t(y);

               BinaryWriter bw_last;
               bw_last.put_BinaryData(bw_first.getData());
               bw_last.put_uint8_t(0xFF);

               auto&& bounds = make_pair(bw_first.getData(), bw_last.getData());
               sshBoundsQueue_.push_back(move(bounds));
            }

            continue;
         }

         BinaryWriter bw_first;
         bw_first.put_uint8_t(DB_PREFIX_SCRIPT);
         bw_first.put_uint8_t(i);

         BinaryWriter bw_last;
         bw_last.put_uint8_t(DB_PREFIX_SCRIPT);
         bw_last.put_uint8_t(i);
         bw_last.put_uint8_t(0xFF);

         auto&& bounds = make_pair(bw_first.getData(), bw_last.getData());

         sshBoundsQueue_.push_back(move(bounds));
      }
   }
   else
   {
      processSshVec.push_back(thread(processSshLambda));

      for (auto& ssh : updateSshHints_)
      {
         pair<BinaryData, BinaryData> bounds;

         BinaryWriter bw_first;
         bw_first.put_uint8_t(DB_PREFIX_SCRIPT);
         bw_first.put_BinaryData(ssh);

         bounds.first = bw_first.getData();
         bounds.second = bw_first.getData();

         sshBoundsQueue_.push_back(move(bounds));
      }
   }


   //wait on process threads
   sshBoundsQueue_.completed();

   for (auto& thr : processSshVec)
   {
      if (thr.joinable())
         thr.join();
   }

   //wait on write thread
   serializedSshQueue_.completed();
   if (writeThr.joinable())
      writeThr.join();

   //merge in temp db dataset
   if (sshSdbi.topBlkHgt_ <= 0)
   {
      //initial sync, let's just swap the files
      db_->swapDatabases(SSH, temp_db);
   }
   else
   {
      LMDBEnv dbEnv;
      LMDB db;
      dbEnv.open(db_->getDbPath(temp_db));

      {
         LMDBEnv::Transaction tx(&dbEnv, LMDB::ReadWrite);
         db.open(&dbEnv, db_->getDbName(SSH));
      }

      {
         LMDBEnv::Transaction swap_tx(&dbEnv, LMDB::ReadOnly);
         LMDBEnv::Transaction ssh_tx;
         db_->beginDBTransaction(&ssh_tx, SSH, LMDB::ReadWrite);

         auto temp_sshIter = db.begin();
         auto main_sshIter = db_->getIterator(SSH);

         auto&& prefixkey = WRITE_UINT8_BE(DB_PREFIX_SCRIPT);
         CharacterArrayRef prefix_car(1, prefixkey.getPtr());
         temp_sshIter.seek(prefix_car, LMDB::Iterator::Seek_GE);


         //iterate over temp db entries
         while (temp_sshIter.isValid())
         {
            BinaryDataRef key_ref(
               (uint8_t*)temp_sshIter.key().mv_data, temp_sshIter.key().mv_size);

            BinaryDataRef data_ref(
               (uint8_t*)temp_sshIter.value().mv_data, temp_sshIter.value().mv_size);

            //sanity checks
            if (!key_ref.startsWith(prefixkey))
               break;

            db_->putValue(SSH, key_ref, data_ref);

            //increment
            ++temp_sshIter;
         }
      }

      //shut down and delete temp db
      db.close();
      dbEnv.close();

      auto&& db_path = db_->getDbPath(temp_db);
      remove(db_path.c_str());
      db_path.append("-lock");
      remove(db_path.c_str());
   }

   {
      //update sdbi
      auto topheader = blockchain_->getHeaderByHash(topScannedBlockHash_);
      auto topheight = topheader->getBlockHeight();

      //update sdbi
      sshSdbi.topScannedBlkHash_ = topBlock->getThisHash();
      sshSdbi.topBlkHgt_ = topheight;

      LMDBEnv::Transaction ssh_tx;
      db_->beginDBTransaction(&ssh_tx, SSH, LMDB::ReadWrite);
      db_->putStoredDBInfo(SSH, sshSdbi, 0);
   }

   TIMER_STOP("updateSSH");
   auto timeSpent = TIMER_READ_SEC("updateSSH");
   if (timeSpent >= 5)
      LOGINFO << "updated SSH in " << timeSpent << "s";
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner_Super::putSSH(const string& dbname)
{
   //create temp ssh db
   LMDBEnv dbEnv;
   LMDB db;
   dbEnv.open(db_->getDbPath(dbname));

   {
      LMDBEnv::Transaction tx(&dbEnv, LMDB::ReadWrite);
      db.open(&dbEnv, db_->getDbName(SSH));
   }

   //loop over serialized ssh queue

   while (1)
   {
      unique_ptr<map<BinaryData, BinaryWriter>> sshMap;

      try
      {
         sshMap = move(serializedSshQueue_.pop_front());
      }
      catch (StopBlockingLoop&)
      {
         break;
      }

      if (sshMap->size() == 0)
         continue;

      LMDBEnv::Transaction tx(&dbEnv, LMDB::ReadWrite);
      for (auto& ssh_pair : *sshMap)
      {
         CharacterArrayRef key(
            ssh_pair.first.getSize(), ssh_pair.first.getPtr());
         CharacterArrayRef data(
            ssh_pair.second.getSize(), ssh_pair.second.getData().getPtr());

         db.insert(key, data);
      }
   }

   //close db
   db.close();
   dbEnv.close();
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner_Super::updateSSHThread(int scanFrom)
{
   size_t size_per_batch = COMMIT_SSH_SIZE / totalThreadCount_;

   auto serializeSSH = [](
      const SshContainer& ssh,
      map<BinaryData, BinaryWriter>& ssh_map)->size_t
   {
      if (!ssh.changed_)
         return 0;

      BinaryData&& sshKey = ssh.obj_.getDBKey();

      BinaryWriter bw;
      ssh.obj_.serializeDBValue(bw, ARMORY_DB_SUPER);

      size_t size = sshKey.getSize() + bw.getSize();

      auto&& ssh_pair = make_pair(move(sshKey), move(bw));
      ssh_map.insert(move(ssh_pair));

      return size;
   };

   while (1)
   {
      pair<BinaryData, BinaryData> bounds;
      try
      {
         bounds = move(sshBoundsQueue_.pop_front());
      }
      catch (StopBlockingLoop&)
      {
         break;
      }

      auto serializedSshMap = move(make_unique<map<BinaryData, BinaryWriter>>());
      size_t tally = 0;
      SshContainer local_ssh;

      LMDBEnv::Transaction historyTx, sshTx;
      db_->beginDBTransaction(&historyTx, SSH, LMDB::ReadOnly);
      db_->beginDBTransaction(&sshTx, SUBSSH, LMDB::ReadOnly);

      auto sshIter = SshIterator(db_, bounds);
      if (!sshIter.isValid())
         continue;

      while (1)
      {
         while (sshIter.isValid())
         {
            if (local_ssh.obj_.isInitialized() &&
               sshIter.getKeyRef().contains(local_ssh.obj_.uniqueKey_))
               break;

            //new address
            auto subsshkey = sshIter.getKeyRef();
            if (subsshkey.getSize() < 5)
            {
               LOGWARN << "invalid scrAddr in SUBSSH db";
               sshIter.advanceAndRead();
               continue;
            }

            //serialize ssh
            if (local_ssh.obj_.isInitialized())
            {
               tally += serializeSSH(local_ssh, *serializedSshMap);
               local_ssh.clear();
            }

            if (tally > size_per_batch)
            {
               serializedSshQueue_.push_back(move(serializedSshMap));
               serializedSshMap = 
                  move(make_unique<map<BinaryData, BinaryWriter>>());
               tally = 0;
            }

            //get what's already in the db
            auto sshKey = subsshkey.getSliceRef(1, subsshkey.getSize() - 5);
            db_->getStoredScriptHistorySummary(local_ssh.obj_, sshKey);

            if (local_ssh.obj_.isInitialized())
            {
               //set iterator at unscanned height
               auto hgtx = sshIter.getKeyRef().getSliceRef(-4, 4);
               int height = DBUtils::hgtxToHeight(hgtx);
               if (scanFrom > height)
               {
                  //this ssh has already been scanned beyond the height sshIter is at,
                  //let's set the iterator to the correct height (or the next key)
                  auto&& newKey = 
                     sshIter.getKeyRef().getSliceCopy(0, subsshkey.getSize() - 4);
                  auto&& newHgtx = DBUtils::heightAndDupToHgtx(
                     scanFrom, 0);

                  newKey.append(newHgtx);
                  sshIter.seekTo(newKey);

                  continue;
               }
            }
            else
            {
               local_ssh.obj_.uniqueKey_ = sshKey;
               break;
            }
         }

         //sanity checks
         if (!sshIter.isValid())
         {
            serializeSSH(local_ssh, *serializedSshMap);
            break;
         }

         //deser subssh
         StoredSubHistory subssh;
         subssh.unserializeDBKey(sshIter.getKeyRef());

         //check dupID
         if (db_->getValidDupIDForHeight(subssh.height_) != subssh.dupID_)
         {
            sshIter.advanceAndRead();
            continue;
         }

         subssh.unserializeDBValue(sshIter.getValueRef());

         unsigned txiocount = 0;
         set<BinaryData> txSet;
         for (auto& txioPair : subssh.txioMap_)
         {
            auto&& keyOfOutput = txioPair.second.getDBKeyOfOutput();

            if (!txioPair.second.isMultisig())
            {
               //add up balance
               if (txioPair.second.hasTxIn())
               {
                  ++txiocount;
                  //check for same block fund&spend
                  auto&& keyOfInput = txioPair.second.getDBKeyOfInput();

                  if (keyOfOutput.startsWith(keyOfInput.getSliceRef(0, 4)))
                  {
                     //both output and input are part of the same block, skip
                     ++txiocount;
                     continue;
                  }

                  local_ssh.obj_.totalUnspent_ -= txioPair.second.getValue();
               }
               else
               {
                  ++txiocount;
                  local_ssh.obj_.totalUnspent_ += txioPair.second.getValue();
               }
            }
         }

         //txio count
         local_ssh.obj_.totalTxioCount_ += txiocount;
         local_ssh.changed_ = true;

         //build subssh summary
         local_ssh.obj_.subsshSummary_[subssh.height_] = txiocount;

         if (!sshIter.advanceAndRead())
         {
            serializeSSH(local_ssh, *serializedSshMap);
            break;
         }
      } 

      if (serializedSshMap->size() > 0)
         serializedSshQueue_.push_back(move(serializedSshMap));
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner_Super::undo(Blockchain::ReorganizationState& reorgState)
{
   //TODO: sanity checks on header ptrs from reorgState
   if (reorgState.prevTop_->getBlockHeight() <=
      reorgState.reorgBranchPoint_->getBlockHeight())
      throw runtime_error("invalid reorg state");

   auto blockPtr = reorgState.prevTop_;
   map<uint32_t, shared_ptr<BlockDataFileMap>> fileMaps_;
   map<BinaryData, StoredScriptHistory> sshMap;
   set<BinaryData> undoSpentness;

   while (blockPtr != reorgState.reorgBranchPoint_)
   {
      int currentHeight = blockPtr->getBlockHeight();
      auto currentDupId = blockPtr->getDuplicateID();

      //create tx to pull subssh data
      LMDBEnv::Transaction sshTx;
      db_->beginDBTransaction(&sshTx, SUBSSH, LMDB::ReadOnly);

      LMDBEnv::Transaction hintsTx;
      db_->beginDBTransaction(&hintsTx, TXHINTS, LMDB::ReadOnly);

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

            //update ssh value and txio count
            auto& ssh = sshMap[scrAddr];
            if (!ssh.isInitialized())
               db_->getStoredScriptHistorySummary(ssh, scrAddr);

            brr.resetPosition();
            uint64_t value = brr.get_uint64_t();
            ssh.totalUnspent_ -= value;
            ssh.totalTxioCount_--;

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

            if (outHash == BtcUtils::EmptyHash_)
               continue;

            uint16_t txOutId = (uint16_t)READ_UINT32_LE(
               txn->data_ + txin.first + 32);

            StoredTxOut stxo;
            if (!db_->getStoredTxOut(stxo, outHash, txOutId))
            {
               LOGERR << "failed to grab stxo";
               throw runtime_error("failed to grab stxo");
            }

            auto& scrAddr = stxo.getScrAddress();

            //update ssh value and txio count
            auto& ssh = sshMap[scrAddr];
            if (!ssh.isInitialized())
               db_->getStoredScriptHistorySummary(ssh, scrAddr);

            ssh.totalUnspent_ += stxo.getValue();
            ssh.totalTxioCount_--;

            //decrement summary count at height, remove entry if necessary
            auto& sum = ssh.subsshSummary_[currentHeight];
            sum--;

            if (sum <= 0)
               ssh.subsshSummary_.erase(currentHeight);
            
            //mark spentness entry for deletion
            undoSpentness.insert(move(stxo.getDBKey(false)));
         }
      }

      //set blockPtr to prev block
      blockPtr = blockchain_->getHeaderByHash(blockPtr->getPrevHashRef());
   }

   //at this point we have a map of updated ssh, as well as a 
   //set of keys to delete from the DB and spentness to undo by stxo key

   int branchPointHeight =
      reorgState.reorgBranchPoint_->getBlockHeight();

   //spentness
   {
      LMDBEnv::Transaction spentness_tx;
      db_->beginDBTransaction(&spentness_tx, SPENTNESS, LMDB::ReadWrite);

      for (auto& spentness_key : undoSpentness)
         db_->deleteValue(SPENTNESS, spentness_key);
   }

   //ssh
   {
      //go thourgh all ssh in scrAddrFilter
      for (auto& ssh_pair : sshMap)
      {
         auto& ssh = ssh_pair.second;

         //if the ssh isn't in our map, pull it from DB
         if (!ssh.isInitialized())
         {
            db_->getStoredScriptHistorySummary(ssh, ssh_pair.first);
            if (ssh.uniqueKey_.getSize() == 0)
            {
               sshMap.erase(ssh_pair.first);
               continue;
            }
         }
      }

      LMDBEnv::Transaction ssh_tx;
      db_->beginDBTransaction(&ssh_tx, SSH, LMDB::ReadWrite);

      //write it all up
      for (auto& ssh : sshMap)
      {
         BinaryWriter bw;
         ssh.second.serializeDBValue(bw, ARMORY_DB_SUPER);
         db_->putValue(SSH,
            ssh.second.getDBKey().getRef(),
            bw.getDataRef());
      }

      //update SSH sdbi      
      auto&& sdbi = db_->getStoredDBInfo(SSH, 0);
      sdbi.topScannedBlkHash_ = reorgState.reorgBranchPoint_->getThisHash();
      sdbi.topBlkHgt_ = branchPointHeight;
      db_->putStoredDBInfo(SSH, sdbi, 0);
   }
}
