################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

import sys
sys.path.append('..')
import tempfile
import unittest

from armoryengine.ALL import *
from armoryengine.BitSet import BitSet
from armoryengine.WalletLabels import *
from BIP32TestVectors import *
sys.argv = sys.argv[:-2]

WALLET_VERSION_BIN = hex_to_binary('002d3101')

# This disables RSEC for all WalletEntry objects.  This causes it to stop
# checking RSEC codes on all entries, and writes all \x00 bytes when creating.
WalletEntry.DisableRSEC()


MSO_FILECODE   = 'MOCKOBJ_'
MSO_ENTRY_ID   = '\x01'+'\x33'*20
MSO_FLAGS_REG  = '\x00\x00'
MSO_FLAGS_DEL  = '\x80\x00'
MSO_PARSCRADDR = '\x05'+'\x11'*20
MSO_PAYLOAD    = '\xaf'*5

FAKE_KDF_ID  = '\x42'*8
FAKE_EKEY_ID = '\x9e'*8


################################################################################
class MockSerializableObject(WalletEntry):
   FILECODE = MSO_FILECODE

   def __init__(self, txt=None):
      super(MockSerializableObject, self).__init__()
      self.setText(txt)

   def setText(self, txt):
      self.text = '' if txt is None else txt

   def getEntryID(self):
      return MSO_ENTRY_ID

   def serialize(self):
      bp = BinaryPacker()
      bp.put(VAR_STR, self.text)
      return bp.getBinaryString()

   def unserialize(self, toUnpack):
      bu = makeBinaryUnpacker(toUnpack) 
      self.text = bu.get(VAR_STR)
      return self
      

################################################################################
def skipFlagExists():
   if os.path.exists('skipmosttests.flag'):
      print '*'*80
      print 'SKIPPING MOST TESTS.  REMOVE skipMostTests.flag TO REENABLE'
      print '*'*80
      return True
   else:
      return False


#############################################################################
def compareWalletObjs(tself, wlt1, wlt2):
   
   def cmpLen(a,b,prop):
      if hasattr(a, prop) and hasattr(b, prop):
         tself.assertEqual(len(getattr(a, prop)), len(getattr(b, prop)))


   cmpLen(wlt1, wlt2, 'allWalletEntries')
   cmpLen(wlt1, wlt2, 'displayableWalletsMap')
   cmpLen(wlt1, wlt2, 'topLevelRoots')
   cmpLen(wlt1, wlt2, 'lockboxMap')
   cmpLen(wlt1, wlt2, 'ekeyMap')
   cmpLen(wlt1, wlt2, 'kdfMap')
   cmpLen(wlt1, wlt2, 'masterScrAddrMap')
   cmpLen(wlt1, wlt2, 'opaqueList')
   cmpLen(wlt1, wlt2, 'unrecognizedList')
   cmpLen(wlt1, wlt2, 'unrecoverableList')
   cmpLen(wlt1, wlt2, 'wltParentMissing')
   cmpLen(wlt1, wlt2, 'disabledRootIDs')
   cmpLen(wlt1, wlt2, 'disabledList')
   tself.assertEqual(wlt1.arbitraryDataMap.countNodes(), 
                     wlt2.arbitraryDataMap.countNodes())

   def cmpMapKeys(a,b,prop):
      tself.assertTrue(hasattr(a, prop) and hasattr(b, prop))
      mapA = getattr(a, prop)
      mapB = getattr(b, prop)
      if not isinstance(mapA, dict) or not isinstance(mapB, dict):
         raise KeyError('Supplied property is not a map: %s' % prop)
      for key in mapA:
         tself.assertTrue(key in mapB)
      for key in mapB:
         tself.assertTrue(key in mapA)

   cmpMapKeys(wlt1, wlt2, 'displayableWalletsMap')
   cmpMapKeys(wlt1, wlt2, 'lockboxMap')
   cmpMapKeys(wlt1, wlt2, 'ekeyMap')
   cmpMapKeys(wlt1, wlt2, 'kdfMap')
   cmpMapKeys(wlt1, wlt2, 'masterScrAddrMap')
      
   def cmpprop(a,b,prop):
      if hasattr(a, prop) and hasattr(b, prop):
         tself.assertEqual(getattr(a, prop), getattr(b, prop))

   cmpprop(wlt1.fileHeader, wlt2.fileHeader, 'wltUserName')
   cmpprop(wlt1.fileHeader, wlt2.fileHeader, 'createTime')
   cmpprop(wlt1.fileHeader, wlt2.fileHeader, 'createBlock')
   cmpprop(wlt1.fileHeader, wlt2.fileHeader, 'rsecParity')
   cmpprop(wlt1.fileHeader, wlt2.fileHeader, 'rsecPerData')
   cmpprop(wlt1.fileHeader, wlt2.fileHeader, 'isDisabled')
   cmpprop(wlt1.fileHeader, wlt2.fileHeader, 'headerSize')
   cmpprop(wlt1.fileHeader, wlt2.fileHeader, 'isTransferWallet')
   cmpprop(wlt1.fileHeader, wlt2.fileHeader, 'isSupplemental')



