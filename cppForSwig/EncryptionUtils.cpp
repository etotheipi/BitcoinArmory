////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include "EncryptionUtils.h"
#include "log.h"
#include "integer.h"
#include "oids.h"

// Maybe someday....
//#include <openssl/ec.h>
//#include <openssl/ecdsa.h>
//#include <openssl/obj_mac.h>

#define CRYPTO_DEBUG false

// Determines if BIP32 key versions will be main or test. For now, force main.
#if 0
#define PUBVER TEST_PUB
#define PRVVER TEST_PRV
#else
#define PUBVER MAIN_PUB
#define PRVVER MAIN_PRV
#endif

// Generator and curve order taken from SEC 2, Sect. 2.7.1. Data is big endian.
const SecureBinaryData ecGenX_BE = SecureBinaryData().CreateFromHex(
            "79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798");
const SecureBinaryData ecGenY_BE = SecureBinaryData().CreateFromHex(
            "483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8");
const SecureBinaryData ecOrder_BE = SecureBinaryData().CreateFromHex(
            "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141");

// Function that takes an incoming child number and determines if the BIP32
// child key will use private or public key derivation.
inline bool isHardened(uint32_t inChildNumber)
{
   return ((0x80000000 & inChildNumber) == 0x80000000);
}


/////////////////////////////////////////////////////////////////////////////
// We have to explicitly re-define some of these methods...
SecureBinaryData & SecureBinaryData::append(SecureBinaryData & sbd2) 
{
   if(sbd2.getSize()==0) 
      return (*this);

   if(getSize()==0) 
      BinaryData::copyFrom(sbd2.getPtr(), sbd2.getSize());
   else
      BinaryData::append(sbd2.getRawRef());

   lockData();
   return (*this);
}


////////////////////////////////////////////////////////////////////////////////
SecureBinaryData& SecureBinaryData::append(uint8_t byte)
{
   BinaryData::append(byte);
   lockData();
   return (*this);
}


////////////////////////////////////////////////////////////////////////////////
SecureBinaryData& SecureBinaryData::append(uint8_t const byte, uint32_t sz)
{
   BinaryData::append(byte, sz);
   lockData();
   return (*this);
}


////////////////////////////////////////////////////////////////////////////////
SecureBinaryData& SecureBinaryData::append(uint8_t const * str, uint32_t sz)
{
   BinaryData::append(str, sz);
   lockData();
   return (*this);
}


/////////////////////////////////////////////////////////////////////////////
SecureBinaryData SecureBinaryData::operator+(SecureBinaryData & sbd2) const
{
   SecureBinaryData out(getSize() + sbd2.getSize());
   memcpy(out.getPtr(), getPtr(), getSize());
   memcpy(out.getPtr()+getSize(), sbd2.getPtr(), sbd2.getSize());
   out.lockData();
   return out;
}

/////////////////////////////////////////////////////////////////////////////
SecureBinaryData & SecureBinaryData::operator=(SecureBinaryData const & sbd2)
{ 
   copyFrom(sbd2.getPtr(), sbd2.getSize() );
   lockData(); 
   return (*this);
}

/////////////////////////////////////////////////////////////////////////////
bool SecureBinaryData::operator==(SecureBinaryData const & sbd2) const
{ 
   if(getSize() != sbd2.getSize())
      return false;
   for(unsigned int i=0; i<getSize(); ++i) {
      if( (*this)[i] != sbd2[i] ) {
         return false;
      }
   }
   return true;
}

/////////////////////////////////////////////////////////////////////////////
// Swap endianness of the bytes in the index range [pos1, pos2)
SecureBinaryData SecureBinaryData::copySwapEndian(size_t pos1, size_t pos2) const
{
   return SecureBinaryData(BinaryData::copySwapEndian(pos1, pos2));
}

/////////////////////////////////////////////////////////////////////////////
// Uses X9.17
SecureBinaryData SecureBinaryData::GenerateRandom(uint32_t numBytes, 
                                                  SecureBinaryData entropy)
{
   BTC_PRNG prng;

   // Entropy here refers to *EXTRA* entropy.  Crypto++ has its own mechanism
   // for generating entropy which is sufficient, but it doesn't hurt to add
   // more if you have it.
   if(entropy.getSize() > 0)
      prng.IncorporateEntropy( (byte*)entropy.getPtr(), entropy.getSize());

   SecureBinaryData randData(numBytes);
   prng.GenerateBlock(randData.getPtr(), numBytes);
   return randData;  
}
/////////////////////////////////////////////////////////////////////////////
SecureBinaryData SecureBinaryData::GenerateRandom2xXOR(uint32_t numBytes, 
                                                  SecureBinaryData entropy)
{
   // NIST (SP800-133) has recommended K=U XOR V, where U is output of an 
   // RNG, V is an indepedently-generated string.  Previously recommended 
   // generating 1.5x the desired bytes and hashing it to the right length.  
   // So here we combine the concepts by just doing TWO 1x RNG pulls, 
   // and XOR them together.  
   SecureBinaryData U = SecureBinaryData().GenerateRandom(numBytes, entropy);
   SecureBinaryData V = SecureBinaryData().GenerateRandom(numBytes);
   return SecureBinaryData().XOR(U, V);  
}

/////////////////////////////////////////////////////////////////////////////
static SecureBinaryData CreateFromHex(string const & str)
{
   SecureBinaryData out;
   out.createFromHex(str);
   return out;
}


// XOR every byte of the current SecureBinaryData with a given value and return
// the result.
/////////////////////////////////////////////////////////////////////////////
SecureBinaryData SecureBinaryData::XOR(uint8_t xorValue) {
   SecureBinaryData out = BinaryData::XOR(xorValue);
   out.lockData();
   return out;
}

/////////////////////////////////////////////////////////////////////////////
SecureBinaryData SecureBinaryData::XOR(SecureBinaryData const & sbd1,
                                       SecureBinaryData const & sbd2)
{
   if(sbd1.getSize() != sbd2.getSize())
   {
      LOGERR << "Attempted to XOR two SBD objects of different lengths";
      return SecureBinaryData(0);
   }

   SecureBinaryData sbdOut(sbd1.getSize());
   for(uint32_t b=0; b<sbd1.getSize(); b++)
      *(sbdOut.getPtr()+b) = *(sbd1.getPtr()+b) ^ *(sbd2.getPtr()+b);

   return sbdOut;
}


// Get the Hash256 of the SecureBinaryData obj.
/////////////////////////////////////////////////////////////////////////////
SecureBinaryData SecureBinaryData::getHash256() const {
   SecureBinaryData rVal = BtcUtils::getHash256(getPtr(), (uint32_t)getSize());
   rVal.lockData();
   return rVal;
}


// Get the Hash160 of the SecureBinaryData obj.
/////////////////////////////////////////////////////////////////////////////
SecureBinaryData SecureBinaryData::getHash160() const {
   SecureBinaryData rVal = BtcUtils::getHash160(getPtr(), (uint32_t)getSize());
   rVal.lockData();
   return rVal;
}


/////////////////////////////////////////////////////////////////////////////
KdfRomix::KdfRomix() : 
   hashFunctionName_( "sha512" ),
   hashOutputBytes_( 64 ),
   kdfOutputBytes_( 32 ),
   memoryReqtBytes_( 32 ),
   numIterations_( 0 )
{ 
   // Nothing to do here
}

/////////////////////////////////////////////////////////////////////////////
KdfRomix::KdfRomix(uint32_t memReqts, uint32_t numIter, SecureBinaryData salt) :
   hashFunctionName_( "sha512" ),
   hashOutputBytes_( 64 ),
   kdfOutputBytes_( 32 )
{
   usePrecomputedKdfParams(memReqts, numIter, salt);
}

/////////////////////////////////////////////////////////////////////////////
void KdfRomix::computeKdfParams(double targetComputeSec, uint32_t maxMemReqts)
{
   // Create a random salt, even though this is probably unnecessary:
   // the variation in numIter and memReqts is probably effective enough
   salt_ = SecureBinaryData().GenerateRandom(32);

   // If target compute is 0s, then this method really only generates 
   // a random salt, and sets the other params to default minimum.
   if(targetComputeSec == 0)
   {
      numIterations_ = 1;
      memoryReqtBytes_ = 1024;
      return;
   }


   // Here, we pick the largest memory reqt that allows the executing system
   // to compute the KDF is less than the target time.  A maximum can be 
   // specified, in case the target system is likely to be memory-limited
   // more than compute-speed limited
   SecureBinaryData testKey("This is an example key to test KDF iteration speed");

   // Start the search for a memory value at 1kB
   memoryReqtBytes_ = 1024;
   double approxSec = 0;
   while(approxSec <= targetComputeSec/4 && memoryReqtBytes_ < maxMemReqts)
   {
      memoryReqtBytes_ *= 2;

      sequenceCount_ = memoryReqtBytes_ / hashOutputBytes_;
      lookupTable_.resize(memoryReqtBytes_);

      TIMER_RESTART("KDF_Mem_Search");
      testKey = DeriveKey_OneIter(testKey);
      TIMER_STOP("KDF_Mem_Search");
      approxSec = TIMER_READ_SEC("KDF_Mem_Search");
   }

   // Recompute here, in case we didn't enter the search above 
   sequenceCount_ = memoryReqtBytes_ / hashOutputBytes_;
   lookupTable_.resize(memoryReqtBytes_);


   // Depending on the search above (or if a low max memory was chosen, 
   // we may need to do multiple iterations to achieve the desired compute
   // time on this system.
   double allItersSec = 0;
   uint32_t numTest = 1;
   while(allItersSec < 0.02)
   {
      numTest *= 2;
      TIMER_RESTART("KDF_Time_Search");
      for(uint32_t i=0; i<numTest; ++i)
      {
         SecureBinaryData testKey("This is an example key to test KDF iteration speed");
         testKey = DeriveKey_OneIter(testKey);
      }
      TIMER_STOP("KDF_Time_Search");
      allItersSec = TIMER_READ_SEC("KDF_Time_Search");
   }

   double perIterSec  = allItersSec / numTest;
   numIterations_ = (uint32_t)(targetComputeSec / (perIterSec+0.0005));
   numIterations_ = (numIterations_ < 1 ? 1 : numIterations_);
   //cout << "System speed test results    :  " << endl;
   //cout << "   Total test of the KDF took:  " << allItersSec*1000 << " ms" << endl;
   //cout << "                   to execute:  " << numTest << " iterations" << endl;
   //cout << "   Target computation time is:  " << targetComputeSec*1000 << " ms" << endl;
   //cout << "   Setting numIterations to:    " << numIterations_ << endl;
}



