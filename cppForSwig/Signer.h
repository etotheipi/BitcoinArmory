////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_SIGNER
#define _H_SIGNER

#include <set>

#include "EncryptionUtils.h"
#include "TxClasses.h"
#include "Transactions.h"
#include "ScriptRecipient.h"
#include "TxEvalState.h"

using namespace std;

enum SpenderStatus
{
   SpenderStatus_Unkonwn,
   SpenderStatus_Partial,
   SpenderStatus_Resolved
};

#define SERIALIZED_SCRIPT_PREFIX 0x01
#define WITNESS_SCRIPT_PREFIX    0x02

#define LEGACY_STACK_PARTIAL    0x03
#define WITNESS_STACK_PARTIAL   0x04

#define PREFIX_UTXO        0x05
#define PREFIX_OUTPOINT    0x06

////////////////////////////////////////////////////////////////////////////////
class ScriptSpender
{
private:
   SpenderStatus legacyStatus_ = SpenderStatus_Unkonwn;
   SpenderStatus segwitStatus_ = SpenderStatus_Unkonwn;

   bool isP2SH_ = false;

   bool isCSV_ = false;
   bool isCLTV_ = false;

   UTXO utxo_;
   const uint64_t value_ = UINT64_MAX;
   BinaryDataRef p2shScript_;
   unsigned sequence_ = UINT32_MAX;
   mutable BinaryData outpoint_;

   //
   shared_ptr<ResolverFeed> resolverFeed_;
   vector<BinaryData> sigVec_;
   BinaryData serializedScript_;
   mutable BinaryData serializedInput_;
   BinaryData witnessData_;

   map<unsigned, shared_ptr<StackItem>> partialStack_;
   map<unsigned, shared_ptr<StackItem>> partialWitnessStack_;

protected:
   SIGHASH_TYPE sigHashType_ = SIGHASH_ALL;

private:
   static BinaryData serializeScript(
      const vector<shared_ptr<StackItem>>& stack, bool no_throw=false);
   static BinaryData serializeWitnessData(
      const vector<shared_ptr<StackItem>>& stack, 
      unsigned& itemCount, bool no_throw=false);

   void updateStack(map<unsigned, shared_ptr<StackItem>>&,
      const vector<shared_ptr<StackItem>>&);

   BinaryData getSerializedOutpoint(void) const;

public:
   ScriptSpender(
      const BinaryDataRef txHash, unsigned index, uint64_t value) :
      value_(value)
   {
      BinaryWriter bw;
      bw.put_BinaryDataRef(txHash);
      bw.put_uint32_t(index);

      outpoint_ = bw.getData();
   }

   ScriptSpender(const UTXO& utxo) :
      utxo_(utxo), value_(utxo.getValue())
   {}

   ScriptSpender(const UTXO& utxo, shared_ptr<ResolverFeed> feed) :
      utxo_(utxo), value_(utxo.getValue()), resolverFeed_(feed)
   {}

   bool isSegWit(void) const { return segwitStatus_ != SpenderStatus_Unkonwn; }
   bool isP2SH(void) const { return isP2SH_; }

   //set
   void setSigHashType(SIGHASH_TYPE sht) { sigHashType_ = sht; }
   void setSequence(unsigned s) { sequence_ = s; }
   void setStack(const vector<shared_ptr<StackItem>>& stack);
   void setWitnessData(const vector<shared_ptr<StackItem>>& stack);
   void flagP2SH(bool flag) { isP2SH_ = flag; }

   //get
   SIGHASH_TYPE getSigHashType(void) const { return sigHashType_; }
   unsigned getSequence(void) const { return sequence_; }
   BinaryDataRef getOutputScript(void) const;
   BinaryDataRef getOutputHash(void) const;
   unsigned getOutputIndex(void) const;
   BinaryDataRef getSerializedInput(void) const;
   BinaryData serializeAvailableStack(void) const;
   BinaryDataRef getWitnessData(void) const;
   BinaryData serializeAvailableWitnessData(void) const;
   BinaryDataRef getOutpoint(void) const;
   uint64_t getValue(void) const { return value_; }
   shared_ptr<ResolverFeed> getFeed(void) const { return resolverFeed_; }
   const UTXO& getUtxo(void) const { return utxo_; }
   void setUtxo(const UTXO& utxo) { utxo_ = utxo; }

   const BinaryData& getSingleSig(void) const;

