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
    // k-value using RNG 6979, which requires only the private key and the data
    // to sign (messageAccumulator).
    // INPUT:  An unused RNG required by the prototype (RandomNumberGenerator&)
    //         The message to sign (PK_MessageAccumulator&)
    //         An unused "restart" variable required by the prototype (bool)
    // OUTPUT: The final signature (byte*)
    // RETURN: The size of the signature in bytes (size_t)
    size_t SignAndRestart(RandomNumberGenerator &rng,
                          PK_MessageAccumulator &messageAccumulator,
                          byte *signature,
                          bool restart) const
    {
        this->GetMaterial().DoQuickSanityCheck();

        // Actual variable locations:
        // SCHEME_OPTIONS = DL_SignatureSchemeOptions<DL_SSDetSign<DL_Keys_ECDSA<ECP>,
        //                                                         DL_Algorithm_ECDSA<ECP>,
        //                                                         DL_SignatureMessageEncodingMethod_DSA,
        //                                                         SHA256,
        //                                                         int>,
        //                                            DL_Keys_ECDSA<ECP>,
        //                                            DL_Algorithm_ECDSA<ECP>,
        //                                            DL_SignatureMessageEncodingMethod_DSA,
        //                                            SHA256>
        // alg - Singleton<CPP_TYPENAME SCHEME_OPTIONS::SignatureAlgorithm>().Ref() (DL_ObjectImpl)
        // params - m_groupParameters (DL_KeyImpl)
        // key - m_key (DL_ObjectImplBase)
        PK_MessageAccumulatorBase &ma = static_cast<PK_MessageAccumulatorBase &>(messageAccumulator);
        const DL_ElgamalLikeSignatureAlgorithm<typename SCHEME_OPTIONS::Element> &alg = this->GetSignatureAlgorithm();
        const DL_GroupParameters<typename SCHEME_OPTIONS::Element> &params = this->GetAbstractGroupParameters();
        const DL_PrivateKey<typename SCHEME_OPTIONS::Element> &key = this->GetKeyInterface();

        // Get the message representative (usually just a hash of the message
        // rep data).
        SecByteBlock representative(this->MessageRepresentativeLength());
        this->GetMessageEncodingInterface().ComputeMessageRepresentative(
                                        rng,
                                        ma.m_recoverableMessage,
                                        ma.m_recoverableMessage.size(),
                                        ma.AccessHash(),
                                        this->GetHashIdentifier(),
                                        ma.m_empty,
                                        representative,
                                        this->MessageRepresentativeBitLength());
        ma.m_empty = true;
        Integer e(representative, representative.size());

        // The k-value must be deterministic.
        Integer k = getDetKVal(key.GetPrivateExponent(),
                               representative,
                               representative.size(),
                               params.GetSubgroupOrder(),
                               params.GetSubgroupOrder().BitCount());

        Integer r, s;
        r = params.ConvertElementToInteger(params.ExponentiateBase(k)); // Set r pre-mod
        alg.Sign(params, key.GetPrivateExponent(), k, e, r, s); // Set s

        size_t rLen = alg.RLen(params);
        r.Encode(signature, rLen);
        s.Encode(signature+rLen, alg.SLen(params));

        return this->SignatureLength();
    }
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
    // FYI: "EMSAD" chosen at random.
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

#endif
