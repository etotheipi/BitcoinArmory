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

#ifndef _BDM_SUPPORTCLASSES_H_
#define _BDM_SUPPORTCLASSES_H_

#include <vector>
#include <atomic>
#include <functional>
#include <memory>

#include "ThreadSafeClasses.h"
#include "BitcoinP2p.h"
#include "BinaryData.h"
#include "ScrAddrObj.h"
#include "BtcWallet.h"

#define GETZC_THREADCOUNT 5

enum ZcAction
{
   Zc_NewTx,
   Zc_Purge,
   Zc_Shutdown
};


class ZeroConfContainer;

struct ZeroConfData
{
   Tx            txobj_;
   uint32_t      txtime_;

   bool operator==(const ZeroConfData& rhs) const
   {
      return (this->txobj_ == rhs.txobj_) && (this->txtime_ == rhs.txtime_);
   }
};

class ScrAddrFilter
{
   /***
   This class keeps track of all registered scrAddr to be scanned by the DB.
   If the DB isn't running in supernode, this class also acts as a helper to
   filter transactions, which is required in order to save only relevant ssh

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

   1) Check ssh entries in the DB for this scrAddr. If there is none, this
   DB never saw this address (full/lite node). Else mark the top scanned block.

   -- Non supernode operations --
   2.a) If the address is new, create an empty ssh header for that scrAddr
   in the DB, marked at the current top height
   2.b) If the address isn't new, scan it from its last seen block, or its
   block creation, or 0 if none of the above is available. This will create
   the ssh entries for the address, which will have the current top height as
   its scanned height.
   --

   3) Add address to scrAddrMap_

   4) Signal the wallet that the address is ready. Wallet object will take it
   up from there.
   ***/

   friend class BlockDataViewer;

public:
   struct WalletInfo
   {
      static atomic<unsigned> idCounter_; //no need to init this

      function<void(bool)> callback_;
      set<BinaryData> scrAddrSet_;
      string ID_;
      const unsigned intID_;


      WalletInfo(void) :
         intID_(idCounter_.fetch_add(1, memory_order_relaxed))
      {}

      bool operator<(const ScrAddrFilter::WalletInfo& rhs) const
      {
         return intID_ < rhs.intID_;
      }
   };

   struct ScrAddrSideScanData
   {
      int32_t startScanFrom_= -1;
      vector<shared_ptr<WalletInfo>> wltInfoVec_;
      bool doScan_ = true;
      unsigned uniqueID_ = UINT32_MAX;

      BinaryData lastScannedBlkHash_;

      ScrAddrSideScanData(void) {}
      ScrAddrSideScanData(uint32_t height) :
         startScanFrom_(height) {}

      vector<string> getWalletIDString(void)
      {
         vector<string> strVec;
         for (auto& wltInfo : wltInfoVec_)
            strVec.push_back(wltInfo->ID_);

         return strVec;
      }
   };

   struct AddrSyncState
   {
   private:
      mutable BinaryData addrHash_;

   public:
      const BinaryData scrAddr_;
      int32_t syncHeight_ = -1;

   public:
      AddrSyncState(const BinaryData& addr) :
         scrAddr_(addr)
      {}

      AddrSyncState(const BinaryDataRef& addrref) :
         scrAddr_(addrref)
      {}

      const BinaryData& getHash(void) const
      {
         if (addrHash_.getSize() == 0)
            addrHash_ = move(BtcUtils::getHash256(scrAddr_));

         return addrHash_;
      }

      bool operator<(const AddrSyncState& rhs) const
      {
         return this->scrAddr_ < rhs.scrAddr_;
      }

      bool operator<(const BinaryDataRef& rhs) const
      {
         return this->scrAddr_.getRef() < rhs;
      }
   };
   
public:
   mutex mergeLock_;
   BinaryData lastScannedHash_;
   const ARMORY_DB_TYPE           armoryDbType_;

private:

   static atomic<unsigned> keyCounter_;
   static atomic<bool> run_;

   //TODO: avoid std::set, results in too many implicit copies on searches
   shared_ptr<set<AddrSyncState>>   scrAddrSet_;

   LMDBBlockDatabase *const       lmdb_;

   const unsigned uniqueKey_;

