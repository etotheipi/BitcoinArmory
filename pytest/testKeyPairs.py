################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

import sys
sys.path.append('..')
import unittest
import sys
sys.path.append('..')
import textwrap

from armoryengine.ArmoryUtils import *
from armoryengine.ArmoryEncryption import *
from armoryengine.WalletEntry import *
from armoryengine.ArmoryKeyPair import *

WALLET_VERSION_BIN = hex_to_binary('002d3101')

# This disables RSEC for all WalletEntry objects.  This causes it to stop
# checking RSEC codes on all entries, and writes all \x00 bytes when creating.
WalletEntry.DisableRSEC()


MSO_FILECODE   = 'MOCKOBJ_'
MSO_ENTRY_ID   = '\x01'+'\x33'*20
MSO_FLAGS_REG  = '\x00\x00'
MSO_FLAGS_DEL  = '\x80\x00'
MSO_PARSCRADDR = '\x05'+'\x11'*20
MSO_PAYLOAD    = '\xaf'*5

FAKE_KDF_ID  = '\x42'*8
FAKE_EKEY_ID = '\x9e'*8



BIP32TestVectors = []

# 0
BIP32TestVectors.append( \
   {
      'seedKey': SecureBinaryData(hex_to_binary("00e8f32e723decf4051aefac8e2c93c9c5b214313817cdb01a1494b917c8436b35")),
      'seedCC': SecureBinaryData(hex_to_binary("873dff81c02f525623fd1fe5167eac3a55a049de3d314bb42ee227ffed37d508")),
      'seedPubKey': SecureBinaryData(hex_to_binary("0439a36013301597daef41fbe593a02cc513d0b55527ec2df1050e2e8ff49c85c23cbe7ded0e7ce6a594896b8f62888fdbc5c8821305e2ea42bf01e37300116281")),
      'seedCompPubKey': SecureBinaryData(hex_to_binary("0339a36013301597daef41fbe593a02cc513d0b55527ec2df1050e2e8ff49c85c2")),
      'seedExtSerPrv': SecureBinaryData(hex_to_binary("0488ade4000000000000000000873dff81c02f525623fd1fe5167eac3a55a049de3d314bb42ee227ffed37d50800e8f32e723decf4051aefac8e2c93c9c5b214313817cdb01a1494b917c8436b35")),
      'seedExtSerPub': SecureBinaryData(hex_to_binary("0488b21e000000000000000000873dff81c02f525623fd1fe5167eac3a55a049de3d314bb42ee227ffed37d5080339a36013301597daef41fbe593a02cc513d0b55527ec2df1050e2e8ff49c85c2")),
      'seedID': SecureBinaryData(hex_to_binary("3442193e1bb70916e914552172cd4e2dbc9df811")),
      'seedFP': SecureBinaryData(hex_to_binary("3442193e")),
      'seedParFP': SecureBinaryData(hex_to_binary("00000000")),
      'nextChild': 2147483648 
   })

# 1
BIP32TestVectors.append( \
   {
      'seedKey': SecureBinaryData(hex_to_binary("00edb2e14f9ee77d26dd93b4ecede8d16ed408ce149b6cd80b0715a2d911a0afea")),
      'seedCC': SecureBinaryData(hex_to_binary("47fdacbd0f1097043b78c63c20c34ef4ed9a111d980047ad16282c7ae6236141")),
      'seedPubKey': SecureBinaryData(hex_to_binary("045a784662a4a20a65bf6aab9ae98a6c068a81c52e4b032c0fb5400c706cfccc567f717885be239daadce76b568958305183ad616ff74ed4dc219a74c26d35f839")),
      'seedCompPubKey': SecureBinaryData(hex_to_binary("035a784662a4a20a65bf6aab9ae98a6c068a81c52e4b032c0fb5400c706cfccc56")),
      'seedExtSerPrv': SecureBinaryData(hex_to_binary("0488ade4013442193e8000000047fdacbd0f1097043b78c63c20c34ef4ed9a111d980047ad16282c7ae623614100edb2e14f9ee77d26dd93b4ecede8d16ed408ce149b6cd80b0715a2d911a0afea")),
      'seedExtSerPub': SecureBinaryData(hex_to_binary("0488b21e013442193e8000000047fdacbd0f1097043b78c63c20c34ef4ed9a111d980047ad16282c7ae6236141035a784662a4a20a65bf6aab9ae98a6c068a81c52e4b032c0fb5400c706cfccc56")),
      'seedID': SecureBinaryData(hex_to_binary("5c1bd648ed23aa5fd50ba52b2457c11e9e80a6a7")),
      'seedFP': SecureBinaryData(hex_to_binary("5c1bd648")),
      'seedParFP': SecureBinaryData(hex_to_binary("3442193e")),
      'nextChild': 1
   })

# 2
BIP32TestVectors.append( \
   {
      'seedKey': SecureBinaryData(hex_to_binary("003c6cb8d0f6a264c91ea8b5030fadaa8e538b020f0a387421a12de9319dc93368")),
      'seedCC': SecureBinaryData(hex_to_binary("2a7857631386ba23dacac34180dd1983734e444fdbf774041578e9b6adb37c19")),
      'seedPubKey': SecureBinaryData(hex_to_binary("04501e454bf00751f24b1b489aa925215d66af2234e3891c3b21a52bedb3cd711c008794c1df8131b9ad1e1359965b3f3ee2feef0866be693729772be14be881ab")),
      'seedCompPubKey': SecureBinaryData(hex_to_binary("03501e454bf00751f24b1b489aa925215d66af2234e3891c3b21a52bedb3cd711c")),
      'seedExtSerPrv': SecureBinaryData(hex_to_binary("0488ade4025c1bd648000000012a7857631386ba23dacac34180dd1983734e444fdbf774041578e9b6adb37c19003c6cb8d0f6a264c91ea8b5030fadaa8e538b020f0a387421a12de9319dc93368")),
      'seedExtSerPub': SecureBinaryData(hex_to_binary("0488b21e025c1bd648000000012a7857631386ba23dacac34180dd1983734e444fdbf774041578e9b6adb37c1903501e454bf00751f24b1b489aa925215d66af2234e3891c3b21a52bedb3cd711c")),
      'seedID': SecureBinaryData(hex_to_binary("bef5a2f9a56a94aab12459f72ad9cf8cf19c7bbe")),
      'seedFP': SecureBinaryData(hex_to_binary("bef5a2f9")),
      'seedParFP': SecureBinaryData(hex_to_binary("5c1bd648")),
      'nextChild': 2147483650
   })

# 3
BIP32TestVectors.append( \
   {
      'seedKey': SecureBinaryData(hex_to_binary("00cbce0d719ecf7431d88e6a89fa1483e02e35092af60c042b1df2ff59fa424dca")),
      'seedCC': SecureBinaryData(hex_to_binary("04466b9cc8e161e966409ca52986c584f07e9dc81f735db683c3ff6ec7b1503f")),
      'seedPubKey': SecureBinaryData(hex_to_binary("0457bfe1e341d01c69fe5654309956cbea516822fba8a601743a012a7896ee8dc24310ef3676384179e713be3115e93f34ac9a3933f6367aeb3081527ea74027b7")),
      'seedCompPubKey': SecureBinaryData(hex_to_binary("0357bfe1e341d01c69fe5654309956cbea516822fba8a601743a012a7896ee8dc2")),
      'seedExtSerPrv': SecureBinaryData(hex_to_binary("0488ade403bef5a2f98000000204466b9cc8e161e966409ca52986c584f07e9dc81f735db683c3ff6ec7b1503f00cbce0d719ecf7431d88e6a89fa1483e02e35092af60c042b1df2ff59fa424dca")),
      'seedExtSerPub': SecureBinaryData(hex_to_binary("0488b21e03bef5a2f98000000204466b9cc8e161e966409ca52986c584f07e9dc81f735db683c3ff6ec7b1503f0357bfe1e341d01c69fe5654309956cbea516822fba8a601743a012a7896ee8dc2")),
      'seedID': SecureBinaryData(hex_to_binary("ee7ab90cde56a8c0e2bb086ac49748b8db9dce72")),
      'seedFP': SecureBinaryData(hex_to_binary("ee7ab90c")),
      'seedParFP': SecureBinaryData(hex_to_binary("bef5a2f9")),
      'nextChild': 2
   })

# 4
BIP32TestVectors.append( \
   {
      'seedKey': SecureBinaryData(hex_to_binary("000f479245fb19a38a1954c5c7c0ebab2f9bdfd96a17563ef28a6a4b1a2a764ef4")),
      'seedCC': SecureBinaryData(hex_to_binary("cfb71883f01676f587d023cc53a35bc7f88f724b1f8c2892ac1275ac822a3edd")),
      'seedPubKey': SecureBinaryData(hex_to_binary("04e8445082a72f29b75ca48748a914df60622a609cacfce8ed0e35804560741d292728ad8d58a140050c1016e21f285636a580f4d2711b7fac3957a594ddf416a0")),
      'seedCompPubKey': SecureBinaryData(hex_to_binary("02e8445082a72f29b75ca48748a914df60622a609cacfce8ed0e35804560741d29")),
      'seedExtSerPrv': SecureBinaryData(hex_to_binary("0488ade404ee7ab90c00000002cfb71883f01676f587d023cc53a35bc7f88f724b1f8c2892ac1275ac822a3edd000f479245fb19a38a1954c5c7c0ebab2f9bdfd96a17563ef28a6a4b1a2a764ef4")),
      'seedExtSerPub': SecureBinaryData(hex_to_binary("0488b21e04ee7ab90c00000002cfb71883f01676f587d023cc53a35bc7f88f724b1f8c2892ac1275ac822a3edd02e8445082a72f29b75ca48748a914df60622a609cacfce8ed0e35804560741d29")),
      'seedID': SecureBinaryData(hex_to_binary("d880d7d893848509a62d8fb74e32148dac68412f")),
      'seedFP': SecureBinaryData(hex_to_binary("d880d7d8")),
      'seedParFP': SecureBinaryData(hex_to_binary("ee7ab90c")),
      'nextChild': 1000000000
   })

# 5
BIP32TestVectors.append( \
   {
      'seedKey': SecureBinaryData(hex_to_binary("00471b76e389e528d6de6d816857e012c5455051cad6660850e58372a6c3e6e7c8")),
      'seedCC': SecureBinaryData(hex_to_binary("c783e67b921d2beb8f6b389cc646d7263b4145701dadd2161548a8b078e65e9e")),
      'seedPubKey': SecureBinaryData(hex_to_binary("042a471424da5e657499d1ff51cb43c47481a03b1e77f951fe64cec9f5a48f7011cf31cb47de7ccf6196d3a580d055837de7aa374e28c6c8a263e7b4512ceee362")),
      'seedCompPubKey': SecureBinaryData(hex_to_binary("022a471424da5e657499d1ff51cb43c47481a03b1e77f951fe64cec9f5a48f7011")),
      'seedExtSerPrv': SecureBinaryData(hex_to_binary("0488ade405d880d7d83b9aca00c783e67b921d2beb8f6b389cc646d7263b4145701dadd2161548a8b078e65e9e00471b76e389e528d6de6d816857e012c5455051cad6660850e58372a6c3e6e7c8")),
      'seedExtSerPub': SecureBinaryData(hex_to_binary("0488b21e05d880d7d83b9aca00c783e67b921d2beb8f6b389cc646d7263b4145701dadd2161548a8b078e65e9e022a471424da5e657499d1ff51cb43c47481a03b1e77f951fe64cec9f5a48f7011")),
      'seedID': SecureBinaryData(hex_to_binary("d69aa102255fed74378278c7812701ea641fdf32")),
      'seedFP': SecureBinaryData(hex_to_binary("d69aa102")),
      'seedParFP': SecureBinaryData(hex_to_binary("d880d7d8")),
      'nextChild': None
   })



SEEDTEST = [{}, {}]

SEEDTEST[0]['Seed']  = SecureBinaryData(hex_to_binary("000102030405060708090a0b0c0d0e0f"));
SEEDTEST[0]['Priv']  = SecureBinaryData(hex_to_binary("e8f32e723decf4051aefac8e2c93c9c5b214313817cdb01a1494b917c8436b35"));
SEEDTEST[0]['Pubk']  = SecureBinaryData(hex_to_binary("0339a36013301597daef41fbe593a02cc513d0b55527ec2df1050e2e8ff49c85c2"));
SEEDTEST[0]['Chain'] = SecureBinaryData(hex_to_binary("873dff81c02f525623fd1fe5167eac3a55a049de3d314bb42ee227ffed37d508"));

SEEDTEST[1]['Seed']  = SecureBinaryData(hex_to_binary("fffcf9f6f3f0edeae7e4e1dedbd8d5d2cfccc9c6c3c0bdbab7b4b1aeaba8a5a29f9c999693908d8a8784817e7b7875726f6c696663605d5a5754514e4b484542"));
SEEDTEST[1]['Priv']  = SecureBinaryData(hex_to_binary("4b03d6fc340455b363f51020ad3ecca4f0850280cf436c70c727923f6db46c3e"));
SEEDTEST[1]['Pubk']  = SecureBinaryData(hex_to_binary("03cbcaa9c98c877a26977d00825c956a238e8dddfbd322cce4f74b0b5bd6ace4a7"));
SEEDTEST[1]['Chain'] = SecureBinaryData(hex_to_binary("60499f801b896d83179a4374aeb7822aaeaceaa0db1f85ee3e904c4defbd9689"));




################################################################################
class MockWalletFile(object):
   def __init__(self):
      self.ekeyMap = {}

   def doFileOperation(*args, **kwargs):
      pass

   def addFileOperationToQueue(*args, **kwargs):
      pass

   def fsyncUpdates(*args, **kwargs):
      pass

   def getName(self):
      return 'MockWalletFile'



################################################################################
def skipFlagExists():
   if os.path.exists('skipmosttests.flag'):
      print '*'*80
      print 'SKIPPING MOST TESTS.  REMOVE skipMostTests.flag TO REENABLE'
      print '*'*80
      return True
   else:
      return False



#############################################################################
def runSerUnserRoundTripTest(tself, akp):
   """
   Can be run with "self" as the first arg from inside a TestCase subclass

   This started out as just a serialize-unserialize round-trip test to be
   run on AKP objects all over the place, but it has turned into a much more
   exhaustive test, now checking key encodings, and variable consistency.
   """
   # Compare all properties for all classes, this function ignores a call 
   # properties that don't exist for the input objects
   def cmpprop(a,b,prop):
      if hasattr(a, prop) and hasattr(b, prop):
         tself.assertEqual(getattr(a, prop), getattr(b, prop))

   # We test serialize, unserialize and copy, all at once
   CLASSAKP   = akp.__class__
   ser1       = akp.serialize()  
   akpNew     = CLASSAKP().unserialize(ser1)
   akpNewCopy = akpNew.copy()
   ser2       = akpNewCopy.serialize()
   akpNew2    = CLASSAKP().unserialize(ser2)
   

   # Now check that all the properties are identical
   cmpprop(akpNew, akpNew2, 'isWatchOnly')
   cmpprop(akpNew, akpNew2, 'isAkpRootRoot')
   cmpprop(akpNew, akpNew2, 'sbdPrivKeyData')
   cmpprop(akpNew, akpNew2, 'sbdPublicKey33')
   cmpprop(akpNew, akpNew2, 'sbdChaincode')
   cmpprop(akpNew, akpNew2, 'useCompressPub')
   cmpprop(akpNew, akpNew2, 'isUsed')
   cmpprop(akpNew, akpNew2, 'notForDirectUse')
   cmpprop(akpNew, akpNew2, 'keyBornTime')
   cmpprop(akpNew, akpNew2, 'keyBornBlock')
   cmpprop(akpNew, akpNew2, 'privKeyNextUnlock')
   cmpprop(akpNew, akpNew2, 'akpParScrAddr')
   cmpprop(akpNew, akpNew2, 'childIndex')
   cmpprop(akpNew, akpNew2, 'maxChildren')
   cmpprop(akpNew, akpNew2, 'rawScript')
   cmpprop(akpNew, akpNew2, 'scrAddrStr')
   cmpprop(akpNew, akpNew2, 'uniqueIDBin')
   cmpprop(akpNew, akpNew2, 'uniqueIDB58')

   tself.assertEqual( akpNew.privCryptInfo.serialize(),
                     akpNew2.privCryptInfo.serialize())

   cmpprop(akpNew, akpNew2, 'walletName')
   cmpprop(akpNew, akpNew2, 'sbdSeedData')
   cmpprop(akpNew, akpNew2, 'seedNumBytes')
   cmpprop(akpNew, akpNew2, 'chainIndex')
   cmpprop(akpNew, akpNew2, 'root135ScrAddr')
   cmpprop(akpNew, akpNew2, 'userRemoved')
   cmpprop(akpNew, akpNew2, 'rootSourceApp')
   cmpprop(akpNew, akpNew2, 'fakeRootID')

   try:
      tself.assertEqual( akpNew.seedCryptInfo.serialize(),
                        akpNew2.seedCryptInfo.serialize())
   except:
      pass

   # Test that the raw serializations are identical
   tself.assertEqual(ser1, ser2)

   # For fun, why not add these encoding tests everywhere we test ser/unser
   if akpNew.sbdPublicKey33.getSize() > 0:
      sbdPubk = akpNew2.sbdPublicKey33.copy()
      if not akpNew.useCompressPub:
         sbdPubk = CryptoECDSA().UncompressPoint(sbdPubk)
      tself.assertEqual(akpNew.getSerializedPubKey('hex'), sbdPubk.toHexStr())
      tself.assertEqual(akpNew.getSerializedPubKey('bin'), sbdPubk.toBinStr())

   if akpNew.getPrivKeyAvailability()==PRIV_KEY_AVAIL.Available:
      lastByte = '\x01' if akpNew.useCompressPub else ''
      lastHex  =   '01' if akpNew.useCompressPub else ''
         
      sbdPriv = akpNew2.getPlainPrivKeyCopy()
      sipaPriv = PRIVKEYBYTE + sbdPriv.toBinStr() + lastByte
      sipaPriv = binary_to_base58(sipaPriv + computeChecksum(sipaPriv))
      tself.assertEqual(akpNew.getSerializedPrivKey('bin'), sbdPriv.toBinStr()+lastByte)
      tself.assertEqual(akpNew.getSerializedPrivKey('hex'), sbdPriv.toHexStr()+lastHex)
      tself.assertEqual(akpNew.getSerializedPrivKey('sipa'), sipaPriv)
      tself.assertEqual(akpNew.getSerializedPrivKey('sipa'), 
            encodePrivKeyBase58(sbdPriv.toBinStr(), isCompressed=akpNew.useCompressPub))

   # Check that if rootroot, it is marked as its own parent
   if akpNew2.isAkpRootRoot:
      tself.assertEqual(akpNew2.getScrAddr(), akpNew2.akpParScrAddr)



