'''
Created on Aug 4, 2013

@author: Andy
'''
import sys
sys.path.append('..')
from pytest.Tiab import TiabTest

from random import shuffle
import unittest

from armoryengine.ArmoryUtils import FiniteField, FiniteFieldError, SplitSecret, \
   hex_to_binary, RightNow, binary_to_hex, ReconstructSecret


sys.argv.append('--nologging')
sys.argv.append('--nologging')

TEST_A = 200
TEST_B = 100
TEST_ADD_RESULT = 49
TEST_SUB_RESULT = 100
TEST_MULT_RESULT = 171
TEST_DIV_RESULT = 2
TEST_MTRX = [[1, 2, 3], [3,4,5], [6,7,8] ]
TEST_VECTER = [1, 2, 3]
TEST_3_BY_2_MTRX = [[1, 2, 3], [3,4,5]]
TEST_2_BY_3_MTRX = [[1, 2], [3,4], [5, 6]]
TEST_RMROW1CO1L_RESULT = [[1, 3], [6, 8]]
TEST_DET_RESULT = 0
TEST_MULT_VECT_RESULT = [14, 26, 44]
TEST_MULT_VECT_RESULT2 = [5, 11, 17]
TEST_MULT_VECT_RESULT3 = [[7, 10], [15, 22], [23, 34]]
TEST_MULT_VECT_RESULT4 = [[248, 5, 249], [6, 241, 4], [248, 5, 249]]
TEST_MULT_VECT_RESULT5 = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

class SplitSecretTest(TiabTest):


   def testFiniteFieldTest(self):
      ff1 = FiniteField(1)
      self.assertRaises(FiniteFieldError, FiniteField, 257)

      self.assertEqual(ff1.add(TEST_A, TEST_B), TEST_ADD_RESULT)
      self.assertEqual(ff1.subtract(TEST_A, TEST_B), TEST_SUB_RESULT)
      self.assertEqual(ff1.mult(TEST_A, TEST_B), TEST_MULT_RESULT)
      self.assertEqual(ff1.divide(TEST_A, TEST_B), TEST_DIV_RESULT)
      self.assertEqual(ff1.mtrxrmrowcol(TEST_MTRX, 1, 1), TEST_RMROW1CO1L_RESULT)
      self.assertEqual(ff1.mtrxrmrowcol(TEST_3_BY_2_MTRX, 1, 1), [])
      self.assertEqual(ff1.mtrxdet([[1]]), 1)
      self.assertEqual(ff1.mtrxdet(TEST_3_BY_2_MTRX), -1)
      self.assertEqual(ff1.mtrxdet(TEST_MTRX), TEST_DET_RESULT)
      self.assertEqual(ff1.mtrxmultvect(TEST_MTRX, TEST_VECTER), TEST_MULT_VECT_RESULT)
      self.assertEqual(ff1.mtrxmultvect(TEST_3_BY_2_MTRX, TEST_VECTER), TEST_MULT_VECT_RESULT[:2])
      self.assertEqual(ff1.mtrxmultvect(TEST_2_BY_3_MTRX, TEST_VECTER), TEST_MULT_VECT_RESULT2)
      self.assertEqual(ff1.mtrxmult(TEST_2_BY_3_MTRX, TEST_3_BY_2_MTRX), TEST_MULT_VECT_RESULT3)
      self.assertEqual(ff1.mtrxmult(TEST_2_BY_3_MTRX, TEST_2_BY_3_MTRX), TEST_MULT_VECT_RESULT3)
      self.assertEqual(ff1.mtrxadjoint(TEST_MTRX), TEST_MULT_VECT_RESULT4)
      self.assertEqual(ff1.mtrxinv(TEST_MTRX), TEST_MULT_VECT_RESULT5)

   def testSplitSecret(self):
      self.callSplitSecret('9f', 2,3)
      self.callSplitSecret('9f', 3,5)
      self.callSplitSecret('9f', 4,7)
      self.callSplitSecret('9f', 5,9)
      self.callSplitSecret('9f', 6,7)
      self.callSplitSecret('9f'*16, 3,5, 16)
      self.callSplitSecret('9f'*16, 7,10, 16)
      self.assertRaises(FiniteFieldError, SplitSecret, '9f'*16, 3, 5, 8)
      self.assertRaises(FiniteFieldError, SplitSecret, '9f', 5,4)
      self.assertRaises(FiniteFieldError, SplitSecret, '9f', 1,1)

   
   def callSplitSecret(self, secretHex, M, N, nbytes=1):
      secret = hex_to_binary(secretHex)
      print '\nSplitting secret into %d-of-%d: secret=%s' % (M,N,secretHex)
      tstart = RightNow() 
      out = SplitSecret(secret, M, N)
      tsplit = RightNow() - tstart
      print 'Fragments:'
      for i in range(len(out)):
         x = binary_to_hex(out[i][0])
         y = binary_to_hex(out[i][1])
         print '   Fragment %d: [%s, %s]' % (i+1,x,y)
      trecon = 0
      print 'Reconstructing secret from various subsets of fragments...'
      for i in range(10):
         shuffle(out)
         tstart = RightNow()
         reconstruct = ReconstructSecret(out, M, nbytes)
         trecon += RightNow() - tstart
         print '   The reconstructed secret is:', binary_to_hex(reconstruct)
         self.assertEqual(binary_to_hex(reconstruct), secretHex)
      print 'Splitting secret took: %0.5f sec' % tsplit
      print 'Reconstructing takes:  %0.5f sec' % (trecon/10)

# Running tests with "python <module name>" will NOT work for any Armory tests
# You must run tests with "python -m unittest <module name>" or run all tests with "python -m unittest discover"
# if __name__ == "__main__":
#    unittest.main()