/////////////////////////////////////////////////////////////////////////////
void KdfRomix::usePrecomputedKdfParams(uint32_t memReqts, 
                                       uint32_t numIter, 
                                       SecureBinaryData salt)
{
   memoryReqtBytes_ = memReqts;
   sequenceCount_   = memoryReqtBytes_ / hashOutputBytes_;
   numIterations_   = numIter;
   salt_            = salt;
}

/////////////////////////////////////////////////////////////////////////////
void KdfRomix::printKdfParams()
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
SecureBinaryData KdfRomix::DeriveKey_OneIter(SecureBinaryData const & password)
{
   CryptoPP::SHA512 sha512;

   // Concatenate the salt/IV to the password
   SecureBinaryData saltedPassword = password + salt_; 
   
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
   SecureBinaryData X(frontOfLUT + memoryReqtBytes_ - HSZ, HSZ);
   SecureBinaryData Y(HSZ);

   // We "integerize" a hash value by taking the last 4 bytes of
   // as a uint32_t, and take modulo sequenceCount
   uint64_t* X64ptr = (uint64_t*)(X.getPtr());
   uint64_t* Y64ptr = (uint64_t*)(Y.getPtr());
   uint64_t* V64ptr = NULL;
   uint32_t newIndex;
   uint32_t const nXorOps = HSZ/sizeof(uint64_t);

   // Pure ROMix would use sequenceCount_ for the number of lookups.
   // We divide by 2 to reduce computation time RELATIVE to the memory usage
   // This still provides suffient LUT operations, but allows us to use more
   // memory in the same amount of time (and this is the justification for
   // the scrypt algorithm -- it is basically ROMix, modified for more 
   // flexibility in controlling compute-time vs memory-usage).
   uint32_t const nLookups = sequenceCount_ / 2;
   for(uint32_t nSeq=0; nSeq<nLookups; ++nSeq)
   {
      // Interpret last 4 bytes of last result (mod seqCt) as next LUT index
      newIndex = *(uint32_t*)(X.getPtr()+HSZ-4) % sequenceCount_;

      // V represents the hash result at <newIndex>
      V64ptr = (uint64_t*)(frontOfLUT + HSZ*newIndex);

      // xor X with V, and store the result in X
      for(uint32_t i=0; i<nXorOps; ++i) {
         *(Y64ptr+i) = *(X64ptr+i) ^ *(V64ptr+i);
      }

      // Hash the xor'd data to get the next index for lookup
      sha512.CalculateDigest(X.getPtr(), Y.getPtr(), HSZ);
   }
   // Truncate the final result to get the final key
   lookupTable_.destroy();
   return X.getSliceCopy(0,kdfOutputBytes_);
}

/////////////////////////////////////////////////////////////////////////////
SecureBinaryData KdfRomix::DeriveKey(SecureBinaryData const & password)
{
   SecureBinaryData masterKey(password);
   for(uint32_t i=0; i<numIterations_; ++i) {
      masterKey = DeriveKey_OneIter(masterKey);
   }
   
   return SecureBinaryData(masterKey);
}


/////////////////////////////////////////////////////////////////////////////
// Implement AES encryption using AES mode, CFB
SecureBinaryData CryptoAES::EncryptCFB(SecureBinaryData & data, 
                                       SecureBinaryData & key,
                                       SecureBinaryData & iv)
{
   if(CRYPTO_DEBUG)
   {
      cout << "AES Decrypt" << endl;
      cout << "   BinData: " << data.toHexStr() << endl;
      cout << "   BinKey : " << key.toHexStr() << endl;
      cout << "   BinIV  : " << iv.toHexStr() << endl;
   }


   if(data.getSize() == 0)
      return SecureBinaryData(0);

   SecureBinaryData encrData(data.getSize());

   // Caller can supply their own IV/entropy, or let it be generated here
   // (variable "iv" is a reference, so check it on the way out)
   if(iv.getSize() == 0)
      iv = SecureBinaryData().GenerateRandom(BTC_AES::BLOCKSIZE);


   BTC_CFB_MODE<BTC_AES>::Encryption aes_enc( (byte*)key.getPtr(), 
                                                     key.getSize(), 
                                              (byte*)iv.getPtr());

   aes_enc.ProcessData( (byte*)encrData.getPtr(), 
                        (byte*)data.getPtr(), 
                               data.getSize());

   return encrData;
}

/////////////////////////////////////////////////////////////////////////////
// Implement AES decryption using AES mode, CFB
SecureBinaryData CryptoAES::DecryptCFB(SecureBinaryData & data, 
                                       SecureBinaryData & key,
                                       SecureBinaryData   iv  )
{
   if(CRYPTO_DEBUG)
   {
      cout << "AES Decrypt" << endl;
      cout << "   BinData: " << data.toHexStr() << endl;
      cout << "   BinKey : " << key.toHexStr() << endl;
      cout << "   BinIV  : " << iv.toHexStr() << endl;
   }


   if(data.getSize() == 0)
      return SecureBinaryData(0);

   SecureBinaryData unencrData(data.getSize());

   BTC_CFB_MODE<BTC_AES>::Decryption aes_enc( (byte*)key.getPtr(), 
                                                     key.getSize(), 
                                              (byte*)iv.getPtr());

   aes_enc.ProcessData( (byte*)unencrData.getPtr(), 
                        (byte*)data.getPtr(), 
                               data.getSize());

   return unencrData;
}


/////////////////////////////////////////////////////////////////////////////
// Same as above, but only changing the AES mode of operation (CBC, not CFB)
SecureBinaryData CryptoAES::EncryptCBC(SecureBinaryData & data, 
                                       SecureBinaryData & key,
                                       SecureBinaryData & iv)
{
   if(CRYPTO_DEBUG)
   {
      cout << "AES Decrypt" << endl;
      cout << "   BinData: " << data.toHexStr() << endl;
      cout << "   BinKey : " << key.toHexStr() << endl;
      cout << "   BinIV  : " << iv.toHexStr() << endl;
   }

   if(data.getSize() == 0)
      return SecureBinaryData(0);

   SecureBinaryData encrData(data.getSize());

   // Caller can supply their own IV/entropy, or let it be generated here
   // (variable "iv" is a reference, so check it on the way out)
   if(iv.getSize() == 0)
      iv = SecureBinaryData().GenerateRandom(BTC_AES::BLOCKSIZE);


   BTC_CBC_MODE<BTC_AES>::Encryption aes_enc( (byte*)key.getPtr(), 
                                                     key.getSize(), 
                                              (byte*)iv.getPtr());

   aes_enc.ProcessData( (byte*)encrData.getPtr(), 
                        (byte*)data.getPtr(), 
                               data.getSize());

   return encrData;
}

/////////////////////////////////////////////////////////////////////////////
// Same as above, but only changing the AES mode of operation (CBC, not CFB)
SecureBinaryData CryptoAES::DecryptCBC(SecureBinaryData & data, 
                                       SecureBinaryData & key,
                                       SecureBinaryData   iv  )
{
   if(CRYPTO_DEBUG)
   {
      cout << "AES Decrypt" << endl;
      cout << "   BinData: " << data.toHexStr() << endl;
      cout << "   BinKey : " << key.toHexStr() << endl;
      cout << "   BinIV  : " << iv.toHexStr() << endl;
   }

   if(data.getSize() == 0)
      return SecureBinaryData(0);

   SecureBinaryData unencrData(data.getSize());

   BTC_CBC_MODE<BTC_AES>::Decryption aes_enc( (byte*)key.getPtr(), 
                                                     key.getSize(), 
                                              (byte*)iv.getPtr());

   aes_enc.ProcessData( (byte*)unencrData.getPtr(), 
                        (byte*)data.getPtr(), 
                               data.getSize());
   return unencrData;
}


// Create a new Crypto++ ECDSA private key based off 32 bytes of PRNG-generated
// data.
// INPUT:  32 bytes of entropy  (SecureBinaryData)
// OUTPUT: None
// RETURN: Crypto++ private key  (BTC_PRIVKEY)
/////////////////////////////////////////////////////////////////////////////
BTC_PRIVKEY CryptoECDSA::CreateNewPrivateKey(SecureBinaryData entropy)
{
   return ParsePrivateKey(SecureBinaryData().GenerateRandom2xXOR(32, entropy));
}


// Create a new Crypto++ ECDSA private key using an incoming private key. The
// incoming key must be 32 bytes long.
// INPUT:  A 32 byte private key  (const SecureBinaryData&)
// OUTPUT: None
// RETURN: A Crypto++ private key  (BTC_PRIVKEY)
/////////////////////////////////////////////////////////////////////////////
BTC_PRIVKEY CryptoECDSA::ParsePrivateKey(SecureBinaryData const & privKeyData)
{
   assert(privKeyData.getSize() == 32);

   BTC_PRIVKEY cppPrivKey;
   CryptoPP::Integer privateExp;
   privateExp.Decode(privKeyData.getPtr(), privKeyData.getSize(), UNSIGNED);
   cppPrivKey.Initialize(CryptoPP::ASN1::secp256k1(), privateExp);
   return cppPrivKey;
}


// Create a new Crypto++ ECDSA public key using an incoming public key. The
// incoming key must be 65 bytes long.
// INPUT:  A 65 byte public key  (const SecureBinaryData&)
// OUTPUT: None
// RETURN: A Crypto++ public key  (BTC_PUBKEY)
/////////////////////////////////////////////////////////////////////////////
BTC_PUBKEY CryptoECDSA::ParsePublicKey(SecureBinaryData const & pubKey65B)
{
   assert(pubKey65B.getSize() == 65);

   SecureBinaryData pubXbin(pubKey65B.getSliceRef( 1,32));
   SecureBinaryData pubYbin(pubKey65B.getSliceRef(33,32));
   return ParsePublicKey(pubXbin, pubYbin);
}

