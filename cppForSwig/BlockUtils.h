////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2014, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _BLOCKUTILS_H_
#define _BLOCKUTILS_H_

#include <stdio.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <queue>
#include <deque>
#include <list>
#include <bitset>
#include <map>
#include <set>
#include <limits>

#include "Blockchain.h"
#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockObj.h"
#include "StoredBlockObj.h"
#include "BlockDataManagerConfig.h"
#include "lmdb_wrapper.h"
#include "ScrAddrObj.h"

#include "cryptlib.h"
#include "sha.h"
#include "UniversalTimer.h"

#include "pthread.h"
#include <functional>
#include "BDM_supportClasses.h"
#include "BDM_mainthread.h"

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

class ProgressReporter;

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// This class is a singleton -- there can only ever be one, accessed through
// the static method GetInstance().  This method gets the single instantiation
// of the BDM class, and then its public members can be used to access the 
// block data that is sitting in memory.
//

class BlockDataManager_LevelDB
{
private:
   BlockDataManagerConfig config_;
   
   class BitcoinQtBlockFiles;
   shared_ptr<BitcoinQtBlockFiles> readBlockHeaders_;
   
   // This is our permanent link to the two databases used
   LMDBBlockDatabase* iface_;
   
   pair<size_t, uint64_t> blkDataPosition_ = {0, 0};
   
   // Reorganization details

   class BDM_ScrAddrFilter;
   shared_ptr<BDM_ScrAddrFilter>    scrAddrData_;

   BDM_Inject*                      bdmInjectPtr_ = nullptr;
  
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

   uint32_t isRunning_ = 0;

public:
   bool                               sideScanFlag_ = false;
   
public:
   BlockDataManager_LevelDB(const BlockDataManagerConfig &config);
   ~BlockDataManager_LevelDB();

public:

   Blockchain& blockchain() { return blockchain_; }
   const Blockchain& blockchain() const { return blockchain_; }
   
   const BlockDataManagerConfig &config() const { return config_; }
   void setConfig(const BlockDataManagerConfig &bdmConfig);
   void openDatabase(void);
   
private:
   //////////////////////////////////////////////////////////////////////////
   // This method opens the databases, and figures out up to what block each
   // of them is sync'd to.  Then it figures out where that corresponds in
   // the blk*.dat files, so that it can pick up where it left off.  You can 
   // use the last argument to specify an approximate amount of blocks 
   // (specified in bytes) that you would like to replay:  i.e. if 10 MB,
   // lastBlkFileNum_ and endOfLastBlockByte_ variables will be set to
   // the first block that is approximately 10 MB behind your latest block.
   // Then you can pick up from there and let the DB clean up any mess that
   // was left from an unclean shutdown.
   bool initializeDBInterface(ARMORY_DB_TYPE dbt = ARMORY_DB_WHATEVER,
                              DB_PRUNE_TYPE prt = DB_PRUNE_WHATEVER);

public:
   /////////////////////////////////////////////////////////////////////////////
   // Get the parameters of the network as they've been set
   const BinaryData& getGenesisHash(void) const  { return config_.genesisBlockHash;   }
   const BinaryData& getGenesisTxHash(void) const { return config_.genesisTxHash; }
   const BinaryData& getMagicBytes(void) const   { return config_.magicBytes;    }

   /////////////////////////////////////////////////////////////////////////////
   // These don't actually work while scanning in another thread!? 
   // The getLoadProgress* methods don't seem to update until after scan done
   uint64_t getTotalBlockchainBytes() const;
   uint32_t getTotalBlkFiles()        const;
   
   uint32_t getTopBlockHeightInDB(DB_SELECT db); // testing
   uint32_t getAppliedToHeightInDB(void);

   /////////////////////////////////////////////////////////////////////////////
public:
   int32_t          getNumConfirmations(BinaryData txHash);

   TxRef            getTxRefByHash(BinaryData const & txHash);

   bool isDirty(uint32_t numBlockToBeConsideredDirty=NUM_BLKS_IS_DIRTY) const; 

   // Parsing requires the data TO ALREADY BE IN ITS PERMANENT MEMORY LOCATION
   // Pass in a wallet if you want to update the initialScanTxHashes_/OutPoints_
   //bool     parseNewBlock(BinaryRefReader & rawBlockDataReader,
                          //uint32_t fileIndex,
                          //uint32_t thisHeaderOffset,
                          //uint32_t blockSize);

   void     destroyAndResetDatabases(void);
   
