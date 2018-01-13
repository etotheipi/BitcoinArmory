////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //            
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                   
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include <algorithm>
#include <time.h>
#include <stdio.h>
#include "BlockUtils.h"
#include "lmdbpp.h"
#include "Progress.h"
#include "util.h"
#include "BlockchainScanner.h"
#include "DatabaseBuilder.h"

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

static uint64_t scanFor(const uint8_t *in, const uint64_t inLen,
   const uint8_t * bytes, const uint64_t len)
{
   uint64_t offset = 0; // the index mod len which we're in ahead

   do
   {
      bool found = true;
      for (uint64_t i = 0; i < len; i++)
      {
         if (in[i] != bytes[i])
         {
            found = false;
            break;
         }
      }
      if (found)
         return offset;

      in++;
      offset++;

   } while (offset + len< inLen);
   return UINT64_MAX;
}


class BlockDataManager::BitcoinQtBlockFiles
{
   const string blkFileLocation_;
   struct BlkFile
   {
      size_t fnum;
      string path;
      uint64_t filesize;
      uint64_t filesizeCumul;
   };
   
   vector<BlkFile> blkFiles_;
   uint64_t totalBlockchainBytes_=0;
   
   const BinaryData magicBytes_;

   class stopReadingHeaders
   {
   public:
      size_t fnum_;
      size_t pos_;

      stopReadingHeaders(size_t fnum, size_t pos) :
         fnum_(fnum), pos_(pos)
      {}
   };

   class StopReading : public std::exception
   {
   };

public:
   BitcoinQtBlockFiles(const string& blkFileLocation, const BinaryData &magicBytes)
      : blkFileLocation_(blkFileLocation), magicBytes_(magicBytes)
   {
   }
   
   void detectAllBlkFiles()
   {
      unsigned numBlkFiles=0;
      if (blkFiles_.size() > 0)
      {
         numBlkFiles = blkFiles_.size()-1;
         totalBlockchainBytes_ -= blkFiles_.back().filesize;
         blkFiles_.pop_back();
      }
      while(numBlkFiles < UINT16_MAX)
      {
         string path = BtcUtils::getBlkFilename(blkFileLocation_, numBlkFiles);
         uint64_t filesize = BtcUtils::GetFileSize(path);
         if(filesize == FILE_DOES_NOT_EXIST)
            break;

         
         BlkFile f;
         f.fnum = numBlkFiles;
         f.path = path;
         f.filesize = filesize;
         f.filesizeCumul = totalBlockchainBytes_;
         blkFiles_.push_back(f);
         
         totalBlockchainBytes_ += filesize;
         
         numBlkFiles++;
      }
   
      if(numBlkFiles==UINT16_MAX)
      {
         throw runtime_error("Error finding blockchain files (blkXXXX.dat)");
      }
   }
   
   uint64_t totalBlockchainBytes() const { return totalBlockchainBytes_; }
   unsigned numBlockFiles() const { return blkFiles_.size(); }
   
   uint64_t offsetAtStartOfFile(size_t fnum) const
   {
      if (fnum==0) return 0;
      if (fnum >= blkFiles_.size())
         throw std::range_error("block file out of range");
      return blkFiles_[fnum].filesizeCumul;
   }
   
