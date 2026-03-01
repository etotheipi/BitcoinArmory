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
#include "txio.h"

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(void) :
amount_(0),
indexOfOutput_(0),
indexOfInput_(0),
isTxOutFromSelf_(false),
isFromCoinbase_(false),
isMultisig_(false),
txtime_(0),
isUTXO_(false)
{}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(uint64_t  amount) :
amount_(amount),
indexOfOutput_(0),
indexOfInput_(0),
isTxOutFromSelf_(false),
isFromCoinbase_(false),
isMultisig_(false),
txtime_(0),
isUTXO_(false)
{}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(TxRef txPtrO, uint32_t txoutIndex) :
amount_(0),
indexOfInput_(0),
isTxOutFromSelf_(false),
isFromCoinbase_(false),
isMultisig_(false),
txtime_(0),
isUTXO_(false)
{
   setTxOut(txPtrO, txoutIndex);
}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(TxRef     txPtrO,
   uint32_t  txoutIndex,
   TxRef     txPtrI,
   uint32_t  txinIndex) :
   amount_(0),
   isTxOutFromSelf_(false),
   isFromCoinbase_(false),
   isMultisig_(false),
   txtime_(0),
   isUTXO_(false)
{
   setTxOut(txPtrO, txoutIndex);
   setTxIn(txPtrI, txinIndex);
}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(const BinaryData& txOutKey8B, uint64_t val) :
amount_(val),
indexOfOutput_(0),
indexOfInput_(0),
isTxOutFromSelf_(false),
isFromCoinbase_(false),
isMultisig_(false),
txtime_(0),
isUTXO_(false)
{
   setTxOut(txOutKey8B);
}
//////////////////////////////////////////////////////////////////////////////
HashString TxIOPair::getTxHashOfOutput(const LMDBBlockDatabase *db) const
{
   if (!hasTxOut())
      return BtcUtils::EmptyHash();
   else if (txHashOfOutput_.getSize() == 32)
      return txHashOfOutput_;
   else if (txRefOfOutput_.isInitialized() && db != nullptr)
   {
      DBTxRef dbTxRef(txRefOfOutput_, db);
      txHashOfOutput_ = dbTxRef.getThisHash();
      return txHashOfOutput_;
   }

   return BinaryData(0);
}

//////////////////////////////////////////////////////////////////////////////
HashString TxIOPair::getTxHashOfInput(const LMDBBlockDatabase *db) const
{
   if (!hasTxIn())
      return BtcUtils::EmptyHash();
   else if (txHashOfInput_.getSize() == 32)
      return txHashOfInput_;
   else if (txRefOfInput_.isInitialized() && db != nullptr)
   {
      DBTxRef dbTxRef(txRefOfInput_, db);
      txHashOfInput_ = dbTxRef.getThisHash();
      return txHashOfInput_;
   }

   return BinaryData(0);
}
//////////////////////////////////////////////////////////////////////////////
TxOut TxIOPair::getTxOutCopy(LMDBBlockDatabase *db) const
{
   // I actually want this to segfault when there is no TxOut... 
   // we should't ever be trying to access it without checking it 
   // first in the calling code (hasTxOut/hasTxOutZC)
   if (hasTxOut())
   {
      DBTxRef dbTxRef(txRefOfOutput_, db);
      return dbTxRef.getTxOutCopy(indexOfOutput_);
   }

   throw runtime_error("Has not TxOutCopy");
}

//////////////////////////////////////////////////////////////////////////////
TxIn TxIOPair::getTxInCopy(LMDBBlockDatabase *db) const
{
   // I actually want this to segfault when there is no TxIn... 
   // we should't ever be trying to access it without checking it 
   // first in the calling code (hasTxIn/hasTxInZC)
   if (hasTxIn())
   {
      DBTxRef dbTxRef(txRefOfInput_, db);
      return dbTxRef.getTxInCopy(indexOfInput_);
   }

   throw runtime_error("Has not TxInCopy");
}


