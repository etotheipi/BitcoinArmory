////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>             //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

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

   uint32_t           getVersion(void) const      { return  *(uint32_t*)(getPtr()  );  }
   BinaryData const & getThisHash(void) const     { return thisHash_;                  }
   BinaryData         getPrevHash(void) const     { return BinaryData(getPtr()+4 ,32); }
   BinaryData const & getNextHash(void) const     { return nextHash_;                  }
   BinaryData         getMerkleRoot(void) const   { return BinaryData(getPtr()+36,32); }
   BinaryData         getDiffBits(void) const     { return BinaryData(getPtr()+72,4 ); }
   uint32_t           getTimestamp(void) const    { return  *(uint32_t*)(getPtr()+68); }
   uint32_t           getNonce(void) const        { return  *(uint32_t*)(getPtr()+76); }
   uint32_t           getBlockHeight(void) const  { return blockHeight_;               }
   uint32_t           isMainBranch(void) const    { return isMainBranch_;              }
   uint32_t           isOrphan(void) const        { return isOrphan_;                  }
   double             getDifficulty(void) const   { return difficultyDbl_;             }
   double             getDifficultySum(void) const{ return difficultySum_;             }
   uint32_t           getNumTx(void) const        { return numTx_;                     }

   BinaryDataRef getThisHashRef(void) const   { return thisHash_.getRef();            }
   BinaryDataRef getPrevHashRef(void) const   { return BinaryDataRef(getPtr()+4, 32); }
   BinaryDataRef getNextHashRef(void) const   { return nextHash_.getRef();            }
   BinaryDataRef getMerkleRootRef(void) const { return BinaryDataRef(getPtr()+36,32); }
   BinaryDataRef getDiffBitsRef(void) const   { return BinaryDataRef(getPtr()+72,4 ); }

   uint8_t const * getPtr(void) const  { assert(isInitialized_); return self_.getPtr(); }
   uint32_t        getSize(void) const { assert(isInitialized_); return self_.getSize(); }
   uint32_t        isInitialized(void) const { return isInitialized_; }
   uint32_t        getBlockSize(void) const;


   /////////////////////////////////////////////////////////////////////////////
   vector<TxRef*> &   getTxRefPtrList(void) {return txPtrList_;}
   vector<BinaryData> getTxHashList(void);
   BinaryData         calcMerkleRoot(vector<BinaryData>* treeOut=NULL);
   bool               verifyMerkleRoot(void);
   bool               verifyIntegrity(void);

   /////////////////////////////////////////////////////////////////////////////
   BlockHeader   getCopy(void) const;
   void          pprint(ostream & os=cout, int nIndent=0, bool pBigendian=true) const;

   /////////////////////////////////////////////////////////////////////////////
   BinaryData    serialize(void)    { return BinaryData(self_); }
   BinaryDataRef serializeRef(void) { return            self_;  }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr);
   void unserialize(BinaryData const & str) { unserialize(str.getRef()); }
   void unserialize(BinaryDataRef const & str);
   void unserialize(BinaryRefReader & brr);


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
   BinaryData    getTxHash(void) const     { return BinaryData(   self_.getPtr(),32); }
   BinaryDataRef getTxHashRef(void) const  { return BinaryDataRef(self_.getPtr(),32); }
   uint32_t      getTxOutIndex(void) const { return *(uint32_t*)(self_.getPtr()+32);  }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData    serialize(void) const     { return BinaryData(self_); }
   BinaryDataRef serializeRef(void) const  { return            self_;  }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr)       { self_.setRef(ptr, 36); }
   void unserialize(BinaryData const & str)    { unserialize(str.getPtr()); } 
   void unserialize(BinaryDataRef const & str) { unserialize(str.getPtr()); } 
   void unserialize(BinaryRefReader & brr)     { unserialize(brr.get_BinaryDataRef(36)); }

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
                   scriptOffset_(0) {}

   TxInRef(uint8_t const * ptr, uint32_t nBytes=0, TxRef* parent=NULL) 
                                       { unserialize(ptr, nBytes, parent); } 

   uint8_t const *  getPtr(void) const { assert(isInitialized()); return self_.getPtr(); }
   uint32_t         getSize(void) const { assert(isInitialized()); return self_.getSize(); }
   bool             isStandard(void) const { return scriptType_!=TXIN_SCRIPT_UNKNOWN; }
   bool             isCoinbase(void) const;
   bool             isInitialized(void) const {return self_.getSize() > 0; }
   TXIN_SCRIPT_TYPE getScriptType(void) const { return scriptType_; }
   uint32_t         getScriptOffset(void) const { return scriptOffset_; }

   TxIn             getCopy(void) const;
   TxRef*           getParentTxPtr(void) { return parentTx_; }
   void             setParentTxPtr(TxRef * txref) { parentTx_ = txref; }

   uint32_t         getSequence(void)   { return *(uint32_t*)(getPtr()+getSize()-4); }
   uint32_t         getScriptSize(void) { return nBytes_ - (scriptOffset_ + 4); }

   OutPoint         getOutPoint(void) const;
   OutPointRef      getOutPointRef(void) const;
   BinaryData       getScript(void) const;
   BinaryDataRef    getScriptRef(void) const;

   // SWIG doesn't handle these enums well, so we will provide some direct bools
   bool             isScriptStandard(void) { return scriptType_ == TXIN_SCRIPT_STANDARD;}
   bool             isScriptCoinbase(void) { return scriptType_ == TXIN_SCRIPT_COINBASE;}
   bool             isScriptSpendCB(void)  { return scriptType_ == TXIN_SCRIPT_SPENDCB; }
   bool             isScriptUnknown(void)  { return scriptType_ == TXIN_SCRIPT_UNKNOWN; }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData    serialize(void)    { return BinaryData(self_); }
   BinaryDataRef serializeRef(void) { return            self_;  }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr, uint32_t nbytes=0, TxRef* parent=NULL);
   void unserialize(BinaryData    const & str, uint32_t nbytes=0, TxRef* parent=NULL);
   void unserialize(BinaryDataRef const & str, uint32_t nbytes=0, TxRef* parent=NULL);
   void unserialize(BinaryRefReader & brr, uint32_t nbytes=0, TxRef* parent=NULL);

   /////////////////////////////////////////////////////////////////////////////
   // Not all TxIns have sendor info.  Might have to go to the Outpoint and get
   // the corresponding TxOut to find the sender.  In the case the sender is
   // not available, return false and don't write the output
   bool       getSenderAddrIfAvailable(BinaryData & addrTarget) const;
   BinaryData getSenderAddrIfAvailable(void) const;

   void pprint(ostream & os=cout, int nIndent=0, bool pBigendian=true) const;


