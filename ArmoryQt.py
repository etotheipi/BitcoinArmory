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
#
# Descr:      This is the client/GUI for Armory.  Complete wallet management,
#             encryption, offline private keys, watching-only wallets, and
#             hopefully multi-signature transactions.
#
#             The features of the underlying library (armoryengine.py) make 
#             this considerably simpler than it could've been, but my PyQt 
#             skills leave much to be desired.
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
from qtdialogs    import *
from qtdefines    import *

# All the twisted/networking functionality
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet.defer import Deferred





class ArmoryMainWindow(QMainWindow):
   """ The primary Armory window """

   #############################################################################
   def __init__(self, parent=None, settingsPath=None):
      super(ArmoryMainWindow, self).__init__(parent)

      
      self.settingsPath = settingsPath
      self.loadWalletsAndSettings()
      self.setupNetworking()

      self.extraHeartbeatFunctions = []
      #self.extraHeartbeatFunctions.append(self.NetworkingFactory.purgeMemoryPool)
      #self.extraHeartbeatFunctions.append(self.createCombinedLedger)

      # Keep a persistent printer object for paper backups
      self.printer = QPrinter(QPrinter.HighResolution)
      self.printer.setPageSize(QPrinter.Letter)

      self.lblLogoIcon = QLabel()
      #self.lblLogoIcon.setPixmap(QPixmap('img/armory_logo_64x64.png'))
      self.lblLogoIcon.setPixmap(QPixmap('img/armory_logo_h72.png'))
      self.lblLogoIcon.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      self.setWindowTitle('Armory - Bitcoin Wallet Management')
      #self.setWindowIcon(QIcon('img/armory_logo_32x32.png'))
      self.setWindowIcon(QIcon('img/armory_icon_32x32.png'))

      # Table for all the wallets
      self.walletModel = AllWalletsDispModel(self)
      self.walletsView  = QTableView()

      # We should really start using font-metrics more, for sizing
      w,h = tightSizeNChar(self.walletsView, 70)
      viewWidth  = 1.2*w
      sectionSz  = 1.5*h
      viewHeight = 4.4*sectionSz
      
      self.walletsView.setModel(self.walletModel)
      self.walletsView.setSelectionBehavior(QTableView.SelectRows)
      self.walletsView.setSelectionMode(QTableView.SingleSelection)
      self.walletsView.verticalHeader().setDefaultSectionSize(sectionSz)
      self.walletsView.setMinimumSize(viewWidth, 4.4*sectionSz)


      if self.usermode == USERMODE.Standard:
         initialColResize(self.walletsView, [0, 0.4, 0.2, 0.2])
         self.walletsView.hideColumn(0)
      else:
         initialColResize(self.walletsView, [0.15, 0.35, 0.18, 0.18])

   


      self.connect(self.walletsView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.execDlgWalletDetails)
                  

      # Table to display ledger/activity
      self.ledgerTable = []
      self.ledgerModel = LedgerDispModelSimple(self.ledgerTable, self, self)
      self.ledgerView  = QTableView()

      w,h = tightSizeNChar(self.ledgerView, 110)
      viewWidth = 1.2*w
      sectionSz = 1.3*h
      viewHeight = 6.4*sectionSz

      self.ledgerView.setModel(self.ledgerModel)
      self.ledgerView.setItemDelegate(LedgerDispDelegate(self))
      self.ledgerView.setSelectionBehavior(QTableView.SelectRows)
      self.ledgerView.setSelectionMode(QTableView.SingleSelection)
      self.ledgerView.verticalHeader().setDefaultSectionSize(sectionSz)
      self.ledgerView.verticalHeader().hide()
      self.ledgerView.setMinimumSize(viewWidth, viewHeight)
      #self.walletsView.setStretchFactor(4)
      self.ledgerView.hideColumn(LEDGERCOLS.isOther)
      self.ledgerView.hideColumn(LEDGERCOLS.WltID)
      self.ledgerView.hideColumn(LEDGERCOLS.TxHash)
      self.ledgerView.hideColumn(LEDGERCOLS.toSelf)

      dateWidth    = tightSizeStr(self.ledgerView, '_9999-Dec-99 99:99pm__')[0]
      nameWidth    = tightSizeStr(self.ledgerView, '9'*32)[0]
      #if self.usermode==USERMODE.Standard:
      initialColResize(self.ledgerView, [20, dateWidth, 72, 0.35, 0.45, 0.3])
      #elif self.usermode in (USERMODE.Advanced, USERMODE.Developer):
         #initialColResize(self.ledgerView, [20, dateWidth, 72, 0.30, 0.45, 150, 0, 0.20, 0.10])
         #self.ledgerView.setColumnHidden(LEDGERCOLS.WltID, False)
         #self.ledgerView.setColumnHidden(LEDGERCOLS.TxHash, False)


      
      self.connect(self.ledgerView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.dblClickLedger)



      btnAddWallet = QPushButton("Create New Wallet")
      btnImportWlt = QPushButton("Import Wallet")
      self.connect(btnAddWallet, SIGNAL('clicked()'), self.createNewWallet)
      self.connect(btnImportWlt, SIGNAL('clicked()'), self.execImportWallet)

      layout = QHBoxLayout()
      layout.addSpacing(100)
      layout.addWidget(btnAddWallet)
      layout.addWidget(btnImportWlt)
      frmAddImport = QFrame()
      frmAddImport.setFrameShape(QFrame.NoFrame)

      # Put the Wallet info into it's own little box
      wltFrame = QFrame()
      wltFrame.setFrameStyle(QFrame.Box|QFrame.Sunken)
      wltLayout = QGridLayout()
      wltLayout.addWidget(QLabel("<b>Available Wallets:</b>"), 0,0)
      wltLayout.addWidget(btnAddWallet, 0,1)
      wltLayout.addWidget(btnImportWlt, 0,2)
      wltLayout.addWidget(self.walletsView, 1,0, 1,3)
      wltFrame.setLayout(wltLayout)

      # Combo box to filter ledger display
      self.comboWalletSelect = QComboBox()
      #self.comboWalletSelect.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
      self.populateLedgerComboBox()

      ccl = lambda x: self.createCombinedLedger() # ignore the arg
      self.connect(self.comboWalletSelect, SIGNAL('currentIndexChanged(QString)'), ccl)

      self.lblTotalFunds  = QLabel()
      self.lblTotalFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

      self.lblUnconfirmed = QLabel()
      self.lblUnconfirmed.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

      # Now add the ledger to the bottom of the window
      ledgFrame = QFrame()
      ledgFrame.setFrameStyle(QFrame.Box|QFrame.Sunken)
      ledgLayout = QGridLayout()
      ledgLayout.addWidget(QLabel("<b>Ledger</b>:"),  0,0)
      ledgLayout.addWidget(self.comboWalletSelect,    4,0, 2,1)
      ledgLayout.addWidget(self.ledgerView,           1,0, 3,4)
      ledgLayout.addWidget(self.lblTotalFunds,        4,2, 1,2)
      ledgLayout.addWidget(self.lblUnconfirmed,       5,2, 1,2)
      ledgFrame.setLayout(ledgLayout)


      btnSendBtc   = QPushButton("Send Bitcoins")
      btnRecvBtc   = QPushButton("Receive Bitcoins")
      btnWltProps  = QPushButton("Wallet Properties")
      btnUnsigned  = QPushButton("Unsigned Transactions")
      btnDevTools  = QPushButton("Developer Tools")
      btnMemPool   = QPushButton("See memory pool")
 

      self.connect(btnWltProps, SIGNAL('clicked()'), self.execDlgWalletDetails)
   
      self.connect(btnRecvBtc,  SIGNAL('clicked()'), self.clickReceiveCoins)
      self.connect(btnSendBtc,  SIGNAL('clicked()'), self.clickSendBitcoins)
      self.connect(btnMemPool,  SIGNAL('clicked()'), self.printZeroConf)
      self.connect(btnDevTools, SIGNAL('clicked()'), self.openDevTools)
      # QTableView.selectedIndexes to get the selection

      layout = QVBoxLayout()
      layout.addWidget(btnSendBtc)
      layout.addWidget(btnRecvBtc)
      layout.addWidget(btnWltProps)
      
      if self.usermode in (USERMODE.Advanced, USERMODE.Developer):
         layout.addWidget(btnUnsigned)
      if self.usermode==USERMODE.Developer:
         layout.addWidget(btnDevTools)
         layout.addWidget(btnMemPool)
      layout.addStretch()
      btnFrame = QFrame()
      btnFrame.setLayout(layout)

      
      layout = QGridLayout()
      layout.addWidget(self.lblLogoIcon,  0, 0, 1, 2)
      layout.addWidget(btnFrame,          1, 0, 2, 2)
      layout.addWidget(wltFrame,          0, 2, 3, 2)
      layout.addWidget(ledgFrame,         3, 0, 4, 4)

      # Attach the layout to the frame that will become the central widget
      mainFrame = QFrame()
      mainFrame.setLayout(layout)
      self.setCentralWidget(mainFrame)
      #if self.usermode==USERMODE.Standard:
      self.setMinimumSize(900,300)
      #else:
         #self.setMinimumSize(1200,300)

      #self.statusBar().showMessage('Blockchain loading, please wait...')

      self.loadBlockchain()
      self.ledgerTable = self.convertLedgerToTable(self.combinedLedger)
      self.ledgerModel = LedgerDispModelSimple(self.ledgerTable, self, self)
      self.ledgerView.setModel(self.ledgerModel)
      from twisted.internet import reactor

      ##########################################################################
      # Set up menu and actions
      MENUS = enum('File', 'Wallet', 'User')
      self.menu = self.menuBar()
      self.menusList = []
      self.menusList.append( self.menu.addMenu('&File') )
      self.menusList.append( self.menu.addMenu('&Wallet') )
      self.menusList.append( self.menu.addMenu('&User') )
      
      def chngStd(b): 
         if b: self.setUserMode(USERMODE.Standard)
      def chngAdv(b): 
         if b: self.setUserMode(USERMODE.Advanced)
      def chngDev(b): 
         if b: self.setUserMode(USERMODE.Developer)

      modeActGrp = QActionGroup(self)
      actSetModeStd = self.createAction('&Standard',  chngStd, True)
      actSetModeAdv = self.createAction('&Advanced',  chngAdv, True)
      actSetModeDev = self.createAction('&Developer', chngDev, True)

      modeActGrp.addAction(actSetModeStd)
      modeActGrp.addAction(actSetModeAdv)
      modeActGrp.addAction(actSetModeDev)

      self.menusList[MENUS.User].addAction(actSetModeStd)
      self.menusList[MENUS.User].addAction(actSetModeAdv)
      self.menusList[MENUS.User].addAction(actSetModeDev)

      currmode = self.settings.get('User_Mode')
      print currmode
      if not currmode: 
         # On first run, set to standard mode
         actSetModeStd.setChecked(True)
      else:
         if currmode==USERMODE.Standard:   
            actSetModeStd.setChecked(True)
         if currmode==USERMODE.Advanced:   
            actSetModeAdv.setChecked(True)
         if currmode==USERMODE.Developer:  
            actSetModeDev.setChecked(True)

      
      #reactor.callLater(2.0,  self.loadBlockchain)
      reactor.callLater(5, self.Heartbeat)


   #############################################################################
   def sizeHint(self):
      return QSize(1000, 650)

   #############################################################################
   def openDevTools(self):
      pass

   #############################################################################
   def printZeroConf(self):
      print 'Printing memory pool:'
      for k,v in self.NetworkingFactory.zeroConfTx.iteritems():
         print binary_to_hex(k), ' '.join([ coin2str(txout.getValue()) for txout in v.outputs])
      self.NetworkingFactory.purgeMemoryPool()

   
   #############################################################################
   def createAction(self,  txt, slot, isCheckable=False, \
                           ttip=None, iconpath=None, shortcut=None):
      """
      Modeled from the "Rapid GUI Programming with Python and Qt" book, page 174
      """
      icon = QIcon()
      if iconpath:
         icon = QIcon(iconpath)

      theAction = QAction(icon, txt, self) 
   
      if isCheckable:
         theAction.setCheckable(True)
         self.connect(theAction, SIGNAL('toggled(bool)'), slot)
      else:
         self.connect(theAction, SIGNAL('triggered()'), slot)

      if ttip:
         theAction.setToolTip(ttip)
         theAction.setStatusTip(ttip)

      if shortcut:
         theAction.setShortcut(shortcut)
      
      return theAction


   #############################################################################
   def setUserMode(self, mode):
      self.usermode = mode
      if mode==USERMODE.Standard:
         self.settings.set('User_Mode', 'Standard')
      if mode==USERMODE.Advanced:
         self.settings.set('User_Mode', 'Advanced')
      if mode==USERMODE.Developer:
         self.settings.set('User_Mode', 'Developer')
      QMessageBox.information(self,'Restart Required', \
         'You must restart Armory in order for the user-mode switching '
         'to take effect.', QMessageBox.Ok)
      


   #############################################################################
   def setupNetworking(self):

      from twisted.internet import reactor
      def restartConnection(protoObj, failReason):
         QMessageBox.critical(self, 'Lost Connection', \
            'Connection to Satoshi client was interrupted.  Please make sure '
            'bitcoin/bitcoind is running, and restart Armory', QMessageBox.Ok)
         print '! Trying to restart connection !'
         reactor.connectTCP(protoObj.peer[0], protoObj.peer[1], self.NetworkingFactory)

      def lockTxOutsAsNecessary(pytxObj):
         for wlt in self.walletMap.itervalues():
            wlt.lockTxOutsOnNewTx(pytxObj)

      self.NetworkingFactory = ArmoryClientFactory( \
                                       func_loseConnect=restartConnection, \
                                       func_newTx=lockTxOutsAsNecessary)
      self.NetworkingFactory.fileMemPool = os.path.join(ARMORY_HOME_DIR, 'mempool.bin')
      self.NetworkingFactory.loadMemoryPool()
      reactor.connectTCP('127.0.0.1', BITCOIN_PORT, self.NetworkingFactory)
      print 'Connected to localhost! (I think...)'




   #############################################################################
   def loadWalletsAndSettings(self):
      self.settings = SettingsFile(self.settingsPath)

      # Determine if we need to do new-user operations, increment load-count
      self.firstLoad = False
      if self.settings.getSettingOrSetDefault('First_Load', True):
         self.firstLoad = True
         self.settings.set('First_Load', False)
         self.settings.set('First_Load_Date', long(RightNow()))
         self.settings.set('Load_Count', 1)
         self.settings.set('AdvFeature_UseCt', 0)
      else:
         self.settings.set('Load_Count', (self.settings.get('Load_Count')+1) % 100)
         firstDate = self.settings.getSettingOrSetDefault('First_Load_Date', RightNow())
         daysSinceFirst = (RightNow() - firstDate) / (60*60*24)
         

      # Set the usermode, default to standard
      self.usermode = USERMODE.Standard
      if self.settings.get('User_Mode') == 'Advanced':
         self.usermode = USERMODE.Advanced
      elif self.settings.get('User_Mode') == 'Developer':
         self.usermode = USERMODE.Developer

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
      self.ledgerTable = []

      self.latestBlockNum = 0

      self.zeroConfWltLEs = {}
      self.zeroConfAddrLEs = {}


      print 'Loading wallets...'
      for f in os.listdir(ARMORY_HOME_DIR):
         fullPath = os.path.join(ARMORY_HOME_DIR, f)
         if os.path.isfile(fullPath) and not fullPath.endswith('backup.wallet'):
            openfile = open(fullPath, 'r')
            first8 = openfile.read(8) 
            openfile.close()
            if first8=='\xbaWALLET\x00':
               wltPaths.append(fullPath)


      wltExclude = self.settings.get('Excluded_Wallets', expectList=True)
      wltOffline = self.settings.get('Offline_WalletIDs', expectList=True)
      for fpath in wltPaths:
         try:
            wltLoad = PyBtcWallet().readWalletFile(fpath)
            wltID = wltLoad.uniqueIDB58
            if fpath in wltExclude or wltID in wltExclude:
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
         except:
            print '***WARNING: Wallet could not be loaded:', fpath
            print '            skipping... '
            raise
                     

      # We will use the settings file to store other:  we will have one entry
      # for each wallet and it will contain a list of strings (dict-esque)
      # that we might want to store about that wallet, that cannot be stored
      # in the wallet file itself:
      #   Wallet_287cFxkr3_IsMine     |  True
      #   Wallet_287cFxkr3_BelongsTo  |  Joe the plumber
      #self.wltExtraProps = {}
      #for name,val in self.settings.getAllSettings().iteritems():
         #parts = name.split('_')
         #if len(parts)>=3 and parts[0]=='Wallet' and self.walletMap.has_key(parts[1]):
            ## The last part is the prop name and the value is the property 
            #wltID=parts[1]
            #propName=parts[2:]
            #if not self.wltExtraProps.has_key(wltID):
               #self.wltExtraProps[wltID] = {}
            #self.wltExtraProps[wltID][propName] = self.settings.get(name)

         
            
      
      print 'Number of wallets read in:', len(self.walletMap)
      for wltID, wlt in self.walletMap.iteritems():
         print '   Wallet (%s):'.ljust(20) % wlt.uniqueIDB58,
         print '"'+wlt.labelName+'"   ',
         print '(Encrypted)' if wlt.useEncryption else '(No Encryption)'


      # Get the last directory
      savedDir = self.settings.get('LastDirectory')
      if len(savedDir)==0 or not os.path.exists(savedDir):
         savedDir = ARMORY_HOME_DIR
      self.lastDirectory = savedDir
      self.settings.set('LastDirectory', savedDir)


   #############################################################################
   def getFileSave(self, title='Save Wallet File', ffilter=['Wallet files (*.wallet)']):
      lastDir = self.settings.get('LastDirectory')
      if len(lastDir)==0 or not os.path.exists(lastDir):
         lastDir = ARMORY_HOME_DIR

      types = list(ffilter)
      types.append('All files (*)')
      typesStr = ';; '.join(types)
      fullPath = unicode(QFileDialog.getSaveFileName(self, title, lastDir, typesStr))
      

      fdir,fname = os.path.split(fullPath)
      if fdir:
         self.settings.set('LastDirectory', fdir)
      return fullPath
      

   #############################################################################
   def getFileLoad(self, title='Load Wallet File', ffilter=['Wallet files (*.wallet)']):
      lastDir = self.settings.get('LastDirectory')
      if len(lastDir)==0 or not os.path.exists(lastDir):
         lastDir = ARMORY_HOME_DIR

      types = list(ffilter)
      types.append('All files (*)')
      typesStr = ';; '.join(types)
      fullPath = unicode(QFileDialog.getOpenFileName(self, title, lastDir, typesStr))

      self.settings.set('LastDirectory', fdir)
      return fullPath
   
   ##############################################################################
   def getWltSetting(self, wltID, propName):
      wltPropName = 'Wallet_%s_%s' % (wltID, propName)
      try:
         return self.settings.get(wltPropName)
      except KeyError:
         return ''

   #############################################################################
   def setWltSetting(self, wltID, propName, value):
      wltPropName = 'Wallet_%s_%s' % (wltID, propName)
      self.settings.set(wltPropName, value)


   #############################################################################
   def toggleIsMine(self, wltID):
      alreadyMine = self.getWltSetting(wltID, 'IsMine')
      if alreadyMine:
         self.setWltSetting(wltID, 'IsMine', False)
      else:
         self.setWltSetting(wltID, 'IsMine', True)
   
   


   #############################################################################
   def getWalletForAddr160(self, addr160):
      for wltID, wlt in self.walletMap.iteritems():
         if wlt.hasAddr(addr160):
            return wltID
      return ''




   #############################################################################
   def loadBlockchain(self):
      print 'Loading blockchain'

      BDM_LoadBlockchainFile()
      self.latestBlockNum = TheBDM.getTopBlockHeader().getBlockHeight()

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
               ledger = wlt.getTxLedger(addr20)
               self.walletSubLedgers[-1].append(ledger)

            self.walletLedgers.append(wlt.getTxLedger())
            
         self.createCombinedLedger(self.walletIDList)
         self.ledgerSize = len(self.combinedLedger)
         print 'Ledger entries:', len(self.combinedLedger), 'Max Block:', self.latestBlockNum
         self.statusBar().showMessage('Blockchain loaded, wallets sync\'d!', 10000)
      else:
         self.statusBar().showMessage('! Blockchain loading failed !', 10000)

      # This will force the table to refresh with new data
      self.walletModel.reset()
         

   #############################################################################
   def updateZeroConfLedger(self, wlt):
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
      print '***Creating zero-conf ledger',
      # We are starting with a map of PyTx objects

      """
      """
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
         zcTxRefList.append( TxRef().createFromStr(zc) )
      # Python will cast to pointers when we try to add to a vector<TxRef*>
      for zc in zcTxRefList:
         zcTxRefPtrList.push_back(zc)
   
      # At this point, we will get a vector<LedgerEntry> list and TxRefs
      # can safely go out of scope
      return wlt.cppWallet.getLedgerEntriesForZeroConfTxList(zcTxRefPtrList)
      """
      """
      Need to convert the zeroConfTxList maintained by NetworkingFactory into
      LedgerEntry objects that can be inclued in the ledger views.  We use
      a special C++ method specifically for scanning zero-conf tx without 
      affecting the underlying wallets.

      zeroConfWltLEs [wltID][txHash]          =   LedgerEntry()
      zeroConfAddrLEs[wltID][txHash][addr160] = [ LedgerEntry(), LedgerEntry(), ... ]

      """
      wltID = wlt.uniqueIDB58
      if not self.zeroConfWltLEs.has_key(wltID):  self.zeroConfWltLEs[wltID] = {}
      if not self.zeroConfAddrLEs.has_key(wltID): self.zeroConfAddrLEs[wltID] = {}

      for txHash,pytx in self.NetworkingFactory.zeroConfTx.iteritems():
         # Delete entries that made it into the blockchain
         if TheBDM.isInitialized() and TheBDM.getTxByHash(txHash):
            if self.zeroConfWltLEs[wltID].has_key(txHash):
               del self.zeroConfWltLEs[wltID][txHash]
               del self.zeroConfAddrLEs[wltID][txHash]


         # Add wallet-level ledger entries for zero-conf list
         le = wlt.cppWallet.getWalletLedgerEntryForTx(pytx.serialize())
         if le.getIndex()<2**32-1:
            if not self.zeroConfWltLEs[wltID].has_key(txHash):
               le.pprint()
               self.zeroConfWltLEs[wltID][txHash] = le


            # Add address-level ledger entries for zero-conf list
            leVect = wlt.cppWallet.getAddrLedgerEntriesForTx(pytx.serialize())
            for lev in leVect:
               # Make sure we have an entry for this tx
               if not self.zeroConfAddrLEs[wltID].has_key(txHash):
                  self.zeroConfAddrLEs[wltID][txHash] = {}
   
               # Make sure we have an sub-entry for this address
               addr20 = le.getAddrStr20()
               if not self.zeroConfAddrLEs[wltID][txHash].has_key(addr20):
                  self.zeroConfAddrLEs[wltID][txHash][addr20] = []
   
               # Now actually add this ledger entry to the addr le list
               alreadyInList = False
               for existingLE in self.zeroConfAddrLEs[wltID][txHash][addr20]:
                  if lev.getIndex() == existingLE.getIndex():
                     alreadyInList = True
   
               if not alreadyInList:
                  self.zeroConfAddrLEs[wltID][txHash][addr20].append(lev)
                  lev.pprint()

         
      
       
      
   

   #############################################################################
   def createCombinedLedger(self, wltIDList=None, withZeroConf=True):
      """
      Create a ledger to display on the main screen, that consists of ledger
      entries of any SUBSET of available wallets.
      """
      print '---Creating combined ledger'
      start = RightNow()
      if wltIDList==None:
         # Create a list of [wltID, type] pairs
         typelist = [[wid, determineWalletType(self.walletMap[wid], self)[0]] \
                                                      for wid in self.walletIDList]

         # We need to figure out which wallets to combine here...
         currIdx  =     self.comboWalletSelect.currentIndex()
         currText = str(self.comboWalletSelect.currentText()).lower()
         if currIdx>=4:
            wltIDList = [self.walletIDList[currIdx-6]]
         else:
            listOffline  = [t[0] for t in filter(lambda x: x[1]==WLTTYPES.Offline,   typelist)]
            listWatching = [t[0] for t in filter(lambda x: x[1]==WLTTYPES.WatchOnly, typelist)]
            listCrypt    = [t[0] for t in filter(lambda x: x[1]==WLTTYPES.Crypt,     typelist)]
            listPlain    = [t[0] for t in filter(lambda x: x[1]==WLTTYPES.Plain,     typelist)]
            
            if currIdx==0:
               wltIDList = self.walletIDList
            elif currIdx==1:
               wltIDList = listOffline + listCrypt + listPlain
            elif currIdx==2:
               wltIDList = listOffline
            elif currIdx==3:
               wltIDList = listWatching
            else:
               pass
               #raise WalletExistsError, 'Bad combo-box selection: ' + str(currIdx)
               

      self.combinedLedger = []
      if wltIDList==None:
         return

      for wltID in wltIDList:
         wlt = self.walletMap[wltID]
         index = self.walletIndices[wltID]

         # Add the LedgerEntries from the blockchain
         self.walletLedgers[index] = self.walletMap[wltID].getTxLedger()
         id_le_pairs = [ [wltID, le] for le in self.walletLedgers[index] ]
         self.combinedLedger.extend(id_le_pairs)

         # Calculate and add the LedgerEntries from zero-conf tx
         self.updateZeroConfLedger(wlt)
         for hsh,le in self.zeroConfWltLEs[wltID].iteritems():
            self.combinedLedger.append([wltID, le])

      self.combinedLedger.sort(key=lambda x:x[1], reverse=True)
      self.ledgerSize = len(self.combinedLedger)

      # Many MainWindow objects haven't been created yet... 
      # let's try to update them and fail silently if they don't exist
      try:

         totFund, unconfFund = 0,0
         for wlt,le in self.combinedLedger:
            if (self.latestBlockNum-le.getBlockNum()+1) < 6:
               unconfFund += le.getValue()
            else:
               totFund += le.getValue()
               
         uncolor = 'red' if unconfFund>0 else 'black'
         self.lblUnconfirmed.setText( \
            '<b>Unconfirmed: <font color="%s"   >%s</font> BTC</b>' % (uncolor,coin2str(unconfFund)))
         self.lblTotalFunds.setText( \
            '<b>Total Funds: <font color="green">%s</font> BTC</b>' % coin2str(totFund))

         # Finally, update the ledger table
         self.ledgerTable = self.convertLedgerToTable(self.combinedLedger)
         self.ledgerModel = LedgerDispModelSimple(self.ledgerTable, self, self)
         self.ledgerView.setModel(self.ledgerModel)
         #self.ledgerModel.reset()

      except AttributeError:
         pass
      

   #############################################################################
   def getFeeForTx(self, txHash):
      if TheBDM.isInitialized():
         txref = TheBDM.getTxByHash(txHash)
         if not txref:
            print 'Why no txref? ', binary_to_hex(txHash)
            return 0

         valIn, valOut = 0,0
         for i in range(txref.getNumTxIn()):
            valIn += TheBDM.getSentValue(txref.getTxInRef(i))
         for i in range(txref.getNumTxOut()):
            valOut += txref.getTxOutRef(i).getValue()
         return valIn - valOut
      

   #############################################################################
   def determineSentToSelfAmt(self, le, wlt):
      """
      NOTE:  this method works ONLY because we always generate a new address
             whenever creating a change-output, which means it must have a
             higher chainIndex than all other addresses.  If you did something 
             creative with this tx, this may not actually work.
      """
      amt = 0
      if TheBDM.isInitialized() and le.isSentToSelf():
         txref = TheBDM.getTxByHash(le.getTxHash())
         maxChainIndex = -5
         txOutChangeVal = 0
         txOutIndex = -1
         valSum = 0
         for i in range(txref.getNumTxOut()):
            valSum += txref.getTxOutRef(i).getValue()
            addr160 = txref.getTxOutRef(i).getRecipientAddr()
            addr    = wlt.getAddrByHash160(addr160)
            if addr.chainIndex > maxChainIndex:
               maxChainIndex = addr.chainIndex
               txOutChangeVal = txref.getTxOutRef(i).getValue()
               txOutIndex = i
                  
         amt = valSum - txOutChangeVal
      return (amt, txOutIndex)
      

   #############################################################################
   def convertLedgerToTable(self, ledger):
      
      table2D = []
      for wltID,le in ledger: 
         row = []

         wlt = self.walletMap[wltID]
         nConf = self.latestBlockNum - le.getBlockNum()+1
         if le.getBlockNum()>=0xffffffff:
            nConf=0

         # We need to compute the fee by adding inputs and outputs...
         amt = le.getValue()
         removeFee = self.settings.getSettingOrSetDefault('DispRmFee', True)
         if TheBDM.isInitialized() and removeFee and amt<0:
            theFee = self.getFeeForTx(le.getTxHash())
            amt += theFee

         # If this was sent-to-self... we should display the actual specified
         # value when the transaction was executed.  This is pretty difficult 
         # when both "recipient" and "change" are indistinguishable... but
         # They're actually not because we ALWAYS generate a new address to
         # for change , which means the change address MUST have a higher 
         # chain index
         if le.isSentToSelf():
            amt = self.determineSentToSelfAmt(le, wlt)[0]
            

         if le.getBlockNum() >= 0xffffffff: nConf = 0
         # NumConf
         row.append(nConf)

         # Date
         if nConf>0: 
            txtime = TheBDM.getHeaderByHeight(le.getBlockNum()).getTimestamp()
         else:       
            pass
            txtime = 2**32-1
            #txtime = self.NetworkingFactory.zeroConfTxTime[le.getTxHash()]
         row.append(unixTimeToFormatStr(txtime))

         # TxDir (actually just the amt... use the sign of the amt for what you want)
         row.append(coin2str(le.getValue(), maxZeros=2))

         # Wlt Name
         row.append(self.walletMap[wltID].labelName)
         
         # Comment
         if wlt.commentsMap.has_key(le.getTxHash()):
            row.append(wlt.commentsMap[le.getTxHash()])
         else:
            row.append('')

         # Amount
         row.append(coin2str(amt, maxZeros=2))

         # Is this money mine?
         row.append( determineWalletType(wlt, self)[0]==WLTTYPES.WatchOnly)

         # WltID
         row.append( wltID )

         # TxHash
         row.append( binary_to_hex(le.getTxHash() ))

         # Sent-to-self
         row.append( le.isSentToSelf() )

         # Finally, attach the row to the table
         table2D.append(row)

      return table2D

      
   #############################################################################
   def walletListChanged(self):
      self.walletModel.reset()
      self.populateLedgerComboBox()
      #self.comboWalletSelect.setCurrentItem(0)
      self.createCombinedLedger()


   #############################################################################
   def populateLedgerComboBox(self):
      self.comboWalletSelect.clear()
      self.comboWalletSelect.addItem( 'All Wallets'       )
      self.comboWalletSelect.addItem( 'My Wallets'        )
      self.comboWalletSelect.addItem( 'Offline Wallets'   )
      self.comboWalletSelect.addItem( 'Other\'s wallets'  )
      for wltID in self.walletIDList:
         self.comboWalletSelect.addItem( self.walletMap[wltID].labelName )
      self.comboWalletSelect.insertSeparator(4)
      self.comboWalletSelect.insertSeparator(4)
      

   #############################################################################
   def execDlgWalletDetails(self, index=None):
      if index==None:
         index = self.walletsView.selectedIndexes()
         if len(index)==0:
            return
         index = index[0]
         
      wlt = self.walletMap[self.walletIDList[index.row()]]
      dialog = DlgWalletDetails(wlt, self.usermode, self, self)
      dialog.exec_()
      self.walletListChanged()
         
         
         
   #############################################################################
   def updateTxCommentFromView(self, view):
      index = view.selectedIndexes()[0]
      row, col = index.row(), index.column()
      currComment = str(view.model().index(row, LEDGERCOLS.Comment).data().toString())
      wltID       = str(view.model().index(row, LEDGERCOLS.WltID  ).data().toString())
      txHash      = str(view.model().index(row, LEDGERCOLS.TxHash ).data().toString())

      dialog = DlgSetComment(currComment, 'Transaction', self, self)
      if dialog.exec_():
         newComment = str(dialog.edtComment.text())
         self.walletMap[wltID].setComment(hex_to_binary(txHash), newComment)
         self.walletListChanged()

   #############################################################################
   def updateAddressCommentFromView(self, view, wlt):
      index = view.selectedIndexes()[0]
      row, col = index.row(), index.column()
      currComment = str(view.model().index(row, ADDRESSCOLS.Comment).data().toString())
      addrStr     = str(view.model().index(row, ADDRESSCOLS.Address).data().toString())

      dialog = DlgSetComment(currComment, 'Address', self, self)
      if dialog.exec_():
         newComment = str(dialog.edtComment.text())
         addr160 = addrStr_to_hash160(addrStr)
         wlt.setComment(addr160, newComment)


   #############################################################################
   def addWalletToApplication(self, newWallet, walletIsNew=True):
      # Update the maps/dictionaries
      newWltID = newWallet.uniqueIDB58
      self.walletMap[newWltID] = newWallet
      self.walletIndices[newWltID] = len(self.walletMap)-1

      # Maintain some linear lists of wallet info
      self.walletIDSet.add(newWltID)
      self.walletIDList.append(newWltID)

      ledger = []
      wlt = self.walletMap[newWltID]
      if not walletIsNew:
         # We may need to search the blockchain for existing tx
         wlt.setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
         wlt.syncWithBlockchain()

         self.walletSubLedgers.append([])
         for addr in wlt.getLinearAddrList():
            ledger = wlt.getTxLedger(addr.getAddr160())
            self.walletSubLedgers[-1].append(ledger)
         self.walletLedgers.append(wlt.getTxLedger())
         self.walletBalances.append(wlt.getBalance())
      else:
         self.walletBalances.append(0)
         self.walletLedgers.append([])
         self.walletSubLedgers.append([])
         self.walletSubLedgers[-1].append([])


      self.walletListChanged()

      
   #############################################################################
   def removeWalletFromApplication(self, wltID):

      idx = -1
      try:
         idx = self.walletIndices[wltID]
      except KeyError:
         print 'Invalid wallet ID passed to "removeWalletFromApplication"'
         raise WalletExistsError

      del self.walletMap[wltID]
      del self.walletIndices[wltID]
      self.walletIDSet.remove(wltID)
      del self.walletIDList[idx]
      del self.walletLedgers[idx]
      del self.walletSubLedgers[idx]
      del self.walletBalances[idx]

      # Reconstruct walletIndices
      for i,wltID in enumerate(self.walletIDList):
         self.walletIndices[wltID] = i

      self.walletListChanged()

   
   #############################################################################
   def createNewWallet(self):
      dlg = DlgNewWallet(self, self)
      if dlg.exec_():

         if dlg.selectedImport:
            self.execImportWallet()
            return
            
         name     = str(dlg.edtName.text())
         descr    = str(dlg.edtDescr.toPlainText())
         kdfSec   = dlg.kdfSec
         kdfBytes = dlg.kdfBytes

         # If this will be encrypted, we'll need to get their passphrase
         passwd = []
         if dlg.chkUseCrypto.isChecked():
            dlgPasswd = DlgChangePassphrase(self, self)
            if dlgPasswd.exec_():
               passwd = SecureBinaryData(str(dlgPasswd.edtPasswd1.text()))
            else:
               return # no passphrase == abort new wallet
      else:
         return False

      newWallet = None
      if passwd:
          newWallet = PyBtcWallet().createNewWallet( \
                                           withEncrypt=True, \
                                           securePassphrase=passwd, \
                                           kdfTargSec=kdfSec, \
                                           kdfMaxMem=kdfBytes, \
                                           shortLabel=name, \
                                           longLabel=descr)
      else:
          newWallet = PyBtcWallet().createNewWallet( \
                                           withEncrypt=False, \
                                           shortLabel=name, \
                                           longLabel=descr)

      # Update the maps/dictionaries
      #newWltID = newWallet.uniqueIDB58
      #self.walletMap[newWltID] = newWallet
      #self.walletIndices[newWltID] = len(self.walletMap)-1

      # Maintain some linear lists of wallet info
      #self.walletIDSet.add(newWltID)
      #self.walletIDList.append(newWltID)
      #self.walletBalances.append(0)
      #self.walletLedgers.append([])
      #self.walletListChanged()

      self.addWalletToApplication(newWallet)

      if dlg.chkPrintPaper.isChecked():
         dlg = DlgPaperBackup(newWallet, self, self)
         dlg.exec_()




   def createSweepAddrTx(self, addrToSweepList, sweepTo160, forceZeroFee=False):
      """
      This method takes a list of addresses (likely just created from private
      key data), finds all their unspent TxOuts, and creates a signed tx that
      transfers 100% of the funds to the sweepTO160 address.  It doesn't 
      actually execute the transaction, but it will return a broadcast-ready
      PyTx object that the user can confirm.  TxFee is automatically calc'd
      and deducted from the output value, if necessary.
      """
      if not isinstance(addrToSweepList, (list, tuple)):
         addrToSweepList = [addrToSweepList]
      addr160List = [a.getAddr160() for a in addrToSweepList]
      getAddr = lambda addr160: addrToSweepList[addr160List.index(addr160)]

      utxoList = getUnspentTxOutsForAddrList(addr160List)
      outValue = sumTxOutList(utxoList)

      pprintUnspentTxOutList(utxoList)
      print 'OutValue:', outValue
      

      inputSide = []
      for utxo in utxoList:
         # The PyCreateAndSignTx method require PyTx and PyBtcAddress objects
         CppPrevTx = TheBDM.getTxByHash(utxo.getTxHash()) 
         PyPrevTx = PyTx().unserialize(CppPrevTx.serialize())
         addr160 = utxo.getRecipientAddr()
         inputSide.append([getAddr(addr160), PyPrevTx, utxo.getTxOutIndex()])

      minFee = calcMinSuggestedFees(utxoList, outValue, 0)[1]

      if minFee > 0 and \
         not forceZeroFee and \
         not self.settings.getSettingOrSetDefault('OverrideMinFee', False):
         print 'Subtracting fee from Sweep-output'
         outValue -= minFee
      outputSide = []
      outputSide.append( [PyBtcAddress().createFromPublicKeyHash160(sweepTo160), outValue] )

      pytx = PyCreateAndSignTx(inputSide, outputSide)
      pytx.pprint()
      return (pytx, outValue, minFee)



   #############################################################################
   def broadcastTransaction(self, pytx, dryRun=False):
      if dryRun:
         pytx.pprint()
         #DlgDispTxInfo(pytx, None, self, self).exec_()
      else:
         # TODO:  MAKE SURE THE TX WAS ACCEPTED?
         print 'Sending Tx,', binary_to_hex(pytx.getHash())
         self.NetworkingFactory.sendTx(pytx)
         self.NetworkingFactory.addTxToMemoryPool(pytx)
         for wltID,wlt in self.walletMap.iteritems():
            wlt.lockTxOutsOnNewTx(pytx.copy())
         self.NetworkingFactory.saveMemoryPool()
         print 'Done!'
      
   
            
            
   #############################################################################
   def execImportWallet(self):
      print 'Executing!'
      dlg = DlgImportWallet(self, self)
      if dlg.exec_():

         if dlg.importType_file:
            if not os.path.exists(dlg.importFile):
               raise FileExistsError, 'How did the dlg pick a wallet file that DNE?'

            wlt = PyBtcWallet().readWalletFile(dlg.importFile, verifyIntegrity=False, \
                                                               skipBlockChainScan=True)
            wltID = wlt.uniqueIDB58

            if self.walletMap.has_key(wltID):
               QMessageBox.warning(self, 'Duplicate Wallet!', \
                  'You selected a wallet that has the same ID as one already '
                  'in your wallet (%s)!  If you would like to import it anyway, '
                  'please delete the duplicate wallet in Armory, first.'%wltID, \
                  QMessageBox.Ok)
               return

            fname = self.getUniqueWalletFilename(dlg.importFile)
            newpath = os.path.join(ARMORY_HOME_DIR, fname)

            print 'Copying imported wallet to:', newpath
            shutil.copy(dlg.importFile, newpath)
            self.addWalletToApplication(PyBtcWallet().readWalletFile(newpath), \
                                                               walletIsNew=False)
         elif dlg.importType_paper:
            dlgPaper = DlgImportPaperWallet(self, self)
            if dlgPaper.exec_():
               print 'Raw import successful.  Searching blockchain for tx data...'
               highestIdx = dlgPaper.newWallet.freshImportFindHighestIndex()
               print 'The highest index used was:', highestIdx
               self.addWalletToApplication(dlgPaper.newWallet, walletIsNew=False)
               print 'Import Complete!'
         else:
            return

   
   #############################################################################
   def getUniqueWalletFilename(self, wltPath):
      root,fname = os.path.split(wltPath)
      base,ext   = os.path.splitext(fname)
      if not ext=='.wallet':
         fname = base+'.wallet'
      currHomeList = os.listdir(ARMORY_HOME_DIR)
      newIndex = 2
      while fname in currHomeList:
         # If we already have a wallet by this name, must adjust name
         base,ext = os.path.splitext(fname)
         fname='%s_%02d.wallet'%(base, newIndex)
         newIndex+=1
         if newIndex==99:
            raise WalletExistsError, ('Cannot find unique filename for wallet.'  
                                      'Too many duplicates!')
      return fname
         

   #############################################################################
   def addrViewDblClicked(self, index, wlt):
      uacfv = lambda x: self.main.updateAddressCommentFromView(self.wltAddrView, self.wlt)


   #############################################################################
   def dblClickLedger(self, index):
      if index.column()==LEDGERCOLS.Comment:
         self.updateTxCommentFromView(self.ledgerView)
      else:
         row = index.row()
         txHash = str(self.ledgerView.model().index(row, LEDGERCOLS.TxHash).data().toString())
         wltID  = str(self.ledgerView.model().index(row, LEDGERCOLS.WltID).data().toString())

         pytx = None
         if self.NetworkingFactory.zeroConfTx.has_key(txHash):
            pytx = self.NetworkingFactory.zeroConfTx[txHash]
         if TheBDM.isInitialized():
            cppTx = TheBDM.getTxByHash(hex_to_binary(txHash))
            if cppTx:
               pytx = PyTx().unserialize(cppTx.serialize())

         if pytx==None:
            QMessageBox.critical(self, 'Invalid Tx:',
            'The transaction ID requested to be displayed does not exist in '
            'the blockchain or the zero-conf tx list...?', QMessageBox.Ok)
            return

         DlgDispTxInfo( pytx, self.walletMap[wltID], self, self).exec_()


   #############################################################################
   def clickSendBitcoins(self):
      wltSelect = self.walletsView.selectedIndexes()
      wltID = None
      if len(wltSelect)>0:
         row = wltSelect[0].row()
         wltID = str(self.walletsView.model().index(row, WLTVIEWCOLS.ID).data().toString())
      dlg = DlgWalletSelect(self, self, 'Send from Wallet...', wltID, onlyMyWallets=True)
      if dlg.exec_():
         wltID = dlg.selectedID 
         wlt = self.walletMap[wltID]

         wlttype = determineWalletType(wlt, self)[0]
         #if wlttype=WLTTYPES.WatchOnly:
            #QMessageBox.warning(self, '
         #elif wlttype==WLTTYPES.Offline:

         dlgSend = DlgSendBitcoins(wlt, self, self)
         dlgSend.exec_()
   

   #############################################################################
   def clickReceiveCoins(self):
      wltSelect = self.walletsView.selectedIndexes()
      wltID = None
      if len(wltSelect)>0:
         row = wltSelect[0].row()
         wltID = str(self.walletsView.model().index(row, WLTVIEWCOLS.ID).data().toString())
      dlg = DlgWalletSelect(self, self, wltID, onlyMyWallets=True)
      if dlg.exec_():
         wltID = dlg.selectedID 
         wlt = self.walletMap[wltID]
         dlgaddr = DlgNewAddressDisp(wlt, self, self)
         dlgaddr.exec_()

   #############################################################################
   def Heartbeat(self, nextBeatSec=2):
      """
      This method is invoked when the app is initialized, and will
      run every 2 seconds, or whatever is specified in the nextBeatSec
      argument.
      """
      #print '.',
      # Check for new blocks in the blk0001.dat file
      if TheBDM.isInitialized():
         newBlks = TheBDM.readBlkFileUpdate()
         if newBlks>0:
            self.ledgerModel.reset()
            self.latestBlockNum = TheBDM.getTopBlockHeader().getBlockHeight()
            didAffectUs = False
            for wltID in self.walletMap.keys():
               prevLedgerSize = len(self.walletMap[wltID].getTxLedger())
               self.walletMap[wltID].syncWithBlockchain()
               newLedgerSize = len(self.walletMap[wltID].getTxLedger())
               didAffectUs = (prevLedgerSize != newLedgerSize)
         
            print 'New Block! :', self.latestBlockNum
            if didAffectUs:
               print 'New Block contained a transaction relevant to us!'
               self.walletListChanged()
            self.NetworkingFactory.purgeMemoryPool()
            self.createCombinedLedger()
      

      #for wltID, wlt in self.walletMap.iteritems():
      for idx,wltID in enumerate(self.walletIDList):
         # Update wallet balances
         self.walletBalances[idx] = self.walletMap[wltID].getBalance()
         self.walletMap[wltID].checkWalletLockTimeout()

      for func in self.extraHeartbeatFunctions:
         func()

      reactor.callLater(nextBeatSec, self.Heartbeat)
      

   #############################################################################
   def closeEvent(self, event):
      '''
      Seriously, I could not figure out how to exit gracefully, so the next
      best thing is to just hard-kill the app with a sys.exit() call.  Oh well... 
      '''
      self.NetworkingFactory.saveMemoryPool()
      from twisted.internet import reactor
      print 'Attempting to close the main window!'
      reactor.stop()
      sys.exit()
      event.accept()
      
      

   


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


   armorymode = ARMORYMODE.WITH_BLOCKCHAIN
   #try:
      #import urllib2
      #response=urllib2.urlopen('http://google.com',timeout=1)
   #except (ImportError, urllib2.URLError):
      #dlg = DlgGetArmoryModeSelection(self,self)
      #if dlg.exec_():
         #if dlg.wltonly:
            #armorymode = ARMORYMODE.WALLET_ONLY
         

   app = QApplication(sys.argv)
   import qt4reactor
   qt4reactor.install()


   if armorymode == ARMORYMODE.WITH_BLOCKCHAIN:
      form = ArmoryMainWindow(settingsPath=options.settingsPath)
      form.show()
   elif armorymode == ARMORYMODE.WALLET_ONLY:
      form = ArmoryWalletMgmtWindow(settingsPath=options.settingsPath)
      form.show()



   # TODO:  How the hell do I get it to shutdown when the MainWindow is closed?
   from twisted.internet import reactor
   def endProgram():
      app.quit()
      sys.exit()
   app.connect(form, SIGNAL("lastWindowClosed()"), endProgram)
   reactor.addSystemEventTrigger('before', 'shutdown', endProgram)
   app.setQuitOnLastWindowClosed(True)
   reactor.run()



"""
We'll mess with threading, later
class BlockchainLoader(threading.Thread):
   def __init__(self, finishedCallback):
      self.finishedCallback = finishedCallback

   def run(self):
      BDM_LoadBlockchainFile()
      self.finishedCallback()
"""


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
