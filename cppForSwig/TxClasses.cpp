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

#include "TxClasses.h"

/////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////
//
// OutPoint methods
//
/////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////
bool OutPoint::operator<(OutPoint const & op2) const
{
   if (txHash_ == op2.txHash_)
      return txOutIndex_ < op2.txOutIndex_;
   else
      return txHash_ < op2.txHash_;
}

/////////////////////////////////////////////////////////////////////////////
bool OutPoint::operator==(OutPoint const & op2) const
{
   return (txHash_ == op2.txHash_ && txOutIndex_ == op2.txOutIndex_);
}

/////////////////////////////////////////////////////////////////////////////
void OutPoint::serialize(BinaryWriter & bw) const
{
   bw.put_BinaryData(txHash_);
   bw.put_uint32_t(txOutIndex_);
}

/////////////////////////////////////////////////////////////////////////////
BinaryData OutPoint::serialize(void) const
{
   BinaryWriter bw(36);
   serialize(bw);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
void OutPoint::unserialize(uint8_t const * ptr, uint32_t size)
{
   if (size < 32)
      throw BlockDeserializingException();

   txHash_.copyFrom(ptr, 32);
   txOutIndex_ = READ_UINT32_LE(ptr + 32);
}

/////////////////////////////////////////////////////////////////////////////
void OutPoint::unserialize(BinaryReader & br)
{
   if (br.getSizeRemaining() < 32)
      throw BlockDeserializingException();
   br.get_BinaryData(txHash_, 32);
   txOutIndex_ = br.get_uint32_t();
}

/////////////////////////////////////////////////////////////////////////////
void OutPoint::unserialize(BinaryRefReader & brr)
{
   if (brr.getSizeRemaining() < 32)
      throw BlockDeserializingException();
   brr.get_BinaryData(txHash_, 32);
   txOutIndex_ = brr.get_uint32_t();
}

/////////////////////////////////////////////////////////////////////////////
void OutPoint::unserialize(BinaryData const & bd)
{
   unserialize(bd.getPtr(), bd.getSize());
}

/////////////////////////////////////////////////////////////////////////////
void OutPoint::unserialize(BinaryDataRef const & bdRef)
{
   unserialize(bdRef.getPtr(), bdRef.getSize());
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// TxIn methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
OutPoint TxIn::getOutPoint(void) const
{
   OutPoint op;
   op.unserialize(getPtr(), getSize());
   return op;
}

/////////////////////////////////////////////////////////////////////////////
BinaryData TxIn::getScript(void) const
{
   uint32_t scrLen = 
      (uint32_t)BtcUtils::readVarInt(getPtr() + 36, getSize() - 36);
   return BinaryData(getPtr() + getScriptOffset(), scrLen);
}

/////////////////////////////////////////////////////////////////////////////
BinaryDataRef TxIn::getScriptRef(void) const
{
   uint32_t scrLen = 
      (uint32_t)BtcUtils::readVarInt(getPtr() + 36, getSize() - 36);
   return BinaryDataRef(getPtr() + getScriptOffset(), scrLen);
}

/////////////////////////////////////////////////////////////////////////////
void TxIn::unserialize_checked(uint8_t const * ptr,
   uint32_t        size,
   uint32_t        nbytes,
   TxRef           parent,
   uint32_t        idx)
{
   parentTx_ = parent;
   index_ = idx;
   uint32_t numBytes = (nbytes == 0 ? BtcUtils::TxInCalcLength(ptr, size) : nbytes);
   if (size < numBytes)
      throw BlockDeserializingException();
   dataCopy_.copyFrom(ptr, numBytes);

   if (dataCopy_.getSize() - 36 < 1)
      throw BlockDeserializingException();
   scriptOffset_ = 36 + BtcUtils::readVarIntLength(getPtr() + 36);

   if (dataCopy_.getSize() < 32)
      throw BlockDeserializingException();
   scriptType_ = BtcUtils::getTxInScriptType(getScriptRef(),
      BinaryDataRef(getPtr(), 32));

   if (!parentTx_.isInitialized())
   {
      parentHeight_ = UINT32_MAX;
      parentHash_ = BinaryData(0);
   }
}

/////////////////////////////////////////////////////////////////////////////
void TxIn::unserialize(BinaryRefReader & brr,
   uint32_t nbytes,
   TxRef parent,
   uint32_t idx)
{
   unserialize_checked(brr.getCurrPtr(), brr.getSizeRemaining(), nbytes, parent, idx);
   brr.advance(getSize());
}

/////////////////////////////////////////////////////////////////////////////
void TxIn::unserialize(BinaryData const & str,
   uint32_t nbytes,
   TxRef parent,
   uint32_t idx)
{
   unserialize_checked(str.getPtr(), str.getSize(), nbytes, parent, idx);
}

/////////////////////////////////////////////////////////////////////////////
void TxIn::unserialize(BinaryDataRef str,
   uint32_t nbytes,
   TxRef parent,
   uint32_t idx)
{
   unserialize_checked(str.getPtr(), str.getSize(), nbytes, parent, idx);
}

/////////////////////////////////////////////////////////////////////////////
// Not all TxIns have this information.  Have to go to the Outpoint and get
// the corresponding TxOut to find the sender.  In the case the sender is
// not available, return false and don't write the output
bool TxIn::getSenderScrAddrIfAvail(BinaryData & addrTarget) const
{
   if (scriptType_ == TXIN_SCRIPT_NONSTANDARD ||
      scriptType_ == TXIN_SCRIPT_COINBASE)
   {
      addrTarget = BtcUtils::BadAddress();
      return false;
   }

   try
   {
      addrTarget = BtcUtils::getTxInAddrFromType(getScript(), scriptType_);
   }
   catch (BlockDeserializingException&)
   {
      return false;
   }
   return true;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData TxIn::getSenderScrAddrIfAvail(void) const
{
   BinaryData addrTarget(20);
   getSenderScrAddrIfAvail(addrTarget);
   return addrTarget;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t TxIn::getParentHeight() const
{
   if (!parentTx_.isInitialized())
      return parentHeight_;
   else
      return parentTx_.getBlockHeight();
}

////////////////////////////////////////////////////////////////////////////////
void TxIn::pprint(ostream & os, int nIndent, bool pBigendian) const
{
   string indent = "";
   for (int i = 0; i<nIndent; i++)
      indent = indent + "   ";

   os << indent << "TxIn:" << endl;
   os << indent << "   Type:    ";
   switch (scriptType_)
   {
   case TXIN_SCRIPT_STDUNCOMPR:  os << "UncomprKey" << endl; break;
   case TXIN_SCRIPT_STDCOMPR:    os << "ComprKey" << endl; break;
   case TXIN_SCRIPT_COINBASE:    os << "Coinbase" << endl; break;
   case TXIN_SCRIPT_SPENDPUBKEY: os << "SpendPubKey" << endl; break;
   case TXIN_SCRIPT_SPENDP2SH:   os << "SpendP2sh" << endl; break;
   case TXIN_SCRIPT_NONSTANDARD: os << "UNKNOWN " << endl; break;
   case TXIN_SCRIPT_SPENDMULTI:  os << "Multi" << endl; break;

   }
   os << indent << "   Bytes:   " << getSize() << endl;
   os << indent << "   Sender:  " << getSenderScrAddrIfAvail().copySwapEndian().toHexStr() << endl;
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// TxOut methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
BinaryData TxOut::getScript(void)
{
   return BinaryData(dataCopy_.getPtr() + scriptOffset_, getScriptSize());
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef TxOut::getScriptRef(void)
{
   return BinaryDataRef(dataCopy_.getPtr() + scriptOffset_, getScriptSize());
}

/////////////////////////////////////////////////////////////////////////////
void TxOut::unserialize_checked(uint8_t const * ptr,
   uint32_t size,
   uint32_t nbytes,
   TxRef parent,
   uint32_t idx)
{
   parentTx_ = parent;
   index_ = idx;
   uint32_t numBytes = (nbytes == 0 ? BtcUtils::TxOutCalcLength(ptr, size) : nbytes);
   if (size < numBytes)
      throw BlockDeserializingException();
   dataCopy_.copyFrom(ptr, numBytes);

   scriptOffset_ = 8 + BtcUtils::readVarIntLength(getPtr() + 8);
   if (dataCopy_.getSize() - scriptOffset_ - getScriptSize() > size)
      throw BlockDeserializingException();
   BinaryDataRef scriptRef(dataCopy_.getPtr() + scriptOffset_, getScriptSize());
   scriptType_ = BtcUtils::getTxOutScriptType(scriptRef);
   uniqueScrAddr_ = BtcUtils::getTxOutScrAddr(scriptRef);

   if (!parentTx_.isInitialized())
   {
      parentHeight_ = UINT32_MAX;
      parentHash_ = BinaryData(0);
   }
}

/////////////////////////////////////////////////////////////////////////////
void TxOut::unserialize(BinaryData const & str,
   uint32_t nbytes,
   TxRef  parent,
   uint32_t idx)
{
   unserialize_checked(str.getPtr(), str.getSize(), nbytes, parent, idx);
}

/////////////////////////////////////////////////////////////////////////////
void TxOut::unserialize(BinaryDataRef const & str,
   uint32_t nbytes,
   TxRef  parent,
   uint32_t idx)
{
   unserialize_checked(str.getPtr(), str.getSize(), nbytes, parent, idx);
}

/////////////////////////////////////////////////////////////////////////////
void TxOut::unserialize(BinaryRefReader & brr,
   uint32_t nbytes,
   TxRef  parent,
   uint32_t idx)
{
   unserialize_checked(brr.getCurrPtr(), brr.getSizeRemaining(), nbytes, parent, idx);
   brr.advance(getSize());
}

////////////////////////////////////////////////////////////////////////////////
uint32_t TxOut::getParentHeight() const
{
   if (!parentTx_.isInitialized())
      return parentHeight_;
   else
      return parentTx_.getBlockHeight();
}

////////////////////////////////////////////////////////////////////////////////
uint32_t TxOut::getParentIndex() const
{
   if (!parentTx_.isInitialized())
      return UINT32_MAX;
   else
      return parentTx_.getBlockTxIndex();
}

/////////////////////////////////////////////////////////////////////////////
void TxOut::pprint(ostream & os, int nIndent, bool pBigendian)
{
   string indent = "";
   for (int i = 0; i<nIndent; i++)
      indent = indent + "   ";

   os << indent << "TxOut:" << endl;
   os << indent << "   Type:   ";
   switch (scriptType_)
   {
   case TXOUT_SCRIPT_STDHASH160:  os << "StdHash160" << endl; break;
   case TXOUT_SCRIPT_STDPUBKEY65: os << "StdPubKey65" << endl; break;
   case TXOUT_SCRIPT_STDPUBKEY33: os << "StdPubKey65" << endl; break;
   case TXOUT_SCRIPT_P2SH:        os << "Pay2ScrHash" << endl; break;
   case TXOUT_SCRIPT_MULTISIG:    os << "Multi" << endl; break;
   case TXOUT_SCRIPT_NONSTANDARD: os << "UNKNOWN " << endl; break;
   }
   os << indent << "   Recip:  "
      << uniqueScrAddr_.toHexStr(pBigendian).c_str()
      << (pBigendian ? " (BE)" : " (LE)") << endl;
   os << indent << "   Value:  " << getValue() << endl;
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// Tx methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
bool Tx::isCoinbase(void) const
{
   if (!isInitialized())
      throw runtime_error("unprocessed tx");

   BinaryDataRef bdr(dataCopy_.getPtr() + offsetsTxIn_[0], 32);
   return bdr == BtcUtils::EmptyHash_;
}

/////////////////////////////////////////////////////////////////////////////
void Tx::unserialize(uint8_t const * ptr, size_t size)
{
   isInitialized_ = false;

   uint32_t nBytes = BtcUtils::TxCalcLength(ptr, size, 
      &offsetsTxIn_, &offsetsTxOut_, &offsetsWitness_);

   if(nBytes > size)
      throw BlockDeserializingException();
   dataCopy_.copyFrom(ptr,nBytes);
   if(8 > size)
      throw BlockDeserializingException();

   usesWitness_ = false;
   auto marker = (const uint16_t*)(ptr + 4);
   if (*marker == 0x0100)
      usesWitness_ = true;

   uint32_t numWitness = offsetsWitness_.size() - 1;
   version_ = READ_UINT32_LE(ptr);
   if(4 > size - offsetsWitness_[numWitness])
      throw BlockDeserializingException();
   lockTime_ = READ_UINT32_LE(ptr + offsetsWitness_[numWitness]);

	isInitialized_ = true;
}

/////////////////////////////////////////////////////////////////////////////
BinaryData Tx::serializeWithMetaData() const
{
   if (txRefObj_.dbKey6B_.getSize() != 6)
      return BinaryData();

   BinaryWriter bw;
   BitPacker<uint8_t> bitpack;
   bitpack.putBit(isRBF_);
   bitpack.putBit(isChainedZc_);

   bw.put_BitPacker(bitpack);
   bw.put_BinaryData(txRefObj_.dbKey6B_);

   bw.put_BinaryData(dataCopy_);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
void Tx::unserializeWithMetaData(const BinaryData& rawTx)
{
   isInitialized_ = false;

   auto size = rawTx.getSize();
   if (size < 7)
      return;

   BinaryRefReader brr(rawTx.getRef());
   BitUnpacker<uint8_t> bitunpack(brr);
   isRBF_ = bitunpack.getBit();
   isChainedZc_ = bitunpack.getBit();
   
   txRefObj_.dbKey6B_ = brr.get_BinaryData(6);

   try
   {
      unserialize(brr);
   }
   catch (...)
   { }
}

/////////////////////////////////////////////////////////////////////////////
BinaryData Tx::serializeNoWitness(void) const
{
   if (!isInitialized())
      throw runtime_error("Tx uninitialized");

   BinaryData dataNoWitness;
   dataNoWitness.append(WRITE_UINT32_LE(version_));
   BinaryDataRef txBody(dataCopy_.getPtr() + 6, offsetsTxOut_.back() - 6);
   dataNoWitness.append(txBody);
   dataNoWitness.append(WRITE_UINT32_LE(lockTime_));

   return dataNoWitness;
}

/////////////////////////////////////////////////////////////////////////////
BinaryData Tx::getThisHash(void) const
{
   if (thisHash_.getSize() == 0)
   {
      if (usesWitness_)
      {
         auto&& dataNoWitness = serializeNoWitness();
         thisHash_ = move(BtcUtils::getHash256(dataNoWitness));
      }
      else
      {
         thisHash_ = move(BtcUtils::getHash256(dataCopy_));
      }
   }

   return thisHash_;
}

/////////////////////////////////////////////////////////////////////////////
void Tx::unserialize(BinaryRefReader & brr)
{
   unserialize(brr.getCurrPtr(), brr.getSizeRemaining());
   brr.advance(getSize());
}

/////////////////////////////////////////////////////////////////////////////
uint64_t Tx::getSumOfOutputs(void)
{
   uint64_t sumVal = 0;
   for (uint32_t i = 0; i<getNumTxOut(); i++)
      sumVal += getTxOutCopy(i).getValue();

   return sumVal;
}

/////////////////////////////////////////////////////////////////////////////
BinaryData Tx::getScrAddrForTxOut(uint32_t txOutIndex)
{
   TxOut txout = getTxOutCopy(txOutIndex);
   return BtcUtils::getTxOutScrAddr(txout.getScript());
}

/////////////////////////////////////////////////////////////////////////////
// This is not a pointer to persistent object, this method actually CREATES
// the TxIn.   But it's fast and doesn't hold a lot of post-construction
// information, so it can probably just be computed on the fly
TxIn Tx::getTxInCopy(int i) const
{
   assert(isInitialized());
   uint32_t txinSize = offsetsTxIn_[i + 1] - offsetsTxIn_[i];
   TxIn out;
   out.unserialize_checked(
      dataCopy_.getPtr() + offsetsTxIn_[i],
      dataCopy_.getSize() - offsetsTxIn_[i],
      txinSize, txRefObj_, i);

   if (txRefObj_.isInitialized())
   {
      out.setParentHash(getThisHash());
      out.setParentHeight(txRefObj_.getBlockHeight());
   }
   return out;
}

/////////////////////////////////////////////////////////////////////////////
// This is not a pointer to persistent object, this method actually CREATES
// the TxOut.   But it's fast and doesn't hold a lot of post-construction
// information, so it can probably just be computed on the fly
TxOut Tx::getTxOutCopy(int i) const
{
   if (!isInitialized())
      int abc = 0;

   assert(isInitialized());
   
   if (i >= offsetsTxOut_.size() - 1)
      throw range_error("index out of bound");

   uint32_t txoutSize = offsetsTxOut_[i + 1] - offsetsTxOut_[i];
   TxOut out;
   out.unserialize_checked(
      dataCopy_.getPtr() + offsetsTxOut_[i], 
      dataCopy_.getSize() - offsetsTxOut_[i], 
      txoutSize, txRefObj_, 
      i);

   out.setParentHash(getThisHash());

   if (txRefObj_.isInitialized())
      out.setParentHeight(txRefObj_.getBlockHeight());

   return out;
}

/////////////////////////////////////////////////////////////////////////////
bool Tx::isRBF() const
{
   if (isRBF_)
      return true;

   for (unsigned i = 0; i < offsetsTxIn_.size() - 1; i++)
   {
      uint32_t sequenceOffset = offsetsTxIn_[i + 1] - 4;
      uint32_t* sequencePtr = (uint32_t*)(dataCopy_.getPtr() + sequenceOffset);

      if (*sequencePtr < 0xFFFFFFFF - 1)
         return true;
   }

   return false;
}

/////////////////////////////////////////////////////////////////////////////
size_t Tx::getTxWeight() const
{
   auto size = getSize();
   
   if (offsetsWitness_.size() > 1)
   {
      auto witnessSize = *offsetsWitness_.rbegin() - *offsetsWitness_.begin();
      float witnessDiscount = float(witnessSize) * 0.75f;

      size -= size_t(witnessDiscount);
   }

   return size;
}

/////////////////////////////////////////////////////////////////////////////
void Tx::pprint(ostream & os, int nIndent, bool pBigendian)
{
   string indent = "";
   for (int i = 0; i<nIndent; i++)
      indent = indent + "   ";

   os << indent << "Tx:   " << thisHash_.toHexStr(pBigendian)
      << (pBigendian ? " (BE)" : " (LE)") << endl;
   if (txRefObj_.isNull())
      os << indent << "   Blk:  <NOT PART OF A BLOCK YET>" << endl;
   else
      os << indent << "   Blk:         " << getBlockHeight() << endl;

   os << indent << "   TxSize:      " << getSize() << " bytes" << endl;
   os << indent << "   NumInputs:   " << getNumTxIn() << endl;
   os << indent << "   NumOutputs:  " << getNumTxOut() << endl;
   os << endl;
   for (uint32_t i = 0; i<getNumTxIn(); i++)
      getTxInCopy(i).pprint(os, nIndent + 1, pBigendian);
   os << endl;
   for (uint32_t i = 0; i<getNumTxOut(); i++)
      getTxOutCopy(i).pprint(os, nIndent + 1, pBigendian);
}

////////////////////////////////////////////////////////////////////////////////
// Need a serious debugging method, that will touch all pointers that are
// supposed to be not NULL.  I'd like to try to force a segfault here, if it
// is going to happen, instead of letting it kill my program where I don't 
// know what happened.
void Tx::pprintAlot(ostream & os)
{
   cout << "Tx hash:   " << thisHash_.toHexStr(true) << endl;
   if (!txRefObj_.isNull())
   {
      cout << "HeaderNum: " << getBlockHeight() << endl;
      //cout << "HeadHash:  " << getBlockHash().toHexStr(true) << endl;
   }

   cout << endl << "NumTxIn:   " << getNumTxIn() << endl;
   for (uint32_t i = 0; i<getNumTxIn(); i++)
   {
      TxIn txin = getTxInCopy(i);
      cout << "   TxIn: " << i << endl;
      cout << "      Siz:  " << txin.getSize() << endl;
      cout << "      Scr:  " << txin.getScriptSize() << "  Type: "
         << (int)txin.getScriptType() << endl;
      cout << "      OPR:  " << txin.getOutPoint().getTxHash().toHexStr(true)
         << txin.getOutPoint().getTxOutIndex() << endl;
      cout << "      Seq:  " << txin.getSequence() << endl;
   }

   cout << endl << "NumTxOut:   " << getNumTxOut() << endl;
   for (uint32_t i = 0; i<getNumTxOut(); i++)
   {
      TxOut txout = getTxOutCopy(i);
      cout << "   TxOut: " << i << endl;
      cout << "      Siz:  " << txout.getSize() << endl;
      cout << "      Scr:  " << txout.getScriptSize() << "  Type: "
         << (int)txout.getScriptType() << endl;
      cout << "      Val:  " << txout.getValue() << endl;
   }

}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// TxRef methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////////////
uint32_t TxRef::getBlockHeight(void) const
{
   if (dbKey6B_.getSize() == 6 && 
      !dbKey6B_.startsWith(DBUtils::ZeroConfHeader_))
      return DBUtils::hgtxToHeight(dbKey6B_.getSliceCopy(0, 4));
   else
      return UINT32_MAX;
}

/////////////////////////////////////////////////////////////////////////////
uint8_t TxRef::getDuplicateID(void) const
{
   if (dbKey6B_.getSize() == 6)
      return DBUtils::hgtxToDupID(dbKey6B_.getSliceCopy(0, 4));
   else
      return UINT8_MAX;
}

/////////////////////////////////////////////////////////////////////////////
uint16_t TxRef::getBlockTxIndex(void) const
{
   if (dbKey6B_.getSize() == 6)
   {
      if (!dbKey6B_.startsWith(DBUtils::ZeroConfHeader_))
         return READ_UINT16_BE(dbKey6B_.getPtr() + 4);
      else
         return READ_UINT32_BE(dbKey6B_.getPtr() + 2);
   }
   else
      return UINT16_MAX;
}


/////////////////////////////////////////////////////////////////////////////
void TxRef::pprint(ostream & os, int nIndent) const
{
   os << "TxRef Information:" << endl;
   //os << "   Hash:      " << getThisHash().toHexStr() << endl;
   os << "   Height:    " << getBlockHeight() << endl;
   os << "   BlkIndex:  " << getBlockTxIndex() << endl;
   //os << "   FileIdx:   " << blkFilePtr_.getFileIndex() << endl;
   //os << "   FileStart: " << blkFilePtr_.getStartByte() << endl;
   //os << "   NumBytes:  " << blkFilePtr_.getNumBytes() << endl;
   os << "   ----- " << endl;
   os << "   Read from disk, full tx-info: " << endl;
   //getTxCopy().pprint(os, nIndent+1); 
}

/////////////////////////////////////////////////////////////////////////////
void TxRef::setRef(BinaryDataRef bdr)
{
   dbKey6B_ = bdr.copy();
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// UTXO methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BinaryData UTXO::serialize() const
{
   BinaryWriter bw;
   //8 + 4 + 2 + 2 + 32 + scriptsize
   bw.reserve(18 + txHash_.getSize() + script_.getSize());
   bw.put_uint64_t(value_);
   bw.put_uint32_t(txHeight_);
   bw.put_uint16_t(txIndex_);
   bw.put_uint16_t(txOutIndex_);
   
   bw.put_var_int(txHash_.getSize());
   bw.put_BinaryData(txHash_);

   bw.put_var_int(script_.getSize());
   bw.put_BinaryData(script_);
   bw.put_uint32_t(preferredSequence_);

   return move(bw.getData());
}

////////////////////////////////////////////////////////////////////////////////
void UTXO::unserialize(const BinaryData& data)
{
   if (data.getSize() < 18)
      throw runtime_error("invalid raw utxo size");
   
   BinaryRefReader brr(data.getRef());


   value_ = brr.get_uint64_t();
   txHeight_ = brr.get_uint32_t();
   txIndex_ = brr.get_uint16_t();
   txOutIndex_ = brr.get_uint16_t();

   auto hashSize = brr.get_var_int();
   txHash_ = move(brr.get_BinaryData(hashSize));

   auto scriptSize = brr.get_var_int();
   if (scriptSize == 0)
      throw runtime_error("no script data in raw utxo");
   script_ = move(brr.get_BinaryData(scriptSize));

   preferredSequence_ = brr.get_uint32_t();
}

////////////////////////////////////////////////////////////////////////////////
void UTXO::unserializeRaw(const BinaryData& data)
{
   BinaryRefReader brr(data.getRef());
   value_ = brr.get_uint64_t();
   auto scriptSize = brr.get_var_int();
   script_ = brr.get_BinaryData(scriptSize);
}

////////////////////////////////////////////////////////////////////////////////
unsigned UTXO::getInputRedeemSize(void) const
{
   if (txinRedeemSizeBytes_ == UINT32_MAX)
      throw runtime_error("redeem size is no set");

   return txinRedeemSizeBytes_;
}

////////////////////////////////////////////////////////////////////////////////
unsigned UTXO::getWitnessDataSize(void) const
{
   if (!isSegWit() || witnessDataSizeBytes_ == UINT32_MAX)
      throw runtime_error("no witness data size available");

   return witnessDataSizeBytes_;
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// AddressBookEntry methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BinaryData AddressBookEntry::serialize(void) const
{
   BinaryWriter bw;
   bw.reserve(8 + scrAddr_.getSize() + txHashList_.size() * 32);

   bw.put_var_int(scrAddr_.getSize());
   bw.put_BinaryData(scrAddr_);
   bw.put_var_int(txHashList_.size());
   
   for (auto& hash : txHashList_)
      bw.put_BinaryData(hash);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
void AddressBookEntry::unserialize(const BinaryData& data)
{
   if (data.getSize() < 2)
      throw runtime_error("invalid serialized AddressBookEntry");

   BinaryRefReader brr(data.getRef());
   
   auto addrSize = brr.get_var_int();

   if (brr.getSizeRemaining() < addrSize + 1)
      throw runtime_error("invalid serialized AddressBookEntry");
   scrAddr_ = move(brr.get_BinaryData(addrSize));

   auto hashListCount = brr.get_var_int();
   if (brr.getSizeRemaining() != hashListCount * 32)
      throw runtime_error("invalid serialized AddressBookEntry");

   for (unsigned i = 0; i < hashListCount; i++)
   {
      auto&& hash = brr.get_BinaryData(32);
      txHashList_.push_back(move(hash));
   }
}
