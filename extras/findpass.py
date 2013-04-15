
from sys import argv, path
import os
import time

path.append('..')
path.append('/usr/share/armory')
from armoryengine import *

if len(argv)<2:
   print '***USAGE: '
   print '    %s /path/to/wallet/file.wallet' % argv[0]
   exit(0)

walletPath = argv[1]

if not os.path.exists(walletPath):
   print 'Wallet does not exist:'
   print '  ', walletPath
   exit(0)


myEncryptedWlt = PyBtcWallet().readWalletFile(walletPath)






################################################################################
# Here is where I'm going to construct a list of a 100,000+ passwords to try.
def generatePassphraseList():
   seed = '1TfoP8bV5'
   alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
   passphraseList = []

   # First try all one-letter variations
   for i in range(len(seed)):
      for a in alphabet:
         passphraseList.append( seed[:i] + a + seed[i+1:] )

   print 'There are %d passphrases different by 1 letter.' % len(passphraseList)

   # And try all two-letter variants of it
   for i in range(len(seed)):
      for j in range(i+1, len(seed)):
         for ai in alphabet:
            for aj in alphabet:
               passphraseList.append( seed[:i] + ai + seed[i+1:j] + aj + seed[j+1:] )

   print 'There are %d passphrases different by 2 letters.' % len(passphraseList)
   return passphraseList


plist = generatePassphraseList()

totalTest = len(plist)
startTime = RightNow()
found = False
for i,p in enumerate(plist):
   isValid = myEncryptedWlt.verifyPassphrase( SecureBinaryData(p) ) 
      
   if isValid:
      # If the passphrase was wrong, it would error out, and not continue
      print 'Passphrase found!'
      print ''
      print '\t', p
      print ''
      print 'Thanks for using this script.  If you recovered coins because of it, '
      print 'please consider donating :) '
      print '   1ArmoryXcfq7TnCSuZa9fQjRYwJ4bkRKfv'
      print ''
      found = True
      break
   else:
      if i%100==0:
         telapsed = (RightNow() - startTime)/3600.
         print ('%d/%d passphrases tested... (%0.1f hours so far)'%(i,totalTest,telapsed)).rjust(40)
      pass


if not found:
   print ''
   print 'Script finished!'
   print 'Sorry, none of the provided passphrases were correct :('
   print ''

exit(0)


