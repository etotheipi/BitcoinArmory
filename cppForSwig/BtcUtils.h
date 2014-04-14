////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2014, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _BTCUTILS_H_
#define _BTCUTILS_H_

#include <stdio.h>

#include <iostream>
#include <vector>
#include <list>
#include <string>
#include <sstream>
#include <assert.h>
#include <cmath>
#include <time.h>
#include <algorithm>
#include <stdexcept>

#include "BinaryData.h"
#include "cryptlib.h"
#include "sha.h"
#include "ripemd.h"
#include "UniversalTimer.h"
#include "log.h"

#define HEADER_SIZE 80
#define COIN 100000000ULL
#define NBLOCKS_REGARDED_AS_RESCAN 144
#define MIN_CONFIRMATIONS   6
#define COINBASE_MATURITY 120

#define TX_0_UNCONFIRMED    0 
#define TX_NOT_EXIST       -1
#define TX_OFF_MAIN_BRANCH -2


#define HashString     BinaryData
#define HashStringRef  BinaryDataRef

#ifdef _DEBUG
   #define PDEBUG(s) (cout << s << endl)
   #define PDEBUG2(s1, s2) (cout << s1 << " " << s2 << endl)
   #define PDEBUG3(s1, s2, s3) (cout << s1 << " " << s2 << " " << s3 << endl)
#else
   #define PDEBUG(s)
   #define PDEBUG2(s1, s2)
   #define PDEBUG3(s1, s2, s3)
#endif


#define FILE_DOES_NOT_EXIST UINT64_MAX


#define TESTNET_MAGIC_BYTES "0b110907"
#define TESTNET_GENESIS_HASH_HEX    "43497fd7f826957108f4a30fd9cec3aeba79972084e90ead01ea330900000000"
#define TESTNET_GENESIS_TX_HASH_HEX "3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a"

#define MAINNET_MAGIC_BYTES "f9beb4d9"
#define MAINNET_GENESIS_HASH_HEX    "6fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000"
#define MAINNET_GENESIS_TX_HASH_HEX "3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a"

#define BITMASK(X) (2**X - 1)

#define HASH160PREFIX WRITE_UINT8_LE((uint8_t)SCRIPT_PREFIX_HASH160)
#define P2SHPREFIX    WRITE_UINT8_LE((uint8_t)SCRIPT_PREFIX_P2SH)
#define MSIGPREFIX    WRITE_UINT8_LE((uint8_t)SCRIPT_PREFIX_MULTISIG)
#define NONSTDPREFIX  WRITE_UINT8_LE((uint8_t)SCRIPT_PREFIX_NONSTD)

// Really, these defs are just for making it painfully clear in the 
// code what you are attempting to compare.  I'm constantly messing 
// up == and != when trying to read through the code.
#define  KEY_NOT_IN_MAP(KEY,MAP)  (MAP.find(KEY) == MAP.end())
#define      KEY_IN_MAP(KEY,MAP)  (MAP.find(KEY) != MAP.end())
#define ITER_NOT_IN_MAP(ITER,MAP) (ITER == MAP.end())
#define     ITER_IN_MAP(ITER,MAP) (ITER != MAP.end())

class BinaryData;
class BinaryDataRef;

typedef enum
{
   TXOUT_SCRIPT_STDHASH160,
   TXOUT_SCRIPT_STDPUBKEY65,
   TXOUT_SCRIPT_STDPUBKEY33,
   TXOUT_SCRIPT_MULTISIG,
   TXOUT_SCRIPT_P2SH,
   TXOUT_SCRIPT_NONSTANDARD,
}  TXOUT_SCRIPT_TYPE;

typedef enum
{
   TXIN_SCRIPT_STDUNCOMPR,
   TXIN_SCRIPT_STDCOMPR,
   TXIN_SCRIPT_COINBASE,
   TXIN_SCRIPT_SPENDPUBKEY,
   TXIN_SCRIPT_SPENDMULTI,
   TXIN_SCRIPT_SPENDP2SH,
   TXIN_SCRIPT_NONSTANDARD
}  TXIN_SCRIPT_TYPE;


typedef enum
{
  SCRIPT_PREFIX_HASH160=0x00,
  SCRIPT_PREFIX_P2SH=0x05,
  SCRIPT_PREFIX_MULTISIG=0xfe,
  SCRIPT_PREFIX_NONSTD=0xff,
} SCRIPT_PREFIX;


enum OPCODETYPE
{
    // push value
    OP_0=0,
    OP_FALSE=OP_0,
    OP_PUSHDATA1=76,
    OP_PUSHDATA2,
    OP_PUSHDATA4,
    OP_1NEGATE,
    OP_RESERVED,
    OP_1,
    OP_TRUE=OP_1,
    OP_2,
    OP_3,
    OP_4,
    OP_5,
    OP_6,
    OP_7,
    OP_8,
    OP_9,
    OP_10,
    OP_11,
    OP_12,
    OP_13,
    OP_14,
    OP_15,
    OP_16,

    // control
    OP_NOP,
    OP_VER,
    OP_IF,
    OP_NOTIF,
    OP_VERIF,
    OP_VERNOTIF,
    OP_ELSE,
    OP_ENDIF,
    OP_VERIFY,
    OP_RETURN,

    // stack ops
    OP_TOALTSTACK,
    OP_FROMALTSTACK,
    OP_2DROP,
    OP_2DUP,
    OP_3DUP,
    OP_2OVER,
    OP_2ROT,
    OP_2SWAP,
    OP_IFDUP,
    OP_DEPTH,
    OP_DROP,
    OP_DUP,
    OP_NIP,
    OP_OVER,
    OP_PICK,
    OP_ROLL,
    OP_ROT,
    OP_SWAP,
    OP_TUCK,

    // splice ops
    OP_CAT,
    OP_SUBSTR,
    OP_LEFT,
    OP_RIGHT,
    OP_SIZE,

    // bit logic
    OP_INVERT,
    OP_AND,
    OP_OR,
    OP_XOR,
    OP_EQUAL,
    OP_EQUALVERIFY,
    OP_RESERVED1,
    OP_RESERVED2,

    // numeric
    OP_1ADD,
    OP_1SUB,
    OP_2MUL,
    OP_2DIV,
    OP_NEGATE,
    OP_ABS,
    OP_NOT,
    OP_0NOTEQUAL,

    OP_ADD,
    OP_SUB,
    OP_MUL,
    OP_DIV,
    OP_MOD,
    OP_LSHIFT,
    OP_RSHIFT,

    OP_BOOLAND,
    OP_BOOLOR,
    OP_NUMEQUAL,
    OP_NUMEQUALVERIFY,
    OP_NUMNOTEQUAL,
    OP_LESSTHAN,
    OP_GREATERTHAN,
    OP_LESSTHANOREQUAL,
    OP_GREATERTHANOREQUAL,
    OP_MIN,
    OP_MAX,
    OP_WITHIN,

    // crypto
    OP_RIPEMD160,
    OP_SHA1,
    OP_SHA256,
    OP_HASH160,
    OP_HASH256,
    OP_CODESEPARATOR,
    OP_CHECKSIG,
    OP_CHECKSIGVERIFY,
    OP_CHECKMULTISIG,
    OP_CHECKMULTISIGVERIFY,

