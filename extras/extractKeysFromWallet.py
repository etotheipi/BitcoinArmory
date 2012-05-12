#! /usr/bin/python

#
#  IMPORTANT:  This script extracts *EVERY KEY & ADDR* out of your wallet.dat 
#              file and writes them to file!!   This is usually a terrible
#              idea, but I made the script to help myself explore the file
#              format.
#
#              Also, wallet.dat includes addresses you HAVE SEEN BUT DO NOT
#              OWN.  This means that many of the addresses (especially the 
#              ones without private keys) this script extracts don't actually
#              contribute anything to your wallet.
#
#  NOTE:       This was created before wallets ever used encryption.  It's 
#              probably fairly useless... but any unencrypted wallets created
#              before Bitcoin-Qt 0.6.0 would still be recoverable, even if 
#              corrupted
#
#
from sys import argv, path
path.append('..')
path.append('.')
from armoryengine import *
from CppBlockUtils import *


pubfile  = 'keylistpub.txt'
pairfile = 'keylistpair.txt'

if len(argv)<2:
   print 'USAGE:', argv[0], 'path/to/wallet.dat'
   for a in argv:
      print a
   exit(0)
else:
   wallet = open(argv[1], 'rb')

def pretty(theStr, width=32):
   if len(theStr) == 130:
      return ('\t\t' + theStr[2:2+64] + '\n\t\t' + theStr[2+64:])
   else:
      return ('\t\t' + theStr)
      

walletBytes = wallet.read()
pubout = open(pubfile,'w')
keyout = open(pairfile,'w')


print 'Wallet is %d bytes ' % len(walletBytes)

privKeyDict = {}
pubKeyDict = {}

for i in range(len(walletBytes)):
   if not walletBytes[i] == '\x04':
      continue
   else:
      try:
         potentialPubKey = SecureBinaryData(walletBytes[i:i+65])
         if CryptoECDSA().VerifyPublicKeyValid(potentialPubKey):
            fileloc = int_to_hex(i, widthBytes=4, endOut=BIGENDIAN)
            print '\nFound PUBLIC key in file (0x%08s) / ' % (fileloc,),
            hash160   = potentialPubKey.getHash160()
            addrStr   = hash160_to_addrStr(hash160)
            pubkeyHex = potentialPubKey.toHexStr()
            print ' Addr: %-34s' % (addrStr,), '   PrivKey:',

            # Now search for a private key that matches
            havePrivKey = False
            for j in [i-207,i-283]:
               if not walletBytes[j:j+2] == '\x04\x20':
                  continue
               startIdx = j+2
               endIdx = startIdx+32
               potentialPrivKey = SecureBinaryData(walletBytes[startIdx:endIdx])
               computedPub = CryptoECDSA().ComputePublicKey(potentialPrivKey)
               if( hash160 == computedPub.getHash160()):
                  havePrivKey = True
                  privkeyHex =  potentialPrivKey.toHexStr()
                  break
   
            if not havePrivKey:
               pubKeyDict[addrStr] = pubkeyHex
               print ' NOT_FOUND ',
            else:
               privKeyDict[addrStr] = (pubkeyHex, privkeyHex)
               print ' FOUND ',
      except:
         raise
         
for k,v in privKeyDict.iteritems():
   keyout.write('\nAddrStr : %s:\nPubX(BE): %s\nPubY(BE): %s\nPriv(BE): %s' % \
                           (k,v[0][2:2+64],v[0][2+64:2+64+64],v[1]))

for k,v in pubKeyDict.iteritems():
   pubout.write('\n%s:\n\tPubKey: %s' % (k,pretty(v)))

print ''
print ''
print 'Total number of PUBLIC  keys found:    ', len(pubKeyDict)
print 'Total number of PRIVATE keys (subset): ', len(privKeyDict)

print ''
print 'All public keys (including your own) saved to: ', pubfile
print 'All public/private keypairs stored in hex in:  ', pairfile
print ''
print '!!!'
print 'Please protect your keypair file.  It contains all the '
print 'information an attacker would need to steal your money!'
print '!!!'
print ''
      
pubout.close()
keyout.close()
