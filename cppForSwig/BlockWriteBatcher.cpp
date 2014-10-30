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
static StoredTx* makeSureSTXInMap(
            LMDBBlockDatabase* iface,
            BinaryDataRef txHash,
            map<BinaryData, StoredTx*> & stxMap,
            vector<StoredTx*> & pulledStx,
            uint64_t* additionalSize)
{
   // TODO:  If we are pruning, we may have completely removed this tx from
   //        the DB, which means that it won't be in the map or the DB.
   //        But this method was written before pruning was ever implemented...
   StoredTx * stxptr;

   // Get the existing STX or make a new one
   auto txIter = stxMap.find(txHash);
   if(ITER_IN_MAP(txIter, stxMap))
      stxptr = txIter->second;
   else
   {
      //allocate new stx that will be cleaned after it is commited
      StoredTx *stxTemp = new StoredTx();
      iface->getStoredTx(*stxTemp, txHash);
      stxMap[txHash] = stxTemp;

      //keep track of this pointer for commit thread to delete
      pulledStx.push_back(stxTemp);

      stxptr = stxMap[txHash];
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
            LMDBBlockDatabase* iface,
            uint32_t hgt,
            uint8_t  dup,
            uint16_t txIdx,
            BinaryDataRef txHash,
            map<BinaryData, StoredTx*> & stxMap,
            vector<StoredTx*> & pulledStx,
            uint64_t* additionalSize)
{
   StoredTx * stxptr;

   // Get the existing STX or make a new one
   auto txIter = stxMap.find(txHash);
   if(ITER_IN_MAP(txIter, stxMap))
      stxptr = txIter->second;
   else
   {
      //allocate new stx that will be cleaned after it is commited
      StoredTx *stxTemp = new StoredTx();
      iface->getStoredTx(*stxTemp, hgt, dup, txIdx);
      stxMap[txHash] = stxTemp;

      //keep track of this pointer for commit thread to delete
      pulledStx.push_back(stxTemp);

      stxptr = stxMap[txHash];
      if (additionalSize)
         *additionalSize += stxptr->numBytes_;
   }
   
   return stxptr;
}




static StoredScriptHistory* makeSureSSHInMap(
            LMDBBlockDatabase* iface,
            BinaryDataRef uniqKey,
            BinaryDataRef hgtX,
            map<BinaryData, StoredScriptHistory> & sshMap,
            uint64_t& additionalSize,
            uint32_t commitId,
            bool createIfDNE)
{
   //SCOPED_TIMER("makeSureSSHInMap");
   StoredScriptHistory * sshptr;

   // If already in Map
   map<BinaryData, StoredScriptHistory>::iterator iter = sshMap.find(uniqKey);
   if(ITER_IN_MAP(iter, sshMap))
   {
      //SCOPED_TIMER("___SSH_AlreadyInMap");
      sshptr = &(iter->second);
   }
   else
   {
      StoredScriptHistory sshTemp;
      
      iface->getStoredScriptHistorySummary(sshTemp, uniqKey);
      // sshTemp.alreadyScannedUpToBlk_ = getAppliedToHeightInDB(); TODO
      additionalSize += UPDATE_BYTES_SSH;

      if(sshTemp.isInitialized())
      {
         //SCOPED_TIMER("___SSH_AlreadyInDB");
         // We already have an SSH in DB -- pull it into the map
         sshMap[uniqKey] = sshTemp; 
         sshptr = &sshMap[uniqKey];
      }
      else
      {
         //SCOPED_TIMER("___SSH_NeedCreate");
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
   if (hgtX.getSize() == 4)
   {
      size_t prevSize = sshptr->subHistMap_.size();
      iface->fetchStoredSubHistory(*sshptr, hgtX, additionalSize, commitId, true, false);
      size_t newSize = sshptr->subHistMap_.size();

      additionalSize += (newSize - prevSize) * UPDATE_BYTES_SUBSSH;
   }

   sshptr->commitId_ = commitId;

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
BlockWriteBatcher::BlockWriteBatcher(
   const BlockDataManagerConfig &config,
   LMDBBlockDatabase* iface,
   bool forCommit
)
   : config_(config), iface_(iface),
   dbUpdateSize_(0), mostRecentBlockApplied_(0), isForCommit_(forCommit)
{}

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

BinaryData BlockWriteBatcher::applyBlockToDB(StoredHeader &sbh,
   ScrAddrFilter& scrAddrData)
{
   //TIMER_START("applyBlockToDBinternal");
   if(iface_->getValidDupIDForHeight(sbh.blockHeight_) != sbh.duplicateID_)
   {
      LOGERR << "Dup requested is not the main branch for the given height!";
      return BinaryData();
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
      applyTxToBatchWriteData(iter->second, &sud, scrAddrData);
   }

   // At this point we should have a list of STX and SSH with all the correct
   // modifications (or creations) to represent this block.  Let's apply it.
   sbh.blockAppliedToDB_ = true;
   sbhToUpdate_.push_back(&sbh);
   dbUpdateSize_ += sbh.numBytes_;

   BinaryData scannedBlockHash = sbh.thisHash_;

   { // we want to commit the undo data at the same time as actual changes   
      // Now actually write all the changes to the DB all at once
      // if we've gotten to that threshold
      if (dbUpdateSize_ > UPDATE_BYTES_THRESH)
      {
         thread committhread = commit();
         if (committhread.joinable())
            committhread.detach();
      }

      // Only if pruning, we need to store 
      // TODO: this is going to get run every block, probably should batch it 
      //       like we do with the other data...when we actually implement pruning
      //if(config_.pruneType == DB_PRUNE_ALL)
         //iface_->putStoredUndoData(sud);
   }

   //TIMER_STOP("applyBlockToDBinternal");
   return scannedBlockHash;
}

void BlockWriteBatcher::applyBlockToDB(uint32_t hgt, uint8_t dup, 
   ScrAddrFilter& scrAddrData)
{
   resetTransactions();

   preloadSSH(scrAddrData);

   StoredHeader* sbhPtr = new StoredHeader();
   iface_->getStoredHeader(*sbhPtr, hgt, dup);
   if (sbhPtr->blockHeight_ == UINT32_MAX)
   {
      LOGERR << "Failed to load block " << hgt << "," << dup;
      delete sbhPtr;
      return;
   }
   applyBlockToDB(*sbhPtr, scrAddrData);

   clearTransactions();
}


////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::undoBlockFromDB(StoredUndoData & sud, 
                                        ScrAddrFilter& scrAddrData)
{
   //SCOPED_TIMER("undoBlockFromDB");
   if (resetTxn_ == true)
      cleanUpSshToModify();

   resetTransactions();

   StoredHeader* sbhPtr = new StoredHeader();
   iface_->getStoredHeader(*sbhPtr, sud.blockHeight_, sud.duplicateID_);

   StoredHeader& sbh = *sbhPtr;
   if(!sbh.blockAppliedToDB_)
   {
      LOGERR << "This block was never applied to the DB...can't undo!";
      return /*false*/;
   }

   mostRecentBlockApplied_ = sud.blockHeight_;

   ///// Put the STXOs back into the DB which were removed by this block
   // Process the stxOutsRemovedByBlock_ in reverse order
   // Use int32_t index so that -1 != UINT32_MAX and we go into inf loop
   for(int32_t i=(int32_t)sud.stxOutsRemovedByBlock_.size()-1; i>=0; i--)
   {
      StoredTxOut & sudStxo = sud.stxOutsRemovedByBlock_[i];

      if (config_.armoryDbType != ARMORY_DB_SUPER)
      {
         if (!scrAddrData.hasScrAddress(sudStxo.getScrAddress()))
            continue;
         
         //UTxO is for one of our scrAddr, add it
         scrAddrData.addUTxO(sudStxo.getDBKey(false));
      }

      StoredTx * stxptr = makeSureSTXInMap( 
               iface_,
               sudStxo.blockHeight_,
               sudStxo.duplicateID_,
               sudStxo.txIndex_,
               sudStxo.parentHash_,
               stxToModify_, stxPulledFromDB_,
               &dbUpdateSize_);

      
      const uint16_t stxoIdx = sudStxo.txOutIndex_;
      map<uint16_t,StoredTxOut>::iterator iter = stxptr->stxoMap_.find(stxoIdx);

      if(config_.pruneType == DB_PRUNE_NONE)
      {
         // If full/super, we have the TxOut in DB, just need mark it unspent
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
         if(ITER_NOT_IN_MAP(iter, stxptr->stxoMap_))
         {
            LOGERR << "Somehow STXO DNE even though we should've just added it!";
            continue;
         }

         StoredTxOut & stxoReAdd = iter->second;
         BinaryData uniqKey = stxoReAdd.getScrAddress();

         BinaryData hgtX    = stxoReAdd.getHgtX();
         StoredScriptHistory* sshptr = makeSureSSHInMap(
               iface_, uniqKey, hgtX, sshToModify_, dbUpdateSize_,
               commitId_, true);

         if(sshptr==NULL)
         {
            LOGERR << "No SSH found for marking TxOut unspent on undo";
            continue;
         }

         // Readd the unspent at TxOut hgtX TxIOPair in the StoredScriptHistory
         sshptr->markTxOutUnspent(
            iface_,
            stxoReAdd.getDBKey(false),
            config_.armoryDbType,
            config_.pruneType,
            dbUpdateSize_,
            commitId_,
            stxoReAdd.getValue(),
            stxoReAdd.isCoinbase_,
            false
         );

         //delete the spent subssh at TxIn hgtX
         if (sudStxo.spentness_ == TXOUT_SPENT)
         {
            hgtX = sudStxo.spentByTxInKey_.getSliceCopy(0, 4);
            sshptr = makeSureSSHInMap(
               iface_, uniqKey, hgtX, sshToModify_, dbUpdateSize_, commitId_, true);

            if (sshptr != nullptr)
               sshptr->eraseSpentTxio(hgtX, sudStxo.getDBKey(false), commitId_);
         }

         // If multisig, we need to update the SSHs for individual addresses
         if(uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
         {
            vector<BinaryData> addr160List;
            BtcUtils::getMultisigAddrList(stxoReAdd.getScriptRef(), addr160List);
            for(uint32_t a=0; a<addr160List.size(); a++)
            {
               // Get the existing SSH or make a new one
               BinaryData uniqKey = HASH160PREFIX + addr160List[a];
               
               if (config_.armoryDbType != ARMORY_DB_SUPER &&
                   scrAddrData.hasScrAddress(uniqKey) == false)
                     continue;

               StoredScriptHistory* sshms = makeSureSSHInMap(iface_, uniqKey, 
                                                            stxoReAdd.getHgtX(),
                                                            sshToModify_, 
                                                            dbUpdateSize_,
                                                            commitId_,
                                                            true);
               sshms->markTxOutUnspent(
                  iface_,
                  stxoReAdd.getDBKey(false),
                  config_.armoryDbType,
                  config_.pruneType,
                  dbUpdateSize_,
                  commitId_,
                  stxoReAdd.getValue(),
                  stxoReAdd.isCoinbase_,
                  true
               );
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
            stxToModify_, stxPulledFromDB_,
            &dbUpdateSize_);

      for(int16_t txoIdx = (int16_t)stxptr->stxoMap_.size()-1; txoIdx >= 0; txoIdx--)
      {

         StoredTxOut & stxo    = stxptr->stxoMap_[txoIdx];
         BinaryData    stxoKey = stxo.getDBKey(false);
   
         // Then fetch the StoredScriptHistory of the StoredTxOut scraddress
         BinaryData uniqKey = stxo.getScrAddress();
         if (config_.armoryDbType != ARMORY_DB_SUPER)
         {
            if (!scrAddrData.hasScrAddress(uniqKey))
               continue;

            scrAddrData.eraseUTxO(stxoKey);
         }

         BinaryData hgtX    = stxo.getHgtX();
         StoredScriptHistory * sshptr = makeSureSSHInMap(
               iface_, uniqKey, 
               hgtX,
               sshToModify_, 
               dbUpdateSize_,
               commitId_,
               false);
   
   
         // If we are tracking that SSH, remove the reference to this OutPoint
         if(sshptr != NULL)
            sshptr->eraseTxio(stxoKey, commitId_);
   
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

               StoredScriptHistory* sshms = makeSureSSHInMap(
                     iface_,
                     uniqKey,
                     hgtX,
                     sshToModify_, 
                     dbUpdateSize_,
                     commitId_,
                     false
                  );
               sshms->eraseTxio(stxoKey, commitId_);
            }
         }
      }
   }

   // Finally, mark this block as UNapplied.
   sbh.blockAppliedToDB_ = false;
   sbhToUpdate_.push_back(sbhPtr);
   
   clearTransactions();
   
   if (dbUpdateSize_ > UPDATE_BYTES_THRESH)
   {
      thread committhread = commit();
      if (committhread.joinable())
         committhread.detach();
   }
}


////////////////////////////////////////////////////////////////////////////////
// Assume that stx.blockHeight_ and .duplicateID_ are set correctly.
// We created the maps and sets outside this function, because we need to keep
// a master list of updates induced by all tx in this block.  
// TODO:  Make sure that if Tx5 spends an input from Tx2 in the same 
//        block that it is handled correctly, etc.
bool BlockWriteBatcher::applyTxToBatchWriteData(
                        StoredTx &       thisSTX,
                        StoredUndoData * sud,
                        ScrAddrFilter& scrAddrData)
{
   //SCOPED_TIMER("applyTxToBatchWriteData");

   vector<size_t> TxInIndexes;
   BtcUtils::TxInCalcLength(thisSTX.dataCopy_.getPtr(), thisSTX.dataCopy_.getSize(),
                          &TxInIndexes);

   // We never expect thisSTX to already be in the map (other tx in the map
   // may be affected/retrieved multiple times).  
   if(KEY_IN_MAP(thisSTX.thisHash_, stxToModify_))
      LOGERR << "How did we already add this tx?";

   // I just noticed we never set TxOuts to TXOUT_UNSPENT.  Might as well do 
   // it here -- by definition if we just added this Tx to the DB, it couldn't
   // have been spent yet.
   
   for(StoredTxOut &stx : values(thisSTX.stxoMap_))
      stx.spentness_ = TXOUT_UNSPENT;

   // This tx itself needs to be added to the map, which makes it accessible 
   // to future tx in the same block which spend outputs from this tx, without
   // doing anything crazy in the code here

   if (config_.armoryDbType == ARMORY_DB_SUPER)
   {
      stxToModify_[thisSTX.thisHash_] = &thisSTX;
      dbUpdateSize_ += thisSTX.numBytes_;
   }
   
   // Go through and find all the previous TxOuts that are affected by this tx

   //TIMER_START("TxInParsing");

   for (uint32_t iin=0; iin < TxInIndexes.size() -1; iin++)
   {
      //TIMER_START("grabTxIn");
      // Get the OutPoint data of TxOut being spent
      const BinaryDataRef opTxHash = 
         thisSTX.dataCopy_.getSliceRef(TxInIndexes[iin], 32);

      if (opTxHash == BtcUtils::EmptyHash_)
      {
         //TIMER_STOP("grabTxIn");
         continue;
      }
      
      const uint32_t opTxoIdx = 
         READ_UINT32_LE(thisSTX.dataCopy_.getPtr() + TxInIndexes[iin] + 32);

      BinaryDataRef       fetchBy = opTxHash;
      StoredTx*           stxptr = nullptr;

      //TIMER_STOP("grabTxIn");

      //For scanning a predefined set of addresses, check if this txin 
      //consumes one of our utxo
      
      //leveraging the stx map in RAM
      //TIMER_START("leverageStxInRAM");
      auto stxIter = stxToModify_.find(opTxHash);
      if (ITER_IN_MAP(stxIter, stxToModify_))
         stxptr = stxIter->second;
      //TIMER_STOP("leverageStxInRAM");

      if (config_.armoryDbType != ARMORY_DB_SUPER)
      {
         if (stxptr != nullptr)
         {
            const StoredTxOut& stxo = stxptr->stxoMap_[opTxoIdx];
            
            //Since this STX is already in map, we have processed it, thus
            //all the relevant outpoints of this STX are already in RAM
            if (scrAddrData.hasUTxO(stxo.getDBKey(false)) < 1)
               continue;

            scrAddrData.eraseUTxO(stxo.getDBKey(false));
            
            if (stxToModify_.insert(make_pair(thisSTX.thisHash_, &thisSTX)).second == true)
               dbUpdateSize_ += thisSTX.numBytes_;
         }
         else
         {
            //TIMER_STOP("leverageStxInRAM");
            //TIMER_START("fecthOutPointFromDB");
            
            //grab UTxO DBkey for comparison first
            BinaryData          txOutDBkey;
            iface_->getStoredTx_byHash(opTxHash, nullptr, &txOutDBkey);
            if (txOutDBkey.getSize() != 6)
               continue;
            txOutDBkey.append(WRITE_UINT16_BE(opTxoIdx));

            int8_t hasKey = scrAddrData.hasUTxO(txOutDBkey);
         
            //TIMER_STOP("fecthOutPointFromDB");

            if (hasKey == 0) continue;
            else if (hasKey == -1)
            {
               //TIMER_START("fullFecthOutPointFromDB");

               fetchBy = txOutDBkey.getSliceRef(0, 6);
               stxptr = makeSureSTXInMap(iface_, fetchBy,
                  stxToModify_, stxPulledFromDB_, &dbUpdateSize_);

               const StoredTxOut& stxo = stxptr->stxoMap_[opTxoIdx];

               if (!scrAddrData.hasScrAddress(stxo.getScrAddress()))
               {
                  //TIMER_STOP("fullFecthOutPointFromDB");
                  continue;
               }

               if (stxToModify_.insert(make_pair(thisSTX.thisHash_, &thisSTX)).second == true)
                  dbUpdateSize_ += thisSTX.numBytes_;

               //TIMER_STOP("fullFecthOutPointFromDB");
            }

            //if we got this far this txin spends one of our utxo, 
            //remove it from utxo set
            scrAddrData.eraseUTxO(txOutDBkey);
         }
      }

      //TIMER_START("CommitTxIn");

      // This will fetch the STX from DB and put it in the stxToModify
      // map if it's not already there.  Or it will do nothing if it's
      // already part of the map.  In both cases, it returns a pointer
      // to the STX that will be written to DB that we can modify.
      if (stxptr == nullptr)
      {
         stxptr = makeSureSTXInMap(iface_, fetchBy, stxToModify_,
                                   stxPulledFromDB_, &dbUpdateSize_);
         dbUpdateSize_ += stxptr->numBytes_;
      }

      StoredTxOut & stxo   = stxptr->stxoMap_[opTxoIdx];
      BinaryData    uniqKey   = stxo.getScrAddress();

      // Update the stxo by marking it spent by this Block:TxIndex:TxInIndex
      const map<uint16_t,StoredTxOut>::iterator iter = stxptr->stxoMap_.find(opTxoIdx);
      
      // Some sanity checks
      if(ITER_NOT_IN_MAP(iter, stxptr->stxoMap_))
      {
         LOGERR << "Needed to get OutPoint for a TxIn, but DNE";
         //TIMER_STOP("CommitTxIn");
         continue;
      }

      // We're aliasing this because "iter->second" is not clear at all
      StoredTxOut & stxoSpend = iter->second;
   
      /* This would be useful if we didn't sometimes apply a block twice
      if(stxoSpend.spentness_ == TXOUT_SPENT)
      {
         LOGERR << "Trying to mark TxOut spent, but it's already marked";
         TIMER_STOP("CommitTxIn");
         continue;
      }
      */

      // Just about to {remove-if-pruning, mark-spent-if-not} STXO
      // Record it in the StoredUndoData object
      /*if(sud != NULL)
         sud->stxOutsRemovedByBlock_.push_back(stxoSpend);*/

      // Need to modify existing UTXOs, so that we can delete or mark as spent
      stxoSpend.spentness_      = TXOUT_SPENT;
      stxoSpend.spentByTxInKey_ = thisSTX.getDBKeyOfChild(iin, false);

      ////// Now update the SSH to show this TxIOPair was spent
      // Same story as stxToModify above, except this will actually create a new
      // SSH if it doesn't exist in the map or the DB
      BinaryData hgtX = stxo.getHgtX();

      StoredScriptHistory* sshptr = makeSureSSHInMap(
            iface_,
            uniqKey,
            hgtX,
            sshToModify_,
            dbUpdateSize_,
            commitId_,
            true
         );

      // update the txio in its subSSH
      sshptr->markTxOutSpent(
         iface_,
         stxoSpend.getDBKey(false),
         thisSTX.getDBKeyOfChild(iin, false),
         commitId_,
         config_.armoryDbType,
         config_.pruneType
      );

      //mirror the spent txio at txin height
      sshptr->insertSpentTxio(stxoSpend.getDBKey(false), 
                              thisSTX.getDBKeyOfChild(iin, false),
                              dbUpdateSize_, commitId_);
      //TIMER_STOP("CommitTxIn");
   }

   //TIMER_STOP("TxInParsing");

   //TIMER_START("TxOutParsing");
   // We don't need to update any TXDATA, since it is part of writing thisSTX
   // to the DB ... but we do need to update the StoredScriptHistory objects
   // with references to the new [unspent] TxOuts
   for(StoredTxOut& stxoToAdd : values(thisSTX.stxoMap_))
   {
      //TIMER_START("getTxOutScrAddrAndHgtx");
      BinaryData uniqKey = stxoToAdd.getScrAddress();
      BinaryData hgtX    = stxoToAdd.getHgtX();
      //TIMER_STOP("getTxOutScrAddrAndHgtx");

      if (config_.armoryDbType != ARMORY_DB_SUPER)
      {
         if (!scrAddrData.hasScrAddress(uniqKey))
            continue;

         //if we got this far, this utxo points to one of the address in our 
         //list, add it to the utxo set
         scrAddrData.addUTxO(stxoToAdd.getDBKey(false));
         
         if (stxToModify_.insert(make_pair(thisSTX.thisHash_, &thisSTX)).second == true)
            dbUpdateSize_ += thisSTX.numBytes_;
      }
      
      //TIMER_START("createSSHentryForTXOUT");
      StoredScriptHistory* sshptr = makeSureSSHInMap(
            iface_,
            uniqKey,
            hgtX,
            sshToModify_,
            dbUpdateSize_,
            commitId_,
            true
         );

      // Add reference to the next STXO to the respective SSH object
      sshptr->markTxOutUnspent(
         iface_,
         stxoToAdd.getDBKey(false),
         config_.armoryDbType,
         config_.pruneType,
         dbUpdateSize_,
         commitId_,
         stxoToAdd.getValue(),
         stxoToAdd.isCoinbase_,
         false
      );
      //TIMER_STOP("createSSHentryForTXOUT");

      // If this was a multisig address, add a ref to each individual scraddr
      if(uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
      {
         vector<BinaryData> addr160List;
         BtcUtils::getMultisigAddrList(stxoToAdd.getScriptRef(), addr160List);
         for(uint32_t a=0; a<addr160List.size(); a++)
         {
            // Get the existing SSH or make a new one
            BinaryData uniqKey = HASH160PREFIX + addr160List[a];
            
            if (config_.armoryDbType != ARMORY_DB_SUPER)
            {
               //do not maintain multisig activity on related scrAddr unless
               //in supernode
               if (scrAddrData.hasScrAddress(uniqKey))
                  continue;
            }

            StoredScriptHistory* sshms = makeSureSSHInMap(
                  iface_,
                  uniqKey,
                  hgtX,
                  sshToModify_,
                  dbUpdateSize_,
                  commitId_,
                  true
               );
            sshms->markTxOutUnspent(
               iface_,
               stxoToAdd.getDBKey(false),
               config_.armoryDbType,
               config_.pruneType,
               dbUpdateSize_,
               commitId_,
               stxoToAdd.getValue(),
               stxoToAdd.isCoinbase_,
               true
            );
         }
      }
   }

   //TIMER_STOP("TxOutParsing");

   return true;
}

////////////////////////////////////////////////////////////////////////////////
thread BlockWriteBatcher::commit(bool finalCommit)
{
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
   }
   else
      l.unlock();

   //create a BWB for commit (pass true to the constructor)
   BlockWriteBatcher *bwbSwapPtr = new BlockWriteBatcher(config_, iface_, true);

   //LOGWARN << "dumping " << dbUpdateSize_ << " bytes in the DB";
   
   bwbSwapPtr->commitId_ = commitId_++;

   bwbSwapPtr->searchForSSHKeysToDelete(sshToModify_);

   bwbSwapPtr->sbhToUpdate_      = std::move(sbhToUpdate_);
   bwbSwapPtr->stxToModify_      = std::move(stxToModify_);
   bwbSwapPtr->stxPulledFromDB_  = std::move(stxPulledFromDB_);
   
   for (const auto& ssh : sshToModify_)
   {
      if (ssh.second.commitId_ == bwbSwapPtr->commitId_ || 
          config_.armoryDbType != ARMORY_DB_SUPER)
      {
         //SSH records are accessed very often and are light so they are copied
         //(without the subSSH entries) rather than referenced
         StoredScriptHistory sshToCopy;
         sshToCopy.totalTxioCount_ = ssh.second.totalTxioCount_;
         sshToCopy.totalUnspent_ = ssh.second.totalUnspent_;
         sshToCopy.uniqueKey_ = ssh.second.uniqueKey_;
         sshToCopy.version_ = ssh.second.version_;
         sshToCopy.alreadyScannedUpToBlk_ = mostRecentBlockApplied_;

         bwbSwapPtr->sshToModify_[ssh.first] = sshToCopy;
      }

      for (const auto& subssh : ssh.second.subHistMap_)
      {
         if (subssh.second.commitId_ == bwbSwapPtr->commitId_ && 
             subssh.second.txioMap_.size() != 0)
            bwbSwapPtr->subSshToApply_.push_back(
               const_cast<StoredSubHistory*>(&subssh.second));
      }
   }

   bwbSwapPtr->dbUpdateSize_ = dbUpdateSize_;
   bwbSwapPtr->mostRecentBlockApplied_ = mostRecentBlockApplied_ +1;
   bwbSwapPtr->updateSDBI_ = updateSDBI_;

   bwbSwapPtr->parent_ = this;
      
   dbUpdateSize_ = 0;

   l.lock();
   thread committhread(commitThread, bwbSwapPtr);

   return committhread;
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::searchForSSHKeysToDelete(
   map<BinaryData, StoredScriptHistory>& sshToModify)
{
   for(map<BinaryData, StoredScriptHistory>::iterator iterSSH  = sshToModify.begin();
       iterSSH != sshToModify.end(); )
   {
      // get our next one in case we delete the current
      map<BinaryData, StoredScriptHistory>::iterator nextSSHi = iterSSH;
      ++nextSSHi;

      StoredScriptHistory & ssh = iterSSH->second;
      
      for (const auto& subssh : ssh.subHistMap_)
      {
         if (subssh.second.txioMap_.size() == 0 && 
             subssh.second.commitId_ == commitId_)
            keysToDelete_.insert(subssh.second.getDBKey(true));
      }
   
      // If the full SSH is empty (not just sub history), mark it to be removed
      // *ONLY IN SUPERNODE* need it in full mode to update the ssh last seen 
      // block

      if (iterSSH->second.totalTxioCount_ == 0 && 
          config_.armoryDbType == ARMORY_DB_SUPER)
      {
         keysToDelete_.insert(iterSSH->second.getDBKey(true));
         sshToModify.erase(iterSSH);
      }
      
      iterSSH = nextSSHi;
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::preloadSSH(const ScrAddrFilter& sasd)
{
   //In full mode, the sshToModify_ container is not wiped after each commit.
   //Instead, all SSH for tracked scrAddr, since we know they're the onyl one
   //that will get any traffic, and in order to update all alreadyScannedUpToBlk_
   //members each commit

   //pass a 0 size BinaryData to avoid loading any subSSH

   if (config_.armoryDbType != ARMORY_DB_SUPER)
   {
      uint64_t updateSize;
      BinaryData hgtX(0);

      for (auto saPair : sasd.getScrAddrMap())
         makeSureSSHInMap(iface_, saPair.first, hgtX, sshToModify_, updateSize, 0, true);
   }
}

////////////////////////////////////////////////////////////////////////////////
void* BlockWriteBatcher::commitThread(void *argPtr)
{
   BlockWriteBatcher* bwbPtr = static_cast<BlockWriteBatcher*>(argPtr);
   unique_lock<mutex> lock(bwbPtr->parent_->writeLock_);

   //create readwrite transactions to apply data to DB
   bwbPtr->txn_.open(&bwbPtr->iface_->dbEnv_, LMDB::ReadWrite);

   // Check for any SSH objects that are now completely empty.  If they exist,
   // they should be removed from the DB, instead of simply written as empty
   // objects
//   TIMER_START("commitToDB");

   {
      for (auto& sshPair : bwbPtr->sshToModify_)
         bwbPtr->iface_->putStoredScriptHistorySummary(sshPair.second);
      
      for (auto subSshPtr : bwbPtr->subSshToApply_)
      {
         //only apply if subssh wasnt modified
         while (subSshPtr->accessing_.test_and_set(memory_order_relaxed) == true);
            //if (subSshPtr->commitId_ == bwbPtr->commitId_)
         bwbPtr->iface_->putStoredSubHistory(*subSshPtr);
         
         subSshPtr->accessing_.clear(memory_order_relaxed);
      }
      
      bwbPtr->txn_.commit();
      bwbPtr->txn_.begin();
      
      for (auto& stxPair : bwbPtr->stxToModify_)
         bwbPtr->iface_->updateStoredTx(*stxPair.second);
      
      bwbPtr->txn_.commit();
      bwbPtr->txn_.begin();

      for (auto& sbh : bwbPtr->sbhToUpdate_)
         updateBlkDataHeader(bwbPtr->config_, bwbPtr->iface_, *sbh);

      bwbPtr->txn_.commit();
      bwbPtr->txn_.begin();

      for (auto& toDel : bwbPtr->keysToDelete_)
         bwbPtr->iface_->deleteValue(BLKDATA, toDel);
      
      bwbPtr->txn_.commit();
      bwbPtr->txn_.begin();


      if (bwbPtr->mostRecentBlockApplied_ != 0 && bwbPtr->updateSDBI_ == true)
      {
         StoredDBInfo sdbi;
         bwbPtr->iface_->getStoredDBInfo(BLKDATA, sdbi);
         if (!sdbi.isInitialized())
            LOGERR << "How do we have invalid SDBI in applyMods?";
         else
         {
            //save top block height
            sdbi.appliedToHgt_ = bwbPtr->mostRecentBlockApplied_;

            //save top block hash
            if (bwbPtr->sbhToUpdate_.size() > 0)
            {
               auto topBlockHeader = bwbPtr->sbhToUpdate_.rbegin();
               sdbi.topScannedBlkHash_ = (*topBlockHeader)->getBlockHeaderCopy().getThisHash();
            }
            bwbPtr->iface_->putStoredDBInfo(BLKDATA, sdbi);
         }
      }

      //final commit
      bwbPtr->clearTransactions();
   }
   
   BlockWriteBatcher* bwbParent = bwbPtr->parent_;
   
   //signal the transaction reset
   bwbParent->resetTxn_ = true;
   
   //signal DB is ready for new commit
   lock.unlock();
   
   //clean up
   for (auto storedTxPtr : bwbPtr->stxPulledFromDB_)
      delete storedTxPtr;

   for (auto storedHeader : bwbPtr->sbhToUpdate_)
      delete storedHeader;

   delete bwbPtr;

/*   TIMER_STOP("commitToDB");
   LOGWARN << "Commited";*/
   
   return nullptr;
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::resetTransactions(void)
{
   resetTxn_ = false;
   
   txn_.commit();
   txn_.open(&iface_->dbEnv_, LMDB::ReadOnly);
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::clearTransactions(void)
{
   txn_.commit();
}

////////////////////////////////////////////////////////////////////////////////
void* BlockWriteBatcher::grabBlocksFromDB(void *in)
{
   /***
   Grab blocks from the DB, put them in the tempBlockVec
   ***/

   //mon
   BlockWriteBatcher* const dis = static_cast<BlockWriteBatcher*>(in);

   //read only db txn
   LMDBEnv::Transaction tx(&dis->iface_->dbEnv_, LMDB::ReadOnly);

   vector<StoredHeader*> shVec;
   uint32_t hgt = dis->tempBlockData_->topLoadedBlock_;
   uint32_t memoryLoad = 0; 

   unique_lock<mutex> uniqLock(dis->grabThreadLock_, defer_lock);

   while (memoryLoad + dis->tempBlockData_->bufferLoad_
      < UPDATE_BYTES_THRESH / 2)
   {
      if (hgt > dis->tempBlockData_->endBlock_)
         break;

      uint8_t dupID = dis->iface_->getValidDupIDForHeight(hgt);
      if (dupID == UINT8_MAX)
      {
         dis->tempBlockData_->endBlock_ = hgt - 1;
         LOGERR << "No block in DB at height " << hgt;
         break;
      }
      
      StoredHeader* sbhPtr = new StoredHeader();
      if (!dis->iface_->getStoredHeader(*sbhPtr, hgt, dupID))
      {
         dis->tempBlockData_->endBlock_ = hgt - 1;
         LOGERR << "No block in DB at height " << hgt;
         break;
      }

      memoryLoad += sbhPtr->numBytes_;
      shVec.push_back(sbhPtr);

      ++hgt;
   }

   //lock tempBlockData_
   while (dis->tempBlockData_->lock_.fetch_or(1, memory_order_acquire));

   dis->tempBlockData_->sbhVec_.insert(dis->tempBlockData_->sbhVec_.end(),
      shVec.begin(), shVec.end());

   dis->tempBlockData_->bufferLoad_ += memoryLoad;
   dis->tempBlockData_->fetching_ = false;
   dis->tempBlockData_->topLoadedBlock_ = hgt;

   //release lock
   dis->tempBlockData_->lock_.store(0, memory_order_release);
   
   dis->grabThreadCondVar_.notify_all();

   return nullptr;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BlockWriteBatcher::applyBlocksToDB(ProgressFilter &progress)
{
   if (tempBlockData_->endBlock_ == 0)
   {
      LOGERR << "Top block is 0, nothing to scan";
      throw std::range_error("Top block is 0, nothing to scan");
   }

   BinaryData lastScannedBlockHash;
   resetTransactions();

   thread grabThread;
   try
   {
      unique_lock<mutex> uniqLock(grabThreadLock_);

      uint64_t totalBlockDataProcessed=0;

      for (uint32_t i = tempBlockData_->startBlock_;
         i <= tempBlockData_->endBlock_;
         i++)
      {
         StoredHeader* sbh;
         uint32_t vectorIndex;
         
         if (resetTxn_ == true)
         {
            resetTransactions();
            cleanUpSshToModify();
         }

         if (!tempBlockData_->fetching_)
         if (tempBlockData_->topLoadedBlock_ <=
            tempBlockData_->endBlock_ &&
            tempBlockData_->bufferLoad_ < UPDATE_BYTES_THRESH / 6)
         {
            //block buffer is below half load, refill it in a side thread
            tempBlockData_->fetching_ = true;

            //this is a single entrant block, so there's only ever one 
            //grabBlocksFromDB thread running. Preemptively detach tID, so that
            //the current grabThread is joinable (for the clean up process)
            if(grabThread.joinable())
               grabThread.detach();
            grabThread = thread(grabBlocksFromDB, this);
         }

         //make sure there's enough data to grab from the block buffer
         grabThreadCondVar_.wait(uniqLock, 
            [&, this]{return (i < this->tempBlockData_->topLoadedBlock_ ||
                              i > this->tempBlockData_->endBlock_); });

         if (i > tempBlockData_->endBlock_)
            break;

         //grab lock
         while (tempBlockData_->lock_.fetch_or(1, memory_order_relaxed));
         vectorIndex = i - tempBlockData_->blockOffset_;

         StoredHeader** sbhEntry = &tempBlockData_->sbhVec_[vectorIndex];
         sbh = *sbhEntry;
         *sbhEntry = nullptr;

         //clean up used vector indexes
         uint32_t nParsedBlocks = i - tempBlockData_->startBlock_;
         if (nParsedBlocks > 0 && (nParsedBlocks % 10000) == 0)
         {
            tempBlockData_->sbhVec_.erase(
               tempBlockData_->sbhVec_.begin(),
               tempBlockData_->sbhVec_.begin() + 10000);

            tempBlockData_->blockOffset_ += 10000;
         }

         //release lock
         tempBlockData_->lock_.store(0, memory_order_relaxed);

         uint32_t blockSize = sbh->numBytes_;

         //scan block
;
         lastScannedBlockHash = 
            applyBlockToDB(*sbh, tempBlockData_->scrAddrFilter_);
 
         //decrement bufferload
         if (tempBlockData_->bufferLoad_ < blockSize)
         {
            LOGWARN << "bufferlLoad_ < blockSize!";
            throw;
         }
         tempBlockData_->bufferLoad_ -= blockSize;

         if (i % 2500 == 2499)
            LOGWARN << "Finished applying blocks up to " << (i + 1);
         
         totalBlockDataProcessed += blockSize;
         progress.advance(totalBlockDataProcessed);
      }
      
      if (grabThread.joinable())
         grabThread.join();

      //join on grabThread before deleting the container shared with the thread
      delete tempBlockData_;
      tempBlockData_ = nullptr;

      clearTransactions();
   }
   catch (...)
   {
      clearTransactions();
      
      if (grabThread.joinable())
         grabThread.join();
      
      //join on grabThread before deleting the container shared with the thread
      delete tempBlockData_;
      tempBlockData_ = nullptr;
      
      throw;
   }
   
   if (grabThread.joinable())
      grabThread.join();

   return lastScannedBlockHash;
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::cleanUpSshToModify(void)
{
   auto sshIter = sshToModify_.begin();

   while (sshIter != sshToModify_.end())
   {
      auto subSshIter = sshIter->second.subHistMap_.begin();
      while (subSshIter != sshIter->second.subHistMap_.end())
      {
         if (subSshIter->second.commitId_ == deleteId_)
            sshIter->second.subHistMap_.erase(subSshIter++);
         else
            ++subSshIter;
      }

      if (sshIter->second.subHistMap_.size() == 0 &&
         config_.armoryDbType ==
         ARMORY_DB_SUPER)
         sshToModify_.erase(sshIter++);
      else
         ++sshIter;
   }

   ++deleteId_;
}


////////////////////////////////////////////////////////////////////////////////
BinaryData BlockWriteBatcher::scanBlocks(
   ProgressFilter &prog,
   uint32_t startBlock, uint32_t endBlock, 
   ScrAddrFilter& scf
)
{
   //TIMER_START("applyBlockRangeToDBIter");
   
   preloadSSH(scf);

   tempBlockData_ = new LoadedBlockData(startBlock, endBlock, scf);
   grabBlocksFromDB(this);

   return applyBlocksToDB(prog);

   /*TIMER_STOP("applyBlockRangeToDBIter");

   double applyBlockRangeToDBIter = TIMER_READ_SEC("applyBlockRangeToDBIter");
   LOGWARN << "applyBlockRangeToDBIter: " << applyBlockRangeToDBIter << " sec";

   double applyBlockToDBinternal = TIMER_READ_SEC("applyBlockToDBinternal");
   LOGWARN << "applyBlockToDBinternal: " << applyBlockToDBinternal << " sec";

   double applyTxToBatchWriteData = TIMER_READ_SEC("applyTxToBatchWriteData");
   LOGWARN << "applyTxToBatchWriteData: " << applyTxToBatchWriteData << " sec";

   double TxInParsing = TIMER_READ_SEC("TxInParsing");
   LOGWARN << "TxInParsing: " << TxInParsing << " sec";

   double grabTxIn = TIMER_READ_SEC("grabTxIn");
   LOGWARN << "grabTxIn: " << grabTxIn << " sec";

   double leverageStxInRAM = TIMER_READ_SEC("leverageStxInRAM");
   LOGWARN << "leverageStxInRAM: " << leverageStxInRAM << " sec";

   double fecthOutPointFromDB = TIMER_READ_SEC("fecthOutPointFromDB");
   LOGWARN << "fecthOutPointFromDB: " << fecthOutPointFromDB << " sec";

   double fullFecthOutPointFromDB = TIMER_READ_SEC("fullFecthOutPointFromDB");
   LOGWARN << "fullFecthOutPointFromDB: " << fullFecthOutPointFromDB << " sec";

   double CommitTxIn = TIMER_READ_SEC("CommitTxIn");
   LOGWARN << "CommitTxIn: " << CommitTxIn << " sec";

   double TxOutParsing = TIMER_READ_SEC("TxOutParsing");
   LOGWARN << "TxOutParsing: " << TxOutParsing << " sec";

   double getTxOutScrAddrAndHgtx = TIMER_READ_SEC("getTxOutScrAddrAndHgtx");
   LOGWARN << "getTxOutScrAddrAndHgtx: " << getTxOutScrAddrAndHgtx << " sec";

   double createSSHentryForTXOUT = TIMER_READ_SEC("createSSHentryForTXOUT");
   LOGWARN << "createSSHentryForTXOUT: " << createSSHentryForTXOUT << " sec";

   double commitToDB = TIMER_READ_SEC("commitToDB");
   LOGWARN << "commitToDB: " << commitToDB << " sec";*/
}

// kate: indent-width 3; replace-tabs on;
