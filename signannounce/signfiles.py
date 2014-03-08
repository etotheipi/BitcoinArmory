import sys
import os
import getpass
import shutil
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

inDir = 'rawFiles'
outDir = 'filesToAnnounce'

###
if CLI_OPTIONS.testAnnounceCode:
   signAddress  = '1PpAJyNoocJt38Vcf4AfPffaxo76D4AAEe'
   announceName = 'testannounce.txt'
   pathPrefix   = 'https://s3.amazonaws.com/bitcoinarmory-testing/'
else:
   signAddress  = '1NWvhByxfTXPYNT4zMBmEY3VL8QJQtQoei'
   announceName = 'announce.txt'
   pathPrefix   = 'https://s3.amazonaws.com/bitcoinarmory-releases/'


announcePath = os.path.join(outDir, announceName)

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

def doSignFile(inFile, outFile):
   with open(inFile, 'rb') as f:
      sigBlock = ASv1CS(addrObj.binPrivKey32_Plain.toBinStr(), f.read())

   with open(outFile, 'wb') as f:
      f.write(sigBlock)



fileMappings = {}
longestID  = 0
longestURL = 0
print 'Reading file mapping...'
with open('filemap.txt','r') as f:
   for line in f.readlines():
      fname, fid = line.strip().split()
      inputPath = os.path.join(inDir, fname)
      if not os.path.exists(inputPath):
         print 'ERROR:  Could not find %s-file (%s)' % (fid, inputPath)
         exit(1)
      print '   Map: %s --> %s' % (fname, fid)
      


if os.path.exists(outDir):
   print 'Wiping old, announced files...'
   shutil.rmtree(outDir)
os.mkdir(outDir)



print 'Signing and copying files to %s directory...' % outDir
with open('filemap.txt','r') as f:
   for line in f.readlines():
      fname, fid = line.strip().split()
      inputPath = os.path.join(inDir, fname)
      outputPath = os.path.join(outDir, fname)

      if fname.endswith('.txt'):
         doSignFile(inputPath, outputPath)
      else:
         shutil.copy(inputPath, outputPath)

      fdata = open(outputPath, 'rb').read()
      fhash = binary_to_hex(sha256(fdata))
      fileMappings[fname] = [fid, fhash]
      longestID  = max(longestID,  len(fid))
      longestURL = max(longestURL, len(pathPrefix+fname))
      


      

print 'Creating digest file...'
digestFile = open(announcePath, 'w')

###
for fname,vals in fileMappings.iteritems():
   fid   = vals[0].ljust(longestID + 3)
   url   = (pathPrefix + fname).ljust(longestURL + 3)
   fhash = vals[1]
   digestFile.write('%s %s %s\n' % (fid, url, fhash))
digestFile.close()


print ''
print '------'
with open(announcePath, 'r') as f:
   dfile = f.read()
   print dfile
print '------'

print 'Please verify the above data to your satisfaction:'
raw_input('Hit <enter> when ready: ')
   



doSignFile(announcePath, os.path.join(outDir, announceName))


print ''
print open(announcePath, 'r').read()
print ''


print 'Done!'






