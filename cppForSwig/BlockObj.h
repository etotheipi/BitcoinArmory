#ifndef _BLOCKOBJ_H_
#define _BLOCKOBJ_H_


#include <iostream>
#include <vector>
#include <map>
#include <cassert>

#include "BinaryData.h"
#include "BlockObjRef.h"



class BlockHeaderRef;
class OutPointRef;
class TxInRef;
class TxOutRef;
class TxRef;


class BlockHeader
{

   friend class BlockDataManager_FullRAM;
   friend class BlockHeaderRef;

public: 

   /////////////////////////////////////////////////////////////////////////////
   uint32_t            getVersion(void) const       { return version_;      }
   BinaryData const &  getPrevHash(void) const      { return prevHash_;     }
   BinaryData const &  getMerkleRoot(void) const    { return merkleRoot_;   }
   uint32_t            getTimestamp(void) const     { return timestamp_;    }
   BinaryData const &  getDiffBits(void) const      { return diffBits_;  }
   uint32_t            getNonce(void) const         { return nonce_;        }
   BinaryData const &  getThisHash(void) const      { return thisHash_;     }
   BinaryData const &  getNextHash(void) const      { return nextHash_;     }
   uint32_t            getNumTx(void) const         { return numTx_;        }
   uint32_t            getBlockHeight(void) const   { return blockHeight_;  }
   double              getDifficulty(void) const    { return difficultyDbl_;  }
   double              getDifficultySum(void) const { return difficultySum_;  }
   bool                isMainBranch(void) const     { return isMainBranch_;  }
   bool                isOrphan(void) const         { return isOrphan_;  }
   
   /////////////////////////////////////////////////////////////////////////////
   void setVersion(uint32_t i)        { version_ = i;                    }
   void setPrevHash(BinaryData str)   { prevHash_.copyFrom(str);         }
   void setMerkleRoot(BinaryData str) { merkleRoot_.copyFrom(str);       }
   void setTimestamp(uint32_t i)      { timestamp_ = i;                  }
   void setDiffBits(BinaryData val)   { diffBits_ = val;              }
   void setNonce(uint32_t i)          { nonce_ = i;                      }
   void setNextHash(BinaryData str)   { nextHash_.copyFrom(str);         }

   /////////////////////////////////////////////////////////////////////////////
   void serialize(BinaryWriter & bw)
   {
      bw.put_uint32_t  ( version_     );
      bw.put_BinaryData( prevHash_    );
      bw.put_BinaryData( merkleRoot_  );
      bw.put_uint32_t  ( timestamp_   );
      bw.put_BinaryData( diffBits_    );
      bw.put_uint32_t  ( nonce_       );
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData serialize(void)
   {
      BinaryWriter bw(HEADER_SIZE);
      serialize(bw);
      return bw.getData();
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * start, BinaryData const * suppliedHash=NULL)
   {
      version_ =     *(uint32_t*)( start +  0     );
      prevHash_.copyFrom         ( start +  4, 32 );
      merkleRoot_.copyFrom       ( start + 36, 32 );
      timestamp_ =   *(uint32_t*)( start + 68     );
      diffBits_.copyFrom         ( start + 72, 4  );
      nonce_ =       *(uint32_t*)( start + 76     );

      if(suppliedHash==NULL)
         BtcUtils::getHash256(start, HEADER_SIZE, thisHash_);
      else
         thisHash_.copyFrom(*suppliedHash);
      difficultyDbl_ = BtcUtils::convertDiffBitsToDouble( diffBits_.getRef() );
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryReader & br)
   {
      BinaryData str;
      br.get_BinaryData(str, HEADER_SIZE);
      unserialize(str);
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(string const & str)
   {
      BinaryDataRef bdr((uint8_t const *)str.c_str(), str.size());
      unserialize(bdr);
   } 

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryData const & str)
   {
      unserialize(str.getPtr());
   } 

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryDataRef const & str)
   {
      unserialize(str.getPtr());
   } 


