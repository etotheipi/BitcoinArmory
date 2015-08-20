
import sys
sys.path.append('..')
import unittest

from CppBlockUtils import HDWalletCrypto
from armoryengine.ArmoryUtils import *
from armoryengine.BinaryPacker import *
from armoryengine.ConstructedScript import *

############# Various constants we wish to use throughout the tests.
# Master key derived from the 2nd BIP32 test vector + child key 0.
strBIP32MasterPubKey2        = \
   "04 cbcaa9c9 8c877a26 977d0082 5c956a23 8e8dddfb d322cce4 f74b0b5b d6ace4a7" \
   "   7bd3305d 363c26f8 2c1e41c6 67e4b356 1c06c60a 2104d2b5 48e6dd05 9056aa51"
BIP32MasterPubKey2        = hex_to_binary(strBIP32MasterPubKey2)
strBIP32MasterPubKey2Comp    = \
   "03 cbcaa9c9 8c877a26 977d0082 5c956a23 8e8dddfb d322cce4 f74b0b5b d6ace4a7"
BIP32MasterPubKey2Comp    = hex_to_binary(strBIP32MasterPubKey2Comp)
strBIP32MasterPubKey2_D1     = \
   "04 fc9e5af0 ac8d9b3c ecfe2a88 8e2117ba 3d089d85 85886c9c 826b6b22 a98d12ea" \
   "   67a50538 b6f7d8b5 f7a1cc65 7efd267c de8cc1d8 c0451d13 40a0fb36 42777544"
BIP32MasterPubKey2_D1     = hex_to_binary(strBIP32MasterPubKey2_D1)
strBIP32MasterPubKey2Comp_D1 = \
   "02 fc9e5af0 ac8d9b3c ecfe2a88 8e2117ba 3d089d85 85886c9c 826b6b22 a98d12ea"
BIP32MasterPubKey2Comp_D1 = hex_to_binary(strBIP32MasterPubKey2Comp_D1)
strBIP32MasterChainCode2     = \
   "   60499f80 1b896d83 179a4374 aeb7822a aeaceaa0 db1f85ee 3e904c4d efbd9689"
BIP32MasterChainCode2     = hex_to_binary(strBIP32MasterChainCode2)

# Data related to BIP32MasterPubKey2.
strBIP32MasterPubKey2Multiplier = \
      "60e3739c c2c3950b 7c4d7f32 cc503e13 b996d0f7 a45623d0 a914e1ef a7f811e0"
BIP32MasterPubKey2Multiplier = hex_to_binary(strBIP32MasterPubKey2Multiplier)
strBIP32MasterPubKey2_D1Hash160 = \
      "5a61ff8e b7aaca30 10db97eb da761216 10b78096"
BIP32MasterPubKey2_D1Hash160 = hex_to_binary(strBIP32MasterPubKey2_D1Hash160)

# Valid PKS serializations based on BIP32MasterPubKey2.
strPKS1Chksum_Uncomp_v1 = \
      "01002041" + strBIP32MasterPubKey2 + "1ff749e6"
PKS1Chksum_Uncomp_v1 = hex_to_binary(strPKS1Chksum_Uncomp_v1)
strPKS1NoChksum_Comp_v1 = \
      "01000221" + strBIP32MasterPubKey2Comp
PKS1NoChksum_Comp_v1 = hex_to_binary(strPKS1NoChksum_Comp_v1)

# Invalid PKS serializations based on BIP32MasterPubKey2.
strPKS1NoChksum_Comp_v1_FlagClash1 = \
      "01000921" + strBIP32MasterPubKey2Comp
PKS1NoChksum_Comp_v1_FlagClash1 = hex_to_binary(strPKS1NoChksum_Comp_v1_FlagClash1)
strPKS1NoChksum_Comp_v1_FlagClash2 = \
      "01001821" + strBIP32MasterPubKey2Comp
PKS1NoChksum_Comp_v1_FlagClash2 = hex_to_binary(strPKS1NoChksum_Comp_v1_FlagClash2)

########## ADD PKS RECORDS THAT DO NOT ALLOW FOR DIRECT PAYMENT ############

# Valid CS serializations based on BIP32MasterPubKey2.
strCS1Chksum_Uncomp_v1 = \
      "01000207 76a914ff 0188ac01 45010004 41" + strBIP32MasterPubKey2 + \
      "86883438"
