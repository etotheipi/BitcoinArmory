'''
Created on Aug 26, 2013

@author: Andy
'''
import sys
sys.argv.append('--nologging')
from extras.findpass import UnknownCaseSeg, MaxResultsExceeded, KnownSeg, \
   UnknownSeg, PwdSeg, PasswordFinder, WalletNotFound
import unittest


seg1Input = 'abc'
seg2Input = '123abcdef123ghijklmno123'

segList1 = [['a','b','c'],['1','2'],['!']]
segOrdList1 = [[0,1,2],[2,0,1,],[0,1]]
expectedResult1 = ['a1!', 'a2!', 'b1!', 'b2!', 'c1!', 'c2!', \
                '!a1', '!a2', '!b1', '!b2', '!c1', '!c2', \
                 'a1', 'a2', 'b1', 'b2', 'c1', 'c2']



def expectedResultGenerator(expectedResult):
   for x in expectedResult:
      yield x

class Test(unittest.TestCase):
   
   def testUnknownCaseSeg(self):
      seg1 = UnknownCaseSeg(seg1Input)
      segStringList1 = seg1.getSegList()
      self.assertEqual(8, len(segStringList1))
      self.assertTrue(seg1Input.upper() in segStringList1)
      
      seg2 = UnknownCaseSeg(seg2Input)
      segStringList2 = seg2.getSegList()
      expectedSeg2Len = 2**len(seg2Input.translate(None, '123'));
      self.assertEqual(expectedSeg2Len, len(segStringList2))
      self.assertTrue(seg2Input.upper() in segStringList2)
      self.assertRaises(MaxResultsExceeded, seg2.getSegList, expectedSeg2Len-1)

   def testKnownSeg(self):
      seg1 = KnownSeg(seg1Input)
      segStringList1 = seg1.getSegList()
      self.assertEqual([seg1Input], segStringList1)
      
      seg2 = KnownSeg(seg2Input)
      self.assertEqual(1, seg2.getSegListLen())
      self.assertEqual([seg2Input], seg2.getSegList())
      
   def testUnknownSeg(self):
      seg1 = UnknownSeg(seg1Input,2,3)
      self.assertEqual(36, seg1.getSegListLen())
      segStringList1 = seg1.getSegList()
      self.assertEqual(36, len(segStringList1))
      self.assertTrue(seg1Input in segStringList1)
      
      seg2Len = 5
      seg2 = UnknownSeg(seg2Input, seg2Len, seg2Len)
      expectedSeg2KnownLen = len(set(seg2Input))
      self.assertEqual(expectedSeg2KnownLen, len(seg2.known))
      segStringList2 = seg2.getSegList()
      expectedSeg2Len = expectedSeg2KnownLen ** seg2Len
      self.assertEqual(expectedSeg2Len, len(segStringList2))
      self.assertTrue(seg2Input[0] * seg2Len in segStringList2)
      self.assertRaises(MaxResultsExceeded, seg2.getSegList, expectedSeg2Len-1)
   

   def testPasswordFinder(self):
      # Name of wallet is the password followed by '.wallet'
      passwordFinder = PasswordFinder(walletPath='FakeWallet123.wallet')
      self.assertTrue(passwordFinder.wallet.isLocked)
      theExpectedResultGenerator = expectedResultGenerator(expectedResult1)
      for i, result in enumerate(passwordFinder.passwordGenerator(segList1, segOrdList1)):
         expectedResult = expectedResult1[i]
         self.assertEqual(expectedResult, result)
      self.assertEqual(len(expectedResult1), \
                       passwordFinder.countPasswords(segList1, segOrdList1))
      passwordFinderSegList = [KnownSeg('Wallet').getSegList(),
                               UnknownSeg('123', 3, 3).getSegList(), 
                               UnknownCaseSeg('Fake').getSegList()]
      expectedFoundPassword = 'FakeWallet123'
      foundPassword = passwordFinder.searchForPassword(passwordFinderSegList, segOrdList1)
      self.assertEqual(foundPassword, expectedFoundPassword)
