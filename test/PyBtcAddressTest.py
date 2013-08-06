'''
Created on Aug 6, 2013

@author: Andy
'''
import unittest
from armoryengine import hex_to_binary, PyBtcAddress, prettyHex, binary_to_hex,\
   UnserializeError
from CppBlockUtils import CryptoECDSA, SecureBinaryData


class PyBtcAddressTest(unittest.TestCase):


   def setUp(self):
      pass

   
   def tearDown(self):
      pass


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
      testAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20)
      testAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20, chksum=privChk)
      testAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20, publicKey65=pubKey)
      testAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20, publicKey65=pubKey, skipCheck=True)
      testAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20, skipPubCompute=True)
      
      testAddr1 = PyBtcAddress().createFromPlainKeyData(privKey, addr20, publicKey65=pubKey)
      serializedAddr1 = testAddr1.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr1)
      serializedRetest1 = retestAddr.serialize()
      self.assertEqual(serializedAddr1, serializedRetest1)
      
      theIV = SecureBinaryData(hex_to_binary('77'*16))
      testAddr1.enableKeyEncryption(theIV)
      testAddr1.lock(fakeKdfOutput1)
      self.assertTrue(testAddr1.useEncryption)
      self.assertTrue(testAddr1.isLocked)
      
      serializedAddr2 = testAddr1.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr2)
      serializedRetest2 = retestAddr.serialize()
      self.assertEqual(serializedAddr2, serializedRetest2)
      testAddr1.unlock(fakeKdfOutput1)
      self.assertTrue(not testAddr1.isLocked)
      
      serializedAddr3 = testAddr1.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr3)
      serializedRetest3 = retestAddr.serialize()
      self.assertEqual(serializedAddr3, serializedRetest3)
      
      testAddr2 = PyBtcAddress().createFromPlainKeyData(privKey, addr20, publicKey65=pubKey)
      testAddr2.enableKeyEncryption(theIV)
      testAddr2.changeEncryptionKey(None, fakeKdfOutput1)
      self.assertTrue(testAddr2.useEncryption)
      self.assertTrue(not testAddr2.isLocked)
   
      # Save off this data for a later test
      addr20_1      = testAddr2.getAddr160()
      encryptedKey1 = testAddr2.binPrivKey32_Encr
      encryptionIV1 = testAddr2.binInitVect16
      plainPubKey1  = testAddr2.binPublicKey65
   
      # OP(Key1 --> Unencrypted)
      testAddr2.changeEncryptionKey(fakeKdfOutput1, None)
      self.assertTrue(not testAddr2.useEncryption)
      self.assertTrue(not testAddr2.isLocked)
         
      # OP(Unencrypted --> Key2)
      if not testAddr2.isKeyEncryptionEnabled():
         testAddr2.enableKeyEncryption(theIV)
      testAddr2.changeEncryptionKey(None, fakeKdfOutput2)
      self.assertTrue(testAddr2.useEncryption)
      self.assertTrue(not testAddr2.isLocked)
      
   
      # Save off this data for a later test
      addr20_2      = testAddr2.getAddr160()
      encryptedKey2 = testAddr2.binPrivKey32_Encr
      encryptionIV2 = testAddr2.binInitVect16
      plainPubKey2  = testAddr2.binPublicKey65
   
      # OP(Key2 --> Key1)
      testAddr2.changeEncryptionKey(fakeKdfOutput2, fakeKdfOutput1)
      self.assertTrue(testAddr2.useEncryption)
      self.assertTrue(not testAddr2.isLocked)
   
      # OP(Key1 --> Lock --> Key2)
      testAddr2.lock(fakeKdfOutput1)
      testAddr2.changeEncryptionKey(fakeKdfOutput1, fakeKdfOutput2)
      self.assertTrue(testAddr2.useEncryption)
      self.assertTrue(testAddr2.isLocked)
   
      # OP(Key2 --> Lock --> Unencrypted)
      testAddr2.changeEncryptionKey(fakeKdfOutput2, None)
      self.assertTrue(not testAddr2.useEncryption)
      self.assertTrue(not testAddr2.isLocked)
      
      # Encryption Key Tests: 
      self.assertEqual(testAddr2.serializePlainPrivateKey(), privKey.toBinStr())
   
if __name__ == "__main__":
   #import sys;sys.argv = ['', 'Test.testName']
   unittest.main()