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

using namespace std;

////
class TxMakerError : public runtime_error
{
public:
   TxMakerError(const string& err) :
      runtime_error(err)
   {}
};

////
enum SpendScriptType
{
   SST_P2PKH,
   SST_P2SH,
   SST_P2WPKH,
   SST_NESTED_P2WPKH,
   SST_P2WSH,
   SST_NESTED_P2WSH
};

////////////////////////////////////////////////////////////////////////////////
class ScriptSpender
{
private:
   bool isP2SH_ = false;
   bool isSegWit_ = false;

   bool isCSV_ = false;
   bool isCLTV_ = false;

   const UTXO utxo_;
   BinaryDataRef p2shScript_;
   unsigned sequence_ = UINT32_MAX;
   SIGHASH_TYPE sigHashType_ = SIGHASH_ALL;

   mutable BinaryData outpoint_;

   //
   shared_ptr<ResolverFeed> resolverFeed_;
   BinaryData serializedScript_;
   mutable BinaryData serializedInput_;
   BinaryData witnessData_;
   bool resolved_ = false;

private:
   static BinaryData serializeScript(
      const vector<shared_ptr<StackItem>>& stack);

   static BinaryData serializeWitnessData(
      const vector<shared_ptr<StackItem>>& stack);

public:
   ScriptSpender(const UTXO& utxo, shared_ptr<ResolverFeed> feed) :
      utxo_(utxo), resolverFeed_(feed)
   {}

   bool isSegWit(void) const { return false; }

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
   BinaryDataRef getOutputHash(void) const { return utxo_.getTxHash().getRef(); }
   unsigned getOutputIndex(void) const { return utxo_.getTxOutIndex(); }
   BinaryDataRef getSerializedInput(void) const;
   BinaryDataRef getWitnessData(void) const { return witnessData_.getRef(); }
   BinaryDataRef getOutpoint(void) const;
   uint64_t getValue(void) const { return utxo_.getValue(); }
   shared_ptr<ResolverFeed> getFeed(void) const { return resolverFeed_; }
   const UTXO& getUtxo(void) const { return utxo_; }

   unsigned getFlags(void) const
   {
      unsigned flags = 0;
      if (isP2SH_)
         flags |= SCRIPT_VERIFY_P2SH;

      if (isSegWit_)
         flags |= SCRIPT_VERIFY_SEGWIT | SCRIPT_VERIFY_P2SH_SHA256;

      if (isCSV_)
         flags |= SCRIPT_VERIFY_CHECKSEQUENCEVERIFY;

      if (isCLTV_)
         flags |= SCRIPT_VERIFY_CHECKLOCKTIMEVERIFY;

      return flags;
   }

   uint8_t getSigHashByte(void) const
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
};

////////////////////////////////////////////////////////////////////////////////
class ScriptRecipient
{
protected:
   const SpendScriptType type_;
   const uint64_t value_ = UINT64_MAX;

   BinaryData script_;

public:
   //tors
   ScriptRecipient(SpendScriptType sst, uint64_t value) :
      type_(sst), value_(value)
   {}

   //virtuals
   virtual const BinaryData& getSerializedScript(void)
   {
      if (script_.getSize() == 0)
         serialize();

      return script_;
   }
   
   virtual ~ScriptRecipient(void) = 0;
   virtual void serialize(void) = 0;
};

////////////////////////////////////////////////////////////////////////////////
class Recipient_P2PKH : public ScriptRecipient
{
private:
   const BinaryData h160_;

public:
   Recipient_P2PKH(const BinaryData& h160, uint64_t val) :
      ScriptRecipient(SST_P2PKH, val), h160_(h160)
   {
      if (h160_.getSize() != 20)
         throw TxMakerError("a160 is not 20 bytes long!");
   }
   
   void serialize(void)
   {
      BinaryWriter bw;
      bw.put_uint64_t(value_);
      bw.put_uint8_t(25);
      bw.put_uint8_t(OP_DUP);
      bw.put_uint8_t(OP_HASH160);
      bw.put_uint8_t(20);
      bw.put_BinaryData(h160_);
      bw.put_uint8_t(OP_EQUALVERIFY);
      bw.put_uint8_t(OP_CHECKSIG);

      script_ = move(bw.getData());
   }
};

