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
#include "leveldb_wrapper.h"
#include "ScrAddrObj.h"

#include "cryptlib.h"
#include "sha.h"
#include "UniversalTimer.h"
#include "leveldb/db.h"

#include "pthread.h"
#include "ThreadSafeContainer.h"
#include <functional>



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

typedef set<BtcWallet*> set_BtcWallet;
typedef ts_container<set_BtcWallet> ts_setBtcWallet;

struct ZeroConfData
{
   Tx            txobj_;   
   uint32_t      txtime_;

   bool operator==(const ZeroConfData& rhs) const
   {
      return (this->txobj_ == rhs.txobj_) && (this->txtime_ == rhs.txtime_);
   }
};

typedef set<BtcWallet*> set_BtcWallet;
typedef ts_container<set_BtcWallet> ts_setBtcWallet;

typedef map<HashString, BinaryData>   BinDataMap;

class ZeroConfContainer;

class ScrAddrScanData
{
   /***
   This class keeps track of all registered scrAddr to be scanned by the DB.
   If the DB isn't running in supernode, this class also acts as a helper to
   filter transactions, which is required in order to save only relevant SSH

   The transaction filter isn't exact however. It gets more efficient as it 
   encounters more UTxO.

   The basic principle of the filter is that it expect to have a complete
   list of UTxO's starting a given height, usually where the DB picked up
   at initial load. It can then guarantee a TxIn isn't spending a tracked 
   UTxO by checking the UTxO DBkey instead of fetching the entire stored TxOut.
   If the DBkey carries a height lower than the cut off, the filter will
   fail to give a definitive answer, in which case the TxOut script will be 
   pulled from the DB, using the DBkey, as it would have otherwise.

   Registering addresses while the BDM isn't initialized will return instantly
   Otherwise, the following steps are taken:

   1) Check SSH entries in the DB for this scrAddr. If there is none, this
   DB never saw this address (full/lite node). Else mark the top scanned block.

   -- Non supernode operations --
   2.a) If the address is new, create an empty SSH header for that scrAddr 
   in the DB, marked at the current top height
   2.b) If the address isn't new, scan it from its last seen block, or its 
   block creation, or 0 if none of the above is available. This will create 
   the SSH entries for the address, which will have the current top height as 
   its scanned height.
   --

   3) Add address to scrAddrMap_

   4) Signal the wallet that the address is ready. Wallet object will take it 
   up from there.
   ***/

public:
   struct ScrAddrMeta
   {
      /***
      scrAddrMap_ is a map so it can only have meta per scrAddr. This means
      only 1 wallet can be registered per post BDM init address scan.
      ***/
      uint32_t lastScannedHeight_;
      BtcWallet* wltPtr_;

      ScrAddrMeta(void) :
         lastScannedHeight_(0),
         wltPtr_(nullptr) {}

      ScrAddrMeta(uint32_t height, BtcWallet* wltPtr = nullptr) :
         lastScannedHeight_(height),
         wltPtr_(wltPtr) {}
   };

private:
   //map of scrAddr and their respective last scanned block
   //this is used only for the inital load currently
   map<BinaryData, ScrAddrMeta>   scrAddrMap_;
   
   set<BinaryData>                UTxO_;
   mutable uint32_t               blockHeightCutOff_;
   BlockDataManager_LevelDB*      bdmPtr_;
   
   //
   ScrAddrScanData*               parent_;
   set<BinaryData>                UTxOToMerge_;
   map<BinaryData, ScrAddrMeta>   scrAddrMapToMerge_;
   atomic<int32_t>                mergeLock_;
   bool                           mergeFlag_;

   void setScrAddrLastScanned(const BinaryData& scrAddr, uint32_t blkHgt)
   {
      auto& scrAddrIter = scrAddrMap_.find(scrAddr);
      if (ITER_IN_MAP(scrAddrIter, scrAddrMap_))
      {
         scrAddrIter->second.lastScannedHeight_ = blkHgt;
         blockHeightCutOff_ = max(blockHeightCutOff_, blkHgt);
      }
   }

public:
   ScrAddrScanData(BlockDataManager_LevelDB* bdmPtr) :
      bdmPtr_(bdmPtr),
      blockHeightCutOff_(0),
      mergeLock_(0),
      mergeFlag_(false)
   {}

