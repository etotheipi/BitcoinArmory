////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //            
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                   
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#ifndef _H_TX_CLASSES
#define _H_TX_CLASSES

#include "BinaryData.h"
#include "BtcUtils.h"
#include "DBUtils.h"

#define USE_FULL_CUSTOM_LIST  1
#define ADJUST_FEE            2
#define SHUFFLE_ENTRIES       4

////
class RecipientReuseException
{
private:
   vector<string> addrVec_;
   uint64_t total_;
   uint64_t value_;

public:
   RecipientReuseException(
      const vector<BinaryData>& scrAddrVec, uint64_t total, uint64_t val) :
      total_(total), value_(val)
   {
      for (auto& scrAddr : scrAddrVec)
      {
         auto&& addr58 = BtcUtils::scrAddrToBase58(scrAddr);
         addrVec_.push_back(string(addr58.getCharPtr(), addr58.getSize()));
      }
   }

   const vector<string>& getAddresses(void) const { return addrVec_; }
   uint64_t total(void) const { return total_; }
   uint64_t value(void) const { return value_; }
};

////////////////////////////////////////////////////////////////////////////////
// OutPoint is just a reference to a TxOut
class OutPoint
{
   friend class BlockDataManager;

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

protected:
   BinaryData txHash_;
   uint32_t   txOutIndex_;

   //this member isn't set by ctor, but processed after the first call to
   //get DBKey
   mutable BinaryData DBkey_;
};

////////////////////////////////////////////////////////////////////////////////
class TxRef
{
   friend class BlockDataManager;
   friend class Tx;

public:
   /////////////////////////////////////////////////////////////////////////////
   TxRef() { }
   TxRef(BinaryDataRef bdr) { setRef(bdr); }

   /////////////////////////////////////////////////////////////////////////////
   void setRef(BinaryDataRef bdr);

   /////////////////////////////////////////////////////////////////////////////
   bool           isInitialized(void)  const { return dbKey6B_.getSize()>0; }
   bool           isNull(void) const { return !isInitialized(); }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData     getDBKey(void) const   { return dbKey6B_; }
   BinaryDataRef  getDBKeyRef(void)      { return dbKey6B_.getRef(); }
   void           setDBKey(BinaryData    const & bd) { dbKey6B_.copyFrom(bd); }
   void           setDBKey(BinaryDataRef const & bd) { dbKey6B_.copyFrom(bd); }


   /////////////////////////////////////////////////////////////////////////////
   BinaryData     getDBKeyOfChild(uint16_t i) const
   {
      return dbKey6B_ + WRITE_UINT16_BE(i);
   }

   uint16_t           getBlockTxIndex(void) const;
   uint32_t           getBlockHeight(void) const;
   uint8_t            getDuplicateID(void) const;

   /////////////////////////////////////////////////////////////////////////////
   void               pprint(ostream & os = cout, int nIndent = 0) const;

   /////////////////////////////////////////////////////////////////////////////
   bool operator==(BinaryData const & dbkey) const { return dbKey6B_ == dbkey; }
   bool operator==(TxRef const & txr) const  { return dbKey6B_ == txr.dbKey6B_; }

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

////////////////////////////////////////////////////////////////////////////////
class TxIn
{
   friend class BlockDataManager;

public:
   TxIn(void) : dataCopy_(0), parentHash_(0), parentHeight_(UINT32_MAX),
      scriptType_(TXIN_SCRIPT_NONSTANDARD), scriptOffset_(0) {}

   uint8_t const *  getPtr(void) const { assert(isInitialized()); return dataCopy_.getPtr(); }
   size_t           getSize(void) const { assert(isInitialized()); return dataCopy_.getSize(); }
   bool             isStandard(void) const { return scriptType_ != TXIN_SCRIPT_NONSTANDARD; }
   bool             isCoinbase(void) const { return (scriptType_ == TXIN_SCRIPT_COINBASE); }
   bool             isInitialized(void) const { return dataCopy_.getSize() > 0; }
   OutPoint         getOutPoint(void) const;

   // Script ops
   BinaryData       getScript(void) const;
   BinaryDataRef    getScriptRef(void) const;
   size_t           getScriptSize(void) { return getSize() - (scriptOffset_ + 4); }
   TXIN_SCRIPT_TYPE getScriptType(void) const { return scriptType_; }
   uint32_t         getScriptOffset(void) const { return scriptOffset_; }

