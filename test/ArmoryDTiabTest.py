'''
Created on Oct 8, 2013

@author: Andy
'''
import os
import unittest
from test.Tiab import TiabTest
from armoryengine.ArmoryUtils import *
from armoryd import AmountToJSON, Armory_Json_Rpc_Server, JSONtoAmount
from armoryengine.BDM import TheBDM
from armoryengine.PyBtcWallet import PyBtcWallet
from armoryengine.Transaction import UnsignedTransaction

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

EXPECTED_TIAB_BALANCE = 964.8997
EXPECTED_TIAB_NEXT_ADDR = 'muEePRR9ShvRm2nqeiJyD8pJRHPuww2ECG'
EXPECTED_UNSPENT_TX = '4434b3eab23189af20d56a81a7bc5ac560f42f4097a90f834535cb94a8d5578201000000'

TIAB_WLT_1_ADDR_1 = 'muxkzd4sitPbMz4BXmkEJKT6ccshxDFsrn'
TIAB_WLT_1_PK_1 = '92vsXfvjpbTj1sN75VSV2M7DWyqoVx5nayp3dE7ZaG9rRVRYU4P'

TIAB_WLT_1_ADDR_2 = 'mtZ2d1jFZ9YNp3Ku5Fb2u8Tfu3RgimBHAD'
TIAB_WLT_1_PK_2 = '934MLhycJEAWL4kMbFt6JRSkNcgEtQXN3ha6Wh8WZyD85cZZZ4N'

TIAB_WLT_1_ADDR_3 = 'mhrpYhQLgYgAvYs1A4E8Z4Dv4ZoZPyLbLS'
TIAB_WLT_1_PK_3 = '91rTQa47dLQhNGDenejW9qxcMTL73GRG347zKfa3qVvzun7ZcNe'

# Has 938.8997 BTC
TIAB_WLT_1_ADDR_8 = 'mikxgMUqkk6Tts1D39Hhx6wKEeQbBH3ons'
TIAB_WLT_1_PK_8 = '92fXG1foeHfn8DYEwTXggCPrFEEY6KpokqoJkp9EhpJw5boc3GY'

TIAB_WLT_2_ADDR_1 = 'mzkKrXNPU6nfBpZCKLmwueb9MvSFaKPDMD'
TIAB_WLT_2_PK_1 = '91jZJ2BnJbk4B6zpqzJqVfbtaq4RMaPPvP7USr9rtWXusSAYrq7'

TIAB_WLT_2_ADDR_2 = 'n2DLXxVZSNBfzXsAm4HewpsfAGBpgTW6DH'
TIAB_WLT_2_PK_2 = '93LLsm4n19Dwbp6zbnmuvHmMjEJFR23h4xstnDnEBYMWSkXaFMT'

TIAB_WLT_2_ADDR_3 = 'mhbmvVedo4i67maX6pfw9trcBWQQ3yXgkB'
TIAB_WLT_2_PK_3 = '92aUXStPSfHDXydGh9MsBnnyacNzJwgWBC4G8W5BiTFkTJpeHEH'

# Has 28.9 BTC
TIAB_WLT_2_ADDR_4 = 'mk7pAQ7YdmnwWaGFCgwiKiEbaGjyEsSVUE'
TIAB_WLT_2_PK_4 = '92gYPs8i6qvSmc8moBAaWLB7M16kX5MBpbGoUygUmQTdrxkNnwR'

TIAB_WLT_3_ADDR_1 = 'mnHywMYRuMyYeamyGhUPJLFSsoWbNAnsNz'
TIAB_WLT_3_PK_1 = '9295sDHkX1xDMzSxit3Bvi8GdLUQq1JFktBQFB8Ca45aLaw8neN'

TIAB_WLT_3_ADDR_2 = 'mpXd2u8fPVYdL1Nf9bZ4EFnqhkNyghGLxL'
TIAB_WLT_3_PK_2 = '92Mic29J44mKLn4qKXm31mMv45BtEnywBnJh36jn1Rk2RT9PTsK'

TIAB_WLT_3_ADDR_3 = 'mmfN9oj2wtMTCACKJz7fUcDeAczz4kucvV'
TIAB_WLT_3_PK_3 = '92ymyLuiEUJJz5madzhPtBTa3of46vLXDSuFPNMAA6DMLSeKA8S'

