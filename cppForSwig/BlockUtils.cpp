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
#include "BtcWallet.h"
#include "BlockWriteBatcher.h"
#include "lmdbpp.h"


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
static void createUndoDataFromBlock(
      LMDBBlockDatabase* iface,
      uint32_t hgt,
      uint8_t  dup,
      StoredUndoData & sud
   )
{
   SCOPED_TIMER("createUndoDataFromBlock");

   StoredHeader sbh;

   // Fetch the full, stored block
   iface->getStoredHeader(sbh, hgt, dup, true);
   if(!sbh.haveFullBlock())
      throw runtime_error("Cannot get undo data for block because not full!");

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
         if(prevHash == BtcUtils::EmptyHash())
            continue;
         
         // Above we checked the block to be undone is full, but we
         // still need to make sure the prevTx we just fetched has our data.
         StoredTx prevStx;
         iface->getStoredTx(prevStx, prevHash);
         //if(prevStx.stxoMap_.find(prevIndex) == prevStx.stxoMap_.end())
         if(KEY_NOT_IN_MAP(prevIndex, prevStx.stxoMap_))
         {
            throw runtime_error("Cannot get undo data for block because not full!");
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
}

// do something when a reorg happens
class ReorgUpdater
{
   Blockchain *const blockchain_;
   LMDBBlockDatabase* const iface_;
   
   set<HashString> txJustInvalidated_;
   set<HashString> txJustAffected_;
   vector<BlockHeader*> previouslyValidBlockHeaderPtrs_;
   
   list<StoredTx> removedTxes_, addedTxes_;
   
   const BlockDataManagerConfig &config_;

public:
   ReorgUpdater(
      const Blockchain::ReorganizationState& state,
      Blockchain *blockchain,
      LMDBBlockDatabase* iface,
      const BlockDataManagerConfig &config,
      ScrAddrScanData *scrAddrData=NULL
   )
      : blockchain_(blockchain)
      , iface_(iface)
      , config_(config)
   {
      reassessAfterReorg(
         state.prevTopBlock,
         &blockchain_->top(),
         state.reorgBranchPoint,
         scrAddrData
      );
   }
   
   const list<StoredTx>& removedTxes() const { return removedTxes_; }
   const list<StoredTx>& addedTxes() const { return addedTxes_; }
      
private:
   void reassessAfterReorg(
      BlockHeader* oldTopPtr,
      BlockHeader* newTopPtr,
      BlockHeader* branchPtr,
      ScrAddrScanData *scrAddrData=NULL
   )
   {
      SCOPED_TIMER("reassessAfterReorg");
      LOGINFO << "Reassessing Tx validity after reorg";

      // Walk down invalidated chain first, until we get to the branch point
      // Mark transactions as invalid
     
      BlockWriteBatcher blockWrites(config_, iface_);
      
      BlockHeader* thisHeaderPtr = oldTopPtr;
      LOGINFO << "Invalidating old-chain transactions...";
      
      while(thisHeaderPtr != branchPtr)
      {
         uint32_t hgt = thisHeaderPtr->getBlockHeight();
         uint8_t  dup = thisHeaderPtr->getDuplicateID();

         //if(config_.armoryDbType != ARMORY_DB_BARE)
         {
            // Added with leveldb... in addition to reversing blocks in RAM, 
            // we also need to undo the blocks in the DB
            StoredUndoData sud;
            createUndoDataFromBlock(iface_, hgt, dup, sud);
            blockWrites.undoBlockFromDB(sud, scrAddrData);
         }
         
         /*StoredHeader sbh;
         iface_->getStoredHeader(sbh, hgt, dup, true);

         // This is the original, tested, reorg code
         previouslyValidBlockHeaderPtrs_.push_back(thisHeaderPtr);
         for(uint32_t i=0; i<sbh.numTx_; i++)
         {
            StoredTx & stx = sbh.stxMap_[i];
            LOGWARN << "   Tx: " << stx.thisHash_.getSliceCopy(0,8).toHexStr();
            txJustInvalidated_.insert(stx.thisHash_);
            txJustAffected_.insert(stx.thisHash_);
            
            removedTxes_.push_back(stx);
         }*/
         thisHeaderPtr = &blockchain_->getHeaderByHash(thisHeaderPtr->getPrevHash());
      }

      // Walk down the newly-valid chain and mark transactions as valid.  If 
      // a tx is in both chains, it will still be valid after this process
      // UPDATE for LevelDB upgrade:
      //       This used to start from the new top block and walk down, but 
      //       I need to apply the blocks in order, so I switched it to start
      //       from the branch point and walk up
      thisHeaderPtr = branchPtr; // note branch block was not undone, skip it
      LOGINFO << "Marking new-chain transactions valid...";
      while( thisHeaderPtr->getNextHash() != BtcUtils::EmptyHash() &&
            thisHeaderPtr->getNextHash().getSize() > 0 ) 
      {
         thisHeaderPtr = &blockchain_->getHeaderByHash(thisHeaderPtr->getNextHash());
         uint32_t hgt = thisHeaderPtr->getBlockHeight();
         uint8_t  dup = thisHeaderPtr->getDuplicateID();
         iface_->markBlockHeaderValid(hgt, dup);
         StoredHeader sbh;
         iface_->getStoredHeader(sbh, hgt, dup, true);

         //if(config_.armoryDbType != ARMORY_DB_BARE)
         blockWrites.applyBlockToDB(sbh, scrAddrData);

         /*for(uint32_t i=0; i<sbh.numTx_; i++)
         {
            StoredTx & stx = sbh.stxMap_[i];
            LOGWARN << "   Tx: " << stx.thisHash_.getSliceCopy(0,8).toHexStr();
            txJustInvalidated_.erase(stx.thisHash_);
            txJustAffected_.insert(stx.thisHash_);
            addedTxes_.push_back(stx);
         }*/
      }

      LOGWARN << "Done reassessing tx validity";
   }
};


// search for the next byte in bsb that looks like it could be a block
static bool scanForMagicBytes(BinaryStreamBuffer& bsb, const BinaryData &bytes, uint32_t *bytesSkipped)
{
   BinaryData firstFour(4);
   if (bytesSkipped) *bytesSkipped=0;
   
   do
   {
      while (bsb.reader().getSizeRemaining() >= 4)
      {
         bsb.reader().get_BinaryData(firstFour, 4);
         if(firstFour==bytes)
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


BlockDataManagerConfig::BlockDataManagerConfig()
{
   armoryDbType = ARMORY_DB_BARE;
   pruneType = DB_PRUNE_NONE;
   
   levelDBBlockSize = 0;
   levelDBMaxOpenFiles = 0;
}

void BlockDataManagerConfig::selectNetwork(const string &netname)
{
   if(netname == "Main")
   {
      genesisBlockHash = READHEX(MAINNET_GENESIS_HASH_HEX);
      genesisTxHash = READHEX(MAINNET_GENESIS_TX_HASH_HEX);
      magicBytes = READHEX(MAINNET_MAGIC_BYTES);
   }
   else if(netname == "Test")
   {
      genesisBlockHash = READHEX(TESTNET_GENESIS_HASH_HEX);
      genesisTxHash = READHEX(TESTNET_GENESIS_TX_HASH_HEX);
      magicBytes = READHEX(TESTNET_MAGIC_BYTES);
   }
}


class ProgressMeasurer
{
   const uint64_t total_;
   
   time_t then_;
   uint64_t lastSample_=0;
   
   double avgSpeed_=0.0;
   
   
public:
   ProgressMeasurer(uint64_t total)
      : total_(total)
   {
      then_ = time(0);
   }
   
   void advance(uint64_t to)
   {
      static const double smoothingFactor=.75;
      
      if (to == lastSample_) return;
      const time_t now = time(0);
      if (now == then_) return;
      
      if (now < then_+10) return;
      
      double speed = (to-lastSample_)/double(now-then_);
      
      if (lastSample_ == 0)
         avgSpeed_ = speed;
      lastSample_ = to;

      avgSpeed_ = smoothingFactor*speed + (1-smoothingFactor)*avgSpeed_;
      
      then_ = now;
   }

   double fractionCompleted() const { return lastSample_/double(total_); }
   
   double unitsPerSecond() const { return avgSpeed_; }
   
   time_t remainingSeconds() const
   {
      return total_/unitsPerSecond();
   }
};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// Start BlockDataManager_LevelDB methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BlockDataManager_LevelDB::BlockDataManager_LevelDB(const BlockDataManagerConfig &bdmConfig) 
   : config_(bdmConfig)
   , iface_(new LMDBBlockDatabase)
   , blockchain_(config_.genesisBlockHash)
   , scrAddrData_(this)
   , ZeroConfCont_(&scrAddrData_)
   , isRunning_(false)
{
   LOGINFO << "Set home directory: " << config_.homeDirLocation;
   LOGINFO << "Set blkfile dir: " << config_.blkFileLocation;
   LOGINFO << "Set leveldb dir: " << config_.levelDBLocation;
   if(config_.genesisBlockHash.getSize() == 0)
   {
      throw runtime_error("ERROR: Genesis Block Hash not set!");
   }

   zcEnabled_  = false;
   zcLiteMode_ = false;
   zcFilename_ = "";

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

   totalBlockchainBytes_ = 0;
   bytesReadSoFar_ = 0;
   blocksReadSoFar_ = 0;
   filesReadSoFar_ = 0;

   corruptHeadersDB_ = false;

   allScannedUpToBlk_ = 0;

   //for 1:1 wallets and BDM push model
   rescanZC_ = false;

   detectAllBlkFiles();
   
   if(numBlkFiles_==0)
   {
      throw runtime_error("No blockfiles could be found!");
   }
   
   iface_->openDatabases(
      LMDB::ReadWrite,
      config_.levelDBLocation, 
      config_.genesisBlockHash, 
      config_.genesisTxHash, 
      config_.magicBytes,
      config_.armoryDbType, 
      config_.pruneType);
}

/////////////////////////////////////////////////////////////////////////////
BlockDataManager_LevelDB::~BlockDataManager_LevelDB()
{
   registeredWallets_.clear();
   iface_->closeDatabases();
   delete iface_;
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
      for(unsigned i=0; i<=blockchain_.top().getBlockHeight(); i++)
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

   if(config_.armoryDbType != ARMORY_DB_BARE)
   {
      // TODO:  finish this
      findFirstUnappliedBlock();
      LOGINFO << "Blkfile of first unapplied block:   " << startApplyBlkFile_;
      LOGINFO << "Location of first unapplied block:  " << startApplyOffset_;
   }


   // If we're content here, just return
   return true;
}


////////////////////////////////////////////////////////////////////////////////
vector<BinaryData> BlockDataManager_LevelDB::getFirstHashOfEachBlkFile(void) const
{
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
      if(magic != config_.magicBytes)
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
      if(magic != config_.magicBytes)  
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
      if(magic!= config_.magicBytes)
         return UINT32_MAX;

      is.read((char*)szstr.getPtr(), 4);
      uint32_t blksize = READ_UINT32_LE(szstr.getPtr());
      if(is.eof()) break;

      loc += blksize + 8;
      is.seekg(blksize, ios::cur);
   }

   return loc;
}

////////////////////////////////////////////////////////////////////////////////
pair<uint32_t, uint32_t> BlockDataManager_LevelDB::findFileAndOffsetForHgt(
                                           uint32_t hgt, 
                                           const vector<BinaryData> * firstHashes)
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
      if(magic!= config_.magicBytes)
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
int32_t BlockDataManager_LevelDB::getNumConfirmations(HashString txHash)
{
   try
   {
      const TxRef txrefobj = getTxRefByHash(txHash);
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
   catch (NoValue&)
   {
      return TX_NOT_EXIST;
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
   LMDB::Transaction batch(&iface_->dbs_[BLKDATA]);

   TxRef txrefobj = getTxRefByHash(txhash);

   if(!txrefobj.isNull())
      return txrefobj.attached(iface_).getTxCopy();
   else
   {
      // It's not in the blockchain, but maybe in the zero-conf tx list
      Tx tx;
      ZeroConfCont_.getTxByHash(txhash, tx);

      return tx;
   }
}


/////////////////////////////////////////////////////////////////////////////
TX_AVAILABILITY BlockDataManager_LevelDB::getTxHashAvail(BinaryDataRef txHash)
{
   if(getTxRefByHash(txHash).isNull())
   {
      if (!ZeroConfCont_.hasTxByHash(txHash))
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
   try
   {
      iface_->getTxRef(txHash);
      return true;
   }
   catch (...)
   {
      return false;
   }
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
   if (registeredWallets_.find(wltPtr) != registeredWallets_.end()) 
      return false;

   // Add it to the list of wallets to watch
   registeredWallets_.insert(wltPtr);
   wltPtr->setRegistered();

   return true;
}

void BlockDataManager_LevelDB::unregisterWallet(BtcWallet* wltPtr)
{
   registeredWallets_.erase(wltPtr);
}

/////////////////////////////////////////////////////////////////////////////
// This method needs to be callable from another thread.  Therefore, I don't
// seek an exact answer, instead just estimate it based on the last block, 
// and the set of currently-registered addresses.  The method called
// "evalRescanIsRequired()" answers a different question, and iterates 
// through the list of registered addresses, which may be changing in 
// another thread.  
bool BlockDataManager_LevelDB::isDirty(
   uint32_t numBlocksToBeConsideredDirty
) const
{
   uint32_t numBlocksBehind = lastTopBlock_-allScannedUpToBlk_;
   return (numBlocksBehind > numBlocksToBeConsideredDirty);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::resetRegisteredWallets(void)
{
   SCOPED_TIMER("resetRegisteredWallets");

   for (auto wltPtr : registeredWallets_)
   {
      // I'm not sure if there's anything else to do
      // I think it's all encapsulated in this call!
      wltPtr->reset();
   }
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::walletIsRegistered(BtcWallet & wlt) const
{
   return (registeredWallets_.find(&wlt) != registeredWallets_.end());
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::scrAddrIsRegistered(BinaryData scraddr)
{
   for (const auto wltPtr : registeredWallets_)
   {
      
      const auto wltScrAddrMap = wltPtr->getScrAddrMap();
      if(wltScrAddrMap.find(scraddr) != wltScrAddrMap.end()) return true;
   }

   return false;
}


/////////////////////////////////////////////////////////////////////////////
// This used to be "rescanBlocks", but now "scanning" has been replaced by
// "reapplying" the blockdata to the databases.  Basically assumes that only
// raw blockdata is stored in the DB with no SSH objects.  This goes through
// and processes every Tx, creating new SSHs if not there, and creating and
// marking-spent new TxOuts.  
void BlockDataManager_LevelDB::applyBlockRangeToDB(uint32_t blk0, 
   uint32_t blk1, ScrAddrScanData* scrAddrData)
{
   SCOPED_TIMER("applyBlockRangeToDB");
   LMDB::Transaction batch(&iface_->dbs_[HEADERS]);
   LMDB::Transaction batch1(&iface_->dbs_[BLKDATA]);

   blk1 = min(blk1, blockchain_.top().getBlockHeight()+1);

   BinaryData startKey = DBUtils::getBlkDataKey(blk0, 0);
   BinaryData endKey   = DBUtils::getBlkDataKey(blk1, 0);

   LDBIter ldbIter = iface_->getIterator(BLKDATA);
   ldbIter.seekTo(startKey);

   // Start scanning and timer
   //bool doBatches = (blk1-blk0 > NUM_BLKS_BATCH_THRESH);
   BlockWriteBatcher blockWrites(config_, iface_);
   uint32_t hgt;

   TIMER_START("applyBlockRangeToDBIter");
   do
   {
      StoredHeader sbh;
      iface_->readStoredBlockAtIter(ldbIter, sbh);
      hgt = sbh.blockHeight_;
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

      //hack to update SSH top block

      TIMER_STOP("applyBlockRangeToDBIter");

      blockWrites.applyBlockToDB(hgt, dup, scrAddrData); 

      TIMER_START("applyBlockRangeToDBIter");
      bytesReadSoFar_ += sbh.numBytes_;

   } while(iface_->advanceToNextBlock(ldbIter, false));

   double applyBlockRangeToDBIter = TIMER_READ_SEC("applyBlockRangeToDBIter");
   LOGWARN << "applyBlockRangeToDBIter: " << applyBlockRangeToDBIter << " sec";

   double applyBlockToDBinternal = TIMER_READ_SEC("applyBlockToDBinternal");
   LOGWARN << "applyBlockToDBinternal: " << applyBlockToDBinternal << " sec";

   double applyTxToBatchWriteData = TIMER_READ_SEC("applyTxToBatchWriteData");
   LOGWARN << "applyTxToBatchWriteData: " << applyTxToBatchWriteData << " sec";

   double TxInParsing = TIMER_READ_SEC("TxInParsing");
   LOGWARN << "TxInParsing: " << TxInParsing << " sec";

   double TxOutParsing = TIMER_READ_SEC("TxOutParsing");
   LOGWARN << "TxOutParsing: " << TxOutParsing << " sec";

   double leverageStxInRAM = TIMER_READ_SEC("leverageStxInRAM");
   LOGWARN << "leverageStxInRAM: " << leverageStxInRAM << " sec";

   double fecthOutPointFromDB = TIMER_READ_SEC("fecthOutPointFromDB");
   LOGWARN << "fecthOutPointFromDB: " << fecthOutPointFromDB << " sec";

   double fullFecthOutPointFromDB = TIMER_READ_SEC("fullFecthOutPointFromDB");
   LOGWARN << "fullFecthOutPointFromDB: " << fullFecthOutPointFromDB << " sec";

   double grabTxIn = TIMER_READ_SEC("grabTxIn");
   LOGWARN << "grabTxIn: " << grabTxIn << " sec";

   double CommitTxIn = TIMER_READ_SEC("CommitTxIn");
   LOGWARN << "CommitTxIn: " << CommitTxIn << " sec";

   double getTxInCopy = TIMER_READ_SEC("getTxInCopy");
   LOGWARN << "getTxInCopy: " << getTxInCopy << " sec";

   double getOutPoint = TIMER_READ_SEC("getOutPoint");
   LOGWARN << "getOutPoint: " << getOutPoint << " sec";
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::pprintRegisteredWallets(void)
{
   for (const BtcWallet *wlt : registeredWallets_)
   {
      cout << "Wallet:";
      wlt->pprintAlittle(cout);
   }
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
      for(iterTxio  = subSSH.txioMap_.begin(); 
          iterTxio != subSSH.txioMap_.end(); 
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
   is.read(reinterpret_cast<char*>(fileMagic.getPtr()), 4);
   is.seekg(startOffset, ios::beg);

   if( fileMagic != config_.magicBytes )
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
         
      if(magic!=config_.magicBytes)
      {
         // I have to start scanning for MagicBytes
         
         BinaryData nulls( (const uint8_t*)"\0\0\0\0", 4);
         
         if (magic == nulls)
            break;
         
         LOGERR << "Did not find block header in expected location, "
            "possible corrupt data, searching for next block header.";
         
         if (!scanFor(is, config_.magicBytes.getPtr(), config_.magicBytes.getSize()))
         {
            LOGERR << "No more blocks found in file " << filename;
            break;
         }
         
         LOGERR << "Next block header found at offset " << uint64_t(is.tellg())-4;
      }
      
      is.read(reinterpret_cast<char*>(szstr.getPtr()), 4);
      uint32_t nextBlkSize = READ_UINT32_LE(szstr.getPtr());
      if(is.eof()) break;

      is.read(reinterpret_cast<char*>(rawHead.getPtr()), HEAD_AND_NTX_SZ); // plus #tx var_int
      if(is.eof()) break;

      // Create a reader for the entire block, grab header, skip rest
      pair<HashString, BlockHeader>                      bhInputPair;
      BlockHeader block;
      BinaryRefReader brr(rawHead);
      block.unserialize(brr);
      HashString blockhash = block.getThisHash();
      
      const uint32_t nTx = brr.get_var_int();
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
         && BtcUtils::EmptyHash() != addedBlock.getPrevHash()
         )
      {
         LOGWARN << "Block header " << addedBlock.getThisHash().toHexStr()
            << " refers to missing previous hash "
            << addedBlock.getPrevHash().toHexStr();
            
         missingBlockHeaderHashes_.push_back(addedBlock.getPrevHash());
      }
      
   }

   return true;
}


/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_LevelDB::detectAllBlkFiles()
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
      string path = BtcUtils::getBlkFilename(config_.blkFileLocation, numBlkFiles_);
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
      LMDB::Transaction batch(&iface_->dbs_[HEADERS]);
         
      for(unsigned i = 0; i <= blockchain_.top().getBlockHeight(); ++i)
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
void BlockDataManager_LevelDB::doRebuildDatabases(function<void(double,unsigned)> fn)
{
   LOGINFO << "Executing: doRebuildDatabases";
   buildAndScanDatabases(fn, true,   true,   true,   false);
   //                    Rescan  Rebuild !Fetch  Initial                    
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doFullRescanRegardlessOfSync(function<void(double,unsigned)> fn)
{
   LOGINFO << "Executing: doFullRescanRegardlessOfSync";
   buildAndScanDatabases(fn, true,   false,  true,   false);
   //                    Rescan  Rebuild !Fetch  Initial                    
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doSyncIfNeeded(function<void(double,unsigned)> fn)
{
   LOGINFO << "Executing: doSyncIfNeeded";
   buildAndScanDatabases(fn, false,  false,  true,   false);
   //                    Rescan  Rebuild !Fetch  Initial                    
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doInitialSyncOnLoad(function<void(double,unsigned)> fn)
{
   LOGINFO << "Executing: doInitialSyncOnLoad";
   buildAndScanDatabases(fn, false,  false,  false,  true);
   //                    Rescan  Rebuild !Fetch  Initial                    
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doInitialSyncOnLoad_Rescan(function<void(double,unsigned)> fn)
{
   LOGINFO << "Executing: doInitialSyncOnLoad_Rescan";
   buildAndScanDatabases(fn, true,   false,  false,  true);
   //                    Rescan  Rebuild !Fetch  Initial                    
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doInitialSyncOnLoad_Rebuild(function<void(double,unsigned)> fn)
{
   LOGINFO << "Executing: doInitialSyncOnLoad_Rebuild";
   buildAndScanDatabases(fn, false,  true,   true,   true);
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
   function<void(double,unsigned)> progress,
   bool forceRescan, 
   bool forceRebuild,
   bool skipFetch,
   bool initialLoad
)
{
   missingBlockHashes_.clear();
   isRunning_ = true; //quick hack to signal scrAddrData_ that the BDM is loading/loaded.

   SCOPED_TIMER("buildAndScanDatabases");

   
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
      scrAddrData_.reset();
   }

   // If we're going to be rescanning, reset the wallets
   if(forceRescan)
   {
      LOGINFO << "Resetting wallets for rescan";
      skipFetch = true;
      deleteHistories();
      resetRegisteredWallets();
      scrAddrData_.reset();
   }

   if (config_.armoryDbType != ARMORY_DB_SUPER && !forceRescan && !skipFetch)
   {
      LOGWARN << "--- Fetching SSH summaries for " << scrAddrData_.numScrAddr() << " registered addresses";
      scrAddrData_.getScrAddrCurrentSyncState();
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
      
      uint64_t totalBytesDoneSoFar=0;
      ProgressMeasurer progressMeasurer(totalBlockchainBytes_);
      
      for(uint32_t fnum=startRawBlkFile_; fnum<numBlkFiles_; fnum++)
      {
         string blkfile = blkFileList_[fnum];
         LOGINFO << "Parsing blockchain file: " << blkfile.c_str();
         
         const uint64_t thisfileSize = BtcUtils::GetFileSize(blkFileList_[fnum]);
         
         auto singleFileProgress =
            [&progressMeasurer, totalBytesDoneSoFar, &progress] (uint64_t bytes)
            {
               progressMeasurer.advance(totalBytesDoneSoFar+bytes);
               progress(
                  progressMeasurer.fractionCompleted(),
                  progressMeasurer.remainingSeconds()
               );
            };
         
         // The supplied offset only applies to the first blockfile we're reading.
         // After that, the offset is always zero
         uint32_t startOffset = 0;
         if(fnum==startRawBlkFile_)
            startOffset = (uint32_t)startRawOffset_;
      
         readRawBlocksInFile(singleFileProgress, fnum, startOffset);
         
         totalBytesDoneSoFar += thisfileSize;
      }
      TIMER_STOP("dumpRawBlocksToDB");
   }

   double timeElapsed = TIMER_READ_SEC("dumpRawBlocksToDB");
   LOGINFO << "Processed " << blocksReadSoFar_ << " raw blocks DB (" 
           <<  (int)timeElapsed << " seconds)";

   // scan addresses from BDM
   if (config_.armoryDbType == ARMORY_DB_SUPER)
      applyBlockRangeToDB(startApplyHgt_,
                          blockchain_.top().getBlockHeight() + 1);
   else
   {
      TIMER_START("applyBlockRangeToDB");

      if (scrAddrData_.numScrAddr() > 0)
         applyBlockRangeToDB(scrAddrData_.scanFrom(),
                             blockchain_.top().getBlockHeight() + 1,
                             &scrAddrData_);
      scrAddrData_.setSSHLastScanned(iface_, blockchain_.top().getBlockHeight());

      TIMER_STOP("applyBlockRangeToDB");
      double timeElapsed = TIMER_READ_SEC("applyBlockRangeToDB");

      LOGINFO << "Applied Block range to DB in " << timeElapsed << "s";
   }

   // We need to maintain the physical size of all blkXXXX.dat files together
   totalBlockchainBytes_ = bytesReadSoFar_;

   // Update registered address list so we know what's already been scanned
   lastTopBlock_ = blockchain_.top().getBlockHeight() + 1;

   // Now start scanning the raw blocks
   if(config_.armoryDbType != ARMORY_DB_SUPER)
   {
      // We don't do this in SUPER mode because there is no rescanning 
      // For progress bar purposes, let's find the blkfile location of scanStart


      scanWallets(0, lastTopBlock_, forceRescan || forceRebuild);
      LOGINFO << "Finished blockchain scan in " 
              << TIMER_READ_SEC("ScanBlockchain") << " seconds";
   }

   allScannedUpToBlk_ = lastTopBlock_;

   #ifdef _DEBUG
      UniversalTimer::instance().printCSV(string("timings.csv"));
      #ifdef _DEBUG_FULL_VERBOSE
         UniversalTimer::instance().printCSV(cout,true);
      #endif
   #endif
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::readRawBlocksInFile(
   function<void(uint64_t)> progress,
   uint32_t fnum, uint32_t foffset
)
{
   string blkfile = blkFileList_[fnum];
   uint64_t filesize = BtcUtils::GetFileSize(blkfile);
   string fsizestr = BtcUtils::numToStrWCommas(filesize);
   LOGINFO << blkfile.c_str() << " is " << fsizestr.c_str() << " bytes";

   // Open the file, and check the magic bytes on the first block
   ifstream is(blkfile.c_str(), ios::in | ios::binary);
   BinaryData fileMagic(4);
   is.read(reinterpret_cast<char*>(fileMagic.getPtr()), 4);
   if( fileMagic != config_.magicBytes )
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

   LMDBBlockDatabase::Batch batchB(iface_, BLKDATA);
   LMDBBlockDatabase::Batch batchH(iface_, HEADERS);

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
            if(firstFour!=config_.magicBytes)
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
               << blkfile << ", blocksize " << nextBlkSize
               << ", top=" << blockchain_.top().getBlockHeight() << ")";
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
            const bool next = scanForMagicBytes(bsb, config_.magicBytes, &bytesSkipped);
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
            batchB.commit();
            batchB.begin();
            batchH.commit();
            batchH.begin();
         }

         blocksReadSoFar_++;
         bytesReadSoFar_ += nextBlkSize;
         locInBlkFile += nextBlkSize;
         bsb.reader().advance(nextBlkSize);

         progress(is.tellg());

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
   BinaryData firstKey = DBUtils::getBlkDataKey(hgt, dup);

   if(!ldbIter.seekToExact(firstKey))
      return nullSBH;

   // Get the full block from the DB
   iface_->readStoredBlockAtIter(ldbIter, returnSBH);

   if(returnSBH.blockHeight_ != hgt || returnSBH.duplicateID_ != dup)
      return nullSBH;

   return returnSBH;

}

////////////////////////////////////////////////////////////////////////////////
uint8_t BlockDataManager_LevelDB::getMainDupFromDB(uint32_t hgt) const
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
// Deletes all SSH entries in the database
void BlockDataManager_LevelDB::deleteHistories(void)
{
   SCOPED_TIMER("deleteHistories");

   LMDBBlockDatabase::Batch batch(iface_, BLKDATA);
   LDBIter ldbIter = iface_->getIterator(BLKDATA);

   if(!ldbIter.seekToStartsWith(DB_PREFIX_SCRIPT, BinaryData(0)))
      return;

   //////////

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
// This method checks whether your blk0001.dat file is bigger than it was when
// we first read in the blockchain.  If so, we read the new data and add it to
// the memory pool.  Return value is how many blocks were added.
//
// NOTE:  You might want to check lastBlockWasReorg_ variable to know whether 
//        to expect some previously valid headers/txs to still be valid
//
uint32_t BlockDataManager_LevelDB::readBlkFileUpdate(void)
{
   LMDBBlockDatabase::Batch batch(iface_, HEADERS);
   LMDBBlockDatabase::Batch batch1(iface_, BLKDATA);
      
   SCOPED_TIMER("readBlkFileUpdate");

   // Make sure the file exists and is readable
   string filename = blkFileList_[blkFileList_.size()-1];

   uint64_t filesize = FILE_DOES_NOT_EXIST;
   ifstream is(OS_TranslatePath(filename).c_str(), ios::in|ios::binary);
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

         if(fourBytes != config_.magicBytes)
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
   string nextFilename = BtcUtils::getBlkFilename(config_.blkFileLocation, numBlkFiles_);
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

   //
   scrAddrData_.checkForMerge();

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
      if(fourBytes != config_.magicBytes)
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
            ReorgUpdater reorg(state, &blockchain_, iface_, config_, 
               getScrAddrScanData());
            
            prevTopBlk = state.reorgBranchPoint->getBlockHeight();
         }
         else if(state.hasNewTop)
         {
            const BlockHeader & bh = blockchain_.top();
            uint32_t hgt = bh.getBlockHeight();
            uint8_t  dup = bh.getDuplicateID();
      
            LOGINFO << "Applying block to DB!";
            BlockWriteBatcher batcher(config_, iface_);
            
            batcher.applyBlockToDB(hgt, dup, getScrAddrScanData());
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

   return prevTopBlk;
}


////////////////////////////////////////////////////////////////////////////////
// BDM detects the reorg, but is wallet-agnostic so it can't update any wallets
// You have to call this yourself after you check whether the last organizeChain
// call indicated that a reorg happened

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
void BlockDataManager_LevelDB::addNewZeroConfTx(BinaryData const & rawTx, 
                                                uint32_t txtime,
                                                bool writeToFile)
{
   SCOPED_TIMER("addNewZeroConfTx");

   if(txtime==0)
      txtime = (uint32_t)time(NULL);

   ZeroConfCont_.addRawTx(rawTx, txtime);
   rescanZC_ = true;

   //return false;
   
/*   zeroConfRawTxMap_[txHash] = rawTx;
   
   ZeroConfData zc;
   zc.txobj_.unserialize(rawTx);
   zc.txtime_ = txtime;
   zeroConfMap_[txHash] = zc;*/

   // Record time.  Write to file
/*   if(writeToFile)
   {
      ofstream zcFile(OS_TranslatePath(zcFilename_).c_str(), ios::app | ios::binary);
      zcFile.write( (char*)(&zc.txtime_), sizeof(uint64_t) );
      zcFile.write( (char*)zc.txobj_.getPtr(),  zc.txobj_.getSize());
      zcFile.close();
   }

   return true;*/
}



////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::purgeZeroConfPool(void)
{
   map<BinaryData, vector<BinaryData> > invalidatedTxIOKeys = 
                                        ZeroConfCont_.purge(iface_);

   for (auto wltPtr : registeredWallets_)
   {
      wltPtr->purgeZeroConfTxIO(invalidatedTxIOKeys);
   }
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::rewriteZeroConfFile(void)
{
   /*SCOPED_TIMER("rewriteZeroConfFile");
   ofstream zcFile(zcFilename_.c_str(), ios::out | ios::binary);

   ts_BinDataMap::const_snapshot listSS(zeroConfRawTxMap_);
   ;

   for(ts_BinDataMap::const_iterator iter = listSS.begin();
       iter != listSS.end();
       ++iter)
   {
      const ZeroConfData& zcd = zeroConfMap_[iter->first].get();
      zcFile.write( (char*)(&zcd.txtime_), sizeof(uint64_t) );
      zcFile.write( (char*)(zcd.txobj_.getPtr()),  zcd.txobj_.getSize());
   }

   zcFile.close();*/

}

////////////////////////////////////////////////////////////////////////////////
/*void BlockDataManager_LevelDB::pprintSSHInfoAboutHash160(BinaryData const & a160)
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
}*/

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::pprintZeroConfPool(void) const
{
   /*ts_BinDataMap::const_snapshot listSS(zeroConfRawTxMap_);

   for (ts_BinDataMap::const_iterator iter = listSS.begin();
      iter != listSS.end(); ++iter
   )
   {
      const ZeroConfData & zcd = zeroConfMap_[iter->first];
      const Tx & tx = zcd.txobj_;
      cout << tx.getThisHash().getSliceCopy(0,8).toHexStr().c_str() << " ";
      for(uint32_t i=0; i<tx.getNumTxOut(); i++)
         cout << tx.getTxOutCopy(i).getValue() << " ";
      cout << endl;
   }*/
}



/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::isTxFinal(const Tx & tx) const
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
   if(first4 == config_.magicBytes)
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
            throw BlockDeserializingException(
               "Error parsing block (corrupt?) - Cannot add raw block to DB without hgt & dup (hash="
                  + bh.getThisHash().toHexStr() + ")"
               );

         iface_->putStoredHeader(sbh, true);
         missingBlockHashes_.push_back( sbh.thisHash_ );
         throw BlockDeserializingException("Error parsing block (corrupt?) - block header valid (hash="
            + bh.getThisHash().toHexStr() + ")"
         );
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
   {
      throw BlockDeserializingException("Cannot add raw block to DB without hgt & dup (hash="
         + bh.getThisHash().toHexStr() + ")"
      );
   }
   iface_->putStoredHeader(sbh, true);
}

void BlockDataManager_LevelDB::scanWallets(uint32_t startBlock,
                                           uint32_t endBlock, 
                                           bool forceScan)
{
   LOGINFO << registeredWallets_.size() << " wallets loaded";
   uint32_t i = 0;
   for (BtcWallet* walletPtr : registeredWallets_)
   {
      LOGINFO << "initializing wallet #" << i;
      i++;

      walletPtr->scanWallet(startBlock, endBlock, forceScan);
   }
}

bool BlockDataManager_LevelDB::parseNewZeroConfTx()
{
   return ZeroConfCont_.parseNewZC(iface_);
}

