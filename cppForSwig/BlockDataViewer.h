#ifndef BLOCK_DATA_VIEWER_H
#define BLOCK_DATA_VIEWER_H

#include <stdint.h>
#include <string>

using namespace std;

#include "BlockUtils.h"
#include "BDM_supportClasses.h"

class BlockDataViewer
{
   public:
      BlockDataViewer(BlockDataManager_LevelDB* bdm);
      ~BlockDataViewer(void);
   
      /////////////////////////////////////////////////////////////////////////////
      // If you register you wallet with the BDM, it will automatically maintain 
      // tx lists relevant to that wallet.  You can get away without registering
      // your wallet objects (using scanBlockchainForTx), but without the full 
      // blockchain in RAM, each scan will take 30-120 seconds.  Registering makes 
      // sure that the intial blockchain scan picks up wallet-relevant stuff as 
      // it goes, and does a full [re-]scan of the blockchain only if necessary.
      bool     registerWallet(BtcWallet* wallet, bool wltIsNew = false);
      bool     registerLockbox(BtcWallet* wallet, bool wltIsNew = false);
      void     unregisterWallet(BtcWallet* wltPtr);
      void     unregisterLockbox(BtcWallet* wltPtr);

      void scanWallets(uint32_t startBlock = UINT32_MAX,
         uint32_t endBlock = UINT32_MAX, uint32_t forceRefresh = 0);
      
      bool hasWallet(BtcWallet* wltPtr);

      bool registerAddresses(const vector<BinaryData>& saVec, 
                             BtcWallet* wltPtr, bool isNew);

      map<BinaryData, map<BinaryData, TxIOPair> >
         getNewZeroConfTxIOMap()
      { return zeroConfCont_.getNewTxioMap(); }

      const map<BinaryData, map<BinaryData, TxIOPair> >&
         getFullZeroConfTxIOMap() const
      { return zeroConfCont_.getFullTxioMap(); }

      set<BinaryData> getNewZCTxHash(void) const
      { return zeroConfCont_.getNewZCByHash(); }

      const LedgerEntry& getTxLedgerByHash(const BinaryData& txHash) const;
      
      void pprintRegisteredWallets(void) const;

      void enableZeroConf(string filename, bool zcLite = true);
      void disableZeroConf(void);
      void readZeroConfFile(string filename);
      void addNewZeroConfTx(BinaryData const & rawTx, uint32_t txtime,
         bool writeToFile);
      void purgeZeroConfPool(void);
      void pprintZeroConfPool(void) const;
      void rewriteZeroConfFile(void);
      bool isZcEnabled() { return zcEnabled_; }
      bool parseNewZeroConfTx(void);

      TX_AVAILABILITY   getTxHashAvail(BinaryDataRef txhash);
      Tx                getTxByHash(BinaryData const & txHash);
      TxOut             getPrevTxOut(TxIn & txin);
      Tx                getPrevTx(TxIn & txin);

      BinaryData        getSenderScrAddr(TxIn & txin);
      int64_t           getSentValue(TxIn & txin);

      LMDBBlockDatabase* getDB(void) const;
      Blockchain& blockchain(void) const;
      uint32_t getTopBlockHeight(void) const;

      void reset();

      void pageWalletsHistory(bool forcePaging = true);
      void pageLockboxesHistory();

      map<uint32_t, uint32_t> computeWalletsSSHSummary(bool forcePaging = true);
      const vector<LedgerEntry>& getHistoryPage(uint32_t, 
                                                bool rebuildLedger = false, 
                                                bool remapWallets = false);
      size_t getPageCount(void) const { return hist_.getPageCount(); }

      void scanScrAddrVector(const map<BinaryData, ScrAddrObj>& scrAddrMap, 
                             uint32_t startBlock, uint32_t endBlock) const;

      void flagRefresh(bool withRemap, BinaryData refreshId);

      void updateWalletFilters(vector<string> walletsVec);

   public:
      bool rescanZC_    = false;
      uint32_t refresh_ = 0;

      //extra arg for refresh notifications
      BinaryData            refreshID_;

   private:
      BlockDataManager_LevelDB* bdmPtr_;
      LMDBBlockDatabase*        db_;
      Blockchain*               bc_;
      ScrAddrFilter*            saf_;

      set<BtcWallet*> registeredWallets_;
      set<BtcWallet*> registeredLockboxes_;
      ZeroConfContainer zeroConfCont_;
      
      bool     zcEnabled_;
      bool     zcLiteMode_;
      string   zcFilename_;

      uint32_t lastScanned_ = 0;
      bool initialized_ = false;

      //The globalLedger (used to render the main transaction ledger) is
      //different from wallet ledgers. While each wallet only has a single
      //entry per transactions (wallets merge all of their scrAddr txn into
      //a single one), the globalLedger does not merge wallet level txn. It
      //can thus have several entries under the same transaction, and cannot
      //be a map.
      vector<LedgerEntry> globalLedger_;
      HistoryPager hist_;

      //UI wallet filter
      map<BinaryData, bool> walletFilters_;
};

#endif