################################################################################
class UtilityFuncTests(unittest.TestCase):

   #############################################################################
   def testSplitChildIndex(self):
      self.assertRaises(ValueError, SplitChildIndex, 2**32)
      self.assertRaises(ValueError, SplitChildIndex, -1)

      TOPBIT = HARDBIT
      self.assertEqual(SplitChildIndex(0),          [0, False])
      self.assertEqual(SplitChildIndex(1),          [1, False])
      self.assertEqual(SplitChildIndex(128),        [128, False])
      self.assertEqual(SplitChildIndex(0+TOPBIT),   [0, True])
      self.assertEqual(SplitChildIndex(1+TOPBIT),   [1, True])
      self.assertEqual(SplitChildIndex(2**32-1),    [2**31-1, True])
      self.assertEqual(SplitChildIndex(0x7fffffff), [0x7fffffff, False])
      self.assertEqual(SplitChildIndex(HARDBIT), [0, True])


   #############################################################################
   def testCreateChildIndex(self):
      TOPBIT = HARDBIT
      self.assertEqual(CreateChildIndex(0, False),          0)
      self.assertEqual(CreateChildIndex(1, False),          1)
      self.assertEqual(CreateChildIndex(128, False),        128)
      self.assertEqual(CreateChildIndex(0, True),           0+TOPBIT)
      self.assertEqual(CreateChildIndex(1, True),           1+TOPBIT)
      self.assertEqual(CreateChildIndex(2**31-1, True),     2**32-1)
      self.assertEqual(CreateChildIndex(0x7fffffff, False), 0x7fffffff)
      self.assertEqual(CreateChildIndex(0, True),           HARDBIT)

   #############################################################################
   def testChildIdxToStr(self):
      TOPBIT = HARDBIT
      self.assertEqual(ChildIndexToStr(0), "0")
      self.assertEqual(ChildIndexToStr(1), "1")
      self.assertEqual(ChildIndexToStr(128), "128")
      self.assertEqual(ChildIndexToStr(0+TOPBIT), "0'")
      self.assertEqual(ChildIndexToStr(1+TOPBIT), "1'")
      self.assertEqual(ChildIndexToStr(2**32-1), "2147483647'")
      self.assertEqual(ChildIndexToStr(0x7fffffff), "2147483647")
      self.assertEqual(ChildIndexToStr(HARDBIT), "0'")


################################################################################
class TestHDWalletLogic(unittest.TestCase):

   #############################################################################
   def testCppConvertSeed(self):
      extkey = Cpp.HDWalletCrypto().convertSeedToMasterKey(SEEDTEST[0]['Seed'])
      self.assertEqual(extkey.getPrivateKey(False), SEEDTEST[0]['Priv'])
      self.assertEqual(extkey.getPublicKey(), SEEDTEST[0]['Pubk'])
      self.assertEqual(extkey.getChaincode(), SEEDTEST[0]['Chain'])

      extkey = Cpp.HDWalletCrypto().convertSeedToMasterKey(SEEDTEST[1]['Seed'])
      self.assertEqual(extkey.getPrivateKey(False), SEEDTEST[1]['Priv'])
      self.assertEqual(extkey.getPublicKey(), SEEDTEST[1]['Pubk'])
      self.assertEqual(extkey.getChaincode(), SEEDTEST[1]['Chain'])


   #############################################################################
   def testCppDeriveChild(self):

      for i in range(len(BIP32TestVectors)-1):
         currEKdata = BIP32TestVectors[i]
         nextEKdata = BIP32TestVectors[i+1]


         currEK = Cpp.ExtendedKey(currEKdata['seedKey'], currEKdata['seedCC'])
         compEK = Cpp.HDWalletCrypto().childKeyDeriv(currEK, currEKdata['nextChild'])
         nextPriv = SecureBinaryData(nextEKdata['seedKey'].toBinStr()[1:])
         self.assertEqual(compEK.getPrivateKey(False), nextPriv)
         self.assertEqual(compEK.getPublicKey(), nextEKdata['seedCompPubKey'])
         self.assertEqual(compEK.getChaincode(), nextEKdata['seedCC'])

         if currEKdata['nextChild'] & HARDBIT == 0:
            # Now test the same thing from the just the public key
            currEK = Cpp.ExtendedKey(currEKdata['seedCompPubKey'], currEKdata['seedCC'])
            compEK = Cpp.HDWalletCrypto().childKeyDeriv(currEK, currEKdata['nextChild'])
            #self.assertTrue(currEK.isPub())
            #self.assertEqual(compEK.getPublicKey(), nextEKdata['seedCompPubKey'])
            #self.assertEqual(compEK.getChaincode(), nextEKdata['seedCC'])
         
         

################################################################################
################################################################################
#
# Armory BIP32 Extended Key tests (NO ENCRYPTION)
#
################################################################################
################################################################################

