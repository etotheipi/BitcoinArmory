'''
Created on Jan 10, 2014

@author: Alan
'''
import sys
import unittest

sys.path.append('..')
from armoryengine.ALL import *


# Unserialize an reserialize

class TransactionTest(unittest.TestCase):

   
   def setUp(self):
      pass
   
   
   def tearDown(self):
      pass
   
   #############################################################################
   def test_read_address(self):
      hashVal = hex_to_binary('c3a9eb6753c449c88ac193e9ddf7ab3a0be8c5ad')
      addrStr00  = '1JqaKdBsruwgGcZkiVCNU2DBh56DJqhemg'
      addrStr05  = '3KXbFAgKQpG4MnGBqarxtea7qbNvtKyuAp'
      addrStrA3  = '28tvtpKmqbKUVaGHshsVKWTaRHJ5yG36xvv'
      addrStrBad = '1JqaKdBsruwgGcZkiVCNU2DBh56DHBsEb1'

      prefix, a160 = addrStr_to_hash160(addrStr00)
      self.assertEqual(prefix, ADDRBYTE)
      self.assertEqual(a160, hashVal)
      self.assertFalse(addrStr_is_p2sh(addrStr00))

      prefix, a160 = addrStr_to_hash160(addrStr05)
      self.assertEqual(prefix, P2SHBYTE)
      self.assertEqual(a160, hashVal)
      self.assertTrue(addrStr_is_p2sh(addrStr05))

      self.assertRaises(BadAddressError, addrStr_to_hash160, addrStrA3)
      self.assertRaises(ChecksumError, addrStr_to_hash160, addrStrBad)


   #############################################################################
   def test_p2pkhash_script(self):
      pkh = '\xab'*20
      computed = hash160_to_p2pkhash_script(pkh)
      expected = '\x76\xa9\x14' + pkh + '\x88\xac'
      self.assertEqual(computed, expected)

      # Make sure it raises an error on non-20-byte inputs
      self.assertRaises(InvalidHashError, hash160_to_p2pkhash_script, '\xab'*21)


   #############################################################################
   def test_p2sh_script(self):
      scriptHash = '\xab'*20
      computed = hash160_to_p2sh_script(scriptHash)
      expected = '\xa9\x14' + scriptHash + '\x87'
      self.assertEqual(computed, expected)
   
      # Make sure it raises an error on non-20-byte inputs
      self.assertRaises(InvalidHashError, hash160_to_p2sh_script, '\xab'*21)


   #############################################################################
   def test_p2pk_script(self):
      pubkey   = ['\x3a'*33, \
                  '\x3a'*65]

      expected = ['\x21' + '\x3a'*33 + '\xac', \
                  '\x41' + '\x3a'*65 + '\xac']

      for i in range(2):
         pk = pubkey[i]
         exp = expected[i]
         self.assertEqual( pubkey_to_p2pk_script(pk), exp)


      # Make sure it raises an error on non-[33,65]-byte inputs
      self.assertRaises(KeyDataError, pubkey_to_p2pk_script, '\xab'*21)


   #############################################################################
   def test_script_to_p2sh(self):
      script = '\xab'*10
      scriptHash = hex_to_binary('fc7eb079a69ac4a98e49ea373c91f62b8b9cebe2')
      expected = '\xa9\x14' + scriptHash + '\x87'
      self.assertEqual( script_to_p2sh_script(script), expected)

   #############################################################################
   def test_pklist_to_multisig(self):
      pk1 = 'x01'*33
      pk2 = 'xfa'*33
      pk3 = 'x33'*33
      pk4 = 'x01'*65
      pk5 = 'xfa'*65
      pk6 = 'x33'*65
      pkNot = 'x33'*100
      pkList1 = [pk1, pk2, pk3]
      pkList2 = [pk4, pk5, pk6]
      pkList3 = [pk1, pk5, pk3]
      pkList4 = [pk1, pkNot, pk3] # error

      self.assertTrue(False) # STUB
     

   
   
if __name__ == "__main__":
   #import sys;sys.argv = ['', 'Test.testName']
   unittest.main()
