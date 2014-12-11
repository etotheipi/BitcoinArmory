////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2014, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////


#ifndef _BLOCKOBJ_H_
#define _BLOCKOBJ_H_


#include <iostream>
#include <vector>
#include <map>
#include <set>
#include <cassert>
#include <functional>

#include "BinaryData.h"
#include "BtcUtils.h"



////////////////////////////////////////////////////////////////////////////////
class LMDBBlockDatabase; 
class LMDBBlockDatabase;
class TxRef;
class Tx;
class TxIn;
class TxOut;


class BlockHeader
{
   friend class Blockchain;

public:

   /////////////////////////////////////////////////////////////////////////////
   BlockHeader(void) : 
      isInitialized_(false), 
      isMainBranch_(false), 
      isOrphan_(false),
      isFinishedCalc_(false),
      duplicateID_(UINT8_MAX),
      numTx_(UINT32_MAX), 
      numBlockBytes_(UINT32_MAX)
   { }

   explicit BlockHeader(uint8_t const * ptr, uint32_t size) { unserialize(ptr, size); }
   explicit BlockHeader(BinaryRefReader & brr)    { unserialize(brr); }
   explicit BlockHeader(BinaryDataRef str)        { unserialize(str); }
   explicit BlockHeader(BinaryData const & str)   { unserialize(str); }

   // SWIG needs a non-overloaded method
   BlockHeader & unserialize_1_(BinaryData const & str) { unserialize(str); return *this; }

   uint32_t           getVersion(void) const      { return READ_UINT32_LE(getPtr() );   }
   BinaryData const & getThisHash(void) const     { return thisHash_;                   }
   BinaryData         getPrevHash(void) const     { return BinaryData(getPtr()+4 ,32);  }
   BinaryData const & getNextHash(void) const     { return nextHash_;                   }
   BinaryData         getMerkleRoot(void) const   { return BinaryData(getPtr()+36,32);  }
   BinaryData         getDiffBits(void) const     { return BinaryData(getPtr()+72,4 );  }
   uint32_t           getTimestamp(void) const    { return READ_UINT32_LE(getPtr()+68); }
   uint32_t           getNonce(void) const        { return READ_UINT32_LE(getPtr()+76); }
   uint32_t           getBlockHeight(void) const  { return blockHeight_;                }
   bool               isMainBranch(void) const    { return isMainBranch_;               }
   bool               isOrphan(void) const        { return isOrphan_;                   }
   double             getDifficulty(void) const   { return difficultyDbl_;              }
   double             getDifficultySum(void) const{ return difficultySum_;              }

   /////////////////////////////////////////////////////////////////////////////
   BinaryDataRef  getThisHashRef(void) const   { return thisHash_.getRef();            }
   BinaryDataRef  getPrevHashRef(void) const   { return BinaryDataRef(getPtr()+4, 32); }
   BinaryDataRef  getNextHashRef(void) const   { return nextHash_.getRef();            }
   BinaryDataRef  getMerkleRootRef(void) const { return BinaryDataRef(getPtr()+36,32); }
   BinaryDataRef  getDiffBitsRef(void) const   { return BinaryDataRef(getPtr()+72,4 ); }
   uint32_t       getNumTx(void) const         { return numTx_; }

   const string&  getFileName(void) const { return blkFile_; }
   uint64_t       getOffset(void) const { return blkFileOffset_; }
   uint32_t       getBlockFileNum(void) const { return blkFileNum_; }
   /////////////////////////////////////////////////////////////////////////////
   uint8_t const * getPtr(void) const  {
      assert(isInitialized_);
      return dataCopy_.getPtr();
   }
   size_t        getSize(void) const {
      assert(isInitialized_);
      return dataCopy_.getSize();
   }
   bool            isInitialized(void) const { return isInitialized_; }
   uint32_t        getBlockSize(void) const { return numBlockBytes_; }
   void            setBlockSize(uint32_t sz) { numBlockBytes_ = sz; }
   void            setNumTx(uint32_t ntx) { numTx_ = ntx; }

   /////////////////////////////////////////////////////////////////////////////
   void           setBlockFile(string filename)     {blkFile_       = filename;}
   void           setBlockFileNum(uint32_t fnum)    {blkFileNum_    = fnum;}
   void           setBlockFileOffset(uint64_t offs) {blkFileOffset_ = offs;}

   /////////////////////////////////////////////////////////////////////////////
   void          pprint(ostream & os=cout, int nIndent=0, bool pBigendian=true) const;
   void          pprintAlot(ostream & os=cout);

   /////////////////////////////////////////////////////////////////////////////
   const BinaryData& serialize(void) const   { return dataCopy_; }

   bool hasFilePos(void) const { return blkFileNum_ != UINT32_MAX; }

