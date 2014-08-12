#! /usr/bin/python
################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

from datetime import datetime
import hashlib
import logging
import math
import os
import platform
import random
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
import psutil
from copy import deepcopy

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol, ClientFactory

import CppBlockUtils as Cpp
from armoryengine.ALL import *
from armorycolors import Colors, htmlColor, QAPP
from armorymodels import *
from ui.toolsDialogs import MessageSigningVerificationDialog
import qrc_img_resources
from qtdefines import *
from qtdialogs import *
from ui.Wizards import WalletWizard, TxWizard
from ui.VerifyOfflinePackage import VerifyOfflinePackageDialog
from ui.UpgradeDownloader import UpgradeDownloaderDialog

from jasvet import verifySignature, readSigBlock
from announcefetch import AnnounceDataFetcher, ANNOUNCE_URL, ANNOUNCE_URL_BACKUP,\
   DEFAULT_FETCH_INTERVAL
from armoryengine.parseAnnounce import *
from armoryengine.PyBtcWalletRecovery import WalletConsistencyCheck

from armoryengine.MultiSigUtils import MultiSigLockbox
from ui.MultiSigDialogs import DlgSelectMultiSigOption, DlgLockboxManager, \
                    DlgMergePromNotes, DlgCreatePromNote, DlgImportAsciiBlock
from armoryengine.Decorators import RemoveRepeatingExtensions
from armoryengine.Block import PyBlock

# HACK ALERT: Qt has a bug in OS X where the system font settings will override
# the app's settings when a window is activated (e.g., Armory starts, the user
# switches to another app, and then switches back to Armory). There is a
# workaround, as used by TeXstudio and other programs.
# https://bugreports.qt-project.org/browse/QTBUG-5469 - Bug discussion.
# http://sourceforge.net/p/texstudio/bugs/594/?page=1 - Fix is mentioned.
# http://pyqt.sourceforge.net/Docs/PyQt4/qapplication.html#setDesktopSettingsAware
# - Mentions that this must be called before the app (QAPP) is created.
if OS_MACOSX:
   QApplication.setDesktopSettingsAware(False)

# PyQt4 Imports
# All the twisted/networking functionality
if OS_WINDOWS:
   from _winreg import *