# has 18.90 BTC
TIAB_WLT_3_ADDR_3 = 'msw6eseNASK8tGVdnQAPURFbHZaayt1pck'
TIAB_WLT_3_PK_3 = '93CiEp gZeLrD qVqEX4 p4xkpi KJf3Ty 6Br9VR Dh9cF4 VgYAHj DY6'

BTC_TO_SEND = 1

# These tests need to be run in the TiaB
class ArmoryDTiabTest(TiabTest):
   
   def setUp(self):
      self.verifyBlockHeight()
      # Load the primary file from the test net in a box
      self.fileA    = os.path.join(self.tiab.tiabDirectory, 'tiab\\armory\\armory_%s_.wallet' % TEST_WALLET_ID)
      self.wlt = PyBtcWallet().readWalletFile(self.fileA, doScanNow=True)
      self.jsonServer = Armory_Json_Rpc_Server(self.wlt)
      TheBDM.registerWallet(self.wlt)
   
   def  testReceivedfromaddress(self):
      result = self.jsonServer.jsonrpc_receivedfromaddress(TIAB_WLT_3_ADDR_3)
      self.assertEqual(result, 6)
      result = self.jsonServer.jsonrpc_receivedfromaddress(TIAB_WLT_1_ADDR_3)
      self.assertEqual(result, 0)
   
   def testGettransaction(self):
      tx = self.jsonServer.jsonrpc_gettransaction('db0ee46beff3a61f38bfc563f92c11449ed57c3d7d5cd5aafbe0114e5a9ceee4')
      self.assertEqual(tx, {'category': 'send', 'inputs': [{'fromtxid': '04b865ecf5fca3a56f6ce73a571a09a668f4b7aa5a7547a5f51fae08eadcdbb5',
                            'ismine': True, 'fromtxindex': 1, 'value': 1000.0, 'address': 'mtZ2d1jFZ9YNp3Ku5Fb2u8Tfu3RgimBHAD'}],
                            'direction': 'send', 'fee': 0.0001, 'totalinputs': 1000.0, 'outputs':
                             [{'address': 'mpXd2u8fPVYdL1Nf9bZ4EFnqhkNyghGLxL', 'value': 20.0, 'ismine': False},
                              {'address': 'mgLjhTCUtbeLPP9fDkBnG8oztWgJaXZQjn', 'value': 979.9999, 'ismine': True}],
                            'txid': 'db0ee46beff3a61f38bfc563f92c11449ed57c3d7d5cd5aafbe0114e5a9ceee4', 'confirmations': 10,
                            'orderinblock': 1, 'mainbranch': True, 'numtxin': 1, 'time': 3947917907L, 'numtxout': 2,
                            'netdiff': -20.0001, 'infomissing': False})
   
   def testGetblock(self):
      block = self.jsonServer.jsonrpc_getblock('0000000064a1ad1f15981a713a6ef08fd98f69854c781dc7b8789cc5f678e01f')
      # This method is broken in a couple ways.
      # For no just verify that raw transaction is correct
      self.assertEqual(block['rawheader'], '02000000d8778a50d43d3e02c4c20bdd0ed97077a3c4bef3e86ce58975f6f43a00000000d25912cfc67228748494d421512c7a6cc31668fa82b72265261558802a89f4c2e0350153ffff001d10bcc285',)
      
   def testGetinfo(self):
      info = self.jsonServer.jsonrpc_getinfo()
      self.assertEqual(info, {'blocks': 247, 'bdmstate': 'BlockchainReady', 'walletversion': 13500000,
                    'difficulty': 1.0, 'proxy': '', 'connections': 0, 'testnet': True, 'version': 9199002,
                    'protocolversion': 0, 'balance': EXPECTED_TIAB_BALANCE, 'keypoolsize': 10})
   
   def testListtransactions(self):
      txList = self.jsonServer.jsonrpc_listtransactions(100)
      self.assertTrue(len(txList)>10)
      self.assertEqual(txList[0], {'blockhash': '0000000064a1ad1f15981a713a6ef08fd98f69854c781dc7b8789cc5f678e01f',
                  'blockindex': 1, 'confirmations': 31, 'address': 'mtZ2d1jFZ9YNp3Ku5Fb2u8Tfu3RgimBHAD',
                  'category': 'receive', 'account': '',
                  'txid': '04b865ecf5fca3a56f6ce73a571a09a668f4b7aa5a7547a5f51fae08eadcdbb5',
                  'blocktime': 1392588256, 'amount': 1000.0, 'timereceived': 1392588256, 'time': 1392588256})
            
      
   def testGetledgersimple(self):
      ledger = self.jsonServer.jsonrpc_getledgersimple()
      self.assertTrue(len(ledger)>4)
      amountList = [row['amount'] for row in ledger]
      expectedAmountList = [1000.0, 20.0, 30.0, 0.8, 10.0]
      self.assertEqual(amountList[:5], expectedAmountList)
      
      
   def testGetledger(self):
      ledger = self.jsonServer.jsonrpc_getledger()
      self.assertTrue(len(ledger)>6)
      amountList = [row['amount'] for row in ledger]
      expectedAmountList = [1000.0, 20.0, 30.0, 0.8, 10.0, 6.0, 20.0]
      self.assertEqual(amountList, expectedAmountList)
      self.assertEqual(ledger[0]['direction'], 'receive')
      self.assertEqual(len(ledger[0]['recipme']), 1)
      self.assertEqual(ledger[0]['recipme'][0]['amount'], 1000.0)
      self.assertEqual(len(ledger[0]['recipother']), 1)
      self.assertEqual(ledger[0]['recipother'][0]['amount'], 49.997)
      self.assertEqual(len(ledger[0]['senderme']), 0)
      self.assertEqual(len(ledger[0]['senderother']), 21)
 
      self.assertEqual(ledger[1]['direction'], 'send')
      self.assertEqual(len(ledger[1]['senderother']), 0)
      self.assertEqual(len(ledger[1]['senderme']), 1)
      self.assertEqual(ledger[1]['senderme'][0]['amount'], 1000.0)
      
   def testSendtoaddress(self):
      # Send 1 BTC 
      serializedUnsignedTx = self.jsonServer.jsonrpc_sendtoaddress(TIAB_WLT_3_ADDR_3, BTC_TO_SEND)
      unsignedTx = UnsignedTransaction().unserializeAscii(serializedUnsignedTx)
      # Should have 2 txouts to TIAB_WLT_3_ADDR_3 and the change
      self.assertEqual(len(unsignedTx.decorTxOuts), 2)
      foundTxOut = False
      for txout in unsignedTx.decorTxOuts:
         if script_to_addrStr(txout.binScript) == TIAB_WLT_3_ADDR_3:
            self.assertEqual(txout.value, JSONtoAmount(BTC_TO_SEND))
            foundTxOut = True
      self.assertTrue(foundTxOut)

   def testSendmany(self):
      # Send 1 BTC 
      serializedUnsignedTx = self.jsonServer.jsonrpc_sendmany(':'.join([TIAB_WLT_3_ADDR_2, str(BTC_TO_SEND)]),
                                                              ':'.join([TIAB_WLT_3_ADDR_3, str(BTC_TO_SEND)]))
      unsignedTx = UnsignedTransaction().unserializeAscii(serializedUnsignedTx)
      # Should have 2 txouts to TIAB_WLT_3_ADDR_3 and the change
      self.assertEqual(len(unsignedTx.decorTxOuts), 3)
      txOutsFound = 0
      for txout in unsignedTx.decorTxOuts:
         if script_to_addrStr(txout.binScript) in [TIAB_WLT_3_ADDR_2, TIAB_WLT_3_ADDR_3]:
            self.assertEqual(txout.value, JSONtoAmount(BTC_TO_SEND))
            txOutsFound += 1
      self.assertEqual(txOutsFound, 2)

   def testListunspent(self):
      actualResult = self.jsonServer.jsonrpc_listunspent()
      self.assertEqual(len(actualResult), 5)
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
         self.assertEqual(result,
                          AmountToJSON(self.wlt.getBalance(ballanceType)))
      self.assertEqual(self.jsonServer.jsonrpc_getbalance('bogus'), -1)

if __name__ == "__main__":
   #import sys;sys.argv = ['', 'Test.testName']
   unittest.main()
