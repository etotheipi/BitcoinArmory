'''
Created on Oct 8, 2013

@author: Andy
'''
import sys
sys.path.append('..')
from tiabtest.Tiab import *

import filecmp
import json
import time

from armoryengine.ALL import *

from armoryd import ArmoryDaemon, ArmoryRPC, JSONtoAmount, \
   addMultWallets, addMultLockboxes, createFuncDict


TEST_XPUB = "tpubDC7fFeL4GbE7eWiFcBJpK9xE2RxVsXWUqiWhbvChfk3nyP9G1MyF1ga4hHpTiYVzZpyPC1b5Sv1GdxkDohpZkVydNHSCAUFeKL8UUUChYq7"
TEST_XPUB_ID = "Wqisqzab"

TX_FILENAME = "test_transaction.tx"

TEST_ADDRESS = "mz4MVnVEg7YTXTyypvznkmuHrj9d6dwXx2"
TEST_ADDRESS_BALANCE = 908.0
TEST_ADDRESS2 = "mrFNfhs1qhKXGq1FZ8qNm241fQPiNWEDMw"

TEST_LOCKBOX_ADDRESS = "2MuKNwPm3cxwB4L473ZwowttqpfD5stqdSg"

TEST_MESSAGE = "My name is Enrico Montoya"
TEST_SIGNED_MESSAGE = """-----BEGIN BITCOIN SIGNED MESSAGE-----
Comment: Signed by Bitcoin Armory v0.97.9

My name is Enrico Montoya
-----BEGIN BITCOIN SIGNATURE-----


H0kbDvHz2neLfn5FjutpRuFYnUg6SNgXzrwAfpSH9DNLuLnL0hLTUwSE5iyNoT0q
QHnHF90VNq4gEGmsMdGswmU=
=5EUe
-----END BITCOIN SIGNATURE-----
"""

COINBASE_TX = 'a96e97867f21b2d366c45af01e9747776786b3d50c996a3bd52cf654ac7b0460'
COINBASE_RAW = '01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0c02f9000102062f503253482fffffffff0100f2052a010000002321027bf17bc74a6094074600b0a2c6146d9d73e29b880684dfb3eb4e6e4ac8dc0495ac00000000'
TX    = 'db0ee46beff3a61f38bfc563f92c11449ed57c3d7d5cd5aafbe0114e5a9ceee4'
TX_OUTS = [20.0, 979.9999]
RAW_TX = '0100000001b5dbdcea08ae1ff5a547755aaab7f468a6091a573ae76c6fa5a3fcf5ec65b804010000008b4830450220081341a4e803c7c8e64c3a3fd285dca34c9f7c71c4dfc2b576d761c5783ce735022100eea66ba382d00e628d86fc5bc1928a93765e26fd8252c4d01efe22147c12b91a01410458fec9d580b0c6842cae00aecd96e89af3ff56f5be49dae425046e64057e0f499acc35ec10e1b544e0f01072296c6fa60a68ea515e59d24ff794cf8923cd30f4ffffffff0200943577000000001976a91462d978319c7d7ac6cceed722c3d08aa81b37101288acf02c41d1160000001976a91409097379782fadfbd72e5a818219cf2eb56249d288ac00000000'

TX2 = 'fe6ce1af081dae060a123608140201cfffa04ea61ffaf96e2caca2a05bd8f9c0'

PASSPHRASE1 = 'abcde'
PASSPHRASE2 = 'fghij'
PASSPHRASE3 = 'ok123'
UNLOCK_TIMEOUT = 3

RANDOM_P2SH_ADDR = "2N794AqNeu2yVfppkin4yhcRMmSGPuztoii"


# Values related primarily to createlockbox().
TWO_OF_THREE_LB_NAME = 'U2ydthgu'
TWO_OF_TWO_LB_NAME = 'ihPSpMih'
GOOD_PK_UNCOMP_1 = '04e8445082a72f29b75ca48748a914df60622a609cacfce8ed0e35804560741d292728ad8d58a140050c1016e21f285636a580f4d2711b7fac3957a594ddf416a0'
GOOD_PK_COMP_1 = '02e8445082a72f29b75ca48748a914df60622a609cacfce8ed0e35804560741d29'
GOOD_PK_UNCOMP_2 = '0439a36013301597daef41fbe593a02cc513d0b55527ec2df1050e2e8ff49c85c23cbe7ded0e7ce6a594896b8f62888fdbc5c8821305e2ea42bf01e37300116281'
GOOD_PK_COMP_2 = '0339a36013301597daef41fbe593a02cc513d0b55527ec2df1050e2e8ff49c85c2'
BAD_WLT_NAME = 'keKoEXp1'
BAD_PK = '04e8445082a72f29b75ca48748a914df60622a609cacfce8ed0e35804560741d2927'
BAD_PK_UNCOMP_1 = '04000102030405060708090a0b0c0d0e0f000102030405060708090a0b0c0d0e0f000102030405060708090a0b0c0d0e0f000102030405060708090a0b0c0d0e0f'
BAD_PK_COMP_1 = '02000102030405060708090a0b0c0d0e0f000102030405060708090a0b0c0d0e0f'
ERRSTR09 = 'The user requires more keys or wallets to unlock a lockbox (%d) ' \
           'than are required to create a lockbox (%d).' % (3, 2)
ERRSTR10 = 'The number of signatures required to unlock a lockbox (%d) ' \
           'exceeds the maximum allowed (%d)' % (8, LB_MAXM)
ERRSTR11 = 'The number of keys or wallets required to create a lockbox (%d) ' \
           'exceeds the maximum allowed (%d)' % (8, LB_MAXN)
ERRSTR12 = 'No keys or wallets were specified. %d wallets or keys are ' \
           'required to create the lockbox.' % 4
ERRSTR13 = 'The number of supplied keys or wallets (%d) exceeds the number ' \
           'required to create the lockbox (%d)' % (3, 2)
ERRSTR14 = 'The number of supplied keys or wallets (%d) is less than the ' \
           'number of required to create the lockbox (%d)' % (1, 2)
ERRSTR15 = 'Lockbox %s already exists.' % TWO_OF_TWO_LB_NAME