   /////////////////////////////////////////////////////////////////////////////
   BlockHeader( uint8_t const * bhDataPtr, BinaryData* thisHash = NULL) :
      prevHash_(32),
      nextHash_(32),
      numTx_(-1),
      fileByteLoc_(0),  
      difficultyDbl_(-1.0),
      difficultySum_(-1.0),
      blockHeight_(0),
      isMainBranch_(false),
      isOrphan_(false),
      isFinishedCalc_(false)
   {
      unserialize(bhDataPtr, thisHash);
   }

   /////////////////////////////////////////////////////////////////////////////
   BlockHeader(BinaryData const & header80B)
   {
      unserialize(header80B);
   }

   /////////////////////////////////////////////////////////////////////////////
   BlockHeader( BinaryData const * serHeader = NULL,
                BinaryData const * suppliedHash  = NULL,
                uint64_t           fileLoc   = UINT64_MAX) :
      prevHash_(32),
      thisHash_(32),
      nextHash_(32),
      numTx_(-1),
      fileByteLoc_(fileLoc),  
      difficultyDbl_(-1.0),
      difficultySum_(-1.0),
      blockHeight_(0),
      isMainBranch_(false),
      isOrphan_(false),
      isFinishedCalc_(false),
      isOnDiskYet_(false)
   {
      if(serHeader != NULL)
      {
         unserialize(*serHeader);
         if( suppliedHash != NULL )
            thisHash_.copyFrom(*suppliedHash);
         else
            BtcUtils::getHash256(*serHeader, thisHash_);
      }
   }



   /////////////////////////////////////////////////////////////////////////////
   void printHeader(ostream & os=cout)
   {
      os << "Block Information: " << blockHeight_ << endl;
      os << "-Hash:       " << thisHash_.toHex().c_str() << endl;
      os << "-Timestamp:  " << getTimestamp() << endl;
      os << "-Prev Hash:  " << prevHash_.toHex().c_str() << endl;
      os << "-MerkleRoot: " << getMerkleRoot().toHex().c_str() << endl;
      os << "-Difficulty: " << (difficultyDbl_)
                            << "    (" << getDiffBits().toHex().c_str() << ")" << endl;
      os << "-CumulDiff:  " << (difficultySum_) << endl;
      os << "-Nonce:      " << getNonce() << endl;
      os << "-FileOffset: " << fileByteLoc_ << endl;
   }


private:

   // All these pointers point to data managed by another class.
   // As such, it is unnecessary to deal with any memory mgmt. 

   // Some more data types to be stored with the header, but not
   // part of the official serialized header data, so these are
   // actual members of the BlockHeader.
   uint32_t       version_;
   BinaryData     prevHash_;
   BinaryData     merkleRoot_;
   uint32_t       timestamp_;
   BinaryData     diffBits_; 
   uint32_t       nonce_; 

   // Derived properties - we expect these to be set after construct/copy
   BinaryData     thisHash_;
   double         difficultyDbl_;

   // To be calculated later
   BinaryData     nextHash_;
   uint32_t       numTx_;
   uint32_t       blockHeight_;
   uint64_t       fileByteLoc_;
   double         difficultySum_;
   bool           isMainBranch_;
   bool           isOrphan_;
   bool           isFinishedCalc_;
   bool           isOnDiskYet_;

   vector<Tx*>    txPtrList_;

};



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// OutPoint is just a reference to a TxOut
class OutPoint
{
   friend class BlockDataManager_FullRAM;
   friend class OutPointRef;

public:
   OutPoint(void) : txHash_(32), txOutIndex_(UINT32_MAX) { }

   OutPoint(BinaryData const & txHash, uint32_t txOutIndex) : 
                txHash_(txHash), txOutIndex_(txOutIndex) { }

   OutPoint(uint8_t const * ptr) { unserialize(ptr); }
   BinaryData const & getTxHash(void) { return txHash_; }
   BinaryDataRef getTxHashRef(void)  { return BinaryDataRef(txHash_); }
   uint32_t getTxOutIndex(void) { return txOutIndex_; }
   void setTxHash(BinaryData const & hash) { txHash_.copyFrom(hash); }
   void setTxOutIndex(uint32_t idx) { txOutIndex_ = idx; }

