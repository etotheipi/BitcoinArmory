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
//#ifdef WIN32
//#include <cstdint>
//#else
//#include <stdlib.h>
//#include <inttypes.h>
//#include <cstring>
//#endif
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
#include "leveldb_wrapper.h"

#include "cryptlib.h"
#include "sha.h"
#include "UniversalTimer.h"
#include "leveldb/db.h"


#define NUM_BLKS_BATCH_THRESH 30

#define NUM_BLKS_IS_DIRTY 2016

using namespace std;

class BlockDataManager_LevelDB;

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


class BtcWallet;

struct ZeroConfData
{
   Tx            txobj_;   
   uint32_t      txtime_;
   list<BinaryData>::iterator iter_;
};



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

   // This is our permanent link to the two databases used
   InterfaceToLDB* iface_;
   
   // Need a separate memory pool just for zero-confirmation transactions
   // We need the second map to make sure we can find the data to remove
   // it, when necessary
   list<BinaryData>                   zeroConfRawTxList_;
   map<HashString, ZeroConfData>      zeroConfMap_;
   bool                               zcEnabled_;
   bool                               zcLiteMode_;
   string                             zcFilename_;

   // This is for detecting external changes made to the blk0001.dat file
   bool                               isBlkParamsSet_;
   bool                               isLevelDBSet_;
   string                             armoryHomeDir_;
   string                             leveldbDir_;
   string                             blkFileDir_;
   vector<string>                     blkFileList_;
   vector<uint64_t>                   blkFileSizes_; // bytes before this blk
   vector<uint64_t>                   blkFileCumul_;
   uint32_t                           numBlkFiles_;
   uint64_t                           endOfLastBlockByte_;

   // These files are for signaling to python code, which had to be hacked 
   // in order to work while TheBDM is scanning
   string                             blkProgressFile_;
   string                             abortLoadFile_;
   uint32_t                           progressTimer_;

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

   bool                               isInitialized_;
   int32_t                            lastScannedBlock_;

   // These will be set for the specific network we are testing
   BinaryData GenesisHash_;
   BinaryData GenesisTxHash_;
   BinaryData MagicBytes_;
   
   //for C++ side maintenance thread
   bool run_;

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
   set<BtcWallet*>                    registeredWallets_;
   //map<BinaryData, RegisteredScrAddr> registeredScrAddrMap_;
   //list<RegisteredTx>                 registeredTxList_;
   //set<HashString>                    registeredTxSet_;
   //set<OutPoint>                      registeredOutPoints_;
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
   BlockDataManager_LevelDB(void);
   ~BlockDataManager_LevelDB(void);

   //for 1:1 wallets
   bool rescanZC_;

public:

   Blockchain& blockchain() { return blockchain_; }
   const Blockchain& blockchain() const { return blockchain_; }

   bool isInitialized(void) const { return isInitialized_;}

   void SetDatabaseModes(ARMORY_DB_TYPE atype, DB_PRUNE_TYPE dtype)
             { DBUtils.setArmoryDbType(atype); DBUtils.setDbPruneType(dtype);}
   void SetDatabaseModes(int atype, int dtype)
             { DBUtils.setArmoryDbType((ARMORY_DB_TYPE)atype); 
               DBUtils.setDbPruneType((DB_PRUNE_TYPE)dtype);}
   void SelectNetwork(string netName);
   void SetHomeDirLocation(string homeDir);
   bool SetBlkFileLocation(string blkdir);
   void SetLevelDBLocation(string ldbdir);
   void SetBtcNetworkParams( BinaryData const & GenHash,
                             BinaryData const & GenTxHash,
                             BinaryData const & MagicBytes);
   void reset(void);
   void DestroyInstance(void);

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
   bool detectCurrentSyncState(bool rebuild, bool initialLoad);

public:
   /////////////////////////////////////////////////////////////////////////////
   // Get the parameters of the network as they've been set
   const BinaryData& getGenesisHash(void) const  { return GenesisHash_;   }
   const BinaryData& getGenesisTxHash(void) const { return GenesisTxHash_; }
   const BinaryData& getMagicBytes(void) const   { return MagicBytes_;    }

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
   uint32_t findOffsetFirstUnrecognized(uint32_t fnum);
   uint32_t findFirstBlkApproxOffset(uint32_t fnum, uint32_t offset) const;
   uint32_t findFirstUnappliedBlock(void);
   pair<uint32_t, uint32_t> findFileAndOffsetForHgt(
               uint32_t hgt, const vector<BinaryData>* firstHashOfEachBlkFile=NULL);


   /////////////////////////////////////////////////////////////////////////////
