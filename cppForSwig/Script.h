////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_SCRIPT
#define _H_SCRIPT

#define SCRIPT_VERIFY_CHECKLOCKTIMEVERIFY 0x00000001
#define SCRIPT_VERIFY_CHECKSEQUENCEVERIFY 0x00000002
#define SCRIPT_VERIFY_P2SH                0x00000004
#define SCRIPT_VERIFY_P2SH_SHA256         0x00000008
#define SCRIPT_VERIFY_SEGWIT              0x00000010
#define P2SH_TIMESTAMP                    1333238400

#include "BinaryData.h"
#include "EncryptionUtils.h"
#include "BtcUtils.h"

////////////////////////////////////////////////////////////////////////////////
class ScriptException : public exception
{
public:
   ScriptException(const char* what) : exception(what)
   {}
};

////////////////////////////////////////////////////////////////////////////////
struct OpCode
{
   size_t offset_;
   uint8_t opcode_;
   BinaryDataRef dataRef_;
};

struct ReversedStackEntry;

////////////////////////////////////////////////////////////////////////////////
struct ExtendedOpCode : public OpCode
{
   unsigned itemIndex_;
   BinaryData data_;

   vector<shared_ptr<ReversedStackEntry>> referenceStackItemVec_;

   ExtendedOpCode(const OpCode& oc) :
      OpCode(oc)
   {}
};

////////////////////////////////////////////////////////////////////////////////
class ScriptParser
{
protected:

   bool notZero(const BinaryData& data)
   {
      //TODO: check for negative zero as well

      if (data.getSize() != 0)
      {
         auto ptr = data.getPtr();

         for (unsigned i = 0; i < data.getSize(); i++)
            if (*(ptr++) != 0)
               return true;
      }

      return false;
   }

   OpCode getNextOpcode(BinaryRefReader& brr) const;

   int64_t rawBinaryToInt(const BinaryData& bd)
   {
      auto len = bd.getSize();
      if (len == 0)
         return 0;

      if (len > 4)
         throw ScriptException("int overflow");

      int64_t val = 0;
      memcpy(&val, bd.getPtr(), len);

      auto valptr = (uint8_t*)&val;
      --len;
      if (valptr[len] & 0x80)
      {
         valptr[len] &= 0x7F;
         val *= -1;
      }

      return val;
   }

   BinaryData intToRawBinary(int64_t val)
   {
      //op_code outputs are allowed to overflow the 32 bit int limitation
      if (val == 0)
         return BinaryData();

      auto absval = abs(val);
      bool neg = val < 0;

      int mostSignificantByteOffset = 7;

      auto intptr = (uint8_t*)&absval;
      while (mostSignificantByteOffset > 0)
      {
         auto byteval = *(intptr + mostSignificantByteOffset);
         if (byteval > 0)
         {
            if (byteval & 0x80)
               ++mostSignificantByteOffset;
            break;
         }

         --mostSignificantByteOffset;
      }

      if (mostSignificantByteOffset > 7)
         throw ScriptException("int overflow");

      if (neg)
      {
         intptr[mostSignificantByteOffset] |= 0x80;
      }

      ++mostSignificantByteOffset;
      BinaryData bd(mostSignificantByteOffset);
      auto ptr = bd.getPtr();
      memcpy(ptr, &absval, mostSignificantByteOffset);

      return bd;
   }

   void seekToEndIf(BinaryRefReader& brr)
   {
      while (brr.getSizeRemaining() > 0)
      {
         seekToNextIfSwitch(brr);
         auto opcode = brr.get_uint8_t();
         if (opcode == OP_ENDIF)
            return;
      }

      throw ScriptException("couldn't not find ENDIF opcode");
   }

   void seekToNextIfSwitch(BinaryRefReader& brr)
   {
      int depth = 0;
      while (brr.getSizeRemaining() > 0)
      {
         auto&& data = getNextOpcode(brr);
         switch (data.opcode_)
         {
         case OP_IF:
         case OP_NOTIF:
            depth++;
            break;

         case OP_ENDIF:
            if (depth-- > 0)
               break;

         case OP_ELSE:
         {
            if (depth > 0)
               break;

            brr.rewind(1 + data.dataRef_.getSize());
            return;
         }
         }
      }

      throw ScriptException("no extra if switches");
   }

