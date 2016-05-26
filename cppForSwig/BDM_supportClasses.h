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
      function<void(void)> callback_;
      set<BinaryData> scrAddrSet_;
      string ID_;

      bool operator<(const ScrAddrFilter::WalletInfo& rhs) const
      {
         return ID_ < rhs.ID_;
      }
   };

   struct ScrAddrSideScanData
   {
      /***
      scrAddrMap_ is a map so it can only have meta per scrAddr. This means
      only 1 wallet can be registered per post BDM init address scan.
      ***/
      uint32_t startScanFrom_=0;
      vector<WalletInfo> wltInfoVec_;
      bool doScan_ = true;

      BinaryData lastScannedBlkHash_;

      ScrAddrSideScanData(void) {}
      ScrAddrSideScanData(uint32_t height) :
         startScanFrom_(height) {}

      vector<string> getWalletIDString(void)
      {
         vector<string> strVec;
         for (auto& wltInfo : wltInfoVec_)
            strVec.push_back(wltInfo.ID_);

         return strVec;
      }
   };
   
public:
   mutex mergeLock_;
   BinaryData lastScannedHash_;

private:

   shared_ptr<map<BinaryData, uint32_t>>   scrAddrMap_;

   LMDBBlockDatabase *const       lmdb_;

   //
   ScrAddrFilter*                 parent_;
   ScrAddrSideScanData            scrAddrDataForSideScan_;
   
   //false: dont scan
   //true: wipe existing ssh then scan
   bool                           doScan_ = true; 
   bool                           isScanning_ = false;

   Pile<ScrAddrSideScanData> scanDataPile_;

   void setScrAddrLastScanned(const BinaryData& scrAddr, uint32_t blkHgt)
   {
      auto scrAddrIter = scrAddrMap_->find(scrAddr);
      if (scrAddrIter != scrAddrMap_->end())
         scrAddrIter->second = blkHgt;
   }

protected:
   function<void(const vector<string>& wltIDs, double prog, unsigned time)>
      scanThreadProgressCallback_;// = [](const vector<string>&, double, unsigned)->void {};

public:
   
   const ARMORY_DB_TYPE           armoryDbType_;
  
   ScrAddrFilter(LMDBBlockDatabase* lmdb, ARMORY_DB_TYPE armoryDbType)
      : lmdb_(lmdb), armoryDbType_(armoryDbType)
   {
      scrAddrMap_ = make_shared<map<BinaryData, uint32_t>>();
      scanThreadProgressCallback_ = 
         [](const vector<string>&, double, unsigned)->void {};
   }

   ScrAddrFilter(const ScrAddrFilter& sca) //copy constructor
      : lmdb_(sca.lmdb_), armoryDbType_(sca.armoryDbType_)
   {}
   
   virtual ~ScrAddrFilter() { }
   
   LMDBBlockDatabase* lmdb() { return lmdb_; }

   const shared_ptr<map<BinaryData, uint32_t>>& getScrAddrMap(void) const
   { return scrAddrMap_; }

   size_t numScrAddr(void) const
   { return scrAddrMap_->size(); }

   uint32_t scanFrom(void) const;
   bool registerAddresses(const set<BinaryData>&, string, bool,
      function<void(void)>);
   bool registerAddressBatch(vector<WalletInfo>&& wltInfoVec, bool areNew);

   void clear(void);

   bool hasScrAddress(const BinaryData & sa)
   { 
      auto scraddrmapptr = scrAddrMap_;
      return (scraddrmapptr->find(sa) != scraddrmapptr->end());
   }

   void getScrAddrCurrentSyncState();
   void getScrAddrCurrentSyncState(BinaryData const & scrAddr);

   void setSSHLastScanned(uint32_t height);

   void regScrAddrForScan(const BinaryData& scrAddr, uint32_t scanFrom)
   { (*scrAddrMap_)[scrAddr] = scanFrom; }

   static void scanFilterInNewThread(shared_ptr<ScrAddrFilter> sca);

   //pointer to the SCA object held by the bdm
   void setParent(ScrAddrFilter* sca) { parent_ = sca; }

   //shared_ptr to the next object in line waiting to get scanned. Only one
   //scan takes place at a time, so if several wallets are imported before
   //the first one is done scanning, a SCA will be built and referenced to as
   //the child to previous side thread scan SCA, which will initiate the next 
   //scan before it cleans itself up

   void addToMergePile(const BinaryData& lastScannedBlkHash);
   void mergeSideScanPile(void);

   void getAllScrAddrInDB(void);
   BinaryData getAddressMapMerkle(void) const;
   bool hasNewAddresses(void) const;