   const map<BinaryData, ScrAddrMeta>& getScrAddrMap(void) const
   {
      return scrAddrMap_;
   }

   uint32_t numScrAddr(void) const
   { return scrAddrMap_.size(); }

   uint32_t scanFrom(void) const
   { 
      uint32_t lowestBlock = UINT32_MAX;

      for (auto scrAddr : scrAddrMap_)
      {
         lowestBlock = min(lowestBlock, scrAddr.second.lastScannedHeight_);
      }

      LOGERR << "blockHeightCutOff: " << blockHeightCutOff_;
      LOGERR << "lowestBlock: " << lowestBlock;

      return lowestBlock;
   }

   bool registerScrAddr(const ScrAddrObj& sa, BtcWallet* wltPtr);

   void unregisterScrAddr(BinaryData& scrAddrIn)
   {
      //simplistic, same as above
      scrAddrMap_.erase(scrAddrIn);
   }

   void reset()
   {
      checkForMerge();
      UTxO_.clear();
      blockHeightCutOff_ = 0;
   }

   bool hasScrAddress(const BinaryData & sa) const
   { return (scrAddrMap_.find(sa) != scrAddrMap_.end()); }

   int8_t hasUTxO(const BinaryData& dbkey) const
   { 
      /*** return values:
      -1: don't know
       0: utxo is not for our addresses
       1: our utxo
      ***/

      if (UTxO_.find(dbkey) == UTxO_.end())
      {
         uint32_t height = DBUtils::hgtxToHeight(dbkey.getSliceRef(0, 4));
         if (height < blockHeightCutOff_)
            return -1;

         return 0;
      }

      return 1;
   }
   
   void addUTxO(pair<const BinaryData, TxIOPair>& txio)
   {
      if (txio.first.getSize() == 8)
      {
         if (txio.second.hasTxOut() && !txio.second.hasTxIn())
            UTxO_.insert(txio.first);
      }
   }

   void addUTxO(const BinaryData& dbkey)
   {
      if (dbkey.getSize() == 8)
         UTxO_.insert(dbkey);
   }

   bool eraseUTxO(const BinaryData& dbkey)
   { return UTxO_.erase(dbkey) == 1; }

   void getScrAddrCurrentSyncState();
   void ScrAddrScanData::getScrAddrCurrentSyncState(
      BinaryData const & scrAddr);

   map<BinaryData, map<BinaryData, TxIOPair> > 
      ZCisMineBulkFilter(const Tx & tx,
      const BinaryData& ZCkey, InterfaceToLDB *db,
      uint32_t txtime,
      const ZeroConfContainer *zcd,
      bool withSecondOrderMultisig = true) const;

   void setSSHLastScanned(InterfaceToLDB *db, uint32_t height);

   void regScrAddrForScan(const BinaryData& scrAddr, uint32_t scanFrom, 
                          BtcWallet* wltPtr)
   { scrAddrMap_[scrAddr] = ScrAddrMeta(scanFrom, wltPtr); }

   void scanScrAddrMapInNewThread(void);

   BlockDataManager_LevelDB* getBDM(void) const { return bdmPtr_; }

   void setParent(ScrAddrScanData* sca) { parent_ = sca; }
   void merge(void);
   void checkForMerge(void);
};

class ZeroConfContainer
{
   /***
   This class does not support parsing ZC without a ScrAddrScanData object to
   filter by scrAddr. This means no undiscriminated ZC tracking is available
   for supernode. However turning the feature on is trivial at this point.

   This class stores and represents ZC transactions by DBkey. While the ZC txn
   do not hit the DB, they are assigned a 6 bytes key like mined transaction
   to unify TxIn parsing by DBkey.

   DBkeys are unique. They are preferable to outPoints because they're cheaper 
   (8 bytes vs 22), and do not incur extra processing to recover when a TxOut
   script is pulled from the DB to recover its scrAddr. They also carry height,
   dupID and TxId natively.

   The first 2 bytes of ZC DBkey will always be 0xFF. The 
   transaction index having to be unique, will be 4 bytes long instead, and 
   produced by atomically incrementing topId_.

   Indeed, at 7 tx/s, including limbo, it is possible a 2 bytes index will 
   overflow on long run cycles.

   Methods:
      addRawTx takes in a raw tx, hashes it and verifies it isnt already added.
      It then unserializes the transaction to a Tx Object, assigns it a key and
      parses it to populate the TxIO map. It returns the Tx key if valid, or an
      empty BinaryData object otherwise.
   ***/