// Create a new Crypto++ ECDSA public key using incoming public X/Y coordinates.
// The incoming coordinates must be 32 bytes long.
// INPUT:  A 32 byte public key X-coordinate  (const SecureBinaryData&)
//         A 32 byte public key Y-coordinate  (const SecureBinaryData&)
// OUTPUT: None
// RETURN: A Crypto++ public key  (BTC_PUBKEY)
/////////////////////////////////////////////////////////////////////////////
BTC_PUBKEY CryptoECDSA::ParsePublicKey(SecureBinaryData const & pubKeyX32B,
                                       SecureBinaryData const & pubKeyY32B)
{
   assert(pubKeyX32B.getSize() == 32);
   assert(pubKeyY32B.getSize() == 32);

   BTC_PUBKEY cppPubKey;

   CryptoPP::Integer pubX;
   CryptoPP::Integer pubY;
   pubX.Decode(pubKeyX32B.getPtr(), pubKeyX32B.getSize(), UNSIGNED);
   pubY.Decode(pubKeyY32B.getPtr(), pubKeyY32B.getSize(), UNSIGNED);
   BTC_ECPOINT publicPoint(pubX, pubY);

   // Initialize the public key with the ECP point just created
   cppPubKey.Initialize(CryptoPP::ASN1::secp256k1(), publicPoint);

   // Validate the public key -- not sure why this needs a PRNG
   BTC_PRNG prng;
   assert(cppPubKey.Validate(prng, 3));

   return cppPubKey;
}

// Serialize a Crypto+ ECDSA private key. The result will be 32 bytes long.
// INPUT:  A Crypto++ private key  (const BTC_PRIVKEY&)
// OUTPUT: None
// RETURN: A 32 byte buffer with the private key  (SecureBinaryData)
/////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::SerializePrivateKey(BTC_PRIVKEY const & privKey)
{
   CryptoPP::Integer privateExp = privKey.GetPrivateExponent();
   SecureBinaryData privKeyData(32);
   privateExp.Encode(privKeyData.getPtr(), privKeyData.getSize(), UNSIGNED);
   return privKeyData;
}
   
// Serialize a Crypto+ ECDSA private key. The result will be 65 bytes long.
// INPUT:  A Crypto++ public key  (const BTC_PUBKEY&)
// OUTPUT: None
// RETURN: A 65 byte buffer with the public key  (SecureBinaryData)
/////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::SerializePublicKey(BTC_PUBKEY const & pubKey)
{
   BTC_ECPOINT publicPoint = pubKey.GetPublicElement();
   CryptoPP::Integer pubX = publicPoint.x;
   CryptoPP::Integer pubY = publicPoint.y;
   SecureBinaryData pubData(65);
   pubData.fill(0x04);  // we fill just to set the first byte...

   pubX.Encode(pubData.getPtr()+1,  32, UNSIGNED);
   pubY.Encode(pubData.getPtr()+33, 32, UNSIGNED);
   return pubData;
}

// Compute a public key based on an incoming private key.
// INPUT:  A 32-byte buffer with a private key. (const SecureBinaryData&)
// OUTPUT: None
// RETURN: A 65-byte buffer with an uncompressed public key. (SecureBinaryData)
/////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::ComputePublicKey(SecureBinaryData const & cppPrivKey)
{
   assert(cppPrivKey.getSize() == 32);

   BTC_PRIVKEY pk = ParsePrivateKey(cppPrivKey);
   BTC_PUBKEY  pub;
   pk.MakePublicKey(pub);
   return SerializePublicKey(pub);
}


// Compute a Crypto++ public key based on an incoming Crypto++ private key.
// INPUT:  A Crypto++ private key. (const BTC_PRIVKEY&)
// OUTPUT: None
// RETURN: A Crypto++ uncompressed public key. (BTC_PUBKEY)
/////////////////////////////////////////////////////////////////////////////
BTC_PUBKEY CryptoECDSA::ComputePublicKey(BTC_PRIVKEY const & cppPrivKey)
{
   BTC_PUBKEY cppPubKey;
   cppPrivKey.MakePublicKey(cppPubKey);

   // Validate the public key -- not sure why this needs a prng...
   BTC_PRNG prng;
   assert(cppPubKey.Validate(prng, 3));

   return cppPubKey;
}


// Generate a private key from an entropy value.
// INPUT:  32 bytes of entropy  (SecureBinaryData)
// OUTPUT: None
// RETURN: A 32 byte buffer with the private key  (SecureBinaryData)
////////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::GenerateNewPrivateKey(SecureBinaryData entropy)
{
   return SecureBinaryData().GenerateRandom(32, entropy);
}


// Check to see if the public key generated from a private key matches an
// incoming public key.
// INPUT:  Crypto++ private key that will generate a pub key. (BTC_PRIVKEY)
//         Crypto++ public key that will be compared. (BTC_PUBKEY)
// OUTPUT: None
// RETURN: Bool indicating if there's a match (true) or not (false).
////////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::CheckPubPrivKeyMatch(BTC_PRIVKEY const & cppPrivKey,
                                       BTC_PUBKEY  const & cppPubKey)
{
   BTC_PUBKEY computedPubKey;
   cppPrivKey.MakePublicKey(computedPubKey);
   
   BTC_ECPOINT ppA = cppPubKey.GetPublicElement();
   BTC_ECPOINT ppB = computedPubKey.GetPublicElement();
   return (ppA.x==ppB.x && ppA.y==ppB.y);
}

// Check to see if the public key generated from a private key matches an
// incoming public key.
// INPUT:  Private key that will generate a pub key. (const SecureBinaryData&)
//         Public key that will be compared. (const SecureBinaryData&)
// OUTPUT: None
// RETURN: Bool indicating if there's a match (true) or not (false).
/////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::CheckPubPrivKeyMatch(SecureBinaryData const & privKey32,
                                       SecureBinaryData const & pubKey33or65)
{
   assert(privKey32.getSize() == 32);
   assert(pubKey33or65.getSize() == 33 || pubKey33or65.getSize()==65);
   
   if(CRYPTO_DEBUG)
   {
      cout << "CheckPubPrivKeyMatch:" << endl;
      cout << "   BinPrv: " << privKey32.toHexStr() << endl;
      cout << "   BinPub: " << pubKey33or65.toHexStr() << endl;
   }

   BTC_PRIVKEY privKey = ParsePrivateKey(privKey32);
   BTC_PUBKEY  pubKey  = ParsePublicKey(pubKey33or65);
   return CheckPubPrivKeyMatch(privKey, pubKey);
}


// Verify that an incoming public key is on the secp256k1 curve.
// INPUT:  A compressed or uncompressed public key  (const SecureBinaryData&)
// OUTPUT: None
// RETURN: Bool indicating if the key's on the curve (true) or not (false).
bool CryptoECDSA::VerifyPublicKeyValid(SecureBinaryData const & pubKey33or65)
{
   if(CRYPTO_DEBUG)
   {
      cout << "BinPub: " << pubKey33or65.toHexStr() << endl;
   }

   SecureBinaryData keyToCheck(65);

   // To support compressed keys, we'll just check to see if a key is compressed
   // and then decompress it.
   if(pubKey33or65.getSize() == 33)
   {
      keyToCheck = UncompressPoint(pubKey33or65);
   }
   else
   { 
      keyToCheck = pubKey33or65;
   }

   // Basically just copying the ParsePublicKey method, but without
   // the assert that would throw an error from C++
   SecureBinaryData pubXbin(keyToCheck.getSliceRef( 1,32));
   SecureBinaryData pubYbin(keyToCheck.getSliceRef(33,32));
   CryptoPP::Integer pubX;
   CryptoPP::Integer pubY;
   pubX.Decode(pubXbin.getPtr(), pubXbin.getSize(), UNSIGNED);
   pubY.Decode(pubYbin.getPtr(), pubYbin.getSize(), UNSIGNED);
   BTC_ECPOINT publicPoint(pubX, pubY);

   // Initialize the public key with the ECP point just created
   BTC_PUBKEY cppPubKey;
   cppPubKey.Initialize(CryptoPP::ASN1::secp256k1(), publicPoint);

   // Validate the public key -- not sure why this needs a PRNG
   BTC_PRNG prng;
   return cppPubKey.Validate(prng, 3);
}


/////////////////////////////////////////////////////////////////////////////
// Use the secp256k1 curve to sign data of an arbitrary length.
// Input:  Data to sign  (const SecureBinaryData&)
//         The private key used to sign the data  (const SecureBinaryData&)
//         A flag indicating if deterministic signing is used  (const bool&)
// Output: None
// Return: The signature of the data  (SecureBinaryData)
SecureBinaryData CryptoECDSA::SignData(SecureBinaryData const & binToSign, 
                                       SecureBinaryData const & binPrivKey,
                                       const bool& detSign)
{
   if(CRYPTO_DEBUG)
   {
      cout << "SignData:" << endl;
      cout << "   BinSgn: " << binToSign.getSize() << " " << binToSign.toHexStr() << endl;
      cout << "   BinPrv: " << binPrivKey.getSize() << " " << binPrivKey.toHexStr() << endl;
      cout << "  DetSign: " << detSign << endl;
   }

   BTC_PRIVKEY cppPrivKey = ParsePrivateKey(binPrivKey);
   return SignData(binToSign, cppPrivKey, detSign);
}


/////////////////////////////////////////////////////////////////////////////
// Use the secp256k1 curve to sign data of an arbitrary length.
// Input:  Data to sign  (const SecureBinaryData&)
//         The private key used to sign the data  (const BTC_PRIVKEY&)
//         A flag indicating if deterministic signing is used  (const bool&)
// Output: None
// Return: The signature of the data  (SecureBinaryData)
SecureBinaryData CryptoECDSA::SignData(SecureBinaryData const & binToSign, 
                                       BTC_PRIVKEY const & cppPrivKey,
                                       const bool& detSign)
{

   // We trick the Crypto++ ECDSA module by passing it a single-hashed
   // message, it will do the second hash before it signs it.  This is 
   // exactly what we need.
   CryptoPP::SHA256  sha256;
   BTC_PRNG prng;

   // Execute the first sha256 op -- the signer will do the other one
   SecureBinaryData hashVal(32);
   sha256.CalculateDigest(hashVal.getPtr(), 
                          binToSign.getPtr(), 
                          binToSign.getSize());

   // Do we want to use a PRNG or use deterministic signing (RFC 6979)?
   string signature;
   if(detSign)
   {
      BTC_DETSIGNER signer(cppPrivKey);
      CryptoPP::StringSource(
         hashVal.toBinStr(), true, new CryptoPP::SignerFilter(
         prng, signer, new CryptoPP::StringSink(signature)));
   }
   else
   {
      BTC_SIGNER signer(cppPrivKey);
      CryptoPP::StringSource(
         hashVal.toBinStr(), true, new CryptoPP::SignerFilter(
         prng, signer, new CryptoPP::StringSink(signature)));
   }

   return SecureBinaryData(signature);
}


