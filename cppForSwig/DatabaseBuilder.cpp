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

/////////////////////////////////////////////////////////////////////////////
DatabaseBuilder::DatabaseBuilder(BlockFiles& blockFiles, 
   BlockDataManager_LevelDB& bdm,
   const ProgressCallback &progress)
   : blockFiles_(blockFiles), db_(bdm.getIFace()),
   blockchain_(bdm.blockchain()),
   scrAddrFilter_(bdm.getScrAddrFilter()),
   progress_(progress),
   magicBytes_(db_->getMagicBytes()), topBlockOffset_(0, 0),
   threadCount_(getThreadCount())
{}


/////////////////////////////////////////////////////////////////////////////
void DatabaseBuilder::init()
{
   //TODO: lower thread count for unit test builds
   TIMER_START("initdb");

   //list all files in block data folder
   blockFiles_.detectAllBlockFiles();

   //read all blocks already in DB and populate blockchain
   topBlockOffset_ = loadBlockHeadersFromDB(progress_);
   blockchain_.forceOrganize();
   blockchain_.setDuplicateIDinRAM(db_);

   //update db
   TIMER_START("updateblocksindb");
   LOGINFO << "updating HEADERS db";
   auto reorgState = updateBlocksInDB(progress_, true);
   TIMER_STOP("updateblocksindb");
   double updatetime = TIMER_READ_SEC("updateblocksindb");
   LOGINFO << "updated HEADERS db in " << updatetime << "s";

   //blockchain object now has the longest chain, update address history
   //retrieve all tracked addresses from DB
   scrAddrFilter_->getAllScrAddrInDB();

   //determine from which block to start scanning
   scrAddrFilter_->getScrAddrCurrentSyncState();
   auto scanFrom = scrAddrFilter_->scanFrom();

   if (!reorgState.prevTopBlockStillValid)
   {
      //reorg
      undoHistory(reorgState);

      scanFrom = min(
         scanFrom, reorgState.reorgBranchPoint->getBlockHeight() + 1);
   }
   
   //don't scan without any registered addresses
   if (scrAddrFilter_->getScrAddrMap().size() == 0)
      return;
   
   //check against last db state
   StoredDBInfo sdbi;
   db_->getStoredDBInfo(HISTORY, sdbi);
   if (sdbi.topBlkHgt_ >= blockchain_.top().getBlockHeight())
      return;

   LOGINFO << "scanning new blocks";
   TIMER_START("scanning");
   while (1)
   {
      auto topScannedBlockHash = updateTransactionHistory(scanFrom);

      if (topScannedBlockHash == blockchain_.top().getThisHash())
         break;

      //if we got this far the scan failed, diagnose the DB and repair it

      LOGWARN << "topScannedBlockHash does match the hash of the current top";
      LOGWARN << "current top is height #" << blockchain_.top().getBlockHeight();

      try
      {
         auto& topscannedblock = blockchain_.getHeaderByHash(topScannedBlockHash);
         LOGWARN << "topScannedBlockHash is height #" << topscannedblock.getBlockHeight();
      }
      catch (...)
      {
         LOGWARN << "topScannedBlockHash is invalid";
      }

      LOGINFO << "repairing DB";

      //TODO: implement repair procedure
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
   blockchain_.clear();

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
      blockchain_.addBlock(h.getThisHash(), h, height, dup);

      BlockOffset currblock(h.getBlockFileNum(), h.getOffset());
      if (currblock > topBlockOffet)
         topBlockOffet = currblock;

      calc.advance(counter++);
      progress(BDMPhase_DBHeaders, 
         calc.fractionCompleted(), calc.remainingSeconds(), counter);
   };

   db_->readAllHeaders(callback);

   LOGINFO << "Found " << blockchain_.allHeaders().size() << " headers in db";

   return topBlockOffet;
}

