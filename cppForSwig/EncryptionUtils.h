////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Implements canned routines in Crypto++ for AES encryption (for wallet
// security), ECDSA (which is already available in the python interface,
// but it is slow, so we might as well use the fast C++ method if avail),
// time- and memory-hard key derivation functions (resistent to brute
// force, and designed to be too difficult for a GPU to implement), and
// secure binary data handling (to make sure we don't leave sensitive 
// data floating around in application memory).
//
// 
// For the KDF:
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
// Even with less than 1,000,000 hashes, as long as it requires more than 64
// kB of memory, a GPU will have to store the computed lookup tables in global
// memory, which is extremely slow for random lookup.  As a result, GPUs are 
// no better (and possibly much worse) than a CPU for brute-forcing the passwd
//
// This KDF is actually the ROMIX algorithm described on page 6 of Colin's
// paper.  This was chosen because it is the simplest technique that provably
// achieves the goal of being secure, and memory-hard.
//
// The computeKdfParams method well test the speed of the system it is running
// on, and try to pick the largest memory-size the system can compute in less
// than 0.25s (or specified target).  
//
//
// NOTE:  If you are getting an error about invalid argument types, from python,
//        it is usually because you passed in a BinaryData/Python-string instead
//        of a SecureBinaryData object
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
#include "eccrypto.h"
#include "filters.h"
#include "DetSign.h"

#include "BinaryData.h"
#include "BtcUtils.h"
#include "UniversalTimer.h"

// This is used to attempt to keep keying material out of swap
// I am stealing this from bitcoin 0.4.0 src, serialize.h
#if defined(_MSC_VER) || defined(__MINGW32__)
   // Note that VirtualLock does not provide this as a guarantee on Windows,
   // but, in practice, memory that has been VirtualLock'd almost never gets written to
   // the pagefile except in rare circumstances where memory is extremely low.
   #include <windows.h>
   #include "leveldb_windows_port\win32_posix\mman.h"
   //#define mlock(p, n) VirtualLock((p), (n));
   //#define munlock(p, n) VirtualUnlock((p), (n));
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

// We will look for a high memory value to use in the KDF
// But as a safety check, we should probably put a cap
// on how much memory the KDF can use -- 32 MB is good
// If a KDF uses 32 MB of memory, it is undeniably easier
// to compute on a CPU than a GPU.
#define DEFAULT_KDF_MAX_MEMORY 32*1024*1024

// Highly deterministic wallet - HMAC-512 key (see BIP32)
/*#define DETWALLETKEYHEX "426974636f696e2073656564" // "Bitcoin seed"
#define SECP256K1_ORDER_HEX "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141"
#define SECP256K1_FP "fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f"
#define SECP256K1_A "0000000000000000000000000000000000000000000000000000000000000000"
#define SECP256K1_B "0000000000000000000000000000000000000000000000000000000000000007"
#define SECP256K1_G "0479be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8"*/

#define PRIKEYSIZE 33
#define PUBKEYSIZE 65
#define EXTKEYSIZE 78

// BIP32 version bytes.
#define MAIN_PUB 76067358 // 0x0488b21e
#define MAIN_PRV 76066276 // 0x0488ade4
#define TEST_PUB 70617039 // 0x043587cf
#define TEST_PRV 70615956 // 0x04358394

// Use this to avoid "using namespace CryptoPP" (which confuses SWIG)
// and also so it's easy to switch the AES MODE or PRNG, in one place
#define UNSIGNED    ((CryptoPP::Integer::Signedness)(0))
#define BTC_AES       CryptoPP::AES
#define BTC_CFB_MODE  CryptoPP::CFB_Mode
#define BTC_CBC_MODE  CryptoPP::CBC_Mode
#define BTC_PRNG      CryptoPP::AutoSeededX917RNG<CryptoPP::AES>

