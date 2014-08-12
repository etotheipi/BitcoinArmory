################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
import inspect
import os.path
import socket
import stat
import time
from threading import Event
from bitcoinrpc_jsonrpc import ServiceProxy
from CppBlockUtils import SecureBinaryData, CryptoECDSA
from armoryengine.ArmoryUtils import BITCOIN_PORT, LOGERROR, hex_to_binary, \
   ARMORY_INFO_SIGN_PUBLICKEY, LOGINFO, BTC_HOME_DIR, LOGDEBUG, OS_WINDOWS, \
   SystemSpecs, subprocess_check_output, LOGEXCEPT, FileExistsError, OS_VARIANT, \
   BITCOIN_RPC_PORT, binary_to_base58, isASCII, USE_TESTNET, GIGABYTE, \
   launchProcess, killProcessTree, killProcess, LOGWARN, RightNow, HOUR, \
   PyBackgroundThread, touchFile, DISABLE_TORRENTDL, secondsToHumanTime, \
   bytesToHumanSize, MAGIC_BYTES, deleteBitcoindDBs, TheTDM, satoshiIsAvailable,\
   MEGABYTE, ARMORY_HOME_DIR, CLI_OPTIONS
from bitcoinrpc_jsonrpc import authproxy


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
# jgarzik'sjj jsonrpc-bitcoin code -- stupid-easy to talk to bitcoind
class SatoshiDaemonManager(object):
   """
   Use an existing implementation of bitcoind
   """

   class BitcoindError(Exception): pass
   class BitcoindNotAvailableError(Exception): pass
   class BitcoinDotConfError(Exception): pass
   class SatoshiHomeDirDNE(Exception): pass
   class ConfigFileUserDNE(Exception): pass
   class ConfigFilePwdDNE(Exception): pass


   #############################################################################
   def __init__(self):
      self.executable = None
      self.satoshiHome = None
      self.bitconf = {}
      self.proxy = None
      self.bitcoind = None
      self.isMidQuery = False
      self.last20queries = []
      self.disabled = False
      self.failedFindExe  = False
      self.failedFindHome = False
      self.foundExe = []
      self.circBufferState = []
      self.circBufferTime = []
      self.btcOut = None
      self.btcErr = None
      self.lastTopBlockInfo = { \
                                 'numblks':    -1,
                                 'tophash':    '',
                                 'toptime':    -1,
                                 'error':      'Uninitialized',
                                 'blkspersec': -1     }

      # Added torrent DL before we *actually* start SDM (if it makes sense)
      self.useTorrentFinalAnswer = False
      self.useTorrentFile = ''
      self.torrentDisabled = False
      self.tdm = None
      self.satoshiHome = None


   #############################################################################
   def setSatoshiDir(self, newDir):
      self.satoshiHome = newDir   
      
   #############################################################################
   def setDisableTorrentDL(self, b):
      self.torrentDisabled = b

   #############################################################################
   def tryToSetupTorrentDL(self, torrentPath):
      if self.torrentDisabled:
         LOGWARN('Tried to setup torrent download mgr but we are disabled')
         return False
      
      if not torrentPath or not os.path.exists(torrentPath):
         self.useTorrentFinalAnswer = False
         return False

      bootfile = os.path.join(self.satoshiHome, 'bootstrap.dat')
      bootfilePart = bootfile + '.partial'
      bootfileOld  = bootfile + '.old'

      # cleartorrent.flag means we should remove any pre-existing files
      delTorrentFlag = os.path.join(ARMORY_HOME_DIR, 'cleartorrent.flag')
      if os.path.exists(delTorrentFlag):
         LOGWARN('Flag found to delete any pre-existing torrent files')
         if os.path.exists(bootfile):       os.remove(bootfile)
         if os.path.exists(bootfilePart):   os.remove(bootfilePart)
         if os.path.exists(bootfileOld):    os.remove(bootfileOld)
         if os.path.exists(delTorrentFlag): os.remove(delTorrentFlag)


      TheTDM.setupTorrent(torrentPath, bootfile)
      if not TheTDM.getTDMState()=='ReadyToStart':
         LOGERROR('Unknown error trying to start torrent manager')
         self.useTorrentFinalAnswer = False
         return False


      # We will tell the TDM to write status updates to the log file, and only
      # every 90 seconds.  After it finishes (or fails), simply launch bitcoind
      # as we would've done without the torrent
      #####
      def torrentLogToFile(dpflag=Event(), fractionDone=None, timeEst=None,
                           downRate=None, upRate=None, activity=None,
                           statistics=None, **kws):
         statStr = ''
         if fractionDone:
            statStr += '   Done: %0.1f%%  ' % (fractionDone*100)
         if downRate:
            statStr += ' / DLRate: %0.1f/sec' % (downRate/1024.)
         if timeEst:
            statStr += ' / TLeft: %s' % secondsToHumanTime(timeEst)
         if statistics:
            statStr += ' / Seeds: %d' % (statistics.numSeeds)
            statStr += ' / Peers: %d' % (statistics.numPeers)

         if len(statStr)==0:
            statStr = 'No torrent info available'

         LOGINFO('Torrent: %s' % statStr)

      #####
      def torrentFinished():
         bootsz = '<Unknown>'
         if os.path.exists(bootfile):
            bootsz = bytesToHumanSize(os.path.getsize(bootfile))

         LOGINFO('Torrent finished; size of %s is %s', torrentPath, bootsz)
         LOGINFO('Remove the core btc databases before doing bootstrap')
         deleteBitcoindDBs()
         self.launchBitcoindAndGuardian()

      #####
      def warnUserHashFail():
         from PyQt4.QtGui import QMessageBox
         QMessageBox.warning(self, tr('Hash Failure'), tr("""The torrent download 
            is currently encountering too many packet hash failures to allow it to 
            progress properly. As a result, the torrent engine has been halted. You 
            should report this incident to the Armory team and turn off this feature 
            until further notice."""), QMessageBox.Ok)      
      
      #####
      def torrentFailed(errMsg=''):
         # Not sure there's actually anything we need to do here...
         if errMsg == 'hashFail':
            warnUserHashFail()
            
         bootsz = '<Unknown>'
         if os.path.exists(bootfile):
            bootsz = bytesToHumanSize(os.path.getsize(bootfile))

         LOGERROR('Torrent failed; size of %s is %s', torrentPath, bootsz)
         self.launchBitcoindAndGuardian()
         

 
 
      TheTDM.setSecondsBetweenUpdates(90)
      TheTDM.setCallback('displayFunc',  torrentLogToFile)
      TheTDM.setCallback('finishedFunc', torrentFinished)
      TheTDM.setCallback('failedFunc',   torrentFailed)

      LOGINFO('Bootstrap file is %s' % bytesToHumanSize(TheTDM.torrentSize))
         
      self.useTorrentFinalAnswer = True
      self.useTorrentFile = torrentPath
      return True
      

   #############################################################################
   def shouldTryBootstrapTorrent(self):
      if DISABLE_TORRENTDL or TheTDM.getTDMState()=='Disabled':
         return False

      # The only torrent we have is for the primary Bitcoin network
      if not MAGIC_BYTES=='\xf9\xbe\xb4\xd9':
         return False
      
         

      if TheTDM.torrentSize:
         bootfile = os.path.join(self.satoshiHome, 'bootstrap.dat')
         if os.path.exists(bootfile):
            if os.path.getsize(bootfile) >= TheTDM.torrentSize/2:
               LOGWARN('Looks like a full bootstrap is already here')
               LOGWARN('Skipping torrent download')
               return False
               

      # If they don't even have a BTC_HOME_DIR, corebtc never been installed
      blockDir = os.path.join(self.satoshiHome, 'blocks')
      if not os.path.exists(self.satoshiHome) or not os.path.exists(blockDir):
         return True
      
      # Get the cumulative size of the blk*.dat files
      blockDirSize = sum([os.path.getsize(os.path.join(blockDir, a)) \
                  for a in os.listdir(blockDir) if a.startswith('blk')])
      sizeStr = bytesToHumanSize(blockDirSize)
      LOGINFO('Total size of files in %s is %s' % (blockDir, sizeStr))

      # If they have only a small portion of the blockchain, do it
      szThresh = 100*MEGABYTE if USE_TESTNET else 6*GIGABYTE
      if blockDirSize < szThresh:
         return True

      # So far we know they have a BTC_HOME_DIR, with more than 6GB in blocks/
      # The only thing that can induce torrent now is if we have a partially-
      # finished bootstrap file bigger than the blocks dir.
      bootFiles = ['','']
      bootFiles[0] = os.path.join(self.satoshiHome, 'bootstrap.dat')
      bootFiles[1] = os.path.join(self.satoshiHome, 'bootstrap.dat.partial')
      for fn in bootFiles:
         if os.path.exists(fn):
            if os.path.getsize(fn) > blockDirSize:
               return True
            
      # Okay, we give up -- just download [the rest] via P2P
      return False


   #############################################################################
   #def setSatoshiDir(self, newDir):
      #self.satoshiHome = newDir

   #############################################################################
   def setupSDM(self, pathToBitcoindExe=None, satoshiHome=None, \
                      extraExeSearch=[], createHomeIfDNE=True):
      LOGDEBUG('Exec setupSDM')
      self.failedFindExe = False
      self.failedFindHome = False
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

      # If no new dir is specified, leave satoshi home if it's already set
      # Give it a default BTC_HOME_DIR if not.
      if not os.path.exists(self.satoshiHome):
         if createHomeIfDNE:
            LOGINFO('Making satoshi home dir')
            os.makedirs(self.satoshiHome)
         else:
            LOGINFO('No home dir, makedir not requested')
            self.failedFindHome = True

      if self.failedFindExe:  raise self.BitcoindError, 'bitcoind not found'
      if self.failedFindHome: raise self.BitcoindError, 'homedir not found'

      self.disabled = False
      self.proxy = None
      self.bitcoind = None  # this will be a Popen object
      self.isMidQuery = False
      self.last20queries = []

      self.readBitcoinConf(makeIfDNE=True)





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
                  LOGINFO('Found Bitcoin-Qt link on desktop: %s', targDir)
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

         searchPaths.extend(['/usr/bin/', '/usr/lib/bitcoin/'])

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
   def readBitcoinConf(self, makeIfDNE=False):
      LOGINFO('Reading bitcoin.conf file')
      bitconf = os.path.join( self.satoshiHome, 'bitcoin.conf' )
      if not os.path.exists(bitconf):
         if not makeIfDNE:
            raise self.BitcoinDotConfError, 'Could not find bitcoin.conf'
         else:
            LOGINFO('No bitcoin.conf available.  Creating it...')
            touchFile(bitconf)

      # Guarantee that bitcoin.conf file has very strict permissions
      if OS_WINDOWS:
         if OS_VARIANT[0].lower()=='xp':
            LOGERROR('Cannot set permissions correctly in XP!')
            LOGERROR('Please confirm permissions on the following file ')
            LOGERROR('are set to exclusive access only for your user ')
            LOGERROR('(it usually is, but Armory cannot guarantee it ')
            LOGERROR('on XP systems):')
            LOGERROR('    %s', bitconf)
         else:
            LOGINFO('Setting permissions on bitcoin.conf')
            import ctypes
            username_u16 = ctypes.create_unicode_buffer(u'\0', 512)
            str_length = ctypes.c_int(512)
            ctypes.windll.Advapi32.GetUserNameW(ctypes.byref(username_u16), 
                                                ctypes.byref(str_length))
            
            if not CLI_OPTIONS.disableConfPermis:
               LOGINFO('Setting permissions on bitcoin.conf')
               cmd_icacls = [u'icacls',bitconf,u'/inheritance:r',u'/grant:r', u'%s:F' % username_u16.value]
               icacls_out = subprocess_check_output(cmd_icacls, shell=True)
               LOGINFO('icacls returned: %s', icacls_out)
            else:
               LOGWARN('Skipped setting permissions on bitcoin.conf file')
            
      else:
         LOGINFO('Setting permissions on bitcoin.conf')
         os.chmod(bitconf, stat.S_IRUSR | stat.S_IWUSR)


      with open(bitconf,'r') as f:
         # Find the last character of the each line:  either a newline or '#'
         endchr = lambda line: line.find('#') if line.find('#')>1 else len(line)

         # Reduce each line to a list of key,value pairs separated with '='
         allconf = [l[:endchr(l)].strip().split('=') for l in f.readlines()]

         # Need to convert to (x[0],x[1:]) in case the password has '=' in it
         allconfPairs = [[x[0], '='.join(x[1:])] for x in allconf if len(x)>1]

         # Convert the list of pairs to a dictionary
         self.bitconf = dict(allconfPairs)


      # Look for rpcport, use default if not there
      self.bitconf['rpcport'] = int(self.bitconf.get('rpcport', BITCOIN_RPC_PORT))

      # We must have a username and password.  If not, append to file
      if not self.bitconf.has_key('rpcuser'):
         LOGDEBUG('No rpcuser: creating one')
         with open(bitconf,'a') as f:
            f.write('\n')
            f.write('rpcuser=generated_by_armory\n')
            self.bitconf['rpcuser'] = 'generated_by_armory'

      if not self.bitconf.has_key('rpcpassword'):
         LOGDEBUG('No rpcpassword: creating one')
         with open(bitconf,'a') as f:
            randBase58 = SecureBinaryData().GenerateRandom(32).toBinStr()
            randBase58 = binary_to_base58(randBase58)
            f.write('\n')
            f.write('rpcpassword=%s' % randBase58)
            self.bitconf['rpcpassword'] = randBase58


      if not isASCII(self.bitconf['rpcuser']):
         LOGERROR('Non-ASCII character in bitcoin.conf (rpcuser)!')
      if not isASCII(self.bitconf['rpcpassword']):
         LOGERROR('Non-ASCII character in bitcoin.conf (rpcpassword)!')

      self.bitconf['host'] = '127.0.0.1'


   #############################################################################
   def cleanupFailedTorrent(self):
      # Right now I think don't do anything
      pass    

   #############################################################################
   def startBitcoind(self):
      self.btcOut, self.btcErr = None,None
      if self.disabled:
         LOGERROR('SDM was disabled, must be re-enabled before starting')
         return

      LOGINFO('Called startBitcoind')

      if self.isRunningBitcoind() or TheTDM.getTDMState()=='Downloading':
         raise self.BitcoindError, 'Looks like we have already started theSDM'

      if not os.path.exists(self.executable):
         raise self.BitcoindError, 'Could not find bitcoind'

      
      chk1 = os.path.exists(self.useTorrentFile)
      chk2 = self.shouldTryBootstrapTorrent()
      chk3 = TheTDM.getTDMState()=='ReadyToStart'

      if chk1 and chk2 and chk3:
         TheTDM.startDownload()
      else:
         self.launchBitcoindAndGuardian()
            


   #############################################################################
   def launchBitcoindAndGuardian(self):

      pargs = [self.executable]

      if USE_TESTNET:
         testhome = self.satoshiHome[:]
         if self.satoshiHome.endswith('/testnet3/'):
            pargs.append('-datadir=%s' % self.satoshiHome[:-10])
         elif self.satoshiHome.endswith('/testnet3'):
            pargs.append('-datadir=%s' % self.satoshiHome[:-9])
         pargs.append('-testnet')
      else:
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


      # Startup bitcoind and get its process ID (along with our own)
      self.bitcoind = launchProcess(pargs)

      self.btcdpid  = self.bitcoind.pid
      self.selfpid  = os.getpid()

      LOGINFO('PID of bitcoind: %d',  self.btcdpid)
      LOGINFO('PID of armory:   %d',  self.selfpid)

      # Startup guardian process -- it will watch Armory's PID
      gpath = self.getGuardianPath()
      pargs = [gpath, str(self.selfpid), str(self.btcdpid)]
      if not OS_WINDOWS:
         pargs.insert(0, 'python')
      launchProcess(pargs)



   #############################################################################
   def stopBitcoind(self):
      LOGINFO('Called stopBitcoind')
      if not self.isRunningBitcoind():
         LOGINFO('...but bitcoind is not running, to be able to stop')
         return

      killProcessTree(self.bitcoind.pid)
      killProcess(self.bitcoind.pid)

      time.sleep(1)
      self.bitcoind = None


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
   def bitcoindIsResponsive(self):
      return satoshiIsAvailable(self.bitconf['host'], self.bitconf['rpcport'])

   #############################################################################
   def getSDMState(self):
      """
      As for why I'm doing this:  it turns out that between "initializing"
      and "synchronizing", bitcoind temporarily stops responding entirely,
      which causes "not-available" to be the state.  I need to smooth that
      out because it wreaks havoc on the GUI which will switch to showing
      a nasty error.
      """

      state = self.getSDMStateLogic()
      self.circBufferState.append(state)
      self.circBufferTime.append(RightNow())
      if len(self.circBufferTime)>2 and \
         (self.circBufferTime[-1] - self.circBufferTime[1]) > 5:
         # Only remove the first element if we have at least 5s history
         self.circBufferState = self.circBufferState[1:]
         self.circBufferTime  = self.circBufferTime[1:]

      # Here's where we modify the output to smooth out the gap between
      # "initializing" and "synchronizing" (which is a couple seconds
      # of "not available").   "NotAvail" keeps getting added to the
      # buffer, but if it was "initializing" in the last 5 seconds,
      # we will keep "initializing"
      if state=='BitcoindNotAvailable':
         if 'BitcoindInitializing' in self.circBufferState:
            LOGWARN('Overriding not-available state. This should happen 0-5 times')
            return 'BitcoindInitializing'

      return state

   #############################################################################
   def getSDMStateLogic(self):

      if self.disabled:
         return 'BitcoindMgmtDisabled'

      if self.failedFindExe:
         return 'BitcoindExeMissing'

      if self.failedFindHome:
         return 'BitcoindHomeMissing'

      if TheTDM.isRunning():
         return 'TorrentSynchronizing'

      latestInfo = self.getTopBlockInfo()

      if self.bitcoind==None and latestInfo['error']=='Uninitialized':
         return 'BitcoindNeverStarted'

      if not self.isRunningBitcoind():
         # Not running at all:  either never started, or process terminated
         if not self.btcErr==None and len(self.btcErr)>0:
            errstr = self.btcErr.replace(',',' ').replace('.',' ').replace('!',' ')
            errPcs = set([a.lower() for a in errstr.split()])
            runPcs = set(['cannot','obtain','lock','already','running'])
            dbePcs = set(['database', 'recover','backup','except','wallet','dat'])
            if len(errPcs.intersection(runPcs))>=(len(runPcs)-1):
               return 'BitcoindAlreadyRunning'
            elif len(errPcs.intersection(dbePcs))>=(len(dbePcs)-1):
               return 'BitcoindDatabaseEnvError'
            else:
               return 'BitcoindUnknownCrash'
         else:
            return 'BitcoindNotAvailable'
      elif not self.bitcoindIsResponsive():
         # Running but not responsive... must still be initializing
         return 'BitcoindInitializing'
      else:
         # If it's responsive, get the top block and check
         # TODO: These conditionals are based on experimental results.  May
         #       not be accurate what the specific errors mean...
         if latestInfo['error']=='ValueError':
            return 'BitcoindWrongPassword'
         elif latestInfo['error']=='JsonRpcException':
            return 'BitcoindInitializing'
         elif latestInfo['error']=='SocketError':
            return 'BitcoindNotAvailable'

         if 'BitcoindReady' in self.circBufferState:
            # If ready, always ready
            return 'BitcoindReady'

         # If we get here, bitcoind is gave us a response.
         secSinceLastBlk = RightNow() - latestInfo['toptime']
         blkspersec = latestInfo['blkspersec']
         #print 'Blocks per 10 sec:', ('UNKNOWN' if blkspersec==-1 else blkspersec*10)
         if secSinceLastBlk > 4*HOUR or blkspersec==-1:
            return 'BitcoindSynchronizing'
         else:
            if blkspersec*20 > 2 and not 'BitcoindReady' in self.circBufferState:
               return 'BitcoindSynchronizing'
            else:
               return 'BitcoindReady'




   #############################################################################
   def createProxy(self, forceNew=False):
      if self.proxy==None or forceNew:
         LOGDEBUG('Creating proxy')
         usr,pas,hst,prt = [self.bitconf[k] for k in ['rpcuser','rpcpassword',\
                                                      'host', 'rpcport']]
         pstr = 'http://%s:%s@%s:%d' % (usr,pas,hst,prt)
         LOGINFO('Creating proxy in SDM: host=%s, port=%s', hst,prt)
         self.proxy = ServiceProxy(pstr)


   #############################################################################
   def __backgroundRequestTopBlock(self):
      self.createProxy()
      self.isMidQuery = True
      try:
         numblks = self.proxy.getinfo()['blocks']
         blkhash = self.proxy.getblockhash(numblks)
         toptime = self.proxy.getblock(blkhash)['time']
         #LOGDEBUG('RPC Call: numBlks=%d, toptime=%d', numblks, toptime)
         # Only overwrite once all outputs are retrieved
         self.lastTopBlockInfo['numblks'] = numblks
         self.lastTopBlockInfo['tophash'] = blkhash
         self.lastTopBlockInfo['toptime'] = toptime
         self.lastTopBlockInfo['error']   = None    # Holds error info

         if len(self.last20queries)==0 or \
               (RightNow()-self.last20queries[-1][0]) > 0.99:
            # This conditional guarantees last 20 queries spans at least 20s
            self.last20queries.append([RightNow(), numblks])
            self.last20queries = self.last20queries[-20:]
            t0,b0 = self.last20queries[0]
            t1,b1 = self.last20queries[-1]

            # Need at least 10s of data to give meaning answer
            if (t1-t0)<10:
               self.lastTopBlockInfo['blkspersec'] = -1
            else:
               self.lastTopBlockInfo['blkspersec'] = float(b1-b0)/float(t1-t0)

      except ValueError:
         # I believe this happens when you used the wrong password
         LOGEXCEPT('ValueError in bkgd req top blk')
         self.lastTopBlockInfo['error'] = 'ValueError'
      except authproxy.JSONRPCException:
         # This seems to happen when bitcoind is overwhelmed... not quite ready
         LOGDEBUG('generic jsonrpc exception')
         self.lastTopBlockInfo['error'] = 'JsonRpcException'
      except socket.error:
         # Connection isn't available... is bitcoind not running anymore?
         LOGDEBUG('generic socket error')
         self.lastTopBlockInfo['error'] = 'SocketError'
      except:
         LOGEXCEPT('generic error')
         self.lastTopBlockInfo['error'] = 'UnknownError'
         raise
      finally:
         self.isMidQuery = False


   #############################################################################
   def updateTopBlockInfo(self):
      """
      We want to get the top block information, but if bitcoind is rigorously
      downloading and verifying the blockchain, it can sometimes take 10s to
      to respond to JSON-RPC calls!  We must do it in the background...

      If it's already querying, no need to kick off another background request,
      just return the last value, which may be "stale" but we don't really
      care for this particular use-case
      """
      if not self.isRunningBitcoind():
         return

      if self.isMidQuery:
         return

      self.createProxy()
      self.queryThread = PyBackgroundThread(self.__backgroundRequestTopBlock)
      self.queryThread.start()


   #############################################################################
   def getTopBlockInfo(self):
      if self.isRunningBitcoind():
         self.updateTopBlockInfo()
         self.queryThread.join(0.001)  # In most cases, result should come in 1 ms
         # We return a copy so that the data is not changing as we use it

      return self.lastTopBlockInfo.copy()


   #############################################################################
   def callJSON(self, func, *args):
      state = self.getSDMState()
      if not state in ('BitcoindReady', 'BitcoindSynchronizing'):
         LOGERROR('Called callJSON(%s, %s)', func, str(args))
         LOGERROR('Current SDM state: %s', state)
         raise self.BitcoindError, 'callJSON while %s'%state

      return self.proxy.__getattr__(func)(*args)


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

   


