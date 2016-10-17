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
class TxMakerError : public exception
{
public:
   TxMakerError(const char* err) :
      exception(err)
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
   bool signed_ = false;

   const SpendScriptType type_;
   const UTXO utxo_;
   unsigned sequence_ = UINT32_MAX;
   SIGHASH_TYPE sigHashType_ = SIGHASH_ALL;

   mutable BinaryData outpoint_;
   BinaryData witness_;

   //
   vector<BinaryData> stackItems_;
   SecureBinaryData signature_;
   shared_ptr<ResolverFeed> resolverFeed_;

private:
   virtual void serialize(void) const = 0;

public:
   ScriptSpender(SpendScriptType sst, const UTXO& utxo,
      shared_ptr<ResolverFeed> feed) :
      type_(sst), utxo_(utxo), resolverFeed_(feed)
   {}

   bool isSegWit(void) const { return false; }

   //set
   void setSigHashType(SIGHASH_TYPE sht) { sigHashType_ = sht; }
   void setSignature(SecureBinaryData& sig) { signature_ = move(sig); }
   void setSequence(unsigned s) { sequence_ = s; }
   void setStack(vector<BinaryData> stack) { stackItems_ = move(stack); }

   //get
   SIGHASH_TYPE getSigHashType(void) const { return sigHashType_; }
   unsigned getSequence(void) const { return sequence_; }
   BinaryDataRef getOutputScript(void) const;
   BinaryDataRef getOutputHash(void) const { return utxo_.getTxHash().getRef(); }
   unsigned getOutputIndex(void) const { return utxo_.getTxOutIndex(); }
   BinaryDataRef getWitnessData(void) const { return witness_.getRef(); }
   BinaryDataRef getOutpoint(void) const;
   uint64_t getValue(void) const { return utxo_.getValue(); }
   shared_ptr<ResolverFeed> getFeed(void) const { return resolverFeed_; }

   BinaryDataRef getSerializedScript(void) const;
};

////////////////////////////////////////////////////////////////////////////////
class ScriptRecipient
{
protected:
   const SpendScriptType type_;
   const uint64_t value_ = UINT64_MAX;

   BinaryData script_;

private:
   virtual void serialize(void) = 0;

public:
   ScriptRecipient(SpendScriptType sst, uint64_t value) :
      type_(sst), value_(value)
   {}

   virtual const BinaryData& getSerializedScript(void)
   {
      if (script_.getSize() == 0)
         serialize();

      return script_;
   }
};

////////////////////////////////////////////////////////////////////////////////
class Recipient_P2PKH : public ScriptRecipient
{
   const BinaryData address160_;
public:
   Recipient_P2PKH(BinaryData& a160, uint64_t val) :
      ScriptRecipient(SST_P2PKH, val), address160_(a160)
   {
      if (address160_.getSize() != 20)
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
      bw.put_BinaryData(address160_);
      bw.put_uint8_t(OP_EQUALVERIFY);
      bw.put_uint8_t(OP_CHECKSIG);

      script_ = move(bw.getData());
   }
};

////////////////////////////////////////////////////////////////////////////////
class Signer : public TransactionStub
{
protected:
   unsigned version_ = 1;
   unsigned lockTime_ = 0;

   mutable BinaryData serializedTx_;
   mutable BinaryData serializedOutputs_;

   vector<shared_ptr<ScriptSpender>> spenders_;
   vector<shared_ptr<ScriptRecipient>> recipients_;

   mutable bool isSegWit_ = false;

protected:

public:
  
   void addSpender(shared_ptr<ScriptSpender>);
   void addRecipient(shared_ptr<ScriptRecipient>);

   virtual void sign(void);
   virtual BinaryDataRef serialize(void) const;
   virtual bool verify(void);

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
   
   SecureBinaryData sign(const SecureBinaryData& privKey, shared_ptr<SigHashData>,
      unsigned index);

   shared_ptr<SigHashData> getSigHashDataForSpender(unsigned) const;
};

////////////////////////////////////////////////////////////////////////////////
class SignerProxy
{
protected:
   function<SecureBinaryData(const BinaryData&)> signerLambda_;

public:
   virtual ~SignerProxy(void) = 0;

   SecureBinaryData sign(const BinaryData& bd)
   {
      return move(signerLambda_(bd));
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

