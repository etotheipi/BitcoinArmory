'''
Created on Aug 6, 2013

@author: Andy
'''
import sys
sys.path.append('..')
from pytest.Tiab import TiabTest, TOP_TIAB_BLOCK

import unittest

from CppBlockUtils import CryptoECDSA, SecureBinaryData
from armoryengine.ArmoryUtils import hex_to_binary, RightNow, int_to_binary, \
   checkAddrStrValid, hash256, UnserializeError, hash160_to_addrStr
from armoryengine.PyBtcAddress import PyBtcAddress


sys.argv.append('--nologging')

INIT_VECTOR = '77'*16
TEST_ADDR1_PRIV_KEY_ENCR1 = '500c41607d79c766859e6d9726ef1ea0fdf095922f3324454f6c4c34abcb23a5'
TEST_ADDR1_PRIV_KEY_ENCR2 = '7966cf5886494246cc5aaf7f1a4a2777cd6126612e7029d79ef9df47f6d6927d'
TEST_ADDR1_PRIV_KEY_ENCR3 = '0db5c1e9a8d1ebc0525bdb534626033b948804a9a34871d67bf58a3df11d6888'
TEST_ADDR1_PRIV_KEY_ENCR4 = '5db1314a20ae9fc978477ab3fe16ab17b246d813a541ecdd4143fcf082b19407'

TEST_PUB_KEY1 = '046c35e36776e997883ad4269dcc0696b10d68f6864ae73b8ad6ad03e879e43062a0139095ece3bd653b809fa7e8c7d78ffe6fac75a84c8283d8a000890bfc879d'

# Create an address to use for all subsequent tests
PRIVATE_KEY = SecureBinaryData(hex_to_binary('aa'*32))
PRIVATE_CHECKSUM = PRIVATE_KEY.getHash256()[:4]
PUBLIC_KEY  = CryptoECDSA().ComputePublicKey(PRIVATE_KEY)
ADDRESS_20  = PUBLIC_KEY.getHash160()

TEST_BLOCK_NUM = 100

# We pretend that we plugged some passphrases through a KDF
FAKE_KDF_OUTPUT1 = SecureBinaryData( hex_to_binary('11'*32) )
FAKE_KDF_OUTPUT2 = SecureBinaryData( hex_to_binary('22'*32) )