CS1Chksum_Uncomp_v1 = hex_to_binary(strCS1Chksum_Uncomp_v1)
strCS1Chksum_Comp_v1 = \
      "01000207 76a914ff 0188ac01 25010006 21" + \
      strBIP32MasterPubKey2Comp + "f823 227a"
CS1Chksum_Comp_v1 = hex_to_binary(strCS1Chksum_Comp_v1)
strCS1NoChksum_Comp_v1 = \
      "01000007 76a914ff 0188ac01 25010006 21" + strBIP32MasterPubKey2Comp
CS1NoChksum_Comp_v1 = hex_to_binary(strCS1NoChksum_Comp_v1)
strCS2Chksum_Comp_v1 = \
      "01000305 52ff0252 ae022501 000221" + strBIP32MasterPubKey2Comp + \
      "25010002 21" + strBIP32MasterPubKey2Comp_D1 + "89e25fe9"
CS2Chksum_Comp_v1 = hex_to_binary(strCS2Chksum_Comp_v1) # Multisig

################# Invalid CS serializations. NEED TO ADD SOME. ############

############ RI serializations. NEED TO ADD SOME. ###################
# Valid RI serializations based on previously created records.
Valid_RI_PKS_Base = "0100"
#RI_

# Valid PKRP serializations based on BIP32MasterPubKey2.
strPKRPMult = \
      "60e3739c c2c3950b 7c4d7f32 cc503e13 b996d0f7 a45623d0 a914e1ef a7f811e0"
strPKRP1_v1 = \
      "010220" + strPKRPMult + "00"
PKRP1_v1 = hex_to_binary(strPKRP1_v1)

# Invalid PKRP serializations based on BIP32MasterPubKey2.
strPKRP1_v1_FlagClash1 = \
      "010020" + strPKRPMult + "00"
PKRP1_v1_FlagClash1 = hex_to_binary(strPKRP1_v1_FlagClash1)

# Valid SRP serializations based on BIP32MasterPubKey2.
strSRP1_v1 = \
      "010124" + strPKRP1_v1
SRP1_v1 = hex_to_binary(strSRP1_v1)
strSRP2_v1 = \
      "010224" + strPKRP1_v1 + "24" + strPKRP1_v1
SRP2_v1 = hex_to_binary(strSRP2_v1)

############# Valid PTV serializations. NEED TO ADD SOME #####################

# Valid PR serializations based on BIP32MasterPubKey2.
daneName1    = "pksrec1.btcshop.com"
daneName1Hex = "706b7372 6563312e 62746373 686f702e 636f6d"
daneName2    = "pksrec2.btcshop.com"
daneName2Hex = "706b7372 6563322e 62746373 686f702e 636f6d"
strUnvalidatedScript1 = \
      "76a9145a 61ff8eb7 aaca3010 db97ebda 76121610 b7809688 ac"
unvalidatedScript1 = hex_to_binary(strUnvalidatedScript1)

# REMINDER: ADD A BAD UNVALIDATED SCRIPT BY REMOVING 0x14 FROM THE SCRIPT ABOVE. USE TO CREATE TESTS THAT CHECK SCRIPTS
strPR1_v1 = \
      "01000001 5619" + strUnvalidatedScript1 +    "13" + daneName1Hex + \
      "27" + strSRP1_v1
PR1_v1 = hex_to_binary(strPR1_v1)
strPR2_v1 = \
      "01000002 ac19" + strUnvalidatedScript1 +    "19" + \
      strUnvalidatedScript1 +    "13" + daneName1Hex +      "13" + \
      daneName1Hex +    "27" + strSRP1_v1 +        "27" + strSRP1_v1
PR2_v1 = hex_to_binary(strPR2_v1)

# Valid PMTA serializations including previously used, valid PKS and CS records.
####################### NEED TO REVISE AS IS APPROPRIATE. ######################
strPMTA_PKS1Chksum_Uncomp_v1 = \
      "00010000 00000001 00204104 cbcaa9c9 8c877a26 977d0082 5c956a23 8e8dddfb" \
      "d322cce4 f74b0b5b d6ace4a7 7bd3305d 363c26f8 2c1e41c6 67e4b356 1c06c60a" \
      "2104d2b5 48e6dd05 9056aa51 1ff749e6"
