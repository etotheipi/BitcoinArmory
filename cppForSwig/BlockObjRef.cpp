////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>             //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include <iostream>
#include <vector>
#include <map>
#include <cassert>

#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockObj.h"
#include "BlockObjRef.h"




////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// BlockHeaderRef methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

uint32_t BlockHeaderRef::getBlockSize(void) const
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
   nBytes += BinaryWriter().put_var_int(nTx);
   return nBytes;
}

BlockHeader BlockHeaderRef::getCopy(void) const
{
   assert(isInitialized_);
   BlockHeader bh;
   bh.unserialize(self_);

   bh.thisHash_     = thisHash_;
   bh.nextHash_     = nextHash_;
   bh.numTx_        = numTx_;
   bh.blockHeight_  = blockHeight_;
   bh.fileByteLoc_  = fileByteLoc_;
   bh.difficultyDbl_ = difficultyDbl_;
   bh.difficultySum_ = difficultySum_;
   bh.isMainBranch_ = isMainBranch_;
   bh.isOrphan_     = isOrphan_;
   bh.isFinishedCalc_ = isFinishedCalc_;
   bh.isOnDiskYet_  = isOnDiskYet_;

   // The copy doesn't have pointers to any Tx (because BHRef class doesn't
   // use any real Tx's, only TxRefs
   bh.txPtrList_.clear();

   return bh;
}

////////////////////////////////////////////////////////////////////////////////
void BlockHeaderRef::unserialize(uint8_t const * ptr)
{
   self_.setRef(ptr, HEADER_SIZE);
   BtcUtils::getHash256(self_.getPtr(), HEADER_SIZE, thisHash_);
   difficultyDbl_ = BtcUtils::convertDiffBitsToDouble( 
                              BinaryDataRef(self_.getPtr()+72, 4));
   isInitialized_ = true;
   nextHash_ = BinaryData(0);
   numTx_ = 0;
   blockHeight_ = UINT32_MAX;
   blockNumBytes_ = 0;
   fileByteLoc_ = 0;
   difficultySum_ = -1;
   isMainBranch_ = false;
   isOrphan_ = true;
   isFinishedCalc_ = false;
   isOnDiskYet_ = false;
   txPtrList_ = vector<TxRef*>(0);
}

////////////////////////////////////////////////////////////////////////////////
void BlockHeaderRef::unserialize(BinaryDataRef const & str) 
{ 
   unserialize(str.getPtr()); 
}

////////////////////////////////////////////////////////////////////////////////
void BlockHeaderRef::unserialize(BinaryRefReader & brr) 
{ 
   unserialize(brr.get_BinaryDataRef(HEADER_SIZE)); 
}


////////////////////////////////////////////////////////////////////////////////
void BlockHeaderRef::pprint(ostream & os, int nIndent, bool pBigendian) const
{
   getCopy().pprint(os, nIndent, pBigendian);
}


////////////////////////////////////////////////////////////////////////////////
vector<BinaryData> BlockHeaderRef::getTxHashList(void)
{
   vector<BinaryData> vectOut(numTx_);
   for(uint32_t i=0; i<numTx_; i++)
      vectOut[i] = txPtrList_[i]->getThisHash();

   return vectOut;
}
////////////////////////////////////////////////////////////////////////////////
BinaryData BlockHeaderRef::calcMerkleRoot(vector<BinaryData>* treeOut) 
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
bool BlockHeaderRef::verifyMerkleRoot(void)
{
   return  (calcMerkleRoot() == getMerkleRoot());

}

