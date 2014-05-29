#ifndef _BTCWALLET_H
#define _BTCWALLET_H

#include "BinaryData.h"
#include "BlockObj.h"
#include "ScrAddrObj.h"
#include "StoredBlockObj.h"
#include "ThreadSafeContainer.h"

class BlockDataManager_LevelDB;

typedef map<BinaryData, RegisteredScrAddr> rsaMap;
typedef ts_pair_container<rsaMap> ts_rsaMap;

typedef map<BinaryData, ScrAddrObj> saMap;
typedef ts_pair_container<saMap> ts_saMap;


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
public:
   BtcWallet(BlockDataManager_LevelDB* bdm)
      : bdmPtr_(bdm),
      allScannedUpToBlk_(0), 
      lastScanned_(0),
      ignoreLastScanned_(true),
      isInitialized_(false)
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
   pair<bool,bool> isMineBulkFilter( Tx & tx,   
                                     bool withMultiSig=false) const;
   pair<bool,bool> isMineBulkFilter( Tx & tx, 
                                     map<OutPoint, TxIOPair> const & txiomap,
                                     bool withMultiSig=false) const;

   void scanTx(Tx & tx, 
               uint32_t txIndex = UINT32_MAX,
               uint32_t blktime = UINT32_MAX,
               uint32_t blknum  = UINT32_MAX);

   void scanNonStdTx(uint32_t    blknum, 
                     uint32_t    txidx, 
                     Tx &        txref,
                     uint32_t    txoutidx,
                     ScrAddrObj& addr);

   LedgerEntry calcLedgerEntryForTx(Tx & tx);
   LedgerEntry calcLedgerEntryForTx(TxRef & txref);
   LedgerEntry calcLedgerEntryForTxStr(BinaryData txStr);

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


   vector<UnspentTxOut> getFullTxOutList(uint32_t currBlk=0);
   vector<UnspentTxOut> getSpendableTxOutList(
      uint32_t currBlk=0,
      bool ignoreAllZeroConf=false
   ) const;
   void clearZeroConfPool(void);

   const ScrAddrObj& getScrAddrObjByKey(BinaryData const & a) const
   {
      const ts_saMap::const_snapshot saSnapshot(scrAddrMap_);
      const ts_saMap::const_iterator i = saSnapshot.find(a);
      
      if (i == saSnapshot.end())
         throw std::runtime_error("Could not find ScrAddrObject with key=" + a.toHexStr());
      return i->second;
   }

   uint32_t removeInvalidEntries(void);

   const vector<LedgerEntry> 
      getZeroConfLedger(BinaryData const * scrAddr = nullptr) const;
   vector<LedgerEntry> 
      getTxLedger(BinaryData const * scrAddr=nullptr) const; 

   bool isOutPointMine(BinaryData const & hsh, uint32_t idx);

   void pprintLedger() const;
   void pprintAlot(InterfaceToLDB *db, uint32_t topBlk=0, bool withAddr=false) const;
   void pprintAlittle(std::ostream &os) const;

   void clearBlkData(void);
   
   vector<AddressBookEntry> createAddressBook(void);

   //for 1:1 wallets
   bool registerNewScrAddr(HashString scraddr);
   bool registerImportedScrAddr(HashString scraddr, uint32_t createBlk);

   void insertRegisteredTxIfNew(RegisteredTx & regTx)
   {
      // .insert() function returns pair<iter,bool> with bool true if inserted
      if(registeredTxSet_.insert(regTx.getTxHash()).second == true)
         registeredTxList_.push_back(regTx);
   }
   vector<TxIOPair> getHistoryForScrAddr(
      BinaryDataRef uniqKey, 
      bool withMultisig=false
   ) const;

   void registerOutPoint(const OutPoint &op) {registeredOutPoints_.insert(op);}
   int  countOutPoints(const OutPoint &op) const {return registeredOutPoints_.count(op);}
   void insertRegisteredTxIfNew(HashString txHash);
   bool scrAddrIsRegistered(HashString scraddr) const
   {
      ts_rsaMap::const_snapshot rsaSS(registeredScrAddrMap_);
      return rsaSS.find(scraddr) != rsaSS.end();
   }
   void scanRegisteredTxList( uint32_t blkStart, uint32_t blkEnd);
   void updateRegisteredScrAddrs(uint32_t newTopBlk);
   uint32_t numBlocksToRescan(uint32_t endBlk) const;
   const RegisteredScrAddr& getRegisteredScrAddr(const BinaryData& uniqKey) const
   {
      const ts_rsaMap::const_snapshot rsaMap_snapshot(registeredScrAddrMap_);
      const ts_rsaMap::const_iterator rsaMap_iter = rsaMap_snapshot.find(uniqKey);
      
      if (rsaMap_iter == rsaMap_snapshot.end())
         throw std::runtime_error("Could not find RegisteredScrAddr with key=" + uniqKey.toHexStr());
      return rsaMap_iter->second;
   }
   ts_rsaMap* getRegisteredScrAddrMap(void)
         { return &registeredScrAddrMap_; }
   void eraseTx(const BinaryData& txHash);
   vector<LedgerEntry> & getTxLedgerForComments(void)
                     { return txLedgerForComments_; }
   void reorgChangeBlkNum(uint32_t blkNum);
   void setIgnoreLastScanned(void) {ignoreLastScanned_ = true;}
   
   //new all purpose wallet scanning call
   void scanWallet(uint32_t startBlock=UINT32_MAX, 
                   uint32_t endBlock=UINT32_MAX,
                   bool forceRescan=false);
   
   //wallet side reorg processing
   void updateAfterReorg(uint32_t lastValidBlockHeight);

   void scanBlocksAgainstRegisteredScrAddr(uint32_t blk0, 
                                           uint32_t blk1 = UINT32_MAX);
   
   void registeredScrAddrScan(Tx & theTx);
   void registeredScrAddrScan(uint8_t const * txptr,
      uint32_t txSize = 0,
      vector<uint32_t> * txInOffsets = NULL,
      vector<uint32_t> * txOutOffsets = NULL);

   bool removeRegisteredTx(BinaryData const & txHash);
   void rescanWalletZeroConf(void);
   uint32_t evalLowestBlockNextScan() const;
   
   //saving scrAddr data to the DB from wallet side
   void saveScrAddrHistories(void);

   //end of 1:1 wallets
   
   uint32_t getNumScrAddr(void) const { return scrAddrMap_.size(); }
   void fetchDBRegisteredScrAddrData(void);
   void fetchDBRegisteredScrAddrData(BinaryData const & scrAddr);