// Verification of a message and its signature.
// INPUT:  The message to verify.
//         The signature used to verify the message.
//         A 65-byte buffer with the public key used to verify the message.
// OUTPUT: None
// RETURN: Bool indicating if the message is verified (true) or not (false).
/////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::VerifyData(SecureBinaryData const & binMessage, 
                             SecureBinaryData const & binSignature,
                             SecureBinaryData const & pubkey65B)
{
   assert(pubkey65B.getSize() == 65);

   if(CRYPTO_DEBUG)
   {
      cout << "VerifyData:" << endl;
      cout << "   BinMsg: " << binMessage.toHexStr() << endl;
      cout << "   BinSig: " << binSignature.toHexStr() << endl;
      cout << "   BinPub: " << pubkey65B.toHexStr() << endl;
   }

   BTC_PUBKEY cppPubKey = ParsePublicKey(pubkey65B);
   return VerifyData(binMessage, binSignature, cppPubKey);
}


// Verification of a message and its signature.
// INPUT:  The message to verify.
//         The signature used to verify the message.
//         A Crypto++ public key used to verify the message.
// OUTPUT: None
// RETURN: Bool indicating if the message is verified (true) or not (false).
/////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::VerifyData(SecureBinaryData const & binMessage, 
                             SecureBinaryData const & binSignature,
                             BTC_PUBKEY const & cppPubKey)
                            
{
   CryptoPP::SHA256  sha256;
   BTC_PRNG prng;

   assert(cppPubKey.Validate(prng, 3));

   // We execute the first SHA256 op, here.  Next one is done by Verifier
   SecureBinaryData hashVal(32);
   sha256.CalculateDigest(hashVal.getPtr(), 
                          binMessage.getPtr(), 
                          binMessage.getSize());

   // Verifying message 
   BTC_VERIFIER verifier(cppPubKey); 
   return verifier.VerifyMessage((const byte*)hashVal.getPtr(), 
                                              hashVal.getSize(),
                                 (const byte*)binSignature.getPtr(), 
                                              binSignature.getSize());
}


/////////////////////////////////////////////////////////////////////////////
// Deterministically generate new private key using a chaincode. (Used for
// legacy (pre-2.0) wallets.)
// Changed:  added using the hash of the public key to the mix
//           b/c multiplying by the chaincode alone is too "linear"
//           (there's no reason to believe it's insecure, but it doesn't
//           hurt to add some extra entropy/non-linearity to the chain
//           generation process)
SecureBinaryData CryptoECDSA::ComputeChainedPrivateKey(
                                 SecureBinaryData const & binPrivKey,
                                 SecureBinaryData const & chaincode,
                                 SecureBinaryData binPubKey,
                                 SecureBinaryData* multiplierOut)
{
   if(CRYPTO_DEBUG)
   {
      cout << "ComputeChainedPrivateKey:" << endl;
      cout << "   BinPrv: " << binPrivKey.toHexStr() << endl;
      cout << "   BinChn: " << chaincode.toHexStr() << endl;
      cout << "   BinPub: " << binPubKey.toHexStr() << endl;
   }

   if( binPubKey.getSize()==0 )
   {
      binPubKey = ComputePublicKey(binPrivKey);
   }

   if( binPrivKey.getSize() != 32 || chaincode.getSize() != 32)
   {
      LOGERR << "***ERROR:  Invalid private key or chaincode (both must be 32B)";
      LOGERR << "BinPrivKey size: " << binPrivKey.getSize();
      LOGERR << "BinPrivKey: (not logged for security)";
      //LOGERR << "BinPrivKey: " << binPrivKey.toHexStr();
      LOGERR << "BinChain  : " << chaincode.getSize();
      LOGERR << "BinChain  : " << chaincode.toHexStr();
   }

   // Adding extra entropy to chaincode by xor'ing with hash256 of pubkey
   BinaryData chainMod  = binPubKey.getHash256();
   BinaryData chainOrig = chaincode.getRawCopy();
   BinaryData chainXor(32);
      
   for(uint8_t i=0; i<8; i++)
   {
      uint8_t offset = 4*i;
      *(uint32_t*)(chainXor.getPtr()+offset) =
                           *(uint32_t*)( chainMod.getPtr()+offset) ^ 
                           *(uint32_t*)(chainOrig.getPtr()+offset);
   }
   
   CryptoPP::Integer mult, origPrivExp, ecOrder;
   // A
   mult.Decode(chainXor.getPtr(), chainXor.getSize(), UNSIGNED);
   // B
   origPrivExp.Decode(binPrivKey.getPtr(), binPrivKey.getSize(), UNSIGNED);
   // C
   ecOrder.Decode(ecOrder_BE.getPtr(), ecOrder_BE.getSize(), UNSIGNED);

   // A*B mod C will get us a new private key exponent
   CryptoPP::Integer newPrivExponent =
                  a_times_b_mod_c(mult, origPrivExp, ecOrder);

   // Convert new private exponent to big-endian binary string
   SecureBinaryData newPrivData(32);
   newPrivExponent.Encode(newPrivData.getPtr(), newPrivData.getSize(), UNSIGNED);

   if(multiplierOut != NULL)
      (*multiplierOut) = SecureBinaryData(chainXor);

   //LOGINFO << "Computed new chained private key using:";
   //LOGINFO << "   Public key: " << binPubKey.toHexStr().c_str();
   //LOGINFO << "   PubKeyHash: " << chainMod.toHexStr().c_str();
   //LOGINFO << "   Chaincode:  " << chainOrig.toHexStr().c_str();
   //LOGINFO << "   Multiplier: " << chainXor.toHexStr().c_str();

   return newPrivData;
}


/////////////////////////////////////////////////////////////////////////////
// Deterministically generate new public key using a chaincode. (Used for
// legacy (pre-2.0) wallets.)
SecureBinaryData CryptoECDSA::ComputeChainedPublicKey(
                                SecureBinaryData const & binPubKey,
                                SecureBinaryData const & chaincode,
                                SecureBinaryData* multiplierOut)
{
   if(CRYPTO_DEBUG)
   {
      cout << "ComputeChainedPUBLICKey:" << endl;
      cout << "   BinPub: " << binPubKey.toHexStr() << endl;
      cout << "   BinChn: " << chaincode.toHexStr() << endl;
   }
   // Added extra entropy to chaincode by xor'ing with hash256 of pubkey
   BinaryData chainMod  = binPubKey.getHash256();
   BinaryData chainOrig = chaincode.getRawCopy();
   BinaryData chainXor(32);
      
   for(uint8_t i=0; i<8; i++)
   {
      uint8_t offset = 4*i;
      *(uint32_t*)(chainXor.getPtr()+offset) =
                           *(uint32_t*)( chainMod.getPtr()+offset) ^ 
                           *(uint32_t*)(chainOrig.getPtr()+offset);
   }

   // Parse the chaincode as a big-endian integer
   CryptoPP::Integer mult;
   mult.Decode(chainXor.getPtr(), chainXor.getSize(), UNSIGNED);

   // "new" init as "old", to make sure it's initialized on the correct curve
   BTC_PUBKEY oldPubKey = ParsePublicKey(binPubKey); 
   BTC_PUBKEY newPubKey = ParsePublicKey(binPubKey);

   // Let Crypto++ do the EC math for us, serialize the new public key
   newPubKey.SetPublicElement( oldPubKey.ExponentiatePublicElement(mult) );

   if(multiplierOut != NULL)
      (*multiplierOut) = SecureBinaryData(chainXor);

   //LOGINFO << "Computed new chained public key using:";
   //LOGINFO << "   Public key: " << binPubKey.toHexStr().c_str();
   //LOGINFO << "   PubKeyHash: " << chainMod.toHexStr().c_str();
   //LOGINFO << "   Chaincode:  " << chainOrig.toHexStr().c_str();
   //LOGINFO << "   Multiplier: " << chainXor.toHexStr().c_str();

   return CryptoECDSA::SerializePublicKey(newPubKey);
}


// Calculate the multiplicative inverse of the input modulo the secp256k1 order.
////////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::InvMod(const SecureBinaryData& m)
{
   CryptoPP::Integer cppM;
   CryptoPP::Integer cppModulo;
   cppM.Decode(m.getPtr(), m.getSize(), UNSIGNED);
   cppModulo.Decode(ecOrder_BE.getPtr(), ecOrder_BE.getSize(), UNSIGNED);
   CryptoPP::Integer cppResult = cppM.InverseMod(cppModulo);
   SecureBinaryData result(32);
   cppResult.Encode(result.getPtr(), result.getSize(), UNSIGNED);
   return result;
}


// Function verifying that given X/Y coordinates are on the secp256k1 curve.
////////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::ECVerifyPoint(BinaryData const & x,
                                BinaryData const & y)
{
   BTC_PUBKEY cppPubKey;

   CryptoPP::Integer pubX;
   CryptoPP::Integer pubY;
   pubX.Decode(x.getPtr(), x.getSize(), UNSIGNED);
   pubY.Decode(y.getPtr(), y.getSize(), UNSIGNED);
   BTC_ECPOINT publicPoint(pubX, pubY);

   // Initialize the public key with the ECP point just created
   cppPubKey.Initialize(CryptoPP::ASN1::secp256k1(), publicPoint);

   // Validate the public key -- not sure why this needs a PRNG
   BTC_PRNG prng;
   return cppPubKey.Validate(prng, 3);
}