   //
   ScrAddrFilter*                 parent_;
   ScrAddrSideScanData            scrAddrDataForSideScan_;
   
   //false: dont scan
   //true: wipe existing ssh then scan
   bool                           doScan_ = true; 
   bool                           isScanning_ = false;

   Pile<ScrAddrSideScanData> scanDataPile_;
   set<shared_ptr<WalletInfo>> scanningAddresses_;

private:

   void setScrAddrLastScanned(const BinaryData& scrAddr, int32_t blkHgt)
   {
      auto scrAddrIter = scrAddrSet_->find(scrAddr);
      if (scrAddrIter != scrAddrSet_->end())
      {
         auto& sa = (AddrSyncState&)*scrAddrIter;
         sa.syncHeight_ = blkHgt;
      }
   }

   static void cleanUpPreviousChildren(LMDBBlockDatabase* lmdb);

protected:
   function<void(const vector<string>& wltIDs, double prog, unsigned time)>
      scanThreadProgressCallback_;

   static unsigned getUniqueKey(void)
   {
      return keyCounter_.fetch_add(1, memory_order_relaxed);
   }

public:

   static void init(void);

   ScrAddrFilter(LMDBBlockDatabase* lmdb, ARMORY_DB_TYPE armoryDbType)
      : lmdb_(lmdb), armoryDbType_(armoryDbType), 
      uniqueKey_(getUniqueKey())
   {
      //make sure we are running off of a clean SDBI set when instantiating the first
      //SAF object (held by the BDM object)
      if (uniqueKey_ == 0) 
         cleanUpPreviousChildren(lmdb);

      scrAddrSet_ = make_shared<set<AddrSyncState>>();
      scanThreadProgressCallback_ = 
         [](const vector<string>&, double, unsigned)->void {};
   }

   ScrAddrFilter(const ScrAddrFilter& sca) //copy constructor
      : lmdb_(sca.lmdb_), armoryDbType_(sca.armoryDbType_),
      uniqueKey_(getUniqueKey()) //even copies' keys are unique
   {}
   
   virtual ~ScrAddrFilter() { }
   
   LMDBBlockDatabase* lmdb() { return lmdb_; }

   const shared_ptr<set<AddrSyncState>>& getScrAddrSet(void) const
   { 
      if (!run_.load(memory_order_relaxed))
         throw runtime_error("ScrAddrFilter flagged for termination");
      return scrAddrSet_; 
   }

   map<TxOutScriptRef, int> getOutScrRefMap(void)
   {
      getScrAddrCurrentSyncState();
      map<TxOutScriptRef, int> outset;

      auto scrAddrSet = scrAddrSet_;

      for (auto& scrAddr : *scrAddrSet_)
      {
         TxOutScriptRef scrRef;
         scrRef.setRef(scrAddr.scrAddr_);

         outset.insert(move(make_pair(scrRef, scrAddr.syncHeight_)));
      }

      return outset;
   }

   size_t numScrAddr(void) const
   { return scrAddrSet_->size(); }

   int32_t scanFrom(void) const;
   bool registerAddresses(const set<BinaryData>&, string, bool,
      function<void(bool)>);
   bool registerAddressBatch(
      vector<shared_ptr<WalletInfo>>&& wltInfoVec, bool areNew);

   void clear(void);

   void getScrAddrCurrentSyncState();
   void getScrAddrCurrentSyncState(BinaryData const & scrAddr);

   void setSSHLastScanned(uint32_t height);

   void regScrAddrForScan(const BinaryData& scrAddr, uint32_t scanFrom)
   { 
      auto addrIter = scrAddrSet_->find(scrAddr);
      if (addrIter == scrAddrSet_->end())
      {
         AddrSyncState acs(scrAddr);
         acs.syncHeight_ = scanFrom;

         scrAddrSet_->insert(move(acs));
         return;
      }

      auto& acsRef = (AddrSyncState&)*addrIter;
      acsRef.syncHeight_ = scanFrom;
   }

   static void scanFilterInNewThread(shared_ptr<ScrAddrFilter> sca);

   //pointer to the SAF object held by the bdm
   void setParent(ScrAddrFilter* sca) { parent_ = sca; }

   void addToMergePile(const BinaryData& lastScannedBlkHash);
   void mergeSideScanPile(void);