private:
   BinaryDataRef self_;

   // Derived properties - we expect these to be set after construct/copy
   uint32_t         nBytes_;
   TXIN_SCRIPT_TYPE scriptType_;
   uint32_t         scriptOffset_;
   TxRef*           parentTx_;

   // No computed variables, because we're always re-computing these
   // objects every time we want them
   
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
   TxRef*          getParentTxPtr(void) { return parentTx_; }
   void            setParentTxPtr(TxRef * txref) { parentTx_ = txref; }

   /////////////////////////////////////////////////////////////////////////////
   TXOUT_SCRIPT_TYPE  getScriptType(void) const { return scriptType_; }
   uint32_t           getScriptSize(void) const { return nBytes_ - scriptOffset_; }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData const & getRecipientAddr(void) const    { return recipientBinAddr20_; }
   BinaryDataRef      getRecipientAddrRef(void) const { return recipientBinAddr20_.getRef(); }
   BinaryData         getScript(void);
   BinaryDataRef      getScriptRef(void);

   // SWIG doesn't handle these enums well, so we will provide some direct bools
   bool               isScriptStandard(void) { return scriptType_ == TXOUT_SCRIPT_STANDARD;}
   bool               isScriptCoinbase(void) { return scriptType_ == TXOUT_SCRIPT_COINBASE;}
   bool               isScriptUnknown(void)  { return scriptType_ == TXOUT_SCRIPT_UNKNOWN; }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData         serialize(void) { return BinaryData(self_); }
   BinaryDataRef      serializeRef(void) { return self_; }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr, uint32_t nbytes=0, TxRef* parent=NULL);
   void unserialize(BinaryData const & str, uint32_t nbytes=0, TxRef* parent=NULL);
   void unserialize(BinaryDataRef const & str, uint32_t nbytes=0, TxRef* parent=NULL);
   void unserialize(BinaryRefReader & brr, uint32_t nbytes=0, TxRef* parent=NULL);

   TxOut getCopy(void) const;
   void  pprint(ostream & os=cout, int nIndent=0, bool pBigendian=true);

