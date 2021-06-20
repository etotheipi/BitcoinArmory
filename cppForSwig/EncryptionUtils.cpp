////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////
#include "EncryptionUtils.h"
#include "log.h"
#include "integer.h"
#include "oids.h"

//#include <openssl/ec.h>
//#include <openssl/ecdsa.h>
//#include <openssl/obj_mac.h>


#define CRYPTO_DEBUG false



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
   for(unsigned int i=0; i<getSize(); i++)
      if( (*this)[i] != sbd2[i] )
         return false;
   return true;
}

/////////////////////////////////////////////////////////////////////////////
// Swap endianness of the bytes in the index range [pos1, pos2)
SecureBinaryData SecureBinaryData::copySwapEndian(size_t pos1, size_t pos2) const
{
   return SecureBinaryData(BinaryData::copySwapEndian(pos1, pos2));
}

/////////////////////////////////////////////////////////////////////////////
SecureBinaryData SecureBinaryData::GenerateRandom(uint32_t numBytes, 
                                                  SecureBinaryData entropy)
{
   BTC_PRNG prng;

   // Entropy here refers to *EXTRA* entropy.  Crypto++ has it's own mechanism
   // for generating entropy which is sufficient, but it doesn't hurt to add
   // more if you have it.
   if(entropy.getSize() > 0)
      prng.IncorporateEntropy( (byte*)entropy.getPtr(), entropy.getSize());

   SecureBinaryData randData(numBytes);
   prng.GenerateBlock(randData.getPtr(), numBytes);
   return randData;  
}