    // expansion
    OP_NOP1,
    OP_NOP2,
    OP_NOP3,
    OP_NOP4,
    OP_NOP5,
    OP_NOP6,
    OP_NOP7,
    OP_NOP8,
    OP_NOP9,
    OP_NOP10,

    // template matching params
    OP_PUBKEYHASH = 0xfd,
    OP_PUBKEY = 0xfe,

    OP_INVALIDOPCODE = 0xff,
};


class BlockDeserializingException : public runtime_error
{
public:
   BlockDeserializingException(const string &what="")
      : runtime_error(what)
   { }
};


// This class holds only static methods.  
// NOTE:  added default ctor and a few non-static, to support SWIG
//        (-classic SWIG doesn't support static methods)
class BtcUtils
{
public:

   // Block of code to be called by SWIG -- i.e. made available to python
   BtcUtils(void) {}
   BinaryData hash256(BinaryData const & str) {return getHash256(str);}
   BinaryData hash160(BinaryData const & str) {return getHash160(str);}

   static BinaryData        BadAddress_;
   static BinaryData        EmptyHash_;

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData BadAddress(void) { return BadAddress_; }
   static BinaryData EmptyHash(void)  { return EmptyHash_;  }

   /////////////////////////////////////////////////////////////////////////////
   static pair<uint64_t, uint8_t> readVarInt(BinaryRefReader & brr)
   {
      uint64_t outVal;
      uint32_t outLen;
      outVal = readVarInt(brr.getCurrPtr(), &outLen);
      brr.advance(outLen);
      return pair<uint64_t, uint8_t>(outVal, (uint8_t)outLen);
   }

   /////////////////////////////////////////////////////////////////////////////
   static uint64_t readVarInt(uint8_t const * strmPtr, uint32_t* lenOutPtr=NULL)
   {
      uint8_t firstByte = strmPtr[0];

      if(firstByte < 0xfd)
      {
         if(lenOutPtr != NULL) 
            *lenOutPtr = 1;
         return firstByte;
      }
      if(firstByte == 0xfd)
      {
         if(lenOutPtr != NULL) 
            *lenOutPtr = 3;
         return READ_UINT16_LE(strmPtr+1);
         
      }
      else if(firstByte == 0xfe)
      {
         if(lenOutPtr != NULL) 
            *lenOutPtr = 5;
         return READ_UINT32_LE(strmPtr+1);
      }
      else //if(firstByte == 0xff)
      {
         if(lenOutPtr != NULL) 
            *lenOutPtr = 9;
         return READ_UINT64_LE(strmPtr+1);
      }
   }
   /////////////////////////////////////////////////////////////////////////////
   static uint64_t readVarInt(uint8_t const * strmPtr, size_t remaining, uint32_t* lenOutPtr=NULL)
   {
      if (remaining < 1)
         throw BlockDeserializingException();
      uint8_t firstByte = strmPtr[0];

      if(firstByte < 0xfd)
      {
         if(lenOutPtr != NULL) 
            *lenOutPtr = 1;
         return firstByte;
      }
      if(firstByte == 0xfd)
      {
         if (remaining < 3)
            throw BlockDeserializingException();
         if(lenOutPtr != NULL) 
            *lenOutPtr = 3;
         return READ_UINT16_LE(strmPtr+1);
         
      }
      else if(firstByte == 0xfe)
      {
         if (remaining < 5)
            throw BlockDeserializingException();
         if(lenOutPtr != NULL) 
            *lenOutPtr = 5;
         return READ_UINT32_LE(strmPtr+1);
      }
      else //if(firstByte == 0xff)
      {
         if (remaining < 9)
            throw BlockDeserializingException();
         if(lenOutPtr != NULL) 
            *lenOutPtr = 9;
         return READ_UINT64_LE(strmPtr+1);
      }
   }

   
   /////////////////////////////////////////////////////////////////////////////
   static inline uint32_t readVarIntLength(uint8_t const * strmPtr)
   {
      uint8_t firstByte = strmPtr[0];
      if(firstByte < 0xfd)
         return 1;

      switch(firstByte)
      {
         case 0xfd: return 3;
         case 0xfe: return 5;
         case 0xff: return 9;
      }
      return -1; // we should never get here
   }

   /////////////////////////////////////////////////////////////////////////////
   static inline uint32_t calcVarIntSize(uint64_t regularInteger)
   {
      if(regularInteger < 0xfd)
         return 1;
      else if(regularInteger <= 0xffff)
         return 3;
      else if(regularInteger <= 0xffffffff)
         return 5;
      else
         return 9;
   }


   /////////////////////////////////////////////////////////////////////////////
   static uint64_t GetFileSize(char const * filename)
   {
      return GetFileSize(string(filename));
   }

   /////////////////////////////////////////////////////////////////////////////
   static uint64_t GetFileSize(string filename)
   {
      ifstream is(OS_TranslatePath(filename.c_str()), ios::in|ios::binary);
      if(!is.is_open())
         return FILE_DOES_NOT_EXIST;
   
      is.seekg(0, ios::end);
      uint64_t filesize = (size_t)is.tellg();
      is.close();
      return filesize;
   }


   /////////////////////////////////////////////////////////////////////////////
   static string numToStrWCommas(int64_t fullNum)
   {
      uint64_t num = fullNum;
      num *= (fullNum < 0 ? -1 : 1);
      vector<uint32_t> triplets;
      do
      {
         int bottom3 = (num % 1000);
         triplets.push_back( bottom3 );
         num = (num - bottom3) / 1000;
      } while(num>=1);

      
      stringstream out;
      out << (fullNum < 0 ? "-" : "");
      uint32_t nt = triplets.size()-1;
      char t[4];
      for(uint32_t i=0; i<=nt; i++)
      {
         if(i==0) 
            sprintf(t, "%d",   triplets[nt-i]); 
         else     
            sprintf(t, "%03d", triplets[nt-i]); 
         out << string(t);
         
         if(i != nt)
            out << ",";
      }
      return out.str();
   }


   /////////////////////////////////////////////////////////////////////////////
   static BinaryData PackBits(list<bool> const & vectBool)
   {
      BinaryData out( (vectBool.size()+7) / 8 );
      for(uint32_t i=0; i<out.getSize(); i++)
         out[i] = 0;

      uint32_t i=0;
      list<bool>::const_iterator iter;
      for(iter  = vectBool.begin();
          iter != vectBool.end();
          iter++, i++)
      {
         if(*iter)
            out[i/8] |= (1<<(7-i%8));
      }
      return out;
   }

   /////////////////////////////////////////////////////////////////////////////
   static list<bool> UnpackBits(BinaryData bits, uint32_t nBits)
   {
      list<bool> out;
      for(uint32_t i=0; i<nBits; i++)
      {
         uint8_t bit = bits[i/8] & (1 << (7-i%8));
         out.push_back(bit>0);
      }
      return out;
   }


