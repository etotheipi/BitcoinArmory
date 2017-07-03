////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef SCRADDROBJ_H
#define SCRADDROBJ_H

#include "BinaryData.h"
#include "lmdb_wrapper.h"
#include "Blockchain.h"
#include "BlockObj.h"
#include "txio.h"
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
struct ScanAddressStruct
{
   set<BinaryData> invalidatedZCKeys_;
   map<BinaryData, shared_ptr<map<BinaryData, TxIOPair>>> zcMap_;
   map<BinaryData, LedgerEntry> zcLedgers_;
};

class ScrAddrObj
{
   friend class BtcWallet;

private:
   struct pagedUTXOs
   {
      static const uint32_t UTXOperFetch = 100;

      map<BinaryData, TxIOPair> utxoList_;
      uint32_t topBlock_ = 0;
      uint64_t value_ = 0;

      /***We use a dedicate count here instead of map::size() so that a thread
      can update the map while another reading the struct won't be aware of the
      new entries until count_ is updated
      ***/
      uint32_t count_ = 0;
      
      const ScrAddrObj *scrAddrObj_;

      pagedUTXOs(const ScrAddrObj* scrAddrObj) : 
         scrAddrObj_(scrAddrObj)
      {}

      const map<BinaryData, TxIOPair>& getUTXOs(void) const
      { return utxoList_; }

      bool fetchMoreUTXO(function<bool(const BinaryData&)> spentByZC)
      {
         //return true if more UTXO were found, false otherwise
         if (topBlock_ < scrAddrObj_->bc_->top()->getBlockHeight())
         {
            uint32_t rangeTop;
            uint32_t count = 0;
            do
            {
               rangeTop = scrAddrObj_->hist_.getRangeForHeightAndCount(
                                                topBlock_, UTXOperFetch);
               count += fetchMoreUTXO(topBlock_, rangeTop, spentByZC);
            } 
            while (count < UTXOperFetch && rangeTop != UINT32_MAX);

            if (count > 0)
               return true;
         }

         return false;
      }

      uint32_t fetchMoreUTXO(uint32_t start, uint32_t end,
         function<bool(const BinaryData&)> spentByZC)
      {
         uint32_t nutxo = 0;
         uint64_t val = 0;

         StoredScriptHistory ssh;
         scrAddrObj_->db_->getStoredScriptHistory(ssh, 
            scrAddrObj_->scrAddr_, start, end);

         for (const auto& subsshPair : ssh.subHistMap_)
         {
            for (const auto& txioPair : subsshPair.second.txioMap_)
            {
               if (txioPair.second.isUTXO())
               {
                  //isMultisig only signifies this scrAddr was used in the
                  //composition of a funded multisig transaction. This is purely
                  //meta-data and shouldn't be returned as a spendable txout
                  if (txioPair.second.isMultisig())
                     continue;

                  if (spentByZC(txioPair.second.getDBKeyOfOutput()) == true)
                     continue;

                  auto txioAdded = utxoList_.insert(txioPair);

                  if (txioAdded.second == true)
                  {
                     val += txioPair.second.getValue();
                     nutxo++;
                  }
               }
            }
         }

         topBlock_ = end;
         value_ += val;
         count_ += nutxo;

         return nutxo;
      }

      uint64_t getValue(void) const { return value_; }
      uint32_t getCount(void) const { return count_; }

      void reset(void)
      {
         topBlock_ = 0;
         value_ = 0;
         count_ = 0;

         utxoList_.clear();
      }

      void addZcUTXOs(const map<BinaryData, TxIOPair>& txioMap,
         function<bool(const BinaryData&)> isFromWallet)
      {
         BinaryData ZCheader(WRITE_UINT16_LE(0xFFFF));

         for (const auto& txio : txioMap)
         {
            if (!txio.first.startsWith(ZCheader))
               continue;

            if (txio.second.hasTxIn())
               continue;

            /*if (!isFromWallet(txio.second.getDBKeyOfOutput().getSliceCopy(0, 6)))
               continue;*/

            utxoList_.insert(txio);
         }
      }
   };

public:

