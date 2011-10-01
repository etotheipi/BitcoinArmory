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
void BlockHeaderRef::pprint(ostream & os)
{
   getCopy().pprint(os);
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
      return (*treeOut)[treeOut.size()-1];
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
BinaryData TxInRef::getScript(void) 
{ 
   uint32_t scrLen = (uint32_t)BtcUtils::readVarInt(getPtr()+36);
   return BinaryData(getPtr() + getScriptOffset(), scrLen);
}

/////////////////////////////////////////////////////////////////////////////
BinaryDataRef TxInRef::getScriptRef(void) 
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
   isMine_ = false;

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
void TxInRef::unserialize(BinaryDataRef const & str, uint32_t nbytes, TxRef* parent)
{
   unserialize(str.getPtr(), nbytes, parent);
}


/////////////////////////////////////////////////////////////////////////////
// Not all TxIns have this information.  Have to go to the Outpoint and get
// the corresponding TxOut to find the sender.  In the case the sender is
// not available, return false and don't write the output
bool TxInRef::getSenderAddrIfAvailable(BinaryData & addrTarget)
{
   if(scriptType_ != TXIN_SCRIPT_STANDARD)
      return false;
   
   BinaryData pubkey65 = getScript().getSliceCopy(-65, 65);
   addrTarget = BtcUtils::getHash160(pubkey65);
   return true;
}

BinaryData TxInRef::getSenderAddrIfAvailable(void)
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
   returnTxIn.isMine_ = isMine_;
   return returnTxIn;
}

////////////////////////////////////////////////////////////////////////////////
void TxInRef::pprint(ostream & os)
{
   cout << "TxIn:" << endl;
   cout << "\tType:    ";
   switch(scriptType_)
   {
   case TXIN_SCRIPT_STANDARD: cout << "STANDARD" << endl; break;
   case TXIN_SCRIPT_COINBASE: cout << "COINBASE" << endl; break;
   case TXIN_SCRIPT_SPENDCB : cout << "SPEND CB" << endl; break;
   case TXIN_SCRIPT_UNKNOWN : cout << "UNKNOWN " << endl; break;
   }
   cout << "\tBytes:   " << getSize() << endl;
   cout << "\tSender:  " << getSenderAddrIfAvailable().toHexStr() << endl;
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
void TxOutRef::unserialize(BinaryRefReader & brr, uint32_t nbytes, TxRef* parent)
{
   unserialize( brr.getCurrPtr(), nbytes, parent);
   brr.advance(nBytes_);
}

/////////////////////////////////////////////////////////////////////////////
void TxOutRef::unserialize(BinaryDataRef const & str, uint32_t nbytes, TxRef* parent)
{
   unserialize(str.getPtr(), nbytes, parent);
}

////////////////////////////////////////////////////////////////////////////////
TxOut TxOutRef::getCopy(void) const
{
   TxOut returnTxOut;
   returnTxOut.unserialize(getPtr());
   returnTxOut.isMine_ = isMine_;
   returnTxOut.isSpent_ = isSpent_;
   returnTxOut.recipientBinAddr20_ = recipientBinAddr20_;
   return returnTxOut;
}

void TxOutRef::pprint(ostream & os)
{
   cout << "TxOut:" << endl;
   cout << "\tType:   ";
   switch(scriptType_)
   {
   case TXOUT_SCRIPT_STANDARD: cout << "STANDARD" << endl; break;
   case TXOUT_SCRIPT_COINBASE: cout << "COINBASE" << endl; break;
   case TXOUT_SCRIPT_UNKNOWN : cout << "UNKNOWN " << endl; break;
   }
   cout << "\tRecip:  " << recipientBinAddr20_.toHexStr().c_str() << endl;
   cout << "\tValue:  " << getValue() << endl;
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






