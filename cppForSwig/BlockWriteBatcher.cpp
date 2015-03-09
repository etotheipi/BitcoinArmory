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
StoredSubHistory& BlockWriteBatcher::makeSureSubSSHInMap(
   const BinaryData& uniqKey,
   const BinaryData& hgtX)
{
   auto& subsshmap = subSshMap_[uniqKey];
   auto& subssh = subsshmap[hgtX];

   if (subssh.hgtX_.getSize() == 0)
   {
      /*if (subSshMapToWrite_.size() > 0)
      {
         auto sshIter = subSshMapToWrite_.find(uniqKey);
         if (sshIter != subSshMapToWrite_.end())
         {
            auto subsshIter = sshIter->second.find(hgtX);
            if (subsshIter != sshIter->second.end())
            {
               subssh = subsshIter->second;
               return subssh;
            }
         }
      }*/

      subssh.hgtX_ = hgtX;

      BinaryData key(uniqKey);
      key.append(hgtX);
      iface_->getStoredSubHistoryAtHgtX(subssh, uniqKey, hgtX);
      
      dbUpdateSize_ += UPDATE_BYTES_SUBSSH;
   }

   return subssh;
}

////////////////////////////////////////////////////////////////////////////////
StoredSubHistory& BlockWriteBatcher::makeSureSubSSHInMap_IgnoreDB(
   const BinaryData& uniqKey,
   const BinaryData& hgtX,
   const uint32_t& currentBlockHeight)
{
   auto& subsshmap = subSshMap_[uniqKey];
   auto& subssh = subsshmap[hgtX];

   if (subssh.hgtX_.getSize() == 0)
   {
      subssh.hgtX_ = hgtX;

      dbUpdateSize_ += UPDATE_BYTES_SUBSSH;
   }

   return subssh;
}

////////////////////////////////////////////////////////////////////////////////
StoredScriptHistory& BlockWriteBatcher::makeSureSSHInMap(
   const BinaryData& uniqKey)
{  
   //this call is only used by undoBlockFrom. sshHeaders will always be valid 
   //and it will always ask for SSHs that are already present in the DB, thus 
   //that have valid subssh keys.

   auto& ssh = (*dataToCommit_.sshHeaders_->sshToModify_)[uniqKey];
   if (!ssh.isInitialized())
   {
      iface_->getStoredScriptHistorySummary(ssh, uniqKey);
      ssh.uniqueKey_ = uniqKey;
   }

   return ssh;
}
////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::insertSpentTxio(
   const TxIOPair& txio,
   StoredSubHistory& inHgtSubSsh,
   const BinaryData& txOutKey, 
   const BinaryData& txInKey)
{
   auto& mirrorTxio = inHgtSubSsh.txioMap_[txOutKey];

   mirrorTxio = txio;
   mirrorTxio.setTxIn(txInKey);

   dbUpdateSize_ += UPDATE_BYTES_KEY;
   
   if (!txOutKey.startsWith(inHgtSubSsh.hgtX_))
      inHgtSubSsh.txioCount_++;
}

////////////////////////////////////////////////////////////////////////////////
BlockWriteBatcher::BlockWriteBatcher(
   const BlockDataManagerConfig &config,
   LMDBBlockDatabase* iface,
   bool forCommit)
   : config_(config), iface_(iface),
   mostRecentBlockApplied_(0), isForCommit_(forCommit),
   dataToCommit_(iface),
   stxos_(iface)
{
   parent_ = this;
}

////////////////////////////////////////////////////////////////////////////////
BlockWriteBatcher::~BlockWriteBatcher()
{
   //a BWB meant for commit doesn't need to run commit() on dtor
   if (isForCommit_)
   {
      clearTransactions();
      return;
   }

   TIMER_START("bwbDtor");

   if (commitingObject_ != nullptr)
      commitingObject_->cleanupFlag_.store(true, memory_order_release);

   resetHistoryTransaction();

   //call final commit, force it
   thread committhread = commit(true);
   thread commitstxo;
   if (config_.armoryDbType == ARMORY_DB_SUPER)
      commitstxo = stxos_.commitStxo(false);

   //join on the thread, don't want the destuctor to return until the data has
   //been commited
   if (committhread.joinable())
      committhread.join();

   if (commitstxo.joinable())
      commitstxo.join();

   clearTransactions();

   TIMER_STOP("bwbDtor");
}

