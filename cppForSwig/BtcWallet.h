#ifndef _BTCWALLET_H
#define _BTCWALLET_H

#include "BinaryData.h"
#include "BlockObj.h"
#include "ScrAddrObj.h"
#include "StoredBlockObj.h"

class BlockDataManager_LevelDB;
class BlockDataViewer;

////////////////////////////////////////////////////////////////////////////////
class AddressBookEntry
{
public:

   /////
   AddressBookEntry(void) : scrAddr_(BtcUtils::EmptyHash()) { txList_.clear(); }
   explicit AddressBookEntry(BinaryData scraddr) : scrAddr_(scraddr) { txList_.clear(); }
   void addTx(Tx & tx) { txList_.push_back( RegisteredTx(tx) ); }
   BinaryData getScrAddr(void) { return scrAddr_; }

   /////
   vector<RegisteredTx> getTxList(void)
   { 
      sort(txList_.begin(), txList_.end()); 
      return txList_;
   }

   /////
   bool operator<(AddressBookEntry const & abe2) const
   {
      // If one of the entries has no tx (this shouldn't happen), sort by hash
      if( txList_.size()==0 || abe2.txList_.size()==0)
         return scrAddr_ < abe2.scrAddr_;

      return (txList_[0] < abe2.txList_[0]);
   }

private:
   BinaryData scrAddr_;
   vector<RegisteredTx> txList_;
};

////////////////////////////////////////////////////////////////////////////////
//
// BtcWallet
//
////////////////////////////////////////////////////////////////////////////////
class BtcWallet
{
   friend class BlockDataViewer;

public:
   BtcWallet(BlockDataViewer* bdv)
      : bdvPtr_(bdv),
      mergeLock_(0)
   {}
   ~BtcWallet(void);

   /////////////////////////////////////////////////////////////////////////////
   // addScrAddr when blockchain rescan req'd, addNewScrAddr for just-created
   void addNewScrAddress(BinaryData addr);
   void addScrAddress(ScrAddrObj const & newAddr);
   void addScrAddress(BinaryData    addr, 
                   uint32_t      firstTimestamp = 0,
                   uint32_t      firstBlockNum  = 0,
                   uint32_t      lastTimestamp  = 0,
                   uint32_t      lastBlockNum   = 0);

   // SWIG has some serious problems with typemaps and variable arg lists
   // Here I just create some extra functions that sidestep all the problems
   // but it would be nice to figure out "typemap typecheck" in SWIG...
   void addScrAddress_ScrAddrObj_(ScrAddrObj const & newAddr);

   // Adds a new address that is assumed to be imported, and thus will
   // require a blockchain scan
   void addScrAddress_1_(BinaryData addr);

   // Adds a new address that we claim has never been seen until thos moment,
   // and thus there's no point in doing a blockchain rescan.
   void addNewScrAddress_1_(BinaryData addr) {addNewScrAddress(addr);}

   // Blockchain rescan will depend on the firstBlockNum input
   void addScrAddress_3_(BinaryData    addr, 
                      uint32_t      firstTimestamp,
                      uint32_t      firstBlockNum);

   // Blockchain rescan will depend on the firstBlockNum input
   void addScrAddress_5_(BinaryData    addr, 
                      uint32_t      firstTimestamp,
                      uint32_t      firstBlockNum,
                      uint32_t      lastTimestamp,
                      uint32_t      lastBlockNum);

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
   uint64_t getSpendableBalance(uint32_t currBlk=0, 
                                bool ignoreAllZeroConf=false) const;
   uint64_t getUnconfirmedBalance(uint32_t currBlk,
                                  bool includeAllZeroConf=false) const;

   uint64_t getAddrTotalTxnCount(const BinaryData& addr) const;

   vector<UnspentTxOut> getSpendableTxOutList(
      uint32_t currBlk=0,
      bool ignoreAllZeroConf=false
   ) const;

   vector<LedgerEntry>
      getTxLedger(BinaryData const &scrAddr) const;
   const vector<LedgerEntry>&
      getTxLedger() const; 

   void pprintLedger() const;
   void pprintAlot(LMDBBlockDatabase *db, uint32_t topBlk=0, bool withAddr=false) const;
   void pprintAlittle(std::ostream &os) const;

   void clearBlkData(void);
   
   vector<AddressBookEntry> createAddressBook(void) const;

   void reset(void);
   
   const map<BinaryData, ScrAddrObj>& getScrAddrMap(void) const
   { return scrAddrMap_; }

   map<BinaryData, ScrAddrObj>& getScrAddrMap(void)
   { return scrAddrMap_; }

   uint32_t getNumScrAddr(void) const { return scrAddrMap_.size(); }

   const ScrAddrObj* getScrAddrObjByKey(BinaryData key) const;

   LedgerEntry getLedgerEntryForTx(const BinaryData& txHash) const;
   void preloadScrAddr(const BinaryData& scrAddr);

   void setWalletID(string wltId) { walletID_ = wltId; }

   bool getMergeFlag(void) { return mergeFlag_; }

private:   
   
   //new all purpose wallet scanning call, returns true on bootstrap and new block,
   //false on ZC
   bool scanWallet(uint32_t startBlock,
      uint32_t endBlock,
      bool reorg = false);

   //wallet side reorg processing
   void updateAfterReorg(uint32_t lastValidBlockHeight);
   void scanWalletZeroConf(bool withReorg = false);

   void fetchDBScrAddrData(uint32_t startBlock, uint32_t endBlock);

   void setRegistered(bool isTrue = true) { isRegistered_ = isTrue; }
   void purgeZeroConfTxIO(
      const map<BinaryData, vector<BinaryData> >& invalidatedTxIO);

   void updateWalletLedgersFromScrAddr(vector<LedgerEntry>& le,
                            const map<BinaryData, ScrAddrObj>& scrAddrMap, 
                            uint32_t startBlock, uint32_t endBlock, 
                            bool purge = true);

   void updateWalletLedgersFromTxio(map<BinaryData, LedgerEntry>& le,
      const map<BinaryData, TxIOPair>& txioMap,
      uint32_t startBlock, uint32_t endBlock) const;

   void purgeLedgerFromHeight(uint32_t height);

   void merge(void);

   void mapPages(void);

   BlockDataViewer* getBdvPtr(void) const
   { return bdvPtr_; }

   map<uint32_t, uint32_t> computeScrAddrMapHistSummary(void);
   const map<uint32_t, uint32_t>& getSSHSummary(void) const
   { return histPages_.getSSHsummary(); }

   void getTxioForRange(uint32_t, uint32_t, 
      map<BinaryData, TxIOPair>&) const;

   void sortLedger();
   void unregister(void) { isRegistered_ = false; }

private:
   BlockDataViewer* const              bdvPtr_;
   map<BinaryData, ScrAddrObj>         scrAddrMap_;
   
   bool                                ignoreLastScanned_=true;
   vector<LedgerEntry>                 ledgerAllAddr_;
   
   // just a null-reference object
   static vector<LedgerEntry>          EmptyLedger_; 

   bool                                isRegistered_=false;

   BtcWallet(const BtcWallet&); // no copies

   //for post init importing of new addresses
   atomic<uint32_t>                    mergeLock_;
   map<BinaryData, ScrAddrObj>         scrAddrMapToMerge_;
   bool                                mergeFlag_=false;
   
   //manages history pages
   HistoryPager                        histPages_;

   //wallet id
   string                              walletID_;
};

#endif
// kate: indent-width 3; replace-tabs on;