#define BTC_ECPOINT   CryptoPP::ECP::Point
#define BTC_ECDSA     CryptoPP::ECDSA<CryptoPP::ECP, CryptoPP::SHA256>
#define BTC_PRIVKEY   CryptoPP::ECDSA<CryptoPP::ECP, CryptoPP::SHA256>::PrivateKey
#define BTC_PUBKEY    CryptoPP::ECDSA<CryptoPP::ECP, CryptoPP::SHA256>::PublicKey
#define BTC_SIGNER    CryptoPP::ECDSA<CryptoPP::ECP, CryptoPP::SHA256>::Signer
#define BTC_DETSIGNER CryptoPP::ECDSA_DetSign<CryptoPP::ECP, CryptoPP::SHA256>::DetSigner
#define BTC_VERIFIER  CryptoPP::ECDSA<CryptoPP::ECP, CryptoPP::SHA256>::Verifier


////////////////////////////////////////////////////////////////////////////////
// Make sure that all crypto information is handled with page-locked data,
// and overwritten when it's destructor is called.  For simplicity, we will
// use this data type for all crypto data, even for data values that aren't
// really sensitive.  We can use the SecureBinaryData(bdObj) to convert our 
// regular strings/BinaryData objects to secure objects
//
class SecureBinaryData : public BinaryData
{
public:
   // We want regular BinaryData, but page-locked and secure destruction
   SecureBinaryData() : BinaryData() 
                   { lockData(); }
   SecureBinaryData(size_t sz) : BinaryData(sz) 
                   { lockData(); }
   SecureBinaryData(BinaryData const & data) : BinaryData(data) 
                   { lockData(); }
   SecureBinaryData(uint8_t const * inData, size_t sz) : BinaryData(inData, sz)
                   { lockData(); }
   SecureBinaryData(uint8_t const * d0, uint8_t const * d1) : BinaryData(d0, d1)
                   { lockData(); }
   SecureBinaryData(string const & str) : BinaryData(str)
                   { lockData(); }
   SecureBinaryData(BinaryDataRef const & bdRef) : BinaryData(bdRef)
                   { lockData(); }

   ~SecureBinaryData() { destroy(); }

   // These methods are definitely inherited, but SWIG needs them here if they
   // are to be used from python
   uint8_t const *   getPtr()  const { return BinaryData::getPtr();  }
   uint8_t       *   getPtr()        { return BinaryData::getPtr();  }
   size_t            getSize() const { return BinaryData::getSize(); }
   SecureBinaryData  copy()    const { return SecureBinaryData(getPtr(),
                                                               getSize()); }
   
   string toHexStr(bool BE=false) const { return BinaryData::toHexStr(BE);}
   string toBinStr() const          { return BinaryData::toBinStr();  }

   SecureBinaryData(SecureBinaryData const & sbd2) : 
           BinaryData(sbd2.getPtr(), sbd2.getSize()) { lockData(); }

   void resize(size_t sz)  { BinaryData::resize(sz);  lockData(); }
   void reserve(size_t sz) { BinaryData::reserve(sz); lockData(); }

   SecureBinaryData XOR(uint8_t xorValue);
   
   SecureBinaryData XOR(SecureBinaryData const & sbd1,
                        SecureBinaryData const & sbd2);

   BinaryData    getRawCopy() const { return BinaryData(getPtr(), getSize()); }
   BinaryDataRef getRawRef()  { return BinaryDataRef(getPtr(), getSize()); }

   SecureBinaryData copySwapEndian(size_t pos1=0, size_t pos2=0) const;

   SecureBinaryData& append(SecureBinaryData & sbd2);
   SecureBinaryData& append(uint8_t byte);
   SecureBinaryData& append(uint8_t const byte, uint32_t sz);
   SecureBinaryData& append(uint8_t const * str, uint32_t sz);

   SecureBinaryData& operator=(SecureBinaryData const & sbd2);
   SecureBinaryData   operator+(SecureBinaryData & sbd2) const;
   //uint8_t const & operator[](size_t i) const {return BinaryData::operator[](i);}
   bool operator==(SecureBinaryData const & sbd2) const;

   SecureBinaryData getHash256() const;
   SecureBinaryData getHash160() const;

   // Uses X9.17, soon to be superceded by SP800-90
   // This would be a static method, as would be appropriate, except SWIG won't
   // play nice with static methods.  Instead, we will just use 
   // SecureBinaryData().GenerateRandom(32), etc
   SecureBinaryData GenerateRandom(uint32_t numBytes, 
                              SecureBinaryData extraEntropy=SecureBinaryData());