// Function that returns the Crypto++ ECP object for the secp256k1 curve. This
// object is used to perform math on the secp256k1 curve.
////////////////////////////////////////////////////////////////////////////////
CryptoPP::ECP CryptoECDSA::Get_secp256k1_ECP(void)
{
   static bool firstRun = true;
   static CryptoPP::Integer intP;
   static CryptoPP::Integer inta;
   static CryptoPP::Integer intb;

   static BinaryData P;
   static BinaryData a;
   static BinaryData b;

   if(firstRun)
   {
      // Data taken from SEC 2, Sect. 2.7.1.
      firstRun = false;
      P = BinaryData::CreateFromHex(
            "fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f");
      a = BinaryData::CreateFromHex(
            "0000000000000000000000000000000000000000000000000000000000000000");
      b = BinaryData::CreateFromHex(
            "0000000000000000000000000000000000000000000000000000000000000007");

      intP.Decode( P.getPtr(),  P.getSize(),  UNSIGNED);
      inta.Decode( a.getPtr(),  a.getSize(),  UNSIGNED);
      intb.Decode( b.getPtr(),  b.getSize(),  UNSIGNED);
   }

   
   return CryptoPP::ECP(intP, inta, intb);
}


// Function multiplying two scalars on the secp256k1 curve (32 bytes each) and
// returning the result.
////////////////////////////////////////////////////////////////////////////////
BinaryData CryptoECDSA::ECMultiplyScalars(BinaryData const & A,
                                          BinaryData const & B)
{
   // Let Crypto++ do the actual multiplication & modulo.
   CryptoPP::Integer intA, intB, intC, intCurveOrd;
   intA.Decode(A.getPtr(), A.getSize(), UNSIGNED);
   intB.Decode(B.getPtr(), B.getSize(), UNSIGNED);
   intCurveOrd.Decode(ecOrder_BE.getPtr(), ecOrder_BE.getSize(), UNSIGNED);
   intC = a_times_b_mod_c(intA, intB, intCurveOrd);

   BinaryData C(32);
   intC.Encode(C.getPtr(), 32, UNSIGNED);
   return C;
}


// Function that multiplies an incoming scalar by the secp256k1 generator and
// adds the result to incoming point (X/Y coordinates).
// INPUT:  Scalar (A) and X/Y coordinates for a point (Bx & By) (32 bytes each).
// OUTPUT: The multiply result (64 bytes).
// RETURN: True if a valid result, false if at infinity (incredibly unlikely)
////////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::ECMultiplyPoint(BinaryData const & A,
                                  BinaryData const & Bx,
                                  BinaryData const & By,
                                  BinaryData& multResult)
{
   CryptoPP::ECP ecp = Get_secp256k1_ECP();
   CryptoPP::Integer intA, intBx, intBy, intCx, intCy;
   bool validResult = true;
   intA.Decode( A.getPtr(),  A.getSize(),  UNSIGNED);

   // Math is taken from ANSI X9.62 (Sect. D.3.2/1998 or I.3.1/2005).
   multResult.clear();
   multResult = BinaryData(64);
   intBx.Decode(Bx.getPtr(), Bx.getSize(), UNSIGNED);
   intBy.Decode(By.getPtr(), By.getSize(), UNSIGNED);
   BTC_ECPOINT B(intBx, intBy);
   BTC_ECPOINT C = ecp.ScalarMultiply(B, intA);
   C.x.Encode(multResult.getPtr(),    32, UNSIGNED);
   C.y.Encode(multResult.getPtr()+32, 32, UNSIGNED);

   // We can't proceed if we're at infinity, even if the likelihood is LOW!!!
   if(C.identity)
   {
      validResult = false;
   }

   return validResult;
}


// Function that adds two points (X/Y coordinates) together, modulo the
// secp256k1 finite field (Fp).
// INPUT:  X & Y coordinates for points A & B (32 bytes each).
// OUTPUT: The addition result (64 bytes).
// RETURN: True if a valid result, false if at infinity (incredibly unlikely)
////////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::ECAddPoints(BinaryData const & Ax,
                              BinaryData const & Ay,
                              BinaryData const & Bx,
                              BinaryData const & By,
                              BinaryData& addResult)
{
   CryptoPP::ECP ecp = Get_secp256k1_ECP();
   CryptoPP::Integer intAx, intAy, intBx, intBy, intCx, intCy;
   bool validResult = true;

   intAx.Decode(Ax.getPtr(), Ax.getSize(), UNSIGNED);
   intAy.Decode(Ay.getPtr(), Ay.getSize(), UNSIGNED);
   intBx.Decode(Bx.getPtr(), Bx.getSize(), UNSIGNED);
   intBy.Decode(By.getPtr(), By.getSize(), UNSIGNED);

   // Math is taken from ANSI X9.62 (Sect. B.3/1998 or G.3/2005).
   BTC_ECPOINT A(intAx, intAy);
   BTC_ECPOINT B(intBx, intBy);
   BTC_ECPOINT C = ecp.Add(A,B);

   addResult.clear();
   addResult = BinaryData(64);
   C.x.Encode(addResult.getPtr(),    32, UNSIGNED);
   C.y.Encode(addResult.getPtr()+32, 32, UNSIGNED);
   if(C.identity)
   {
      validResult = false;
   }

   return validResult;
}


// Function that takes an incoming point (X/Y coords) on the secp256k1 curve and
// returns the inverse. (The inverse is the original X coordinate and the
// inverted Y coordinate (i.e., the bits are flipped).
// INPUT:  X & Y coordinates for point A.
// OUTPUT: The inversion result.
// RETURN: True if a valid result, false if at infinity (incredibly unlikely)
////////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::ECInverse(BinaryData const & Ax, 
                            BinaryData const & Ay,
                            BinaryData& invResult)
{
   CryptoPP::ECP ecp = Get_secp256k1_ECP();
   CryptoPP::Integer intAx, intAy, intCx, intCy;
   bool validResult = true;

   intAx.Decode(Ax.getPtr(), Ax.getSize(), UNSIGNED);
   intAy.Decode(Ay.getPtr(), Ay.getSize(), UNSIGNED);

   // Math is taken from ANSI X9.62 (Sect. B.1/1998 or G.1/2005).
   BTC_ECPOINT A(intAx, intAy);
   BTC_ECPOINT C = ecp.Inverse(A);

   invResult.clear();
   invResult = BinaryData(64);
   C.x.Encode(invResult.getPtr(),    32, UNSIGNED);
   C.y.Encode(invResult.getPtr()+32, 32, UNSIGNED);
   if(C.identity)
   {
       validResult = false;
   }

   return validResult;
}


// Function that takes a signature and message hash and returns the 
// pubkey.
////////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::GetPubKeyFromSigAndMsgHash(SecureBinaryData const & sig, SecureBinaryData const & msgHash)
{
   assert(sig.getSize() == 65);
   assert(msgHash.getSize() == 32);

   int hs = sig.toBinStr()[0];
   assert(hs >= 27 && hs < 35);

   bool compressed = (hs - 27) >= 4;
   bool addOrder = (hs - 27) % 4 >= 2;
   bool even = (hs - 27) % 2 == 0;

   CryptoPP::Integer intR, intS, intE, intN, intX, Gx, Gy;
   intR.Decode(sig.getPtr() + 1, 32, UNSIGNED);
   intS.Decode(sig.getPtr() + 33, 32, UNSIGNED);
   intN.Decode(ecOrder_BE.getPtr(), ecOrder_BE.getSize(), UNSIGNED);
   intE.Decode(msgHash.getPtr(), msgHash.getSize(), UNSIGNED);
   Gx.Decode(ecGenX_BE.getPtr(), ecGenX_BE.getSize(), UNSIGNED);
   Gy.Decode(ecGenY_BE.getPtr(), ecGenY_BE.getSize(), UNSIGNED);

   CryptoPP::ECP ecp = Get_secp256k1_ECP();
   CryptoPP::Integer intP = ecp.FieldSize();
   CryptoPP::Integer b = ecp.GetB();

   // compute the point for multiplication with s
   intX = intR;
   if (addOrder) {
     intX = intX.Plus(intN).Modulo(intP);
   }

   SecureBinaryData tmp(32);
   intX.Encode((byte*)tmp.getPtr(), tmp.getSize(), UNSIGNED);
   SecureBinaryData r2(33);
   SecureBinaryData r3(33);
   r2 = SecureBinaryData('\x02' + tmp.toBinStr());
   r3 = SecureBinaryData('\x03' + tmp.toBinStr());

   SecureBinaryData pEven = UncompressPoint(r2);
   SecureBinaryData pOdd = UncompressPoint(r3);
   SecureBinaryData rBin(65);

   if ((pEven.toBinStr()[64] - (hs - 27)) % 2 == 0) {
     rBin = pEven;
   } else {
     rBin = pOdd;
   }

   BTC_ECPOINT G(Gx, Gy);
   BTC_ECPOINT R;
   ecp.DecodePoint(R, (byte*)rBin.getPtr(), 65);
   R = ecp.Multiply(intS, R);
   intE = CryptoPP::Integer::Zero().Minus(intE).Plus(intN);
   BTC_ECPOINT T = ecp.Multiply(intE, G);
   BTC_ECPOINT Q = ecp.Multiply(intR.InverseMod(intN), ecp.Add(R,T));
   assert(ecp.VerifyPoint(Q));
   
   if (compressed) {
     SecureBinaryData pt(33);
     ecp.EncodePoint((byte*)pt.getPtr(), Q, true);
     return pt; 
   }
   SecureBinaryData pt(65);
   ecp.EncodePoint((byte*)pt.getPtr(), Q, false);
   return pt; 
}


// Function that takes an incoming 65 byte public key and returns a 33 byte
// compressed version.
////////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::CompressPoint(SecureBinaryData const & pubKey65)
{
   // In case a compressed key is passed in, just send it right back out.
   if(pubKey65.getSize() == 33 && (pubKey65[0] == 0x02 || pubKey65[0] == 0x03))
   {
      return pubKey65;
   }

   // Let Crypto++ do the heavy lifting. Build uncompressed key, then compress.
   assert(pubKey65.getSize() == 65 && pubKey65[0] == 0x04);
   CryptoPP::ECP ecp = Get_secp256k1_ECP();
   BTC_ECPOINT ptPub;
   ecp.DecodePoint(ptPub, (byte*)pubKey65.getPtr(), 65);
   SecureBinaryData ptCompressed(33);
   ecp.EncodePoint((byte*)ptCompressed.getPtr(), ptPub, true);
   return ptCompressed; 
}


