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
// This avoids having to do the double-lookup when fetching by hash.
// We still pass in the hash anyway, because the map is indexed by the hash,
// and we'd like to not have to do a lookup for the hash if only provided
// {hgt, dup, idx}
StoredTxOut* BlockWriteBatcher::makeSureSTXOInMap(
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

   stxoIter = utxoMapBackup_.find(hashAndId);
   if (stxoIter != utxoMapBackup_.end())
   {
      stxoToUpdate_.push_back(stxoIter->second);
      utxoMapBackup_.erase(stxoIter);

      return stxoToUpdate_.back().get();
   }

   shared_ptr<StoredTxOut> stxo(new StoredTxOut);
   BinaryData dbKey;
   iface->getStoredTx_byHash(txHash, nullptr, &dbKey);
   dbKey.append(WRITE_UINT16_BE(txoId));
   iface->getStoredTxOut(*stxo, dbKey);

   dbUpdateSize_ += sizeof(StoredTxOut) + stxo->dataCopy_.getSize();
   stxoToUpdate_.push_back(move(stxo));

   return stxoToUpdate_.back().get();
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::moveStxoToUTXOMap(
   const shared_ptr<StoredTxOut>& thisTxOut)
{
   stxoToUpdate_.push_back(thisTxOut);
   dbUpdateSize_ += sizeof(StoredTxOut)+thisTxOut->dataCopy_.getSize();

   utxoMap_[thisTxOut->hashAndId_] = thisTxOut; 
}

////////////////////////////////////////////////////////////////////////////////
StoredTxOut* BlockWriteBatcher::lookForUTXOInMap(const BinaryData& txHash, 
   const uint16_t& txoId)
{
   auto utxoIter = utxoMap_.find(txHash);
   if (utxoIter != utxoMap_.end())
   {
      stxoToUpdate_.push_back(utxoIter->second);

      return utxoIter->second.get();
   }

   utxoIter = utxoMapBackup_.find(txHash);
   if (utxoIter != utxoMapBackup_.end())
   {
      stxoToUpdate_.push_back(utxoIter->second);

      return utxoIter->second.get();
   }

   if (config_.armoryDbType == ARMORY_DB_SUPER)
   {
      shared_ptr<StoredTxOut> stxo(new StoredTxOut);
      BinaryData dbKey;
      iface_->getStoredTx_byHash(txHash.getSliceRef(0, 32), nullptr, &dbKey);
      dbKey.append(WRITE_UINT16_BE(txoId));
      iface_->getStoredTxOut(*stxo, dbKey);

      dbUpdateSize_ += sizeof(StoredTxOut)+stxo->dataCopy_.getSize();
      stxoToUpdate_.push_back(stxo);

      return stxoToUpdate_.back().get();
   }

   return nullptr;
}
////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::getSshHeader(
   StoredScriptHistory& ssh, const BinaryData& uniqKey) const
{
   iface_->getStoredScriptHistorySummary(ssh, uniqKey);
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
      if (subSshMapToWrite_.size() != 0)
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
      }

      subssh.hgtX_ = hgtX;

      BinaryData key(uniqKey);
      key.append(hgtX);

      BinaryRefReader brr = iface_->getValueReader(BLKDATA, DB_PREFIX_SCRIPT, key);
      if (brr.getSize() > 0)
         subssh.unserializeDBValue(brr);
      
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
      uint32_t fetchHeight = DBUtils::hgtxToHeight(hgtX);
      subssh.hgtX_ = hgtX;

      if (fetchHeight < currentBlockHeight)
      {
         BinaryData key(uniqKey);
         key.append(hgtX);

         BinaryRefReader brr = iface_->getValueReader(BLKDATA, DB_PREFIX_SCRIPT, key);
         if (brr.getSize() > 0)
            subssh.unserializeDBValue(brr);
      }

      dbUpdateSize_ += UPDATE_BYTES_SUBSSH;
   }

   return subssh;
}