   // This pulls 2x entropy from the PRNG, XORs the two halves
   SecureBinaryData GenerateRandom2xXOR(uint32_t numBytes, 
                              SecureBinaryData extraEntropy=SecureBinaryData());

   void lockData()
   {
      if(getSize() > 0)
         mlock(getPtr(), getSize());
   }

   void destroy()
   {
      if(getSize() > 0)
      {
         fill(0x00);
         munlock(getPtr(), getSize());
      }
      resize(0);
   }
};


////////////////////////////////////////////////////////////////////////////////
// A memory-bound key-derivation function -- uses a variation of Colin 
// Percival's ROMix algorithm: http://www.tarsnap.com/scrypt/scrypt.pdf
//
// The computeKdfParams method takes in a target time, T, for computation
// on the computer executing the test.  The final KDF should take somewhere
// between T/2 and T seconds.
class KdfRomix
{
public:

   /////////////////////////////////////////////////////////////////////////////
   KdfRomix();

   /////////////////////////////////////////////////////////////////////////////
   KdfRomix(uint32_t memReqts, uint32_t numIter, SecureBinaryData salt);


   /////////////////////////////////////////////////////////////////////////////
   // Default max-memory reqt will 
   void computeKdfParams(double   targetComputeSec=0.25, 
                         uint32_t maxMemReqtsBytes=DEFAULT_KDF_MAX_MEMORY);

   /////////////////////////////////////////////////////////////////////////////
   void usePrecomputedKdfParams(uint32_t memReqts, 
                                uint32_t numIter, 
                                SecureBinaryData salt);

   /////////////////////////////////////////////////////////////////////////////
   void printKdfParams();

   /////////////////////////////////////////////////////////////////////////////
   SecureBinaryData DeriveKey_OneIter(SecureBinaryData const & password);

   /////////////////////////////////////////////////////////////////////////////
   SecureBinaryData DeriveKey(SecureBinaryData const & password);

   /////////////////////////////////////////////////////////////////////////////
   string       getHashFunctionName() const { return hashFunctionName_; }
   uint32_t     getMemoryReqtBytes() const  { return memoryReqtBytes_; }
   uint32_t     getNumIterations() const    { return numIterations_; }
   SecureBinaryData   getSalt() const       { return salt_; }
   
private:

   string   hashFunctionName_;  // name of hash function to use (only one)
   uint32_t hashOutputBytes_;
   uint32_t kdfOutputBytes_;    // size of final key data

   uint32_t memoryReqtBytes_;
   uint32_t sequenceCount_;
   SecureBinaryData lookupTable_;
   SecureBinaryData salt_;            // prob not necessary amidst numIter, memReqts
                                // but I guess it can't hurt

   uint32_t numIterations_;     // We set the ROMIX params for a given memory 
                                // req't. Then run it numIter times to meet
                                // the computation-time req't
};


////////////////////////////////////////////////////////////////////////////////
// Leverage CryptoPP library for AES encryption/decryption
class CryptoAES
{
public:
   CryptoAES() {}

   /////////////////////////////////////////////////////////////////////////////
   SecureBinaryData EncryptCFB(SecureBinaryData & data, 
                               SecureBinaryData & key,
                               SecureBinaryData & iv);

   /////////////////////////////////////////////////////////////////////////////
   SecureBinaryData DecryptCFB(SecureBinaryData & data, 
                               SecureBinaryData & key,
                               SecureBinaryData   iv);

   /////////////////////////////////////////////////////////////////////////////
   SecureBinaryData EncryptCBC(SecureBinaryData & data, 
                               SecureBinaryData & key,
                               SecureBinaryData & iv);

   /////////////////////////////////////////////////////////////////////////////
   SecureBinaryData DecryptCBC(SecureBinaryData & data, 
                               SecureBinaryData & key,
                               SecureBinaryData   iv);
};


