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

#ifndef _BLOCKUTILS_H_
#define _BLOCKUTILS_H_

#include <iostream>
#include <fstream>
#include <vector>
#include <set>
#include <future>

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
   //#include "leveldb_windows_port\win32_posix\win32_posix.h"
   #else
   #include <fcntl.h>
   #include <sys/mman.h>
#endif


#define NUM_BLKS_BATCH_THRESH 30

#define NUM_BLKS_IS_DIRTY 2016


using namespace std;

class BlockDataManager;
class LSM;

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
class FoundAllBlocksException {};

class debug_replay_blocks {};

class BlockFiles;
class DatabaseBuilder;
class BDV_Server_Object;

////////////////////////////////////////////////////////////////////////////////
class BlockDataManager
{
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
   bool     zcEnabled_;

   Blockchain blockchain_;

   BDM_state BDMstate_ = BDM_offline;

   shared_ptr<BlockFiles> blockFiles_;
   shared_ptr<DatabaseBuilder> dbBuilder_;


public:
   typedef function<void(BDMPhase, double,unsigned, unsigned)> ProgressCallback;   
   shared_ptr<BitcoinP2P> networkNode_;
   shared_future<bool> isReadyFuture_;

   BlockingStack<Blockchain::ReorganizationState> newBlocksStack_;
   shared_ptr<ZeroConfContainer>   zeroConfCont_;

public:
   BlockDataManager(const BlockDataManagerConfig &config);
   ~BlockDataManager();

   Blockchain& blockchain() { return blockchain_; }
   const Blockchain& blockchain() const { return blockchain_; }
   
   const BlockDataManagerConfig &config() const { return config_; }
   void setConfig(const BlockDataManagerConfig &bdmConfig);
   
   LMDBBlockDatabase *getIFace(void) {return iface_;}
   
   shared_future<bool> registerAddressBatch(
      const set<BinaryData>& addrSet, bool isNew);
   
   /////////////////////////////////////////////////////////////////////////////
   // Get the parameters of the network as they've been set
   const BinaryData& getGenesisHash(void) const  
   { return config_.genesisBlockHash;   }
   const BinaryData& getGenesisTxHash(void) const 
   { return config_.genesisTxHash; }
   const BinaryData& getMagicBytes(void) const   
   { return config_.magicBytes;    }

   void openDatabase(void);
   void     destroyAndResetDatabases(void);
   
   void doRebuildDatabases(const ProgressCallback &progress);
   void doInitialSyncOnLoad(const ProgressCallback &progress);
   void doInitialSyncOnLoad_Rescan(const ProgressCallback &progress);
   void doInitialSyncOnLoad_Rebuild(const ProgressCallback &progress);
   void doInitialSyncOnLoad_RescanBalance(
      const ProgressCallback &progress);

   // for testing only
   struct BlkFileUpdateCallbacks
   {
      std::function<void()> headersRead, headersUpdated, blockDataLoaded;
   };
   
   void registerBDVwithZCcontainer(shared_ptr<BDV_Server_Object>);
   
private:
   void loadDiskState(
      const ProgressCallback &progress,
      bool doRescan=false
   );
   
public:
   Blockchain::ReorganizationState readBlkFileUpdate(
      const BlkFileUpdateCallbacks &callbacks=BlkFileUpdateCallbacks());

   BinaryData applyBlockRangeToDB(ProgressReporter &prog, 
                            uint32_t blk0, uint32_t blk1,
                            ScrAddrFilter& scrAddrData,
                            bool updateSDBI = true);

   uint32_t getTopBlockHeight() const {return blockchain_.top().getBlockHeight();}
      
   uint8_t getValidDupIDForHeight(uint32_t blockHgt) const
   { return iface_->getValidDupIDForHeight(blockHgt); }

   shared_ptr<ScrAddrFilter> getScrAddrFilter(void) const;


   StoredHeader getMainBlockFromDB(uint32_t hgt) const;
   StoredHeader getBlockFromDB(uint32_t hgt, uint8_t dup) const;

   void enableZeroConf(bool cleanMempool = false);
   void disableZeroConf(void);
   bool isZcEnabled() const { return zcEnabled_; }
   shared_ptr<ZeroConfContainer> zeroConfCont(void) const
   {
      return zeroConfCont_;
   }

public:

   bool startSideScan(
      const function<void(const vector<string>&, double prog,unsigned time)> &cb
   );

   bool isRunning(void) const { return BDMstate_ != BDM_offline; }
   void blockUntilReady(void) const { isReadyFuture_.wait(); }
   bool isReady(void) const
   {
      return 
         isReadyFuture_.wait_for(chrono::seconds(0)) == 
         std::future_status::ready;
   }

   vector<string> getNextWalletIDToScan(void);
};

#endif
