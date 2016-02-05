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
   const BlockHeader& blockHeader)
{
   //deser header from raw and run a quick sanity check
   if (size < HEADER_SIZE)
      throw runtime_error("raw data is smaller than HEADER_SIZE");

   BinaryDataRef bdr(data, HEADER_SIZE);
   BlockHeader bh(bdr);

   if (bh.getThisHashRef() != blockHeader.getThisHashRef())
      throw runtime_error("raw data does not back expected block hash");

   //get numTx, check against blockheader too
   BinaryRefReader brr(data + HEADER_SIZE, size - HEADER_SIZE);
   unsigned numTx = (unsigned)brr.get_var_int();

   if (numTx != blockHeader.getNumTx())
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
      blockFuture = make_shared<future<BlockDataLink>>(blockPromise.get_future());

      //TODO: encapsulate in try block to catch deser errors and signal pull thread
      //termination before exiting scope. cant have the scan thread hanging if this
      //one fails

      //grab block file map
      auto blockheader = blockchain_->getHeaderByHeight(currentBlock);
      auto filenum = blockheader.getBlockFileNum();
      
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
         filemap->getPtr() + blockheader.getOffset(), blockheader.getSize(),
         blockheader);

      //fill promise
      blockPromise.set_value(blockfuture);

      //prepare next iteration
      blockFuture = blockFuture->get().next_;
      currentBlock += totalThreadCount_;
   }
}