////////////////////////////////////////////////////////////////////////////////
// Create a C++ interface to the Crypto++ ECDSA ops:  should be more secure
// and much faster than the pure-python methods created by Lis
//
// These methods might as well just be static methods, but SWIG doesn't like
// static methods.  So we will invoke these via CryptoECDSA().Function()
class CryptoECDSA
{
public:
   CryptoECDSA() {}

   /////////////////////////////////////////////////////////////////////////////
   static BTC_PRIVKEY CreateNewPrivateKey(
                              SecureBinaryData extraEntropy=SecureBinaryData());

   /////////////////////////////////////////////////////////////////////////////
   static BTC_PRIVKEY ParsePrivateKey(SecureBinaryData const & privKeyData);
   
   /////////////////////////////////////////////////////////////////////////////
   static BTC_PUBKEY ParsePublicKey(SecureBinaryData const & pubKey65B);

   /////////////////////////////////////////////////////////////////////////////
   static BTC_PUBKEY ParsePublicKey(SecureBinaryData const & pubKeyX32B,
                                    SecureBinaryData const & pubKeyY32B);
   
   /////////////////////////////////////////////////////////////////////////////
   static SecureBinaryData SerializePrivateKey(BTC_PRIVKEY const & privKey);
   
   /////////////////////////////////////////////////////////////////////////////
   static SecureBinaryData SerializePublicKey(BTC_PUBKEY const & pubKey);

   /////////////////////////////////////////////////////////////////////////////
   static BTC_PUBKEY ComputePublicKey(BTC_PRIVKEY const & cppPrivKey);

   
   /////////////////////////////////////////////////////////////////////////////
   static bool CheckPubPrivKeyMatch(BTC_PRIVKEY const & cppPrivKey,
                                    BTC_PUBKEY  const & cppPubKey);
   
   /////////////////////////////////////////////////////////////////////////////
   // For signing and verification, pass in original, UN-HASHED binary string.
   // For signing, k-value can use a PRNG or deterministic value (RFC 6979).
   static SecureBinaryData SignData(SecureBinaryData const & binToSign, 
                                    BTC_PRIVKEY const & cppPrivKey,
                                    const bool& detSign = true);

   /////////////////////////////////////////////////////////////////////////////
   // For signing and verification, pass in original, UN-HASHED binary string
   static bool VerifyData(SecureBinaryData const & binMessage, 
                          SecureBinaryData const & binSignature,
                          BTC_PUBKEY const & cppPubKey);

   /////////////////////////////////////////////////////////////////////////////
   // For doing direct raw ECPoint operations... need the ECP object
   static CryptoPP::ECP Get_secp256k1_ECP(void);


   /////////////////////////////////////////////////////////////////////////////
   // We need to make sure that we have methods that take only secure strings
   // and return secure strings (I don't feel like figuring out how to get 
   // SWIG to take BTC_PUBKEY and BTC_PRIVKEY

   /////////////////////////////////////////////////////////////////////////////
   SecureBinaryData GenerateNewPrivateKey(
                              SecureBinaryData extraEntropy=SecureBinaryData());
   
   /////////////////////////////////////////////////////////////////////////////
   SecureBinaryData ComputePublicKey(SecureBinaryData const & cppPrivKey);

   /////////////////////////////////////////////////////////////////////////////
   bool VerifyPublicKeyValid(SecureBinaryData const & pubKey);

   /////////////////////////////////////////////////////////////////////////////
   bool CheckPubPrivKeyMatch(SecureBinaryData const & privKey32,
                             SecureBinaryData const & pubKey65);

   /////////////////////////////////////////////////////////////////////////////
   // For signing and verification, pass in original, UN-HASHED binary string.
   // For signing, k-value can use a PRNG or deterministic value (RFC 6979).
   SecureBinaryData SignData(SecureBinaryData const & binToSign, 
                             SecureBinaryData const & binPrivKey,
                             const bool& detSign = true);

   /////////////////////////////////////////////////////////////////////////////
   // For signing and verification, pass in original, UN-HASHED binary string
   bool VerifyData(SecureBinaryData const & binMessage, 
                   SecureBinaryData const & binSignature,
                   SecureBinaryData const & pubkey65B);