// Function that takes an incoming 33 byte public key and returns a 65 byte
// uncompressed version.
////////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::UncompressPoint(SecureBinaryData const & pubKey33)
{
   // In case an uncompressed key is passed in, just send it right back out.
   if(pubKey33.getSize() == 65 && pubKey33[0] == 0x04)
   {
      return pubKey33;
   }

   // Let Crypto++ do the heavy lifting. Build compressed key, then decompress.
   assert(pubKey33.getSize() == 33);
   CryptoPP::ECP ecp = Get_secp256k1_ECP();
   BTC_ECPOINT ptPub;
   ecp.DecodePoint(ptPub, (byte*)pubKey33.getPtr(), 33);
   SecureBinaryData ptUncompressed(65);
   ecp.EncodePoint((byte*)ptUncompressed.getPtr(), ptPub, false);
   return ptUncompressed; 

}


// Check to see if our primary key is public (compressed).
const bool ExtendedKey::isPub() const
{
   // Bail if the primary key doesn't exist.
   if(key_.getSize() == 0)
   {
      return false;
   }

   return (key_[0] == 0x02 || key_[0] == 0x03);
}


// Check to see if our primary key is private.
const bool ExtendedKey::isPrv() const
{
   // Bail if the primary key doesn't exist.
   if(key_.getSize() == 0)
   {
      return false;
   }

   return (key_[0] == 0x00);
}


// Function that returns the 4-byte fingerprint of the ExtendedKey. This is the
// first 4 bytes of the Hash160 of the compressed public key.
const SecureBinaryData ExtendedKey::getFingerprint() const 
{
   SecureBinaryData compressedPubKey = CryptoECDSA().CompressPoint(pubKey_);
   SecureBinaryData myHash = compressedPubKey.getHash160();
   return myHash.getSliceRef(0, 4);
}


// Function that returns the 20-byte identifier of the ExtendedKey. This is the
// Hash160 of the compressed public key.
const SecureBinaryData ExtendedKey::getIdentifier() const 
{
   SecureBinaryData compressedPubKey = CryptoECDSA().CompressPoint(pubKey_);
   return compressedPubKey.getHash160();
}


// Get the private key from the extended key.
// Input:  None
// Output: None
// Result: A 32-byte big-endian buffer with the private key, or zeroed out if
//         the extended key has only public key data (SecureBinaryData)
SecureBinaryData ExtendedKey::getPrivateKey(bool withZeroByte) const
{
   SecureBinaryData retVal(0);

   if(isPrv())
   {
      retVal = key_;
      if(!withZeroByte)
      {
         retVal = retVal.getSliceCopy(1,32);
      }
   }

   return retVal;
}


// Get the public key from the extended key. The default format is compressed.
// Input:  A flag indicating if the key should be compressed (bool)
// Output: None
// Result: A big-endian buffer with the compressed (33-byte) or uncompressed
//         (65-byte) public key (SecureBinaryData)
SecureBinaryData ExtendedKey::getPublicKey(bool compr) const
{
   SecureBinaryData retVal;

   // Keep logic simple and just compress the public key instead of determining
   // if the primary key is already compressed.
   if(compr)
   {
      retVal = CryptoECDSA().CompressPoint(pubKey_);
   }
   else
   {
      retVal = pubKey_;
   }

   return retVal;
}


// Function that performs a Hash160 (SHA256, then RIPEMD160) on the uncompressed
// public key, which is used as the Hash160 value of the entire key.
// INPUT:  None
// OUTPUT: None
// RETURN: 20 byte Hash160 result.
////////////////////////////////////////////////////////////////////////////////
BinaryData ExtendedKey::getHash160() const
{
   return BtcUtils::getHash160(pubKey_.getPtr(), pubKey_.getSize());
}


// Get the key's current index. Will be 0 if it's the master key.
////////////////////////////////////////////////////////////////////////////////
uint32_t ExtendedKey::getChildNum() const
{
   uint32_t retVal = 0;

   // If the indices list is empty, we're the master key.
   if(indicesList_.size() != 0)
   {
      list<uint32_t>::const_iterator iter = indicesList_.end();
      --iter;
      retVal = *iter;
   }

   return retVal;
}


// Get a vector showing where in the tree the key is located.
////////////////////////////////////////////////////////////////////////////////
vector<uint32_t> ExtendedKey::getIndicesVect() const
{
   list<uint32_t>::const_iterator iter;
   vector<uint32_t> out(indicesList_.size());
   uint32_t index = 0;
   for(iter=indicesList_.begin(); iter!=indicesList_.end(); ++iter)
   {
      out[index] = *iter;
      ++index;
   }
   return out;
}


// Overloaded constructor. Meant to be used with the HDCryptoWalletSeed contents
// to create a master ExtendedKey.
// INPUT:  Seed key (33 bytes)
//         Seed chain code (32 bytes)
// OUTPUT: None
// RETURN: A completed ExtendedKey object.
////////////////////////////////////////////////////////////////////////////////
ExtendedKey::ExtendedKey(SecureBinaryData const & key,
                         SecureBinaryData const & ch)
{
   assert(key.getSize() == 33);
   assert(ch.getSize() == 32);

   // If we're good to go, set about creating the master key.
   key_ = key;
   chaincode_ = ch;

   // This allows us to initialize a public extended key.
   if(key[0] == 0x02 || key[0] == 0x03)
   {
      pubKey_ = key.copy();
      version_ = PUBVER;
   }
   else
      version_ = PRVVER;

   updatePubKey();
   parentFP_ = SecureBinaryData::CreateFromHex("00000000");
   validKey_ = true;
}


// Overloaded constructor.
// INPUT:  Incoming private (33 bytes) or public (65 bytes) key.
//         Chain code (32 bytes)
//         Hash160 of the parent (20 bytes)
//         Bool indicating if the incoming key is pub (true) or prv (false).
// OUTPUT: None
// RETURN: A completed ExtendedKey object.
////////////////////////////////////////////////////////////////////////////////
ExtendedKey::ExtendedKey(SecureBinaryData const & key,
                         SecureBinaryData const & ch,
                         SecureBinaryData const & parFP,
                         list<uint32_t> parentTreeIdx,
                         uint32_t netVer,
                         uint32_t inChildNum,
                         bool keyIsPub) :
   chaincode_(ch),
   indicesList_(parentTreeIdx),
   version_(netVer)
{
   assert(key.getSize() == 33 || key.getSize() == 65);
   assert(ch.getSize() == 32);
   assert(parFP.getSize() == 4);

   parentFP_ = parFP.getSliceRef(0, 4);
   indicesList_.push_back(inChildNum);

   // Create and compute keys as required. Let Crypto++ do the heavy lifting.
   if(keyIsPub)
   {
      key_ = CryptoECDSA().CompressPoint(key);
      pubKey_ = key;
   }
   else
   {
      key_ = key;
      BTC_PRIVKEY tmpA = CryptoECDSA().ParsePrivateKey(key_.getSliceRef(1, 32));
      BTC_PUBKEY tmpB = CryptoECDSA().ComputePublicKey(tmpA);
      pubKey_ = CryptoECDSA().SerializePublicKey(tmpB);
   }

   validKey_ = true;
}


// Overloaded constructor. Basically acts as a copy constructor.
// INPUT:  Incoming private key (33 bytes, or 0 bytes if not set).
//         Incoming public key (65 bytes).
//         Chain code (32 bytes)
//         Parent's fingerprint (uint32_t)
//         Position of the ExtendedKey  (list<uint32_t>)
//         Version (uint32_t)
//         Depth (uint8_t)
//         Child number (uint32_t)
// OUTPUT: None
// RETURN: A copy of an ExtendedKey object.
ExtendedKey::ExtendedKey(SecureBinaryData const & pr, 
                         SecureBinaryData const & pb, 
                         SecureBinaryData const & ch,
                         SecureBinaryData const & parFP,
                         list<uint32_t> parentTreeIdx,
                         uint32_t inVer,
                         uint32_t inChildNum) :
   key_(pr),
   pubKey_(pb),
   chaincode_(ch),
   indicesList_(parentTreeIdx),
   version_(inVer),
   parentFP_(parFP)
{
   assert(key_.getSize() == 0 || key_.getSize() == 33);
   assert(pubKey_.getSize() == 65);
   assert(chaincode_.getSize() == 32);
   parentFP_ = parFP.getSliceRef(0, 4);
   indicesList_.push_back(inChildNum);
   validKey_ = true;
}


// Delete the private key and replace it with the public key.
////////////////////////////////////////////////////////////////////////////////
void ExtendedKey::deletePrivateKey()
{
   if(key_[0] == 0x00)
   {
      // Get rid of the private key and compress the public key.
      key_.destroy();
      key_ = CryptoECDSA().CompressPoint(pubKey_);

      // Change the version value.
      if(version_ == MAIN_PRV)
      {
         version_ = MAIN_PUB;
      }
      else if(version_ == TEST_PRV)
      {
         version_ = TEST_PUB;
      }
      else
      {
         LOGERR << "Extended key (identifier " << getIdentifier().toHexStr()
            << ") has an invalid version!";
      }
   }
}


// Make a public copy of the ExtendedKey that doesn't have any private keys.
////////////////////////////////////////////////////////////////////////////////
ExtendedKey ExtendedKey::makePublicCopy()
{
   ExtendedKey ekout = copy();
   ekout.deletePrivateKey();
   return ekout;
}


// Clean up an ExtendedKey object. Not used for now.
////////////////////////////////////////////////////////////////////////////////
void ExtendedKey::destroy() {}


////////////////////////////////////////////////////////////////////////////////
// Strictly speaking, this isn't necessary, but I want a method in python/SWIG
// that guarantees I'm getting a copy, not a reference
ExtendedKey ExtendedKey::copy() const
{
   return ExtendedKey(key_, pubKey_, chaincode_, parentFP_, indicesList_,
                      version_, getChildNum());
}