   // SWIG doesn't handle these enums well, so we will provide some direct bools
   bool             isScriptStandard() const   { return scriptType_ != TXIN_SCRIPT_NONSTANDARD; }
   bool             isScriptStdUncompr() const { return scriptType_ == TXIN_SCRIPT_STDUNCOMPR; }
   bool             isScriptStdCompr() const  { return scriptType_ == TXIN_SCRIPT_STDCOMPR; }
   bool             isScriptCoinbase() const   { return scriptType_ == TXIN_SCRIPT_COINBASE; }
   bool             isScriptSpendMulti() const { return scriptType_ == TXIN_SCRIPT_SPENDMULTI; }
   bool             isScriptSpendPubKey() const { return scriptType_ == TXIN_SCRIPT_SPENDPUBKEY; }
   bool             isScriptSpendP2SH() const  { return scriptType_ == TXIN_SCRIPT_SPENDP2SH; }
   bool             isScriptNonStd() const    { return scriptType_ == TXIN_SCRIPT_NONSTANDARD; }

   TxRef            getParentTxRef() const { return parentTx_; }
   uint32_t         getIndex(void) const { return index_; }

   //void setParentTx(TxRef txref, int32_t idx=-1) {parentTx_=txref; index_=idx;}

   uint32_t         getSequence() const  { return READ_UINT32_LE(getPtr() + getSize() - 4); }
   uint32_t         getParentHeight() const;

   void             setParentHash(BinaryData const & txhash) { parentHash_ = txhash; }
   const BinaryData& getParentHash(void) const { return parentHash_; }
   void             setParentHeight(uint32_t blkheight) { parentHeight_ = blkheight; }

   /////////////////////////////////////////////////////////////////////////////
   const BinaryData&  serialize(void) const { return dataCopy_; }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize_checked(uint8_t const * ptr,
      uint32_t        size,
      uint32_t        nbytes = 0,
      TxRef           parent = TxRef(),
      uint32_t        idx = UINT32_MAX);

   void unserialize(BinaryData const & str,
      uint32_t       nbytes = 0,
      TxRef          parent = TxRef(),
      uint32_t       idx = UINT32_MAX);

   void unserialize(BinaryDataRef  str,
      uint32_t       nbytes = 0,
      TxRef          parent = TxRef(),
      uint32_t       idx = UINT32_MAX);

   void unserialize(BinaryRefReader & brr,
      uint32_t       nbytes = 0,
      TxRef          parent = TxRef(),
      uint32_t       idx = UINT32_MAX);

   void unserialize_swigsafe_(BinaryData const & rawIn) { unserialize(rawIn); }

   /////////////////////////////////////////////////////////////////////////////
   // Not all TxIns have sendor info.  Might have to go to the Outpoint and get
   // the corresponding TxOut to find the sender.  In the case the sender is
   // not available, return false and don't write the output
   bool       getSenderScrAddrIfAvail(BinaryData & addrTarget) const;
   BinaryData getSenderScrAddrIfAvail(void) const;

   void pprint(ostream & os = cout, int nIndent = 0, bool pBigendian = true) const;


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
class TxOut
{
   friend class BlockDataManager;
   friend class ZeroConfContainer;

private:
   void setParentTxRef(const BinaryData& key)
   {
      parentTx_.setDBKey(key);
   }

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
   bool            isInitialized(void) const { return dataCopy_.getSize() > 0; }
   TxRef           getParentTxRef() const { return parentTx_; }
   uint32_t        getParentIndex() const;
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
   bool isScriptStandard(void)    { return scriptType_ != TXOUT_SCRIPT_NONSTANDARD; }
   bool isScriptStdHash160(void)  { return scriptType_ == TXOUT_SCRIPT_STDHASH160; }
   bool isScriptStdPubKey65(void) { return scriptType_ == TXOUT_SCRIPT_STDPUBKEY65; }
   bool isScriptStdPubKey33(void) { return scriptType_ == TXOUT_SCRIPT_STDPUBKEY33; }
   bool isScriptP2SH(void)        { return scriptType_ == TXOUT_SCRIPT_P2SH; }
   bool isScriptNonStd(void)      { return scriptType_ == TXOUT_SCRIPT_NONSTANDARD; }


   /////////////////////////////////////////////////////////////////////////////
   BinaryData         serialize(void) { return BinaryData(dataCopy_); }
   BinaryDataRef      serializeRef(void) { return dataCopy_; }

   uint32_t           getParentHeight() const;

   void               setParentHash(BinaryData const & txhash) { parentHash_ = txhash; }
   const BinaryData& getParentHash(void) const { return parentHash_; }
   void               setParentHeight(uint32_t blkheight) { parentHeight_ = blkheight; }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize_checked(uint8_t const *   ptr,
      uint32_t          size,
      uint32_t          nbytes = 0,
      TxRef             parent = TxRef(),
      uint32_t          idx = UINT32_MAX);

