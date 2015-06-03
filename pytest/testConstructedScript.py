
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
   "04cbcaa9 c98c877a 26977d00 825c956a 238e8ddd fbd322cc e4f74b0b 5bd6ace4"
   "a77bd330 5d363c26 f82c1e41 c667e4b3 561c06c6 0a2104d2 b548e6dd 059056aa 51")
BIP32MasterPubKey2Comp    = hex_to_binary(
   "03cbcaa9 c98c877a 26977d00 825c956a 238e8ddd fbd322cc e4f74b0b 5bd6ace4 a7")
BIP32MasterPubKey2_D1     = hex_to_binary(
   "04fc9e5a f0ac8d9b 3cecfe2a 888e2117 ba3d089d 8585886c 9c826b6b 22a98d12"
   "ea67a505 38b6f7d8 b5f7a1cc 657efd26 7cde8cc1 d8c0451d 1340a0fb 36427775 44")
BIP32MasterPubKey2Comp_D1 = hex_to_binary(
   "02fc9e5a f0ac8d9b 3cecfe2a 888e2117 ba3d089d 8585886c 9c826b6b 22a98d12 ea")

# Data related to BIP32MasterPubKey2.
BIP32MasterPubKey2Multiplier = hex_to_binary(
   "60e3739c c2c3950b 7c4d7f32 cc503e13 b996d0f7 a45623d0 a914e1ef a7f811e0")
BIP32MasterPubKey2_D1Hash160 = hex_to_binary(
   "5a61ff8e b7aaca30 10db97eb da761216 10b78096")

# PKS serializations based on BIP32MasterPubKey2.
PKS1Chksum_Uncomp_v0 = hex_to_binary(
   "00004041 04cbcaa9 c98c877a 26977d00 825c956a 238e8ddd fbd322cc e4f74b0b"
   "5bd6ace4 a77bd330 5d363c26 f82c1e41 c667e4b3 561c06c6 0a2104d2 b548e6dd"
   "059056aa 513a6dee 2c")
PKS1NoChksum_Comp_v0 = hex_to_binary(
   "00000221 03cbcaa9 c98c877a 26977d00 825c956a 238e8ddd fbd322cc e4f74b0b"
   "5bd6ace4 a7")

# CS serializations based on BIP32MasterPubKey2.
CS1Chksum_Uncomp_v0 = hex_to_binary(
   "00000206 76a9ff01 88ac0145 00000441 04cbcaa9 c98c877a 26977d00 825c956a"
   "238e8ddd fbd322cc e4f74b0b 5bd6ace4 a77bd330 5d363c26 f82c1e41 c667e4b3"
   "561c06c6 0a2104d2 b548e6dd 059056aa 51142038 ce")
CS1Chksum_Comp_v0 = hex_to_binary(
   "00000206 76a9ff01 88ac0125 00000621 03cbcaa9 c98c877a 26977d00 825c956a"
   "238e8ddd fbd322cc e4f74b0b 5bd6ace4 a744677b 26")
CS1NoChksum_Comp_v0 = hex_to_binary(
   "00000006 76a9ff01 88ac0125 00000621 03cbcaa9 c98c877a 26977d00 825c956a"
   "238e8ddd fbd322cc e4f74b0b 5bd6ace4 a7")
CS2Chksum_Comp_v0 = hex_to_binary( # Multisig
   "00000305 52ff0252 ae022500 00022103 cbcaa9c9 8c877a26 977d0082 5c956a23"
   "8e8dddfb d322cce4 f74b0b5b d6ace4a7 25000002 2102fc9e 5af0ac8d 9b3cecfe"
   "2a888e21 17ba3d08 9d858588 6c9c826b 6b22a98d 12ea87d6 e378")

# PKRP serializations based on BIP32MasterPubKey2.
PKRP1_v0 = hex_to_binary(
   "00012060 e3739cc2 c3950b7c 4d7f32cc 503e13b9 96d0f7a4 5623d0a9 14e1efa7"
   "f811e0")
PKRP2_v0 = hex_to_binary(
   "00022060 e3739cc2 c3950b7c 4d7f32cc 503e13b9 96d0f7a4 5623d0a9 14e1efa7"
   "f811e020 60e3739c c2c3950b 7c4d7f32 cc503e13 b996d0f7 a45623d0 a914e1ef"
   "a7f811e0")

# SRP serializations based on BIP32MasterPubKey2.
SRP1_v0 = hex_to_binary(
   "00012300 012060e3 739cc2c3 950b7c4d 7f32cc50 3e13b996 d0f7a456 23d0a914"
   "e1efa7f8 11e0")
SRP2_v0 = hex_to_binary(
   "00022300 012060e3 739cc2c3 950b7c4d 7f32cc50 3e13b996 d0f7a456 23d0a914"
   "e1efa7f8 11e02300 012060e3 739cc2c3 950b7c4d 7f32cc50 3e13b996 d0f7a456"
   "23d0a914 e1efa7f8 11e0")

# PR serializations based on BIP32MasterPubKey2.
daneName1 = "pksrec1.btcshop.com"
daneName2 = "pksrec2.btcshop.com"
unvalidatedScript1 = hex_to_binary(
   "76a95a61 ff8eb7aa ca3010db 97ebda76 121610b7 809688ac")
PR1_v0 = hex_to_binary(
   "00000001 541876a9 5a61ff8e b7aaca30 10db97eb da761216 10b78096 88ac1370"
   "6b737265 63312e62 74637368 6f702e63 6f6d2600 01230001 2060e373 9cc2c395"
   "0b7c4d7f 32cc503e 13b996d0 f7a45623 d0a914e1 efa7f811 e0")
