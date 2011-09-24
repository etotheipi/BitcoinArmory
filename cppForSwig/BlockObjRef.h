#ifndef _BLOCKOBJREF_H_
#define _BLOCKOBJREF_H_


#include <iostream>
#include <vector>
#include <map>
#include <cassert>

#include "BtcUtils.h"
#include "BinaryData.h"
#include "BlockObj.h"



class BlockHeader;
class OutPoint;
class TxIn;
class TxOut;
class Tx;

class BlockHeaderRef;
class OutPointRef;
class TxInRef;
class TxOutRef;
class TxRef;


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// These classes don't hold actually block header data, it only holds pointers
// to where the data is in the BlockHeaderManager.  So there is a single place
// where all block headers are stored, and this class tells us where exactly
// is the one we want.
class BlockHeaderRef
{
   friend class BlockDataManager_FullRAM;

public:

   BlockHeaderRef(void) : isInitialized_(false), isFinishedCalc_(false), fileByteLoc_(0) {}
   BlockHeaderRef(uint8_t const * ptr)       { unserialize(ptr); }
   BlockHeaderRef(BinaryRefReader & brr)     { unserialize(brr); }
   BlockHeaderRef(BinaryDataRef const & str) { unserialize(str); }
   BlockHeaderRef(BinaryData    const & str) { unserialize(str); }

   uint32_t      getVersion(void) const      { assert(isInitialized_); return  *(uint32_t*)(getPtr()      ); }
   BinaryDataRef getPrevHash(void) const     { assert(isInitialized_); return BinaryDataRef(getPtr()+4,32 ); }
   BinaryDataRef getMerkleRoot(void) const   { assert(isInitialized_); return BinaryDataRef(getPtr()+36,32); }
   uint32_t      getTimestamp(void) const    { assert(isInitialized_); return  *(uint32_t*)(getPtr()+68   ); }
   BinaryDataRef getDiffBits(void) const     { assert(isInitialized_); return BinaryDataRef(getPtr()+72,4 ); }
   uint32_t      getNonce(void) const        { assert(isInitialized_); return  *(uint32_t*)(getPtr()+76   ); }
   uint32_t      getBlockHeight(void) const  { assert(isInitialized_); return blockHeight_;                  }
   uint32_t      isMainBranch(void) const    { assert(isInitialized_); return isMainBranch_;                 }
   uint32_t      isOrphan(void) const        { assert(isInitialized_); return isOrphan_;                     }

   BinaryDataRef getHash(void) const     { assert(isInitialized_); return thisHash_.getRef();}

   uint8_t const * getPtr(void) const  { assert(isInitialized_); return self_.getPtr(); }
   uint32_t        getSize(void) const { assert(isInitialized_); return self_.getSize(); }

   BlockHeader getCopy(void) const;

   BinaryDataRef serialize(void)
   {
      assert(isInitialized_);
      return self_;
   }

   void unserialize(uint8_t const * ptr)
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

   void unserialize(BinaryDataRef const & str)
   {
      unserialize(str.getPtr());
   }

   void unserialize(BinaryRefReader & brr)
   {
      unserialize(brr.get_BinaryDataRef(HEADER_SIZE));
   }

   vector<TxRef*> const & getTxRefPtrList(void) const {return txPtrList_;}


private:
   BinaryDataRef  self_;
   bool isInitialized_;

   // Derived properties - we expect these to be set after construct/copy
   BinaryData     thisHash_;
   double         difficultyDbl_;

   // Need to compute these later
   BinaryData     nextHash_;
   uint32_t       numTx_;
   uint32_t       blockNumBytes_;
   uint32_t       blockHeight_;
   uint64_t       fileByteLoc_;
   double         difficultySum_;
   bool           isMainBranch_;
   bool           isOrphan_;
   bool           isFinishedCalc_;
   bool           isOnDiskYet_;
   vector<TxRef*> txPtrList_;
};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// OutPoint is just a reference to a TxOut
class OutPointRef
{
   friend class BlockDataManager_FullRAM;

public:
   OutPointRef(uint8_t const * ptr) { unserialize(ptr); }

   uint8_t const * getPtr(void) const { return self_.getPtr(); }
   uint32_t        getSize(void) const { return self_.getSize(); }

   OutPoint getCopy(void) const;

