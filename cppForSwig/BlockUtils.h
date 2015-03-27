////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _BLOCKUTILS_H_
#define _BLOCKUTILS_H_

#include <iostream>
#include <fstream>
#include <vector>
#include <set>

#include "Blockchain.h"
#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockObj.h"
#include "StoredBlockObj.h"
#include "BlockDataManagerConfig.h"
#include "lmdb_wrapper.h"
#include "ScrAddrObj.h"
#include "bdmenums.h"

#include "cryptlib.h"
#include "sha.h"
#include "UniversalTimer.h"

#include <functional>
#include "BDM_supportClasses.h"

#ifndef MAXSIZE_T
   #if defined(_WIN64) || defined(__X86_64__)
      #define MAXSIZE_T UINT64_MAX
   #else
      #define MAXSIZE_T UINT32_MAX
   #endif
#endif

#ifdef _MSC_VER
   #include "mman.h"
   #include "leveldb_windows_port\win32_posix\win32_posix.h"
   #else
   #include <fcntl.h>
   #include <sys/mman.h>
#endif


#define NUM_BLKS_BATCH_THRESH 30

#define NUM_BLKS_IS_DIRTY 2016


using namespace std;

class BlockDataManager_LevelDB;
class LSM;
//class BDM_Inject;

typedef enum
{
  TX_DNE,
  TX_ZEROCONF,
  TX_IN_BLOCKCHAIN
} TX_AVAILABILITY;


typedef enum
{
  DB_BUILD_HEADERS,
  DB_BUILD_ADD_RAW,
  DB_BUILD_APPLY,
  DB_BUILD_SCAN
} DB_BUILD_PHASE;

typedef enum 
{
   BDM_offline,
   BDM_initializing,
   BDM_ready
}BDM_state;

class ProgressReporter;

typedef std::pair<size_t, uint64_t> BlockFilePosition;

////////////////////////////////////////////////////////////////////////////////
class FileMap
{
   friend class BlockFileAccessor;

private:
   atomic<uint64_t> lastSeenCumulated_;

public:
   uint8_t* filemap_ = nullptr;
   uint64_t mapsize_ = 0;
   uint16_t fnum_;

   FileMap(BlkFile& blk);
   //FileMap(FileMap&& fm);

   ~FileMap(void);


   void getRawBlock(BinaryDataRef& bdr, uint64_t offset, uint32_t size,
      atomic<uint64_t>& lastSeenCumulative);
private:
   FileMap(const FileMap&); // not defined
};

class BlockFileAccessor
{
private:
   shared_ptr<vector<BlkFile> > blkFiles_;
   map<uint16_t, shared_ptr<FileMap> > blkMaps_;
   atomic<uint64_t> lastSeenCumulative_;

   static const uint64_t threshold_ = 50 * 1024 * 1024LL;
   uint64_t nextThreshold_ = threshold_;

   mutex mu_;

public:
   ///////
   BlockFileAccessor(shared_ptr<vector<BlkFile> > blkfiles);

   void getRawBlock(BinaryDataRef& bdr, uint32_t fnum, uint64_t offset,
      uint32_t size, shared_ptr<FileMap>** fmPtr);

   shared_ptr<FileMap>& getFileMap(uint32_t fnum);
   void dropFileMap(uint32_t fnum);
};

////////////////////////////////////////////////////////////////////////////////
class BlockDataManager_LevelDB
{
   void grablock(uint32_t n);


private:
   BlockDataManagerConfig config_;
   
   class BitcoinQtBlockFiles;
   shared_ptr<BitcoinQtBlockFiles> readBlockHeaders_;
   
   // This is our permanent link to the two databases used
   LMDBBlockDatabase* iface_;
   
   BlockFilePosition blkDataPosition_ = {0, 0};
   
   // Reorganization details

   class BDM_ScrAddrFilter;
   shared_ptr<BDM_ScrAddrFilter>    scrAddrData_;

  
   // If the BDM is not in super-node mode, then it will be specifically tracking
   // a set of addresses & wallets.  We register those addresses and wallets so
   // that we know what TxOuts to track as we process blockchain data.  And when
   // it may be necessary to do rescans.
   //
   // If instead we ARE in ARMORY_DB_SUPER (not implemented yet, as of this
   // comment being written), then we don't have anything to track -- the DB
   // will automatically update for all addresses, period.  And we'd best not 
   // track those in RAM (maybe on a huge server...?)

   // list of block headers that appear to be missing 
   // when scanned by buildAndScanDatabases
   vector<BinaryData>                 missingBlockHeaderHashes_;
   // list of blocks whose contents are invalid but we have
   // their headers
   vector<BinaryData>                 missingBlockHashes_;
   
   // TODO: We eventually want to maintain some kind of master TxIO map, instead
   // of storing them in the individual wallets.  With the new DB, it makes more
   // sense to do this, and it will become easier to compute total balance when
   // multiple wallets share the same addresses
   //map<OutPoint,   TxIOPair>          txioMap_;