################################################################################
class ABEK_Tests(unittest.TestCase):

   #############################################################################
   def setUp(self):
      self.mockwlt  = MockWalletFile()

      self.password = SecureBinaryData('hello')
      master32 = SecureBinaryData('\x3e'*32)
      randomiv = SecureBinaryData('\x7d'*8)

      # Create a KDF to be used for encryption key password
      self.kdf = KdfObject('ROMIXOV2', memReqd=32*KILOBYTE,
                                       numIter=1, 
                                       salt=SecureBinaryData('\x21'*32))

      # Create the new master encryption key to be used to encrypt priv keys
      self.ekey = EncryptionKey().createNewMasterKey(self.kdf, 'AE256CBC', 
                     self.password, preGenKey=master32, preGenIV8=randomiv)

      # This will be attached to each ABEK object, to define its encryption
      self.privACI = ArmoryCryptInfo(NULLKDF, 'AE256CBC', 
                                 self.ekey.ekeyID, 'PUBKEY20')

      
   #############################################################################
   def tearDown(self):
      pass
      

   #############################################################################
   def test_InitABEK(self):
      abek = ABEK_Generic()
         
      self.assertEqual(abek.isWatchOnly, False)
      self.assertEqual(abek.sbdPrivKeyData, NULLSBD())
      self.assertEqual(abek.sbdPublicKey33, NULLSBD())
      self.assertEqual(abek.sbdChaincode, NULLSBD())
      self.assertEqual(abek.useCompressPub, True)
      self.assertEqual(abek.isUsed, False)
      self.assertEqual(abek.keyBornTime, 0)
      self.assertEqual(abek.keyBornBlock, 0)
      self.assertEqual(abek.privKeyNextUnlock, False)
      self.assertEqual(abek.akpParScrAddr, None)
      self.assertEqual(abek.childIndex, None)
      self.assertEqual(abek.childPoolSize, 5)
      self.assertEqual(abek.maxChildren, UINT32_MAX)
      self.assertEqual(abek.rawScript, None)
      self.assertEqual(abek.scrAddrStr, None)
      self.assertEqual(abek.uniqueIDBin, None)
      self.assertEqual(abek.uniqueIDB58, None)
      self.assertEqual(abek.akpChildByIndex, {})
      self.assertEqual(abek.akpChildByScrAddr, {})
      self.assertEqual(abek.lowestUnusedChild, 0)
      self.assertEqual(abek.nextChildToCalc,   0)
      self.assertEqual(abek.akpParentRef, None)
      self.assertEqual(abek.masterEkeyRef, None)

      self.assertEqual(abek.TREELEAF, False)
      self.assertEqual(abek.getName(), 'ABEK_Generic')
      self.assertEqual(abek.getPrivKeyAvailability(), PRIV_KEY_AVAIL.Uninit)

      # WalletEntry fields
      self.assertEqual(abek.wltFileRef, None)
      self.assertEqual(abek.wltByteLoc, None)
      self.assertEqual(abek.wltEntrySz, None)
      self.assertEqual(abek.isRequired, False)
      self.assertEqual(abek.parEntryID, None)
      self.assertEqual(abek.outerCrypt.serialize(), NULLCRYPTINFO().serialize())
      self.assertEqual(abek.serPayload, None)
      self.assertEqual(abek.defaultPad, 256)
      self.assertEqual(abek.wltParentRef, None)
      self.assertEqual(abek.wltChildRefs, [])
      self.assertEqual(abek.outerEkeyRef, None)
      self.assertEqual(abek.isOpaque,        False)
      self.assertEqual(abek.isUnrecognized,  False)
      self.assertEqual(abek.isUnrecoverable, False)
      self.assertEqual(abek.isDeleted,       False)
      self.assertEqual(abek.isDisabled,      False)
      self.assertEqual(abek.needFsync,       False)

      self.assertRaises(UninitializedError, abek.serialize)

   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testSpawnABEK(self):
      sbdPriv  = SecureBinaryData(BIP32TestVectors[1]['seedKey'].toBinStr()[1:])
      sbdPubk  = BIP32TestVectors[1]['seedCompPubKey']
      sbdChain = BIP32TestVectors[1]['seedCC']
      nextIdx  = BIP32TestVectors[1]['nextChild']

      parA160    = hash160(sbdPubk.toBinStr())
      parScript  = hash160_to_p2pkhash_script(parA160)
      parScrAddr = SCRADDR_P2PKH_BYTE + parA160

      nextPriv  = SecureBinaryData(BIP32TestVectors[2]['seedKey'].toBinStr()[1:])
      nextPubk  = BIP32TestVectors[2]['seedCompPubKey']
      nextChain = BIP32TestVectors[2]['seedCC']

      chA160    = hash160(nextPubk.toBinStr())
      chScript  = hash160_to_p2pkhash_script(chA160)
      chScrAddr = SCRADDR_P2PKH_BYTE + chA160


      abek = ABEK_Generic()
      abek.isWatchOnly = False
      abek.sbdPrivKeyData = sbdPriv.copy()
      abek.sbdPublicKey33 = sbdPubk.copy()
      abek.sbdChaincode   = sbdChain.copy()
      abek.useCompressPub = True
      abek.privKeyNextUnlock = False

      childAbek = abek.spawnChild(nextIdx, fsync=False)

      self.assertEqual(childAbek.sbdPrivKeyData, nextPriv)
      self.assertEqual(childAbek.sbdPublicKey33, nextPubk)
      self.assertEqual(childAbek.sbdChaincode,   nextChain)
      self.assertEqual(childAbek.useCompressPub, True)
      self.assertEqual(childAbek.isUsed, False)
      self.assertEqual(childAbek.privKeyNextUnlock, False)
      self.assertEqual(childAbek.akpParScrAddr, parScrAddr)
      self.assertEqual(childAbek.childIndex, nextIdx)
      self.assertEqual(childAbek.childPoolSize, 5)
      self.assertEqual(childAbek.maxChildren, UINT32_MAX)
      self.assertEqual(childAbek.rawScript, chScript)
      self.assertEqual(childAbek.scrAddrStr, chScrAddr)
      #self.assertEqual(childAbek.akpChildByIndex, {})
      #self.assertEqual(childAbek.akpChildByScrAddr, {})
      self.assertEqual(childAbek.lowestUnusedChild, 0)
      self.assertEqual(childAbek.nextChildToCalc,   0)
      self.assertEqual(childAbek.masterEkeyRef, None)
      
      # Check the uniqueID, by spawning another child
      subCh = childAbek.spawnChild(0x7fffffff, fsync=False, forIDCompute=True)
      ch256  = hash256(subCh.getScrAddr())
      firstByte = binary_to_int(ch256[0])
      newFirst  = firstByte ^ binary_to_int(ADDRBYTE)
      uidBin = int_to_binary(newFirst) + ch256[1:6]
      uidB58 = binary_to_base58(uidBin)
      self.assertEqual(childAbek.uniqueIDBin, uidBin)
      self.assertEqual(childAbek.uniqueIDB58, uidB58)

      runSerUnserRoundTripTest(self, childAbek)

      # Test the serialized Pub/Priv methods
      sipaPriv = PRIVKEYBYTE + sbdPriv.toBinStr() + '\x01'
      sipaPriv = binary_to_base58(sipaPriv + computeChecksum(sipaPriv))
      self.assertEqual(abek.getSerializedPrivKey('bin'), sbdPriv.toBinStr()+'\x01')
      self.assertEqual(abek.getSerializedPrivKey('hex'), sbdPriv.toHexStr()+'01')
      self.assertEqual(abek.getSerializedPrivKey('sipa'), sipaPriv)
      self.assertEqual(abek.getSerializedPrivKey('sipa'), 
            encodePrivKeyBase58(sbdPriv.toBinStr(), isCompressed=True))
      self.assertEqual(abek.getSerializedPubKey('hex'), sbdPubk.toHexStr())
      self.assertEqual(abek.getSerializedPubKey('bin'), sbdPubk.toBinStr())


   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testSpawnABEK_WO(self):
      #This test appears to demonstrate a problem with pubkey-based spawnChild
      #Disabled for now...

      sbdPriv  = SecureBinaryData(BIP32TestVectors[1]['seedKey'].toBinStr()[1:])
      sbdPubk  = BIP32TestVectors[1]['seedCompPubKey']
      sbdChain = BIP32TestVectors[1]['seedCC']
      nextIdx  = BIP32TestVectors[1]['nextChild']

      parA160    = hash160(sbdPubk.toBinStr())
      parScript  = hash160_to_p2pkhash_script(parA160)
      parScrAddr = SCRADDR_P2PKH_BYTE + parA160

      nextPriv  = SecureBinaryData(BIP32TestVectors[2]['seedKey'].toBinStr()[1:])
      nextPubk  = BIP32TestVectors[2]['seedCompPubKey']
      nextChain = BIP32TestVectors[2]['seedCC']

      chA160    = hash160(nextPubk.toBinStr())
      chScript  = hash160_to_p2pkhash_script(chA160)
      chScrAddr = SCRADDR_P2PKH_BYTE + chA160


      abek = ABEK_Generic()
      abek.isWatchOnly = True
      abek.sbdPrivKeyData = NULLSBD()
      abek.sbdPublicKey33 = sbdPubk.copy()
      abek.sbdChaincode   = sbdChain.copy()
      abek.useCompressPub = True

      self.assertRaises(KeyDataError, abek.spawnChild, nextIdx, privSpawnReqd=True)

      childAbek = abek.spawnChild(nextIdx, fsync=False)

      self.assertEqual(childAbek.sbdPrivKeyData, NULLSBD())
      self.assertEqual(childAbek.sbdChaincode,   nextChain)
      self.assertEqual(childAbek.sbdPublicKey33, nextPubk)
      self.assertEqual(childAbek.useCompressPub, True)
      self.assertEqual(childAbek.isUsed, False)
      self.assertEqual(childAbek.privKeyNextUnlock, False)
      self.assertEqual(childAbek.akpParScrAddr, parScrAddr)
      self.assertEqual(childAbek.childIndex, nextIdx)
      self.assertEqual(childAbek.childPoolSize, 5)
      self.assertEqual(childAbek.maxChildren, UINT32_MAX)
      self.assertEqual(childAbek.rawScript, chScript)
      self.assertEqual(childAbek.scrAddrStr, chScrAddr)
      self.assertEqual(childAbek.lowestUnusedChild, 0)
      self.assertEqual(childAbek.nextChildToCalc,   0)
      self.assertEqual(childAbek.masterEkeyRef, None)


      # Test setting the child ref, which is normally done for you if fsync=True
      abek.addChildRef(childAbek)
      self.assertEqual(childAbek.akpParScrAddr, parScrAddr)


      # Test the serialized Pub/Priv methods
      self.assertEqual(childAbek.getSerializedPubKey('hex'), nextPubk.toHexStr())
      self.assertEqual(childAbek.getSerializedPubKey('bin'), nextPubk.toBinStr())
      



   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def test_InitABEK2(self):
      #leaf = makeABEKGenericClass()
      abek = ABEK_Generic()

      sbdPriv  = SecureBinaryData(BIP32TestVectors[0]['seedKey'].toBinStr()[1:])
      sbdPubk  = BIP32TestVectors[0]['seedCompPubKey']
      sbdChain = BIP32TestVectors[0]['seedCC']

      a160    = hash160(sbdPubk.toBinStr())
      rawScr  = hash160_to_p2pkhash_script(a160)
      scrAddr = SCRADDR_P2PKH_BYTE + a160

      t = long(RightNow())
      abek.initializeAKP(isWatchOnly=False,
                         isAkpRootRoot=False,
                         privCryptInfo=NULLCRYPTINFO(),
                         sbdPrivKeyData=sbdPriv,
                         sbdPublicKey33=sbdPubk,
                         sbdChaincode=sbdChain,
                         privKeyNextUnlock=False,
                         akpParScrAddr=None,
                         childIndex=None,
                         useCompressPub=True,
                         isUsed=True,
                         notForDirectUse=False,
                         keyBornTime=t,
                         keyBornBlock=t)

      # Recompute unique ID directly for comparison
      childAbek  = abek.spawnChild(0x7fffffff, fsync=False, forIDCompute=True)
      child256  = hash256(childAbek.getScrAddr())
      firstByte = binary_to_int(child256[0])
      newFirst  = firstByte ^ binary_to_int(ADDRBYTE)
      uidBin = int_to_binary(newFirst) + child256[1:6]
      uidB58 = binary_to_base58(uidBin)

                           
      self.assertEqual(abek.isWatchOnly, False)
      self.assertEqual(abek.sbdPrivKeyData, sbdPriv)
      self.assertEqual(abek.getPlainPrivKeyCopy(), sbdPriv)
      self.assertEqual(abek.sbdPublicKey33, sbdPubk)
      self.assertEqual(abek.sbdChaincode, sbdChain)
      self.assertEqual(abek.useCompressPub, True)
      self.assertEqual(abek.isUsed, True)
      self.assertEqual(abek.keyBornTime, t)
      self.assertEqual(abek.keyBornBlock, t)
      self.assertEqual(abek.privKeyNextUnlock, False)
      self.assertEqual(abek.akpParScrAddr, None)
      self.assertEqual(abek.childIndex, None)
      self.assertEqual(abek.childPoolSize, 5)
      self.assertEqual(abek.maxChildren, UINT32_MAX)
      self.assertEqual(abek.rawScript, rawScr)
      self.assertEqual(abek.scrAddrStr, scrAddr)
      self.assertEqual(abek.uniqueIDBin, uidBin)
      self.assertEqual(abek.uniqueIDB58, uidB58)
      self.assertEqual(abek.akpChildByIndex, {})
      self.assertEqual(abek.akpChildByScrAddr, {})
      self.assertEqual(abek.lowestUnusedChild, 0)
      self.assertEqual(abek.nextChildToCalc,   0)
      self.assertEqual(abek.akpParentRef, None)
      self.assertEqual(abek.masterEkeyRef, None)

      self.assertEqual(abek.TREELEAF, False)
      self.assertEqual(abek.getName(), 'ABEK_Generic')
      self.assertEqual(abek.getPrivKeyAvailability(), PRIV_KEY_AVAIL.Available)

      self.assertEqual(abek.getPlainPrivKeyCopy(), sbdPriv)

      runSerUnserRoundTripTest(self, abek)
      


   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testKeyPool_D1(self):
      """
      Doesn't test the accuracy of ABEK calculations, only the keypool sizes
      """
      mockwlt = MockWalletFile()
      echain = ABEK_StdChainExt()
      sbdPriv  = SecureBinaryData(BIP32TestVectors[0]['seedKey'].toBinStr()[1:])
      sbdPubk  = BIP32TestVectors[0]['seedCompPubKey']
      sbdChain = BIP32TestVectors[0]['seedCC']


      # Do this both for priv-key-based derivation and WO-based deriv
      for testWatchOnly in [True,False]:
         echain.initializeAKP(isWatchOnly=testWatchOnly,
                              isAkpRootRoot=False,
                              privCryptInfo=NULLCRYPTINFO(),
                              sbdPrivKeyData=sbdPriv,
                              sbdPublicKey33=sbdPubk,
                              sbdChaincode=sbdChain,
                              privKeyNextUnlock=False,
                              akpParScrAddr=None,
                              childIndex=None,
                              useCompressPub=True,
                              isUsed=True,
                              notForDirectUse=False)

         # Test privKeyAvail methods
         if testWatchOnly:
            self.assertEqual(echain.getPrivKeyAvailability(), PRIV_KEY_AVAIL.WatchOnly)
         else:
            self.assertEqual(echain.getPrivKeyAvailability(), PRIV_KEY_AVAIL.Available)
      
         echain.wltFileRef = mockwlt
         echain.setChildPoolSize(5)

      
         self.assertEqual(echain.isWatchOnly,    testWatchOnly)
         self.assertEqual(echain.sbdPublicKey33, sbdPubk)
         self.assertEqual(echain.sbdChaincode,   sbdChain)

         if not testWatchOnly:
            self.assertEqual(echain.sbdPrivKeyData, sbdPriv)
            self.assertEqual(echain.getPlainPrivKeyCopy(), sbdPriv)

         self.assertEqual(echain.lowestUnusedChild,   0)
         self.assertEqual(echain.nextChildToCalc,     0)
         self.assertEqual(echain.childPoolSize,       5)

         echain.fillKeyPool()

         self.assertEqual(echain.lowestUnusedChild,  0)
         self.assertEqual(echain.nextChildToCalc,    5)
         self.assertEqual(echain.childPoolSize,      5)



   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testKeyPool_D2(self):
      """
      Doesn't test the accuracy of ABEK calculations, only the keypool sizes
      """
      mockwlt  = MockWalletFile()
      awlt   = ABEK_StdWallet()

      self.assertRaises(ChildDeriveError, awlt.getChildClass, 2)
      self.assertRaises(ChildDeriveError, awlt.getChildClass, HARDBIT)
      self.assertRaises(ChildDeriveError, awlt.getChildClass, 2+HARDBIT)

      sbdPriv  = SecureBinaryData(BIP32TestVectors[0]['seedKey'].toBinStr()[1:])
      sbdPubk  = BIP32TestVectors[0]['seedCompPubKey']
      sbdChain = BIP32TestVectors[0]['seedCC']

      for testWatchOnly in [True,False]:
         awlt.initializeAKP(  isWatchOnly=testWatchOnly,
                              isAkpRootRoot=False,
                              privCryptInfo=NULLCRYPTINFO(),
                              sbdPrivKeyData=sbdPriv,
                              sbdPublicKey33=sbdPubk,
                              sbdChaincode=sbdChain,
                              privKeyNextUnlock=False,
                              akpParScrAddr=None,
                              childIndex=None,
                              useCompressPub=True,
                              isUsed=True,
                              notForDirectUse=False)
      
   
         awlt.wltFileRef = mockwlt
      
         self.assertEqual(awlt.isWatchOnly,    testWatchOnly)
         self.assertEqual(awlt.sbdPublicKey33, sbdPubk)
         self.assertEqual(awlt.sbdChaincode,   sbdChain)

         if not testWatchOnly:
            self.assertEqual(awlt.sbdPrivKeyData, sbdPriv)
            self.assertEqual(awlt.getPlainPrivKeyCopy(), sbdPriv)

         self.assertEqual(awlt.lowestUnusedChild, 0)
         self.assertEqual(awlt.nextChildToCalc,   0)

         awlt.fillKeyPool()

         self.assertEqual(awlt.lowestUnusedChild,  0)
         self.assertEqual(awlt.nextChildToCalc,    2)
         self.assertEqual(len(awlt.akpChildByIndex), 2)
         self.assertEqual(awlt.akpChildByIndex[0].__class__, ABEK_StdChainExt)
         self.assertEqual(awlt.akpChildByIndex[1].__class__, ABEK_StdChainInt)
         self.assertEqual(awlt.akpChildByIndex[0].childPoolSize, 
                                       DEFAULT_CHILDPOOLSIZE['ABEK_StdChainExt'])
         self.assertEqual(awlt.akpChildByIndex[1].childPoolSize, 
                                       DEFAULT_CHILDPOOLSIZE['ABEK_StdChainInt'])







   #############################################################################
   def testABEK_seedCalc(self):
      mockwlt  = MockWalletFile()
      abekSeed = ABEK_StdBip32Seed()
      abekSeed.setWalletAndCryptInfo(mockwlt, None)

      WRONGPUBK = SecureBinaryData('\x03' + '\xaa'*32)
   
      abekSeed.initializeFromSeed(SEEDTEST[0]['Seed'], fillPool=False)
      self.assertEqual(abekSeed.getPlainPrivKeyCopy(), SEEDTEST[0]['Priv'])
      self.assertEqual(abekSeed.sbdPublicKey33,        SEEDTEST[0]['Pubk'])
      self.assertEqual(abekSeed.sbdChaincode,          SEEDTEST[0]['Chain'])
      self.assertEqual(abekSeed.getPlainSeedCopy(),    SEEDTEST[0]['Seed'])
      
      abekSeed.initializeFromSeed(SEEDTEST[0]['Seed'], 
                        verifyPub=SEEDTEST[0]['Pubk'], fillPool=False)
      self.assertEqual(abekSeed.getPlainPrivKeyCopy(), SEEDTEST[0]['Priv'])
      self.assertEqual(abekSeed.sbdPublicKey33,        SEEDTEST[0]['Pubk'])
      self.assertEqual(abekSeed.sbdChaincode,          SEEDTEST[0]['Chain'])
      self.assertEqual(abekSeed.getPlainSeedCopy(),    SEEDTEST[0]['Seed'])

      self.assertRaises(KeyDataError, abekSeed.initializeFromSeed, 
                        SEEDTEST[0]['Seed'], verifyPub=WRONGPUBK)



      abekSeed.initializeFromSeed(SEEDTEST[1]['Seed'], fillPool=False)
      self.assertEqual(abekSeed.getPlainPrivKeyCopy(), SEEDTEST[1]['Priv'])
      self.assertEqual(abekSeed.sbdPublicKey33,        SEEDTEST[1]['Pubk'])
      self.assertEqual(abekSeed.sbdChaincode,          SEEDTEST[1]['Chain'])
      self.assertEqual(abekSeed.getPlainSeedCopy(),    SEEDTEST[1]['Seed'])
      
      abekSeed.initializeFromSeed(SEEDTEST[1]['Seed'], 
                        verifyPub=SEEDTEST[1]['Pubk'], fillPool=False)
      self.assertEqual(abekSeed.getPlainPrivKeyCopy(), SEEDTEST[1]['Priv'])
      self.assertEqual(abekSeed.sbdPublicKey33,        SEEDTEST[1]['Pubk'])
      self.assertEqual(abekSeed.sbdChaincode,          SEEDTEST[1]['Chain'])
      self.assertEqual(abekSeed.getPlainSeedCopy(),    SEEDTEST[1]['Seed'])

      self.assertRaises(KeyDataError, abekSeed.initializeFromSeed, 
                        SEEDTEST[1]['Seed'], verifyPub=WRONGPUBK)


      runSerUnserRoundTripTest(self, abekSeed)


   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testABEK_newSeed(self):
      mockwlt  = MockWalletFile()
      abekSeed = ABEK_StdBip32Seed()
      abekSeed.wltFileRef = mockwlt
   
      abekSeed.privCryptInfo = NULLCRYPTINFO()

      # Extra entropy should be pulled from external sources!  Such as
      # system files, screenshots, uninitialized RAM states... only do
      # it the following way for testing!
      entropy = SecureBinaryData().GenerateRandom(16)

      # Should fail for seed being too small
      self.assertRaises(KeyDataError, abekSeed.createNewSeed, 8, entropy)

      # Should fail for not supplying extra entropy
      self.assertRaises(TypeError, abekSeed.createNewSeed, 16, None)

      # Should fail for not supplying extra entropy
      self.assertRaises(KeyDataError, abekSeed.createNewSeed, 16, NULLSBD())

      for seedsz in [16, 20, 64]:
         abekSeed.createNewSeed(seedsz, entropy, fillPool=False)

      runSerUnserRoundTripTest(self, abekSeed)

   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testGetParentList(self):
      mockwlt  = MockWalletFile()
      abekSeed = ABEK_StdBip32Seed()
      abekSeed.wltFileRef = mockwlt
      abekSeed.privCryptInfo = NULLCRYPTINFO()
      entropy = SecureBinaryData().GenerateRandom(16)
      abekSeed.createNewSeed(16, entropy, fillPool=False)

      # Test root itself, shoudl be empty
      self.assertEqual(abekSeed.getParentList(), [])

      abekSeed.fillKeyPool()

      # Test first-level parent lists
      for widx,abekWlt in abekSeed.akpChildByIndex.iteritems():
         expect = [[abekSeed, widx]]
         self.assertEqual(abekWlt.getParentList(), expect)

      # Test two-levels:
      for widx,abekWlt in abekSeed.akpChildByIndex.iteritems():
         for cidx,abekChn in abekWlt.akpChildByIndex.iteritems():
            expect = [[abekSeed, widx], [abekWlt, cidx]]
            self.assertEqual(abekChn.getParentList(), expect)

      # Test two-levels:
      for widx,abekWlt in abekSeed.akpChildByIndex.iteritems():
         for cidx,abekChn in abekWlt.akpChildByIndex.iteritems():
            expect = [[abekSeed, widx], [abekWlt, cidx]]
            self.assertEqual(abekChn.getParentList(), expect)

      # Test three-levels:
      for widx,abekWlt in abekSeed.akpChildByIndex.iteritems():
         for cidx,abekChn in abekWlt.akpChildByIndex.iteritems():
            for lidx,abekLeaf in abekChn.akpChildByIndex.iteritems():
               expect = [[abekSeed, widx], [abekWlt, cidx], [abekChn, lidx]]
               self.assertEqual(abekLeaf.getParentList(), expect)

      # Test up to different base
      for widx,abekWlt in abekSeed.akpChildByIndex.iteritems():
         for cidx,abekChn in abekWlt.akpChildByIndex.iteritems():
            for lidx,abekLeaf in abekChn.akpChildByIndex.iteritems():
               expect = [[abekWlt, cidx], [abekChn, lidx]]
               wsa = abekWlt.getScrAddr()
               self.assertEqual(abekLeaf.getParentList(wsa), expect)
               self.assertRaises(ChildDeriveError, abekLeaf.getParentList, 'abc')
   


   ################################################################################
   ################################################################################
   #
   # Armory BIP32 Extended Key tests (WITH ENCRYPTION)
   #
   ################################################################################
   ################################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testSpawnABEK_Crypt(self):
      #leaf = makeABEKGenericClass()
      abek = ABEK_Generic()
      
      sbdPriv  = SecureBinaryData(BIP32TestVectors[0]['seedKey'].toBinStr()[1:])
      sbdPubk  = BIP32TestVectors[0]['seedCompPubKey']
      sbdChain = BIP32TestVectors[0]['seedCC']

      a160    = hash160(sbdPubk.toBinStr())
      rawScr  = hash160_to_p2pkhash_script(a160)
      scrAddr = SCRADDR_P2PKH_BYTE + a160

      # First some prep for encryption/decryption, and verify outputs
      self.ekey.unlock(self.password)
      iv = SecureBinaryData(hash256(sbdPubk.toBinStr())[:16])
      privCrypt = self.privACI.encrypt(sbdPriv,   ekeyObj=self.ekey, ivData=iv)
      decrypted = self.privACI.decrypt(privCrypt, ekeyObj=self.ekey, ivData=iv)
      self.assertEqual(sbdPriv, decrypted)
      self.ekey.lock()


      t = long(RightNow())
      abek.initializeAKP(isWatchOnly=False,
                         isAkpRootRoot=False,
                         privCryptInfo=self.privACI,
                         sbdPrivKeyData=privCrypt,
                         sbdPublicKey33=sbdPubk,
                         sbdChaincode=sbdChain,
                         privKeyNextUnlock=False,
                         akpParScrAddr=None,
                         childIndex=None,
                         useCompressPub=True,
                         isUsed=True,
                         notForDirectUse=False,
                         keyBornTime=t,
                         keyBornBlock=t)

      abek.masterEkeyRef = self.ekey


      # Need to test the privkey available func
      self.ekey.lock()
      self.assertEqual(abek.getPrivKeyAvailability(), PRIV_KEY_AVAIL.NeedDecrypt)
      self.ekey.unlock(self.password)
      self.assertEqual(abek.getPrivKeyAvailability(), PRIV_KEY_AVAIL.Available)
      self.ekey.lock()
      self.assertEqual(abek.getPrivKeyAvailability(), PRIV_KEY_AVAIL.NeedDecrypt)


      # Recompute unique ID directly for comparison
      childAbek  = abek.spawnChild(0x7fffffff, fsync=False, forIDCompute=True)
      child256  = hash256(childAbek.getScrAddr())
      firstByte = binary_to_int(child256[0])
      newFirst  = firstByte ^ binary_to_int(ADDRBYTE)
      uidBin = int_to_binary(newFirst) + child256[1:6]
      uidB58 = binary_to_base58(uidBin)

      self.ekey.lock()
      self.assertRaises(WalletLockError, abek.getPlainPrivKeyCopy)
      self.ekey.unlock(self.password)
      self.assertEqual(abek.sbdPrivKeyData, privCrypt)
      self.assertEqual(abek.getPlainPrivKeyCopy(), sbdPriv)
      self.ekey.lock()

      self.assertEqual(abek.isWatchOnly, False)
      self.assertEqual(abek.sbdPublicKey33, sbdPubk)
      self.assertEqual(abek.sbdChaincode, sbdChain)
      self.assertEqual(abek.useCompressPub, True)
      self.assertEqual(abek.isUsed, True)
      self.assertEqual(abek.keyBornTime, t)
      self.assertEqual(abek.keyBornBlock, t)
      self.assertEqual(abek.privKeyNextUnlock, False)
      self.assertEqual(abek.akpParScrAddr, None)
      self.assertEqual(abek.childIndex, None)
      self.assertEqual(abek.childPoolSize, 5)
      self.assertEqual(abek.maxChildren, UINT32_MAX)
      self.assertEqual(abek.rawScript, rawScr)
      self.assertEqual(abek.scrAddrStr, scrAddr)
      self.assertEqual(abek.uniqueIDBin, uidBin)
      self.assertEqual(abek.uniqueIDB58, uidB58)
      self.assertEqual(abek.akpChildByIndex, {})
      self.assertEqual(abek.akpChildByScrAddr, {})
      self.assertEqual(abek.lowestUnusedChild, 0)
      self.assertEqual(abek.nextChildToCalc,   0)
      self.assertEqual(abek.akpParentRef, None)
      self.assertEqual(abek.privCryptInfo.serialize(), self.privACI.serialize())

      self.assertEqual(abek.TREELEAF, False)
      self.assertEqual(abek.getName(), 'ABEK_Generic')

      runSerUnserRoundTripTest(self, abek)

   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testSpawnABEK_Crypt2(self):
      # Start with this key pair
      sbdPriv  = SecureBinaryData(BIP32TestVectors[1]['seedKey'].toBinStr()[1:])
      sbdPubk  = BIP32TestVectors[1]['seedCompPubKey']
      sbdChain = BIP32TestVectors[1]['seedCC']
      nextIdx  = BIP32TestVectors[1]['nextChild']
      parA160    = hash160(sbdPubk.toBinStr())
      parScript  = hash160_to_p2pkhash_script(parA160)
      parScrAddr = SCRADDR_P2PKH_BYTE + parA160

      # Derive this keypair
      nextPriv  = SecureBinaryData(BIP32TestVectors[2]['seedKey'].toBinStr()[1:])
      nextPubk  = BIP32TestVectors[2]['seedCompPubKey']
      nextChain = BIP32TestVectors[2]['seedCC']
      chA160    = hash160(nextPubk.toBinStr())
      chScript  = hash160_to_p2pkhash_script(chA160)
      chScrAddr = SCRADDR_P2PKH_BYTE + chA160


      # First some prep for encryption/decryption, and verify RT encrypt/decrypt
      self.ekey.unlock(self.password)
      iv1 = SecureBinaryData(hash256(sbdPubk.toBinStr())[:16])
      iv2 = SecureBinaryData(hash256(nextPubk.toBinStr())[:16])

      privCrypt1 = self.privACI.encrypt(sbdPriv,    ekeyObj=self.ekey, ivData=iv1)
      privCrypt2 = self.privACI.encrypt(nextPriv,   ekeyObj=self.ekey, ivData=iv2)

      decrypted1 = self.privACI.decrypt(privCrypt1, ekeyObj=self.ekey, ivData=iv1)
      decrypted2 = self.privACI.decrypt(privCrypt2, ekeyObj=self.ekey, ivData=iv2)

      self.assertEqual(sbdPriv, decrypted1)
      self.assertEqual(nextPriv, decrypted2)
      self.ekey.lock()



      abek = ABEK_Generic()
      abek.isWatchOnly = False
      abek.privCryptInfo  = self.privACI
      abek.sbdPrivKeyData = privCrypt1
      abek.sbdPublicKey33 = sbdPubk.copy()
      abek.sbdChaincode   = sbdChain.copy()
      abek.useCompressPub = True
      abek.masterEkeyRef = self.ekey
      abek.privKeyNextUnlock = False
      abek.wltFileRef = self.mockwlt

      self.ekey.unlock(self.password)
      childAbek = abek.spawnChild(nextIdx, fsync=False, privSpawnReqd=True)

      self.assertEqual(childAbek.sbdPrivKeyData, privCrypt2)
      self.assertEqual(childAbek.getPlainPrivKeyCopy(), nextPriv)

      self.assertEqual(childAbek.sbdPublicKey33, nextPubk)
      self.assertEqual(childAbek.sbdChaincode,   nextChain)
      self.assertEqual(childAbek.useCompressPub, True)
      self.assertEqual(childAbek.isUsed, False)
      self.assertEqual(childAbek.privKeyNextUnlock, False)
      self.assertEqual(childAbek.akpParScrAddr, parScrAddr)
      self.assertEqual(childAbek.childIndex, nextIdx)
      self.assertEqual(childAbek.childPoolSize, 5)
      self.assertEqual(childAbek.maxChildren, UINT32_MAX)
      self.assertEqual(childAbek.rawScript, chScript)
      self.assertEqual(childAbek.scrAddrStr, chScrAddr)
      self.assertEqual(childAbek.lowestUnusedChild, 0)
      self.assertEqual(childAbek.nextChildToCalc,   0)
      
      # Check the uniqueID, by spawning another child
      subCh = childAbek.spawnChild(0x7fffffff, fsync=False, forIDCompute=True)
      ch256  = hash256(subCh.getScrAddr())
      firstByte = binary_to_int(ch256[0])
      newFirst  = firstByte ^ binary_to_int(ADDRBYTE)
      uidBin = int_to_binary(newFirst) + ch256[1:6]
      uidB58 = binary_to_base58(uidBin)
      self.assertEqual(childAbek.uniqueIDBin, uidBin)
      self.assertEqual(childAbek.uniqueIDB58, uidB58)

      self.ekey.lock()
      self.assertRaises(WalletLockError, abek.spawnChild, nextIdx, privSpawnReqd=True)

   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testSpawn_CreateNextUnlock(self):
      # Start with this key pair
      sbdPriv  = SecureBinaryData(BIP32TestVectors[1]['seedKey'].toBinStr()[1:])
      sbdPubk  = BIP32TestVectors[1]['seedCompPubKey']
      sbdChain = BIP32TestVectors[1]['seedCC']
      nextIdx  = BIP32TestVectors[1]['nextChild']
      parA160    = hash160(sbdPubk.toBinStr())
      parScript  = hash160_to_p2pkhash_script(parA160)
      parScrAddr = SCRADDR_P2PKH_BYTE + parA160

      # Derive this keypair
      nextPriv  = SecureBinaryData(BIP32TestVectors[2]['seedKey'].toBinStr()[1:])
      nextPubk  = BIP32TestVectors[2]['seedCompPubKey']
      nextChain = BIP32TestVectors[2]['seedCC']
      chA160    = hash160(nextPubk.toBinStr())
      chScript  = hash160_to_p2pkhash_script(chA160)
      chScrAddr = SCRADDR_P2PKH_BYTE + chA160

      # First some prep for encryption/decryption, and verify RT encrypt/decrypt
      self.ekey.unlock(self.password)
      iv1 = SecureBinaryData(hash256(sbdPubk.toBinStr())[:16])
      iv2 = SecureBinaryData(hash256(nextPubk.toBinStr())[:16])

      privCrypt1 = self.privACI.encrypt(sbdPriv,    ekeyObj=self.ekey, ivData=iv1)
      privCrypt2 = self.privACI.encrypt(nextPriv,   ekeyObj=self.ekey, ivData=iv2)

      decrypted1 = self.privACI.decrypt(privCrypt1, ekeyObj=self.ekey, ivData=iv1)
      decrypted2 = self.privACI.decrypt(privCrypt2, ekeyObj=self.ekey, ivData=iv2)

      self.assertEqual(sbdPriv, decrypted1)
      self.assertEqual(nextPriv, decrypted2)
      self.ekey.lock()

      abek = ABEK_Generic()
      abek.isWatchOnly = False
      abek.privCryptInfo  = self.privACI
      abek.sbdPrivKeyData = privCrypt1
      abek.sbdPublicKey33 = sbdPubk.copy()
      abek.sbdChaincode   = sbdChain.copy()
      abek.useCompressPub = True
      abek.masterEkeyRef = self.ekey
      abek.privKeyNextUnlock = False
      abek.wltFileRef = self.mockwlt

      # Now DON'T unlock before spawning
      #self.ekey.unlock(self.password)
      self.ekey.lock()
      childAbek = abek.spawnChild(nextIdx, fsync=False)

      self.assertEqual(childAbek.sbdPublicKey33, nextPubk)
      self.assertEqual(childAbek.sbdChaincode,   nextChain)
      self.assertEqual(childAbek.useCompressPub, True)
      self.assertEqual(childAbek.isUsed, False)

      self.assertEqual(childAbek.getPrivKeyAvailability(), PRIV_KEY_AVAIL.NextUnlock)
      self.assertEqual(childAbek.privKeyNextUnlock, True)

      self.assertEqual(childAbek.akpParScrAddr, parScrAddr)
      self.assertEqual(childAbek.childIndex, nextIdx)
      self.assertEqual(childAbek.childPoolSize, 5)
      self.assertEqual(childAbek.maxChildren, UINT32_MAX)
      self.assertEqual(childAbek.rawScript, chScript)
      self.assertEqual(childAbek.scrAddrStr, chScrAddr)

      runSerUnserRoundTripTest(self, childAbek)



   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testKeyPool_D1_Crypt(self):
      """
      Doesn't test the accuracy of ABEK calculations, only the keypool sizes
      """
      echain = ABEK_StdChainExt()
      mockwlt = MockWalletFile()
      sbdPriv  = SecureBinaryData(BIP32TestVectors[0]['seedKey'].toBinStr()[1:])
      sbdPubk  = BIP32TestVectors[0]['seedCompPubKey']
      sbdChain = BIP32TestVectors[0]['seedCC']

      a160    = hash160(sbdPubk.toBinStr())
      rawScr  = hash160_to_p2pkhash_script(a160)
      scrAddr = SCRADDR_P2PKH_BYTE + a160

      # First some prep for encryption/decryption, and verify outputs
      self.ekey.unlock(self.password)
      iv = SecureBinaryData(hash256(sbdPubk.toBinStr())[:16])
      privCrypt = self.privACI.encrypt(sbdPriv,   ekeyObj=self.ekey, ivData=iv)
      decrypted = self.privACI.decrypt(privCrypt, ekeyObj=self.ekey, ivData=iv)
      self.assertEqual(sbdPriv, decrypted)
      self.ekey.lock()


      t = long(RightNow())
      echain.initializeAKP(isWatchOnly=False,
                           isAkpRootRoot=False,
                           privCryptInfo=self.privACI,
                           sbdPrivKeyData=privCrypt,
                           sbdPublicKey33=sbdPubk,
                           sbdChaincode=sbdChain,
                           privKeyNextUnlock=False,
                           akpParScrAddr=None,
                           childIndex=None,
                           useCompressPub=True,
                           isUsed=True,
                           notForDirectUse=False,
                           keyBornTime=t,
                           keyBornBlock=t)

      echain.masterEkeyRef = self.ekey
      echain.wltFileRef = mockwlt
      echain.setChildPoolSize(5)

      
      self.assertEqual(echain.isWatchOnly,    False)
      self.assertEqual(echain.sbdPublicKey33, sbdPubk)
      self.assertEqual(echain.sbdChaincode,   sbdChain)

      #self.assertEqual(echain.sbdPrivKeyData, sbdPriv)
      self.assertRaises(WalletLockError, echain.getPlainPrivKeyCopy)

      self.assertEqual(echain.lowestUnusedChild,   0)
      self.assertEqual(echain.nextChildToCalc,     0)
      self.assertEqual(echain.childPoolSize,       5)

      self.ekey.unlock(self.password)
      echain.fillKeyPool()

      self.assertEqual(echain.lowestUnusedChild,  0)
      self.assertEqual(echain.nextChildToCalc,    5)
      self.assertEqual(echain.childPoolSize,      5)

      # Check doing some sanity checking on the children, not accuracy check
      for i,ch in echain.akpChildByIndex.iteritems():
         priv = ch.getPlainPrivKeyCopy()
         pub = CryptoECDSA().ComputePublicKey(priv)
         pub = CryptoECDSA().CompressPoint(pub)
         self.assertEqual(pub, ch.sbdPublicKey33)
         self.assertEqual(ch.masterEkeyRef, self.ekey)
         self.assertTrue(ch.privCryptInfo.useEncryption())
         self.assertEqual(ch.getPrivKeyAvailability(), PRIV_KEY_AVAIL.Available)

      


   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testKeyPool_D2_Crypt(self):
      """
      Doesn't test the accuracy of ABEK calculations, only the keypool sizes
      """
      mockwlt  = MockWalletFile()
      awlt   = ABEK_StdWallet()

      sbdPriv  = SecureBinaryData(BIP32TestVectors[0]['seedKey'].toBinStr()[1:])
      sbdPubk  = BIP32TestVectors[0]['seedCompPubKey']
      sbdChain = BIP32TestVectors[0]['seedCC']

      # First some prep for encryption/decryption, and verify outputs
      self.ekey.unlock(self.password)
      iv = SecureBinaryData(hash256(sbdPubk.toBinStr())[:16])
      privCrypt = self.privACI.encrypt(sbdPriv,   ekeyObj=self.ekey, ivData=iv)
      decrypted = self.privACI.decrypt(privCrypt, ekeyObj=self.ekey, ivData=iv)
      self.assertEqual(sbdPriv, decrypted)
      self.ekey.lock()

      t = long(RightNow())
      awlt.initializeAKP(isWatchOnly=False,
                         isAkpRootRoot=False,
                         privCryptInfo=self.privACI,
                         sbdPrivKeyData=privCrypt,
                         sbdPublicKey33=sbdPubk,
                         sbdChaincode=sbdChain,
                         privKeyNextUnlock=False,
                         akpParScrAddr=None,
                         childIndex=None,
                         useCompressPub=True,
                         isUsed=True,
                         notForDirectUse=False,
                         keyBornTime=t,
                         keyBornBlock=t)

      awlt.masterEkeyRef = self.ekey
      awlt.wltFileRef = mockwlt
      awlt.setChildPoolSize(5)

      
      self.assertEqual(awlt.isWatchOnly,    False)
      self.assertEqual(awlt.sbdPublicKey33, sbdPubk)
      self.assertEqual(awlt.sbdChaincode,   sbdChain)

      #self.assertEqual(awlt.sbdPrivKeyData, sbdPriv)
      #self.assertEqual(awlt.getPlainPrivKeyCopy(), sbdPriv)

      self.assertEqual(awlt.lowestUnusedChild, 0)
      self.assertEqual(awlt.nextChildToCalc,   0)

      self.ekey.unlock(self.password)
      awlt.fillKeyPool()

      self.assertEqual(awlt.lowestUnusedChild,  0)
      self.assertEqual(awlt.nextChildToCalc,    2)
      self.assertEqual(len(awlt.akpChildByIndex), 2)
      self.assertEqual(awlt.akpChildByIndex[0].__class__, ABEK_StdChainExt)
      self.assertEqual(awlt.akpChildByIndex[1].__class__, ABEK_StdChainInt)
      self.assertEqual(awlt.akpChildByIndex[0].childPoolSize, 
                                    DEFAULT_CHILDPOOLSIZE['ABEK_StdChainExt'])
      self.assertEqual(awlt.akpChildByIndex[1].childPoolSize, 
                                    DEFAULT_CHILDPOOLSIZE['ABEK_StdChainInt'])

      # Check doing some sanity checking on the children, not accuracy check
      for i,ch in awlt.akpChildByIndex.iteritems():
         for j,ch2 in ch.akpChildByIndex.iteritems():
            priv = ch.getPlainPrivKeyCopy()
            pub = CryptoECDSA().ComputePublicKey(priv)
            pub = CryptoECDSA().CompressPoint(pub)
            self.assertEqual(pub, ch.sbdPublicKey33)
            self.assertEqual(ch.masterEkeyRef, self.ekey)
            self.assertTrue(ch.privCryptInfo.useEncryption())
            self.assertEqual(ch.getPrivKeyAvailability(), PRIV_KEY_AVAIL.Available)

      runSerUnserRoundTripTest(self, awlt)


   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testABEK_seedCalc_Crypt(self):
      mockwlt  = MockWalletFile()
      abekSeed = ABEK_StdBip32Seed()
      abekSeed.setWalletAndCryptInfo(mockwlt, self.privACI, self.ekey)

      WRONGPUBK = SecureBinaryData('\x03' + '\xaa'*32)

      self.ekey.lock()
      self.assertRaises(WalletLockError, abekSeed.initializeFromSeed, \
                                       SEEDTEST[0]['Seed'], fillPool=False)
      self.ekey.unlock(self.password)
   
      abekSeed.initializeFromSeed(SEEDTEST[0]['Seed'], fillPool=False)
      self.assertEqual(abekSeed.getPlainPrivKeyCopy(), SEEDTEST[0]['Priv'])
      self.assertEqual(abekSeed.sbdPublicKey33,        SEEDTEST[0]['Pubk'])
      self.assertEqual(abekSeed.sbdChaincode,          SEEDTEST[0]['Chain'])
      self.assertEqual(abekSeed.getPlainSeedCopy(),    SEEDTEST[0]['Seed'])
      self.assertFalse(abekSeed.sbdPrivKeyData == SEEDTEST[0]['Priv'])
      self.assertFalse(abekSeed.sbdSeedData    == SEEDTEST[0]['Seed'])
      self.assertEqual(abekSeed.seedCryptInfo.keySource, self.ekey.ekeyID)
      
      abekSeed.initializeFromSeed(SEEDTEST[0]['Seed'], 
                        verifyPub=SEEDTEST[0]['Pubk'], fillPool=False)
      self.assertEqual(abekSeed.getPlainPrivKeyCopy(), SEEDTEST[0]['Priv'])
      self.assertEqual(abekSeed.sbdPublicKey33,        SEEDTEST[0]['Pubk'])
      self.assertEqual(abekSeed.sbdChaincode,          SEEDTEST[0]['Chain'])
      self.assertEqual(abekSeed.getPlainSeedCopy(),    SEEDTEST[0]['Seed'])
      self.assertFalse(abekSeed.sbdPrivKeyData == SEEDTEST[0]['Priv'])
      self.assertFalse(abekSeed.sbdSeedData    == SEEDTEST[0]['Seed'])
      self.assertEqual(abekSeed.seedCryptInfo.keySource, self.ekey.ekeyID)

      self.assertRaises(KeyDataError, abekSeed.initializeFromSeed, 
                        SEEDTEST[0]['Seed'], verifyPub=WRONGPUBK)



      abekSeed.initializeFromSeed(SEEDTEST[1]['Seed'], fillPool=False)
      self.assertEqual(abekSeed.getPlainPrivKeyCopy(), SEEDTEST[1]['Priv'])
      self.assertEqual(abekSeed.sbdPublicKey33,        SEEDTEST[1]['Pubk'])
      self.assertEqual(abekSeed.sbdChaincode,          SEEDTEST[1]['Chain'])
      self.assertEqual(abekSeed.getPlainSeedCopy(),    SEEDTEST[1]['Seed'])
      self.assertFalse(abekSeed.sbdPrivKeyData == SEEDTEST[0]['Priv'])
      self.assertFalse(abekSeed.sbdSeedData    == SEEDTEST[0]['Seed'])
      self.assertEqual(abekSeed.seedCryptInfo.keySource, self.ekey.ekeyID)
      
      abekSeed.initializeFromSeed(SEEDTEST[1]['Seed'], 
                        verifyPub=SEEDTEST[1]['Pubk'], fillPool=False)
      self.assertEqual(abekSeed.getPlainPrivKeyCopy(), SEEDTEST[1]['Priv'])
      self.assertEqual(abekSeed.sbdPublicKey33,        SEEDTEST[1]['Pubk'])
      self.assertEqual(abekSeed.sbdChaincode,          SEEDTEST[1]['Chain'])
      self.assertEqual(abekSeed.getPlainSeedCopy(),    SEEDTEST[1]['Seed'])
      self.assertFalse(abekSeed.sbdPrivKeyData == SEEDTEST[0]['Priv'])
      self.assertFalse(abekSeed.sbdSeedData    == SEEDTEST[0]['Seed'])
      self.assertEqual(abekSeed.seedCryptInfo.keySource, self.ekey.ekeyID)

      self.assertRaises(KeyDataError, abekSeed.initializeFromSeed, 
                        SEEDTEST[1]['Seed'], verifyPub=WRONGPUBK)

      runSerUnserRoundTripTest(self, abekSeed)

   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testABEK_newSeed_Crypt(self):
      mockwlt  = MockWalletFile()
      abekSeed = ABEK_StdBip32Seed()
      abekSeed.wltFileRef = mockwlt
      abekSeed.masterEkeyRef = self.ekey
   
      abekSeed.privCryptInfo = self.privACI

      # Extra entropy should be pulled from external sources!  Such as
      # system files, screenshots, uninitialized RAM states... only do
      # it the following way for testing!
      entropy = SecureBinaryData().GenerateRandom(16)

      self.ekey.unlock(self.password)
      # Should fail for seed being too small
      self.assertRaises(KeyDataError, abekSeed.createNewSeed, 8, entropy)

      # Should fail for not supplying extra entropy
      self.assertRaises(TypeError, abekSeed.createNewSeed, 16, None)

      # Should fail for not supplying extra entropy
      self.assertRaises(KeyDataError, abekSeed.createNewSeed, 16, NULLSBD())


      self.ekey.lock()
      for seedsz in [16, 20, 64]:
         self.assertRaises(WalletLockError, abekSeed.createNewSeed, seedsz, entropy, fillPool=False)

      self.ekey.unlock(self.password)
      for seedsz in [16, 20, 64]:
         abekSeed.createNewSeed(seedsz, entropy, fillPool=False)

      runSerUnserRoundTripTest(self, abekSeed)


   ################################################################################
   def test_FillKeyPool_NextUnlock(self):
      mockwlt  = MockWalletFile()

      
      # Do this three times, once unencrypted, once encrypted-but-unlocked, then
      # build the same tree encrypted-and-locked then trigger resolveNextUnlock
      # We use ABEK_SoftBip32Seed since it is real wallet structure with no
      # hardened derivations

      # Generate entropy once for all seeds
      sbdSeed = SecureBinaryData('\xfc\x3d'*8)

      abekSeedBase = ABEK_SoftBip32Seed()
      abekSeedBase.setWalletAndCryptInfo(mockwlt, None)
      abekSeedBase.initializeFromSeed(sbdSeed, fillPool=False)
      abekSeedBase.fillKeyPool()

      
      abekSeedCrypt = ABEK_SoftBip32Seed()
      abekSeedCrypt.setWalletAndCryptInfo(mockwlt, self.privACI, self.ekey)
      self.ekey.unlock(self.password)
      abekSeedCrypt.initializeFromSeed(sbdSeed, fillPool=False)
      abekSeedCrypt.fillKeyPool()

      
      abekSeedNU = ABEK_SoftBip32Seed()
      abekSeedNU.setWalletAndCryptInfo(mockwlt, self.privACI, self.ekey)
      abekSeedNU.initializeFromSeed(sbdSeed, fillPool=False)
      self.ekey.lock(self.password)
      abekSeedNU.fillKeyPool()

      def cmpNodes(a,b,c, withpriv):
         self.assertTrue(a.sbdPublicKey33 == b.sbdPublicKey33 == c.sbdPublicKey33)
         self.assertTrue(a.sbdChaincode   == b.sbdChaincode   == c.sbdChaincode  )
         privMatch = True
         if withpriv:
            self.assertTrue( a.getPlainPrivKeyCopy() == \
                             b.getPlainPrivKeyCopy() == \
                             c.getPlainPrivKeyCopy()  )
         else:
            self.assertTrue(c.getPrivKeyAvailability()==PRIV_KEY_AVAIL.NextUnlock)

         

      
      def cmpTrees(withPriv):
         for i,lvl0_child in abekSeedBase.akpChildByIndex.iteritems():
            wa = abekSeedBase.getChildByIndex(i)
            wb = abekSeedCrypt.getChildByIndex(i)
            wc = abekSeedNU.getChildByIndex(i)
            cmpNodes(wa, wb, wc, withPriv)
            for j,lvl1_child in lvl0_child.akpChildByIndex.iteritems():
               ca = wa.getChildByIndex(j)
               cb = wb.getChildByIndex(j)
               cc = wc.getChildByIndex(j)
               cmpNodes(ca, cb, cc, withPriv)
               for k,lvl2_child in lvl1_child.akpChildByIndex.iteritems():
                  aa = ca.getChildByIndex(k)
                  ab = cb.getChildByIndex(k)
                  ac = cc.getChildByIndex(k)
                  cmpNodes(aa, ab, ac, withPriv)


      cmpTrees(False)

      # Check that getChildByPath is only returning pre-generated addrs
      self.assertRaises(ChildDeriveError, abekSeedNU.getChildByPath, [10,10,10], False)

      # Two passes, first time nextUnlock should be True, unlock, then shoudl be false
      for nu in [True, False]:
         expectAvail = PRIV_KEY_AVAIL.NextUnlock if nu else PRIV_KEY_AVAIL.Available 

         abek = abekSeedNU

         abek = abek.getChildByIndex(1);  
         self.assertEqual(abek.getPrivKeyAvailability(), expectAvail)
         runSerUnserRoundTripTest(self, abek)

         abek = abek.getChildByIndex(0);  
         self.assertEqual(abek.getPrivKeyAvailability(), expectAvail)
         runSerUnserRoundTripTest(self, abek)

         abek = abek.getChildByIndex(4);  
         self.assertEqual(abek.getPrivKeyAvailability(), expectAvail)
         runSerUnserRoundTripTest(self, abek)

         cmp104a = abekSeedBase.getChildByPath([1,0,4])
         cmp104b = abekSeedCrypt.getChildByPath([1,0,4])
         cmpNodes(cmp104a, cmp104b, abek, not nu) 


         # Before and after, [1,0,5] should remain in nextUnlock state
         abek105 = abekSeedNU.getChildByPath([1,0,5])
         self.assertEqual(abek105.getPrivKeyAvailability(), PRIV_KEY_AVAIL.NextUnlock)

         # Before and after, [0] should remain in nextUnlock state
         abek000 = abekSeedNU.getChildByPath([0])
         self.assertEqual(abek000.getPrivKeyAvailability(), PRIV_KEY_AVAIL.NextUnlock)

         if not nu:
            self.assertEqual(abek.sbdPrivKeyData,        cmp104b.sbdPrivKeyData)
            self.assertEqual(abek.getPlainPrivKeyCopy(), cmp104b.getPlainPrivKeyCopy())
         
         self.ekey.unlock(self.password)
         abek.resolveNextUnlockFlag()
      
      
      runSerUnserRoundTripTest(self, abek105)

      abek105 = abekSeedNU.getChildByPath([1,0,5])
      self.assertEqual(abek105.getPrivKeyAvailability(), PRIV_KEY_AVAIL.NextUnlock)
      abek105.getPlainPrivKeyCopy()
      self.assertEqual(abek105.getPrivKeyAvailability(), PRIV_KEY_AVAIL.Available)
      self.ekey.lock()
      self.assertEqual(abek105.getPrivKeyAvailability(), PRIV_KEY_AVAIL.NeedDecrypt)

      runSerUnserRoundTripTest(self, abek105)



   ################################################################################
   def test_FillKeyPool_NextUnlock_MKEY(self):
      """
      An exact copy of the test above, but using multi-password encryption
      key instead of self.ekey.  This test confirms that multi-pwd encryption
      is plug-n-play with anything that works with ekey
      """
      passwordList = [SecureBinaryData(a) for a in ['hello','gday','goodbye']]
      master32 = SecureBinaryData('\x3e'*32)
      randomiv = SecureBinaryData('\x7d'*8)
      lbls = ['']*3

      # Create a KDF to be used for encryption key password
      
      kdfList = []
      kdfSalt = ['\xaa'*32, '\xbb'*32, '\x33'*32]
      for i in range(3):
         kdfList.append(KdfObject('ROMIXOV2', 
                                  memReqd=32*KILOBYTE,
                                  numIter=1, 
                                  salt=SecureBinaryData(kdfSalt[i])))

      # Create the new master encryption key to be used to encrypt priv keys
      mkey = MultiPwdEncryptionKey().createNewMasterKey( \
                           kdfList, 'AE256CBC', 2, passwordList, lbls,
                           preGenKey=master32, preGenIV8List=[randomiv]*3)

      # This will be attached to each ABEK object, to define its encryption
      privACI = ArmoryCryptInfo(NULLKDF, 'AE256CBC', mkey.ekeyID, 'PUBKEY20')


      unlockList = [[MPEK_FRAG_TYPE.PASSWORD, passwordList[0]],
                    [MPEK_FRAG_TYPE.NONE,     ''],
                    [MPEK_FRAG_TYPE.PASSWORD, passwordList[2]]]
      
      # Do this three times, once unencrypted, once encrypted-but-unlocked, then
      # build the same tree encrypted-and-locked then trigger resolveNextUnlock
      # We use ABEK_SoftBip32Seed since it is real wallet structure with no
      # hardened derivations

      # Generate entropy once for all seeds
      sbdSeed = SecureBinaryData('\xfc\x3d'*8)

      abekSeedBase = ABEK_SoftBip32Seed()
      abekSeedBase.setWalletAndCryptInfo(self.mockwlt, None)
      abekSeedBase.initializeFromSeed(sbdSeed, fillPool=False)
      abekSeedBase.fillKeyPool()

      
      abekSeedCrypt = ABEK_SoftBip32Seed()
      abekSeedCrypt.setWalletAndCryptInfo(self.mockwlt, privACI, mkey)
      mkey.unlock(unlockList)
      abekSeedCrypt.initializeFromSeed(sbdSeed, fillPool=False)
      abekSeedCrypt.fillKeyPool()

      
      abekSeedNU = ABEK_SoftBip32Seed()
      abekSeedNU.setWalletAndCryptInfo(self.mockwlt, privACI, mkey)
      abekSeedNU.initializeFromSeed(sbdSeed, fillPool=False)
      mkey.lock()
      abekSeedNU.fillKeyPool()

      def cmpNodes(a,b,c, withpriv):
         self.assertTrue(a.sbdPublicKey33 == b.sbdPublicKey33 == c.sbdPublicKey33)
         self.assertTrue(a.sbdChaincode   == b.sbdChaincode   == c.sbdChaincode  )
         privMatch = True
         if withpriv:
            self.assertTrue( a.getPlainPrivKeyCopy() == \
                             b.getPlainPrivKeyCopy() == \
                             c.getPlainPrivKeyCopy()  )
         else:
            self.assertTrue(c.getPrivKeyAvailability()==PRIV_KEY_AVAIL.NextUnlock)

         

      
      def cmpTrees(withPriv):
         for i,lvl0_child in abekSeedBase.akpChildByIndex.iteritems():
            wa = abekSeedBase.getChildByIndex(i)
            wb = abekSeedCrypt.getChildByIndex(i)
            wc = abekSeedNU.getChildByIndex(i)
            cmpNodes(wa, wb, wc, withPriv)
            for j,lvl1_child in lvl0_child.akpChildByIndex.iteritems():
               ca = wa.getChildByIndex(j)
               cb = wb.getChildByIndex(j)
               cc = wc.getChildByIndex(j)
               cmpNodes(ca, cb, cc, withPriv)
               for k,lvl2_child in lvl1_child.akpChildByIndex.iteritems():
                  aa = ca.getChildByIndex(k)
                  ab = cb.getChildByIndex(k)
                  ac = cc.getChildByIndex(k)
                  cmpNodes(aa, ab, ac, withPriv)


      cmpTrees(False)

      # Check that getChildByPath is only returning pre-generated addrs
      self.assertRaises(ChildDeriveError, abekSeedNU.getChildByPath, [10,10,10], False)

      # Two passes, first time nextUnlock should be True, unlock, then shoudl be false
      for nu in [True, False]:
         expectAvail = PRIV_KEY_AVAIL.NextUnlock if nu else PRIV_KEY_AVAIL.Available 

         abek = abekSeedNU

         abek = abek.getChildByIndex(1);  
         self.assertEqual(abek.getPrivKeyAvailability(), expectAvail)
         runSerUnserRoundTripTest(self, abek)

         abek = abek.getChildByIndex(0);  
         self.assertEqual(abek.getPrivKeyAvailability(), expectAvail)
         runSerUnserRoundTripTest(self, abek)

         abek = abek.getChildByIndex(4);  
         self.assertEqual(abek.getPrivKeyAvailability(), expectAvail)
         runSerUnserRoundTripTest(self, abek)

         cmp104a = abekSeedBase.getChildByPath([1,0,4])
         cmp104b = abekSeedCrypt.getChildByPath([1,0,4])
         cmpNodes(cmp104a, cmp104b, abek, not nu) 


         # Before and after, [1,0,5] should remain in nextUnlock state
         abek105 = abekSeedNU.getChildByPath([1,0,5])
         self.assertEqual(abek105.getPrivKeyAvailability(), PRIV_KEY_AVAIL.NextUnlock)

         # Before and after, [0] should remain in nextUnlock state
         abek000 = abekSeedNU.getChildByPath([0])
         self.assertEqual(abek000.getPrivKeyAvailability(), PRIV_KEY_AVAIL.NextUnlock)

         if not nu:
            self.assertEqual(abek.sbdPrivKeyData,        cmp104b.sbdPrivKeyData)
            self.assertEqual(abek.getPlainPrivKeyCopy(), cmp104b.getPlainPrivKeyCopy())
         
         mkey.unlock(unlockList)
         abek.resolveNextUnlockFlag()
      
      
      runSerUnserRoundTripTest(self, abek105)

      abek105 = abekSeedNU.getChildByPath([1,0,5])
      self.assertEqual(abek105.getPrivKeyAvailability(), PRIV_KEY_AVAIL.NextUnlock)
      abek105.getPlainPrivKeyCopy()
      self.assertEqual(abek105.getPrivKeyAvailability(), PRIV_KEY_AVAIL.Available)
      mkey.lock()
      self.assertEqual(abek105.getPrivKeyAvailability(), PRIV_KEY_AVAIL.NeedDecrypt)

      runSerUnserRoundTripTest(self, abek105)




