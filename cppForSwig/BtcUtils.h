#ifndef _BTCUTILS_H_
#define _BTCUTILS_H_

#include <stdio.h>
#ifdef WIN32
   #include <cstdint>
#else
   #include <stdlib.h>
   #include <inttypes.h>   
   #include <cstring>
#endif

#include <iostream>
#include <vector>
#include <string>
#include <assert.h>

#include "BinaryData.h"
#include "cryptlib.h"
#include "sha.h"
#include "ripemd.h"

#define HEADER_SIZE 80
#define CONVERTBTC 100000000
#define HashString     BinaryData
#define HashStringRef  BinaryDataRef


//#ifdef MAIN_NETWORK
   #define MAGICBYTES "f9beb4d9"
   #define GENESIS_HASH_HEX "6fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000"
//#else
   //#define MAGICBYTES "fabfb5da"
   //#define GENESIS_HASH_HEX "08b067b31dc139ee8e7a76a4f2cfcca477c4c06e1ef89f4ae308951907000000"
//#endif

class BinaryData;
class BinaryDataRef;

typedef enum
{
   TXOUT_SCRIPT_STANDARD,
   TXOUT_SCRIPT_COINBASE,
   TXOUT_SCRIPT_UNKNOWN
}  TXOUT_SCRIPT_TYPE;

typedef enum
{
   TXIN_SCRIPT_STANDARD,
   TXIN_SCRIPT_COINBASE,
   TXIN_SCRIPT_SPENDCB,
   TXIN_SCRIPT_UNKNOWN
}  TXIN_SCRIPT_TYPE;


// This class holds only static methods.  
class BtcUtils
{
public:

   // We should keep the genesis hash handy 
   static BinaryData        BadAddress_;
   static BinaryData        GenesisHash_;
   static BinaryData        EmptyHash_;

   /////////////////////////////////////////////////////////////////////////////
   static uint64_t readVarInt(uint8_t const * strmPtr, uint32_t* lenOutPtr=NULL)
   {
      uint8_t firstByte = strmPtr[0];

      if(firstByte < 0xfd)
      {
         if(lenOutPtr != NULL) 
            *lenOutPtr = 1;
         return (uint64_t)firstByte;
      }
      if(firstByte == 0xfd)
      {
         if(lenOutPtr != NULL) 
            *lenOutPtr = 3;
         return (uint64_t)(*(uint16_t*)(strmPtr + 1));
         
      }
      else if(firstByte == 0xfe)
      {
         if(lenOutPtr != NULL) 
            *lenOutPtr = 5;
         return (uint64_t)(*(uint32_t*)(strmPtr + 1));
      }
      else //if(firstByte == 0xff)
      {
         if(lenOutPtr != NULL) 
            *lenOutPtr = 9;
         return *(uint64_t*)(strmPtr + 1);
      }
   }

   
   static inline uint32_t readVarIntLength(uint8_t const * strmPtr)
   {
      uint8_t firstByte = strmPtr[0];
      switch(firstByte)
      {
         case 0xfd: return 3;
         case 0xfe: return 5;
         case 0xff: return 9;
         default:   return 1;
      }
   }

