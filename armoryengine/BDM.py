################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
import Queue
import os.path
import random
import threading
import traceback

from armoryengine.ArmoryUtils import *
from SDM import SatoshiDaemonManager
from armoryengine.Timer import TimeThisFunction
import CppBlockUtils as Cpp
from armoryengine.BinaryPacker import UINT64


def newTheBDM(isOffline=False):
   global TheBDM
   if TheBDM and TheBDM.getState() != 'Uninitialized':
      TheBDM.execCleanShutdown()
   TheBDM = BlockDataManager(isOffline=isOffline)

class PySide_CallBack(Cpp.BDM_CallBack):
   def __init__(self, bdm):
      Cpp.BDM_CallBack.__init__(self)
      self.bdm = bdm
      self.bdm.progressComplete=0
      self.bdm.secondsRemaining=0
      self.bdm.progressPhase=0
      
   def run(self, action, arg, block):
      act = ''
      arglist = []
      
      # AOTODO replace with constants
      
      if action == 1:
         act = 'finishLoadBlockchain'
         TheBDM.currentBlock = block
         TheBDM.setState('BlockchainReady')
      elif action == 2:
         act = 'sweepAfterScanList'
      elif action == 3:
         act = 'newZC'
         castArg = Cpp.BtcUtils_cast_to_LedgerVector(arg)
         arglist = castArg
      elif action == 4:
         act = 'newblock'
         castArg = Cpp.BtcUtils_cast_to_int(arg)
         arglist.append(castArg)
         TheBDM.currentBlock = block
      elif action == 5:
         act = 'refresh'
   
      cppPushTrigger[0](act, arglist)
      
   def progress(self, phase, walletId, prog, seconds):
      try:
         self.bdm.progressPhase = phase
         self.bdm.walletId = walletId
         self.bdm.progressComplete = prog
         self.bdm.secondsRemaining = seconds
      except:
         LOGEXCEPT('Error in running progress callback')
         print sys.exc_info()

class BDM_Inject(Cpp.BDM_Inject):
   def __init__(self):
      Cpp.BDM_Inject.__init__(self)
      self.command = None
      self.response = None
      self.hasResponse = False
      
   def run(self):
      try:
         if self.command:
            cmd = self.command
            self.command = None
            self.response = cmd()
            self.hasResponse = True
      except:
         LOGEXCEPT('Error in running thread callback')
         print sys.exc_info()

   def runCommand(self, fn):
      self.hasResponse = False
      self.command = fn
      
      while not self.hasResponse:
         self.notify()
         self.waitRun();
      res = self.response
      self.response=None
      return res
      
