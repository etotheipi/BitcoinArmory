import copy
import os
import shutil
import subprocess
import tempfile
import zipfile


TIAB_SATOSHI_PORT = 19000

# runs a Test In a Box (TIAB) bitcoind session. By copying a prebuilt
# testnet with a known state
# Charles's recommendation is that you keep the TIAB somewhere like ~/.armory/tiab.charles
# and export that path in your .bashrc as ARMORY_TIAB_PATH
class TiabSession(object):
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

   def callBitcoinD(self, bitcoinDArgs):
      bitcoinDArgsCopy = copy.copy(bitcoinDArgs)
      bitcoinDArgsCopy.insert(0, "bitcoind")
      return self.processes.append(subprocess.Popen(bitcoinDArgsCopy))

   def restart(self):
      self.clean()
      if TiabSession.numInstances != 0:
         raise RuntimeError("Cannot have more than one Test-In-A-Box session "
                            "simultaneously (yet)")
      
      TiabSession.numInstances += 1
      with zipfile.ZipFile(self.tiabZipPath, "r") as z:
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
      with zipfile.ZipFile(self.tiabZipPath, "r") as z:
         z.extractall(self.tiabDirectory,  [fileName for fileName in z.namelist() if fileName.endswith('.wlt')])

   def getBitcoinDir(self):
      return os.path.join(self.tiabDirectory,'tiab','1')

   def getArmoryDir(self):
      return os.path.join(self.tiabDirectory,'tiab','armory')


theTiabSession = None
TIAB_ZIPFILE_NAME = 'tiab.zip'

def StartTiabSession():
    # Tiab runs on testnet and supernode
      
    # Handle both calling the this test from the context of the test directory
    # and calling this test from the context of the main directory. 
    # The latter happens if you run all of the tests in the directory
    if os.path.exists(TIAB_ZIPFILE_NAME):
        tiabZipPath = TIAB_ZIPFILE_NAME
    elif os.path.exists(os.path.join('tiabtest',TIAB_ZIPFILE_NAME)):
        tiabZipPath = (os.path.join('tiabtest',TIAB_ZIPFILE_NAME))
    else:
        raise RuntimeError(NEED_TIAB_MSG)
    global theTiabSession
    theTiabSession = TiabSession(tiabZipPath=tiabZipPath)

StartTiabSession()