   /////////////////////////////////////////////////////////////////////////////
   // Just in case we ever want to calculate a difficulty-1 header via CPU...
   int64_t findNonce(const char* inDiffStr);

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr, uint32_t size);
   void unserialize(BinaryData const & str) { unserialize(str.getRef()); }
   void unserialize(BinaryDataRef const & str);
   void unserialize(BinaryRefReader & brr);

   void unserialize_swigsafe_(BinaryData const & rawHead) { unserialize(rawHead); }

   uint8_t getDuplicateID(void) const { return duplicateID_; }
   void    setDuplicateID(uint8_t d)  { duplicateID_ = d; }

   void clearDataCopy() {dataCopy_.resize(0);}

private:
   BinaryData     dataCopy_;
   bool           isInitialized_:1;
   bool           isMainBranch_:1;
   bool           isOrphan_:1;
   bool           isFinishedCalc_:1;
   // Specific to the DB storage
   uint8_t        duplicateID_; // ID of this blk rel to others at same height
   uint32_t       blockHeight_;
   
   uint32_t       numTx_;
   uint32_t       numBlockBytes_; // includes header + nTx + sum(Tx)
   
   // Derived properties - we expect these to be set after construct/copy
   BinaryData     thisHash_;
   double         difficultyDbl_;

   // Need to compute these later
   BinaryData     nextHash_;
   double         difficultySum_;

   string         blkFile_;
   uint32_t       blkFileNum_ = UINT32_MAX;
   uint64_t       blkFileOffset_;


};



////////////////////////////////////////////////////////////////////////////////
class DBTxRef;

class TxRef
{
   friend class BlockDataManager_LevelDB;
   friend class Tx;

public:
   /////////////////////////////////////////////////////////////////////////////
   TxRef() { }
   TxRef(BinaryDataRef bdr) { setRef(bdr); }

   /////////////////////////////////////////////////////////////////////////////
   void setRef(BinaryDataRef bdr);

   DBTxRef attached(const LMDBBlockDatabase* db) const;
      
   /////////////////////////////////////////////////////////////////////////////
   bool           isInitialized(void)  const {return dbKey6B_.getSize()>0;}
   bool           isNull(void) const { return !isInitialized();}

   /////////////////////////////////////////////////////////////////////////////
   BinaryData     getDBKey(void) const   { return dbKey6B_;}
   BinaryDataRef  getDBKeyRef(void)      { return dbKey6B_.getRef();}
   void           setDBKey(BinaryData    const & bd) {dbKey6B_.copyFrom(bd);}
   void           setDBKey(BinaryDataRef const & bd) {dbKey6B_.copyFrom(bd);}


   /////////////////////////////////////////////////////////////////////////////
   BinaryData     getDBKeyOfChild(uint16_t i) const
      {return dbKey6B_+WRITE_UINT16_BE(i);}

   uint16_t           getBlockTxIndex(void) const;
   uint32_t           getBlockHeight(void) const;
   uint8_t            getDuplicateID(void) const;

   /////////////////////////////////////////////////////////////////////////////
   void               pprint(ostream & os=cout, int nIndent=0) const;

   /////////////////////////////////////////////////////////////////////////////
   bool operator==(BinaryData const & dbkey) const { return dbKey6B_ == dbkey; }
   bool operator==(TxRef const & txr) const  { return dbKey6B_ == txr.dbKey6B_;}

   bool operator>=(const BinaryData& dbkey) const { return dbKey6B_ >= dbkey; }
protected:
   //FileDataPtr        blkFilePtr_;
   //BlockHeader*       headerPtr_;

   // Both filePtr and headerPtr can be replaced by a single dbKey
   // It is 6 bytes:  [ HeaderHgt(3) || DupID(1) || TxIndex(2) ]
   // It tells us exactly how to get this Tx from DB, and by the way
   // the DB is structured, the first four bytes also tells us how 
   // to get the associated header.  
   BinaryData           dbKey6B_;  

   // TxRefs are associated with a particular interface (at this time, there
   // will only be one interface).
};

class DBTxRef : public TxRef
{
public:
   DBTxRef()
   { }
   DBTxRef( const TxRef &txref, const LMDBBlockDatabase* db)
      : TxRef(txref), db_(db)
   { }
   
   BinaryData serialize() const; 
   
   BinaryData getBlockHash() const;
   uint32_t getBlockTimestamp() const;
   BinaryData getThisHash() const;
   Tx getTxCopy() const;
   bool isMainBranch()  const;
   
   /////////////////////////////////////////////////////////////////////////////
   // This as fast as you can get a single TxIn or TxOut from the DB.  But if 
   // need multiple of them from the same Tx, you should getTxCopy() and then
   // iterate over them in the Tx object
   TxIn  getTxInCopy(uint32_t i); 
   TxOut getTxOutCopy(uint32_t i);

private:
   const LMDBBlockDatabase*  db_;  
};


