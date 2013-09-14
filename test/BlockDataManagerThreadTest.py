'''
Created on Jul 29, 2013

@author: Andy
'''
import sys
sys.argv.append('--nologging')
import unittest
from armoryengine import BlockDataManagerThread

class BlockDataManagerThreadTest(unittest.TestCase):

   def setUp(self):
      self.theBDM = BlockDataManagerThread()


   def testPredictLoadTime(self):
      # blkfiles1.txt - completed phase 1, should be exactly a quarter complete
      # time left is last time(200) - first time(100) * 3 
      # There is still phase 2 which 3 times longer than phase 1
      actual = self.theBDM.predictLoadTime('.', 'blkfiles1.txt')
      self.assertTrue(actual)
      self.assertEqual(.25, actual[0])
      self.assertEqual(.0025, actual[1])
      self.assertEqual(300, actual[2])
      
      # set values to be about half way through
      actual = self.theBDM.predictLoadTime('.', 'blkfiles2.txt')
      self.assertTrue(actual)
      self.assertAlmostEqual(.5, actual[0], 2)
      self.assertAlmostEqual(.0025, actual[1], 2)
      self.assertAlmostEqual(200.3, actual[2], 2)

      # set values to be all the way through
      actual = self.theBDM.predictLoadTime('.', 'blkfiles3.txt')
      self.assertTrue(actual)
      self.assertEqual(1, actual[0])
      self.assertEqual(0, actual[2])
      


if __name__ == "__main__":
   #import sys;sys.argv = ['', 'Test.testArmoryEngine']
   unittest.main()