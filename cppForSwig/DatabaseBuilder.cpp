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
   magicBytes_(db_->getMagicBytes()), topBlockOffset_(0, 0)
{}


/////////////////////////////////////////////////////////////////////////////
void DatabaseBuilder::init()
{
   //list all files in block data folder
   blockFiles_.detectAllBlockFiles();

   //read all blocks already in DB and populate blockchain
   topBlockOffset_ = loadBlockHeadersFromDB(progress_);
   blockchain_.forceOrganize();

   //update db
   updateBlocksInDB(progress_);

   //blockchain object now has the longest chain, update the wallets history
   //1) retrieve all tracked addresses from DB
   scrAddrFilter_->getAllScrAddrInDB();

   //2) determine from which block to start scanning
   scrAddrFilter_->getScrAddrCurrentSyncState();
   auto scanFrom = scrAddrFilter_->scanFrom();

   //don't scan without any registered addresses
   if (scrAddrFilter_->getScrAddrMap().size() == 0)
      return;

   while (1)
   {
      //3) scan it!
      auto topScannedBlockHash = updateTransactionHistory(scanFrom);

      //4) make sure the topScannedBlockHash matches the top block hash
      //in the blockchain object
      if (topScannedBlockHash == blockchain_.top().getThisHash())
         break;

      //if we got this far the scan failed, diagnose the DB and repair it
   }
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
   const ProgressCallback &progress)
{
   //TODO: squeeze in the progress callback

   //preload and prefetch
   BlockDataLoader bdl(blockFiles_.folderPath(), true, true);

   auto addblocks = [&](uint16_t fileID, size_t startOffset, 
      BlockOffset& bo)->void
   {
      //TODO: use only the BlockOffset argument
      while (1)
      {
         if (!addBlocksToDB(bdl, fileID, startOffset, bo))
            return;

         //reset startOffset for the next file
         startOffset = 0;
         fileID += thread::hardware_concurrency();
      }
   };

   //TODO: don't run more threads than there are blkfiles to read

   vector<thread> tIDs;
   vector<BlockOffset> boVec;
   for (unsigned i = 1; i < thread::hardware_concurrency(); i++)
   {
      boVec.push_back(topBlockOffset_);
      auto& bo = boVec.back();
      tIDs.push_back(thread(addblocks, topBlockOffset_.fileID_ + i, 0, bo));
   }

   boVec.push_back(topBlockOffset_);
   auto& bo = boVec.back();
   addblocks(topBlockOffset_.fileID_, topBlockOffset_.offset_, bo);

   for (auto& tID : tIDs)
   {
      if (tID.joinable())
         tID.join();
   }

   for (auto& blockoffset : boVec)
   {
      if (blockoffset > topBlockOffset_)
         topBlockOffset_ = blockoffset;
   }

   //done parsing new blocks, let's add them to the DB

   auto&& reorgState = blockchain_.organize();
   blockchain_.putNewBareHeaders(db_);

   return reorgState;
}

/////////////////////////////////////////////////////////////////////////////
bool DatabaseBuilder::addBlocksToDB(BlockDataLoader& bdl, 
   uint16_t fileID, size_t startOffset, BlockOffset& bo)
{
   auto&& blockfilemappointer = bdl.get(fileID, true);
   auto ptr = blockfilemappointer.get()->getPtr();

   //ptr is null if we're out of block files
   if (ptr == nullptr)
      return false;

   vector<StoredHeader> sbhVec;

   auto tallyBlocks = [&](const uint8_t* data, size_t size, size_t offset)->void
   {
      //deser full block, check merkle
      StoredHeader sbh;
      BinaryRefReader brr(data, size);

      try
      {
         //this call unserializes too much (we're just verifying the merkle for 
         //consistentcy), replace it with something lighter.
         sbh.unserializeFullBlock(brr, false, false);
      }
      catch (...)
      {
         //deser failed, ignore this block
         return;
      }

      //block is valid, add to container
      //build header version of block first
      sbh.fileID_ = fileID;
      sbh.offset_ = offset;
      
      BlockOffset blockoffset(fileID, offset + sbh.numBytes_);
      if (blockoffset > bo)
         bo = blockoffset;

      sbhVec.push_back(sbh);
   };

   parseBlockFile(ptr, blockfilemappointer.size(),
      startOffset, tallyBlocks);


   //done parsing, add the headers to the blockchain object
   //convert StoredHeader vector to BlockHeader map first
   map<HashString, BlockHeader> bhmap;
   for (auto& sbh : sbhVec)
      bhmap.insert(make_pair(sbh.thisHash_, sbh.getBlockHeaderCopy()));

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
         BinaryDataRef theFile(fileMap + localProgress, fileSize - progress);
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
   BlockchainScanner bcs(&blockchain_, db_, scrAddrFilter_,
      blockFiles_);
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
   auto&& reorgState = updateBlocksInDB(progress_);

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

   return blockchain_.top().getBlockHeight();
}

/////////////////////////////////////////////////////////////////////////////
void DatabaseBuilder::undoHistory(
   Blockchain::ReorganizationState& reorgState)
{

}
