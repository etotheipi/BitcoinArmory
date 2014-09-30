// #############################################################################
// #                                                                           #
// # Copyright (C) 2011-2014, Armory Technologies, Inc.                        #
// # Distributed under the GNU Affero General Public License (AGPL v3)         #
// # See LICENSE or http://www.gnu.org/licenses/agpl.html                      #
// #                                                                           #
// #############################################################################

// Implementation of RFC 6979 for Crypto++. ECDSA_DetSign<ECP, SHA256>::Signer
// is an example of a signer that uses RFC 6979 to determine the k-value.

#include "pch.h"

#ifndef CRYPTOPP_IMPORTS

#include <iostream>
#include <cstdio>
#include "DetSign.h"
#include "integer.h"
#include "hmac.h"
#include "pubkey.h"
#include "sha.h"

NAMESPACE_BEGIN(CryptoPP)

// Function that takes a big-endian block of data and creates a Crypto++ Integer
// from the data. The Integer will be no larger in size than the ECDSA curve's
// order. (See Sect. 2.3.2 of RFC 6979.)
// INPUT:  Input data (const SecByteBlock&)
//         Number of bits in the ECDSA curve's order (const unsigned int&)
// OUTPUT: N/A
// RETURN: An Integer created from the input data (Integer)
Integer bits2int(const SecByteBlock& inData, const unsigned int& numOrderBits)
{
    Integer newInt(inData, inData.size());
    // If the Integer's larger than the curve order, we must right shift the Int
    // by enough bits to make it the same size as the curve order.
    if(newInt.BitCount() > numOrderBits)
    {
        // TO DO: Think about corner cases where Crypto++ BitCount() could return, say,
        // 255, and possibly mess with the algorithm.
        newInt >>= (newInt.BitCount() - numOrderBits);
    }

    return newInt;
}


// Function that takes a Crypto++ Integer and creates a big-endian data block
// with the same number of bytes as the ECDSA curve's order. (See Sect. 2.3.4 of
// RFC 6979.) Note that the code doesn't care if the input data has a larger
// value than the order. If such a state is important, the input must be
// checked/fixed before calling this function.
// INPUT:  Input Integer (const Integer&)
//         Number of bytes in the ECDSA curve's order (const unsigned int&)
// OUTPUT: N/A
// RETURN: A SecByteBlock, as long as the curve order, created from the input
// data (Integer)
SecByteBlock int2octets(const Integer& inInt, const unsigned int& numOrderBytes)
{
    // Initial setup.
    SecByteBlock retBlock;
    SecByteBlock inIntData(inInt.ByteCount());
    inInt.Encode(inIntData, inInt.ByteCount());

    if(inIntData.size() < numOrderBytes)
    {
        // If incoming Integer is smaller than the curve, encode the input in
        // MSB form and then save the encoded data.
        SecByteBlock tmpData1(numOrderBytes);
        memset(tmpData1, 0, numOrderBytes); // Make sure there are no stray bits
        unsigned int offset = numOrderBytes - tmpData1.size();
        memcpy(tmpData1 + offset, inIntData, numOrderBytes - offset);
        retBlock = tmpData1;
    }
    else if(inIntData.size() > numOrderBytes)
    {
        // If incoming Integer is larger than the curve, encode and save the
        // LSBs of the input.
        SecByteBlock tmpData2(numOrderBytes);
        unsigned int offset = inIntData.size() - numOrderBytes;
        memcpy(tmpData2, inIntData + offset, numOrderBytes);
        retBlock = tmpData2;
    }
    else
    {
        // If incoming Integer the same size as the curve, just save the input.
        retBlock = inIntData;
    }

    return retBlock;
}

// Function that takes a big-endian block of data and creates a Crypto++ Integer
// from the data. The Integer will be no larger in size than the ECDSA curve's
// order. (See Sect. 2.3.2 of RFC 6979.)
// INPUT:  Input data (const SecByteBlock&)
//         Number of bits in the ECDSA curve's order (const unsigned int&)
// OUTPUT: N/A
// RETURN: An Integer from the input data modulo the curve order (Integer)
SecByteBlock bits2octets(const SecByteBlock& inData, const Integer& curveOrder)
{
    // Reduce the input to the length of the ECDSA curve's order. Return it or,
    // if larger than the order, the modulo value.
    Integer newInt1 = bits2int(inData, curveOrder.BitCount());
    Integer newInt2 = newInt1 - curveOrder;
    return int2octets(newInt2.IsNegative() ? newInt1 : newInt2,
                      curveOrder.ByteCount());
}