private:
   BinaryDataRef self_;

   // Derived properties - we expect these to be set after construct/copy
   uint32_t          nBytes_;
   uint32_t          scriptOffset_;
   TXOUT_SCRIPT_TYPE scriptType_;
   BinaryData        recipientBinAddr20_;
   TxRef*            parentTx_;

   // No computed variables, because we're always re-computing these
   // objects every time we want them


};

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxRef
{
   friend class BlockDataManager_FullRAM;

public:
   TxRef(void) : isInitialized_(false), isMainBranch_(false) {}
   TxRef(uint8_t const * ptr)       { unserialize(ptr);       }
   TxRef(BinaryRefReader & brr)     { unserialize(brr);       }
   TxRef(BinaryData const & str)    { unserialize(str);       }
   TxRef(BinaryDataRef const & str) { unserialize(str);       }
     
   uint8_t const * getPtr(void) const { return self_.getPtr(); }
   uint32_t        getSize(void) const {  return self_.getSize(); }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t           getVersion(void)  const { return *(uint32_t*)(self_.getPtr()+4);}
   uint32_t           getNumTxIn(void)  const { return offsetsTxIn_.size()-1;}
   uint32_t           getNumTxOut(void) const { return offsetsTxOut_.size()-1;}
   BinaryData const & getThisHash(void) const    { return thisHash_; }
   BinaryDataRef      getThisHashRef(void) const { return BinaryDataRef(thisHash_); }
   void               setMainBranch(bool b=true) { isMainBranch_ = b; }
   bool               isMainBranch(void)  { return isMainBranch_; }

   Tx              getCopy(void) const;
   BlockHeaderRef* getHeaderPtr(void)  const { return headerPtr_; }
   void            setHeaderPtr(BlockHeaderRef* bhr)   { headerPtr_ = bhr; }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData    serialize(void) const    { return BinaryData(self_); }
   BinaryDataRef serializeRef(void) const { return            self_;  }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr);
   void unserialize(BinaryData const & str) { unserialize(str.getPtr()); }
   void unserialize(BinaryDataRef const & str) { unserialize(str.getPtr()); }
   void unserialize(BinaryRefReader & brr);

   // We actually can't get the sum of inputs without going and finding the 
   // referenced TxOuts -- need BDM to help with this
   //uint64_t    getSumOfInputs(void);
   uint32_t    getLockTime(void)  const;
   uint64_t    getSumOfOutputs(void);


   /////////////////////////////////////////////////////////////////////////////
   // These are not pointers to persistent object, these methods actually 
   // CREATES the TxInRef/TxOutRef.  But the construction is fast, so it's
   // okay to do it on the fly
   TxInRef   getTxInRef(int i);
   TxOutRef  getTxOutRef(int i);
   TxIn      getTxInCopy(int i);
   TxOut     getTxOutCopy(int i);
   
   /////////////////////////////////////////////////////////////////////////////
   uint32_t  getBlockTimestamp(void);
   uint32_t  getBlockHeight(void);

   /////////////////////////////////////////////////////////////////////////////
   void pprint(ostream & os=cout, int nIndent=0, bool pBigendian=true);

private:
   BinaryDataRef self_; 
   bool isInitialized_;

   // Derived properties - we expect these to be set after construct/copy
   BinaryData       thisHash_;
   uint32_t         nBytes_;
   uint64_t         fileByteLoc_;
   vector<uint32_t> offsetsTxIn_;
   vector<uint32_t> offsetsTxOut_;

   // To be calculated/set later
   BlockHeaderRef*  headerPtr_;
   bool             isMainBranch_;

};


#endif
