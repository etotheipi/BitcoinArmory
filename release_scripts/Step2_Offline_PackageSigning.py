#! /usr/bin/python

# Take a directory full of things to be signed, and do the right thing.
# Make sure you cert-sign the windows installers, first
import sys
import os
import time
import shutil
import getpass
from subprocess import Popen, PIPE
from release_utils import *

from signannounce import signAnnounceFiles



uploadlog = open('step2_log.txt', 'w')
def logprint(s):
   print s
   uploadlog.write(s + '\n')


################################################################################
# DEFAULTS FOR RUNNING THIS SCRIPT
gpgKeyID  = 'FB596985'
btcWltID  = '2xT8467b'
builder   = 'Armory Technologies, Inc.'

gitRepo   = './BitcoinArmory' 
gitBranch = 'testing'
gituser   = 'Armory Technologies, Inc.'
gitemail  = 'contact@bitcoinarmory.com'

# We expect to find one file with each of the following suffixes
suffixes = set(['_raspbian.tar.gz', 
                '_12.04_64bit.deb',
                '_12.04_32bit.deb',
                '_winAll.exe', 
                '_osx.tar.gz'])


# Specify the names, and properties of each package that will be signed

# [PkgName] = [pkgSuffix, OSList, SubOSList, SupportedBits]
WindowsPkgs = {}
WindowsPkgs['Windows All'] = ['_winAll.exe', ['Windows'], ['All'], [32, 64]]

# [PkgName] = [pkgSuffix, OSList, SubOSList, SupportedBits]
MacOSXPkgs = {}
MacOSXPkgs['MacOSX All'] = ['.app.tar.gz', ['Mac/OSX'], ['All'], [64]]
   
# [PkgName] = [pkgSuffix, OSList, OSVersion, 32or64-bit]
LinuxPkgs = {}
LinuxPkgs['Ubuntu 12.04-64bit'] = ['_12.04-64bit.deb', ['Ubuntu', 'Debian'], ['12.04+'],  64]
LinuxPkgs['Ubuntu 12.04-32bit'] = ['_12.04-32bit.deb', ['Ubuntu', 'Debian'], ['12.04+'],  32]
LinuxPkgs['Raspberry Pi']       = ['_raspbian.tar.gz', ['Raspbian'],         ['Rpi'],     32]

# [BundleName] = [PkgName, DependenciesDir, Suffix]
OfflineBundles = {}
OfflineBundles['UbuntuBundle 12.04-64bit'] = ['Ubuntu 12.04-64bit', 'ubuntu_12.04-64_all_deps', 'OfflineUbuntu64']
OfflineBundles['UbuntuBundle 12.04-32bit'] = ['Ubuntu 12.04-32bit', 'ubuntu_12.04-32_all_deps', 'OfflineUbuntu32']
OfflineBundles['Raspberry Pi Bundle']      = ['Raspberry Pi',       'armory_raspbian_deps',     'OfflineRaspbian']
#OfflineBundles['Tails']                    = ['Tails OS',           'armory_tails64_deps',      'OfflineTails']
#LinuxPkgs['Tails 32bit']        = ['tails32.deb',      ['TailsOS'],          ['0.23'], 32]

# For now we are disabling these because they are enormous, holding the git repo with them
LinuxRaw = {}
#LinuxRaw['Ubuntu 12.04-32bit'] = ['_12.04-64bit.tar.gz', ['Ubuntu', 'Debian'], ['12.04'], 64]
#LinuxRaw['Ubuntu 12.04-32bit'] = ['_12.04-32bit.tar.gz', ['Ubuntu', 'Debian'], ['12.04'], 32]


################################################################################
# Do some sanity checks to make sure things are in order before continuing
if len(sys.argv) < 3:
   print '***ERROR: Must give a directory containing Armory installers'
   print 'USAGE: %s <installersdir>' % argv[0]
   exit(1)

instDir = sys.argv[1]
if not os.path.exists(instDir):
   logprint('Installers dir does not exist!' + instDir)
   exit(1)

if not os.path.exists(gitRepo):
   logprint('Git repo does not exist! ' + gitRepo)
   exit(1)


# Verify we have at least one installer of each type at the same, latest version
suffixMissing = suffixes[:]
for fn in os.listdir(instDir):
   fivevals = parseInstallerName(fn)
   if fivevals == None:
      continue

   verint = fivevals[-2]
   for suf in suffixMissing:
      if fn.endswith(suf)  and (verint == latestVerInt):
         suffixMissing.remove(suf)
         break


if not len(suffixMissing)==0:
   logprint('Not all installers found; remaining %s' % str(suffixMissing))
   exit(1)


# Check that we have offline bundle dependencies dirs for each
for name,trip in OfflineBundles.iteritems():
   pkgname,depsdir,suff = trip[:] 
   if not os.path.exists(depsdir):
      logprint('Directory does not exist: ' + fn)
      exit(1)
   else:
      print 'Found offline bundle deps dir: %s' % depsdir


# Check wallet exists for announcement signing
wltPath = os.path.expanduser('~/.armory/wallet_%s_.wallet' % btcWltID)
if not os.path.exists(wltPath):
   logprint('Wallet for signing announcements does not exist: %s' % wltPath)
   exit(1)


# Grab the latest file version from the list   
latestVerInt,latestVerStr,latestVerType = getLatestVerFromList2(os.listdir(instDir))

