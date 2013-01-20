
from armoryengine import *
from sys import argv
import os
import time


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

# Reads the scrabble dictionary file, strips whitespace, and converts to lowercase
words = [line.strip().lower() for line in open('dictionary.txt','r').readlines()]

# Capitalize the first letter of each word, add the 56874
passphraseList = [w[0].upper()+w[1:]+'56874' for w in words]

totalTest = len(passphraseList)
startTime = RightNow()
found = False
for i,p in enumerate(passphraseList):
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


