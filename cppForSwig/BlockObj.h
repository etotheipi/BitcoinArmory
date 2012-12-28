////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef _BLOCKOBJ_H_
#define _BLOCKOBJ_H_


#include <iostream>
#include <vector>
#include <map>
#include <cassert>

#include "BinaryData.h"
#include "FileDataPtr.h"



class TxRef;
class Tx;


class BlockHeader
{
   friend class BlockDataManager_FileRefs;

public:

   /////////////////////////////////////////////////////////////////////////////
   BlockHeader(void) : 
           isInitialized_(false),  isFinishedCalc_(false) {}
   BlockHeader(uint8_t const * ptr)       { unserialize(ptr); }
   BlockHeader(BinaryRefReader & brr)     { unserialize(brr); }
   BlockHeader(BinaryDataRef const & str) { unserialize(str); }
   BlockHeader(BinaryData    const & str) { unserialize(str); }
   // SWIG needs a non-overloaded method
   BlockHeader & unserialize_1_(BinaryData const & str) { unserialize(str); return *this; }

   uint32_t           getVersion(void) const      { return  *(uint32_t*)(getPtr()  );  }
   BinaryData const & getThisHash(void) const     { return thisHash_;                  }
   BinaryData         getPrevHash(void) const     { return BinaryData(getPtr()+4 ,32); }
   BinaryData const & getNextHash(void) const     { return nextHash_;                  }
   BinaryData         getMerkleRoot(void) const   { return BinaryData(getPtr()+36,32); }
   BinaryData         getDiffBits(void) const     { return BinaryData(getPtr()+72,4 ); }
   uint32_t           getTimestamp(void) const    { return  *(uint32_t*)(getPtr()+68); }
   uint32_t           getNonce(void) const        { return  *(uint32_t*)(getPtr()+76); }
   uint32_t           getBlockHeight(void) const  { return blockHeight_;               }
   bool               isMainBranch(void) const    { return isMainBranch_;              }
   bool               isOrphan(void) const        { return isOrphan_;                  }
   double             getDifficulty(void) const   { return difficultyDbl_;             }
   double             getDifficultySum(void) const{ return difficultySum_;             }

   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef  getThisHashRef(void) const   { return thisHash_.getRef();            }
   BinaryDataRef  getPrevHashRef(void) const   { return BinaryDataRef(getPtr()+4, 32); }
   BinaryDataRef  getNextHashRef(void) const   { return nextHash_.getRef();            }
   BinaryDataRef  getMerkleRootRef(void) const { return BinaryDataRef(getPtr()+36,32); }
   BinaryDataRef  getDiffBitsRef(void) const   { return BinaryDataRef(getPtr()+72,4 ); }
   uint32_t       getNumTx(void) const         { return txPtrList_.size();             }

   /////////////////////////////////////////////////////////////////////////////
   uint8_t const * getPtr(void) const  { assert(isInitialized_); return dataCopy_.getPtr(); }
   uint32_t        getSize(void) const { assert(isInitialized_); return dataCopy_.getSize(); }
   uint32_t        isInitialized(void) const { return isInitialized_; }
   uint32_t        getBlockSize(void) const;
   FileDataPtr     getBlockFilePtr(void) { return thisBlockFilePtr_; }
   void            setBlockFilePtr(FileDataPtr b) { thisBlockFilePtr_ = b; }


   /////////////////////////////////////////////////////////////////////////////
   vector<TxRef*> &   getTxRefPtrList(void) {return txPtrList_;}
   vector<BinaryData> getTxHashList(void);
   BinaryData         calcMerkleRoot(vector<BinaryData>* treeOut=NULL);
   bool               verifyMerkleRoot(void);
   bool               verifyIntegrity(void);

   /////////////////////////////////////////////////////////////////////////////
   void          pprint(ostream & os=cout, int nIndent=0, bool pBigendian=true) const;
   void          pprintAlot(ostream & os=cout);

   /////////////////////////////////////////////////////////////////////////////
   BinaryData    serialize(void)    { return dataCopy_; }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData    serializeWholeBlock(BinaryData const & magic, 
                                     bool withLead8Bytes=true) const;

   // Just in case we ever want to calculate a difficulty-1 header via CPU...
   uint32_t      findNonce(void);

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr);
   void unserialize(BinaryData const & str) { unserialize(str.getRef()); }
   void unserialize(BinaryDataRef const & str);
   void unserialize(BinaryRefReader & brr);

   void clearDataCopy() {dataCopy_.resize(0);}