public:
   int32_t          getNumConfirmations(BinaryData txHash);
   string           getBlockfilePath(void) {return blkFileDir_;}

   TxRef            getTxRefByHash(BinaryData const & txHash);
   Tx               getTxByHash(BinaryData const & txHash);

   bool isDirty(uint32_t numBlockToBeConsideredDirty=NUM_BLKS_IS_DIRTY) const; 

   //uint32_t getNumTx(void) { return txHintMap_.size(); }

   /////////////////////////////////////////////////////////////////////////////
   // If you register you wallet with the BDM, it will automatically maintain 
   // tx lists relevant to that wallet.  You can get away without registering
   // your wallet objects (using scanBlockchainForTx), but without the full 
   // blockchain in RAM, each scan will take 30-120 seconds.  Registering makes 
   // sure that the intial blockchain scan picks up wallet-relevant stuff as 
   // it goes, and does a full [re-]scan of the blockchain only if necessary.
   bool     registerWallet(BtcWallet* wallet, bool wltIsNew=false);
   void     unregisterWallet(BtcWallet* wlt) {registeredWallets_.erase(wlt);}

   uint32_t evalLowestBlockNextScan(void);
   uint32_t evalLowestScrAddrCreationBlock(void);
   bool     evalRescanIsRequired(void);
   void     updateRegisteredScrAddrs(uint32_t newTopBlk);

   bool     walletIsRegistered(BtcWallet & wlt);
   bool     scrAddrIsRegistered(HashString scrAddr);

   void     registeredScrAddrScan( Tx & theTx );
   void     registeredScrAddrScan( uint8_t const * txptr,
                                   uint32_t txSize=0,
                                   vector<uint32_t> * txInOffsets=NULL,
                                   vector<uint32_t> * txOutOffsets=NULL);
public:
   void     resetRegisteredWallets(void);
   void     pprintRegisteredWallets(void);

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
   void     buildAndScanDatabases(bool forceRescan=false, 
                                  bool forceRebuild=false, 
                                  bool skipFetch=false,
                                  bool initialLoad=false);
   void readRawBlocksInFile(uint32_t blkFileNum, uint32_t offset);
   // These are wrappers around "buildAndScanDatabases"
   void doRebuildDatabases(void);
   void doFullRescanRegardlessOfSync(void);
   void doSyncIfNeeded(void);
   void doInitialSyncOnLoad(void);
   void doInitialSyncOnLoad_Rescan(void);
   void doInitialSyncOnLoad_Rebuild(void);

private:
   void addRawBlockToDB(BinaryRefReader & brr);
public:
   void applyBlockRangeToDB(uint32_t blk0=0, uint32_t blk1=UINT32_MAX);

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
   void saveScrAddrHistories(void);
   
   //for 1:1 wallets
   void fetchWalletsRegisteredScrAddrData(void);
   const BlockHeader* getHeaderPtrForTx(Tx& theTx)
                     {return &blockchain_.getHeaderPtrForTx(theTx);}
   bool isZcEnabled() {return zcEnabled_;}
   uint32_t getTopBlockHeight() {return blockchain_.top().getBlockHeight();}
   bool doRun() {return run_;}
   void doShutdown() {run_ = false;}
   void scanBlockchainForTx(uint32_t startBlknum, uint32_t endBlknum,
                                                   bool fetchFirst);
   void rescanWalletZeroConf();
   InterfaceToLDB *getIFace(void) {return iface_;}
   vector<TxIOPair> getHistoryForScrAddr(BinaryDataRef uniqKey, 
                                          bool withMultisig=false);
   void eraseTx(const BinaryData& txHash);
   uint32_t numBlocksToRescan( BtcWallet & wlt, uint32_t endBlk);


   // Check for availability of data with a given hash
   TX_AVAILABILITY getTxHashAvail(BinaryDataRef txhash);
   bool hasTxWithHash(BinaryData const & txhash);
   bool hasTxWithHashInDB(BinaryData const & txhash);

