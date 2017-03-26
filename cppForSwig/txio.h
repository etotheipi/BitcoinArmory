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
#ifndef _TXIO_H_
#define _TXIO_H_

#include <functional>

#include "BinaryData.h"
#include "BlockObj.h"

class TxIOPair
{
public:
   //////////////////////////////////////////////////////////////////////////////
   // TODO:  since we tend not to track TxIn/TxOuts but make them on the fly,
   //        we should probably do that here, too.  I designed this before I
   //        realized that these copies will fall out of sync on a reorg
   TxIOPair(void);
   explicit TxIOPair(uint64_t amount);
   explicit TxIOPair(TxRef txRefO, uint32_t txoutIndex);
   explicit TxIOPair(const BinaryData& txOutKey8B, uint64_t value);
   explicit TxIOPair(TxRef txRefO, uint32_t txoutIndex,
      TxRef txRefI, uint32_t txinIndex);

   TxIOPair(const TxIOPair& txio)
   {
      *this = txio;
      getScrAddr_ = [](void)->const BinaryData&{ return BinaryData::EmptyBinData_; };
   }

   // Lots of accessors
   bool      hasTxOut(void) const   { return (txRefOfOutput_.isInitialized()); }
   bool      hasTxIn(void) const    { return (txRefOfInput_.isInitialized()); }
   bool      hasTxOutInMain(LMDBBlockDatabase *db) const;
   bool      hasTxInInMain(LMDBBlockDatabase *db) const;
   bool      hasTxOutZC(void) const;
   bool      hasTxInZC(void) const;
   bool      hasValue(void) const   { return (amount_ != 0); }
   uint64_t  getValue(void) const   { return  amount_; }
   void      setValue(const uint64_t& newVal) { amount_ = newVal; }

   //////////////////////////////////////////////////////////////////////////////
   TxRef     getTxRefOfOutput(void) const { return txRefOfOutput_; }
   TxRef     getTxRefOfInput(void) const  { return txRefOfInput_; }
   uint32_t  getIndexOfOutput(void) const { return indexOfOutput_; }
   uint32_t  getIndexOfInput(void) const  { return indexOfInput_; }
   OutPoint  getOutPoint(LMDBBlockDatabase *db) const { return OutPoint(getTxHashOfOutput(db), indexOfOutput_); }

   pair<bool, bool> reassessValidity(LMDBBlockDatabase *db);
   bool  isTxOutFromSelf(void) const  { return isTxOutFromSelf_; }
   void setTxOutFromSelf(bool isTrue = true) { isTxOutFromSelf_ = isTrue; }
   bool  isFromCoinbase(void) const { return isFromCoinbase_; }
   void setFromCoinbase(bool isTrue = true) { isFromCoinbase_ = isTrue; }
   bool  isMultisig(void) const { return isMultisig_; }
   void setMultisig(bool isTrue = true) { isMultisig_ = isTrue; }
   bool isRBF(void) const { return isRBF_; }
   void setRBF(bool isTrue) { isRBF_ = isTrue; }
   void setChained(bool isTrue) { isZCChained_ = isTrue; }
   bool isChainedZC(void) const { return isZCChained_; }

   BinaryData getDBKeyOfOutput(void) const
   {
      return txRefOfOutput_.getDBKeyOfChild(indexOfOutput_);
   }
   BinaryData getDBKeyOfInput(void) const
   {
      return txRefOfInput_.getDBKeyOfChild(indexOfInput_);
   }

   //////////////////////////////////////////////////////////////////////////////
   BinaryData    getTxHashOfInput(const LMDBBlockDatabase *db = nullptr) const;
   BinaryData    getTxHashOfOutput(const LMDBBlockDatabase *db = nullptr) const;

   void setTxHashOfInput(const BinaryData& txHash)
   {
      txHashOfInput_ = txHash;
   }
   void setTxHashOfOutput(const BinaryData& txHash)
   {
      txHashOfOutput_ = txHash;
   }

   TxOut getTxOutCopy(LMDBBlockDatabase *db) const;
   TxIn  getTxInCopy(LMDBBlockDatabase *db) const;

   bool setTxIn(TxRef  txref, uint32_t index);
   bool setTxIn(const BinaryData& dbKey8B);
   bool setTxOut(TxRef  txref, uint32_t index);
   bool setTxOut(const BinaryData& dbKey8B);

   //////////////////////////////////////////////////////////////////////////////
   bool isSourceUnknown(void) { return (!hasTxOut() && hasTxIn()); }

   bool isSpent(LMDBBlockDatabase *db) const;
   bool isUnspent(LMDBBlockDatabase *db) const;
   bool isSpendable(LMDBBlockDatabase *db, uint32_t currBlk) const;
   bool isMineButUnconfirmed(LMDBBlockDatabase *db, uint32_t currBlk) const;
   void pprintOneLine(LMDBBlockDatabase *db) const;

   bool operator<(TxIOPair const & t2)
   {
      return (getDBKeyOfOutput() < t2.getDBKeyOfOutput());
   }
   bool operator==(TxIOPair const & t2)
   {
      return (getDBKeyOfOutput() == t2.getDBKeyOfOutput());
   }
   bool operator>=(const BinaryData &) const;
   TxIOPair& operator=(const TxIOPair &);
   TxIOPair& operator=(TxIOPair&& toMove);

   void setTxTime(uint32_t t) { txtime_ = t; }
   uint32_t getTxTime(void) const { return txtime_; }

   bool isUTXO(void) const { return isUTXO_; }
   void setUTXO(bool val) { isUTXO_ = val; }

   void setScrAddrLambda(function < const BinaryData&(void) > func)
   {
      getScrAddr_ = func;
   }

   const BinaryData& getScrAddr(void) const
   {
      return getScrAddr_();
   }

public:
   bool flagged = false;

private:
   uint64_t  amount_;

   TxRef     txRefOfOutput_;
   uint32_t  indexOfOutput_;
   TxRef     txRefOfInput_;
   uint32_t  indexOfInput_;

   mutable BinaryData txHashOfOutput_;
   mutable BinaryData txHashOfInput_;

   // Zero-conf data isn't on disk, yet, so can't use TxRef
   bool      isTxOutFromSelf_ = false;
   bool      isFromCoinbase_;
   bool      isMultisig_;
   bool      isRBF_ = false;
   bool      isZCChained_ = false;

   //mainly for ZC ledgers. Could replace the need for a blockchain 
   //object to build scrAddrObj ledgers.
   uint32_t txtime_;

   /***marks txio as spent for serialize/deserialize operations. It signifies
   whether a subSSH entry with only a TxOut DBkey is spent.

   To allow for partial parsing of ssh history, all txouts need to be visible at
   the height they appeared, amd spent txouts need to be visible at the
   spending txin's height as well.

   While spent txouts at txin height are unique, spent txouts at txout height
   need to be differenciated from UTXOs.
   ***/
   bool isUTXO_ = false;

   //used to get a relevant scrAddr from a txio
   function<const BinaryData& (void)> getScrAddr_ = 
      [](void)->const BinaryData&
      { return BinaryData::EmptyBinData_; };
};

#endif
