////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright(C) 2011-2013, Armory Technologies, Inc.                         //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include "EncryptionUtils.h"
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

// Function that takes an incoming child number and determines if the BIP32
// child key will use private or public key derivation.
inline bool usePrvDer(uint32_t inChildNumber) {
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

SecureBinaryData & SecureBinaryData::append(uint8_t byte)
{
   BinaryData::append(byte);
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
SecureBinaryData SecureBinaryData::GenerateRandom(uint32_t numBytes)
{
   static BTC_PRNG prng;
   SecureBinaryData randData(numBytes);
   prng.GenerateBlock(randData.getPtr(), numBytes);
   return randData;  
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
   static CryptoPP::SHA512 sha512;

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
/////////////////////////////////////////////////////////////////////////////
BTC_PRIVKEY CryptoECDSA::CreateNewPrivateKey()
{
   return ParsePrivateKey(SecureBinaryData().GenerateRandom(32));
}


// Create a new ECDSA private key based off 32 bytes of PRNG-generated data.
////////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::GenerateNewPrivateKey()
{
   return SecureBinaryData().GenerateRandom(32);
}


// Create a new Crypto++ ECDSA private key using an incoming private key. The
// incoming key must be 32 bytes long.
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
   static BTC_PRNG prng;
   assert(cppPubKey.Validate(prng, 3));

   return cppPubKey;
}

// Serialize a Crypto+ ECDSA private key. The result will be 32 bytes long.
/////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::SerializePrivateKey(BTC_PRIVKEY const & privKey)
{
   CryptoPP::Integer privateExp = privKey.GetPrivateExponent();
   SecureBinaryData privKeyData(32);
   privateExp.Encode(privKeyData.getPtr(), privKeyData.getSize(), UNSIGNED);
   return privKeyData;
}
   
// Serialize a Crypto+ ECDSA private key. The result will be 65 bytes long.
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
   static BTC_PRNG prng;
   assert(cppPubKey.Validate(prng, 3));

   return cppPubKey;
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
                                       SecureBinaryData const & pubKey65)
{
   assert(privKey32.getSize() == 32);
   assert(pubKey65.getSize() == 65);
   
   if(CRYPTO_DEBUG)
   {
      cout << "CheckPubPrivKeyMatch:" << endl;
      cout << "   BinPrv: " << privKey32.toHexStr() << endl;
      cout << "   BinPub: " << pubKey65.toHexStr() << endl;
   }

   BTC_PRIVKEY privKey = ParsePrivateKey(privKey32);
   BTC_PUBKEY  pubKey  = ParsePublicKey(pubKey65);
   return CheckPubPrivKeyMatch(privKey, pubKey);
}


// Verify that an incoming public key is on the secp256k1 curve.
// INPUT:  A 65-byte public key to check. (const SecureBinaryData&)
// OUTPUT: None
// RETURN: Bool indicating if the key's on the curve (true) or not (false).
bool CryptoECDSA::VerifyPublicKeyValid(SecureBinaryData const & pubKey65)
{
   assert(pubKey65.getSize() == 65);

   if(CRYPTO_DEBUG)
   {
      cout << "BinPub: " << pubKey65.toHexStr() << endl;
   }

   // Basically just copying the ParsePublicKey method, but without
   // the assert that would throw an error from C++
   SecureBinaryData pubXbin(pubKey65.getSliceRef( 1,32));
   SecureBinaryData pubYbin(pubKey65.getSliceRef(33,32));
   CryptoPP::Integer pubX;
   CryptoPP::Integer pubY;
   pubX.Decode(pubXbin.getPtr(), pubXbin.getSize(), UNSIGNED);
   pubY.Decode(pubYbin.getPtr(), pubYbin.getSize(), UNSIGNED);
   BTC_ECPOINT publicPoint(pubX, pubY);

   // Initialize the public key with the ECP point just created
   BTC_PUBKEY cppPubKey;
   cppPubKey.Initialize(CryptoPP::ASN1::secp256k1(), publicPoint);

   // Validate the public key -- not sure why this needs a PRNG
   static BTC_PRNG prng;
   return cppPubKey.Validate(prng, 3);
}


// Function that takes a 32-byte private key and signs an incoming buffer.
// INPUT:  The incoming buffer.
//         The 32-byte private key used to sign the data.
// OUTPUT: None
// RETURN: A buffer with the signature.
/////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::SignData(SecureBinaryData const & binToSign, 
                                       SecureBinaryData const & binPrivKey)
{
   assert(binPrivKey.getSize() == 32);

   if(CRYPTO_DEBUG)
   {
      cout << "SignData:" << endl;
      cout << "   BinSgn: " << binToSign.getSize() << " " << binToSign.toHexStr() << endl;
      cout << "   BinPrv: " << binPrivKey.getSize() << " " << binPrivKey.toHexStr() << endl;
   }
   BTC_PRIVKEY cppPrivKey = ParsePrivateKey(binPrivKey);
   return SignData(binToSign, cppPrivKey);
}


