////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "DatabaseBuilder.h"
#include "BlockUtils.h"
#include "BlockchainScanner.h"
#include "BDM_supportClasses.h"
#include "Transactions.h"

/////////////////////////////////////////////////////////////////////////////
DatabaseBuilder::DatabaseBuilder(BlockFiles& blockFiles, 
   BlockDataManager& bdm,
   const ProgressCallback &progress)
   : blockFiles_(blockFiles), db_(bdm.getIFace()),
   bdmConfig_(bdm.config()), blockchain_(bdm.blockchain()),
   scrAddrFilter_(bdm.getScrAddrFilter()),
   progress_(progress),
   magicBytes_(db_->getMagicBytes()), topBlockOffset_(0, 0)
{}

/////////////////////////////////////////////////////////////////////////////
void DatabaseBuilder::init()
{
   if (bdmConfig_.checkChain_)
   {
      verifyChain();
      return;
   }

   TIMER_START("initdb");

   //list all files in block data folder
   blockFiles_.detectAllBlockFiles();

   //read all blocks already in DB and populate blockchain
   topBlockOffset_ = loadBlockHeadersFromDB(progress_);
   
   if (bdmConfig_.reportProgress_)
      progress_(BDMPhase_OrganizingChain, 0, UINT32_MAX, 0);

   blockchain_->forceOrganize();
   blockchain_->setDuplicateIDinRAM(db_);

   try
   {
      //rewind the top block offset to catch on missed blocks for db init
      auto& topBlock = blockchain_->top();
      auto rewindHeight = topBlock.getBlockHeight();
      if (rewindHeight > 100)
         rewindHeight -= 100;
      else
         rewindHeight = 1;

      auto& rewindBlock = blockchain_->getHeaderByHeight(rewindHeight);
      topBlockOffset_.fileID_ = rewindBlock.getBlockFileNum();
      topBlockOffset_.offset_ = rewindBlock.getOffset();

      LOGINFO << "Rewinding 100 blocks";
   }
   catch (exception&)
   {}

   //update db
   TIMER_START("updateblocksindb");
   LOGINFO << "updating HEADERS db";
   auto reorgState = updateBlocksInDB(
      progress_, bdmConfig_.reportProgress_, false);
   TIMER_STOP("updateblocksindb");
   double updatetime = TIMER_READ_SEC("updateblocksindb");
   LOGINFO << "updated HEADERS db in " << updatetime << "s";

   verifyTxFilters();

   //blockchain object now has the longest chain, update address history
   //retrieve all tracked addresses from DB
   scrAddrFilter_->getAllScrAddrInDB();

   //don't scan without any registered addresses
   if (scrAddrFilter_->getScrAddrMap()->size() == 0)
      return;

   bool reset = false;

   //determine from which block to start scanning
   scrAddrFilter_->getScrAddrCurrentSyncState();
   auto scanFrom = scrAddrFilter_->scanFrom();

   //DatabaseBuilder objects always operate on sdbi index 0
   //BlockchainScanner object depend on the underlying ScrAddrFilter uniqueID
   auto&& subsshSdbi = db_->getStoredDBInfo(SUBSSH, 0);
   auto&& sshsdbi = db_->getStoredDBInfo(SSH, 0);

   //check merkle of registered addresses vs what's in the DB
   if (!scrAddrFilter_->hasNewAddresses())
   {
      //no new addresses were registered in between runs.

      if (subsshSdbi.topBlkHgt_ > sshsdbi.topBlkHgt_)
      {
         //SUBSSH db has scanned ahead of SSH db, no point rescanning these
         //blocks
         scanFrom = subsshSdbi.topBlkHgt_;
      }
   }
   else
   {
      //we have newly registered addresses this run, force a full rescan
      resetHistory();
      scanFrom = -1;
      reset = true;
   }

   if (!reorgState.prevTopStillValid && !reset)
   {
      //reorg
      undoHistory(reorgState);

      scanFrom = min(
         scanFrom, (int)reorgState.reorgBranchPoint->getBlockHeight() + 1);
   }
   
   LOGINFO << "scanning new blocks from #" << scanFrom << " to #" <<
      blockchain_->top().getBlockHeight();

   TIMER_START("scanning");
   while (1)
   {
      auto topScannedBlockHash = updateTransactionHistory(scanFrom);

      if (topScannedBlockHash == blockchain_->top().getThisHash())
         break;

      //if we got this far the scan failed, diagnose the DB and repair it

      LOGWARN << "topScannedBlockHash does match the hash of the current top";
      LOGWARN << "current top is height #" << blockchain_->top().getBlockHeight();

      try
      {
         auto& topscannedblock = blockchain_->getHeaderByHash(topScannedBlockHash);
         LOGWARN << "topScannedBlockHash is height #" << topscannedblock.getBlockHeight();
      }
      catch (...)
      {
         LOGWARN << "topScannedBlockHash is invalid";
      }

      LOGINFO << "repairing DB";

      //grab top scanned height from SUBSSH DB
      auto&& sdbi = db_->getStoredDBInfo(SUBSSH, 0);

      //get fileID for height
      auto& topHeader = blockchain_->getHeaderByHeight(sdbi.topBlkHgt_);
      int fileID = topHeader.getBlockFileNum();
      
      //rewind 5 blk files for the good measure
      fileID -= 5;
      if (fileID < 0)
         fileID = 0;

      //reparse these blk files
      if (!reparseBlkFiles(fileID))
      {
         LOGERR << "failed to repair DB, aborting";
         throw runtime_error("failed to repair DB");
      }
   }

   TIMER_STOP("scanning");
   double scanning = TIMER_READ_SEC("scanning");
   LOGINFO << "scanned new blocks in " << scanning << "s";

   TIMER_STOP("initdb");
   double timeSpent = TIMER_READ_SEC("initdb");
   LOGINFO << "init db in " << timeSpent << "s";
}

