# stub
import subprocess
import os
import time
import shutil
import ast
import textwrap
from sys import argv
from release_utils import execAndWait

#####
from master_list import masterPkgList
#####

CLONE_URL = 'https://github.com/etotheipi/BitcoinArmory.git'

if len(argv)<3:
   print textwrap.dedent("""
      Script Arguments (* is optional)
            argv[0]   "python %s"
            argv[1]   version string,  "0.91.1"
            argv[2]   version type,    "-testing", "-beta", ""
            argv[3]*  output directory      (default ~ ./exportToOffline)
            argv[4]*  path to fetchlist.txt (default ~ ./fetchlist.txt)
            argv[5]*  unsigned announce dir (default ~ ./unsignedannounce)
            argv[6]*  Bitcoin Core SHA256SUMS.asc (default ~ "None")
            """) % argv[0]
   exit(1)

verStr  = argv[1]
verType = argv[2]
outDir  = argv[3] if len(argv)>3 else './exportToOffline'
annSrc  = argv[4] if len(argv)>5 else './unsignedannounce'
shaCore = argv[5] if len(argv)>6 else None

if os.path.exists(outDir):
   shutil.rmtree(outDir)
os.mkdir(outDir)

check_exists(annSrc)
if shaCore is not None:
   check_exists(shaCore)
   shutil.copy(shaCore, annDst)

# Grab the list of scp and cp commands from fetchlist
for pkgName,pkgDetails in masterPkgList.iteritems():
   cmd,cmdArgs = pkgDetails[0],pkgDetails[1:]
   if cmd=='cp':
      copyFrom = src % verStr
      copyTo = os.path.join(outDir,  % (verStr, verType))
      print 'Copying: %s --> %s' % (copyFrom, copyTo)
      shutil.copy(copyFrom, copyTo)
   if cmd=='scp':
      for usr,ip,port,path,rllist in cplist:
         for remoteSrc,localDst in rllist:
            remoteSrc = os.path.join(path, remoteSrc % verStr)
            hostPath = '%s@%s:%s' % (usr, ip, remoteSrc)
            localDst  = os.path.join(outDir, localDst % (verStr,verType))
            execAndWait(['scp', '-P', str(port), hostPath, localPath])

cloneDir = os.path.join(outDir, 'BitcoinArmory')
rscrDir  = os.path.join(outDir, 'release_scripts')
annDst   = os.path.join(outDir, 'unsignedannounce')

execAndWait(['git', 'clone', CLONE_URL, cloneDir])
shutil.copytree('../release_scripts', rscrDir)
shutil.copytree(annSrc, annDst)


