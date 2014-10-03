// #############################################################################
// #                                                                           #
// # Copyright (C) 2011-2014, Armory Technologies, Inc.                        #
// # Distributed under the GNU Affero General Public License (AGPL v3)         #
// # See LICENSE or http://www.gnu.org/licenses/agpl.html                      #
// #                                                                           #
// #############################################################################

// Implementation of RFC 6979 for Crypto++. ECDSA_DetSign<ECP, SHA256>::Signer
// is an example of a signer that uses RFC 6979 to determine the k-value.

#ifndef CRYPTOPP_DETSIGNRNG_H
#define CRYPTOPP_DETSIGNRNG_H

#include "pubkey.h"
#include "eccrypto.h"

NAMESPACE_BEGIN(CryptoPP)

Integer getDetKVal(const Integer& prvKey, const byte* msgToHash,
                   const size_t& msgToHashSize, const Integer& curveOrder,
                   const size_t& curveOrderNumBits);

template <class SCHEME_OPTIONS>
class DL_SignerImplDetSign : public DL_SignerImpl<SCHEME_OPTIONS>
{
    // This is actually taken from DL_SignerBase (pubkey.h) with one
    // modification: The RNG is completely ignored. Instead, we'll determine the
    // k-value using RNG 6979, which requires only the private key (m_key, from
    // DL_ObjectImplBase - pubkey.h) and the data to be signed
    // (messageAccumulator).
    size_t SignAndRestart(RandomNumberGenerator &rng,
                          PK_MessageAccumulator &messageAccumulator,
                          byte *signature,
                          bool restart) const;
};

// Forward declaration used by the actual class declaration.
template <class KEYS, class SA, class MEM, class H, class ALG_INFO>
class DL_SSDetSign;

//! Discrete Log Based Signature Scheme
template <class KEYS, class SA, class MEM, class H, class ALG_INFO = DL_SSDetSign<KEYS, SA, MEM, H, int> >
class DL_SSDetSign : public KEYS
{
	typedef DL_SignatureSchemeOptions<ALG_INFO, KEYS, SA, MEM, H> DetSchemeOptions;

public:
	static std::string StaticAlgorithmName() {return SA::StaticAlgorithmName() + std::string("/EMSAD(") + H::StaticAlgorithmName() + ")";}

	//! implements PK_Signer interface
	typedef PK_FinalTemplate<DL_SignerImplDetSign<DetSchemeOptions> > DetSigner;
	//! implements PK_Verifier interface
	typedef PK_FinalTemplate<DL_VerifierImpl<DetSchemeOptions> > DetVerifier;
};

template <class EC, class H>
struct ECDSA_DetSign : public DL_SSDetSign<DL_Keys_ECDSA<EC>, DL_Algorithm_ECDSA<EC>, DL_SignatureMessageEncodingMethod_DSA, H>
{
};

NAMESPACE_END

#ifdef CRYPTOPP_MANUALLY_INSTANTIATE_TEMPLATES
#include "DetSign.cpp"
#endif

#endif