   /////////////////////////////////////////////////////////////////////////////
   // Deterministically generate new private key using a chaincode
   // Changed:  Added using the hash of the public key to the mix
   //           b/c multiplying by the chaincode alone is too "linear"
   //           (there's no reason to believe it's insecure, but it doesn't
   //           hurt to add some extra entropy/non-linearity to the chain
   //           generation process)
   SecureBinaryData ComputeChainedPrivateKey(
                           SecureBinaryData const & binPrivKey,
                           SecureBinaryData const & chaincode,
                           SecureBinaryData binPubKey=SecureBinaryData(),
                           SecureBinaryData* computedMultiplier=NULL);
                               
   /////////////////////////////////////////////////////////////////////////////
   // Deterministically generate new private key using a chaincode
   SecureBinaryData ComputeChainedPublicKey(
                           SecureBinaryData const & binPubKey,
                           SecureBinaryData const & chaincode,
                           SecureBinaryData* multiplierOut=NULL);

   /////////////////////////////////////////////////////////////////////////////
   // We need some direct access to Crypto++ math functions
   SecureBinaryData InvMod(const SecureBinaryData& m);

   /////////////////////////////////////////////////////////////////////////////
   // Some standard ECC operations
   ////////////////////////////////////////////////////////////////////////////////
   bool ECVerifyPoint(BinaryData const & x,
                      BinaryData const & y);

   BinaryData ECMultiplyScalars(BinaryData const & A, 
                                BinaryData const & B);

   bool ECMultiplyPoint(BinaryData const & A, 
                        BinaryData const & Bx,
                        BinaryData const & By,
                        BinaryData& multResult);

   bool ECAddPoints(BinaryData const & Ax, 
                    BinaryData const & Ay,
                    BinaryData const & Bx,
                    BinaryData const & By,
                    BinaryData& addResult);

   bool ECInverse(BinaryData const & Ax, 
                  BinaryData const & Ay,
                  BinaryData& invResult);

   SecureBinaryData GetPubKeyFromSigAndMsgHash(SecureBinaryData const & sig, SecureBinaryData const & msgHash);

   /////////////////////////////////////////////////////////////////////////////
   // For Point-compression
   SecureBinaryData CompressPoint(SecureBinaryData const & pubKey65);
   SecureBinaryData UncompressPoint(SecureBinaryData const & pubKey33);
};


////////////////////////////////////////////////////////////////////////////////
// Extended keys should never hold encrypted keys.  We maintain encryption 
// details outside this class, and don't want to mistakenly believe that an
// ExtendedKey object has a priv key if it doesn't.
// Note that the class has two keys: a "primary" key and a public key. The
// primary key will be private if a private key is desired, and the public key
// will be its match. If we're deriving a public key, both keys will match and
// be public. In either case, the primary key will be 33 bytes, meaning it'll be
// compressed if it's public. The public key will be 65 bytes (uncompressed).
// Unless otherwise noted, all algorithms are from the BIP32 paper.
class ExtendedKey
{
public:
   ExtendedKey() : key_(0), pubKey_(0), chaincode_(0), version_(TEST_PUB),
                   parentFP_(0), validKey_(false) {}

   // Constructor that requires an incoming key (pub or pri), chain code, parent
   // fingerprint, position in the chain, and a boolean indicating if the key's
   // public or private.
   ExtendedKey(SecureBinaryData const & key,
               SecureBinaryData const & ch,
               SecureBinaryData const & parFP,
               list<uint32_t> parentTreeIdx,
               uint32_t inVer,
               uint32_t inChildNum,
               bool keyIsPub);

   // Constructor that requires private & public keys, and the chain code.
   ExtendedKey(SecureBinaryData const & pr, 
               SecureBinaryData const & pb, 
               SecureBinaryData const & ch,
               SecureBinaryData const & parFP,
               list<uint32_t> parentTreeIdx,
               uint32_t inVer,
               uint32_t inChildNum);

   // Constructor that requires a private key and chain code.
   ExtendedKey(SecureBinaryData const & key,
               SecureBinaryData const & ch);

   void destroy();
   void deletePrivateKey();
   ExtendedKey makePublicCopy();