   /////////////////////////////////////////////////////////////////////////////
   static void getHash256(uint8_t const * strToHash,
                          uint32_t        nBytes,
                          BinaryData &    hashOutput)
   {
      // TODO: Check whether static sha256_ is necessary.  The use of static
      //       MAY prevent this method from being thread-safe
      static CryptoPP::SHA256 sha256_;
      if(hashOutput.getSize() != 32)
         hashOutput.resize(32);

      sha256_.CalculateDigest(hashOutput.getPtr(), strToHash, nBytes);
      sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);
   }


   /////////////////////////////////////////////////////////////////////////////
   static void getHash256(BinaryData const & strToHash, 
                          BinaryData &       hashOutput)
   {
      getHash256(strToHash.getPtr(), strToHash.getSize(), hashOutput);

      //static CryptoPP::SHA256 sha256_;
      //if(hashOutput.getSize() != 32)
         //hashOutput.resize(32);
      //sha256_.CalculateDigest(hashOutput.getPtr(), strToHash.getPtr(), strToHash.getSize());
      //sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);
   }

   /////////////////////////////////////////////////////////////////////////////
   static void getHash256(BinaryDataRef const & strToHash, 
                          BinaryData          & hashOutput)
   {
      getHash256(strToHash.getPtr(), strToHash.getSize(), hashOutput);

      //static CryptoPP::SHA256 sha256_;
      //if(hashOutput.getSize() != 32)
         //hashOutput.resize(32);
      //sha256_.CalculateDigest(hashOutput.getPtr(), strToHash.getPtr(), strToHash.getSize());
      //sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);

   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getHash256(BinaryData const & strToHash)
   {
      BinaryData hashOutput(32);
      getHash256(strToHash.getPtr(), strToHash.getSize(), hashOutput);
      return hashOutput;

      //static CryptoPP::SHA256 sha256_;
      //BinaryData hashOutput(32);
      //sha256_.CalculateDigest(hashOutput.getPtr(), strToHash.getPtr(), strToHash.getSize());
      //sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);
      //return hashOutput;
   }


   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getHash256(BinaryDataRef const & strToHash)
   {
      BinaryData hashOutput(32);
      getHash256(strToHash.getPtr(), strToHash.getSize(), hashOutput);
      return hashOutput;

      //static CryptoPP::SHA256 sha256_;
      //BinaryData hashOutput(32);
      //sha256_.CalculateDigest(hashOutput.getPtr(), strToHash.getPtr(), strToHash.getSize());
      //sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);
      //return hashOutput;
   }

   /////////////////////////////////////////////////////////////////////////////
   static void getHash160(uint8_t const * strToHash,
                          uint32_t        nBytes,
                          BinaryData &    hashOutput)
   {
      // TODO: Check whether static sha256_ is necessary.  The use of static
      //       MAY prevent this method from being thread-safe
      static CryptoPP::SHA256 sha256_;
      static CryptoPP::RIPEMD160 ripemd160_;
      static BinaryData bd32(32);
      if(hashOutput.getSize() != 20)
         hashOutput.resize(20);

      sha256_.CalculateDigest(bd32.getPtr(), strToHash, nBytes);
      ripemd160_.CalculateDigest(hashOutput.getPtr(), bd32.getPtr(), 32);
   }

   /////////////////////////////////////////////////////////////////////////////
   static void getHash160(BinaryDataRef const & strToHash,
                          BinaryData & hashOutput)
   {
      getHash160(strToHash.getPtr(), strToHash.getSize(), hashOutput);
   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getHash160(BinaryDataRef const & strToHash)
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

   /////////////////////////////////////////////////////////////////////////////
   static uint32_t TxOutCalcLength(uint8_t const * ptr)
   {
      uint32_t viLen;
      uint32_t scrLen = (uint32_t)readVarInt(ptr+8, &viLen);
      return (8 + viLen + scrLen);
   }

   /////////////////////////////////////////////////////////////////////////////
   static uint32_t TxCalcLength(uint8_t const * ptr,
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
      brr.advance(4);

      return brr.getPosition();
   }



   /////////////////////////////////////////////////////////////////////////////
   static TXOUT_SCRIPT_TYPE getTxOutScriptType(BinaryDataRef const & s)
   {
      uint32_t sz = s.getSize();
      if(sz < 2) return TXOUT_SCRIPT_UNKNOWN;

      if( s[0]    == 0x76 && 
          s[1]    == 0xa9 &&
          s[sz-2] == 0x88 &&
          s[sz-1] == 0xac    )
         return TXOUT_SCRIPT_STANDARD;

      if(sz==67 && s[0]==0x41 && s[1]==0x04 && s[sz-1]==0xac)
         return TXOUT_SCRIPT_COINBASE;

      return TXOUT_SCRIPT_UNKNOWN;
   }

   /////////////////////////////////////////////////////////////////////////////
   static TXIN_SCRIPT_TYPE getTxInScriptType(BinaryDataRef const & s,
                                             BinaryDataRef const & prevTxHash)
   {
      if(prevTxHash == BtcUtils::EmptyHash_)
         return TXIN_SCRIPT_COINBASE;

      if( !(s[1]==0x30 && s[3]==0x02) )
         return TXIN_SCRIPT_UNKNOWN;

      uint32_t sigSize = s[2] + 4;
      uint32_t keySize = 66;  // \x41 \x04 [X32] [Y32] 

      if(s.getSize() == sigSize)
         return TXIN_SCRIPT_SPENDCB;
      else if(s.getSize() == sigSize + keySize)
         return TXIN_SCRIPT_STANDARD;

      return TXIN_SCRIPT_UNKNOWN;
   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getTxOutRecipientAddr(BinaryDataRef const & script, 
                                           TXOUT_SCRIPT_TYPE type=TXOUT_SCRIPT_UNKNOWN)
   {
      if(type==TXOUT_SCRIPT_UNKNOWN)
         type = getTxOutScriptType(script);
      switch(type)
      {
         case(TXOUT_SCRIPT_STANDARD): return script.getSliceCopy(3,20);
         case(TXOUT_SCRIPT_COINBASE): return getHash160(script.getSliceRef(1,65));
         case(TXOUT_SCRIPT_UNKNOWN):  return BadAddress_;
         default:                     return BadAddress_;
      }
   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getTxInAddr(BinaryDataRef const & script, 
                                 BinaryDataRef const & prevTxHash,
                                 TXIN_SCRIPT_TYPE type=TXIN_SCRIPT_UNKNOWN)
   {
      if(type==TXIN_SCRIPT_UNKNOWN)
         type = getTxInScriptType(script, prevTxHash);
      switch(type)
      {
         case(TXIN_SCRIPT_STANDARD):  return getHash160(script.getSliceRef(-65, 65));
         case(TXIN_SCRIPT_COINBASE):
         case(TXIN_SCRIPT_SPENDCB):   
         case(TXIN_SCRIPT_UNKNOWN):   
         default:                     return BadAddress_;
      }
   }

   /////////////////////////////////////////////////////////////////////////////
   static double convertDiffBitsToDouble(BinaryData const & diffBitsBinary)
   {
       uint32_t diffBits = *(uint32_t*)(diffBitsBinary.getPtr());
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

};




#endif
