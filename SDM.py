################################################################################
#                                                                              #
# Copyright (C) 2011-2013, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
import inspect
import os.path
import socket
import stat
import time
from jsonrpc import ServiceProxy
from CppBlockUtils import SecureBinaryData, CryptoECDSA
from armoryengine.ArmoryUtils import BITCOIN_PORT, LOGERROR, hex_to_binary, \
   ARMORY_INFO_SIGN_PUBLICKEY, LOGINFO, BTC_HOME_DIR, LOGDEBUG, OS_WINDOWS, \
   SystemSpecs, subprocess_check_output, LOGEXCEPT, FileExistsError, OS_VARIANT, \
   BITCOIN_RPC_PORT, binary_to_base58, isASCII, USE_TESTNET, GIGABYTE, \
   launchProcess, killProcessTree, killProcess, LOGWARN, RightNow, HOUR, \
   PyBackgroundThread, touchFile
from jsonrpc import authproxy


#############################################################################
def satoshiIsAvailable(host='127.0.0.1', port=BITCOIN_PORT, timeout=0.01):

   if not isinstance(port, (list,tuple)):
      port = [port]

   for p in port:
      s = socket.socket()
      s.settimeout(timeout)   # Most of the time checking localhost -- FAST
      try:
         s.connect((host, p))
         s.close()
         return p
      except:
         pass

   return 0


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



   #############################################################################
   def setupSDM(self, pathToBitcoindExe=None, satoshiHome=BTC_HOME_DIR, \
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

      if not os.path.exists(satoshiHome):
         if createHomeIfDNE:
            LOGINFO('Making satoshi home dir')
            os.makedirs(satoshiHome)
         else:
            LOGINFO('No home dir, makedir not requested')
            self.failedFindHome = True

      if self.failedFindExe:  raise self.BitcoindError, 'bitcoind not found'
      if self.failedFindHome: raise self.BitcoindError, 'homedir not found'

      self.satoshiHome = satoshiHome
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
         # First check desktop for links
         possBaseDir = []
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
         possBaseDir.append(os.getenv('PROGRAMFILES'))
         if SystemSpecs.IsX64:
            possBaseDir.append(os.getenv('PROGRAMFILES(X86)'))
         

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
            import win32api
            username = win32api.GetUserName()
            LOGINFO('Setting permissions on bitcoin.conf')
            cmd_icacls = ['icacls',bitconf,'/inheritance:r','/grant:r', '%s:F' % username]
            icacls_out = subprocess_check_output(cmd_icacls, shell=True)
            LOGINFO('icacls returned: %s', icacls_out)
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
   def startBitcoind(self):
      self.btcOut, self.btcErr = None,None
      if self.disabled:
         LOGERROR('SDM was disabled, must be re-enabled before starting')
         return

      LOGINFO('Called startBitcoind')

      if self.isRunningBitcoind():
         raise self.BitcoindError, 'Looks like we have already started bitcoind'

      if not os.path.exists(self.executable):
         raise self.BitcoindError, 'Could not find bitcoind'
   

      pargs = [self.executable]

      if USE_TESTNET:
         dataDir = self.satoshiHome
         if os.path.basename(dataDir) == "testnet3":
            dataDir = os.path.abspath(self.satoshiHome + "/..")
         pargs.append('-datadir=%s' % dataDir)
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
            LOGWARN('Overriding not-available message. This should happen 0-5 times')
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
