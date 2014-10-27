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
#include "BlockWriteBatcher.h"
#include "lmdbpp.h"
#include "Progress.h"
#include "util.h"

#ifdef _MSC_VER
#define NOEXCEPT _NOEXCEPT
#else
#define NOEXCEPT noexcept
#endif

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

   LMDBEnv::Transaction tx(&iface->dbEnv_, LMDB::ReadOnly);
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
   
   BlockHeader* oldTopPtr_;
   BlockHeader* newTopPtr_;
   BlockHeader* branchPtr_;
   ScrAddrFilter *scrAddrData_;
   bool onlyUndo_;
   
   //list<StoredTx> removedTxes_, addedTxes_;
   
   const BlockDataManagerConfig &config_;

public:
   class MissingBlockToApply : public std::exception
   {
      const uint32_t height_;
      const uint8_t dup_;
   public:
      MissingBlockToApply(uint32_t height, uint8_t dup)
         : height_(height), dup_(dup) { }
         
      virtual const char* what() const NOEXCEPT //getting noexcept to compile for MSVS
         { return "A block could not be applied because it's missing"; }
      
      uint32_t height() const
      {
         return height_;
      }
      uint8_t dup() const
      {
         return dup_;
      }

   };
   
public:
   ReorgUpdater(
      const Blockchain::ReorganizationState& state,
      Blockchain *blockchain,
      LMDBBlockDatabase* iface,
      const BlockDataManagerConfig &config,
      ScrAddrFilter *scrAddrData,
      bool onlyUndo = false
   )
      : blockchain_(blockchain)
      , iface_(iface)
      , config_(config)
   {
      oldTopPtr_    = state.prevTopBlock;
      newTopPtr_    = &blockchain_->top();
      branchPtr_    = state.reorgBranchPoint;
      if (!branchPtr_)
         branchPtr_ = oldTopPtr_;
      scrAddrData_  = scrAddrData;
      onlyUndo_     = onlyUndo;
      
      /***
      reassessThread needs a write access to the DB. Most transactions
      created in the main thead are read only, and based on user request, a
      real only transaction may be opened. Since LMDB doesn't support different
      transaction types running concurently within the same thread, this whole 
      code is ran in a new thread, while the calling thread joins on it, to 
      guarantee control over the transactions in the running thread.
      ***/
      auto reassessThread = [this]()
         { this->reassessAfterReorgThread(); };
      thread reorgthread(reassessThread);
      reorgthread.join();
      
      if (errorProcessing_)
         throw *errorProcessing_;
   }
   
   //const list<StoredTx>& removedTxes() const { return removedTxes_; }
   //const list<StoredTx>& addedTxes() const { return addedTxes_; }
      
