################################################################################
#
# Copyright (C) 2011-2012, Alan C. Reiner    <alan.reiner@gmail.com>
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
import platform
import traceback
import socket
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


      # SETUP THE WINDOWS DECORATIONS
      self.lblLogoIcon = QLabel()
      if USE_TESTNET:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [TESTNET]')
         self.iconfile = ':/armory_icon_green_32x32.png'
         self.lblLogoIcon.setPixmap(QPixmap(':/armory_logo_green_h56.png'))
         if Colors.isDarkBkgd:
            self.lblLogoIcon.setPixmap(QPixmap(':/armory_logo_white_text_green_h56.png'))
      else:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [MAIN NETWORK]')
         self.iconfile = ':/armory_icon_32x32.png'
         self.lblLogoIcon.setPixmap(QPixmap(':/armory_logo_h56.png'))
         if Colors.isDarkBkgd:
            self.lblLogoIcon.setPixmap(QPixmap(':/armory_logo_white_text_h56.png'))
      self.setWindowIcon(QIcon(self.iconfile))
      self.lblLogoIcon.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      self.netMode     = NETWORKMODE.Offline
      self.abortLoad   = False
      self.allowRescan = True
      self.memPoolInit = False
      self.WltsToScan  = []
      self.prevTopBlock = -1
      self.needUpdateAfterScan = True
      self.sweepAfterScanList = []
      self.newZeroConfSinceLastUpdate = []
      self.callCount = 0
      self.lastBDMState = ['Uninitialized', None]
      
      self.settingsPath = CLI_OPTIONS.settingsPath
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

      # Setup system tray and register "bitcoin:" URLs with the OS
      self.setupSystemTray()
      self.setupUriRegistration()


      self.extraHeartbeatOnline = [self.doTheSystemTrayThing]
      self.extraHeartbeatAlways = []

      self.lblArmoryStatus = QRichLabel('<font color=%s><i>Disconnected</i></font>' % \
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


      # Table to display ledger/activity
      self.ledgerTable = []
      self.ledgerModel = LedgerDispModelSimple(self.ledgerTable, self, self)

      self.ledgerProxy = LedgerDispSortProxy()
      self.ledgerProxy.setSourceModel(self.ledgerModel)
      self.ledgerProxy.setDynamicSortFilter(False)
      #self.ledgerProxy.sort(LEDGERCOLS.NumConf, Qt.AscendingOrder)

      self.ledgerView  = QTableView()
      self.ledgerView.setModel(self.ledgerProxy)
      #self.ledgerView.setModel(self.ledgerModel)
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
      #if self.usermode==USERMODE.Standard:
      cWidth = 20 # num-confirm icon width
      tWidth = 72 # date icon width
      initialColResize(self.ledgerView, [cWidth, 0, dateWidth, tWidth, 0.30, 0.40, 0.3])
      #elif self.usermode in (USERMODE.Advanced, USERMODE.Expert):
         #initialColResize(self.ledgerView, [20, dateWidth, 72, 0.30, 0.45, 150, 0, 0.20, 0.10])
         #self.ledgerView.setColumnHidden(LEDGERCOLS.WltID, False)
         #self.ledgerView.setColumnHidden(LEDGERCOLS.TxHash, False)
      
      self.connect(self.ledgerView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.dblClickLedger)


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


      self.btnModeSwitch = QPushButton('')
      #btnW,btnH = relaxedSizeStr(self, 'Switch to online mode!')
      #self.btnModeSwitch.setMaximumWidth( btnW)
      #self.btnModeSwitch.setMaximumHeight( btnH)
      self.connect(self.btnModeSwitch, SIGNAL('clicked()'), self.pressModeSwitchButton)
      self.lblDashMode = QRichLabel('',doWrap=False)
      self.lblDashMode.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      self.frmDashModeSub = makeHorizFrame([self.lblDashMode, self.btnModeSwitch], STYLE_SUNKEN)
      self.frmDashMode = makeHorizFrame(['Stretch', self.frmDashModeSub, 'Stretch'])
      self.lblDashDescr = QTextBrowser()
      self.lblDashDescr.setStyleSheet('padding: 5px')
      self.lblDashDescr.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
      qpal = self.lblDashDescr.palette()
      qpal.setColor(QPalette.Base, Colors.Background)
      self.lblDashDescr.setPalette(qpal)
      self.lblDashDescr.setOpenExternalLinks(True)

      dashLayout = QVBoxLayout()
      dashLayout.addWidget(self.frmDashMode)
      dashLayout.addWidget(self.lblDashDescr)
      self.tabDashboard.setLayout(dashLayout)

      


      # Combo box to filter ledger display
      self.comboWalletSelect = QComboBox()
      self.populateLedgerComboBox()

      ccl = lambda x: self.createCombinedLedger() # ignore the arg
      self.connect(self.comboWalletSelect, SIGNAL('activated(int)'), ccl)

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
      frmLower = makeLayoutFrame('Horiz', [QLabel('Filter:'), \
                                           self.comboWalletSelect, \
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
      self.DASHMODES = enum('Loading','Offline','Online')
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

      verStr = 'Armory %s-alpha / %s User' % (getVersionString(BTCARMORY_VERSION), \
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
      #if self.usermode==USERMODE.Standard:
      self.setMinimumSize(750,500)
      #else:
         #self.setMinimumSize(1200,300)

      #self.statusBar().showMessage('Blockchain loading, please wait...')


      from twisted.internet import reactor

      self.prevBlkLoadFinish = False
      self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Dashboard)
      if TheBDM.getBDMState()=='Uninitialized':
         # 'Uninitialized' means it is currently offline but want to be online
         TheBDM.loadBlockchain(wait=False)
         TheBDM.setAllowRescan(True)
      elif TheBDM.getBDMState()=='Offline':
         # 'Offline' means we are offline and want to stay offline
         TheBDM.setAllowRescan(False)

      # Show the appropriate information on the dashboard
      self.setDashboardDetails()


      ##########################################################################
      # Set up menu and actions
      #MENUS = enum('File', 'Wallet', 'User', "Tools", "Network")
      MENUS = enum('File', 'User', 'Tools', 'Wallets', 'Help')
      self.menu = self.menuBar()
      self.menusList = []
      self.menusList.append( self.menu.addMenu('&File') )
      self.menusList.append( self.menu.addMenu('&User') )
      self.menusList.append( self.menu.addMenu('&Tools') )
      self.menusList.append( self.menu.addMenu('&Wallets') )
      self.menusList.append( self.menu.addMenu('&Help') )
      #self.menusList.append( self.menu.addMenu('&Network') )


      exportFn = lambda: DlgExportTxHistory(self,self).exec_()
      actExportTx    = self.createAction('&Export Transactions', exportFn)
      actPreferences = self.createAction('&Preferences', self.openPrefDlg)
      actMinimApp    = self.createAction('&Minimize Armory', self.minimizeArmory)
      actExportLog   = self.createAction('Export &Log File', self.exportLogFile)
      actCloseApp    = self.createAction('&Quit Armory', self.closeForReal)
      self.menusList[MENUS.File].addAction(actExportTx)
      self.menusList[MENUS.File].addAction(actPreferences)
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


      actCreateNew      = self.createAction('&Create &New Wallet',        self.createNewWallet)
      actImportWlt      = self.createAction('&Import Armory Wallet',      self.execGetImportWltName)
      actRestorePaper   = self.createAction('&Restore from Paper Backup', self.execRestorePaperBackup)
      #actMigrateSatoshi = self.createAction('&Migrate Bitcoin Wallet',    self.execMigrateSatoshi)
      actAddressBook    = self.createAction('View &Address Book',         self.execAddressBook)


      self.menusList[MENUS.Wallets].addAction(actCreateNew)
      self.menusList[MENUS.Wallets].addAction(actImportWlt)
      self.menusList[MENUS.Wallets].addAction(actRestorePaper)
      #self.menusList[MENUS.Wallets].addAction(actMigrateSatoshi)
      self.menusList[MENUS.Wallets].addAction(actAddressBook)


      execAbout   = lambda: DlgHelpAbout(self).exec_()
      execVersion = lambda: self.checkForLatestVersion(wasRequested=True)
      actAboutWindow  = self.createAction('About Armory', execAbout)
      actVersionCheck = self.createAction('Armory Version...', execVersion)
      self.menusList[MENUS.Help].addAction(actAboutWindow)
      self.menusList[MENUS.Help].addAction(actVersionCheck)

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



      reactor.callLater(0.1,  self.execIntroDialog)
      reactor.callLater(5, self.Heartbeat)

      if CLI_ARGS:
         reactor.callLater(1, self.uriLinkClicked, CLI_ARGS[0])
      elif not self.firstLoad:
         # Don't need to bother the user on the first load with updating
         reactor.callLater(0.2, self.checkForLatestVersion)



   ####################################################
   def openPrefDlg(self):
      dlgPref = DlgPreferences(self, self)
      dlgPref.exec_()

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
         QMessageBox.information(self,'Restart Required', \
         'You must restart Armory in order for the user-mode switching '
         'to take effect.', QMessageBox.Ok)

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
            line = popNextLine(currLineIdx)

         if len(changeLog)==0 and not wasRequested:
            LOGINFO('You are running the latest version!')
         elif optChkVer[1:]==changeLog[0][0]:
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

      LOGINFO('Setting up networking...')
      self.internetAvail = False
      self.satoshiAvail  = False

      # Only need to check for the first blk file
      blk0001filename = os.path.join(BTC_HOME_DIR, 'blk0001.dat')
      self.haveBlkFile = os.path.exists(blk0001filename)

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
      

      # Check for Satoshi-client connection
      #self.satoshiAvail = self.bitcoindIsAvailable()
         


      # Check general internet connection
      self.internetAvail = False
      if not CLI_OPTIONS.forceOnline:
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
      LOGINFO('Bitcoin-Qt/bitcoind is Available: %s', self.bitcoindIsAvailable)
         

       

      if CLI_OPTIONS.offline:
         if CLI_OPTIONS.forceOnline:
            LOGERROR('Cannot mix --force-online and --offline options!  Using offline mode.')
         self.switchNetworkMode(NETWORKMODE.Offline)
         TheBDM.setOnlineMode(False, wait=False)
      elif self.onlineModeIsPossible():
         self.switchNetworkMode(NETWORKMODE.Full)
         TheBDM.setOnlineMode(True, wait=False)
      else:
         self.switchNetworkMode(NETWORKMODE.Offline)
         TheBDM.setOnlineMode(False, wait=False)
          

      #print 'InternetAvail = ', self.internetAvail
      #print 'SatoshiAvail  = ', self.satoshiAvail
      #print 'blkXXXX.dat   = ', self.haveBlkFile





   #############################################################################
   def onlineModeIsPossible(self):
      return ((self.internetAvail or CLI_OPTIONS.forceOnline) and \
               self.bitcoindIsAvailable() and \
               self.haveBlkFile)

   #############################################################################
   def bitcoindIsAvailable(self):
      # Check for Satoshi-client connection
      s = socket.socket()
      try:
         s.connect(('127.0.0.1', BITCOIN_PORT))
         s.close()
         return True
      except:
         return False


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
                     'or receive Bitcoins until connection is re-established.', \
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
   def updateWalletsOnNewBlockData(self):
      for wltID,wlt in self.walletMap.iteritems():
         # Absorb the new tx into the BDM & wallets
         TheBDM.scanBlockchainForTx(self.walletMap[wltID].cppWallet, wait=True)
   
         # Above doesn't return anything, but we want to know what it is...
         le = wlt.cppWallet.calcLedgerEntryForTxStr(pytxObj.serialize())

         # If it is ours, let's add it to the notifier queue
         if not le.getTxHash()=='\x00'*32:
            notifyIn  = self.getSettingOrSetDefault('NotifyBtcIn',  True)
            notifyOut = self.getSettingOrSetDefault('NotifyBtcOut', True)
            if (le.getValue()<=0 and notifyOut) or (le.getValue()>0 and notifyIn):
               self.notifyQueue.append([wltID, le, False])  # notifiedAlready=False
            self.createCombinedLedger()
            self.walletModel.reset()


   #############################################################################
   def newTxFunc(self, pytxObj):
      if TheBDM.getBDMState()=='Offline':
         return

      TheBDM.addNewZeroConfTx(pytxObj.serialize(), long(RightNow()), True, wait=False)
      self.newZeroConfSinceLastUpdate.append(pytxObj.serialize())

      #for wltID,wlt in self.walletMap.iteritems():
         ## Absorb the new tx into the BDM & wallets
         #TheBDM.rescanWalletZeroConf(self.walletMap[wltID].cppWallet)
   
         # Above doesn't return anything, but we want to know what it is...
         #le = wlt.cppWallet.calcLedgerEntryForTxStr(pytxObj.serialize())

         # If it is ours, let's add it to the notifier queue
         #if not le.getTxHash()=='\x00'*32:
            #notifyIn  = self.getSettingOrSetDefault('NotifyBtcIn',  True)
            #notifyOut = self.getSettingOrSetDefault('NotifyBtcOut', True)
            #if (le.getValue()<=0 and notifyOut) or (le.getValue()>0 and notifyIn):
               #self.notifyQueue.append([wltID, le, False])  # notifiedAlready=False
            #self.createCombinedLedger()
            #self.walletModel.reset()



   #############################################################################
   def uriLinkClicked(self, uriStr):
      LOGINFO('URI link clicked!')
      LOGINFO('The following string was passed through the socket')
      LOGINFO(uriStr.replace('%','%%'))
      uriDict = parseBitcoinURI(uriStr)
      if TheBDM.getBDMState()=='Offline':
         LOGERROR('Clicked "bitcoin:" link in offline mode.')
         self.bringArmoryToFront() 
         QMessageBox.warning(self, 'Offline Mode',
            'You clicked on a "bitcoin:" link, but Armory is in '
            'offline mode, and is not capable of creating transactions. '
            'Clicking on links will only work if Armory is connected '
            'to the Bitcoin network!', QMessageBox.Ok)
         return
         
      if len(uriDict)==0:
         warnMsg = ('It looks like you just clicked a "bitcoin:" link, but '
                    'that link is malformed.  ')
         if self.usermode == USERMODE.Standard:
            warnMsg += ('Please check the source of the link and enter the '
                        'transaction manually.')
         else:
            warnMsg += 'The raw URI string is:<br><br>' + uriStr
         QMessageBox.warning(self, 'Invalid URI', warnMsg, QMessageBox.Ok)
         LOGERROR(warnMsg)
         return

      if not uriDict.has_key('address'):
         QMessageBox.warning(self, 'The "bitcoin:" link you just clicked '
            'does not even contain an address!  There is nothing that '
            'Armory can do with this link!', QMessageBox.Ok)
         LOGERROR('No address in "bitcoin:" link!  Nothing to do!')
         return

      # Verify the URI is for the same network as this Armory instnance
      theAddrByte = checkAddrType(base58_to_binary(uriDict['address']))
      if theAddrByte!=-1 and theAddrByte!=ADDRBYTE:
         net = 'Unknown Network'
         if NETWORKS.has_key(theAddrByte):
            net = NETWORKS[theAddrByte]
         QMessageBox.warning(self, 'Wrong Network!', \
            'The address for the "bitcoin:" link you just clicked is '
            'for the wrong network!  You are on the <b>%s</b> '
            'and the address you supplied is for the the '
            '<b>%s</b>!' % (NETWORKS[ADDRBYTE], net), QMessageBox.Ok)
         LOGERROR('URI link is for the wrong network!')
         return

      # If the URI contains "req-" strings we don't recognize, throw error
      recognized = ['address','version','amount','label','message']
      for key,value in uriDict.iteritems():
         if key.startswith('req-') and not key[4:] in recognized:
            QMessageBox.warning(self,'Unsupported URI', 'The "bitcoin:" link '
               'you just clicked contains fields that are required but not '
               'recognized by Armory.  This may be an older version of Armory, '
               'or the link you clicked on uses an exotic, unsupported format.'
               '<br><br>The action cannot be completed.', \
               QMessageBox.Ok)
            LOGERROR('URI link contains unrecognized req- fields.')
            return
         
      self.bringArmoryToFront() 
      self.uriSendBitcoins(uriDict)
      

   #############################################################################
   def loadWalletsAndSettings(self):
      self.settings = SettingsFile(self.settingsPath)

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
      fullPath = unicode(QFileDialog.getOpenFileName(self, title, lastDir, typesStr))

      self.writeSetting('LastDirectory', os.path.split(fullPath)[0])
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
      if TheBDM.getBDMState()=='Offline':
         LOGWARNING('Rescan requested but Armory is in offline mode')
         return 

      if not TheBDM.isDirty:
         LOGWARNING('Rescan requested but there is no evidence it is needed')
         # no return, we will rescan anyway

      if not TheBDM.getAllowRescan():
         LOGWARNING('Rescan requested but allowRescan=False')
         return 

      if TheBDM.getBDMState()=='Scanning':
         LOGINFO('Need to rescan again but previous rescan not finished')
         return
      elif TheBDM.getBDMState()=='BlockchainReady':
         # Start it in the background
         self.needUpdateAfterScan = True
         TheBDM.rescanBlockchain(wait=False)
         self.setDashboardDetails()




   #############################################################################
   def finishLoadBlockchain(self):

      # Now that the blockchain is loaded, let's populate the wallet info
      if TheBDM.isInitialized():
         self.currBlockNum = TheBDM.getTopBlockHeight()
         self.setDashboardDetails()
         if not self.memPoolInit:
            mempoolfile = os.path.join(ARMORY_HOME_DIR,'mempool.bin')
            self.checkMemoryPoolCorruption(mempoolfile)
            TheBDM.enableZeroConf(mempoolfile)
            self.memPoolInit = True

         for wltID, wlt in self.walletMap.iteritems():
            LOGINFO('Syncing wallet: %s', wltID)
            self.walletMap[wltID].setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
            self.walletMap[wltID].syncWithBlockchain()

         
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
               
         self.netMode = NETWORKMODE.Full
      else:
         self.statusBar().showMessage('! Blockchain loading failed !', 10000)
   
   
      # This will force the table to refresh with new data
      self.setDashboardDetails()
      self.walletModel.reset()
      

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
         currIdx  = max(self.comboWalletSelect.currentIndex(), 0)
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
         self.writeSetting('LastFilterState', currIdx)
               

      if wltIDList==None:
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


      self.combinedLedger.sort(key=lambda x: x[LEDGERCOLS.UnixTime], reverse=True)
      self.ledgerSize = len(self.combinedLedger)

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
         self.ledgerTable = self.convertLedgerToTable(self.combinedLedger)
         self.ledgerModel.ledger = self.ledgerTable
         self.ledgerModel.reset()
         self.ledgerProxy.reset()

         #self.ledgerModel = LedgerDispModelSimple(self.ledgerTable, self, self)
         #self.ledgerProxy = LedgerDispSortProxy()
         ##self.ledgerProxy.setDynamicSortFilter(True)
         #self.ledgerProxy.setSourceModel(self.ledgerModel)
         #self.ledgerView.setModel(self.ledgerProxy)
         #self.ledgerView.hideColumn(LEDGERCOLS.isOther)
         #self.ledgerView.hideColumn(LEDGERCOLS.UnixTime)
         #self.ledgerView.hideColumn(LEDGERCOLS.WltID)
         #self.ledgerView.hideColumn(LEDGERCOLS.TxHash)
         #self.ledgerView.hideColumn(LEDGERCOLS.toSelf)
         #self.ledgerView.hideColumn(LEDGERCOLS.DoubleSpend)
         #self.ledgerView.setModel(self.ledgerModel)

      except AttributeError:
         raise
      

   #############################################################################
   def getFeeForTx(self, txHash):
      if TheBDM.isInitialized():
         txref = TheBDM.getTxByHash(txHash)
         if not txref.isInitialized():
            LOGERROR('Why no txref?  %s', binary_to_hex(txHash))
            return 0
         valIn, valOut = 0,0
         for i in range(txref.getNumTxIn()):
            valIn += TheBDM.getSentValue(txref.getTxIn(i))
         for i in range(txref.getNumTxOut()):
            valOut += txref.getTxOut(i).getValue()
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
         if not txref.isInitialized():
            return (0, 0)
         if txref.getNumTxOut()==1:
            return (txref.getTxOut(0).getValue(), -1)
         maxChainIndex = -5
         txOutChangeVal = 0
         txOutIndex = -1
         valSum = 0
         for i in range(txref.getNumTxOut()):
            valSum += txref.getTxOut(i).getValue()
            addr160 = txref.getTxOut(i).getRecipientAddr()
            addr    = wlt.getAddrByHash160(addr160)
            if addr and addr.chainIndex > maxChainIndex:
               maxChainIndex = addr.chainIndex
               txOutChangeVal = txref.getTxOut(i).getValue()
               txOutIndex = i
                  
         amt = valSum - txOutChangeVal
      return (amt, txOutIndex)
      

   #############################################################################
   def convertLedgerToTable(self, ledger):
      
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
            amt = self.determineSentToSelfAmt(le, wlt)[0]
            

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
         if wlt.commentsMap.has_key(le.getTxHash()):
            row.append(wlt.commentsMap[le.getTxHash()])
         else:
            # [[ COMMENTS ]] are not meant to be displayed on main ledger
            comment = self.getAddrCommentIfAvail(le.getTxHash())
            if comment.startswith('[[') and comment.endswith(']]'):
               comment = ''
            row.append(comment)

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

      return table2D

      
   #############################################################################
   def walletListChanged(self):
      self.walletModel.reset()
      self.populateLedgerComboBox()
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
      comboIdx = self.getSettingOrSetDefault('LastFilterState', 0)
      self.comboWalletSelect.setCurrentIndex(comboIdx)
      

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
   def getAddrCommentIfAvail(self, txHash):
      if not TheBDM.isInitialized():
         return ''
      else:
         tx = TheBDM.getTxByHash(txHash)
         if not tx.isInitialized():
            return ''
         else:
            addrComments = []
            pytx = PyTx().unserialize(tx.serialize())
            for txout in pytx.outputs: 
               scrType = getTxOutScriptType(txout.binScript)
               if not scrType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
                  continue
               a160 = TxOutScriptExtractAddr160(txout.binScript) 
               wltID = self.getWalletForAddr160(a160)
               if len(wltID)==0:
                  continue
               wlt = self.walletMap[wltID]
               if wlt.commentsMap.has_key(a160):
                  addrComments.append(wlt.commentsMap[a160])
            return '; '.join(addrComments)
      return ''
                  


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
                                           longLabel=descr)
      else:
          newWallet = PyBtcWallet().createNewWallet( \
                                           withEncrypt=False, \
                                           shortLabel=name, \
                                           longLabel=descr)


      TheBDM.registerWallet(newWallet, isFresh=True)
      TheBDM.addWalletToApplication(newWallet, isFresh=True)


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
      outputSide = []
      outputSide.append( [PyBtcAddress().createFromPublicKeyHash160(sweepTo160), outValue] )

      pytx = PyCreateAndSignTx(inputSide, outputSide)
      return (pytx, outValue, minFee)


      

   #############################################################################
   def BDM_SyncArmoryWallet_Confirm(self, pyWlt, startBlock=None, \
                                                   warnMsg=None, waitMsg=None):
      """
      We may want to retreive the the balance/UTXO list for a wallet, but doing
      so might require doing a full blockchain scan -- which can take a long
      time.  So we just do it if it's quick, or ask the user for confirmation
      and return false if they cancel.
     
      NOTE: This method does not return the Balance/UTXO list, but it
            guarantees that a call to retreive the Balance/UTXOs will
            be nearly instantaneous after this method returns a TRUE.
            The only way this doesn't work is if you import an address
            between the time you call this method, and the next time
            attempt to sync with the blockchain
      """

      if TheBDM.getBDMState()=='Offline':
         LOGWARN('Requested sync-wallet confirmation dialog, in offline mode')

      # Method to execute while the "Please Wait..." message is displayed
      def updateBalance():
         pyWlt.syncWithBlockchain(startBlock)


      if not pyWlt.checkIfRescanRequired():
         updateBalance()
         return True
      else:
         if warnMsg==None:
            warnMsg = ('In order to determine the new wallet balance, the entire, '
                   '<i>global</i> transaction history must be scanned. '
                   'This can take anywhere from 5 seconds to 3 minutes, '
                   'depending on your system.  During this time you will '
                   'not be able to use any other Armory features.'
                   '<br><br>'
                   'Do you wish to continue with this scan? '
                   'If you click "Cancel", your wallet balances may '
                   'appear incorrect until the next time Armory is '
                   'restarted.')

         doIt = QMessageBox.question(self, 'Blockchain Scan Needed', warnMsg, \
                QMessageBox.Ok | QMessageBox.Cancel);
      
         if doIt!=QMessageBox.Ok:
            return False

         if waitMsg==None:
            waitMsg = 'Collecting balance of new addresses'
         DlgExecLongProcess(updateBalance, waitMsg, self, self).exec_()
         return True
         
      
   #############################################################################
   def BDM_SyncCppWallet_Confirm(self, cppWlt, warnMsg=None, waitMsg=None):
      """
      Very similar to above except that you are trying to collect blockchain 
      information on a wallet that is not a persistent part of Armory -- for
      instance, you only need to collect information on one address, so you 
      create a temporary wallet just to scan it and then throw it away (since
      BDM only operates on wallets, not addresses)

      Same NOTE applies as the previous method:  discarding the wallet will
      not "un-sync" the BDM -- the BDM has already added the wallet addresses
      to it's registered list and will continue maintaining them even if there
      are no active wallets containin them.
      """

      # TODO:  not sure how to handle the offline case
      if not self.haveBlkFile:
         return False

      def scanBlockchain():
         TheBDM.scanBlockchainForTx(cppWlt, 0)

      if TheBDM.numBlocksToRescan(cppWlt)<2016:
         scanBlockchain()
         return True
      else:
         if warnMsg==None:
            warnMsg = ('In order to determine the balance of new addresses, '
                       'the entire <i>global transaction history</i> must be '
                       'scanned.  This can take anywhere from 5 seconds to 3 '
                       'minutes, depending on your system.  During this time '
                       'you will not be able to use any other Armory features.'
                       '<br><br>'
                       'Do you wish to continue with this scan? '
                       'If you click "Cancel", the scan will not be performed '
                       'and the original operation will not continue. ')

         doIt = QMessageBox.question(self, 'Blockchain Scan Needed', warnMsg, \
                QMessageBox.Ok | QMessageBox.Cancel);
      
         if doIt!=QMessageBox.Ok:
            return False

         if waitMsg==None:
            waitMsg = 'Collecting balance of new addresses'
         DlgExecLongProcess(scanBlockchain, waitMsg, self, self).exec_()
         return True


   #############################################################################
   def BDM_SyncAddressList_Confirm(self, addrList, warnMsg=None, waitMsg=None):
      """
      This method shortcuts the work needed to use the above method,
      BDM_SyncCppWallet_Confirm, on an arbitrary list of addresses.
      Because the BDM only operates on CppWallets, not individual addrs
      """
      if not isinstance(addrList, (list, tuple)):
         addrList = [addrList]

      cppWlt = Cpp.BtcWallet()
      for addr in addrList:
         if isinstance(addr, PyBtcAddress):
            cppWlt.addAddress_1_(addr.getAddr160())
         else:
            cppWlt.addAddress_1_(addr)

      return self.BDM_SyncCppWallet_Confirm(cppWlt, warnMsg, waitMsg)



   #############################################################################
   def confirmSweepScan(self, pybtcaddrList, targAddr160):

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
         QMessageBox.info(self, 'Armory is Offline', \
            'You have chosen to sweep %d addresses, but Armory is currently '
            'in offline mode.  The sweep will be performed the next time you '
            'go into online mode.  You can initiate online mode (if available) '
            'from the dashboard in the main window.')
         confirmed=True

      else:
         msgConfirm = ( \
            'Armory must scan the global transaction history in order to '
            'find any bitcoins associated with the addresses you supplied. '
            'Armory will go into offline mode temporarily while the scan '
            'is performed, and you will not have access to balances or be '
            'able to create transactions.  The scan may take several minutes.'
            '<br><br>')

         if TheBDM.getBDMState()=='Scanning':
            msgConfirm += ( \
               'There is currently another scan operation being performed.  '
               'Would you like to start the sweep operation after it completes? ')
         elif TheBDM.getBDMState()=='BlockchainReady':
            msgConfirm += ( \
               '<b>Would you like to start the scan operation right now?</b>')
   
         msgConfirm += ( \
               '<br><br>'
               'Clicking "No" will abort the entire sweep operation and Armory '
               'will go into online mode as soon as the current scan completes.')

         confirmed = QMessageBox.question(self, 'Confirm Rescan', msgConfirm, \
                                                QMessageBox.Yes | QMessageBox.No)

      if confirmed==QMessageBox.Yes:
         for addr in pybtcaddrList:
            TheBDM.registerImportedAddress(addr.getAddr160())
         self.sweepAfterScanList = pybtcaddrList
         self.sweepAfterScanTarg = targAddr160
         TheBDM.rescanBlockchain(wait=False)
         return True


   #############################################################################
   def finishSweepScan(self):
      sweepList, self.sweepAfterScanList = self.sweepAfterScanList,[]
     
      #######################################################################
      # The createSweepTx method will return instantly because the blockchain
      # has already been rescanned, as described above
      finishedTx, outVal, fee = self.createSweepAddrTx(sweepList, self.sweepAfterScanTarg)

      gt1 = len(sweepList)>1

      if outVal<=fee:
         QMessageBox.critical(self, 'Cannot sweep',\
         'You cannot sweep the funds from the address%s you specified, because '
         'the transaction fee would be equal to or greater than the amount '
         'swept.  The sweep operation will be canceled' % 'es' if gt1 else '',
          QMessageBox.Ok)
         return

      if outVal==0:
         QMessageBox.critical(self, 'Nothing to do', \
         'The private key%s you have provided does not appear to contain '
         'any funds.  There is nothing to sweep.' % 's' if gt1 else '', \
         QMessageBox.Ok)
         return

      wltID = self.getWalletForAddr160(self.sweepAfterScanTarg)
      wlt = self.walletMap[wltID]
      
      # Finally, if we got here, we're ready to broadcast!
      dispIn  = 'address <b>%s</b>' % sweepAddr.getAddrStr()
      if gt1:
         dispIn  = '<Multiple Addresses>' % sweepAddr.getAddrStr()
          
      dispOut = 'wallet <b>"%s"</b> (%s) ' % (wlt.labelName, wlt.uniqueIDB58)
      if DlgVerifySweep(dispIn, dispOut, outVal, fee).exec_():
         self.main.broadcastTransaction(finishedTx, dryRun=False)

      if TheBDM.getBDMState()=='BlockchainReady':
         self.wlt.syncWithBlockchain(0)

      self.main.walletListChanged()
      self.accept()

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
               QMessageBox.warning(self, 'Invalid Transaction', \
                  'The transaction that you just executed, does not '
                  'appear to have been accepted by the Bitcoin network. '
                  'This sometimes happens with legitimate transactions '
                  'when a fee is not included but was required.  Sometimes it '
                  'is caused by network issues.  '
                  'Or it is due to a bug in the Armory software.  '
                  '<br><br>Please consider reporting this error the the Armory '
                  'developers.  If you do, please use '
                  '"<b>File</b>"-->"<b>Export Log File</b>" '
                  'from the main window to make a copy of your log file to send '
                  'via email to alan.reiner@gmail.com.  Please also include any '
                  'information you might consider relevant about the context of '
                  'this failed transaction.' , \
                  QMessageBox.Ok)
                  
         self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Transactions)
         reactor.callLater(2, sendGetDataMsg)
         reactor.callLater(4, checkForTxInBDM)

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
      self.addWalletToApplication(PyBtcWallet().readWalletFile(newpath), \
                                                         walletIsNew=False)

   #############################################################################
   def execRestorePaperBackup(self):
      dlgPaper = DlgImportPaperWallet(self, self)
      if dlgPaper.exec_():
         LOGINFO('Raw import successful.  Searching blockchain for tx data...')
         
         wlt = dlgPaper.newWallet
         #DlgExecLongProcess(dlgPaper.newWallet.freshImportFindHighestIndex, \
               #'Restoring wallet.  This may take many minutes. Delete and '
               #'re-import wallet if this operation is interrupted.', \
               #self, self).exec_()
         #highestIdx = dlgPaper.newWallet.freshImportFindHighestIndex()
         self.safeAddWallet(wlt, walletIsNew=False)
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
         row = index.row()
         txHash = str(self.ledgerView.model().index(row, LEDGERCOLS.TxHash).data().toString())
         wltID  = str(self.ledgerView.model().index(row, LEDGERCOLS.WltID).data().toString())
         txtime = str(self.ledgerView.model().index(row, LEDGERCOLS.DateStr).data().toString())

         pytx = None
         txHashBin = hex_to_binary(txHash)
         if TheBDM.isInitialized():
            cppTx = TheBDM.getTxByHash(txHashBin)
            if cppTx.isInitialized():
               pytx = PyTx().unserialize(cppTx.serialize())

         if pytx==None:
            QMessageBox.critical(self, 'Invalid Tx:',
            'The transaction ID requested to be displayed does not exist in '
            'the blockchain or the zero-conf tx list...?', QMessageBox.Ok)
            return

         DlgDispTxInfo( pytx, self.walletMap[wltID], self, self, txtime=txtime).exec_()


   #############################################################################
   def clickSendBitcoins(self):
      if TheBDM.getBDMState()=='Offline':
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
            'You cannot send any Bitcoins until you create a wallet and '
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
      descrStr = ('You just clicked on a "bitcoin:" link requesting Bitcoins ' 
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
         return
      elif len(self.walletMap)>1:
         dlg = DlgWalletSelect(self, self, 'Send from Wallet...', descrStr, \
                               onlyMyWallets=True, atLeast=amt)
         if not dlg.exec_():
            return
         selectedWalletID = dlg.selectedID
      else:
         selectedWalletID = self.walletIDList[0]
         
      wlt = self.walletMap[selectedWalletID]
      dlgSend = DlgSendBitcoins(wlt, self, self, uriDict)
      dlgSend.exec_()
      

   #############################################################################
   def clickReceiveCoins(self):
      LOGDEBUG('Clicked "Receive Bitcoins Button"')
      wltID = None
      selectionMade = True
      if len(self.walletMap)==0:
         reply = QMessageBox.information(self, 'No Wallets!', \
            'You have not created any wallets which means there is nowhere to '
            'store you Bitcoins!  Would you like to create a wallet now?', \
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
            '<br><br><b><u>Advanced tip:</u></b> The log file is maintained at '
            'the following location on your hard drive:'
            '<br><br>'
            '%s'
            '<br><br>'
            'You can manually edit this file to remove information that '
            'does not seem relevant for debugging purposes, or simply '
            'copy the error messages inline to an email.' % ARMORY_LOG_FILE)
            
      #reply = QMessageBox.warning(self, 'Export Log File', \
      reply = MsgBoxCustom(MSGBOX.Warning, 'Privacy Warning', \
         'The log file contains information about your interactions '
         'with Armory and recent transactions.  This '
         'includes error messages produced by Armory that the developers need '
         'to help diagnose bugs.'
         '<br><br>'
         'This information may be considered sensitive by some users.  '
         'Log files should be protected the same '
         'way you would protect a watcing-only wallet, even though it '
         'typically will not even contain that much information.'
         '<br><br>'
         '<i>No private key data is ever written to the log file</i>, '
         'and all other logged information is related only to your '
         '<i>usage</i> of Armory.  There is no intention to record any '
         'information about your addresses, wallets or balances, but fragments '
         'of that information may be in this file.'
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
   def pressModeSwitchButton(self):
      if TheBDM.getBDMState() == 'BlockchainReady' and TheBDM.isDirty:
         self.startRescanBlockchain()
      elif TheBDM.getBDMState() in ('Offline','Uninitialized'):
         TheBDM.setOnlineMode(True)
         self.switchNetworkMode(NETWORKMODE.Full)
      else:
         LOGERROR('ModeSwitch button pressed when it should be disabled')
      time.sleep(0.3)
      self.setDashboardDetails()
         

   #############################################################################
   def setDashboardDetails(self):
      onlineAvail = self.onlineModeIsPossible()
      txtOfflineFunc = ( \
         'In offline mode, The following functionality is available:'
         '<ul>'
         '<li>Create, import or recover wallets</li>'
         '<li>Generate new receiving addresses for your wallets</li>'
         '<li>Create backups of your wallets (printed or digital)</li>'
         '<li>Import private keys to wallets</li>'
         '<li><b>Sign transactions created from an online system</b></li>'
         '<li>Change wallet encryption settings</li>'
         '<li>Sign messages</li>'
         '</ul>')

      txtOnlineFunc = ( \
         '<ul>'
         '<li>Create, import or recover Armory wallets</li>'
         '<li>Generate new addresses to receive coins</li>'
         '<li>Send Bitcoins to other people</li>'
         '<li>Create one-time backups of your wallets (in printed or digital form)</li>'
         '<li>Click on "bitcoin:" links in your web browser '
            '(not supported on some operating systems)</li>'
         '<li>Import private keys to wallets</li>'
         '<li>Monitor payments to watching-only wallets and create '
            'unsigned transactions</li>'
         '<li>Sign messages</li>'
         '<li><b>Create transactions for watching-only wallets, '
            'to be signed by an offline wallet</b></li>'
         '</ul>')

      if TheBDM.getBDMState() in ('Offline', 'Uninitialized'):
         if onlineAvail and not self.lastBDMState[1]==onlineAvail:
            LOGINFO('Dashboard switched to "Offline" mode, with online option')
            self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, False)
            self.btnModeSwitch.setVisible(True)
            self.btnModeSwitch.setEnabled(True)
            self.btnModeSwitch.setText('Go Online!')
            self.lblDashMode.setText('Armory is <u>offline</u>', size=4, bold=True)
            self.lblDashDescr.setText('You are currently in offline mode, but can '
               'switch to online mode by pressing the button above.  However, '
               'it is not recommended that you switch until '
               'Bitcoin-Qt/bitcoind is fully synchronized with the bitcoin network.  '
               'You will see a green checkmark in the bottom-right corner of '
               'the Bitcoin-Qt window when it is finished.'
               '<br><br>'
               'Switching to online mode will give you access '
               'to more Armory functionality, including sending and receiving '
               'bitcoins and viewing the balances and transaction histories '
               'of each of your wallets.')
         elif not onlineAvail and not self.lastBDMState[1]==onlineAvail:
            LOGINFO('Dashboard switched to "Offline" mode, can\'t go online')
            self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, False)
            self.btnModeSwitch.setVisible(False)
            self.btnModeSwitch.setEnabled(False)
            self.lblDashMode.setText( 'Armory is in <u>offline</u> mode', \
                                             size=4, color='TextWarn', bold=True)
            if not self.bitcoindIsAvailable():
               if self.internetAvail:
                  LOGDEBUG('Satoshi client is not available')
                  lblText  = 'You are currently in offline mode because '
                  lblText += 'Bitcoin-Qt/bitcoind is not running.  If you want '
                  lblText += 'to switch to online mode, please start Bitcoin-Qt '
                  lblText += 'and let it synchronize with the bitcoin network.  Once '
                  lblText += 'you see the green checkbox in the bottom-right corner '
                  lblText += 'of the Bitcoin-Qt window, press the button above to '
                  lblText += 'switch to online mode.  <i>Note: the button will '
                  lblText += 'appear as soon as you open the Bitcoin-Qt, but '
                  lblText += 'do not click it until you see the checkmark.</i>'
                  lblText += '<br><br>'
                  lblText += 'If you do not have Bitcoin-Qt installed, you can '
                  lblText += 'download it from <a href="http://www.bitcoin.org">'
                  lblText += 'http://www.bitcoin.org</a>.'
               else:
                  LOGDEBUG('Satoshi client and internet not available')
                  lblText += 'No internet connection was detected, and neither '
                  lblText += 'Bitcoin-Qt or bitcoind is running.  Most likely '
                  lblText += 'you are here because this is a system dedicated '
                  lblText += 'to manage offline wallets! '
                  lblText += '<br><br>'
                  lblText += '<b>If you expected Armory to be in online mode</b>, '
                  lblText += 'please verify your internet connection is active, then '
                  lblText += 'start Bitcoin-Qt and let it synchronize with the '
                  lblText += 'network (a green checkbox will appear in the bottom '
                  lblText += 'right corner of the Bitcoin-Qt window when it is '
                  lblText += 'finished).  Then restart Armory.'
                  lblText += '<br><br>'
                  lblText += 'If you do not have Bitcoin-Qt installed, you can '
                  lblText += 'download it from <a href="http://www.bitcoin.org">'
                  lblText += 'http://www.bitcoin.org</a>.'
            elif not self.internetAvail:
               LOGDEBUG('Internet is not detected')
               lblText  = 'You are currently in offline mode because '
               lblText += 'Armory could not detect an internet connection.  '
               lblText += 'If you think this is in error '
               lblText += '(perhaps because you are using proxies), then '
               lblText += 'restart Armory using the " --skip-online-check" option. '
               lblText += '<br><br>'
               lblText += 'If this is intended to be an offline computer, note '
               lblText += 'that it is not necessary to have Bitcoin-Qt or bitcoind '
               lblText += 'running.' 
            elif not self.haveBlkFile:
               LOGDEBUG('The blkXXXX.dat files are not accessible')
               lblText  = 'You are currently in offline mode because '
               lblText += 'Armory could not find the blockchain files produced '
               lblText += 'by Bitcoin-Qt.  Do you run Bitcoin-Qt (or bitcoind) '
               lblText += 'from a non-standard directory?   Armory expects to '
               lblText += 'find the blkXXXX.dat files in <br><br>%s<br><br> '
               lblText += 'If you know where it is located, please restart '
               lblText += 'Armory using the " --satoshi-datadir=<FOLDERPATH> '
               lblText += 'to notify Armory where to find them.'
            lblText += '<br><br>' + txtOfflineFunc
            self.lblDashDescr.setText(lblText)
      elif TheBDM.getBDMState() == 'BlockchainReady':
         self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, True)
         if self.netMode == NETWORKMODE.Disconnected:
            self.btnModeSwitch.setVisible(False)
            self.lblDashMode.setText( 'Armory is disconnected', size=4, color='TextWarn', bold=True)
            self.lblDashDescr.setText( \
               'Armory was previously online, but the connection to Bitcoin-Qt/'
               'bitcoind was interrupted.  You will not be able to send bitcoins or '
               'confirm receipt of bitcoins until the connection is reestablished.  '
               '<br><br>Please check that Bitcoin-Qt is open '
               'and synchronized with the network.  Armory will <i>try to reconnect</i> '
               'automatically when the connection is available again.  If Bitcoin-Qt is '
               'available again, and reconnection does not happen, please restart Armory.')
         elif TheBDM.needsRescan():
            self.btnModeSwitch.setVisible(True)
            self.btnModeSwitch.setText('Rescan Now')
            self.lblDashMode.setText( 'Armory is online, but needs to rescan ' \
                           'the blockchain</b>', size=4, color='TextWarn', bold=True)
            if len(self.sweepAfterScanList) > 0:
               self.lblDashDescr.setText( \
                  'Armory is currently online, but you have requested a sweep operation '
                  'on one or more private keys.  This requires searching the global '
                  'transaction history for the available balance of the keys to be '
                  'swept. '
                  '<br><br>'
                  'Press the button to start the blockchain scan, which '
                  'will also put Armory into offline mode for a few minutes '
                  'until the scan operation is complete')
            else:
               self.lblDashDescr.setText( \
                  '<b>Wallet balances may '
                  'be incorrect until the rescan operation is performed!</b>'
                  '<br><br>'
                  'Armory is currently online, but you have imported private keys '
                  'without initiating a blockchain scan.  Press the button to start '
                  'the blockchain scan, which '
                  'will also put Armory into offline mode for a few minutes '
                  'until the scan operation is complete.')
         else:
            # Fully online mode
            self.btnModeSwitch.setVisible(False)
            self.lblDashMode.setText( 'Armory is online!', color='TextGreen', size=4, bold=True)
            self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, True)
            self.lblDashDescr.setText( \
               '<p><b>You now have access to all the features Armory has to offer!</b><br>'
               'To see your balances and transaction history, please click '
               'on the "Transactions" tab above this text.  <br>'
               'Here\'s some things you can do with Armory Bitcoin Client:'
               '<br>' + txtOnlineFunc + '<br>'
               'If you experience any performance issues with Armory, '
               'please confirm that Bitcoin-Qt is running and <i>fully '
               'synchronized with the Bitcoin network</i>.  You will see '
               'a green checkmark in the bottom right corner of the '
               'Bitcoin-Qt window if it is synchronized.  If not, it is '
               'recommended you close Armory and restart it only when you '
               'see that checkmark.'
               '<br><br>'
               '<b>Please backup your wallets!</b>  Armory wallets are '
               '"deterministic", meaning they only need to be backed up '
               'one time (unless you have imported external addresses/keys). '
               'Make a backup and keep it in a safe place!  All funds from '
               'Armory-generated addresses will always be recoverable with '
               'a paper backup, any time in the future.  Use the "Backup '
               'Individual Keys" option fore each wallet to backup imported '
               'keys.</p>')
         self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Dashboard)
               
      elif TheBDM.getBDMState() == 'Scanning':
         LOGINFO('Dashboard switched to "Scanning" mode')
         self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Transactions, False)
         self.lblDashMode.setText( 'Armory is offline while scanning the blockchain', \
                                                                     size=4, bold=True)
         self.btnModeSwitch.setVisible(False)
         lblText = '<b>Please be patient, scanning may take several minutes!</b><br><br>'
         if len(self.walletMap)==0:
            lblText += 'Armory will go into online mode automatically, as soon as '
            lblText += 'the scan is complete.'
         else:
            lblText += 'Armory is scanning the global transaction history to retrieve '
            lblText += 'information about your wallets.  The "Transactions" tab will '
            lblText += 'update with your balances and transaction history as soon as '
            lblText += 'the scan is complete.'

         lblText += '<br><br>'
         lblText += 'While you wait, you may manage your Armory wallets.'
         lblText += '<br>'
         lblText += txtOfflineFunc
         lblText += '<br>'
         self.lblDashDescr.setText(lblText)
         self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Dashboard)
      else:
         LOGERROR('What the hell blockchain mode are we in?  %s', TheBDM.getBDMState())

      self.lastBDMState = [TheBDM.getBDMState(), onlineAvail]
      self.lblDashMode.setContentsMargins(50,5,50,5)
      #self.scrollDashDescr.setWidget(self.lblDashDescr)
      
         


   #############################################################################
   def Heartbeat(self, nextBeatSec=2):
      """
      This method is invoked when the app is initialized, and will
      run every 2 seconds, or whatever is specified in the nextBeatSec
      argument.
      """

      print 'Netmode:', self.netMode
      try:
         print 'BDMState:', TheBDM.getBDMState()
         for func in self.extraHeartbeatAlways:
            func()
   
         for idx,wltID in enumerate(self.walletIDList):
            self.walletMap[wltID].checkWalletLockTimeout()
   
         self.callCount +=1
         if TheBDM.getBDMState()=='Offline':
            # This call seems out of place, but it's because if you are in offline
            # mode, it needs to check periodically for the existence of Bitcoin-Qt
            # so that it can enable the "Go Online" button
            self.setDashboardDetails()
            return


         if self.netMode==NETWORKMODE.Disconnected:
            if self.onlineModeIsPossible():
               self.switchNetworkMode(NETWORKMODE.Full)
   
         if TheBDM.getBDMState()=='BlockchainReady':
            newBlocks = TheBDM.readBlkFileUpdate(wait=True)
            self.currBlockNum = TheBDM.getTopBlockHeight()
   
            if self.needUpdateAfterScan:
               print 'Running finishLoadBlockchain'
               self.finishLoadBlockchain()
               self.needUpdateAfterScan = False
               self.setDashboardDetails()
               
            if len(self.sweepAfterScanList)>0:
               self.finishSweepScan()
               for addr in self.sweepAfterScanList:
                  addr.binPrivKey32_Plain.destroy()
               self.sweepAfterScanList = []
               self.setDashboardDetails()
   
            # If we have new zero-conf transactions, scan them and update ledger
            if len(self.newZeroConfSinceLastUpdate)>0:
               self.newZeroConfSinceLastUpdate.reverse()
               for wltID in self.walletMap.keys():
                  wlt = self.walletMap[wltID]
                  TheBDM.rescanWalletZeroConf(wlt.cppWallet, wait=True)

            while len(self.newZeroConfSinceLastUpdate)>0:
               # For each new tx, check each wallet
               rawTx = self.newZeroConfSinceLastUpdate.pop()
               for wltID in self.walletMap.keys():
                  wlt = self.walletMap[wltID]
                  le = wlt.cppWallet.calcLedgerEntryForTxStr(rawTx)
                  if not le.getTxHash()=='\x00'*32:
                     notifyIn  = self.getSettingOrSetDefault('NotifyBtcIn',  True)
                     notifyOut = self.getSettingOrSetDefault('NotifyBtcOut', True)
                     if (le.getValue()<=0 and notifyOut) or (le.getValue()>0 and notifyIn):
                        self.notifyQueue.append([wltID, le, False])  # notifiedAlready=False
                     self.createCombinedLedger()
                     self.walletModel.reset()
   
            if newBlocks>0 and not TheBDM.isDirty:
   
               # This says "after scan", but works when new blocks appear, too
               TheBDM.updateWalletsAfterScan(wait=True)
               prevLedgSize = dict([(wltID, len(self.walletMap[wltID].getTxLedger())) \
                                                   for wltID in self.walletMap.keys()])
               print self.currBlockNum
         
               self.ledgerModel.reset()
               LOGINFO('New Block! : %d', self.currBlockNum)
               didAffectUs = False
   
               for wltID in self.walletMap.keys():
                  self.walletMap[wltID].syncWithBlockchain()
                  TheBDM.rescanWalletZeroConf(self.walletMap[wltID].cppWallet)
                  newLedgerSize = len(self.walletMap[wltID].getTxLedger())
                  didAffectUs = (prevLedgSize[wltID] != newLedgerSize)
            
               if didAffectUs:
                  LOGINFO('New Block contained a transaction relevant to us!')
                  self.walletListChanged()
                  self.notifyOnSurpriseTx(self.currBlockNum-newBlks, \
                                          self.currBlockNum+1)
      
               self.createCombinedLedger()
               self.blkReceived  = RightNow()
               self.writeSetting('LastBlkRecvTime', self.blkReceived)
            
               if self.netMode==NETWORKMODE.Full:
                  self.lblArmoryStatus.setText(\
                     '<font color=%s>Connected (%s blocks)</font> ' % \
                     (htmlColor('TextGreen'), self.currBlockNum))
      
               # Update the wallet view to immediately reflect new balances
               self.walletModel.reset()
      
               nowtime = RightNow()
               blkRecvAgo  = nowtime - self.blkReceived
               blkStampAgo = nowtime - TheBDM.getTopBlockHeader().getTimestamp()
               self.lblArmoryStatus.setToolTip('Last block timestamp is %s ago' % \
                                                      secondsToHumanTime(blkStampAgo))
               
   
               for func in self.extraHeartbeatOnline:
                  func()
   
               # Update the "prev" variables
               self.prevTopBlock = TheBDM.getTopBlockHeader().getBlockHeight()
   
      except:
         LOGEXCEPT('Error in heartbeat function')
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
      if not TheBDM.isInitialized() or RightNow()<self.notifyBlockedUntil:
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
            amt = self.determineSentToSelfAmt(le, wlt)[0]
            self.sysTray.showMessage('Your Bitcoins just did a lap!', \
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
                  #if addrComment:
                     #dispLines.append('%s...' % addrComment[:24])
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
                  #if addrComment:
                     #dispLines.append('%s...' % addrComment[:24])
               else:
                  dispLines.append('<Sent to Multiple Addresses>')
               dispLines.append('From:\tWallet "%s" (%s)' % (wlt.labelName, wltID))

            self.sysTray.showMessage(title, \
                                     '\n'.join(dispLines),  \
                                     QSystemTrayIcon.Information, \
                                     10000)

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
         TheBDM.execCleanShutdown()
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
      except:
         # Don't want a strange error here interrupt shutdown 
         pass

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
def execAndWait(cli_str):
   from subprocess import Popen, PIPE
   process = Popen(cli_str, shell=True, stdout=PIPE, stderr=PIPE)
   while process.poll() == None:
      time.sleep(0.1)
   out,err = process.communicate()
   return [out,err]



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
      TheBDM.execCleanShutdown()
      if reactor.threadpool is not None:
         reactor.threadpool.stop()
      QAPP.quit()
      os._exit(0)
      
   QAPP.connect(form, SIGNAL("lastWindowClosed()"), endProgram)
   reactor.addSystemEventTrigger('before', 'shutdown', endProgram)
   QAPP.setQuitOnLastWindowClosed(True)
   reactor.runReturn()
   os._exit(QAPP.exec_())


