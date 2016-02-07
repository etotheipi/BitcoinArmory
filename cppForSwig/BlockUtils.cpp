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
#include "BlockWriteBatcher.h"
#include "lmdbpp.h"
#include "Progress.h"
#include "util.h"
#include "DatabaseBuilder.h"

#include "ReorgUpdater.h"

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

class BlockDataManager_LevelDB::BitcoinQtBlockFiles
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
      map<HashString, BlockHeader> &allHeaders = bc.allHeaders();
      
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
      auto topBlockHash = bc.top().getThisHash();

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

         if (bhIter->second.getThisHash() == topBlockHash)
            foundTopBlock = true;

         bhIter->second.setBlockFileNum(pos.first);
         bhIter->second.setBlockFileOffset(pos.second);
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

         bool foundTopBlock = false;
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
            foundTopBlock = true;
            // we're fine
         }

         if (!foundTopBlock)
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
}

BlockDataManagerConfig::BlockDataManagerConfig(const BlockDataManagerConfig& in)
{
   *this = in;
}

BlockDataManagerConfig& BlockDataManagerConfig::operator=(
   const BlockDataManagerConfig& in)
{
   if (this != &in)
   {
      armoryDbType = ARMORY_DB_BARE;
      pruneType = DB_PRUNE_NONE;

      blkFileLocation = in.blkFileLocation;
      levelDBLocation = in.levelDBLocation;

      genesisBlockHash = in.genesisBlockHash;
      genesisTxHash = in.genesisTxHash;
      magicBytes = in.magicBytes;
   }

   return *this;
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
      return (total_-lastSample_)/unitsPerSecond();
   }
};



class BlockDataManager_LevelDB::BDM_ScrAddrFilter : public ScrAddrFilter
{
   BlockDataManager_LevelDB *const bdm_;
   //0: didn't start, 1: is initializing, 2: done initializing
   
public:
   BDM_ScrAddrFilter(BlockDataManager_LevelDB *bdm)
      : ScrAddrFilter(bdm->getIFace(), bdm->config().armoryDbType)
      , bdm_(bdm)
   {
   
   }

   virtual BDM_ScrAddrFilter* copy()
   {
      return new BDM_ScrAddrFilter(bdm_);
   }

protected:
   virtual bool bdmIsRunning() const
   {
      return bdm_->BDMstate_ != BDM_offline;
   }
   
   virtual BinaryData applyBlockRangeToDB(
      uint32_t startBlock, uint32_t endBlock, 
      const vector<string>& wltIDs
   )
   {
      class WalletIdProgressReporter : public ProgressReporter
      {
         const vector<string>& wIDs_;
         const function<void(const vector<string>&, double prog,unsigned time)> &cb;
      public:
         WalletIdProgressReporter(
            const vector<string>& wIDs,
            const function<void(const vector<string>&, double prog,unsigned time)> &cb
         )
            : wIDs_(wIDs), cb(cb) {}
         
         virtual void progress(
            double progress, unsigned secondsRemaining
         )
         {
            cb(wIDs_, progress, secondsRemaining);
         }
      };
   
      WalletIdProgressReporter progress(wltIDs, scanThreadProgressCallback_);
      
      //pass to false to skip SDBI top block updates
      return bdm_->applyBlockRangeToDB(progress, startBlock, endBlock, *this, false);
   }
   
   virtual uint32_t currentTopBlockHeight() const
   {
      return bdm_->blockchain().top().getBlockHeight();
   }
   
   virtual void flagForScanThread(void)
   {
      bdm_->sideScanFlag_ = true;
   }

   virtual void wipeScrAddrsSSH(const vector<BinaryData>& saVec)
   {
      bdm_->wipeScrAddrsSSH(saVec);
   }

