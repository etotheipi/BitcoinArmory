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

#ifndef BLOCK_DATA_VIEWER_H
#define BLOCK_DATA_VIEWER_H

#include <stdint.h>
#include <string>

using namespace std;

#include "BlockUtils.h"
#include "txio.h"
#include "BDM_supportClasses.h"
#include "util.h"
#include "bdmenums.h"

typedef enum
{
   order_ascending,
   order_descending
}HistoryOrdering;


typedef enum
{
   group_wallet,
   group_lockbox
}LedgerGroups;

class WalletGroup;

class BDMnotReady : public exception
{
   virtual const char* what() const throw()
   {
      return "BDM is not ready!";
   }
};

class BlockDataViewer
{
private:
   virtual void pushNotification(unique_ptr<BDV_Notification>) = 0;

protected:
   unique_ptr<BDV_Notification_ZC> createZcStruct(void);

public:
   BlockDataViewer(BlockDataManager* bdm);
   ~BlockDataViewer(void);

   /////////////////////////////////////////////////////////////////////////////
   // If you register you wallet with the BDM, it will automatically maintain 
   // tx lists relevant to that wallet.  You can get away without registering
   // your wallet objects (using scanBlockchainForTx), but without the full 
   // blockchain in RAM, each scan will take 30-120 seconds.  Registering makes 
   // sure that the intial blockchain scan picks up wallet-relevant stuff as 
   // it goes, and does a full [re-]scan of the blockchain only if necessary.
   shared_ptr<BtcWallet> createWallet(const string& id);
   shared_ptr<BtcWallet> createLockbox(const string& id);

   shared_ptr<BtcWallet> registerWallet(vector<BinaryData> const& scrAddrVec,
                              string ID, bool wltIsNew);
   shared_ptr<BtcWallet> registerLockbox(vector<BinaryData> const& scrAddrVec, 
                              string ID, bool wltIsNew);
   void       unregisterWallet(const string& ID);
   void       unregisterLockbox(const string& ID);

   void scanWallets(shared_ptr<BDV_Notification>);
   
   bool hasWallet(const BinaryData& ID) const;

   bool registerAddresses(const vector<BinaryData>& saVec, 
                           const string& walletID, bool areNew);
   void registerArbitraryAddressVec(const vector<BinaryData>& saVec,
      const string& walletID);

   const shared_ptr<map<BinaryData, shared_ptr<map<BinaryData, TxIOPair>>>>
      getFullZeroConfTxIOMap() const
   { return zeroConfCont_->getFullTxioMap(); }

   const LedgerEntry& getTxLedgerByHash_FromWallets(
      const BinaryData& txHash) const;
   const LedgerEntry& getTxLedgerByHash_FromLockboxes(
      const BinaryData& txHash) const;

   Tx                getTxByHash(BinaryData const & txHash) const;
   TxOut             getPrevTxOut(TxIn & txin) const;
   Tx                getPrevTx(TxIn & txin) const;

   BinaryData        getTxHashForDbKey(const BinaryData& dbKey6) const
   { return db_->getTxHashForLdbKey(dbKey6); }
   
   bool isTxMainBranch(const Tx &tx) const;

   BinaryData        getSenderScrAddr(TxIn & txin) const;
   int64_t           getSentValue(TxIn & txin) const;

   LMDBBlockDatabase* getDB(void) const;
   const Blockchain& blockchain() const  { return *bc_; }
   Blockchain& blockchain() { return *bc_; }
   uint32_t getTopBlockHeight(void) const;
   const shared_ptr<BlockHeader> getTopBlockHeader(void) const
   { return bc_->top(); }
   shared_ptr<BlockHeader> getHeaderByHash(const BinaryData& blockHash) const;

   void reset();

   size_t getWalletsPageCount(void) const;
   vector<LedgerEntry> getWalletsHistoryPage(uint32_t, 
                                             bool rebuildLedger, 
                                             bool remapWallets);

