////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2014, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include <iostream>
#include <vector>
#include <map>
#include <cmath>
#include <algorithm>

#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockObj.h"
#include "leveldb_wrapper.h"




////////////////////////////////////////////////////////////////////////////////
void BlockHeader::unserialize(uint8_t const * ptr, uint32_t size)
{
   if (size < HEADER_SIZE)
      throw BlockDeserializingException();
   dataCopy_.copyFrom(ptr, HEADER_SIZE);
   BtcUtils::getHash256(dataCopy_.getPtr(), HEADER_SIZE, thisHash_);
   difficultyDbl_ = BtcUtils::convertDiffBitsToDouble( 
                              BinaryDataRef(dataCopy_.getPtr()+72, 4));
   isInitialized_ = true;
   nextHash_ = BinaryData(0);
   blockHeight_ = UINT32_MAX;
   difficultySum_ = -1;
   isMainBranch_ = false;
   isOrphan_ = true;
   //txPtrList_ = vector<TxRef*>(0);
   numTx_ = UINT32_MAX;
}

////////////////////////////////////////////////////////////////////////////////
void BlockHeader::unserialize(BinaryDataRef const & str) 
{ 
   unserialize(str.getPtr(), str.getSize()); 
}

////////////////////////////////////////////////////////////////////////////////
void BlockHeader::unserialize(BinaryRefReader & brr) 
{ 
   unserialize(brr.get_BinaryDataRef(HEADER_SIZE)); 
}




/////////////////////////////////////////////////////////////////////////////
void BlockHeader::pprint(ostream & os, int nIndent, bool pBigendian) const
{
   string indent = "";
   for(int i=0; i<nIndent; i++)
      indent = indent + "   ";

   string endstr = (pBigendian ? " (BE)" : " (LE)");
   os << indent << "Block Information: " << blockHeight_ << endl;
   os << indent << "   Hash:       " 
                << getThisHash().toHexStr(pBigendian).c_str() << endstr << endl;
   os << indent << "   Timestamp:  " << getTimestamp() << endl;
   os << indent << "   Prev Hash:  " 
                << getPrevHash().toHexStr(pBigendian).c_str() << endstr << endl;
   os << indent << "   MerkleRoot: " 
                << getMerkleRoot().toHexStr(pBigendian).c_str() << endstr << endl;
   os << indent << "   Difficulty: " << (difficultyDbl_)
                         << "    (" << getDiffBits().toHexStr().c_str() << ")" << endl;
   os << indent << "   CumulDiff:  " << (difficultySum_) << endl;
   os << indent << "   Nonce:      " << getNonce() << endl;
}

