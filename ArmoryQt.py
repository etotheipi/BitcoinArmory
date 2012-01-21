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

      self.haveBlkFile = os.path.exists(BLK0001_PATH)

      
      self.settingsPath = settingsPath
      self.loadWalletsAndSettings()
      self.setupNetworking()

      self.extraHeartbeatFunctions = []

      self.lblArmoryStatus = QRichLabel('<font color=#550000><i>Offline</i></font>', \
                                                                          doWrap=False)
      self.statusBar().insertPermanentWidget(0, self.lblArmoryStatus)

      # Keep a persistent printer object for paper backups
      self.printer = QPrinter(QPrinter.HighResolution)
      self.printer.setPageSize(QPrinter.Letter)

      self.lblLogoIcon = QLabel()
      #self.lblLogoIcon.setPixmap(QPixmap('img/armory_logo_64x64.png'))

      if USE_TESTNET:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [TESTNET]')
         self.iconfile = 'img/armory_icon_green_32x32.png'
         self.lblLogoIcon.setPixmap(QPixmap('img/armory_logo_green_h72.png'))
      else:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [MAIN NETWORK]')
         self.iconfile = 'img/armory_icon_32x32.png'
         self.lblLogoIcon.setPixmap(QPixmap('img/armory_logo_h72.png'))
      self.setWindowIcon(QIcon(self.iconfile))
      self.lblLogoIcon.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      #self.setWindowIcon(QIcon('img/armory_logo_32x32.png'))

      # Table for all the wallets
      self.walletModel = AllWalletsDispModel(self)
      self.walletsView  = QTableView()

      # For some reason, I can't get an acceptable value that works for both
      if OS_WINDOWS:
         w,h = tightSizeNChar(self.walletsView, 100)
      else:
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
      self.ledgerView.hideColumn(LEDGERCOLS.DoubleSpend)

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
      lblAvail = QLabel("<b>Available Wallets:</b>")
      viewHeader = makeLayoutFrame('Horiz', [lblAvail, 'Stretch', btnAddWallet, btnImportWlt])
      wltFrame = QFrame()
      wltFrame.setFrameStyle(QFrame.Box|QFrame.Sunken)
      wltLayout = QGridLayout()
      wltLayout.addWidget(viewHeader, 0,0, 1,3)
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

      self.lblSpendFunds  = QLabel()
      self.lblSpendFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

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
      btnOfflineTx = QPushButton("Offline Transactions")
      btnDevTools  = QPushButton("Developer Tools")
 

      self.connect(btnWltProps, SIGNAL('clicked()'), self.execDlgWalletDetails)
      self.connect(btnRecvBtc,  SIGNAL('clicked()'), self.clickReceiveCoins)
      self.connect(btnSendBtc,  SIGNAL('clicked()'), self.clickSendBitcoins)
      self.connect(btnDevTools, SIGNAL('clicked()'), self.openToolsDlg)
      self.connect(btnOfflineTx,SIGNAL('clicked()'), self.execOfflineTx)
      # QTableView.selectedIndexes to get the selection

      layout = QVBoxLayout()
      layout.addWidget(btnSendBtc)
      layout.addWidget(btnRecvBtc)
      layout.addWidget(btnWltProps)
      
      if self.usermode in (USERMODE.Advanced, USERMODE.Developer):
         layout.addWidget(btnOfflineTx)
      if self.usermode==USERMODE.Developer:
         layout.addWidget(btnDevTools)
      layout.addStretch()
      btnFrame = QFrame()
      btnFrame.setLayout(layout)

      
      lblInfo = QLabel('Armory Version %s (alpha) / %s User Mode' % \
               (getVersionString(BTCARMORY_VERSION), UserModeStr(self.usermode)))
      lblInfo.setFont(GETFONT('var',10))
      lblInfo.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      layout.addWidget(lblInfo)
               
      
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

      if self.haveBlkFile:
         self.loadBlockchain()
      self.ledgerTable = self.convertLedgerToTable(self.combinedLedger)
      self.ledgerModel = LedgerDispModelSimple(self.ledgerTable, self, self)
      self.ledgerView.setModel(self.ledgerModel)
      from twisted.internet import reactor

      ##########################################################################
      # Set up menu and actions
      MENUS = enum('File', 'Wallet', 'User', "Tools", "Network")
      self.menu = self.menuBar()
      self.menusList = []
      self.menusList.append( self.menu.addMenu('&File') )
      self.menusList.append( self.menu.addMenu('&Wallet') )
      self.menusList.append( self.menu.addMenu('&User') )
      self.menusList.append( self.menu.addMenu('&Tools') )
      self.menusList.append( self.menu.addMenu('&Network') )


      actCloseApp = self.createAction('&Quit Armory', self.closeEvent)
      self.menusList[MENUS.File].addAction(actCloseApp)

      
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


      # Network stuff (for now, temporary 
      def memClear(): self.memoryPoolAction('clear')
      def memPurge(): self.memoryPoolAction('purge')
      def memPrint(): self.memoryPoolAction('print')
      actEnableMemPool = self.createAction('&Enable Zero-Conf', self.enableMemoryPool, True)
      actClearMemPool = self.createAction('&Clear',  memClear)
      actPrintMemPool = self.createAction('&Print',  memPrint)
      actPurgeMemPool = self.createAction('&Purge',  memPurge)

      if self.settings.getSettingOrSetDefault('ZeroConfEnable', False):
         actEnableMemPool.setChecked(True)
         

      self.menusList[MENUS.Network].addAction(actEnableMemPool)
      self.menusList[MENUS.Network].addAction(actClearMemPool)
      self.menusList[MENUS.Network].addAction(actPrintMemPool)
      self.menusList[MENUS.Network].addAction(actPurgeMemPool)

      self.NetworkingFactory.purgeMemoryPool()

      currmode = self.settings.getSettingOrSetDefault('User_Mode', 'Advanced')
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

      

      reactor.callLater(0.1,  self.execIntroDialog)

      reactor.callLater(5, self.Heartbeat)



   #############################################################################
   def execOfflineTx(self):
      dlgSelect = DlgOfflineSelect(self, self)
      if dlgSelect.exec_():

         # If we got here, one of three buttons was clicked.
         if dlgSelect.do_create:
            selectWlt = []
            for wltID in self.walletIDList:
               if self.walletMap[wltID].watchingOnly:
                  selectWlt.append(wltID)
            dlg = DlgWalletSelect(self, self, 'Wallet for Offline Transaction (watching-only list)', \
                                                      wltIDList=selectWlt)
            if not dlg.exec_():
               return
            else:
               wltID = dlg.selectedID 
               wlt = self.walletMap[wltID]
               dlgSend = DlgSendBitcoins(wlt, self, self)
               dlgSend.exec_()
               return

         elif dlgSelect.do_review:
            dlg = DlgReviewOfflineTx(self,self)
            dlg.exec_()

         elif dlgSelect.do_broadc:
            dlg = DlgReviewOfflineTx(self,self)
            dlg.exec_()


   #############################################################################
   def memoryPoolAction(self, opString):
      if opString.lower()=='clear':
         self.NetworkingFactory.zeroConfTx.clear()
         self.NetworkingFactory.zeroConfTxTime.clear()
         self.NetworkingFactory.saveMemoryPool()
      elif opString.lower()=='print':
         for k,v in self.NetworkingFactory.zeroConfTx.iteritems():
            print binary_to_hex(k), 
            print ' '.join([ coin2str(txout.getValue()) for txout in v.outputs])
      elif opString.lower()=='purge':
         print 'Before purging:'
         self.memoryPoolAction('Print')
         self.NetworkingFactory.purgeMemoryPool()
         print 'After purging:'
         self.memoryPoolAction('Print')

   def enableMemoryPool(self, doEnable):
      if doEnable: 
         QMessageBox.information(self,'Zero-Confirmation Transactions', \
         'Zero-confirmation transactions in Armory are not handled well.  A short-'
         'term solution has been implemented, but it usually results in extra, '
         'ghost transactions appearing in the wallet ledger.  Please do not consider '
         'any such transactions to be truth, until you see them with 1 or more '
         'confirmations. \n\n'
         'You can use the "Network" menu to clear or purge the memory pool if '
         'too many transactions appear. \n\n'
         'This feature will be fixed in the following release.', QMessageBox.Ok)
         self.settings.set('ZeroConfEnable', True)
      else:
         self.settings.set('ZeroConfEnable', False)

   #############################################################################
   def sizeHint(self):
      return QSize(1000, 650)

   #############################################################################
   def openToolsDlg(self):
      QMessageBox.information(self, 'No Tools Yet!', \
         'The developer tools are not available yet, but will be added '
         'soon.  Regardless, developer-mode still offers lots of '
         'extra information and functionality that is not available in '
         'Standard or Advanced mode.', QMessageBox.Ok)



   #############################################################################
   def execIntroDialog(self):
      if not self.settings.getSettingOrSetDefault('DNAA_IntroDialog', False):
         dlg = DlgIntroMessage(self, self)
         result = dlg.exec_()

         if dlg.chkDnaaIntroDlg.isChecked():
            self.settings.set('DNAA_IntroDialog', True)

         if dlg.requestCreate:
            self.createNewWallet(initLabel='Primary Wallet')
            
      
   
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

      internetAvail = False
      satoshiAvail  = False


      # Check for Satoshi-client connection
      import socket
      s = socket.socket()
      try:
         s.connect(('127.0.0.1', BITCOIN_PORT))
         s.close()
         self.satoshiAvail = True
      except:
         self.satoshiAvail = False
         


      # Check general internet connection
      try:
         import urllib2
         response=urllib2.urlopen('http://google.com', timeout=1)
         self.internetAvail = True
      except ImportError:
         print 'No module urllib2 -- cannot determine if internet is available'
      except urllib2.URLError:
         # In the extremely rare case that google might be down...
         try:
            response=urllib2.urlopen('http://microsoft.com', timeout=1)
         except urllib2.URLError:
            self.internetAvail = False
         
      self.isOnline = (self.internetAvail and self.satoshiAvail)

      if not self.isOnline:
         dlg = DlgBadConnection(self.internetAvail, self.satoshiAvail, self)
         dlg.exec_()
         self.NetworkingFactory = FakeClientFactory()
         return
   


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




   #############################################################################
   def loadWalletsAndSettings(self):
      self.settings = SettingsFile(self.settingsPath)

      self.settings.getSettingOrSetDefault('First_Load',         True)
      self.settings.getSettingOrSetDefault('Load_Count',         0)
      self.settings.getSettingOrSetDefault('User_Mode',          'Advanced')
      self.settings.getSettingOrSetDefault('UnlockTimeout',      10)
      self.settings.getSettingOrSetDefault('DNAA_UnlockTimeout', False)
      self.settings.getSettingOrSetDefault('ZeroConfEnable',     False)


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
   def getFileSave(self, title='Save Wallet File', \
                         ffilter=['Wallet files (*.wallet)'], \
                         defaultFilename=None):
      startPath = self.settings.get('LastDirectory')
      if len(startPath)==0 or not os.path.exists(startPath):
         startPath = ARMORY_HOME_DIR

      if not defaultFilename==None:
         startPath = os.path.join(startPath, defaultFilename)
      
      types = ffilter
      types.append('All files (*)')
      typesStr = ';; '.join(types)
      fullPath = unicode(QFileDialog.getSaveFileName(self, title, startPath, typesStr))
      

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

      self.settings.set('LastDirectory', os.path.split(fullPath)[0])
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
         TheBDM.enableZeroConf(os.path.join(ARMORY_HOME_DIR,'mempool.bin'))

         self.statusBar().showMessage('Syncing wallets with blockchain...')
         print 'Syncing wallets with blockchain...'
         for wltID, wlt in self.walletMap.iteritems():
            print 'Syncing', wltID
            self.walletMap[wltID].setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
            self.walletMap[wltID].syncWithBlockchain()
            TheBDM.rebuildZeroConfLedgers(self.walletMap[wltID]

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

         if self.isOnline:
            self.lblArmoryStatus.setText(\
               '<font color="green">Connected (%s blocks)</font> ' % self.latestBlockNum)
         self.blkReceived  = self.settings.getSettingOrSetDefault('LastBlkRecvTime', 0)
      else:
         self.statusBar().showMessage('! Blockchain loading failed !', 10000)


      # This will force the table to refresh with new data
      self.walletModel.reset()
         

   

   #############################################################################
   def createCombinedLedger(self, wltIDList=None, withZeroConf=True):
      """
      Create a ledger to display on the main screen, that consists of ledger
      entries of any SUBSET of available wallets.
      """
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
               wltIDList = listOffline + listCrypt + listPlain
            elif currIdx==1:
               wltIDList = listOffline
            elif currIdx==2:
               wltIDList = listWatching
            elif currIdx==3:
               wltIDList = self.walletIDList
            else:
               pass
               #raise WalletExistsError, 'Bad combo-box selection: ' + str(currIdx)
               

      self.combinedLedger = []
      if wltIDList==None:
         return

      for wltID in wltIDList:
         wlt = self.walletMap[wltID]
         index = self.walletIndices[wltID]
         self.walletLedgers[index] = []

         # Add the LedgerEntries from the blockchain
         for ledgList in [wlt.getTxLedger(), wlt.getZeroConfLedger()]:
            self.walletLedgers[index].extend([[wltID, le] for le in ledgList])
            self.combinedLedger.extend(id_le_pairs)


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
         if not txref:
            return (0, 0)
         if txref.getNumTxOut()==1:
            return (txref.getTxOutRef(0).getValue(), -1)
         maxChainIndex = -5
         txOutChangeVal = 0
         txOutIndex = -1
         valSum = 0
         for i in range(txref.getNumTxOut()):
            valSum += txref.getTxOutRef(i).getValue()
            addr160 = txref.getTxOutRef(i).getRecipientAddr()
            addr    = wlt.getAddrByHash160(addr160)
            if addr and addr.chainIndex > maxChainIndex:
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
         removeFee = self.settings.getSettingOrSetDefault('DispRmFee', False)
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
            txtime = 0
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

         # Tx was invalidated!  (double=spend!)
         row.append( not le.isValid())

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
      self.comboWalletSelect.addItem( 'My Wallets'        )
      self.comboWalletSelect.addItem( 'Offline Wallets'   )
      self.comboWalletSelect.addItem( 'Other\'s wallets'  )
      self.comboWalletSelect.addItem( 'All Wallets'       )
      for wltID in self.walletIDList:
         self.comboWalletSelect.addItem( self.walletMap[wltID].labelName )
      self.comboWalletSelect.insertSeparator(4)
      self.comboWalletSelect.insertSeparator(4)
      

   #############################################################################
   def execDlgWalletDetails(self, index=None):
      if index==None:
         index = self.walletsView.selectedIndexes()
         if len(index)==0:
            QMessageBox.warning(self, 'Select a Wallet', \
               'Please select a wallet on the right, to see its properties.', \
               QMessageBox.Ok)
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
   def createNewWallet(self, initLabel=''):
      dlg = DlgNewWallet(self, self, initLabel=initLabel)
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

      #pprintUnspentTxOutList(utxoList)
      #print 'OutValue:', outValue
      

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
      #pytx.pprint()
      return (pytx, outValue, minFee)



   #############################################################################
   def broadcastTransaction(self, pytx, dryRun=False):
      print 'Pretty tx: ', pytx.pprint()
      print 'Raw serialize tx: ', binary_to_hex(pytx.serialize())
      if dryRun:
         #DlgDispTxInfo(pytx, None, self, self).exec_()
         return
      else:
         print 'Sending Tx,', binary_to_hex(pytx.getHash())
         self.NetworkingFactory.sendTx(pytx)
         print 'Done!'

         # Wait one sec, then send an inv to the Satoshi
         # client asking for the same tx back.  This has two great benefits:
         #   (1)  The tx was accepted by the network (it'd be dropped if it 
         #        was invalid)
         #   (2)  The memory-pool operations will be handled through existing 
         #        NetworkingFactory code.  Don't need to duplicate anything 
         #        here.
         #time.sleep(1)
         #self.checkForTxInNetwork(pytx.getHash())
      
         # TODO:  MAKE SURE THE TX WAS ACCEPTED?
         # But I'm not ready to implement this, so far now I'll just assume 
         # it worked... will be fixed in the next release
         self.NetworkingFactory.addTxToMemoryPool(pytx)
         for wltID,wlt in self.walletMap.iteritems():
            wlt.lockTxOutsOnNewTx(pytx.copy())
         self.NetworkingFactory.saveMemoryPool()

         QMessageBox.information(self, 'Broadcast Complete!', \
            'The transaction has been broadcast to the Bitcoin network.  However '
            'there is no way to know for sure whether it was accepted until you '
            'see it in the blockchain with 1+ confirmations.  Please search '
            'www.blockchain.info for the for recipient\'s address, to '
            'verify whether it was accepted or not.  '
            '\n\nAlso note: other transactions you send '
            'from this wallet may not succeed until that first confirmation is '
            'received.  Both issues are a problem with Armory that will be fixed '
            'with the next release.', QMessageBox.Ok)

   
   #############################################################################
   #def checkForTxInNetwork(self, txHash):
      #self.NetworkingFactory.sendMessage
      
            
            
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
         txHashBin = hex_to_binary(txHash)
         if self.NetworkingFactory.zeroConfTx.has_key(txHashBin):
            pytx = self.NetworkingFactory.zeroConfTx[txHashBin]
         if TheBDM.isInitialized():
            cppTx = TheBDM.getTxByHash(txHashBin)
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
         self.topTimestamp   = TheBDM.getTopBlockHeader().getTimestamp()
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
            self.blkReceived  = RightNow()
            self.settings.set('LastBlkRecvTime', self.blkReceived)
      
            if self.isOnline:
               self.lblArmoryStatus.setText(\
                  '<font color="green">Connected (%s blocks)</font> ' % self.latestBlockNum)

         nowtime = RightNow()
         blkRecvAgo  = nowtime - self.blkReceived
         blkStampAgo = nowtime - self.topTimestamp
         #if self.usermode==USERMODE.Standard:
            #self.lblArmoryStatus.setToolTip( 'Last block was received %s ago' % \
                                                         #secondsToHumanTime(blkRecvAgo))
         self.lblArmoryStatus.setToolTip('Last block timestamp is %s ago' % \
                                                   secondsToHumanTime(blkStampAgo))
      

      for idx,wltID in enumerate(self.walletIDList):
         # Update wallet balances
         self.walletBalances[idx] = self.walletMap[wltID].getBalance()
         self.walletMap[wltID].checkWalletLockTimeout()


      for func in self.extraHeartbeatFunctions:
         func()

      reactor.callLater(nextBeatSec, self.Heartbeat)
      

   #############################################################################
   def closeEvent(self, event=None):
      '''
      Seriously, I could not figure out how to exit gracefully, so the next
      best thing is to just hard-kill the app with a sys.exit() call.  Oh well... 
      '''
      #self.NetworkingFactory.saveMemoryPool()
      from twisted.internet import reactor
      print 'Attempting to close the main window!'
      try:
         reactor.stop()
      except: 
         pass
      sys.exit()
      event.accept()
      
      

   


if 1:  #__name__ == '__main__':
 
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
   parser.add_option("--testnet", dest="testnet", action="store_true", default=False,
                     help="Use the testnet protocol")
   parser.add_option("--mainnet", dest="testnet", action="store_false", default=False,
                     help="Use the testnet protocol")

   (options, args) = parser.parse_args()



   app = QApplication(sys.argv)
   import qt4reactor
   qt4reactor.install()


      
   pixLogo = QPixmap('img/splashlogo.png')
   SPLASH = QSplashScreen(pixLogo)
   SPLASH.setMask(pixLogo.mask())
   SPLASH.show()
   app.processEvents()

   form = ArmoryMainWindow(settingsPath=options.settingsPath)
   form.show()


   SPLASH.finish(form)

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