   // find the location of the first block that is not in @p bc
   BlockFilePosition findFirstUnrecognizedBlockHeader(
      Blockchain &bc
   ) 
   {
      auto& allHeaders = bc.allHeaders();
      
      size_t index=0;
      
      for (; index < blkFiles_.size(); index++)
      {
         const BinaryData hash = getFirstHash(blkFiles_[index]);

         if (allHeaders.find(hash) == allHeaders.end())
         { // not found in this file
            if (index == 0)
               return { 0, 0 };
            
            break;
         }
      }
      
      if (index == 0)
         return { 0, 0 };
      index--;
      
      // ok, now "index" is for the last blkfile that we found a header in
      // now lets linearly search this file until we find an unrecognized blk
      
      BlockFilePosition foundAtPosition{ 0, 0 };
            
      bool foundTopBlock = false;
      auto topBlockHash = bc.top()->getThisHash();

      const auto stopIfBlkHeaderRecognized =
      [&allHeaders, &foundAtPosition, &foundTopBlock, &topBlockHash] (
         const BinaryData &blockheader,
         const BlockFilePosition &pos,
         uint32_t blksize
      )
      {
         // always set our position so that eventually it's at the end
         foundAtPosition = pos;
         
         BlockHeader block;
         BinaryRefReader brr(blockheader);
         block.unserialize(brr);
         
         const HashString blockhash = block.getThisHash();
         auto bhIter = allHeaders.find(blockhash);
         
         if(bhIter == allHeaders.end())
            throw StopReading();

         if (bhIter->second->getThisHash() == topBlockHash)
            foundTopBlock = true;

         bhIter->second->setBlockFileNum(pos.first);
         bhIter->second->setBlockFileOffset(pos.second);
      };
      
      uint64_t returnedOffset = UINT64_MAX;
      try
      {
         returnedOffset = readHeadersFromFile(
            blkFiles_[index],
            0,
            stopIfBlkHeaderRecognized
         );
         
      }
      catch (StopReading&)
      {
         // we're fine
      }

      // but we never find the genesis block, because
      // it always appears in Blockchain even if unloaded, and
      // we need to load it
      if (foundAtPosition.first == 0 && foundAtPosition.second==293)
         return { 0, 0 };
      if (returnedOffset != UINT64_MAX)
         foundAtPosition.second = returnedOffset;


      if (!foundTopBlock)
      {
         LOGWARN << "Couldn't find top block hash in last seen blk file."
            " Searching for it further down the chain";

         //Couldn't find the top header in the last seen blk file. Since Core
         //0.10, this can be an indicator of missing hashes. Let's find the
         //the top block header in file.
         BlockFilePosition topBlockPos(0, 0);
         auto checkBlkHash = [&topBlockHash, &topBlockPos]
            (const BinaryData &rawBlock,
            const BlockFilePosition &pos,
            uint32_t blksize)->void
         {
            BlockHeader bhUnser(rawBlock);
            if (bhUnser.getThisHash() == topBlockHash)
            {
               topBlockPos = pos;
               throw StopReading();
            }
         };

         bool _foundTopBlock = false;
         int32_t fnum = blkFiles_.size();
         if (fnum > 0)
            fnum--;
         try
         {
            for (; fnum > -1; fnum--)
               readHeadersFromFile(blkFiles_[fnum], 0, 
                                   checkBlkHash);
         }
         catch (StopReading&)
         {
            _foundTopBlock = true;
            // we're fine
         }

         if (!_foundTopBlock)
         {
            //can't find the top header, let's just rescan all headers
            LOGERR << "Failed to find last known top block hash in "
               "blk files. Rescanning all headers";
            
            return BlockFilePosition(0, 0);
         }

         //Check this file to see if we are missing any block hashes in there
         auto& f = blkFiles_[foundAtPosition.first];
         try
         {
            readHeadersFromFile(f, 0, stopIfBlkHeaderRecognized);
         }
         catch (StopReading&)
         {
            //so we are indeed missing some block headers. Let's just scan the 
            //blocks folder for headers
            foundAtPosition.first = 0;
            foundAtPosition.second = 0;

            LOGWARN << "Inconsistent headers DB, attempting repairs";
         }
      }

      return foundAtPosition;
   }

   BlockFilePosition readHeaders(
      BlockFilePosition startAt,
      const function<void(
         const BinaryData &,
         const BlockFilePosition &pos,
         uint32_t blksize
      )> &blockDataCallback
   ) const
   {
      if (startAt.first == blkFiles_.size())
         return startAt;
      if (startAt.first > blkFiles_.size())
         throw std::runtime_error("blkFile out of range");
         
      uint64_t finishOffset=startAt.second;

      try
      {
         while (startAt.first < blkFiles_.size())
         {
            const BlkFile &f = blkFiles_[startAt.first];
            finishOffset = readHeadersFromFile(
               f, startAt.second, blockDataCallback
               );
            startAt.second = 0;
            startAt.first++;
         }
      }
      catch (stopReadingHeaders& e)
      {
         startAt.first++;
         finishOffset = e.pos_;
      }

      return { startAt.first -1, finishOffset };
   }
   