   virtual Blockchain& blockchain(void)
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
// Start BlockDataManager_LevelDB methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BlockDataManager_LevelDB::BlockDataManager_LevelDB(const BlockDataManagerConfig &bdmConfig) 
   : config_(bdmConfig)
   , blockchain_(config_.genesisBlockHash)
{
   auto isready = [this](void)->bool { return this->isReady(); };
   iface_ = new LMDBBlockDatabase(isready);

   scrAddrData_ = make_shared<BDM_ScrAddrFilter>(this);
   setConfig(bdmConfig);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::setConfig(
   const BlockDataManagerConfig &bdmConfig)
{
   config_ = bdmConfig;
   readBlockHeaders_ = make_shared<BitcoinQtBlockFiles>(
      config_.blkFileLocation,
      config_.magicBytes
   );
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::openDatabase()
{
   LOGINFO << "blkfile dir: " << config_.blkFileLocation;
   LOGINFO << "lmdb dir: " << config_.levelDBLocation;
   if (config_.genesisBlockHash.getSize() == 0)
   {
      throw runtime_error("ERROR: Genesis Block Hash not set!");
   }

   try
   {
      iface_->openDatabases(
         config_.levelDBLocation,
         config_.genesisBlockHash,
         config_.genesisTxHash,
         config_.magicBytes,
         config_.armoryDbType,
         config_.pruneType);
   }
   catch (runtime_error &e)
   {
      stringstream ss;
      ss << "DB failed to open, reporting the following error: " << e.what();
      throw runtime_error(ss.str());
   }
   catch (...)
   {
      stringstream ss;
      ss << "DB failed to open, unknown error";
      ss >> criticalError_;
      throw runtime_error(ss.str());
   }

}

/////////////////////////////////////////////////////////////////////////////
BlockDataManager_LevelDB::~BlockDataManager_LevelDB()
{
   iface_->closeDatabases();
   scrAddrData_.reset();
   delete iface_;
}

// returns where we left off and the blockheaders
pair<BlockFilePosition, vector<BlockHeader*>>
   BlockDataManager_LevelDB::loadBlockHeadersStartingAt(
      ProgressReporter &prog,
      const BlockFilePosition &fileAndOffset
   )
{
   readBlockHeaders_->detectAllBlkFiles();
   
   vector<BlockHeader*> blockHeadersAdded;
   
   ProgressFilter progfilter(
      &prog,
      readBlockHeaders_->totalBlockchainBytes()
   );
   uint64_t totalOffset=0;
   bool suppressOutput = false;
   if (fileAndOffset.first == 0 && fileAndOffset.second == 0)
      suppressOutput = true;
   
   class StopReading {};

   auto blockHeaderCallback
      = [&] (const BinaryData &blockdata, const BlockFilePosition &pos, uint32_t blksize)
      {
         BlockHeader block;
         BinaryRefReader brr(blockdata);
         block.unserialize(brr);
         
         const HashString blockhash = block.getThisHash();
         
         const uint32_t nTx = brr.get_var_int();
         BlockHeader& addedBlock = blockchain().addNewBlock(
            blockhash, block, suppressOutput);

         blockHeadersAdded.push_back(&addedBlock);

         addedBlock.setBlockFileNum(pos.first);
         addedBlock.setBlockFileOffset(pos.second);
         addedBlock.setNumTx(nTx);
         addedBlock.setBlockSize(blksize);
         
         totalOffset += blksize+8;
         progfilter.advance(totalOffset);

#ifdef _DEBUG_REPLAY_BLOCKS
         if (fileAndOffset.first == 0)
         {
            if (pos.first == readBlockHeaders_->numBlockFiles() -1)
               throw debug_replay_blocks();
         }
         else
            throw debug_replay_blocks();
#endif
      };
   
   BlockFilePosition position
         = readBlockHeaders_->readHeaders(fileAndOffset, blockHeaderCallback);

   return { position, blockHeadersAdded };
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
// This used to be "rescanBlocks", but now "scanning" has been replaced by
// "reapplying" the blockdata to the databases.  Basically assumes that only
// raw blockdata is stored in the DB with no SSH objects.  This goes through
// and processes every Tx, creating new SSHs if not there, and creating and
// marking-spent new TxOuts.  
BinaryData BlockDataManager_LevelDB::applyBlockRangeToDB(
   ProgressReporter &prog, 
   uint32_t blk0, uint32_t blk1, 
   ScrAddrFilter& scrAddrData,
   bool updateSDBI)
{
   // compute how many bytes of raw blockdata we're going to apply
   uint64_t startingAt=0, totalBytes=0;
   for (unsigned i=0; i < blockchain().top().getBlockHeight(); i++)
   {
      const BlockHeader &bh = blockchain().getHeaderByHeight(i);
      if (i < blk0)
         startingAt += bh.getBlockSize();
      totalBytes += bh.getBlockSize();
   }
   
   ProgressFilter progress(&prog, startingAt, totalBytes);
   
   // Start scanning and timer
   BlockWriteBatcher blockWrites(config_, iface_);
   blockWrites.setUpdateSDBI(updateSDBI);

   auto errorLambda = [this](string str)->void
   {  criticalError_ = str;
      this->notifyMainThread(); };
   blockWrites.setCriticalErrorLambda(errorLambda);

   if (blk1 > blockchain_.top().getBlockHeight())
      blk1 = blockchain_.top().getBlockHeight();
   
   LOGWARN << "Scanning from " << blk0 << " to " << blk1;
   return blockWrites.scanBlocks(progress, blk0, blk1, scrAddrData);
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
   if(iface_)
   {
      LOGWARN << "Destroying databases;  will need to be rebuilt";
      iface_->destroyAndResetDatabases();
      return;
   }
   LOGERR << "Attempted to destroy databases, but no DB interface set";
}


/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doInitialSyncOnLoad(
   const ProgressCallback &progress
)
{
   LOGINFO << "Executing: doInitialSyncOnLoad";
   loadDiskState(progress);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doInitialSyncOnLoad_Rescan(
   const ProgressCallback &progress
)
{
   LOGINFO << "Executing: doInitialSyncOnLoad_Rescan";
   loadDiskState(progress, true);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doInitialSyncOnLoad_Rebuild(
   const ProgressCallback &progress
)
{
   LOGINFO << "Executing: doInitialSyncOnLoad_Rebuild";
   destroyAndResetDatabases();
   scrAddrData_->clear();
   blockchain_.clear();
   loadDiskState(progress, true);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doRebuildDatabases(
   const ProgressCallback &progress
)
{
   LOGINFO << "Executing: doRebuildDatabases";
   destroyAndResetDatabases();
   deleteHistories();
   scrAddrData_->clear();
   loadDiskState(progress);
}

void BlockDataManager_LevelDB::loadDiskState(
   const ProgressCallback &progress,
   bool forceRescan
)
{
   class ProgressWithPhase : public ProgressReporter
   {
      const BDMPhase phase_;
      const ProgressCallback progress_;
   public:
      ProgressWithPhase(
         BDMPhase phase,
         const ProgressCallback& progress
      ) : phase_(phase), progress_(progress)
      {
         this->progress(0.0, 0);
      }
      
      virtual void progress(
         double progress, unsigned secondsRemaining
      )
      {
         progress_(phase_, progress, secondsRemaining, 0);
      }
   };
  
   //quick hack to signal scrAddrData_ that the BDM is loading/loaded.
   BDMstate_ = BDM_initializing;
   
   /*readBlockHeaders_->detectAllBlkFiles();
   if (readBlockHeaders_->numBlockFiles()==0)
   {
      throw runtime_error("No blockfiles could be found!");
   }
   LOGINFO << "Total number of blk*.dat files: " << readBlockHeaders_->numBlockFiles();
   LOGINFO << "Total blockchain bytes: " 
      << BtcUtils::numToStrWCommas(readBlockHeaders_->totalBlockchainBytes());
      
   // load the headers from lmdb into blockchain()
   loadBlockHeadersFromDB(progress);

   {
      progress(BDMPhase_OrganizingChain, 0, 0, 0);
      // organize the blockchain we have so far
      const Blockchain::ReorganizationState state
         = blockchain().forceOrganize();
      if(!state.prevTopBlockStillValid)
      {
         LOGERR << "Organize chain indicated reorg in process all headers!";
         LOGERR << "Did we shut down last time on an orphan block?";
      }
   }

   blockchain_.setDuplicateIDinRAM(iface_, true);
   uint32_t lastTop = blockchain_.top().getBlockHeight();
   
   if (forceRescan)
   {
      deleteHistories();
      scrAddrData_->clear();
   }
   
   if (config_.armoryDbType != ARMORY_DB_SUPER)
   {
      LOGWARN << "--- Fetching SSH summaries for "
         << scrAddrData_->numScrAddr() << " registered addresses";
      scrAddrData_->getScrAddrCurrentSyncState();
   }
   
   // find where we left off
   // here in loadDiskState, this value is used to read the headers 
   // and then again in loadBlockData.
   // loadBlockData then updates blkDataPosition_ again
   blkDataPosition_
      = readBlockHeaders_->findFirstUnrecognizedBlockHeader(
         blockchain()
      );
   LOGINFO << "Left off at file " << blkDataPosition_.first
      << ", offset " << blkDataPosition_.second;
   
   LOGINFO << "Reading headers and building chain...";
   LOGINFO << "Starting at block file " << blkDataPosition_.first
      << " offset " << blkDataPosition_.second;
   LOGINFO << "Block height "
      << blockchain().top().getBlockHeight();
      
   // now load the new headers found in the blkfiles
   BlockFilePosition readHeadersUpTo;
   
   {
      ProgressWithPhase prog(BDMPhase_BlockHeaders, progress);
      readHeadersUpTo = loadBlockHeadersStartingAt(prog, blkDataPosition_).first;
   }
   
   try
   {
      // This will return true unless genesis block was reorg'd...
      progress(BDMPhase_OrganizingChain, 0, 0, 0);
      bool prevTopBlkStillValid = blockchain_.forceOrganize().prevTopBlockStillValid;
      if(!prevTopBlkStillValid)
      {
         LOGERR << "Organize chain indicated reorg in process all headers!";
         LOGERR << "Did we shut down last time on an orphan block?";
      }
   }
   catch (std::exception &e)
   {
      LOGERR << e.what() << ", continuing";
   }
   
   //This calls writes new headers to DB and update dupIDs in RAM.
   //For now we will only run in on headers found in the DB, in order
   //to get their dupIDs in RAM. This will allow us to undo the current
   //blocks currently scanned in the DB, in case of a reorg.
   //blockchain_.putBareHeadersByReadOrder(iface_, 0, headerCountFromDB);

   findFirstBlockToApply();

   LOGINFO << "Looking for first unrecognized block";
   uint32_t scanFrom = findFirstBlockToScan();

   //Now we can put the new headers found in blk files.
   blockchain_.putNewBareHeaders(iface_);

   /////////////////////////////////////////////////////////////////////////////
   // Now we start the meat of this process...
   
   // start reading blocks right after the last block applied, and up
   // to where we finished reading headers
   {
      TIMER_START("writeBlocksToDB");
      ProgressWithPhase prog(BDMPhase_BlockData, progress);
      loadBlockData(prog, readHeadersUpTo, true);
      TIMER_STOP("writeBlocksToDB");
      double timeElapsed = TIMER_READ_SEC("writeBlocksToDB");
      LOGINFO << "Wrote blocks to DB in " << timeElapsed << "s";
   }

   {
      //Core 0.10 specific change:
      //Let's be consistent across different blocks folders by checking if the
      //newly added range of blocks is continuous
      

      set<uint32_t> missingHeadersHeight;
      set<uint32_t> missingBlocks;

      uint32_t checkFrom = min(lastTop, scanFrom);
      if (checkFrom > 0)
         checkFrom--;

      {
         LOGINFO << "Checking dupIDs from " << checkFrom << " onward";
         uint8_t dupId;
         uint32_t currentTop = blockchain_.top().getBlockHeight();
         LMDBEnv::Transaction blktx(iface_->dbEnv_[BLKDATA].get(), LMDB::ReadOnly);
         for (uint32_t i = checkFrom; i <= currentTop; i++)
         {
            dupId = iface_->getValidDupIDForHeight(i);
            if (dupId == UINT8_MAX)
            {
               missingHeadersHeight.insert(i);
               missingBlocks.insert(i);
               continue;
            }

            auto blockKey = DBUtils::getBlkDataKey(i, dupId);
            auto blockData = iface_->getValueNoCopy(BLKDATA, blockKey);
            if (blockData.getSize() == 0)
               missingBlocks.insert(i);
         }
      }

      if (missingHeadersHeight.size() > 0)
      {
         LOGERR << "missing " << missingHeadersHeight.size() << " block headers";
         throw runtime_error("Missing headers! "
            "This is unexpected, Armory will have to close. "
            "If the error persists, do a factory reset.");
      }

      if (missingBlocks.size() > 0)
      {
         LOGERR << "Missing block data, attempting to repair the DB";
         set<BinaryData> missingBlocksByHash;
         for (auto id : missingBlocks)
         {
            auto& bh = blockchain_.getHeaderByHeight(id);
            missingBlocksByHash.insert(bh.getThisHash());
         }

         repairBlockDataDB(missingBlocksByHash);
      }
   }

   
   {
      ProgressWithPhase progPhase(BDMPhase_Rescan, progress);

      // TODO: use applyBlocksProgress in applyBlockRangeToDB
      // scan addresses from BDM
      TIMER_START("applyBlockRangeToDB");
      if (config_.armoryDbType == ARMORY_DB_SUPER)
      {
         uint32_t topBlock = blockchain_.top().getBlockHeight();

         //no point rescanning the last known block
         if (scanFrom < topBlock)
         {
            applyBlockRangeToDB(progPhase, scanFrom,
               topBlock, *scrAddrData_);
         }
      }
      else
      {
         if (scrAddrData_->numScrAddr() > 0)
         {
            uint32_t scanfrom = min(scrAddrData_->scanFrom(), scanFrom);

            if (!scanfrom)
               deleteHistories();

            applyBlockRangeToDB(progPhase, scanfrom,
               blockchain_.top().getBlockHeight(),
               *scrAddrData_.get());
         }
      }
      
      TIMER_STOP("applyBlockRangeToDB");
      double timeElapsed = TIMER_READ_SEC("applyBlockRangeToDB");
      CLEANUP_ALL_TIMERS();
      LOGINFO << "Scanned Block range in " << timeElapsed << "s";
   }

   LOGINFO << "Finished loading at file " << blkDataPosition_.first
      << ", offset " << blkDataPosition_.second;*/
      
   BlockFiles blockFiles(iface_->baseDir());
   DatabaseBuilder dbBuilder(blockFiles, *this, progress);
   dbBuilder.init();
   BDMstate_ = BDM_ready;
}


void BlockDataManager_LevelDB::loadBlockData(
   ProgressReporter &prog,
   const BlockFilePosition &stopAt,
   bool updateDupID
)
{
   ProgressFilter progfilter(
      &prog,
      readBlockHeaders_->totalBlockchainBytes()
   );

   uint64_t totalOffset=0;
   
   const auto blockCallback
      = [&] (const BinaryData &blockdata, const BlockFilePosition &pos, uint32_t blksize)
      {
         LMDBEnv::Transaction tx;
         iface_->beginDBTransaction(&tx, BLKDATA, LMDB::ReadWrite);

         BinaryRefReader brr(blockdata);
         addRawBlockToDB(brr, updateDupID);
         
         totalOffset += blksize;
         progfilter.advance(
            readBlockHeaders_->offsetAtStartOfFile(pos.first) + pos.second
         );
      };
   
   LOGINFO << "Loading block data... file "
      << blkDataPosition_.first << " offset " << blkDataPosition_.second;
   blkDataPosition_ = readBlockHeaders_->readRawBlocks(
      blkDataPosition_, stopAt, blockCallback
   );
}

uint32_t BlockDataManager_LevelDB::readBlkFileUpdate(
   const BlockDataManager_LevelDB::BlkFileUpdateCallbacks& callbacks
)
{
   // callbacks is used by gtest to update the blockchain at certain moments

   // i don't know why this is here
   scrAddrData_->checkForMerge();
   
   uint32_t prevTopBlk = blockchain_.top().getBlockHeight()+1;
   
   const BlockFilePosition headerOffset
      = blkDataPosition_;
   NullProgressReporter prog;
   
   const pair<BlockFilePosition, vector<BlockHeader*>>
      loadResult = loadBlockHeadersStartingAt(prog, headerOffset);
   
   const BlockFilePosition &readHeadersUpTo = loadResult.first;

   if (callbacks.headersRead)
      callbacks.headersRead();
      
   if (loadResult.second.empty())
      return 0;
   
   
   try
   {
      const Blockchain::ReorganizationState state = blockchain_.organize();
      const bool updateDupID = state.prevTopBlockStillValid;

      if (!state.hasNewTop)
      {
         blkDataPosition_ = readHeadersUpTo;
         return 0;
      }

      {
         LMDBEnv::Transaction tx;
         iface_->beginDBTransaction(&tx, HEADERS, LMDB::ReadWrite);

         //grab all blocks from previous to current top
         vector<BlockHeader*> newHeadersVec;
         {
            BlockHeader* newHeader = state.prevTopBlock;
            if (!state.prevTopBlockStillValid)
               newHeader = state.reorgBranchPoint;

            while (1)
            {
               BinaryData nextHash = newHeader->getNextHashRef();
               try
               {
                  newHeader = &blockchain_.getHeaderByHash(nextHash);
                  newHeadersVec.push_back(newHeader);
               }
               catch (std::range_error& e)
               {
                  //got the last block
                  break;
               }
            }
         }
      
         for (BlockHeader *bh : newHeadersVec)
         {
            StoredHeader sbh;
            sbh.createFromBlockHeader(*bh);
            uint8_t dup = iface_->putBareHeader(sbh, updateDupID);
            bh->setDuplicateID(dup);
         }

         if (callbacks.headersUpdated)
            callbacks.headersUpdated();
         
         //find lowest offset in the new blocks to add
         for (auto bh : newHeadersVec)
         {
            if (bh->getBlockFileNum() < blkDataPosition_.first ||
               (bh->getBlockFileNum() == blkDataPosition_.first &&
               bh->getOffset() < blkDataPosition_.second))
            {
               blkDataPosition_.first = bh->getBlockFileNum();
               blkDataPosition_.second = bh->getOffset();
            }
         }

         loadBlockData(prog, readHeadersUpTo, updateDupID);
         if (callbacks.blockDataLoaded)
            callbacks.blockDataLoaded();
      }
      
      if(!state.prevTopBlockStillValid)
      {
         LOGWARN << "Blockchain Reorganization detected!";
         ReorgUpdater reorg(state, &blockchain_, iface_, config_, 
            scrAddrData_.get(), false);
         
         LOGINFO << prevTopBlk - state.reorgBranchPoint->getBlockHeight() << " blocks long reorg!";
         prevTopBlk = state.reorgBranchPoint->getBlockHeight();
      }
      else if(state.hasNewTop)
      {
         const BlockHeader & bh = blockchain_.top();
         uint32_t hgt = bh.getBlockHeight();
   
         //LOGINFO << "Applying block to DB!";
         applyBlockRangeToDB(prog, prevTopBlk, hgt, *scrAddrData_.get());
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
   
   // If an orphan block is found, I won't get here and therefor
   // the orphan block will have its header read again. Then, if 
   // the header gets a height, its blkdata is also read
   blkDataPosition_ = readHeadersUpTo;
   return prevTopBlk;
}

////////////////////////////////////////////////////////////////////////////////
StoredHeader BlockDataManager_LevelDB::getBlockFromDB(uint32_t hgt, uint8_t dup) const
{

   // Get the full block from the DB
   StoredHeader returnSBH;
   if(!iface_->getStoredHeader(returnSBH, hgt, dup))
      return {};

   return returnSBH;

}

////////////////////////////////////////////////////////////////////////////////
StoredHeader BlockDataManager_LevelDB::getMainBlockFromDB(uint32_t hgt) const
{
   uint8_t dupMain = iface_->getValidDupIDForHeight(hgt);
   return getBlockFromDB(hgt, dupMain);
}

////////////////////////////////////////////////////////////////////////////////
// Deletes all SSH entries in the database
void BlockDataManager_LevelDB::deleteHistories(void)
{
   //LOGINFO << "Clearing all SSH";
   if (config_.armoryDbType != ARMORY_DB_SUPER)
   {
      wipeHistoryAndHintDB();
      return;
   }

   LMDBEnv::Transaction tx;
   iface_->beginDBTransaction(&tx, HISTORY, LMDB::ReadWrite);

   StoredDBInfo sdbi;
   iface_->getStoredDBInfo(iface_->getDbSelect(HISTORY), sdbi);

   sdbi.appliedToHgt_ = 0;
   sdbi.topScannedBlkHash_ = BinaryData(0);
   iface_->putStoredDBInfo(iface_->getDbSelect(HISTORY), sdbi);
   //////////

   bool done = false;
   uint32_t i=0;
   //can't iterate and delete at the same time with LMDB
   vector<BinaryData> keysToDelete;

   while (!done)
   {
      bool recycle = false;

      {
         LDBIter ldbIter(iface_->getIterator(iface_->getDbSelect(HISTORY)));

         try
         {
            if (!ldbIter.seekToStartsWith(DB_PREFIX_SCRIPT, BinaryData(0)))
            {
               done = true;
               break;
            }
         }
         catch (exception &e)
         {
            LOGERR << "iter recycling snafu";
            LOGERR << e.what();
            done = true;
            break;
         }

         do
         {
            if ((++i % 10000) == 0)
            {
               recycle = true;
               break;
            }

            BinaryData key = ldbIter.getKey();

            if (key.getSize() == 0)
            {
               done = true;
               break;
            }

            if (key[0] != (uint8_t)DB_PREFIX_SCRIPT)
            {
               done = true;
               break;
            }

            keysToDelete.push_back(key);
         } while (ldbIter.advanceAndRead(DB_PREFIX_SCRIPT));
      }

      for (auto& keytodel : keysToDelete)
         iface_->deleteValue(iface_->getDbSelect(HISTORY), keytodel);

      keysToDelete.clear();

      if (!recycle)
      {
         break;
      }

      tx.commit();
      tx.begin();
   }

   for (auto& keytodel : keysToDelete)
      iface_->deleteValue(iface_->getDbSelect(HISTORY), keytodel);

   if (i)
      LOGINFO << "Deleted " << i << " SSH and subSSH entries";
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::wipeHistoryAndHintDB()
{
   { 
      LMDBEnv::Transaction tx;
      iface_->beginDBTransaction(&tx, HISTORY, LMDB::ReadWrite);

      StoredDBInfo sdbi;
      iface_->getStoredDBInfo(iface_->getDbSelect(HISTORY), sdbi);

      sdbi.appliedToHgt_ = 0;
      sdbi.topScannedBlkHash_ = BinaryData(0);

      iface_->dbs_[HISTORY].drop();
      iface_->putStoredDBInfo(HISTORY, sdbi);
   }

   LMDBEnv::Transaction tx;
   iface_->beginDBTransaction(&tx, TXHINTS, LMDB::ReadWrite);
   iface_->dbs_[TXHINTS].drop();
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
   
////////////////////////////////////////////////////////////////////////////////
// We must have already added this to the header map and DB and have a dupID
void BlockDataManager_LevelDB::addRawBlockToDB(BinaryRefReader & brr,
   bool updateDupID)
{
   SCOPED_TIMER("addRawBlockToDB");

   //if(sbh.stxMap_.size() == 0)
   //{
   //LOGERR << "Cannot add raw block to DB without any transactions";
   //return false;
   //}

   BinaryDataRef first4 = brr.get_BinaryDataRef(4);

   // Skip magic bytes and block sz if exist, put ptr at beginning of header
   if (first4 == config_.magicBytes)
      brr.advance(4);
   else
      brr.rewind(4);

   // Again, we rely on the assumption that the header has already been
   // added to the headerMap and the DB, and we have its correct height 
   // and dupID
   if (config().armoryDbType == ARMORY_DB_SUPER)
   {
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
            sbh.blockHeight_ = bh.getBlockHeight();
            sbh.duplicateID_ = bh.getDuplicateID();
            sbh.isMainBranch_ = bh.isMainBranch();
            sbh.numBytes_ = bh.getBlockSize();
            sbh.blockAppliedToDB_ = false;

            // Don't put it into the DB if it's not proper!
            if (sbh.blockHeight_ == UINT32_MAX || sbh.duplicateID_ == UINT8_MAX)
               throw BlockDeserializingException(
               "Error parsing block (corrupt?) - Cannot add raw block to DB without hgt & dup (hash="
               + bh.getThisHash().copySwapEndian().toHexStr() + ")"
               );

            iface_->putStoredHeader(sbh, true);
            missingBlockHashes_.push_back(sbh.thisHash_);
            throw BlockDeserializingException("Error parsing block (corrupt?) - block header valid (hash="
               + bh.getThisHash().copySwapEndian().toHexStr() + ")"
               );
         }
         else
         {
            throw BlockDeserializingException("Error parsing block (corrupt?) and block header invalid");
         }
      }

      BlockHeader *bh;
      try
      {
          bh = &blockchain_.getHeaderByHash(sbh.thisHash_);
      }
      catch (range_error&)
      {
         LOGWARN << "Header not on main chain, skiping addRawBlockToDB"; 
         return;
      }

      sbh.blockHeight_ = bh->getBlockHeight();
      sbh.duplicateID_ = bh->getDuplicateID();
      sbh.isMainBranch_ = bh->isMainBranch();
      sbh.blockAppliedToDB_ = false;
      sbh.numBytes_ = bh->getBlockSize();

      // Don't put it into the DB if it's not proper!
      if (sbh.blockHeight_ == UINT32_MAX || sbh.duplicateID_ == UINT8_MAX)
      {
         LOGWARN << "Header not on main chain, skiping addRawBlockToDB";
         return;
      }

      //make sure this block is not already in the DB
      auto valRef = iface_->getValueNoCopy(BLKDATA, sbh.getDBKey());
      if (valRef.getSize() > 0)
      {
         LOGWARN << "Block is already in BLKDATA, skipping addRawBlockToDB";
         return;
      }

      iface_->putStoredHeader(sbh, true, updateDupID);
   }
   else
   {
      auto getBH = [this](const BinaryData& hash)->const BlockHeader&
      { return this->blockchain_.getHeaderByHash(hash); };
      
      iface_->putRawBlockData(brr, getBH);
   }
}


////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScrAddrFilter> BlockDataManager_LevelDB::getScrAddrFilter(void) const
{
   return scrAddrData_;
}


////////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::startSideScan(
   const function<void(const vector<string>&, double prog,unsigned time)> &cb
)
{
   return scrAddrData_->startSideScan(cb);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::wipeScrAddrsSSH(const vector<BinaryData>& saVec)
{
   LMDBEnv::Transaction tx;
   iface_->beginDBTransaction(&tx, HISTORY, LMDB::ReadWrite);

   vector<BinaryData> keysToDelete;

   for (const auto& scrAddr : saVec)
   {
      LDBIter ldbIter = iface_->getIterator(iface_->getDbSelect(HISTORY));

      if (!ldbIter.seekToStartsWith(DB_PREFIX_SCRIPT, scrAddr))
         continue;

      do
      {
         BinaryData key = ldbIter.getKey();

         if (key.getSliceRef(1, 21) != scrAddr)
            break;

         if (key.getSize() == 0)
            break;

         if (key[0] != (uint8_t)DB_PREFIX_SCRIPT)
            break;

         keysToDelete.push_back(key);
      } while (ldbIter.advanceAndRead(DB_PREFIX_SCRIPT));

      for (const auto& keyToDel : keysToDelete)
         iface_->deleteValue(iface_->getDbSelect(HISTORY), keyToDel);
   }
}

////////////////////////////////////////////////////////////////////////////////
vector<string> BlockDataManager_LevelDB::getNextWalletIDToScan(void)
{
   return scrAddrData_->getNextWalletIDToScan();
}

////////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataManager_LevelDB::findFirstBlockToScan(void)
{
   StoredDBInfo sdbi;
   BinaryData lastTopBlockHash;

   {
      //pull last scanned blockhash from sdbi
      LMDBEnv::Transaction tx;
      iface_->beginDBTransaction(&tx, HISTORY, LMDB::ReadOnly);
      iface_->getStoredDBInfo(iface_->getDbSelect(HISTORY), sdbi);
      lastTopBlockHash = sdbi.topScannedBlkHash_;
   }

   //check if blockchain_ has the header for this hash
   uint32_t scanFrom = 0;
   if (blockchain_.hasHeaderWithHash(lastTopBlockHash))
   {
      const BlockHeader& lastTopBlockHeader =
         blockchain_.getHeaderByHash(lastTopBlockHash);

      if (lastTopBlockHeader.isMainBranch())
      {
         //if the last known top block is on the main branch, nothing to do,
         //set scanFrom to height +1
         if (lastTopBlockHeader.getBlockHeight() > 0)
            scanFrom = lastTopBlockHeader.getBlockHeight() + 1;
      }
      else
      {
         //last known top block is not on the main branch anymore, undo SSH
         //entries up to the branch point, then scan from there
         const Blockchain::ReorganizationState state =
            blockchain_.findReorgPointFromBlock(lastTopBlockHash);

         bool undoData = true;
         if (config_.armoryDbType != ARMORY_DB_SUPER)
         {
            uint32_t topScannedBlock = scrAddrData_->scanFrom();
            if (topScannedBlock < state.reorgBranchPoint->getBlockHeight())
            {
               /***This is a special case. In full node only registered
               addresses are scanned. If we got here we hit 2 special
               conditions:

               1) The BDM was shutdown on a chain invalidated before the next
               load
               2) Fresh addresses were registered, which need to be scanned on
               their own.

               The simplest approach here is to wipe all SSH history and scan
               from scratch. The other solution is to undo the original set of
               scrAddr to the reorg point, and scan the fresh addresses
               independantly up to the reorg point, which is way too convoluted
               for such a rare case.
               ***/

               undoData = false;
               deleteHistories();

               scrAddrData_->clear();
            }
         }

         if (undoData == true)
         {
            //undo blocks up to the branch point, we'll apply the main chain
            //through the regular scan
            ReorgUpdater reorgOnlyUndo(state,
               &blockchain_, iface_, config_, scrAddrData_.get(), true);

            scanFrom = state.reorgBranchPoint->getBlockHeight() + 1;
         }
      }
   }

   return scanFrom;
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::findFirstBlockToApply(void)
{
   LMDBEnv::Transaction tx;
   iface_->beginDBTransaction(&tx, HISTORY, LMDB::ReadOnly);

   StoredDBInfo sdbi;
   iface_->getStoredDBInfo(iface_->getDbSelect(HISTORY), sdbi);
   BinaryData lastTopBlockHash = sdbi.topBlkHash_;

   if (blockchain_.hasHeaderWithHash(lastTopBlockHash))
   {
      BlockHeader* bh = &blockchain_.getHeaderByHash(lastTopBlockHash);

      if (bh->getBlockHeight() == 0)
      {
         blkDataPosition_ = { 0, 0 };
         return;
      }

      BinaryData nextHash = bh->getNextHash();

      if (nextHash == BtcUtils::EmptyHash_ || nextHash.getSize() == 0)
         return;

      if (bh->hasFilePos())
      {
         blkDataPosition_ = { bh->getBlockFileNum(), bh->getOffset() + bh->getBlockSize() };
         return;
      }

      bh = &blockchain_.getHeaderByHash(nextHash);
      
      if (!bh->hasFilePos())
         readBlockHeaders_->getFileAndPosForBlockHash(*bh);

      blkDataPosition_ = { bh->getBlockFileNum(), bh->getOffset() };
   }
   else
   {
      blkDataPosition_ = { 0, 0 };
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::repairBlockDataDB(
   set<BinaryData>& missingBlocksByHash)
{
   const auto blockCallback
      = [&](const BinaryData &blockdata, const BlockFilePosition &pos, uint32_t blksize)
   {
      BlockHeader bhUnser(blockdata);
      auto hashIter = missingBlocksByHash.find(bhUnser.getThisHash());

      if (hashIter != missingBlocksByHash.end())
      {
         LMDBEnv::Transaction tx;
         iface_->beginDBTransaction(&tx, BLKDATA, LMDB::ReadWrite);

         BinaryRefReader brr(blockdata);
         addRawBlockToDB(brr, true);

         missingBlocksByHash.erase(hashIter);

         if (missingBlocksByHash.size() == 0)
            throw FoundAllBlocksException();
      }
   };

   try
   {
      readBlockHeaders_->readRawBlocksFromTop( 
         readBlockHeaders_->numBlockFiles()-1,
         blockCallback);
   }
   catch (FoundAllBlocksException&)
   {
      //graceful throw, move on
   }

   if (missingBlocksByHash.size() > 0)
      throw runtime_error("Failed to repair BLKDATA DB, Armory will now shutdown. "
      "If the error persists, do a factory reset.");

   LOGINFO << "BLKDATA DB was repaired successfully";

}

// kate: indent-width 3; replace-tabs on;
