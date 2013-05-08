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
//#include "FileDataPtr.h"



class TxRef;
class Tx;


class BlockHeader
{
   friend class BlockDataManager_LevelDB;
   friend class InterfaceToLevelDB;

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
   uint32_t        setBlockSize(uint32_t sz) { wholeBlockSize_ = sz; }
   //FileDataPtr     getBlockFilePtr(void) { return thisBlockFilePtr_; }
   //void            setBlockFilePtr(FileDataPtr b) { thisBlockFilePtr_ = b; }


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
                                     bool withLead8Bytes) const;

   // Just in case we ever want to calculate a difficulty-1 header via CPU...
   uint32_t      findNonce(void);

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr);
   void unserialize(BinaryData const & str) { unserialize(str.getRef()); }
   void unserialize(BinaryDataRef const & str);
   void unserialize(BinaryRefReader & brr);

   void unserialize_swigsafe_(BinaryData const & rawHead) { unserialize(rawHead); }

   void clearDataCopy() {dataCopy_.resize(0);}

private:
   BinaryData     dataCopy_;
   bool           isInitialized_;

   // Derived properties - we expect these to be set after construct/copy
   BinaryData     thisHash_;
   double         difficultyDbl_;
   //FileDataPtr    thisBlockFilePtr_;  // points to beginning of blk, magic bytes


   // Need to compute these later
   BinaryData     nextHash_;
   uint32_t       blockHeight_;
   double         difficultySum_;
   bool           isMainBranch_;
   bool           isOrphan_;
   bool           isFinishedCalc_;
   bool           isOnDiskYet_;
   uint32_t       wholeBlockSize_;
   vector<TxRef*> txPtrList_;

   // Added for LevelDB engine, which indexes block by height
   // This is just a hint so we can go directly to the correct
   // block in the blkdata DB, instead of searching all blocks
   // at the same height (though, there's usually 1, rarely >2)
   uint32_t       storedNumTx_;
   uint32_t       storedNumBytes_;
   uint32_t       storedHeight_;
   BinaryData     merkle_;
   bool           merkleIsPartial_;
   uint8_t        duplicateID_;
   bool           haveAllTx_;
};



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// OutPoint is just a reference to a TxOut
class OutPoint
{
   friend class BlockDataManager_LevelDB;
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

   void unserialize_swigsafe_(BinaryData const & rawOP) { unserialize(rawOP); }

private:
   BinaryData txHash_;
   uint32_t   txOutIndex_;

};



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxIn
{
   friend class BlockDataManager_LevelDB;
   friend class InterfaceToLevelDB;

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

   void unserialize_swigsafe_(BinaryData const & rawIn) { unserialize(rawIn); }

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
   friend class BlockDataManager_LevelDB;
   friend class InterfaceToLevelDB;

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

   void unserialize_swigsafe_(BinaryData const & rawOut) { unserialize(rawOut); }

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

   // LevelDB extras related to reading these from storage before verifying
   uint32_t          storedHeight_;
   uint8_t           storedDupID_;
   uint16_t          storedTxIndex_;
   uint16_t          storedTxOutIndex_;
   bool              storedIsValid_;
   uint32_t          spentByHgtX_;
   uint16_t          spentByTxIndex_;


};





////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class Tx
{
   friend class BlockDataManager_LevelDB;
   friend class InterfaceToLevelDB;

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
   void unserialize_swigsafe_(BinaryData const & rawTx) { unserialize(rawTx); }


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

   // LevelDB modifications
   bool          isPartial_;
   uint32_t      storedHeight_;
   uint8_t       storedDupID_;
   uint8_t       storedIndex_;
   uint32_t      storedNumTxOut_;
   uint8_t       storedValid_;
   vector<TxOut> storedTxOuts_;
};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxRef
{
   friend class BlockDataManager_LevelDB;
   friend class Tx;

public:
   /////////////////////////////////////////////////////////////////////////////
   TxRef(void) : ldbKey8B_(0), headerPtr_(NULL) {}
   //TxRef(FileDataPtr fdr) : blkFilePtr_(fdr), headerPtr_(NULL) {}
     
   /////////////////////////////////////////////////////////////////////////////
   BinaryData         getThisHash(void) const;
   Tx                 getTxCopy(void) const;
   bool               isMainBranch(void)  const;
   uint32_t           getSize(void) const {  return blkFilePtr_.getNumBytes(); }

   /////////////////////////////////////////////////////////////////////////////
   BlockHeader*       getHeaderPtr(void)  const { return headerPtr_; }
   void               setHeaderPtr(BlockHeader* bh)   { headerPtr_ = bh; }
   //FileDataPtr        getBlkFilePtr(void) { return blkFilePtr_; }
   //void               setBlkFilePtr(FileDataPtr const & b) { blkFilePtr_ = b; }
   BinaryData         getLevelDBKey(void) { return ldbKey8B_;}
   void               setLevelDBKey(BinaryData const & bd) { ldbKey8B_ = bd;}


   /////////////////////////////////////////////////////////////////////////////
   BinaryData         serialize(void) const { return blkFilePtr_.getDataCopy(); }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t           getBlockTimestamp(void) const;
   uint32_t           getBlockHeight(void) const;
   uint32_t           getBlockTxIndex(void) const;

   /////////////////////////////////////////////////////////////////////////////
   void               pprint(ostream & os=cout, int nIndent=0) const;

private:
   //FileDataPtr        blkFilePtr_;
   BinaryData         ldbKey8B_;  // hgt(3) + dup(1) + txIdx(2) + txOutIdx(2)
   BlockHeader*       headerPtr_;
};


