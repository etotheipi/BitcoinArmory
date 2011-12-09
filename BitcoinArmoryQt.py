#! /usr/bin/python
################################################################################
#
# Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
#
# Project:    BitcoinArmory          (https://github.com/etotheipi/BitcoinArmory)
# Author:     Alan Reiner
# Orig Date:  20 November, 2011
# Descr:      This file serves as an engine for python-based Bitcoin software.
#             I forked this from my own project -- PyBtcEngine -- because I
#             I needed to start including/rewriting code to use CppBlockUtils
#             but did not want to break the pure-python-ness of PyBtcEngine.
#             If you are interested in in a pure-python set of bitcoin utils
#             please go checkout the PyBtcEngine github project.
#
#
################################################################################

import hashlib
import random
import time
import os
import sys
import shutil
import math
import threading
from datetime import datetime

# PyQt4 Imports
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# 8000 lines of python to help us out...
from btcarmoryengine import *
from armorymodels import *

# All the twisted/networking functionality
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet.defer import Deferred

# This is an amazing trick for create enum-like dictionaries. 
# Either automatically numbers (*args), or name-val pairs (**kwargs)
#http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

TXTBL = enum("Status", "Date", "Direction", "Address", "Amount")


SETTINGS_PATH = os.path.join(ARMORY_HOME_DIR, 'ArmorySettings.txt')
wallets = []


UserMode = enum('Standard', 'Advanced')