   private:
      map<HashString, HashString>                  txHashToDBKey_;
      map<HashString, Tx>                          txMap_;
      map<HashString, map<BinaryData, TxIOPair> >  txioMap_;

      std::atomic<uint32_t>       topId_;

      ScrAddrScanData*            scrAddrDataPtr_;

      atomic<uint32_t>            lock_;

      //newZCmap_ is ephemeral. Raw ZC are saved until they are processed.
      //The code has a thread pushing new ZC, and set the BDM thread flag
      //to parse it

      map<BinaryData, Tx> newZCMap_;

      BinaryData getNewZCkey(void);
      bool RemoveTxByKey(const BinaryData key);
      bool RemoveTxByHash(const BinaryData txHash);

   public:
      ZeroConfContainer(ScrAddrScanData* sadPtr) : 
         scrAddrDataPtr_(sadPtr), topId_(0) {}

      void addRawTx(const BinaryData& rawTx, uint32_t txtime);
      
      bool hasTxByHash(const BinaryData& txHash) const;
      bool getTxByHash(const BinaryData& txHash, Tx& tx) const;

      map<BinaryData, vector<BinaryData> > purge(InterfaceToLDB *db);

      const map<HashString, map<BinaryData, TxIOPair> >& getTxioMap(void) const
      { return txioMap_; }

      bool parseNewZC(InterfaceToLDB* db);

      bool getKeyForTxHash(const BinaryData& txHash, BinaryData zcKey) const
      {
         const auto& hashPair = txHashToDBKey_.find(txHash);
         if (hashPair != txHashToDBKey_.end())
         {
            zcKey = hashPair->second;
            return true;
         }
         return false;
      }
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

   BlockDataManagerConfig config_;
   
   // This is our permanent link to the two databases used
   InterfaceToLDB* iface_;
   
   // Need a separate memory pool just for zero-confirmation transactions
   // We need the second map to make sure we can find the data to remove
   // it, when necessary
   bool                               zcEnabled_;
   bool                               zcLiteMode_;
   string                             zcFilename_;

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

   ScrAddrScanData                    scrAddrData_;
   ZeroConfContainer                  ZeroConfCont_;

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

   //for 1:1 wallets
   bool rescanZC_;

public:

   Blockchain& blockchain() { return blockchain_; }
   const Blockchain& blockchain() const { return blockchain_; }
   
   const BlockDataManagerConfig &config() const { return config_; }

   /*
   void SetDatabaseModes(ARMORY_DB_TYPE atype, DB_PRUNE_TYPE dtype)
             { DBUtils::setArmoryDbType(atype); DBUtils::setDbPruneType(dtype);}
   void SetDatabaseModes(int atype, int dtype)
             { DBUtils::setArmoryDbType((ARMORY_DB_TYPE)atype); 
               DBUtils::setDbPruneType((DB_PRUNE_TYPE)dtype);}
   void SelectNetwork(string netName);
   void SetHomeDirLocation(string homeDir);
   bool SetBlkFileLocation(string blkdir);
   void SetLevelDBLocation(string ldbdir);
   void SetBtcNetworkParams( BinaryData const & GenHash,
                             BinaryData const & GenTxHash,
                             BinaryData const & MagicBytes);
   void reset(void);
   void DestroyInstance(void);
   */

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
   uint32_t findOffsetFirstUnrecognized(uint32_t fnum);
   uint32_t findFirstBlkApproxOffset(uint32_t fnum, uint32_t offset) const;
   uint32_t findFirstUnappliedBlock(void);
   pair<uint32_t, uint32_t> findFileAndOffsetForHgt(
               uint32_t hgt, const vector<BinaryData>* firstHashOfEachBlkFile=NULL);


