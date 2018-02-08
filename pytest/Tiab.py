import sys
# This Code chunk has to appear before ArmoryUtils is imported
# If not, it will run the tests in Mainnet.
# TODO: Fix the code base so that nothing is started during imports.
sys.argv.append('--testnet')
# Uncomment when debugging
sys.argv.append('--debug')
sys.argv.append('--supernode')
# sys.argv.append('--nologging')

import os
import time
import tempfile
import shutil
import subprocess
import copy
import unittest
from zipfile import ZipFile
from armoryengine.BDM import TheBDM, BlockDataManager, newTheBDM,\
   BDM_BLOCKCHAIN_READY, STOPPED_ACTION

TOP_TIAB_BLOCK = 247


doneShuttingDownBDM = False
      
FIRST_WLT_FILE_NAME = "armory_GDHFnMQ2_.wallet"
FIRST_WLT_NAME = "GDHFnMQ2"

SECOND_WLT_FILE_NAME = "armory_vzgEfJrJ_.wallet"
SECOND_WLT_NAME = "vzgEfJrJ"

THIRD_WLT_FILE_NAME = "armory_DZMmtb2v_.wallet"
THIRD_WLT_NAME = "DZMmtb2v"


FIRST_WLT_BALANCE = 964.8997

TIAB_SATOSHI_PORT = 19000

# runs a Test In a Box (TIAB) bitcoind session. By copying a prebuilt
# testnet with a known state
# Charles's recommendation is that you keep the TIAB somewhere like ~/.armory/tiab.charles
# and export that path in your .bashrc as ARMORY_TIAB_PATH
class TiabSession:
   numInstances=0
   
   # create a Test In a Box, initializing it and filling it with data
   # the data comes from a path in the environment unless tiabdatadir is set
   # tiab_repository is used to name which flavor of box is used if
   # tiabdatadir is not used - It is intended to be used for when we
   # have multiple testnets in a box with different properties
   def __init__(self, tiabZipPath="tiab.zip"):
      self.processes = []
      self.tiabDirectory = tempfile.mkdtemp("armory_tiab")
      self.tiabZipPath = tiabZipPath
      
      self.running = False
      
      self.restart()
   
   def __del__(self):
      self.clean()
   
   # exit bitcoind and remove all data
   def clean(self):
      if not self.running:
         return
      TiabSession.numInstances -= 1
      for x in self.processes:
         x.kill()
      for x in self.processes:
         x.wait()
      self.processes = []
      shutil.rmtree(self.tiabDirectory)
      self.running=False
   
   # returns the port the first bitcoind is running on
   # In future versions of this class, multiple bitcoinds will get different ports,
   # so therefor, you should call this function to get the port to connect to
   def port(self, instanceNum):
      instance = instanceNum
      if instance==0:
         return TIAB_SATOSHI_PORT
      elif instance==1:
         return 19010
      else:
         raise RuntimeError("No such instance number")

   # clean() and then start bitcoind again

   def callBitcoinD(self, bitcoinDArgs):
      bitcoinDArgsCopy = copy.copy(bitcoinDArgs)
      bitcoinDArgsCopy.insert(0, "bitcoind")
      return self.processes.append(subprocess.Popen(bitcoinDArgsCopy))

   def restart(self):
      self.clean()
      if TiabSession.numInstances != 0:
         raise RuntimeError("Cannot have more than one Test-In-A-Box session simultaneously (yet)")
      
      TiabSession.numInstances += 1
      with ZipFile(self.tiabZipPath, "r") as z:
         z.extractall(self.tiabDirectory)
      try:
         self.callBitcoinD(["-datadir=" + os.path.join(self.tiabDirectory,'tiab','1'), "-debug"])
         self.callBitcoinD(["-datadir=" + os.path.join(self.tiabDirectory,'tiab','2'), "-debug"])
      except:
         self.clean()
         raise
      self.running = True
      
   # Use this to get reset the wallet files
   # previously run tests don't affect the state of the wallet file.
   def resetWalletFiles(self):
      with ZipFile(self.tiabZipPath, "r") as z:
         z.extractall(self.tiabDirectory,  [fileName for fileName in z.namelist() if fileName.endswith('.wallet')])

TIAB_ZIPFILE_NAME = 'tiab.zip'
NEED_TIAB_MSG = "This Test must be run with <TBD>. Copy to the test directory. Actual Block Height is "



class TiabTest(unittest.TestCase):      
   
   def __init__(self, methodName='runTest'):
      unittest.TestCase.__init__(self, methodName)
      self.maxDiff = None
      
   
   @classmethod
   def setUpClass(self):
      global doneShuttingDownBDM
      doneShuttingDownBDM = False
      
      # Handle both calling the this test from the context of the test directory
      # and calling this test from the context of the main directory. 
      # The latter happens if you run all of the tests in the directory
      if os.path.exists(TIAB_ZIPFILE_NAME):
         tiabZipPath = TIAB_ZIPFILE_NAME
      elif os.path.exists(os.path.join('pytest',TIAB_ZIPFILE_NAME)):
         tiabZipPath = (os.path.join('pytest',TIAB_ZIPFILE_NAME))
      else:
         self.fail(NEED_TIAB_MSG)
      self.tiab = TiabSession(tiabZipPath=tiabZipPath)
      
      newTheBDM()
      self.armoryHomeDir = os.path.join(self.tiab.tiabDirectory,'tiab','armory')
      TheBDM.setSatoshiDir(os.path.join(self.tiab.tiabDirectory,'tiab','1','testnet3'))
      TheBDM.setArmoryDBDir(os.path.join(self.tiab.tiabDirectory,'tiab','armory','databases'))
      TheBDM.goOnline(armoryDBDir=self.armoryHomeDir)
      
      i = 0
      while not TheBDM.getState()==BDM_BLOCKCHAIN_READY:
         time.sleep(2)
         i += 1
         if i >= 60:
            raise RuntimeError("Timeout waiting for TheBDM to get into BlockchainReady state.")

   @classmethod
   def tearDownClass(self):
      def tiabBDMShutdownCallback(action, arg):
         global doneShuttingDownBDM
         if action == STOPPED_ACTION:
            doneShuttingDownBDM = True
      
      TheBDM.registerCppNotification(tiabBDMShutdownCallback)
      TheBDM.beginCleanShutdown()
      
      i = 0
      while not doneShuttingDownBDM:
         time.sleep(0.5)
         i += 1
         if i >= 40:
            raise RuntimeError("Timeout waiting for TheBDM to shutdown.")
      
      self.tiab.clean()

   # Use this to get reset the wallet files
   # previously run tests don't affect the state of the wallet file.
   def resetWalletFiles(self):
      self.tiab.resetWalletFiles()

   def verifyBlockHeight(self):
      blockHeight = TheBDM.getTopBlockHeight()
      self.assertEqual(blockHeight, TOP_TIAB_BLOCK, NEED_TIAB_MSG + str(blockHeight))