class ArmoryMainWindow(QMainWindow):
   """ The primary Armory window """

   #############################################################################
   @TimeThisFunction
   def __init__(self, parent=None):
      super(ArmoryMainWindow, self).__init__(parent)


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
         self.lblLogoIcon.setPixmap(QPixmap(':/armory_logo_h44.png'))
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
      self.doShutdown = False
      self.downloadDict = {}
      self.notAvailErrorCount = 0
      self.satoshiVerWarnAlready = False
      self.satoshiLatestVer = None
      self.latestVer = {}
      self.downloadDict = {}
      self.satoshiHomePath = None
      self.satoshiExeSearchPath = None
      self.initSyncCircBuff = []
      self.latestVer = {}
      self.lastVersionsTxtHash = ''
      self.dlgCptWlt = None
      self.torrentFinished = False
      self.torrentCircBuffer = []
      self.lastAskedUserStopTorrent = 0
      self.wasSynchronizing = False
      self.announceIsSetup = False
      self.entropyAccum = []
      self.allLockboxes = []
      self.lockboxIDMap = {}
      self.cppLockboxWltMap = {}

      # Full list of notifications, and notify IDs that should trigger popups
      # when sending or receiving.
      self.lastAnnounceUpdate = {}
      self.changelog = []
      self.downloadLinks = {}
      self.almostFullNotificationList = {}
      self.notifyOnSend = set()
      self.notifyonRecv = set()
      self.versionNotification = {}
      self.notifyIgnoreLong  = []
      self.notifyIgnoreShort = []
      self.maxPriorityID = None
      self.satoshiVersions = ['','']  # [curr, avail]
      self.armoryVersions = [getVersionString(BTCARMORY_VERSION), '']
      self.NetworkingFactory = None


      # Kick off announcement checking, unless they explicitly disabled it
      # The fetch happens in the background, we check the results periodically
      self.announceFetcher = None
      self.setupAnnouncementFetcher()

      #delayed URI parsing dict
      self.delayedURIData = {}
      self.delayedURIData['qLen'] = 0

      #Setup the signal to spawn progress dialogs from the main thread
      self.connect(self, SIGNAL('initTrigger') , self.initTrigger)
      self.connect(self, SIGNAL('execTrigger'), self.execTrigger)
      self.connect(self, SIGNAL('checkForNegImports'), self.checkForNegImports)

      # We want to determine whether the user just upgraded to a new version
      self.firstLoadNewVersion = False
      currVerStr = 'v'+getVersionString(BTCARMORY_VERSION)
      if self.settings.hasSetting('LastVersionLoad'):
         lastVerStr = self.settings.get('LastVersionLoad')
         if not lastVerStr==currVerStr:
            LOGINFO('First load of new version: %s', currVerStr)
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
      self.doAutoBitcoind = \
            self.getSettingOrSetDefault('ManageSatoshi', not OS_MACOSX)


      # If we're going into online mode, start loading blockchain
      if self.doAutoBitcoind:
         self.startBitcoindIfNecessary()
      else:
         self.loadBlockchainIfNecessary()

      # Setup system tray and register "bitcoin:" URLs with the OS
      self.setupSystemTray()
      self.setupUriRegistration()


      self.extraHeartbeatSpecial  = []
      self.extraHeartbeatAlways   = []
      self.extraHeartbeatOnline   = []
      self.extraNewTxFunctions    = []
      self.extraNewBlockFunctions = []
      self.extraShutdownFunctions = []
      self.extraGoOnlineFunctions = []

      """
      pass a function to extraHeartbeatAlways to run on every heartbeat.
      pass a list for more control on the function, as
         [func, [args], keep_running],
      where:
         func is the function
         [args] is a list of arguments
         keep_running is a bool, pass False to remove the function from
         extraHeartbeatAlways on the next iteration
      """


      self.lblArmoryStatus = QRichLabel('<font color=%s>Offline</font> ' %
                                      htmlColor('TextWarn'), doWrap=False)

      self.statusBar().insertPermanentWidget(0, self.lblArmoryStatus)

      # Table for all the wallets
      self.walletModel = AllWalletsDispModel(self)
      self.walletsView  = QTableView()

      w,h = tightSizeNChar(self.walletsView, 55)
      viewWidth  = 1.2*w
      sectionSz  = 1.3*h
      viewHeight = 4.4*sectionSz

      self.walletsView.setModel(self.walletModel)
      self.walletsView.setSelectionBehavior(QTableView.SelectRows)
      self.walletsView.setSelectionMode(QTableView.SingleSelection)
      self.walletsView.verticalHeader().setDefaultSectionSize(sectionSz)
      self.walletsView.setMinimumSize(viewWidth, viewHeight)
      self.walletsView.setItemDelegate(AllWalletsCheckboxDelegate(self))
      self.walletsView.horizontalHeader().setResizeMode(0, QHeaderView.Fixed)



      self.walletsView.hideColumn(0)
      if self.usermode == USERMODE.Standard:
         initialColResize(self.walletsView, [20, 0, 0.35, 0.2, 0.2])
      else:
         initialColResize(self.walletsView, [20, 0.15, 0.30, 0.2, 0.20])


      if self.settings.hasSetting('LastFilterState'):
         if self.settings.get('LastFilterState')==4:
            self.walletsView.showColumn(0)


      self.connect(self.walletsView, SIGNAL('doubleClicked(QModelIndex)'), 
                   self.execDlgWalletDetails)
      self.connect(self.walletsView, SIGNAL('clicked(QModelIndex)'), 
                   self.execClickRow)

      self.walletsView.setColumnWidth(WLTVIEWCOLS.Visible, 20)
      w,h = tightSizeNChar(GETFONT('var'), 100)


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

      # Another table and model, for lockboxes
      self.lockboxLedgTable = []
      self.lockboxLedgModel = LedgerDispModelSimple(self.lockboxLedgTable, 
                                                                   self, self, isLboxModel=True)

      dateWidth    = tightSizeStr(self.ledgerView, '_9999-Dec-99 99:99pm__')[0]
      nameWidth    = tightSizeStr(self.ledgerView, '9'*32)[0]
      cWidth = 20 # num-confirm icon width
      tWidth = 72 # date icon width
      initialColResize(self.ledgerView, [cWidth, 0, dateWidth, tWidth, 0.30, 0.40, 0.3])

      self.connect(self.ledgerView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.dblClickLedger)

      self.ledgerView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.ledgerView.customContextMenuRequested.connect(self.showContextMenuLedger)

      btnAddWallet  = QPushButton("Create Wallet")
      btnImportWlt  = QPushButton("Import or Restore Wallet")
      self.connect(btnAddWallet,  SIGNAL('clicked()'), self.startWalletWizard)
      self.connect(btnImportWlt,  SIGNAL('clicked()'), self.execImportWallet)

      # Put the Wallet info into it's own little box
      lblAvail = QLabel("<b>Available Wallets:</b>")
      viewHeader = makeLayoutFrame(HORIZONTAL, [lblAvail, \
                                             'Stretch', \
                                             btnAddWallet, \
                                             btnImportWlt, ])
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
      self.setupDashboard()


      # Combo box to filter ledger display
      self.comboWltSelect = QComboBox()
      self.populateLedgerComboBox()
      self.connect(self.ledgerView.horizontalHeader(), \
                   SIGNAL('sortIndicatorChanged(int,Qt::SortOrder)'), \
                   self.changeLedgerSorting)


      self.connect(self.comboWltSelect, SIGNAL('activated(int)'), 
                   self.changeWltFilter)

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
      self.ttipTot = self.createToolTipWidget( \
            'Funds if all current transactions are confirmed.  '
            'Value appears gray when it is the same as your spendable funds.')
      self.ttipSpd = self.createToolTipWidget( 'Funds that can be spent <i>right now</i>')
      self.ttipUcn = self.createToolTipWidget( \
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
      ledgLayout.addWidget(self.ledgerView,           1,0)
      ledgLayout.addWidget(frmLower,                  2,0)
      ledgLayout.setRowStretch(0, 0)
      ledgLayout.setRowStretch(1, 1)
      ledgLayout.setRowStretch(2, 0)
      ledgFrame.setLayout(ledgLayout)

      self.tabActivity = QWidget()
      self.tabActivity.setLayout(ledgLayout)

      self.tabAnnounce = QWidget()
      self.setupAnnounceTab()


      # Add the available tabs to the main tab widget
      self.MAINTABS  = enum('Dash','Ledger','Announce')

      self.mainDisplayTabs.addTab(self.tabDashboard, 'Dashboard')
      self.mainDisplayTabs.addTab(self.tabActivity,  'Transactions')
      self.mainDisplayTabs.addTab(self.tabAnnounce,  'Announcements')

      ##########################################################################
      if USE_TESTNET and not CLI_OPTIONS.disableModules:
         self.loadArmoryModules()   
      ##########################################################################


      btnSendBtc   = QPushButton(tr("Send Bitcoins"))
      btnRecvBtc   = QPushButton(tr("Receive Bitcoins"))
      btnWltProps  = QPushButton(tr("Wallet Properties"))
      btnOfflineTx = QPushButton(tr("Offline Transactions"))
      btnMultisig  = QPushButton(tr("Lockboxes (Multi-Sig)"))

      self.connect(btnWltProps, SIGNAL('clicked()'), self.execDlgWalletDetails)
      self.connect(btnRecvBtc,  SIGNAL('clicked()'), self.clickReceiveCoins)
      self.connect(btnSendBtc,  SIGNAL('clicked()'), self.clickSendBitcoins)
      self.connect(btnOfflineTx,SIGNAL('clicked()'), self.execOfflineTx)
      self.connect(btnMultisig, SIGNAL('clicked()'), self.browseLockboxes)

      verStr = 'Armory %s / %s User' % (getVersionString(BTCARMORY_VERSION),
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
      if self.usermode in (USERMODE.Expert,):
         logoBtnFrame.append(btnMultisig)
      logoBtnFrame.append(lblInfo)
      logoBtnFrame.append('Stretch')

      btnFrame = makeVertFrame(logoBtnFrame, STYLE_SUNKEN)
      logoWidth=220
      btnFrame.sizeHint = lambda: QSize(logoWidth*1.0, 10)
      btnFrame.setMaximumWidth(logoWidth*1.2)
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
      self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Dash)


      ##########################################################################
      # Set up menu and actions
      #MENUS = enum('File', 'Wallet', 'User', "Tools", "Network")
      currmode = self.getSettingOrSetDefault('User_Mode', 'Advanced')
      MENUS = enum('File', 'User', 'Tools', 'Addresses', 'Wallets', \
                                                'MultiSig', 'Help')
      self.menu = self.menuBar()
      self.menusList = []
      self.menusList.append( self.menu.addMenu('&File') )
      self.menusList.append( self.menu.addMenu('&User') )
      self.menusList.append( self.menu.addMenu('&Tools') )
      self.menusList.append( self.menu.addMenu('&Addresses') )
      self.menusList.append( self.menu.addMenu('&Wallets') )
      self.menusList.append( self.menu.addMenu('&MultiSig') )
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


      actExportTx    = self.createAction('&Export Transactions...', exportTx)
      actSettings    = self.createAction('&Settings...', self.openSettings)
      actMinimApp    = self.createAction('&Minimize Armory', self.minimizeArmory)
      actExportLog   = self.createAction('Export &Log File...', self.exportLogFile)
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
      actSetModeDev = self.createAction('&Expert',    chngDev, True)

      modeActGrp.addAction(actSetModeStd)
      modeActGrp.addAction(actSetModeAdv)
      modeActGrp.addAction(actSetModeDev)

      self.menusList[MENUS.User].addAction(actSetModeStd)
      self.menusList[MENUS.User].addAction(actSetModeAdv)
      self.menusList[MENUS.User].addAction(actSetModeDev)



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

      def openMsgSigning():
         MessageSigningVerificationDialog(self,self).exec_()

      def openBlindBroad():
         if not satoshiIsAvailable():
            QMessageBox.warning(self, tr("Not Online"), tr("""
               Bitcoin Core is not available, so Armory will not be able
               to broadcast any transactions for you."""), QMessageBox.Ok)
            return
         DlgBroadcastBlindTx(self,self).exec_()



      actOpenSigner = self.createAction('&Message Signing/Verification...', openMsgSigning)
      if currmode=='Expert':
         actOpenTools  = self.createAction('&EC Calculator...',   lambda: DlgECDSACalc(self,self, 1).exec_())
         actBlindBroad = self.createAction('&Broadcast Raw Transaction...', openBlindBroad)

      self.menusList[MENUS.Tools].addAction(actOpenSigner)
      if currmode=='Expert':
         self.menusList[MENUS.Tools].addAction(actOpenTools)
         self.menusList[MENUS.Tools].addAction(actBlindBroad)

      def mkprom():
         if not TheBDM.getBDMState()=='BlockchainReady':
            QMessageBox.warning(self, tr('Offline'), tr("""
               Armory is currently offline, and cannot determine what funds are
               available for simulfunding.  Please try again when Armory is in
               online mode."""), QMessageBox.Ok)
         else:
            DlgCreatePromNote(self, self).exec_()


      def msrevsign():
         title = tr('Import Multi-Spend Transaction')
         descr = tr("""
            Import a signature-collector text block for review and signing.  
            It is usually a block of text with "TXSIGCOLLECT" in the first line,
            or a <i>*.sigcollect.tx</i> file.""")
         ftypes = ['Signature Collectors (*.sigcollect.tx)']
         dlgImport = DlgImportAsciiBlock(self, self, title, descr, ftypes, 
                                                         UnsignedTransaction)
         dlgImport.exec_()
         if dlgImport.returnObj:
            DlgMultiSpendReview(self, self, dlgImport.returnObj).exec_()
            

      simulMerge   = lambda: DlgMergePromNotes(self, self).exec_()
      actMakeProm    = self.createAction('Simulfund &Promissory Note', mkprom)
      actPromCollect = self.createAction('Simulfund &Collect && Merge', simulMerge)
      actMultiSpend  = self.createAction('Simulfund &Review && Sign', msrevsign)

      if not self.usermode==USERMODE.Expert:
         self.menusList[MENUS.MultiSig].menuAction().setVisible(False)


      # Addresses
      actAddrBook   = self.createAction('View &Address Book...',          self.execAddressBook)
      actSweepKey   = self.createAction('&Sweep Private Key/Address...',  self.menuSelectSweepKey)
      actImportKey  = self.createAction('&Import Private Key/Address...', self.menuSelectImportKey)

      self.menusList[MENUS.Addresses].addAction(actAddrBook)
      if not currmode=='Standard':
         self.menusList[MENUS.Addresses].addAction(actImportKey)
         self.menusList[MENUS.Addresses].addAction(actSweepKey)

      actCreateNew    = self.createAction('&Create New Wallet',        self.startWalletWizard)
      actImportWlt    = self.createAction('&Import or Restore Wallet', self.execImportWallet)
      actAddressBook  = self.createAction('View &Address Book',        self.execAddressBook)
      actRecoverWlt   = self.createAction('&Fix Damaged Wallet',        self.RecoverWallet)
      #actRescanOnly   = self.createAction('Rescan Blockchain', self.forceRescanDB)
      #actRebuildAll   = self.createAction('Rescan with Database Rebuild', self.forceRebuildAndRescan)

      self.menusList[MENUS.Wallets].addAction(actCreateNew)
      self.menusList[MENUS.Wallets].addAction(actImportWlt)
      self.menusList[MENUS.Wallets].addSeparator()
      self.menusList[MENUS.Wallets].addAction(actRecoverWlt)
      #self.menusList[MENUS.Wallets].addAction(actRescanOnly)
      #self.menusList[MENUS.Wallets].addAction(actRebuildAll)

      #self.menusList[MENUS.Wallets].addAction(actMigrateSatoshi)
      #self.menusList[MENUS.Wallets].addAction(actAddressBook)

      def execVersion():
         self.explicitCheckAnnouncements()
         self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Announce)

      execAbout   = lambda: DlgHelpAbout(self).exec_()
      execTrouble = lambda: webbrowser.open('https://bitcoinarmory.com/troubleshooting/')
      execBugReport = lambda: DlgBugReport(self, self).exec_()


      execVerifySigned = lambda: VerifyOfflinePackageDialog(self, self).exec_()
      actAboutWindow  = self.createAction(tr('&About Armory...'), execAbout)
      actVersionCheck = self.createAction(tr('Armory Version'), execVersion)
      actDownloadUpgrade = self.createAction(tr('Update Software...'), self.openDownloaderAll)
      actVerifySigned = self.createAction(tr('Verify Signed Package...'), execVerifySigned)
      actTroubleshoot = self.createAction(tr('Troubleshooting Armory'), execTrouble)
      actSubmitBug    = self.createAction(tr('Submit Bug Report'), execBugReport)
      actClearMemPool = self.createAction(tr('Clear All Unconfirmed'), self.clearMemoryPool)
      actRescanDB     = self.createAction(tr('Rescan Databases'), self.rescanNextLoad)
      actRebuildDB    = self.createAction(tr('Rebuild and Rescan Databases'), self.rebuildNextLoad)
      actFactoryReset = self.createAction(tr('Factory Reset'), self.factoryReset)
      actPrivacyPolicy = self.createAction(tr('Armory Privacy Policy'), self.showPrivacyGeneric)

      self.menusList[MENUS.Help].addAction(actAboutWindow)
      self.menusList[MENUS.Help].addAction(actVersionCheck)
      self.menusList[MENUS.Help].addAction(actDownloadUpgrade)
      self.menusList[MENUS.Help].addAction(actVerifySigned)
      self.menusList[MENUS.Help].addSeparator()
      self.menusList[MENUS.Help].addAction(actTroubleshoot)
      self.menusList[MENUS.Help].addAction(actSubmitBug)
      self.menusList[MENUS.Help].addAction(actPrivacyPolicy)
      self.menusList[MENUS.Help].addSeparator()
      self.menusList[MENUS.Help].addAction(actClearMemPool)
      self.menusList[MENUS.Help].addAction(actRescanDB)
      self.menusList[MENUS.Help].addAction(actRebuildDB)
      self.menusList[MENUS.Help].addAction(actFactoryReset)



      execMSHack = lambda: DlgSelectMultiSigOption(self,self).exec_()
      execBrowse = lambda: DlgLockboxManager(self,self).exec_()
      actMultiHacker = self.createAction(tr('Multi-Sig Lockboxes'), execMSHack)
      actBrowseLockboxes = self.createAction(tr('Lockbox &Manager...'), execBrowse)
      #self.menusList[MENUS.MultiSig].addAction(actMultiHacker)
      self.menusList[MENUS.MultiSig].addAction(actBrowseLockboxes)
      self.menusList[MENUS.MultiSig].addAction(actMakeProm)
      self.menusList[MENUS.MultiSig].addAction(actPromCollect)
      self.menusList[MENUS.MultiSig].addAction(actMultiSpend)



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

      haveGUI[0] = True
      haveGUI[1] = self
      BDMcurrentBlock[1] = 1

      if DO_WALLET_CHECK: 
         self.checkWallets()

      self.setDashboardDetails()

      from twisted.internet import reactor
      reactor.callLater(0.1,  self.execIntroDialog)
      reactor.callLater(1, self.Heartbeat)

      if self.getSettingOrSetDefault('MinimizeOnOpen', False) and not CLI_ARGS:
         LOGINFO('MinimizeOnOpen is True')
         reactor.callLater(0, self.minimizeArmory)


      if CLI_ARGS:
         reactor.callLater(1, self.uriLinkClicked, CLI_ARGS[0])


   ####################################################
   def getWatchingOnlyWallets(self):
      result = []
      for wltID in self.walletIDList:
         if self.walletMap[wltID].watchingOnly:
            result.append(wltID)
      return result


   ####################################################
   def changeWltFilter(self):

      currIdx  = max(self.comboWltSelect.currentIndex(), 0)
      currText = str(self.comboWltSelect.currentText()).lower()

      if currText.lower().startswith('custom filter'):
         self.walletsView.showColumn(0)
      else:
         self.walletsView.hideColumn(0)


      # If "custom" is selected, do nothing...
      if currIdx==4:
         return

      for i in range(len(self.walletVisibleList)):
         self.walletVisibleList[i] = False
         self.setWltSetting(self.walletIDList[i], 'LedgerShow', False)

      # If a specific wallet is selected, just set that and you're done
      if currIdx >= 4:
         self.walletVisibleList[currIdx-7] = True
         self.setWltSetting(self.walletIDList[currIdx-7], 'LedgerShow', True)
      else:
         # Else we walk through the wallets and flag the particular ones
         typelist = [[wid, determineWalletType(self.walletMap[wid], self)[0]] \
                                                   for wid in self.walletIDList]

         for i,winfo in enumerate(typelist):
            wid,wtype = winfo[:]
            if currIdx==0:
               # My wallets
               doShow = wtype in [WLTTYPES.Offline,WLTTYPES.Crypt,WLTTYPES.Plain]
               self.walletVisibleList[i] = doShow
               self.setWltSetting(wid, 'LedgerShow', doShow)
            elif currIdx==1:
               # Offline wallets
               doShow = winfo[1] in [WLTTYPES.Offline]
               self.walletVisibleList[i] = doShow
               self.setWltSetting(wid, 'LedgerShow', doShow)
            elif currIdx==2:
               # Others' Wallets
               doShow = winfo[1] in [WLTTYPES.WatchOnly]
               self.walletVisibleList[i] = doShow
               self.setWltSetting(wid, 'LedgerShow', doShow)
            elif currIdx==3:
               # All Wallets
               self.walletVisibleList[i] = True
               self.setWltSetting(wid, 'LedgerShow', True)

      self.walletsView.reset()
      self.createCombinedLedger()
      if self.frmLedgUpDown.isVisible():
         self.changeNumShow()


   ############################################################################
   def loadArmoryModules(self):
      """
      This method checks for any .py files in the exec directory
      """ 
      moduleDir = os.path.join(GetExecDir(), 'modules')
      if not moduleDir or not os.path.exists(moduleDir):
         return

      LOGWARN('Attempting to load modules from: %s' % moduleDir)

      from dynamicImport import getModuleList, dynamicImport

      # This call does not eval any code in the modules.  It simply
      # loads the python files as raw chunks of text so we can
      # check hashes and signatures
      modMap = getModuleList(moduleDir)
      for name,infoMap in modMap.iteritems():
         modPath = os.path.join(infoMap['SourceDir'], infoMap['Filename'])
         modHash = binary_to_hex(sha256(infoMap['SourceCode']))

         isSignedByATI = False
         if 'Signature' in infoMap:
            """
            Signature file contains multiple lines, of the form "key=value\n"
            The last line is the hex-encoded signature, which is over the 
            source code + everything in the sig file up to the last line.
            The key-value lines may contain properties such as signature 
            validity times/expiration, contact info of author, etc.
            """
            sigFile = infoMap['SigData']
            sigLines = [line.strip() for line in sigFile.strip().split('\n')]
            properties = dict([line.split('=') for line in sigLines[:-1]])
            msgSigned = infoMap['SourceCode'] + '\x00' + '\n'.join(sigLines[:1])

            sbdMsg = SecureBinaryData(sha256(msgSigned))
            sbdSig = SecureBinaryData(hex_to_binary(sigLines[-1]))
            sbdPub = SecureBinaryData(hex_to_binary(ARMORY_INFO_SIGN_PUBLICKEY))
            isSignedByATI = CryptoECDSA().VerifyData(sbdMsg, sbdSig, sbdPub)
            LOGWARN('Sig on "%s" is valid: %s' % (name, str(isSignedByATI)))
            

         if not isSignedByATI and not USE_TESTNET:
            reply = QMessageBox.warning(self, tr("UNSIGNED Module"), tr("""
               Armory detected the following module which is 
               <font color="%s"><b>unsigned</b></font> and may be dangerous:
               <br><br>
                  <b>Module Name:</b>  %s<br>
                  <b>Module Path:</b>  %s<br>
                  <b>Module Hash:</b>  %s<br>
               <br><br>
               You should <u>never</u> trust unsigned modules!  At this time,
               Armory will not allow you to run this module unless you are 
               in testnet mode.""") % \
               (name, modPath, modHash[:16]), QMessageBox.Ok)

            if not reply==QMessageBox.Yes:
               continue


         module = dynamicImport(moduleDir, name, globals())
         plugObj = module.PluginObject(self)

         if not hasattr(plugObj,'getTabToDisplay') or \
            not hasattr(plugObj,'tabName'):
            LOGERROR('Module is malformed!  No tabToDisplay or tabName attrs')
            QMessageBox.critical(self, tr("Bad Module"), tr("""
               The module you attempted to load (%s) is malformed.  It is 
               missing attributes that are needed for Armory to load it.  
               It will be skipped.""") % name, QMessageBox.Ok)
            continue
               
         verPluginInt = getVersionInt(readVersionString(plugObj.maxVersion))
         verArmoryInt = getVersionInt(BTCARMORY_VERSION)
         if verArmoryInt >verPluginInt:
            reply = QMessageBox.warning(self, tr("Outdated Module"), tr("""
               Module "%s" is only specified to work up to Armory version %s.
               You are using Armory version %s.  Please remove the module if
               you experience any problems with it, or contact the maintainer
               for a new version.
               <br><br>
               Do you want to continue loading the module?"""), 
               QMessageBox.Yes | QMessageBox.No)

            if not reply==QMessageBox.Yes:
               continue

         # All plugins should have "tabToDisplay" and "tabName" attributes
         LOGWARN('Adding module to tab list: "' + plugObj.tabName + '"')
         self.mainDisplayTabs.addTab(plugObj.getTabToDisplay(), plugObj.tabName)

         # Also inject any extra methods that will be 
         injectFuncList = [ \
               ['injectHeartbeatAlwaysFunc', 'extraHeartbeatAlways'], 
               ['injectHeartbeatOnlineFunc', 'extraHeartbeatOnline'], 
               ['injectGoOnlineFunc',        'extraGoOnlineFunctions'], 
               ['injectNewTxFunc',           'extraNewTxFunctions'], 
               ['injectNewBlockFunc',        'extraNewBlockFunctions'], 
               ['injectShutdownFunc',        'extraShutdownFunctions'] ]

         # Add any methods
         for plugFuncName,funcListName in injectFuncList:
            if not hasattr(plugObj, plugFuncName):
               continue
      
            if not hasattr(self, funcListName):
               LOGERROR('Missing an ArmoryQt list variable: %s' % funcListName)
               continue

            LOGINFO('Found module function: %s' % plugFuncName)
            funcList = getattr(self, funcListName)
            plugFunc = getattr(plugObj, plugFuncName)
            funcList.append(plugFunc)
                                    

   ############################################################################
   def factoryReset(self):
      """
      reply = QMessageBox.information(self,'Factory Reset', \
         'You are about to revert all Armory settings '
         'to the state they were in when Armory was first installed.  '
         '<br><br>'
         'If you click "Yes," Armory will exit after settings are '
         'reverted.  You will have to manually start Armory again.'
         '<br><br>'
         'Do you want to continue? ', \
         QMessageBox.Yes | QMessageBox.No)

      if reply==QMessageBox.Yes:
         self.removeSettingsOnClose = True
         self.closeForReal()
      """

      if DlgFactoryReset(self,self).exec_():
         # The dialog already wrote all the flag files, just close now
         self.closeForReal()


   ####################################################
   def showPrivacyGeneric(self):
      DlgPrivacyPolicy().exec_()

   ####################################################
   def clearMemoryPool(self):
      touchFile( os.path.join(ARMORY_HOME_DIR, 'clearmempool.flag') )
      msg = tr("""
         The next time you restart Armory, all unconfirmed transactions will
         be cleared allowing you to retry any stuck transactions.""")
      if not self.doAutoBitcoind:
         msg += tr("""
         <br><br>Make sure you also restart Bitcoin-Qt
         (or bitcoind) and let it synchronize again before you restart
         Armory.  Doing so will clear its memory pool, as well""")
      QMessageBox.information(self, tr('Memory Pool'), msg, QMessageBox.Ok)



   ####################################################
   def registerWidgetActivateTime(self, widget):
      # This is a bit of a hack, but it's a very isolated method to make 
      # it easy to link widgets to my entropy accumulator

      # I just realized this doesn't do exactly what I originally intended...
      # I wanted it to work on arbitrary widgets like QLineEdits, but using
      # super is not the answer.  What I want is the original class method
      # to be called after logging keypress, not its superclass method.
      # Nonetheless, it does do what I need it to, as long as you only
      # registered frames and dialogs, not individual widgets/controls.
      mainWindow = self
      
      def newKPE(wself, event=None):
         mainWindow.logEntropy()
         super(wself.__class__, wself).keyPressEvent(event)

      def newKRE(wself, event=None):
         mainWindow.logEntropy()
         super(wself.__class__, wself).keyReleaseEvent(event)

      def newMPE(wself, event=None):
         mainWindow.logEntropy()
         super(wself.__class__, wself).mousePressEvent(event)

      def newMRE(wself, event=None):
         mainWindow.logEntropy()
         super(wself.__class__, wself).mouseReleaseEvent(event)

      from types import MethodType
      widget.keyPressEvent     = MethodType(newKPE, widget)
      widget.keyReleaseEvent   = MethodType(newKRE, widget)
      widget.mousePressEvent   = MethodType(newMPE, widget)
      widget.mouseReleaseEvent = MethodType(newMRE, widget)

      
   ####################################################
   def logEntropy(self):
      try:
         self.entropyAccum.append(RightNow())
         self.entropyAccum.append(QCursor.pos().x()) 
         self.entropyAccum.append(QCursor.pos().y()) 
      except:
         LOGEXCEPT('Error logging keypress entropy')

   ####################################################
   def getExtraEntropyForKeyGen(self):
      # The entropyAccum var has all the timestamps, down to the microsecond,
      # of every keypress and mouseclick made during the wallet creation
      # wizard.   Also logs mouse positions on every press, though it will
      # be constant while typing.  Either way, even, if they change no text
      # and use a 5-char password, we will still pickup about 40 events. 
      # Then we throw in the [name,time,size] triplets of some volatile 
      # system directories, and the hash of a file in that directory that
      # is expected to have timestamps and system-dependent parameters.
      # Finally, take a desktop screenshot... 
      # All three of these source are likely to have sufficient entropy alone.
      source1,self.entropyAccum = self.entropyAccum,[]

      if len(source1)==0:
         LOGERROR('Error getting extra entropy from mouse & key presses')

      source2 = []

      try:
         if OS_WINDOWS:
            tempDir = os.getenv('TEMP')
            extraFiles = []
         elif OS_LINUX:
            tempDir = '/var/log'
            extraFiles = ['/var/log/Xorg.0.log']
         elif OS_MACOSX:
            tempDir = '/var/log'
            extraFiles = ['/var/log/system.log']

         # A simple listing of the directory files, sizes and times is good
         if os.path.exists(tempDir):
            for fname in os.listdir(tempDir):
               fullpath = os.path.join(tempDir, fname)
               sz = os.path.getsize(fullpath)
               tm = os.path.getmtime(fullpath)
               source2.append([fname, sz, tm])

         # On Linux we also throw in Xorg.0.log
         for f in extraFiles:
            if os.path.exists(f):
               with open(f,'rb') as infile:
                  source2.append(hash256(infile.read()))
               
         if len(source2)==0:
            LOGWARN('Second source of supplemental entropy will be empty')

      except:
         LOGEXCEPT('Error getting extra entropy from filesystem')


      source3 = ''
      try:
         pixDesk = QPixmap.grabWindow(QApplication.desktop().winId())
         pixRaw = QByteArray()
         pixBuf = QBuffer(pixRaw)
         pixBuf.open(QIODevice.WriteOnly)
         pixDesk.save(pixBuf, 'PNG')
         source3 = pixBuf.buffer().toHex()
      except:
         LOGEXCEPT('Third source of entropy (desktop screenshot) failed')
         
      if len(source3)==0:
         LOGWARN('Error getting extra entropy from screenshot')

      LOGINFO('Adding %d keypress events to the entropy pool', len(source1)/3)
      LOGINFO('Adding %s bytes of filesystem data to the entropy pool', 
                  bytesToHumanSize(len(str(source2))))
      LOGINFO('Adding %s bytes from desktop screenshot to the entropy pool', 
                  bytesToHumanSize(len(str(source3))/2))
      

      allEntropy = ''.join([str(a) for a in [source1, source1, source3]])
      return SecureBinaryData(HMAC256('Armory Entropy', allEntropy))
      



   ####################################################
   def rescanNextLoad(self):
      reply = QMessageBox.warning(self, tr('Queue Rescan?'), tr("""
         The next time you restart Armory, it will rescan the blockchain
         database, and reconstruct your wallet histories from scratch.
         The rescan will take 10-60 minutes depending on your system.
         <br><br>
         Do you wish to force a rescan on the next Armory restart?"""), \
         QMessageBox.Yes | QMessageBox.No)
      if reply==QMessageBox.Yes:
         touchFile( os.path.join(ARMORY_HOME_DIR, 'rescan.flag') )

   ####################################################
   def rebuildNextLoad(self):
      reply = QMessageBox.warning(self, tr('Queue Rebuild?'), tr("""
         The next time you restart Armory, it will rebuild and rescan
         the entire blockchain database.  This operation can take between
         30 minutes and 4 hours depending on you system speed.
         <br><br>
         Do you wish to force a rebuild on the next Armory restart?"""), \
         QMessageBox.Yes | QMessageBox.No)
      if reply==QMessageBox.Yes:
         touchFile( os.path.join(ARMORY_HOME_DIR, 'rebuild.flag') )

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
      LOGDEBUG('openSettings')
      dlgSettings = DlgSettings(self, self)
      dlgSettings.exec_()

   ####################################################
   def setupSystemTray(self):
      LOGDEBUG('setupSystemTray')
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
   @AllowAsync
   def registerBitcoinWithFF(self):
      #the 3 nodes needed to add to register bitcoin as a protocol in FF
      rdfschemehandler = 'about=\"urn:scheme:handler:bitcoin\"'
      rdfscheme = 'about=\"urn:scheme:bitcoin\"'
      rdfexternalApp = 'about=\"urn:scheme:externalApplication:bitcoin\"'

      #find mimeTypes.rdf file
      home = os.getenv('HOME')
      out,err = execAndWait('find %s -type f -name \"mimeTypes.rdf\"' % home)

      for rdfs in out.split('\n'):
         if rdfs:
            try:
               FFrdf = open(rdfs, 'r+')
            except:
               continue

            ct = FFrdf.readlines()
            rdfsch=-1
            rdfsc=-1
            rdfea=-1
            i=0
            #look for the nodes
            for line in ct:
               if rdfschemehandler in line:
                  rdfsch=i
               elif rdfscheme in line:
                  rdfsc=i
               elif rdfexternalApp in line:
                  rdfea=i
               i+=1

            #seek to end of file
            FFrdf.seek(-11, 2)
            i=0;

            #add the missing nodes
            if rdfsch == -1:
               FFrdf.write(' <RDF:Description RDF:about=\"urn:scheme:handler:bitcoin\"\n')
               FFrdf.write('                  NC:alwaysAsk=\"false\">\n')
               FFrdf.write('    <NC:externalApplication RDF:resource=\"urn:scheme:externalApplication:bitcoin\"/>\n')
               FFrdf.write('    <NC:possibleApplication RDF:resource=\"urn:handler:local:/usr/bin/xdg-open\"/>\n')
               FFrdf.write(' </RDF:Description>\n')
               i+=1

            if rdfsc == -1:
               FFrdf.write(' <RDF:Description RDF:about=\"urn:scheme:bitcoin\"\n')
               FFrdf.write('                  NC:value=\"bitcoin\">\n')
               FFrdf.write('    <NC:handlerProp RDF:resource=\"urn:scheme:handler:bitcoin\"/>\n')
               FFrdf.write(' </RDF:Description>\n')
               i+=1

            if rdfea == -1:
               FFrdf.write(' <RDF:Description RDF:about=\"urn:scheme:externalApplication:bitcoin\"\n')
               FFrdf.write('                  NC:prettyName=\"xdg-open\"\n')
               FFrdf.write('                  NC:path=\"/usr/bin/xdg-open\" />\n')
               i+=1

            if i != 0:
               FFrdf.write('</RDF:RDF>\n')

            FFrdf.close()

   #############################################################################
   def setupUriRegistration(self, justDoIt=False):
      """
      Setup Armory as the default application for handling bitcoin: links
      """
      LOGINFO('setupUriRegistration')

      if USE_TESTNET:
         return

      if OS_LINUX:
         out,err = execAndWait('gconftool-2 --get /desktop/gnome/url-handlers/bitcoin/command')
         out2,err = execAndWait('xdg-mime query default x-scheme-handler/bitcoin')

         #check FF protocol association
         #checkFF_thread = threading.Thread(target=self.registerBitcoinWithFF)
         #checkFF_thread.start()
         self.registerBitcoinWithFF(async=True)

         def setAsDefault():
            LOGINFO('Setting up Armory as default URI handler...')
            execAndWait('gconftool-2 -t string -s /desktop/gnome/url-handlers/bitcoin/command "python /usr/lib/armory/ArmoryQt.py \"%s\""')
            execAndWait('gconftool-2 -s /desktop/gnome/url-handlers/bitcoin/needs_terminal false -t bool')
            execAndWait('gconftool-2 -t bool -s /desktop/gnome/url-handlers/bitcoin/enabled true')
            execAndWait('xdg-mime default armory.desktop x-scheme-handler/bitcoin')


         if ('no value' in out.lower() or 'no value' in err.lower()) and not 'armory.desktop' in out2.lower():
            # Silently add Armory if it's never been set before
            setAsDefault()
         elif (not 'armory' in out.lower() or not 'armory.desktop' in out2.lower()) and not self.firstLoad:
            # If another application has it, ask for permission to change it
            # Don't bother the user on the first load with it if verification is
            # needed.  They have enough to worry about with this weird new program...
            if not self.getSettingOrSetDefault('DNAA_DefaultApp', False):
               reply = MsgBoxWithDNAA(MSGBOX.Question, 'Default URL Handler', \
                  'Armory is not set as your default application for handling '
                  '"bitcoin:" links.  Would you like to use Armory as the '
                  'default?', 'Do not ask this question again')
               if reply[0]==True:
                  setAsDefault()
               if reply[1]==True:
                  self.writeSetting('DNAA_DefaultApp', True)

      elif OS_WINDOWS:
         # Check for existing registration (user first, then root, if necessary)
         action = 'DoNothing'
         modulepathname = '"'
         if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
            app_path = os.path.join(app_dir, sys.executable)
         elif __file__:
            return #running from a .py script, not gonna register URI on Windows

         #justDoIt = True
         import ctypes
         GetModuleFileNameW = ctypes.windll.kernel32.GetModuleFileNameW
         GetModuleFileNameW.restype = ctypes.c_int
         app_path = ctypes.create_string_buffer(1024)
         rtlength = ctypes.c_int()
         rtlength = GetModuleFileNameW(None, ctypes.byref(app_path), 1024)
         passstr = str(app_path.raw)

         modulepathname += unicode(passstr[0:(rtlength*2)], encoding='utf16') + u'" "%1"'
         modulepathname = modulepathname.encode('utf8')

         rootKey = 'bitcoin\\shell\\open\\command'
         try:
            userKey = 'Software\\Classes\\' + rootKey
            registryKey = OpenKey(HKEY_CURRENT_USER, userKey, 0, KEY_READ)
            val,code = QueryValueEx(registryKey, '')
            if 'armory' in val.lower():
               if val.lower()==modulepathname.lower():
                  LOGINFO('Armory already registered for current user.  Done!')
                  return
               else:
                  action = 'DoIt' #armory is registered, but to another path
            else:
               # Already set to something (at least created, which is enough)
               action = 'AskUser'
         except:
            # No user-key set, check if root-key is set
            try:
               registryKey = OpenKey(HKEY_CLASSES_ROOT, rootKey, 0, KEY_READ)
               val,code = QueryValueEx(registryKey, '')
               if 'armory' in val.lower():
                  LOGINFO('Armory already registered at admin level.  Done!')
                  return
               else:
                  # Root key is set (or at least created, which is enough)
                  action = 'AskUser'
            except:
               action = 'DoIt'

         dontAsk = self.getSettingOrSetDefault('DNAA_DefaultApp', False)
         dontAskDefault = self.getSettingOrSetDefault('AlwaysArmoryURI', False)
         if justDoIt:
            LOGINFO('URL-register: just doing it')
            action = 'DoIt'
         elif dontAsk and dontAskDefault:
            LOGINFO('URL-register: user wants to do it by default')
            action = 'DoIt'
         elif action=='AskUser' and not self.firstLoad and not dontAsk:
            # If another application has it, ask for permission to change it
            # Don't bother the user on the first load with it if verification is
            # needed.  They have enough to worry about with this weird new program...
            reply = MsgBoxWithDNAA(MSGBOX.Question, 'Default URL Handler', \
               'Armory is not set as your default application for handling '
               '"bitcoin:" links.  Would you like to use Armory as the '
               'default?', 'Do not ask this question again')

            if reply[1]==True:
               LOGINFO('URL-register:  do not ask again:  always %s', str(reply[0]))
               self.writeSetting('DNAA_DefaultApp', True)
               self.writeSetting('AlwaysArmoryURI', reply[0])

            if reply[0]==True:
               action = 'DoIt'
            else:
               LOGINFO('User requested not to use Armory as URI handler')
               return

         # Finally, do it if we're supposed to!
         LOGINFO('URL-register action: %s', action)
         if action=='DoIt':

            LOGINFO('Registering Armory  for current user')
            baseDir = os.path.dirname(unicode(passstr[0:(rtlength*2)], encoding='utf16'))
            regKeys = []
            regKeys.append(['Software\\Classes\\bitcoin', '', 'URL:bitcoin Protocol'])
            regKeys.append(['Software\\Classes\\bitcoin', 'URL Protocol', ""])
            regKeys.append(['Software\\Classes\\bitcoin\\shell', '', None])
            regKeys.append(['Software\\Classes\\bitcoin\\shell\\open', '',  None])

            for key,name,val in regKeys:
               dkey = '%s\\%s' % (key,name)
               LOGINFO('\tWriting key: [HKEY_CURRENT_USER\\] ' + dkey)
               registryKey = CreateKey(HKEY_CURRENT_USER, key)
               SetValueEx(registryKey, name, 0, REG_SZ, val)
               CloseKey(registryKey)

            regKeysU = []
            regKeysU.append(['Software\\Classes\\bitcoin\\shell\\open\\command',  '', \
                           modulepathname])
            regKeysU.append(['Software\\Classes\\bitcoin\\DefaultIcon', '',  \
                          '"%s\\armory48x48.ico"' % baseDir])
            for key,name,val in regKeysU:
               dkey = '%s\\%s' % (key,name)
               LOGINFO('\tWriting key: [HKEY_CURRENT_USER\\] ' + dkey)
               registryKey = CreateKey(HKEY_CURRENT_USER, key)
               #hKey = ctypes.c_int(registryKey.handle)
               #ctypes.windll.Advapi32.RegSetValueEx(hKey, None, 0, REG_SZ, val, (len(val)+1))
               SetValueEx(registryKey, name, 0, REG_SZ, val)
               CloseKey(registryKey)


   #############################################################################
   def warnNewUSTXFormat(self):
      if not self.getSettingOrSetDefault('DNAA_Version092Warn', False):
         reply = MsgBoxWithDNAA(MSGBOX.Warning, tr("Version Warning"), tr("""
            Since Armory version 0.92 the formats for offline transaction
            operations has changed to accommodate multi-signature 
            transactions.  This format is <u>not</u> compatible with
            versions of Armory before 0.92.
            <br><br>
            To continue, the other system will need to be upgraded to
            to version 0.92 or later.  If you cannot upgrade the other 
            system, you will need to reinstall an older version of Armory
            on this system."""), dnaaMsg='Do not show this warning again')
         self.writeSetting('DNAA_Version092Warn', reply[1])


   #############################################################################
   def execOfflineTx(self):
      self.warnNewUSTXFormat()

      dlgSelect = DlgOfflineSelect(self, self)
      if dlgSelect.exec_():

         # If we got here, one of three buttons was clicked.
         if dlgSelect.do_create:
            DlgSendBitcoins(self.getSelectedWallet(), self, self, 
                                          onlyOfflineWallets=True).exec_()
         elif dlgSelect.do_broadc:
            DlgSignBroadcastOfflineTx(self,self).exec_()


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
            self.startWalletWizard()

         if dlg.requestImport:
            self.execImportWallet()



   #############################################################################
   def makeWalletCopy(self, parent, wlt, copyType='Same', suffix='', changePass=False):
      '''Create a digital backup of your wallet.'''
      if changePass:
         LOGERROR('Changing password is not implemented yet!')
         raise NotImplementedError

      # Set the file name.
      if copyType.lower()=='pkcc':
         fn = 'armory_%s.%s' % (wlt.uniqueIDB58, suffix)
      else:
         fn = 'armory_%s_%s.wallet' % (wlt.uniqueIDB58, suffix)

      if wlt.watchingOnly and copyType.lower() != 'pkcc':
         fn = 'armory_%s_%s.watchonly.wallet' % (wlt.uniqueIDB58, suffix)
      savePath = unicode(self.getFileSave(defaultFilename=fn))
      if not len(savePath)>0:
         return False

      # Create the file based on the type you want.
      if copyType.lower()=='same':
         wlt.writeFreshWalletFile(savePath)
      elif copyType.lower()=='decrypt':
         if wlt.useEncryption:
            dlg = DlgUnlockWallet(wlt, parent, self, 'Unlock Private Keys')
            if not dlg.exec_():
               return False
         # Wallet should now be unlocked
         wlt.makeUnencryptedWalletCopy(savePath)
      elif copyType.lower()=='encrypt':
         newPassphrase=None
         if not wlt.useEncryption:
            dlgCrypt = DlgChangePassphrase(parent, self, not wlt.useEncryption)
            if not dlgCrypt.exec_():
               QMessageBox.information(parent, tr('Aborted'), tr("""
                  No passphrase was selected for the encrypted backup.
                  No backup was created"""), QMessageBox.Ok)
            newPassphrase = SecureBinaryData(str(dlgCrypt.edtPasswd1.text()))

         wlt.makeEncryptedWalletCopy(savePath, newPassphrase)
      elif copyType.lower() == 'pkcc':
         wlt.writePKCCFile(savePath)
      else:
         LOGERROR('Invalid "copyType" supplied to makeWalletCopy: %s', copyType)
         return False

      QMessageBox.information(parent, tr('Backup Complete'), tr("""
         Your wallet was successfully backed up to the following
         location:<br><br>%s""") % savePath, QMessageBox.Ok)
      return True


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
   def setupAnnouncementFetcher(self):
      skipChk1 = self.getSettingOrSetDefault('SkipAnnounceCheck', False)
      skipChk2 = CLI_OPTIONS.skipAnnounceCheck
      skipChk3 = CLI_OPTIONS.offline and not CLI_OPTIONS.testAnnounceCode
      self.skipAnnounceCheck = skipChk1 or skipChk2 or skipChk3

      url1 = ANNOUNCE_URL
      url2 = ANNOUNCE_URL_BACKUP
      fetchPath = os.path.join(ARMORY_HOME_DIR, 'atisignedannounce')
      if self.announceFetcher is None:
         self.announceFetcher = AnnounceDataFetcher(url1, url2, fetchPath)
         self.announceFetcher.setDisabled(self.skipAnnounceCheck)
         self.announceFetcher.start()

         # Set last-updated vals to zero to force processing at startup
         for fid in ['changelog, downloads','notify','bootstrap']:
            self.lastAnnounceUpdate[fid] = 0

      # If we recently updated the settings to enable or disable checking...
      if not self.announceFetcher.isRunning() and not self.skipAnnounceCheck:
         self.announceFetcher.setDisabled(False)
         self.announceFetcher.setFetchInterval(DEFAULT_FETCH_INTERVAL)
         self.announceFetcher.start()
      elif self.announceFetcher.isRunning() and self.skipAnnounceCheck:
         self.announceFetcher.setDisabled(True)
         self.announceFetcher.shutdown()



   #############################################################################
   def processAnnounceData(self, forceCheck=False, forceWait=5):

      adf = self.announceFetcher



      # The ADF always fetches everything all the time.  If forced, do the
      # regular fetch first, then examine the individual files without forcing
      if forceCheck:
         adf.fetchRightNow(forceWait)

      # Check each of the individual files for recent modifications
      idFuncPairs = [
                      ['announce',  self.updateAnnounceTab],
                      ['changelog', self.processChangelog],
                      ['downloads', self.processDownloads],
                      ['notify',    self.processNotifications],
                      ['bootstrap', self.processBootstrap] ]

      # If modified recently
      for fid,func in idFuncPairs:
         if not fid in self.lastAnnounceUpdate or \
            adf.getFileModTime(fid) > self.lastAnnounceUpdate[fid]:
            self.lastAnnounceUpdate[fid] = RightNow()
            fileText = adf.getAnnounceFile(fid)
            func(fileText)




   #############################################################################
   def processChangelog(self, txt):
      try:
         clp = changelogParser()
         self.changelog = clp.parseChangelogText(txt)
      except:
         # Don't crash on an error, but do log what happened
         LOGEXCEPT('Failed to parse changelog data')



   #############################################################################
   def processDownloads(self, txt):
      try:
         dlp = downloadLinkParser()
         self.downloadLinks = dlp.parseDownloadList(txt)

         if self.downloadLinks is None:
            return

         thisVer = getVersionInt(BTCARMORY_VERSION)

         # Check ARMORY versions
         if not 'Armory' in self.downloadLinks:
            LOGWARN('No Armory links in the downloads list')
         else:
            maxVer = 0
            self.versionNotification = {}
            for verStr,vermap in self.downloadLinks['Armory'].iteritems():
               dlVer = getVersionInt(readVersionString(verStr))
               if dlVer > maxVer:
                  maxVer = dlVer
                  self.armoryVersions[1] = verStr
                  if thisVer >= maxVer:
                     continue

                  shortDescr = tr('Armory version %s is now available!') % verStr
                  notifyID = binary_to_hex(hash256(shortDescr)[:4])
                  self.versionNotification['UNIQUEID'] = notifyID
                  self.versionNotification['VERSION'] = '0'
                  self.versionNotification['STARTTIME'] = '0'
                  self.versionNotification['EXPIRES'] = '%d' % long(UINT64_MAX)
                  self.versionNotification['CANCELID'] = '[]'
                  self.versionNotification['MINVERSION'] = '*'
                  self.versionNotification['MAXVERSION'] = '<%s' % verStr
                  self.versionNotification['PRIORITY'] = '3072'
                  self.versionNotification['ALERTTYPE'] = 'Upgrade'
                  self.versionNotification['NOTIFYSEND'] = 'False'
                  self.versionNotification['NOTIFYRECV'] = 'False'
                  self.versionNotification['SHORTDESCR'] = shortDescr
                  self.versionNotification['LONGDESCR'] = \
                     self.getVersionNotifyLongDescr(verStr).replace('\n','<br>')
                     
            if 'ArmoryTesting' in self.downloadLinks:
               for verStr,vermap in self.downloadLinks['ArmoryTesting'].iteritems():
                  dlVer = getVersionInt(readVersionString(verStr))
                  if dlVer > maxVer:
                     maxVer = dlVer
                     self.armoryVersions[1] = verStr
                     if thisVer >= maxVer:
                        continue

                     shortDescr = tr('Armory Testing version %s is now available!') % verStr
                     notifyID = binary_to_hex(hash256(shortDescr)[:4])
                     self.versionNotification['UNIQUEID'] = notifyID
                     self.versionNotification['VERSION'] = '0'
                     self.versionNotification['STARTTIME'] = '0'
                     self.versionNotification['EXPIRES'] = '%d' % long(UINT64_MAX)
                     self.versionNotification['CANCELID'] = '[]'
                     self.versionNotification['MINVERSION'] = '*'
                     self.versionNotification['MAXVERSION'] = '<%s' % verStr
                     self.versionNotification['PRIORITY'] = '1024'
                     self.versionNotification['ALERTTYPE'] = 'upgrade-testing'
                     self.versionNotification['NOTIFYSEND'] = 'False'
                     self.versionNotification['NOTIFYRECV'] = 'False'
                     self.versionNotification['SHORTDESCR'] = shortDescr
                     self.versionNotification['LONGDESCR'] = \
                        self.getVersionNotifyLongDescr(verStr, True).replace('\n','<br>')


         # For Satoshi updates, we don't trigger any notifications like we
         # do for Armory above -- we will release a proper announcement if
         # necessary.  But we want to set a flag to
         if not 'Satoshi' in self.downloadLinks:
            LOGWARN('No Satoshi links in the downloads list')
         else:
            try:
               maxVer = 0
               for verStr,vermap in self.downloadLinks['Satoshi'].iteritems():
                  dlVer = getVersionInt(readVersionString(verStr))
                  if dlVer > maxVer:
                     maxVer = dlVer
                     self.satoshiVersions[1] = verStr

               if not self.NetworkingFactory:
                  return

               # This is to detect the running versions of Bitcoin-Qt/bitcoind
               thisVerStr = self.NetworkingFactory.proto.peerInfo['subver']
               thisVerStr = thisVerStr.strip('/').split(':')[-1]

               if sum([0 if c in '0123456789.' else 1 for c in thisVerStr]) > 0:
                  return

               self.satoshiVersions[0] = thisVerStr

            except:
               pass




      except:
         # Don't crash on an error, but do log what happened
         LOGEXCEPT('Failed to parse download link data')


   #############################################################################
   def getVersionNotifyLongDescr(self, verStr, testing=False):
      shortOS = None
      if OS_WINDOWS:
         shortOS = 'windows'
      elif OS_LINUX:
         shortOS = 'ubuntu'
      elif OS_MACOSX:
         shortOS = 'mac'

      webURL = 'https://bitcoinarmory.com/download/'
      if shortOS is not None:
         webURL += '#' + shortOS

      if testing:
         return tr("""
            A new testing version of Armory is out. You can upgrade to version
            %s through our secure downloader inside Armory (link at the bottom
            of this notification window).
            """) % (verStr)
         
      return tr("""
         Your version of Armory is now outdated.  Please upgrade to version
         %s through our secure downloader inside Armory (link at the bottom
         of this notification window).  Alternatively, you can get the new
         version from our website downloads page at:
         <br><br>
         <a href="%s">%s</a> """) % (verStr, webURL, webURL)



   #############################################################################
   def processBootstrap(self, binFile):
      # Nothing to process, actually.  We'll grab the bootstrap from its
      # current location, if needed
      pass



   #############################################################################
   def notificationIsRelevant(self, notifyID, notifyMap):
      currTime = RightNow()
      thisVerInt = getVersionInt(BTCARMORY_VERSION)

      # Ignore transactions below the requested priority
      minPriority = self.getSettingOrSetDefault('NotifyMinPriority', 2048)
      if int(notifyMap['PRIORITY']) < minPriority:
         return False

      # Ignore version upgrade notifications if disabled in the settings
      if 'upgrade' in notifyMap['ALERTTYPE'].lower() and \
         self.getSettingOrSetDefault('DisableUpgradeNotify', False):
         return False

      if notifyID in self.notifyIgnoreShort:
         return False

      if notifyMap['STARTTIME'].isdigit():
         if currTime < long(notifyMap['STARTTIME']):
            return False

      if notifyMap['EXPIRES'].isdigit():
         if currTime > long(notifyMap['EXPIRES']):
            return False


      try:
         minVerStr  = notifyMap['MINVERSION']
         minExclude = minVerStr.startswith('>')
         minVerStr  = minVerStr[1:] if minExclude else minVerStr
         minVerInt  = getVersionInt(readVersionString(minVerStr))
         minVerInt += 1 if minExclude else 0
         if thisVerInt < minVerInt:
            return False
      except:
         pass


      try:
         maxVerStr  = notifyMap['MAXVERSION']
         maxExclude = maxVerStr.startswith('<')
         maxVerStr  = maxVerStr[1:] if maxExclude else maxVerStr
         maxVerInt  = getVersionInt(readVersionString(maxVerStr))
         maxVerInt -= 1 if maxExclude else 0
         if thisVerInt > maxVerInt:
            return False
      except:
         pass

      return True


   #############################################################################
   def processNotifications(self, txt):

      # Keep in mind this will always be run on startup with a blank slate, as
      # well as every 30 min while Armory is running.  All notifications are
      # "new" on startup (though we will allow the user to do-not-show-again
      # and store the notification ID in the settings file).
      try:
         np = notificationParser()
         currNotificationList = np.parseNotificationText(txt)
      except:
         # Don't crash on an error, but do log what happened
         LOGEXCEPT('Failed to parse notifications')

      if currNotificationList is None:
         currNotificationList = {}

      # If we have a new-version notification, it's not ignroed, and such
      # notifications are not disabled, add it to the list
      vnotify = self.versionNotification
      if vnotify and 'UNIQUEID' in vnotify:
         currNotificationList[vnotify['UNIQUEID']] = deepcopy(vnotify)

      # Create a copy of almost all the notifications we have.
      # All notifications >= 2048, unless they've explictly allowed testing
      # notifications.   This will be shown on the "Announcements" tab.
      self.almostFullNotificationList = {}
      currMin = self.getSettingOrSetDefault('NotifyMinPriority', \
                                                     DEFAULT_MIN_PRIORITY)
      minmin = min(currMin, DEFAULT_MIN_PRIORITY)
      for nid,valmap in currNotificationList.iteritems():
         if int(valmap['PRIORITY']) >= minmin:
            self.almostFullNotificationList[nid] = deepcopy(valmap)


      tabPriority = 0
      self.maxPriorityID = None

      # Check for new notifications
      addedNotifyIDs = set()
      irrelevantIDs = set()
      for nid,valmap in currNotificationList.iteritems():
         if not self.notificationIsRelevant(nid, valmap):
            # Can't remove while iterating over the map
            irrelevantIDs.add(nid)
            self.notifyIgnoreShort.add(nid)
            continue

         if valmap['PRIORITY'].isdigit():
            if int(valmap['PRIORITY']) > tabPriority:
               tabPriority = int(valmap['PRIORITY'])
               self.maxPriorityID = nid

         if not nid in self.almostFullNotificationList:
            addedNotifyIDs.append(nid)

      # Now remove them from the set that we are working with
      for nid in irrelevantIDs:
         del currNotificationList[nid]

      # Check for notifications we had before but no long have
      removedNotifyIDs = []
      for nid,valmap in self.almostFullNotificationList.iteritems():
         if not nid in currNotificationList:
            removedNotifyIDs.append(nid)


      #for nid in removedNotifyIDs:
         #self.notifyIgnoreShort.discard(nid)
         #self.notifyIgnoreLong.discard(nid)



      # Change the "Announcements" tab color if something important is there
      tabWidgetBar = self.mainDisplayTabs.tabBar()
      tabColor = Colors.Foreground
      if tabPriority >= 5120:
         tabColor = Colors.TextRed
      elif tabPriority >= 4096:
         tabColor = Colors.TextRed
      elif tabPriority >= 3072:
         tabColor = Colors.TextBlue
      elif tabPriority >= 2048:
         tabColor = Colors.TextBlue

      tabWidgetBar.setTabTextColor(self.MAINTABS.Announce, tabColor)
      self.updateAnnounceTab()

      # We only do popups for notifications >=4096, AND upgrade notify
      if tabPriority >= 3072:
         DlgNotificationWithDNAA(self, self, self.maxPriorityID, \
                           currNotificationList[self.maxPriorityID]).show()
      elif vnotify:
         if not vnotify['UNIQUEID'] in self.notifyIgnoreShort:
            DlgNotificationWithDNAA(self,self,vnotify['UNIQUEID'],vnotify).show()







   #############################################################################
   @TimeThisFunction
   def setupNetworking(self):
      LOGINFO('Setting up networking...')
      self.internetAvail = False

      # Prevent Armory from being opened twice
      from twisted.internet import reactor
      import twisted
      def uriClick_partial(a):
         self.uriLinkClicked(a)

      if CLI_OPTIONS.interport > 1:
         try:
            self.InstanceListener = ArmoryListenerFactory(self.bringArmoryToFront, \
                                                          uriClick_partial )
            reactor.listenTCP(CLI_OPTIONS.interport, self.InstanceListener)
         except twisted.internet.error.CannotListenError:
            LOGWARN('Socket already occupied!  This must be a duplicate Armory')
            QMessageBox.warning(self, tr('Already Open'), tr("""
               Armory is already running!  You can only have one Armory open
               at a time.  Exiting..."""), QMessageBox.Ok)
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
            except:
               LOGEXCEPT('Error checking for internet connection')
               LOGERROR('Run --skip-online-check if you think this is an error')
               self.internetAvail = False
         except:
            LOGEXCEPT('Error checking for internet connection')
            LOGERROR('Run --skip-online-check if you think this is an error')
            self.internetAvail = False


      LOGINFO('Internet connection is Available: %s', self.internetAvail)
      LOGINFO('Bitcoin-Qt/bitcoind is Available: %s', satoshiIsAvailable())
      LOGINFO('The first blk*.dat was Available: %s', str(self.checkHaveBlockfiles()))
      LOGINFO('Online mode currently possible:   %s', self.onlineModeIsPossible())





   #############################################################################
   def manageBitcoindAskTorrent(self):

      if not satoshiIsAvailable():
         reply = MsgBoxCustom(MSGBOX.Question, tr('BitTorrent Option'), tr("""
            You are currently configured to run the core Bitcoin software
            yourself (Bitcoin-Qt or bitcoind).  <u>Normally</u>, you should
            start the Bitcoin software first and wait for it to synchronize
            with the network before starting Armory.
            <br><br>
            <b>However</b>, Armory can shortcut most of this initial
            synchronization
            for you using BitTorrent.  If your firewall allows it,
            using BitTorrent can be an order of magnitude faster (2x to 20x)
            than letting the Bitcoin software download it via P2P.
            <br><br>
            <u>To synchronize using BitTorrent (recommended):</u>
            Click "Use BitTorrent" below, and <u>do not</u> start the Bitcoin
            software until after it is complete.
            <br><br>
            <u>To synchronize using Bitcoin P2P (fallback):</u>
            Click "Cancel" below, then close Armory and start Bitcoin-Qt
            (or bitcoind).  Do not start Armory until you see a green checkmark
            in the bottom-right corner of the Bitcoin-Qt window."""), \
            wCancel=True, yesStr='Use BitTorrent')

         if not reply:
            QMessageBox.warning(self, tr('Synchronize'), tr("""
               When you are ready to start synchronization, close Armory and
               start Bitcoin-Qt or bitcoind.  Restart Armory only when
               synchronization is complete.  If using Bitcoin-Qt, you will see
               a green checkmark in the bottom-right corner"""), QMessageBox.Ok)
            return False

      else:
         reply = MsgBoxCustom(MSGBOX.Question, tr('BitTorrent Option'), tr("""
            You are currently running the core Bitcoin software, but it
            is not fully synchronized with the network, yet.  <u>Normally</u>,
            you should close Armory until Bitcoin-Qt (or bitcoind) is
            finished
            <br><br>
            <b><u>However</u></b>, Armory can speed up this initial
            synchronization for you using BitTorrent.  If your firewall
            allows it, using BitTorrent can be an order of magnitude
            faster (2x to 20x)
            than letting the Bitcoin software download it via P2P.
            <br><br>
            <u>To synchronize using BitTorrent (recommended):</u>
            Close the running Bitcoin software <b>right now</b>.  When it is
            closed, click "Use BitTorrent" below.  Restart the Bitcoin software
            when Armory indicates it is complete.
            <br><br>
            <u>To synchronize using Bitcoin P2P (fallback):</u>
            Click "Cancel" below, and then close Armory until the Bitcoin
            software is finished synchronizing.  If using Bitcoin-Qt, you
            will see a green checkmark in the bottom-right corner of the
            main window."""), QMessageBox.Ok)

         if reply:
            if satoshiIsAvailable():
               QMessageBox.warning(self, tr('Still Running'), tr("""
                  The Bitcoin software still appears to be open!
                  Close it <b>right now</b>
                  before clicking "Ok."  The BitTorrent engine will start
                  as soon as you do."""), QMessageBox.Ok)
         else:
            QMessageBox.warning(self, tr('Synchronize'), tr("""
               You chose to finish synchronizing with the network using
               the Bitcoin software which is already running.  Please close
               Armory until it is finished.  If you are running Bitcoin-Qt,
               you will see a green checkmark in the bottom-right corner,
               when it is time to open Armory again."""), QMessageBox.Ok)
            return False

         return True


   ############################################################################
   def findTorrentFileForSDM(self, forceWaitTime=0):
      """
      Hopefully the announcement fetcher has already gotten one for us,
      or at least we have a default.
      """

      # Only do an explicit announce check if we have no bootstrap at all
      # (don't need to spend time doing an explicit check if we have one)
      if self.announceFetcher.getFileModTime('bootstrap') == 0:
         if forceWaitTime>0:
            self.explicitCheckAnnouncements(forceWaitTime)

      # If it's still not there, look for a default file
      if self.announceFetcher.getFileModTime('bootstrap') == 0:
         LOGERROR('Could not get announce bootstrap; using default')
         srcTorrent = os.path.join(GetExecDir(), 'default_bootstrap.torrent')
      else:
         srcTorrent = self.announceFetcher.getAnnounceFilePath('bootstrap')

      # Maybe we still don't have a torrent for some reason
      if not srcTorrent or not os.path.exists(srcTorrent):
         return ''

      torrentPath = os.path.join(ARMORY_HOME_DIR, 'bootstrap.dat.torrent')
      LOGINFO('Using torrent file: ' + torrentPath)
      shutil.copy(srcTorrent, torrentPath)

      return torrentPath





   ############################################################################
   def startBitcoindIfNecessary(self):
      LOGINFO('startBitcoindIfNecessary')
      if not (self.forceOnline or self.internetAvail) or CLI_OPTIONS.offline:
         LOGWARN('Not online, will not start bitcoind')
         return False

      if not self.doAutoBitcoind:
         LOGWARN('Tried to start bitcoind, but ManageSatoshi==False')
         return False

      if satoshiIsAvailable():
         LOGWARN('Tried to start bitcoind, but satoshi already running')
         return False

      self.setSatoshiPaths()
      TheSDM.setDisabled(False)

      torrentIsDisabled = self.getSettingOrSetDefault('DisableTorrent', False)

      # Give the SDM the torrent file...it will use it if it makes sense
      if not torrentIsDisabled and TheSDM.shouldTryBootstrapTorrent():
         torrentFile = self.findTorrentFileForSDM(2)
         if not torrentFile or not os.path.exists(torrentFile):
            LOGERROR('Could not find torrent file')
         else:
            TheSDM.tryToSetupTorrentDL(torrentFile)


      try:
         # "satexe" is actually just the install directory, not the direct
         # path the executable.  That dir tree will be searched for bitcoind
         TheSDM.setupSDM(extraExeSearch=self.satoshiExeSearchPath)
         TheSDM.startBitcoind()
         LOGDEBUG('Bitcoind started without error')
         return True
      except:
         LOGEXCEPT('Failed to setup SDM')
         self.switchNetworkMode(NETWORKMODE.Offline)


   ############################################################################
   def setSatoshiPaths(self):
      LOGINFO('setSatoshiPaths')

      # We skip the getSettingOrSetDefault call, because we don't want to set
      # it if it doesn't exist
      if self.settings.hasSetting('SatoshiExe'):
         if not os.path.exists(self.settings.get('SatoshiExe')):
            LOGERROR('Bitcoin installation setting is a non-existent directory')
         self.satoshiExeSearchPath = [self.settings.get('SatoshiExe')]
      else:
         self.satoshiExeSearchPath = []


      self.satoshiHomePath = BTC_HOME_DIR
      if self.settings.hasSetting('SatoshiDatadir') and \
         CLI_OPTIONS.satoshiHome=='DEFAULT':
         # Setting override BTC_HOME_DIR only if it wasn't explicitly
         # set as the command line.
         self.satoshiHomePath = self.settings.get('SatoshiDatadir')
         LOGINFO('Setting satoshi datadir = %s' % self.satoshiHomePath)

      TheBDM.setSatoshiDir(self.satoshiHomePath)
      TheSDM.setSatoshiDir(self.satoshiHomePath)
      TheTDM.setSatoshiDir(self.satoshiHomePath)


   ############################################################################
   def loadBlockchainIfNecessary(self):
      LOGINFO('loadBlockchainIfNecessary')
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
         #self.resetBdmBeforeScan()
         TheBDM.setOnlineMode(True, wait=False)

      else:
         self.switchNetworkMode(NETWORKMODE.Offline)
         TheBDM.setOnlineMode(False, wait=False)


   #############################################################################
   def checkHaveBlockfiles(self):
      return os.path.exists(os.path.join(TheBDM.btcdir, 'blocks'))

   #############################################################################
   def onlineModeIsPossible(self):
      return ((self.internetAvail or self.forceOnline) and \
               satoshiIsAvailable() and \
               self.checkHaveBlockfiles())


   #############################################################################
   def switchNetworkMode(self, newMode):
      LOGINFO('Setting netmode: %s', newMode)
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
            if not self.getSettingOrSetDefault('NotifyDiscon', not OS_MACOSX):
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
            if not self.getSettingOrSetDefault('NotifyReconn', not OS_MACOSX):
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
                                          TheBDM,
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

      TheBDM.addNewZeroConfTx(pytxObj.serialize(), long(RightNow()), True, wait=True)
      self.newZeroConfSinceLastUpdate.append(pytxObj.serialize())
      #LOGDEBUG('Added zero-conf tx to pool: ' + binary_to_hex(pytxObj.thisHash))

      # All extra tx functions take one arg:  the PyTx object of the new ZC tx
      for txFunc in self.extraNewTxFunctions:
         txFunc(pytxObj)   



   #############################################################################
   def parseUriLink(self, uriStr, clickOrEnter='click'):
      if len(uriStr) < 1:
         QMessageBox.critical(self, 'No URL String', \
               'You have not entered a URL String yet. '
               'Please go back and enter a URL String.', \
               QMessageBox.Ok)
         return {}
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
      if theAddrByte!=-1 and not theAddrByte in [ADDRBYTE, P2SHBYTE]:
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
      LOGINFO('uriLinkClicked')
      if TheBDM.getBDMState()=='Offline':
         QMessageBox.warning(self, 'Offline', \
            'You just clicked on a "bitcoin:" link, but Armory is offline '
            'and cannot send transactions.  Please click the link '
            'again when Armory is online.', \
            QMessageBox.Ok)
         return
      elif not TheBDM.getBDMState()=='BlockchainReady':
         # BDM isnt ready yet, saved URI strings in the delayed URIDict to
         # call later through finishLoadBlockChainGUI
         qLen = self.delayedURIData['qLen']

         self.delayedURIData[qLen] = uriStr
         qLen = qLen +1
         self.delayedURIData['qLen'] = qLen
         return

      uriDict = self.parseUriLink(uriStr, 'click')

      if len(uriDict)>0:
         self.bringArmoryToFront()
         return self.uriSendBitcoins(uriDict)


   #############################################################################
   @TimeThisFunction
   def loadWalletsAndSettings(self):
      LOGINFO('loadWalletsAndSettings')

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


      # The user may have asked to never be notified of a particular
      # notification again.  We have a short-term list (wiped on every
      # load), and a long-term list (saved in settings).  We simply
      # initialize the short-term list with the long-term list, and add
      # short-term ignore requests to it
      notifyStr = self.getSettingOrSetDefault('NotifyIgnore', '')
      nsz = len(notifyStr)
      self.notifyIgnoreLong  = set(notifyStr[8*i:8*(i+1)] for i in range(nsz/8))
      self.notifyIgnoreShort = set(notifyStr[8*i:8*(i+1)] for i in range(nsz/8))


      # Load wallets found in the .armory directory
      self.walletMap = {}
      self.walletIndices = {}
      self.walletIDSet = set()

      # I need some linear lists for accessing by index
      self.walletIDList = []
      self.walletVisibleList = []
      self.combinedLedger = []
      self.ledgerSize = 0
      self.ledgerTable = []

      self.currBlockNum = 0

      LOGINFO('Loading wallets...')
      wltPaths = readWalletFiles()

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
                  LOGWARN('     Wallet 1 (skipped): %s', fpath)
                  LOGWARN('     Wallet 2 (loaded):  %s', self.walletMap[wltID].walletPath)
            else:
               # Update the maps/dictionaries
               self.walletMap[wltID] = wltLoad
               self.walletIndices[wltID] = len(self.walletMap)-1

               # Maintain some linear lists of wallet info
               self.walletIDSet.add(wltID)
               self.walletIDList.append(wltID)
               wtype = determineWalletType(wltLoad, self)[0]
               notWatch = (not wtype == WLTTYPES.WatchOnly)
               defaultVisible = self.getWltSetting(wltID, 'LedgerShow', notWatch)
               self.walletVisibleList.append(defaultVisible)
               wltLoad.mainWnd = self
         except:
            LOGEXCEPT( '***WARNING: Wallet could not be loaded: %s (skipping)', 
                                                                           fpath)
            raise



      LOGINFO('Number of wallets read in: %d', len(self.walletMap))
      for wltID, wlt in self.walletMap.iteritems():
         dispStr  = ('   Wallet (%s):' % wlt.uniqueIDB58).ljust(25)
         dispStr +=  '"'+wlt.labelName.ljust(32)+'"   '
         dispStr +=  '(Encrypted)' if wlt.useEncryption else '(No Encryption)'
         LOGINFO(dispStr)
         # Register all wallets with TheBDM
         TheBDM.registerWallet( wlt.cppWallet )
         TheBDM.bdm.registerWallet(wlt.cppWallet)


      # Create one wallet per lockbox to make sure we can query individual
      # lockbox histories easily.
      if self.usermode==USERMODE.Expert:
         LOGINFO('Loading Multisig Lockboxes')
         self.loadLockboxesFromFile(MULTISIG_FILE)


      # Get the last directory
      savedDir = self.settings.get('LastDirectory')
      if len(savedDir)==0 or not os.path.exists(savedDir):
         savedDir = ARMORY_HOME_DIR
      self.lastDirectory = savedDir
      self.writeSetting('LastDirectory', savedDir)


   #############################################################################
   @RemoveRepeatingExtensions
   def getFileSave(self, title='Save Wallet File', \
                         ffilter=['Wallet files (*.wallet)'], \
                         defaultFilename=None):
      LOGDEBUG('getFileSave')
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
   def getFileLoad(self, title='Load Wallet File', \
                         ffilter=['Wallet files (*.wallet)'], \
                         defaultDir=None):

      LOGDEBUG('getFileLoad')

      if defaultDir is None:
         defaultDir = self.settings.get('LastDirectory')
         if len(defaultDir)==0 or not os.path.exists(defaultDir):
            defaultDir = ARMORY_HOME_DIR


      types = list(ffilter)
      types.append(tr('All files (*)'))
      typesStr = ';; '.join(types)
      # Found a bug with Swig+Threading+PyQt+OSX -- save/load file dialogs freeze
      # User picobit discovered this is avoided if you use the Qt dialogs, instead
      # of the native OS dialogs.  Use native for all except OSX...
      if not OS_MACOSX:
         fullPath = unicode(QFileDialog.getOpenFileName(self, title, defaultDir, typesStr))
      else:
         fullPath = unicode(QFileDialog.getOpenFileName(self, title, defaultDir, typesStr, \
                                             options=QFileDialog.DontUseNativeDialog))

      self.writeSetting('LastDirectory', os.path.split(fullPath)[0])
      return fullPath

   ##############################################################################
   def getWltSetting(self, wltID, propName, defaultValue=''):
      # Sometimes we need to settings specific to individual wallets -- we will
      # prefix the settings name with the wltID.
      wltPropName = 'Wallet_%s_%s' % (wltID, propName)
      if self.settings.hasSetting(wltPropName):
         return self.settings.get(wltPropName)
      else:
         if not defaultValue=='':
            self.setWltSetting(wltID, propName, defaultValue)
         return defaultValue

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
   def loadLockboxesFromFile(self, fn):
      self.allLockboxes = []
      self.cppLockboxWltMap = {}
      if not os.path.exists(fn):
         return

      lbList = readLockboxesFile(fn)
      for lb in lbList:
         self.updateOrAddLockbox(lb)


   #############################################################################
   def updateOrAddLockbox(self, lbObj, isFresh=False):
      try:
         lbID = lbObj.uniqueIDB58
         index = self.lockboxIDMap.get(lbID)
         if index is None:
            # Add new lockbox to list
            self.allLockboxes.append(lbObj)
            self.lockboxIDMap[lbID] = len(self.allLockboxes)-1
   
            # Create new wallet to hold the lockbox, register it with BDM
            self.cppLockboxWltMap[lbID] = BtcWallet()
            scraddrReg = script_to_scrAddr(lbObj.binScript)
            scraddrP2SH = script_to_scrAddr(script_to_p2sh_script(lbObj.binScript))
            TheBDM.registerWallet(self.cppLockboxWltMap[lbID], isFresh)
            TheBDM.bdm.registerWallet(self.cppLockboxWltMap[lbID], isFresh)
            if not isFresh:
               self.cppLockboxWltMap[lbID].addScrAddress_1_(scraddrReg)
               self.cppLockboxWltMap[lbID].addScrAddress_1_(scraddrP2SH)
            else:
               self.cppLockboxWltMap[lbID].addNewScrAddress(scraddrReg)
               self.cppLockboxWltMap[lbID].addNewScrAddress(scraddrP2SH)

            # Save the scrAddr histories again to make sure no rescan nexttime
            if TheBDM.getBDMState()=='BlockchainReady':
               TheBDM.saveScrAddrHistories()
         else:
            # Replace the original
            self.allLockboxes[index] = lbObj

         writeLockboxesFile(self.allLockboxes, MULTISIG_FILE)
      except:
         LOGEXCEPT('Failed to add/update lockbox')
        
   
   #############################################################################
   def removeLockbox(self, lbObj):
      lbID = lbObj.uniqueIDB58
      index = self.lockboxIDMap.get(lbID)
      if index is None:
         LOGERROR('Tried to remove lockbox that DNE: %s', lbID)
      else:
         del self.allLockboxes[index]
         self.reconstructLockboxMaps()
         writeLockboxesFile(self.allLockboxes, MULTISIG_FILE)


   #############################################################################
   def reconstructLockboxMaps(self):
      self.lockboxIDMap.clear()
      for i,box in enumerate(self.allLockboxes):
         self.lockboxIDMap[box.uniqueIDB58] = i

   #############################################################################
   def getLockboxByID(self, boxID):
      index = self.lockboxIDMap.get(boxID)
      return None if index is None else self.allLockboxes[index]
   
   ################################################################################
   # Get  the lock box ID if the p2shAddrString is found in one of the lockboxes
   # otherwise it returns None
   def getLockboxByP2SHAddrStr(self, p2shAddrStr):
      for lboxId in self.lockboxIDMap.keys():
         lbox = self.allLockboxes[self.lockboxIDMap[lboxId]]
         if p2shAddrStr == binScript_to_p2shAddrStr(lbox.binScript):
            return lbox
      return None


   #############################################################################
   def browseLockboxes(self):
      DlgLockboxManager(self,self).exec_()



   #############################################################################
   def getContribStr(self, binScript, contribID='', contribLabel=''):
      """ 
      This is used to display info for the lockbox interface.  It might also be
      useful as a general script_to_user_string method, where you have a 
      binScript and you want to tell the user something about it.  However,
      it is verbose, so it won't fit in a send-confirm dialog, necessarily.

      We should extract as much information as possible without contrib*.  This
      at least guarantees that we see the correct data for our own wallets
      and lockboxes, even if the data for other parties is incorrect.
      """

      displayInfo = self.getDisplayStringForScript(binScript, 60, 2)
      if displayInfo['WltID'] is not None:
         return displayInfo['String'], ('WLT:%s' % displayInfo['WltID'])
      elif displayInfo['LboxID'] is not None:
         return displayInfo['String'], ('LB:%s' % displayInfo['LboxID'])

      scriptType = getTxOutScriptType(binScript) 
      scrAddr = script_to_scrAddr(binScript)

   
      # At this point, we can use the contrib ID (and know we can't sign it)
      if contribID or contribLabel:
         if contribID:
            if contribLabel:
               outStr = 'Contributor "%s" (%s)' % (contribLabel, contribID)
            else:
               outStr = 'Contributor %s' % contribID
         else:
            if contribLabel:
               outStr = 'Contributor "%s"' % contribLabel
            else:
               outStr = 'Unknown Contributor'
               LOGERROR('How did we get to this impossible else-statement?')

         return outStr, ('CID:%s' % contribID)

      # If no contrib ID, then salvage anything
      astr = displayInfo['AddrStr']
      cid = None
      if scriptType == CPP_TXOUT_MULTISIG:
         M,N,a160s,pubs = getMultisigScriptInfo(binScript)
         dispStr = 'Unrecognized Multisig %d-of-%d: P2SH=%s' % (M,N,astr)
         cid     = 'MS:%s' % astr
      elif scriptType == CPP_TXOUT_P2SH:
         dispStr = 'Unrecognized P2SH: %s' % astr
         cid     = 'P2SH:%s' % astr
      elif scriptType in CPP_TXOUT_HAS_ADDRSTR:
         dispStr = 'Address: %s' % astr
         cid     = 'ADDR:%s' % astr
      else:
         dispStr = 'Non-standard: P2SH=%s' % astr
         cid     = 'NS:%s' % astr

      return dispStr, cid



   #############################################################################
   def getWalletForAddr160(self, addr160):
      for wltID, wlt in self.walletMap.iteritems():
         if wlt.hasAddr(addr160):
            return wltID
      return ''

   #############################################################################
   def getWalletForScrAddr(self, scrAddr):
      for wltID, wlt in self.walletMap.iteritems():
         if wlt.hasScrAddr(scrAddr):
            return wltID
      return ''

   #############################################################################
   def getSettingOrSetDefault(self, settingName, defaultVal):
      s = self.settings.getSettingOrSetDefault(settingName, defaultVal)
      return s

   #############################################################################
   def writeSetting(self, settingName, val):
      self.settings.set(settingName, val)

   #############################################################################
   def startRescanBlockchain(self, forceFullScan=False):
      if TheBDM.getBDMState() in ('Offline','Uninitialized'):
         LOGWARN('Rescan requested but Armory is in offline mode')
         return

      if TheBDM.getBDMState()=='Scanning':
         LOGINFO('Queueing rescan after current scan completes.')
      else:
         LOGINFO('Starting blockchain rescan...')


      # Start it in the background
      TheBDM.rescanBlockchain('AsNeeded', wait=False)
      self.needUpdateAfterScan = True
      self.setDashboardDetails()

   #############################################################################
   def forceRescanDB(self):
      self.needUpdateAfterScan = True
      self.lblDashModeBuild.setText( 'Build Databases', \
                                        size=4, bold=True, color='DisableFG')
      self.lblDashModeScan.setText( 'Scanning Transaction History', \
                                        size=4, bold=True, color='Foreground')
      TheBDM.rescanBlockchain('ForceRescan', wait=False)
      self.setDashboardDetails()

   #############################################################################
   def forceRebuildAndRescan(self):
      self.needUpdateAfterScan = True
      self.lblDashModeBuild.setText( 'Preparing Databases', \
                                        size=4, bold=True, color='Foreground')
      self.lblDashModeScan.setText( 'Scan Transaction History', \
                                        size=4, bold=True, color='DisableFG')
      #self.resetBdmBeforeScan()  # this resets BDM and then re-registeres wlts
      TheBDM.rescanBlockchain('ForceRebuild', wait=False)
      self.setDashboardDetails()





   #############################################################################
   @TimeThisFunction
   def initialWalletSync(self):
      for wltID in self.walletMap.iterkeys():
         LOGINFO('Syncing wallet: %s', wltID)
         self.walletMap[wltID].setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
         # Used to do "sync-lite" when we had to rescan for new addresses,
         self.walletMap[wltID].syncWithBlockchainLite(0)
         #self.walletMap[wltID].syncWithBlockchain(0)
         self.walletMap[wltID].detectHighestUsedIndex(True) # expand wlt if necessary
         self.walletMap[wltID].fillAddressPool()

      for lbID,cppWallet in self.cppLockboxWltMap.iteritems():
         TheBDM.scanRegisteredTxForWallet(cppWallet, wait=True)


   @TimeThisFunction
   # NB: armoryd has a similar function (Armory_Daemon::start()), and both share
   # common functionality in ArmoryUtils (finishLoadBlockchainCommon). If you
   # mod this function, please be mindful of what goes where, and make sure
   # any critical functionality makes it into armoryd.
   def finishLoadBlockchainGUI(self):
      # Let's populate the wallet info after finishing loading the blockchain.
      if TheBDM.isInitialized():
         self.setDashboardDetails()
         (self.currBlockNum, self.memPoolInit) = \
                                    TheBDM.finishLoadBlockchainCommon(self.walletMap, \
                                                        self.cppLockboxWltMap, \
                                                        self.memPoolInit)
         self.statusBar().showMessage('Blockchain loaded. Wallets synced!', 10000)

         # We still need to put together various bits of info.
         self.createCombinedLedger()
         self.ledgerSize = len(self.combinedLedger)
         if self.netMode==NETWORKMODE.Full:
            LOGINFO('Current block number: %d', self.currBlockNum)
            self.lblArmoryStatus.setText(\
               '<font color=%s>Connected (%s blocks)</font> ' %
               (htmlColor('TextGreen'), self.currBlockNum))

         self.blkReceived = TheBDM.getTopBlockHeader().getTimestamp()
         self.writeSetting('LastBlkRecv',     self.currBlockNum)
         self.writeSetting('LastBlkRecvTime', self.blkReceived)

         currSyncSuccess = self.getSettingOrSetDefault("SyncSuccessCount", 0)
         self.writeSetting('SyncSuccessCount', min(currSyncSuccess+1, 10))

         # If there are missing blocks, continue, but throw up a huge warning.
         vectMissingBlks = TheBDM.missingBlockHashes()
         LOGINFO('Blockfile corruption check: Missing blocks: %d', \
                 len(vectMissingBlks))
         if len(vectMissingBlks) > 0:
            LOGINFO('Missing blocks: %d', len(vectMissingBlks))
            QMessageBox.critical(self, tr('Blockdata Error'), tr("""
               Armory has detected an error in the blockchain database
               maintained by the third-party Bitcoin software (Bitcoin-Qt
               or bitcoind).  This error is not fatal, but may lead to
               incorrect balances, inability to send coins, or application
               instability.
               <br><br>
               It is unlikely that the error affects your wallets,
               but it <i>is</i> possible.  If you experience crashing,
               or see incorrect balances on any wallets, it is strongly
               recommended you re-download the blockchain using:
               "<i>Help</i>"\xe2\x86\x92"<i>Factory Reset</i>"."""), \
                QMessageBox.Ok)

         # If necessary, throw up a window stating the the blockchain's loaded.
         if self.getSettingOrSetDefault('NotifyBlkFinish',True):
            reply,remember = MsgBoxWithDNAA(MSGBOX.Info, \
               'Blockchain Loaded!', 'Blockchain loading is complete.  '
               'Your balances and transaction history are now available '
               'under the "Transactions" tab.  You can also send and '
               'receive bitcoins.', \
               dnaaMsg='Do not show me this notification again ', yesStr='OK')

            if remember==True:
               self.writeSetting('NotifyBlkFinish',False)

         self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Ledger)

         # Execute any extra functions we may have.
         for fn in self.extraGoOnlineFunctions:
            fn(self.currBlockNum)

         self.netMode = NETWORKMODE.Full
         self.settings.set('FailedLoadCount', 0)
      else:
         self.statusBar().showMessage('! Blockchain loading failed !', 10000)


      # This will force the table to refresh with new data
      self.setDashboardDetails()
      self.updateAnnounceTab()  # make sure satoshi version info is up to date
      self.removeBootstrapDat()  # if we got here, we're *really* done with it
      self.walletModel.reset()

      qLen = self.delayedURIData['qLen']
      if qLen > 0:
         #delayed URI parses, feed them back to the uri parser now
         for i in range(0, qLen):
            uriStr = self.delayedURIData[qLen-i-1]
            self.delayedURIData['qLen'] = qLen -i -1
            self.uriLinkClicked(uriStr)


   #############################################################################
   def removeBootstrapDat(self):
      bfile = os.path.join(BTC_HOME_DIR, 'bootstrap.dat.old')
      if os.path.exists(bfile):
         os.remove(bfile)

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
   @TimeThisFunction
   def createCombinedLedger(self, wltIDList=None, withZeroConf=True):
      """
      Create a ledger to display on the main screen, that consists of ledger
      entries of any SUBSET of available wallets.
      """
      start = RightNow()
      if wltIDList==None:
         currIdx  = max(self.comboWltSelect.currentIndex(), 0)
         wltIDList = []
         for i,vis in enumerate(self.walletVisibleList):
            if vis:
               wltIDList.append(self.walletIDList[i])
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


      def keyFuncNumConf(x):
         numConf = x[1].getBlockNum() - currBlk  # returns neg for reverse sort
         txTime  = x[1].getTxTime() 
         txhash  = x[1].getTxHash()
         value   = x[1].getValue()
         return (numConf, txTime, txhash, value)

      def keyFuncTxTime(x):
         numConf = x[1].getBlockNum() - currBlk  # returns neg for reverse sort
         txTime  = x[1].getTxTime() 
         txhash  = x[1].getTxHash()
         value   = x[1].getValue()
         return (txTime, numConf, txhash, value)

      # Apply table sorting -- this is very fast
      sortDir = (self.sortLedgOrder == Qt.AscendingOrder)
      if self.sortLedgCol == LEDGERCOLS.NumConf:
         self.combinedLedger.sort(key=keyFuncNumConf, reverse=sortDir)
      if self.sortLedgCol == LEDGERCOLS.DateStr:
         self.combinedLedger.sort(key=keyFuncTxTime, reverse=sortDir)
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


      if not self.usermode==USERMODE.Expert:
         return 

      # In expert mode, we're updating the lockbox info, too
      try:
         lockboxTable = []
         for lbID,cppWlt in self.cppLockboxWltMap.iteritems():

            zcLedger = cppWlt.getZeroConfLedger()
            for i in range(len(zcLedger)):
               lockboxTable.append([lbID, zcLedger[i]])

            ledger = cppWlt.getTxLedger()
            for i in range(len(ledger)):
               lockboxTable.append([lbID, ledger[i]])

         self.lockboxLedgTable = self.convertLedgerToTable(lockboxTable)
         self.lockboxLedgModel.ledger = self.lockboxLedgTable
         self.lockboxLedgModel.reset()
      except:
         LOGEXCEPT('Failed to update lockbox ledger')

   #############################################################################
   def getCommentForLockboxTx(self, lboxId, le):
      commentSet = set([])
      lbox = self.allLockboxes[self.lockboxIDMap[lboxId]]
      for a160 in lbox.a160List:
         wltID = self.getWalletForAddr160(a160)
         if wltID:
            commentSet.add(self.walletMap[wltID].getCommentForLE(le))
      return ' '.join(commentSet)

   #############################################################################
   @TimeThisFunction
   def convertLedgerToTable(self, ledger, showSentToSelfAmt=True):
      table2D = []
      datefmt = self.getPreferredDateFormat()
      for wltID,le in ledger:
         row = []

         wlt = self.walletMap.get(wltID)

         if wlt:
            isWatch = (determineWalletType(wlt, self)[0] == WLTTYPES.WatchOnly)
            wltName = wlt.labelName 
            dispComment = self.getCommentForLE(wltID, le)
         else:
            lboxId = wltID
            lbox = self.getLockboxByID(lboxId)
            if not lbox:
               continue
            isWatch = True
            wltName = '%s-of-%s: %s (%s)' % (lbox.M, lbox.N, lbox.shortName, lboxId)
            dispComment = self.getCommentForLockboxTx(lboxId, le)

         nConf = self.currBlockNum - le.getBlockNum()+1
         if le.getBlockNum()>=0xffffffff:
            nConf=0

         # If this was sent-to-self... we should display the actual specified
         # value when the transaction was executed.  This is pretty difficult
         # when both "recipient" and "change" are indistinguishable... but
         # They're actually not because we ALWAYS generate a new address to
         # for change , which means the change address MUST have a higher
         # chain index
         amt = le.getValue()
         if le.isSentToSelf() and wlt and showSentToSelfAmt:
            amt = determineSentToSelfAmt(le, wlt)[0]

         # NumConf
         row.append(nConf)

         # UnixTime (needed for sorting)
         row.append(le.getTxTime())

         # Date
         row.append(unixTimeToFormatStr(le.getTxTime(), datefmt))

         # TxDir (actually just the amt... use the sign of the amt to determine dir)
         row.append(coin2str(le.getValue(), maxZeros=2))

         # Wlt Name
         row.append(wltName)

         # Comment
         row.append(dispComment)

         # Amount
         row.append(coin2str(amt, maxZeros=2))

         # Is this money mine?
         row.append(isWatch)

         # ID to display (this might be the lockbox ID)
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
   @TimeThisFunction
   def walletListChanged(self):
      self.walletModel.reset()
      self.populateLedgerComboBox()
      self.createCombinedLedger()


   #############################################################################
   @TimeThisFunction
   def populateLedgerComboBox(self):
      self.comboWltSelect.clear()
      self.comboWltSelect.addItem( 'My Wallets'        )
      self.comboWltSelect.addItem( 'Offline Wallets'   )
      self.comboWltSelect.addItem( 'Other\'s wallets'  )
      self.comboWltSelect.addItem( 'All Wallets'       )
      self.comboWltSelect.addItem( 'Custom Filter'     )
      for wltID in self.walletIDList:
         self.comboWltSelect.addItem( self.walletMap[wltID].labelName )
      self.comboWltSelect.insertSeparator(5)
      self.comboWltSelect.insertSeparator(5)
      comboIdx = self.getSettingOrSetDefault('LastFilterState', 0)
      self.comboWltSelect.setCurrentIndex(comboIdx)

   #############################################################################
   def execDlgWalletDetails(self, index=None):
      if len(self.walletMap)==0:
         reply = QMessageBox.information(self, 'No Wallets!', \
            'You currently do not have any wallets.  Would you like to '
            'create one, now?', QMessageBox.Yes | QMessageBox.No)
         if reply==QMessageBox.Yes:
            self.startWalletWizard()
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
   def execClickRow(self, index=None):
      row,col = index.row(), index.column()
      if not col==WLTVIEWCOLS.Visible:
         return

      wltID = self.walletIDList[row]
      currEye = self.walletVisibleList[row]
      self.walletVisibleList[row] = not currEye 
      self.setWltSetting(wltID, 'LedgerShow', not currEye)
      
      # Set it to "Custom Filter"
      self.comboWltSelect.setCurrentIndex(4)
      
      if TheBDM.getBDMState()=='BlockchainReady':
         self.createCombinedLedger()
         self.ledgerModel.reset()
         self.walletModel.reset()


   #############################################################################
   def updateTxCommentFromView(self, view):
      index = view.selectedIndexes()[0]
      row, col = index.row(), index.column()
      currComment = str(view.model().index(row, LEDGERCOLS.Comment).data().toString())
      wltID       = str(view.model().index(row, LEDGERCOLS.WltID  ).data().toString())
      txHash      = str(view.model().index(row, LEDGERCOLS.TxHash ).data().toString())

      dialog = DlgSetComment(self, self, currComment, 'Transaction')
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

      dialog = DlgSetComment(self, self, currComment, 'Address')
      if dialog.exec_():
         newComment = str(dialog.edtComment.text())
         atype, addr160 = addrStr_to_hash160(addrStr)
         if atype==P2SHBYTE:
            LOGWARN('Setting comment for P2SH address: %s' % addrStr)
         wlt.setComment(addr160, newComment)



   #############################################################################
   @TimeThisFunction
   def getAddrCommentIfAvailAll(self, txHash):
      if not TheBDM.isInitialized():
         return ''
      else:

         appendedComments = []
         for wltID,wlt in self.walletMap.iteritems():
            cmt = wlt.getAddrCommentIfAvail(txHash)
            if len(cmt)>0:
               appendedComments.append(cmt)

         return '; '.join(appendedComments)



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
      LOGINFO('addWalletToApplication')
      # Update the maps/dictionaries
      newWltID = newWallet.uniqueIDB58

      if self.walletMap.has_key(newWltID):
         return

      self.walletMap[newWltID] = newWallet
      self.walletIndices[newWltID] = len(self.walletMap)-1

      # Maintain some linear lists of wallet info
      self.walletIDSet.add(newWltID)
      self.walletIDList.append(newWltID)
      showByDefault = (determineWalletType(newWallet, self)[0] != WLTTYPES.WatchOnly)
      self.walletVisibleList.append(showByDefault)
      self.setWltSetting(newWltID, 'LedgerShow', showByDefault)

      ledger = []
      self.walletListChanged()
      self.mainWnd = self


   #############################################################################
   def removeWalletFromApplication(self, wltID):
      LOGINFO('removeWalletFromApplication')
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
      del self.walletVisibleList[idx]

      # Reconstruct walletIndices
      for i,wltID in enumerate(self.walletIDList):
         self.walletIndices[wltID] = i

      self.walletListChanged()

   #############################################################################
   def RecoverWallet(self):
      DlgWltRecoverWallet(self, self).promptWalletRecovery()


   #############################################################################
   def createSweepAddrTx(self, sweepFromAddrObjList, sweepToScript):
      """
      This method takes a list of addresses (likely just created from private
      key data), finds all their unspent TxOuts, and creates a signed tx that
      transfers 100% of the funds to the sweepTO160 address.  It doesn't
      actually execute the transaction, but it will return a broadcast-ready
      PyTx object that the user can confirm.  TxFee is automatically calc'd
      and deducted from the output value, if necessary.
      """


      LOGINFO('createSweepAddrTx')
      if not isinstance(sweepFromAddrObjList, (list, tuple)):
         sweepFromAddrObjList = [sweepFromAddrObjList]

      
      addr160List = [a.getAddr160() for a in sweepFromAddrObjList]
      utxoList = getUnspentTxOutsForAddr160List(addr160List, 'Sweep', 0)
      if len(utxoList)==0:
         return [None, 0, 0]

      outValue = sumTxOutList(utxoList)

      inputSide = []
      outputSide = []

      for utxo in utxoList:
         # The PyCreateAndSignTx method require PyTx and PyBtcAddress objects
         rawTx = TheBDM.getTxByHash(utxo.getTxHash()).serialize()
         PyPrevTx = PyTx().unserialize(rawTx)
         a160 = CheckHash160(utxo.getRecipientScrAddr())
         for aobj in sweepFromAddrObjList:
            if a160 == aobj.getAddr160():
               pubKey = aobj.binPublicKey65.toBinStr()
               txoIdx = utxo.getTxOutIndex()
               inputSide.append(UnsignedTxInput(rawTx, txoIdx, None, pubKey))
               break

      minFee = calcMinSuggestedFees(utxoList, outValue, 0, 1)[1]

      if minFee > 0:
         LOGDEBUG( 'Subtracting fee from Sweep-output')
         outValue -= minFee

      if outValue<=0:
         return [None, outValue, minFee]

      # Creating the output list is pretty easy...
      outputSide = []
      outputSide.append(DecoratedTxOut(sweepToScript, outValue))

      try:
         # Make copies, destroy them in the finally clause
         privKeyMap = {}
         for addrObj in sweepFromAddrObjList:
            scrAddr = SCRADDR_P2PKH_BYTE + addrObj.getAddr160()
            privKeyMap[scrAddr] = addrObj.binPrivKey32_Plain.copy()
   
         pytx = PyCreateAndSignTx(inputSide, outputSide, privKeyMap)
         return (pytx, outValue, minFee)

      finally:
         for scraddr in privKeyMap:
            privKeyMap[scraddr].destroy()

      """
      # Try with zero fee and exactly one output
      minFee = calcMinSuggestedFees(utxoList, outValue, 0, 1)[1]

      if minFee > 0:
         LOGDEBUG( 'Subtracting fee from Sweep-output')
         outValue -= minFee

      if outValue<=0:
         return [None, outValue, minFee]

      outputSide = []
      outputSide.append( [PyBtcAddress().createFromPublicKeyHash160(sweepTo160), \
                          outValue] )

      pytx = PyCreateAndSignTx(inputSide, outputSide)
      return (pytx, outValue, minFee)
      """





   #############################################################################
   def confirmSweepScan(self, pybtcaddrList, targAddr160):
      LOGINFO('confirmSweepScan')
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
            TheBDM.registerImportedScrAddr(Hash160ToScrAddr(addr.getAddr160()))
         self.sweepAfterScanList = pybtcaddrList
         self.sweepAfterScanTarg = targAddr160
         #TheBDM.rescanBlockchain('AsNeeded', wait=False)
         self.startRescanBlockchain()
         self.setDashboardDetails()
         return True


   #############################################################################
   def finishSweepScan(self):
      LOGINFO('finishSweepScan')
      sweepList, self.sweepAfterScanList = self.sweepAfterScanList,[]

      #######################################################################
      # The createSweepTx method will return instantly because the blockchain
      # has already been rescanned, as described above
      targScript = scrAddr_to_script(SCRADDR_P2PKH_BYTE + self.sweepAfterScanTarg)
      finishedTx, outVal, fee = self.createSweepAddrTx(sweepList, targScript)

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
         dispIn  = 'multiple addresses'
      else:
         dispIn  = 'address <b>%s</b>' % sweepList[0].getAddrStr()

      dispOut = 'wallet <b>"%s"</b> (%s) ' % (wlt.labelName, wlt.uniqueIDB58)
      if DlgVerifySweep(dispIn, dispOut, outVal, fee).exec_():
         self.broadcastTransaction(finishedTx, dryRun=False)

      if TheBDM.getBDMState()=='BlockchainReady':
         wlt.syncWithBlockchain(0)

      self.walletListChanged()

   #############################################################################
   def broadcastTransaction(self, pytx, dryRun=False, withOldSigWarning=True):

      if dryRun:
         #DlgDispTxInfo(pytx, None, self, self).exec_()
         return
      else:
         modified, newTx = pytx.minimizeDERSignaturePadding()
         if modified and withOldSigWarning:
            reply = QMessageBox.warning(self, 'Old signature format detected', \
                 'The transaction that you are about to execute '
                 'has been signed with an older version Bitcoin Armory '
                 'that has added unnecessary padding to the signature. '
                 'If you are running version Bitcoin 0.8.2 or later the unnecessary '
                 'the unnecessary signature padding will not be broadcast. '
                 'Note that removing the unnecessary padding will change the hash value '
                 'of the transaction. Do you want to remove the unnecessary padding?', QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
               pytx = newTx
         LOGRAWDATA(pytx.serialize(), logging.INFO)
         LOGPPRINT(pytx, logging.INFO)
         newTxHash = pytx.getHash()
         LOGINFO('Sending Tx, %s', binary_to_hex(newTxHash))
         self.NetworkingFactory.sendTx(pytx)
         LOGINFO('Transaction sent to Satoshi client...!')


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
               searchstr  = binary_to_hex(newTxHash, BIGENDIAN)

               supportURL       = 'https://bitcoinarmory.com/support' 
               blkexplURL       = BLOCKEXPLORE_URL_TX % searchstr
               blkexplURL_short = BLOCKEXPLORE_URL_TX % searchstr[:20]

               QMessageBox.warning(self, tr('Transaction Not Accepted'), tr("""
                  The transaction that you just executed, does not 
                  appear to have been accepted by the Bitcoin network. 
                  This can happen for a variety of reasons, but it is 
                  usually due to a bug in the Armory software.  
                  <br><br>On some occasions the transaction actually did succeed 
                  and this message is the bug itself!  To confirm whether the 
                  the transaction actually succeeded, you can try this direct link 
                  to %s:
                  <br><br>
                  <a href="%s">%s...</a>  
                  <br><br>
                  If you do not see the 
                  transaction on that webpage within one minute, it failed and you 
                  should attempt to re-send it. 
                  If it <i>does</i> show up, then you do not need to do anything 
                  else -- it will show up in Armory as soon as it receives one
                  confirmation. 
                  <br><br>If the transaction did fail, please consider 
                  reporting this error the the Armory developers.  
                  From the main window, go to "<i>Help</i>" and select 
                  "<i>Submit Bug Report</i>".  Or use "<i>File</i>" -> 
                  "<i>Export Log File</i>" and then attach it to a support 
                  ticket at 
                  <a href="%s">%s</a>""") % (BLOCKEXPLORE_NAME, blkexplURL, 
                  blkexplURL_short, supportURL, supportURL), QMessageBox.Ok)

         self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Ledger)

         # Send the Tx after a short delay, give the system time to see the Tx
         # on the network and process it, and check to see if the Tx was seen.
         # We may change this setup in the future, but for now....
         reactor.callLater(3, sendGetDataMsg)
         reactor.callLater(7, checkForTxInBDM)


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
      sdm = TheSDM.getSDMState()
      bdm = TheBDM.getBDMState()
      if sdm in ['BitcoindInitializing', \
                 'BitcoindSynchronizing', \
                 'TorrentSynchronizing'] or \
         bdm in ['Scanning']:
         QMessageBox.warning(self, tr('Scanning'), tr("""
            Armory is currently in the middle of scanning the blockchain for
            your existing wallets.  New wallets cannot be imported until this
            operation is finished."""), QMessageBox.Ok)
         return

      DlgUniversalRestoreSelect(self, self).exec_()


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

      self.addWalletToAppAndAskAboutRescan(newWlt)

      """ I think the addWalletToAppAndAskAboutRescan replaces this...
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
         #TheBDM.startWalletRecoveryScan(newWlt)  # TODO: re-enable this later
         #TheBDM.rescanBlockchain('AsNeeded', wait=False)
         self.startRescanBlockchain()
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

      self.addWalletToApplication(newWlt, walletIsNew=False)
      self.newWalletList.append([newWlt, False])
      LOGINFO('Import Complete!')
      """




   #############################################################################
   def addWalletToAppAndAskAboutRescan(self, newWallet):
      LOGINFO('Raw import successful.')

      # If we are offline, then we can't assume there will ever be a
      # rescan.  Just add the wallet to the application
      if TheBDM.getBDMState() in ('Uninitialized', 'Offline'):
         TheBDM.registerWallet(newWallet.cppWallet)
         self.addWalletToApplication(newWallet, walletIsNew=False)
         return

      """  TODO:  Temporarily removed recovery-rescan operations
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
      """

      doRescanNow = QMessageBox.Cancel

      if TheBDM.getBDMState()=='BlockchainReady':
         doRescanNow = QMessageBox.question(self, tr('Rescan Needed'), \
            tr("""The wallet was restored successfully but its balance
            cannot be displayed until the blockchain is rescanned.
            Armory will need to go into offline mode for 5-20 minutes.
            <br><br>
            Would you like to do the scan now?  Clicking "No" will
            abort the restore/import operation."""), \
            QMessageBox.Yes | QMessageBox.No)
      else:
         doRescanNow = QMessageBox.question(self, tr('Rescan Needed'), \
            tr("""The wallet was restored successfully but its balance
            cannot be displayed until the blockchain is rescanned.
            However, Armory is currently in the middle of a rescan
            operation right now.  Would you like to start a new scan
            as soon as this one is finished?
            <br><br>
            Clicking "No" will abort adding the wallet to Armory."""), \
            QMessageBox.Yes | QMessageBox.No)


      if doRescanNow == QMessageBox.Yes:
         LOGINFO('User requested rescan after wallet restore')
         #TheBDM.startWalletRecoveryScan(newWallet)
         TheBDM.registerWallet(newWallet.cppWallet)
         self.startRescanBlockchain()
         self.setDashboardDetails()
      else:
         LOGINFO('User aborted the wallet-recovery scan')
         QMessageBox.warning(self, 'Import Failed', \
            'The wallet was not restored.  To restore the wallet, reenter '
            'the "Restore Wallet" dialog again when you are able to wait '
            'for the rescan operation.  ', QMessageBox.Ok)
         # The wallet cannot exist without also being on disk.
         # If the user aborted, we should remove the disk data.
         thepath       = newWallet.getWalletPath()
         thepathBackup = newWallet.getWalletPath('backup')
         os.remove(thepath)
         os.remove(thepathBackup)
         return

      self.addWalletToApplication(newWallet, walletIsNew=False)
      LOGINFO('Import Complete!')


   #############################################################################
   def digitalBackupWarning(self):
      reply = QMessageBox.warning(self, 'Be Careful!', tr("""
        <font color="red"><b>WARNING:</b></font> You are about to make an
        <u>unencrypted</u> backup of your wallet.  It is highly recommended
        that you do <u>not</u> ever save unencrypted wallets to your regular
        hard drive.  This feature is intended for saving to a USB key or
        other removable media."""), QMessageBox.Ok | QMessageBox.Cancel)
      return (reply==QMessageBox.Ok)


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
            raise WalletExistsError('Cannot find unique filename for wallet.'
                                                       'Too many duplicates!')
      return fname


   #############################################################################
   def addrViewDblClicked(self, index, wlt):
      uacfv = lambda x: self.updateAddressCommentFromView(self.wltAddrView, self.wlt)


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

      row = self.ledgerView.selectedIndexes()[0].row()

      txHash = str(self.ledgerView.model().index(row, LEDGERCOLS.TxHash).data().toString())
      txHash = hex_switchEndian(txHash)
      wltID  = str(self.ledgerView.model().index(row, LEDGERCOLS.WltID).data().toString())


      actViewTx     = menu.addAction("View Details")
      actViewBlkChn = menu.addAction("View on %s" % BLOCKEXPLORE_NAME)
      actComment    = menu.addAction("Change Comment")
      actCopyTxID   = menu.addAction("Copy Transaction ID")
      actOpenWallet = menu.addAction("Open Relevant Wallet")
      action = menu.exec_(QCursor.pos())

      if action==actViewTx:
         self.showLedgerTx()
      elif action==actViewBlkChn:
         try:
            webbrowser.open(BLOCKEXPLORE_URL_TX % txHash)
         except:
            LOGEXCEPT('Failed to open webbrowser')
            QMessageBox.critical(self, 'Could not open browser', \
               'Armory encountered an error opening your web browser.  To view '
               'this transaction on blockchain.info, please copy and paste '
               'the following URL into your browser: '
               '<br><br>%s' % (BLOCKEXPLORE_URL_TX % txHash), QMessageBox.Ok)
      elif action==actCopyTxID:
         clipb = QApplication.clipboard()
         clipb.clear()
         clipb.setText(txHash)
      elif action==actComment:
         self.updateTxCommentFromView(self.ledgerView)
      elif action==actOpenWallet:
         DlgWalletDetails(self.getSelectedWallet(), self.usermode, self, self).exec_()

   #############################################################################

   def getSelectedWallet(self):
      wltID = None
      if len(self.walletMap) > 0:
         wltID = self.walletMap.keys()[0]
      wltSelect = self.walletsView.selectedIndexes()
      if len(wltSelect) > 0:
         row = wltSelect[0].row()
         wltID = str(self.walletsView.model().index(row, WLTVIEWCOLS.ID).data().toString())
      # Starting the send dialog  with or without a wallet
      return None if wltID == None else self.walletMap[wltID]

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

      selectionMade = True
      if len(self.walletMap)==0:
         reply = QMessageBox.information(self, 'No Wallets!', \
            'You cannot send any bitcoins until you create a wallet and '
            'receive some coins.  Would you like to create a wallet?', \
            QMessageBox.Yes | QMessageBox.No)
         if reply==QMessageBox.Yes:
            self.startWalletWizard()
      else:
         DlgSendBitcoins(self.getSelectedWallet(), self, self).exec_()


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
            self.startWalletWizard()
         return False
      else:
         DlgSendBitcoins(self.getSelectedWallet(), self, self, uriDict).exec_()
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
            self.startWalletWizard()
         return
      elif len(self.walletMap)==1:
         wltID = self.walletMap.keys()[0]
      else:
         wltSelect = self.walletsView.selectedIndexes()
         if len(wltSelect)>0:
            row = wltSelect[0].row()
            wltID = str(self.walletsView.model().index(row, WLTVIEWCOLS.ID).data().toString())
         dlg = DlgWalletSelect(self, self, 'Receive coins with wallet...', '', \
                                       firstSelect=wltID, onlyMyWallets=False)
         if dlg.exec_():
            wltID = dlg.selectedID
         else:
            selectionMade = False

      if selectionMade:
         wlt = self.walletMap[wltID]
         wlttype = determineWalletType(wlt, self)[0]
         if showRecvCoinsWarningIfNecessary(wlt, self):
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
   def startWalletWizard(self):
      walletWizard = WalletWizard(self, self)
      walletWizard.exec_()

   #############################################################################
   def startTxWizard(self, prefill=None, onlyOfflineWallets=False):
      txWizard = TxWizard(self, self, self.getSelectedWallet(), prefill, onlyOfflineWallets=onlyOfflineWallets)
      txWizard.exec_()

   #############################################################################
   def exportLogFile(self):
      LOGDEBUG('exportLogFile')
      reply = QMessageBox.warning(self, tr('Bug Reporting'), tr("""
         As of version 0.91, Armory now includes a form for reporting
         problems with the software.  Please use
         <i>"Help"</i>\xe2\x86\x92<i>"Submit Bug Report"</i>
         to send a report directly to the Armory team, which will include
         your log file automatically."""), QMessageBox.Ok | QMessageBox.Cancel)

      if not reply==QMessageBox.Ok:
         return

      if self.logFilePrivacyWarning(wCancel=True):
         self.saveCombinedLogFile()

   #############################################################################
   def getUserAgreeToPrivacy(self, getAgreement=False):
      ptype = 'submitbug' if getAgreement else 'generic'
      dlg = DlgPrivacyPolicy(self, self, ptype)
      if not dlg.exec_():
         return False

      return dlg.chkUserAgrees.isChecked()

   #############################################################################
   def logFileTriplePrivacyWarning(self):
      return MsgBoxCustom(MSGBOX.Warning, tr('Privacy Warning'), tr("""
         <b><u><font size=4>ATI Privacy Policy</font></u></b>
         <br><br>
         You should review the <a href="%s">Armory Technologies, Inc. privacy 
         policy</a> before sending any data to ATI servers.
         <br><br>

         <b><u><font size=3>Wallet Analysis Log Files</font></u></b>
         <br><br>
         The wallet analysis logs contain no personally-identifiable
         information, only a record of errors and inconsistencies 
         found in your wallet file.  No private keys or even public 
         keys are included.
         <br><br>

         <b><u><font size=3>Regular Log Files</font></u></b>
         <br><br>
         The regular log files do not contain any <u>security</u>-sensitive
         information, but some users may consider the information to be
         <u>privacy</u>-sensitive.  The log files may identify some addresses
         and transactions that are related to your wallets.  It is always 
         recommended you include your log files with any request to the
         Armory team, unless you are uncomfortable with the privacy 
         implications.
         <br><br>

         <b><u><font size=3>Watching-only Wallet</font></u></b>
         <br><br>
         A watching-only wallet is a copy of a regular wallet that does not 
         contain any signing keys.  This allows the holder to see the balance
         and transaction history of the wallet, but not spend any of the funds.
         <br><br>
         You may be requested to submit a watching-only copy of your wallet
         to <i>Armory Technologies, Inc.</i> to make sure that there is no 
         risk to the security of your funds.  You should not even consider 
         sending your
         watching-only wallet unless it was specifically requested by an
         Armory representative.""") % PRIVACY_URL, yesStr="&Ok")
          

   #############################################################################
   def logFilePrivacyWarning(self, wCancel=False):
      return MsgBoxCustom(MSGBOX.Warning, tr('Privacy Warning'), tr("""
         <b><u><font size=4>ATI Privacy Policy</font></u></b>
         <br>
         You should review the <a href="%s">Armory Technologies, Inc. privacy 
         policy</a> before sending any data to ATI servers.
         <br><br>

         Armory log files do not contain any <u>security</u>-sensitive
         information, but some users may consider the information to be
         <u>privacy</u>-sensitive.  The log files may identify some addresses
         and transactions that are related to your wallets.
         <br><br>

         <b>No signing-key data is ever written to the log file</b>.
         Only enough data is there to help the Armory developers
         track down bugs in the software, but it may still be considered
         sensitive information to some users.
         <br><br>

         Please do not send the log file to the Armory developers if you
         are not comfortable with the privacy implications!  However, if you
         do not send the log file, it may be very difficult or impossible
         for us to help you with your problem.

         <br><br><b><u>Advanced tip:</u></b> You can use
         "<i>File</i>"\xe2\x86\x92"<i>Export Log File</i>" from the main
         window to save a copy of the log file that you can manually
         review."""), wCancel=wCancel, yesStr="&Ok")


   #############################################################################
   def saveCombinedLogFile(self, saveFile=None):
      if saveFile is None:
         # TODO: Interleave the C++ log and the python log.
         #       That could be a lot of work!
         defaultFN = 'armorylog_%s.txt' % \
                     unixTimeToFormatStr(RightNow(),'%Y%m%d_%H%M')
         saveFile = self.getFileSave(title='Export Log File', \
                                  ffilter=['Text Files (*.txt)'], \
                                  defaultFilename=defaultFN)

      if len(unicode(saveFile)) > 0:
         fout = open(saveFile, 'wb')
         fout.write(getLastBytesOfFile(ARMORY_LOG_FILE, 256*1024))
         fout.write(getLastBytesOfFile(ARMCPP_LOG_FILE, 256*1024))
         fout.close()

         LOGINFO('Log saved to %s', saveFile)

   #############################################################################
   def blinkTaskbar(self):
      self.activateWindow()


   #############################################################################
   def lookForBitcoind(self):
      LOGDEBUG('lookForBitcoind')
      if satoshiIsAvailable():
         return 'Running'

      self.setSatoshiPaths()

      try:
         TheSDM.setupSDM(extraExeSearch=self.satoshiExeSearchPath)
      except:
         LOGEXCEPT('Error setting up SDM')
         pass

      if TheSDM.failedFindExe:
         return 'StillMissing'

      return 'AllGood'

   #############################################################################
   def executeModeSwitch(self):
      LOGDEBUG('executeModeSwitch')

      if TheSDM.getSDMState() == 'BitcoindExeMissing':
         bitcoindStat = self.lookForBitcoind()
         if bitcoindStat=='Running':
            result = QMessageBox.warning(self, tr('Already running!'), tr("""
               The Bitcoin software appears to be installed now, but it
               needs to be closed for Armory to work.  Would you like Armory
               to close it for you?"""), QMessageBox.Yes | QMessageBox.No)
            if result==QMessageBox.Yes:
               self.closeExistingBitcoin()
               self.startBitcoindIfNecessary()
         elif bitcoindStat=='StillMissing':
            QMessageBox.warning(self, tr('Still Missing'), tr("""
               The Bitcoin software still appears to be missing.  If you
               just installed it, then please adjust your settings to point
               to the installation directory."""), QMessageBox.Ok)
         self.startBitcoindIfNecessary()
      elif self.doAutoBitcoind and not TheSDM.isRunningBitcoind():
         if satoshiIsAvailable():
            result = QMessageBox.warning(self, tr('Still Running'), tr("""
               'Bitcoin-Qt is still running.  Armory cannot start until
               'it is closed.  Do you want Armory to close it for you?"""), \
               QMessageBox.Yes | QMessageBox.No)
            if result==QMessageBox.Yes:
               self.closeExistingBitcoin()
               self.startBitcoindIfNecessary()
         else:
            self.startBitcoindIfNecessary()
      elif TheBDM.getBDMState() == 'BlockchainReady' and TheBDM.isDirty():
         #self.resetBdmBeforeScan()
         self.startRescanBlockchain()
      elif TheBDM.getBDMState() in ('Offline','Uninitialized'):
         #self.resetBdmBeforeScan()
         TheBDM.setOnlineMode(True)
         self.switchNetworkMode(NETWORKMODE.Full)
      else:
         LOGERROR('ModeSwitch button pressed when it should be disabled')
      time.sleep(0.3)
      self.setDashboardDetails()




   #############################################################################
   @TimeThisFunction
   def resetBdmBeforeScan(self):
      if TheBDM.getBDMState()=='Scanning':
         LOGINFO('Aborting load')
         touchFile(os.path.join(ARMORY_HOME_DIR,'abortload.txt'))
         os.remove(os.path.join(ARMORY_HOME_DIR,'blkfiles.txt'))

      TheBDM.Reset(wait=False)
      for wid,wlt in self.walletMap.iteritems():
         TheBDM.registerWallet(wlt.cppWallet)



   #############################################################################
   def setupDashboard(self):
      LOGDEBUG('setupDashboard')
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
                                       self.executeModeSwitch)


      # Will switch this to array/matrix of widgets if I get more than 2 rows
      self.lblDashModeTorrent = QRichLabel('',doWrap=False)
      self.lblDashModeSync    = QRichLabel('',doWrap=False)
      self.lblDashModeBuild   = QRichLabel('',doWrap=False)
      self.lblDashModeScan    = QRichLabel('',doWrap=False)

      self.lblDashModeTorrent.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
      self.lblDashModeSync.setAlignment(   Qt.AlignLeft | Qt.AlignVCenter)
      self.lblDashModeBuild.setAlignment(  Qt.AlignLeft | Qt.AlignVCenter)
      self.lblDashModeScan.setAlignment(   Qt.AlignLeft | Qt.AlignVCenter)

      self.barProgressTorrent = QProgressBar(self)
      self.barProgressSync    = QProgressBar(self)
      self.barProgressBuild   = QProgressBar(self)
      self.barProgressScan    = QProgressBar(self)

      self.barProgressTorrent.setRange(0,100)
      self.barProgressSync.setRange(0,100)
      self.barProgressBuild.setRange(0,100)
      self.barProgressScan.setRange(0,100)


      self.lblTorrentStats       = QRichLabel('', hAlign=Qt.AlignHCenter)

      twid = relaxedSizeStr(self,'99 seconds')[0]
      self.lblTimeLeftTorrent = QRichLabel('')
      self.lblTimeLeftSync    = QRichLabel('')
      self.lblTimeLeftBuild   = QRichLabel('')
      self.lblTimeLeftScan    = QRichLabel('')

      self.lblTimeLeftSync.setMinimumWidth(twid)
      self.lblTimeLeftScan.setMinimumWidth(twid)

      self.lblStatsTorrent = QRichLabel('')

      layoutDashMode = QGridLayout()
      layoutDashMode.addWidget(self.lblDashModeTorrent,  0,0)
      layoutDashMode.addWidget(self.barProgressTorrent,  0,1)
      layoutDashMode.addWidget(self.lblTimeLeftTorrent,  0,2)
      layoutDashMode.addWidget(self.lblTorrentStats,     1,0)

      layoutDashMode.addWidget(self.lblDashModeSync,     2,0)
      layoutDashMode.addWidget(self.barProgressSync,     2,1)
      layoutDashMode.addWidget(self.lblTimeLeftSync,     2,2)

      layoutDashMode.addWidget(self.lblDashModeBuild,    3,0)
      layoutDashMode.addWidget(self.barProgressBuild,    3,1)
      layoutDashMode.addWidget(self.lblTimeLeftBuild,    3,2)

      layoutDashMode.addWidget(self.lblDashModeScan,     4,0)
      layoutDashMode.addWidget(self.barProgressScan,     4,1)
      layoutDashMode.addWidget(self.lblTimeLeftScan,     4,2)

      layoutDashMode.addWidget(self.lblBusy,             0,3, 5,1)
      layoutDashMode.addWidget(self.btnModeSwitch,       0,3, 5,1)

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
      self.lblDashBtnDescr.setOpenExternalLinks(True)
      BTN,LBL,TTIP = range(3)
      self.dashBtns = [[None]*3 for i in range(5)]
      self.dashBtns[DASHBTNS.Close   ][BTN] = QPushButton('Close Bitcoin Process')
      self.dashBtns[DASHBTNS.Install ][BTN] = QPushButton('Download Bitcoin')
      self.dashBtns[DASHBTNS.Browse  ][BTN] = QPushButton('Open www.bitcoin.org')
      self.dashBtns[DASHBTNS.Instruct][BTN] = QPushButton('Installation Instructions')
      self.dashBtns[DASHBTNS.Settings][BTN] = QPushButton('Change Settings')


      #####
      def openBitcoinOrg():
         webbrowser.open('http://www.bitcoin.org/en/download')


      #####
      def openInstruct():
         if OS_WINDOWS:
            webbrowser.open('https://www.bitcoinarmory.com/install-windows/')
         elif OS_LINUX:
            webbrowser.open('https://www.bitcoinarmory.com/install-linux/')
         elif OS_MACOSX:
            webbrowser.open('https://www.bitcoinarmory.com/install-macosx/')






      self.connect(self.dashBtns[DASHBTNS.Close][BTN], SIGNAL('clicked()'), \
                                                   self.closeExistingBitcoin)
      self.connect(self.dashBtns[DASHBTNS.Install][BTN], SIGNAL('clicked()'), \
                                                     self.openDLSatoshi)
      self.connect(self.dashBtns[DASHBTNS.Browse][BTN], SIGNAL('clicked()'), \
                                                             openBitcoinOrg)
      self.connect(self.dashBtns[DASHBTNS.Settings][BTN], SIGNAL('clicked()'), \
                                                           self.openSettings)
      #self.connect(self.dashBtns[DASHBTNS.Instruct][BTN], SIGNAL('clicked()'), \
                                                     #self.openInstructWindow)

      self.dashBtns[DASHBTNS.Close][LBL] = QRichLabel( \
           'Stop existing Bitcoin processes so that Armory can open its own')
      self.dashBtns[DASHBTNS.Browse][LBL]     = QRichLabel( \
           'Open browser to Bitcoin webpage to download and install Bitcoin software')
      self.dashBtns[DASHBTNS.Instruct][LBL] = QRichLabel( \
           'Instructions for manually installing Bitcoin for operating system')
      self.dashBtns[DASHBTNS.Settings][LBL]  = QRichLabel( \
           'Open Armory settings window to change Bitcoin software management')


      self.dashBtns[DASHBTNS.Browse][TTIP] = self.createToolTipWidget( \
           'Will open your default browser to http://www.bitcoin.org where you can '
           'download the latest version of Bitcoin-Qt, and get other information '
           'and links about Bitcoin, in general.')
      self.dashBtns[DASHBTNS.Instruct][TTIP] = self.createToolTipWidget( \
           'Instructions are specific to your operating system and include '
           'information to help you verify you are installing the correct software')
      self.dashBtns[DASHBTNS.Settings][TTIP] = self.createToolTipWidget(
           'Change Bitcoin-Qt/bitcoind management settings or point Armory to '
           'a non-standard Bitcoin installation')
      self.dashBtns[DASHBTNS.Close][TTIP] = self.createToolTipWidget( \
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
         self.dashBtns[DASHBTNS.Install][TTIP] = self.createToolTipWidget( \
            'The downloaded files are cryptographically verified.  '
            'Using this option will start the installer, you will '
            'have to click through it to complete installation.')

         #self.lblDashInstallForMe = QRichLabel( \
           #'Armory will download, verify, and start the Bitcoin installer for you')
         #self.ttipInstallForMe = self.createToolTipWidget( \
           #'Armory will download the latest version of the Bitcoin software '
           #'for Windows and verify its digital signatures.  You will have to '
           #'click through the installation options.<u></u>')
      elif OS_LINUX:
         # Only display the install button if using a debian-based distro
         dist = platform.linux_distribution()
         if dist[0] in ['Ubuntu','LinuxMint'] or 'debian' in dist:
            self.dashBtns[DASHBTNS.Install][BTN].setEnabled(True)
            self.dashBtns[DASHBTNS.Install][LBL] = QRichLabel( tr("""
               Download and Install Bitcoin Core for Ubuntu/Debian"""))
            self.dashBtns[DASHBTNS.Install][TTIP] = self.createToolTipWidget( tr("""
               'Will download and Bitcoin software and cryptographically verify it"""))
      elif OS_MACOSX:
         pass
      else:
         LOGERROR('Unrecognized OS!')


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

      self.dashScrollArea = QScrollArea()
      self.dashScrollArea.setWidgetResizable(True)
      self.dashScrollArea.setWidget(frmInner)
      scrollLayout = QVBoxLayout()
      scrollLayout.addWidget(self.dashScrollArea)
      self.tabDashboard.setLayout(scrollLayout)



   #############################################################################
   def setupAnnounceTab(self):

      self.lblAlertStr = QRichLabel(tr("""
         <font size=4><b>Announcements and alerts from <i>Armory Technologies,
         Inc.</i></b></font>"""), doWrap=False, hAlign=Qt.AlignHCenter)

      def checkUpd():
         lastUpdate = self.announceFetcher.getLastSuccessfulFetchTime()
         self.explicitCheckAnnouncements(5)
         lastUpdate2 = self.announceFetcher.getLastSuccessfulFetchTime()
         if lastUpdate==lastUpdate2:
            QMessageBox.warning(self, tr('Not Available'), tr("""
               Could not access the <font color="%s"><b>Armory
               Technologies, Inc.</b></font> announcement feeder.
               Try again in a couple minutes.""") % \
               htmlColor('TextGreen'), QMessageBox.Ok)
         else:
            QMessageBox.warning(self, tr('Update'), tr("""
               Announcements are now up to date!"""), QMessageBox.Ok)


      self.lblLastUpdated = QRichLabel('', doWrap=False)
      self.btnCheckForUpdates  = QPushButton(tr('Check for Updates'))
      self.connect(self.btnCheckForUpdates, SIGNAL(CLICKED), checkUpd)


      frmLastUpdate = makeHorizFrame(['Stretch', \
                                      self.lblLastUpdated, \
                                      self.btnCheckForUpdates, \
                                      'Stretch'])

      self.icoArmorySWVersion = QLabel('')
      self.lblArmorySWVersion = QRichLabel(tr("""
         No version information is available"""), doWrap=False)
      self.icoSatoshiSWVersion = QLabel('')
      self.lblSatoshiSWVersion = QRichLabel('', doWrap=False)

      self.btnSecureDLArmory  = QPushButton(tr('Secure Downloader'))
      self.btnSecureDLSatoshi = QPushButton(tr('Secure Downloader'))
      self.btnSecureDLArmory.setVisible(False)
      self.btnSecureDLSatoshi.setVisible(False)
      self.connect(self.btnSecureDLArmory, SIGNAL(CLICKED), self.openDLArmory)
      self.connect(self.btnSecureDLSatoshi, SIGNAL(CLICKED), self.openDLSatoshi)


      frmVersions = QFrame()
      layoutVersions = QGridLayout()
      layoutVersions.addWidget(self.icoArmorySWVersion, 0,0)
      layoutVersions.addWidget(self.lblArmorySWVersion, 0,1)
      layoutVersions.addWidget(self.btnSecureDLArmory,  0,2)
      layoutVersions.addWidget(self.icoSatoshiSWVersion, 1,0)
      layoutVersions.addWidget(self.lblSatoshiSWVersion, 1,1)
      layoutVersions.addWidget(self.btnSecureDLSatoshi,  1,2)
      layoutVersions.setColumnStretch(0,0)
      layoutVersions.setColumnStretch(1,1)
      layoutVersions.setColumnStretch(2,0)
      frmVersions.setLayout(layoutVersions)
      frmVersions.setFrameStyle(STYLE_RAISED)

      lblVerHeader = QRichLabel(tr("""<font size=4><b>
         Software Version Updates:</b></font>"""), doWrap=False, \
         hAlign=Qt.AlignHCenter)
      lblTableHeader = QRichLabel(tr("""<font size=4><b>
         All Available Notifications:</b></font>"""), doWrap=False, \
         hAlign=Qt.AlignHCenter)


      # We need to generate popups when a widget is clicked, and be able
      # change that particular widget's target, when the table is updated.
      # Create one of these DlgGen objects for each of the 10 rows, simply
      # update it's nid and notifyMap when the table is updated
      class DlgGen():
         def setParams(self, parent, nid, notifyMap):
            self.parent = parent
            self.nid = nid
            self.notifyMap = notifyMap

         def __call__(self):
            return DlgNotificationWithDNAA(self.parent, self.parent, \
                                          self.nid, self.notifyMap, False).exec_()

      self.announceTableWidgets = \
         [[QLabel(''), QRichLabel(''), QLabelButton('+'), DlgGen()] \
                                                      for i in range(10)]



      layoutTable = QGridLayout()
      for i in range(10):
         for j in range(3):
            layoutTable.addWidget(self.announceTableWidgets[i][j], i,j)
         self.connect(self.announceTableWidgets[i][2], SIGNAL(CLICKED), \
                      self.announceTableWidgets[i][3])

      layoutTable.setColumnStretch(0,0)
      layoutTable.setColumnStretch(1,1)
      layoutTable.setColumnStretch(2,0)

      frmTable = QFrame()
      frmTable.setLayout(layoutTable)
      frmTable.setFrameStyle(STYLE_SUNKEN)

      self.updateAnnounceTable()


      frmEverything = makeVertFrame( [ self.lblAlertStr,
                                       frmLastUpdate,
                                       'Space(30)',
                                       lblTableHeader,
                                       frmTable,
                                       'Space(30)',
                                       lblVerHeader,
                                       frmVersions,
                                       'Stretch'])

      frmEverything.setMinimumWidth(300)
      frmEverything.setMaximumWidth(800)

      frmFinal = makeHorizFrame(['Stretch', frmEverything, 'Stretch'])

      self.announceScrollArea = QScrollArea()
      self.announceScrollArea.setWidgetResizable(True)
      self.announceScrollArea.setWidget(frmFinal)
      scrollLayout = QVBoxLayout()
      scrollLayout.addWidget(self.announceScrollArea)
      self.tabAnnounce.setLayout(scrollLayout)

      self.announceIsSetup = True


   #############################################################################
   def openDownloaderAll(self):
      dl,cl = self.getDownloaderData()
      if not dl is None and not cl is None:
         UpgradeDownloaderDialog(self, self, None, dl, cl).exec_()

   #############################################################################
   def openDLArmory(self):
      dl,cl = self.getDownloaderData()
      if not dl is None and not cl is None:
         UpgradeDownloaderDialog(self, self, 'Armory', dl, cl).exec_()

   #############################################################################
   def openDLSatoshi(self):
      dl,cl = self.getDownloaderData()
      if not dl is None and not cl is None:
         UpgradeDownloaderDialog(self, self, 'Satoshi', dl, cl).exec_()


   #############################################################################
   def getDownloaderData(self):
      dl = self.announceFetcher.getAnnounceFile('downloads')
      cl = self.announceFetcher.getAnnounceFile('changelog')

      dlObj = downloadLinkParser().parseDownloadList(dl)
      clObj = changelogParser().parseChangelogText(cl)

      if dlObj is None or clObj is None:
         QMessageBox.warning(self, tr('No Data'), tr("""
            The secure downloader has not received any download
            data to display.  Either the <font color="%s"><b>Armory
            Technologies, Inc.</b></font> announcement feeder is
            down, or this computer cannot access the server.""") % \
            htmlColor('TextGreen'), QMessageBox.Ok)
         return None,None

      lastUpdate = self.announceFetcher.getLastSuccessfulFetchTime()
      sinceLastUpd = RightNow() - lastUpdate
      if lastUpdate < RightNow()-1*WEEK:
         QMessageBox.warning(self, tr('Old Data'), tr("""
            The last update retrieved from the <font color="%s"><b>Armory
            Technologies, Inc.</b></font> announcement feeder was <b>%s</b>
            ago.  The following downloads may not be the latest
            available.""") % (htmlColor("TextGreen"), \
            secondsToHumanTime(sinceLastUpd)), QMessageBox.Ok)

      dl = self.announceFetcher.getAnnounceFile('downloads')
      cl = self.announceFetcher.getAnnounceFile('changelog')

      return dl,cl



   #############################################################################
   def updateAnnounceTab(self, *args):

      if not self.announceIsSetup:
         return

      iconArmory   = ':/armory_icon_32x32.png'
      iconSatoshi  = ':/bitcoinlogo.png'
      iconInfoFile = ':/MsgBox_info48.png'
      iconGoodFile = ':/MsgBox_good48.png'
      iconWarnFile = ':/MsgBox_warning48.png'
      iconCritFile = ':/MsgBox_critical24.png'

      lastUpdate = self.announceFetcher.getLastSuccessfulFetchTime()
      noAnnounce = (lastUpdate == 0)

      if noAnnounce:
         self.lblLastUpdated.setText(tr("No announcement data was found!"))
         self.btnSecureDLArmory.setVisible(False)
         self.icoArmorySWVersion.setVisible(True)
         self.lblArmorySWVersion.setText(tr(""" You are running Armory
            version %s""") % getVersionString(BTCARMORY_VERSION))
      else:
         updTimeStr = unixTimeToFormatStr(lastUpdate)
         self.lblLastUpdated.setText(tr("<u>Last Updated</u>: %s") % updTimeStr)


      verStrToInt = lambda s: getVersionInt(readVersionString(s))

      # Notify of Armory updates
      self.icoArmorySWVersion.setPixmap(QPixmap(iconArmory).scaled(24,24))
      self.icoSatoshiSWVersion.setPixmap(QPixmap(iconSatoshi).scaled(24,24))

      try:
         armCurrent = verStrToInt(self.armoryVersions[0])
         armLatest  = verStrToInt(self.armoryVersions[1])
         if armCurrent >= armLatest:
            dispIcon = QPixmap(iconArmory).scaled(24,24)
            self.icoArmorySWVersion.setPixmap(dispIcon)
            self.btnSecureDLArmory.setVisible(False)
            self.lblArmorySWVersion.setText(tr("""
               You are using the latest version of Armory"""))
         else:
            dispIcon = QPixmap(iconWarnFile).scaled(24,24)
            self.icoArmorySWVersion.setPixmap(dispIcon)
            self.btnSecureDLArmory.setVisible(True)
            self.lblArmorySWVersion.setText(tr("""
               <b>There is a newer version of Armory available!</b>"""))
         self.btnSecureDLArmory.setVisible(True)
         self.icoArmorySWVersion.setVisible(True)
      except:
         self.btnSecureDLArmory.setVisible(False)
         self.lblArmorySWVersion.setText(tr(""" You are running Armory
            version %s""") % getVersionString(BTCARMORY_VERSION))


      try:
         satCurrStr,satLastStr = self.satoshiVersions
         satCurrent = verStrToInt(satCurrStr) if satCurrStr else 0
         satLatest  = verStrToInt(satLastStr) if satLastStr else 0

      # Show CoreBTC updates
         if satCurrent and satLatest:
            if satCurrent >= satLatest:
               dispIcon = QPixmap(iconGoodFile).scaled(24,24)
               self.btnSecureDLSatoshi.setVisible(False)
               self.icoSatoshiSWVersion.setPixmap(dispIcon)
               self.lblSatoshiSWVersion.setText(tr(""" You are using
                  the latest version of core Bitcoin (%s)""") % satCurrStr)
            else:
               dispIcon = QPixmap(iconWarnFile).scaled(24,24)
               self.btnSecureDLSatoshi.setVisible(True)
               self.icoSatoshiSWVersion.setPixmap(dispIcon)
               self.lblSatoshiSWVersion.setText(tr("""
                  <b>There is a newer version of the core Bitcoin software
                  available!</b>"""))
         elif satCurrent:
            # satLatest is not available
            dispIcon = QPixmap(iconGoodFile).scaled(24,24)
            self.btnSecureDLSatoshi.setVisible(False)
            self.icoSatoshiSWVersion.setPixmap(None)
            self.lblSatoshiSWVersion.setText(tr(""" You are using
               core Bitcoin version %s""") % satCurrStr)
         elif satLatest:
            # only satLatest is avail (maybe offline)
            dispIcon = QPixmap(iconSatoshi).scaled(24,24)
            self.btnSecureDLSatoshi.setVisible(True)
            self.icoSatoshiSWVersion.setPixmap(dispIcon)
            self.lblSatoshiSWVersion.setText(tr("""Core Bitcoin version
               %s is available.""") % satLastStr)
         else:
            # only satLatest is avail (maybe offline)
            dispIcon = QPixmap(iconSatoshi).scaled(24,24)
            self.btnSecureDLSatoshi.setVisible(False)
            self.icoSatoshiSWVersion.setPixmap(dispIcon)
            self.lblSatoshiSWVersion.setText(tr("""No version information
               is available for core Bitcoin""") )




         #self.btnSecureDLSatoshi.setVisible(False)
         #if self.satoshiVersions[0]:
            #self.lblSatoshiSWVersion.setText(tr(""" You are running
               #core Bitcoin software version %s""") % self.satoshiVersions[0])
         #else:
            #self.lblSatoshiSWVersion.setText(tr("""No information is
            #available for the core Bitcoin software"""))
      except:
         LOGEXCEPT('Failed to process satoshi versions')


      self.updateAnnounceTable()


   #############################################################################
   def updateAnnounceTable(self):

      # Default: Make everything non-visible except first row, middle column
      for i in range(10):
         for j in range(3):
            self.announceTableWidgets[i][j].setVisible(i==0 and j==1)

      if len(self.almostFullNotificationList)==0:
         self.announceTableWidgets[0][1].setText(tr("""
            There are no announcements or alerts to display"""))
         return


      alertsForSorting = []
      for nid,nmap in self.almostFullNotificationList.iteritems():
         alertsForSorting.append([nid, int(nmap['PRIORITY'])])

      sortedAlerts = sorted(alertsForSorting, key=lambda a: -a[1])[:10]

      i = 0
      for nid,priority in sortedAlerts:
         if priority>=4096:
            pixm = QPixmap(':/MsgBox_critical64.png')
         elif priority>=3072:
            pixm = QPixmap(':/MsgBox_warning48.png')
         elif priority>=2048:
            pixm = QPixmap(':/MsgBox_info48.png')
         else:
            pixm = QPixmap(':/MsgBox_info48.png')


         shortDescr = self.almostFullNotificationList[nid]['SHORTDESCR']
         if priority>=4096:
            shortDescr = '<font color="%s">' + shortDescr + '</font>'
            shortDescr = shortDescr % htmlColor('TextWarn')

         self.announceTableWidgets[i][0].setPixmap(pixm.scaled(24,24))
         self.announceTableWidgets[i][1].setText(shortDescr)
         self.announceTableWidgets[i][2].setVisible(True)
         self.announceTableWidgets[i][3].setParams(self, nid, \
                                 self.almostFullNotificationList[nid])

         for j in range(3):
            self.announceTableWidgets[i][j].setVisible(True)

         i += 1

   #############################################################################
   def explicitCheckAnnouncements(self, waitTime=3):
      self.announceFetcher.fetchRightNow(waitTime)
      self.processAnnounceData()
      self.updateAnnounceTab()

   #############################################################################
   def closeExistingBitcoin(self):
      for proc in psutil.process_iter():
         if proc.name.lower() in ['bitcoind.exe','bitcoin-qt.exe',\
                                     'bitcoind','bitcoin-qt']:
            killProcess(proc.pid)
            time.sleep(2)
            return

      # If got here, never found it
      QMessageBox.warning(self, 'Not Found', \
         'Attempted to kill the running Bitcoin-Qt/bitcoind instance, '
         'but it was not found.  ', QMessageBox.Ok)

   #############################################################################
   def getPercentageFinished(self, maxblk, lastblk):
      curr = EstimateCumulativeBlockchainSize(lastblk)
      maxb = EstimateCumulativeBlockchainSize(maxblk)
      return float(curr)/float(maxb)

   #############################################################################
   def updateSyncProgress(self):

      if TheTDM.getTDMState()=='Downloading':

         dlSpeed  = TheTDM.getLastStats('downRate')
         timeEst  = TheTDM.getLastStats('timeEst')
         fracDone = TheTDM.getLastStats('fracDone')
         numSeeds = TheTDM.getLastStats('numSeeds')
         numPeers = TheTDM.getLastStats('numPeers')

         self.barProgressTorrent.setVisible(True)
         self.lblDashModeTorrent.setVisible(True)
         self.lblTimeLeftTorrent.setVisible(True)
         self.lblTorrentStats.setVisible(True)
         self.barProgressTorrent.setFormat('%p%')

         self.lblDashModeSync.setVisible(True)
         self.barProgressSync.setVisible(True)
         self.barProgressSync.setValue(0)
         self.lblTimeLeftSync.setVisible(True)
         self.barProgressSync.setFormat('')

         self.lblDashModeBuild.setVisible(True)
         self.barProgressBuild.setVisible(True)
         self.barProgressBuild.setValue(0)
         self.lblTimeLeftBuild.setVisible(True)
         self.barProgressBuild.setFormat('')

         self.lblDashModeScan.setVisible(True)
         self.barProgressScan.setVisible(True)
         self.barProgressScan.setValue(0)
         self.lblTimeLeftScan.setVisible(True)
         self.barProgressScan.setFormat('')

         if not numSeeds:
            self.barProgressTorrent.setValue(0)
            self.lblTimeLeftTorrent.setText('')
            self.lblTorrentStats.setText('')

            self.lblDashModeTorrent.setText(tr('Initializing Torrent Engine'), \
                                          size=4, bold=True, color='Foreground')

            self.lblTorrentStats.setVisible(False)
         else:
            self.lblDashModeTorrent.setText(tr('Downloading via Armory CDN'), \
                                          size=4, bold=True, color='Foreground')

            if fracDone:
               self.barProgressTorrent.setValue(int(99.9*fracDone))

            if timeEst:
               self.lblTimeLeftTorrent.setText(secondsToHumanTime(timeEst))

            self.lblTorrentStats.setText(tr("""
               Bootstrap Torrent:  %s/sec from %d peers""") % \
               (bytesToHumanSize(dlSpeed), numSeeds+numPeers))

            self.lblTorrentStats.setVisible(True)



      elif TheBDM.getBDMState()=='Scanning':
         self.barProgressTorrent.setVisible(TheTDM.isStarted())
         self.lblDashModeTorrent.setVisible(TheTDM.isStarted())
         self.barProgressTorrent.setValue(100)
         self.lblTimeLeftTorrent.setVisible(False)
         self.lblTorrentStats.setVisible(False)
         self.barProgressTorrent.setFormat('')

         self.lblDashModeSync.setVisible(self.doAutoBitcoind)
         self.barProgressSync.setVisible(self.doAutoBitcoind)
         self.barProgressSync.setValue(100)
         self.lblTimeLeftSync.setVisible(False)
         self.barProgressSync.setFormat('')

         self.lblDashModeBuild.setVisible(True)
         self.barProgressBuild.setVisible(True)
         self.lblTimeLeftBuild.setVisible(True)

         self.lblDashModeScan.setVisible(True)
         self.barProgressScan.setVisible(True)
         self.lblTimeLeftScan.setVisible(True)

         # Scan time is super-simple to predict: it's pretty much linear
         # with the number of bytes remaining.

         phase,pct,rate,tleft = TheBDM.predictLoadTime()
         if phase==1:
            self.lblDashModeBuild.setText( 'Building Databases', \
                                        size=4, bold=True, color='Foreground')
            self.lblDashModeScan.setText( 'Scan Transaction History', \
                                        size=4, bold=True, color='DisableFG')
            self.barProgressBuild.setFormat('%p%')
            self.barProgressScan.setFormat('')

         elif phase==3:
            self.lblDashModeBuild.setText( 'Build Databases', \
                                        size=4, bold=True, color='DisableFG')
            self.lblDashModeScan.setText( 'Scanning Transaction History', \
                                        size=4, bold=True, color='Foreground')
            self.lblTimeLeftBuild.setVisible(False)
            self.barProgressBuild.setFormat('')
            self.barProgressBuild.setValue(100)
            self.barProgressScan.setFormat('%p%')
         elif phase==4:
            self.lblDashModeScan.setText( 'Global Blockchain Index', \
                                        size=4, bold=True, color='Foreground')

         tleft15 = (int(tleft-1)/15 + 1)*15
         if tleft < 2:
            tstring = ''
            pvalue  = 100
         else:
            tstring = secondsToHumanTime(tleft15)
            pvalue = pct*100

         if phase==1:
            self.lblTimeLeftBuild.setText(tstring)
            self.barProgressBuild.setValue(pvalue)
         elif phase==3:
            self.lblTimeLeftScan.setText(tstring)
            self.barProgressScan.setValue(pvalue)

      elif TheSDM.getSDMState() in ['BitcoindInitializing','BitcoindSynchronizing']:

         self.barProgressTorrent.setVisible(TheTDM.isStarted())
         self.lblDashModeTorrent.setVisible(TheTDM.isStarted())
         self.barProgressTorrent.setValue(100)
         self.lblTimeLeftTorrent.setVisible(False)
         self.lblTorrentStats.setVisible(False)
         self.barProgressTorrent.setFormat('')

         self.lblDashModeSync.setVisible(True)
         self.barProgressSync.setVisible(True)
         self.lblTimeLeftSync.setVisible(True)
         self.barProgressSync.setFormat('%p%')

         self.lblDashModeBuild.setVisible(True)
         self.barProgressBuild.setVisible(True)
         self.lblTimeLeftBuild.setVisible(False)
         self.barProgressBuild.setValue(0)
         self.barProgressBuild.setFormat('')

         self.lblDashModeScan.setVisible(True)
         self.barProgressScan.setVisible(True)
         self.lblTimeLeftScan.setVisible(False)
         self.barProgressScan.setValue(0)
         self.barProgressScan.setFormat('')

         ssdm = TheSDM.getSDMState()
         lastBlkNum  = self.getSettingOrSetDefault('LastBlkRecv',     0)
         lastBlkTime = self.getSettingOrSetDefault('LastBlkRecvTime', 0)

         # Get data from SDM if it has it
         info = TheSDM.getTopBlockInfo()
         if len(info['tophash'])>0:
            lastBlkNum  = info['numblks']
            lastBlkTime = info['toptime']

         # Use a reference point if we are starting from scratch
         refBlock = max(290746,      lastBlkNum)
         refTime  = max(1394922889,  lastBlkTime)


         # Ten min/block is pretty accurate, even from genesis (about 1% slow)
         # And it gets better as we sync past the reference block above
         self.approxMaxBlock = refBlock + int((RightNow() - refTime) / (10*MINUTE))
         self.approxBlkLeft  = self.approxMaxBlock - lastBlkNum
         self.approxPctSoFar = self.getPercentageFinished(self.approxMaxBlock, \
                                                                  lastBlkNum)

         self.initSyncCircBuff.append([RightNow(), self.approxPctSoFar])
         if len(self.initSyncCircBuff)>30:
            # There's always a couple wacky measurements up front, start at 10
            t0,p0 = self.initSyncCircBuff[10]
            t1,p1 = self.initSyncCircBuff[-1]
            dt,dp = t1-t0, p1-p0
            if dt>600:
               self.initSyncCircBuff = self.initSyncCircBuff[1:]

            if dp>0 and dt>0:
               dpPerSec = dp / dt
               if lastBlkNum < 200000:
                  dpPerSec = dpPerSec / 2
               timeRemain = (1 - self.approxPctSoFar) / dpPerSec
               #timeRemain = min(timeRemain, 8*HOUR)
            else:
               timeRemain = None
         else:
            timeRemain = None


         intPct = int(100*self.approxPctSoFar)
         strPct = '%d%%' % intPct


         self.barProgressSync.setFormat('%p%')
         if ssdm == 'BitcoindReady':
            return (0,0,0.99)  # because it's probably not completely done...
            self.lblTimeLeftSync.setText('Almost Done...')
            self.barProgressSync.setValue(99)
         elif ssdm == 'BitcoindSynchronizing':
            sdmPercent = int(99.9*self.approxPctSoFar)
            if self.approxBlkLeft < 10000:
               if self.approxBlkLeft < 200:
                  self.lblTimeLeftSync.setText('%d blocks' % self.approxBlkLeft)
               else:
                  # If we're within 10k blocks, estimate based on blkspersec
                  if info['blkspersec'] > 0:
                     timeleft = int(self.approxBlkLeft/info['blkspersec'])
                     self.lblTimeLeftSync.setText(secondsToHumanTime(timeleft))
            else:
               # If we're more than 10k blocks behind...
               if timeRemain:
                  timeRemain = min(24*HOUR, timeRemain)
                  self.lblTimeLeftSync.setText(secondsToHumanTime(timeRemain))
               else:
                  self.lblTimeLeftSync.setText('')
         elif ssdm == 'BitcoindInitializing':
            sdmPercent = 0
            self.barProgressSync.setFormat('')
            self.barProgressBuild.setFormat('')
            self.barProgressScan.setFormat('')
         else:
            LOGERROR('Should not predict sync info in non init/sync SDM state')
            return ('UNKNOWN','UNKNOWN', 'UNKNOWN')

         self.barProgressSync.setValue(sdmPercent)
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
         return tr("""
         For more information about Armory, and even Bitcoin itself, you should
         visit the <a href="https://bitcoinarmory.com/faqs/">frequently
         asked questions page</a>.  If
         you are experiencing problems using this software, please visit the
         <a href="https://bitcoinarmory.com/troubleshooting/">Armory
         troubleshooting webpage</a>.  It will be updated frequently with
         solutions to common problems.
         <br><br>
         <b><u>IMPORTANT:</u></b> Make a backup of your wallet(s)!  Paper
         backups protect you <i>forever</i> against forgotten passwords,
         hard-drive failure, and make it easy for your family to recover
         your funds if something terrible happens to you.  <i>Each wallet
         only needs to be backed up once, ever!</i>  Without it, you are at
         risk of losing all of your Bitcoins!  For more information,
         visit the <a href="https://bitcoinarmory.com/armory-backups-are-forever/">Armory
         Backups page</a>.
         <br><br>
         To learn about improving your security through the use of offline
         wallets, visit the
         <a href="https://bitcoinarmory.com/using-our-wallet">Armory
         Quick Start Guide</a>, and the
         <a href="https://bitcoinarmory.com/using-our-wallet/#offlinewallet">Offline
         Wallet Tutorial</a>.<br><br> """)
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
         '<br><br>'  if not self.doAutoBitcoind else '') + (
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
            bitconf = os.path.join(BTC_HOME_DIR, 'bitcoin.conf')
            return ( \
            'You are currently in offline mode because '
            'Bitcoin-Qt is not running.  To switch to online '
            'mode, start Bitcoin-Qt and let it synchronize with the network '
            '-- you will see a green checkmark in the bottom-right corner when '
            'it is complete.  If Bitcoin-Qt is already running and you believe '
            'the lack of connection is an error (especially if using proxies), '
            'please see <a href="'
            'https://bitcointalk.org/index.php?topic=155717.msg1719077#msg1719077">'
            'this link</a> for options.'
            '<br><br>'
            '<b>If you prefer to have Armory do this for you</b>, '
            'then please check "Let Armory run '
            'Bitcoin-Qt in the background" under "File"->"Settings."'
            '<br><br>'
            'If you are new to Armory and/or Bitcoin-Qt, '
            'please visit the Armory '
            'webpage for more information.  Start at '
            '<a href="https://bitcoinarmory.com/armory-and-bitcoin-qt">'
            'Why Armory needs Bitcoin-Qt</a> or go straight to our <a '
            'href="https://bitcoinarmory.com/faqs/">'
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
            'to notify Armory where to find them.') % BLKFILE_DIR
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
            return tr("""
            <b>To maximize your security, the Bitcoin engine is downloading
            and verifying the global transaction ledger.  <u>This will take
            several hours, but only needs to be done once</u>!</b>  It is
            usually best to leave it running over night for this
            initialization process.  Subsequent loads will only take a few
            minutes.
            <br><br>
            <b>Please Note:</b> Between Armory and the underlying Bitcoin
            engine, you need to have 40-50 GB of spare disk space available
            to hold the global transaction history.
            <br><br>
            While you wait, you can manage your wallets.  Make new wallets,
            make digital or paper backups, create Bitcoin addresses to receive
            payments,
            sign messages, and/or import private keys.  You will always
            receive Bitcoin payments regardless of whether you are online,
            but you will have to verify that payment through another service
            until Armory is finished this initialization.""")
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
            '(from the "File" menu) and send it to support@bitcoinarmory.com')
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
         if state == 'OfflineBadDBEnv':
            return ( \
            'The Bitcoin software indicates there '
            'is a problem with its databases.  This can occur when '
            'Bitcoin-Qt/bitcoind is upgraded or downgraded, or sometimes '
            'just by chance after an unclean shutdown.'
            '<br><br>'
            'You can either revert your installed Bitcoin software to the '
            'last known working version (but not earlier than version 0.8.1) '
            'or delete everything <b>except</b> "wallet.dat" from the your Bitcoin '
            'home directory:<br><br>'
            '<font face="courier"><b>%s</b></font>'
            '<br><br>'
            'If you choose to delete the contents of the Bitcoin home '
            'directory, you will have to do a fresh download of the blockchain '
            'again, which will require a few hours the first '
            'time.' % self.satoshiHomePath)
         if state == 'OfflineBtcdCrashed':
            sout = '' if TheSDM.btcOut==None else str(TheSDM.btcOut)
            serr = '' if TheSDM.btcErr==None else str(TheSDM.btcErr)
            soutHtml = '<br><br>' + '<br>'.join(sout.strip().split('\n'))
            serrHtml = '<br><br>' + '<br>'.join(serr.strip().split('\n'))
            soutDisp = '<b><font face="courier">StdOut: %s</font></b>' % soutHtml
            serrDisp = '<b><font face="courier">StdErr: %s</font></b>' % serrHtml
            if len(sout)>0 or len(serr)>0:
               return  (tr("""
               There was an error starting the underlying Bitcoin engine.
               This should not normally happen.  Usually it occurs when you
               have been using Bitcoin-Qt prior to using Armory, especially
               if you have upgraded or downgraded Bitcoin-Qt recently.
               Output from bitcoind:<br>""") + \
               (soutDisp if len(sout)>0 else '') + \
               (serrDisp if len(serr)>0 else '') )
            else:
               return ( tr("""
                  There was an error starting the underlying Bitcoin engine.
                  This should not normally happen.  Usually it occurs when you
                  have been using Bitcoin-Qt prior to using Armory, especially
                  if you have upgraded or downgraded Bitcoin-Qt recently.
                  <br><br>
                  Unfortunately, this error is so strange, Armory does not
                  recognize it.  Please go to "Export Log File" from the "File"
                  menu and email at as an attachment to <a href="mailto:
                  support@bitcoinarmory.com?Subject=Bitcoind%20Crash">
                  support@bitcoinarmory.com</a>.  We apologize for the
                  inconvenience!"""))


   #############################################################################
   @TimeThisFunction
   def setDashboardDetails(self, INIT=False):
      """
      We've dumped all the dashboard text into the above 2 methods in order
      to declutter this method.
      """
      onlineAvail = self.onlineModeIsPossible()

      sdmState = TheSDM.getSDMState()
      bdmState = TheBDM.getBDMState()
      tdmState = TheTDM.getTDMState()
      descr  = ''
      descr1 = ''
      descr2 = ''

      # Methods for showing/hiding groups of widgets on the dashboard
      def setBtnRowVisible(r, visBool):
         for c in range(3):
            self.dashBtns[r][c].setVisible(visBool)

      def setSyncRowVisible(b):
         self.lblDashModeSync.setVisible(b)
         self.barProgressSync.setVisible(b)
         self.lblTimeLeftSync.setVisible(b)


      def setTorrentRowVisible(b):
         self.lblDashModeTorrent.setVisible(b)
         self.barProgressTorrent.setVisible(b)
         self.lblTimeLeftTorrent.setVisible(b)
         self.lblTorrentStats.setVisible(b)

      def setBuildRowVisible(b):
         self.lblDashModeBuild.setVisible(b)
         self.barProgressBuild.setVisible(b)
         self.lblTimeLeftBuild.setVisible(b)

      def setScanRowVisible(b):
         self.lblDashModeScan.setVisible(b)
         self.barProgressScan.setVisible(b)
         self.lblTimeLeftScan.setVisible(b)

      def setOnlyDashModeVisible():
         setTorrentRowVisible(False)
         setSyncRowVisible(False)
         setBuildRowVisible(False)
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
         setBtnRowVisible(DASHBTNS.Install, False)
         setBtnRowVisible(DASHBTNS.Browse, False)
         setBtnRowVisible(DASHBTNS.Instruct, False)
         setBtnRowVisible(DASHBTNS.Settings, False)
         setBtnRowVisible(DASHBTNS.Close, False)
         setOnlyDashModeVisible()
         self.btnModeSwitch.setVisible(False)

      # This keeps popping up for some reason!
      self.lblTorrentStats.setVisible(False)

      if self.doAutoBitcoind and not sdmState=='BitcoindReady':
         # User is letting Armory manage the Satoshi client for them.

         if not sdmState==self.lastSDMState:

            self.lblBusy.setVisible(False)
            self.btnModeSwitch.setVisible(False)

            # There's a whole bunch of stuff that has to be hidden/shown
            # depending on the state... set some reasonable defaults here
            setBtnFrameVisible(False)
            setBtnRowVisible(DASHBTNS.Install, False)
            setBtnRowVisible(DASHBTNS.Browse, False)
            setBtnRowVisible(DASHBTNS.Instruct, False)
            setBtnRowVisible(DASHBTNS.Settings, True)
            setBtnRowVisible(DASHBTNS.Close, False)

            if not (self.forceOnline or self.internetAvail) or CLI_OPTIONS.offline:
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)
               setOnlyDashModeVisible()
               self.lblDashModeSync.setText( 'Armory is <u>offline</u>', \
                                            size=4, color='TextWarn', bold=True)
               if satoshiIsAvailable():
                  self.frmDashMidButtons.setVisible(True)
                  setBtnRowVisible(DASHBTNS.Close, True)
                  if CLI_OPTIONS.offline:
                     # Forced offline but bitcoind is running
                     LOGINFO('Dashboard switched to auto-OfflineForcedButSatoshiAvail')
                     descr1 += self.GetDashStateText('Auto', 'OfflineForcedButSatoshiAvail')
                     descr2 += self.GetDashFunctionalityText('Offline')
                     self.lblDashDescr1.setText(descr1)
                     self.lblDashDescr2.setText(descr2)
                  else:
                     LOGINFO('Dashboard switched to auto-OfflineSatoshiAvail')
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
                  setBtnRowVisible(DASHBTNS.Browse, True)
                  setBtnRowVisible(DASHBTNS.Install, True)
                  setBtnRowVisible(DASHBTNS.Settings, True)
                  #setBtnRowVisible(DASHBTNS.Instruct, not OS_WINDOWS)
                  descr1 += self.GetDashStateText('Auto','OfflineNoSatoshiNoInternet')
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
            elif not TheSDM.isRunningBitcoind() and not TheTDM.isRunning():
               setOnlyDashModeVisible()
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)
               self.lblDashModeSync.setText( 'Armory is <u>offline</u>', \
                                            size=4, color='TextWarn', bold=True)
               # Bitcoind is not being managed, but we want it to be
               if satoshiIsAvailable() or sdmState=='BitcoindAlreadyRunning':
                  # But bitcoind/-qt is already running
                  LOGINFO('Dashboard switched to auto-butSatoshiRunning')
                  self.lblDashModeSync.setText(' Please close Bitcoin-Qt', \
                                                         size=4, bold=True)
                  setBtnFrameVisible(True, '')
                  setBtnRowVisible(DASHBTNS.Close, True)
                  self.btnModeSwitch.setVisible(True)
                  self.btnModeSwitch.setText('Check Again')
                  #setBtnRowVisible(DASHBTNS.Close, True)
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
                  setBtnRowVisible(DASHBTNS.Close, satoshiIsAvailable())
                  setBtnRowVisible(DASHBTNS.Install, True)
                  setBtnRowVisible(DASHBTNS.Browse, True)
                  setBtnRowVisible(DASHBTNS.Settings, True)
                  #setBtnRowVisible(DASHBTNS.Instruct, not OS_WINDOWS)
                  self.btnModeSwitch.setVisible(True)
                  self.btnModeSwitch.setText('Check Again')
                  setBtnFrameVisible(True)
                  descr1 += self.GetDashStateText('Auto', 'OfflineNeedBitcoinInst')
                  descr2 += self.GetDashStateText('Auto', 'NewUserInfo')
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
               elif sdmState in ['BitcoindDatabaseEnvError']:
                  LOGINFO('Dashboard switched to auto-BadDBEnv')
                  setOnlyDashModeVisible()
                  setBtnRowVisible(DASHBTNS.Install, True)
                  #setBtnRowVisible(DASHBTNS.Instruct, not OS_WINDOWS)
                  setBtnRowVisible(DASHBTNS.Settings, True)
                  self.lblDashModeSync.setText( 'Armory is <u>offline</u>', \
                                            size=4, color='TextWarn', bold=True)
                  descr1 += self.GetDashStateText('Auto', 'OfflineBadDBEnv')
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
                  setBtnFrameVisible(True, '')
               elif sdmState in ['BitcoindUnknownCrash']:
                  LOGERROR('Should not usually get here')
                  setOnlyDashModeVisible()
                  setBtnFrameVisible(True, \
                     'Try reinstalling the Bitcoin '
                     'software then restart Armory.  If you continue to have '
                     'problems, please contact Armory\'s core developer at '
                     '<a href="mailto:support@bitcoinarmory.com?Subject=Bitcoind%20Crash"'
                     '>support@bitcoinarmory.com</a>.')
                  setBtnRowVisible(DASHBTNS.Settings, True)
                  setBtnRowVisible(DASHBTNS.Install, True)
                  LOGINFO('Dashboard switched to auto-BtcdCrashed')
                  self.lblDashModeSync.setText( 'Armory is <u>offline</u>', \
                                            size=4, color='TextWarn', bold=True)
                  descr1 += self.GetDashStateText('Auto', 'OfflineBtcdCrashed')
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
                  self.lblDashDescr1.setTextInteractionFlags( \
                                          Qt.TextSelectableByMouse | \
                                          Qt.TextSelectableByKeyboard)
               elif sdmState in ['BitcoindNotAvailable']:
                  LOGERROR('BitcoindNotAvailable: should not happen...')
                  self.notAvailErrorCount += 1
                  #if self.notAvailErrorCount < 5:
                     #LOGERROR('Auto-mode-switch')
                     #self.executeModeSwitch()
                  descr1 += ''
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
               else:
                  setBtnFrameVisible(False)
                  descr1 += ''
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
            else:  # online detected/forced, and TheSDM has already been started
               if sdmState in ['BitcoindWrongPassword', 'BitcoindNotAvailable']:

                  extraTxt = ''
                  if not self.wasSynchronizing:
                     setOnlyDashModeVisible()
                  else:
                     extraTxt = tr("""
                        <b>Armory has lost connection to the
                        core Bitcoin software.  If you did not do anything
                        that affects your network connection or the bitcoind
                        process, it will probably recover on its own in a
                        couple minutes</b><br><br>""")
                     self.lblTimeLeftSync.setVisible(False)
                     self.barProgressSync.setFormat('')


                  self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)
                  LOGINFO('Dashboard switched to auto-BadConnection')
                  self.lblDashModeSync.setText( 'Armory is <u>offline</u>', \
                                            size=4, color='TextWarn', bold=True)
                  descr1 += self.GetDashStateText('Auto', 'OfflineBadConnection')
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(extraTxt + descr1)
                  self.lblDashDescr2.setText(descr2)
               elif sdmState in ['BitcoindInitializing', \
                                 'BitcoindSynchronizing', \
                                 'TorrentSynchronizing']:
                  self.wasSynchronizing = True
                  LOGINFO('Dashboard switched to auto-InitSync')
                  self.lblBusy.setVisible(True)
                  self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)
                  self.updateSyncProgress()


                  # If torrent ever ran, leave it visible
                  setSyncRowVisible(True)
                  setScanRowVisible(True)
                  setTorrentRowVisible(TheTDM.isStarted())

                  if TheTDM.isRunning():
                     self.lblDashModeTorrent.setText('Downloading via Armory CDN', \
                                          size=4, bold=True, color='Foreground')
                     self.lblDashModeSync.setText( 'Synchronizing with Network', \
                                          size=4, bold=True, color='DisableFG')
                     self.lblTorrentStats.setVisible(True)
                  elif sdmState=='BitcoindInitializing':
                     self.lblDashModeTorrent.setText('Download via Armory CDN', \
                                          size=4, bold=True, color='DisableFG')
                     self.lblDashModeSync.setText( 'Initializing Bitcoin Engine', \
                                              size=4, bold=True, color='Foreground')
                     self.lblTorrentStats.setVisible(False)
                  else:
                     self.lblDashModeTorrent.setText('Download via Armory CDN', \
                                          size=4, bold=True, color='DisableFG')
                     self.lblDashModeSync.setText( 'Synchronizing with Network', \
                                              size=4, bold=True, color='Foreground')
                     self.lblTorrentStats.setVisible(False)


                  self.lblDashModeBuild.setText( 'Build Databases', \
                                              size=4, bold=True, color='DisableFG')
                  self.lblDashModeScan.setText( 'Scan Transaction History', \
                                              size=4, bold=True, color='DisableFG')

                  # If more than 10 days behind, or still downloading torrent
                  if tdmState=='Downloading' or self.approxBlkLeft > 1440:
                     descr1 += self.GetDashStateText('Auto', 'InitializingLongTime')
                     descr2 += self.GetDashStateText('Auto', 'NewUserInfo')
                  else:
                     descr1 += self.GetDashStateText('Auto', 'InitializingDoneSoon')
                     descr2 += self.GetDashStateText('Auto', 'NewUserInfo')

                  setBtnRowVisible(DASHBTNS.Settings, True)
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
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)
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
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)
               setOnlyDashModeVisible()
               self.lblBusy.setVisible(False)
               self.btnModeSwitch.setVisible(False)
               self.btnModeSwitch.setEnabled(False)
               self.lblDashModeSync.setText( 'Armory is <u>offline</u>', \
                                         size=4, color='TextWarn', bold=True)

               if not satoshiIsAvailable():
                  if self.internetAvail:
                     descr = self.GetDashStateText('User','OfflineNoSatoshi')
                     setBtnRowVisible(DASHBTNS.Settings, True)
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
            self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, True)
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
               self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Dash)
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
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, True)
               descr  = self.GetDashStateText('User', 'OnlineFull1')
               descr += self.GetDashFunctionalityText('Online')
               descr += self.GetDashStateText('User', 'OnlineFull2')
               self.lblDashDescr1.setText(descr)
            #self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Dash)
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

            if len(str(self.lblDashModeBuild.text()).strip()) == 0:
               self.lblDashModeBuild.setText( 'Preparing Databases', \
                                          size=4, bold=True, color='Foreground')

            if len(str(self.lblDashModeScan.text()).strip()) == 0:
               self.lblDashModeScan.setText( 'Scan Transaction History', \
                                          size=4, bold=True, color='DisableFG')

            self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)

            if len(self.walletMap)==0:
               descr = self.GetDashStateText('User','ScanNoWallets')
            else:
               descr = self.GetDashStateText('User','ScanWithWallets')

            descr += self.GetDashStateText('Auto', 'NewUserInfo')
            descr += self.GetDashFunctionalityText('Scanning') + '<br>'
            self.lblDashDescr1.setText(descr)
            self.lblDashDescr2.setText('')
            self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Dash)
         else:
            LOGERROR('What the heck blockchain mode are we in?  %s', bdmState)

      self.lastBDMState = [bdmState, onlineAvail]
      self.lastSDMState =  sdmState
      self.lblDashModeTorrent.setContentsMargins( 50,5,50,5)
      self.lblDashModeSync.setContentsMargins( 50,5,50,5)
      self.lblDashModeBuild.setContentsMargins(50,5,50,5)
      self.lblDashModeScan.setContentsMargins( 50,5,50,5)
      vbar = self.dashScrollArea.verticalScrollBar()

      # On Macs, this causes the main window scroll area to keep bouncing back
      # to the top. Not setting the value seems to fix it. DR - 2014/02/12
      if not OS_MACOSX:
         vbar.setValue(vbar.minimum())

   #############################################################################
   def createToolTipWidget(self, tiptext, iconSz=2):
      """
      The <u></u> is to signal to Qt that it should be interpretted as HTML/Rich
      text even if no HTML tags are used.  This appears to be necessary for Qt
      to wrap the tooltip text
      """
      fgColor = htmlColor('ToolTipQ')
      lbl = QLabel('<font size=%d color=%s>(?)</font>' % (iconSz, fgColor))
      lbl.setMaximumWidth(relaxedSizeStr(lbl, '(?)')[0])

      def setAllText(wself, txt):
         def pressEv(ev):
            QWhatsThis.showText(ev.globalPos(), txt, self)
         wself.mousePressEvent = pressEv
         wself.setToolTip('<u></u>' + txt)
         
      # Calling setText on this widget will update both the tooltip and QWT
      from types import MethodType
      lbl.setText = MethodType(setAllText, lbl)

      lbl.setText(tiptext)
      return lbl

   #############################################################################
   def createAddressEntryWidgets(self, parent, initString='', maxDetectLen=128,
                                           boldDetectParts=0, **cabbKWArgs):
      """
      If you are putting the LBL_DETECT somewhere that is space-constrained,
      set maxDetectLen to a smaller value.  It will limit the number of chars
      to be included in the autodetect label.

      "cabbKWArgs" is "create address book button kwargs"
      Here's the signature of that function... you can pass any named args
      to this function and they will be passed along to createAddrBookButton
         def createAddrBookButton(parent, targWidget, defaultWltID=None, 
                                  actionStr="Select", selectExistingOnly=False, 
                                  selectMineOnly=False, getPubKey=False,
                                  showLockboxes=True)

      Returns three widgets that can be put into layouts:
         [[QLineEdit: addr/pubkey]]  [[Button: Addrbook]]
         [[Label: Wallet/Lockbox/Addr autodetect]]
      """

      addrEntryObjs = {}
      addrEntryObjs['QLE_ADDR'] = QLineEdit()
      addrEntryObjs['QLE_ADDR'].setText(initString)
      addrEntryObjs['BTN_BOOK']  = createAddrBookButton(parent, 
                                                        addrEntryObjs['QLE_ADDR'], 
                                                        **cabbKWArgs)
      addrEntryObjs['LBL_DETECT'] = QRichLabel('')
      addrEntryObjs['CALLBACK_GETSCRIPT'] = None

      ##########################################################################
      # Create a function that reads the user string and updates labels if 
      # the entry is recognized.  This will be used to automatically show the
      # user that what they entered is recognized and gives them more info
      # 
      # It's a little awkward to put this whole thing in here... this could
      # probably use some refactoring
      def updateAddrDetectLabels():
         try:
            enteredText = str(addrEntryObjs['QLE_ADDR'].text()).strip()

            scriptInfo = self.getScriptForUserString(enteredText)
            displayInfo = self.getDisplayStringForScript(
                           scriptInfo['Script'], maxDetectLen, boldDetectParts,
                           prefIDOverAddr=scriptInfo['ShowID'])

            dispStr = displayInfo['String']
            if displayInfo['WltID'] is None and displayInfo['LboxID'] is None:
               addrEntryObjs['LBL_DETECT'].setText(dispStr)
            else:
               addrEntryObjs['LBL_DETECT'].setText(dispStr, color='TextBlue')

            # No point in repeating what the user just entered
            addrEntryObjs['LBL_DETECT'].setVisible(enteredText != dispStr)
            addrEntryObjs['QLE_ADDR'].setCursorPosition(0)

         except:
            #LOGEXCEPT('Invalid recipient string')
            addrEntryObjs['LBL_DETECT'].setVisible(False)
            addrEntryObjs['LBL_DETECT'].setVisible(False)
      # End function to be connected
      ##########################################################################
            
      # Now actually connect the entry widgets
      parent.connect(addrEntryObjs['QLE_ADDR'], SIGNAL('textChanged(QString)'), 
                                                         updateAddrDetectLabels)

      updateAddrDetectLabels()

      # Create a func that can be called to get the script that was entered
      # This uses getScriptForUserString() which actually returns 4 vals
      #        rawScript, wltIDorNone, lboxIDorNone, addrStringEntered
      # (The last one is really only used to determine what info is most 
      #  relevant to display to the user...it can be ignored in most cases)
      def getScript():
         entered = str(addrEntryObjs['QLE_ADDR'].text()).strip()
         return self.getScriptForUserString(entered)

      addrEntryObjs['CALLBACK_GETSCRIPT'] = getScript
      return addrEntryObjs



   #############################################################################
   def getScriptForUserString(self, userStr):
      return getScriptForUserString(userStr, self.walletMap, self.allLockboxes)


   #############################################################################
   def getDisplayStringForScript(self, binScript, maxChars=256, 
                                 doBold=0, prefIDOverAddr=False, 
                                 lblTrunc=12, lastTrunc=12):
      return getDisplayStringForScript(binScript, self.walletMap, 
                                       self.allLockboxes, maxChars, doBold,
                                       prefIDOverAddr, lblTrunc, lastTrunc) 


   #############################################################################
   @TimeThisFunction
   def checkNewZeroConf(self):
      '''
      Function that looks at an incoming zero-confirmation transaction queue and
      determines if any incoming transactions were created by Armory. If so, the
      transaction will be passed along to a user notification queue.
      '''
      while len(self.newZeroConfSinceLastUpdate)>0:
         rawTx = self.newZeroConfSinceLastUpdate.pop()

         # Iterate through the Python wallets and create a ledger entry for the
         # transaction. If the transaction is for us, put it on the notification
         # queue, create the combined ledger, and reset the Qt table model.
         for wltID in self.walletMap.keys():
            wlt = self.walletMap[wltID]
            le = wlt.cppWallet.calcLedgerEntryForTxStr(rawTx)
            if not le.getTxHash() == '\x00' * 32:
               LOGDEBUG('ZerConf tx for wallet: %s.  Adding to notify queue.' \
                        % wltID)
               notifyIn = self.getSettingOrSetDefault('NotifyBtcIn', \
                                                      not OS_MACOSX)
               notifyOut = self.getSettingOrSetDefault('NotifyBtcOut', \
                                                       not OS_MACOSX)
               if (le.getValue() <= 0 and notifyOut) or \
                  (le.getValue() > 0 and notifyIn):
                  # notifiedAlready = False, 
                  self.notifyQueue.append([wltID, le, False])
               self.createCombinedLedger()
               self.walletModel.reset()

         # Iterate through the C++ lockbox wallets and create a ledger entry for
         # the transaction. If the transaction is for us, put it on the
         # notification queue, create the combined ledger, and reset the Qt
         # table models.
         for lbID,cppWlt in self.cppLockboxWltMap.iteritems():
            le = cppWlt.calcLedgerEntryForTxStr(rawTx)
            if not le.getTxHash() == '\x00' * 32:
               LOGDEBUG('ZerConf tx for LOCKBOX: %s' % lbID)
               # notifiedAlready = False, 
               self.notifyQueue.append([lbID, le, False])
               self.createCombinedLedger()
               self.walletModel.reset()
               self.lockboxLedgModel.reset()


   #############################################################################
   #############################################################################
   def Heartbeat(self, nextBeatSec=1):
      """
      This method is invoked when the app is initialized, and will
      run every second, or whatever is specified in the nextBeatSec
      argument.
      """

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
            LOGEXCEPT('Error in special heartbeat function')
            self.extraHeartbeatSpecial = []
            reactor.callLater(1, self.Heartbeat)
         return


      # TorrentDownloadManager
      # SatoshiDaemonManager
      # BlockDataManager
      tdmState = TheTDM.getTDMState()
      sdmState = TheSDM.getSDMState()
      bdmState = TheBDM.getBDMState()
      #print '(SDM, BDM) State = (%s, %s)' % (sdmState, bdmState)

      self.processAnnounceData()

      try:
         for func in self.extraHeartbeatAlways:
            if isinstance(func, list):
               fnc = func[0]
               kargs = func[1]
               keep_running = func[2]
               if keep_running == False:
                  self.extraHeartbeatAlways.remove(func)
               fnc(*kargs)
            else:
               func()

         for idx,wltID in enumerate(self.walletIDList):
            self.walletMap[wltID].checkWalletLockTimeout()




         if self.doAutoBitcoind:
            if TheTDM.isRunning():
               if tdmState=='Downloading':
                  self.updateSyncProgress()

               downRate  = TheTDM.getLastStats('downRate')
               self.torrentCircBuffer.append(downRate if downRate else 0)

               # Assumes 1 sec heartbeat
               bufsz = len(self.torrentCircBuffer)
               if bufsz > 5*MINUTE:
                  self.torrentCircBuffer = self.torrentCircBuffer[1:]

               if bufsz >= 4.99*MINUTE:
                  # If dlrate is below 30 kB/s, offer the user a way to skip it
                  avgDownRate = sum(self.torrentCircBuffer) / float(bufsz)
                  if avgDownRate < 30*KILOBYTE:
                     if (RightNow() - self.lastAskedUserStopTorrent) > 5*MINUTE:
                        self.lastAskedUserStopTorrent = RightNow()
                        reply = QMessageBox.warning(self, tr('Torrent'), tr("""
                           Armory is attempting to use BitTorrent to speed up
                           the initial synchronization, but it appears to be
                           downloading slowly or not at all.  
                           <br><br>
                           If the torrent engine is not starting properly,
                           or is not downloading
                           at a reasonable speed for your internet connection, 
                           you should disable it in
                           <i>File\xe2\x86\x92Settings</i> and then
                           restart Armory."""), QMessageBox.Ok)

                        # For now, just show once then disable
                        self.lastAskedUserStopTorrent = UINT64_MAX

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

            if not sdmState==self.lastSDMState or \
               not bdmState==self.lastBDMState[0]:
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
               LOGDEBUG('Running finishLoadBlockchainGUI')
               self.finishLoadBlockchainGUI()
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
                  LOGDEBUG('Registering %s wallet' % ('NEW' if isFresh else 'IMPORTED'))
                  TheBDM.registerWallet(wlt.cppWallet, isFresh)
                  self.addWalletToApplication(wlt, walletIsNew=isFresh)
               self.setDashboardDetails()

   
            # If there's a new block, use this to determine it affected our wallets
            prevLedgSize = dict([(wltID, len(self.walletMap[wltID].getTxLedger())) \
                                                for wltID in self.walletMap.keys()])


            # Now we start the normal array of heartbeat operations
            newBlocks = TheBDM.readBlkFileUpdate(wait=True)
            self.currBlockNum = TheBDM.getTopBlockHeight()
            if isinstance(self.currBlockNum, int): BDMcurrentBlock[0] = self.currBlockNum

            if not newBlocks:
               newBlocks = 0


            # If we have new zero-conf transactions, scan them and update ledger
            if len(self.newZeroConfSinceLastUpdate)>0:
               self.newZeroConfSinceLastUpdate.reverse()
               for wltID in self.walletMap.keys():
                  wlt = self.walletMap[wltID]
                  TheBDM.rescanWalletZeroConf(wlt.cppWallet, wait=True)

               for lbID,cppWlt in self.cppLockboxWltMap.iteritems():
                  TheBDM.rescanWalletZeroConf(cppWlt, wait=True)
                  

            self.checkNewZeroConf()

            # Trigger any notifications, if we have them...
            self.doTheSystemTrayThing()

            if newBlocks>0 and not TheBDM.isDirty():

               # This says "after scan", but works when new blocks appear, too
               TheBDM.updateWalletsAfterScan(wait=True)

               self.ledgerModel.reset()

               LOGINFO('New Block! : %d', self.currBlockNum)
               didAffectUs = False

               # LITE sync means it won't rescan if addresses have been imported
               didAffectUs = newBlockSyncRescanZC(TheBDM, self.walletMap, \
                                                  prevLedgSize)

               if didAffectUs:
                  LOGINFO('New Block contained a transaction relevant to us!')
                  self.walletListChanged()
                  notifyOnSurpriseTx(self.currBlockNum-newBlocks, \
                                     self.currBlockNum+1, self.walletMap, \
                                     self.cppLockboxWltMap, True, TheBDM, \
                                     self.notifyQueue, self.settings)

               self.createCombinedLedger()
               self.blkReceived  = RightNow()
               self.writeSetting('LastBlkRecvTime', self.blkReceived)
               self.writeSetting('LastBlkRecv',     self.currBlockNum)

               if self.netMode==NETWORKMODE.Full:
                  LOGINFO('Current block number: %d', self.currBlockNum)
                  self.lblArmoryStatus.setText(\
                     '<font color=%s>Connected (%s blocks)</font> ' % \
                     (htmlColor('TextGreen'), self.currBlockNum))


               # Update the wallet view to immediately reflect new balances
               self.walletModel.reset()

               # Any extra functions that may have been injected to be run
               # when new blocks are received.  
               if len(self.extraNewBlockFunctions) > 0:
                  cppHead = TheBDM.getMainBlockFromDB(self.currBlockNum)
                  pyBlock = PyBlock().unserialize(cppHead.getSerializedBlock())
                  for blockFunc in self.extraNewBlockFunctions:
                     blockFunc(pyBlock)


            blkRecvAgo  = RightNow() - self.blkReceived
            #blkStampAgo = RightNow() - TheBDM.getTopBlockHeader().getTimestamp()
            self.lblArmoryStatus.setToolTip('Last block received is %s ago' % \
                                                secondsToHumanTime(blkRecvAgo))


            for func in self.extraHeartbeatOnline:
               func()

      except:
         # When getting the error info, don't collect the traceback in order to
         # avoid circular references. https://docs.python.org/2/library/sys.html
         # has more info.
         LOGEXCEPT('Error in heartbeat function')
         (errType, errVal) = sys.exc_info()[:2]
         errStr = 'Error Type: %s\nError Value: %s' % (errType, errVal)
         LOGERROR(errStr)
      finally:
         reactor.callLater(nextBeatSec, self.Heartbeat)


   #############################################################################
   def printAlert(self, moneyID, ledgerAmt, txAmt):
      '''
      Function that prints a notification for a transaction that affects an
      address we control.
      '''
      dispLines = []
      title = ''
      totalStr = coin2strNZS(txAmt)


      if moneyID in self.walletMap:
         wlt = self.walletMap[moneyID]
         if len(wlt.labelName) <= 20:
            dispName = '"%s"' % wlt.labelName
         else:
            dispName = '"%s..."' % wlt.labelName[:17]
         dispName = 'Wallet %s (%s)' % (dispName, wlt.uniqueIDB58)
      elif moneyID in self.cppLockboxWltMap:
         lbox = self.getLockboxByID(moneyID)
         if len(lbox.shortName) <= 20:
            dispName = '%d-of-%d "%s"' % (lbox.M, lbox.N, lbox.shortName)
         else:
            dispName = '%d-of-%d "%s..."' % (lbox.M, lbox.N, lbox.shortName[:17])
         dispName = 'Lockbox %s (%s)' % (dispName, lbox.uniqueIDB58)
      else:
         LOGERROR('Asked to show notification for wlt/lbox we do not have')
         return

      # Collected everything we need to display, now construct it and do it.
      if ledgerAmt > 0:
         # Received!
         title = 'Bitcoins Received!'
         dispLines.append('Amount:  %s BTC' % totalStr)
         dispLines.append('Recipient:  %s' % dispName)
      elif ledgerAmt < 0:
         # Sent!
         title = 'Bitcoins Sent!'
         dispLines.append('Amount:  %s BTC' % totalStr)
         dispLines.append('Sender:  %s' % dispName)

      self.sysTray.showMessage(title, \
                               '\n'.join(dispLines),  \
                               QSystemTrayIcon.Information, \
                               10000)
      LOGINFO(title)


   #############################################################################
   @TimeThisFunction
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

      # Notify queue input is: [WltID/LBID, LedgerEntry, alreadyNotified]
      for i in range(len(self.notifyQueue)):
         moneyID, le, alreadyNotified = self.notifyQueue[i]

         # Skip the ones we've notified of already.
         if alreadyNotified:
            continue

         # Marke it alreadyNotified=True
         self.notifyQueue[i][2] = True

         # Catch condition that somehow the tx isn't related to us
         if le.getTxHash()=='\x00'*32:
            continue

         # Make sure the wallet ID or lockbox ID keys are actually valid before
         # using them to grab the appropriate C++ wallet.
         pywlt = self.walletMap.get(moneyID)
         lbox  = self.getLockboxByID(moneyID)

         # If we couldn't find a matching wallet or lbox, bail
         if pywlt is None and lbox is None:
            LOGERROR('Could not find moneyID = %s; skipping notify' % moneyID)
            continue

         
         if pywlt:
            cppWlt  = self.walletMap[moneyID].cppWallet
            wname = self.walletMap[moneyID].labelName
            if len(wname)>20:
               wname = wname[:17] + '...'
            wltName = 'Wallet "%s" (%s)' % (wname, moneyID)
         else:
            cppWlt = self.cppLockboxWltMap[moneyID]
            lbox   = self.getLockboxByID(moneyID)
            M      = self.getLockboxByID(moneyID).M
            N      = self.getLockboxByID(moneyID).N
            lname  = self.getLockboxByID(moneyID).shortName
            if len(lname) > 20:
               lname = lname[:17] + '...'
            wltName = 'Lockbox %d-of-%d "%s" (%s)' % (M, N, lname, moneyID)


         if le.isSentToSelf():
            # Used to display the sent-to-self amount, but if this is a lockbox
            # we only have a cppWallet, and the determineSentToSelfAmt() func
            # only operates on python wallets.  Oh well, the user can double-
            # click on the tx in their ledger if they want to see what's in it.
            # amt = determineSentToSelfAmt(le, cppWlt)[0]
            # self.sysTray.showMessage('Your bitcoins just did a lap!', \
            #                  'Wallet "%s" (%s) just sent %s BTC to itself!' % \
            #         (wlt.labelName, moneyID, coin2str(amt,maxZeros=1).strip()),
            self.sysTray.showMessage('Your bitcoins just did a lap!', \
                              '%s just sent some BTC to itself!' % wltName, 
                              QSystemTrayIcon.Information, 10000)
            return


         # If coins were either received or sent from the loaded wlt/lbox         
         dispLines = []
         totalStr = coin2strNZS(abs(le.getValue()))
         if le.getValue() > 0:
            title = 'Bitcoins Received!'
            dispLines.append('Amount:  %s BTC' % totalStr)
            dispLines.append('Recipient:  %s' % wltName)
         elif le.getValue() < 0:
            # Also display the address of where they went
            txref = TheBDM.getTxByHash(le.getTxHash())
            nOut = txref.getNumTxOut()
            recipStr = ''
            for i in range(nOut):
               script = txref.getTxOutCopy(i).getScript()
               if cppWlt.hasScrAddress(script_to_scrAddr(script)):
                  continue
               if len(recipStr)==0:
                  recipStr = self.getDisplayStringForScript(script, 45)['String']
               else:
                  recipStr = '<Multiple Recipients>'
            
            title = 'Bitcoins Sent!'
            dispLines.append('Amount:  %s BTC' % totalStr)
            dispLines.append('From:    %s' % wltName)
            dispLines.append('To:      %s' % recipStr)
   
         self.sysTray.showMessage(title, '\n'.join(dispLines), 
                                 QSystemTrayIcon.Information, 10000)
         LOGINFO(title + '\n' + '\n'.join(dispLines))

         # Wait for 5 seconds before processing the next queue object.
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
         self.sysTray.hide()
         self.closeForReal(event)
      else:
         return  # how would we get here?



   #############################################################################
   def unpackLinuxTarGz(self, targzFile, changeSettings=True):
      if targzFile is None:
         return None

      if not os.path.exists(targzFile):
         return None

      unpackDir  = os.path.join(ARMORY_HOME_DIR, 'latestBitcoinInst')
      unpackDir2 = os.path.join(ARMORY_HOME_DIR, 'latestBitcoinInstOld')
      if os.path.exists(unpackDir):
         if os.path.exists(unpackDir2):
            shutil.rmtree(unpackDir2)
         shutil.move(unpackDir, unpackDir2)

      os.mkdir(unpackDir)

      out,err = execAndWait('tar -zxf %s -C %s' % (targzFile, unpackDir), \
                                                                  timeout=5)

      LOGINFO('UNPACK STDOUT: "' + out + '"')
      LOGINFO('UNPACK STDERR: "' + err + '"')

      
      # There should only be one subdir
      unpackDirChild = None
      for fn in os.listdir(unpackDir):
         unpackDirChild = os.path.join(unpackDir, fn)

      if unpackDirChild is None:
         LOGERROR('There was apparently an error unpacking the file')
         return None

      finalDir = os.path.abspath(unpackDirChild)
      LOGWARN('Bitcoin Core unpacked into: %s', finalDir)

      if changeSettings:
         self.settings.set('SatoshiExe', finalDir)

      return finalDir
      


   #############################################################################
   def closeForReal(self, event=None):
      '''
      Unlike File->Quit or clicking the X on the window, which may actually
      minimize Armory, this method is for *really* closing Armory
      '''
      try:
         # Save the main window geometry in the settings file
         self.writeSetting('MainGeometry',   str(self.saveGeometry().toHex()))
         self.writeSetting('MainWalletCols', saveTableView(self.walletsView))
         self.writeSetting('MainLedgerCols', saveTableView(self.ledgerView))

         if TheBDM.getBDMState()=='Scanning':
            LOGINFO('BDM state is scanning -- force shutdown BDM')
            TheBDM.execCleanShutdown(wait=False)
         else:
            LOGINFO('BDM is safe for clean shutdown')
            TheBDM.execCleanShutdown(wait=True)

         # This will do nothing if bitcoind isn't running.
         TheSDM.stopBitcoind()
      except:
         # Don't want a strange error here interrupt shutdown
         LOGEXCEPT('Strange error during shutdown')


      # Any extra shutdown activities, perhaps added by modules
      for fn in self.extraShutdownFunctions:
         try:
            fn()
         except:
            LOGEXCEPT('Shutdown function failed.  Skipping.')


      from twisted.internet import reactor
      LOGINFO('Attempting to close the main window!')
      reactor.stop()
      if event:
         event.accept()



   #############################################################################
   def execTrigger(self, toSpawn):
      super(ArmoryDialog, toSpawn).exec_()


   #############################################################################
   def initTrigger(self, toInit):
      if isinstance(toInit, DlgProgress):
         toInit.setup(self)
         toInit.status = 1


   #############################################################################
   def checkForNegImports(self):
      
      negativeImports = []
      
      for wlt in self.walletMap:
         if self.walletMap[wlt].hasNegativeImports:
            negativeImports.append(self.walletMap[wlt].uniqueIDB58)
            
      # If we detect any negative import
      if len(negativeImports) > 0:
         logDirs = []
         for wltID in negativeImports:
            if not wltID in self.walletMap:
               continue

            homedir = os.path.dirname(self.walletMap[wltID].walletPath)
            wltlogdir  = os.path.join(homedir, wltID)
            if not os.path.exists(wltlogdir):
               continue
   
            for subdirname in os.listdir(wltlogdir):
               subdirpath = os.path.join(wltlogdir, subdirname)
               logDirs.append([wltID, subdirpath])

         
         DlgInconsistentWltReport(self, self, logDirs).exec_()


   #############################################################################
   def getAllRecoveryLogDirs(self, wltIDList):
      self.logDirs = []
      for wltID in wltIDList:
         if not wltID in self.walletMap:
            continue

         homedir = os.path.dirname(self.walletMap[wltID].walletPath)
         logdir  = os.path.join(homedir, wltID)
         if not os.path.exists(logdir):
            continue

         self.logDirs.append([wltID, logdir])

      return self.logDirs 

      
   #############################################################################
   @AllowAsync
   def CheckWalletConsistency(self, wallets, prgAt=None):

      if prgAt:
         totalSize = 0
         walletSize = {}
         for wlt in wallets:
            statinfo = os.stat(wallets[wlt].walletPath)
            walletSize[wlt] = statinfo.st_size
            totalSize = totalSize + statinfo.st_size

      i=0
      dlgrdy = [0]
      nerrors = 0

      for wlt in wallets:
         if prgAt:
            prgAt[0] = i
            f = 10000*walletSize[wlt]/totalSize
            prgAt[1] = f
            i = f +i

         self.wltCstStatus = WalletConsistencyCheck(wallets[wlt], prgAt)
         if self.wltCstStatus[0] != 0:
            self.WltCstError(wallets[wlt], self.wltCstStatus[1], dlgrdy)
            while not dlgrdy[0]:
               time.sleep(0.01)
            nerrors = nerrors +1

      prgAt[2] = 1

      dlgrdy[0] = 0
      while prgAt[2] != 2:
         time.sleep(0.1)
      if nerrors == 0:
         self.emit(SIGNAL('UWCS'), [1, 'All wallets are consistent', 10000, dlgrdy])
         self.emit(SIGNAL('checkForNegImports'))
      else:
         while not dlgrdy:
            self.emit(SIGNAL('UWCS'), [1, 'Consistency Check Failed!', 0, dlgrdy])
            time.sleep(1)

         self.checkRdyForFix()


   def checkRdyForFix(self):
      #check BDM first
      time.sleep(1)
      self.dlgCptWlt.emit(SIGNAL('Show'))
      while 1:
         if TheBDM.getBDMState() == 'Scanning':
            canFix = tr("""
               The wallet analysis tool will become available
               as soon as Armory is done loading.   You can close this 
               window and it will reappear when ready.""")
            self.dlgCptWlt.UpdateCanFix([canFix])
            time.sleep(1)
         elif TheBDM.getBDMState() == 'Offline' or \
              TheBDM.getBDMState() == 'Uninitialized':
            TheSDM.setDisabled(True)
            CLI_OPTIONS.offline = True
            break
         else:
            break

      #check running dialogs
      self.dlgCptWlt.emit(SIGNAL('Show'))
      runningList = []
      while 1:
         listchanged = 0
         canFix = []
         for dlg in runningList:
            if dlg not in runningDialogsList:
               runningList.remove(dlg)
               listchanged = 1

         for dlg in runningDialogsList:
            if not isinstance(dlg, DlgCorruptWallet):
               if dlg not in runningList:
                  runningList.append(dlg)
                  listchanged = 1

         if len(runningList):
            if listchanged:
               canFix.append(tr("""
                  <b>The following windows need closed before you can 
                  run the wallet analysis tool:</b>"""))
               canFix.extend([str(myobj.windowTitle()) for myobj in runningList])
               self.dlgCptWlt.UpdateCanFix(canFix)
            time.sleep(0.2)
         else:
            break


      canFix.append('Ready to analyze inconsistent wallets!')
      self.dlgCptWlt.UpdateCanFix(canFix, True)
      self.dlgCptWlt.exec_()

   def checkWallets(self):
      nwallets = len(self.walletMap)

      if nwallets > 0:
         self.prgAt = [0, 0, 0]

         self.pbarWalletProgress = QProgressBar()
         self.pbarWalletProgress.setMaximum(10000)
         self.pbarWalletProgress.setMaximumSize(300, 22)
         self.pbarWalletProgress.setStyleSheet('text-align: center; margin-bottom: 2px; margin-left: 10px;')
         self.pbarWalletProgress.setFormat('Wallet Consistency Check: %p%')
         self.pbarWalletProgress.setValue(0)
         self.statusBar().addWidget(self.pbarWalletProgress)

         self.connect(self, SIGNAL('UWCS'), self.UpdateWalletConsistencyStatus)
         self.connect(self, SIGNAL('PWCE'), self.PromptWltCstError)
         self.CheckWalletConsistency(self.walletMap, self.prgAt, async=True)
         self.UpdateConsistencyCheckMessage(async = True)
         #self.extraHeartbeatAlways.append(self.UpdateWalletConsistencyPBar)

   @AllowAsync
   def UpdateConsistencyCheckMessage(self):
      while self.prgAt[2] == 0:
         self.emit(SIGNAL('UWCS'), [0, self.prgAt[0]])
         time.sleep(0.5)

      self.emit(SIGNAL('UWCS'), [2])
      self.prgAt[2] = 2

   def UpdateWalletConsistencyStatus(self, msg):
      if msg[0] == 0:
         self.pbarWalletProgress.setValue(msg[1])
      elif msg[0] == 1:
         self.statusBar().showMessage(msg[1], msg[2])
         msg[3][0] = 1
      else:
         self.pbarWalletProgress.hide()

   def WltCstError(self, wlt, status, dlgrdy):
      self.emit(SIGNAL('PWCE'), dlgrdy, wlt, status)
      LOGERROR('Wallet consistency check failed! (%s)', wlt.uniqueIDB58)

   def PromptWltCstError(self, dlgrdy, wallet=None, status='', mode=None):
      if not self.dlgCptWlt:
         self.dlgCptWlt = DlgCorruptWallet(wallet, status, self, self)
         dlgrdy[0] = 1
      else:
         self.dlgCptWlt.addStatus(wallet, status)

      if not mode:
         self.dlgCptWlt.show()
      else:
         self.dlgCptWlt.exec_()


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
      sock = socket.create_connection(('127.0.0.1',CLI_OPTIONS.interport), 0.1);
      # If we got here (no error), there's already another Armory open

      if OS_WINDOWS:
         # Windows can be tricky, sometimes holds sockets even after closing
         checkForAlreadyOpenError()

      LOGERROR('Socket already in use.  Sending CLI args to existing proc.')
      if CLI_ARGS:
         sock.send(CLI_ARGS[0])
      sock.close()
      LOGERROR('Exiting...')
      os._exit(0)
   except:
      # This is actually the normal condition:  we expect this to be the
      # first/only instance of Armory and opening the socket will err out
      pass



############################################
def checkForAlreadyOpenError():
   LOGINFO('Already open error checking')
   # Sometimes in Windows, Armory actually isn't open, because it holds
   # onto the socket even after it's closed.
   armoryExists = []
   bitcoindExists = []
   aexe = os.path.basename(sys.argv[0])
   bexe = 'bitcoind.exe' if OS_WINDOWS else 'bitcoind'
   for proc in psutil.process_iter():
      if aexe in proc.name:
         LOGINFO('Found armory PID: %d', proc.pid)
         armoryExists.append(proc.pid)
      if bexe in proc.name:
         LOGINFO('Found bitcoind PID: %d', proc.pid)
         if ('testnet' in proc.name) == USE_TESTNET:
            bitcoindExists.append(proc.pid)

   if len(armoryExists)>0:
      LOGINFO('Not an error!  Armory really is open')
      return
   elif len(bitcoindExists)>0:
      # Strange condition where bitcoind doesn't get killed by Armory/guardian
      # (I've only seen this happen on windows, though)
      LOGERROR('Found zombie bitcoind process...killing it')
      for pid in bitcoindExists:
         killProcess(pid)
      time.sleep(0.5)
      raise


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