// Function that takes a Crypto++ private key and signs an incoming buffer.
// INPUT:  The incoming buffer.
//         The Crypto++ private key used to sign the data.
// OUTPUT: None
// RETURN: A buffer with the signature.
/////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::SignData(SecureBinaryData const & binToSign, 
                                       BTC_PRIVKEY const & cppPrivKey)
{

   // We trick the Crypto++ ECDSA module by passing it a single-hashed
   // message, it will do the second hash before it signs it.  This is 
   // exactly what we need.
   static CryptoPP::SHA256  sha256;
   static BTC_PRNG prng;

   // Execute the first sha256 op -- the signer will do the other one
   SecureBinaryData hashVal(32);
   sha256.CalculateDigest(hashVal.getPtr(), 
                          binToSign.getPtr(), 
                          binToSign.getSize());

   string signature;
   BTC_SIGNER signer(cppPrivKey);
   CryptoPP::StringSource(
               hashVal.toBinStr(), true, new CryptoPP::SignerFilter(
               prng, signer, new CryptoPP::StringSink(signature))); 
  
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
   static CryptoPP::SHA256  sha256;
   static BTC_PRNG prng;

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

// THIS FUNCTION IS UNTESTED AND MAY NOT BE ACCURATE.
/////////////////////////////////////////////////////////////////////////////
// Deterministically generate new private key using a chaincode
// Changed:  added using the hash of the public key to the mix
//           b/c multiplying by the chaincode alone is too "linear"
//           (there's no reason to believe it's insecure, but it doesn't
//           hurt to add some extra entropy/non-linearity to the chain
//           generation process)
/*SecureBinaryData CryptoECDSA::ComputeChainedPrivateKey(
                                            SecureBinaryData const & binPrivKey,
                                            SecureBinaryData const & chainCode,
                                            SecureBinaryData binPubKey)
{
   if(CRYPTO_DEBUG)
   {
      cout << "ComputeChainedPrivateKey:" << endl;
      cout << "   BinPrv: " << binPrivKey.toHexStr() << endl;
      cout << "   BinChn: " << chainCode.toHexStr() << endl;
      cout << "   BinPub: " << binPubKey.toHexStr() << endl;
   }

   if( binPubKey.getSize()==0 )
      binPubKey = ComputePublicKey(binPrivKey);

   if( binPrivKey.getSize() != 32 || chainCode.getSize() != 32)
   {
      cerr << "***ERROR:  Invalid private key or chaincode (both must be 32B)";
      cerr << endl;
      cerr << "BinPrivKey: " << binPrivKey.getSize() << endl;
      cerr << "BinPrivKey: " << binPrivKey.toHexStr() << endl;
      cerr << "BinChain  : " << chainCode.getSize() << endl;
      cerr << "BinChain  : " << chainCode.toHexStr() << endl;
   }

   // Adding extra entropy to chaincode by xor'ing with hash256 of pubkey
   BinaryData chainMod  = binPubKey.getHash256();
   BinaryData chainOrig = chainCode.getRawCopy();
   BinaryData chainXor(32);
      
   for(uint8_t i=0; i<8; ++i)
   {
      uint8_t offset = 4*i;
      *(uint32_t*)(chainXor.getPtr()+offset) =
                           *(uint32_t*)( chainMod.getPtr()+offset) ^ 
                           *(uint32_t*)(chainOrig.getPtr()+offset);
   }

   // Hard-code the order of the group
   static SecureBinaryData SECP256K1_ORDER_BE = SecureBinaryData().CreateFromHex(
           SECP256K1_ORDER_HEX);
   
   CryptoPP::Integer chaincode, origPrivExp, ecOrder;
   // A 
   chaincode.Decode(chainXor.getPtr(), chainXor.getSize(), UNSIGNED);
   // B 
   origPrivExp.Decode(binPrivKey.getPtr(), binPrivKey.getSize(), UNSIGNED);
   // C
   ecOrder.Decode(SECP256K1_ORDER_BE.getPtr(), SECP256K1_ORDER_BE.getSize(), UNSIGNED);

   // A*B mod C will get us a new private key exponent
   CryptoPP::Integer newPrivExponent = 
                  a_times_b_mod_c(chaincode, origPrivExp, ecOrder);

   // Convert new private exponent to big-endian binary string 
   SecureBinaryData newPrivData(32);
   newPrivExponent.Encode(newPrivData.getPtr(), newPrivData.getSize(), UNSIGNED);
   return newPrivData;
}*/
                            
// THIS FUNCTION IS UNTESTED AND MAY NOT BE ACCURATE.
/////////////////////////////////////////////////////////////////////////////
// Deterministically generate new public key using a chaincode
/*SecureBinaryData CryptoECDSA::ComputeChainedPublicKey(
                                SecureBinaryData const & binPubKey,
                                SecureBinaryData const & chainCode)
{
   if(CRYPTO_DEBUG)
   {
      cout << "ComputeChainedPUBLICKey:" << endl;
      cout << "   BinPub: " << binPubKey.toHexStr() << endl;
      cout << "   BinChn: " << chainCode.toHexStr() << endl;
   }
   static SecureBinaryData SECP256K1_ORDER_BE = SecureBinaryData::CreateFromHex(
           SECP256K1_ORDER_HEX);

   // Added extra entropy to chaincode by xor'ing with hash256 of pubkey
   BinaryData chainMod  = binPubKey.getHash256();
   BinaryData chainOrig = chainCode.getRawCopy();
   BinaryData chainXor(32);
      
   for(uint8_t i=0; i<8; ++i)
   {
      uint8_t offset = 4*i;
      *(uint32_t*)(chainXor.getPtr()+offset) =
                           *(uint32_t*)( chainMod.getPtr()+offset) ^ 
                           *(uint32_t*)(chainOrig.getPtr()+offset);
   }

   // Parse the chaincode as a big-endian integer
   CryptoPP::Integer chaincode;
   chaincode.Decode(chainXor.getPtr(), chainXor.getSize(), UNSIGNED);

   // "new" init as "old", to make sure it's initialized on the correct curve
   BTC_PUBKEY oldPubKey = ParsePublicKey(binPubKey); 
   BTC_PUBKEY newPubKey = ParsePublicKey(binPubKey);

   // Let Crypto++ do the EC math for us, serialize the new public key
   newPubKey.SetPublicElement( oldPubKey.ExponentiatePublicElement(chaincode) );
   return CryptoECDSA::SerializePublicKey(newPubKey);
}*/


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
   static BTC_PRNG prng;
   return cppPubKey.Validate(prng, 3);
}


