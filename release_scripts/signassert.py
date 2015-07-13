#!/usr/bin/env python

################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

import getpass
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from armoryengine.PyBtcWallet import *
from armoryengine.ArmoryUtils import CLI_OPTIONS, CLI_ARGS
from jasvet import ASv1CS, readSigBlock, verifySignature

def signAssertFile(wltPath, assertFile):
   wlt = PyBtcWallet().readWalletFile(wltPath)
   if not wlt.hasAddr(signAddress):
      print 'Supplied wallet does not have the correct signing key'
      exit(1)

   if wlt.useEncryption and wlt.isLocked:
      print 'Must unlock wallet to sign the assert file...'
      passcnt = 0
      while True:
         passwd = SecureBinaryData(getpass.getpass('Wallet passphrase: '))
         if not wlt.verifyPassphrase(passwd):
            print 'Invalid passphrase!'
            if passcnt == 2:
               print 'Too many password attempts. Exiting.'
               exit(1)
            passcnt += 1
            continue
         break

      wlt.unlock(securePassphrase=passwd)
      passwd.destroy()

   addrObj = wlt.getAddrByHash160(addrStr_to_hash160(signAddress)[1])

   def doSignFile(inFile, outFile):
      with open(inFile, 'rb') as f:
         try:
            sigBlock = ASv1CS(addrObj.binPrivKey32_Plain.toBinStr(), f.read())
         except:
            print 'Error with call to sigBlock'
            exit(1)

      with open(outFile, 'wb') as f:
         f.write(sigBlock)

   doSignFile(assertFile, '%s.sig' % assertFile)

if __name__=='__main__':
   if not CLI_ARGS:
      print ('Must supply assert path (typically something like '
             'gitian-builder/sigs/name/release/signer/name-build.assert)')
      exit(1)
   assertFile = CLI_ARGS[0]
   wltCode = CLI_OPTIONS.signer.split('/')[0]
   signAddress = CLI_OPTIONS.signer.split('/')[1]
   wltPath = os.path.join(os.path.expanduser('~'), '.armory',
           'armory_%s_.wallet' % wltCode)
   if not os.path.exists(wltPath):
      print 'Wallet file was not found (%s)' % wltPath
      exit(1)
   signAssertFile(wltPath, assertFile)

   print ''
   print 'Verifying file'
   with open('%s.sig' % assertFile) as f:
      try:
         sig,msg = readSigBlock(f.read())
      except:
         print 'Error with call to readSigBlock'
         exit(1)
      try:
         addrB58 = verifySignature(sig, msg, 'v1', ord(ADDRBYTE))
      except:
         print 'Error with call to verifySignature'
         exit(1)
      print 'The address used to sign %s.sig was %s' % (assertFile, addrB58)

   print 'Done!'
