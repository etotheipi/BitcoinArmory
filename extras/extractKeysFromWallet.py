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
#
from sys import argv, path
path.append('..')
path.append('.')
from pybtcengine import *


pubfile  = 'keylistpub.txt'
pairfile = 'keylistpair.txt'

if len(argv)<2:
   print 'USAGE:', argv[0], 'path/to/wallet.dat'
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


privKeyDict = {}
pubKeyDict = {}

for i in range(len(walletBytes)):
   if not walletBytes[i] == '\x04':
      continue
   else:
      try:
         potentialPubKey = walletBytes[i+1:i+65]
         x = binary_to_int( potentialPubKey[:32], BIGENDIAN)
         y = binary_to_int( potentialPubKey[32:], BIGENDIAN)
         if isValidEcPoint(x,y):
            acct =  PyBtcAddress().createFromPublicKey((x,y))
            fileloc = int_to_hex(i, widthBytes=4, endOut=BIGENDIAN)
            print '\nFound PUBLIC key in file (0x%08s) / ' % (fileloc,),
            addrStr   = acct.calculateAddrStr()
            pubkeyHex = binary_to_hex(acct.pubKey_serialize()[1:])
            print ' Addr: %-34s' % (addrStr,), '   PrivKey:',

            # Now search for a private key that matches
            havePrivKey = False
            for j in [i-207,i-283]:
               if not walletBytes[j:j+2] == '\x04\x20':
                  continue
               startIdx = j+2
               endIdx = startIdx+32
               potentialPrivKeyBE = binary_to_int(walletBytes[startIdx:endIdx], BIGENDIAN)
               pubpointBE = EC_GenPt * potentialPrivKeyBE
               x2 = pubpointBE.x()
               y2 = pubpointBE.y()
               if( (x==x2 and y==y2)):
                  havePrivKey = True
                  privkeyHex =  binary_to_hex(walletBytes[startIdx:endIdx])
                  break
   
            if not havePrivKey:
               pubKeyDict[addrStr] = pubkeyHex
               print ' NOT_FOUND ',
            else:
               privKeyDict[addrStr] = (pubkeyHex, privkeyHex)
               print ' FOUND ',
      except:
         pass
         
for k,v in privKeyDict.iteritems():
   keyout.write('\n%s:\n\tPubX(BE): %s\n\tPubY(BE): %s\n\tPriv(BE): %s' % \
                           (k,v[0][:64],v[0][64:64+64],v[1]))

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





