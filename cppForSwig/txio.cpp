////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
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
      txHashOfOutput_ = txRefOfOutput_.attached(db).getThisHash();
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
      txHashOfInput_ = txRefOfInput_.attached(db).getThisHash();
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
      return txRefOfOutput_.attached(db).getTxOutCopy(indexOfOutput_);

   throw runtime_error("Has not TxOutCopy");
}

//////////////////////////////////////////////////////////////////////////////
TxIn TxIOPair::getTxInCopy(LMDBBlockDatabase *db) const
{
   // I actually want this to segfault when there is no TxIn... 
   // we should't ever be trying to access it without checking it 
   // first in the calling code (hasTxIn/hasTxInZC)
   if (hasTxIn())
      return txRefOfInput_.attached(db).getTxInCopy(indexOfInput_);
   /*else
   return getTxInZC();*/
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
      uint16_t      txInIdx = brr.get_uint16_t(BIGENDIAN);
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
      uint16_t      txOutIdx = brr.get_uint16_t(BIGENDIAN);
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
bool TxIOPair::isSpendable(LMDBBlockDatabase *db, uint32_t currBlk, bool ignoreAllZeroConf) const
{
   // Spendable TxOuts are ones with at least 1 confirmation, or zero-conf
   // TxOuts that were sent-to-self.  Obviously, they should be unspent, too
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

   if (hasTxOutZC() && isTxOutFromSelf())
      return !ignoreAllZeroConf;

   return false;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isMineButUnconfirmed(
   LMDBBlockDatabase *db,
   uint32_t currBlk, bool inclAllZC
   ) const
{
   // All TxOuts that were from our own transactions are always confirmed
   if (isTxOutFromSelf())
      return false;

   if (hasTxInZC() || (hasTxIn() && txRefOfInput_.attached(db).isMainBranch()))
      return false;

   if (hasTxOutInMain(db))
   {
      uint32_t nConf = currBlk - txRefOfOutput_.getBlockHeight() + 1;
      if (isFromCoinbase_)
         return (nConf<COINBASE_MATURITY);
      else
         return (nConf<MIN_CONFIRMATIONS);
   }
   else if (hasTxOutZC() && (!isTxOutFromSelf() || inclAllZC))
      return true;


   return false;
}

bool TxIOPair::hasTxOutInMain(LMDBBlockDatabase *db) const
{
   return (!hasTxOutZC() &&
      hasTxOut() && txRefOfOutput_.attached(db).isMainBranch());
}

bool TxIOPair::hasTxInInMain(LMDBBlockDatabase *db) const
{
   return (!hasTxInZC() &&
      hasTxIn() && txRefOfInput_.attached(db).isMainBranch());
}

bool TxIOPair::hasTxOutZC(void) const
{
   return txRefOfOutput_.getDBKey().startsWith(READHEX("ffff"));
}

bool TxIOPair::hasTxInZC(void) const
{
   return txRefOfInput_.getDBKey().startsWith(READHEX("ffff"));
}

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

bool TxIOPair::operator>=(const BinaryData &dbKey) const
{
   if (txRefOfOutput_ >= dbKey)
      return true;

   if (txRefOfInput_ >= dbKey)
      return true;

   return false;
}

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
   this->isFromSameTx_ = rhs.isFromSameTx_;

   return *this;
}

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
   this->isFromSameTx_ = toMove.isFromSameTx_;

   return *this;
}

void TxIOPair::unserialize(const BinaryDataRef& val)
{
   BinaryRefReader brr(val);

   BitUnpacker<uint8_t> bitunpack(brr);
   isTxOutFromSelf_  = bitunpack.getBit();
   isFromCoinbase_   = bitunpack.getBit();
   bool isSpent      = bitunpack.getBit();
   isMultisig_       = bitunpack.getBit();
   isUTXO_           = bitunpack.getBit();
   isFromSameTx_     = bitunpack.getBit();

   // We always include the 8-byte value
   amount_ = brr.get_uint64_t();

   setTxOut(val.getSliceRef(9, 8));
   if (val.getSize() == 25)
      setTxIn(val.getSliceRef(17, 8));

   //the key always carries the full txout ref
   /*if (!isSpent)
      setTxOut(key);
   else
   {
      //spent subssh, txout key      
      setTxOut(val.getSliceRef(9, 8));

      //when keyed by txins, the top bit in the tx index is always flipped
      BinaryData txinKey(key);
      txinKey.getPtr()[4] &= 0x7F;
      
      //last 8 bytes carry the txin key
      setTxIn(txinKey);
   }*/
}

BinaryData TxIOPair::serializeDbKey(void) const
{
   if (!hasTxIn())
      return getDBKeyOfOutput();
   
   BinaryData bd(getDBKeyOfInput());
   bd.getPtr()[4] |= 0x80;

   return bd;
}

void TxIOPair::serializeDbValue(BinaryWriter& bw) const
{
   uint8_t sersize = 17; //bit pack + amount + txout key

   if (hasTxIn())
      sersize += 8;

   bw.put_uint8_t(sersize);

   BitPacker<uint8_t> bitpacker;

   bitpacker.putBit(isTxOutFromSelf_);
   bitpacker.putBit(isFromCoinbase_);
   bitpacker.putBit(hasTxIn());
   bitpacker.putBit(isMultisig_);
   bitpacker.putBit(isUTXO_);
   bitpacker.putBit(isFromSameTx_);

   bw.put_BitPacker(bitpacker);
   bw.put_uint64_t(amount_);

   bw.put_BinaryData(getDBKeyOfOutput());

   if (hasTxIn())
   {
      bw.put_BinaryData(getDBKeyOfInput());
   }
}