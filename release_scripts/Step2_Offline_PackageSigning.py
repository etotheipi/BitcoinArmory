#! /usr/bin/python

# Take a directory full of things to be signed, and do the right thing.
# Make sure you cert-sign the windows installers, first
import sys
import os
import time
import shutil
from subprocess import Popen, PIPE


################################################################################
# DEFAULTS FOR RUNNING THIS SCRIPT
instDir   = '.' 
verType   = 'testing'
gpgKeyID  = 'FB596985'
builder   = 'Armory Technologies, Inc.'

gitRepo   = './BitcoinArmory' 
gitBranch    = 'testing'
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

print '*'*80
print 'Please confirm all parameters before continuing:'
print '   Dir with all the installers: "%s"' % instDir
print '   This is release of type    : "%s"' % verType
print '   Use the following GPG key  : "%s"' % gpgKeyID
print '   Builder for signing deb    : "%s"' % builder
print '   Git repo to be signed is   : "%s", branch: "%s"' % (gitRepo,gitBranch)
print '   Git user to tag release    : "%s" / <%s>' % (gituser, gitemail)
print ''
print '   Expected files to find     :'
for suf in suffixes:
   print '      ', suf

print ''
print '   Expected offline bundles to create: '
for bndl in offlinebundles:
   print '      ', bndl
print ''
print 'Make sure all non-deb files are ready before continuing...'
print ''

reply = raw_input('Does all this look correct? [Y/n]')
if not reply.lower().startswith('y'):
   print 'User aborted'
   exit(0)

print '*'*80
print ''

################################################################################
# Do some sanity checks to make sure things are in order before continuing
if len(sys.argv) > 1:
   instDir = sys.argv[1]

if not os.path.exists(instDir):
   print 'Installers dir does not exist!', instDir
   exit(1)

if not os.path.exists(gitRepo):
   print 'Git repo does not exist!', gitRepo
   exit(1)

# Check that we have offline bundle dependencies dirs for each
depsdirs = ['./armory_deps_%s_%s' % (dist,arch) for dist,arch in offlinebundles]
for fn in depsdirs:
   if not os.path.exists(fn):
      print 'Directory does not exist:', fn
      exit(1)