PMTA_PKS1Chksum_Uncomp_v1 = hex_to_binary(strPMTA_PKS1Chksum_Uncomp_v1)
strPMTA_PKS1NoChksum_Comp_v1 = \
      "0002ffff 002e6874 7470733a 2f2f7777 772e6269 74636f69 6e61726d 6f72792e" \
      "636f6d2f 7061796d 656e745f 696e666f 2e747874 00010002 2103cbca a9c98c87" \
      "7a26977d 00825c95 6a238e8d ddfbd322 cce4f74b 0b5bd6ac e4a7"
PMTA_PKS1NoChksum_Comp_v1 = hex_to_binary(strPMTA_PKS1NoChksum_Comp_v1)
strPMTA_CS1Chksum_Comp_v1 = \
      "0001abba 002e6874 7470733a 2f2f7777 772e6269 74636f69 6e61726d 6f72792e" \
      "636f6d2f 7061796d 656e745f 696e666f 2e747874 00010002 0776a914 ff0188ac" \
      "01250100 062103cb caa9c98c 877a2697 7d00825c 956a238e 8dddfbd3 22cce4f7" \
      "4b0b5bd6 ace4a7f8 23227a"
PMTA_CS1Chksum_Comp_v1 = hex_to_binary(strPMTA_CS1Chksum_Comp_v1)
strPMTA_CS1NoChksum_Comp_v1 = \
      "00020002 00000001 00000776 a914ff01 88ac0125 01000621 03cbcaa9 c98c877a" \
      "26977d00 825c956a 238e8ddd fbd322cc e4f74b0b 5bd6ace4 a7"
PMTA_CS1NoChksum_Comp_v1 = hex_to_binary(strPMTA_CS1NoChksum_Comp_v1)

# Inalid PMTA serializations.
strPMTA_BadPayNet = \
      "0200000d 00000001 00000676 a914ff01 88ac0125 01000621 03cbcaa9 c98c877a" \
      "26977d00 825c956a 238e8ddd fbd322cc e4f74b0b 5bd6ace4a7"
PMTA_BadPayNet = hex_to_binary(strPMTA_BadPayNet)
strPMTA_BadDataType = \
      "00010000 00000101 00000676 a914ff01 88ac0125 01000621 03cbcaa9 c98c877a" \
      "26977d00 825c956a 238e8ddd fbd322cc e4f74b0b 5bd6ace4 a7"
PMTA_BadDataType = hex_to_binary(strPMTA_BadDataType)
strPMTA_BadURILen1 = \
      "0002ffff 00006874 7470733a 2f2f7777 772e6269 74636f69 6e61726d 6f72792e" \
      "636f6d2f 7061796d 656e745f 696e666f 2e747874 00010002 2103cbca a9c98c87" \
      "7a26977d 00825c95 6a238e8d ddfbd322 cce4f74b 0b5bd6ac e4a7"
PMTA_BadURILen1 = hex_to_binary(strPMTA_BadURILen1)
strPMTA_BadURILen2 = \
      "0002ffff 002d6874 7470733a 2f2f7777 772e6269 74636f69 6e61726d 6f72792e" \
      "636f6d2f 7061796d 656e745f 696e666f 2e747874 00010002 2103cbca a9c98c87" \
      "7a26977d 00825c95 6a238e8d ddfbd322 cce4f74b 0b5bd6ac e4a7"
PMTA_BadURILen2 = hex_to_binary(strPMTA_BadURILen2)
PMTA_BadURILen3 = \
      "0002ffff 002f6874 7470733a 2f2f7777 772e6269 74636f69 6e61726d 6f72792e" \
      "636f6d2f 7061796d 656e745f 696e666f 2e747874 00010002 2103cbca a9c98c87" \
      "7a26977d 00825c95 6a238e8d ddfbd322 cce4f74b 0b5bd6ac e4a7"
PMTA_BadURILen3 = hex_to_binary(PMTA_BadURILen3)
strPMTA_PKS1NoChksum_Comp_v1_FlagClash1 = \
      "00010000 00000001 00092103 cbcaa9c9 8c877a26 977d0082 5c956a23 8e8dddfb" \
      "d322cce4 f74b0b5b d6ace4a7"
PMTA_PKS1NoChksum_Comp_v1_FlagClash1 = hex_to_binary(strPMTA_PKS1NoChksum_Comp_v1_FlagClash1)

