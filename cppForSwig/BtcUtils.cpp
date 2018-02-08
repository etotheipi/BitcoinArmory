////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BtcUtils.h"
#include "hmac.h"
#include "sha.h"
#include "base64.h"
#include "EncryptionUtils.h"
#include "BlockDataManagerConfig.h"


const BinaryData BtcUtils::BadAddress_ = BinaryData::CreateFromHex("0000000000000000000000000000000000000000");
const BinaryData BtcUtils::EmptyHash_  = BinaryData::CreateFromHex("0000000000000000000000000000000000000000000000000000000000000000");
const string BtcUtils::base58Chars_ = string("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz");

////////////////////////////////////////////////////////////////////////////////
const map<char, uint8_t> BtcUtils::base58Vals_ = {
   { '1', 0 }, { '2', 1 }, { '3', 2 }, { '4', 3 }, { '5', 4 }, { '6', 5 },
   { '7', 6 }, { '8', 7 }, { '9', 8 }, { 'A', 9 }, { 'B', 10 }, { 'C', 11 },
   { 'D', 12 }, { 'E', 13 }, { 'F', 14 }, { 'G', 15 }, { 'H', 16 }, { 'J', 17 },
   { 'K', 18 }, { 'L', 19 }, { 'M', 20 }, { 'N', 21 }, { 'P', 22 }, { 'Q', 23 },
   { 'R', 24 }, { 'S', 25 }, { 'T', 26 }, { 'U', 27 }, { 'V', 28 }, { 'W', 29 },
   { 'X', 30 }, { 'Y', 31 }, { 'Z', 32 }, { 'a', 33 }, { 'b', 34 }, { 'c', 35 },
   { 'd', 36 }, { 'e', 37 }, { 'f', 38 }, { 'g', 39 }, { 'h', 40 }, { 'i', 41 },
   { 'j', 42 }, { 'k', 43 }, { 'm', 44 }, { 'n', 45 }, { 'o', 46 }, { 'p', 47 }, 
   { 'q', 48 }, { 'r', 49 }, { 's', 50 }, { 't', 51 }, { 'u', 52 }, { 'v', 53 }, 
   { 'w', 54 }, { 'x', 55 }, { 'y', 56 }, { 'z', 57 }
};

