////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include "BlockWriteBatcher.h"

#include "StoredBlockObj.h"
#include "BlockDataManagerConfig.h"
#include "lmdb_wrapper.h"
#include "Progress.h"
#include "util.h"

#ifdef _MSC_VER
#include "win32_posix.h"
#endif

shared_ptr<BlockDataBatch> BlockDataBatchLoader::interruptBatch_ =
   make_shared<BlockDataBatch>(0, 0, 0);

////////////////////////////////////////////////////////////////////////////////
static void updateBlkDataHeader(
      const BlockDataManagerConfig &config,
      LMDBBlockDatabase* iface,
      StoredHeader const & sbh
   )
{
   iface->putValue(
      BLKDATA, sbh.getDBKey(),
      serializeDBValue(sbh, BLKDATA, config.armoryDbType, config.pruneType)
   );
}

////////////////////////////////////////////////////////////////////////////////
void insertSpentTxio(
   const TxIOPair& txio,
   StoredSubHistory& inHgtSubSsh,
   const BinaryData& txOutKey, 
   const BinaryData& txInKey)
{
   auto& mirrorTxio = inHgtSubSsh.txioMap_[txOutKey];

   mirrorTxio = txio;
   mirrorTxio.setTxIn(txInKey);
   
   if (!txOutKey.startsWith(inHgtSubSsh.hgtX_))
      inHgtSubSsh.txioCount_++;
}

////////////////////////////////////////////////////////////////////////////////
//// BlockWriteBatcher
////////////////////////////////////////////////////////////////////////////////
ARMORY_DB_TYPE BlockWriteBatcher::armoryDbType_;
LMDBBlockDatabase* BlockWriteBatcher::iface_;
ScrAddrFilter* BlockWriteBatcher::scrAddrFilter_;
function<void(string)> BlockWriteBatcher::criticalError_;

