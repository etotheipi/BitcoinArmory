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
void BlockData::deserialize(const uint8_t* data, size_t size,
   const BlockHeader* blockHeader)
{
   headerPtr_ = blockHeader;

   //deser header from raw and run a quick sanity check
   if (size < HEADER_SIZE)
      throw runtime_error("raw data is smaller than HEADER_SIZE");

   BinaryDataRef bdr(data, HEADER_SIZE);
   BlockHeader bh(bdr);

   if (bh.getThisHashRef() != blockHeader->getThisHashRef())
      throw runtime_error("raw data does not back expected block hash");

   //get numTx, check against blockheader too
   BinaryRefReader brr(data + HEADER_SIZE, size - HEADER_SIZE);
   unsigned numTx = (unsigned)brr.get_var_int();

   if (numTx != blockHeader->getNumTx())
      throw runtime_error("tx count mismatch in deser header");

   for (int i = 0; i < numTx; i++)
   {
      //light tx deserialization, just figure out the offset and size of
      //txins and txouts
      vector<size_t> offsetIns, offsetOuts;
      auto txSize = BtcUtils::TxCalcLength(
         brr.getCurrPtr(), brr.getSizeRemaining(),
         &offsetIns, &offsetOuts);

      //create BCTX object and fill it up
      BCTX tx(brr.getCurrPtr(), txSize);
      tx.version_ = READ_UINT32_LE(brr.getCurrPtr());
     
      //convert offsets to offset + size pairs
      for (int y = 0; y < offsetIns.size() - 1; y++)
         tx.txins_.push_back(
            make_pair(
               offsetIns[y], 
               offsetIns[y+1] - offsetIns[y]));

      for (int y = 0; y < offsetOuts.size() - 1; y++)
         tx.txouts_.push_back(
            make_pair(
               offsetOuts[y], 
               offsetOuts[y+1] - offsetOuts[y]));
      
      tx.lockTime_ = READ_UINT32_LE(brr.getCurrPtr() + offsetOuts.back());

      //move it to BlockData object vector
      txns_.push_back(move(tx));

      //increment ptr offset
      brr.advance(txSize);
   }
}

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

   //lambdas
   auto readBlockDataLambda = [&](shared_ptr<BlockDataBatch> batch)
   { readBlockData(batch); };

   auto scanBlockDataLambda = [&](shared_ptr<BlockDataBatch> batch)
   { scanBlockData(batch); };

   auto startHeight = scanFrom;
   unsigned endHeight = 0;

   //start write thread

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

         for (int i = 0; i < totalThreadCount_; i++)
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
         for (int i = 0; i < totalThreadCount_; i++)
         {
            //lock each batch mutex before start scan thread
            lockVec.push_back(unique_lock<mutex>(batchVec[i]->mu_));
            tIDs.push_back(thread(scanBlockDataLambda, batchVec[i]));
         }

         //wait for utxo scan to complete
         for (int i = 0; i < totalThreadCount_; i++)
         {
            auto utxoScanFlag = batchVec[i]->doneScanningUtxos_;
            utxoScanFlag.get();
         }

         //update utxoMap_
         for (auto& batch : batchVec)
         {
            utxoMap_.insert(batch->utxos_.begin(), batch->utxos_.end());
         }

         //signal txin scan by releasing all mutexes
         lockVec.clear();

         //figure out top scanned block num

         //push processed batch to write thread

         //increment startBlock
         startHeight += endHeight + 1;
      }
   }
   catch (range_error& e)
   {
      LOGERR << "failed to grab block data starting height: " << startHeight;
      if (startHeight == scanFrom)
         LOGERR << "no block data was scanned";
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockchainScanner::readBlockData(shared_ptr<BlockDataBatch> batch)
{
   auto currentBlock = batch->start_;
   auto blockFuture = batch->first_;

   mutex mu;
   unique_lock<mutex> lock(mu);

   while (currentBlock >= batch->end_)
   {
      //stay within nBlocksLookAhead of the scan thread
      while (batch->highestProcessedHeight_.load(memory_order_relaxed) >
         nBlocksLookAhead_ * totalThreadCount_)
      {
         batch->readThreadCV_.wait(lock);
      }

      //setup promise
      promise<BlockDataLink> blockPromise;
      blockFuture = blockPromise.get_future();

      //TODO: encapsulate in try block to catch deser errors and signal pull thread
      //termination before exiting scope. cant have the scan thread hanging if this
      //one fails

      //grab block file map
      BlockHeader* blockheader = &blockchain_->getHeaderByHeight(currentBlock);
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
         filemap->getPtr() + blockheader->getOffset(), blockheader->getSize(),
         blockheader);

      //fill promise
      blockPromise.set_value(blockfuture);

      //prepare next iteration
      blockFuture = blockFuture.get().next_;
      currentBlock += totalThreadCount_;
   }

   //we're done, fill the block future with the termination block
   promise<BlockDataLink> blockPromise;
   blockFuture = blockPromise.get_future();
   blockPromise.set_value(BlockDataLink());
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
      const BlockHeader* header = blockdata.header();

      //update processed height
      auto topHeight = header->getBlockHeight();
      batch->highestProcessedHeight_.store(topHeight, memory_order_relaxed);

      auto& txns = blockdata.getTxns();
      for (unsigned i = 0; i < txns.size(); i++)
      {
         auto& txn = txns[i];
         for (unsigned y = 0; y < txn.txouts_.size(); y++)
         {
            auto& txout = txn.txouts_[y];

            BinaryRefReader brr(txout.first);
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
            auto value = stxo.getValue();

            auto&& hgtx = DBUtils::heightAndDupToHgtx(
               stxo.blockHeight_, stxo.duplicateID_);
            
            auto&& txioKey = DBUtils::getBlkDataKeyNoPrefix(
               stxo.blockHeight_, stxo.duplicateID_,
               i, y);

            //update utxos_
            auto& stxoHashMap = batch->utxos_[txHash];
            stxoHashMap.insert(make_pair(i, move(stxo)));

            //update ssh_
            auto& ssh = batch->ssh_[scrAddr];
            auto& subssh = ssh.subHistMap_[hgtx];
            
            //deal with txio count in subssh at serialization
            TxIOPair txio;
            txio.setValue(value);
            txio.setTxOut(txioKey);
            subssh.txioMap_.insert(make_pair(txioKey, txio));
         }
      }
   };

   //txin lambda
   auto txinParser = [&](const BlockData& blockdata)->void
   {
      const BlockHeader* header = blockdata.header();
      auto& txns = blockdata.getTxns();

      for (unsigned i = 0; i < txns.size(); i++)
      {
         auto& txn = txns[i];

         for (unsigned y = 0; y < txn.txins_.size(); y++)
         {
            auto& txin = txn.txins_[y];
            BinaryDataRef outHash(
               txn.data_ + txin.first, 32);

            auto utxoIter = batch->utxos_.find(outHash);
            if (utxoIter == batch->utxos_.end())
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

            //add to spentTxOuts_
            batch->spentTxOuts_.push_back(move(stxo));

            //add to ssh_
            auto& ssh = batch->ssh_[stxo.scrAddr_];
            auto& subssh = ssh.subHistMap_[hgtx];

            //deal with txio count in subssh at serialization
            TxIOPair txio;
            txio.setTxOut(stxo.getDBKey(false));
            txio.setTxIn(txinkey);
            txio.setValue(stxo.getValue());
            subssh.txioMap_.insert(make_pair(txinkey, txio));
         }
      }
   };

   //setup future flag
   promise<bool> utxoScanFlag;
   batch->doneScanningUtxos_ = utxoScanFlag.get_future();

   //txout loop
   blockDataLoop(txoutParser);

   //done with txouts, fill the future flag and wait on the mutex 
   //to move to txins processing
   utxoScanFlag.set_value(true);
   unique_lock<mutex> lock(batch->mu_);

   //txins loop
   blockDataLoop(txinParser);
}