   // Define these operators so that we can use OutPoint as a map<> key
   bool operator<(OutPoint const & op2) const
   {
      if(txHash_ == op2.txHash_)
         return txOutIndex_ < op2.txOutIndex_;
      else
         return txHash_ < op2.txHash_;
   }
   bool operator==(OutPoint const & op2) const
   {
      return (txHash_ == op2.txHash_ && txOutIndex_ == op2.txOutIndex_);
   }

   void serialize(BinaryWriter & bw)
   {
      bw.put_BinaryData(txHash_);
      bw.put_uint32_t(txOutIndex_);
   }

   BinaryData serialize(void)
   {
      BinaryWriter bw(36);
      serialize(bw);
      return bw.getData();
   }

   void unserialize(uint8_t const * ptr)
   {
      txHash_.copyFrom(ptr, 32);
      txOutIndex_ = *(uint32_t*)(ptr+32);
   }
   void unserialize(BinaryData const & bd) { unserialize(bd.getPtr()); }
   void unserialize(BinaryDataRef const & bdRef) { unserialize(bdRef.getPtr()); }
   void unserialize(BinaryReader & br)
   {
      br.get_BinaryData(txHash_, 32);
      txOutIndex_ = br.get_uint32_t();
   }
   void unserialize(BinaryRefReader & brr)
   {
      brr.get_BinaryData(txHash_, 32);
      txOutIndex_ = brr.get_uint32_t();
   }

private:
   BinaryData txHash_;
   uint32_t   txOutIndex_;

};



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// TxIn 
class TxIn
{
   friend class BlockDataManager_FullRAM;
   friend class TxInRef;

public:
   TxIn(void) :
      outPoint_(),
      binScript_(0),
      sequence_(0),
      scriptSize_(0),
      scriptType_(TXIN_SCRIPT_UNKNOWN)
   {
      // Nothing to put here
   }

   TxIn(OutPoint const & op,
        BinaryData const & script,
        uint32_t seq,
        bool coinbase) : 
      outPoint_(op),
      binScript_(script),
      sequence_(seq),
      scriptType_(TXIN_SCRIPT_UNKNOWN)
   {
      scriptSize_ = (uint32_t)(binScript_.getSize());
   }

   OutPoint const & getOutPoint(void) { return outPoint_; }
   BinaryData const & getBinScript(void) { return binScript_; }
   uint32_t getSequence(void) { return sequence_; }
   uint32_t getScriptSize(void) { return scriptSize_; }
   uint32_t getSize(void) { return nBytes_; }


   void setOutPoint(OutPoint const & op) { outPoint_ = op; }
   void setBinScript(BinaryData const & scr) { binScript_.copyFrom(scr); }
   void setSequence(uint32_t seq) { sequence_ = seq; }
   void setIsMine(bool ismine) { isMine_ = ismine; }


   void serialize(BinaryWriter & bw)
   {
      outPoint_.serialize(bw);
      bw.put_var_int(scriptSize_);
      bw.put_BinaryData(binScript_);
      bw.put_uint32_t(sequence_);
   }

   BinaryData serialize(void)
   {
      BinaryWriter bw(250);
      serialize(bw);
      return bw.getData();
   }