# These tests need to be run in the TiaB
class ClientTest(TiabTest):
   """
   These are tests that don't need the actual armoryd server to be running.
   We initialize the jsonServer and call that directly instead of
   creating an ArmoryDaemon.
   """


   def setUp(self):
      useTestnet()

      self.verifyBlockHeight()

      # wallets
      self.fileA = os.path.join(self.armoryHomeDir, FIRST_WLT_FILE_NAME)
      self.fileB = os.path.join(self.armoryHomeDir, SECOND_WLT_FILE_NAME)
      self.fileC = os.path.join(self.armoryHomeDir, THIRD_WLT_FILE_NAME)

      inWltPaths = [self.fileA, self.fileB, self.fileC]
      inWltMap = addMultWallets(inWltPaths)
      self.wltA = inWltMap[FIRST_WLT_NAME]
      self.wltB = inWltMap[SECOND_WLT_NAME]
      self.wltC = inWltMap[THIRD_WLT_NAME]

      # lockboxes
      self.fileLBA = os.path.join(
         self.armoryHomeDir, "Lockbox_%s_.lockbox.def" % FIRST_LOCKBOX_NAME)
      self.fileLBB = os.path.join(
         self.armoryHomeDir, "Lockbox_%s_.lockbox.def" % SECOND_LOCKBOX_NAME)

      inLBPaths = [self.fileLBA, self.fileLBB]
      inLBMap = addMultLockboxes(inLBPaths)
      self.lockboxA = inLBMap[FIRST_LOCKBOX_NAME]
      self.lockboxB = inLBMap[SECOND_LOCKBOX_NAME]

      inLBCppMap = {}
      # Create the CPP wallet map for each lockbox.
      for lbID,lbox in inLBMap.iteritems():
         scraddrReg = script_to_scrAddr(lbox.binScript)
         scraddrP2SH = script_to_scrAddr(script_to_p2sh_script(lbox.binScript))
         lockboxScrAddr = [scraddrReg, scraddrP2SH]

         inLBCppMap[lbID] = getBDM().registerLockbox(lbID, lockboxScrAddr)

      self.privKey   = SecureBinaryData(b'\xaa'*32)

      self.walletFile = self.wltA.wltFileRef

      wallets = [self.wltA, self.wltB, self.wltC]
      self.jsonServer = ArmoryRPC(
         self.wltA,
         inWltMap=inWltMap,
         lockbox=self.lockboxA,
         inLBMap=inLBMap,
         inLBCppWalletMap=inLBCppMap,
         armoryHomeDir=self.armoryHomeDir)

      self.wltIDs = []

      for wlt in wallets:
         wlt.fillKeyPool()
         self.wltIDs.append(wlt.uniqueIDB58)

      for i in range(4):
         self.wltA.getNextChangeAddress()


      #register a callback
      getBDM().registerCppNotification(self.armoryDTiabTestCallback)

      #flag to check on wallet scan status
      self.numberOfWalletsScanned = 0

      for wlt in wallets:
         wlt.registerWallet()
         time.sleep(0.5)

      #wait on scan for 20sec then raise if the scan hasn't finished yet
      i = 0
      while self.numberOfWalletsScanned < len(self.wltIDs):
         time.sleep(0.5)
         i += 1
         if i >= 40:
            raise RuntimeError("self.numberOfWalletsScanned = %d" % self.numberOfWalletsScanned)

      self.jsonServer.jsonrpc_setactivelockbox(FIRST_LOCKBOX_NAME)
      self.jsonServer.jsonrpc_setactivewallet(FIRST_WLT_NAME)


   def tearDown(self):
      getBDM().unregisterCppNotification(self.armoryDTiabTestCallback)
      self.wltA.unregisterWallet()
      self.wltB.unregisterWallet()
      self.wltC.unregisterWallet()
      self.resetWalletFiles()
      removeIfExists(TX_FILENAME)


   def armoryDTiabTestCallback(self, action, args):
      if action == REFRESH_ACTION:
         for wltID in args:
            if wltID in self.wltIDs:
               self.numberOfWalletsScanned += 1


   def removeFileList(self, fileList):
      for f in fileList:
         removeIfExists(f)


   def testBackupWallet(self):
      backupTestPath = os.path.join(self.armoryHomeDir,
                                    "%s.test" % FIRST_WLT_FILE_NAME)
      # Remove backupTestPath in case it exists
      backupFileList = [backupTestPath]
      self.removeFileList(backupFileList)
      # Remove the backup test path that is to be created after tear down.
      self.addCleanup(self.removeFileList, backupFileList)
      self.jsonServer.jsonrpc_backupwallet(backupTestPath)
      self.assertTrue(filecmp.cmp(backupTestPath, self.fileA))
      result = self.jsonServer.jsonrpc_backupwallet(backupTestPath)
      self.assertEqual(result['Error Type'], 'FileExists')
      result = self.jsonServer.jsonrpc_backupwallet('/root/blah')
      self.assertEqual(result['Error Type'], 'BackupFailed')


   def testClearAddressMetadata(self):
      # also tests: getaddressmetadata setaddressmetadata
      self.jsonServer.jsonrpc_clearaddressmetadata()
      metadata = {TEST_ADDRESS:{"something": "whatever"}}
      self.jsonServer.jsonrpc_setaddressmetadata(metadata)
      result = self.jsonServer.jsonrpc_getaddressmetadata()
      self.assertEqual(result[TEST_ADDRESS]["something"], "whatever")
      self.jsonServer.jsonrpc_clearaddressmetadata()
      result = self.jsonServer.jsonrpc_getaddressmetadata()
      self.assertEqual(result, {})
      result = self.jsonServer.jsonrpc_setaddressmetadata({'1178':{"a":"b"}})
      self.assertEqual(result['Error Type'], 'InvalidBitcoinAddress')
      result = self.jsonServer.jsonrpc_setaddressmetadata({
         'mjNDcriv5k1YW7opWNX3iuCbYyWNHGAbYi':{"a":"b"}})
      self.assertEqual(result['Error Type'], 'AddressNotInWallet')


   def testCreateLockbox(self):
      # also tests: createwallet
      self.assertEqual(self.jsonServer.jsonrpc_getactivelockbox(),
                       FIRST_LOCKBOX_NAME)
      self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE1)

      pubkeys = []
      pubkeys.append(self.wltA.peekNextReceivingAddress().getSerializedPubKey("hex"))
      pubkeys.append(self.wltB.peekNextReceivingAddress().getSerializedPubKey("hex"))
      pubkeys.append(self.wltC.peekNextReceivingAddress().getSerializedPubKey("hex"))
      # This test should succeed.
      result1 = self.jsonServer.jsonrpc_createlockbox(2, 3,
                                                      pubkeys[0],
                                                      pubkeys[2],
                                                      FOURTH_WLT_NAME)
      self.assertEqual(TWO_OF_THREE_LB_NAME, result1['id'])

      # This test should succeed.
      result3 = self.jsonServer.jsonrpc_createlockbox(2, 2,
                                                      pubkeys[1],
                                                      pubkeys[2])
      self.assertEqual(TWO_OF_TWO_LB_NAME, result3['id'])
      listResult3 = self.jsonServer.jsonrpc_listloadedlockboxes()
      self.assertEqual(len(listResult3.keys()), 4)
      self.assertTrue(TWO_OF_TWO_LB_NAME in listResult3.values())

      # This test should fail because of a bad wallet name.
      result4 = self.jsonServer.jsonrpc_createlockbox(2, 2,
                                                      pubkeys[0],
                                                      BAD_WLT_NAME)
      self.assertTrue(BAD_WLT_NAME in result4['Error Value'])

      # This test should fail because of a malformed, uncompressed public key.
      result5 = self.jsonServer.jsonrpc_createlockbox(2, 2,
                                                      pubkeys[0],
                                                      BAD_PK_UNCOMP_1)
      self.assertTrue(BAD_PK_UNCOMP_1 in result5['Error Value'])

      # This test should fail because of a malformed, compressed public key.
      result6 = self.jsonServer.jsonrpc_createlockbox(2, 2,
                                                      pubkeys[0],
                                                      BAD_PK_COMP_1)
      self.assertTrue(BAD_PK_COMP_1 in result6['Error Value'])


      # This test should fail due to a malformed public key (incorrect length).
      result8 = self.jsonServer.jsonrpc_createlockbox(2, 2,
                                                      pubkeys[0],
                                                      BAD_PK)
      self.assertTrue(BAD_PK in result8['Error Value'])

      # These tests should fail for various reasons related to the # of inputs.
      result09 = self.jsonServer.jsonrpc_createlockbox(3, 2,
                                                       pubkeys[0],
                                                       pubkeys[2])
      self.assertTrue(ERRSTR09 in result09['Error Value'])
      result10 = self.jsonServer.jsonrpc_createlockbox(8, 8,
                                                       pubkeys[0],
                                                       pubkeys[1],
                                                       pubkeys[2],
                                                       FIRST_WLT_NAME,
                                                       SECOND_WLT_NAME,
                                                       THIRD_WLT_NAME,
                                                       GOOD_PK_UNCOMP_1,
                                                       GOOD_PK_UNCOMP_2)
      self.assertTrue(ERRSTR10 in result10['Error Value'])
      result11 = self.jsonServer.jsonrpc_createlockbox(1, 8,
                                                       pubkeys[0],
                                                       pubkeys[1],
                                                       pubkeys[2],
                                                       FIRST_WLT_NAME,
                                                       SECOND_WLT_NAME,
                                                       THIRD_WLT_NAME,
                                                       GOOD_PK_UNCOMP_1,
                                                       GOOD_PK_UNCOMP_2)
      self.assertTrue(ERRSTR11 in result11['Error Value'])
      result12 = self.jsonServer.jsonrpc_createlockbox(1, 4)
      self.assertTrue(ERRSTR12 in result12['Error Value'])
      result13 = self.jsonServer.jsonrpc_createlockbox(1, 2,
                                                       pubkeys[0],
                                                       pubkeys[1],
                                                       pubkeys[2])
      self.assertTrue(ERRSTR13 in result13['Error Value'])
      result14 = self.jsonServer.jsonrpc_createlockbox(1, 2,
                                                       pubkeys[0])
      self.assertTrue(ERRSTR14 in result14['Error Value'])

      result15 = self.jsonServer.jsonrpc_createlockbox(2, 2,
                                                       pubkeys[1],
                                                       pubkeys[2])
      self.assertEqual(ERRSTR15, result15['Error Value'])


      # These tests should succeed.
      self.jsonServer.jsonrpc_setactivelockbox(TWO_OF_TWO_LB_NAME)
      self.assertEqual(self.jsonServer.jsonrpc_getactivelockbox(),
                       TWO_OF_TWO_LB_NAME)
      self.jsonServer.jsonrpc_setactivelockbox(TWO_OF_THREE_LB_NAME)
      self.assertEqual(self.jsonServer.jsonrpc_getactivelockbox(),
                       TWO_OF_THREE_LB_NAME)
      self.resetWalletFiles()



   def testCreateLockboxUSTXForMany(self):
      # also tests: signasciitransaction gethextxtobroadcast

      amount1 = 0.2
      amount2 = 0.3
      serializedUnsignedTx = self.jsonServer.jsonrpc_createlockboxustxformany(
         '0', '%s,%s' % (TEST_ADDRESS, amount1),
         '%s,%s' % (TEST_ADDRESS2, amount2))

      unsignedTx = UnsignedTransaction().unserializeAscii(serializedUnsignedTx)
      # Should have 3 txouts to TEST_ADDRESS* and the change address
      self.assertEqual(len(unsignedTx.decorTxOuts), 3)
      txOutsFound = 0

      # sign with one key
      f = open(TX_FILENAME, b'wb')
      f.write(serializedUnsignedTx)
      f.close()
      self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE1)
      serializedSignedTx = \
            self.jsonServer.jsonrpc_signasciitransaction(TX_FILENAME)

      # sign with the other key
      f = open(TX_FILENAME, b'wb')
      f.write(serializedSignedTx)
      f.close()
      self.jsonServer.jsonrpc_setactivewallet(SECOND_WLT_NAME)
      self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE3)
      serializedSignedTx = \
            self.jsonServer.jsonrpc_signasciitransaction(TX_FILENAME)

      self.wltA.unlock(SecureBinaryData(PASSPHRASE1), timeout=1000000)
      signedTx = UnsignedTransaction().unserializeAscii(serializedSignedTx)
      # check number of outputs. two addresses get amount1 and amount2
      # and the other goes to change
      self.assertEqual(len(signedTx.decorTxOuts), 3)
      f = open(TX_FILENAME, b'wb')
      f.write(signedTx.serializeAscii())
      f.close()
      txHexToBroadcast = self.jsonServer.jsonrpc_gethextxtobroadcast(TX_FILENAME)
      finalPyTx = PyTx().unserialize(hex_to_binary(txHexToBroadcast))
      self.assertEqual(len(finalPyTx.outputs), 3)
      outVals = [o.value for o in finalPyTx.outputs]
      self.assertTrue(JSONtoAmount(amount1) in outVals)
      self.assertTrue(JSONtoAmount(amount2) in outVals)


   def testCreateLockboxUSTXToAddress(self):
      # also tests: signasciitransaction gethextxtobroadcast

      amount = 0.9
      serializedUnsignedTx = self.jsonServer.jsonrpc_createlockboxustxtoaddress(
         TEST_ADDRESS, str(amount), '0.0')
      unsignedTx = UnsignedTransaction().unserializeAscii(serializedUnsignedTx)
      # Should have 2 txouts to TEST_ADDRESS and the change address
      self.assertEqual(len(unsignedTx.decorTxOuts), 2)
      txOutsFound = 0

      # sign with one key
      f = open(TX_FILENAME, b'wb')
      f.write(serializedUnsignedTx)
      f.close()
      self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE1)
      serializedSignedTx = \
            self.jsonServer.jsonrpc_signasciitransaction(TX_FILENAME)

      # sign with the other key
      f = open(TX_FILENAME, b'wb')
      f.write(serializedSignedTx)
      f.close()
      self.jsonServer.jsonrpc_setactivewallet(SECOND_WLT_NAME)
      self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE3)
      serializedSignedTx = \
            self.jsonServer.jsonrpc_signasciitransaction(TX_FILENAME)

      self.wltA.unlock(SecureBinaryData(PASSPHRASE1), timeout=1000000)
      signedTx = UnsignedTransaction().unserializeAscii(serializedSignedTx)
      # check number of outputs. one should be to TEST_ADDRESS
      # and the other goes to change
      self.assertEqual(len(signedTx.decorTxOuts), 2)
      f = open(TX_FILENAME, b'wb')
      f.write(signedTx.serializeAscii())
      f.close()
      txHexToBroadcast = self.jsonServer.jsonrpc_gethextxtobroadcast(TX_FILENAME)
      finalPyTx = PyTx().unserialize(hex_to_binary(txHexToBroadcast))
      self.assertEqual(len(finalPyTx.outputs), 2)
      outVals = [o.value for o in finalPyTx.outputs]
      self.assertTrue(JSONtoAmount(amount) in outVals)


   def testCreateUSTXForMany(self):
      # also tests: signasciitransaction gethextxtobroadcast

      amount1 = 0.5
      amount2 = 0.4
      serializedUnsignedTx = self.jsonServer.jsonrpc_createustxformany(
         '0.0', ','.join([TEST_ADDRESS, str(amount1)]),
         ','.join([TEST_ADDRESS2, str(amount2)]))
      unsignedTx = UnsignedTransaction().unserializeAscii(serializedUnsignedTx)
      # Should have 3 txouts to TEST_ADDRESS* and the change
      self.assertEqual(len(unsignedTx.decorTxOuts), 3)
      txOutsFound = 0
      for txout in unsignedTx.decorTxOuts:
         if script_to_addrStr(txout.binScript) == TEST_ADDRESS:
            self.assertEqual(txout.value, JSONtoAmount(amount1))
            txOutsFound += 1
         elif script_to_addrStr(txout.binScript) == TEST_ADDRESS2:
            self.assertEqual(txout.value, JSONtoAmount(amount2))
            txOutsFound += 1
      self.assertEqual(txOutsFound, 2)

      f = open(TX_FILENAME, 'w')
      f.write(serializedUnsignedTx)
      f.close()
      self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE1)
      serializedSignedTx = \
            self.jsonServer.jsonrpc_signasciitransaction(TX_FILENAME)
      self.wltA.unlock(SecureBinaryData(PASSPHRASE1), timeout=1000000)
      signedTx = UnsignedTransaction().unserializeAscii(serializedSignedTx)
      # check number of outputs two TEST_ADDRESS outputs
      # and the other goes to change
      self.assertEqual(len(signedTx.decorTxOuts), 3)
      f = open(TX_FILENAME, 'w')
      f.write(signedTx.serializeAscii())
      f.close()
      txHexToBroadcast = self.jsonServer.jsonrpc_gethextxtobroadcast(TX_FILENAME)
      finalPyTx = PyTx().unserialize(hex_to_binary(txHexToBroadcast))
      self.assertEqual(len(finalPyTx.outputs), 3)
      outVals = [o.value for o in finalPyTx.outputs]
      self.assertTrue(JSONtoAmount(amount1) in outVals)
      self.assertTrue(JSONtoAmount(amount2) in outVals)


   def testCreateUSTXToAddress(self):
      # also tests: signasciitransaction and gethextxtobroadcast

      amount = 1.0
      serializedUnsignedTx = \
         self.jsonServer.jsonrpc_createustxtoaddress(TEST_ADDRESS2, amount, '0')
      unsignedTx = UnsignedTransaction().unserializeAscii(serializedUnsignedTx)
      # Should have 2 txouts to TEST_ADDRESS* and the change
      self.assertEqual(len(unsignedTx.decorTxOuts), 2)
      foundTxOut = False
      for txout in unsignedTx.decorTxOuts:
         if script_to_addrStr(txout.binScript) == TEST_ADDRESS2:
            self.assertEqual(txout.value, JSONtoAmount(amount))
            foundTxOut = True
      self.assertTrue(foundTxOut)

      f = open(TX_FILENAME, 'w')
      f.write(serializedUnsignedTx)
      f.close()
      self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE1)
      serializedSignedTx = \
            self.jsonServer.jsonrpc_signasciitransaction(TX_FILENAME)
      self.wltA.unlock(SecureBinaryData(PASSPHRASE1), timeout=1000000)
      signedTx = UnsignedTransaction().unserializeAscii(serializedSignedTx)
      # check number of outputs 1 btc to TEST_ADDRESS and 1 to change
      self.assertEqual(len(signedTx.decorTxOuts), 2)
      self.assertTrue(JSONtoAmount(amount) in
             [signedTx.decorTxOuts[0].value,
              signedTx.decorTxOuts[1].value])
      f = open(TX_FILENAME, 'w')
      f.write(signedTx.serializeAscii())
      f.close()
      txHexToBroadcast = self.jsonServer.jsonrpc_gethextxtobroadcast(TX_FILENAME)
      finalPyTx = PyTx().unserialize(hex_to_binary(txHexToBroadcast))
      self.assertEqual(len(finalPyTx.outputs), 2)
      outVals = [o.value for o in finalPyTx.outputs]
      self.assertTrue(JSONtoAmount(amount) in outVals)


   def testCreateWallet(self):
      self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE1)
      testName = "blahblahblahblah"
      testDescription = "hello"
      result = self.jsonServer.jsonrpc_createwallet(testName, testDescription)
      self.assertEqual(result, '2jp3AVEBW')
      self.resetWalletFiles()


   def testCreateWalletFile(self):
      testName = "blahblahblahblah"
      self.jsonServer.jsonrpc_createwalletfile(testName, PASSPHRASE1)
      result = self.jsonServer.jsonrpc_listloadedwallets()
      self.assertEqual(len(result), 5)
      self.assertTrue(testName in str(result))
      self.resetWalletFiles()


   def testDecodeRawTransaction(self):
      result = self.jsonServer.jsonrpc_decoderawtransaction(RAW_TX)
      # Test specific values pulled from bitcoin daemon's output for the test raw TX
      expectScriptStr = 'OP_DUP OP_HASH160 PUSHDATA(20) [62d978319c7d7ac6cceed722c3d08aa81b371012] OP_EQUALVERIFY OP_CHECKSIG'
      self.assertEqual(result['locktime'], 0)
      self.assertEqual(result['version'], 1)
      self.assertEqual(len(result['vin']), 1)
      self.assertEqual(result['vin'][0]['sequence'], 4294967295L)
      self.assertEqual(result['vin'][0]['scriptSig']['hex'], '4830450220081341a4e803c7c8e64c3a3fd285dca34c9f7c71c4dfc2b576d761c5783ce735022100eea66ba382d00e628d86fc5bc1928a93765e26fd8252c4d01efe22147c12b91a01410458fec9d580b0c6842cae00aecd96e89af3ff56f5be49dae425046e64057e0f499acc35ec10e1b544e0f01072296c6fa60a68ea515e59d24ff794cf8923cd30f4')
      self.assertEqual(result['vin'][0]['vout'], 1)
      self.assertEqual(result['vin'][0]['txid'], '04b865ecf5fca3a56f6ce73a571a09a668f4b7aa5a7547a5f51fae08eadcdbb5')
      self.assertEqual(len(result['vout']), 2)
      self.assertEqual(result['vout'][0]['value'], 20.0)
      self.assertEqual(result['vout'][0]['n'], 0)
      self.assertEqual(result['vout'][0]['scriptPubKey']['reqSigs'], 1)
      self.assertEqual(result['vout'][0]['scriptPubKey']['hex'], '76a91462d978319c7d7ac6cceed722c3d08aa81b37101288ac')
      self.assertEqual(result['vout'][0]['scriptPubKey']['addresses'], ['mpXd2u8fPVYdL1Nf9bZ4EFnqhkNyghGLxL'])
      self.assertEqual(result['vout'][0]['scriptPubKey']['asm'], expectScriptStr)
      self.assertEqual(result['vout'][0]['scriptPubKey']['type'], 'Standard (PKH)')
      self.assertEqual(result['vout'][1]['scriptPubKey']['type'], 'Standard (PKH)')
      result = self.jsonServer.jsonrpc_decoderawtransaction(COINBASE_RAW)
      self.assertFalse(result['vin'][0].get('coinbase') is None)


   def testDumpPrivKey(self):
      testPrivKey = self.privKey.toBinStr()
      hash160 = convertKeyDataToAddress(testPrivKey)
      addr58 = hash160_to_addrStr(hash160)

      # Verify that a locked wallet Raises WalletUnlockNeeded Exception
      self.wltA.lock()
      result = self.jsonServer.jsonrpc_dumpprivkey(addr58, 'hex')
      self.assertEqual(result['Error Type'],'WalletUnlockNeeded')

      # unlock the wallet
      result =  self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE1)

      # Verify that a bogus addrss Raises InvalidBitcoinAddress Exception
      result =  self.jsonServer.jsonrpc_dumpprivkey('bogus', 'hex')
      self.assertEqual(result['Error Type'],'InvalidBitcoinAddress')

      result =  self.jsonServer.jsonrpc_dumpprivkey(addr58, 'hex')
      self.assertEqual(result['Error Type'],'PrivateKeyNotFound')

      # verify that the first private key can be found
      firstAddr = self.wltA.getNextReceivingAddress()
      firstAddr58 = firstAddr.getAddrStr()
      actualPrivateKeyHex = self.jsonServer.jsonrpc_dumpprivkey(firstAddr58, \
                                                                'hex')
      actualPrivateKeyB58 = self.jsonServer.jsonrpc_dumpprivkey(firstAddr58, \
                                                                'base58')

      # the private key is now compressed, so we need the \x01 at the end
      self.privKey = firstAddr.getPlainPrivKeyCopy().toBinStr() + "\x01"
      expectedPrivateKeyHex = binary_to_hex(self.privKey)
      expectedPrivateKeyB58 = privKey_to_base58(self.privKey)
      self.assertEqual(actualPrivateKeyHex, expectedPrivateKeyHex)
      self.assertEqual(actualPrivateKeyB58, expectedPrivateKeyB58)


   def testEncryptWalletFile(self):
      self.jsonServer.jsonrpc_setactivewallet(FIRST_WLT_NAME)

      # verify that the passphrase can be changed
      result = self.jsonServer.jsonrpc_encryptwalletfile(PASSPHRASE1,
                                                         PASSPHRASE2)
      successMessage = 'Wallet %s has been encrypted' \
                       ' with the new passphrase' % FIRST_WLT_NAME
      self.assertEqual(result, successMessage)
      self.assertTrue(self.wltA.isLocked())


      # Verify that changing the encryption to the same passphrase raises
      # an error
      result = self.jsonServer.jsonrpc_encryptwalletfile(PASSPHRASE2,
                                                         PASSPHRASE2)
      self.assertEqual(result.get('Error Type'), 'PassphraseError')

      # Verify that changing the encryption with no passphrase raises
      # an error
      result = self.jsonServer.jsonrpc_encryptwalletfile('',
                                                         PASSPHRASE2)
      self.assertEqual(result.get('Error Type'), 'PassphraseError')


      # Verify that giving the wrong passphrase results in an error
      self.jsonServer.jsonrpc_setactivewallet(FIRST_WLT_NAME)
      result = self.jsonServer.jsonrpc_encryptwalletfile(PASSPHRASE1,
                                                         PASSPHRASE2)
      self.assertEqual(result.get('Error Type'), 'PassphraseError')

      # change back the passphrase
      result = self.jsonServer.jsonrpc_encryptwalletfile(PASSPHRASE2,
                                                         PASSPHRASE1)
      self.assertEqual(result, successMessage)

      # remove encryption from the wallet
      result = self.jsonServer.jsonrpc_encryptwalletfile(PASSPHRASE1, '')
      self.assertEqual(result, 'Wallet %s has been decrypted.' % FIRST_WLT_NAME)

      # verify we can sign whatever since there's no encryption
      result = self.jsonServer.jsonrpc_signmessage(TEST_ADDRESS, TEST_MESSAGE)
      self.assertEqual(result[:10], "-----BEGIN")

      # put the encryption back to the wallet
      result = self.jsonServer.jsonrpc_encryptwalletfile('', PASSPHRASE1)
      self.assertEqual(result, 'Wallet %s has been encrypted.' % FIRST_WLT_NAME)
      
      # verify we can't sign whatever since there's encryption now
      result = self.jsonServer.jsonrpc_signmessage(TEST_ADDRESS, TEST_MESSAGE)
      self.assertEqual(result['Error Type'], 'WalletUnlockNeeded')


   def testGetActiveLockbox(self):
      # also tests setactivelockbox
      self.jsonServer.jsonrpc_setactivewallet(FIRST_LOCKBOX_NAME)
      result = self.jsonServer.jsonrpc_getactivelockbox()
      self.assertEqual(result, FIRST_LOCKBOX_NAME)

      bogusResult = self.jsonServer.jsonrpc_setactivelockbox('bogus lb name')
      self.assertTrue('does not exist' in bogusResult)


   def testGetActiveWallet(self):
      # also tests setactivewallet
      self.jsonServer.jsonrpc_setactivewallet(FIRST_WLT_NAME)
      result = self.jsonServer.jsonrpc_getactivewallet()
      self.assertEqual(result, FIRST_WLT_NAME)

      bogusResult = self.jsonServer.jsonrpc_setactivewallet('bogus wallet name')
      self.assertTrue('does not exist' in bogusResult)


   def testGetAddrBalance(self):
      for btype in ['spendable','spend', 'unconf', 'unconfirmed',
                    'ultimate','unspent', 'full']:
         result = self.jsonServer.jsonrpc_getaddrbalance(TEST_ADDRESS, btype)
         self.assertEqual(result, TEST_ADDRESS_BALANCE)
         result = self.jsonServer.jsonrpc_getaddrbalance(
            FIRST_LOCKBOX_ADDRESS, btype)
         self.assertEqual(result, FIRST_LOCKBOX_BALANCE)
      result = self.jsonServer.jsonrpc_getaddrbalance(RANDOM_P2SH_ADDR)
      self.assertEqual(result['Error Type'], 'BitcoindError')


   def testGetAddressMetadata(self):
      # see testClearAddressMetadata
      pass


   def testGetArmoryDInfo(self):
      info = self.jsonServer.jsonrpc_getarmorydinfo()
      self.assertEqual(info['blocks'], TOP_TIAB_BLOCK)
      self.assertEqual(info['bdmstate'], BDM_BLOCKCHAIN_READY)
      self.assertEqual(info['walletversionstr'], '2.00')
      self.assertEqual(info['difficulty'], 1.0)
      self.assertEqual(info['balance'], FIRST_WLT_BALANCE)


   def testGetBalance(self):
      balances = {
         'spendable' : FIRST_WLT_BALANCE,
         'spend' : FIRST_WLT_BALANCE,
         'unconf' : FIRST_WLT_BALANCE,
         'unconfirmed' :  FIRST_WLT_BALANCE,
         'total' : FIRST_WLT_BALANCE,
         'ultimate'  :  FIRST_WLT_BALANCE,
         'unspent' :  FIRST_WLT_BALANCE,
         'full' :  FIRST_WLT_BALANCE,
      }
      for balanceType, val in balances.iteritems():
         result = self.jsonServer.jsonrpc_getbalance(balanceType)
         self.assertEqual(result, val)


   def testGetBlock(self):
      block = self.jsonServer.jsonrpc_getblock('0000000064a1ad1f15981a713a6ef08fd98f69854c781dc7b8789cc5f678e01f')
      # For now just verify that raw transaction is correct
      self.assertEqual(block['rawheader'], '02000000d8778a50d43d3e02c4c20bdd0ed97077a3c4bef3e86ce58975f6f43a00000000d25912cfc67228748494d421512c7a6cc31668fa82b72265261558802a89f4c2e0350153ffff001d10bcc285',)
      result = self.jsonServer.jsonrpc_getblock('0000000064a1ad1f15981a713a6ef08fd98f69854c781dc7b8789cc5f678e01f', 'False')
      self.assertEqual(result['Error Type'], 'NotImplementedError')
      result = self.jsonServer.jsonrpc_getblock('0000000064a1ad1f15981a713a6ef08fd98f69854c781dc7b8789cc5f678e01f', 'blah')
      self.assertEqual(result['Error Type'], 'InvalidRequest')
      # TODO: test when the BDM is offline
      # TODO: test when block doesn't exist


   def testGetHexTxToBroadcast(self):
      # see testCreateUSTX*
      pass
      # TODO: test the various ways it can error (BadAddress, NetworkID, Unserialize)
      # TODO: test the various invalidities (bad data, invalid sigs, not enough sigs)


   def testGetHistoryPageCount(self):
      # see testListTransactions
      pass


   def testGetLedger(self):
      # wallet
      ledger = self.jsonServer.jsonrpc_getledger(FIRST_WLT_NAME)
      self.assertEqual(len(ledger), 5)
      amountList = [row['amount'] for row in ledger]
      expectedAmountList = [20.0, 900.0, 5.0, 3.0, 1.0]
      self.assertEqual(amountList, expectedAmountList)
      self.assertEqual(ledger[0]['direction'], 'receive')
      self.assertEqual(len(ledger[0]['recipme']), 1)
      self.assertEqual(ledger[0]['recipme'][0]['amount'], 20.0)
      self.assertEqual(len(ledger[0]['recipother']), 1)
      self.assertEqual(ledger[0]['recipother'][0]['amount'], 918.8996)
      self.assertEqual(len(ledger[0]['senderme']), 0)
      self.assertEqual(len(ledger[0]['senderother']), 1)

      # lockbox
      ledger = self.jsonServer.jsonrpc_getledger(FIRST_LOCKBOX_NAME)
      self.assertTrue(len(ledger)>0)
      amountList = [row['amount'] for row in ledger]
      expectedAmountList = [FIRST_LOCKBOX_BALANCE]
      self.assertEqual(amountList, expectedAmountList)
      self.assertEqual(ledger[0]['direction'], 'receive')
      self.assertEqual(len(ledger[0]['recipme']), 1)
      self.assertEqual(ledger[0]['recipme'][0]['amount'], FIRST_LOCKBOX_BALANCE)
      self.assertEqual(len(ledger[0]['recipother']), 1)
      self.assertEqual(ledger[0]['recipother'][0]['amount'], 2.4998)
      self.assertEqual(len(ledger[0]['senderme']), 0)
      self.assertEqual(len(ledger[0]['senderother']), 1)

      # invalid
      result = self.jsonServer.jsonrpc_getledger("nonsense")
      self.assertEqual(result["Error Type"], 'WalletDoesNotExist')

      # TODO: test various ways that getledger can give errors


   def testGetLedgerSimple(self):
      ledger = self.jsonServer.jsonrpc_getledgersimple(FIRST_WLT_NAME)
      self.assertEqual(len(ledger), 5)
      amountList = [row['amount'] for row in ledger]
      expectedAmountList = [20.0, 900.0, 5.0, 3.0, 1.0]
      self.assertEqual(amountList[:5], expectedAmountList)


   def testGetLockboxBalance(self):
      balances = {
         'spendable' : FIRST_LOCKBOX_BALANCE,
         'spend' : FIRST_LOCKBOX_BALANCE,
         'unconf' : FIRST_LOCKBOX_BALANCE,
         'unconfirmed' :  FIRST_LOCKBOX_BALANCE,
         'total' : FIRST_LOCKBOX_BALANCE,
         'ultimate'  :  FIRST_LOCKBOX_BALANCE,
         'unspent' :  FIRST_LOCKBOX_BALANCE,
         'full' :  FIRST_LOCKBOX_BALANCE,
      }
      for balanceType, val in balances.iteritems():
         result = self.jsonServer.jsonrpc_getlockboxbalance(balanceType)
         self.assertEqual(result, val)


   def testGetLockboxInfo(self):
      # also tests: setlockboxinfo
      testName = "some weird name"
      testDesc = "some looooooooooooooooooooooong description"
      self.jsonServer.jsonrpc_setlockboxinfo(
         FIRST_LOCKBOX_NAME, testName, testDesc)
      lockboxInfo = self.jsonServer.jsonrpc_getlockboxinfo()
      self.assertEqual(lockboxInfo['name'], testName)
      self.assertEqual(lockboxInfo['description'], testDesc)
      self.assertEqual(lockboxInfo['M'], 2)
      self.assertEqual(lockboxInfo['N'], 3)
      self.assertEqual(lockboxInfo['balance'], FIRST_LOCKBOX_BALANCE)
      hexInfo = self.jsonServer.jsonrpc_getlockboxinfo(
         SECOND_LOCKBOX_NAME, 'Hex')
      self.assertEqual(hexInfo, '010000000b1109072800545500000000104c6f636b626f782034396a36614354462634396a3661435446202d20322d6f662d32202d20437265617465642062792061726d6f72796402022e010000000b1109072102ff299f3e424d458ba1a6a9332f60bccc4048a392cdb21796e218b89491b2c53b000000002e010000000b11090721038ceba585dcdfa4e435b4f067c2865c84512ed34878d267790f41e71e9d8bedde00000000')
      base64Info = self.jsonServer.jsonrpc_getlockboxinfo(
         SECOND_LOCKBOX_NAME, 'BASE64')
      self.assertEqual(base64Info, 'MDEwMDAwMDAwYjExMDkwNzI4MDA1NDU1MDAwMDAwMDAxMDRjNmY2MzZiNjI2Zjc4MjAzNDM5NmEzNjYxNDM1NDQ2MjYzNDM5NmEzNjYxNDM1NDQ2MjAyZDIwMzIyZDZmNjYyZDMyMjAyZDIwNDM3MjY1NjE3NDY1NjQyMDYyNzkyMDYxNzI2ZDZmNzI3OTY0MDIwMjJlMDEwMDAwMDAwYjExMDkwNzIxMDJmZjI5OWYzZTQyNGQ0NThiYTFhNmE5MzMyZjYwYmNjYzQwNDhhMzkyY2RiMjE3OTZlMjE4Yjg5NDkxYjJjNTNiMDAwMDAwMDAyZTAxMDAwMDAwMGIxMTA5MDcyMTAzOGNlYmE1ODVkY2RmYTRlNDM1YjRmMDY3YzI4NjVjODQ1MTJlZDM0ODc4ZDI2Nzc5MGY0MWU3MWU5ZDhiZWRkZTAwMDAwMDAw')
      result = self.jsonServer.jsonrpc_getlockboxinfo(SECOND_LOCKBOX_NAME, 'a')
      self.assertEqual(result['Error Type'], 'InvalidRequest')
      result = self.jsonServer.jsonrpc_getlockboxinfo('nonsense')
      self.assertEqual(result['Error Type'], 'LockboxDoesNotExist')
      # TODO: figure out a way to test when Lockboxes don't exist


   def testGetNewAddress(self):
      addr = self.wltA.peekNextReceivingAddress().getAddrStr()
      result = self.jsonServer.jsonrpc_getnewaddress()
      self.assertEqual(result, addr)
      addr = self.wltA.peekNextChangeAddress().getAddrStr()
      result = self.jsonServer.jsonrpc_getnewaddress(1)
      self.assertEqual(result, addr)
      result = self.jsonServer.jsonrpc_getnewaddress(2)
      self.assertEqual(result['Error Type'], 'InvalidRequest')


   def testGetRawTransaction(self):
      actualRawTx = self.jsonServer.jsonrpc_getrawtransaction(TX)
      pyTx = PyTx().unserialize(hex_to_binary(actualRawTx))
      self.assertEquals(TX, binary_to_hex(pyTx.getHash(), BIGENDIAN))
      verboseTx = self.jsonServer.jsonrpc_getrawtransaction(TX, '1')
      self.assertEqual(len(verboseTx['vout']), 2)
      result = self.jsonServer.jsonrpc_getrawtransaction('01')
      self.assertEqual(result['Error Type'], 'InvalidTransaction')
      result = self.jsonServer.jsonrpc_getrawtransaction('nonsense')
      self.assertEqual(result['Error Type'], 'TypeError')


   def testGetReceivedByAddress(self):
      result = self.jsonServer.jsonrpc_getreceivedbyaddress(TEST_ADDRESS)
      self.assertEqual(result, TEST_ADDRESS_BALANCE)
      result = self.jsonServer.jsonrpc_getreceivedbyaddress(
         FIRST_LOCKBOX_ADDRESS)
      self.assertEqual(result, FIRST_LOCKBOX_BALANCE)
      result = self.jsonServer.jsonrpc_getreceivedbyaddress(
         '1EHNa6Q4Jz2uvNExL497mE43ikXhwF6kZm')
      self.assertEqual(result['Error Type'], 'BadAddressError')


   def testGetReceivedFromAddress(self):
      result = self.jsonServer.jsonrpc_getreceivedfromaddress(FIRST_WLT_ADDR1)
      self.assertEqual(result, 19.9999)
      result = self.jsonServer.jsonrpc_getreceivedfromaddress(FIRST_WLT_ADDR2)
      self.assertEqual(result, 0)


   def testGetReceivedFromSigner(self):
      # unlock first
      self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE1)
      addrObj = self.wltA.getAddress(addrStr_to_scrAddr(FIRST_WLT_ADDR1))
      clearSignMessage = addrObj.clearSignMessage(TEST_MESSAGE)
      inMsg = '\"' + clearSignMessage + '\"'
      result = self.jsonServer.jsonrpc_getreceivedfromsigner(inMsg)
      self.assertEqual(result['message'], TEST_MESSAGE)
      self.assertEqual(result['amount'], 19.9999)


   def testGetTransaction(self):
      tx = self.jsonServer.jsonrpc_gettransaction(TX2)
      self.assertEqual(tx, {
         'category': 'receive',
         'confirmations': TOP_TIAB_BLOCK - 247,
         'direction': 'receive',
         'fee': 0.0001,
         'infomissing': False,
         'inputs': [{'fromtxid': '111842cb336995ac460f302f9f611e94e5b27222368d79cfd7db4c7cbc071572', 'ismine': False, 'fromtxindex': 0, 'value': 938.8997, 'address': 'mikxgMUqkk6Tts1D39Hhx6wKEeQbBH3ons'}],
         'mainbranch': True,
         'netdiff': 20.0,
         'numtxin': 1,
         'numtxout': 2,
         'orderinblock': 1,
         'outputs': [{'address': 'mfaNcTbpiX2f6WXsjREoYsmM2VKBLWRu1N', 'value': 918.8996, 'ismine': False}, {'address': 'mrFNfhs1qhKXGq1FZ8qNm241fQPiNWEDMw', 'value': 20.0, 'ismine': True}],
         'totalinputs': 938.8997,
         'txid': 'fe6ce1af081dae060a123608140201cfffa04ea61ffaf96e2caca2a05bd8f9c0',
      })
      result = self.jsonServer.jsonrpc_gettransaction("0101")
      self.assertEqual(result["Error Type"], "InvalidTransaction")
      # TODO: more types of transactions: toself, send, receive
      # TODO: add a coinbase transaction


   def testGetTxOut(self):
      txOut = self.jsonServer.jsonrpc_gettxout(TX, 0)
      self.assertEquals(txOut['value'],TX_OUTS[0])
      txOut = self.jsonServer.jsonrpc_gettxout(TX, 1)
      self.assertEquals(txOut['value'],TX_OUTS[1])
      result = self.jsonServer.jsonrpc_gettxout(TX, 5)
      self.assertEquals(result['Error Type'], 'InvalidRequest')
      result = self.jsonServer.jsonrpc_gettxout('abcd', 5)
      self.assertEquals(result['Error Type'], 'InvalidTransaction')


   def testGetWalletInfo(self):
      # also tests: setwalletinfo
      testName = "some weird wallet name"
      testDesc = "some looooooooooooooooooooooooooong wallet description"
      wltInfo = self.jsonServer.jsonrpc_setwalletinfo(
         FIRST_WLT_NAME, testName, testDesc)
      wltInfo = self.jsonServer.jsonrpc_getwalletinfo(FIRST_WLT_NAME)
      self.assertEqual(wltInfo['balance'], FIRST_WLT_BALANCE)
      e = self.wltA.external.getChildIndex()
      i = self.wltB.internal.getChildIndex()
      self.assertEqual(wltInfo['numaddrgen'], e+i)
      self.assertEqual(wltInfo['externaladdrgen'], e)
      self.assertEqual(wltInfo['internaladdrgen'], i)
      self.assertEqual(wltInfo['islocked'], True)
      self.assertEqual(wltInfo['name'], testName)
      self.assertEqual(wltInfo['description'], testDesc)
      self.assertEqual(wltInfo['xpub'], FIRST_WLT_XPUB)

      result = self.jsonServer.jsonrpc_getwalletinfo('nonsense')
      self.assertEqual(result['Error Type'], 'WalletDoesNotExist')


   def testHelp(self):
      createFuncDict()
      result = self.jsonServer.jsonrpc_help()
      self.assertEqual(result["help"]["Description"], "Get a directionary with all functions the armoryd server can run.")


   # TODO Try more types of priv keys
   def testImportPrivKey(self):
      # unlock first
      self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE1)
      key = binary_to_hex(self.privKey.toBinStr())
      result = self.jsonServer.jsonrpc_importprivkey(key)
      self.assertEqual(result["PubKey"], "mh5rx2637FQWDkr7YuHkfWK1XS7WqziQJp")
      # trying a second time should show an error
      result = self.jsonServer.jsonrpc_importprivkey(key)
      self.assertEqual(result["Error Type"], "InvalidRequest")
      result = self.jsonServer.jsonrpc_importprivkey('nonsense')
      self.assertEqual(result['Error Type'], 'BadAddressError')
      # trying to import an address in the wallet already should show an error
      firstAddr = self.wltA.getNextReceivingAddress()
      self.privKey = firstAddr.getPlainPrivKeyCopy().toBinStr() + "\x01"
      pkeyB58 = privKey_to_base58(self.privKey)
      result = self.jsonServer.jsonrpc_importprivkey(pkeyB58)
      self.assertEqual(result['Error Type'], 'InvalidRequest')


   def testImportWatchOnly(self):
      result = self.jsonServer.jsonrpc_importwatchonly(TEST_XPUB)
      self.assertEqual(result, TEST_XPUB_ID)
      result = self.jsonServer.jsonrpc_getactivewallet()
      self.assertEqual(result, TEST_XPUB_ID)
      result = self.jsonServer.jsonrpc_importwatchonly(FIRST_WLT_XPUB)
      self.assertEqual(result['Error Type'], 'WalletExistsError')

      # Verify that adding a passphrase to a watch-only wallet raises
      # an error
      result = self.jsonServer.jsonrpc_encryptwalletfile('',
                                                         PASSPHRASE2)
      self.assertEqual(result.get('Error Type'), 'WalletUpdateError')


   def testListAddresses(self):
      result = self.jsonServer.jsonrpc_listaddresses(FIRST_WLT_NAME)
      self.assertEqual(result["external"][0], TEST_ADDRESS)
      self.assertEqual(result["internal"][0], TEST_ADDRESS2)
      result = self.jsonServer.jsonrpc_listaddresses('nonsense')
      self.assertEqual(result['Error Type'], 'WalletDoesNotExist')


   def testListAddrUnspent(self):
      addrs = ','.join([FIRST_WLT_ADDR2, FIRST_LOCKBOX_ADDRESS])
      result = self.jsonServer.jsonrpc_listaddrunspent(addrs)

      self.assertEqual(result['addrbalance'][FIRST_WLT_ADDR2],
                       FIRST_WLT_ADDR2_BAL)
      self.assertEqual(result['addrbalance'][FIRST_LOCKBOX_ADDRESS],
                       FIRST_LOCKBOX_BALANCE)
      self.assertEqual(result['totalbalance'],
                       FIRST_WLT_ADDR2_BAL + FIRST_LOCKBOX_BALANCE)
      self.assertEqual(result['numutxo'], 4)
      self.assertEqual(result['utxolist'][-1]['address'], FIRST_LOCKBOX_ADDRESS)
      result = self.jsonServer.jsonrpc_listaddrunspent(RANDOM_P2SH_ADDR)
      self.assertEqual(result['Error Type'], 'BitcoindError')


   def testListLoadedLockboxes(self):
      result = self.jsonServer.jsonrpc_listloadedlockboxes()
      self.assertEqual(len(result.keys()), 2)
      self.assertTrue(FIRST_LOCKBOX_NAME in result.values())
      self.assertTrue(SECOND_LOCKBOX_NAME in result.values())


   def testListLoadedWallets(self):
      result = self.jsonServer.jsonrpc_listloadedwallets()
      self.assertEqual(len(result.keys()), 4)
      self.assertTrue(FIRST_WLT_NAME in result.values())
      self.assertTrue(SECOND_WLT_NAME in result.values())
      self.assertTrue(THIRD_WLT_NAME in result.values())


   def testListTransactions(self):
      # also tests gethistorypagecount

      #takes a history page count now, not an amount of transactions to return
      num = self.jsonServer.jsonrpc_gethistorypagecount()

      for page in range(num):
         txList = self.jsonServer.jsonrpc_listtransactions(page)
         self.assertTrue(len(txList) > 0)
         for tx in txList:
            if tx['blockhash'] == '00000000e49ff04fd80d82d434230eca23f259434ad19323d688a70ccc3e6255':
               self.assertEqual(tx, {'blockhash': '00000000e49ff04fd80d82d434230eca23f259434ad19323d688a70ccc3e6255', 'blockindex': 1L, 'confirmations': TOP_TIAB_BLOCK - 247, 'address': 'mrFNfhs1qhKXGq1FZ8qNm241fQPiNWEDMw', 'category': 'receive', 'account': '', 'txid': 'fe6ce1af081dae060a123608140201cfffa04ea61ffaf96e2caca2a05bd8f9c0', 'blocktime': 1431493892, 'amount': 20.0, 'timereceived': 1431493892, 'time': 1431493892})
      # TODO: test the various ways the BDM can fail
      # TODO: try a tx that's to yourself
      # TODO: try a tx that's outgoing
      # TODO: try a coinbase tx with exactly 1 output


   def testListUnspent(self):
      result = self.jsonServer.jsonrpc_listunspent()

      tx1Found = False
      for i in range(len(result)):
         if result[i]['txid'] == \
            '0f341c4279e4e197d36f0328d2a26f7eee593dd71c660881364ff59357ea8c53':
            self.assertEqual(result[i]['amount'], 3.0)
            self.assertEqual(result[i]['confirmations'], TOP_TIAB_BLOCK - 249)
            self.assertEqual(result[i]['priority'], 3.0)
            tx1Found = True
      self.assertTrue(tx1Found)


   def testSetActiveLockbox(self):
      # see testGetActiveLockbox
      pass


   def testSetActiveWallet(self):
      # see testGetActiveWallet
      pass


   def testSetLockboxInfo(self):
      # see testGetLockboxInfo
      pass


   def testSetWalletInfo(self):
      # see testGetWalletInfo
      pass


   def testSignAsciiTransaction(self):
      # see testCreateUSTX*
      pass


   def testSignMessage(self):
      # unlock first
      self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE1)
      result = self.jsonServer.jsonrpc_signmessage(TEST_ADDRESS, TEST_MESSAGE)
      self.assertEqual(result[:10], "-----BEGIN")
      inp = '"%s"' % result
      result = self.jsonServer.jsonrpc_verifysignature(TEST_ADDRESS, inp)
      self.assertEqual(result.get("message"), TEST_MESSAGE)
      result = self.jsonServer.jsonrpc_signmessage('1abc', TEST_MESSAGE)
      self.assertEqual(result['Error Type'], 'BadAddressError')


   def testVerifySignature(self):
      # unlock first
      self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE1)
      addrObj = self.wltA.getAddress(addrStr_to_scrAddr(FIRST_WLT_ADDR1))
      clearSignMessage = addrObj.clearSignMessage(TEST_MESSAGE)
      inMsg = '\"' + clearSignMessage + '\"'
      result = self.jsonServer.jsonrpc_verifysignature(inMsg)
      self.assertEqual(result['message'], TEST_MESSAGE)
      self.assertEqual(result['address'], FIRST_WLT_ADDR1)


   def testWalletLock(self):
      # see testWalletPassphrase
      pass


   def testWalletPassphrase(self):
      self.jsonServer.jsonrpc_walletlock()
      self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE1, UNLOCK_TIMEOUT)
      self.assertFalse(self.wltA.isLocked())
      time.sleep(UNLOCK_TIMEOUT+2)
      self.wltA.checkLockTimeout()
      self.assertTrue(self.wltA.isLocked())
      result = self.jsonServer.jsonrpc_walletpassphrase(PASSPHRASE2, 1)
      self.assertTrue("failed" in result)



