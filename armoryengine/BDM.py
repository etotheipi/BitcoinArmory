################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
import Queue
import os.path

from armoryengine.ArmoryUtils import *
from SDM import SatoshiDaemonManager
from armoryengine.Timer import TimeThisFunction
import CppBlockUtils as Cpp
from armoryengine.BinaryUnpacker import BinaryUnpacker
from armoryengine.BinaryPacker import UINT64

BDMcurrentBlock = [UINT32_MAX, 0]


def getCurrTimeAndBlock():
   time0 = long(RightNowUTC())
   if TheBDM.getBDMState()=='BlockchainReady':
      if BDMcurrentBlock[1]: return (time0, BDMcurrentBlock[0])
      else: return (time0, TheBDM.getTopBlockHeight())
   else:
      return (time0, UINT32_MAX)
   
################################################################################
# Let's create a thread-wrapper for the blockchain utilities.  Enable the
# ability for multi-threaded blockchain scanning -- have a main thread and 
# a blockchain thread:  blockchain can scan, and main thread will check back
# every now and then to see if it's done
BLOCKCHAINMODE  = enum('Offline', \
                       'Uninitialized', \
                       'Full', \
                       'Rescanning', \
                       'LiteScanning', \
                       'FullPrune', \
                       'Lite')

BDMINPUTTYPE  = enum('RegisterAddr', \
                     'ZeroConfTxToInsert', \
                     'HeaderRequested', \
                     'TxRequested', \
                     'BlockRequested', \
                     'AddrBookRequested', \
                     'BlockAtHeightRequested', \
                     'HeaderAtHeightRequested', \
                     'ForceRebuild', \
                     'RescanRequested', \
                     'WalletRecoveryScan', \
                     'UpdateWallets', \
                     'ReadBlkUpdate', \
                     'GoOnlineRequested', \
                     'GoOfflineRequested', \
                     'Passthrough', \
                     'Reset', \
                     'Shutdown')

def newTheBDM(isOffline=False, blocking=False):
   global TheBDM
   TheBDM = BlockDataManagerThread(isOffline=isOffline, blocking=blocking)
   

# Make TheBDM act like it's a singleton. Always use the global singleton TheBDM
# instance that exists in this module regardless of the instance that passed as self
def ActLikeASingletonBDM(func):
   def inner(*args, **kwargs):
      if TheBDM and len(args) > 0:
         newArgs = (TheBDM,) + args[1:]
         return func(*newArgs, **kwargs)
      else:
         return func(*args, **kwargs)
   return inner

