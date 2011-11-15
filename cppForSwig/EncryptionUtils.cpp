#include "EncryptionUtils.h"
#include "integer.h"
#include "oids.h"

//#include <openssl/ec.h>
//#include <openssl/ecdsa.h>
//#include <openssl/obj_mac.h>



/////////////////////////////////////////////////////////////////////////////
// We have to explicitly re-define some of these methods...
SecureBinaryData & SecureBinaryData::append(SecureBinaryData & sbd2) 
{
   BinaryData::append(sbd2.getRawRef());
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

SecureBinaryData SecureBinaryData::GenerateRandom(uint32_t numBytes)
{
   static CryptoPP::AutoSeededRandomPool prng;
   SecureBinaryData randData(numBytes);
   prng.GenerateBlock(randData.getPtr(), numBytes);
   return randData;  
}

/////////////////////////////////////////////////////////////////////////////
KdfRomix::KdfRomix(void) : 
   hashFunctionName_( "sha512" ),
   hashOutputBytes_( 64 ),
   kdfOutputBytes_( 32 )
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
   salt_ = SecureBinaryData::GenerateRandom(32);

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
      for(uint32_t i=0; i<numTest; i++)
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
   cout << "System speed test results    : " << endl;
   cout << "   Total test of the KDF took:  " << allItersSec*1000 << " ms" << endl;
   cout << "                   to execute:  " << numTest << " iterations" << endl;
   cout << "   Target computation time is:  " << targetComputeSec*1000 << " ms" << endl;
   cout << "   Setting numIterations to:    " << numIterations_ << endl;
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
void KdfRomix::printKdfParams(void)
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
   lookupTable_.destroy();
   return X.getSliceCopy(0,kdfOutputBytes_);
}

/////////////////////////////////////////////////////////////////////////////
SecureBinaryData KdfRomix::DeriveKey(SecureBinaryData const & password)
{
   SecureBinaryData masterKey(password);
   for(uint32_t i=0; i<numIterations_; i++)
      masterKey = DeriveKey_OneIter(masterKey);
   
   return SecureBinaryData(masterKey);
}





/////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoAES::Encrypt(SecureBinaryData & data, 
                                    SecureBinaryData & key,
                                    SecureBinaryData & iv)
{
   if(data.getSize() == 0)
      return SecureBinaryData(0);

   SecureBinaryData encrData(data.getSize());
   cout << "   StartPlain: " << data.toHexStr() << endl;
   cout << "   Key Data  : " << key.toHexStr() << endl;

   // Caller can supply their own IV/entropy, or let it be generated here
   if(iv.getSize() == 0)
      iv = SecureBinaryData::GenerateRandom(BTC_AES::BLOCKSIZE);

   cout << "   IV Data   : " << iv.toHexStr() << endl;

   BTC_AES_MODE<BTC_AES>::Encryption aes_enc( (byte*)key.getPtr(), 
                                                     key.getSize(), 
                                              (byte*)iv.getPtr());

   aes_enc.ProcessData( (byte*)encrData.getPtr(), 
                        (byte*)data.getPtr(), 
                               data.getSize());

   cout << "   Ciphertext: " << encrData.toHexStr() << endl;
   return encrData;
}

/////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoAES::Decrypt(SecureBinaryData & data, 
                                    SecureBinaryData & key,
                                    SecureBinaryData   iv  )
{
   if(data.getSize() == 0)
      return SecureBinaryData(0);

   SecureBinaryData unencrData(data.getSize());

   cout << "   StrtCipher: " << data.toHexStr() << endl;
   cout << "   Key Data  : " << key.toHexStr() << endl;
   cout << "   IV Data   : " << iv.toHexStr() << endl;

   BTC_AES_MODE<BTC_AES>::Decryption aes_enc( (byte*)key.getPtr(), 
                                                     key.getSize(), 
                                              (byte*)iv.getPtr());

   aes_enc.ProcessData( (byte*)unencrData.getPtr(), 
                        (byte*)data.getPtr(), 
                               data.getSize());

   cout << "   Plaintext : " << unencrData.toHexStr() << endl;
   return unencrData;
}







