#include "BlockWriteBatcher.h"

#include "StoredBlockObj.h"
#include "leveldb_wrapper.h"


static const uint64_t UPDATE_BYTES_SSH = 25;
static const uint64_t UPDATE_BYTES_SUBSSH = 75;

static void updateBlkDataHeader(InterfaceToLDB* iface, StoredHeader const & sbh)
{
   iface->putValue(BLKDATA, sbh.getDBKey(), sbh.serializeDBValue(BLKDATA));
}

////////////////////////////////////////////////////////////////////////////////
static StoredTx* makeSureSTXInMap(
            InterfaceToLDB* iface,
            BinaryDataRef txHash,
            map<BinaryData, StoredTx> & stxMap,
            uint64_t* additionalSize)
{
   // TODO:  If we are pruning, we may have completely removed this tx from
   //        the DB, which means that it won't be in the map or the DB.
   //        But this method was written before pruning was ever implemented...
   StoredTx * stxptr;

   // Get the existing STX or make a new one
   map<BinaryData, StoredTx>::iterator txIter = stxMap.find(txHash);
   if(ITER_IN_MAP(txIter, stxMap))
      stxptr = &(txIter->second);
   else
   {
      StoredTx stxTemp;
      iface->getStoredTx(stxTemp, txHash);
      stxMap[txHash] = stxTemp;
      stxptr = &stxMap[txHash];
      if (additionalSize)
         *additionalSize += stxptr->numBytes_;
   }
   
   return stxptr;
}

////////////////////////////////////////////////////////////////////////////////
// This avoids having to do the double-lookup when fetching by hash.
// We still pass in the hash anyway, because the map is indexed by the hash,
// and we'd like to not have to do a lookup for the hash if only provided
// {hgt, dup, idx}
static StoredTx* makeSureSTXInMap(
            InterfaceToLDB* iface,
            uint32_t hgt,
            uint8_t  dup,
            uint16_t txIdx,
            BinaryDataRef txHash,
            map<BinaryData, StoredTx> & stxMap,
            uint64_t* additionalSize)
{
   StoredTx * stxptr;

   // Get the existing STX or make a new one
   map<BinaryData, StoredTx>::iterator txIter = stxMap.find(txHash);
   if(ITER_IN_MAP(txIter, stxMap))
      stxptr = &(txIter->second);
   else
   {
      StoredTx &stxTemp = stxMap[txHash];
      iface->getStoredTx(stxTemp, hgt, dup, txIdx);
      stxptr = &stxMap[txHash];
      if (additionalSize)
         *additionalSize += stxptr->numBytes_;
   }
   
   return stxptr;
}




static StoredScriptHistory* makeSureSSHInMap(
            InterfaceToLDB* iface,
            BinaryDataRef uniqKey,
            BinaryDataRef hgtX,
            map<BinaryData, StoredScriptHistory> & sshMap,
            uint64_t* additionalSize,
            bool createIfDNE=true)
{
   SCOPED_TIMER("makeSureSSHInMap");
   StoredScriptHistory * sshptr;

   // If already in Map
   map<BinaryData, StoredScriptHistory>::iterator iter = sshMap.find(uniqKey);
   if(ITER_IN_MAP(iter, sshMap))
   {
      SCOPED_TIMER("___SSH_AlreadyInMap");
      sshptr = &(iter->second);
   }
   else
   {
      StoredScriptHistory sshTemp;
      
      iface->getStoredScriptHistorySummary(sshTemp, uniqKey);
      // sshTemp.alreadyScannedUpToBlk_ = getAppliedToHeightInDB(); TODO
      if (additionalSize)
         *additionalSize += UPDATE_BYTES_SSH;
      if(sshTemp.isInitialized())
      {
         SCOPED_TIMER("___SSH_AlreadyInDB");
         // We already have an SSH in DB -- pull it into the map
         sshMap[uniqKey] = sshTemp; 
         sshptr = &sshMap[uniqKey];
      }
      else
      {
         SCOPED_TIMER("___SSH_NeedCreate");
         if(!createIfDNE)
            return NULL;

         sshMap[uniqKey] = StoredScriptHistory(); 
         sshptr = &sshMap[uniqKey];
         sshptr->uniqueKey_ = uniqKey;
      }
   }


   // If sub-history for this block doesn't exist, add an empty one before
   // returning the pointer to the SSH.  Since we haven't actually inserted
   // anything into the SubSSH, we don't need to adjust the totalTxioCount_
   uint32_t prevSize = sshptr->subHistMap_.size();
   iface->fetchStoredSubHistory(*sshptr, hgtX, true, false);
   uint32_t newSize = sshptr->subHistMap_.size();

   if (additionalSize)
      *additionalSize += (newSize - prevSize) * UPDATE_BYTES_SUBSSH;
   return sshptr;
}