/////////////////////////////////////////////////////////////////////////////
KdfRomix::KdfRomix(void) : 
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
      for(uint32_t i=0; i<numTest; i++)
      {
         SecureBinaryData _testKey("This is an example key to test KDF iteration speed");
         _testKey = DeriveKey_OneIter(_testKey);
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
   for(uint32_t nSeq=0; nSeq<nLookups; nSeq++)
   {
      // Interpret last 4 bytes of last result (mod seqCt) as next LUT index
      newIndex = *(uint32_t*)(X.getPtr()+HSZ-4) % sequenceCount_;

      // V represents the hash result at <newIndex>
      V64ptr = (uint64_t*)(frontOfLUT + HSZ*newIndex);

      // xor X with V, and store the result in X
      for(uint32_t i=0; i<nXorOps; i++)
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
SecureBinaryData CryptoAES::EncryptCBC(const SecureBinaryData & data, 
                                       const SecureBinaryData & key,
                                       SecureBinaryData & iv) const
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
SecureBinaryData CryptoAES::DecryptCBC(const SecureBinaryData & data, 
                                       const SecureBinaryData & key,
                                       const SecureBinaryData & iv  ) const
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




/////////////////////////////////////////////////////////////////////////////
BTC_PRIVKEY CryptoECDSA::CreateNewPrivateKey(SecureBinaryData entropy)
{
   return ParsePrivateKey(SecureBinaryData().GenerateRandom(32, entropy));
}

/////////////////////////////////////////////////////////////////////////////
BTC_PRIVKEY CryptoECDSA::ParsePrivateKey(SecureBinaryData const & privKeyData)
{
   BTC_PRIVKEY cppPrivKey;

   CryptoPP::Integer privateExp;
   privateExp.Decode(privKeyData.getPtr(), privKeyData.getSize(), UNSIGNED);
   cppPrivKey.Initialize(CryptoPP::ASN1::secp256k1(), privateExp);
   return cppPrivKey;
}


/////////////////////////////////////////////////////////////////////////////
BTC_PUBKEY CryptoECDSA::ParsePublicKey(SecureBinaryData const & pubKey65B)
{
   SecureBinaryData pubXbin(pubKey65B.getSliceRef( 1,32));
   SecureBinaryData pubYbin(pubKey65B.getSliceRef(33,32));
   return ParsePublicKey(pubXbin, pubYbin);
}

/////////////////////////////////////////////////////////////////////////////
BTC_PUBKEY CryptoECDSA::ParsePublicKey(SecureBinaryData const & pubKeyX32B,
                                       SecureBinaryData const & pubKeyY32B)
{
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

/////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::SerializePrivateKey(BTC_PRIVKEY const & privKey)
{
   CryptoPP::Integer privateExp = privKey.GetPrivateExponent();
   SecureBinaryData privKeyData(32);
   privateExp.Encode(privKeyData.getPtr(), privKeyData.getSize(), UNSIGNED);
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

   pubX.Encode(pubData.getPtr()+1,  32, UNSIGNED);
   pubY.Encode(pubData.getPtr()+33, 32, UNSIGNED);
   return pubData;
}

/////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::ComputePublicKey(SecureBinaryData const & cppPrivKey)
{
   BTC_PRIVKEY pk = ParsePrivateKey(cppPrivKey);
   BTC_PUBKEY  pub;
   pk.MakePublicKey(pub);
   return SerializePublicKey(pub);
}

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

////////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::GenerateNewPrivateKey(SecureBinaryData entropy)
{
   return SecureBinaryData().GenerateRandom(32, entropy);
}


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

/////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::CheckPubPrivKeyMatch(SecureBinaryData const & privKey32,
                                       SecureBinaryData const & pubKey65)
{
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

bool CryptoECDSA::VerifyPublicKeyValid(SecureBinaryData const & pubKey)
{
   if(CRYPTO_DEBUG)
   {
      cout << "BinPub: " << pubKey.toHexStr() << endl;
   }

   SecureBinaryData keyToCheck(65);

   // To support compressed keys, we'll just check to see if a key is compressed
   // and then decompress it.
   if(pubKey.getSize() == 33) {
      keyToCheck = UncompressPoint(pubKey);
   }
   else {
      keyToCheck = pubKey;
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


/////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::VerifyData(SecureBinaryData const & binMessage, 
                             SecureBinaryData const & binSignature,
                             SecureBinaryData const & pubkey65B)
{
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

/////////////////////////////////////////////////////////////////////////////
bool CryptoECDSA::VerifyData(BinaryData const & binMessage,
   const BinaryData& sig,
   BTC_PUBKEY const & cppPubKey) const
{
   /***
   This is the faster sig verification, with less sanity checks and copies.
   Meant for chain verifiation, use the SecureBinaryData versions for regular
   verifications.
   ***/

   CryptoPP::SHA256  sha256;
   BTC_PRNG prng;

   //pub keys are already validated by the script parser

   // We execute the first SHA256 op, here.  Next one is done by Verifier
   BinaryData hashVal(32);
   sha256.CalculateDigest(hashVal.getPtr(),
      binMessage.getPtr(),
      binMessage.getSize());

   // Verifying message 
   BTC_VERIFIER verifier(cppPubKey);
   return verifier.VerifyMessage((const byte*)hashVal.getPtr(),
      hashVal.getSize(),
      (const byte*)sig.getPtr(),
      sig.getSize());
}

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
// Deterministically generate new private key using a chaincode
// Changed:  added using the hash of the public key to the mix
//           b/c multiplying by the chaincode alone is too "linear"
//           (there's no reason to believe it's insecure, but it doesn't
//           hurt to add some extra entropy/non-linearity to the chain
//           generation process)
SecureBinaryData CryptoECDSA::ComputeChainedPrivateKey(
                                 SecureBinaryData const & binPrivKey,
                                 SecureBinaryData const & chainCode,
                                 SecureBinaryData binPubKey,
                                 SecureBinaryData* multiplierOut)
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
      LOGERR << "***ERROR:  Invalid private key or chaincode (both must be 32B)";
      LOGERR << "BinPrivKey: " << binPrivKey.getSize();
      LOGERR << "BinPrivKey: (not logged for security)";
      //LOGERR << "BinPrivKey: " << binPrivKey.toHexStr();
      LOGERR << "BinChain  : " << chainCode.getSize();
      LOGERR << "BinChain  : " << chainCode.toHexStr();
   }

   // Adding extra entropy to chaincode by xor'ing with hash256 of pubkey
   BinaryData chainMod  = binPubKey.getHash256();
   BinaryData chainOrig = chainCode.getRawCopy();
   BinaryData chainXor(32);
      
   for(uint8_t i=0; i<8; i++)
   {
      uint8_t offset = 4*i;
      *(uint32_t*)(chainXor.getPtr()+offset) =
                           *(uint32_t*)( chainMod.getPtr()+offset) ^ 
                           *(uint32_t*)(chainOrig.getPtr()+offset);
   }


   // Hard-code the order of the group
   static SecureBinaryData SECP256K1_ORDER_BE = SecureBinaryData().CreateFromHex(
           "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141");
   
   CryptoPP::Integer mult, origPrivExp, ecOrder;
   // A 
   mult.Decode(chainXor.getPtr(), chainXor.getSize(), UNSIGNED);
   // B 
   origPrivExp.Decode(binPrivKey.getPtr(), binPrivKey.getSize(), UNSIGNED);
   // C
   ecOrder.Decode(SECP256K1_ORDER_BE.getPtr(), SECP256K1_ORDER_BE.getSize(), UNSIGNED);

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
// Deterministically generate new public key using a chaincode
SecureBinaryData CryptoECDSA::ComputeChainedPublicKey(
                                SecureBinaryData const & binPubKey,
                                SecureBinaryData const & chainCode,
                                SecureBinaryData* multiplierOut)
{
   if(CRYPTO_DEBUG)
   {
      cout << "ComputeChainedPUBLICKey:" << endl;
      cout << "   BinPub: " << binPubKey.toHexStr() << endl;
      cout << "   BinChn: " << chainCode.toHexStr() << endl;
   }
   static SecureBinaryData SECP256K1_ORDER_BE = SecureBinaryData::CreateFromHex(
           "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141");

   // Added extra entropy to chaincode by xor'ing with hash256 of pubkey
   BinaryData chainMod  = binPubKey.getHash256();
   BinaryData chainOrig = chainCode.getRawCopy();
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

////////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::InvMod(const SecureBinaryData& m)
{
   static BinaryData N = BinaryData::CreateFromHex(
           "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141");
   CryptoPP::Integer cppM;
   CryptoPP::Integer cppModulo;
   cppM.Decode(m.getPtr(), m.getSize(), UNSIGNED);
   cppModulo.Decode(N.getPtr(), N.getSize(), UNSIGNED);
   CryptoPP::Integer cppResult = cppM.InverseMod(cppModulo);
   SecureBinaryData result(32);
   cppResult.Encode(result.getPtr(), result.getSize(), UNSIGNED);
   return result;
}


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


////////////////////////////////////////////////////////////////////////////////
CryptoPP::ECP CryptoECDSA::Get_secp256k1_ECP(void)
{
   static bool firstRun = true;
   static CryptoPP::Integer intN;
   static CryptoPP::Integer inta;
   static CryptoPP::Integer intb;

   static BinaryData N;
   static BinaryData a;
   static BinaryData b;

   if(firstRun)
   {
      firstRun = false;
      N = BinaryData::CreateFromHex(
            "fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f");
      a = BinaryData::CreateFromHex(
            "0000000000000000000000000000000000000000000000000000000000000000");
      b = BinaryData::CreateFromHex(
            "0000000000000000000000000000000000000000000000000000000000000007");

      intN.Decode( N.getPtr(),  N.getSize(),  UNSIGNED);
      inta.Decode( a.getPtr(),  a.getSize(),  UNSIGNED);
      intb.Decode( b.getPtr(),  b.getSize(),  UNSIGNED);
   }

   
   return CryptoPP::ECP(intN, inta, intb);
}




////////////////////////////////////////////////////////////////////////////////
BinaryData CryptoECDSA::ECMultiplyScalars(BinaryData const & A, 
                                          BinaryData const & B)
{
   // Hardcode the order of the secp256k1 EC group
   static BinaryData N = BinaryData::CreateFromHex(
           "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141");

   CryptoPP::Integer intA, intB, intC, intN;
   intA.Decode(A.getPtr(), A.getSize(), UNSIGNED);
   intB.Decode(B.getPtr(), B.getSize(), UNSIGNED);
   intN.Decode(N.getPtr(), N.getSize(), UNSIGNED);
   intC = a_times_b_mod_c(intA, intB, intN);

   BinaryData C(32);
   intC.Encode(C.getPtr(), 32, UNSIGNED);
   return C;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData CryptoECDSA::ECMultiplyPoint(BinaryData const & A, 
                                        BinaryData const & Bx,
                                        BinaryData const & By)
{
   CryptoPP::ECP ecp = Get_secp256k1_ECP();
   CryptoPP::Integer intA, intBx, intBy, intCx, intCy;

   intA.Decode( A.getPtr(),  A.getSize(),  UNSIGNED);
   intBx.Decode(Bx.getPtr(), Bx.getSize(), UNSIGNED);
   intBy.Decode(By.getPtr(), By.getSize(), UNSIGNED);

   BTC_ECPOINT B(intBx, intBy);
   BTC_ECPOINT C = ecp.ScalarMultiply(B, intA);

   BinaryData Cbd(64);
   C.x.Encode(Cbd.getPtr(),    32, UNSIGNED);
   C.y.Encode(Cbd.getPtr()+32, 32, UNSIGNED);

   return Cbd;
}

////////////////////////////////////////////////////////////////////////////////
BinaryData CryptoECDSA::ECAddPoints(BinaryData const & Ax, 
                                    BinaryData const & Ay,
                                    BinaryData const & Bx,
                                    BinaryData const & By)
{
   CryptoPP::ECP ecp = Get_secp256k1_ECP();
   CryptoPP::Integer intAx, intAy, intBx, intBy, intCx, intCy;

   intAx.Decode(Ax.getPtr(), Ax.getSize(), UNSIGNED);
   intAy.Decode(Ay.getPtr(), Ay.getSize(), UNSIGNED);
   intBx.Decode(Bx.getPtr(), Bx.getSize(), UNSIGNED);
   intBy.Decode(By.getPtr(), By.getSize(), UNSIGNED);


   BTC_ECPOINT A(intAx, intAy);
   BTC_ECPOINT B(intBx, intBy);

   BTC_ECPOINT C = ecp.Add(A,B);

   BinaryData Cbd(64);
   C.x.Encode(Cbd.getPtr(),    32, UNSIGNED);
   C.y.Encode(Cbd.getPtr()+32, 32, UNSIGNED);

   return Cbd;
}


////////////////////////////////////////////////////////////////////////////////
BinaryData CryptoECDSA::ECInverse(BinaryData const & Ax, 
                                  BinaryData const & Ay)
                                  
{
   CryptoPP::ECP ecp = Get_secp256k1_ECP();
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


////////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::CompressPoint(SecureBinaryData const & pubKey65)
{
   CryptoPP::ECP ecp = Get_secp256k1_ECP();
   BTC_ECPOINT ptPub;
   ecp.DecodePoint(ptPub, (byte*)pubKey65.getPtr(), 65);
   SecureBinaryData ptCompressed(33);
   ecp.EncodePoint((byte*)ptCompressed.getPtr(), ptPub, true);
   return ptCompressed; 
}

////////////////////////////////////////////////////////////////////////////////
SecureBinaryData CryptoECDSA::UncompressPoint(SecureBinaryData const & pubKey33)
{
   CryptoPP::ECP ecp = Get_secp256k1_ECP();
   BTC_ECPOINT ptPub;
   ecp.DecodePoint(ptPub, (byte*)pubKey33.getPtr(), 33);
   SecureBinaryData ptUncompressed(65);
   ecp.EncodePoint((byte*)ptUncompressed.getPtr(), ptPub, false);
   return ptUncompressed; 

}

////////////////////////////////////////////////////////////////////////////////
BinaryData CryptoECDSA::computeLowS(BinaryDataRef s)
{
   static SecureBinaryData SECP256K1_ORDER_BE = SecureBinaryData().CreateFromHex(
      "fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141");

   CryptoPP::Integer ecOrder, sInteger;
   ecOrder.Decode(SECP256K1_ORDER_BE.getPtr(), SECP256K1_ORDER_BE.getSize(), UNSIGNED);

   //divide by 2
   auto&& halfOrder = ecOrder >> 1;

   sInteger.Decode(s.getPtr(), s.getSize(), UNSIGNED);
   if (sInteger > halfOrder)
      sInteger = ecOrder - sInteger;

   auto len = sInteger.ByteCount();
   BinaryData lowS(len);
   sInteger.Encode(lowS.getPtr(), len, UNSIGNED);

   return lowS;
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