class PyBtcAddressTest(TiabTest):
   # TODO: This test needs more verification of the results.
   def testEncryptedAddress(self):


      # test serialization and unserialization of an empty PyBtcAddrss
      # Should serialize to a string that starts with 20 bytes of zeros
      # Unserialize should throw an UnserializeError caused by checksum mismatch
      emptyBtcAddr = PyBtcAddress()
      emptyBtcAddrSerialized = emptyBtcAddr.serialize()
      self.assertEqual(emptyBtcAddrSerialized[:20], hex_to_binary('00'*20))
      self.assertRaises(UnserializeError, PyBtcAddress().unserialize, emptyBtcAddrSerialized)

      # Test non-crashing
      testAddr1 = PyBtcAddress().createFromPlainKeyData(PRIVATE_KEY, ADDRESS_20)
      testAddr2 = PyBtcAddress().createFromPlainKeyData(PRIVATE_KEY, ADDRESS_20, chksum=PRIVATE_CHECKSUM)
      testAddr3 = PyBtcAddress().createFromPlainKeyData(PRIVATE_KEY, ADDRESS_20, publicKey65=PUBLIC_KEY)
      testAddr4 = PyBtcAddress().createFromPlainKeyData(PRIVATE_KEY, ADDRESS_20, publicKey65=PUBLIC_KEY, skipCheck=True)
      testAddr5 = PyBtcAddress().createFromPlainKeyData(PRIVATE_KEY, ADDRESS_20, skipPubCompute=True)
      
      testString = testAddr1.toString()
      self.assertTrue(len(testString) > 0)

      testAddr = PyBtcAddress().createFromPlainKeyData(PRIVATE_KEY, ADDRESS_20, publicKey65=PUBLIC_KEY)
      serializedAddr1 = testAddr.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr1)
      serializedRetest1 = retestAddr.serialize()
      self.assertEqual(serializedAddr1, serializedRetest1)
      
      theIV = SecureBinaryData(hex_to_binary(INIT_VECTOR))
      testAddr.enableKeyEncryption(theIV)
      testAddr.lock(FAKE_KDF_OUTPUT1)
      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), '')
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR1)
      
      serializedAddr2 = testAddr.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr2)
      serializedRetest2 = retestAddr.serialize()
      self.assertEqual(serializedAddr2, serializedRetest2)
      testAddr.unlock(FAKE_KDF_OUTPUT1)
      self.assertFalse(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), PRIVATE_KEY.toHexStr())
      
      testAddr.changeEncryptionKey(None, FAKE_KDF_OUTPUT1)
      self.assertTrue(testAddr.useEncryption)
      self.assertFalse(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), PRIVATE_KEY.toHexStr())
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR1)
      
      # Save off this data for a later test
      addr20_1      = testAddr.getAddr160()
      encryptedKey1 = testAddr.binPrivKey32_Encr
      encryptionIV1 = testAddr.binInitVect16
      plainPubKey1  = testAddr.binPublicKey65
   
      # OP(Key1 --> Unencrypted)
      testAddr.changeEncryptionKey(FAKE_KDF_OUTPUT1, None)
      self.assertFalse(testAddr.useEncryption)
      self.assertFalse(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), PRIVATE_KEY.toHexStr())
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), '')
      
      # OP(Unencrypted --> Key2)
      if not testAddr.isKeyEncryptionEnabled():
         testAddr.enableKeyEncryption(theIV)
      testAddr.changeEncryptionKey(None, FAKE_KDF_OUTPUT2)
      self.assertTrue(testAddr.useEncryption)
      self.assertFalse(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), PRIVATE_KEY.toHexStr())
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR2)
      
      # Save off this data for a later test
      addr20_2      = testAddr.getAddr160()
      encryptedKey2 = testAddr.binPrivKey32_Encr
      encryptionIV2 = testAddr.binInitVect16
      plainPubKey2  = testAddr.binPublicKey65
   
      # OP(Key2 --> Key1)
      testAddr.changeEncryptionKey(FAKE_KDF_OUTPUT2, FAKE_KDF_OUTPUT1)
      self.assertTrue(testAddr.useEncryption)
      self.assertFalse(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), PRIVATE_KEY.toHexStr())
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR1)
      
      # OP(Key1 --> Lock --> Key2)
      testAddr.lock(FAKE_KDF_OUTPUT1)
      testAddr.changeEncryptionKey(FAKE_KDF_OUTPUT1, FAKE_KDF_OUTPUT2)
      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), '')
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR2)
   
      # OP(Key2 --> Lock --> Unencrypted)
      testAddr.changeEncryptionKey(FAKE_KDF_OUTPUT2, None)
      self.assertFalse(testAddr.useEncryption)
      self.assertFalse(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), PRIVATE_KEY.toHexStr())
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), '')
      
      # Encryption Key Tests: 
      self.assertEqual(testAddr.serializePlainPrivateKey(), PRIVATE_KEY.toBinStr())
   
      # Test loading pre-encrypted key data
      testAddr = PyBtcAddress().createFromEncryptedKeyData(addr20_1, encryptedKey1, encryptionIV1)

      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), '')
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR1)
      
      # OP(EncrAddr --> Unlock1)
      testAddr.unlock(FAKE_KDF_OUTPUT1)
      self.assertTrue(testAddr.useEncryption)
      self.assertFalse(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), PRIVATE_KEY.toHexStr())
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR1)
   
      # OP(Unlock1 --> Lock1)
      testAddr.lock()
      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), '')
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR1)
      
      # OP(Lock1 --> Lock2)
      testAddr.changeEncryptionKey(FAKE_KDF_OUTPUT1, FAKE_KDF_OUTPUT2)
      self.assertTrue(testAddr.useEncryption)
      self.assertTrue(testAddr.isLocked)
      self.assertEqual(testAddr.binPrivKey32_Plain.toHexStr(), '')
      self.assertEqual(testAddr.binPrivKey32_Encr.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR2)
         
      # Test serializing locked wallet from pre-encrypted data'
      serializedAddr = testAddr.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr)
      serializedRetest = retestAddr.serialize()
      self.assertEqual(serializedAddr, serializedRetest)
   
      #############################################################################
      # Now testing chained-key (deterministic) address generation
      # Test chained priv key generation
      # Starting with plain key data
      chaincode = SecureBinaryData(hex_to_binary('ee'*32))
      addr0 = PyBtcAddress().createFromPlainKeyData(PRIVATE_KEY, ADDRESS_20)
      addr0.markAsRootAddr(chaincode)
      pub0  = addr0.binPublicKey65
   
      # Test serializing address-chain-root
      serializedAddr = addr0.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr)
      serializedRetest = retestAddr.serialize()
      self.assertEqual(serializedAddr, serializedRetest)
      self.assertEqual(retestAddr.binPrivKey32_Plain.toHexStr(), PRIVATE_KEY.toHexStr())
   
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
   
      # Addr1.PRIVATE_KEY == Addr1a.PRIVATE_KEY:',
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
      addr0 = PyBtcAddress().createFromPlainKeyData( PRIVATE_KEY, \
                                                willBeEncr=True, IV16=theIV)
      addr0.markAsRootAddr(chaincode)
      # OP(addr[0] plain)
   
      # Test serializing unlocked addr-chain-root
      serializedAddr = addr0.serialize()
      retestAddr = PyBtcAddress().unserialize(serializedAddr)
      serializedRetest = retestAddr.serialize()
      self.assertEqual(serializedAddr, serializedRetest)
      self.assertFalse(retestAddr.useEncryption)
   
      # OP(addr[0] locked)
      addr0.lock(FAKE_KDF_OUTPUT1)      
      self.assertEqual(addr0.binPrivKey32_Plain.toHexStr(), '')
   
      # OP(addr[0] w/Key --> addr[1])
      addr1 = addr0.extendAddressChain(FAKE_KDF_OUTPUT1, newIV=theIV)
      self.assertEqual(addr1.binPrivKey32_Plain.toHexStr(), '')
      
      # OP(addr[1] w/Key --> addr[2])
      addr2 = addr1.extendAddressChain(FAKE_KDF_OUTPUT1, newIV=theIV)
      addr2.unlock(FAKE_KDF_OUTPUT1)
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
      addr0 = PyBtcAddress().createFromPlainKeyData( PRIVATE_KEY, \
                                             willBeEncr=True, IV16=theIV)
      addr0.markAsRootAddr(chaincode)
      # OP(addr[0] locked)
      addr0.lock(FAKE_KDF_OUTPUT1)
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
   
      addr2.unlock(FAKE_KDF_OUTPUT1)
      priv2b = addr2.binPrivKey32_Plain.copy()
      # OP(addr[2] locked --> unlocked)
      self.assertEqual(priv2b.toHexStr(), TEST_ADDR1_PRIV_KEY_ENCR4)
   
   
      addr2.lock()
      # OP(addr[2] unlocked --> locked)'
      # Addr2.priv == Addr2b.priv:
      self.assertEqual(priv2, priv2b)
   
   # TODO: Add coverage for condition where TheBDM is in BlockchainReady state.
   def testTouch(self):
      testAddr = PyBtcAddress().createFromPlainKeyData(PRIVATE_KEY, ADDRESS_20, publicKey65=PUBLIC_KEY)
      theIV = SecureBinaryData(hex_to_binary(INIT_VECTOR))
      testAddr.enableKeyEncryption(theIV)
      rightNow = RightNow()
      testAddr.touch(rightNow)
      self.assertEqual(testAddr.timeRange[0], long(rightNow))
      self.assertEqual(testAddr.timeRange[1], long(rightNow))
      testAddr.touch(0)
      self.assertEqual(testAddr.timeRange[0], long(0))
      self.assertEqual(testAddr.timeRange[1], long(rightNow))
      testAddr.touch(blkNum=TEST_BLOCK_NUM)
      self.assertEqual(testAddr.blkRange[0], TEST_BLOCK_NUM)
      self.assertEqual(testAddr.blkRange[1], TOP_TIAB_BLOCK)
      testAddr.touch(blkNum=0)
      self.assertEqual(testAddr.blkRange[0], 0)
      self.assertEqual(testAddr.blkRange[1], TOP_TIAB_BLOCK)
      # Cover the case where the blkRange[0] starts at 0 
      testAddr.touch(blkNum=TEST_BLOCK_NUM)
      self.assertEqual(testAddr.blkRange[0], TEST_BLOCK_NUM)
      self.assertEqual(testAddr.blkRange[1], TOP_TIAB_BLOCK)
      
   def testCopy(self):
      testAddr = PyBtcAddress().createFromPlainKeyData(PRIVATE_KEY, ADDRESS_20, publicKey65=PUBLIC_KEY)
      testCopy = testAddr.copy()
      self.assertEqual(testAddr.binPrivKey32_Plain, testCopy.binPrivKey32_Plain)
      self.assertEqual(testAddr.binPrivKey32_Encr, testCopy.binPrivKey32_Encr)
      self.assertEqual(testAddr.binPublicKey65, testCopy.binPublicKey65)
      self.assertEqual(testAddr.binInitVect16, testCopy.binInitVect16)
      self.assertEqual(testAddr.isLocked, testCopy.isLocked)
      self.assertEqual(testAddr.useEncryption, testCopy.useEncryption)
      self.assertEqual(testAddr.isInitialized, testCopy.isInitialized)
      self.assertEqual(testAddr.keyChanged, testCopy.keyChanged)
      self.assertEqual(testAddr.walletByteLoc, testCopy.walletByteLoc)
      self.assertEqual(testAddr.chaincode, testCopy.chaincode)
      self.assertEqual(testAddr.chainIndex, testCopy.chainIndex)
   
   def testVerifyEncryptionKey(self):
      testAddr = PyBtcAddress().createFromPlainKeyData(PRIVATE_KEY, ADDRESS_20, publicKey65=PUBLIC_KEY)
      theIV = SecureBinaryData(hex_to_binary(INIT_VECTOR))
      testAddr.enableKeyEncryption(theIV)
      self.assertFalse(testAddr.verifyEncryptionKey(FAKE_KDF_OUTPUT1))
      testAddr.lock(FAKE_KDF_OUTPUT1)
      self.assertTrue(testAddr.verifyEncryptionKey(FAKE_KDF_OUTPUT1))
      self.assertFalse(testAddr.verifyEncryptionKey(FAKE_KDF_OUTPUT2))
      
   def testSimpleAddress(self):
      # Execute the tests with Satoshi's public key from the Bitcoin specification page
      satoshiPubKeyHex = '04fc9702847840aaf195de8442ebecedf5b095cdbb9bc716bda9110971b28a49e0ead8564ff0db22209e0374782c093bb899692d524e9d6a6956e7c5ecbcd68284'
      addrPiece1Hex = '65a4358f4691660849d9f235eb05f11fabbd69fa'
      addrPiece1Bin = hex_to_binary(addrPiece1Hex)
      satoshiAddrStr = hash160_to_addrStr(addrPiece1Bin)

      saddr = PyBtcAddress().createFromPublicKey( hex_to_binary(satoshiPubKeyHex) )
      print '\tAddr calc from pubkey: ', saddr.calculateAddrStr()
      self.assertTrue(checkAddrStrValid(satoshiAddrStr))
   
      testAddr = PyBtcAddress().createFromPlainKeyData(PRIVATE_KEY, ADDRESS_20, publicKey65=PUBLIC_KEY)
      msg = int_to_binary(39029348428)
      theHash = hash256(msg)
      derSig = testAddr.generateDERSignature(theHash)
      # Testing ECDSA signing & verification -- arbitrary binary strings:
      self.assertTrue(testAddr.verifyDERSignature( theHash, derSig))

# Running tests with "python <module name>" will NOT work for any Armory tests
# You must run tests with "python -m unittest <module name>" or run all tests with "python -m unittest discover"
# if __name__ == "__main__":
#    unittest.main()