////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>             //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// This technique is described in Colin Percival's paper on memory-hard 
// key-derivation functions, used to create "scrypt":
//
//       http://www.tarsnap.com/scrypt/scrypt.pdf
//
// The goal is to create a key-derivation function that can force a memory
// requirement on the thread applying the KDF.  By picking a sequence-length
// of 1,000,000, each thread will require 32 MB of memory to compute the keys,
// which completely disarms GPUs of their massive parallelization capabilities
// (for maximum parallelization, the kernel must use less than 1-2 MB/thread)
//
// Even with less than 1e6 sequence length, as long as it requires more than 64
// kB of memory, a GPU will have to store the computed lookup tables in global
// memory, which is extremely slow for random lookup.  As a result, GPUs are 
// no better (and possibly much worse) than a CPU for brute-forcing the passwd
//
// This KDF is actually the ROMIX algorithm described on page 6 of Colin's
// paper.  This was chosen because it is the simplest technique that provably
// achieves the goal of being secure, and memory-hard.
//
// In the future, I may add functionality to try to detect the capabilities of
// the host system, and pick KDF parameters that guarantee at least 0.1s of 
// compute time.  This is what the default client uses right now.
//
//
////////////////////////////////////////////////////////////////////////////////

#ifndef _KDF_ROMIX_H_
#define _KDF_ROMIX_H_

#include <iostream>
#include <vector>
#include <map>
#include <cmath>
#include <algorithm>

#include "cryptlib.h"
#include "sha.h"
#include "BinaryData.h"
#include "BtcUtils.h"
#include "UniversalTimer.h"


using namespace std;

class kdfRomix
{
public:

   /////////////////////////////////////////////////////////////////////////////
   kdfRomix(uint32_t memReqt=1048576, uint32_t numIter=1)
   {
      // SHA512 computes 64-byte outputs
      hashFunctionName_ = "sha512";
      hashOutputBytes_  = 64;
      memoryReqtBytes_  = memReqt;
      sequenceCount_    = memoryReqtBytes_ / hashOutputBytes_;
      numIterations_    = numIter;
      kdfOutputBytes_   = 32;
      lookupTable_.resize(memoryReqtBytes_);
   }


   /////////////////////////////////////////////////////////////////////////////
   void SingleHash(uint8_t  const * inputPtr, 
                   uint32_t const   inputSz, 
                   uint8_t        * outputPtr)
   {
      // ASSUME that the outputPtr has at least 64 bytes allocated
      static CryptoPP::SHA512 sha512_;
      sha512_.CalculateDigest(outputPtr, inputPtr, hashOutputBytes_);
   }
   
   //void getLUTOutput(uint32_t index)
   
   
   /////////////////////////////////////////////////////////////////////////////

   /////////////////////////////////////////////////////////////////////////////
   BinaryData DeriveKeyIteration(BinaryData const & password)
   {
      // First, compute <sequenceCount_> consecutive hashes of the passphrase
      // Every iteration is stored in the next 64-bytes in the Lookup table
      uint32_t const HSZ = hashOutputBytes_;
      uint8_t* frontOfLUT = lookupTable_.getPtr();
      uint8_t* nextRead  = NULL;
      uint8_t* nextWrite = NULL;
      SingleHash(password.getPtr(), password.getSize(), frontOfLUT);
      for(uint32_t nByte=0; nByte<memoryReqtBytes_-HSZ; nByte+=HSZ)
      {
         // Compute hash of slot i, put result in slot i+1
         nextRead  = frontOfLUT + nByte;
         nextWrite = nextRead + hashOutputBytes_;
         SingleHash(nextRead, hashOutputBytes_, nextWrite);
      }

      // LookupTable should be complete, now start lookup sequence.
      // Start with the last hash from the previous step
      BinaryData X(frontOfLUT + memoryReqtBytes_ - HSZ, HSZ);

      // We "integerize" a hash value by taking the last 4 bytes of
      // as a uint32_t, and take modulo sequenceCount
      uint64_t* X64ptr = (uint64_t*)(X.getPtr());
      uint32_t newIndex;
      uint32_t const nXorOps = HSZ/sizeof(uint64_t);
      for(uint32_t nSeq=0; nSeq<sequenceCount_; nSeq++)
      {
         // Interpret last 4 bytes of last result (mod seqCt) as next LUT index
         newIndex = *(uint32_t*)(X.getPtr()+HSZ-4) % sequenceCount_;

         // V represents the hash result at <newIndex>
         uint64_t* V64ptr = (uint64_t*)(frontOfLUT + HSZ*newIndex);

         // xor X with V, and store the result in X
         for(int i=0; i<nXorOps; i++)
            *(X64ptr+i) = *(X64ptr+i) ^ *(V64ptr+i);
         
         // Hash the xor'd data to get the next index for lookup
         SingleHash(X.getPtr(), HSZ, X.getPtr());
      }
      // Truncate the final result to get the final key
      return X.getSliceCopy(0,kdfOutputBytes_);
   }

   /////////////////////////////////////////////////////////////////////////////
   uint32_t computeNumIterationsForTime(uint32_t target_ms)
   {
      BinaryData testKey("This is an example key to test KDF iteration speed");
      TIMER_START("KDF_10_Iterations");
      for(uint32_t i=0; i<10; i++)
         testKey = DeriveKeyIteration(testKey);
      TIMER_STOP("KDF_10_Iterations");

      double tenIters_s = UniversalTimer::instance().read("KDF_10_Iterations");
      numIterations_ = (uint32_t)(target_ms / (tenIters_s*1000.0));
      return (numIterations_ < 1 ? 1 : numIterations_);
   }


   
private:
   uint32_t hashOutputBytes_;
   uint32_t sequenceCount_;
   uint32_t memoryReqtBytes_;
   uint32_t kdfOutputBytes_;    // size of final key data
   string   hashFunctionName_;  // name of hash function to use (not impl)

   uint32_t numIterations_;     // We set the ROMIX params for a given memory 
                                // req't. Then run it numIter times to meet
                                // the computation-time req't
                                
   BinaryData lookupTable_;

};



#endif