   BlockFilePosition readRawBlocks(
      BlockFilePosition startAt,
      BlockFilePosition stopAt,
      const function<void(
         const BinaryData &,
         const BlockFilePosition &pos,
         uint32_t blksize
      )> &blockDataCallback
   )
   {
      if (startAt.first == blkFiles_.size())
         return startAt;
      if (startAt.first > blkFiles_.size())
         throw std::runtime_error("blkFile out of range");

      stopAt.first = (std::min)(stopAt.first, blkFiles_.size());
         
      uint64_t finishLocation=stopAt.second;
      while (startAt.first <= stopAt.first)
      {
         const BlkFile &f = blkFiles_[startAt.first];
         const uint64_t stopAtOffset
            = startAt.first < stopAt.first ? f.filesize : stopAt.second;
         finishLocation = readRawBlocksFromFile(
            f, startAt.second, stopAtOffset, blockDataCallback
         );
         startAt.second = 0;
         startAt.first++;
      }
      
      return { startAt.first-1, finishLocation };
   }

   void readRawBlocksFromTop(
      uint32_t fnum,
      const function<void(
      const BinaryData &,
      const BlockFilePosition &pos,
      uint32_t blksize
      )> &blockDataCallback
      )
   {
      for (int32_t i = fnum; i > -1; i--)
      {
         const BlkFile &f = blkFiles_[i];
         readRawBlocksFromFile(f, 0, f.filesize, blockDataCallback);
      }
   }


   void getFileAndPosForBlockHash(BlockHeader& blk)
   {
      BlockFilePosition filePos = { 0, 0 };

      //we dont have the file position for this header, let's find it
      class StopReading : public std::exception
      {
      };

      const BinaryData& thisHash = blk.getThisHash();

      const auto stopIfBlkHeaderRecognized =
         [&thisHash, &filePos](
         const BinaryData &blockheader,
         const BlockFilePosition &pos,
         uint32_t blksize
         )
      {
         filePos = pos;

         BlockHeader block;
         BinaryRefReader brr(blockheader);
         block.unserialize(brr);

         const HashString blockhash = block.getThisHash();
         if (blockhash == thisHash)
            throw StopReading();
      };

      try
      {
         //at this point, the last blkFile has been scanned for block, so skip it
         for (int32_t i = blkFiles_.size() - 2; i > -1; i--)
         {
            readHeadersFromFile(
               blkFiles_[i],
               0,
               stopIfBlkHeaderRecognized
               );
         }
      }
      catch (StopReading&)
      {
         // we're fine
      }

      blk.setBlockFileNum(filePos.first);
      blk.setBlockFileOffset(filePos.second);
   }

private:

   struct MapAndSize
   {
      uint8_t* filemap_;
      uint64_t size_;
   };

   MapAndSize getMapOfFile(string path, size_t fileSize)
   {
      MapAndSize mas;

      #ifdef WIN32
         int fd = _open(path.c_str(), _O_RDONLY | _O_BINARY);
         if (fd == -1)
            throw std::runtime_error("failed to open file");
         
         HANDLE fdHandle = (HANDLE)_get_osfhandle(fd);
         uint32_t sizelo = fileSize & 0xffffffff;
         uint32_t sizehi = fileSize >> 16 >> 16;


         HANDLE mh = CreateFileMapping(fdHandle, NULL, 
                              PAGE_READONLY | SEC_COMMIT,
                              sizehi, sizelo, NULL);
         if (mh == NULL)
            throw std::runtime_error("failed to map file");

         mas.filemap_ = (uint8_t*)MapViewOfFile(mh, FILE_MAP_READ,
                             0, 0, fileSize);
         mas.size_ = fileSize;

         if(mas.filemap_ == NULL)
            throw std::runtime_error("failed to map file");

         CloseHandle(mh);
         _close(fd);
      #else
         int fd = open(path.c_str(), O_RDONLY);
         if (fd == -1)
            throw std::runtime_error("failed to open file");

         mas.filemap_ = (uint8_t*)mmap(NULL, fileSize, PROT_READ, MAP_SHARED, fd, 0);
         mas.size_ = fileSize;

         if(mas.filemap_ == NULL)
            throw std::runtime_error("failed to map file");
         close(fd);
      #endif

      return mas;
   }