private:
   vector<LedgerEntry> & getEmptyLedger(void) { EmptyLedger_.clear(); return EmptyLedger_;}
   void sortLedger();

private:
   BlockDataManager_LevelDB*const     bdmPtr_;
   ts_saMap                           scrAddrMap_;
   map<OutPoint, TxIOPair>            txioMap_;

   //for 1:1 wallets
   ts_rsaMap                          registeredScrAddrMap_;

   list<RegisteredTx>                 registeredTxList_;
   set<HashString>                    registeredTxSet_;
   set<OutPoint>                      registeredOutPoints_;
   uint32_t                           allScannedUpToBlk_; // one past top
   uint32_t                           lastScanned_;
   bool                               ignoreLastScanned_;

   vector<LedgerEntry>          ledgerAllAddr_;  
   vector<LedgerEntry>          ledgerAllAddrZC_;  
   vector<LedgerEntry>          txLedgerForComments_;

   // For non-std transactions
   map<OutPoint, TxIOPair>      nonStdTxioMap_;
   set<OutPoint>                nonStdUnspentOutPoints_;

   static vector<LedgerEntry>   EmptyLedger_; // just a null-reference object

   //marks if the DB was scanned against registeredScrAddrMap, to fill its
   //registeredTxList with existing data
   bool                         isInitialized_;
   
   BtcWallet(const BtcWallet&); // no copies
};

#endif
// kate: indent-width 3; replace-tabs on;