   void unserialize(BinaryData const & str,
      uint32_t           nbytes = 0,
      TxRef              parent = TxRef(),
      uint32_t           idx = UINT32_MAX);

   void unserialize(BinaryDataRef const & str,
      uint32_t          nbytes = 0,
      TxRef             parent = TxRef(),
      uint32_t          idx = UINT32_MAX);
   void unserialize(BinaryRefReader & brr,
      uint32_t          nbytes = 0,
      TxRef             parent = TxRef(),
      uint32_t          idx = UINT32_MAX);

   void unserialize_swigsafe_(BinaryData const & rawOut) { unserialize(rawOut); }

   void  pprint(ostream & os = cout, int nIndent = 0, bool pBigendian = true);

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
class Tx
{
   friend class BtcWallet;
   friend class BlockDataManager;
   friend class TransactionVerifier;

public:
   Tx(void) : isInitialized_(false), offsetsTxIn_(0), offsetsTxOut_(0) {}
   explicit Tx(uint8_t const * ptr, uint32_t size) { unserialize(ptr, size); }
   explicit Tx(BinaryRefReader & brr)     { unserialize(brr); }
   explicit Tx(BinaryData const & str)    { unserialize(str); }
   explicit Tx(BinaryDataRef const & str) { unserialize(str); }

   uint8_t const *    getPtr(void)  const { return dataCopy_.getPtr(); }
   size_t             getSize(void) const { return dataCopy_.getSize(); }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t           getVersion(void)   const { return READ_UINT32_LE(dataCopy_.getPtr()); }
   size_t             getNumTxIn(void)   const { return offsetsTxIn_.size() - 1; }
   size_t             getNumTxOut(void)  const { return offsetsTxOut_.size() - 1; }
   BinaryData         getThisHash(void)  const;
   bool               isInitialized(void) const { return isInitialized_; }
   bool               isCoinbase(void) const;

   /////////////////////////////////////////////////////////////////////////////
   size_t             getTxInOffset(uint32_t i) const  { return offsetsTxIn_[i]; }
   size_t             getTxOutOffset(uint32_t i) const { return offsetsTxOut_[i]; }
   size_t             getWitnessOffset(uint32_t i) const { return  offsetsWitness_[i]; }

   /////////////////////////////////////////////////////////////////////////////
   static Tx          createFromStr(BinaryData const & bd) { return Tx(bd); }

   /////////////////////////////////////////////////////////////////////////////
   bool               hasTxRef(void) const { return txRefObj_.isInitialized(); }
   TxRef              getTxRef(void) const { return txRefObj_; }
   void               setTxRef(TxRef ref) { txRefObj_ = ref; }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData         serialize(void) const    { return dataCopy_; }
   BinaryData         serializeWithMetaData(void) const;
   BinaryData         serializeNoWitness(void) const;

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr, size_t size);
   void unserialize(BinaryData const & str) { unserialize(str.getPtr(), str.getSize()); }
   void unserialize(BinaryDataRef const & str) { unserialize(str.getPtr(), str.getSize()); }
   void unserialize(BinaryRefReader & brr);
   //void unserialize_no_txout(BinaryRefReader & brr);
   void unserialize_swigsafe_(BinaryData const & rawTx) { unserialize(rawTx); }

   void unserializeWithMetaData(const BinaryData& rawTx);


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
   uint32_t   getBlockHeight(void)    { return txRefObj_.getBlockHeight(); }
   uint8_t    getDuplicateID(void)    { return txRefObj_.getDuplicateID(); }
   uint16_t   getBlockTxIndex(void)   { return txRefObj_.getBlockTxIndex(); }

   bool isRBF(void) const;
   void setRBF(bool isTrue)
   {
      isRBF_ = isTrue;
   }

   bool isChained(void) const { return isChainedZc_; }
   void setChainedZC(bool isTrue)
   {
      isChainedZc_ = isTrue;
   }

   /////////////////////////////////////////////////////////////////////////////
   void pprint(ostream & os = cout, int nIndent = 0, bool pBigendian = true);
   void pprintAlot(ostream & os = cout);

   bool operator==(const Tx& rhs) const
   {
      if (this->isInitialized() && rhs.isInitialized())
         return this->thisHash_ == rhs.thisHash_;
      return false;
   }

   void setTxTime(uint32_t txtime) { txTime_ = txtime; }
   uint32_t getTxTime(void) const { return txTime_; }

