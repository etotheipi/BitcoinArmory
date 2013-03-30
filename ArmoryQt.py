################################################################################
#
# Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
#
# Project:    Armory              
# Author:     Alan Reiner
# Website:    www.bitcoinarmory.com
# Orig Date:  20 November, 2011
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
import platform
import traceback
import socket
import subprocess
from datetime import datetime

# PyQt4 Imports
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# Over 15,000 lines of python to help us out
from armoryengine import *
from armorymodels import *
from qtdialogs    import *
from qtdefines    import *
from armorycolors import Colors, htmlColor, QAPP

import qrc_img_resources

# All the twisted/networking functionality
from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet.defer import Deferred


if OS_WINDOWS:
   from _winreg import *


class ArmoryMainWindow(QMainWindow):
   """ The primary Armory window """

   #############################################################################
   def __init__(self, parent=None):
      super(ArmoryMainWindow, self).__init__(parent)

      TimerStart('MainWindowInit')

      # Load the settings file
      self.settingsPath = CLI_OPTIONS.settingsPath
      self.settings = SettingsFile(self.settingsPath)

      # SETUP THE WINDOWS DECORATIONS
      self.lblLogoIcon = QLabel()
      if USE_TESTNET:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [TESTNET]')
         self.iconfile = ':/armory_icon_green_32x32.png'
         self.lblLogoIcon.setPixmap(QPixmap(':/armory_logo_green_h56.png'))
         if Colors.isDarkBkgd:
            self.lblLogoIcon.setPixmap(QPixmap(':/armory_logo_white_text_green_h56.png'))
      else:
         self.setWindowTitle('Armory - Bitcoin Wallet Management')
         self.iconfile = ':/armory_icon_32x32.png'
         self.lblLogoIcon.setPixmap(QPixmap(':/armory_logo_h56.png'))
         if Colors.isDarkBkgd:
            self.lblLogoIcon.setPixmap(QPixmap(':/armory_logo_white_text_h56.png'))
      self.setWindowIcon(QIcon(self.iconfile))
      self.lblLogoIcon.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      self.netMode     = NETWORKMODE.Offline
      self.abortLoad   = False
      self.memPoolInit = False
      self.dirtyLastTime = False
      self.needUpdateAfterScan = True
      self.sweepAfterScanList = []
      self.newWalletList = []
      self.newZeroConfSinceLastUpdate = []
      self.lastBDMState = ['Uninitialized', None]
      self.lastSDMState = 'Uninitialized'
      self.detectNotSyncQ = [0,0,0,0,0]
      self.noSyncWarnYet = True
      self.doHardReset = False
      self.doShutdown = False
      self.downloadDict = {}
      self.latestVerSatoshi = None
      self.latestVerArmory = None


      # We want to determine whether the user just upgraded to a new version
      self.firstLoadNewVersion = False
      currVerStr = 'v'+getVersionString(BTCARMORY_VERSION)
      if self.settings.hasSetting('LastVersionLoad'):
         lastVerStr = self.settings.get('LastVersionLoad')
         if not lastVerStr==currVerStr:
            self.firstLoadNewVersion = True
      self.settings.set('LastVersionLoad', currVerStr)

      # Because dynamically retrieving addresses for querying transaction 
      # comments can be so slow, I use this txAddrMap to cache the mappings
      # between tx's and addresses relevant to our wallets.  It really only 
      # matters for massive tx with hundreds of outputs -- but such tx do 
      # exist and this is needed to accommodate wallets with lots of them.
      self.txAddrMap = {}

      
      self.loadWalletsAndSettings()

      eulaAgreed = self.getSettingOrSetDefault('Agreed_to_EULA', False)
      if not eulaAgreed:
         DlgEULA(self,self).exec_()


      if not self.abortLoad:
         self.setupNetworking()

      # setupNetworking may have set this flag if something went wrong
      if self.abortLoad:
         LOGWARN('Armory startup was aborted.  Closing.')
         os._exit(0)

      # We need to query this once at the beginning, to avoid having
      # strange behavior if the user changes the setting but hasn't
      # restarted yet...
      self.doManageSatoshi = \
            self.getSettingOrSetDefault('ManageSatoshi', not OS_MACOSX)


      # If we're going into online mode, start loading blockchain
      if self.doManageSatoshi:
         self.startBitcoindIfNecessary()
      else:
         self.loadBlockchainIfNecessary()

      # Setup system tray and register "bitcoin:" URLs with the OS
      self.setupSystemTray()
      self.setupUriRegistration()


      self.extraHeartbeatSpecial = []
      self.extraHeartbeatOnline = []
      self.extraHeartbeatAlways = []

      self.lblArmoryStatus = QRichLabel('<font color=%s>Offline</font> ' % 
                                      htmlColor('TextWarn'), doWrap=False)
      self.statusBar().insertPermanentWidget(0, self.lblArmoryStatus)

      # Keep a persistent printer object for paper backups
      self.printer = QPrinter(QPrinter.HighResolution)
      self.printer.setPageSize(QPrinter.Letter)


      # Table for all the wallets
      self.walletModel = AllWalletsDispModel(self)
      self.walletsView  = QTableView()

      # For some reason, I can't get an acceptable value that works for both
      if OS_WINDOWS:
         w,h = tightSizeNChar(self.walletsView, 80)
      else:
         w,h = tightSizeNChar(self.walletsView, 55)
      viewWidth  = 1.2*w
      sectionSz  = 1.5*h
      viewHeight = 4.4*sectionSz
      
      self.walletsView.setModel(self.walletModel)
      self.walletsView.setSelectionBehavior(QTableView.SelectRows)
      self.walletsView.setSelectionMode(QTableView.SingleSelection)
      self.walletsView.verticalHeader().setDefaultSectionSize(sectionSz)
      self.walletsView.setMinimumSize(viewWidth, 4.4*sectionSz)


      if self.usermode == USERMODE.Standard:
         initialColResize(self.walletsView, [0, 0.35, 0.2, 0.2])
         self.walletsView.hideColumn(0)
      else:
         initialColResize(self.walletsView, [0.15, 0.30, 0.2, 0.20])


      self.connect(self.walletsView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.execDlgWalletDetails)
                  

      w,h = tightSizeNChar(GETFONT('var'), 100)
      viewWidth = 1.2*w
      if OS_WINDOWS:
         sectionSz = 1.3*h
         viewHeight = 6.0*sectionSz
      else:
         sectionSz = 1.3*h
         viewHeight = 6.4*sectionSz


      # Prepare for tableView slices (i.e. "Showing 1 to 100 of 382", etc)
      self.numShowOpts = [100,250,500,1000,'All']
      self.sortLedgOrder = Qt.AscendingOrder
      self.sortLedgCol = 0
      self.currLedgMin = 1
      self.currLedgMax = 100
      self.currLedgWidth = 100

      # Table to display ledger/activity
      self.ledgerTable = []
      self.ledgerModel = LedgerDispModelSimple(self.ledgerTable, self, self)

      #self.ledgerProxy = LedgerDispSortProxy()
      #self.ledgerProxy.setSourceModel(self.ledgerModel)
      #self.ledgerProxy.setDynamicSortFilter(False)

      self.ledgerView  = QTableView()

      self.ledgerView.setModel(self.ledgerModel)
      self.ledgerView.setSortingEnabled(True)
      self.ledgerView.setItemDelegate(LedgerDispDelegate(self))
      self.ledgerView.setSelectionBehavior(QTableView.SelectRows)
      self.ledgerView.setSelectionMode(QTableView.SingleSelection)

      self.ledgerView.verticalHeader().setDefaultSectionSize(sectionSz)
      self.ledgerView.verticalHeader().hide()
      self.ledgerView.horizontalHeader().setResizeMode(0, QHeaderView.Fixed)
      self.ledgerView.horizontalHeader().setResizeMode(3, QHeaderView.Fixed)

      self.ledgerView.hideColumn(LEDGERCOLS.isOther)
      self.ledgerView.hideColumn(LEDGERCOLS.UnixTime)
      self.ledgerView.hideColumn(LEDGERCOLS.WltID)
      self.ledgerView.hideColumn(LEDGERCOLS.TxHash)
      self.ledgerView.hideColumn(LEDGERCOLS.isCoinbase)
      self.ledgerView.hideColumn(LEDGERCOLS.toSelf)
      self.ledgerView.hideColumn(LEDGERCOLS.DoubleSpend)


      dateWidth    = tightSizeStr(self.ledgerView, '_9999-Dec-99 99:99pm__')[0]
      nameWidth    = tightSizeStr(self.ledgerView, '9'*32)[0]
      cWidth = 20 # num-confirm icon width
      tWidth = 72 # date icon width
      initialColResize(self.ledgerView, [cWidth, 0, dateWidth, tWidth, 0.30, 0.40, 0.3])
      
      self.connect(self.ledgerView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.dblClickLedger)

      self.ledgerView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.ledgerView.customContextMenuRequested.connect(self.showContextMenuLedger)

      btnAddWallet = QPushButton("Create New Wallet")
      btnImportWlt = QPushButton("Import Wallet")
      self.connect(btnAddWallet, SIGNAL('clicked()'), self.createNewWallet)
      self.connect(btnImportWlt, SIGNAL('clicked()'), self.execImportWallet)

      # Put the Wallet info into it's own little box
      lblAvail = QLabel("<b>Available Wallets:</b>")
      viewHeader = makeLayoutFrame('Horiz', [lblAvail, 'Stretch', btnAddWallet, btnImportWlt])
      wltFrame = QFrame()
      wltFrame.setFrameStyle(QFrame.Box|QFrame.Sunken)
      wltLayout = QGridLayout()
      wltLayout.addWidget(viewHeader, 0,0, 1,3)
      wltLayout.addWidget(self.walletsView, 1,0, 1,3)
      wltFrame.setLayout(wltLayout)



      # Make the bottom 2/3 a tabwidget
      self.mainDisplayTabs = QTabWidget()

      # Put the labels into scroll areas just in case window size is small.
      self.tabDashboard = QWidget()

      

      self.SetupDashboard()
      


      # Combo box to filter ledger display
      self.comboWltSelect = QComboBox()
      self.populateLedgerComboBox()
      self.connect(self.ledgerView.horizontalHeader(), \
                   SIGNAL('sortIndicatorChanged(int,Qt::SortOrder)'), \
                   self.changeLedgerSorting)


      # Create the new ledger twice:  can't update the ledger up/down
      # widgets until we know how many ledger entries there are from 
      # the first call
      def createLedg():
         self.createCombinedLedger() 
         if self.frmLedgUpDown.isVisible():
            self.changeNumShow() 
      self.connect(self.comboWltSelect, SIGNAL('activated(int)'), createLedg)

      self.lblTot  = QRichLabel('<b>Maximum Funds:</b>', doWrap=False); 
      self.lblSpd  = QRichLabel('<b>Spendable Funds:</b>', doWrap=False); 
      self.lblUcn  = QRichLabel('<b>Unconfirmed:</b>', doWrap=False); 

      self.lblTotalFunds  = QRichLabel('-'*12, doWrap=False)
      self.lblSpendFunds  = QRichLabel('-'*12, doWrap=False)
      self.lblUnconfFunds = QRichLabel('-'*12, doWrap=False)
      self.lblTotalFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.lblSpendFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.lblUnconfFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

      self.lblTot.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.lblSpd.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.lblUcn.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

      self.lblBTC1 = QRichLabel('<b>BTC</b>', doWrap=False)
      self.lblBTC2 = QRichLabel('<b>BTC</b>', doWrap=False)
      self.lblBTC3 = QRichLabel('<b>BTC</b>', doWrap=False)
      self.ttipTot = createToolTipObject( \
            'Funds if all current transactions are confirmed.  '
            'Value appears gray when it is the same as your spendable funds.')
      self.ttipSpd = createToolTipObject( 'Funds that can be spent <i>right now</i>')
      self.ttipUcn = createToolTipObject( \
            'Funds that have less than 6 confirmations, and thus should not '
            'be considered <i>yours</i>, yet.')

      frmTotals = QFrame()
      frmTotals.setFrameStyle(STYLE_NONE)
      frmTotalsLayout = QGridLayout()
      frmTotalsLayout.addWidget(self.lblTot, 0,0)
      frmTotalsLayout.addWidget(self.lblSpd, 1,0)
      frmTotalsLayout.addWidget(self.lblUcn, 2,0)

      frmTotalsLayout.addWidget(self.lblTotalFunds,  0,1)
      frmTotalsLayout.addWidget(self.lblSpendFunds,  1,1)
      frmTotalsLayout.addWidget(self.lblUnconfFunds, 2,1)

      frmTotalsLayout.addWidget(self.lblBTC1, 0,2)
      frmTotalsLayout.addWidget(self.lblBTC2, 1,2)
      frmTotalsLayout.addWidget(self.lblBTC3, 2,2)

      frmTotalsLayout.addWidget(self.ttipTot, 0,3)
      frmTotalsLayout.addWidget(self.ttipSpd, 1,3)
      frmTotalsLayout.addWidget(self.ttipUcn, 2,3)

      frmTotals.setLayout(frmTotalsLayout)



      # Will fill this in when ledgers are created & combined
      self.lblLedgShowing = QRichLabel('Showing:', hAlign=Qt.AlignHCenter)
      self.lblLedgRange   = QRichLabel('', hAlign=Qt.AlignHCenter)
      self.lblLedgTotal   = QRichLabel('', hAlign=Qt.AlignHCenter)
      self.comboNumShow = QComboBox()
      for s in self.numShowOpts:
         self.comboNumShow.addItem( str(s) )
      self.comboNumShow.setCurrentIndex(0)
      self.comboNumShow.setMaximumWidth( tightSizeStr(self, '_9999_')[0]+25 )


      self.btnLedgUp = QLabelButton('')
      self.btnLedgUp.setMaximumHeight(20)
      self.btnLedgUp.setPixmap(QPixmap(':/scroll_up_18.png'))
      self.btnLedgUp.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
      self.btnLedgUp.setVisible(False)

      self.btnLedgDn = QLabelButton('')
      self.btnLedgDn.setMaximumHeight(20)
      self.btnLedgDn.setPixmap(QPixmap(':/scroll_down_18.png'))
      self.btnLedgDn.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)


      self.connect(self.comboNumShow, SIGNAL('activated(int)'), self.changeNumShow)
      self.connect(self.btnLedgUp,    SIGNAL('clicked()'),      self.clickLedgUp)
      self.connect(self.btnLedgDn,    SIGNAL('clicked()'),      self.clickLedgDn)

      frmFilter = makeVertFrame([QLabel('Filter:'), self.comboWltSelect, 'Stretch'])

      self.frmLedgUpDown = QFrame()
      layoutUpDown = QGridLayout()
      layoutUpDown.addWidget(self.lblLedgShowing,0,0)
      layoutUpDown.addWidget(self.lblLedgRange,  1,0)
      layoutUpDown.addWidget(self.lblLedgTotal,  2,0)
      layoutUpDown.addWidget(self.btnLedgUp,     0,1)
      layoutUpDown.addWidget(self.comboNumShow,  1,1)
      layoutUpDown.addWidget(self.btnLedgDn,     2,1)
      layoutUpDown.setVerticalSpacing(2)
      self.frmLedgUpDown.setLayout(layoutUpDown)
      self.frmLedgUpDown.setFrameStyle(STYLE_SUNKEN)
      

      frmLower = makeHorizFrame([ frmFilter, \
                                 'Stretch', \
                                 self.frmLedgUpDown, \
                                 'Stretch', \
                                 frmTotals])

      # Now add the ledger to the bottom of the window
      ledgFrame = QFrame()
      ledgFrame.setFrameStyle(QFrame.Box|QFrame.Sunken)
      ledgLayout = QGridLayout()
      #ledgLayout.addWidget(QLabel("<b>Ledger</b>:"),  0,0)
      ledgLayout.addWidget(self.ledgerView,           1,0)
      ledgLayout.addWidget(frmLower,                  2,0)
      ledgLayout.setRowStretch(0, 0)
      ledgLayout.setRowStretch(1, 1)
      ledgLayout.setRowStretch(2, 0)
      ledgFrame.setLayout(ledgLayout)

      self.tabActivity = QWidget()
      self.tabActivity.setLayout(ledgLayout)

      # Add the available tabs to the main tab widget
      self.MAINTABS  = enum('Dashboard','Transactions')

      self.mainDisplayTabs.addTab(self.tabDashboard, 'Dashboard')
      self.mainDisplayTabs.addTab(self.tabActivity,  'Transactions')


      btnSendBtc   = QPushButton("Send Bitcoins")
      btnRecvBtc   = QPushButton("Receive Bitcoins")
      btnWltProps  = QPushButton("Wallet Properties")
      btnOfflineTx = QPushButton("Offline Transactions")
 

      self.connect(btnWltProps, SIGNAL('clicked()'), self.execDlgWalletDetails)
      self.connect(btnRecvBtc,  SIGNAL('clicked()'), self.clickReceiveCoins)
      self.connect(btnSendBtc,  SIGNAL('clicked()'), self.clickSendBitcoins)
      self.connect(btnOfflineTx,SIGNAL('clicked()'), self.execOfflineTx)

      verStr = 'Armory %s-beta / %s User' % (getVersionString(BTCARMORY_VERSION), \
                                              UserModeStr(self.usermode))
      lblInfo = QRichLabel(verStr, doWrap=False)
      lblInfo.setFont(GETFONT('var',10))
      lblInfo.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      logoBtnFrame = []
      logoBtnFrame.append(self.lblLogoIcon)
      logoBtnFrame.append(btnSendBtc)
      logoBtnFrame.append(btnRecvBtc)
      logoBtnFrame.append(btnWltProps)
      if self.usermode in (USERMODE.Advanced, USERMODE.Expert):
         logoBtnFrame.append(btnOfflineTx)
      logoBtnFrame.append(lblInfo)
      logoBtnFrame.append('Stretch')

      btnFrame = makeVertFrame(logoBtnFrame, STYLE_SUNKEN)
      logoWidth=275
      btnFrame.sizeHint = lambda: QSize(logoWidth*1.0, 10)
      btnFrame.setMaximumWidth(logoWidth*1.1)
      btnFrame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
      
      layout = QGridLayout()
      layout.addWidget(btnFrame,          0, 0, 1, 1)
      layout.addWidget(wltFrame,          0, 1, 1, 1)
      layout.addWidget(self.mainDisplayTabs,  1, 0, 1, 2)
      layout.setRowStretch(0, 1)
      layout.setRowStretch(1, 5)

      # Attach the layout to the frame that will become the central widget
      mainFrame = QFrame()
      mainFrame.setLayout(layout)
      self.setCentralWidget(mainFrame)
      self.setMinimumSize(750,500)

      # Start the user at the dashboard
      self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Dashboard)

      from twisted.internet import reactor
      # Show the appropriate information on the dashboard
      self.setDashboardDetails(INIT=True)


      ##########################################################################
      # Set up menu and actions
      #MENUS = enum('File', 'Wallet', 'User', "Tools", "Network")
      MENUS = enum('File', 'User', 'Tools', 'Addresses', 'Wallets', 'Help')
      self.menu = self.menuBar()
      self.menusList = []
      self.menusList.append( self.menu.addMenu('&File') )
      self.menusList.append( self.menu.addMenu('&User') )
      self.menusList.append( self.menu.addMenu('&Tools') )
      self.menusList.append( self.menu.addMenu('&Addresses') )
      self.menusList.append( self.menu.addMenu('&Wallets') )
      self.menusList.append( self.menu.addMenu('&Help') )
      #self.menusList.append( self.menu.addMenu('&Network') )

      
      def exportTx():
         if not TheBDM.getBDMState()=='BlockchainReady':
            QMessageBox.warning(self, 'Transactions Unavailable', \
               'Transaction history cannot be collected until Armory is '
               'in online mode.  Please try again when Armory is online. ',
               QMessageBox.Ok)
            return
         else:
            DlgExportTxHistory(self,self).exec_()
            

      actExportTx    = self.createAction('&Export Transactions', exportTx)
      actSettings    = self.createAction('&Settings', self.openSettings)
      actMinimApp    = self.createAction('&Minimize Armory', self.minimizeArmory)
      actExportLog   = self.createAction('Export &Log File', self.exportLogFile)
      actCloseApp    = self.createAction('&Quit Armory', self.closeForReal)
      self.menusList[MENUS.File].addAction(actExportTx)
      self.menusList[MENUS.File].addAction(actSettings)
      self.menusList[MENUS.File].addAction(actMinimApp)
      self.menusList[MENUS.File].addAction(actExportLog)
      self.menusList[MENUS.File].addAction(actCloseApp)

      
      def chngStd(b): 
         if b: self.setUserMode(USERMODE.Standard)
      def chngAdv(b): 
         if b: self.setUserMode(USERMODE.Advanced)
      def chngDev(b): 
         if b: self.setUserMode(USERMODE.Expert)

      modeActGrp = QActionGroup(self)
      actSetModeStd = self.createAction('&Standard',  chngStd, True)
      actSetModeAdv = self.createAction('&Advanced',  chngAdv, True)
      actSetModeDev = self.createAction('&Expert', chngDev, True)

      modeActGrp.addAction(actSetModeStd)
      modeActGrp.addAction(actSetModeAdv)
      modeActGrp.addAction(actSetModeDev)

      self.menusList[MENUS.User].addAction(actSetModeStd)
      self.menusList[MENUS.User].addAction(actSetModeAdv)
      self.menusList[MENUS.User].addAction(actSetModeDev)



      currmode = self.getSettingOrSetDefault('User_Mode', 'Advanced')
      LOGINFO('Usermode: %s', currmode)
      self.firstModeSwitch=True
      if currmode=='Standard':
         self.usermode = USERMODE.Standard               
         actSetModeStd.setChecked(True)
      elif currmode=='Advanced':
         self.usermode = USERMODE.Advanced               
         actSetModeAdv.setChecked(True)
      elif currmode=='Expert':
         self.usermode = USERMODE.Expert               
         actSetModeDev.setChecked(True)

      actOpenSigner = self.createAction('&Message Signing', lambda: DlgECDSACalc(self,self, 0).exec_())
      actOpenTools  = self.createAction('&EC Calculator',   lambda: DlgECDSACalc(self,self, 1).exec_())
      self.menusList[MENUS.Tools].addAction(actOpenSigner)
      self.menusList[MENUS.Tools].addAction(actOpenTools)


      # Addresses
      actAddrBook   = self.createAction('View &Address Book',          self.execAddressBook)
      actSweepKey   = self.createAction('&Sweep Private Key/Address',  self.menuSelectSweepKey)
      actImportKey  = self.createAction('&Import Private Key/Address', self.menuSelectImportKey)

      self.menusList[MENUS.Addresses].addAction(actAddrBook)
      if not currmode=='Standard':
         self.menusList[MENUS.Addresses].addAction(actImportKey)
         self.menusList[MENUS.Addresses].addAction(actSweepKey)

      actCreateNew      = self.createAction('&Create New Wallet',        self.createNewWallet)
      actImportWlt      = self.createAction('&Import Armory Wallet File',      self.execGetImportWltName)
      actRestorePaper   = self.createAction('&Restore from Paper Backup', self.execRestorePaperBackup)
      #actMigrateSatoshi = self.createAction('&Migrate Bitcoin Wallet',    self.execMigrateSatoshi)
      actAddressBook    = self.createAction('View &Address Book',         self.execAddressBook)


      self.menusList[MENUS.Wallets].addAction(actCreateNew)
      self.menusList[MENUS.Wallets].addAction(actImportWlt)
      self.menusList[MENUS.Wallets].addAction(actRestorePaper)
      #self.menusList[MENUS.Wallets].addAction(actMigrateSatoshi)
      #self.menusList[MENUS.Wallets].addAction(actAddressBook)


      execAbout   = lambda: DlgHelpAbout(self).exec_()
      execVersion = lambda: self.checkForLatestVersion(wasRequested=True)
      actAboutWindow  = self.createAction('About Armory', execAbout)
      actVersionCheck = self.createAction('Armory Version...', execVersion)
      actFactoryReset = self.createAction('Revert All Settings', self.factoryReset)
      self.menusList[MENUS.Help].addAction(actAboutWindow)
      self.menusList[MENUS.Help].addAction(actVersionCheck)
      self.menusList[MENUS.Help].addAction(actFactoryReset)

      # Restore any main-window geometry saved in the settings file
      hexgeom   = self.settings.get('MainGeometry')
      hexledgsz = self.settings.get('MainLedgerCols')
      hexwltsz  = self.settings.get('MainWalletCols')
      if len(hexgeom)>0:
         geom = QByteArray.fromHex(hexgeom)
         self.restoreGeometry(geom)
      if len(hexwltsz)>0:
         restoreTableView(self.walletsView, hexwltsz)
      if len(hexledgsz)>0:
         restoreTableView(self.ledgerView, hexledgsz)
         self.ledgerView.setColumnWidth(LEDGERCOLS.NumConf, 20)
         self.ledgerView.setColumnWidth(LEDGERCOLS.TxDir,   72)


      TimerStop('MainWindowInit')

      reactor.callLater(0.1,  self.execIntroDialog)
      reactor.callLater(1, self.Heartbeat)

      if CLI_ARGS:
         reactor.callLater(1, self.uriLinkClicked, CLI_ARGS[0])
      elif not self.firstLoad:
         # Don't need to bother the user on the first load with updating
         reactor.callLater(0.2, self.checkForLatestVersion)


   ####################################################
   def factoryReset(self):
      reply = QMessageBox.information(self,'Revert all Settings?', \
         'You are about to revert all Armory settings '
         'to the state they were in when Armory was first installed.  '
         '<br><br>'
         'If you click "Yes," Armory will exit after settings are '
         'reverted.  You will have to manually start Armory again.'
         '<br><br>'
         'Do you want to continue? ', \
         QMessageBox.Yes | QMessageBox.No)

      if reply==QMessageBox.Yes:
         self.doHardReset = True
         self.closeForReal()
         

   ####################################################
   def loadFailedManyTimesFunc(self, nFail):
      """
      For now, if the user is having trouble loading the blockchain, all 
      we do is delete mempool.bin (which is frequently corrupted but not 
      detected as such.  However, we may expand this in the future, if 
      it's determined that more-complicated things are necessary.
      """
      LOGERROR('%d attempts to load blockchain failed.  Remove mempool.bin.' % nFail)
      mempoolfile = os.path.join(ARMORY_HOME_DIR,'mempool.bin')
      if os.path.exists(mempoolfile): 
         os.remove(mempoolfile)
      else:
         LOGERROR('File mempool.bin does not exist. Nothing deleted.')

   ####################################################
   def menuSelectImportKey(self):
      QMessageBox.information(self, 'Select Wallet', \
         'You must import an address into a specific wallet.  If '
         'you do not want to import the key into any available wallet, '
         'it is recommeneded you make a new wallet for this purpose.'
         '<br><br>'
         'Double-click on the desired wallet from the main window, then '
         'click on "Import/Sweep Private Keys" on the bottom-right '
         'of the properties window.'
         '<br><br>'
         'Keys cannot be imported into watching-only wallets, only full '
         'wallets.', QMessageBox.Ok)

   ####################################################
   def menuSelectSweepKey(self):
      QMessageBox.information(self, 'Select Wallet', \
         'You must select a wallet into which funds will be swept. '
         'Double-click on the desired wallet from the main window, then '
         'click on "Import/Sweep Private Keys" on the bottom-right '
         'of the properties window to sweep to that wallet.'
         '<br><br>'
         'Keys cannot be swept into watching-only wallets, only full '
         'wallets.', QMessageBox.Ok)

   ####################################################
   def changeNumShow(self):
      prefWidth = self.numShowOpts[self.comboNumShow.currentIndex()]
      if prefWidth=='All':
         self.currLedgMin = 1;
         self.currLedgMax = self.ledgerSize
         self.currLedgWidth = -1;
      else:
         self.currLedgMax = self.currLedgMin + prefWidth - 1
         self.currLedgWidth = prefWidth
      
      self.applyLedgerRange()


   ####################################################
   def clickLedgUp(self):
      self.currLedgMin -= self.currLedgWidth
      self.currLedgMax -= self.currLedgWidth
      self.applyLedgerRange()

   ####################################################
   def clickLedgDn(self):
      self.currLedgMin += self.currLedgWidth
      self.currLedgMax += self.currLedgWidth
      self.applyLedgerRange()


   ####################################################
   def applyLedgerRange(self):
      if self.currLedgMin < 1:
         toAdd = 1 - self.currLedgMin
         self.currLedgMin += toAdd
         self.currLedgMax += toAdd

      if self.currLedgMax > self.ledgerSize:
         toSub = self.currLedgMax - self.ledgerSize
         self.currLedgMin -= toSub
         self.currLedgMax -= toSub

      self.currLedgMin = max(self.currLedgMin, 1)

      self.btnLedgUp.setVisible(self.currLedgMin!=1)
      self.btnLedgDn.setVisible(self.currLedgMax!=self.ledgerSize)

      self.createCombinedLedger()
         


   ####################################################
   def openSettings(self):
      dlgSettings = DlgSettings(self, self)
      dlgSettings.exec_()

   ####################################################
   def setupSystemTray(self):
      # Creating a QSystemTray
      self.sysTray = QSystemTrayIcon(self)
      self.sysTray.setIcon( QIcon(self.iconfile) )
      self.sysTray.setVisible(True)
      self.sysTray.setToolTip('Armory' + (' [Testnet]' if USE_TESTNET else ''))
      self.connect(self.sysTray, SIGNAL('messageClicked()'), self.bringArmoryToFront)
      self.connect(self.sysTray, SIGNAL('activated(QSystemTrayIcon::ActivationReason)'), \
                   self.sysTrayActivated)
      menu = QMenu(self)

      def traySend():
         self.bringArmoryToFront()
         self.clickSendBitcoins()

      def trayRecv():
         self.bringArmoryToFront()
         self.clickReceiveCoins()

      actShowArmory = self.createAction('Show Armory', self.bringArmoryToFront)
      actSendBtc    = self.createAction('Send Bitcoins', traySend)
      actRcvBtc     = self.createAction('Receive Bitcoins', trayRecv)
      actClose      = self.createAction('Quit Armory', self.closeForReal)
      # Create a short menu of options
      menu.addAction(actShowArmory)
      menu.addAction(actSendBtc)
      menu.addAction(actRcvBtc)
      menu.addSeparator()
      menu.addAction(actClose)
      self.sysTray.setContextMenu(menu)
      self.notifyQueue = []
      self.notifyBlockedUntil = 0


   #############################################################################
   def setupUriRegistration(self):
      """
      Setup Armory as the default application for handling bitcoin: links
      """
      # Don't bother the user on the first load with it if verification is 
      # needed.  They have enough to worry about with this weird new program.
      isFirstLoad = self.getSettingOrSetDefault('First_Load', True)

      if OS_LINUX:
         out,err = execAndWait('gconftool-2 --get /desktop/gnome/url-handlers/bitcoin/command')
      
         def setAsDefault():
            LOGINFO('Setting up Armory as default URI handler...')
            execAndWait('gconftool-2 -t string -s /desktop/gnome/url-handlers/bitcoin/command "python /usr/share/armory/ArmoryQt.py \"%s\""')
            execAndWait('gconftool-2 -s /desktop/gnome/url-handlers/bitcoin/needs_terminal false -t bool')
            execAndWait('gconftool-2 -t bool -s /desktop/gnome/url-handlers/bitcoin/enabled true')


         if 'no value' in out.lower() or 'no value' in err.lower():
            # Silently add Armory if it's never been set before
            setAsDefault()
         elif not 'armory' in out.lower() and not isFirstLoad:
            # If another application has it, ask for permission to change it
            if not self.getSettingOrSetDefault('DNAA_DefaultApp', False):
               reply = MsgBoxWithDNAA(MSGBOX.Question, 'Default URL Handler', \
                  'Armory is not set as your default application for handling '
                  '"bitcoin:" links.  Would you like to use Armory as the '
                  'default?', 'Do not ask this question again')
               if reply[0]==True:
                  setAsDefault()
               if reply[1]==True:
                  self.writeSetting('DNAA_DefaultApp', True)

      if OS_WINDOWS:
         # Check for existing registration (user first, then root, if necessary)
         action = 'DoNothing'
         rootKey = 'bitcoin\\shell\\open\\command'
         try:
            userKey = 'Software\\Classes\\' + rootKey
            registryKey = OpenKey(HKEY_CURRENT_USER, userKey, 0, KEY_READ)
            val,code = QueryValueEx(registryKey, '')
            if 'armory.exe' in val.lower():
               # Already set to Armory, we're done!
               return
            else:
               # Already set to something (at least created, which is enough)
               action = 'AskUser'
         except:
            # No user-key set, check if root-key is set
            try:
               registryKey = OpenKey(HKEY_CLASSES_ROOT, rootKey, 0, KEY_READ)
               val,code = QueryValueEx(registryKey, '')
               if 'armory.exe' in val.lower():
                  # Already set to Armory, we're done!
                  return
               else:
                  # Root key is set (or at least created, which is enough)
                  action = 'AskUser'
            except:
               action = 'DoIt'

         dontAsk = self.getSettingOrSetDefault('DNAA_DefaultApp', False)
         if action=='AskUser' and not isFirstLoad and not dontAsk:
            # If another application has it, ask for permission to change it
            reply = MsgBoxWithDNAA(MSGBOX.Question, 'Default URL Handler', \
               'Armory is not set as your default application for handling '
               '"bitcoin:" links.  Would you like to use Armory as the '
               'default?', 'Do not ask this question again')

            if reply[1]==True:
               self.writeSetting('DNAA_DefaultApp', True)

            if reply[0]==True:
               action = 'DoIt'
            else:
               return 

         # Finally, do it if we're supposed to!
         if action=='DoIt':
            x86str = '' if platform.architecture()[0][:2]=='32' else ' (x86)'
            baseDir = 'C:\\Program Files%s\\Armory\\Armory Bitcoin Client' % x86str
            regKeys = []
            regKeys.append(['Software\\Classes\\bitcoin', '', 'URL:bitcoin Protocol'])
            regKeys.append(['Software\\Classes\\bitcoin', 'URL Protocol', ""])
            regKeys.append(['Software\\Classes\\bitcoin\\shell', '', None])
            regKeys.append(['Software\\Classes\\bitcoin\\shell\\open', '',  None])
            regKeys.append(['Software\\Classes\\bitcoin\\shell\\open\\command',  '', \
                           '"%s\\Armory.exe" %%1' % baseDir])
            regKeys.append(['Software\\Classes\\bitcoin\\DefaultIcon', '',  \
                           '"%s\\armory48x48.ico"' % baseDir])

            for key,name,val in regKeys:
               dkey = '%s\\%s' % (key,name)
               LOGINFO('\tWriting key: [HKEY_CURRENT_USER\\] ' + dkey)
               registryKey = CreateKey(HKEY_CURRENT_USER, key)
               SetValueEx(registryKey, name, 0, REG_SZ, val)
               CloseKey(registryKey)

         
         


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
      if not self.getSettingOrSetDefault('DNAA_IntroDialog', False):
         dlg = DlgIntroMessage(self, self)
         result = dlg.exec_()

         if dlg.chkDnaaIntroDlg.isChecked():
            self.writeSetting('DNAA_IntroDialog', True)

         if dlg.requestCreate:
            self.createNewWallet(initLabel='Primary Wallet')

         if dlg.requestImport:
            self.execImportWallet()
            
      
   
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
      LOGINFO('Changing usermode:')
      LOGINFO('   From: %s', self.settings.get('User_Mode'))
      self.usermode = mode
      if mode==USERMODE.Standard:
         self.writeSetting('User_Mode', 'Standard')
      if mode==USERMODE.Advanced:
         self.writeSetting('User_Mode', 'Advanced')
      if mode==USERMODE.Expert:
         self.writeSetting('User_Mode', 'Expert')
      LOGINFO('     To: %s', self.settings.get('User_Mode'))

      if not self.firstModeSwitch:
         QMessageBox.information(self,'Restart Armory', \
         'You may have to restart Armory for all aspects of '
         'the new usermode to go into effect.', QMessageBox.Ok)

      self.firstModeSwitch = False
      


   #############################################################################
   def getPreferredDateFormat(self):
      # Treat the format as "binary" to make sure any special symbols don't
      # interfere with the SettingsFile symbols
      globalDefault = binary_to_hex(DEFAULT_DATE_FORMAT)
      fmt = self.getSettingOrSetDefault('DateFormat', globalDefault)
      return hex_to_binary(str(fmt))  # short hex strings could look like int()

   #############################################################################
   def setPreferredDateFormat(self, fmtStr):
      # Treat the format as "binary" to make sure any special symbols don't
      # interfere with the SettingsFile symbols
      try:
         unixTimeToFormatStr(1000000000, fmtStr)
      except:
         QMessageBox.warning(self, 'Invalid Date Format', \
            'The date format you specified was not valid.  Please re-enter '
            'it using only the strftime symbols shown in the help text.', \
            QMessageBox.Ok)
         return False

      self.writeSetting('DateFormat', binary_to_hex(fmtStr))
      return True


   #############################################################################
   def checkForLatestVersion(self, wasRequested=False):
      # Download latest versions.txt file, accumulate changelog
      if CLI_OPTIONS.skipVerCheck:
         return

      optChkVer = self.getSettingOrSetDefault('CheckVersion', 'Always')
      if optChkVer.lower()=='never' and not wasRequested:
         LOGINFO('User requested never check for new versions')
         return

      if wasRequested and not self.internetAvail:
         QMessageBox.critical(self, 'Offline Mode', \
            'You are in offline mode, which means that version information '
            'cannot be retrieved from the internet.  Please visit '
            'www.bitcoinarmory.com from an internet-connected computer '
            'to get the latest version information.', QMessageBox.Ok)
         return

      versionFile = None
      try:
         import urllib2
         import socket
         socket.setdefaulttimeout(CLI_OPTIONS.nettimeout)
         versionLines = urllib2.urlopen(HTTP_VERSION_FILE, timeout=CLI_OPTIONS.nettimeout)
         versionLines = versionLines.readlines()
      except ImportError:
         LOGERROR('No module urllib2 -- cannot get latest version')
         return
      except (urllib2.URLError, urllib2.HTTPError):
         if wasRequested:
            QMessageBox.critical(self, 'Unavailable',  \
              'The latest Armory version information could not be retrieved.'
              'Please check www.bitcoinarmory.com for the latest version '
              'information.', QMessageBox.Ok)
         LOGERROR('Could not access latest Armory version information')
         LOGERROR('Tried: %s', HTTP_VERSION_FILE)
         return
      
      try:
         currLineIdx = [0]

         def popNextLine(currIdx):
            if currIdx[0] < len(versionLines):
               outstr = versionLines[ currIdx[0] ]
               currIdx[0] += 1
               return outstr.strip()
            else:
               return None
            

         thisVerString = getVersionString(BTCARMORY_VERSION)
         changeLog = []
         vernum = ''

         line = popNextLine(currLineIdx)
         comments = ''
         while line != None:
            if not line.startswith('#') and len(line)>0:
               if line.startswith('VERSION'):
                  vstr = line.split(' ')[-1]
                  myVersionInt = getVersionInt(readVersionString(thisVerString))
                  latestVerInt = getVersionInt(readVersionString(vstr))
                  if myVersionInt>=latestVerInt and not wasRequested:
                     break
                  changeLog.append([vstr, []])
               elif line.startswith('-'):
                  featureTitle = line[2:]
                  changeLog[-1][1].append([featureTitle, []])
               else:
                  changeLog[-1][1][-1][1].append(line)
            if line.startswith('#'):
               comments += line+'\n'
            line = popNextLine(currLineIdx)

         # We also store the list of latest
         try:
            msg = extractSignedDataFromVersionsDotTxt(comments)
            if len(msg)>0:
               dldict,verstrs = parseLinkList(msg)
               self.downloadDict = dldict.copy()
               self.latestVer = verstrs.copy()
            else:
               raise ECDSA_Error, 'Could not verify'
         except:
            print sys.exc_info()
            
            

         if len(changeLog)==0 and not wasRequested:
            LOGINFO('You are running the latest version!')
         elif optChkVer[1:]==changeLog[0][0] and not wasRequested:
            LOGINFO('Latest version is %s -- Notify user on next version.', optChkVer)
            return
         else:
            DlgVersionNotify(self,self, changeLog, wasRequested).exec_()
      except:
         if wasRequested:
            QMessageBox.critical(self, 'Parse Error',  \
              'The version information is malformed and cannot be understood. '
              'Please check www.bitcoinarmory.com for the latest version '
              'information.', QMessageBox.Ok)
         LOGEXCEPT('Error trying to parse versions.txt file')
       

   #############################################################################
   def setupNetworking(self):

      TimerStart('setupNetworking')

      LOGINFO('Setting up networking...')
      self.internetAvail = False

      # Prevent Armory from being opened twice
      from twisted.internet import reactor
      def uriClick_partial(a):
         self.uriLinkClicked(a)

      if CLI_OPTIONS.interport > 1:
         try:
            self.InstanceListener = ArmoryListenerFactory(self.bringArmoryToFront, \
                                                          uriClick_partial )
            reactor.listenTCP(CLI_OPTIONS.interport, self.InstanceListener)
         except twisted.internet.error.CannotListenError:
            LOGWARN('Socket already occupied!  This must be a duplicate Armory instance!')
            QMessageBox.warning(self, 'Only One, Please!', \
               'Armory is already running!  You can only have one instance open '
               'at a time.  Aborting...', QMessageBox.Ok)
            os._exit(0)
      else:
         LOGWARN('*** Listening port is disabled.  URI-handling will not work')
      

      settingSkipCheck = self.getSettingOrSetDefault('SkipOnlineCheck', False)
      self.forceOnline = CLI_OPTIONS.forceOnline or settingSkipCheck
      if self.forceOnline:
         LOGINFO('Forced online mode: True')

      # Check general internet connection
      self.internetAvail = False
      if not self.forceOnline:
         try:
            import urllib2
            response=urllib2.urlopen('http://google.com', timeout=CLI_OPTIONS.nettimeout)
            self.internetAvail = True
         except ImportError:
            LOGERROR('No module urllib2 -- cannot determine if internet is available')
         except urllib2.URLError:
            # In the extremely rare case that google might be down (or just to try again...)
            try:
               response=urllib2.urlopen('http://microsoft.com', timeout=CLI_OPTIONS.nettimeout)
            except urllib2.URLError:
               self.internetAvail = False

      LOGINFO('Internet connection is Available: %s', self.internetAvail)
      LOGINFO('Bitcoin-Qt/bitcoind is Available: %s', self.bitcoindIsAvailable())


      TimerStop('setupNetworking')

   ############################################################################
   def startBitcoindIfNecessary(self):
      if not (self.forceOnline or self.internetAvail) or CLI_OPTIONS.offline:
         LOGWARN('Not online, will not start bitcoind')
         return False

      if not self.doManageSatoshi:
         LOGWARN('Tried to start bitcoind, but ManageSatoshi==False')
         return False

      
      # We skip the getSettingOrSetDefault call, because we don't want to set
      # it if it doesn't exist
      satexe = None
      if self.settings.hasSetting('SatoshiExe'):
         satexe = [self.settings.get('SatoshiExe')]
      else:
         satexe = []
   
      sathome = BTC_HOME_DIR
      if self.settings.hasSetting('SatoshiDatadir') and \
         CLI_OPTIONS.satoshiHome=='DEFAULT':
         # Setting override BTC_HOME_DIR only if it wasn't explicitly
         # set as the command line.  
         sathome = self.settings.get('SatoshiDatadir')
  
      TheSDM.setDisabled(False)
      try:
         # "satexe" is actually just the install directory, not the direct
         # path the executable.  That dir tree will be searched for bitcoind
         TheSDM.setupSDM(None, sathome, extraExeSearch=satexe)
         TheSDM.startBitcoind()
         return True
      except:
         LOGERROR('Failed to setup SDM')
         self.switchNetworkMode(NETWORKMODE.Offline)
      
       
   ############################################################################
   def loadBlockchainIfNecessary(self):

      if CLI_OPTIONS.offline:
         if self.forceOnline:
            LOGERROR('Cannot mix --force-online and --offline options!  Using offline mode.')
         self.switchNetworkMode(NETWORKMODE.Offline)
         TheBDM.setOnlineMode(False, wait=False)
      elif self.onlineModeIsPossible():
         # Track number of times we start loading the blockchain.
         # We will decrement the number when loading finishes
         # We can use this to detect problems with mempool or blkxxxx.dat
         self.numTriesOpen = self.getSettingOrSetDefault('FailedLoadCount', 0)
         if self.numTriesOpen>2:
            self.loadFailedManyTimesFunc(self.numTriesOpen)
         self.settings.set('FailedLoadCount', self.numTriesOpen+1)

         self.switchNetworkMode(NETWORKMODE.Full)
         self.resetBdmBeforeScan()
         TheBDM.setOnlineMode(True, wait=False)

      else:
         self.switchNetworkMode(NETWORKMODE.Offline)
         TheBDM.setOnlineMode(False, wait=False)
          




   #############################################################################
   def checkHaveBlockfiles(self):
      return os.path.exists(BLKFILE_FIRSTFILE)

   #############################################################################
   def onlineModeIsPossible(self):
      return ((self.internetAvail or self.forceOnline) and \
               self.bitcoindIsAvailable() and \
               self.checkHaveBlockfiles())


   #############################################################################
   def bitcoindIsAvailable(self):
      return satoshiIsAvailable('127.0.0.1', BITCOIN_PORT)

   #############################################################################
   def checkForInstalledBitcoind(self):
      
      # it if it doesn't exist
      satexe  = BITCOIND_PATH
      if self.settings.hasSetting('SatoshiExe'):
         satexe  = self.settings.get('SatoshiExe')
   
      sathome = BTC_HOME_DIR
      if self.settings.hasSetting('SatoshiDatadir'):
         sathome = self.getSettingOrSetDefault('SatoshiDatadir', BTC_HOME_DIR)
   
      try:
         TheSDM.setupSDM(satexe, sathome)
      except self.BitcoindError:
         LOGINFO('SetupSDM failed (FailedExe: %s, FailedHome: %s)', \
                     TheSDM.failedFindExe, TheSDM.failedFindHome)
                  

   #############################################################################
   def switchNetworkMode(self, newMode):
      print 'Setting netmode:', newMode
      self.netMode=newMode
      if newMode in (NETWORKMODE.Offline, NETWORKMODE.Disconnected):
         self.NetworkingFactory = FakeClientFactory()
         return
      elif newMode==NETWORKMODE.Full:
               
         # Actually setup the networking, now
         from twisted.internet import reactor

         def showOfflineMsg():
            self.netMode = NETWORKMODE.Disconnected
            self.setDashboardDetails()
            self.lblArmoryStatus.setText( \
               '<font color=%s><i>Disconnected</i></font>' % htmlColor('TextWarn'))
            if not self.getSettingOrSetDefault('NotifyDiscon', True):
               return 
   
            try:
               self.sysTray.showMessage('Disconnected', \
                     'Connection to Bitcoin-Qt client lost!  Armory cannot send \n'
                     'or receive bitcoins until connection is re-established.', \
                     QSystemTrayIcon.Critical, 10000)
            except:
               LOGEXCEPT('Failed to show disconnect notification')


         self.connectCount = 0
         def showOnlineMsg():
            self.netMode = NETWORKMODE.Full
            self.setDashboardDetails()
            self.lblArmoryStatus.setText(\
                     '<font color=%s>Connected (%s blocks)</font> ' % 
                     (htmlColor('TextGreen'), self.currBlockNum))
            if not self.getSettingOrSetDefault('NotifyReconn', True):
               return
   
            try:
               if self.connectCount>0:
                  self.sysTray.showMessage('Connected', \
                     'Connection to Bitcoin-Qt re-established', \
                     QSystemTrayIcon.Information, 10000)
               self.connectCount += 1
            except:
               LOGEXCEPT('Failed to show reconnect notification')
   
   
         self.NetworkingFactory = ArmoryClientFactory( \
                                          func_loseConnect=showOfflineMsg, \
                                          func_madeConnect=showOnlineMsg, \
                                          func_newTx=self.newTxFunc)
                                          #func_newTx=newTxFunc)
         reactor.callWhenRunning(reactor.connectTCP, '127.0.0.1', \
                                          BITCOIN_PORT, self.NetworkingFactory)

   


   #############################################################################
   def newTxFunc(self, pytxObj):
      if TheBDM.getBDMState() in ('Offline','Uninitialized') or self.doShutdown:
         return

      TheBDM.addNewZeroConfTx(pytxObj.serialize(), long(RightNow()), True, wait=False)
      self.newZeroConfSinceLastUpdate.append(pytxObj.serialize())
      #LOGDEBUG('Added zero-conf tx to pool: ' + binary_to_hex(pytxObj.thisHash))




   #############################################################################
   def parseUriLink(self, uriStr, clickOrEnter='click'):
      ClickOrEnter = clickOrEnter[0].upper() + clickOrEnter[1:]
      LOGINFO('URI link clicked!')
      LOGINFO('The following URI string was parsed:')
      LOGINFO(uriStr.replace('%','%%'))
      uriDict = parseBitcoinURI(uriStr)
      if TheBDM.getBDMState() in ('Offline','Uninitialized'):
         LOGERROR('%sed "bitcoin:" link in offline mode.' % ClickOrEnter)
         self.bringArmoryToFront() 
         QMessageBox.warning(self, 'Offline Mode',
            'You %sed on a "bitcoin:" link, but Armory is in '
            'offline mode, and is not capable of creating transactions. '
            '%sing links will only work if Armory is connected '
            'to the Bitcoin network!' % (clickOrEnter, ClickOrEnter), \
             QMessageBox.Ok)
         return {}
         
      if len(uriDict)==0:
         warnMsg = ('It looks like you just %sed a "bitcoin:" link, but '
                    'that link is malformed.  ' % clickOrEnter)
         if self.usermode == USERMODE.Standard:
            warnMsg += ('Please check the source of the link and enter the '
                        'transaction manually.')
         else:
            warnMsg += 'The raw URI string is:<br><br>' + uriStr
         QMessageBox.warning(self, 'Invalid URI', warnMsg, QMessageBox.Ok)
         LOGERROR(warnMsg)
         return {}

      if not uriDict.has_key('address'):
         QMessageBox.warning(self, 'The "bitcoin:" link you just %sed '
            'does not even contain an address!  There is nothing that '
            'Armory can do with this link!' % clickOrEnter, QMessageBox.Ok)
         LOGERROR('No address in "bitcoin:" link!  Nothing to do!')
         return {}

      # Verify the URI is for the same network as this Armory instnance
      theAddrByte = checkAddrType(base58_to_binary(uriDict['address']))
      if theAddrByte!=-1 and theAddrByte!=ADDRBYTE:
         net = 'Unknown Network'
         if NETWORKS.has_key(theAddrByte):
            net = NETWORKS[theAddrByte]
         QMessageBox.warning(self, 'Wrong Network!', \
            'The address for the "bitcoin:" link you just %sed is '
            'for the wrong network!  You are on the <b>%s</b> '
            'and the address you supplied is for the the '
            '<b>%s</b>!' % (clickOrEnter, NETWORKS[ADDRBYTE], net), \
            QMessageBox.Ok)
         LOGERROR('URI link is for the wrong network!')
         return {}

      # If the URI contains "req-" strings we don't recognize, throw error
      recognized = ['address','version','amount','label','message']
      for key,value in uriDict.iteritems():
         if key.startswith('req-') and not key[4:] in recognized:
            QMessageBox.warning(self,'Unsupported URI', 'The "bitcoin:" link '
               'you just %sed contains fields that are required but not '
               'recognized by Armory.  This may be an older version of Armory, '
               'or the link you %sed on uses an exotic, unsupported format.'
               '<br><br>The action cannot be completed.' % (clickOrEnter, clickOrEnter), \
               QMessageBox.Ok)
            LOGERROR('URI link contains unrecognized req- fields.')
            return {}

      return uriDict



   #############################################################################
   def uriLinkClicked(self, uriStr):
      if not TheBDM.getBDMState()=='BlockchainReady':
         QMessageBox.warning(self, 'Offline', \
            'You just clicked on a "bitcoin:" link, but Armory is offline ' 
            'and cannot send transactions.  Please click the link '
            'again when Armory is online.', \
            QMessageBox.Ok)
         return

      uriDict = self.parseUriLink(uriStr, 'click')
         
      if len(uriDict)>0:
         self.bringArmoryToFront() 
         return self.uriSendBitcoins(uriDict)
      

   #############################################################################
   def loadWalletsAndSettings(self):

      TimerStart('loadWltSettings')

      self.getSettingOrSetDefault('First_Load',         True)
      self.getSettingOrSetDefault('Load_Count',         0)
      self.getSettingOrSetDefault('User_Mode',          'Advanced')
      self.getSettingOrSetDefault('UnlockTimeout',      10)
      self.getSettingOrSetDefault('DNAA_UnlockTimeout', False)


      # Determine if we need to do new-user operations, increment load-count
      self.firstLoad = False
      if self.getSettingOrSetDefault('First_Load', True):
         self.firstLoad = True
         self.writeSetting('First_Load', False)
         self.writeSetting('First_Load_Date', long(RightNow()))
         self.writeSetting('Load_Count', 1)
         self.writeSetting('AdvFeature_UseCt', 0)
      else:
         self.writeSetting('Load_Count', (self.settings.get('Load_Count')+1) % 100)
         firstDate = self.getSettingOrSetDefault('First_Load_Date', RightNow())
         daysSinceFirst = (RightNow() - firstDate) / (60*60*24)
         

      # Set the usermode, default to standard
      self.usermode = USERMODE.Standard
      if self.settings.get('User_Mode') == 'Advanced':
         self.usermode = USERMODE.Advanced
      elif self.settings.get('User_Mode') == 'Expert':
         self.usermode = USERMODE.Expert

      # Load wallets found in the .armory directory
      wltPaths = self.settings.get('Other_Wallets', expectList=True)
      self.walletMap = {}
      self.walletIndices = {}  
      self.walletIDSet = set()

      # I need some linear lists for accessing by index
      self.walletIDList = []   
      self.combinedLedger = []
      self.ledgerSize = 0
      self.ledgerTable = []

      self.currBlockNum = 0



      LOGINFO('Loading wallets...')
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
               LOGWARN('***WARNING: Duplicate wallet detected, %s', wltID)
               wo1 = self.walletMap[wltID].watchingOnly
               wo2 = wltLoad.watchingOnly
               if wo1 and not wo2:
                  prevWltPath = self.walletMap[wltID].walletPath
                  self.walletMap[wltID] = wltLoad
                  LOGWARN('First wallet is more useful than the second one...')
                  LOGWARN('     Wallet 1 (loaded):  %s', fpath)
                  LOGWARN('     Wallet 2 (skipped): %s', prevWltPath)
               else:
                  LOGWARN('Second wallet is more useful than the first one...')
                  LOGWARN('     Wallet 1 (loaded):  %s', self.walletMap[wltID].walletPath)
                  LOGWARN('     Wallet 2 (skipped): %s', fpath)
            else:
               # Update the maps/dictionaries
               self.walletMap[wltID] = wltLoad
               self.walletIndices[wltID] = len(self.walletMap)-1

               # Maintain some linear lists of wallet info
               self.walletIDSet.add(wltID)
               self.walletIDList.append(wltID)
         except:
            LOGEXCEPT( '***WARNING: Wallet could not be loaded: %s (skipping)', fpath)
            raise
                     

      
      LOGINFO('Number of wallets read in: %d', len(self.walletMap))
      for wltID, wlt in self.walletMap.iteritems():
         dispStr  = ('   Wallet (%s):' % wlt.uniqueIDB58).ljust(25)
         dispStr +=  '"'+wlt.labelName.ljust(32)+'"   '
         dispStr +=  '(Encrypted)' if wlt.useEncryption else '(No Encryption)'
         LOGINFO(dispStr)
         # Register all wallets with TheBDM
         TheBDM.registerWallet( wlt.cppWallet )


      # Get the last directory
      savedDir = self.settings.get('LastDirectory')
      if len(savedDir)==0 or not os.path.exists(savedDir):
         savedDir = ARMORY_HOME_DIR
      self.lastDirectory = savedDir
      self.writeSetting('LastDirectory', savedDir)

      TimerStop('loadWltSettings')

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

      # Found a bug with Swig+Threading+PyQt+OSX -- save/load file dialogs freeze
      # User picobit discovered this is avoided if you use the Qt dialogs, instead 
      # of the native OS dialogs.  Use native for all except OSX...
      if not OS_MACOSX:
         fullPath = unicode(QFileDialog.getSaveFileName(self, title, startPath, typesStr))
      else:
         fullPath = unicode(QFileDialog.getSaveFileName(self, title, startPath, typesStr,
                                             options=QFileDialog.DontUseNativeDialog))
      

      fdir,fname = os.path.split(fullPath)
      if fdir:
         self.writeSetting('LastDirectory', fdir)
      return fullPath
      

   #############################################################################
   def getFileLoad(self, title='Load Wallet File', ffilter=['Wallet files (*.wallet)']):
      lastDir = self.settings.get('LastDirectory')
      if len(lastDir)==0 or not os.path.exists(lastDir):
         lastDir = ARMORY_HOME_DIR

      types = list(ffilter)
      types.append('All files (*)')
      typesStr = ';; '.join(types)
      # Found a bug with Swig+Threading+PyQt+OSX -- save/load file dialogs freeze
      # User picobit discovered this is avoided if you use the Qt dialogs, instead 
      # of the native OS dialogs.  Use native for all except OSX...
      if not OS_MACOSX:
         fullPath = unicode(QFileDialog.getOpenFileName(self, title, lastDir, typesStr))
      else:
         fullPath = unicode(QFileDialog.getOpenFileName(self, title, lastDir, typesStr, \
                                             options=QFileDialog.DontUseNativeDialog))

      self.writeSetting('LastDirectory', os.path.split(fullPath)[0])
      return fullPath
   
   ##############################################################################
   def getWltSetting(self, wltID, propName):
      # Sometimes we need to settings specific to individual wallets -- we will
      # prefix the settings name with the wltID.
      wltPropName = 'Wallet_%s_%s' % (wltID, propName)
      try:
         return self.settings.get(wltPropName)
      except KeyError:
         return ''

   #############################################################################
   def setWltSetting(self, wltID, propName, value):
      wltPropName = 'Wallet_%s_%s' % (wltID, propName)
      self.writeSetting(wltPropName, value)


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
   def getSettingOrSetDefault(self, settingName, defaultVal, forceStr=False):
      s = self.settings.getSettingOrSetDefault(settingName, defaultVal)
      if forceStr:
         s = str(s)
      return s

   #############################################################################
   def writeSetting(self, settingName, val):
      self.settings.set(settingName, val)


   #############################################################################
   def startRescanBlockchain(self):
      if TheBDM.getBDMState() in ('Offline','Uninitialized'):
         LOGWARNING('Rescan requested but Armory is in offline mode')
         return 

      if TheBDM.getBDMState()=='Scanning':
         LOGINFO('Queueing rescan after current scan completes.')
      else:
         LOGINFO('Starting blockchain rescan...')

      # Start it in the background
      self.needUpdateAfterScan = True
      TheBDM.rescanBlockchain(wait=False)
      self.setDashboardDetails()




   #############################################################################
   def finishLoadBlockchain(self):

      TimerStart('finishLoadBlockchain')
      # Now that the blockchain is loaded, let's populate the wallet info
      if TheBDM.isInitialized():

         self.currBlockNum = TheBDM.getTopBlockHeight()
         self.setDashboardDetails()
         if not self.memPoolInit:
            mempoolfile = os.path.join(ARMORY_HOME_DIR,'mempool.bin')
            self.checkMemoryPoolCorruption(mempoolfile)
            TheBDM.enableZeroConf(mempoolfile)
            self.memPoolInit = True

         TimerStart('initialWalletSync')
         for wltID in self.walletMap.iterkeys():
            LOGINFO('Syncing wallet: %s', wltID)
            self.walletMap[wltID].setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
            self.walletMap[wltID].syncWithBlockchainLite(0)
            self.walletMap[wltID].detectHighestUsedIndex(True)  # expand wlt if necessary
            self.walletMap[wltID].fillAddressPool()
         TimerStop('initialWalletSync')

         
         self.createCombinedLedger()
         self.ledgerSize = len(self.combinedLedger)
         self.statusBar().showMessage('Blockchain loaded, wallets sync\'d!', 10000) 
         if self.netMode==NETWORKMODE.Full:
            self.lblArmoryStatus.setText(\
               '<font color=%s>Connected (%s blocks)</font> ' % 
               (htmlColor('TextGreen'), self.currBlockNum))
         self.blkReceived  = self.getSettingOrSetDefault('LastBlkRecvTime', 0)

         if self.getSettingOrSetDefault('NotifyBlkFinish',True):
            reply,remember = MsgBoxWithDNAA(MSGBOX.Info, \
               'Blockchain Loaded!', 'Blockchain loading is complete.  '
               'Your balances and transaction history are now available '
               'under the "Transactions" tab.  You can also send and '
               'receive bitcoins.', \
               dnaaMsg='Do not show me this notification again ', yesStr='OK')
                  
            if remember==True:
               self.writeSetting('NotifyBlkFinish',False)
         else:
            self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Transactions)

               
         self.netMode = NETWORKMODE.Full
         self.settings.set('FailedLoadCount', 0)
      else:
         self.statusBar().showMessage('! Blockchain loading failed !', 10000)
   
   
      # This will force the table to refresh with new data
      self.setDashboardDetails()
      self.walletModel.reset()
      
      TimerStop('finishLoadBlockchain')


   #############################################################################
   def checkMemoryPoolCorruption(self, mempoolname):
      if not os.path.exists(mempoolname): 
         return

      memfile = open(mempoolname, 'r')
      memdata = memfile.read()
      memfile.close()

      binunpacker = BinaryUnpacker(memdata)
      try:
         while binunpacker.getRemainingSize() > 0:
            binunpacker.get(UINT64)
            PyTx().unserialize(binunpacker)
      except:
         os.remove(mempoolname);
         LOGWARN('Memory pool file was corrupt.  Deleted. (no further action is needed)')
      

   
   #############################################################################
   def changeLedgerSorting(self, col, order):
      """
      The direct sorting was implemented to avoid having to search for comment
      information for every ledger entry.  Therefore, you can't sort by comments
      without getting them first, which is the original problem to avoid.  
      """
      if col in (LEDGERCOLS.NumConf, LEDGERCOLS.DateStr, \
                 LEDGERCOLS.Comment, LEDGERCOLS.Amount, LEDGERCOLS.WltName):
         self.sortLedgCol = col
         self.sortLedgOrder = order
      self.createCombinedLedger()


   #############################################################################
   def createCombinedLedger(self, wltIDList=None, withZeroConf=True):
      """
      Create a ledger to display on the main screen, that consists of ledger
      entries of any SUBSET of available wallets.
      """
   
      TimerStart('createCombinedLedger')

      start = RightNow()
      if wltIDList==None:
         # Create a list of [wltID, type] pairs
         typelist = [[wid, determineWalletType(self.walletMap[wid], self)[0]] \
                                                      for wid in self.walletIDList]

         # We need to figure out which wallets to combine here...
         currIdx  = max(self.comboWltSelect.currentIndex(), 0)
         currText = str(self.comboWltSelect.currentText()).lower()
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
         self.writeSetting('LastFilterState', currIdx)
               

      if wltIDList==None:
         TimerStop('createCombinedLedger')
         return

      self.combinedLedger = []
      totalFunds  = 0
      spendFunds  = 0
      unconfFunds = 0
      currBlk = 0xffffffff
      if TheBDM.isInitialized():
         currBlk = TheBDM.getTopBlockHeight()

      for wltID in wltIDList:
         wlt = self.walletMap[wltID]
         id_le_pairs = [[wltID, le] for le in wlt.getTxLedger('Full')]
         self.combinedLedger.extend(id_le_pairs)
         totalFunds += wlt.getBalance('Total')
         spendFunds += wlt.getBalance('Spendable')
         unconfFunds += wlt.getBalance('Unconfirmed')


      # Apply table sorting -- this is very fast
      sortDir = (self.sortLedgOrder == Qt.AscendingOrder)
      if self.sortLedgCol == LEDGERCOLS.NumConf:
         self.combinedLedger.sort(key=lambda x: currBlk-x[1].getBlockNum()+1, reverse=not sortDir)
      if self.sortLedgCol == LEDGERCOLS.DateStr:
         self.combinedLedger.sort(key=lambda x: x[1].getTxTime(), reverse=sortDir)
      if self.sortLedgCol == LEDGERCOLS.WltName:
         self.combinedLedger.sort(key=lambda x: self.walletMap[x[0]].labelName, reverse=sortDir)
      if self.sortLedgCol == LEDGERCOLS.Comment:
         self.combinedLedger.sort(key=lambda x: self.getCommentForLE(x[0],x[1]), reverse=sortDir)
      if self.sortLedgCol == LEDGERCOLS.Amount:
         self.combinedLedger.sort(key=lambda x: abs(x[1].getValue()), reverse=sortDir)

      self.ledgerSize = len(self.combinedLedger)

      # Hide the ledger slicer if our data set is smaller than the slice width
      self.frmLedgUpDown.setVisible(self.ledgerSize>self.currLedgWidth)
      self.lblLedgRange.setText('%d to %d' % (self.currLedgMin, self.currLedgMax))
      self.lblLedgTotal.setText('(of %d)' % self.ledgerSize)

      # Many MainWindow objects haven't been created yet... 
      # let's try to update them and fail silently if they don't exist
      try:
         if TheBDM.getBDMState() in ('Offline', 'Scanning'):
            self.lblTotalFunds.setText( '-'*12 )
            self.lblSpendFunds.setText( '-'*12 )
            self.lblUnconfFunds.setText('-'*12 )
            return
            
         uncolor =  htmlColor('MoneyNeg')  if unconfFunds>0          else htmlColor('Foreground')
         btccolor = htmlColor('DisableFG') if spendFunds==totalFunds else htmlColor('MoneyPos')
         lblcolor = htmlColor('DisableFG') if spendFunds==totalFunds else htmlColor('Foreground')
         goodColor= htmlColor('TextGreen')
         self.lblTotalFunds.setText( '<b><font color="%s">%s</font></b>' % (btccolor,coin2str(totalFunds)))
         self.lblTot.setText('<b><font color="%s">Maximum Funds:</font></b>' % lblcolor)
         self.lblBTC1.setText('<b><font color="%s">BTC</font></b>' % lblcolor)
         self.lblSpendFunds.setText( '<b><font color=%s>%s</font></b>' % (goodColor, coin2str(spendFunds)))
         self.lblUnconfFunds.setText('<b><font color="%s">%s</font></b>' % \
                                             (uncolor, coin2str(unconfFunds)))

         # Finally, update the ledger table
         rmin,rmax = self.currLedgMin-1, self.currLedgMax
         self.ledgerTable = self.convertLedgerToTable(self.combinedLedger[rmin:rmax])
         self.ledgerModel.ledger = self.ledgerTable
         self.ledgerModel.reset()

      except AttributeError:
         raise
      finally: 
         TimerStop('createCombinedLedger')


      

   #############################################################################
   def convertLedgerToTable(self, ledger):

      TimerStart('convertLedgerTbl')
      
      table2D = []
      datefmt = self.getPreferredDateFormat()
      for wltID,le in ledger: 
         row = []

         wlt = self.walletMap[wltID]
         nConf = self.currBlockNum - le.getBlockNum()+1
         if le.getBlockNum()>=0xffffffff:
            nConf=0

         # We need to compute the fee by adding inputs and outputs...
         amt = le.getValue()
         #removeFee = self.getSettingOrSetDefault('DispRmFee', False)
         #if TheBDM.isInitialized() and removeFee and amt<0:
            #amt += self.getFeeForTx(le.getTxHash())

         # If this was sent-to-self... we should display the actual specified
         # value when the transaction was executed.  This is pretty difficult 
         # when both "recipient" and "change" are indistinguishable... but
         # They're actually not because we ALWAYS generate a new address to
         # for change , which means the change address MUST have a higher 
         # chain index
         if le.isSentToSelf():
            amt = determineSentToSelfAmt(le, wlt)[0]
            

         if le.getBlockNum() >= 0xffffffff: nConf = 0
         # NumConf
         row.append(nConf)

         # UnixTime (needed for sorting)
         row.append(le.getTxTime())

         # Date
         row.append(unixTimeToFormatStr(le.getTxTime(), datefmt))

         # TxDir (actually just the amt... use the sign of the amt to determine dir)
         row.append(coin2str(le.getValue(), maxZeros=2))

         # Wlt Name
         row.append(self.walletMap[wltID].labelName)
         
         # Comment
         row.append(self.getCommentForLE(wltID, le))

         # Amount
         row.append(coin2str(amt, maxZeros=2))

         # Is this money mine?
         row.append( determineWalletType(wlt, self)[0]==WLTTYPES.WatchOnly)

         # WltID
         row.append( wltID )

         # TxHash
         row.append( binary_to_hex(le.getTxHash() ))

         # Is this a coinbase/generation transaction
         row.append( le.isCoinbase() )

         # Sent-to-self
         row.append( le.isSentToSelf() )

         # Tx was invalidated!  (double=spend!)
         row.append( not le.isValid())

         # Finally, attach the row to the table
         table2D.append(row)

      TimerStop('convertLedgerTbl')

      return table2D

      
   #############################################################################
   def walletListChanged(self):
      TimerStart('wltListChanged')
      self.walletModel.reset()
      self.populateLedgerComboBox()
      self.createCombinedLedger()
      TimerStop('wltListChanged')


   #############################################################################
   def populateLedgerComboBox(self):
      TimerStart('populateLedgerCombo')
      self.comboWltSelect.clear()
      self.comboWltSelect.addItem( 'My Wallets'        )
      self.comboWltSelect.addItem( 'Offline Wallets'   )
      self.comboWltSelect.addItem( 'Other\'s wallets'  )
      self.comboWltSelect.addItem( 'All Wallets'       )
      for wltID in self.walletIDList:
         self.comboWltSelect.addItem( self.walletMap[wltID].labelName )
      self.comboWltSelect.insertSeparator(4)
      self.comboWltSelect.insertSeparator(4)
      comboIdx = self.getSettingOrSetDefault('LastFilterState', 0)
      self.comboWltSelect.setCurrentIndex(comboIdx)
      TimerStop('populateLedgerCombo')
      

   #############################################################################
   def execDlgWalletDetails(self, index=None):
      if len(self.walletMap)==0:
         reply = QMessageBox.information(self, 'No Wallets!', \
            'You currently do not have any wallets.  Would you like to '
            'create one, now?', QMessageBox.Yes | QMessageBox.No)
         if reply==QMessageBox.Yes:
            self.createNewWallet(initLabel='Primary Wallet')
         return

      if index==None:
         index = self.walletsView.selectedIndexes()
         if len(self.walletMap)==1:
            self.walletsView.selectRow(0)
            index = self.walletsView.selectedIndexes()
         elif len(index)==0:
            QMessageBox.warning(self, 'Select a Wallet', \
               'Please select a wallet on the right, to see its properties.', \
               QMessageBox.Ok)
            return
         index = index[0]
         
      wlt = self.walletMap[self.walletIDList[index.row()]]
      dialog = DlgWalletDetails(wlt, self.usermode, self, self)
      dialog.exec_()
      #self.walletListChanged()
         
         
         
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
   def getAddrCommentIfAvailAll(self, txHash):
      TimerStart('getAddrCommentIfAvail')
      if not TheBDM.isInitialized():
         TimerStop('getAddrCommentIfAvail')
         return ''
      else:
         
         appendedComments = []
         for wltID,wlt in self.walletMap.iteritems():
            cmt = wlt.getAddrCommentIfAvail(txHash)
            if len(cmt)>0:
               appendedComments.append(cmt)
   
         return '; '.join(appendedComments)

         """
         # If we haven't extracted relevant addresses for this tx, yet -- do it
         if not self.txAddrMap.has_key(txHash):
            self.txAddrMap[txHash] = []
            tx = TheBDM.getTxByHash(txHash)
            if tx.isInitialized():
               for i in range(tx.getNumTxOut()):
                  a160 = tx.getRecipientForTxOut(i)
                  wltID = self.getWalletForAddr160(a160)
      
                  if not len(wltID)==0:
                     self.txAddrMap[txHash].append([wltID, tx.getRecipientForTxOut(i)])
            

         addrComments = []
         for wltID,a160 in self.txAddrMap[txHash]:
            wlt = self.walletMap[wltID]
            if wlt.commentsMap.has_key(a160):
               addrComments.append(wlt.commentsMap[a160])

         TimerStop('getAddrCommentIfAvail')
         return '; '.join(addrComments)
         """

                  
   #############################################################################
   def getCommentForLE(self, wltID, le):
      # Smart comments for LedgerEntry objects:  get any direct comments ... 
      # if none, then grab the one for any associated addresses.
       
      return self.walletMap[wltID].getCommentForLE(le)
      """
      txHash = le.getTxHash()
      if wlt.commentsMap.has_key(txHash):
         comment = wlt.commentsMap[txHash]
      else:
         # [[ COMMENTS ]] are not meant to be displayed on main ledger
         comment = self.getAddrCommentIfAvail(txHash)
         if comment.startswith('[[') and comment.endswith(']]'):
            comment = ''

      return comment
      """




   #############################################################################
   def addWalletToApplication(self, newWallet, walletIsNew=True):
      # Update the maps/dictionaries
      newWltID = newWallet.uniqueIDB58

      if self.walletMap.has_key(newWltID):
         return
      
      self.walletMap[newWltID] = newWallet
      self.walletIndices[newWltID] = len(self.walletMap)-1

      # Maintain some linear lists of wallet info
      self.walletIDSet.add(newWltID)
      self.walletIDList.append(newWltID)

      ledger = []
      wlt = self.walletMap[newWltID]
      self.walletListChanged()

      
   #############################################################################
   def removeWalletFromApplication(self, wltID):

      idx = -1
      try:
         idx = self.walletIndices[wltID]
      except KeyError:
         LOGERROR('Invalid wallet ID passed to "removeWalletFromApplication"')
         raise WalletExistsError

      del self.walletMap[wltID]
      del self.walletIndices[wltID]
      self.walletIDSet.remove(wltID)
      del self.walletIDList[idx]

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
                                           longLabel=descr, \
                                           doRegisterWithBDM=False)
      else:
          newWallet = PyBtcWallet().createNewWallet( \
                                           withEncrypt=False, \
                                           shortLabel=name, \
                                           longLabel=descr, \
                                           doRegisterWithBDM=False)


      # And we must unlock it before the first fillAddressPool call
      if newWallet.useEncryption:
         newWallet.unlock(securePassphrase=passwd)

      # We always want to fill the address pool, right away.  
      fillpool = lambda: newWallet.fillAddressPool(doRegister=False)
      DlgExecLongProcess(fillpool, 'Creating Wallet...', self, self).exec_()

      # Reopening from file helps make sure everything is correct -- don't
      # let the user use a wallet that triggers errors on reading it
      wltpath = newWallet.walletPath
      newWallet = None
      newWallet = PyBtcWallet().readWalletFile(wltpath)
      

      self.addWalletToApplication(newWallet, walletIsNew=True)

      if TheBDM.getBDMState() in ('Uninitialized', 'Offline'):
         TheBDM.registerWallet(newWallet, isFresh=True, wait=False)
      else:
         self.newWalletList.append([newWallet, True])
      
      # Prompt user to print paper backup if they requested it.
      if dlg.chkPrintPaper.isChecked():
         dlg = DlgPaperBackup(newWallet, self, self)
         dlg.exec_()






   #############################################################################
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

      utxoList = getUnspentTxOutsForAddrList(addr160List, 'Sweep', 0)
      if len(utxoList)==0:
         return [None, 0, 0]
      
      outValue = sumTxOutList(utxoList)

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
         not self.getSettingOrSetDefault('OverrideMinFee', False):
         LOGDEBUG( 'Subtracting fee from Sweep-output')
         outValue -= minFee

      if outValue<=0:
         return [None, outValue, minFee]

      outputSide = []
      outputSide.append( [PyBtcAddress().createFromPublicKeyHash160(sweepTo160), outValue] )

      pytx = PyCreateAndSignTx(inputSide, outputSide)
      return (pytx, outValue, minFee)


      


   #############################################################################
   def confirmSweepScan(self, pybtcaddrList, targAddr160):

      gt1 = len(self.sweepAfterScanList)>1

      if len(self.sweepAfterScanList) > 0:
         QMessageBox.critical(self, 'Already Sweeping',
            'You are already in the process of scanning the blockchain for '
            'the purposes of sweeping other addresses.  You cannot initiate '
            'sweeping new addresses until the current operation completes. '
            '<br><br>'
            'In the future, you may select "Multiple Keys" when entering '
            'addresses to sweep.  There is no limit on the number that can be '
            'specified, but they must all be entered at once.', QMessageBox.Ok)
         # Destroy the private key data
         for addr in pybtcaddrList:
            addr.binPrivKey32_Plain.destroy()
         return False


      confirmed=False
      if TheBDM.getBDMState() in ('Offline', 'Uninitialized'):
         #LOGERROR('Somehow ended up at confirm-sweep while in offline mode')
         #QMessageBox.info(self, 'Armory is Offline', \
            #'Armory is currently in offline mode.  You must be in online '
            #'mode to initiate the sweep operation.')
         nkey = len(self.sweepAfterScanList)
         strPlur = 'addresses' if nkey>1 else 'address'
         QMessageBox.info(self, 'Armory is Offline', \
            'You have chosen to sweep %d %s, but Armory is currently '
            'in offline mode.  The sweep will be performed the next time you '
            'go into online mode.  You can initiate online mode (if available) '
            'from the dashboard in the main window.' (nkey,strPlur), QMessageBox.Ok)
         confirmed=True

      else:
         msgConfirm = ( \
            'Armory must scan the global transaction history in order to '
            'find any bitcoins associated with the %s you supplied. '
            'Armory will go into offline mode temporarily while the scan '
            'is performed, and you will not have access to balances or be '
            'able to create transactions.  The scan may take several minutes.'
            '<br><br>' % ('keys' if gt1 else 'key'))

         if TheBDM.getBDMState()=='Scanning':
            msgConfirm += ( \
               'There is currently another scan operation being performed.  '
               'Would you like to start the sweep operation after it completes? ')
         elif TheBDM.getBDMState()=='BlockchainReady':
            msgConfirm += ( \
               '<b>Would you like to start the scan operation right now?</b>')
   
         msgConfirm += ('<br><br>Clicking "No" will abort the sweep operation')

         confirmed = QMessageBox.question(self, 'Confirm Rescan', msgConfirm, \
                                                QMessageBox.Yes | QMessageBox.No)

      if confirmed==QMessageBox.Yes:
         for addr in pybtcaddrList:
            TheBDM.registerImportedAddress(addr.getAddr160())
         self.sweepAfterScanList = pybtcaddrList
         self.sweepAfterScanTarg = targAddr160
         TheBDM.rescanBlockchain(wait=False)
         self.setDashboardDetails()
         return True


   #############################################################################
   def finishSweepScan(self):
      sweepList, self.sweepAfterScanList = self.sweepAfterScanList,[]
     
      #######################################################################
      # The createSweepTx method will return instantly because the blockchain
      # has already been rescanned, as described above
      finishedTx, outVal, fee = self.createSweepAddrTx(sweepList, self.sweepAfterScanTarg)
 
      gt1 = len(sweepList)>1

      if finishedTx==None:
         if (outVal,fee)==(0,0):
            QMessageBox.critical(self, 'Nothing to do', \
               'The private %s you have provided does not appear to contain '
               'any funds.  There is nothing to sweep.' % ('keys' if gt1 else 'key'), \
               QMessageBox.Ok)
            return
         else:
            pladdr = ('addresses' if gt1 else 'address')
            QMessageBox.critical(self, 'Cannot sweep',\
               'You cannot sweep the funds from the %s you specified, because '
               'the transaction fee would be equal to or greater than the amount '
               'swept.'
               '<br><br>'
               '<b>Balance of %s:</b> %s<br>'
               '<b>Fee to sweep %s:</b> %s'
               '<br><br>The sweep operation has been canceled.' % (pladdr, pladdr, \
               coin2str(outVal+fee,maxZeros=0), pladdr, coin2str(fee,maxZeros=0)), \
               QMessageBox.Ok)
            LOGERROR('Sweep amount (%s) is less than fee needed for sweeping (%s)', \
                     coin2str(outVal+fee, maxZeros=0), coin2str(fee, maxZeros=0))
            return

      wltID = self.getWalletForAddr160(self.sweepAfterScanTarg)
      wlt = self.walletMap[wltID]
      
      # Finally, if we got here, we're ready to broadcast!
      if gt1:
         dispIn  = '<Multiple Addresses>'
      else:
         dispIn  = 'address <b>%s</b>' % sweepList[0].getAddrStr()
          
      dispOut = 'wallet <b>"%s"</b> (%s) ' % (wlt.labelName, wlt.uniqueIDB58)
      if DlgVerifySweep(dispIn, dispOut, outVal, fee).exec_():
         self.broadcastTransaction(finishedTx, dryRun=False)

      if TheBDM.getBDMState()=='BlockchainReady':
         wlt.syncWithBlockchain(0)

      self.walletListChanged()

   #############################################################################
   def broadcastTransaction(self, pytx, dryRun=False):
      LOGRAWDATA(pytx.serialize(), logging.INFO)
      LOGPPRINT(pytx, logging.INFO)
      if dryRun:
         #DlgDispTxInfo(pytx, None, self, self).exec_()
         return
      else:
         newTxHash = pytx.getHash()
         LOGINFO('Sending Tx, %s', binary_to_hex(newTxHash))
         self.NetworkingFactory.sendTx(pytx)
         LOGINFO('Transaction sent to Satoshi client...!')

         # Wait one sec, then send an inv to the Satoshi
         # client asking for the same tx back.  This has two great benefits:
         #   (1)  The tx was accepted by the network (it'd be dropped if it 
         #        was invalid)
         #   (2)  The memory-pool operations will be handled through existing 
         #        NetworkingFactory code.  Don't need to duplicate anything 
         #        here.
         #time.sleep(1)
         #self.checkForTxInNetwork(pytx.getHash())
      
   
         def sendGetDataMsg():
            msg = PyMessage('getdata')
            msg.payload.invList.append( [MSG_INV_TX, newTxHash] )
            self.NetworkingFactory.sendMessage(msg)

         def checkForTxInBDM():
            # The sleep/delay makes sure we have time to receive a response
            # but it also gives the user a chance to SEE the change to their
            # balance occur.  In some cases, that may be more satisfying than
            # just seeing the updated balance when they get back to the main
            # screen
            if not TheBDM.getTxByHash(newTxHash).isInitialized():
               LOGERROR('Transaction was not accepted by the Satoshi client')
               LOGERROR('Raw transaction:')
               LOGRAWDATA(pytx.serialize(), logging.ERROR)
               LOGERROR('Transaction details')
               LOGPPRINT(pytx, logging.ERROR)
               searchstr = binary_to_hex(newTxHash, BIGENDIAN)
               QMessageBox.warning(self, 'Invalid Transaction', \
                  'The transaction that you just executed, does not '
                  'appear to have been accepted by the Bitcoin network. '
                  'This can happen for a variety of reasons, but it is '
                  'usually due to a bug in the Armory software.  '
                  '<br><br>On some occasions the transaction actually did succeed '
                  'and this message is the bug itself!  To confirm whether the '
                  'the transaction actually succeeded, you can try this direct link '
                  'to blockchain.info:'
                  '<br><br>'
                  '<a href="http://blockchain.info/search/%s">'
                  'http://blockchain.info/search/%s...</a>.  '
                  '<br><br>'
                  'If you do not see the '
                  'transaction on that webpage within one minute, it failed and you '
                  'should attempt to re-send it. '
                  'If it <i>does</i> show up, then you do not need to do anything '
                  'else -- it will show up in Armory as soon as it receives 1 '
                  'confirmation. '
                  '<br><br>If the transaction did fail, please consider '
                  'reporting this error the the Armory '
                  'developers.  From the main window, go to '
                  '"<b>File</b>"-->"<b>Export Log File</b>" to make a copy of your '
                  'log file to send via email to alan.reiner@gmail.com.  ' \
                   % (searchstr,searchstr[:8]), \
                  QMessageBox.Ok)
                  
         self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Transactions)
         reactor.callLater(4, sendGetDataMsg)
         reactor.callLater(5, checkForTxInBDM)

         #QMessageBox.information(self, 'Broadcast Complete!', \
            #'The transaction has been broadcast to the Bitcoin network.  However '
            #'there is no way to know for sure whether it was accepted until you '
            #'see it in the blockchain with 1+ confirmations.  Please search '
            #'www.blockchain.info for the for recipient\'s address, to '
            #'verify whether it was accepted or not.  '
            #'\n\nAlso note: other transactions you send '
            #'from this wallet may not succeed until that first confirmation is '
            #'received.  Both issues are a problem with Armory that will be fixed '
            #'with the next release.', QMessageBox.Ok)

   
      
   #############################################################################
   def warnNoImportWhileScan(self):
      extraMsg = ''
      if not self.usermode==USERMODE.Standard:
         extraMsg = ('<br><br>'
                     'In the future, you may avoid scanning twice by '
                     'starting Armory in offline mode (--offline), and '
                     'perform the import before switching to online mode.')
      QMessageBox.warning(self, 'Armory is Busy', \
         'Wallets and addresses cannot be imported while Armory is in '
         'the middle of an existing blockchain scan.  Please wait for '
         'the scan to finish.  ' + extraMsg, QMessageBox.Ok)
      
            
            
   #############################################################################
   def execImportWallet(self):
      dlg = DlgImportWallet(self, self)
      if dlg.exec_():
         if dlg.importType_file:
            self.execGetImportWltName()
         elif dlg.importType_paper:
            self.execRestorePaperBackup()
         elif dlg.importType_migrate:
            self.execMigrateSatoshi()


   #############################################################################
   def execGetImportWltName(self):
      
      fn = self.getFileLoad('Import Wallet File')
      if not os.path.exists(fn):
         return

      wlt = PyBtcWallet().readWalletFile(fn, verifyIntegrity=False, \
                                             doScanNow=False)
      wltID = wlt.uniqueIDB58
      wlt = None

      if self.walletMap.has_key(wltID):
         QMessageBox.warning(self, 'Duplicate Wallet!', \
            'You selected a wallet that has the same ID as one already '
            'in your wallet (%s)!  If you would like to import it anyway, '
            'please delete the duplicate wallet in Armory, first.'%wltID, \
            QMessageBox.Ok)
         return

      fname = self.getUniqueWalletFilename(fn)
      newpath = os.path.join(ARMORY_HOME_DIR, fname)

      LOGINFO('Copying imported wallet to: %s', newpath)
      shutil.copy(fn, newpath)
      newWlt = PyBtcWallet().readWalletFile(newpath)
      newWlt.fillAddressPool()
      

      if TheBDM.getBDMState() in ('Uninitialized', 'Offline'):
         self.addWalletToApplication(newWlt, walletIsNew=False)
         return
         
      if TheBDM.getBDMState()=='BlockchainReady':
         doRescanNow = QMessageBox.question(self, 'Rescan Needed', \
            'The wallet was imported successfully, but cannot be displayed '
            'until the global transaction history is '
            'searched for previous transactions.  This scan will potentially '
            'take much longer than a regular rescan, and the wallet cannot '
            'be shown on the main display until this rescan is complete.'
            '<br><br>'
            '<b>Would you like to go into offline mode to start this scan now?'
            '</b>  If you click "No" the scan will be aborted, and the wallet '
            'will not be added to Armory.', \
            QMessageBox.Yes | QMessageBox.No)
      else:
         doRescanNow = QMessageBox.question(self, 'Rescan Needed', \
            'The wallet was imported successfully, but its balance cannot '
            'be determined until Armory performs a "recovery scan" for the '
            'wallet.  This scan potentially takes much longer than a regular '
            'scan, and must be completed for all imported wallets. '  
            '<br><br>'
            'Armory is already in the middle of a scan and cannot be interrupted. '
            'Would you like to start the recovery scan when it is done?'
            '<br><br>'
            '</b>  If you click "No," the wallet import will be aborted '
            'and you must re-import the wallet when you ' 
            'are able to wait for the recovery scan.', \
            QMessageBox.Yes | QMessageBox.No)

      if doRescanNow == QMessageBox.Yes:
         LOGINFO('User requested rescan after wallet import')
         TheBDM.startWalletRecoveryScan(newWlt) 
         self.setDashboardDetails()
      else:
         LOGINFO('User aborted the wallet-import scan')
         QMessageBox.warning(self, 'Import Failed', \
            'The wallet was not imported.', QMessageBox.Ok)

         # The wallet cannot exist without also being on disk. 
         # If the user aborted, we should remove the disk data.
         thepath       = newWlt.getWalletPath()
         thepathBackup = newWlt.getWalletPath('backup')
         os.remove(thepath)
         os.remove(thepathBackup)
         return

      #self.addWalletToApplication(newWlt, walletIsNew=False)
      self.newWalletList.append([newWlt, False])
      LOGINFO('Import Complete!')


   #############################################################################
   def execRestorePaperBackup(self):
      #if TheBDM.getBDMState()=='Scanning':
         #self.warnNoImportWhileScan()
         #return

      dlgPaper = DlgImportPaperWallet(self, self)
      if dlgPaper.exec_():

         LOGINFO('Raw import successful.')
         
         # If we are offline, then we can't assume there will ever be a 
         # rescan.  Just add the wallet to the application
         if TheBDM.getBDMState() in ('Uninitialized', 'Offline'):
            self.addWalletToApplication(dlgPaper.newWallet, walletIsNew=False)
            return
         
         elif TheBDM.getBDMState()=='BlockchainReady':
            doRescanNow = QMessageBox.question(self, 'Rescan Needed', \
               'The wallet was recovered successfully, but cannot be displayed '
               'until the global transaction history is '
               'searched for previous transactions.  This scan will potentially '
               'take much longer than a regular rescan, and the wallet cannot '
               'be shown on the main display until this rescan is complete.'
               '<br><br>'
               '<b>Would you like to go into offline mode to start this scan now?'
               '</b>  If you click "No" the scan will be aborted, and the wallet '
               'will not be added to Armory.', \
               QMessageBox.Yes | QMessageBox.No)
         else:
            doRescanNow = QMessageBox.question(self, 'Rescan Needed', \
               'The wallet was recovered successfully, but cannot be displayed '
               'until a special kind of rescan is performed to find previous '
               'transactions.  However, Armory is currently in the middle of '
               'a scan.  Would you like to start the recovery scan immediately '
               'afterwards?'
               '<br><br>'
               '</b>  If you click "No" the scan will be aborted, and the wallet '
               'will not be added to Armory.  Restore the wallet again when you '
               'are able to wait for the recovery scan.', \
               QMessageBox.Yes | QMessageBox.No)

         if doRescanNow == QMessageBox.Yes:
            LOGINFO('User requested rescan after wallet restore')
            TheBDM.startWalletRecoveryScan(dlgPaper.newWallet) 
            self.setDashboardDetails()
         else:
            LOGINFO('User aborted the wallet-recovery scan')
            QMessageBox.warning(self, 'Import Failed', \
               'The wallet was not restored.  To restore the wallet, reenter '
               'the "Restore Wallet" dialog again when you are able to wait '
               'for the rescan operation.  ', QMessageBox.Ok)
            # The wallet cannot exist without also being on disk. 
            # If the user aborted, we should remove the disk data.
            thepath       = dlgPaper.newWallet.getWalletPath()
            thepathBackup = dlgPaper.newWallet.getWalletPath('backup')
            os.remove(thepath)
            os.remove(thepathBackup)
            return

         self.addWalletToApplication(dlgPaper.newWallet, walletIsNew=False)
         #self.newWalletList.append([dlgPaper.newWallet, False])
         LOGINFO('Import Complete!')
   
   #############################################################################
   def execMigrateSatoshi(self):
      reply = MsgBoxCustom(MSGBOX.Question, 'Wallet Version Warning', \
           'This wallet migration tool only works with regular Bitcoin wallets '
           'produced using version 0.5.X and earlier.  '
           'You can determine the version by '
           'opening the regular Bitcoin client, then choosing "Help"'
           '-->"About Bitcoin-Qt" from the main menu.  '
           '<br><br>'
           '<b>If you have used your wallet with any version of the regular '
           'Bitcoin client 0.6.0 or higher, this tool <u>will fail</u></b>.  '
           'In fact, it is highly recommended that you do not even attempt '
           'to use the tool on such wallets until it is officially supported '
           'by Armory.'
           '<br><br>'
           'Has your wallet ever been opened in the 0.6.0+ Bitcoin-Qt client?', \
           yesStr='Yes, Abort!', noStr='No, Carry On!')
            
      if reply:
         return

      DlgMigrateSatoshiWallet(self, self).exec_()



   #############################################################################
   def execAddressBook(self):
      if TheBDM.getBDMState()=='Scanning':
         QMessageBox.warning(self, 'Blockchain Not Ready', \
            'The address book is created from transaction data available in '
            'the blockchain, which has not finished loading.  The address '
            'book will become available when Armory is online.', QMessageBox.Ok)
      elif TheBDM.getBDMState() in ('Uninitialized','Offline'):
         QMessageBox.warning(self, 'Blockchain Not Ready', \
            'The address book is created from transaction data available in '
            'the blockchain, but Armory is currently offline.  The address '
            'book will become available when Armory is online.', QMessageBox.Ok)
      else:
         if len(self.walletMap)==0:
            QMessageBox.warning(self, 'No wallets!', 'You have no wallets so '
               'there is no address book to display.', QMessageBox.Ok)
            return
         DlgAddressBook(self, self, None, None, None).exec_()


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
         self.showLedgerTx()


   #############################################################################
   def showLedgerTx(self):
      row = self.ledgerView.selectedIndexes()[0].row()
      txHash = str(self.ledgerView.model().index(row, LEDGERCOLS.TxHash).data().toString())
      wltID  = str(self.ledgerView.model().index(row, LEDGERCOLS.WltID).data().toString())
      txtime = unicode(self.ledgerView.model().index(row, LEDGERCOLS.DateStr).data().toString())

      pytx = None
      txHashBin = hex_to_binary(txHash)
      if TheBDM.isInitialized():
         cppTx = TheBDM.getTxByHash(txHashBin)
         if cppTx.isInitialized():
            pytx = PyTx().unserialize(cppTx.serialize())

      if pytx==None:
         QMessageBox.critical(self, 'Invalid Tx:',
         'The transaction you requested be displayed does not exist in '
         'in Armory\'s database.  This is unusual...', QMessageBox.Ok)
         return

      DlgDispTxInfo( pytx, self.walletMap[wltID], self, self, txtime=txtime).exec_()


   #############################################################################
   def showContextMenuLedger(self):
      menu = QMenu(self.ledgerView)
   
      if len(self.ledgerView.selectedIndexes())==0:
         return
      
      actViewTx     = menu.addAction("View Details")
      actViewBlkChn = menu.addAction("View on www.blockchain.info")
      actComment    = menu.addAction("Change Comment")
      actCopyTxID   = menu.addAction("Copy Transaction ID")
      actOpenWallet = menu.addAction("Open Relevant Wallet")
      row = self.ledgerView.selectedIndexes()[0].row()
      action = menu.exec_(QCursor.pos())

      txHash = str(self.ledgerView.model().index(row, LEDGERCOLS.TxHash).data().toString())
      txHash = hex_switchEndian(txHash)
      wltID  = str(self.ledgerView.model().index(row, LEDGERCOLS.WltID).data().toString())

      blkchnURL = 'http://blockchain.info/tx/%s' % txHash

      if action==actViewTx:
         self.showLedgerTx()
      elif action==actViewBlkChn:
         try:
            import webbrowser
            webbrowser.open(blkchnURL)
         except: 
            QMessageBox.critical(self, 'Could not open browser', \
               'Armory encountered an error opening your web browser.  To view '
               'this transaction on blockchain.info, please copy and paste '
               'the following URL into your browser: '
               '<br><br>%s' % blkchnURL, QMessageBox.Ok)
      elif action==actCopyTxID:
         clipb = QApplication.clipboard()
         clipb.clear()
         clipb.setText(txHash)
      elif action==actComment:
         self.updateTxCommentFromView(self.ledgerView)
      elif action==actOpenWallet:
         DlgWalletDetails(self.walletMap[wltID], self.usermode, self, self).exec_()



   #############################################################################
   def clickSendBitcoins(self):
      if TheBDM.getBDMState() in ('Offline', 'Uninitialized'):
         QMessageBox.warning(self, 'Offline Mode', \
           'Armory is currently running in offline mode, and has no '
           'ability to determine balances or create transactions. '
           '<br><br>'
           'In order to send coins from this wallet you must use a '
           'full copy of this wallet from an online computer, '
           'or initiate an "offline transaction" using a watching-only '
           'wallet on an online computer.', QMessageBox.Ok)
         return
      elif TheBDM.getBDMState()=='Scanning':
         QMessageBox.warning(self, 'Armory Not Ready', \
           'Armory is currently scanning the blockchain to collect '
           'the information needed to create transactions.  This typically '
           'takes between one and five minutes.  Please wait until your '
           'balance appears on the main window, then try again.', \
            QMessageBox.Ok)
         return

      wltID = None
      selectionMade = True
      if len(self.walletMap)==0:
         reply = QMessageBox.information(self, 'No Wallets!', \
            'You cannot send any bitcoins until you create a wallet and '
            'receive some coins.  Would you like to create a wallet?', \
            QMessageBox.Yes | QMessageBox.No)
         if reply==QMessageBox.Yes:
            self.createNewWallet(initLabel='Primary Wallet')
         return
      elif len(self.walletMap)==1:
         wltID = self.walletMap.keys()[0]
      else:
         wltSelect = self.walletsView.selectedIndexes()
         if len(wltSelect)>0:
            row = wltSelect[0].row()
            wltID = str(self.walletsView.model().index(row, WLTVIEWCOLS.ID).data().toString())
         dlg = DlgWalletSelect(self, self, 'Send from Wallet...', firstSelect=wltID, onlyMyWallets=False)
         if dlg.exec_():
            wltID = dlg.selectedID 
         else:
            selectionMade = False

      if selectionMade:
         wlt = self.walletMap[wltID]
         wlttype = determineWalletType(wlt, self)[0]
         dlgSend = DlgSendBitcoins(wlt, self, self)
         dlgSend.exec_()
   

   #############################################################################
   def uriSendBitcoins(self, uriDict):
      # Because Bitcoin-Qt doesn't store the message= field we have to assume
      # that the label field holds the Tx-info.  So we concatenate them for 
      # the display message
      uri_has = lambda s: uriDict.has_key(s)

      haveLbl = uri_has('label')
      haveMsg = uri_has('message')

      newMsg = '' 
      if haveLbl and haveMsg:
         newMsg = uriDict['label'] + ': ' + uriDict['message']
      elif not haveLbl and haveMsg:
         newMsg = uriDict['message']
      elif haveLbl and not haveMsg:
         newMsg = uriDict['label']
      
      descrStr = ''
      descrStr = ('You just clicked on a "bitcoin:" link requesting bitcoins ' 
                'to be sent to the following address:<br> ')

      descrStr += '<br>--<b>Address</b>:\t%s ' % uriDict['address']

      #if uri_has('label'):
         #if len(uriDict['label'])>30:
            #descrStr += '(%s...)' % uriDict['label'][:30]
         #else:
            #descrStr += '(%s)' % uriDict['label']

      amt = 0
      if uri_has('amount'):
         amt     = uriDict['amount']
         amtstr  = coin2str(amt, maxZeros=1)
         descrStr += '<br>--<b>Amount</b>:\t%s BTC' % amtstr


      if newMsg:
         if len(newMsg)>60:
            descrStr += '<br>--<b>Message</b>:\t%s...' % newMsg[:60]
         else:
            descrStr += '<br>--<b>Message</b>:\t%s' % newMsg

      uriDict['message'] = newMsg
      
      if not uri_has('amount'):
          descrStr += ('<br><br>There is no amount specified in the link, so '
            'you can decide the amount after selecting a wallet to use '
            'for this this transaction. ')
      else:
          descrStr += ('<br><br><b>The specified amount <u>can</u> be changed</b> on the '
            'next screen before hitting the "Send" button. ')


      selectedWalletID = None
      if len(self.walletMap)==0:
         reply = QMessageBox.information(self, 'No Wallets!', \
            'You just clicked on a "bitcoin:" link to send money, but you '
            'currently have no wallets!  Would you like to create a wallet '
            'now?', QMessageBox.Yes | QMessageBox.No)
         if reply==QMessageBox.Yes:
            self.createNewWallet(initLabel='Primary Wallet')
         return False
      elif len(self.walletMap)>1:
         dlg = DlgWalletSelect(self, self, 'Send from Wallet...', descrStr, \
                               onlyMyWallets=True, atLeast=amt)
         if not dlg.exec_():
            return False
         selectedWalletID = dlg.selectedID
      else:
         selectedWalletID = self.walletIDList[0]
         
      wlt = self.walletMap[selectedWalletID]
      dlgSend = DlgSendBitcoins(wlt, self, self, uriDict)
      dlgSend.exec_()
      return True
      

   #############################################################################
   def clickReceiveCoins(self):
      LOGDEBUG('Clicked "Receive Bitcoins Button"')
      wltID = None
      selectionMade = True
      if len(self.walletMap)==0:
         reply = QMessageBox.information(self, 'No Wallets!', \
            'You have not created any wallets which means there is nowhere to '
            'store you bitcoins!  Would you like to create a wallet now?', \
            QMessageBox.Yes | QMessageBox.No)
         if reply==QMessageBox.Yes:
            self.createNewWallet(initLabel='Primary Wallet')
         return
      elif len(self.walletMap)==1:
         wltID = self.walletMap.keys()[0]
      else:
         wltSelect = self.walletsView.selectedIndexes()
         if len(wltSelect)>0:
            row = wltSelect[0].row()
            wltID = str(self.walletsView.model().index(row, WLTVIEWCOLS.ID).data().toString())
         dlg = DlgWalletSelect(self, self, 'Receive coins with wallet...', '', firstSelect=wltID, onlyMyWallets=False)
         if dlg.exec_():
            wltID = dlg.selectedID 
         else:
            selectionMade = False

      if selectionMade:
         wlt = self.walletMap[wltID]
         wlttype = determineWalletType(wlt, self)[0]
         if showWatchOnlyRecvWarningIfNecessary(wlt, self):
            DlgNewAddressDisp(wlt, self, self).exec_()



   #############################################################################
   def sysTrayActivated(self, reason):
      if reason==QSystemTrayIcon.DoubleClick:
         self.bringArmoryToFront()

      

   #############################################################################
   def bringArmoryToFront(self):
      self.show()
      self.setWindowState(Qt.WindowActive)
      self.activateWindow()
      self.raise_()

   #############################################################################
   def minimizeArmory(self):
      LOGDEBUG('Minimizing Armory')
      self.hide()
      self.sysTray.show()

   #############################################################################
   def exportLogFile(self):
      extraStr = ''
      if self.usermode in (USERMODE.Advanced, USERMODE.Expert):
         extraStr = ( \
            '<br><br><b><u>Advanced tip:</u></b> This log file is maintained at '
            'the following location on your hard drive:'
            '<br><br>'
            '%s'
            '<br><br>'
            'Before sending the log file, you may edit it to remove information that '
            'does not seem relevant for debugging purposes.  Or, extract the error '
            'messages from the log file and copy only those into a bug report email ' % \
            ARMORY_LOG_FILE)
            
      #reply = QMessageBox.warning(self, 'Export Log File', \
      reply = MsgBoxCustom(MSGBOX.Warning, 'Privacy Warning', \
         'The log file contains information that may be considered sensitive '
         'by some users.  Log files should be protected the same '
         'way you would protect a watching-only wallet, though it '
         'usually contains much less information than that. '
         '<br><br>'
         '<b>No private key data is ever written to the log file</b>. '
         'All logged information is geared towards diagnosing '
         'problems you may encounter while you use Armory.  '  
         'Some information about your wallets or balances may appear '
         'in the log file, but only enough to help the Armory developers '
         'track down bugs in the software.'
         '<br><br>'
         'Please do not send the log file to the Armory developers if you are not '
         'comfortable with the privacy implications.' + extraStr, \
         wCancel=True, yesStr='Export', noStr='Cancel')
         

      if reply:
         defaultFn = 'armorylog_%s.txt' % unixTimeToFormatStr(RightNow(), '%Y%m%d_%H%M')
         logfn = self.getFileSave(title='Export Log File', \
                                  ffilter=['Text Files (*.txt)'], \
                                  defaultFilename=defaultFn)
         if len(str(logfn)) > 0:
            shutil.copy(ARMORY_LOG_FILE, logfn)
            LOGINFO('Log saved to %s', logfn)

   #############################################################################
   def blinkTaskbar(self):
      self.activateWindow()
      

   #############################################################################
   def lookForBitcoind(self):
      if satoshiIsAvailable():
         return 'Running'
      
      satexe = None
      if self.settings.hasSetting('SatoshiExe'):
         satexe = [self.settings.get('SatoshiExe')]
      else:
         satexe = []

      try:
         TheSDM.setupSDM(extraExeSearch=satexe)
      except:
         pass

      if TheSDM.failedFindExe:
         return 'StillMissing'

      return 'AllGood'

   #############################################################################
   def pressModeSwitchButton(self):

      print self.doManageSatoshi
      print not TheSDM.isRunningBitcoind()
      print satoshiIsAvailable()
      if TheSDM.getSDMState() == 'BitcoindExeMissing':
         result = self.lookForBitcoind()
         if result=='Running':
            QMessageBox.warning(self, 'Already running!', \
               'The Bitcoin software appears to be installed now, but you '
               'must close it in order for Armory to work.', QMessageBox.Ok)
         elif result=='StillMissing':
            QMessageBox.warning(self, 'Still Missing', \
               'The Bitcoin software still appears to be missing.  If you '
               'just installed it, then please adjust your settings to point '
               'to the installation directory.', QMessageBox.Ok)
         self.startBitcoindIfNecessary() 
      elif self.doManageSatoshi and not TheSDM.isRunningBitcoind():
         if satoshiIsAvailable():
            QMessageBox.warning(self, 'Still Running', \
               'Bitcoin-Qt is still running.  Armory cannot start until '
               'it is closed.', QMessageBox.Ok)
         else:
            self.startBitcoindIfNecessary() 
      elif TheBDM.getBDMState() == 'BlockchainReady' and TheBDM.isDirty():
         self.startRescanBlockchain()
      elif TheBDM.getBDMState() in ('Offline','Uninitialized'):
         self.resetBdmBeforeScan()
         TheBDM.setOnlineMode(True)
         self.switchNetworkMode(NETWORKMODE.Full)
      else:
         LOGERROR('ModeSwitch button pressed when it should be disabled')
      time.sleep(0.3)
      self.setDashboardDetails()


      
   
   #############################################################################
   def resetBdmBeforeScan(self):
      """
      I have spend hours trying to debug situations where starting a scan or 
      rescan fails, and still not found the reason.  However, it always seems
      to work after a reset and re-register of all addresses/wallets.  
      """
      TimerStart("resetBdmBeforeScan")
      TheBDM.Reset(wait=False)
      for wid,wlt in self.walletMap.iteritems():
         TheBDM.registerWallet(wlt.cppWallet)
      TimerStop("resetBdmBeforeScan")



   #############################################################################
   def SetupDashboard(self):

      self.lblBusy = QLabel('')
      if OS_WINDOWS:
         # Unfortunately, QMovie objects don't work in Windows with py2exe
         # had to create my own little "Busy" icon and hook it up to the 
         # heartbeat
         self.lblBusy.setPixmap(QPixmap(':/loadicon_0.png'))
         self.numHeartBeat = 0
         def loadBarUpdate():
            if self.lblBusy.isVisible():
               self.numHeartBeat += 1
               self.lblBusy.setPixmap(QPixmap(':/loadicon_%d.png' % \
                                                (self.numHeartBeat%6)))
         self.extraHeartbeatAlways.append(loadBarUpdate)
      else:
         self.qmov = QMovie(':/busy.gif')
         self.lblBusy.setMovie( self.qmov )
         self.qmov.start()


      self.btnModeSwitch = QPushButton('')
      self.connect(self.btnModeSwitch, SIGNAL('clicked()'), \
                                       self.pressModeSwitchButton)

      # Will switch this to array/matrix of widgets if I get more than 2 rows
      self.lblDashModeSync = QRichLabel('',doWrap=False)
      self.lblDashModeScan = QRichLabel('',doWrap=False)
      self.lblDashModeSync.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
      self.lblDashModeScan.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

      self.barProgressSync = QProgressBar(self)
      self.barProgressScan = QProgressBar(self)
      self.barProgressSync.setRange(0,100)
      self.barProgressScan.setRange(0,100)

      twid = relaxedSizeStr(self,'99 seconds')[0]
      self.lblTimeLeftSync = QRichLabel('')
      self.lblTimeLeftScan = QRichLabel('')
      self.lblTimeLeftSync.setMinimumWidth(twid)
      self.lblTimeLeftScan.setMinimumWidth(twid)

      layoutDashMode = QGridLayout()
      layoutDashMode.addWidget(self.lblDashModeSync,  0,0)
      layoutDashMode.addWidget(self.barProgressSync,  0,1)
      layoutDashMode.addWidget(self.lblTimeLeftSync,  0,2)
      layoutDashMode.addWidget(self.lblDashModeScan,  1,0)
      layoutDashMode.addWidget(self.barProgressScan,  1,1)
      layoutDashMode.addWidget(self.lblTimeLeftScan,  1,2)
      layoutDashMode.addWidget(self.lblBusy,          0,3, 2,1)
      layoutDashMode.addWidget(self.btnModeSwitch,    0,3, 2,1)
      self.frmDashModeSub = QFrame()
      self.frmDashModeSub.setFrameStyle(STYLE_SUNKEN)
      self.frmDashModeSub.setLayout(layoutDashMode)
      self.frmDashMode = makeHorizFrame(['Stretch', \
                                         self.frmDashModeSub, \
                                         'Stretch'])

      
      self.lblDashDescr1 = QRichLabel('')
      self.lblDashDescr2 = QRichLabel('')
      for lbl in [self.lblDashDescr1, self.lblDashDescr2]:
         # One textbox above buttons, one below
         lbl.setStyleSheet('padding: 5px')
         qpal = lbl.palette()
         qpal.setColor(QPalette.Base, Colors.Background)
         lbl.setPalette(qpal)
         lbl.setOpenExternalLinks(True)

      # Set up an array of buttons in the middle of the dashboard, to be used 
      # to help the user install bitcoind.
      self.lblDashBtnDescr = QRichLabel('')
      BTN,LBL,TTIP = range(3)
      self.dashBtns = [[None]*3 for i in range(5)]
      self.dashBtns[DASHBTNS.Browse  ][BTN] = QPushButton('Open www.bitcoin.org')
      self.dashBtns[DASHBTNS.Install ][BTN] = QPushButton('Install Bitcoin Software')
      self.dashBtns[DASHBTNS.Instruct][BTN] = QPushButton('Installation Instructions')
      self.dashBtns[DASHBTNS.Settings][BTN] = QPushButton('Change Settings')
      self.dashBtns[DASHBTNS.Close   ][BTN] = QPushButton('Close Bitcoin Process')


      #####
      def openBitcoinOrg(): 
         import webbrowser
         webbrowser.open('http://www.bitcoin.org/en/download')


      #####
      def openInstruct():
         import webbrowser
         if OS_WINDOWS:
            webbrowser.open('https://www.bitcoinarmory.com/install-windows/')
         elif OS_LINUX:
            webbrowser.open('https://www.bitcoinarmory.com/install-linux/')
         elif OS_MACOSX:
            webbrowser.open('https://www.bitcoinarmory.com/install-macosx/')


      #####
      def installUbuntu():
         result = QMessageBox.information(self, 'Install Bitcoin', \
            'This automatic Bitcoin installation only works on default Ubuntu '
            '(using Unity or Gnome) and probably other Debian-based distros. '
            'If this operation fails, please use the '
            'manual installation instructions and restart Armory.<br><br>'
            'Armory may appear unresponsive for a minute while installing. '
            'Would you like to continue?', \
            QMessageBox.Yes, QMessageBox.No)
         if result==QMessageBox.Yes:
            tryInstallUbuntu(self)

      #####
      def installWindows():
         if not 'SATOSHI' in self.downloadDict or \
            not 'Windows' in self.downloadDict['SATOSHI']:
            QMessageBox.warning(self, 'Verification Unavaiable', \
               'Armory cannot verify the authenticity of any downloaded '
               'files.  You will need t download it yourself from '
               'bitcoin.org', QMessageBox.Ok)
            self.dashBtns[DASHBTNS.Install][BTN].setEnabled(False)
            self.dashBtns[DASHBTNS.Install][LBL].setText( \
               'This option is currently unavailable.  Please visit bitcoin.org '
               'to download and install the software.', color='DisableFG')
            self.dashBtns[DASHBTNS.Install][TTIP] = createToolTipObject( \
               'Armory has an internet connection but no way to verify '
               'the authenticity of the downloaded files.  You should '
               'download the installer yourself.')
            openBitcoinOrg()
            return
            
         print self.downloadDict['SATOSHI']['Windows']
         theLink = self.downloadDict['SATOSHI']['Windows'][0]
         theHash = self.downloadDict['SATOSHI']['Windows'][1]
         dlg = DlgDownloadFile(self, self, theLink, theHash)
         dlg.exec_()
         fileData = dlg.dlFileData
         if len(fileData)==0 or dlg.dlVerifyFailed:
            QMessageBox.critical(self, 'Download Failed', \
               'The download failed.  Please visit www.bitcoin.org '
               'to download and install Bitcoin-Qt manually.', QMessageBox.Ok)
            openBitcoinOrg()
            return
         
         installerPath = os.path.join(ARMORY_HOME_DIR, os.path.basename(theLink))
         LOGINFO('Installer path: %s', installerPath)
         instFile = open(installerPath, 'wb')
         instFile.write(fileData)
         instFile.close()
         subprocess.Popen('"'+installerPath+'"', shell=True, **ALLPIPE)


      #####
      def installForMe():
         if   OS_WINDOWS: installWindows()
         elif OS_LINUX:   installUbuntu()
         elif OS_MACOSX:  installMacOSX()
            

      self.connect(self.dashBtns[DASHBTNS.Browse][BTN], SIGNAL('clicked()'), \
                                                               openBitcoinOrg)
      self.connect(self.dashBtns[DASHBTNS.Install][BTN], SIGNAL('clicked()'), \
                                                               installForMe)
      self.connect(self.dashBtns[DASHBTNS.Settings][BTN], SIGNAL('clicked()'), \
                                                             self.openSettings)
      self.connect(self.dashBtns[DASHBTNS.Instruct][BTN], SIGNAL('clicked()'), \
                                                      self.openInstructWindow) 

      self.dashBtns[DASHBTNS.Browse][LBL]     = QRichLabel( \
           'Open browser to Bitcoin webpage to download and install Bitcoin software')
      self.dashBtns[DASHBTNS.Instruct][LBL] = QRichLabel( \
           'Show installation instructions for your operating system')
      self.dashBtns[DASHBTNS.Settings][LBL]  = QRichLabel( \
           'Open Armory settings window to change Bitcoin software management')
      self.dashBtns[DASHBTNS.Close][LBL] = QRichLabel( \
           'Stop existing Bitcoin processes so that Armory can open its own')


      self.dashBtns[DASHBTNS.Browse][TTIP] = createToolTipObject( \
           'Will open your default browser to http://www.bitcoin.org where you can '
           'download the latest version of Bitcoin-Qt, and get other information '
           'and links about Bitcoin, in general.')
      self.dashBtns[DASHBTNS.Instruct][TTIP] = createToolTipObject( \
           'Instructions are specific to your operating system and include '
           'information to help you verify you are installing the correct software')
      self.dashBtns[DASHBTNS.Settings][TTIP] = createToolTipObject( \
           'Change Bitcoin-Qt/bitcoind management settings or point Armory to '
           'a non-standard Bitcoin installation')
      self.dashBtns[DASHBTNS.Close][TTIP] = createToolTipObject( \
           'Armory has detected a running Bitcoin-Qt or bitcoind instance and '
           'will force it to exit')

      self.dashBtns[DASHBTNS.Install][BTN].setEnabled(False)
      self.dashBtns[DASHBTNS.Install][LBL] = QRichLabel('')
      self.dashBtns[DASHBTNS.Install][LBL].setText( \
          'This option is not yet available yet!', color='DisableFG')
      self.dashBtns[DASHBTNS.Install][TTIP] = QRichLabel('') # disabled

      #if OS_LINUX:
      if OS_WINDOWS:
         self.dashBtns[DASHBTNS.Install][BTN].setEnabled(True)
         self.dashBtns[DASHBTNS.Install][LBL] = QRichLabel('')
         self.dashBtns[DASHBTNS.Install][LBL].setText( \
            'Securely download Bitcoin software for Windows %s' % OS_VARIANT[0])
         self.dashBtns[DASHBTNS.Install][TTIP] = createToolTipObject( \
            'The downloaded files are cryptographically verified.  '
            'Using this option will start the installer, you will '
            'have to click through it to complete installation.')

         #self.lblDashInstallForMe = QRichLabel( \
           #'Armory will download, verify, and start the Bitcoin installer for you')
         #self.ttipInstallForMe = createToolTipObject( \
           #'Armory will download the latest version of the Bitcoin software '
           #'for Windows and verify its digital signatures.  You will have to '
           #'click through the installation options.<u></u>')
      elif OS_LINUX:
         # Only display the install button if using a debian-based distro
         dist = platform.linux_distribution()
         if dist[0] in ['Ubuntu','LinuxMint'] or 'debian' in dist:
            self.dashBtns[DASHBTNS.Install][BTN].setEnabled(True)
            self.dashBtns[DASHBTNS.Install][LBL] = QRichLabel( \
               'Attempt automatic installation for Ubuntu/Debian')
            self.dashBtns[DASHBTNS.Install][TTIP] = createToolTipObject( \
               'Debian-based Linux distributions can use the PPA to '
               'install and maintain the core Bitcoin-Qt software')
      elif OS_MACOSX:
         pass
      else:
         print 'Unrecognized OS!'
   

      self.frmDashMgmtButtons = QFrame()
      self.frmDashMgmtButtons.setFrameStyle(STYLE_SUNKEN)
      layoutButtons = QGridLayout()
      layoutButtons.addWidget(self.lblDashBtnDescr, 0,0, 1,3)
      for r in range(5):
         for c in range(3):
            if c==LBL:
               wMin = tightSizeNChar(self, 50)[0]
               self.dashBtns[r][c].setMinimumWidth(wMin)
            layoutButtons.addWidget(self.dashBtns[r][c],  r+1,c)
            
      self.frmDashMgmtButtons.setLayout(layoutButtons)
      self.frmDashMidButtons  = makeHorizFrame(['Stretch', \
                                              self.frmDashMgmtButtons, 
                                              'Stretch'])

      dashLayout = QVBoxLayout()
      dashLayout.addWidget(self.frmDashMode)
      dashLayout.addWidget(self.lblDashDescr1)
      dashLayout.addWidget(self.frmDashMidButtons )
      dashLayout.addWidget(self.lblDashDescr2)
      frmInner = QFrame()
      frmInner.setLayout(dashLayout)

      self.scrl = QScrollArea()
      self.scrl.setWidgetResizable(True)
      self.scrl.setWidget(frmInner)
      scrollLayout = QVBoxLayout()
      scrollLayout.addWidget(self.scrl)
      self.tabDashboard.setLayout(scrollLayout)

   #############################################################################
   def openInstructWindow(self):
      if OS_WINDOWS:
         DlgInstallWindows(self, self).exec_()
      elif OS_LINUX:
         DlgInstallLinux(self,self).exec_()
      elif OS_MACOSX:
         DlgInstallMacOSX(self,self).exec_()

   #############################################################################
   def getPercentageFinished(self, maxblk, lastblk):
      # The X^8 relationship is surprisingly accurate
      return min((float(lastblk)/float(maxblk))**7, 0.99)
      #raise NotImplementedError 
      #from blkdensitytable import blkDensTable
      #sz = len(blkDensTable)
      #if not self.blockTimeHist:

   #############################################################################
   def updateSyncProgress(self):

      if TheBDM.getBDMState()=='Scanning':
         # Scan time is super-simple to predict: it's pretty much linear
         # with the number of bytes remaining.
         pct,rate,tleft = TheBDM.predictLoadTime()
         self.barProgressSync.setValue(100)
         tleft15 = (int(tleft-1)/15 + 1)*15
         if tleft < 2:
            self.lblTimeLeftScan.setText('')
            self.barProgressScan.setValue(1)
         else:
            self.lblTimeLeftScan.setText(secondsToHumanTime(tleft15))
            self.barProgressScan.setValue(pct*100)
      elif TheSDM.getSDMState() in ['BitcoindInitializing','BitcoindSynchronizing']:
         ssdm = TheSDM.getSDMState() 
         lastBlkNum  = self.getSettingOrSetDefault('LastBlkRecv',     0)
         lastBlkTime = self.getSettingOrSetDefault('LastBlkRecvTime', 0)
   
         # Get data from SDM if it has it
         info = TheSDM.getTopBlockInfo()
         if len(info['tophash'])>0:
            lastBlkNum  = info['numblks']
            lastBlkTime = info['toptime']
   
         # Use a reference point if we are starting from scratch
         refBlock = max(226609,      lastBlkNum)
         refTime  = max(1363636591,  lastBlkTime)
   
         # Ten min/block is pretty accurate, even at genesis blk (about 1% slow)
         self.approxMaxBlock = refBlock + int((RightNow() - refTime) / (10*MINUTE))
         self.approxBlkLeft  = self.approxMaxBlock - lastBlkNum
         self.approxPctSoFar = self.getPercentageFinished(self.approxMaxBlock, \
                                                                  lastBlkNum)

         
         intPct = int(100*self.approxPctSoFar)
         strPct = '%d%%' % intPct
   
         self.barProgressSync.setFormat('%p%')
         if ssdm == 'BitcoindReady':
            return (0,0,0.99)  # because it's probably not completely done...
            self.lblTimeLeftSync.setText('Almost Done...')
            self.barProgressSync.setValue(99)
         elif ssdm == 'BitcoindSynchronizing':
            if info['blkspersec'] > 0:
               if self.approxBlkLeft < 10000:
                  timeleft = int(self.approxBlkLeft/info['blkspersec'])
                  if timeleft < 2*MINUTE:
                     self.lblTimeLeftSync.setText('1-2 minutes')
                  else:
                     self.lblTimeLeftSync.setText('')
                     #self.lblTimeLeftSync.setText(secondsToHumanTime(timeleft))
                  #ratioDone = 1 - float(self.approxBlkLeft)/float(self.approxMaxBlock)
                  self.barProgressSync.setValue(int(99.9*self.approxPctSoFar))
               else:
                  # If we're way behind (like initial sync)
                  self.barProgressSync.setValue(int(100*self.approxPctSoFar))
                  #self.lblTimeLeftSync.setText('Calculating time...')
            else:
               self.barProgressSync.setValue(int(100*self.approxPctSoFar))
               #self.lblTimeLeftSync.setText('Calculating time...')
         elif ssdm == 'BitcoindInitializing':
            self.barProgressSync.setValue(0)
            self.barProgressSync.setFormat('')
         else:
            LOGERROR('Should not predict sync info in non init/sync SDM state')
            return ('UNKNOWN','UNKNOWN', 'UNKNOWN')
      else:
         LOGWARN('Called updateSyncProgress while not sync\'ing')


   #############################################################################
   def GetDashFunctionalityText(self, func):
      """
      Outsourcing all the verbose dashboard text to here, to de-clutter the   
      logic paths in the setDashboardDetails function
      """
      LOGINFO('Switching Armory functional mode to "%s"', func)
      if func.lower() == 'scanning':
         return ( \
         'The following functionality is available while scanning in offline mode:'
         '<ul>'
         '<li>Create new wallets</li>'
         '<li>Generate receiving addresses for your wallets</li>'
         '<li>Create backups of your wallets (printed or digital)</li>'
         '<li>Change wallet encryption settings</li>'
         '<li>Sign transactions created from an online system</li>'
         '<li>Sign messages</li>'
         '</ul>'
         '<br><br><b>NOTE:</b>  The Bitcoin network <u>will</u> process transactions '
         'to your addresses, even if you are offline.  It is perfectly '
         'okay to create and distribute payment addresses while Armory is offline, '
         'you just won\'t be able to verify those payments until the next time '
         'Armory is online.')
      elif func.lower() == 'offline':
         return ( \
         'The following functionality is available in offline mode:'
         '<ul>'
         '<li>Create, import or recover wallets</li>'
         '<li>Generate new receiving addresses for your wallets</li>'
         '<li>Create backups of your wallets (printed or digital)</li>'
         '<li>Import private keys to wallets</li>'
         '<li>Change wallet encryption settings</li>'
         '<li>Sign messages</li>'
         '<li><b>Sign transactions created from an online system</b></li>'
         '</ul>'
         '<br><br><b>NOTE:</b>  The Bitcoin network <u>will</u> process transactions '
         'to your addresses, regardless of whether you are online.  It is perfectly '
         'okay to create and distribute payment addresses while Armory is offline, '
         'you just won\'t be able to verify those payments until the next time '
         'Armory is online.')
      elif func.lower() == 'online':
         return ( \
         '<ul>'
         '<li>Create, import or recover Armory wallets</li>'
         '<li>Generate new addresses to receive coins</li>'
         '<li>Send bitcoins to other people</li>'
         '<li>Create one-time backups of your wallets (in printed or digital form)</li>'
         '<li>Click on "bitcoin:" links in your web browser '
            '(not supported on all operating systems)</li>'
         '<li>Import private keys to wallets</li>'
         '<li>Monitor payments to watching-only wallets and create '
            'unsigned transactions</li>'
         '<li>Sign messages</li>'
         '<li><b>Create transactions with watching-only wallets, '
            'to be signed by an offline wallets</b></li>'
         '</ul>')
      

   #############################################################################
   def GetDashStateText(self, mgmtMode, state):
      """
      Outsourcing all the verbose dashboard text to here, to de-clutter the   
      logic paths in the setDashboardDetails function
      """
      LOGINFO('Switching Armory state text to Mgmt:%s, State:%s', mgmtMode, state)

      # A few states don't care which mgmtMode you are in...
      if state == 'NewUserInfo':
         return ( \
         'For more information about Armory, and even Bitcoin itself, you '
         'should visit the <a href="https://bitcoinarmory.com/index.php/fr'
         'equently-asked-questions">frequently asked questions page</a>.'
         '<br><br>'
         '<b><u>IMPORTANT:</u></b> Make a backup of your wallet(s)!  Paper '
         'backups protect you <i>forever</i> against forgotten passwords, '
         'hard-drive failure, and make it easy for your family to recover '
         'your funds if something terrible happens to you.  <i>Each wallet '
         'only needs to be backed up once, ever!</i>  Without it, you are at '
         'risk of losing all of your Bitcoins!  For more information, '
         'visit the <a href="https://bitcoinarmory.com/">Armory Backups'
         '</a> page.'
         '<br><br>'
         'To learn about improving your security through the use of offline '
         'wallets, visit the <a href="https://bitcoinarmory.com/armory-quick-'
         'start-guide/">Armory Quick Start Guide</a>, and the <a href="https:'
         '//bitcoinarmory.com/using-offline-wallets-in-armory/">Offline '
         'Wallet Tutorial</a>.<br><br>')
      elif state == 'OnlineFull1':
         return ( \
         '<p><b>You now have access to all the features Armory has to offer!</b><br>'
         'To see your balances and transaction history, please click '
         'on the "Transactions" tab above this text.  <br>'
         'Here\'s some things you can do with Armory Bitcoin Client:'
         '<br>')
      elif state == 'OnlineFull2':
         return ( \
         ('If you experience any performance issues with Armory, '
         'please confirm that Bitcoin-Qt is running and <i>fully '
         'synchronized with the Bitcoin network</i>.  You will see '
         'a green checkmark in the bottom right corner of the '
         'Bitcoin-Qt window if it is synchronized.  If not, it is '
         'recommended you close Armory and restart it only when you '
         'see that checkmark.'
         '<br><br>'  if not self.doManageSatoshi else '') + (
         '<b>Please backup your wallets!</b>  Armory wallets are '
         '"deterministic", meaning they only need to be backed up '
         'one time (unless you have imported external addresses/keys). '
         'Make a backup and keep it in a safe place!  All funds from '
         'Armory-generated addresses will always be recoverable with '
         'a paper backup, any time in the future.  Use the "Backup '
         'Individual Keys" option for each wallet to backup imported '
         'keys.</p>'))
      elif state == 'OnlineNeedSweep':
         return ( \
         'Armory is currently online, but you have requested a sweep operation '
         'on one or more private keys.  This requires searching the global '
         'transaction history for the available balance of the keys to be '
         'swept. '
         '<br><br>'
         'Press the button to start the blockchain scan, which '
         'will also put Armory into offline mode for a few minutes '
         'until the scan operation is complete')
      elif state == 'OnlineDirty':
         return ( \
         '<b>Wallet balances may '
         'be incorrect until the rescan operation is performed!</b>'
         '<br><br>'
         'Armory is currently online, but addresses/keys have been added '
         'without rescanning the blockchain.  You may continue using '
         'Armory in online mode, but any transactions associated with the '
         'new addresses will not appear in the ledger. '
         '<br><br>'
         'Pressing the button above will put Armory into offline mode '
         'for a few minutes until the scan operation is complete.')
      elif state == 'OfflineNoSatoshiNoInternet':
         return ( \
         'There is no connection to the internet, and there is no other '
         'Bitcoin software running.  Most likely '
         'you are here because this is a system dedicated '
         'to manage offline wallets! '
         '<br><br>'
         '<b>If you expected Armory to be in online mode</b>, '
         'please verify your internet connection is active, '
         'then restart Armory.  If you think the lack of internet '
         'connection is in error (such as if you are using Tor), '
         'then you can restart Armory with the "--skip-online-check" '
         'option, or change it in the Armory settings.'
         '<br><br>'
         'If you do not have Bitcoin-Qt installed, you can '
         'download it from <a href="http://www.bitcoin.org">'
         'http://www.bitcoin.org</a>.')

      # Branch the available display text based on which Satoshi-Management
      # mode Armory is using.  It probably wasn't necessary to branch the 
      # the code like this, but it helped me organize the seemingly-endless
      # number of dashboard screens I need
      if mgmtMode.lower()=='user':
         if state == 'OfflineButOnlinePossible':
            return ( \
            'You are currently in offline mode, but can '
            'switch to online mode by pressing the button above.  However, '
            'it is not recommended that you switch until '
            'Bitcoin-Qt/bitcoind is fully synchronized with the bitcoin network.  '
            'You will see a green checkmark in the bottom-right corner of '
            'the Bitcoin-Qt window when it is finished.'
            '<br><br>'
            'Switching to online mode will give you access '
            'to more Armory functionality, including sending and receiving '
            'bitcoins and viewing the balances and transaction histories '
            'of each of your wallets.<br><br>')
         elif state == 'OfflineNoSatoshi':
            return ( \
            'You are currently in offline mode because '
            'Bitcoin-Qt is not running.  To switch to online ' 
            'mode, start Bitcoin-Qt and let it synchronize with the network '
            '-- you will see a green checkmark in the bottom-right corner when '
            'it is complete.  '
            '<br><br>'
            '<b>If you prefer to have Armory do this for you</b>, '
            'then please check "Let Armory run '
            'Bitcoin-Qt in the background" under "File"->"Settings."'
            '<br><br>'
            'If you are new to Armory and/or Bitcoin-Qt, '
            'please visit the Armory '
            'webpage for more information.  Start at '
            '<a href="https://bitcoinarmory.com/index.php/armory-and-bitcoin-qt">'
            'Why Armory needs Bitcoin-Qt</a> or go straight to our <a '
            'href="https://bitcoinarmory.com/index.php/frequently-asked-questions">'
            'frequently asked questions</a> page for more general information.  '
            'If you already know what you\'re doing and simply need '
            'to fetch the latest version of Bitcoin-Qt, you can download it from '
            '<a href="http://www.bitcoin.org">http://www.bitcoin.org</a>.')
         elif state == 'OfflineNoInternet':
            return ( \
            'You are currently in offline mode because '
            'Armory could not detect an internet connection.  '
            'If you think this is in error, then '
            'restart Armory using the " --skip-online-check" option, '
            'or adjust the Armory settings.  Then restart Armory.'
            '<br><br>'
            'If this is intended to be an offline computer, note '
            'that it is not necessary to have Bitcoin-Qt or bitcoind '
            'running.' )
         elif state == 'OfflineNoBlkFiles':
            return ( \
            'You are currently in offline mode because '
            'Armory could not find the blockchain files produced '
            'by Bitcoin-Qt.  Do you run Bitcoin-Qt (or bitcoind) '
            'from a non-standard directory?   Armory expects to '
            'find the blkXXXX.dat files in <br><br>%s<br><br> '
            'If you know where they are located, please restart '
            'Armory using the " --satoshi-datadir=[path]" '
            'to notify Armory where to find them.') % BLKFILE_DIRECTORY
         elif state == 'Disconnected':
            return ( \
            'Armory was previously online, but the connection to Bitcoin-Qt/'
            'bitcoind was interrupted.  You will not be able to send bitcoins '
            'or confirm receipt of bitcoins until the connection is '
            'reestablished.  br><br>Please check that Bitcoin-Qt is open '
            'and synchronized with the network.  Armory will <i>try to '
            'reconnect</i> automatically when the connection is available '
            'again.  If Bitcoin-Qt is available again, and reconnection does '
            'not happen, please restart Armory.<br><br>')
         elif state == 'ScanNoWallets':
            return ( \
            'Please wait while the global transaction history is scanned. '
            'Armory will go into online mode automatically, as soon as '
            'the scan is complete.')
         elif state == 'ScanWithWallets':
            return ( \
            'Armory is scanning the global transaction history to retrieve '
            'information about your wallets.  The "Transactions" tab will '
            'be updated with wallet balance and history as soon as the scan is '
            'complete.  You may manage your wallets while you wait.<br><br>')
         else:
            LOGERROR('Unrecognized dashboard state: Mgmt:%s, State:%s', \
                                                          mgmtMode, state)
            return ''
      elif mgmtMode.lower()=='auto':
         if state == 'OfflineBitcoindRunning':
            return ( \
            'It appears you are already running Bitcoin software '
            '(Bitcoin-Qt or bitcoind). '
            'Unlike previous versions of Armory, you should <u>not</u> run '
            'this software yourself --  Armory '
            'will run it in the background for you.  Either close the '
            'Bitcoin application or adjust your settings.  If you change '
            'your settings, then please restart Armory.')
         if state == 'OfflineNeedBitcoinInst':
            return ( \
            '<b>Only one more step to getting online with Armory!</b>   You '
            'must install the Bitcoin software from www.bitcoin.org in order '
            'for Armory to communicate with the Bitcoin network.  If the '
            'Bitcoin software is already installed and/or you would prefer '
            'to manage it yourself, please adjust your settings and '
            'restart Armory.')
         if state == 'InitializingLongTime':
            return ( \
            'You are offline while the Bitcoin engine is downloading the '
            'global transaction history in order to maximize your '
            'security.  <b>This takes a few hours the first time, but '
            'should only take a few minutes on subsequent loads.</b>  '
            'Please be patient!'
            '<br><br>'
            'While you wait, you can manage your wallets.  Make new wallets, '
            'make digital or paper backups, create Bitcoin addresses to receive '
            'payments, '
            'sign messages, and/or import private keys.  You will always '
            'receive Bitcoin payments regardless of whether you are online, '
            'but you will have to verify that payment through another service '
            'until Armory is finished this initialization.')
         if state == 'InitializingDoneSoon':
            return ( \
            'The software is downloading and processing the latest activity '
            'on the network related to your wallet%s.  This should take only '
            'a few minutes.  While you wait, you can manage your wallets.  '
            '<br><br>'
            'Now would be a good time to make paper (or digital) backups of '
            'your wallet%s if you have not done so already!  You are protected '
            '<i>forever</i> from hard-drive loss, or forgetting you password. '
            'If you do not have a backup, you could lose all of your '
            'Bitcoins forever!  See the <a href="https://bitcoinarmory.com/">'
            'Armory Backups page</a> for more info.' % \
            (('' if len(self.walletMap)==1 else 's',)*2))
         if state == 'OnlineDisconnected':
            return ( \
            'Armory\'s communication with the Bitcoin network was interrupted. '
            'This usually does not happen unless you closed the process that '
            'Armory was using to communicate with the network. Armory requires '
            '%s to be running in the background, and this error pops up if it '
            'disappears.'
            '<br><br>You may continue in offline mode, or you can close '
            'all Bitcoin processes and restart Armory.' \
            % os.path.basename(TheSDM.executable))
         if state == 'OfflineBadConnection':
            return ( \
            'Armory has experienced an issue trying to communicate with the '
            'Bitcoin software.  The software is running in the background, '
            'but Armory cannot communicate with it through RPC as it expects '
            'to be able to.  If you changed any settings in the Bitcoin home '
            'directory, please make sure that RPC is enabled and that it is '
            'accepting connections from localhost.  '
            '<br><br>'
            'If you have not changed anything, please export the log file '
            '(from the "File" menu) and send it to alan.reiner@gmail.com.')
         if state == 'OfflineSatoshiAvail':
            return ( \
            'Armory does not detect internet access, but it does detect '
            'running Bitcoin software.  Armory is in offline-mode. <br><br>'
            'If you are intending to run an offline system, you will not '
            'need to have the Bitcoin software installed on the offline '
            'computer.  It is only needed for the online computer. '
            'If you expected to be online and '
            'the absence of internet is an error, please restart Armory '
            'using the "--skip-online-check" option.  ')
         if state == 'OfflineForcedButSatoshiAvail':
            return ( \
            'Armory was started in offline-mode, but detected you are '
            'running Bitcoin software.  If you are intending to run an '
            'offline system, you will <u>not</u> need to have the Bitcoin '
            'software installed or running on the offline '
            'computer.  It is only required for being online. ')
         

   #############################################################################
   def setDashboardDetails(self, INIT=False):
      """
      We've dumped all the dashboard text into the above 2 methods in order
      to declutter this method.
      """

      TimerStart('setDashboardDetails')
      onlineAvail = self.onlineModeIsPossible()

      sdmState = TheSDM.getSDMState()
      bdmState = TheBDM.getBDMState()
      descr1 = ''
      descr2 = ''

      # Methods for showing/hiding groups of widgets on the dashboard
      def setBtnRowVisible(r, visBool):
         for c in range(3):
            self.dashBtns[r][c].setVisible(visBool)
      hideRow = lambda r: setBtnRowVisible(r, False)
      showRow = lambda r: setBtnRowVisible(r, True)

      def setSyncRowVisible(b):
         self.lblDashModeSync.setVisible(b)
         self.barProgressSync.setVisible(b)
         self.lblTimeLeftSync.setVisible(b)
         
      def setScanRowVisible(b):
         self.lblDashModeScan.setVisible(b)
         self.barProgressScan.setVisible(b)
         self.lblTimeLeftScan.setVisible(b)

      def setOnlyDashModeVisible():
         setSyncRowVisible(False)
         setScanRowVisible(False)
         self.lblBusy.setVisible(False)
         self.btnModeSwitch.setVisible(False)
         self.lblDashModeSync.setVisible(True)

      def setBtnFrameVisible(b, descr=''):
         self.frmDashMidButtons.setVisible(b)
         self.lblDashBtnDescr.setVisible(len(descr)>0)
         self.lblDashBtnDescr.setText(descr)


      if INIT:
         setBtnFrameVisible(False)
         hideRow(DASHBTNS.Install)
         hideRow(DASHBTNS.Browse)
         hideRow(DASHBTNS.Instruct)
         hideRow(DASHBTNS.Settings)
         hideRow(DASHBTNS.Close)
         setOnlyDashModeVisible()
         self.btnModeSwitch.setVisible(False)

      if self.doManageSatoshi and not sdmState=='BitcoindReady':
         # User is letting Armory manage the Satoshi client for them.
         
         if not sdmState==self.lastSDMState:

            self.lblBusy.setVisible(False)
            self.btnModeSwitch.setVisible(False)

            # There's a whole bunch of stuff that has to be hidden/shown 
            # depending on the state... set some reasonable defaults here
            setBtnFrameVisible(False)
            hideRow(DASHBTNS.Install)
            hideRow(DASHBTNS.Browse)
            hideRow(DASHBTNS.Instruct)
            showRow(DASHBTNS.Settings)
            hideRow(DASHBTNS.Close)
   
            if not (self.forceOnline or self.internetAvail) or CLI_OPTIONS.offline:
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, False)
               setOnlyDashModeVisible()
               self.lblDashModeSync.setText( 'Armory is <u>offline</u>', \
                                            size=4, color='TextWarn', bold=True)
               if satoshiIsAvailable():
                  if CLI_OPTIONS.offline:
                     # Forced offline but bitcoind is running
                     LOGINFO('Dashboard switched to auto-OfflineForcedButSatoshiAvail')
                     self.frmDashMidButtons.setVisible(False)
                     descr1 += self.GetDashStateText('Auto', 'OfflineForcedButSatoshiAvail')
                     descr2 += self.GetDashFunctionalityText('Offline')
                     self.lblDashDescr1.setText(descr1)
                     self.lblDashDescr2.setText(descr2)
                  else:
                     LOGINFO('Dashboard switched to auto-OfflineSatoshiAvail')
                     self.frmDashMidButtons.setVisible(False)
                     descr1 += self.GetDashStateText('Auto', 'OfflineSatoshiAvail')
                     descr2 += self.GetDashFunctionalityText('Offline')
                     self.lblDashDescr1.setText(descr1)
                     self.lblDashDescr2.setText(descr2)
               else:
                  LOGINFO('Dashboard switched to auto-OfflineNoSatoshiNoInternet')
                  setBtnFrameVisible(True, \
                     'In case you actually do have internet access, use can use '
                     'the following links to get Armory installed.  Or change '
                     'your settings.')
                  showRow(DASHBTNS.Browse)
                  showRow(DASHBTNS.Install)
                  showRow(DASHBTNS.Settings)
                  if not OS_WINDOWS:
                     showRow(DASHBTNS.Instruct) 
                  descr1 += self.GetDashStateText('Auto','OfflineNoSatoshiNoInternet')
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
            elif not TheSDM.isRunningBitcoind():
               setOnlyDashModeVisible()
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, False)
               self.lblDashModeSync.setText( 'Armory is <u>offline</u>', \
                                            size=4, color='TextWarn', bold=True)
               # Bitcoind is not being managed, but we want it to be
               if satoshiIsAvailable():
                  # But bitcoind/-qt is already running
                  LOGINFO('Dashboard switched to auto-butSatoshiRunning')
                  self.lblDashModeSync.setText(' Please close Bitcoin-Qt', \
                                                         size=4, bold=True)
                  setBtnFrameVisible(True, '')
                  self.btnModeSwitch.setVisible(True)
                  self.btnModeSwitch.setText('Check Again')
                  #showRow(DASHBTNS.Close)
                  descr1 += self.GetDashStateText('Auto', 'OfflineBitcoindRunning')
                  descr2 += self.GetDashStateText('Auto', 'NewUserInfo')
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
                  #self.psutil_detect_bitcoin_exe_path()
               elif sdmState in ['BitcoindExeMissing', 'BitcoindHomeMissing']:
                  LOGINFO('Dashboard switched to auto-cannotFindExeHome')
                  if sdmState=='BitcoindExeMissing':
                     self.lblDashModeSync.setText('Cannot find Bitcoin Installation', \
                                                         size=4, bold=True)
                  else:
                     self.lblDashModeSync.setText('Cannot find Bitcoin Home Directory', \
                                                         size=4, bold=True)
                  showRow(DASHBTNS.Install)
                  showRow(DASHBTNS.Browse)
                  showRow(DASHBTNS.Settings)
                  if not OS_WINDOWS:
                     showRow(DASHBTNS.Instruct) 
                  self.btnModeSwitch.setVisible(True)
                  self.btnModeSwitch.setText('Check Again')
                  setBtnFrameVisible(True)
                  descr1 += self.GetDashStateText('Auto', 'OfflineNeedBitcoinInst')
                  descr2 += self.GetDashStateText('Auto', 'NewUserInfo')
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
                   
               elif sdmState in ['BitcoindNeverStarted']:
                  raise ShouldNotGetHereError, 'Bitcoind Never started...?'
               elif sdmState in ['BitcoindNotAvailable']:
                  setOnlyDashModeVisible()
                  LOGINFO('Dashboard switched to auto-BadConnection')
                  self.lblDashModeSync.setText( 'Armory is <u>offline</u>', \
                                            size=4, color='TextWarn', bold=True)
                  descr1 += self.GetDashStateText('Auto', 'OfflineBadConnection')
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
            else:  # online detected/forced, and TheSDM has already been started
               if sdmState in ['BitcoindWrongPassword', 'BitcoindNotAvailable']:
                  setOnlyDashModeVisible()
                  self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, False)
                  LOGINFO('Dashboard switched to auto-BadConnection')
                  self.lblDashModeSync.setText( 'Armory is <u>offline</u>', \
                                            size=4, color='TextWarn', bold=True)
                  descr1 += self.GetDashStateText('Auto', 'OfflineBadConnection')
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
               elif sdmState in ['BitcoindInitializing', 'BitcoindSynchronizing']:
                  LOGINFO('Dashboard switched to auto-InitSync')
                  self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, False)
                  self.updateSyncProgress()
                  setSyncRowVisible(True)
                  setScanRowVisible(True)
                  self.lblBusy.setVisible(True)

                  if sdmState=='BitcoindInitializing':
                     self.lblDashModeSync.setText( 'Initializing Bitcoin Engine', \
                                              size=4, bold=True, color='Foreground')
                  else:
                     self.lblDashModeSync.setText( 'Synchronizing with Network', \
                                              size=4, bold=True, color='Foreground')

                  self.lblDashModeScan.setText( 'Scanning Transaction History', \
                                              size=4, bold=True, color='DisableFG')
                  if self.approxBlkLeft > 1440: # more than 10 days
                     descr1 += self.GetDashStateText('Auto', 'InitializingLongTime')
                     descr2 += self.GetDashStateText('Auto', 'NewUserInfo')
                  else:
                     descr1 += self.GetDashStateText('Auto', 'InitializingDoneSoon')

                  showRow(DASHBTNS.Settings)
                  setBtnFrameVisible(True, \
                     'Since version 0.88, Armory runs bitcoind in the '
                     'background.  You can switch back to '
                     'the old way in the Settings dialog. ')
   
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
      else:
         # User is managing satoshi client, or bitcoind is already sync'd
         self.frmDashMidButtons.setVisible(False)
         if bdmState in ('Offline', 'Uninitialized'):
            if onlineAvail and not self.lastBDMState[1]==onlineAvail:
               LOGINFO('Dashboard switched to user-OfflineOnlinePoss')
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, False)
               setOnlyDashModeVisible()
               self.lblBusy.setVisible(False)
               self.btnModeSwitch.setVisible(True)
               self.btnModeSwitch.setEnabled(True)
               self.btnModeSwitch.setText('Go Online!')
               self.lblDashModeSync.setText('Armory is <u>offline</u>', size=4, bold=True)
               descr  = self.GetDashStateText('User', 'OfflineButOnlinePossible')
               descr += self.GetDashFunctionalityText('Offline')
               self.lblDashDescr1.setText(descr)
            elif not onlineAvail and not self.lastBDMState[1]==onlineAvail:
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, False)
               setOnlyDashModeVisible()
               self.lblBusy.setVisible(False)
               self.btnModeSwitch.setVisible(False)
               self.btnModeSwitch.setEnabled(False)
               self.lblDashModeSync.setText( 'Armory is <u>offline</u>', \
                                         size=4, color='TextWarn', bold=True)
   
               if not self.bitcoindIsAvailable():
                  if self.internetAvail:
                     descr = self.GetDashStateText('User','OfflineNoSatoshi')
                     showRow(DASHBTNS.Settings)
                     setBtnFrameVisible(True, \
                        'If you would like Armory to manage the Bitcoin software '
                        'for you (Bitcoin-Qt or bitcoind), then adjust your '
                        'Armory settings, then restart Armory.')
                  else:
                     descr = self.GetDashStateText('User','OfflineNoSatoshiNoInternet')
               elif not self.internetAvail:
                  descr = self.GetDashStateText('User', 'OfflineNoInternet')
               elif not self.checkHaveBlockfiles():
                  descr = self.GetDashStateText('User', 'OfflineNoBlkFiles')
   
               descr += '<br><br>' 
               descr += self.GetDashFunctionalityText('Offline')
               self.lblDashDescr1.setText(descr)
   
         elif bdmState == 'BlockchainReady':
            setOnlyDashModeVisible()
            self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, True)
            self.lblBusy.setVisible(False)
            if self.netMode == NETWORKMODE.Disconnected:
               self.btnModeSwitch.setVisible(False)
               self.lblDashModeSync.setText( 'Armory is disconnected', size=4, color='TextWarn', bold=True)
               descr  = self.GetDashStateText('User','Disconnected')
               descr += self.GetDashFunctionalityText('Offline')
               self.lblDashDescr1.setText(descr)
            elif TheBDM.isDirty():
               LOGINFO('Dashboard switched to online-but-dirty mode')
               self.btnModeSwitch.setVisible(True)
               self.btnModeSwitch.setText('Rescan Now')
               self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Dashboard)
               self.lblDashModeSync.setText( 'Armory is online, but needs to rescan ' \
                              'the blockchain</b>', size=4, color='TextWarn', bold=True)
               if len(self.sweepAfterScanList) > 0:
                  self.lblDashDescr1.setText( self.GetDashStateText('User', 'OnlineNeedSweep'))
               else:
                  self.lblDashDescr1.setText( self.GetDashStateText('User', 'OnlineDirty'))
            else:
               # Fully online mode
               LOGINFO('Dashboard switched to fully-online mode')
               self.btnModeSwitch.setVisible(False)
               self.lblDashModeSync.setText( 'Armory is online!', color='TextGreen', size=4, bold=True)
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, True)
               descr  = self.GetDashStateText('User', 'OnlineFull1')
               descr += self.GetDashFunctionalityText('Online')
               descr += self.GetDashStateText('User', 'OnlineFull2')
               self.lblDashDescr1.setText(descr)
            #self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Dashboard)
         elif bdmState == 'Scanning':
            LOGINFO('Dashboard switched to "Scanning" mode')
            self.updateSyncProgress()
            self.lblDashModeScan.setVisible(True)
            self.barProgressScan.setVisible(True)
            self.lblTimeLeftScan.setVisible(True)
            self.lblBusy.setVisible(True)
            self.btnModeSwitch.setVisible(False)

            if TheSDM.getSDMState() == 'BitcoindReady':
               self.barProgressSync.setVisible(True)
               self.lblTimeLeftSync.setVisible(True)
               self.lblDashModeSync.setVisible(True)
               self.lblTimeLeftSync.setText('')
               self.lblDashModeSync.setText( 'Synchronizing with Network', \
                                       size=4, bold=True, color='DisableFG')
            else:
               self.barProgressSync.setVisible(False)
               self.lblTimeLeftSync.setVisible(False)
               self.lblDashModeSync.setVisible(False)

            self.lblDashModeScan.setText( 'Scanning Transaction History', \
                                        size=4, bold=True, color='Foreground')
            self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, False)
   
            if len(self.walletMap)==0:
               descr = self.GetDashStateText('User','ScanNoWallets')
            else:
               descr = self.GetDashStateText('User','ScanWithWallets')
   
            descr += self.GetDashFunctionalityText('Scanning') + '<br>'
            self.lblDashDescr1.setText(descr)
            self.lblDashDescr2.setText('')
            self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Dashboard)
         else:
            LOGERROR('What the heck blockchain mode are we in?  %s', bdmState)
   
      self.lastBDMState = [bdmState, onlineAvail]
      self.lastSDMState =  sdmState
      self.lblDashModeSync.setContentsMargins(50,5,50,5)
      self.lblDashModeScan.setContentsMargins(50,5,50,5)
      vbar = self.scrl.verticalScrollBar()
      vbar.setValue(vbar.minimum())
         
      TimerStop('setDashboardDetails')
            
   
   
   #############################################################################
   def Heartbeat(self, nextBeatSec=1):
      """
      This method is invoked when the app is initialized, and will
      run every second, or whatever is specified in the nextBeatSec
      argument.
      """
         
      sdmState = TheSDM.getSDMState()
      bdmState = TheBDM.getBDMState()
      print "SDM       : ", sdmState.rjust(20),
      #print "SDM (last): ", self.lastSDMState.rjust(20)
      print "BDM       : ", bdmState.rjust(20)
      #print "BDM (last): ", self.lastBDMState[0].rjust(20)


      # Special heartbeat functions are for special windows that may need
      # to update every, say, every 0.1s 
      # is all that matters at that moment, like a download progress window.
      # This is "special" because you are putting all other processing on
      # hold while this special window is active
      # IMPORTANT: Make sure that the special heartbeat function returns
      #            a value below zero when it's done OR if it errors out!
      #            Otherwise, it should return the next heartbeat delay, 
      #            which would probably be something like 0.1 for a rapidly
      #            updating progress counter
      for fn in self.extraHeartbeatSpecial:
         try:
            nextBeat = fn()
            if nextBeat>0:
               reactor.callLater(nextBeat, self.Heartbeat)
            else:
               self.extraHeartbeatSpecial = []
               reactor.callLater(1, self.Heartbeat)
         except:
            LOGERROR('Error in special heartbeat function')
            self.extraHeartbeatSpecial = []
            reactor.callLater(1, self.Heartbeat)
         return
            
            

      try:
         for func in self.extraHeartbeatAlways:
            func()
   
         for idx,wltID in enumerate(self.walletIDList):
            self.walletMap[wltID].checkWalletLockTimeout()
   

         if self.doManageSatoshi:
            if sdmState in ['BitcoindInitializing','BitcoindSynchronizing']:
               self.updateSyncProgress()
            elif sdmState == 'BitcoindReady':
               if bdmState == 'Uninitialized':
                  LOGINFO('Starting load blockchain')
                  self.loadBlockchainIfNecessary()
               elif bdmState == 'Offline':
                  LOGERROR('Bitcoind is ready, but we are offline... ?')
               elif bdmState=='Scanning':
                  self.updateSyncProgress()

            if not sdmState==self.lastSDMState or not bdmState==self.lastBDMState[0]:
               self.setDashboardDetails()
         else:
            if bdmState in ('Offline','Uninitialized'):
               # This call seems out of place, but it's because if you are in offline
               # mode, it needs to check periodically for the existence of Bitcoin-Qt
               # so that it can enable the "Go Online" button
               self.setDashboardDetails()
               return
            elif bdmState=='Scanning':
               self.updateSyncProgress()


         if self.netMode==NETWORKMODE.Disconnected:
            if self.onlineModeIsPossible():
               self.switchNetworkMode(NETWORKMODE.Full)

         if not TheBDM.isDirty() == self.dirtyLastTime:
            self.setDashboardDetails()
         self.dirtyLastTime = TheBDM.isDirty()

   
         if bdmState=='BlockchainReady':

            #####
            # Blockchain just finished loading.  Do lots of stuff...
            if self.needUpdateAfterScan:
               LOGDEBUG('Running finishLoadBlockchain')
               self.finishLoadBlockchain()
               self.needUpdateAfterScan = False
               self.setDashboardDetails()
               
            #####
            # If we just rescanned to sweep an address, need to finish it
            if len(self.sweepAfterScanList)>0:
               LOGDEBUG('SweepAfterScanList is not empty -- exec finishSweepScan()')
               self.finishSweepScan()
               for addr in self.sweepAfterScanList:
                  addr.binPrivKey32_Plain.destroy()
               self.sweepAfterScanList = []
               self.setDashboardDetails()

            #####
            # If we had initiated any wallet restoration scans, we need to add
            # Those wallets to the display
            if len(self.newWalletList)>0:
               LOGDEBUG('Wallet restore completed.  Add to application.')
               while len(self.newWalletList)>0:
                  wlt,isFresh = self.newWalletList.pop()
                  print 'Registering %s wallet' % ('NEW' if isFresh else 'IMPORTED')
                  TheBDM.registerWallet(wlt.cppWallet, isFresh)
                  self.addWalletToApplication(wlt, walletIsNew=isFresh)
               self.setDashboardDetails()


            # Now we start the normal array of heartbeat operations
            newBlocks = TheBDM.readBlkFileUpdate(wait=True)
            self.currBlockNum = TheBDM.getTopBlockHeight()

            #####
            # If we are getting lots of blocks, very rapidly, issue a warning
            # We look at a rolling sum of the last 5 heartbeat updates (5s)
            if not newBlocks:
               newBlocks = 0
            self.detectNotSyncQ.insert(0, newBlocks)
            self.detectNotSyncQ.pop()
            blksInLast5sec = sum(self.detectNotSyncQ)
            if( blksInLast5sec>10 ):
               LOGERROR('Detected Bitcoin-Qt/bitcoind not synchronized')
               LOGERROR('New blocks added in last 5 sec: %d', blksInLast5sec)
               if self.noSyncWarnYet:
                  self.noSyncWarnYet = False
                  QMessageBox.warning(self,'Bitcoin-Qt is not synchronized', \
                     'Armory has detected that Bitcoin-Qt is not synchronized '
                     'with the bitcoin network yet, and Armory <b>may</b> not '
                     'work properly.  If you experience any unusual behavior, it is '
                     'recommended that you close Armory and only restart it '
                     'when you see the green checkmark in the bottom-right '
                     'corner of the Bitcoin-Qt window.', QMessageBox.Ok)
               return
            
         
   
            # If we have new zero-conf transactions, scan them and update ledger
            if len(self.newZeroConfSinceLastUpdate)>0:
               self.newZeroConfSinceLastUpdate.reverse()
               for wltID in self.walletMap.keys():
                  wlt = self.walletMap[wltID]
                  TheBDM.rescanWalletZeroConf(wlt.cppWallet, wait=True)

            while len(self.newZeroConfSinceLastUpdate)>0:
               TimerStart('CheckNewZeroConf')
               # For each new tx, check each wallet
               rawTx = self.newZeroConfSinceLastUpdate.pop()
               for wltID in self.walletMap.keys():
                  wlt = self.walletMap[wltID]
                  le = wlt.cppWallet.calcLedgerEntryForTxStr(rawTx)
                  if not le.getTxHash()=='\x00'*32:
                     LOGDEBUG('ZerConf tx for wallet: %s.  Adding to notify queue.' % wltID)
                     notifyIn  = self.getSettingOrSetDefault('NotifyBtcIn',  True)
                     notifyOut = self.getSettingOrSetDefault('NotifyBtcOut', True)
                     if (le.getValue()<=0 and notifyOut) or (le.getValue()>0 and notifyIn):
                        self.notifyQueue.append([wltID, le, False])  # notifiedAlready=False
                     self.createCombinedLedger()
                     self.walletModel.reset()
               TimerStop('CheckNewZeroConf')
   
            # Trigger any notifications, if we have them...
            TimerStart('doSystemTrayThing')
            self.doTheSystemTrayThing()
            TimerStop('doSystemTrayThing')

            if newBlocks>0 and not TheBDM.isDirty():
   
               # This says "after scan", but works when new blocks appear, too
               TheBDM.updateWalletsAfterScan(wait=True)

               prevLedgSize = dict([(wltID, len(self.walletMap[wltID].getTxLedger())) \
                                                   for wltID in self.walletMap.keys()])

               print 'New Block: ', self.currBlockNum

               self.ledgerModel.reset()

               LOGINFO('New Block! : %d', self.currBlockNum)
               didAffectUs = False
   
               # LITE sync means it won't rescan if addresses have been imported
               TimerStart('newBlockSyncRescanZC')
               for wltID in self.walletMap.keys():
                  self.walletMap[wltID].syncWithBlockchainLite()
                  TheBDM.rescanWalletZeroConf(self.walletMap[wltID].cppWallet)
                  newLedgerSize = len(self.walletMap[wltID].getTxLedger())
                  didAffectUs = (prevLedgSize[wltID] != newLedgerSize)
               TimerStop('newBlockSyncRescanZC')
            
               if didAffectUs:
                  LOGINFO('New Block contained a transaction relevant to us!')
                  self.walletListChanged()
                  self.notifyOnSurpriseTx(self.currBlockNum-newBlks, \
                                          self.currBlockNum+1)
      
               self.createCombinedLedger()
               self.blkReceived  = RightNow()
               self.writeSetting('LastBlkRecvTime', self.blkReceived)
               self.writeSetting('LastBlkRecv',     self.currBlockNum)
            
               if self.netMode==NETWORKMODE.Full:
                  self.lblArmoryStatus.setText(\
                     '<font color=%s>Connected (%s blocks)</font> ' % \
                     (htmlColor('TextGreen'), self.currBlockNum))
      
               # Update the wallet view to immediately reflect new balances
               TimerStart('walletModelReset')
               self.walletModel.reset()
               TimerStop('walletModelReset')
      
            blkRecvAgo  = RightNow() - self.blkReceived
            #blkStampAgo = RightNow() - TheBDM.getTopBlockHeader().getTimestamp()
            self.lblArmoryStatus.setToolTip('Last block received is %s ago' % \
                                                secondsToHumanTime(blkRecvAgo))
               
   
            for func in self.extraHeartbeatOnline:
               func()
   
   
      except:
         LOGEXCEPT('Error in heartbeat function')
         print sys.exc_info()
      finally:
         reactor.callLater(nextBeatSec, self.Heartbeat)
      

   #############################################################################
   def notifyOnSurpriseTx(self, blk0, blk1):
      # We usually see transactions as zero-conf first, then they show up in 
      # a block. It is a "surprise" when the first time we see it is in a block
      notifiedAlready = set([ n[1].getTxHash() for n in self.notifyQueue ])
      for blk in range(blk0, blk1):
         for tx in TheBDM.getHeaderByHeight(blk).getTxRefPtrList():
            for wltID,wlt in self.walletMap.iteritems():
               le = wlt.cppWallet.calcLedgerEntryForTx(tx)
               if not le.getTxHash() in notifiedAlready:
                  notifyIn  = self.getSettingOrSetDefault('NotifyBtcIn',  True)
                  notifyOut = self.getSettingOrSetDefault('NotifyBtcOut', True)
                  if (le.getValue()<=0 and notifyOut) or (le.getValue>0 and notifyIn):
                     self.notifyQueue.append([wltID, le, False])
               else:
                  pass
               
            

   #############################################################################
   def doTheSystemTrayThing(self):
      """
      I named this method as it is because this is not just "show a message."
      I need to display all relevant transactions, in sequence that they were 
      received.  I will store them in self.notifyQueue, and this method will
      do nothing if it's empty.
      """
      if not TheBDM.getBDMState()=='BlockchainReady' or \
         RightNow()<self.notifyBlockedUntil:
         return

      # Input is:  [WltID, LedgerEntry, NotifiedAlready] 
      txNotifyList = []
      for i in range(len(self.notifyQueue)):
         wltID, le, alreadyNotified = self.notifyQueue[i]
         if not self.walletMap.has_key(wltID):
            continue
         wlt = self.walletMap[wltID]

         # Skip the ones we've notified of already
         if alreadyNotified:
            continue

         # Notification is not actually for us
         if le.getTxHash()=='\x00'*32:
            continue
         
         self.notifyQueue[i][2] = True
         if le.isSentToSelf():
            amt = determineSentToSelfAmt(le, wlt)[0]
            self.sysTray.showMessage('Your bitcoins just did a lap!', \
               'Wallet "%s" (%s) just sent %s BTC to itself!' % \
               (wlt.labelName, wltID, coin2str(amt,maxZeros=1).strip()),
               QSystemTrayIcon.Information, 10000)
         else:
            txref = TheBDM.getTxByHash(le.getTxHash())
            nOut = txref.getNumTxOut()
            recips = [txref.getTxOut(i).getRecipientAddr() for i in range(nOut)]
            values = [txref.getTxOut(i).getValue()         for i in range(nOut)]
            idxMine  = filter(lambda i:     wlt.hasAddr(recips[i]), range(nOut))
            idxOther = filter(lambda i: not wlt.hasAddr(recips[i]), range(nOut))
            mine  = [(recips[i],values[i]) for i in idxMine]
            other = [(recips[i],values[i]) for i in idxOther]
            dispLines = []
            title = ''

            # Collected everything we need to display, now construct it and do it
            if le.getValue()>0:
               # Received!
               title = 'Bitcoins Received!'
               totalStr = coin2str( sum([mine[i][1] for i in range(len(mine))]), maxZeros=1)
               dispLines.append(   'Amount: \t%s BTC' % totalStr.strip())
               if len(mine)==1:
                  dispLines.append('Address:\t%s' % hash160_to_addrStr(mine[0][0]))
                  addrComment = wlt.getComment(mine[0][0])
               else:
                  dispLines.append('<Received with Multiple Addresses>')
               dispLines.append(   'Wallet:\t"%s" (%s)' % (wlt.labelName, wltID))
            elif le.getValue()<0:
               # Sent!
               title = 'Bitcoins Sent!'
               totalStr = coin2str( sum([other[i][1] for i in range(len(other))]), maxZeros=1)
               dispLines.append(   'Amount: \t%s BTC' % totalStr.strip())
               if len(other)==1:
                  dispLines.append('Sent To:\t%s' % hash160_to_addrStr(other[0][0]))
                  addrComment = wlt.getComment(other[0][0])
               else:
                  dispLines.append('<Sent to Multiple Addresses>')
               dispLines.append('From:\tWallet "%s" (%s)' % (wlt.labelName, wltID))

            self.sysTray.showMessage(title, \
                                     '\n'.join(dispLines),  \
                                     QSystemTrayIcon.Information, \
                                     10000)
            #qsnd = QSound('drip.wav')
            #qsnd.play()

         self.notifyBlockedUntil = RightNow() + 5
         return
            
      
      
   #############################################################################
   def closeEvent(self, event=None):
      moc = self.getSettingOrSetDefault('MinimizeOrClose', 'DontKnow')
      doClose, doMinimize = False, False
      if moc=='DontKnow':
         reply,remember = MsgBoxWithDNAA(MSGBOX.Question, 'Minimize or Close', \
            'Would you like to minimize Armory to the system tray instead '
            'of closing it?', dnaaMsg='Remember my answer', \
            yesStr='Minimize', noStr='Close')
         if reply==True:
            doMinimize = True
            if remember:
               self.writeSetting('MinimizeOrClose', 'Minimize')
         else:
            doClose = True;
            if remember:
               self.writeSetting('MinimizeOrClose', 'Close')

      if doMinimize or moc=='Minimize':
         self.minimizeArmory()
         if event:
            event.ignore()
      elif doClose or moc=='Close':
         self.doShutdown = True
         TheBDM.execCleanShutdown(wait=False)
         self.sysTray.hide()
         self.closeForReal(event)
      else:
         return  # how would we get here?



   #############################################################################
   def closeForReal(self, event=None):
      '''
      Seriously, I could not figure out how to exit gracefully, so the next
      best thing is to just hard-kill the app with a sys.exit() call.  Oh well... 
      '''
      try:
         # Save the main window geometry in the settings file
         self.writeSetting('MainGeometry',   str(self.saveGeometry().toHex()))
         self.writeSetting('MainWalletCols', saveTableView(self.walletsView))
         self.writeSetting('MainLedgerCols', saveTableView(self.ledgerView))
         # If user explicitly closed the window, don't count as a failed load
         #nTries = max(1,self.getSettingOrSetDefault('FailedLoadCount', 1))
         #self.writeSetting('FailedLoadCount', nTries-1)
      except:
         # Don't want a strange error here interrupt shutdown 
         pass

      # This will do nothing if bitcoind isn't running
      TheSDM.stopBitcoind()

      # Mostly for my own use, I'm curious how fast various things run
      if CLI_OPTIONS.doDebug:
         SaveTimingsCSV( os.path.join(ARMORY_HOME_DIR, 'timings.csv') )

      if self.doHardReset:
         try:
            os.remove(self.settingsPath) 
         except:
            LOGERROR('Could not remove settings path.')

         mempoolfile = os.path.join(ARMORY_HOME_DIR, 'mempool.bin')
         if os.path.exists(mempoolfile):
            os.remove(mempoolfile)

      from twisted.internet import reactor
      LOGINFO('Attempting to close the main window!')
      reactor.stop()
      if event:
         event.accept()
      
      