/////////////////////////////////////////////////////////////////////////////
BlockOffset DatabaseBuilder::loadBlockHeadersFromDB(
   const ProgressCallback &progress)
{
   //TODO: preload the headers db file to speed process up

   LOGINFO << "Reading headers from db";
   blockchain_->clear();

   unsigned counter = 0;
   BlockOffset topBlockOffet(0, 0);

   const unsigned howManyBlocks = [&]() -> unsigned
   {
      const time_t btcEpoch = 1230963300; // genesis block ts
      const time_t now = time(nullptr);

      // every ten minutes we get a block, how many blocks exist?
      const unsigned blocks = (now - btcEpoch) / 60 / 10;
      return blocks;
   }();

   ProgressCalculator calc(howManyBlocks);

   const auto callback = [&](const BlockHeader &h, uint32_t height, uint8_t dup)
   {
      blockchain_->addBlock(h.getThisHash(), h, height, dup);

      BlockOffset currblock(h.getBlockFileNum(), h.getOffset());
      if (currblock > topBlockOffet)
         topBlockOffet = currblock;

      if ((counter++ % 50000) != 0)
         return;

      if (!bdmConfig_.reportProgress_)
         return;

      calc.advance(counter);
      progress(BDMPhase_DBHeaders, 
         calc.fractionCompleted(), calc.remainingSeconds(), counter);
   };

   db_->readAllHeaders(callback);

   LOGINFO << "Found " << blockchain_->allHeaders().size() << " headers in db";

   return topBlockOffet;
}

/////////////////////////////////////////////////////////////////////////////
Blockchain::ReorganizationState DatabaseBuilder::updateBlocksInDB(
   const ProgressCallback &progress, bool verbose, bool fullHints)
{
   //preload and prefetch
   BlockDataLoader bdl(blockFiles_.folderPath(), true, true, true);

   unsigned threadcount = min(bdmConfig_.threadCount_,
      blockFiles_.fileCount() - topBlockOffset_.fileID_);

   mutex progressMutex;
   unsigned baseID = topBlockOffset_.fileID_;

   //init progress
   ProgressCalculator calc(blockFiles_.fileCount());
   if (verbose)
   {
      calc.init(baseID);
      auto val = calc.fractionCompleted();
      progress(BDMPhase_BlockData,
         calc.fractionCompleted(), UINT32_MAX,
         baseID);
   }


   auto addblocks = [&](uint16_t fileID, size_t startOffset, 
      shared_ptr<BlockOffset> bo, bool _verbose)->void
   {
      while (1)
      {
         if (!addBlocksToDB(bdl, fileID, startOffset, bo, fullHints))
            return;

         if (_verbose)
         {
            unique_lock<mutex> lock(progressMutex, defer_lock);
            if (lock.try_lock() && fileID >= baseID)
            {
               LOGINFO << "parsed block file #" << fileID;

               calc.advance(fileID);
               progress(BDMPhase_BlockData,
                  calc.fractionCompleted(), calc.remainingSeconds(),
                  fileID);

               baseID = fileID;
            }
         }

         //reset startOffset for the next file
         startOffset = 0;
         fileID += threadcount;
      }
   };

   vector<thread> tIDs;
   vector<shared_ptr<BlockOffset>> boVec;

   for (unsigned i = 1; i < threadcount; i++)
   {
      boVec.push_back(make_shared<BlockOffset>(topBlockOffset_));
      tIDs.push_back(thread(addblocks, topBlockOffset_.fileID_ + i, 0, 
	                  boVec.back(), verbose));
   }

   boVec.push_back(make_shared<BlockOffset>(topBlockOffset_));
   addblocks(topBlockOffset_.fileID_, topBlockOffset_.offset_,
	          boVec.back(), verbose);

   for (auto& tID : tIDs)
   {
      if (tID.joinable())
         tID.join();
   }

   for (auto& blockoffset : boVec)
   {
      if (*blockoffset > topBlockOffset_)
         topBlockOffset_ = *blockoffset;
   }

   //done parsing new blocks, reorg and add to DB
   if (verbose)
      progress_(BDMPhase_OrganizingChain, 0, UINT32_MAX, 0);
   auto&& reorgState = blockchain_->organize(verbose);
   blockchain_->putNewBareHeaders(db_);

   return reorgState;
}

