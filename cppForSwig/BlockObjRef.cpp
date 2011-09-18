#include <iostream>
#include <vector>
#include <map>
#include <cassert>

#include "BinaryData.h"
#include "BtcUtils.h"
#include "BlockObj.h"
#include "BlockObjRef.h"




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
OutPoint OutPointRef::getCopy(void) const
{
   OutPoint op;
   op.unserialize( self_.getPtr() );
   return op;
}

////////////////////////////////////////////////////////////////////////////////
OutPoint TxInRef::getOutPoint(void) 
{ 
   OutPoint op;
   op.unserialize(getPtr());
   return op;
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
TxOut TxOutRef::getCopy(void) const
{
   TxOut returnTxOut;
   returnTxOut.unserialize(getPtr());
   returnTxOut.isMine_ = isMine_;
   returnTxOut.isSpent_ = isSpent_;
   returnTxOut.recipientBinAddr20_ = recipientBinAddr20_;
   return returnTxOut;
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


////////////////////////////////////////////////////////////////////////////////
TxIn  TxRef::getTxIn (int i) const
{ 
   assert(isInitialized_);  
   return getTxInRef(i).getCopy();
}

////////////////////////////////////////////////////////////////////////////////
TxOut TxRef::getTxOut(int i) const
{ 
   assert(isInitialized_);  
   return getTxOutRef(i).getCopy(); 
}







