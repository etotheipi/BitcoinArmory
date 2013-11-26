#! /usr/bin/python

# Take a directory full of things to be signed, and do the right thing.
# Make sure you cert-sign the windows installers, first
import sys
import os
import time
import shutil
from subprocess import Popen, PIPE
from release_utils import *

#uploadlog = open('step2_log_%d.txt' % long(time.time()), 'w')
uploadlog = open('step2_log.txt', 'w')
def logprint(s):
   print s
   uploadlog.write(s + '\n')


################################################################################
# DEFAULTS FOR RUNNING THIS SCRIPT
instDir   = '.' 
verType   = 'testing'
gpgKeyID  = 'FB596985'
builder   = 'Armory Technologies, Inc.'

gitRepo   = './BitcoinArmory' 
gitBranch = 'testing'
gituser   = 'Armory Technologies, Inc.'
gitemail  = 'support@bitcoinarmory.com'

# We expect to find one file with each of the following suffixes
suffixes = set(['_10.04_amd64.deb', \
                '_10.04_i386.deb', \
                '_12.04_amd64.deb', \
                '_12.04_i386.deb', \
                '_win32.exe', \
                '.app.tar.gz'])

# We may have more installers than we want to make bundles.
# Specify just the ones you want bundled, here (and we expect
# to find an "armory_deps_XX.XX_arch" dir with the dependencies)
offlinebundles = [ \
                   ['10.04', 'i386' ], \
                   ['10.04', 'amd64'], \
                   ['12.04', 'i386' ], \
                   ['12.04', 'amd64']  \
                 ]

logprint('*'*80)
logprint('Please confirm all parameters before continuing:')
logprint('   Dir with all the installers: "%s"' % instDir)
logprint('   This is release of type    : "%s"' % verType)
logprint('   Use the following GPG key  : "%s"' % gpgKeyID)
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

################################################################################
# Do some sanity checks to make sure things are in order before continuing
if len(sys.argv) > 1:
   instDir = sys.argv[1]

if not os.path.exists(instDir):
   logprint('Installers dir does not exist! ' + instDir)
   exit(1)

if not os.path.exists(gitRepo):
   logprint('Git repo does not exist! ' + gitRepo)
   exit(1)

# Check that we have offline bundle dependencies dirs for each
depsdirs = ['./armory_deps_%s_%s' % (dist,arch) for dist,arch in offlinebundles]
for fn in depsdirs:
   if not os.path.exists(fn):
      logprint('Directory does not exist: ' + fn)
      exit(1)


# Grab the latest file version from the list   
latestVerInt,latestVerStr = getLatestVerFromList(os.listdir(instDir))


logprint('\nHighest version number found: ("%s", %d)' % (latestVerStr, latestVerInt))

# Verify we have at least one installer of each type at the same, latest version
for fn in os.listdir(instDir):
   fivevals = parseInstallerName(fn)
   if fivevals == None:
      continue

   verint = fivevals[-2]
   for suf in suffixes:
      if fn.endswith(suf)  and (verint == latestVerInt):
         suffixes.remove(suf)
         break

if not len(suffixes)==0:
   logprint('Not all installers found; remaining %s' % str(suffixes))
   exit(1)


instFiles  = []
debbundles = []
for fn in os.listdir(instDir):
   try:
      osStr,subOS,bits,verint,verstr = parseInstallerName(fn) 
   except:
      continue

   if not verint == latestVerInt:
      continue

   instFiles.append(fn)
   if osStr == 'Linux':
      arch = 'i386' if bits==32 else 'amd64'
      if [subOS, arch] in offlinebundles:
         newBundleDir = 'armory_%s-%s_OfflineBundle_%s-%dbit' % (verstr, verType, subOS, bits)
         debbundles.append( [fn, 'armory_deps_%s_%s'%(subOS, arch), newBundleDir])
         
   
logprint('\nAll installers to be hashed and signed:')
for fn in instFiles:
   logprint('   ' + fn.ljust(45) + ':' + str(parseInstallerName(fn)))

logprint('\nAll debian bundles to create:')
for deb in debbundles:
   logprint('   ' + str(deb))


for fn in instFiles:
   if fn.endswith('.deb'):
      cmd = 'dpkg-sig -s builder -m "%s" -k %s %s' % (builder,gpgKeyID,fn)
      logprint('EXEC: ' + cmd)
      execAndWait(cmd)
      logprint(execAndWait('dpkg-sig --verify %s' % fn)[0])


for fn,depsdir,bundledir in debbundles:
   if os.path.exists(bundledir):
      logprint('Removing old bundle directory: ' + bundledir)
      shutil.rmtree(bundledir)

   targz = '%s.tar.gz' % bundledir
   shutil.copytree(depsdir, bundledir)
   shutil.copy(fn, bundledir)
   execAndWait('tar -zcf %s %s/*' % (targz, bundledir))
   instFiles.append(targz)

instFiles.sort()

newHashes = getAllHashes(instFiles)
hashfilename = os.path.join(instDir, 'armory_%s-%s_sha256sum.txt' % (latestVerStr, verType))
hashfile = open(hashfilename, 'w')
for hline in newHashes:
   fn,h = hline
   basefn = os.path.basename(fn) 
   logprint('   ' + h + ' ' + basefn)
   hashfile.write('%s %s\n' % (h,basefn))
hashfile.write('\n')
hashfile.close()

execAndWait('gpg -sa --clearsign --digest-algo SHA256 %s ' %  hashfilename)
os.remove(hashfilename)



# GIT SIGN
gittag  = 'v%s-%s' % (latestVerStr, verType)
logprint('*'*80)
logprint('About to tag and sign git repo with:')
logprint('   Tag:   ' + gittag)
logprint('   User:  ' + gituser)
logprint('   Email: ' + gitemail)

gitmsg = raw_input('Put your commit message here: ')

prevDir = os.getcwd()
os.chdir(gitRepo)
execAndWait('git checkout %s' % gitBranch)
execAndWait('git config user.name "%s"' % gituser)
execAndWait('git config user.email %s' % gitemail)
execAndWait('git tag -s %s -u %s -m "%s"' % (gittag, gpgKeyID, gitmsg))

out,err = execAndWait('git tag -v %s' % gittag)
logprint(out)
logprint(err)

os.chdir(prevDir)


logprint('*'*80)
logprint('CLEAN UP & BUNDLE EVERYTHING TOGETHER')
toExport = instFiles[:]
toExport.append(hashfilename + '.asc')
toExport.append("%s" % gitRepo)

execAndWait('tar -zcf signed_release_%s-%s.tar.gz %s' % (latestVerStr, verType, ' '.join(toExport)))