////////////////////////////////////////////////////////////////////////////////
void ExtendedKey::debugPrint()
{
   cout << "Indices:                 " << getIndexListString() << endl;
   cout << "Fingerprint (Self):      " << getFingerprint().toHexStr() << endl;
   cout << "Fingerprint (Parent):    " << getParentFP().toHexStr() << endl;
   cout << "Private Key:             " << key_.toHexStr() << endl;
   cout << "Public Key Compressed:   " << CryptoECDSA().CompressPoint(pubKey_).toHexStr() << endl;
   cout << "Public Key Uncompressed: " << pubKey_.toHexStr() << endl;
   cout << "Chain Code:              " << chaincode_.toHexStr() << endl;
   cout << "Hash160 (Uncom Pub Key): " << getHash160().toHexStr() << endl << endl;
}


////////////////////////////////////////////////////////////////////////////////
const string ExtendedKey::getIndexListString(const string prefix)
{
   stringstream ss;
   ss << prefix;
   vector<uint32_t> indexList = getIndicesVect();

   // Loops through index list. If empty, key is a master key or is invalid.
   for(uint32_t i=0; i<indexList.size(); ++i)
   {
      if(isHardened(indexList[i]))
      {
         ss << "/" << (0x80000000 ^ indexList[i]) << "'";
      }
      else
      {
         ss << "/" << indexList[i];
      }
   }
   return ss.str();
}


// Function that updates the public key based on the primary key.
void ExtendedKey::updatePubKey()
{
   // If primary key is private, derive the uncompressed private key. If public,
   // just save an uncompressed copy.
   if(isPrv())
   {
      SecureBinaryData inPrvKey = key_.getSliceRef(1, 32);
      pubKey_ = CryptoECDSA().ComputePublicKey(inPrvKey);
   }
   else
   {
      pubKey_ = CryptoECDSA().UncompressPoint(pubKey_);
   }
}


// Function that returns the 78 byte, serialized, big/net endian extended key.
// If the ExtendedKey isn't valid yet, return an empty 78 byte buffer.
// Format is version/depth/parentFP/childNum/chainCode/key.
const SecureBinaryData ExtendedKey::getExtKeySer() 
{
   SecureBinaryData outKey;
   if(!validKey_)
   {
      // Zero-pad smaller keys
      SecureBinaryData zeros(78);
      zeros.fill(0x00);
      outKey = zeros;
   }
   else
   {
      SecureBinaryData tmpVal = WRITE_UINT32_BE(version_);
      outKey.append(tmpVal);
      tmpVal = WRITE_UINT8_BE(getDepth());
      outKey.append(tmpVal);
      outKey.append(parentFP_);
      tmpVal = WRITE_UINT32_BE(getChildNum());
      outKey.append(tmpVal);
      outKey.append(chaincode_);
      outKey.append(key_);
   }

   return outKey;
}


// Function indicating if an ExtendedKey is a master key.
const bool ExtendedKey::isMaster() const 
{
   return (indicesList_.size() == 0 && validKey_);
}


// Overloaded constructor that should be used instead of the default
// constructor. Takes incoming (P)RNG data and creates an HD master key and
// chain code.
// INPUT:  (P)RNG data seeding the HD crypto wallet. Must be 16-64 bytes.
//         (SecureBinaryData)
// OUTPUT: None
// RETURN: None
HDWalletCryptoSeed::HDWalletCryptoSeed(SecureBinaryData const& rngData) 
{
   SecureBinaryData hmacKey = SecureBinaryData("Bitcoin seed");
   SecureBinaryData hVal = HDWalletCrypto().HMAC_SHA512(hmacKey, rngData);
   masterKey_   = hVal.getSliceCopy( 0, 32);
   masterChain_ = hVal.getSliceCopy(32, 32);
}


// Function that performs an HMAC-SHA512 operation on an incoming key and data.
// INPUT:  The HMAC key.
// OUTPUT: The message that will be hashed.
// RETURN: The 64 byte output.
////////////////////////////////////////////////////////////////////////////////
SecureBinaryData HDWalletCrypto::HMAC_SHA512(SecureBinaryData key,
                                             SecureBinaryData msg)
{
   static uint32_t const BLOCKSIZE  = 128;

   if(key.getSize() > BLOCKSIZE) 
   { 
      // Reduce large keys via hash function.
      key = BtcUtils::getHash512(key);
   }
   else if(key.getSize() < BLOCKSIZE) 
   { 
      // Zero-pad smaller keys
      SecureBinaryData zeros(BLOCKSIZE - key.getSize());
      zeros.fill(0x00);
      key.append(zeros);
   }

   SecureBinaryData i_key_pad = key.XOR(0x36);
   SecureBinaryData o_key_pad = key.XOR(0x5c);

   // Inner hash operation
   i_key_pad.append(msg);
   SecureBinaryData innerHash;
   BtcUtils::getHash512(i_key_pad.getPtr(), i_key_pad.getSize(), innerHash);

   // Outer hash operation
   o_key_pad.append(innerHash);
   SecureBinaryData outerHash;
   BtcUtils::getHash512(o_key_pad.getPtr(), o_key_pad.getSize(), outerHash);

   return outerHash;
}


// The ExtendedKey class accommodates full private-included ExtendedKey objects
// or public-key-only.  You can pass in either one here, and it will derive the
// child for whatever key data is there. Note that this function doesn't perform
// private-to-public conversions. Such conversions will require the caller to
// manually convert a private key to a public key. For example, in the case of
// hardened public keys, a private-to-private derivation must occur, and the
// derived private key must then be converted to a public key.
//
// INPUT:  The parent key. (const ExtendedKey&)
//         The child number. (uint32_t)
// OUTPUT: If a buffer is sent in and the child isn't hardened, the code saves
//         the multiplier used to find the child's pub key. (SecureBinaryData*)
// RETURN: The child key. (ExtendedKey)
ExtendedKey HDWalletCrypto::childKeyDeriv(ExtendedKey const & extPar,
                                          uint32_t childNum,
                                          SecureBinaryData* multiplierOut)
{
   // Can't compute a child with no parent!
   assert(extPar.isInitialized());

   // Continue only if public-to-non-hardened-public derivation isn't requested.
   ExtendedKey derivKey;
   if(extPar.isPub() && isHardened(childNum))
   {
      LOGERR << "Cannot perform hardened derivation on public key #" << childNum
         << ". You must have access to the private key.";
   }
   else
   {
      SecureBinaryData childKey;
      bool derivSuccess = false;
      bool keyIsPub = false;

      // First, let's use HMAC-SHA512 to get some data. The key will always be
      // the parent's chain code. The HMAC-SHA512 msg will depend on if the
      // key's hardened. (| = Concatenation)
      //
      // Prv par (Hardened) - 0x00 | Prv par key | Incoming position
      // Pub par (Hardened) - Compressed pub par key | Incoming position
      // Prv or pub par (Non-hardened) - Compressed pub par key | Incoming pos
      //
      // At a glance, for non-hardened prv parents, this is incorrect. It is
      // correct. Point multiplication of the prv parent key yields the parent
      // pub key, which we already have. See X9.62:1998 (Sect. 5.2.1) or
      // X9.62:2005 (Sect. A.4.3) for the formal pub key derivation definition.
      SecureBinaryData binaryN = WRITE_UINT32_BE(childNum);
      SecureBinaryData hashData;

      if(isHardened(childNum))
      {
         SecureBinaryData pKey = extPar.getKey();
         hashData.append(pKey);
      }
      else
      {
         SecureBinaryData cp = extPar.getPublicKey();
         hashData.append(cp);
      }
      hashData.append(binaryN);

      // Hash that sucker and slice up the result!
      SecureBinaryData hVal = HMAC_SHA512(extPar.getChaincode(), hashData);
      SecureBinaryData leftHMAC = hVal.getSliceRef(0, 32);
      SecureBinaryData rightHMAC = hVal.getSliceRef(32, 32);

      // Curve order taken from SEC 2, Sect. 2.7.1.
      CryptoPP::Integer intLeft;
      CryptoPP::Integer ecOrder;
      ecOrder.Decode(ecOrder_BE.getPtr(), ecOrder_BE.getSize(), UNSIGNED);
      intLeft.Decode(leftHMAC.getPtr(), leftHMAC.getSize(), UNSIGNED);

      // If the caller wants to save a non-hardened child's multiplier, save it.
      if(multiplierOut != NULL && !isHardened(childNum))
      {
         multiplierOut->copyFrom(leftHMAC);
      }

      // BIP32 requires the multiplier to be smaller than the curve order. BIP32
      // requests that we try again w/ child#+1. We'll leave that to other code.
      if(intLeft >= ecOrder)
      {
         LOGERR << "HMAC-SHA512 multiplier for child #" << childNum << " is "
            << "larger than the curve order! Try again for child # "
            << (childNum + 1) << ".";
      }
      else
      {
         // Now, let's build the key and chain code. The process depends on if
         // the parent is public or private. (Child will share parents' status.)
         // PRV: Key = (1st 32 bytes of HMAC-SHA512 + Par prv key) % secp256k1 ord
         //      Chain code = 2nd 32 bytes of HMAC-512
         // PUB: Key = (1st 32 bytes of HMAC-SHA512 * secp256k1 base) + par pub key
         //      Chain code = 2nd 32 bytes of HMAC-512
         if(extPar.isPrv())
         {
            derivSuccess = childKeyDerivPrv(const_cast<SecureBinaryData&>(leftHMAC),
                                            extPar.getKey(),
                                            ecOrder_BE,
                                            childKey);
         }
         else
         {
            derivSuccess = childKeyDerivPub(const_cast<SecureBinaryData&>(leftHMAC),
                                            extPar.getPublicKey(false),
                                            ecGenX_BE,
                                            ecGenY_BE,
                                            childKey);
            if(derivSuccess)
            {
               keyIsPub = true;
            }
         }
      }

      if(derivSuccess)
      {
         // Create and return the child object.
         derivKey = ExtendedKey(childKey, rightHMAC, extPar.getFingerprint(),
                                extPar.getIndicesList(), extPar.getVersion(),
                                childNum, keyIsPub);
      }
      else
      {
         LOGERR << "Child #" << childNum << " failed. Try the next child "
            << "number.";
      }
   }

   return derivKey;
}