inline DBTxRef TxRef::attached(const LMDBBlockDatabase* db) const
{
   return DBTxRef(*this, db);
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// OutPoint is just a reference to a TxOut
class OutPoint
{
   friend class BlockDataManager_LevelDB;
   friend class OutPointRef;

public:
   OutPoint(void) : txHash_(32), txOutIndex_(UINT32_MAX) { }

   explicit OutPoint(uint8_t const * ptr, uint32_t remaining) { unserialize(ptr, remaining); }
   explicit OutPoint(BinaryData const & txHash, uint32_t txOutIndex) : 
                txHash_(txHash), txOutIndex_(txOutIndex) { }

   BinaryData const &   getTxHash(void)     const { return txHash_; }
   BinaryDataRef        getTxHashRef(void)  const { return BinaryDataRef(txHash_); }
   uint32_t             getTxOutIndex(void) const { return txOutIndex_; }
   bool                 isCoinbase(void) const { return txHash_ == BtcUtils::EmptyHash_; }

   void setTxHash(BinaryData const & hash) { txHash_.copyFrom(hash); }
   void setTxOutIndex(uint32_t idx) { txOutIndex_ = idx; }

   // Define these operators so that we can use OutPoint as a map<> key
   bool operator<(OutPoint const & op2) const;
   bool operator==(OutPoint const & op2) const;

   void        serialize(BinaryWriter & bw) const;
   BinaryData  serialize(void) const;
   void        unserialize(uint8_t const * ptr, uint32_t remaining);
   void        unserialize(BinaryReader & br);
   void        unserialize(BinaryRefReader & brr);
   void        unserialize(BinaryData const & bd);
   void        unserialize(BinaryDataRef const & bdRef);

   void unserialize_swigsafe_(BinaryData const & rawOP) { unserialize(rawOP); }
   const BinaryDataRef getDBkey(LMDBBlockDatabase* db=nullptr) const;

private:
   BinaryData txHash_;
   uint32_t   txOutIndex_;

   //this member isn't set by ctor, but processed after the first call to
   //get DBKey
   mutable BinaryData DBkey_;
};



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxIn
{
   friend class BlockDataManager_LevelDB;

public:
   TxIn(void) : dataCopy_(0), parentHash_(0), parentHeight_(UINT32_MAX),
                scriptType_(TXIN_SCRIPT_NONSTANDARD), scriptOffset_(0) {}

   // Ptr to the beginning of the TxIn, last two arguments are supplemental
   /*TxIn(uint8_t const * ptr,  
        uint32_t size,
        uint32_t        nBytes=0, 
        TxRef           parent=TxRef(), 
        uint32_t        idx=UINT32_MAX) { unserialize_checked(ptr, size, nBytes, parent, idx); } 
*/
   uint8_t const *  getPtr(void) const { assert(isInitialized()); return dataCopy_.getPtr(); }
   size_t           getSize(void) const { assert(isInitialized()); return dataCopy_.getSize(); }
   bool             isStandard(void) const { return scriptType_!=TXIN_SCRIPT_NONSTANDARD; }
   bool             isCoinbase(void) const { return (scriptType_ == TXIN_SCRIPT_COINBASE); }
   bool             isInitialized(void) const {return dataCopy_.getSize() > 0; }
   OutPoint         getOutPoint(void) const;

   // Script ops
   BinaryData       getScript(void) const;
   BinaryDataRef    getScriptRef(void) const;
   size_t           getScriptSize(void) { return getSize() - (scriptOffset_ + 4); }
   TXIN_SCRIPT_TYPE getScriptType(void) const { return scriptType_; }
   uint32_t         getScriptOffset(void) const { return scriptOffset_; }

   // SWIG doesn't handle these enums well, so we will provide some direct bools
   bool             isScriptStandard() const   { return scriptType_ != TXIN_SCRIPT_NONSTANDARD;}
   bool             isScriptStdUncompr() const { return scriptType_ == TXIN_SCRIPT_STDUNCOMPR;}
   bool             isScriptStdCompr() const  { return scriptType_ == TXIN_SCRIPT_STDCOMPR;}
   bool             isScriptCoinbase() const   { return scriptType_ == TXIN_SCRIPT_COINBASE;}
   bool             isScriptSpendMulti() const { return scriptType_ == TXIN_SCRIPT_SPENDMULTI; }
   bool             isScriptSpendPubKey() const { return scriptType_ == TXIN_SCRIPT_SPENDPUBKEY; }
   bool             isScriptSpendP2SH() const  { return scriptType_ == TXIN_SCRIPT_SPENDP2SH; }
   bool             isScriptNonStd() const    { return scriptType_ == TXIN_SCRIPT_NONSTANDARD; }

   TxRef            getParentTxRef() const { return parentTx_; }
   uint32_t         getIndex(void) const { return index_; }

   //void setParentTx(TxRef txref, int32_t idx=-1) {parentTx_=txref; index_=idx;}

   uint32_t         getSequence() const  { return READ_UINT32_LE(getPtr()+getSize()-4); }

   BinaryData       getParentHash(LMDBBlockDatabase *db);
   uint32_t         getParentHeight() const;

   void             setParentHash(BinaryData const & txhash) {parentHash_ = txhash;}
   void             setParentHeight(uint32_t blkheight) {parentHeight_ = blkheight;}

   /////////////////////////////////////////////////////////////////////////////
   const BinaryData&  serialize(void) const { return dataCopy_; }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize_checked( uint8_t const * ptr,
                     uint32_t        size,
                     uint32_t        nbytes=0, 
                     TxRef           parent=TxRef(), 
                     uint32_t        idx=UINT32_MAX);

   void unserialize( BinaryData const & str,
                     uint32_t       nbytes=0,
                     TxRef          parent=TxRef(), 
                     uint32_t       idx=UINT32_MAX);

   void unserialize( BinaryDataRef  str, 
                     uint32_t       nbytes=0, 
                     TxRef          parent=TxRef(), 
                     uint32_t       idx=UINT32_MAX);

   void unserialize( BinaryRefReader & brr, 
                     uint32_t       nbytes=0, 
                     TxRef          parent=TxRef(), 
                     uint32_t       idx=UINT32_MAX);

   void unserialize_swigsafe_(BinaryData const & rawIn) { unserialize(rawIn); }

   /////////////////////////////////////////////////////////////////////////////
   // Not all TxIns have sendor info.  Might have to go to the Outpoint and get
   // the corresponding TxOut to find the sender.  In the case the sender is
   // not available, return false and don't write the output
   bool       getSenderScrAddrIfAvail(BinaryData & addrTarget) const;
   BinaryData getSenderScrAddrIfAvail(void) const;

   void pprint(ostream & os=cout, int nIndent=0, bool pBigendian=true) const;


private:
   BinaryData       dataCopy_;
   BinaryData       parentHash_;
   uint32_t         parentHeight_;

   // Derived properties - we expect these to be set after construct/copy
   uint32_t         index_;
   TXIN_SCRIPT_TYPE scriptType_;
   uint32_t         scriptOffset_;
   TxRef            parentTx_;


};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxOut
{
   friend class BlockDataManager_LevelDB;

public:

   /////////////////////////////////////////////////////////////////////////////
   TxOut(void) : dataCopy_(0), parentHash_(0) {}
   /*
   TxOut(uint8_t const * ptr, 
         uint32_t        nBytes=0, 
         TxRef           parent=TxRef(), 
         uint32_t        idx=UINT32_MAX) { unserialize(ptr, nBytes, parent, idx); } */

   uint8_t const * getPtr(void) const { return dataCopy_.getPtr(); }
   uint32_t        getSize(void) const { return (uint32_t)dataCopy_.getSize(); }
   uint64_t        getValue(void) const { return READ_UINT64_LE(dataCopy_.getPtr()); }
   bool            isStandard(void) const { return scriptType_ != TXOUT_SCRIPT_NONSTANDARD; }
   bool            isInitialized(void) const {return dataCopy_.getSize() > 0; }
   TxRef           getParentTxRef() const { return parentTx_; }
   uint32_t        getIndex(void) { return index_; }

   //void setParentTx(TxRef txref, uint32_t idx=-1) { parentTx_=txref; index_=idx;}


   /////////////////////////////////////////////////////////////////////////////
   BinaryData const & getScrAddressStr(void) const { return uniqueScrAddr_; }
   BinaryDataRef      getScrAddressRef(void) const { return uniqueScrAddr_.getRef(); }
   //BinaryData const & getRecipientAddr(void) const    { return recipientBinAddr20_; }
   //BinaryDataRef      getRecipientAddrRef(void) const { return recipientBinAddr20_.getRef(); }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData         getScript(void);
   BinaryDataRef      getScriptRef(void);
   TXOUT_SCRIPT_TYPE  getScriptType(void) const { return scriptType_; }
   uint32_t           getScriptSize(void) const { return getSize() - scriptOffset_; }

   // SWIG doesn't handle these enums well, so we will provide some direct bools
   bool isScriptStandard(void)    { return scriptType_ != TXOUT_SCRIPT_NONSTANDARD;}
   bool isScriptStdHash160(void)  { return scriptType_ == TXOUT_SCRIPT_STDHASH160;}
   bool isScriptStdPubKey65(void) { return scriptType_ == TXOUT_SCRIPT_STDPUBKEY65;}
   bool isScriptStdPubKey33(void) { return scriptType_ == TXOUT_SCRIPT_STDPUBKEY33; }
   bool isScriptP2SH(void)        { return scriptType_ == TXOUT_SCRIPT_P2SH; }
   bool isScriptNonStd(void)      { return scriptType_ == TXOUT_SCRIPT_NONSTANDARD; }


   /////////////////////////////////////////////////////////////////////////////
   BinaryData         serialize(void) { return BinaryData(dataCopy_); }
   BinaryDataRef      serializeRef(void) { return dataCopy_; }

   BinaryData         getParentHash(LMDBBlockDatabase *db);
   uint32_t           getParentHeight() const;

   void               setParentHash(BinaryData const & txhash) {parentHash_ = txhash;}
   void               setParentHeight(uint32_t blkheight) {parentHeight_ = blkheight;}

   /////////////////////////////////////////////////////////////////////////////
   void unserialize_checked( uint8_t const *   ptr, 
                     uint32_t          size,
                     uint32_t          nbytes=0, 
                     TxRef             parent=TxRef(), 
                     uint32_t          idx=UINT32_MAX);

   void unserialize( BinaryData const & str, 
                     uint32_t           nbytes=0, 
                     TxRef              parent=TxRef(), 
                     uint32_t           idx=UINT32_MAX);

   void unserialize( BinaryDataRef const & str, 
                     uint32_t          nbytes=0, 
                     TxRef             parent=TxRef(), 
                     uint32_t          idx=UINT32_MAX);
   void unserialize( BinaryRefReader & brr, 
                     uint32_t          nbytes=0, 
                     TxRef             parent=TxRef(), 
                     uint32_t          idx=UINT32_MAX);

   void unserialize_swigsafe_(BinaryData const & rawOut) { unserialize(rawOut); }

   void  pprint(ostream & os=cout, int nIndent=0, bool pBigendian=true);

private:
   BinaryData        dataCopy_;
   BinaryData        parentHash_;
   uint32_t          parentHeight_;

   // Derived properties - we expect these to be set after construct/copy
   //BinaryData        recipientBinAddr20_;
   BinaryData        uniqueScrAddr_;
   TXOUT_SCRIPT_TYPE scriptType_;
   uint32_t          scriptOffset_;
   uint32_t          index_;
   TxRef             parentTx_;
};




////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class Tx
{
   friend class BtcWallet;
   friend class BlockDataManager_LevelDB;

public:
   Tx(void) : isInitialized_(false), offsetsTxIn_(0), offsetsTxOut_(0) {}
   explicit Tx(uint8_t const * ptr, uint32_t size) { unserialize(ptr, size); }
   explicit Tx(BinaryRefReader & brr)     { unserialize(brr);       }
   explicit Tx(BinaryData const & str)    { unserialize(str);       }
   explicit Tx(BinaryDataRef const & str) { unserialize(str);       }
     
   uint8_t const *    getPtr(void)  const { return dataCopy_.getPtr();  }
   size_t             getSize(void) const { return dataCopy_.getSize(); }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t           getVersion(void)   const { return READ_UINT32_LE(dataCopy_.getPtr());}
   size_t             getNumTxIn(void)   const { return offsetsTxIn_.size()-1;}
   size_t             getNumTxOut(void)  const { return offsetsTxOut_.size()-1;}
   BinaryData         getThisHash(void)  const;
   //bool               isMainBranch(void) const;
   bool               isInitialized(void) const { return isInitialized_; }

   /////////////////////////////////////////////////////////////////////////////
   size_t             getTxInOffset(uint32_t i) const  { return offsetsTxIn_[i]; }
   size_t             getTxOutOffset(uint32_t i) const { return offsetsTxOut_[i]; }

   /////////////////////////////////////////////////////////////////////////////
   static Tx          createFromStr(BinaryData const & bd) {return Tx(bd);}

   /////////////////////////////////////////////////////////////////////////////
   bool               hasTxRef(void) const { return txRefObj_.isInitialized(); }
   TxRef              getTxRef(void) const { return txRefObj_; }
   void               setTxRef(TxRef ref) { txRefObj_ = ref; }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData         serialize(void) const    { return dataCopy_; }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr, size_t size);
   void unserialize(BinaryData const & str) { unserialize(str.getPtr(), str.getSize()); }
   void unserialize(BinaryDataRef const & str) { unserialize(str.getPtr(), str.getSize()); }
   void unserialize(BinaryRefReader & brr);
   //void unserialize_no_txout(BinaryRefReader & brr);
   void unserialize_swigsafe_(BinaryData const & rawTx) { unserialize(rawTx); }


   /////////////////////////////////////////////////////////////////////////////
   uint32_t    getLockTime(void) const { return lockTime_; }
   uint64_t    getSumOfOutputs(void);


   BinaryData getScrAddrForTxOut(uint32_t txOutIndex);

   /////////////////////////////////////////////////////////////////////////////
   // These are not pointers to persistent object, these methods actually 
   // CREATES the TxIn/TxOut.  But the construction is fast, so it's
   // okay to do it on the fly
   TxIn     getTxInCopy(int i) const;
   TxOut    getTxOutCopy(int i) const;


   /////////////////////////////////////////////////////////////////////////////
   // All these methods return UINTX_MAX if txRefObj.isNull()
   // BinaryData getBlockHash(void)      { return txRefObj_.getBlockHash();      }
   // uint32_t   getBlockTimestamp(void) { return txRefObj_.getBlockTimestamp(); }
   uint32_t   getBlockHeight(void)    { return txRefObj_.getBlockHeight();    }
   uint8_t    getDuplicateID(void)    { return txRefObj_.getDuplicateID();    }
   uint16_t   getBlockTxIndex(void)   { return txRefObj_.getBlockTxIndex();   }

   /////////////////////////////////////////////////////////////////////////////
   void pprint(ostream & os=cout, int nIndent=0, bool pBigendian=true);
   void pprintAlot(ostream & os=cout);

   bool operator==(const Tx& rhs) const
   {
      if (this->isInitialized() && rhs.isInitialized())
         return this->thisHash_ == rhs.thisHash_;
      return false;
   }

   void setTxTime(uint32_t txtime) { txTime_ = txtime; }
   uint32_t getTxTime(void) const { return txTime_; }

private:
   // Full copy of the serialized tx
   BinaryData    dataCopy_;
   bool          isInitialized_;

   uint32_t      version_;
   uint32_t      lockTime_;
   
   // Derived properties - we expect these to be set after construct/copy
   BinaryData    thisHash_;

   // Will always create TxIns and TxOuts on-the-fly; only store the offsets
   vector<size_t> offsetsTxIn_;
   vector<size_t> offsetsTxOut_;

   // To be calculated later
   //BlockHeader*  headerPtr_;
   TxRef         txRefObj_;

   uint32_t      txTime_;
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
   explicit TxIOPair(uint64_t amount);
   explicit TxIOPair(TxRef txRefO, uint32_t txoutIndex);
   explicit TxIOPair(const BinaryData& txOutKey8B, uint64_t value);
   explicit TxIOPair(TxRef txRefO, uint32_t txoutIndex,
      TxRef txRefI, uint32_t txinIndex);

   TxIOPair(const TxIOPair& txio) 
   {
      *this = txio;
      getScrAddr_ = [](void)->const BinaryData&{ return BinaryData::EmptyBinData_; };
   }

   // Lots of accessors
   bool      hasTxOut(void) const   { return (txRefOfOutput_.isInitialized()); }
   bool      hasTxIn(void) const    { return (txRefOfInput_.isInitialized()); }
   bool      hasTxOutInMain(LMDBBlockDatabase *db) const;
   bool      hasTxInInMain(LMDBBlockDatabase *db) const;
   bool      hasTxOutZC(void) const;
   bool      hasTxInZC(void) const;
   bool      hasValue(void) const   { return (amount_ != 0); }
   uint64_t  getValue(void) const   { return  amount_; }
   void      setValue(const uint64_t& newVal) { amount_ = newVal; }

   //////////////////////////////////////////////////////////////////////////////
   TxRef     getTxRefOfOutput(void) const { return txRefOfOutput_; }
   TxRef     getTxRefOfInput(void) const  { return txRefOfInput_; }
   uint32_t  getIndexOfOutput(void) const { return indexOfOutput_; }
   uint32_t  getIndexOfInput(void) const  { return indexOfInput_; }
   OutPoint  getOutPoint(LMDBBlockDatabase *db) const { return OutPoint(getTxHashOfOutput(db), indexOfOutput_); }

   pair<bool, bool> reassessValidity(LMDBBlockDatabase *db);
   bool  isTxOutFromSelf(void) const  { return isTxOutFromSelf_; }
   void setTxOutFromSelf(bool isTrue = true) { isTxOutFromSelf_ = isTrue; }
   bool  isFromCoinbase(void) const { return isFromCoinbase_; }
   void setFromCoinbase(bool isTrue = true) { isFromCoinbase_ = isTrue; }
   bool  isMultisig(void) const { return isMultisig_; }
   void setMultisig(bool isTrue = true) { isMultisig_ = isTrue; }

   BinaryData getDBKeyOfOutput(void) const
   {
      return txRefOfOutput_.getDBKeyOfChild(indexOfOutput_);
   }
   BinaryData getDBKeyOfInput(void) const
   {
      return txRefOfInput_.getDBKeyOfChild(indexOfInput_);
   }

   //////////////////////////////////////////////////////////////////////////////
   BinaryData    getTxHashOfInput(const LMDBBlockDatabase *db = nullptr) const;
   BinaryData    getTxHashOfOutput(const LMDBBlockDatabase *db = nullptr) const;

   void setTxHashOfInput(const BinaryData& txHash)
   {
      txHashOfInput_ = txHash;
   }
   void setTxHashOfOutput(const BinaryData& txHash)
   {
      txHashOfOutput_ = txHash;
   }

   TxOut getTxOutCopy(LMDBBlockDatabase *db) const;
   TxIn  getTxInCopy(LMDBBlockDatabase *db) const;

   bool setTxIn(TxRef  txref, uint32_t index);
   bool setTxIn(const BinaryData& dbKey8B);
   bool setTxOut(TxRef  txref, uint32_t index);
   bool setTxOut(const BinaryData& dbKey8B);

   //////////////////////////////////////////////////////////////////////////////
   bool isSourceUnknown(void) { return (!hasTxOut() && hasTxIn()); }

   bool isSpent(LMDBBlockDatabase *db) const;
   bool isUnspent(LMDBBlockDatabase *db) const;
   bool isSpendable(
      LMDBBlockDatabase *db,
      uint32_t currBlk = 0, bool ignoreAllZeroConf = false
      ) const;
   bool isMineButUnconfirmed(
      LMDBBlockDatabase *db,
      uint32_t currBlk, bool includeAllZeroConf = false
      ) const;
   void pprintOneLine(LMDBBlockDatabase *db) const;

   bool operator<(TxIOPair const & t2)
   {
      return (getDBKeyOfOutput() < t2.getDBKeyOfOutput());
   }
   bool operator==(TxIOPair const & t2)
   {
      return (getDBKeyOfOutput() == t2.getDBKeyOfOutput());
   }
   bool operator>=(const BinaryData &) const;
   TxIOPair& operator=(const TxIOPair &);
   TxIOPair& operator=(TxIOPair&& toMove);

   void setTxTime(uint32_t t) { txtime_ = t; }
   uint32_t getTxTime(void) const { return txtime_; }

   bool isUTXO(void) const { return isUTXO_; }
   void setUTXO(bool val) { isUTXO_ = val; }

   void setScrAddrLambda(function < const BinaryData&(void) > func)
   { getScrAddr_ = func; }

   const BinaryData& getScrAddr(void) const
   { return getScrAddr_(); }

public:
   bool flagged = false;
   
private:
   uint64_t  amount_;

   TxRef     txRefOfOutput_;
   uint32_t  indexOfOutput_;
   TxRef     txRefOfInput_;
   uint32_t  indexOfInput_;

   mutable BinaryData txHashOfOutput_;
   mutable BinaryData txHashOfInput_;

   // Zero-conf data isn't on disk, yet, so can't use TxRef
   bool      isTxOutFromSelf_ = false;
   bool      isFromCoinbase_;
   bool      isMultisig_;

   //mainly for ZC ledgers. Could replace the need for a blockchain 
   //object to build scrAddrObj ledgers.
   uint32_t txtime_;

   /***marks txio as spent for serialize/deserialize operations. It signifies
   whether a subSSH entry with only a TxOut DBkey is spent.

   To allow for partial parsing of SSH history, all txouts need to be visible at
   the height they appeared, amd spent txouts need to be visible at the
   spending txin's height as well.

   While spent txouts at txin height are unique, spent txouts at txout height
   need to be differenciated from UTXOs.
   ***/
   bool isUTXO_ = false; 

   //used to get a relevant scrAddr from a txio
   function<const BinaryData& (void)> getScrAddr_;
};

