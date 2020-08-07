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
#define TXGETDATA_TIMEOUT_MS 10000

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
   friend class ZeroConfContainer;

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
         {
            if (wltInfo->ID_.size() == 0)
               continue;

            strVec.push_back(wltInfo->ID_);
         }

         return strVec;
      }
   };

   struct AddrAndHash
   {
   private:
      mutable BinaryData addrHash_;

   public:
      const BinaryData scrAddr_;

   public:
      AddrAndHash(const BinaryData& addr) :
         scrAddr_(addr)
      {}

      AddrAndHash(const BinaryDataRef& addrref) :
         scrAddr_(addrref)
      {}

      const BinaryData& getHash(void) const
      {
         if (addrHash_.getSize() == 0)
            addrHash_ = move(BtcUtils::getHash256(scrAddr_));

         return addrHash_;
      }

      bool operator<(const AddrAndHash& rhs) const
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

   shared_ptr<TransactionalMap<AddrAndHash, int>>   scrAddrMap_;

   LMDBBlockDatabase *const       lmdb_;

   const unsigned uniqueKey_;

   //
   ScrAddrFilter*                 parent_ = nullptr;
   ScrAddrSideScanData            scrAddrDataForSideScan_;
   
   //false: dont scan
   //true: wipe existing ssh then scan
   bool                           isScanning_ = false;

   Pile<ScrAddrSideScanData> scanDataPile_;
   set<shared_ptr<WalletInfo>> scanningAddresses_;

private:
   static void cleanUpPreviousChildren(LMDBBlockDatabase* lmdb);

   shared_ptr<TransactionalMap<AddrAndHash, int>>
      getScrAddrTransactionalMap(void) const
   {
      return scrAddrMap_;
   }

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

      scrAddrMap_ = make_shared<TransactionalMap<AddrAndHash, int>>();
      scanThreadProgressCallback_ = 
         [](const vector<string>&, double, unsigned)->void {};
   }

   ScrAddrFilter(const ScrAddrFilter& sca) //copy constructor
      : lmdb_(sca.lmdb_), armoryDbType_(sca.armoryDbType_),
      uniqueKey_(getUniqueKey()) //even copies' keys are unique
   {
      scrAddrMap_ = make_shared<TransactionalMap<AddrAndHash, int>>();
   }
   
   virtual ~ScrAddrFilter() { }
   
   LMDBBlockDatabase* lmdb() { return lmdb_; }

   shared_ptr<map<AddrAndHash, int>> getScrAddrMap(void) const
   { 
      if (!run_.load(memory_order_relaxed))
      {
         LOGERR << "ScrAddrFilter flagged for termination";
         throw runtime_error("ScrAddrFilter flagged for termination");
      }
      return scrAddrMap_->get(); 
   }

   shared_ptr<map<TxOutScriptRef, int>> getOutScrRefMap(void)
   {
      getScrAddrCurrentSyncState();
      auto outset = make_shared<map<TxOutScriptRef, int>>();

      auto scrAddrMap = scrAddrMap_->get();

      for (auto& scrAddr : *scrAddrMap)
      {
         if (scrAddr.first.scrAddr_.getSize() == 0)
            continue;

         TxOutScriptRef scrRef;
         scrRef.setRef(scrAddr.first.scrAddr_);

         outset->insert(move(make_pair(scrRef, scrAddr.second)));
      }

      return outset;
   }

   size_t numScrAddr(void) const
   {
      return scrAddrMap_->size();
   }

   int32_t scanFrom(void) const;
   bool registerAddresses(const set<BinaryData>&, string, bool,
      function<void(bool)>);
   bool registerAddressBatch(
      vector<shared_ptr<WalletInfo>>&& wltInfoVec, bool areNew);

   void clear(void);

   void getScrAddrCurrentSyncState();
   int getScrAddrCurrentSyncState(BinaryData const & scrAddr);

   void setSSHLastScanned(uint32_t height);

   void regScrAddrVecForScan(
      const vector<pair<BinaryData, unsigned>>& addrVec)
   { 
      map<AddrAndHash, int> saMap;
      for (auto& addrpair : addrVec)
      {
         AddrAndHash aah(addrpair.first);
         saMap.insert(move(make_pair(move(aah), addrpair.second)));
      }

      scrAddrMap_->update(saMap);
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
      uint32_t startBlock, uint32_t endBlock, const vector<string>& wltIDs,
      bool reportProgress)=0;
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
      map<BinaryData, set<BinaryData>> keyToSpentScrAddr_;
      map<BinaryData, set<BinaryData>> keyToFundedScrAddr_;

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
      function<void(string&, string&)> zcErrorCallback_;
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
   TransactionalMap<HashString, HashString>     txHashToDBKey_;      //<txHash, dbKey>
   TransactionalMap<HashString, Tx>             txMap_;              //<zcKey, zcTx>
   TransactionalSet<HashString>                 txOutsSpentByZC_;    //<txOutDbKeys>
   set<HashString>                              allZcTxHashes_;
   map<BinaryData, map<unsigned, BinaryData>>   outPointsSpentByKey_; //<txHash, map<opId, ZcKeys>>

   //<scrAddr,  <dbKeyOfOutput, TxIOPair>>
   TransactionalMap<BinaryData, shared_ptr<map<BinaryData, TxIOPair>>>  txioMap_;
   
   //<zcKey, vector<ScrAddr>>
   TransactionalMap<HashString, set<HashString>> keyToSpentScrAddr_;
   map<BinaryData, set<BinaryData>> keyToFundedScrAddr_;

   //
   map<string, pair<bool, set<BinaryData>>> flaggedBDVs_;
   
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
   mutex parserMutex_;

   Stack<thread> parserThreads_;
   atomic<bool> zcEnabled_;
   const unsigned maxZcThreadCount_;

   shared_ptr<TransactionalMap<ScrAddrFilter::AddrAndHash, int>> scrAddrMap_;

