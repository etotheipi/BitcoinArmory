import sys
sys.path.append('..')
import unittest
from pytest.Tiab import TiabTest

from CppBlockUtils import SecureBinaryData, CryptoECDSA
from armoryengine.ArmoryUtils import *
from armoryengine.MultiSigUtils import calcLockboxID
from armoryengine.Transaction import getTxOutScriptType
from armoryengine.UserAddressUtils import getDisplayStringForScript, \
   getScriptForUserString


################################################################################
class MockWallet(object):
   def __init__(self, wltID, lblName, scrAddr):
      self.labelName = lblName
      self.uniqueIDB58 = wltID
      self.scrAddr = scrAddr

   def hasScrAddr(self, scraddr):
      return scraddr==self.scrAddr
      

################################################################################
class MockLockbox(object):
   def __init__(self, lboxID, lboxName, script, M, N):
      self.uniqueIDB58 = lboxID
      self.shortName   = lboxName
      self.binScript   = script
      self.M           = M
      self.N           = N

      if getTxOutScriptType(script) == CPP_TXOUT_P2SH:
         self.p2shScrAddr = script_to_scrAddr(self.binScript)
      elif getTxOutScriptType(script) == CPP_TXOUT_MULTISIG:
         self.p2shScrAddr = script_to_scrAddr(script_to_p2sh_script(self.binScript))
      else:
         raise BadAddressError('Must initialize [mocked] lbox with MS or P2SH')