################################################################################
class BlockDataManagerThread(threading.Thread):
   """ 
   A note about this class: 

      It was mainly created to allow for asynchronous blockchain scanning,
      but the act of splitting the BDM into it's own thread meant that ALL
      communication with the BDM requires thread-safe access.  So basically,
      I had to wrap EVERYTHING.  And then make it flexible. 

      For this reason, any calls not explicitly related to rescanning will
      block by default, which could be a long time if the BDM is in the 
      middle of rescanning.  For this reason, you are expected to either 
      pass wait=False if you just want to queue the function call and move
      on in the main thread, or check the BDM state first, to make sure 
      it's not currently scanning and can expect immediate response.

      This makes using the BDM much more complicated.  But comes with the 
      benefit of all rescanning being able to happen in the background.  
      If you want to run it like single-threaded, you can use 
      TheBDM.setBlocking(True) and all calls will block.  Always (unless
      you pass wait=False explicitly to one of those calls).

      Any calls that retrieve data from the BDM should block, even if you
      technically can specify wait=False.  This is because the class was 
      not designed to maintain organization of output data asynchronously.  
      So a call like TheBDM.getTopBlockHeader() will always block, and you
      should check the BDM state if you want to make sure it returns 
      immediately.  Since there is only one main thread, There is really no
      way for a rescan to be started between the time you check the state
      and the time you call the method (so if you want to access the BDM 
      from multiple threads, this class will need some redesign).
       

   This serves as a layer between the GUI and the Blockchain utilities.
   If a request is made to mess with the BDM while it is in the 
   middle of scanning, it will queue it for when it's done

   All private methods (those starting with two underscores, like __method),
   are executed only by the BDM thread.  These should never be called
   externally, and are only safe to run when the BDM is ready to execute 
   them.  

   You can use any non-private methods at any time, and if you set wait=True,
   the main thread will block until that operation is complete.  If the BDM
   is in the middle of a scan, the main thread could block for minutes until
   the scanning is complete and then it processes your request.

   Therefore, use setBlocking(True) to make sure you always wait/block after
   every call, if you are interested in simplicity and don't mind waiting.

   Use setBlocking(False) along with wait=False for the appropriate calls
   to queue up your request and continue the main thread immediately.  You
   can finish up something else, and then come back and check whether the
   job is finished (usually using TheBDM.getBDMState()=='BlockchainReady')

   Any methods not defined explicitly in this class will "passthrough" the
   __getattr__() method, which will then call that exact method name on 
   the BDM.  All calls block by default.  All such calls can also include
   wait=False if you want to queue it and then continue asynchronously.


   Implementation notes:
      
      Before the multi-threaded BDM, there was wallets, and there was the BDM.
      We always gave the wallets to the BDM and said "please search the block-
      chain for relevant transactions".  Now that this is asynchronous, the 
      calling thread is going to queue the blockchain scan, and then run off 
      and do other things: which may include address/wallet operations that 
      would collide with the BDM updating it.

      THEREFORE, the BDM now has a single, master wallet.  Any address you add
      to any of your wallets, should be added to the master wallet, too.  The 
      PyBtcWallet class does this for you, but if you are using raw BtcWallets
      (the C++ equivalent), you need to do:
   
            cppWallet.addScrAddress_1_(Hash160ToScrAddr(newAddr))
            TheBDM.registerScrAddr(newAddr, isFresh=?) 

      This will add the address to the TheBDM.masterCppWallet.  Then when you 
      queue up the TheBDM to do a rescan (if necessary), it will update only 
      its own wallet.  Luckily, I designed the BDM so that data for addresses
      in one wallet (the master), can be applied immediately to other/new 
      wallets that have the same addresses.  

      If you say isFresh=False, then the BDM will set isDirty=True.  This means
      that a full rescan will have to be performed, and wallet information may
      not be accurate until it is performed.  isFresh=True should be used for
      addresses/wallets you just created, and thus there's no reason to rescan,
      because there's no chance they could have any history in the blockchain.

      Tying this all together:  if you add an address to a PYTHON wallet, you
      just add it through an existing call.  If you add it with a C++ wallet,
      you need to explicitly register it with TheBDM, too.  Then you need to 
      tell the BDM to do a rescan (if isDirty==True), and then call the method 
      updateWalletsAfterScan(
      are ready, you can chec
      
   """
   #############################################################################
   def __init__(self, isOffline=False, blocking=False):
      super(BlockDataManagerThread, self).__init__()

      if isOffline:
         self.blkMode  = BLOCKCHAINMODE.Offline
         self.prefMode = BLOCKCHAINMODE.Offline
      else:
         self.blkMode  = BLOCKCHAINMODE.Uninitialized
         self.prefMode = BLOCKCHAINMODE.Full

      self.bdm = Cpp.BlockDataManager().getBDM()

      # These are for communicating with the master (GUI) thread
      self.inputQueue  = Queue.Queue()
      self.outputQueue = Queue.Queue()

      # Flags
      self.startBDM      = False
      self.doShutdown    = False
      self.aboutToRescan = False
      self.errorOut      = 0

      self.setBlocking(blocking)

      self.currentActivity = 'None'

      # Lists of wallets that should be checked after blockchain updates
      self.pyWltList    = []   # these will be python refs
      self.cppWltList   = []   # these will be python refs

      # The BlockDataManager is easier to use if you put all your addresses
      # into a C++ BtcWallet object, and let it 
      self.masterCppWallet = Cpp.BtcWallet()
      self.bdm.registerWallet(self.masterCppWallet)
       
      self.btcdir = BTC_HOME_DIR
      self.ldbdir = LEVELDB_DIR
      self.lastPctLoad = 0
      
      
   #############################################################################
   @ActLikeASingletonBDM
   def setDaemon(self, daemonic):
      if not self.isDaemon():
         super(BlockDataManagerThread, self).setDaemon(daemonic)

   #############################################################################
   @ActLikeASingletonBDM
   def start(self):
      try:
         super(BlockDataManagerThread, self).start()
      except RuntimeError:
         LOGWARN("Attempt to start singleton TheBDM that has already been started.")
         pass
      
   #############################################################################
   @ActLikeASingletonBDM
   def __getattr__(self, name):
      '''
      Anything that is not explicitly defined in this class should 
      passthrough to the C++ BlockDataManager class

      This remaps such calls into "passthrough" requests via the input
      queue.  This makes sure that the requests are processed only when
      the BDM is ready.  Hopefully, this will prevent multi-threaded
      disasters, such as seg faults due to trying to read memory that is
      in the process of being updated.
   
      Specifically, any passthrough call is expected to return output
      unless you add 'waitForReturn=False' to the arg list.  i.e. all
      calls that "passthrough" will always block unless you explicitly
      tell it not to.
      '''

      
      rndID = int(random.uniform(0,100000000)) 
      if not hasattr(self.bdm, name):
         LOGERROR('No BDM method: %s', name)
         raise AttributeError
      else:
         def passthruFunc(*args, **kwargs):
            #LOGDEBUG('External thread requesting: %s (%d)', name, rndID)
            waitForReturn = True
            if len(kwargs)>0 and \
               kwargs.has_key('wait') and \
               not kwargs['wait']:
               waitForReturn = False


            # If this was ultimately called from the BDM thread, don't go
            # through the queue, just do it!
            if len(kwargs)>0 and \
               kwargs.has_key('calledFromBDM') and \
               kwargs['calledFromBDM']:
                  return getattr(self.bdm, name)(*args)

            self.inputQueue.put([BDMINPUTTYPE.Passthrough, rndID, waitForReturn, name] + list(args))
            

            if waitForReturn:
               try:
                  out = self.outputQueue.get(True, self.mtWaitSec)
                  return out
               except Queue.Empty:
                  LOGERROR('BDM was not ready for your request!  Waited %d sec.' % self.mtWaitSec)
                  LOGERROR('  getattr   name: %s', name)
                  LOGERROR('BDM currently doing: %s (%d)', self.currentActivity,self.currentID )
                  LOGERROR('Waiting for completion: ID= %d', rndID)
                  LOGERROR('Direct traceback')
                  traceback.print_stack()
                  self.errorOut += 1
                  LOGEXCEPT('Traceback:')
         return passthruFunc


   
   #############################################################################
   @ActLikeASingletonBDM
   def waitForOutputIfNecessary(self, expectOutput, rndID=0):
      # The get() command will block until the thread puts something there.
      # We don't always expect output, but we use this method to 
      # replace inputQueue.join().  The reason for doing it is so 
      # that we can guarantee that BDM thread knows whether we are waiting
      # for output or not, and any additional requests put on the inputQueue
      # won't extend our wait time for this request
      if expectOutput:
         try:
            return self.outputQueue.get(True, self.mtWaitSec)
         except Queue.Empty:
            stkOneUp = traceback.extract_stack()[-2]
            filename,method = stkOneUp[0], stkOneUp[1]
            LOGERROR('Waiting for BDM output that didn\'t come after %ds.' % self.mtWaitSec)
            LOGERROR('BDM state is currently: %s', self.getBDMState())
            LOGERROR('Called from: %s:%d (%d)', os.path.basename(filename), method, rndID)
            LOGERROR('BDM currently doing: %s (%d)', self.currentActivity, self.currentID)
            LOGERROR('Direct traceback')
            traceback.print_stack()
            LOGEXCEPT('Traceback:')
            self.errorOut += 1
      else:
         return None
      
      
   #############################################################################
   @ActLikeASingletonBDM
   def setBlocking(self, doblock=True, newTimeout=MT_WAIT_TIMEOUT_SEC):
      """
      If we want TheBDM to behave as a single-threaded app, we need to disable
      the timeouts so that long operations (such as reading the blockchain) do
      not crash the process.

      So setting wait=True is NOT identical to setBlocking(True), since using
      wait=True with blocking=False will break when the timeout has been reached
      """
      if doblock:
         self.alwaysBlock = True
         self.mtWaitSec   = None
      else:
         self.alwaysBlock = False
         self.mtWaitSec   = newTimeout


   #############################################################################
   @ActLikeASingletonBDM
   def Reset(self, wait=None):
      expectOutput = False
      if not wait==False and (self.alwaysBlock or wait==True):
         expectOutput = True

      rndID = int(random.uniform(0,100000000)) 
      self.inputQueue.put([BDMINPUTTYPE.Reset, rndID, expectOutput] )
      return self.waitForOutputIfNecessary(expectOutput, rndID)

   #############################################################################
   @ActLikeASingletonBDM
   def getBlkMode(self):
      return self.blkMode

   #############################################################################
   @ActLikeASingletonBDM
   def getBDMState(self):
      if self.blkMode == BLOCKCHAINMODE.Offline:
         # BDM will not be able to provide any blockchain data, or scan
         return 'Offline'
      elif self.blkMode == BLOCKCHAINMODE.Full and not self.aboutToRescan:
         # The BDM is idle, waiting for things to do
         return 'BlockchainReady'
      elif self.blkMode == BLOCKCHAINMODE.LiteScanning and not self.aboutToRescan:
         # The BDM is doing some processing but it is expected to be done within
         # 0.1s.  For instance, readBlkFileUpdate requires processing, but can be
         # performed 100/sec.  For the outside calling thread, this is not any
         # different than BlockchainReady. 
         return 'BlockchainReady'
      elif self.blkMode == BLOCKCHAINMODE.Rescanning or self.aboutToRescan:
         # BDM is doing a FULL scan of the blockchain, and expected to take
         
         return 'Scanning'
      elif self.blkMode == BLOCKCHAINMODE.Uninitialized and not self.aboutToRescan:
         # BDM wants to be online, but the calling thread never initiated the 
         # loadBlockchain() call.  Usually setOnlineMode, registerWallets, then
         # load the blockchain.
         return 'Uninitialized'
      elif self.blkMode == BLOCKCHAINMODE.FullPrune:
         # NOT IMPLEMENTED
         return 'FullPrune'
      elif self.blkMode == BLOCKCHAINMODE.Lite:
         # NOT IMPLEMENTED
         return 'Lite'
      else:
         return '<UNKNOWN: %d>' % self.blkMode


   #############################################################################
   @ActLikeASingletonBDM
   def predictLoadTime(self):
      # Apparently we can't read the C++ state while it's scanning, 
      # specifically getLoadProgress* methods.  Thus we have to resort
      # to communicating via files... bleh 
      bfile = os.path.join(ARMORY_HOME_DIR,'blkfiles.txt')
      if not os.path.exists(bfile):
         return [-1,-1,-1,-1]

      try:
         with open(bfile,'r') as f:
            tmtrx = [line.split() for line in f.readlines() if len(line.strip())>0]
            phases  = [float(row[0])  for row in tmtrx]
            currPhase = phases[-1]
            startat = [float(row[1]) for row in tmtrx if float(row[0])==currPhase]
            sofar   = [float(row[2]) for row in tmtrx if float(row[0])==currPhase]
            total   = [float(row[3]) for row in tmtrx if float(row[0])==currPhase]
            times   = [float(row[4]) for row in tmtrx if float(row[0])==currPhase]
            
            todo = total[0] - startat[0]
            pct0 = sofar[0]  / todo
            pct1 = sofar[-1] / todo
            t0,t1 = times[0], times[-1]
            if (not t1>t0) or todo<0:
               return [-1,-1,-1,-1]
            rate = (pct1-pct0) / (t1-t0) 
            tleft = (1-pct1)/rate
            totalPct = (startat[-1] + sofar[-1]) / total[-1]
            if not self.lastPctLoad == pct1:
               LOGINFO('Reading blockchain, pct complete: %0.1f', 100*totalPct)
            self.lastPctLoad = totalPct 
            return (currPhase,totalPct,rate,tleft)
      except:
         raise
         return [-1,-1,-1,-1]
            

   
      
   #############################################################################
   @ActLikeASingletonBDM
   def execCleanShutdown(self, wait=True):
      expectOutput = False
      if not wait==False and (self.alwaysBlock or wait==True):
         expectOutput = True

      rndID = int(random.uniform(0,100000000)) 
      self.inputQueue.put([BDMINPUTTYPE.Shutdown, rndID, expectOutput])
      return self.waitForOutputIfNecessary(expectOutput, rndID)

   #############################################################################
   @ActLikeASingletonBDM
   def setSatoshiDir(self, newBtcDir):
      if not os.path.exists(newBtcDir):
         LOGERROR('setSatoshiDir: directory does not exist: %s', newBtcDir)
         return

      if not self.blkMode in (BLOCKCHAINMODE.Offline, BLOCKCHAINMODE.Uninitialized):
         LOGERROR('Cannot set blockchain/satoshi path after BDM is started')
         return

      self.btcdir = newBtcDir

   #############################################################################
   @ActLikeASingletonBDM
   def setLevelDBDir(self, ldbdir):

      if not self.blkMode in (BLOCKCHAINMODE.Offline, BLOCKCHAINMODE.Uninitialized):
         LOGERROR('Cannot set blockchain/satoshi path after BDM is started')
         return

      if not os.path.exists(ldbdir):
         os.makedirs(ldbdir)

      self.ldbdir = ldbdir


   #############################################################################
   @ActLikeASingletonBDM
   def setOnlineMode(self, goOnline=True, wait=None):
      LOGINFO('Setting online mode: %s (wait=%s)' % (str(goOnline), str(wait)))
      expectOutput = False
      # Wait is tri-state - True, False, or None
      if not wait==False and (self.alwaysBlock or wait==True):
         expectOutput = True

      rndID = int(random.uniform(0,100000000)) 

      if goOnline:
         if TheBDM.getBDMState() in ('Offline','Uninitialized'):
            self.inputQueue.put([BDMINPUTTYPE.GoOnlineRequested, rndID, expectOutput])
      else:
         if TheBDM.getBDMState() in ('Scanning','BlockchainReady'):
            self.inputQueue.put([BDMINPUTTYPE.GoOfflineRequested, rndID, expectOutput])

      return self.waitForOutputIfNecessary(expectOutput, rndID)
   
   #############################################################################
   @ActLikeASingletonBDM
   def isScanning(self):
      return (self.aboutToRescan or self.blkMode==BLOCKCHAINMODE.Rescanning)


   #############################################################################
   @ActLikeASingletonBDM
   def readBlkFileUpdate(self, wait=True):
      """
      This method can be blocking... it always has been without a problem,
      because the block file updates are always fast.  But I have to assume 
      that it theoretically *could* take a while.  Consider using wait=False
      if you want it to do its thing and not wait for it (this matters, because
      you'll want to call TheBDM.updateWalletsAfterScan() when this is 
      finished to make sure that 
      """
      expectOutput = False
      if not wait==False and (self.alwaysBlock or wait==True):
         expectOutput = True

      rndID = int(random.uniform(0,100000000)) 
      self.inputQueue.put([BDMINPUTTYPE.ReadBlkUpdate, rndID, expectOutput])
      return self.waitForOutputIfNecessary(expectOutput, rndID)
      

   #############################################################################
   @ActLikeASingletonBDM
   def isInitialized(self):
      return self.blkMode==BLOCKCHAINMODE.Full and self.bdm.isInitialized()


   #############################################################################
   @ActLikeASingletonBDM
   def isDirty(self):
      return self.bdm.isDirty()
   


   #############################################################################
   @ActLikeASingletonBDM
   def rescanBlockchain(self, scanType='AsNeeded', wait=None):
      expectOutput = False
      if not wait==False and (self.alwaysBlock or wait==True):
         expectOutput = True

      self.aboutToRescan = True

      rndID = int(random.uniform(0,100000000)) 
      self.inputQueue.put([BDMINPUTTYPE.RescanRequested, rndID, expectOutput, scanType])
      LOGINFO('Blockchain rescan requested')
      return self.waitForOutputIfNecessary(expectOutput, rndID)


   #############################################################################
   @ActLikeASingletonBDM
   def updateWalletsAfterScan(self, wait=True):
      """
      Be careful with this method:  it is asking the BDM thread to update 
      the wallets in the main thread.  If you do this with wait=False, you
      need to avoid any wallet operations in the main thread until it's done.
      However, this is usually very fast as long as you know the BDM is not
      in the middle of a rescan, so you might as well set wait=True.  

      In fact, I highly recommend you always use wait=True, in order to 
      guarantee thread-safety.

      NOTE:  If there are multiple wallet-threads, this might not work.  It 
             might require specifying which wallets to update after a scan,
             so that other threads don't collide with the BDM updating its
             wallet when called from this thread.
      """
      expectOutput = False
      if not wait==False and (self.alwaysBlock or wait==True):
         expectOutput = True

      rndID = int(random.uniform(0,100000000)) 
      self.inputQueue.put([BDMINPUTTYPE.UpdateWallets, rndID, expectOutput])
      return self.waitForOutputIfNecessary(expectOutput, rndID)


   #############################################################################
   @ActLikeASingletonBDM
   def startWalletRecoveryScan(self, pywlt, wait=None):
      """
      A wallet recovery scan may require multiple, independent rescans.  This 
      is because we don't know how many addresses to pre-calculate for the
      initial scan.  So, we will calculate the first X addresses in the wallet,
      do a scan, and then if any addresses have tx history beyond X/2, calculate
      another X and rescan.  This will usually only have to be done once, but
      may need to be repeated for super-active wallets.  
      (In the future, I may add functionality to sample the gap between address
      usage, so I can more-intelligently determine when we're at the end...)
      """
      
      
      expectOutput = False
      if not wait==False and (self.alwaysBlock or wait==True):
         expectOutput = True

      self.aboutToRescan = True

      rndID = int(random.uniform(0,100000000)) 
      self.inputQueue.put([BDMINPUTTYPE.WalletRecoveryScan, rndID, expectOutput, pywlt])
      LOGINFO('Wallet recovery scan requested')
      return self.waitForOutputIfNecessary(expectOutput, rndID)



   #############################################################################
   @ActLikeASingletonBDM
   def __checkBDMReadyToServeData(self):
      if self.blkMode==BLOCKCHAINMODE.Rescanning:
         LOGERROR('Requested blockchain data while scanning.  Don\'t do this!')
         LOGERROR('Check self.getBlkModeStr()==BLOCKCHAINMODE.Full before')
         LOGERROR('making requests!  Skipping request')
         return False
      if self.blkMode==BLOCKCHAINMODE.Offline:
         LOGERROR('Requested blockchain data while BDM is in offline mode.')
         LOGERROR('Please start the BDM using TheBDM.setOnlineMode() before,')
         LOGERROR('and then wait for it to complete, before requesting data.')
         return False
      if not self.bdm.isInitialized():
         LOGERROR('The BDM thread declares the BDM is ready, but the BDM ')
         LOGERROR('itself reports that it is not initialized!  What is ')
         LOGERROR('going on...?')
         return False
         

      return True

   #############################################################################
   @ActLikeASingletonBDM
   def getTxByHash(self, txHash):
      """
      All calls that retrieve blockchain data are blocking calls.  You have 
      no choice in the matter!
      """
      #if not self.__checkBDMReadyToServeData():
         #return None

      rndID = int(random.uniform(0,100000000)) 
      self.inputQueue.put([BDMINPUTTYPE.TxRequested, rndID, True, txHash])

      try:
         result = self.outputQueue.get(True, 10)
         if result==None:
            LOGERROR('Requested tx does not exist:\n%s', binary_to_hex(txHash))
         return result
      except Queue.Empty:
         LOGERROR('Waited 10s for tx to be returned.  Abort')
         LOGERROR('ID: getTxByHash (%d)', rndID)
         return None
         #LOGERROR('Going to block until we get something...')
         #return self.outputQueue.get(True)
         
      return None


   ############################################################################
   @ActLikeASingletonBDM
   def getHeaderByHash(self, headHash):
      """
      All calls that retrieve blockchain data are blocking calls.  You have 
      no choice in the matter!
      """
      #if not self.__checkBDMReadyToServeData():
         #return None

      rndID = int(random.uniform(0,100000000)) 
      self.inputQueue.put([BDMINPUTTYPE.HeaderRequested, rndID, True, headHash])

      try:
         result = self.outputQueue.get(True, 10)
         if result==None:
            LOGERROR('Requested header does not exist:\n%s', \
                                          binary_to_hex(headHash))
         return result
      except Queue.Empty:
         LOGERROR('Waited 10s for header to be returned.  Abort')
         LOGERROR('ID: getTxByHash (%d)', rndID)
         #LOGERROR('Going to block until we get something...')
         #return self.outputQueue.get(True)

      return None


   #############################################################################
   @ActLikeASingletonBDM
   def getBlockByHash(self,headHash):
      """
      All calls that retrieve blockchain data are blocking calls.  You have 
      no choice in the matter!

      This retrives the full block, not just the header, encoded the same 
      way as it is in the blkXXXX.dat files (including magic bytes and 
      block 4-byte block size)
      """
      #if not self.__checkBDMReadyToServeData():
         #return None

      rndID = int(random.uniform(0,100000000)) 
      self.inputQueue.put([BDMINPUTTYPE.BlockRequested, rndID, True, headHash])

      try:
         result = self.outputQueue.get(True, 10)
         if result==None:
            LOGERROR('Requested block does not exist:\n%s', \
                                          binary_to_hex(headHash))
         return result
      except Queue.Empty:
         LOGERROR('Waited 10s for block to be returned.  Abort')
         LOGERROR('ID: getTxByHash (%d)', rndID)
         #LOGERROR('Going to block until we get something...')
         #return self.outputQueue.get(True)

      return None


   #############################################################################
   @ActLikeASingletonBDM
   def getAddressBook(self, wlt):
      """
      Address books are constructed from Blockchain data, which means this 
      must be a blocking method.  
      """
      rndID = int(random.uniform(0,100000000)) 
      if isinstance(wlt, PyBtcWallet):
         self.inputQueue.put([BDMINPUTTYPE.AddrBookRequested, rndID, True, wlt.cppWallet])
      elif isinstance(wlt, Cpp.BtcWallet):
         self.inputQueue.put([BDMINPUTTYPE.AddrBookRequested, rndID, True, wlt])

      try:
         result = self.outputQueue.get(True, self.mtWaitSec)
         return result
      except Queue.Empty:
         LOGERROR('Waited %ds for addrbook to be returned.  Abort' % self.mtWaitSec)
         LOGERROR('ID: getTxByHash (%d)', rndID)
         #LOGERROR('Going to block until we get something...')
         #return self.outputQueue.get(True)

      return None

   #############################################################################
   @ActLikeASingletonBDM
   def addNewZeroConfTx(self, rawTx, timeRecv, writeToFile, wait=None):
      expectOutput = False
      if not wait==False and (self.alwaysBlock or wait==True):
         expectOutput = True

      rndID = int(random.uniform(0,100000000)) 
      self.inputQueue.put([BDMINPUTTYPE.ZeroConfTxToInsert, rndID, expectOutput, rawTx, timeRecv])
      return self.waitForOutputIfNecessary(expectOutput, rndID)
      
   #############################################################################
   @ActLikeASingletonBDM
   def registerScrAddr(self, scrAddr, isFresh=False, wait=None):
      """
      This is for a generic address:  treat it as imported (requires rescan)
      unless specifically specified otherwise
      """
      if isFresh:
         self.registerNewScrAddr(scrAddr, wait=wait)
      else:
         self.registerImportedScrAddr(scrAddr, wait=wait)

 
   #############################################################################
   @ActLikeASingletonBDM
   def registerNewScrAddr(self, scrAddr, wait=None):
      """
      Variable isFresh==True means the address was just [freshly] created,
      and we need to watch for transactions with it, but we don't need
      to rescan any blocks
      """
      expectOutput = False
      if not wait==False and (self.alwaysBlock or wait==True):
         expectOutput = True

      rndID = int(random.uniform(0,100000000)) 
      self.inputQueue.put([BDMINPUTTYPE.RegisterAddr, rndID, expectOutput, scrAddr, True])

      return self.waitForOutputIfNecessary(expectOutput, rndID)



   #############################################################################
   @ActLikeASingletonBDM
   def registerImportedScrAddr(self, scrAddr, \
                                     firstTime=UINT32_MAX, \
                                     firstBlk=UINT32_MAX, \
                                     lastTime=0, \
                                     lastBlk=0, wait=None):
      """
      TODO:  Need to clean up the first/last blk/time variables.  Rather,
             I need to make sure they are maintained and applied intelligently
             and consistently
      """
      expectOutput = False
      if not wait==False and (self.alwaysBlock or wait==True):
         expectOutput = True

      rndID = int(random.uniform(0,100000000)) 
      self.inputQueue.put([BDMINPUTTYPE.RegisterAddr, rndID, expectOutput, \
                           scrAddr, [firstTime, firstBlk, lastTime, lastBlk]])

      return self.waitForOutputIfNecessary(expectOutput, rndID)

         
   #############################################################################
   @ActLikeASingletonBDM
   def registerWallet(self, wlt, isFresh=False, wait=None):
      """
      Will register a C++ wallet or Python wallet
      """
      if isinstance(wlt, PyBtcWallet):
         scrAddrs = [Hash160ToScrAddr(a.getAddr160()) for a in wlt.getAddrList()]

         if isFresh:
            for scrad in scrAddrs:
               self.registerNewScrAddr(scrad, wait=wait)
         else:
            for scrad in scrAddrs:
               self.registerImportedScrAddr(scrad, wait=wait)

         if not wlt in self.pyWltList:
            self.pyWltList.append(wlt)

      elif isinstance(wlt, Cpp.BtcWallet):
         # We are using this branch to add multi-sig wallets, which aren't
         # even help as python wallets, only low-level BtcWallets 
         naddr = wlt.getNumScrAddr()

         for a in range(naddr):
            self.registerScrAddr(wlt.getScrAddrObjByIndex(a).getScrAddr(), 
                                                          isFresh, wait=wait)

         if not wlt in self.cppWltList:
            self.cppWltList.append(wlt)
      else:
         LOGERROR('Unrecognized object passed to registerWallet function')
               


   
   
   #############################################################################
   # These bdm_direct methods feel like a hack.  They probably are.  I need 
   # find an elegant way to get the code normally run outside the BDM thread,
   # to be able to run inside the BDM thread without using the BDM queue (since 
   # the queue is specifically FOR non-BDM-thread calls).  For now, the best 
   # I can do is create non-private versions of these methods that access BDM
   # methods directly, but should not be used under any circumstances, unless
   # we know for sure that the BDM ultimately called this method.
   @ActLikeASingletonBDM
   def registerScrAddr_bdm_direct(self, scrAddr, timeInfo):
      """ 
      Something went awry calling __registerScrAddrNow from the PyBtcWallet
      code (apparently I don't understand __methods).  Use this method to 
      externally bypass the BDM thread queue and register the address 
      immediately.  

      THIS METHOD IS UNSAFE UNLESS CALLED FROM A METHOD RUNNING IN THE BDM THREAD
      This method can be called from a non BDM class, but should only do so if 
      that class method was called by the BDM (thus, no conflicts)
      """
      self.__registerScrAddrNow(scrAddr, timeInfo)


   #############################################################################
   @ActLikeASingletonBDM
   def scanBlockchainForTx_bdm_direct(self, cppWlt, startBlk=0, endBlk=UINT32_MAX):
      """ 
      THIS METHOD IS UNSAFE UNLESS CALLED FROM A METHOD RUNNING IN THE BDM THREAD
      This method can be called from a non BDM class, but should only do so if 
      that class method was called by the BDM (thus, no conflicts)
      """
      self.bdm.scanRegisteredTxForWallet(cppWlt, startBlk, endBlk)
   
   #############################################################################
   @ActLikeASingletonBDM
   def scanRegisteredTxForWallet_bdm_direct(self, cppWlt, startBlk=0, endBlk=UINT32_MAX):
      """ 
      THIS METHOD IS UNSAFE UNLESS CALLED FROM A METHOD RUNNING IN THE BDM THREAD
      This method can be called from a non BDM class, but should only do so if 
      that class method was called by the BDM (thus, no conflicts)
      """
      self.bdm.scanRegisteredTxForWallet(cppWlt, startBlk, endBlk)

   #############################################################################
   @ActLikeASingletonBDM
   def getTopBlockHeight_bdm_direct(self):
      """ 
      THIS METHOD IS UNSAFE UNLESS CALLED FROM A METHOD RUNNING IN THE BDM THREAD
      This method can be called from a non BDM class, but should only do so if 
      that class method was called by the BDM (thus, no conflicts)
      """
      return self.bdm.getTopBlockHeight()



   #############################################################################
   @ActLikeASingletonBDM
   def getLoadProgress(self):
      """
      This method does not actually work!  The load progress in bytes is not
      updated properly while the BDM thread is scanning.  It might have to 
      emit this information explicitly in order to be useful.
      """
      return (self.bdm.getLoadProgressBytes(), self.bdm.getTotalBlockchainBytes())
   

   #############################################################################
   @ActLikeASingletonBDM
   def __registerScrAddrNow(self, scrAddr, timeInfo):
      """
      Do the registration right now.  This should not be called directly
      outside of this class.  This is only called by the BDM thread when
      any previous scans have been completed
      """

      if isinstance(timeInfo, bool):
         isFresh = timeInfo
         if isFresh:
            # We claimed to have just created this ScrAddr...(so no rescan needed)
            self.masterCppWallet.addNewScrAddress(scrAddr)
         else:
            self.masterCppWallet.addScrAddress_1_(scrAddr)
      else:
         if isinstance(timeInfo, (list,tuple)) and len(timeInfo)==4:
            self.masterCppWallet.addScrAddress_5_(scrAddr, *timeInfo)
         else:
            LOGWARN('Unrecognized time information in register method.')
            LOGWARN('   Data: %s', str(timeInfo))
            LOGWARN('Assuming imported key requires full rescan...')
            self.masterCppWallet.addScrAddress_1_(scrAddr)



   #############################################################################
   @TimeThisFunction
   @ActLikeASingletonBDM
   def __startLoadBlockchain(self):
      """
      This should only be called by the threaded BDM, and thus there should
      never be a conflict.  
      """
      if self.blkMode == BLOCKCHAINMODE.Rescanning:
         LOGERROR('Blockchain is already scanning.  Was this called already?')         
         return
      elif self.blkMode == BLOCKCHAINMODE.Full:
         LOGERROR('Blockchain has already been loaded -- maybe we meant')
         LOGERROR('to call startRescanBlockchain()...?')
         return
      elif not self.blkMode == BLOCKCHAINMODE.Uninitialized:
         LOGERROR('BDM should be in "Uninitialized" mode before starting ')
         LOGERROR('the initial scan.  If BDM is in offline mode, you should ')
         LOGERROR('switch it to online-mode, first, then request the scan.')
         LOGERROR('Continuing with the scan, anyway.')
         

      # Remove "blkfiles.txt" to make sure we get accurate TGO
      bfile = os.path.join(ARMORY_HOME_DIR,'blkfiles.txt')
      if os.path.exists(bfile):
         os.remove(bfile)

      # Check for the existence of the Bitcoin-Qt directory
      if not os.path.exists(self.btcdir):
         raise FileExistsError, ('Directory does not exist: %s' % self.btcdir)

      blkdir = os.path.join(self.btcdir, 'blocks')
      blk1st = os.path.join(blkdir, 'blk00000.dat')

      # ... and its blk000X.dat files
      if not os.path.exists(blk1st):
         LOGERROR('Blockchain data not available: %s', blk1st)
         self.prefMode = BLOCKCHAINMODE.Offline
         raise FileExistsError, ('Blockchain data not available: %s' % self.blk1st)

      # We have the data, we're ready to go
      self.blkMode = BLOCKCHAINMODE.Rescanning
      self.aboutToRescan = False
      
      armory_homedir = ARMORY_HOME_DIR
      blockdir = blkdir
      leveldbdir = self.ldbdir
      
      if OS_WINDOWS:
         if isinstance(ARMORY_HOME_DIR, unicode):
            armory_homedir = ARMORY_HOME_DIR.encode('utf8')
         if isinstance(blkdir, unicode):
            blockdir = blkdir.encode('utf8')
         if isinstance(self.ldbdir, unicode):
            leveldbdir = self.ldbdir.encode('utf8')

      LOGINFO('Setting Armory Home Dir: %s' % armory_homedir)
      LOGINFO('Setting BlkFile Dir:     %s' % blockdir)
      LOGINFO('Setting LevelDB Dir:     %s' % leveldbdir)

      self.bdm.SetDatabaseModes(ARMORY_DB_BARE, DB_PRUNE_NONE);
      self.bdm.SetHomeDirLocation(armory_homedir)
      self.bdm.SetBlkFileLocation(blockdir)
      self.bdm.SetLevelDBLocation(leveldbdir)
      self.bdm.SetBtcNetworkParams( GENESIS_BLOCK_HASH, \
                                    GENESIS_TX_HASH,    \
                                    MAGIC_BYTES)

      # The master wallet contains all addresses of all wallets registered
      self.bdm.registerWallet(self.masterCppWallet)

      # Now we actually startup the BDM and run with it
      if CLI_OPTIONS.rebuild:
         self.bdm.doInitialSyncOnLoad_Rebuild()
      elif CLI_OPTIONS.rescan:
         self.bdm.doInitialSyncOnLoad_Rescan()
      else:
         self.bdm.doInitialSyncOnLoad()

      # The above op populates the BDM with all relevent tx, but those tx
      # still need to be scanned to collect the wallet ledger and UTXO sets
      self.bdm.scanBlockchainForTx(self.masterCppWallet)
      self.bdm.saveScrAddrHistories()

      
   #############################################################################
   @TimeThisFunction
   @ActLikeASingletonBDM
   def __startRescanBlockchain(self, scanType='AsNeeded'):
      """
      This should only be called by the threaded BDM, and thus there should
      never be a conflict.  
   
      If we don't force a full scan, we let TheBDM figure out how much of the 
      chain needs to be rescanned.  Which may not be very much.  We may 
      force a full scan if we think there's an issue with balances.
      """
      if self.blkMode==BLOCKCHAINMODE.Offline:
         LOGERROR('Blockchain is in offline mode.  How can we rescan?')
      elif self.blkMode==BLOCKCHAINMODE.Uninitialized:
         LOGERROR('Blockchain was never loaded.  Why did we request rescan?')

      # Remove "blkfiles.txt" to make sure we get accurate TGO
      bfile = os.path.join(ARMORY_HOME_DIR,'blkfiles.txt')
      if os.path.exists(bfile):
         os.remove(bfile)

      if not self.isDirty():
         LOGWARN('It does not look like we need a rescan... doing it anyway')

      if scanType=='AsNeeded':
         if self.bdm.numBlocksToRescan(self.masterCppWallet) < 144:
            LOGINFO('Rescan requested, but <1 day\'s worth of block to rescan')
            self.blkMode = BLOCKCHAINMODE.LiteScanning
         else:
            LOGINFO('Rescan requested, and very large scan is necessary')
            self.blkMode = BLOCKCHAINMODE.Rescanning


      self.aboutToRescan = False
      
      if scanType=='AsNeeded':
         self.bdm.doSyncIfNeeded()
      elif scanType=='ForceRescan':
         LOGINFO('Forcing full rescan of blockchain')
         self.bdm.doFullRescanRegardlessOfSync()
         self.blkMode = BLOCKCHAINMODE.Rescanning
      elif scanType=='ForceRebuild':
         LOGINFO('Forcing full rebuild of blockchain database')
         self.bdm.doRebuildDatabases()
         self.blkMode = BLOCKCHAINMODE.Rescanning

      # missingBlocks = self.bdm.missingBlockHashes()
      
      self.bdm.scanBlockchainForTx(self.masterCppWallet)
      self.bdm.saveScrAddrHistories()


   #############################################################################
   @TimeThisFunction
   @ActLikeASingletonBDM
   def __startRecoveryRescan(self, pywlt):
      """
      This should only be called by the threaded BDM, and thus there should
      never be a conflict.  

      In order to work cleanly with the threaded BDM, the search code 
      needed to be integrated directly here, instead of being called
      from the PyBtcWallet method.  Because that method is normally called 
      from outside the BDM thread, but this method is only called from 
      _inside_ the BDM thread.  Those calls use the BDM stack which will
      deadlock waiting for the itself before it can move on...

      Unfortunately, because of this, we have to break a python-class 
      privacy rules:  we are accessing the PyBtcWallet object as if this
      were PyBtcWallet code (accessing properties directly).  
      """
      if not isinstance(pywlt, PyBtcWallet):
         LOGERROR('Only python wallets can be passed for recovery scans')
         return

      if self.blkMode==BLOCKCHAINMODE.Offline:
         LOGERROR('Blockchain is in offline mode.  How can we rescan?')
      elif self.blkMode==BLOCKCHAINMODE.Uninitialized:
         LOGERROR('Blockchain was never loaded.  Why did we request rescan?')


      self.blkMode = BLOCKCHAINMODE.Rescanning
      self.aboutToRescan = False

      #####

      # Whenever calling PyBtcWallet methods from BDM, set flag
      prevCalledFromBDM = pywlt.calledFromBDM
      pywlt.calledFromBDM = True
      
      # Do the scan...
      pywlt.freshImportFindHighestIndex()

      # Unset flag when done
      pywlt.calledFromBDM = prevCalledFromBDM

      #####
      self.bdm.scanRegisteredTxForWallet(self.masterCppWallet)

   

   #############################################################################
   @TimeThisFunction
   @ActLikeASingletonBDM
   def __readBlockfileUpdates(self):
      ''' 
      This method can be blocking... it always has been without a problem,
      because the block file updates are always fast.  But I have to assume 
      that it theoretically *could* take a while, and the caller might care.
      ''' 
      if self.blkMode == BLOCKCHAINMODE.Offline:
         LOGERROR('Can\'t update blockchain in %s mode!', self.getBDMState())
         return

      self.blkMode = BLOCKCHAINMODE.LiteScanning
      nblk = self.bdm.readBlkFileUpdate() 

      # On new blocks, re-save the histories
      # ACR: This was removed because the histories get saved already on the
      #      call to TheBDM.updateWalletsAfterScan()
      #if nblk > 0:
         #self.bdm.saveScrAddrHistories()

      return nblk
         

   #############################################################################
   @TimeThisFunction
   @ActLikeASingletonBDM
   def __updateWalletsAfterScan(self):
      """
      This will actually do a scan regardless of whether it is currently
      "after scan", but it will usually only be requested right after a
      full rescan 
      """

      numToRescan = 0
      for pyWlt in self.pyWltList:
         thisNum = self.bdm.numBlocksToRescan(pyWlt.cppWallet)
         numToRescan = max(numToRescan, thisNum)

      for cppWlt in self.cppWltList:
         thisNum = self.bdm.numBlocksToRescan(cppWlt)
         numToRescan = max(numToRescan, thisNum)

      if numToRescan<144:
         self.blkMode = BLOCKCHAINMODE.LiteScanning
      else:
         self.blkMode = BLOCKCHAINMODE.Rescanning


      for pyWlt in self.pyWltList:
         # We use "calledFromBDM" to avoid deadlocking -- no other messages
         # on the BDM queue can be processed until this function returns, but 
         # the syncWithBlockchain call will put a request on the queue
         # and wait for the BDM to process it.  We use "calledFromBDM" to 
         # request that the call go around the queue, right to the self.bdm
         # object.
         prevCFB = pyWlt.calledFromBDM
         pyWlt.calledFromBDM = True
         pyWlt.syncWithBlockchain()
         pyWlt.calledFromBDM = prevCFB


      for cppWlt in self.cppWltList:
         # The pre-leveldb version of Armory specifically required to call
         #
         #    scanRegisteredTxForWallet   (scan already-collected reg tx)
         #
         # instead of 
         #
         #    scanBlockchainForTx         (search for reg tx then scan)
         #
         # Because the second one will induce a full rescan to find all new
         # registeredTx, if we recently imported an addr or wallet.  If we 
         # imported but decided not to rescan yet, we wan tthe first one,  
         # which only scans the registered tx that are already collected 
         # (including new blocks, but not previous blocks).  
         #
         # NOTE:  In versions 0.90-0.92, the following paragraph is not
         #        actually true:  we don't have supernode support.  Yet,
         #        we never converted this back to scanRegisteredTxForWallet.
         #        Hmmm...
         # However, with the leveldb stuff only supporting super-node, there
         # is no rescanning, thus it's safe to always call scanBlockchainForTx,
         # which grabs everything from the database almost instantaneously.  
         # However we may want to re-examine this after we implement new
         # database modes of operation
         #self.bdm.scanRegisteredTxForWallet(cppWlt)
         self.bdm.scanBlockchainForTx(cppWlt)

      # At this point all wallets should be 100% up-to-date, save the histories
      # to be reloaded next time
      self.bdm.saveScrAddrHistories()



   #############################################################################
   @ActLikeASingletonBDM
   def __shutdown(self):
      if not self.blkMode == BLOCKCHAINMODE.Rescanning:
         self.bdm.saveScrAddrHistories()

      self.__reset()
      self.blkMode = BLOCKCHAINMODE.Offline
      self.doShutdown = True

   #############################################################################
   @ActLikeASingletonBDM
   def __fullRebuild(self):
      self.bdm.destroyAndResetDatabases()
      self.__reset()
      self.__startLoadBlockchain()

   #############################################################################
   @ActLikeASingletonBDM
   def __reset(self):
      LOGERROR('Resetting BDM and all wallets')
      self.bdm.Reset()
      
      if self.blkMode in (BLOCKCHAINMODE.Full, BLOCKCHAINMODE.Rescanning):
         # Uninitialized means we want to be online, but haven't loaded yet
         self.blkMode = BLOCKCHAINMODE.Uninitialized
      elif not self.blkMode==BLOCKCHAINMODE.Offline:
         return
         
      self.bdm.resetRegisteredWallets()

      # Flags
      self.startBDM     = False
      #self.btcdir       = BTC_HOME_DIR

      # Lists of wallets that should be checked after blockchain updates
      self.pyWltList    = []   # these will be python refs
      self.cppWltList   = []   # these will be C++ refs


      # The BlockDataManager is easier to use if you put all your addresses
      # into a C++ BtcWallet object, and let it 
      self.masterCppWallet = Cpp.BtcWallet()
      self.bdm.registerWallet(self.masterCppWallet)


   #############################################################################
   @ActLikeASingletonBDM
   def __getFullBlock(self, headerHash):
      headerObj = self.bdm.getHeaderByHash(headerHash)
      if not headerObj:
         return None

      rawTxList = []
      txList = headerObj.getTxRefPtrList()
      for txref in txList:
         tx = txref.getTxCopy() 
         rawTxList.append(tx.serialize())

      numTxVarInt = len(rawTxList)
      blockBytes = 80 + len(numTxVarInt) + sum([len(tx) for tx in rawTxList])

      rawBlock = MAGIC_BYTES
      rawBlock += int_to_hex(blockBytes, endOut=LITTLEENDIAN, widthBytes=4)
      rawBlock += headerObj.serialize() 
      rawBlock += packVarInt(numTxVarInt)  
      rawBlock += ''.join(rawTxList)
      return rawBlock

   
   #############################################################################
   @ActLikeASingletonBDM
   def getBDMInputName(self, i):
      for name in dir(BDMINPUTTYPE):
         if getattr(BDMINPUTTYPE, name)==i:
            return name   

   #############################################################################
   @TimeThisFunction
   @ActLikeASingletonBDM
   def createAddressBook(self, cppWlt):
      return cppWlt.createAddressBook()

   ###############################
   # This is critical code used when kicking off ArmoryQt and armoryd. Ideally, all
   # initialization would happen here, but there's too much GUI stuff to make it
   # work. So, we'll do what we can here, which is a significant amount.
   # INPUT: A Python wallet map, a C++ lockbox wallet map, a flag indicating if the
   #        memory pool has been initialized, and the BDM.
   # OUTPUT: The top block height and a flag indicating that the mem pool has been
   #         initialized.
   #######################################################################
   @ActLikeASingletonBDM
   def finishLoadBlockchainCommon(self, inWltMap, inLBWltMap, initMemPool):
      retVal = self.getTopBlockHeight()
   
      # If necessary, initialize the mem pool.
      if not initMemPool:
         mempoolfile = os.path.join(ARMORY_HOME_DIR,'mempool.bin')
         clearpoolfile = os.path.join(ARMORY_HOME_DIR,'clearmempool.flag')
         if os.path.exists(clearpoolfile):
            LOGINFO('clearmempool.flag found.  Clearing memory pool')
            os.remove(clearpoolfile)
            if os.path.exists(mempoolfile):
               os.remove(mempoolfile)
         elif os.path.exists(mempoolfile):
            memfile = open(mempoolfile, 'rb')
            memdata = memfile.read()
            memfile.close()
         
            binunpacker = BinaryUnpacker(memdata)
            try:
               while binunpacker.getRemainingSize() > 0:
                  binunpacker.get(UINT64)
                  PyTx().unserialize(binunpacker)
            except:
               os.remove(mempoolfile)
               LOGWARN('Memory pool file was corrupt and has been deleted. No further ' \
                       'action is required.')
                  
         cppMempoolFile = mempoolfile
         if OS_WINDOWS and isinstance(mempoolfile, unicode):
            cppMempoolFile = mempoolfile.encode('utf8')
         self.enableZeroConf(cppMempoolFile)
   
      # Sync each Python wallet.
      for wltID in inWltMap.iterkeys():
         LOGINFO('Syncing wallet: %s', wltID)
         inWltMap[wltID].setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
         inWltMap[wltID].syncWithBlockchainLite(0)
         inWltMap[wltID].detectHighestUsedIndex(True)  # expand wlt if necessary
         inWltMap[wltID].fillAddressPool()
   
      # The lockboxes use C++ wallets 'til the 2.0 wallets are ready. We just need
      # to scan each wallet.
      for lbID,cppWallet in inLBWltMap.iteritems():
         self.scanRegisteredTxForWallet(cppWallet, 0, wait=True)
   
      LOGINFO('Blockchain load and wallet sync finished')
      return (retVal, True)


   @ActLikeASingletonBDM
   def run(self):
      """
      This thread runs in an infinite loop, waiting for things to show up
      on the self.inputQueue, and then processing those entries.  If there
      are no requests to the BDM from the main thread, this thread will just
      sit idle (in a CPU-friendly fashion) until something does.
      """

      while not self.doShutdown:
         # If there were any errors, we will have that many extra output
         # entries on the outputQueue.  We clear them off so that this 
         # thread can be re-sync'd with the main thread
         try:
            while self.errorOut>0:
               self.outputQueue.get_nowait()
               self.errorOut -= 1
         except Queue.Empty:
            LOGERROR('ErrorOut var over-represented number of errors!')
            self.errorOut = 0
               

         # Now start the main 
         try:
            try:
               inputTuple = self.inputQueue.get_nowait()
               # If we don't error out, we have stuff to process right now
            except Queue.Empty:
               # We only switch to offline/full/uninitialzed when the queue
               # is empty.  After that, then we block in a CPU-friendly way
               # until data shows up on the Queue
               if self.prefMode==BLOCKCHAINMODE.Full:
                  if self.bdm.isInitialized():
                     self.blkMode = BLOCKCHAINMODE.Full
                  else:
                     self.blkMode = BLOCKCHAINMODE.Uninitialized
               else:
                  self.blkMode = BLOCKCHAINMODE.Offline

               self.currentActivity = 'None'

               # Block until something shows up.
               inputTuple = self.inputQueue.get()
            except:
               LOGERROR('Unknown error in BDM thread')



            # The first list element is always the BDMINPUTTYPE (command)
            # The second argument is whether the caller will be waiting 
            # for the output:  which means even if it's None, we need to
            # put something on the output queue.
            cmd          = inputTuple[0]
            rndID        = inputTuple[1]
            expectOutput = inputTuple[2]
            output       = None

            # Some variables that can be queried externally to figure out 
            # what the BDM is currently doing
            self.currentActivity = self.getBDMInputName(inputTuple[0])
            self.currentID = rndID

            if cmd == BDMINPUTTYPE.RegisterAddr:
               scrAddr,timeInfo = inputTuple[3:]
               self.__registerScrAddrNow(scrAddr, timeInfo)

            elif cmd == BDMINPUTTYPE.ZeroConfTxToInsert:
               rawTx  = inputTuple[3]
               timeIn = inputTuple[4]
               if isinstance(rawTx, PyTx):
                  rawTx = rawTx.serialize()
               self.bdm.addNewZeroConfTx(rawTx, timeIn, True)
               
            elif cmd == BDMINPUTTYPE.HeaderRequested:
               headHash = inputTuple[3]
               rawHeader = self.bdm.getHeaderByHash(headHash)
               if rawHeader:
                  output = rawHeader
               else:
                  output = None

            elif cmd == BDMINPUTTYPE.TxRequested:
               txHash = inputTuple[3] 
               rawTx = self.bdm.getTxByHash(txHash)
               if rawTx:
                  output = rawTx
               else:
                  output = None
                  
            elif cmd == BDMINPUTTYPE.BlockRequested:
               headHash = inputTuple[3] 
               rawBlock = self.__getFullBlock(headHash)
               if rawBlock:
                  output = rawBlock
               else:
                  output = None
                  LOGERROR('Requested header does not exist:\n%s', \
                                             binary_to_hex(headHash))

            elif cmd == BDMINPUTTYPE.HeaderAtHeightRequested:
               height = inputTuple[3] 
               rawHeader = self.bdm.getHeaderByHeight(height)
               if rawHeader:
                  output = rawHeader
               else:
                  output = None
                  LOGERROR('Requested header does not exist:\nHeight=%s', height)
         
            elif cmd == BDMINPUTTYPE.BlockAtHeightRequested:
               height = inputTuple[3] 
               rawBlock = self.__getFullBlock(height)
               if rawBlock:
                  output = rawBlock
               else:
                  output = None
                  LOGERROR('Requested header does not exist:\nHeight=%s', height)

            elif cmd == BDMINPUTTYPE.AddrBookRequested:
               cppWlt = inputTuple[3] 
               output = self.createAddressBook(cppWlt)
                                             
            elif cmd == BDMINPUTTYPE.UpdateWallets:
               self.__updateWalletsAfterScan()

            elif cmd == BDMINPUTTYPE.RescanRequested:
               scanType = inputTuple[3]
               if not scanType in ('AsNeeded', 'ForceRescan', 'ForceRebuild'):
                  LOGERROR('Invalid scan type for rescanning: ' + scanType)
                  scanType = 'AsNeeded'
               self.__startRescanBlockchain(scanType)

            elif cmd == BDMINPUTTYPE.WalletRecoveryScan:
               LOGINFO('Wallet Recovery Scan Requested')
               pywlt = inputTuple[3]
               self.__startRecoveryRescan(pywlt)
               
            elif cmd == BDMINPUTTYPE.ReadBlkUpdate:
               output = self.__readBlockfileUpdates()

            elif cmd == BDMINPUTTYPE.Passthrough:
               # If the caller is waiting, then it is notified by output
               funcName = inputTuple[3]
               funcArgs = inputTuple[4:]
               output = getattr(self.bdm, funcName)(*funcArgs)

            elif cmd == BDMINPUTTYPE.Shutdown:
               LOGINFO('Shutdown Requested')
               self.__shutdown()

            elif cmd == BDMINPUTTYPE.ForceRebuild:
               LOGINFO('Rebuild databases requested')
               self.__fullRebuild()

            elif cmd == BDMINPUTTYPE.Reset:
               LOGINFO('Reset Requested')
               self.__reset()
               
            elif cmd == BDMINPUTTYPE.GoOnlineRequested:
               LOGINFO('Go online requested')
               # This only sets the blkMode to what will later be
               # recognized as online-requested, or offline
               self.prefMode = BLOCKCHAINMODE.Full
               if self.bdm.isInitialized():
                  # The BDM was started and stopped at one point, without
                  # being reset.  It can safely pick up from where it 
                  # left off
                  self.__readBlockfileUpdates()
               else:
                  self.blkMode = BLOCKCHAINMODE.Uninitialized
                  self.__startLoadBlockchain()

            elif cmd == BDMINPUTTYPE.GoOfflineRequested:
               LOGINFO('Go offline requested')
               self.prefMode = BLOCKCHAINMODE.Offline

            self.inputQueue.task_done()
            if expectOutput:
               self.outputQueue.put(output)

         except Queue.Empty:
            continue
         except:
            inputName = self.getBDMInputName(inputTuple[0])
            LOGERROR('Error processing BDM input')
            #traceback.print_stack()
            LOGERROR('Received inputTuple: ' + inputName + ' ' + str(inputTuple))
            LOGERROR('Error processing ID (%d)', rndID)
            LOGEXCEPT('ERROR:')
            if expectOutput:
               self.outputQueue.put('BDM_REQUEST_ERROR')
            self.inputQueue.task_done()
            continue
           
      LOGINFO('BDM is shutdown.')
      
         