////////////////////////////////////////////////////////////////////////////////
// Just a simple struct for storing spentness info
/*
class SpentByRef
{
public:
   SpentByRef(BinaryData const & ref) 
   { 
      BinaryRefReader brr(ref);
      initialize(brr); 
   }

   SpentByRef(BinaryDataRef const & ref) 
   {
      BinaryRefReader brr(ref);
      initialize(brr); 
   }

   SpentByRef(BinaryRefReader & brr) { initialize(brr); }

   SpentByRef(BinaryData const & hgtxPlusTxIdx, uint16_t key)
   {
      //static uint8_t blkdataprefix = (uint8_t)DB_PREFIX_BLKDATA;
      //dbKey_     = BinaryData(&blkdataprefix,1) + hgtxPlusTxIdx;
      //txInIndex_ = brr.get_uint16_t();
   }

   void initialize(BinaryRefReader & brr)
   {
      //static uint8_t blkdataprefix = (uint8_t)DB_PREFIX_BLKDATA;
      //dbKey_     = BinaryData(&blkdataprefix,1) + brr.get_BinaryData(6);
      //txInIndex_ = brr.get_uint16_t();
   }

public:
   BinaryData dbKey_;
   uint16_t   txInIndex_;
};
*/


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// This class is mainly for sorting by priority
class UnspentTxOut
{
public:
   UnspentTxOut(void);
   UnspentTxOut(LMDBBlockDatabase *db, TxOut & txout, uint32_t blknum) 
      { init(db, txout, blknum);}


