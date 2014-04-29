# stub
import subprocess
import os
import time
import shutil
import ast
from sys import argv
from release_utils import *

#####
from release_settings import getReleaseParams, getMasterPackageList
#####

masterPkgList = getMasterPackageList()

CLONE_URL = 'https://github.com/etotheipi/BitcoinArmory.git'

if len(argv)<3:
   import textwrap
   print textwrap.dedent("""
      Script Arguments (* is optional)
            argv[0]   "python %s"
            argv[1]   version string,  "0.91.1"
            argv[2]   version type,    "-testing", "-beta", ""
            argv[3]*  output directory      (default ~ ./exportToOffline)
            argv[4]*  unsigned announce dir (default ~ ./unsignedannounce)
            argv[5]*  Bitcoin Core SHA256SUMS.asc (default ~ "None")
            """) % argv[0]
   exit(1)

print argv

verStr  = argv[1]
verType = argv[2]
outDir  = argv[3] if len(argv)>3 else './exportToOffline'
annSrc  = argv[4] if len(argv)>4 else './unsignedannounce'
shaCore = argv[5] if len(argv)>5 else None

instDst  = os.path.join(outDir, 'installers')
cloneDir = os.path.join(outDir, 'BitcoinArmory')
rscrDir  = os.path.join(outDir, 'release_scripts')
annDst   = os.path.join(outDir, 'unsignedannounce')

if os.path.exists(outDir):
   shutil.rmtree(outDir)
os.makedirs(instDst)  # will create outdir and installers dir

# Check that unsigned announcements dir exists
checkExists(annSrc)

# Throw in the Bitcoin Core hashes file if supplied
if shaCore is not None:
   checkExists(shaCore)
   shutil.copy(shaCore, os.path.join(outDir,'SHA256SUMS.asc'))

# Grab the list of scp and cp commands from fetchlist
for pkgName,pkgInfo in masterPkgList.iteritems():
   fetchCmd = pkgInfo['FetchFrom']
   cmd,cmdArgs = fetchCmd[0],fetchCmd[1:]
   localFn = 'armory_%s%s_%s' % (verStr, verType, pkgInfo['FileSuffix'])
   copyTo = os.path.join(instDst, localFn)
   if cmd=='cp':
      assert(len(cmdArgs)==1) 
      copyFrom = checkExists(cmdArgs[0] % verStr)
      print 'Copying: %s --> %s' % (copyFrom, copyTo)
      shutil.copy(copyFrom, copyTo)
   if cmd=='scp':
      assert(len(cmdArgs)==4) 
      usr,ip,port,src = cmdArgs
      remoteSrc = src % verStr
      hostPath = '%s@%s:%s' % (usr, ip, remoteSrc)
      execAndWait(['scp', '-P', str(port), hostPath, copyTo])


execAndWait(['git', 'clone', CLONE_URL, cloneDir])
shutil.copytree('../release_scripts', rscrDir)
shutil.copytree(annSrc, annDst)


