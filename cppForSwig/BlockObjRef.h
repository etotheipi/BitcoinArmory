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

   /////////////////////////////////////////////////////////////////////////////
   BlockHeaderRef(void) : isInitialized_(false),  fileByteLoc_(0), isFinishedCalc_(false) {}
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
   double        getDifficulty(void) const   { assert(isInitialized_); return difficultyDbl_;                }
   double        getDifficultySum(void) const{ assert(isInitialized_); return difficultySum_;                }
   BinaryDataRef getThisHash(void) const     { assert(isInitialized_); return thisHash_.getRef();            }
   uint32_t      getNumTx(void) const        { assert(isInitialized_); return numTx_;                        }

   uint8_t const * getPtr(void) const  { assert(isInitialized_); return self_.getPtr(); }
   uint32_t        getSize(void) const { assert(isInitialized_); return self_.getSize(); }


   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef serialize(void) { assert(isInitialized_); return self_; }
   BlockHeader   getCopy(void) const;
   void          pprint(ostream & os=cout);

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr);
   void unserialize(BinaryDataRef const & str);
   void unserialize(BinaryRefReader & brr);

   /////////////////////////////////////////////////////////////////////////////
   vector<TxRef*> & getTxRefPtrList(void) {return txPtrList_;}

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

   /////////////////////////////////////////////////////////////////////////////
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
   TxInRef(void) : self_(0),  nBytes_(0), scriptType_(TXIN_SCRIPT_UNKNOWN), 
                   scriptOffset_(0), isMine_(false) {}

   TxInRef(uint8_t const * ptr, uint32_t nBytes=0, TxRef* parent=NULL) 
                                       { unserialize(ptr, nBytes, parent); } 

   uint8_t const *  getPtr(void) const { return self_.getPtr(); }
   uint32_t         getSize(void) const { return self_.getSize(); }
   bool             isStandard(void) const { return scriptType_!=TXIN_SCRIPT_UNKNOWN; }
   bool             isCoinbase(void) const;
   bool             isInitialized(void) const {return self_.getSize() > 0; }
   bool             isMine(void) const {return isMine_;}
   TxRef*           getParentTxPtr(void) { return parentTx_; }
   void             setParentTxPtr(TxRef * txref) { parentTx_ = txref; }
   TXIN_SCRIPT_TYPE getScriptType(void) const { return scriptType_; }
   uint32_t         getScriptOffset(void) { return scriptOffset_; }

   TxIn             getCopy(void) const;
   OutPoint         getOutPoint(void) const;
   OutPointRef      getOutPointRef(void) const;
   BinaryData       getBinScript(void) ;
   BinaryDataRef    getBinScriptRef(void) ;
   uint32_t         getSequence(void)   { return *(uint32_t*)(getPtr()+getSize()-4); }
   uint32_t         getScriptSize(void) { return nBytes_ - (scriptOffset_ + 4); }
   void             setMine(bool b) { isMine_ = b; }

   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef serialize(void) { return self_; }
   void unserialize(uint8_t const * ptr, uint32_t nbytes=0, TxRef* parent=NULL);
   void unserialize(BinaryRefReader & brr, uint32_t nbytes=0, TxRef* parent=NULL);
   void unserialize(BinaryDataRef const & str, uint32_t nbytes=0, TxRef* parent=NULL);

   /////////////////////////////////////////////////////////////////////////////
   // Not all TxIns have sendor info.  Might have to go to the Outpoint and get
   // the corresponding TxOut to find the sender.  In the case the sender is
   // not available, return false and don't write the output
   bool       getSenderAddrIfAvailable(BinaryData & addrTarget);
   BinaryData getSenderAddrIfAvailable(void);

   void pprint(ostream & os=cout);