   UnspentTxOut(BinaryData const & hash, uint32_t outIndex, uint32_t height, 
                uint64_t val, BinaryData const & script) :
      txHash_(hash), txOutIndex_(outIndex), txHeight_(height),
      value_(val), script_(script) {}

   void init(LMDBBlockDatabase *db, TxOut & txout, uint32_t blknum, bool isMultiRef=false);

   BinaryData   getTxHash(void) const      { return txHash_;     }
   uint32_t     getTxOutIndex(void) const  { return txOutIndex_; }
   uint64_t     getValue(void)  const      { return value_;      }
   uint64_t     getTxHeight(void)  const   { return txHeight_;   }
   uint32_t     getNumConfirm(void) const  { return numConfirm_; }
   uint32_t     isMultisigRef(void) const  { return isMultisigRef_; }

   OutPoint getOutPoint(void) const { return OutPoint(txHash_, txOutIndex_); }

   BinaryData const & getScript(void) const      { return script_;     }
   BinaryData   getRecipientScrAddr(void) const;

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
   bool       isMultisigRef_;

   // This can be set and used as part of a compare function:  if you want
   // each TxOut prioritization to be dependent on the target Tx amount.
   uint64_t   targetTxAmount_;
};



////////////////////////////////////////////////////////////////////////////////
// BDM is now tracking "registered" addresses and wallets during each of its
// normal scanning operations.  
class RegisteredScrAddr
{
public:
   RegisteredScrAddr(HashString  a160=HashString(0),
                     uint32_t    blkCreated=0) :
         uniqueKey_(a160),
         blkCreated_(blkCreated),
         alreadyScannedUpToBlk_(blkCreated) { }