private:
   BinaryData     dataCopy_;
   bool           isInitialized_;

   // Derived properties - we expect these to be set after construct/copy
   BinaryData     thisHash_;
   double         difficultyDbl_;
   FileDataPtr    thisBlockFilePtr_;  // points to beginning of blk, magic bytes

   // Need to compute these later
   BinaryData     nextHash_;
   uint32_t       blockHeight_;
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
class OutPoint
{
   friend class BlockDataManager_FileRefs;
   friend class OutPointRef;

public:
   OutPoint(void) : txHash_(32), txOutIndex_(UINT32_MAX) { }

   OutPoint(uint8_t const * ptr) { unserialize(ptr); }
   OutPoint(BinaryData const & txHash, uint32_t txOutIndex) : 
                txHash_(txHash), txOutIndex_(txOutIndex) { }

   BinaryData const &   getTxHash(void)     const { return txHash_; }
   BinaryDataRef        getTxHashRef(void)  const { return BinaryDataRef(txHash_); }
   uint32_t             getTxOutIndex(void) const { return txOutIndex_; }

   void setTxHash(BinaryData const & hash) { txHash_.copyFrom(hash); }
   void setTxOutIndex(uint32_t idx) { txOutIndex_ = idx; }

   // Define these operators so that we can use OutPoint as a map<> key
   bool operator<(OutPoint const & op2) const;
   bool operator==(OutPoint const & op2) const;

   void        serialize(BinaryWriter & bw);
   BinaryData  serialize(void);
   void        unserialize(uint8_t const * ptr);
   void        unserialize(BinaryReader & br);
   void        unserialize(BinaryRefReader & brr);
   void        unserialize(BinaryData const & bd);
   void        unserialize(BinaryDataRef const & bdRef);

private:
   BinaryData txHash_;
   uint32_t   txOutIndex_;

};



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxIn
{
   friend class BlockDataManager_FileRefs;

public:
   TxIn(void) : dataCopy_(0), scriptType_(TXIN_SCRIPT_UNKNOWN), 
                scriptOffset_(0), parentHash_(0) {}

   // Ptr to the beginning of the TxIn, last two arguments are supplemental
   TxIn(uint8_t const * ptr,  
        uint32_t        nBytes=0, 
        TxRef*          parent=NULL, 
        int32_t         idx=-1) { unserialize(ptr, nBytes, parent, idx); } 

   uint8_t const *  getPtr(void) const { assert(isInitialized()); return dataCopy_.getPtr(); }
   uint32_t         getSize(void) const { assert(isInitialized()); return dataCopy_.getSize(); }
   bool             isStandard(void) const { return scriptType_!=TXIN_SCRIPT_UNKNOWN; }
   bool             isCoinbase(void) const;
   bool             isInitialized(void) const {return dataCopy_.getSize() > 0; }
   OutPoint         getOutPoint(void) const;

   // Script ops
   BinaryData       getScript(void) const;
   BinaryDataRef    getScriptRef(void) const;
   uint32_t         getScriptSize(void) { return getSize() - (scriptOffset_ + 4); }
   TXIN_SCRIPT_TYPE getScriptType(void) const { return scriptType_; }
   uint32_t         getScriptOffset(void) const { return scriptOffset_; }

   // SWIG doesn't handle these enums well, so we will provide some direct bools
   bool             isScriptStandard(void) { return scriptType_ == TXIN_SCRIPT_STANDARD;}
   bool             isScriptCoinbase(void) { return scriptType_ == TXIN_SCRIPT_COINBASE;}
   bool             isScriptSpendCB(void)  { return scriptType_ == TXIN_SCRIPT_SPENDCB; }
   bool             isScriptUnknown(void)  { return scriptType_ == TXIN_SCRIPT_UNKNOWN; }

   TxRef*           getParentTxPtr(void) { return parentTx_; }
   uint32_t         getIndex(void) { return index_; }

   void setParentTx(TxRef* txref, int32_t idx=-1) { parentTx_=txref; index_=idx;}

   uint32_t         getSequence(void)   { return *(uint32_t*)(getPtr()+getSize()-4); }

   BinaryData       getParentHash(void);
   uint32_t         getParentHeight(void);

   void             setParentHash(BinaryData const & txhash) {parentHash_ = txhash;}
   void             setParentHeight(uint32_t blkheight) {parentHeight_ = blkheight;}

   /////////////////////////////////////////////////////////////////////////////
   BinaryData       serialize(void)    { return dataCopy_; }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr, 
                        uint32_t nbytes=0, TxRef* parent=NULL, int32_t idx=-1);
   void unserialize(BinaryData    const & str, 
                        uint32_t nbytes=0, TxRef* parent=NULL, int32_t idx=-1);
   void unserialize(BinaryDataRef const & str, 
                        uint32_t nbytes=0, TxRef* parent=NULL, int32_t idx=-1);
   void unserialize(BinaryRefReader & brr, 
                        uint32_t nbytes=0, TxRef* parent=NULL, int32_t idx=-1);

   /////////////////////////////////////////////////////////////////////////////
   // Not all TxIns have sendor info.  Might have to go to the Outpoint and get
   // the corresponding TxOut to find the sender.  In the case the sender is
   // not available, return false and don't write the output
   bool       getSenderAddrIfAvailable(BinaryData & addrTarget) const;
   BinaryData getSenderAddrIfAvailable(void) const;

   void pprint(ostream & os=cout, int nIndent=0, bool pBigendian=true) const;