   virtual void processOpCode(const OpCode&) = 0;

public:

   void parseScript(BinaryRefReader& brr);

   size_t seekToOpCode(BinaryRefReader&, OPCODETYPE) const;
};

class TransactionStub;
class SigHashData;
class SigHashDataSegWit;

////////////////////////////////////////////////////////////////////////////////
class StackInterpreter : public ScriptParser
{
private:
   vector<BinaryData> stack_;
   vector<BinaryData> altstack_;
   bool onlyPushDataInInput_ = true;

   const TransactionStub* txStubPtr_;
   const unsigned inputIndex_;

   bool isValid_ = false;
   unsigned opcount_ = 0;

   unsigned flags_;

   BinaryDataRef outputScriptRef_;
   BinaryData p2shScript_;

   shared_ptr<SigHashDataSegWit> SHD_SW_ = nullptr;
   shared_ptr<SigHashData> sigHashDataObject_ = nullptr;

private:
   void processOpCode(const OpCode&);

   void op_if(BinaryRefReader& brr, bool isOutputScript)
   {
      //find next if switch offset
      auto innerBlock = brr.fork();
      seekToNextIfSwitch(innerBlock);

      //get block ref for this if block
      BinaryRefReader thisIfBlock(
         brr.get_BinaryDataRef(innerBlock.getPosition()));

      try
      {
         //verify top stack item
         op_verify();

         //reset isValid flag
         isValid_ = false;

         //process block
         processScript(thisIfBlock, isOutputScript);

         //exit if statement
         seekToEndIf(brr);
      }
      catch (ScriptException&)
      {
         //move to next opcode
         auto opcode = brr.get_uint8_t();
         if (opcode == OP_ENDIF)
            return;

         if (opcode != OP_ELSE)
            throw ScriptException("expected OP_ELSE");

         //look for else or endif opcode
         innerBlock = brr.fork();
         seekToNextIfSwitch(innerBlock);

         thisIfBlock = BinaryRefReader(
            brr.get_BinaryDataRef(innerBlock.getPosition()));

         //process block
         processScript(thisIfBlock, isOutputScript);

         //exit if statement
         seekToEndIf(brr);
      }
   }

   void op_0(void)
   {
      stack_.push_back(BinaryData());
   }

   void op_true(void)
   {
      BinaryData btrue;
      btrue.append(1);

      stack_.push_back(move(btrue));
   }

   void op_1negate(void)
   {
      stack_.push_back(move(intToRawBinary(-1)));
   }

   void op_depth(void)
   {
      BinaryWriter bw;
      stack_.push_back(move(intToRawBinary(stack_.size())));
   }

   void op_dup(void)
   {
      stack_.push_back(stack_.back());
   }

   void op_nip(void)
   {
      auto&& data1 = pop_back();
      auto&& data2 = pop_back();

      stack_.push_back(move(data1));
   }

   void op_over(void)
   {
      if (stack_.size() < 2)
         throw ScriptException("stack is too small for op_over");

      auto stackIter = stack_.rbegin();
      auto data = *(stackIter + 1);
      stack_.push_back(move(data));
   }

   void op_2dup(void)
   {
      if (stack_.size() < 2)
         throw ScriptException("stack is too small for op_2dup");

      auto stackIter = stack_.rbegin();
      auto i0 = *(stackIter + 1);
      auto i1 = *stackIter;

      stack_.push_back(i0);
      stack_.push_back(i1);
   }

   void op_3dup(void)
   {
      if (stack_.size() < 3)
         throw ScriptException("stack is too small for op_3dup");

      auto stackIter = stack_.rbegin();
      auto i0 = *(stackIter + 2);
      auto i1 = *(stackIter + 1);
      auto i2 = *stackIter;

      stack_.push_back(i0);
      stack_.push_back(i1);
      stack_.push_back(i2);
   }