   /////////////////////////////////////////////////////////////////////////////
   static void getHash256(uint8_t const * strToHash,
                          uint32_t        nBytes,
                          BinaryData &    hashOutput)
   {
      CryptoPP::SHA256 sha256_;
      if(hashOutput.getSize() != 32)
         hashOutput.resize(32);

      sha256_.CalculateDigest(hashOutput.getPtr(), strToHash, nBytes);
      sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);
   }

   /////////////////////////////////////////////////////////////////////////////
   static void getHash256_NoSafetyCheck(
                          uint8_t const * strToHash,
                          uint32_t        nBytes,
                          BinaryData &    hashOutput)
   {
      CryptoPP::SHA256 sha256_;

      sha256_.CalculateDigest(hashOutput.getPtr(), strToHash, nBytes);
      sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);
   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getHash256(uint8_t const * strToHash,
                                uint32_t        nBytes)
   {
      CryptoPP::SHA256 sha256_;

      BinaryData hashOutput(32);
      sha256_.CalculateDigest(hashOutput.getPtr(), strToHash, nBytes);
      sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);
      return hashOutput;
   }

   /////////////////////////////////////////////////////////////////////////////
   static void getHash256(BinaryData const & strToHash, 
                          BinaryData &       hashOutput)
   {
      getHash256(strToHash.getPtr(), strToHash.getSize(), hashOutput);
   }

   /////////////////////////////////////////////////////////////////////////////
   static void getHash256(BinaryDataRef strToHash, 
                          BinaryData &  hashOutput)
   {
      getHash256(strToHash.getPtr(), strToHash.getSize(), hashOutput);
   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getHash256(BinaryData const & strToHash)
   {
      BinaryData hashOutput(32);
      getHash256(strToHash.getPtr(), strToHash.getSize(), hashOutput);
      return hashOutput;
   }


   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getHash256(BinaryDataRef strToHash)
   {
      BinaryData hashOutput(32);
      getHash256(strToHash.getPtr(), strToHash.getSize(), hashOutput);
      return hashOutput;
   }

   /////////////////////////////////////////////////////////////////////////////
   static void getHash160(uint8_t const * strToHash,
                          uint32_t        nBytes,
                          BinaryData &    hashOutput)
   {
      CryptoPP::SHA256 sha256_;
      CryptoPP::RIPEMD160 ripemd160_;
      BinaryData bd32(32);
      if(hashOutput.getSize() != 20)
         hashOutput.resize(20);

      sha256_.CalculateDigest(bd32.getPtr(), strToHash, nBytes);
      ripemd160_.CalculateDigest(hashOutput.getPtr(), bd32.getPtr(), 32);
   }

   /////////////////////////////////////////////////////////////////////////////
   static void getHash160_NoSafetyCheck(
                          uint8_t const * strToHash,
                          uint32_t        nBytes,
                          BinaryData &    hashOutput)
   {
      CryptoPP::SHA256 sha256_;
      CryptoPP::RIPEMD160 ripemd160_;
      BinaryData bd32(32);

      sha256_.CalculateDigest(bd32.getPtr(), strToHash, nBytes);
      ripemd160_.CalculateDigest(hashOutput.getPtr(), bd32.getPtr(), 32);

   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getHash160(uint8_t const * strToHash,
                                uint32_t        nBytes)
                          
   {
      BinaryData hashOutput(20);
      getHash160(strToHash, nBytes, hashOutput);
      return hashOutput;
   }

   /////////////////////////////////////////////////////////////////////////////
   static void getHash160(BinaryDataRef strToHash,
                          BinaryData &  hashOutput)
   {
      getHash160(strToHash.getPtr(), strToHash.getSize(), hashOutput);
   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getHash160(BinaryDataRef strToHash)
   {
      BinaryData hashOutput(20);
      getHash160(strToHash.getPtr(), strToHash.getSize(), hashOutput);
      return hashOutput;
   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getHash160(BinaryData const & strToHash)
   {
      BinaryData hashOutput(20);
      getHash160(strToHash.getPtr(), strToHash.getSize(), hashOutput);
      return hashOutput;
   }


   /////////////////////////////////////////////////////////////////////////////
   //  I need a non-static, non-overloaded method to be able to use this in SWIG
   BinaryData getHash160_SWIG(BinaryData const & strToHash)
   {
      return getHash160(strToHash);
   }

   /////////////////////////////////////////////////////////////////////////////
   //  I need a non-static, non-overloaded method to be able to use this in SWIG
   BinaryData ripemd160_SWIG(BinaryData const & strToHash)
   {
      CryptoPP::RIPEMD160 ripemd160_;
      BinaryData bd20(20);

      ripemd160_.CalculateDigest(bd20.getPtr(), strToHash.getPtr(), strToHash.getSize());
      return bd20;
   }


   /////////////////////////////////////////////////////////////////////////////
   static BinaryData calculateMerkleRoot(vector<BinaryData> const & txhashlist)
   {
      vector<BinaryData> mtree = calculateMerkleTree(txhashlist);
      return mtree[mtree.size()-1];
   }

   /////////////////////////////////////////////////////////////////////////////
   static vector<BinaryData> calculateMerkleTree(vector<BinaryData> const & txhashlist)
   {
      // Don't know in advance how big this list will be, make a list too big
      // and copy the result to the right size list afterwards
      uint32_t numTx = txhashlist.size();
      vector<BinaryData> merkleTree(3*numTx);
      CryptoPP::SHA256 sha256_;
      BinaryData hashInput(64);
      BinaryData hashOutput(32);
   
      for(uint32_t i=0; i<numTx; i++)
         merkleTree[i] = txhashlist[i];
   
      uint32_t thisLevelStart = 0;
      uint32_t nextLevelStart = numTx;
      uint32_t levelSize = numTx;
      while(levelSize>1)
      {
         for(uint32_t j=0; j<(levelSize+1)/2; j++)
         {
            uint8_t* half1Ptr = hashInput.getPtr();
            uint8_t* half2Ptr = hashInput.getPtr()+32;
         
            if(j < levelSize/2)
            {
               merkleTree[thisLevelStart+(2*j)  ].copyTo(half1Ptr, 32);
               merkleTree[thisLevelStart+(2*j)+1].copyTo(half2Ptr, 32);
            }
            else 
            {
               merkleTree[nextLevelStart-1].copyTo(half1Ptr, 32);
               merkleTree[nextLevelStart-1].copyTo(half2Ptr, 32);
            }
            
            sha256_.CalculateDigest(hashOutput.getPtr(), hashInput.getPtr(),  64);
            sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);
            merkleTree[nextLevelStart+j] = hashOutput;
         }
         levelSize = (levelSize+1)/2;
         thisLevelStart = nextLevelStart;
         nextLevelStart = nextLevelStart+levelSize;
      }

      // nextLevelStart is the size of the merkle tree
      merkleTree.erase(merkleTree.begin()+nextLevelStart, merkleTree.end());
      return merkleTree;
   
   }
   
   /////////////////////////////////////////////////////////////////////////////
   // ALL THESE METHODS ASSUME THERE IS A FULL TX/TXIN/TXOUT BEHIND THE PTR
   // The point of these methods is to calculate the length of the object,
   // hence we don't know in advance how big the object actually will be, so
   // we can't provide it as an input for safety checking...
   static uint32_t TxInCalcLength(uint8_t const * ptr)
   {
      uint32_t viLen;
      uint32_t scrLen = (uint32_t)readVarInt(ptr+36, &viLen);
      return (36 + viLen + scrLen + 4);
   }
   
   static uint32_t TxInCalcLength(uint8_t const * ptr, uint32_t size)
   {
      if (size < 37)
        throw BlockDeserializingException();
      uint32_t viLen;
      uint32_t scrLen = (uint32_t)readVarInt(ptr+36, size-36, &viLen);
      return (36 + viLen + scrLen + 4);
   }

   /////////////////////////////////////////////////////////////////////////////
   static uint32_t TxOutCalcLength(uint8_t const * ptr)
   {
      uint32_t viLen;
      uint32_t scrLen = (uint32_t)readVarInt(ptr+8, &viLen);
      return (8 + viLen + scrLen);
   }
   
   /////////////////////////////////////////////////////////////////////////////
   static uint32_t TxOutCalcLength(uint8_t const * ptr, uint32_t size)
   {
      if (size < 9)
        throw BlockDeserializingException();
      uint32_t viLen;
      uint32_t scrLen = (uint32_t)readVarInt(ptr+8, size-8, &viLen);
      return (8 + viLen + scrLen);
   }

   /////////////////////////////////////////////////////////////////////////////
   static uint32_t TxCalcLength(uint8_t const * ptr,
                                uint32_t size,
                                vector<uint32_t> * offsetsIn=NULL,
                                vector<uint32_t> * offsetsOut=NULL)
   {
      BinaryRefReader brr(ptr, size);  
      
      if (brr.getSizeRemaining() < 4)
         throw BlockDeserializingException();
      // Tx Version;
      brr.advance(4);

      // TxIn List
      uint32_t nIn = (uint32_t)brr.get_var_int();
      if(offsetsIn != NULL)
      {
         offsetsIn->resize(nIn+1);
         for(uint32_t i=0; i<nIn; i++)
         {
            (*offsetsIn)[i] = brr.getPosition();
            brr.advance( TxInCalcLength(brr.getCurrPtr(), brr.getSizeRemaining()) );
         }
         (*offsetsIn)[nIn] = brr.getPosition(); // Get the end of the last
      }
      else
      {
         // Don't need to track the offsets, just leap over everything
         for(uint32_t i=0; i<nIn; i++)
            brr.advance( TxInCalcLength(brr.getCurrPtr(), brr.getSizeRemaining()) );
      }

      // Now extract the TxOut list
      uint32_t nOut = (uint32_t)brr.get_var_int();
      if(offsetsOut != NULL)
      {
         offsetsOut->resize(nOut+1);
         for(uint32_t i=0; i<nOut; i++)
         {
            (*offsetsOut)[i] = brr.getPosition();
            brr.advance( TxOutCalcLength(brr.getCurrPtr(), brr.getSizeRemaining()) );
         }
         (*offsetsOut)[nOut] = brr.getPosition();
      }
      else
      {
         for(uint32_t i=0; i<nOut; i++)
            brr.advance( TxOutCalcLength(brr.getCurrPtr(), brr.getSizeRemaining()) );
      }
      brr.advance(4);

      return brr.getPosition();
   }


   /////////////////////////////////////////////////////////////////////////////
   static uint32_t StoredTxCalcLength( 
                                uint8_t const * ptr,
                                bool fragged,
                                vector<uint32_t> * offsetsIn=NULL,
                                vector<uint32_t> * offsetsOut=NULL)
   {
      BinaryRefReader brr(ptr);  

      
      // Tx Version;
      brr.advance(4);

      // TxIn List
      uint32_t nIn = (uint32_t)brr.get_var_int();
      if(offsetsIn != NULL)
      {
         offsetsIn->resize(nIn+1);
         for(uint32_t i=0; i<nIn; i++)
         {
            (*offsetsIn)[i] = brr.getPosition();
            brr.advance( TxInCalcLength(brr.getCurrPtr()) );
         }
         (*offsetsIn)[nIn] = brr.getPosition(); // Get the end of the last
      }
      else
      {
         // Don't need to track the offsets, just leap over everything
         for(uint32_t i=0; i<nIn; i++)
            brr.advance( TxInCalcLength(brr.getCurrPtr()) );
      }

      // Now extract the TxOut list
      uint32_t nOut = (uint32_t)brr.get_var_int();

      if(fragged)
      {
         offsetsOut->resize(nOut+1);
         for(uint32_t i=0; i<nOut+1; i++)
            (*offsetsOut)[i] = brr.getPosition();
      }
      else
      {
         // Now extract the TxOut list
         if(offsetsOut != NULL)
         {
            offsetsOut->resize(nOut+1);
            for(uint32_t i=0; i<nOut; i++)
            {
               (*offsetsOut)[i] = brr.getPosition();
               brr.advance( TxOutCalcLength(brr.getCurrPtr()) );
            }
            (*offsetsOut)[nOut] = brr.getPosition();
         }
         else
         {
            for(uint32_t i=0; i<nOut; i++)
               brr.advance( TxOutCalcLength(brr.getCurrPtr()) );
         }
      }
      brr.advance(4);

      return brr.getPosition();
   }


   /////////////////////////////////////////////////////////////////////////////
   // TXOUT_SCRIPT_STDHASH160,
   // TXOUT_SCRIPT_STDPUBKEY65,
   // TXOUT_SCRIPT_STDPUBKEY33,
   // TXOUT_SCRIPT_MULTISIG,
   // TXOUT_SCRIPT_P2SH,
   // TXOUT_SCRIPT_NONSTANDARD,
   static TXOUT_SCRIPT_TYPE getTxOutScriptType(BinaryDataRef s)
   {
      uint32_t sz = s.getSize();
      if(sz < 23) 
         return TXOUT_SCRIPT_NONSTANDARD;
      else if( sz      == 25   &&
               s[0]    == 0x76 && 
               s[1]    == 0xa9 &&
               s[2]    == 0x14 &&  
               s[-2]   == 0x88 &&
               s[-1]   == 0xac   )
         return TXOUT_SCRIPT_STDHASH160;
      else if( sz      == 67   &&
               s[0]    == 0x41 &&
               s[1]    == 0x04 &&
               s[-1]   == 0xac)
         return TXOUT_SCRIPT_STDPUBKEY65;
      else if( sz      == 35   &&
               s[0]    == 0x21 &&
              (s[1]    == 0x02 || s[1] == 0x03) &&
               s[-1]   == 0xac)
         return TXOUT_SCRIPT_STDPUBKEY33;
      else if( sz      == 23   &&
               s[0]    == 0xa9 &&
               s[1]    == 0x14 &&
               s[-1]   == 0x87)
         return TXOUT_SCRIPT_P2SH;
      else if( s[-1]   == 0xae && isMultisigScript(s))
         return TXOUT_SCRIPT_MULTISIG;
      else 
         return TXOUT_SCRIPT_NONSTANDARD;
   }

   /////////////////////////////////////////////////////////////////////////////
   // TXIN_SCRIPT_STDUNCOMPR
   // TXIN_SCRIPT_STDCOMPR
   // TXIN_SCRIPT_COINBASE
   // TXIN_SCRIPT_SPENDPUBKEY
   // TXIN_SCRIPT_SPENDMULTI
   // TXIN_SCRIPT_SPENDP2SH
   // TXIN_SCRIPT_NONSTANDARD
   static TXIN_SCRIPT_TYPE getTxInScriptType(BinaryDataRef script,
                                             BinaryDataRef prevTxHash)
   {
      if(script.getSize() == 0)
         return TXIN_SCRIPT_NONSTANDARD;

      if(prevTxHash == BtcUtils::EmptyHash_)
         return TXIN_SCRIPT_COINBASE;

      // Technically, this doesn't recognize all P2SH spends.  Only 
      // spends of P2SH scripts that are, themselves, standard
      BinaryData lastPush = getLastPushDataInScript(script);
      if(getTxOutScriptType(lastPush) != TXOUT_SCRIPT_NONSTANDARD)
         return TXIN_SCRIPT_SPENDP2SH;

      if(script[0]==0x00)
      {
         // TODO: All this complexity to check TxIn type may be too slow when 
         //       scanning the blockchain...will need to investigate later
         vector<BinaryDataRef> splitScr = splitPushOnlyScriptRefs(script);
   
         if(splitScr.size() == 0)
            return TXIN_SCRIPT_NONSTANDARD;

         // TODO: Maybe should identify whether the other pushed data
         //       in the script is a potential solution for the 
         //       subscript... meh?
         //BinaryDataRef lastObj = splitScr[splitScr.size() - 1];

         if(script[2]==0x30 && script[4]==0x02)
            return TXIN_SCRIPT_SPENDMULTI;
      }
         

      if( !(script[1]==0x30 && script[3]==0x02) )
         return TXIN_SCRIPT_NONSTANDARD;

      uint32_t sigSize = script[2] + 4;

      if(script.getSize() == sigSize)
         return TXIN_SCRIPT_SPENDPUBKEY;

      uint32_t keySizeFull = 66;  // \x41 \x04 [X32] [Y32] 
      uint32_t keySizeCompr= 34;  // \x41 \x02 [X32]

      if(script.getSize() == sigSize + keySizeFull)
         return TXIN_SCRIPT_STDUNCOMPR;
      else if(script.getSize() == sigSize + keySizeCompr)
         return TXIN_SCRIPT_STDCOMPR;

      return TXIN_SCRIPT_NONSTANDARD;
   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getTxOutRecipientAddr(BinaryDataRef const & script, 
                                           TXOUT_SCRIPT_TYPE type=TXOUT_SCRIPT_NONSTANDARD)
   {
      if(type==TXOUT_SCRIPT_NONSTANDARD)
         type = getTxOutScriptType(script);
      switch(type)
      {
         case(TXOUT_SCRIPT_STDHASH160):  return script.getSliceCopy(3,20);
         case(TXOUT_SCRIPT_STDPUBKEY65): return getHash160(script.getSliceRef(1,65));
         case(TXOUT_SCRIPT_STDPUBKEY33): return getHash160(script.getSliceRef(1,33));
         case(TXOUT_SCRIPT_P2SH):        return script.getSliceCopy(2,20);
         case(TXOUT_SCRIPT_MULTISIG):    return BadAddress_;
         case(TXOUT_SCRIPT_NONSTANDARD): return BadAddress_;
         default:                        return BadAddress_;
      }
   }

   /////////////////////////////////////////////////////////////////////////////
   // We use this for LevelDB keys, to return same key if the same priv/pub 
   // pair is used, and also saving a few bytes for common script types
   static BinaryData getTxOutScrAddr(BinaryDataRef script, 
                                    TXOUT_SCRIPT_TYPE type=TXOUT_SCRIPT_NONSTANDARD)
   {
      BinaryWriter bw; 
      if(type==TXOUT_SCRIPT_NONSTANDARD)
         type = getTxOutScriptType(script);
      switch(type)
      {
         case(TXOUT_SCRIPT_STDHASH160):  
            bw.put_uint8_t(SCRIPT_PREFIX_HASH160);
            bw.put_BinaryData(script.getSliceCopy(3,20));
            return bw.getData();
         case(TXOUT_SCRIPT_STDPUBKEY65): 
            bw.put_uint8_t(SCRIPT_PREFIX_HASH160);
            bw.put_BinaryData( getHash160(script.getSliceRef(1,65)));
            return bw.getData();
         case(TXOUT_SCRIPT_STDPUBKEY33): 
            bw.put_uint8_t(SCRIPT_PREFIX_HASH160);
            bw.put_BinaryData( getHash160(script.getSliceRef(1,33)));
            return bw.getData();
         case(TXOUT_SCRIPT_P2SH):       
            bw.put_uint8_t(SCRIPT_PREFIX_P2SH);
            bw.put_BinaryData(script.getSliceCopy(2,20));
            return bw.getData();
         case(TXOUT_SCRIPT_NONSTANDARD):     
            bw.put_uint8_t(SCRIPT_PREFIX_NONSTD);
            bw.put_BinaryData(getHash160(script));
            return bw.getData();
         case(TXOUT_SCRIPT_MULTISIG):     
            bw.put_uint8_t(SCRIPT_PREFIX_MULTISIG);
            bw.put_BinaryData(getMultisigUniqueKey(script));
            return bw.getData();
         default:
            LOGERR << "What kind of TxOutScript did we get?";
            return BinaryData(0);
      }
   }

   /////////////////////////////////////////////////////////////////////////////
   // This is basically just for SWIG to access via python
   static BinaryData getScrAddrForScript(BinaryData const & script)
   {
      return getTxOutScrAddr(script.getRef());
   }

   /////////////////////////////////////////////////////////////////////////////
   // This is basically just for SWIG to access via python
   static uint32_t getTxOutScriptTypeInt(BinaryData const & script)
   {
      return (uint32_t)getTxOutScriptType(script.getRef());
   }

   /////////////////////////////////////////////////////////////////////////////
   // This is basically just for SWIG to access via python
   static uint32_t getTxInScriptTypeInt(BinaryData const & script,
                                        BinaryData const & prevHash)
   {
      return (uint32_t)getTxInScriptType(script.getRef(), prevHash);
   }

   /////////////////////////////////////////////////////////////////////////////
   static bool isMultisigScript(BinaryDataRef script)
   {
      return (getMultisigUniqueKey(script).getSize() > 0);
   }

   /////////////////////////////////////////////////////////////////////////////
   //        "UniqueKey"=="ScrAddr" minus prefix
   // TODO:  Interesting exercise:  is there a non-standard script that could
   //        look like the output of this function operating on a multisig 
   //        script (doesn't matter if it's valid or not)?  In other words, is
   //        there is a hole where someone could mine a script that would be
   //        forwarded by Bitcoin-Qt to this code, which would then produce
   //        a non-std-unique-key that would be indistinguishable from the 
   //        output of this function?  My guess is, no.  And my guess is that 
   //        it's not a very useful even if it did.  But it would be good to
   //        rule it out.
   static BinaryData getMultisigUniqueKey(BinaryData const & script)
   {

      vector<BinaryData> a160List(0);

      uint8_t M = getMultisigAddrList(script, a160List);
      uint8_t N = a160List.size();

      if(M==0)
         return BinaryData(0);

      BinaryWriter bw(2 + N*20);  // reserve enough space for header + N addr
      bw.put_uint8_t(M);
      bw.put_uint8_t(N);

      sort(a160List.begin(), a160List.end());
      
      for(uint32_t i=0; i<a160List.size(); i++)
         bw.put_BinaryData(a160List[i]);

      return bw.getData();
   }


   /////////////////////////////////////////////////////////////////////////////
   // Returns M in M-of-N.  Use addr160List.size() for N.  Output is sorted.
   static uint8_t getMultisigAddrList( BinaryData const & script, 
                                       vector<BinaryData> & addr160List)
   {

      vector<BinaryData> pkList;
      uint32_t M = getMultisigPubKeyList(script, pkList);
      uint32_t N = pkList.size();
      
      if(M==0)
         return 0;

      addr160List.resize(N);
      for(uint32_t i=0; i<N; i++)
         addr160List[i] = getHash160(pkList[i]);

      return M;
   }


   /////////////////////////////////////////////////////////////////////////////
   // Returns M in M-of-N.  Use pkList.size() for N.  Output is sorted.
   static uint8_t getMultisigPubKeyList( BinaryData const & script, 
                                         vector<BinaryData> & pkList)
   {
      if( script[-1] != 0xae )
         return 0;

      uint8_t M = script[0];
      uint8_t N = script[-2];
      
      if(M<81 || M>96|| N<81 || N>96)
         return 0;

      M -= 80;
      N -= 80;

      BinaryRefReader brr(script);

      brr.advance(1); // Skip over M-value
      pkList.resize(N);
      for(uint8_t i=0; i<N; i++)
      {
         uint8_t nextSz = brr.get_uint8_t();
         if( nextSz != 0x41 && nextSz != 0x21 )
            return 0;

         pkList[i] = brr.get_BinaryDataRef(nextSz);
      }

      return M;
   }


   
   /////////////////////////////////////////////////////////////////////////////
   // These two methods are basically just to make SWIG access easier
   static BinaryData getMultisigAddr160InfoStr( BinaryData const & script)
   {
      vector<BinaryData> outVect;
      uint32_t M = getMultisigAddrList(script, outVect);
      uint32_t N = outVect.size();
      
      BinaryWriter bw(2 + N*20);  // reserve enough space for header + N addr
      bw.put_uint8_t(M);
      bw.put_uint8_t(N);
      for(uint32_t i=0; i<N; i++)
         bw.put_BinaryData(outVect[i]);

      return bw.getData();
   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getMultisigPubKeyInfoStr( BinaryData const & script)
   {
      vector<BinaryData> outVect;
      uint32_t M = getMultisigPubKeyList(script, outVect);
      uint32_t N = outVect.size();
      
      BinaryWriter bw(2 + N*20);  // reserve enough space for header + N addr
      bw.put_uint8_t(M);
      bw.put_uint8_t(N);
      for(uint32_t i=0; i<N; i++)
         bw.put_BinaryData(outVect[i]);

      return bw.getData();
   }

   /////////////////////////////////////////////////////////////////////////////


   /////////////////////////////////////////////////////////////////////////////
   // TXIN_SCRIPT_STDUNCOMPR,
   // TXIN_SCRIPT_STDCOMPR,
   // TXIN_SCRIPT_COINBASE,
   // TXIN_SCRIPT_SPENDPUBKEY,
   // TXIN_SCRIPT_SPENDMULTI,
   // TXIN_SCRIPT_SPENDP2SH,
   // TXIN_SCRIPT_NONSTANDARD
   static BinaryData getTxInAddr(BinaryDataRef script, 
                                 BinaryDataRef prevTxHash,
                                 TXIN_SCRIPT_TYPE type=TXIN_SCRIPT_NONSTANDARD)
   {
      if(type==TXIN_SCRIPT_NONSTANDARD)
         type = getTxInScriptType(script, prevTxHash);

      return getTxInAddrFromType(script, type);
   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getTxInAddrFromType( BinaryDataRef script,
                                          TXIN_SCRIPT_TYPE type)
   {
      switch(type)
      {
         case(TXIN_SCRIPT_STDUNCOMPR):  
            if (script.getSize() < 65)
               throw BlockDeserializingException();
            return getHash160(script.getSliceRef(-65, 65));
         case(TXIN_SCRIPT_STDCOMPR):    
            if (script.getSize() < 33)
               throw BlockDeserializingException();
            return getHash160(script.getSliceRef(-33, 33));
         case(TXIN_SCRIPT_SPENDP2SH):   
         {
            vector<BinaryDataRef> pushVect = splitPushOnlyScriptRefs(script);
            return getHash160(pushVect[pushVect.size()-1]);
         }
         case(TXIN_SCRIPT_COINBASE):    
         case(TXIN_SCRIPT_SPENDPUBKEY):   
         case(TXIN_SCRIPT_SPENDMULTI):   
         case(TXIN_SCRIPT_NONSTANDARD): 
            return BadAddress_;
         default:
            LOGERR << "What kind of TxIn script did we get?";
            return BadAddress_;
      }
   }
   
   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getTxInAddrFromTypeInt( BinaryData const & script,
                                             uint32_t typeInt)
   {
      return getTxInAddrFromType(script.getRef(), (TXIN_SCRIPT_TYPE)typeInt);
   }

   /////////////////////////////////////////////////////////////////////////////
   static vector<BinaryDataRef> splitPushOnlyScriptRefs(BinaryDataRef script)
   {
      list<BinaryDataRef> opList;

      BinaryRefReader brr(script);
      uint8_t nextOp;
      
      while(brr.getSizeRemaining() > 0)
      {
         nextOp = brr.get_uint8_t();
         if(nextOp == 0)
         {
            // Implicit pushdata
            brr.rewind(1);
            opList.push_back(brr.get_BinaryDataRef(1));
         }
         else if(nextOp < 76)
         {
            // Implicit pushdata
            opList.push_back(brr.get_BinaryDataRef(nextOp));
         }
         else if(nextOp == 76)
         {
            uint8_t nb = brr.get_uint8_t();
            opList.push_back( brr.get_BinaryDataRef(nb));
         }
         else if(nextOp == 77)
         {
            uint16_t nb = brr.get_uint16_t();
            opList.push_back( brr.get_BinaryDataRef(nb));
         }
         else if(nextOp == 78)
         {
            uint16_t nb = brr.get_uint32_t();
            opList.push_back( brr.get_BinaryDataRef(nb));
         }
         else if(nextOp > 78 && nextOp < 97 && nextOp !=80)
         {
            brr.rewind(1);
            opList.push_back( brr.get_BinaryDataRef(1));
         }
         else
            return vector<BinaryDataRef>(0);
      }

      vector<BinaryDataRef> vectOut(opList.size());
      list<BinaryDataRef>::iterator iter;
      uint32_t i=0;
      for(iter = opList.begin(); iter != opList.end(); iter++,i++)
         vectOut[i] = *iter;
      return vectOut;
   }


   /////////////////////////////////////////////////////////////////////////////
   static vector<BinaryData> splitPushOnlyScript(BinaryData const & script)
   {
      vector<BinaryDataRef> refs = splitPushOnlyScriptRefs(script);
      vector<BinaryData> out(refs.size());
      for(uint32_t i=0; i<refs.size(); i++)
         out[i].copyFrom(refs[i]);
      return out;
   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getLastPushDataInScript(BinaryData const & script)
   {
      vector<BinaryDataRef> refs = splitPushOnlyScriptRefs(script);
      if(refs.size()==0)
         return BinaryData(0);

      return refs[refs.size() - 1];
   }

   /////////////////////////////////////////////////////////////////////////////
   static double convertDiffBitsToDouble(BinaryData const & diffBitsBinary)
   {
       uint32_t diffBits = READ_UINT32_LE(diffBitsBinary);
       int nShift = (diffBits >> 24) & 0xff;
       double dDiff = (double)0x0000ffff / (double)(diffBits & 0x00ffffff);
   
       while (nShift < 29)
       {
           dDiff *= 256.0;
           nShift++;
       }
       while (nShift > 29)
       {
           dDiff /= 256.0;
           nShift--;
       }
       return dDiff;
   }


   // This got more complicated when Bitcoin-Qt 0.8 switched from
   // blk0001.dat to blocks/blk00000.dat
   static string getBlkFilename(string dir, uint32_t fblkNum)
   {
      /// Update:  It's been enough time since the hardfork that just about 
      //           everyone must've upgraded to 0.8+ by now... remove pre-0.8
      //           compatibility.
      char* fname = new char[1024];
      sprintf(fname, "%s/blk%05d.dat", dir.c_str(), fblkNum);
      string strName(fname);
      delete[] fname;
      return strName;
   }



   static string getOpCodeName(OPCODETYPE opcode)
   {
      switch (opcode)
      {
      // push value
      case OP_0                 : return "OP_0";
      case OP_PUSHDATA1           : return "OP_PUSHDATA1";
      case OP_PUSHDATA2           : return "OP_PUSHDATA2";
      case OP_PUSHDATA4           : return "OP_PUSHDATA4";
      case OP_1NEGATE            : return "OP_1NEGATE";
      case OP_RESERVED            : return "OP_RESERVED";
      case OP_1                 : return "OP_1";
      case OP_2                 : return "OP_2";
      case OP_3                 : return "OP_3";
      case OP_4                 : return "OP_4";
      case OP_5                 : return "OP_5";
      case OP_6                 : return "OP_6";
      case OP_7                 : return "OP_7";
      case OP_8                 : return "OP_8";
      case OP_9                 : return "OP_9";
      case OP_10                : return "OP_10";
      case OP_11                : return "OP_11";
      case OP_12                : return "OP_12";
      case OP_13                : return "OP_13";
      case OP_14                : return "OP_14";
      case OP_15                : return "OP_15";
      case OP_16                : return "OP_16";
   
      // control
      case OP_NOP               : return "OP_NOP";
      case OP_VER               : return "OP_VER";
      case OP_IF                : return "OP_IF";
      case OP_NOTIF              : return "OP_NOTIF";
      case OP_VERIF              : return "OP_VERIF";
      case OP_VERNOTIF            : return "OP_VERNOTIF";
      case OP_ELSE               : return "OP_ELSE";
      case OP_ENDIF              : return "OP_ENDIF";
      case OP_VERIFY             : return "OP_VERIFY";
      case OP_RETURN             : return "OP_RETURN";
   
      // stack ops
      case OP_TOALTSTACK          : return "OP_TOALTSTACK";
      case OP_FROMALTSTACK         : return "OP_FROMALTSTACK";
      case OP_2DROP              : return "OP_2DROP";
      case OP_2DUP               : return "OP_2DUP";
      case OP_3DUP               : return "OP_3DUP";
      case OP_2OVER              : return "OP_2OVER";
      case OP_2ROT               : return "OP_2ROT";
      case OP_2SWAP              : return "OP_2SWAP";
      case OP_IFDUP              : return "OP_IFDUP";
      case OP_DEPTH              : return "OP_DEPTH";
      case OP_DROP               : return "OP_DROP";
      case OP_DUP               : return "OP_DUP";
      case OP_NIP               : return "OP_NIP";
      case OP_OVER               : return "OP_OVER";
      case OP_PICK               : return "OP_PICK";
      case OP_ROLL               : return "OP_ROLL";
      case OP_ROT               : return "OP_ROT";
      case OP_SWAP               : return "OP_SWAP";
      case OP_TUCK               : return "OP_TUCK";
   
      // splice ops
      case OP_CAT               : return "OP_CAT";
      case OP_SUBSTR             : return "OP_SUBSTR";
      case OP_LEFT               : return "OP_LEFT";
      case OP_RIGHT              : return "OP_RIGHT";
      case OP_SIZE               : return "OP_SIZE";
   
      // bit logic
      case OP_INVERT             : return "OP_INVERT";
      case OP_AND               : return "OP_AND";
      case OP_OR                : return "OP_OR";
      case OP_XOR               : return "OP_XOR";
      case OP_EQUAL              : return "OP_EQUAL";
      case OP_EQUALVERIFY         : return "OP_EQUALVERIFY";
      case OP_RESERVED1           : return "OP_RESERVED1";
      case OP_RESERVED2           : return "OP_RESERVED2";
   
      // numeric
      case OP_1ADD               : return "OP_1ADD";
      case OP_1SUB               : return "OP_1SUB";
      case OP_2MUL               : return "OP_2MUL";
      case OP_2DIV               : return "OP_2DIV";
      case OP_NEGATE             : return "OP_NEGATE";
      case OP_ABS               : return "OP_ABS";
      case OP_NOT               : return "OP_NOT";
      case OP_0NOTEQUAL           : return "OP_0NOTEQUAL";
      case OP_ADD               : return "OP_ADD";
      case OP_SUB               : return "OP_SUB";
      case OP_MUL               : return "OP_MUL";
      case OP_DIV               : return "OP_DIV";
      case OP_MOD               : return "OP_MOD";
      case OP_LSHIFT             : return "OP_LSHIFT";
      case OP_RSHIFT             : return "OP_RSHIFT";
      case OP_BOOLAND            : return "OP_BOOLAND";
      case OP_BOOLOR             : return "OP_BOOLOR";
      case OP_NUMEQUAL            : return "OP_NUMEQUAL";
      case OP_NUMEQUALVERIFY       : return "OP_NUMEQUALVERIFY";
      case OP_NUMNOTEQUAL         : return "OP_NUMNOTEQUAL";
      case OP_LESSTHAN            : return "OP_LESSTHAN";
      case OP_GREATERTHAN         : return "OP_GREATERTHAN";
      case OP_LESSTHANOREQUAL      : return "OP_LESSTHANOREQUAL";
      case OP_GREATERTHANOREQUAL    : return "OP_GREATERTHANOREQUAL";
      case OP_MIN               : return "OP_MIN";
      case OP_MAX               : return "OP_MAX";
      case OP_WITHIN             : return "OP_WITHIN";
   
      // crypto
      case OP_RIPEMD160           : return "OP_RIPEMD160";
      case OP_SHA1               : return "OP_SHA1";
      case OP_SHA256             : return "OP_SHA256";
      case OP_HASH160            : return "OP_HASH160";
      case OP_HASH256            : return "OP_HASH256";
      case OP_CODESEPARATOR        : return "OP_CODESEPARATOR";
      case OP_CHECKSIG            : return "OP_CHECKSIG";
      case OP_CHECKSIGVERIFY       : return "OP_CHECKSIGVERIFY";
      case OP_CHECKMULTISIG        : return "OP_CHECKMULTISIG";
      case OP_CHECKMULTISIGVERIFY   : return "OP_CHECKMULTISIGVERIFY";
   
      // expanson
      case OP_NOP1               : return "OP_NOP1";
      case OP_NOP2               : return "OP_NOP2";
      case OP_NOP3               : return "OP_NOP3";
      case OP_NOP4               : return "OP_NOP4";
      case OP_NOP5               : return "OP_NOP5";
      case OP_NOP6               : return "OP_NOP6";
      case OP_NOP7               : return "OP_NOP7";
      case OP_NOP8               : return "OP_NOP8";
      case OP_NOP9               : return "OP_NOP9";
      case OP_NOP10              : return "OP_NOP10";
   
   
   
      // template matching params
      case OP_PUBKEYHASH          : return "OP_PUBKEYHASH";
      case OP_PUBKEY             : return "OP_PUBKEY";
   
      case OP_INVALIDOPCODE        : return "OP_INVALIDOPCODE";
      default:
         return "OP_UNKNOWN";
      }
   }
   
   static vector<string> convertScriptToOpStrings(BinaryData const & script)
   {
      list<string> opList;

      uint32_t i = 0;
      uint32_t sz=script.getSize();
      bool error=false;
      while(i < sz)
      {
         uint8_t nextOp = script[i];
         if(nextOp == 0)
         {
            opList.push_back("OP_0");
            i++;
         }
         else if(nextOp < 76)
         {
            opList.push_back("[PUSHDATA -- " + num2str(nextOp) + " BYTES:]");
            opList.push_back(script.getSliceCopy(i+1, nextOp).toHexStr());
            i += nextOp+1;
         }
         else if(nextOp == 76)
         {
            uint8_t nb = READ_UINT8_LE(script.getPtr() + i+1);
            if(i+1+1+nb > sz) { error=true; break; }
            BinaryData binObj = script.getSliceCopy(i+2, nb);
            opList.push_back("[OP_PUSHDATA1 -- " + num2str(nb) + " BYTES:]");
            opList.push_back(binObj.toHexStr());
            i += nb+2;
         }
         else if(nextOp == 77)
         {
            uint16_t nb = READ_UINT16_LE(script.getPtr() + i+1);
            if(i+1+2+nb > sz) { error=true; break; }
            BinaryData binObj = script.getSliceCopy(i+3, min((int)nb,256));
            opList.push_back("[OP_PUSHDATA2 -- " + num2str(nb) + " BYTES:]");
            opList.push_back(binObj.toHexStr() + "...");
            i += nb+3;
         }
         else if(nextOp == 78)
         {
            uint32_t nb = READ_UINT32_LE(script.getPtr() + i+1);
            if(i+1+4+nb > sz) { error=true; break; }
            BinaryData binObj = script.getSliceCopy(i+5, min((int)nb,256));
            opList.push_back("[OP_PUSHDATA4 -- " + num2str(nb) + " BYTES:]");
            opList.push_back(binObj.toHexStr() + "...");
            i += nb+5;
         }
         else
         {
            opList.push_back(getOpCodeName((OPCODETYPE)nextOp));
            i++;
         }
            
      }

      if(error)
      {
         opList.clear();
         opList.push_back("ERROR PROCESSING SCRIPT");
      }

      uint32_t nops = opList.size();
      vector<string> vectOut(nops);
      list<string>::iterator iter;
      uint32_t op=0;
      for(iter = opList.begin(); iter != opList.end(); iter++)
      {
         vectOut[op] = *iter;
         op++;
      }
      return vectOut;
   }
   
   static string num2str(uint64_t n)
   {
      stringstream out;
      out << n;
      return out.str();
   }
   
   static void pprintScript(BinaryData const & script)
   {
      vector<string> oplist = convertScriptToOpStrings(script);
      for(uint32_t i=0; i<oplist.size(); i++)
         cout << "   " << oplist[i] << endl;
   }


   /////////////////////////////////////////////////////////////////////////////
   // Simple method for copying files (works in all OS, probably not efficient)
   static bool copyFile(string src, string dst, uint32_t nbytes=UINT32_MAX)
   {
      uint64_t srcsz = GetFileSize(src);
      if(srcsz == FILE_DOES_NOT_EXIST)
         return false;

      srcsz = min((uint32_t)srcsz, nbytes);
   
      BinaryData temp((size_t)srcsz);
      ifstream is(src.c_str(), ios::in  | ios::binary);
      is.read((char*)temp.getPtr(), srcsz);
      is.close();
   
      ofstream os(dst.c_str(), ios::out | ios::binary);
      os.write((char*)temp.getPtr(), srcsz);
      os.close();
      return true;
   }

   /////////////////////////////////////////////////////////////////////////////
   // Simple method for copying files (works in all OS, probably not efficient)
   static bool appendFile(string src, string dst)
   {
      uint64_t srcsz = GetFileSize(src);
      if(srcsz == FILE_DOES_NOT_EXIST)
         return false;
   
      BinaryData temp((size_t)srcsz);
      ifstream is(src.c_str(), ios::in  | ios::binary);
      is.read((char*)temp.getPtr(), srcsz);
      is.close();
   
      ofstream os(dst.c_str(), ios::app | ios::binary);
      os.write((char*)temp.getPtr(), srcsz);
      os.close();
      return true;
   }


   /*
   static bool verifyProofOfWork(BinaryDataRef bh80)
   {
      BinaryData theHash = getHash256(bh80);
      return verifyProofOfWork(bh80, theHash.getRef());
   }

   static bool verifyProofOfWork(BinaryData bh80,
                                 BinaryData const & theHash)
   {
      return verifyProofOfWork(bh80.getRef(), theHash.getRef());
   }

   static bool verifyProofOfWork(BinaryDataRef bh80, BinaryDataRef bhrHash)
   {
      // This is only approximate.  I can put in an exact verifier once 
      // I figure out big integers better in C++, or another way to do
      // the calculation.  I just want to make sure this isn't a completely
      // bogus proof of work.
      double diff = convertDiffBitsToDouble( BinaryDataRef(bh80.getPtr()+72, 4) );
      double diffFactor = diff * (double)UINT32_MAX;
      double nZeroBits  = int( log(diffFactor) / log(2.0));
      int    nZeroBytes = int( log(diffFactor) / log(2.0) / 8.0);

      // TODO: check that I'm comparing the correct end of the hash
      for(uint32_t i=0; i<nZeroBytes; i++)
         if(bhrHash[31-i]!=0)
            return false;

      return true;
   }
   */

};
   
   
   


#endif