### TODO: Place this stuff where it belongs when it's time!
# TxOutscript validator. From ArmoryUtils.py:512?
# getTxOutScriptType(binScript)


################################################################################
class PKSClassTests(unittest.TestCase):
   # Use serialize/unserialize to confirm that the data struct is correctly
   # formed and can be correctly formed.
   def testSerialization(self):
      # PKS1 with a checksum & uncompressed key.
      pks1ChksumPres = PublicKeySource(False, False, False, False, False,
                                       BIP32MasterPubKey2, True, False)
      stringPKS1ChksumPres = pks1ChksumPres.serialize()
      self.assertEqual(binary_to_hex(stringPKS1ChksumPres),
                       binary_to_hex(PKS1Chksum_Uncomp_v1))

      # PKS1 without a checksum & with a compressed key.
      pks1NoChksum = PublicKeySource(False, True, False, False, False,
                                     BIP32MasterPubKey2Comp, False, False)
      stringPKS1NoChksum = pks1NoChksum.serialize()
      self.assertEqual(binary_to_hex(stringPKS1NoChksum),
                       binary_to_hex(PKS1NoChksum_Comp_v1))

      # Unserialize and re-serialize to confirm unserialize works.
      pks1ChksumPres_unser = decodePublicKeySource(PKS1Chksum_Uncomp_v1)
      pks1NoChksum_unser = decodePublicKeySource(PKS1NoChksum_Comp_v1)
      stringPKS1Chksum_unser = pks1ChksumPres_unser.serialize()
      stringPKS1NoChksum_unser = pks1NoChksum_unser.serialize()
      self.assertEqual(binary_to_hex(stringPKS1Chksum_unser),
                       binary_to_hex(PKS1Chksum_Uncomp_v1))
      self.assertEqual(binary_to_hex(stringPKS1NoChksum_unser),
                       binary_to_hex(PKS1NoChksum_Comp_v1))

      # Are various PKS structures valid?
      # (NB: Bad checksum and version tests are slight hacks because the
      # unserialize code correctly fails. Direct editing works best.)
      pks1BadChksum = decodePublicKeySource(PKS1Chksum_Uncomp_v1)
      pks1BadChksum.checksum = b'\xde\xad\xbe\xef'
      pks1BadVer = decodePublicKeySource(PKS1Chksum_Uncomp_v1)
      pks1BadVer.version = 100
      pks1BadFlag1  = decodePublicKeySource(PKS1NoChksum_Comp_v1_FlagClash1)
      pks1BadFlag2  = decodePublicKeySource(PKS1NoChksum_Comp_v1_FlagClash2)
      pksIsValid = pks1ChksumPres.isValid(False)
      self.assertEqual(pksIsValid, True)
      pksIsValid = pks1NoChksum.isValid(False)
      self.assertEqual(pksIsValid, True)
      pksIsValid = pks1BadChksum.isValid(False)
      self.assertEqual(pksIsValid, False)
      pksIsValid = pks1BadVer.isValid(False)
      self.assertEqual(pksIsValid, False)
      pksIsValid = pks1BadFlag1.isValid(False)
      self.assertEqual(pksIsValid, False)
      pksIsValid = pks1BadFlag2.isValid(False)
      self.assertEqual(pksIsValid, False)


