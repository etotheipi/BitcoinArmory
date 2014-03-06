import sys
import os
import getpass
sys.path.append('..')

from armoryengine.ALL import *
from jasvet import ASv1CS


if len(CLI_ARGS)<1:
   print 'Must specify a wallet file containing the signing key'
   exit(1)

wltPath = CLI_ARGS[0]
if not os.path.exists(wltPath):
   print 'Wallet file was not found (%s)' % wltPath
   exit(1)

###
if CLI_OPTIONS.testAnnounceCode:
   signAddress  = '1PpAJyNoocJt38Vcf4AfPffaxo76D4AAEe'
   announceName = 'testannounce.txt'
   pathPrefix   = 'https://s3.amazonaws.com/bitcoinarmory-testing/'
else:
   signAddress  = '1NWvhByxfTXPYNT4zMBmEY3VL8QJQtQoei'
   announceName = 'announce.txt'
   pathPrefix   = 'https://s3.amazonaws.com/bitcoinarmory-releases/'


###
wlt = PyBtcWallet().readWalletFile(wltPath)
if not wlt.hasAddr(signAddress):
   print 'Supplied wallet does not have the correct signing key'
   exit(1)



print 'Must unlock wallet to sign the announce file...'
passwd = SecureBinaryData(getpass.getpass('Wallet passphrase: '))
if not wlt.verifyPassphrase(passwd):
   print 'Invalid passphrase!'
   exit(1)

wlt.unlock(securePassphrase=passwd)
passwd.destroy()
addrObj = wlt.getAddrByHash160(addrStr_to_hash160(signAddress)[1])

def doSignFile(fname):
   with open(fname, 'rb') as f:
      sigBlock = ASv1CS(addrObj.binPrivKey32_Plain.toBinStr(), f.read())

   with open(fname, 'wb') as f:
      f.write(sigBlock)



fileMappings = {}
longestID  = 0
longestURL = 0
print 'Reading file mapping...'
with open('filemap.txt','r') as f:
   for line in f.readlines():
      fname, fid = line.strip().split()
      if not os.path.exists(fname):
         print 'ERROR:  Could not find %s-file (%s)' % (fid, fname)
         exit(1)
      print '   Map: %s --> %s' % (fname, fid)
      

print 'Do you want to sign any individual files before continuing? '
with open('filemap.txt','r') as f:
   for line in f.readlines():
      fname, fid = line.strip().split()

      fdata = open(fname, 'rb').read()
      if not fdata.strip().startswith('-----BEGIN'):
         yesno = raw_input('   Sign %s? [y/N] ' % fname)
         if yesno.lower().startswith('y'):
            doSignFile(fname)

      fdata = open(fname, 'rb').read()
      fhash = binary_to_hex(sha256(fdata))
      fileMappings[fname] = [fid, fhash]
      longestID  = max(longestID,  len(fid))
      longestURL = max(longestURL, len(pathPrefix+fname))
      


      

print 'Creating digest file...'
digestFile = open(announceName, 'w')

###
for fname,vals in fileMappings.iteritems():
   fid   = vals[0].ljust(longestID + 3)
   url   = (pathPrefix + fname).ljust(longestURL + 3)
   fhash = vals[1]
   digestFile.write('%s %s %s\n' % (fid, url, fhash))
digestFile.close()


print ''
print '------'
with open(announceName, 'r') as f:
   dfile = f.read()
   print dfile
print '------'

print 'Please verify the above data to your satisfaction:'
raw_input('Hit <enter> when ready: ')
   



doSignFile(announceName)


print ''
print open(announceName, 'r').read()
print ''


print 'Done!'