private:
   BinaryData       dataCopy_;
   BinaryData       parentHash_;
   uint32_t         parentHeight_;

   // Derived properties - we expect these to be set after construct/copy
   uint32_t         index_;
   TXIN_SCRIPT_TYPE scriptType_;
   uint32_t         scriptOffset_;
   TxRef*           parentTx_;


};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxOut
{
   friend class BlockDataManager_FileRefs;

public:

   /////////////////////////////////////////////////////////////////////////////
   TxOut(void) : dataCopy_(0), parentHash_(0) {}
   TxOut(uint8_t const * ptr, 
         uint32_t        nBytes=0, 
         TxRef*          parent=NULL, 
         int32_t         idx=-1) { unserialize(ptr, nBytes, parent, idx); } 

   uint8_t const * getPtr(void) const { return dataCopy_.getPtr(); }
   uint32_t        getSize(void) const { return dataCopy_.getSize(); }
   uint64_t        getValue(void) const { return *(uint64_t*)(dataCopy_.getPtr()); }
   bool            isStandard(void) const { return scriptType_ != TXOUT_SCRIPT_UNKNOWN; }
   bool            isInitialized(void) const {return dataCopy_.getSize() > 0; }
   TxRef*          getParentTxPtr(void) { return parentTx_; }
   uint32_t        getIndex(void) { return index_; }

   void setParentTx(TxRef * txref, int32_t idx=-1) { parentTx_=txref; index_=idx;}


   /////////////////////////////////////////////////////////////////////////////
   BinaryData const & getRecipientAddr(void) const    { return recipientBinAddr20_; }
   BinaryDataRef      getRecipientAddrRef(void) const { return recipientBinAddr20_.getRef(); }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData         getScript(void);
   BinaryDataRef      getScriptRef(void);
   TXOUT_SCRIPT_TYPE  getScriptType(void) const { return scriptType_; }
   uint32_t           getScriptSize(void) const { return getSize() - scriptOffset_; }

   // SWIG doesn't handle these enums well, so we will provide some direct bools
   bool               isScriptStandard(void) { return scriptType_ == TXOUT_SCRIPT_STANDARD;}
   bool               isScriptCoinbase(void) { return scriptType_ == TXOUT_SCRIPT_COINBASE;}
   bool               isScriptUnknown(void)  { return scriptType_ == TXOUT_SCRIPT_UNKNOWN; }


   /////////////////////////////////////////////////////////////////////////////
   BinaryData         serialize(void) { return BinaryData(dataCopy_); }
   BinaryDataRef      serializeRef(void) { return dataCopy_; }

   BinaryData         getParentHash(void);
   uint32_t           getParentHeight(void);

   void               setParentHash(BinaryData const & txhash) {parentHash_ = txhash;}
   void               setParentHeight(uint32_t blkheight) {parentHeight_ = blkheight;}

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr, 
                         uint32_t nbytes=0, TxRef* parent=NULL, int32_t idx=-1);
   void unserialize(BinaryData const & str, 
                         uint32_t nbytes=0, TxRef* parent=NULL, int32_t idx=-1);
   void unserialize(BinaryDataRef const & str, 
                         uint32_t nbytes=0, TxRef* parent=NULL, int32_t idx=-1);
   void unserialize(BinaryRefReader & brr, 
                         uint32_t nbytes=0, TxRef* parent=NULL, int32_t idx=-1);

   void  pprint(ostream & os=cout, int nIndent=0, bool pBigendian=true);

