#################################################################
#
# Tiab.py - Testnet in a Box (tiab)
#
# Tiab works by utilizing a very short blockchain that's been
# manually mined using testnet.
#
# This is all in tiab.zip with two directories for bitcoin
# and one for armory.
#
#################################################################

import sys
sys.path.append('..')

import os
import subprocess
import time
import unittest

from twisted.python import filepath

from armoryengine.ArmoryOptions import *
from armoryengine.BDM import BlockDataManager, reloadBDM, getBDM, initializeBDM

from TiabSession import *


TOP_TIAB_BLOCK = 250

# this is a valid block 251
# it has one transaction that goes from the FIRST_WLT_ADDR2
NEXT_BLOCK = "03000000fd1bc6371eae1a73fcd78f8ef3f9b273b4224d570711e68351cdf80200000000f6761ed9e05ff18af3b14c5049f223814c2d9ab00a6fe30871268daae9b80a28302a5755ffff001dadba32c00201000000010000000000000000000000000000000000000000000000000000000000000000ffffffff0c02fb000105062f503253482fffffffff0100f2052a010000002321035af4eb9e7d0d7ab0a75d7e497798c107cb36a30a089a1d3b8ac605dac78080d4ac0000000001000000017857ac1e96312b3a189b21a5276e0e7c6ac713b457439be00456f33bdd3efbd1010000006c493046022100b1c5b3e3e0f00fe2fa675675260572b36a0a0a9b1f450468c9bd6b73f1adc212022100c29c7ccf2666ca27aa3eda322d2282a0600d0f103a2d7894ab49dc99b7aef387012103d2b0ebef17c3edf886a761b08241918631bc31f44a733e2ae3a52884df0a71a7ffffffff02002375ee140000001976a914c148d5517e76e71b9c9f9b5e3c40d183606e4b1d88ac00e1f505000000001976a914e3ce52a2077f0543f361f0a2d730be3a6820a09f88ac00000000"

doneShuttingDownBDM = False

# two wallets in the same file
FIRST_WLT_FILE_NAME = "armory_wallet2.0_1BsmPcJN.wlt"
FIRST_WLT_NAME = "2quaZFBk4"
FIRST_WLT_XPUB = "tpubDD6WexxvZ9pVbrust6XhywpDFWDA2VymA9wiVHytWwQGuw84FfkUsKfRhX2isBHbbV6PaPjC5Wwyd3MfpaDBZ9NUjRawn3heH86pXPmuwmR"

FIRST_WLT_ADDR1 = 'mrFNfhs1qhKXGq1FZ8qNm241fQPiNWEDMw'
FIRST_WLT_ADDR1_BAL = 0.0

FIRST_WLT_ADDR2 = 'mz4MVnVEg7YTXTyypvznkmuHrj9d6dwXx2'
FIRST_WLT_ADDR2_BAL  = 908.0


FOURTH_WLT_NAME = "Q9Mkhp4V"

SECOND_WLT_FILE_NAME = "armory_wallet2.0_4R56FxEm.wlt"
SECOND_WLT_NAME = "2dDG7chzb"

THIRD_WLT_FILE_NAME = "armory_wallet2.0_egC6gByp.wlt"
THIRD_WLT_NAME = "uAPj7PA"

FIRST_WLT_BALANCE = 927.9999

FIRST_LOCKBOX_NAME = "82XXBBVi"
FIRST_LOCKBOX_ADDRESS = "2MuKNwPm3cxwB4L473ZwowttqpfD5stqdSg"
FIRST_LOCKBOX_BALANCE = 2.5
SECOND_LOCKBOX_NAME = "49j6aCTF"
SECOND_LOCKBOX_ADDRESS = "2NDRc1aUCJY7Gp8dzT7P5aps5tnW6gm7jfM"
SECOND_LOCKBOX_BALANCE = 6.1


NEED_TIAB_MSG = "This Test must be run with <TBD>. Copy to the test directory. Actual Block Height is %s"

class TiabTest(unittest.TestCase):      
   
   def __init__(self, methodName='runTest'):
      unittest.TestCase.__init__(self, methodName)
      self.maxDiff = None
      
   
   @classmethod
   def setUpClass(self):
      initializeOptions()
      # make sure there's a bitcoind to run
      if not isWindows():
         try:
            subprocess.check_output(['which', 'bitcoind'])
         except subprocess.CalledProcessError:
            raise RuntimeError("bitcoind is not in your PATH, "
                               "cannot run unit-tests")

      # change a few options first
      useTestnet()
      setSupernodeFlag(True)
      setBitcoinHomeDir(theTiabSession.getBitcoinDir())
      setArmoryHomeDir(theTiabSession.getArmoryDir())
      setBitcoinPort(TIAB_SATOSHI_PORT)
      initializeBDM()

      global doneShuttingDownBDM
      doneShuttingDownBDM = False
      self.tiab = theTiabSession
      self.tiab.restart()
      reloadBDM()
      self.armoryHomeDir = getArmoryHomeDir()
      getBDM().setSatoshiDir(getBitcoinHomeDir())
      getBDM().setArmoryDBDir(os.path.join(self.armoryHomeDir,'databases'))
      getBDM().goOnline()
      
      i = 0
      while getBDM().getState() != BDM_BLOCKCHAIN_READY:
         time.sleep(2)
         i += 1
         if i >= 60:
            raise RuntimeError("Timeout waiting for getBDM() to get into BlockchainReady state.")

   @classmethod
   def tearDownClass(self):
      def tiabBDMShutdownCallback(action, arg):
         global doneShuttingDownBDM
         if action == STOPPED_ACTION:
            doneShuttingDownBDM = True
      
      getBDM().registerCppNotification(tiabBDMShutdownCallback)
      getBDM().beginCleanShutdown()
      
      i = 0
      while not doneShuttingDownBDM:
         time.sleep(0.5)
         i += 1
         if i >= 40:
            raise RuntimeError("Timeout waiting for getBDM() to shutdown.")
      
      self.tiab.clean()

   def submitNextBlock(self):
      datadir = os.path.join(self.tiab.tiabDirectory, 'tiab', '1')
      args = ["bitcoin-cli", "-datadir=%s" % datadir, "submitblock", NEXT_BLOCK]
      subprocess.call(args)

   # Use this to get reset the wallet files
   # previously run tests don't affect the state of the wallet file.
   def resetWalletFiles(self):
      self.tiab.resetWalletFiles()

   def verifyBlockHeight(self):
      blockHeight = getBDM().getTopBlockHeight()
      self.assertEqual(blockHeight, TOP_TIAB_BLOCK, NEED_TIAB_MSG % blockHeight)