################################################################################
class CSClassTests(unittest.TestCase):
   # Use serialize/unserialize to confirm that the data struct is correctly
   # formed and can be correctly formed.
   def testSerialization(self):
      # CS1 w/ a checksum - Pre-built P2PKH
      cs1ChksumPres = StandardP2PKHConstructed(BIP32MasterPubKey2)
      stringCS1ChksumPres = cs1ChksumPres.serialize()
      self.assertEqual(binary_to_hex(stringCS1ChksumPres),
                       binary_to_hex(CS1Chksum_Uncomp_v1))

      # CS2 w/ a checksum - Pre-built multisig
      testKeyList = [BIP32MasterPubKey2Comp, BIP32MasterPubKey2Comp_D1]
      cs2ChksumPres = StandardMultisigConstructed(2, testKeyList)
      stringCS2ChksumPres = cs2ChksumPres.serialize()
      self.assertEqual(binary_to_hex(stringCS2ChksumPres),
                       binary_to_hex(CS2Chksum_Comp_v1))

      # Unserialize and re-serialize to confirm unserialize works.
      cs1ChksumPres_unser = decodeConstructedScript(CS1Chksum_Uncomp_v1)
      cs2ChksumPres_unser = decodeConstructedScript(CS2Chksum_Comp_v1)
      stringCS1Chksum_unser = cs1ChksumPres_unser.serialize()
      stringCS2Chksum_unser = cs2ChksumPres_unser.serialize()
      self.assertEqual(binary_to_hex(stringCS1Chksum_unser),
                       binary_to_hex(CS1Chksum_Uncomp_v1))
      self.assertEqual(binary_to_hex(stringCS2Chksum_unser),
                       binary_to_hex(CS2Chksum_Comp_v1))

      # Are various CS structures valid?
      # (NB: Bad checksum and version tests are slight hacks because the
      # unserialize code correctly fails. Direct editing works best.)
      cs1NoChksum_Comp   = decodeConstructedScript(CS1NoChksum_Comp_v1)
      cs1BadChksum_Uncomp = decodeConstructedScript(CS1Chksum_Uncomp_v1)
      cs1BadChksum_Uncomp.checksum = b'\xde\xad\xbe\xef'
      cs1BadChksum_Comp   = decodeConstructedScript(CS1Chksum_Comp_v1)
      cs1BadChksum_Comp.checksum = b'\xde\xad\xbe\xef'
      cs1BadVer           = decodeConstructedScript(CS1Chksum_Comp_v1)
      cs1BadVer.version   = 255
      csIsValid = cs1ChksumPres.isValid(False)
      self.assertEqual(csIsValid, True)
      csIsValid = cs2ChksumPres.isValid(False)
      self.assertEqual(csIsValid, True)
      csIsValid = cs1NoChksum_Comp.isValid(False)
      self.assertEqual(csIsValid, True)
      csIsValid = cs1BadChksum_Uncomp.isValid(False)
      self.assertEqual(csIsValid, False)
      csIsValid = cs1BadChksum_Comp.isValid(False)
      self.assertEqual(csIsValid, False)
      csIsValid = cs1BadVer.isValid(False)
      self.assertEqual(csIsValid, False)


################################################################################
class PKRPClassTests(unittest.TestCase):
   # Use serialize/unserialize to confirm that the data struct is correctly
   # formed and can be correctly formed.
   def testSerialization(self):
      # 1 multiplier.
      pkrp1 = PublicKeyRelationshipProof(BIP32MasterPubKey2Multiplier)
      stringPKRP1 = pkrp1.serialize()
      self.assertEqual(binary_to_hex(stringPKRP1),
                       binary_to_hex(PKRP1_v1))

      # Unserialize and re-serialize to confirm unserialize works.
      pkrp1_unser = decodePublicKeyRelationshipProof(PKRP1_v1)
      stringPKRP1_unser = pkrp1_unser.serialize()
      self.assertEqual(binary_to_hex(stringPKRP1_unser),
                       binary_to_hex(PKRP1_v1))

      # Are various PKRP structures valid?
      # (NB: Bad version test is a slight hacks because the unserialize code
      # correctly fails. Direct editing works best.)
      pkrp1_BadVersion = decodePublicKeyRelationshipProof(PKRP1_v1)
      pkrp1_BadVersion.version = 13
      pkrp1_FlagClash1 = decodePublicKeyRelationshipProof(PKRP1_v1_FlagClash1)
      pkrpIsValid = pkrp1.isValid()
      self.assertEqual(pkrpIsValid, True)
      pkrpIsValid = pkrp1_BadVersion.isValid()
      self.assertEqual(pkrpIsValid, False)
      pkrpIsValid = pkrp1_FlagClash1.isValid()
      self.assertEqual(pkrpIsValid, False)