////////////////////////////////////////////////////////////////////////////////
BlockWriteBatcher::BlockWriteBatcher(BlockWriteBatcher&& bwb) :
   config_(bwb.config_), iface_(bwb.iface_), 
   dataToCommit_(move(bwb.dataToCommit_)),
   stxos_(bwb.iface_), isForCommit_(true)
{
   //this a dedicated move operator for write object cleanup, don't use it 
   //elsewhere
   
   txCountAndHint_ = move(bwb.txCountAndHint_);
   //subSshMapToWrite_ = move(bwb.subSshMapToWrite_);
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BlockWriteBatcher::applyBlockToDB(shared_ptr<PulledBlock> pb,
   ScrAddrFilter& scrAddrData)
{
   TIMER_START("applyBlockToDBinternal");
   if(iface_->getValidDupIDForHeight(pb->blockHeight_) != pb->duplicateID_)
   {
      LOGERR << "Dup requested is not the main branch for the given height!";
      return BinaryData();
   }
   else
      pb->isMainBranch_ = true;
   
   stxos_.recycleTxn();

   mostRecentBlockApplied_ = pb->blockHeight_;

   // We will accumulate undoData as we apply the tx
   StoredUndoData sud;
   sud.blockHash_   = pb->thisHash_;
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

      applyTxToBatchWriteData(stx.second, &sud, scrAddrData);
   }

   topScannedBlockHash_ = pb->thisHash_;

   if (iface_->armoryDbType() == ARMORY_DB_SUPER)
      stxos_.commit();

   if (dbUpdateSize_ > UPDATE_BYTES_THRESH)
   {
      thread committhread = commit();
      if (committhread.joinable())
         committhread.detach();
   }

   TIMER_STOP("applyBlockToDBinternal");
   return topScannedBlockHash_;
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::reorgApplyBlock(uint32_t hgt, uint8_t dup,
   ScrAddrFilter& scrAddrData, BlockFileAccessor& bfa)
{
   forceUpdateSsh_ = true;

   resetHistoryTransaction();
   resetTransactions();

   prepareSshToModify(scrAddrData);

   shared_ptr<PulledBlock> pb(new PulledBlock());
   {
      LMDBEnv::Transaction blockTx(iface_->dbEnv_[BLKDATA].get(), LMDB::ReadOnly);
      if (!pullBlockFromDB(*pb, hgt, dup, bfa))
      {
         //Should notify UI before returning
         LOGERR << "Failed to load block " << hgt << "," << dup;
         return;
      }
   }

   applyBlockToDB(pb, scrAddrData);

   thread writeThread = commit(true);
   if (writeThread.joinable())
      writeThread.join();

   clearTransactions();
}


////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::undoBlockFromDB(StoredUndoData & sud, 
   ScrAddrFilter& scrAddrData, BlockFileAccessor& bfa)
{
   prepareSshToModify(scrAddrData);

   resetHistoryTransaction();
   resetTransactions();

   if (dataToCommit_.sshHeaders_ == nullptr)
   {
      dataToCommit_.sshHeaders_.reset(new SSHheaders(iface_, 1));
      dataToCommit_.sshHeaders_->sshToModify_.reset(
         new map<BinaryData, StoredScriptHistory>());
   }

   PulledBlock pb;
   {
      LMDBEnv::Transaction blkdataTx(iface_->dbEnv_[BLKDATA].get(), LMDB::ReadOnly);
      pullBlockFromDB(pb, sud.blockHeight_, sud.duplicateID_, bfa);
   }
   
   mostRecentBlockApplied_ = sud.blockHeight_ -1;

   ///// Put the STXOs back into the DB which were removed by this block
   // Process the stxOutsRemovedByBlock_ in reverse order
   // Use int32_t index so that -1 != UINT32_MAX and we go into inf loop
   for(int32_t i=(int32_t)sud.stxOutsRemovedByBlock_.size()-1; i>=0; i--)
   {
      StoredTxOut & sudStxo = sud.stxOutsRemovedByBlock_[i];
      const uint16_t stxoIdx = sudStxo.txOutIndex_;

      if (config_.armoryDbType != ARMORY_DB_SUPER)
      {
         if (!scrAddrData.hasScrAddress(sudStxo.getScrAddress()))
            continue;
      }

      StoredTxOut* stxoPtr = stxos_.makeSureSTXOInMap( 
               iface_,
               sudStxo.parentHash_,
               stxoIdx);

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
            dbUpdateSize_,
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

      if (config_.pruneType == DB_PRUNE_NONE)
      {
         // If full/super, we have the TxOut in DB, just need mark it unspent
         if (stxoPtr->spentness_ == TXOUT_UNSPENT ||
            stxoPtr->spentByTxInKey_.getSize() == 0)
         {
            LOGERR << "STXO needs to be re-added/marked-unspent but it";
            LOGERR << "was already declared unspent in the DB";
         }

         stxoPtr->spentness_ = TXOUT_UNSPENT;
         stxoPtr->spentByTxInKey_ = BinaryData(0);
      }
      else
      {
         // If we're pruning, we should have the Tx in the DB, but without the
         // TxOut because it had been pruned by this block on the forward op

         stxoPtr->spentness_ = TXOUT_UNSPENT;
         stxoPtr->spentByTxInKey_ = BinaryData(0);
      }
   }

   // The OutPoint list is every new, unspent TxOut created by this block.
   // When they were added, we updated all the StoredScriptHistory objects
   // to include references to them.  We need to remove them now.
   // Use int32_t index so that -1 != UINT32_MAX and we go into inf loop
   //for(int16_t itx=pb.numTx_-1; itx>=0; itx--)
   for (auto& stx : pb.stxMap_)
   {
      for (auto& stxo : values(stx.second.stxoMap_))
      {
         BinaryData    stxoKey = stxo->getDBKey(false);
   
         // Then fetch the StoredScriptHistory of the StoredTxOut scraddress
         BinaryData uniqKey = stxo->getScrAddress();
         if (config_.armoryDbType != ARMORY_DB_SUPER)
         {
            if (!scrAddrData.hasScrAddress(uniqKey))
               continue;
         }

         BinaryData hgtX    = stxo->getHgtX();
         StoredSubHistory& subssh =
            makeSureSubSSHInMap(uniqKey, hgtX);
   
         subssh.eraseTxio(stxoKey);
         auto& ssh = makeSureSSHInMap(uniqKey);
         ssh.totalTxioCount_--;
         ssh.totalUnspent_ -= stxo->getValue();
   
         // Now remove any multisig entries that were added due to this TxOut
         if(uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
         {
            vector<BinaryData> addr160List;
            BtcUtils::getMultisigAddrList(stxo->getScriptRef(), addr160List);
            for(uint32_t a=0; a<addr160List.size(); a++)
            {
               // Get the individual address obj for this multisig piece
               BinaryData uniqKey = HASH160PREFIX + addr160List[a];

               if (scrAddrData.armoryDbType_ != ARMORY_DB_SUPER)
               {
                  if (!scrAddrData.hasScrAddress(uniqKey))
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
   pb.blockAppliedToDB_ = false;
   
   clearTransactions();
   
   if (dbUpdateSize_ > UPDATE_BYTES_THRESH)
   {
      thread committhread = commit(true);
      if (committhread.joinable())
         committhread.join();
   }
}

////////////////////////////////////////////////////////////////////////////////
bool BlockWriteBatcher::parseTxIns(
   PulledTx& thisSTX, 
   StoredUndoData * sud, 
   ScrAddrFilter& scrAddrData)
{
   bool txIsMine = false;

   for (uint32_t iin = 0; iin < thisSTX.txInIndexes_.size() - 1; iin++)
   {
      // Get the OutPoint data of TxOut being spent
      if (thisSTX.isCoinbase_)
         continue;
      
      BinaryData& opTxHashAndId =
         thisSTX.txHash34_[iin];

      //For scanning a predefined set of addresses, check if this txin 
      //consumes one of our utxo

      //leveraging the stxo in RAM
      StoredTxOut* stxoPtr = nullptr;
      stxoPtr = stxos_.lookForUTXOInMap(opTxHashAndId);

      if (config_.armoryDbType != ARMORY_DB_SUPER)
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

      StoredSubHistory& subssh = makeSureSubSSHInMap_IgnoreDB(uniqKey, hgtX, 0);
      
      StoredSubHistory& mirrorsubssh = 
         makeSureSubSSHInMap_IgnoreDB(
            uniqKey, 
            stxoPtr->spentByTxInKey_.getSliceRef(0, 4),
            0);

      // update the txio in its subSSH
      auto& txio = subssh.txioMap_[stxoKey];
      if (txio.getValue() == 0)
         subssh.markTxOutUnspent(stxoKey, dbUpdateSize_, stxoPtr->getValue(),
            stxoPtr->isCoinbase_, false, false);
      subssh.markTxOutSpent(stxoKey);
         
      //Mirror the spent txio at txin height
      insertSpentTxio(txio, mirrorsubssh, stxoKey, stxoPtr->spentByTxInKey_);
   }

   return txIsMine;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockWriteBatcher::parseTxOuts(
   PulledTx& thisSTX,
   StoredUndoData * sud,
   ScrAddrFilter& scrAddrData)
{
   bool txIsMine = false;

   for (auto& stxoPair : thisSTX.stxoMap_)
   {
      auto& stxoToAdd = *stxoPair.second;
      const BinaryData& uniqKey = stxoToAdd.getScrAddress();
      BinaryData hgtX = stxoToAdd.getHgtX();

      if (config_.armoryDbType != ARMORY_DB_SUPER)
      {
         if (!scrAddrData.hasScrAddress(uniqKey))
            continue;

         auto height = 
            (*dataToCommit_.sshHeaders_->
               sshToModify_)[uniqKey].alreadyScannedUpToBlk_;

         if (height >= thisSTX.blockHeight_ && height != 0)
            continue;

         txIsMine = true;
      }
         
      stxoToAdd.spentness_ = TXOUT_UNSPENT;

      StoredSubHistory& subssh = makeSureSubSSHInMap_IgnoreDB(
         uniqKey,
         hgtX,
         thisSTX.blockHeight_);

      // Add reference to the next STXO to the respective SSH object
      if (config_.armoryDbType == ARMORY_DB_SUPER)
      {
         auto& txio = thisSTX.preprocessedUTXO_[stxoPair.first];
         subssh.txioMap_[txio.getDBKeyOfOutput()] = txio;
         subssh.txioCount_++;
         dbUpdateSize_ += sizeof(TxIOPair)+8;
      }
      else
      {
         subssh.markTxOutUnspent(
            stxoToAdd.getDBKey(false),
            dbUpdateSize_,
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

            if (config_.armoryDbType != ARMORY_DB_SUPER)
            {
               //do not maintain multisig activity on related scrAddr unless
               //in supernode
               if (!scrAddrData.hasScrAddress(uniqKey))
                  continue;
            }

            StoredSubHistory& sshms = makeSureSubSSHInMap_IgnoreDB(
               uniqKey,
               hgtX,
               thisSTX.blockHeight_);

            sshms.markTxOutUnspent(
               stxoToAdd.getDBKey(false),
               dbUpdateSize_,
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
// Assume that stx.blockHeight_ and .duplicateID_ are set correctly.
// We created the maps and sets outside this function, because we need to keep
// a master list of updates induced by all tx in this block.  
// TODO:  Make sure that if Tx5 spends an input from Tx2 in the same 
//        block that it is handled correctly, etc.
void BlockWriteBatcher::applyTxToBatchWriteData(
                        PulledTx& thisSTX,
                        StoredUndoData * sud,
                        ScrAddrFilter& scrAddrData)
{
   TIMER_START("parseTxOuts");
   bool txIsMine = parseTxOuts(thisSTX, sud, scrAddrData);
   TIMER_STOP("parseTxOuts");
   TIMER_START("parseTxIns");
   txIsMine |= parseTxIns(thisSTX, sud, scrAddrData);
   TIMER_STOP("parseTxIns");

   if (config_.armoryDbType != ARMORY_DB_SUPER && txIsMine)
   {
      auto& countAndHint = txCountAndHint_[thisSTX.getDBKey(true)];
      countAndHint.count_ = thisSTX.numTxOut_;
      countAndHint.hash_ = thisSTX.thisHash_;
   }
}

////////////////////////////////////////////////////////////////////////////////
thread BlockWriteBatcher::commit(bool finalCommit)
{
   TIMER_START("inCommit");
   bool isCommiting = false;
   unique_lock<mutex> l(writeLock_, try_to_lock);
   if (!l.owns_lock())
   {
      // lock_ is held if commit() is running, but if we have
      // accumulated too much data we can't return from this function
      // to accumulate some more, so do a commit() anyway at the end
      // of this function. lock_ is used as a flag to indicate 
      // commitThread is running.
      if (!finalCommit && dbUpdateSize_ < UPDATE_BYTES_THRESH * 2)
      {
         TIMER_STOP("inCommit");
         return thread();
      }

      isCommiting = true;
   }
   else
      l.unlock();

   //create a BWB for commit (pass true to the constructor)
   auto bwbWriteObj = shared_ptr<BlockWriteBatcher>(
     new BlockWriteBatcher(config_, iface_, true));

   bwbWriteObj->cleanupFlag_.store(finalCommit, memory_order_relaxed);
   
   if (forceUpdateSsh_)
   {
      bwbWriteObj->dataToCommit_.forceUpdateSshAtHeight_ =
         mostRecentBlockApplied_ -1;
   }

   if (config_.armoryDbType != ARMORY_DB_SUPER)
   {
      bwbWriteObj->txCountAndHint_ = std::move(txCountAndHint_);
      bwbWriteObj->stxos_.stxoToUpdate_ = std::move(stxos_.stxoToUpdate_);
   }

   bwbWriteObj->mostRecentBlockApplied_ = mostRecentBlockApplied_;
   bwbWriteObj->parent_ = this;
   bwbWriteObj->topScannedBlockHash_ = topScannedBlockHash_;

   /*if (isCommiting)
   {
      //the write thread is already running and we cumulated enough data in the
      //read thread for the next write. Let's use that idle time to serialize
      //the data to commit ahead of time
      TIMER_START("serializeInCommitThread");
      bwbWriteObj->serializeData(subSshMap_);
      TIMER_STOP("serializeInCommitThread");
   }*/
      
   bwbWriteObj->dbUpdateSize_ = dbUpdateSize_;
   bwbWriteObj->updateSDBI_ = updateSDBI_;
      
   dbUpdateSize_ = 0;

   TIMER_START("waitingOnWriteThread");
   l.lock();
   TIMER_STOP("waitingOnWriteThread");

   bwbWriteObj->subSshMap_ = move(subSshMap_);
   commitingObject_ = bwbWriteObj;

   if (isCommiting)
      resetTransactions();

   thread committhread(writeToDB, bwbWriteObj);

   TIMER_STOP("inCommit");

   return committhread;
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::prepareSshToModify(const ScrAddrFilter& sasd)
{
   //In fullnode, the sshToModify_ container is not wiped after each commit.
   //Instead, all SSH for tracked scrAddr, since we know they're the onyl one
   //that will get any traffic, and in order to update all alreadyScannedUpToBlk_
   //members each commit

   if (config_.armoryDbType == ARMORY_DB_SUPER)
      return;
   
   if (dataToCommit_.sshHeaders_ != nullptr)
      return;

   dataToCommit_.sshHeaders_.reset(new SSHheaders(iface_, 1));
   dataToCommit_.sshHeaders_->buildSshHeadersFromSAF(sasd);
   
   uint32_t utxoCount=0;
   LMDBEnv::Transaction tx;
   iface_->beginDBTransaction(&tx, HISTORY, LMDB::ReadOnly);

   auto& sshMap = dataToCommit_.sshHeaders_->sshToModify_;

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

                  stxos_.utxoMap_[bwUtxoKey.getDataRef()] = stxo;
                  utxoCount++;
               }
            }
         }
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::writeToDB(shared_ptr<BlockWriteBatcher> bwb)
{
   unique_lock<mutex> lock(bwb->parent_->writeLock_);
   TIMER_START("writeToDB");

   bwb->dataToCommit_.serializeData(bwb);

   {
      TIMER_START("putSSH");
      bwb->dataToCommit_.putSSH();
      TIMER_STOP("putSSH");

      TIMER_START("putSTX");
      bwb->dataToCommit_.putSTX();
      TIMER_STOP("putSTX");

      bwb->dataToCommit_.deleteEmptyKeys();


      if (bwb->mostRecentBlockApplied_ != 0 && bwb->updateSDBI_ == true)
         bwb->dataToCommit_.updateSDBI();

      //bwb->parent_->commitingObject_.reset();
   }

   BlockWriteBatcher* bwbParent = bwb->parent_;

   if (bwb->cleanupFlag_.load(memory_order_acquire) == true)
      return;
   
   //signal the readonly transaction to reset
   unique_lock<mutex> cleanUpLock(bwb->writeLock_);

   while (bwbParent->resetWriterPtr_.load(memory_order_acquire) != nullptr);
   bwbParent->resetWriterPtr_.store(&bwb, memory_order_release);

   //signal DB is ready for new commit
   TIMER_STOP("writeToDB");
   lock.unlock();

   //wait for scan thread to dump its useless containers on this bwb object in
   //order to delete them within this thread
   while (bwb->cleanupFlag_.load(memory_order_acquire) == false)
      bwb->signalCleanup_.wait(cleanUpLock);

   //std::thread is holding a ref to our shared_ptr. We want to clean up its
   //content in this thread, so let's move the data to a local variable before
   //exiting
   //BlockWriteBatcher bwbCleanup(move(*bwb));
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::resetTransactions(void)
{
   txn_.open(iface_->dbEnv_[HISTORY].get(), LMDB::ReadOnly);
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::clearTransactions(void)
{
   txn_.commit();
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::grabBlocksFromDB(shared_ptr<LoadedBlockData> blockData,
   LMDBBlockDatabase* db, uint32_t threadId)
{
   /***
   Grab blocks from the DB, put each block in the current block's nextBlock_
   ***/

   //TIMER_START("grabBlocksFromDB");

   uint32_t offsetHgt = blockData->topLoadedBlock_ / blockData->nThreads_;
   uint32_t hgt = offsetHgt * blockData->nThreads_ + threadId;
   if (hgt < blockData->topLoadedBlock_)
      hgt = (offsetHgt +1) * blockData->nThreads_ + threadId;

   if (hgt > blockData->endBlock_)
      return;

   //find last block
   GrabThreadData& GTD = blockData->GTD_[threadId];
   shared_ptr<PulledBlock> *lastBlock = &GTD.block_;
   shared_ptr<FileMap> prevFileMap;

   if (hgt != blockData->topLoadedBlock_)
   {
      GTD.block_ = shared_ptr<PulledBlock>(new PulledBlock());
      lastBlock = &GTD.block_->nextBlock_;
   }

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
         if (hgt > blockData->endBlock_)
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
            unique_lock<mutex> mu(blockData->scanLock_, defer_lock);
            if (mu.try_lock())
               blockData->scanCV_.notify_all();
         }

         //set shared_ptr to next empty block
         lastBlock = &pb->nextBlock_;

         blockData->topLoadedBlock_ = hgt;
         hgt += blockData->nThreads_;
      }

      if (hgt > blockData->endBlock_)
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
   if (blockData->endBlock_ == 0)
   {
      LOGERR << "Top block is 0, nothing to scan";
      throw std::range_error("Top block is 0, nothing to scan");
   }

   BinaryData lastScannedBlockHash;
   resetTransactions();
   if (config_.armoryDbType == ARMORY_DB_SUPER)
      stxos_.resetTransactions();

   try
   {
      unique_lock<mutex> scanLock(blockData->scanLock_);
      
      shared_ptr<PulledBlock> block;
      block = blockData->startGrabThreads(iface_, blockData, &scanLock);

      uint64_t totalBlockDataProcessed=0;

      if (block == blockData->interruptBlock_)
      {
         string errorMessage("The scanning process "
            "interrupted unexpectedly, Armory will now shutdown. "
            "You will have to proceed to \"Help -> Rebuild and Rescan\" "
            "on the next start. If the error persists, contact support. "
            "Refer to your log file for more details on the error.");

         criticalError_(errorMessage);
         return lastScannedBlockHash;
      }

      for (uint32_t i = blockData->startBlock_;
         i <= blockData->endBlock_;
         i++)
      {
         resetHistoryTransaction();

         if (i > blockData->endBlock_)
            break;
         
         uint32_t blockSize = block->numBytes_;

         //scan block
         lastScannedBlockHash = 
            applyBlockToDB(block, blockData->scrAddrFilter_);

         TIMER_START("getNextBlock");
         if (i == blockData->endBlock_)
            break;

         blockData->wakeGrabThreadsIfNecessary();
         block = blockData->getNextBlock(i+1, &scanLock);

         //check if next block is valid
         if (block == blockData->interruptBlock_)
         {
            string errorMessage("The scanning process "
               "interrupted unexpectedly, Armory will now shutdown. "
               "You will have to proceed to \"Help -> Rebuild and Rescan\" "
               "on the next start. If the error persists, contact support. "
               "Refer to your log file for more details on the error.");

            criticalError_(errorMessage);
            return lastScannedBlockHash;
         }
 
         if (i % 2500 == 2499)
            LOGWARN << "Finished applying blocks up to " << (i + 1);
         TIMER_STOP("getNextBlock");

         TIMER_START("updateProgress");
         totalBlockDataProcessed += blockSize;
         progress.advance(totalBlockDataProcessed);
         TIMER_START("updateProgress");
      }
      
      clearTransactions();
   }
   catch (...)
   {
      clearTransactions();
      
      string errorMessage("Scan thread encountered an unkonwn error");
      criticalError_(errorMessage);
   }

   double timeElapsed = TIMER_READ_SEC("grabThreadSleep");
   LOGINFO << "grabThreadSleep: " << timeElapsed << "s";

   timeElapsed = TIMER_READ_SEC("scanThreadSleep");
   LOGINFO << "scanThreadSleep: " << timeElapsed << "s";
   
   return lastScannedBlockHash;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BlockWriteBatcher::scanBlocks(
   ProgressFilter &prog,
   uint32_t startBlock, uint32_t endBlock, 
   ScrAddrFilter& scf
)
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

   shared_ptr<LoadedBlockData> tempBlockData = 
      make_shared<LoadedBlockData>(startBlock, endBlock, scf, nThreads);

   BinaryData bd = applyBlocksToDB(prog, tempBlockData);

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
bool BlockWriteBatcher::pullBlockAtIter(PulledBlock& pb, LDBIter& iter,
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

   return pullBlockAtIter(pb, ldbIter, iface_, bfa);
}


////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::resetHistoryTransaction(void)
{
   if (resetWriterPtr_.load(memory_order_acquire) != nullptr)
   {
      TIMER_START("resetTxn");
      shared_ptr<BlockWriteBatcher>* writer = 
         resetWriterPtr_.load(memory_order_acquire);
      resetWriterPtr_.store(nullptr, memory_order_release);

      resetTransactions();

      unique_lock<mutex> lock((*writer)->writeLock_);
      if (commitingObject_ == *writer)
      {
         //commitingObject_->subSshMapToWrite_ = move(subSshMapToWrite_);
         commitingObject_.reset();
      }

      (*writer)->cleanupFlag_.store(true, memory_order_release);
      (*writer)->signalCleanup_.notify_all();
      TIMER_STOP("resetTxn");
   }
}

////////////////////////////////////////////////////////////////////////////////
/// DataToCommit
////////////////////////////////////////////////////////////////////////////////
void DataToCommit::serializeSSH(shared_ptr<BlockWriteBatcher> bwb)
{
   auto dbType = bwb->config_.armoryDbType;
   auto pruneType = bwb->config_.pruneType;

   auto& subsshMap = bwb->subSshMap_;

   sshHeaders_->getSshHeaders(bwb);
   
   auto& sshMap = sshHeaders_->sshToModify_;
   for (auto& sshPair : *sshMap)
   {
      BinaryData sshKey;
      sshKey.append(WRITE_UINT8_LE(DB_PREFIX_SCRIPT));
      sshKey.append(sshPair.first);
      
      auto& ssh = sshPair.second;
      auto subsshIter = subsshMap.find(sshPair.first);

      if (subsshIter != subsshMap.end())
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
                     if (!txio.isMultisig())
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

         if (dbType == ARMORY_DB_SUPER)
         {
            if (ssh.totalTxioCount_ > 0)
            {
               ssh.alreadyScannedUpToBlk_ = bwb->mostRecentBlockApplied_;
               BinaryWriter& bw = serializedSshToModify_[sshKey];
               ssh.serializeDBValue(bw, dbType, pruneType);
            }
            else
               sshKeysToDelete_.insert(sshKey);
         }
      }

      if (dbType != ARMORY_DB_SUPER)
      {
         ssh.alreadyScannedUpToBlk_ = bwb->mostRecentBlockApplied_;
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

   auto dbType = stxos.dbType_;
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
void DataToCommit::serializeDataToCommit(shared_ptr<BlockWriteBatcher> bwb)
{
   auto dbType = bwb->config_.armoryDbType;
   auto pruneType = bwb->config_.pruneType;

   auto& subsshMap = bwb->subSshMap_;

   //subssh
   {
      for (auto& sshPair : subsshMap)
      {
         uint32_t keysize = sshPair.first.getSize();
         BinaryData subkey(keysize +4);
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
   serializeStxo(bwb->stxos_);

   //txOutCount
   if (dbType != ARMORY_DB_SUPER)
   {
      LMDBEnv::Transaction txHints(bwb->iface_->dbEnv_[TXHINTS].get(), LMDB::ReadOnly);
      for (auto& txData : bwb->txCountAndHint_)
      {
         BinaryWriter& bw = serializedTxCountAndHash_[txData.first];
         bw.put_uint32_t(txData.second.count_);
         bw.put_BinaryData(txData.second.hash_);

         BinaryDataRef ldbKey = txData.first.getSliceRef(1, 6);
         StoredTxHints sths;
         bwb->iface_->getStoredTxHints(sths, txData.second.hash_);

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

   topBlockHash_ = bwb->topScannedBlockHash_;
   mostRecentBlockApplied_ = bwb->mostRecentBlockApplied_ +1;
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::serializeData(shared_ptr<BlockWriteBatcher> bwb)
{
   if (isSerialized_)
      return;

   uint32_t nThreads = getProcessSSHnThreads();
   sshHeaders_.reset(new SSHheaders(db_, nThreads));

   unique_lock<mutex> lock(sshHeaders_->mu_);

   auto& subsshMap = bwb->subSshMap_;

   auto serialize = [&](void)
   { serializeDataToCommit(bwb); };

   thread serThread = thread(serialize);

   serializeSSH(bwb);
   lock.unlock();

   if (serThread.joinable())
      serThread.join();

   for (auto& inbw : intermidiarrySubSshToApply_)
   {
      auto& sshkey = sshPrefixes_[inbw.first];
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
   db_->beginDBTransaction(&tx, HISTORY, LMDB::ReadWrite);

   auto putThread = [this](uint32_t keyLength)->void
   { this->putSubSSH(keyLength); };

   vector<thread> subSshThreads;
   for (auto& submap : serializedSubSshToApply_)
      subSshThreads.push_back(thread(putThread, submap.first));

   for (auto& sshPair : serializedSshToModify_)
      db_->putValue(HISTORY, sshPair.first, sshPair.second.getData());

   for (auto& writeThread : subSshThreads)
      if (writeThread.joinable())
         writeThread.join();
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::putSubSSH(uint32_t keyLength)
{
   LMDBEnv::Transaction subsshtx;

   db_->beginSubSSHDBTransaction(subsshtx,
      keyLength, LMDB::ReadWrite);

   auto& submap = serializedSubSshToApply_[keyLength];

   for (auto& subsshentry : submap)
      db_->putValue(keyLength, subsshentry.first,
      subsshentry.second.getData());
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::putSTX()
{
   if (serializedStxOutToModify_.size() > 0)
   {
      LMDBEnv::Transaction tx(db_->dbEnv_[STXO].get(), LMDB::ReadWrite);

      for (auto& stxoPair : serializedStxOutToModify_)
         db_->putValue(STXO, stxoPair.first, stxoPair.second.getData());
   }

   {
      LMDBEnv::Transaction tx(db_->dbEnv_[SPENTNESS].get(), LMDB::ReadWrite);

      for (auto& spentness : serializedSpentness_)
         db_->putValue(SPENTNESS, spentness.first, spentness.second.getData());

      for (auto& delKey : spentnessToDelete_)
         db_->deleteValue(SPENTNESS, delKey);
   }
   
   if (dbType_ == ARMORY_DB_SUPER)
      return;
   
   {
      LMDBEnv::Transaction tx(db_->dbEnv_[HISTORY].get(), LMDB::ReadWrite);

      for (auto& txCount : serializedTxCountAndHash_)
         db_->putValue(HISTORY, txCount.first, txCount.second.getData());

      ////
      LMDBEnv::Transaction txHints(db_->dbEnv_[TXHINTS].get(), LMDB::ReadWrite);
      for (auto& txHints : serializedTxHints_)
      db_->putValue(TXHINTS, txHints.first, txHints.second.getData());
   }
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::deleteEmptyKeys()
{
   {
      LMDBEnv::Transaction tx;
      db_->beginDBTransaction(&tx, HISTORY, LMDB::ReadWrite);

      for (auto& toDel : sshKeysToDelete_)
         db_->deleteValue(HISTORY, toDel.getRef());
   }

   for (auto& subset : subSshKeysToDelete_)
   {
      uint32_t keySize = subset.first;

      LMDBEnv::Transaction subtx;
      db_->beginSubSSHDBTransaction(subtx, keySize, LMDB::ReadWrite);

      for (auto& ktd : subset.second)
         db_->deleteValue(keySize, ktd.getRef());
   }
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::updateSDBI()
{
   LMDBEnv::Transaction tx;
   db_->beginDBTransaction(&tx, HISTORY, LMDB::ReadWrite);

   StoredDBInfo sdbi;
   db_->getStoredDBInfo(HISTORY, sdbi);
   if (!sdbi.isInitialized())
      LOGERR << "How do we have invalid SDBI in applyMods?";
   else
   {
      //save top block height
      sdbi.appliedToHgt_ = mostRecentBlockApplied_;

      //save top block hash
      if (topBlockHash_ != BtcUtils::EmptyHash_)
         sdbi.topScannedBlkHash_ = topBlockHash_;

      db_->putStoredDBInfo(HISTORY, sdbi);
   }
}

////////////////////////////////////////////////////////////////////////////////
DataToCommit::DataToCommit(DataToCommit&& dtc) :
   dbType_(dtc.dbType_)
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

   if (utxoMapBackup_.size() > 0)
   {
      stxoIter = utxoMapBackup_.find(hashAndId);
      if (stxoIter != utxoMapBackup_.end())
      {
         stxoToUpdate_.push_back(stxoIter->second);

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
   if (dbType_ != ARMORY_DB_SUPER)
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

   if (utxoMapBackup_.size() > 0)
   {
      utxoIter = utxoMapBackup_.find(txHash);
      if (utxoIter != utxoMapBackup_.end())
      {
         stxoToUpdate_.push_back(utxoIter->second);
         TIMER_STOP("leverageUTXOinRAM");
         return stxoToUpdate_.back().get();
      }
   }

   TIMER_STOP("leverageUTXOinRAM");

   if (dbType_ == ARMORY_DB_SUPER)
   {
      TIMER_START("lookforutxo");

      shared_ptr<StoredTxOut> stxo(new StoredTxOut);
      BinaryData dbKey;
      if (!iface_->getStoredTx_byHash(txHash.getSliceRef(0, 32), nullptr, &dbKey))
      {
         LOGERR << "missing txhint in supenode";
         throw runtime_error("missing txhint in supernode");
      }

      uint32_t txoId = READ_UINT16_BE(txHash.getPtr() + 32);
      dbKey.append(WRITE_UINT16_BE(txoId));
      if (!iface_->getUnspentTxOut(*stxo, dbKey))
      {
         LOGERR << "missing txout in supernode";
         throw runtime_error("missing txout in supernode");
      }

      stxoToUpdate_.push_back(stxo);
      
      TIMER_STOP("lookforutxo");

      return stxoToUpdate_.back().get();
   }

   return nullptr;
}

////////////////////////////////////////////////////////////////////////////////
thread STXOS::commitStxo(bool waitOnCleanup)
{
   //same syncing mechanism with the write threed as with 
   //BlockWriteBatcher::commit(bool)

   TIMER_START("inCommitStxo");
   bool isCommiting = true;
   
   {
      unique_lock<mutex> lock(*(writeMutex_.get()), try_to_lock);
      if (lock.owns_lock())
         isCommiting = false;
   }

   shared_ptr<STXOS> toCommit(new STXOS(*this));
   
   shared_ptr<STXOS>* nextPtr = &nextStxo_;
   while (*nextPtr != nullptr)
      nextPtr = &(*nextPtr)->nextStxo_;


   toCommit->waitOnCleanup_ = waitOnCleanup;

   toCommit->stxoToUpdate_ = std::move(stxoToUpdate_);
   if (isCommiting)
   {
      toCommit->dataToCommit_.serializeStxo(*toCommit);
      toCommit->dataToCommit_.isSerialized_ = true;
   }

   /***
   utxoMapBackup_ has to be valid until its corresponding write thread has
   completed and the db RO transaction has been recycled. The simplest way
   to make sure the containers remain consistent accross threads is to wait
   on the write mutex
   ***/

   TIMER_START("preppingStxoWrite");
   if (utxoMapBackup_.size() > 0)
      nextStxo_->utxoMapBackup_ = move(utxoMapBackup_);

   utxoMapBackup_ = std::move(utxoMap_);
   TIMER_STOP("preppingStxoWrite");
   
   unique_lock<mutex> lock(*writeMutex_);
   *nextPtr = toCommit;

   thread committhread(writeStxoToDB, toCommit);

   TIMER_STOP("inCommitStxo");
   return committhread;
}

////////////////////////////////////////////////////////////////////////////////
void STXOS::commit()
{
   if (stxoToUpdate_.size() > STXO_THRESHOLD ||
      utxoMap_.size() > UTXO_THRESHOLD)
   {
      auto committhread = commitStxo(true);
      if (committhread.joinable())
         committhread.detach();
   }
}

////////////////////////////////////////////////////////////////////////////////
void STXOS::writeStxoToDB(shared_ptr<STXOS> stxos)
{
   {
      unique_lock<mutex> lock(*(stxos->writeMutex_));
      LMDBBlockDatabase *db = stxos->iface_;
      stxos->dataToCommit_.serializeStxo(*stxos);

      stxos->dataToCommit_.putSTX();
   }

   if (stxos->waitOnCleanup_)
   {
      stxos->resetTxn_.store(true, memory_order_release);

      unique_lock<mutex> sgn(stxos->signalMutex_);
      while (!stxos->cleanup_.load(memory_order_acquire))
         stxos->signalCV_.wait(sgn);
   }

   stxos.reset();
}

////////////////////////////////////////////////////////////////////////////////
void STXOS::resetTransactions()
{
   dbTxn_.commit();
   dbTxn_.open(iface_->dbEnv_[STXO].get(), LMDB::ReadOnly);
}

////////////////////////////////////////////////////////////////////////////////
void STXOS::recycleTxn(void)
{
   shared_ptr<STXOS> next = nextStxo_;
   if (next == nullptr)
      return;

   if (!next->resetTxn_.load(memory_order_acquire))
      return;

   resetTransactions();

   if (next->utxoMapBackup_.size() == 0)
      next->utxoMapBackup_ = move(utxoMapBackup_);

   if (next->nextStxo_ != nullptr)
      nextStxo_ = next->nextStxo_;
   else 
      nextStxo_.reset();

   next->cleanup_.store(true, memory_order_release);

   unique_lock<mutex> lock(next->signalMutex_);
   next->signalCV_.notify_all();
}

////////////////////////////////////////////////////////////////////////////////
////SSHheaders
////////////////////////////////////////////////////////////////////////////////
void SSHheaders::getSshHeaders(shared_ptr<BlockWriteBatcher> bwb)
{
   TIMER_START("getParentSshToModify");
   if (db_->armoryDbType() != ARMORY_DB_SUPER)
   {
      shared_ptr<SSHheaders> parent = bwb->parent_->dataToCommit_.sshHeaders_;
      unique_lock<mutex> lock(parent->mu_);
      sshToModify_ = parent->sshToModify_;
      return;
   }

   shared_ptr<SSHheaders> commitingHeaders = nullptr;

   {
      shared_ptr<BlockWriteBatcher> commitingObj = nullptr;
      if (bwb->parent_ != nullptr)
      {
         if (bwb->parent_->dataToCommit_.sshHeaders_ != nullptr)
         {
            //parent has a valid SSHheaders object, just use that
            commitingHeaders = bwb->parent_->dataToCommit_.sshHeaders_;
         }
         else commitingObj = bwb->parent_->commitingObject_;
      }

      if (commitingObj != nullptr)
         commitingHeaders = commitingObj->dataToCommit_.sshHeaders_;
   }
   TIMER_STOP("getParentSshToModify");

   if (commitingHeaders != nullptr && commitingHeaders.get() != this)
   {
      unique_lock<mutex> lock(commitingHeaders->mu_);
      processSshHeaders(
         bwb->subSshMap_, *commitingHeaders->sshToModify_);
   }
   else
   {
      processSshHeaders(
         bwb->subSshMap_, map<BinaryData, StoredScriptHistory>());
   }
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::processSshHeaders(
   const map <BinaryData, map<BinaryData, StoredSubHistory>>& subsshMap,
   const map<BinaryData, StoredScriptHistory>& prevSshToModify)
{
   TIMER_START("processHeaders");
   sshToModify_.reset(new map<BinaryData, StoredScriptHistory>());
   vector<BinaryData> saStart;

   if (subsshMap.size() == 0)
      return;

   int i = 0, cut = subsshMap.size() / nThreads_;
   if (cut == 0)
      cut = subsshMap.size();

   for (auto& subssh : subsshMap)
   {
      StoredScriptHistory& ssh = (*sshToModify_)[subssh.first];

      auto sshIter = prevSshToModify.find(subssh.first);
      if (sshIter != prevSshToModify.end())
         ssh = sshIter->second;

      if (i % cut == 0)
         saStart.push_back(subssh.first);

      i++;
   }

   auto processSshThread = [this](const BinaryData& start, uint32_t count)->void
   { this->fetchSshHeaders(start, count); };

   int curNThreads = saStart.size() -1;

   vector<thread> vecTh;
   for (i = 0; i < curNThreads; i++)
      vecTh.push_back(thread(processSshThread, saStart[i+1], cut));

   processSshThread(saStart[0], cut);

   for (i = 0; i < curNThreads; i++)
      if (vecTh[i].joinable())
         vecTh[i].join();

   //check for key collisions
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

   TIMER_STOP("processHeaders");
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::fetchSshHeaders(const BinaryData& start, uint32_t count)
{
   auto iter = sshToModify_->find(start);

   uint32_t i = 0;
   uint32_t distribute = 0;
   while(iter != sshToModify_->end() && i<=count)
   {
      auto& ssh = iter->second;
      if (ssh.keyLength_ == 0)
      {
         db_->getStoredScriptHistorySummary(ssh, iter->first);
         if (!ssh.isInitialized())
         {
            BinaryData key = db_->getSubSSHKey(iter->first);
            ssh.uniqueKey_ = iter->first;
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

      ++iter;
      ++i;
   }
}

////////////////////////////////////////////////////////////////////////////////
void SSHheaders::buildSshHeadersFromSAF(const ScrAddrFilter& SAF)
{
   //for (auto saPair : sasd.getScrAddrMap())
   map<BinaryData, map<BinaryData, StoredSubHistory>> subsshMap;

   auto& saMap = SAF.getScrAddrMap();

   for (auto& sa : saMap)
      subsshMap.insert(
         make_pair(sa.first, map<BinaryData, StoredSubHistory>()));

   processSshHeaders(subsshMap, map<BinaryData, StoredScriptHistory>());
}