//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::setTxIn(TxRef  txref, uint32_t index)
{
   txRefOfInput_ = txref;
   indexOfInput_ = index;

   return true;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::setTxIn(const BinaryData& dbKey8B)
{
   if (dbKey8B.getSize() == 8)
   {
      BinaryRefReader brr(dbKey8B);
      BinaryDataRef txKey6B = brr.get_BinaryDataRef(6);
      uint16_t      txInIdx = brr.get_uint16_t(BE);
      return setTxIn(TxRef(txKey6B), (uint32_t)txInIdx);
   }
   else
   {
      //pass a 0 byte dbkey to reset the txin
      setTxIn(TxRef(), 0);
      return false;
   }
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::setTxOut(const BinaryData& dbKey8B)
{
   if (dbKey8B.getSize() == 8)
   {
      BinaryRefReader brr(dbKey8B);
      BinaryDataRef txKey6B = brr.get_BinaryDataRef(6);
      uint16_t      txOutIdx = brr.get_uint16_t(BE);
      return setTxOut(TxRef(txKey6B), (uint32_t)txOutIdx);
   }
   else
   {
      //pass 0 byte dbkey to reset the txout
      setTxOut(TxRef(), 0);
      return false;
   }
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::setTxOut(TxRef txref, uint32_t index)
{
   txRefOfOutput_ = txref;
   indexOfOutput_ = index;
   return true;
}


//////////////////////////////////////////////////////////////////////////////
pair<bool, bool> TxIOPair::reassessValidity(LMDBBlockDatabase *db)
{
   pair<bool, bool> result;
   result.first = hasTxOutInMain(db);
   result.second = hasTxInInMain(db);
   return result;
}


//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isSpent(LMDBBlockDatabase *db) const
{
   // Not sure whether we should verify hasTxOut.  It wouldn't make much 
   // sense to have TxIn but not TxOut, but there might be a preferred 
   // behavior in such awkward circumstances
   return (hasTxInZC() || hasTxInInMain(db));
}


//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isUnspent(LMDBBlockDatabase *db) const
{
   return ((hasTxOutZC() || hasTxOutInMain(db)) && !isSpent(db));

}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isSpendable(LMDBBlockDatabase *db, uint32_t currBlk) const
{
   // Spendable TxOuts are ones with at least 1 confirmation
   if (hasTxInZC() || hasTxInInMain(db))
      return false;

   if (hasTxOutInMain(db))
   {
      uint32_t nConf = currBlk - txRefOfOutput_.getBlockHeight() + 1;
      if (isFromCoinbase_ && nConf <= COINBASE_MATURITY)
         return false;
      else
         return true;
   }

   if (hasTxOutZC()/* && isTxOutFromSelf()*/)
      return false;

   return false;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isMineButUnconfirmed(
   LMDBBlockDatabase *db, uint32_t currBlk) const
{
   DBTxRef dbTxRef(txRefOfInput_, db);
   if (hasTxInZC() || (hasTxIn() && dbTxRef.isMainBranch()))
      return false;

   if (hasTxOutZC())
      return true;

   if (hasTxOutInMain(db))
   {
      uint32_t nConf = currBlk - txRefOfOutput_.getBlockHeight() + 1;
      if (isFromCoinbase_)
         return (nConf<COINBASE_MATURITY);
      else
         return (nConf<MIN_CONFIRMATIONS);
   }

   return false;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::hasTxOutInMain(LMDBBlockDatabase *db) const
{
   DBTxRef dbTxRef(txRefOfOutput_, db);
   return (!hasTxOutZC() && hasTxOut() && dbTxRef.isMainBranch());
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::hasTxInInMain(LMDBBlockDatabase *db) const
{
   DBTxRef dbTxRef(txRefOfInput_, db);
   return (!hasTxInZC() && hasTxIn() && dbTxRef.isMainBranch());
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::hasTxOutZC(void) const
{
   return txRefOfOutput_.getDBKey().startsWith(READHEX("ffff"));
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::hasTxInZC(void) const
{
   return txRefOfInput_.getDBKey().startsWith(READHEX("ffff"));
}

//////////////////////////////////////////////////////////////////////////////
void TxIOPair::pprintOneLine(LMDBBlockDatabase *db) const
{
   printf("   Val:(%0.3f)\t  (STS, O,I, Omb,Imb, Oz,Iz)  %d  %d%d %d%d %d%d\n",
      (double)getValue() / 1e8,
      (isTxOutFromSelf() ? 1 : 0),
      (hasTxOut() ? 1 : 0),
      (hasTxIn() ? 1 : 0),
      (hasTxOutInMain(db) ? 1 : 0),
      (hasTxInInMain(db) ? 1 : 0),
      (hasTxOutZC() ? 1 : 0),
      (hasTxInZC() ? 1 : 0));

}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::operator>=(const BinaryData &dbKey) const
{
   if (txRefOfOutput_ >= dbKey)
      return true;

   if (txRefOfInput_ >= dbKey)
      return true;

   return false;
}

//////////////////////////////////////////////////////////////////////////////
TxIOPair& TxIOPair::operator=(const TxIOPair &rhs)
{
   this->amount_ = rhs.amount_;

   this->txRefOfOutput_ = rhs.txRefOfOutput_;
   this->indexOfOutput_ = rhs.indexOfOutput_;
   this->txRefOfInput_ = rhs.txRefOfInput_;
   this->indexOfInput_ = rhs.indexOfInput_;

   this->txHashOfOutput_ = rhs.txHashOfOutput_;
   this->txHashOfInput_ = rhs.txHashOfInput_;

   this->isTxOutFromSelf_ = rhs.isTxOutFromSelf_;
   this->isFromCoinbase_ = rhs.isFromCoinbase_;
   this->isMultisig_ = rhs.isMultisig_;

   this->txtime_ = rhs.txtime_;

   this->isUTXO_ = rhs.isUTXO_;
   this->isRBF_ = rhs.isRBF_;
   this->isZCChained_ = rhs.isZCChained_;

   return *this;
}

//////////////////////////////////////////////////////////////////////////////
TxIOPair& TxIOPair::operator=(TxIOPair&& toMove)
{
   this->amount_ = toMove.amount_;

   this->txRefOfOutput_ = move(toMove.txRefOfOutput_);
   this->indexOfOutput_ = move(toMove.indexOfOutput_);
   this->txRefOfInput_ = move(toMove.txRefOfInput_);
   this->indexOfInput_ = move(toMove.indexOfInput_);

   this->txHashOfOutput_ = move(toMove.txHashOfOutput_);
   this->txHashOfInput_ = move(toMove.txHashOfInput_);

   this->isTxOutFromSelf_ = toMove.isTxOutFromSelf_;
   this->isFromCoinbase_ = toMove.isFromCoinbase_;
   this->isMultisig_ = toMove.isMultisig_;

   this->txtime_ = toMove.txtime_;

   this->isUTXO_ = toMove.isUTXO_;
   this->isRBF_ = toMove.isRBF_;
   this->isZCChained_ = toMove.isZCChained_;

   return *this;
}