public:
   //uint32_t getNumTx(void) const { return txHintMap_.size(); }
   StoredHeader getMainBlockFromDB(uint32_t hgt);
   uint8_t      getMainDupFromDB(uint32_t hgt);
   StoredHeader getBlockFromDB(uint32_t hgt, uint8_t dup);


   // Traverse the blockchain and update the wallet[s] with the relevant Tx data
   // See comments above the scanBlockchainForTx in the .cpp, for more info
   // NOTE: THIS ASSUMES THAT registeredTxSet_/List_ is already populated!
   void scanBlockchainForTx(BtcWallet & myWallet,
                            uint32_t startBlknum=0,
                            uint32_t endBlknum=UINT32_MAX,
                            bool fetchFirst=true);

private:
   void writeProgressFile(DB_BUILD_PHASE phase, 
                          string bfile, 
                          string timerName);

public:
   // This will only be used by the above method, probably wouldn't be called
   // directly from any other code
   void scanRegisteredTxForWallets( uint32_t blkStart=0,
                                   uint32_t blkEnd=UINT32_MAX);
private:
   void scanDBForRegisteredTx(uint32_t blk0=0, uint32_t blk1=UINT32_MAX);
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
   void enableZeroConf(string filename, bool zcLite=true);
   void disableZeroConf(void);
   void readZeroConfFile(string filename);
   bool addNewZeroConfTx(BinaryData const & rawTx, uint32_t txtime, bool writeToFile);
   void purgeZeroConfPool(void);
   void pprintZeroConfPool(void);
   void rewriteZeroConfFile(void);
   bool isTxFinal(const Tx & tx) const;
   void rescanWalletZeroConf(BtcWallet & wlt);

public:
   // Use these two methods to get ALL information about your unused TxOuts
   //vector<UnspentTxOut> getUnspentTxOutsForWallet(BtcWallet & wlt, int sortType=-1);
   //vector<UnspentTxOut> getNonStdUnspentTxOutsForWallet(BtcWallet & wlt);

   ////////////////////////////////////////////////////////////////////////////////
   // We're going to need the BDM's help to get the sender for a TxIn since it
   // sometimes requires going and finding the TxOut from the distant past
   TxOut      getPrevTxOut(TxIn & txin);
   Tx         getPrevTx(TxIn & txin);
   BinaryData getSenderScrAddr(TxIn & txin);
   int64_t    getSentValue(TxIn & txin);

// These things should probably be private, but they also need to be test-able,
// and googletest apparently cannot access private methods without polluting 
// this class with gtest code
//private: 

   void pprintSSHInfoAboutHash160(BinaryData const & a160);

   
   /////////////////////////////////////////////////////////////////////////////
   void     setMaxOpenFiles(uint32_t n) {iface_->setMaxOpenFiles(n);}
   uint32_t getMaxOpenFiles(void)       {return iface_->getMaxOpenFiles();}
   void     setLdbBlockSize(uint32_t sz){iface_->setLdbBlockSize(sz);}
   uint32_t getLdbBlockSize(void)       {return iface_->getLdbBlockSize();}

   // Simple wrapper around the logger so that they are easy to access from SWIG
   void StartCppLogging(string fname, int lvl) { STARTLOGGING(fname, (LogLevel)lvl); }
   void ChangeCppLogLevel(int lvl) { SETLOGLEVEL((LogLevel)lvl); }
   void DisableCppLogging(void) { SETLOGLEVEL(LogLvlDisabled); }
   void EnableCppLogStdOut(void) { LOGENABLESTDOUT(); }
   void DisableCppLogStdOut(void) { LOGDISABLESTDOUT(); }

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


////////////////////////////////////////////////////////////////////////////////
//
// We have a problem with "classic" swig refusing to compile static functions,
// which gives me no way to access BDM which is a singleton class accessed by
// a static class method.  This class simply wraps the call to be invoked in
// python/swig
//
////////////////////////////////////////////////////////////////////////////////
class BlockDataManager
{
public:
   BlockDataManager_LevelDB & getBDM(void)
   {
      if (!bdm_)
         bdm_ = new BlockDataManager_LevelDB;
      return *bdm_;
   }
   
   void destroy()
   {
      delete bdm_;
      bdm_ = 0;
   }

private:
   static BlockDataManager_LevelDB* bdm_;
};

// kate: indent-width 3; replace-tabs on;

#endif
