#ifndef SCRADDROBJ_H
#define SCRADDROBJ_H

#include "BinaryData.h"
#include "lmdb_wrapper.h"
#include "Blockchain.h"
#include "BlockObj.h"
#include "LedgerEntry.h"
#include "HistoryPager.h"

////////////////////////////////////////////////////////////////////////////////
//
// ScrAddrObj  
//
// This class is only for scanning the blockchain (information only).  It has
// no need to keep track of the public and private keys of various addresses,
// which is done by the python code leveraging this class.
//
// I call these as "scraddresses".  In most contexts, it represents an
// "address" that people use to send coins per-to-person, but it could actually
// represent any kind of TxOut script.  Multisig, P2SH, or any non-standard,
// unusual, escrow, whatever "address."  While it might be more technically
// correct to just call this class "Script" or "TxOutScript", I felt like 
// "address" is a term that will always exist in the Bitcoin ecosystem, and 
// frequently used even when not preferred.
//
// Similarly, we refer to the member variable scraddr_ as a "scradder".  It
// is actually a reduction of the TxOut script to a form that is identical
// regardless of whether pay-to-pubkey or pay-to-pubkey-hash is used. 
//
//
////////////////////////////////////////////////////////////////////////////////

class ScrAddrObj
{
   friend class BtcWallet;
public:

   ScrAddrObj() :
      db_(nullptr),
      bc_(nullptr),
      scrAddr_(0), firstBlockNum_(0), firstTimestamp_(0),
      lastBlockNum_(0), lastTimestamp_(0), hasMultisigEntries_(false),
      totalTxioCount_(0)
   {
      relevantTxIO_.clear();
   }

   ScrAddrObj(LMDBBlockDatabase *db, Blockchain *bc,
              BinaryData    addr, 
              uint32_t      firstBlockNum  = UINT32_MAX,
              uint32_t      firstTimestamp = UINT32_MAX,
              uint32_t      lastBlockNum   = 0,
              uint32_t      lastTimestamp  = 0);
   
   BinaryData const &  getScrAddr(void) const    {return scrAddr_;       }
   uint32_t       getFirstBlockNum(void) const   {return firstBlockNum_; }
   uint32_t       getFirstTimestamp(void) const  {return firstTimestamp_;}
   uint32_t       getLastBlockNum(void) const    {return lastBlockNum_;  }
   uint32_t       getLastTimestamp(void) const   {return lastTimestamp_; }
   void           setFirstBlockNum(uint32_t b)   { firstBlockNum_  = b; }
   void           setFirstTimestamp(uint32_t t)  { firstTimestamp_ = t; }
   void           setLastBlockNum(uint32_t b)    { lastBlockNum_   = b; }
   void           setLastTimestamp(uint32_t t)   { lastTimestamp_  = t; }

   void           setScrAddr(LMDBBlockDatabase *db, BinaryData bd) { db_ = db; scrAddr_.copyFrom(bd);}

   // BlkNum is necessary for "unconfirmed" list, since it is dependent
   // on number of confirmations.  But for "spendable" TxOut list, it is
   // only a convenience, if you want to be able to calculate numConf from
   // the Utxos in the list.  If you don't care (i.e. you only want to 
   // know what TxOuts are available to spend, you can pass in 0 for currBlk
   uint64_t getFullBalance() const;
   uint64_t getSpendableBalance(
      uint32_t currBlk=0, 
      bool ignoreAllZeroConf=false
   ) const;
   uint64_t getUnconfirmedBalance(
      uint32_t currBlk, 
      bool includeAllZeroConf=false
   ) const;
   vector<UnspentTxOut> getFullTxOutList(uint32_t currBlk=0) const;
   vector<UnspentTxOut> getSpendableTxOutList(uint32_t currBlk=0, 
                                              bool ignoreAllZeroConf=false
                                             ) const;


   const map<BinaryData, LedgerEntry> & getTxLedger(void) const 
   { return *ledger_; }
   
   vector<LedgerEntry> getTxLedgerAsVector(
      map<BinaryData, LedgerEntry>& leMap) const;

   size_t getTxLedgerSize(void) const
   {
      if (ledger_ == nullptr)
         return 0;
      return ledger_->size(); }


   map<BinaryData, TxIOPair> &   getTxIOMap(void) { return relevantTxIO_; }
   const map<BinaryData, TxIOPair> & getTxIOMap(void) const 
                           { return relevantTxIO_; }

   void addTxIO(TxIOPair & txio, bool isZeroConf=false);

   void pprintLedger(void) const;
   void clearBlkData(void);

   bool operator== (const ScrAddrObj& rhs) const
   { return (scrAddr_ == rhs.scrAddr_); }

   void updateTxIOMap(map<BinaryData, TxIOPair>& txio_map);

   void scanZC(const map<HashString, TxIOPair>& zcTxIOMap);
   void purgeZC(const vector<BinaryData>& invalidatedTxOutKeys);

   void updateAfterReorg(uint32_t lastValidBlockHeight);

   void updateLedgers(map<BinaryData, LedgerEntry>& leMap,
                      const map<BinaryData, TxIOPair>& txioMap,
                      uint32_t startBlock, uint32_t endBlock, 
                      bool purge = false) const;

   void updateLedgers(const map<BinaryData, TxIOPair>& txioMap,
                      uint32_t startBlock, uint32_t endBlock,
                      bool purge = false)
   { updateLedgers(*ledger_, txioMap, startBlock, endBlock, purge); }

   void setTxioCount(uint64_t count) { totalTxioCount_ = count; }
   uint64_t getTxioCount(void) const { return totalTxioCount_; }
   uint64_t getTxioCountFromSSH(void) const;

   void mapHistory(void);

   const map<uint32_t, uint32_t>& getHistSSHsummary(void) const
   { return hist_.getSSHsummary(); }

   void fetchDBScrAddrData(uint32_t startBlock, 
                           uint32_t endBlock);

   void getHistoryForScrAddr(
      uint32_t startBlock, uint32_t endBlock,
      map<BinaryData, TxIOPair>& output,
      bool update,
      bool withMultisig = false) const;

   size_t getPageCount(void) const { return hist_.getPageCount(); }
   vector<LedgerEntry> getHistoryPageById(uint32_t id);
   void updateLedgerPointer(void) 
      { ledger_ = &hist_.getPageLedgerMap(0); }

   ScrAddrObj& operator= (const ScrAddrObj& rhs);

private:
   LMDBBlockDatabase *db_;
   Blockchain        *bc_;
   
   BinaryData     scrAddr_; // this includes the prefix byte!
   uint32_t       firstBlockNum_;
   uint32_t       firstTimestamp_;
   uint32_t       lastBlockNum_;
   uint32_t       lastTimestamp_;

   // If any multisig scripts that include this address, we'll track them
   bool           hasMultisigEntries_=false;

   // Each address will store a list of pointers to its transactions
   map<BinaryData, TxIOPair>     relevantTxIO_;
   map<BinaryData, LedgerEntry>*  ledger_ = &LedgerEntry::EmptyLedgerMap_;
   
   mutable uint64_t totalTxioCount_=0;
   mutable uint32_t lastSeenBlock_=0;

   //prebuild history indexes for quick fetch from SSH
   HistoryPager hist_;
};

#endif
