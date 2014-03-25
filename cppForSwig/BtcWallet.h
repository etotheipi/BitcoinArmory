#ifndef _BTCWALLET_H
#define _BTCWALLET_H

#include "BinaryData.h"
#include "BlockObj.h"
#include "ScrAddrObj.h"

class BlockDataManager_LevelDB;

////////////////////////////////////////////////////////////////////////////////
class AddressBookEntry
{
public:

   /////
   AddressBookEntry(void) : scrAddr_(BtcUtils::EmptyHash_) { txList_.clear(); }
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
   BtcWallet(void) : bdmPtr_(NULL), lastScanned_(0) {}
   explicit BtcWallet(BlockDataManager_LevelDB* bdm)
      : bdmPtr_(bdm), lastScanned_(0) {}
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
               uint32_t blknum  = UINT32_MAX,
               bool mainwallet = true);

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
   uint64_t getFullBalance(void);
   uint64_t getSpendableBalance(uint32_t currBlk=0, 
                                bool ignoreAllZeroConf=false);
   uint64_t getUnconfirmedBalance(uint32_t currBlk,
                                  bool includeAllZeroConf=false);
   vector<UnspentTxOut> getFullTxOutList(uint32_t currBlk=0);
   vector<UnspentTxOut> getSpendableTxOutList(uint32_t currBlk=0,
                                              bool ignoreAllZeroConf=false);
   void clearZeroConfPool(void);

   
   uint32_t     getNumScrAddr(void) const {return scrAddrMap_.size();}
   ScrAddrObj & getScrAddrObjByIndex(uint32_t i) { return *(scrAddrPtrs_[i]); }
   ScrAddrObj & getScrAddrObjByKey(BinaryData const & a) { return scrAddrMap_[a];}

   void     sortLedger(void);
   uint32_t removeInvalidEntries(void);

   vector<LedgerEntry> &     getZeroConfLedger(BinaryData const * scrAddr=NULL);
   vector<LedgerEntry> &     getTxLedger(BinaryData const * scrAddr=NULL); 
   map<OutPoint, TxIOPair> & getTxIOMap(void)    {return txioMap_;}
   map<OutPoint, TxIOPair> & getNonStdTxIO(void) {return nonStdTxioMap_;}

   bool isOutPointMine(BinaryData const & hsh, uint32_t idx);

   void pprintLedger(void);
   void pprintAlot(uint32_t topBlk=0, bool withAddr=false);

   void setBdmPtr(BlockDataManager_LevelDB * bdmptr) {bdmPtr_=bdmptr;}
   void clearBlkData(void);
   
   vector<AddressBookEntry> createAddressBook(void);

   
   uint32_t lastScanned_;

private:
	vector<LedgerEntry> & getEmptyLedger(void) { EmptyLedger_.clear(); return EmptyLedger_;}

private:
   vector<ScrAddrObj*>          scrAddrPtrs_;
   map<BinaryData, ScrAddrObj>  scrAddrMap_;
   map<OutPoint, TxIOPair>      txioMap_;

   vector<LedgerEntry>          ledgerAllAddr_;  
   vector<LedgerEntry>          ledgerAllAddrZC_;  

   // For non-std transactions
   map<OutPoint, TxIOPair>      nonStdTxioMap_;
   set<OutPoint>                nonStdUnspentOutPoints_;

   BlockDataManager_LevelDB*    bdmPtr_;
   static vector<LedgerEntry>   EmptyLedger_; // just a null-reference object


};

#endif
