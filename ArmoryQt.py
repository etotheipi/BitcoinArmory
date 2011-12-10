################################################################################
#
# Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
#
# Project:    Armory                (https://github.com/etotheipi/BitcoinArmory)
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
from armoryengine import *
from armorymodels import *

# All the twisted/networking functionality
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet.defer import Deferred



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
      self.loadBlockchain()

      self.lblAvailWlt = QLabel('Available Wallets:')
      self.lblAvailWlt.setAlignment(Qt.AlignBottom)

      self.lblLogoIcon = QLabel()
      self.lblLogoIcon.setPixmap(QPixmap('icons/armory_logo_64x64.png'))
      self.lblLogoIcon.setAlignment(Qt.AlignRight)

      self.setWindowTitle('Armory - Bitcoin Wallet Management')
      self.setWindowIcon(QIcon('icons/armory_logo_32x32.png'))

      # Table for all the wallets
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

      # Table to display ledger/activity
      self.ledgerModel = ActivityDispModel(self)
      self.ledgerView  = QTableView()
      self.ledgerView.setModel(self.ledgerModel)
      self.ledgerView.setSelectionBehavior(QTableView.SelectRows)
      self.ledgerView.setSelectionMode(QTableView.SingleSelection)
      self.ledgerView.horizontalHeader().setStretchLastSection(True)
      self.ledgerView.verticalHeader().setDefaultSectionSize(25)
      self.ledgerView.horizontalHeader().resizeSection(1, 150)

      
      layout = QGridLayout()
      layout.addWidget(self.lblLogoIcon,             0, 2, 1, 1)
      layout.addWidget(QLabel("Available Wallets:"), 1, 0, 1, 1)
      layout.addWidget(self.walletView,              2, 0, 3, 2)
      layout.addWidget(QLabel("Transactions:"),      5, 0, 1, 1)
      layout.addWidget(self.ledgerView,              6, 0, 3, 3)

      # Attach the layout to the frame that will become the central widget
      mainFrame = QFrame()
      mainFrame.setLayout(layout)
      self.setCentralWidget(mainFrame)
      self.setMinimumSize(700,700)

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

      self.NetworkingFactory = ArmoryClientFactory( \
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

      # Load wallets found in the .armory directory
      wltPaths = self.settings.get('Other_Wallets', expectList=True)
      self.walletMap = {}
      self.walletIndices = {}  
      self.walletIDSet = set()

      # I need some linear lists for accessing by index
      self.walletIDList = []   
      self.walletBalances = []  
      self.walletSubLedgers = []  
      self.walletLedgers = []
      self.combinedLedger = []
      self.ledgerSize = 0

      self.latestBlockNum = 0

      # Use this store IDs of wallets that are watching-only, 
      self.walletOfflines = set()

      print 'Loading wallets...'
      for f in os.listdir(ARMORY_HOME_DIR):
         if f.startswith('armory_') and f.endswith('.wallet') and \
            not f.endswith('backup.wallet') and not ('unsuccessful' in f):
               wltPaths.append(os.path.join(root, f))


      wltExclude = self.settings.get('Excluded_Wallets', expectList=True)
      wltOffline = self.settings.get('Offline_WalletIDs', expectList=True)
      for fpath in wltPaths:
         try:
            wltLoad = PyBtcWallet().readWalletFile(fpath)
            wltID = wltLoad.wltUniqueIDB58
            if fpath in wltExclude:
               continue

            if wltID in self.walletIDSet:
               print '***WARNING: Duplicate wallet detected,', wltID
               print ' '*10, 'Wallet 1 (loaded): ', self.walletMap[wltID].walletPath
               print ' '*10, 'Wallet 2 (skipped):', fpath
            else:
               # Update the maps/dictionaries
               self.walletMap[wltID] = wltLoad
               self.walletIndices[wltID] = len(self.walletMap)-1

               # Maintain some linear lists of wallet info
               self.walletIDSet.add(wltID)
               self.walletIDList.append(wltID)
               self.walletBalances.append(-1)

               if wltID in wltOffline or fpath in wltOffline:
                  self.walletOfflines.add(wltID)
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

      # Now that theb blockchain is loaded, let's populate the wallet info
      if TheBDM.isInitialized():
         self.statusBar().showMessage('Syncing wallets with blockchain...')
         print 'Syncing wallets with blockchain...'
         for wltID, wlt in self.walletMap.iteritems():
            print 'Syncing', wltID
            self.walletMap[wltID].setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
            self.walletMap[wltID].syncWithBlockchain()

            # We need to mirror all blockchain & wallet data in linear lists
            wltIndex = self.walletIndices[wltID]

            self.walletBalances[wltIndex] = wlt.getBalance()
            self.walletSubLedgers.append([])
            for addrIndex,addr in enumerate(wlt.getAddrList()):
               addr20 = addr.getAddr160()
               self.walletSubLedgers[-1].append(wlt.getTxLedger(addr20))

            t = wlt.getTxLedger()
            print wltID, len(t)
            self.walletLedgers.append(wlt.getTxLedger())
            
         self.createCombinedLedger()
         self.ledgerSize = len(self.combinedLedger)
         self.latestBlockNum = TheBDM.getTopBlockHeader().getBlockHeight()
         print len(self.combinedLedger), self.latestBlockNum
         self.statusBar().showMessage('Blockchain loaded, wallets sync\'d!', 10000)
      else:
         self.statusBar().showMessage('! Blockchain loading failed !', 10000)

      # This will force the table to refresh with new data
      #for row in range(len(self.walletMap)):
         #self.walletView.selectRow(row)
      #self.walletView.selectRow(0)
         
   def createZeroConfLedger(self, wlt):
      """
      This is kind of hacky, but I don't want to disrupt the C++ code
      too much to implement a *proper* solution... which is that I need
      to find a way to process zero-confirmation transactions and produce
      ledger entries for them, the same as all the other [past] txs.
      
      So, I added TxRef::getLedgerEntriesForZeroConfTxList to the C++ code
      (name was created to be annoying so maybe I remove/replace later).
      Then we carefully create TxRef objects to pass into it and copy out
      the resulting list.  But since these are TxREF objects, they need
      to point to persistent memory, which is why the following loops are
      weird:  they are guaranteed to create data once, and not move it 
      around in memory, so that my TxRef objects don't get mangled.  We
      only need them long enough to get the vector<LedgerEntry> result.

      (to be more specific, I'm pretty sure this should work no matter
       how wacky python's memory mgmt is, unless it moves list data around
       in memory between calls)
      """
      # We are starting with a map of PyTx objects
      zcMap   = self.NetworkingFactory.zeroConfTx
      timeMap = self.NetworkingFactory.zeroConfTxTime
      #print 'ZeroConfListSize:', len(zcMap)
      zcTxBinList = []
      zcTxRefList = []
      zcTxRefPtrList = vector_TxRefPtr(0)
      zcTxTimeList = []
      # Create persistent list of serialized Tx objects (language-agnostic)
      for zchash in zcMap.keys():
         zcTxBinList.append( zcMap[zchash].serialize() )
         zcTxTimeList.append(timeMap[zchash])
      # Create list of TxRef objects
      for zc in zcTxBinList:
         zcTxRefList.append( TxRef(zc) )
      # Python will cast to pointers when we try to add to a vector<TxRef*>
      for zc in zcTxRefList:
         zcTxRefPtrList.push_back(zc)
   
      # At this point, we will get a vector<LedgerEntry> list and TxRefs
      # can safely go out of scope
      return wlt.cppWallet.getLedgerEntriesForZeroConfTxList(zcTxRefPtrList)
   

   def createCombinedLedger(self, wltIDList=None, withZeroConf=True):
      """
      Create a ledger to display on the main screen, that consists of ledger
      entries of any SUBSET of available wallets.
      """
      start = RightNow()
      if wltIDList==None:
         wltIDList = self.walletIDList

      self.combinedLedger = []
      #for wltID,wlt in self.walletMap.iteritems():
      for wltID in wltIDList:
         wlt = self.walletMap[wltID]
         index = self.walletIndices[wltID]
         # Make sure the ledgers are up to date and then combine and sort
         #self.walletLedgers[index] = self.walletMap[wltID].getTxLedger()
         id_le_pairs   = [ [wltID, le] for le in self.walletLedgers[index] ]
         id_le_zcpairs = [ [wltID, le] for le in self.createZeroConfLedger(wlt)]
         self.combinedLedger.extend(id_le_pairs)
         self.combinedLedger.extend(id_le_zcpairs)

      self.combinedLedger.sort(key=lambda x:x[1], reverse=True)
      print 'Combined ledger:', (RightNow()-start), 'sec', len(self.combinedLedger)
      

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
         else:
            self.latestBlockNum = TheBDM.getTopBlockHeader().getBlockHeight()


      
      # Check for new tx in the zeroConf pool
      self.createCombinedLedger()

      """
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
      """


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