#############################################################################
def writeReadWalletRoundTripTest(tself, wlt):
   wltDir = 'tempwallets'
   if not os.path.exists(wltDir):
      os.makedirs(wltDir)

   tstr = str(time.time())
   fnameA = os.path.join(wltDir, 'testWltRW_%s_A.wallet' % tstr)
   fnameB = os.path.join(wltDir, 'testWltRW_%s_B.wallet' % tstr)
   fnameC = os.path.join(wltDir, 'testWltRW_%s_C.wallet' % tstr)

   testWlt = wlt
   for f in [fnameA, fnameB, fnameC]:
      if os.path.exists(f):
         raise FileExistsError('Temporary wallet file already exists')
      

      try:
         testWlt.writeFreshWalletFile(f)
         wlt2 = ArmoryWalletFile.ReadWalletFile(f)
         compareWalletObjs(tself, wlt, wlt2)
         testWlt = wlt2
      finally:
         for f in [fnameA, fnameB, fnameC]:
            removeIfExists(f)
            break
            

################################################################################
class ArmoryFileHeaderTests(unittest.TestCase):

   #############################################################################
   def setUp(self):
      setDebugFlag(False)
      useMainnet()

   #############################################################################
   def tearDown(self):
      pass
      

   #############################################################################
   def roundTripTest(self, afh):
      afhSer  = afh.serialize()
      afh2    = ArmoryFileHeader.Unserialize(afhSer)
      afhSer2 = afh2.serialize()
      afh3    = ArmoryFileHeader.Unserialize(afhSer2)
      self.assertEqual(afhSer, afhSer2)
      
      self.cmp2afh(afh, afh3)

   #############################################################################
   def cmp2afh(self, afh1, afh2):
      def cmp(prop):
         self.assertEqual(getattr(afh1, prop), getattr(afh2, prop))

      cmp('wltUserName')
      cmp('createTime')
      cmp('createBlock')
      cmp('rsecParity')
      cmp('rsecPerData')
      cmp('isDisabled')
      cmp('headerSize')
      cmp('isTransferWallet')
      cmp('isSupplemental')


   #############################################################################
   @unittest.skip('')
   def test_CreateAFH(self):
      
      afh = ArmoryFileHeader()
      
      afh.isTransferWallet = False
      afh.isSupplemental = False
      afh.createTime  = long(1.4e9)
      afh.createBlock = 320000
      afh.wltUserName = u''
      afh.rsecParity  = RSEC_PARITY_BYTES
      afh.rsecPerData = RSEC_PER_DATA_BYTES
      afh.isDisabled  = False
      afh.headerSize  = ArmoryFileHeader.DEFAULTSIZE

      self.roundTripTest(afh)


      fl = BitSet(32)
      fl.setBit(0, False)
      fl.setBit(1, False)
      afh2 = ArmoryFileHeader()
      afh2.initialize(u'', long(1.4e9), 320000, fl)

      self.cmp2afh(afh, afh2)
      self.roundTripTest(afh)


      fl = BitSet(32)
      fl.setBit(0, True)
      fl.setBit(1, True)
      afh3 = ArmoryFileHeader()
      self.assertRaises(UnserializeError, afh3.initialize, u'Armory Wallet Test\u2122', 0, 0, fl)

      fl = BitSet(32)
      fl.setBit(0, False)
      fl.setBit(1, False)
      afh3 = ArmoryFileHeader()
      afh3.initialize(u'Armory Wallet Test\u2122', 0, 0, fl)

      fl = BitSet(32)
      fl.setBit(0, False)
      fl.setBit(1, False)
      afh4 = ArmoryFileHeader()
      afh4.initialize(u'', 0, 0, fl)

      self.assertEqual( afh3.serialize(), 
                        afh4.serialize(altName=u'Armory Wallet Test\u2122'))


   #############################################################################
   def test_MagicFail(self):
      fl = BitSet(32)
      fl.setBit(0, False)
      fl.setBit(1, False)
      afh = ArmoryFileHeader()
      afh.initialize(u'Armory Wallet Test\u2122', long(1.4e9), 320000, fl)

      mgcC = '\xffARMORY\xff'
      mgcW = '\xbaWALLET\x00'
      afhSer1 = afh.serialize()
      afhSer2 = mgcW + afhSer1[8:]
      afhSer3 = '\x00'*8 + afhSer1[8:]
      self.assertRaises(FileExistsError, ArmoryFileHeader.Unserialize, afhSer2)
      self.assertRaises(FileExistsError, ArmoryFileHeader.Unserialize, afhSer3)

      afhSer4 = afhSer1[:16] + '\x0b\x11\x09\x07' + afhSer1[20:]
      self.assertRaises(NetworkIDError, ArmoryFileHeader.Unserialize, afhSer4)

      

