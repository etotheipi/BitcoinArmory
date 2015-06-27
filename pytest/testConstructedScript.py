
import sys
sys.path.append('..')
import unittest

from CppBlockUtils import HDWalletCrypto
from armoryengine.ArmoryUtils import *
from armoryengine.BinaryPacker import *
from armoryengine.BinaryUnpacker import *
from armoryengine.ConstructedScript import *

############# Various constants we wish to use throughout the tests.
# Master key derived from the 2nd BIP32 test vector + child key 0.
BIP32MasterPubKey2        = hex_to_binary(
   "04 cbcaa9c9 8c877a26 977d0082 5c956a23 8e8dddfb d322cce4 f74b0b5b d6ace4a7"
   "   7bd3305d 363c26f8 2c1e41c6 67e4b356 1c06c60a 2104d2b5 48e6dd05 9056aa51")
BIP32MasterPubKey2Comp    = hex_to_binary(
   "03 cbcaa9c9 8c877a26 977d0082 5c956a23 8e8dddfb d322cce4 f74b0b5b d6ace4a7")
BIP32MasterPubKey2_D1     = hex_to_binary(
   "04 fc9e5af0 ac8d9b3c ecfe2a88 8e2117ba 3d089d85 85886c9c 826b6b22 a98d12ea"
   "   67a50538 b6f7d8b5 f7a1cc65 7efd267c de8cc1d8 c0451d13 40a0fb36 42777544")
BIP32MasterPubKey2Comp_D1 = hex_to_binary(
   "02 fc9e5af0 ac8d9b3c ecfe2a88 8e2117ba 3d089d85 85886c9c 826b6b22 a98d12ea")
BIP32MasterChainCode2     = hex_to_binary(
   "   60499f80 1b896d83 179a4374 aeb7822a aeaceaa0 db1f85ee 3e904c4d efbd9689")

# Data related to BIP32MasterPubKey2.
BIP32MasterPubKey2Multiplier = hex_to_binary(
      "60e3739c c2c3950b 7c4d7f32 cc503e13 b996d0f7 a45623d0 a914e1ef a7f811e0")
BIP32MasterPubKey2_D1Hash160 = hex_to_binary(
      "5a61ff8e b7aaca30 10db97eb da761216 10b78096")

# Valid PKS serializations based on BIP32MasterPubKey2.
PKS1Chksum_Uncomp_v0 = hex_to_binary(
      "01002041 04cbcaa9 c98c877a 26977d00 825c956a 238e8ddd fbd322cc e4f74b0b"
      "5bd6ace4 a77bd330 5d363c26 f82c1e41 c667e4b3 561c06c6 0a2104d2 b548e6dd"
      "059056aa 511ff749 e6")
PKS1NoChksum_Comp_v0 = hex_to_binary(
      "01000221 03cbcaa9 c98c877a 26977d00 825c956a 238e8ddd fbd322cc e4f74b0b"
      "5bd6ace4 a7")

# Valid PKS serializations based on BIP32MasterPubKey2.
PKS1NoChksum_Comp_v0_FlagClash1 = hex_to_binary(
      "01000921 03cbcaa9 c98c877a 26977d00 825c956a 238e8ddd fbd322cc e4f74b0b"
      "5bd6ace4 a7")
PKS1NoChksum_Comp_v0_FlagClash2 = hex_to_binary(
      "01001821 03cbcaa9 c98c877a 26977d00 825c956a 238e8ddd fbd322cc e4f74b0b"
      "5bd6ace4 a7")

# CS serializations based on BIP32MasterPubKey2.
CS1Chksum_Uncomp_v0 = hex_to_binary(
      "01000206 76a9ff01 88ac0145 01000441 04cbcaa9 c98c877a 26977d00 825c956a"
      "238e8ddd fbd322cc e4f74b0b 5bd6ace4 a77bd330 5d363c26 f82c1e41 c667e4b3"
      "561c06c6 0a2104d2 b548e6dd 059056aa 51a7e7c4 42")
CS1Chksum_Comp_v0 = hex_to_binary(
      "01000206 76a9ff01 88ac0125 00000621 03cbcaa9 c98c877a 26977d00 825c956a"
      "238e8ddd fbd322cc e4f74b0b 5bd6ace4 a744677b 26")
CS1NoChksum_Comp_v0 = hex_to_binary(
      "01000006 76a9ff01 88ac0125 00000621 03cbcaa9 c98c877a 26977d00 825c956a"
      "238e8ddd fbd322cc e4f74b0b 5bd6ace4 a7")
CS2Chksum_Comp_v0 = hex_to_binary( # Multisig
      "01000305 52ff0252 ae022501 00022103 cbcaa9c9 8c877a26 977d0082 5c956a23"
      "8e8dddfb d322cce4 f74b0b5b d6ace4a7 25010002 2102fc9e 5af0ac8d 9b3cecfe"
      "2a888e21 17ba3d08 9d858588 6c9c826b 6b22a98d 12ea89e2 5fe9")