   BinaryData    getTxHash(void) const{ return BinaryData(self_.getPtr(), 32); }
   BinaryDataRef getTxHashRef(void) const  { return BinaryDataRef(self_.getPtr(),32); }
   uint32_t      getTxOutIndex(void) const { return *(uint32_t*)(self_.getPtr()+32); }
   BinaryDataRef serialize(void) const     { return self_; }
   void unserialize(uint8_t const * ptr) { self_.setRef(ptr, 36); }
   void unserialize(BinaryRefReader & brr) { unserialize(brr.get_BinaryDataRef(36)); }
   void unserialize(BinaryDataRef const & str) { unserialize(str.getPtr()); } 

private:
   BinaryDataRef self_;

};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxInRef
{
   friend class BlockDataManager_FullRAM;

public:
   TxInRef(void) : self_(0), isMine_(false) {}
   TxInRef(uint8_t const * ptr, uint32_t nBytes=0) {unserialize(ptr, nBytes);}

   uint8_t const * getPtr(void) const { return self_.getPtr(); }
   uint32_t        getSize(void) const { return self_.getSize(); }
   bool            isStandard(void) const { return scriptType_!=TXIN_SCRIPT_UNKNOWN; }
   bool            isInitialized(void) const {return self_.getSize() > 0; }
   bool            isMine(void) const {return isMine_;}
   TXIN_SCRIPT_TYPE getScriptType(void) const { return scriptType_; }

   void setMine(bool b) { isMine_ = b; }

   /////////////////////////////////////////////////////////////////////////////
   TxIn getCopy(void) const;

   uint32_t getScriptOffset(void) { return scriptOffset_; }

   /////////////////////////////////////////////////////////////////////////////
   OutPoint getOutPoint(void) const;

   /////////////////////////////////////////////////////////////////////////////
   OutPointRef getOutPointRef(void) const
   { 
      return OutPointRef(getPtr());
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData getBinScript(void) 
   { 
      uint32_t scrLen = (uint32_t)BtcUtils::readVarInt(getPtr()+36);
      return BinaryData(getPtr() + getScriptOffset(), scrLen);
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef getBinScriptRef(void) 
   { 
      uint32_t scrLen = (uint32_t)BtcUtils::readVarInt(getPtr()+36);
      return BinaryDataRef(getPtr() + scriptOffset_, scrLen);
   }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t getSequence(void)   { return *(uint32_t*)(getPtr()+getSize()-4); }
   uint32_t getScriptSize(void) { return nBytes_ - (scriptOffset_ + 4); }

   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef serialize(void) 
   { 
      return self_;
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr, uint32_t nbytes=0)
   {
      nBytes_ = (nbytes==0 ? BtcUtils::TxInCalcLength(ptr) : nbytes);
      self_ = BinaryDataRef(ptr, nBytes_);
      isMine_ = false;

      char const & v = self_[36];
      scriptOffset_ = (v<0xfd ? 37 : (v==0xfd ? 39 : (v==0xfe ? 41 : 45)));
      scriptType_ = BtcUtils::getTxInScriptType(getBinScriptRef(), 
                                                BinaryDataRef(getPtr(), 32));
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryRefReader & brr, uint32_t nbytes=0)
   {
      unserialize(brr.getCurrPtr(), nbytes);
      brr.advance(nBytes_);
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryDataRef const & str, uint32_t nbytes=0)
   {
      unserialize(str.getPtr(), nbytes);
   }


   /////////////////////////////////////////////////////////////////////////////
   // Not all TxIns have this information.  Have to go to the Outpoint and get
   // the corresponding TxOut to find the sender.  In the case the sender is
   // not available, return false and don't write the output
   bool getSenderAddrIfAvailable(BinaryData & addrTarget)
   {
      if(scriptType_ != TXIN_SCRIPT_STANDARD)
         return false;
      
      BinaryData pubkey65 = getBinScriptRef().getSliceCopy(-65, 65);
      addrTarget = BtcUtils::getHash160(pubkey65);
      return true;
   }


private:
   BinaryDataRef self_;

   // Derived properties - we expect these to be set after construct/copy
   uint32_t         nBytes_;
   TXIN_SCRIPT_TYPE scriptType_;
   uint32_t         scriptOffset_;

   // To be calculated later
   bool             isMine_;

};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxOutRef
{
   friend class BlockDataManager_FullRAM;

public:

   /////////////////////////////////////////////////////////////////////////////
   TxOutRef(void) : self_(0) {}
   TxOutRef(uint8_t const * ptr, uint32_t nBytes=0) { unserialize(ptr, nBytes); }


   uint8_t const * getPtr(void) const { return self_.getPtr(); }
   uint32_t        getSize(void) const { return self_.getSize(); }
   uint64_t        getValue(void) const { return *(uint64_t*)(self_.getPtr()); }
   bool            isStandard(void) const { return scriptType_ != TXOUT_SCRIPT_UNKNOWN; }
   bool            isInitialized(void) const {return self_.getSize() > 0; }

   bool            isMine(void)  const { return isMine_;  }
   bool            isSpent(void) const { return isSpent_; }

   void            setMine(bool b)  { isMine_  = b; }
   void            setSpent(bool b) { isSpent_ = b; }

   BinaryDataRef getRecipientAddr(void) const { return recipientBinAddr20_.getRef(); }
   TXOUT_SCRIPT_TYPE getScriptType(void) const { return scriptType_; }

   /////////////////////////////////////////////////////////////////////////////
   TxOut getCopy(void) const;

   uint32_t getScriptSize(void) { return nBytes_ - scriptOffset_; }

   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef serialize(void) { return self_; }


   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef getScriptRef(void) 
   { 
      return BinaryDataRef( self_.getPtr()+scriptOffset_, getScriptSize() );
   }



   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr, uint32_t nbytes=0)
   {
      nBytes_ = (nbytes==0 ? BtcUtils::TxOutCalcLength(ptr) : nbytes);
      self_ = BinaryDataRef(ptr, nBytes_);
      char const & v = self_[8];
      scriptOffset_ = (v<0xfd ? 9 : (v==0xfd ? 11 : (v==0xfe ? 13 : 17)));

      BinaryDataRef scriptRef(self_.getPtr()+scriptOffset_, getScriptSize());
      scriptType_ = BtcUtils::getTxOutScriptType(scriptRef);
      recipientBinAddr20_ = BtcUtils::getTxOutRecipientAddr(scriptRef, scriptType_);
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryRefReader & brr, uint32_t nbytes=0)
   {
      unserialize( brr.getCurrPtr(), nbytes);
      brr.advance(nBytes_);
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryDataRef const & str, uint32_t nbytes=0)
   {
      unserialize(str.getPtr(), nbytes);
   }


private:
   BinaryDataRef self_;

   // Derived properties - we expect these to be set after construct/copy
   uint32_t          nBytes_;
   uint32_t          scriptOffset_;
   TXOUT_SCRIPT_TYPE scriptType_;
   BinaryData        recipientBinAddr20_;

   // To be calculated later
   bool              isMine_;
   bool              isSpent_;


};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxRef
{
   friend class BlockDataManager_FullRAM;

public:
   TxRef(void)                      { isInitialized_ = false; }
   TxRef(uint8_t const * ptr)       { unserialize(ptr); }
   TxRef(BinaryRefReader & brr)     { unserialize(brr); }
   TxRef(BinaryDataRef const & str) { unserialize(str); }
   TxRef(BinaryData const & str)    { unserialize(str); }
     
   uint8_t const * getPtr(void) const { assert(isInitialized_); return self_.getPtr(); }
   uint32_t        getSize(void) const { assert(isInitialized_); return self_.getSize(); }

   uint32_t  getNumTxIn(void)  const { assert(isInitialized_); return (uint32_t)offsetsTxIn_.size()-1;}
   uint32_t  getNumTxOut(void) const { assert(isInitialized_); return (uint32_t)offsetsTxOut_.size()-1;}

   BlockHeaderRef* getHeaderPtr_(void)  const { assert(isInitialized_); return headerPtr_; }

   /////////////////////////////////////////////////////////////////////////////
   Tx getCopy(void) const;

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr)
   {
      nBytes_ = BtcUtils::TxCalcLength(ptr, &offsetsTxIn_, &offsetsTxOut_);
      BtcUtils::getHash256(ptr, nBytes_, thisHash_);
      self_.setRef(ptr, nBytes_);
      isInitialized_ = true;
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryRefReader & brr)
   {
      unserialize(brr.getCurrPtr());
      brr.advance(nBytes_);
   }

   void unserialize(BinaryDataRef const & str) { unserialize(str.getPtr()); }
   void unserialize(BinaryData const & str) { unserialize(str.getPtr()); }

   BinaryDataRef const & serialize(void) const { return self_; }
   BinaryData const & getHash(void) const { return thisHash_; }
   BinaryDataRef getHashRef(void) const { return BinaryDataRef(thisHash_); }


   /////////////////////////////////////////////////////////////////////////////
   // This is not a pointer to persistent object, this method actually CREATES
   // the TxInRef (once) that will be stored in a txioMap
   TxInRef createTxInRef(int i) const
   {
      assert(isInitialized_);
      uint32_t txinSize = offsetsTxIn_[i+1] - offsetsTxIn_[i];
      return TxInRef(self_.getPtr()+offsetsTxIn_[i], txinSize);
   }

   /////////////////////////////////////////////////////////////////////////////
   // This is not a pointer to persistent object, this method actually CREATES
   // the TxOutRef (once) that will be stored in a txioMap
   TxOutRef createTxOutRef(int i) const
   {
      assert(isInitialized_);
      uint32_t txoutSize = offsetsTxOut_[i+1] - offsetsTxOut_[i];
      return TxOutRef(self_.getPtr()+offsetsTxOut_[i], txoutSize);
   }

   /////////////////////////////////////////////////////////////////////////////
   TxIn  getTxInCopy (int i) const;
   TxOut getTxOutCopy(int i) const;

   uint32_t getBlockTimestamp(void)
   {
      if(headerPtr_==NULL)
         return headerPtr_->getTimestamp();
      return 0;
   }

   uint32_t getBlockHeight(void)
   {
      if(headerPtr_==NULL)
         if(headerPtr_->isMainBranch())
            return headerPtr_->getBlockHeight();
      return 0;
   }


private:
   BinaryDataRef self_; 
   bool isInitialized_;

   // Derived properties - we expect these to be set after construct/copy
   BinaryData    thisHash_;
   uint32_t      nBytes_;
   uint64_t      fileByteLoc_;
   vector<uint32_t> offsetsTxIn_;
   vector<uint32_t> offsetsTxOut_;

   // To be calculated/set later
   BlockHeaderRef*  headerPtr_;

};


#endif
