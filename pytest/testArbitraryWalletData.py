###############################################################################
#                                                                             #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                          #
# Distributed under the GNU Affero General Public License (AGPL v3)           #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                        #
#                                                                             #
###############################################################################
import sys
sys.path.append('..')
import unittest
import sys
sys.path.append('..')
import textwrap

from armoryengine.ALL import *
from armoryengine.ArbitraryWalletData import ArbitraryWalletData


###############################################################################
class InfinimapTests(unittest.TestCase):

   ############################################################################
   def setUp(self):
      useMainnet()

   ############################################################################
   def testInfinimap(self):
      inf = Infinimap()

      inf.setData(['a','b','c'], 'Helloabc')
      inf.setData(['a','b'], 'abhi')
      inf.setData(['a','c'], 'I c u')
      inf.setData(['a','d'], 'ddddd')
      inf.setData(['a','z'], 'skipped a few')
      inf.setData(['123','456','789'], 'numbers')
      inf.setData(['123','456','abc'], 'not all numbers')
      inf.setData(['123','456','ab3'], 'hexnumbers')
      inf.setData(['123'], 'lessnumbers')

      #inf.pprint()


      self.assertEqual(inf.getData(['123']), 'lessnumbers')
      self.assertEqual(inf.getData(['123','456','ab3']), 'hexnumbers')
      self.assertEqual(inf.getData(['123','456','abr3']), None)

      self.assertEqual(inf.countNodes(), 11)
      self.assertEqual(inf.countLeaves(), 7)
      self.assertEqual(inf.countNonEmpty(), 9)

      self.assertEqual(inf.getData(['zzz']), None)
      inf.setData(['zzz'], 'zzz')
      self.assertEqual(inf.getData(['zzz']), 'zzz')

   #############################################################################
   def testGetKeyList(self):
      listlist = [ ['a'],  ['a','b'], ['123','456','789'], []]
      inf = Infinimap()
      for lst in listlist:
         inf.setData(lst, 'hello')

      # Get node from in the inf via key list, then check getKeyList matches
      for lst in listlist:
         self.assertEqual(inf.root.getNodeRecurse(lst).keyList, lst)

   #############################################################################
   def testRecurseApply(self):
      # Count all nodes that are only a single letter
      singleLetterKeys = []
      def checkNode(node):
         if len(node.getSelfKey())==1:
            singleLetterKeys.append(node.getSelfKey())

      countRef = [0]
      def anotherCheck(node):
         if not node.isEmpty():
            countRef[0] += len(node.getPlainDataCopy())

      def justPrint(node):
         print str(node.getKeyList()) + ' : ' + node.getPlainDataCopy()
      
      inf = Infinimap()
      inf.setData(['a','b','c'],       'Helloabc')
      inf.setData(['a','b'],           '')
      inf.setData(['a','z'],           'skipped a few')
      inf.setData(['123','456','789'], 'numbers')
      inf.setData(['123'],             'lessnumbers')
      inf.setData(['123', '3', 'a'],   'something different')
      inf.setData(['123', '3', 'ab'],  'and simple')

      inf.applyToMap(checkNode)

      self.assertEqual(len(singleLetterKeys), 6)
      self.assertEqual(sorted(singleLetterKeys), ['3','a','a','b','c','z'])

      inf.applyToMap(anotherCheck)
      self.assertEqual(countRef[0], 68)

      
      singleLetterKeys = []
      inf.applyToBranch(['a'], checkNode)
      self.assertEqual(len(singleLetterKeys), 4)
      self.assertEqual(sorted(singleLetterKeys), ['a','b','c','z'])


   #############################################################################
   def testClearData(self):

      inf = Infinimap()
      inf.setData(['a','b','c'],       'Helloabc')
      inf.setData(['a','b'],           '')
      inf.setData(['a','z'],           'skipped a few')
      inf.setData(['123','456','789'], 'numbers')
      inf.setData(['123'],             'lessnumbers')
      inf.setData(['123', '3', 'a'],   'something different')
      inf.setData(['123', '3', 'ab'],  'and simple')

      self.assertEqual(inf.countNodes(), 10)
      self.assertEqual(inf.countLeaves(), 5)
      self.assertEqual(inf.countNonEmpty(), 6)

      inf.clearMap()
      self.assertEqual(inf.countNodes(), 0)
      self.assertEqual(inf.countLeaves(), 0)
      self.assertEqual(inf.countNonEmpty(), 0)

      inf.setData(['a','b','c'],       'Helloabc')
      inf.setData(['a','b',],          '')
      inf.setData(['a','z',],          'skipped a few')
      inf.setData(['123','456','789'], 'numbers')
      inf.setData(['123'],             'lessnumbers')
      inf.setData(['123', '3', 'a'],   'something different')
      inf.setData(['123', '3', 'ab'],  'and simple')
      
      inf.clearBranch(['123','3'])
      self.assertEqual(inf.countNodes(), 7)
      self.assertEqual(inf.countLeaves(), 3)
      self.assertEqual(inf.countNonEmpty(), 4)

      inf.clearBranch(['a'], andBranchPoint=False)
      self.assertEqual(inf.countNodes(), 4)
      self.assertEqual(inf.countLeaves(), 2)
      self.assertEqual(inf.countNonEmpty(), 2)


   #############################################################################
   def testEncrypted(self):
      # This test data was copied from the testEncryptInfo.py tests

      SampleKdfAlgo   = 'ROMIXOV2'
      SampleKdfMem    = 4194304
      SampleKdfIter   = 3
      SampleKdfSalt   = SecureBinaryData(hex_to_binary( \
            '38c1355eb2b39330bab691b58b7ee0c0c7fbc6c706c088244d3fd3becea5e958'))
      SamplePasswd    = SecureBinaryData('TestPassword')
      SampleKdfOutKey = SecureBinaryData(hex_to_binary( \
            'affc2dbe749a9f5b3c01b4a88fb150fcdb7b10187555e9009265eec911108e8b'))
      SampleKdfID     = hex_to_binary('92c130cd7399b061')
      SamplePlainStr  = SecureBinaryData('test_encrypt____')  
      SampleCryptAlgo = 'AE256CBC'
      SampleCryptIV8  = 'randomIV'
      SampleCryptIV16 = stretchIV(SecureBinaryData(SampleCryptIV8), 16)
      SampleCryptStr  = SecureBinaryData(hex_to_binary( \
            '467450aeb63bbe83d9758cb4ae44477e'))
      SampleMasterEKey = SecureBinaryData('samplemasterkey0' + '\xfa'*16)
      SampleMasterCrypt = SecureBinaryData(hex_to_binary( \
            '5ab2e112def50f0e1f4fd7e5d81a3af37c6754f28bc7533c2db9f779ba0a79b8'))
      SampleMasterEkeyID = hex_to_binary('0524acc0d96da57f')

      self.kdf = KdfObject(SampleKdfAlgo, memReqd=SampleKdfMem, 
                                          numIter=SampleKdfIter, 
                                          salt=SampleKdfSalt)

      self.ekey = EncryptionKey()
      self.ekey.createNewMasterKey(self.kdf, SampleCryptAlgo, SamplePasswd,
                           preGenKey=SampleMasterEKey, preGenIV8=SampleCryptIV8)

      aci = ArmoryCryptInfo(NULLKDF, SampleCryptAlgo, self.ekey.ekeyID, SampleCryptIV8)
      computeCrypt = aci.encrypt(SamplePlainStr, 
                                 SamplePasswd,
                                 kdfObj=self.kdf,
                                 ekeyObj=self.ekey)

      expectCrypt = CryptoAES().EncryptCBC(SamplePlainStr, 
                                           SampleMasterEKey, 
                                           SampleCryptIV16)

      # Just doing a sanity check here that the endecrypt working correctly
      self.assertEqual(computeCrypt, expectCrypt)


      inf = Infinimap()
      inf.setData(['a','b','c'],       'Helloabc')
      inf.setData(['a','b'],           '')
      inf.setData(['a','z'],           'skipped a few')
      inf.setData(['123','456','789'], 'numbers')
      inf.setData(['123'],             'lessnumbers')
      inf.setData(['123', '3', 'a'],   'something different')
      inf.setData(['123', '3', 'ab'],  'and simple')

      nodeabc = inf.getNode(['a','b','c'])
      nodeabc.enableEncryption(aci, self.ekey)

      self.ekey.lock()
      self.assertRaises(WalletLockError, nodeabc.setPlaintextToEncrypt, SamplePlainStr)

      self.ekey.unlock(SamplePasswd)
      nodeabc.setPlaintextToEncrypt(SamplePlainStr)

      self.assertEqual(len(nodeabc.dataStr), ArbitraryWalletData.CRYPTPADDING)
      self.assertEqual(SamplePlainStr, nodeabc.getPlainDataCopy())
      
      countEncrypt = [0]
      def countFunc(node):
         if node.useEncryption():
            countEncrypt[0] += 1

      inf.applyToMap(countFunc)
      self.assertEqual(countEncrypt[0], 1)

      inf.pprint()


      node = inf.getNode(['a','b','c'])
      self.assertRaises(EncryptionError, node.setPlaintext, 'AAAA')

      node = inf.getNode(['123','3','ab'])
      self.assertRaises(EncryptionError, node.setPlaintextToEncrypt, 'Plain')

      self.ekey.lock()
      sbdNew = SecureBinaryData('NewSecret')
      self.assertRaises(WalletLockError, inf.setData, ['a','b','c'], sbdNew)

      self.ekey.unlock(SamplePasswd)
      inf.setData(['a','b','c'], sbdNew)

      self.ekey.lock()
      self.assertRaises(WalletLockError, inf.getData, ['a','b','c'])

      self.ekey.unlock(SamplePasswd)
      self.assertEqual(inf.getData(['a','b','c']), sbdNew)


   #############################################################################
   def testInsertObject(self):
      inf = Infinimap()
      inf.setData(['a','b','c'],       'Helloabc')
      inf.setData(['a','b'],           '')
      inf.setData(['a','z'],           'skipped a few')
      inf.setData(['123','456','789'], 'numbers')
      inf.setData(['123'],             'lessnumbers')
      inf.setData(['123', '3', 'a'],   'something different')
      inf.setData(['123', '3', 'ab'],  'and simple')

      newStr = 'test insert!'
      awd = ArbitraryWalletData(['123','4'], newStr)
      self.assertEqual(inf.countNonEmpty(), 6)
      awd.insertIntoInfinimap(inf)
      self.assertEqual(inf.countNonEmpty(), 7)
      self.assertEqual(inf.getData(['123','4']), newStr)


   #############################################################################
   def testSerUnserRoundTrip(self):
      awd = ArbitraryWalletData(['123','4'], 'abc')
      awdStr = awd.serialize()
      awd2 = ArbitraryWalletData().unserialize(awdStr)
      awd2Str = awd2.serialize()
      self.assertEqual(awdStr, awd2Str)

      # Now test an encrypted AWDs
      SampleKdfAlgo   = 'ROMIXOV2'
      SampleKdfMem    = 4194304
      SampleKdfIter   = 3
      SampleKdfSalt   = SecureBinaryData(hex_to_binary( \
            '38c1355eb2b39330bab691b58b7ee0c0c7fbc6c706c088244d3fd3becea5e958'))

      SamplePasswd    = SecureBinaryData('TestPassword')

      SampleCryptAlgo = 'AE256CBC'
      SampleCryptIV8  = 'randomIV'
      SampleMasterEKey = SecureBinaryData('samplemasterkey0' + '\xfa'*16)

      kdf = KdfObject(SampleKdfAlgo, memReqd=SampleKdfMem, 
                                          numIter=SampleKdfIter, 
                                          salt=SampleKdfSalt)

      ekey = EncryptionKey()
      ekey.createNewMasterKey(kdf, SampleCryptAlgo, SamplePasswd,
                           preGenKey=SampleMasterEKey, preGenIV8=SampleCryptIV8)

      aci = ArmoryCryptInfo(NULLKDF, SampleCryptAlgo, ekey.ekeyID, SampleCryptIV8)

      ekey.unlock(SamplePasswd)
      awd3 = ArbitraryWalletData(['a','b'])
      awd3.enableEncryption(aci, ekey)
      awd3.setPlaintextToEncrypt('sampletext')

      # Make sure serialization works on both locked and unlocked AWDs
      ekey.lock()
      awd3Str = awd3.serialize()
      awd4 = ArbitraryWalletData().unserialize(awd3Str)
      awd4Str = awd4.serialize()
      self.assertEqual(awd3Str, awd4Str)

      ekey.unlock(SamplePasswd)
      awd5 = ArbitraryWalletData(['a','b'])
      awd5.enableEncryption(aci, ekey)
      awd5.setPlaintextToEncrypt('sampletext')
      awd5Str = awd5.serialize()
      awd6 = ArbitraryWalletData().unserialize(awd5Str)
      awd6Str = awd6.serialize()
      self.assertEqual(awd5Str, awd6Str)
      self.assertEqual(awd3Str, awd6Str)


################################################################################
# if __name__ == "__main__":
#    unittest.main()