   void unmapFile(MapAndSize& mas)
   {
      #ifdef WIN32
      if (!UnmapViewOfFile(mas.filemap_))
         throw std::runtime_error("failed to unmap file");
      #else
      if(munmap(mas.filemap_, mas.size_))
         throw std::runtime_error("failed to unmap file");
      #endif
   }
   // read blocks from f, starting at offset blockFileOffset,
   // returning the offset we finished at
   uint64_t readRawBlocksFromFile(
      const BlkFile &f, uint64_t blockFileOffset, uint64_t stopBefore,
      const function<void(
         const BinaryData &,
         const BlockFilePosition &pos,
         uint32_t blksize
      )> &blockDataCallback
   )
   {
      // short circuit
      if (blockFileOffset >= stopBefore)
         return blockFileOffset;
      
      MapAndSize mas = getMapOfFile(f.path, f.filesize);
      BinaryData fileMagic(4);
      memcpy(fileMagic.getPtr(), mas.filemap_, 4);
      if( fileMagic != magicBytes_ )
      {
         LOGERR << "Block file '" << f.path << "' is the wrong network! File: "
            << fileMagic.toHexStr()
            << ", expecting " << magicBytes_.toHexStr();
      }
      // Seek to the supplied offset
      uint64_t pos = blockFileOffset;
      
      {
         BinaryDataRef magic, szstr, rawBlk;
         // read the file, we can't go past what we think is the end,
         // because we haven't gone past that in Headers
         while(pos < (std::min)(f.filesize, stopBefore))
         {
            magic = BinaryDataRef(mas.filemap_ + pos, 4);
            pos += 4;
            if (pos >= f.filesize)
               break;
               
            if(magic != magicBytes_)
            {
               // start scanning for MagicBytes
               uint64_t offset = scanFor(mas.filemap_ + pos, f.filesize - pos,
                  magicBytes_.getPtr(), magicBytes_.getSize());
               if (offset == UINT64_MAX)
               {
                  LOGERR << "No more blocks found in file " << f.path;
                  break;
               }
               
               pos += offset +4;
               LOGERR << "Next block header found at offset " << pos-4;
            }
            
            szstr = BinaryDataRef(mas.filemap_ + pos, 4);
            pos += 4;
            uint32_t blkSize = READ_UINT32_LE(szstr.getPtr());
            if(pos >= f.filesize) 
               break;

            rawBlk = BinaryDataRef(mas.filemap_ +pos, blkSize);
            pos += blkSize;
            
            try
            {
               blockDataCallback(rawBlk, { f.fnum, blockFileOffset }, blkSize);
            }
            catch (std::exception &e)
            {
               // this might very well just mean that we tried to load
               // blkdata past where we loaded headers. This isn't a problem
               LOGERR << e.what() << " (error encountered processing block at byte "
                  << blockFileOffset << " file "
                  << f.path << ", blocksize " << blkSize << ")";
            }
            blockFileOffset = pos;
         }
      }
      
      LOGINFO << "Reading raw blocks finished at file "
         << f.fnum << " offset " << blockFileOffset;
      
      unmapFile(mas);
      return blockFileOffset;
   }
   
