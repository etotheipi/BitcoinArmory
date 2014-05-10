'''
Created on Oct 8, 2013

@author: Andy
'''
import os
import sys
import time
import unittest
from test import Tiab

sys.argv.append('--nologging')
sys.argv.append('--testnet')
from CppBlockUtils import SecureBinaryData, CryptoECDSA
from armoryd import Armory_Json_Rpc_Server, PrivateKeyNotFound, \
   InvalidBitcoinAddress, WalletUnlockNeeded, Armory_Daemon, AmountToJSON
from armoryengine.ArmoryUtils import ARMORY_HOME_DIR, hex_to_binary, \
   binary_to_base58, binary_to_hex, convertKeyDataToAddress, hash160_to_addrStr,\
   hex_switchEndian, hash160, BIGENDIAN
from armoryengine.BDM import TheBDM
from armoryengine.PyBtcWallet import PyBtcWallet
from armoryengine.Transaction import PyTx


TEST_WALLET_NAME = 'Test Wallet Name'
TEST_WALLET_DESCRIPTION = 'Test Wallet Description'
TEST_WALLET_ID = 'PMjjFm6E'

TX_ID1_OUTPUT0_VALUE = 63000
TX_ID1_OUTPUT1_VALUE = 139367000

PASSPHRASE1 = 'abcde'
UNLOCK_TIMEOUT = 5
TIAB_DIR = '.\\tiab'
TEST_TIAB_DIR = '.\\test\\tiab'
NEED_TIAB_MSG = "This Test must be run with J:/Development_Stuff/bitcoin-testnet-boxV2.7z (Armory jungle disk). Copy to the test directory."

class ArmoryDTiabTest(unittest.TestCase):      
   def removeFileList(self, fileList):
      for f in fileList:
         if os.path.exists(f):
            os.remove(f)
            
   @classmethod
   def setUpClass(self):
      currentPath = os.path.curdir
      # Handle both calling the this test from the context of the test directory
      # and calling this test from the context of the main directory. 
      # The latter happens if you run all of the tests in the directory
      if os.path.exists(TIAB_DIR):
         tiabDataDir = TIAB_DIR
      elif os.path.exists(TEST_TIAB_DIR):
         tiabDataDir = TEST_TIAB_DIR
      else:
         self.fail(NEED_TIAB_MSG)
      self.tiab = Tiab.TiabSession(tiabdatadir='.\\tiab')
      if TheBDM.getBDMState()=='BlockchainReady':
         TheBDM.Reset(wait=True)
      TheBDM.setSatoshiDir(self.tiab.directory + '\\1\\testnet3')
      TheBDM.setLevelDBDir(self.tiab.directory + '\\armory\\databases')
      TheBDM.setBlocking(True)
      TheBDM.setOnlineMode(True)
      while not TheBDM.getBDMState()=='BlockchainReady':
         time.sleep(2)

   @classmethod
   def tearDownClass(self):
      self.tiab.clean()


   def setUp(self):
      self.assertEqual(TheBDM.getTopBlockHeight(), 56109, NEED_TIAB_MSG)
      # Load the primary file from the test net in a box
      self.fileA    = os.path.join(self.tiab.directory, 'armory\\armory_%s_.wallet' % TEST_WALLET_ID)
      self.wallet = PyBtcWallet().readWalletFile(self.fileA, doScanNow=True)
      self.jsonServer = Armory_Json_Rpc_Server(self.wallet)
      TheBDM.registerWallet(self.wallet)
      
   
   def testListunspent(self):
      actualResult = self.jsonServer.jsonrpc_listunspent()
      self.assertEqual(len(actualResult), 1)
      self.assertEqual(binary_to_hex(actualResult[0]), 'b547cc4ec882fb7bf79d7409310c9f4f439cd8f9d5d1f86fbda987f3f41536d201000000')
      
   
   def testGetNewAddress(self):
      actualResult = self.jsonServer.jsonrpc_getnewaddress()
      self.assertEqual(actualResult, 'mwEDzkBBtafcPZQasVBJYVaf6w2vEfaDdw')
      
   
   # This should return the followin balances for the test wallet
   # spendable  -  2499.9998
   # spend  -  2499.9998
   # unconf  -  0.0
   # unconfirmed  -  0.0
   # total  -  2499.9998
   # ultimate  -  2499.9998
   # unspent  -  2499.9998
   # full  -  2499.9998
   def testGetBalance(self):
      ballances = {'spendable' : 2499.9998, \
                   'spend' : 2499.9998, \
                   'unconf' : 0, \
                   'unconfirmed' :  0, \
                   'total' : 2499.9998, \
                   'ultimate'  :  2499.9998, \
                   'unspent' :  2499.9998, \
                   'full' :  2499.9998}
      for ballanceType in ballances.keys():
         result = self.jsonServer.jsonrpc_getbalance(ballanceType)
         print ballanceType, ' - ', result
         self.assertEqual(result,
                          AmountToJSON(self.wallet.getBalance(ballanceType)))
      self.assertEqual(self.jsonServer.jsonrpc_getbalance('bogus'), -1)

      
if __name__ == "__main__":
   #import sys;sys.argv = ['', 'Test.testName']
   unittest.main()