# PKRP serializations based on BIP32MasterPubKey2.
PKRP1_v0 = hex_to_binary(
      "01022060 e3739cc2 c3950b7c 4d7f32cc 503e13b9 96d0f7a4 5623d0a9 14e1efa7"
      "f811e000")

# SRP serializations based on BIP32MasterPubKey2.
SRP1_v0 = hex_to_binary(
      "01012401 022060e3 739cc2c3 950b7c4d 7f32cc50 3e13b996 d0f7a456 23d0a914"
      "e1efa7f8 11e000")
SRP2_v0 = hex_to_binary(
      "01022401 022060e3 739cc2c3 950b7c4d 7f32cc50 3e13b996 d0f7a456 23d0a914"
      "e1efa7f8 11e00024 01022060 e3739cc2 c3950b7c 4d7f32cc 503e13b9 96d0f7a4"
      "5623d0a9 14e1efa7 f811e000")

# PR serializations based on BIP32MasterPubKey2.
daneName1 = "pksrec1.btcshop.com"
daneName2 = "pksrec2.btcshop.com"
unvalidatedScript1 = hex_to_binary(
      "76a95a61 ff8eb7aa ca3010db 97ebda76 121610b7 809688ac")
PR1_v0 = hex_to_binary(
      "01000001 551876a9 5a61ff8e b7aaca30 10db97eb da761216 10b78096 88ac1370"
      "6b737265 63312e62 74637368 6f702e63 6f6d2701 01240102 2060e373 9cc2c395"
      "0b7c4d7f 32cc503e 13b996d0 f7a45623 d0a914e1 efa7f811 e000")
PR2_v0 = hex_to_binary(
      "01000002 aa1876a9 5a61ff8e b7aaca30 10db97eb da761216 10b78096 88ac1876"
      "a95a61ff 8eb7aaca 3010db97 ebda7612 1610b780 9688ac13 706b7372 6563312e"
      "62746373 686f702e 636f6d13 706b7372 6563312e 62746373 686f702e 636f6d27"
      "01012401 022060e3 739cc2c3 950b7c4d 7f32cc50 3e13b996 d0f7a456 23d0a914"
      "e1efa7f8 11e00027 01012401 022060e3 739cc2c3 950b7c4d 7f32cc50 3e13b996"
      "d0f7a456 23d0a914 e1efa7f8 11e000")

### TODO: Place this stuff where it belongs when it's time!
# TxOutscript validator. From ArmoryUtils.py:512?
# getTxOutScriptType(binScript)


################################################################################
class PKSClassTests(unittest.TestCase):
   # Use serialize/unserialize to confirm that the data struct is correctly
   # formed and can be correctly formed.
   def testSerialization(self):
      # PKS1 with a checksum & uncompressed key.
      pks1ChksumPres = PublicKeySource()
      pks1ChksumPres.initialize(False, False, False, False, False,
                                BIP32MasterPubKey2, True)
      stringPKS1ChksumPres = pks1ChksumPres.serialize()
      self.assertEqual(binary_to_hex(stringPKS1ChksumPres),
                       binary_to_hex(PKS1Chksum_Uncomp_v0))

      # PKS1 without a checksum & with a compressed key.
      pks1NoChksum = PublicKeySource()
      pks1NoChksum.initialize(False, True, False, False, False,
                              BIP32MasterPubKey2Comp, False)
      stringPKS1NoChksum = pks1NoChksum.serialize()
      self.assertEqual(binary_to_hex(stringPKS1NoChksum),
                       binary_to_hex(PKS1NoChksum_Comp_v0))

      # Unserialize and re-serialize to confirm unserialize works.
      pks1ChksumPres_unser = PublicKeySource().unserialize(PKS1Chksum_Uncomp_v0)
      pks1NoChksum_unser = PublicKeySource().unserialize(PKS1NoChksum_Comp_v0)
      stringPKS1Chksum_unser = pks1ChksumPres_unser.serialize()
      stringPKS1NoChksum_unser = pks1NoChksum_unser.serialize()
      self.assertEqual(binary_to_hex(stringPKS1Chksum_unser),
                       binary_to_hex(PKS1Chksum_Uncomp_v0))
      self.assertEqual(binary_to_hex(stringPKS1NoChksum_unser),
                       binary_to_hex(PKS1NoChksum_Comp_v0))

      # Are various PKS structures valid?
      # (NB: Bad checksum test is a slight hack. unserialize() auto-checksums.
      pks1BadChksum = PublicKeySource().unserialize(PKS1Chksum_Uncomp_v0)
      pks1BadChksum.checksum = b'\xde\xad\xbe\xef'
      pks1BadFlag1  = PublicKeySource().unserialize(PKS1NoChksum_Comp_v0_FlagClash1)
      pks1BadFlag2  = PublicKeySource().unserialize(PKS1NoChksum_Comp_v0_FlagClash2)
      pksIsValid = pks1ChksumPres.isValid()
      self.assertEqual(pksIsValid, True)
      pksIsValid = pks1NoChksum.isValid()
      self.assertEqual(pksIsValid, True)
      pksIsValid = pks1BadChksum.isValid()
      self.assertEqual(pksIsValid, False)
      pksIsValid = pks1BadFlag1.isValid()
      self.assertEqual(pksIsValid, False)
      pksIsValid = pks1BadFlag2.isValid()
      self.assertEqual(pksIsValid, False)