   uint64_t readHeadersFromFile(
      const BlkFile &f,
      uint64_t blockFileOffset,
      const function<void(
         const BinaryData &,
         const BlockFilePosition &pos,
         uint32_t blksize
      )> &blockDataCallback
   ) const
   {
      ifstream is(f.path, ios::binary);
      {
         BinaryData fileMagic(4);
         is.read(reinterpret_cast<char*>(fileMagic.getPtr()), 4);

         if( fileMagic != magicBytes_)
         {
            std::ostringstream ss;
            ss << "Block file '" << f.path << "' is the wrong network! File: "
               << fileMagic.toHexStr()
               << ", expecting " << magicBytes_.toHexStr();
            throw runtime_error(ss.str());
         }
      }
      is.seekg(blockFileOffset, ios::beg);
      
      {
         const uint32_t HEAD_AND_NTX_SZ = HEADER_SIZE + 10; // enough
         BinaryData magic(4), szstr(4), rawHead(HEAD_AND_NTX_SZ);
         while(!is.eof())
         {
            is.read((char*)magic.getPtr(), 4);
            if (is.eof())
               break;
               
            if(magic != magicBytes_)
            {
               // I have to start scanning for MagicBytes
               if (!scanFor(is, magicBytes_.getPtr(), magicBytes_.getSize()))
               {
                  break;
               }
               
               LOGERR << "Next block header found at offset " << uint64_t(is.tellg())-4;
            }
            
            is.read(reinterpret_cast<char*>(szstr.getPtr()), 4);
            uint32_t nextBlkSize = READ_UINT32_LE(szstr.getPtr());
            if(is.eof()) break;

            is.read(reinterpret_cast<char*>(rawHead.getPtr()), HEAD_AND_NTX_SZ); // plus #tx var_int
            try
            {
               blockDataCallback(rawHead, { f.fnum, blockFileOffset }, nextBlkSize);
            }
            catch (debug_replay_blocks&)
            {
               blockFileOffset += nextBlkSize + 8;
               throw stopReadingHeaders(f.fnum, blockFileOffset);
            }
            
            blockFileOffset += nextBlkSize+8;
            is.seekg(nextBlkSize - HEAD_AND_NTX_SZ, ios::cur);
         }
      }
      
      return blockFileOffset;
   }
      

   BinaryData getFirstHash(const BlkFile &f) const
   {
      ifstream is(f.path, ios::binary);
      is.seekg(0, ios::end);
      if(is.tellg() < 88)
      {
         LOGERR << "File: " << f.path << " is less than 88 bytes!";
         return {};
      }
      is.seekg(0, ios::beg);
      
      BinaryData magic(4), szstr(4), rawHead(HEADER_SIZE);
      
      is.read(magic.getCharPtr(), 4);
      is.read(szstr.getCharPtr(), 4);
      if(magic != magicBytes_)
      {
         LOGERR << "Magic bytes mismatch.  Block file is for another network!";
         return {};
      }
      
      is.read(rawHead.getCharPtr(), HEADER_SIZE);
      BinaryData h(32);
      BtcUtils::getHash256(rawHead, h);
      return h;
   }
};

////////////////////////////////////////////////////////////////////////////////
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
      return (total_-lastSample_)/unitsPerSecond();
   }
};



class BlockDataManager::BDM_ScrAddrFilter : public ScrAddrFilter
{
   BlockDataManager *const bdm_;
   //0: didn't start, 1: is initializing, 2: done initializing
   
public:
   BDM_ScrAddrFilter(BlockDataManager *bdm)
      : ScrAddrFilter(bdm->getIFace(), bdm->config().armoryDbType_)
      , bdm_(bdm)
   {
   
   }

   virtual shared_ptr<ScrAddrFilter> copy()
   {
      shared_ptr<ScrAddrFilter> sca = make_shared<BDM_ScrAddrFilter>(bdm_);
      return sca;
   }

protected:
   virtual bool bdmIsRunning() const
   {
      return bdm_->BDMstate_ != BDM_offline;
   }
   
