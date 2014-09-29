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
#include "mman.h"
#ifdef _MSC_VER
   #include "leveldb_windows_port\win32_posix\win32_posix.h"
#endif


#define NUM_BLKS_BATCH_THRESH 30

#define NUM_BLKS_IS_DIRTY 2016

using namespace std;

class BlockDataManager_LevelDB;
class LSM;

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
   
   // This is our permanent link to the two databases used
   LMDBBlockDatabase* iface_;
   
   // This is for detecting external changes made to the blk0001.dat file
   vector<string>                     blkFileList_;
   vector<uint64_t>                   blkFileSizes_; // bytes before this blk
   vector<uint64_t>                   blkFileCumul_;
   uint32_t                           numBlkFiles_;
   uint64_t                           endOfLastBlockByte_;

   // On DB initialization, we start processing here
   uint32_t                           startHeaderHgt_;
   uint32_t                           startRawBlkHgt_;
   uint32_t                           startScanHgt_;
   uint32_t                           startApplyHgt_;

   // The following blkfile and offsets correspond to the above heights
   uint32_t                           startHeaderBlkFile_;
   uint64_t                           startHeaderOffset_;
   uint32_t                           startRawBlkFile_;
   uint64_t                           startRawOffset_;
   uint32_t                           startScanBlkFile_;
   uint64_t                           startScanOffset_;
   uint32_t                           startApplyBlkFile_;
   uint64_t                           startApplyOffset_;
   
   // set after the blockchain is organized
   uint32_t                           lastTopBlock_;

   // Reorganization details

   bool                               corruptHeadersDB_;
   int32_t                            lastScannedBlock_;

   class BDM_ScrAddrFilter;
   shared_ptr<BDM_ScrAddrFilter>    scrAddrData_;

private:
  
   // Variables that will be updated as the blockchain loads:
   // can be used to report load progress
   uint64_t totalBlockchainBytes_;
   uint64_t bytesReadSoFar_;
   uint32_t blocksReadSoFar_;
   uint16_t filesReadSoFar_;


   // If the BDM is not in super-node mode, then it will be specifically tracking
   // a set of addresses & wallets.  We register those addresses and wallets so
   // that we know what TxOuts to track as we process blockchain data.  And when
   // it may be necessary to do rescans.
   //
   // If instead we ARE in ARMORY_DB_SUPER (not implemented yet, as of this
   // comment being written), then we don't have anything to track -- the DB
   // will automatically update for all addresses, period.  And we'd best not 
   // track those in RAM (maybe on a huge server...?)
   uint32_t                           allScannedUpToBlk_; // one past top

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
   
public:
   BlockDataManager_LevelDB(const BlockDataManagerConfig &config);
   ~BlockDataManager_LevelDB();

public:

   Blockchain& blockchain() { return blockchain_; }
   const Blockchain& blockchain() const { return blockchain_; }
   
   const BlockDataManagerConfig &config() const { return config_; }

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

   // This figures out where we should start loading headers/rawblocks/scanning
   // The replay argument has been temporarily disable since it's not currently
   // being used, and was causing problems instead.
   uint32_t detectCurrentSyncState(bool rebuild, bool initialLoad);

public:
   /////////////////////////////////////////////////////////////////////////////
   // Get the parameters of the network as they've been set
   const BinaryData& getGenesisHash(void) const  { return config_.genesisBlockHash;   }
   const BinaryData& getGenesisTxHash(void) const { return config_.genesisTxHash; }
   const BinaryData& getMagicBytes(void) const   { return config_.magicBytes;    }

   /////////////////////////////////////////////////////////////////////////////
   // These don't actually work while scanning in another thread!? 
   // The getLoadProgress* methods don't seem to update until after scan done
   uint64_t getTotalBlockchainBytes(void) const {return totalBlockchainBytes_;}
   uint32_t getTotalBlkFiles(void)        const {return numBlkFiles_;}
   uint64_t getLoadProgressBytes(void)    const {return bytesReadSoFar_;}
   uint32_t getLoadProgressBlocks(void)   const {return blocksReadSoFar_;}
   uint16_t getLoadProgressFiles(void)    const {return filesReadSoFar_;}

   
   uint32_t getTopBlockHeightInDB(DB_SELECT db); // testing
   uint32_t getAppliedToHeightInDB(void);

