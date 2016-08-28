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
#include "TxClasses.h"

typedef uint32_t TxFilterType;

////////////////////////////////////////////////////////////////////////////////
class LMDBBlockDatabase; 
class TxRef;
class Tx;
class TxIn;
class TxOut;

////////////////////////////////////////////////////////////////////////////////
template<typename T> class TxFilter
{
   template <typename U> friend class TxFilterPool;

private:
   vector<T> filterVector_;
   const uint8_t* filterPtr_ = nullptr;
   
   uint32_t blockKey_ = UINT32_MAX;
   size_t len_ = SIZE_MAX;
   bool isValid_ = false;

private:
   void update(const BinaryData& hash)
   {
      if (hash.getSize() != 32)
         throw range_error("unexpected hash length");

      auto hashHead = (T*)hash.getPtr();

      filterVector_.push_back(*hashHead);
   }

   uint32_t getBlockKeyFromPtr(const uint8_t* ptr)
   {
      return *(uint32_t*)(ptr + 4);
   }

   uint32_t getLenFromPtr(const uint8_t* ptr)
   {
      return *(uint32_t*)(ptr + 8);
   }

   bool checkPtrLen(const uint8_t* ptr)
   {
      if (ptr == nullptr)
         throw runtime_error("invalid txfilter ptr");

      auto size = (uint32_t*)(ptr);
      if (*size < 12)
         throw runtime_error("invalid txfilter ptr");

      auto len = (uint32_t*)(ptr + 8);
      auto total = *len * sizeof(T) + 12;
      if (total != *size)
         throw runtime_error("invalid txfilter ptr");

      return true;
   }

   void deserialize(uint8_t* ptr)
   {
      auto size = (uint32_t*)ptr;
      blockKey_ = *(uint32_t*)(ptr + 4);
      len_ = *(uint32_t*)(ptr + 8);

      if (*size != len_ * sizeof(T) + 12)
         throw runtime_error("deser error");
      
      filterVector_.resize(len_);
      memcpy(&filterVector_[0], ptr + 12, len_ * sizeof(T));

      isValid_ = true;
   }


public:
   TxFilter(void)
   {}

   TxFilter(unsigned blockkey, size_t len) :
      blockKey_(blockkey), len_(len)
   {      
      filterVector_.reserve(len_);

      isValid_ = true;
   }

   TxFilter(const uint8_t* ptr) :
      isValid_(checkPtrLen(ptr)),
      blockKey_(getBlockKeyFromPtr(ptr)), 
      len_(getLenFromPtr(ptr))
   {
      filterPtr_ = ptr;
   }

   TxFilter(const TxFilter<T>& obj) :
      blockKey_(obj.blockKey_), len_(obj.len_),
      isValid_(obj.isValid_), filterPtr_(obj.filterPtr_)
   {
      filterVector_ = obj.filterVector_;
   }

   TxFilter(TxFilter<T>&& mv) :
      blockKey_(mv.blockKey_), len_(mv.len_),
      isValid_(mv.isValid_), filterPtr_(mv.filterPtr_)
   {
      filterVector_ = move(mv.filterVector_);
   }

   TxFilter& operator=(const TxFilter& rhs)
   {
      blockKey_ = rhs.blockKey_;
      len_ = rhs.len_;
      filterVector_ = rhs.filterVector_;
      filterPtr_ = rhs.filterPtr_;

      isValid_ = true;

      return *this;
   }

   bool isValid(void) const { return isValid_; }

   void update(const vector<BinaryData>& hashVec)
   {
      if (!isValid())
         throw runtime_error("txfilter needs initialized first");

      for (auto& hash : hashVec)
      {
         update(hash);
      }
   }   
   
   set<uint32_t> compare(const BinaryData& hash) const
   {
      auto key = (T*)hash.getPtr();
      return compare(*key);
   }

   set<uint32_t> compare(const T& key) const
   {
      set<uint32_t> resultSet;
      if (filterVector_.size() != 0)
      {
         for (unsigned i = 0; i < filterVector_.size(); i++)
         {
            if (filterVector_[i] == key)
               resultSet.insert(i);
         }
      }
      else if (filterPtr_ != nullptr)
      {
         auto ptr = (T*)(filterPtr_ + 12);
         for (unsigned i = 0; i < len_; i++)
            if (ptr[i] == key)
               resultSet.insert(i);
      }
      else
         throw runtime_error("invalid filter");

      return resultSet;
   }

   uint32_t getBlockKey(void) const { return blockKey_; }

   void serialize(BinaryWriter& bw) const
   {
      if (blockKey_ == UINT32_MAX)
         throw runtime_error("invalid block key");

      uint32_t size = 12 + filterVector_.size() * sizeof(T);
      bw.put_uint32_t(size);
      bw.put_uint32_t(blockKey_);
      bw.put_uint32_t(filterVector_.size());
      
      BinaryDataRef bdr(
         (uint8_t*)&filterVector_[0], filterVector_.size() * sizeof(T));
      bw.put_BinaryData(bdr);
   }

   bool operator < (const TxFilter& rhs) const
   {
      //we want higher blocks to appear earlier in sets/maps
      return blockKey_ > rhs.blockKey_;
   }
};

