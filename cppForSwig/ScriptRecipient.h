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
   SST_NESTED_P2WSH
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
   virtual size_t getSize(void) const = 0;

   //locals
   uint64_t getValue(void) const { return value_; }
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

#endif