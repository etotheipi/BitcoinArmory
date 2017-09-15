////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_SCRIPT_RECIPIENT
#define _H_SCRIPT_RECIPIENT

#include <stdint.h>
#include "BinaryData.h"
#include "BtcUtils.h"

////
enum SpendScriptType
{
   SST_P2PKH,
   SST_P2SH,
   SST_P2WPKH,
   SST_NESTED_P2WPKH,
   SST_P2WSH,
   SST_NESTED_P2WSH,
   SST_OPRETURN,
   SST_UNIVERSAL
};

////
class ScriptRecipientException : public runtime_error
{
public:
   ScriptRecipientException(const string& err) :
      runtime_error(err)
   {}
};

////////////////////////////////////////////////////////////////////////////////
class ScriptRecipient
{
protected:
   const SpendScriptType type_;
   uint64_t value_ = UINT64_MAX;

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
   virtual size_t getSize(void) const = 0;

   //locals
   uint64_t getValue(void) const { return value_; }
   void setValue(uint64_t val) { value_ = val; }

   //static
   static shared_ptr<ScriptRecipient> deserialize(const BinaryDataRef& dataPtr);
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
         throw ScriptRecipientException("a160 is not 20 bytes long!");
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

   //return size is static
   size_t getSize(void) const { return 34; }
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
         throw ScriptRecipientException("a160 is not 20 bytes long!");
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

   size_t getSize(void) const { return 31; }
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
         throw ScriptRecipientException("a160 is not 20 bytes long!");
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

   size_t getSize(void) const { return 32; }
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
         throw ScriptRecipientException("a256 is not 32 bytes long!");
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

   size_t getSize(void) const { return 43; }
};

////////////////////////////////////////////////////////////////////////////////
class Recipient_OPRETURN : public ScriptRecipient
{
private:
   const BinaryData message_;

public:
   Recipient_OPRETURN(const BinaryData& message) :
      ScriptRecipient(SST_OPRETURN, 0), message_(message)
   {
      if (message_.getSize() > 80)
         throw ScriptRecipientException(
            "OP_RETURN message cannot exceed 80 bytes");
   }

   void serialize(void)
   {
      BinaryWriter bw;
      bw.put_uint64_t(0);
      
      BinaryWriter bw_msg;
      auto size = message_.getSize();
      if (size > 75)
      {
         bw_msg.put_uint8_t(OP_PUSHDATA1);
         bw_msg.put_uint8_t(size);
      }
      else if (size > 0)
      {
         bw_msg.put_uint8_t(size);
      }

      if (size > 0)
         bw_msg.put_BinaryData(message_);

      bw.put_uint8_t(bw_msg.getSize() + 1);
      bw.put_uint8_t(OP_RETURN);
      bw.put_BinaryData(bw_msg.getData());

      script_ = bw.getData();
   }

   size_t getSize(void) const
   {
      auto size = message_.getSize();
      if (size > 75)
         size += 2;
      else if (size > 0)
         size += 1;
      
      size += 9; //8 for value, one for op_return
      return size;
   }
};

////////////////////////////////////////////////////////////////////////////////
class Recipient_Universal : public ScriptRecipient
{
private: 
   const BinaryData binScript_;

public:
   Recipient_Universal(const BinaryData& script, uint64_t val) :
      ScriptRecipient(SST_UNIVERSAL, val), binScript_(script)
   {}

   void serialize(void)
   {
      if (script_.getSize() != 0)
         return;

      BinaryWriter bw;
      bw.put_uint64_t(value_);
      bw.put_var_int(binScript_.getSize());
      bw.put_BinaryData(binScript_);

      script_ = move(bw.getData());
   }

   size_t getSize(void) const
   {
      size_t varint_len = 1;
      if (binScript_.getSize() >= 0xfd)
         varint_len = 3; //larger scripts would make the tx invalid

      return 8 + binScript_.getSize() + varint_len;
   }
};
#endif