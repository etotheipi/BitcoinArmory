################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
import sys
sys.path.append('..')
from pytest.Tiab import TiabTest
from armoryengine.ArmoryUtils import SplitSecret, binary_to_hex, ReconstructSecret,\
   FiniteFieldError
import itertools
import unittest


SECRET = '\x00\x01\x02\x03\x04\x05\x06\x07'

BAD_SECRET = '\xff\xff\xff\xff\xff\xff\xff\xff'

# Fragment combination to String abreviated name for debugging purposes
def c2s(combinationMap):
   return '\n'.join([' '.join([str(k), binary_to_hex(v[0]), binary_to_hex(v[1])]) \
                      for k,v in combinationMap.iteritems()])
   
def splitSecretToFragmentMap(splitSecret):
   fragMap = {}
   for i,frag in enumerate(splitSecret):
      fragMap[i] = frag
   return fragMap


class Test(TiabTest):

   def setUp(self):
      pass
      
   def tearDown(self):
      pass

   def getNextCombination(self, fragmentMap, m):
      combinationIterator = itertools.combinations(fragmentMap.iterkeys(), m)
      for keyList in combinationIterator:
         combinationMap = {}
         for key in keyList:
            combinationMap[key] = fragmentMap[key] 
         yield combinationMap
   
   
   def subtestAllFragmentedBackups(self, secret, m, n):
      fragmentMap = splitSecretToFragmentMap(SplitSecret(secret, m, n))
      for combinationMap in self.getNextCombination(fragmentMap, m):
         fragmentList = [value for value in combinationMap.itervalues()]
         reconSecret = ReconstructSecret(fragmentList, m, len(secret))
         self.assertEqual(reconSecret, secret)
         

   def testFragmentedBackup(self):

      self.subtestAllFragmentedBackups(SECRET, 2, 3)
      self.subtestAllFragmentedBackups(SECRET, 2, 3)
      self.subtestAllFragmentedBackups(SECRET, 3, 4)
      self.subtestAllFragmentedBackups(SECRET, 5, 7)
      self.subtestAllFragmentedBackups(SECRET, 8, 8)
      self.subtestAllFragmentedBackups(SECRET, 2, 12)

      # Secret Too big test
      self.assertRaises(FiniteFieldError, SplitSecret, BAD_SECRET, 2,3)

      # More needed than pieces
      self.assertRaises(FiniteFieldError, SplitSecret, SECRET, 4,3)
      
      # Secret Too many needed needed
      self.assertRaises(FiniteFieldError, SplitSecret, SECRET, 9, 12)

      # Too few pieces needed
      self.assertRaises(FiniteFieldError, SplitSecret, SECRET, 1, 12)
      
      # Test Reconstuction failures
      fragmentList = SplitSecret(SECRET, 3, 5)
      reconSecret = ReconstructSecret(fragmentList[:2], 2, len(SECRET))
      self.assertNotEqual(reconSecret, SECRET)

# Running tests with "python <module name>" will NOT work for any Armory tests
# You must run tests with "python -m unittest <module name>" or run all tests with "python -m unittest discover"
# if __name__ == "__main__":
#    unittest.main()