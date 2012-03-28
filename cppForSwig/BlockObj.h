////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2012, Alan C. Reiner    <alan.reiner@gmail.com>        //
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
   BinaryData serialize(void);
   void serialize(BinaryWriter & bw);
   void unserialize_1_(BinaryData const & bh) { unserialize(bh); }
   void unserialize(uint8_t const * start, BinaryData const * suppliedHash=NULL);
   void unserialize(BinaryReader & br);
   void unserialize(string const & str);
   void unserialize(BinaryData const & str);
   void unserialize(BinaryDataRef const & str);
   BlockHeader( uint8_t const * bhDataPtr, BinaryData* thisHash = NULL);
   BlockHeader(BinaryData const & header80B);
   BlockHeader( BinaryData const * serHeader = NULL,
                BinaryData const * suppliedHash  = NULL,
                uint64_t           fileLoc   = UINT64_MAX);

   void pprint(ostream & os=cout, int nIndent=0, bool pBigendian=true) const;
   uint32_t findNonce(void);

private:

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
   uint64_t       blkByteLoc_;
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
// TxIn 
class TxIn
{
   friend class BlockDataManager_FullRAM;
   friend class TxInRef;

public:
   TxIn(void);
   TxIn(OutPoint const & op, BinaryData const & script, uint32_t seq, bool coinbase); 

   OutPoint const & getOutPoint(void) { return outPoint_; }
   BinaryData const & getBinScript(void) { return binScript_; }
   uint32_t getSequence(void) { return sequence_; }
   uint32_t getScriptSize(void) { return scriptSize_; }
   uint32_t getSize(void) { return nBytes_; }


   void setOutPoint(OutPoint const & op) { outPoint_ = op; }
   void setBinScript(BinaryData const & scr) { binScript_.copyFrom(scr); }
   void setSequence(uint32_t seq) { sequence_ = seq; }
   void setIsMine(bool ismine) { isMine_ = ismine; }


   void serialize(BinaryWriter & bw);
   BinaryData serialize(void);
   void unserialize(uint8_t const * ptr);
   void unserialize(BinaryReader & br);
   void unserialize(BinaryRefReader & brr);
   void unserialize(BinaryData const & str);
   void unserialize(BinaryDataRef const & str);

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
   TxOut(void);

   /////////////////////////////////////////////////////////////////////////////
   TxOut(uint64_t val, BinaryData const & scr);

   uint64_t           getValue(void) { return value_; }
   BinaryData const & getPkScript(void) { return pkScript_; }
   uint32_t           getScriptSize(void) { return scriptSize_; }
   bool               isStandard(void) { return scriptType_ != TXOUT_SCRIPT_UNKNOWN; }
   BinaryData const & getRecipientAddr(void) { return recipientBinAddr20_; }

   void               setValue(uint64_t val) { value_ = val; }
   void               setPkScript(BinaryData const & scr) { pkScript_.copyFrom(scr); }

   void               serialize(BinaryWriter & bw);
   BinaryData         serialize(void);
   void               unserialize(uint8_t const * ptr);
   void               unserialize(BinaryReader & br);
   void               unserialize(BinaryRefReader & brr);
   void               unserialize(BinaryData    const & str) ;
   void               unserialize(BinaryDataRef const & str);


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
   Tx(void);

   uint32_t          getVersion_(void)  { return version_;   }
   uint32_t          getNumTxIn_(void)  { return numTxIn_;   }
   uint32_t          getNumTxOut_(void) { return numTxOut_;  }
   vector<TxIn>      getTxInList_(void) { return txInList_;  }
   vector<TxOut>     getTxOutList_(void){ return txOutList_; }
   uint32_t          getLockTime_(void) { return lockTime_;  }
   uint32_t          getNumBytes(void)  { return nBytes_;  }

   // We expect one of these two to be set so that we can get header info
   BlockHeader*      getHeaderPtr(void)    { return headerPtr_;    }
   BlockHeaderRef*   getHeaderRefPtr(void) { return headerRefPtr_; }
   

     
   /////////////////////////////////////////////////////////////////////////////
   OutPoint createOutPoint(int txOutIndex);
   void serialize(BinaryWriter & bw);
   BinaryData serialize(void);
   void unserialize(uint8_t const * ptr);
   void unserialize(BinaryReader & br);
   void unserialize(BinaryRefReader & brr);
   void unserialize(BinaryData const & str);
   void unserialize(BinaryDataRef const & str);


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




////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
// This class is mainly for sorting by priority
class UnspentTxOut
{
public:
   UnspentTxOut(void);
   UnspentTxOut(TxOutRef & txout, uint32_t blknum) { init(txout, blknum);}

   void init(TxOutRef & txout, uint32_t blknum);

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

