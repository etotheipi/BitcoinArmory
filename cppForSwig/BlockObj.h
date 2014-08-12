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

#include "BinaryData.h"
#include "BtcUtils.h"



////////////////////////////////////////////////////////////////////////////////
class InterfaceToLDB;  
class GlobalDBUtilities;  
class TxRef;
class Tx;
class TxIn;
class TxOut;



class BlockHeader
{
   friend class BlockDataManager_LevelDB;
   friend class InterfaceToLDB;

public:

   /////////////////////////////////////////////////////////////////////////////
   BlockHeader(void) : 
      isInitialized_(false), 
      numTx_(UINT32_MAX), 
      numBlockBytes_(UINT32_MAX),
      duplicateID_(UINT8_MAX) {}

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

   /////////////////////////////////////////////////////////////////////////////
   uint8_t const * getPtr(void) const  {
      assert(isInitialized_);
      return dataCopy_.getPtr();
   }
   uint32_t        getSize(void) const {
      assert(isInitialized_);
      return dataCopy_.getSize();
   }
   uint32_t        isInitialized(void) const { return isInitialized_; }
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
   BinaryData    serialize(void)    { return dataCopy_; }

   /////////////////////////////////////////////////////////////////////////////
   // Just in case we ever want to calculate a difficulty-1 header via CPU...
   uint32_t      findNonce(void);

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
   bool           isInitialized_;

   // Derived properties - we expect these to be set after construct/copy
   BinaryData     thisHash_;
   double         difficultyDbl_;

   // Need to compute these later
   BinaryData     nextHash_;
   uint32_t       blockHeight_;
   double         difficultySum_;
   bool           isMainBranch_;
   bool           isOrphan_;
   bool           isFinishedCalc_;
   uint32_t       numTx_;
   uint32_t       numBlockBytes_; // includes header + nTx + sum(Tx)

   string         blkFile_;
   uint32_t       blkFileNum_;
   uint64_t       blkFileOffset_;

   // Specific to the DB storage
   uint8_t        duplicateID_; // ID of this blk rel to others at same height

};



////////////////////////////////////////////////////////////////////////////////

class TxRef
{
   friend class BlockDataManager_LevelDB;
   friend class Tx;

public:
   /////////////////////////////////////////////////////////////////////////////
   TxRef(void) { setRef(); }
   TxRef(BinaryDataRef bdr) { setRef(bdr); }
   TxRef(BinaryDataRef bdr, InterfaceToLDB* ifc) { setRef(bdr, ifc); }

   /////////////////////////////////////////////////////////////////////////////
   void setRef(BinaryDataRef bdr=BinaryDataRef(), InterfaceToLDB* iface=NULL);
     
   /////////////////////////////////////////////////////////////////////////////
   BinaryData     getThisHash(void) const;
   Tx             getTxCopy(void) const;
   bool           isMainBranch(void)  const;
   bool           isInitialized(void)  const {return dbKey6B_.getSize()>0;}
   bool           isBound(void)  const {return dbIface_!=NULL;}

   /////////////////////////////////////////////////////////////////////////////
   BinaryData     getDBKey(void) const   { return dbKey6B_;}
   BinaryDataRef  getDBKeyRef(void)      { return dbKey6B_.getRef();}
   void           setDBKey(BinaryData    const & bd) {dbKey6B_.copyFrom(bd);}
   void           setDBKey(BinaryDataRef const & bd) {dbKey6B_.copyFrom(bd);}

   bool           isNull(void) const { return !isInitialized();}

   /////////////////////////////////////////////////////////////////////////////
   BinaryData     getDBKeyOfChild(uint16_t i) const
                                          {return dbKey6B_+WRITE_UINT16_BE(i);}

   /////////////////////////////////////////////////////////////////////////////
   // This as fast as you can get a single TxIn or TxOut from the DB.  But if 
   // need multiple of them from the same Tx, you should getTxCopy() and then
   // iterate over them in the Tx object
   TxIn  getTxInCopy(uint32_t i); 
   TxOut getTxOutCopy(uint32_t i);

   /////////////////////////////////////////////////////////////////////////////
   BinaryData         serialize(void) const; 

   /////////////////////////////////////////////////////////////////////////////
   BinaryData         getBlockHash(void) const;
   uint32_t           getBlockTimestamp(void);
   uint32_t           getBlockHeight(void) const;
   uint8_t            getDuplicateID(void) const;
   uint16_t           getBlockTxIndex(void) const;

