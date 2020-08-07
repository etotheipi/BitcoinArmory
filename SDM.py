################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
import inspect
import os.path
import socket
import stat
import time
from urllib import quote_plus as urlquote
from threading import Event
from CppBlockUtils import SecureBinaryData, CryptoECDSA, NodeStatusStruct, \
   RpcStatus_Disabled, RpcStatus_Online, RpcStatus_Error_28, \
   NodeStatus_Online, NodeStatus_Offline, ChainStatus_Unknown, ChainStatus_Syncing
   
from armoryengine.ArmoryUtils import BITCOIN_PORT, LOGERROR, hex_to_binary, \
   ARMORY_INFO_SIGN_PUBLICKEY, LOGINFO, BTC_HOME_DIR, LOGDEBUG, OS_MACOSX, \
   OS_WINDOWS, OS_LINUX, SystemSpecs, subprocess_check_output, LOGEXCEPT, \
   FileExistsError, OS_VARIANT, BITCOIN_RPC_PORT, binary_to_base58, isASCII, \
   USE_TESTNET, USE_REGTEST, GIGABYTE, launchProcess, killProcessTree, killProcess, \
   LOGWARN, RightNow, HOUR, PyBackgroundThread, touchFile, secondsToHumanTime, \
   bytesToHumanSize, MAGIC_BYTES, deleteBitcoindDBs,\
   MEGABYTE, ARMORY_HOME_DIR, CLI_OPTIONS, AllowAsync, ARMORY_RAM_USAGE,\
   ARMORY_THREAD_COUNT, ARMORY_DB_TYPE, ARMORYDB_IP, ARMORYDB_DEFAULT_IP, ARMORYDB_PORT, \
   ARMORYDB_DEFAULT_PORT


################################################################################
def extractSignedDataFromVersionsDotTxt(wholeFile, doVerify=True):
   """
   This method returns a pair: a dictionary to lookup link by OS, and
   a formatted string that is sorted by OS, and re-formatted list that
   will hash the same regardless of original format or ordering
   """

   msgBegin = wholeFile.find('# -----BEGIN-SIGNED-DATA-')
   msgBegin = wholeFile.find('\n', msgBegin+1) + 1
   msgEnd   = wholeFile.find('# -----SIGNATURE---------')
   sigBegin = wholeFile.find('\n', msgEnd+1) + 3
   sigEnd   = wholeFile.find('# -----END-SIGNED-DATA---')

   MSGRAW = wholeFile[msgBegin:msgEnd]
   SIGHEX = wholeFile[sigBegin:sigEnd].strip()

   if -1 in [msgBegin,msgEnd,sigBegin,sigEnd]:
      LOGERROR('No signed data block found')
      return ''


   if doVerify:
      Pub = SecureBinaryData(hex_to_binary(ARMORY_INFO_SIGN_PUBLICKEY))
      Msg = SecureBinaryData(MSGRAW)
      Sig = SecureBinaryData(hex_to_binary(SIGHEX))
      isVerified = CryptoECDSA().VerifyData(Msg, Sig, Pub)

      if not isVerified:
         LOGERROR('Signed data block failed verification!')
         return ''
      else:
         LOGINFO('Signature on signed data block is GOOD!')

   return MSGRAW


################################################################################
def parseLinkList(theData):
   """
   Plug the verified data into here...
   """
   DLDICT,VERDICT = {},{}
   sectStr = None
   for line in theData.split('\n'):
      pcs = line[1:].split()
      if line.startswith('# SECTION-') and 'INSTALLERS' in line:
         sectStr = pcs[0].split('-')[-1]
         if not sectStr in DLDICT:
            DLDICT[sectStr] = {}
            VERDICT[sectStr] = ''
         if len(pcs)>1:
            VERDICT[sectStr] = pcs[-1]
         continue

      if len(pcs)==3 and pcs[1].startswith('http'):
         DLDICT[sectStr][pcs[0]] = pcs[1:]

   return DLDICT,VERDICT