################################################################################
class SRPClassTests(unittest.TestCase):
   # Use serialize/unserialize to confirm that the data struct is correctly
   # formed and can be correctly formed.
   def testSerialization(self):
      # 1 PKRP.
      pkrp1 = PublicKeyRelationshipProof(BIP32MasterPubKey2Multiplier)
      srp1 = ScriptRelationshipProof([pkrp1])
      stringSRP1 = srp1.serialize()
      self.assertEqual(binary_to_hex(stringSRP1),
                       binary_to_hex(SRP1_v1))

      # 2 PKRPs. Both PKRPs are the same. This test just confirms that the
      # serialization code works for multiple PKRPs.
      srp2 = ScriptRelationshipProof([pkrp1, pkrp1])
      stringSRP2 = srp2.serialize()
      self.assertEqual(binary_to_hex(stringSRP2),
                       binary_to_hex(SRP2_v1))

      # Unserialize and re-serialize to confirm unserialize works.
      srp1_unser = decodeScriptRelationshipProof(SRP1_v1)
      srp2_unser = decodeScriptRelationshipProof(SRP2_v1)
      stringSRP1_unser = srp1_unser.serialize()
      stringSRP2_unser = srp2_unser.serialize()
      self.assertEqual(binary_to_hex(stringSRP1_unser),
                       binary_to_hex(SRP1_v1))
      self.assertEqual(binary_to_hex(stringSRP2_unser),
                       binary_to_hex(SRP2_v1))

      # Are various SRP structures valid?
      # (NB: Bad version test is a slight hack because the unserialize code
      # correctly fails. Direct editing works best.)
      srp1_BadVersion = decodeScriptRelationshipProof(SRP1_v1)
      srp1_BadVersion.version = 16
      srpIsValid = srp1.isValid()
      self.assertEqual(srpIsValid, True)
      srpIsValid = srp2.isValid()
      self.assertEqual(srpIsValid, True)
      srpIsValid = srp1_BadVersion.isValid()
      self.assertEqual(srpIsValid, False)


################################################################################
class PRClassTests(unittest.TestCase):
   # Use serialize/unserialize to confirm that the data struct is correctly
   # formed and can be correctly formed.
   def testSerialization(self):
      pkrp1 = PublicKeyRelationshipProof(BIP32MasterPubKey2Multiplier)
      srp1 = ScriptRelationshipProof([pkrp1])

      # 1 TxOut script.
      pr1 = PaymentRequest([unvalidatedScript1], [daneName1],
                           [srp1.serialize()])
      stringPR1 = pr1.serialize()
      self.assertEqual(binary_to_hex(stringPR1),
                       binary_to_hex(PR1_v1))

      # 2 TxOut scripts. Both scripts are the same. This test just confirms that
      # the serialization code works for multiple TxOut scripts.
      pr2 = PaymentRequest([unvalidatedScript1, unvalidatedScript1],
                           [daneName1, daneName1],
                           [srp1.serialize(), srp1.serialize()])
      stringPR2 = pr2.serialize()
      self.assertEqual(binary_to_hex(stringPR2),
                       binary_to_hex(PR2_v1))

      # Unserialize and re-serialize to confirm unserialize works.
      pr1_unser = decodePaymentRequest(PR1_v1)
      pr2_unser = decodePaymentRequest(PR2_v1)
      stringPR1_ser = pr1_unser.serialize()
      stringPR2_ser = pr2_unser.serialize()
      self.assertEqual(binary_to_hex(stringPR1_ser),
                       binary_to_hex(PR1_v1))
      self.assertEqual(binary_to_hex(stringPR2_ser),
                       binary_to_hex(PR2_v1))

      # Are various PR structures valid?
      # (NB: Bad version test is a slight hacks because the unserialize code
      # correctly fails. Direct editing works best.)
      pr1_BadVersion = decodePaymentRequest(PR1_v1)
      pr1_BadVersion.version = 160
      prIsValid = pr1.isValid()
      self.assertEqual(prIsValid, True)
      prIsValid = pr2.isValid()
      self.assertEqual(prIsValid, True)
      prIsValid = pr1_BadVersion.isValid()
      self.assertEqual(prIsValid, False)


