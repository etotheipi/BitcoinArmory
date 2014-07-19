#ifndef SCRADDROBJ_H
#define SCRADDROBJ_H

#include "BinaryData.h"
#include "leveldb_wrapper.h"
#include "Blockchain.h"
#include "BlockObj.h"
#include "LedgerEntry.h"

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


class ScrAddrObj;

////////////////////////////////////////////////////////////////////////////////
//
// HistoryPages
//
////////////////////////////////////////////////////////////////////////////////

class HistoryPages
{
private:

   struct Page
   {
      uint32_t blockStart_;
      uint32_t blockEnd_;
      uint32_t count_;

      vector<LedgerEntry> pageLedgers_;

      Page(void) : blockStart_(UINT32_MAX), blockEnd_(UINT32_MAX), count_(0)
      {}

      Page(uint32_t count, uint32_t bottom, uint32_t top) :
         blockStart_(bottom), blockEnd_(top), count_(count)
      {}

      bool operator< (const Page& rhs) const
      {
         return this->blockStart_ < rhs.blockStart_;
      }
   };

   vector<Page> pages_;
   map<uint32_t, uint32_t> SSHsummary_;

public:
   HistoryPages(void) {}

   vector<LedgerEntry> getPage(const ScrAddrObj* sa, uint32_t pageId);
   void reset(void) { pages_.clear();}
   void addPage(uint32_t count, uint32_t bottom, uint32_t top);
   void sortPages(void) { std::sort(pages_.begin(), pages_.end()); }
   void mapScrAddrHistory(InterfaceToLDB* db,
                          const BinaryData& scrAddr, 
                          uint32_t txnPerPage);
   const map<uint32_t, uint32_t>& getSSHsummary(void) const
   { return SSHsummary_; }
};

class ScrAddrObj
{
   friend class BtcWallet;
public:

   ScrAddrObj() :
      db_(nullptr),
      bc_(nullptr),
      scrAddr_(0), firstBlockNum_(0), firstTimestamp_(0),
      lastBlockNum_(0), lastTimestamp_(0), hasMultisigEntries_(false),
      totalTxioCount_(0), txnPerPage_(100)
   {
      relevantTxIO_.clear();
   }

   ScrAddrObj(InterfaceToLDB *db, Blockchain *bc, 
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

   void           setScrAddr(InterfaceToLDB *db, BinaryData bd) { db_ = db; scrAddr_.copyFrom(bd);}

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
   { return ledger_; }

   uint32_t getTxLedgerSize(void) const
   { return ledger_.size(); }

   vector<LedgerEntry> getTxLedgerAsVector(void) const;



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

  /* BinaryData getLedgerKey(const BinaryData& DBkey, 
                           bool isTxOut=true) const;*/
   void updateLedgers(map<BinaryData, LedgerEntry>& le,
                      const map<BinaryData, TxIOPair>& newTxio) const;

   void updateLedgers(const map<BinaryData, TxIOPair>& newTxio)
   { updateLedgers(ledger_, newTxio); }

   void setTxioCount(uint64_t count) { totalTxioCount_ = count; }
   uint64_t getTxioCount(void) const { return totalTxioCount_; }
   uint64_t getTxioCountFromSSH(void) const;

   void mapHistory(void)
   { hist_.mapScrAddrHistory(db_, scrAddr_, txnPerPage_); }

   const map<uint32_t, uint32_t>& getHistSSHsummary(void) const
   { return hist_.getSSHsummary(); }

   void fetchDBScrAddrData(uint32_t startBlock, 
                           uint32_t endBlock);

   map<BinaryData, TxIOPair> ScrAddrObj::getHistoryForScrAddr(
      uint32_t startBlock, uint32_t endBlock,
      bool withMultisig = false) const;


private:
   InterfaceToLDB *db_;
   Blockchain     *bc_;
   
   BinaryData     scrAddr_; // this includes the prefix byte!
   uint32_t       firstBlockNum_;
   uint32_t       firstTimestamp_;
   uint32_t       lastBlockNum_;
   uint32_t       lastTimestamp_;

   // If any multisig scripts that include this address, we'll track them
   bool           hasMultisigEntries_;

   // Each address will store a list of pointers to its transactions
   map<BinaryData, TxIOPair>     relevantTxIO_;
   map<BinaryData, LedgerEntry>  ledger_;
   
   uint64_t totalTxioCount_;

   //prebuild history indexes for quick fetch from SSH
   HistoryPages hist_;
   uint32_t txnPerPage_;
};

#endif