/////////////////////////////////////////////////////////////////////////////
bool DatabaseBuilder::addBlocksToDB(BlockDataLoader& bdl, 
   uint16_t fileID, size_t startOffset, shared_ptr<BlockOffset> bo,
   bool fullHints)
{
   auto&& blockfilemappointer = bdl.get(fileID, true);
   auto ptr = blockfilemappointer.get()->getPtr();

   //ptr is null if we're out of block files
   if (ptr == nullptr)
      return false;

   map<uint32_t, BlockData> bdMap;

   auto getID = [&](void)->uint32_t
   {
      return blockchain_->getNewUniqueID();
   };

   auto tallyBlocks = 
      [&](const uint8_t* data, size_t size, size_t offset)->bool
   {
      //deser full block, check merkle
      BlockData bd;
      BinaryRefReader brr(data, size);

      try
      {
         bd.deserialize(data, size, nullptr, 
            getID, true, fullHints);
      }
      catch (BlockDeserializingException &e)
      {
         LOGERR << "block deser except: " <<  e.what();
         LOGERR << "block fileID: " << fileID;
         return false;
      }
      catch (exception &e)
      {
         LOGERR << "exception: " << e.what();
         return false;
      }
      catch (...)
      {
         //deser failed, ignore this block
         LOGERR << "unknown exception";
         return false;
      }

      //block is valid, add to container
      bd.setFileID(fileID);
      bd.setOffset(offset);
      
      BlockOffset blockoffset(fileID, offset + bd.size());
      if (blockoffset > *bo)
         *bo = blockoffset;

      bdMap.insert(move(make_pair(bd.uniqueID(), move(bd))));
      return true;
   };

   parseBlockFile(ptr, blockfilemappointer.size(),
      startOffset, tallyBlocks);

   //done parsing, add the headers to the blockchain object
   //convert BlockData vector to BlockHeader map first
   map<HashString, BlockHeader> bhmap;
   for (auto& bd : bdMap)
   {
      auto&& bh = bd.second.createBlockHeader();
      bhmap.insert(move(make_pair(bh.getThisHash(), move(bh))));
   }

   //add in bulk
   auto&& insertedBlocks = blockchain_->addBlocksInBulk(bhmap);

   if (!fullHints)
   {
      //process filters
      if (bdmConfig_.armoryDbType_ == ARMORY_DB_FULL)
      {
         //pull existing file filter bucket from db (if any)
         auto&& pool = db_->getFilterPoolForFileNum<TxFilterType>(fileID);

         if (insertedBlocks.size() == 0)
         {
            if (pool.isValid())
            {
               //this block has a filter pool and there is no data to append,
               //we can return
               return true;
            }

            //if we got this far, this block file does not add any new blocks 
            //to the chain, but it still needs an empty filter pool for the 
            //resolver to fetch. we simply let it run on an empty block set
         }

         //tally all block filters
         set<TxFilter<TxFilterType>> allFilters;

         for (auto& bdId : insertedBlocks)
         {
            allFilters.insert(bdMap[bdId].getTxFilter());
         }

         //update bucket
         pool.update(allFilters);

         //update db entry
         db_->putFilterPoolForFileNum(fileID, pool);
      }
   }
   else
   {
      commitAllTxHints(bdMap);
   }

   return true;
}