   //returns tx weight in bytes
   size_t getTxWeight(void) const;

private:
   // Full copy of the serialized tx
   BinaryData    dataCopy_;
   bool          isInitialized_;
   bool          usesWitness_ = false;

   uint32_t      version_;
   uint32_t      lockTime_;

   // Derived properties - we expect these to be set after construct/copy
   mutable BinaryData    thisHash_;

   // Will always create TxIns and TxOuts on-the-fly; only store the offsets
   vector<size_t> offsetsTxIn_;
   vector<size_t> offsetsTxOut_;
   vector<size_t> offsetsWitness_;

   // To be calculated later
   //BlockHeader*  headerPtr_;
   TxRef         txRefObj_;

   uint32_t      txTime_;

   bool isRBF_ = false;
   bool isChainedZc_ = false;
};

////////////////////////////////////////////////////////////////////////////////
struct UTXO
{
   BinaryData txHash_;
   uint32_t   txOutIndex_ = UINT32_MAX;
   uint32_t   txHeight_ = UINT32_MAX;
   uint32_t   txIndex_ = UINT32_MAX;
   uint64_t   value_ = 0;
   BinaryData script_;
   bool       isMultisigRef_ = false;
   unsigned   preferredSequence_ = UINT32_MAX;

   //for coin selection
   bool isInputSW_ = false;
   unsigned txinRedeemSizeBytes_ = UINT32_MAX;
   unsigned witnessDataSizeBytes_ = UINT32_MAX;

   UTXO(uint64_t value, uint32_t txHeight, uint32_t txIndex, 
      uint32_t txOutIndex, BinaryData txHash, BinaryData script) :
      txHash_(move(txHash)), txHeight_(txHeight), txIndex_(txIndex), 
      txOutIndex_(txOutIndex), value_(value), script_(move(script))
   {}

   UTXO(void) {}

   BinaryData getRecipientScrAddr(void) const
   {
      return BtcUtils::getTxOutScrAddr(script_);
   }

   uint64_t getValue(void) const { return value_; }
   const BinaryData& getTxHash(void) const { return txHash_; }
   string getTxHashStr(void) const { return txHash_.toHexStr(); }
   const BinaryData& getScript(void) const { return script_; }
   uint32_t getTxIndex(void) const { return txIndex_; }
   uint32_t getTxOutIndex(void) const { return txOutIndex_; }
   uint32_t getNumConfirm(uint32_t height) const
   {
      if (txHeight_ == UINT32_MAX)
         return 0;

      return height - txHeight_ + 1;
   }
   unsigned getPreferredSequence(void) const { return preferredSequence_; }

   uint32_t getHeight(void) const { return txHeight_; }

   BinaryData serialize(void) const;
   void unserialize(const BinaryData&);
   void unserializeRaw(const BinaryData&);

   //coin seletion methods
   bool isSegWit(void) const { return isInputSW_; }
   unsigned getInputRedeemSize(void) const;
   unsigned getWitnessDataSize(void) const;

   bool operator==(const UTXO& rhs) const
   {
      if (rhs.getTxHash() != getTxHash())
         return false;

      return rhs.getTxOutIndex() == getTxOutIndex();
   }

   bool operator<(const UTXO& rhs) const
   {
      if (txHeight_ != rhs.txHeight_)
         return txHeight_ < rhs.txHeight_;

      if (txIndex_ != rhs.txIndex_)
         return txIndex_ < rhs.txIndex_;

      if (txOutIndex_ != rhs.txOutIndex_)
         return txOutIndex_ < rhs.txOutIndex_;

      return false;
   }

   bool isInitialized(void) const { return script_.getSize() > 0; }
};


////////////////////////////////////////////////////////////////////////////////
class AddressBookEntry
{
public:

   /////
   AddressBookEntry(void) : scrAddr_(BtcUtils::EmptyHash()) {}
   AddressBookEntry(BinaryData scraddr) : scrAddr_(scraddr) {}
   void addTxHash(const BinaryData& hash) { txHashList_.push_back(hash); }
   const BinaryData& getScrAddr(void) { return scrAddr_; }

   /////
   vector<BinaryData> getTxHashList(void) const
   {
      return txHashList_;
   }

   /////
   bool operator<(AddressBookEntry const & abe2) const
   {
      return scrAddr_ < abe2.scrAddr_;
   }

   BinaryData serialize(void) const;
   void unserialize(const BinaryData& data);

private:
   BinaryData scrAddr_;
   vector<BinaryData> txHashList_;
};

#endif