################################################################################
class ScriptToDispStrTest(TiabTest):
   """
   I know, these are not real unit tests!   The problem here is that it's going
   to take a ton of time to prepare the 300 different test outputs, and it's 
   very likely that I'll be tweaking the getDisplayStringForScript() many times
   before settling down on one I like.  for now, this is simply printing the
   outputs of the function, and you manually review it.

   Once this method is settled down, we can make it a real unit test
   """
   def setUp(self):
      self.pubKeyList    = [self.makePubKey(a) for a in ['\xbb','\xaa','\xcc']]
      self.binScriptMS   = pubkeylist_to_multisig_script(self.pubKeyList, 2) 
      self.binScriptP2PK = pubkey_to_p2pk_script(self.pubKeyList[0])
      self.p2pkHash160   = hash160(self.pubKeyList[0])
      self.binScriptP2PKH = hash160_to_p2pkhash_script(self.p2pkHash160)
      self.binScriptP2SH_MS = script_to_p2sh_script(self.binScriptMS)
      self.binScriptNonStd = '\x01'*25


      # Create two wallets, one will be used, one won't (both in map)
      self.wlt = MockWallet('AbCd1234z', 'Primary Long-Term Savings Wallet',
                                     script_to_scrAddr(self.binScriptP2PKH))

      self.wltNull = MockWallet('YyBb7788b', 'This wallet is not used',
                                                script_to_scrAddr('\x00'))

      # Create two lockboxes, one will be used, one won't (both in map)
      self.lboxID = calcLockboxID(self.binScriptMS)
      self.lbox = MockLockbox(self.lboxID, 'My Ultra-Secure Savings Lockbox',
                                       self.binScriptP2SH_MS, 2, 3)

      # Create some other public keys to create a lockbox that won't be used
      self.pubKeyListOther  = [self.makePubKey(a) for a in ['\x32','\x19','\xfc']]
      self.binScriptMSOther = pubkeylist_to_multisig_script(self.pubKeyListOther, 2) 
      self.lboxNull = MockLockbox('ZzCc8899a', 'This lockbox is not used',
                                                   self.binScriptMSOther, 3, 5)

      self.binScriptTestList = [ \
               [self.binScriptP2PKH,    'mfi7ZGQSEUSudTFeXrSnZUpo9u1dAtTBon'],
               [self.binScriptP2PK,     'mfi7ZGQSEUSudTFeXrSnZUpo9u1dAtTBon'],
               [self.binScriptMS,       '2N8pebcLPhfPhJpre5v1biNNTXxd9Qt3rcx'],
               [self.binScriptP2SH_MS,  '2N8pebcLPhfPhJpre5v1biNNTXxd9Qt3rcx'], 
               [self.binScriptNonStd,   '2NEF6nBRNhSDcsZu8UB877nnqwCWdKXbZXq']]

      
      self.maxLengthTestList = [256, 60, 58, 54, 45, 32]

   #############################################################################
   def makePubKey(self, byte):
      """
      The input byte will be repeated 32 times, then treated as the x-value of 
      a compressed pubkey.  Uncompress it to get a real pubkey.  We do this so
      that we have a valid public key for our tests, in which the validity of
      our 65-byte keys are checked
      """
      sbd33 = SecureBinaryData('\x02' + byte*32)
      return CryptoECDSA().UncompressPoint(sbd33).toBinStr()


   ##########################################################################
   def createTestFunction(self, wltList, lboxList, binScrList, lenList, descr):
      """
      All of the test basically reduce to a single, triply-nested loop with
      different inputs.  
      """
      def myTestFunc():
         print ''
         print '*'*80
         print descr
         print '*'*80

         wltMap = {}
         for wlt in wltList:
            wltMap[wlt.uniqueIDB58] = wlt

         for scr,addrStr in binScrList:
            print '\nAddrStr:', addrStr
            for pref in [True, False]:
               print '   PrefID:', str(pref)
               for lenMax in lenList:
                  outInfo = getDisplayStringForScript(scr, wltMap, lboxList, 
                                                      lenMax, prefIDOverAddr=pref)
                  outStr = outInfo['String']
                  lenStr = str(len(outStr)).rjust(3)
                  print '      ', lenStr,outStr
                  self.assertTrue(isinstance(outStr, basestring))
                  self.assertTrue(len(outStr) <= lenMax)

      return myTestFunc


   #############################################################################
   def testNoWalletsOrLockboxes(self):
      
      self.createTestFunction([], [], 
                              self.binScriptTestList, self.maxLengthTestList, 
                              "No wallets or lockboxes loaded")()

      
   #############################################################################
   def testOneWalletNoLockbox(self):
               
      self.createTestFunction([self.wlt], [], 
                              self.binScriptTestList, self.maxLengthTestList, 
                              "One wallet but no lockboxes")()



   #############################################################################
   def testOneWalletPlusNulls(self):
      self.createTestFunction([self.wlt, self.wltNull], [self.lboxNull], 
                              self.binScriptTestList, self.maxLengthTestList, 
                              "One wallet, one empty/null wallet and lockbox")()
               
   #############################################################################
   def testNoWalletOneLockbox(self):
      self.createTestFunction([], [self.lbox], 
                              self.binScriptTestList, self.maxLengthTestList, 
                              "One lockbox no wallets")()


   #############################################################################
   def testOneWalletOneLockbox(self):
      self.createTestFunction([self.wlt], [self.lbox], 
                              self.binScriptTestList, self.maxLengthTestList, 
                              "One lockbox and one wallet")()
   #############################################################################
   def testTwoWalletsTwoLockboxes(self):
      self.createTestFunction([self.wlt], [self.lbox], 
                              self.binScriptTestList, self.maxLengthTestList, 
                              "Two wallets and two lockboxes (one empty of each)")()
               