/////////////////////////////////////////////////////////////////////////////
void DatabaseBuilder::parseBlockFile(
   const uint8_t* fileMap, size_t fileSize, size_t startOffset,
   function<bool(const uint8_t* data, size_t size, size_t offset)> callback)
{
   //check magic bytes at start of file
   auto magicBytesSize = magicBytes_.getSize();
   if (fileSize < magicBytesSize)
   {
      stringstream ss;
      ss << "Block data file size is " << fileSize << "bytes long";
      throw runtime_error(ss.str());
   }

   BinaryDataRef dataMagic(fileMap, magicBytesSize);
   if (dataMagic != magicBytes_)
      throw runtime_error("Unexpected network magic bytes found in block data file");

   //set pointer to start offset
   fileMap += startOffset;

   //parse the file
   size_t progress = startOffset;
   while (progress + magicBytesSize < fileSize)
   {
      size_t localProgress = magicBytesSize;
      BinaryDataRef magic(fileMap, magicBytesSize);

      if (magic != magicBytes_)
      {
         //no magic byte trailing the last valid file offset, let's look for one
         BinaryDataRef theFile(fileMap + localProgress, 
            fileSize - progress - localProgress);
         int32_t foundOffset = theFile.find(magicBytes_);
         if (foundOffset == -1)
            return;
         
         LOGINFO << "Found next block after skipping " << foundOffset - 4 << "bytes";

         localProgress += foundOffset;

         magic.setRef(fileMap + localProgress, magicBytesSize);
         if (magic != magicBytes_)
            throw runtime_error("parsing for magic byte failed");

         localProgress += 4;
      }

      if (progress + localProgress + 4 >= fileSize)
         return;

      BinaryDataRef blockSize(fileMap + localProgress, 4);
      localProgress += 4;
      size_t thisBlkSize = READ_UINT32_LE(blockSize.getPtr());

      if (progress + localProgress + thisBlkSize > fileSize)
         return;

      fileMap += localProgress;
      progress += localProgress;

      if (callback(
         fileMap, thisBlkSize, progress))
      {
         //only advance for the whole blockSize if callback returned true
         fileMap += thisBlkSize;
         progress += thisBlkSize;
      }
   }
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DatabaseBuilder::updateTransactionHistory(int32_t startHeight)
{
   //Scan history
   auto topScannedBlockHash = 
      scanHistory(startHeight, bdmConfig_.reportProgress_);

   //return the hash of the last scanned block
   return topScannedBlockHash;
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DatabaseBuilder::scanHistory(int32_t startHeight,
   bool reportprogress)
{
   BlockchainScanner bcs(blockchain_, db_, scrAddrFilter_.get(),
      blockFiles_, bdmConfig_.threadCount_, bdmConfig_.ramUsage_,
      progress_, reportprogress);
   
   bcs.scan(startHeight);
   bcs.resetFileMaps(reportprogress);
   bcs.updateSSH(false);
   bcs.resolveTxHashes();

   scrAddrFilter_->lastScannedHash_ = bcs.getTopScannedBlockHash();
   return bcs.getTopScannedBlockHash();
}

/////////////////////////////////////////////////////////////////////////////
Blockchain::ReorganizationState DatabaseBuilder::update(void)
{
   unique_lock<mutex> lock(scrAddrFilter_->mergeLock_);

   //list all files in block data folder
   blockFiles_.detectAllBlockFiles();

   //update db
   auto&& reorgState = updateBlocksInDB(progress_, false, false);

   if (!reorgState.hasNewTop)
      return reorgState;

   uint32_t prevTop = reorgState.prevTop->getBlockHeight();
   uint32_t startHeight = reorgState.prevTop->getBlockHeight() + 1;


   if (!reorgState.prevTopStillValid)
   {
      //reorg, undo blocks up to branch point
      undoHistory(reorgState);

      startHeight = reorgState.reorgBranchPoint->getBlockHeight() + 1;
   }

   //scan new blocks   
   BinaryData&& topScannedHash = scanHistory(startHeight, false);
   if (topScannedHash != blockchain_->top().getThisHash())
      throw runtime_error("scan failure during DatabaseBuilder::update");

   //TODO: recover from failed scan 

   return reorgState;
}

/////////////////////////////////////////////////////////////////////////////
void DatabaseBuilder::undoHistory(
   Blockchain::ReorganizationState& reorgState)
{
   //unique_lock<mutex> lock(scrAddrFilter_->mergeLock_);
   BlockchainScanner bcs(blockchain_, db_, scrAddrFilter_.get(), 
      blockFiles_, bdmConfig_.threadCount_, bdmConfig_.ramUsage_, 
      progress_, false);
   bcs.undo(reorgState);

   blockchain_->setDuplicateIDinRAM(db_);
}

/////////////////////////////////////////////////////////////////////////////
void DatabaseBuilder::resetHistory()
{
   //nuke SSH, SUBSSH, TXHINT and STXO DBs
   LOGINFO << "reseting history in DB";
   db_->resetHistoryDatabases();
}

/////////////////////////////////////////////////////////////////////////////
bool DatabaseBuilder::reparseBlkFiles(unsigned fromID)
{
   mutex mu;
   map<BinaryData, BlockHeader> headerMap;

   BlockDataLoader bdl(blockFiles_.folderPath(), true, false, true);

   auto assessLambda = [&](unsigned fileID)->void
   {
      while (fileID < blockFiles_.fileCount())
      {
         auto&& hmap = assessBlkFile(bdl, fileID);

         fileID += bdmConfig_.threadCount_;

         if (hmap.size() == 0)
            continue;

         unique_lock<mutex> lock(mu);
         headerMap.insert(hmap.begin(), hmap.end());
      }
   };

   unsigned threadcount = min(bdmConfig_.threadCount_,
      blockFiles_.fileCount() - topBlockOffset_.fileID_);

   vector<thread> tIDs;
   for (unsigned i = 1; i < threadcount; i++)
      tIDs.push_back(thread(assessLambda, fromID + i));

   assessLambda(fromID);

   for (auto& tID : tIDs)
   {
      if (tID.joinable())
         tID.join();
   }

   //headerMap contains blocks that are either missing from our blockchain 
   //object or are recorded under invalid fileID/offset. Lets forcefully add
   //them to the blockchain object, then force a full reorg

   if (headerMap.size() == 0)
   {
      LOGWARN << "did not find any damaged and/or missings blocks";
      return false;
   }

   blockchain_->forceAddBlocksInBulk(headerMap);
   blockchain_->forceOrganize();
   blockchain_->putNewBareHeaders(db_);

   //TODO: edge case: all the new blocks found were orphans, nothing was added
   //to the db, will run into the same blocks next run

   return true;
}

/////////////////////////////////////////////////////////////////////////////
map<BinaryData, BlockHeader> DatabaseBuilder::assessBlkFile(
   BlockDataLoader& bdl, unsigned fileID)
{
   map<BinaryData, BlockHeader> returnMap;

   auto&& blockfilemappointer = bdl.get(fileID, false);
   auto ptr = blockfilemappointer.get()->getPtr();

   //ptr is null if we're out of block files
   if (ptr == nullptr)
      return returnMap;

   vector<BlockData> bdVec;

   auto tallyBlocks = [&](const uint8_t* data, size_t size, size_t offset)->bool
   {
      //deser full block, check merkle
      BlockData bd;
      BinaryRefReader brr(data, size);

      auto getID = [this](void)->uint32_t
      { return blockchain_->getNewUniqueID(); };

      try
      {
         bd.deserialize(data, size, nullptr, getID, true, false);
      }
      catch (...)
      {
         //deser failed, ignore this block
         return false;
      }

      bd.setFileID(fileID);
      bd.setOffset(offset);


      //query blockchain object for block by hash
      BlockHeader* bhPtr = nullptr;
      try
      {
         blockchain_->getHeaderByHash(bd.getHash());
      }
      catch (range_error&)
      {
         //catch and continue
      }

      //add the block either if we don't have it in our blockchain object,
      //or if the offsets and/or fileID mismatch
      if (bhPtr != nullptr)
      {
         if (bhPtr->getBlockFileNum() == fileID &&
            bhPtr->getOffset() == offset)
            return true;
      }

      bdVec.push_back(move(bd));
      return true;
   };

   parseBlockFile(ptr, blockfilemappointer.size(), 0, tallyBlocks);

   //done parsing, add the headers to the blockchain object
   //convert BlockData vector to BlockHeader map first
   map<HashString, BlockHeader> bhmap;
   for (auto& bd : bdVec)
   {
      auto&& bh = bd.createBlockHeader();
      bhmap.insert(make_pair(bh.getThisHash(), move(bh)));
   }

   return returnMap;
}

/////////////////////////////////////////////////////////////////////////////
void DatabaseBuilder::verifyChain()
{
   /*
   builds db (no scanning) with full txhints, then verifies all tx.
   */

   //list all files in block data folder
   blockFiles_.detectAllBlockFiles();

   //read all blocks already in DB and populate blockchain
   topBlockOffset_ = loadBlockHeadersFromDB(progress_);

   if (bdmConfig_.reportProgress_)
      progress_(BDMPhase_OrganizingChain, 0, UINT32_MAX, 0);

   blockchain_->forceOrganize();
   blockchain_->setDuplicateIDinRAM(db_);

   //update db
   LOGINFO << "updating HEADERS db";
   auto reorgState = updateBlocksInDB(
      progress_, bdmConfig_.reportProgress_, true);
   LOGINFO << "updated HEADERS db";

   //verify transactions
   verifyTransactions();
}

/////////////////////////////////////////////////////////////////////////////
void DatabaseBuilder::commitAllTxHints(const map<uint32_t, BlockData>& bdMap)
{
   map<BinaryData, StoredTxHints> txHints;

   auto addTxHint =
      [&](StoredTxHints& stxh, const BinaryData& txkey)->void
   {
      //make sure key isn't already in there
      for (auto& key : stxh.dbKeyList_)
      {
         if (key == txkey)
            return;
      }

      stxh.dbKeyList_.push_back(txkey);
   };

   //The readwrite db transactions makes sure only one thread is batching 
   //txhints at a time. This is relevant, as hints are first pulled from
   //disk then updated. In case 2 different blocks commit the to the same 
   //hint, one will likely overwrite the other.
   LMDBEnv::Transaction hintdbtx;
   db_->beginDBTransaction(&hintdbtx, TXHINTS, LMDB::ReadWrite);

   {
      auto addTxHintMap =
         [&](shared_ptr<BCTX> txn, const BinaryData& txkey)->void
      {
         auto&& txHashPrefix = txn->txHash_.getSliceCopy(0, 4);
         StoredTxHints& stxh = txHints[txHashPrefix];

         //pull txHint from DB first, don't want to override 
         //existing hints
         if (stxh.isNull())
            db_->getStoredTxHints(stxh, txHashPrefix);

         addTxHint(stxh, txkey);

         stxh.preferredDBKey_ = stxh.dbKeyList_.front();
      };

      for (auto& block : bdMap)
      {
         auto& txns = block.second.getTxns();
         auto nTxn = txns.size();
         for (unsigned i=0; i < nTxn; i++)
         {
            auto& txn = txns[i];
            auto&& txkey = DBUtils::getBlkDataKeyNoPrefix(block.first, 0xFF, i);

            addTxHintMap(txn, txkey);
         }
      }
   }

   map<BinaryData, BinaryWriter> serializedHints;

   //serialize
   for (auto& txhint : txHints)
   {
      auto& bw = serializedHints[txhint.second.getDBKey()];
      txhint.second.serializeDBValue(bw);
   }

   //write
   {
      for (auto& txhint : serializedHints)
      {
         db_->putValue(TXHINTS,
            txhint.first.getRef(),
            txhint.second.getDataRef());
      }
   }
}

/////////////////////////////////////////////////////////////////////////////
void DatabaseBuilder::verifyTransactions()
{
   struct ParserState
   {
      atomic<unsigned> blockHeight_;
      atomic<unsigned> unknownErrors_;
      atomic<unsigned> unsupportedSigHash_;
      atomic<unsigned> unresolvedHashes_;
      atomic<unsigned> parsedCount_;
      mutex mu_;

      ParserState() 
      {
         blockHeight_.store(0);
         unknownErrors_.store(0);
         unsupportedSigHash_.store(0);
         unresolvedHashes_.store(0);
         parsedCount_.store(0);
      }
   };

   TIMER_START("10blocks");

   //dont preload, prefetch
   BlockDataLoader bdl(blockFiles_.folderPath(), true, false, true);

   auto stateStruct = make_shared<ParserState>();

   auto verifyBlockTx = [&bdl, this, stateStruct](void)->void
   {
      map<unsigned, shared_ptr<BlockFileMapPointer>> filePtrMap;

      auto getFileMap = [&bdl, &filePtrMap](unsigned fileNum)->
         shared_ptr<BlockFileMapPointer>&
      {
         auto& fmp = filePtrMap[fileNum];
         if (fmp == nullptr)
            fmp = make_shared<BlockFileMapPointer>(bdl.get(fileNum, false));

         return fmp;
      };

      auto getUtxoMap = [&bdl, stateStruct, getFileMap, this]
         (shared_ptr<BCTX> txn)->TransactionVerifier::utxoMap
      {
         TransactionVerifier::utxoMap utxomap;
         for (auto& txin : txn->txins_)
         {
            //get output hash
            BinaryDataRef hashref(txn->data_ + txin.first, 32);
            auto outputID = (uint32_t*)(txn->data_ + txin.first + 32);

            //resolve hash
            StoredTxHints sths;
            if (!db_->getStoredTxHints(sths, hashref.getSliceRef(0, 4)))
            {
               stateStruct->unresolvedHashes_.fetch_add(1, memory_order_relaxed);
               throw UnresolvedHashException();
            }

            bool foundtx = false;
            for (auto& outpointkey : sths.dbKeyList_)
            {
               if (outpointkey.getSize() == 0)
                  continue;

               //parse key
               auto blockkey = outpointkey.getSliceRef(0, 4);
               auto opDup = (uint8_t*)(outpointkey.getPtr() + 3);
               if (*opDup != 0xFF)
                  continue;

               auto blockID = DBUtils::hgtxToHeight(blockkey);
               BlockHeader* bhPtr;
               try
               {
                  bhPtr = &blockchain_->getHeaderById(blockID);
               }
               catch (exception&)
               {
                  continue;
               }

               //get tx index
               BinaryRefReader brr(outpointkey);
               brr.advance(4);
               auto txid = brr.get_uint16_t(BE);

               //get block data
               auto blockFileNum = bhPtr->getBlockFileNum();
               auto& fileMap = getFileMap(blockFileNum);

               auto getID = [bhPtr](void)->unsigned int
               {
                  return bhPtr->getThisID();
               };

               BlockData bdata;
               bdata.deserialize(
                  fileMap->get()->getPtr() + bhPtr->getOffset(),
                  bhPtr->getBlockSize(),
                  bhPtr, getID, false, false);

               auto& txns = bdata.getTxns();
               if (txid > txns.size())
                  continue;

               //check hash
               auto _txn = txns[txid];
               _txn->getHash();
               if (hashref != _txn->txHash_)
                  continue;

               //grab output
               auto txoutcount = _txn->txouts_.size();
               if (*outputID > txoutcount)
                  break;

               BinaryDataRef output(_txn->data_ + _txn->txouts_[*outputID].first,
                  _txn->txouts_[*outputID].second);

               UTXO utxo;
               utxo.unserializeRaw(output);
               auto& idmap = utxomap[hashref];
               idmap[*outputID] = move(utxo);

               foundtx = true;
               break;
            }

            if (!foundtx)
               throw UnresolvedHashException();
         }

         return utxomap;
      };

      unsigned thisHeight = 0;
      unsigned failedVerifications = 0;

      LMDBEnv::Transaction hintdbtx;
      db_->beginDBTransaction(&hintdbtx, TXHINTS, LMDB::ReadOnly);

      while (thisHeight < blockchain_->top().getBlockHeight())
      {
         //grab blockheight
         thisHeight = stateStruct->blockHeight_.fetch_add(1, memory_order_relaxed);

         BlockData bdata;
         BlockHeader* blockheader;

         blockheader = &blockchain_->getHeaderByHeight(thisHeight);

         auto& fileMap = getFileMap(blockheader->getBlockFileNum());

         auto getID = [blockheader](void)->unsigned int
         {
            return blockheader->getThisID();
         };

         bdata.deserialize(
            fileMap->get()->getPtr() + blockheader->getOffset(),
            blockheader->getBlockSize(),
            blockheader, getID, false, false);

         auto& txns = bdata.getTxns();
         for (unsigned i = 1; i < txns.size(); i++)
         {
            auto& txn = txns[i];

            try
            {
               //gather utxos
               auto&& utxomap = getUtxoMap(txn);

               //verify tx
               TransactionVerifier txV(*txn, utxomap);
               auto flags = txV.getFlags();

               if (blockheader->getTimestamp() > P2SH_TIMESTAMP)
                  flags |= SCRIPT_VERIFY_P2SH;

               if (txn->usesWitness_)
                  flags |= SCRIPT_VERIFY_SEGWIT;

               txV.setFlags(flags);

               if (txV.verify())
                  stateStruct->parsedCount_.fetch_add(1, memory_order_relaxed);
               else
                  ++failedVerifications;
            }
            catch (UnsupportedSigHashTypeException&)
            {
               stateStruct->unsupportedSigHash_.fetch_add(1, memory_order_relaxed);
            }
            catch (UnresolvedHashException&)
            {
               stateStruct->unresolvedHashes_.fetch_add(1, memory_order_relaxed);
            }
            catch (exception& e)
            {
               unique_lock<mutex> lock(stateStruct->mu_);
               auto error = e.what();
               LOGERR << "+++ error at #" << thisHeight << ":" << i;
               LOGERR << "+++ strerr: " << e.what();
               stateStruct->unknownErrors_.fetch_add(1, memory_order_relaxed);
            }
         }

         if (thisHeight % 1000 == 0)
         {
            unique_lock<mutex> lock(stateStruct->mu_);
            auto tE = TIMER_READ_SEC("10blocks");
            TIMER_RESTART("10blocks");

            LOGINFO << "=== time elapsed: " << tE << " ===";

            LOGINFO << "current block: " << thisHeight;
            LOGINFO << "--- verified " << 
               stateStruct->parsedCount_.load(memory_order_relaxed) << " transactions";

            LOGINFO << "--- *encountered " <<
               stateStruct->unsupportedSigHash_.load(memory_order_relaxed) <<
               " unknown sighashes";

            LOGINFO << "--- *encountered " <<
               stateStruct->unresolvedHashes_.load(memory_order_relaxed) <<
               " unresolved hashes";

            LOGINFO << "--- ***encountered " <<
               stateStruct->unknownErrors_.load(memory_order_relaxed) <<
               " unknown errors";
         }
      }
   };

   vector<thread> parserThrVec;
   for (unsigned i = 1; i < bdmConfig_.threadCount_; i++)
      parserThrVec.push_back(thread(verifyBlockTx));

   verifyBlockTx();

   checkedTransactions_ = stateStruct->parsedCount_.load(memory_order_relaxed);

   for (auto& thr : parserThrVec)
      if (thr.joinable())
         thr.join();

   if (stateStruct->unresolvedHashes_.load(memory_order_relaxed) > 0)
      throw runtime_error("checkChain failed with unresolved hash errors");

   if (stateStruct->unsupportedSigHash_.load(memory_order_relaxed) > 0)
      throw runtime_error("checkChain failed with unsupported sig hash errors");

   if (stateStruct->unknownErrors_.load(memory_order_relaxed) > 0)
      throw runtime_error("checkChain failed with unknown errors");

   LOGINFO << "Done checking chain";
}

/////////////////////////////////////////////////////////////////////////////
void DatabaseBuilder::verifyTxFilters()
{
   LOGINFO << "verifying txfilters integrity";

   atomic<unsigned> fileCounter;
   fileCounter.store(0, memory_order_relaxed);

   auto checkThr = [&](void)->void
   {
      LMDBEnv::Transaction tx;
      db_->beginDBTransaction(&tx, TXFILTERS, LMDB::ReadOnly);

      map<unsigned, set<unsigned>> mismatches;

      while (1)
      {
         unsigned fileNum = fileCounter.fetch_add(1, memory_order_relaxed);
         try
         {
            auto&& pool = db_->getFilterPoolRefForFileNum<TxFilterType>(fileNum);
            auto&& filters = pool.getFilterPoolPtr();

            for (auto& filter : filters)
            {
               //check filter blockid is for this block file
               auto& header = blockchain_->getHeaderById(filter.getBlockKey());
               if (header.getBlockFileNum() != fileNum)
               {
                  auto& mismatchSet = mismatches[header.getBlockFileNum()];
                  mismatchSet.insert(filter.getBlockKey());
               }
            }

            if (mismatches.size() > 0)
            {
               LOGWARN << "filter for file #" << fileNum << 
                  " mismatches to " << mismatches.size() << " files";
               for (auto& mm_set : mismatches)
               {
                  LOGERR << " === " << mm_set.second.size() << 
                     " blocks to file #" << mm_set.first;
               }
            }
         }
         catch (runtime_error&)
         {
            if (fileNum < blockFiles_.fileCount())
               LOGWARN << "couldnt get filter pool for file: " << fileNum;
            return;
         }
      }
   };

   vector<thread> thrs;
   for (unsigned i = 1; i < bdmConfig_.threadCount_; i++)
      thrs.push_back(thread(checkThr));
   checkThr();

   for (auto& thr : thrs)
      if (thr.joinable())
         thr.join();
   
   LOGINFO << "done checking txfilters";
}