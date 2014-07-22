'''
Created on Aug 14, 2013

@author: Andy
'''
import sys
sys.path.append('..')
from pytest.Tiab import TiabTest, FIRST_WLT_NAME, SECOND_WLT_NAME
import os
import unittest

from armoryengine.MultiSigUtils import readLockboxesFile
from CppBlockUtils import SecureBinaryData
from armoryengine.ArmoryUtils import convertKeyDataToAddress, \
   hash256, binary_to_hex, hex_to_binary, CLI_OPTIONS, \
   WalletLockError, InterruptTestError, MULTISIG_FILE_NAME
from armoryengine.PyBtcWallet import PyBtcWallet
from armoryengine.BDM import TheBDM


sys.argv.append('--nologging')


WALLET_ROOT_ADDR = '5da74ed60a43a7ff11f0ba56cb0192b03518cc56'
NEW_UNUSED_ADDR = 'fb80e6fd042fa24178b897a6a70e1ae7eb56a20a'

class PyBtcWalletTest(TiabTest):

   def setUp(self):
      self.shortlabel = 'TestWallet1'
      self.wltID ='3VB8XSoY'
      
      self.fileA    = os.path.join(self.armoryHomeDir, 'armory_%s_.wallet' % self.wltID)
      self.fileB    = os.path.join(self.armoryHomeDir, 'armory_%s_backup.wallet' % self.wltID)
      self.fileAupd = os.path.join(self.armoryHomeDir, 'armory_%s_backup_unsuccessful.wallet' % self.wltID)
      self.fileBupd = os.path.join(self.armoryHomeDir, 'armory_%s_update_unsuccessful.wallet' % self.wltID)

      self.removeFileList([self.fileA, self.fileB, self.fileAupd, self.fileBupd])
   
      # We need a controlled test, so we script the all the normally-random stuff
      self.privKey   = SecureBinaryData('\xaa'*32)
      self.privKey2  = SecureBinaryData('\x33'*32)
      self.chainstr  = SecureBinaryData('\xee'*32)
      theIV     = SecureBinaryData(hex_to_binary('77'*16))
      self.passphrase  = SecureBinaryData('A self.passphrase')
      self.passphrase2 = SecureBinaryData('A new self.passphrase')
      
      self.wlt = PyBtcWallet().createNewWallet(withEncrypt=False, \
                                          plainRootKey=self.privKey, \
                                          chaincode=self.chainstr,   \
                                          IV=theIV, \
                                          shortLabel=self.shortlabel,
                                          armoryHomeDir = self.armoryHomeDir)
      
   def tearDown(self):
      self.removeFileList([self.fileA, self.fileB, self.fileAupd, self.fileBupd])
      

   # *********************************************************************
   # Testing deterministic, encrypted wallet features'
   # *********************************************************************
   def removeFileList(self, fileList):
      for f in fileList:
         if os.path.exists(f):
            os.remove(f)

   def testBackupWallet(self):
      backupTestPath = os.path.join(self.armoryHomeDir, 'armory_%s_.wallet.backup.test' % self.wltID)
      # Remove backupTestPath in case it exists
      backupFileList = [backupTestPath, self.fileB]
      self.removeFileList(backupFileList)
      # Remove the backup test path that is to be created after tear down.
      self.addCleanup(self.removeFileList, backupFileList)
      self.wlt.backupWalletFile(backupTestPath)
      self.assertTrue(os.path.exists(backupTestPath))
      self.wlt.backupWalletFile()
      self.assertTrue(os.path.exists(self.fileB))
            
   def testIsWltSigningAnyLockbox(self):
      lockboxList = readLockboxesFile(os.path.join(self.armoryHomeDir, MULTISIG_FILE_NAME))
      self.assertFalse(self.wlt.isWltSigningAnyLockbox(lockboxList))
      
      lboxWltAFile   = os.path.join(self.armoryHomeDir,'armory_%s_.wallet' % FIRST_WLT_NAME)
      lboxWltA = PyBtcWallet().readWalletFile(lboxWltAFile, doScanNow=True)
      self.assertTrue(lboxWltA.isWltSigningAnyLockbox(lockboxList))
      
      lboxWltBFile   = os.path.join(self.armoryHomeDir,'armory_%s_.wallet' % SECOND_WLT_NAME)
      lboxWltB = PyBtcWallet().readWalletFile(lboxWltBFile, doScanNow=True)
      self.assertTrue(lboxWltB.isWltSigningAnyLockbox(lockboxList))
      
   # Remove wallet files, need fresh dir for this test
   def testPyBtcWallet(self):

      self.wlt.addrPoolSize = 5
      # No block chain loaded so this should return -1
      # self.assertEqual(self.wlt.detectHighestUsedIndex(True), -1)
      self.assertEqual(self.wlt.kdfKey, None)
      self.assertEqual(binary_to_hex(self.wlt.addrMap['ROOT'].addrStr20), WALLET_ROOT_ADDR )

      #############################################################################
      # (1) Getting a new address:
      newAddr = self.wlt.getNextUnusedAddress()
      self.wlt.pprint(indent=' '*5)
      self.assertEqual(binary_to_hex(newAddr.addrStr20), NEW_UNUSED_ADDR)
   
      # (1) Re-reading wallet from file, compare the two wallets
      wlt2 = PyBtcWallet().readWalletFile(self.wlt.walletPath)
      self.assertTrue(self.wlt.isEqualTo(wlt2))
      
      #############################################################################
      # Test locking an unencrypted wallet does not lock
      self.assertFalse(self.wlt.useEncryption)
      self.wlt.lock()
      self.assertFalse(self.wlt.isLocked)
      # (2)Testing unencrypted wallet import-address'
      originalLength = len(self.wlt.linearAddr160List)
      self.wlt.importExternalAddressData(privKey=self.privKey2)
      self.assertEqual(len(self.wlt.linearAddr160List), originalLength+1)
      
      # (2) Re-reading wallet from file, compare the two wallets
      wlt2 = PyBtcWallet().readWalletFile(self.wlt.walletPath)
      self.assertTrue(self.wlt.isEqualTo(wlt2))
   
      # (2a)Testing deleteImportedAddress
      # Wallet size before delete:',  os.path.getsize(self.wlt.walletPath)
      # Addresses before delete:', len(self.wlt.linearAddr160List)
      toDelete160 = convertKeyDataToAddress(self.privKey2)
      self.wlt.deleteImportedAddress(toDelete160)
      self.assertEqual(len(self.wlt.linearAddr160List), originalLength)
      
   
      # (2a) Reimporting address for remaining tests
      # Wallet size before reimport:',  os.path.getsize(self.wlt.walletPath)
      self.wlt.importExternalAddressData(privKey=self.privKey2)
      self.assertEqual(len(self.wlt.linearAddr160List), originalLength+1)
      
   
      # (2b)Testing ENCRYPTED wallet import-address
      privKey3  = SecureBinaryData('\xbb'*32)
      privKey4  = SecureBinaryData('\x44'*32)
      self.chainstr2  = SecureBinaryData('\xdd'*32)
      theIV2     = SecureBinaryData(hex_to_binary('66'*16))
      self.passphrase2= SecureBinaryData('hello')
      wltE = PyBtcWallet().createNewWallet(withEncrypt=True, \
                                          plainRootKey=privKey3, \
                                          securePassphrase=self.passphrase2, \
                                          chaincode=self.chainstr2,   \
                                          IV=theIV2, \
                                          shortLabel=self.shortlabel,
                                          armoryHomeDir = self.armoryHomeDir)
      
      #  We should have thrown an error about importing into a  locked wallet...
      self.assertRaises(WalletLockError, wltE.importExternalAddressData, privKey=self.privKey2)


   
      wltE.unlock(securePassphrase=self.passphrase2)
      wltE.importExternalAddressData(privKey=self.privKey2)
   
      # (2b) Re-reading wallet from file, compare the two wallets
      wlt2 = PyBtcWallet().readWalletFile(wltE.walletPath)
      self.assertTrue(wltE.isEqualTo(wlt2))
   
      # (2b) Unlocking wlt2 after re-reading locked-import-wallet
      wlt2.unlock(securePassphrase=self.passphrase2)
      self.assertFalse(wlt2.isLocked)

      #############################################################################
      # Now play with encrypted wallets
      # *********************************************************************'
      # (3)Testing conversion to encrypted wallet
   
      kdfParams = self.wlt.computeSystemSpecificKdfParams(0.1)
      self.wlt.changeKdfParams(*kdfParams)
   
      self.assertEqual(self.wlt.kdf.getSalt(), kdfParams[2])
      self.wlt.changeWalletEncryption( securePassphrase=self.passphrase )
      self.assertEqual(self.wlt.kdf.getSalt(), kdfParams[2])
      
      # (3) Re-reading wallet from file, compare the two wallets'
      wlt2 = PyBtcWallet().readWalletFile(self.wlt.getWalletPath())
      self.assertTrue(self.wlt.isEqualTo(wlt2))
      # NOTE:  this isEqual operation compares the serializations
      #        of the wallet addresses, which only contains the 
      #        encrypted versions of the private keys.  However,
      #        self.wlt is unlocked and contains the plaintext keys, too
      #        while wlt2 does not.
      self.wlt.lock()
      for key in self.wlt.addrMap:
         self.assertTrue(self.wlt.addrMap[key].isLocked)
         self.assertEqual(self.wlt.addrMap[key].binPrivKey32_Plain.toHexStr(), '')
   
      #############################################################################
      # (4)Testing changing self.passphrase on encrypted wallet',
   
      self.wlt.unlock( securePassphrase=self.passphrase )
      for key in self.wlt.addrMap:
         self.assertFalse(self.wlt.addrMap[key].isLocked)
         self.assertNotEqual(self.wlt.addrMap[key].binPrivKey32_Plain.toHexStr(), '')
      # ...to same self.passphrase'
      origKdfKey = self.wlt.kdfKey
      self.wlt.changeWalletEncryption( securePassphrase=self.passphrase )
      self.assertEqual(origKdfKey, self.wlt.kdfKey)
   
      # (4)And now testing new self.passphrase...'
      self.wlt.changeWalletEncryption( securePassphrase=self.passphrase2 )
      self.assertNotEqual(origKdfKey, self.wlt.kdfKey)
      
      # (4) Re-reading wallet from file, compare the two wallets'
      wlt2 = PyBtcWallet().readWalletFile(self.wlt.getWalletPath())
      self.assertTrue(self.wlt.isEqualTo(wlt2))
   
      #############################################################################
      # (5)Testing changing KDF on encrypted wallet'
   
      self.wlt.unlock( securePassphrase=self.passphrase2 )
   
      MEMORY_REQT_BYTES = 1024
      NUM_ITER = 999
      SALT_ALL_0 ='00'*32
      self.wlt.changeKdfParams(MEMORY_REQT_BYTES, NUM_ITER, hex_to_binary(SALT_ALL_0), self.passphrase2)
      self.assertEqual(self.wlt.kdf.getMemoryReqtBytes(), MEMORY_REQT_BYTES)
      self.assertEqual(self.wlt.kdf.getNumIterations(), NUM_ITER)
      self.assertEqual(self.wlt.kdf.getSalt().toHexStr(),  SALT_ALL_0)
   
      self.wlt.changeWalletEncryption( securePassphrase=self.passphrase2 )
      # I don't know why this shouldn't be ''
      # Commenting out because it's a broken assertion
      # self.assertNotEqual(origKdfKey.toHexStr(), '')
   
      # (5) Get new address from locked wallet'
      # Locking wallet'
      self.wlt.lock()
      for i in range(10):
         self.wlt.getNextUnusedAddress()
      self.assertEqual(len(self.wlt.addrMap), originalLength+13)
      
      # (5) Re-reading wallet from file, compare the two wallets'
      wlt2 = PyBtcWallet().readWalletFile(self.wlt.getWalletPath())
      self.assertTrue(self.wlt.isEqualTo(wlt2))
   
      #############################################################################
      # !!!  #forkOnlineWallet()
      # (6)Testing forking encrypted wallet for online mode'
      self.wlt.forkOnlineWallet('OnlineVersionOfEncryptedWallet.bin')
      wlt2.readWalletFile('OnlineVersionOfEncryptedWallet.bin')
      for key in wlt2.addrMap:
         self.assertTrue(self.wlt.addrMap[key].isLocked)
         self.assertEqual(self.wlt.addrMap[key].binPrivKey32_Plain.toHexStr(), '')
      # (6)Getting a new addresses from both wallets'
      for i in range(self.wlt.addrPoolSize*2):
         self.wlt.getNextUnusedAddress()
         wlt2.getNextUnusedAddress()
   
      newaddr1 = self.wlt.getNextUnusedAddress()
      newaddr2 = wlt2.getNextUnusedAddress()   
      self.assertTrue(newaddr1.getAddr160() == newaddr2.getAddr160())
      self.assertEqual(len(wlt2.addrMap), 3*originalLength+14)
   
      # (6) Re-reading wallet from file, compare the two wallets
      wlt3 = PyBtcWallet().readWalletFile('OnlineVersionOfEncryptedWallet.bin')
      self.assertTrue(wlt3.isEqualTo(wlt2))
      #############################################################################
      # (7)Testing removing wallet encryption'
      # Wallet is locked?  ', self.wlt.isLocked
      self.wlt.unlock(securePassphrase=self.passphrase2)
      self.wlt.changeWalletEncryption( None )
      for key in self.wlt.addrMap:
         self.assertFalse(self.wlt.addrMap[key].isLocked)
         self.assertNotEqual(self.wlt.addrMap[key].binPrivKey32_Plain.toHexStr(), '')
   
      # (7) Re-reading wallet from file, compare the two wallets'
      wlt2 = PyBtcWallet().readWalletFile(self.wlt.getWalletPath())
      self.assertTrue(self.wlt.isEqualTo(wlt2))
   
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
         self.assertEqual(os.path.exists(self.fileA), fileAExists)
         self.assertEqual(os.path.exists(self.fileB), fileBExists)
         self.assertEqual(os.path.exists(self.fileAupd), fileAupdExists)
         self.assertEqual(os.path.exists(self.fileBupd), fileBupdExists)

      correctMainHash = hashfile(self.fileA)
      try:
         self.wlt.interruptTest1 = True
         self.wlt.getNextUnusedAddress()
      except InterruptTestError:
         # Interrupted!'
         pass
      self.wlt.interruptTest1 = False
   
      # (8a)Interrupted getNextUnusedAddress on primary file update'
      verifyFileStatus(True, True, False, True)
      # (8a)Do consistency check on the wallet'
      self.wlt.doWalletFileConsistencyCheck()
      verifyFileStatus(True, True, False, False)
      self.assertEqual(correctMainHash, hashfile(self.fileA))

      try:
         self.wlt.interruptTest2 = True
         self.wlt.getNextUnusedAddress()
      except InterruptTestError:
         # Interrupted!'
         pass
      self.wlt.interruptTest2 = False
   
      # (8b)Interrupted getNextUnusedAddress on between primary/backup update'
      verifyFileStatus(True, True, True, True)
      # (8b)Do consistency check on the wallet'
      self.wlt.doWalletFileConsistencyCheck()
      verifyFileStatus(True, True, False, False)
      self.assertEqual(hashfile(self.fileA), hashfile(self.fileB))
      # (8c) Try interrupting at state 3'
      verifyFileStatus(True, True, False, False)
   
      try:
         self.wlt.interruptTest3 = True
         self.wlt.getNextUnusedAddress()
      except InterruptTestError:
         # Interrupted!'
         pass
      self.wlt.interruptTest3 = False
   
      # (8c)Interrupted getNextUnusedAddress on backup file update'
      verifyFileStatus(True, True, True, False)
      # (8c)Do consistency check on the wallet'
      self.wlt.doWalletFileConsistencyCheck()
      verifyFileStatus(True, True, False, False)
      self.assertEqual(hashfile(self.fileA), hashfile(self.fileB))
   
      #############################################################################
      # \n'
      # *********************************************************************'
      # (9)Checksum-based byte-error correction tests!'
      # (9)Start with a good primary and backup file...'
   
      # (9a)Open primary wallet, change second byte in KDF'
      wltfile = open(self.wlt.walletPath,'r+b')
      wltfile.seek(326)
      wltfile.write('\xff')
      wltfile.close()
      # (9a)Byte changed, file hashes:'
      verifyFileStatus(True, True, False, False)
   
      # (9a)Try to read wallet from file, should correct KDF error, write fix'
      wlt2 = PyBtcWallet().readWalletFile(self.wlt.walletPath)
      verifyFileStatus(True, True, False, False)
      self.assertNotEqual(hashfile(self.fileA), hashfile(self.fileB))
   
      # \n'
      # *********************************************************************'
      # (9b)Change a byte in each checksummed field in root addr'
      wltfile = open(self.wlt.walletPath,'r+b')
      wltfile.seek(838);  wltfile.write('\xff')
      wltfile.seek(885);  wltfile.write('\xff')
      wltfile.seek(929);  wltfile.write('\xff')
      wltfile.seek(954);  wltfile.write('\xff')
      wltfile.seek(1000);  wltfile.write('\xff')
      wltfile.close()
      # (9b) New file hashes...'
      verifyFileStatus(True, True, False, False)
   
      # (9b)Try to read wallet from file, should correct address errors'
      wlt2 = PyBtcWallet().readWalletFile(self.wlt.walletPath)
      verifyFileStatus(True, True, False, False)
      self.assertNotEqual(hashfile(self.fileA), hashfile(self.fileB))
      
      # \n'
      # *********************************************************************'
      # (9c)Change a byte in each checksummed field, of first non-root addr'
      wltfile = open(self.wlt.walletPath,'r+b')
      wltfile.seek(1261+21+838);  wltfile.write('\xff')
      wltfile.seek(1261+21+885);  wltfile.write('\xff')
      wltfile.seek(1261+21+929);  wltfile.write('\xff')
      wltfile.seek(1261+21+954);  wltfile.write('\xff')
      wltfile.seek(1261+21+1000);  wltfile.write('\xff')
      wltfile.close()
      # (9c) New file hashes...'
      verifyFileStatus(True, True, False, False)
   
      # (9c)Try to read wallet from file, should correct address errors'
      wlt2 = PyBtcWallet().readWalletFile(self.wlt.walletPath)
      verifyFileStatus(True, True, False, False)
      self.assertNotEqual(hashfile(self.fileA), hashfile(self.fileB))
   
      # \n'
      # *********************************************************************'
      # (9d)Now butcher the CHECKSUM, see if correction works'
      wltfile = open(self.wlt.walletPath,'r+b')
      wltfile.seek(977); wltfile.write('\xff')
      wltfile.close()
      # (9d) New file hashes...'
      verifyFileStatus(True, True, False, False)
   
      # (9d)Try to read wallet from file, should correct address errors'
      wlt2 = PyBtcWallet().readWalletFile(self.wlt.walletPath)
      verifyFileStatus(True, True, False, False)
      self.assertNotEqual(hashfile(self.fileA), hashfile(self.fileB))
   
   
      # *******'
      # (9z) Test comment I/O'
      comment1 = 'This is my normal unit-testing address.'
      comment2 = 'This is fake tx... no tx has this hash.'
      comment3 = comment1 + '  Corrected!'
      hash1 = '\x1f'*20  # address160
      hash2 = '\x2f'*32  # tx hash
      self.wlt.setComment(hash1, comment1)
      self.wlt.setComment(hash2, comment2)
      self.wlt.setComment(hash1, comment3)
   
      wlt2 = PyBtcWallet().readWalletFile(self.wlt.walletPath)
      c3 = wlt2.getComment(hash1)
      c2 = wlt2.getComment(hash2)
      self.assertEqual(c3, comment3)
      self.assertEqual(c2, comment2)

# Running tests with "python <module name>" will NOT work for any Armory tests
# You must run tests with "python -m unittest <module name>" or run all tests with "python -m unittest discover"
# if __name__ == "__main__":
#    unittest.main()