// Function that goes through the process of creating a k-value to be used when
// performing ECDSA signing of a message. (See Sects. 3.1 & 3.2 of RFC 6979.)
// INPUT:  The private key (const Integer&)
//         The message to hash (const byte*)
//         The size of the message to hash (const size_t&)
//         The ECDSA curve order (const Integer&)
// OUTPUT: N/A
// RETURN: The final k-value (Integer)
Integer getDetKVal(const Integer& prvKey, const byte* msgToHash,
                   const size_t& msgToHashSize, const Integer& curveOrder)
{
    // Initial setup.
    // NB: SHA256 is hard-coded. This ought to be changed if at all possible.
    unsigned int numOrderBits = curveOrder.BitCount(); // 256 for secp256k1
    unsigned int numOrderBytes = curveOrder.ByteCount(); // 32 for secp256k1
    SecByteBlock hmacKey(32); // SHA-256
    memset(hmacKey, 0, 32); // This is the initial key.
    HMAC<SHA256> dummyHMAC(hmacKey, hmacKey.size());
    const unsigned int hmacBits = dummyHMAC.DigestSize() * 8; // 256 for HMAC-SHA256
    SecByteBlock inputHash(dummyHMAC.DigestSize());
    SecByteBlock V(dummyHMAC.DigestSize());
    SecByteBlock prvKeyBlock = int2octets(prvKey, numOrderBytes);
    SecByteBlock singleByte(1);
    memset(V, '\x01', dummyHMAC.DigestSize());
    memset(singleByte, 0, 1);

    // Hash the input.
    SHA256 hashFunct;
    hashFunct.CalculateDigest(inputHash, msgToHash, msgToHashSize);
    SecByteBlock choppedHash = bits2octets(inputHash, curveOrder);

    // Create the second key. (The first key was already created w/ memset(0).)
    HMAC<SHA256> detSignMAC1(hmacKey, hmacKey.size());
    SecByteBlock hmacInput1 = V + singleByte + prvKeyBlock + choppedHash;
    detSignMAC1.CalculateDigest(hmacKey, hmacInput1, hmacInput1.size());

    // Hash the V value.
    HMAC<SHA256> detSignMAC2(hmacKey, hmacKey.size());
    detSignMAC2.CalculateDigest(V, V, V.size());

    // Create the third (and probably final) key.
    memset(singleByte, '\x01', 1);
    HMAC<SHA256> detSignMAC3(hmacKey, hmacKey.size());
    SecByteBlock hmacInput2 = V + singleByte + prvKeyBlock + inputHash;
    detSignMAC3.CalculateDigest(hmacKey, hmacInput2, hmacInput2.size());

    // Hash the V value.
    HMAC<SHA256> detSignMAC4(hmacKey, hmacKey.size());
    detSignMAC4.CalculateDigest(V, V, V.size());

    // Loop around and search for the final k-value.
    bool finalKValFound = false;
    Integer finalLoopVar;
    while(!finalKValFound)
    {
        SecByteBlock loopVarData;
        unsigned int loopVarBytes = 0;
        while(loopVarBytes < numOrderBytes) {
            HMAC<SHA256> detSignMAC5(hmacKey, hmacKey.size());
            detSignMAC5.CalculateDigest(V, V, V.size());
            loopVarData += V;
            loopVarBytes += hmacKey.size();
        }

        // Check to see if the final value is valid. If not, we must compute a
        // new k-value. (Failure is highly improbable.)
        Integer tmpLoopVar = bits2int(loopVarData, numOrderBits);
        if(tmpLoopVar >= Integer::One() && tmpLoopVar < curveOrder)
        {
            finalLoopVar = tmpLoopVar;
            finalKValFound = true;
        }
        else
        {
            // Create a new V value by hashing it twice, the first time w/ 0x00
            // appended.
            memset(singleByte, 0, 1);
            SecByteBlock newHMACInput = V + singleByte;
            HMAC<SHA256> detSignMAC6(hmacKey, hmacKey.size());
            detSignMAC6.CalculateDigest(hmacKey, newHMACInput, newHMACInput.size());
            HMAC<SHA256> detSignMAC7(hmacKey, hmacKey.size());
            detSignMAC7.CalculateDigest(V, V, V.size());
        }
    }

    return finalLoopVar;
}


// This is actually taken from DL_SignerBase (pubkey.h) with one modification:
// The RNG is completely ignored. Instead, we'll determine the k-value using RNG
// 6979, which requires only the private key (m_key, from DL_ObjectImplBase -
// pubkey.h) and the data to be signed (messageAccumulator).
// INPUT:  An RNG that can be ignored (RandomNumberGenerator&)
//         The message to sign (PK_MessageAccumulator&)
//         The ECDSA curve order (const Integer&)
// OUTPUT: The signature (byte*)
// RETURN: The size of the signature in bytes (size_t)
template <class T>
size_t DL_SignerImplDetSign<T>::SignAndRestart(RandomNumberGenerator &rng,
                                               PK_MessageAccumulator &messageAccumulator,
                                               byte *signature,
                                               bool restart) const
{
	this->GetMaterial().DoQuickSanityCheck();

	PK_MessageAccumulatorBase &ma = static_cast<PK_MessageAccumulatorBase &>(messageAccumulator);
	const DL_ElgamalLikeSignatureAlgorithm<typename T::Element> &alg = this->GetSignatureAlgorithm();
	const DL_GroupParameters<typename T::Element> &params = this->GetAbstractGroupParameters();
	const DL_PrivateKey<typename T::Element> &key = this->GetKeyInterface();

	// Get the message representative (usually just a hash of the message
	// rep data).
	SecByteBlock representative(this->MessageRepresentativeLength());
	this->GetMessageEncodingInterface().ComputeMessageRepresentative(
    	rng,
    	ma.m_recoverableMessage, ma.m_recoverableMessage.size(), 
		ma.AccessHash(), this->GetHashIdentifier(), ma.m_empty, 
		representative, this->MessageRepresentativeBitLength());
	ma.m_empty = true;
	Integer e(representative, representative.size());

	Integer k = GetVal(key.GetPrivateExponent(),
                       representative,
                       representative.size(),
                       params.GetSubgroupOrder());

	Integer r, s;
	r = params.ConvertElementToInteger(params.ExponentiateBase(k)); // Set r pre-mod
	alg.Sign(params, key.GetPrivateExponent(), k, e, r, s); // Set s

	size_t rLen = alg.RLen(params);
	r.Encode(signature, rLen);
	s.Encode(signature+rLen, alg.SLen(params));

	return this->SignatureLength();
}

NAMESPACE_END

#endif
