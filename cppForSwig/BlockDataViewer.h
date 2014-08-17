#ifndef BLOCK_DATA_VIEWER_H
#define BLOCK_DATA_VIEWER_H

#include <stdint.h>
#include <string>

using namespace std;

#include "BlockUtils.h"
#include "BDM_supportClasses.h"

/*class BlockDataManager_LevelDB;
class BinaryData;
class BinaryDataRef;
class BtcWallet;
class TxIn;
class TxOut;*/

class BlockDataViewer
{
   public:
      BlockDataViewer(BlockDataManager_LevelDB* bdm);
   
      /////////////////////////////////////////////////////////////////////////////
      // If you register you wallet with the BDM, it will automatically maintain 
      // tx lists relevant to that wallet.  You can get away without registering
      // your wallet objects (using scanBlockchainForTx), but without the full 
      // blockchain in RAM, each scan will take 30-120 seconds.  Registering makes 
      // sure that the intial blockchain scan picks up wallet-relevant stuff as 
      // it goes, and does a full [re-]scan of the blockchain only if necessary.
      bool     registerWallet(BtcWallet* wallet, bool wltIsNew = false);
      void     unregisterWallet(BtcWallet* wltPtr);

      void scanWallets(uint32_t startBlock = UINT32_MAX,
         uint32_t endBlock = UINT32_MAX);
      
      bool hasWallet(BtcWallet* wltPtr);

      bool registerScrAddr(const ScrAddrObj& sa, BtcWallet* wltPtr = nullptr);

      map<BinaryData, map<BinaryData, TxIOPair> >
         getNewZeroConfTxIOMap()
      { return zeroConfCont_.getNewTxioMap(); }

      const map<BinaryData, map<BinaryData, TxIOPair> >&
         getFullZeroConfTxIOMap() const
      { return zeroConfCont_.getFullTxioMap(); }

      set<BinaryData> getNewZCTxHash(void) const
      { return zeroConfCont_.getNewZCByHash(); }

      LedgerEntry getTxLedgerByHash(const BinaryData& txHash) const;
      
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

   public:
      bool     rescanZC_;

   private:
      LMDBBlockDatabase* db_;
      Blockchain*        bc_;
      ScrAddrFilter*     saf_;

      set<BtcWallet*> registeredWallets_;
      ZeroConfContainer zeroConfCont_;
      
      bool     zcEnabled_;
      bool     zcLiteMode_;
      string   zcFilename_;

      uint32_t lastScanned_;
};

#endif