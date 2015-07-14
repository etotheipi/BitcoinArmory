###############################################################################
#
# Copyright (C) 2011-2015, Armory Technologies, Inc.                         
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
###############################################################################
#
# Project:    Armory
# Author:     Alan Reiner
# Website:    www.bitcoinarmory.com
# Orig Date:  02 April, 2015
#
###############################################################################
import sys
sys.path.append('..')
import unittest
import textwrap

from armoryengine.ALL import *
from armoryengine.ErrorCorrection import *

def skipFlagExists():
   if os.path.exists('skipmosttests.flag'):
      print '*'*80
      print 'SKIPPING MOST TESTS.  REMOVE skipMostTests.flag TO REENABLE'
      print '*'*80
      return True
   else:
      return False




#############################################################################
class ChecksumTests(unittest.TestCase):

   def setUp(self):
      useMainnet()
      self.CHKSZ = 4
      self.PERSZ = 256
      
   def tearDown(self):
      pass

   ############################################################################
   def testChecksumValid(self):
      for mult in [20, 32, 200, 256, 1000]:
         data = 'abcd1234'*mult

         nBlks = ((len(data) - 1) / int(self.PERSZ)) + 1
         chk = ''
         for i in range(nBlks):
            chk += hash256(data[i*self.PERSZ:(i+1)*self.PERSZ])[:self.CHKSZ]
         
         chk2 = createChecksumBytes(data, self.CHKSZ, self.PERSZ)
         self.assertEquals(chk, chk2)
         data2,err,mod = verifyChecksumBytes(data, chk, self.CHKSZ, self.PERSZ)
      
         self.assertEquals(data, data2)
         self.assertFalse(err)
         self.assertFalse(mod)
      
   ############################################################################
   def testChecksumOneErr(self):
      for mult in [20, 32, 200, 256, 1000]:
         print 'Testing with one error, data size = %d' % (mult*8)
         data = 'abcd1234'*mult

         nBlks = ((len(data) - 1) / int(self.PERSZ)) + 1
         chk = ''
         for i in range(nBlks):
            chk += hash256(data[i*self.PERSZ:(i+1)*self.PERSZ])[:self.CHKSZ]
      
         chk2 = createChecksumBytes(data, self.CHKSZ, self.PERSZ)
         self.assertEquals(chk, chk2)

         oneErr = '_' + data[1:]
         data2,err,mod = verifyChecksumBytes(oneErr, chk, self.CHKSZ, self.PERSZ)
      
         self.assertEquals(data, data2)
         self.assertFalse(err)
         self.assertTrue(mod)

   ############################################################################
   def testChecksumOneErr_InChk(self):
      for mult in [20, 32, 200, 256, 1000]:
         print 'Testing with error in checksum itself, size = %d' % (mult*8)
         data = 'abcd1234'*mult

         nBlks = ((len(data) - 1) / int(self.PERSZ)) + 1
         chk = ''
         for i in range(nBlks):
            chk += hash256(data[i*self.PERSZ:(i+1)*self.PERSZ])[:self.CHKSZ]
      
         chk2 = createChecksumBytes(data, self.CHKSZ, self.PERSZ)
         self.assertEquals(chk, chk2)

         chkErr = '_' + chk[1:]
         data2,err,mod = verifyChecksumBytes(data, chkErr, self.CHKSZ, self.PERSZ)
      
         self.assertEquals(data, data2)
         self.assertFalse(err)
         self.assertTrue(mod)

         chkErr = chk[:-1] + '_'
         data2,err,mod = verifyChecksumBytes(data, chkErr, self.CHKSZ, self.PERSZ)
      
         self.assertEquals(data, data2)
         self.assertFalse(err)
         self.assertTrue(mod)


   ############################################################################
   def testChecksumTwoErr(self):
      for mult in [20, 32, 200, 256, 1000]:
         print 'Testing with two errors, data size = %d' % (mult*8)
         data = 'abcd1234'*mult

         nBlks = ((len(data) - 1) / int(self.PERSZ)) + 1
         chk = ''
         for i in range(nBlks):
            chk += hash256(data[i*self.PERSZ:(i+1)*self.PERSZ])[:self.CHKSZ]
      
         chk2 = createChecksumBytes(data, self.CHKSZ, self.PERSZ)
         self.assertEquals(chk, chk2)

         twoErr = '__' + data[2:]
         data2,err,mod = verifyChecksumBytes(twoErr, chk, self.CHKSZ, self.PERSZ)
      
         self.assertEquals(data2, '')
         self.assertTrue(err)
         self.assertFalse(mod)

         twoErr = data[:-2] + '__'
         data2,err,mod = verifyChecksumBytes(twoErr, chk, self.CHKSZ, self.PERSZ)
      
         self.assertEquals(data2, '')
         self.assertTrue(err)
         self.assertFalse(mod)

   ############################################################################
   def testChecksumOneErrorTwoBlks(self):
      # If there's two bytes wrong but in two different blocks, it should work 
      for mult in [200, 256, 1000]:
         print 'Testing with one error in each of two blocks  size = %d' % (mult*8)
         data = 'abcd1234'*mult

         nBlks = ((len(data) - 1) / int(self.PERSZ)) + 1
         chk = ''
         for i in range(nBlks):
            chk += hash256(data[i*self.PERSZ:(i+1)*self.PERSZ])[:self.CHKSZ]
      
         chk2 = createChecksumBytes(data, self.CHKSZ, self.PERSZ)
         self.assertEquals(chk, chk2)

         twoErr = '_' + data[1:-1] + '_'
         data2,err,mod = verifyChecksumBytes(twoErr, chk, self.CHKSZ, self.PERSZ)
      
         self.assertEquals(data2, data)
         self.assertFalse(err)
         self.assertTrue(mod)


#############################################################################
class RsecTests(unittest.TestCase):
   pass