   void op_2over(void)
   {
      if (stack_.size() < 4)
         throw ScriptException("stack is too small for op_2over");

      auto stackIter = stack_.rbegin();
      auto i0 = *(stackIter + 3);
      auto i1 = *(stackIter + 2);

      stack_.push_back(i0);
      stack_.push_back(i1);
   }

   void op_toaltstack(void)
   {
      auto&& a = pop_back();
      altstack_.push_back(move(a));
   }

   void op_fromaltstack(void)
   {
      auto& a = altstack_.back();
      stack_.push_back(a);
      altstack_.pop_back();
   }

   void op_ifdup(void)
   {
      auto& data = stack_.back();
      if (notZero(data))
         stack_.push_back(data);
   }

   void op_pick(void)
   {
      auto&& a = pop_back();
      auto aI = rawBinaryToInt(a);

      if (aI >= stack_.size())
         throw ScriptException("op_pick index exceeds stack size");

      auto stackIter = stack_.rbegin() + aI;
      stack_.push_back(*stackIter);
   }

   void op_roll(void)
   {
      auto&& a = pop_back();
      auto rollindex = rawBinaryToInt(a);

      if (rollindex >= stack_.size())
         throw ScriptException("op_roll index exceeds stack size");

      vector<BinaryData> dataVec;
      while (rollindex-- > 0)
         dataVec.push_back(move(pop_back()));
      auto&& rolldata = pop_back();

      auto dataIter = dataVec.rbegin();
      while (dataIter != dataVec.rend())
      {
         stack_.push_back(move(*dataIter));
         ++dataIter;
      }

      stack_.push_back(rolldata);
   }

   void op_rot(void)
   {
      auto&& c = pop_back();
      auto&& b = pop_back();
      auto&& a = pop_back();

      stack_.push_back(move(b));
      stack_.push_back(move(c));
      stack_.push_back(move(a));
   }

   void op_swap(void)
   {
      auto&& data1 = pop_back();
      auto&& data2 = pop_back();

      stack_.push_back(move(data1));
      stack_.push_back(move(data2));
   }

   void op_tuck(void)
   {
      auto&& b = pop_back();
      auto&& a = pop_back();

      stack_.push_back(move(b));
      stack_.push_back(move(a));
      stack_.push_back(move(b));
   }

   void op_ripemd160(void)
   {
      auto&& data = pop_back();
      auto&& hash = BtcUtils().ripemd160_SWIG(data);
      stack_.push_back(move(hash));
   }

   void op_sha256(void)
   {
      auto&& data = pop_back();
      auto&& sha256 = BtcUtils::getSha256(data);
      stack_.push_back(move(sha256));
   }

   void op_hash160()
   {
      auto&& data = pop_back();
      auto&& hash160 = BtcUtils::getHash160(data);
      stack_.push_back(move(hash160));
   }

   void op_hash256()
   {
      auto&& data = pop_back();
      auto&& hash256 = BtcUtils::getHash256(data);
      stack_.push_back(move(hash256));
   }

   void op_size(void)
   {
      auto& data = stack_.back();
      stack_.push_back(move(intToRawBinary(data.getSize())));
   }

   void op_equal(void)
   {
      auto&& data1 = pop_back();
      auto&& data2 = pop_back();

      bool state = (data1 == data2);

      BinaryData bd;
      bd.append(state);
      stack_.push_back(move(bd));
   }

   void op_1add(void)
   {
      auto&& a = pop_back();
      auto aI = rawBinaryToInt(a);

      stack_.push_back(move(intToRawBinary(aI + 1)));
   }

   void op_1sub(void)
   {
      auto&& a = pop_back();
      auto aI = rawBinaryToInt(a);

      stack_.push_back(move(intToRawBinary(aI - 1)));
   }

   void op_negate(void)
   {
      auto&& a = pop_back();
      auto aI = rawBinaryToInt(a);

      stack_.push_back(move(intToRawBinary(-aI)));
   }