////////////////////////////////////////////////////////////////////////////////
// TxIOPair
//
// This makes a lot of sense, despite the added complexity.  No TxIn exists
// unless there was a TxOut, and they both have the same value, so we will
// store them together here.
//
// This will provide the future benefit of easily determining what Tx data
// can be pruned.  If a TxIOPair has both TxIn and TxOut, then the value 
// was received and spent, contributes zero to our balance, and can effectively
// ignored.  For now we will maintain them, but in the future we may decide
// to just start removing TxIOPairs after they are spent (in which case they 
// are no longer TxIO pairs, they're just TxO's...which eventually are removed)
//
//
class TxIOPair
{
public:
   //////////////////////////////////////////////////////////////////////////////
   // TODO:  since we tend not to track TxIn/TxOuts but make them on the fly,
   //        we should probably do that here, too.  I designed this before I
   //        realized that these copies will fall out of sync on a reorg
   TxIOPair(void);
   TxIOPair(uint64_t  amount);
   TxIOPair(TxRef* txPtrO, uint32_t txoutIndex);
   TxIOPair(TxRef* txPtrO, uint32_t txoutIndex, TxRef* txPtrI, uint32_t txinIndex);

   // Lots of accessors
   bool      hasTxOut(void) const   { return (txPtrOfOutput_   != NULL); }
   bool      hasTxIn(void) const    { return (txPtrOfInput_    != NULL); }
   bool      hasTxOutInMain(void) const;
   bool      hasTxInInMain(void) const;
   bool      hasTxOutZC(void) const;
   bool      hasTxInZC(void) const;
   bool      hasValue(void) const   { return (amount_!=0); }
   uint64_t  getValue(void) const   { return  amount_;}

   //////////////////////////////////////////////////////////////////////////////
   TxOut     getTxOut(void) const;   
   TxIn      getTxIn(void) const;   
   TxOut     getTxOutZC(void) const {return txOfOutputZC_->getTxOut(indexOfOutputZC_);}
   TxIn      getTxInZC(void) const  {return txOfInputZC_->getTxIn(indexOfInputZC_);}
   TxRef&    getTxRefOfOutput(void) const { return *txPtrOfOutput_; }
   TxRef&    getTxRefOfInput(void) const  { return *txPtrOfInput_;  }
   OutPoint  getOutPoint(void) { return OutPoint(getTxHashOfOutput(),indexOfOutput_);}

   pair<bool,bool> reassessValidity(void);
   bool  isTxOutFromSelf(void)  { return isTxOutFromSelf_; }
   void setTxOutFromSelf(bool isTrue=true) { isTxOutFromSelf_ = isTrue; }
   bool  isFromCoinbase(void) { return isFromCoinbase_; }
   void setFromCoinbase(bool isTrue=true) { isFromCoinbase_ = isTrue; }


   //////////////////////////////////////////////////////////////////////////////
   BinaryData    getTxHashOfInput(void);
   BinaryData    getTxHashOfOutput(void);

   bool setTxIn   (TxRef* txref, uint32_t index);
   bool setTxOut  (TxRef* txref, uint32_t index);
   bool setTxInZC (Tx*    tx,    uint32_t index);
   bool setTxOutZC(Tx*    tx,    uint32_t index);

   //////////////////////////////////////////////////////////////////////////////
   bool isSourceUnknown(void) { return ( !hasTxOut() &&  hasTxIn() ); }
   bool isStandardTxOutScript(void);

   bool isSpent(void);
   bool isUnspent(void);
   bool isSpendable(uint32_t currBlk=0);
   bool isMineButUnconfirmed(uint32_t currBlk);
   void clearZCFields(void);

   void pprintOneLine(void);

private:
   uint64_t  amount_;
   TxRef*    txPtrOfOutput_;
   uint32_t  indexOfOutput_;
   TxRef*    txPtrOfInput_;
   uint32_t  indexOfInput_;

   // Zero-conf data isn't on disk, yet, so can't use TxRef
   Tx *      txOfOutputZC_;
   uint32_t  indexOfOutputZC_;
   Tx *      txOfInputZC_;
   uint32_t  indexOfInputZC_;