   void doRebuildDatabases(const function<void(unsigned, double,unsigned)> &progress);
   void doInitialSyncOnLoad(const function<void(unsigned, double,unsigned)> &progress);
   void doInitialSyncOnLoad_Rescan(const function<void(unsigned, double,unsigned)> &progress);
   void doInitialSyncOnLoad_Rebuild(const function<void(unsigned, double,unsigned)> &progress);
   uint32_t readBlkFileUpdate();
   
private:
   void loadDiskState(
      const function<void(unsigned, double,unsigned)> &progress,
      bool doRescan=false
   );
   void loadBlockData(ProgressReporter &prog, bool updateDupID);
   void loadBlockHeadersFromDB();
   pair<pair<size_t, uint64_t>, vector<BlockHeader*> >
      loadBlockHeadersStartingAt(
         ProgressReporter &prog,
         const pair<size_t, uint64_t> &fileAndOffset
      );
   void deleteHistories(void);
   void addRawBlockToDB(BinaryRefReader & brr, bool updateDupID = true);

public:
   
   void setNotifyPtr(BDM_Inject* injectPtr) { bdmInjectPtr_ = injectPtr; }
   void notifyMainThread(void) 
   { 
      if (bdmInjectPtr_) 
         bdmInjectPtr_->notify(); 
   }
   bool hasInjectPtr(void) const { return bdmInjectPtr_ != nullptr; }

   BinaryData applyBlockRangeToDB(ProgressReporter &prog, 
                            uint32_t blk0, uint32_t blk1,
                            ScrAddrFilter& scrAddrData,
                            bool updateSDBI = true);

   uint32_t getTopBlockHeight() const {return blockchain_.top().getBlockHeight();}
   LMDBBlockDatabase *getIFace(void) {return iface_;}
      
   LDBIter getIterator(DB_SELECT db)
   {
      return iface_->getIterator(db);
   }
   
   bool readStoredBlockAtIter(LDBIter & iter, StoredHeader & sbh)
   { return iface_->readStoredBlockAtIter(iter, sbh); }

   uint8_t getValidDupIDForHeight(uint32_t blockHgt)
   { return iface_->getValidDupIDForHeight(blockHgt); }

   // Check for availability of data with a given hash
   bool hasTxWithHash(BinaryData const & txhash);
   bool hasTxWithHashInDB(BinaryData const & txhash);

   ScrAddrFilter* getScrAddrFilter(void) const;


   StoredHeader getMainBlockFromDB(uint32_t hgt);
   uint8_t      getMainDupFromDB(uint32_t hgt) const;
   StoredHeader getBlockFromDB(uint32_t hgt, uint8_t dup);

   /////////////////////////////////////////////////////////////////////////////
   // With the blockchain in supernode mode, we can just query address balances
   // and UTXO sets directly.  These will fail if not supernode mode
   uint64_t             getDBBalanceForHash160(BinaryDataRef addr160);
private:
   uint64_t             getDBReceivedForHash160(BinaryDataRef addr160);
   vector<UnspentTxOut> getUTXOVectForHash160(BinaryDataRef addr160);
public:
   // For zero-confirmation tx-handling
   bool isTxFinal(const Tx & tx) const;

public:

// These things should probably be private, but they also need to be test-able,
// and googletest apparently cannot access private methods without polluting 
// this class with gtest code
//private: 

   //void pprintSSHInfoAboutHash160(BinaryData const & a160);

   // Simple wrapper around the logger so that they are easy to access from SWIG

   ////////////////////////////////////////////////////////////////////////////////
   void debugPrintDatabases(void) { iface_->pprintBlkDataDB(BLKDATA); }

   /////////////////////////////////////////////////////////////////////////////
   // We may use this to trigger flushing the queued DB updates
   //bool estimateDBUpdateSize(
                        //map<BinaryData, StoredTx> &            stxToModify,
                        //map<BinaryData, StoredScriptHistory> & sshToModify);

   vector<BinaryData> missingBlockHeaderHashes() const { return missingBlockHeaderHashes_; }
   
   vector<BinaryData> missingBlockHashes() const { return missingBlockHashes_; }

   void startSideScan(
      function<void(const BinaryData&, double prog, unsigned time)> progress);

   void wipeScrAddrsSSH(const vector<BinaryData>& saVec);

   bool isRunning(void) const { return isRunning_ > 0; }
};


// kate: indent-width 3; replace-tabs on;

#endif
