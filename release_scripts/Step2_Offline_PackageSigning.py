#! /usr/bin/python

# Take a directory full of things to be signed, and do the right thing.
# Make sure you cert-sign the windows installers, first
import os
import time
import shutil
import getpass
from sys import argv
from subprocess import Popen, PIPE
from release_utils import *

#####
from release_settings import getReleaseParams, getMasterPackageList
#####


if len(argv)<4:
   import textwrap
   print textwrap.dedent("""
      Script Arguments (* is optional)
         argv[0]   "python %s"
         argv[1]   inputDir  (from Step1)
         argv[2]   outputDir (for Step3)
         argv[3]   bundleDir 
         argv[4]   isTestingRelease  (default ~ "0")
         argv[5]*  git branch to tag (default ~ "master")
         argv[6]*  use testing settings (default ~ "0")
            """) % argv[0]
   exit(1)

# Process CLI args
inDir      = checkExists(argv[1])
outDir     = argv[2]
bundleDir  = argv[3]
isTestRelease = (len(argv)>4 and not argv[4]=="0")
gitBranch  = 'master' if len(argv)<5 else argv[5]
testParams = (len(argv)>6 and not argv[6]=="0")
outDir = makeOutputDir(outDir, wipe=False)


masterPkgList = getMasterPackageList()
RELEASE = getReleaseParams(testParams)


# Other defaults -- same for all Armory releases
builder        = RELEASE['Builder']
gituser        = RELEASE['GitUser']
gitemail       = RELEASE['GitEmail']
signAddress    = RELEASE['SignAddr']
announceName   = RELEASE['AnnounceFile']
bucketPrefix   = RELEASE['BucketPrefix']
bucketAnnounce = bucketPrefix + RELEASE['BucketAnnounce']
bucketReleases = bucketPrefix + RELEASE['BucketReleases']
gpgKeyID       = RELEASE['GPGKeyID']
btcWltID       = RELEASE['BTCWltID']


# Setup dual writing to console and log file
writelog = open('step2_log.txt', 'w')
def logprint(s):
   print s
   writelog.write(s + '\n')


# Check that all the paths expected from step 1 actually exist
srcGitRepo  = checkExists(os.path.join(inDir, 'BitcoinArmory'))
srcInstalls = checkExists(os.path.join(inDir, 'installers'))
srcAnnounce = checkExists(os.path.join(inDir, 'unsignedannounce'))
srcCoreSHA  = checkExists(os.path.join(inDir, 'SHA256SUMS.asc'), 'skip')

# Check that all the paths expected from step 1 actually exist
dstGitRepo  =               os.path.join(outDir, 'BitcoinArmory')
dstInstalls = makeOutputDir(os.path.join(outDir, 'installers'))
dstAnnounce = makeOutputDir(os.path.join(outDir, 'signedannounce'))

# Scan the list of files in installers dir to get latest 
instList = [fn for fn in os.listdir(srcInstalls)]
topVerInt,topVerStr,topVerType = getLatestVerFromList(instList)

# A shortcut to get the full path of the installer filename for a given pkg
def getSrcPath(pkgName, suffixStr='FileSuffix'):
   pkgSuffix = masterPkgList[pkgName][suffixStr]
   fname = 'armory_%s%s_%s' % (topVerStr, topVerType, pkgSuffix)
   return os.path.join(srcInstalls, fname)

def getDstPath(pkgName, suffixStr='FileSuffix'):
   if pkgName=='SHAFILE_TXT':
      pkgSuffix = 'sha256sum.txt'
   elif pkgName=='SHAFILE_ASC':
      pkgSuffix = 'sha256sum.txt.asc'
   else:
      pkgSuffix = masterPkgList[pkgName][suffixStr]

   fname = 'armory_%s%s_%s' % (topVerStr, topVerType, pkgSuffix)
   return os.path.join(dstInstalls, fname)

# Check that all the master packages exist, as well as any bundle dirs
for pkgName,pkgInfo in masterPkgList.iteritems():
   checkExists(getSrcPath(pkgName))
   logprint('Regular pacakge "%s": %s' % (pkgName.ljust(20), getSrcPath(pkgName)))

   if pkgInfo['HasBundle']:
      logprint('Offline bundle  "%s": %s' % (pkgName.ljust(20), pkgInfo['BundleDeps']))
      checkExists(os.path.join(bundleDir, pkgInfo['BundleDeps']))
   
# Check for wallet in ARMORY_HOME_DIR
wltPath = checkExists('~/.armory/armory_%s_.wallet' % btcWltID)

logprint('*'*80)
logprint('Please confirm all parameters before continuing:')
logprint('   Dir with all the installers: "%s"' % srcInstalls)
logprint('   Dir with announcement data : "%s"' % srcAnnounce)
logprint('   Dir with fresh git checkout: "%s"' % srcGitRepo)
logprint('   Path to Bitcoin Core SHA256: "%s"' % str(srcCoreSHA))
logprint('   Detected Version Integer   : "%s"' % topVerInt)
logprint('   Detected Version String    : "%s"' % topVerStr)
logprint('   This is release of type    : "%s"' % topVerType)
logprint('   Use the following GPG key  : "%s"' % gpgKeyID)
logprint('   Use the following wallet   : "%s"' % wltPath)
logprint('   Builder for signing deb    : "%s"' % builder)
logprint('   Git branch to be signed is : "%s"' % gitBranch)
logprint('   Git user to tag release    : "%s" / <%s>' % (gituser, gitemail))