// Function that returns the Crypto++ ECP object for the secp256k1 surve
////////////////////////////////////////////////////////////////////////////////
CryptoPP::ECP& CryptoECDSA::Get_secp256k1_ECP()
{
   static bool firstRun = true;
   static CryptoPP::ECP theECP;
   if(firstRun) 
   {
      BinaryData N = BinaryData::CreateFromHex(
            "fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f");
      BinaryData a = BinaryData::CreateFromHex(
            "0000000000000000000000000000000000000000000000000000000000000000");
      BinaryData b = BinaryData::CreateFromHex(
            "0000000000000000000000000000000000000000000000000000000000000007");

      CryptoPP::Integer intN, inta, intb;

      intN.Decode( N.getPtr(),  N.getSize(),  UNSIGNED);
      inta.Decode( a.getPtr(),  a.getSize(),  UNSIGNED);
      intb.Decode( b.getPtr(),  b.getSize(),  UNSIGNED);
  
      theECP = CryptoPP::ECP(intN, inta, intb);
   }
   return theECP;
}


// Function multiplying two scalars on the secp256k1 curve and returning the
// result.
////////////////////////////////////////////////////////////////////////////////
BinaryData CryptoECDSA::ECMultiplyScalars(BinaryData const & A, 
                                          BinaryData const & B)
{
   // Hardcode the order of the secp256k1 EC group
   static BinaryData curveOrd = BinaryData::CreateFromHex(
             "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141");

   CryptoPP::Integer intA, intB, intC, intCurveOrd;
   intA.Decode(A.getPtr(), A.getSize(), UNSIGNED);
   intB.Decode(B.getPtr(), B.getSize(), UNSIGNED);
   intCurveOrd.Decode(curveOrd.getPtr(), curveOrd.getSize(), UNSIGNED);
   intC = a_times_b_mod_c(intA, intB, intCurveOrd);

   BinaryData C(32);
   intC.Encode(C.getPtr(), 32, UNSIGNED);
   return C;
}


