'''
Created on Oct 8, 2013

@author: Andy
'''
import sys
sys.path.append('..')
import os
import time
from pytest.Tiab import TiabTest
from CppBlockUtils import SecureBinaryData, CryptoECDSA
from armoryd import Armory_Json_Rpc_Server, PrivateKeyNotFound, \
   InvalidBitcoinAddress, WalletUnlockNeeded, Armory_Daemon, AmountToJSON
from armoryengine.ArmoryUtils import hex_to_binary, \
   binary_to_base58, binary_to_hex, convertKeyDataToAddress, hash160_to_addrStr,\
   hex_switchEndian, hash160, BIGENDIAN
from armoryengine.BDM import TheBDM
from armoryengine.PyBtcWallet import PyBtcWallet
from armoryengine.Transaction import PyTx
import unittest


TEST_WALLET_NAME = 'Test Wallet Name'
TEST_WALLET_DESCRIPTION = 'Test Wallet Description'
TEST_WALLET_ID = '3VB8XSoY'

RAW_TX1    = '0100000001b5dbdcea08ae1ff5a547755aaab7f468a6091a573ae76c6fa5a3fcf5ec65b804010000008b4830450220081341a4e803c7c8e64c3a3fd285dca34c9f7c71c4dfc2b576d761c5783ce735022100eea66ba382d00e628d86fc5bc1928a93765e26fd8252c4d01efe22147c12b91a01410458fec9d580b0c6842cae00aecd96e89af3ff56f5be49dae425046e64057e0f499acc35ec10e1b544e0f01072296c6fa60a68ea515e59d24ff794cf8923cd30f4ffffffff0200943577000000001976a91462d978319c7d7ac6cceed722c3d08aa81b37101288acf02c41d1160000001976a91409097379782fadfbd72e5a818219cf2eb56249d288ac00000000'
TX_ID1      = 'db0ee46beff3a61f38bfc563f92c11449ed57c3d7d5cd5aafbe0114e5a9ceee4'

TX_ID1_OUTPUT0_VALUE = 20.0
TX_ID1_OUTPUT1_VALUE = 979.9999

PASSPHRASE1 = 'abcde'
UNLOCK_TIMEOUT = 5