private:
   BinaryData        dataCopy_;
   BinaryData        parentHash_;
   uint32_t          parentHeight_;

   // Derived properties - we expect these to be set after construct/copy
   uint32_t          scriptOffset_;
   uint32_t          index_;
   TXOUT_SCRIPT_TYPE scriptType_;
   BinaryData        recipientBinAddr20_;
   TxRef*            parentTx_;

   // No computed variables, because we're always re-computing these
   // objects every time we want them


};





////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class Tx
{
   friend class BlockDataManager_FileRefs;

public:
   Tx(void) : isInitialized_(false), headerPtr_(NULL), txRefPtr_(NULL),
              offsetsTxIn_(0), offsetsTxOut_(0) {}
   Tx(uint8_t const * ptr)       { unserialize(ptr);       }
   Tx(BinaryRefReader & brr)     { unserialize(brr);       }
   Tx(BinaryData const & str)    { unserialize(str);       }
   Tx(BinaryDataRef const & str) { unserialize(str);       }
   Tx(TxRef* txref);
     
   uint8_t const * getPtr(void) const { return dataCopy_.getPtr(); }
   uint32_t        getSize(void) const {  return dataCopy_.getSize(); }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t           getVersion(void)   const { return *(uint32_t*)(dataCopy_.getPtr()+4);}
   uint32_t           getNumTxIn(void)   const { return offsetsTxIn_.size()-1;}
   uint32_t           getNumTxOut(void)  const { return offsetsTxOut_.size()-1;}
   BinaryData         getThisHash(void)  const;
   bool               isMainBranch(void) const;
   bool               isInitialized(void) const { return isInitialized_; }


   uint32_t           getTxInOffset(uint32_t i) const  { return offsetsTxIn_[i]; }
   uint32_t           getTxOutOffset(uint32_t i) const { return offsetsTxOut_[i]; }

   static Tx          createFromStr(BinaryData const & bd) {return Tx(bd);}

   TxRef*             getTxRefPtr(void) const { return txRefPtr_; }
   void               setTxRefPtr(TxRef* ptr) { txRefPtr_ = ptr; }
   BlockHeader*       getHeaderPtr(void)  const { return headerPtr_; }
   void               setHeaderPtr(BlockHeader* bh)   { headerPtr_ = bh; }

   // This is to identify whether this tx has an counterpart on disk
   // If not, it's just a floater (probably zero-conf tx) and we need
   // to avoid using the txRefPtr_
   bool               isTethered(void) {return txRefPtr_!=NULL; }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData         serialize(void) const    { return dataCopy_; }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr);
   void unserialize(BinaryData const & str) { unserialize(str.getPtr()); }
   void unserialize(BinaryDataRef const & str) { unserialize(str.getPtr()); }
   void unserialize(BinaryRefReader & brr);

   uint32_t    getLockTime(void) const { return lockTime_; }
   uint64_t    getSumOfOutputs(void);


   BinaryData getRecipientForTxOut(uint32_t txOutIndex);

   /////////////////////////////////////////////////////////////////////////////
   // These are not pointers to persistent object, these methods actually 
   // CREATES the TxIn/TxOut.  But the construction is fast, so it's
   // okay to do it on the fly
   TxIn   getTxIn(int i);
   TxOut  getTxOut(int i);

   /////////////////////////////////////////////////////////////////////////////
   uint32_t  getBlockTimestamp(void);
   uint32_t  getBlockHeight(void);
   uint32_t  getBlockTxIndex(void);

   /////////////////////////////////////////////////////////////////////////////
   void pprint(ostream & os=cout, int nIndent=0, bool pBigendian=true);
   void pprintAlot(ostream & os=cout);


   