////////////////////////////////////////////////////////////////////////////////
void BlockHeader::pprintAlot(ostream & os)
{
   cout << "Header:   " << getBlockHeight() << endl;
   cout << "Hash:     " << getThisHash().toHexStr(true)  << endl;
   cout << "Hash:     " << getThisHash().toHexStr(false) << endl;
   cout << "PrvHash:  " << getPrevHash().toHexStr(true)  << endl;
   cout << "PrvHash:  " << getPrevHash().toHexStr(false) << endl;
   cout << "this*:    " << this << endl;
   cout << "TotSize:  " << getBlockSize() << endl;
   cout << "Tx Count: " << numTx_ << endl;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t BlockHeader::findNonce(void)
{
   BinaryData playHeader(serialize());
   BinaryData fourZeros = BinaryData::CreateFromHex("00000000");
   BinaryData hashResult(32);
   for(uint32_t nonce=0; nonce<(uint32_t)(-1); nonce++)
   {
      *(uint32_t*)(playHeader.getPtr()+76) = nonce;
      BtcUtils::getHash256_NoSafetyCheck(playHeader.getPtr(), HEADER_SIZE, hashResult);
      if(hashResult.getSliceRef(28,4) == fourZeros)
      {
         cout << "NONCE FOUND! " << nonce << endl;
         unserialize(playHeader);
         cout << "Raw Header: " << serialize().toHexStr() << endl;
         pprint();
         cout << "Hash:       " << hashResult.toHexStr() << endl;
         return nonce;
      }

      if(nonce % 10000000 == 0)
      {
         cout << ".";
         cout.flush();
      }
   }
   cout << "No nonce found!" << endl;
   return 0;
   // We have to change the coinbase script, recompute merkle root, and then
   // can cycle through all the nonces again.
}




/////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////
//
// OutPoint methods
//
/////////////////////////////////////////////////////////////////////////////
/////////////////////////////////////////////////////////////////////////////
// Define these operators so that we can use OutPoint as a map<> key
bool OutPoint::operator<(OutPoint const & op2) const
{
   if(txHash_ == op2.txHash_)
      return txOutIndex_ < op2.txOutIndex_;
   else
      return txHash_ < op2.txHash_;
}
bool OutPoint::operator==(OutPoint const & op2) const
{
   return (txHash_ == op2.txHash_ && txOutIndex_ == op2.txOutIndex_);
}

void OutPoint::serialize(BinaryWriter & bw) const
{
   bw.put_BinaryData(txHash_);
   bw.put_uint32_t(txOutIndex_);
}

BinaryData OutPoint::serialize(void) const
{
   BinaryWriter bw(36);
   serialize(bw);
   return bw.getData();
}

void OutPoint::unserialize(uint8_t const * ptr, uint32_t size)
{
   if (size < 32)
      throw BlockDeserializingException();

   txHash_.copyFrom(ptr, 32);
   txOutIndex_ = READ_UINT32_LE(ptr+32);
}
void OutPoint::unserialize(BinaryReader & br)
{
   if (br.getSizeRemaining() < 32)
      throw BlockDeserializingException();
   br.get_BinaryData(txHash_, 32);
   txOutIndex_ = br.get_uint32_t();
}
void OutPoint::unserialize(BinaryRefReader & brr)
{
   if (brr.getSizeRemaining() < 32)
      throw BlockDeserializingException();
   brr.get_BinaryData(txHash_, 32);
   txOutIndex_ = brr.get_uint32_t();
}


void OutPoint::unserialize(BinaryData const & bd) 
{ 
   unserialize(bd.getPtr(), bd.getSize());
}
void OutPoint::unserialize(BinaryDataRef const & bdRef) 
{ 
   unserialize(bdRef.getPtr(), bdRef.getSize());
}

const BinaryDataRef OutPoint::getDBkey(InterfaceToLDB* db) const
{
   if (DBkey_.getSize() == 8)
      return DBkey_;

   if (db != nullptr)
   {
      if (db->getStoredTx_byHash(txHash_, nullptr, &DBkey_))
      {
         DBkey_.append(WRITE_UINT16_BE((uint16_t)txOutIndex_));
         return DBkey_;
      }
   }

   return BinaryDataRef();
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
   uint32_t scrLen = (uint32_t)BtcUtils::readVarInt(getPtr()+36);
   return BinaryData(getPtr() + getScriptOffset(), scrLen);
}

/////////////////////////////////////////////////////////////////////////////
BinaryDataRef TxIn::getScriptRef(void) const
{ 
   uint32_t scrLen = (uint32_t)BtcUtils::readVarInt(getPtr()+36);
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
   uint32_t numBytes = (nbytes==0 ? BtcUtils::TxInCalcLength(ptr, size) : nbytes);
   if (size < numBytes)
      throw BlockDeserializingException();
   dataCopy_.copyFrom(ptr, numBytes);

   if (dataCopy_.getSize()-36 < 1)
      throw BlockDeserializingException();
   scriptOffset_ = 36 + BtcUtils::readVarIntLength(getPtr()+36);

   if (dataCopy_.getSize() < 32)
      throw BlockDeserializingException();
   scriptType_ = BtcUtils::getTxInScriptType(getScriptRef(),
                                             BinaryDataRef(getPtr(),32));

   if(!parentTx_.isInitialized())
   {
      parentHeight_ = UINT32_MAX;
      parentHash_   = BinaryData(0);
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
   if(scriptType_ == TXIN_SCRIPT_NONSTANDARD ||
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
BinaryData TxIn::getParentHash(InterfaceToLDB *db)
{
   if(!parentTx_.isInitialized())
      return parentHash_;
   else
      return parentTx_.attached(db).getThisHash();
}


////////////////////////////////////////////////////////////////////////////////
uint32_t TxIn::getParentHeight() const
{
   if(!parentTx_.isInitialized())
      return parentHeight_;
   else
      return parentTx_.getBlockHeight();
}


////////////////////////////////////////////////////////////////////////////////
void TxIn::pprint(ostream & os, int nIndent, bool pBigendian) const
{
   string indent = "";
   for(int i=0; i<nIndent; i++)
      indent = indent + "   ";

   os << indent << "TxIn:" << endl;
   os << indent << "   Type:    ";
   switch(scriptType_)
   {
      case TXIN_SCRIPT_STDUNCOMPR:  os << "UncomprKey" << endl; break;
      case TXIN_SCRIPT_STDCOMPR:    os << "ComprKey" << endl; break;
      case TXIN_SCRIPT_COINBASE:    os << "Coinbase" << endl; break;
      case TXIN_SCRIPT_SPENDPUBKEY: os << "SpendPubKey" << endl; break;
      case TXIN_SCRIPT_SPENDP2SH:   os << "SpendP2sh" << endl; break;
      case TXIN_SCRIPT_NONSTANDARD: os << "UNKNOWN " << endl; break;
   }
   os << indent << "   Bytes:   " << getSize() << endl;
   os << indent << "   Sender:  " << getSenderScrAddrIfAvail().toHexStr() << endl;
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
   return BinaryData( dataCopy_.getPtr()+scriptOffset_, getScriptSize() );
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef TxOut::getScriptRef(void) 
{ 
   return BinaryDataRef( dataCopy_.getPtr()+scriptOffset_, getScriptSize() );
}

/////////////////////////////////////////////////////////////////////////////
void TxOut::unserialize_checked( uint8_t const * ptr,
                         uint32_t size,
                         uint32_t nbytes,
                         TxRef parent,
                         uint32_t idx)
{
   parentTx_ = parent;
   index_ = idx;
   uint32_t numBytes = (nbytes==0 ? BtcUtils::TxOutCalcLength(ptr) : nbytes);
   if (size < numBytes)
      throw BlockDeserializingException();
   dataCopy_.copyFrom(ptr, numBytes);

   scriptOffset_ = 8 + BtcUtils::readVarIntLength(getPtr()+8);
   if (dataCopy_.getSize()-scriptOffset_-getScriptSize() > size)
      throw BlockDeserializingException();
   BinaryDataRef scriptRef(dataCopy_.getPtr()+scriptOffset_, getScriptSize());
   scriptType_ = BtcUtils::getTxOutScriptType(scriptRef);
   uniqueScrAddr_ = BtcUtils::getTxOutScrAddr(scriptRef);

   if(!parentTx_.isInitialized())
   {
      parentHeight_ = UINT32_MAX;
      parentHash_   = BinaryData(0);
   }
}

/////////////////////////////////////////////////////////////////////////////
void TxOut::unserialize( BinaryData const & str,
                         uint32_t nbytes,
                         TxRef  parent,
                         uint32_t idx)
{
   unserialize_checked(str.getPtr(), str.getSize(), nbytes, parent, idx);
}

/////////////////////////////////////////////////////////////////////////////
void TxOut::unserialize( BinaryDataRef const & str,
                         uint32_t nbytes,
                         TxRef  parent,
                         uint32_t idx)
{
   unserialize_checked(str.getPtr(), str.getSize(), nbytes, parent, idx);
}

/////////////////////////////////////////////////////////////////////////////
void TxOut::unserialize( BinaryRefReader & brr,
                         uint32_t nbytes,
                         TxRef  parent,
                         uint32_t idx)
{
   unserialize_checked( brr.getCurrPtr(), brr.getSizeRemaining(), nbytes, parent, idx );
   brr.advance(getSize());
}

////////////////////////////////////////////////////////////////////////////////
uint32_t TxOut::getParentHeight() const
{
   if(!parentTx_.isInitialized())
      return parentHeight_;
   else
      return parentTx_.getBlockHeight();

}

BinaryData TxOut::getParentHash(InterfaceToLDB *db)
{
   if(!parentTx_.isInitialized())
      return parentHash_;
   else
      return parentTx_.attached(db).getThisHash();
}


/////////////////////////////////////////////////////////////////////////////
void TxOut::pprint(ostream & os, int nIndent, bool pBigendian) 
{
   string indent = "";
   for(int i=0; i<nIndent; i++)
      indent = indent + "   ";

   os << indent << "TxOut:" << endl;
   os << indent << "   Type:   ";
   switch(scriptType_)
   {
   case TXOUT_SCRIPT_STDHASH160:  os << "StdHash160" << endl; break;
   case TXOUT_SCRIPT_STDPUBKEY65: os << "StdPubKey65" << endl; break;
   case TXOUT_SCRIPT_STDPUBKEY33: os << "StdPubKey65" << endl; break;
   case TXOUT_SCRIPT_P2SH:        os << "Pay2ScrHash" << endl; break;
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

/////////////////////////////////////////////////////////////////////////////
void Tx::unserialize(uint8_t const * ptr, uint32_t size)
{
   uint32_t nBytes = BtcUtils::TxCalcLength(ptr, size, &offsetsTxIn_, &offsetsTxOut_);
   
   if (nBytes > size)
      throw BlockDeserializingException();
   dataCopy_.copyFrom(ptr, nBytes);
   BtcUtils::getHash256(ptr, nBytes, thisHash_);
   if (8 > size)
      throw BlockDeserializingException();

   uint32_t numTxOut = offsetsTxOut_.size()-1;
   version_  = READ_UINT32_LE(ptr);
   if (4 > size - offsetsTxOut_[numTxOut])
      throw BlockDeserializingException();
   lockTime_ = READ_UINT32_LE(ptr + offsetsTxOut_[numTxOut]);

   isInitialized_ = true;
   //headerPtr_ = NULL;
}


/////////////////////////////////////////////////////////////////////////////
BinaryData Tx::getThisHash(void) const
{
   return BtcUtils::getHash256(dataCopy_.getPtr(), dataCopy_.getSize());
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
   for(uint32_t i=0; i<getNumTxOut(); i++)
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
   uint32_t txinSize = offsetsTxIn_[i+1] - offsetsTxIn_[i];
   TxIn out;
   out.unserialize_checked(dataCopy_.getPtr()+offsetsTxIn_[i], dataCopy_.getSize()-offsetsTxIn_[i], txinSize, txRefObj_, i);
   
   if(txRefObj_.isInitialized())
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
   assert(isInitialized());
   uint32_t txoutSize = offsetsTxOut_[i+1] - offsetsTxOut_[i];
   TxOut out;
   out.unserialize_checked(dataCopy_.getPtr()+offsetsTxOut_[i], dataCopy_.getSize()-offsetsTxOut_[i], txoutSize, txRefObj_, i);
   out.setParentHash(getThisHash());

   if(txRefObj_.isInitialized())
      out.setParentHeight(txRefObj_.getBlockHeight());

   return out;
}


/////////////////////////////////////////////////////////////////////////////
void Tx::pprint(ostream & os, int nIndent, bool pBigendian) 
{
   string indent = "";
   for(int i=0; i<nIndent; i++)
      indent = indent + "   ";
    
   os << indent << "Tx:   " << thisHash_.toHexStr(pBigendian) 
                << (pBigendian ? " (BE)" : " (LE)") << endl;
   if( txRefObj_.isNull())
      os << indent << "   Blk:  <NOT PART OF A BLOCK YET>" << endl;
   else
      os << indent << "   Blk:         " << getBlockHeight() << endl;

   os << indent << "   TxSize:      " << getSize() << " bytes" << endl;
   os << indent << "   NumInputs:   " << getNumTxIn() << endl;
   os << indent << "   NumOutputs:  " << getNumTxOut() << endl;
   os << endl;
   for(uint32_t i=0; i<getNumTxIn(); i++)
      getTxInCopy(i).pprint(os, nIndent+1, pBigendian);
   os << endl;
   for(uint32_t i=0; i<getNumTxOut(); i++)
      getTxOutCopy(i).pprint(os, nIndent+1, pBigendian);
}

////////////////////////////////////////////////////////////////////////////////
// Need a serious debugging method, that will touch all pointers that are
// supposed to be not NULL.  I'd like to try to force a segfault here, if it
// is going to happen, instead of letting it kill my program where I don't 
// know what happened.
void Tx::pprintAlot(ostream & os)
{
   cout << "Tx hash:   " << thisHash_.toHexStr(true) << endl;
   if(!txRefObj_.isNull())
   {
      cout << "HeaderNum: " << getBlockHeight() << endl;
      //cout << "HeadHash:  " << getBlockHash().toHexStr(true) << endl;
   }

   cout << endl << "NumTxIn:   " << getNumTxIn() << endl;
   for(uint32_t i=0; i<getNumTxIn(); i++)
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

   cout << endl <<  "NumTxOut:   " << getNumTxOut() << endl;
   for(uint32_t i=0; i<getNumTxOut(); i++)
   {
      TxOut txout = getTxOutCopy(i);
      cout << "   TxOut: " << i << endl;
      cout << "      Siz:  " << txout.getSize() << endl;
      cout << "      Scr:  " << txout.getScriptSize() << "  Type: " 
                        << (int)txout.getScriptType() << endl;
      cout << "      Val:  " << txout.getValue() << endl;
   }

}



/////////////////////////////////////////////////////////////////////////////
BinaryData DBTxRef::serialize(void) const 
{ 
   return db_->getFullTxCopy(dbKey6B_).serialize();
}


/////////////////////////////////////////////////////////////////////////////
Tx DBTxRef::getTxCopy(void) const
{
   return db_->getFullTxCopy(dbKey6B_);
}

/////////////////////////////////////////////////////////////////////////////
bool DBTxRef::isMainBranch(void) const
{
   if(dbKey6B_.getSize() != 6)
      return false;
   else
   {
      uint8_t dup8 = db_->getValidDupIDForHeight(getBlockHeight());
      return (getDuplicateID() == dup8);
   }
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBTxRef::getThisHash(void) const
{
   return db_->getTxHashForLdbKey(dbKey6B_);
}

/////////////////////////////////////////////////////////////////////////////
void TxRef::setRef(BinaryDataRef bdr)
{
   dbKey6B_ = bdr.copy();
}

/////////////////////////////////////////////////////////////////////////////
uint32_t DBTxRef::getBlockTimestamp() const
{
   StoredHeader sbh;

   if(dbKey6B_.getSize() == 6)
   {
      db_->getStoredHeader(sbh, getBlockHeight(), getDuplicateID(), false);
      return READ_UINT32_LE(sbh.dataCopy_.getPtr()+68);
   }
   else
      return UINT32_MAX;
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBTxRef::getBlockHash(void) const
{
   StoredHeader sbh;
   if(dbKey6B_.getSize() == 6)
   {
      db_->getStoredHeader(sbh, getBlockHeight(), getDuplicateID(), false);
      return sbh.thisHash_;
   }
   else
      return BtcUtils::EmptyHash();
}


/////////////////////////////////////////////////////////////////////////////
uint32_t TxRef::getBlockHeight(void) const
{
   if(dbKey6B_.getSize() == 6)
      return DBUtils::hgtxToHeight(dbKey6B_.getSliceCopy(0,4));
   else
      return UINT32_MAX;
}

/////////////////////////////////////////////////////////////////////////////
uint8_t TxRef::getDuplicateID(void) const
{
   if(dbKey6B_.getSize() == 6)
      return DBUtils::hgtxToDupID(dbKey6B_.getSliceCopy(0,4));
   else
      return UINT8_MAX;
}

/////////////////////////////////////////////////////////////////////////////
uint16_t TxRef::getBlockTxIndex(void) const
{
   if(dbKey6B_.getSize() == 6)
      return READ_UINT16_BE(dbKey6B_.getPtr() + 4);
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


////////////////////////////////////////////////////////////////////////////////
TxIn  DBTxRef::getTxInCopy(uint32_t i)  
{
   return db_->getTxInCopy( dbKey6B_, i);
}

////////////////////////////////////////////////////////////////////////////////
TxOut DBTxRef::getTxOutCopy(uint32_t i)
{
   return db_->getTxOutCopy(dbKey6B_, i);
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// TxIOPair Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(void) : 
   amount_(0),
   indexOfOutput_(0),
   indexOfInput_(0),
   isTxOutFromSelf_(false),
   isFromCoinbase_(false),
   isMultisig_(false)
   {}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(uint64_t  amount) :
   amount_(amount),
   indexOfOutput_(0),
   indexOfInput_(0),
   isTxOutFromSelf_(false),
   isFromCoinbase_(false),
   isMultisig_(false)
   {}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(TxRef txPtrO, uint32_t txoutIndex) :
   amount_(0),
   indexOfInput_(0) ,
   isTxOutFromSelf_(false),
   isFromCoinbase_(false),
   isMultisig_(false)
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
   isMultisig_(false)
{ 
   setTxOut(txPtrO, txoutIndex);
   setTxIn (txPtrI, txinIndex );
}

//////////////////////////////////////////////////////////////////////////////
TxIOPair::TxIOPair(BinaryData txOutKey8B, uint64_t val) :
   amount_(val),
   indexOfOutput_(0),
   indexOfInput_(0),
   isTxOutFromSelf_(false),
   isFromCoinbase_(false),
   isMultisig_(false)
{
   setTxOut(txOutKey8B);
}
 //////////////////////////////////////////////////////////////////////////////
HashString TxIOPair::getTxHashOfOutput(InterfaceToLDB *db) const
{
   if (!hasTxOut())
      return BtcUtils::EmptyHash();
   else if (txHashOfOutput_.getSize() == 32)
      return txHashOfOutput_;
   else if (txRefOfOutput_.isInitialized())
   {
      txHashOfOutput_ = txRefOfOutput_.attached(db).getThisHash();
      return txHashOfOutput_;
   }
   else
      return BinaryData(0);
}

//////////////////////////////////////////////////////////////////////////////
HashString TxIOPair::getTxHashOfInput(InterfaceToLDB *db) const
{
   if (!hasTxIn())
      return BtcUtils::EmptyHash();
   else if (txHashOfInput_.getSize() == 32)
      return txHashOfInput_;
   else if (txRefOfInput_.isInitialized())
   {
      txHashOfInput_ = txRefOfInput_.attached(db).getThisHash();
      return txHashOfInput_;
   }
   else
      return BinaryData(0);
}
//////////////////////////////////////////////////////////////////////////////
TxOut TxIOPair::getTxOutCopy(InterfaceToLDB *db) const
{
   // I actually want this to segfault when there is no TxOut... 
   // we should't ever be trying to access it without checking it 
   // first in the calling code (hasTxOut/hasTxOutZC)
   if(hasTxOut())
      return txRefOfOutput_.attached(db).getTxOutCopy(indexOfOutput_);
   /*else
      return getTxOutZC();*/
}


//////////////////////////////////////////////////////////////////////////////
TxIn TxIOPair::getTxInCopy(InterfaceToLDB *db) const
{
   // I actually want this to segfault when there is no TxIn... 
   // we should't ever be trying to access it without checking it 
   // first in the calling code (hasTxIn/hasTxInZC)
   if(hasTxIn())
      return txRefOfInput_.attached(db).getTxInCopy(indexOfInput_);
   /*else
      return getTxInZC();*/
}


//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::setTxIn(TxRef  txref, uint32_t index)
{ 
   txRefOfInput_  = txref;
   indexOfInput_  = index;

   return true;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::setTxIn(BinaryData dbKey8B)
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
bool TxIOPair::setTxOut(BinaryData dbKey8B)
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
   txRefOfOutput_   = txref; 
   indexOfOutput_   = index;
   return true;
}


//////////////////////////////////////////////////////////////////////////////
pair<bool,bool> TxIOPair::reassessValidity(InterfaceToLDB *db)
{
   pair<bool,bool> result;
   result.first  = hasTxOutInMain(db);
   result.second = hasTxInInMain(db);
   return result;
}


//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isSpent(InterfaceToLDB *db) const
{ 
   // Not sure whether we should verify hasTxOut.  It wouldn't make much 
   // sense to have TxIn but not TxOut, but there might be a preferred 
   // behavior in such awkward circumstances
   return (hasTxInZC() || hasTxInInMain(db));
}


//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isUnspent(InterfaceToLDB *db) const
{ 
   return ( (hasTxOutZC() || hasTxOutInMain(db)) && !isSpent(db));

}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isSpendable(InterfaceToLDB *db, 
                           uint32_t currBlk, bool ignoreAllZeroConf) const
{ 
   // Spendable TxOuts are ones with at least 1 confirmation, or zero-conf
   // TxOuts that were sent-to-self.  Obviously, they should be unspent, too
   if ( hasTxInZC() ||hasTxInInMain(db))
      return false;
   
   if( hasTxOutInMain(db) )
   {
      uint32_t nConf = currBlk - txRefOfOutput_.getBlockHeight() + 1;
      if(isFromCoinbase_ && nConf<=COINBASE_MATURITY)
         return false;
      else
         return true;
   }

   if( hasTxOutZC() && isTxOutFromSelf() )
      return !ignoreAllZeroConf;

   return false;
}

//////////////////////////////////////////////////////////////////////////////
bool TxIOPair::isMineButUnconfirmed(
   InterfaceToLDB *db,
   uint32_t currBlk, bool inclAllZC
) const
{
   // All TxOuts that were from our own transactions are always confirmed
   if(isTxOutFromSelf())
      return false;   

   if (hasTxInZC() || (hasTxIn() && txRefOfInput_.attached(db).isMainBranch()))
      return false;

   if(hasTxOutInMain(db))
   {
      uint32_t nConf = currBlk - txRefOfOutput_.getBlockHeight() + 1;
      if(isFromCoinbase_)
         return (nConf<COINBASE_MATURITY);
      else 
         return (nConf<MIN_CONFIRMATIONS);
   }
   else if( hasTxOutZC() && (!isTxOutFromSelf() || inclAllZC))
      return true;


   return false;
}

bool TxIOPair::hasTxOutInMain(InterfaceToLDB *db) const
{
   return (hasTxOut() && txRefOfOutput_.attached(db).isMainBranch());
}

bool TxIOPair::hasTxInInMain(InterfaceToLDB *db) const
{
   return (hasTxIn() && txRefOfInput_.attached(db).isMainBranch());
}

bool TxIOPair::hasTxOutZC(void) const
{ 
   return txRefOfOutput_.getDBKey().startsWith(READHEX("ffff"));
}

bool TxIOPair::hasTxInZC(void) const
{ 
   return txRefOfInput_.getDBKey().startsWith(READHEX("ffff"));
}

void TxIOPair::pprintOneLine(InterfaceToLDB *db) const
{
   printf("   Val:(%0.3f)\t  (STS, O,I, Omb,Imb, Oz,Iz)  %d  %d%d %d%d %d%d\n", 
           (double)getValue()/1e8,
           (isTxOutFromSelf() ? 1 : 0),
           (hasTxOut() ? 1 : 0),
           (hasTxIn() ? 1 : 0),
           (hasTxOutInMain(db) ? 1 : 0),
           (hasTxInInMain(db) ? 1 : 0),
           (hasTxOutZC() ? 1 : 0),
           (hasTxInZC() ? 1 : 0));

}







////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// UnspentTxOut Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
UnspentTxOut::UnspentTxOut(void) :
   txHash_(BtcUtils::EmptyHash()),
   txOutIndex_(0),
   txHeight_(0),
   value_(0),
   script_(BinaryData(0)),
   numConfirm_(0),
   isMultisigRef_(false)
{
   // Nothing to do here
}

////////////////////////////////////////////////////////////////////////////////
void UnspentTxOut::init(InterfaceToLDB *db, TxOut & txout, uint32_t blkNum, bool isMulti)
{
   txHash_     = txout.getParentHash(db);
   txOutIndex_ = txout.getIndex();
   txHeight_   = txout.getParentHeight();
   value_      = txout.getValue();
   script_     = txout.getScript();
   updateNumConfirm(blkNum);
   isMultisigRef_ = isMulti;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData UnspentTxOut::getRecipientScrAddr(void) const
{
   return BtcUtils::getTxOutScrAddr(getScript());
}


////////////////////////////////////////////////////////////////////////////////
uint32_t UnspentTxOut::updateNumConfirm(uint32_t currBlkNum)
{
   if(txHeight_ == UINT32_MAX)
      numConfirm_ = 0;
   else
      numConfirm_ = currBlkNum - txHeight_ + 1;
   return numConfirm_;
}

////////////////////////////////////////////////////////////////////////////////
bool UnspentTxOut::CompareNaive(UnspentTxOut const & uto1, 
                                UnspentTxOut const & uto2)
{
   float val1 = (float)uto1.getValue();
   float val2 = (float)uto2.getValue();
   return (val1*uto1.numConfirm_ < val2*uto2.numConfirm_);
}

////////////////////////////////////////////////////////////////////////////////
bool UnspentTxOut::CompareTech1(UnspentTxOut const & uto1,
                                UnspentTxOut const & uto2)
{
   float val1 = pow((float)uto1.getValue(), 1.0f/3.0f);
   float val2 = pow((float)uto2.getValue(), 1.0f/3.0f);
   return (val1*uto1.numConfirm_ < val2*uto2.numConfirm_);

}

////////////////////////////////////////////////////////////////////////////////
bool UnspentTxOut::CompareTech2(UnspentTxOut const & uto1,
                                UnspentTxOut const & uto2)
{
   float val1 = pow(log10((float)uto1.getValue()) + 5, 5);
   float val2 = pow(log10((float)uto2.getValue()) + 5, 5);
   return (val1*uto1.numConfirm_ < val2*uto2.numConfirm_);

}

////////////////////////////////////////////////////////////////////////////////
bool UnspentTxOut::CompareTech3(UnspentTxOut const & uto1,
                                UnspentTxOut const & uto2)
{
   float val1 = pow(log10((float)uto1.getValue()) + 5, 4);
   float val2 = pow(log10((float)uto2.getValue()) + 5, 4);
   return (val1*uto1.numConfirm_ < val2*uto2.numConfirm_);
}


////////////////////////////////////////////////////////////////////////////////
void UnspentTxOut::sortTxOutVect(vector<UnspentTxOut> & utovect, int sortType)
{
   switch(sortType)
   {
   case 0: sort(utovect.begin(), utovect.end(), CompareNaive); break;
   case 1: sort(utovect.begin(), utovect.end(), CompareTech1); break;
   case 2: sort(utovect.begin(), utovect.end(), CompareTech2); break;
   case 3: sort(utovect.begin(), utovect.end(), CompareTech3); break;
   default: break; // do nothing
   }
}


////////////////////////////////////////////////////////////////////////////////
void UnspentTxOut::pprintOneLine(uint32_t currBlk)
{
   updateNumConfirm(currBlk);
   printf(" Tx:%s:%02d   BTC:%0.3f   nConf:%04d\n",
             txHash_.copySwapEndian().getSliceCopy(0,8).toHexStr().c_str(),
             txOutIndex_,
             value_/1e8,
             numConfirm_);
}





////////////////////////////////////////////////////////////////////////////////
/*
RegisteredScrAddr::RegisteredScrAddr(BtcAddress const & addrObj, 
                                     int32_t blkCreated)
{
   uniqueKey_ = addrObj.getAddrStr20();
   addrType_ = 0x00;

   if(blkCreated<0)
      blkCreated = addrObj.getFirstBlockNum();

   blkCreated_            = blkCreated;
   alreadyScannedUpToBlk_ = blkCreated;
}
*/





// kate: indent-width 3; replace-tabs on;