################################################################################
################################################################################
#
# Armory Wallet 1.35 (backport) tests
#
################################################################################
################################################################################
class Armory135Tests(unittest.TestCase):

   #############################################################################
   def setUp(self):
      self.rootID    = 'zrPzapKR'
      self.rootLine1 = 'okkn weod aajf skrs jdrj rafa gjtr saho eari'.replace(' ','')
      self.rootLine2 = 'rdeg jaah soea ugas jeot niua jdeg hkou gsih'.replace(' ','')
      self.binSeed   = readSixteenEasyBytes(self.rootLine1)[0] + \
                       readSixteenEasyBytes(self.rootLine2)[0]
      self.chaincode = DeriveChaincodeFromRootKey_135(SecureBinaryData(self.binSeed))

      # Use for the 1.35a seed tests: same root but non-priv-derived chain
      self.altChain1 = 'okkn weod aajf skrs jdrj rafa gjtr saho eari'.replace(' ','')
      self.altChain2 = 'rdeg jaah soea ugas jeot niua jdeg hkou gsih'.replace(' ','')
      self.binAltChn = readSixteenEasyBytes(self.altChain1)[0] + \
                       readSixteenEasyBytes(self.altChain2)[0]

      self.keyList = {}

      self.keyList[0] = { \
         'AddrStr': '13QVfpnE7TWAnkGGpHak1Z9cJVQWTZrYqb',
         'PrivB58': '5JWFgYDRyCqxMcXprSf84RAfPC4p6x2eifXxNwHuqeL137JC11A',
         'PubKeyX': '1a84426c38a0099975d683365436ee3eedaf2c9589c44635aa3808ede5f87081',
         'PubKeyY': '6a905e1f3055c0982307951e5e4150349c5c98a644f3da9aeef9c80f103cf2af' }
      self.keyList[1] = { \
         'AddrStr': '1Dy4cGbv3KKm4EhQYVKvUJQfy6sgmGR4ii',
         'PrivB58': '5KMBzjqDE8dXxtvRaY8dGHnMUNyE6uonDwKgeG44XBsngqTYkf9',
         'PubKeyX': '6c23cc6208a1f6daaa196ba6e763b445555ada6315ebf9465a0b9cb49e813e3a',
         'PubKeyY': '341eb33ed738b6a1ac6a57526a80af2e6841dcf71f287dbe721dd4486d9cf8c4' }
      self.keyList[2] = { \
         'AddrStr': '1BKG36rBdxiYNRQbLCYfPzi6Cf4pW2aRxQ',
         'PrivB58': '5KhpN6mmdiVcKmZtPjqfC41Af7181Dj4JadyU7dDLVefdPcMbZi',
         'PubKeyX': 'eb013f8047ad532a8bcc4d4f69a62887ce82afb574d7fb8a326b9bab82d240fa',
         'PubKeyY': 'a8fdcd604105292cb04c7707da5e42300bc418654f8ffc94e2c83bd5a54e09e2' }
      self.keyList[3] = { \
         'AddrStr': '1NhZfoXMLmohuvAh7Ks67JMx6mpcVq2FCa',
         'PrivB58': '5KaxXWwQgFcp3d5Bqd58xvtBDN8FEPQeRZJDpyxY5LTZ5ALZHE3',
         'PubKeyX': 'd6e6d3031d5d3de48293d97590f5b697089e8e6b40e919a68e2a07c300c1256b',
         'PubKeyY': '3d9b428e0ef9f73bd81c9388e1d8702f477138ca444eed57370d0e31ba9bafe5' }
      self.keyList[4] = { \
         'AddrStr': '1GHvHhrUBL5mMryscJa9uzDnPXeEpqU7Tn',
         'PrivB58': '5Jb4u9bpWDv19y6hu6nAE7cDdQoUrJMoyrwGDjPxMKo8oxULSdn',
         'PubKeyX': 'e40d3923bfffad0cdc6d6a3341c8e669beb1264b86cbfd21229ca8a74cf53ca5',
         'PubKeyY': '587b7a9b18b648cd421d17d45d05e8fc647f7ea02f61b670a2d4c2012e3b717f' }
      self.keyList[5] = { \
         'AddrStr': '1DdAdN2VQXg52YqDssZ4o6XprVgEB4Evpj',
         'PrivB58': '5JxD9BrDhCgWEKfEUG2FBcAk1D667G97hNREg81M5Qzgi9CAgdD',
         'PubKeyX': '7e043899f917288db2962819cd78c8328efb6dd172b9cbe1bfaaf8d745fd3e99',
         'PubKeyY': '746b29150ff3828556595291419d579c824ac2879d83fb3d51d5efea5de4715d' }
      self.keyList[6] = { \
         'AddrStr': '1K9QBzxv2jL7ftMkJ9jghr8dJgZ6u6zhHR',
         'PrivB58': '5K7GHu48sqxnYNhiMNVVoeh8WXnnerrNhL2TWocHngaP8zyUPAr',
         'PubKeyX': 'bbc9cd69dd6977b08d7916c0da81208df0b8a491b0897ca482bd42df47102d6b',
         'PubKeyY': 'f0318b3298ba93831df82b7ce51da5e0e8647a3ecd994f600a84834b424ed2b8' }

      # For reference, here's the first 6 ScrAddrs
      # ROOT: 00ef2ba030696d99d945fea3990e4213c62d042ddd
      # 0: 001a61c02c74328db5122fa9c1d4917f05de86a8c2
      # 1: 008e3bd0ad4a85b3fd3d4998397e8da93635aab664
      # 2: 0071254bf82804253fbafaf49b45fe7f85eba0d3d5
      # 3: 00ee068cf6c7b6fc77326cba37d621aebe834a5257
      # 4: 00a7bd0654e2bebf43acfab6b75a4619e70464cce8
      # 5: 008a78852b767f5b5dc8567dbfa53214e914430789

      self.password = SecureBinaryData('hello')
      master32 = SecureBinaryData('\x3e'*32)
      randomiv = SecureBinaryData('\x7d'*8)
      # Create a KDF to be used for encryption key password
      self.kdf = KdfObject('ROMIXOV2', memReqd=32*KILOBYTE,
                                       numIter=1, 
                                       salt=SecureBinaryData('\x21'*32))

      # Create the new master encryption key to be used to encrypt priv keys
      self.ekey = EncryptionKey().createNewMasterKey(self.kdf, 'AE256CBC', 
                     self.password, preGenKey=master32, preGenIV8=randomiv)

      # This will be attached to each ABEK object, to define its encryption
      self.privACI = ArmoryCryptInfo(NULLKDF, 'AE256CBC', 
                                 self.ekey.ekeyID, 'PUBKEY20')

      self.ekey.unlock(self.password)
      for idx,imap in self.keyList.iteritems():
         imap['PrivKey']   = SecureBinaryData(parsePrivateKeyData(imap['PrivB58'])[0])
         imap['PubKey']    = SecureBinaryData(hex_to_binary('04' + imap['PubKeyX'] + imap['PubKeyY']))
         imap['Chaincode'] = self.chaincode.copy()
         imap['ScrAddr']   = SCRADDR_P2PKH_BYTE + hash160(imap['PubKey'].toBinStr())

         # Compute encrypted version of privkey with associated (compr) pubkey
         pub33 = CryptoECDSA().CompressPoint(imap['PubKey'])
         iv = SecureBinaryData(hash256(pub33.toBinStr())[:16])
         imap['PrivCrypt'] = self.privACI.encrypt(imap['PrivKey'], ekeyObj=self.ekey, ivData=iv)
      self.ekey.lock()
      
   #############################################################################
   def tearDown(self):
      pass
      

   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testInitA135(self):
      #leaf = makeABEKGenericClass()
      a135 = Armory135KeyPair()
         
      self.assertEqual(a135.isWatchOnly, False)
      self.assertEqual(a135.sbdPrivKeyData, NULLSBD())
      self.assertEqual(a135.sbdPublicKey33, NULLSBD())
      self.assertEqual(a135.sbdChaincode, NULLSBD())
      self.assertEqual(a135.useCompressPub, False)
      self.assertEqual(a135.isUsed, False)
      self.assertEqual(a135.keyBornTime, 0)
      self.assertEqual(a135.keyBornBlock, 0)
      self.assertEqual(a135.privKeyNextUnlock, False)
      self.assertEqual(a135.childPoolSize, 1)
      self.assertEqual(a135.maxChildren, 1)
      self.assertEqual(a135.rawScript, None)
      self.assertEqual(a135.scrAddrStr, None)
      self.assertEqual(a135.uniqueIDBin, None)
      self.assertEqual(a135.uniqueIDB58, None)
      self.assertEqual(a135.akpChildByIndex, {})
      self.assertEqual(a135.akpChildByScrAddr, {})
      self.assertEqual(a135.lowestUnusedChild, 0)
      self.assertEqual(a135.nextChildToCalc,   0)
      self.assertEqual(a135.akpParentRef, None)
      self.assertEqual(a135.masterEkeyRef, None)

      self.assertEqual(a135.getName(), 'Armory135KeyPair')
      self.assertEqual(a135.getPrivKeyAvailability(), PRIV_KEY_AVAIL.Uninit)

      self.assertEqual(a135.chainIndex, None)
      self.assertEqual(a135.childIndex, 0)

      # WalletEntry fields
      self.assertEqual(a135.wltFileRef, None)
      self.assertEqual(a135.wltByteLoc, None)
      self.assertEqual(a135.wltEntrySz, None)
      self.assertEqual(a135.isRequired, False)
      self.assertEqual(a135.parEntryID, None)
      self.assertEqual(a135.outerCrypt.serialize(), NULLCRYPTINFO().serialize())
      self.assertEqual(a135.serPayload, None)
      self.assertEqual(a135.defaultPad, 256)
      self.assertEqual(a135.wltParentRef, None)
      self.assertEqual(a135.wltChildRefs, [])
      self.assertEqual(a135.outerEkeyRef, None)
      self.assertEqual(a135.isOpaque,        False)
      self.assertEqual(a135.isUnrecognized,  False)
      self.assertEqual(a135.isUnrecoverable, False)
      self.assertEqual(a135.isDeleted,       False)
      self.assertEqual(a135.isDisabled,      False)
      self.assertEqual(a135.needFsync,       False)

      self.assertRaises(UninitializedError, a135.serialize)


   #############################################################################
   def testInitFromSeed32(self):
      seed = SecureBinaryData(self.binSeed)

      a135rt = Armory135Root()
      a135rt.privCryptInfo = NULLCRYPTINFO()
      a135rt.childPoolSize = 3
      a135rt.initializeFromSeed(seed, fillPool=False)

      self.assertEqual(a135rt.sbdSeedData.toHexStr(), '') # supposed to be empty
      self.assertEqual(a135rt.privCryptInfo.serialize(), NULLCRYPTINFO().serialize())
      self.assertEqual(a135rt.privKeyNextUnlock, False)

      self.assertEqual(a135rt.getPlainSeedCopy(), seed)
      self.assertEqual(a135rt.getUniqueIDB58(), self.rootID)

      self.assertEqual(a135rt.rootLowestUnused, 0)
      self.assertEqual(a135rt.rootNextToCalc,   0)

      runSerUnserRoundTripTest(self, a135rt)

   #############################################################################
   def testInitFromSeed64(self):
      seed = SecureBinaryData(self.binSeed + self.binAltChn)

      a135rt = Armory135Root()
      a135rt.privCryptInfo = NULLCRYPTINFO()
      a135rt.childPoolSize = 3
      a135rt.initializeFromSeed(seed, fillPool=False)

      self.assertEqual(a135rt.sbdSeedData.toHexStr(), '') # supposed to be empty
      self.assertEqual(a135rt.privCryptInfo.serialize(), NULLCRYPTINFO().serialize())
      self.assertEqual(a135rt.privKeyNextUnlock, False)

      self.assertEqual(a135rt.getPlainSeedCopy().toHexStr(), seed.toHexStr())
      self.assertEqual(a135rt.sbdChaincode.toBinStr(), self.binAltChn)
      self.assertEqual(a135rt.getUniqueIDB58(), '2tyiWrmKd') # diff chain->diff id

      self.assertEqual(a135rt.rootLowestUnused, 0)
      self.assertEqual(a135rt.rootNextToCalc,   0)

      runSerUnserRoundTripTest(self, a135rt)


   #############################################################################
   def testSpawnA135(self):

      for WO in [False, True]:
         a135 = Armory135KeyPair()
         mockwlt = MockWalletFile()

         seed = SecureBinaryData(self.binSeed)
         a135rt = Armory135Root()
         a135rt.setWalletAndCryptInfo(mockwlt, None)
         a135rt.childPoolSize = 3
         a135rt.initializeFromSeed(seed, fillPool=False)

         if WO:
            a135rt.wipePrivateData()


         a135 = a135rt.spawnChild()
         self.assertEqual(a135rt.rootLowestUnused, 0)
         self.assertEqual(a135rt.rootNextToCalc,   1)

         prevScrAddr = a135rt.getScrAddr()
         rootScrAddr = a135rt.getScrAddr()

         kidx = 0
         while kidx+1 in self.keyList:
   
            pub65 = self.keyList[kidx]['PubKey']
            a160  = hash160(pub65.toBinStr())
   
            expectPriv   = self.keyList[kidx]['PrivKey'].copy()
            expectPub    = CryptoECDSA().CompressPoint(pub65)
            expectChain  = self.chaincode.copy()
            expectScript = hash160_to_p2pkhash_script(a160)
            expectScrAddr= script_to_scrAddr(expectScript)
            self.assertEqual(expectScrAddr, self.keyList[kidx]['ScrAddr'])

            if not WO:
               self.assertEqual(a135.sbdPrivKeyData, expectPriv)
               self.assertEqual(a135.getPlainPrivKeyCopy(), expectPriv)
               self.assertEqual(a135.getSerializedPrivKey('bin'), expectPriv.toBinStr())
               self.assertEqual(a135.getSerializedPrivKey('hex'), expectPriv.toHexStr())
               self.assertEqual(a135.getSerializedPrivKey('sipa'), encodePrivKeyBase58(expectPriv.toBinStr()))
            else:
               self.assertEqual(a135.sbdPrivKeyData, NULLSBD())
   
            self.assertEqual(a135.isWatchOnly, WO)
            self.assertEqual(a135.sbdPublicKey33, expectPub)
            self.assertEqual(a135.getSerializedPubKey('hex'), pub65.toHexStr())
            self.assertEqual(a135.getSerializedPubKey('bin'), pub65.toBinStr())
            self.assertEqual(a135.sbdChaincode,   expectChain)
            self.assertEqual(a135.useCompressPub, False)
            self.assertEqual(a135.isUsed, False)
            self.assertEqual(a135.privKeyNextUnlock, False)
            self.assertEqual(a135.akpParScrAddr, prevScrAddr)
            self.assertEqual(a135.childIndex, 0)
            self.assertEqual(a135.chainIndex, kidx)
            self.assertEqual(a135.childPoolSize, 1)
            self.assertEqual(a135.maxChildren, 1)
            self.assertEqual(a135.rawScript,  expectScript)
            self.assertEqual(a135.scrAddrStr, expectScrAddr)
            self.assertEqual(a135.akpParentRef.akpChildByIndex[0].getScrAddr(), expectScrAddr)
            self.assertEqual(a135.root135Ref.root135ChainMap[kidx].getScrAddr(), expectScrAddr)
            self.assertEqual(a135.lowestUnusedChild, 0)
            self.assertEqual(a135.nextChildToCalc,   0)
         
            kidx += 1
            prevScrAddr = expectScrAddr
            a135 = a135.spawnChild()
         
   
         scrAddrToIndex = {}
         for idx,a135 in a135rt.root135ChainMap.iteritems():
            scrAddrToIndex[a135.getScrAddr()] = idx
            self.assertEqual(a135.root135Ref.getScrAddr(), rootScrAddr)
            if idx>0:
               self.assertEqual(a135.akpParentRef.getScrAddr(), self.keyList[idx-1]['ScrAddr'])
               self.assertEqual(a135.akpParentRef.akpChildByIndex[0].getScrAddr(), a135.getScrAddr())
               self.assertEqual(len(a135.akpParentRef.akpChildByIndex), 1)
               self.assertEqual(len(a135.akpParentRef.akpChildByScrAddr), 1)
   
         for scrAddr,a135 in a135rt.root135ScrAddrMap.iteritems():
            self.assertEqual(scrAddrToIndex[a135.getScrAddr()], a135.chainIndex)

         runSerUnserRoundTripTest(self, a135rt)
         runSerUnserRoundTripTest(self, a135)


   #############################################################################
   def test135KeyPool(self):
      for WO in [False, True]:
         mockwlt = MockWalletFile()
         seed = SecureBinaryData(self.binSeed)
         a135rt = Armory135Root()
         a135rt.setWalletAndCryptInfo(mockwlt, None)
         a135rt.childPoolSize = 5
         a135rt.initializeFromSeed(seed, fillPool=False)


         self.assertEqual(len(a135rt.akpChildByIndex),   0)
         self.assertEqual(len(a135rt.akpChildByScrAddr), 0)
         self.assertEqual(len(a135rt.root135ChainMap),   0)
         self.assertEqual(len(a135rt.root135ScrAddrMap), 0)
         self.assertEqual(a135rt.rootLowestUnused,       0)
         self.assertEqual(a135rt.rootNextToCalc,         0)

         if WO:
            a135rt.wipePrivateData()

         # Peek at the next addr, confirm root didn't change
         testChild = a135rt.peekNextUnusedChild()
         self.assertEqual(len(a135rt.akpChildByIndex),   0)
         self.assertEqual(len(a135rt.akpChildByScrAddr), 0)
         self.assertEqual(len(a135rt.root135ChainMap),   0)
         self.assertEqual(len(a135rt.root135ScrAddrMap), 0)
         self.assertEqual(a135rt.rootLowestUnused,       0)
         self.assertEqual(a135rt.rootNextToCalc,         0)
         self.assertEqual(testChild.getScrAddr(), self.keyList[0]['ScrAddr'])
         

         a135rt.fillKeyPool()

         self.assertEqual(len(a135rt.akpChildByIndex),   1)
         self.assertEqual(len(a135rt.akpChildByScrAddr), 1)
         self.assertEqual(len(a135rt.root135ChainMap),   5)
         self.assertEqual(len(a135rt.root135ScrAddrMap), 5)
         self.assertEqual(a135rt.rootLowestUnused,       0)
         self.assertEqual(a135rt.rootNextToCalc,         5)


         parScrAddr = a135rt.getScrAddr()
         for i,ch in a135rt.root135ChainMap.iteritems():
            kdata = self.keyList[i]
            pub65 = kdata['PubKey']
            a160  = hash160(pub65.toBinStr())
            expectPriv   = kdata['PrivKey'].copy()
            expectPub    = CryptoECDSA().CompressPoint(pub65)
            expectChain  = self.chaincode.copy()
            expectScript = hash160_to_p2pkhash_script(a160)
            expectScrAddr= script_to_scrAddr(expectScript)

            self.assertEqual(expectScrAddr, kdata['ScrAddr'])
            self.assertEqual(expectScrAddr, kdata['ScrAddr'])

            self.assertEqual(ch.isWatchOnly, WO)
            self.assertEqual(ch.sbdPublicKey33, expectPub)
            self.assertEqual(ch.sbdChaincode,   expectChain)
            self.assertEqual(ch.useCompressPub, False)
            self.assertEqual(ch.isUsed, False)
            self.assertEqual(ch.privKeyNextUnlock, False)
            self.assertEqual(ch.akpParScrAddr, parScrAddr)
            self.assertEqual(ch.childIndex, 0)
            self.assertEqual(ch.chainIndex, i)
            self.assertEqual(ch.childPoolSize, 1)
            self.assertEqual(ch.maxChildren, 1)
            self.assertEqual(ch.rawScript,  expectScript)
            self.assertEqual(ch.scrAddrStr, expectScrAddr)
            self.assertEqual(ch.lowestUnusedChild, 0)
            self.assertEqual(ch.nextChildToCalc,   1 if i<4 else 0)

            
            if i>0:
               # These checks look redundant, but are making sure all the refs
               # are set properly between root, parent, child
               par = a135rt.root135ChainMap[i-1]
               self.assertEqual(par.akpChildByIndex[0].getScrAddr(), expectScrAddr)
               self.assertEqual(ch.akpParentRef.akpChildByIndex[0].getScrAddr(), expectScrAddr)
               self.assertEqual(a135rt.root135ChainMap[i].getScrAddr(), expectScrAddr)
               self.assertEqual(ch.root135Ref.root135ChainMap[i].getScrAddr(), expectScrAddr)
               self.assertTrue(expectScrAddr in par.akpChildByScrAddr)
               self.assertTrue(expectScrAddr in a135rt.root135ScrAddrMap)

               self.assertEqual(expectScrAddr, a135rt.getChildByIndex(i).getScrAddr())
               self.assertEqual(a135rt.getChildByScrAddr(expectScrAddr).getScrAddr(), expectScrAddr)

            parScrAddr = expectScrAddr




         
         a135rt.rootLowestUnused += 2
         a135rt.fillKeyPool()

         self.assertEqual(len(a135rt.akpChildByIndex),   1)
         self.assertEqual(len(a135rt.akpChildByScrAddr), 1)
         self.assertEqual(len(a135rt.root135ChainMap),   7)
         self.assertEqual(len(a135rt.root135ScrAddrMap), 7)
         self.assertEqual(a135rt.rootLowestUnused,       2)
         self.assertEqual(a135rt.rootNextToCalc,         7)

         self.assertRaises(ChildDeriveError, a135rt.getChildByIndex, 100)


   #############################################################################
   def testGetNextUnused(self):
      for WO in [False, True]:
         POOLSZ = 3
         mockwlt = MockWalletFile()
         seed = SecureBinaryData(self.binSeed)
         a135rt = Armory135Root()
         a135rt.setWalletAndCryptInfo(mockwlt, None)
         a135rt.childPoolSize = POOLSZ
         a135rt.initializeFromSeed(seed, fillPool=False)

         self.assertEqual(len(a135rt.akpChildByIndex),   0)
         self.assertEqual(len(a135rt.akpChildByScrAddr), 0)
         self.assertEqual(len(a135rt.root135ChainMap),   0)
         self.assertEqual(len(a135rt.root135ScrAddrMap), 0)
         self.assertEqual(a135rt.rootLowestUnused,       0)
         self.assertEqual(a135rt.rootNextToCalc,         0)

         if WO:
            a135rt.wipePrivateData()

         kidx = 0
         prevScrAddr = a135rt.getScrAddr()
         rootScrAddr = a135rt.getScrAddr()

         #a135rt.pprintVerbose()

         while kidx+3 in self.keyList:
            #print '---Testing k =', kidx
   
            # This calls fillKeyPool, so the keypool is always +3
            a135 = a135rt.getNextUnusedChild()
            #a135rt.pprintVerbose()
            self.assertEqual(len(a135rt.root135ChainMap), kidx+POOLSZ+1)
            self.assertEqual(len(a135rt.root135ScrAddrMap), kidx+POOLSZ+1)
            self.assertEqual(a135rt.rootLowestUnused, kidx+1)
            self.assertEqual(a135rt.rootNextToCalc, kidx+POOLSZ+1)

            pub65 = self.keyList[kidx]['PubKey']
            a160  = hash160(pub65.toBinStr())
   
            expectPriv   = self.keyList[kidx]['PrivKey'].copy()
            expectPub    = CryptoECDSA().CompressPoint(pub65)
            expectChain  = self.chaincode.copy()
            expectScript = hash160_to_p2pkhash_script(a160)
            expectScrAddr= script_to_scrAddr(expectScript)
            self.assertEqual(expectScrAddr, self.keyList[kidx]['ScrAddr'])

            if not WO:
               self.assertEqual(a135.sbdPrivKeyData, expectPriv)
               self.assertEqual(a135.getPlainPrivKeyCopy(), expectPriv)
            else:
               self.assertEqual(a135.sbdPrivKeyData, NULLSBD())
   
            self.assertEqual(a135.isWatchOnly, WO)
            self.assertEqual(a135.sbdPublicKey33, expectPub)
            self.assertEqual(a135.sbdChaincode,   expectChain)
            self.assertEqual(a135.useCompressPub, False)
            self.assertEqual(a135.isUsed, True)
            self.assertEqual(a135.privKeyNextUnlock, False)
            self.assertEqual(a135.akpParScrAddr, prevScrAddr)
            self.assertEqual(a135.childIndex, 0)
            self.assertEqual(a135.childPoolSize, 1)
            self.assertEqual(a135.maxChildren, 1)
            self.assertEqual(a135.rawScript,  expectScript)
            self.assertEqual(a135.scrAddrStr, expectScrAddr)
            self.assertEqual(a135.lowestUnusedChild, 0)
            self.assertEqual(a135.nextChildToCalc,   1)

            self.assertEqual(a135.root135Ref.root135ChainMap[kidx].getScrAddr(), expectScrAddr)
            self.assertEqual(a135.akpParentRef.akpChildByIndex[0].getScrAddr(), expectScrAddr)

         
            kidx += 1
            prevScrAddr = expectScrAddr
         
   
         scrAddrToIndex = {}
         for idx,a135 in a135rt.root135ChainMap.iteritems():
            #print 'Testing,  %d:%s' % (idx,binary_to_hex(a135.getScrAddr()))
            scrAddrToIndex[a135.getScrAddr()] = idx
            self.assertEqual(a135.root135Ref.getScrAddr(), rootScrAddr)
            if idx>0:
               self.assertEqual(a135.akpParentRef.getScrAddr(), self.keyList[idx-1]['ScrAddr'])
               self.assertEqual(a135.akpParentRef.akpChildByIndex[0].getScrAddr(), a135.getScrAddr())
               self.assertEqual(len(a135.akpParentRef.akpChildByIndex), 1)
               self.assertEqual(len(a135.akpParentRef.akpChildByScrAddr), 1)
   
         for scrAddr,a135 in a135rt.root135ScrAddrMap.iteritems():
            self.assertEqual(scrAddrToIndex[a135.getScrAddr()], a135.chainIndex)
      

   ################################################################################
   ################################################################################
   #
   # Armory 1.35 Encryption Tests
   #
   ################################################################################
   #############################################################################
   def testInitFromSeed32_Crypt(self):
      seed = SecureBinaryData(self.binSeed)

      a135rt = Armory135Root()
      a135rt.setWalletAndCryptInfo(None, self.privACI, self.ekey)
      a135rt.childPoolSize = 3

      self.assertRaises(WalletLockError, a135rt.initializeFromSeed, seed, fillPool=False)

      self.ekey.unlock(self.password)
      a135rt.initializeFromSeed(seed, fillPool=False)

      self.assertEqual(a135rt.sbdSeedData.toHexStr(), '') # supposed to be empty
      self.assertEqual(a135rt.privCryptInfo.serialize(), self.privACI.serialize())
      self.assertEqual(a135rt.privKeyNextUnlock, False)

      self.assertEqual(a135rt.getPlainSeedCopy(), seed)
      self.assertEqual(a135rt.getUniqueIDB58(), self.rootID)

      self.assertEqual(a135rt.rootLowestUnused, 0)
      self.assertEqual(a135rt.rootNextToCalc,   0)

      runSerUnserRoundTripTest(self, a135rt)

   #############################################################################
   def testInitFromSeed64_Crypt(self):
      seed = SecureBinaryData(self.binSeed + self.binAltChn)

      a135rt = Armory135Root()
      a135rt.setWalletAndCryptInfo(None, self.privACI, self.ekey)
      a135rt.childPoolSize = 3

      self.assertRaises(WalletLockError, a135rt.initializeFromSeed, seed, fillPool=False)

      self.ekey.unlock(self.password)
      a135rt.initializeFromSeed(seed, fillPool=False)

      self.assertEqual(a135rt.sbdSeedData.toHexStr(), '') # supposed to be empty
      self.assertEqual(a135rt.privCryptInfo.serialize(), self.privACI.serialize())
      self.assertEqual(a135rt.privKeyNextUnlock, False)

      self.assertEqual(a135rt.getPlainSeedCopy(), seed)
      self.assertEqual(a135rt.sbdChaincode.toBinStr(), self.binAltChn)
      self.assertEqual(a135rt.getUniqueIDB58(), '2tyiWrmKd') # diff chain->diff id

      self.assertEqual(a135rt.rootLowestUnused, 0)
      self.assertEqual(a135rt.rootNextToCalc,   0)

      runSerUnserRoundTripTest(self, a135rt)

   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testSpawnA135_Crypt(self):

      a135 = Armory135KeyPair()
      mockwlt = MockWalletFile()
      seed = SecureBinaryData(self.binSeed)

      a135rt = Armory135Root()
      a135rt.setWalletAndCryptInfo(mockwlt, self.privACI, self.ekey)
      a135rt.childPoolSize = 3

      self.ekey.unlock(self.password)
      a135rt.initializeFromSeed(seed, fillPool=False)


      self.ekey.lock(self.password)
      self.assertRaises(WalletLockError, a135rt.spawnChild, privSpawnReqd=True)

      self.ekey.unlock(self.password)
      a135 = a135rt.spawnChild()
      self.assertEqual(a135rt.rootLowestUnused, 0)
      self.assertEqual(a135rt.rootNextToCalc,   1)

      prevScrAddr = a135rt.getScrAddr()
      rootScrAddr = a135rt.getScrAddr()

      kidx = 0
      while kidx+1 in self.keyList:

         pub65 = self.keyList[kidx]['PubKey']
         a160  = hash160(pub65.toBinStr())

         expectPriv   = self.keyList[kidx]['PrivKey'].copy()
         expectCrypt  = self.keyList[kidx]['PrivCrypt'].copy()
         expectPub    = CryptoECDSA().CompressPoint(pub65)
         expectChain  = self.chaincode.copy()
         expectScript = hash160_to_p2pkhash_script(a160)
         expectScrAddr= script_to_scrAddr(expectScript)
         self.assertEqual(expectScrAddr, self.keyList[kidx]['ScrAddr'])

         self.assertEqual(a135.sbdPrivKeyData, expectCrypt)
         self.assertEqual(a135.getPlainPrivKeyCopy(), expectPriv)

         self.assertEqual(a135.isWatchOnly, False)
         self.assertEqual(a135.sbdPublicKey33, expectPub)
         self.assertEqual(a135.sbdChaincode,   expectChain)
         self.assertEqual(a135.useCompressPub, False)
         self.assertEqual(a135.isUsed, False)
         self.assertEqual(a135.privKeyNextUnlock, False)
         self.assertEqual(a135.akpParScrAddr, prevScrAddr)
         self.assertEqual(a135.childIndex, 0)
         self.assertEqual(a135.childPoolSize, 1)
         self.assertEqual(a135.maxChildren, 1)
         self.assertEqual(a135.rawScript,  expectScript)
         self.assertEqual(a135.scrAddrStr, expectScrAddr)
         self.assertEqual(a135.akpParentRef.akpChildByIndex[0].getScrAddr(), expectScrAddr)
         self.assertEqual(a135.root135Ref.root135ChainMap[kidx].getScrAddr(), expectScrAddr)
         self.assertEqual(a135.lowestUnusedChild, 0)
         self.assertEqual(a135.nextChildToCalc,   0)
      
         kidx += 1
         prevScrAddr = expectScrAddr
         a135 = a135.spawnChild()
      

      scrAddrToIndex = {}
      for idx,a135 in a135rt.root135ChainMap.iteritems():
         scrAddrToIndex[a135.getScrAddr()] = idx
         self.assertEqual(a135.root135Ref.getScrAddr(), rootScrAddr)
         if idx>0:
            self.assertEqual(a135.akpParentRef.getScrAddr(), self.keyList[idx-1]['ScrAddr'])
            self.assertEqual(a135.akpParentRef.akpChildByIndex[0].getScrAddr(), a135.getScrAddr())
            self.assertEqual(len(a135.akpParentRef.akpChildByIndex), 1)
            self.assertEqual(len(a135.akpParentRef.akpChildByScrAddr), 1)

      for scrAddr,a135 in a135rt.root135ScrAddrMap.iteritems():
         self.assertEqual(scrAddrToIndex[a135.getScrAddr()], a135.chainIndex)


      runSerUnserRoundTripTest(self, a135rt)
      runSerUnserRoundTripTest(self, a135)


   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def test135KeyPool_Crypt(self):
      a135 = Armory135KeyPair()
      mockwlt = MockWalletFile()
      seed = SecureBinaryData(self.binSeed)

      a135rt = Armory135Root()
      a135rt.setWalletAndCryptInfo(mockwlt, self.privACI, self.ekey)
      a135rt.childPoolSize = 5

      self.ekey.unlock(self.password)
      a135rt.initializeFromSeed(seed, fillPool=False)


      self.assertEqual(len(a135rt.akpChildByIndex),   0)
      self.assertEqual(len(a135rt.akpChildByScrAddr), 0)
      self.assertEqual(len(a135rt.root135ChainMap),   0)
      self.assertEqual(len(a135rt.root135ScrAddrMap), 0)
      self.assertEqual(a135rt.rootLowestUnused,       0)
      self.assertEqual(a135rt.rootNextToCalc,         0)


      # Peek at the next addr, confirm root didn't change
      testChild = a135rt.peekNextUnusedChild()
      self.assertEqual(len(a135rt.akpChildByIndex),   0)
      self.assertEqual(len(a135rt.akpChildByScrAddr), 0)
      self.assertEqual(len(a135rt.root135ChainMap),   0)
      self.assertEqual(len(a135rt.root135ScrAddrMap), 0)
      self.assertEqual(a135rt.rootLowestUnused,       0)
      self.assertEqual(a135rt.rootNextToCalc,         0)
      self.assertEqual(testChild.getScrAddr(), self.keyList[0]['ScrAddr'])
      

      a135rt.fillKeyPool()

      self.assertEqual(len(a135rt.akpChildByIndex),   1)
      self.assertEqual(len(a135rt.akpChildByScrAddr), 1)
      self.assertEqual(len(a135rt.root135ChainMap),   5)
      self.assertEqual(len(a135rt.root135ScrAddrMap), 5)
      self.assertEqual(a135rt.rootLowestUnused,       0)
      self.assertEqual(a135rt.rootNextToCalc,         5)


      parScrAddr = a135rt.getScrAddr()
      for i,ch in a135rt.root135ChainMap.iteritems():
         kdata = self.keyList[i]
         pub65 = kdata['PubKey']
         a160  = hash160(pub65.toBinStr())
         expectPriv   = kdata['PrivKey'].copy()
         expectCrypt  = kdata['PrivCrypt'].copy()
         expectPub    = CryptoECDSA().CompressPoint(pub65)
         expectChain  = self.chaincode.copy()
         expectScript = hash160_to_p2pkhash_script(a160)
         expectScrAddr= script_to_scrAddr(expectScript)

         self.assertEqual(expectScrAddr, kdata['ScrAddr'])
         self.assertEqual(expectScrAddr, kdata['ScrAddr'])

         self.assertEqual(ch.isWatchOnly, False)
         self.assertEqual(ch.sbdPrivKeyData, expectCrypt)
         self.assertEqual(ch.getPlainPrivKeyCopy(), expectPriv)
         self.assertEqual(ch.sbdPublicKey33, expectPub)
         self.assertEqual(ch.sbdChaincode,   expectChain)
         self.assertEqual(ch.useCompressPub, False)
         self.assertEqual(ch.isUsed, False)
         self.assertEqual(ch.privKeyNextUnlock, False)
         self.assertEqual(ch.akpParScrAddr, parScrAddr)
         self.assertEqual(ch.childIndex, 0)
         self.assertEqual(ch.chainIndex, i)
         self.assertEqual(ch.childPoolSize, 1)
         self.assertEqual(ch.maxChildren, 1)
         self.assertEqual(ch.rawScript,  expectScript)
         self.assertEqual(ch.scrAddrStr, expectScrAddr)
         self.assertEqual(ch.lowestUnusedChild, 0)
         self.assertEqual(ch.nextChildToCalc,   1 if i<4 else 0)

         
         if i>0:
            # These checks look redundant, but are making sure all the refs
            # are set properly between root, parent, child
            par = a135rt.root135ChainMap[i-1]
            self.assertEqual(par.akpChildByIndex[0].getScrAddr(), expectScrAddr)
            self.assertEqual(ch.akpParentRef.akpChildByIndex[0].getScrAddr(), expectScrAddr)
            self.assertEqual(a135rt.root135ChainMap[i].getScrAddr(), expectScrAddr)
            self.assertEqual(ch.root135Ref.root135ChainMap[i].getScrAddr(), expectScrAddr)
            self.assertTrue(expectScrAddr in par.akpChildByScrAddr)
            self.assertTrue(expectScrAddr in a135rt.root135ScrAddrMap)

         
         runSerUnserRoundTripTest(self, ch)

         parScrAddr = expectScrAddr



      
      a135rt.rootLowestUnused += 2
      a135rt.fillKeyPool()

      self.assertEqual(len(a135rt.akpChildByIndex),   1)
      self.assertEqual(len(a135rt.akpChildByScrAddr), 1)
      self.assertEqual(len(a135rt.root135ChainMap),   7)
      self.assertEqual(len(a135rt.root135ScrAddrMap), 7)
      self.assertEqual(a135rt.rootLowestUnused,       2)
      self.assertEqual(a135rt.rootNextToCalc,         7)

      runSerUnserRoundTripTest(self, a135rt)


   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testGetNextUnused_Crypt(self):
      POOLSZ = 3
      mockwlt = MockWalletFile()
      seed = SecureBinaryData(self.binSeed)
      a135rt = Armory135Root()
      a135rt.setWalletAndCryptInfo(mockwlt, self.privACI, self.ekey)
      a135rt.childPoolSize = POOLSZ

      self.ekey.unlock(self.password)
      a135rt.initializeFromSeed(seed, fillPool=False)

      self.assertEqual(len(a135rt.akpChildByIndex),   0)
      self.assertEqual(len(a135rt.akpChildByScrAddr), 0)
      self.assertEqual(len(a135rt.root135ChainMap),   0)
      self.assertEqual(len(a135rt.root135ScrAddrMap), 0)
      self.assertEqual(a135rt.rootLowestUnused,       0)
      self.assertEqual(a135rt.rootNextToCalc,         0)


      kidx = 0
      prevScrAddr = a135rt.getScrAddr()
      rootScrAddr = a135rt.getScrAddr()

      #a135rt.pprintVerbose()

      while kidx+3 in self.keyList:
         #print '---Testing k =', kidx

         # This calls fillKeyPool, so the keypool is always +3
         a135 = a135rt.getNextUnusedChild()
         #a135rt.pprintVerbose()
         self.assertEqual(len(a135rt.root135ChainMap), kidx+POOLSZ+1)
         self.assertEqual(len(a135rt.root135ScrAddrMap), kidx+POOLSZ+1)
         self.assertEqual(a135rt.rootLowestUnused, kidx+1)
         self.assertEqual(a135rt.rootNextToCalc, kidx+POOLSZ+1)

         pub65 = self.keyList[kidx]['PubKey']
         a160  = hash160(pub65.toBinStr())

         expectPriv   = self.keyList[kidx]['PrivKey'].copy()
         expectCrypt  = self.keyList[kidx]['PrivCrypt'].copy()
         expectPub    = CryptoECDSA().CompressPoint(pub65)
         expectChain  = self.chaincode.copy()
         expectScript = hash160_to_p2pkhash_script(a160)
         expectScrAddr= script_to_scrAddr(expectScript)
         self.assertEqual(expectScrAddr, self.keyList[kidx]['ScrAddr'])

         self.assertEqual(a135.sbdPrivKeyData, expectCrypt)
         self.assertEqual(a135.getPlainPrivKeyCopy(), expectPriv)

         self.assertEqual(a135.isWatchOnly, False)
         self.assertEqual(a135.sbdPublicKey33, expectPub)
         self.assertEqual(a135.sbdChaincode,   expectChain)
         self.assertEqual(a135.useCompressPub, False)
         self.assertEqual(a135.isUsed, True)
         self.assertEqual(a135.privKeyNextUnlock, False)
         self.assertEqual(a135.akpParScrAddr, prevScrAddr)
         self.assertEqual(a135.childIndex, 0)
         self.assertEqual(a135.childPoolSize, 1)
         self.assertEqual(a135.maxChildren, 1)
         self.assertEqual(a135.rawScript,  expectScript)
         self.assertEqual(a135.scrAddrStr, expectScrAddr)
         self.assertEqual(a135.lowestUnusedChild, 0)
         self.assertEqual(a135.nextChildToCalc,   1)

         self.assertEqual(a135.root135Ref.root135ChainMap[kidx].getScrAddr(), expectScrAddr)
         self.assertEqual(a135.akpParentRef.akpChildByIndex[0].getScrAddr(), expectScrAddr)

      
         kidx += 1
         prevScrAddr = expectScrAddr

         runSerUnserRoundTripTest(self, a135)
      

      scrAddrToIndex = {}
      for idx,a135 in a135rt.root135ChainMap.iteritems():
         #print 'Testing,  %d:%s' % (idx,binary_to_hex(a135.getScrAddr()))
         scrAddrToIndex[a135.getScrAddr()] = idx
         self.assertEqual(a135.root135Ref.getScrAddr(), rootScrAddr)
         if idx>0:
            self.assertEqual(a135.akpParentRef.getScrAddr(), self.keyList[idx-1]['ScrAddr'])
            self.assertEqual(a135.akpParentRef.akpChildByIndex[0].getScrAddr(), a135.getScrAddr())
            self.assertEqual(len(a135.akpParentRef.akpChildByIndex), 1)
            self.assertEqual(len(a135.akpParentRef.akpChildByScrAddr), 1)

      for scrAddr,a135 in a135rt.root135ScrAddrMap.iteritems():
         self.assertEqual(scrAddrToIndex[a135.getScrAddr()], a135.chainIndex)

      
   ################################################################################
   ################################################################################
   #
   # Armory 135 NEXTUNLOCK TESTS
   #
   ################################################################################
   ################################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testSpawnA135_ResolveNextUnlock(self):
      """
      This test is going to create an artificial chain of 135 keys, with 
      the nextUnlock flags set to True, then attempt to resolve it.  Later 
      we will create naturally-occurring nextUnlock structures to test resolving
      """
      POOLSZ = 3
      mockwlt = MockWalletFile()
      seed = SecureBinaryData(self.binSeed)
      a135rt = Armory135Root()
      a135rt.setWalletAndCryptInfo(mockwlt, self.privACI, self.ekey)
      a135rt.childPoolSize = POOLSZ

      self.ekey.unlock(self.password)
      a135rt.initializeFromSeed(seed, fillPool=False)

      a135 = a135rt.spawnChild() 
      a135List = []
      kidx = 0
      while kidx in self.keyList:

         pub65 = self.keyList[kidx]['PubKey']
         a160  = hash160(pub65.toBinStr())
         expectPriv   = self.keyList[kidx]['PrivKey'].copy()
         expectCrypt  = self.keyList[kidx]['PrivCrypt'].copy()
         expectPub    = CryptoECDSA().CompressPoint(pub65)
         expectChain  = self.chaincode.copy()
         expectScript = hash160_to_p2pkhash_script(a160)
         expectScrAddr= script_to_scrAddr(expectScript)
         self.assertEqual(expectScrAddr, self.keyList[kidx]['ScrAddr'])

         self.assertEqual(a135.sbdPrivKeyData, expectCrypt)
         self.assertEqual(a135.getPlainPrivKeyCopy(), expectPriv)
         self.assertEqual(a135.isWatchOnly, False)
         self.assertEqual(a135.sbdPublicKey33, expectPub)
         self.assertEqual(a135.sbdChaincode,   expectChain)
         self.assertEqual(a135.useCompressPub, False)
         self.assertEqual(a135.isUsed, False)
         self.assertEqual(a135.privKeyNextUnlock, False)
         self.assertEqual(a135.rawScript,  expectScript)
         self.assertEqual(a135.scrAddrStr, expectScrAddr)
      
         kidx += 1
         a135List.append(a135)
         a135 = a135.spawnChild()

      # Okay, the above was just setup an verification of the setup
      # Now we delete the encrypted priv key data and try resolving from var points
      def resetTest(keyWipeList):
         for i,kmap in self.keyList.iteritems():
            if i in keyWipeList:
               a135List[i].sbdPrivKeyData.destroy()
               a135List[i].privKeyNextUnlock = True
            else:
               a135List[i].sbdPrivKeyData = kmap['PrivCrypt'].copy()
               a135List[i].privKeyNextUnlock = False


      def printResolveList():
         print 'Reset List:'
         for a in a135List:
            print a.chainIndex, a.privKeyNextUnlock, a.sbdPrivKeyData.getSize()

      def testResolveAndCheck(idx):
         a135List[idx].resolveNextUnlockFlag()
         for i,a135 in enumerate(a135List):
            if i<=idx:
               expectCrypt  = self.keyList[i]['PrivCrypt'].copy()
               expectPubKey = self.keyList[i]['PubKey'].copy()
               expectChain  = a135rt.sbdChaincode.copy()
               expectUnlock  = False
            else:
               expectCrypt  = NULLSBD()
               expectPubKey = self.keyList[i]['PubKey'].copy()
               expectChain  = a135rt.sbdChaincode.copy()
               expectUnlock = True

            expectPubKey = CryptoECDSA().CompressPoint(expectPubKey)
            self.assertEqual(a135.sbdPrivKeyData, expectCrypt)
            self.assertEqual(a135.sbdPublicKey33, expectPubKey)
            self.assertEqual(a135.sbdChaincode,   expectChain)
            self.assertEqual(a135.privKeyNextUnlock, expectUnlock)
            runSerUnserRoundTripTest(self, a135)

      self.ekey.unlock(self.password)

      resetTest(range(7))
      testResolveAndCheck(0)

      resetTest(range(7))
      testResolveAndCheck(1)
      testResolveAndCheck(3)

      resetTest(range(7))
      testResolveAndCheck(6)

      resetTest([4,5,6])
      testResolveAndCheck(5)

      resetTest([4,5,6])
      testResolveAndCheck(6)

      # This really shouldn't happen...ever...
      resetTest([2,5,6])
      a135List[2].resolveNextUnlockFlag()
      testResolveAndCheck(6)


   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testSpawnA135_NextUnlock1(self):
      """
      Create a naturally-occurring next-unlock tree, then resolve it
      """
      mockwlt = MockWalletFile()
      seed = SecureBinaryData(self.binSeed)
      a135rt = Armory135Root()
      a135rt.setWalletAndCryptInfo(mockwlt, self.privACI, self.ekey)
      a135rt.childPoolSize = 3

      self.ekey.unlock(self.password)
      a135rt.initializeFromSeed(seed, fillPool=False)

      # Now lock and spawn
      self.ekey.lock()
      self.assertRaises(WalletLockError, a135rt.spawnChild, privSpawnReqd=True)
      a135 = a135rt.spawnChild()

      pub65 = self.keyList[0]['PubKey']
      a160  = hash160(pub65.toBinStr())
      expectPriv   = self.keyList[0]['PrivKey'].copy()
      expectCrypt  = self.keyList[0]['PrivCrypt'].copy()
      expectPub    = CryptoECDSA().CompressPoint(pub65)
      expectChain  = self.chaincode.copy()

      # Should've spawned public key and marked nextUnlock
      self.assertEqual(a135.privKeyNextUnlock, True)
      self.assertRaises(WalletLockError, a135.getPlainPrivKeyCopy)
      self.assertEqual(a135.sbdPrivKeyData, NULLSBD())
      self.assertEqual(a135.isWatchOnly, False)
      self.assertEqual(a135.sbdPublicKey33, expectPub)
      self.assertEqual(a135.sbdChaincode,   expectChain)

      # Now unlock and resolve
      self.assertRaises(WalletLockError, a135.resolveNextUnlockFlag)
      self.ekey.unlock(self.password)
      a135.resolveNextUnlockFlag()

      # Priv key should be available and nextUnlock=False
      self.assertEqual(a135.sbdPrivKeyData, expectCrypt)
      self.assertEqual(a135.getPlainPrivKeyCopy(), expectPriv)
      self.assertEqual(a135.privKeyNextUnlock, False)
      self.assertEqual(a135.isWatchOnly, False)
      self.assertEqual(a135.sbdPublicKey33, expectPub)
      self.assertEqual(a135.sbdChaincode,   expectChain)
      self.assertEqual(a135.useCompressPub, False)
      self.assertEqual(a135.isUsed, False)

      runSerUnserRoundTripTest(self, a135)

   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testSpawnA135_NextUnlock3(self):
      """
      Create a naturally-occurring next-unlock tree, then resolve it
      """
      mockwlt = MockWalletFile()
      seed = SecureBinaryData(self.binSeed)
      a135rt = Armory135Root()
      a135rt.setWalletAndCryptInfo(mockwlt, self.privACI, self.ekey)
      a135rt.childPoolSize = 3

      self.ekey.unlock(self.password)
      a135rt.initializeFromSeed(seed, fillPool=False)

      # Now lock and spawn
      self.ekey.lock()

      a135List = []
      a135 = a135rt
      for i in range(5):
         a135 = a135.spawnChild()
         a135List.append(a135)
      
         pub65 = self.keyList[i]['PubKey']
         a160  = hash160(pub65.toBinStr())
         expectPriv   = self.keyList[i]['PrivKey'].copy()
         expectCrypt  = self.keyList[i]['PrivCrypt'].copy()
         expectPub    = CryptoECDSA().CompressPoint(pub65)
         expectChain  = self.chaincode.copy()

         # Should've spawned public key and marked nextUnlock
         self.assertEqual(a135.privKeyNextUnlock, True)
         self.assertEqual(a135.sbdPrivKeyData, NULLSBD())
         self.assertEqual(a135.sbdPublicKey33, expectPub)
         self.assertEqual(a135.sbdChaincode,   expectChain)

      # Now unlock and resolve
      self.assertRaises(WalletLockError, a135.resolveNextUnlockFlag)
      self.ekey.unlock(self.password)
      a135List[2].resolveNextUnlockFlag()

      for i in range(5):
         a135 = a135List[i]
         pub65 = self.keyList[i]['PubKey']
         a160  = hash160(pub65.toBinStr())
         expectCrypt  = self.keyList[i]['PrivCrypt'].copy()
         expectPub    = CryptoECDSA().CompressPoint(pub65)
         expectChain  = self.chaincode.copy()

         if i>2:
            expectCrypt  = NULLSBD()

         # Should've spawned public key and marked nextUnlock
         self.assertEqual(a135.privKeyNextUnlock, i>2)
         self.assertEqual(a135.sbdPrivKeyData, expectCrypt)
         self.assertEqual(a135.sbdPublicKey33, expectPub)
         self.assertEqual(a135.sbdChaincode,   expectChain)


      # Now one more step inside
      a135List[4].resolveNextUnlockFlag()

      for i in range(5):
         a135 = a135List[i]
         pub65 = self.keyList[i]['PubKey']
         a160  = hash160(pub65.toBinStr())
         expectCrypt  = self.keyList[i]['PrivCrypt'].copy()
         expectPub    = CryptoECDSA().CompressPoint(pub65)
         expectChain  = self.chaincode.copy()

         if i>4:
            expectCrypt  = NULLSBD()

         # Should've spawned public key and marked nextUnlock
         self.assertEqual(a135.privKeyNextUnlock, i>4)
         self.assertEqual(a135.sbdPrivKeyData, expectCrypt)
         self.assertEqual(a135.sbdPublicKey33, expectPub)
         self.assertEqual(a135.sbdChaincode,   expectChain)

         runSerUnserRoundTripTest(self, a135)


   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testGetNextUnused_NextUnlock(self):
      """
      Pretty much same as regular encrypted test, but all keys gen while locked
      """
      POOLSZ = 3
      mockwlt = MockWalletFile()
      seed = SecureBinaryData(self.binSeed)
      a135rt = Armory135Root()
      a135rt.setWalletAndCryptInfo(mockwlt, self.privACI, self.ekey)
      a135rt.childPoolSize = POOLSZ

      self.ekey.unlock(self.password)
      a135rt.initializeFromSeed(seed, fillPool=False)

      kidx = 0
      rootScrAddr = a135rt.getScrAddr()

      #### Lock before generating any keys
      self.ekey.lock(self.password)

      runSerUnserRoundTripTest(self, a135rt)

      while kidx+3 in self.keyList:
         a135 = a135rt.getNextUnusedChild()
         self.assertEqual(len(a135rt.root135ChainMap), kidx+POOLSZ+1)
         self.assertEqual(len(a135rt.root135ScrAddrMap), kidx+POOLSZ+1)
         self.assertEqual(a135rt.rootLowestUnused, kidx+1)
         self.assertEqual(a135rt.rootNextToCalc, kidx+POOLSZ+1)

         pub65 = self.keyList[kidx]['PubKey']
         a160  = hash160(pub65.toBinStr())
         expectPriv   = self.keyList[kidx]['PrivKey'].copy()
         expectCrypt  = self.keyList[kidx]['PrivCrypt'].copy()
         expectPub    = CryptoECDSA().CompressPoint(pub65)
         expectChain  = self.chaincode.copy()
         expectScript = hash160_to_p2pkhash_script(a160)
         expectScrAddr= script_to_scrAddr(expectScript)
         self.assertEqual(expectScrAddr, self.keyList[kidx]['ScrAddr'])

         self.assertEqual(a135.privKeyNextUnlock, True)
         self.assertEqual(a135.sbdPrivKeyData, NULLSBD())
         self.assertEqual(a135.isWatchOnly, False)
         self.assertEqual(a135.sbdPublicKey33, expectPub)
         self.assertEqual(a135.sbdChaincode,   expectChain)
      
         kidx += 1
         runSerUnserRoundTripTest(self, a135)
      

      self.assertEqual(a135rt.getChildByIndex(2).sbdPrivKeyData, NULLSBD())
      self.assertEqual(a135rt.getChildByIndex(3).sbdPrivKeyData, NULLSBD())
      self.ekey.unlock(self.password)
      # Unlocking shouldn't have changed anything yet
      self.assertEqual(a135rt.getChildByIndex(2).sbdPrivKeyData, NULLSBD())
      self.assertEqual(a135rt.getChildByIndex(3).sbdPrivKeyData, NULLSBD())

      runSerUnserRoundTripTest(self, a135rt.getChildByIndex(3))

      # The act of requesting the plain priv key, should trigger resolveUnlock
      self.assertEqual(a135rt.getChildByIndex(3).getPlainPrivKeyCopy(), self.keyList[3]['PrivKey'])
      self.assertEqual(a135rt.getChildByIndex(2).sbdPrivKeyData, self.keyList[2]['PrivCrypt'])
      self.assertEqual(a135rt.getChildByIndex(3).sbdPrivKeyData, self.keyList[3]['PrivCrypt'])

      runSerUnserRoundTripTest(self, a135rt.getChildByIndex(3))



