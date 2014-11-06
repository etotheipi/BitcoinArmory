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


BDM_OFFLINE = 'Offline'
BDM_UNINITIALIZED = 'Uninitialized'
BDM_BLOCKCHAIN_READY = 'BlockChainReady'
BDM_SCANNING = 'Scanning'
FINISH_LOAD_BLOCKCHAIN_ACTION = 'FinishLoadBlockchain'   
NEW_ZC_ACTION = 'newZC'
NEW_BLOCK_ACTION = 'newBlock'
REFRESH_ACTION = 'refresh'
STOPPED_ACTION = 'stopped'
WARNING_ACTION = 'warning'


def newTheBDM(isOffline=False):
   global TheBDM
   if TheBDM:
      TheBDM.beginCleanShutdown()
   TheBDM = BlockDataManager(isOffline=isOffline)

class PySide_CallBack(Cpp.BDM_CallBack):
   def __init__(self, bdm):
      Cpp.BDM_CallBack.__init__(self)
      self.bdm = bdm
      self.bdm.progressComplete=0
      self.bdm.secondsRemaining=0
      self.bdm.progressPhase=0
      
   def run(self, action, arg, block):
      try:
         act = ''
         arglist = []
         
         # AOTODO replace with constants
         
         if action == Cpp.BDMAction_Ready:
            act = FINISH_LOAD_BLOCKCHAIN_ACTION
            TheBDM.topBlockHeight = block
            TheBDM.setState(BDM_BLOCKCHAIN_READY)
         elif action == Cpp.BDMAction_ZC:
            act = NEW_ZC_ACTION
            castArg = Cpp.BtcUtils_cast_to_LedgerVector(arg)
            arglist = castArg
         elif action == Cpp.BDMAction_NewBlock:
            act = NEW_BLOCK_ACTION
            castArg = Cpp.BtcUtils_cast_to_int(arg)
            arglist.append(castArg)
            TheBDM.topBlockHeight = block
         elif action == Cpp.BDMAction_Refresh:
            act = REFRESH_ACTION
            castArg = Cpp.BtcUtils_cast_to_BinaryDataVector(arg)
            arglist = castArg
         elif action == Cpp.BDMAction_Exited:
            act = STOPPED_ACTION
         elif action == Cpp.BDMAction_ErrorMsg:
            act = WARNING_ACTION
            argstr = Cpp.BtcUtils_cast_to_string(arg)
            arglist.append(argstr)
            
         listenerList = TheBDM.getListenerList()
         for cppNotificationListener in listenerList:
            cppNotificationListener(act, arglist)
      except:
         LOGEXCEPT('Error in running callback')
         print sys.exc_info()
         raise

   def progress(self, phase, walletId, prog, seconds):
      try:
         walletIdString = str(walletId)
         if len(walletIdString) == 0:
            self.bdm.progressPhase = phase
            self.bdm.progressComplete = prog
            self.bdm.secondsRemaining = seconds
         else:
            progInfo = [walletIdString, prog]
            for cppNotificationListener in TheBDM.getListenerList():
               cppNotificationListener('progress', progInfo)
               
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
   return (time0, TheBDM.getTopBlockHeight())

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

   #############################################################################
   def __init__(self, isOffline=False):
      super(BlockDataManager, self).__init__()

      #register callbacks
      self.callback = PySide_CallBack(self).__disown__()
      self.inject = BDM_Inject().__disown__()
      
      self.ldbdir = ""

      #dbType
      #self.dbType = Cpp.ARMORY_DB_BARE
      self.dbType = Cpp.ARMORY_DB_SUPER      
      
      self.bdmThread = Cpp.BlockDataManagerThread(self.bdmConfig(forInit=True));

      # Flags
      self.aboutToRescan = False
      self.errorOut      = 0
      
      self.currentActivity = 'None'
      self.walletsToRegister = []
      
      if isOffline == True: self.bdmState = BDM_OFFLINE
      else: self.bdmState = BDM_UNINITIALIZED

      self.btcdir = BTC_HOME_DIR
      self.ldbdir = LEVELDB_DIR
      self.lastPctLoad = 0
      
      self.topBlockHeight = 0
      self.cppNotificationListenerList = []
   
   
   #############################################################################
   @ActLikeASingletonBDM
   def getListenerList(self):
      return self.cppNotificationListenerList
         
   
   #############################################################################
   @ActLikeASingletonBDM
   def cleanUpBDMThread(self):
      self.bdmThread = None
         
   #############################################################################
   @ActLikeASingletonBDM
   def BDMshutdownCallback(self, action, args):
      if action == 'stopped':
         self.cppNotificationListenerList.remove(self.BDMshutdownCallback)
         self.cleanUpBDMThread()

   #############################################################################
   @ActLikeASingletonBDM
   def bdv(self):
      return self.bdmThread.bdv()

   #############################################################################
   @ActLikeASingletonBDM
   def getTxByHash(self, txHash):
      return self.bdv().getTxByHash(txHash)
   
   #############################################################################
   @ActLikeASingletonBDM
   def getSentValue(self, txIn):
      return self.bdv().getSentValue(txIn)

   #############################################################################
   @ActLikeASingletonBDM
   def getTopBlockHeight(self):
      return self.topBlockHeight
   
   #############################################################################
   @ActLikeASingletonBDM
   def getTopBlockDifficulty(self):
      return self.bdv().getTopBlockHeader().getDifficulty()
   
   #############################################################################
   @ActLikeASingletonBDM
   def registerCppNotification(self, cppNotificationListener):
      self.cppNotificationListenerList.append(cppNotificationListener)
    
   #############################################################################
   @ActLikeASingletonBDM
   def unregisterCppNotification(self, cppNotificationListener):
      if cppNotificationListener in self.cppNotificationListenerList:
         self.cppNotificationListenerList.remove(cppNotificationListener)
   
   #############################################################################
   @ActLikeASingletonBDM
   def goOnline(self, satoshiDir=None, levelDBDir=None, armoryHomeDir=None):

      self.bdmThread.setConfig(self.bdmConfig())
      
      self.bdmState = BDM_SCANNING
      self.bdmThread.start(self.bdmMode(), self.callback, self.inject)

   #############################################################################
   @ActLikeASingletonBDM
   def registerWallet(self, prefixedKeys, uniqueIDB58, isNew=False):
      #this returns a pointer to the BtcWallet C++ object. This object is
      #instantiated at registration and is unique for the BDV object, so we
      #should only ever set the cppWallet member here 
      return self.bdv().registerWallet(prefixedKeys, uniqueIDB58, isNew)

   #############################################################################
   @ActLikeASingletonBDM
   def unregisterWallet(self, uniqueIDB58):
      self.bdv().unregisterWallet(uniqueIDB58)

   #############################################################################
   @ActLikeASingletonBDM
   def registerLockbox(self, uniqueIDB58, addressList, isNew=False):
      #this returns a pointer to the BtcWallet C++ object. This object is
      #instantiated at registration and is unique for the BDV object, so we
      #should only ever set the cppWallet member here 
      return self.bdv().registerLockbox(addressList, uniqueIDB58, isNew)

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
   
   #############################################################################   
   @ActLikeASingletonBDM
   def bdmMode(self):
      if CLI_OPTIONS.rebuild:
         mode = 2
      elif CLI_OPTIONS.rescan:
         mode = 1
      else:
         mode = 0
         
      if CLI_OPTIONS.clearMempool:
         mode += 4
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
      bdmConfig.armoryDbType = self.dbType
      bdmConfig.pruneType = Cpp.DB_PRUNE_NONE
      bdmConfig.homeDirLocation = armoryHomeDir
      bdmConfig.blkFileLocation = blockdir
      bdmConfig.levelDBLocation = leveldbdir
      bdmConfig.setGenesisBlockHash(GENESIS_BLOCK_HASH)
      bdmConfig.setGenesisTxHash(GENESIS_TX_HASH)
      bdmConfig.setMagicBytes(MAGIC_BYTES)

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
   def setState(self, state):
      self.bdmState = state
      
   #############################################################################
   @ActLikeASingletonBDM
   def getState(self):
      return self.bdmState

   #############################################################################
   @ActLikeASingletonBDM
   def beginCleanShutdown(self):
      if self.bdmThread: 
         self.bdmState = BDM_UNINITIALIZED
         self.registerCppNotification(self.BDMshutdownCallback)      
         self.bdv().reset()
         if self.bdmThread.requestShutdown() == False:
            self.cleanUpBDMThread()

   #############################################################################
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
   Cpp.StartCppLogging(cpplf, 4)
   Cpp.EnableCppLogStdOut()    

   #LOGINFO('LevelDB max-open-files is %d', TheBDM.getMaxOpenFiles())

   # Also load the might-be-needed SatoshiDaemonManager
   TheSDM = SatoshiDaemonManager()


# Put the import at the end to avoid circular reference problem
from armoryengine.MultiSigUtils import MultiSigLockbox
from armoryengine.Transaction import PyTx

# kate: indent-width 3; replace-tabs on;