   /////////////////////////////////////////////////////////////////////////////
   void               pprint(ostream & os=cout, int nIndent=0) const;

   /////////////////////////////////////////////////////////////////////////////
   bool operator==(BinaryData const & dbkey) const { return dbKey6B_ == dbkey; }
   bool operator==(TxRef const & txr) const  { return dbKey6B_ == txr.dbKey6B_;}

private:
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
   InterfaceToLDB*  dbIface_;  
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

   explicit OutPoint(uint8_t const * ptr, uint32_t remaining) { unserialize(ptr, remaining); }
   explicit OutPoint(BinaryData const & txHash, uint32_t txOutIndex) : 
                txHash_(txHash), txOutIndex_(txOutIndex) { }

   BinaryData const &   getTxHash(void)     const { return txHash_; }
   BinaryDataRef        getTxHashRef(void)  const { return BinaryDataRef(txHash_); }
   uint32_t             getTxOutIndex(void) const { return txOutIndex_; }

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

private:
   BinaryData txHash_;
   uint32_t   txOutIndex_;

};



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class TxIn
{
   friend class BlockDataManager_LevelDB;
   friend class InterfaceToLDB;

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
   uint32_t         getSize(void) const { assert(isInitialized()); return dataCopy_.getSize(); }
   bool             isStandard(void) const { return scriptType_!=TXIN_SCRIPT_NONSTANDARD; }
   bool             isCoinbase(void) const { return (scriptType_ == TXIN_SCRIPT_COINBASE); }
   bool             isInitialized(void) const {return dataCopy_.getSize() > 0; }
   OutPoint         getOutPoint(void) const;

   // Script ops
   BinaryData       getScript(void) const;
   BinaryDataRef    getScriptRef(void) const;
   uint32_t         getScriptSize(void) { return getSize() - (scriptOffset_ + 4); }
   TXIN_SCRIPT_TYPE getScriptType(void) const { return scriptType_; }
   uint32_t         getScriptOffset(void) const { return scriptOffset_; }

   // SWIG doesn't handle these enums well, so we will provide some direct bools
   bool             isScriptStandard(void)   { return scriptType_ != TXIN_SCRIPT_NONSTANDARD;}
   bool             isScriptStdUncompr(void) { return scriptType_ == TXIN_SCRIPT_STDUNCOMPR;}
   bool             isScriptStdCompr(void)   { return scriptType_ == TXIN_SCRIPT_STDCOMPR;}
   bool             isScriptCoinbase(void)   { return scriptType_ == TXIN_SCRIPT_COINBASE;}
   bool             isScriptSpendMulti(void) { return scriptType_ == TXIN_SCRIPT_SPENDMULTI; }
   bool             isScriptSpendPubKey(void){ return scriptType_ == TXIN_SCRIPT_SPENDPUBKEY; }
   bool             isScriptSpendP2SH(void)  { return scriptType_ == TXIN_SCRIPT_SPENDP2SH; }
   bool             isScriptNonStd(void)     { return scriptType_ == TXIN_SCRIPT_NONSTANDARD; }

   TxRef            getParentTxRef(void) { return parentTx_; }
   uint32_t         getIndex(void) { return index_; }

   //void setParentTx(TxRef txref, int32_t idx=-1) {parentTx_=txref; index_=idx;}

   uint32_t         getSequence(void)   { return READ_UINT32_LE(getPtr()+getSize()-4); }

   BinaryData       getParentHash(void);
   uint32_t         getParentHeight(void);

   void             setParentHash(BinaryData const & txhash) {parentHash_ = txhash;}
   void             setParentHeight(uint32_t blkheight) {parentHeight_ = blkheight;}

   /////////////////////////////////////////////////////////////////////////////
   BinaryData       serialize(void)    { return dataCopy_; }

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
   friend class InterfaceToLDB;

public:

   /////////////////////////////////////////////////////////////////////////////
   TxOut(void) : dataCopy_(0), parentHash_(0) {}
   /*
   TxOut(uint8_t const * ptr, 
         uint32_t        nBytes=0, 
         TxRef           parent=TxRef(), 
         uint32_t        idx=UINT32_MAX) { unserialize(ptr, nBytes, parent, idx); } */

   uint8_t const * getPtr(void) const { return dataCopy_.getPtr(); }
   uint32_t        getSize(void) const { return dataCopy_.getSize(); }
   uint64_t        getValue(void) const { return READ_UINT64_LE(dataCopy_.getPtr()); }
   bool            isStandard(void) const { return scriptType_ != TXOUT_SCRIPT_NONSTANDARD; }
   bool            isInitialized(void) const {return dataCopy_.getSize() > 0; }
   TxRef           getParentTxRef(void) { return parentTx_; }
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

   BinaryData         getParentHash(void);
   uint32_t           getParentHeight(void);

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
   friend class BlockDataManager_LevelDB;
   friend class InterfaceToLDB;

public:
   Tx(void) : isInitialized_(false), offsetsTxIn_(0), offsetsTxOut_(0) {}
   explicit Tx(uint8_t const * ptr, uint32_t size) { unserialize(ptr, size);       }
   explicit Tx(BinaryRefReader & brr)     { unserialize(brr);       }
   explicit Tx(BinaryData const & str)    { unserialize(str);       }
   explicit Tx(BinaryDataRef const & str) { unserialize(str);       }
   explicit Tx(TxRef txref);
     
   uint8_t const *    getPtr(void)  const { return dataCopy_.getPtr();  }
   uint32_t           getSize(void) const { return dataCopy_.getSize(); }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t           getVersion(void)   const { return READ_UINT32_LE(dataCopy_.getPtr());}
   uint32_t           getNumTxIn(void)   const { return offsetsTxIn_.size()-1;}
   uint32_t           getNumTxOut(void)  const { return offsetsTxOut_.size()-1;}
   BinaryData         getThisHash(void)  const;
   bool               isMainBranch(void) const;
   bool               isInitialized(void) const { return isInitialized_; }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t           getTxInOffset(uint32_t i) const  { return offsetsTxIn_[i]; }
   uint32_t           getTxOutOffset(uint32_t i) const { return offsetsTxOut_[i]; }

   /////////////////////////////////////////////////////////////////////////////
   static Tx          createFromStr(BinaryData const & bd) {return Tx(bd);}

   /////////////////////////////////////////////////////////////////////////////
   bool               hasTxRef(void) const { return txRefObj_.isInitialized(); }
   TxRef              getTxRef(void) const { return txRefObj_; }
   void               setTxRef(TxRef ref) { txRefObj_ = ref; }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData         serialize(void) const    { return dataCopy_; }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr, uint32_t size);
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
   TxIn   getTxInCopy(int i);
   TxOut  getTxOutCopy(int i);

   /////////////////////////////////////////////////////////////////////////////
   // All these methods return UINTX_MAX if txRefObj.isNull()
   BinaryData getBlockHash(void)      { return txRefObj_.getBlockHash();      }
   uint32_t   getBlockTimestamp(void) { return txRefObj_.getBlockTimestamp(); }
   uint32_t   getBlockHeight(void)    { return txRefObj_.getBlockHeight();    }
   uint8_t    getDuplicateID(void)    { return txRefObj_.getDuplicateID();    }
   uint16_t   getBlockTxIndex(void)   { return txRefObj_.getBlockTxIndex();   }

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
   //BlockHeader*  headerPtr_;
   TxRef         txRefObj_;
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
   explicit TxIOPair(BinaryData txOutKey8B, uint64_t value);
   explicit TxIOPair(TxRef txRefO, uint32_t txoutIndex, 
                     TxRef txRefI, uint32_t txinIndex);

   // Lots of accessors
   bool      hasTxOut(void) const   { return (txRefOfOutput_.isInitialized()); }
   bool      hasTxIn(void) const    { return (txRefOfInput_.isInitialized()); }
   bool      hasTxOutInMain(void) const;
   bool      hasTxInInMain(void) const;
   bool      hasTxOutZC(void) const;
   bool      hasTxInZC(void) const;
   bool      hasValue(void) const   { return (amount_!=0); }
   uint64_t  getValue(void) const   { return  amount_;}
   void      setValue(uint64_t newVal) { amount_ = newVal;}

   //////////////////////////////////////////////////////////////////////////////
   TxOut     getTxOutCopy(void);
   TxIn      getTxInCopy(void);
   TxOut     getTxOutZC(void) const {return txOfOutputZC_->getTxOutCopy(indexOfOutputZC_);}
   TxIn      getTxInZC(void) const  {return txOfInputZC_->getTxInCopy(indexOfInputZC_);}
   TxRef     getTxRefOfOutput(void) const { return txRefOfOutput_; }
   TxRef     getTxRefOfInput(void) const  { return txRefOfInput_;  }
   uint32_t  getIndexOfOutput(void) const { return indexOfOutput_; }
   uint32_t  getIndexOfInput(void) const  { return indexOfInput_;  }
   OutPoint  getOutPoint(void) { return OutPoint(getTxHashOfOutput(),indexOfOutput_);}

   pair<bool,bool> reassessValidity(void);
   bool  isTxOutFromSelf(void) const  { return isTxOutFromSelf_; }
   void setTxOutFromSelf(bool isTrue=true) { isTxOutFromSelf_ = isTrue; }
   bool  isFromCoinbase(void) const { return isFromCoinbase_; }
   void setFromCoinbase(bool isTrue=true) { isFromCoinbase_ = isTrue; }
   bool  isMultisig(void) const { return isMultisig_; }
   void setMultisig(bool isTrue=true) { isMultisig_ = isTrue; }

   BinaryData getDBKeyOfOutput(void) const
               { return txRefOfOutput_.getDBKeyOfChild(indexOfOutput_);}
   BinaryData getDBKeyOfInput(void) const
               { return txRefOfInput_.getDBKeyOfChild(indexOfInput_);}

   //////////////////////////////////////////////////////////////////////////////
   BinaryData    getTxHashOfInput(void);
   BinaryData    getTxHashOfOutput(void);

   bool setTxIn   (TxRef  txref, uint32_t index);
   bool setTxIn   (BinaryData dbKey8B);
   bool setTxOut  (TxRef  txref, uint32_t index);
   bool setTxOut  (BinaryData dbKey8B);
   bool setTxInZC (Tx*    tx,    uint32_t index);
   bool setTxOutZC(Tx*    tx,    uint32_t index);

   //////////////////////////////////////////////////////////////////////////////
   bool isSourceUnknown(void) { return ( !hasTxOut() &&  hasTxIn() ); }
   bool isStandardTxOutScript(void);

   bool isSpent(void);
   bool isUnspent(void);
   bool isSpendable(uint32_t currBlk=0, bool ignoreAllZeroConf=false);
   bool isMineButUnconfirmed(uint32_t currBlk, bool includeAllZeroConf=false);
   void clearZCFields(void);
   void pprintOneLine(void);

   bool operator<(TxIOPair const & t2)
      { return (getDBKeyOfOutput() < t2.getDBKeyOfOutput()); }
   bool operator==(TxIOPair const & t2)
      { return (getDBKeyOfOutput() == t2.getDBKeyOfOutput()); }