   void op_abs(void)
   {
      auto&& a = pop_back();
      auto aI = rawBinaryToInt(a);

      auto&& negA = intToRawBinary(abs(aI));
      stack_.push_back(negA);
   }

   void op_not(void)
   {
      auto&& a = pop_back();
      auto aI = rawBinaryToInt(a);

      if (aI != 0)
         aI = 0;
      else
         aI = 1;

      stack_.push_back(move(intToRawBinary(aI)));
   }

   void op_0notequal(void)
   {
      auto&& a = pop_back();
      auto aI = rawBinaryToInt(a);

      if (aI != 0)
         aI = 1;

      stack_.push_back(move(intToRawBinary(aI)));
   }

   void op_numequal(void)
   {
      auto&& b = pop_back();
      auto&& a = pop_back();

      auto aI = rawBinaryToInt(a);
      auto bI = rawBinaryToInt(b);

      bool state = (aI == bI);

      BinaryData bd;
      bd.append(state);
      stack_.push_back(move(bd));
   }

   void op_numnotequal()
   {
      auto&& b = pop_back();
      auto&& a = pop_back();

      auto aI = rawBinaryToInt(a);
      auto bI = rawBinaryToInt(b);

      bool state = (aI != bI);

      BinaryData bd;
      bd.append(state);
      stack_.push_back(move(bd));
   }

   void op_lessthan(void)
   {
      auto&& b = pop_back();
      auto&& a = pop_back();

      auto aI = rawBinaryToInt(a);
      auto bI = rawBinaryToInt(b);

      bool state = (aI < bI);

      BinaryData bd;
      bd.append(state);
      stack_.push_back(move(bd));
   }

   void op_lessthanorequal(void)
   {
      auto&& b = pop_back();
      auto&& a = pop_back();

      auto aI = rawBinaryToInt(a);
      auto bI = rawBinaryToInt(b);

      bool state = (aI <= bI);

      BinaryData bd;
      bd.append(state);
      stack_.push_back(move(bd));
   }

   void op_greaterthan(void)
   {
      auto&& b = pop_back();
      auto&& a = pop_back();

      auto aI = rawBinaryToInt(a);
      auto bI = rawBinaryToInt(b);

      bool state = (aI > bI);

      BinaryData bd;
      bd.append(state);
      stack_.push_back(move(bd));
   }

   void op_greaterthanorequal(void)
   {
      auto&& b = pop_back();
      auto&& a = pop_back();

      auto aI = rawBinaryToInt(a);
      auto bI = rawBinaryToInt(b);

      bool state = (aI >= bI);

      BinaryData bd;
      bd.append(state);
      stack_.push_back(move(bd));
   }

   void op_min(void)
   {
      auto&& b = pop_back();
      auto&& a = pop_back();

      auto aI = rawBinaryToInt(a);
      auto bI = rawBinaryToInt(b);

      auto cI = min(aI, bI);
      stack_.push_back(move(intToRawBinary(cI)));
   }

   void op_max(void)
   {
      auto&& b = pop_back();
      auto&& a = pop_back();

      auto aI = rawBinaryToInt(a);
      auto bI = rawBinaryToInt(b);

      auto cI = max(aI, bI);
      stack_.push_back(move(intToRawBinary(cI)));
   }

   void op_within(void)
   {
      auto&& top = pop_back();
      auto&& bot = pop_back();
      auto&& x = pop_back();

      auto xI = rawBinaryToInt(x);
      auto topI = rawBinaryToInt(top);
      auto botI = rawBinaryToInt(bot);

      bool state = (xI >= botI && xI < topI);

      BinaryData bd;
      bd.append(state);
      stack_.push_back(move(bd));
   }

   void op_booland(void)
   {
      auto&& b = pop_back();
      auto&& a = pop_back();

      auto aI = rawBinaryToInt(a);
      auto bI = rawBinaryToInt(b);

      uint8_t val = 0;
      if (aI != 0 && bI != 0)
         val = 1;

      BinaryData bd;
      bd.append(val);
      stack_.push_back(move(bd));
   }