private:
   shared_ptr<std::exception> errorProcessing_;

   void undoBlocksFromDB()
   {
      // Walk down invalidated chain first, until we get to the branch point
      // Mark transactions as invalid

      BlockWriteBatcher blockWrites(config_, iface_);

      BlockHeader* thisHeaderPtr = oldTopPtr_;
      LOGINFO << "Invalidating old-chain transactions...";

      while (thisHeaderPtr != branchPtr_)
      {
         uint32_t hgt = thisHeaderPtr->getBlockHeight();
         uint8_t  dup = thisHeaderPtr->getDuplicateID();

         //if(config_.armoryDbType != ARMORY_DB_BARE)
         {
            // Added with leveldb... in addition to reversing blocks in RAM, 
            // we also need to undo the blocks in the DB
            StoredUndoData sud;
            createUndoDataFromBlock(iface_, hgt, dup, sud);
            blockWrites.undoBlockFromDB(sud, *scrAddrData_);
         }

         try
         {
            thisHeaderPtr = &blockchain_->getHeaderByHash(thisHeaderPtr->getPrevHash());
         }
         catch (exception &e)
         {
            throw runtime_error("Exception occured while looking for branch="
               + branchPtr_->getThisHash().toHexStr() + ": " + e.what()
            );
         }
      }
   }

   void updateBlockDupIDs(void)
   {
      //create a readwrite tx to update the dupIDs
      LMDBEnv::Transaction tx(&iface_->dbEnv_, LMDB::ReadWrite);

      BlockHeader* thisHeaderPtr = branchPtr_;

      while (thisHeaderPtr->getNextHash() != BtcUtils::EmptyHash() &&
         thisHeaderPtr->getNextHash().getSize() > 0)
      {
         thisHeaderPtr = &blockchain_->getHeaderByHash(thisHeaderPtr->getNextHash());
         uint32_t hgt = thisHeaderPtr->getBlockHeight();
         uint8_t  dup = thisHeaderPtr->getDuplicateID();
         iface_->markBlockHeaderValid(hgt, dup);
      }  
   }

   void applyBlocksFromBranchPoint(void)
   {
      // Walk down the newly-valid chain and mark transactions as valid.  If 
      // a tx is in both chains, it will still be valid after this process
      // UPDATE for LevelDB upgrade:
      //       This used to start from the new top block and walk down, but 
      //       I need to apply the blocks in order, so I switched it to start
      //       from the branch point and walk up
       
      BlockWriteBatcher blockWrites(config_, iface_);

      BlockHeader* thisHeaderPtr = branchPtr_;
      
      LOGINFO << "Marking new-chain transactions valid...";
      while (thisHeaderPtr->getNextHash() != BtcUtils::EmptyHash() &&
         thisHeaderPtr->getNextHash().getSize() > 0)
      {
         thisHeaderPtr = &blockchain_->getHeaderByHash(thisHeaderPtr->getNextHash());
         uint32_t hgt = thisHeaderPtr->getBlockHeight();
         uint8_t  dup = thisHeaderPtr->getDuplicateID();

         blockWrites.applyBlockToDB(hgt, dup, *scrAddrData_);
      }
   }

   void reassessAfterReorgThread()
   {
      try
      {
         SCOPED_TIMER("reassessAfterReorg");
         LOGINFO << "Reassessing Tx validity after reorg";

         undoBlocksFromDB();

         if (onlyUndo_)
            return;
         
         updateBlockDupIDs();

         applyBlocksFromBranchPoint();

         LOGWARN << "Done reassessing tx validity";
      }
      catch (runtime_error&e)
      {
         errorProcessing_ = make_shared<runtime_error>(e);
      }
      catch (exception&e)
      {
         errorProcessing_ = make_shared<exception>(e);
      }
   }
};


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
      LOGINFO << "Total number of blk*.dat files: " << numBlkFiles;
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

   pair<size_t, uint64_t> findFileAndOffsetForBlockHgt(
      const Blockchain &bc, uint32_t hgt
   ) const
   {
      size_t blkfile=0;
      
      // find the first blockfile that we don't have its first header
      for(; blkfile < blkFiles_.size(); blkfile++)
      {
         try
         {
            const BlockHeader &bh = bc.getHeaderByHash(
               getFirstHash(blkFiles_[blkfile])
            );

            if(bh.getBlockHeight() >= hgt)
               break;
         }
         catch (...)
         {
            break;
         }
      }

      if (blkfile > 0) blkfile--;
      
      // now find the first first header in this file that we don't have
      BinaryData magic(4), szstr(4), rawHead(HEADER_SIZE), hashResult(32);
      ifstream is(blkFiles_[blkfile].path, ios::binary);
      uint64_t loc = 0;
      while(!is.eof())
      {
         is.read(magic.getCharPtr(), 4);
         if(is.eof()) break;
         if(magic!= magicBytes_)
            break;

         is.read(szstr.getCharPtr(), 4);
         uint32_t blksize = READ_UINT32_LE(szstr.getPtr());
         if(is.eof()) break;

         is.read(rawHead.getCharPtr(), HEADER_SIZE); 
         BtcUtils::getHash256_NoSafetyCheck(rawHead.getPtr(), 
                                          HEADER_SIZE, 
                                          hashResult);

         try
         {
            const BlockHeader &bh = bc.getHeaderByHash(hashResult);
            
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

      return { blkfile, loc };
   }
   
   std::pair<size_t, uint64_t> readHeaders(
      size_t startBlkFile, uint64_t startBlockFileOffset,
      const function<void(
         const BinaryData &,
         size_t fnum,
         uint64_t offset,
         uint32_t blksize
      )> &blockDataCallback
   ) const
   {
      if (startBlkFile == blkFiles_.size())
         return { startBlkFile, startBlockFileOffset };
      if (startBlkFile > blkFiles_.size())
         throw std::runtime_error("blkFile out of range");
         
      uint64_t finishLocation=startBlockFileOffset;

      while (startBlkFile < blkFiles_.size())
      {
         const BlkFile &f = blkFiles_[startBlkFile];
         finishLocation = readHeadersFromFile(f, startBlockFileOffset, blockDataCallback);
         startBlockFileOffset = 0;
         startBlkFile++;
      }
      
      LOGINFO << "Total blockchain bytes: " 
         << BtcUtils::numToStrWCommas(totalBlockchainBytes_);
      return { startBlkFile-1, finishLocation };
   }
   
   std::pair<size_t, uint64_t> readRawBlocks(
      size_t startBlkFile, uint64_t startBlockFileOffset,
      const function<void(
         const BinaryData &,
         size_t fnum,
         uint64_t offset,
         uint32_t blksize
      )> &blockDataCallback
   )
   {
      if (startBlkFile == blkFiles_.size())
         return { startBlkFile, startBlockFileOffset };
      if (startBlkFile > blkFiles_.size())
         throw std::runtime_error("blkFile out of range");

      uint64_t finishLocation=startBlockFileOffset;
      while (startBlkFile < blkFiles_.size())
      {
         const BlkFile &f = blkFiles_[startBlkFile];
         finishLocation = readRawBlocksFromFile(f, startBlockFileOffset, blockDataCallback);
         startBlockFileOffset = 0;
         startBlkFile++;
      }
      
      return { startBlkFile-1, finishLocation };
   }
   
private:
   // read blocks from f, starting at offset blockFileOffset,
   // returning the offset we finished at
   uint64_t readRawBlocksFromFile(
      const BlkFile &f, uint64_t blockFileOffset,
      const function<void(
         const BinaryData &,
         size_t fnum,
         uint64_t offset,
         uint32_t blksize
      )> &blockDataCallback
   )
   {
      ifstream is(f.path, ios::binary);
      BinaryData fileMagic(4);
      is.read(reinterpret_cast<char*>(fileMagic.getPtr()), 4);
      if( fileMagic != magicBytes_ )
      {
         LOGERR << "Block file is the wrong network! File: "
            << fileMagic.toHexStr()
            << ", expecting " << magicBytes_.toHexStr();
      }
      // Seek to the supplied offset
      is.seekg(blockFileOffset, ios::beg);
      
      {
         BinaryData magic(4), szstr(4), rawBlk;
         // read the file, we can't go past what we think is the end,
         // because we haven't gone past that in Headers
         while(!is.eof() && uint64_t(is.tellg()) < f.filesize)
         {
            is.read((char*)magic.getPtr(), 4);
            if (is.eof())
               break;
               
            if(magic != magicBytes_)
            {
               // I have to start scanning for MagicBytes
               if (!scanFor(is, magicBytes_.getPtr(), magicBytes_.getSize()))
               {
                  LOGERR << "No more blocks found in file " << f.path;
                  break;
               }
               
               LOGERR << "Next block header found at offset " << uint64_t(is.tellg())-4;
            }
            
            is.read(reinterpret_cast<char*>(szstr.getPtr()), 4);
            uint32_t blkSize = READ_UINT32_LE(szstr.getPtr());
            if(is.eof()) break;

            rawBlk.resize(blkSize);
            is.read(reinterpret_cast<char*>(rawBlk.getPtr()), blkSize);
            
            try
            {
               blockDataCallback(rawBlk, f.fnum, blockFileOffset, blkSize);
            }
            catch (std::exception &e)
            {
               // this might very well just mean that we tried to load
               // blkdata past where we loaded headers. This isn't a problem
               LOGERR << e.what() << " (error encountered processing block at byte "
                  << blockFileOffset << " file "
                  << f.path << ", blocksize " << blkSize << ")";
            }
            blockFileOffset += blkSize+8;
         }
      }
      
      LOGINFO << "Reading raw blocks finished at file "
         << f.fnum << " offset " << blockFileOffset;
      
      return blockFileOffset;
   }
   
   uint64_t readHeadersFromFile(
      const BlkFile &f,
      uint64_t blockFileOffset,
      const function<void(
         const BinaryData &,
         size_t fnum,
         uint64_t offset,
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
            ss << "Block file is the wrong network! File: "
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
                  LOGERR << "No more blocks found in file " << f.path;
                  break;
               }
               
               LOGERR << "Next block header found at offset " << uint64_t(is.tellg())-4;
            }
            
            is.read(reinterpret_cast<char*>(szstr.getPtr()), 4);
            uint32_t nextBlkSize = READ_UINT32_LE(szstr.getPtr());
            if(is.eof()) break;

            is.read(reinterpret_cast<char*>(rawHead.getPtr()), HEAD_AND_NTX_SZ); // plus #tx var_int
            blockDataCallback(rawHead, f.fnum, blockFileOffset, nextBlkSize);
            
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
      
protected:
   virtual int32_t bdmIsRunning() const
   {
      return bdm_->isRunning_;
   }
   
   virtual void applyBlockRangeToDB(
      uint32_t startBlock, uint32_t endBlock, BtcWallet *wltPtr
   )
   {
      class WalletIdProgressReporter : public ProgressReporter
      {
         BtcWallet *const wltPtr;
         const function<void(const BinaryData&, double prog,unsigned time)> &cb;
      public:
         WalletIdProgressReporter(
            BtcWallet *wltPtr,
            const function<void(const BinaryData&, double prog,unsigned time)> &cb
         )
            : wltPtr(wltPtr), cb(cb) {}
         
         virtual void progress(
            double progress, unsigned secondsRemaining
         )
         {
            const BinaryData empty;
            const BinaryData &wltId = wltPtr ? wltPtr->walletID() : empty;
            cb(wltId, progress, secondsRemaining);
         }
      };
   
      WalletIdProgressReporter progress(wltPtr, scanThreadProgressCallback_);
      
      //pass to false to skip SDBI top block updates
      bdm_->applyBlockRangeToDB(progress, startBlock, endBlock, *this, false);
   }
   
   virtual uint32_t currentTopBlockHeight() const
   {
      return bdm_->blockchain().top().getBlockHeight();
   }
   
   virtual BDM_ScrAddrFilter* copy()
   {
      return new BDM_ScrAddrFilter(bdm_);
   }

   virtual void flagForScanThread(void)
   {
      bdm_->sideScanFlag_ = true;
   }

   virtual void wipeScrAddrsSSH(const vector<BinaryData>& saVec)
   {
      bdm_->wipeScrAddrsSSH(saVec);
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
{
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
   LOGINFO << "Set home directory: " << config_.homeDirLocation;
   LOGINFO << "Set blkfile dir: " << config_.blkFileLocation;
   LOGINFO << "Set leveldb dir: " << config_.levelDBLocation;
   if (config_.genesisBlockHash.getSize() == 0)
   {
      throw runtime_error("ERROR: Genesis Block Hash not set!");
   }

   iface_->openDatabases(
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
   iface_->closeDatabases();
   scrAddrData_.reset();
   delete iface_;
}

pair<pair<size_t, uint64_t>, vector<BlockHeader*>>
   BlockDataManager_LevelDB::loadBlockHeadersStartingAt(
      ProgressReporter &prog,
      const pair<size_t, uint64_t> &fileAndOffset
   )
{
   readBlockHeaders_->detectAllBlkFiles();
   
   vector<BlockHeader*> blockHeadersAdded;
   
   ProgressFilter progfilter(
      &prog,
      readBlockHeaders_->totalBlockchainBytes()
   );
   uint64_t totalOffset=0;
   
   auto blockHeaderCallback
      = [&] (const BinaryData &blockdata, size_t fnum, uint64_t offset, uint32_t blksize)
      {
         BlockHeader block;
         BinaryRefReader brr(blockdata);
         block.unserialize(brr);
         
         const HashString blockhash = block.getThisHash();
         
         const uint32_t nTx = brr.get_var_int();
         BlockHeader& addedBlock = blockchain().addBlock(blockhash, block);

         blockHeadersAdded.push_back(&addedBlock);
         //LOGINFO << "Added block header with hash " << addedBlock.getThisHash().copySwapEndian().toHexStr()
         //   << " from " << fnum << " offset " << offset;
         
         // is there any reason I can't just do this to "block"?
         addedBlock.setBlockFileNum(fnum);
         addedBlock.setBlockFileOffset(offset);
         addedBlock.setNumTx(nTx);
         addedBlock.setBlockSize(blksize);
         
         totalOffset += blksize+8;
         progfilter.advance(totalOffset);
      };
   
   LOGINFO << "Reading headers and building chain...";
   LOGINFO << "Starting at block file " << fileAndOffset.first
      << " offset " << fileAndOffset.second;
   LOGINFO << "Block height "
      << blockchain().top().getBlockHeight();
      
   const pair<size_t, uint64_t> position = readBlockHeaders_->readHeaders(
      fileAndOffset.first, fileAndOffset.second,
      blockHeaderCallback
   );
   
   if (totalOffset >0)
   {
      LOGINFO << "Read " << totalOffset << " bytes";
   }
   
   return { position, blockHeadersAdded };
}

uint64_t BlockDataManager_LevelDB::getTotalBlockchainBytes() const
{
   return readBlockHeaders_->totalBlockchainBytes();
}

uint32_t BlockDataManager_LevelDB::getTotalBlkFiles()        const
{
   return readBlockHeaders_->numBlockFiles();
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
bool BlockDataManager_LevelDB::hasTxWithHashInDB(BinaryData const & txHash)
{
   return iface_->getTxRef(txHash).isInitialized();
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataManager_LevelDB::hasTxWithHash(BinaryData const & txHash)
{
   LMDBEnv::Transaction tx(&iface_->dbEnv_, LMDB::ReadOnly);
   TxRef txref = iface_->getTxRef(txHash);
   if (txref.isInitialized())
      return true;

   return false;
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
   if (config_.armoryDbType == ARMORY_DB_SUPER)
      return false;

   return false;
}

/////////////////////////////////////////////////////////////////////////////
// This used to be "rescanBlocks", but now "scanning" has been replaced by
// "reapplying" the blockdata to the databases.  Basically assumes that only
// raw blockdata is stored in the DB with no SSH objects.  This goes through
// and processes every Tx, creating new SSHs if not there, and creating and
// marking-spent new TxOuts.  
void BlockDataManager_LevelDB::applyBlockRangeToDB(ProgressReporter &prog, 
   uint32_t blk0, uint32_t blk1, 
   ScrAddrFilter& scrAddrData,
   bool updateSDBI)
{
   ProgressFilter progress(&prog, readBlockHeaders_->totalBlockchainBytes());
   
   // Start scanning and timer
   BlockWriteBatcher blockWrites(config_, iface_);
   blockWrites.setUpdateSDBI(updateSDBI);

   LOGWARN << "Scanning from " << blk0 << " to " << blk1;
   blockWrites.scanBlocks(progress, blk0, blk1, scrAddrData);
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


static size_t scanFor(const uint8_t *in, const size_t inLen, 
                      const uint8_t * bytes, const size_t len)
{
   unsigned offset = 0; // the index mod len which we're in ahead

   do
   {
      bool found = true;
      for (unsigned i = 0; i < len; i++)
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
   return MAXSIZE_T;
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
   const function<void(unsigned, double,unsigned)> &progress
)
{
   LOGINFO << "Executing: doInitialSyncOnLoad";
   loadDiskState(progress);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doInitialSyncOnLoad_Rescan(
   const function<void(unsigned, double,unsigned)> &progress
)
{
   LOGINFO << "Executing: doInitialSyncOnLoad_Rescan";
   loadDiskState(progress, true);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::doInitialSyncOnLoad_Rebuild(
   const function<void(unsigned, double,unsigned)> &progress
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
   const function<void(unsigned, double,unsigned)> &progress
)
{
   LOGINFO << "Executing: doRebuildDatabases";
   destroyAndResetDatabases();
   deleteHistories();
   scrAddrData_->clear();
   loadDiskState(progress);
}


void BlockDataManager_LevelDB::loadDiskState(
   const function<void(unsigned, double,unsigned)> &progress,
   bool forceRescan
)
{
   class ProgressWithPhase : public ProgressReporter
   {
      const unsigned phase_;
      const function<void(unsigned, double,unsigned)> progress_;
   public:
      ProgressWithPhase(
         unsigned phase,
         const function<void(unsigned, double,unsigned)>& progress
      ) : phase_(phase), progress_(progress)
      {
         this->progress(0.0, 0);
      }
      
      virtual void progress(
         double progress, unsigned secondsRemaining
      )
      {
         progress_(phase_, progress, secondsRemaining);
      }
   };
   
   //quick hack to signal scrAddrData_ that the BDM is loading/loaded.
   isRunning_ = 1;
   
   readBlockHeaders_->detectAllBlkFiles();
   if (readBlockHeaders_->numBlockFiles()==0)
   {
      throw runtime_error("No blockfiles could be found!");
   }
   
   //pull last scanned blockhash from sdbi
   StoredDBInfo sdbi;
   iface_->getStoredDBInfo(BLKDATA, sdbi);
   const BinaryData lastTopBlockHash = sdbi.topBlkHash_;
   
   // load the headers from lmdb into blockchain()
   loadBlockHeadersFromDB();
   
   uint32_t firstUnappliedHeight=0;
   
   try
   {
      // organize the blockchain we have so far
      const Blockchain::ReorganizationState state
         = blockchain().forceOrganize();
      if(!state.prevTopBlockStillValid)
      {
         LOGERR << "Organize chain indicated reorg in process all headers!";
         LOGERR << "Did we shut down last time on an orphan block?";
      }
      firstUnappliedHeight = blockchain_.top().getBlockHeight();
   }
   catch (Blockchain::BlockCorruptionError &)
   {
      // If the headers DB ended up corrupted (triggered by forceOrganize),
      // then nuke and rebuild the headers
      LOGERR << "Corrupted headers DB. Need to reload blocks";
      blockchain_.clear();
   }
   
   
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
   {
      StoredDBInfo sdbiB;
      iface_->getStoredDBInfo(BLKDATA, sdbiB);
      uint32_t hgt = sdbiB.topBlkHgt_ == 0 ? 0 : (sdbiB.topBlkHgt_+1);
      
      blkDataPosition_
         = readBlockHeaders_->findFileAndOffsetForBlockHgt(
            blockchain(), hgt
         );
      
   }

   
   // now load the new headers found in the blkfiles
   {
      const pair<size_t, uint64_t> headerOffset
         = readBlockHeaders_->findFileAndOffsetForBlockHgt(
            blockchain(), blockchain().top().getBlockHeight()
         );
      
      ProgressWithPhase prog(1, progress);
      loadBlockHeadersStartingAt(prog, headerOffset);
   }
   
   try
   {
      // This will return true unless genesis block was reorg'd...
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

   //write headers to the DB, update dupIDs in RAM
   blockchain_.putBareHeaders(iface_);
   
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
            
         //undo blocks up to the branch point, we'll apply the main chain
         //through the regular scan
         ReorgUpdater reorgOnlyUndo(state,
            &blockchain_, iface_, config_, scrAddrData_.get(), true);
         
         scanFrom = state.reorgBranchPoint->getBlockHeight() + 1;
      }
   }
   
   firstUnappliedHeight = min(scanFrom, firstUnappliedHeight);
   
   /////////////////////////////////////////////////////////////////////////////
   // Now we start the meat of this process...
   
   // start reading blocks right after the last block applied
   {

      ProgressWithPhase prog(2, progress);
      loadBlockData(prog, false);
   }
   
   {
      ProgressWithPhase progPhase(3, progress);
      if (!blockchain_.hasHeaderWithHash(sdbi.topScannedBlkHash_))
         scanFrom = 0;
      else
      {
         const BlockHeader& bh = blockchain_.getHeaderByHash(sdbi.topScannedBlkHash_);
         scanFrom = min(scanFrom, bh.getBlockHeight());
      }
      // TODO: use applyBlocksProgress in applyBlockRangeToDB
      // scan addresses from BDM
      TIMER_START("applyBlockRangeToDB");
      if (config_.armoryDbType == ARMORY_DB_SUPER)
      {
         applyBlockRangeToDB(progPhase, scanFrom,
         blockchain_.top().getBlockHeight(), *scrAddrData_.get());
      }
      else
      {
         if (scrAddrData_->numScrAddr() > 0)
         {
            uint32_t scanfrom = min(scrAddrData_->scanFrom(), scanFrom);
            applyBlockRangeToDB(progPhase, scanfrom,
               blockchain_.top().getBlockHeight(),
               *scrAddrData_.get());
         }
      }
      TIMER_STOP("applyBlockRangeToDB");
      double timeElapsed = TIMER_READ_SEC("applyBlockRangeToDB");
      CLEANUP_ALL_TIMERS();
      LOGINFO << "Applied Block range to DB in " << timeElapsed << "s";
   }   
   currentHeaderPosition_ = readBlockHeaders_->findFileAndOffsetForBlockHgt(
         blockchain(),
         blockchain().top().getBlockHeight()
      );
   
   isRunning_ = 2;
}


void BlockDataManager_LevelDB::loadBlockData(
   ProgressReporter &prog,
   bool updateDupID
)
{
   ProgressFilter progfilter(
      &prog,
      readBlockHeaders_->totalBlockchainBytes()
   );

   uint64_t totalOffset=0;
   
   const auto blockCallback
      = [&] (const BinaryData &blockdata, size_t fnum, uint64_t foff, uint32_t blksize)
      {
         LMDBEnv::Transaction tx(&iface_->dbEnv_);

         BinaryRefReader brr(blockdata);
         addRawBlockToDB(brr, updateDupID);
         
         totalOffset += blksize;
         progfilter.advance(
            readBlockHeaders_->offsetAtStartOfFile(fnum) + foff
         );
      };
   
   LOGINFO << "Loading block data... file "
      << blkDataPosition_.first << " offset " << blkDataPosition_.second;
   blkDataPosition_ = readBlockHeaders_->readRawBlocks(
      blkDataPosition_.first, blkDataPosition_.second,
      blockCallback
   );
}

uint32_t BlockDataManager_LevelDB::readBlkFileUpdate()
{
   
   // i don't know why this is here
   scrAddrData_->checkForMerge();
   
   uint32_t prevTopBlk = blockchain_.top().getBlockHeight()+1;
   
   const pair<size_t, uint64_t> headerOffset
      = currentHeaderPosition_;
   NullProgressReporter prog;
   
   const pair<pair<size_t, uint64_t>, vector<BlockHeader*>>
      loadResult = loadBlockHeadersStartingAt(prog, headerOffset);
   
   const vector<BlockHeader*> &loadedBlockHeaders = loadResult.second;
   const pair<size_t, uint64_t> &position = loadResult.first;
   if (loadedBlockHeaders.empty())
      return 0;
   
   
   try
   {
      
      const Blockchain::ReorganizationState state = blockchain_.organize();
      
      const bool updateDupID = state.prevTopBlockStillValid;
      
      {
         LMDBEnv::Transaction tx(&iface_->dbEnv_, LMDB::ReadWrite);
      
         for (BlockHeader *bh : loadedBlockHeaders)
         {
            StoredHeader sbh;
            sbh.createFromBlockHeader(*bh);
            uint8_t dup = iface_->putBareHeader(sbh, updateDupID);
            bh->setDuplicateID(dup);
         }
         
         loadBlockData(prog, updateDupID);
      }
      
      if(!state.prevTopBlockStillValid)
      {
         LOGWARN << "Blockchain Reorganization detected!";
         ReorgUpdater reorg(state, &blockchain_, iface_, config_, 
            scrAddrData_.get(), false);
         
         LOGINFO << prevTopBlk - state.reorgBranchPoint->getBlockHeight() << " blocks long reorg!";
         prevTopBlk = state.reorgBranchPoint->getBlockHeight();
         
         //const BlockHeader & bh = blockchain_.top();
         //uint32_t hgt = bh.getBlockHeight();
         //applyBlockRangeToDB(prog, prevTopBlk, hgt, *scrAddrData_.get());
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
   
   currentHeaderPosition_ = position;
   return prevTopBlk;
}

void BlockDataManager_LevelDB::loadBlockHeadersFromDB()
{
   LOGINFO << "Reading headers from db";
   blockchain().clear();
   {
      unordered_map<HashString, BlockHeader, BinaryDataHash> headers;
      iface_->readAllHeaders(headers);
      for (auto& i : headers)
      {
         blockchain().addBlock(i.first, i.second);
      }
   }
   
   LOGINFO << "Found " << blockchain().allHeaders().size() << " headers in db";
   
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
   LOGINFO << "Clearing all SSH";

   LMDBEnv::Transaction tx(&iface_->dbEnv_, LMDB::ReadWrite);

   StoredDBInfo sdbi;
   iface_->getStoredDBInfo(BLKDATA, sdbi);

   sdbi.appliedToHgt_ = 0;
   sdbi.topBlkHash_ = config_.genesisBlockHash;
   sdbi.topScannedBlkHash_ = BinaryData(0);
   iface_->putStoredDBInfo(BLKDATA, sdbi);
   //////////

   bool done = false;
   uint32_t i=0;
   //can't iterate and delete at the same time with LMDB
   vector<BinaryData> keysToDelete;

   while (!done)
   {
      std::shared_ptr<LDBIter> ldbIter; 

      try
      {
         ldbIter = make_shared<LDBIter>(iface_->getIterator(BLKDATA));

         if (!ldbIter->seekToStartsWith(DB_PREFIX_SCRIPT, BinaryData(0)))
         {
            done = true;
            break;
         }
      }
      catch (runtime_error &e)
      {
         LOGERR << "iter recycling snafu";
         LOGERR << e.what();
         done = true;
         break;
      }
      catch (...)
      {
         LOGERR << "iter recycling snafu";
         LOGERR << "unknown exception";
         done = true;
         break;
      }

      bool recycle = false;
      do
      {
         if ((++i % 10000) == 0)
         {
            recycle = true;
            break;
         }

         BinaryData key = ldbIter->getKey();

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
      } while (ldbIter->advanceAndRead(DB_PREFIX_SCRIPT));

      for (auto& keytodel : keysToDelete)
         iface_->deleteValue(BLKDATA, keytodel);

      keysToDelete.clear();

      if (!recycle)
      {
         break;
      }

      tx.commit();
      tx.begin();
   }

   for (auto& keytodel : keysToDelete)
      iface_->deleteValue(BLKDATA, keytodel);

   LOGINFO << "Deleted " << i << " SSH and subSSH entries";
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
   iface_->putStoredHeader(sbh, true, updateDupID);
}

////////////////////////////////////////////////////////////////////////////////
ScrAddrFilter* BlockDataManager_LevelDB::getScrAddrFilter(void) const
{
   return scrAddrData_.get();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::startSideScan(
   function<void(const BinaryData&, double prog, unsigned time)> progress)
{
   scrAddrData_->startSideScan(progress);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataManager_LevelDB::wipeScrAddrsSSH(const vector<BinaryData>& saVec)
{
   LMDBEnv::Transaction tx(&iface_->dbEnv_, LMDB::ReadWrite);

   vector<BinaryData> keysToDelete;

   for (const auto& scrAddr : saVec)
   {
      LDBIter ldbIter = iface_->getIterator(BLKDATA);

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
         iface_->deleteValue(BLKDATA, keyToDel);
   }
}

// kate: indent-width 3; replace-tabs on;