# These tests could be run in or out of the TiaB
class ArmoryDTest(TiabTest):      
   def removeFileList(self, fileList):
      for f in fileList:
         if os.path.exists(f):
            os.remove(f)

   def setUp(self):
      self.verifyBlockHeight()
      self.fileA    = os.path.join(self.armoryHomeDir, 'armory_%s_.wallet' % TEST_WALLET_ID)
      self.fileB    = os.path.join(self.armoryHomeDir, 'armory_%s_backup.wallet' % TEST_WALLET_ID)
      self.fileAupd = os.path.join(self.armoryHomeDir, 'armory_%s_backup_unsuccessful.wallet' % TEST_WALLET_ID)
      self.fileBupd = os.path.join(self.armoryHomeDir, 'armory_%s_update_unsuccessful.wallet' % TEST_WALLET_ID)

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
                                          shortLabel=TEST_WALLET_NAME, \
                                          longLabel=TEST_WALLET_DESCRIPTION,
                                          armoryHomeDir = self.armoryHomeDir)
      self.jsonServer = Armory_Json_Rpc_Server(self.wallet)
      TheBDM.registerWallet(self.wallet)
      
   def tearDown(self):
      self.removeFileList([self.fileA, self.fileB, self.fileAupd, self.fileBupd])
   

   # Can't test with actual transactions in this environment. See ARMORY-34.
   # This wallet has no txs
   # def testListunspent(self):
   #    actualResult = self.jsonServer.jsonrpc_listunspent()
   #    self.assertEqual(actualResult, [])

   def testImportprivkey(self):
      originalLength = len(self.wallet.linearAddr160List)
      self.jsonServer.jsonrpc_importprivkey(binary_to_hex(self.privKey2.toBinStr()))
      self.assertEqual(len(self.wallet.linearAddr160List), originalLength+1)

   def testGettxout(self):
      txOut = self.jsonServer.jsonrpc_gettxout(TX_ID1, 0)
      self.assertEquals(txOut['value'],TX_ID1_OUTPUT0_VALUE)
      txOut = self.jsonServer.jsonrpc_gettxout(TX_ID1, 1)
      self.assertEquals(txOut['value'],TX_ID1_OUTPUT1_VALUE)
         
   # Cannot unit test actual balances. Only verify that getreceivedbyaddress return a 0 result.
   def testGetreceivedbyaddress(self):
      a160 = hash160(self.wallet.getNextUnusedAddress().binPublicKey65.toBinStr())
      testAddr = hash160_to_addrStr(a160)
      result = self.jsonServer.jsonrpc_getreceivedbyaddress(testAddr)
      self.assertEqual(result, 0)
      
   def testGetrawtransaction(self):
      actualRawTx = self.jsonServer.jsonrpc_getrawtransaction(TX_ID1)
      pyTx = PyTx().unserialize(hex_to_binary(actualRawTx))
      self.assertEquals(TX_ID1, binary_to_hex(pyTx.getHash(), BIGENDIAN))

   def testBackupWallet(self):
      backupTestPath = os.path.join(self.armoryHomeDir, 'armory_%s_.wallet.backup.test' % TEST_WALLET_ID)
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
      expectScriptStr = 'OP_DUP OP_HASH160 PUSHDATA(20) [62d978319c7d7ac6cceed722c3d08aa81b371012] OP_EQUALVERIFY OP_CHECKSIG'
      self.assertEqual(actualDD['locktime'], 0)
      self.assertEqual(actualDD['version'], 1)
      self.assertEqual(len(actualDD['vin']), 1)
      self.assertEqual(actualDD['vin'][0]['sequence'], 4294967295L)
      self.assertEqual(actualDD['vin'][0]['scriptSig']['hex'], '4830450220081341a4e803c7c8e64c3a3fd285dca34c9f7c71c4dfc2b576d761c5783ce735022100eea66ba382d00e628d86fc5bc1928a93765e26fd8252c4d01efe22147c12b91a01410458fec9d580b0c6842cae00aecd96e89af3ff56f5be49dae425046e64057e0f499acc35ec10e1b544e0f01072296c6fa60a68ea515e59d24ff794cf8923cd30f4')
      self.assertEqual(actualDD['vin'][0]['vout'], 1)
      self.assertEqual(actualDD['vin'][0]['txid'], '04b865ecf5fca3a56f6ce73a571a09a668f4b7aa5a7547a5f51fae08eadcdbb5')
      self.assertEqual(len(actualDD['vout']), 2)
      self.assertEqual(actualDD['vout'][0]['value'], 20.0)
      self.assertEqual(actualDD['vout'][0]['n'], 0)
      self.assertEqual(actualDD['vout'][0]['scriptAddrStrs']['reqSigs'], 1)
      self.assertEqual(actualDD['vout'][0]['scriptAddrStrs']['hex'], '76a91462d978319c7d7ac6cceed722c3d08aa81b37101288ac')
      self.assertEqual(actualDD['vout'][0]['scriptAddrStrs']['addresses'], ['mpXd2u8fPVYdL1Nf9bZ4EFnqhkNyghGLxL'])
      self.assertEqual(actualDD['vout'][0]['scriptAddrStrs']['asm'], expectScriptStr)
      self.assertEqual(actualDD['vout'][0]['scriptAddrStrs']['type'], 'Standard (PKH)')
      self.assertEqual(actualDD['vout'][1]['scriptAddrStrs']['type'], 'Standard (PKH)')


   def testDumpprivkey(self):

      testPrivKey = self.privKey.toBinStr()
      hash160 = convertKeyDataToAddress(testPrivKey)
      addr58 = hash160_to_addrStr(hash160)
      
      # Verify that a bogus addrss Raises InvalidBitcoinAddress Exception
      result =  self.jsonServer.jsonrpc_dumpprivkey('bogus')
      self.assertEqual(result['Error Type'],'InvalidBitcoinAddress')
      
      result =  self.jsonServer.jsonrpc_dumpprivkey(addr58)
      self.assertEqual(result['Error Type'],'PrivateKeyNotFound')
      
      # verify that the first private key can be found
      firstHash160 = self.wallet.getNextUnusedAddress().getAddr160()
      firstAddr58 = hash160_to_addrStr(firstHash160)
      actualPrivateKey = self.jsonServer.jsonrpc_dumpprivkey(firstAddr58)
      expectedPrivateKey = binary_to_hex(self.wallet.getAddrByHash160(firstHash160).serializePlainPrivateKey())
      
      self.assertEqual(actualPrivateKey, expectedPrivateKey)
      
      # Verify that a locked wallet Raises WalletUnlockNeeded Exception
      kdfParams = self.wallet.computeSystemSpecificKdfParams(0.1)
      self.wallet.changeKdfParams(*kdfParams)
      self.wallet.changeWalletEncryption( securePassphrase=self.passphrase )
      self.wallet.lock()
      result = self.jsonServer.jsonrpc_dumpprivkey(addr58)
      self.assertEqual(result['Error Type'],'WalletUnlockNeeded')
      
   def testEncryptwallet(self):
      kdfParams = self.wallet.computeSystemSpecificKdfParams(0.1)
      self.wallet.changeKdfParams(*kdfParams)
      self.jsonServer.jsonrpc_encryptwallet(PASSPHRASE1)
      self.assertTrue(self.wallet.isLocked)
      
      # Verify that a locked wallet Raises WalletUnlockNeeded Exception
      # self.assertRaises(WalletUnlockNeeded, self.jsonServer.jsonrpc_encryptwallet, PASSPHRASE1)
      result = self.jsonServer.jsonrpc_encryptwallet(PASSPHRASE1)
      print result
      
   def testUnlockwallet(self):
      kdfParams = self.wallet.computeSystemSpecificKdfParams(0.1)
      self.wallet.changeKdfParams(*kdfParams)
      self.jsonServer.jsonrpc_encryptwallet(PASSPHRASE1)
      self.assertTrue(self.wallet.isLocked)
      self.jsonServer.jsonrpc_unlockwallet(PASSPHRASE1, UNLOCK_TIMEOUT)
      self.assertFalse(self.wallet.isLocked)
      time.sleep(UNLOCK_TIMEOUT+1)
      self.wallet.checkWalletLockTimeout()
      self.assertTrue(self.wallet.isLocked)
      
   def testGetWalletInfo(self):
      wltInfo = self.jsonServer.jsonrpc_getwalletinfo()
      self.assertEqual(wltInfo['name'], TEST_WALLET_NAME)
      self.assertEqual(wltInfo['description'], TEST_WALLET_DESCRIPTION)
      self.assertEqual(wltInfo['balance'], AmountToJSON(self.wallet.getBalance('Spend')))
      self.assertEqual(wltInfo['keypoolsize'], self.wallet.addrPoolSize)
      self.assertEqual(wltInfo['numaddrgen'], len(self.wallet.addrMap))
      self.assertEqual(wltInfo['highestusedindex'], self.wallet.highestUsedChainIndex)
   
   # This should always return 0 balance
   # Need to create our own test net to test with balances
   def testGetBalance(self):
      for ballanceType in ['spendable','spend', 'unconf', \
                           'unconfirmed', 'total', 'ultimate','unspent', 'full']:
         self.assertEqual(self.jsonServer.jsonrpc_getbalance(ballanceType),
                          AmountToJSON(self.wallet.getBalance(ballanceType)))
      
      
# Running tests with "python <module name>" will NOT work for any Armory tests
# You must run tests with "python -m unittest <module name>" or run all tests with "python -m unittest discover"
# if __name__ == "__main__":
#    unittest.main()
