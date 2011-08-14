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


//#ifdef MAIN_NETWORK
   #define MAGICBYTES "f9beb4d9"
   #define GENESIS_HASH_HEX "6fe28c0ab6f1b372c1a6a246ae63f74f931e8365e15a089c68d6190000000000"
//#else
   //#define MAGICBYTES "fabfb5da"
   //#define GENESIS_HASH_HEX "08b067b31dc139ee8e7a76a4f2cfcca477c4c06e1ef89f4ae308951907000000"
//#endif


// This class holds only static methods.  
class BtcUtils
{
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
      static CryptoPP::SHA256 sha256_;
      if(hashOutput.getSize() != 32)
         hashOutput.resize(32);

      sha256_.CalculateDigest(hashOutput.getPtr(), strToHash.getPtr(), strToHash.getSize());
      sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);

   }

   /////////////////////////////////////////////////////////////////////////////
   static void getHash256(BinaryDataRef const & strToHash, 
                          BinaryData          & hashOutput)
   {
      static CryptoPP::SHA256 sha256_;
      if(hashOutput.getSize() != 32)
         hashOutput.resize(32);

      sha256_.CalculateDigest(hashOutput.getPtr(), strToHash.getPtr(), strToHash.getSize());
      sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);

   }

   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getHash256(BinaryData const & strToHash)
   {
      static CryptoPP::SHA256 sha256_;
      
      BinaryData hashOutput(32);
      sha256_.CalculateDigest(hashOutput.getPtr(), strToHash.getPtr(), strToHash.getSize());
      sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);
      return hashOutput;
   }


   /////////////////////////////////////////////////////////////////////////////
   static BinaryData getHash256(BinaryDataRef const & strToHash)
   {
      static CryptoPP::SHA256 sha256_;
      
      BinaryData hashOutput(32);
      sha256_.CalculateDigest(hashOutput.getPtr(), strToHash.getPtr(), strToHash.getSize());
      sha256_.CalculateDigest(hashOutput.getPtr(), hashOutput.getPtr(), 32);
      return hashOutput;
   }


   static uint32_t TxInCalcLength(uint8_t const * ptr)
   {
      uint32_t viLen;
      uint32_t scrLen = BtcUtils::readVarInt(getPtr()+36, &viLen);
      return (36 + viLen + scrLen + 4);
   }

   static uint32_t TxOutCalcLength(uint8_t const * ptr)
   {
      uint32_t viLen;
      uint32_t scrLen = BtcUtils::readVarInt(getPtr()+8, &viLen);
      return (8 + viLen + scrLen);
   }

   static uint32_t TxCalcLength(uint8_t const * ptr)
   {
      // Not written yet!
      return 0;
   }
};




#endif
