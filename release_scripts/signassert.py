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

from armoryengine.ALL import *
from jasvet import ASv1CS, readSigBlock, verifySignature

def signAssertFile(wltPath, assertFile):
   wlt = PyBtcWallet().readWalletFile(wltPath)
   if not wlt.hasAddr(signAddress):
      print 'Supplied wallet does not have the correct signing key'
      exit(1)

   print 'Must unlock wallet to sign the assert file...'
   while True:
      passwd = SecureBinaryData(getpass.getpass('Wallet passphrase: '))
      if not wlt.verifyPassphrase(passwd):
         print 'Invalid passphrase!'
         continue
      break

   wlt.unlock(securePassphrase=passwd)
   passwd.destroy()

   addrObj = wlt.getAddrByHash160(addrStr_to_hash160(signAddress)[1])

   def doSignFile(inFile, outFile):
      with open(inFile, 'rb') as f:
         sigBlock = ASv1CS(addrObj.binPrivKey32_Plain.toBinStr(), f.read())

      with open(outFile, 'wb') as f:
         f.write(sigBlock)

   doSignFile(assertFile, '%s.sig' % assertFile)

if __name__=='__main__':
   assertFile = sys.argv[1]
   wltCode = raw_input('Enter your Armory wallet code (e.g. CeL6h2HD): ')
   signAddress = raw_input('Enter an address in the wallet with which to sign: ')
   wltPath = os.path.join(os.path.expanduser('~'), '.armory',
           'armory_%s_.wallet' % wltCode)
   if not os.path.exists(wltPath):
      print 'Wallet file was not found (%s)' % wltPath
      exit(1)
   signAssertFile(wltPath, assertFile)

   print ''
   print 'Verifying file'
   with open('%s.sig' % assertFile) as f:
      sig,msg = readSigBlock(f.read())
      addrB58 = verifySignature(sig, msg, 'v1', ord(ADDRBYTE))
      print 'Sign addr for:', '%s.sig' % assertFile, addrB58

   print 'Done!'