################################################################################
class CSClassTests(unittest.TestCase):
   # Use serialize/unserialize to confirm that the data struct is correctly
   # formed and can be correctly formed.
   def testSerialization(self):
      # CS1 w/ a checksum - Pre-built P2PKH
      cs1ChksumPres = ConstructedScript().StandardP2PKHConstructed(BIP32MasterPubKey2)
      stringCS1ChksumPres = cs1ChksumPres.serialize()
      self.assertEqual(binary_to_hex(stringCS1ChksumPres),
                       binary_to_hex(CS1Chksum_Uncomp_v0))

      # CS2 w/ a checksum - Pre-built multisig
      testKeyList = [BIP32MasterPubKey2Comp, BIP32MasterPubKey2Comp_D1]
      cs2ChksumPres = ConstructedScript().StandardMultisigConstructed(2, testKeyList)
      stringCS2ChksumPres = cs2ChksumPres.serialize()
      self.assertEqual(binary_to_hex(stringCS2ChksumPres),
                       binary_to_hex(CS2Chksum_Comp_v0))

      # Unserialize and re-serialize to confirm unserialize works.
      cs1ChksumPres_unser = ConstructedScript().unserialize(CS1Chksum_Uncomp_v0)
      cs2ChksumPres_unser = ConstructedScript().unserialize(CS2Chksum_Comp_v0)
      stringCS1Chksum_unser = cs1ChksumPres_unser.serialize()
      stringCS2Chksum_unser = cs2ChksumPres_unser.serialize()
      self.assertEqual(binary_to_hex(stringCS1Chksum_unser),
                       binary_to_hex(CS1Chksum_Uncomp_v0))
      self.assertEqual(binary_to_hex(stringCS2Chksum_unser),
                       binary_to_hex(CS2Chksum_Comp_v0))


################################################################################
class PKRPClassTests(unittest.TestCase):
   # Use serialize/unserialize to confirm that the data struct is correctly
   # formed and can be correctly formed.
   def testSerialization(self):
      # 1 multiplier.
      pkrp1 = PublicKeyRelationshipProof()
      pkrp1.initialize(BIP32MasterPubKey2Multiplier)
      stringPKRP1 = pkrp1.serialize()
      self.assertEqual(binary_to_hex(stringPKRP1),
                       binary_to_hex(PKRP1_v0))

      # Unserialize and re-serialize to confirm unserialize works.
      pkrp1_unser = PublicKeyRelationshipProof().unserialize(PKRP1_v0)
      stringPKRP1_unser = pkrp1_unser.serialize()
      self.assertEqual(binary_to_hex(stringPKRP1_unser),
                       binary_to_hex(PKRP1_v0))

      # TO DO: ADD isValid() TESTS. NEED SOME BROKEN EXAMPLES ABOVE.


################################################################################
class SRPClassTests(unittest.TestCase):
   # Use serialize/unserialize to confirm that the data struct is correctly
   # formed and can be correctly formed.
   def testSerialization(self):
      # 1 PKRP.
      pkrp1 = PublicKeyRelationshipProof()
      pkrp1.initialize(BIP32MasterPubKey2Multiplier)
      srp1 = ScriptRelationshipProof()
      srp1.initialize([pkrp1])
      stringSRP1 = srp1.serialize()
      self.assertEqual(binary_to_hex(stringSRP1),
                       binary_to_hex(SRP1_v0))

      # 2 PKRPs. Both PKRPs are the same. This test just confirms that the
      # serialization code works for multiple PKRPs.
      srp2 = ScriptRelationshipProof()
      srp2.initialize([pkrp1, pkrp1])
      stringSRP2 = srp2.serialize()
      self.assertEqual(binary_to_hex(stringSRP2),
                       binary_to_hex(SRP2_v0))

      # Unserialize and re-serialize to confirm unserialize works.
      srp1_unser = ScriptRelationshipProof().unserialize(SRP1_v0)
      srp2_unser = ScriptRelationshipProof().unserialize(SRP2_v0)
      stringSRP1_unser = srp1_unser.serialize()
      stringSRP2_unser = srp2_unser.serialize()
      self.assertEqual(binary_to_hex(stringSRP1_unser),
                       binary_to_hex(SRP1_v0))
      self.assertEqual(binary_to_hex(stringSRP2_unser),
                       binary_to_hex(SRP2_v0))


