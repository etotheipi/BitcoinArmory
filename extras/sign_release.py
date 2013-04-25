#! /usr/bin/python

# Take a directory full of things to be signed, and do the right thing.
# Make sure you cert-sign the windows installers, first
import sys
import os
import time
import shutil

################################################################################
def execAndWait(cli_str, timeout=0, skipAsk=False):
   """ 
   There may actually still be references to this function where check_output
   would've been more appropriate.  But I didn't know about check_output at 
   the time...
   """
   if not skipAsk:
      raw_input('Confirm command: "%s"' % cli_str)
   from subprocess import Popen, PIPE
   process = Popen(cli_str, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
   pid = process.pid
   start = time.time()
   while process.poll() == None:
      time.sleep(0.1)
      if timeout>0 and (time.time() - start)>timeout:
         print 'Process exceeded timeout, killing it'
         killProcess(pid)
   out,err = process.communicate()
   if len(err.strip())>0:
      print '***ERROR in subprocess: cmd:', cli_str
      print '***ERROR in subprocess: err:', err
   return [out,err]


def getAllHashes(fnlist):
   hashes = []
   for fn in fnlist:
      out,err = execAndWait('sha256sum %s' % fn, skipAsk=True)
      hashes.append(out.strip())
   return hashes
   

def ASSERT(isTrue, txt):
   if not isTrue:
      print '***ERROR:', txt
      exit(1)


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



def getVersionNumber(fn):
   if fn.endswith('.msi') or fn.endswith('.deb') or fn.endswith('.dmg'):
      try:
         verQuad = readVersionString(fn.split('_')[1].split('-')[0])
         verInt  = getVersionInt(verQuad)
         return verInt, getVersionString(verQuad)
      except:
         print 'WARNING: Could not parse installer filename: %s' % fn

      
   return 0,''
      

instDir = '.' if len(sys.argv) < 2 else sys.argv[1]
ASSERT(os.path.exists(instDir), 'Directory does not exist')
   
suffixes = set(['_amd64.deb', '_i386.deb', '_win64.msi', '_win32.msi', '_OSX.dmg'])

latestVerInt = 0
latestVerStr = ''
for fn in os.listdir(instDir):
   vi,vs = getVersionNumber(fn)
   if vi>latestVerInt:
      latestVerInt = vi
      latestVerStr = vs
   for suf in suffixes:
      if fn.endswith(suf):
         suffixes.remove(suf)
         break

print '\nVersion number found: ("%s", %d)' % (latestVerStr, latestVerInt)
ASSERT(len(suffixes)==0, 'Not all installers found; remaining %s' % str(suffixes))

off32 = os.path.join(instDir, 'armory_deps_10.04_32bit')
off64 = os.path.join(instDir, 'armory_deps_10.04_64bit')
ASSERT(os.path.exists(off32), 'Need armory32 deps dir to create offline bundles')
ASSERT(os.path.exists(off64), 'Need armory64 deps dir to create offline bundles')


instFiles = []
deb32 = ''
deb64 = ''
for fn in os.listdir(instDir):
   fullfn =  os.path.join(instDir,fn)
   if getVersionNumber(fn)[0]==latestVerInt:
      instFiles.append(fullfn)

   if fn.endswith('.deb'):
      if 'i386' in fullfn:
         deb32 = fullfn
      elif 'amd64' in fullfn:
         deb64 = fullfn

print '\nAll installation files:'
for f in instFiles:
   print '   ', f
print 'All armory debs:'
print '   ', deb32
print '   ', deb64

print '\nPlease verify the pre-signed SHA256 hashes!'
hashes = getAllHashes(instFiles)
for h in hashes:
   print '   ',h.strip()

raw_input('Make sure the .msi files are signed... continue?')

print '\nSigning debian packages'
execAndWait('dpkg-sig -s builder -m "Alan C. Reiner" -k fb596985 %s' % deb32)
execAndWait('dpkg-sig -s builder -m "Alan C. Reiner" -k fb596985 %s' % deb64)

print '\nCopying signed debian pacakges to offline directories'
newOff32 = os.path.join(instDir, 'Armory_Offline_Bundle_10.04-32bit')
newOff64 = os.path.join(instDir, 'Armory_Offline_Bundle_10.04-64bit')

if os.path.exists(newOff32):
   shutil.rmtree(newOff32)

if os.path.exists(newOff64):
   shutil.rmtree(newOff64)

print '\nCopying trees'
shutil.copytree(off32, newOff32)
shutil.copytree(off64, newOff64)


shutil.copy(deb32, newOff32)
shutil.copy(deb64, newOff64)

# I freakin hate tar... it never does what I want... which is to not have 
# to os.chdir in a python script...
print '\nTarring the offline bundle directories...'
tar32 = 'armory_%s-beta_OfflineBundle_Ubuntu-10.04-32bit.tar.gz' % latestVerStr
tar64 = 'armory_%s-beta_OfflineBundle_Ubuntu-10.04-64bit.tar.gz' % latestVerStr
newOff32_abs = newOff32
newOff64_abs = os.path.abspath(newOff64)
prevdir = os.getcwd()
os.chdir(instDir)
execAndWait('tar -zcf %s Armory_Offline_Bundle_10.04-32bit/*' % (tar32))
execAndWait('tar -zcf %s Armory_Offline_Bundle_10.04-64bit/*' % (tar64))
os.chdir(prevdir)

instFiles.extend([os.path.join(instDir, tar32), os.path.join(instDir, tar64)])
instFiles.sort()
newHashes = getAllHashes(instFiles)
for h in newHashes:
   print '   ', h.strip()

hashfn = os.path.join(instDir, 'armory_%s-beta_sha256sum.txt' % latestVerStr)
hashfile = open(hashfn, 'w')
print newHashes
for hline in newHashes:
   if len(hline.strip()) > 0:
      h,fn = hline.split()
      basefn = os.path.basename(fn) 
      print '   ', h, basefn
      hashfile.write('%s %s\n' % (h,basefn))
hashfile.close()

execAndWait('gpg -s --output %s --clearsign %s ' % (hashfn+'.asc', hashfn))
os.remove(hashfn)





# GIT SIGN