private:
   uint64_t  amount_;

   TxRef     txRefOfOutput_;
   uint32_t  indexOfOutput_;
   TxRef     txRefOfInput_;
   uint32_t  indexOfInput_;

   // Zero-conf data isn't on disk, yet, so can't use TxRef
   Tx*       txOfOutputZC_;
   uint32_t  indexOfOutputZC_;
   Tx*       txOfInputZC_;
   uint32_t  indexOfInputZC_;

   bool      isTxOutFromSelf_;
   bool      isFromCoinbase_;
   bool      isMultisig_;
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
   UnspentTxOut(TxOut & txout, uint32_t blknum) { init(txout, blknum);}


   UnspentTxOut(BinaryData const & hash, uint32_t outIndex, uint32_t height, 
                uint64_t val, BinaryData const & script) :
      txHash_(hash), txOutIndex_(outIndex), txHeight_(height),
      value_(val), script_(script) {}

   void init(TxOut & txout, uint32_t blknum, bool isMultiRef=false);

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

   
   void setUniqueKey(BinaryData const & key)
   {
      addrType_ = uniqueKey_[0];
      uniqueKey_.copyFrom(key.getPtr()+1, key.getSize()-1);
   }

   BinaryData        uniqueKey_;
   uint8_t           addrType_;
   uint32_t          blkCreated_;
   uint32_t          alreadyScannedUpToBlk_;
   uint64_t          sumValue_;
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
   Tx         getTxCopy()    { return txRefObj_.getTxCopy(); }
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

   RegisteredTx( TxRef txref, 
                 BinaryData const & txHash,
                 uint32_t blkNum,
                 uint16_t txIndex) :
         txRefObj_(txref),
         txHash_(txHash),
         blkNum_(blkNum),
         txIndex_(txIndex) { }

   explicit RegisteredTx(TxRef txref) :
         txRefObj_(txref),
         txHash_(txref.getThisHash()),
         blkNum_(txref.getBlockHeight()),
         txIndex_(txref.getBlockTxIndex()) { }

   explicit RegisteredTx(Tx & tx) :
         txRefObj_(tx.getTxRef()),
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

// kate: indent-width 3; replace-tabs on;
#endif