   Blockchain blockchain_;

   BDM_state BDMstate_ = BDM_offline;


public:
   bool                               sideScanFlag_ = false;
   typedef function<void(BDMPhase, double,unsigned, unsigned)> ProgressCallback;
   
   class Notifier
   {
   public:
      virtual ~Notifier() { }
      virtual void notify()=0;
   };
   
   string criticalError_;

private:
   Notifier* notifier_ = nullptr;

public:
   BlockDataManager_LevelDB(const BlockDataManagerConfig &config);
   ~BlockDataManager_LevelDB();

public:

   Blockchain& blockchain() { return blockchain_; }
   const Blockchain& blockchain() const { return blockchain_; }
   
   const BlockDataManagerConfig &config() const { return config_; }
   void setConfig(const BlockDataManagerConfig &bdmConfig);
   
   LMDBBlockDatabase *getIFace(void) {return iface_;}
   void setNotifier(Notifier* notifier) { notifier_ = notifier; }
   void notifyMainThread() const
   { 
      if (notifier_)
         notifier_->notify(); 
   }
   
   bool hasNotifier() const { return notifier_ != nullptr; }

   
   
   /////////////////////////////////////////////////////////////////////////////
   // Get the parameters of the network as they've been set
   const BinaryData& getGenesisHash(void) const  { return config_.genesisBlockHash;   }
   const BinaryData& getGenesisTxHash(void) const { return config_.genesisTxHash; }
   const BinaryData& getMagicBytes(void) const   { return config_.magicBytes;    }

public:
   void openDatabase(void);
   void     destroyAndResetDatabases(void);
   
   void doRebuildDatabases(const ProgressCallback &progress);
   void doInitialSyncOnLoad(const ProgressCallback &progress);
   void doInitialSyncOnLoad_Rescan(const ProgressCallback &progress);
   void doInitialSyncOnLoad_Rebuild(const ProgressCallback &progress);
   
   // for testing only
   struct BlkFileUpdateCallbacks
   {
      std::function<void()> headersRead, headersUpdated, blockDataLoaded;
   };
   
   uint32_t readBlkFileUpdate(const BlkFileUpdateCallbacks &callbacks=BlkFileUpdateCallbacks());
   
private:
   void loadDiskState(
      const ProgressCallback &progress,
      bool doRescan=false
   );
   void loadBlockData(
      ProgressReporter &prog,
      const BlockFilePosition &stopAt,
      bool updateDupID
   );
   void loadBlockHeadersFromDB(const ProgressCallback &progress);
   pair<BlockFilePosition, vector<BlockHeader*> >
      loadBlockHeadersStartingAt(
         ProgressReporter &prog,
         const BlockFilePosition &fileAndOffset
      );
   
   void deleteHistories(void);

   void addRawBlockToDB(BinaryRefReader & brr, 
      uint16_t fnum, uint64_t offset, bool updateDupID = true);
   uint32_t findFirstBlockToScan(void);
   void findFirstBlockToApply(void);

public:

   BinaryData applyBlockRangeToDB(ProgressReporter &prog, 
                            uint32_t blk0, uint32_t blk1,
                            ScrAddrFilter& scrAddrData,
                            bool updateSDBI = true);

   uint32_t getTopBlockHeight() const {return blockchain_.top().getBlockHeight();}
      
   uint8_t getValidDupIDForHeight(uint32_t blockHgt) const
   { return iface_->getValidDupIDForHeight(blockHgt); }

   ScrAddrFilter* getScrAddrFilter(void) const;


   StoredHeader getMainBlockFromDB(uint32_t hgt) const;
   StoredHeader getBlockFromDB(uint32_t hgt, uint8_t dup) const;

public:

// These things should probably be private, but they also need to be test-able,
// and googletest apparently cannot access private methods without polluting 
// this class with gtest code
//private: 

   //void pprintSSHInfoAboutHash160(BinaryData const & a160);

   // Simple wrapper around the logger so that they are easy to access from SWIG

   /////////////////////////////////////////////////////////////////////////////
   // We may use this to trigger flushing the queued DB updates
   //bool estimateDBUpdateSize(
                        //map<BinaryData, StoredTx> &            stxToModify,
                        //map<BinaryData, StoredScriptHistory> & sshToModify);

   vector<BinaryData> missingBlockHeaderHashes() const { return missingBlockHeaderHashes_; }
   
   vector<BinaryData> missingBlockHashes() const { return missingBlockHashes_; }

   bool startSideScan(
      const function<void(const vector<string>&, double prog,unsigned time)> &cb
   );

   void wipeScrAddrsSSH(const vector<BinaryData>& saVec);

   bool isRunning(void) const { return BDMstate_ != BDM_offline; }
   bool isReady(void) const   { return BDMstate_ == BDM_ready; }

   vector<string> getNextWalletIDToScan(void);
};


// kate: indent-width 3; replace-tabs on;

#endif