class ArmoryMainWindow(QMainWindow):
   """ The primary Armory window """

   #############################################################################
   def __init__(self, parent=None, settingsPath=None):
      super(ArmoryMainWindow, self).__init__(parent)

      self.extraHeartbeatFunctions = []
      self.settingsPath = settingsPath


      self.loadWalletsAndSettings()
      self.setupNetworking()

      self.lblAvailWlt = QLabel('Available Wallets:')
      self.lblAvailWlt.setAlignment(Qt.AlignBottom)

      self.lblLogoIcon = QLabel()
      self.lblLogoIcon.setPixmap(QPixmap('icons/armory_logo_64x64.png'))
      self.lblLogoIcon.setAlignment(Qt.AlignRight)

      self.setWindowTitle('Armory - Bitcoin Wallet Management')
      self.setWindowIcon(QIcon('icons/armory_logo_32x32.png'))

      self.walletModel = WalletDispModel(self)
      self.walletView  = QTableView()
      self.walletView.setModel(self.walletModel)
      self.walletView.setSelectionBehavior(QTableView.SelectRows)
      self.walletView.setSelectionMode(QTableView.SingleSelection)
      #self.headView.setMinimumSize(800,200)
      self.walletView.horizontalHeader().setStretchLastSection(True)
      self.walletView.verticalHeader().setDefaultSectionSize(20)
      self.walletView.horizontalHeader().resizeSection(1, 150)

      if self.usermode == UserMode.Standard:
         self.walletView.hideColumn(0)
         self.walletView.horizontalHeader().resizeSection(1, 200)

      
      layout = QGridLayout()
      layout.addWidget(QLabel("Available Wallets:"), 0, 0, 1, 1)
      layout.addWidget(self.walletView,              2, 0, 1, 2)
      layout.addWidget(self.lblLogoIcon,             0, 1, 1, 1)

      # Attach the layout to the frame that will become the central widget
      mainFrame = QFrame()
      mainFrame.setLayout(layout)
      self.setCentralWidget(mainFrame)
      self.setMinimumSize(500,300)

      self.statusBar().showMessage('Blockchain loading, please wait...')

      from twisted.internet import reactor
      reactor.callLater(2.0,  self.loadBlockchain)
      #reactor.callLater(10, form.Heartbeat)

   #############################################################################
   def setupNetworking(self):

      from twisted.internet import reactor
      def restartConnection(protoObj, failReason):
         print '! Trying to restart connection !'
         reactor.connectTCP(protoObj.peer[0], protoObj.peer[1], self.NetworkingFactory)

      self.NetworkingFactory = BitcoinArmoryClientFactory( \
                                       func_loseConnect=restartConnection)
      #reactor.connectTCP('127.0.0.1', BITCOIN_PORT, self.NetworkingFactory)


   #############################################################################
   def loadWalletsAndSettings(self):
      self.settings = SettingsFile(self.settingsPath)

      # Determine if we need to do new-user operations, increment load-count
      self.firstLoad = False
      if self.settings.get('First_Load'): 
         self.firstLoad = True
         self.settings.set('First_Load', False)
         self.settings.set('Load_Count', 1)
      else:
         self.settings.set('Load_Count', (self.settings.get('Load_Count')+1) % 10)

      # Set the usermode, default to standard
      if self.settings.get('User_Mode') == 'Advanced':
         self.usermode = UserMode.Advanced
      else:
         self.usermode = UserMode.Standard

      # Load wallets found in the .bitcoinarmory directory
      wltPaths = self.settings.get('Other_Wallets', expectList=True)
      self.walletMap = {}
      self.walletIDSet = set()
      self.walletIDList = []  # Also need an easily, deterministically-iterable list
      self.walletBalances = []  # Also need an easily, deterministically-iterable list
      self.walletIndices = {}  


      print 'Loading wallets...'
      for root,subs,files in os.walk(ARMORY_HOME_DIR):
         for f in files:
            if f.startswith('armory_') and f.endswith('.wallet') and \
               not f.endswith('backup.wallet') and not ('unsuccessful' in f):
                  wltPaths.append(os.path.join(root, f))


      wltExclude = self.settings.get('Excluded_Wallets', expectList=True)
      for index,fpath in enumerate(wltPaths):
         try:
            wltLoad = PyBtcWallet().readWalletFile(fpath)
            wltID = wltLoad.wltUniqueIDB58
            if wltID in wltExclude:
               continue

            if wltID in self.walletIDSet:
               print '***WARNING: Duplicate wallet detected,', wltID
               print ' '*10, 'Wallet 1 (loaded): ', self.walletMap[wltID].walletPath
               print ' '*10, 'Wallet 2 (skipped):', fpath
            else:
               self.walletMap[wltID] = wltLoad
               self.walletIDSet.add(wltID)
               self.walletIDList.append(wltID)
               self.walletBalances.append(-1)
               self.walletIndices[wltID] = index
         except:
            print '***WARNING: Wallet could not be loaded:', fpath
            print '            skipping... '
            raise
                     

      print 'Number of wallets read in:', len(self.walletMap)
      for wltID, wlt in self.walletMap.iteritems():
         print '   Wallet (%s):'.ljust(20) % wlt.wltUniqueIDB58,
         print '"'+wlt.labelName+'"   ',
         print '(Encrypted)' if wlt.useEncryption else '(Not Encrypted)'




   #############################################################################
   def getWalletForAddr160(self, addr160):
      for wltID, wlt in self.walletMap.iteritems():
         if wlt.hasAddr(addr160):
            return wltID
      return None


   #############################################################################
   def loadBlockchain(self):
      print 'Loading blockchain'
      BDM_LoadBlockchainFile()
      if TheBDM.isInitialized():
         self.statusBar().showMessage('Syncing wallets with blockchain...')
         print 'Syncing wallets with blockchain...'
         for wltID, wlt in self.walletMap.iteritems():
            print 'Syncing', wltID
            self.walletMap[wltID].setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
            self.walletMap[wltID].syncWithBlockchain()
            index = self.walletIndices[wltID]
            self.walletBalances[index] = self.walletMap[wltID].getBalance()
         self.statusBar().showMessage('Blockchain loaded, wallets sync\'d!', 10000)
      else:
         self.statusBar().showMessage('! Blockchain loading failed !', 10000)

      # This will force the table to refresh with new data
      self.walletView.selectRow(-1)
         

   def Heartbeat(self, nextBeatSec=3):
      """
      This method is invoked when the app is initialized, and will
      run every 3 seconds, or whatever is specified in the nextBeatSec
      argument.
      """
      # Check for new blocks in the blk0001.dat file
      if TheBDM.isInitialized():
         newBlks = TheBDM.readBlkFileUpdate()
         if newBlks>0:
            pass # do something eventually
      
      # Check for new tx in the zeroConf pool
      self.txNotInBlkchainYet = []
      if TheBDM.isInitialized():
         for hsh,tx in self.NetworkingFactory.zeroConfTx.iteritems():
            for txout in tx.outputs:
               addr = TxOutScriptExtractAddr160(txout.binScript)
               if isinstance(addr, list): 
                  continue # ignore multisig
                  
               for wltID, wlt in self.walletMap.iteritems():
                  if wlt.hasAddr(addr):
                     self.txNotInBlkchainYet.append(hsh)

      for tx in self.txNotInBlkchainYet:
         print '   ',binary_to_hex(tx)


      for wltID, wlt in self.walletMap.iteritems():
         # Update wallet balances
         self.walletBalances = self.walletMap[wltID].getBalance()

      for func in self.extraHeartbeatFunctions:
         func()

      reactor.callLater(nextBeatSec, self.Heartbeat)
      

"""
We'll mess with threading, later
class BlockchainLoader(threading.Thread):
   def __init__(self, finishedCallback):
      self.finishedCallback = finishedCallback

   def run(self):
      BDM_LoadBlockchainFile()
      self.finishedCallback()
"""
      



if __name__ == '__main__':
 
   import optparse
   parser = optparse.OptionParser(usage="%prog [options]\n")
   parser.add_option("--host", dest="host", default="127.0.0.1",
                     help="IP/hostname to connect to (default: %default)")
   parser.add_option("--port", dest="port", default="8333", type="int",
                     help="port to connect to (default: %default)")
   parser.add_option("--settings", dest="settingsPath", default=SETTINGS_PATH, type="str",
                     help="load Armory with a specific settings file")
   parser.add_option("--verbose", dest="verbose", action="store_true", default=False,
                     help="Print all messages sent/received")
   #parser.add_option("--testnet", dest="testnet", action="store_true", default=False,
                     #help="Speak testnet protocol")

   (options, args) = parser.parse_args()



   app = QApplication(sys.argv)
   import qt4reactor
   qt4reactor.install()

   form = ArmoryMainWindow(settingsPath=options.settingsPath)
   form.show()

   from twisted.internet import reactor
   reactor.run()



