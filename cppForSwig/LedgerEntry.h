////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef _LEDGER_ENTRY_H
#define _LEDGER_ENTRY_H

#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockObj.h"
#include "Blockchain.h"
#include "StoredBlockObj.h"


////////////////////////////////////////////////////////////////////////////////
//
// LedgerEntry  
//
// LedgerEntry class is used for bother ScrAddresses and BtcWallets.  Members
// have slightly different meanings (or irrelevant) depending which one it's
// used with.
//
//  Address -- Each entry corresponds to ONE TxIn OR ONE TxOut
//
//    scrAddr_    -  useless - just repeating this address
//    value_     -  net debit/credit on addr balance, in Satoshis (1e-8 BTC)
//    blockNum_  -  block height of the tx in which this txin/out was included
//    txHash_    -  hash of the tx in which this txin/txout was included
//    index_     -  index of the txin/txout in this tx
//    isValid_   -  default to true -- invalidated due to reorg/double-spend
//    isCoinbase -  is the input side a coinbase/generation input
//    isSentToSelf_ - if this is a txOut, did it come from ourself?
//    isChangeBack_ - meaningless:  can't quite figure out how to determine
//                    this unless I do a prescan to determine if all txOuts
//                    are ours, or just some of them
//    isOptInRBF_ - is the sequence number opting into RBF
//    usesWitness - does the input or output use a witness format
//
//  BtcWallet -- Each entry corresponds to ONE WHOLE TRANSACTION
//
//    scrAddr_    -  useless - originally had a purpose, but lost it
//    value_     -  total debit/credit on WALLET balance, in Satoshis (1e-8 BTC)
//    blockNum_  -  block height of the block in which this tx was included
//    txHash_    -  hash of this tx 
//    index_     -  index of the tx in the block
//    isValid_   -  default to true -- invalidated due to reorg/double-spend
//    isCoinbase -  is the input side a coinbase/generation input
//    isSentToSelf_ - if we supplied inputs and rx ALL outputs
//    isChangeBack_ - if we supplied inputs and rx ANY outputs
//    isOptInRBF_ -  is there an input that opts into RBF
//    usesWitness - are the marker and flag for segwit set
//
////////////////////////////////////////////////////////////////////////////////

class LMDBBlockDatabase;

class LedgerEntry
{
public:
   LedgerEntry(void) :
      ID_(0),
      value_(0),
      blockNum_(UINT32_MAX),
      txHash_(BtcUtils::EmptyHash_),
      index_(UINT32_MAX),
      txTime_(0),
      isCoinbase_(false),
      isSentToSelf_(false),
      isChangeBack_(false),
      isOptInRBF_(false),
      usesWitness_(false) {}

   LedgerEntry(BinaryData const & ID,
               int64_t val, 
               uint32_t blkNum, 
               BinaryData const & txhash, 
               uint32_t idx,
               uint32_t txtime,
               bool isCoinbase,
               bool isToSelf,
               bool isChange,
               bool isOptInRBF,
               bool usesWitness,
               bool isChainedZC) :
      ID_(ID),
      value_(val),
      blockNum_(blkNum),
      txHash_(txhash),
      index_(idx),
      txTime_(txtime),
      isCoinbase_(isCoinbase),
      isSentToSelf_(isToSelf),
      isChangeBack_(isChange),
      isOptInRBF_(isOptInRBF),
      usesWitness_(usesWitness),
      isChainedZC_(isChainedZC) {}

   BinaryData const &  getScrAddr(void) const;
   string              getWalletID(void) const;
   int64_t             getValue(void) const     { return value_;         }
   uint32_t            getBlockNum(void) const  { return blockNum_;      }
   BinaryData const &  getTxHash(void) const    { return txHash_;        }
   uint32_t            getIndex(void) const     { return index_;         }
   uint32_t            getTxTime(void) const    { return txTime_;        }
   bool                isCoinbase(void) const   { return isCoinbase_;    }
   bool                isSentToSelf(void) const { return isSentToSelf_;  }
   bool                isChangeBack(void) const { return isChangeBack_;  }
   bool                isOptInRBF(void) const   { return isOptInRBF_;    }
   bool                usesWitness(void) const  { return usesWitness_;   }
   bool                isChainedZC(void) const  { return isChainedZC_;   }

   SCRIPT_PREFIX getScriptType(void) const {return (SCRIPT_PREFIX)ID_[0];}

   void setScrAddr(BinaryData const & bd);
   void setWalletID(BinaryData const & bd);
   void changeBlkNum(uint32_t newHgt) {blockNum_ = newHgt; }
      
   bool operator<(LedgerEntry const & le2) const;
   bool operator>(LedgerEntry const & le2) const;
   bool operator==(LedgerEntry const & le2) const;

   void pprint(void);
   void pprintOneLine(void) const;

   static void purgeLedgerMapFromHeight(map<BinaryData, LedgerEntry>& leMap,
                                        uint32_t purgeFrom);
   static void purgeLedgerVectorFromHeight(vector<LedgerEntry>& leMap,
      uint32_t purgeFrom);

   static void computeLedgerMap(map<BinaryData, LedgerEntry> &leMap,
                                const map<BinaryData, TxIOPair>& txioMap,
                                uint32_t startBlock, uint32_t endBlock,
                                const BinaryData& ID,
                                const LMDBBlockDatabase* db,
                                const Blockchain* bc,
                                bool purge);
   
   set<BinaryData> getScrAddrList(void) const
   { return scrAddrSet_; }
   
public:

   static LedgerEntry EmptyLedger_;
   static map<BinaryData, LedgerEntry> EmptyLedgerMap_;
   static BinaryData ZCheader_;
   static BinaryData EmptyID_;

private:
   
   //holds either a scrAddr or a walletId
   BinaryData       ID_;

   int64_t          value_;
   uint32_t         blockNum_;
   BinaryData       txHash_;
   uint32_t         index_;  // either a tx index, txout index or txin index
   uint32_t         txTime_ = 0;
   bool             isCoinbase_ = false;
   bool             isSentToSelf_ = false;
   bool             isChangeBack_ = false;
   bool             isOptInRBF_ = false;
   bool             usesWitness_ = false;
   bool             isChainedZC_ = false;

   //for matching scrAddr comments to LedgerEntries on the Python side
   set<BinaryData> scrAddrSet_;
}; 

struct LedgerEntry_DescendingOrder
{
   bool operator() (const LedgerEntry& a, const LedgerEntry& b)
   { return a > b; }
};

class LedgerDelegate
{
   friend class BlockDataViewer;

public:
   vector<LedgerEntry> getHistoryPage(uint32_t id)
   {
      return getHistoryPage_(id);
   }

   uint32_t getBlockInVicinity(uint32_t blk)
   {
      return getBlockInVicinity_(blk);
   }

   uint32_t getPageIdForBlockHeight(uint32_t blk)
   {
      return getPageIdForBlockHeight_(blk);
   }

private:
   LedgerDelegate(
      function<vector<LedgerEntry>(uint32_t)> getHist,
      function<uint32_t(uint32_t)> getBlock,
      function<uint32_t(uint32_t)> getPageId) :
      getHistoryPage_(getHist),
      getBlockInVicinity_(getBlock),
      getPageIdForBlockHeight_(getPageId)
   {}

private:
   const function<vector<LedgerEntry>(uint32_t)> getHistoryPage_;
   const function<uint32_t(uint32_t)>            getBlockInVicinity_;
   const function<uint32_t(uint32_t)>            getPageIdForBlockHeight_;
};

#endif