   void unserialize(uint8_t const * ptr)
   {
      outPoint_.unserialize(ptr);
      uint32_t viLen;
      scriptSize_ = (uint32_t)BtcUtils::readVarInt(ptr+36, &viLen);
      binScript_.copyFrom(ptr+36+viLen, scriptSize_);
      sequence_ = *(uint32_t*)(ptr+36+viLen+scriptSize_);

      // Derived values
      nBytes_ = 36+viLen+scriptSize_+4;
      scriptType_ = BtcUtils::getTxInScriptType(binScript_, outPoint_.getTxHash().getRef());
   }
   void unserialize(BinaryReader & br)
   {
      uint32_t posStart = br.getPosition();
      outPoint_.unserialize(br);
      scriptSize_ = (uint32_t)br.get_var_int();
      br.get_BinaryData(binScript_, scriptSize_);
      sequence_ = br.get_uint32_t();

      nBytes_ = br.getPosition() - posStart;
      scriptType_ = BtcUtils::getTxInScriptType(binScript_, outPoint_.getTxHash().getRef());
   }
   void unserialize(BinaryRefReader & brr)
   {
      uint32_t posStart = brr.getPosition();
      outPoint_.unserialize(brr);
      scriptSize_ = (uint32_t)brr.get_var_int();
      brr.get_BinaryData(binScript_, scriptSize_);
      sequence_ = brr.get_uint32_t();
      nBytes_ = brr.getPosition() - posStart;
      scriptType_ = BtcUtils::getTxInScriptType(binScript_, outPoint_.getTxHashRef());
   }

   void unserialize(BinaryData const & str)
   {
      unserialize(str.getPtr());
   }
   void unserialize(BinaryDataRef const & str)
   {
      unserialize(str.getPtr());
   }


private:
   OutPoint         outPoint_;
   uint32_t         scriptSize_;
   BinaryData       binScript_;
   uint32_t         sequence_;

   // Derived properties - we expect these to be set after construct/copy
   uint32_t         nBytes_;
   TXIN_SCRIPT_TYPE scriptType_;

   // To be calculated later
   bool             isMine_;

};


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// TxOut 
class TxOut
{
   friend class BlockDataManager_FullRAM;
   friend class TxOutRef;

public:
   /////////////////////////////////////////////////////////////////////////////
   TxOut(void) :
      value_(0),
      pkScript_(0),
      scriptSize_(0),
      scriptType_(TXOUT_SCRIPT_UNKNOWN),
      recipientBinAddr20_(0),
      isMine_(false),
      isSpent_(false)
   
   {
      // Nothing to put here
   }

   /////////////////////////////////////////////////////////////////////////////
   TxOut(uint64_t val, BinaryData const & scr) :
      value_(val),
      pkScript_(scr)
   {
      scriptSize_ = (uint32_t)(pkScript_.getSize());
   }

   uint64_t getValue(void) { return value_; }
   BinaryData const & getPkScript(void) { return pkScript_; }
   uint32_t getScriptSize(void) { return scriptSize_; }
   bool isStandard(void) { return scriptType_ != TXOUT_SCRIPT_UNKNOWN; }

   void setValue(uint64_t val) { value_ = val; }
   void setPkScript(BinaryData const & scr) { pkScript_.copyFrom(scr); }



   /////////////////////////////////////////////////////////////////////////////
   BinaryData const & getRecipientAddr(void) { return recipientBinAddr20_; }



   /////////////////////////////////////////////////////////////////////////////
   void serialize(BinaryWriter & bw)
   {
      bw.put_uint64_t(value_);
      bw.put_var_int(scriptSize_);
      bw.put_BinaryData(pkScript_);
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData serialize(void)
   {
      BinaryWriter bw(45);
      serialize(bw);
      return bw.getData();
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr)
   {
      value_ = *(uint64_t*)(ptr);
      uint32_t viLen;
      scriptSize_ = (uint32_t)BtcUtils::readVarInt(ptr+8, &viLen);
      pkScript_.copyFrom(ptr+8+viLen, scriptSize_);
      nBytes_ = 8 + viLen + scriptSize_;
      scriptType_ = BtcUtils::getTxOutScriptType(pkScript_.getRef());
      recipientBinAddr20_ = BtcUtils::getTxOutRecipientAddr(pkScript_, 
                                                            scriptType_);
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryReader & br)
   {
      unserialize(br.getCurrPtr());
      br.advance(nBytes_);
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryRefReader & brr)
   {
      unserialize(brr.getCurrPtr());
      brr.advance(nBytes_);
   }

   void unserialize(BinaryData    const & str) { unserialize(str.getPtr()); }
   void unserialize(BinaryDataRef const & str) { unserialize(str.getPtr()); }


private:
   uint64_t          value_;
   uint32_t          scriptSize_;
   BinaryData        pkScript_;

   // Derived properties - we expect these to be set after construct/copy
   uint32_t          nBytes_;
   TXOUT_SCRIPT_TYPE scriptType_;
   BinaryData        recipientBinAddr20_;

   // To be calculated later
   bool       isMine_;
   bool       isSpent_;

};





////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
class Tx
{
   friend class BlockDataManager_FullRAM;
   friend class TxRef;

public:
   Tx(void) :
      version_(0),
      numTxIn_(0),
      numTxOut_(0),
      txInList_(0),
      txOutList_(0),
      lockTime_(UINT32_MAX),
      thisHash_(32),
      headerPtr_(NULL),
      headerRefPtr_(NULL)
   {
      // Nothing to put here
   }

     
   /////////////////////////////////////////////////////////////////////////////
   OutPoint createOutPoint(int txOutIndex)
   {
      return OutPoint(thisHash_, txOutIndex);
   }