////////////////////////////////////////////////////////////////////////////////
BlockWriteBatcher::BlockWriteBatcher(
   const BlockDataManagerConfig &config,
   LMDBBlockDatabase* iface,
   ScrAddrFilter& sca, 
   bool undo)
   : undo_(undo)
{
   iface_ = iface;
   armoryDbType_ = iface_->armoryDbType();
   scrAddrFilter_ = &sca;

   batchVector_.resize(MAX_BATCH_BUFFER);

   if (undo)
   {
      //force all threads down to 1 for reorgs
      totalThreadCount_ = 1;
   }
   else
   {
      totalThreadCount_ = thread::hardware_concurrency();
      if (totalThreadCount_ < 1)
         totalThreadCount_ = 1;
   }

   if (BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER)
   {
      //for supernode, split workers and writers evenly, round up writers
      //only 1 reader is enough
      uint32_t totalThr = totalThreadCount_ - 1;
      uint32_t workers = totalThr / 2;
      if (workers < 1)
         workers = 1;

      int32_t writers = totalThr - (int32_t)workers;
      if (writers < 1)
         writers = 1;

      setThreadCounts(1, workers, writers);
   }
   else
   {
      //50% workers, 1 writer, rest as readers
      int32_t workers = totalThreadCount_ / 2;
      if (workers < 1)
         workers = 1;

      int32_t readers = totalThreadCount_ - 1 - workers;
      if (readers < 1)
         readers = 1;

      setThreadCounts(readers, workers, 1);
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::prepareSshHeaders(BlockBatchProcessor& bbp, 
   const ScrAddrFilter& saf)
{
   //In fullnode, the sshToModify_ container is not wiped after each commit.
   //Instead, all SSH for tracked scrAddr, since we know they're the onyl one
   //that will get any traffic, and in order to update all alreadyScannedUpToBlk_
   //members each commit

   if (BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER)
      return;
   
   if (bbp.sshHeaders_ != nullptr)
      return;

   bbp.sshHeaders_.reset(new SSHheaders(1, 0));
   bbp.sshHeaders_->buildSshHeadersFromSAF(
      saf);
   
   uint32_t utxoCount=0;
   LMDBEnv::Transaction tx;
   iface_->beginDBTransaction(&tx, HISTORY, LMDB::ReadOnly);

   auto& sshMap = bbp.sshHeaders_->sshToModify_;

   for (auto sshPair : *sshMap)
   {
      auto& ssh = sshPair.second;
      
      if (ssh.totalTxioCount_ != 0)
      {
         StoredScriptHistory tempSSH = ssh;
         BinaryData subKey = ssh.getSubKey();
         LMDBEnv::Transaction subtx;
         iface_->beginSubSSHDBTransaction(subtx, ssh.keyLength_, LMDB::ReadOnly);

         LDBIter dbIter = iface_->getSubSSHIterator(ssh.keyLength_);
         dbIter.seekTo(subKey);

         iface_->readStoredScriptHistoryAtIter(dbIter, tempSSH, 0, UINT32_MAX);

         for (auto& subssh : tempSSH.subHistMap_)
         {
            for (auto& txio : subssh.second.txioMap_)
            {
               if (txio.second.isUTXO())
               {
                  BinaryData dbKey = txio.second.getDBKeyOfOutput();
                  shared_ptr<StoredTxOut> stxo(new StoredTxOut);
                  iface_->getUnspentTxOut(*stxo, dbKey);

                  BinaryData txHash = iface_->getTxHashForLdbKey(dbKey.getSliceRef(0, 6));

                  BinaryWriter bwUtxoKey(34);
                  bwUtxoKey.put_BinaryData(txHash);
                  bwUtxoKey.put_uint16_t(stxo->txOutIndex_, BE);

                  bbp.stxos_.utxoMap_[bwUtxoKey.getDataRef()] = stxo;
                  utxoCount++;
               }
            }
         }
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::pushBatch(shared_ptr<BlockDataBatch> batch)
{
   uint32_t topId = topBatch_ % MAX_BATCH_BUFFER;
   
   batch->chargeSleep_ = clock();
   unique_lock<mutex> lock(batchLock_);
   while (batchVector_[topId] != nullptr)
   {
      batchCV_.wait(lock);
   }

   if (batch->hasData_)
      batchVector_[topId] = batch;
   else
      batchVector_[topId] = BlockDataBatchLoader::interruptBatch_;

   batch->chargeSleep_ = clock() - batch->chargeSleep_;

   topBatch_++;
   batchCV_.notify_all();
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<BlockDataBatch> BlockWriteBatcher::popBatch()
{
   shared_ptr<BlockDataBatch> batch;
   uint32_t currentId = currentBatch_ % MAX_BATCH_BUFFER;

   //grab the feed lock, assign the feed ptr locally and check if it's valid
   unique_lock<mutex> lock(batchLock_);
   while (1)
   {
      batch = batchVector_[currentId];

      if (batch != nullptr)
         break;

      //batch isn't ready, wake grab thread and wait on it
      batchCV_.wait(lock);
   }

   if (batch == BlockDataBatchLoader::interruptBatch_)
      return nullptr;

   //reset current feed so a new one can replace it
   batchVector_[currentId].reset();
   currentBatch_++;
   batchCV_.notify_all();

   return batch;
}


////////////////////////////////////////////////////////////////////////////////
//// BlockDataBatchLoader
////////////////////////////////////////////////////////////////////////////////
int32_t BlockDataBatchLoader::getOffsetHeight(BlockDataBatchLoader& blockData,
   uint32_t threadId)
{

   if (blockData.startBlock_ <= blockData.endBlock_)
   {
      uint32_t offset = blockData.startBlock_ / blockData.nThreads_;
      offset *= blockData.nThreads_;
      offset += threadId;
      if (offset < blockData.startBlock_)
         offset += blockData.nThreads_;
      return offset;
   }

   uint32_t offset = blockData.startBlock_ / blockData.nThreads_;
   offset *= blockData.nThreads_;
   offset += threadId;
   if (offset > blockData.startBlock_)
      offset -= blockData.nThreads_;
   return offset;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataBatchLoader::isHeightValid(BlockDataBatchLoader& blockBatch,
   int32_t hgt)
{
   if (blockBatch.terminate_.load(memory_order_acquire) == true)
      return false;

   if (blockBatch.startBlock_ <= blockBatch.endBlock_)
      return hgt <= (int)blockBatch.endBlock_;

   return hgt >= (int)blockBatch.endBlock_;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataBatchLoader::nextHeight(BlockDataBatchLoader& blockData,
   int32_t& hgt)
{
   if (blockData.startBlock_ <= blockData.endBlock_)
      hgt += blockData.nThreads_;
   else
      hgt -= blockData.nThreads_;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataBatchLoader::getTopHeight(
   BlockDataBatchLoader& lbd, PulledBlock& pb)
{
   if (lbd.startBlock_ <= lbd.endBlock_)
      return pb.blockHeight_;

   return pb.blockHeight_ - 1;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BlockDataBatchLoader::getTopHash(
   BlockDataBatchLoader& lbd, PulledBlock& pb)
{
   if (lbd.startBlock_ <= lbd.endBlock_)
      return pb.thisHash_;

   uint32_t height = pb.blockHeight_ - 1;
   uint8_t dup = BlockWriteBatcher::iface_->getValidDupIDForHeight(height);
   BinaryData dbKey = DBUtils::getBlkDataKey(height, dup);

   LMDBEnv::Transaction tx;
   BlockWriteBatcher::iface_->beginDBTransaction(&tx, HEADERS, LMDB::ReadOnly);
   
   StoredHeader sbh;
   BlockWriteBatcher::iface_->getBareHeader(sbh, dbKey);
   return sbh.thisHash_;
}


////////////////////////////////////////////////////////////////////////////////
void PullBlockThread::pullThread(
   shared_ptr<BlockDataBatchLoader> blockData, uint32_t threadId)
{
   /***
   Pull raw block data from DB/blockchain
   ***/

   auto db = BlockWriteBatcher::iface_;

   int32_t hgt = BlockDataBatchLoader::getOffsetHeight(*blockData, threadId);

   if (!BlockDataBatchLoader::isHeightValid(*blockData, hgt))
      return;

   //find last block
   PullBlockThread& pullThr = blockData->pullThreads_[threadId];
   shared_ptr<PulledBlock> *lastBlock = &pullThr.block_->nextBlock_;
   shared_ptr<FileMap> prevFileMap;

   unique_lock<mutex> grabLock(pullThr.grabLock_);

   while (1)
   {
      //create read only db txn within main loop, so that it is renewed
      //after each sleep period
      LMDBEnv::Transaction tx(db->dbEnv_[BLKDATA].get(), LMDB::ReadOnly);
      LDBIter ldbIter = db->getIterator(BLKDATA);

      uint8_t dupID = db->getValidDupIDForHeight(hgt);
      if (!ldbIter.seekToExact(DBUtils::getBlkMetaKey(hgt, dupID)))
      {
         unique_lock<mutex> assignLock(pullThr.assignLock_);
         *lastBlock = blockData->interruptBlock_;
         LOGERR << "Header heigh&dup is not in BLKDATA DB";
         LOGERR << "(" << hgt << ", " << dupID << ")";
         return;
      }

      while (pullThr.bufferLoad_.load(memory_order_acquire)
         < BYTES_PER_BATCH / blockData->nThreads_ ||
         (pullThr.block_ != nullptr && 
          pullThr.block_->nextBlock_ == nullptr))
      {
         if (!BlockDataBatchLoader::isHeightValid(*blockData, hgt))
            return;

         uint8_t dupID = db->getValidDupIDForHeight(hgt);
         if (dupID == UINT8_MAX)
         {
            unique_lock<mutex> assignLock(pullThr.assignLock_);
            *lastBlock = blockData->interruptBlock_;
            LOGERR << "No block in DB at height " << hgt;
            return;
         }

         //make sure iterator is at the right position
         auto expected = DBUtils::heightAndDupToHgtx(hgt, dupID);
         auto key = ldbIter.getKeyRef().getSliceRef(1, 4);
         if (key != expected)
         {
            //in case the iterator is not at the right key, set it
            if (!ldbIter.seekToExact(DBUtils::getBlkMetaKey(hgt, dupID)))
            {
               unique_lock<mutex> assignLock(pullThr.assignLock_);
               *lastBlock = blockData->interruptBlock_;
               LOGERR << "Header heigh&dup is not in BLKDATA DB";
               LOGERR << "(" << hgt << ", " << dupID << ")";
               return;
            }
         }

         shared_ptr<PulledBlock> pb = make_shared<PulledBlock>();
         pb->fmp_.prev_ = prevFileMap;
         if (!pullBlockAtIter(*pb, ldbIter, db, blockData->BFA_))
         {
            unique_lock<mutex> assignLock(pullThr.assignLock_);
            *lastBlock = blockData->interruptBlock_;
            LOGERR << "No block in DB at height " << hgt;
            return;
         }

         prevFileMap = pb->fmp_.current_;

         //increment bufferLoad
         pullThr.bufferLoad_.fetch_add(
            pb->numBytes_, memory_order_release);

         //assign newly grabbed block to shared_ptr
         {
            {
               unique_lock<mutex> assignLock(pullThr.assignLock_);
               *lastBlock = pb;
            }

            //let's try to wake up the scan thread
            unique_lock<mutex> mu(blockData->pullLock_, defer_lock);
            if (mu.try_lock())
               blockData->pullCV_.notify_all();
         }

         //set shared_ptr to next empty block
         lastBlock = &pb->nextBlock_;

         BlockDataBatchLoader::nextHeight(*blockData, hgt);
      }

      if (!BlockDataBatchLoader::isHeightValid(*blockData, hgt))
         return;

      //sleep 10sec or until scan thread signals block buffer is low
      pullThr.grabCV_.wait_for(grabLock, chrono::seconds(2));
   }
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BlockWriteBatcher::applyBlocksToDB(ProgressFilter &progress,
   ScrAddrFilter& scf)
{
   try
   {
      //for progress reporting
      uint64_t totalBlockDataProcessed=0;
      uint32_t threshold = 1 + startBlock_ / 2500;
      threshold *= 2500;
      
      //setup raw block reader + batch loader
      uint32_t prevReadersCount = nReaders_.load(memory_order_acquire);
      shared_ptr<BlockDataBatchLoader> prevLoader = nullptr;
      shared_ptr<BlockDataBatchLoader> batchLoader =
         make_shared<BlockDataBatchLoader>(
         this, prevReadersCount, prevLoader);
      batchLoader->startPullThreads(batchLoader);
      prevLoader = batchLoader;

      //setup batch processor
      BlockBatchProcessor batchProcessor(this, undo_);
      batchProcessor.forceUpdateSSH_ = forceUpdateSSH_;
      prepareSshHeaders(batchProcessor, scf);
      
      thread processorTID = batchProcessor.startThreads();

      while (1)
      {
         //reader main loop
         uint32_t feedTopBlockHeight;
         uint32_t feedSize;
         uint32_t nReaders = nReaders_.load(memory_order_acquire);
         uint32_t nWorkers = nWorkers_.load(memory_order_acquire);
         uint32_t nWriters = nWriters_.load(memory_order_acquire);

         if (nReaders != prevReadersCount)
         {
            //readers thread count changed, create object with new count.
            batchLoader->terminate();

            batchLoader = make_shared<BlockDataBatchLoader>(
               this, nReaders, prevLoader);
            prevLoader = batchLoader;
            prevReadersCount = nReaders;

            batchLoader->startPullThreads(batchLoader);
         }

         auto nextBatch = batchLoader->chargeNextBatch(
            nReaders, nWorkers, nWriters);
         
         if (!nextBatch->hasData_)
         {
            //no more data, join on processor then exit loop
            batchLoader->terminate();

            if (processorTID.joinable())
               processorTID.join();
            break;
         }

         //progress reporting
         if (nextBatch->topBlockHeight_ > threshold)
         {
            LOGWARN << "Finished applying blocks up to " << threshold;
            threshold = ((nextBatch->topBlockHeight_ / 2500) + 1) * 2500;
         }

         totalBlockDataProcessed += nextBatch->totalSizeInBytes_;
         progress.advance(totalBlockDataProcessed);
         nextBatch.reset();
      }
   
      return batchProcessor.lastScannedBlockHash_;
   }
   catch (...)
   {      
      string errorMessage("Scan thread encountered an unkonwn error");
      criticalError_(errorMessage);
   }
   
   return BinaryData();
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::setThreadCounts(
   uint32_t nReaders, uint32_t nWorkers, uint32_t nWriters) const
{
   nReaders_.store(nReaders, memory_order_release);
   nWorkers_.store(nWorkers, memory_order_release);
   nWriters_.store(nWriters, memory_order_release);
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BlockWriteBatcher::scanBlocks(
   ProgressFilter &prog,
   uint32_t startBlock, uint32_t endBlock, 
   ScrAddrFilter& scf,
   bool forceUpdateSSH)
{
   //Grab the SSHheader static mutex. This makes sure only this scan is 
   //creating new SSH keys. If several scanning threads were to take place, 
   //it could possibly result in key collision, as scan threads are not aware
   //of each others' state
   unique_lock<mutex> addressingLock(SSHheaders::keyAddressingMutex_);

   startBlock_ = startBlock;
   endBlock_ = endBlock;
   forceUpdateSSH_ = forceUpdateSSH;
   
   BinaryData bd = applyBlocksToDB(prog, scf);
   if (abs((int)startBlock - (int)endBlock) > 500)
   {
      double timeElapsed = TIMER_READ_SEC("feedSleep");
      LOGWARN << "--- feedSleep: " << timeElapsed << " s";

      timeElapsed = TIMER_READ_SEC("workers");
      LOGWARN << "--- workers: " << timeElapsed << " s";

      timeElapsed = TIMER_READ_SEC("writeStxo");
      LOGWARN << "--- writeStxo: " << timeElapsed << " s";
      timeElapsed = TIMER_READ_SEC("writeStxo_grabMutex");
      LOGWARN << "--- writeStxo_grabMutex: " << timeElapsed << " s";

      timeElapsed = TIMER_READ_SEC("waitingOnSerThread");
      LOGWARN << "--- waitingOnSerThread: " << timeElapsed << " s";
      timeElapsed = TIMER_READ_SEC("waitForDataToWrite");
      LOGWARN << "--- waitForDataToWrite: " << timeElapsed << " s";


      timeElapsed = TIMER_READ_SEC("checkForCollisions");
      LOGWARN << "--- checkForCollisions: " << timeElapsed << " s";
      timeElapsed = TIMER_READ_SEC("getExistingKeys");
      LOGWARN << "--- getExistingKeys: " << timeElapsed << " s";
      timeElapsed = TIMER_READ_SEC("getNewKeys");
      LOGWARN << "--- getNewKeys: " << timeElapsed << " s";
      timeElapsed = TIMER_READ_SEC("getSSHHeadersLock");
      LOGWARN << "--- getSSHHeadersLock: " << timeElapsed << " s";
      timeElapsed = TIMER_READ_SEC("computeDBKeys");
      LOGWARN << "--- computeDBKeys: " << timeElapsed << " s";
      timeElapsed = TIMER_READ_SEC("getSshHeaders");
      LOGWARN << "--- getSshHeaders: " << timeElapsed << " s";
      timeElapsed = TIMER_READ_SEC("finalizeSerialization");
      LOGWARN << "--- finalizeSerialization: " << timeElapsed << " s";



      timeElapsed = TIMER_READ_SEC("serializeBatch");
      LOGWARN << "--- serializeBatch: " << timeElapsed << " s";
      timeElapsed = TIMER_READ_SEC("updateSSH");
      LOGWARN << "--- updateSSH: " << timeElapsed << " s";
      timeElapsed = TIMER_READ_SEC("serializeSubSsh");
      LOGWARN << "--- serializeSubSsh: " << timeElapsed << " s";
      timeElapsed = TIMER_READ_SEC("waitOnSSHser");
      LOGWARN << "--- waitOnSSHser: " << timeElapsed << " s";


      timeElapsed = TIMER_READ_SEC("waitOnWriteThread");
      LOGWARN << "--- waitOnWriteThread: " << timeElapsed << " s";

      timeElapsed = TIMER_READ_SEC("putSSH");
      LOGWARN << "--- putSSH: " << timeElapsed << " s";
      timeElapsed = TIMER_READ_SEC("putSTX");
      LOGWARN << "--- putSTX: " << timeElapsed << " s";

      timeElapsed = TIMER_READ_SEC("getnextfeed");
      LOGWARN << "--- getnextfeed: " << timeElapsed << " s";
      timeElapsed = TIMER_READ_SEC("inControlThread");
      LOGWARN << "--- inControlThread: " << timeElapsed << " s";
   }

   return bd;
}

////////////////////////////////////////////////////////////////////////////////
bool PullBlockThread::pullBlockAtIter(PulledBlock& pb, LDBIter& iter,
   LMDBBlockDatabase* db, BlockFileAccessor& bfa)
{

   // Now we read the whole block, not just the header
   BinaryRefReader brr(iter.getValueReader());
   if (brr.getSize() != 16)
      return false;

   uint16_t fnum = brr.get_uint32_t();
   uint64_t offset = brr.get_uint64_t();
   uint32_t size = brr.get_uint32_t();

   pb.blockHeight_ = DBUtils::hgtxToHeight(iter.getKey().getSliceRef(1, 4));
   pb.duplicateID_ = DBUtils::hgtxToDupID(iter.getKey().getSliceRef(1, 4));

   try
   {
      BinaryDataRef bdr;
      bfa.getRawBlock(bdr, fnum, offset, size, &pb.fmp_);


      pb.unserializeFullBlock(bdr, true, false);
      pb.preprocessTx(db->armoryDbType());
      return true;
   }
   catch (exception &e)
   {
      LOGERR << "error grabbing block " <<
         pb.blockHeight_ << "|" << pb.duplicateID_ <<
         " in file #" << fnum << ", offset: " << offset <<
         ", with a size of " << size << " bytes";
      LOGERR << "error: " << e.what();

      return false;
   }
   catch (...)
   {
      LOGERR << "unknown error grabbing block " <<
         pb.blockHeight_ << "|" << pb.duplicateID_ <<
         " in file #" << fnum << ", offset: " << offset <<
         ", with a size of " << size << " bytes";
      
      return false;
   }

   return false;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockWriteBatcher::pullBlockFromDB(
   PulledBlock& pb, uint32_t height, uint8_t dup,
   BlockFileAccessor& bfa)
{
   LDBIter ldbIter = iface_->getIterator(BLKDATA);

   if (!ldbIter.seekToExact(DBUtils::getBlkMetaKey(height, dup)))
   {
      LOGERR << "Header heigh&dup is not in BLKDATA DB";
      LOGERR << "(" << height << ", " << dup << ")";
      return false;
   }

   return PullBlockThread::pullBlockAtIter(pb, ldbIter, iface_, bfa);
}

////////////////////////////////////////////////////////////////////////////////
/// ProcessedBatchSerializer
////////////////////////////////////////////////////////////////////////////////
void ProcessedBatchSerializer::updateSSHThread(
   shared_ptr<BatchThreadContainer> btc, uint32_t tID)
{
   try
   {
      uint32_t rangeStep = UINT32_MAX / btc->dataBatch_->nWriters_;
      uint32_t rangeStart = rangeStep * tID;
      uint32_t rangeEnd = rangeStep * (tID + 1);
      if (tID + 1 == btc->dataBatch_->nWriters_)
         rangeEnd = UINT32_MAX;

      uint32_t intKey;
      auto dbType = BlockWriteBatcher::armoryDbType_;
      auto pruneType = DB_PRUNE_NONE;

      auto& sshMap = btc->sshHeaders_->sshToModify_;

      for (auto& sshPair : *sshMap)
      {
         memcpy(&intKey, sshPair.first.getPtr() + 1, 4);
         if (intKey < rangeStart || intKey >= rangeEnd)
            continue;

         BinaryData sshKey;
         sshKey.append(WRITE_UINT8_LE(DB_PREFIX_SCRIPT));
         sshKey.append(sshPair.first);

         auto& ssh = sshPair.second;

         for (auto& threadData : btc->threads_)
         {
            if (threadData->subSshMap_.size() == 0)
               continue;

            auto subsshIter = threadData->subSshMap_.find(sshPair.first);
            if (subsshIter != threadData->subSshMap_.end())
            {
               for (auto& subsshPair : subsshIter->second)
               {
                  auto& subssh = subsshPair.second;
                  uint32_t subsshHeight = DBUtils::hgtxToHeight(subsshPair.first);
                  if (subsshHeight > ssh.alreadyScannedUpToBlk_ ||
                     ssh.alreadyScannedUpToBlk_ == 0 ||
                     subsshHeight >= forceUpdateSshAtHeight_)
                  {
                     for (const auto& txioPair : subssh.txioMap_)
                     {
                        auto& txio = txioPair.second;

                        if (!txio.hasTxIn())
                        {
                           if (!txio.isMultisig())
                           {
                              if (txio.isUTXO() || txio.flagged_)
                              {
                                 ssh.totalUnspent_ += txio.getValue();
                                 ssh.totalTxioCount_++;
                              }
                           }
                           else
                              ssh.totalTxioCount_++;
                        }
                        else
                        {
                           if (!txio.flagged_)
                              ssh.totalUnspent_ -= txio.getValue();
                           else
                              ssh.totalTxioCount_++;
                           ssh.totalTxioCount_++;
                        }
                     }
                  }
               }
            }
         }

         ssh.alreadyScannedUpToBlk_ = btc->highestBlockProcessed_;
      }
   }
   catch (exception &e)
   {
      LOGERR << e.what();
   }
   catch (...)
   {
      LOGERR << "unknown exception in updateSSHThread()";
   }
}

////////////////////////////////////////////////////////////////////////////////
void ProcessedBatchSerializer::updateSSH(
   shared_ptr<BatchThreadContainer> btc)
{
   TIMER_START("updateSSH");
   auto updateThread = [&btc, this](uint32_t tID)->void
   { this->updateSSHThread(btc, tID); };

   vector<thread> threadVec;

   for (uint32_t i = 1; i < btc->dataBatch_->nWriters_; i++)
      threadVec.push_back(thread(updateThread, i));
   updateThread(0);

   for (auto& thr : threadVec)
   {
      if (thr.joinable())
         thr.join();
   }
   TIMER_STOP("updateSSH");
}

////////////////////////////////////////////////////////////////////////////////
void ProcessedBatchSerializer::serializeStxo(STXOS& stxos)
{
   if (isSerialized_)
      return;

   auto dbType = BlockWriteBatcher::armoryDbType_;
   auto pruneType = DB_PRUNE_TYPE();

   for (auto& Stxo : stxos.stxoToUpdate_)
   {
      if (dbType != ARMORY_DB_SUPER)
      {
         BinaryWriter& bw = serializedStxOutToModify_[Stxo->getDBKey()];
         Stxo->serializeDBValue(bw, dbType, pruneType);
      }

      if (Stxo->isSpent())
      {
         BinaryWriter& bw = serializedSpentness_[Stxo->getDBKey(false)];
         bw.put_BinaryData(Stxo->spentByTxInKey_);
      }
      else
         spentnessToDelete_.insert(Stxo->getDBKey(false));
   }
}

////////////////////////////////////////////////////////////////////////////////
void ProcessedBatchSerializer::serializeSubSSHThread(
   shared_ptr<BatchThreadContainer> btc, uint32_t tID)
{
   uint32_t rangeStep = UINT32_MAX / btc->dataBatch_->nWriters_;
   uint32_t rangeStart = rangeStep * tID;
   uint32_t rangeEnd = rangeStep * (tID + 1);
   if (tID + 1 == btc->dataBatch_->nWriters_)
      rangeEnd = UINT32_MAX;

   uint32_t first4;
   auto& subsshtoapply = subSshToApply_[tID];

   for (auto& threadData : btc->threads_)
   {
      auto& subsshMap = threadData->subSshMap_;
      if (subsshMap.size() == 0)
         continue;

      for (auto& sshPair : subsshMap)
      {
         memcpy(&first4, sshPair.first.getPtr() + 1, 4);

         if (first4 < rangeStart || first4 >= rangeEnd)
            continue;

         uint32_t keysize = sshPair.first.getSize();
         BinaryData subkey(keysize + 4);
         memcpy(subkey.getPtr(), sshPair.first.getPtr(), keysize);

         auto& serializedSubSSH = subsshtoapply[sshPair.first];
         auto& submap = serializedSubSSH.subSshMap_;

         for (const auto& subsshPair : sshPair.second)
         {
            auto& subssh = subsshPair.second;

            if (subssh.txioMap_.size() != 0)
            {
               for (auto& txioPair : subssh.txioMap_)
               {
                  BinaryData txioKey = txioPair.second.serializeDbKey();
                  BinaryWriter& bw = submap[txioKey];

                  //do we already have a serialized txio for this key?
                  if (bw.getSize() != 0)
                  {
                     //is this txio a UTXO?
                     if (txioPair.second.isUTXO())
                        continue;

                     bw.reset();
                  }

                  txioPair.second.serializeDbValue(bw);
               }

               if (subssh.txioCount_ > 0)
               {
                  BinaryWriter &bw = submap[subsshPair.first];
                  bw.put_var_int(subssh.txioCount_);
               }
            }
            else
            {
               auto& sshdelset =
                  intermediarrySubSshKeysToDelete_[sshPair.first];
               sshdelset.insert(subssh.hgtX_);
            }

            if (subssh.keysToDelete_.size() > 0)
            {
               auto& sshdelset =
                  intermediarrySubSshKeysToDelete_[sshPair.first];
               for (auto& ktd : subssh.keysToDelete_)
                  sshdelset.insert(ktd);
            }
         }
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void ProcessedBatchSerializer::serializeSubSSH(
   shared_ptr<BatchThreadContainer> btc)
{
   auto dbType = BlockWriteBatcher::armoryDbType_;
   auto pruneType = DB_PRUNE_NONE;
   auto iface = BlockWriteBatcher::iface_;

   //subssh
   subSshToApply_.resize(btc->dataBatch_->nWriters_);

   auto serThread = [&btc, this](uint32_t tID)->void
   { this->serializeSubSSHThread(btc, tID); };

   vector<thread> serThreadIDs;
   TIMER_START("serializeSubSsh");
   for (uint32_t i = 1; i < btc->dataBatch_->nWriters_; i++)
      serThreadIDs.push_back(thread(serThread, i));
   serThread(0);

   for (auto& thr : serThreadIDs)
   {
      if (thr.joinable())
         thr.join();
   }

   TIMER_STOP("serializeSubSsh");

   //stxout
   serializeStxo(btc->commitStxos_);

   //txOutCount
   if (dbType != ARMORY_DB_SUPER)
   {
      LMDBEnv::Transaction txHints(iface->dbEnv_[TXHINTS].get(), LMDB::ReadOnly);
      for (auto& threadData : btc->threads_)
      {
         auto& txCountAndHint = threadData->txCountAndHint_;
         for (auto& txData : txCountAndHint)
         {
            BinaryWriter& bw = serializedTxCountAndHash_[txData.first];
            bw.put_uint32_t(txData.second.count_);
            bw.put_BinaryData(txData.second.hash_);

            BinaryDataRef ldbKey = txData.first.getSliceRef(1, 6);
            StoredTxHints sths;
            iface->getStoredTxHints(sths, txData.second.hash_);

            // Check whether the hint already exists in the DB
            bool needToAddTxToHints = true;
            bool needToUpdateHints = false;
            for (uint32_t i = 0; i < sths.dbKeyList_.size(); i++)
            {
               if (sths.dbKeyList_[i] == ldbKey)
               {
                  needToAddTxToHints = false;
                  needToUpdateHints = (sths.preferredDBKey_ != ldbKey);
                  sths.preferredDBKey_ = ldbKey;
                  break;
               }
            }

            // Add it to the hint list if needed
            if (needToAddTxToHints)
            {
               sths.dbKeyList_.push_back(ldbKey);
               sths.preferredDBKey_ = ldbKey;
            }

            if (needToAddTxToHints || needToUpdateHints)
            {
               BinaryWriter& bwHints = serializedTxHints_[sths.getDBKey()];
               sths.serializeDBValue(bwHints);
            }
         }
      }
   }

   topBlockHash_ = btc->topScannedBlockHash_;
   mostRecentBlockApplied_ = btc->highestBlockProcessed_ + 1;
}

////////////////////////////////////////////////////////////////////////////////
void ProcessedBatchSerializer::serializeSSH(
   shared_ptr<BatchThreadContainer> btc)
{
   try
   {
      uint32_t nthreads = btc->dataBatch_->nWriters_ / 2;
      if (nthreads < 1)
         nthreads = 1;

      auto serializeThread = [&nthreads, &btc, this](uint32_t tID)->void
      {
         try
         {
            uint32_t rangeStep = UINT32_MAX / nthreads;
            uint32_t rangeStart = rangeStep * tID;
            uint32_t rangeEnd = rangeStep * (tID + 1);
            if (tID + 1 == nthreads)
               rangeEnd = UINT32_MAX;
            uint32_t shortKey;

            auto dbType = BlockWriteBatcher::armoryDbType_;
            auto pruneType = DB_PRUNE_NONE;

            auto& sshMap = btc->sshHeaders_->sshToModify_;

            for (auto& sshPair : *sshMap)
            {
               shortKey = *(reinterpret_cast<const uint32_t*>(sshPair.first.getPtr() + 1));
               if (shortKey < rangeStart || shortKey > rangeEnd)
                  continue;

               BinaryData sshKey;
               sshKey.append(WRITE_UINT8_LE(DB_PREFIX_SCRIPT));
               sshKey.append(sshPair.first);

               auto& ssh = sshPair.second;
               if (dbType == ARMORY_DB_SUPER)
               {
                  if (ssh.totalTxioCount_ > 0)
                  {
                     BinaryWriter& bw = serializedSshToModify_[tID][sshKey];
                     ssh.serializeDBValue(bw, dbType, pruneType);
                  }
                  else
                     sshKeysToDelete_.insert(sshKey);
               }
               else
               {
                  BinaryWriter& bw = serializedSshToModify_[tID][sshKey];
                  ssh.serializeDBValue(bw, dbType, pruneType);
               }
            }

            //save top prefix values for each key
            for (auto& topPrefix : btc->sshHeaders_->topPrefix_)
            {
               const BinaryData& bdPrefix = topPrefix.first;
               int32_t keySize = min(4, (int)bdPrefix.getSize() - 1);
               memcpy(&shortKey, bdPrefix.getPtr() + 1, keySize);

               if (shortKey < rangeStart || shortKey >= rangeEnd)
                  continue;

               auto& submap = prefixesToUpdate_[tID][bdPrefix.getSize()];
               submap[bdPrefix] = topPrefix.second.first;
            }
         }
         catch (exception &e)
         {
            LOGERR << e.what();
         }
         catch (...)
         {
            LOGERR << "unknown exception in serializeThread()";
         }
      };

      serializedSshToModify_.resize(nthreads);
      prefixesToUpdate_.resize(nthreads);

      vector<thread> threadVec;
      for (uint32_t i = 1; i < nthreads; i++)
         threadVec.push_back(thread(serializeThread, i));
      serializeThread(0);

      for (auto& thr : threadVec)
      {
         if (thr.joinable())
            thr.join();
      }
   }
   catch (exception &e)
   {
      LOGERR << e.what();
   }
   catch (...)
   {
      LOGERR << "unknown exception in serializeSSH()";
   }
}

////////////////////////////////////////////////////////////////////////////////
void ProcessedBatchSerializer::finalizeSerialization(
   shared_ptr<BatchThreadContainer> btc)
{
   TIMER_START("finalizeSerialization");

   auto serializeSSH = [&btc, this](void)->void
   { this->serializeSSH(btc); };
   thread finishSSHThread(serializeSSH);

   for (auto& ssh : *btc->sshHeaders_->sshToModify_)
      sshKeys_[ssh.first] = ssh.second.getSubKey();

   //set ssh key for each subssh entry
   for (auto& subsshtoapply : subSshToApply_)
   {
      for (auto& serSubSsh : subsshtoapply)
      {
         auto keyIter = sshKeys_.find(serSubSsh.first);
         if (keyIter == sshKeys_.end())
            continue;

         auto& key = keyIter->second;
         size_t keySize = key.getSize();
         serSubSsh.second.sshKey_ = key;

         BinaryData subKey(keySize + 8);
         keyedSubSshToApply_[keySize].push_back(&serSubSsh.second);
      }
   }

   for (auto& ktdSet : intermediarrySubSshKeysToDelete_)
   {
      auto& sshkey = sshKeys_[ktdSet.first];
      size_t keySize = sshkey.getSize();

      auto& subset = subSshKeysToDelete_[keySize];
      BinaryData subKey(keySize + 8);
      memcpy(subKey.getPtr(), sshkey.getPtr(), keySize);

      for (auto& ktd : ktdSet.second)
      {
         if (ktd.getSize() == 8)
         {
            memcpy(subKey.getPtr() + keySize, ktd.getPtr(), 8);
            subset.insert(subKey);
         }
         else
         {
            BinaryData ktdbd(sshkey);
            ktdbd.append(ktd);
            subset.insert(ktdbd);
         }
      }
   }

   TIMER_START("waitOnSSHser");
   if (finishSSHThread.joinable())
      finishSSHThread.join();
   TIMER_STOP("waitOnSSHser");

   isSerialized_ = true;
   TIMER_STOP("finalizeSerialization");
}

////////////////////////////////////////////////////////////////////////////////
void ProcessedBatchSerializer::serializeBatch(
   shared_ptr<BatchThreadContainer> btc, 
   unique_lock<mutex>* serializeLock)
{
   try
   {
      if (isSerialized_)
         return;

      TIMER_START("serializeBatch");

      uint32_t nThreads = btc->dataBatch_->nWriters_;
      btc->sshHeaders_ = make_shared<SSHheaders>(nThreads, btc->commitId_);

      auto serialize = [&](void)
      { serializeSubSSH(btc); };

      thread serThread = thread(serialize);

      {
         TIMER_START("getSshHeaders");
         unique_lock<mutex> lock;
         auto newSSH = btc->sshHeaders_->getSshHeaders(btc, lock);
         TIMER_STOP("getSshHeaders");

         auto getNewSSHKeys = [&btc, &newSSH](void)->void
         { btc->sshHeaders_->computeDBKeys(newSSH); };

         thread getNewSSHKeysThread(getNewSSHKeys);
         updateSSH(btc);

         if (getNewSSHKeysThread.joinable())
            getNewSSHKeysThread.join();

         btc->serializeCV_.notify_all();

         serializeLock->unlock();
      }

      if (serThread.joinable())
         serThread.join();

      TIMER_STOP("serializeBatch");

      finalizeSerialization(btc);
   }
   catch (exception &e)
   {
      LOGERR << e.what();
   }
   catch (...)
   {
      LOGERR << "unknown exception in serializeBatch()";
   }
}

////////////////////////////////////////////////////////////////////////////////
void ProcessedBatchSerializer::putSSH()
{
   LMDBEnv::Transaction tx;
   auto db = BlockWriteBatcher::iface_;
   db->beginDBTransaction(&tx, HISTORY, LMDB::ReadWrite);

   auto putThread = [this](uint32_t keyLength)->void
   { this->putSubSSH(keyLength); };

   vector<thread> subSshThreads;
   for (auto& submap : keyedSubSshToApply_)
      subSshThreads.push_back(thread(putThread, submap.first));

   for (auto& sshMap : serializedSshToModify_)
   {
      for (auto& sshPair : sshMap)
         db->putValue(HISTORY, sshPair.first, sshPair.second.getData());
   }

   for (auto& writeThread : subSshThreads)
      if (writeThread.joinable())
         writeThread.join();
}

////////////////////////////////////////////////////////////////////////////////
void ProcessedBatchSerializer::putSubSSH(uint32_t keyLength)
{
   try
   {
      LMDBEnv::Transaction subsshtx;
      auto db = BlockWriteBatcher::iface_;

      db->beginSubSSHDBTransaction(subsshtx,
         keyLength, LMDB::ReadWrite);

      //update prefixes
      BinaryData prefixVal(1);
      for (auto& prefixV : prefixesToUpdate_)
      {
         auto& prefixMap = prefixV[keyLength];

         for (auto& prefix : prefixMap)
         {
            prefixVal.getPtr()[0] = prefix.second;
            db->putValue(keyLength, prefix.first, prefixVal);
         }
      }

      //put subssh data
      auto& subsshvec = keyedSubSshToApply_[keyLength];

      vector<uint8_t> subkey(keyLength + 16);
      for (auto subsshentry : subsshvec)
      {
         //copy prefix in key object
         memcpy(&subkey[0], subsshentry->sshKey_.getPtr(), keyLength);

         for (auto& subssh : subsshentry->subSshMap_)
         {
            //copy hgtx in key object
            memcpy(&subkey[0] + keyLength,
               subssh.first.getPtr(), subssh.first.getSize());

            db->putValue(keyLength,
               BinaryDataRef(&subkey[0], keyLength + subssh.first.getSize()),
               subssh.second.getData());
         }
      }
   }
   catch (exception &e)
   {
      LOGERR << e.what();
   }
   catch (...)
   {
      LOGERR << "unknown exception in putSubSSH()";
   }
}

////////////////////////////////////////////////////////////////////////////////
void ProcessedBatchSerializer::putSTX()
{
   auto db = BlockWriteBatcher::iface_;

   if (serializedStxOutToModify_.size() > 0)
   {
      LMDBEnv::Transaction tx(db->dbEnv_[STXO].get(), LMDB::ReadWrite);

      for (auto& stxoPair : serializedStxOutToModify_)
         db->putValue(STXO, stxoPair.first, stxoPair.second.getData());
   }

   {
      LMDBEnv::Transaction tx(db->dbEnv_[SPENTNESS].get(), LMDB::ReadWrite);

      for (auto& spentness : serializedSpentness_)
         db->putValue(SPENTNESS, spentness.first, spentness.second.getData());

      for (auto& delKey : spentnessToDelete_)
         db->deleteValue(SPENTNESS, delKey);
   }
   
   if (BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER)
      return;
   
   {
      LMDBEnv::Transaction tx(db->dbEnv_[HISTORY].get(), LMDB::ReadWrite);

      for (auto& txCount : serializedTxCountAndHash_)
         db->putValue(HISTORY, txCount.first, txCount.second.getData());

      ////
      LMDBEnv::Transaction txHints(db->dbEnv_[TXHINTS].get(), LMDB::ReadWrite);
      for (auto& txHints : serializedTxHints_)
      db->putValue(TXHINTS, txHints.first, txHints.second.getData());
   }
}

////////////////////////////////////////////////////////////////////////////////
void ProcessedBatchSerializer::deleteEmptyKeys()
{
   auto db = BlockWriteBatcher::iface_;
   
   {
      LMDBEnv::Transaction tx;
      db->beginDBTransaction(&tx, HISTORY, LMDB::ReadWrite);

      for (auto& toDel : sshKeysToDelete_)
         db->deleteValue(HISTORY, toDel.getRef());
   }

   for (auto& subset : subSshKeysToDelete_)
   {
      uint32_t keySize = subset.first;

      LMDBEnv::Transaction subtx;
      db->beginSubSSHDBTransaction(subtx, keySize, LMDB::ReadWrite);

      for (auto& ktd : subset.second)
         db->deleteValue(keySize, ktd.getRef());
   }
}

////////////////////////////////////////////////////////////////////////////////
void ProcessedBatchSerializer::updateSDBI()
{
   auto db = BlockWriteBatcher::iface_;

   LMDBEnv::Transaction tx;
   db->beginDBTransaction(&tx, HISTORY, LMDB::ReadWrite);

   StoredDBInfo sdbi;
   db->getStoredDBInfo(HISTORY, sdbi);
   if (!sdbi.isInitialized())
      LOGERR << "How do we have invalid SDBI in applyMods?";
   else
   {
      //save top block height
      sdbi.appliedToHgt_ = mostRecentBlockApplied_;

      //save top block hash
      if (topBlockHash_ != BtcUtils::EmptyHash_)
         sdbi.topScannedBlkHash_ = topBlockHash_;

      db->putStoredDBInfo(HISTORY, sdbi);
   }
}

////////////////////////////////////////////////////////////////////////////////
ProcessedBatchSerializer::ProcessedBatchSerializer(
   ProcessedBatchSerializer&& dtc)
{
   keyedSubSshToApply_              = move(dtc.keyedSubSshToApply_);
   serializedSshToModify_           = move(dtc.serializedSshToModify_);
   serializedStxOutToModify_        = move(dtc.serializedStxOutToModify_);
   sshKeysToDelete_                 = move(dtc.sshKeysToDelete_);
   subSshKeysToDelete_              = move(dtc.subSshKeysToDelete_);
   serializedSpentness_             = move(dtc.serializedSpentness_);
   spentnessToDelete_               = move(dtc.spentnessToDelete_);
   sshKeys_                         = move(dtc.sshKeys_);
   subSshToApply_                   = move(dtc.subSshToApply_);
   intermediarrySubSshKeysToDelete_ = move(dtc.intermediarrySubSshKeysToDelete_);
   prefixesToUpdate_                = move(dtc.prefixesToUpdate_);
   
   //Fullnode only
   serializedTxCountAndHash_ = move(dtc.serializedTxCountAndHash_);
   serializedTxHints_ = move(dtc.serializedTxHints_);

   topBlockHash_ = move(dtc.topBlockHash_);
}

////////////////////////////////////////////////////////////////////////////////
uint32_t ProcessedBatchSerializer::getProcessSSHnThreads(void) const
{
   if (BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER)
      return 5;

   return 1;
}

////////////////////////////////////////////////////////////////////////////////
/// STXOS
////////////////////////////////////////////////////////////////////////////////
void STXOS::moveStxoToUTXOMap(
   const shared_ptr<StoredTxOut>& thisTxOut)
{
   if (BlockWriteBatcher::armoryDbType_ != ARMORY_DB_SUPER)
      stxoToUpdate_.push_back(thisTxOut);

   utxoMap_[thisTxOut->hashAndId_] = thisTxOut;
}

////////////////////////////////////////////////////////////////////////////////
StoredTxOut* STXOS::getStoredTxOut(const BinaryData& txHash, uint16_t utxoid)
{
   shared_ptr<StoredTxOut> stxo(new StoredTxOut());
   BinaryData dbKey;

   if (!BlockWriteBatcher::iface_->getStoredTx_byHash(txHash, nullptr, &dbKey))
      return nullptr;

   dbKey.append(WRITE_UINT16_BE(utxoid));
   if (!BlockWriteBatcher::iface_->getStoredTxOut(*stxo, dbKey))
      return nullptr;

   stxoToUpdate_.push_back(stxo);
   return stxo.get();
}

////////////////////////////////////////////////////////////////////////////////
StoredTxOut* STXOS::lookForUTXOInMap(const BinaryData& hashAndId, 
   bool forceFetch)
{
   //TIMER_START("leverageUTXOinRAM");

   //look in thread's local utxo map
   auto utxoIter = utxoMap_.find(hashAndId);
   if (utxoIter != utxoMap_.end())
   {
      stxoToUpdate_.push_back(utxoIter->second);

      utxoMap_.erase(utxoIter);
      //TIMER_STOP("leverageUTXOinRAM");
      return stxoToUpdate_.back().get();
   }

   if (parent_ != nullptr)
   {
      //look in global utxo map
      auto stxoIter = parent_->utxoMap_.find(hashAndId);
      if (stxoIter != parent_->utxoMap_.end())
      {
         stxoToUpdate_.push_back(stxoIter->second);
         keysToDelete_.push_back(stxoIter->first);

         return stxoToUpdate_.back().get();
      }
      
      //look in global utxo map about to be flushed from ram
      if (utxoMapBackup_ != 0 && utxoMapBackup_->size() > 0)
      {
         stxoIter = utxoMapBackup_->find(hashAndId);
         if (stxoIter != utxoMapBackup_->end())
         {
            stxoToUpdate_.push_back(stxoIter->second);

            return stxoToUpdate_.back().get();
         }
      }

      //look in BlockDataFeed stxo map
      stxoIter = parent_->feedStxos_->find(hashAndId);
      if (stxoIter != parent_->feedStxos_->end())
      {
         //The feed stxo container is does not filter entries by scrAddr.
         //In Fullnode this means we have to check the stxo's scrAddr against
         //the list of registered ones to make sure this address belongs to our
         //wallet.
         if (BlockWriteBatcher::armoryDbType_ != ARMORY_DB_SUPER)
         {
            const BinaryData& scrAddr = stxoIter->second->getScrAddress();
            if (!BlockWriteBatcher::scrAddrFilter_->hasScrAddress(scrAddr))
               return nullptr;
         }

         stxoToUpdate_.push_back(stxoIter->second);
         return stxoToUpdate_.back().get();
      }
   }


   //TIMER_STOP("leverageUTXOinRAM");

   if (BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER || forceFetch)
   {
      //TIMER_START("lookforutxo");

      shared_ptr<StoredTxOut> stxo(new StoredTxOut);
      BinaryData dbKey;
      if (!BlockWriteBatcher::iface_->getStoredTx_byHash(
         hashAndId.getSliceRef(0, 32), nullptr, &dbKey))
      {
         if (BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER)
         {
            LOGERR << "missing txhint in supenode";
            throw runtime_error("missing txhint in supernode");
         }
         else
            return nullptr;
      }

      uint32_t txoId = READ_UINT16_BE(hashAndId.getPtr() + 32);
      dbKey.append(WRITE_UINT16_BE(txoId));
      if (!BlockWriteBatcher::iface_->getUnspentTxOut(*stxo, dbKey, false))
      {
         if (BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER)
         {
            LOGERR << "missing stxo in supenode";
            throw runtime_error("missing txhint in supernode");
         }
         else
            return nullptr;
      }

      stxoToUpdate_.push_back(stxo);
      
      //TIMER_STOP("lookforutxo");

      return stxoToUpdate_.back().get();
   }

   return nullptr;
}

////////////////////////////////////////////////////////////////////////////////
thread STXOS::commitStxo(shared_ptr<BatchThreadContainer> btc)
{
   //create commiting object and fill it up
   shared_ptr<STXOS> toCommit(new STXOS(*this));
   
   //clean up spent txouts from the utxo map, move stxos to update in the 
   //commiting object containers
   for (auto& threadData : btc->threads_)
   {
      auto& keysToDelete = threadData->stxos_.keysToDelete_;
      for (auto& key : keysToDelete)
         utxoMap_.erase(key);
   }

   if (utxoMap_.size() > UTXO_THRESHOLD &&
       BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER)
   {
      //utxoMap is getting too big, let's move data to the backup and clear
      //it
      toCommit->utxoMapBackup_ = utxoMapBackup_;
      utxoMapBackup_.reset(new map<BinaryData, shared_ptr<StoredTxOut>>());
      *utxoMapBackup_ = move(utxoMap_);
   }

   for (auto& threadData : btc->threads_)
   {
      toCommit->stxoToUpdate_.insert(toCommit->stxoToUpdate_.end(),
         std::make_move_iterator(threadData->stxos_.stxoToUpdate_.begin()), 
         std::make_move_iterator(threadData->stxos_.stxoToUpdate_.end()));
   }

   //add cumulated utxos of each thread to the utxo map
   for (auto& threadData : btc->threads_)
   {
      auto& stxo = threadData->stxos_;
      utxoMap_.insert(
         std::make_move_iterator(stxo.utxoMap_.begin()), 
         std::make_move_iterator(stxo.utxoMap_.end()));
   }

   /***
   utxoMapBackup_ has to be valid until its corresponding write thread has
   completed and the db RO transaction has been recycled. The simplest way
   to make sure the containers remain consistent accross threads is to wait
   on the write mutex
   ***/
   
   thread committhread(writeStxoToDB, toCommit);
   return committhread;
}

////////////////////////////////////////////////////////////////////////////////
void STXOS::commit(shared_ptr<BatchThreadContainer> btc)
{
   if (committhread_.joinable())
      committhread_.detach();
   committhread_ = commitStxo(btc);
}

////////////////////////////////////////////////////////////////////////////////
void STXOS::writeStxoToDB(shared_ptr<STXOS> stxos)
{
   {
      TIMER_START("writeStxo_grabMutex");
      unique_lock<mutex> writeLock(stxos->parent_->writeMutex_);
      TIMER_STOP("writeStxo_grabMutex");
      {
         LMDBBlockDatabase *db = BlockWriteBatcher::iface_;
         stxos->processedBatchSerializer_.serializeStxo(*stxos);

         stxos->processedBatchSerializer_.putSTX();
      }
   }

   stxos.reset();
}

////////////////////////////////////////////////////////////////////////////////
//// BlockDataBatchLoader
////////////////////////////////////////////////////////////////////////////////
BlockDataBatchLoader::BlockDataBatchLoader(BlockWriteBatcher *bwbPtr, 
   uint32_t nthreads, 
   shared_ptr<BlockDataBatchLoader> prevLoader) :
   bwbPtr_(bwbPtr), scrAddrFilter_(*BlockWriteBatcher::scrAddrFilter_),
   BFA_(BlockWriteBatcher::iface_->getBlkFiles(), getPrefetchMode()),
      nThreads_(nthreads)
{
   startBlock_ = bwbPtr->startBlock_;
   endBlock_ = bwbPtr->endBlock_;
   currentHeight_ = bwbPtr->startBlock_;

   interruptBlock_ = make_shared<PulledBlock>();
   interruptBlock_->nextBlock_ = interruptBlock_;

   pullThreads_.resize(nThreads_);

   if (prevLoader != nullptr)
   {
      /***If the ctor is provided a previous loader, let's bootstrap this
      object off of it.
      ***/

      if (startBlock_ < endBlock_)
      {
         startBlock_ = prevLoader->currentHeight_ + 1;
         currentHeight_ = prevLoader->currentHeight_ + 1;
      }
      else
      {
         startBlock_ = prevLoader->currentHeight_ - 1;
         currentHeight_ = prevLoader->currentHeight_ - 1;
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataBatchLoader::terminate(void)
{
   terminate_.store(true, memory_order_release);
   for (auto& pullthr : pullThreads_)
   {
      if (pullthr.tID_.joinable())
         pullthr.tID_.join();
   }
}

////////////////////////////////////////////////////////////////////////////////
BlockDataBatchLoader::~BlockDataBatchLoader(void)
{
   interruptBlock_->nextBlock_.reset();
   interruptBlock_.reset();
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<PulledBlock> BlockDataBatchLoader::getNextBlock(
   unique_lock<mutex>* mu)
{
   if (!isHeightValid(*this, currentHeight_))
      return nullptr;

   shared_ptr<PulledBlock> blk;
   PullBlockThread& pullThread = pullThreads_[currentHeight_ % nThreads_];

   while (1)
   {
      {
         unique_lock<mutex> assignLock(pullThread.assignLock_);
         blk = pullThread.block_->nextBlock_;
      }

      if (blk != nullptr)
         break;

      //wakeGrabThreads in case they are sleeping
      wakePullThreadsIfNecessary();

      //wait for grabThread signal
      pullCV_.wait_for(*mu, chrono::seconds(2));
   }

   pullThread.block_->nextBlock_.reset();
   pullThread.block_ = blk;

   //decrement bufferload
   pullThread.bufferLoad_.fetch_sub(
      blk->numBytes_, memory_order_release);

   if (startBlock_ <= endBlock_)
      currentHeight_++;
   else
      currentHeight_--;

   return blk;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<BlockDataBatch> BlockDataBatchLoader::chargeNextBatch(
   uint32_t nReaders, uint32_t nWorkers, uint32_t nWriters)
{
   shared_ptr<BlockDataBatch> nextBatch = 
      make_shared<BlockDataBatch>(nReaders, nWorkers, nWriters);
   nextBatch->chargeBatch(*this);

   bwbPtr_->pushBatch(nextBatch);

   return nextBatch;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataBatchLoader::startPullThreads(
   shared_ptr<BlockDataBatchLoader>& bdb)
{
   for (uint32_t i = 0; i < nThreads_; i++)
      bdb->pullThreads_[i].tID_ = thread(PullBlockThread::pullThread, bdb, i);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataBatchLoader::wakePullThreadsIfNecessary()
{
   for (uint32_t i = 0; i < nThreads_; i++)
   {
      if (pullThreads_[i].bufferLoad_.load(memory_order_consume) <
         BYTES_PER_BATCH / (nThreads_ * 2))
      {
         /***
         Buffer is running low. Try to take ownership of the blockData
         mutex. If that succeeds, the grab thread is sleeping, so
         signal it to wake. Otherwise the grab thread is already running
         and is lagging behind the processing thread (very unlikely)
         ***/

         unique_lock<mutex> lock(pullThreads_[i].grabLock_, defer_lock);
         if (lock.try_lock())
            pullThreads_[i].grabCV_.notify_all();
      }
   }
}


////////////////////////////////////////////////////////////////////////////////
//// BlockDataFeed
////////////////////////////////////////////////////////////////////////////////
void BlockDataBatch::chargeBatch(BlockDataBatchLoader& blockBatch)
{
   shared_ptr<PulledBlock> block;
   shared_ptr<PulledBlock> lastValidBlock;

   unique_lock<mutex> scanLock(blockBatch.pullLock_);

   size_t sizePerThread = BYTES_PER_BATCH / nWorkers_;

   totalSizeInBytes_ = 0;
   uint32_t i = 0, lowestBlockHeight = UINT32_MAX;
   uint32_t txoutCount = 0;

   batchStxos_ = make_shared<map<BinaryData, shared_ptr<StoredTxOut>>>();

   readTime_ = clock();

   while (1)
   {
      block = blockBatch.getNextBlock(&scanLock);

      if (block == nullptr)
         break;

      //check if next block is valid
      if (block == blockBatch.interruptBlock_)
      {
         /*string errorMessage("The scanning process "
            "interrupted unexpectedly, Armory will now shutdown. "
            "You will have to proceed to \"Help -> Rebuild and Rescan\" "
            "on the next start. If the error persists, contact support. "
            "Refer to your log file for more details on the error.");

         BlockWriteBatcher::criticalError(errorMessage);*/
         hasData_ = false;
         return;
      }

      if (block->blockHeight_ < lowestBlockHeight)
         lowestBlockHeight = block->blockHeight_;
      lastValidBlock = block;
      hasData_ = true;


      uint32_t blockSize = block->numBytes_;
      for (auto& tx : block->stxMap_)
         txoutCount += tx.second.numTxOut_;

      
      uint32_t rotation = 0;
      while (rotation < nWorkers_)
      {
         uint32_t currThread = (i + rotation) % nWorkers_;

         if (blockPackets_[currThread].byteSize_ < sizePerThread)
         {
            blockPackets_[currThread].blocks_.push_back(block);
            blockPackets_[currThread].byteSize_ += blockSize;
            break;
         }

         rotation++;
      }

      if (rotation > nWorkers_)
      {
         uint32_t currThread = i % nWorkers_;

         blockPackets_[currThread].blocks_.push_back(block);
         blockPackets_[currThread].byteSize_ += blockSize;
         break;
      }

      //fill up feed stxo container
      for (auto& stx : block->stxMap_)
      {
         for (auto& stxo : stx.second.stxoMap_)
         {
            (*batchStxos_)[stxo.second->hashAndId_] = stxo.second;
         }
      }

      totalSizeInBytes_ += block->numBytes_;
      if (totalSizeInBytes_ >= BYTES_PER_BATCH ||
         txoutCount > TXOUT_PER_BATCH)
         break;

      i++;
   }

   if (lastValidBlock != nullptr)
   {
      topBlockHeight_ = 
         BlockDataBatchLoader::getTopHeight(blockBatch, *lastValidBlock);

      topBlockHash_ = 
         BlockDataBatchLoader::getTopHash(blockBatch, *lastValidBlock);

      bottomBlockHeight_ = lowestBlockHeight;
   }

   readTime_ = clock() - readTime_;
}

////////////////////////////////////////////////////////////////////////////////
//// BlockDataProcesser
////////////////////////////////////////////////////////////////////////////////
BlockBatchProcessor::BlockBatchProcessor(
   BlockWriteBatcher* const bwbPtr, bool undo)
   : bwbPtr_(bwbPtr), undo_(undo)
{
   if (bwbPtr == nullptr)
      throw runtime_error(
         "bad BlockWriteBatcher pointer in BlockBatchProcessor ctor");
   
   commitedId_.store(0);

   if (undo)
   {
      sshHeaders_.reset(new SSHheaders(1, 0));
      sshHeaders_->sshToModify_.reset(
         new map<BinaryData, StoredScriptHistory>());
   }
}

////////////////////////////////////////////////////////////////////////////////
thread BlockBatchProcessor::startThreads()
{
   
   auto processThread = [this](void)->void
   { this->processBlockData(); };

   thread tID(processThread);
   return tID;
}

////////////////////////////////////////////////////////////////////////////////
void BlockBatchProcessor::processBlockData()
{
   try
   {
      TIMER_START("inControlThread");

      auto writeData = [this](void)->void
      { writeThread(); };
      thread writethread(writeData);

      shared_ptr<BlockDataBatch> dataBatch;
      while (1)
      {
         TIMER_START("getnextfeed");
         dataBatch = bwbPtr_->popBatch();
         TIMER_STOP("getnextfeed");
         if (dataBatch == nullptr)
            break;

         stxos_.feedStxos_ = dataBatch->batchStxos_;
         worker_ = make_shared<BatchThreadContainer>(this, dataBatch);

         for (auto threadData : worker_->threads_)
         {
            if (threadData->tID_.joinable())
               threadData->tID_.join();
         }

         worker_->workTime_ = clock() - worker_->workTime_;

         //all workers are done, commit the processed data
         worker_->highestBlockProcessed_ = dataBatch->topBlockHeight_;
         worker_->lowestBlockProcessed_ = dataBatch->bottomBlockHeight_;
         worker_->topScannedBlockHash_ = dataBatch->topBlockHash_;
         dataBatch.reset();

         TIMER_START("writeStxo");
         stxos_.commit(worker_);
         TIMER_STOP("writeStxo");

         commit();
      }

      {
         //shutdown write thread
         unique_lock<mutex> writeLock(writeMutex_);
         writeMap_[commitId_] = nullptr;
         writeCV_.notify_all();
      }

      if (stxos_.committhread_.joinable())
         stxos_.committhread_.join();
      if (writethread.joinable())
         writethread.join();

      TIMER_STOP("inControlThread");
   }
   catch (exception &e)
   {
      LOGERR << e.what();
   }
   catch (...)
   {
      LOGERR << "unexpected error in processBlockData()";
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockBatchProcessor::commit()
{
   //set writer_ as worker_ then reset it. We'll create a new worker_ in the
   //processBlockData loop
   shared_ptr<BatchThreadContainer> commitObject = worker_;
   worker_.reset();

   auto serThread = [this](shared_ptr<BatchThreadContainer> bdc)->void
   { serializeData(bdc); };
   unique_lock<mutex> lock(commitObject->serializeMutex_);
   thread serializeThread(serThread, commitObject);
   if (serializeThread.joinable())
      serializeThread.detach();

   TIMER_START("waitingOnSerThread");
   commitObject->serializeCV_.wait(lock);
   TIMER_STOP("waitingOnSerThread");

   currentSSHheaders_ = commitObject->sshHeaders_;
}


////////////////////////////////////////////////////////////////////////////////
void BlockBatchProcessor::serializeData(shared_ptr<BatchThreadContainer> bdc)
{
   try
   {
      unique_lock<mutex> serializeLock(bdc->serializeMutex_);

      {
         //This is the write queue bottleneck. The serialize thread will block
         //the process until there is less then 2 processed batch in the 
         //write queue.

         //This bottleneck, along with the one at the batch loader level, guarantees
         //that there won't be more than (MAX_BATCH_BUFFER*2 +2) batches in RAM at 
         //any point in time.
         TIMER_START("waitOnWriteThread");
         unique_lock<mutex> lock(writeMutex_);
         if (writeMap_.size() >= MAX_BATCH_BUFFER)
            writeCV_.wait(lock);
         TIMER_STOP("waitOnWriteThread");
      }

      //bdc->writeTime_ = clock();
      shared_ptr<SSHheaders> headersPtr =
         bdc->processor_->currentSSHheaders_;

      shared_ptr<ProcessedBatchSerializer> pbs =
         make_shared<ProcessedBatchSerializer>();
      if (bdc->processor_->forceUpdateSSH_)
      {
         pbs->forceUpdateSshAtHeight_ =
            bdc->lowestBlockProcessed_;
      }

      pbs->serializeBatch(bdc, &serializeLock);

      bdc->processedBatchSerializer_ = pbs;

      unique_lock<mutex> writerLock(writeMutex_);
      writeMap_[bdc->commitId_] = bdc;

      //notify write thread that a new batch is in the write queue
      writeCV_.notify_all();
   }
   catch (exception &e)
   {
      LOGERR << e.what();
   }
   catch (...)
   {
      LOGERR << "unknown exception in serializeData()";
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockBatchProcessor::writeThread()
{
   auto cleanUpThread = [](shared_ptr<BatchThreadContainer> btc)->void
   {
      try
      {
         btc->threads_.clear();
         btc->processedBatchSerializer_.reset();
         btc->sshHeaders_.reset();
         btc->dataBatch_.reset();
      }
      catch (exception &e)
      {
         LOGERR << e.what();
      }
      catch (...)
      {
         LOGERR << "unknown exception in cleanUpThread()";
      }
   };

   try
   {
      while (1)
      {
         uint32_t currentId = commitedId_.load(memory_order_relaxed);
         shared_ptr<BatchThreadContainer> commitObject = nullptr;

         while (1)
         {
            unique_lock<mutex> lock(writeMutex_);
            auto iter = writeMap_.find(currentId);
            if (iter != writeMap_.end())
            {
               commitObject = iter->second;
               writeMap_.erase(iter);
               //writeCV_.notify_all();
               break;
            }

            TIMER_START("waitForDataToWrite");
            writeCV_.wait(lock);
            TIMER_STOP("waitForDataToWrite");
         }

         //nullptr marks the bottom of the write list
         if (commitObject == nullptr)
            return;

         //notify the writeCV in case the serialize thread was waiting on it
         //to push the next processed batch in the write queue.
         writeCV_.notify_all();

         commitObject->writeTime_ = clock();
         TIMER_START("putSSH");
         commitObject->processedBatchSerializer_->putSSH();
         TIMER_STOP("putSSH");

         TIMER_START("putSTX");
         commitObject->processedBatchSerializer_->putSTX();
         TIMER_STOP("putSTX");

         commitObject->processedBatchSerializer_->deleteEmptyKeys();

         if (commitObject->highestBlockProcessed_ != 0 &&
            commitObject->updateSDBI_ == true)
            commitObject->processedBatchSerializer_->updateSDBI();

         lastScannedBlockHash_ = commitObject->topScannedBlockHash_;

         commitedId_.fetch_add(1, memory_order_release);
         commitObject->writeTime_ = clock() - commitObject->writeTime_;
         commitObject->processor_->adjustThreadCount(commitObject);

         thread cleanup(cleanUpThread, commitObject);
         if (cleanup.joinable())
            cleanup.detach();
      }
   }
   catch (exception &e)
   {
      LOGERR << e.what();
   }
   catch (...)
   {
      LOGERR << "unknown exception in writeThread()";
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockBatchProcessor::adjustThreadCount(
   shared_ptr<BatchThreadContainer> btc)
{
   /***The idea is to write the processed data in parallel of the worker.
   To achieve this, we adjust threads per task in an attempt to keep the 
   write time below the work time, while keeping the work time as low as
   possible.
   ***/

   uint32_t nreaders = btc->dataBatch_->nReaders_;
   uint32_t nworkers = btc->dataBatch_->nWorkers_;
   uint32_t nwriters = btc->dataBatch_->nWriters_;
   uint32_t totalThreadCount = bwbPtr_->totalThreadCount_;

   uint32_t newWriterCount, newWorkerCount, newReaderCount;

   cumulatedReadTime_  += btc->dataBatch_->readTime_;
   cumulatedWorkTime_  += btc->workTime_;
   cumulatedWriteTime_ += btc->writeTime_;
   cumulatedBatchSleep_ += btc->dataBatch_->chargeSleep_;
   cumulatedCount_++;

   if (cumulatedCount_ != 10)
      return;

   uint64_t totalTime = 
      cumulatedReadTime_ + cumulatedWorkTime_ + cumulatedWriteTime_;

   float readRatio  = (float)cumulatedReadTime_  / (float)totalTime;
   float workRatio  = (float)cumulatedWorkTime_  / (float)totalTime;
   float writeRatio = (float)cumulatedWriteTime_ / (float)totalTime;

   float readWeight  = readRatio  * (float)nreaders;
   float workWeight  = workRatio  * (float)nworkers;
   float writeWeight = writeRatio * (float)nwriters;

   float totalWeight = readWeight + workWeight + writeWeight;
   readRatio  = readWeight  / totalWeight;
   workRatio  = workWeight  / totalWeight;
   writeRatio = writeWeight / totalWeight;

   newReaderCount = uint32_t(floor(readRatio  * (float)totalThreadCount + 0.5f));
   newWorkerCount = uint32_t(floor(workRatio  * (float)totalThreadCount + 0.5f));
   newWriterCount = uint32_t(floor(writeRatio * (float)totalThreadCount + 0.5f));

   if (newReaderCount == 0)
      newReaderCount = 1;

   if (newWorkerCount == 0)
      newWorkerCount = 1;

   if (newWriterCount == 0)
      newWriterCount = 1;

  /* LOGINFO << " &&&&&&&&& cumulatedReadTime: " << (float)cumulatedReadTime_ / (float)CLOCKS_PER_SEC << "s";
   LOGINFO << " &&&&&&&&& cumulatedWorkTime: " << (float)cumulatedWorkTime_ / (float)CLOCKS_PER_SEC << "s";
   LOGINFO << " &&&&&&&&& cumulatedWriteTime: " << (float)cumulatedWriteTime_ / (float)CLOCKS_PER_SEC << "s";
   */
   cumulatedReadTime_  = 0;
   cumulatedWorkTime_  = 0;
   cumulatedWriteTime_ = 0;
   cumulatedCount_     = 0;

   if (newWorkerCount != nworkers || 
       newWriterCount != nwriters || 
       newReaderCount != nreaders)
   {
      bwbPtr_->setThreadCounts(newReaderCount, newWorkerCount, newWriterCount);

      //msg
      LOGWARN << "Readjusting thread count: ";
      LOGWARN << newReaderCount << " readers";
      LOGWARN << newWorkerCount << " workers";
      LOGWARN << newWriterCount << " writers";
      LOGWARN << nreaders << " old reader count";
      LOGWARN << nworkers << " old worker count";
      LOGWARN << nwriters << " old writer count";
   }
}

////////////////////////////////////////////////////////////////////////////////
//// BatchThreadContainer
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BatchThreadContainer::BatchThreadContainer(BlockBatchProcessor* bdpPtr,
   shared_ptr<BlockDataBatch> bdb)
   : processor_(bdpPtr), 
   undo_(bdpPtr->undo_), commitId_(bdpPtr->commitId_++)
{
   for (uint32_t i = 0; i < bdb->nWorkers_; i++)
   {
      shared_ptr<BlockDataThread> bdt(new BlockDataThread(*this));
      threads_.push_back(bdt);

      if (bdb->blockPackets_[i].blocks_.size() > 0)
         threads_[i]->blocks_ = move(bdb->blockPackets_[i].blocks_);
   }

   workTime_ = clock();
   dataBatch_ = bdb;
   startThreads();
}

////////////////////////////////////////////////////////////////////////////////
//// BlockDataThread
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
StoredSubHistory& BlockDataThread::makeSureSubSSHInMap(
   const BinaryData& uniqKey,
   const BinaryData& hgtX)
{
   auto& subsshmap = subSshMap_[uniqKey];
   auto& subssh = subsshmap[hgtX];

   if (subssh.hgtX_.getSize() == 0)
   {
      subssh.hgtX_ = hgtX;

      BinaryData key(uniqKey);
      key.append(hgtX);
      if (!BlockWriteBatcher::iface_->
         getStoredSubHistoryAtHgtX(subssh, uniqKey, hgtX))
         throw runtime_error("missing subssh for undo operation");
   }

   return subssh;
}

////////////////////////////////////////////////////////////////////////////////
StoredSubHistory& BlockDataThread::makeSureSubSSHInMap_IgnoreDB(
   const BinaryData& uniqKey,
   const BinaryData& hgtX)
{
   auto& subsshmap = subSshMap_[uniqKey];
   auto& subssh = subsshmap[hgtX];

   if (subssh.hgtX_.getSize() == 0)
      subssh.hgtX_ = hgtX;

   return subssh;
}

////////////////////////////////////////////////////////////////////////////////
StoredScriptHistory& BlockDataThread::makeSureSSHInMap(
   const BinaryData& uniqKey)
{
   //this call is only used by undoBlockFrom. sshHeaders will always be valid 
   //and it will always ask for SSHs that are already present in the DB, thus 
   //that have valid subssh keys.

   auto& ssh = (*container_->processor_->sshHeaders_->sshToModify_)[uniqKey];
   if (!ssh.isInitialized())
   {
      BlockWriteBatcher::iface_->
         getStoredScriptHistorySummary(ssh, uniqKey);
      ssh.uniqueKey_ = uniqKey;
   }

   return ssh;
}

////////////////////////////////////////////////////////////////////////////////
BlockDataThread::BlockDataThread(BatchThreadContainer& parent)
   : container_(&parent), stxos_(parent.processor_->stxos_), undo_(parent.undo_)
{
   if (!undo_)
   {
      processMethod_ = [this](shared_ptr<PulledBlock> block)->void
      { applyBlockToDB(block); };
   }
   else
   {
      processMethod_ = [this](shared_ptr<PulledBlock> block)->void
      { undoBlockFromDB(block);  };
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataThread::processBlockFeed()
{
   try
   {
      LMDBEnv::Transaction stxoTx(BlockWriteBatcher::iface_->dbEnv_[STXO].get(),
         LMDB::ReadOnly);

      if (blocks_.size())
      {
         for (auto& block : blocks_)
            processMethod_(block);
      }
   }
   catch (exception &e)
   {
      LOGERR << e.what();
   }
   catch (...)
   {
      LOGERR << "unknown exception in processBlockFeed()";
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataThread::applyBlockToDB(shared_ptr<PulledBlock> pb)
{
   if (BlockWriteBatcher::iface_->getValidDupIDForHeight(pb->blockHeight_) != 
       pb->duplicateID_)
   {
      LOGERR << "Dup requested is not the main branch for the given height!";
      throw range_error(
         "Dup requested is not the main branch for the given height!");
      return;
   }

   // We will accumulate undoData as we apply the tx
   StoredUndoData sud;
   sud.blockHash_ = pb->thisHash_;
   sud.blockHeight_ = pb->blockHeight_;
   sud.duplicateID_ = pb->duplicateID_;

   // Apply all the tx to the update data
   for (auto& stx : pb->stxMap_)
   {
      if (stx.second.dataCopy_.getSize() == 0)
      {
         LOGERR << "bad STX data in applyBlockToDB at height " << pb->blockHeight_;
         throw std::range_error("bad STX data while applying blocks");
      }

      applyTxToBatchWriteData(stx.second, &sud);
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataThread::applyTxToBatchWriteData(
   PulledTx& thisSTX,
   StoredUndoData * sud)
{
   bool txIsMine = parseTxOuts(thisSTX, sud);
   txIsMine |= parseTxIns(thisSTX, sud);

   if (BlockWriteBatcher::armoryDbType_ != ARMORY_DB_SUPER && txIsMine)
   {
      auto& countAndHint = txCountAndHint_[thisSTX.getDBKey(true)];
      countAndHint.count_ = thisSTX.numTxOut_;
      countAndHint.hash_ = thisSTX.thisHash_;
   }
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataThread::parseTxIns(
   PulledTx& thisSTX,
   StoredUndoData * sud)
{
   bool txIsMine = false;
      
   if (thisSTX.isCoinbase_)
      return false;

   for (uint32_t iin = 0; iin < thisSTX.txInIndexes_.size() - 1; iin++)
   {
      BinaryData& opTxHashAndId = thisSTX.txHash34_[iin];

      //leveraging the stxo in RAM
      StoredTxOut* stxoPtr = nullptr;
      stxoPtr = stxos_.lookForUTXOInMap(opTxHashAndId);

      if (BlockWriteBatcher::armoryDbType_ != ARMORY_DB_SUPER)
      {
         if (stxoPtr == nullptr)
            continue;
      }

      txIsMine = true;

      const BinaryData& uniqKey = stxoPtr->getScrAddress();
      BinaryData stxoKey = stxoPtr->getDBKey(false);

      // Need to modify existing UTXOs, so that we can delete or mark as spent
      stxoPtr->spentByTxInKey_ = thisSTX.getDBKeyOfChild(iin, false);
      stxoPtr->spentness_ = TXOUT_SPENT;

      ////// Now update the SSH to show this TxIOPair was spent
      // Same story as stxToModify above, except this will actually create a new
      // SSH if it doesn't exist in the map or the DB
      BinaryData& hgtX = stxoPtr->getHgtX();

      StoredSubHistory& subssh = 
         makeSureSubSSHInMap_IgnoreDB(uniqKey, hgtX);

      StoredSubHistory& mirrorsubssh =
         makeSureSubSSHInMap_IgnoreDB(
            uniqKey, stxoPtr->spentByTxInKey_.getSliceRef(0, 4));

      // update the txio in its subSSH
      auto& txio = subssh.txioMap_[stxoKey];
      if (txio.getValue() == 0)
      {
         subssh.markTxOutUnspent(stxoKey, stxoPtr->getValue(),
            stxoPtr->isCoinbase_, false, false);
         txio.flagged_ = true;
      }
      subssh.markTxOutSpent(stxoKey);

      //Mirror the spent txio at txin height
      insertSpentTxio(txio, mirrorsubssh, stxoKey, stxoPtr->spentByTxInKey_);
   }

   return txIsMine;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataThread::parseTxOuts(
   PulledTx& thisSTX,
   StoredUndoData * sud)
{
   bool txIsMine = false;

   for (auto& stxoPair : thisSTX.stxoMap_)
   {
      auto& stxoToAdd = *stxoPair.second;
      const BinaryData& uniqKey = stxoToAdd.getScrAddress();
      BinaryData hgtX = stxoToAdd.getHgtX();

      if (BlockWriteBatcher::armoryDbType_ != ARMORY_DB_SUPER)
      {
         if (!BlockWriteBatcher::scrAddrFilter_->hasScrAddress(uniqKey))
            continue;

         auto height =
            (*container_->processor_->sshHeaders_->
            sshToModify_)[uniqKey].alreadyScannedUpToBlk_;

         txIsMine = true;
      }


      StoredSubHistory& subssh = 
         makeSureSubSSHInMap_IgnoreDB(uniqKey, hgtX);

      // Add reference to the next STXO to the respective SSH object
      if (BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER)
      {
         auto& txio = thisSTX.preprocessedUTXO_[stxoPair.first];
         subssh.txioMap_[txio.getDBKeyOfOutput()] = txio;
         subssh.txioCount_++;
      }
      else
      {
         if (stxoToAdd.spentness_ != TXOUT_SPENT)
            stxoToAdd.spentness_ = TXOUT_UNSPENT;
         
         subssh.markTxOutUnspent(
            stxoToAdd.getDBKey(false),
            stxoToAdd.getValue(),
            stxoToAdd.isCoinbase_,
            false, true);
      }

      // If this was a multisig address, add a ref to each individual scraddr
      if (uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
      {
         vector<BinaryData> addr160List;
         BtcUtils::getMultisigAddrList(stxoToAdd.getScriptRef(), addr160List);
         for (uint32_t a = 0; a<addr160List.size(); a++)
         {
            // Get the existing SSH or make a new one
            BinaryData uniqKey = HASH160PREFIX + addr160List[a];

            if (BlockWriteBatcher::armoryDbType_ != ARMORY_DB_SUPER)
            {
               //do not maintain multisig activity on related scrAddr unless
               //in supernode
               if (!BlockWriteBatcher::scrAddrFilter_->hasScrAddress(uniqKey))
                  continue;
            }

            StoredSubHistory& sshms = 
               makeSureSubSSHInMap_IgnoreDB(uniqKey, hgtX);

            sshms.markTxOutUnspent(
               stxoToAdd.getDBKey(false),
               stxoToAdd.getValue(),
               stxoToAdd.isCoinbase_,
               true, true);
         }
      }

      stxos_.moveStxoToUTXOMap(stxoPair.second);
   }

   return txIsMine;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataThread::undoBlockFromDB(shared_ptr<PulledBlock> block)
{
   StoredUndoData sud;
   prepareUndoData(sud, block);
   processUndoData(sud, block);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataThread::prepareUndoData(
   StoredUndoData& sud, shared_ptr<PulledBlock> block)
{
   sud.blockHash_ = block->thisHash_;
   sud.blockHeight_ = block->blockHeight_;
   sud.duplicateID_ = block->duplicateID_;


   // Go through tx list, fetch TxOuts that are spent, record OutPoints added
   for (auto& stx : values(block->stxMap_))
   {
      // Convert to a regular tx to make accessing TxIns easier
      for (uint32_t iin = 0; iin < stx.txInIndexes_.size() - 1; iin++)
      {
         BinaryDataRef prevHash = stx.txHash34_[iin].getSliceRef(0, 32);
         uint16_t prevIndex =
            READ_UINT16_BE(stx.txHash34_[iin].getSliceRef(32, 2));

         // Skip if coinbase input
         if (prevHash == BtcUtils::EmptyHash())
            continue;

         // Above we checked the block to be undone is full, but we
         // still need to make sure the prevTx we just fetched has our data.
         StoredTx prevStx;
         if(!BlockWriteBatcher::iface_->getStoredTx(prevStx, prevHash))
         {
            if (BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER)
            {
               throw runtime_error("Cannot get undo data for block because not full!");
            }

            continue;
         }

         // 
         sud.stxOutsRemovedByBlock_.push_back(prevStx.stxoMap_[prevIndex]);
      }

      // Use the stxoMap_ to iterate through TxOuts
      for (uint32_t iout = 0; iout<stx.numTxOut_; iout++)
      {
         OutPoint op(stx.thisHash_, iout);
         sud.outPointsAddedByBlock_.push_back(op);
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataThread::processUndoData(StoredUndoData & sud,
   shared_ptr<PulledBlock> pb)
{
   LMDBEnv::Transaction txHistory(
      BlockWriteBatcher::iface_->dbEnv_[HISTORY].get(), LMDB::ReadOnly);
   LMDBEnv::Transaction txSpentness(
      BlockWriteBatcher::iface_->dbEnv_[SPENTNESS].get(), LMDB::ReadOnly);

   ///// Put the STXOs back into the DB which were removed by this block
   // Process the stxOutsRemovedByBlock_ in reverse order
   // Use int32_t index so that -1 != UINT32_MAX and we go into inf loop
   for (int32_t i = (int32_t)sud.stxOutsRemovedByBlock_.size() - 1; i >= 0; i--)
   {
      StoredTxOut & sudStxo = sud.stxOutsRemovedByBlock_[i];
      const uint16_t stxoIdx = sudStxo.txOutIndex_;

      if (BlockWriteBatcher::armoryDbType_ != ARMORY_DB_SUPER)
      {
         if (!BlockWriteBatcher::scrAddrFilter_->hasScrAddress(
            sudStxo.getScrAddress()))
            continue;
      }

      StoredTxOut* stxoPtr = stxos_.getStoredTxOut(
         sudStxo.parentHash_, stxoIdx);

      if (stxoPtr == nullptr)
      {
         LOGWARN << "missing stxo for undo data, this shouldn't happen";
         continue;
      }

      ////// Finished updating STX, now update the SSH in the DB
      // Updating the SSH objects works the same regardless of pruning

      BinaryData uniqKey = stxoPtr->getScrAddress();

      BinaryData hgtX = stxoPtr->getHgtX();
      StoredSubHistory& subssh =
         makeSureSubSSHInMap(uniqKey, hgtX);

      // Readd the unspent at TxOut hgtX TxIOPair in the StoredScriptHistory
      subssh.markTxOutUnspent(
         stxoPtr->getDBKey(false),
         stxoPtr->getValue(),
         stxoPtr->isCoinbase_,
         false, false
         );

      auto& ssh = makeSureSSHInMap(uniqKey);
      ssh.totalUnspent_ += stxoPtr->getValue();

      //delete the spent subssh at TxIn hgtX
      if (stxoPtr->spentness_ == TXOUT_SPENT)
      {
         hgtX = stxoPtr->spentByTxInKey_.getSliceCopy(0, 4);
         StoredSubHistory& subsshAtInHgt =
            makeSureSubSSHInMap(uniqKey, hgtX);

         subsshAtInHgt.eraseTxio(stxoPtr->getDBKey(false));
         ssh.totalTxioCount_--;
      }
      
      if (stxoPtr->spentness_ == TXOUT_UNSPENT ||
         stxoPtr->spentByTxInKey_.getSize() == 0)
      {
         LOGERR << "STXO needs to be re-added/marked-unspent but it";
         LOGERR << "was already declared unspent in the DB";
      }

      stxoPtr->spentness_ = TXOUT_UNSPENT;
      stxoPtr->spentByTxInKey_ = BinaryData(0);

   }

   // The OutPoint list is every new, unspent TxOut created by this block.
   // When they were added, we updated all the StoredScriptHistory objects
   // to include references to them.  We need to remove them now.
   // Use int32_t index so that -1 != UINT32_MAX and we go into inf loop
   //for(int16_t itx=pb.numTx_-1; itx>=0; itx--)
   for (auto& stx : pb->stxMap_)
   {
      for (auto& stxo : values(stx.second.stxoMap_))
      {
         BinaryData    stxoKey = stxo->getDBKey(false);

         // Then fetch the StoredScriptHistory of the StoredTxOut scraddress
         BinaryData uniqKey = stxo->getScrAddress();
         if (BlockWriteBatcher::armoryDbType_ != ARMORY_DB_SUPER)
         {
            if (!BlockWriteBatcher::scrAddrFilter_->hasScrAddress(uniqKey))
               continue;
         }

         BinaryData hgtX = stxo->getHgtX();
         StoredSubHistory& subssh =
            makeSureSubSSHInMap(uniqKey, hgtX);
         subssh.eraseTxio(stxoKey);

         auto& ssh = makeSureSSHInMap(uniqKey);
         ssh.totalTxioCount_--;
         ssh.totalUnspent_ -= stxo->getValue();

         // Now remove any multisig entries that were added due to this TxOut
         if (uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
         {
            vector<BinaryData> addr160List;
            BtcUtils::getMultisigAddrList(stxo->getScriptRef(), addr160List);
            for (uint32_t a = 0; a<addr160List.size(); a++)
            {
               // Get the individual address obj for this multisig piece
               BinaryData uniqKey = HASH160PREFIX + addr160List[a];

               if (BlockWriteBatcher::armoryDbType_ != ARMORY_DB_SUPER)
               {
                  if (!BlockWriteBatcher::scrAddrFilter_->hasScrAddress(uniqKey))
                     continue;
               }

               StoredSubHistory& sshms =
                  makeSureSubSSHInMap(uniqKey, hgtX);
               sshms.eraseTxio(stxoKey);

               auto& ssh = makeSureSSHInMap(uniqKey);
               ssh.totalTxioCount_--;
            }
         }
      }
   }

   // Finally, mark this block as UNapplied.
   pb->blockAppliedToDB_ = false;
   container_->highestBlockProcessed_ = sud.blockHeight_ - 1;
}