private:
   BulkFilterData ZCisMineBulkFilter(const Tx & tx,
      const BinaryData& ZCkey,
      uint32_t txtime,
      function<bool(const BinaryData&, BinaryData&)> getzckeyfortxhash,
      function<const Tx&(const BinaryData&)> getzctxbykey);

   void loadZeroConfMempool(bool clearMempool);
   set<BinaryData> purge(void);

   void processInvTxThread(void);
   bool processInvTxThread(InvEntry, unsigned timeout_ms);

public:
   //stacks new zc Tx objects from node
   BinaryData getNewZCkey(void);   
   BlockingStack<ZcActionStruct> newZcStack_;

public:
   ZeroConfContainer(LMDBBlockDatabase* db, 
      shared_ptr<BitcoinP2P> node, unsigned maxZcThread) :
      topId_(0), db_(db), maxZcThreadCount_(maxZcThread), networkNode_(node)
   {
      zcEnabled_.store(false, memory_order_relaxed);

      //register ZC callback
      auto processInvTx = [this](vector<InvEntry> entryVec)->void
      {
         this->processInvTxVec(entryVec);
      };

      networkNode_->registerInvTxLambda(processInvTx);
   }

   bool hasTxByHash(const BinaryData& txHash) const;
   Tx getTxByHash(const BinaryData& txHash) const;

   shared_ptr<map<BinaryData, shared_ptr<map<BinaryData, TxIOPair>>>>
      getFullTxioMap(void) const { return txioMap_.get(); }

   void dropZC(const set<BinaryData>& txHashes);
   void parseNewZC(void);
   void parseNewZC(map<BinaryData, Tx> zcMap, bool updateDB, bool notify);
   bool isTxOutSpentByZC(const BinaryData& dbKey) const;

   void clear(void);

   map<BinaryData, TxIOPair> getUnspentZCforScrAddr(BinaryData scrAddr) const;
   map<BinaryData, TxIOPair> getRBFTxIOsforScrAddr(BinaryData scrAddr) const;

   vector<TxOut> getZcTxOutsForKey(const set<BinaryData>&) const;

   const set<BinaryData>& getSpentSAforZCKey(const BinaryData& zcKey) const;
   const shared_ptr<map<BinaryData, set<HashString>>> getKeyToSpentScrAddrMap(void) const;

   void updateZCinDB(
      const vector<BinaryData>& keysToWrite, const vector<BinaryData>& keysToDel);

   void processInvTxVec(vector<InvEntry>, bool extend = true);

   void init(shared_ptr<ScrAddrFilter>, bool clearMempool);
   void shutdown();

   void insertBDVcallback(string, BDV_Callbacks);
   void eraseBDVcallback(string);

   void broadcastZC(const BinaryData& rawzc, 
      const string& bdvId, uint32_t timeout_ms);

   bool isEnabled(void) const { return zcEnabled_.load(memory_order_relaxed); }
   void pushZcToParser(const BinaryData& rawTx);
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
   map<BinaryData, LedgerEntry> leMap_;

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
   const vector<string> walletIDs_;

   BDV_Notification_Progress(BDMPhase phase, double prog,
      unsigned time, unsigned numProg, const vector<string>& walletIDs) :
      phase_(phase), progress_(prog), time_(time),
      numericProgress_(numProg), walletIDs_(walletIDs)
   {}

   BDV_Action action_type(void)
   {
      return BDV_Progress;
   }
};

struct BDV_Notification_NodeStatus : public BDV_Notification
{
   const NodeStatusStruct status_;

   BDV_Notification_NodeStatus(NodeStatusStruct nss) :
      status_(nss)
   {}

   BDV_Action action_type(void)
   {
      return BDV_NodeStatus;
   }
};

struct BDV_Notification_Error : public BDV_Notification
{
   BDV_Error_Struct errStruct;

   BDV_Notification_Error(
      BDV_ErrorType errt, string errstr, string extra)
   {
      errStruct.errType_ = errt;
      errStruct.errorStr_ = errstr;
      errStruct.extraMsg_ = extra;
   }

   BDV_Action action_type(void)
   {
      return BDV_Error;
   }

};

#endif
// kate: indent-width 3; replace-tabs on;