/////////////////////////////////////////////////////////////////////////////
BTC_PRIVKEY CryptoECDSA::ParsePrivateKey(SecureBinaryData const & privKeyData)
{
   BTC_PRIVKEY cppPrivKey;

   CryptoPP::Integer privateExp;
   privateExp.Decode(privKeyData.getPtr(), privKeyData.getSize());
   cppPrivKey.Initialize(CryptoPP::ASN1::secp256k1(), privateExp);
   return cppPrivKey;
}

/////////////////////////////////////////////////////////////////////////////
BTC_PUBKEY CryptoECDSA::ParsePublicKey(SecureBinaryData const & pubKeyXData,
                                       SecureBinaryData const & pubKeyYData)
{
   BTC_PUBKEY cppPubKey;

   CryptoPP::Integer pubX;
   CryptoPP::Integer pubY;
   pubX.Decode(pubKeyXData.getPtr(), pubKeyXData.getSize());
   pubY.Decode(pubKeyYData.getPtr(), pubKeyYData.getSize());
   BTC_ECPOINT publicPoint(pubX, pubY);

   // Initialize the public key with the ECP point just created
   cppPubKey.Initialize(CryptoPP::ASN1::secp256k1(), publicPoint);

   // Validate the public key -- not sure why this needs a prng...
   static BTC_PRNG prng;
   assert(cppPubKey.Validate(prng, 3));

   return cppPubKey;
}

/////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::SerializePrivateKey(BTC_PRIVKEY const & privKey)
{
   CryptoPP::Integer privateExp = privKey.GetPrivateExponent();
   SecureBinaryData privKeyData(32);
   privateExp.Encode(privKeyData.getPtr(), privKeyData.getSize());
   return privKeyData;
}
   
/////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::SerializePublicKey(BTC_PUBKEY const & pubKey)
{
   BTC_ECPOINT publicPoint = pubKey.GetPublicElement();
   CryptoPP::Integer pubX = publicPoint.x;
   CryptoPP::Integer pubY = publicPoint.y;
   SecureBinaryData pubData(65);
   pubData.fill(0x04);  // we fill just to set the first byte...

   pubX.Encode(pubData.getPtr()+1,  32);
   pubY.Encode(pubData.getPtr()+33, 32);
   return pubData;
}

/////////////////////////////////////////////////////////////////////////////
BTC_PUBKEY CryptoECDSA::ComputePublicKey(BTC_PRIVKEY const & cppPrivKey)
{
   BTC_PUBKEY cppPubKey;
   cppPrivKey.MakePublicKey(cppPubKey);

   // Validate the public key -- not sure why this needs a prng...
   static BTC_PRNG prng;
   assert(cppPubKey.Validate(prng, 3));
   assert(cppPubKey.Validate(prng, 3));

   return cppPubKey;
}


/////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::SignData(SecureBinaryData const & binToSign, 
                                       SecureBinaryData const & binPrivKey)
{
   BTC_PRIVKEY cppPrivKey = ParsePrivateKey(binPrivKey);
   return SignData(binToSign, cppPrivKey);
}

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


/////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::VerifyData(SecureBinaryData const & binMessage, 
                             SecureBinaryData const & binSignature,
                             SecureBinaryData const & pubkeyX,
                             SecureBinaryData const & pubkeyY)
{
   BTC_PUBKEY cppPubKey = ParsePublicKey(pubkeyX, pubkeyY);
   return VerifyData(binMessage, binSignature, cppPubKey);
}

/////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::VerifyData(SecureBinaryData const & binMessage, 
                             SecureBinaryData const & binSignature,
                             BTC_PUBKEY const & cppPubKey)
                            
{


   static CryptoPP::SHA256  sha256;
   static CryptoPP::AutoSeededRandomPool prng;

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









