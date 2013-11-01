'''
Created on Oct 8, 2013

@author: Andy
'''
import sys
import time
sys.argv.append('--nologging')
sys.argv.append('--testnet')
import unittest
import os
from armoryengine import ARMORY_HOME_DIR, PyBtcWallet, TheBDM, PyTx
from CppBlockUtils import SecureBinaryData, CryptoECDSA
from utilities.ArmoryUtils import hex_to_binary, binary_to_base58,\
   convertKeyDataToAddress, hash160_to_addrStr, binary_to_hex
from armoryd import Armory_Json_Rpc_Server, PrivateKeyNotFound,\
   InvalidBitcoinAddress, WalletUnlockNeeded, Armory_Daemon

RAW_TX1     = '01000000081fa335f8aa332693c7bf77c960ac1eb86c50a5f60d8dc6892d4'+\
              '3f89473dc50e4b104000000ffffffff4be787d4a6009ba04534c9b42af46e'+\
              '5442744804e6050ad08e58804ef8f067882601000000ffffffffa20b1cdd9'+\
              '232e335f6200f7d2623d2789a0847dc53faa79387ffab38271307be650400'+\
              '0000ffffffff3a7771644a35dbe67e071f7d3ec8e097ec23817311c0a0d0e'+\
              'a6a03d6c3a62f1b7000000000ffffffff445d69280e25c34db1159deef391'+\
              '10fb47e7d3091972e4366e3991d52ac38edfec00000000ffffffffc258ede'+\
              'c7fc46646ab2d4c682abf3757dabdee91b7635aa0e62f0d620cdb97830204'+\
              '000000ffffffff38b93d88c22b56e58489dba7bbf439bb5044e5f76e00969'+\
              'd591e805636601c886600000000ffffffffdada1b7c73ce39cffb8245f343'+\
              '91c0f0d54f32cb3f05570b1c37635c44179df72700000000ffffffff03f04'+\
              'b0000000000001976a914be17ec0fc1f8aa029223dbe5f53109d0faf8c797'+\
              '88ac10270000000000001976a91443134735b72a1e9cf5e4c56d910295313'+\
              '2352ba688ac00000000000000000000000000000000000000000000000000'+\
              '00000000000000ffffffff3a4c3754686973206973206120636f6d6d656e7'+\
              '420617474616368656420746f2061207472616e73616374696f6e206f6e20'+\
              '6d61696e6e65742e7500000000'
              
RAW_TX2     = '00006c493046022100d43c4e239fc8bf31dbf14f9c71301cf985865b11c92'+\
              'f5a0963f2c0382f1aefc4022100b6fdb3b1fb00aa8a62fbec3cda2d353981'+\
              '7adc34bc28f761f929346920278c710121023a9ea0a00446698198523b904'+\
              '97d6e1fe58548eaccc3898a88904c675c311bfcffffffff0200d8ee730100'+\
              '00001976a914ecf3738156325a0e90339ce2f7c1d6ae87cf9b9188ac00ab9'+\
              '041000000001976a914a4a6b6a83aae2744dd10a8d055d9fb75383cd9d488'+\
              'ac00000000'

TX_ID1      = 'e0dc8e3d3654c5bfeb1eb077f835179395ee82d623b0c0d3c7074fc2d4c0706f'

PASSPHRASE1 = 'abcde'
              