# runs a Test In a Box (TIAB) bitcoind session. By copying a prebuilt
# testnet with a known state
# Charles's recommendation is that you keep the TIAB somewhere like ~/.armory/tiab.charles
# and export that path in your .bashrc as ARMORY_TIAB_PATH
class ArmoryDSession:
   numInstances=0

   # create a Test In a Box, initializing it and filling it with data
   # the data comes from a path in the environment unless tiabdatadir is set
   # tiab_repository is used to name which flavor of box is used if
   # tiabdatadir is not used - It is intended to be used for when we
   # have multiple testnets in a box with different properties
   def __init__(self, tiab, armoryHomeDir):
      self.processes = []
      self.armoryHomeDir = armoryHomeDir
      self.running = False
      self.tiab = tiab
      if os.path.exists('armoryd.py'):
         self.armorydPath = 'armoryd.py'
      else:
         self.armorydPath = os.path.join('..', 'armoryd.py')
      if os.path.exists('armory-cli.py'):
         self.armorycliPath = 'armory-cli.py'
      else:
         self.armorycliPath = os.path.join('..', 'armory-cli.py')
      self.restart()


   def __del__(self):
      self.clean()


   # exit bitcoind and remove all data
   def clean(self):
      if not self.running:
         return
      ArmoryDSession.numInstances -= 1
      for x in self.processes:
         if x.returncode is None:
            self.callArmoryRPC(["stop"])
      for x in self.processes:
         x.wait()
      self.processes = []
      self.running=False


   def startArmoryD(self, additionalArgs):
      args = ['python', self.armorydPath,
              '--testnet',
              '--datadir=' + self.armoryHomeDir,
              '--satoshi-datadir=' + os.path.join(self.tiab.tiabDirectory, 'tiab', '1'),
              '--satoshi-port=' + str(TIAB_SATOSHI_PORT),
              '--skip-online-check',
              '--supernode']
      # if this is process is in debug mode, make the subrocess debug too
      if getDebugFlag():
         args.append('--debug')

      args.extend(additionalArgs)

      # If we are not waiting output, e.g. when starting ArmoryD, return the started process.
      startedProcess = subprocess.Popen(args)
      self.processes.append(startedProcess)
      return startedProcess


   # clean() and then start bitcoind again
   def callArmoryRPC(self, additionalArgs):
      args = ['python', self.armorycliPath,
              '--testnet',
              '--supernode',
              '--datadir=' + self.armoryHomeDir,
              '--satoshi-datadir=' + os.path.join(self.tiab.tiabDirectory, 'tiab', '1'),
              '--satoshi-port=' + str(TIAB_SATOSHI_PORT),
              '--skip-online-check',
           ]
            # if this is process is in debug mode, make the subrocess debug too
      if getDebugFlag():
         args.append('--debug')

      args.extend(additionalArgs)

      # We're expecting some json to come back, that means there should
      # already be a daemon running
      if not ArmoryDaemon.checkForAlreadyRunning():
         raise RuntimeError("armoryd isn't running")

      # If there is output coming back convert it from a string to a dictionary
      return subprocess.check_output(args)


   def restart(self):
      self.clean()
      if ArmoryDSession.numInstances != 0:
         raise RuntimeError(
            "Cannot have more than one ArmoryD session simultaneously %s"
            % ArmoryDSession.numInstances)

      try:
         self.startArmoryD([os.path.join(self.armoryHomeDir,FIRST_WLT_FILE_NAME)])
         ArmoryDSession.numInstances += 1
         # Wait for ArmoryDaemon to start running
         i = 0
         while not ArmoryDaemon.checkForAlreadyRunning() and i < 10:
            time.sleep(1)
            i += 1
         if i >= 10:
            raise RuntimeError("ArmoryD session not running")

      except:
         self.clean()
         raise
      self.running = True