   /////////////////////////////////////////////////////////////////////////////
   void serialize(BinaryWriter & bw)
   {
      bw.put_uint32_t(version_);
      bw.put_var_int(numTxIn_);
      for(uint32_t i=0; i<numTxIn_; i++)
      {
         txInList_[i].serialize(bw);
      }
      bw.put_var_int(numTxOut_);
      for(uint32_t i=0; i<numTxOut_; i++)
      {
         txOutList_[i].serialize(bw);
      }
      bw.put_uint32_t(lockTime_);
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData serialize(void)
   {
      BinaryWriter bw(300);
      serialize(bw);
      return bw.getData();
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(uint8_t const * ptr)
   {
      // This would be too annoying to write in raw pointer-arithmatic
      // So I will just create a BinaryRefReader
      BinaryRefReader brr(ptr);
      unserialize(brr);
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryReader & br)
   {
      uint32_t posStart = br.getPosition();
      version_ = br.get_uint32_t();

      numTxIn_ = (uint32_t)br.get_var_int();
      txInList_ = vector<TxIn>(numTxIn_);
      for(uint32_t i=0; i<numTxIn_; i++)
         txInList_[i].unserialize(br); 

      numTxOut_ = (uint32_t)br.get_var_int();
      txOutList_ = vector<TxOut>(numTxOut_);
      for(uint32_t i=0; i<numTxOut_; i++)
         txOutList_[i].unserialize(br); 

      lockTime_ = br.get_uint32_t();
      nBytes_ = br.getPosition() - posStart;
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryRefReader & brr)
   {
      uint32_t posStart = brr.getPosition();
      version_ = brr.get_uint32_t();

      numTxIn_ = (uint32_t)brr.get_var_int();
      txInList_ = vector<TxIn>(numTxIn_);
      for(uint32_t i=0; i<numTxIn_; i++)
         txInList_[i].unserialize(brr); 

      numTxOut_ = (uint32_t)brr.get_var_int();
      txOutList_ = vector<TxOut>(numTxOut_);
      for(uint32_t i=0; i<numTxOut_; i++)
         txOutList_[i].unserialize(brr); 

      lockTime_ = brr.get_uint32_t();
      nBytes_ = brr.getPosition() - posStart;
   }

   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryData const & str)
   {
      unserialize(str.getPtr());
   }
   /////////////////////////////////////////////////////////////////////////////
   void unserialize(BinaryDataRef const & str)
   {
      unserialize(str.getPtr());
   }


private:
   uint32_t      version_;
   uint32_t      numTxIn_;
   uint32_t      numTxOut_;
   vector<TxIn>  txInList_;
   vector<TxOut> txOutList_;
   uint32_t      lockTime_;
   
   // Derived properties - we expect these to be set after construct/copy
   BinaryData    thisHash_;
   uint32_t      nBytes_;

   // To be calculated later
   BlockHeader*     headerPtr_;
   BlockHeaderRef*  headerRefPtr_;
};



#endif

