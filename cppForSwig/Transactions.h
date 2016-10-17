////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_TRANSACTIONS_
#define _H_TRANSACTIONS_

#include <map>
#include <vector>

#include "BinaryData.h"
#include "EncryptionUtils.h"
#include "BtcUtils.h"
#include "BlockDataMap.h"
#include "Script.h"

enum SIGHASH_TYPE
{
   SIGHASH_ALL = 1
};

class UnsupportedSigHashTypeException : public exception
{
public:
   UnsupportedSigHashTypeException(const char* what) : exception(what)
   {}
};

////////////////////////////////////////////////////////////////////////////////
struct TxInData
{
   BinaryDataRef outputHash_;
   uint32_t outputIndex_;
   uint32_t sequence_;
};
 
////////////////////////////////////////////////////////////////////////////////
class TransactionStub
{
protected:
   unsigned flags_;
   mutable shared_ptr<SigHashDataSegWit> sigHashDataObject_ = nullptr;

public:
   mutable map<unsigned, size_t> lastCodeSeparatorMap_;

public:
   TransactionStub(void)
   {}

   virtual ~TransactionStub(void) = 0;

   virtual BinaryDataRef getSerializedOutputScripts(void) const = 0;
   virtual vector<TxInData> getTxInsData(void) const = 0;
   virtual BinaryData getSubScript(unsigned index) const = 0;
   virtual BinaryDataRef getWitnessData(unsigned inputId) const = 0;

   virtual uint32_t getVersion(void) const = 0;
   virtual uint32_t getTxOutCount(void) const = 0;
   virtual uint32_t getLockTime(void) const = 0;

   //sw methods
   virtual BinaryData serializeAllOutpoints(void) const = 0;
   virtual BinaryData serializeAllSequences(void) const = 0;
   virtual BinaryDataRef getOutpoint(unsigned) const = 0;
   virtual uint64_t getOutpointValue(unsigned) const = 0;
   virtual unsigned getTxInSequence(unsigned) const = 0;

   //flags
   unsigned getFlags(void) const { return flags_; }
   void setFlags(unsigned flags) { flags_ = flags; }

   //op_cs
   void setLastOpCodeSeparator(unsigned index, size_t offset) const
   {
      lastCodeSeparatorMap_[index] = offset;
   }

   unsigned getLastCodeSeparatorOffset(unsigned index) const
   {
      auto csIter = lastCodeSeparatorMap_.find(index);
      if (csIter == lastCodeSeparatorMap_.end())
         return 0;

      return csIter->second;
   }
};

////////////////////////////////////////////////////////////////////////////////
class SigHashData
{
   //this class and its children do not return the sighash, rather the data that
   //will yield the hash
private:
   virtual BinaryData getDataForSigHashAll(const TransactionStub&,
      BinaryDataRef, unsigned) = 0;

public:
   BinaryData getDataForSigHash(SIGHASH_TYPE, const TransactionStub&,
      BinaryDataRef outputScript, unsigned inputIndex);
   
   vector<BinaryDataRef> tokenize(const BinaryData&, uint8_t);
};

////////////////////////////////////////////////////////////////////////////////
class SigHashDataLegacy : public SigHashData
{
private:
   BinaryData getDataForSigHashAll(const TransactionStub&,
      BinaryDataRef, unsigned);
};

////////////////////////////////////////////////////////////////////////////////
class SigHashDataSegWit : public SigHashData
{
private:
   bool initialized_ = false;
   BinaryData hashPrevouts_;
   BinaryData hashSequence_;
   BinaryData hashOutputs_;

private:
   BinaryData getDataForSigHashAll(const TransactionStub&,
      BinaryDataRef, unsigned);

   void computePreState(const TransactionStub&);
};

////////////////////////////////////////////////////////////////////////////////
class TransactionVerifier : public TransactionStub
{
public:
   typedef map<BinaryData, map<unsigned, UTXO>> utxoMap;

private:
   const BCTX theTx_;
   utxoMap utxos_;

private:
   uint64_t checkOutputs(void) const;
   bool checkSigs(void) const;
   bool checkSig(unsigned) const;

public:
   TransactionVerifier(const BCTX& theTx, const utxoMap& utxos) :
      utxos_(utxos), theTx_(theTx)
   {}
   
   bool verify(void) const;

   BinaryDataRef getSerializedOutputScripts(void) const;
   vector<TxInData> getTxInsData(void) const;
   BinaryData getSubScript(unsigned index) const;
   BinaryDataRef getWitnessData(unsigned inputId) const;

   uint32_t getVersion(void) const { return theTx_.version_; }
   uint32_t getTxOutCount(void) const { return theTx_.txouts_.size(); }
   uint32_t getLockTime(void) const { return theTx_.lockTime_; }

   //sw
   BinaryData serializeAllOutpoints(void) const;
   BinaryData serializeAllSequences(void) const;
   BinaryDataRef getOutpoint(unsigned) const;
   uint64_t getOutpointValue(unsigned) const;
   unsigned getTxInSequence(unsigned) const;
};


#endif