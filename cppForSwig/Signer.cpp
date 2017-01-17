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

StackItem::~StackItem()
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
const BinaryData& ScriptSpender::getSingleSig(void) const
{
   if (sigVec_.size() == 0)
      throw ScriptException("no sig for script (yet?)");
   else if (sigVec_.size() > 1)
      throw ScriptException("script does not yield a single signature");

   return sigVec_[0];
}

////////////////////////////////////////////////////////////////////////////////
BinaryData ScriptSpender::serializeScript(
   const vector<shared_ptr<StackItem>>& stack)
{
   BinaryWriter bwStack;
   for (auto& stackItem : stack)
   {
      switch (stackItem->type_)
      {
      case StackItemType_PushData:
      {
         auto stackItem_pushdata = 
            dynamic_pointer_cast<StackItem_PushData>(stackItem);
         if (stackItem_pushdata == nullptr)
            throw ScriptException("unexpected StackItem type");

         bwStack.put_BinaryData(
            BtcUtils::getPushDataHeader(stackItem_pushdata->data_));
         bwStack.put_BinaryData(stackItem_pushdata->data_);
         break;
      }

      case StackItemType_SerializedScript:
      {
         auto stackItem_ss =
            dynamic_pointer_cast<StackItem_SerializedScript>(stackItem);
         if (stackItem_ss == nullptr)
            throw ScriptException("unexpected StackItem type");

         bwStack.put_BinaryData(stackItem_ss->data_);
         break;
      }

      case StackItemType_Sig:
      {
         auto stackItem_sig =
            dynamic_pointer_cast<StackItem_Sig>(stackItem);
         if (stackItem_sig == nullptr)
            throw ScriptException("unexpected StackItem type");

         bwStack.put_BinaryData(
            BtcUtils::getPushDataHeader(stackItem_sig->data_));
         bwStack.put_BinaryData(stackItem_sig->data_);
         break;
      }

      case StackItemType_OpCode:
      {
         auto stackItem_opcode =
            dynamic_pointer_cast<StackItem_OpCode>(stackItem);
         if (stackItem_opcode == nullptr)
            throw ScriptException("unexpected StackItem type");

         bwStack.put_uint8_t(stackItem_opcode->opcode_);
         break;
      }

      default:
         throw ScriptException("unexpected StackItem type");
      }
   }

   return bwStack.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData ScriptSpender::serializeWitnessData(
   const vector<shared_ptr<StackItem>>& stack)
{
   BinaryWriter bwStack;
   for (auto& stackItem : stack)
   {
      switch (stackItem->type_)
      {
      case StackItemType_PushData:
      {
         auto stackItem_pushdata =
            dynamic_pointer_cast<StackItem_PushData>(stackItem);
         if (stackItem_pushdata == nullptr)
            throw ScriptException("unexpected StackItem type");

         bwStack.put_var_int(stackItem_pushdata->data_.getSize());
         bwStack.put_BinaryData(stackItem_pushdata->data_);
         break;
      }

      case StackItemType_SerializedScript:
      {
         auto stackItem_ss =
            dynamic_pointer_cast<StackItem_SerializedScript>(stackItem);
         if (stackItem_ss == nullptr)
            throw ScriptException("unexpected StackItem type");

         bwStack.put_BinaryData(stackItem_ss->data_);
         break;
      }

      case StackItemType_Sig:
      {
         auto stackItem_sig =
            dynamic_pointer_cast<StackItem_Sig>(stackItem);
         if (stackItem_sig == nullptr)
            throw ScriptException("unexpected StackItem type");

         bwStack.put_var_int(stackItem_sig->data_.getSize());
         bwStack.put_BinaryData(stackItem_sig->data_);
         break;
      }

      case StackItemType_OpCode:
      {
         auto stackItem_opcode =
            dynamic_pointer_cast<StackItem_OpCode>(stackItem);
         if (stackItem_opcode == nullptr)
            throw ScriptException("unexpected StackItem type");

         bwStack.put_uint8_t(stackItem_opcode->opcode_);
         break;
      }

      default:
         throw ScriptException("unexpected StackItem type");
      }
   }

   return bwStack.getData();
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
void ScriptSpender::setStack(const vector<shared_ptr<StackItem>>& stack)
{
   serializedScript_ = move(serializeScript(stack));

   for (auto& stackItem : stack)
   {
      switch (stackItem->type_)
      {
      case StackItemType_Sig:
      {
         auto stackItem_sig =
            dynamic_pointer_cast<StackItem_Sig>(stackItem);
         if (stackItem_sig == nullptr)
            throw ScriptException("unexpected StackItem type");

         sigVec_.push_back(stackItem_sig->data_);
         break;
      }

      default:
         continue;
      }
   }

   resolved_ = true;
}

////////////////////////////////////////////////////////////////////////////////
void ScriptSpender::setWitnessData(const vector<shared_ptr<StackItem>>& stack)
{  
   BinaryWriter bw;
   //put stack item count
   bw.put_var_int(stack.size());

   //put serialized stack
   bw.put_BinaryData(serializeWitnessData(stack));

   witnessData_ = bw.getData();
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
   auto spender = getSpender(index);
   return spender->getOutputScript();
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef Signer::getWitnessData(unsigned index) const
{
   auto spender = getSpender(index);
   return spender->getWitnessData();
}

////////////////////////////////////////////////////////////////////////////////
bool Signer::isInputSW(unsigned index) const
{
   auto spender = getSpender(index);
   return spender->isSegWit();
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
      auto proxy = make_shared<SignerProxyFromSigner>(this, i);
      
      StackResolver resolver(
         spender->getOutputScript(),
         spender->getFeed(),
         proxy);

      resolver.setFlags(flags_);


      auto resolvedStack = resolver.getResolvedStack();

      auto resolvedStackLegacy = 
         dynamic_pointer_cast<ResolvedStackLegacy>(resolvedStack);

      if (resolvedStackLegacy == nullptr)
         throw runtime_error("invalid resolved stack ptr type");

      spender->setStack(resolvedStackLegacy->getStack());
      spender->flagP2SH(resolvedStack->isP2SH());

      auto resolvedStackWitness =
         dynamic_pointer_cast<ResolvedStackWitness>(resolvedStack);

      if (resolvedStackWitness == nullptr)
         continue;

      spender->setWitnessData(resolvedStackWitness->getWitnessStack());
      isSegWit_ = true;
   }
}

////////////////////////////////////////////////////////////////////////////////
SecureBinaryData Signer::sign(
   BinaryDataRef script,
   const SecureBinaryData& privKey,
   shared_ptr<SigHashData> SHD, unsigned index)
{
   auto spender = spenders_[index];

   auto&& dataToHash = SHD->getDataForSigHash(
      spender->getSigHashType(), *this,
      script, index);

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
      {
         BinaryDataRef witnessRef = spender->getWitnessData();
         
         //account for empty witness data
         if (witnessRef.getSize() == 0)
            bw.put_uint8_t(0);
         else
            bw.put_BinaryDataRef(spender->getWitnessData());
      }
   }

   //lock time
   bw.put_uint32_t(lockTime_);

   serializedTx_ = move(bw.getData());

   return serializedTx_.getRef();
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<SigHashData> Signer::getSigHashDataForSpender(
   unsigned index, bool sw) const
{
   if (index > spenders_.size())
      throw ScriptException("invalid spender index");

   auto& spender = spenders_[index];

   shared_ptr<SigHashData> SHD;
   if (sw)
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
bool Signer::verifyRawTx(const BinaryData& rawTx, 
   const map<BinaryData, map<unsigned, BinaryData>>& rawUTXOs)
{
   //deser raw tx
   auto bctx = BCTX::parse(rawTx);

   map<BinaryData, map<unsigned, UTXO>> utxoMap;

   //deser utxos
   for (auto& utxoPair : rawUTXOs)
   {
      map<unsigned, UTXO> idMap;
      for (auto& rawUtxoPair : utxoPair.second)
      {
         UTXO utxo;
         utxo.unserializeRaw(rawUtxoPair.second);
         idMap.insert(move(make_pair(rawUtxoPair.first, move(utxo))));
      }

      utxoMap.insert(move(make_pair(utxoPair.first, move(idMap))));
   }

   //setup verifier
   TransactionVerifier tsv(*bctx, utxoMap);
   auto tsvFlags = tsv.getFlags();
   tsvFlags |= SCRIPT_VERIFY_P2SH | SCRIPT_VERIFY_SEGWIT;
   tsv.setFlags(tsvFlags);

   return tsv.verify(true);
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& Signer::getSigForInputIndex(unsigned id) const
{
   auto& spender = getSpender(id);
   return spender->getSingleSig();
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
   auto signerLBD = [signer, index]
      (BinaryDataRef script, const BinaryData& pubkey, bool sw)->SecureBinaryData
   {
      auto spender = signer->getSpender(index);
      auto SHD = signer->getSigHashDataForSpender(index, sw);

      //get priv key for pubkey
      auto&& privKey = spender->getFeed()->getPrivKeyForPubkey(pubkey);

      //sign
      auto&& sig = signer->sign(script, privKey, SHD, index);

      //convert to DER
      auto&& derSig = BtcUtils::rsToDerSig(sig.getRef());

      //append sighash byte
      derSig.append(spender->getSigHashByte());

      return SecureBinaryData(derSig);
   };

   signerLambda_ = signerLBD;
}