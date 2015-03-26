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

ARMORY_DB_TYPE BlockWriteBatcher::armoryDbType_;
LMDBBlockDatabase* BlockWriteBatcher::iface_;
ScrAddrFilter* BlockWriteBatcher::scrAddrData_;
function<void(string)> BlockWriteBatcher::criticalError_;


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
BlockWriteBatcher::BlockWriteBatcher(
   const BlockDataManagerConfig &config,
   LMDBBlockDatabase* iface,
   ScrAddrFilter& sca, 
   bool undo)
   : dataProcessor_(1, undo)
{
   iface_ = iface;
   armoryDbType_ = iface_->armoryDbType();
   scrAddrData_ = &sca;
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::prepareSshToModify(const ScrAddrFilter& sasd)
{
   //In fullnode, the sshToModify_ container is not wiped after each commit.
   //Instead, all SSH for tracked scrAddr, since we know they're the onyl one
   //that will get any traffic, and in order to update all alreadyScannedUpToBlk_
   //members each commit

   if (BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER)
      return;
   
   if (dataProcessor_.sshHeaders_ != nullptr)
      return;

   dataProcessor_.sshHeaders_.reset(new SSHheaders(1));
   dataProcessor_.sshHeaders_->buildSshHeadersFromSAF(
      sasd);
   
   uint32_t utxoCount=0;
   LMDBEnv::Transaction tx;
   iface_->beginDBTransaction(&tx, HISTORY, LMDB::ReadOnly);

   auto& sshMap = dataProcessor_.sshHeaders_->sshToModify_;

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

         /*for (auto& subssh : tempSSH.subHistMap_)
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

                  stxos_.utxoMap_[bwUtxoKey.getDataRef()] = stxo;
                  utxoCount++;
               }
            }
         }*/
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
int32_t LoadedBlockData::getOffsetHeight(LoadedBlockData& blockData,
   uint32_t threadId)
{

   if (blockData.topLoadedBlock_ <= blockData.endBlock_)
      return blockData.topLoadedBlock_ + threadId;

   return blockData.topLoadedBlock_ - threadId;
}

////////////////////////////////////////////////////////////////////////////////
bool LoadedBlockData::isHeightValid(LoadedBlockData& blockData,
   int32_t hgt)
{
   if (blockData.topLoadedBlock_ <= blockData.endBlock_)
      return hgt <= blockData.endBlock_;

   return hgt >= blockData.endBlock_;
}

////////////////////////////////////////////////////////////////////////////////
void LoadedBlockData::nextHeight(LoadedBlockData& blockData,
   int32_t& hgt)
{
   if (blockData.topLoadedBlock_ <= blockData.endBlock_)
      hgt += blockData.nThreads_;
   else
      hgt -= blockData.nThreads_;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t LoadedBlockData::getTopHeight(LoadedBlockData& lbd, PulledBlock& pb)
{
   if (lbd.startBlock_ <= lbd.endBlock_)
      return pb.blockHeight_;

   return pb.blockHeight_ - 1;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData LoadedBlockData::getTopHash(LoadedBlockData& lbd, PulledBlock& pb)
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
void GrabThreadData::grabBlocksFromDB(shared_ptr<LoadedBlockData> blockData,
   LMDBBlockDatabase* db, uint32_t threadId)
{
   /***
   Grab blocks from the DB, put each block in the current block's nextBlock_
   ***/

   //TIMER_START("grabBlocksFromDB");

   int32_t hgt = LoadedBlockData::getOffsetHeight(*blockData, threadId);

   if (!LoadedBlockData::isHeightValid(*blockData, hgt))
      return;

   //find last block
   GrabThreadData& GTD = blockData->GTD_[threadId];
   shared_ptr<PulledBlock> *lastBlock = &GTD.block_->nextBlock_;
   shared_ptr<FileMap> prevFileMap;

   unique_lock<mutex> grabLock(GTD.grabLock_);

   while (1)
   {
      //create read only db txn within main loop, so that it is rewed
      //after each sleep period
      LMDBEnv::Transaction tx(db->dbEnv_[BLKDATA].get(), LMDB::ReadOnly);
      LDBIter ldbIter = db->getIterator(BLKDATA);

      uint8_t dupID = db->getValidDupIDForHeight(hgt);
      if (!ldbIter.seekToExact(DBUtils::getBlkMetaKey(hgt, dupID)))
      {
         unique_lock<mutex> assignLock(GTD.assignLock_);
         *lastBlock = blockData->interruptBlock_;
         LOGERR << "Header heigh&dup is not in BLKDATA DB";
         LOGERR << "(" << hgt << ", " << dupID << ")";
         return;
      }

      while (GTD.bufferLoad_.load(memory_order_acquire)
         < UPDATE_BYTES_THRESH / blockData->nThreads_ || 
         (GTD.block_ != nullptr && GTD.block_->nextBlock_ == nullptr))
      {
         if (!LoadedBlockData::isHeightValid(*blockData, hgt))
            return;

         uint8_t dupID = db->getValidDupIDForHeight(hgt);
         if (dupID == UINT8_MAX)
         {
            unique_lock<mutex> assignLock(GTD.assignLock_);
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
               unique_lock<mutex> assignLock(GTD.assignLock_);
               *lastBlock = blockData->interruptBlock_;
               LOGERR << "Header heigh&dup is not in BLKDATA DB";
               LOGERR << "(" << hgt << ", " << dupID << ")";
               return;
            }
         }

         shared_ptr<PulledBlock> pb(new PulledBlock());
         pb->fmp_.prev_ = &prevFileMap;
         if (!pullBlockAtIter(*pb, ldbIter, db, blockData->BFA_))
         {
            unique_lock<mutex> assignLock(GTD.assignLock_);
            *lastBlock = blockData->interruptBlock_;
            LOGERR << "No block in DB at height " << hgt;
            return;
         }

         prevFileMap = pb->fmp_.current_;

         //increment bufferLoad
         GTD.bufferLoad_.fetch_add(
            pb->numBytes_, memory_order_release);

         //assign newly grabbed block to shared_ptr
         {
            {
               unique_lock<mutex> assignLock(GTD.assignLock_);
               *lastBlock = pb;
            }

            //let's try to wake up the scan thread
            unique_lock<mutex> mu(blockData->grabLock_, defer_lock);
            if (mu.try_lock())
               blockData->grabCV_.notify_all();
         }

         //set shared_ptr to next empty block
         lastBlock = &pb->nextBlock_;

         blockData->topLoadedBlock_ = hgt;
         LoadedBlockData::nextHeight(*blockData, hgt);
      }

      if (!LoadedBlockData::isHeightValid(*blockData, hgt))
         return;

      TIMER_START("grabThreadSleep");
      //sleep 10sec or until scan thread signals block buffer is low
      GTD.grabCV_.wait_for(grabLock, chrono::seconds(2));
      TIMER_STOP("grabThreadSleep");
   }
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BlockWriteBatcher::applyBlocksToDB(ProgressFilter &progress,
   shared_ptr<LoadedBlockData> blockData)
{
   try
   {
      uint32_t threshold = 2500;

      blockData->blockDataFeed_.reset(new BlockDataFeed(1));
      shared_ptr<BlockDataFeed>* bdfPtr = &blockData->blockDataFeed_->next_;
      
      blockData->startGrabThreads(iface_, blockData);
      thread processorTID = dataProcessor_.startThreads(blockData);

      uint64_t totalBlockDataProcessed=0;

      while (1)
      {
         shared_ptr<BlockDataFeed> nextFeed(new BlockDataFeed(1));
         nextFeed->chargeFeed(blockData);

         if (nextFeed->hasData_ == true)
         {
            unique_lock<mutex> lock(blockData->feedLock_);
            *bdfPtr = nextFeed;
            bdfPtr = &nextFeed->next_;
            blockData->feedCV_.notify_all();

            if (blockData->blockDataFeed_->next_ != nullptr)
            {
               //we have charged up to the next feed, sleep until the current
               //feed is processed

               blockData->feedCV_.wait(lock);
            }
         }
         else
         {
            {
               unique_lock<mutex> lock(blockData->feedLock_);
               *bdfPtr = blockData->interruptFeed_;
               blockData->feedCV_.notify_all();
            }

            if (processorTID.joinable())
               processorTID.join();
            break;
         }


         if (nextFeed->topBlockHeight_ > threshold)
         {
            LOGWARN << "Finished applying blocks up to " << threshold;
            threshold = ((nextFeed->topBlockHeight_ / 2500) + 1) * 2500;
         }

         TIMER_START("updateProgress");
         totalBlockDataProcessed += nextFeed->totalSizeInBytes_;
         progress.advance(totalBlockDataProcessed);
         TIMER_START("updateProgress");
      }
   }
   catch (...)
   {      
      string errorMessage("Scan thread encountered an unkonwn error");
      criticalError_(errorMessage);
   }

   double timeElapsed = TIMER_READ_SEC("grabThreadSleep");
   LOGINFO << "grabThreadSleep: " << timeElapsed << "s";

   timeElapsed = TIMER_READ_SEC("scanThreadSleep");
   LOGINFO << "scanThreadSleep: " << timeElapsed << "s";
   
   return dataProcessor_.lastScannedBlockHash_;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BlockWriteBatcher::scanBlocks(
   ProgressFilter &prog,
   uint32_t startBlock, uint32_t endBlock, 
   ScrAddrFilter& scf,
   bool forceUpdateSSH)
{
   //endBlock = 220000;
   uint32_t nThreads = 1;
   if (scf.armoryDbType_ != ARMORY_DB_SUPER)
   {
      if (int(endBlock - startBlock) > 100)
         nThreads = 2;
   }
   
   LOGINFO << "running with " << nThreads << " threads";

   prepareSshToModify(scf);

   dataProcessor_.forceUpdateSSH_ = forceUpdateSSH;
   shared_ptr<LoadedBlockData> blockData = 
      make_shared<LoadedBlockData>(startBlock, endBlock, scf, nThreads);

   BinaryData bd = applyBlocksToDB(prog, blockData);

   double timeElapsed = TIMER_READ_SEC("scanThreadSleep");
   LOGWARN << "--- scanThreadSleep: " << timeElapsed << " s";

   timeElapsed = TIMER_READ_SEC("parseTxOuts");
   LOGWARN << "--- parseTxOuts: " << timeElapsed << " s";
   timeElapsed = TIMER_READ_SEC("parseTxIns");
   LOGWARN << "--- parseTxIns: " << timeElapsed << " s";
   
   timeElapsed = TIMER_READ_SEC("lookforutxo");
   LOGWARN << "--- lookforutxo: " << timeElapsed << " s";
   timeElapsed = TIMER_READ_SEC("leverageUTXOinRAM");
   LOGWARN << "--- leverageUTXOinRAM: " << timeElapsed << " s";
   
   timeElapsed = TIMER_READ_SEC("inCommit");
   LOGWARN << "--- inCommit: " << timeElapsed << " s";
   timeElapsed = TIMER_READ_SEC("serializeInCommitThread");
   LOGWARN << "--- serializeInCommitThread: " << timeElapsed << " s";
   timeElapsed = TIMER_READ_SEC("waitingOnWriteThread");
   LOGWARN << "--- waitingOnWriteThread: " << timeElapsed << " s";
   

   timeElapsed = TIMER_READ_SEC("inCommitStxo");
   LOGWARN << "--- inCommitStxo: " << timeElapsed << " s";
   timeElapsed = TIMER_READ_SEC("preppingStxoWrite");
   LOGWARN << "--- preppingStxoWrite: " << timeElapsed << " s";

   timeElapsed = TIMER_READ_SEC("applyBlockToDBinternal");
   LOGWARN << "--- applyBlockToDBinternal: " << timeElapsed << " s";
   
   timeElapsed = TIMER_READ_SEC("resetTxn");
   LOGWARN << "--- resetTxn: " << timeElapsed << " s";

   timeElapsed = TIMER_READ_SEC("getNextBlock");
   LOGWARN << "--- getNextBlock: " << timeElapsed << " s";
   
   
   timeElapsed = TIMER_READ_SEC("writeToDB");
   LOGWARN << "--- writeToDB: " << timeElapsed << " s";

   timeElapsed = TIMER_READ_SEC("putSSH");
   LOGWARN << "--- putSSH: " << timeElapsed << " s";

   timeElapsed = TIMER_READ_SEC("putSTX");
   LOGWARN << "--- putSTX: " << timeElapsed << " s";

   timeElapsed = TIMER_READ_SEC("processHeaders");
   LOGWARN << "--- processHeaders: " << timeElapsed << " s";
   
   timeElapsed = TIMER_READ_SEC("getParentSshToModify");
   LOGWARN << "--- getParentSshToModify: " << timeElapsed << " s";

   return bd;
}

////////////////////////////////////////////////////////////////////////////////
bool GrabThreadData::pullBlockAtIter(PulledBlock& pb, LDBIter& iter,
   LMDBBlockDatabase* db, BlockFileAccessor& bfa)
{

   // Now we read the whole block, not just the header
   BinaryRefReader brr(iter.getValueReader());
   if (brr.getSize() != 16)
      return false;

   uint16_t fnum = brr.get_uint32_t();
   uint64_t offset = brr.get_uint64_t();
   uint32_t size = brr.get_uint32_t();

   try
   {
      BinaryDataRef bdr;
      bfa.getRawBlock(bdr, fnum, offset, size, &pb.fmp_);

      pb.blockHeight_ = DBUtils::hgtxToHeight(iter.getKey().getSliceRef(1, 4));
      pb.duplicateID_ = DBUtils::hgtxToDupID(iter.getKey().getSliceRef(1, 4));

      pb.unserializeFullBlock(bdr, true, false);
      pb.preprocessTx(db->armoryDbType());
      return true;
   }
   catch (...)
   {
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

   return GrabThreadData::pullBlockAtIter(pb, ldbIter, iface_, bfa);
}

////////////////////////////////////////////////////////////////////////////////
/// DataToCommit
////////////////////////////////////////////////////////////////////////////////
void DataToCommit::serializeSSH(shared_ptr<BlockDataContainer> bdc)
{
   auto dbType = BlockWriteBatcher::armoryDbType_;
   auto pruneType = DB_PRUNE_NONE;

   sshHeaders_->getSshHeaders(bdc);
   
   auto& sshMap = sshHeaders_->sshToModify_;
   for (auto& sshPair : *sshMap)
   {
      BinaryData sshKey;
      sshKey.append(WRITE_UINT8_LE(DB_PREFIX_SCRIPT));
      sshKey.append(sshPair.first);
      
      auto& ssh = sshPair.second;

      for (auto& threadData : bdc->threads_)
      {
         auto subsshIter = threadData->subSshMap_.find(sshPair.first);
         if (subsshIter != threadData->subSshMap_.end())
         {
            for (auto& subsshPair : subsshIter->second)
            {
               auto& subssh = subsshPair.second;
               uint32_t extraTxioCount = 0;
               uint32_t subsshHeight = DBUtils::hgtxToHeight(subsshPair.first);
               if (subsshHeight > ssh.alreadyScannedUpToBlk_ ||
                  !ssh.alreadyScannedUpToBlk_ ||
                  subsshHeight > forceUpdateSshAtHeight_)
               {
                  for (const auto& txioPair : subssh.txioMap_)
                  {
                     auto& txio = txioPair.second;

                     if (!txio.hasTxIn())
                     {
                        if (!txio.isMultisig() && txio.isUTXO())
                           ssh.totalUnspent_ += txio.getValue();
                     }
                     else
                     {
                        if (!txio.flagged)
                           ssh.totalUnspent_ -= txio.getValue();
                        else
                           extraTxioCount++;
                     }
                  }

                  ssh.totalTxioCount_ += subssh.txioMap_.size() + extraTxioCount;
               }
            }
         }
      }

      if (dbType == ARMORY_DB_SUPER)
      {
         if (ssh.totalTxioCount_ > 0)
         {
            ssh.alreadyScannedUpToBlk_ = bdc->mostRecentBlockApplied_;
            BinaryWriter& bw = serializedSshToModify_[sshKey];
            ssh.serializeDBValue(bw, dbType, pruneType);
         }
         else
            sshKeysToDelete_.insert(sshKey);
      }

      if (dbType != ARMORY_DB_SUPER)
      {
         ssh.alreadyScannedUpToBlk_ = bdc->mostRecentBlockApplied_;
         BinaryWriter& bw = serializedSshToModify_[sshKey];
         ssh.serializeDBValue(bw, dbType, pruneType);
      }
   }

   for (auto& ssh : *sshMap)
      sshPrefixes_[ssh.first] = ssh.second.getSubKey();
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::serializeStxo(STXOS& stxos)
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
void DataToCommit::serializeDataToCommit(shared_ptr<BlockDataContainer> bdc)
{
   auto dbType = BlockWriteBatcher::armoryDbType_;
   auto pruneType = DB_PRUNE_NONE;
   auto iface = BlockWriteBatcher::iface_;


   //subssh
   for (auto& threadData : bdc->threads_)
   {
      auto& subsshMap = threadData->subSshMap_;

      for (auto& sshPair : subsshMap)
      {
         uint32_t keysize = sshPair.first.getSize();
         BinaryData subkey(keysize + 4);
         memcpy(subkey.getPtr(), sshPair.first.getPtr(), keysize);

         auto& submap = intermidiarrySubSshToApply_[sshPair.first];

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
   
   //stxout
   serializeStxo(bdc->stxos_);

   //txOutCount
   if (dbType != ARMORY_DB_SUPER)
   {
      LMDBEnv::Transaction txHints(iface->dbEnv_[TXHINTS].get(), LMDB::ReadOnly);
      for (auto& threadData : bdc->threads_)
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

   topBlockHash_ = bdc->topScannedBlockHash_;
   mostRecentBlockApplied_ = bdc->mostRecentBlockApplied_ +1;
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::serializeData(shared_ptr<BlockDataContainer> bdc)
{
   if (isSerialized_)
      return;

   uint32_t nThreads = getProcessSSHnThreads();
   sshHeaders_.reset(new SSHheaders(nThreads));

   unique_lock<mutex> lock(sshHeaders_->mu_);

   auto serialize = [&](void)
   { serializeDataToCommit(bdc); };

   thread serThread = thread(serialize);

   serializeSSH(bdc);
   lock.unlock();

   if (serThread.joinable())
      serThread.join();

   for (auto& inbw : intermidiarrySubSshToApply_)
   {
      auto sshIter = sshPrefixes_.find(inbw.first);
      if (sshIter == sshPrefixes_.end())
         continue;

      auto& sshkey = sshIter->second;
      size_t keySize = sshkey.getSize();

      auto& submap = serializedSubSshToApply_[keySize];
      BinaryData subKey(keySize + 8);
      memcpy(subKey.getPtr(), sshkey.getPtr(), keySize);

      for (auto& txio : inbw.second)
      {
         if (txio.first.getSize() == 8)
         {
            memcpy(subKey.getPtr() + keySize, txio.first.getPtr(), 8);
            submap.insert(make_pair(subKey, move(txio.second)));
         }
         else
         {
            BinaryData key(sshkey);
            key.append(txio.first);
            submap.insert(make_pair(key, move(txio.second)));
         }
      }
   }
      
   for (auto& ktdSet : intermediarrySubSshKeysToDelete_)
   {
      auto& sshkey = sshPrefixes_[ktdSet.first];
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

   isSerialized_ = true;
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::putSSH()
{
   LMDBEnv::Transaction tx;
   auto db = BlockWriteBatcher::iface_;
   db->beginDBTransaction(&tx, HISTORY, LMDB::ReadWrite);

   auto putThread = [this](uint32_t keyLength)->void
   { this->putSubSSH(keyLength); };

   vector<thread> subSshThreads;
   for (auto& submap : serializedSubSshToApply_)
      subSshThreads.push_back(thread(putThread, submap.first));

   for (auto& sshPair : serializedSshToModify_)
      db->putValue(HISTORY, sshPair.first, sshPair.second.getData());

   for (auto& writeThread : subSshThreads)
      if (writeThread.joinable())
         writeThread.join();
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::putSubSSH(uint32_t keyLength)
{
   LMDBEnv::Transaction subsshtx;
   auto db = BlockWriteBatcher::iface_;

   db->beginSubSSHDBTransaction(subsshtx,
      keyLength, LMDB::ReadWrite);

   auto& submap = serializedSubSshToApply_[keyLength];

   for (auto& subsshentry : submap)
      db->putValue(keyLength, subsshentry.first,
      subsshentry.second.getData());
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::putSTX()
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
void DataToCommit::deleteEmptyKeys()
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
void DataToCommit::updateSDBI()
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
DataToCommit::DataToCommit(DataToCommit&& dtc) 
{
   serializedSubSshToApply_         = move(dtc.serializedSubSshToApply_);
   serializedSshToModify_           = move(dtc.serializedSshToModify_);
   serializedStxOutToModify_        = move(dtc.serializedStxOutToModify_);
   sshKeysToDelete_                 = move(dtc.sshKeysToDelete_);
   subSshKeysToDelete_              = move(dtc.subSshKeysToDelete_);
   serializedSpentness_             = move(dtc.serializedSpentness_);
   spentnessToDelete_               = move(dtc.spentnessToDelete_);
   sshPrefixes_                     = move(dtc.sshPrefixes_);
   intermidiarrySubSshToApply_      = move(dtc.intermidiarrySubSshToApply_);
   intermediarrySubSshKeysToDelete_ = move(dtc.intermediarrySubSshKeysToDelete_);

   
   //Fullnode only
   serializedTxCountAndHash_ = move(dtc.serializedTxCountAndHash_);
   serializedTxHints_ = move(dtc.serializedTxHints_);

   topBlockHash_ = move(dtc.topBlockHash_);
}

////////////////////////////////////////////////////////////////////////////////
uint32_t DataToCommit::getProcessSSHnThreads(void) const
{
   if (BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER)
      return 3;

   return 1;
}

////////////////////////////////////////////////////////////////////////////////
/// STXOS
////////////////////////////////////////////////////////////////////////////////
// This avoids having to do the double-lookup when fetching by hash.
// We still pass in the hash anyway, because the map is indexed by the hash,
// and we'd like to not have to do a lookup for the hash if only provided
// {hgt, dup, idx}
StoredTxOut* STXOS::makeSureSTXOInMap(
   LMDBBlockDatabase* iface,
   BinaryDataRef txHash,
   uint16_t txoId)
{
   // Get the existing STX in RAM and move it to the stxo vector 
   // or grab it from DB

   BinaryData hashAndId = txHash;
   hashAndId.append(WRITE_UINT16_BE(txoId));

   auto stxoIter = utxoMap_.find(hashAndId);
   if (stxoIter != utxoMap_.end())
   {
      stxoToUpdate_.push_back(stxoIter->second);
      utxoMap_.erase(stxoIter);

      return stxoToUpdate_.back().get();
   }

   if (utxoMapBackup_->size() > 0)
   {
      stxoIter = utxoMapBackup_->find(hashAndId);
      if (stxoIter != utxoMapBackup_->end())
      {
         stxoToUpdate_.push_back(stxoIter->second);

         return stxoToUpdate_.back().get();
      }
   }

   if (parent_ != nullptr)
   {
      auto stxoIter = parent_->utxoMap_.find(hashAndId);
      if (stxoIter != parent_->utxoMap_.end())
      {
         stxoToUpdate_.push_back(stxoIter->second);
         keysToDelete_.push_back(stxoIter->first);

         return stxoToUpdate_.back().get();
      }
   }

   shared_ptr<StoredTxOut> stxo(new StoredTxOut);
   BinaryData dbKey;
   iface->getStoredTx_byHash(txHash, nullptr, &dbKey);
   dbKey.append(WRITE_UINT16_BE(txoId));
   iface->getStoredTxOut(*stxo, dbKey);

   stxoToUpdate_.push_back(move(stxo));

   return stxoToUpdate_.back().get();
}

////////////////////////////////////////////////////////////////////////////////
void STXOS::moveStxoToUTXOMap(
   const shared_ptr<StoredTxOut>& thisTxOut)
{
   if (BlockWriteBatcher::armoryDbType_ != ARMORY_DB_SUPER)
      stxoToUpdate_.push_back(thisTxOut);

   utxoMap_[thisTxOut->hashAndId_] = thisTxOut;
}

////////////////////////////////////////////////////////////////////////////////
StoredTxOut* STXOS::lookForUTXOInMap(const BinaryData& txHash)
{
   TIMER_START("leverageUTXOinRAM");
   auto utxoIter = utxoMap_.find(txHash);
   if (utxoIter != utxoMap_.end())
   {
      stxoToUpdate_.push_back(utxoIter->second);

      //if (dbType_ != ARMORY_DB_SUPER)
      utxoMap_.erase(utxoIter);
      TIMER_STOP("leverageUTXOinRAM");
      return stxoToUpdate_.back().get();
   }

   if(utxoMapBackup_->size())
   {
      utxoIter = utxoMapBackup_->find(txHash);
      if (utxoIter != utxoMapBackup_->end())
      {
         stxoToUpdate_.push_back(utxoIter->second);
         TIMER_STOP("leverageUTXOinRAM");
         return stxoToUpdate_.back().get();
      }
   }

   TIMER_STOP("leverageUTXOinRAM");

   //if (BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER)
   {
      TIMER_START("lookforutxo");

      shared_ptr<StoredTxOut> stxo(new StoredTxOut);
      BinaryData dbKey;
      if (!BlockWriteBatcher::iface_->getStoredTx_byHash(
          txHash.getSliceRef(0, 32), nullptr, &dbKey))
      {
         if (BlockWriteBatcher::armoryDbType_ == ARMORY_DB_SUPER)
         {
            LOGERR << "missing txhint in supenode";
            throw runtime_error("missing txhint in supernode");
         }
         else
            return nullptr;
      }

      uint32_t txoId = READ_UINT16_BE(txHash.getPtr() + 32);
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
      
      TIMER_STOP("lookforutxo");

      return stxoToUpdate_.back().get();
   }

   return nullptr;
}

////////////////////////////////////////////////////////////////////////////////
thread STXOS::commitStxo(shared_ptr<BlockDataContainer> bdc)
{
   TIMER_START("inCommitStxo");


   //create commiting object and fill it up
   shared_ptr<STXOS> toCommit(new STXOS(*this));
   
   //clean up spent txouts from the utxo map, move stxos to update in the 
   //commiting object containers
   for (auto& threadData : bdc->threads_)
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

   for (auto& threadData : bdc->threads_)
   {
      toCommit->stxoToUpdate_.insert(toCommit->stxoToUpdate_.end(),
         std::make_move_iterator(threadData->stxos_.stxoToUpdate_.begin()), 
         std::make_move_iterator(threadData->stxos_.stxoToUpdate_.end()));
   }

   //add cumulated utxos of each thread to the utxo map
   for (auto& threadData : bdc->threads_)
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

   TIMER_STOP("inCommitStxo");
   return committhread;
}

////////////////////////////////////////////////////////////////////////////////
void STXOS::commit(shared_ptr<BlockDataContainer> bdp)
{
   auto committhread = commitStxo(bdp);
   if (committhread.joinable())
      committhread.join();
}

////////////////////////////////////////////////////////////////////////////////
void STXOS::writeStxoToDB(shared_ptr<STXOS> stxos)
{
   {
      unique_lock<mutex> writeLock(stxos->parent_->writeMutex_);
      {
         LMDBBlockDatabase *db = BlockWriteBatcher::iface_;
         stxos->dataToCommit_.serializeStxo(*stxos);

         stxos->dataToCommit_.putSTX();
      }
   }

   stxos.reset();
}


////////////////////////////////////////////////////////////////////////////////
////SSHheaders
////////////////////////////////////////////////////////////////////////////////
void SSHheaders::getSshHeaders(shared_ptr<BlockDataContainer> bdc)
{
   TIMER_START("getParentSshToModify");

   //if there is a parent SSHheader, we have to use that one
   if (bdc->parent_->sshHeaders_ != nullptr)
   {
      shared_ptr<SSHheaders> parent =
         bdc->parent_->sshHeaders_;
      unique_lock<mutex> lock(parent->mu_);
      sshToModify_ = parent->sshToModify_;
      return;
   }


   //otherwise we may need to build one from scratch
   //but first let's make sure there isn't one available, in case
   //there is a writer running
   
   shared_ptr<SSHheaders> commitingHeaders = nullptr;
   unique_lock<mutex> parentWriterLock(bdc->parent_->writeMutex_, defer_lock);

   if (!parentWriterLock.try_lock())
   {
      //couldn't grab the parent writeMutex_, this means a write is under
      //process, which means there is a writer object referenced by parent_
      //with a valid SSHheaders. We will wait on the writer to complete
      //its serialization and grab that shared_ptr to serialize this
      //batch of data with. Otherwise, we'd have to wait on the write to
      //complete to get valid SSH balance and txio count.

      shared_ptr<BlockDataContainer> commitingObj = nullptr;
      if (bdc->parent_->writer_ != nullptr)
      {
         if (bdc->parent_->writer_->dataToCommit_.sshHeaders_ != nullptr)
         {
            //parent has a valid SSHheaders object, just use that
            commitingHeaders =
               bdc->parent_->writer_->dataToCommit_.sshHeaders_;
         }
         else commitingObj = bdc->parent_->writer_;
      }

      if (commitingObj != nullptr)
         commitingHeaders = commitingObj->dataToCommit_.sshHeaders_;
   }
   TIMER_STOP("getParentSshToModify");

   if (commitingHeaders != nullptr && commitingHeaders.get() != this)
   {
      unique_lock<mutex> lock(commitingHeaders->mu_);
      processSshHeaders(
         bdc, *commitingHeaders->sshToModify_);
   }
   else
   {
      processSshHeaders(
         bdc, map<BinaryData, StoredScriptHistory>());
   }
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::processSshHeaders(shared_ptr<BlockDataContainer> bdc,
   const map<BinaryData, StoredScriptHistory>& prevSshToModify)
{
   TIMER_START("processHeaders");
   sshToModify_.reset(new map<BinaryData, StoredScriptHistory>());

   vector<vector<const BinaryData*>> saVec;
   saVec.resize(nThreads_);

   uint32_t i = 0;
   for (auto& threadData : bdc->threads_)
   {
      auto& subsshMap = threadData->subSshMap_;
      for (auto& subssh : subsshMap)
      {
         StoredScriptHistory& ssh = (*sshToModify_)[subssh.first];

         auto sshIter = prevSshToModify.find(subssh.first);
         if (sshIter != prevSshToModify.end())
            ssh = sshIter->second;

         saVec[i % nThreads_].push_back(&subssh.first);

         i++;
      }
   }

   auto processSshThread = [&saVec, this](uint32_t vecId)->void
   { this->fetchSshHeaders(*sshToModify_, saVec[vecId]); };

   uint32_t curNThreads = saVec.size() - 1;

   vector<thread> vecTh;
   for (i = 0; i < curNThreads; i++)
      vecTh.push_back(thread(processSshThread, i + 1));

   processSshThread(0);

   for (i = 0; i < curNThreads; i++)
      if (vecTh[i].joinable())
         vecTh[i].join();

   //check for key collisions
   checkForSubKeyCollisions();

   TIMER_STOP("processHeaders");
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::checkForSubKeyCollisions(void)
{
   uint32_t i;
   bool increasedKeySize = true;
   while (increasedKeySize)
   {
      increasedKeySize = false;
      map<BinaryData, vector<StoredScriptHistory*> > collisionMap;

      for (auto& ssh : *sshToModify_)
         collisionMap[ssh.second.getSubKey()].push_back(&ssh.second);

      for (auto& subkey : collisionMap)
      {
         if (subkey.second.size())
         {
            //several new ssh are sharing the same key, let's fix that
            uint32_t previousPrefix = subkey.second[0]->dbPrefix_;
            uint32_t previousKeylen = subkey.second[0]->keyLength_;

            for (i = 1; i < subkey.second.size(); i++)
            {
               ++previousPrefix;
               if (previousPrefix > 0xFF)
               {
                  previousPrefix = 0;
                  ++previousKeylen;
                  increasedKeySize = true;
               }

               StoredScriptHistory& ssh = *subkey.second[i];
               ssh.dbPrefix_ = previousPrefix;
               ssh.keyLength_ = previousKeylen;
            }
         }
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::fetchSshHeaders(
   map<BinaryData, StoredScriptHistory>& sshMap,
   const vector<const BinaryData*>& saVec)
{
   uint32_t distribute = 0;
   for (auto saPtr : saVec)
   {
      auto& ssh = sshMap.find(*saPtr)->second;
      if (ssh.keyLength_ == 0)
      {
         BlockWriteBatcher::iface_->getStoredScriptHistorySummary(
            ssh, *saPtr);
         if (!ssh.isInitialized())
         {
            BinaryData key = 
               BlockWriteBatcher::iface_->getSubSSHKey(*saPtr);
            ssh.uniqueKey_ = *saPtr;
            ssh.dbPrefix_ = key.getPtr()[0];
            ssh.keyLength_ = key.getSize() + (distribute % nThreads_);
            distribute++;
         }
         else
         {
            if (ssh.keyLength_ == SUBSSHDB_PREFIX_MIN + (distribute % nThreads_))
               distribute++;
         }
      }
      else
      {
         if (ssh.keyLength_ == SUBSSHDB_PREFIX_MIN + (distribute % nThreads_))
            distribute++;
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::buildSshHeadersFromSAF(const ScrAddrFilter& SAF)
{
   //for (auto saPair : sasd.getScrAddrMap())
   map<BinaryData, map<BinaryData, StoredSubHistory>> subsshMap;

   vector<const BinaryData*> saVec;
   auto& saMap = SAF.getScrAddrMap();


   sshToModify_.reset(new map<BinaryData, StoredScriptHistory>());
   for (auto& sa : saMap)
   {
      sshToModify_->insert(make_pair(sa.first, StoredScriptHistory()));
      saVec.push_back(&sa.first);
   }
   
   fetchSshHeaders(*sshToModify_, saVec);
   checkForSubKeyCollisions();
}

////////////////////////////////////////////////////////////////////////////////
//// LoadedBlockData
////////////////////////////////////////////////////////////////////////////////
shared_ptr<PulledBlock> LoadedBlockData::getNextBlock(unique_lock<mutex>* mu)
{
   if (!isHeightValid(*this, currentHeight_))
      return nullptr;

   shared_ptr<PulledBlock> blk;
   GrabThreadData& currGTD = GTD_[currentHeight_ % nThreads_];

   while (1)
   {
      {
         unique_lock<mutex> assignLock(currGTD.assignLock_);
         blk = currGTD.block_->nextBlock_;
      }

      if (blk != nullptr)
         break;

      //wakeGrabThreads in case they are sleeping
      wakeGrabThreadsIfNecessary();

      //wait for grabThread signal
      TIMER_START("scanThreadSleep");
      grabCV_.wait_for(*mu, chrono::seconds(2));
      TIMER_STOP("scanThreadSleep");
   }

   currGTD.block_ = blk;

   //decrement bufferload
   currGTD.bufferLoad_.fetch_sub(
      blk->numBytes_, memory_order_release);

   nextHeight(*this, currentHeight_);
   return blk;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<BlockDataFeed> LoadedBlockData::getNextFeed()
{
   shared_ptr<BlockDataFeed> currentFeed;
   
   //we grab the feed lock, assign the feed ptr locally and check if it's valid
   unique_lock<mutex> lock(feedLock_);
   currentFeed = blockDataFeed_->next_;

   //try wake up the grab thread
   feedCV_.notify_all();

   if (currentFeed == nullptr)
   {
      //feed isn't ready, wait on grab thread signal
      feedCV_.wait(lock);
      currentFeed = blockDataFeed_->next_;
   }

   if (currentFeed == interruptFeed_)
      return nullptr;

   //set current feed to the next one and return
   blockDataFeed_ = blockDataFeed_->next_;
   feedCV_.notify_all();

   return currentFeed;
}

////////////////////////////////////////////////////////////////////////////////
void LoadedBlockData::startGrabThreads(
   LMDBBlockDatabase* db,
   shared_ptr<LoadedBlockData>& lbd)
{
   for (uint32_t i = 0; i < nThreads_; i++)
   {
      thread grabThread(GrabThreadData::grabBlocksFromDB, lbd, db, i);
      grabThread.detach();
   }
}

////////////////////////////////////////////////////////////////////////////////
void LoadedBlockData::wakeGrabThreadsIfNecessary()
{
   for (uint32_t i = 0; i < nThreads_; i++)
   {
      if (GTD_[i].bufferLoad_.load(memory_order_consume) <
         UPDATE_BYTES_THRESH / (nThreads_ * 2))
      {
         /***
         Buffer is running low. Try to take ownership of the blockData
         mutex. If that succeeds, the grab thread is sleeping, so
         signal it to wake. Otherwise the grab thread is already running
         and is lagging behind the processing thread (very unlikely)
         ***/

         unique_lock<mutex> lock(GTD_[i].grabLock_, defer_lock);
         if (lock.try_lock())
            GTD_[i].grabCV_.notify_all();
      }
   }
}


////////////////////////////////////////////////////////////////////////////////
//// BlockDataFeed
////////////////////////////////////////////////////////////////////////////////
void BlockDataFeed::chargeFeed(shared_ptr<LoadedBlockData> blockData)
{
   shared_ptr<PulledBlock> block;
   shared_ptr<PulledBlock> lastValidBlock;

   unique_lock<mutex> scanLock(blockData->grabLock_);

   size_t sizePerThread = UPDATE_BYTES_THRESH / nThreads_;

   totalSizeInBytes_ = 0;
   uint32_t i = 0;
   while (1)
   {
      blockData->wakeGrabThreadsIfNecessary();
      block = blockData->getNextBlock(&scanLock);

      if (block == nullptr)
         break;
      
      lastValidBlock = block;
      hasData_ = true;

      uint32_t blockSize = block->numBytes_;
      
      uint32_t rotation = 0;
      while (rotation < nThreads_)
      {
         uint32_t currThread = (i + rotation) % nThreads_;

         if (blockPackets_[currThread].byteSize_ < sizePerThread)
         {
            blockPackets_[currThread].blocks_.push_back(block);
            blockPackets_[currThread].byteSize_ += blockSize;
            break;
         }

         rotation++;
      }

      if (rotation > nThreads_)
      {
         uint32_t currThread = i % nThreads_;

         blockPackets_[currThread].blocks_.push_back(block);
         blockPackets_[currThread].byteSize_ += blockSize;
         break;
      }

      //check if next block is valid
      if (block == blockData->interruptBlock_)
      {
         string errorMessage("The scanning process "
            "interrupted unexpectedly, Armory will now shutdown. "
            "You will have to proceed to \"Help -> Rebuild and Rescan\" "
            "on the next start. If the error persists, contact support. "
            "Refer to your log file for more details on the error.");

         BlockWriteBatcher::criticalError(errorMessage);
      }

      totalSizeInBytes_ += block->numBytes_;
      if (totalSizeInBytes_ >= UPDATE_BYTES_THRESH)
         break;

      i++;
   }

   if (lastValidBlock != nullptr)
   {
      topBlockHeight_ = 
         LoadedBlockData::getTopHeight(*blockData, *lastValidBlock);

      topBlockHash_ = 
         LoadedBlockData::getTopHash(*blockData, *lastValidBlock);
   }
}

////////////////////////////////////////////////////////////////////////////////
//// BlockDataProcesser
////////////////////////////////////////////////////////////////////////////////
thread BlockDataProcessor::startThreads(shared_ptr<LoadedBlockData> blockData)
{
   
   auto processThread = [this](shared_ptr<LoadedBlockData> bd)->void
   { this->processBlockData(bd); };

   thread tID(processThread, blockData);
   return tID;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataProcessor::processBlockData(shared_ptr<LoadedBlockData> blockData)
{
   TIMER_START("applyBlockToDBinternal");
   
   shared_ptr<BlockDataFeed> dataFeed;
   while (1)
   {      
      unique_lock<mutex> workLock(workMutex_);
      dataFeed = blockData->getNextFeed();
      if (dataFeed == nullptr)
         break;

      //update the worker threads struct with the new data and wake them up
      worker_.reset(new BlockDataContainer(this));
      uint32_t i = 0;
      for (auto& thr : worker_->threads_)
      {
         unique_lock<mutex> threadLock(thr->mu_);
         thr->blocks_ = dataFeed->blockPackets_[i].blocks_;
         thr->cv_.notify_all();
         i++;
      }

      uint32_t finishedWork = 0;
      while (finishedWork < nThreads_)
      {
         workCV_.wait(workLock);

         for (auto& threadData : worker_->threads_)
         {
            if (threadData->workDone_ == true)
               finishedWork++;
         }
      }

      //all workers are done, time to commit
      worker_->mostRecentBlockApplied_ = dataFeed->topBlockHeight_;
      worker_->topScannedBlockHash_ = dataFeed->topBlockHash_;

      stxos_.commit(worker_);

      thread committhread = commit();
      if (committhread.joinable())
         committhread.join();
   }

   unique_lock<mutex> stxoWriter(stxos_.writeMutex_);
   unique_lock<mutex> blockDataWriter(writeMutex_);

   TIMER_STOP("applyBlockToDBinternal");
}

////////////////////////////////////////////////////////////////////////////////
thread BlockDataProcessor::commit(bool finalCommit)
{
   TIMER_START("inCommit");
   bool isCommiting = false;
   unique_lock<mutex> l(writeMutex_, try_to_lock);
   if (!l.owns_lock())
      isCommiting = true;
   else
      l.unlock();

   //set writer_ as worker_ then reset it. We'll create a new worker_ in the
   //processBlockData loop
   shared_ptr<BlockDataContainer> commitObject = worker_;
   worker_.reset();

   if (forceUpdateSSH_)
   {
      commitObject->dataToCommit_.forceUpdateSshAtHeight_ =
         commitObject->mostRecentBlockApplied_ - 1;
   }

   /*if (isCommiting)
   {
      //the write thread is already running and we cumulated enough data in the
      //read thread for the next write. Let's use that idle time to serialize
      //the data to commit ahead of time
      TIMER_START("serializeInCommitThread");
      bwbWriteObj->serializeData(subSshMap_);
      TIMER_STOP("serializeInCommitThread");
   }*/


   TIMER_START("waitingOnWriteThread");
   l.lock();
   TIMER_STOP("waitingOnWriteThread");

   writer_ = commitObject;

   thread committhread(writeToDB, writer_);

   TIMER_STOP("inCommit");

   return committhread;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataProcessor::writeToDB(shared_ptr<BlockDataContainer> commitObject)
{
   {
      unique_lock<mutex> lock(commitObject->parent_->writeMutex_);
      TIMER_START("writeToDB");

      commitObject->dataToCommit_.serializeData(commitObject);

      {
         TIMER_START("putSSH");
         commitObject->dataToCommit_.putSSH();
         TIMER_STOP("putSSH");

         TIMER_START("putSTX");
         commitObject->dataToCommit_.putSTX();
         TIMER_STOP("putSTX");

         commitObject->dataToCommit_.deleteEmptyKeys();


         if (commitObject->mostRecentBlockApplied_ != 0 &&
            commitObject->updateSDBI_ == true)
            commitObject->dataToCommit_.updateSDBI();

         commitObject->parent_->lastScannedBlockHash_ =
            commitObject->topScannedBlockHash_;
         commitObject->parent_->writer_.reset();
      }
   
      TIMER_STOP("writeToDB");
   }

   commitObject.reset();
}

////////////////////////////////////////////////////////////////////////////////
BlockDataContainer::BlockDataContainer(BlockDataProcessor* bdpPtr)
   : parent_(bdpPtr), nThreads_(bdpPtr->nThreads_), undo_(bdpPtr->undo_)
{
   for (uint32_t i = 0; i < nThreads_; i++)
   {
      shared_ptr<BlockDataThread> bdt(new BlockDataThread(*this));
      threads_.push_back(bdt);
   }

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
      BlockWriteBatcher::iface_->
         getStoredSubHistoryAtHgtX(subssh, uniqKey, hgtX);
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

   auto& ssh = (*parent_->parent_->sshHeaders_->sshToModify_)[uniqKey];
   if (!ssh.isInitialized())
   {
      BlockWriteBatcher::iface_->
         getStoredScriptHistorySummary(ssh, uniqKey);
      ssh.uniqueKey_ = uniqKey;
   }

   return ssh;
}

////////////////////////////////////////////////////////////////////////////////
BlockDataThread::BlockDataThread(BlockDataContainer& parent)
   : parent_(&parent), stxos_(parent.parent_->stxos_), undo_(parent.undo_)
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
   unique_lock<mutex> lock(mu_);

   //control thread will wake this up when a feed is ready
   cv_.wait(lock);

   LMDBEnv::Transaction stxoTx(BlockWriteBatcher::iface_->dbEnv_[STXO].get(),
      LMDB::ReadOnly);

   for (auto& block : blocks_)
      processMethod_(block);

   unique_lock<mutex> workLock(parent_->parent_->workMutex_);
   workDone_ = true;
   parent_->parent_->workCV_.notify_all();
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
   TIMER_START("parseTxOuts");
   bool txIsMine = parseTxOuts(thisSTX, sud);
   TIMER_STOP("parseTxOuts");
   TIMER_START("parseTxIns");
   txIsMine |= parseTxIns(thisSTX, sud);
   TIMER_STOP("parseTxIns");

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
         subssh.markTxOutUnspent(stxoKey, stxoPtr->getValue(),
         stxoPtr->isCoinbase_, false, false);
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
         if (!BlockWriteBatcher::scrAddrData_->hasScrAddress(uniqKey))
            continue;

         auto height =
            (*parent_->parent_->sshHeaders_->
            sshToModify_)[uniqKey].alreadyScannedUpToBlk_;

         /*if (height >= thisSTX.blockHeight_ && height != 0)
            continue;*/

         txIsMine = true;
      }

      stxoToAdd.spentness_ = TXOUT_UNSPENT;

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
               if (!BlockWriteBatcher::scrAddrData_->hasScrAddress(uniqKey))
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
      for (uint32_t iin = 0; iin<stx.txInIndexes_.size() -1; iin++)
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
         BlockWriteBatcher::iface_->getStoredTx(prevStx, prevHash);
         if (KEY_NOT_IN_MAP(prevIndex, prevStx.stxoMap_))
         {
            throw runtime_error("Cannot get undo data for block because not full!");
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
         if (!BlockWriteBatcher::scrAddrData_->hasScrAddress(
               sudStxo.getScrAddress()))
            continue;
      }

      StoredTxOut* stxoPtr = stxos_.makeSureSTXOInMap(
         BlockWriteBatcher::iface_, sudStxo.parentHash_, stxoIdx);

      {
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
            if (!BlockWriteBatcher::scrAddrData_->hasScrAddress(uniqKey))
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
                  if (!BlockWriteBatcher::scrAddrData_->hasScrAddress(uniqKey))
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
   parent_->mostRecentBlockApplied_ = sud.blockHeight_ - 1;
}