   void op_boolor(void)
   {
      auto&& b = pop_back();
      auto&& a = pop_back();

      auto aI = rawBinaryToInt(a);
      auto bI = rawBinaryToInt(b);

      uint8_t val = 0;
      if (aI != 0 || bI != 0)
         val = 1;

      BinaryData bd;
      bd.append(val);
      stack_.push_back(move(bd));
   }

   void op_add(void)
   {
      auto&& b = pop_back();
      auto&& a = pop_back();

      auto aI = rawBinaryToInt(a);
      auto bI = rawBinaryToInt(b);

      auto cI = aI + bI;
      stack_.push_back(move(intToRawBinary(cI)));
   }

   void op_sub(void)
   {
      auto&& b = pop_back();
      auto&& a = pop_back();

      auto aI = rawBinaryToInt(a);
      auto bI = rawBinaryToInt(b);

      auto cI = aI - bI;
      stack_.push_back(move(intToRawBinary(cI)));
   }

   void op_checksig(void);

   void op_checkmultisig(void);

   void op_verify(void)
   {
      auto&& data = pop_back();
      isValid_ = notZero(data);

      if (!isValid_)
         throw ScriptException("op_verify returned false");
   }

   void process_p2wpkh(const BinaryData& scriptHash);
   void process_p2wsh(const BinaryData& scriptHash);

   //
public:
   StackInterpreter(void) :
      txStubPtr_(nullptr), inputIndex_(-1)
   {
      //TODO: figure out rule detection
      flags_ = SCRIPT_VERIFY_P2SH;
   }

   StackInterpreter(const TransactionStub* stubPtr, unsigned inputId) :
      txStubPtr_(stubPtr), inputIndex_(inputId)
   {}

   void push_back(const BinaryData& data) { stack_.push_back(data); }
   BinaryData pop_back(void)
   {
      if (stack_.size() == 0)
         throw ScriptException("tried to pop an empty stack");

      auto data = stack_.back();
      stack_.pop_back();

      return data;
   }

   void checkState(void);
   void processSW(BinaryDataRef outputScript);
   void setSegWitSigHashDataObject(shared_ptr<SigHashDataSegWit> shdo)
   {
      SHD_SW_ = shdo;
   }

   unsigned getFlags(void) const { return flags_; }
   void setFlags(unsigned flags) { flags_ = flags; }

   void processScript(const BinaryDataRef&, bool);
   void processScript(BinaryRefReader&, bool);
};


////////////////////////////////////////////////////////////////////////////////
struct ReversedStackEntry;

////
enum StackValueEnum
{
   StackValue_Static,
   StackValue_FromFeed,
   StackValue_Sig,
   StackValue_Reference
};

////
struct StackValue
{
private:
   const StackValueEnum type_;

public:
   StackValue(StackValueEnum type) :
      type_(type)
   {}

   virtual ~StackValue(void) = 0;

   StackValueEnum type(void) const { return type_; }
};

////
struct StackValueStatic : public StackValue
{
   const BinaryData value_;

   StackValueStatic(BinaryData val) :
      StackValue(StackValue_Static), value_(val)
   {}
};

////
struct StackValueReference : public StackValue
{
   shared_ptr<ReversedStackEntry> valueReference_;
   BinaryData value_;

   StackValueReference(shared_ptr<ReversedStackEntry> rsePtr) :
      StackValue(StackValue_Reference), valueReference_(rsePtr)
   {}
};

////
struct StackValueFromFeed : public StackValue
{
   const BinaryData requestString_;
   BinaryData value_;

   StackValueFromFeed(const BinaryData& bd) :
      StackValue(StackValue_FromFeed), requestString_(bd)
   {}
};

////
struct StackValueSig : public StackValue
{
   shared_ptr<ReversedStackEntry> pubkeyRef_;
   SecureBinaryData sig_;

   StackValueSig(shared_ptr<ReversedStackEntry> ref) :
      StackValue(StackValue_Sig), pubkeyRef_(ref)
   {}
};

////////////////////////////////////////////////////////////////////////////////
struct ReversedStackEntry
{
public:
   
