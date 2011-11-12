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

#ifndef _ENCRYPTION_UTILS_
#define _ENCRYPTION_UTILS_

#include <iostream>
#include <vector>
#include <map>
#include <cmath>
#include <algorithm>

#include "cryptlib.h"
#include "osrng.h"
#include "sha.h"
#include "aes.h"
#include "modes.h"
#include "filters.h"

#include "BinaryData.h"
#include "BtcUtils.h"
#include "UniversalTimer.h"

// This is used to attempt to keep keying material out of swap
// I am stealing this from bitcoin 0.4.0 src, serialize.h
#ifdef _MSC_VER
   // Note that VirtualLock does not provide this as a guarantee on Windows,
   // but, in practice, memory that has been VirtualLock'd almost never gets written to
   // the pagefile except in rare circumstances where memory is extremely low.
   #include <windows.h>
   #define mlock(p, n) VirtualLock((p), (n));
   #define munlock(p, n) VirtualUnlock((p), (n));
#else
   #include <sys/mman.h>
   #include <limits.h>
   /* This comes from limits.h if it's not defined there set a sane default */
   #ifndef PAGESIZE
      #include <unistd.h>
      #define PAGESIZE sysconf(_SC_PAGESIZE)
   #endif
   #define mlock(a,b) \
     mlock(((void *)(((size_t)(a)) & (~((PAGESIZE)-1)))),\
     (((((size_t)(a)) + (b) - 1) | ((PAGESIZE) - 1)) + 1) - (((size_t)(a)) & (~((PAGESIZE) - 1))))
   #define munlock(a,b) \
     munlock(((void *)(((size_t)(a)) & (~((PAGESIZE)-1)))),\
     (((((size_t)(a)) + (b) - 1) | ((PAGESIZE) - 1)) + 1) - (((size_t)(a)) & (~((PAGESIZE) - 1))))
#endif


using namespace std;
using namespace CryptoPP;


// Make sure that any time we're handling keys, we mlock/munlock it to 
// avoid it being paged/swapped
class SensitiveKeyData
{
public:
   SensitiveKeyData(void) { keyData_ = BinaryData(0); }
   SensitiveKeyData(BinaryData const & data) { setKeyData(data); }
   ~SensitiveKeyData(void) { dealloc(); }
   SensitiveKeyData(SensitiveKeyData const & skd2) {setKeyData(skd2.keyData_);}

   BinaryData const &    getKeyDataRef(void) const  {return  keyData_;}
   BinaryData const *    getKeyDataPtr(void) const  {return &keyData_;}
   uint8_t const *       getPtr(void) const      {return  keyData_.getPtr();}
   uint32_t              getSize(void) const        {return  keyData_.getSize();}
   string                toBinStr(void) const { return keyData_.toBinStr(); }
   string                toHexStr(void) const { return keyData_.toHexStr(); }

   void setKeyData(BinaryData const & data)
   {
      dealloc();
      keyData_.copyFrom(data);
      mlock(keyData_.getPtr(), keyData_.getSize());
   }

   void dealloc(void)
   {
      if(keyData_.getSize() > 0)
      {
         keyData_.fill(0x00);
         munlock(keyData_.getPtr(), keyData_.getSize());
      }
   }

private:
   BinaryData keyData_;
};



class AesCrypto
{
public:
   /////////////////////////////////////////////////////////////////////////////
   AesCrypto(void) {}

   /////////////////////////////////////////////////////////////////////////////
   void EncryptInPlace(BinaryData & data, 
                       SensitiveKeyData & key,
                       BinaryData & iv)
   {
      cout << "   StartPlain: " << data.toHexStr() << endl;
      cout << "   Key Data  : " << key.toHexStr() << endl;

      // Caller can supply their own IV/entropy, or let it be generated here
      if(iv.getSize() == 0)
      {
         AutoSeededRandomPool prng;
         iv.resize(AES::BLOCKSIZE);
         prng.GenerateBlock(iv.getPtr(), AES::BLOCKSIZE);
      }
      cout << "   IV Data   : " << iv.toHexStr() << endl;

      CFB_Mode<AES>::Encryption aes_enc( (byte*)key.getPtr(), 
                                                key.getSize(), 
                                         (byte*)iv.getPtr());

      aes_enc.ProcessData( (byte*)data.getPtr(), 
                           (byte*)data.getPtr(), 
                                  data.getSize());

      cout << "   Ciphertext: " << data.toHexStr() << endl;
   }

   /////////////////////////////////////////////////////////////////////////////
   void DecryptInPlace(BinaryData &       data, 
                       SensitiveKeyData & key,
                       BinaryData         iv  )
   {
      cout << "   StrtCipher: " << data.toHexStr() << endl;
      cout << "   Key Data  : " << key.toHexStr() << endl;
      cout << "   IV Data   : " << iv.toHexStr() << endl;

      CFB_Mode<AES>::Decryption aes_enc( (byte*)key.getPtr(), 
                                                key.getSize(), 
                                         (byte*)iv.getPtr());

      aes_enc.ProcessData( (byte*)data.getPtr(), 
                           (byte*)data.getPtr(), 
                                  data.getSize());

      cout << "   Plaintext : " << data.toHexStr() << endl;
   }
};