   //RegisteredScrAddr(BtcAddress const & addrObj, int32_t blkCreated=-1);


   bool operator==(RegisteredScrAddr const & ra2) const 
                                    { return uniqueKey_ == ra2.uniqueKey_;}
   bool operator< (RegisteredScrAddr const & ra2) const 
                                    { return uniqueKey_ <  ra2.uniqueKey_;}
   bool operator> (RegisteredScrAddr const & ra2) const 
                                    { return uniqueKey_ >  ra2.uniqueKey_;}

   
   BinaryData        uniqueKey_;
   uint32_t          blkCreated_;
   uint32_t          alreadyScannedUpToBlk_;
};


////////////////////////////////////////////////////////////////////////////////
// We're going to need to be able to sort our list of registered transactions,
// so I decided to make a new class to support it, with a native operator<().
//
// I debated calling this class "SortableTx"
class RegisteredTx
{
public:
   TxRef         txRefObj_;  // Not necessary for sorting, but useful
   BinaryData    txHash_;
   uint32_t      blkNum_;
   uint16_t      txIndex_;


   TxRef      getTxRef()     { return txRefObj_; }
   Tx         getTxCopy(LMDBBlockDatabase *db)
      { return txRefObj_.attached(db).getTxCopy(); }
   BinaryData getTxHash()    { return txHash_; }
   uint32_t   getBlkNum()    { return blkNum_; }
   uint16_t   getTxIndex()   { return txIndex_; }

   RegisteredTx(void) :
         txHash_(""),
         blkNum_(UINT32_MAX),
         txIndex_(UINT16_MAX) { }

   RegisteredTx( BinaryData const & txHash,
                 uint32_t blkNum,
                 uint16_t txIndex) :
         txHash_(txHash),
         blkNum_(blkNum),
         txIndex_(txIndex) { }

   explicit RegisteredTx(Tx & tx) :
         txRefObj_(tx.getTxRef()),
         txHash_(tx.getThisHash()),
         blkNum_(tx.getBlockHeight()),
         txIndex_(tx.getBlockTxIndex()) { }

   RegisteredTx( const TxRef& txref, 
                 BinaryData const & txHash,
                 uint32_t blkNum,
                 uint16_t txIndex) :
         txRefObj_(txref),
         txHash_(txHash),
         blkNum_(blkNum),
         txIndex_(txIndex)
   { }

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

// kate: indent-width 3; replace-tabs on;
#endif