def getCurrTimeAndBlock():
   time0 = long(RightNowUTC())
   return (time0, TheBDM.getCurrBlock())

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
class BlockDataManager(object):
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
   job is finished (usually using TheBDM.getState()=='BlockchainReady')

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
      
      NOTE: Do not call any methods on from init. The are all wrapped by ActLikeASingleton
      and will operate on the current entity stored in the global TheBDM variable, and not
      on the new instance. This is necesary for TI

   """
   #############################################################################
   def __init__(self, isOffline=False):
      super(BlockDataManager, self).__init__()

      #register callbacks
      self.callback = PySide_CallBack(self).__disown__()
      self.inject = BDM_Inject().__disown__()
      
      self.ldbdir = ""

      self.bdmThread = Cpp.BlockDataManagerThread(self.bdmConfig(forInit=True));
      self.bdm = self.bdmThread.bdm()
      self.bdv = self.bdmThread.bdv()

      # Flags
      self.aboutToRescan = False
      self.errorOut      = 0

      self.currentActivity = 'None'
      self.walletsToRegister = []
      
      if isOffline == True: self.bdmState = 'Offline'
      else: self.bdmState = 'Uninitialized'

      self.btcdir = BTC_HOME_DIR
      self.ldbdir = LEVELDB_DIR
      self.lastPctLoad = 0
      
      self.currentBlock = 0
      
   #############################################################################
   @ActLikeASingletonBDM
   def goOnline(self, satoshiDir=None, levelDBDir=None, armoryHomeDir=None):

      self.bdm.setConfig(self.bdmConfig())
      
      self.bdmState = 'Scanning'
      self.bdmThread.start(self.bdmMode(), self.callback, self.inject)

   #############################################################################
   @ActLikeASingletonBDM
   def registerWallet(self, wlt, isNew=False):
      toRegister = None
      if isinstance(wlt, PyBtcWallet):
         toRegister = wlt.cppWallet
      elif isinstance(wlt, Cpp.BtcWallet):
         toRegister = wlt
      else:
         LOGERROR('tried to register an invalid object as a wallet')
         return
      
      self.bdv.registerWallet(toRegister, isNew)

   #############################################################################
   @ActLikeASingletonBDM
   def setSatoshiDir(self, newBtcDir):
      if not os.path.exists(newBtcDir):
         LOGERROR('setSatoshiDir: directory does not exist: %s', newBtcDir)
         return

      self.btcdir = newBtcDir

   #############################################################################
   @ActLikeASingletonBDM
   def setLevelDBDir(self, ldbdir):
      if not os.path.exists(ldbdir):
         os.makedirs(ldbdir)

      self.ldbdir = ldbdir
   
   @ActLikeASingletonBDM
   def bdmMode(self):
      if CLI_OPTIONS.rebuild:
         mode = 2
      elif CLI_OPTIONS.rescan:
         mode = 1
      else:
         mode = 0
      return mode
      
   #############################################################################
   @ActLikeASingletonBDM
   def bdmConfig(self, armoryHomeDir=None, forInit=False):

      
      blkdir = ""
      
      if forInit == False:
      # Check for the existence of the Bitcoin-Qt directory         
         if not os.path.exists(self.btcdir):
            raise FileExistsError, ('Directory does not exist: %s' % self.btcdir)
   
         blkdir = os.path.join(self.btcdir, 'blocks')
         blk1st = os.path.join(blkdir, 'blk00000.dat')
   
         # ... and its blk000X.dat files
         if not os.path.exists(blk1st):
            LOGERROR('Blockchain data not available: %s', blk1st)
            raise FileExistsError, ('Blockchain data not available: %s' % blk1st)

      if armoryHomeDir == None:
         armoryHomeDir = ARMORY_HOME_DIR
      blockdir = blkdir
      leveldbdir = self.ldbdir
      
      if OS_WINDOWS:
         if isinstance(ARMORY_HOME_DIR, unicode):
            armoryHomeDir = ARMORY_HOME_DIR.encode('utf8')
         if isinstance(blkdir, unicode):
            blockdir = blkdir.encode('utf8')
         if isinstance(self.ldbdir, unicode):
            leveldbdir = self.ldbdir.encode('utf8')

      bdmConfig = Cpp.BlockDataManagerConfig()
      bdmConfig.armoryDbType = Cpp.ARMORY_DB_SUPER
      #bdmConfig.armoryDbType = Cpp.ARMORY_DB_BARE
      bdmConfig.pruneType = Cpp.DB_PRUNE_NONE
      bdmConfig.homeDirLocation = armoryHomeDir
      bdmConfig.blkFileLocation = blockdir
      bdmConfig.levelDBLocation = leveldbdir
      bdmConfig.setGenesisBlockHash(GENESIS_BLOCK_HASH)
      bdmConfig.setGenesisTxHash(GENESIS_TX_HASH)
      bdmConfig.setMagicBytes(MAGIC_BYTES)
         
      # 32-bit linux has an issue with max open files.  Rather than modifying
      # the system, we can tell LevelDB to take it easy with max files to open
      if OS_LINUX and not SystemSpecs.IsX64:
         LOGINFO('Lowering max-open-files parameter in LevelDB for 32-bit linux')
         bdmConfig.levelDBMaxOpenFiles = 75

      # Override the above if they explicitly specify it as CLI arg
      if CLI_OPTIONS.maxOpenFiles > 0:
         LOGINFO('Overriding max files via command-line arg')
         bdmConfig.levelDBMaxOpenFiles = CLI_OPTIONS.maxOpenFiles

      return bdmConfig

   #############################################################################
   @ActLikeASingletonBDM
   def predictLoadTime(self):
      return (self.progressPhase, self.progressComplete, self.secondsRemaining)

   #############################################################################
   @TimeThisFunction
   @ActLikeASingletonBDM
   def createAddressBook(self, cppWlt):
      return cppWlt.createAddressBook()

   #############################################################################
   @ActLikeASingletonBDM
   def getCurrBlock(self):
      return self.currentBlock
   
   #############################################################################
   @ActLikeASingletonBDM
   def setState(self, state):
      self.bdmState = state
      
   #############################################################################
   @ActLikeASingletonBDM
   def getState(self):
      return self.bdmState

   #############################################################################
   @ActLikeASingletonBDM
   def execCleanShutdown(self):
      self.bdv.reset()
      self.bdmThread.shutdownAndWait()
   
   @ActLikeASingletonBDM
   def runBDM(self, fn):
      return self.inject.runCommand(fn)
   
################################################################################
# Make TheBDM reference the asyncrhonous BlockDataManager wrapper if we are 
# running 
TheBDM = None
TheSDM = None
if CLI_OPTIONS.offline:
   LOGINFO('Armory loaded in offline-mode.  Will not attempt to load ')
   LOGINFO('blockchain without explicit command to do so.')
   TheBDM = BlockDataManager(isOffline=True)

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
   LOGINFO('Devs: check TheBDM.getState() before asking for data.')
   LOGINFO('Registering addresses during rescans will queue them for ')
   LOGINFO('inclusion after the current scan is completed.')
   TheBDM = BlockDataManager(isOffline=False)

   cppLogFile = os.path.join(ARMORY_HOME_DIR, 'armorycpplog.txt')
   cpplf = cppLogFile
   if OS_WINDOWS and isinstance(cppLogFile, unicode):
      cpplf = cppLogFile.encode('utf8')
   Cpp.BlockDataManager_LevelDB_StartCppLogging(cpplf, 4)
   Cpp.BlockDataManager_LevelDB_EnableCppLogStdOut()    

   #LOGINFO('LevelDB max-open-files is %d', TheBDM.getMaxOpenFiles())

   # Also load the might-be-needed SatoshiDaemonManager
   TheSDM = SatoshiDaemonManager()


# Put the import at the end to avoid circular reference problem
from armoryengine.PyBtcWallet import PyBtcWallet
from armoryengine.Transaction import PyTx

# kate: indent-width 3; replace-tabs on;
