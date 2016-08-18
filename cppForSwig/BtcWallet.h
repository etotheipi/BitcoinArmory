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
#ifndef _BTCWALLET_H
#define _BTCWALLET_H

#include "BinaryData.h"
#include "BlockObj.h"
#include "ScrAddrObj.h"
#include "StoredBlockObj.h"
#include "bdmenums.h"

class BlockDataManager;
class BlockDataViewer;

struct ScanWalletStruct
{
   BDV_Action action_;
   
   unsigned startBlock_;
   unsigned endBlock_ = UINT32_MAX;
   bool reorg_ = false;

   ScanAddressStruct saStruct_;
};

////////////////////////////////////////////////////////////////////////////////
class AddressBookEntry
{
public:

   /////
   AddressBookEntry(void) : scrAddr_(BtcUtils::EmptyHash()) { txList_.clear(); }
   explicit AddressBookEntry(BinaryData scraddr) : scrAddr_(scraddr) { txList_.clear(); }
   void addTx(Tx & tx) { txList_.push_back( tx ); }
   BinaryData getScrAddr(void) { return scrAddr_; }

   /////
   vector<Tx> getTxList(void)
   { 
      //sort(txList_.begin(), txList_.end()); 
      return txList_;
   }

   /////
   bool operator<(AddressBookEntry const & abe2) const
   {
      // If one of the entries has no tx (this shouldn't happen), sort by hash
      //if( txList_.size()==0 || abe2.txList_.size()==0)
         return scrAddr_ < abe2.scrAddr_;

      //return (txList_[0] < abe2.txList_[0]);
   }

private:
   BinaryData scrAddr_;
   vector<Tx> txList_;
};

////////////////////////////////////////////////////////////////////////////////
//
// BtcWallet
//
////////////////////////////////////////////////////////////////////////////////
class BtcWallet
{
   friend class WalletGroup;

   static const uint32_t MIN_UTXO_PER_TXN = 100;

private:

   class AddressMap
   {
      shared_ptr<map<BinaryData, shared_ptr<ScrAddrObj>>> addrMap_;
      mutex mergeLock_;

      AddressMap& operator=(const AddressMap&) = delete;

   public:

      AddressMap()
      {
         addrMap_ = make_shared<map<BinaryData, shared_ptr<ScrAddrObj>>>();
      }

      const shared_ptr<map<BinaryData, shared_ptr<ScrAddrObj>>>
         getAddrMap(void) const
      {
         return addrMap_;
      }

      void mergeScrAddrMap(
         const map<BinaryData, shared_ptr<ScrAddrObj>>& scrAddrMap)
      {
         auto newAddrMap =
            make_shared<map<BinaryData, shared_ptr<ScrAddrObj>>>();


         {
            unique_lock<mutex> lock(mergeLock_);

            *newAddrMap = *addrMap_;
         }

         newAddrMap->insert(scrAddrMap.begin(), scrAddrMap.end());

         addrMap_ = newAddrMap;
      }

      void deleteScrAddrVector(const vector<BinaryData>& saVec)
      {
         auto newAddrMap =
            make_shared<map<BinaryData, shared_ptr<ScrAddrObj>>>();

         unique_lock<mutex> lock(mergeLock_);

         *newAddrMap = *addrMap_;
         for (auto& sa : saVec)
            newAddrMap->erase(sa);

         addrMap_ = newAddrMap;
      }
   };

public:

   BtcWallet(BlockDataViewer* bdv, BinaryData ID)
      : bdvPtr_(bdv), walletID_(ID)
   {}

   ~BtcWallet(void)
   {}

   BtcWallet(const BtcWallet& wlt) = delete;

   /////////////////////////////////////////////////////////////////////////////
   // addScrAddr when blockchain rescan req'd, addNewScrAddr for just-created
   void addScrAddress(const BinaryData& addr);
   void removeAddressBulk(vector<BinaryData> const & scrAddrBulk);

   bool hasScrAddress(BinaryData const & scrAddr) const;


   // Scan a Tx for our TxIns/TxOuts.  Override default blk vals if you think
   // you will save time by not checking addresses that are much newer than
   // the block

   void scanNonStdTx(uint32_t    blknum, 
                     uint32_t    txidx, 
                     Tx &        txref,
                     uint32_t    txoutidx,
                     ScrAddrObj& addr);