   const bool isPub() const;
   const bool isPrv() const;
   const bool isMaster() const;
   bool hasChaincode() const   { return (chaincode_.getSize() > 0); }
   bool isInitialized() const  { return validKey_; }

   const SecureBinaryData getExtKeySer();
   list<uint32_t>           getIndicesList() const { return indicesList_; }
   vector<uint32_t>         getIndicesVect() const;
   const SecureBinaryData   getFingerprint() const;
   const SecureBinaryData   getIdentifier() const;
   SecureBinaryData const & getParentFP() const { return parentFP_; }
   SecureBinaryData const & getKey() const   { return key_; }
   SecureBinaryData getPrivateKey(bool withZeroByte) const;
   SecureBinaryData getPublicKey(bool compr=true) const;
   SecureBinaryData getChaincode() const  { return chaincode_; }

   BinaryData               getHash160() const; // Hash160 of uncomp pub key
   ExtendedKey              copy() const;

   void debugPrint();

   uint32_t                 getChildNum() const;
   const string getIndexListString(const string prefix="M");

   const uint32_t getVersion() const { return version_; }
   const uint8_t getDepth() const { return (uint8_t)indicesList_.size(); }

private:
   void updatePubKey();

   // Due to Crypto++ handling, these will be big/network endian.
   SecureBinaryData key_; // 33 bytes: (0x00 + prv key) or compressed pub key.
   SecureBinaryData pubKey_;  // 65 bytes - Key is uncompressed.
   SecureBinaryData chaincode_; // 32 bytes.

   list<uint32_t> indicesList_; // Shows where in the chain we are.
                                // Empty if key is master or invalid.

   uint32_t version_;
   SecureBinaryData parentFP_;
   bool validKey_;
};


// NOT USED FOR NOW.
////////////////////////////////////////////////////////////////////////////////
typedef enum 
{
   HDW_CHAIN_EXTERNAL=0,
   HDW_CHAIN_INTERNAL=1,
}  HDW_CHAIN_TYPE;


////////////////////////////////////////////////////////////////////////////////
class HDWalletCrypto
{
public:
   HDWalletCrypto() {}

   // Perform an HMAC-SHA512 hash.
   SecureBinaryData HMAC_SHA512(SecureBinaryData key,
                                SecureBinaryData msg);

   // Derive a child key from an incoming key (pub or pri).
   ExtendedKey childKeyDeriv(ExtendedKey const& extPar,
                             uint32_t childNum,
                             SecureBinaryData* multiplierOut=NULL);

   // Use a seed to create a master key.
   ExtendedKey convertSeedToMasterKey(SecureBinaryData const& seed);

   // Get a child key based off a list of multipliers/addends.
   SecureBinaryData getChildKeyFromOps(SecureBinaryData const& parKey,
                                       vector<SecureBinaryData>& mathOps);

   // Same as above but using BinaryData objects which are SWIG friendly
   BinaryData getChildKeyFromOps_SWIG(BinaryData parKey,
                                      const vector<BinaryData>& mathOps);

   ~HDWalletCrypto();

private:
   bool childKeyDerivPub(SecureBinaryData const& multiplier,
                         SecureBinaryData const& parKey,
                         SecureBinaryData const& ecGenX,
                         SecureBinaryData const& ecGenY,
                         SecureBinaryData& childKey);
   bool childKeyDerivPrv(SecureBinaryData const& addend,
                         SecureBinaryData const& parKey,
                         SecureBinaryData const& ecGenOrder,
                         SecureBinaryData& childKey);
};


////////////////////////////////////////////////////////////////////////////////
// The HDWalletCryptoSeed class really isn't meant to be used directly. It ought
// to be used indirectly via HDWalletCrypto calls.
class HDWalletCryptoSeed 
{
public:
   HDWalletCryptoSeed() {}
   HDWalletCryptoSeed(SecureBinaryData const& rngData);

   const SecureBinaryData& getMasterKey()   { return masterKey_; }
   const SecureBinaryData& getMasterChain() { return masterChain_; }

private:
   SecureBinaryData masterKey_;   
   SecureBinaryData masterChain_;
};
#endif