class BlockHeader
{
   friend class Blockchain;
   friend class testBlockHeader;
   friend class BlockData;

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

   BinaryData getBlockDataKey(void) const
   {
      return DBUtils::getBlkDataKeyNoPrefix(blockHeight_, duplicateID_);
   }

   unsigned int getThisID(void) const { return uniqueID_; }
   void setUniqueID(unsigned int& ID) { uniqueID_ = ID; }

private:
   BinaryData     dataCopy_;
   bool           isInitialized_ = false;
   bool           isMainBranch_ = false;
   bool           isOrphan_ = true;
   bool           isFinishedCalc_ = false;
   // Specific to the DB storage
   uint8_t        duplicateID_ = 0xFF; // ID of this blk rel to others at same height
   uint32_t       blockHeight_ = UINT32_MAX;
   
   uint32_t       numTx_ = UINT32_MAX;
   uint32_t       numBlockBytes_; // includes header + nTx + sum(Tx)
   
   // Derived properties - we expect these to be set after construct/copy
   BinaryData     thisHash_;
   double         difficultyDbl_ = 0.0;

   // Need to compute these later
   BinaryData     nextHash_;
   double         difficultySum_ = 0.0;

   string         blkFile_;
   uint32_t       blkFileNum_ = UINT32_MAX;
   uint64_t       blkFileOffset_ = SIZE_MAX;

   unsigned int uniqueID_ = UINT32_MAX;
};



////////////////////////////////////////////////////////////////////////////////
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

////////////////////////////////////////////////////////////////////////////////
class DBOutPoint : public OutPoint
{
private:
   LMDBBlockDatabase* db_;

public:
   DBOutPoint(OutPoint op, LMDBBlockDatabase* db) :
      OutPoint(op), db_(db)
   {}

   BinaryDataRef getDBkey(void) const;

};

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
   uint32_t     getTxtIndex(void) const    { return txIndex_; }
   uint32_t     getTxOutIndex(void) const  { return txOutIndex_; }
   uint64_t     getValue(void)  const      { return value_;      }
   uint64_t     getTxHeight(void)  const   { return txHeight_;   }
   uint32_t     isMultisigRef(void) const  { return isMultisigRef_; }

   OutPoint getOutPoint(void) const { return OutPoint(txHash_, txOutIndex_); }

   BinaryData const & getScript(void) const      { return script_;     }
   BinaryData   getRecipientScrAddr(void) const;

   uint32_t   getNumConfirm(uint32_t currBlknum) const;
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
   uint32_t   txIndex_;
   uint64_t   value_;
   BinaryData script_;
   bool       isMultisigRef_;

   // This can be set and used as part of a compare function:  if you want
   // each TxOut prioritization to be dependent on the target Tx amount.
   uint64_t   targetTxAmount_;
};

#endif