   // BlkNum is necessary for "unconfirmed" list, since it is dependent
   // on number of confirmations.  But for "spendable" TxOut list, it is
   // only a convenience, if you want to be able to calculate numConf from
   // the Utxos in the list.  If you don't care (i.e. you only want to 
   // know what TxOuts are available to spend, you can pass in 0 for currBlk
   uint64_t getFullBalance(void) const;
   uint64_t getFullBalanceFromDB(void) const;
   uint64_t getSpendableBalance(uint32_t currBlk = 0,
                                bool ignoreAllZeroConf=true) const;
   uint64_t getUnconfirmedBalance(uint32_t currBlk,
                                  bool includeAllZeroConf=true) const;

   map<BinaryData, uint32_t> getAddrTxnCounts(uint32_t updateID) const;
   map<BinaryData, tuple<uint64_t, uint64_t, uint64_t>> 
      getAddrBalances(uint32_t updateID) const;

   uint64_t getWltTotalTxnCount(void) const;

   void prepareTxOutHistory(uint64_t val, bool ignoreZC);
   void prepareFullTxOutHistory(bool ignoreZC);
   vector<UnspentTxOut> getSpendableTxOutListForValue(uint64_t val = UINT64_MAX,
      bool ignoreZC = true);

   vector<LedgerEntry>
      getTxLedger(BinaryData const &scrAddr) const;
   vector<LedgerEntry>
      getTxLedger(void) const;

   void pprintLedger() const;
   void pprintAlot(LMDBBlockDatabase *db, uint32_t topBlk=0, bool withAddr=false) const;
   void pprintAlittle(std::ostream &os) const;
   
   void clearBlkData(void);
   
   vector<AddressBookEntry> createAddressBook(void) const;

   void reset(void);
   
   const ScrAddrObj* getScrAddrObjByKey(const BinaryData& key) const;
   ScrAddrObj& getScrAddrObjRef(const BinaryData& key);

   const LedgerEntry& getLedgerEntryForTx(const BinaryData& txHash) const;

   void setWalletID(BinaryData const & wltId) { walletID_ = wltId; }
   const BinaryData& walletID() const { return walletID_; }

   const map<BinaryData, LedgerEntry>& getHistoryPage(uint32_t);
   vector<LedgerEntry> getHistoryPageAsVector(uint32_t);
   size_t getHistoryPageCount(void) const { return histPages_.getPageCount(); }

   void needsRefresh(bool refresh);
   bool hasBdvPtr(void) const { return bdvPtr_ != nullptr; }

   void setRegistrationCallback(function<void(void)> lbd)
   {
      doneRegisteringCallback_ = lbd;
   }

private:   
   
   //returns true on bootstrap and new block, false on ZC
   bool scanWallet(const ScanWalletStruct&, uint32_t);

   //wallet side reorg processing
   void updateAfterReorg(uint32_t lastValidBlockHeight);
   void scanWalletZeroConf(const ScanWalletStruct&, uint32_t);

   void setRegistered(bool isTrue = true) { isRegistered_ = isTrue; }

   void updateWalletLedgersFromTxio(map<BinaryData, LedgerEntry>& le,
      const map<BinaryData, TxIOPair>& txioMap,
      uint32_t startBlock, uint32_t endBlock,
      bool purge = false) const;

   void mapPages(void);
   bool isPaged(void) const;

   BlockDataViewer* getBdvPtr(void) const
   { return bdvPtr_; }

   map<uint32_t, uint32_t> computeScrAddrMapHistSummary(void);
   const map<uint32_t, uint32_t>& getSSHSummary(void) const
   { return histPages_.getSSHsummary(); }

   void getTxioForRange(uint32_t, uint32_t, 
      map<BinaryData, TxIOPair>&) const;
   void unregister(void) { isRegistered_ = false; }
   void resetTxOutHistory(void);

private:

   BlockDataViewer* const        bdvPtr_;
   AddressMap                    scrAddrMap_;
   
   bool                          ignoreLastScanned_=true;
   map<BinaryData, LedgerEntry>* ledgerAllAddr_ = &LedgerEntry::EmptyLedgerMap_;
                                 
   bool                          isRegistered_=false;
   
   //manages history pages
   HistoryPager                  histPages_;

   //wallet id
   BinaryData                    walletID_;

   uint64_t                      balance_ = 0;

   //set to true to add wallet paged history to global ledgers 
   bool                          uiFilter_ = true;

   //call this lambda once a wallet is done registering and scanning 
   //for the first time
   function<void(void)> doneRegisteringCallback_ = [](void)->void{};

   set<BinaryData> validZcKeys_;

   mutable unsigned lastPulledCountsID_ = 0;
   mutable unsigned lastPulledBalancesID_ = 0;
};

#endif
// kate: indent-width 3; replace-tabs on;