   unsigned getFlags(void) const
   {
      unsigned flags = 0;
      if (isP2SH_)
         flags |= SCRIPT_VERIFY_P2SH;

      if (isSegWit())
         flags |= SCRIPT_VERIFY_SEGWIT | SCRIPT_VERIFY_P2SH_SHA256;

      if (isCSV_)
         flags |= SCRIPT_VERIFY_CHECKSEQUENCEVERIFY;

      if (isCLTV_)
         flags |= SCRIPT_VERIFY_CHECKLOCKTIMEVERIFY;

      return flags;
   }

   virtual uint8_t getSigHashByte(void) const
   {
      uint8_t hashbyte;
      switch (sigHashType_)
      {
      case SIGHASH_ALL:
         hashbyte = 1;
         break;

      default:
         throw ScriptException("unsupported sighash type");
      }

      return hashbyte;
   }

   void updatePartialStack(const vector<shared_ptr<StackItem>>& stack)
   {
      if (legacyStatus_ == SpenderStatus_Resolved)
         return;

      updateStack(partialStack_, stack);
      legacyStatus_ = SpenderStatus_Partial;
   }

   void updatePartialWitnessStack(const vector<shared_ptr<StackItem>>& stack)
   {
      if (segwitStatus_ == SpenderStatus_Resolved)
         return;

      updateStack(partialWitnessStack_, stack);
      segwitStatus_ = SpenderStatus_Partial;
   }
   
   void evaluatePartialStacks(void);
   bool resolved(void) const;
   bool isPartial(void) const;

   BinaryData serializeState(void) const;
   static shared_ptr<ScriptSpender> deserializeState(
      const BinaryDataRef&);

   void merge(const ScriptSpender&);
   bool hasUTXO(void) const { return utxo_.isInitialized(); }

   bool hasFeed(void) const { return resolverFeed_ != nullptr; }
   void setFeed(shared_ptr<ResolverFeed> feedPtr) { resolverFeed_ = feedPtr; }

   bool operator==(const ScriptSpender& rhs)
   {
      return this->getOutpoint() == rhs.getOutpoint();
   }
};

////////////////////////////////////////////////////////////////////////////////
class ScriptSpender_BCH : public ScriptSpender
{
public:
   ScriptSpender_BCH(
      const BinaryDataRef txHash, unsigned index, uint64_t value) :
      ScriptSpender(txHash, index, value)
   {}

   ScriptSpender_BCH(const UTXO& utxo) :
      ScriptSpender(utxo)
   {}

   ScriptSpender_BCH(const UTXO& utxo, shared_ptr<ResolverFeed> feed) :
      ScriptSpender(utxo, feed)
   {}

   ScriptSpender_BCH(const ScriptSpender& scriptSpender) :
      ScriptSpender(scriptSpender)
   {}

   virtual uint8_t getSigHashByte(void) const
   {
      uint8_t hashbyte;
      switch (sigHashType_)
      {
      case SIGHASH_ALL:
         hashbyte = 0x40 | 1;
         break;

      default:
         throw ScriptException("unsupported sighash type");
      }

      return hashbyte;
   }
};

////////////////////////////////////////////////////////////////////////////////
class Signer : public TransactionStub
{
   friend class SignerProxyFromSigner;

protected:
   unsigned version_ = 1;
   unsigned lockTime_ = 0;

   mutable BinaryData serializedTx_;
   mutable BinaryData serializedOutputs_;

   vector<shared_ptr<ScriptSpender>> spenders_;
   vector<shared_ptr<ScriptRecipient>> recipients_;

   shared_ptr<ResolverFeed> resolverPtr_;

   mutable bool isSegWit_ = false;

protected:
   virtual shared_ptr<SigHashData> getSigHashDataForSpender(bool) const;
   SecureBinaryData sign(
      BinaryDataRef script,
      const SecureBinaryData& privKey, 
      shared_ptr<SigHashData>,
      unsigned index);

   virtual unique_ptr<TransactionVerifier> getVerifier(shared_ptr<BCTX>,
      map<BinaryData, map<unsigned, UTXO>>&) const;

   void evaluateSpenderStatus(void);
   BinaryData serializeAvailableResolvedData(void) const;
   TxEvalState verify(const BinaryData& rawTx, 
      map<BinaryData, map<unsigned, UTXO>>&, unsigned flags) const;