   bool      isTxOutFromSelf_;
   bool      isFromCoinbase_;
};


////////////////////////////////////////////////////////////////////////////////
// Just a simple struct for storing spentness info
class SpentByRef
{
public:
   SpentByRef(BinaryData const & ref) { initialize(BinaryRefReader(ref)); }
   SpentByRef(BinaryDataRef const & ref) { initialize(BinaryRefReader(ref)); }
   SpentByRef(BinaryRefReader & brr) { initialize(brr); }
   SpentByRef(BinaryData const & hgtxPlusTxIdx, uint16_t key)
   {
      static uint8_t blkdataprefix = (uint8_t)DB_PREFIX_BLKDATA;
      dbKey_     = BinaryData(&blkdataprefix,1) + hgtxPlusTxIdx;
      txInIndex_ = brr.get_uint16_t();
   }

   void initialize(BinaryRefReader & brr)
   {
      static uint8_t blkdataprefix = (uint8_t)DB_PREFIX_BLKDATA;
      dbKey_     = BinaryData(&blkdataprefix,1) + brr.get_BinaryData(6);
      txInIndex_ = brr.get_uint16_t();
   }

public:
   BinaryData dbKey_;
   uint16_t   txInIndex_;
}


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



////////////////////////////////////////////////////////////////////////////////
// BDM is now tracking "registered" addresses and wallets during each of its
// normal scanning operations.  
class BtcAddress;
class RegisteredAddress
{
public:
   RegisteredAddress(HashString  a160=HashString(0),
                     uint32_t    blkCreated=0) :
         addr160_(a160),
         blkCreated_(blkCreated),
         alreadyScannedUpToBlk_(blkCreated) { }


   RegisteredAddress(BtcAddress const & addrObj, int32_t blkCreated=-1)
   {
      addr160_ = addrObj.getAddrStr20();

      if(blkCreated<0)
         blkCreated = addrObj.getFirstBlockNum();

      blkCreated_            = blkCreated;
      alreadyScannedUpToBlk_ = blkCreated;
   }


   //HashString    addr160_;
   BinaryData    addressID_;
   uint32_t      blkCreated_;
   uint32_t      alreadyScannedUpToBlk_;
   uint64_t      sumValue_;

   bool operator==(RegisteredAddress const & ra2) const 
                                    { return addr160_ == ra2.addr160_;}
   bool operator< (RegisteredAddress const & ra2) const 
                                    { return addr160_ <  ra2.addr160_;}
   bool operator> (RegisteredAddress const & ra2) const 
                                    { return addr160_ >  ra2.addr160_;}

};



////////////////////////////////////////////////////////////////////////////////
// We're going to need to be able to sort our list of registered transactions,
// so I decided to make a new class to support it, with a native operator<().
//
// I debated calling this class "SortableTx"
class RegisteredTx
{
public:
   TxRef *       txrefPtr_;  // Not necessary for sorting, but useful
   BinaryData    txHash_;
   uint32_t      blkNum_;
   uint32_t      txIndex_;


   TxRef *    getTxRefPtr()  { return txrefPtr_; }
   Tx         getTxCopy()    { return txrefPtr_->getTxCopy(); }
   BinaryData getTxHash()    { return txHash_; }
   uint32_t   getBlkNum()    { return blkNum_; }
   uint32_t   getTxIndex()   { return txIndex_; }

   RegisteredTx(void) :
         txrefPtr_(NULL),
         txHash_(""),
         blkNum_(UINT32_MAX),
         txIndex_(UINT32_MAX) { }

   RegisteredTx(BinaryData const & txHash, uint32_t blkNum, uint32_t txIndex) :
         txrefPtr_(NULL),
         txHash_(txHash),
         blkNum_(blkNum),
         txIndex_(txIndex) { }

   RegisteredTx(TxRef* txptr, BinaryData const & txHash, uint32_t blkNum, uint32_t txIndex) :
         txrefPtr_(txptr),
         txHash_(txHash),
         blkNum_(blkNum),
         txIndex_(txIndex) { }

   RegisteredTx(TxRef & txref) :
         txrefPtr_(&txref),
         txHash_(txref.getThisHash()),
         blkNum_(txref.getBlockHeight()),
         txIndex_(txref.getBlockTxIndex()) { }

   RegisteredTx(Tx & tx) :
         txrefPtr_(tx.getTxRefPtr()),
         txHash_(tx.getThisHash()),
         blkNum_(tx.getBlockHeight()),
         txIndex_(tx.getBlockTxIndex()) { }

   bool operator<(RegisteredTx const & rt2) const 
   {
      if( blkNum_ < rt2.blkNum_ )
         return true;
      else if( rt2.blkNum_ < blkNum_ )
         return false;
      else
         return (txIndex_<rt2.txIndex_);
   }


};


#endif