if srcCoreSHA:
   logprint('\n'*2)
   logprint('*'*80)
   logprint('Output of gpg-verify on SHA256SUMS')
   logprint(execAndWait('gpg -v %s' % srcCoreSHA)[0])
   logprint('*'*80)
   logprint('Contents of SHA256SUM.asc:')
   logprint(open(srcCoreSHA,'r').read())
   logprint('*'*80)
   logprint('Contents of dllinks.txt (to be signed):')
   logprint(open(os.path.join(srcAnnounce, 'dllinks.txt'),'r').read())
   logprint('\n')
   if raw_input('Visually verify -- good?  [Y/n]: ').lower().startswith('n'):
      exit(1)


reply = raw_input('Does all this look correct? [Y/n]')
if reply.lower().startswith('n'):
   logprint('User aborted')
   exit(0)

logprint('*'*80)
logprint('')
         

# First thing: sign all debs
logprint('Signing all .deb files:')
for pkgName in masterPkgList:
   pkgSrc = getSrcPath(pkgName)
   pkgDst = getDstPath(pkgName)
   shutil.copy(pkgSrc, pkgDst)
   if pkgDst.endswith('.deb'):
      logprint('Signing: ' + pkgDst)
      cmd = 'dpkg-sig -s builder -m "%s" -k %s %s' % (builder, gpgKeyID, pkgDst)
      logprint('EXEC: ' + cmd)
      execAndWait(cmd)
      logprint(execAndWait('dpkg-sig --verify %s' % pkgDst)[0])



################################################################################
logprint('Creating bundles:')
for pkgName,pkgInfo in masterPkgList.iteritems():
   if not pkgInfo['HasBundle']:
      continue

   bpath = getDstPath(pkgName, 'BundleSuffix')
   tempDir  = 'OfflineBundle'
   if os.path.exists(tempDir):
      logprint('Removing temp bundle directory: ' + tempDir)
      shutil.rmtree(tempDir)

   logprint('\tCopying bundle dependencies')
   shutil.copytree(os.path.join(bundleDir, pkgInfo['BundleDeps']), tempDir)
   shutil.copy(getSrcPath(pkgName), tempDir)
   execAndWait('tar -zcf %s %s/*' % (bpath, tempDir))
      
   if os.path.exists(tempDir):
      logprint('Removing temp bundle directory: ' + tempDir)
      shutil.rmtree(tempDir)


# Finally, create the signed hashes file
filesToSign = []
for pkgName,pkgInfo in masterPkgList.iteritems():
   filesToSign.append(getDstPath(pkgName))
   if pkgInfo['HasBundle']:
      filesToSign.append(getDstPath(pkgName, 'BundleSuffix'))
      

logprint('All files to be included in hashes file:')
for f in filesToSign:
   logprint('   ' + f)
   

newHashes = getAllHashes(filesToSign)
#hashname = 'armory_%s%s_sha256sum.txt' % (topVerStr, topVerType)
hashname = getDstPath('SHAFILE_TXT')
hashpath = os.path.join(dstInstalls, hashname)
with open(hashpath, 'w') as hashfile:
   for fn,sha2 in newHashes:
      basefn = os.path.basename(fn) 
      logprint('   ' + sha2 + ' ' + basefn)
      hashfile.write('%s %s\n' % (sha2,basefn))
   hashfile.write('\n')

execAndWait('gpg -sa --clearsign --digest-algo SHA256 %s ' %  hashpath)
os.remove(hashpath)



################################################################################
################################################################################
# Now update the announcements (require armoryengine)
sys.path.append('/usr/lib/armory')
from armoryengine.ALL import PyBtcWallet, binary_to_hex, hex_to_binary, \
                             SecureBinaryData, addrStr_to_hash160, sha256, \
                             ADDRBYTE
from jasvet import ASv1CS, readSigBlock, verifySignature
   
origDLFile   = os.path.join(srcAnnounce, 'dllinks.txt')
newDLFile    = os.path.join(srcAnnounce, 'dllinks_temp.txt')
announcePath = os.path.join(dstAnnounce, announceName)

# Checking that wallet has signing key, and user can unlock wallet
wlt = PyBtcWallet().readWalletFile(wltPath)
if not wlt.hasAddr(signAddress):
   print 'Supplied wallet does not have the correct signing key'
   exit(1)

print 'Must unlock wallet to sign the announce file...'
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

def getFileHash(baseDir, fname):
   fullpath = os.path.join(baseDir, fn)
   with open(fullpath, 'rb') as fdata:
      return binary_to_hex(sha256(fdata.read()))