private:
   BinaryDataRef self_;

   // Derived properties - we expect these to be set after construct/copy
   uint32_t         nBytes_;
   TXIN_SCRIPT_TYPE scriptType_;
   uint32_t         scriptOffset_;
   TxRef*           parentTx_;

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
   TxOutRef(uint8_t const * ptr, uint32_t nBytes=0, TxRef* parent=NULL) 
                                       { unserialize(ptr, nBytes, parent); } 

   uint8_t const * getPtr(void) const { return self_.getPtr(); }
   uint32_t        getSize(void) const { return self_.getSize(); }
   uint64_t        getValue(void) const { return *(uint64_t*)(self_.getPtr()); }
   bool            isStandard(void) const { return scriptType_ != TXOUT_SCRIPT_UNKNOWN; }
   bool            isInitialized(void) const {return self_.getSize() > 0; }
   bool            isMine(void)  const { return isMine_;  }
   bool            isSpent(void) const { return isSpent_; }
   TxRef*          getParentTxPtr(void) { return parentTx_; }
   void            setParentTxPtr(TxRef * txref) { parentTx_ = txref; }
   void            setMine(bool b)  { isMine_  = b; }
   void            setSpent(bool b) { isSpent_ = b; }

   BinaryDataRef      getRecipientAddr(void) const { return recipientBinAddr20_.getRef(); }
   TXOUT_SCRIPT_TYPE  getScriptType(void) const { return scriptType_; }
   TxOut              getCopy(void) const;
   uint32_t           getScriptSize(void) { return nBytes_ - scriptOffset_; }
   BinaryDataRef      serialize(void) { return self_; }
   BinaryDataRef      getScriptRef(void) ;

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr, uint32_t nbytes=0, TxRef* parent=NULL);
   void unserialize(BinaryRefReader & brr, uint32_t nbytes=0, TxRef* parent=NULL);
   void unserialize(BinaryDataRef const & str, uint32_t nbytes=0, TxRef* parent=NULL);

   void pprint(ostream & os=cout);

private:
   BinaryDataRef self_;

   // Derived properties - we expect these to be set after construct/copy
   uint32_t          nBytes_;
   uint32_t          scriptOffset_;
   TXOUT_SCRIPT_TYPE scriptType_;
   BinaryData        recipientBinAddr20_;
   TxRef*            parentTx_;

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
   TxRef(uint8_t const * ptr)       { unserialize(ptr);       }
   TxRef(BinaryRefReader & brr)     { unserialize(brr);       }
   TxRef(BinaryDataRef const & str) { unserialize(str);       }
   TxRef(BinaryData const & str)    { unserialize(str);       }
     
   uint8_t const * getPtr(void) const { assert(isInitialized_); return self_.getPtr(); }
   uint32_t        getSize(void) const { assert(isInitialized_); return self_.getSize(); }
   uint32_t        getNumTxIn(void)  const { assert(isInitialized_); return (uint32_t)offsetsTxIn_.size()-1;}
   uint32_t        getNumTxOut(void) const { assert(isInitialized_); return (uint32_t)offsetsTxOut_.size()-1;}
   BlockHeaderRef* getHeaderPtr(void)  const { assert(isInitialized_); return headerPtr_; }
   Tx              getCopy(void) const;

   /////////////////////////////////////////////////////////////////////////////

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr);
   void unserialize(BinaryRefReader & brr);
   void unserialize(BinaryDataRef const & str) { unserialize(str.getPtr()); }
   void unserialize(BinaryData const & str) { unserialize(str.getPtr()); }

   BinaryDataRef const & serialize(void) const { return self_; }
   BinaryData const & getThisHash(void) const { return thisHash_; }
   BinaryDataRef getThisHashRef(void) const { return BinaryDataRef(thisHash_); }


   /////////////////////////////////////////////////////////////////////////////
   // These are not pointers to persistent object, these methods actually 
   // CREATES the TxInRef/TxOutRef.  But the construction is fast, so it's
   // okay to do it on the fly
   TxInRef   getTxInRef(int i);
   TxOutRef  getTxOutRef(int i);
   TxIn      getTxInCopy(int i);
   TxOut     getTxOutCopy(int i);
   
   /////////////////////////////////////////////////////////////////////////////
   uint32_t getBlockTimestamp(void);
   uint32_t getBlockHeight(void);


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