// A SWIG-friendly function that takes a set of BIP32 multipliers and adds them
// modulo the secp256k1 curve order. The resultant multiplier, w will produce the
// same result as using each multiplier, one at a time, to derive a child key.
//
// INPUT:  A set of 32 byte multipliers to be added modulo curve order. (const
//         vector<BinaryData>&)
// OUTPUT: None
// RETURN: The resultant, equivalent 32 byte multiplier. (BinaryData)
SecureBinaryData HDWalletCrypto::addModMults(
                                        const vector<SecureBinaryData>& mathOps)
{
   CryptoPP::Integer ecOrder;
   ecOrder.Decode(ecOrder_BE.getPtr(), ecOrder_BE.getSize(), UNSIGNED);

   // Add up all the multipliers.
   CryptoPP::Integer totMult((long)0);
   for(uint32_t i = 0; i < mathOps.size(); ++i)
   {
      assert(mathOps[i].getSize() == 32);
      CryptoPP::Integer curMult;
      curMult.Decode(mathOps[i].getPtr(), mathOps[i].getSize(), UNSIGNED);
      totMult += curMult; 
   }
   SecureBinaryData tempMultData(totMult.ByteCount());
   totMult.Encode(tempMultData.getPtr(), tempMultData.getSize(), UNSIGNED);

   // Create and return the final multiplier.
   SecureBinaryData retVal;
   CryptoPP::Integer finalMult(totMult.Modulo(ecOrder));
   SecureBinaryData finalMultData(32);
   finalMult.Encode(finalMultData.getPtr(), finalMultData.getSize(), UNSIGNED);
   if(finalMult != CryptoPP::Integer::Zero())
   {
      retVal = finalMultData;
   }
   else
   {
      // This will never happen in a billion lifetimes, but to be thorough....
      LOGERR << "Derived BIP32 multiplier is zero (invalid)!";
   }
   return retVal;
}


// Same as above but using BinaryData objects which are SWIG friendly
BinaryData HDWalletCrypto::addModMults_SWIG(const vector<BinaryData>& mathOps)
{
   vector<SecureBinaryData> sbdOpsVect;
   for(uint32_t i = 0; i < mathOps.size(); ++i)
   {
      sbdOpsVect.push_back(SecureBinaryData(mathOps[i]));
   }
   
   return addModMults(sbdOpsVect).getRawCopy();
}


// Perform BIP32 key derivation.
//
// INPUT:  The curve's base order multiplier (32 bytes). (const
//         SecureBinaryData&)
//         The parent key (33 or 65 bytes). (const SecureBinaryData&)
//         The curve's generator (X-coordinate). (const SecureBinaryData&)
//         The curve's generator (Y-coordinate). (const SecureBinaryData&)
// OUTPUT: The child key (65 bytes). (SecureBinaryData&)
// RETURN: A bool indicating if derivation was successful. (bool)
bool HDWalletCrypto::childKeyDerivPub(SecureBinaryData const& multiplier,
                                      SecureBinaryData const& parKey,
                                      SecureBinaryData const& ecGenX,
                                      SecureBinaryData const& ecGenY,
                                      SecureBinaryData& childKey)
{
   assert(multiplier.getSize() == 32);
   assert(parKey.getSize() == 65 || parKey.getSize() == 33);
   assert(ecGenX.getSize() == 32);
   assert(ecGenY.getSize() == 32);

   SecureBinaryData parKey65 = CryptoECDSA().UncompressPoint(parKey);

   bool retVal = true;
   childKey.clear();
   SecureBinaryData newPub;
   CryptoPP::Integer multInt;
   multInt.Decode(multiplier.getPtr(), multiplier.getSize(), UNSIGNED);

   // Multiply base point by the multiplier to get an intermediate key. Don't
   // proceed if at the point of infinity. This is extremely unlikely.
   // NB: BIP32 doesn't seem to require using the next child #.
   if(!(CryptoECDSA().ECMultiplyPoint(multiplier, ecGenX, ecGenY, newPub)))
   {
      LOGERR << "Multiplication derived the point at infinity for the public "
         << "key! Try again with a new child number.";
      retVal = false;
   }
   else
   {
      SecureBinaryData pubX = parKey65.getSliceRef(1, 32);
      SecureBinaryData pubY = parKey65.getSliceRef(33, 32);
      SecureBinaryData newX = newPub.getSliceRef(0, 32);
      SecureBinaryData newY = newPub.getSliceRef(32, 32);
      SecureBinaryData addRes;

      // BIP32 requires child key to not be at the point of infinity. BIP32 also
      // requests that we try again w/ child#+1. We'll leave that to other code.
      if(!(CryptoECDSA().ECAddPoints(newX, newY, pubX, pubY, addRes)))
      {
         LOGERR << "Addition derived the point at infinity for the public key! "
            << "Try again with the next child number.";
         retVal = false;
      }
      else
      {
         // We have the child public key!
         uint8_t pubHdr = 0x04;
         childKey.append(pubHdr);
         childKey.append(addRes);
      }
   }

   return retVal;
}


// INPUT:  The curve's base order addend (32 bytes). (const SecureBinaryData&)
//         The parent key (33 bytes). (const SecureBinaryData&)
//         The curve's generator order. (const SecureBinaryData&)
// OUTPUT: The child key (33 bytes). (SecureBinaryData&)
// RETURN: A bool indicating if derivation was successful. (bool)
bool HDWalletCrypto::childKeyDerivPrv(SecureBinaryData const& addend,
                                      SecureBinaryData const& parKey,
                                      SecureBinaryData const& ecGenOrder,
                                      SecureBinaryData& childKey)
{
   assert(addend.getSize() == 32);
   assert(parKey.getSize() == 33);
   assert(ecGenOrder.getSize() == 32);

   bool retVal = true;
   SecureBinaryData prvKey = parKey.getSliceRef(1, 32);
   childKey.clear();
   CryptoPP::Integer addendInt;
   CryptoPP::Integer intKey;
   CryptoPP::Integer ecOrder;
   CryptoPP::Integer check0;
   addendInt.Decode(addend.getPtr(), addend.getSize(), UNSIGNED);
   intKey.Decode(prvKey.getPtr(), prvKey.getSize(), UNSIGNED);
   ecOrder.Decode(ecGenOrder.getPtr(), ecGenOrder.getSize(), UNSIGNED);
   check0 = (intKey + addendInt) % ecOrder;

   // BIP32 requires the child key to not be at the point of infinity. BIP32
   // also requests that we try again w/ child#+1. We'll leave that to other
   // code.
   if(check0.IsZero())
   {
      LOGERR << "Addition derived the point at infinity for the private key! "
         << "Try again with the next child number.";
      retVal = false;
    }
    else
    {
      // We have the child private key!
      SecureBinaryData zero = SecureBinaryData(PRIKEYSIZE - check0.ByteCount());
      zero.fill(0x00);
      childKey.append(zero);
      SecureBinaryData check0Str(check0.ByteCount());
      check0.Encode(check0Str.getPtr(), check0Str.getSize(), UNSIGNED);
      childKey.append(check0Str);
   }

   return retVal;
}


// Function that takes a parent key and some math ops (multipliers or addends)
// and uses the ops to derive a child key. Note that the input and output key
// size must match.
//
// INPUT:  Parent key (33 or 65 bytes). (SecureBinaryData const&)
//         Sequential collection of operators. (vector<SecureBinaryData>)
// OUTPUT: None
// RETURN: The child key (33 or 65 bytes, or 0 bytes if a key couldn't be
//         successfully derived (extremely unlikely). (SecureBinaryData)
SecureBinaryData HDWalletCrypto::getChildKeyFromMult(
                                                 SecureBinaryData const& parKey,
                                             SecureBinaryData const& multiplier)
{
   assert(parKey.getSize() == 33 || parKey.getSize() == 65);

   bool inKeyComp = ((parKey[0] == 0x02 || parKey[0] == 0x03) &&
                     parKey.getSize() == 33) ? true : false;
   SecureBinaryData retKey(0);
   SecureBinaryData nextKey = parKey;
   bool success = true;

   if(parKey[0] == 0x00) // Private parent
   {
      assert(multiplier.getSize() == 32);
      success = childKeyDerivPrv(multiplier,
                                 const_cast<const SecureBinaryData&>(nextKey),
                                 ecOrder_BE,
                                 retKey);
      if(success)
      {
         nextKey = retKey;
      }
      else
      {
         LOGERR << "Multiplier " << multiplier.toHexStr() << " led to a point "
            << "at infinity. The final private key cannot be derived.";
         retKey = SecureBinaryData(0);
      }
   }
   else               // Public parent
   {
      assert(multiplier.getSize() == 32);
      success = childKeyDerivPub(multiplier,
                                 const_cast<const SecureBinaryData&>(nextKey),
                                 ecGenX_BE,
                                 ecGenY_BE,
                                 retKey);
      if(success)
      {
         nextKey = retKey;
      }
      else
      {
         LOGERR << "Multiplier " << multiplier.toHexStr() << " led to a point "
            << "at infinity. The final public key cannot be derived.";
         retKey = SecureBinaryData(0);
      }
   }

   // childKeyDerivPub() returns uncompressed keys. We may need to compress.
   if(inKeyComp && success)
   {
      retKey = CryptoECDSA().CompressPoint(retKey);
   }
   return retKey;
}


// Same as above but using BinaryData objects which are SWIG friendly
BinaryData HDWalletCrypto::getChildKeyFromMult_SWIG(BinaryData parKey,
                                                    BinaryData const& multiplier)
{
   SecureBinaryData sbdParKey(parKey);
   SecureBinaryData sbdMathOps(multiplier);
   return getChildKeyFromMult(sbdParKey, sbdMathOps).getRawCopy();
}


// Function that takes an incoming SecureBinaryData buffer and creates a master
// ExtendedKey object. BIP32 requires the seed to be 16-64 bytes long, with 32
// recommended.
ExtendedKey HDWalletCrypto::convertSeedToMasterKey(
                                                  SecureBinaryData const & seed)
{
   assert(seed.getSize() >= 16 && seed.getSize() <= 64);

   HDWalletCryptoSeed newSeed(seed);
   SecureBinaryData newMasterPriv = SecureBinaryData().CreateFromHex("00");
   SecureBinaryData master32 = newSeed.getMasterKey().copy();
   newMasterPriv.append(master32);
   ExtendedKey masterKey(newMasterPriv, newSeed.getMasterChain());
   return masterKey;
}


// HDWalletCrypto destructor. Does nothing for now.
HDWalletCrypto::~HDWalletCrypto() {}