////////////////////////////////////////////////////////////////////////////////
bool BlockHeaderRef::verifyIntegrity(void)
{
   // Calculate the merkle root, and compare to the one already stored in header
   bool merkleIsGood = (calcMerkleRoot() == getMerkleRoot());

   // Check that the last four bytes of the hash are zeros
   BinaryData fourzerobytes = BtcUtils::EmptyHash_.getSliceCopy(0,4);
   bool headerIsGood = (thisHash_.getSliceCopy(28,4) == fourzerobytes);
   return (merkleIsGood && headerIsGood);
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// OutPointRef methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
OutPoint OutPointRef::getCopy(void) const
{
   OutPoint op;
   op.unserialize( self_.getPtr() );
   return op;
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// TxInRef methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
OutPoint TxInRef::getOutPoint(void) const
{ 
   OutPoint op;
   op.unserialize(getPtr());
   return op;
}

/////////////////////////////////////////////////////////////////////////////
OutPointRef TxInRef::getOutPointRef(void) const
{
   return OutPointRef(getPtr());
}



/////////////////////////////////////////////////////////////////////////////
BinaryData TxInRef::getScript(void) const
{ 
   uint32_t scrLen = (uint32_t)BtcUtils::readVarInt(getPtr()+36);
   return BinaryData(getPtr() + getScriptOffset(), scrLen);
}

/////////////////////////////////////////////////////////////////////////////
BinaryDataRef TxInRef::getScriptRef(void) const
{ 
   uint32_t scrLen = (uint32_t)BtcUtils::readVarInt(getPtr()+36);
   return BinaryDataRef(getPtr() + scriptOffset_, scrLen);
}


bool TxInRef::isCoinbase(void) const
{
   return (scriptType_ == TXIN_SCRIPT_COINBASE);
}

/////////////////////////////////////////////////////////////////////////////
void TxInRef::unserialize(uint8_t const * ptr, uint32_t nbytes, TxRef* parent)
{
   parentTx_ = parent;
   nBytes_ = (nbytes==0 ? BtcUtils::TxInCalcLength(ptr) : nbytes);
   self_ = BinaryDataRef(ptr, nBytes_);

   char const & v = self_[36];
   scriptOffset_ = (v<0xfd ? 37 : (v==0xfd ? 39 : (v==0xfe ? 41 : 45)));
   scriptType_ = BtcUtils::getTxInScriptType(getScriptRef(), 
                                             BinaryDataRef(getPtr(), 32));
}

void TxInRef::unserialize(BinaryRefReader & brr, uint32_t nbytes, TxRef* parent)
{
   unserialize(brr.getCurrPtr(), nbytes, parent);
   brr.advance(nBytes_);
}

/////////////////////////////////////////////////////////////////////////////
void TxInRef::unserialize(BinaryData const & str, uint32_t nbytes, TxRef* parent)
{
   unserialize(str.getPtr(), nbytes, parent);
}

/////////////////////////////////////////////////////////////////////////////
void TxInRef::unserialize(BinaryDataRef const & str, uint32_t nbytes, TxRef* parent)
{
   unserialize(str.getPtr(), nbytes, parent);
}


/////////////////////////////////////////////////////////////////////////////
// Not all TxIns have this information.  Have to go to the Outpoint and get
// the corresponding TxOut to find the sender.  In the case the sender is
// not available, return false and don't write the output
bool TxInRef::getSenderAddrIfAvailable(BinaryData & addrTarget) const
{
   if(scriptType_ != TXIN_SCRIPT_STANDARD)
      return false;
   
   BinaryData pubkey65 = getScript().getSliceCopy(-65, 65);
   addrTarget = BtcUtils::getHash160(pubkey65);
   return true;
}

BinaryData TxInRef::getSenderAddrIfAvailable(void) const
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
TxIn TxInRef::getCopy(void) const
{
   TxIn returnTxIn;
   returnTxIn.unserialize(getPtr());
   returnTxIn.scriptType_ = scriptType_;
   return returnTxIn;
}

////////////////////////////////////////////////////////////////////////////////
void TxInRef::pprint(ostream & os, int nIndent, bool pBigendian) const
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
// TxOutRef methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
BinaryData TxOutRef::getScript(void) 
{ 
   return BinaryData( self_.getPtr()+scriptOffset_, getScriptSize() );
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef TxOutRef::getScriptRef(void) 
{ 
   return BinaryDataRef( self_.getPtr()+scriptOffset_, getScriptSize() );
}



/////////////////////////////////////////////////////////////////////////////
void TxOutRef::unserialize(uint8_t const * ptr, uint32_t nbytes, TxRef* parent)
{
   parentTx_ = parent;
   nBytes_ = (nbytes==0 ? BtcUtils::TxOutCalcLength(ptr) : nbytes);
   self_ = BinaryDataRef(ptr, nBytes_);
   char const & v = self_[8];
   scriptOffset_ = (v<0xfd ? 9 : (v==0xfd ? 11 : (v==0xfe ? 13 : 17)));

   BinaryDataRef scriptRef(self_.getPtr()+scriptOffset_, getScriptSize());
   scriptType_ = BtcUtils::getTxOutScriptType(scriptRef);
   recipientBinAddr20_ = BtcUtils::getTxOutRecipientAddr(scriptRef, scriptType_);
}

/////////////////////////////////////////////////////////////////////////////
void TxOutRef::unserialize(BinaryData const & str, uint32_t nbytes, TxRef* parent)
{
   unserialize(str.getPtr(), nbytes, parent);
}

/////////////////////////////////////////////////////////////////////////////
void TxOutRef::unserialize(BinaryDataRef const & str, uint32_t nbytes, TxRef* parent)
{
   unserialize(str.getPtr(), nbytes, parent);
}

/////////////////////////////////////////////////////////////////////////////
void TxOutRef::unserialize(BinaryRefReader & brr, uint32_t nbytes, TxRef* parent)
{
   unserialize( brr.getCurrPtr(), nbytes, parent);
   brr.advance(nBytes_);
}


////////////////////////////////////////////////////////////////////////////////
TxOut TxOutRef::getCopy(void) const
{
   TxOut returnTxOut;
   returnTxOut.unserialize(getPtr());
   returnTxOut.recipientBinAddr20_ = recipientBinAddr20_;
   return returnTxOut;
}

void TxOutRef::pprint(ostream & os, int nIndent, bool pBigendian) 
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
// TxRef methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
void TxRef::unserialize(uint8_t const * ptr)
{
   nBytes_ = BtcUtils::TxCalcLength(ptr, &offsetsTxIn_, &offsetsTxOut_);
   BtcUtils::getHash256(ptr, nBytes_, thisHash_);
   self_.setRef(ptr, nBytes_);
   isInitialized_ = true;
   isMainBranch_ = false;  // only BDM::organizeChain() can set this
}

/////////////////////////////////////////////////////////////////////////////
void TxRef::unserialize(BinaryRefReader & brr)
{
   unserialize(brr.getCurrPtr());
   brr.advance(nBytes_);
}

////////////////////////////////////////////////////////////////////////////////
Tx TxRef::getCopy(void) const
{
   assert(isInitialized_);    
   Tx returnTx;
   returnTx.unserialize(getPtr());
   returnTx.thisHash_ = thisHash_;
   returnTx.nBytes_ = nBytes_;
   returnTx.headerRefPtr_ = headerPtr_;
   return returnTx;
}

/////////////////////////////////////////////////////////////////////////////
// This is not a pointer to persistent object, this method actually CREATES
// the TxInRef.   But it's fast and doesn't hold a lot of post-construction
// information, so it can probably just be computed on the fly
TxInRef TxRef::getTxInRef(int i)
{
   assert(isInitialized_);
   uint32_t txinSize = offsetsTxIn_[i+1] - offsetsTxIn_[i];
   return TxInRef(self_.getPtr()+offsetsTxIn_[i], txinSize, this);
}

/////////////////////////////////////////////////////////////////////////////
// This is not a pointer to persistent object, this method actually CREATES
// the TxOutRef.   But it's fast and doesn't hold a lot of post-construction
// information, so it can probably just be computed on the fly
TxOutRef TxRef::getTxOutRef(int i)
{
   assert(isInitialized_);
   uint32_t txoutSize = offsetsTxOut_[i+1] - offsetsTxOut_[i];
   return TxOutRef(self_.getPtr()+offsetsTxOut_[i], txoutSize, this);
}



////////////////////////////////////////////////////////////////////////////////
TxIn  TxRef::getTxInCopy (int i)
{ 
   assert(isInitialized_);  
   return getTxInRef(i).getCopy();
}

////////////////////////////////////////////////////////////////////////////////
TxOut TxRef::getTxOutCopy(int i)
{ 
   assert(isInitialized_);  
   return getTxOutRef(i).getCopy(); 
}


/////////////////////////////////////////////////////////////////////////////
uint32_t TxRef::getBlockTimestamp(void)
{
   if(headerPtr_==NULL)
      return headerPtr_->getTimestamp();
   return UINT32_MAX;
}

/////////////////////////////////////////////////////////////////////////////
uint32_t TxRef::getBlockHeight(void)
{
   if(headerPtr_==NULL)
      if(headerPtr_->isMainBranch())
         return headerPtr_->getBlockHeight();
   return UINT32_MAX;
}


void TxRef::pprint(ostream & os, int nIndent, bool pBigendian) 
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
   os << indent << "   NumOutputs:  " << getNumTxIn() << endl;
   os << endl;
   for(int i=0; i<getNumTxIn(); i++)
      getTxInRef(i).pprint(os, nIndent+1, pBigendian);
   os << endl;
   for(int i=0; i<getNumTxOut(); i++)
      getTxOutRef(i).pprint(os, nIndent+1, pBigendian);
}