   size_t getLockboxesPageCount(void) const;
   vector<LedgerEntry> getLockboxesHistoryPage(uint32_t,
      bool rebuildLedger,
      bool remapWallets);

   void scanScrAddrVector(const map<BinaryData, ScrAddrObj>& scrAddrMap, 
                           uint32_t startBlock, uint32_t endBlock) const;

   void flagRefresh(BDV_refresh refresh, const BinaryData& refreshId);

   StoredHeader getMainBlockFromDB(uint32_t height) const;
   StoredHeader getBlockFromDB(uint32_t height, uint8_t dupID) const;
   bool scrAddressIsRegistered(const BinaryData& scrAddr) const;
   
   const shared_ptr<BlockHeader> getHeaderPtrForTx(Tx& theTx) const
      { return bc_->getHeaderPtrForTx(theTx); }

   vector<UnspentTxOut> 
      getUnspentTxoutsForAddr160List(
      const vector<BinaryData>&, bool ignoreZc) const;

   bool isBDMRunning(void) const 
   { 
      if (bdmPtr_ == nullptr)
         return false;
      return bdmPtr_->isRunning(); 
   }

   void blockUntilBDMisReady(void) const
   {
      if (bdmPtr_ == nullptr)
         throw runtime_error("no bdmPtr_");
      bdmPtr_->blockUntilReady();
   }

   bool isTxOutSpentByZC(const BinaryData& dbKey) const
   { return zeroConfCont_->isTxOutSpentByZC(dbKey); }

   map<BinaryData, TxIOPair> getUnspentZCForScrAddr(
      const BinaryData& scrAddr) const
   { return zeroConfCont_->getUnspentZCforScrAddr(scrAddr); }

   map<BinaryData, TxIOPair> getRBFTxIOsforScrAddr(
      const BinaryData& scrAddr) const
   {
      return zeroConfCont_->getRBFTxIOsforScrAddr(scrAddr);
   }

   vector<TxOut> getZcTxOutsForKeys(const set<BinaryData>& keys) const
   {
      return zeroConfCont_->getZcTxOutsForKey(keys);
   }

   const set<BinaryData>& getSpentSAforZCKey(const BinaryData& zcKey) const
   { return zeroConfCont_->getSpentSAforZCKey(zcKey); }

   ScrAddrFilter* getSAF(void) { return saf_; }
   const BlockDataManagerConfig& config() const { return bdmPtr_->config(); }

   WalletGroup getStandAloneWalletGroup(
      const vector<BinaryData>& wltIDs, HistoryOrdering order);

   void updateWalletsLedgerFilter(const vector<BinaryData>& walletsList);
   void updateLockboxesLedgerFilter(const vector<BinaryData>& walletsList);

   uint32_t getBlockTimeByHeight(uint32_t) const;
   uint32_t getClosestBlockHeightForTime(uint32_t);
   
   LedgerDelegate getLedgerDelegateForWallets();
   LedgerDelegate getLedgerDelegateForLockboxes();
   LedgerDelegate getLedgerDelegateForScrAddr(
      const BinaryData& wltID, const BinaryData& scrAddr);

   TxOut getTxOutCopy(const BinaryData& txHash, uint16_t index) const;
   TxOut getTxOutCopy(const BinaryData& dbKey) const;

   Tx getSpenderTxForTxOut(uint32_t height, uint32_t txindex, uint16_t txoutid) const;

   bool isZcEnabled() const { return bdmPtr_->isZcEnabled(); }

   void flagRescanZC(bool flag)
   { rescanZC_.store(flag, memory_order_release); }

   bool getZCflag(void) const
   { return rescanZC_.load(memory_order_acquire); }

   bool isRBF(const BinaryData& txHash) const;
   bool hasScrAddress(const BinaryData& sa) const;

   shared_ptr<BtcWallet> getWalletOrLockbox(const BinaryData& id) const;

