
import os
import tempfile
import shutil
import subprocess

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
   def __init__(self, tiab_repository="", tiabdatadir=None):
      self.tiabdatadir = tiabdatadir
      self.processes = []
      if not self.tiabdatadir:
         self.tiabdatadir = os.environ['ARMORY_TIAB_PATH'+tiab_repository]
      # an obvious race condition lives here
      self.directory = tempfile.mkdtemp("armory_tiab")
      
      self.running = False
      
      self.restart()
   
   def __del__(self):
      self.clean()
   
   # exit bitcoind and remove all data
   def clean(self):
      if not self.running:
         return
      TiabSession.numInstances -= 1
      try:
         for x in self.processes:
            x.kill()
         for x in self.processes:
            x.wait()
         self.processes = []
         shutil.rmtree(self.directory)
      except:
         pass
      self.running=False
   
   # returns the port the first bitcoind is running on
   # In future versions of this class, multiple bitcoinds will get different ports,
   # so therefor, you should call this function to get the port to connect to
   def port(self, instanceNum):
      instance = instanceNum
      if instance==0:
         return 19000
      elif instance==1:
         return 19010
      else:
         raise RuntimeError("No such instance number")

   # clean() and then start bitcoind again
   def restart(self):
      self.clean()
      if TiabSession.numInstances != 0:
         raise RuntimeError("Cannot have more than one Test-In-A-Box session simultaneously (yet)")
      
      TiabSession.numInstances += 1
      os.rmdir(self.directory)
      shutil.copytree(self.tiabdatadir, self.directory)
      try:
         print "executing in datadir " + self.directory
         self.processes.append( subprocess.Popen(["bitcoind", "-datadir=" + self.directory + "/1", "-debugnet", "-debug" ]) )
         self.processes.append( subprocess.Popen(["bitcoind", "-datadir=" + self.directory + "/2", "-debugnet", "-debug" ]) )
      except:
         self.clean()
         raise
      self.running = True
      
# kate: indent-width 3; replace-tabs on;
