################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
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
SCAN_ACTION = 'StartedWalletScan'
NODESTATUS_UPDATE = 'NodeStatusUpdate'
BDM_SCAN_PROGRESS = 'BDM_Progress'

def newTheBDM(isOffline=False):
   global TheBDM
   if TheBDM:
      TheBDM.beginCleanShutdown()
   TheBDM = BlockDataManager(isOffline=isOffline)

class PySide_CallBack(Cpp.PythonCallback):
   def __init__(self, bdm):
      Cpp.PythonCallback.__init__(self, bdm.bdv())
      self.bdm = bdm
      
   def run(self, action, arg, block):
      try:
         act = ''
         arglist = []
         
         # AOTODO replace with constants
         
         if action == Cpp.BDMAction_Ready:
            print 'BDM is ready!'
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
         elif action == Cpp.BDMAction_StartedWalletScan:
            act = SCAN_ACTION
            argstr = Cpp.BtcUtils_cast_to_string_vec(arg)
            arglist.append(argstr)
         elif action == Cpp.BDMAction_NodeStatus:
            act = NODESTATUS_UPDATE
            argNodeStatus = Cpp.NodeStatusStruct_cast_to_NodeStatusStruct(arg)
            arglist.append(argNodeStatus)
            
         listenerList = TheBDM.getListenerList()
         for cppNotificationListener in listenerList:
            cppNotificationListener(act, arglist)
      except:
         LOGEXCEPT('Error in running callback')
         print sys.exc_info()
         raise

   def progress(self, phase, walletVec, prog, seconds, progressNumeric):
      try:
         if len(walletVec) == 0:
            self.bdm.progressPhase = phase
            self.bdm.progressComplete = prog
            self.bdm.secondsRemaining = seconds
            self.bdm.progressNumeric = progressNumeric
            
            self.bdm.bdmState = BDM_SCANNING
            
            for cppNotificationListener in TheBDM.getListenerList():
               cppNotificationListener(BDM_SCAN_PROGRESS, [None, None])            
         else:
            progInfo = [walletVec, prog]
            for cppNotificationListener in TheBDM.getListenerList():
               cppNotificationListener('progress', progInfo)
               
      except:
         LOGEXCEPT('Error in running progress callback')
         print sys.exc_info()
      
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
      self.armoryDBDir = ""

      # Flags
      self.aboutToRescan = False
      self.errorOut      = 0
      
      self.currentActivity = 'None'
      self.walletsToRegister = []
      
      if isOffline == True: self.bdmState = BDM_OFFLINE
      else: self.bdmState = BDM_UNINITIALIZED

      self.btcdir = BTC_HOME_DIR
      self.armoryDBDir = ARMORY_DB_DIR
      self.datadir = ARMORY_HOME_DIR
      self.lastPctLoad = 0
      
      self.topBlockHeight = 0
      self.cppNotificationListenerList = []

      self.progressComplete=0
      self.secondsRemaining=0
      self.progressPhase=0
      self.progressNumeric=0
            
      self.remoteDB = False
      self.instantiateBDV()
      
      self.exception = ""
      
      self.cookie = None
   
   #############################################################################  
   def instantiateBDV(self):
      if self.bdmState == BDM_OFFLINE:
         return
      
      socketType = Cpp.SocketFcgi
      if ARMORYDB_IP != ARMORYDB_DEFAULT_IP or ARMORYDB_PORT != ARMORYDB_DEFAULT_PORT:
         socketType = Cpp.SocketHttp 
         self.remoteDB = True

      self.bdv_ = Cpp.BlockDataViewer_getNewBDV(ARMORYDB_IP, ARMORYDB_PORT, socketType)   

   #############################################################################
   def registerBDV(self):   
      if self.bdmState == BDM_OFFLINE:
         return   
      
      try:
         self.bdv_.registerWithDB(MAGIC_BYTES)
      except Cpp.DbErrorMsg as e:
         self.exception = e.what()
         LOGERROR('DB error: ' + e.what())
         raise e
      
   #############################################################################
   @ActLikeASingletonBDM
   def hasRemoteDB(self):
      return self.remoteDB
            
   #############################################################################
   @ActLikeASingletonBDM
   def getListenerList(self):
      return self.cppNotificationListenerList

   #############################################################################
   @ActLikeASingletonBDM
   def bdv(self):
      return self.bdv_

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
   def goOnline(self, satoshiDir=None, armoryDBDir=None, armoryHomeDir=None):
      self.bdv().goOnline()
      self.callback = PySide_CallBack(self).__disown__()
      self.callback.startLoop()
      
   #############################################################################
   @ActLikeASingletonBDM
   def registerWallet(self, prefixedKeys, uniqueIDB58, isNew=False):
      #this returns a pointer to the BtcWallet C++ object. This object is
      #instantiated at registration and is unique for the BDV object, so we
      #should only ever set the cppWallet member here 
      return self.bdv().registerWallet(uniqueIDB58, prefixedKeys, isNew)

   #############################################################################
   @ActLikeASingletonBDM
   def registerLockbox(self, uniqueIDB58, addressList, isNew=False):
      #this returns a pointer to the BtcWallet C++ object. This object is
      #instantiated at registration and is unique for the BDV object, so we
      #should only ever set the cppWallet member here 
      return self.bdv().registerLockbox(uniqueIDB58, addressList, isNew)

   #############################################################################
   @ActLikeASingletonBDM
   def setSatoshiDir(self, newBtcDir):
      if not os.path.exists(newBtcDir):
         LOGERROR('setSatoshiDir: directory does not exist: %s', newBtcDir)
         return

      self.btcdir = newBtcDir

   #############################################################################
   @ActLikeASingletonBDM
   def setArmoryDBDir(self, armoryDBDir):
      if not os.path.exists(armoryDBDir):
         os.makedirs(armoryDBDir)

      self.armoryDBDir = armoryDBDir
   
   #############################################################################   
   @ActLikeASingletonBDM
   def bdmMode(self):
      if CLI_OPTIONS.rebuild:
         mode = 2
      elif CLI_OPTIONS.rescan:
         mode = 1
      elif CLI_OPTIONS.rescanBalance:
         mode = 3
      else:
         mode = 0
         
      if CLI_OPTIONS.clearMempool:
         mode += 4
      return mode
      
   #############################################################################
   @ActLikeASingletonBDM
   def predictLoadTime(self):
      return (self.progressPhase, self.progressComplete, self.secondsRemaining, self.progressNumeric)

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
   def shutdown(self):
      if self.bdmState == BDM_OFFLINE:
         return
      
      try:         
         self.bdv_.unregisterFromDB()
         self.callback.shutdown()
         
         cookie = self.getCookie()        
         self.bdv_.shutdown(cookie)
      except:
         pass
      
   #############################################################################
   def getCookie(self):
      if self.cookie == None:
         
         #get cookie from file
         cookiePath = os.path.join(self.datadir, ".cookie_")
         cookieFile = open(cookiePath, "r")
         self.cookie = cookieFile.read()
      return self.cookie

   #############################################################################
   @ActLikeASingletonBDM
   def runBDM(self, fn):
      return self.inject.runCommand(fn)
   
   #############################################################################
   @ActLikeASingletonBDM
   def RegisterEventForSignal(self, func, signal):
      def bdmCallback(bdmSignal, args):
         if bdmSignal == signal:
            func(args)
      self.registerCppNotification(bdmCallback)
      
   
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
