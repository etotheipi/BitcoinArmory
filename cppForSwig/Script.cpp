////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "Script.h"
#include "Transactions.h"
#include "Signer.h"
#include "oids.h"

//dtors
StackValue::~StackValue()
{}

ResolvedStack::~ResolvedStack()
{}

ResolverFeed::~ResolverFeed()
{}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// StackItem
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
bool StackItem_PushData::isSame(const StackItem* obj) const
{
   auto obj_cast = dynamic_cast<const StackItem_PushData*>(obj);
   if (obj_cast == nullptr)
      return false;
 
   return data_ == obj_cast->data_;
}

////////////////////////////////////////////////////////////////////////////////
bool StackItem_Sig::isSame(const StackItem* obj) const
{
   auto obj_cast = dynamic_cast<const StackItem_Sig*>(obj);
   if (obj_cast == nullptr)
      return false;

   return data_ == obj_cast->data_;
}

////////////////////////////////////////////////////////////////////////////////
bool StackItem_MultiSig::isSame(const StackItem* obj) const
{
   auto obj_cast = dynamic_cast<const StackItem_MultiSig*>(obj);
   if (obj_cast == nullptr)
      return false;

   return m_ == obj_cast->m_ &&
      sigs_ == obj_cast->sigs_;
}

////////////////////////////////////////////////////////////////////////////////
bool StackItem_OpCode::isSame(const StackItem* obj) const
{
   auto obj_cast = dynamic_cast<const StackItem_OpCode*>(obj);
   if (obj_cast == nullptr)
      return false;

   return opcode_ == obj_cast->opcode_;
}

////////////////////////////////////////////////////////////////////////////////
bool StackItem_SerializedScript::isSame(const StackItem* obj) const
{
   auto obj_cast = dynamic_cast<const StackItem_SerializedScript*>(obj);
   if (obj_cast == nullptr)
      return false;

   return data_ == obj_cast->data_;
}