############################################
class ArmoryInstanceListener(Protocol):
   def connectionMade(self):
      LOGINFO('Another Armory instance just tried to open.')
      self.factory.func_conn_made()
      
   def dataReceived(self, data):
      LOGINFO('Received data from alternate Armory instance')
      self.factory.func_recv_data(data)
      self.transport.loseConnection()

############################################
class ArmoryListenerFactory(ClientFactory):
   protocol = ArmoryInstanceListener
   def __init__(self, fn_conn_made, fn_recv_data):
      self.func_conn_made = fn_conn_made
      self.func_recv_data = fn_recv_data



############################################
def checkForAlreadyOpen():
   import socket
   LOGDEBUG('Checking for already open socket...')
   try:
      # If create doesn't throw an error, there's another Armory open already!
      sock = socket.create_connection(('127.0.0.1',CLI_OPTIONS.interport), 0.1);
      if CLI_ARGS:
         sock.send(CLI_ARGS[0])
      sock.close()
      os._exit(0)
   except:
      pass




############################################
if 1:

   import qt4reactor
   qt4reactor.install()

   if CLI_OPTIONS.interport > 1:
      checkForAlreadyOpen()

   pixLogo = QPixmap(':/splashlogo.png')
   if USE_TESTNET:
      pixLogo = QPixmap(':/splashlogo_testnet.png')
   SPLASH = QSplashScreen(pixLogo)
   SPLASH.setMask(pixLogo.mask())
   SPLASH.show()
   QAPP.processEvents()

   # Will make this customizable
   QAPP.setFont(GETFONT('var'))

   form = ArmoryMainWindow()
   form.show()

   SPLASH.finish(form)

   from twisted.internet import reactor
   def endProgram():
      print 'Resetting BlockDataMgr, freeing memory'
      LOGINFO('Resetting BlockDataMgr, freeing memory')
      TheBDM.Reset()
      TheBDM.execCleanShutdown(wait=False)
      if reactor.threadpool is not None:
         reactor.threadpool.stop()
      QAPP.quit()
      os._exit(0)
      
   QAPP.connect(form, SIGNAL("lastWindowClosed()"), endProgram)
   reactor.addSystemEventTrigger('before', 'shutdown', endProgram)
   QAPP.setQuitOnLastWindowClosed(True)
   reactor.runReturn()
   os._exit(QAPP.exec_())