/////////////////////////////////////////////////////////////////////////////
Blockchain::ReorganizationState DatabaseBuilder::updateBlocksInDB(
   const ProgressCallback &progress, bool verbose)
{
   //TODO: squeeze in the progress callback

   //preload and prefetch
   BlockDataLoader bdl(blockFiles_.folderPath(), true, true, true);

   auto addblocks = [&](uint16_t fileID, size_t startOffset, 
      shared_ptr<BlockOffset> bo, bool verbose)->void
   {
      //TODO: use only the BlockOffset argument
      while (1)
      {
         if (!addBlocksToDB(bdl, fileID, startOffset, bo))
            return;

         if (verbose)
            LOGINFO << "parsed block file #" << fileID;

         //reset startOffset for the next file
         startOffset = 0;
         fileID += threadCount_;
      }
   };

   vector<thread> tIDs;
   vector<shared_ptr<BlockOffset>> boVec;

   unsigned threadcount = min(threadCount_,
      blockFiles_.fileCount() - topBlockOffset_.fileID_);

   for (unsigned i = 1; i < threadcount; i++)
   {
      boVec.push_back(make_shared<BlockOffset>(topBlockOffset_));
      tIDs.push_back(thread(addblocks, topBlockOffset_.fileID_ + i, 0, 
	                  boVec.back(), false));
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

   //done parsing new blocks, let's add them to the DB

   auto&& reorgState = blockchain_.organize(verbose);
   blockchain_.putNewBareHeaders(db_);

   return reorgState;
}

/////////////////////////////////////////////////////////////////////////////
bool DatabaseBuilder::addBlocksToDB(BlockDataLoader& bdl, 
   uint16_t fileID, size_t startOffset, shared_ptr<BlockOffset> bo)
{
   auto&& blockfilemappointer = bdl.get(fileID, true);
   auto ptr = blockfilemappointer.get()->getPtr();

   //ptr is null if we're out of block files
   if (ptr == nullptr)
      return false;

   vector<BlockData> bdVec;

   auto tallyBlocks = [&](const uint8_t* data, size_t size, size_t offset)->void
   {
      //deser full block, check merkle
      BlockData bd;
      BinaryRefReader brr(data, size);

      try
      {
         bd.deserialize(data, size, nullptr, true);
      }
      catch (...)
      {
         //deser failed, ignore this block
         return;
      }

      //block is valid, add to container
      //build header version of block first
      bd.setFileID(fileID);
      bd.setOffset(offset);
      
      BlockOffset blockoffset(fileID, offset + bd.size());
      if (blockoffset > *bo)
         *bo = blockoffset;

      bdVec.push_back(move(bd));
   };

   parseBlockFile(ptr, blockfilemappointer.size(),
      startOffset, tallyBlocks);


   //done parsing, add the headers to the blockchain object
   //convert BlockData vector to BlockHeader map first
   map<HashString, BlockHeader> bhmap;
   for (auto& bd : bdVec)
   {
      auto&& bh = bd.createBlockHeader();
      bhmap.insert(make_pair(bh.getThisHash(), move(bh)));
   }

   //add in bulk
   blockchain_.addBlocksInBulk(bhmap);

   return true;
}

/////////////////////////////////////////////////////////////////////////////
void DatabaseBuilder::parseBlockFile(
   const uint8_t* fileMap, size_t fileSize, size_t startOffset,
   function<void(const uint8_t* data, size_t size, size_t offset)> callback)
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

      //TODO: deal with blocks that advertize more size than they actually use
      //(next block shows up before blockSize bytes)

      callback(fileMap + localProgress, thisBlkSize, progress + localProgress);

      //update progress counters
      fileMap += localProgress + thisBlkSize;
      progress += localProgress + thisBlkSize;
   }
}


/////////////////////////////////////////////////////////////////////////////
BinaryData DatabaseBuilder::updateTransactionHistory(uint32_t startHeight)
{
   //Scan history
   auto topScannedBlockHash = scanHistory(startHeight);

   //return the hash of the last scanned block
   return topScannedBlockHash;
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DatabaseBuilder::scanHistory(uint32_t startHeight)
{
   BlockchainScanner bcs(&blockchain_, db_, scrAddrFilter_.get(),
      blockFiles_, threadCount_);
   bcs.scan(startHeight);
   bcs.updateSSH();

   return bcs.getTopScannedBlockHash();
}

/////////////////////////////////////////////////////////////////////////////
uint32_t DatabaseBuilder::update(void)
{
   //list all files in block data folder
   blockFiles_.detectAllBlockFiles();

   //update db
   auto&& reorgState = updateBlocksInDB(progress_, false);

   uint32_t prevTop = reorgState.prevTopBlock->getBlockHeight();
   if (prevTop == blockchain_.top().getBlockHeight())
      return 0;

   uint32_t startHeight = reorgState.prevTopBlock->getBlockHeight() + 1;

   if (!reorgState.hasNewTop)
      return startHeight - 1;

   if (!reorgState.prevTopBlockStillValid)
   {
      //reorg, undo blocks up to branch point
      undoHistory(reorgState);

      startHeight = reorgState.reorgBranchPoint->getBlockHeight() + 1;
   }

   //scan new blocks   
   BinaryData&& topScannedHash = scanHistory(startHeight);
   if (topScannedHash != blockchain_.top().getThisHash())
      throw runtime_error("scan failure during DatabaseBuilder::update");

   //TODO: recover from failed scan 

   return startHeight;
}

/////////////////////////////////////////////////////////////////////////////
void DatabaseBuilder::undoHistory(
   Blockchain::ReorganizationState& reorgState)
{
   BlockchainScanner bcs(&blockchain_, db_, scrAddrFilter_.get(), 
      blockFiles_, threadCount_);
   bcs.undo(reorgState);

   blockchain_.setDuplicateIDinRAM(db_);
}