class ArmoryDTest(unittest.TestCase):      
   def removeFileList(self, fileList):
      for f in fileList:
         if os.path.exists(f):
            os.remove(f)
            
   @classmethod
   def setUpClass(self):
      # This is not a UI so no need to worry about the main thread being blocked.
      # Any UI that uses this Daemon can put the call to the Daemon on it's own thread.
      TheBDM.setBlocking(True)
      TheBDM.setOnlineMode(True)
      while not TheBDM.getBDMState()=='BlockchainReady':
         time.sleep(2)

   def setUp(self):
      self.shortlabel = 'TestWallet1'
      self.wltID = '3VB8XSoY'

      self.fileA    = os.path.join(ARMORY_HOME_DIR, 'armory_%s_.wallet' % self.wltID)
      self.fileB    = os.path.join(ARMORY_HOME_DIR, 'armory_%s_backup.wallet' % self.wltID)
      self.fileAupd = os.path.join(ARMORY_HOME_DIR, 'armory_%s_backup_unsuccessful.wallet' % self.wltID)
      self.fileBupd = os.path.join(ARMORY_HOME_DIR, 'armory_%s_update_unsuccessful.wallet' % self.wltID)

      self.removeFileList([self.fileA, self.fileB, self.fileAupd, self.fileBupd])
   
      # We need a controlled test, so we script the all the normally-random stuff
      self.privKey   = SecureBinaryData('\xaa'*32)
      self.privKey2  = SecureBinaryData('\x33'*32)
      self.chainstr  = SecureBinaryData('\xee'*32)
      theIV     = SecureBinaryData(hex_to_binary('77'*16))
      self.passphrase  = SecureBinaryData('A self.passphrase')
      self.passphrase2 = SecureBinaryData('A new self.passphrase')
      
      self.wallet = PyBtcWallet().createNewWallet(withEncrypt=False, \
                                          plainRootKey=self.privKey, \
                                          chaincode=self.chainstr,   \
                                          IV=theIV, \
                                          shortLabel=self.shortlabel)
      self.jsonServer = Armory_Json_Rpc_Server(self.wallet)
      TheBDM.registerWallet(self.wallet)
      
   def tearDown(self):
      self.removeFileList([self.fileA, self.fileB, self.fileAupd, self.fileBupd])
      
   def testGetrawtransaction(self):
      actualRawTx = self.jsonServer.jsonrpc_getrawtransaction(hex_to_binary(TX_ID1))
      pyTx = PyTx().unserialize(actualRawTx)
      self.assertEquals(TX_ID1, binary_to_hex(pyTx.getHash()))

   def testBackupWallet(self):
      backupTestPath = os.path.join(ARMORY_HOME_DIR, 'armory_%s_.wallet.backup.test' % self.wltID)
      # Remove backupTestPath in case it exists
      backupFileList = [backupTestPath, self.fileB]
      self.removeFileList(backupFileList)
      # Remove the backup test path that is to be created after tear down.
      self.addCleanup(self.removeFileList, backupFileList)
      self.jsonServer.jsonrpc_backupwallet(backupTestPath)
      self.assertTrue(os.path.exists(backupTestPath))
      self.wallet.backupWalletFile()
      self.assertTrue(os.path.exists(self.fileB))
      
   def testDecoderawtransaction(self):
      actualDD = self.jsonServer.jsonrpc_decoderawtransaction(RAW_TX1)
      # Test specific values pulled from bitcoin daemon's output for the test raw TX
      self.assertEqual(actualDD['locktime'], 0)
      self.assertEqual(actualDD['version'], 1)
      self.assertEqual(actualDD['vin'][0]['sequence'], 4294967295L)
      self.assertEqual(actualDD['vin'][0]['scriptSig']['hex'], '')
      # self.assertEqual(actualDD['vin'][0]['scriptSig']['asm'], '') - NOT IMPLEMENTED
      self.assertEqual(actualDD['vin'][0]['vout'], 1201)
      self.assertEqual(actualDD['vin'][0]['txid'], 'e450dc7394f8432d89c68d0df6a5506cb81eac60c977bfc7932633aaf835a31f')
      self.assertEqual(actualDD['vin'][1]['vout'], 294)
      self.assertEqual(actualDD['vin'][1]['txid'], '8867f0f84e80588ed00a05e604487442546ef42ab4c93445a09b00a6d487e74b')
      self.assertEqual(actualDD['vout'][0]['value'], 0.0001944)
      self.assertEqual(actualDD['vout'][0]['n'], 0)
      # self.assertEqual(actualDD['vout'][0]['scriptPubKey']['reqSigs'], 1) - NOT IMPLEMENTED
      self.assertEqual(actualDD['vout'][0]['scriptPubKey']['hex'], 'ac8897c7f8fad00931f5e5db239202aaf8c10fec17be14a976')
      # self.assertEqual(actualDD['vout'][0]['scriptPubKey']['addresses'], ['mxr5Le3bt7dfbFqmpK6saUYPt5xtcDB7Yw']) - NOT IMPLEMENTED
      # self.assertEqual(actualDD['vout'][0]['scriptPubKey']['asm'], 'OP_DUP OP_HASH160 be17ec0fc1f8aa029223dbe5f53109d0faf8c797 OP_EQUALVERIFY OP_CHECKSIG') - NOT IMPLEMENTED
      self.assertEqual(actualDD['vout'][0]['scriptPubKey']['type'], 'pubkeyhash')
      self.assertEqual(actualDD['vout'][1]['scriptPubKey']['type'], 'pubkeyhash')
      self.assertEqual(actualDD['vout'][2]['scriptPubKey']['type'], 'nonstandard')
      
      
   def testDumpprivkey(self):

      testPrivKey = self.privKey.toBinStr()
      hash160 = convertKeyDataToAddress(testPrivKey)
      addr58 = hash160_to_addrStr(hash160)
      
      # Verify that a bogus addrss Raises InvalidBitcoinAddress Exception
      self.assertRaises(InvalidBitcoinAddress, self.jsonServer.jsonrpc_dumpprivkey, 'bogus')
      
      # verify that the root private key is not found
      self.assertRaises(PrivateKeyNotFound, self.jsonServer.jsonrpc_dumpprivkey, addr58)
      
      # verify that the first private key can be found
      firstHash160 = self.wallet.getNextUnusedAddress().getAddr160()
      firstAddr58 = hash160_to_addrStr(firstHash160)
      actualPrivateKey = self.jsonServer.jsonrpc_dumpprivkey(firstAddr58)
      expectedPrivateKey = self.wallet.getAddrByHash160(firstHash160).serializePlainPrivateKey()
      self.assertEqual(actualPrivateKey, expectedPrivateKey)
      
      # Verify that a locked wallet Raises WalletUnlockNeeded Exception
      kdfParams = self.wallet.computeSystemSpecificKdfParams(0.1)
      self.wallet.changeKdfParams(*kdfParams)
      self.wallet.changeWalletEncryption( securePassphrase=self.passphrase )
      self.wallet.lock()
      self.assertRaises(WalletUnlockNeeded, self.jsonServer.jsonrpc_dumpprivkey, addr58)

   def testEncryptwallet(self):
      kdfParams = self.wallet.computeSystemSpecificKdfParams(0.1)
      self.wallet.changeKdfParams(*kdfParams)
      self.jsonServer.jsonrpc_encryptwallet(PASSPHRASE1)
      self.assertTrue(self.wallet.isLocked)
      
      # Verify that a locked wallet Raises WalletUnlockNeeded Exception
      self.assertRaises(WalletUnlockNeeded, self.jsonServer.jsonrpc_encryptwallet, PASSPHRASE1)
      

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()