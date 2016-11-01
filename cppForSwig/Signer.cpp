////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "Signer.h"
#include "Script.h"
#include "Transactions.h"

ScriptRecipient::~ScriptRecipient() 
{}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// ScriptSpender
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BinaryDataRef ScriptSpender::getOutputScript(void) const
{
   return utxo_.getScript();
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef ScriptSpender::getOutpoint() const
{
   if (outpoint_.getSize() == 0)
   {
      BinaryWriter bw;
      bw.put_BinaryDataRef(getOutputHash());
      bw.put_uint32_t(getOutputIndex());

      outpoint_ = move(bw.getData());
   }

   return outpoint_.getRef();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData ScriptSpender::getSerializedScript(
   const vector<BinaryData>& stack) const
{
   BinaryWriter stackItems;
   for (auto& stackItem : stack)
   {
      stackItems.put_BinaryData(BtcUtils::getPushDataHeader(stackItem));
      stackItems.put_BinaryData(stackItem);
   }

   return stackItems.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef ScriptSpender::getSerializedInput() const
{
   if (!resolved_)
      throw ScriptException("unresolved spender");
   
   BinaryWriter bw;
   bw.put_BinaryData(utxo_.getTxHash());
   bw.put_uint32_t(utxo_.getTxOutIndex());


   bw.put_var_int(serializedScript_.getSize());
   bw.put_BinaryData(serializedScript_);
   bw.put_uint32_t(sequence_);

   serializedInput_ = move(bw.getData());
   return serializedInput_.getRef();
}

////////////////////////////////////////////////////////////////////////////////
void ScriptSpender::setStack(const vector<BinaryData>& stack)
{
   serializedScript_ = move(getSerializedScript(stack));
   resolved_ = true;
}

////////////////////////////////////////////////////////////////////////////////
void ScriptSpender::setWitnessData(const vector<BinaryData>& stack)
{
   BinaryWriter bw;
   bw.put_var_int(stack.size());
   for (auto& stackItem : stack)
   {
      bw.put_var_int(stackItem.getSize());
      bw.put_BinaryData(stackItem);
   }
   
   witnessData_ = move(bw.getData());
   isSegWit_ = true;
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// Signer
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BinaryDataRef Signer::getSerializedOutputScripts(void) const
{
   if (serializedOutputs_.getSize() == 0)
   {
      BinaryWriter bw;
      for (auto& recipient : recipients_)
      {
         auto&& serializedOutput = recipient->getSerializedScript();
         bw.put_BinaryData(serializedOutput);
      }

      serializedOutputs_ = move(bw.getData());
   }

   return serializedOutputs_.getRef();
}

////////////////////////////////////////////////////////////////////////////////
vector<TxInData> Signer::getTxInsData(void) const
{
   vector<TxInData> tidVec;

   for (auto& spender : spenders_)
   {
      TxInData tid;
      tid.outputHash_ = spender->getOutputHash();
      tid.outputIndex_ = spender->getOutputIndex();
      tid.sequence_ = spender->getSequence();

      tidVec.push_back(move(tid));
   }

   return tidVec;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData Signer::getSubScript(unsigned index) const
{
   return spenders_[index]->getOutputScript();
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef Signer::getWitnessData(unsigned inputId) const
{
   return spenders_[inputId]->getWitnessData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData Signer::serializeAllOutpoints(void) const
{
   BinaryWriter bw;
   for (auto& spender : spenders_)
   {
      bw.put_BinaryDataRef(spender->getOutputHash());
      bw.put_uint32_t(spender->getOutputIndex());
   }

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData Signer::serializeAllSequences(void) const
{
   BinaryWriter bw;
   for (auto& spender : spenders_)
   {
      bw.put_uint32_t(spender->getSequence());
   }

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef Signer::getOutpoint(unsigned index) const
{
   return spenders_[index]->getOutpoint();
}

////////////////////////////////////////////////////////////////////////////////
uint64_t Signer::getOutpointValue(unsigned index) const
{
   return spenders_[index]->getValue();
}

////////////////////////////////////////////////////////////////////////////////
unsigned Signer::getTxInSequence(unsigned index) const
{
   return spenders_[index]->getSequence();
}

////////////////////////////////////////////////////////////////////////////////
void Signer::sign(void)
{ 
   //run through each spenders
   for (unsigned i = 0; i < spenders_.size(); i++)
   {
      auto& spender = spenders_[i];

      //resolve spender script
      StackResolver resolver;
      resolver.setFlags(flags_);

      auto proxy = make_shared<SignerProxyFromSigner>(this, i);

      auto resolvedStack = resolver.getResolvedStack(
         spender->getOutputScript(),
         spender->getFeed(),
         proxy);


      auto resolvedStackLegacy = 
         dynamic_pointer_cast<ResolvedStackLegacy>(resolvedStack);

      if (resolvedStackLegacy == nullptr)
         throw runtime_error("invalid resolved stack ptr type");

      spender->setStack(resolvedStackLegacy->getStack());

      auto resolvedStackWitness =
         dynamic_pointer_cast<ResolvedStackWitness>(resolvedStack);

      if (resolvedStackWitness == nullptr)
         continue;

      spender->setWitnessData(resolvedStackWitness->getWitnessStack());
      isSegWit_ = true;
   }
}

////////////////////////////////////////////////////////////////////////////////
SecureBinaryData Signer::sign(const SecureBinaryData& privKey,
   shared_ptr<SigHashData> SHD, unsigned index)
{
   auto spender = spenders_[index];
   auto&& dataToHash = SHD->getDataForSigHash(
      spender->getSigHashType(), *this,
      spender->getOutputScript(), index);

   SecureBinaryData dataSBD(dataToHash);
   auto&& sig = CryptoECDSA().SignData(dataSBD, privKey, false);

   return sig;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptSpender> Signer::getSpender(unsigned index) const
{
   if (index > spenders_.size())
      throw ScriptException("invalid spender index");

   return spenders_[index];
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef Signer::serialize(void) const
{
   if (serializedTx_.getSize() != 0)
      return serializedTx_.getRef();

   BinaryWriter bw;

   //version
   bw.put_uint32_t(version_);

   if (isSegWit_)
   {
      //marker and flag
      bw.put_uint8_t(0);
      bw.put_uint8_t(1);
   }

   //txin count
   bw.put_var_int(spenders_.size());

   //txins
   for (auto& spender : spenders_)
      bw.put_BinaryDataRef(spender->getSerializedInput());

   //txout count
   bw.put_var_int(recipients_.size());

   //txouts
   for (auto& recipient : recipients_)
      bw.put_BinaryDataRef(recipient->getSerializedScript());

   if (isSegWit_)
   {
      //witness data
      for (auto& spender : spenders_)
         bw.put_BinaryDataRef(spender->getWitnessData());
   }

   //lock time
   bw.put_uint32_t(lockTime_);

   serializedTx_ = move(bw.getData());

   return serializedTx_.getRef();
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<SigHashData> Signer::getSigHashDataForSpender(unsigned index) const
{
   if (index > spenders_.size())
      throw ScriptException("invalid spender index");

   auto& spender = spenders_[index];

   shared_ptr<SigHashData> SHD;
   if (spender->isSegWit())
   {
      if (sigHashDataObject_ == nullptr)
         sigHashDataObject_ = make_shared<SigHashDataSegWit>();

      SHD = sigHashDataObject_;
      isSegWit_ = true;
   }
   else
   {
      SHD = make_shared<SigHashDataLegacy>();
   }

   return SHD;
}

////////////////////////////////////////////////////////////////////////////////
bool Signer::verify(void)
{
   //serialize signed tx
   auto txdata = serialize();
   auto bctx = BCTX::parse(txdata);

   map<BinaryData, map<unsigned, UTXO>> utxoMap;

   //gather utxos and spender flags
   unsigned flags = 0;
   for (auto& spender : spenders_)
   {
      auto& indexMap = utxoMap[spender->getOutputHash()];
      indexMap[spender->getOutputIndex()] = spender->getUtxo();
      
      flags |= spender->getFlags();
   }

   //setup verifier
   TransactionVerifier tsv(*bctx, utxoMap);
   auto tsvFlags = tsv.getFlags();
   tsvFlags |= flags;
   tsv.setFlags(tsvFlags);

   return tsv.verify();
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// SignerProxy
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
SignerProxy::~SignerProxy(void)
{}

SignerProxyFromSigner::SignerProxyFromSigner(
   Signer* signer, unsigned index)
{
   auto signerLBD = [signer, index](const BinaryData& pubkey)->SecureBinaryData
   {
      auto spender = signer->getSpender(index);
      auto SHD = signer->getSigHashDataForSpender(index);

      //get priv key for pubkey
      auto&& privKey = spender->getFeed()->getPrivKeyForPubkey(pubkey);

      //sign
      auto&& sig = signer->sign(privKey, SHD, index);

      //convert to DER
      auto&& derSig = BtcUtils::rsToDerSig(sig.getRef());

      //append sighash byte
      derSig.append(spender->getSigHashByte());

      return SecureBinaryData(derSig);
   };

   signerLambda_ = signerLBD;
}