################################################################################
class UserAddressToScript(TiabTest):
   """
   Test a bunch of different strings that the user could enter, and check
   the output of getScriptForUserString(), with and without relevant wallets
   loaded/available
   """
   def setUp(self):
      self.pubKeyList    = [self.makePubKey(a) for a in ['\xaa','\x33','\x44']]
      self.binScriptMS   = pubkeylist_to_multisig_script(self.pubKeyList, 2) 
      self.binScriptP2PK = pubkey_to_p2pk_script(self.pubKeyList[0])
      self.p2pkHash160   = hash160(self.pubKeyList[0])
      self.binScriptP2PKH = hash160_to_p2pkhash_script(self.p2pkHash160)
      self.binScriptP2SH_MS = script_to_p2sh_script(self.binScriptMS)
      self.binScriptNonStd = '\x01'*25


      pubKeyCompr = '\x02' + '\xaa'*32
      self.binScriptP2PKCompr = pubkey_to_p2pk_script(pubKeyCompr)
      self.binScriptP2PKHCompr = hash160_to_p2pkhash_script(hash160(pubKeyCompr))

      # Create two wallets, one will be used, one won't (both in map)
      self.wlt = MockWallet('AbCd1234z', 'Primary Long-Term Savings Wallet',
                                     script_to_scrAddr(self.binScriptP2PKH))
      self.wlt2 = MockWallet('BcDe2345y', 'Another long-term savings wallet',
                                  script_to_scrAddr(self.binScriptP2PKCompr))
      self.wltNull = MockWallet('YyBb7788b', 'This wallet is not used',
                                                script_to_scrAddr('\x00'))

      self.lboxID = calcLockboxID(self.binScriptMS)
      self.lbox = MockLockbox(self.lboxID, 'My Ultra-Secure Savings Lockbox',
                               self.binScriptMS, 2, 3)

      # Create some other public keys to create a lockbox that won't be used
      self.pubKeyListOther  = [self.makePubKey(a) for a in ['\x32','\x19','\xfc']]
      self.binScriptMSOther = pubkeylist_to_multisig_script(self.pubKeyListOther, 2) 
      lboxIDOther = calcLockboxID(self.binScriptMSOther)
      self.lboxNull = MockLockbox(lboxIDOther, 'This lockbox is not used',
                                                   self.binScriptMSOther, 3, 5)



      # When all wallets and lockboxes are avail, these will all be recognized
      self.validInputStrings = [ \
         'n4TMVYp9BX4yDtjqPgJHrnRPu7zdZ2aLGj',
         '2N1j5GnC97dXRprEzbQVJJAYXMqCsffdX29',
         'Lockbox[%s]' % self.lboxID,
         'Lockbox[Bare:%s]' % self.lboxID,
         binary_to_hex(self.pubKeyList[0]),
         binary_to_hex(pubKeyCompr)]   # a compressed key
         
      # Now a few others that should fail to return useful info
      self.badInputStrings = [ \
         'mpduARVk95R9EXDtbb54fZG1VVQ4CWZmY6',   # bad checksum on addr
         'Lockbox{%s}' % self.lboxID,   
         'Lockbox[BARE:%s]' % self.lboxID,   # wrong casing
         'abc123',
         '']
         


   #############################################################################
   def makePubKey(self, byte):
      """
      The input byte will be repeated 32 times, then treated as the x-value of 
      a compressed pubkey.  Uncompress it to get a real pubkey.  We do this so
      that we have a valid public key for our tests, in which the validity of
      our 65-byte keys are checked
      """
      sbd33 = SecureBinaryData('\x02' + byte*32)
      return CryptoECDSA().UncompressPoint(sbd33).toBinStr()

   #############################################################################
   def testReadP2PKH(self):

      wltMap = {}
      lboxList = []

      scrInfo = getScriptForUserString(self.validInputStrings[0], wltMap, lboxList) 

      self.assertEqual(scrInfo['Script'], self.binScriptP2PKH)
      self.assertEqual(scrInfo['WltID'], None)
      self.assertEqual(scrInfo['LboxID'], None)
      self.assertTrue(scrInfo['ShowID'])


      wltMap = {}
      wltMap[self.wlt.uniqueIDB58]  = self.wlt
      wltMap[self.wlt2.uniqueIDB58] = self.wlt2
      lboxList = [self.lbox]

      scrInfo = getScriptForUserString(self.validInputStrings[0], wltMap, lboxList) 

      self.assertEqual(scrInfo['Script'], self.binScriptP2PKH)
      self.assertEqual(scrInfo['WltID'],  'AbCd1234z')
      self.assertEqual(scrInfo['LboxID'], None)
      self.assertTrue(scrInfo['ShowID'])

   #############################################################################
   def testReadP2SH(self):

      wltMap = {}
      lboxList = []

      scrInfo = getScriptForUserString(self.validInputStrings[1], wltMap, lboxList) 

      self.assertEqual(scrInfo['Script'], self.binScriptP2SH_MS)
      self.assertEqual(scrInfo['WltID'], None)
      self.assertEqual(scrInfo['LboxID'], None)
      self.assertTrue(scrInfo['ShowID'])


      wltMap = {}
      wltMap[self.wlt.uniqueIDB58]  = self.wlt
      wltMap[self.wlt2.uniqueIDB58] = self.wlt2
      lboxList = [self.lbox]

      scrInfo = getScriptForUserString(self.validInputStrings[1], wltMap, lboxList) 

      self.assertEqual(scrInfo['Script'], self.binScriptP2SH_MS)
      self.assertEqual(scrInfo['WltID'],  None)
      self.assertEqual(scrInfo['LboxID'], self.lboxID)
      self.assertTrue(scrInfo['ShowID'])



   #############################################################################
   def testReadLockboxP2SH(self):
      #self.validInputStrings = [ \
         #'1CAGDKTRT1erLn2pHUQjZcUHuQvEyxGp3j',
         #'3HGSXsQN6CtM73E6QnPj6RPCKcQyXS4Sek',
         #'Lockbox[%s]' % self.lboxID,
         #'Lockbox[Bare:%s]' % self.lboxID,
         #binary_to_hex(self.pubKeyList[0]),
         #binary_to_hex(pubKeyCompr]   # a compressed key

      wltMap = {}
      lboxList = []

      scrInfo = getScriptForUserString(self.validInputStrings[2], wltMap, lboxList) 

      self.assertEqual(scrInfo['Script'], None)
      self.assertEqual(scrInfo['WltID'], None)
      self.assertEqual(scrInfo['LboxID'], None)


      wltMap = {}
      wltMap[self.wlt.uniqueIDB58]  = self.wlt
      wltMap[self.wlt2.uniqueIDB58] = self.wlt2
      lboxList = [self.lbox]

      scrInfo = getScriptForUserString(self.validInputStrings[2], wltMap, lboxList) 

      self.assertEqual(scrInfo['Script'], self.binScriptP2SH_MS)
      self.assertEqual(scrInfo['WltID'],  None)
      self.assertEqual(scrInfo['LboxID'], self.lboxID)
      self.assertFalse(scrInfo['ShowID'])


   #############################################################################
   def testReadLockboxBare(self):
      #self.validInputStrings = [ \
         #'1CAGDKTRT1erLn2pHUQjZcUHuQvEyxGp3j',
         #'3HGSXsQN6CtM73E6QnPj6RPCKcQyXS4Sek',
         #'Lockbox[%s]' % self.lboxID,
         #'Lockbox[Bare:%s]' % self.lboxID,
         #binary_to_hex(self.pubKeyList[0]),
         #binary_to_hex(pubKeyCompr]   # a compressed key

      wltMap = {}
      lboxList = []

      scrInfo = getScriptForUserString(self.validInputStrings[3], wltMap, lboxList) 

      self.assertEqual(scrInfo['Script'], None)
      self.assertEqual(scrInfo['WltID'], None)
      self.assertEqual(scrInfo['LboxID'], None)


      wltMap = {}
      wltMap[self.wlt.uniqueIDB58]  = self.wlt
      wltMap[self.wlt2.uniqueIDB58] = self.wlt2
      lboxList = [self.lbox]

      scrInfo = getScriptForUserString(self.validInputStrings[3], wltMap, lboxList) 

      self.assertEqual(scrInfo['Script'], self.binScriptMS)
      self.assertEqual(scrInfo['WltID'],  None)
      self.assertEqual(scrInfo['LboxID'], self.lboxID)
      self.assertFalse(scrInfo['ShowID'])


   #############################################################################
   def testReadPubKeyUncompr(self):
      #self.validInputStrings = [ \
         #'1CAGDKTRT1erLn2pHUQjZcUHuQvEyxGp3j',
         #'3HGSXsQN6CtM73E6QnPj6RPCKcQyXS4Sek',
         #'Lockbox[%s]' % self.lboxID,
         #'Lockbox[Bare:%s]' % self.lboxID,
         #binary_to_hex(self.pubKeyList[0]),
         #binary_to_hex(pubKeyCompr]   # a compressed key

      wltMap = {}
      lboxList = []

      scrInfo = getScriptForUserString(self.validInputStrings[4], wltMap, lboxList) 

      self.assertEqual(scrInfo['Script'], self.binScriptP2PKH)
      self.assertEqual(scrInfo['WltID'], None)
      self.assertEqual(scrInfo['LboxID'], None)
      self.assertFalse(scrInfo['ShowID'])


      wltMap = {}
      wltMap[self.wlt.uniqueIDB58]  = self.wlt
      wltMap[self.wlt2.uniqueIDB58] = self.wlt2
      lboxList = [self.lbox]

      scrInfo = getScriptForUserString(self.validInputStrings[4], wltMap, lboxList) 

      self.assertEqual(scrInfo['Script'], self.binScriptP2PKH)
      self.assertEqual(scrInfo['WltID'],  'AbCd1234z')
      self.assertEqual(scrInfo['LboxID'], None)
      self.assertFalse(scrInfo['ShowID'])

   #############################################################################
   def testReadPubKeyCompr(self):
      #self.validInputStrings = [ \
         #'1CAGDKTRT1erLn2pHUQjZcUHuQvEyxGp3j',
         #'3HGSXsQN6CtM73E6QnPj6RPCKcQyXS4Sek',
         #'Lockbox[%s]' % self.lboxID,
         #'Lockbox[Bare:%s]' % self.lboxID,
         #binary_to_hex(self.pubKeyList[0]),
         #binary_to_hex(pubKeyCompr]   # a compressed key

      wltMap = {}
      lboxList = []

      scrInfo = getScriptForUserString(self.validInputStrings[5], wltMap, lboxList) 

      self.assertEqual(scrInfo['Script'], self.binScriptP2PKHCompr)
      self.assertEqual(scrInfo['WltID'], None)
      self.assertEqual(scrInfo['LboxID'], None)
      self.assertFalse(scrInfo['ShowID'])


      wltMap = {}
      wltMap[self.wlt.uniqueIDB58]  = self.wlt
      wltMap[self.wlt2.uniqueIDB58] = self.wlt2
      lboxList = [self.lbox]

      scrInfo = getScriptForUserString(self.validInputStrings[5], wltMap, lboxList) 

      self.assertEqual(scrInfo['Script'], self.binScriptP2PKHCompr)
      self.assertEqual(scrInfo['WltID'],  'BcDe2345y')
      self.assertEqual(scrInfo['LboxID'], None)
      self.assertFalse(scrInfo['ShowID'])


   #############################################################################
   def testReadBadStrings(self):

      wltMap = {}
      lboxList = []

      for badStr in self.badInputStrings:
         scrInfo = getScriptForUserString(badStr, wltMap, lboxList) 

         self.assertEqual(scrInfo['Script'], None)
         self.assertEqual(scrInfo['WltID'], None)
         self.assertEqual(scrInfo['LboxID'], None)


      wltMap = {}
      wltMap[self.wlt.uniqueIDB58]  = self.wlt
      wltMap[self.wlt2.uniqueIDB58] = self.wlt2
      lboxList = [self.lbox]

      for badStr in self.badInputStrings:
         scrInfo = getScriptForUserString(badStr, wltMap, lboxList) 

         self.assertEqual(scrInfo['Script'], None)
         self.assertEqual(scrInfo['WltID'], None)
         self.assertEqual(scrInfo['LboxID'], None)

# Running tests with "python <module name>" will NOT work for any Armory tests
# You must run tests with "python -m unittest <module name>" or run all tests with "python -m unittest discover"
# if __name__ == "__main__":
#    unittest.main()