################################################################################
########## TO BE COMPLETED
class PMTAClassTests(unittest.TestCase):
   # Use serialize/unserialize to confirm that the data struct is correctly
   # formed and can be correctly formed.
   def testSerialization(self):
      # Create PMTA with a checksummed PKS.
      pks1ChksumPres = decodePublicKeySource(PKS1Chksum_Uncomp_v1)
      pmta1 = PMTARecord(pks1ChksumPres.serialize(), PAYNET_TBTC, 0, '')
      stringPMTA1 = pmta1.serialize()
      self.assertEqual(binary_to_hex(stringPMTA1),
                       binary_to_hex(PMTA_PKS1Chksum_Uncomp_v1))

      # Create PMTA with a non-checksummed PKS.
      pks1NoChksumPres = decodePublicKeySource(PKS1NoChksum_Comp_v1)
      pmta2 = PMTARecord(pks1NoChksumPres.serialize(), PAYNET_BTC, 65535,
                       'https://www.bitcoinarmory.com/payment_info.txt')
      stringPMTA2 = pmta2.serialize()
      self.assertEqual(binary_to_hex(stringPMTA2),
                       binary_to_hex(PMTA_PKS1NoChksum_Comp_v1))

      # Create PMTA with a checksummed CS.
      cs1ChksumPres = decodeConstructedScript(CS1Chksum_Comp_v1)
      pmta3 = PMTARecord(cs1ChksumPres.serialize(), PAYNET_TBTC, 43962,
                       'https://www.bitcoinarmory.com/payment_info.txt')
      stringPMTA3 = pmta3.serialize()
      self.assertEqual(binary_to_hex(stringPMTA3),
                       binary_to_hex(PMTA_CS1Chksum_Comp_v1))

      # Create PMTA with a non-checksummed CS.
      cs1NoChksumPres = decodeConstructedScript(CS1NoChksum_Comp_v1)
      pmta4 = PMTARecord(cs1NoChksumPres.serialize(), PAYNET_BTC, 2, '')
      stringPMTA4 = pmta4.serialize()
      self.assertEqual(binary_to_hex(stringPMTA4),
                       binary_to_hex(PMTA_CS1NoChksum_Comp_v1))

      # Unserialize and re-serialize to confirm unserialize works.
      pmta1_unser = decodePMTARecord(PMTA_PKS1Chksum_Uncomp_v1)
      pmta2_unser = decodePMTARecord(PMTA_PKS1NoChksum_Comp_v1)
      pmta3_unser = decodePMTARecord(PMTA_CS1Chksum_Comp_v1)
      pmta4_unser = decodePMTARecord(PMTA_CS1NoChksum_Comp_v1)
      stringPMTA1_unser = pmta1_unser.serialize()
      stringPMTA2_unser = pmta2_unser.serialize()
      stringPMTA3_unser = pmta3_unser.serialize()
      stringPMTA4_unser = pmta4_unser.serialize()
      self.assertEqual(binary_to_hex(stringPMTA1_unser),
                       binary_to_hex(PMTA_PKS1Chksum_Uncomp_v1))
      self.assertEqual(binary_to_hex(stringPMTA2_unser),
                       binary_to_hex(PMTA_PKS1NoChksum_Comp_v1))
      self.assertEqual(binary_to_hex(stringPMTA3_unser),
                       binary_to_hex(PMTA_CS1Chksum_Comp_v1))
      self.assertEqual(binary_to_hex(stringPMTA4_unser),
                       binary_to_hex(PMTA_CS1NoChksum_Comp_v1))

      # Check PMTA validity.
      pmtaIsValid = pmta1_unser.isValid()
      self.assertEqual(pmtaIsValid, True)
      pmtaIsValid = pmta2_unser.isValid()
      self.assertEqual(pmtaIsValid, True)
      pmtaIsValid = pmta3_unser.isValid()
      self.assertEqual(pmtaIsValid, True)
      pmtaIsValid = pmta4_unser.isValid()
      self.assertEqual(pmtaIsValid, True)
      badPMTA1 = decodePMTARecord(PMTA_BadPayNet)
      self.assertEqual(badPMTA1, None)
      badPMTA2 = decodePMTARecord(PMTA_BadDataType)
      self.assertEqual(badPMTA2, None)
      badPMTA3 = decodePMTARecord(PMTA_BadURILen1)
      self.assertEqual(badPMTA3, None)
      badPMTA4 = decodePMTARecord(PMTA_BadURILen2)
      self.assertEqual(badPMTA4, None)
      badPMTA5 = decodePMTARecord(PMTA_BadURILen3)
      self.assertEqual(badPMTA5, None)
      badPMTA6 = decodePMTARecord(PMTA_PKS1NoChksum_Comp_v1_FlagClash1)
      self.assertEqual(badPMTA6, None)


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

      # Confirm that we can apply the multiplier directly and get the correct
      # final key.
      final1ApplyMult = HDWalletCrypto().getChildKeyFromMult_SWIG(
                                                          sbdPubKey1.toBinStr(),
                                                          multProof1.multiplier)
      self.assertEqual(finalPub1, final1ApplyMult)

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