   //static data is usually result of a pushdata opcode
   bool static_ = false; 
   BinaryData staticData_;

   //ptr to parent for op_dup style entries
   shared_ptr<ReversedStackEntry> parent_ = nullptr; 

   //effective opcodes on this item
   vector<shared_ptr<OpCode>> opcodes_;

   //original value prior to opcode effect
   shared_ptr<StackValue> resolvedValue_;

public:
   ReversedStackEntry(void)
   {}

   ReversedStackEntry(const BinaryData& data) :
      static_(true), staticData_(data)
   {}

   bool push_opcode(const OpCode& oc)
   {
      if (static_ && parent_ == nullptr)
         return false;

      auto ocPtr = make_shared<OpCode>(oc);
      push_opcode(ocPtr);
      return true;
   }

   bool push_opcode(shared_ptr<OpCode> ocptr)
   {
      if (static_ && parent_ == nullptr)
         return false;

      if (parent_ != nullptr)
         return parent_->push_opcode(ocptr);

      opcodes_.push_back(ocptr);
      return true;
   }
};

////////////////////////////////////////////////////////////////////////////////
class ResolverFeed
{
public:

   virtual BinaryData getByVal(const BinaryData&) = 0;
   virtual SecureBinaryData getPrivKeyForPubkey(const BinaryData&) = 0;
};

class SignerProxy;

////////////////////////////////////////////////////////////////////////////////
class StackResolver : ScriptParser
{
private:
   deque<shared_ptr<ReversedStackEntry>> stack_;

private:
   shared_ptr<ReversedStackEntry> pop_back(void)
   {
      shared_ptr<ReversedStackEntry> item;

      if (stack_.size() > 0)
      {
         item = stack_.back();
         stack_.pop_back();
      }
      else
         item = make_shared<ReversedStackEntry>();

      return item;
   }

   shared_ptr<ReversedStackEntry> getTopStackEntryPtr(void)
   {
      if (stack_.size() == 0)
         stack_.push_back(make_shared<ReversedStackEntry>());
      
      return stack_.back();
   }

   void processOpCode(const OpCode&);

   void push_int(unsigned i)
   {
      auto&& valBD = intToRawBinary(i);
      pushdata(valBD);
   }

   void pushdata(const BinaryData& data)
   {
      auto rse = make_shared<ReversedStackEntry>(data);
      stack_.push_back(rse);
   }

   void op_dup(void)
   {
      auto rsePtr = getTopStackEntryPtr();

      auto rseDup = make_shared<ReversedStackEntry>();
      rseDup->static_ = true;
      rseDup->parent_ = rsePtr;

      stack_.push_back(rseDup);
   }

   void op_1item(const OpCode& oc)
   {
      auto item1 = pop_back();
      if (item1->push_opcode(oc))
         stack_.push_back(item1);
      
      push_int(1);
   }

   void op_1item_verify(const OpCode& oc)
   {
      op_1item(oc);
      pop_back();
   }

   void op_2items(const OpCode& oc)
   {
      auto item2 = pop_back();
      auto item1 = pop_back();

      ExtendedOpCode eoc1(oc);
      eoc1.itemIndex_ = 1;
      eoc1.referenceStackItemVec_.push_back(item2);
      if(item1->push_opcode(eoc1))
         stack_.push_back(item1);

      ExtendedOpCode eoc2(oc);
      eoc2.itemIndex_ = 2;
      eoc2.referenceStackItemVec_.push_back(item1);
      if(item2->push_opcode(eoc2))
         stack_.push_back(item2);
      
      push_int(1);
   }

   void op_2items_verify(const OpCode& oc)
   {
      op_2items(oc);
      pop_back();
   }
   
   void processScript(BinaryRefReader&);
   void resolveStack(shared_ptr<ResolverFeed>, shared_ptr<SignerProxy>);

public:
   vector<BinaryData> getResolvedStack(
      const BinaryData& script,
      shared_ptr<ResolverFeed>, 
      shared_ptr<SignerProxy>);
};

#endif