// Function that multiplies an incoming scalar by the secp256k1 generator and
// adds the result to incoming point (X/Y coordinates).
// INPUT:  Scalar (A) and X/Y coordinates for a point (Bx & By).
// OUTPUT: The multiply result. If the result is at infinity, this is set to 0.
// RETURN: True if a valid result, false if at infinity (incredibly unlikely)
////////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::ECMultiplyPoint(BinaryData const & A, 
                                  BinaryData const & Bx,
                                  BinaryData const & By,
                                  BinaryData& multResult)
{
   CryptoPP::ECP ecp = Get_secp256k1_ECP();
   CryptoPP::Integer intA, intBx, intBy, intCx, intCy, intCurveOrder;
   bool validResult = true;

   // We can't proceed if we're at infinity, even if the likelihood is LOW!!!
   // From X9.62 D.3.2?
   intA.Decode( A.getPtr(),  A.getSize(),  UNSIGNED);
   BinaryData curveOrder = BinaryData::CreateFromHex(
            "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141");
   intCurveOrder.Decode(curveOrder.getPtr(), curveOrder.getSize(), UNSIGNED);
   BinaryData Cbd(64);
   if(intA % intCurveOrder == 0) {
      multResult.clear();
      multResult.append(0x00);
      validResult = false;
   }
   else {
      multResult.clear();
      multResult = BinaryData(64);
      intBx.Decode(Bx.getPtr(), Bx.getSize(), UNSIGNED);
      intBy.Decode(By.getPtr(), By.getSize(), UNSIGNED);

      BTC_ECPOINT B(intBx, intBy);
      BTC_ECPOINT C = ecp.ScalarMultiply(B, intA);

      C.x.Encode(multResult.getPtr(),    32, UNSIGNED);
      C.y.Encode(multResult.getPtr()+32, 32, UNSIGNED);
   }

   return validResult;
}


// Function that adds two points (X/Y coordinates) together, modulo the
// secp256k1 finite field (Fp).
// INPUT:  X & Y coordinates for points A & B.
// OUTPUT: The addition result. If the result is at infinity, this is set to 0.
// RETURN: True if a valid result, false if at infinity (incredibly unlikely)
////////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::ECAddPoints(BinaryData const & Ax, 
                              BinaryData const & Ay,
                              BinaryData const & Bx,
                              BinaryData const & By,
                              BinaryData& addResult)
{
   CryptoPP::ECP ecp = Get_secp256k1_ECP();
   CryptoPP::Integer intAx, intAy, intBx, intBy, intCx, intCy, intFP;
   bool validResult = true;

   intAx.Decode(Ax.getPtr(), Ax.getSize(), UNSIGNED);
   intAy.Decode(Ay.getPtr(), Ay.getSize(), UNSIGNED);
   intBx.Decode(Bx.getPtr(), Bx.getSize(), UNSIGNED);
   intBy.Decode(By.getPtr(), By.getSize(), UNSIGNED);
   BinaryData fp = BinaryData::CreateFromHex(
            "fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f");
   intFP.Decode(fp.getPtr(), fp.getSize(), UNSIGNED);

   // Let's make sure we're not at infinity. This should be from X9.62 B.3.
   if((intAx == intBx) && ((intAy + intBy) % intFP == 0)) {
      addResult.clear();
      addResult.append(0x00);
      validResult = false;
   }
   else {
      BTC_ECPOINT A(intAx, intAy);
      BTC_ECPOINT B(intBx, intBy);

      BTC_ECPOINT C = ecp.Add(A,B);

      BinaryData Cbd(64);
      C.x.Encode(Cbd.getPtr(),    32, UNSIGNED);
      C.y.Encode(Cbd.getPtr()+32, 32, UNSIGNED);
      addResult = Cbd;
   }

   return validResult;
}