################################################################################
################################################################################
#
# Armory Imported KeyPair Tests (No encryption)
#
################################################################################
################################################################################
class Imported_NoCrypt_Tests(unittest.TestCase):

   #############################################################################
   def setUp(self):
      # Will use the same keylist as for Armory135, just assume not related

      self.keyList = {}

      self.keyList[0] = { \
         'AddrStr': '13QVfpnE7TWAnkGGpHak1Z9cJVQWTZrYqb',
         'PrivB58': '5JWFgYDRyCqxMcXprSf84RAfPC4p6x2eifXxNwHuqeL137JC11A',
         'PubKeyX': '1a84426c38a0099975d683365436ee3eedaf2c9589c44635aa3808ede5f87081',
         'PubKeyY': '6a905e1f3055c0982307951e5e4150349c5c98a644f3da9aeef9c80f103cf2af' }
      self.keyList[1] = { \
         'AddrStr': '1Dy4cGbv3KKm4EhQYVKvUJQfy6sgmGR4ii',
         'PrivB58': '5KMBzjqDE8dXxtvRaY8dGHnMUNyE6uonDwKgeG44XBsngqTYkf9',
         'PubKeyX': '6c23cc6208a1f6daaa196ba6e763b445555ada6315ebf9465a0b9cb49e813e3a',
         'PubKeyY': '341eb33ed738b6a1ac6a57526a80af2e6841dcf71f287dbe721dd4486d9cf8c4' }
      self.keyList[2] = { \
         'AddrStr': '1BKG36rBdxiYNRQbLCYfPzi6Cf4pW2aRxQ',
         'PrivB58': '5KhpN6mmdiVcKmZtPjqfC41Af7181Dj4JadyU7dDLVefdPcMbZi',
         'PubKeyX': 'eb013f8047ad532a8bcc4d4f69a62887ce82afb574d7fb8a326b9bab82d240fa',
         'PubKeyY': 'a8fdcd604105292cb04c7707da5e42300bc418654f8ffc94e2c83bd5a54e09e2' }
      self.keyList[3] = { \
         'AddrStr': '1NhZfoXMLmohuvAh7Ks67JMx6mpcVq2FCa',
         'PrivB58': '5KaxXWwQgFcp3d5Bqd58xvtBDN8FEPQeRZJDpyxY5LTZ5ALZHE3',
         'PubKeyX': 'd6e6d3031d5d3de48293d97590f5b697089e8e6b40e919a68e2a07c300c1256b',
         'PubKeyY': '3d9b428e0ef9f73bd81c9388e1d8702f477138ca444eed57370d0e31ba9bafe5' }
      self.keyList[4] = { \
         'AddrStr': '1GHvHhrUBL5mMryscJa9uzDnPXeEpqU7Tn',
         'PrivB58': '5Jb4u9bpWDv19y6hu6nAE7cDdQoUrJMoyrwGDjPxMKo8oxULSdn',
         'PubKeyX': 'e40d3923bfffad0cdc6d6a3341c8e669beb1264b86cbfd21229ca8a74cf53ca5',
         'PubKeyY': '587b7a9b18b648cd421d17d45d05e8fc647f7ea02f61b670a2d4c2012e3b717f' }
      self.keyList[5] = { \
         'AddrStr': '1DdAdN2VQXg52YqDssZ4o6XprVgEB4Evpj',
         'PrivB58': '5JxD9BrDhCgWEKfEUG2FBcAk1D667G97hNREg81M5Qzgi9CAgdD',
         'PubKeyX': '7e043899f917288db2962819cd78c8328efb6dd172b9cbe1bfaaf8d745fd3e99',
         'PubKeyY': '746b29150ff3828556595291419d579c824ac2879d83fb3d51d5efea5de4715d' }
      self.keyList[6] = { \
         'AddrStr': '1K9QBzxv2jL7ftMkJ9jghr8dJgZ6u6zhHR',
         'PrivB58': '5K7GHu48sqxnYNhiMNVVoeh8WXnnerrNhL2TWocHngaP8zyUPAr',
         'PubKeyX': 'bbc9cd69dd6977b08d7916c0da81208df0b8a491b0897ca482bd42df47102d6b',
         'PubKeyY': 'f0318b3298ba93831df82b7ce51da5e0e8647a3ecd994f600a84834b424ed2b8' }


      for idx,imap in self.keyList.iteritems():
         imap['PrivKey']   = SecureBinaryData(parsePrivateKeyData(imap['PrivB58'])[0])
         imap['PubKey']    = SecureBinaryData(hex_to_binary('04' + imap['PubKeyX'] + imap['PubKeyY']))
         imap['ScrAddr']   = SCRADDR_P2PKH_BYTE + hash160(imap['PubKey'].toBinStr())
      
   #############################################################################
   def tearDown(self):
      pass
      

   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testImportedInit(self):

      for i in range(2):
         aikp    =  ArmoryImportedKeyPair() if i==0 else  ArmoryImportedRoot()
         clsName = 'ArmoryImportedKeyPair'  if i==0 else 'ArmoryImportedRoot'

         self.assertRaises(aikp.getChildClass, None)
            
         self.assertEqual(aikp.isWatchOnly, False)
         self.assertEqual(aikp.sbdPrivKeyData, NULLSBD())
         self.assertEqual(aikp.sbdPublicKey33, NULLSBD())
         self.assertEqual(aikp.sbdChaincode,   NULLSBD())
         self.assertEqual(aikp.useCompressPub, True)
         self.assertEqual(aikp.isUsed, False)
         self.assertEqual(aikp.keyBornTime, 0)
         self.assertEqual(aikp.keyBornBlock, 0)
         self.assertEqual(aikp.privKeyNextUnlock, False)
         self.assertEqual(aikp.childPoolSize, 0)
         self.assertEqual(aikp.maxChildren, 0)
         self.assertEqual(aikp.rawScript, None)
         self.assertEqual(aikp.scrAddrStr, None)
         self.assertEqual(aikp.uniqueIDBin, None)
         self.assertEqual(aikp.uniqueIDB58, None)
         self.assertEqual(aikp.akpChildByIndex, {})
         self.assertEqual(aikp.akpChildByScrAddr, {})
         self.assertEqual(aikp.lowestUnusedChild, 0)
         self.assertEqual(aikp.nextChildToCalc,   0)
         self.assertEqual(aikp.akpParentRef, None)
         self.assertEqual(aikp.masterEkeyRef, None)
   
         self.assertEqual(aikp.getName(), clsName)
         self.assertEqual(aikp.getPrivKeyAvailability(), PRIV_KEY_AVAIL.Uninit)
   
         self.assertEqual(aikp.childIndex, None)
   
         # WalletEntry fields
         self.assertEqual(aikp.wltFileRef, None)
         self.assertEqual(aikp.wltByteLoc, None)
         self.assertEqual(aikp.wltEntrySz, None)
         self.assertEqual(aikp.isRequired, False)
         self.assertEqual(aikp.parEntryID, None)
         self.assertEqual(aikp.outerCrypt.serialize(), NULLCRYPTINFO().serialize())
         self.assertEqual(aikp.serPayload, None)
         self.assertEqual(aikp.defaultPad, 256)
         self.assertEqual(aikp.wltParentRef, None)
         self.assertEqual(aikp.wltChildRefs, [])
         self.assertEqual(aikp.outerEkeyRef, None)
         self.assertEqual(aikp.isOpaque,        False)
         self.assertEqual(aikp.isUnrecognized,  False)
         self.assertEqual(aikp.isUnrecoverable, False)
         self.assertEqual(aikp.isDeleted,       False)
         self.assertEqual(aikp.isDisabled,      False)
         self.assertEqual(aikp.needFsync,       False)
   
         self.assertRaises(UninitializedError, aikp.serialize)




   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testImportedCompressed(self):

      for i in range(2):
         aikp    =  ArmoryImportedKeyPair() if i==0 else  ArmoryImportedRoot()
         clsName = 'ArmoryImportedKeyPair'  if i==0 else 'ArmoryImportedRoot'

         self.assertRaises(aikp.getChildClass, None)

         sbdPriv = self.keyList[0]['PrivKey'].copy()
         sbdPubk = self.keyList[0]['PubKey'].copy()
         scrAddr = self.keyList[0]['ScrAddr']
         t = long(1.4e9)

   
         sbdPubkCompr = CryptoECDSA().CompressPoint(sbdPubk)
         scrAddrCompr = '\x00' + hash160(sbdPubkCompr.toBinStr())
         uniqID  = '' if i==0 else hash256(sbdPubkCompr.toBinStr())[:6]
   
         aikp.initializeAKP(isWatchOnly=False,
                            isAkpRootRoot=False,
                            privCryptInfo=NULLCRYPTINFO(),
                            sbdPrivKeyData=sbdPriv,
                            sbdPublicKey33=sbdPubk,
                            sbdChaincode=NULLSBD(),
                            privKeyNextUnlock=False,
                            akpParScrAddr=None,
                            childIndex=None,
                            useCompressPub=True,
                            isUsed=True,
                            notForDirectUse=False,
                            keyBornTime=t,
                            keyBornBlock=t)
   
   
                              
         self.assertEqual(aikp.isWatchOnly, False)
         self.assertEqual(aikp.isAkpRootRoot, False)
         self.assertEqual(aikp.sbdPrivKeyData, sbdPriv)
         self.assertEqual(aikp.getPlainPrivKeyCopy(), sbdPriv)
         self.assertEqual(aikp.sbdPublicKey33, sbdPubkCompr)
         self.assertEqual(aikp.sbdChaincode, NULLSBD())
         self.assertEqual(aikp.useCompressPub, True)
         self.assertEqual(aikp.isUsed, True)
         self.assertEqual(aikp.keyBornTime, t)
         self.assertEqual(aikp.keyBornBlock, t)
         self.assertEqual(aikp.privKeyNextUnlock, False)
         self.assertEqual(aikp.akpParScrAddr, None)
         self.assertEqual(aikp.childIndex, None)
         self.assertEqual(aikp.maxChildren, 0)
         self.assertEqual(aikp.scrAddrStr, scrAddrCompr)
         self.assertEqual(aikp.uniqueIDBin, uniqID)
         self.assertEqual(aikp.uniqueIDB58, binary_to_base58(uniqID))
         self.assertEqual(aikp.akpChildByIndex, {})
         self.assertEqual(aikp.akpChildByScrAddr, {})
         self.assertEqual(aikp.lowestUnusedChild, 0)
         self.assertEqual(aikp.nextChildToCalc,   0)
         self.assertEqual(aikp.akpParentRef, None)
         self.assertEqual(aikp.masterEkeyRef, None)
   
         self.assertEqual(aikp.TREELEAF, True)
         self.assertEqual(aikp.getName(), clsName)
         self.assertEqual(aikp.getPrivKeyAvailability(), PRIV_KEY_AVAIL.Available)
         self.assertEqual(aikp.getPlainPrivKeyCopy(), sbdPriv)
   
         runSerUnserRoundTripTest(self, aikp)


   #############################################################################
   @unittest.skipIf(skipFlagExists(), '')
   def testImportedUncompressed(self):
      for i in range(2):
         aikp    =  ArmoryImportedKeyPair() if i==0 else  ArmoryImportedRoot()
         clsName = 'ArmoryImportedKeyPair'  if i==0 else 'ArmoryImportedRoot'
   
         sbdPriv = self.keyList[0]['PrivKey'].copy()
         sbdPubk = self.keyList[0]['PubKey'].copy()
         scrAddr = self.keyList[0]['ScrAddr']
         t = long(1.4e9)
   
         sbdPubkCompr = CryptoECDSA().CompressPoint(sbdPubk)
         uniqID  = '' if i==0 else hash256(sbdPubk.toBinStr())[:6]
   
         aikp.initializeAKP(isWatchOnly=False,
                           isAkpRootRoot=False,
                           privCryptInfo=NULLCRYPTINFO(),
                           sbdPrivKeyData=sbdPriv,
                           sbdPublicKey33=sbdPubk,
                           sbdChaincode=NULLSBD(),
                           privKeyNextUnlock=False,
                           akpParScrAddr=None,
                           childIndex=None,
                           useCompressPub=False,
                           isUsed=True,
                           notForDirectUse=False,
                           keyBornTime=t,
                           keyBornBlock=t)
   
   
                              
         self.assertEqual(aikp.isWatchOnly, False)
         self.assertEqual(aikp.isAkpRootRoot, False)
         self.assertEqual(aikp.sbdPrivKeyData, sbdPriv)
         self.assertEqual(aikp.getPlainPrivKeyCopy(), sbdPriv)
         self.assertEqual(aikp.sbdPublicKey33, sbdPubkCompr)
         self.assertEqual(aikp.sbdChaincode, NULLSBD())
         self.assertEqual(aikp.useCompressPub, False)
         self.assertEqual(aikp.isUsed, True)
         self.assertEqual(aikp.keyBornTime, t)
         self.assertEqual(aikp.keyBornBlock, t)
         self.assertEqual(aikp.privKeyNextUnlock, False)
         self.assertEqual(aikp.akpParScrAddr, None)
         self.assertEqual(aikp.childIndex, None)
         self.assertEqual(aikp.maxChildren, 0)
         self.assertEqual(aikp.scrAddrStr, scrAddr)
         self.assertEqual(aikp.uniqueIDBin, uniqID)
         self.assertEqual(aikp.uniqueIDB58, binary_to_base58(uniqID))
         self.assertEqual(aikp.akpChildByIndex, {})
         self.assertEqual(aikp.akpChildByScrAddr, {})
         self.assertEqual(aikp.lowestUnusedChild, 0)
         self.assertEqual(aikp.nextChildToCalc,   0)
         self.assertEqual(aikp.akpParentRef, None)
         self.assertEqual(aikp.masterEkeyRef, None)
   
         self.assertEqual(aikp.TREELEAF, True)
         self.assertEqual(aikp.getName(), clsName)
         self.assertEqual(aikp.getPrivKeyAvailability(), PRIV_KEY_AVAIL.Available)
         self.assertEqual(aikp.getPlainPrivKeyCopy(), sbdPriv)
   
         runSerUnserRoundTripTest(self, aikp)


   #############################################################################
   def testCreateImportedRoot(self):
      aikp = ArmoryImportedKeyPair() 
      airt = ArmoryImportedRoot()

      sbdPrivRoot  = self.keyList[0]['PrivKey'].copy()
      sbdPubkRoot  = self.keyList[0]['PubKey'].copy()
      scrAddrRoot  = self.keyList[0]['ScrAddr']

      sbdPubRtCompr = CryptoECDSA().CompressPoint(sbdPubkRoot)

      sbdPrivAikp  = self.keyList[2]['PrivKey'].copy()
      sbdPubkAikp  = self.keyList[2]['PubKey'].copy()
      scrAddrAikp  = self.keyList[2]['ScrAddr']

      sbdPubRtCompr = CryptoECDSA().CompressPoint(sbdPubkRoot)
      sbdPubKpCompr = CryptoECDSA().CompressPoint(sbdPubkAikp)

      airt.createNewRoot(pregenRoot=sbdPrivRoot, currBlk=10)
      uniqID = hash256(sbdPubRtCompr.toBinStr())[:6]


      self.assertEqual(airt.isAkpRootRoot, True)
      self.assertEqual(airt.sbdPrivKeyData, sbdPrivRoot)
      self.assertEqual(airt.sbdPublicKey33, sbdPubRtCompr)
      self.assertEqual(airt.sbdChaincode, NULLSBD())
      self.assertEqual(airt.useCompressPub, True)
      self.assertEqual(airt.keyBornBlock, 10)
      self.assertEqual(airt.akpParScrAddr, airt.getScrAddr())
      #self.assertEqual(airt.akpParScrAddr, scrAddrRoot) #scraddr is for uncompr
      self.assertEqual(airt.childIndex, None)
      self.assertEqual(airt.maxChildren, 0)
      self.assertEqual(airt.uniqueIDBin, uniqID)
      self.assertEqual(airt.uniqueIDB58, binary_to_base58(uniqID))

      aikp.initializeAKP(isWatchOnly=False,
                         isAkpRootRoot=False,
                         privCryptInfo=NULLCRYPTINFO(),
                         sbdPrivKeyData=sbdPrivAikp,
                         sbdPublicKey33=sbdPubkAikp,
                         sbdChaincode=NULLSBD(),
                         privKeyNextUnlock=False,
                         akpParScrAddr=scrAddrRoot,
                         childIndex=None,
                         useCompressPub=True,
                         isUsed=True,
                         notForDirectUse=False,
                         keyBornBlock=10)
      
     
      airt.addChildRef(aikp)

      self.assertEqual(aikp.akpParScrAddr, airt.getScrAddr())
      self.assertEqual(aikp.akpParentRef.getScrAddr(), airt.getScrAddr())
      self.assertEqual(airt.akpChildByIndex[0].getScrAddr(), aikp.getScrAddr())
      self.assertEqual(airt.getChildByIndex(0).getScrAddr(), aikp.getScrAddr())
      self.assertTrue(aikp.getScrAddr() in airt.akpChildByScrAddr)


################################################################################
################################################################################
#
# Multisig BIP32 Extended Key tests 
#
################################################################################
################################################################################

################################################################################
class MBEK_Tests(unittest.TestCase):

   def testMBEK(self):
      raise NotImplementedError('Have not implemented any MBEK tests yet!')
      



if __name__ == "__main__":
   unittest.main()














