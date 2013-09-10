'''
Created on Jul 29, 2013

@author: Andy
'''
import sys
sys.argv.append('--nologging')
import unittest
from armoryengine import BlockDataManagerThread
sys.argv.append('--nologging')



class BlockDataManagerThreadTest(unittest.TestCase):

   def setUp(self):
      self.theBDM = BlockDataManagerThread()


   def testPredictLoadTime(self):
      actual = self.theBDM.predictLoadTime('.', 'blkfiles1.txt')
      self.assertTrue(actual)
      



if __name__ == "__main__":
   #import sys;sys.argv = ['', 'Test.testArmoryEngine']
   unittest.main()