class ServerTest(TiabTest):
   """
   These are tests that need the actual armoryd server to be running.
   We start armoryd directly and call everything via RPC.
   """


   def setUp(self):
      useTestnet()
      self.armoryDSession = ArmoryDSession(self.tiab, self.armoryHomeDir)
      time.sleep(1)


   def tearDown(self):
      self.armoryDSession.clean()


   def testGetWalletInfo(self):
      self.armoryDSession.callArmoryRPC(['setactivewallet', FIRST_WLT_NAME])
      result = json.loads(self.armoryDSession.callArmoryRPC(['getarmorydinfo']))
      self.assertEqual(result['balance'], FIRST_WLT_BALANCE)
      self.assertEqual(result['bdmstate'], BDM_BLOCKCHAIN_READY)
      self.assertEqual(result['blocks'], TOP_TIAB_BLOCK)
      self.assertEqual(result['difficulty'], 1.0)
      self.assertEqual(result['testnet'], True)


   def testSetActiveWallet(self):
      self.armoryDSession.callArmoryRPC(['setactivewallet', FIRST_WLT_NAME])
      wltDictionary = json.loads(self.armoryDSession.callArmoryRPC(['listloadedwallets']))
      self.assertTrue(len(wltDictionary), 3)
      result = json.loads(self.armoryDSession.callArmoryRPC(['getwalletinfo']))
      self.assertEqual(result['walletid'], FIRST_WLT_NAME)
      setWltResult = self.armoryDSession.callArmoryRPC(['setactivewallet', THIRD_WLT_NAME])
      self.assertTrue(setWltResult.index(THIRD_WLT_NAME) > 0)
      result2 = json.loads(self.armoryDSession.callArmoryRPC(['getwalletinfo']))
      self.assertEqual(result2['walletid'], THIRD_WLT_NAME)


   def testSendAsciiTransaction(self):
      amount1 = 0.2
      amount2 = 0.3
      args = ['createlockboxustxformany', '0.001',
              "%s,%s" % (TEST_ADDRESS, str(amount1)),
              "%s,%s" % (TEST_ADDRESS2, str(amount2)),
              ]
      serializedUnsignedTx0 = self.armoryDSession.callArmoryRPC(args)
      self.assertFalse('Error Type' in serializedUnsignedTx0)

      # sign with one key
      f = open(TX_FILENAME, b'wb')
      f.write(serializedUnsignedTx0)
      f.close()
      args = ['setactivewallet', FIRST_WLT_NAME]
      self.armoryDSession.callArmoryRPC(args)
      args = ['walletpassphrase', PASSPHRASE1]
      self.armoryDSession.callArmoryRPC(args)
      args = ['signasciitransaction',TX_FILENAME]
      serializedSignedTx1 = self.armoryDSession.callArmoryRPC(args)

      # sign with the other key
      f = open(TX_FILENAME, b'wb')
      f.write(serializedSignedTx1)
      f.close()
      args = ['setactivewallet', SECOND_WLT_NAME]
      self.armoryDSession.callArmoryRPC(args)
      args = ['walletpassphrase', PASSPHRASE3]
      self.armoryDSession.callArmoryRPC(args)
      args = ['signasciitransaction', TX_FILENAME]
      serializedSignedTx2 = self.armoryDSession.callArmoryRPC(args)

      f = open(TX_FILENAME, b'wb')
      f.write(serializedSignedTx2)
      f.close()
      args = ['sendasciitransaction', TX_FILENAME]
      txhash = self.armoryDSession.callArmoryRPC(args)
      self.assertEqual(len(txhash.strip()), 64)


   def testStop(self):
      result = self.armoryDSession.callArmoryRPC(['stop'])
      proc = self.armoryDSession.processes[0]
      proc.wait()
      self.assertEqual(proc.returncode, 0)


