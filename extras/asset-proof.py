#! /usr/bin/python

# This script signs all addresses with a given message and write a json file containing a list of public addresses alonside the signature. The file can be given to auditors to verify the signatures and get the balance for this wallet.
# For more information, see https://github.com/olalonde/bitcoin-asset-proof 
#
# Usage:
# asset-proof.py  armory_ABCDEF_.wallet "Airbex Btc Assets" airbex-btc-assets.json
# more airbex-btc-assets.json
#{
#    "signatures": [
#        {
#            "signature": "HP0ehv2bUm8tSDJwFNiHzlN+Nyk0NP6ZyKsPm/emoAX4Ntyg/KRtPEFTieY3Yth3/7RbeZhVhEP52TdXi4QOY5c=", 
#            "address": "1ErNyayp5CdX7qBmmYjLuN2cFVpQJhf4t9"
#        }, 
#        {
#            "signature": "HKIwUnCadn+YUFzrcqtlnxdkkYqAOcT1n8/2fCWxNp1xObCFXEKPtd1Yr0N2th2tvRvHdCLgWsE81nAvLjxWHWk=", 
#            "address": "1PLvZNm1gZ7n32HHtgmVGgj8Zh5a3DxVbg"
#        }
#    ], 
#    "blockhash": "00000000000000000a94cd53c34e2cdfd2b7eab95e7b2d948e5ad200d863bcd4"
#    "currency": "BTC", 
#    "message": "Airbex Btc Assets"
#}

import sys
sys.path.append('..')
sys.path.append('.')

from armoryengine.ALL import *
from jasvet import ASv0
import getpass
from sys import argv
import os
import json

# Do not ever access the same wallet file from two different processes at the same time
print '\n'
#raw_input('PLEASE CLOSE ARMORY BEFORE RUNNING THIS SCRIPT!  (press enter to continue)\n')

if len(argv)<5:
   print 'USAGE: %s <wallet file> <asset-name> <asset-file> <blockhash>' % argv[0]
   print 'USAGE: %s armory_ABCDEF_.wallet "Airbex Btc Asset" airbex-btc-assets.json 00000000000000000a94cd53c34e2cdfd2b7eab95e7b2d948e5ad200d863bcd4' % argv[0]
   exit(0)

wltfile = argv[1]
message = argv[2]
outfilename = argv[3]
blockhash = argv[4]
messageToSign = blockhash + '|' + message
signatures = []

if not os.path.exists(wltfile):
   print 'Wallet file was not found: %s' % wltfile

wlt  = PyBtcWallet().readWalletFile(wltfile)

# If the wallet is encrypted, get the passphrase
if wlt.useEncryption:
   print 'Please enter your passphrase to unlock your wallet: '
   for ntries in range(3):
      passwd = SecureBinaryData(getpass.getpass('Wallet Passphrase: '))
      if wlt.verifyPassphrase(passwd):
         break;

      print 'Passphrase was incorrect!'
      if ntries==2:
         print 'Wallet could not be unlocked.  Aborting.'
         exit(0)

   print 'Correct Passphrase.  Unlocking wallet...'
   wlt.unlock(securePassphrase=passwd)
   passwd.destroy()


try:
   addrList = wlt.getLinearAddrList()
   print 'Addresses in this wallet:%s' % len(addrList)
   
   for addr in addrList[0:100]:
      privateKey = addr.binPrivKey32_Plain.toBinStr()
      signature = ASv0(privateKey, messageToSign)
      signatureb64 = signature['b64-signature']
      pair = {"address" : addr.getAddrStr(), "signature": signatureb64}
      signatures.append(pair)
      print '\t%s, %s' % (addr.getAddrStr(), signatureb64)

except WalletLockError:
   print 'Error signing transaction.  Wallet is somehow still locked'
   raise
except:
   print 'Error signing transsaction.  Unknown reason.'
   raise
   
out = {'blockhash': blockhash, 'message':message, 'currency':'BTC', 'signatures':signatures}

outDump = json.dumps(out, sort_keys = False, indent = 4)

outfile = open(outfilename, 'w')
outfile.write(outDump)
outfile.close()

print '\nAssets written to :'
print '\t', outfilename, '\n'

