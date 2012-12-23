////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>        //
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




////////////////////////////////////////////////////////////////////////////////
void BlockHeader::unserialize(uint8_t const * ptr)
{
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
   isFinishedCalc_ = false;
   isOnDiskYet_ = false;
   txPtrList_ = vector<TxRef*>(0);
}

////////////////////////////////////////////////////////////////////////////////
void BlockHeader::unserialize(BinaryDataRef const & str) 
{ 
   unserialize(str.getPtr()); 
}

////////////////////////////////////////////////////////////////////////////////
void BlockHeader::unserialize(BinaryRefReader & brr) 
{ 
   unserialize(brr.get_BinaryDataRef(HEADER_SIZE)); 
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BlockHeader::serializeWholeBlock(BinaryData const & magic, 
                                            bool withLead8Bytes) const
{
   BinaryWriter serializedBlock;
   uint32_t blksize = getBlockSize();
   if(withLead8Bytes)
   {
      serializedBlock.reserve(blksize + 8);
      serializedBlock.put_BinaryData(magic);
      serializedBlock.put_uint32_t(blksize);
   }
   else
      serializedBlock.reserve(blksize);

   serializedBlock.put_BinaryData(dataCopy_);
   serializedBlock.put_var_int(getNumTx());
   for(uint32_t i=0; i<getNumTx(); i++)
      serializedBlock.put_BinaryData(txPtrList_[i]->serialize());

   return serializedBlock.getData();
   
}



////////////////////////////////////////////////////////////////////////////////
vector<BinaryData> BlockHeader::getTxHashList(void)
{
   vector<BinaryData> vectOut(getNumTx());
   for(uint32_t i=0; i<getNumTx(); i++)
      vectOut[i] = txPtrList_[i]->getThisHash();

   return vectOut;
}
////////////////////////////////////////////////////////////////////////////////
BinaryData BlockHeader::calcMerkleRoot(vector<BinaryData>* treeOut) 
{
   if(treeOut == NULL)
      return BtcUtils::calculateMerkleRoot( getTxHashList() );
   else
   {
      *treeOut = BtcUtils::calculateMerkleTree( getTxHashList() );
      return (*treeOut)[treeOut->size()-1];
   }
}

////////////////////////////////////////////////////////////////////////////////
bool BlockHeader::verifyMerkleRoot(void)
{
   return (calcMerkleRoot() == getMerkleRoot());

}

////////////////////////////////////////////////////////////////////////////////
bool BlockHeader::verifyIntegrity(void)
{
   // Calculate the merkle root, and compare to the one already stored in header
   bool merkleIsGood = (calcMerkleRoot() == getMerkleRoot());

   // Check that the last four bytes of the hash are zeros
   BinaryData fourzerobytes = BtcUtils::EmptyHash_.getSliceCopy(0,4);
   bool headerIsGood = (thisHash_.getSliceCopy(28,4) == fourzerobytes);
   return (merkleIsGood && headerIsGood);
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
   vector<TxRef*> txlist = getTxRefPtrList();
   vector<BinaryData> hashlist = getTxHashList();
   cout << "Number of Tx:  " << txlist.size() << ", " << hashlist.size() << endl;
   for(uint32_t i=0; i<txlist.size(); i++)
      txlist[i]->getTxCopy().pprintAlot();

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



// Returns the size of the header + numTx + tx[i], no leading bytes
uint32_t BlockHeader::getBlockSize(void) const
{
   uint32_t nBytes = HEADER_SIZE; 
   uint32_t nTx = txPtrList_.size();
   for(uint32_t i=0; i<nTx; i++)
   {
      if(txPtrList_[i] == NULL)
         return 0;
      else
         nBytes += txPtrList_[i]->getSize();
   }

   // Add in a couple bytes for the var_int
   // Use a fake BinaryWriter to write it out which returns the size
   nBytes += BinaryWriter().put_var_int(nTx);
   return nBytes;
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

void OutPoint::serialize(BinaryWriter & bw)
{
   bw.put_BinaryData(txHash_);
   bw.put_uint32_t(txOutIndex_);
}

BinaryData OutPoint::serialize(void)
{
   BinaryWriter bw(36);
   serialize(bw);
   return bw.getData();
}

void OutPoint::unserialize(uint8_t const * ptr)
{
   txHash_.copyFrom(ptr, 32);
   txOutIndex_ = *(uint32_t*)(ptr+32);
}
void OutPoint::unserialize(BinaryReader & br)
{
   br.get_BinaryData(txHash_, 32);
   txOutIndex_ = br.get_uint32_t();
}
void OutPoint::unserialize(BinaryRefReader & brr)
{
   brr.get_BinaryData(txHash_, 32);
   txOutIndex_ = brr.get_uint32_t();
}


void OutPoint::unserialize(BinaryData const & bd) 
{ 
   unserialize(bd.getPtr()); 
}
void OutPoint::unserialize(BinaryDataRef const & bdRef) 
{ 
   unserialize(bdRef.getPtr());
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
   op.unserialize(getPtr());
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
bool TxIn::isCoinbase(void) const
{
   return (scriptType_ == TXIN_SCRIPT_COINBASE);
}

/////////////////////////////////////////////////////////////////////////////
void TxIn::unserialize(uint8_t const * ptr, uint32_t nbytes, TxRef* parent, int32_t idx)
{
   parentTx_ = parent;
   index_ = idx;
   uint32_t numBytes = (nbytes==0 ? BtcUtils::TxInCalcLength(ptr) : nbytes);
   dataCopy_.copyFrom(ptr, numBytes);

   scriptOffset_ = 36 + BtcUtils::readVarIntLength(getPtr()+36);

   scriptType_ = BtcUtils::getTxInScriptType(getScriptRef(),
                                             BinaryDataRef(getPtr(),32));
}

/////////////////////////////////////////////////////////////////////////////
void TxIn::unserialize(BinaryRefReader & brr, uint32_t nbytes, TxRef* parent, int32_t idx)
{
   unserialize(brr.getCurrPtr(), nbytes, parent, idx);
   brr.advance(getSize());
}

/////////////////////////////////////////////////////////////////////////////
void TxIn::unserialize(BinaryData const & str, uint32_t nbytes, TxRef* parent, int32_t idx)
{
   unserialize(str.getPtr(), nbytes, parent, idx);
}

/////////////////////////////////////////////////////////////////////////////
void TxIn::unserialize(BinaryDataRef const & str, uint32_t nbytes, TxRef* parent, int32_t idx)
{
   unserialize(str.getPtr(), nbytes, parent, idx);
}


/////////////////////////////////////////////////////////////////////////////
// Not all TxIns have this information.  Have to go to the Outpoint and get
// the corresponding TxOut to find the sender.  In the case the sender is
// not available, return false and don't write the output
bool TxIn::getSenderAddrIfAvailable(BinaryData & addrTarget) const
{
   if(scriptType_ != TXIN_SCRIPT_STANDARD)
      return false;
   
   BinaryData pubkey65 = getScript().getSliceCopy(-65, 65);
   addrTarget = BtcUtils::getHash160(pubkey65);
   return true;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData TxIn::getSenderAddrIfAvailable(void) const
{
   BinaryData addrTarget(0);
   if(scriptType_ == TXIN_SCRIPT_STANDARD)
   {
      BinaryData pubkey65 = getScriptRef().getSliceCopy(-65, 65);
      addrTarget = BtcUtils::getHash160(pubkey65);
   }
   return addrTarget;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData TxIn::getParentHash(void)
{
   if(parentTx_==NULL)
      return parentHash_;
   else
      return parentTx_->getThisHash();
}

////////////////////////////////////////////////////////////////////////////////
uint32_t TxIn::getParentHeight(void)
{
   if(parentTx_==NULL)
      return parentHeight_;
   else
      return parentTx_->getBlockHeight();
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
      case TXIN_SCRIPT_STANDARD: os << "STANDARD" << endl; break;
      case TXIN_SCRIPT_COINBASE: os << "COINBASE" << endl; break;
      case TXIN_SCRIPT_SPENDCB : os << "SPEND CB" << endl; break;
      case TXIN_SCRIPT_UNKNOWN : os << "UNKNOWN " << endl; break;
   }
   os << indent << "   Bytes:   " << getSize() << endl;
   os << indent << "   Sender:  " << getSenderAddrIfAvailable().toHexStr() << endl;
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
void TxOut::unserialize(uint8_t const * ptr, uint32_t nbytes, TxRef* parent, int32_t idx)
{
   parentTx_ = parent;
   index_ = idx;
   uint32_t numBytes = (nbytes==0 ? BtcUtils::TxOutCalcLength(ptr) : nbytes);
   dataCopy_.copyFrom(ptr, numBytes);

   scriptOffset_ = 8 + BtcUtils::readVarIntLength(getPtr()+8);
   BinaryDataRef scriptRef(dataCopy_.getPtr()+scriptOffset_, getScriptSize());
   scriptType_ = BtcUtils::getTxOutScriptType(scriptRef);
   recipientBinAddr20_ = BtcUtils::getTxOutRecipientAddr(scriptRef, scriptType_);
}

/////////////////////////////////////////////////////////////////////////////
void TxOut::unserialize(BinaryData const & str, uint32_t nbytes, TxRef* parent, int32_t idx)
{
   unserialize(str.getPtr(), nbytes, parent, idx);
}

/////////////////////////////////////////////////////////////////////////////
void TxOut::unserialize(BinaryDataRef const & str, uint32_t nbytes, TxRef* parent, int32_t idx)
{
   unserialize(str.getPtr(), nbytes, parent, idx);
}

/////////////////////////////////////////////////////////////////////////////
void TxOut::unserialize(BinaryRefReader & brr, uint32_t nbytes, TxRef* parent, int32_t idx)
{
   unserialize( brr.getCurrPtr(), nbytes, parent, idx );
   brr.advance(getSize());
}

////////////////////////////////////////////////////////////////////////////////
BinaryData TxOut::getParentHash(void)
{
   if(parentTx_==NULL)
      return parentHash_;
   else
      return parentTx_->getThisHash();
}

////////////////////////////////////////////////////////////////////////////////
uint32_t   TxOut::getParentHeight(void)
{
   if(parentTx_==NULL)
      return parentHeight_;
   else
      return parentTx_->getBlockHeight();

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
   case TXOUT_SCRIPT_STANDARD: os << "STANDARD" << endl; break;
   case TXOUT_SCRIPT_COINBASE: os << "COINBASE" << endl; break;
   case TXOUT_SCRIPT_UNKNOWN : os << "UNKNOWN " << endl; break;
   }
   os << indent << "   Recip:  " 
                << recipientBinAddr20_.toHexStr(pBigendian).c_str() 
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

Tx::Tx(TxRef* txref)
{
   if(txref != NULL)
   {
      unserialize(txref->getBlkFilePtr().getUnsafeDataPtr());
      headerPtr_ = txref->getHeaderPtr();
   }
   txRefPtr_ = txref;
}

/////////////////////////////////////////////////////////////////////////////
void Tx::unserialize(uint8_t const * ptr)
{
   uint32_t numBytes = BtcUtils::TxCalcLength(ptr, &offsetsTxIn_, &offsetsTxOut_);
   dataCopy_.copyFrom(ptr, numBytes);
   BtcUtils::getHash256(ptr, numBytes, thisHash_);

   uint32_t numTxOut = offsetsTxOut_.size()-1;
   version_  = *(uint32_t*)(ptr);
   lockTime_ = *(uint32_t*)(ptr + offsetsTxOut_[numTxOut]);

   isInitialized_ = true;
   headerPtr_ = NULL;
   txRefPtr_ = NULL;
}

/////////////////////////////////////////////////////////////////////////////
bool Tx::isMainBranch(void) const
{
   if(headerPtr_==NULL || !headerPtr_->isMainBranch())
      return false;
   else
      return true;   
}

/////////////////////////////////////////////////////////////////////////////
BinaryData Tx::getThisHash(void) const
{
   return BtcUtils::getHash256(dataCopy_.getPtr(), dataCopy_.getSize());
}

/////////////////////////////////////////////////////////////////////////////
void Tx::unserialize(BinaryRefReader & brr)
{
   unserialize(brr.getCurrPtr());
   brr.advance(getSize());
}


/////////////////////////////////////////////////////////////////////////////
uint64_t Tx::getSumOfOutputs(void)
{
   uint64_t sumVal = 0;
   for(uint32_t i=0; i<getNumTxOut(); i++)
      sumVal += getTxOut(i).getValue();

   return sumVal;
}


/////////////////////////////////////////////////////////////////////////////
BinaryData Tx::getRecipientForTxOut(uint32_t txOutIndex) 
{
   TxOut txout = getTxOut(txOutIndex);
   if(txout.getScriptType() == TXOUT_SCRIPT_STANDARD ||
      txout.getScriptType() == TXOUT_SCRIPT_COINBASE)
   {
      return txout.getRecipientAddr();
   }
   else
   {
      // TODO:  We may actually want to have another branch for P2SH
      //        and pass out the P2SH script hash
      return BinaryData("");
   }

}


/////////////////////////////////////////////////////////////////////////////
// This is not a pointer to persistent object, this method actually CREATES
// the TxIn.   But it's fast and doesn't hold a lot of post-construction
// information, so it can probably just be computed on the fly
TxIn Tx::getTxIn(int i)
{
   assert(isInitialized());
   uint32_t txinSize = offsetsTxIn_[i+1] - offsetsTxIn_[i];
   TxIn out(dataCopy_.getPtr()+offsetsTxIn_[i], txinSize, getTxRefPtr(), i);
   
   if(getTxRefPtr()==NULL)
   {
      out.setParentHash(getThisHash());
      out.setParentHeight(UINT32_MAX);
   }
   return out;
}

/////////////////////////////////////////////////////////////////////////////
// This is not a pointer to persistent object, this method actually CREATES
// the TxOut.   But it's fast and doesn't hold a lot of post-construction
// information, so it can probably just be computed on the fly
TxOut Tx::getTxOut(int i)
{
   assert(isInitialized());
   uint32_t txoutSize = offsetsTxOut_[i+1] - offsetsTxOut_[i];
   TxOut out(dataCopy_.getPtr()+offsetsTxOut_[i], txoutSize, getTxRefPtr(), i);
   
   if(getTxRefPtr()==NULL)
   {
      out.setParentHash(getThisHash());
      out.setParentHeight(UINT32_MAX);
   }
   return out;
}


/////////////////////////////////////////////////////////////////////////////
uint32_t Tx::getBlockTimestamp(void)
{
   if(headerPtr_!=NULL)
      return headerPtr_->getTimestamp();
   return UINT32_MAX;
}

/////////////////////////////////////////////////////////////////////////////
uint32_t Tx::getBlockHeight(void)
{
   if(headerPtr_!=NULL && headerPtr_->isMainBranch())
      return headerPtr_->getBlockHeight();
   return UINT32_MAX;
}


/////////////////////////////////////////////////////////////////////////////
// We have the Tx, but we don't know its index... gotta get Tx list from
// header and try to match up
uint32_t Tx::getBlockTxIndex(void)
{
   if(headerPtr_ == NULL)
      return UINT32_MAX;

   vector<TxRef*> txlist = headerPtr_->getTxRefPtrList();
   for(uint32_t i=0; i<txlist.size(); i++)
      if( txlist[i]->getThisHash() == getThisHash() )
         return i;
   return UINT32_MAX;
}

/////////////////////////////////////////////////////////////////////////////
void Tx::pprint(ostream & os, int nIndent, bool pBigendian) 
{
   string indent = "";
   for(int i=0; i<nIndent; i++)
      indent = indent + "   ";
    
   os << indent << "Tx:   " << thisHash_.toHexStr(pBigendian) 
                << (pBigendian ? " (BE)" : " (LE)") << endl;
   if( headerPtr_==NULL)
      os << indent << "   Blk:  <NOT PART OF A BLOCK YET>" << endl;
   else
      os << indent << "   Blk:         " << headerPtr_->getBlockHeight() << endl;

   os << indent << "   TxSize:      " << getSize() << " bytes" << endl;
   os << indent << "   NumInputs:   " << getNumTxIn() << endl;
   os << indent << "   NumOutputs:  " << getNumTxOut() << endl;
   os << endl;
   for(uint32_t i=0; i<getNumTxIn(); i++)
      getTxIn(i).pprint(os, nIndent+1, pBigendian);
   os << endl;
   for(uint32_t i=0; i<getNumTxOut(); i++)
      getTxOut(i).pprint(os, nIndent+1, pBigendian);
}

////////////////////////////////////////////////////////////////////////////////
// Need a serious debugging method, that will touch all pointers that are
// supposed to be not NULL.  I'd like to try to force a segfault here, if it
// is going to happen, instead of letting it kill my program where I don't 
// know what happened.
void Tx::pprintAlot(ostream & os)
{
   cout << "Tx hash:   " << thisHash_.toHexStr(true) << endl;
   if(headerPtr_!=NULL)
   {
      cout << "HeaderNum: " << headerPtr_->getBlockHeight() << endl;
      cout << "HeadHash:  " << headerPtr_->getThisHash().toHexStr(true) << endl;
   }

   cout << endl << "NumTxIn:   " << getNumTxIn() << endl;
   for(uint32_t i=0; i<getNumTxIn(); i++)
   {
      TxIn txin = getTxIn(i);
      cout << "   TxIn: " << i <<  "   ParentPtr: " << txin.getParentTxPtr() << endl;
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
      TxOut txout = getTxOut(i);
      cout << "   TxOut: " << i <<  "   ParentPtr: " << txout.getParentTxPtr() << endl;
      cout << "      Siz:  " << txout.getSize() << endl;
      cout << "      Scr:  " << txout.getScriptSize() << "  Type: " 
                        << (int)txout.getScriptType() << endl;
      cout << "      Val:  " << txout.getValue() << endl;
   }

}



/////////////////////////////////////////////////////////////////////////////
Tx TxRef::getTxCopy(void) const
{
   // It seems unnecessary to have to make this method non-const, but also
   // unnecessary to require (TxRef const *) for the tx copy...
   // I've never used const_cast before, but it seems appropriate here...
   Tx out(blkFilePtr_.getUnsafeDataPtr());
   out.setTxRefPtr(const_cast<TxRef*>(this));
   out.setHeaderPtr(headerPtr_);
   return out;
}

/////////////////////////////////////////////////////////////////////////////
bool TxRef::isMainBranch(void) const
{
   if(headerPtr_==NULL || !headerPtr_->isMainBranch())
      return false;
   else
      return true;   
}

/////////////////////////////////////////////////////////////////////////////
BinaryData TxRef::getThisHash(void) const
{
   uint8_t* tempPtr = blkFilePtr_.getUnsafeDataPtr();
   return BtcUtils::getHash256(tempPtr, blkFilePtr_.getNumBytes());
}


/////////////////////////////////////////////////////////////////////////////
uint32_t TxRef::getBlockTimestamp(void) const
{
   if(headerPtr_!=NULL)
      return headerPtr_->getTimestamp();
   return UINT32_MAX;
}

/////////////////////////////////////////////////////////////////////////////
uint32_t TxRef::getBlockHeight(void) const
{
   if(headerPtr_!=NULL && headerPtr_->isMainBranch())
         return headerPtr_->getBlockHeight();
   return UINT32_MAX;
}

/////////////////////////////////////////////////////////////////////////////
// We have the TxRef, but we don't know its index... gotta get Tx list from
// header and try to match up
uint32_t TxRef::getBlockTxIndex(void) const
{
   if(headerPtr_ == NULL)
      return UINT32_MAX;

   vector<TxRef*> txlist = headerPtr_->getTxRefPtrList();
   for(uint32_t i=0; i<txlist.size(); i++)
      if( txlist[i] == this )
         return i;
   return UINT32_MAX;
}


/////////////////////////////////////////////////////////////////////////////
void TxRef::pprint(ostream & os, int nIndent) const
{
   os << "TxRef Information:" << endl;
   os << "   Hash:      " << getThisHash().toHexStr() << endl;
   os << "   Height:    " << getBlockHeight() << endl;
   os << "   BlkIndex:  " << getBlockTxIndex() << endl;
   os << "   FileIdx:   " << blkFilePtr_.getFileIndex() << endl;
   os << "   FileStart: " << blkFilePtr_.getStartByte() << endl;
   os << "   NumBytes:  " << blkFilePtr_.getNumBytes() << endl;
   os << "   ----- " << endl;
   os << "   Read from disk, full tx-info: " << endl;
   getTxCopy().pprint(os, nIndent+1); 
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
   txHash_(BtcUtils::EmptyHash_),
   txOutIndex_(0),
   txHeight_(0),
   value_(0),
   script_(BinaryData(0)),
   numConfirm_(0)
{
   // Nothing to do here
}

////////////////////////////////////////////////////////////////////////////////
void UnspentTxOut::init(TxOut & txout, uint32_t blkNum)
{
   txHash_     = txout.getParentHash();
   txOutIndex_ = txout.getIndex();
   txHeight_   = txout.getParentHeight();
   value_      = txout.getValue();
   script_     = txout.getScript();
   updateNumConfirm(blkNum);
}

////////////////////////////////////////////////////////////////////////////////
BinaryData UnspentTxOut::getRecipientAddr(void) const
{
   return BtcUtils::getTxOutRecipientAddr(getScript());
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
   float val1 = uto1.getValue();
   float val2 = uto2.getValue();
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
                      txHash_.getSliceCopy(0,8).toHexStr().c_str(),
                      txOutIndex_,
                      value_/1e8,
                      numConfirm_);
}