////////////////////////////////////////////////////////////////////////////////
StoredScriptHistory& BlockWriteBatcher::makeSureSSHInMap(
   const BinaryData& uniqKey)
{  
   auto& ssh = (*sshToModify_)[uniqKey];
   if (!ssh.isInitialized())
   {
      getSshHeader(ssh, uniqKey);
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
}

////////////////////////////////////////////////////////////////////////////////
BlockWriteBatcher::BlockWriteBatcher(
   const BlockDataManagerConfig &config,
   LMDBBlockDatabase* iface,
   bool forCommit
)
   : config_(config), iface_(iface),
   mostRecentBlockApplied_(0), isForCommit_(forCommit)
{
   parent_ = this;
}

BlockWriteBatcher::~BlockWriteBatcher()
{
   //a BWB meant for commit doesn't need to run commit() on dtor
   if (isForCommit_)
   {
      clearTransactions();
      return;
   }

   //call final commit, force it
   thread committhread = commit(true);

   //join on the thread, don't want the destuctor to return until the data has
   //been commited
   committhread.join();
   clearTransactions();
}

BinaryData BlockWriteBatcher::applyBlockToDB(PulledBlock& pb,
   ScrAddrFilter& scrAddrData)
{
   //TIMER_START("applyBlockToDBinternal");
   if(iface_->getValidDupIDForHeight(pb.blockHeight_) != pb.duplicateID_)
   {
      LOGERR << "Dup requested is not the main branch for the given height!";
      return BinaryData();
   }
   else
      pb.isMainBranch_ = true;
   
   mostRecentBlockApplied_ = pb.blockHeight_;

   // We will accumulate undoData as we apply the tx
   StoredUndoData sud;
   sud.blockHash_   = pb.thisHash_;
   sud.blockHeight_ = pb.blockHeight_;
   sud.duplicateID_ = pb.duplicateID_;
   
   sbhToUpdate_.push_back(move(pb));

   auto& block = sbhToUpdate_.back();
   // Apply all the tx to the update data
   for (auto& stx : block.stxMap_)
   {
      if (stx.second.dataCopy_.getSize() == 0)
      {
         LOGERR << "bad STX data in applyBlockToDB at height " << pb.blockHeight_;
         throw std::range_error("bad STX data while applying blocks");
      }

      applyTxToBatchWriteData(stx.second, &sud, scrAddrData);
   }

   // At this point we should have a list of STX and SSH with all the correct
   // modifications (or creations) to represent this block.  Let's apply it.
   BinaryData scannedBlockHash = block.thisHash_;
   block.blockAppliedToDB_ = true;
   dbUpdateSize_ += block.numBytes_;

   if (dbUpdateSize_ > UPDATE_BYTES_THRESH)
   {
      thread committhread = commit();
      if (committhread.joinable())
         committhread.detach();
   }

   return scannedBlockHash;
}

void BlockWriteBatcher::reorgApplyBlock(uint32_t hgt, uint8_t dup, 
   ScrAddrFilter& scrAddrData)
{
   forceUpdateSsh_ = true;

   resetTransactions();

   prepareSshToModify(scrAddrData);

   PulledBlock pb;
   pullBlockFromDB(pb, hgt, dup);
   if (pb.blockHeight_ == UINT32_MAX)
   {
      LOGERR << "Failed to load block " << hgt << "," << dup;
      return;
   }
   applyBlockToDB(pb, scrAddrData);

   thread writeThread = commit(true);
   if (writeThread.joinable())
      writeThread.join();

   clearTransactions();
}


////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::undoBlockFromDB(StoredUndoData & sud, 
                                        ScrAddrFilter& scrAddrData)
{
   if (resetTxn_ > 0)
      clearSubSshMap(resetTxn_);

   prepareSshToModify(scrAddrData);

   resetTransactions();

   PulledBlock pb;
   pullBlockFromDB(pb, sud.blockHeight_, sud.duplicateID_);

   if(!pb.blockAppliedToDB_)
   {
      LOGERR << "This block was never applied to the DB...can't undo!";
      return;
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

      StoredTxOut* stxoPtr = makeSureSTXOInMap( 
               iface_,
               sudStxo.parentHash_,
               stxoIdx);

      if(config_.pruneType == DB_PRUNE_NONE)
      {
         // If full/super, we have the TxOut in DB, just need mark it unspent
         if(stxoPtr->spentness_ == TXOUT_UNSPENT || 
            stxoPtr->spentByTxInKey_.getSize() == 0 )
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
            false
         );
         
         auto& ssh = makeSureSSHInMap(uniqKey);
         ssh.totalUnspent_ += stxoPtr->getValue();

         //delete the spent subssh at TxIn hgtX
         if (sudStxo.spentness_ == TXOUT_SPENT)
         {
            hgtX = sudStxo.spentByTxInKey_.getSliceCopy(0, 4);
            StoredSubHistory& subsshAtInHgt = 
               makeSureSubSSHInMap(uniqKey, hgtX);

            subsshAtInHgt.eraseTxio(sudStxo.getDBKey(false));
            ssh.totalTxioCount_--;
         }
      }
   }


   // The OutPoint list is every new, unspent TxOut created by this block.
   // When they were added, we updated all the StoredScriptHistory objects
   // to include references to them.  We need to remove them now.
   // Use int32_t index so that -1 != UINT32_MAX and we go into inf loop
   for(int16_t itx=pb.numTx_-1; itx>=0; itx--)
   {
      // Ironically, even though I'm using hgt & dup, I still need the hash
      // in order to key the stxToModify map
      BinaryData txHash = iface_->getHashForDBKey(pb.blockHeight_,
                                                  pb.duplicateID_,
                                                  itx);

      StoredTx stx;
      if (!iface_->getStoredTx(stx, txHash))
      {
         LOGERR << "could not grab STX for hash: " << txHash.toHexStr(false);
         throw std::runtime_error("iface->getStoredTx failed in undoBlockFromDB");
      }

      for(int16_t txoIdx = (int16_t)stx.stxoMap_.size()-1; txoIdx >= 0; txoIdx--)
      {
         StoredTxOut & stxo    = stx.stxoMap_[txoIdx];
         BinaryData    stxoKey = stxo.getDBKey(false);
   
         // Then fetch the StoredScriptHistory of the StoredTxOut scraddress
         BinaryData uniqKey = stxo.getScrAddress();
         if (config_.armoryDbType != ARMORY_DB_SUPER)
         {
            if (!scrAddrData.hasScrAddress(uniqKey))
               continue;
         }

         BinaryData hgtX    = stxo.getHgtX();
         StoredSubHistory& subssh =
            makeSureSubSSHInMap(uniqKey, hgtX);
   
         subssh.eraseTxio(stxoKey);
         auto& ssh = makeSureSSHInMap(uniqKey);
         ssh.totalTxioCount_--;
         ssh.totalUnspent_ -= stxo.getValue();
   
         // Now remove any multisig entries that were added due to this TxOut
         if(uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
         {
            vector<BinaryData> addr160List;
            BtcUtils::getMultisigAddrList(stxo.getScriptRef(), addr160List);
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
   sbhToUpdate_.push_back(move(pb));
   
   clearTransactions();
   
   if (dbUpdateSize_ > UPDATE_BYTES_THRESH)
   {
      thread committhread = commit();
      if (committhread.joinable())
         committhread.join();
   }
}

bool BlockWriteBatcher::parseTxIns(
   PulledTx& thisSTX, 
   StoredUndoData * sud, 
   ScrAddrFilter& scrAddrData)
{
   for (uint32_t iin = 0; iin < thisSTX.txInIndexes_.size() - 1; iin++)
   {
      // Get the OutPoint data of TxOut being spent
      BinaryData opTxHashAndId =
         thisSTX.dataCopy_.getSliceCopy(thisSTX.txInIndexes_[iin], 32);

      if (opTxHashAndId == BtcUtils::EmptyHash_)
         continue;

      const uint32_t opTxoIdx =
         READ_UINT32_LE(thisSTX.dataCopy_.getPtr() + thisSTX.txInIndexes_[iin] + 32);

      opTxHashAndId.append(WRITE_UINT16_BE(opTxoIdx));

      //For scanning a predefined set of addresses, check if this txin 
      //consumes one of our utxo

      //leveraging the stxo in RAM
      StoredTxOut* stxoPtr = nullptr;
      stxoPtr = lookForUTXOInMap(opTxHashAndId, opTxoIdx);

      if (config_.armoryDbType != ARMORY_DB_SUPER)
      {
         if (stxoPtr == nullptr)
         {
            //if we have a list of all relevant UTXO and we couldnt find this
            //one in there, then it isnt a relevant UTXO and we can skip it
            if (haveFullUTXOList_)
            {
               if (thisSTX.blockHeight_ > utxoFromHeight_)
                  continue;
            }

            //otherwise we need to grab it and check it against our scrAddr
            //list. UTXO are consumed only once so we do not need to keep
            //this one in RAM if it turns out it isn't relevant
            shared_ptr<StoredTxOut> stxoToSpend(new StoredTxOut);
            BinaryData dbKey;
            iface_->getStoredTx_byHash(opTxHashAndId.getSliceRef(0, 32), nullptr, &dbKey);
            dbKey.append(WRITE_UINT16_BE(opTxoIdx));
            iface_->getStoredTxOut(*stxoToSpend, dbKey);

            if (!scrAddrData.hasScrAddress(stxoToSpend->getScrAddress()))
               continue;
           
            dbUpdateSize_ += sizeof(StoredTxOut)+stxoToSpend->dataCopy_.getSize();

            stxoToUpdate_.push_back(stxoToSpend);
            stxoPtr = stxoToSpend.get();
         }
      }
      
      const BinaryData& uniqKey = stxoPtr->getScrAddress();
      BinaryData stxoKey = stxoPtr->getDBKey(false);

      // Need to modify existing UTXOs, so that we can delete or mark as spent
      stxoPtr->spentByTxInKey_ = thisSTX.getDBKeyOfChild(iin, false);
      stxoPtr->spentness_ = TXOUT_SPENT;

      ////// Now update the SSH to show this TxIOPair was spent
      // Same story as stxToModify above, except this will actually create a new
      // SSH if it doesn't exist in the map or the DB
      BinaryData& hgtX = stxoPtr->getHgtX();

      StoredSubHistory& subssh = makeSureSubSSHInMap(uniqKey, hgtX);
      
      StoredSubHistory& mirrorsubssh = 
         makeSureSubSSHInMap_IgnoreDB(
            uniqKey, 
            stxoPtr->spentByTxInKey_.getSliceRef(0, 4),
            0);

      // update the txio in its subSSH
      auto& txio = subssh.markTxOutSpent(stxoKey);
         
      //Mirror the spent txio at txin height
      insertSpentTxio(txio, mirrorsubssh, stxoKey, stxoPtr->spentByTxInKey_);
   }

   return true;
}

bool BlockWriteBatcher::parseTxOuts(
   PulledTx& thisSTX,
   StoredUndoData * sud,
   ScrAddrFilter& scrAddrData)
{
   for (auto& stxoPair : thisSTX.stxoMap_)
   {
      auto& stxoToAdd = *stxoPair.second;
      const BinaryData& uniqKey = stxoToAdd.getScrAddress();
      BinaryData hgtX = stxoToAdd.getHgtX();

      if (config_.armoryDbType != ARMORY_DB_SUPER)
      {
         if (!scrAddrData.hasScrAddress(uniqKey))
            continue;
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
         dbUpdateSize_ += sizeof(TxIOPair)+8;
      }
      else
      {
         subssh.markTxOutUnspent(
            stxoToAdd.getDBKey(false),
            dbUpdateSize_,
            stxoToAdd.getValue(),
            stxoToAdd.isCoinbase_,
            false);
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
               true);
         }
      }

      moveStxoToUTXOMap(stxoPair.second);
   }

   return true;
}

////////////////////////////////////////////////////////////////////////////////
// Assume that stx.blockHeight_ and .duplicateID_ are set correctly.
// We created the maps and sets outside this function, because we need to keep
// a master list of updates induced by all tx in this block.  
// TODO:  Make sure that if Tx5 spends an input from Tx2 in the same 
//        block that it is handled correctly, etc.
bool BlockWriteBatcher::applyTxToBatchWriteData(
                        PulledTx& thisSTX,
                        StoredUndoData * sud,
                        ScrAddrFilter& scrAddrData)
{
   parseTxOuts(thisSTX, sud, scrAddrData);
   parseTxIns( thisSTX, sud, scrAddrData);

   return true;
}

////////////////////////////////////////////////////////////////////////////////
thread BlockWriteBatcher::commit(bool finalCommit)
{
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
         return thread();

      isCommiting = true;
   }
   else
      l.unlock();

   //create a BWB for commit (pass true to the constructor)
   auto bwbWriteObj = shared_ptr<BlockWriteBatcher>(
     new BlockWriteBatcher(config_, iface_, true));
   
   if (forceUpdateSsh_)
   {
      bwbWriteObj->dataToCommit_.forceUpdateSshAtHeight_ =
         mostRecentBlockApplied_ -1;
   }
   
   bwbWriteObj->commitId_ = commitId_++;

   bwbWriteObj->sbhToUpdate_ = std::move(sbhToUpdate_);
   bwbWriteObj->stxoToUpdate_ = std::move(stxoToUpdate_);
   
   bwbWriteObj->mostRecentBlockApplied_ = mostRecentBlockApplied_;
   bwbWriteObj->parent_ = this;

   if (utxoMap_.size() > UTXO_THRESHOLD)
   {
      utxoMapBackup_.clear();
      utxoMapBackup_ = std::move(utxoMap_);
      haveFullUTXOList_ = false;
   }

   if (isCommiting)
   {
      //the write thread is already running and we cumulated enough data in the
      //read thread for the next write. Let's use that idle time to serialize
      //the data to commit ahead of time
      bwbWriteObj->serializeData(subSshMap_);
   }
      
   deleteId_++;

   bwbWriteObj->dbUpdateSize_ = dbUpdateSize_;
   bwbWriteObj->updateSDBI_ = updateSDBI_;
   bwbWriteObj->deleteId_ = deleteId_;
      
   dbUpdateSize_ = 0;

   auto write = [](shared_ptr<BlockWriteBatcher> obj)->void
   { obj->writeToDB(); };

   l.lock();
   subSshMapToWrite_ = std::move(subSshMap_);
   commitingObject_ = bwbWriteObj;

   if (isCommiting)
      resetTransactions();

   thread committhread(write, bwbWriteObj);

   return committhread;
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::prepareSshToModify(const ScrAddrFilter& sasd)
{
   //In full mode, the sshToModify_ container is not wiped after each commit.
   //Instead, all SSH for tracked scrAddr, since we know they're the onyl one
   //that will get any traffic, and in order to update all alreadyScannedUpToBlk_
   //members each commit

   //pass a 0 size BinaryData to avoid loading any subSSH

   if (sshToModify_)
      return;

   sshToModify_ = shared_ptr<map<BinaryData, StoredScriptHistory>>(
      new map<BinaryData, StoredScriptHistory>);
   
   if (config_.armoryDbType == ARMORY_DB_SUPER)
      return;

   BinaryData hgtX(0);

   uint32_t utxoCount=0;
   LMDBEnv::Transaction tx(&iface_->dbEnv_, LMDB::ReadOnly);

   StoredDBInfo sdbi;
   iface_->getStoredDBInfo(BLKDATA, sdbi);
   utxoFromHeight_ = sdbi.topBlkHgt_;

   for (auto saPair : sasd.getScrAddrMap())
   {
      auto& ssh = (*sshToModify_)[saPair.first];
      getSshHeader(ssh, saPair.first);

      if (ssh.totalTxioCount_ != 0 &&
          utxoCount + ssh.totalTxioCount_ < UTXO_THRESHOLD)
      {
         BinaryWriter bwKey(saPair.first.getSize() + 1);
         bwKey.put_uint8_t((uint8_t)DB_PREFIX_SCRIPT);
         bwKey.put_BinaryData(saPair.first);

         LDBIter dbIter = iface_->getIterator(BLKDATA);

         dbIter.seekToExact(bwKey.getDataRef());
         while (dbIter.getKeyRef().startsWith(bwKey.getDataRef()))
         {
            if (dbIter.getKeyRef().getSize()==bwKey.getSize() +4)
            {
               //grab subssh
               StoredSubHistory subssh;
               subssh.hgtX_ = dbIter.getKeyRef().getSliceRef(-4, 4);
               subssh.unserializeDBValue(dbIter.getValueReader());

               //load all UTXOs listed
               for (auto txio : subssh.txioMap_)
               {
                  if (txio.second.isUTXO())
                  {
                     BinaryData dbKey = txio.second.getDBKeyOfOutput();
                     shared_ptr<StoredTxOut> stxo(new StoredTxOut);
                     iface_->getStoredTxOut(*stxo, dbKey);
                     
                     BinaryData txHash = iface_->getTxHashForLdbKey(dbKey.getSliceRef(0, 6));

                     BinaryWriter bwUtxoKey(34);
                     bwUtxoKey.put_BinaryData(txHash);
                     bwUtxoKey.put_uint16_t(stxo->txOutIndex_, BE);
                     
                     utxoMap_[bwUtxoKey.getDataRef()] = stxo;
                     utxoCount++;
                  }
               }
            }
               
            dbIter.advanceAndRead(DB_PREFIX_SCRIPT);
         }
      }
      else haveFullUTXOList_ = false;
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::writeToDB(void)
{
   unique_lock<mutex> lock(parent_->writeLock_);

   dataToCommit_.serializeData(*this, parent_->subSshMapToWrite_);

   txn_.open(&iface_->dbEnv_, LMDB::ReadWrite);

   {
      dataToCommit_.putSSH(iface_);

      txn_.commit();
      txn_.begin();

      dataToCommit_.putSTX(iface_);

      txn_.commit();
      txn_.begin();

      dataToCommit_.putSBH(iface_);

      txn_.commit();
      txn_.begin();

      dataToCommit_.deleteEmptyKeys(iface_);

      txn_.commit();
      txn_.begin();

      if (mostRecentBlockApplied_ != 0 && updateSDBI_ == true)
         dataToCommit_.updateSDBI(iface_);

      //final commit
      clearTransactions();
      parent_->commitingObject_.reset();
   }

   BlockWriteBatcher* bwbParent = parent_;

   //signal the readonly transaction to reset
   bwbParent->resetTxn_ = deleteId_;

   //signal DB is ready for new commit
   lock.unlock();
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::resetTransactions(void)
{
   resetTxn_ = 0;
   
   txn_.commit();
   txn_.open(&iface_->dbEnv_, LMDB::ReadOnly);
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::clearTransactions(void)
{
   txn_.commit();
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::grabBlocksFromDB(shared_ptr<LoadedBlockData> blockData)
{
   /***
   Grab blocks from the DB, put each block in the current block's nextBlock_
   ***/

   //TIMER_START("grabBlocksFromDB");

   uint32_t hgt = blockData->topLoadedBlock_;

   //find last block
   shared_ptr<PulledBlock> *lastBlock = &blockData->block_;
   while (*lastBlock != nullptr)
      lastBlock = &(*lastBlock)->nextBlock_;

   unique_lock<mutex> lock(blockData->mu_);

   while (1)
   {
      //create read only db txn within main loop, so that it is rewed
      //after each sleep period
      LMDBEnv::Transaction tx(&iface_->dbEnv_, LMDB::ReadOnly);
      LDBIter ldbIter = iface_->getIterator(BLKDATA);

      uint8_t dupID = iface_->getValidDupIDForHeight(hgt);
      if (!ldbIter.seekToExact(DBUtils::getBlkDataKey(hgt, dupID)))
      {
         *lastBlock = blockData->interruptBlock_;
         LOGERR << "Header heigh&dup is not in BLKDATA DB";
         LOGERR << "(" << hgt << ", " << dupID << ")";
         return;
      }

      while (blockData->bufferLoad_.load(memory_order_acquire)
         < UPDATE_BYTES_THRESH * 5)
      {
         if (hgt > blockData->endBlock_)
            return;

         uint8_t dupID = iface_->getValidDupIDForHeight(hgt);
         if (dupID == UINT8_MAX)
         {
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
            if (!ldbIter.seekToExact(DBUtils::getBlkDataKey(hgt, dupID)))
            {
               *lastBlock = blockData->interruptBlock_;
               LOGERR << "Header heigh&dup is not in BLKDATA DB";
               LOGERR << "(" << hgt << ", " << dupID << ")";
               return;
            }
         }

         shared_ptr<PulledBlock> pb(new PulledBlock());
         if (!pullBlockAtIter(*pb, ldbIter))
         {
            *lastBlock = blockData->interruptBlock_;
            LOGERR << "No block in DB at height " << hgt;
            return;
         }

         //increment bufferLoad
         blockData->bufferLoad_.fetch_add(
            pb->numBytes_, memory_order_release);

         //assign newly grabbed block to shared_ptr
         *lastBlock = pb;

         //set shared_ptr to next empty block
         lastBlock = &(*lastBlock)->nextBlock_;

         blockData->topLoadedBlock_ = hgt;
         ++hgt;
      }

      if (hgt > blockData->endBlock_)
         return;

      //sleep 10sec or until process thread signals block buffer is low
      blockData->cv_.wait_for(lock, chrono::seconds(10));
   }

   //TIMER_STOP("grabBlocksFromDB");
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

   try
   {
      shared_ptr<PulledBlock> block;
      auto grabLambda = [&, this](void)->void
      { this->grabBlocksFromDB(blockData); };
      thread grabThread = thread(grabLambda);
      grabThread.detach();

      uint64_t totalBlockDataProcessed=0;

      for (uint32_t i = blockData->startBlock_;
         i <= blockData->endBlock_;
         i++)
      {
         if (resetTxn_ != 0)
         {
            uint32_t id = resetTxn_;
            resetTransactions();
            clearSubSshMap(id);
         }

         if (i > blockData->endBlock_)
            break;
         
         //wait until the shared_ptr has been assigned some data
         while (!(block = blockData->block_));

         //grab it and check if its valid
         if (blockData->block_ == blockData->interruptBlock_)
            throw;

         uint32_t blockSize = blockData->block_->numBytes_;

         //decrement bufferload
         blockData->bufferLoad_.fetch_sub(
            blockSize, memory_order_release);

         //scan block
         lastScannedBlockHash = 
            applyBlockToDB(*blockData->block_, blockData->scrAddrFilter_);

         if (i == blockData->endBlock_)
            break;

         if (blockData->bufferLoad_.load(memory_order_consume)
            < UPDATE_BYTES_THRESH * 2)
         {
            /***
            Buffer is running low. Try to take ownership of the blockData
            mutex. If that succeeds, then the grab thread is sleeping, so 
            signal it to wake. Otherwise the grab thread is already running 
            and is lagging behind the processing thread (very unlikely)
            ***/
            unique_lock<mutex> lock(blockData->mu_, defer_lock);
            if(lock.try_lock())
               blockData->cv_.notify_all();
         }

         //wait until next block is available
         while (!(block = blockData->block_->nextBlock_));

         //check if next block is valid
         if (blockData->block_->nextBlock_ == blockData->interruptBlock_)
            throw;

         //assign next block to current
         blockData->block_ = blockData->block_->nextBlock_;
 
         if (i % 2500 == 2499)
            LOGWARN << "Finished applying blocks up to " << (i + 1);

         totalBlockDataProcessed += blockSize;
         progress.advance(totalBlockDataProcessed);
      }
      
      clearTransactions();
   }
   catch (...)
   {
      clearTransactions();
      throw;
   }
   
   return lastScannedBlockHash;
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::clearSubSshMap(uint32_t id)
{
   if (id == deleteId_)
      subSshMapToWrite_.clear();
}


////////////////////////////////////////////////////////////////////////////////
BinaryData BlockWriteBatcher::scanBlocks(
   ProgressFilter &prog,
   uint32_t startBlock, uint32_t endBlock, 
   ScrAddrFilter& scf
)
{
   //TIMER_START("applyBlockRangeToDBIter");
   
   prepareSshToModify(scf);

   shared_ptr<LoadedBlockData> tempBlockData = 
      make_shared<LoadedBlockData>(startBlock, endBlock, scf);

   return applyBlocksToDB(prog, tempBlockData);
}

////////////////////////////////////////////////////////////////////////////////
bool BlockWriteBatcher::pullBlockAtIter(PulledBlock& pb, LDBIter& iter)
{

   // Now we read the whole block, not just the header
   if (iface_->readStoredBlockAtIter(iter, pb))
   {
      pb.preprocessStxo(config_.armoryDbType);
      return true;
   }

   return false;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockWriteBatcher::pullBlockFromDB(
   PulledBlock& pb, uint32_t height, uint8_t dup)
{
   LDBIter ldbIter = iface_->getIterator(BLKDATA);

   if (!ldbIter.seekToExact(DBUtils::getBlkDataKey(height, dup)))
   {
      LOGERR << "Header heigh&dup is not in BLKDATA DB";
      LOGERR << "(" << height << ", " << dup << ")";
      return false;
   }

   return pullBlockAtIter(pb, ldbIter);
}

////////////////////////////////////////////////////////////////////////////////
map<BinaryData, StoredScriptHistory>& BlockWriteBatcher::getSSHMap(
   const map<BinaryData, map<BinaryData, StoredSubHistory> >& subsshMap)
{
   {
      shared_ptr<BlockWriteBatcher> commitingObj = parent_->commitingObject_;
      if (commitingObj)
      {
         if (&commitingObj->dataToCommit_ != &dataToCommit_)
         {
            sshToModify_ = commitingObj->sshToModify_;
            
            if(!commitingObj->dataToCommit_.sshReady_)
               unique_lock<mutex> lock(commitingObj->dataToCommit_.lock_);
         }
      }
      else parent_->resetTransactions();
   }

   if (parent_->sshToModify_ && parent_->sshToModify_->size() != 0)
      return *parent_->sshToModify_;

   if (!sshToModify_)
      sshToModify_ = shared_ptr<map<BinaryData, StoredScriptHistory>>(
      new map<BinaryData, StoredScriptHistory>);

   for (auto& scrAddr : subsshMap)
   {
      auto& ssh = (*sshToModify_)[scrAddr.first];
      if (ssh.alreadyScannedUpToBlk_ == 0)
         getSshHeader(ssh, scrAddr.first);
   }

   return *sshToModify_;
}


////////////////////////////////////////////////////////////////////////////////
/// DataToCommit
////////////////////////////////////////////////////////////////////////////////
set<BinaryData> DataToCommit::serializeSSH(BlockWriteBatcher& bwb,
   const map<BinaryData, map<BinaryData, StoredSubHistory> >& subsshMap)
{
   set<BinaryData> keysToDelete;

   auto dbType = bwb.config_.armoryDbType;
   auto pruneType = bwb.config_.pruneType;

   auto& sshMap = bwb.getSSHMap(subsshMap);
   
   for (auto& sshPair : sshMap)
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
            uint32_t subsshHeight = DBUtils::hgtxToHeight(subsshPair.first);
            if (subsshHeight > ssh.alreadyScannedUpToBlk_ ||
               !ssh.alreadyScannedUpToBlk_ ||
               subsshHeight > forceUpdateSshAtHeight_)
            {
               for (const auto& txioPair : subssh.txioMap_)
               {
                  auto& txio = txioPair.second;
                  if (!txio.isMultisig())
                  {
                     if (!txio.hasTxIn())
                        ssh.totalUnspent_ += txio.getValue();
                     else if (!txio.flagged)
                        ssh.totalUnspent_ -= txio.getValue();
                  }
               }

               ssh.totalTxioCount_ += subssh.txioMap_.size();
            }
         }

         if (bwb.config_.armoryDbType == ARMORY_DB_SUPER)
         {
            if (ssh.totalTxioCount_ > 0)
            {
               ssh.alreadyScannedUpToBlk_ = bwb.mostRecentBlockApplied_;
               BinaryWriter& bw = serializedSshToModify_[sshKey];
               ssh.serializeDBValue(bw, dbType, pruneType);
            }
            else
               keysToDelete.insert(sshKey);
         }
      }

      if (bwb.config_.armoryDbType != ARMORY_DB_SUPER)
      {
         ssh.alreadyScannedUpToBlk_ = bwb.mostRecentBlockApplied_;
         BinaryWriter& bw = serializedSshToModify_[sshKey];
         ssh.serializeDBValue(bw, dbType, pruneType);
      }
   }

   sshReady_ = true;
   //condVar_.notify_all();

   return keysToDelete;
}
////////////////////////////////////////////////////////////////////////////////
void DataToCommit::serializeDataToCommit(BlockWriteBatcher& bwb,
   const map<BinaryData, map<BinaryData, StoredSubHistory> >& subsshMap)
{
   auto dbType = bwb.config_.armoryDbType;
   auto pruneType = bwb.config_.pruneType;

   //subssh
   {
      for (auto& sshPair : subsshMap)
      {
         BinaryData sshKey;
         sshKey.append(WRITE_UINT8_LE(DB_PREFIX_SCRIPT));
         sshKey.append(sshPair.first);

         for (const auto& subsshPair : sshPair.second)
         {
            auto& subssh = subsshPair.second;

            BinaryData subsshKey = sshKey + subssh.hgtX_;
            if (subssh.txioMap_.size() != 0)
            {
               BinaryWriter& bw = serializedSubSshToApply_[subsshKey];
               subssh.serializeDBValue(bw, bwb.iface_, dbType, pruneType);
            }
            else
               keysToDelete_.insert(subsshKey);
         }
      }
   }
   
   //stxout
   for (auto& spentStxo : bwb.stxoToUpdate_)
   {
      BinaryWriter& bw = serializedStxOutToModify_[spentStxo->getDBKey()];
      spentStxo->serializeDBValue(bw, dbType, pruneType);
   }

   //sbh
   for (auto& sbh : bwb.sbhToUpdate_)
   {
      BinaryWriter& bw = serializedSbhToUpdate_[sbh.getDBKey()];
      if (bw.getSize() == 0)
         sbh.serializeDBValue(bw, BLKDATA, dbType, pruneType);
   }

   if (bwb.sbhToUpdate_.size())
   {
      auto iterLast = bwb.sbhToUpdate_.rbegin();
      topBlockHash_ = iterLast->thisHash_;
   }
   else topBlockHash_ = BtcUtils::EmptyHash_;

   mostRecentBlockApplied_ = bwb.mostRecentBlockApplied_ +1;
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::serializeData(BlockWriteBatcher& bwb,
   const map<BinaryData, map<BinaryData, StoredSubHistory> >& subsshMap)
{
   if (isSerialized_)
      return;

   unique_lock<mutex> lock(lock_);

   auto serialize = [&](void)
   { serializeDataToCommit(bwb, subsshMap); };

   thread serThread = thread(serialize);

   const auto& keysToDelete = serializeSSH(bwb, subsshMap);
   lock.unlock();

   if (serThread.joinable())
      serThread.join();
   
   keysToDelete_.insert(keysToDelete.begin(), keysToDelete.end());

   isSerialized_ = true;
}
////////////////////////////////////////////////////////////////////////////////
void DataToCommit::putSSH(LMDBBlockDatabase* db)
{
   for (auto& sshPair : serializedSshToModify_)
      db->putValue(BLKDATA, sshPair.first, sshPair.second.getData());

   for (auto subSshPair : serializedSubSshToApply_)
      db->putValue(BLKDATA, subSshPair.first, subSshPair.second.getData());
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::putSTX(LMDBBlockDatabase* db)
{
   for (auto& stxoPair : serializedStxOutToModify_)
      db->putValue(BLKDATA, stxoPair.first, stxoPair.second.getData());
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::putSBH(LMDBBlockDatabase* db)
{
   for (auto sbh : serializedSbhToUpdate_)
      db->putValue(BLKDATA, sbh.first, sbh.second.getData());
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::deleteEmptyKeys(LMDBBlockDatabase* db)
{
   for (auto& toDel : keysToDelete_)
      db->deleteValue(BLKDATA, toDel);
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::updateSDBI(LMDBBlockDatabase* db)
{
   StoredDBInfo sdbi;
   db->getStoredDBInfo(BLKDATA, sdbi);
   if (!sdbi.isInitialized())
      LOGERR << "How do we have invalid SDBI in applyMods?";
   else
   {
      //save top block height
      sdbi.appliedToHgt_ = mostRecentBlockApplied_;

      //save top block hash
      if (topBlockHash_ != BtcUtils::EmptyHash_)
         sdbi.topScannedBlkHash_ = topBlockHash_;

      db->putStoredDBInfo(BLKDATA, sdbi);
   }
}