private:
   vector<BinaryData> getFirstHashOfEachBlkFile(void) const;
   uint64_t findOffsetFirstUnrecognized(uint32_t fnum);
   uint32_t findFirstBlkApproxOffset(uint32_t fnum, uint32_t offset) const;
   uint32_t findFirstUnappliedBlock(void);
   pair<uint32_t, uint32_t> findFileAndOffsetForHgt(
               uint32_t hgt, const vector<BinaryData>* firstHashOfEachBlkFile=NULL);


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
                     

   //

   // These are the high-level methods for reading block files, and indexing
   // the blockfile data.
   bool     extractHeadersInBlkFile(uint32_t fnum, uint64_t offset=0);
   uint32_t detectAllBlkFiles(void);
   bool     processNewHeadersInBlkFiles(uint32_t fnumStart=0, uint64_t offset=0);
   //bool     processHeadersInFile(string filename);
   void     destroyAndResetDatabases(void);
   void     buildAndScanDatabases(
      function<void(double,unsigned)> fn,
      bool forceRescan=false, 
      bool forceRebuild=false, 
      bool skipFetch=false,
      bool initialLoad=false
   );
   void readRawBlocksInFile(function<void(uint64_t)> fn, uint32_t blkFileNum, uint32_t offset);
   void readRawBlocksInFile(function<void(uint64_t)> fn, uint32_t blockHeight);
   // These are wrappers around "buildAndScanDatabases"
   void doRebuildDatabases(function<void(double,unsigned)> fn);
   void doFullRescanRegardlessOfSync(function<void(double,unsigned)> fn);
   void doSyncIfNeeded(function<void(double,unsigned)> fn);
   void doInitialSyncOnLoad(function<void(double,unsigned)> fn);
   void doInitialSyncOnLoad_Rescan(function<void(double,unsigned)> fn);
   void doInitialSyncOnLoad_Rebuild(function<void(double,unsigned)> fn);

private:
   void addRawBlockToDB(BinaryRefReader & brr);
   uint32_t getTopScannedBlock(void) const;

public:
   void applyBlockRangeToDB(uint32_t blk0, uint32_t blk1, ScrAddrFilter& scrAddrData);

   // When we add new block data, we will need to store/copy it to its
   // permanent memory location before parsing it.
   // These methods return (blockAddSucceeded, newBlockIsTop, didCauseReorg)
   uint32_t       readBlkFileUpdate(void);
private:
   Blockchain::ReorganizationState addNewBlockData(BinaryRefReader & brrRawBlock, 
                                uint32_t fileIndex0Idx,
                                uint32_t thisHeaderOffset,
                                uint32_t blockSize);


   void deleteHistories(void);
public:
   
   //for 1:1 wallets
   const BlockHeader* getHeaderPtrForTx(Tx& theTx)
                     {return &blockchain_.getHeaderPtrForTx(theTx);}
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

public:

   StoredHeader getMainBlockFromDB(uint32_t hgt);
   uint8_t      getMainDupFromDB(uint32_t hgt) const;
   StoredHeader getBlockFromDB(uint32_t hgt, uint8_t dup);

public:
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
   static void StartCppLogging(string fname, int lvl) { STARTLOGGING(fname, (LogLevel)lvl); }
   static void ChangeCppLogLevel(int lvl) { SETLOGLEVEL((LogLevel)lvl); }
   static void DisableCppLogging() { SETLOGLEVEL(LogLvlDisabled); }
   static void EnableCppLogStdOut() { LOGENABLESTDOUT(); }
   static void DisableCppLogStdOut() { LOGDISABLESTDOUT(); }

   ////////////////////////////////////////////////////////////////////////////////
   void debugPrintDatabases(void) { iface_->pprintBlkDataDB(BLKDATA); }

   /////////////////////////////////////////////////////////////////////////////
   // We may use this to trigger flushing the queued DB updates
   //bool estimateDBUpdateSize(
                        //map<BinaryData, StoredTx> &            stxToModify,
                        //map<BinaryData, StoredScriptHistory> & sshToModify);

   vector<BinaryData> missingBlockHeaderHashes() const { return missingBlockHeaderHashes_; }
   
   vector<BinaryData> missingBlockHashes() const { return missingBlockHashes_; }
};


// kate: indent-width 3; replace-tabs on;

#endif