////////////////////////////////////////////////////////////////////////////////
// AddRawBlockTODB
//
// Assumptions:
//  -- We have already determined the correct height and dup for the header 
//     and we assume it's part of the sbh object
//  -- It has definitely been added to the headers DB (bail if not)
//  -- We don't know if it's been added to the blkdata DB yet
//
// Things to do when adding a block:
//
//  -- PREPARATION:
//    -- Create list of all OutPoints affected, and scripts touched
//    -- If not supernode, then check above data against registeredSSHs_
//    -- Fetch all StoredTxOuts from DB about to be removed
//    -- Get/create TXHINT entries for all tx in block
//    -- Compute all script keys and get/create all StoredScriptHistory objs
//    -- Check if any multisig scripts are affected, if so get those objs
//    -- If pruning, create StoredUndoData from TxOuts about to be removed
//    -- Modify any Tx/TxOuts in the SBH tree to accommodate any tx in this 
//       block that affect any other tx in this block
//
//
//  -- Check if the block {hgt,dup} has already been written to BLKDATA DB
//  -- Check if the header has already been added to HEADERS DB
//  
//  -- BATCH (HEADERS)
//    -- Add header to HEADHASH list
//    -- Add header to HEADHGT list
//    -- Update validDupByHeight_
//    -- Update DBINFO top block data
//
//  -- BATCH (BLKDATA)
//    -- Modify StoredTxOut with spentness info (or prep a delete operation
//       if pruning).
//    -- Modify StoredScriptHistory objs same as above.  
//    -- Modify StoredScriptHistory multisig objects as well.
//    -- Update SSH objects alreadyScannedUpToBlk_, if necessary
//    -- Write all new TXDATA entries for {hgt,dup}
//    -- If pruning, write StoredUndoData objs to DB
//    -- Update DBINFO top block data
//
// IMPORTANT: we also need to make sure this method does nothing if the
//            block has already been added properly (though, it okay for 
//            it to take time to verify nothing needs to be done).  We may
//            end up replaying some blocks to force consistency of the DB, 
//            and this method needs to be robust to replaying already-added
//            blocks, as well as fixing data if the replayed block appears
//            to have been added already but is different.
//
////////////////////////////////////////////////////////////////////////////////
BlockWriteBatcher::BlockWriteBatcher(InterfaceToLDB* iface)
   : iface_(iface), dbUpdateSize_(0)
{

}

BlockWriteBatcher::~BlockWriteBatcher()
{
   commit();
}

void BlockWriteBatcher::applyBlockToDB(StoredHeader &sbh)
{
   if(iface_->getValidDupIDForHeight(sbh.blockHeight_) != sbh.duplicateID_)
   {
      LOGERR << "Dup requested is not the main branch for the given height!";
      return;
   }
   else
      sbh.isMainBranch_ = true;
   
   mostRecentBlockApplied_= sbh.blockHeight_;

   // We will accumulate undoData as we apply the tx
   StoredUndoData sud;
   sud.blockHash_   = sbh.thisHash_; 
   sud.blockHeight_ = sbh.blockHeight_;
   sud.duplicateID_ = sbh.duplicateID_;
   
   // Apply all the tx to the update data
   for(map<uint16_t, StoredTx>::iterator iter = sbh.stxMap_.begin();
      iter != sbh.stxMap_.end(); iter++)
   {
      // This will fetch all the affected [Stored]Tx and modify the maps in 
      // RAM.  It will check the maps first to see if it's already been pulled,
      // and then it will modify either the pulled StoredTx or pre-existing
      // one.  This means that if a single Tx is affected by multiple TxIns
      // or TxOuts, earlier changes will not be overwritten by newer changes.
      applyTxToBatchWriteData(iter->second, &sud);
   }

   // At this point we should have a list of STX and SSH with all the correct
   // modifications (or creations) to represent this block.  Let's apply it.
   sbh.blockAppliedToDB_ = true;
   updateBlkDataHeader(iface_, sbh);
   //iface_->putStoredHeader(sbh, false);

   { // we want to commit the undo data at the same time as actual changes
      InterfaceToLDB::Batch batch(iface_, BLKDATA);
   
      // Now actually write all the changes to the DB all at once
      // if we've gotten to that threshold
      if (dbUpdateSize_ > UPDATE_BYTES_THRESH)
         commit();

      // Only if pruning, we need to store 
      // TODO: this is going to get run every block, probably should batch it 
      //       like we do with the other data...when we actually implement pruning
      if(DBUtils.getDbPruneType() == DB_PRUNE_ALL)
         iface_->putStoredUndoData(sud);
   }
}