   virtual BinaryData applyBlockRangeToDB(
      uint32_t startBlock, uint32_t endBlock, 
      const vector<string>& wltIDs, bool reportProgress
   )
   {
      //make sure sdbis are initialized (fresh ids wont have sdbi entries)
      try
      {
         auto&& sdbi = getSshSDBI();
      }
      catch (runtime_error&)
      {
         StoredDBInfo sdbi;
         sdbi.magic_ = config().magicBytes_;
         sdbi.metaHash_ = BtcUtils::EmptyHash_;
         sdbi.topBlkHgt_ = 0;
         sdbi.armoryType_ = config().armoryDbType_;

         //write sdbi
         putSshSDBI(sdbi);
      }

      try
      {
         auto&& sdbi = getSubSshSDBI();
      }
      catch (runtime_error&)
      {
         StoredDBInfo sdbi;
         sdbi.magic_ = config().magicBytes_;
         sdbi.metaHash_ = BtcUtils::EmptyHash_;
         sdbi.topBlkHgt_ = 0;
         sdbi.armoryType_ = config().armoryDbType_;

         //write sdbi
         putSubSshSDBI(sdbi);
      }
      
      const auto progress
         = [&](BDMPhase phase, double prog, unsigned time, unsigned numericProgress)
      {
         if (!reportProgress)
            return;

         auto&& notifPtr = make_unique<BDV_Notification_Progress>(
            phase, prog, time, numericProgress, wltIDs);

         bdm_->notificationStack_.push_back(move(notifPtr));
      };

      return bdm_->applyBlockRangeToDB(progress, startBlock, endBlock, *this, false);
   }
   
   virtual uint32_t currentTopBlockHeight() const
   {
      return bdm_->blockchain()->top()->getBlockHeight();
   }
   
   virtual void wipeScrAddrsSSH(const vector<BinaryData>& saVec)
   {
      bdm_->getIFace()->resetHistoryForAddressVector(saVec);
   }

   virtual shared_ptr<Blockchain> blockchain(void)
   {
      return bdm_->blockchain();
   }