   /////////////////////////////////////////////////////////////////////////////
public:
   int32_t          getNumConfirmations(BinaryData txHash);

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
   void     unregisterWallet(BtcWallet* wltPtr);

   bool     walletIsRegistered(BtcWallet & wlt) const;
   bool     scrAddrIsRegistered(BinaryData scrAddr);

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
   void     buildAndScanDatabases(
      function<void(double,unsigned)> fn,
      bool forceRescan=false, 
      bool forceRebuild=false, 
      bool skipFetch=false,
      bool initialLoad=false
   );
   void readRawBlocksInFile(function<void(uint64_t)> fn, uint32_t blkFileNum, uint32_t offset);
   // These are wrappers around "buildAndScanDatabases"
   void doRebuildDatabases(function<void(double,unsigned)> fn);
   void doFullRescanRegardlessOfSync(function<void(double,unsigned)> fn);
   void doSyncIfNeeded(function<void(double,unsigned)> fn);
   void doInitialSyncOnLoad(function<void(double,unsigned)> fn);
   void doInitialSyncOnLoad_Rescan(function<void(double,unsigned)> fn);
   void doInitialSyncOnLoad_Rebuild(function<void(double,unsigned)> fn);

private:
   void addRawBlockToDB(BinaryRefReader & brr);
public:
   void applyBlockRangeToDB(uint32_t blk0=0, uint32_t blk1=UINT32_MAX,
      ScrAddrScanData* scrAddrData = NULL);

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
   bool isZcEnabled() {return zcEnabled_;}
   uint32_t getTopBlockHeight() const {return blockchain_.top().getBlockHeight();}
   InterfaceToLDB *getIFace(void) {return iface_;}
   
   void scanWallets(uint32_t startBlock=UINT32_MAX, 
                    uint32_t endBlock=UINT32_MAX, 
                    bool forceScan=false);
   
   LDBIter getIterator(DB_SELECT db, bool fill_cache = true)
   { return iface_->getIterator(db, fill_cache); }
   
   bool readStoredBlockAtIter(LDBIter & iter, StoredHeader & sbh)
   { return iface_->readStoredBlockAtIter(iter, sbh); }

   uint8_t getValidDupIDForHeight(uint32_t blockHgt)
   { return iface_->getValidDupIDForHeight(blockHgt); }

   // Check for availability of data with a given hash
   TX_AVAILABILITY getTxHashAvail(BinaryDataRef txhash);
   bool hasTxWithHash(BinaryData const & txhash);
   bool hasTxWithHashInDB(BinaryData const & txhash);

   bool parseNewZeroConfTx(void);
   bool hasWallet(BtcWallet* wltPtr) 
      { return registeredWallets_.find(wltPtr) != registeredWallets_.end(); }

public:
   StoredHeader getMainBlockFromDB(uint32_t hgt);
   uint8_t      getMainDupFromDB(uint32_t hgt);
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
   void enableZeroConf(string filename, bool zcLite=true);
   void disableZeroConf(void);
   void readZeroConfFile(string filename);
   void addNewZeroConfTx(BinaryData const & rawTx, uint32_t txtime, 
      bool writeToFile);
   void purgeZeroConfPool(void);
   void pprintZeroConfPool(void) const;
   void rewriteZeroConfFile(void);
   bool isTxFinal(const Tx & tx) const;

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

   /*vector<TxIOPair> getHistoryForScrAddr(BinaryDataRef uniqKey,
                                         bool withMultisig = false) const;*/

   ScrAddrScanData* getScrAddrScanData(void)
   {
      if (config_.armoryDbType != ARMORY_DB_SUPER)
         return &scrAddrData_;

      return nullptr;
   }

   bool registerScrAddr(const ScrAddrObj& sa, BtcWallet* wltPtr=nullptr)
   {
      return scrAddrData_.registerScrAddr(sa, wltPtr);
   }

   const map<BinaryData, map<BinaryData, TxIOPair> >& 
      getZeroConfTxIOMap(void) const
   { return ZeroConfCont_.getTxioMap(); }
};


// kate: indent-width 3; replace-tabs on;

#endif
