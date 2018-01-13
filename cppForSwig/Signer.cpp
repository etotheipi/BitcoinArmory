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

StackItem::~StackItem()
{}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// ScriptSpender
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
ScriptRecipient::~ScriptRecipient() 
{}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptRecipient> ScriptRecipient::deserialize(
   const BinaryDataRef& dataPtr)
{
   shared_ptr<ScriptRecipient> result_ptr;

   BinaryRefReader brr(dataPtr);

   auto value = brr.get_uint64_t();
   auto script = brr.get_BinaryDataRef(brr.getSizeRemaining());

   BinaryRefReader brr_script(script);

   auto byte0 = brr_script.get_uint8_t();
   auto byte1 = brr_script.get_uint8_t();
   auto byte2 = brr_script.get_uint8_t();

   if (byte0 == 25 && byte1 == OP_DUP && byte2 == OP_HASH160)
   {
      auto byte3 = brr_script.get_uint8_t();
      if (byte3 == 20)
      {
         auto&& hash160 = brr_script.get_BinaryData(20);
         result_ptr = make_shared<Recipient_P2PKH>(hash160, value);
      }
   }
   else if (byte0 == 22 && byte1 == 0 && byte2 == 20)
   {
      auto&& hash160 = brr_script.get_BinaryData(20);
      result_ptr = make_shared<Recipient_P2WPKH>(hash160, value);
   }
   else if (byte0 == 23 && byte1 == OP_HASH160 && byte2 == 20)
   {
      auto&& hash160 = brr_script.get_BinaryData(20);
      result_ptr = make_shared<Recipient_P2SH>(hash160, value);
   }
   else if (byte0 == 34 && byte1 == 0 && byte2 == 32)
   {
      auto&& hash256 = brr_script.get_BinaryData(32);
      result_ptr = make_shared<Recipient_PW2SH>(hash256, value);
   }

   if (result_ptr == nullptr)
      throw runtime_error("unexpected recipient script");

   return result_ptr;
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// ScriptSpender
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
BinaryDataRef ScriptSpender::getOutputScript() const
{
   if (!utxo_.isInitialized())
      throw runtime_error("missing utxo");

   return utxo_.getScript();
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef ScriptSpender::getOutputHash() const
{
   if (utxo_.isInitialized())
      return utxo_.getTxHash();

   if (outpoint_.getSize() != 36)
      throw runtime_error("missing utxo");

   BinaryRefReader brr(outpoint_);
   return brr.get_BinaryDataRef(32);
}

////////////////////////////////////////////////////////////////////////////////
unsigned ScriptSpender::getOutputIndex() const
{
   if (utxo_.isInitialized())
      return utxo_.getTxOutIndex();
   
   if (outpoint_.getSize() != 36)
      throw runtime_error("missing utxo");

   BinaryRefReader brr(outpoint_);
   brr.advance(32);

   return brr.get_uint32_t();
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef ScriptSpender::getOutpoint() const
{
   if (outpoint_.getSize() == 0)
   {
      BinaryWriter bw;
      bw.put_BinaryDataRef(getOutputHash());
      bw.put_uint32_t(getOutputIndex());

      outpoint_ = bw.getData();
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
   const vector<shared_ptr<StackItem>>& stack, bool no_throw)
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
         {
            if (!no_throw)
               throw ScriptException("unexpected StackItem type");

            bwStack.put_uint8_t(0);
            break;
         }

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
         {
            if (!no_throw)
               throw ScriptException("unexpected StackItem type");
            
            break;
         }

         bwStack.put_BinaryData(stackItem_ss->data_);
         break;
      }

      case StackItemType_Sig:
      {
         auto stackItem_sig =
            dynamic_pointer_cast<StackItem_Sig>(stackItem);
         if (stackItem_sig == nullptr)
         {
            if (!no_throw)
               throw ScriptException("unexpected StackItem type");

            bwStack.put_uint8_t(0);
            break;
         }

         bwStack.put_BinaryData(
            BtcUtils::getPushDataHeader(stackItem_sig->data_));
         bwStack.put_BinaryData(stackItem_sig->data_);
         break;
      }

      case StackItemType_MultiSig:
      {
         auto stackItem_sig =
            dynamic_pointer_cast<StackItem_MultiSig>(stackItem);
         if (stackItem_sig == nullptr)
         {
            if (!no_throw)
               throw ScriptException("unexpected StackItem type");
            
            bwStack.put_uint8_t(0);
            break;
         }

         if (stackItem_sig->sigs_.size() < stackItem_sig->m_)
         {
            if (!no_throw)
               throw ScriptException("missing sigs for ms script");
         }

         for (auto& sigpair : stackItem_sig->sigs_)
         {
            bwStack.put_BinaryData(
               BtcUtils::getPushDataHeader(sigpair.second));
            bwStack.put_BinaryData(sigpair.second);
         }
         break;
      }

      case StackItemType_OpCode:
      {
         auto stackItem_opcode =
            dynamic_pointer_cast<StackItem_OpCode>(stackItem);
         if (stackItem_opcode == nullptr)
         {
            if (no_throw)
               throw ScriptException("unexpected StackItem type");
            
            bwStack.put_uint8_t(0);
            break;
         }

         bwStack.put_uint8_t(stackItem_opcode->opcode_);
         break;
      }

      default:
         if (!no_throw)
            throw ScriptException("unexpected StackItem type");
      }
   }

   return bwStack.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData ScriptSpender::serializeWitnessData(
   const vector<shared_ptr<StackItem>>& stack, 
   unsigned &itemCount, bool no_throw)
{
   itemCount = 0;

   BinaryWriter bwStack;
   for (auto& stackItem : stack)
   {
      switch (stackItem->type_)
      {
      case StackItemType_PushData:
      {
         ++itemCount;

         auto stackItem_pushdata =
            dynamic_pointer_cast<StackItem_PushData>(stackItem);
         if (stackItem_pushdata == nullptr)
         {
            if (!no_throw)
               throw ScriptException("unexpected StackItem type");

            bwStack.put_uint8_t(0);
            break;
         }

         bwStack.put_var_int(stackItem_pushdata->data_.getSize());
         bwStack.put_BinaryData(stackItem_pushdata->data_);
         break;
      }

      case StackItemType_SerializedScript:
      {

         auto stackItem_ss =
            dynamic_pointer_cast<StackItem_SerializedScript>(stackItem);
         if (stackItem_ss == nullptr)
         {
            if (!no_throw)
               throw ScriptException("unexpected StackItem type");

            break;
         }

         bwStack.put_BinaryData(stackItem_ss->data_);
         ++itemCount;
         break;
      }

      case StackItemType_Sig:
      {
         ++itemCount;
         auto stackItem_sig =
            dynamic_pointer_cast<StackItem_Sig>(stackItem);
         if (stackItem_sig == nullptr)
         {
            if (!no_throw)
               throw ScriptException("unexpected StackItem type");

            bwStack.put_uint8_t(0);
            break;
         }

         bwStack.put_var_int(stackItem_sig->data_.getSize());
         bwStack.put_BinaryData(stackItem_sig->data_);
         break;
      }

      case StackItemType_MultiSig:
      {
         auto stackItem_sig =
            dynamic_pointer_cast<StackItem_MultiSig>(stackItem);
         if (stackItem_sig == nullptr)
         {
            if (!no_throw)
               throw ScriptException("unexpected StackItem type");

            bwStack.put_uint8_t(0);
            break;
         }

         if (stackItem_sig->sigs_.size() < stackItem_sig->m_)
         {
            if (!no_throw)
               throw ScriptException("missing sigs for ms script");
         }

         for (auto& sigpair : stackItem_sig->sigs_)
         {
            bwStack.put_BinaryData(
               BtcUtils::getPushDataHeader(sigpair.second));
            bwStack.put_BinaryData(sigpair.second);
            ++itemCount;
         }
         break;
      }

      case StackItemType_OpCode:
      {
         ++itemCount;
         auto stackItem_opcode =
            dynamic_pointer_cast<StackItem_OpCode>(stackItem);
         if (stackItem_opcode == nullptr)
         {
            if (!no_throw)
               throw ScriptException("unexpected StackItem type");

            bwStack.put_uint8_t(0);
            break;
         }

         bwStack.put_uint8_t(stackItem_opcode->opcode_);
         break;
      }

      default:
         if (!no_throw)
            throw ScriptException("unexpected StackItem type");
      }
   }

   return bwStack.getData();
}

////////////////////////////////////////////////////////////////////////////////
bool ScriptSpender::resolved() const
{
   if (legacyStatus_ != SpenderStatus_Resolved)
      return false;

   if (segwitStatus_ == SpenderStatus_Partial)
      return false;

   return true;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData ScriptSpender::getSerializedOutpoint() const
{
   if (utxo_.isInitialized())
   {
      BinaryWriter bw;

      bw.put_BinaryData(utxo_.getTxHash());
      bw.put_uint32_t(utxo_.getTxOutIndex());

      return bw.getData();
   }

   if (outpoint_.getSize() != 36)
      throw ScriptException("missing outpoint");

   return outpoint_;
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef ScriptSpender::getSerializedInput() const
{
   if (legacyStatus_ != SpenderStatus_Resolved)
      throw ScriptException("unresolved spender");
   
   BinaryWriter bw;
   bw.put_BinaryData(getSerializedOutpoint());

   bw.put_var_int(serializedScript_.getSize());
   bw.put_BinaryData(serializedScript_);
   bw.put_uint32_t(sequence_);

   serializedInput_ = move(bw.getData());
   return serializedInput_.getRef();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData ScriptSpender::serializeAvailableStack() const
{
   try
   {
      return getSerializedInput();
   }
   catch (exception&)
   {}

   vector<shared_ptr<StackItem>> partial_stack;
   for (auto& stack_item : partialStack_)
      partial_stack.push_back(stack_item.second);

   auto&& serialized_script = serializeScript(partial_stack, true);

   BinaryWriter bw;
   bw.put_BinaryData(getSerializedOutpoint());

   bw.put_var_int(serialized_script.getSize());
   bw.put_BinaryData(serialized_script);
   bw.put_uint32_t(sequence_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef ScriptSpender::getWitnessData(void) const
{
   if (segwitStatus_ == SpenderStatus_Partial)
      throw runtime_error("unresolved witness");

   return witnessData_.getRef();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData ScriptSpender::serializeAvailableWitnessData(void) const
{
   try
   {
      return getWitnessData();
   }
   catch (exception&)
   {}

   vector<shared_ptr<StackItem>> partial_stack;
   for (auto& stack_item : partialWitnessStack_)
      partial_stack.push_back(stack_item.second);

   //serialize and get item count
   unsigned itemCount = 0;
   auto&& data = serializeWitnessData(partial_stack, itemCount, true);

   //put stack item count
   BinaryWriter bw;
   bw.put_var_int(itemCount);

   //put serialized stack
   bw.put_BinaryData(data);

   return bw.getData();
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

   legacyStatus_ = SpenderStatus_Resolved;
}

////////////////////////////////////////////////////////////////////////////////
void ScriptSpender::setWitnessData(const vector<shared_ptr<StackItem>>& stack)
{  
   //serialize and get item count
   unsigned itemCount = 0;
   auto&& data = serializeWitnessData(stack, itemCount);

   //put stack item count
   BinaryWriter bw;
   bw.put_var_int(itemCount);

   //put serialized stack
   bw.put_BinaryData(data);

   witnessData_ = bw.getData();
   segwitStatus_ = SpenderStatus_Resolved;
}

////////////////////////////////////////////////////////////////////////////////
void ScriptSpender::updateStack(map<unsigned, shared_ptr<StackItem>>& stackMap,
   const vector<shared_ptr<StackItem>>& stackVec)
{
   for (auto& stack_item : stackVec)
   {
      auto iter_pair = stackMap.insert(
         make_pair(stack_item->getId(), stack_item));

      if (iter_pair.second == true)
         continue;

      //already have a stack item for this id, let's compare them
      if (iter_pair.first->second->isSame(stack_item.get()))
         continue;

      //stack items differ, are they multisig items?

      switch (iter_pair.first->second->type_)
      {
      case StackItemType_MultiSig:
      {
         auto stack_item_ms = 
            dynamic_pointer_cast<StackItem_MultiSig>(iter_pair.first->second);

         stack_item_ms->merge(stack_item.get());
         break;
      }

      default:
         throw ScriptException("unexpected StackItem type inequality");
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void ScriptSpender::evaluatePartialStacks()
{
   if (partialStack_.size() > 0)
   {
      bool isValid = true;
      
      for (auto& item_pair : partialStack_)
         isValid &= item_pair.second->isValid();

      if (isValid)
      {
         vector<shared_ptr<StackItem>> stack_vec;
         for (auto& item_pair : partialStack_)
            stack_vec.push_back(item_pair.second);
         
         setStack(stack_vec);
         partialStack_.clear();
      }
   }
   
   if (partialWitnessStack_.size() > 0)
   {
      bool isValid = true;

      for (auto& item_pair : partialWitnessStack_)
         isValid &= item_pair.second->isValid();

      if (isValid)
      {
         vector<shared_ptr<StackItem>> stack_vec;
         for (auto& item_pair : partialWitnessStack_)
            stack_vec.push_back(item_pair.second);

         setWitnessData(stack_vec);
         partialWitnessStack_.clear();
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
BinaryData ScriptSpender::serializeState() const
{
   BitPacker<uint8_t> bp;
   bp.putBits(legacyStatus_, 2);
   bp.putBits(segwitStatus_, 2);
   bp.putBit(isP2SH_);
   bp.putBit(isCSV_);
   bp.putBit(isCLTV_);

   BinaryWriter bw;
   bw.put_BitPacker(bp);
   bw.put_uint8_t(sigHashType_);
   bw.put_uint32_t(sequence_);

   if (hasUTXO())
   {
      bw.put_uint8_t(PREFIX_UTXO);
      auto&& ser_utxo = utxo_.serialize();
      bw.put_var_int(ser_utxo.getSize());
      bw.put_BinaryData(ser_utxo);
   }
   else
   {
      auto outpoint = getOutpoint();
      bw.put_uint8_t(PREFIX_OUTPOINT);
      bw.put_var_int(outpoint.getSize());
      bw.put_BinaryData(outpoint);
      bw.put_uint64_t(value_);
   }

   if (legacyStatus_ == SpenderStatus_Resolved)
   {
      //put resolved script
      bw.put_uint8_t(SERIALIZED_SCRIPT_PREFIX);
      bw.put_var_int(serializedScript_.getSize());
      bw.put_BinaryData(serializedScript_);
   }
   else if (legacyStatus_ == SpenderStatus_Partial)
   {
      bw.put_uint8_t(LEGACY_STACK_PARTIAL);
      bw.put_var_int(partialStack_.size());

      //put partial stack
      for (auto item_pair : partialStack_)
      {
         auto&& ser_item = item_pair.second->serialize();
         bw.put_var_int(ser_item.getSize());
         bw.put_BinaryData(ser_item);
      }
   }

   if (segwitStatus_ == SpenderStatus_Resolved)
   {
      //put resolved witness data
      bw.put_uint8_t(WITNESS_SCRIPT_PREFIX);
      bw.put_var_int(witnessData_.getSize());
      bw.put_BinaryData(witnessData_);
   }
   else if (segwitStatus_ == SpenderStatus_Partial)
   {
      bw.put_uint8_t(WITNESS_STACK_PARTIAL);
      bw.put_var_int(partialWitnessStack_.size());

      //put partial stack
      for (auto item_pair : partialWitnessStack_)
      {
         auto&& ser_item = item_pair.second->serialize();
         bw.put_var_int(ser_item.getSize());
         bw.put_BinaryData(ser_item);
      }
   }

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptSpender> ScriptSpender::deserializeState(
   const BinaryDataRef& dataRef)
{
   BinaryRefReader brr(dataRef);

   BitUnpacker<uint8_t> bup(brr.get_uint8_t());
   auto sighash_type = (SIGHASH_TYPE)brr.get_uint8_t();
   auto sequence = brr.get_uint32_t();
   
   shared_ptr<ScriptSpender> script_spender;

   auto prefix = brr.get_uint8_t();
   switch (prefix)
   {
   case PREFIX_UTXO:
   {
      auto utxo_len = brr.get_var_int();
      auto utxo_data = brr.get_BinaryDataRef(utxo_len);
      UTXO utxo;
      utxo.unserialize(utxo_data);
      script_spender = make_shared<ScriptSpender>(utxo);
      break;
   }

   case PREFIX_OUTPOINT:
   {
      auto outpoint_len = brr.get_var_int();
      auto outpoint = brr.get_BinaryDataRef(outpoint_len);

      BinaryRefReader brr_outpoint(outpoint);
      auto hash_ref = brr_outpoint.get_BinaryDataRef(32);
      auto idx = brr_outpoint.get_uint32_t();
      auto val = brr.get_uint64_t();

      script_spender = make_shared<ScriptSpender>(hash_ref, idx, val);
      break;
   }

   default:
      throw runtime_error("invalid prefix for utxo/outpoint deser");
   }


   script_spender->legacyStatus_ = (SpenderStatus)bup.getBits(2);
   script_spender->segwitStatus_ = (SpenderStatus)bup.getBits(2);

   script_spender->isP2SH_ = bup.getBit();
   script_spender->isCSV_  = bup.getBit();
   script_spender->isCLTV_ = bup.getBit();

   script_spender->sequence_ = sequence;
   script_spender->sigHashType_ = sighash_type;

   while (brr.getSizeRemaining() > 0)
   {
      auto prefix = brr.get_uint8_t();

      switch (prefix)
      {
      case SERIALIZED_SCRIPT_PREFIX:
      {
         auto len = brr.get_var_int();
         script_spender->serializedScript_ = move(brr.get_BinaryData(len));
         break;
      }

      case WITNESS_SCRIPT_PREFIX:
      {
         auto len = brr.get_var_int();
         script_spender->witnessData_ = move(brr.get_BinaryData(len));
         break;
      }

      case LEGACY_STACK_PARTIAL:
      {
         auto count = brr.get_var_int();

         for (unsigned i = 0; i < count; i++)
         {
            auto len = brr.get_var_int();
            auto stack_item = StackItem::deserialize(brr.get_BinaryDataRef(len));
            script_spender->partialStack_.insert(make_pair(
               stack_item->getId(), stack_item));
         }

         break;
      }

      case WITNESS_STACK_PARTIAL:
      {
         auto count = brr.get_var_int();
          
         for (unsigned i = 0; i < count; i++)
         {
            auto len = brr.get_var_int();
            auto stack_item = StackItem::deserialize(brr.get_BinaryDataRef(len));
            script_spender->partialWitnessStack_.insert(make_pair(
               stack_item->getId(), stack_item));
         }

         break;
      }

      default:
         throw ScriptException("invalid spender state");
      }
   }

   return script_spender;
}

////////////////////////////////////////////////////////////////////////////////
void ScriptSpender::merge(const ScriptSpender& obj)
{
   if (resolved())
      return;

   if (!utxo_.isInitialized() && obj.utxo_.isInitialized())
      utxo_ = obj.utxo_;

   if (legacyStatus_ != SpenderStatus_Resolved)
   {
      switch (obj.legacyStatus_)
      {
      case SpenderStatus_Resolved:
      {
         serializedScript_ = obj.serializedScript_;
         legacyStatus_ = SpenderStatus_Resolved;
         break;
      }

      case SpenderStatus_Partial:
         partialStack_.insert(obj.partialStack_.begin(), obj.partialStack_.end());
         evaluatePartialStacks();
      }
   }

   if (segwitStatus_ != SpenderStatus_Resolved)
   {
      switch (obj.segwitStatus_)
      {
      case SpenderStatus_Resolved:
      {
         witnessData_ = obj.witnessData_;
         segwitStatus_ = SpenderStatus_Resolved;
         break;
      }

      case SpenderStatus_Partial:
         partialWitnessStack_.insert(
            obj.partialWitnessStack_.begin(), obj.partialWitnessStack_.end());
         evaluatePartialStacks();
      }
   }
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
      bw.put_BinaryDataRef(spender->getOutpoint());
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

      if (spender->resolved())
         continue;

      if (!spender->hasUTXO())
         continue;

      if (!spender->hasFeed())
      {
         if (resolverPtr_ == nullptr)
            continue;

         spender->setFeed(resolverPtr_);
      }

      //resolve spender script
      auto proxy = make_shared<SignerProxyFromSigner>(this, i);
      
      StackResolver resolver(
         spender->getOutputScript(),
         spender->getFeed(),
         proxy);

      resolver.setFlags(flags_);

      try
      {
         auto resolvedStack = resolver.getResolvedStack();

         auto resolvedStackLegacy =
            dynamic_pointer_cast<ResolvedStackLegacy>(resolvedStack);

         if (resolvedStackLegacy == nullptr)
            throw runtime_error("invalid resolved stack ptr type");

         spender->flagP2SH(resolvedStack->isP2SH());
         spender->updatePartialStack(
            resolvedStackLegacy->getStack());
         spender->evaluatePartialStacks();

         auto resolvedStackWitness =
            dynamic_pointer_cast<ResolvedStackWitness>(resolvedStack);

         if (resolvedStackWitness == nullptr)
            continue;
         isSegWit_ = true;

         spender->updatePartialWitnessStack(
            resolvedStackWitness->getWitnessStack());
         spender->evaluatePartialStacks();
      }
      catch (...)
      {
         continue;
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void Signer::evaluateSpenderStatus()
{

   //run through each spenders
   for (unsigned i = 0; i < spenders_.size(); i++)
   {
      auto& spender = spenders_[i];
      
      if (spender->resolved())
         continue;
      
      if (!spender->hasUTXO())
         continue;

      auto publicResolver = make_shared<ResolverFeedPublic>(resolverPtr_.get());
      if (spender->hasFeed())
         publicResolver = make_shared<ResolverFeedPublic>(spender->getFeed().get());

      //resolve spender script
      auto proxy = make_shared<SignerProxyFromSigner>(this, i, publicResolver);
      StackResolver resolver(
         spender->getOutputScript(),
         publicResolver,
         proxy);

      resolver.setFlags(flags_);

      try
      {
         auto resolvedStack = resolver.getResolvedStack();

         auto resolvedStackLegacy =
            dynamic_pointer_cast<ResolvedStackLegacy>(resolvedStack);

         if (resolvedStackLegacy == nullptr)
            throw runtime_error("invalid resolved stack ptr type");

         spender->flagP2SH(resolvedStack->isP2SH());
         spender->updatePartialStack(
            resolvedStackLegacy->getStack());
         spender->evaluatePartialStacks();

         auto resolvedStackWitness =
            dynamic_pointer_cast<ResolvedStackWitness>(resolvedStack);

         if (resolvedStackWitness == nullptr)
            continue;
         isSegWit_ = true;

         spender->updatePartialWitnessStack(
            resolvedStackWitness->getWitnessStack());
         spender->evaluatePartialStacks();
      }
      catch (exception&)
      {
         //nothing to do here, just trying to evaluate signing status
         continue;
      }
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
   
#ifdef SIGNER_DEBUG   
   auto&& pubkey = CryptoECDSA().ComputePublicKey(privKey);
   LOGWARN << "signing for: ";
   LOGWARN << "   pubkey: " << pubkey.toHexStr();

   auto&& msghash = BtcUtils::getHash256(dataToHash);
   LOGWARN << "   message: " << dataToHash.toHexStr();
#endif

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
            bw.put_BinaryDataRef(witnessRef);
      }
   }

   //lock time
   bw.put_uint32_t(lockTime_);

   serializedTx_ = move(bw.getData());

   return serializedTx_.getRef();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData Signer::serializeAvailableResolvedData(void) const
{
   try
   {
      auto&& serTx = serialize();
      return serTx;
   }
   catch (exception&)
   {}
   
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
      bw.put_BinaryDataRef(spender->serializeAvailableStack());

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
         BinaryData witnessData = spender->serializeAvailableWitnessData();

         //account for empty witness data
         if (witnessData.getSize() == 0)
            bw.put_uint8_t(0);
         else
            bw.put_BinaryData(witnessData);
      }
   }

   //lock time
   bw.put_uint32_t(lockTime_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<SigHashData> Signer::getSigHashDataForSpender(bool sw) const
{
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
unique_ptr<TransactionVerifier> Signer::getVerifier(shared_ptr<BCTX> bctx,
   map<BinaryData, map<unsigned, UTXO>>& utxoMap) const
{
   return move(make_unique<TransactionVerifier>(*bctx, utxoMap));
}

////////////////////////////////////////////////////////////////////////////////
TxEvalState Signer::verify(const BinaryData& rawTx,
   map<BinaryData, map<unsigned, UTXO>>& utxoMap, unsigned flags) const
{
   auto bctx = BCTX::parse(rawTx);

   //setup verifier
   auto tsv = getVerifier(bctx, utxoMap);
   auto tsvFlags = tsv->getFlags();
   tsvFlags |= flags;
   tsv->setFlags(tsvFlags);

   return tsv->evaluateState();
}

////////////////////////////////////////////////////////////////////////////////
bool Signer::verify(void) 
{
   //serialize signed tx
   auto txdata = serialize();

   map<BinaryData, map<unsigned, UTXO>> utxoMap;

   //gather utxos and spender flags
   unsigned flags = 0;
   for (auto& spender : spenders_)
   {
      auto& indexMap = utxoMap[spender->getOutputHash()];
      indexMap[spender->getOutputIndex()] = spender->getUtxo();
      
      flags |= spender->getFlags();
   }

   auto evalState = verify(txdata, utxoMap, flags);
   return evalState.isValid();
}

////////////////////////////////////////////////////////////////////////////////
bool Signer::verifyRawTx(const BinaryData& rawTx, 
   const map<BinaryData, map<unsigned, BinaryData>>& rawUTXOs)
{
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

   auto&& evalState = 
      verify(rawTx, utxoMap, SCRIPT_VERIFY_P2SH | SCRIPT_VERIFY_SEGWIT);

   return evalState.isValid();
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& Signer::getSigForInputIndex(unsigned id) const
{
   auto spender = getSpender(id);
   return spender->getSingleSig();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData Signer::serializeState() const
{
   BinaryWriter bw;
   bw.put_uint32_t(version_);
   bw.put_uint32_t(lockTime_);
   bw.put_uint32_t(flags_);
   bw.put_uint8_t(isSegWit_);

   bw.put_var_int(spenders_.size());
   for (auto& spender : spenders_)
   {
      auto&& state = spender->serializeState();
      bw.put_var_int(state.getSize());
      bw.put_BinaryData(state);
   }

   bw.put_var_int(recipients_.size());
   for (auto& recipient : recipients_)
   {
      auto&& state = recipient->getSerializedScript();
      bw.put_var_int(state.getSize());
      bw.put_BinaryData(state);
   }

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
Signer Signer::createFromState(const BinaryData& state)
{
   Signer signer;
   BinaryRefReader brr(state.getRef());

   signer.version_ = brr.get_uint32_t();
   signer.lockTime_ = brr.get_uint32_t();
   signer.flags_ = brr.get_uint32_t();
   signer.isSegWit_ = brr.get_uint8_t();

   auto spender_count = brr.get_var_int();
   for (unsigned i = 0; i < spender_count; i++)
   {
      auto spender_len = brr.get_var_int();
      auto spender_data = brr.get_BinaryDataRef(spender_len);

      try
      {
         auto spender_ptr = ScriptSpender::deserializeState(spender_data);
         signer.spenders_.push_back(spender_ptr);
      }
      catch (exception &e)
      {
         LOGWARN << "failed to deser spender";
         LOGWARN << "error: " << e.what();
      }
   }

   auto recipient_count = brr.get_var_int();
   for (unsigned i = 0; i < recipient_count; i++)
   {
      auto recipient_len = brr.get_var_int();
      auto recipient_data = brr.get_BinaryDataRef(recipient_len);

      auto recipient_ptr = ScriptRecipient::deserialize(recipient_data);
      signer.recipients_.push_back(recipient_ptr);
   }

   return signer;
}

////////////////////////////////////////////////////////////////////////////////
void Signer::deserializeState(
   const BinaryData& data)
{
   //deser into a new object
   auto&& new_signer = createFromState(data);

   version_ = new_signer.version_;
   lockTime_ = new_signer.lockTime_;
   flags_ |= new_signer.flags_;
   isSegWit_ |= new_signer.isSegWit_;

   auto find_spender = [this](shared_ptr<ScriptSpender> obj)->
      shared_ptr<ScriptSpender>
   {
      for (auto spd : this->spenders_)
      {
         if (*spd == *obj)
            return spd;
      }

      return nullptr;
   };

   auto find_recipient = [this](shared_ptr<ScriptRecipient> obj)->
      shared_ptr<ScriptRecipient>
   {
      auto& scriptHash = obj->getSerializedScript();
      for (auto rec : this->recipients_)
      {
         if (scriptHash == rec->getSerializedScript())
            return rec;
      }

      return nullptr;
   };

   //Merge new signer with this. As a general rule, the added entries are all 
   //pushed back.

   //merge spender
   for (auto& spender : new_signer.spenders_)
   {
      auto spender_converted = convertSpender(spender);
      auto local_spender = find_spender(spender_converted);
      if (local_spender != nullptr)
         local_spender->merge(*spender_converted);
      else
         spenders_.push_back(spender_converted);
   }


   /*Recipients are told apart by their script hash. Several recipients with
   the same script hash will be aggregated into a single one.

   Note that in case the local signer has several recipient with the same
   hash scripts, these won't be aggregated. Only those from the new_signer will.

   As a general rule, do not create several outputs with the script hash.

   NOTE: adding recipients or triggering an aggregation will render prior signatures 
   invalid. This code does NOT check for that. It's the caller's responsibility 
   to check for this condition.

   As with spenders, new recipients are pushed back.
   */

   for (auto& recipient : new_signer.recipients_)
   {
      auto local_recipient = find_recipient(recipient);

      if (local_recipient == nullptr)
         recipients_.push_back(recipient);
      else
         local_recipient->setValue(
            local_recipient->getValue() + recipient->getValue());
   }
}

////////////////////////////////////////////////////////////////////////////////
bool Signer::isValid() const
{
   for (auto& spender : spenders_)
   {
      if (!spender->resolved())
         return false;
   }

   return true;
}

////////////////////////////////////////////////////////////////////////////////
void Signer::populateUtxo(const UTXO& utxo)
{
   for (auto& spender : spenders_)
   {
      if (spender->hasUTXO())
      {
         auto& spender_utxo = spender->getUtxo();
         if (spender_utxo == utxo)
            return;
      }
      else
      {
         auto outpoint = spender->getOutpoint();
         BinaryRefReader brr(outpoint);
         
         auto&& hash = brr.get_BinaryDataRef(32);
         if (hash != utxo.getTxHash())
            continue;

         auto txoutid = brr.get_uint32_t();
         if (txoutid != utxo.getTxOutIndex())
            continue;

         spender->setUtxo(utxo);
         return;
      }
   }

   throw runtime_error("could not match utxo to any spender");
}

////////////////////////////////////////////////////////////////////////////////
BinaryData Signer::getTxId()
{
   try
   {
      auto txdataref = serialize();
      Tx tx(txdataref);
      return tx.getThisHash();
   }
   catch (exception&)
   {
   }

   //tx isn't signed, let's check for SW inputs
   evaluateSpenderStatus();
   
   //serialize the tx
   BinaryWriter bw;

   //version
   bw.put_uint32_t(version_);
   
   //inputs
   bw.put_var_int(spenders_.size());
   for (auto spender : spenders_)
      bw.put_BinaryDataRef(spender->getSerializedInput());

   //outputs
   bw.put_var_int(recipients_.size());
   for (auto recipient : recipients_)
      bw.put_BinaryDataRef(recipient->getSerializedScript());

   //locktime
   bw.put_uint32_t(lockTime_);

   //hash and return
   return BtcUtils::getHash256(bw.getDataRef());
}

////////////////////////////////////////////////////////////////////////////////
void Signer::addSpender_ByOutpoint(
   const BinaryData& hash, unsigned index, unsigned sequence, uint64_t value)
{
   auto spender = make_shared<ScriptSpender>(hash, index, value);
   spender->setSequence(sequence);

   addSpender(spender);
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptSpender> Signer::convertSpender(
   shared_ptr<ScriptSpender> spender_base) const
{
   //only useful for signers that deviate from the standard code
   return spender_base;
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// Signer_BCH
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
shared_ptr<SigHashData> Signer_BCH::getSigHashDataForSpender(bool sw) const
{
   shared_ptr<SigHashData> SHD;
   if (sigHashDataObject_ == nullptr)
      sigHashDataObject_ = make_shared<SigHashData_BCH>();

   SHD = sigHashDataObject_;
   return SHD;
}

////////////////////////////////////////////////////////////////////////////////
unique_ptr<TransactionVerifier> Signer_BCH::getVerifier(shared_ptr<BCTX> bctx,
   map<BinaryData, map<unsigned, UTXO>>& utxoMap) const
{
   return move(make_unique<TransactionVerifier_BCH>(*bctx, utxoMap));
}

////////////////////////////////////////////////////////////////////////////////
void Signer_BCH::addSpender_ByOutpoint(
   const BinaryData& hash, unsigned index, unsigned sequence, uint64_t value)
{
   auto spender = make_shared<ScriptSpender_BCH>(hash, index, value);
   spender->setSequence(sequence);

   addSpender(spender);
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ScriptSpender> Signer_BCH::convertSpender(
   shared_ptr<ScriptSpender> spender_base) const
{
   //convert to BCH script spender to get the proper sighash byte at 
   //signature serialization
   return make_shared<ScriptSpender_BCH>(*spender_base);
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// SignerProxy
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
SignerProxy::~SignerProxy(void)
{}

////////////////////////////////////////////////////////////////////////////////
void SignerProxyFromSigner::setLambda(
   Signer* signer, shared_ptr<ScriptSpender> spender, unsigned index,
   shared_ptr<ResolverFeed> feedPtr)
{
   auto signerLBD = [signer, spender, index, feedPtr]
      (BinaryDataRef script, const BinaryData& pubkey, bool sw)->SecureBinaryData
   {
      auto SHD = signer->getSigHashDataForSpender(sw);

      //get priv key for pubkey
      auto&& privKey = feedPtr->getPrivKeyForPubkey(pubkey);

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