   virtual BlockDataManagerConfig config(void)
   {
      return bdm_->config();
   }
};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// Start BlockDataManager methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BlockDataManager::BlockDataManager(
   const BlockDataManagerConfig &bdmConfig) 
   : config_(bdmConfig)
{

   if (bdmConfig.exceptionPtr_ != nullptr)
   {
      exceptPtr_ = bdmConfig.exceptionPtr_;
      return;
   }
   
   blockchain_ = make_shared<Blockchain>(config_.genesisBlockHash_);

   iface_ = new LMDBBlockDatabase(blockchain_, 
      config_.blkFileLocation_, config_.armoryDbType_);

   readBlockHeaders_ = make_shared<BitcoinQtBlockFiles>(
      config_.blkFileLocation_,
      config_.magicBytes_
      );

   nodeStatusPollMutex_ = make_shared<mutex>();

   try
   {
      openDatabase();
      
      if (bdmConfig.nodeType_ == Node_BTC)
      {
         networkNode_ = make_shared<BitcoinP2P>("127.0.0.1", config_.btcPort_,
            *(uint32_t*)config_.magicBytes_.getPtr());
         nodeRPC_ = make_shared<NodeRPC>(config_);
      }
      else if (bdmConfig.nodeType_ == Node_UnitTest)
      {
         networkNode_ = make_shared<NodeUnitTest>("127.0.0.1", config_.btcPort_,
            *(uint32_t*)config_.magicBytes_.getPtr());
         nodeRPC_ = make_shared<NodeRPC_UnitTest>(config_);
      }
      else
      {
         throw DbErrorMsg("invalid node type in bdmConfig");
      }

      config_.armoryDbType_ = iface_->armoryDbType();

      zeroConfCont_ = make_shared<ZeroConfContainer>(
         iface_, networkNode_, config_.zcThreadCount_);
      scrAddrData_ = make_shared<BDM_ScrAddrFilter>(this);
   }
   catch (...)
   {
      exceptPtr_ = current_exception();
   }
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager::openDatabase()
{
   LOGINFO << "blkfile dir: " << config_.blkFileLocation_;
   LOGINFO << "lmdb dir: " << config_.dbDir_;
   if (config_.genesisBlockHash_.getSize() == 0)
   {
      throw runtime_error("ERROR: Genesis Block Hash not set!");
   }

   try
   {
      iface_->openDatabases(
         config_.dbDir_,
         config_.genesisBlockHash_,
         config_.genesisTxHash_,
         config_.magicBytes_);
   }
   catch (runtime_error &e)
   {
      stringstream ss;
      ss << "DB failed to open, reporting the following error: " << e.what();
      throw runtime_error(ss.str());
   }
}

/////////////////////////////////////////////////////////////////////////////
BlockDataManager::~BlockDataManager()
{
   zeroConfCont_.reset();
   blockFiles_.reset();
   dbBuilder_.reset();
   networkNode_.reset();
   readBlockHeaders_.reset();
   scrAddrData_.reset();
   
   if (iface_ != nullptr)
      iface_->closeDatabases();
   delete iface_;

   blockchain_.reset();
}

/////////////////////////////////////////////////////////////////////////////
// This used to be "rescanBlocks", but now "scanning" has been replaced by
// "reapplying" the blockdata to the databases.  Basically assumes that only
// raw blockdata is stored in the DB with no ssh objects.  This goes through
// and processes every Tx, creating new SSHs if not there, and creating and
// marking-spent new TxOuts.  
BinaryData BlockDataManager::applyBlockRangeToDB(
   ProgressCallback prog, 
   uint32_t blk0, uint32_t blk1, 
   ScrAddrFilter& scrAddrData,
   bool updateSDBI)
{
   // Start scanning and timer
   BlockchainScanner bcs(blockchain_, iface_, &scrAddrData, 
      *blockFiles_.get(), config_.threadCount_, config_.ramUsage_,
      prog, config_.reportProgress_);
   bcs.scan_nocheck(blk0);
   bcs.updateSSH(true);
   bcs.resolveTxHashes();

   return bcs.getTopScannedBlockHash();
}

/////////////////////////////////////////////////////////////////////////////
/*  This is not currently being used, and is actually likely to change 
 *  a bit before it is needed, so I have just disabled it.
vector<TxRef*> BlockDataManager::findAllNonStdTx(void)
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
void BlockDataManager::resetDatabases(ResetDBMode mode)
{
   if (mode == Reset_SSH)
   {
      iface_->resetSSHdb();
      return;
   }

   if (config_.armoryDbType_ != ARMORY_DB_SUPER)
   {
      //we keep all scrAddr data in between db reset/clear
      scrAddrData_->getAllScrAddrInDB();
   }
   
   switch (mode)
   {
   case Reset_Rescan:
      iface_->resetHistoryDatabases();
      break;

   case Reset_Rebuild:
      iface_->destroyAndResetDatabases();
      blockchain_->clear();
      break;
   }


   if (config_.armoryDbType_ != ARMORY_DB_SUPER)
   {
      //reapply scrAddrData_'s content to the db
      scrAddrData_->putAddrMapInDB();

      scrAddrData_->clear();
   }
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager::doInitialSyncOnLoad(
   const ProgressCallback &progress
)
{
   LOGINFO << "Executing: doInitialSyncOnLoad";
   loadDiskState(progress);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager::doInitialSyncOnLoad_Rescan(
   const ProgressCallback &progress
)
{
   LOGINFO << "Executing: doInitialSyncOnLoad_Rescan";
   resetDatabases(Reset_Rescan);
   loadDiskState(progress, true);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager::doInitialSyncOnLoad_Rebuild(
   const ProgressCallback &progress
)
{
   LOGINFO << "Executing: doInitialSyncOnLoad_Rebuild";
   resetDatabases(Reset_Rebuild);
   loadDiskState(progress, true);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager::doInitialSyncOnLoad_RescanBalance(
   const ProgressCallback &progress
   )
{
   LOGINFO << "Executing: doInitialSyncOnLoad_RescanBalance";
   resetDatabases(Reset_SSH);
   loadDiskState(progress, false);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager::loadDiskState(
   const ProgressCallback &progress,
   bool forceRescan
)
{  
   BDMstate_ = BDM_initializing;
         
   blockFiles_ = make_shared<BlockFiles>(config_.blkFileLocation_);
   dbBuilder_ = make_shared<DatabaseBuilder>(*blockFiles_, *this, progress);
   dbBuilder_->init();

   if (config_.checkChain_)
      checkTransactionCount_ = dbBuilder_->getCheckedTxCount();

   BDMstate_ = BDM_ready;
}

////////////////////////////////////////////////////////////////////////////////
Blockchain::ReorganizationState BlockDataManager::readBlkFileUpdate(
   const BlockDataManager::BlkFileUpdateCallbacks& callbacks
)
{ 
   return dbBuilder_->update();
}

////////////////////////////////////////////////////////////////////////////////
StoredHeader BlockDataManager::getBlockFromDB(uint32_t hgt, uint8_t dup) const
{

   // Get the full block from the DB
   StoredHeader returnSBH;
   if(!iface_->getStoredHeader(returnSBH, hgt, dup))
      return {};

   return returnSBH;

}

////////////////////////////////////////////////////////////////////////////////
StoredHeader BlockDataManager::getMainBlockFromDB(uint32_t hgt) const
{
   uint8_t dupMain = iface_->getValidDupIDForHeight(hgt);
   return getBlockFromDB(hgt, dupMain);
}
   
////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScrAddrFilter> BlockDataManager::getScrAddrFilter(void) const
{
   return scrAddrData_;
}

////////////////////////////////////////////////////////////////////////////////
shared_future<bool> BlockDataManager::registerAddressBatch(
   const set<BinaryData>& addrSet, bool isNew)
{
   auto waitOnPromise = make_shared<promise<bool>>();
   shared_future<bool> waitOnFuture = waitOnPromise->get_future();

   auto callback = [waitOnPromise](bool refresh)->void
   {
      waitOnPromise->set_value(refresh);
   };

   shared_ptr<ScrAddrFilter::WalletInfo> wltInfo = 
      make_shared<ScrAddrFilter::WalletInfo>();
   wltInfo->scrAddrSet_ = addrSet;
   wltInfo->callback_ = callback;

   vector<shared_ptr<ScrAddrFilter::WalletInfo>> wltInfoVec;
   wltInfoVec.push_back(move(wltInfo));

   scrAddrData_->registerAddressBatch(move(wltInfoVec), isNew);

   return waitOnFuture;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager::enableZeroConf(bool clearMempool)
{
   if (zeroConfCont_ == nullptr)
      throw runtime_error("null zc object");

   zeroConfCont_->init(scrAddrData_, clearMempool);
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager::isZcEnabled(void) const
{
   if (zeroConfCont_ == nullptr)
      return false;

   return zeroConfCont_->isEnabled();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager::disableZeroConf(void)
{
   if (zeroConfCont_ == nullptr)
      return;

   zeroConfCont_->shutdown();
}

////////////////////////////////////////////////////////////////////////////////
NodeStatusStruct BlockDataManager::getNodeStatus() const
{
   NodeStatusStruct nss;
   if (networkNode_ == nullptr)
      return nss;
   
   if(networkNode_->connected())
      nss.status_ = NodeStatus_Online;

   if (networkNode_->isSegWit())
      nss.SegWitEnabled_ = true;

   if (nodeRPC_ == nullptr)
      return nss;

   nss.rpcStatus_ = nodeRPC_->testConnection();
   if (nss.rpcStatus_ != RpcStatus_Online)
      pollNodeStatus();

   nss.chainState_ = nodeRPC_->getChainStatus();
   return nss;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager::pollNodeStatus() const
{
   if (!nodeRPC_->canPool())
      return;

   unique_lock<mutex> lock(*nodeStatusPollMutex_, defer_lock);

   if (!lock.try_lock())
      return;

   auto poll_thread = [this](void)->void
   {
      auto nodeRPC = this->nodeRPC_;
      auto mutexPtr = this->nodeStatusPollMutex_;

      unique_lock<mutex> lock(*mutexPtr);

      unsigned count = 0;
      while (nodeRPC->testConnection() != RpcStatus_Online)
      {
         ++count;
         if (count > 10)
            break; //give up after 20sec

         this_thread::sleep_for(chrono::seconds(2));
      }
   };

   thread pollThr(poll_thread);
   if (pollThr.joinable())
      pollThr.detach();
}