################################################################################
# Make TheBDM reference the asyncrhonous BlockDataManager wrapper if we are 
# running 
TheBDM = None
TheSDM = None
if CLI_OPTIONS.offline:
   LOGINFO('Armory loaded in offline-mode.  Will not attempt to load ')
   LOGINFO('blockchain without explicit command to do so.')
   TheBDM = BlockDataManagerThread(isOffline=True, blocking=False)
   TheBDM.start()

   # Also create the might-be-needed SatoshiDaemonManager
   TheSDM = SatoshiDaemonManager()

else:
   # NOTE:  "TheBDM" is sometimes used in the C++ code to reference the
   #        singleton BlockDataManager_LevelDB class object.  Here, 
   #        "TheBDM" refers to a python BlockDataManagerThead class 
   #        object that wraps the C++ version.  It implements some of 
   #        it's own methods, and then passes through anything it 
   #        doesn't recognize to the C++ object.
   LOGINFO('Using the asynchronous/multi-threaded BlockDataManager.')
   LOGINFO('Blockchain operations will happen in the background.  ')
   LOGINFO('Devs: check TheBDM.getBDMState() before asking for data.')
   LOGINFO('Registering addresses during rescans will queue them for ')
   LOGINFO('inclusion after the current scan is completed.')
   TheBDM = BlockDataManagerThread(isOffline=False, blocking=False)
   TheBDM.setDaemon(True)
   TheBDM.start()

   #if CLI_OPTIONS.doDebug or CLI_OPTIONS.netlog or CLI_OPTIONS.mtdebug:
   cppLogFile = os.path.join(ARMORY_HOME_DIR, 'armorycpplog.txt')
   
   cpplf = cppLogFile
   if OS_WINDOWS and isinstance(cppLogFile, unicode):
      cpplf = cppLogFile.encode('utf8')
   
   # For C++ logging, higher levels is more logging, 0 is disabled
   # For Python logging (in ArmoryUtils) it's reversed
   if CLI_OPTIONS.logDisable:
      TheBDM.StartCppLogging(cpplf, 0)
   else:
      TheBDM.StartCppLogging(cpplf, 4)
      TheBDM.EnableCppLogStdOut()

   # 32-bit linux has an issue with max open files.  Rather than modifying
   # the system, we can tell LevelDB to take it easy with max files to open
   if OS_LINUX and not SystemSpecs.IsX64:
      LOGINFO('Lowering max-open-files parameter in LevelDB for 32-bit linux')
      TheBDM.setMaxOpenFiles(75)

   # Override the above if they explicitly specify it as CLI arg
   if CLI_OPTIONS.maxOpenFiles > 0:
      LOGINFO('Overriding max files via command-line arg')
      TheBDM.setMaxOpenFiles( CLI_OPTIONS.maxOpenFiles )

   #LOGINFO('LevelDB max-open-files is %d', TheBDM.getMaxOpenFiles())

   # Also load the might-be-needed SatoshiDaemonManager
   TheSDM = SatoshiDaemonManager()


# Put the import at the end to avoid circular reference problem
from armoryengine.PyBtcWallet import PyBtcWallet, BLOCKCHAIN_READONLY
from armoryengine.Transaction import PyTx