################################################################################
def execAndWait(cli_str, timeout=0):
   """ 
   There may actually still be references to this function where check_output
   would've been more appropriate.  But I didn't know about check_output at 
   the time...
   """
   process = Popen(cli_str, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
   pid = process.pid
   start = time.time()
   while process.poll() == None:
      time.sleep(0.1)
      if timeout>0 and (time.time() - start)>timeout:
         print 'Process exceeded timeout, killing it'
         killProcess(pid)
   out,err = process.communicate()
   return [out,err]


################################################################################
def getAllHashes(fnlist):
   hashes = []
   for fn in fnlist:
      out,err = execAndWait('sha256sum %s' % fn)
      hashes.append([fn, out.strip().split()[0]])
   return hashes
   

################################################################################
# Copied from armoryengine.py
def getVersionString(vquad, numPieces=4):
   vstr = '%d.%02d' % vquad[:2]
   if (vquad[2] > 0 or vquad[3] > 0) and numPieces>2:
      vstr += '.%d' % vquad[2]
   if vquad[3] > 0 and numPieces>3:
      vstr += '.%d' % vquad[3]
   return vstr

def readVersionString(verStr):
   verList = [int(piece) for piece in verStr.split('.')]
   while len(verList)<4:
      verList.append(0)
   return tuple(verList)

def getVersionInt(vquad, numPieces=4):
   vint  = int(vquad[0] * 1e7)
   vint += int(vquad[1] * 1e5)
   if numPieces>2:
      vint += int(vquad[2] * 1e3)
   if numPieces>3:
      vint += int(vquad[3])
   return vint


################################################################################
# Extract [osStr, subOS, armoryVersion, bits]
def parseInstallerName(fn):
   if fn[-4:] in ('.msi', '.exe', '.deb', '.app', '.dmg') or fn.endswith('.app.tar.gz'):
      try:
         pieces = fn.replace('-','_').split('_')
         osStr, subOS, bits, armVerInt, armVerStr = None,'',32,None,None
         for pc in pieces:
            if 'win' in pc.lower():
               osStr = 'Win'
            elif pc.endswith('.deb'):
               osStr = 'Linux'
            elif 'osx' in pc.lower():
               osStr = 'Mac'
   
            try:
               verpieces = [int(a) for a in pc.split('.')]
               # Could be Armory version or Ubuntu version, or nothing
               if verpieces[0]>=10:
                  subOS = pc 
               else:
                  while len(verpieces)<4:
                     verpieces.append(0)
                  armVerInt = getVersionInt(verpieces)
                  armVerStr = pc
            except Exception as e:
               pass

            if 'amd64' in pc or 'win64' in pc:
               bits = 64
               
         return osStr,subOS,bits,armVerInt,armVerStr

      except:
         print 'WARNING: Could not parse installer filename: %s' % fn

      
   return None
      

   
latestVerInt = 0
latestVerStr = ''

# Find the highest version number
for fn in os.listdir(instDir):
   fivevals = parseInstallerName(fn)
   if fivevals == None:
      continue;
   verint,verstr = fivevals[-2], fivevals[-1]
   if verint>latestVerInt:
      latestVerInt = verint
      latestVerStr = verstr

print '\nHighest version number found: ("%s", %d)' % (latestVerStr, latestVerInt)

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
   print 'Not all installers found; remaining %s' % str(suffixes)
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
         
   
print '\nAll installers to be hashed and signed:'
for fn in instFiles:
   print '   ',fn.ljust(45), ':', parseInstallerName(fn)

print '\nAll debian bundles to create:'
for deb in debbundles:
   print '   ',deb


for fn in instFiles:
   if fn.endswith('.deb'):
      cmd = 'dpkg-sig -s builder -m "%s" -k %s %s' % (builder,gpgKeyID,fn)
      print'EXEC: ', cmd
      execAndWait(cmd)
      print execAndWait('dpkg-sig --verify %s' % fn)[0]


for fn,depsdir,bundledir in debbundles:
   if os.path.exists(bundledir):
      print 'Removing old bundle directory: ', bundledir
      shutil.rmtree(bundledir)

   targz = '%s.tar.gz' % bundledir
   shutil.copytree(depsdir, bundledir)
   shutil.copy(fn, bundledir)
   execAndWait('tar -zcf %s %s/*' % (targz, bundledir))
   instFiles.append(targz)

instFiles.sort()

newHashes = getAllHashes(instFiles)
hashfilename = os.path.join(instDir, 'armory_%s-beta_sha256sum.txt' % latestVerStr)
hashfile = open(hashfilename, 'w')
for hline in newHashes:
   fn,h = hline
   basefn = os.path.basename(fn) 
   print '   ', h, basefn
   hashfile.write('%s %s\n' % (h,basefn))
hashfile.write('\n')
hashfile.close()

execAndWait('gpg -sa --clearsign --digest-algo SHA256 %s ' %  hashfilename)
os.remove(hashfilename)



# GIT SIGN
gittag  = 'v%s-%s' % (latestVerStr, verType)
print '*'*80
print 'About to tag and sign git repo with:'
print '   Tag:   ', gittag
print '   User:  ', gituser
print '   Email: ', gitemail

gitmsg = raw_input('Put your commit message here: ')

prevDir = os.getcwd()
os.chdir(gitRepo)
execAndWait('git checkout %s' % gitBranch)
execAndWait('git config user.name %s' % gituser)
execAndWait('git config user.email %s' % gitemail)
execAndWait('git tag -s %s -u %s -m "%s"' % (gittag, gpgKeyID, gitmsg))

out,err = execAndWait('git tag -v %s' % gittag)
print out
print err

os.chdir(prevDir)


print '*'*80
print 'CLEAN UP & BUNDLE EVERYTHING TOGETHER'
toExport = instFiles[:]
toExport.append(hashfilename + '.asc')
toExport.append("%s" % gitRepo)

execAndWait('tar -zcf signed_release_%s-%s.tar.gz %s' % (latestVerStr, verType, ' '.join(toExport)))