   ScrAddrObj() :
      db_(nullptr),
      bc_(nullptr),
      scrAddr_(0), firstBlockNum_(0), firstTimestamp_(0),
      lastBlockNum_(0), lastTimestamp_(0), hasMultisigEntries_(false),
      totalTxioCount_(0), utxos_(this)
   {
      relevantTxIO_.clear();
   }

   ScrAddrObj(LMDBBlockDatabase *db, Blockchain *bc,
              BinaryData    addr, 
              uint32_t      firstBlockNum  = UINT32_MAX,
              uint32_t      firstTimestamp = UINT32_MAX,
              uint32_t      lastBlockNum   = 0,
              uint32_t      lastTimestamp  = 0);

   ScrAddrObj(const ScrAddrObj& rhs) : 
      utxos_(nullptr)
   {
      *this = rhs;
   }
   
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
   uint64_t getSpendableBalance(uint32_t currBlk) const;
   uint64_t getUnconfirmedBalance(uint32_t currBlk) const;

   vector<UnspentTxOut> getFullTxOutList(uint32_t currBlk=UINT32_MAX, bool ignoreZC=true) const;
   vector<UnspentTxOut> getSpendableTxOutList(bool ignoreZC=true) const;


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

   void scanZC(const ScanAddressStruct&, function<bool(const BinaryDataRef)>,
      int32_t);
   bool purgeZC(const set<BinaryData>& invalidatedTxOutKeys);

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
   uint64_t getTxioCount(void) const { return getTxioCountFromSSH(); }
   uint64_t getTxioCountFromSSH(void) const;

   void mapHistory(void);

   const map<uint32_t, uint32_t>& getHistSSHsummary(void) const
   { return hist_.getSSHsummary(); }

   void fetchDBScrAddrData(uint32_t startBlock, 
                           uint32_t endBlock,
                           int32_t updateID);

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

   const map<BinaryData, TxIOPair>& getPreparedTxOutList(void) const
   { return utxos_.getUTXOs(); }
   
   bool getMoreUTXOs(pagedUTXOs&, 
      function<bool(const BinaryData&)> hasTxOutInZC) const;
   bool getMoreUTXOs(function<bool(const BinaryData&)> hasTxOutInZC);
   vector<UnspentTxOut> getAllUTXOs(
      function<bool(const BinaryData&)> hasTxOutInZC) const;

   uint64_t getLoadedTxOutsValue(void) const { return utxos_.getValue(); }
   uint32_t getLoadedTxOutsCount(void) const { return utxos_.getCount(); }

   void resetTxOutHistory(void) { utxos_.reset(); }

   LedgerEntry getFirstLedger(void) const;

   void addZcUTXOs(const map<BinaryData, TxIOPair>& txioMap,
      function<bool(const BinaryData&)> isFromWallet)
   { utxos_.addZcUTXOs(txioMap, isFromWallet); }

   uint32_t getBlockInVicinity(uint32_t blk) const;
   uint32_t getPageIdForBlockHeight(uint32_t blk) const;

   uint32_t getTxioCountForLedgers(void)
   {
      //return UINT32_MAX unless count has changed since last call
      //(or it's the first call)
      auto count = getTxioCountFromSSH();
      if (count == txioCountForLedgers_)
         return UINT32_MAX;

      txioCountForLedgers_ = count;
      return count;
   }

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

   uint32_t txioCountForLedgers_ = UINT32_MAX;

   //prebuild history indexes for quick fetch from ssh
   HistoryPager hist_;

   //fetches and maintains utxos
   pagedUTXOs   utxos_;

   map<BinaryData, set<BinaryData> > validZCKeys_;

   int32_t updateID_ = 0;
};

#endif
