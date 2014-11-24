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
shared_ptr<StoredTxOut>& BlockWriteBatcher::makeSureSTXOInMap(
            LMDBBlockDatabase* iface,
            BinaryDataRef txHash, 
            uint16_t txoId)
{
   // Get the existing STX or make a new one
   auto& stxoMap = stxoToModify_[txHash];

   auto& stxo = stxoMap[txoId];

   if (!stxo)
   {
      stxo.reset(new StoredTxOut);
      BinaryData dbKey;
      iface->getStoredTx_byHash(txHash, nullptr, &dbKey);
      dbKey.append(WRITE_UINT16_BE(txoId));
      iface->getStoredTxOut(*stxo.get(), dbKey);

      dbUpdateSize_ += sizeof(StoredTxOut) + stxo->dataCopy_.getSize();
   }
   
   return stxo;
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::addStxToSTXOMap(const shared_ptr<PulledTx>& thisTx)
{
   auto& stxoMap = stxoToModify_[thisTx->thisHash_];

   for (auto& stxo : thisTx->stxoMap_)
   {
      auto wasInserted = stxoMap.insert(stxo);
      if (wasInserted.second == true)
         dbUpdateSize_ += sizeof(StoredTxOut) + stxo.second->dataCopy_.getSize();
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockWriteBatcher::addStxoToSTXOMap(const shared_ptr<StoredTxOut>& thisTxOut)
{
   auto& stxoMap = stxoToModify_[thisTxOut->parentHash_];

   auto wasInserted = stxoMap.insert({ thisTxOut->txOutIndex_, thisTxOut });
   if(wasInserted.second == true)
      dbUpdateSize_ += sizeof(StoredTxOut) + thisTxOut->dataCopy_.getSize();
}

////////////////////////////////////////////////////////////////////////////////
bool BlockWriteBatcher::lookForSTXOInMap(const BinaryData& txHash, 
   const uint16_t& txoId, shared_ptr<StoredTxOut>& txOut) const
{
   //TIMER_START("leverageStxInRAM");

   auto stxIter = stxoToModify_.find(txHash);
   if (stxIter == stxoToModify_.end())
      return false;

   auto stxoIter = stxIter->second.find(txoId);
   if (stxoIter == stxIter->second.end())
      return false;

   txOut = stxoIter->second;

   //TIMER_STOP("leverageStxInRAM");
   return true;
}

////////////////////////////////////////////////////////////////////////////////
static StoredScriptHistory* makeSureSSHInMap_BlindFetch(
   LMDBBlockDatabase* iface,
   BinaryDataRef uniqKey,
   BinaryDataRef hgtX,
   map<BinaryData, StoredScriptHistory> & sshMap,
   uint64_t& additionalSize,
   uint32_t commitId,
   uint32_t currentBlockHeight,
   bool forceFetch)
{
   //SCOPED_TIMER("makeSureSSHInMap");
   StoredScriptHistory * sshptr;

   // If already in Map
   map<BinaryData, StoredScriptHistory>::iterator iter = sshMap.find(uniqKey);
   if (ITER_IN_MAP(iter, sshMap))
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

      if (sshTemp.isInitialized())
      {
         //SCOPED_TIMER("___SSH_AlreadyInDB");
         // We already have an SSH in DB -- pull it into the map
         sshMap[uniqKey] = sshTemp;
         sshptr = &sshMap[uniqKey];
      }
      else
      {
         sshMap[uniqKey] = StoredScriptHistory();
         sshptr = &sshMap[uniqKey];
         sshptr->uniqueKey_ = uniqKey;
      }
   }

   if (hgtX.getSize() == 4)
   {
      size_t prevSize = sshptr->subHistMap_.size();
      
      auto subIter = sshptr->subHistMap_.find(hgtX);
      if (subIter == sshptr->subHistMap_.end())
      {
         uint32_t fetchHeight = DBUtils::hgtxToHeight(hgtX);
         BinaryData key = sshptr->uniqueKey_ + hgtX;

         StoredSubHistory subssh;
         subssh.uniqueKey_ = sshptr->uniqueKey_;
         subssh.hgtX_ = hgtX;

         //only fetch if the ssh wasnt scanned up to this point, otherwise create.
         if (fetchHeight < currentBlockHeight || forceFetch)
         {
            BinaryRefReader brr = iface->getValueReader(BLKDATA, DB_PREFIX_SCRIPT, key);
            if (brr.getSize() > 0)
               subssh.unserializeDBValue(brr);
         }
         
         sshptr->mergeSubHistory(subssh, additionalSize, commitId);
      }

      size_t newSize = sshptr->subHistMap_.size();
      additionalSize += (newSize - prevSize) * UPDATE_BYTES_SUBSSH;
   }

   sshptr->commitId_ = commitId;

   return sshptr;
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

BinaryData BlockWriteBatcher::applyBlockToDB(shared_ptr<PulledBlock>& pb,
   ScrAddrFilter& scrAddrData, bool forceUpdateValue)
{
   //TIMER_START("applyBlockToDBinternal");
   if(iface_->getValidDupIDForHeight(pb->blockHeight_) != pb->duplicateID_)
   {
      LOGERR << "Dup requested is not the main branch for the given height!";
      return BinaryData();
   }
   else
      pb->isMainBranch_ = true;
   
   mostRecentBlockApplied_ = pb->blockHeight_;

   // We will accumulate undoData as we apply the tx
   StoredUndoData sud;
   sud.blockHash_   = pb->thisHash_;
   sud.blockHeight_ = pb->blockHeight_;
   sud.duplicateID_ = pb->duplicateID_;
   
   // Apply all the tx to the update data
   for (auto& stx : pb->stxMap_)
   {
      if (stx.second->dataCopy_.getSize() == 0)
      {
         LOGERR << "bad STX data in applyBlockToDB at height " << pb->blockHeight_;
         throw std::range_error("bad STX data while applying blocks");
      }

      applyTxToBatchWriteData(stx.second, &sud, scrAddrData, forceUpdateValue);
   }

   // At this point we should have a list of STX and SSH with all the correct
   // modifications (or creations) to represent this block.  Let's apply it.
   pb->blockAppliedToDB_ = true;
   sbhToUpdate_.push_back(pb);
   dbUpdateSize_ += pb->numBytes_;

   BinaryData scannedBlockHash = pb->thisHash_;

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

   shared_ptr<PulledBlock> pb(new PulledBlock);
   pullBlockFromDB(pb, hgt, dup);
   if (pb->blockHeight_ == UINT32_MAX)
   {
      LOGERR << "Failed to load block " << hgt << "," << dup;
      return;
   }
   applyBlockToDB(pb, scrAddrData, true);

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

   shared_ptr<PulledBlock> pb(new PulledBlock);
   pullBlockFromDB(pb, sud.blockHeight_, sud.duplicateID_);

   if(!pb->blockAppliedToDB_)
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
         
         //UTxO is for one of our scrAddr, add it
         scrAddrData.addUTxO(sudStxo.getDBKey(false));
      }

      shared_ptr<StoredTxOut>& stxo = makeSureSTXOInMap( 
               iface_,
               sudStxo.parentHash_,
               stxoIdx);

      if(config_.pruneType == DB_PRUNE_NONE)
      {
         // If full/super, we have the TxOut in DB, just need mark it unspent
         if(stxo->spentness_ == TXOUT_UNSPENT || 
            stxo->spentByTxInKey_.getSize() == 0 )
         {
            LOGERR << "STXO needs to be re-added/marked-unspent but it";
            LOGERR << "was already declared unspent in the DB";
         }
         
         stxo->spentness_ = TXOUT_UNSPENT;
         stxo->spentByTxInKey_ = BinaryData(0);
      }
      else
      {
         // If we're pruning, we should have the Tx in the DB, but without the
         // TxOut because it had been pruned by this block on the forward op

         stxo->spentness_      = TXOUT_UNSPENT;
         stxo->spentByTxInKey_ = BinaryData(0);
      }


      {
         ////// Finished updating STX, now update the SSH in the DB
         // Updating the SSH objects works the same regardless of pruning

         BinaryData uniqKey = stxo->getScrAddress();

         BinaryData hgtX    = stxo->getHgtX();
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
            stxo->getDBKey(false),
            config_.armoryDbType,
            config_.pruneType,
            dbUpdateSize_,
            commitId_,
            stxo->getValue(),
            stxo->isCoinbase_,
            false, true
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
            BtcUtils::getMultisigAddrList(stxo->getScriptRef(), addr160List);
            for(uint32_t a=0; a<addr160List.size(); a++)
            {
               // Get the existing SSH or make a new one
               BinaryData uniqKey = HASH160PREFIX + addr160List[a];
               
               if (config_.armoryDbType != ARMORY_DB_SUPER &&
                   scrAddrData.hasScrAddress(uniqKey) == false)
                     continue;

               StoredScriptHistory* sshms = makeSureSSHInMap(iface_, uniqKey, 
                                                            stxo->getHgtX(),
                                                            sshToModify_, 
                                                            dbUpdateSize_,
                                                            commitId_,
                                                            true);
               sshms->markTxOutUnspent(
                  iface_,
                  stxo->getDBKey(false),
                  config_.armoryDbType,
                  config_.pruneType,
                  dbUpdateSize_,
                  commitId_,
                  stxo->getValue(),
                  stxo->isCoinbase_,
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
   for(int16_t itx=pb->numTx_-1; itx>=0; itx--)
   {
      // Ironically, even though I'm using hgt & dup, I still need the hash
      // in order to key the stxToModify map
      BinaryData txHash = iface_->getHashForDBKey(pb->blockHeight_,
                                                  pb->duplicateID_,
                                                  itx);

      StoredTx stx;
      if (!iface_->getStoredTx(stx, txHash))
      {
         LOGERR << "could not grab STX for hash: " << txHash.toHexStr(false);
         throw std::runtime_error("iface->getStoredTx failed in makeSureSTXInMap");
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

         shared_ptr<StoredTxOut> stxoSP(new StoredTxOut);
         *stxoSP = stxo;
         addStxoToSTXOMap(stxoSP);
      }
   }

   // Finally, mark this block as UNapplied.
   pb->blockAppliedToDB_ = false;
   sbhToUpdate_.push_back(pb);
   
   clearTransactions();
   
   if (dbUpdateSize_ > UPDATE_BYTES_THRESH)
   {
      thread committhread = commit();
      if (committhread.joinable())
         committhread.detach();
   }
}

bool BlockWriteBatcher::parseTxIns(
   shared_ptr<PulledTx>& thisSTX, 
   StoredUndoData * sud, 
   ScrAddrFilter& scrAddrData,
   bool forceUpdateValue)
{
   //TIMER_START("TxInParsing");

   for (uint32_t iin = 0; iin < thisSTX->txInIndexes_.size() - 1; iin++)
   {
      //TIMER_START("grabTxIn");
      // Get the OutPoint data of TxOut being spent
      const BinaryDataRef opTxHash =
         thisSTX->dataCopy_.getSliceRef(thisSTX->txInIndexes_[iin], 32);

      if (opTxHash == BtcUtils::EmptyHash_)
      {
         //TIMER_STOP("grabTxIn");
         continue;
      }

      const uint32_t opTxoIdx =
         READ_UINT32_LE(thisSTX->dataCopy_.getPtr() + thisSTX->txInIndexes_[iin] + 32);

      BinaryDataRef       fetchBy = opTxHash;

      //TIMER_STOP("grabTxIn");

      //For scanning a predefined set of addresses, check if this txin 
      //consumes one of our utxo

      //leveraging the stxo in RAM
      shared_ptr<StoredTxOut> stxo;
      lookForSTXOInMap(opTxHash, opTxoIdx, stxo);

      if (config_.armoryDbType != ARMORY_DB_SUPER)
      {
         if (stxo)
         {
            //Since this STX is already in map, we have processed it, thus
            //all the relevant outpoints of this STX are already in RAM
            if (scrAddrData.hasUTxO(stxo->getDBKey(false)) < 1)
               continue;

            scrAddrData.eraseUTxO(stxo->getDBKey(false));
         }
         else
         {
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
               stxo = makeSureSTXOInMap(iface_, opTxHash, opTxoIdx);

               if (!scrAddrData.hasScrAddress(stxo->getScrAddress()))
               {
                  //TIMER_STOP("fullFecthOutPointFromDB");
                  continue;
               }

               //TIMER_STOP("fullFecthOutPointFromDB");
            }

            //if we got this far this txin spends one of our utxo, 
            //remove it from utxo set
            scrAddrData.eraseUTxO(txOutDBkey);
         }
      }

      //TIMER_START("CommitTxIn");

      if (!stxo)
         stxo = makeSureSTXOInMap(iface_, fetchBy, opTxoIdx);

      const BinaryData& uniqKey = stxo->getScrAddress();

      // Need to modify existing UTXOs, so that we can delete or mark as spent
      stxo->spentness_ = TXOUT_SPENT;
      stxo->spentByTxInKey_ = thisSTX->getDBKeyOfChild(iin, false);

      ////// Now update the SSH to show this TxIOPair was spent
      // Same story as stxToModify above, except this will actually create a new
      // SSH if it doesn't exist in the map or the DB
      BinaryData hgtX = stxo->getHgtX();

      StoredScriptHistory* sshptr = makeSureSSHInMap_BlindFetch(
         iface_,
         uniqKey,
         hgtX,
         sshToModify_,
         dbUpdateSize_,
         commitId_,
         thisSTX->blockHeight_,
         true);

      // update the txio in its subSSH
      sshptr->markTxOutSpent(
         iface_,
         stxo->getDBKey(false),
         stxo->spentByTxInKey_,
         commitId_,
         config_.armoryDbType,
         config_.pruneType,
         forceUpdateValue);
         
      //Mirror the spent txio at txin height only if the txout was marked
      //unspent

      sshptr->insertSpentTxio(stxo->getDBKey(false),
                              stxo->spentByTxInKey_,
                              dbUpdateSize_, commitId_);

      //TIMER_STOP("CommitTxIn");
   }

   //TIMER_STOP("TxInParsing");

   return true;
}

bool BlockWriteBatcher::parseTxOuts(
   shared_ptr<PulledTx>& thisSTX,
   StoredUndoData * sud,
   ScrAddrFilter& scrAddrData,
   bool forceUpdateValue)
{
   //TIMER_START("TxOutParsing");

   if (config_.armoryDbType == ARMORY_DB_SUPER)
   {
      addStxToSTXOMap(thisSTX);
   }

   for (shared_ptr<StoredTxOut>& stxoToAdd : values(thisSTX->stxoMap_))
   {
      stxoToAdd->spentness_ = TXOUT_UNSPENT;

      //TIMER_START("getTxOutScrAddrAndHgtx");
      BinaryData uniqKey = stxoToAdd->getScrAddress();
      BinaryData hgtX = stxoToAdd->getHgtX();
      //TIMER_STOP("getTxOutScrAddrAndHgtx");

      if (config_.armoryDbType != ARMORY_DB_SUPER)
      {
         if (!scrAddrData.hasScrAddress(uniqKey))
            continue;

         //if we got this far, this utxo points to one of the address in our 
         //list, add it to the utxo set
         scrAddrData.addUTxO(stxoToAdd->getDBKey(false));

         addStxoToSTXOMap(stxoToAdd);
      }

      //TIMER_START("createSSHentryForTXOUT");
      StoredScriptHistory* sshptr = makeSureSSHInMap_BlindFetch(
         iface_,
         uniqKey,
         hgtX,
         sshToModify_,
         dbUpdateSize_,
         commitId_,
         thisSTX->blockHeight_,
         false);

      // Add reference to the next STXO to the respective SSH object
      sshptr->markTxOutUnspent(
         iface_,
         stxoToAdd->getDBKey(false),
         config_.armoryDbType,
         config_.pruneType,
         dbUpdateSize_,
         commitId_,
         stxoToAdd->getValue(),
         stxoToAdd->isCoinbase_,
         false,
         forceUpdateValue
         );
      //TIMER_STOP("createSSHentryForTXOUT");

      // If this was a multisig address, add a ref to each individual scraddr
      if (uniqKey[0] == SCRIPT_PREFIX_MULTISIG)
      {
         vector<BinaryData> addr160List;
         BtcUtils::getMultisigAddrList(stxoToAdd->getScriptRef(), addr160List);
         for (uint32_t a = 0; a<addr160List.size(); a++)
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

            StoredScriptHistory* sshms = makeSureSSHInMap_BlindFetch(
               iface_,
               uniqKey,
               hgtX,
               sshToModify_,
               dbUpdateSize_,
               commitId_,
               thisSTX->blockHeight_,
               false
               );
            sshms->markTxOutUnspent(
               iface_,
               stxoToAdd->getDBKey(false),
               config_.armoryDbType,
               config_.pruneType,
               dbUpdateSize_,
               commitId_,
               stxoToAdd->getValue(),
               stxoToAdd->isCoinbase_,
               true,
               forceUpdateValue
               );
         }
      }
   }

   //TIMER_STOP("TxOutParsing");

   return true;
}

////////////////////////////////////////////////////////////////////////////////
// Assume that stx.blockHeight_ and .duplicateID_ are set correctly.
// We created the maps and sets outside this function, because we need to keep
// a master list of updates induced by all tx in this block.  
// TODO:  Make sure that if Tx5 spends an input from Tx2 in the same 
//        block that it is handled correctly, etc.
bool BlockWriteBatcher::applyTxToBatchWriteData(
                        shared_ptr<PulledTx>& thisSTX,
                        StoredUndoData * sud,
                        ScrAddrFilter& scrAddrData,
                        bool forceUpdateValue)
{
   parseTxOuts(thisSTX, sud, scrAddrData, forceUpdateValue);
   parseTxIns( thisSTX, sud, scrAddrData, forceUpdateValue);

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
   BlockWriteBatcher *bwbSwapPtr = new BlockWriteBatcher(config_, iface_, true);

   //LOGWARN << "dumping " << dbUpdateSize_ << " bytes in the DB";
   
   bwbSwapPtr->commitId_ = commitId_++;

   bwbSwapPtr->searchForSSHKeysToDelete(sshToModify_);

   bwbSwapPtr->sbhToUpdate_   = std::move(sbhToUpdate_);
   bwbSwapPtr->sshToModify_   = sshToModify_;
   bwbSwapPtr->stxoToModify_  = std::move(stxoToModify_);

   bwbSwapPtr->mostRecentBlockApplied_ = mostRecentBlockApplied_;

   if (isCommiting)
   {
      //the write thread is already running and we cumulated enough data in the
      //read thread for the next write. Let's use that idle time to serialize
      //the data to commit ahead of time
      bwbSwapPtr->serializeData();
   }

   bwbSwapPtr->dbUpdateSize_ = dbUpdateSize_;
   bwbSwapPtr->updateSDBI_ = updateSDBI_;

   bwbSwapPtr->parent_ = this;
      
   dbUpdateSize_ = 0;

   /*auto write = [](BlockWriteBatcher* ptr)->void
   { ptr->writeToDB(); };*/

   l.lock();
   thread committhread(executeWrite, bwbSwapPtr);

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
void BlockWriteBatcher::writeToDB(void)
{
   unique_lock<mutex> lock(parent_->writeLock_);

   dataToCommit_.serializeData(*this);

   txn_.open(&iface_->dbEnv_, LMDB::ReadWrite);

   //   TIMER_START("commitToDB");

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

      for (auto& toDel : keysToDelete_)
         iface_->deleteValue(BLKDATA, toDel);

      txn_.commit();
      txn_.begin();

      if (mostRecentBlockApplied_ != 0 && updateSDBI_ == true)
         dataToCommit_.updateSDBI(iface_);

      //final commit
      clearTransactions();
   }

   iface_->dbEnv_.print_remap_status();

   BlockWriteBatcher* bwbParent = parent_;

   //signal the readonly transaction to reset
   bwbParent->resetTxn_ = true;

   //signal DB is ready for new commit
   lock.unlock();

   //delete this;

   //TIMER_STOP("commitToDB");
}

void BlockWriteBatcher::executeWrite(BlockWriteBatcher* ptr)
{
   ptr->writeToDB();
   delete ptr;
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

   vector<shared_ptr<PulledBlock> > pbVec;
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
      
      shared_ptr<PulledBlock> pb(new PulledBlock);
      if (!dis->pullBlockFromDB(pb, hgt, dupID))
      {
         dis->tempBlockData_->endBlock_ = hgt - 1;
         LOGERR << "No block in DB at height " << hgt;
         break;
      }

      memoryLoad += pb->numBytes_;
      pbVec.push_back(pb);

      ++hgt;
   }

   //lock tempBlockData_
   while (dis->tempBlockData_->lock_.fetch_or(1, memory_order_acquire));

   dis->tempBlockData_->pbVec_.insert(dis->tempBlockData_->pbVec_.end(),
      pbVec.begin(), pbVec.end());

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

         shared_ptr<PulledBlock> pb = tempBlockData_->pbVec_[vectorIndex];

         if (!pb)
         {
            LOGERR << "nullptr ** at height " << i;
            throw std::runtime_error("bad sbh pointer at height i");
         }

         tempBlockData_->pbVec_[vectorIndex].reset();

         //clean up used vector indexes
         uint32_t nParsedBlocks = i - tempBlockData_->startBlock_;
         if (nParsedBlocks > 0 && (nParsedBlocks % 10000) == 0)
         {
            tempBlockData_->pbVec_.erase(
               tempBlockData_->pbVec_.begin(),
               tempBlockData_->pbVec_.begin() + 10000);

            tempBlockData_->blockOffset_ += 10000;
         }

         //release lock
         tempBlockData_->lock_.store(0, memory_order_relaxed);

         uint32_t blockSize = pb->numBytes_;

         //scan block
         lastScannedBlockHash = 
            applyBlockToDB(pb, tempBlockData_->scrAddrFilter_);
 
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

////////////////////////////////////////////////////////////////////////////////
bool BlockWriteBatcher::pullBlockFromDB(shared_ptr<PulledBlock>& pb, 
                                        uint32_t height, 
                                        uint8_t dup)
{
   LDBIter ldbIter = iface_->getIterator(BLKDATA);
   if (!ldbIter.seekToExact(DBUtils::getBlkDataKey(height, dup)))
   {
      LOGERR << "Header heigh&dup is not in BLKDATA DB";
      LOGERR << "(" << height << ", " << dup << ")";
      return false;
   }

   // Now we read the whole block, not just the header
   bool success = iface_->readStoredBlockAtIter(ldbIter, *pb.get());
   
   return success;
}


////////////////////////////////////////////////////////////////////////////////
/// DataToCommit
////////////////////////////////////////////////////////////////////////////////
void DataToCommit::serializeData(BlockWriteBatcher& bwb)
{
   if (isSerialized_)
      return;

   auto dbType = bwb.config_.armoryDbType;
   auto pruneType = bwb.config_.pruneType;

   //stxout
   for (auto& stxByHash : bwb.stxoToModify_)
   {
      for (auto& stxo : stxByHash.second)
      {
         BinaryWriter& bw = serializedStxOutToModify_[stxo.second->getDBKey()];
         stxo.second->serializeDBValue(bw, dbType, pruneType);
      }
   }

   bwb.stxoToModify_.clear();
   
   //ssh and subssh
   for (auto& ssh : bwb.sshToModify_)
   {
      if (ssh.second.commitId_ == bwb.commitId_ ||
         bwb.config_.armoryDbType != ARMORY_DB_SUPER)
      {
         ssh.second.alreadyScannedUpToBlk_ = bwb.mostRecentBlockApplied_;

         BinaryWriter& bw = serializedSshToModify_[ssh.second.getDBKey()];
         ssh.second.serializeDBValue(bw, bwb.iface_, dbType, pruneType);
      }

      for (const auto& subssh : ssh.second.subHistMap_)
      {
         if (subssh.second.commitId_ == bwb.commitId_ &&
            subssh.second.txioMap_.size() != 0)
         {
            BinaryWriter& bw = serialuzedSubSshToApply_[subssh.second.getDBKey()];
            subssh.second.serializeDBValue(bw, bwb.iface_, dbType, pruneType);
         }
      }
   }

   bwb.sshToModify_.clear();

   //sbh
   for (auto& sbh : bwb.sbhToUpdate_)
   {
      BinaryWriter& bw = serializedSbhToUpdate_[sbh->getDBKey()];
      sbh->serializeDBValue(bw, BLKDATA, dbType, pruneType);
   }

   if (bwb.sbhToUpdate_.size())
   {
      auto iterLast = bwb.sbhToUpdate_.rbegin();
      topBlockHash_ = (*iterLast)->thisHash_;
   }
   else topBlockHash_ = BtcUtils::EmptyHash_;

   bwb.sbhToUpdate_.clear();

   mostRecentBlockApplied_ = bwb.mostRecentBlockApplied_ +1;

   isSerialized_ = true;
}

////////////////////////////////////////////////////////////////////////////////
void DataToCommit::putSSH(LMDBBlockDatabase* db)
{
   for (auto& sshPair : serializedSshToModify_)
      db->putValue(BLKDATA, sshPair.first, sshPair.second.getData());

   for (auto subSshPair : serialuzedSubSshToApply_)
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