////////////////////////////////////////////////////////////////////////////////
BinaryData BtcUtils::computeID(const SecureBinaryData& pubkey)
{
   BinaryDataRef bdr(pubkey);
   auto&& h160 = getHash160(bdr);
   
   BinaryWriter bw;
   bw.put_uint8_t(BlockDataManagerConfig::getPubkeyHashPrefix());
   bw.put_BinaryDataRef(h160.getSliceRef(0, 5));

   //now reverse it
   auto& data = bw.getData();
   auto ptr = data.getPtr();
   BinaryWriter bwReverse;
   for (unsigned i = 0; i < data.getSize(); i++)
   {
      bwReverse.put_uint8_t(ptr[data.getSize() - 1 - i]);
   }

   auto&& b58_5bytes = BtcUtils::base58_encode(bwReverse.getDataRef());

   return b58_5bytes;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BtcUtils::getHMAC256(const SecureBinaryData& key,
   const SecureBinaryData& message)
{
   BinaryData digest;
   digest.resize(32);
   
   getHMAC256(key.getPtr(), key.getSize(), 
      message.getCharPtr(), message.getSize(),
      digest.getPtr());

   return digest;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BtcUtils::getHMAC256(const BinaryData& key,
   const string& message)
{
   BinaryData digest;
   digest.resize(32);
   
   getHMAC256(key.getPtr(), key.getSize(), 
      message.c_str(), message.size(),
      digest.getPtr());

   return digest;
}


////////////////////////////////////////////////////////////////////////////////
void BtcUtils::getHMAC256(const uint8_t* keyptr, size_t keylen,
   const char* msgptr, size_t msglen, uint8_t* digest)
{
   CryptoPP::HMAC<CryptoPP::SHA256> hmac(keyptr, keylen);
   hmac.CalculateDigest(digest, (const byte*)msgptr, msglen);
}

////////////////////////////////////////////////////////////////////////////////
SecureBinaryData BtcUtils::computeChainCode_Armory135(
   const SecureBinaryData& privateRoot)
{
   /*
   Armory 1.35c defines the chaincode as HMAC<SHA256> with:
   key: double SHA256 of the root key
   message: 'Derive Chaincode from Root Key'
   */

   auto&& hmacKey = BtcUtils::hash256(privateRoot);
   string hmacMsg("Derive Chaincode from Root Key");
   SecureBinaryData chainCode(32);

   getHMAC256(hmacKey.getPtr(), hmacKey.getSize(),
      hmacMsg.c_str(), hmacMsg.size(), chainCode.getPtr());

   return chainCode;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BtcUtils::rsToDerSig(BinaryDataRef bdr)
{
   if (bdr.getSize() != 64)
      throw runtime_error("unexpected rs sig length");

   //split r and s
   auto r_bdr = bdr.getSliceRef(0, 32);
   auto s_bdr = bdr.getSliceRef(32, 32);

   //trim r
   unsigned trim = 0;
   auto ptr = r_bdr.getPtr();
   while (trim < r_bdr.getSize())
   {
      if (ptr[trim] != 0)
         break;

      trim++;
   }

   auto r_trim = bdr.getSliceRef(trim, 32 - trim);
   
   //prepend 0 for negative values
   BinaryWriter bwR;
   if (*r_trim.getPtr() > 0x7f)
      bwR.put_uint8_t(0);
   bwR.put_BinaryDataRef(r_trim);

   //get lowS
   auto&& lowS = CryptoECDSA::computeLowS(s_bdr);

   //prepend 0 for negative values
   BinaryWriter bwS;
   if (*lowS.getPtr() > 0x7f)
      bwS.put_uint8_t(0);
   bwS.put_BinaryData(lowS);

   BinaryWriter bw;

   //code byte
   bw.put_uint8_t(0x30);

   //size
   bw.put_uint8_t(4 + bwR.getSize() + bwS.getSize());

   //r code byte
   bw.put_uint8_t(0x02);

   //r size
   bw.put_uint8_t(bwR.getSize());

   //r
   bw.put_BinaryDataRef(bwR.getDataRef());

   //s code byte
   bw.put_uint8_t(0x02);

   //s size
   bw.put_uint8_t(bwS.getSize());

   //s
   bw.put_BinaryDataRef(bwS.getDataRef());

   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData BtcUtils::getTxOutScrAddr(BinaryDataRef script,
   TXOUT_SCRIPT_TYPE type)
{
   BinaryWriter bw;
   if (type == TXOUT_SCRIPT_NONSTANDARD)
      type = getTxOutScriptType(script);

   auto h160Prefix = BlockDataManagerConfig::getPubkeyHashPrefix();
   auto scriptPrefix = BlockDataManagerConfig::getScriptHashPrefix();

   switch (type)
   {
      case(TXOUT_SCRIPT_STDHASH160) :
         bw.put_uint8_t(h160Prefix);
         bw.put_BinaryData(script.getSliceCopy(3, 20));
         return bw.getData();
      case(TXOUT_SCRIPT_P2WPKH) :
         bw.put_uint8_t(h160Prefix);
         bw.put_BinaryData(script.getSliceCopy(2, 20));
         return bw.getData();
      case(TXOUT_SCRIPT_P2WSH) :
         bw.put_uint8_t(scriptPrefix);
         bw.put_BinaryData(script.getSliceCopy(2, 32));
         return bw.getData();
      case(TXOUT_SCRIPT_STDPUBKEY65) :
         bw.put_uint8_t(h160Prefix);
         bw.put_BinaryData(getHash160(script.getSliceRef(1, 65)));
         return bw.getData();
      case(TXOUT_SCRIPT_STDPUBKEY33) :
         bw.put_uint8_t(h160Prefix);
         bw.put_BinaryData(getHash160(script.getSliceRef(1, 33)));
         return bw.getData();
      case(TXOUT_SCRIPT_P2SH) :
         bw.put_uint8_t(scriptPrefix);
         bw.put_BinaryData(script.getSliceCopy(2, 20));
         return bw.getData();
      case(TXOUT_SCRIPT_NONSTANDARD) :
         bw.put_uint8_t(SCRIPT_PREFIX_NONSTD);
         bw.put_BinaryData(getHash160(script));
         return bw.getData();
      case(TXOUT_SCRIPT_MULTISIG) :
         bw.put_uint8_t(SCRIPT_PREFIX_MULTISIG);
         bw.put_BinaryData(getMultisigUniqueKey(script));
         return bw.getData();
      case(TXOUT_SCRIPT_OPRETURN) :
      {
         bw.put_uint8_t(SCRIPT_PREFIX_NONSTD);
         unsigned msg_pos = 1;
         if (script.getSize() > 77)
            msg_pos += 2;
         else if (script.getSize() > 1)
            ++msg_pos;

         bw.put_BinaryData(
            script.getSliceRef(msg_pos, script.getSize() - msg_pos));
         return bw.getData();
      }

      default:
         LOGERR << "What kind of TxOutScript did we get?";
         return BinaryData(0);
   }
}

/////////////////////////////////////////////////////////////////////////////
//no copy version, the regular one is too slow for scanning operations
TxOutScriptRef BtcUtils::getTxOutScrAddrNoCopy(BinaryDataRef script)
{
   TxOutScriptRef outputRef;

   auto p2pkh_prefix = 
      SCRIPT_PREFIX(BlockDataManagerConfig::getPubkeyHashPrefix());
   auto p2sh_prefix = 
      SCRIPT_PREFIX(BlockDataManagerConfig::getScriptHashPrefix());

   auto type = getTxOutScriptType(script);
   switch (type)
   {
   case(TXOUT_SCRIPT_STDHASH160) :
   {
      outputRef.type_ = p2pkh_prefix;
      outputRef.scriptRef_ = move(script.getSliceRef(3, 20));
      break;
   }

   case(TXOUT_SCRIPT_P2WPKH) :
   {
      outputRef.type_ = p2pkh_prefix;
      outputRef.scriptRef_ = move(script.getSliceRef(2, 20));
      break;
   }

   case(TXOUT_SCRIPT_P2WSH) :
   {
      outputRef.type_ = p2sh_prefix;
      outputRef.scriptRef_ = move(script.getSliceRef(2, 32));
      break;
   }

   case(TXOUT_SCRIPT_STDPUBKEY65) :
   {
      outputRef.type_ = p2pkh_prefix;
      outputRef.scriptCopy_ = move(getHash160(script.getSliceRef(1, 65)));
      outputRef.scriptRef_.setRef(outputRef.scriptCopy_);
      break;
   }

   case(TXOUT_SCRIPT_STDPUBKEY33) :
   {
      outputRef.type_ = p2pkh_prefix;
      outputRef.scriptCopy_ = move(getHash160(script.getSliceRef(1, 33)));
      outputRef.scriptRef_.setRef(outputRef.scriptCopy_);
      break;
   }

   case(TXOUT_SCRIPT_P2SH) :
   {
      outputRef.type_ = p2sh_prefix;
      outputRef.scriptRef_ = move(script.getSliceRef(2, 20));
      break;
   }

   case(TXOUT_SCRIPT_NONSTANDARD) :
   {
      outputRef.type_ = SCRIPT_PREFIX_NONSTD;
      outputRef.scriptCopy_ = move(getHash160(script));
      outputRef.scriptRef_.setRef(outputRef.scriptCopy_);
      break;
   }

   case(TXOUT_SCRIPT_MULTISIG) :
   {
      outputRef.type_ = SCRIPT_PREFIX_MULTISIG;
      outputRef.scriptCopy_ = move(getMultisigUniqueKey(script));
      outputRef.scriptRef_.setRef(outputRef.scriptCopy_);
      break;
   }

   case(TXOUT_SCRIPT_OPRETURN) :
   {
      outputRef.type_ = SCRIPT_PREFIX_OPRETURN;
      auto size = script.getSize();
      size_t pos = 1;
      if (size > 77)
         pos += 2;
      if (size > 1)
         ++pos;

      outputRef.scriptRef_ = script.getSliceRef(pos, size - pos);
      break;
   }

   default:
      LOGERR << "What kind of TxOutScript did we get?";
   }

   return outputRef;
}

////////////////////////////////////////////////////////////////////////////////
string BtcUtils::base64_encode(const string& in)
{
   string output;
   CryptoPP::Base64Encoder base64e(
      new CryptoPP::StringSink(output), false, in.size() + 1);
   base64e.Put((const byte*)in.c_str(), in.size());
   base64e.MessageEnd();

   return output;
}

////////////////////////////////////////////////////////////////////////////////
string BtcUtils::base64_decode(const string& in)
{
   string output;
   CryptoPP::Base64Decoder base64e(new CryptoPP::StringSink(output));
   base64e.Put((const byte*)in.c_str(), in.size());
   base64e.MessageEnd();

   return output;
}