################################################################################
class SimpleWalletTests(unittest.TestCase):

   #############################################################################
   def setUp(self):
      useMainnet()
      setDebugFlag(False)
      self.tmpdir = tempfile.mkdtemp("armory_wallet")
      setArmoryHomeDir(self.tmpdir)

      self.wltDir = 'tempwallets'
      self.wltFN = 'test_wallet_file.wallet'

      if not os.path.exists(self.wltDir):
         os.makedirs(self.wltDir)

      self.clearWallets()

      self.pwd = SecureBinaryData('T3ST1NG_P455W0RD')
      self.seed = SecureBinaryData('\xaa'*32) 
      self.wltName = u'Test wallet\u2122'
   
      
   #############################################################################
   def tearDown(self):
      self.clearWallets()
      shutil.rmtree(self.tmpdir)

   #############################################################################
   def clearWallets(self):
      flist = []
      flist.append(self.wltDir + '/test_wallet_file.wallet')
      flist.append(self.wltDir + '/test_wallet_file_backup.wallet')
      flist.append(self.wltDir + '/test_wallet_file_update_unsuccessful.wallet')
      flist.append(self.wltDir + '/test_wallet_file_backup_unsuccessful.wallet')
      for f in flist:
         removeIfExists(f)

   #############################################################################
   def getProgressFunc(self):
      lastChk = [0]
      def prgUpdate(curr, tot):
         if float(curr)/float(tot) > lastChk+0.05:
            sys.stdout.write('.')
            lastChk += 0.05
      
   #############################################################################
   def testCreateAndReadWallet_BIP32TestVects(self):

      self.clearWallets()

      pwd = SecureBinaryData('T3ST1NG_P455W0RD')
      seed = SecureBinaryData(hex_to_binary('000102030405060708090a0b0c0d0e0f'))
      wltName = u'Test wallet\u2122'
   
      newWallet = ArmoryWalletFile.CreateWalletFile_SinglePwd(
         wltName, pwd, BIP32_TESTVECT_0, None, seed, createInDir=self.wltDir,
         specificFilename=self.wltFN, Progress=self.getProgressFunc())

      self.assertEqual(len(newWallet.topLevelRoots), 1)

      akp = newWallet.topLevelRoots[0]
      for i in range(6):
         self.assertEqual(BIP32TestVectors[i]['seedCompPubKey'].toBinStr(),
                          akp.sbdPublicKey33.toBinStr())

         self.assertEqual(BIP32TestVectors[i]['seedCC'].toBinStr(),
                          akp.sbdChaincode.toBinStr())

         # There should only be one in the map, but we don't know the ID
         for i,child in akp.akpChildByIndex.iteritems():
            akp = child
            break
         

   #############################################################################
   def testArbWltData(self):

      pwd2 = SecureBinaryData('AWDPWD')
      awdACI,awdEkey = ArmoryWalletFile.generateNewSinglePwdMasterEKey(pwd2)

      newWallet = ArmoryWalletFile.CreateWalletFile_SinglePwd(
         self.wltName, self.pwd, ABEK_BIP44Seed, None, self.seed,
         createInDir=self.wltDir, specificFilename=self.wltFN,
         Progress=emptyFunc)

      newWallet.addCryptObjsToWallet(awdEkey)
      awdEkeyID = awdEkey.getEncryptionKeyID()

      msgPlain1 = 'plain ole text'
      msgPlain2 = 'more plain text'
      msgCrypt = SecureBinaryData('super secret!')

      print 'topNode:'
      topAKP = newWallet.topLevelRoots[0]
      topAKP.pprintOneLine()
      newWallet.addArbitraryWalletData(topAKP, ['Message'], msgPlain1)
      newWallet.addArbitraryWalletData(topAKP, ['Message', 'PL41N'], msgPlain2)

      newWallet.unlockWalletEkey(awdEkeyID, pwd2)

      self.assertRaises(KeyError, newWallet.addArbitraryWalletData_Encrypted,
                        topAKP, ['Message'], msgCrypt, awdEkeyID)
      newWallet.addArbitraryWalletData_Encrypted(
         topAKP, ['Message','Encrypted'], msgCrypt, awdEkeyID)

      newWallet.forceLockWalletEkey(awdEkeyID)
      self.assertEqual(newWallet.getArbitraryWalletData(['Message']), msgPlain1)
      self.assertEqual(newWallet.getArbitraryWalletData(['Message', 'PL41N']), msgPlain2)

      self.assertRaises(WalletLockError, newWallet.getArbitraryWalletData, ['Message', 'Encrypted'])
      newWallet.unlockWalletEkey(awdEkeyID, pwd2)
      self.assertEqual(newWallet.getArbitraryWalletData(['Message', 'Encrypted']), msgCrypt)

      #newWallet.pprintEntryList()
      print 'Printing to CSV:  pprintSimple.csv'
      newWallet.pprintToCSV_Simple('pprintSimple.csv')
      print 'Printing to CSV:  pprintColumns.csv'
      newWallet.pprintToCSV_Columns('pprintColumns.csv')

      writeReadWalletRoundTripTest(self, newWallet)

   #############################################################################
   def testCreateAndReadWallet_UpdateChangeSize(self):
      # TODO
      pass

   #############################################################################
   def testWalletLabels(self):
      scrAddr = script_to_scrAddr(pubkey_to_p2pk_script('\x03' + '\xaa' * 32))
      saLbl = ScrAddrLabel()
      saLbl.initialize(scrAddr, 'Deposit Label')

   #############################################################################
   def testCreateAndReadWallet_DeleteData(self):

      self.clearWallets()
      pwd = SecureBinaryData('T3ST1NG_P455W0RD')
      seed = SecureBinaryData('\xaa'*32) 
      wltName = u'Test wallet\u2122'
   
      newWallet = ArmoryWalletFile.CreateWalletFile_SinglePwd(
         wltName, pwd, ABEK_BIP44Seed, None, seed, createInDir=self.wltDir,
         specificFilename=self.wltFN, Progress=self.getProgressFunc())



   #############################################################################
   def testCreateAndReadWallet_PregenSeed(self):

      self.clearWallets()
      pwd = SecureBinaryData('T3ST1NG_P455W0RD')
      seed = SecureBinaryData('\xaa'*32) 
      wltName = u'Test wallet\u2122'
   
      newWallet = ArmoryWalletFile.CreateWalletFile_SinglePwd(
         wltName, pwd, ABEK_BIP44Seed, None, seed, createInDir=self.wltDir,
         specificFilename=self.wltFN, Progress=self.getProgressFunc())

      # Pass 0: check the already-created wallet
      # Pass 1: re-read the wallet from file and check
      # Pass 2: re-read the wallet from file in read-only mode 
      for i in range(3):
         wpath = os.path.join(self.wltDir, self.wltFN)
         self.assertTrue(os.path.exists(wpath))
         self.assertEqual(wltName, newWallet.fileHeader.wltUserName)
         self.assertEqual(113, len(newWallet.allWalletEntries))
         self.assertEqual(111, len(newWallet.masterScrAddrMap))
         self.assertEqual(1,  len(newWallet.displayableWalletsMap))
         self.assertEqual(1,  len(newWallet.ekeyMap))
         self.assertEqual(1,  len(newWallet.kdfMap))
         self.assertEqual(0 , len(newWallet.opaqueList))
         self.assertEqual(0 , len(newWallet.unrecognizedList))
         self.assertEqual(0 , len(newWallet.unrecoverableList))
         self.assertEqual(0 , newWallet.arbitraryDataMap.countNodes())
         self.assertEqual(0 , len(newWallet.disabledRootIDs))
         self.assertEqual(0 , len(newWallet.disabledList))
         self.assertEqual(None, newWallet.masterWalletRef)
         self.assertEqual(None, newWallet.supplementalWltRef)
         self.assertEqual(None, newWallet.supplementalWltPath)
         self.assertEqual(newWallet.isReadOnly, (i==2))

         for scrAddr,akpDisp in newWallet.displayableWalletsMap.iteritems():
            self.assertEqual(akpDisp.__class__.__name__, 'ABEK_StdWallet')
            self.assertTrue(akpDisp.getChildIndex() is not None)
            akpDisp.pprintOneLine(indent=3)


         newWallet = ArmoryWalletFile.ReadWalletFile(wpath, openReadOnly=(i>0))

       
      # Wallet should be open in RO mode, so updating should fail
      self.assertRaises(WalletUpdateError, newWallet.addFileOperationToQueue,
                                                'AddEntry', EncryptionKey())


      newWallet.pprintEntryList()


   #############################################################################
   def testPregenSeed_Unlock(self):

      self.clearWallets()
      pwd = SecureBinaryData('T3ST1NG_P455W0RD')
      seed = SecureBinaryData('\xaa'*32) 
      wltName = u'Test wallet\u2122'
   
      newWallet = ArmoryWalletFile.CreateWalletFile_SinglePwd(
         wltName, pwd, ABEK_BIP44Seed, None, seed, createInDir=self.wltDir,
         specificFilename=self.wltFN, Progress=self.getProgressFunc())


      self.assertEqual(1, len(newWallet.ekeyMap))
      self.assertEqual(1, len(newWallet.kdfMap))
      
      self.assertTrue(newWallet.getOnlyEkey().isLocked())
      newWallet.unlockWalletEkey(newWallet.getOnlyEkeyID(), pwd)
      self.assertFalse(newWallet.getOnlyEkey().isLocked())