################################################################################
class SatoshiDaemonManager(object):
   """
   Use an existing implementation of bitcoind
   """

   class BitcoindError(Exception): pass
   class BitcoindNotAvailableError(Exception): pass
   class BadPath(Exception): pass
   class BitcoinDotConfError(Exception): pass
   class SatoshiHomeDirDNE(Exception): pass
   class ConfigFileUserDNE(Exception): pass
   class ConfigFilePwdDNE(Exception): pass


   #############################################################################
   def __init__(self):
      self.executable = None
      self.satoshiHome = None
      self.bitcoind = None

      self.disabled = False
      self.failedFindExe  = False
      self.foundExe = []

      self.satoshiHome = None
      self.satoshiRoot = None
      self.nodeState = NodeStatusStruct()


   #############################################################################
   def setSatoshiDir(self, newDir):
      self.satoshiHome = newDir
      self.satoshiRoot = newDir

      if 'testnet' in newDir or 'regtest' in newDir:
         self.satoshiRoot, tail = os.path.split(newDir)

      execDir = os.path.dirname(inspect.getsourcefile(SatoshiDaemonManager))
      if execDir.endswith('.zip'):
         execDir = os.path.dirname(execDir)

      if OS_MACOSX:
         # OSX separates binaries/start scripts from the Python code. Back up!
         execDir = os.path.join(execDir, '../../bin/')
      self.dbExecutable = os.path.join(execDir, 'ArmoryDB')  
         
      if OS_WINDOWS:
         self.dbExecutable += ".exe"
         if not os.path.exists(self.dbExecutable):
            self.dbExecutable = "./ArmoryDB.exe"
      
      if OS_LINUX:
         #if there is no local armorydb in the execution folder, 
         #look for an installed one
         if not os.path.exists(self.dbExecutable):
            self.dbExecutable = "ArmoryDB"

   #############################################################################
   def setupSDM(self, pathToBitcoindExe=None, satoshiHome=None, \
                      extraExeSearch=[], createHomeIfDNE=True):
      LOGDEBUG('Exec setupSDM')
      # If the client is remote, don't do anything.
      if not self.localDB:
         LOGWARN("No SDM since the client is remote")
         return

      self.failedFindExe = False

      # If we are supplied a path, then ignore the extra exe search paths
      if pathToBitcoindExe==None:
         pathToBitcoindExe = self.findBitcoind(extraExeSearch)
         if len(pathToBitcoindExe)==0:
            LOGDEBUG('Failed to find bitcoind')
            self.failedFindExe = True
         else:
            LOGINFO('Found bitcoind in the following places:')
            for p in pathToBitcoindExe:
               LOGINFO('   %s', p)
            pathToBitcoindExe = pathToBitcoindExe[0]
            LOGINFO('Using: %s', pathToBitcoindExe)

            if not os.path.exists(pathToBitcoindExe):
               LOGINFO('Somehow failed to find exe even after finding it...?')
               self.failedFindExe = True

      self.executable = pathToBitcoindExe

      # Four possible conditions for already-set satoshi home dir, and input arg
      if satoshiHome is not None:
         self.satoshiHome = satoshiHome
      else:
         if self.satoshiHome is None:
            self.satoshiHome = BTC_HOME_DIR

      if self.failedFindExe:  raise self.BitcoindError, 'bitcoind not found'

      self.disabled = False
      self.bitcoind = None  # this will be a Popen object

   #############################################################################
   def checkDBIsLocal(self):
      if ARMORYDB_IP != ARMORYDB_DEFAULT_IP or \
         ARMORYDB_PORT != ARMORYDB_DEFAULT_PORT:
         self.localDB = False
      else:
         self.localDB = True

   #############################################################################
   def setDisabled(self, newBool=True):
      s = self.getSDMState()

      if newBool==True:
         if s in ('BitcoindInitializing', 'BitcoindSynchronizing', 'BitcoindReady'):
            self.stopBitcoind()

      self.disabled = newBool


   #############################################################################
   def getAllFoundExe(self):
      return list(self.foundExe)


   #############################################################################
   def findBitcoind(self, extraSearchPaths=[]):
      self.foundExe = []

      searchPaths = list(extraSearchPaths)  # create a copy

      if OS_WINDOWS:
         # Making sure the search path argument comes with /daemon and /Bitcoin on Windows

         searchPaths.extend([os.path.join(sp, 'Bitcoin') for sp in searchPaths])
         searchPaths.extend([os.path.join(sp, 'daemon') for sp in searchPaths])
         searchPaths.extend([os.path.join(sp, 'bin') for sp in searchPaths])

         possBaseDir = []

         from platform import machine
         if '64' in machine():
            possBaseDir.append(os.getenv("ProgramW6432"))
            possBaseDir.append(os.getenv('PROGRAMFILES(X86)'))
         else:
            possBaseDir.append(os.getenv('PROGRAMFILES'))

         # check desktop for links

         home      = os.path.expanduser('~')
         desktop   = os.path.join(home, 'Desktop')

         if os.path.exists(desktop):
            dtopfiles = os.listdir(desktop)
            for path in [os.path.join(desktop, fn) for fn in dtopfiles]:
               if 'bitcoin' in path.lower() and path.lower().endswith('.lnk'):
                  import win32com.client
                  shell = win32com.client.Dispatch('WScript.Shell')
                  targ = shell.CreateShortCut(path).Targetpath
                  targDir = os.path.dirname(targ)
                  LOGINFO('Found Bitcoin Core link on desktop: %s', targDir)
                  possBaseDir.append( targDir )

         # Also look in default place in ProgramFiles dirs




         # Now look at a few subdirs of the
         searchPaths.extend(possBaseDir)
         searchPaths.extend([os.path.join(p, 'Bitcoin', 'daemon') for p in possBaseDir])
         searchPaths.extend([os.path.join(p, 'daemon') for p in possBaseDir])
         searchPaths.extend([os.path.join(p, 'Bitcoin') for p in possBaseDir])

         for p in searchPaths:
            testPath = os.path.join(p, 'bitcoind.exe')
            if os.path.exists(testPath):
               self.foundExe.append(testPath)

      else:
         # In case this was a downloaded copy, make sure we traverse to bin/64 dir
         if SystemSpecs.IsX64:
            searchPaths.extend([os.path.join(p, 'bin/64') for p in extraSearchPaths])
         else:
            searchPaths.extend([os.path.join(p, 'bin/32') for p in extraSearchPaths])

         searchPaths.extend(['/usr/lib/bitcoin/'])
         searchPaths.extend(os.getenv("PATH").split(':'))

         for p in searchPaths:
            testPath = os.path.join(p, 'bitcoind')
            if os.path.exists(testPath):
               self.foundExe.append(testPath)

         try:
            locs = subprocess_check_output(['whereis','bitcoind']).split()
            if len(locs)>1:
               locs = filter(lambda x: os.path.basename(x)=='bitcoind', locs)
               LOGINFO('"whereis" returned: %s', str(locs))
               self.foundExe.extend(locs)
         except:
            LOGEXCEPT('Error executing "whereis" command')


      # For logging purposes, check that the first answer matches one of the
      # extra search paths.  There should be some kind of notification that
      # their supplied search path was invalid and we are using something else.
      if len(self.foundExe)>0 and len(extraSearchPaths)>0:
         foundIt = False
         for p in extraSearchPaths:
            if self.foundExe[0].startswith(p):
               foundIt=True

         if not foundIt:
            LOGERROR('Bitcoind could not be found in the specified installation:')
            for p in extraSearchPaths:
               LOGERROR('   %s', p)
            LOGERROR('Bitcoind is being started from:')
            LOGERROR('   %s', self.foundExe[0])

      return self.foundExe

   #############################################################################
   def getGuardianPath(self):
      if OS_WINDOWS:
         armoryInstall = os.path.dirname(inspect.getsourcefile(SatoshiDaemonManager))
         # This should return a zip file because of py2exe
         if armoryInstall.endswith('.zip'):
            armoryInstall = os.path.dirname(armoryInstall)
         gpath = os.path.join(armoryInstall, 'guardian.exe')
      else:
         theDir = os.path.dirname(inspect.getsourcefile(SatoshiDaemonManager))
         gpath = os.path.join(theDir, 'guardian.py')

      if not os.path.exists(gpath):
         LOGERROR('Could not find guardian script: %s', gpath)
         raise FileExistsError
      return gpath

   #############################################################################
   def startBitcoind(self):
      self.btcOut, self.btcErr = None,None
      if self.disabled:
         LOGERROR('SDM was disabled, must be re-enabled before starting')
         return

      LOGINFO('Called startBitcoind')

      if self.isRunningBitcoind():
         raise self.BitcoindError, 'Looks like we have already started theSDM'

      if not os.path.exists(self.executable):
         raise self.BitcoindError, 'Could not find bitcoind'

      self.launchBitcoindAndGuardian()

   #############################################################################
   @AllowAsync
   def pollBitcoindState(self, callback):
      while self.getSDMStateLogic() != 'BitcoindReady':
         time.sleep(1.0)
      callback()

   #############################################################################
   def spawnDB(self, dataDir, dbDir):
      pargs = [self.dbExecutable]

      pargs.append('--db-type="' + ARMORY_DB_TYPE + '"')
      pargs.append('--cookie')

      if USE_TESTNET:
         pargs.append('--testnet')
      if USE_REGTEST:
         pargs.append('--regtest');

      haveSatoshiDir = False
      blocksdir = os.path.join(self.satoshiHome, 'blocks')
      if os.path.exists(blocksdir):   
         pargs.append('--satoshi-datadir="' + blocksdir + '"')

      if (CLI_OPTIONS.satoshiPort):
         pargs.append('--satoshi-port=' + str(BITCOIN_PORT))
         
      pargs.append('--datadir="' + dataDir + '"')
      pargs.append('--dbdir="' + dbDir + '"')

      if CLI_OPTIONS.rebuild:
         pargs.append('--rebuild')
      elif CLI_OPTIONS.rescan:
         pargs.append('--rescan')
      elif CLI_OPTIONS.rescanBalance:
         pargs.append('--rescanSSH')
         
      if CLI_OPTIONS.clearMempool:
         pargs.append('--clear_mempool')

      if ARMORY_RAM_USAGE != -1:
         pargs.append('--ram-usage=' + str(ARMORY_RAM_USAGE))
      if ARMORY_THREAD_COUNT != -1:
         pargs.append('--thread-count=' + str(ARMORY_THREAD_COUNT))

      kargs = {}
      if OS_WINDOWS:
         import win32process
         kargs['shell'] = True
         kargs['creationflags'] = win32process.CREATE_NO_WINDOW

      argStr = " ".join(astr for astr in pargs)
      LOGWARN('Spawning DB with command: ' + argStr)

      launchProcess(pargs, **kargs)

   #############################################################################
   def launchBitcoindAndGuardian(self):

      pargs = [self.executable]

      if USE_TESTNET:
         pargs.append('-testnet')
      elif USE_REGTEST:
         pargs.append('-regtest')

      pargs.append('-datadir=%s' % self.satoshiHome)

      try:
         # Don't want some strange error in this size-check to abort loading
         blocksdir = os.path.join(self.satoshiHome, 'blocks')
         sz = long(0)
         if os.path.exists(blocksdir):
            for fn in os.listdir(blocksdir):
               fnpath = os.path.join(blocksdir, fn)
               sz += long(os.path.getsize(fnpath))

         if sz < 5*GIGABYTE:
            if SystemSpecs.Memory>9.0:
               pargs.append('-dbcache=2000')
            elif SystemSpecs.Memory>5.0:
               pargs.append('-dbcache=1000')
            elif SystemSpecs.Memory>3.0:
               pargs.append('-dbcache=500')
      except:
         LOGEXCEPT('Failed size check of blocks directory')

      kargs = {}
      if OS_WINDOWS:
         import win32process
         kargs['shell'] = True
         kargs['creationflags'] = win32process.CREATE_NO_WINDOW

      # Startup bitcoind and get its process ID (along with our own)
      argStr = " ".join(astr for astr in pargs)
      LOGWARN('Spawning bitcoind with command: ' + argStr)      
      self.bitcoind = launchProcess(pargs, **kargs)

      self.btcdpid  = self.bitcoind.pid
      self.selfpid  = os.getpid()

      LOGINFO('PID of bitcoind: %d',  self.btcdpid)
      LOGINFO('PID of armory:   %d',  self.selfpid)

      # Startup guardian process -- it will watch Armory's PID
      gpath = self.getGuardianPath()
      pargs = [gpath, str(self.selfpid), str(self.btcdpid)]
      if not OS_WINDOWS:
         pargs.insert(0, 'python')
      launchProcess(pargs, **kargs)



   #############################################################################
   def stopBitcoind(self):
      LOGINFO('Called stopBitcoind')
      if self.bitcoind == False:
         self.bitcoind = None
         return
      try:
         if not self.isRunningBitcoind():
            LOGINFO('...but bitcoind is not running, to be able to stop')
            return
         
         from armoryengine.BDM import TheBDM
         cookie = TheBDM.getCookie()
         TheBDM.bdv().shutdownNode(cookie);

         #poll the pid until it's gone, for as long as 2 minutes
         total = 0
         while self.bitcoind.poll()==None:
            time.sleep(0.1)
            total += 1

            if total > 1200:
               LOGERROR("bitcoind failed to shutdown in less than 2 minutes."
                      " Terminating.")
               return

         self.bitcoind = None
      except Exception as e:
         LOGERROR(e)
         return


   #############################################################################
   def isRunningBitcoind(self):
      """
      armoryengine satoshiIsAvailable() only tells us whether there's a
      running bitcoind that is actively responding on its port.  But it
      won't be responding immediately after we've started it (still doing
      startup operations).  If bitcoind was started and still running,
      then poll() will return None.  Any othe poll() return value means
      that the process terminated
      """
      if self.bitcoind==None:
         return False
      # Assume Bitcoind is running if manually started
      if self.bitcoind==False:
         return True
      else:
         if not self.bitcoind.poll()==None:
            LOGDEBUG('Bitcoind is no more')
            if self.btcOut==None:
               self.btcOut, self.btcErr = self.bitcoind.communicate()
               LOGWARN('bitcoind exited, bitcoind STDOUT:')
               for line in self.btcOut.split('\n'):
                  LOGWARN(line)
               LOGWARN('bitcoind exited, bitcoind STDERR:')
               for line in self.btcErr.split('\n'):
                  LOGWARN(line)
         return self.bitcoind.poll()==None

   #############################################################################
   def wasRunningBitcoind(self):
      return (not self.bitcoind==None)

   #############################################################################
   def returnSDMInfo(self):
      sdminfo = {}
      for key,val in self.bitconf.iteritems():
         sdminfo['bitconf_%s'%key] = val

      for key,val in self.lastTopBlockInfo.iteritems():
         sdminfo['topblk_%s'%key] = val

      sdminfo['executable'] = self.executable
      sdminfo['isrunning']  = self.isRunningBitcoind()
      sdminfo['homedir']    = self.satoshiHome
      sdminfo['proxyinit']  = (not self.proxy==None)
      sdminfo['ismidquery'] = self.isMidQuery
      sdminfo['querycount'] = len(self.last20queries)

      return sdminfo

   #############################################################################
   def printSDMInfo(self):
      print '\nCurrent SDM State:'
      print '\t', 'SDM State Str'.ljust(20), ':', self.getSDMState()
      for key,value in self.returnSDMInfo().iteritems():
         print '\t', str(key).ljust(20), ':', str(value)


   #############################################################################
   def updateState(self, nodeStatus):
      self.nodeState = nodeStatus

   #############################################################################
   def getSDMState(self):
      return self.nodeState
   
   #############################################################################
   def getSDMStateStr(self):
      sdmStr = ""
      
      if self.nodeState.status_ == NodeStatus_Offline:
         sdmStr = "NodeStatus_Offline"
         
         if self.nodeState.rpcStatus_ == RpcStatus_Online or \
            self.nodeState.rpcStatus_ == RpcStatus_Error_28: 
            sdmStr = "NodeStatus_Initializing"
         elif isinstance(self.executable, str):
            if not os.path.exists(self.executable):
               sdmStr = "NodeStatus_BadPath"
      
      else:
         sdmStr = "NodeStatus_Ready"
         
         if self.nodeState.rpcStatus_ == RpcStatus_Disabled:
            return sdmStr
         
         if self.nodeState.rpcStatus_ != RpcStatus_Online:
            sdmStr = "NodeStatus_Initializing"
            
         else:
            if self.nodeState.chainState_.state() == ChainStatus_Unknown:
               sdmStr = "NodeStatus_Initializing"
            elif self.nodeState.chainState_.state() == ChainStatus_Syncing:
               sdmStr = "NodeStatus_Syncing"   
               
      return sdmStr
   
   #############################################################################
   def satoshiIsAvailable(self):
      return self.nodeState.rpcStatus_ != RpcStatus_Disabled
