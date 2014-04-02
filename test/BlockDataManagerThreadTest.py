'''
Created on Jul 29, 2013

@author: Andy
'''
import sys
from armoryengine.BDM import BlockDataManagerThread
sys.argv.append('--nologging')
import unittest

class BlockDataManagerThreadTest(unittest.TestCase):

   def setUp(self):
      self.theBDM = BlockDataManagerThread()


   def testPredictLoadTime(self):
      '''
      This whole test and all of the test files are out of date.
      
      Add optional args to the subject to run this test.
      
      Update with the latest format that looks like this.
      3 909278307 285 0 0.001
      3 909278307 37621601 0 4.782
      3 909278307 74125505 0 9.788
      3 909278307 108883082 0 14.779
      3 909278307 145392744 0 19.771

      # blkfiles1.txt - completed phase 1, should be exactly a quarter complete
      # time left is last time(200) - first time(100) * 3 
      # There is still phase 2 which 3 times longer than phase 1
      actual = self.theBDM.predictLoadTime('.', 'blkfiles1.txt')
      self.assertTrue(actual)
      self.assertEqual(1, actual[0])
      self.assertEqual(.25, actual[1])
      self.assertEqual(.0025, actual[2])
      self.assertEqual(300, actual[3])
      
      # set values to be about half way through
      actual = self.theBDM.predictLoadTime('.', 'blkfiles2.txt')
      self.assertTrue(actual)
      self.assertAlmostEqual(2, actual[0], 2)
      self.assertAlmostEqual(.5, actual[1], 2)
      self.assertAlmostEqual(.0025, actual[2], 2)
      self.assertAlmostEqual(200.3, actual[3], 2)

      # set values to be all the way through
      actual = self.theBDM.predictLoadTime('.', 'blkfiles3.txt')
      self.assertTrue(actual)
      self.assertEqual(1, actual[1])
      self.assertEqual(0, actual[3])
      '''


if __name__ == "__main__":
   #import sys;sys.argv = ['', 'Test.testArmoryEngine']
   unittest.main()