////////////////////////////////////////////////////////////////////////////////
class Recipient_P2WPKH : public ScriptRecipient
{
private:
   const BinaryData h160_;

public:
   Recipient_P2WPKH(const BinaryData& h160, uint64_t val) :
      ScriptRecipient(SST_P2WPKH, val), h160_(h160)
   {
      if (h160_.getSize() != 20)
         throw TxMakerError("a160 is not 20 bytes long!");
   }

   void serialize(void)
   {
      BinaryWriter bw;
      bw.put_uint64_t(value_);
      bw.put_uint8_t(22);
      bw.put_uint8_t(0);
      bw.put_uint8_t(20);
      bw.put_BinaryData(h160_);

      script_ = move(bw.getData());
   }
};

////////////////////////////////////////////////////////////////////////////////
class Recipient_P2SH : public ScriptRecipient
{
private:
   const BinaryData h160_;

public:
   Recipient_P2SH(const BinaryData& h160, uint64_t val) :
      ScriptRecipient(SST_P2SH, val), h160_(h160)
   {
      if (h160_.getSize() != 20)
         throw TxMakerError("a160 is not 20 bytes long!");
   }

   void serialize(void)
   {
      BinaryWriter bw;
      bw.put_uint64_t(value_);
      bw.put_uint8_t(23);
      bw.put_uint8_t(OP_HASH160);
      bw.put_uint8_t(20);
      bw.put_BinaryData(h160_);
      bw.put_uint8_t(OP_EQUAL);

      script_ = move(bw.getData());
   }
};

////////////////////////////////////////////////////////////////////////////////
class Recipient_PW2SH : public ScriptRecipient
{
private:
   const BinaryData h256_;

public:
   Recipient_PW2SH(const BinaryData& h256, uint64_t val) :
      ScriptRecipient(SST_P2WSH, val), h256_(h256)
   {
      if (h256_.getSize() != 32)
         throw TxMakerError("a256 is not 32 bytes long!");
   }

   void serialize(void)
   {
      BinaryWriter bw;
      bw.put_uint64_t(value_);
      bw.put_uint8_t(34);
      bw.put_uint8_t(0);
      bw.put_uint8_t(32);
      bw.put_BinaryData(h256_);

      script_ = move(bw.getData());
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

   mutable bool isSegWit_ = false;

protected:
   shared_ptr<SigHashData> getSigHashDataForSpender(unsigned, bool) const;
   SecureBinaryData sign(
      BinaryDataRef script,
      const SecureBinaryData& privKey, 
      shared_ptr<SigHashData>,
      unsigned index);

public:
   void addSpender(shared_ptr<ScriptSpender> spender) 
   { spenders_.push_back(spender); }
   
   void addRecipient(shared_ptr<ScriptRecipient> recipient) 
   { recipients_.push_back(recipient); }

   void sign(void);
   BinaryDataRef serialize(void) const;
   bool verify(void);

   ////
   BinaryDataRef getSerializedOutputScripts(void) const;
   vector<TxInData> getTxInsData(void) const;
   BinaryData getSubScript(unsigned index) const;
   BinaryDataRef getWitnessData(unsigned inputId) const;

   uint32_t getVersion(void) const { return version_; }
   uint32_t getTxOutCount(void) const { return recipients_.size(); }
   uint32_t getLockTime(void) const { return lockTime_; }
   shared_ptr<ScriptSpender> getSpender(unsigned) const;

   //sw methods
   BinaryData serializeAllOutpoints(void) const;
   BinaryData serializeAllSequences(void) const;
   BinaryDataRef getOutpoint(unsigned) const;
   uint64_t getOutpointValue(unsigned) const;
   unsigned getTxInSequence(unsigned) const;
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
public:
   SignerProxyFromSigner(Signer* signer, 
      unsigned index);
};

#endif