// Function that takes an incoming point (X/Y coords) on the secp256k1 curve and
// returns the inverse. (The inverse is the original X coordinate and the
// inverted Y coordinate (i.e., the bits are flipped).
////////////////////////////////////////////////////////////////////////////////
BinaryData CryptoECDSA::ECInverse(BinaryData const & Ax, 
                                  BinaryData const & Ay)
                                  
{
   CryptoPP::ECP & ecp = Get_secp256k1_ECP();
   CryptoPP::Integer intAx, intAy, intCx, intCy;

   intAx.Decode(Ax.getPtr(), Ax.getSize(), UNSIGNED);
   intAy.Decode(Ay.getPtr(), Ay.getSize(), UNSIGNED);

   BTC_ECPOINT A(intAx, intAy);
   BTC_ECPOINT C = ecp.Inverse(A);

   BinaryData Cbd(64);
   C.x.Encode(Cbd.getPtr(),    32, UNSIGNED);
   C.y.Encode(Cbd.getPtr()+32, 32, UNSIGNED);

   return Cbd;
}


// Function that takes an incoming 65 byte public key and returns a 33 byte
// compressed version.
////////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::CompressPoint(SecureBinaryData const & pubKey65)
{
   assert(pubKey65.getSize() == 65);

   CryptoPP::ECP & ecp = Get_secp256k1_ECP();
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
   assert(pubKey33.getSize() == 33);

   CryptoPP::ECP & ecp = Get_secp256k1_ECP();
   BTC_ECPOINT ptPub;
   ecp.DecodePoint(ptPub, (byte*)pubKey33.getPtr(), 33);
   SecureBinaryData ptUncompressed(65);
   ecp.EncodePoint((byte*)ptUncompressed.getPtr(), ptPub, false);
   return ptUncompressed; 

}

const bool ExtendedKey::isPub() const {
   return (key_[0] == 0x02 || key_[0] == 0x03);
}

// Check to see if our primary key is private.
const bool ExtendedKey::isPrv() const {
   return (key_[0] == 0x00);
}


// Function that returns the 4-byte fingerprint of the ExtendedKey. This is the
// first 4 bytes of the Hash160 of the compressed public key.
const SecureBinaryData ExtendedKey::getFingerprint() const {
   SecureBinaryData compressedPubKey = CryptoECDSA().CompressPoint(pubKey_);
   SecureBinaryData myHash = compressedPubKey.getHash160();
   return myHash.getSliceRef(0, 4);
}


// Function that returns the 20-byte identifier of the ExtendedKey. This is the
// Hash160 of the compressed public key.
const SecureBinaryData ExtendedKey::getIdentifier() const {
   SecureBinaryData compressedPubKey = CryptoECDSA().CompressPoint(pubKey_);
   return compressedPubKey.getHash160();
}