   void getAllScrAddrInDB(void);
   void putAddrMapInDB(void);

   BinaryData getAddressMapMerkle(void) const;
   bool hasNewAddresses(void) const;

   void updateAddressMerkleInDB(void);
   
   StoredDBInfo getSubSshSDBI(void) const;
   void putSubSshSDBI(const StoredDBInfo&);
   StoredDBInfo getSshSDBI(void) const;
   void putSshSDBI(const StoredDBInfo&);
   
   set<BinaryData> getMissingHashes(void) const;
   void putMissingHashes(const set<BinaryData>&);

   static void shutdown(void)
   {
      run_.store(false, memory_order_relaxed);
   }

public:
   virtual shared_ptr<ScrAddrFilter> copy()=0;

protected:
   virtual bool bdmIsRunning() const=0;
   virtual BinaryData applyBlockRangeToDB(
      uint32_t startBlock, uint32_t endBlock, const vector<string>& wltIDs
   )=0;
   virtual uint32_t currentTopBlockHeight() const=0;
   virtual void wipeScrAddrsSSH(const vector<BinaryData>& saVec) = 0;
   virtual shared_ptr<Blockchain> blockchain(void) = 0;
   virtual BlockDataManagerConfig config(void) = 0;

private:
   void scanScrAddrThread(void);
   void buildSideScanData(
      const vector<shared_ptr<WalletInfo>>& wltInfoSet, bool areNew);
};

////////////////////////////////////////////////////////////////////////////////
class ZeroConfContainer
{
private:
   struct BulkFilterData
   {
      map<BinaryData, shared_ptr<map<BinaryData, TxIOPair>>> scrAddrTxioMap_;
      map<BinaryData, map<unsigned, BinaryData>> outPointsSpentByKey_;
      set<BinaryData> txOutsSpentByZC_;

      map<string, set<BinaryData>> flaggedBDVs_;

      bool isEmpty(void) { return scrAddrTxioMap_.size() == 0; }
   };

public:
   struct BDV_Callbacks
   {
      function<void(
         map<BinaryData, shared_ptr<map<BinaryData, TxIOPair>>>
         )> newZcCallback_;

      function<bool(const BinaryData&)> addressFilter_;
   };

   struct ZcActionStruct
   {
      ZcAction action_;
      map<BinaryData, Tx> zcMap_;
      shared_ptr<promise<bool>> finishedPromise_ = nullptr;

      void setData(map<BinaryData, Tx> zcmap)
      {
         zcMap_ = move(zcmap);
      }
   };

private:
   map<HashString, HashString>                  txHashToDBKey_; //<txHash, dbKey>
   map<HashString, Tx>                          txMap_; //<zcKey, zcTx>
   set<HashString>                              txOutsSpentByZC_;     //<txOutDbKeys>
   set<HashString>                              allZcTxHashes_;
   map<BinaryData, map<unsigned, BinaryData>>   outPointsSpentByKey_; //<txHash, map<opId, ZcKeys>>

   //<scrAddr,  <dbKeyOfOutput, TxIOPair>>
   TransactionalMap<HashString, map<BinaryData, TxIOPair>>  txioMap_;
   
   //<zcKey, vector<ScrAddr>>
   TransactionalMap<HashString, set<HashString>> keyToSpentScrAddr_;
   
   BinaryData lastParsedBlockHash_;
   std::atomic<uint32_t> topId_;
   LMDBBlockDatabase* db_;

   static map<BinaryData, TxIOPair> emptyTxioMap_;
   bool enabled_ = false;

   set<BinaryData> emptySetBinData_;

   //stacks inv tx packets from node
   shared_ptr<BitcoinP2P> networkNode_;
   Stack<promise<InvEntry>> newInvTxStack_;
   
   TransactionalMap<string, BDV_Callbacks> bdvCallbacks_;
   TransactionalMap<BinaryData, shared_ptr<promise<bool>>> waitOnZcMap_;

   function<shared_ptr<set<ScrAddrFilter::AddrSyncState>>(void)> getMainAddressSet_;
   mutex parserMutex_;

   vector<thread> parserThreads_;

private:
   BulkFilterData ZCisMineBulkFilter(const Tx & tx,
      const BinaryData& ZCkey,
      uint32_t txtime);