   virtual shared_ptr<ScriptSpender> convertSpender(shared_ptr<ScriptSpender>) const;

public:
   void addSpender(shared_ptr<ScriptSpender> spender) 
   { spenders_.push_back(spender); }

   virtual void addSpender_ByOutpoint(
      const BinaryData& hash, unsigned index, unsigned sequence, uint64_t value);
   
   void addRecipient(shared_ptr<ScriptRecipient> recipient) 
   { recipients_.push_back(recipient); }

   void sign(void);
   BinaryDataRef serialize(void) const;
   
   bool verify(void);
   bool verifyRawTx(const BinaryData& rawTx,
      const map<BinaryData, map<unsigned, BinaryData> >& rawUTXOs);

   ////
   BinaryDataRef getSerializedOutputScripts(void) const;
   vector<TxInData> getTxInsData(void) const;
   BinaryData getSubScript(unsigned index) const;
   BinaryDataRef getWitnessData(unsigned inputId) const;
   bool isInputSW(unsigned inputId) const;

   uint32_t getVersion(void) const { return version_; }
   uint32_t getTxOutCount(void) const { return recipients_.size(); }
   shared_ptr<ScriptSpender> getSpender(unsigned) const;

   uint32_t getLockTime(void) const { return lockTime_; }
   void setLockTime(unsigned locktime) { lockTime_ = locktime; }
   void setVersion(unsigned version) { version_ = version; }

   //sw methods
   BinaryData serializeAllOutpoints(void) const;
   BinaryData serializeAllSequences(void) const;
   BinaryDataRef getOutpoint(unsigned) const;
   uint64_t getOutpointValue(unsigned) const;
   unsigned getTxInSequence(unsigned) const;
   const BinaryData& getSigForInputIndex(unsigned) const;

   BinaryData serializeState(void) const;
   void deserializeState(const BinaryData&);
   bool isValid(void) const;
   
   void setFeed(shared_ptr<ResolverFeed> feedPtr) { resolverPtr_ = feedPtr; }
   void populateUtxo(const UTXO& utxo);

   static Signer createFromState(const BinaryData&);

   BinaryData getTxId(void);

   TxEvalState evaluateSignedState(void)
   {
      evaluateSpenderStatus();
      auto&& txdata = serializeAvailableResolvedData();

      map<BinaryData, map<unsigned, UTXO>> utxoMap;
      unsigned flags = 0;
      for (auto& spender : spenders_)
      {
         auto& indexMap = utxoMap[spender->getOutputHash()];
         indexMap[spender->getOutputIndex()] = spender->getUtxo();

         flags |= spender->getFlags();
      }

      return verify(txdata, utxoMap, flags);
   }
};

////////////////////////////////////////////////////////////////////////////////
class Signer_BCH : public Signer
{
protected:
   shared_ptr<SigHashData> getSigHashDataForSpender(bool) const;
   unique_ptr<TransactionVerifier> getVerifier(shared_ptr<BCTX>,
      map<BinaryData, map<unsigned, UTXO>>&) const;
   shared_ptr<ScriptSpender> convertSpender(shared_ptr<ScriptSpender>) const;

public:
   void addSpender_ByOutpoint(
      const BinaryData& hash, unsigned index, unsigned sequence, uint64_t value);
};

////////////////////////////////////////////////////////////////////////////////
class SignerProxy
{
protected:
   function<SecureBinaryData(
      BinaryDataRef, const BinaryData&, bool)> signerLambda_;

public:
   virtual ~SignerProxy(void) = 0;

   SecureBinaryData sign(
      BinaryDataRef script,
      const BinaryData& pubkey,
      bool sw)
   {
      return move(signerLambda_(script, pubkey, sw));
   }
};

////
class SignerProxyFromSigner : public SignerProxy
{
private:
   void setLambda(Signer*, shared_ptr<ScriptSpender>, unsigned index,
      shared_ptr<ResolverFeed>);

public:
   SignerProxyFromSigner(Signer* signer,
      unsigned index)
   {
      auto spender = signer->getSpender(index);
      setLambda(signer, spender, index, spender->getFeed());
   }

   SignerProxyFromSigner(Signer* signer,
      unsigned index, shared_ptr<ResolverFeed> feedPtr)
   {
      auto spender = signer->getSpender(index);
      setLambda(signer, spender, index, feedPtr);
   }
};

#endif