// Function that performs a Hash160 (SHA256, then RIPEMD160) on the uncompressed
// public key.
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
   if(indicesList_.size() != 0) {
      list<uint32_t>::const_iterator iter = indicesList_.end();
      --iter;
      retVal = *iter;
   }

   return retVal;
}

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
   chainCode_ = ch;
   updatePubKey();
   version = PRVVER;
   parentFP = SecureBinaryData::CreateFromHex("00000000");
   validKey = true;
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
   chainCode_(ch),
   version(netVer),
   indicesList_(parentTreeIdx)
{
   assert(key.getSize() == 33 || key.getSize() == 65);
   assert(ch.getSize() == 32);
   assert(parFP.getSize() == 4);

   parentFP = parFP.getSliceRef(0, 4);
   indicesList_.push_back(inChildNum);
   //
   if(keyIsPub) {
      key_ = CryptoECDSA().CompressPoint(key);
      pubKey_ = key;
   }
   else {
      key_ = key;
      BTC_PRIVKEY tmpA = CryptoECDSA().ParsePrivateKey(key_.getSliceRef(1, 32));
      BTC_PUBKEY tmpB = CryptoECDSA().ComputePublicKey(tmpA);
      pubKey_ = CryptoECDSA().SerializePublicKey(tmpB);
   }

   validKey = true;
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
   chainCode_(ch),
   indicesList_(parentTreeIdx),
   parentFP(parFP),
   version(inVer)
{
   assert(key_.getSize() == 0 || key_.getSize() == 33);
   assert(pubKey_.getSize() == 65);
   assert(chainCode_.getSize() == 32);
   parentFP = parFP.getSliceRef(0, 4);
   indicesList_.push_back(inChildNum);
   validKey = true;
}


// Delete the private key and replace it with the public key.
////////////////////////////////////////////////////////////////////////////////
void ExtendedKey::deletePrivateKey()
{
   if(key_[0] == 0x00) {
      key_.destroy();
     key_ = CryptoECDSA().CompressPoint(pubKey_);
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
   return ExtendedKey(key_, pubKey_, chainCode_, parentFP, indicesList_,
                      version, getChildNum());
}


////////////////////////////////////////////////////////////////////////////////
void ExtendedKey::debugPrint()
{
   cout << "Indices:              " << getIndexListString() << endl;
   cout << "Fingerprint (Self):   " << getFingerprint().toHexStr() << endl;
   cout << "Fingerprint (Parent): " << getParentFP().toHexStr() << endl;
   cout << "Private Key:          " << key_.toHexStr() << endl;
   cout << "Public Key Comp:      " << CryptoECDSA().CompressPoint(pubKey_).toHexStr() << endl;
   cout << "Public Key:           " << pubKey_.toHexStr() << endl;
   cout << "Chain Code:           " << chainCode_.toHexStr() << endl;
   cout << "Hash160:              " << getHash160().toHexStr() << endl << endl;
}


////////////////////////////////////////////////////////////////////////////////
const string ExtendedKey::getIndexListString(const string prefix)
{
   stringstream ss;
   ss << prefix;
   vector<uint32_t> indexList = getIndicesVect();

   // Loops through index list. If empty, key is a master key or is invalid.
   for(uint32_t i=0; i<indexList.size(); ++i) {
      ss << "/";
      if(usePrvDer(indexList[i])) {
         ss << "Prv(";
      }
      else {
         ss << "Pub(";
      }
      ss << indexList[i] << ")";
   }
   return ss.str();
}


// Get a compressed copy (33 bytes) of the public key.
////////////////////////////////////////////////////////////////////////////////
SecureBinaryData ExtendedKey::getPubCompressed() const
{
   return CryptoECDSA().CompressPoint(pubKey_);
}

// Function that updates the public key based on the primary key. (FINISH!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!)
void ExtendedKey::updatePubKey() {
   // If primary key is private, derive the uncompressed private key. If public,
   // just save an uncompressed copy.
   if(isPrv()) {
      SecureBinaryData inPrvKey = key_.getSliceRef(1, 32);
      pubKey_ = CryptoECDSA().ComputePublicKey(inPrvKey);
   }
   else {
      pubKey_ = CryptoECDSA().UncompressPoint(pubKey_);
   }
}


// Function that returns the 78 byte, serialized, big/net endian extended key.
// If the ExtendedKey isn't valid yet, return an empty 78 byte buffer.
// Format is version/depth/parentFP/childNum/chainCode/key.
const SecureBinaryData ExtendedKey::getExtKeySer() {
   SecureBinaryData outKey;
   if(!validKey) {
      outKey.append(0x00);
   }
   else {
      SecureBinaryData tmpVal = WRITE_UINT32_BE(version);
      outKey.append(tmpVal);
      tmpVal = WRITE_UINT8_BE(getDepth());
      outKey.append(tmpVal);
      outKey.append(parentFP);
      tmpVal = WRITE_UINT32_BE(getChildNum());
      outKey.append(tmpVal);
      outKey.append(chainCode_);
      outKey.append(key_);
   }

   return outKey;
}


// Function indicating if an ExtendedKey is a master key.
const bool ExtendedKey::isMaster() const {
   return (indicesList_.size() == 0 && validKey);
}


// Overloaded constructor that should be used instead of the default
// constructor. Takes incoming (P)RNG data and creates an HD master key and
// chain code.
// INPUT:  (P)RNG data seeding the HD crypto wallet. Can be any length but 32
//         bytes is recommended.
// OUTPUT: None
// RETURN: None
HDWalletCryptoSeed::HDWalletCryptoSeed(const SecureBinaryData& rngData) {
   SecureBinaryData hmacKey = SecureBinaryData::CreateFromHex("426974636f696e2073656564");
   SecureBinaryData hVal = HDWalletCrypto().HMAC_SHA512(hmacKey, rngData);
   SecureBinaryData hValLeft = hVal.getSliceRef(0, 32);
   masterKey.append(0x00);
   masterKey.append(hValLeft);
   masterChainCode = hVal.getSliceRef(32, 32);
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

   if(key.getSize() > BLOCKSIZE) { // Reduce large keys via hash function.
      key = BtcUtils::getHash512(key);
   }
   else if(key.getSize() < BLOCKSIZE) { // Zero-pad smaller keys
      SecureBinaryData zeros = SecureBinaryData(BLOCKSIZE - key.getSize());
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


////////////////////////////////////////////////////////////////////////////////
// In the HDWallet gist by Pieter, CKD takes two inputs:
//    1.  Extended Key  (priv/pub key, chaincode)
//    2.  Child number
//
// The ExtendedKey class accommodates full private-included ExtendedKey objects
// or public-key-only.  You can pass in either one here, and it will derive the
// child for whatever key data is there.
//
ExtendedKey HDWalletCrypto::childKeyDeriv(ExtendedKey const & extPar,
                                          uint32_t childNum)
{
   // Can't compute a child with no parent!
   assert(extPar.isInitialized());

   ExtendedKey derivKey;
   if(extPar.isPub() && usePrvDer(childNum)) {
      //ERROR/////////////////////////////////////////////!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   }
   else {
      // First, let's get ready for an HMAC-SHA512 call. The key will always be
      // the parent's chain code. The data will depend on the parent key type
      // and the type of derivation. (| = Concatenation)
      // Prv par/Prv der - 0x00 | Prv par key | Incoming position
      // Prv par/Pub der - Compressed pub par key | Incoming position
      // Pub par/Prv der - NOT VALID  (Already handled above)
      // Pub par/Pub der - Compressed pub par key | Incoming position
      SecureBinaryData binaryN = WRITE_UINT32_BE(childNum);
      SecureBinaryData hashData;

      if(usePrvDer(childNum)) {
         SecureBinaryData pKey = extPar.getKey();
         hashData.append(pKey);
      }
      else {
         SecureBinaryData cp = CryptoECDSA().CompressPoint(extPar.getPub());
         hashData.append(cp);
      }
      hashData.append(binaryN);

      // Hash that sucker and slice up the result!
      SecureBinaryData hVal = HMAC_SHA512(extPar.getChainCode(), hashData);
      SecureBinaryData leftHMAC = hVal.getSliceRef(0, 32);
      SecureBinaryData rightHMAC = hVal.getSliceRef(32, 32);

      // Is our new key valid? (Almost impossible to fail, but just in case....)
      CryptoPP::Integer intLeft;
      CryptoPP::Integer ecOrder;
      SecureBinaryData CURVE_ORDER_BE = SecureBinaryData().CreateFromHex(
            "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141");
      ecOrder.Decode(CURVE_ORDER_BE.getPtr(), CURVE_ORDER_BE.getSize(),
                     UNSIGNED);
      intLeft.Decode(leftHMAC.getPtr(), leftHMAC.getSize(), UNSIGNED);
      if(intLeft >= ecOrder) {
         // ERROR!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
      }

      // Now, let's build the key and chain code. The process depends on if the
      // parent is public or private. (Child will share the parents' status.)
      // PRV: Key = (1st 32 bytes of HMAC-SHA512 + Par prv key) % secp256k1 ord
      //      Chain code = 2nd 32 bytes of HMAC-512
      // PUB: Key = (1st 32 bytes of HMAC-SHA512 * secp256k1 gen) + par pub key
      //      Chain code = 2nd 32 bytes of HMAC-512
      SecureBinaryData childKey;
      bool keyIsPub = false;
      if(extPar.isPrv()) {
         CryptoPP::Integer intKey;
         CryptoPP::Integer check0;
         SecureBinaryData prvKey = extPar.getKey().getSliceRef(1, 32);
         intKey.Decode(prvKey.getPtr(), prvKey.getSize(), UNSIGNED);
         check0 = (intLeft + intKey) % ecOrder;
   
         // Highly doubtful the key hit the point of infinity. Just in case....
         if(check0.IsZero()) {
            // ERROR!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! AT INFINITY!!!!!!!!!!!!!
         }
         else {
            // Finish child setup.
            SecureBinaryData zeros = SecureBinaryData(PRIKEYSIZE - check0.ByteCount());
            zeros.fill(0x00);
            childKey.append(zeros);
            SecureBinaryData check0Str(check0.ByteCount());
            check0.Encode(check0Str.getPtr(), check0Str.getSize(), UNSIGNED);
            childKey.append(check0Str);
         }
      }
      else {
         SecureBinaryData pubX = extPar.getPub().getSliceRef(1, 32);
         SecureBinaryData pubY = extPar.getPub().getSliceRef(33, 32);
         SecureBinaryData newPub;

         // Calc the child key. Don't proceed if at the point of infinity.
         if(!(CryptoECDSA().ECMultiplyPoint(leftHMAC, pubX, pubY, newPub))) {
            // ERROR!!!!!!!!! AT INFINITY!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
         }
         else {
            // Finish child setup.
            CryptoPP::Integer newX;
            CryptoPP::Integer newY;
            newX.Decode(newPub.getPtr(), 32, UNSIGNED);
            newY.Decode(newPub.getPtr() + 32, 32, UNSIGNED);
            uint8_t pubHdr = 0x04;
            childKey.append(pubHdr);
            childKey.append(newPub);
            keyIsPub = true;
         }
      }

      // Create and return the child.
      derivKey = ExtendedKey(childKey, rightHMAC, extPar.getFingerprint(),
                             extPar.getIndicesList(), extPar.getVersion(),
                             childNum, keyIsPub);
   }
   return derivKey;
}


// Function that takes an incoming HDWalletCryptoSeed buffer and creates a
// master ExtendedKey object.
ExtendedKey HDWalletCrypto::ConvertSeedToMasterKey(SecureBinaryData const & seed)
{
   HDWalletCryptoSeed newSeed(seed);
   ExtendedKey masterKey(newSeed.getMasterKey(), newSeed.getMasterChainCode());
   return masterKey;
}


// HDWalletCrypto destructor. Does nothing for now.
HDWalletCrypto::~HDWalletCrypto() {}






   /* OpenSSL code (untested)
   static SecureBinaryData sigSpace(1000);
   static uint32_t sigSize = 0;

   // Create the key object
   EC_KEY* pubKey = EC_KEY_new_by_curve_name(NID_secp256k1);

   uint8_t* pbegin = privKey.getPtr();
   d2i_ECPrivateKey(&pubKey, &pbegin, privKey.getSize());

   ECDSA_sign(0, binToSign.getPtr(), 
                 binToSign.getSize(), 
                 sigSpace.getPtr(), 
                 &sigSize, 
                 pubKey)

   EC_KEY_free(pubKey);
   return SecureBinaryData(sigSpace.getPtr(), sigSize);
   */
