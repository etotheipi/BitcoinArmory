////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2014, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include <algorithm>
#include <time.h>
#include <stdio.h>
#include "BlockUtils.h"
#include "Util.h"
#include "BtcWallet.h"


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




BlockDataManager_LevelDB* BlockDataManager_LevelDB::theOnlyBDM_ = NULL;
InterfaceToLDB* BlockDataManager_LevelDB::iface_=NULL;
bool BlockDataManager_LevelDB::bdmCreatedYet_=false;




/////////////////////////////////////////////////////////////////////////////
// This method is used in the registeredScrAddrScan to conditionally create and
// insert a transaction into the registered list 
void BlockDataManager_LevelDB::insertRegisteredTxIfNew(HashString txHash)
{
   // .insert() function returns pair<iter,bool> with bool true if inserted
   if(registeredTxSet_.insert(txHash).second == true)
   {
      TxRef txref = getTxRefByHash(txHash);
      RegisteredTx regTx(txref,
                         txref.getThisHash(),
                         txref.getBlockHeight(),
                         txref.getBlockTxIndex());
      registeredTxList_.push_back(regTx);
   }
}

/////////////////////////////////////////////////////////////////////////////
// TODO: I should investigate whether we should remove registered tx on
//       a reorg.  It doesn't look like we do, though it may also not 
//       matter as long as the scanRegisteredTxForWallet checks for main
//       branch before processing it.
void BlockDataManager_LevelDB::insertRegisteredTxIfNew(TxRef const & txref,
                                                       BinaryDataRef txHash,
                                                       uint32_t hgt,
                                                       uint16_t txIndex)
{
   if(registeredTxSet_.insert(txHash).second == true)
   {
      if(txref.isNull())
      {
         LOGERR << "Could not get the tx from the DB, either!";
         registeredTxSet_.erase(txHash);
         return;
      }
         
      RegisteredTx regTx(txref, txHash, hgt, txIndex);
      registeredTxList_.push_back(regTx);
   }
   
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::insertRegisteredTxIfNew(RegisteredTx & regTx)
{
   // .insert() function returns pair<iter,bool> with bool true if inserted
   if(registeredTxSet_.insert(regTx.getTxHash()).second == true)
      registeredTxList_.push_back(regTx);
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::removeRegisteredTx(BinaryData const & txHash)
{
   list<RegisteredTx>::iterator iter;
   for(iter  = registeredTxList_.begin();
       iter != registeredTxList_.end();
       iter++)
   {
      if(iter->txHash_ == txHash)
      {
         registeredTxList_.erase(iter);
         return true;
      }
   }

   return false;
}

/////////////////////////////////////////////////////////////////////////////
//  This basically does the same thing as the bulk filter, but it's for the
//  BDM to collect data on registered wallets/addresses during bulk
//  blockchain scaning.  It needs to track relevant OutPoints and produce 
//  a list of transactions that are relevant to the registered wallets.
//
//  Also, this takes a raw pointer to memory, because it is assumed that 
//  the data is being buffered and not converted/parsed for Tx objects, yet.
//
//  If the txSize and offsets have been pre-calculated, you can pass them 
//  in, or pass {0, NULL, NULL} to have it calculated for you.
//  
void BlockDataManager_LevelDB::registeredScrAddrScan( 
                                            uint8_t const * txptr,
                                            uint32_t txSize,
                                            vector<uint32_t> * txInOffsets,
                                            vector<uint32_t> * txOutOffsets)
{
   // Probably doesn't matter, but I'll keep these on the heap between calls
   static vector<uint32_t> localOffsIn;
   static vector<uint32_t> localOffsOut;

   if(txSize==0 || txInOffsets==NULL || txOutOffsets==NULL)
   {
      txInOffsets  = &localOffsIn;
      txOutOffsets = &localOffsOut;
      BtcUtils::TxCalcLength(txptr, txSize, txInOffsets, txOutOffsets);
   }
   
   uint32_t nTxIn  = txInOffsets->size()-1;
   uint32_t nTxOut = txOutOffsets->size()-1;
   

   if(registeredScrAddrMap_.size() == 0)
      return;

   uint8_t const * txStartPtr = txptr;
   for(uint32_t iin=0; iin<nTxIn; iin++)
   {
      // We have the txin, now check if it contains one of our TxOuts
      static OutPoint op;
      op.unserialize(txStartPtr + (*txInOffsets)[iin], txSize - (*txInOffsets)[iin]);
      if(registeredOutPoints_.count(op) > 0)
      {
         insertRegisteredTxIfNew(BtcUtils::getHash256(txptr, txSize));
         break; // we only care if ANY txIns are ours, not which ones
      }
   }

   // We have to scan all TxOuts regardless, to make sure our list of 
   // registeredOutPoints_ is up-to-date so that we can identify TxIns that are
   // ours on future to-be-scanned transactions
   for(uint32_t iout=0; iout<nTxOut; iout++)
   {
      static uint8_t scriptLenFirstByte;
      static HashString addr160(20);

      uint8_t const * ptr = (txStartPtr + (*txOutOffsets)[iout] + 8);
      scriptLenFirstByte = *(uint8_t*)ptr;
      if(scriptLenFirstByte == 25)
      {
         // Std TxOut with 25-byte script
         addr160.copyFrom(ptr+4, 20);
         if( scrAddrIsRegistered(HASH160PREFIX + addr160) )
         {
            HashString txHash = BtcUtils::getHash256(txptr, txSize);
            insertRegisteredTxIfNew(txHash);
            registeredOutPoints_.insert(OutPoint(txHash, iout));
         }
      }
      else if(scriptLenFirstByte==67)
      {
         // Std spend-coinbase TxOut script
         BtcUtils::getHash160_NoSafetyCheck(ptr+2, 65, addr160);
         if( scrAddrIsRegistered(HASH160PREFIX + addr160) )
         {
            HashString txHash = BtcUtils::getHash256(txptr, txSize);
            insertRegisteredTxIfNew(txHash);
            registeredOutPoints_.insert(OutPoint(txHash, iout));
         }
      }
      else
      {
         /* TODO:  Right now we will just ignoring non-std tx
                   I don't do anything with them right now, anyway
         TxOut txout = tx.getTxOutCopy(iout);
         for(uint32_t i=0; i<scrAddrPtrs_.size(); i++)
         {
            ScrAddrObj & thisAddr = *(scrAddrPtrs_[i]);
            HashString const & scraddr = thisAddr.getScrAddr();
            if(txout.getScriptRef().find(thisAddr.getScrAddr()) > -1)
               scanNonStdTx(0, 0, tx, iout, thisAddr);
            continue;
         }
         //break;
         */
      }
   }
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::registeredScrAddrScan( Tx & theTx )
{
   registeredScrAddrScan(theTx.getPtr(),
                         theTx.getSize(),
                         &theTx.offsetsTxIn_, 
                         &theTx.offsetsTxOut_);
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


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// Start Blockchain methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

Blockchain::Blockchain(BlockDataManager_LevelDB* bdm)
   : bdm_(bdm)
{
   clear();
}

void Blockchain::clear()
{
   headerMap_.clear();
   headersByHeight_.resize(0);
   topBlockPtr_ = genesisBlockBlockPtr_ = &headerMap_[
         bdm_->GenesisHash_
      ];
}

BlockHeader& Blockchain::addBlock(
      const HashString &blockhash,
      const BlockHeader &block
   )
{
   if (hasHeaderWithHash(blockhash))
   {
      LOGWARN << "Somehow tried to add header that's already in map";
      LOGWARN << "Header Hash: " << blockhash.toHexStr();
   }
   return headerMap_[blockhash] = block;
}

Blockchain::ReorganizationState Blockchain::organize()
{
   ReorganizationState st;
   st.prevTopBlock = &top();
   st.reorgBranchPoint = organizeChain();
   st.prevTopBlockStillValid = !st.reorgBranchPoint;
   st.hasNewTop = (st.prevTopBlock != &top());
   return st;
}

Blockchain::ReorganizationState Blockchain::forceOrganize()
{
   ReorganizationState st;
   st.prevTopBlock = &top();
   st.reorgBranchPoint = organizeChain(true);
   st.prevTopBlockStillValid = !st.reorgBranchPoint;
   st.hasNewTop = (st.prevTopBlock != &top());
   return st;
}

BlockHeader& Blockchain::top() const
{
   return *topBlockPtr_;
}

BlockHeader& Blockchain::getGenesisBlock() const
{
   return *genesisBlockBlockPtr_;
}

BlockHeader& Blockchain::getHeaderByHeight(unsigned index) const
{
   if(index>=headersByHeight_.size())
      throw std::range_error("Cannot get block at height " + Util::to_string(index));

   return *headersByHeight_[index];
}

const BlockHeader& Blockchain::getHeaderByHash(HashString const & blkHash) const
{
   map<HashString, BlockHeader>::const_iterator it = headerMap_.find(blkHash);
   if(ITER_NOT_IN_MAP(it, headerMap_))
      throw std::range_error("Cannot find block with hash " + blkHash.toHexStr());
   else
      return it->second;
}
BlockHeader& Blockchain::getHeaderByHash(HashString const & blkHash)
{
   map<HashString, BlockHeader>::iterator it = headerMap_.find(blkHash);
   if(ITER_NOT_IN_MAP(it, headerMap_))
      throw std::range_error("Cannot find block with hash " + blkHash.toHexStr());
   else
      return it->second;
}

bool Blockchain::hasHeaderWithHash(BinaryData const & txHash) const
{
   return KEY_IN_MAP(txHash, headerMap_);
}

const BlockHeader& Blockchain::getHeaderPtrForTxRef(const TxRef &txr) const
{
   if(txr.isNull())
      throw std::range_error("Null TxRef");

   uint32_t hgt = txr.getBlockHeight();
   uint8_t  dup = txr.getDuplicateID();
   const BlockHeader& bh= getHeaderByHeight(hgt);
   if(bh.getDuplicateID() != dup)
   {
      throw runtime_error("Requested txref not on main chain (BH dupID is diff)");
   }
   return bh;
}


////////////////////////////////////////////////////////////////////////////////
// Returns nullptr if the new top block is a direct follower of
// the previous top. Returns the branch point if we had to reorg
// TODO:  Figure out if there is an elegant way to deal with a forked 
//        blockchain containing two equal-length chains
BlockHeader* Blockchain::organizeChain(bool forceRebuild)
{
   SCOPED_TIMER("organizeChain");

   // Why did this line not through an error?  I left here to remind 
   // myself to go figure it out.
   //LOGINFO << ("Organizing chain", (forceRebuild ? "w/ rebuild" : ""));
   LOGDEBUG << "Organizing chain " << (forceRebuild ? "w/ rebuild" : "");

   
   // If rebuild, we zero out any original organization data and do a 
   // rebuild of the chain from scratch.  This will need to be done in
   // the event that our first call to organizeChain returns false, which
   // means part of blockchain that was previously valid, has become
   // invalid.  Rather than get fancy, just rebuild all which takes less
   // than a second, anyway.
   if(forceRebuild)
   {
      map<HashString, BlockHeader>::iterator iter;
      for( iter  = headerMap_.begin(); 
           iter != headerMap_.end(); 
           iter++)
      {
         iter->second.difficultySum_  = -1;
         iter->second.blockHeight_    =  0;
         iter->second.isFinishedCalc_ =  false;
         iter->second.nextHash_       =  BtcUtils::EmptyHash_;
         iter->second.isMainBranch_   =  false;
      }
      topBlockPtr_ = NULL;
   }

   // Set genesis block
   BlockHeader & genBlock = getGenesisBlock();
   genBlock.blockHeight_    = 0;
   genBlock.difficultyDbl_  = 1.0;
   genBlock.difficultySum_  = 1.0;
   genBlock.isMainBranch_   = true;
   genBlock.isOrphan_       = false;
   genBlock.isFinishedCalc_ = true;
   genBlock.isInitialized_  = true; 

   // If this is the first run, the topBlock is the genesis block
   if(topBlockPtr_ == NULL)
      topBlockPtr_ = &genBlock;

   const BlockHeader& prevTopBlock = top();
   
   // Iterate over all blocks, track the maximum difficulty-sum block
   map<HashString, BlockHeader>::iterator iter;
   double   maxDiffSum     = prevTopBlock.getDifficultySum();
   for( iter = headerMap_.begin(); iter != headerMap_.end(); iter ++)
   {
      // *** Walk down the chain following prevHash fields, until
      //     you find a "solved" block.  Then walk back up and 
      //     fill in the difficulty-sum values (do not set next-
      //     hash ptrs, as we don't know if this is the main branch)
      //     Method returns instantly if block is already "solved"
      double thisDiffSum = traceChainDown(iter->second);

      // Determine if this is the top block.  If it's the same diffsum
      // as the prev top block, don't do anything
      if(thisDiffSum > maxDiffSum)
      {
         maxDiffSum     = thisDiffSum;
         topBlockPtr_   = &(iter->second);
      }
   }

   
   // Walk down the list one more time, set nextHash fields
   // Also set headersByHeight_;
   bool prevChainStillValid = (topBlockPtr_ == &prevTopBlock);
   topBlockPtr_->nextHash_ = BtcUtils::EmptyHash_;
   BlockHeader* thisHeaderPtr = topBlockPtr_;
   //headersByHeight_.reserve(topBlockPtr_->getBlockHeight()+32768);
   headersByHeight_.resize(topBlockPtr_->getBlockHeight()+1);
   while( !thisHeaderPtr->isFinishedCalc_ )
   {
      thisHeaderPtr->isFinishedCalc_ = true;
      thisHeaderPtr->isMainBranch_   = true;
      thisHeaderPtr->isOrphan_       = false;
      headersByHeight_[thisHeaderPtr->getBlockHeight()] = thisHeaderPtr;

      // This loop not necessary anymore with the DB implementation
      // We need to guarantee that the txs are pointing to the right block
      // header, because they could've been linked to an invalidated block
      //for(uint32_t i=0; i<thisHeaderPtr->getTxRefPtrList().size(); i++)
      //{
         //TxRef & tx = *(thisHeaderPtr->getTxRefPtrList()[i]);
         //tx.setHeaderPtr(thisHeaderPtr);
         //tx.setMainBranch(true);
      //}

      HashString & childHash    = thisHeaderPtr->thisHash_;
      thisHeaderPtr             = &(headerMap_[thisHeaderPtr->getPrevHash()]);
      thisHeaderPtr->nextHash_  = childHash;

      if(thisHeaderPtr == &prevTopBlock)
         prevChainStillValid = true;

   }
   // Last header in the loop didn't get added (the genesis block on first run)
   thisHeaderPtr->isMainBranch_ = true;
   headersByHeight_[thisHeaderPtr->getBlockHeight()] = thisHeaderPtr;


   // Force a full rebuild to make sure everything is marked properly
   // On a full rebuild, prevChainStillValid should ALWAYS be true
   if( !prevChainStillValid )
   {
      LOGWARN << "Reorg detected!";

      organizeChain(true); // force-rebuild blockchain (takes less than 1s)
      return thisHeaderPtr;
   }

   // Let the caller know that there was no reorg
   LOGDEBUG << "Done organizing chain";
   return 0;
}


/////////////////////////////////////////////////////////////////////////////
// Start from a node, trace down to the highest solved block, accumulate
// difficulties and difficultySum values.  Return the difficultySum of 
// this block.
double Blockchain::traceChainDown(BlockHeader & bhpStart)
{
   if(bhpStart.difficultySum_ > 0)
      return bhpStart.difficultySum_;

   // Prepare some data structures for walking down the chain
   vector<BlockHeader*>   headerPtrStack(headerMap_.size());
   vector<double>         difficultyStack(headerMap_.size());
   uint32_t blkIdx = 0;

   // Walk down the chain of prevHash_ values, until we find a block
   // that has a definitive difficultySum value (i.e. >0). 
   BlockHeader* thisPtr = &bhpStart;
   while( thisPtr->difficultySum_ < 0)
   {
      double thisDiff         = thisPtr->difficultyDbl_;
      difficultyStack[blkIdx] = thisDiff;
      headerPtrStack[blkIdx]  = thisPtr;
      blkIdx++;

      map<HashString, BlockHeader>::iterator iter = headerMap_.find(thisPtr->getPrevHash());
      if(ITER_IN_MAP(iter, headerMap_))
         thisPtr = &(iter->second);
      else
      {
         // Under some circumstances, the headers DB is not getting written
         // properly and triggering this code due to missing headers.  For 
         // now, we simply avoid this condition by flagging the headers DB
         // to be rebuilt.  The bug probably has to do with batching of
         // header data.
         throw BlockCorruptionError();
         
         // previously here: markOrphanBlock
      }
   }


   // Now we have a stack of difficulties and pointers.  Walk back up
   // (by pointer) and accumulate the difficulty values 
   double   seedDiffSum = thisPtr->difficultySum_;
   uint32_t blkHeight   = thisPtr->blockHeight_;
   for(int32_t i=blkIdx-1; i>=0; i--)
   {
      seedDiffSum += difficultyStack[i];
      blkHeight++;
      thisPtr                 = headerPtrStack[i];
      thisPtr->difficultyDbl_ = difficultyStack[i];
      thisPtr->difficultySum_ = seedDiffSum;
      thisPtr->blockHeight_   = blkHeight;
   }
   
   // Finally, we have all the difficulty sums calculated, return this one
   return bhpStart.difficultySum_;
  
}



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// Start BlockDataManager_LevelDB methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BlockDataManager_LevelDB::BlockDataManager_LevelDB(void) 
   : blockchain_(this)
{
   Reset();
}

/////////////////////////////////////////////////////////////////////////////
BlockDataManager_LevelDB::~BlockDataManager_LevelDB(void)
{
   set<BtcWallet*>::iterator iter;
   for(iter  = registeredWallets_.begin();
       iter != registeredWallets_.end();
       iter++)
   {
      delete *iter;
   }

   Reset();
}

/////////////////////////////////////////////////////////////////////////////
// We must set the network-specific data for this blockchain
//
// bdm.SetBtcNetworkParams( READHEX(MAINNET_GENESIS_HASH_HEX),
//                          READHEX(MAINNET_GENESIS_TX_HASH_HEX),
//                          READHEX(MAINNET_MAGIC_BYTES));
//
// The above call will work 
void BlockDataManager_LevelDB::SetBtcNetworkParams(
                                    BinaryData const & GenHash,
                                    BinaryData const & GenTxHash,
                                    BinaryData const & MagicBytes)
{
   LOGINFO << "SetBtcNetworkParams";
   GenesisHash_.copyFrom(GenHash);
   GenesisTxHash_.copyFrom(GenTxHash);
   MagicBytes_.copyFrom(MagicBytes);
   
   // this is needed for making gtest work, I don't know why (~CS)
   blockchain_.clear();
}



/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::SetHomeDirLocation(string homeDir)
{
   // This will eventually be used to store blocks/DB
   LOGINFO << "Set home directory: " << armoryHomeDir_.c_str();
   armoryHomeDir_   = homeDir; 
   blkProgressFile_ = homeDir + string("/blkfiles.txt");
   abortLoadFile_   = homeDir + string("/abortload.txt");
}

/////////////////////////////////////////////////////////////////////////////
// Bitcoin-Qt/bitcoind 0.8+ changed the location and naming convention for 
// the blkXXXX.dat files.  The first block file use to be:
//
//    ~/.bitcoin/blocks/blk00000.dat   
//
// UPDATE:  Compatibility with pre-0.8 nodes removed after 6+ months and
//          a hard-fork that makes it tougher to use old versions.
//
bool BlockDataManager_LevelDB::SetBlkFileLocation(string blkdir)
{
   blkFileDir_    = blkdir; 
   isBlkParamsSet_ = true;

   detectAllBlkFiles();

   LOGINFO << "Set blkfile dir: " << blkFileDir_.c_str();

   return (numBlkFiles_!=UINT16_MAX);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::SetLevelDBLocation(string ldbdir)
{
   leveldbDir_    = ldbdir; 
   isLevelDBSet_  = true;
   LOGINFO << "Set leveldb dir: " << leveldbDir_.c_str();
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::SelectNetwork(string netName)
{
   if(netName.compare("Main") == 0)
   {
      SetBtcNetworkParams( READHEX(MAINNET_GENESIS_HASH_HEX),
                           READHEX(MAINNET_GENESIS_TX_HASH_HEX),
                           READHEX(MAINNET_MAGIC_BYTES)         );
   }
   else if(netName.compare("Test") == 0)
   {
      SetBtcNetworkParams( READHEX(TESTNET_GENESIS_HASH_HEX),
                           READHEX(TESTNET_GENESIS_TX_HASH_HEX),
                           READHEX(TESTNET_MAGIC_BYTES)         );
   }
   else
      LOGERR << "ERROR: Unrecognized network name";

   isNetParamsSet_ = true;
}



/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::checkLdbStatus(leveldb::Status stat)
{
   if( stat.ok() )
      return true;

   LOGERR << "***LevelDB Error: " << stat.ToString();
   return false;
}

//////////////////////////////////////////////////////////////////////////
// This method opens the databases, and figures out up to what block each
// of them is sync'd to.  Then it figures out where that corresponds in
// the blk*.dat files, so that it can pick up where it left off.  You can 
// use the last argument to specify an approximate amount of blocks 
// (specified in bytes) that you would like to replay:  i.e. if 10 MB,
// startScanBlkFile_ and endOfLastBlockByte_ variables will be set to
// the first block that is approximately 10 MB behind your latest block.
// Then you can pick up from there and let the DB clean up any mess that
// was left from an unclean shutdown.
bool BlockDataManager_LevelDB::initializeDBInterface(ARMORY_DB_TYPE dbtype,
                                                     DB_PRUNE_TYPE  prtype)
{
   SCOPED_TIMER("initializeDBInterface");
   if(!isBlkParamsSet_ || !isLevelDBSet_)
   {
      LOGERR << "Cannot sync DB until blkfile and LevelDB paths are set. ";
      return false;
   }

   if(iface_->databasesAreOpen())
   {
      LOGERR << "Attempted to initialize a database that was already open";
      return false;
   }


   bool openWithErr = iface_->openDatabases(leveldbDir_, 
                                            GenesisHash_, 
                                            GenesisTxHash_, 
                                            MagicBytes_,
                                            dbtype, 
                                            prtype);

   return openWithErr;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::detectCurrentSyncState(
                                          bool forceRebuild,
                                          bool initialLoad)
{
   // Make sure we detected all the available blk files
   detectAllBlkFiles();
   vector<BinaryData> firstHashes = getFirstHashOfEachBlkFile();
   LOGINFO << "Total blk*.dat files:                 " << numBlkFiles_;

   if(!iface_->databasesAreOpen())
   {
      LOGERR << "Could not open databases!";
      return false;
   }

   // We add 1 to each of these, since we always use exclusive upperbound
   startHeaderHgt_ = getTopBlockHeightInDB(HEADERS) + 1;
   startRawBlkHgt_ = getTopBlockHeightInDB(BLKDATA) + 1;
   startApplyHgt_  = getAppliedToHeightInDB() + 1;

   // If the values were supposed to be zero, they'll get set to 1.  Fix it
   startHeaderHgt_ -= (startHeaderHgt_==1 ? 1 : 0);
   startRawBlkHgt_ -= (startRawBlkHgt_==1 ? 1 : 0);
   startApplyHgt_  -= (startApplyHgt_ ==1 ? 1 : 0);

   LOGINFO << "Current Top block in HEADERS DB:  " << startHeaderHgt_;
   LOGINFO << "Current Top block in BLKDATA DB:  " << startRawBlkHgt_;
   LOGINFO << "Current Applied blocks up to hgt: " << startApplyHgt_;

   if(startHeaderHgt_ == 0 || forceRebuild)
   {
      if(forceRebuild)
         LOGINFO << "Ignore existing sync state, rebuilding databases";

      startHeaderHgt_     = 0;
      startHeaderBlkFile_ = 0;
      startHeaderOffset_  = 0;
      startRawBlkHgt_     = 0;
      startRawBlkFile_    = 0;
      startRawOffset_     = 0;
      startApplyHgt_      = 0;
      startApplyBlkFile_  = 0;
      startApplyOffset_   = 0;
      lastTopBlock_ = UINT32_MAX;
      blockchain_.clear();
      return true;
   }

   // This fetches the header data from the DB
   if(!initialLoad)
   {
      // If this isn't the initial load, we assume everything is sync'd
      startHeaderBlkFile_= numBlkFiles_ - 1;
      startHeaderOffset_ = endOfLastBlockByte_;
      startRawBlkHgt_    = startHeaderHgt_;  
      startRawBlkFile_   = numBlkFiles_ - 1;
      startRawOffset_    = endOfLastBlockByte_;
      startApplyHgt_     = startHeaderHgt_;
      startApplyBlkFile_ = numBlkFiles_ - 1;
      startApplyOffset_  = endOfLastBlockByte_;
      return true;
   }

   map<HashString, StoredHeader> sbhMap;
   blockchain_.clear();
   {
      map<HashString, BlockHeader> headers;
      iface_->readAllHeaders(headers, sbhMap);
      for (map<HashString, BlockHeader>::iterator i = headers.begin();
            i != headers.end(); ++i
         )
      {
         blockchain_.addBlock(i->first, i->second);
      }
   }

   try
   {
      // Organize them into the longest chain
      blockchain_.forceOrganize();
   }
   catch (Blockchain::BlockCorruptionError &)
   {
      // If the headers DB ended up corrupted (triggered by forceOrganize), 
      // then nuke and rebuild the headers
      LOGERR << "Corrupted headers DB!";
      startHeaderHgt_     = 0;
      startHeaderBlkFile_ = 0;
      startHeaderOffset_  = 0;
      startRawBlkHgt_     = 0;
      startRawBlkFile_    = 0;
      startRawOffset_     = 0;
      startApplyHgt_      = 0;
      startApplyBlkFile_  = 0;
      startApplyOffset_   = 0;
      lastTopBlock_       = UINT32_MAX;
      blockchain_.clear();
      return true;
   }
   
   {
      // Now go through the linear list of main-chain headers, mark valid
      for(unsigned i=0; i<blockchain_.numHeaders(); i++)
      {
         BinaryDataRef headHash = blockchain_.getHeaderByHeight(i).getThisHashRef();
         StoredHeader & sbh = sbhMap[headHash];
         sbh.isMainBranch_ = true;
         iface_->setValidDupIDForHeight(sbh.blockHeight_, sbh.duplicateID_);
      }

      // startHeaderBlkFile_/Offset_ is where we were before the last shutdown
      for(startHeaderBlkFile_ = 0; 
         startHeaderBlkFile_ < firstHashes.size(); 
         startHeaderBlkFile_++)
      {
         // hasHeaderWithHash is probing the RAM block headers we just organized
         if(!blockchain_.hasHeaderWithHash(firstHashes[startHeaderBlkFile_]))
            break;
      }

      // If no new blkfiles since last load, the above loop ends w/o "break"
      // If it's zero, then we don't have anything, start at zero
      // If new blk file, then startHeaderBlkFile_ is at the first blk file
      // with an unrecognized hash... we must've left off in the prev blkfile
      if(startHeaderBlkFile_ > 0)
         startHeaderBlkFile_--;

      startHeaderOffset_ = findOffsetFirstUnrecognized(startHeaderBlkFile_);
   }

   LOGINFO << "First unrecognized hash file:       " << startHeaderBlkFile_;
   LOGINFO << "Offset of first unrecog block:      " << startHeaderOffset_;


   // Note that startRawBlkHgt_ is topBlk+1, so this return where we should
   // actually start processing raw blocks, not the last one we processed
   pair<uint32_t, uint32_t> rawBlockLoc;
   rawBlockLoc = findFileAndOffsetForHgt(startRawBlkHgt_, &firstHashes);
   startRawBlkFile_ = rawBlockLoc.first;
   startRawOffset_ = rawBlockLoc.second;
   LOGINFO << "First blkfile not in DB:            " << startRawBlkFile_;
   LOGINFO << "Location of first block not in DB:  " << startRawOffset_;

   if(DBUtils.getArmoryDbType() != ARMORY_DB_BARE)
   {
      // TODO:  finish this
      findFirstUnappliedBlock();
      LOGINFO << "Blkfile of first unapplied block:   " << startApplyBlkFile_;
      LOGINFO << "Location of first unapplied block:  " << startApplyOffset_;
   }


   // If we're content here, just return
   return true;

   /*

   // If we want to replay some blocks, we need to adjust startScanBlkFile_
   // and startScanOffset_ to be approx "replayNBytes" behind where
   // they are currently set.
   int32_t targOffset = (int32_t)startScanOffset_ - (int32_t)replayNBytes;
   if(targOffset > 0 || startScanBlkFile_==0)
   {
      targOffset = max(0, targOffset);
      startScanOffset_ = findFirstBlkApproxOffset(startScanBlkFile_, targOffset); 
   }
   else
   {
      startScanBlkFile_--;
      uint32_t prevFileSize = BtcUtils::GetFileSize(blkFileList_[startScanBlkFile_]);
      targOffset = (int32_t)prevFileSize - (int32_t)replayNBytes;
      targOffset = max(0, targOffset);
      startScanOffset_ = findFirstBlkApproxOffset(startScanBlkFile_, targOffset); 
   }

   LOGINFO << "Rewinding start block to enforce DB integrity";
   LOGINFO << "Start at blockfile:              " << startScanBlkFile_;
   LOGINFO << "Start location in above blkfile: " << startScanOffset_;
   return true;
   */
}


////////////////////////////////////////////////////////////////////////////////
vector<BinaryData> BlockDataManager_LevelDB::getFirstHashOfEachBlkFile(void) const
{
   if(!isBlkParamsSet_)
   {
      LOGERR << "Can't get blk files until blkfile params are set";
      return vector<BinaryData>(0);
   }

   uint32_t nFile = (uint32_t)blkFileList_.size();
   BinaryData magic(4), szstr(4), rawHead(HEADER_SIZE);
   vector<BinaryData> headHashes(nFile);
   for(uint32_t f=0; f<nFile; f++)
   {
      ifstream is(blkFileList_[f].c_str(), ios::in|ios::binary);
      is.seekg(0, ios::end);
      size_t filesize = (size_t)is.tellg();
      is.seekg(0, ios::beg);
      if(filesize < 88)
      {
         is.close(); 
         LOGERR << "File: " << blkFileList_[f] << " is less than 88 bytes!";
         continue;
      }

      is.read((char*)magic.getPtr(), 4);
      is.read((char*)szstr.getPtr(), 4);
      if(magic != MagicBytes_)
      {
         is.close(); 
         LOGERR << "Magic bytes mismatch.  Block file is for another network!";
         return vector<BinaryData>(0);
      }
      
      is.read((char*)rawHead.getPtr(), HEADER_SIZE);
      headHashes[f] = BinaryData(32);
      BtcUtils::getHash256(rawHead, headHashes[f]);
      is.close();
   }
   return headHashes;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_LevelDB::findOffsetFirstUnrecognized(uint32_t fnum) 
{
   uint32_t loc = 0;
   BinaryData magic(4), szstr(4), rawHead(80), hashResult(32);

   ifstream is(blkFileList_[fnum].c_str(), ios::in|ios::binary);
   while(!is.eof())
   {
      is.read((char*)magic.getPtr(), 4);
      if(is.eof()) break;

   
      // This is not an error, it just simply hit the padding
      if(magic!=MagicBytes_)  
         break;

      is.read((char*)szstr.getPtr(), 4);
      uint32_t blksize = READ_UINT32_LE(szstr.getPtr());
      if(is.eof()) break;

      is.read((char*)rawHead.getPtr(), HEADER_SIZE); 

      BtcUtils::getHash256_NoSafetyCheck(rawHead.getPtr(), HEADER_SIZE, hashResult);
      if(!blockchain_.hasHeaderWithHash(hashResult))
         break; // first hash in the file that isn't in our header map

      loc += blksize + 8;
      is.seekg(blksize - HEADER_SIZE, ios::cur);

   }
   
   is.close();
   return loc;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_LevelDB::findFirstBlkApproxOffset(uint32_t fnum,
                                                            uint32_t offset) const
{
   if(fnum >= numBlkFiles_)
   {
      LOGERR << "Blkfile number out of range! (" << fnum << ")";
      return UINT32_MAX;
   }

   uint32_t loc = 0;
   BinaryData magic(4), szstr(4), rawHead(80), hashResult(32);
   ifstream is(blkFileList_[fnum].c_str(), ios::in|ios::binary);
   while(!is.eof() && loc <= offset)
   {
      is.read((char*)magic.getPtr(), 4);
      if(is.eof()) break;
      if(magic!=MagicBytes_)
         return UINT32_MAX;

      is.read((char*)szstr.getPtr(), 4);
      uint32_t blksize = READ_UINT32_LE(szstr.getPtr());
      if(is.eof()) break;

      loc += blksize + 8;
      is.seekg(blksize, ios::cur);
   }

   is.close();
   return loc;
}

////////////////////////////////////////////////////////////////////////////////
pair<uint32_t, uint32_t> BlockDataManager_LevelDB::findFileAndOffsetForHgt(
                                           uint32_t hgt, 
                                           vector<BinaryData> * firstHashes)
{
   vector<BinaryData> recomputedHashes;
   if(firstHashes==NULL)
   {
      recomputedHashes = getFirstHashOfEachBlkFile();
      firstHashes = &recomputedHashes;
   }

   pair<uint32_t, uint32_t> outPair;
   int32_t blkfile;
   for(blkfile = 0; blkfile < (int32_t)firstHashes->size(); blkfile++)
   {
      try
      {
         BlockHeader &bh = blockchain_.getHeaderByHash((*firstHashes)[blkfile]);

         if(bh.getBlockHeight() > hgt)
            break;
      }
      catch (...)
      {
         break;
      }
   }

   blkfile = max(blkfile-1, 0);
   if(blkfile >= (int32_t)numBlkFiles_)
   {
      LOGERR << "Blkfile number out of range! (" << blkfile << ")";
      return outPair;
   }

   uint32_t loc = 0;
   BinaryData magic(4), szstr(4), rawHead(HEADER_SIZE), hashResult(32);
   ifstream is(blkFileList_[blkfile].c_str(), ios::in|ios::binary);
   while(!is.eof())
   {
      is.read((char*)magic.getPtr(), 4);
      if(is.eof()) break;
      if(magic!=MagicBytes_)
         break;

      is.read((char*)szstr.getPtr(), 4);
      uint32_t blksize = READ_UINT32_LE(szstr.getPtr());
      if(is.eof()) break;

      is.read((char*)rawHead.getPtr(), HEADER_SIZE); 
      BtcUtils::getHash256_NoSafetyCheck(rawHead.getPtr(), 
                                         HEADER_SIZE, 
                                         hashResult);

      try
      {
         BlockHeader &bh = blockchain_.getHeaderByHash(hashResult);
         
         if(bh.getBlockHeight() >= hgt)
            break;
      }
      catch (...)
      {
         break;
      }
      loc += blksize + 8;
      is.seekg(blksize - HEADER_SIZE, ios::cur);
   }

   is.close();

   outPair.first  = blkfile;
   outPair.second = loc;
   
   return outPair;
   

}


////////////////////////////////////////////////////////////////////////////////
// This behaves very much like the algorithm for finding the branch point 
// in the header tree with a peer.
uint32_t BlockDataManager_LevelDB::findFirstUnappliedBlock(void)
{
   SCOPED_TIMER("findFirstUnappliedBlock");

   if(!iface_->databasesAreOpen())
   {
      LOGERR << "Database is not open!";
      return UINT32_MAX;
   }
   
   int32_t blkCheck = (int32_t)getTopBlockHeightInDB(BLKDATA);

   StoredHeader sbh;
   uint32_t toSub = 0;
   uint32_t nIter = 0;
   do
   {
      blkCheck -= toSub;
      if(blkCheck < 0)
      {
         blkCheck = 0;
         break;
      }

      iface_->getStoredHeader(sbh, (uint32_t)blkCheck);

      if(nIter++ < 10) 
         toSub += 1;  // we get some N^2 action here (for the first 10 iter)
      else
         toSub = (uint32_t)(1.5*toSub); // after that, increase exponentially

   } while(!sbh.blockAppliedToDB_);

   // We likely overshot in the last loop, so walk forward until we get to it.
   do
   {
      iface_->getStoredHeader(sbh, (uint32_t)blkCheck);
      blkCheck += 1;   
   } while(sbh.blockAppliedToDB_);

   return (uint32_t)blkCheck;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_LevelDB::getTopBlockHeightInDB(DB_SELECT db)
{
   StoredDBInfo sdbi;
   iface_->getStoredDBInfo(db, sdbi, false); 
   return sdbi.topBlkHgt_;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_LevelDB::getAppliedToHeightInDB(void)
{
   StoredDBInfo sdbi;
   iface_->getStoredDBInfo(BLKDATA, sdbi, false); 
   return sdbi.appliedToHgt_;
}

/////////////////////////////////////////////////////////////////////////////
// The only way to "create" a BDM is with this method, which creates it
// if one doesn't exist yet, or returns a reference to the only one
// that will ever exist
BlockDataManager_LevelDB & BlockDataManager_LevelDB::GetInstance(void) 
{
   if( !bdmCreatedYet_ )
   {
      theOnlyBDM_ = new BlockDataManager_LevelDB;
      bdmCreatedYet_ = true;
      iface_ = LevelDBWrapper::GetInterfacePtr();
   }
   return (*theOnlyBDM_);
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::DestroyInstance(void)
{
   theOnlyBDM_->Reset();
   iface_->closeDatabases();
   delete theOnlyBDM_;
   bdmCreatedYet_ = false;
   iface_ = NULL;
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::Reset(void)
{
   SCOPED_TIMER("BDM::Reset");

   // Clear out all the "real" data in the blkfile
   blkFileDir_ = "";
   blockchain_.clear();

   zeroConfRawTxList_.clear();
   zeroConfMap_.clear();
   zcEnabled_  = false;
   zcLiteMode_ = false;
   zcFilename_ = "";

   isNetParamsSet_ = false;
   isBlkParamsSet_ = false;
   isLevelDBSet_ = false;
   armoryHomeDir_ = string("");
   blkFileDir_ = string("");
   blkFileList_.clear();
   numBlkFiles_ = UINT32_MAX;

   endOfLastBlockByte_ = 0;

   startHeaderHgt_ = 0;
   startRawBlkHgt_ = 0;
   startApplyHgt_ = 0;
   startHeaderBlkFile_ = 0;
   startHeaderOffset_ = 0;
   startRawBlkFile_ = 0;
   startRawOffset_ = 0;
   startApplyBlkFile_ = 0;
   startApplyOffset_ = 0;
   lastTopBlock_ = 0;


   // Reorganization details
   txJustInvalidated_.clear();
   txJustAffected_.clear();

   // Reset orphan chains
   previouslyValidBlockHeaderPtrs_.clear();
   orphanChainStartBlocks_.clear();

   GenesisHash_.resize(0);
   GenesisTxHash_.resize(0);
   MagicBytes_.resize(0);
   
   totalBlockchainBytes_ = 0;
   bytesReadSoFar_ = 0;
   blocksReadSoFar_ = 0;
   filesReadSoFar_ = 0;

   isInitialized_ = false;
   corruptHeadersDB_ = false;

   // Clear out any of the registered tx data we have collected so far.
   // Doesn't take any time to recollect if it we have to rescan, anyway.

   registeredWallets_.clear();
   registeredScrAddrMap_.clear();
   registeredTxSet_.clear();
   registeredTxList_.clear(); 
   registeredOutPoints_.clear(); 
   allScannedUpToBlk_ = 0;

}



/////////////////////////////////////////////////////////////////////////////
int32_t BlockDataManager_LevelDB::getNumConfirmations(HashString txHash)
{
   TxRef txrefobj = getTxRefByHash(txHash);
   if(txrefobj.isNull())
      return TX_NOT_EXIST;
   else
   {
      try
      {
         BlockHeader & txbh = blockchain_.getHeaderByHeight(txrefobj.getBlockHeight());
         if(!txbh.isMainBranch())
            return TX_OFF_MAIN_BRANCH;

         int32_t txBlockHeight  = txbh.getBlockHeight();
         int32_t topBlockHeight = blockchain_.top().getBlockHeight();
         return  topBlockHeight - txBlockHeight + 1;
      }
      catch (std::exception &e)
      {
         LOGERR << "Failed to get num confirmations: " << e.what();
         return TX_0_UNCONFIRMED;
      }
   }
}

/////////////////////////////////////////////////////////////////////////////
TxRef BlockDataManager_LevelDB::getTxRefByHash(HashString const & txhash) 
{
   return iface_->getTxRef(txhash);
}


/////////////////////////////////////////////////////////////////////////////
Tx BlockDataManager_LevelDB::getTxByHash(HashString const & txhash)
{

   TxRef txrefobj = getTxRefByHash(txhash);

   if(!txrefobj.isNull())
      return txrefobj.getTxCopy();
   else
   {
      // It's not in the blockchain, but maybe in the zero-conf tx list
      map<HashString, ZeroConfData>::const_iterator iter = zeroConfMap_.find(txhash);
      //if(iter==zeroConfMap_.end())
      if(ITER_NOT_IN_MAP(iter, zeroConfMap_))
         return Tx();
      else
         return iter->second.txobj_;
   }
}


/////////////////////////////////////////////////////////////////////////////
TX_AVAILABILITY BlockDataManager_LevelDB::getTxHashAvail(BinaryDataRef txHash)
{
   if(getTxRefByHash(txHash).isNull())
   {
      //if(zeroConfMap_.find(txHash)==zeroConfMap_.end())
      if(KEY_NOT_IN_MAP(txHash, zeroConfMap_))
         return TX_DNE;  // No tx at all
      else
         return TX_ZEROCONF;  // Zero-conf tx
   }
   else
      return TX_IN_BLOCKCHAIN; // In the blockchain already
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::hasTxWithHashInDB(BinaryData const & txHash)
{
   return iface_->getTxRef(txHash).isInitialized();
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::hasTxWithHash(BinaryData const & txHash)
{
   if(iface_->getTxRef(txHash).isInitialized())
      return true;
   else
      return KEY_IN_MAP(txHash, zeroConfMap_);
}

/////////////////////////////////////////////////////////////////////////////
/*
vector<BlockHeader*> BlockDataManager_LevelDB::prefixSearchHeaders(BinaryData const & searchStr)
{
   vector<BlockHeader*> outList(0);
   uint32_t lenSearch = searchStr.getSize();
   if(lenSearch < 2)
      return outList;  // don't search unless we have at least two bytes

   BinaryData searchLow(32);
   BinaryData searchHigh(32);
   for(uint32_t i=0; i<lenSearch; i++)
   {
      searchLow[i]  = searchStr[i];
      searchHigh[i] = searchStr[i];
   }
   for(uint32_t i=lenSearch; i<32; i++)
   {
      searchLow[i]  = 0;
      searchHigh[i] = 255;
   }

   map<HashString, BlockHeader>::iterator iter;
   for(iter  = headerMap_.lower_bound(searchLow);
       iter != headerMap_.upper_bound(searchHigh);
       iter++)
   {
      outList.push_back(&(iter->second));
   }
   return outList;
}
*/

/////////////////////////////////////////////////////////////////////////////
/*
vector<TxRef*> BlockDataManager_LevelDB::prefixSearchTx(BinaryData const & searchStr)
{
   vector<TxRef*> outList(0);
   uint32_t lenSearch = searchStr.getSize();
   if(lenSearch < 2)
      return outList;  // don't search unless we have at least two bytes

   BinaryData searchLow(32);
   BinaryData searchHigh(32);
   for(uint32_t i=0; i<lenSearch; i++)
   {
      searchLow[i]  = searchStr[i];
      searchHigh[i] = searchStr[i];
   }
   for(uint32_t i=lenSearch; i<32; i++)
   {
      searchLow[i]  = 0;
      searchHigh[i] = 255;
   }

   BinaryData searchLow4  = searchLow.getSliceCopy(0,4);
   BinaryData searchHigh4 = searchHigh.getSliceCopy(0,4);
   multimap<HashString, TxRef>::iterator iter;
   for(iter  = txHintMap_.lower_bound(searchLow4);
       iter != txHintMap_.upper_bound(searchHigh4);
       iter++)
   {
      if(iter->second.getThisHash().startsWith(searchStr))
         outList.push_back(&(iter->second));
   }
   return outList;
}

/////////////////////////////////////////////////////////////////////////////
// Since the cpp code doesn't have full addresses (only 20-byte hashes),
// that's all we can search for.  
vector<BinaryData> BlockDataManager_LevelDB::prefixSearchAddress(BinaryData const & searchStr)
{
   // Actually, we can't even search for this, because we don't have a list
   // of addresses in the blockchain.  We could construct one, but it would
   // take up a lot of RAM (and time)... I will need to create a separate 
   // call to allow the caller to create a set<BinaryData> of addresses 
   // before calling this method
   return vector<BinaryData>(0);
}
*/





/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::registerWallet(BtcWallet* wltPtr, bool wltIsNew)
{
   SCOPED_TIMER("registerWallet");

   // Check if the wallet is already registered
   //if(registeredWallets_.find(wltPtr) != registeredWallets_.end())
   if(KEY_IN_MAP(wltPtr, registeredWallets_))
      return false;

   // Add it to the list of wallets to watch
   registeredWallets_.insert(wltPtr);

   // Now add all the individual addresses from the wallet
   for(uint32_t i=0; i<wltPtr->getNumScrAddr(); i++)
   {
      // If this is a new wallet, the value of getFirstBlockNum is irrelevant
      ScrAddrObj & addr = wltPtr->getScrAddrObjByIndex(i);

      if(wltIsNew)
         registerNewScrAddr(addr.getScrAddr());
      else
         registerImportedScrAddr(addr.getScrAddr(), addr.getFirstBlockNum());
   }

   // We need to make sure the wallet can tell the BDM when an address is added
   wltPtr->setBdmPtr(this);
   return true;
}


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::registerScrAddr(HashString scraddr, 
                                                bool addrIsNew,
                                                uint32_t firstBlk)
{
   SCOPED_TIMER("registerScrAddr");
   if(KEY_IN_MAP(scraddr, registeredScrAddrMap_))
   {
      // Address is already registered.  Don't think there's anything to do 
      return false;
   }

   if(addrIsNew)
      firstBlk = blockchain_.top().getBlockHeight() + 1;

   registeredScrAddrMap_[scraddr] = RegisteredScrAddr(scraddr, firstBlk);
   allScannedUpToBlk_  = min(firstBlk, allScannedUpToBlk_);
   return true;
}


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::registerNewScrAddr(HashString scraddr)
{
   SCOPED_TIMER("registerNewScrAddr");
   if(KEY_IN_MAP(scraddr, registeredScrAddrMap_))
      return false;

   uint32_t currBlk = blockchain_.top().getBlockHeight();
   registeredScrAddrMap_[scraddr] = RegisteredScrAddr(scraddr, currBlk);

   // New address cannot affect allScannedUpToBlk_, so don't bother
   //allScannedUpToBlk_  = min(currBlk, allScannedUpToBlk_);
   return true;
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::registerImportedScrAddr(HashString scraddr,
                                                    uint32_t createBlk)
{
   SCOPED_TIMER("registerImportedScrAddr");
   if(KEY_IN_MAP(scraddr, registeredScrAddrMap_))
      return false;

   // In some cases we may have used UINT32_MAX to specify "don't know"
   if(createBlk==UINT32_MAX)
      createBlk = 0;

   registeredScrAddrMap_[scraddr] = RegisteredScrAddr(scraddr, createBlk);
   allScannedUpToBlk_ = min(createBlk, allScannedUpToBlk_);
   return true;
}


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::unregisterScrAddr(HashString scraddr)
{
   SCOPED_TIMER("unregisterScrAddr");
   //if(registeredScrAddrMap_.find(scraddr) == registeredScrAddrMap_.end())
   if(KEY_IN_MAP(scraddr, registeredScrAddrMap_))
      return false;
   
   registeredScrAddrMap_.erase(scraddr);
   allScannedUpToBlk_ = evalLowestBlockNextScan();
   return true;
}



/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_LevelDB::evalLowestBlockNextScan(void)
{
   SCOPED_TIMER("evalLowestBlockNextScan");

   uint32_t lowestBlk = UINT32_MAX;
   uint32_t i=0;
   map<HashString, RegisteredScrAddr>::iterator rsaIter;
   for(rsaIter  = registeredScrAddrMap_.begin();
       rsaIter != registeredScrAddrMap_.end();
       rsaIter++)
   {
      // If we happen to have any imported addresses, this will set the
      // lowest block to 0, which will require a full rescan
      lowestBlk = min(lowestBlk, rsaIter->second.alreadyScannedUpToBlk_);
   }
   return lowestBlk;
}

/////////////////////////////////////////////////////////////////////////////
// This method isn't really used yet...
uint32_t BlockDataManager_LevelDB::evalLowestScrAddrCreationBlock(void)
{
   SCOPED_TIMER("evalLowestAddressCreationBlock");

   uint32_t lowestBlk = UINT32_MAX;
   map<HashString, RegisteredScrAddr>::iterator rsaIter;
   for(rsaIter  = registeredScrAddrMap_.begin();
       rsaIter != registeredScrAddrMap_.end();
       rsaIter++)
   {
      // If we happen to have any imported addresses, this will set the
      // lowest block to 0, which will require a full rescan
      lowestBlk = min(lowestBlk, rsaIter->second.blkCreated_);
   }
   return lowestBlk;
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::evalRescanIsRequired(void)
{
   // This method tells us whether we have to scan ANY blocks from disk
   // in order to produce accurate balances and TxOut lists.  If this
   // returns false, we can get away without any disk access at all, and
   // just use the registeredTxList_ object to get our information.
   allScannedUpToBlk_ = evalLowestBlockNextScan();
   return (allScannedUpToBlk_ < blockchain_.top().getBlockHeight()+1);
}


/////////////////////////////////////////////////////////////////////////////
// This method needs to be callable from another thread.  Therefore, I don't
// seek an exact answer, instead just estimate it based on the last block, 
// and the set of currently-registered addresses.  The method called
// "evalRescanIsRequired()" answers a different question, and iterates 
// through the list of registered addresses, which may be changing in 
// another thread.  
bool BlockDataManager_LevelDB::isDirty( 
                              uint32_t numBlocksToBeConsideredDirty ) const
{
   if(!isInitialized_)
      return false;
   
   uint32_t numBlocksBehind = lastTopBlock_-allScannedUpToBlk_;
   return (numBlocksBehind > numBlocksToBeConsideredDirty);
  
}


/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_LevelDB::numBlocksToRescan( BtcWallet & wlt,
                                                       uint32_t endBlk)
{
   SCOPED_TIMER("numBlocksToRescan");
   // This method tells us whether we have to scan ANY blocks from disk
   // in order to produce accurate balances and TxOut lists.  If this
   // returns false, we can get away without any disk access at all, and
   // just use the registeredTxList_ object to get our information.
   uint32_t currNextBlk = blockchain_.top().getBlockHeight() + 1;
   endBlk = min(endBlk, currNextBlk);

   // If wallet is registered and current, no rescan necessary
   if(walletIsRegistered(wlt))
      return (endBlk - allScannedUpToBlk_);

   // The wallet isn't registered with the BDM, but there's a chance that 
   // each of its addresses are -- if any one is not, do rescan
   uint32_t maxAddrBehind = 0;
   for(uint32_t i=0; i<wlt.getNumScrAddr(); i++)
   {
      ScrAddrObj & addr = wlt.getScrAddrObjByIndex(i);

      // If any address is not registered, will have to do a full scan
      //if(registeredScrAddrMap_.find(addr.getScrAddr()) == registeredScrAddrMap_.end())
      if(KEY_NOT_IN_MAP(addr.getScrAddr(), registeredScrAddrMap_))
         return endBlk;  // Gotta do a full rescan!

      RegisteredScrAddr & ra = registeredScrAddrMap_[addr.getScrAddr()];
      maxAddrBehind = max(maxAddrBehind, endBlk-ra.alreadyScannedUpToBlk_);
   }

   // If we got here, then all addr are already registered and current
   return maxAddrBehind;
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::updateRegisteredScrAddrs(uint32_t newTopBlk)
{
   map<HashString, RegisteredScrAddr>::iterator rsaIter;
   for(rsaIter  = registeredScrAddrMap_.begin();
       rsaIter != registeredScrAddrMap_.end();
       rsaIter++)
   {
      rsaIter->second.alreadyScannedUpToBlk_ = newTopBlk;
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::resetRegisteredWallets(void)
{
   SCOPED_TIMER("resetRegisteredWallets");

   set<BtcWallet*>::iterator wltPtrIter;
   for(wltPtrIter  = registeredWallets_.begin();
       wltPtrIter != registeredWallets_.end();
       wltPtrIter++)
   {
      // I'm not sure if there's anything else to do
      // I think it's all encapsulated in this call!
      (*wltPtrIter)->clearBlkData();
   }

   // Reset all addresses to "new"
   updateRegisteredScrAddrs(0);
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::walletIsRegistered(BtcWallet & wlt)
{
   //return (registeredWallets_.find(&wlt)!=registeredWallets_.end());
   return KEY_IN_MAP(&wlt, registeredWallets_);
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::scrAddrIsRegistered(HashString scraddr)
{
   //return (registeredScrAddrMap_.find(scraddr)!=registeredScrAddrMap_.end());
   return KEY_IN_MAP(scraddr, registeredScrAddrMap_);
}



/////////////////////////////////////////////////////////////////////////////
// first scans the blockchain and collects the registered tx (all tx relevant
// to your wallet), then does a heartier scan of that subset to actually
// collect balance information, utxo sets
// 
// This method is now a hybrid of the original, Blockchain-in-RAM code,
// and the new mmap()-based blockchain operations.  The initial blockchain
// scan will look for wallet-relevant transactions, and keep track of what 
// blocks still need to be scanned given the registered wallets
// 
// Therefore, when we scan, we will first scan the registered tx list,
// then any raw blocks that haven't been filtered yet, then all the 
// zero-conf tx list.
//
// If the wallet contains any addresses that are not part of the prefiltered
// tx-hash-list, then the entire blockchain will have to be rescanned, anyway.
// It doesn't take any less time to search for one address than it does 
// all of them.
//
//
//  Some new notes on this method ...
//     We will ONLY scan transactions from the registeredTxList_
//
//     Therefore, we need to make sure that registeredTxList_ is
//     completely up-to-date FIRST. 
//
//     Then we can sort it and scanTx all of them with the wallet.
//
//     We need to scan from blocks X-->Y.  Assume X is 1000 and Y is 2000
//     If allScannedUpToBlk_==1500:
//
//     registeredScrAddrScan from 1500-->2000
//     sort registered list
//     scanTx all tx in registered list between 1000 and 2000
void BlockDataManager_LevelDB::scanBlockchainForTx(BtcWallet & myWallet,
                                                   uint32_t startBlknum,
                                                   uint32_t endBlknum,
                                                   bool fetchFirst)
{
   SCOPED_TIMER("scanBlockchainForTx");

   // TODO:  We should implement selective fetching!  (i.e. only fetch
   //        and register scraddr data that is between those two blocks).
   //        At the moment, it is 
   if(fetchFirst && DBUtils.getArmoryDbType()!=ARMORY_DB_BARE)
      fetchAllRegisteredScrAddrData(myWallet);

   // The BDM knows the highest block to which ALL CURRENT REGISTERED ADDRESSES
   // are up-to-date in the registeredTxList_ list.  
   // If this wallet is not registered, it needs to be, before we start
   if(!walletIsRegistered(myWallet))
      registerWallet( &myWallet );

   
   // Check whether we can get everything we need from the registered tx list
   endBlknum = min(endBlknum, blockchain_.top().getBlockHeight()+1);
   uint32_t numRescan = numBlocksToRescan(myWallet, endBlknum);


   // This is the part that might take a while...
   //applyBlockRangeToDB(allScannedUpToBlk_, endBlknum);
   scanDBForRegisteredTx(allScannedUpToBlk_, endBlknum);

   allScannedUpToBlk_ = endBlknum;
   updateRegisteredScrAddrs(endBlknum);


   // *********************************************************************** //
   // Finally, walk through all the registered tx
   scanRegisteredTxForWallet(myWallet, startBlknum, endBlknum);


   // I think these lines of code where causing the serious peformance issues
   // so they were commented out and don't appear to be needed
   // if(zcEnabled_)
   //    rescanWalletZeroConf(myWallet);
}


/////////////////////////////////////////////////////////////////////////////
// This used to be "rescanBlocks", but now "scanning" has been replaced by
// "reapplying" the blockdata to the databases.  Basically assumes that only
// raw blockdata is stored in the DB with no SSH objects.  This goes through
// and processes every Tx, creating new SSHs if not there, and creating and
// marking-spent new TxOuts.  
void BlockDataManager_LevelDB::applyBlockRangeToDB(uint32_t blk0, uint32_t blk1)
{
   SCOPED_TIMER("applyBlockRangeToDB");

   blk1 = min(blk1, blockchain_.top().getBlockHeight()+1);

   BinaryData startKey = DBUtils.getBlkDataKey(blk0, 0);
   BinaryData endKey   = DBUtils.getBlkDataKey(blk1, 0);

   LDBIter ldbIter = iface_->getIterator(BLKDATA);
   ldbIter.seekTo(startKey);

   // Start scanning and timer
   //bool doBatches = (blk1-blk0 > NUM_BLKS_BATCH_THRESH);
   BlockWriteBatcher blockWrites(iface_);

   do
   {
      StoredHeader sbh;
      iface_->readStoredBlockAtIter(ldbIter, sbh);
      const uint32_t hgt = sbh.blockHeight_;
      const uint8_t dup = sbh.duplicateID_;
      if(blk0 > hgt || hgt >= blk1)
         break;

      if(hgt%2500 == 2499)
         LOGWARN << "Finished applying blocks up to " << (hgt+1);

      if(dup != iface_->getValidDupIDForHeight(hgt))
         continue;

      // IS THIS COMMENT STILL RELEVANT? ~CS
      // Ugh!  Design inefficiency: this loop and applyToBlockDB both use
      // the same iterator, which means that applyBlockToDB will usually 
      // leave us with the iterator in a different place than we started.
      // I'm not clear how inefficient it is to keep re-seeking (given that
      // there's a lot of caching going on under-the-hood).  It may be better
      // to have each method create its own iterator... TODO:  profile/test
      // this idea.  For now we will just save the current DB key, and 
      // re-seek to it afterwards.
      blockWrites.applyBlockToDB(hgt, dup); 

      bytesReadSoFar_ += sbh.numBytes_;

      // Will write out about once every 5 sec
      writeProgressFile(DB_BUILD_APPLY, blkProgressFile_, "applyBlockRangeToDB");

   } while(iface_->advanceToNextBlock(ldbIter, false));

}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::writeProgressFile(DB_BUILD_PHASE phase,
                                                    string bfile,
                                                    string timerName)
{
   // Nothing to write if we don't even have a home dir
   if(armoryHomeDir_.size() == 0 || bfile.size() == 0)
      return;

   time_t currTime;
   time(&currTime);
   int32_t diffTime = (int32_t)currTime - (int32_t)progressTimer_;

   // Don't write out more than once every 5 sec
   if(diffTime < 5)
      return;
   else
      progressTimer_ = (uint32_t)currTime;

   uint64_t offset;
   uint32_t height, blkfile;

   if(phase==DB_BUILD_ADD_RAW)
   {
      height  = startRawBlkHgt_;
      blkfile = startRawBlkFile_;
      offset  = startRawOffset_;
   }
   else if(phase==DB_BUILD_SCAN)
   {
      height  = startScanHgt_;
      blkfile = startScanBlkFile_;
      offset  = startScanOffset_;
   }
   else if(phase==DB_BUILD_APPLY)
   {
      height  = startApplyHgt_;
      blkfile = startApplyBlkFile_;
      offset  = startApplyOffset_;
   }
   else
   {
      LOGERR << "What the heck build phase are we in: " << (uint32_t)phase;
      return;
   }

   uint64_t startAtByte = 0;
   if(height!=0)
      startAtByte = blkFileCumul_[blkfile] + offset;
      
   ofstream topblks(OS_TranslatePath(bfile.c_str()), ios::app);
   double t = TIMER_READ_SEC(timerName);
   topblks << (uint32_t)phase << " "
           << startAtByte << " " 
           << bytesReadSoFar_ << " " 
           << totalBlockchainBytes_ << " " 
           << t << endl;
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::pprintRegisteredWallets(void)
{
   set<BtcWallet*>::iterator iter;
   for(iter  = registeredWallets_.begin(); 
       iter != registeredWallets_.end(); 
       iter++)
   {
      cout << "Wallet:";
      cout << "\tBalance: " << (*iter)->getFullBalance();
      cout << "\tNAddr:   " << (*iter)->getNumScrAddr();
      cout << "\tNTxio:   " << (*iter)->getTxIOMap().size();
      cout << "\tNLedg:   " << (*iter)->getTxLedger().size();
      cout << "\tNZC:     " << (*iter)->getZeroConfLedger().size() << endl;      
   }
}

/////////////////////////////////////////////////////////////////////////////
BtcWallet* BlockDataManager_LevelDB::createNewWallet(void)
{
   BtcWallet* newWlt = new BtcWallet(this);
   registeredWallets_.insert(newWlt);  
   return newWlt;
}


/////////////////////////////////////////////////////////////////////////////
// This assumes that registeredTxList_ has already been populated from 
// the initial blockchain scan.  The blockchain contains millions of tx,
// but this list will at least 3 orders of magnitude smaller
void BlockDataManager_LevelDB::scanRegisteredTxForWallet( BtcWallet & wlt,
                                                           uint32_t blkStart,
                                                           uint32_t blkEnd)
{
   SCOPED_TIMER("scanRegisteredTxForWallet");

   // Make sure RegisteredTx objects have correct data, then sort.
   // TODO:  Why did I not need this with the MMAP blockchain?  Somehow
   //        I was able to sort correctly without this step, before...?
   list<RegisteredTx>::iterator txIter;
   for(txIter  = registeredTxList_.begin();
       txIter != registeredTxList_.end();
       txIter++)
   {
      if(txIter->txIndex_ > UINT32_MAX/2)
      {
         // The RegisteredTx was created before the chain was organized
         txIter->blkNum_ = txIter->txRefObj_.getBlockHeight();
         txIter->txIndex_ = txIter->txRefObj_.getBlockTxIndex();
      }
   }
   registeredTxList_.sort();

   ///// LOOP OVER ALL RELEVANT TX ////
   for(txIter  = registeredTxList_.begin();
       txIter != registeredTxList_.end();
       txIter++)
   {
      // Pull the tx from disk and check it for the supplied wallet
      Tx theTx = txIter->getTxCopy();
      if( !theTx.isInitialized() )
      {
         LOGWARN << "***WARNING: How did we get a NULL tx?";
         continue;
      }

      
      const BlockHeader* bhptr;
      try
      {
         bhptr = &blockchain_.getHeaderPtrForTx(theTx);
      }
      catch (...)
      {
         // This condition happens on invalid Tx (like invalid P2Pool coinbases)
         // or when the blockheader isn't on the main branch
         if( bhptr==NULL )
            continue;
      }

      uint32_t thisBlk = bhptr->getBlockHeight();
      if(thisBlk < blkStart  ||  thisBlk >= blkEnd)
         continue;

      if( !isTxFinal(theTx) )
         continue;

      // If we made it here, we want to scan this tx!
      wlt.scanTx(theTx, txIter->txIndex_, bhptr->getTimestamp(), thisBlk);
   }
 
   wlt.sortLedger();


   // We should clean up any dangling TxIOs in the wallet then rescan
   if(zcEnabled_)
      rescanWalletZeroConf(wlt);

}


/////////////////////////////////////////////////////////////////////////////
uint64_t BlockDataManager_LevelDB::getDBBalanceForHash160(   
                                                      BinaryDataRef addr160)
{
   StoredScriptHistory ssh;

   iface_->getStoredScriptHistory(ssh, HASH160PREFIX + addr160);
   if(!ssh.isInitialized())
      return 0;

   return ssh.getScriptBalance();
}

/////////////////////////////////////////////////////////////////////////////
uint64_t BlockDataManager_LevelDB::getDBReceivedForHash160(   
                                                      BinaryDataRef addr160)
{
   StoredScriptHistory ssh;

   iface_->getStoredScriptHistory(ssh, HASH160PREFIX + addr160);
   if(!ssh.isInitialized())
      return 0;

   return ssh.getScriptReceived();
}

/////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> BlockDataManager_LevelDB::getUTXOVectForHash160(
                                                      BinaryDataRef addr160)
{
   StoredScriptHistory ssh;
   vector<UnspentTxOut> outVect(0);

   iface_->getStoredScriptHistory(ssh, HASH160PREFIX + addr160);
   if(!ssh.isInitialized())
      return outVect;


   size_t numTxo = (size_t)ssh.totalTxioCount_;
   outVect.reserve(numTxo);
   map<BinaryData, StoredSubHistory>::iterator iterSubSSH;
   map<BinaryData, TxIOPair>::iterator iterTxio;
   for(iterSubSSH  = ssh.subHistMap_.begin(); 
       iterSubSSH != ssh.subHistMap_.end(); 
       iterSubSSH++)
   {
      StoredSubHistory & subSSH = iterSubSSH->second;
      for(iterTxio  = subSSH.txioSet_.begin(); 
          iterTxio != subSSH.txioSet_.end(); 
          iterTxio++)
      {
         TxIOPair & txio = iterTxio->second;
         StoredTx stx;
         BinaryData txKey = txio.getTxRefOfOutput().getDBKey();
         uint16_t txoIdx = txio.getIndexOfOutput();
         iface_->getStoredTx(stx, txKey);

         StoredTxOut & stxo = stx.stxoMap_[txoIdx];
         if(stxo.isSpent())
            continue;
   
         UnspentTxOut utxo(stx.thisHash_, 
                           txoIdx,
                           stx.blockHeight_,
                           txio.getValue(),
                           stx.stxoMap_[txoIdx].getScriptRef());
         
         outVect.push_back(utxo);
      }
   }

   return outVect;

}

/////////////////////////////////////////////////////////////////////////////
vector<TxIOPair> BlockDataManager_LevelDB::getHistoryForScrAddr(
                                                BinaryDataRef uniqKey,
                                                bool withMultisig)
{
   StoredScriptHistory ssh;
   iface_->getStoredScriptHistory(ssh, uniqKey);

   map<BinaryData, RegisteredScrAddr>::iterator iter;
   iter = registeredScrAddrMap_.find(uniqKey);
   if(ITER_IN_MAP(iter, registeredScrAddrMap_))
   {
      if (ssh.alreadyScannedUpToBlk_ == 123456789)
         iter->second.alreadyScannedUpToBlk_ = getAppliedToHeightInDB();
      else
         iter->second.alreadyScannedUpToBlk_ = ssh.alreadyScannedUpToBlk_;
   }
   
   vector<TxIOPair> outVect(0);
   if(!ssh.isInitialized())
      return outVect;

   outVect.reserve((size_t)ssh.totalTxioCount_);
   map<BinaryData, StoredSubHistory>::iterator iterSubSSH;
   map<BinaryData, TxIOPair>::iterator iterTxio;
   for(iterSubSSH  = ssh.subHistMap_.begin();
       iterSubSSH != ssh.subHistMap_.end(); 
       iterSubSSH++)
   {
      StoredSubHistory & subssh = iterSubSSH->second;
      for(iterTxio  = subssh.txioSet_.begin();
          iterTxio != subssh.txioSet_.end(); 
          iterTxio++)
      {
         TxIOPair & txio = iterTxio->second;
         if(withMultisig || !txio.isMultisig())
            outVect.push_back(txio);   
      }
   }
   
   return outVect;
}


/////////////////////////////////////////////////////////////////////////////
/*  This is not currently being used, and is actually likely to change 
 *  a bit before it is needed, so I have just disabled it.
vector<TxRef*> BlockDataManager_LevelDB::findAllNonStdTx(void)
{
   PDEBUG("Finding all non-std tx");
   vector<TxRef*> txVectOut(0);
   uint32_t nHeaders = headersByHeight_.size();

   ///// LOOP OVER ALL HEADERS ////
   for(uint32_t h=0; h<nHeaders; h++)
   {
      BlockHeader & bhr = *(headersByHeight_[h]);
      vector<TxRef*> const & txlist = bhr.getTxRefPtrList();

      ///// LOOP OVER ALL TX /////
      for(uint32_t itx=0; itx<txlist.size(); itx++)
      {
         TxRef & tx = *(txlist[itx]);

         ///// LOOP OVER ALL TXIN IN BLOCK /////
         for(uint32_t iin=0; iin<tx.getNumTxIn(); iin++)
         {
            TxIn txin = tx.getTxInCopy(iin);
            if(txin.getScriptType() == TXIN_SCRIPT_UNKNOWN)
            {
               txVectOut.push_back(&tx);
               cout << "Attempting to interpret TXIN script:" << endl;
               cout << "Block: " << h << " Tx: " << itx << endl;
               cout << "PrevOut: " << txin.getOutPoint().getTxHash().toHexStr()
                    << ", "        << txin.getOutPoint().getTxOutIndex() << endl;
               cout << "Raw Script: " << txin.getScript().toHexStr() << endl;
               cout << "Raw Tx: " << txin.getParentTxPtr()->serialize().toHexStr() << endl;
               cout << "pprint: " << endl;
               BtcUtils::pprintScript(txin.getScript());
               cout << endl;
            }
         }

         ///// LOOP OVER ALL TXOUT IN BLOCK /////
         for(uint32_t iout=0; iout<tx.getNumTxOut(); iout++)
         {
            
            TxOut txout = tx.getTxOutCopy(iout);
            if(txout.getScriptType() == TXOUT_SCRIPT_UNKNOWN)
            {
               txVectOut.push_back(&tx);               
               cout << "Attempting to interpret TXOUT script:" << endl;
               cout << "Block: " << h << " Tx: " << itx << endl;
               cout << "ThisOut: " << txout.getParentTxPtr()->getThisHash().toHexStr() 
                    << ", "        << txout.getIndex() << endl;
               cout << "Raw Script: " << txout.getScript().toHexStr() << endl;
               cout << "Raw Tx: " << txout.getParentTxPtr()->serialize().toHexStr() << endl;
               cout << "pprint: " << endl;
               BtcUtils::pprintScript(txout.getScript());
               cout << endl;
            }

         }
      }
   }

   PDEBUG("Done finding all non-std tx");
   return txVectOut;
}
*/

static bool scanFor(std::istream &in, const uint8_t * bytes, const unsigned len)
{
   unsigned matched=0; // how many bytes we've matched so far
   std::vector<uint8_t> ahead(len); // the bytes matched
   
   in.read((char*)&ahead.front(), len);
   unsigned count = in.gcount();
   if (count < len) return false;
   
   unsigned offset=0; // the index mod len which we're in ahead
   
   do
   {
      bool found=true;
      for (unsigned i=0; i < len; i++)
      {
         if (ahead[(i+offset)%len] != bytes[i])
         {
            found=false;
            break;
         }
      }
      if (found)
         return true;
      
      ahead[offset++%len] = in.get();
      
   } while (!in.eof());
   return false;
}

/////////////////////////////////////////////////////////////////////////////
// With the LevelDB database integration, we now index all blockchain data
// by block height and index (tx index in block, txout index in tx).  The
// only way to actually do that is to process the headers first, so that 
// when we do read the block data the first time, we know how to put it
// into the DB.  
//
// For now, we have no problem holding all the headers in RAM and organizing
// them all in one shot.  But RAM-limited devices (say, if this was going 
// to be ported to Android), may not be able to do even that, and may have
// to read and process the headers in batches.  
bool BlockDataManager_LevelDB::extractHeadersInBlkFile(uint32_t fnum, 
                                                       uint64_t startOffset)
{
   SCOPED_TIMER("extractHeadersInBlkFile");
   
   missingBlockHeaderHashes_.clear();
   
   string filename = blkFileList_[fnum];
   uint64_t filesize = BtcUtils::GetFileSize(filename);
   if(filesize == FILE_DOES_NOT_EXIST)
   {
      LOGERR << "File does not exist: " << filename.c_str();
      return false;
   }

   // This will trigger if this is the last blk file and no new blocks
   if(filesize < startOffset)
      return true;
   

   ifstream is(filename.c_str(), ios::in | ios::binary);
   BinaryData fileMagic(4);
   is.read((char*)(fileMagic.getPtr()), 4);
   is.seekg(startOffset, ios::beg);

   if( !(fileMagic == MagicBytes_ ) )
   {
      LOGERR << "Block file is the wrong network!  MagicBytes: "
             << fileMagic.toHexStr().c_str();
      return false;
   }


   endOfLastBlockByte_ = startOffset;

   uint32_t const HEAD_AND_NTX_SZ = HEADER_SIZE + 10; // enough
   BinaryData magic(4), szstr(4), rawHead(HEAD_AND_NTX_SZ);
   while(!is.eof())
   {
      is.read((char*)magic.getPtr(), 4);
      if (is.eof())
         break;
         
      if(magic!=MagicBytes_)
      {
         // I have to start scanning for MagicBytes
         
         BinaryData nulls( (const uint8_t*)"\0\0\0\0", 4);
         
         if (magic == nulls)
            break;
         
         LOGERR << "Did not find block header in expected location, "
            "possible corrupt data, searching for next block header.";
         
         if (!scanFor(is, MagicBytes_.getPtr(), MagicBytes_.getSize()))
         {
            LOGERR << "No more blocks found in file " << filename;
            break;
         }
         
         LOGERR << "Next block header found at offset " << uint64_t(is.tellg())-4;
      }
      
      is.read((char*)szstr.getPtr(), 4);
      uint32_t nextBlkSize = READ_UINT32_LE(szstr.getPtr());
      if(is.eof()) break;

      is.read((char*)rawHead.getPtr(), HEAD_AND_NTX_SZ); // plus #tx var_int
      if(is.eof()) break;

      // Create a reader for the entire block, grab header, skip rest
      pair<HashString, BlockHeader>                      bhInputPair;
      BlockHeader block;
      BinaryRefReader brr(rawHead);
      block.unserialize(brr);
      HashString blockhash = block.getThisHash();
      
      uint32_t nTx = (uint32_t)brr.get_var_int();
      BlockHeader& addedBlock = blockchain_.addBlock(blockhash, block);

      // is there any reason I can't just do this to "block"?
      addedBlock.setBlockFile(filename);
      addedBlock.setBlockFileNum(fnum);
      addedBlock.setBlockFileOffset(endOfLastBlockByte_);
      addedBlock.setNumTx(nTx);
      addedBlock.setBlockSize(nextBlkSize);
      
      endOfLastBlockByte_ += nextBlkSize+8;
      is.seekg(nextBlkSize - HEAD_AND_NTX_SZ, ios::cur);
      
      // now check if the previous hash is in there
      // (unless the previous hash is 0)
      // most should be there, so search the map before checking for 0
      if (!blockchain_.hasHeaderWithHash(addedBlock.getPrevHash())
         && BtcUtils::EmptyHash_ != addedBlock.getPrevHash()
         )
      {
         LOGWARN << "Block header " << addedBlock.getThisHash().toHexStr()
            << " refers to missing previous hash "
            << addedBlock.getPrevHash().toHexStr();
            
         missingBlockHeaderHashes_.push_back(addedBlock.getPrevHash());
      }
      
   }

   is.close();
   return true;
}


/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_LevelDB::detectAllBlkFiles(void)
{
   SCOPED_TIMER("detectAllBlkFiles");

   // Next thing we need to do is find all the blk000X.dat files.
   // BtcUtils::GetFileSize uses only ifstreams, and thus should be
   // able to determine if a file exists in an OS-independent way.
   numBlkFiles_=0;
   totalBlockchainBytes_ = 0;
   blkFileList_.clear();
   blkFileSizes_.clear();
   blkFileCumul_.clear();
   while(numBlkFiles_ < UINT16_MAX)
   {
      string path = BtcUtils::getBlkFilename(blkFileDir_, numBlkFiles_);
      uint64_t filesize = BtcUtils::GetFileSize(path);
      if(filesize == FILE_DOES_NOT_EXIST)
         break;

      numBlkFiles_++;
      blkFileList_.push_back(string(path));
      blkFileSizes_.push_back(filesize);
      blkFileCumul_.push_back(totalBlockchainBytes_);
      totalBlockchainBytes_ += filesize;
   }

   if(numBlkFiles_==UINT16_MAX)
   {
      LOGERR << "Error finding blockchain files (blkXXXX.dat)";
      return 0;
   }
   return numBlkFiles_;
}


/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::processNewHeadersInBlkFiles(uint32_t fnumStart,
                                                           uint64_t startOffset)
{
   SCOPED_TIMER("processNewHeadersInBlkFiles");

   detectAllBlkFiles();
   
   // In first file, start at supplied offset;  start at beginning for others
   for(uint32_t fnum=fnumStart; fnum<numBlkFiles_; fnum++)
   {
      uint64_t useOffset = (fnum==fnumStart ? startOffset : 0);
      extractHeadersInBlkFile(fnum, useOffset);
   }

   bool prevTopBlkStillValid=false;
   
   try
   {
      // This will return true unless genesis block was reorg'd...
      prevTopBlkStillValid = blockchain_.forceOrganize().prevTopBlockStillValid;
      if(!prevTopBlkStillValid)
      {
         LOGERR << "Organize chain indicated reorg in process all headers!";
         LOGERR << "Did we shut down last time on an orphan block?";
      }
   }
   catch (std::exception &e)
   {
      LOGERR << e.what();
   }

   {
      InterfaceToLDB::Batch batch(iface_, HEADERS);
         
      for(unsigned i=0; i < blockchain_.numHeaders(); i++)
      {
         BlockHeader &block = blockchain_.getHeaderByHeight(i);
         StoredHeader sbh;
         sbh.createFromBlockHeader(block);
         uint8_t dup = iface_->putBareHeader(sbh);
         block.setDuplicateID(dup);  // make sure headerMap_ and DB agree
      }
   }

   return prevTopBlkStillValid;


}

////////////////////////////////////////////////////////////////////////////////
// We assume that all the addresses we care about have been registered with
// the BDM.  Before, the BDM we would rescan the blockchain and use the method
// isMineBulkFilter() to extract all "RegisteredTx" which are all tx relevant
// to the list of "RegisteredScrAddr" objects.  Now, the DB defaults to super-
// node mode and tracks all that for us on disk.  So when we start up, rather
// than having to search the blockchain, we just look the StoredScriptHistory
// list for each of our "RegisteredScrAddr" objects, and then pull all the 
// relevant tx from the database.  After that, the BDM operates 99% identically
// to before.  We just didn't have to do a full scan to fill the RegTx list
//
// In the future, we will use the StoredScriptHistory objects to directly fill
// the TxIOPair map -- all the data is tracked by the DB and we could pull it
// directly.  But that would require reorganizing a ton of BDM code, and may
// be difficult to guarantee that all the previous functionality was there and
// working.  This way, all of our previously-tested code remains mostly 
// untouched
void BlockDataManager_LevelDB::fetchAllRegisteredScrAddrData(void)
{
   fetchAllRegisteredScrAddrData(registeredScrAddrMap_);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::fetchAllRegisteredScrAddrData(
                                                       BtcWallet & myWallet)
{
   SCOPED_TIMER("fetchAllRegisteredScrAddrData");

   uint32_t numAddr = myWallet.getNumScrAddr();
   for(uint32_t s=0; s<numAddr; s++)
   {
      ScrAddrObj & scrAddrObj = myWallet.getScrAddrObjByIndex(s);
      fetchAllRegisteredScrAddrData(scrAddrObj.getScrAddr());
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::fetchAllRegisteredScrAddrData(
                           map<BinaryData, RegisteredScrAddr> & addrMap)
{
   SCOPED_TIMER("fetchAllRegisteredScrAddrData");


   map<BinaryData, RegisteredScrAddr>::iterator iter;
   for(iter  = addrMap.begin(); iter != addrMap.end(); iter++)
      fetchAllRegisteredScrAddrData(iter->second.uniqueKey_);
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::fetchAllRegisteredScrAddrData(
                                             BinaryData const & scrAddr)
{
   vector<TxIOPair> hist = getHistoryForScrAddr(scrAddr);

   BinaryData txKey;
   StoredTx stx;
   TxRef txref;
   RegisteredTx regTx;
   for(uint32_t i=0; i<hist.size(); i++)
   {
      // Fetch the full tx of the arriving coins
      txref = hist[i].getTxRefOfOutput();
      iface_->getStoredTx(stx, txref.getDBKey());
      regTx = RegisteredTx(txref, stx.thisHash_, stx.blockHeight_, stx.txIndex_);
      insertRegisteredTxIfNew(regTx);
      registeredOutPoints_.insert(hist[i].getOutPoint());

      txref = hist[i].getTxRefOfInput();
      if(txref.isNull())
         continue;

      // If the coins were spent, also fetch the tx in which they were spent
      iface_->getStoredTx(stx, txref.getDBKey());
      regTx = RegisteredTx(txref, stx.thisHash_, stx.blockHeight_, stx.txIndex_);
      insertRegisteredTxIfNew(regTx);
   }
}



/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::destroyAndResetDatabases(void)
{
   if(iface_ != NULL)
   {
      LOGWARN << "Destroying databases;  will need to be rebuilt";
      iface_->destroyAndResetDatabases();
      return;
   }
   LOGERR << "Attempted to destroy databases, but no DB interface set";
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doRebuildDatabases(void)
{
   LOGINFO << "Executing: doRebuildDatabases";
   buildAndScanDatabases(true,   true,   true,   false);
   //                    Rescan  Rebuild !Fetch  Initial                    
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doFullRescanRegardlessOfSync(void)
{
   LOGINFO << "Executing: doFullRescanRegardlessOfSync";
   buildAndScanDatabases(true,   false,  true,   false);
   //                    Rescan  Rebuild !Fetch  Initial                    
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doSyncIfNeeded(void)
{
   LOGINFO << "Executing: doSyncIfNeeded";
   buildAndScanDatabases(false,  false,  true,   false);
   //                    Rescan  Rebuild !Fetch  Initial                    
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doInitialSyncOnLoad(void)
{
   LOGINFO << "Executing: doInitialSyncOnLoad";
   buildAndScanDatabases(false,  false,  false,  true);
   //                    Rescan  Rebuild !Fetch  Initial                    
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doInitialSyncOnLoad_Rescan(void)
{
   LOGINFO << "Executing: doInitialSyncOnLoad_Rescan";
   buildAndScanDatabases(true,   false,  false,  true);
   //                    Rescan  Rebuild !Fetch  Initial                    
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doInitialSyncOnLoad_Rebuild(void)
{
   LOGINFO << "Executing: doInitialSyncOnLoad_Rebuild";
   buildAndScanDatabases(false,  true,   true,   true);
   //                    Rescan  Rebuild !Fetch  Initial                    
}

/////////////////////////////////////////////////////////////////////////////
// This used to be "parseEntireBlockchain()", but changed because it will 
// only be used when rebuilding the DB from scratch (hopefully).
//
// The default behavior of this method is to do the minimal amount of work
// neceesary to get sync'd.  It does this by assuming all database data is 
// correct.  We can choose to rebuild/recalculate.  "forceRescan" and
// "skipFetch" are slightly different:  forceRescan will guarantee that
// we always start scanning from block 0.  skipFetch means we won't pull
// any data out of the database when this is called, but if all our 
// wallets are already synchronized, we won't bother rescanning
void BlockDataManager_LevelDB::buildAndScanDatabases(
                                             bool forceRescan, 
                                             bool forceRebuild,
                                             bool skipFetch,
                                             bool initialLoad)
{
   missingBlockHashes_.clear();
   
   SCOPED_TIMER("buildAndScanDatabases");
   LOGINFO << "Number of registered addr: " << registeredScrAddrMap_.size();

   
   
   // Will use this updating the GUI with progress bar
   time_t t;
   time(&t);
   progressTimer_ = (uint32_t)t;

   if(!iface_->databasesAreOpen())
      initializeDBInterface(DBUtils.getArmoryDbType(), DBUtils.getDbPruneType());
      
   LOGDEBUG << "Called build&scan with ("
            << (forceRescan ? 1 : 0) << ","
            << (forceRebuild ? 1 : 0) << ","
            << (skipFetch ? 1 : 0) << ","
            << (initialLoad ? 1 : 0) << ")";


   // This will figure out where we should start reading headers, blocks,
   // and where we should start applying or scanning
   detectCurrentSyncState(forceRebuild, initialLoad);

   // If we're going to rebuild, might as well destroy the DB for good measure
   if(forceRebuild || (startHeaderHgt_==0 && startRawBlkHgt_==0))
   {
      LOGINFO << "Clearing databases for clean build";
      forceRebuild = true;
      forceRescan = true;
      skipFetch = true;
      destroyAndResetDatabases();
   }

   // If we're going to be rescanning, reset the wallets
   if(forceRescan)
   {
      LOGINFO << "Resetting wallets for rescan";
      skipFetch = true;
      deleteHistories();
      resetRegisteredWallets();
   }

   // If no rescan is forced, grab the SSH entries from the DB
   if(!skipFetch && initialLoad)
   {
      LOGINFO << "Fetching stored script histories from DB";
      fetchAllRegisteredScrAddrData();
   }



   // Remove this file

#ifndef _MSC_VER
   if(BtcUtils::GetFileSize(blkProgressFile_) != FILE_DOES_NOT_EXIST)
      remove(blkProgressFile_.c_str());
   if(BtcUtils::GetFileSize(abortLoadFile_) != FILE_DOES_NOT_EXIST)
      remove(abortLoadFile_.c_str());
#else
   if(BtcUtils::GetFileSize(blkProgressFile_) != FILE_DOES_NOT_EXIST)
      _wunlink(OS_TranslatePath(blkProgressFile_).c_str());
   if(BtcUtils::GetFileSize(abortLoadFile_) != FILE_DOES_NOT_EXIST)
      _wunlink(OS_TranslatePath(abortLoadFile_).c_str());
#endif
   
   if(!initialLoad)
      detectAllBlkFiles(); // only need to spend time on this on the first call

   if(numBlkFiles_==0)
   {
      LOGERR << "No blockfiles could be found!  Aborting...";
      return;
   }

   if(GenesisHash_.getSize() == 0)
   {
      LOGERR << "***ERROR: Set net params before loading blockchain!";
      return;
   }


   /////////////////////////////////////////////////////////////////////////////
   // New with LevelDB:  must read and organize headers before handling the
   // full blockchain data.  We need to figure out the longest chain and write
   // the headers to the DB before actually processing any block data.  
   if(initialLoad || forceRebuild)
   {
      LOGINFO << "Reading all headers and building chain...";
      processNewHeadersInBlkFiles(startHeaderBlkFile_, startHeaderOffset_);
   }

   LOGINFO << "Total number of blk*.dat files: " << numBlkFiles_;
   LOGINFO << "Total number of blocks found:   " << blockchain_.top().getBlockHeight() + 1;

   /////////////////////////////////////////////////////////////////////////////
   // Now we start the meat of this process...

   /////////////////////////////////////////////////////////////////////////////
   // Add the raw blocks from the blk*.dat files into the DB
   blocksReadSoFar_ = 0;
   bytesReadSoFar_ = 0;

   if(initialLoad || forceRebuild)
   {
      LOGINFO << "Getting latest blocks from blk*.dat files";
      LOGINFO << "Total blockchain bytes: " 
              << BtcUtils::numToStrWCommas(totalBlockchainBytes_);
      TIMER_START("dumpRawBlocksToDB");
      for(uint32_t fnum=startRawBlkFile_; fnum<numBlkFiles_; fnum++)
      {
         string blkfile = blkFileList_[fnum];
         LOGINFO << "Parsing blockchain file: " << blkfile.c_str();
   
         // The supplied offset only applies to the first blockfile we're reading.
         // After that, the offset is always zero
         uint32_t startOffset = 0;
         if(fnum==startRawBlkFile_)
            startOffset = (uint32_t)startRawOffset_;
      
         readRawBlocksInFile(fnum, startOffset);
      }
      TIMER_STOP("dumpRawBlocksToDB");
   }

   double timeElapsed = TIMER_READ_SEC("dumpRawBlocksToDB");
   LOGINFO << "Processed " << blocksReadSoFar_ << " raw blocks DB (" 
           <<  (int)timeElapsed << " seconds)";

   // Now start scanning the raw blocks
   if(registeredScrAddrMap_.size() == -1)
   {
      LOGWARN << "No addresses are registered with the BDM, so there's no";
      LOGWARN << "point in doing a blockchain scan yet.";
   }
   else if(DBUtils.getArmoryDbType() != ARMORY_DB_SUPER)
   {
      // We don't do this in SUPER mode because there is no rescanning 
      // For progress bar purposes, let's find the blkfile location of scanStart
      if(forceRescan)
      {
         startScanHgt_ = 0;
         startScanBlkFile_ = 0;
         startScanOffset_ = 0;
      }
      else
      {
         startScanHgt_     = evalLowestBlockNextScan();
         // Rewind 4 days, to rescan recent history in case problem last shutdown
         startScanHgt_ = (startScanHgt_>576 ? startScanHgt_-576 : 0);
         pair<uint32_t, uint32_t> blkLoc = findFileAndOffsetForHgt(startScanHgt_);
         startScanBlkFile_ = blkLoc.first;
         startScanOffset_  = blkLoc.second;
      }

      LOGINFO << "Starting scan from block height: " << startScanHgt_;
      scanDBForRegisteredTx(startScanHgt_);
      LOGINFO << "Finished blockchain scan in " 
              << TIMER_READ_SEC("ScanBlockchain") << " seconds";
   }

   // If bare mode, we don't do
   if(DBUtils.getArmoryDbType() != ARMORY_DB_BARE)
   { 
      // In any DB type other than bare, we will be walking through the blocks
      // and updating the spentness fields and script histories
      applyBlockRangeToDB(startApplyHgt_, blockchain_.top().getBlockHeight()+1);
   }

   // We need to maintain the physical size of all blkXXXX.dat files together
   totalBlockchainBytes_ = bytesReadSoFar_;

   // Update registered address list so we know what's already been scanned
   lastTopBlock_ = blockchain_.top().getBlockHeight() + 1;
   allScannedUpToBlk_ = lastTopBlock_;
   updateRegisteredScrAddrs(lastTopBlock_);

   // Since loading takes so long, there's a good chance that new block data
   // came in... let's get it.
   readBlkFileUpdate();
   isInitialized_ = true;
   purgeZeroConfPool();

   #ifdef _DEBUG
      UniversalTimer::instance().printCSV(string("timings.csv"));
      #ifdef _DEBUG_FULL_VERBOSE
         UniversalTimer::instance().printCSV(cout,true);
      #endif
   #endif

   /*
   for(iter  = registeredScrAddrMap_.begin();
       iter != registeredScrAddrMap_.end();
       iter ++)
      LOGINFO << "ScrAddr: " << iter->second.uniqueKey_.toHexStr().c_str()
               << " " << iter->second.alreadyScannedUpToBlk_;
   */

}

// search for the next byte in bsb that looks like it could be a block
bool BlockDataManager_LevelDB::scanForMagicBytes(BinaryStreamBuffer& bsb, uint32_t *bytesSkipped) const
{
   BinaryData firstFour(4);
   if (bytesSkipped) *bytesSkipped=0;
   
   do
   {
      while (bsb.reader().getSizeRemaining() >= 4)
      {
         bsb.reader().get_BinaryData(firstFour, 4);
         if(firstFour==MagicBytes_)
         {
            bsb.reader().rewind(4);
            return true;
         }
         // try again at the very next byte
         if (bytesSkipped) (*bytesSkipped)++;
         bsb.reader().rewind(3);
      }
      
   } while (bsb.streamPull());
   
   return false;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::readRawBlocksInFile(uint32_t fnum, uint32_t foffset)
{
   string blkfile = blkFileList_[fnum];
   uint64_t filesize = BtcUtils::GetFileSize(blkfile);
   string fsizestr = BtcUtils::numToStrWCommas(filesize);
   LOGINFO << blkfile.c_str() << " is " << fsizestr.c_str() << " bytes";

   // Open the file, and check the magic bytes on the first block
   ifstream is(blkfile.c_str(), ios::in | ios::binary);
   BinaryData fileMagic(4);
   is.read((char*)(fileMagic.getPtr()), 4);
   if( !(fileMagic == MagicBytes_ ) )
   {
      LOGERR << "Block file is the wrong network!  MagicBytes: "
             << fileMagic.toHexStr().c_str();
   }

   // Seek to the supplied offset
   is.seekg(foffset, ios::beg);
   
   uint64_t dbUpdateSize=0;

   BinaryStreamBuffer bsb;
   bsb.attachAsStreamBuffer(is, (uint32_t)filesize-foffset);

   bool alreadyRead8B = false;
   uint32_t nextBlkSize;
   bool isEOF = false;
   BinaryData firstFour(4);

   // We use these two vars to stop parsing if we exceed the last header
   // that was processed (a new block was added since we processed headers)
   bool breakbreak = false;
   uint32_t locInBlkFile = foffset;

   InterfaceToLDB::Batch batch(iface_, BLKDATA);

   unsigned failedAttempts=0;
   
   // It turns out that this streambuffering is probably not helping, but
   // it doesn't hurt either, so I'm leaving it alone
   while(bsb.streamPull())
   {
      while(bsb.reader().getSizeRemaining() >= 8)
      {
         
         if(!alreadyRead8B)
         {
            bsb.reader().get_BinaryData(firstFour, 4);
            if(firstFour!=MagicBytes_)
            {
               isEOF = true; 
               break;
            }
            nextBlkSize = bsb.reader().get_uint32_t();
            bytesReadSoFar_ += 8;
            locInBlkFile += 8;
         }

         if(bsb.reader().getSizeRemaining() < nextBlkSize)
         {
            alreadyRead8B = true;
            break;
         }
         alreadyRead8B = false;

         BinaryRefReader brr(bsb.reader().getCurrPtr(), nextBlkSize);
         
         try
         {
            addRawBlockToDB(brr);
         }
         catch (BlockDeserializingException &e)
         {
            LOGERR << e.what() << " (error encountered processing block at byte "
               << locInBlkFile << " file "
               << blkfile << ", blocksize " << nextBlkSize << ")";
            failedAttempts++;
            
            if (failedAttempts >= 4)
            {
               // It looks like this file is irredeemably corrupt
               LOGERR << "Giving up searching " << blkfile
                  << " after having found 4 block headers with unparseable contents";
               breakbreak=true;
               break;
            }
            
            uint32_t bytesSkipped;
            const bool next = scanForMagicBytes(bsb, &bytesSkipped);
            if (!next)
            {
               LOGERR << "Could not find another block in the file";
               breakbreak=true;
               break;
            }
            else
            {
               locInBlkFile += bytesSkipped;
               LOGERR << "Found another block header at " << locInBlkFile;
            }

            continue;
         }
         dbUpdateSize += nextBlkSize;

         if(dbUpdateSize>BlockWriteBatcher::UPDATE_BYTES_THRESH)
         {
            dbUpdateSize = 0;
            batch.restart();
         }

         blocksReadSoFar_++;
         bytesReadSoFar_ += nextBlkSize;
         locInBlkFile += nextBlkSize;
         bsb.reader().advance(nextBlkSize);

         // This is a hack of hacks, but I can't seem to pass this data 
         // out through getLoadProgress* methods, because they don't 
         // update properly (from the main python thread) when the BDM 
         // is actively loading/scanning in a separate thread.
         // We'll watch for this file from the python code.
         writeProgressFile(DB_BUILD_ADD_RAW, blkProgressFile_, "dumpRawBlocksToDB");

         // Don't read past the last header we processed (in case new 
         // blocks were added since we processed the headers
         if(fnum == numBlkFiles_-1 && locInBlkFile >= endOfLastBlockByte_)
         {
            breakbreak = true;
            break;
         }
      }


      if(isEOF || breakbreak)
         break;
   }
}


////////////////////////////////////////////////////////////////////////////////
StoredHeader BlockDataManager_LevelDB::getBlockFromDB(uint32_t hgt, uint8_t dup)
{
   StoredHeader nullSBH;
   StoredHeader returnSBH;

   LDBIter ldbIter = iface_->getIterator(BLKDATA);
   BinaryData firstKey = DBUtils.getBlkDataKey(hgt, dup);

   if(!ldbIter.seekToExact(firstKey))
      return nullSBH;

   // Get the full block from the DB
   iface_->readStoredBlockAtIter(ldbIter, returnSBH);

   if(returnSBH.blockHeight_ != hgt || returnSBH.duplicateID_ != dup)
      return nullSBH;

   return returnSBH;

}

////////////////////////////////////////////////////////////////////////////////
uint8_t BlockDataManager_LevelDB::getMainDupFromDB(uint32_t hgt)
{
   return iface_->getValidDupIDForHeight(hgt);
}

////////////////////////////////////////////////////////////////////////////////
StoredHeader BlockDataManager_LevelDB::getMainBlockFromDB(uint32_t hgt)
{
   uint8_t dupMain = iface_->getValidDupIDForHeight(hgt);
   return getBlockFromDB(hgt, dupMain);
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::scanDBForRegisteredTx(uint32_t blk0,
                                                     uint32_t blk1)
{
   SCOPED_TIMER("scanDBForRegisteredTx");
   bytesReadSoFar_ = 0;

   bool doScanProgressThing = (blk1-blk0 > NUM_BLKS_IS_DIRTY);
   if(doScanProgressThing)
   {
      //if(BtcUtils::GetFileSize(bfile) != FILE_DOES_NOT_EXIST)
         //remove(bfile.c_str());
   }

   LDBIter ldbIter = iface_->getIterator(BLKDATA, BULK_SCAN);
   BinaryData firstKey = DBUtils.getBlkDataKey(blk0, 0);
   ldbIter.seekTo(firstKey);

   TIMER_START("ScanBlockchain");
   while(ldbIter.isValid(DB_PREFIX_TXDATA))
   {
      // Get the full block from the DB
      StoredHeader sbh;
      iface_->readStoredBlockAtIter(ldbIter, sbh);
      bytesReadSoFar_ += sbh.numBytes_;

      uint32_t hgt     = sbh.blockHeight_;
      uint8_t  dup     = sbh.duplicateID_;
      uint8_t  dupMain = iface_->getValidDupIDForHeight(hgt);
      if(!sbh.isMainBranch_ || dup != dupMain)
         continue;

      if(hgt >= blk1)
         break;
   
      // If we're here, we need to check the tx for relevance to the 
      // global scrAddr list.  Add to registered Tx map if so
      map<uint16_t, StoredTx>::iterator iter;
      for(iter  = sbh.stxMap_.begin();
          iter != sbh.stxMap_.end();
          iter++)
      {
         StoredTx & stx = iter->second;
         Tx tx = stx.getTxCopy();
         registeredScrAddrScan(tx.getPtr(), tx.getSize());
      }

      // This will write out about once every 5 sec
      writeProgressFile(DB_BUILD_SCAN, blkProgressFile_, "ScanBlockchain");
   }
   TIMER_STOP("ScanBlockchain");
}

////////////////////////////////////////////////////////////////////////////////
// Deletes all SSH entries in the database
void BlockDataManager_LevelDB::deleteHistories(void)
{
   SCOPED_TIMER("deleteHistories");

   LDBIter ldbIter = iface_->getIterator(BLKDATA);

   if(!ldbIter.seekToStartsWith(DB_PREFIX_SCRIPT, BinaryData(0)))
      return;

   //////////
   InterfaceToLDB::Batch batch(iface_, BLKDATA);

   do 
   {
      BinaryData key = ldbIter.getKey();

      if(key.getSize() == 0)
         break;

      if(key[0] != (uint8_t)DB_PREFIX_SCRIPT)
         break;

      iface_->deleteValue(BLKDATA, key);
      
   } while(ldbIter.advanceAndRead(DB_PREFIX_SCRIPT));
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::saveScrAddrHistories(void)
{
   LOGINFO << "Saving wallet history to DB";

   if(DBUtils.getArmoryDbType() != ARMORY_DB_BARE)
   {
      LOGERR << "Should only use saveScrAddrHistories in ARMORY_DB_BARE mode";
      LOGERR << "Aborting save operation.";
      return;
   }

   InterfaceToLDB::Batch batch(iface_, BLKDATA);

   uint32_t i=0;
   set<BtcWallet*>::iterator wltIter;
   for(wltIter  = registeredWallets_.begin();
       wltIter != registeredWallets_.end();
       wltIter++)
   {
      for(uint32_t a=0; a<(*wltIter)->getNumScrAddr(); a++)
      { 
         ScrAddrObj & scrAddr = (*wltIter)->getScrAddrObjByIndex(a);
         BinaryData uniqKey = scrAddr.getScrAddr();

         if(KEY_NOT_IN_MAP(uniqKey, registeredScrAddrMap_))
         {
            LOGERR << "How does the wallet have a non-registered ScrAddr?";
            LOGERR << uniqKey.toHexStr().c_str();
            continue;
         }

         RegisteredScrAddr & rsa = registeredScrAddrMap_[uniqKey];
         vector<TxIOPair*> & txioList = scrAddr.getTxIOList();

         StoredScriptHistory ssh;
         ssh.uniqueKey_ = scrAddr.getScrAddr();
         ssh.version_ = ARMORY_DB_VERSION;
         ssh.alreadyScannedUpToBlk_ = rsa.alreadyScannedUpToBlk_;
         for(uint32_t t=0; t<txioList.size(); t++)
            ssh.insertTxio(*(txioList[t]));

         iface_->putStoredScriptHistory(ssh); 
         
      }
   }
}


////////////////////////////////////////////////////////////////////////////////
// This method checks whether your blk0001.dat file is bigger than it was when
// we first read in the blockchain.  If so, we read the new data and add it to
// the memory pool.  Return value is how many blocks were added.
//
// NOTE:  You might want to check lastBlockWasReorg_ variable to know whether 
//        to expect some previously valid headers/txs to still be valid
//
uint32_t BlockDataManager_LevelDB::readBlkFileUpdate(void)
{
   SCOPED_TIMER("readBlkFileUpdate");

   // Make sure the file exists and is readable
   string filename = blkFileList_[blkFileList_.size()-1];

   uint64_t filesize = FILE_DOES_NOT_EXIST;
   ifstream is(filename.c_str(), ios::in|ios::binary);
   if(is.is_open())
   {
      is.seekg(0, ios::end);
      filesize = (size_t)is.tellg();
   }
      
   uint32_t prevTopBlk = blockchain_.top().getBlockHeight()+1;
   uint64_t currBlkBytesToRead;

   if( filesize == FILE_DOES_NOT_EXIST )
   {
      LOGERR << "***ERROR:  Cannot open " << filename.c_str();
      return 0;
   }
   else if((int64_t)filesize-(int64_t)endOfLastBlockByte_ < 8)
   {
      // This condition triggers if we hit the end of the file -- will
      // usually only be triggered by Bitcoin-Qt/bitcoind pre-0.8
      currBlkBytesToRead = 0;
   }
   else
   {
      // For post-0.8, the filesize will almost always be larger (padded).
      // Keep checking where we expect to see magic bytes, we know we're 
      // at the end if we see zero-bytes instead.
      uint64_t endOfNewLastBlock = endOfLastBlockByte_;
      BinaryData fourBytes(4);
      while((int64_t)filesize - (int64_t)endOfNewLastBlock >= 8)
      {
         is.seekg(endOfNewLastBlock, ios::beg);
         is.read((char*)fourBytes.getPtr(), 4);

         if(fourBytes != MagicBytes_)
            break;
         else
         {
            is.read((char*)fourBytes.getPtr(), 4);
            endOfNewLastBlock += READ_UINT32_LE((fourBytes.getPtr())) + 8;
         }
      }

      currBlkBytesToRead = endOfNewLastBlock - endOfLastBlockByte_;
   }
      

   // Check to see if there was a blkfile split, and we have to switch
   // to tracking the new file..  this condition triggers about once a week
   string nextFilename = BtcUtils::getBlkFilename(blkFileDir_, numBlkFiles_);
   uint64_t nextBlkBytesToRead = BtcUtils::GetFileSize(nextFilename);
   if(nextBlkBytesToRead == FILE_DOES_NOT_EXIST)
      nextBlkBytesToRead = 0;
   else
      LOGINFO << "New block file split! " << nextFilename.c_str();


   // If there is no new data, no need to continue
   if(currBlkBytesToRead==0 && nextBlkBytesToRead==0)
      return 0;
   
   // Observe if everything was up to date when we started, because we're 
   // going to add new blockchain data and don't want to trigger a rescan 
   // if this is just a normal update.
   const uint32_t nextBlk = blockchain_.top().getBlockHeight() + 1;
   const bool prevRegisteredUpToDate = (allScannedUpToBlk_==nextBlk);
   
   // Pull in the remaining data in old/curr blkfile, and beginning of new
   BinaryData newBlockDataRaw((size_t)(currBlkBytesToRead+nextBlkBytesToRead));

   // Seek to the beginning of the new data and read it
   if(currBlkBytesToRead>0)
   {
      ifstream is(filename.c_str(), ios::in | ios::binary);
      is.seekg(endOfLastBlockByte_, ios::beg);
      is.read((char*)newBlockDataRaw.getPtr(), currBlkBytesToRead);
      is.close();
   }

   // If a new block file exists, read that one too
   // nextBlkBytesToRead will include up to 16 MB of padding if our gateway
   // is a bitcoind/qt 0.8+ node.  Either way, it will be easy to detect when
   // we've reached the end of the real data, as long as there is no gap 
   // between the end of currBlk data and the start of newBlk data (there isn't)
   if(nextBlkBytesToRead>0)
   {
      uint8_t* ptrNextData = newBlockDataRaw.getPtr() + currBlkBytesToRead;
      ifstream is(nextFilename.c_str(), ios::in | ios::binary);
      is.read((char*)ptrNextData, nextBlkBytesToRead);
      is.close();
   }


   // Walk through each of the new blocks, adding each one to RAM and DB
   // Do a full update of everything after each block, for simplicity
   // (which means we may be adding a couple blocks, the first of which
   // may appear valid but orphaned by later blocks -- that's okay as 
   // we'll just reverse it when we add the later block -- this is simpler)
   BinaryRefReader brr(newBlockDataRaw);
   BinaryData fourBytes(4);
   uint32_t nBlkRead = 0;
   bool keepGoing = true;
   while(keepGoing)
   {
      // We concatenated all data together, even if across two files
      // Check which file data belongs to and set FileDataPtr appropriately
      uint32_t useFileIndex0Idx = numBlkFiles_-1;
      uint32_t bhOffset = (uint32_t)(endOfLastBlockByte_ + 8);
      if(brr.getPosition() >= currBlkBytesToRead)
      {
         useFileIndex0Idx = numBlkFiles_;
         bhOffset = (uint32_t)(brr.getPosition() - currBlkBytesToRead + 8);
      }
      

      ////////////
      // The reader should be at the start of magic bytes of the new block
      brr.get_BinaryData(fourBytes, 4);
      if(fourBytes != MagicBytes_)
         break;
         
      uint32_t nextBlockSize = brr.get_uint32_t();

      try
      {
         const Blockchain::ReorganizationState state =
               addNewBlockData(
                     brr, 
                     useFileIndex0Idx,
                     bhOffset,
                     nextBlockSize
                  );

         nBlkRead++;

         if(!state.prevTopBlockStillValid)
         {
            LOGWARN << "Blockchain Reorganization detected!";
            reassessAfterReorg(
                  state.prevTopBlock, &blockchain_.top(), state.reorgBranchPoint
               );
            purgeZeroConfPool();

            // Update all the registered wallets...
            updateWalletsAfterReorg(registeredWallets_);
         }
         else if(state.hasNewTop)
         {
            const BlockHeader & bh = blockchain_.top();
            uint32_t hgt = bh.getBlockHeight();
            uint8_t  dup = bh.getDuplicateID();
      
            if(DBUtils.getArmoryDbType() != ARMORY_DB_BARE) 
            {
               LOGINFO << "Applying block to DB!";
               BlockWriteBatcher batcher(iface_);
               batcher.applyBlockToDB(hgt, dup);
            }

            // Replaced this with the scanDBForRegisteredTx call outside the loop
            //StoredHeader sbh;
            //iface_->getStoredHeader(sbh, hgt, dup);
            //map<uint16_t, StoredTx>::iterator iter;
            //for(iter = sbh.stxMap_.begin(); iter != sbh.stxMap_.end(); iter++)
            //{
               //Tx regTx = iter->second.getTxCopy();
               //registeredScrAddrScan(regTx.getPtr(), regTx.getSize());
            //}
         }
         else
         {
            LOGWARN << "Block data did not extend the main chain!";
            // New block was added -- didn't cause a reorg but it's not the
            // new top block either (it's a fork block).  We don't do anything
            // at all until the reorg actually happens
         }
      }
      catch (std::exception &e)
      {
         LOGERR << "Error adding block data: " << e.what();
      }
      if(brr.isEndOfStream() || brr.getSizeRemaining() < 8)
         keepGoing = false;
   }

   lastTopBlock_ = blockchain_.top().getBlockHeight()+1;

   purgeZeroConfPool();
   scanDBForRegisteredTx(prevTopBlk, lastTopBlock_);

   if(prevRegisteredUpToDate)
   {
      allScannedUpToBlk_ = blockchain_.top().getBlockHeight()+1;
      updateRegisteredScrAddrs(allScannedUpToBlk_);
   }

   // If the blk file split, switch to tracking it
   LOGINFO << "Added new blocks to memory pool: " << nBlkRead;

   // If we pull non-zero amount of data from next block file...there 
   // was a blkfile split!
   if(nextBlkBytesToRead>0)
   {
      numBlkFiles_ += 1;
      blkFileList_.push_back(nextFilename);
   }

   #ifdef _DEBUG
	   UniversalTimer::instance().printCSV(string("timings.csv"));
	   #ifdef _DEBUG_FULL_VERBOSE 
         UniversalTimer::instance().printCSV(cout,true);
	   #endif
   #endif

   return nBlkRead;

}


////////////////////////////////////////////////////////////////////////////////
// BDM detects the reorg, but is wallet-agnostic so it can't update any wallets
// You have to call this yourself after you check whether the last organizeChain
// call indicated that a reorg happened
void BlockDataManager_LevelDB::updateWalletAfterReorg(BtcWallet & wlt)
{
   SCOPED_TIMER("updateWalletAfterReorg");

   // Fix the wallet's ledger
   vector<LedgerEntry> & ledg = wlt.getTxLedger();
   for(uint32_t i=0; i<ledg.size(); i++)
   {
      HashString const & txHash = ledg[i].getTxHash();
      if(txJustInvalidated_.count(txHash) > 0)
         ledg[i].setValid(false);

      if(txJustAffected_.count(txHash) > 0)
         ledg[i].changeBlkNum(getTxRefByHash(txHash).getBlockHeight());
   }

   // Now fix the individual address ledgers
   for(uint32_t a=0; a<wlt.getNumScrAddr(); a++)
   {
      ScrAddrObj & addr = wlt.getScrAddrObjByIndex(a);
      vector<LedgerEntry> & addrLedg = addr.getTxLedger();
      for(uint32_t i=0; i<addrLedg.size(); i++)
      {
         HashString const & txHash = addrLedg[i].getTxHash();
         if(txJustInvalidated_.count(txHash) > 0)
            addrLedg[i].setValid(false);
   
         if(txJustAffected_.count(txHash) > 0) 
            addrLedg[i].changeBlkNum(getTxRefByHash(txHash).getBlockHeight());
      }
   }
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::updateWalletsAfterReorg(vector<BtcWallet*> wltvect)
{
   for(uint32_t i=0; i<wltvect.size(); i++)
      updateWalletAfterReorg(*wltvect[i]);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::updateWalletsAfterReorg(set<BtcWallet*> wltset)
{
   set<BtcWallet*>::iterator iter;
   for(iter = wltset.begin(); iter != wltset.end(); iter++)
      updateWalletAfterReorg(**iter);
}

/////////////////////////////////////////////////////////////////////////////
/* This was never actually used
bool BlockDataManager_LevelDB::verifyBlkFileIntegrity(void)
{
   SCOPED_TIMER("verifyBlkFileIntegrity");
   PDEBUG("Verifying blk0001.dat integrity");

   bool isGood = true;
   map<HashString, BlockHeader>::iterator headIter;
   for(headIter  = headerMap_.begin();
       headIter != headerMap_.end();
       headIter++)
   {
      BlockHeader & bhr = headIter->second;
      bool thisHeaderIsGood = bhr.verifyIntegrity();
      if( !thisHeaderIsGood )
      {
         cout << "Blockfile contains incorrect header or tx data:" << endl;
         cout << "  Block number:    " << bhr.getBlockHeight() << endl;
         cout << "  Block hash (BE):   " << endl;
         cout << "    " << bhr.getThisHash().copySwapEndian().toHexStr() << endl;
         cout << "  Num Tx :         " << bhr.getNumTx() << endl;
         //cout << "  Tx Hash List: (compare to raw tx data on blockexplorer)" << endl;
         //for(uint32_t t=0; t<bhr.getNumTx(); t++)
            //cout << "    " << bhr.getTxRefPtrList()[t]->getThisHash().copySwapEndian().toHexStr() << endl;
      }
      isGood = isGood && thisHeaderIsGood;
   }
   return isGood;
   PDEBUG("Done verifying blockfile integrity");
}
*/



/////////////////////////////////////////////////////////////////////////////
// Pass in a BRR that starts at the beginning of the serialized block,
// i.e. the first 80 bytes of this BRR is the blockheader
/*
bool BlockDataManager_LevelDB::parseNewBlock(BinaryRefReader & brr,
                                             uint32_t fileIndex0Idx,
                                             uint32_t thisHeaderOffset,
                                             uint32_t blockSize)
{
   if(brr.getSizeRemaining() < blockSize || brr.isEndOfStream())
   {
      LOGERR << "***ERROR:  parseNewBlock did not get enough data...";
      return false;
   }

   // Create the objects once that will be used for insertion
   // (txInsResult always succeeds--because multimap--so only iterator returns)
   static pair<HashString, BlockHeader>                      bhInputPair;
   static pair<map<HashString, BlockHeader>::iterator, bool> bhInsResult;
   
   // Read the header and insert it into the map.
   bhInputPair.second.unserialize(brr);
   bhInputPair.first = bhInputPair.second.getThisHash();
   bhInsResult = headerMap_.insert(bhInputPair);
   BlockHeader * bhptr = &(bhInsResult.first->second);
   if(!bhInsResult.second)
      *bhptr = bhInsResult.first->second; // overwrite it even if insert fails

   // Then put the bare header into the DB and get its duplicate ID.
   StoredHeader sbh;
   sbh.createFromBlockHeader(*bhptr);
   uint8_t dup = iface_->putBareHeader(sbh);
   bhptr->setDuplicateID(dup);

   // Regardless of whether this was a reorg, we have to add the raw block
   // to the DB, but we don't apply it yet.
   brr.rewind(HEADER_SIZE);
   addRawBlockToDB(brr);

   // Note where we will start looking for the next block, later
   endOfLastBlockByte_ = thisHeaderOffset + blockSize;

   // Read the #tx and fill in some header properties
   uint8_t viSize;
   uint32_t nTx = (uint32_t)brr.get_var_int(&viSize);

   // The file offset of the first tx in this block is after the var_int
   uint32_t txOffset = thisHeaderOffset + HEADER_SIZE + viSize; 

   // Read each of the Tx
   //bhptr->txPtrList_.resize(nTx);
   uint32_t txSize;
   static vector<uint32_t> offsetsIn;
   static vector<uint32_t> offsetsOut;
   static BinaryData hashResult(32);

   for(uint32_t i=0; i<nTx; i++)
   {
      // We get a little funky here because I need to avoid ALL unnecessary
      // copying -- therefore everything is pointers...and confusing...
      uint8_t const * ptrToRawTx = brr.getCurrPtr();
      
      txSize = BtcUtils::TxCalcLength(ptrToRawTx, &offsetsIn, &offsetsOut);
      BtcUtils::getHash256_NoSafetyCheck(ptrToRawTx, txSize, hashResult);

      // Figure out, as quickly as possible, whether this tx has any relevance
      // to any of the registered addresses.  Again, using pointers...
      registeredScrAddrScan(ptrToRawTx, txSize, &offsetsIn, &offsetsOut);

      // Prepare for the next tx.  Manually advance brr since used ptr directly
      txOffset += txSize;
      brr.advance(txSize);
   }
   return true;
}
*/
   


////////////////////////////////////////////////////////////////////////////////
// This method returns the result of our inserting the block
Blockchain::ReorganizationState BlockDataManager_LevelDB::addNewBlockData(
                                                BinaryRefReader & brrRawBlock,
                                                uint32_t fileIndex0Idx,
                                                uint32_t thisHeaderOffset,
                                                uint32_t blockSize)
{
   SCOPED_TIMER("addNewBlockData");
   uint8_t const * startPtr = brrRawBlock.getCurrPtr();
   HashString newHeadHash = BtcUtils::getHash256(startPtr, HEADER_SIZE);

   /////////////////////////////////////////////////////////////////////////////
   // This used to be in parseNewBlock(...) but relocated here because it's
   // not duplicated anywhere, and during the upgrade to LevelDB I needed
   // the code flow to be more linear in order to figure out how to put 
   // all the pieces together properly.  I may refactor this code out into
   // its own method again, later
   if(brrRawBlock.getSizeRemaining() < blockSize || brrRawBlock.isEndOfStream())
   {
      throw std::runtime_error("addNewBlockData: Failed to read block data");
   }

   // Insert the block

   BlockHeader bl;
   bl.unserialize(brrRawBlock);
   HashString hash = bl.getThisHash();
   
   BlockHeader &addedBlock = blockchain_.addBlock(hash, bl);
   const Blockchain::ReorganizationState state = blockchain_.organize();
   
   // Then put the bare header into the DB and get its duplicate ID.
   StoredHeader sbh;
   sbh.createFromBlockHeader(addedBlock);
   uint8_t dup = iface_->putBareHeader(sbh);
   addedBlock.setDuplicateID(dup);

   // Regardless of whether this was a reorg, we have to add the raw block
   // to the DB, but we don't apply it yet.
   brrRawBlock.rewind(HEADER_SIZE);
   addRawBlockToDB(brrRawBlock);

   // Note where we will start looking for the next block, later
   endOfLastBlockByte_ = thisHeaderOffset + blockSize;

   /* From parseNewBlock but not needed here in the new code
   // Read the #tx and fill in some header properties
   uint8_t viSize;
   uint32_t nTx = (uint32_t)brrRawBlock.get_var_int(&viSize);

   // The file offset of the first tx in this block is after the var_int
   uint32_t txOffset = thisHeaderOffset + HEADER_SIZE + viSize; 

   // Read each of the Tx
   //bhptr->txPtrList_.resize(nTx);
   uint32_t txSize;
   static vector<uint32_t> offsetsIn;
   static vector<uint32_t> offsetsOut;
   static BinaryData hashResult(32);

   for(uint32_t i=0; i<nTx; i++)
   {
      // We get a little funky here because I need to avoid ALL unnecessary
      // copying -- therefore everything is pointers...and confusing...
      uint8_t const * ptrToRawTx = brrRawBlock.getCurrPtr();
      
      txSize = BtcUtils::TxCalcLength(ptrToRawTx, &offsetsIn, &offsetsOut);
      BtcUtils::getHash256_NoSafetyCheck(ptrToRawTx, txSize, hashResult);

      // Figure out, as quickly as possible, whether this tx has any relevance
      registeredScrAddrScan(ptrToRawTx, txSize, &offsetsIn, &offsetsOut);

      // Prepare for the next tx.  Manually advance brr since used ptr directly
      txOffset += txSize;
      brrRawBlock.advance(txSize);
   }
   return true;
   */


   // We actually accessed the pointer directly in this method, without 
   // advancing the BRR position.  But the outer function expects to see
   // the new location we would've been at if the BRR was used directly.
   brrRawBlock.advance(blockSize);
   return state;
}



// This piece may be useful for adding new data, but I don't want to enforce it,
// yet
/*
#ifndef _DEBUG
   // In the real client, we want to execute these checks.  But we may want
   // to pass in hand-made data when debugging, and don't want to require
   // the hand-made blocks to have leading zeros.
   if(! (headHash.getSliceCopy(28,4) == BtcUtils::EmptyHash_.getSliceCopy(28,4)))
   {
      cout << "***ERROR: header hash does not have leading zeros" << endl;   
      cerr << "***ERROR: header hash does not have leading zeros" << endl;   
      return true;  // no data added, so no reorg
   }

   // Same story with merkle roots in debug mode
   HashString merkleRoot = BtcUtils::calculateMerkleRoot(txHashes);
   if(! (merkleRoot == BinaryDataRef(rawHeader.getPtr() + 36, 32)))
   {
      cout << "***ERROR: merkle root does not match header data" << endl;
      cerr << "***ERROR: merkle root does not match header data" << endl;
      return true;  // no data added, so no reorg
   }
#endif
*/
   



////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::reassessAfterReorg( BlockHeader* oldTopPtr,
                                                   BlockHeader* newTopPtr,
                                                   BlockHeader* branchPtr)
{
   SCOPED_TIMER("reassessAfterReorg");
   LOGINFO << "Reassessing Tx validity after reorg";

   // Walk down invalidated chain first, until we get to the branch point
   // Mark transactions as invalid
   txJustInvalidated_.clear();
   txJustAffected_.clear();
   
   BlockWriteBatcher blockWrites(iface_);
   
   BlockHeader* thisHeaderPtr = oldTopPtr;
   LOGINFO << "Invalidating old-chain transactions...";
   
   while(thisHeaderPtr != branchPtr)
   {
      uint32_t hgt = thisHeaderPtr->getBlockHeight();
      uint8_t  dup = thisHeaderPtr->getDuplicateID();

      if(DBUtils.getArmoryDbType() != ARMORY_DB_BARE)
      {
         // Added with leveldb... in addition to reversing blocks in RAM, 
         // we also need to undo the blocks in the DB
         StoredUndoData sud;
         createUndoDataFromBlock(hgt, dup, sud);
         blockWrites.undoBlockFromDB(sud);
      }
      
      StoredHeader sbh;
      iface_->getStoredHeader(sbh, hgt, dup, true);

      // This is the original, tested, reorg code
      previouslyValidBlockHeaderPtrs_.push_back(thisHeaderPtr);
      for(uint32_t i=0; i<sbh.numTx_; i++)
      {
         StoredTx & stx = sbh.stxMap_[i];
         LOGWARN << "   Tx: " << stx.thisHash_.getSliceCopy(0,8).toHexStr();
         txJustInvalidated_.insert(stx.thisHash_);
         txJustAffected_.insert(stx.thisHash_);
         registeredTxSet_.erase(stx.thisHash_);
         removeRegisteredTx(stx.thisHash_);
      }
      thisHeaderPtr = &blockchain_.getHeaderByHash(thisHeaderPtr->getPrevHash());
   }

   // Walk down the newly-valid chain and mark transactions as valid.  If 
   // a tx is in both chains, it will still be valid after this process
   // UPDATE for LevelDB upgrade:
   //       This used to start from the new top block and walk down, but 
   //       I need to apply the blocks in order, so I switched it to start
   //       from the branch point and walk up
   thisHeaderPtr = branchPtr; // note branch block was not undone, skip it
   LOGINFO << "Marking new-chain transactions valid...";
   while( thisHeaderPtr->getNextHash() != BtcUtils::EmptyHash_ &&
          thisHeaderPtr->getNextHash().getSize() > 0 ) 
   {
      thisHeaderPtr = &blockchain_.getHeaderByHash(thisHeaderPtr->getNextHash());
      uint32_t hgt = thisHeaderPtr->getBlockHeight();
      uint8_t  dup = thisHeaderPtr->getDuplicateID();
      iface_->markBlockHeaderValid(hgt, dup);
      StoredHeader sbh;
      iface_->getStoredHeader(sbh, hgt, dup, true);

      if(DBUtils.getArmoryDbType() != ARMORY_DB_BARE)
         blockWrites.applyBlockToDB(sbh);

      for(uint32_t i=0; i<sbh.numTx_; i++)
      {
         StoredTx & stx = sbh.stxMap_[i];
         LOGWARN << "   Tx: " << stx.thisHash_.getSliceCopy(0,8).toHexStr();
         txJustInvalidated_.erase(stx.thisHash_);
         txJustAffected_.insert(stx.thisHash_);
         Tx tx = stx.getTxCopy();
         registeredScrAddrScan(tx.getPtr(), tx.getSize());
      }
   }

   LOGWARN << "Done reassessing tx validity";
}

////////////////////////////////////////////////////////////////////////////////
// We're going to need the BDM's help to get the sender for a TxIn since it
// sometimes requires going and finding the TxOut from the distant past
////////////////////////////////////////////////////////////////////////////////
TxOut BlockDataManager_LevelDB::getPrevTxOut(TxIn & txin)
{
   if(txin.isCoinbase())
      return TxOut();

   OutPoint op = txin.getOutPoint();
   Tx theTx = getTxByHash(op.getTxHash());
   uint32_t idx = op.getTxOutIndex();
   return theTx.getTxOutCopy(idx);
}

////////////////////////////////////////////////////////////////////////////////
// We're going to need the BDM's help to get the sender for a TxIn since it
// sometimes requires going and finding the TxOut from the distant past
////////////////////////////////////////////////////////////////////////////////
Tx BlockDataManager_LevelDB::getPrevTx(TxIn & txin)
{
   if(txin.isCoinbase())
      return Tx();

   OutPoint op = txin.getOutPoint();
   return getTxByHash(op.getTxHash());
}

////////////////////////////////////////////////////////////////////////////////
HashString BlockDataManager_LevelDB::getSenderScrAddr(TxIn & txin)
{
   if(txin.isCoinbase())
      return HashString(0);

   return getPrevTxOut(txin).getScrAddressStr();
}


////////////////////////////////////////////////////////////////////////////////
int64_t BlockDataManager_LevelDB::getSentValue(TxIn & txin)
{
   if(txin.isCoinbase())
      return -1;

   return getPrevTxOut(txin).getValue();

}


////////////////////////////////////////////////////////////////////////////////
// Methods for handling zero-confirmation transactions
////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::enableZeroConf(string zcFilename, bool zcLite)
{
   SCOPED_TIMER("enableZeroConf");
   LOGINFO << "Enabling zero-conf tracking " << (zcLite ? "(lite)" : "");
   zcFilename_ = zcFilename;
   zcEnabled_  = true; 
   zcLiteMode_ = zcLite;

   readZeroConfFile(zcFilename_); // does nothing if DNE
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::readZeroConfFile(string zcFilename)
{
   SCOPED_TIMER("readZeroConfFile");
   uint64_t filesize = BtcUtils::GetFileSize(zcFilename);
   if(filesize<8 || filesize==FILE_DOES_NOT_EXIST)
      return;

   ifstream zcFile(zcFilename_.c_str(),  ios::in | ios::binary);
   BinaryData zcData((size_t)filesize);
   zcFile.read((char*)zcData.getPtr(), filesize);
   zcFile.close();

   // We succeeded opening the file...
   BinaryRefReader brr(zcData);
   while(brr.getSizeRemaining() > 8)
   {
      uint64_t txTime = brr.get_uint64_t();
      uint32_t txSize = BtcUtils::TxCalcLength(brr.getCurrPtr(), brr.getSizeRemaining());
      BinaryData rawtx(txSize);
      brr.get_BinaryData(rawtx.getPtr(), txSize);
      addNewZeroConfTx(rawtx, (uint32_t)txTime, false);
   }
   purgeZeroConfPool();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::disableZeroConf(void)
{
   SCOPED_TIMER("disableZeroConf");
   zcEnabled_  = false; 
}


////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::addNewZeroConfTx(BinaryData const & rawTx, 
                                                uint32_t txtime,
                                                bool writeToFile)
{
   SCOPED_TIMER("addNewZeroConfTx");

   if(txtime==0)
      txtime = (uint32_t)time(NULL);

   HashString txHash = BtcUtils::getHash256(rawTx);

   // If this is already in the zero-conf map or in the blockchain, ignore it
   if(hasTxWithHash(txHash))
      return false;


   // In zero-conf-lite-mode, we only actually add the ZC if it's related
   // to one of our registered wallets.  
   if(zcLiteMode_)
   {
      // The bulk filter
      Tx txObj(rawTx);

      bool isOurs = false;
      set<BtcWallet*>::iterator wltIter;
      for(wltIter  = registeredWallets_.begin();
          wltIter != registeredWallets_.end();
          wltIter++)
      {
         // The bulk filter returns pair<isRelatedToUs, inputIsOurs>
         isOurs = isOurs || (*wltIter)->isMineBulkFilter(txObj).first;
      }

      if(!isOurs)
         return false;
   }
    
   
   zeroConfMap_[txHash] = ZeroConfData();
   ZeroConfData & zc = zeroConfMap_[txHash];
   zc.iter_ = zeroConfRawTxList_.insert(zeroConfRawTxList_.end(), rawTx);
   zc.txobj_.unserialize(*(zc.iter_));
   zc.txtime_ = txtime;

   // Record time.  Write to file
   if(writeToFile)
   {
      ofstream zcFile(zcFilename_.c_str(), ios::app | ios::binary);
      zcFile.write( (char*)(&zc.txtime_), sizeof(uint64_t) );
      zcFile.write( (char*)zc.txobj_.getPtr(),  zc.txobj_.getSize());
      zcFile.close();
   }
   return true;
}



////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::purgeZeroConfPool(void)
{
   SCOPED_TIMER("purgeZeroConfPool");
   list< map<HashString, ZeroConfData>::iterator > mapRmList;

   // Find all zero-conf transactions that made it into the blockchain
   map<HashString, ZeroConfData>::iterator iter;
   for(iter  = zeroConfMap_.begin();
       iter != zeroConfMap_.end();
       iter++)
   {
      if(!getTxRefByHash(iter->first).isNull())
         mapRmList.push_back(iter);
   }

   // We've made a list of the zc tx to remove, now let's remove them
   // I decided this was safer than erasing the data as we were iterating
   // over it in the previous loop
   list< map<HashString, ZeroConfData>::iterator >::iterator rmIter;
   for(rmIter  = mapRmList.begin();
       rmIter != mapRmList.end();
       rmIter++)
   {
      zeroConfRawTxList_.erase( (*rmIter)->second.iter_ );
      zeroConfMap_.erase( *rmIter );
   }

   // Rewrite the zero-conf pool file
   if(mapRmList.size() > 0)
      rewriteZeroConfFile();

}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::rewriteZeroConfFile(void)
{
   SCOPED_TIMER("rewriteZeroConfFile");
   ofstream zcFile(zcFilename_.c_str(), ios::out | ios::binary);

   static HashString txHash(32);
   list<HashString>::iterator iter;
   for(iter  = zeroConfRawTxList_.begin();
       iter != zeroConfRawTxList_.end();
       iter++)
   {
      BtcUtils::getHash256(*iter, txHash);
      ZeroConfData & zcd = zeroConfMap_[txHash];
      zcFile.write( (char*)(&zcd.txtime_), sizeof(uint64_t) );
      zcFile.write( (char*)(zcd.txobj_.getPtr()),  zcd.txobj_.getSize());
   }

   zcFile.close();

}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::rescanWalletZeroConf(BtcWallet & wlt)
{
   SCOPED_TIMER("rescanWalletZeroConf");
   // Clear the whole list, rebuild
   wlt.clearZeroConfPool();

   static HashString txHash(32);
   list<HashString>::iterator iter;
   for(iter  = zeroConfRawTxList_.begin();
       iter != zeroConfRawTxList_.end();
       iter++)
   {

      if(iter->getSize() == 0)
         continue;

      BtcUtils::getHash256(*iter, txHash);
      ZeroConfData & zcd = zeroConfMap_[txHash];

      if( !isTxFinal(zcd.txobj_) )
         continue;

      wlt.scanTx(zcd.txobj_, 0, (uint32_t)zcd.txtime_, UINT32_MAX);
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::pprintSSHInfoAboutHash160(BinaryData const & a160)
{
   StoredScriptHistory ssh;
   iface_->getStoredScriptHistory(ssh, HASH160PREFIX + a160);
   if(!ssh.isInitialized())
   {
      LOGERR << "Address is not in DB: " << a160.toHexStr().c_str();
      return;
   }

   vector<UnspentTxOut> utxos = getUTXOVectForHash160(a160);
   vector<TxIOPair> txios = getHistoryForScrAddr(a160);

   uint64_t bal = getDBBalanceForHash160(a160);
   uint64_t rcv = getDBReceivedForHash160(a160);

   cout << "Information for hash160: " << a160.toHexStr().c_str() << endl;
   cout << "Received:  " << rcv << endl;
   cout << "Balance:   " << bal << endl;
   cout << "NumUtxos:  " << utxos.size() << endl;
   cout << "NumTxios:  " << txios.size() << endl;
   for(uint32_t i=0; i<utxos.size(); i++)
      utxos[i].pprintOneLine(UINT32_MAX);

   cout << "Full SSH info:" << endl; 
   ssh.pprintFullSSH();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::pprintZeroConfPool(void)
{
   static HashString txHash(32);
   list<HashString>::iterator iter;
   for(iter  = zeroConfRawTxList_.begin();
       iter != zeroConfRawTxList_.end();
       iter++)
   {
      BtcUtils::getHash256(*iter, txHash);
      ZeroConfData & zcd = zeroConfMap_[txHash];
      Tx & tx = zcd.txobj_;
      cout << tx.getThisHash().getSliceCopy(0,8).toHexStr().c_str() << " ";
      for(uint32_t i=0; i<tx.getNumTxOut(); i++)
         cout << tx.getTxOutCopy(i).getValue() << " ";
      cout << endl;
   }
}



/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::isTxFinal(Tx & tx)
{
   // Anything that is replaceable (regular or through blockchain injection)
   // will be considered isFinal==false.  Users shouldn't even see the tx,
   // because the concept may be confusing, and the CURRENT use of non-final
   // tx is most likely for malicious purposes (as of this writing)
   //
   // This will change as multi-sig becomes integrated, and replacement will
   // eventually be enabled (properly), in which case I will expand this
   // to be more rigorous.
   //
   // For now I consider anything time-based locktimes (instead of block-
   // based locktimes) to be final if this is more than one day after the 
   // locktime expires.  This accommodates the most extreme case of silliness
   // due to time-zones (this shouldn't be an issue, but I haven't spent the
   // time to figure out how UTC and local time interact with time.h and 
   // block timestamps).  In cases where locktime is legitimately used, it 
   // is likely to be many days in the future, and one day may not even
   // matter.  I'm erring on the side of safety, not convenience.
   
   if(tx.getLockTime() == 0)
      return true;

   bool allSeqMax = true;
   for(uint32_t i=0; i<tx.getNumTxIn(); i++)
      if(tx.getTxInCopy(i).getSequence() < UINT32_MAX)
         allSeqMax = false;

   if(allSeqMax)
      return true;

   if(tx.getLockTime() < 500000000)
      return (blockchain_.top().getBlockHeight()>tx.getLockTime());
   else
      return (time(NULL)>tx.getLockTime()+86400);
}









////////////////////////////////////////////////////////////////////////////////
// We must have already added this to the header map and DB and have a dupID
void BlockDataManager_LevelDB::addRawBlockToDB(BinaryRefReader & brr)
{
   SCOPED_TIMER("addRawBlockToDB");
   
   //if(sbh.stxMap_.size() == 0)
   //{
      //LOGERR << "Cannot add raw block to DB without any transactions";
      //return false;
   //}

   BinaryDataRef first4 = brr.get_BinaryDataRef(4);
   
   // Skip magic bytes and block sz if exist, put ptr at beginning of header
   if(first4 == MagicBytes_)
      brr.advance(4);
   else
      brr.rewind(4);

   // Again, we rely on the assumption that the header has already been
   // added to the headerMap and the DB, and we have its correct height 
   // and dupID
   StoredHeader sbh;
   try
   {
      sbh.unserializeFullBlock(brr, true, false);
   }
   catch (BlockDeserializingException &)
   {
      if (sbh.hasBlockHeader_)
      {
         // we still add this block to the chain in this case,
         // if we miss a few transactions it's better than
         // missing the entire block
         const BlockHeader & bh = blockchain_.getHeaderByHash(sbh.thisHash_);
         sbh.blockHeight_  = bh.getBlockHeight();
         sbh.duplicateID_  = bh.getDuplicateID();
         sbh.isMainBranch_ = bh.isMainBranch();
         sbh.blockAppliedToDB_ = false;

         // Don't put it into the DB if it's not proper!
         if(sbh.blockHeight_==UINT32_MAX || sbh.duplicateID_==UINT8_MAX)
            throw BlockDeserializingException("Error parsing block (corrupt?) - Cannot add raw block to DB without hgt & dup");

         iface_->putStoredHeader(sbh, true);
         missingBlockHashes_.push_back( sbh.thisHash_ );
         throw BlockDeserializingException("Error parsing block (corrupt?) - block header valid");
      }
      else
      {
         throw BlockDeserializingException("Error parsing block (corrupt?) and block header invalid");
      }
   }
   BlockHeader & bh = blockchain_.getHeaderByHash(sbh.thisHash_);
   sbh.blockHeight_  = bh.getBlockHeight();
   sbh.duplicateID_  = bh.getDuplicateID();
   sbh.isMainBranch_ = bh.isMainBranch();
   sbh.blockAppliedToDB_ = false;

   // Don't put it into the DB if it's not proper!
   if(sbh.blockHeight_==UINT32_MAX || sbh.duplicateID_==UINT8_MAX)
      throw BlockDeserializingException("Cannot add raw block to DB without hgt & dup");
   iface_->putStoredHeader(sbh, true);
}





////////////////////////////////////////////////////////////////////////////////
// For now, we will call createUndoDataFromBlock(), and then pass that data to 
// undoBlockFromDB(), even though it will result in accessing the DB data 
// twice --
//    (1) LevelDB does an excellent job caching results, so the second lookup
//        should be instantaneous
//    (2) We prefer to integrate StoredUndoData objects now, which will be 
//        needed for pruning even though we don't strictly need it for no-prune
//        now (and could save a lookup by skipping it).  But I want unified
//        code flow for both pruning and non-pruning. 
bool BlockDataManager_LevelDB::createUndoDataFromBlock(uint32_t hgt, 
                                                       uint8_t  dup,
                                                       StoredUndoData & sud)
{
   SCOPED_TIMER("createUndoDataFromBlock");

   StoredHeader sbh;

   // Fetch the full, stored block
   iface_->getStoredHeader(sbh, hgt, dup, true);
   if(!sbh.haveFullBlock())
   {
      LOGERR << "Cannot get undo data for block because not full!";
      return false;
   }

   sud.blockHash_   = sbh.thisHash_;
   sud.blockHeight_ = sbh.blockHeight_;
   sud.duplicateID_ = sbh.duplicateID_;

   // Go through tx list, fetch TxOuts that are spent, record OutPoints added
   for(uint32_t itx=0; itx<sbh.numTx_; itx++)
   {
      StoredTx & stx = sbh.stxMap_[itx];
      
      // Convert to a regular tx to make accessing TxIns easier
      Tx regTx = stx.getTxCopy();
      for(uint32_t iin=0; iin<regTx.getNumTxIn(); iin++)
      {
         TxIn txin = regTx.getTxInCopy(iin);
         BinaryData prevHash  = txin.getOutPoint().getTxHash();
         uint16_t   prevIndex = txin.getOutPoint().getTxOutIndex();

         // Skip if coinbase input
         if(prevHash == BtcUtils::EmptyHash_)
            continue;
         
         // Above we checked the block to be undone is full, but we
         // still need to make sure the prevTx we just fetched has our data.
         StoredTx prevStx;
         iface_->getStoredTx(prevStx, prevHash);
         //if(prevStx.stxoMap_.find(prevIndex) == prevStx.stxoMap_.end())
         if(KEY_NOT_IN_MAP(prevIndex, prevStx.stxoMap_))
         {
            LOGERR << "StoredTx retrieved from DB, but TxOut not with it";
            return false;
         }
         
         // 
         sud.stxOutsRemovedByBlock_.push_back(prevStx.stxoMap_[prevIndex]);
      }
      
      // Use the stxoMap_ to iterate through TxOuts
      for(uint32_t iout=0; iout<stx.numTxOut_; iout++)
      {
         OutPoint op(stx.thisHash_, iout);
         sud.outPointsAddedByBlock_.push_back(op);
      }
   }

   return true;
}




////////////////////////////////////////////////////////////////////////////////
// We may use this to trigger flushing the queued DB updates
//bool BlockDataManager_LevelDB::estimateDBUpdateSize(
                        //map<BinaryData, StoredTx> &            stxToModify,
                        //map<BinaryData, StoredScriptHistory> & sshToModify)
//{
 
//}



// kate: indent-width 3; replace-tabs on;