logprint('*'*80)
logprint('Please confirm all parameters before continuing:')
logprint('   Dir with all the installers: "%s"' % instDir)
logprint('   Detected Version String    : "%s"' % latestVerStr)
logprint('   This is release of type    : "%s"' % latestVerType)
logprint('   Use the following GPG key  : "%s"' % gpgKeyID)
logprint('   Use the following wallet   : "%s"' % wltPath)
logprint('   Builder for signing deb    : "%s"' % builder)
logprint('   Git repo to be signed is   : "%s", branch: "%s"' % (gitRepo,gitBranch))
logprint('   Git user to tag release    : "%s" / <%s>' % (gituser, gitemail))
logprint('')
logprint('   Expected files to find     :')
for suf in suffixes:
   logprint('      ' + suf)

logprint('')
logprint('   Expected offline bundles to create: ')
for bndl in offlinebundles:
   logprint('      ' + str(bndl))
logprint('')
logprint('Make sure all non-deb files are ready before continuing...')
logprint('')

reply = raw_input('Does all this look correct? [Y/n]')
if not reply.lower().startswith('y'):
   logprint('User aborted')
   exit(0)

logprint('*'*80)
logprint('')






instFiles  = []
#debbundles = []
for fn in os.listdir(instDir):
   try:
      osName,verStr,verInt,verType,osExt = parseInstallerName2(fn) 
   except:
      continue

   if not verint == latestVerInt:
      continue

   instFiles.append(fn)
   #if osStr == 'Linux':
      #arch = 'i386' if bits==32 else 'amd64'
      #if [subOS, arch] in offlinebundles:
         #newBundleDir = 'armory_%s-%s_OfflineBundle_%s-%dbit' % (verstr, verType, subOS, bits)
         #debbundles.append( [fn, 'armory_deps_%s_%s'%(subOS, arch), newBundleDir])
         
   
logprint('\nAll installers to be hashed and signed:')
for fn in instFiles:
   logprint('   ' + fn.ljust(45) + ':' + str(parseInstallerName2(fn)))


for fn in instFiles:
   if fn.endswith('.deb'):
      cmd = 'dpkg-sig -s builder -m "%s" -k %s %s' % (builder,gpgKeyID,fn)
      logprint('EXEC: ' + cmd)
      execAndWait(cmd)
      logprint(execAndWait('dpkg-sig --verify %s' % fn)[0])


"""
for fn,depsdir,bundledir in debbundles:
   if os.path.exists(bundledir):
      logprint('Removing old bundle directory: ' + bundledir)
      shutil.rmtree(bundledir)

   targz = '%s.tar.gz' % bundledir
   shutil.copytree(depsdir, bundledir)
   shutil.copy(fn, bundledir)
   execAndWait('tar -zcf %s %s/*' % (targz, bundledir))
   instFiles.append(targz)
"""

################################################################################
# Create Offline Bundles
OfflineBundles['UbuntuBundle 12.04-64bit'] = ['Ubuntu 12.04-64bit', 'ubuntu_12.04-64_all_deps']
for bundleName,trip in OfflineBundles.iteritems():
   pkgName,depsdir,suff = trip[:]

   newDir = 'armory_%s%s_%s' % (latestVerStr, latestVerType, suff)
   newTar = newDir + '.tar.gz'
   
   if os.path.exists(newDir):
      logprint('Removing old bundle directory: ' + newDir)
      shutil.rmtree(bundledir)

   shutil.copytree(depsdir, newDir)
   shutil.copy(fn, bundledir)
   execAndWait('tar -zcf %s %s/*' % (targz, bundledir))
   instFiles.append(targz)

instFiles.sort()

newHashes = getAllHashes(instFiles)
hashfilename = os.path.join(instDir, 'armory_%s%s_sha256sum.txt' % (latestVerStr, latestVerType))
with open(hashfilename, 'w') as hashfile:
   for fn,sha2 in newHashes:
      basefn = os.path.basename(fn) 
      logprint('   ' + sha2 + ' ' + basefn)
      hashfile.write('%s %s\n' % (sha2,basefn))
   hashfile.write('\n')

execAndWait('gpg -sa --clearsign --digest-algo SHA256 %s ' %  hashfilename)
os.remove(hashfilename)



################################################################################
################################################################################
# Now update the announcements


# GIT SIGN
gittag  = 'v%s%s' % (latestVerStr, latestVerType)
logprint('*'*80)
logprint('About to tag and sign git repo with:')
logprint('   Tag:   ' + gittag)
logprint('   User:  ' + gituser)
logprint('   Email: ' + gitemail)

gitmsg = raw_input('Put your commit message here: ')

os.chdir(gitRepo)
execAndWait('git checkout %s' % gitBranch, cwd=gitRepo)
execAndWait('git config user.name "%s"' % gituser, cwd=gitRepo)
execAndWait('git config user.email %s' % gitemail, cwd=gitRepo)
execAndWait('git tag -s %s -u %s -m "%s"' % (gittag, gpgKeyID, gitmsg), cwd=gitRepo)

out,err = execAndWait('git tag -v %s' % gittag, cwd=gitRepo)
logprint(out)
logprint(err)


logprint('*'*80)
logprint('CLEAN UP & BUNDLE EVERYTHING TOGETHER')
toExport = instFiles[:]
toExport.append(hashfilename + '.asc')
toExport.append("%s" % gitRepo)

execAndWait('tar -zcf signed_release_%s%s.tar.gz %s' % (latestVerStr, latestVerType, ' '.join(toExport)))