PR2_v0 = hex_to_binary(
   "00000002 a81876a9 5a61ff8e b7aaca30 10db97eb da761216 10b78096 88ac1876"
   "a95a61ff 8eb7aaca 3010db97 ebda7612 1610b780 9688ac13 706b7372 6563312e"
   "62746373 686f702e 636f6d13 706b7372 6563312e 62746373 686f702e 636f6d26"
   "00012300 012060e3 739cc2c3 950b7c4d 7f32cc50 3e13b996 d0f7a456 23d0a914"
   "e1efa7f8 11e02600 01230001 2060e373 9cc2c395 0b7c4d7f 32cc503e 13b996d0"
   "f7a45623 d0a914e1 efa7f811 e0")

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
      pks1NoChksum.initialize(False, False, False, False, False,
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
      pkrp1.initialize([BIP32MasterPubKey2Multiplier])
      stringPKRP1 = pkrp1.serialize()
      self.assertEqual(binary_to_hex(stringPKRP1),
                       binary_to_hex(PKRP1_v0))

      # 2 multipliers. Both mults are the same. This test just confirms that the
      # serialization code works.
      pkrp2 = PublicKeyRelationshipProof()
      pkrp2.initialize([BIP32MasterPubKey2Multiplier,
                        BIP32MasterPubKey2Multiplier])
      stringPKRP2 = pkrp2.serialize()
      self.assertEqual(binary_to_hex(stringPKRP2),
                       binary_to_hex(PKRP2_v0))

      # Unserialize and re-serialize to confirm unserialize works.
      pkrp1_unser = PublicKeyRelationshipProof().unserialize(PKRP1_v0)
      pkrp2_unser = PublicKeyRelationshipProof().unserialize(PKRP2_v0)
      stringPKRP1_unser = pkrp1_unser.serialize()
      stringPKRP2_unser = pkrp2_unser.serialize()
      self.assertEqual(binary_to_hex(stringPKRP1_unser),
                       binary_to_hex(PKRP1_v0))
      self.assertEqual(binary_to_hex(stringPKRP2_unser),
                       binary_to_hex(PKRP2_v0))


################################################################################
class SRPClassTests(unittest.TestCase):
   # Use serialize/unserialize to confirm that the data struct is correctly
   # formed and can be correctly formed.
   def testSerialization(self):
      # 1 PKRP.
      pkrp1 = PublicKeyRelationshipProof()
      pkrp1.initialize([BIP32MasterPubKey2Multiplier])
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
      srp1_unser = PublicKeyRelationshipProof().unserialize(SRP1_v0)
      srp2_unser = PublicKeyRelationshipProof().unserialize(SRP2_v0)
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
      pkrp1.initialize([BIP32MasterPubKey2Multiplier])
      srp1 = ScriptRelationshipProof()
      srp1.initialize([pkrp1])

      # 1 TxOut script.
      pr1 = PaymentRequest()
      pr1.initialize([unvalidatedScript1], [daneName1], [srp1.serialize()], 0)
      stringPR1 = pr1.serialize()
      self.assertEqual(binary_to_hex(stringPR1),
                       binary_to_hex(PR1_v0))

      # 2 TxOut scripts. Both scripts are the same. This test just confirms that
      # the serialization code works for multiple TxOut scripts.
      pr2 = PaymentRequest()
      pr2.initialize([unvalidatedScript1, unvalidatedScript1],
                     [daneName1, daneName1],
                     [srp1.serialize(), srp1.serialize()],
                     0)
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

      # Now, let's confirm that we can add the multipliers into one multiplier
      # and get the same final key as if we got children one at a time.
      finalMult1 = HDWalletCrypto().addModMults_SWIG(multProof1.rawMultList)
      finalMultList1 = []
      finalMultList1.append(finalMult1)
      final1CombMults = HDWalletCrypto().getChildKeyFromOps_SWIG(
                                                          sbdPubKey1.toBinStr(),
                                                                 finalMultList1)
      self.assertEqual(final1, final1CombMults)

      # Now, let's confirm that we can add the multipliers into two different
      # multipliers (1 & 2+3, or 1+2 & 3) and get the same final key as if we
      # got children one at a time.
      # (1 & 2+3)
      listY1 = []
      listZ1 = []
      listY1.append(multProof1.rawMultList[1])
      listY1.append(multProof1.rawMultList[2])
      tempMult1 = HDWalletCrypto().addModMults_SWIG(listY1)
      listZ1.append(multProof1.rawMultList[0])
      listZ1.append(tempMult1)
      temp1CombMults = HDWalletCrypto().getChildKeyFromOps_SWIG(
                                                          sbdPubKey1.toBinStr(),
                                                                listZ1)
      self.assertEqual(final1, temp1CombMults)

      # (1+2 & 3)
      listY2 = []
      listZ2 = []
      listY2.append(multProof1.rawMultList[0])
      listY2.append(multProof1.rawMultList[1])
      tempMult2 = HDWalletCrypto().addModMults_SWIG(listY2)
      listZ2.append(tempMult2)
      listZ2.append(multProof1.rawMultList[2])
      temp2CombMults = HDWalletCrypto().getChildKeyFromOps_SWIG(
                                                          sbdPubKey1.toBinStr(),
                                                                listZ2)
      self.assertEqual(final1, temp2CombMults)

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

      # Now, let's confirm that we can add the multipliers into one multiplier
      # and get the same final key as if we got children one at a time.
      finalMult2 = HDWalletCrypto().addModMults_SWIG(multProof2.rawMultList)
      finalMultList2 = []
      finalMultList2.append(finalMult2)
      final2CombMults = HDWalletCrypto().getChildKeyFromOps_SWIG(
                                                          sbdPubKey2.toBinStr(),
                                                                 finalMultList2)
      self.assertEqual(finalPub2, final2CombMults)

if __name__ == "__main__":
   unittest.main()
