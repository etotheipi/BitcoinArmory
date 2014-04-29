#! /usr/bin/python
import sys
import os
import time
import shutil
from subprocess import Popen, PIPE

################################################################################
def execAndWait(cli_str, timeout=0, usepipes=True, cwd=None):
   """ 
   There may actually still be references to this function where check_output
   would've been more appropriate.  But I didn't know about check_output at 
   the time...
   """
   if isinstance(cli_str, (list, tuple)):
      cli_str = ' '.join(cli_str)
   print 'Executing:', '"' + cli_str + '"'
   if usepipes:
      process = Popen(cli_str, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True, cwd=cwd)
   else:
      process = Popen(cli_str, shell=True, cwd=cwd)

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
# Extract [osName, verStr, verInt, verType, ext]
# Example ['winAll', '0.91.1', 91001000, 'rc1', '.exe']
def parseInstallerName(fn):
   pcs = fn.split('_')
   if not len(pcs)==3 or not pcs[0]=='armory':
      return None

   temp,verWhole,osNameExt = pcs[:]
   vpcs    = verWhole.split('-')
   verStr  = vpcs[0]
   verType = ('-'+vpcs[1]) if len(vpcs)>1 else ''
   epcs    = osNameExt.split('.')
   osName  = epcs[0]
   osExt   = '.'.join(epcs[1:])

   verQuad = readVersionString(verStr)
   verInt  = getVersionInt(verQuad)
   return [osName, verStr, verInt, verType, osExt]
        

################################################################################
# Parse filenames to return the latest version number present (and assoc type)
def getLatestVerFromList(filelist):
   latestVerInt = 0
   latestVerStr = ''
   verType = ''
   
   # Find the highest version number
   for fn in filelist:
      fivevals = parseInstallerName(fn)
      if fivevals is None:
         continue;

      verstr,verint,vertype = fivevals[1:4]
      if verint>latestVerInt:
         latestVerInt  = verint
         latestVerStr  = verstr
         latestVerType = vertype

   return (latestVerInt, latestVerStr, latestVerType)
   




################################################################################
def getAllHashes(fnlist):
   hashes = []
   for fn in fnlist:
      out,err = execAndWait('sha256sum %s' % fn)
      hashes.append([fn, out.strip().split()[0]])
   return hashes


################################################################################
def checkExists(fullPath, onDNE='exit'):
   fullPath = os.path.expanduser(fullPath)
   if os.path.exists(fullPath):
      print 'Found file: %s' % fullPath 
   else:
      print 'Path does not exist: %s' % fullPath
      if onDNE=='skip':
         return None
      elif onDNE=='exit':
         exit(1)

   return fullPath


def makeOutputDir(dirpath, wipe=True):
   if os.path.exists(dirpath) and wipe:
      shutil.rmtree(dirpath)

   if not os.path.exists(dirpath):
      os.makedirs(dirpath)
   return dirpath

    