class EmailTest(TiabTest):
   """
   These are tests that need the actual armoryd and a fake smtp server
   to be running. We start armoryd directly and call everything via RPC.
   We check the results of the email by reading the email file.
   """

   EMAIL_FILE = 'email.tmp'

   def setUp(self):
      useTestnet()

      removeIfExists(self.EMAIL_FILE)
      self.armoryDSession = ArmoryDSession(self.tiab, self.armoryHomeDir)
      smtp = ''
      if os.path.isfile('testArmoryD.py'):
         smtp = os.path.join('..', 'pytest', 'mockSMTP.py')
      elif os.path.isdir('pytest'):
         smtp = os.path.join('pytest', 'mockSMTP.py')
      else:
         raise RuntimeError("cannot find mock SMTP server")
      self.smtpd = subprocess.Popen(["python", smtp])
      self.email_from = "sender@nowhere.none"
      self.email_to = "receiver@nowhere.none"
      self.subject = "test email!"
      self.server = "127.0.0.1:1025"
      self.pwd = ' '
      time.sleep(1)


   def tearDown(self):
      if self.smtpd.returncode is None:
         self.smtpd.kill()
         self.smtpd.wait()
      removeIfExists(self.EMAIL_FILE)
      self.armoryDSession.clean()


   def getEmail(self):
      f = open(self.EMAIL_FILE, 'r')
      data = f.read()
      f.close()
      return data


   def testSendLockbox(self):
      args = ['sendlockbox', FIRST_LOCKBOX_NAME, self.email_from,
               self.server, self.pwd, self.email_to, self.subject, "1"]
      result = self.armoryDSession.callArmoryRPC(args)
      self.assertEqual(result.strip(), 'sendlockbox command succeeded.')
      self.smtpd.terminate()
      self.smtpd.wait()
      email = self.getEmail()
      self.assertTrue(FIRST_LOCKBOX_NAME in email)
      self.assertTrue("From: %s" % self.email_from in email)
      self.assertTrue("To: %s" % self.email_to in email)
      self.assertTrue("Subject: %s" % self.subject in email)


   def testWatchWallet(self):
      args = ['setactivewallet', FIRST_WLT_NAME]
      self.armoryDSession.callArmoryRPC(args)

      # add some metadata, this should show up in the email
      mStr = "noteasilyfoundinthisthing"
      metadata = {FIRST_WLT_ADDR2:{"testmetadata": mStr}}
      args = ['setaddressmetadata', json.dumps(metadata)]
      self.armoryDSession.callArmoryRPC(args)
      args = ['getaddressmetadata']

      args = ['watchwallet', self.email_from, self.server, self.pwd,
              self.email_to, self.subject, "add", "1"]
      result = self.armoryDSession.callArmoryRPC(args)
      self.assertEqual(result.strip(), 'watchwallet command succeeded.')

      # trigger an email by submitting the next block which has 
      # a transaction from FIRST_WLT_ADDR2
      self.submitNextBlock()

      time.sleep(3)

      self.smtpd.terminate()
      self.smtpd.wait()
      self.assertTrue(os.path.isfile(self.EMAIL_FILE))
      email = self.getEmail()
      self.assertTrue("From: %s" % self.email_from in email)
      self.assertTrue("To: %s" % self.email_to in email)
      self.assertTrue("Subject: %s" % self.subject in email)
      self.assertTrue(mStr in email)