////////////////////////////////////////////////////////////////////////////////
void StackItem_MultiSig::merge(const StackItem* obj)
{
   auto obj_cast = dynamic_cast<const StackItem_MultiSig*>(obj);
   if (obj_cast == nullptr)
      throw ScriptException("unexpected StackItem type");

   if (m_ != obj_cast->m_)
      throw ScriptException("m mismatch");

   sigs_.insert(obj_cast->sigs_.begin(), obj_cast->sigs_.end());
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StackItem_PushData::serialize(void) const
{
   BinaryWriter bw;
   bw.put_uint32_t(id_);
   bw.put_uint8_t(STACKITEM_PUSHDATA_PREFIX);
   bw.put_var_int(data_.getSize());
   bw.put_BinaryData(data_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StackItem_Sig::serialize(void) const
{
   BinaryWriter bw;
   bw.put_uint32_t(id_);
   bw.put_uint8_t(STACKITEM_SIG_PREFIX);
   bw.put_var_int(data_.getSize());
   bw.put_BinaryData(data_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StackItem_MultiSig::serialize(void) const
{
   BinaryWriter bw;
   bw.put_uint32_t(id_);
   bw.put_uint8_t(STACKITEM_MULTISIG_PREFIX);
   bw.put_uint16_t(m_);
   bw.put_var_int(sigs_.size());
   
   for (auto& sig_pair : sigs_)
   {
      bw.put_uint16_t(sig_pair.first);
      bw.put_var_int(sig_pair.second.getSize());
      bw.put_BinaryData(sig_pair.second);
   }

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StackItem_OpCode::serialize(void) const
{
   BinaryWriter bw;
   bw.put_uint32_t(id_);
   bw.put_uint8_t(STACKITEM_OPCODE_PREFIX);
   bw.put_uint8_t(opcode_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StackItem_SerializedScript::serialize(void) const
{
   BinaryWriter bw;
   bw.put_uint32_t(id_);
   bw.put_uint8_t(STACKITEM_SERSCRIPT_PREFIX);
   bw.put_var_int(data_.getSize());
   bw.put_BinaryData(data_);

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<StackItem> StackItem::deserialize(const BinaryDataRef& dataRef)
{
   shared_ptr<StackItem> itemPtr;

   BinaryRefReader brr(dataRef);

   auto id = brr.get_uint32_t();
   auto prefix = brr.get_uint8_t();

   switch (prefix)
   {
   case STACKITEM_PUSHDATA_PREFIX:
   {
      auto len = brr.get_var_int();
      auto&& data = brr.get_BinaryData(len);

      itemPtr = make_shared<StackItem_PushData>(id, move(data));
      break;
   }

   case STACKITEM_SIG_PREFIX:
   {
      auto len = brr.get_var_int();
      SecureBinaryData data(brr.get_BinaryData(len));

      itemPtr = make_shared<StackItem_Sig>(id, move(data));
      break;
   }

   case STACKITEM_MULTISIG_PREFIX:
   {
      auto m = brr.get_uint16_t();
      auto item_ms = make_shared<StackItem_MultiSig>(id, m);

      auto count = brr.get_var_int();
      for (unsigned i = 0; i < count; i++)
      {
         auto pos = brr.get_uint16_t();
         auto len = brr.get_var_int();
         SecureBinaryData data(brr.get_BinaryData(len));

         item_ms->setSig(pos, data);
      }

      itemPtr = item_ms;
      break;
   }

   case STACKITEM_OPCODE_PREFIX:
   {
      auto opcode = brr.get_uint8_t();

      itemPtr = make_shared<StackItem_OpCode>(id, opcode);
      break;
   }

   case STACKITEM_SERSCRIPT_PREFIX:
   {
      auto len = brr.get_var_int();
      auto&& data = brr.get_BinaryData(len);

      itemPtr = make_shared<StackItem_SerializedScript>(id, move(data));
      break;
   }

   default:
      throw runtime_error("unexpected stack item prefix");
   }

   return itemPtr;
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// ScriptParser
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
OpCode ScriptParser::getNextOpcode(BinaryRefReader& brr) const
{
   OpCode val;
   val.offset_ = brr.getPosition();
   val.opcode_ = brr.get_uint8_t();
   if (val.opcode_ <= 75 && val.opcode_ > 0)
   {
      val.dataRef_ = brr.get_BinaryDataRef(val.opcode_);
   }
   else
   {
      unsigned len = 0;
      switch (val.opcode_)
      {
      case OP_PUSHDATA1:
         len = brr.get_uint8_t();
         break;

      case OP_PUSHDATA2:
         len = brr.get_uint16_t();
         break;

      case OP_PUSHDATA4:
         len = brr.get_uint32_t();
         break;

      case OP_IF:
      case OP_NOTIF:
         len = brr.getSizeRemaining();
         break;

      default:
         return val;
      }

      val.dataRef_ = brr.get_BinaryDataRef(len);
   }

   return val;
}

////////////////////////////////////////////////////////////////////////////////
size_t ScriptParser::seekToOpCode(BinaryRefReader& brr, OPCODETYPE opcode) const
{
   while (brr.getSizeRemaining() > 0)
   {
      auto&& oc = getNextOpcode(brr);
      if (oc.opcode_ == opcode)
         return brr.getPosition() - 1 - oc.dataRef_.getSize();
   }

   return brr.getPosition();
}

void ScriptParser::parseScript(BinaryRefReader& brr)
{
   while (brr.getSizeRemaining() != 0)
   {
      auto&& oc = getNextOpcode(brr);
      processOpCode(oc);
   }
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// StackInterpreter
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
void StackInterpreter::processScript(
   const BinaryDataRef& script, bool isOutputScript)
{
   BinaryRefReader brr(script);
   processScript(brr, isOutputScript);
}

////////////////////////////////////////////////////////////////////////////////
void StackInterpreter::processScript(BinaryRefReader& brr, bool isOutputScript)
{
   if (txStubPtr_ == nullptr)
      throw ("uninitialized stack");

   if (isOutputScript)
      outputScriptRef_ = brr.getRawRef();

   opcount_ = 0;
   isValid_ = false;

   ScriptParser::parseScript(brr);
}

////////////////////////////////////////////////////////////////////////////////
void StackInterpreter::processOpCode(const OpCode& oc)
{
   ++opcount_;

   //handle push data by itself, doesn't play well with switch
   if (oc.opcode_ == 0)
   {
      op_0();
      return;
   }

   if (oc.opcode_ <= 75)
   {
      stack_.push_back(oc.dataRef_);
      return;
   }

   if (oc.opcode_ < 79)
   {
      //op push data
      stack_.push_back(oc.dataRef_);
      return;
   }

   if (oc.opcode_ == OP_1NEGATE)
   {
      op_1negate();
      return;
   }

   if (oc.opcode_ <= 96 && oc.opcode_ >= 81)
   {
      //op_1 - op_16
      uint8_t val = oc.opcode_ - 80;
      stack_.push_back(move(intToRawBinary(val)));
      return;
   }

   //If we got this far this op code is not push data. If this is the input
   //script, set the flag as per P2SH parsing rules (only push data in inputs)
   if (outputScriptRef_.getSize() == 0)
      onlyPushDataInInput_ = false;

   switch (oc.opcode_)
   {
   case OP_NOP:
      break;

   case OP_IF:
   {
      BinaryRefReader brr(oc.dataRef_);
      op_if(brr, false);
      break;
   }

   case OP_NOTIF:
   {
      op_not();
      BinaryRefReader brr(oc.dataRef_);
      op_if(brr, false);
      break;
   }

   case OP_ELSE:
      //processed by opening if statement
      throw ScriptException("a wild else appears");

   case OP_ENDIF:
      //processed by opening if statement
      throw ScriptException("a wild endif appears");

   case OP_VERIFY:
      op_verify();
      break;

   case OP_TOALTSTACK:
      op_toaltstack();
      break;

   case OP_FROMALTSTACK:
      op_fromaltstack();
      break;

   case OP_IFDUP:
      op_ifdup();
      break;

   case OP_2DROP:
   {
      stack_.pop_back();
      stack_.pop_back();
      break;
   }

   case OP_2DUP:
      op_2dup();
      break;

   case OP_3DUP:
      op_3dup();
      break;

   case OP_2OVER:
      op_2over();
      break;

   case OP_DEPTH:
      op_depth();
      break;

   case OP_DROP:
      stack_.pop_back();
      break;

   case OP_DUP:
      op_dup();
      break;

   case OP_NIP:
      op_nip();
      break;

   case OP_OVER:
      op_over();
      break;

   case OP_PICK:
      op_pick();
      break;

   case OP_ROLL:
      op_roll();
      break;

   case OP_ROT:
      op_rot();
      break;

   case OP_SWAP:
      op_swap();
      break;

   case OP_TUCK:
      op_tuck();
      break;

   case OP_SIZE:
      op_size();
      break;

   case OP_EQUAL:
   {
      op_equal();
      if (onlyPushDataInInput_ && p2shScript_.getSize() != 0)
      {
         //check the op_equal result
         op_verify();
         if (!isValid_)
            break;

         if (flags_ & SCRIPT_VERIFY_SEGWIT)
            if (p2shScript_.getSize() == 22 ||
               p2shScript_.getSize() == 34)
            {
               auto versionByte = p2shScript_.getPtr();
               if (*versionByte <= 16)
               {
                  processSW(p2shScript_);
                  return;
               }
            }

         processScript(p2shScript_, true);
      }
      break;
   }

   case OP_EQUALVERIFY:
   {
      op_equal();
      op_verify();
      break;
   }

   case OP_1ADD:
      op_1add();
      break;

   case OP_1SUB:
      op_1sub();
      break;

   case OP_NEGATE:
      op_negate();
      break;

   case OP_ABS:
      op_abs();
      break;

   case OP_NOT:
      op_not();
      break;

   case OP_0NOTEQUAL:
      op_0notequal();
      break;

   case OP_ADD:
      op_add();
      break;

   case OP_SUB:
      op_sub();
      break;

   case OP_BOOLAND:
      op_booland();
      break;

   case OP_BOOLOR:
      op_boolor();
      break;

   case OP_NUMEQUAL:
      op_numequal();
      break;

   case OP_NUMEQUALVERIFY:
   {
      op_numequal();
      op_verify();
      break;
   }

   case OP_NUMNOTEQUAL:
      op_numnotequal();
      break;

   case OP_LESSTHAN:
      op_lessthan();
      break;

   case OP_GREATERTHAN:
      op_greaterthan();
      break;

   case OP_LESSTHANOREQUAL:
      op_lessthanorequal();
      break;

   case OP_GREATERTHANOREQUAL:
      op_greaterthanorequal();
      break;

   case OP_MIN:
      op_min();
      break;

   case OP_MAX:
      op_max();
      break;

   case OP_WITHIN:
      op_within();
      break;

   case OP_RIPEMD160:
      op_ripemd160();
      break;

   case OP_SHA256:
   {
      //save the script if this output is a possible p2sh
      if (flags_ & SCRIPT_VERIFY_P2SH_SHA256)
         if (opcount_ == 1 && onlyPushDataInInput_)
            p2shScript_ = stack_back();

      op_sha256();
      break;
   }

   case OP_HASH160:
   {
      //save the script if this output is a possible p2sh
      if (flags_ & SCRIPT_VERIFY_P2SH)
         if (opcount_ == 1 && onlyPushDataInInput_)
            p2shScript_ = stack_back();

      op_hash160();
      break;
   }

   case OP_HASH256:
      op_hash256();
      break;

   case OP_CODESEPARATOR:
   {
      opcount_ = 0;
      if (outputScriptRef_.getSize() != 0)
         txStubPtr_->setLastOpCodeSeparator(inputIndex_, oc.offset_);
      break;
   }

   case OP_CHECKSIG:
      op_checksig();
      break;

   case OP_CHECKSIGVERIFY:
   {
      op_checksig();
      op_verify();
      break;
   }

   case OP_CHECKMULTISIG:
      op_checkmultisig();
      break;

   case OP_CHECKMULTISIGVERIFY:
   {
      op_checkmultisig();
      op_verify();
   }

   case OP_NOP1:
      break;

   case OP_NOP2:
   {
      if (!(flags_ & SCRIPT_VERIFY_CHECKLOCKTIMEVERIFY))
         break; // not enabled; treat as a NOP

      //CLTV mechanics
      throw ScriptException("OP_CLTV not supported");
   }

   case OP_NOP3:
   {
      if (!(flags_ & SCRIPT_VERIFY_CHECKSEQUENCEVERIFY))
         break; // not enabled; treat as a NOP

      //CSV mechanics
      throw ScriptException("OP_CSV not supported");
   }

   case OP_NOP4:
      break;

   case OP_NOP5:
      break;

   case OP_NOP6:
      break;

   case OP_NOP7:
      break;

   case OP_NOP8:
      break;

   case OP_NOP9:
      break;

   case OP_NOP10:
      break;

   default:
   {
      stringstream ss;
      ss << "unknown opcode: " << (unsigned)oc.opcode_;
      throw runtime_error(ss.str());
   }
   }
}

////////////////////////////////////////////////////////////////////////////////
SIGHASH_TYPE StackInterpreter::getSigHashSingleByte(uint8_t sighashbyte) const
{
   return SIGHASH_TYPE(sighashbyte);
}

////////////////////////////////////////////////////////////////////////////////
SIGHASH_TYPE StackInterpreter_BCH::getSigHashSingleByte(uint8_t sighashbyte) const
{
   if (!(sighashbyte & 0x40))
      throw ScriptException("invalid sighash for bch sig");
   return SIGHASH_TYPE(sighashbyte & 0xBF);
}

////////////////////////////////////////////////////////////////////////////////
void StackInterpreter::op_checksig()
{
   //pop sig and pubkey from the stack
   if (stack_.size() < 2)
      throw ScriptException("insufficient stack size for checksig operation");

   auto&& pubkey = pop_back();
   auto&& sigScript = pop_back();
   if (sigScript.getSize() < 65)
   {
      stack_.push_back(move(intToRawBinary(false)));
      return;
   }

   txInEvalState_.n_ = 1;
   txInEvalState_.m_ = 1;

   //extract sig and sighash type
   BinaryRefReader brrSig(sigScript);
   auto sigsize = sigScript.getSize() - 1;
   auto sig = brrSig.get_BinaryDataRef(sigsize);
   auto hashType = getSigHashSingleByte(brrSig.get_uint8_t());

   //get data for sighash
   if (sigHashDataObject_ == nullptr)
      sigHashDataObject_ = make_shared<SigHashDataLegacy>();
   auto&& sighashdata =
      sigHashDataObject_->getDataForSigHash(hashType, *txStubPtr_,
      outputScriptRef_, inputIndex_);

   //prepare pubkey
   BTC_ECPOINT ptPub;
   CryptoPP::ECP ecp = CryptoECDSA::Get_secp256k1_ECP();
   ecp.DecodePoint(ptPub, (byte*)pubkey.getPtr(), pubkey.getSize());

   BTC_PUBKEY cppPubKey;
   cppPubKey.Initialize(CryptoPP::ASN1::secp256k1(), ptPub);

   //check point validity
   /*BTC_PRNG prng;
   if (!cppPubKey.Validate(prng, 3))
   throw ScriptException("invalid pubkey");*/

   //check signature
   auto&& rs = BtcUtils::extractRSFromDERSig(sig);

   bool result = CryptoECDSA().VerifyData(sighashdata, rs, cppPubKey);
   stack_.push_back(move(intToRawBinary(result)));

   if (result)
      txInEvalState_.pubKeyState_.insert(make_pair(pubkey, true));
}

////////////////////////////////////////////////////////////////////////////////
void StackInterpreter::op_checkmultisig()
{
   //stack needs to have at least m, n, output script
   if (stack_.size() < 3)
      throw ScriptException("insufficient stack size for checkmultisig operation");

   //pop n
   auto&& n = pop_back();
   auto nI = rawBinaryToInt(n);
   if (nI < 0 || nI > 20)
      throw ScriptException("invalid n");

   //pop pubkeys
   map<unsigned, pair<BTC_PUBKEY, BinaryData>> pubkeys;
   for (unsigned i = 0; i < nI; i++)
   {
      auto&& pubkey = pop_back();

      CryptoPP::ECP ecp = CryptoECDSA::Get_secp256k1_ECP();
      BTC_ECPOINT ptPub;
      ecp.DecodePoint(ptPub, (byte*)pubkey.getPtr(), pubkey.getSize());

      BTC_PUBKEY cppPubKey;
      cppPubKey.Initialize(CryptoPP::ASN1::secp256k1(), ptPub);

      BTC_PRNG prng;
      if (cppPubKey.Validate(prng, 3))
      {
         txInEvalState_.pubKeyState_.insert(make_pair(pubkey, false));
         auto&& pubkeypair = make_pair(move(cppPubKey), pubkey);
         pubkeys.insert(move(make_pair(i, move(pubkeypair))));
      }
   }

   //pop m
   auto&& m = pop_back();
   auto mI = rawBinaryToInt(m);
   if (mI < 0 || mI > nI)
      throw ScriptException("invalid m");

   txInEvalState_.n_ = nI;
   txInEvalState_.m_ = mI;

   //pop sigs
   struct sigData
   {
      BinaryData sig_;
      SIGHASH_TYPE hashType_;
   };
   vector<sigData> sigVec;

   while (stack_.size() > 0)
   {
      auto&& sig = pop_back();
      if (sig.getSize() == 0)
         break;

      sigData sdata;

      sdata.sig_ = sig.getSliceCopy(0, sig.getSize() - 1);

      //grab hash type
      sdata.hashType_ = 
         getSigHashSingleByte(*(sig.getPtr() + sig.getSize() - 1));

      //push to vector
      sigVec.push_back(move(sdata));
   }

   //should have at least as many sigs as m
   /*if (sigVec.size() < mI)
      throw ScriptException("invalid sig count");*/

   //check sigs
   map<SIGHASH_TYPE, BinaryData> dataToHash;

   //check sighashdata object
   if (sigHashDataObject_ == nullptr)
      sigHashDataObject_ = make_shared<SigHashDataLegacy>();

   unsigned validSigCount = 0;
   int index = nI - 1;
   auto sigIter = sigVec.rbegin();
   while(sigIter != sigVec.rend())
   {
      auto& sigD = *sigIter++;

      //get data to hash
      auto& hashdata = dataToHash[sigD.hashType_];
      if (hashdata.getSize() == 0)
      {
         hashdata = sigHashDataObject_->getDataForSigHash(
            sigD.hashType_, *txStubPtr_, outputScriptRef_, inputIndex_);
      }

      //prepare sig
      auto&& rs = BtcUtils::extractRSFromDERSig(sigD.sig_);
      BinaryWriter sigW;

      //pop pubkeys from deque to verify against sig
      while (pubkeys.size() > 0)
      {
         auto pubkey = pubkeys[index];
         pubkeys.erase(index--);

#ifdef SIGNER_DEBUG
         LOGWARN << "Verifying sig for: ";
         LOGWARN << "   pubkey: " << pubkey.second.toHexStr();

         auto&& msg_hash = BtcUtils::getHash256(hashdata);
         LOGWARN << "   message: " << hashdata.toHexStr();
#endif
            
         if (CryptoECDSA().VerifyData(hashdata, rs, pubkey.first))
         {
            txInEvalState_.pubKeyState_[pubkey.second] = true;
            validSigCount++;
            break;
         }        
      }
   }

   if (validSigCount >= mI)
      op_true();
   else
      op_0();
}

////////////////////////////////////////////////////////////////////////////////
void StackInterpreter::processSW(BinaryDataRef outputScript)
{
   if (flags_ & SCRIPT_VERIFY_SEGWIT)
   {
      //set sig hash object to sw if it's missing
      sigHashDataObject_ = SHD_SW_;

      BinaryRefReader brr(outputScript);
      auto versionByte = brr.get_uint8_t();

      switch (versionByte)
      {
      case 0:
      {
         auto&& scriptSize = brr.get_uint8_t();
         auto&& scriptHash = brr.get_BinaryDataRef(scriptSize);

         if (brr.getSizeRemaining() > 0)
            throw ScriptException("invalid v0 SW ouput size");

         switch (scriptSize)
         {
         case 20:
         {
            //P2WPKH
            process_p2wpkh(scriptHash);
            break;
         }

         case 32:
         {
            //P2WSH
            process_p2wsh(scriptHash);
            break;
         }

         default:
            throw ScriptException("invalid data size for version 0 SW");
         }

         break;
      }

      default:
         throw ScriptException("unsupported SW versions");
      }
   }
   else
      throw ScriptException("not flagged for SW parsing");
}

////////////////////////////////////////////////////////////////////////////////
void StackInterpreter::checkState()
{
   if (!isValid_)
      op_verify();

   txInEvalState_.validStack_ = true;
}

////////////////////////////////////////////////////////////////////////////////
void StackInterpreter::process_p2wpkh(const BinaryData& scriptHash)
{
   //get witness data
   auto witnessData = txStubPtr_->getWitnessData(inputIndex_);

   //prepare stack
   BinaryRefReader brr(witnessData);
   auto itemCount = brr.get_uint8_t();
   if (itemCount != 2)
      throw ScriptException("v0 P2WPKH witness has to be 2 items");

   for (unsigned i = 0; i < itemCount; i++)
   {
      auto len = brr.get_var_int();
      stack_.push_back(brr.get_BinaryData(len));
   }
   
   if (brr.getSizeRemaining() != 0)
      throw ScriptException("witness size mismatch");

   //construct output script
   auto&& swScript = BtcUtils::getP2WPKHScript(scriptHash);
   processScript(swScript, true);
}

////////////////////////////////////////////////////////////////////////////////
void StackInterpreter::process_p2wsh(const BinaryData& scriptHash)
{
   //get witness data
   auto witnessData = txStubPtr_->getWitnessData(inputIndex_);
   BinaryData witBD(witnessData);

   //prepare stack
   BinaryRefReader brr(witnessData);
   auto itemCount = brr.get_uint8_t();
   
   for (unsigned i = 0; i < itemCount; i++)
   {
      auto len = brr.get_var_int();
      stack_.push_back(brr.get_BinaryData(len));
   }

   if (brr.getSizeRemaining() != 0)
      throw ScriptException("witness size mismatch");

   flags_ |= SCRIPT_VERIFY_P2SH_SHA256;

   //construct output script
   auto&& swScript = BtcUtils::getP2WSHScript(scriptHash);
   processScript(swScript, true);
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// StackInterpreter_BCH
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
StackInterpreter_BCH::StackInterpreter_BCH(void) :
StackInterpreter()
{
   sigHashDataObject_ = make_shared<SigHashData_BCH>();
}

////////////////////////////////////////////////////////////////////////////////
StackInterpreter_BCH::StackInterpreter_BCH(
   const TransactionStub* stubPtr, unsigned inputId) :
StackInterpreter(stubPtr, inputId)
{
   sigHashDataObject_ = make_shared<SigHashData_BCH>();
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//// ReversedStackInterpreter
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
void StackResolver::processScript(BinaryRefReader& brr)
{
   while (brr.getSizeRemaining() != 0)
   {
      auto&& oc = getNextOpcode(brr);
      processOpCode(oc);
   }
}

////////////////////////////////////////////////////////////////////////////////
void StackResolver::processOpCode(const OpCode& oc)
{
   if (oc.opcode_ >= 1 && oc.opcode_ <= 75)
   {
      pushdata(oc.dataRef_);
      return;
   }

   if (oc.opcode_ >= 81 && oc.opcode_ <= 96)
   {
      unsigned val = oc.opcode_ - 80;
      push_int(val);
      return;
   }

   opCodeCount_++;
   switch (oc.opcode_)
   {
   case OP_0:
      pushdata(BinaryData());
      break;

   case OP_PUSHDATA1:
   case OP_PUSHDATA2:
   case OP_PUSHDATA4:
      pushdata(oc.dataRef_);
      break;

   case OP_DUP:
      op_dup();
      break;

   case OP_HASH160:
   case OP_SHA256:
   {
      opHash_ = true;
      op_1item_verify(oc);
      break;
   }

   case OP_RIPEMD160:
   case OP_HASH256:
      op_1item_verify(oc);
      break;

   case OP_EQUAL:
   {
      if (opCodeCount_ == 2 && opHash_)
         isP2SH_ = true;
      op_2items(oc);
      break;
   }

   case OP_CHECKSIG:
      op_2items(oc);
      break;

   case OP_EQUALVERIFY:
   case OP_CHECKSIGVERIFY:
      op_2items_verify(oc);
      break;

   case OP_CHECKMULTISIG:
   case OP_CHECKMULTISIGVERIFY:
      push_op_code(oc);
      break;

   default:
      throw ScriptException("opcode not implemented with reverse stack");
   }
}

////////////////////////////////////////////////////////////////////////////////
void StackResolver::resolveStack()
{
   auto resolveReferenceValue = [](
      shared_ptr<ReversedStackEntry> inPtr)->BinaryData
   {
      auto currentPtr = inPtr;
      while (1)
      {
         if (currentPtr->parent_ != nullptr)
         {
            currentPtr = currentPtr->parent_;
         }
         else if (currentPtr->static_)
         {
            return currentPtr->staticData_;
         }
         else
         {
            switch (currentPtr->resolvedValue_->type())
            {
            case StackValueType_Static:
            {
               auto staticVal = dynamic_pointer_cast<StackValue_Static>(
                  currentPtr->resolvedValue_);

               return staticVal->value_;
            }

            case StackValueType_FromFeed:
            {
               auto feedVal = dynamic_pointer_cast<StackValue_FromFeed>(
                  currentPtr->resolvedValue_);

               return feedVal->value_;
            }

            case StackValueType_Reference:
            {
               auto refVal = dynamic_pointer_cast<StackValue_Reference>(
                  currentPtr->resolvedValue_);

               currentPtr = refVal->valueReference_;
               break;
            }

            default:
               throw ScriptException("unexpected StackValue type \
                  during reference resolution");
            }
         }

         if (currentPtr == inPtr)
            throw ScriptException("infinite loop in reference resolution");
      }
   };

   unsigned static_count = 0;

   auto stackIter = stack_.rbegin();
   while (stackIter != stack_.rend())
   {
      auto stackItem = *stackIter++;

      if (stackItem->static_)
      {
         static_count++;
         continue;
      }

      //resolve the stack item value by reverting the effect of the opcodes 
      //it goes through
      auto opcodeIter = stackItem->opcodes_.begin();
      while (opcodeIter != stackItem->opcodes_.end())
      {
         auto opcodePtr = *opcodeIter++;
         switch (opcodePtr->opcode_)
         {

         case OP_EQUAL:
         case OP_EQUALVERIFY:
         {
            //TODO: use something safer than a C style cast
            auto opcodeExPtr = (ExtendedOpCode*)opcodePtr.get();
            if (opcodeExPtr->referenceStackItemVec_.size() != 1)
               throw ScriptException(
                  "invalid stack item reference count for op_equal resolution");

            auto& stackItemRefPtr = opcodeExPtr->referenceStackItemVec_[0];

            if (stackItem->resolvedValue_ == nullptr)
            {
               if (stackItemRefPtr->static_)
               {
                  //references a static item, just copy the value
                  stackItem->resolvedValue_ =
                     make_shared<StackValue_Static>(stackItemRefPtr->staticData_);
               }
               else
               {
                  //references a dynamic item, point to it
                  stackItem->resolvedValue_ =
                     make_shared<StackValue_Reference>(stackItemRefPtr);
               }
            }
            else
            {
               auto vrPtr = dynamic_pointer_cast<StackValue_Reference>(
                  stackItem->resolvedValue_);
               if (vrPtr != nullptr)
               {
                  vrPtr->valueReference_ = stackItemRefPtr;
                  break;
               }

               auto ffPtr = dynamic_pointer_cast<StackValue_FromFeed>(
                  stackItem->resolvedValue_);
               if (ffPtr != nullptr)
               {
                  if (!stackItemRefPtr->static_)
                     throw ScriptException("unexpected StackValue type in op_equal");
                  ffPtr->requestString_ = stackItemRefPtr->staticData_;
                  break;
               }

               throw ScriptException("unexpected StackValue type in op_equal");
            }

            break;
         }

         case OP_HASH160:
         case OP_HASH256:
         case OP_RIPEMD160:
         case OP_SHA256:
         {
            auto stackItemValPtr =
               dynamic_pointer_cast<StackValue_Static>(
               stackItem->resolvedValue_);
            if (stackItemValPtr != nullptr)
            {
               stackItem->resolvedValue_ =
                  make_shared<StackValue_FromFeed>(
                  stackItemValPtr->value_);
            }
            else
            {
               stackItem->resolvedValue_ =
                  make_shared<StackValue_FromFeed>(
                  BinaryData());
            }

            break;
         }

         case OP_CHECKSIG:
         case OP_CHECKSIGVERIFY:
         {
            auto opcodeExPtr = (ExtendedOpCode*)opcodePtr.get();
            if (opcodeExPtr == nullptr)
               throw ScriptException(
               "expected extended op code entry for op_checksig resolution");

            //second item of checksigs are pubkeys, skip
            if (opcodeExPtr->itemIndex_ == 2)
               break;

            if (opcodeExPtr->referenceStackItemVec_.size() != 1)
               throw ScriptException(
               "invalid stack item reference count for op_checksig resolution");

            //first items are always signatures, overwrite any stackvalue object
            auto& refItem = opcodeExPtr->referenceStackItemVec_[0];
            stackItem->resolvedValue_ =
               make_shared<StackValue_Sig>(refItem);

            break;
         }

         case OP_CHECKMULTISIG:
         case OP_CHECKMULTISIGVERIFY:
         {
            auto getStackItem = [&, this](void)->shared_ptr<ReversedStackEntry>
            {
               if (stackIter == stack_.rend())
                  throw ScriptException("stack is too small for OP_CMS");
               
               auto stack_item = *stackIter++;
               if (!stack_item->static_)
                  throw ScriptException("OP_CMS item is not static");

               return stack_item;
            };

            auto n_item = getStackItem();
            auto n_item_val = rawBinaryToInt(n_item->staticData_);

            vector<BinaryDataRef> pubKeyVec;
            for (unsigned y = 0; y < n_item_val; y++)
            {
               auto pubkey = getStackItem();
               pubKeyVec.push_back(pubkey->staticData_.getRef());
            }

            auto m_sig = getStackItem();
            auto m_sig_val = rawBinaryToInt(m_sig->staticData_);

            if (m_sig_val > n_item_val)
               throw ScriptException("OP_CMS m > n");

            stackItem->resolvedValue_ =
               make_shared<StackValue_Multisig>(move(pubKeyVec), (unsigned)m_sig_val);

            break;
         }

         default:
            throw ScriptException("no resolution rule for opcode");
         }
      }
         
      //fulfill resolution
      switch (stackItem->resolvedValue_->type())
      {
      case StackValueType_FromFeed:
      {
         //grab from feed
         auto fromFeed = dynamic_pointer_cast<StackValue_FromFeed>(
            stackItem->resolvedValue_);
         fromFeed->value_ = feed_->getByVal(fromFeed->requestString_);

         if (isP2SH_)
         {
            //if this output is flagged as p2sh, this value is the script
            //process that script and set the resolved stack
            StackResolver resolver(fromFeed->value_, feed_, proxy_);
            resolver.setFlags(flags_);
            resolver.isSW_ = isSW_;

            auto stackptr = move(resolver.getResolvedStack());
            resolvedStack_ = stackptr;
         }

         break;
      }

      case StackValueType_Sig:
      {
         //grab pubkey from reference, then sign
         auto ref = dynamic_pointer_cast<StackValue_Sig>(
            stackItem->resolvedValue_);

         auto&& pubkey = resolveReferenceValue(ref->pubkeyRef_);
         ref->sig_ = move(proxy_->sign(script_, pubkey, isSW_));
         break;
      }

      case StackValueType_Multisig:
      {
         auto msObj = dynamic_pointer_cast<StackValue_Multisig>(
            stackItem->resolvedValue_);

         unsigned sigCount = 0;
         unsigned keyCount = 0;
         auto pubkeyIter = msObj->pubkeyVec_.rbegin();
         while (pubkeyIter != msObj->pubkeyVec_.rend())
         {
            try
            {
               auto thisKeyId = keyCount++;
               auto&& sig = proxy_->sign(script_, *pubkeyIter++, isSW_);
               msObj->sig_.insert(make_pair(keyCount, move(sig)));
               ++sigCount;
               if (sigCount >= msObj->m_)
                  break;
            }
            catch (runtime_error&)
            {
               //feed is missing private key, nothing to do
            }
         }

         break;
      }

      case StackValueType_Reference:
      {
         //grab from reference
         auto ref = dynamic_pointer_cast<StackValue_Reference>(
            stackItem->resolvedValue_);
         ref->value_ = move(resolveReferenceValue(ref->valueReference_));
         break;
      }

      default:
         //nothing to do
         continue;
      }
   }

   if (flags_ & SCRIPT_VERIFY_SEGWIT)
   {
      if (static_count == 2 && stack_.size() == 2)
      {
         auto _stackIter = stack_.begin();
         auto firstStackItem = *_stackIter;

         auto header = rawBinaryToInt(firstStackItem->staticData_);

         if (header == 0)
         {
            ++_stackIter;
            auto secondStackItem = *_stackIter;

            BinaryData swScript;

            if (secondStackItem->staticData_.getSize() == 20)
            {
               //resolve P2WPKH script
               swScript =
                  BtcUtils::getP2WPKHScript(secondStackItem->staticData_);
            }
            else if (secondStackItem->staticData_.getSize() == 32)
            {
               //resolve P2WSH script
               swScript =
                  BtcUtils::getP2WSHScript(secondStackItem->staticData_);
               isP2SH_ = true;
            }
            else
            {
               throw ScriptException("invalid SW script format");
            }
            
            StackResolver resolver(swScript, feed_, proxy_);
            resolver.setFlags(flags_);
            resolver.isSW_ = true;

            try
            {
               //failed SW should just result in an empty stack instead of an actual throw
               auto newResolvedStack = make_shared<ResolvedStackWitness>(resolvedStack_);
               resolvedStack_ = newResolvedStack;

               auto stackptr = move(resolver.getResolvedStack());

               auto stackptrLegacy = dynamic_pointer_cast<ResolvedStackLegacy>(stackptr);
               if (stackptrLegacy == nullptr)
                  throw runtime_error("unexpected resolved stack ptr type");

               newResolvedStack->setWitnessStack(
                  stackptrLegacy->getStack());
            }
            catch (exception&)
            { }
         }
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<ResolvedStack> StackResolver::getResolvedStack()
{
   if (resolvedStack_ != nullptr)
   {
      if (resolvedStack_->isValid())
         return resolvedStack_;
   }

   BinaryRefReader brr(script_);
   processScript(brr);
   resolveStack();

   bool isValid = true;
   unsigned count = 0;
   if (resolvedStack_ != nullptr)
      count = resolvedStack_->stackSize();

   vector<shared_ptr<StackItem>> resolvedStack;

   for (auto& stackItem : stack_)
   {
      if (stackItem->static_)
         continue;

      switch (stackItem->resolvedValue_->type())
      {
      case StackValueType_Static:
      {
         auto val = dynamic_pointer_cast<StackValue_Static>(
            stackItem->resolvedValue_);

         resolvedStack.push_back(
            make_shared<StackItem_PushData>(
               count++, move(val->value_)));
         break;
      }

      case StackValueType_FromFeed:
      {
         auto val = dynamic_pointer_cast<StackValue_FromFeed>(
            stackItem->resolvedValue_);

         resolvedStack.push_back(
            make_shared<StackItem_PushData>(
               count++, move(val->value_)));
         break;
      }

      case StackValueType_Reference:
      {
         auto val = dynamic_pointer_cast<StackValue_Reference>(
            stackItem->resolvedValue_);

         resolvedStack.push_back(
            make_shared<StackItem_PushData>(
               count++, move(val->value_)));
         break;
      }

      case StackValueType_Sig:
      {
         auto val = dynamic_pointer_cast<StackValue_Sig>(
            stackItem->resolvedValue_);

         resolvedStack.push_back(
            make_shared<StackItem_Sig>(
               count++, move(val->sig_)));
         break;
      }

      case StackValueType_Multisig:
      {
         auto msObj = dynamic_pointer_cast<StackValue_Multisig>(
            stackItem->resolvedValue_);

         //push lead 0 to cover for OP_CMS bug
         resolvedStack.push_back(
            make_shared<StackItem_OpCode>(count++, 0));

         auto stackitem_ms = make_shared<StackItem_MultiSig>(
            count++, msObj->m_);

         //sigs
         for (auto& sig : msObj->sig_)
            stackitem_ms->setSig(sig.first, sig.second);
         resolvedStack.push_back(stackitem_ms);

         if (msObj->sig_.size() < msObj->m_)
            isValid = false;

         break;
      }

      default:
         throw runtime_error("unexpected stack value type");
      }
   }
   
   if (resolvedStack_ == nullptr)
      resolvedStack_ = make_shared<ResolvedStackLegacy>();

   auto resolvedStackPtr = dynamic_pointer_cast<ResolvedStackLegacy>(resolvedStack_);
   if (resolvedStackPtr == nullptr)
      throw runtime_error("unexpected resolved stack ptr type");

   resolvedStackPtr->setStack(move(resolvedStack));
   resolvedStackPtr->isValid_ = isValid;
   resolvedStackPtr->flagP2SH(isP2SH_);

   return resolvedStack_;
}