private:
   // Full copy of the serialized tx
   BinaryData    dataCopy_;
   bool          isInitialized_;

   uint32_t      version_;
   uint32_t      lockTime_;
   
   // Derived properties - we expect these to be set after construct/copy
   BinaryData    thisHash_;

   // Will always create TxIns and TxOuts on-the-fly; only store the offsets
   vector<uint32_t> offsetsTxIn_;
   vector<uint32_t> offsetsTxOut_;

   // To be calculated later
   BlockHeader*  headerPtr_;
   TxRef*        txRefPtr_;
};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxRef
{
   friend class BlockDataManager_FileRefs;
   friend class Tx;

public:
   /////////////////////////////////////////////////////////////////////////////
   TxRef(void) : headerPtr_(NULL) {}
   TxRef(FileDataPtr fdr) : blkFilePtr_(fdr), headerPtr_(NULL) {}
     
   /////////////////////////////////////////////////////////////////////////////
   BinaryData         getThisHash(void) const;
   Tx                 getTxCopy(void) const;
   bool               isMainBranch(void)  const;
   uint32_t           getSize(void) const {  return blkFilePtr_.getNumBytes(); }

   /////////////////////////////////////////////////////////////////////////////
   BlockHeader*       getHeaderPtr(void)  const { return headerPtr_; }
   void               setHeaderPtr(BlockHeader* bh)   { headerPtr_ = bh; }
   FileDataPtr        getBlkFilePtr(void) { return blkFilePtr_; }
   void               setBlkFilePtr(FileDataPtr const & b) { blkFilePtr_ = b; }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData         serialize(void) const { return blkFilePtr_.getDataCopy(); }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t           getBlockTimestamp(void) const;
   uint32_t           getBlockHeight(void) const;
   uint32_t           getBlockTxIndex(void) const;

   /////////////////////////////////////////////////////////////////////////////
   void               pprint(ostream & os=cout, int nIndent=0) const;

private:
   FileDataPtr        blkFilePtr_;
   BlockHeader*       headerPtr_;
};





////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// This class is mainly for sorting by priority
class UnspentTxOut
{
public:
   UnspentTxOut(void);
   UnspentTxOut(TxOut & txout, uint32_t blknum) { init(txout, blknum);}

   void init(TxOut & txout, uint32_t blknum);

   BinaryData   getTxHash(void) const      { return txHash_;     }
   uint32_t     getTxOutIndex(void) const  { return txOutIndex_; }
   uint64_t     getValue(void)  const      { return value_;      }
   uint64_t     getTxHeight(void)  const   { return txHeight_;   }
   uint32_t     getNumConfirm(void) const  { return numConfirm_; }

   OutPoint getOutPoint(void) const { return OutPoint(txHash_, txOutIndex_); }

   BinaryData const & getScript(void) const      { return script_;     }
   BinaryData   getRecipientAddr(void) const;

   uint32_t   updateNumConfirm(uint32_t currBlknum);
   void pprintOneLine(uint32_t currBlk=UINT32_MAX);


   //float getPriority(void);  
   //bool operator<(UnspentTxOut const & t2)
                     //{ return (getPriority() < t2.getPriority()); }
   //bool operator==(UnspentTxOut const & t2)
                     //{ return (getPriority() == t2.getPriority()); }

   // These four methods are listed from steepest-to-shallowest in terms of 
   // how much they favor large inputs over small inputs.  
   // NOTE:  This isn't useful at all anymore:  it was hardly useful even before
   //        I had UTXO sorting in python.  This was really more experimental 
   //        than anything, so I wouldn't bother doing anything with it unless
   //        you want to use it as a template for custom sorting in C++
   static bool CompareNaive(UnspentTxOut const & uto1, UnspentTxOut const & uto2);
   static bool CompareTech1(UnspentTxOut const & uto1, UnspentTxOut const & uto2);
   static bool CompareTech2(UnspentTxOut const & uto1, UnspentTxOut const & uto2);
   static bool CompareTech3(UnspentTxOut const & uto1, UnspentTxOut const & uto2);
   static void sortTxOutVect(vector<UnspentTxOut> & utovect, int sortType=1);


public:
   BinaryData txHash_;
   uint32_t   txOutIndex_;
   uint32_t   txHeight_;
   uint64_t   value_;
   BinaryData script_;
   uint32_t   numConfirm_;

   // This can be set and used as part of a compare function:  if you want
   // each TxOut prioritization to be dependent on the target Tx amount.
   uint64_t   targetTxAmount_;
};

#endif

