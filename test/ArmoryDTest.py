'''
Created on Oct 8, 2013

@author: Andy
'''
import unittest


class ArmoryDTest(unittest.TestCase):


 def testIsASCII(self):
      self.assertTrue(isASCII(ASCII_STRING))
      self.assertFalse(isASCII(NON_ASCII_STRING))

   def testToBytes(self):
      self.assertEqual(toBytes(UNICODE_STRING), UNICODE_STRING.encode('utf-8'))
      self.assertEqual(toBytes(ASCII_STRING), ASCII_STRING)
      self.assertEqual(toBytes(NON_ASCII_STRING), NON_ASCII_STRING)
      self.assertEqual(toBytes(5), None)
      
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()