void BlockWriteBatcher::applyBlockToDB(uint32_t hgt, uint8_t dup)
{
   StoredHeader sbh;
   iface_->getStoredHeader(sbh, hgt, dup);
   applyBlockToDB(sbh);
}


////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::undoBlockFromDB(StoredUndoData & sud)
{
   SCOPED_TIMER("undoBlockFromDB");

   StoredHeader sbh;
   iface_->getStoredHeader(sbh, sud.blockHeight_, sud.duplicateID_);
   if(!sbh.blockAppliedToDB_)
   {
      LOGERR << "This block was never applied to the DB...can't undo!";
      return /*false*/;
   }
   
   mostRecentBlockApplied_ = sud.blockHeight_;

   // In the future we will accommodate more user modes
   if(DBUtils.getArmoryDbType() != ARMORY_DB_SUPER)
   {
      LOGERR << "Don't know what to do this in non-supernode mode!";
   }
   
   ///// Put the STXOs back into the DB which were removed by this block
   // Process the stxOutsRemovedByBlock_ in reverse order
   // Use int32_t index so that -1 != UINT32_MAX and we go into inf loop
   for(int32_t i=sud.stxOutsRemovedByBlock_.size()-1; i>=0; i--)
   {
      StoredTxOut & sudStxo = sud.stxOutsRemovedByBlock_[i];
      StoredTx * stxptr = makeSureSTXInMap( 
               iface_,
               sudStxo.blockHeight_,
               sudStxo.duplicateID_,
               sudStxo.txIndex_,
               sudStxo.parentHash_,
               stxToModify_,
               &dbUpdateSize_);

      
      const uint16_t stxoIdx = sudStxo.txOutIndex_;

      if(DBUtils.getDbPruneType() == DB_PRUNE_NONE)
      {
         // If full/super, we have the TxOut in DB, just need mark it unspent
         map<uint16_t,StoredTxOut>::iterator iter = stxptr->stxoMap_.find(stxoIdx);
         //if(iter == stxptr->stxoMap_.end())
         if(ITER_NOT_IN_MAP(iter, stxptr->stxoMap_))
         {
            LOGERR << "Expecting to find existing STXO, but DNE";
            continue;
         }

         StoredTxOut & stxoReAdd = iter->second;
         if(stxoReAdd.spentness_ == TXOUT_UNSPENT || 
            stxoReAdd.spentByTxInKey_.getSize() == 0 )
         {
            LOGERR << "STXO needs to be re-added/marked-unspent but it";
            LOGERR << "was already declared unspent in the DB";
         }
         
         stxoReAdd.spentness_ = TXOUT_UNSPENT;
         stxoReAdd.spentByTxInKey_ = BinaryData(0);
      }
      else
      {
         // If we're pruning, we should have the Tx in the DB, but without the
         // TxOut because it had been pruned by this block on the forward op
         map<uint16_t,StoredTxOut>::iterator iter = stxptr->stxoMap_.find(stxoIdx);
         //if(iter != stxptr->stxoMap_.end())
         if(ITER_IN_MAP(iter, stxptr->stxoMap_))
            LOGERR << "Somehow this TxOut had not been pruned!";
         else
            iter->second = sudStxo;

         iter->second.spentness_      = TXOUT_UNSPENT;
         iter->second.spentByTxInKey_ = BinaryData(0);
      }


      {
         ////// Finished updating STX, now update the SSH in the DB
         // Updating the SSH objects works the same regardless of pruning
         map<uint16_t,StoredTxOut>::iterator iter = stxptr->stxoMap_.find(stxoIdx);
         //if(iter == stxptr->stxoMap_.end())
         if(ITER_NOT_IN_MAP(iter, stxptr->stxoMap_))
         {
            LOGERR << "Somehow STXO DNE even though we should've just added it!";
            continue;
         }

         StoredTxOut & stxoReAdd = iter->second;
         BinaryData uniqKey = stxoReAdd.getScrAddress();
         BinaryData hgtX    = stxoReAdd.getHgtX();
         StoredScriptHistory* sshptr = makeSureSSHInMap(
               iface_, uniqKey, hgtX, sshToModify_, &dbUpdateSize_
            );
         if(sshptr==NULL)
         {
            LOGERR << "No SSH found for marking TxOut unspent on undo";
            continue;
         }

         // Now get the TxIOPair in the StoredScriptHistory and mark unspent
         sshptr->markTxOutUnspent(stxoReAdd.getDBKey(false),
                                 stxoReAdd.getValue(),
                                 stxoReAdd.isCoinbase_,
                                 false);

         
         // If multisig, we need to update the SSHs for individual addresses
         if(uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
         {
            vector<BinaryData> addr160List;
            BtcUtils::getMultisigAddrList(stxoReAdd.getScriptRef(), addr160List);
            for(uint32_t a=0; a<addr160List.size(); i++)
            {
               // Get the existing SSH or make a new one
               BinaryData uniqKey = HASH160PREFIX + addr160List[a];
               StoredScriptHistory* sshms = makeSureSSHInMap(iface_, uniqKey, 
                                                            stxoReAdd.getHgtX(),
                                                            sshToModify_, &dbUpdateSize_);
               sshms->markTxOutUnspent(stxoReAdd.getDBKey(false),
                                       stxoReAdd.getValue(),
                                       stxoReAdd.isCoinbase_,
                                       true);
            }
         }
      }
   }


   // The OutPoint list is every new, unspent TxOut created by this block.
   // When they were added, we updated all the StoredScriptHistory objects
   // to include references to them.  We need to remove them now.
   // Use int32_t index so that -1 != UINT32_MAX and we go into inf loop
   for(int16_t itx=sbh.numTx_-1; itx>=0; itx--)
   {
      // Ironically, even though I'm using hgt & dup, I still need the hash
      // in order to key the stxToModify map
      BinaryData txHash = iface_->getHashForDBKey(sbh.blockHeight_,
                                                  sbh.duplicateID_,
                                                  itx);

      StoredTx * stxptr  = makeSureSTXInMap(
            iface_,
            sbh.blockHeight_,
            sbh.duplicateID_,
            itx, 
            txHash,
            stxToModify_,
            &dbUpdateSize_);

      for(int16_t txoIdx = stxptr->stxoMap_.size()-1; txoIdx >= 0; txoIdx--)
      {

         StoredTxOut & stxo    = stxptr->stxoMap_[txoIdx];
         BinaryData    stxoKey = stxo.getDBKey(false);

   
         // Then fetch the StoredScriptHistory of the StoredTxOut scraddress
         BinaryData uniqKey = stxo.getScrAddress();
         BinaryData hgtX    = stxo.getHgtX();
         StoredScriptHistory * sshptr = makeSureSSHInMap(
               iface_, uniqKey, 
               hgtX,
               sshToModify_, 
               &dbUpdateSize_,
               false);
   
   
         // If we are tracking that SSH, remove the reference to this OutPoint
         if(sshptr != NULL)
            sshptr->eraseTxio(stxoKey);
   
         // Now remove any multisig entries that were added due to this TxOut
         if(uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
         {
            vector<BinaryData> addr160List;
            BtcUtils::getMultisigAddrList(stxo.getScriptRef(), addr160List);
            for(uint32_t a=0; a<addr160List.size(); a++)
            {
               // Get the individual address obj for this multisig piece
               BinaryData uniqKey = HASH160PREFIX + addr160List[a];
               StoredScriptHistory* sshms = makeSureSSHInMap(
                     iface_,
                     uniqKey,
                     hgtX,
                     sshToModify_, 
                     &dbUpdateSize_,
                     false
                  );
               sshms->eraseTxio(stxoKey);
            }
         }
      }
   }

   // Finally, mark this block as UNapplied.
   sbh.blockAppliedToDB_ = false;
   updateBlkDataHeader(iface_, sbh);
   
   if (dbUpdateSize_ > UPDATE_BYTES_THRESH)
      commit();
}


////////////////////////////////////////////////////////////////////////////////
// Assume that stx.blockHeight_ and .duplicateID_ are set correctly.
// We created the maps and sets outside this function, because we need to keep
// a master list of updates induced by all tx in this block.  
// TODO:  Make sure that if Tx5 spends an input from Tx2 in the same 
//        block that it is handled correctly, etc.
bool BlockWriteBatcher::applyTxToBatchWriteData(
                        StoredTx &       thisSTX,
                        StoredUndoData * sud)
{
   SCOPED_TIMER("applyTxToBatchWriteData");

   Tx tx = thisSTX.getTxCopy();

   // We never expect thisSTX to already be in the map (other tx in the map
   // may be affected/retrieved multiple times).  
   if(KEY_IN_MAP(tx.getThisHash(), stxToModify_))
      LOGERR << "How did we already add this tx?";

   // I just noticed we never set TxOuts to TXOUT_UNSPENT.  Might as well do 
   // it here -- by definition if we just added this Tx to the DB, it couldn't
   // have been spent yet.
   
   for(map<uint16_t, StoredTxOut>::iterator iter = thisSTX.stxoMap_.begin(); 
       iter != thisSTX.stxoMap_.end();
       iter++)
      iter->second.spentness_ = TXOUT_UNSPENT;

   // This tx itself needs to be added to the map, which makes it accessible 
   // to future tx in the same block which spend outputs from this tx, without
   // doing anything crazy in the code here
   stxToModify_[tx.getThisHash()] = thisSTX;

   dbUpdateSize_ += thisSTX.numBytes_;
   
   // Go through and find all the previous TxOuts that are affected by this tx
   for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
   {
      TxIn txin = tx.getTxInCopy(iin);
      if(txin.isCoinbase())
         continue;

      // Get the OutPoint data of TxOut being spent
      const OutPoint      op       = txin.getOutPoint();
      const BinaryDataRef opTxHash = op.getTxHashRef();
      const uint32_t      opTxoIdx = op.getTxOutIndex();

      // This will fetch the STX from DB and put it in the stxToModify
      // map if it's not already there.  Or it will do nothing if it's
      // already part of the map.  In both cases, it returns a pointer
      // to the STX that will be written to DB that we can modify.
      StoredTx    * stxptr = makeSureSTXInMap(iface_, opTxHash, stxToModify_, &dbUpdateSize_);
      StoredTxOut & stxo   = stxptr->stxoMap_[opTxoIdx];
      BinaryData    uniqKey   = stxo.getScrAddress();

      // Update the stxo by marking it spent by this Block:TxIndex:TxInIndex
      map<uint16_t,StoredTxOut>::iterator iter = stxptr->stxoMap_.find(opTxoIdx);
      
      // Some sanity checks
      //if(iter == stxptr->stxoMap_.end())
      if(ITER_NOT_IN_MAP(iter, stxptr->stxoMap_))
      {
         LOGERR << "Needed to get OutPoint for a TxIn, but DNE";
         continue;
      }

      // We're aliasing this because "iter->second" is not clear at all
      StoredTxOut & stxoSpend = iter->second;
   
      if(stxoSpend.spentness_ == TXOUT_SPENT)
      {
         LOGERR << "Trying to mark TxOut spent, but it's already marked";
         continue;
      }

      // Just about to {remove-if-pruning, mark-spent-if-not} STXO
      // Record it in the StoredUndoData object
      if(sud != NULL)
         sud->stxOutsRemovedByBlock_.push_back(stxoSpend);

      // Need to modify existing UTXOs, so that we can delete or mark as spent
      stxoSpend.spentness_      = TXOUT_SPENT;
      stxoSpend.spentByTxInKey_ = thisSTX.getDBKeyOfChild(iin, false);

      if(DBUtils.getArmoryDbType() != ARMORY_DB_SUPER)
      {
         LOGERR << "Don't know what to do this in non-supernode mode!";
      }

      ////// Now update the SSH to show this TxIOPair was spent
      // Same story as stxToModify above, except this will actually create a new
      // SSH if it doesn't exist in the map or the DB
      BinaryData hgtX = stxo.getHgtX();
      StoredScriptHistory* sshptr = makeSureSSHInMap(
            iface_,
            uniqKey,
            hgtX,
            sshToModify_,
            &dbUpdateSize_
         );

      // Assuming supernode, we don't need to worry about removing references
      // to multisig scripts that reference this script.  Simply find and 
      // update the correct SSH TXIO directly
      sshptr->markTxOutSpent(stxoSpend.getDBKey(false),
                             thisSTX.getDBKeyOfChild(iin, false));
   }



   // We don't need to update any TXDATA, since it is part of writing thisSTX
   // to the DB ... but we do need to update the StoredScriptHistory objects
   // with references to the new [unspent] TxOuts
   for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
   {
      StoredTxOut & stxoToAdd = thisSTX.stxoMap_[iout];
      BinaryData uniqKey = stxoToAdd.getScrAddress();
      BinaryData hgtX    = stxoToAdd.getHgtX();
      StoredScriptHistory* sshptr = makeSureSSHInMap(
            iface_,
            uniqKey,
            hgtX,
            sshToModify_,
            &dbUpdateSize_
         );

      // Add reference to the next STXO to the respective SSH object
      sshptr->markTxOutUnspent(stxoToAdd.getDBKey(false),
                               stxoToAdd.getValue(),
                               stxoToAdd.isCoinbase_,
                               false);
                             
      // If this was a multisig address, add a ref to each individual scraddr
      if(uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
      {
         vector<BinaryData> addr160List;
         BtcUtils::getMultisigAddrList(stxoToAdd.getScriptRef(), addr160List);
         for(uint32_t a=0; a<addr160List.size(); a++)
         {
            // Get the existing SSH or make a new one
            BinaryData uniqKey = HASH160PREFIX + addr160List[a];
            StoredScriptHistory* sshms = makeSureSSHInMap(
                  iface_,
                  uniqKey,
                  hgtX,
                  sshToModify_,
                  &dbUpdateSize_
               );
            sshms->markTxOutUnspent(stxoToAdd.getDBKey(false),
                                    stxoToAdd.getValue(),
                                    stxoToAdd.isCoinbase_,
                                    true);
         }
      }
   }

   return true;
}



void BlockWriteBatcher::commit()
{
   // Check for any SSH objects that are now completely empty.  If they exist,
   // they should be removed from the DB, instead of simply written as empty
   // objects
   const set<BinaryData> keysToDelete = searchForSSHKeysToDelete();
   
   {
      InterfaceToLDB::Batch batch(iface_, BLKDATA);

      for(map<BinaryData, StoredTx>::iterator iter_stx = stxToModify_.begin();
         iter_stx != stxToModify_.end();
         iter_stx++)
      {
         iface_->putStoredTx(iter_stx->second, true);
      }
         
      for(map<BinaryData, StoredScriptHistory>::iterator iter_ssh = sshToModify_.begin();
         iter_ssh != sshToModify_.end();
         iter_ssh++)
      {
         iface_->putStoredScriptHistory(iter_ssh->second);
      }

      for(set<BinaryData>::const_iterator iter_del  = keysToDelete.begin();
         iter_del != keysToDelete.end();
         iter_del++)
      {
         iface_->deleteValue(BLKDATA, *iter_del);
      }


      if(mostRecentBlockApplied_ != 0)
      {
         StoredDBInfo sdbi;
         iface_->getStoredDBInfo(BLKDATA, sdbi);
         if(!sdbi.isInitialized())
            LOGERR << "How do we have invalid SDBI in applyMods?";
         else
         {
            sdbi.appliedToHgt_  = mostRecentBlockApplied_;
            iface_->putStoredDBInfo(BLKDATA, sdbi);
         }
      }
   }
   
   stxToModify_.clear();
   sshToModify_.clear();
   dbUpdateSize_ = 0;
}

set<BinaryData> BlockWriteBatcher::searchForSSHKeysToDelete()
{
   set<BinaryData> keysToDelete;
   vector<BinaryData> fullSSHToDelete;
   
   for(map<BinaryData, StoredScriptHistory>::iterator iterSSH  = sshToModify_.begin();
       iterSSH != sshToModify_.end(); )
   {
      // get our next one in case we delete the current
      map<BinaryData, StoredScriptHistory>::iterator nextSSHi = iterSSH;
      ++nextSSHi;
      
      StoredScriptHistory & ssh = iterSSH->second;
      
      for(map<BinaryData, StoredSubHistory>::iterator iterSub = ssh.subHistMap_.begin(); 
          iterSub != ssh.subHistMap_.end(); 
          iterSub++)
      {
         StoredSubHistory & subssh = iterSub->second;
         if(subssh.txioSet_.size() == 0)
            keysToDelete.insert(subssh.getDBKey(true));
      }
   
      // If the full SSH is empty (not just sub history), mark it to be removed
      if(iterSSH->second.totalTxioCount_ == 0)
      {
         sshToModify_.erase(iterSSH);
      }
      
      iterSSH = nextSSHi;
   }

   return keysToDelete;
}

// kate: indent-width 3; replace-tabs on;
