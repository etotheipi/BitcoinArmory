'''
Created on Aug 6, 2013

@author: Andy
'''
import unittest
from armoryengine import hex_to_binary, PyBtcAddress, prettyHex, binary_to_hex,\
   UnserializeError
from CppBlockUtils import CryptoECDSA, SecureBinaryData

INIT_VECTOR = '77'*16
TEST_ADDR1_PRIV_KEY_ENCR1 = '500c41607d79c766859e6d9726ef1ea0fdf095922f3324454f6c4c34abcb23a5'
TEST_ADDR1_PRIV_KEY_ENCR2 = '7966cf5886494246cc5aaf7f1a4a2777cd6126612e7029d79ef9df47f6d6927d'
TEST_ADDR1_PRIV_KEY_ENCR3 = '0db5c1e9a8d1ebc0525bdb534626033b948804a9a34871d67bf58a3df11d6888'
TEST_ADDR1_PRIV_KEY_ENCR4 = '5db1314a20ae9fc978477ab3fe16ab17b246d813a541ecdd4143fcf082b19407'

TEST_PUB_KEY1 = '046c35e36776e997883ad4269dcc0696b10d68f6864ae73b8ad6ad03e879e43062a0139095ece3bd653b809fa7e8c7d78ffe6fac75a84c8283d8a000890bfc879d'
class PyBtcAddressTest(unittest.TestCase):


   def setUp(self):
      pass

   
   def tearDown(self):
      pass


   # TODO: This test needs more verification of the results.
   def testEncryptedAddress(self):
      # Create an address to use for all subsequent tests
      privKey = SecureBinaryData(hex_to_binary('aa'*32))
      privChk = privKey.getHash256()[:4]
      pubKey  = CryptoECDSA().ComputePublicKey(privKey)
      addr20  = pubKey.getHash160()
      
      # We pretend that we plugged some passphrases through a KDF
      fakeKdfOutput1 = SecureBinaryData( hex_to_binary('11'*32) )
      fakeKdfOutput2 = SecureBinaryData( hex_to_binary('22'*32) )

      # test serialization and unserialization of an empty PyBtcAddrss
      # Should serialize to a string that starts with 20 bytes of zeros
      # Unserialize should throw an UnserializeError caused by checksum mismatch
      emptyBtcAddr = PyBtcAddress()
      emptyBtcAddrSerialized = emptyBtcAddr.serialize()
      self.assertEqual(emptyBtcAddrSerialized[:20], hex_to_binary('00'*20))
      self.assertRaises(UnserializeError, PyBtcAddress().unserialize, emptyBtcAddrSerialized)

      # Test non-crashing
      testAddr1 = PyBtcAddress().createFromPlainKeyData(privKey, addr20)
      testAddr2 = PyBtcAddress().createFromPlainKeyData(privKey, addr20, chksum=privChk)
      testAddr3 = PyBtcAddress().createFromPlainKeyData(privKey, addr20, publicKey65=pubKey)
      testAddr4 = PyBtcAddress().createFromPlainKeyData(privKey, addr20, publicKey65=pubKey, skipCheck=True)
      testAddr5 = PyBtcAddress().createFromPlainKeyData(privKey, addr20, skipPubCompute=True)
      
      testAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20, publicKey65=pubKey)
      serializedAddr1 = testAddr.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr1)
      serializedRetest1 = retestAddr.serialize()
      self.assertEqual(serializedAddr1, serializedRetest1)
      
      theIV = SecureBinaryData(hex_to_binary(INIT_VECTOR))
      testAddr.enableKeyEncryption(theIV)
      testAddr.lock(fakeKdfOutput1)
      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), '')
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR1)
      
      serializedAddr2 = testAddr.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr2)
      serializedRetest2 = retestAddr.serialize()
      self.assertEqual(serializedAddr2, serializedRetest2)
      testAddr.unlock(fakeKdfOutput1)
      self.assertTrue(not testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), privKey.toHexStr())
      
      testAddr.changeEncryptionKey(None, fakeKdfOutput1)
      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(not testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), privKey.toHexStr())
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR1)
      
      # Save off this data for a later test
      addr20_1      = testAddr.getAddr160()
      encryptedKey1 = testAddr.binPrivKey32_Encr
      encryptionIV1 = testAddr.binInitVect16
      plainPubKey1  = testAddr.binPublicKey65
   
      # OP(Key1 --> Unencrypted)
      testAddr.changeEncryptionKey(fakeKdfOutput1, None)
      self.assertTrue(not testAddr.useEncryption)
      self.assertTrue(not testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), privKey.toHexStr())
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), '')
      
      # OP(Unencrypted --> Key2)
      if not testAddr.isKeyEncryptionEnabled():
         testAddr.enableKeyEncryption(theIV)
      testAddr.changeEncryptionKey(None, fakeKdfOutput2)
      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(not testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), privKey.toHexStr())
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR2)
      
      # Save off this data for a later test
      addr20_2      = testAddr.getAddr160()
      encryptedKey2 = testAddr.binPrivKey32_Encr
      encryptionIV2 = testAddr.binInitVect16
      plainPubKey2  = testAddr.binPublicKey65
   
      # OP(Key2 --> Key1)
      testAddr.changeEncryptionKey(fakeKdfOutput2, fakeKdfOutput1)
      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(not testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), privKey.toHexStr())
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR1)
      
      # OP(Key1 --> Lock --> Key2)
      testAddr.lock(fakeKdfOutput1)
      testAddr.changeEncryptionKey(fakeKdfOutput1, fakeKdfOutput2)
      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), '')
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR2)
   
      # OP(Key2 --> Lock --> Unencrypted)
      testAddr.changeEncryptionKey(fakeKdfOutput2, None)
      self.assertTrue(not testAddr.useEncryption)
      self.assertTrue(not testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), privKey.toHexStr())
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), '')
      
      # Encryption Key Tests: 
      self.assertEqual(testAddr.serializePlainPrivateKey(), privKey.toBinStr())
   
      # Test loading pre-encrypted key data
      testAddr = PyBtcAddress().createFromEncryptedKeyData(addr20_1, encryptedKey1, encryptionIV1)

      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), '')
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR1)
      
      # OP(EncrAddr --> Unlock1)
      testAddr.unlock(fakeKdfOutput1)
      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(not testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), privKey.toHexStr())
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR1)
   
      # OP(Unlock1 --> Lock1)
      testAddr.lock()
      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), '')
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR1)
      
      # OP(Lock1 --> Lock2)
      testAddr.changeEncryptionKey(fakeKdfOutput1, fakeKdfOutput2)
      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), '')
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR2)
         
      print '\nTest serializing locked wallet from pre-encrypted data',
      serializedAddr = testAddr.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr)
      serializedRetest = retestAddr.serialize()
      self.assertEqual(serializedAddr, serializedRetest)
   
      #############################################################################
      # Now testing chained-key (deterministic) address generation
      # Test chained priv key generation
      # Starting with plain key data
      chaincode = SecureBinaryData(hex_to_binary('ee'*32))
      addr0 = PyBtcAddress().createFromPlainKeyData(privKey, addr20)
      addr0.markAsRootAddr(chaincode)
      pub0  = addr0.binPublicKey65
   
      # Test serializing address-chain-root
      serializedAddr = addr0.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr)
      serializedRetest = retestAddr.serialize()
      self.assertEqual(serializedAddr, serializedRetest)
      self.assertEqual(retestAddr.binPrivKey32_Plain.toHexStr(), privKey.toHexStr())
   
      # Generate chained PRIVATE key address
      # OP(addr[0] --> addr[1])
      addr1 = addr0.extendAddressChain()
      self.assertEqual(addr1.binPrivKey32_Plain.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR3)
   
      # OP(addr[0] --> addr[1]) [again]'
      addr1a = addr0.extendAddressChain()
      self.assertEqual(addr1a.binPrivKey32_Plain.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR3)
   
      # OP(addr[1] --> addr[2])
      addr2 = addr1.extendAddressChain()
      pub2 = addr2.binPublicKey65.copy()
      priv2 = addr2.binPrivKey32_Plain.copy()
      self.assertEqual(priv2.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR4)
   
      # Addr1.privKey == Addr1a.privKey:',
      self.assertEqual(addr1.binPublicKey65, addr1a.binPublicKey65)
   
      # Test serializing priv-key-chained',
      serializedAddr = addr2.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr)
      serializedRetest = retestAddr.serialize()
      self.assertEqual(serializedAddr, serializedRetest)
      
      #############################################################################
      # Generate chained PUBLIC key address
      # addr[0]
      addr0 = PyBtcAddress().createFromPublicKeyData(pub0)
      addr0.markAsRootAddr(chaincode)
      self.assertEqual(addr0.chainIndex,  -1)
      self.assertEqual(addr0.chaincode,  chaincode)
   
      # Test serializing pub-key-only-root',
      serializedAddr = addr0.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr)
      serializedRetest = retestAddr.serialize()
      self.assertEqual(serializedAddr, serializedRetest)
   
      # OP(addr[0] --> addr[1])'
      addr1 = addr0.extendAddressChain()
      self.assertEqual(addr1.binPrivKey32_Plain.toHexStr(), '')
      
   
      # OP(addr[1] --> addr[2])'
      addr2 = addr1.extendAddressChain()
      pub2a = addr2.binPublicKey65.copy()
      self.assertEqual(addr2.binPrivKey32_Plain.toHexStr(), '')
      self.assertEqual(pub2a.toHexStr(), TEST_PUB_KEY1)
   
      # Addr2.PublicKey == Addr2a.PublicKey:'
      # Test serializing pub-key-from-chain'
      serializedAddr = addr2.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr)
      serializedRetest = retestAddr.serialize()
      self.assertEqual(serializedAddr, serializedRetest)
   
      #############################################################################
      # Generate chained keys from locked addresses
      addr0 = PyBtcAddress().createFromPlainKeyData( privKey, \
                                                willBeEncr=True, IV16=theIV)
      addr0.markAsRootAddr(chaincode)
      # OP(addr[0] plain)
   
      # Test serializing unlocked addr-chain-root
      serializedAddr = addr0.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr)
      serializedRetest = retestAddr.serialize()
      self.assertEqual(serializedAddr, serializedRetest)
      self.assertTrue(not retestAddr.useEncryption)
   
      # OP(addr[0] locked)
      addr0.lock(fakeKdfOutput1)      
      self.assertEqual(addr0.binPrivKey32_Plain.toHexStr(), '')
   
      # OP(addr[0] w/Key --> addr[1])
      addr1 = addr0.extendAddressChain(fakeKdfOutput1, newIV=theIV)
      self.assertEqual(addr1.binPrivKey32_Plain.toHexStr(), '')
      
      # OP(addr[1] w/Key --> addr[2])
      addr2 = addr1.extendAddressChain(fakeKdfOutput1, newIV=theIV)
      addr2.unlock(fakeKdfOutput1)
      priv2a = addr2.binPrivKey32_Plain.copy()
      addr2.lock()
      self.assertEqual(addr2.binPrivKey32_Plain.toHexStr(), '')
   
      # Addr2.priv == Addr2a.priv:
      self.assertEqual(priv2, priv2a)
   
      # Test serializing chained address from locked root
      serializedAddr = addr2.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr)
      serializedRetest = retestAddr.serialize()
      self.assertEqual(serializedAddr, serializedRetest)
   
      #############################################################################
      # Generate chained keys from locked addresses, no unlocking
      addr0 = PyBtcAddress().createFromPlainKeyData( privKey, \
                                             willBeEncr=True, IV16=theIV)
      addr0.markAsRootAddr(chaincode)
      # OP(addr[0] locked)
      addr0.lock(fakeKdfOutput1)
      self.assertEqual(addr0.binPrivKey32_Plain.toHexStr(), '')
   
      # OP(addr[0] locked --> addr[1] locked)'
      addr1 = addr0.extendAddressChain(newIV=theIV)
      self.assertEqual(addr1.binPrivKey32_Plain.toHexStr(), '')
   
      # OP(addr[1] locked --> addr[2] locked)
      addr2 = addr1.extendAddressChain(newIV=theIV)
      pub2b = addr2.binPublicKey65.copy()
      self.assertEqual(addr2.binPrivKey32_Plain.toHexStr(), '')
      self.assertEqual(pub2b.toHexStr(), TEST_PUB_KEY1)
   
      # Addr2.Pub == Addr2b.pub:
      # Test serializing priv-key-bearing address marked for unlock
      serializedAddr = addr2.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr)
      serializedRetest = retestAddr.serialize()
      self.assertEqual(serializedAddr, serializedRetest)
   
      addr2.unlock(fakeKdfOutput1)
      priv2b = addr2.binPrivKey32_Plain.copy()
      # OP(addr[2] locked --> unlocked)
      self.assertEqual(priv2b.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR4)
   
   
      addr2.lock()
      # OP(addr[2] unlocked --> locked)'
      # Addr2.priv == Addr2b.priv:
      self.assertEqual(priv2, priv2b)
   
   
if __name__ == "__main__":
   #import sys;sys.argv = ['', 'Test.testName']
   unittest.main()