################################################################################
class PRClassTests(unittest.TestCase):
   # Use serialize/unserialize to confirm that the data struct is correctly
   # formed and can be correctly formed.
   def testSerialization(self):
      pkrp1 = PublicKeyRelationshipProof()
      pkrp1.initialize(BIP32MasterPubKey2Multiplier)
      srp1 = ScriptRelationshipProof()
      srp1.initialize([pkrp1])

      # 1 TxOut script.
      pr1 = PaymentRequest()
      pr1.initialize([unvalidatedScript1], [daneName1], [srp1.serialize()])
      stringPR1 = pr1.serialize()
      self.assertEqual(binary_to_hex(stringPR1),
                       binary_to_hex(PR1_v0))

      # 2 TxOut scripts. Both scripts are the same. This test just confirms that
      # the serialization code works for multiple TxOut scripts.
      pr2 = PaymentRequest()
      pr2.initialize([unvalidatedScript1, unvalidatedScript1],
                     [daneName1, daneName1],
                     [srp1.serialize(), srp1.serialize()])
      stringPR2 = pr2.serialize()
      self.assertEqual(binary_to_hex(stringPR2),
                       binary_to_hex(PR2_v0))

      # Unserialize and re-serialize to confirm unserialize works.
      pr1_unser = PaymentRequest().unserialize(PR1_v0)
      pr2_unser = PaymentRequest().unserialize(PR2_v0)
      stringPR1_unser = pr1_unser.serialize()
      stringPR2_unser = pr2_unser.serialize()
      self.assertEqual(binary_to_hex(stringPR1),
                       binary_to_hex(PR1_v0))
      self.assertEqual(binary_to_hex(stringPR2),
                       binary_to_hex(PR2_v0))


################################################################################
class DerivationTests(unittest.TestCase):
   # Confirm that BIP32 multipliers can be obtained from C++ and can be used to
   # create keys that match the keys directly derived via BIP32.
   def testBIP32Derivation(self):
      fakeRootSeed  = SecureBinaryData('\xf1'*32)
      masterExtPrv1 = HDWalletCrypto().convertSeedToMasterKey(fakeRootSeed)
      sbdPubKey1    = masterExtPrv1.getPublicKey()
      sbdChain1     = masterExtPrv1.getChaincode()

      # Get the final pub key and the multiplier proofs, then confirm that we
      # can reverse engineer the final key with the proofs and the root pub key.
      # Note that the proofs will be based on a compressed root pub key.
      finalPub1, multProof1 = DeriveBip32PublicKeyWithProof(sbdPubKey1.toBinStr(),
                                                            sbdChain1.toBinStr(),
                                                            [2, 12, 37])
      final1 = ApplyProofToRootKey(sbdPubKey1.toBinStr(), multProof1)
      final1_alt = ApplyProofToRootKey(sbdPubKey1.toBinStr(), multProof1,
                                       finalPub1)
      self.assertEqual(final1, finalPub1)
      self.assertEqual(final1, final1_alt)

      # Confirm that we can get the 1st derived key from the BIP32 test vector's
      # second key.
      bip32Seed2            = SecureBinaryData(hex_to_binary(
         "fffcf9f6 f3f0edea e7e4e1de dbd8d5d2 cfccc9c6 c3c0bdba b7b4b1ae"
         "aba8a5a2 9f9c9996 93908d8a 8784817e 7b787572 6f6c6966 63605d5a"
         "5754514e 4b484542"))
      masterExtPrv2         = HDWalletCrypto().convertSeedToMasterKey(bip32Seed2)
      sbdPubKey2            = masterExtPrv2.getPublicKey()
      sbdChain2             = masterExtPrv2.getChaincode()
      finalPub2, multProof2 = DeriveBip32PublicKeyWithProof(sbdPubKey2.toBinStr(),
                                                            sbdChain2.toBinStr(),
                                                            [0])
      self.assertEqual(finalPub2, BIP32MasterPubKey2Comp_D1)

      # Confirm that we can apply the multiplier directly and get the correct
      # final key.
      final2ApplyMult = HDWalletCrypto().getChildKeyFromMult_SWIG(
                                                          sbdPubKey2.toBinStr(),
                                                          multProof2.multiplier)
      self.assertEqual(finalPub2, final2ApplyMult)


if __name__ == "__main__":
   unittest.main()