//
class KdfRomix
{
public:

   /////////////////////////////////////////////////////////////////////////////
   KdfRomix(void) : 
      hashFunctionName_( "sha512" ),
      hashOutputBytes_( 64 ),
      kdfOutputBytes_( 32 )
   { 
      // Nothing to do here
   }

   /////////////////////////////////////////////////////////////////////////////
   KdfRomix(uint32_t memReqts, uint32_t numIter, BinaryData salt) :
      hashFunctionName_( "sha512" ),
      hashOutputBytes_( 64 ),
      kdfOutputBytes_( 32 )
   {
      usePrecomputedKdfParams(memReqts, numIter, salt);
   }


   /////////////////////////////////////////////////////////////////////////////
   void computeKdfParams(uint32_t memReqt, uint32_t targetComputeMs)
   {
      // Allocate memory for the lookup table
      memoryReqtBytes_  = memReqt;
      sequenceCount_    = memoryReqtBytes_ / hashOutputBytes_;

      // Create a random salt, even though this is probably unnecessary:
      // the variation in numIter and memReqts is probably effective enough
      salt_.resize(32);
      AutoSeededRandomPool prng;
      prng.GenerateBlock(salt_.getPtr(), 32);

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
      cout << "   Setting numIterations to:       " << numIterations_ << endl;
   }

   /////////////////////////////////////////////////////////////////////////////
   void usePrecomputedKdfParams(uint32_t memReqts, uint32_t numIter, BinaryData salt)
   {
      memoryReqtBytes_ = memReqts;
      sequenceCount_   = memoryReqtBytes_ / hashOutputBytes_;
      numIterations_   = numIter;
      salt_            = salt;
   }

   /////////////////////////////////////////////////////////////////////////////
   void printKdfParams(void)
   {
      // SHA512 computes 64-byte outputs
      cout << "KDF Parameters:" << endl;
      cout << "   HashFunction : " << hashFunctionName_ << endl;
      cout << "   HashOutBytes : " << hashOutputBytes_ << endl;
      cout << "   Memory/thread: " << memoryReqtBytes_ << " bytes" << endl;
      cout << "   SequenceCount: " << sequenceCount_   << endl;
      cout << "   NumIterations: " << numIterations_   << endl;
      cout << "   KDFOutBytes  : " << kdfOutputBytes_  << endl;
      cout << "   Salt         : " << salt_.toHexStr() << endl;
   }


   /////////////////////////////////////////////////////////////////////////////
   BinaryData DeriveKey_OneIter(BinaryData const & password)
   {
      static CryptoPP::SHA512 sha512;

      // Concatenate the salt/IV to the password
      BinaryData saltedPassword = password + salt_; 
      
      // Prepare the lookup table
      lookupTable_.resize(memoryReqtBytes_);
      lookupTable_.fill(0);
      uint32_t const HSZ = hashOutputBytes_;
      uint8_t* frontOfLUT = lookupTable_.getPtr();
      uint8_t* nextRead  = NULL;
      uint8_t* nextWrite = NULL;

      // First hash to seed the lookup table, input is variable length anyway
      sha512.CalculateDigest(frontOfLUT, 
                             saltedPassword.getPtr(), 
                             saltedPassword.getSize());

      // Compute <sequenceCount_> consecutive hashes of the passphrase
      // Every iteration is stored in the next 64-bytes in the Lookup table
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

      // We divide by 4 to reduce computation time -- k
      uint32_t const nLookups = sequenceCount_ / 4;
      for(uint32_t nSeq=0; nSeq<nLookups; nSeq++)
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
   SensitiveKeyData DeriveKey(BinaryData const & password)
   {
      BinaryData masterKey(password);
      for(uint32_t i=0; i<numIterations_; i++)
         masterKey = DeriveKey_OneIter(masterKey);
      
      return SensitiveKeyData(masterKey);
   }


   string       getHashFunctionName(void) const { return hashFunctionName_; }
   uint32_t     getMemoryReqtBytes(void) const  { return memoryReqtBytes_; }
   uint32_t     getNumIterations(void) const    { return numIterations_; }
   BinaryData   getSalt(void) const             { return salt_; }
   
private:

   string   hashFunctionName_;  // name of hash function to use (only one)
   uint32_t hashOutputBytes_;
   uint32_t kdfOutputBytes_;    // size of final key data

   uint32_t memoryReqtBytes_;
   uint32_t sequenceCount_;
   BinaryData lookupTable_;
   BinaryData salt_;            // prob not necessary amidst numIter, memReqts
                                // but I guess it can't hurt

   uint32_t numIterations_;     // We set the ROMIX params for a given memory 
                                // req't. Then run it numIter times to meet
                                // the computation-time req't
                                

};



#endif














