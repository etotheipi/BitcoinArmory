#ifndef _BDM_SUPPORTCLASSES_H_
#define _BDM_SUPPORTCLASSES_H_

#include <vector>
#include <atomic>

#include "BinaryData.h"
#include "ScrAddrObj.h"
#include "BtcWallet.h"

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
      map<BinaryData, ScrAddrMeta>::iterator scrAddrIter =
         scrAddrMap_.find(scrAddr);
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
   {
      return scrAddrMap_.size();
   }

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
   {
      return (scrAddrMap_.find(sa) != scrAddrMap_.end());
   }

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
   {
      return UTxO_.erase(dbkey) == 1;
   }

   void getScrAddrCurrentSyncState();
   void getScrAddrCurrentSyncState(BinaryData const & scrAddr);

   map<BinaryData, map<BinaryData, TxIOPair> >
      ZCisMineBulkFilter(const Tx & tx,
      const BinaryData& ZCkey, InterfaceToLDB *db,
      uint32_t txtime,
      const ZeroConfContainer *zcd,
      bool withSecondOrderMultisig = true) const;

   void setSSHLastScanned(InterfaceToLDB *db, uint32_t height);

   void regScrAddrForScan(const BinaryData& scrAddr, uint32_t scanFrom,
      BtcWallet* wltPtr)
   {
      scrAddrMap_[scrAddr] = ScrAddrMeta(scanFrom, wltPtr);
   }

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
   bool                        parsing_;

   //newZCmap_ is ephemeral. Raw ZC are saved until they are processed.
   //The code has a thread pushing new ZC, and set the BDM thread flag
   //to parse it
   map<BinaryData, Tx> newZCMap_;

   //newTxioMap_ is ephemeral too. It's contains ZC txios that have not been
   //seen by the scrAddrObj. It's content is returned then wiped by each call
   //to getNewTxioMap
   map<HashString, map<BinaryData, TxIOPair> >  newTxioMap_;


   BinaryData getNewZCkey(void);
   bool RemoveTxByKey(const BinaryData key);
   bool RemoveTxByHash(const BinaryData txHash);

public:
   ZeroConfContainer(ScrAddrScanData* sadPtr) :
      scrAddrDataPtr_(sadPtr), topId_(0), lock_(0) {}

   void addRawTx(const BinaryData& rawTx, uint32_t txtime);

   bool hasTxByHash(const BinaryData& txHash) const;
   bool getTxByHash(const BinaryData& txHash, Tx& tx) const;

   map<BinaryData, vector<BinaryData> > purge(InterfaceToLDB *db);

   map<HashString, map<BinaryData, TxIOPair> > getNewTxioMap(void);
   const map<HashString, map<BinaryData, TxIOPair> >&
      getFullTxioMap(void) const { return txioMap_; }


   bool parseNewZC(InterfaceToLDB* db);
   //bool setNewZC(void);
   //bool hasNewZC(void);

   bool getKeyForTxHash(const BinaryData& txHash, BinaryData zcKey) const;
};

#endif
