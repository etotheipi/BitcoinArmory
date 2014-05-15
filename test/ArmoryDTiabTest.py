'''
Created on Oct 8, 2013

@author: Andy
'''
import os
import unittest
from test.Tiab import TiabTest
from armoryengine.ArmoryUtils import binary_to_hex
from armoryd import AmountToJSON, Armory_Json_Rpc_Server
from armoryengine.BDM import TheBDM
from armoryengine.PyBtcWallet import PyBtcWallet

TEST_WALLET_NAME = 'Test Wallet Name'
TEST_WALLET_DESCRIPTION = 'Test Wallet Description'
TEST_WALLET_ID = 'GDHFnMQ2'

TX_ID1_OUTPUT0_VALUE = 63000
TX_ID1_OUTPUT1_VALUE = 139367000

PASSPHRASE1 = 'abcde'
UNLOCK_TIMEOUT = 5
TIAB_DIR = '.\\tiab'
TEST_TIAB_DIR = '.\\test\\tiab'
NEED_TIAB_MSG = "This Test must be run with J:/Development_Stuff/bitcoin-testnet-boxV2.7z (Armory jungle disk). Copy to the test directory."

EXPECTED_TIAB_BALANCE = 938.8997
EXPECTED_TIAB_NEXT_ADDR = 'muEePRR9ShvRm2nqeiJyD8pJRHPuww2ECG'
EXPECTED_UNSPENT_TX = '721507bc7c4cdbd7cf798d362272b2e5941e619f2f300f46ac956933cb42181100000000'
     
class ArmoryDTiabTest(TiabTest):
   
   def setUp(self):
      self.verifyBlockHeight()
      # Load the primary file from the test net in a box
      self.fileA    = os.path.join(self.tiab.tiabDirectory, 'armory\\armory_%s_.wallet' % TEST_WALLET_ID)
      self.wallet = PyBtcWallet().readWalletFile(self.fileA, doScanNow=True)
      self.jsonServer = Armory_Json_Rpc_Server(self.wallet)
      TheBDM.registerWallet(self.wallet)

   def testListunspent(self):
      actualResult = self.jsonServer.jsonrpc_listunspent()
      self.assertEqual(len(actualResult), 1)
      self.assertEqual(binary_to_hex(actualResult[0]), EXPECTED_UNSPENT_TX)
      
   
   def testGetNewAddress(self):
      actualResult = self.jsonServer.jsonrpc_getnewaddress()
      self.assertEqual(actualResult, EXPECTED_TIAB_NEXT_ADDR)
      
   def testGetBalance(self):
      ballances = {'spendable' : EXPECTED_TIAB_BALANCE, \
                   'spend' : EXPECTED_TIAB_BALANCE, \
                   'unconf' : 0, \
                   'unconfirmed' :  0, \
                   'total' : EXPECTED_TIAB_BALANCE, \
                   'ultimate'  :  EXPECTED_TIAB_BALANCE, \
                   'unspent' :  EXPECTED_TIAB_BALANCE, \
                   'full' :  EXPECTED_TIAB_BALANCE}
      for ballanceType in ballances.keys():
         result = self.jsonServer.jsonrpc_getbalance(ballanceType)
         print ballanceType, result
         self.assertEqual(result,
                          AmountToJSON(self.wallet.getBalance(ballanceType)))
      self.assertEqual(self.jsonServer.jsonrpc_getbalance('bogus'), -1)