   void loadZeroConfMempool(bool clearMempool);
   set<BinaryData> purge(void);

public:
   //stacks new zc Tx objects from node
   BinaryData getNewZCkey(void);   
   BlockingStack<ZcActionStruct> newZcStack_;

public:
   ZeroConfContainer(LMDBBlockDatabase* db, 
      shared_ptr<BitcoinP2P> node) :
      topId_(0), db_(db), 
      networkNode_(node)
   {
      //register ZC callback
      auto processInvTx = [this](vector<InvEntry> entryVec)->void
      {
         this->processInvTxVec(entryVec);
      };

      networkNode_->registerInvTxLambda(processInvTx);
   }

   bool hasTxByHash(const BinaryData& txHash) const;
   Tx getTxByHash(const BinaryData& txHash) const;

   shared_ptr<map<HashString, map<BinaryData, TxIOPair>>>
      getFullTxioMap(void) const { return txioMap_.get(); }

   void dropZC(const set<BinaryData>& txHashes);
   void parseNewZC(void);
   void parseNewZC(map<BinaryData, Tx> zcMap, bool updateDB, bool notify);
   bool isTxOutSpentByZC(const BinaryData& dbKey) const;
   bool getKeyForTxHash(const BinaryData& txHash, BinaryData& zcKey) const;

   void clear(void);

   map<BinaryData, TxIOPair> getZCforScrAddr(BinaryData scrAddr) const;
   const set<BinaryData>& getSpentSAforZCKey(const BinaryData& zcKey) const;
   const shared_ptr<map<HashString, set<HashString>>> getKeyToSpentScrAddrMap(void) const;

   void updateZCinDB(
      const vector<BinaryData>& keysToWrite, const vector<BinaryData>& keysToDel);

   void processInvTxVec(vector<InvEntry>);
   void processInvTxThread(void);

   void init(function<shared_ptr<set<ScrAddrFilter::AddrSyncState>>(void)>,
      bool clearMempool);
   void shutdown();

   void insertBDVcallback(string, BDV_Callbacks);
   void eraseBDVcallback(string);

   void broadcastZC(const BinaryData& rawzc, uint32_t timeout_sec = 3);
};

//////
struct BDV_Notification
{
   virtual ~BDV_Notification(void)
   {}

   virtual BDV_Action action_type(void) = 0;
};

struct BDV_Notification_Init : public BDV_Notification
{
   BDV_Notification_Init(void)
   {}

   BDV_Action action_type(void)
   {
      return BDV_Init;
   }
};

struct BDV_Notification_NewBlock : public BDV_Notification
{
   Blockchain::ReorganizationState reorgState_;

   BDV_Notification_NewBlock(
      const Blockchain::ReorganizationState& ref) :
      reorgState_(ref)
   {}

   BDV_Action action_type(void)
   {
      return BDV_NewBlock;
   }
};

struct BDV_Notification_ZC : public BDV_Notification
{
   typedef map<BinaryData, shared_ptr<map<BinaryData, TxIOPair>>> zcMapType;
   zcMapType scrAddrZcMap_;

   BDV_Notification_ZC(zcMapType&& mv) :
      scrAddrZcMap_(move(mv))
   {}

   BDV_Action action_type(void)
   {
      return BDV_ZC;
   }
};

struct BDV_Notification_Refresh : public BDV_Notification
{
   const BDV_refresh refresh_;
   const BinaryData refreshID_;

   BDV_Notification_Refresh(
      BDV_refresh refresh, const BinaryData& refreshID) :
      refresh_(refresh), refreshID_(refreshID)
   {}

   BDV_Action action_type(void)
   {
      return BDV_Refresh;
   }
};

struct BDV_Notification_Progress : public BDV_Notification
{
   BDMPhase phase_;
   double progress_;
   unsigned time_;
   unsigned numericProgress_;

   BDV_Notification_Progress(BDMPhase phase, double prog,
      unsigned time, unsigned numProg) :
      phase_(phase), progress_(prog), time_(time),
      numericProgress_(numProg)
   {}

   BDV_Action action_type(void)
   {
      return BDV_Progress;
   }
};

#endif
// kate: indent-width 3; replace-tabs on;