# Now compute the hashes of the files in the signed-installer dir, write out
fnew = open(newDLFile, 'w')
fnew.write(open(origDLFile, 'r').read())
fnew.write('\n')
typeSuffix = 'Testing' if isTestRelease else ''
for pkgName,pkgInfo in masterPkgList.iteritems():
   fn = 'armory_%s%s_%s' % (topVerStr, topVerType, pkgInfo['FileSuffix'])
   outputStr = ['Armory%s' % typeSuffix, 
                topVerStr, 
                pkgInfo['OSNameLink'],
                pkgInfo['OSVarLink'],
                pkgInfo['OSArchLink'],
                os.path.join(bucketReleases, fn),                       
                getFileHash(dstInstalls, fn)]
   fnew.write(' '.join(outputStr) + '\n')

   if pkgInfo['HasBundle']:
      # Note different 4th arg for OSVar -- because bundles have different reqts
      fn = 'armory_%s%s_%s' % (topVerStr, topVerType, pkgInfo['BundleSuffix'])
      outputStr = ['ArmoryOffline%s' % typeSuffix, 
                   topVerStr, 
                   pkgInfo['OSNameLink'],
                   pkgInfo['BundleOSVar'],
                   pkgInfo['OSArchLink'],
                   os.path.join(bucketReleases, fn),                       
                   getFileHash(dstInstalls, fn)]
      fnew.write(' '.join(outputStr) + '\n')

fnew.write('\n')
fnew.close()



fileMappings = {}
longestID  = 0
longestURL = 0
print 'Reading file mapping...'
with open('announcemap.txt','r') as f:
   for line in f.readlines():
      fname, fid = line.strip().split()
      inputPath = os.path.join(srcAnnounce, fname)
      if not os.path.exists(inputPath):
         print 'ERROR:  Could not find %s-file (%s)' % (fid, inputPath)
         exit(1)
      print '   Map: %s --> %s' % (fname, fid)
      


print 'Signing and copying files to %s directory...' % dstAnnounce
with open('announcemap.txt','r') as f:
   for line in f.readlines():
      fname, fid = line.strip().split()

      inputPath = os.path.join(srcAnnounce, fname)
      outputPath = os.path.join(dstAnnounce, fname)

      # If we're using a modified DL file
      if fname=='dllinks.txt':
         inputPath = newDLFile

      if fname.endswith('.txt'):
         doSignFile(inputPath, outputPath)
      else:
         shutil.copy(inputPath, outputPath)

      fdata = open(outputPath, 'rb').read()
      fhash = binary_to_hex(sha256(fdata))
      fileMappings[fname] = [fid, fhash]
      longestID  = max(longestID,  len(fid))
      longestURL = max(longestURL, len(bucketAnnounce + fname))
      


print 'Creating digest file...'
digestFile = open(announcePath, 'w')

###
for fname,vals in fileMappings.iteritems():
   fid   = vals[0].ljust(longestID + 3)
   url   = (bucketAnnounce + fname).ljust(longestURL + 3)
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
   

doSignFile(announcePath, os.path.join(dstAnnounce, announceName))


print '*'*80
print open(announcePath, 'r').read()
print '*'*80


print ''
print 'Verifying files'
for fname,vals in fileMappings.iteritems():
   if 'bootstrap' in fname:
      continue
   with open(os.path.join(dstAnnounce, fname), 'rb') as f:
      sig,msg = readSigBlock(f.read())
      addrB58 = verifySignature(sig, msg, 'v1', ord(ADDRBYTE))
      print 'Sign addr for:', vals[0].ljust(longestID+3), addrB58
   


print 'Done!'



################################################################################
# GIT SIGN
gittag  = 'v%s%s' % (topVerStr, topVerType)
logprint('*'*80)
logprint('About to tag and sign git repo with:')
logprint('   Tag:   ' + gittag)
logprint('   User:  ' + gituser)
logprint('   Email: ' + gitemail)

gitmsg = raw_input('Put your commit message here: ')
if os.path.exists(dstGitRepo):
   shutil.rmtree(dstGitRepo)
shutil.copytree(srcGitRepo, dstGitRepo)
os.chdir(dstGitRepo)
execAndWait('git checkout %s' % gitBranch, cwd=dstGitRepo)
execAndWait('git config user.name "%s"' % gituser, cwd=dstGitRepo)
execAndWait('git config user.email %s' % gitemail, cwd=dstGitRepo)
execAndWait('git tag -s %s -u %s -m "%s"' % (gittag, gpgKeyID, gitmsg), cwd=dstGitRepo)

out,err = execAndWait('git tag -v %s' % gittag, cwd=dstGitRepo)
logprint(out)
logprint(err)


logprint('*'*80)
#logprint('CLEAN UP & BUNDLE EVERYTHING TOGETHER')
#toExport = instFiles[:]
#toExport.append(hashpath + '.asc')
#toExport.append("%s" % dstGitRepo)

#execAndWait('tar -zcf signed_release_%s%s.tar.gz %s' % (topVerStr, topVerType, ' '.join(toExport)))