public:
   virtual shared_ptr<ScrAddrFilter> copy()=0;

protected:
   virtual bool bdmIsRunning() const=0;
   virtual BinaryData applyBlockRangeToDB(
      uint32_t startBlock, uint32_t endBlock, const vector<string>& wltIDs
   )=0;
   virtual uint32_t currentTopBlockHeight() const=0;
   virtual void wipeScrAddrsSSH(const vector<BinaryData>& saVec) = 0;
   virtual Blockchain& blockchain(void) = 0;
   virtual BlockDataManagerConfig config(void) = 0;

private:
   void scanScrAddrThread(void);
   void buildSideScanData(const vector<WalletInfo>& wltInfoSet, bool areNew);
};

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
         map<
         BinaryData, shared_ptr<
         map<BinaryData, TxIOPair >> >
         )> newZcCallback_;

      function<bool(const BinaryData&)> addressFilter_;
   };

   struct ZcActionStruct
   {
      ZcAction action_;
      map<BinaryData, Tx> zcMap_;

      void setData(map<BinaryData, Tx> zcmap)
      {
         zcMap_ = move(zcmap);
      }
   };

private:
   map<HashString, HashString>                  txHashToDBKey_; //<txHash, dbKey>
   map<HashString, Tx>                          txMap_; //<zcKey, zcTx>
   map<HashString, map<BinaryData, TxIOPair> >  txioMap_; //<scrAddr,  <dbKeyOfOutput, TxIOPair>>
   map<HashString, vector<HashString> >         keyToSpentScrAddr_; //<zcKey, vector<ScrAddr>>
   set<HashString>                              txOutsSpentByZC_;     //<txOutDbKeys>
   set<HashString>                              allZcTxHashes_;
   map<BinaryData, map<unsigned, BinaryData>>   outPointsSpentByKey_; //<txHash, map<opId, ZcKeys>>

   BinaryData lastParsedBlockHash_;

   std::atomic<uint32_t> topId_;

   LMDBBlockDatabase* db_;

   static map<BinaryData, TxIOPair> emptyTxioMap_;
   bool enabled_ = false;

   vector<BinaryData> emptyVecBinData_;

   //stacks inv tx packets from node
   shared_ptr<BitcoinP2P> networkNode_;
   Stack<promise<InvEntry>> newInvTxStack_;
   
   TransactionalMap<string, BDV_Callbacks> bdvCallbacks_;
   TransactionalMap<BinaryData, shared_ptr<promise<bool>>> waitOnZcMap_;

private:
   BinaryData getNewZCkey(void);   
   BulkFilterData ZCisMineBulkFilter(const Tx & tx,
      const BinaryData& ZCkey,
      uint32_t txtime);

   void loadZeroConfMempool(bool clearMempool);
   set<BinaryData> purge(void);

public:
   //stacks new zc Tx objects from node
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

   const map<HashString, map<BinaryData, TxIOPair> >&
      getFullTxioMap(void) const { return txioMap_; }

   void dropZC(const set<BinaryData>& txHashes);
   void parseNewZC(void);
   bool isTxOutSpentByZC(const BinaryData& dbKey) const;
   bool getKeyForTxHash(const BinaryData& txHash, BinaryData& zcKey) const;

   void clear(void);

   map<BinaryData, TxIOPair> getZCforScrAddr(BinaryData scrAddr) const;
   const vector<BinaryData>& getSpentSAforZCKey(const BinaryData& zcKey) const;

   void updateZCinDB(
      const vector<BinaryData>& keysToWrite, const vector<BinaryData>& keysToDel);

   void processInvTxVec(vector<InvEntry>);
   void processInvTxThread(void);

   void init(function<bool(const BinaryData&)>, bool clearMempool);

   void insertBDVcallback(string, BDV_Callbacks);

   void broadcastZC(const BinaryData& rawzc, uint32_t timeout_sec = 3);
};

#endif
// kate: indent-width 3; replace-tabs on;