################################################################################
class UnencryptedWalletTests(unittest.TestCase):

   #############################################################################
   def setUp(self):
      useMainnet()
      setDebugFlag(False)
      self.tmpdir = tempfile.mkdtemp("armory_wallet")
      setArmoryHomeDir(self.tmpdir)

      self.wltDir = 'tempwallets'
      self.wltFN = 'test_wallet_file.wallet'

      if not os.path.exists(self.wltDir):
         os.makedirs(self.wltDir)

      self.clearWallets()

      self.seed = SecureBinaryData('\xaa'*32) 
      self.wltName = u'Test wallet\u2122'
   
      self.newWallet = ArmoryWalletFile.CreateWalletFile_NewRoot(
         self.wltName, ABEK_BIP44Seed, None, self.seed, NULLCRYPTINFO(), None,
         None, createInDir=self.wltDir, specificFilename=self.wltFN,
         Progress=emptyFunc)
      self.root = self.newWallet.topLevelRoots[0]

      
   #############################################################################
   def tearDown(self):
      self.clearWallets()
      shutil.rmtree(self.tmpdir)

   #############################################################################
   def clearWallets(self):
      flist = []
      flist.append(self.wltDir + '/test_wallet_file.wallet')
      flist.append(self.wltDir + '/test_wallet_file_backup.wallet')
      flist.append(self.wltDir + '/test_wallet_file_update_unsuccessful.wallet')
      flist.append(self.wltDir + '/test_wallet_file_backup_unsuccessful.wallet')
      for f in flist:
         removeIfExists(f)

   #############################################################################
   def testWallet(self):
      writeReadWalletRoundTripTest(self, self.newWallet)
      # locking shouldn't do anything
      self.root.lock()
      # getting the priv key shouldn't require an unlock
      self.assertEqual(len(self.root.getSerializedPrivKey('xprv')), 111)