   tuple<uint64_t, uint64_t> getAddrFullBalance(const BinaryData&);

protected:
   atomic<bool> rescanZC_;

   BlockDataManager* bdmPtr_ = nullptr;
   LMDBBlockDatabase*        db_;
   shared_ptr<Blockchain>    bc_;
   ScrAddrFilter*            saf_;

   //Wanna keep the BtcWallet non copyable so the only existing object for
   //a given wallet is in the registered* map. Don't want to save pointers
   //to avoid cleanup snafus. Time for smart pointers

   vector<WalletGroup> groups_;
   
   uint32_t lastScanned_ = 0;
   const shared_ptr<ZeroConfContainer> zeroConfCont_;

   int32_t updateID_ = 0;
};


class WalletGroup
{
   friend class BlockDataViewer;
   friend class BDV_Server_Object;

public:

   WalletGroup(BlockDataViewer* bdvPtr, ScrAddrFilter* saf) :
      bdvPtr_(bdvPtr), saf_(saf)
   {}

   WalletGroup(const WalletGroup& wg)
   {
      this->bdvPtr_ = wg.bdvPtr_;
      this->saf_ = wg.saf_;

      this->hist_ = wg.hist_;
      this->order_ = wg.order_;

      ReadWriteLock::ReadLock rl(this->lock_);
      this->wallets_ = wg.wallets_;
   }

   ~WalletGroup();

   shared_ptr<BtcWallet> registerWallet(
      vector<BinaryData> const& scrAddrVec, string IDstr, bool wltIsNew);
   void unregisterWallet(const string& IDstr);
   bool registerAddresses(const vector<BinaryData>& saVec,
      const string& walletID, bool areNew);

   bool hasID(const BinaryData& ID) const;
   shared_ptr<BtcWallet> getWalletByID(const BinaryData& ID) const;

   const LedgerEntry& getTxLedgerByHash(const BinaryData& txHash) const;

   void reset();
   
   size_t getPageCount(void) const { return hist_.getPageCount(); }
   vector<LedgerEntry> getHistoryPage(uint32_t pageId,
      bool rebuildLedger, bool remapWallets);

   const set<BinaryData>& getValidZcSet(void) const
   {
      return validZcSet_;
   }

private:   
   map<uint32_t, uint32_t> computeWalletsSSHSummary(
      bool forcePaging, bool pageAnyway);
   bool pageHistory(bool forcePaging, bool pageAnyway);
   void updateLedgerFilter(const vector<BinaryData>& walletsVec);

   void scanWallets(ScanWalletStruct&, int32_t);
   void updateGlobalLedgerFirstPage(uint32_t startBlock, 
      uint32_t endBlock, BDV_refresh forceRefresh);

   map<BinaryData, shared_ptr<BtcWallet> > getWalletMap(void) const;

   uint32_t getBlockInVicinity(uint32_t) const;
   uint32_t getPageIdForBlockHeight(uint32_t) const;

private:
   map<BinaryData, shared_ptr<BtcWallet> > wallets_;
   mutable ReadWriteLock lock_;

   //The globalLedger (used to render the main transaction ledger) is
   //different from wallet ledgers. While each wallet only has a single
   //entry per transactions (wallets merge all of their scrAddr txn into
   //a single one), the globalLedger does not merge wallet level txn. It
   //can thus have several entries under the same transaction. Thus, this
   //cannot be a map nor a set.
   vector<LedgerEntry> globalLedger_;
   HistoryPager hist_;
   HistoryOrdering order_ = order_descending;

   BlockDataViewer* bdvPtr_ = nullptr;
   ScrAddrFilter*   saf_;

   //the global ledger may be modified concurently by the maintenance thread
   //and user actions, so it needs a synchronization primitive.
   std::mutex globalLedgerLock_;

   set<BinaryData> validZcSet_;
};

#endif

// kate: indent-width 3; replace-tabs on;
