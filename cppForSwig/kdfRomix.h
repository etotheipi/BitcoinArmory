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
   kdfRomix(uint32_t memReqt=256*1024, uint32_t targetComputeMs=250) :
      hashFunctionName_( "sha512" ),
      hashOutputBytes_( 64 ),
      kdfOutputBytes_( 32 )
   {
      // SHA512 computes 64-byte outputs
      setKdfParams(memReqt, targetComputeMs);
   }

   /////////////////////////////////////////////////////////////////////////////
   void setKdfParams(uint32_t memReqt, uint32_t targetComputeMs)
   {
      // Allocate memory for the lookup table
      memoryReqtBytes_  = memReqt;
      sequenceCount_    = memoryReqtBytes_ / hashOutputBytes_;
      lookupTable_.resize(memoryReqtBytes_);

      // Now test the speed of this system and set the number of iterations
      // to run as many iterations as we can in 0.25s (or specified input)
      BinaryData testKey("This is an example key to test KDF iteration speed");
      TIMER_START("KDF_10_Iterations");
      for(uint32_t i=0; i<10; i++)
         testKey = DeriveKey_OneIter(testKey);
      TIMER_STOP("KDF_10_Iterations");

      double tenIters_s = UniversalTimer::instance().read("KDF_10_Iterations");
      uint32_t msPerIter = (uint32_t)(tenIters_s * 100.);
      numIterations_ = (uint32_t)(targetComputeMs / msPerIter);
      numIterations_ = (numIterations_ < 1 ? 1 : numIterations_);
      cout << "System speed test results: " << endl;
      cout << "   10 iterations of the KDF took:  " << tenIters_s*1000 << " ms" << endl;
      cout << "   Target computation time is:     " << targetComputeMs << " ms" << endl;
      cout << "   Setting numIterations to:       " << numIterations_;
   }


   void printKdfParams(void)
   {
      // SHA512 computes 64-byte outputs
      cout << "KDF Parameters:" << endl;
      cout << "   HashFunction : " << hashFunctionName_ << endl;
      cout << "   HashOutBytes : " << hashOutputBytes_ << endl;
      cout << "   MemoryReqts  : " << memoryReqtBytes_ << endl;
      cout << "   SequenceCount: " << sequenceCount_   << endl;
      cout << "   NumIterations: " << numIterations_   << endl;
      cout << "   KDFOutBytes  : " << kdfOutputBytes_  << endl;
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
   BinaryData DeriveKey_OneIter(BinaryData const & password)
   {
      static CryptoPP::SHA512 sha512;

      // First, compute <sequenceCount_> consecutive hashes of the passphrase
      // Every iteration is stored in the next 64-bytes in the Lookup table
      uint32_t const HSZ = hashOutputBytes_;
      lookupTable_.fill(0);
      uint8_t* frontOfLUT = lookupTable_.getPtr();
      uint8_t* nextRead  = NULL;
      uint8_t* nextWrite = NULL;
      sha512.CalculateDigest(frontOfLUT, password.getPtr(), password.getSize());
      for(uint32_t nByte=0; nByte<memoryReqtBytes_-HSZ; nByte+=HSZ)
      {
         // Compute hash of slot i, put result in slot i+1
         nextRead  = frontOfLUT + nByte;
         nextWrite = nextRead + hashOutputBytes_;
         sha512.CalculateDigest(nextWrite, nextRead, hashOutputBytes_);
      }

      // LookupTable should be complete, now start lookup sequence.
      // Start with the last hash from the previous step
      BinaryData X(frontOfLUT + memoryReqtBytes_ - HSZ, HSZ);
      BinaryData Y(HSZ);

      // We "integerize" a hash value by taking the last 4 bytes of
      // as a uint32_t, and take modulo sequenceCount
      uint64_t* X64ptr = (uint64_t*)(X.getPtr());
      uint64_t* Y64ptr = (uint64_t*)(Y.getPtr());
      uint64_t* V64ptr = NULL;
      uint32_t newIndex;
      uint32_t const nXorOps = HSZ/sizeof(uint64_t);
      for(uint32_t nSeq=0; nSeq<sequenceCount_/4; nSeq++)
      {
         // Interpret last 4 bytes of last result (mod seqCt) as next LUT index
         newIndex = *(uint32_t*)(X.getPtr()+HSZ-4) % sequenceCount_;

         // V represents the hash result at <newIndex>
         V64ptr = (uint64_t*)(frontOfLUT + HSZ*newIndex);

         // xor X with V, and store the result in X
         for(int i=0; i<nXorOps; i++)
            *(Y64ptr+i) = *(X64ptr+i) ^ *(V64ptr+i);

         // Hash the xor'd data to get the next index for lookup
         sha512.CalculateDigest(X.getPtr(), Y.getPtr(), HSZ);
      }
      // Truncate the final result to get the final key
      return X.getSliceCopy(0,kdfOutputBytes_);
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData DeriveKey(BinaryData const & password)
   {
      BinaryData masterKey(password);
      for(uint32_t i=0; i<numIterations_; i++)
         masterKey = DeriveKey_OneIter(masterKey);
      
      return masterKey;
   }


   string   getHashFunctionName(void) const { return hashFunctionName_; }
   uint32_t getMemoryReqtBytes(void)  const { return memoryReqtBytes_; }
   uint32_t getNumIterations(void)    const { return numIterations_; }
   
private:
   uint32_t hashOutputBytes_;
   uint32_t sequenceCount_;
   uint32_t memoryReqtBytes_;
   uint32_t kdfOutputBytes_;    // size of final key data
   string   hashFunctionName_;  // name of hash function to use (not impl)
   BinaryData lookupTable_;

   uint32_t numIterations_;     // We set the ROMIX params for a given memory 
                                // req't. Then run it numIter times to meet
                                // the computation-time req't
                                

};



#endif














