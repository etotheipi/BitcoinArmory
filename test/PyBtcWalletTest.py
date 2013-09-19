'''
Created on Aug 14, 2013

@author: Andy
'''
import sys
sys.argv.append('--nologging')
import unittest
from utilities.ArmoryUtils import USE_TESTNET, convertKeyDataToAddress, hash256,\
   binary_to_hex, hex_to_binary, CLI_OPTIONS
from armoryengine import ARMORY_HOME_DIR, PyBtcWallet, WalletAddressError,\
   InterruptTestError, BLOCKCHAIN_READONLY, WalletLockError
import os
from CppBlockUtils import SecureBinaryData

WALLET_ROOT_ADDR = '5da74ed60a43a7ff11f0ba56cb0192b03518cc56'
NEW_UNUSED_ADDR = 'fb80e6fd042fa24178b897a6a70e1ae7eb56a20a'

class PyBtcWalletTest(unittest.TestCase):

   # *********************************************************************
   # Testing deterministic, encrypted wallet features'
   # *********************************************************************

   # Remove wallet files, need fresh dir for this test
   def testPyBtcWallet(self):
      shortlabel = 'TestWallet1'
      wltID = '3VB8XSmd'
      
      fileA    = os.path.join(ARMORY_HOME_DIR, 'armory_%s_.wallet' % wltID)
      fileB    = os.path.join(ARMORY_HOME_DIR, 'armory_%s_backup.wallet' % wltID)
      fileAupd = os.path.join(ARMORY_HOME_DIR, 'armory_%s_backup_unsuccessful.wallet' % wltID)
      fileBupd = os.path.join(ARMORY_HOME_DIR, 'armory_%s_update_unsuccessful.wallet' % wltID)

      for f in (fileA, fileB, fileAupd, fileBupd):
         # Removing file:', f, 
         if os.path.exists(f):
            os.remove(f)
            # ...removed!'
         else:
            # (DNE, do nothing)'
            pass
   
      # We need a controlled test, so we script the all the normally-random stuff
      privKey   = SecureBinaryData('\xaa'*32)
      privKey2  = SecureBinaryData('\x33'*32)
      chainstr  = SecureBinaryData('\xee'*32)
      theIV     = SecureBinaryData(hex_to_binary('77'*16))
      passphrase  = SecureBinaryData('A passphrase')
      passphrase2 = SecureBinaryData('A new passphrase')
      
      wlt = PyBtcWallet().createNewWallet(withEncrypt=False, \
                                          plainRootKey=privKey, \
                                          chaincode=chainstr,   \
                                          IV=theIV, \
                                          shortLabel=shortlabel)
      wlt.addrPoolSize = 5
      # No block chain loaded so this should return -1
      self.assertEqual(wlt.detectHighestUsedIndex(True), -1)
      self.assertEqual(wlt.kdfKey, None)
      self.assertEqual(binary_to_hex(wlt.addrMap['ROOT'].addrStr20), WALLET_ROOT_ADDR )
   
      # New wallet is at:', wlt.getWalletPath()
      self.assertEqual(len(wlt.linearAddr160List), CLI_OPTIONS.keypool)

      #############################################################################
      # (1) Getting a new address:
      newAddr = wlt.getNextUnusedAddress()
      wlt.pprint(indent=' '*5)
      self.assertEqual(binary_to_hex(newAddr.addrStr20), NEW_UNUSED_ADDR)
   
      # (1) Re-reading wallet from file, compare the two wallets
      wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
      self.assertTrue(wlt.isEqualTo(wlt2))
      
      #############################################################################
      # (2)Testing unencrypted wallet import-address'
      originalLength = len(wlt.linearAddr160List)
      wlt.importExternalAddressData(PRIVATE_KEY=privKey2)
      self.assertEqual(len(wlt.linearAddr160List), originalLength+1)
      
      # (2) Re-reading wallet from file, compare the two wallets
      wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
      self.assertTrue(wlt.isEqualTo(wlt2))
   
      # (2a)Testing deleteImportedAddress
      # Wallet size before delete:',  os.path.getsize(wlt.walletPath)
      # Addresses before delete:', len(wlt.linearAddr160List)
      toDelete160 = convertKeyDataToAddress(privKey2)
      wlt.deleteImportedAddress(toDelete160)
      self.assertEqual(len(wlt.linearAddr160List), originalLength)
      
   
      # (2a) Reimporting address for remaining tests
      # Wallet size before reimport:',  os.path.getsize(wlt.walletPath)
      wlt.importExternalAddressData(PRIVATE_KEY=privKey2)
      self.assertEqual(len(wlt.linearAddr160List), originalLength+1)
      
   
      # (2b)Testing ENCRYPTED wallet import-address
      privKey3  = SecureBinaryData('\xbb'*32)
      privKey4  = SecureBinaryData('\x44'*32)
      chainstr2  = SecureBinaryData('\xdd'*32)
      theIV2     = SecureBinaryData(hex_to_binary('66'*16))
      passphrase2= SecureBinaryData('hello')
      wltE = PyBtcWallet().createNewWallet(withEncrypt=True, \
                                          plainRootKey=privKey3, \
                                          securePassphrase=passphrase2, \
                                          chaincode=chainstr2,   \
                                          IV=theIV2, \
                                          shortLabel=shortlabel)
      
      #  We should have thrown an error about importing into a  locked wallet...
      self.assertRaises(WalletLockError, wltE.importExternalAddressData, PRIVATE_KEY=privKey2)


   
      wltE.unlock(securePassphrase=passphrase2)
      wltE.importExternalAddressData(PRIVATE_KEY=privKey2)
   
      # (2b) Re-reading wallet from file, compare the two wallets
      wlt2 = PyBtcWallet().readWalletFile(wltE.walletPath)
      self.assertTrue(wltE.isEqualTo(wlt2))
   
      # (2b) Unlocking wlt2 after re-reading locked-import-wallet
      wlt2.unlock(securePassphrase=passphrase2)
      self.assertFalse(wlt2.isLocked)

      #############################################################################
      # Now play with encrypted wallets
      # *********************************************************************'
      # (3)Testing conversion to encrypted wallet
   
      kdfParams = wlt.computeSystemSpecificKdfParams(0.1)
      wlt.changeKdfParams(*kdfParams)
   
      self.assertEqual(wlt.kdf.getSalt(), kdfParams[2])
      wlt.changeWalletEncryption( securePassphrase=passphrase )
      self.assertEqual(wlt.kdf.getSalt(), kdfParams[2])
      
      # (3) Re-reading wallet from file, compare the two wallets'
      wlt2 = PyBtcWallet().readWalletFile(wlt.getWalletPath())
      self.assertTrue(wlt.isEqualTo(wlt2))
      # NOTE:  this isEqual operation compares the serializations
      #        of the wallet addresses, which only contains the 
      #        encrypted versions of the private keys.  However,
      #        wlt is unlocked and contains the plaintext keys, too
      #        while wlt2 does not.
      wlt.lock()
      for key in wlt.addrMap:
         self.assertTrue(wlt.addrMap[key].isLocked)
         self.assertEqual(wlt.addrMap[key].binPrivKey32_Plain.toHexStr(), '')
   
      #############################################################################
      # (4)Testing changing passphrase on encrypted wallet',
   
      wlt.unlock( securePassphrase=passphrase )
      for key in wlt.addrMap:
         self.assertFalse(wlt.addrMap[key].isLocked)
         self.assertNotEqual(wlt.addrMap[key].binPrivKey32_Plain.toHexStr(), '')
      # ...to same passphrase'
      origKdfKey = wlt.kdfKey
      wlt.changeWalletEncryption( securePassphrase=passphrase )
      self.assertEqual(origKdfKey, wlt.kdfKey)
   
      # (4)And now testing new passphrase...'
      wlt.changeWalletEncryption( securePassphrase=passphrase2 )
      self.assertNotEqual(origKdfKey, wlt.kdfKey)
      
      # (4) Re-reading wallet from file, compare the two wallets'
      wlt2 = PyBtcWallet().readWalletFile(wlt.getWalletPath())
      self.assertTrue(wlt.isEqualTo(wlt2))
   
      #############################################################################
      # (5)Testing changing KDF on encrypted wallet'
   
      wlt.unlock( securePassphrase=passphrase2 )
   
      MEMORY_REQT_BYTES = 1024
      NUM_ITER = 999
      SALT_ALL_0 ='00'*32
      wlt.changeKdfParams(MEMORY_REQT_BYTES, NUM_ITER, hex_to_binary(SALT_ALL_0), passphrase2)
      self.assertEqual(wlt.kdf.getMemoryReqtBytes(), MEMORY_REQT_BYTES)
      self.assertEqual(wlt.kdf.getNumIterations(), NUM_ITER)
      self.assertEqual(wlt.kdf.getSalt().toHexStr(),  SALT_ALL_0)
   
      wlt.changeWalletEncryption( securePassphrase=passphrase2 )
      self.assertNotEqual(origKdfKey.toHexStr(), '')
   
      # (5) Get new address from locked wallet'
      # Locking wallet'
      wlt.lock()
      for i in range(10):
         wlt.getNextUnusedAddress()
      self.assertEqual(len(wlt.addrMap), CLI_OPTIONS.keypool+13)
      
      # (5) Re-reading wallet from file, compare the two wallets'
      wlt2 = PyBtcWallet().readWalletFile(wlt.getWalletPath())
      self.assertTrue(wlt.isEqualTo(wlt2))
   
      #############################################################################
      # !!!  #forkOnlineWallet()
      # (6)Testing forking encrypted wallet for online mode'
      wlt.forkOnlineWallet('OnlineVersionOfEncryptedWallet.bin')
      wlt2.readWalletFile('OnlineVersionOfEncryptedWallet.bin')
      for key in wlt2.addrMap:
         self.assertTrue(wlt.addrMap[key].isLocked)
         self.assertEqual(wlt.addrMap[key].binPrivKey32_Plain.toHexStr(), '')
      # (6)Getting a new addresses from both wallets'
      for i in range(wlt.addrPoolSize*2):
         wlt.getNextUnusedAddress()
         wlt2.getNextUnusedAddress()
   
      newaddr1 = wlt.getNextUnusedAddress()
      newaddr2 = wlt2.getNextUnusedAddress()   
      self.assertTrue(newaddr1.getAddr160() == newaddr2.getAddr160())
      self.assertEqual(len(wlt2.addrMap), 3*CLI_OPTIONS.keypool+14)
   
      # (6) Re-reading wallet from file, compare the two wallets
      wlt3 = PyBtcWallet().readWalletFile('OnlineVersionOfEncryptedWallet.bin')
      self.assertTrue(wlt3.isEqualTo(wlt2))
      #############################################################################
      # (7)Testing removing wallet encryption'
      # Wallet is locked?  ', wlt.isLocked
      wlt.unlock(securePassphrase=passphrase2)
      wlt.changeWalletEncryption( None )
      for key in wlt.addrMap:
         self.assertFalse(wlt.addrMap[key].isLocked)
         self.assertNotEqual(wlt.addrMap[key].binPrivKey32_Plain.toHexStr(), '')
   
      # (7) Re-reading wallet from file, compare the two wallets'
      wlt2 = PyBtcWallet().readWalletFile(wlt.getWalletPath())
      self.assertTrue(wlt.isEqualTo(wlt2))
   
      #############################################################################
      # \n'
      # *********************************************************************'
      # (8)Doing interrupt tests to test wallet-file-update recovery'
      def hashfile(fn):
         f = open(fn,'r')
         d = hash256(f.read())
         f.close()
         return binary_to_hex(d[:8])

      def verifyFileStatus(fileAExists = True, fileBExists = True, \
                           fileAupdExists = True, fileBupdExists = True):
         self.assertEqual(os.path.exists(fileA), fileAExists)
         self.assertEqual(os.path.exists(fileB), fileBExists)
         self.assertEqual(os.path.exists(fileAupd), fileAupdExists)
         self.assertEqual(os.path.exists(fileBupd), fileBupdExists)

      correctMainHash = hashfile(fileA)
      try:
         wlt.interruptTest1 = True
         wlt.getNextUnusedAddress()
      except InterruptTestError:
         # Interrupted!'
         pass
      wlt.interruptTest1 = False
   
      # (8a)Interrupted getNextUnusedAddress on primary file update'
      verifyFileStatus(True, True, False, True)
      # (8a)Do consistency check on the wallet'
      wlt.doWalletFileConsistencyCheck()
      verifyFileStatus(True, True, False, False)
      self.assertEqual(correctMainHash, hashfile(fileA))

      try:
         wlt.interruptTest2 = True
         wlt.getNextUnusedAddress()
      except InterruptTestError:
         # Interrupted!'
         pass
      wlt.interruptTest2 = False
   
      # (8b)Interrupted getNextUnusedAddress on between primary/backup update'
      verifyFileStatus(True, True, True, True)
      # (8b)Do consistency check on the wallet'
      wlt.doWalletFileConsistencyCheck()
      verifyFileStatus(True, True, False, False)
      self.assertEqual(hashfile(fileA), hashfile(fileB))
      # (8c) Try interrupting at state 3'
      verifyFileStatus(True, True, False, False)
   
      try:
         wlt.interruptTest3 = True
         wlt.getNextUnusedAddress()
      except InterruptTestError:
         # Interrupted!'
         pass
      wlt.interruptTest3 = False
   
      # (8c)Interrupted getNextUnusedAddress on backup file update'
      verifyFileStatus(True, True, True, False)
      # (8c)Do consistency check on the wallet'
      wlt.doWalletFileConsistencyCheck()
      verifyFileStatus(True, True, False, False)
      self.assertEqual(hashfile(fileA), hashfile(fileB))
   
      #############################################################################
      # \n'
      # *********************************************************************'
      # (9)Checksum-based byte-error correction tests!'
      # (9)Start with a good primary and backup file...'
   
      # (9a)Open primary wallet, change second byte in KDF'
      wltfile = open(wlt.walletPath,'r+b')
      wltfile.seek(326)
      wltfile.write('\xff')
      wltfile.close()
      # (9a)Byte changed, file hashes:'
      verifyFileStatus(True, True, False, False)
   
      # (9a)Try to read wallet from file, should correct KDF error, write fix'
      wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
      verifyFileStatus(True, True, False, False)
      self.assertNotEqual(hashfile(fileA), hashfile(fileB))
   
      # \n'
      # *********************************************************************'
      # (9b)Change a byte in each checksummed field in root addr'
      wltfile = open(wlt.walletPath,'r+b')
      wltfile.seek(838);  wltfile.write('\xff')
      wltfile.seek(885);  wltfile.write('\xff')
      wltfile.seek(929);  wltfile.write('\xff')
      wltfile.seek(954);  wltfile.write('\xff')
      wltfile.seek(1000);  wltfile.write('\xff')
      wltfile.close()
      # (9b) New file hashes...'
      verifyFileStatus(True, True, False, False)
   
      # (9b)Try to read wallet from file, should correct address errors'
      wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
      verifyFileStatus(True, True, False, False)
      self.assertNotEqual(hashfile(fileA), hashfile(fileB))
      
      # \n'
      # *********************************************************************'
      # (9c)Change a byte in each checksummed field, of first non-root addr'
      wltfile = open(wlt.walletPath,'r+b')
      wltfile.seek(1261+21+838);  wltfile.write('\xff')
      wltfile.seek(1261+21+885);  wltfile.write('\xff')
      wltfile.seek(1261+21+929);  wltfile.write('\xff')
      wltfile.seek(1261+21+954);  wltfile.write('\xff')
      wltfile.seek(1261+21+1000);  wltfile.write('\xff')
      wltfile.close()
      # (9c) New file hashes...'
      verifyFileStatus(True, True, False, False)
   
      # (9c)Try to read wallet from file, should correct address errors'
      wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
      verifyFileStatus(True, True, False, False)
      self.assertNotEqual(hashfile(fileA), hashfile(fileB))
   
      # \n'
      # *********************************************************************'
      # (9d)Now butcher the CHECKSUM, see if correction works'
      wltfile = open(wlt.walletPath,'r+b')
      wltfile.seek(977); wltfile.write('\xff')
      wltfile.close()
      # (9d) New file hashes...'
      verifyFileStatus(True, True, False, False)
   
      # (9d)Try to read wallet from file, should correct address errors'
      wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
      verifyFileStatus(True, True, False, False)
      self.assertNotEqual(hashfile(fileA), hashfile(fileB))
   
   
      # *******'
      # (9z) Test comment I/O'
      comment1 = 'This is my normal unit-testing address.'
      comment2 = 'This is fake tx... no tx has this hash.'
      comment3 = comment1 + '  Corrected!'
      hash1 = '\x1f'*20  # address160
      hash2 = '\x2f'*32  # tx hash
      wlt.setComment(hash1, comment1)
      wlt.setComment(hash2, comment2)
      wlt.setComment(hash1, comment3)
   
      wlt2 = PyBtcWallet().readWalletFile(wlt.walletPath)
      c3 = wlt2.getComment(hash1)
      c2 = wlt2.getComment(hash2)
      self.assertEqual(c3, comment3)
      self.assertEqual(c2, comment2)

if __name__ == "__main__":
   #import sys;sys.argv = ['', 'Test.testName']
   unittest.main()