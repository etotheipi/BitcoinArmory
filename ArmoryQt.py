#! /usr/bin/python
# -*- coding: UTF-8 -*-
################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

import gettext


from copy import deepcopy
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
import glob


from PyQt4.QtCore import *
from PyQt4.QtGui import *
import psutil
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol, ClientFactory

import CppBlockUtils as Cpp
from announcefetch import AnnounceDataFetcher, ANNOUNCE_URL, ANNOUNCE_URL_BACKUP, \
   DEFAULT_FETCH_INTERVAL
from armorycolors import Colors, htmlColor, QAPP
from armoryengine.ALL import *
from armoryengine.Block import PyBlock
from armoryengine.Decorators import RemoveRepeatingExtensions
from armoryengine.PyBtcWalletRecovery import WalletConsistencyCheck
from armoryengine.parseAnnounce import changelogParser, downloadLinkParser, \
   notificationParser
from armorymodels import *
from jasvet import verifySignature
import qrc_img_resources
from qtdefines import *
from qtdialogs import *
from ui.MultiSigDialogs import DlgSelectMultiSigOption, DlgLockboxManager, \
                    DlgMergePromNotes, DlgCreatePromNote, DlgImportAsciiBlock
from ui.VerifyOfflinePackage import VerifyOfflinePackageDialog
from ui.Wizards import WalletWizard, TxWizard
from ui.toolsDialogs import MessageSigningVerificationDialog
from dynamicImport import MODULE_PATH_KEY, ZIP_EXTENSION, getModuleList, importModule,\
   verifyZipSignature, MODULE_ZIP_STATUS, INNER_ZIP_FILENAME,\
   MODULE_ZIP_STATUS_KEY, getModuleListNoZip, dynamicImportNoZip
import tempfile


# Load our framework with OS X-specific code.
if OS_MACOSX:
   import ArmoryMac

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


MODULES_ZIP_DIR_NAME = 'modules'

class ArmoryMainWindow(QMainWindow):
   """ The primary Armory window """

   #############################################################################

   def __init__(self, parent=None, splashScreen=None):
      super(ArmoryMainWindow, self).__init__(parent)

      self.isShuttingDown = False
      
      # Load the settings file
      self.settingsPath = CLI_OPTIONS.settingsPath
      self.settings = SettingsFile(self.settingsPath)

      # SETUP THE WINDOWS DECORATIONS
      self.lblLogoIcon = QLabel()
      if USE_TESTNET:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [TESTNET] dlgMain')
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

      # OS X requires some Objective-C code if we're switching to the testnet
      # (green) icon. We should also use a larger icon. Otherwise, Info.plist
      # takes care of everything.
      if not OS_MACOSX:
         self.setWindowIcon(QIcon(self.iconfile))
      else:
         self.notifCtr = ArmoryMac.MacNotificationHandler.None
         if USE_TESTNET:
            self.iconfile = ':/armory_icon_green_fullres.png'
            ArmoryMac.MacDockIconHandler.instance().setMainWindow(self)
            ArmoryMac.MacDockIconHandler.instance().setIcon(QIcon(self.iconfile))
      self.lblLogoIcon.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      self.netMode     = NETWORKMODE.Offline
      self.abortLoad   = False
      self.memPoolInit = False
      self.needUpdateAfterScan = True
      self.sweepAfterScanList = []
      self.newWalletList = []
      self.newZeroConfSinceLastUpdate = []
      self.lastSDMState = BDM_UNINITIALIZED
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
      self.tempModulesDirName = None
      self.internetStatus = None

      # We only need a single connection to bitcoind since it's a
      # reconnecting connection, so we keep it around.
      self.SingletonConnectedNetworkingFactory = None

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

      #generic signal to run pass any method as the arg
      self.connect(self, SIGNAL('method_signal') , self.method_signal)  
                
      #push model BDM notify signal
      self.connect(self, SIGNAL('cppNotify'), self.handleCppNotification)
      TheBDM.registerCppNotification(self.cppNotifySignal)

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

      def updateProgress(val):
         if splashScreen is not None:
            splashScreen.updateProgress(val)
      self.loadWalletsAndSettings(updateProgress)      

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


      # This is a list of alerts that the user has chosen to no longer
      # be notified about
      alert_str = str(self.getSettingOrSetDefault('IgnoreAlerts', ""))
      if alert_str == "":
         alerts = []
      else:
         alerts = alert_str.split(",")
      self.ignoreAlerts = {int(s):True for s in alerts}


      # If we're going into online mode, start loading blockchain
      if self.doAutoBitcoind:
         self.startBitcoindIfNecessary()
      else:
         self.loadBlockchainIfNecessary()

      # Setup system tray and register "bitcoin:" URLs with the OS
      self.setupSystemTray()
      self.setupUriRegistration()

      self.heartbeatCount = 0

      self.extraHeartbeatSpecial  = []
      self.extraHeartbeatAlways   = []
      self.extraHeartbeatOnline   = []
      self.extraNewTxFunctions    = []
      self.extraNewBlockFunctions = []
      self.extraShutdownFunctions = []
      self.extraGoOnlineFunctions = []
      
      self.walletDialogDict = {}

      self.lblArmoryStatus = QRichLabel(tr('<font color=%(color)s>Offline</font> ') %
                                      { 'color' : htmlColor('TextWarn') }, doWrap=False)

      self.statusBar().insertPermanentWidget(0, self.lblArmoryStatus)

      # Table for all the wallets
      self.walletModel = AllWalletsDispModel(self)
      self.walletsView  = QTableView(self)

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
      self.ledgerModel.setLedgerDelegate(TheBDM.bdv().getLedgerDelegateForWallets())
      self.ledgerModel.setConvertLedgerMethod(self.convertLedgerToTable)


      self.frmLedgUpDown = QFrame()
      self.ledgerView  = ArmoryTableView(self, self, self.frmLedgUpDown)
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
      self.currentLBPage = 0
      self.lockboxLedgTable = []
      self.lockboxLedgModel = LedgerDispModelSimple(self.lockboxLedgTable, 
                                                    self, self, isLboxModel=True)
      self.lockboxLedgModel.setLedgerDelegate(TheBDM.bdv().getLedgerDelegateForLockboxes())
      self.lockboxLedgModel.setConvertLedgerMethod(self.convertLedgerToTable)
      self.lbDialogModel = None

      dateWidth    = tightSizeStr(self.ledgerView, '_9999-Dec-99 99:99pm__')[0]
      nameWidth    = tightSizeStr(self.ledgerView, '9'*32)[0]
      cWidth = 20 # num-confirm icon width
      tWidth = 72 # date icon width
      initialColResize(self.ledgerView, [cWidth, 0, dateWidth, tWidth, 0.30, 0.40, 0.3])

      self.connect(self.ledgerView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.dblClickLedger)

      self.ledgerView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.ledgerView.customContextMenuRequested.connect(self.showContextMenuLedger)

      btnAddWallet  = QPushButton(tr("Create Wallet"))
      btnImportWlt  = QPushButton(tr("Import or Restore Wallet"))
      self.connect(btnAddWallet,  SIGNAL('clicked()'), self.startWalletWizard)
      self.connect(btnImportWlt,  SIGNAL('clicked()'), self.execImportWallet)

      # Put the Wallet info into it's own little box
      lblAvail = QLabel(tr("<b>Available Wallets:</b>"))
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

      #page selection UI
      self.mainLedgerCurrentPage = 1
      self.lblPages     = QRichLabel('Page: ')
      self.PageLineEdit = QLineEdit('1')
      self.lblNPages    = QRichLabel(' out of 1') 
      
      self.connect(self.PageLineEdit, SIGNAL('editingFinished()'), \
                   self.loadNewPage)
            
      self.changeWltFilter()      
      

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

      frmFilter = makeVertFrame([QLabel(tr('Filter:')), self.comboWltSelect, 'Stretch'])

      frmLower = makeHorizFrame([ frmFilter, \
                                 'Stretch', \
                                 self.frmLedgUpDown, \
                                 'Stretch', \
                                 frmTotals])

      # Now add the ledger to the bottom of the window
      ledgLayout = QGridLayout()
      ledgLayout.addWidget(self.ledgerView,           1,0)
      ledgLayout.addWidget(frmLower,                  2,0)
      ledgLayout.setRowStretch(0, 0)
      ledgLayout.setRowStretch(1, 1)
      ledgLayout.setRowStretch(2, 0)

      self.tabActivity = QWidget()
      self.tabActivity.setLayout(ledgLayout)

      self.tabAnnounce = QWidget()
      self.setupAnnounceTab()


      # Add the available tabs to the main tab widget
      self.MAINTABS  = enum('Dash','Ledger','Announce')

      self.mainDisplayTabs.addTab(self.tabDashboard, tr('Dashboard'))
      self.mainDisplayTabs.addTab(self.tabActivity,  tr('Transactions'))
      self.mainDisplayTabs.addTab(self.tabAnnounce,  tr('Announcements'))

      ##########################################################################
      if not CLI_OPTIONS.disableModules:
         if USE_TESTNET:
            self.loadArmoryModulesNoZip()
      # Armory Modules are diabled on main net. If enabled it uses zip files to 
      # contain the modules     
      #   else:
      #      self.loadArmoryModules()   
      ##########################################################################

      self.lbDialog = None

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

      verStr = 'Armory %s / %s' % (getVersionString(BTCARMORY_VERSION),
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
      self.menusList.append( self.menu.addMenu(tr('&File')) )
      self.menusList.append( self.menu.addMenu(tr('&User')) )
      self.menusList.append( self.menu.addMenu(tr('&Tools')) )
      self.menusList.append( self.menu.addMenu(tr('&Addresses')) )
      self.menusList.append( self.menu.addMenu(tr('&Wallets')) )
      self.menusList.append( self.menu.addMenu(tr('&MultiSig')) )
      self.menusList.append( self.menu.addMenu(tr('&Help')) )
      #self.menusList.append( self.menu.addMenu('&Network') )


      def exportTx():
         if not TheBDM.getState()==BDM_BLOCKCHAIN_READY:
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
         if not TheBDM.getState()==BDM_BLOCKCHAIN_READY:
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

      self.menusList[MENUS.Wallets].addAction(actCreateNew)
      self.menusList[MENUS.Wallets].addAction(actImportWlt)
      self.menusList[MENUS.Wallets].addSeparator()
      self.menusList[MENUS.Wallets].addAction(actRecoverWlt)

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


      if DO_WALLET_CHECK: 
         self.checkWallets()

      self.blkReceived = RightNow()

      self.setDashboardDetails()

      from twisted.internet import reactor
      reactor.callLater(0.1,  self.execIntroDialog)
      reactor.callLater(1, self.Heartbeat)

      if self.getSettingOrSetDefault('MinimizeOnOpen', False) and not CLI_ARGS:
         LOGINFO('MinimizeOnOpen is True')
         reactor.callLater(0, self.minimizeArmory)

      if CLI_ARGS:
         reactor.callLater(1, self.uriLinkClicked, CLI_ARGS[0])

      if OS_MACOSX:
         self.macNotifHdlr = ArmoryMac.MacNotificationHandler()
         if self.macNotifHdlr.hasUserNotificationCenterSupport():
            self.notifCtr = ArmoryMac.MacNotificationHandler.BuiltIn
         else:
            # In theory, Qt can support notifications via Growl on pre-10.8
            # machines. It's shaky as hell, though, so we'll rely on alternate
            # code for now. In the future, according to
            # https://bugreports.qt-project.org/browse/QTBUG-33733 (which may not
            # be accurate, as the official documentation is contradictory),
            # showMessage() may have direct support for the OS X notification
            # center in Qt5.1. Something to experiment with later....
            self.notifCtr = self.macNotifHdlr.hasGrowl()

      # Now that construction of the UI is done
      # Check for warnings to be displayed

     # This is true if and only if the command line has a data dir that doesn't exist
      # and can't be created.
      if not CLI_OPTIONS.datadir in [ARMORY_HOME_DIR, DEFAULT]:
         QMessageBox.warning(self, tr('Default Data Directory'), tr("""
            Armory is using the default data directory because
            the data directory specified in the command line, could
            not be found and could not be created."""), QMessageBox.Ok)
      # This is true if and only if the command line has a database dir that doesn't exist
      # and can't be created.
      elif not CLI_OPTIONS.armoryDBDir in [ARMORY_DB_DIR, DEFAULT]:
         QMessageBox.warning(self, tr('Default Database Directory'), tr("""
            Armory is using the default database directory because
            the database directory specified in the command line, could
            not be found and could not be created."""), QMessageBox.Ok)
      
      # This is true if and only if the command line has a bitcoin dir that doesn't exist
      if not CLI_OPTIONS.satoshiHome in [BTC_HOME_DIR, DEFAULT]:
         QMessageBox.warning(self, tr('Bitcoin Directory'), tr("""
            Armory is using the default Bitcoin directory because
            the Bitcoin director specified in the command line, could
            not be found."""), QMessageBox.Ok)
         
      if not self.getSettingOrSetDefault('DNAA_DeleteLevelDB', False) and \
            os.path.exists(os.path.join(ARMORY_DB_DIR, LEVELDB_BLKDATA)):
               reply = MsgBoxWithDNAA(self, self, MSGBOX.Question, 'Delete Old DB Directory', \
                  'Armory detected an older version Database. '
                  'Do you want to delete the old database? Choose yes if '
                  'do not think that you will revert to an older version of Armory.', 'Do not ask this question again')
               if reply[0]==True:
                  shutil.rmtree(os.path.join(ARMORY_DB_DIR, LEVELDB_BLKDATA))
                  shutil.rmtree(os.path.join(ARMORY_DB_DIR, LEVELDB_HEADERS))
               if reply[1]==True:
                  self.writeSetting('DNAA_DeleteLevelDB', True)   
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
         #self.walletsView.resizeColumnToContents(0)
      else:
         self.walletsView.hideColumn(0)

      if currIdx != 4: 
         for i in range(0, len(self.walletVisibleList)):         
            self.walletVisibleList[i] = False
            
      # If a specific wallet is selected, just set that and you're done
      if currIdx > 4:
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
      
      self.mainLedgerCurrentPage = 1
      self.PageLineEdit.setText(str(self.mainLedgerCurrentPage))
      
      self.wltIDList = []
      for i,vis in enumerate(self.walletVisibleList):
         if vis:
            wltid = self.walletIDList[i]
            if self.walletMap[wltid].isEnabled:
               self.wltIDList.append(wltid)

      try:
         TheBDM.bdv().updateWalletsLedgerFilter(self.wltIDList)      
      except:
         pass

   ############################################################################
   def loadArmoryModulesNoZip(self):
      """
      This method checks for any .py files in the exec directory
      """ 
      moduleDir = os.path.join(GetExecDir(), MODULES_ZIP_DIR_NAME)
      if not moduleDir or not os.path.exists(moduleDir):
         return

      LOGWARN('Attempting to load modules from: %s' % MODULES_ZIP_DIR_NAME)

      # This call does not eval any code in the modules.  It simply
      # loads the python files as raw chunks of text so we can
      # check hashes and signatures
      modMap = getModuleListNoZip(moduleDir)
      for moduleName,infoMap in modMap.iteritems():
         module = dynamicImportNoZip(moduleDir, moduleName, globals())
         plugObj = module.PluginObject(self)

         if not hasattr(plugObj,'getTabToDisplay') or \
            not hasattr(plugObj,'tabName'):
            LOGERROR('Module is malformed!  No tabToDisplay or tabName attrs')
            QMessageBox.critmoduleName(self, tr("Bad Module"), tr("""
               The module you attempted to load (%s) is malformed.  It is 
               missing attributes that are needed for Armory to load it.  
               It will be skipped.""") % moduleName, QMessageBox.Ok)
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
   def loadArmoryModules(self):
      """
      This method checks for any .zip files in the modules directory
      """ 
      modulesZipDirPath = os.path.join(GetExecDir(), MODULES_ZIP_DIR_NAME)
      if modulesZipDirPath and os.path.exists(modulesZipDirPath):
         
         self.tempModulesDirName = tempfile.mkdtemp('modules')

   
         # This call does not eval any code in the modules.  It simply
         # loads the python files as raw chunks of text so we can
         # check hashes and signatures
         modMap = getModuleList(modulesZipDirPath)
         for moduleName,infoMap in modMap.iteritems():
            moduleZipPath = os.path.join(modulesZipDirPath, infoMap[MODULE_PATH_KEY])
            if  infoMap[MODULE_ZIP_STATUS_KEY] == MODULE_ZIP_STATUS.Invalid:
               reply = QMessageBox.warning(self, tr("Invalid Module"), tr("""
                  Armory detected the following module which is 
                  <font color=%(color)s"><b>invalid</b></font>:
                  <br><br>
                     <b>Module Name:</b> %(name)s<br>
                     <b>Module Path:</b> %(path)s<br>
                  <br><br>
                  Armory will only run a module from a zip file that
                  has the required stucture.""") % \
                  { 'color' : htmlColor('TextRed'), 'name' : moduleName, 'path' : moduleZipPath}, QMessageBox.Ok)
            elif not USE_TESTNET and infoMap[MODULE_ZIP_STATUS_KEY] == MODULE_ZIP_STATUS.Unsigned:
               reply = QMessageBox.warning(self, tr("UNSIGNED Module"), tr("""
                  Armory detected the following module which  
                  <font color="%(color)s"><b>has not been signed by Armory</b></font> and may be dangerous:
                  <br><br>
                     <b>Module Name:</b> %(name)s<br>
                     <b>Module Path:</b> %(path)s<br>
                  <br><br>
                  Armory will not allow you to run this module.""") % \
                  { 'color' : htmlColor('TextRed'), 'name' : moduleName, 'path' : moduleZipPath}, QMessageBox.Ok)
            else:
   
               ZipFile(moduleZipPath).extract(INNER_ZIP_FILENAME, self.tempModulesDirName)
               ZipFile(os.path.join(self.tempModulesDirName,INNER_ZIP_FILENAME)).extractall(self.tempModulesDirName)
               
               plugin = importModule(self.tempModulesDirName, moduleName, globals())
               plugObj = plugin.PluginObject(self)
      
               if not hasattr(plugObj,'getTabToDisplay') or \
                  not hasattr(plugObj,'tabName'):
                  LOGERROR('Module is malformed!  No tabToDisplay or tabName attrs')
                  QMessageBox.critmoduleName(self, tr("Bad Module"), tr("""
                     The module you attempted to load (%s) is malformed.  It is 
                     missing attributes that are needed for Armory to load it.  
                     It will be skipped.""") % moduleName, QMessageBox.Ok)
                  continue
                     
               verPluginInt = getVersionInt(readVersionString(plugObj.maxVersion))
               verArmoryInt = getVersionInt(BTCARMORY_VERSION)
               if verArmoryInt >verPluginInt:
                  reply = QMessageBox.warning(self, tr("Outdated Module"), tr("""
                     Module %(mod)s is only specified to work up to Armory version %(maxver)s.
                     You are using Armory version %(curver)s.  Please remove the module if
                     you experience any problems with it, or contact the maintainer
                     for a new version.
                     <br><br>
                     Do you want to continue loading the module?""") \
                        % { 'mod' : moduleName, 'maxver' : plugObj.maxVersion, 
                                 'curver' : getVersionString(BTCARMORY_VERSION)} , 
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
      rdfs_found = glob.glob(
          os.path.join(
              os.path.expanduser("~"),
              ".mozilla",
              "firefox",
              "*",
              "mimeTypes.rdf"
          )
      )
      for rdfs in rdfs_found:
         if rdfs:
            try:
               FFrdf = open(rdfs, 'r+')
            except IOError:
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
               reply = MsgBoxWithDNAA(self, self, MSGBOX.Question, 'Default URL Handler', \
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
            reply = MsgBoxWithDNAA(self, self, MSGBOX.Question, 'Default URL Handler', \
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
         reply = MsgBoxWithDNAA(self, self, MSGBOX.Warning, tr("Version Warning"), tr("""
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
         fn = 'armory_%s_%s_WatchOnly.wallet' % (wlt.uniqueIDB58, suffix)
      savePath = unicode(self.getFileSave(defaultFilename=fn, 
                ffilter=[tr('Root Pubkey Text Files (*.rootpubkey)')]))
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
      # Decide if disable OS/version reporting sent with announce fetches
      skipStats1 = self.getSettingOrSetDefault('SkipStatsReport', False)
      skipStats2 = CLI_OPTIONS.skipStatsReport
      self.skipStatsReport = skipStats1 or skipStats2

      # This determines if we should disable all of it
      skipChk1 = self.getSettingOrSetDefault('SkipAnnounceCheck', False)
      skipChk2 = CLI_OPTIONS.skipAnnounceCheck
      skipChk3 = CLI_OPTIONS.offline and not CLI_OPTIONS.testAnnounceCode
      skipChk4  = CLI_OPTIONS.useTorSettings 
      skipChk5  = self.getSettingOrSetDefault('UseTorSettings', False)
      self.skipAnnounceCheck = \
                  skipChk1 or skipChk2 or skipChk3 or skipChk4 or skipChk5


      url1 = ANNOUNCE_URL
      url2 = ANNOUNCE_URL_BACKUP
      fetchPath = os.path.join(ARMORY_HOME_DIR, 'atisignedannounce')
      if self.announceFetcher is None:

         # We keep an ID in the settings file that can be used by ATI's
         # statistics aggregator to remove duplicate reports.  We store
         # the month&year that the ID was generated, so that we can change
         # it every month for privacy reasons
         idData = self.getSettingOrSetDefault('MonthlyID', '0000_00000000')
         storedYM,currID = idData.split('_')
         monthyear = unixTimeToFormatStr(RightNow(), '%m%y')
         if not storedYM == monthyear:
            currID = SecureBinaryData().GenerateRandom(4).toHexStr()
            self.settings.set('MonthlyID', '%s_%s' % (monthyear, currID))
            
         self.announceFetcher = AnnounceDataFetcher(url1, url2, fetchPath, currID)
         self.announceFetcher.setStatsDisable(self.skipStatsReport)
         self.announceFetcher.setFullyDisabled(self.skipAnnounceCheck)
         self.announceFetcher.start()

         # Set last-updated vals to zero to force processing at startup
         for fid in ['changelog, downloads','notify','bootstrap']:
            self.lastAnnounceUpdate[fid] = 0

      # If we recently updated the settings to enable or disable checking...
      if not self.announceFetcher.isRunning() and not self.skipAnnounceCheck:
         self.announceFetcher.setFullyDisabled(False)
         self.announceFetcher.setFetchInterval(DEFAULT_FETCH_INTERVAL)
         self.announceFetcher.start()
      elif self.announceFetcher.isRunning() and self.skipAnnounceCheck:
         self.announceFetcher.setFullyDisabled(True)
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
   def processAlerts(self):
      # display to the user any alerts that came in through the bitcoin
      # network
      
      if self.NetworkingFactory == None:
         return
      
      factory = self.NetworkingFactory
      armoryClient = factory.getProto()
      if armoryClient is None:
         return
      alerts = armoryClient.alerts
      
      try:
         peerInfo = armoryClient.peerInfo
      except: 
         LOGERROR("failed to process alerts from bitcoind")
         return

      for id, alert in alerts.items():
         if self.ignoreAlerts.get(id):
            continue
         if time.time() > alert.expiration:
            continue
         if peerInfo["version"] < alert.minVersion \
            or peerInfo["version"] > alert.maxVersion:
            continue
         if peerInfo["subver"] not in alert.subVerSet:
            continue
         title = "Bitcoin alert %s" % alert.uniqueID
         alert_str = "%s<br>%s<br>%s<br>" % (alert.statusBar, alert.comment, alert.reserved)
         msg = "This alert has been received from the bitcoin network:<p>" + \
               alert_str + \
               "</p>Please visit <a href='http://www.bitcoin.org/en/alerts'>http://www.bitcoin.org/en/alerts</a> for more information.<br>"
         reply, self.ignoreAlerts[id] = MsgBoxWithDNAA(
            self, self, MSGBOX.Warning, title, msg,
            'Do not show me this notification again', yesStr='OK')
         self.writeSetting('IgnoreAlerts', ",".join([str(i) for i in self.ignoreAlerts.keys()]))


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
               if self.NetworkingFactory.getProto():
                  thisVerStr = self.NetworkingFactory.getProto().peerInfo['subver']
                  thisVerStr = thisVerStr.strip('/').split(':')[-1]

                  if sum([0 if c in '0123456789.' else 1 for c in thisVerStr]) > 0:
                     return
   
                  self.satoshiVersions[0] = thisVerStr
               else:
                  return

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
            %(ver)s through our secure downloader inside Armory (link at the bottom
            of this notification window).
            """) % { 'ver' : verStr}
         
      return tr("""
         Your version of Armory is now outdated.  Please upgrade to version
         %(ver)s through our secure downloader inside Armory (link at the bottom
         of this notification window).  Alternatively, you can get the new
         version from our website downloads page at:
         <br><br>
         <a href="%(url)s">%(url)s</a> """) % {'ver' : verStr, 'url' : webURL}



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

   def setupNetworking(self):
      LOGINFO('Setting up networking...')

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
      useTor = self.getSettingOrSetDefault('UseTorSettings', False)
      # Check general internet connection
      self.internetStatus = isInternetAvailable(forceOnline =
             CLI_OPTIONS.forceOnline or settingSkipCheck or useTor)

      LOGINFO('Internet status: %s', self.internetStatus)

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
      if self.internetStatus == INTERNET_STATUS.Unavailable or CLI_OPTIONS.offline:
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
         TheSDM.startBitcoind(self.notifyBitcoindIsReady)
         LOGDEBUG('Bitcoind started without error')
         return True
      except:
         LOGEXCEPT('Failed to setup SDM')
         self.switchNetworkMode(NETWORKMODE.Offline)
   
   ############################################################################
   def notifyBitcoindIsReady(self):
      self.emit(SIGNAL('method_signal'), self.proceedOnceBitcoindIsReady)    

   ############################################################################
   def proceedOnceBitcoindIsReady(self):
      self.loadBlockchainIfNecessary()
      self.setDashboardDetails()  
      
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
         CLI_OPTIONS.satoshiHome==DEFAULT:
         # Setting override BTC_HOME_DIR only if it wasn't explicitly
         # set as the command line.
         self.satoshiHomePath = self.settings.get('SatoshiDatadir')
         LOGINFO('Setting satoshi datadir = %s' % self.satoshiHomePath)

      TheBDM.setSatoshiDir(self.satoshiHomePath)
      TheSDM.setSatoshiDir(self.satoshiHomePath)
      TheTDM.setSatoshiDir(self.satoshiHomePath)
      
      
   ############################################################################
   # This version of online mode is possible doesn't check the internet everytime
   def isOnlineModePossible(self):
      return self.internetStatus != INTERNET_STATUS.Unavailable and \
               satoshiIsAvailable() and \
               os.path.exists(os.path.join(TheBDM.btcdir, 'blocks'))

   ############################################################################
   def loadBlockchainIfNecessary(self):
      LOGINFO('loadBlockchainIfNecessary')
      if CLI_OPTIONS.offline:
         self.switchNetworkMode(NETWORKMODE.Offline)
      elif self.isOnlineModePossible():
         # Track number of times we start loading the blockchain.
         # We will decrement the number when loading finishes
         # We can use this to detect problems with mempool or blkxxxx.dat
         self.numTriesOpen = self.getSettingOrSetDefault('FailedLoadCount', 0)
         if self.numTriesOpen>2:
            self.loadFailedManyTimesFunc(self.numTriesOpen)
         self.settings.set('FailedLoadCount', self.numTriesOpen+1)

         self.switchNetworkMode(NETWORKMODE.Full)
         TheBDM.goOnline()           
      else:
         self.switchNetworkMode(NETWORKMODE.Offline)
         
 

   #############################################################################
   def switchNetworkMode(self, newMode):
      LOGINFO('Setting netmode: %s', newMode)
      self.netMode=newMode
      if newMode in (NETWORKMODE.Offline, NETWORKMODE.Disconnected):
         self.NetworkingFactory = FakeClientFactory()
      elif newMode==NETWORKMODE.Full:
         self.NetworkingFactory = self.getSingletonConnectedNetworkingFactory()
      return


   #############################################################################
   def getSingletonConnectedNetworkingFactory(self):
      if not self.SingletonConnectedNetworkingFactory:
         # ArmoryClientFactory auto-reconnects, so add the connection
         # the very first time and never afterwards.

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
               self.showTrayMsg('Disconnected', 'Connection to Bitcoin-Qt ' \
			                    'client lost!  Armory cannot send nor ' \
								'receive bitcoins until connection is ' \
								're-established.', QSystemTrayIcon.Critical, \
								10000)
            except:
               LOGEXCEPT('Failed to show disconnect notification')


         self.connectCount = 0
         def showOnlineMsg():
            self.netMode = NETWORKMODE.Full
            self.setDashboardDetails()
            self.lblArmoryStatus.setText(\
                     '<font color=%s>Connected (%s blocks)</font> ' %
                     (htmlColor('TextGreen'), TheBDM.getTopBlockHeight()))
            if not self.getSettingOrSetDefault('NotifyReconn', True):
               return

            try:
               if self.connectCount>0:
                  self.showTrayMsg('Connected', 'Connection to Bitcoin-Qt ' \
                                   're-established', \
								   QSystemTrayIcon.Information, 10000)
               self.connectCount += 1
            except:
               LOGEXCEPT('Failed to show reconnect notification')

         self.SingletonConnectedNetworkingFactory = ArmoryClientFactory(
                                      TheBDM,
                                      func_loseConnect=showOfflineMsg,
                                      func_madeConnect=showOnlineMsg,
                                      func_newTx=self.newTxFunc)
         reactor.callWhenRunning(reactor.connectTCP, '127.0.0.1',
                                 BITCOIN_PORT,
                                 self.SingletonConnectedNetworkingFactory)
      return self.SingletonConnectedNetworkingFactory


   #############################################################################
   def newTxFunc(self, pytxObj):
      if TheBDM.getState() in (BDM_OFFLINE,BDM_UNINITIALIZED) or self.doShutdown:
         return

      TheBDM.bdv().addNewZeroConfTx(pytxObj.serialize(), long(RightNow()), True)

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

      try:
         uriDict = parseBitcoinURI(uriStr)
      except:
         # malformed uri, make the dict empty, which will trigger the warning
         uriDict = {}
         
      if TheBDM.getState() in (BDM_OFFLINE,BDM_UNINITIALIZED):
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
            warnMsg += 'The raw URI string is:\n\n' + uriStr
         QMessageBox.warning(self, 'Invalid URI', warnMsg, QMessageBox.Ok)
         LOGERROR(warnMsg.replace('\n', ' '))
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
      if TheBDM.getState()==BDM_OFFLINE:
         QMessageBox.warning(self, 'Offline', \
            'You just clicked on a "bitcoin:" link, but Armory is offline '
            'and cannot send transactions.  Please click the link '
            'again when Armory is online.', \
            QMessageBox.Ok)
         return
      elif not TheBDM.getState()==BDM_BLOCKCHAIN_READY:
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

   def loadWalletsAndSettings(self, updateProgress):
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
      self.wltIDList = []
      self.combinedLedger = []
      self.ledgerSize = 0
      self.ledgerTable = []
      self.walletSideScanProgress = {}


      LOGINFO('Loading wallets...')
      wltPaths = readWalletFiles()

      wltExclude = self.settings.get('Excluded_Wallets', expectList=True)
      
      ratioPerWallet = 0
      if len(wltPaths) > 0:
         ratioPerWallet = 100 / float(len(wltPaths))
         
      i = 0
      for fpath in wltPaths:
         currentProgress = float(i) * ratioPerWallet
         updateProgress(currentProgress)
         i += 1
         
         def reportProgress(val):
            updateProgress(currentProgress + val*ratioPerWallet
                           )
         try:
            wltLoad = PyBtcWallet().readWalletFile(fpath, \
                                 reportProgress=reportProgress)
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
            #raise



      LOGINFO('Number of wallets read in: %d', len(self.walletMap))
      for wltID, wlt in self.walletMap.iteritems():
         dispStr  = ('   Wallet (%s):' % wlt.uniqueIDB58).ljust(25)
         dispStr +=  '"'+wlt.labelName.ljust(32)+'"   '
         dispStr +=  '(Encrypted)' if wlt.useEncryption else '(No Encryption)'
         LOGINFO(dispStr)
         # Register all wallets with TheBDM
         
         wlt.registerWallet()


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

      updateProgress(100)

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

      # Open the native file save dialog and grab the saved file/path unless
      # we're in OS X, where native dialogs sometimes freeze. Looks like a Qt
      # issue of some sort. Some experimental code under ArmoryMac that directly
      # calls a dialog produces better results but still freezes under some
      # circumstances.
      if not OS_MACOSX:
         fullPath = unicode(QFileDialog.getSaveFileName(self, title, startPath,
                                                        typesStr))
      else:
         fullPath = unicode(QFileDialog.getSaveFileName(self, title, startPath,
                                                        typesStr,
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

      # Open the native file load dialog and grab the loaded file/path unless
      # we're in OS X, where native dialogs sometimes freeze. Looks like a Qt
      # issue of some sort. Some experimental code under ArmoryMac that directly
      # calls a dialog produces better results but still freezes under some
      # circumstances.
      if not OS_MACOSX:
         fullPath = unicode(QFileDialog.getOpenFileName(self, title, defaultDir,
                                                        typesStr))
      else:
         fullPath = unicode(QFileDialog.getOpenFileName(self, title, defaultDir,
                                                        typesStr,
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
              
            scraddrReg = script_to_scrAddr(lbObj.binScript)
            scraddrP2SH = script_to_scrAddr(script_to_p2sh_script(lbObj.binScript))
            scrAddrList = []
            scrAddrList.append(scraddrReg)
            scrAddrList.append(scraddrP2SH)
            self.cppLockboxWltMap[lbID] = lbObj.registerLockbox(scrAddrList, isFresh)

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
      self.lbDialog = DlgLockboxManager(self, self)
      self.lbDialog.exec_()
      self.lblDialog = None

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



   # NB: armoryd has a similar function (Armory_Daemon::start()), and both share
   # common functionality in ArmoryUtils (finishLoadBlockchainCommon). If you
   # mod this function, please be mindful of what goes where, and make sure
   # any critical functionality makes it into armoryd.
   def finishLoadBlockchainGUI(self):
      # Let's populate the wallet info after finishing loading the blockchain.
         
      self.setDashboardDetails()
      self.memPoolInit = True

      self.createCombinedLedger()
      self.ledgerSize = len(self.combinedLedger)
      self.statusBar().showMessage('Blockchain loaded, wallets sync\'d!', 10000)
      if self.netMode==NETWORKMODE.Full:
         LOGINFO('Current block number: %d', TheBDM.getTopBlockHeight())
         self.lblArmoryStatus.setText(\
            '<font color=%s>Connected (%s blocks)</font> ' %
            (htmlColor('TextGreen'), TheBDM.getTopBlockHeight()))

      currSyncSuccess = self.getSettingOrSetDefault("SyncSuccessCount", 0)
      self.writeSetting('SyncSuccessCount', min(currSyncSuccess+1, 10))

      if self.getSettingOrSetDefault('NotifyBlkFinish',True):
         reply,remember = MsgBoxWithDNAA(self, self, MSGBOX.Info, \
            'Blockchain Loaded!', 'Blockchain loading is complete.  '
            'Your balances and transaction history are now available '
            'under the "Transactions" tab.  You can also send and '
            'receive bitcoins.', \
            dnaaMsg='Do not show me this notification again ', yesStr='OK')

         if remember==True:
            self.writeSetting('NotifyBlkFinish',False)

      self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Ledger)


      self.netMode = NETWORKMODE.Full
      self.settings.set('FailedLoadCount', 0)

      # This will force the table to refresh with new data
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

   def createCombinedLedger(self, resetMainLedger=False):
      """
      Create a ledger to display on the main screen, that consists of ledger
      entries of any SUBSET of available wallets.
      """
      bdmState = TheBDM.getState()
      

      self.combinedLedger = []
      #self.combinedLedger.extend(TheBDM.bdv().getWalletsHistoryPage(self.mainLedgerCurrentPage -1))
      totalFunds  = 0
      spendFunds  = 0
      unconfFunds = 0

      if bdmState == BDM_BLOCKCHAIN_READY:
         for wltID in self.wltIDList:
            wlt = self.walletMap[wltID]
            totalFunds += wlt.getBalance('Total')
            spendFunds += wlt.getBalance('Spendable')
            unconfFunds += wlt.getBalance('Unconfirmed')

            
      self.ledgerSize = len(self.combinedLedger)

      # Many MainWindow objects haven't been created yet...
      # let's try to update them and fail silently if they don't exist
      try:
         if bdmState in (BDM_OFFLINE, BDM_SCANNING):
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
         
         if resetMainLedger == False:
            self.ledgerModel.reset()
         else:
            self.ledgerView.goToTop()

      except AttributeError:
         raise


      if not self.usermode==USERMODE.Expert:
         return 

      # In expert mode, we're updating the lockbox info, too
      try:
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

   def convertLedgerToTable(self, ledger, showSentToSelfAmt=True, wltIDIn=None):
      table2D = []
      datefmt = self.getPreferredDateFormat()
      for le in ledger:
         if wltIDIn is None:
            wltID = le.getWalletID()
         else: 
            wltID = wltIDIn
          
         row = []

         wlt = self.walletMap.get(wltID)

         if wlt:
            isWatch = (determineWalletType(wlt, self)[0] == WLTTYPES.WatchOnly)
            wltName = wlt.labelName 
            dispComment = self.getCommentForLE(le, wltID)
         else:
            lboxId = wltID
            lbox = self.getLockboxByID(lboxId)
            if not lbox:
               continue
            isWatch = True
            wltName = '%s-of-%s: %s (%s)' % (lbox.M, lbox.N, lbox.shortName, lboxId)
            dispComment = self.getCommentForLockboxTx(lboxId, le)

         nConf = TheBDM.getTopBlockHeight() - le.getBlockNum()+1
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

         # Finally, attach the row to the table
         table2D.append(row)

      return table2D


   #############################################################################

   def walletListChanged(self):
      self.walletModel.reset()
      self.populateLedgerComboBox()
      self.changeWltFilter()

   #############################################################################

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
      self.walletDialogDict[wlt.uniqueIDB58] = dialog
      dialog.exec_()
      if wlt.uniqueIDB58 in self.walletDialogDict:
         del self.walletDialogDict[wlt.uniqueIDB58]

   #############################################################################
   def execClickRow(self, index=None):
      row,col = index.row(), index.column()
      if not col==WLTVIEWCOLS.Visible:
         return

      wltID = self.walletIDList[row]
      currEye = self.walletVisibleList[row]
      self.walletVisibleList[row] = not currEye 
      self.setWltSetting(wltID, 'LedgerShow', not currEye)
      
      if TheBDM.getState()==BDM_BLOCKCHAIN_READY:

         self.changeWltFilter()


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

   def getAddrCommentIfAvailAll(self, txHash):
      if not TheBDM.getState()==BDM_BLOCKCHAIN_READY:
         return ''
      else:

         appendedComments = []
         for wltID,wlt in self.walletMap.iteritems():
            cmt = wlt.getAddrCommentIfAvail(txHash)
            if len(cmt)>0:
               appendedComments.append(cmt)

         return '; '.join(appendedComments)



   #############################################################################
   def getCommentForLE(self, le, wltID=None):
      # Smart comments for LedgerEntry objects:  get any direct comments ...
      # if none, then grab the one for any associated addresses.

      if wltID is None:
         wltID = le.getWalletID()
      return self.walletMap[wltID].getCommentForLE(le)
            
   #############################################################################
   def addWalletToApplication(self, newWallet, walletIsNew=False):
      LOGINFO('addWalletToApplication')
      
      newWallet.registerWallet(walletIsNew)

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
      
      self.walletMap[wltID].unregisterWallet()

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
      utxoList = getUnspentTxOutsForAddr160List(addr160List)
      if len(utxoList)==0:
         return [None, 0, 0]

      outValue = sumTxOutList(utxoList)

      inputSide = []

      for utxo in utxoList:
         # The PyCreateAndSignTx method require PyTx and PyBtcAddress objects
         rawTx = TheBDM.bdv().getTxByHash(utxo.getTxHash()).serialize()
         a160 = CheckHash160(utxo.getRecipientScrAddr())
         for aobj in sweepFromAddrObjList:
            if a160 == aobj.getAddr160():
               pubKey = aobj.binPublicKey65.toBinStr()
               txoIdx = utxo.getTxOutIndex()
               inputSide.append(UnsignedTxInput(rawTx, txoIdx, None, pubKey))
               break

      minFee = calcMinSuggestedFees(utxoList, outValue, 0, 1)

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
      if TheBDM.getState() in (BDM_OFFLINE, BDM_UNINITIALIZED):
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

         if TheBDM.getState()==BDM_SCANNING:
            msgConfirm += ( \
               'There is currently another scan operation being performed.  '
               'Would you like to start the sweep operation after it completes? ')
         elif TheBDM.getState()==BDM_BLOCKCHAIN_READY:
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
         self.setDashboardDetails()
         return True


   #############################################################################
   def finishSweepScan(self, wlt, sweepList, sweepAfterScanTarget):
      LOGINFO('finishSweepScan')
      self.sweepAfterScanList = []

      #######################################################################
      # The createSweepTx method will return instantly because the blockchain
      # has already been rescanned, as described above
      targScript = scrAddr_to_script(SCRADDR_P2PKH_BYTE + sweepAfterScanTarget)
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

      # Finally, if we got here, we're ready to broadcast!
      if gt1:
         dispIn  = 'multiple addresses'
      else:
         dispIn  = 'address <b>%s</b>' % sweepList[0].getAddrStr()

      dispOut = 'wallet <b>"%s"</b> (%s) ' % (wlt.labelName, wlt.uniqueIDB58)
      if DlgVerifySweep(dispIn, dispOut, outVal, fee).exec_():
         self.broadcastTransaction(finishedTx, dryRun=False)

      wlt.finishSweepScan(sweepList)

   #############################################################################
   def broadcastTransaction(self, pytx, dryRun=False):

      if dryRun:
         #DlgDispTxInfo(pytx, None, self, self).exec_()
         return
      else:
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
            if not TheBDM.bdv().getTxByHash(newTxHash).isInitialized():
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
                  appear to have been accepted by the Bitcoin network yet. 
                  This can happen for a variety of reasons.  
                  <br><br>On some occasions the transaction actually will succeed 
                  and this message is displayed prematurely.  To confirm whether the 
                  the transaction actually succeeded, you can try this direct link 
                  to %(blockexplorer)s:
                  <br><br>
                  <a href="%(url)s">%(urlshort)s...</a>  
                  <br><br>
                  If you do not see the 
                  transaction on that webpage within one minute, it failed and you 
                  should attempt to re-send it. 
                  If it <i>does</i> show up, then you do not need to do anything 
                  else -- it will show up in Armory as soon as it receives one
                  confirmation. 
                  <br><br>If the transaction did fail, it is likely because the fee
                  is too low. Try again with a higher fee.
                  
                  If the problem persists, go to "<i>Help</i>" and select 
                  "<i>Submit Bug Report</i>".  Or use "<i>File</i>" -> 
                  "<i>Export Log File</i>" and then attach it to a support 
                  ticket at 
                  <a href="%(supporturl)s">%(supporturl)s</a>""") % {
                     'blockexplorer' : BLOCKEXPLORE_NAME, 'url' : blkexplURL, \
                     'urlshort' : blkexplURL_short, 'supporturl' : supportURL}, QMessageBox.Ok)

         self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Ledger)

         # Send the Tx after a short delay, give the system time to see the Tx
         # on the network and process it, and check to see if the Tx was seen.
         # We may change this setup in the future, but for now....
         reactor.callLater(3, sendGetDataMsg)
         reactor.callLater(15, checkForTxInBDM)


   #############################################################################
   def warnNoImportWhileScan(self):
      extraMsg = ''
      if not self.usermode==USERMODE.Standard:
         extraMsg = ('<br><br>' + \
                     tr('In the future, you may avoid scanning twice by '
                     'starting Armory in offline mode (--offline), and '
                     'perform the import before switching to online mode.'))
      QMessageBox.warning(self, tr('Armory is Busy'), \
         tr('Wallets and addresses cannot be imported while Armory is in '
         'the middle of an existing blockchain scan.  Please wait for '
         'the scan to finish.  ') + extraMsg, QMessageBox.Ok)



   #############################################################################
   def execImportWallet(self):
      sdm = TheSDM.getSDMState()
      bdm = TheBDM.getState()
      if sdm in ['BitcoindInitializing', \
                 'BitcoindSynchronizing', \
                 'TorrentSynchronizing'] or \
         bdm in [BDM_SCANNING]:
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

      wlt = PyBtcWallet().readWalletFile(fn, verifyIntegrity=False)
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

      self.addWalletToApplication(newWlt)
      
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
      if TheBDM.getState()==BDM_SCANNING:
         QMessageBox.warning(self, 'Blockchain Not Ready', \
            'The address book is created from transaction data available in '
            'the blockchain, which has not finished loading.  The address '
            'book will become available when Armory is online.', QMessageBox.Ok)
      elif TheBDM.getState() in (BDM_UNINITIALIZED,BDM_OFFLINE):
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
      cppTx = TheBDM.bdv().getTxByHash(txHashBin)
      if cppTx.isInitialized():
         pytx = PyTx().unserialize(cppTx.serialize())

      if pytx==None:
         QMessageBox.critical(self, 'Invalid Tx',
         'The transaction you requested be displayed does not exist in '
         'Armory\'s database.  This is unusual...', QMessageBox.Ok)
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
      if TheBDM.getState() in (BDM_OFFLINE, BDM_UNINITIALIZED):
         QMessageBox.warning(self, 'Offline Mode', \
           'Armory is currently running in offline mode, and has no '
           'ability to determine balances or create transactions. '
           '<br><br>'
           'In order to send coins from this wallet you must use a '
           'full copy of this wallet from an online computer, '
           'or initiate an "offline transaction" using a watching-only '
           'wallet on an online computer.', QMessageBox.Ok)
         return
      elif TheBDM.getState()==BDM_SCANNING:
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
      loading = None
      QAPP.processEvents()
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
         loading = LoadingDisp(self, self)
         loading.show()
         wltID = self.walletMap.keys()[0]
      else:
         wltSelect = self.walletsView.selectedIndexes()
         if len(wltSelect)>0:
            row = wltSelect[0].row()
            wltID = str(self.walletsView.model().index(row, WLTVIEWCOLS.ID).data().toString())
         dlg = DlgWalletSelect(self, self, 'Receive coins with wallet...', '', \
                                       firstSelect=wltID, onlyMyWallets=False)
         if dlg.exec_():
            loading = LoadingDisp(self, self)
            loading.show()
            wltID = dlg.selectedID
         else:
            selectionMade = False

      if selectionMade:
         wlt = self.walletMap[wltID]
         wlttype = determineWalletType(wlt, self)[0]
         if showRecvCoinsWarningIfNecessary(wlt, self, self):
            QAPP.processEvents()
            dlg = DlgNewAddressDisp(wlt, self, self, loading)
            dlg.exec_()


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
      reply = QMessageBox.warning(self, tr('Bug Reporting'), tr("""<qt>
         As of version 0.91, Armory now includes a form for reporting
         problems with the software.  Please use
         <i>"Help"</i>→<i>"Submit Bug Report"</i>
         to send a report directly to the Armory team, which will include
         your log file automatically.</qt>"""), QMessageBox.Ok | QMessageBox.Cancel)

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
      elif TheBDM.getState() in (BDM_OFFLINE,BDM_UNINITIALIZED):
         #self.resetBdmBeforeScan()
         TheBDM.goOnline()
         self.switchNetworkMode(NETWORKMODE.Full)
      else:
         LOGERROR('ModeSwitch button pressed when it should be disabled')
      time.sleep(0.3)
      self.setDashboardDetails()


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
         self.extraHeartbeatAlways.append(loadBarUpdate) # TODO - Remove this. Put the method in the handle CPP Notification event handler 
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

      # The "Now shutting down" frame
      self.lblShuttingDown    = QRichLabel('', doWrap=False)
      self.lblShuttingDown.setText(tr('Preparing to shut down..'), \
                                    size=4, bold=True, color='Foreground')
      self.lblShuttingDown.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

      layoutDashExit = QGridLayout()
      layoutDashExit.addWidget(self.lblShuttingDown,  0,0, 0, 1)
      
      self.frmDashSubExit = QFrame()
      self.frmDashSubExit.setFrameStyle(STYLE_SUNKEN)
      self.frmDashSubExit.setLayout(layoutDashExit)
      self.frmDashSubExit = makeHorizFrame(['Stretch', \
                                         self.frmDashSubExit, \
                                         'Stretch'])
      

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
      dashLayout.addWidget(self.frmDashSubExit)
      dashLayout.addWidget(self.frmDashMode)
      dashLayout.addWidget(self.lblDashDescr1)
      dashLayout.addWidget(self.frmDashMidButtons )
      dashLayout.addWidget(self.lblDashDescr2)
      dashLayout.addWidget(self.lblDashDescr2)
      frmInner = QFrame()
      frmInner.setLayout(dashLayout)

      self.dashScrollArea = QScrollArea()
      self.dashScrollArea.setWidgetResizable(True)
      self.dashScrollArea.setWidget(frmInner)
      scrollLayout = QVBoxLayout()
      scrollLayout.addWidget(self.dashScrollArea)
      self.tabDashboard.setLayout(scrollLayout)
      self.frmDashSubExit.setVisible(False)



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
            The last update retrieved from the <font color="%(color)s"><b>Armory
            Technologies, Inc.</b></font> announcement feeder was <b>%(time)s</b>
            ago.  The following downloads may not be the latest
            available.""") % { 'color' : htmlColor("TextGreen"), \
            'time' : secondsToHumanTime(sinceLastUpd)}, QMessageBox.Ok)

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
            self.lblArmorySWVersion.setText(tr(
               "You are using the latest version of Armory (%s)"
               % self.armoryVersions[0]))
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
         try:
            if proc.name().lower() in ['bitcoind.exe','bitcoin-qt.exe',\
                                        'bitcoind','bitcoin-qt']:
               killProcess(proc.pid)
               time.sleep(2)
               return
         # If the block above rasises access denied or anything else just skip it
         except:
            pass

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
   def showShuttingDownMessage(self):
      self.isShuttingDown = True
      self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Dash)
      self.frmDashSubExit.setVisible(True)
      self.frmDashMode.setVisible(False)
      self.lblDashDescr1.setVisible(False)
      self.frmDashMidButtons.setVisible(False)
      self.lblDashDescr2.setVisible(False)
      self.lblDashDescr2.setVisible(False)
   
   #############################################################################
   def updateSyncProgress(self):
      
      if self.isShuttingDown:
         return
   
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
               Bootstrap Torrent:  %(sec)s/sec from %(peers)d peers""") % \
               {'sec' : bytesToHumanSize(dlSpeed), 'peers' : numSeeds+numPeers})

            self.lblTorrentStats.setVisible(True)

      elif TheBDM.getState()==BDM_SCANNING:
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

         phase,pct,tleft,numericProgress = TheBDM.predictLoadTime()
         if phase==Cpp.BDMPhase_DBHeaders:
            self.lblDashModeBuild.setText( tr('Loading Database Headers'), \
                                        size=4, bold=True, color='Foreground')
            self.lblDashModeScan.setText( 'Scan Transaction History', \
                                        size=4, bold=True, color='DisableFG')
            self.barProgressBuild.setFormat('%p%')
            self.barProgressScan.setFormat('')
            self.barProgressBuild.setRange(0,100)
            
         elif phase==Cpp.BDMPhase_OrganizingChain:
            self.lblDashModeBuild.setText( tr('Organizing Blockchain'), \
                                        size=4, bold=True, color='Foreground')
            self.lblDashModeScan.setText( tr('Scan Transaction History'), \
                                        size=4, bold=True, color='DisableFG')
            self.barProgressBuild.setFormat('')
            self.barProgressScan.setFormat('')
            self.barProgressBuild.setValue(0)
            self.barProgressBuild.setRange(0,0)
            self.lblTimeLeftBuild.setVisible(False)
         elif phase==Cpp.BDMPhase_BlockHeaders:
            self.lblDashModeBuild.setText( tr('Reading New Block Headers'), \
                                        size=4, bold=True, color='Foreground')
            self.lblDashModeScan.setText( tr('Scan Transaction History'), \
                                        size=4, bold=True, color='DisableFG')
            self.barProgressBuild.setFormat('%p%')
            self.barProgressScan.setFormat('')
            self.barProgressBuild.setRange(0,100)
         elif phase==Cpp.BDMPhase_BlockData:
            self.lblDashModeBuild.setText( tr('Building Databases'), \
                                        size=4, bold=True, color='Foreground')
            self.lblDashModeScan.setText( tr('Scan Transaction History'), \
                                        size=4, bold=True, color='DisableFG')
            self.barProgressBuild.setFormat('%p%')
            self.barProgressScan.setFormat('')
            self.barProgressBuild.setRange(0,100)
         elif phase==Cpp.BDMPhase_Rescan:
            self.lblDashModeBuild.setText( tr('Build Databases'), \
                                        size=4, bold=True, color='DisableFG')
            self.lblDashModeScan.setText( tr('Scanning Transaction History'), \
                                        size=4, bold=True, color='Foreground')
            self.lblTimeLeftBuild.setVisible(False)
            self.barProgressBuild.setFormat('')
            self.barProgressBuild.setValue(100)
            self.barProgressBuild.setRange(0,100)
            self.barProgressScan.setFormat('%p%')

         tleft15 = (int(tleft-1)/15 + 1)*15
         if tleft < 2:
            tstring = ''
            pvalue  = pct*100
         else:
            tstring = secondsToHumanTime(tleft15)
            pvalue = pct*100

         if phase==BDMPhase_BlockHeaders or phase==BDMPhase_BlockData or phase==BDMPhase_DBHeaders:
            self.lblTimeLeftBuild.setText(tstring)
            self.barProgressBuild.setValue(pvalue)
         elif phase==BDMPhase_Rescan:
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
            self.lblTimeLeftSync.setText(tr('Almost Done...'))
            self.barProgressSync.setValue(99)
         elif ssdm == 'BitcoindSynchronizing':
            sdmPercent = int(99.9*self.approxPctSoFar)
            if self.approxBlkLeft < 10000:
               if self.approxBlkLeft < 200:
                  self.lblTimeLeftSync.setText(tr('%(n)d blocks') % { 'n':self.approxBlkLeft})
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
      if func.lower() == 'scanning':
         return tr( \
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
         return tr( \
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
         return tr( \
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
      
      # A few states don't care which mgmtMode you are in...
      if state == 'NewUserInfo':
         return tr("""
         For more information about Armory, and even Bitcoin itself, you should
         visit the <a href="https://bitcoinarmory.com/faq/">frequently
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
         return tr( \
         '<p><b>You now have access to all the features Armory has to offer!</b><br>'
         'To see your balances and transaction history, please click '
         'on the "Transactions" tab above this text.  <br>'
         'Here\'s some things you can do with Armory Bitcoin Client:'
         '<br>')
      elif state == 'OnlineFull2':
         return ( \
         (tr('If you experience any performance issues with Armory, '
         'please confirm that Bitcoin-Qt is running and <i>fully '
         'synchronized with the Bitcoin network</i>.  You will see '
         'a green checkmark in the bottom right corner of the '
         'Bitcoin-Qt window if it is synchronized.  If not, it is '
         'recommended you close Armory and restart it only when you '
         'see that checkmark.'
         '<br><br>')  if not self.doAutoBitcoind else '') + tr(
         '<b>Please backup your wallets!</b>  Armory wallets are '
         '"deterministic", meaning they only need to be backed up '
         'one time (unless you have imported external addresses/keys). '
         'Make a backup and keep it in a safe place!  All funds from '
         'Armory-generated addresses will always be recoverable with '
         'a paper backup, any time in the future.  Use the "Backup '
         'Individual Keys" option for each wallet to backup imported '
         'keys.</p>'))
      elif state == 'OnlineNeedSweep':
         return tr( \
         'Armory is currently online, but you have requested a sweep operation '
         'on one or more private keys.  This requires searching the global '
         'transaction history for the available balance of the keys to be '
         'swept. '
         '<br><br>'
         'Press the button to start the blockchain scan, which '
         'will also put Armory into offline mode for a few minutes '
         'until the scan operation is complete')
      elif state == 'OnlineDirty':
         return tr( \
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
         return tr( \
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
            return tr( \
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
            return tr( \
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
            'href="https://bitcoinarmory.com/faq/">'
            'frequently asked questions</a> page for more general information.  '
            'If you already know what you\'re doing and simply need '
            'to fetch the latest version of Bitcoin-Qt, you can download it from '
            '<a href="http://www.bitcoin.org">http://www.bitcoin.org</a>.')
         elif state == 'OfflineNoInternet':
            return tr( \
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
            return tr( \
            'You are currently in offline mode because '
            'Armory could not find the blockchain files produced '
            'by Bitcoin-Qt.  Do you run Bitcoin-Qt (or bitcoind) '
            'from a non-standard directory?   Armory expects to '
            'find the blkXXXX.dat files in <br><br>%s<br><br> '
            'If you know where they are located, please restart '
            'Armory using the " --satoshi-datadir=[path]" '
            'to notify Armory where to find them.') % BLKFILE_DIR
         elif state == 'Disconnected':
            return tr( \
            'Armory was previously online, but the connection to Bitcoin-Qt/'
            'bitcoind was interrupted.  You will not be able to send bitcoins '
            'or confirm receipt of bitcoins until the connection is '
            'reestablished.  <br><br>Please check that Bitcoin-Qt is open '
            'and synchronized with the network.  Armory will <i>try to '
            'reconnect</i> automatically when the connection is available '
            'again.  If Bitcoin-Qt is available again, and reconnection does '
            'not happen, please restart Armory.<br><br>')
         elif state == 'ScanNoWallets':
            return tr( \
            'Please wait while the global transaction history is scanned. '
            'Armory will go into online mode automatically, as soon as '
            'the scan is complete.')
         elif state == 'ScanWithWallets':
            return tr( \
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
            return tr( \
            'It appears you are already running Bitcoin software '
            '(Bitcoin-Qt or bitcoind). '
            'Unlike previous versions of Armory, you should <u>not</u> run '
            'this software yourself --  Armory '
            'will run it in the background for you.  Either close the '
            'Bitcoin application or adjust your settings.  If you change '
            'your settings, then please restart Armory.')
         if state == 'OfflineNeedBitcoinInst':
            return tr( \
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
            msg = tr( \
            'The software is downloading and processing the latest activity '
            'on the network related to your wallet.  This should take only '
            'a few minutes.  While you wait, you can manage your wallets.  '
            '<br><br>'
            'Now would be a good time to make paper (or digital) backups of '
            'your wallet if you have not done so already!  You are protected '
            '<i>forever</i> from hard-drive loss, or forgetting you password. '
            'If you do not have a backup, you could lose all of your '
            'Bitcoins forever!  See the <a href="https://bitcoinarmory.com/">'
            'Armory Backups page</a> for more info.',
            'The software is downloading and processing the latest activity '
            'on the network related to your wallets.  This should take only '
            'a few minutes.  While you wait, you can manage your wallets.  '
            '<br><br>'
            'Now would be a good time to make paper (or digital) backups of '
            'your wallets if you have not done so already!  You are protected '
            '<i>forever</i> from hard-drive loss, or forgetting you password. '
            'If you do not have a backup, you could lose all of your '
            'Bitcoins forever!  See the <a href="https://bitcoinarmory.com/">'
            'Armory Backups page</a> for more info.',
               len(self.walletMap)
            )
            
            return msg
         if state == 'OnlineDisconnected':
            return tr( \
            'Armory\'s communication with the Bitcoin network was interrupted. '
            'This usually does not happen unless you closed the process that '
            'Armory was using to communicate with the network. Armory requires '
            '%(sdm)s to be running in the background, and this error pops up if it '
            'disappears.'
            '<br><br>You may continue in offline mode, or you can close '
            'all Bitcoin processes and restart Armory.') \
            % { 'sdm' : os.path.basename(TheSDM.executable) }
         if state == 'OfflineBadConnection':
            return tr( \
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
            return tr( \
            'Armory does not detect internet access, but it does detect '
            'running Bitcoin software.  Armory is in offline-mode. <br><br>'
            'If you are intending to run an offline system, you will not '
            'need to have the Bitcoin software installed on the offline '
            'computer.  It is only needed for the online computer. '
            'If you expected to be online and '
            'the absence of internet is an error, please restart Armory '
            'using the "--skip-online-check" option.  ')
         if state == 'OfflineForcedButSatoshiAvail':
            return tr( \
            'Armory was started in offline-mode, but detected you are '
            'running Bitcoin software.  If you are intending to run an '
            'offline system, you will <u>not</u> need to have the Bitcoin '
            'software installed or running on the offline '
            'computer.  It is only required for being online. ')
         if state == 'OfflineBadDBEnv':
            return tr( \
            'The Bitcoin software indicates there '
            'is a problem with its databases.  This can occur when '
            'Bitcoin-Qt/bitcoind is upgraded or downgraded, or sometimes '
            'just by chance after an unclean shutdown.'
            '<br><br>'
            'You can either revert your installed Bitcoin software to the '
            'last known working version (but not earlier than version 0.8.1) '
            'or delete everything <b>except</b> "wallet.dat" from the your Bitcoin '
            'home directory:<br><br>'
            '<font face="courier"><b>%(satoshipath)s</b></font>'
            '<br><br>'
            'If you choose to delete the contents of the Bitcoin home '
            'directory, you will have to do a fresh download of the blockchain '
            'again, which will require a few hours the first '
            'time.') % { 'satoshipath' : self.satoshiHomePath }
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

   # TODO - move out of polling and call on events
   #############################################################################

   def setDashboardDetails(self, INIT=False):
      """
      We've dumped all the dashboard text into the above 2 methods in order
      to declutter this method.
      """
      if self.isShuttingDown:
         return

      sdmState = TheSDM.getSDMState()
      bdmState = TheBDM.getState()
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

      # This keeps popping up for some reason!
      self.lblTorrentStats.setVisible(False)

      if self.doAutoBitcoind and not sdmState=='BitcoindReady':
         # User is letting Armory manage the Satoshi client for them.
         # TODO -  Move to event handlers
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

            if self.internetStatus == INTERNET_STATUS.Unavailable or CLI_OPTIONS.offline:
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)
               setOnlyDashModeVisible()
               self.lblDashModeSync.setText( tr('Armory is <u>offline</u>'), \
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
                     tr('In case you actually do have internet access, you can use '
                     'the following links to get Armory installed.  Or change '
                     'your settings.'))
                  setBtnRowVisible(DASHBTNS.Browse, True)
                  setBtnRowVisible(DASHBTNS.Install, True)
                  setBtnRowVisible(DASHBTNS.Settings, True)
                  #setBtnRowVisible(DASHBTNS.Instruct, not OS_WINDOWS)
                  descr1 += self.GetDashStateText('Auto','OfflineNoSatoshiNoInternet')
                  descr2 += self.GetDashFunctionalityText(tr('Offline'))
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
            elif not TheSDM.isRunningBitcoind() and not TheTDM.isRunning():
               setOnlyDashModeVisible()
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)
               self.lblDashModeSync.setText( tr('Armory is <u>offline</u>'), \
                                            size=4, color='TextWarn', bold=True)
               # Bitcoind is not being managed, but we want it to be
               if satoshiIsAvailable() or sdmState=='BitcoindAlreadyRunning':
                  # But bitcoind/-qt is already running
                  LOGINFO('Dashboard switched to auto-butSatoshiRunning')
                  self.lblDashModeSync.setText(tr(' Please close Bitcoin-Qt'), \
                                                         size=4, bold=True)
                  setBtnFrameVisible(True, '')
                  setBtnRowVisible(DASHBTNS.Close, True)
                  self.btnModeSwitch.setVisible(True)
                  self.btnModeSwitch.setText(tr('Check Again'))
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
                     self.lblDashModeSync.setText(tr('Cannot find Bitcoin Installation'), \
                                                         size=4, bold=True)
                  else:
                     self.lblDashModeSync.setText(tr('Cannot find Bitcoin Home Directory'), \
                                                         size=4, bold=True)
                  setBtnRowVisible(DASHBTNS.Close, satoshiIsAvailable())
                  setBtnRowVisible(DASHBTNS.Install, True)
                  setBtnRowVisible(DASHBTNS.Browse, True)
                  setBtnRowVisible(DASHBTNS.Settings, True)
                  #setBtnRowVisible(DASHBTNS.Instruct, not OS_WINDOWS)
                  self.btnModeSwitch.setVisible(True)
                  self.btnModeSwitch.setText(tr('Check Again'))
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
                  self.lblDashModeSync.setText( tr('Armory is <u>offline</u>'), \
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
                     tr('Try reinstalling the Bitcoin '
                     'software then restart Armory.  If you continue to have '
                     'problems, please contact Armory\'s core developer at '
                     '<a href="mailto:support@bitcoinarmory.com?Subject=Bitcoind%20Crash"'
                     '>support@bitcoinarmory.com</a>.'))
                  setBtnRowVisible(DASHBTNS.Settings, True)
                  setBtnRowVisible(DASHBTNS.Install, True)
                  LOGINFO('Dashboard switched to auto-BtcdCrashed')
                  self.lblDashModeSync.setText( tr('Armory is <u>offline</u>'), \
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
                  self.lblDashModeSync.setText( tr('Armory is <u>offline</u>'), \
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
                     self.lblDashModeTorrent.setText(tr('Downloading via Armory CDN'), \
                                          size=4, bold=True, color='Foreground')
                     self.lblDashModeSync.setText( tr('Synchronizing with Network'), \
                                          size=4, bold=True, color='DisableFG')
                     self.lblTorrentStats.setVisible(True)
                  elif sdmState=='BitcoindInitializing':
                     self.lblDashModeTorrent.setText(tr('Download via Armory CDN'), \
                                          size=4, bold=True, color='DisableFG')
                     self.lblDashModeSync.setText( tr('Initializing Bitcoin Engine'), \
                                              size=4, bold=True, color='Foreground')
                     self.lblTorrentStats.setVisible(False)
                  else:
                     self.lblDashModeTorrent.setText(tr('Download via Armory CDN'), \
                                          size=4, bold=True, color='DisableFG')
                     self.lblDashModeSync.setText( 'Synchronizing with Network', \
                                              size=4, bold=True, color='Foreground')
                     self.lblTorrentStats.setVisible(False)


                  self.lblDashModeBuild.setText( tr('Build Databases'), \
                                              size=4, bold=True, color='DisableFG')
                  self.lblDashModeScan.setText( tr('Scan Transaction History'), \
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
                     tr('Since version 0.88, Armory runs bitcoind in the '
                     'background.  You can switch back to '
                     'the old way in the Settings dialog. '))

                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
      else:
         # User is managing satoshi client, or bitcoind is already sync'd
         self.frmDashMidButtons.setVisible(False)
         if bdmState in (BDM_OFFLINE, BDM_UNINITIALIZED):
            if self.internetStatus == INTERNET_STATUS.Unavailable:
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)
               setOnlyDashModeVisible()
               self.lblBusy.setVisible(False)
               self.btnModeSwitch.setVisible(False)
               self.btnModeSwitch.setEnabled(False)
               self.lblDashModeSync.setText( tr('Armory is <u>offline</u>'), \
                                         size=4, color='TextWarn', bold=True)

               if not satoshiIsAvailable():
                  descr = self.GetDashStateText('User','OfflineNoSatoshiNoInternet')
               else:
                  descr = self.GetDashStateText('User', 'OfflineNoInternet')

               descr += '<br><br>'
               descr += self.GetDashFunctionalityText('Offline')
               self.lblDashDescr1.setText(descr)
            else:
               LOGINFO('Dashboard switched to user-OfflineOnlinePoss')
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)
               setOnlyDashModeVisible()
               self.lblBusy.setVisible(False)
               self.lblDashModeSync.setText(tr('Armory is <u>offline</u>'), size=4, bold=True)
               descr  = self.GetDashStateText('User', 'OfflineButOnlinePossible')
               descr += self.GetDashFunctionalityText('Offline')
               self.lblDashDescr1.setText(descr)
               
               if not satoshiIsAvailable():
                  descr = self.GetDashStateText('User','OfflineNoSatoshi')
                  setBtnRowVisible(DASHBTNS.Settings, True)
                  setBtnFrameVisible(True, \
                     tr('If you would like Armory to manage the Bitcoin software '
                     'for you (Bitcoin-Qt or bitcoind), then adjust your '
                     'Armory settings, then restart Armory.'))
                  descr = self.GetDashStateText('User','OfflineNoSatoshiNoInternet')
               else:
                  self.btnModeSwitch.setVisible(True)
                  self.btnModeSwitch.setEnabled(True)
                  self.btnModeSwitch.setText(tr('Go Online!'))
                  descr = self.GetDashStateText('User', 'OfflineNoInternet')

               descr += '<br><br>'
               descr += self.GetDashFunctionalityText('Offline')
               self.lblDashDescr1.setText(descr)

         elif bdmState == BDM_BLOCKCHAIN_READY:
            setOnlyDashModeVisible()
            self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, True)
            self.lblBusy.setVisible(False)
            if self.netMode == NETWORKMODE.Disconnected:
               self.btnModeSwitch.setVisible(False)
               self.lblDashModeSync.setText( tr('Armory is disconnected'), size=4, color='TextWarn', bold=True)
               descr  = self.GetDashStateText('User','Disconnected')
               descr += self.GetDashFunctionalityText('Offline')
               self.lblDashDescr1.setText(descr)
            else:
               # Fully online mode
               self.btnModeSwitch.setVisible(False)
               self.lblDashModeSync.setText( tr('Armory is online!'), color='TextGreen', size=4, bold=True)
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, True)
               descr  = self.GetDashStateText('User', 'OnlineFull1')
               descr += self.GetDashFunctionalityText('Online')
               descr += self.GetDashStateText('User', 'OnlineFull2')
               self.lblDashDescr1.setText(descr)
            #self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Dash)
         elif bdmState == BDM_SCANNING:
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
               self.lblDashModeSync.setText( tr('Synchronizing with Network'), \
                                       size=4, bold=True, color='DisableFG')
            else:
               self.barProgressSync.setVisible(False)
               self.lblTimeLeftSync.setVisible(False)
               self.lblDashModeSync.setVisible(False)

            if len(str(self.lblDashModeBuild.text()).strip()) == 0:
               self.lblDashModeBuild.setText( tr('Preparing Databases'), \
                                          size=4, bold=True, color='Foreground')

            if len(str(self.lblDashModeScan.text()).strip()) == 0:
               self.lblDashModeScan.setText( tr('Scan Transaction History'), \
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

   def checkNewZeroConf(self, ledgers):
      '''
      Function that looks at an incoming zero-confirmation transaction queue and
      determines if any incoming transactions were created by Armory. If so, the
      transaction will be passed along to a user notification queue.
      '''
      for le in ledgers:
         notifyIn = self.getSettingOrSetDefault('NotifyBtcIn', \
                                                      not OS_MACOSX)
         notifyOut = self.getSettingOrSetDefault('NotifyBtcOut', \
                                                       not OS_MACOSX)
         if (le.getValue() <= 0 and notifyOut) or \
                  (le.getValue() > 0 and notifyIn):
                  # notifiedAlready = False, 
            self.notifyQueue.append([le.getWalletID(), le, False])
               
      self.createCombinedLedger()
      self.walletModel.reset()
      self.lockboxLedgModel.reset()

   #############################################################################
   def handleCppNotification(self, action, args):

      if action == FINISH_LOAD_BLOCKCHAIN_ACTION:
         #Blockchain just finished loading, finish initializing UI and render the
         #ledgers
         
         self.blkReceived = RightNow()
         if self.needUpdateAfterScan:
            LOGDEBUG('Running finishLoadBlockchain')
            self.finishLoadBlockchainGUI()
            self.needUpdateAfterScan = False
            self.setDashboardDetails()
     
      elif action == NEW_ZC_ACTION:
         #A zero conf Tx conerns one of the address Armory is tracking, pull the 
         #updated ledgers from the BDM and create the related notifications.         

         self.checkNewZeroConf(args)        

      elif action == NEW_BLOCK_ACTION:
         #A new block has appeared, pull updated ledgers from the BDM, display
         #the new block height in the status bar and note the block received time         

         newBlocks = args[0]
         if newBlocks>0:       
            print 'New Block: ', TheBDM.getTopBlockHeight()

            self.ledgerModel.reset()

            LOGINFO('New Block! : %d', TheBDM.getTopBlockHeight())

            self.createCombinedLedger()
            self.blkReceived  = RightNow()
            self.writeSetting('LastBlkRecvTime', self.blkReceived)
            self.writeSetting('LastBlkRecv',     TheBDM.getTopBlockHeight())

            if self.netMode==NETWORKMODE.Full:
               LOGINFO('Current block number: %d', TheBDM.getTopBlockHeight())
               self.lblArmoryStatus.setText(\
                  tr('<font color=%(color)s>Connected (%(hgt)s blocks)</font> ') % \
                  { 'color' : htmlColor('TextGreen'), 'hgt' : TheBDM.getTopBlockHeight()})

            # Update the wallet view to immediately reflect new balances
            self.walletModel.reset()    
      elif action == REFRESH_ACTION:
         #The wallet ledgers have been updated from an event outside of new ZC
         #or new blocks (usually a wallet or address was imported, or the 
         #wallet filter was modified
         reset  = False
         if len(args) == 0:
            self.createCombinedLedger()
            return
         
         for wltID in args:
            if len(wltID) > 0:
               if wltID in self.walletMap:
                  wlt = self.walletMap[wltID]                  
                  wlt.isEnabled = True
                  self.walletModel.reset()                  
                  wlt.doAfterScan()                  
                  self.changeWltFilter()              

               elif wltID in self.lockboxIDMap:
                  lbID = self.lockboxIDMap[wltID]                
                  self.allLockboxes[lbID].isEnabled = True
                  
                  if self.lbDialogModel != None:
                     self.lbDialogModel.reset()
                 
                  if self.lbDialog != None:
                     self.lbDialog.changeLBFilter()               
               
               elif wltID == "wallet_filter_changed":
                  reset = True
                        
               if self.walletSideScanProgress.has_key(wltID):
                  del self.walletSideScanProgress[wltID]
               
         self.createCombinedLedger(reset)

      elif action == 'progress':
         #Received progress data for a wallet side scan
         wltIDList = args[0]
         prog = args[1]
         
         hasWallet = False
         hasLockbox = False
         for wltID in wltIDList:
            self.walletSideScanProgress[wltID] = prog*100
            
            if wltID in self.walletMap:
               hasWallet = True
            else:
               hasLockbox = True

                
         if hasWallet:
            self.walletModel.reset()   
         
         if hasLockbox:
            self.lockboxLedgModel.reset()
            if self.lbDialogModel != None:
               self.lbDialogModel.reset()                     
               
      elif action == WARNING_ACTION:
         #something went wrong on the C++ side, create a message box to report
         #it to the user
         if 'rescan' in args[0].lower() or 'rebuild' in args[0].lower():
            result = MsgBoxWithDNAA(self, self, MSGBOX.Critical, 'BDM error!', args[0], 
                                    "Rebuild and rescan on next start", dnaaStartChk=False)
            if result[1] == True:
               touchFile( os.path.join(ARMORY_HOME_DIR, 'rebuild.flag') )
         
         elif 'factory reset' in args[0].lower():
            result = MsgBoxWithDNAA(self, self, MSGBOX.Critical, 'BDM error!', args[0], 
                                    "Factory reset on next start", dnaaStartChk=False)
            if result[1] == True:
               DlgFactoryReset(self, self).exec_()           
         
         else:   
            QMessageBox.critical(self, tr('BlockDataManager Warning'), \
                              tr(args[0]), \
                              QMessageBox.Ok) 
         #this is a critical error reporting channel, should kill the app right
         #after
         os._exit(0) 
      
      elif action == SCAN_ACTION:
         wltIDList = args[0]
         
         hasWallet = False
         hasLockbox = False
         
         for wltID in wltIDList:
            self.walletSideScanProgress[wltID] = 0    
            if len(wltID) > 0:
               if wltID in self.walletMap:
                  wlt = self.walletMap[wltID]                
                  wlt.disableWalletUI()
                  if wltID in self.walletDialogDict:
                     self.walletDialogDict[wltID].reject()
                     del self.walletDialogDict[wltID]
                  
                  hasWallet = True
                  
               else:
                  lbID = self.lockboxIDMap[wltID]                
                  self.allLockboxes[lbID].isEnabled = False
                  hasLockbox = True
         
         if hasWallet:
            self.changeWltFilter()  
            
         if hasLockbox:
            if self.lbDialogModel != None:
               self.lbDialogModel.reset()       
                    
            if self.lbDialog != None:
               self.lbDialog.resetLBSelection()   
               self.lbDialog.changeLBFilter()                           
                 
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
      bdmState = TheBDM.getState()

      self.heartbeatCount += 1
      if self.heartbeatCount % 60 == 20:
         self.processAnnounceData()
         self.processAlerts()

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
            if TheTDM.isRunning():    # TODO Put this whole conditional block in a method
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

            if (sdmState in ['BitcoindInitializing','BitcoindSynchronizing']) or \
               (sdmState == 'BitcoindReady' and bdmState==BDM_SCANNING):
               self.updateSyncProgress()
               
         else:
            if bdmState in (BDM_OFFLINE,BDM_UNINITIALIZED):
               # This call seems out of place, but it's because if you are in offline
               # mode, it needs to check periodically for the existence of Bitcoin-Qt
               # so that it can enable the "Go Online" button
               self.setDashboardDetails()
               return
            elif bdmState==BDM_SCANNING:  # TODO - Move to handle cpp notification
               self.updateSyncProgress()


         if self.netMode==NETWORKMODE.Disconnected:
            if self.isOnlineModePossible():
               self.switchNetworkMode(NETWORKMODE.Full)


         if bdmState==BDM_BLOCKCHAIN_READY:
            # Trigger any notifications, if we have them... TODO - Remove add to new block, and block chain ready
            self.doTheSystemTrayThing()

            # Any extra functions that may have been injected to be run TODO - Call on New block
            # when new blocks are received.  
            if len(self.extraNewBlockFunctions) > 0:
               cppHead = TheBDM.getMainBlockFromDB(self.currBlockNum)
               pyBlock = PyBlock().unserialize(cppHead.getSerializedBlock())
               for blockFunc in self.extraNewBlockFunctions:
                  blockFunc(pyBlock)


            blkRecvAgo  = RightNow() - self.blkReceived
            #blkStampAgo = RightNow() - TheBDM.blockchain().top().getTimestamp()  # TODO - show absolute time, and show only on new block
            self.lblArmoryStatus.setToolTip(tr('Last block received is %(time)s ago') % \
                                                { 'time' : secondsToHumanTime(blkRecvAgo) })

            # TODO - remove
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
            dispName = tr('"%(name)s"') % { 'name' : wlt.labelName }
         else:
            dispName = tr('"%(shortname)s..."') % { 'shortname' : wlt.labelName[:17] }
         dispName = tr('Wallet %(n)s (%(id)s)') % { 'n' : dispName, 'id':wlt.uniqueIDB58}
      elif moneyID in self.cppLockboxWltMap:
         lbox = self.getLockboxByID(moneyID)
         if len(lbox.shortName) <= 20:
            dispName = '%(M)d-of-%(N)d "%(shortname)s"' % { 'M' : lbox.M, 'N' : lbox.N, 'shortname' : lbox.shortName}
         else:
            dispName = tr('%(M)d-of-%(N)d "%(shortname)s..."') % {'M' : lbox.M, 'N' : lbox.N, 'shortname' : lbox.shortName[:17] }
         dispName = tr('Lockbox %(name)s (%(id)s)') % { 'name' : dispName, 'id' : lbox.uniqueIDB58 }
      else:
         LOGERROR('Asked to show notification for wlt/lbox we do not have')
         return

      # Collected everything we need to display, now construct it and do it.
      if ledgerAmt > 0:
         # Received!
         title = tr('Bitcoins Received!')
         dispLines.append(tr('Amount:  %(total)s BTC') % { 'total' : totalStr })
         dispLines.append(tr('Recipient:  %(recp)s') % { 'recp' : dispName } )
      elif ledgerAmt < 0:
         # Sent!
         title = tr('Bitcoins Sent!')
         dispLines.append(tr('Amount:  %(tot)s BTC') % { 'tot' : totalStr })
         dispLines.append(tr('Sender:  %(disp)s') % { 'disp' : dispName })

      self.showTrayMsg(title, '\n'.join(dispLines), \
                       QSystemTrayIcon.Information, 10000)
      LOGINFO(title)


   #############################################################################

   def doTheSystemTrayThing(self):
      """
      I named this method as it is because this is not just "show a message."
      I need to display all relevant transactions, in sequence that they were
      received.  I will store them in self.notifyQueue, and this method will
      do nothing if it's empty.
      """
      if not TheBDM.getState()==BDM_BLOCKCHAIN_READY or \
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
            wltName = tr('Wallet "%(wname)s" (%(moneyID)s)') % { 'wname': wname, 'moneyID' : moneyID }
         else:
            cppWlt = self.cppLockboxWltMap[moneyID]
            lbox   = self.getLockboxByID(moneyID)
            M      = self.getLockboxByID(moneyID).M
            N      = self.getLockboxByID(moneyID).N
            lname  = self.getLockboxByID(moneyID).shortName
            if len(lname) > 20:
               lname = lname[:17] + '...'
            wltName = tr('Lockbox %(M)d-of-%(N)d "%(lname)s" (%(id)s)') % { 'M' : M, 'N' : N, 'lname' : lname, 'id' : moneyID }

         if le.isSentToSelf():
            # Used to display the sent-to-self amount, but if this is a lockbox
            # we only have a cppWallet, and the determineSentToSelfAmt() func
            # only operates on python wallets.  Oh well, the user can double-
            # click on the tx in their ledger if they want to see what's in it.
            # amt = determineSentToSelfAmt(le, cppWlt)[0]
            # self.showTrayMsg('Your bitcoins just did a lap!', \
            #             'Wallet "%s" (%s) just sent %s BTC to itself!' % \
            #         (wlt.labelName, moneyID, coin2str(amt,maxZeros=1).strip()),
            self.showTrayMsg(tr('Your bitcoins just did a lap!'), \
                             tr('%(wltName)s just sent some BTC to itself!') % { 'wltName' : wltName }, \
                             QSystemTrayIcon.Information, 10000)
            return

         # If coins were either received or sent from the loaded wlt/lbox         
         dispLines = []
         totalStr = coin2strNZS(abs(le.getValue()))
         if le.getValue() > 0:
            title = tr('Bitcoins Received!')
            dispLines.append(tr('Amount:  %(tot)s BTC') % { 'tot' : totalStr })
            dispLines.append(tr('From:    %(wlt)s') % { 'wlt' : wltName })
         elif le.getValue() < 0:
            # Also display the address of where they went
            txref = TheBDM.bdv().getTxByHash(le.getTxHash())
            nOut = txref.getNumTxOut()
            recipStr = ''
            for i in range(nOut):
               script = txref.getTxOutCopy(i).getScript()
               if cppWlt.hasScrAddress(script_to_scrAddr(script)):
                  continue
               if len(recipStr)==0:
                  recipStr = self.getDisplayStringForScript(script, 45)['String']
               else:
                  recipStr = tr('<Multiple Recipients>')
            
            title = tr('Bitcoins Sent!')
            dispLines.append(tr('Amount:  %(tot)s BTC') % { 'tot' : totalStr })
            dispLines.append(tr('From:    %(wlt)s') % { 'wlt' : wltName })
            dispLines.append(tr('To:      %(recp)s') % { 'recp' : recipStr })
   
         self.showTrayMsg(title, '\n'.join(dispLines), \
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
         reply,remember = MsgBoxWithDNAA(self, self, MSGBOX.Question, tr('Minimize or Close'), \
            tr('Would you like to minimize Armory to the system tray instead '
            'of closing it?'), dnaaMsg=tr('Remember my answer'), \
            yesStr=tr('Minimize'), noStr=tr('Close'))
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
         self.closeForReal()
         event.ignore()
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
   def closeForReal(self):
      '''
      Unlike File->Quit or clicking the X on the window, which may actually
      minimize Armory, this method is for *really* closing Armory
      '''
      
      self.setCursor(Qt.WaitCursor)
      self.showShuttingDownMessage()
      
      try:
         # Save the main window geometry in the settings file
         self.writeSetting('MainGeometry',   str(self.saveGeometry().toHex()))
         self.writeSetting('MainWalletCols', saveTableView(self.walletsView))
         self.writeSetting('MainLedgerCols', saveTableView(self.ledgerView))

         if TheBDM.getState()==BDM_SCANNING:
            LOGINFO('BDM state is scanning -- force shutdown BDM')
         else:
            LOGINFO('BDM is safe for clean shutdown')

         #no callback notify in offline mode, just exit
         if TheBDM.getState() in (BDM_OFFLINE,BDM_UNINITIALIZED):
            self.actuallyDoExitNow(STOPPED_ACTION, 1)
            return
         
         self.shutdownBitcoindThread = threading.Thread(target=TheSDM.stopBitcoind)
         self.shutdownBitcoindThread.start()
         
         TheBDM.registerCppNotification(self.actuallyDoExitNow)
         TheBDM.beginCleanShutdown()

         # Remove Temp Modules Directory if it exists:
         if self.tempModulesDirName:
            shutil.rmtree(self.tempModulesDirName)
      except:
         # Don't want a strange error here interrupt shutdown
         LOGEXCEPT('Strange error during shutdown')


   def actuallyDoExitNow(self, action, l):
      # this is a BDM callback
      if action != STOPPED_ACTION:
         return
      # Any extra shutdown activities, perhaps added by modules
      for fn in self.extraShutdownFunctions:
         try:
            fn()
         except:
            LOGEXCEPT('Shutdown function failed.  Skipping.')

      
      # This will do nothing if bitcoind isn't running.
      try:
         self.shutdownBitcoindThread.join()
      except:
         pass

      

      from twisted.internet import reactor
      LOGINFO('Attempting to close the main window!')
      reactor.stop()
    

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
         self.emit(SIGNAL('UWCS'), [1, tr('All wallets are consistent'), 10000, dlgrdy])
         self.emit(SIGNAL('checkForNegImports'))
      else:
         while not dlgrdy:
            self.emit(SIGNAL('UWCS'), [1, tr('Consistency Check Failed!'), 0, dlgrdy])
            time.sleep(1)

         self.checkRdyForFix()


   def checkRdyForFix(self):
      #check BDM first
      time.sleep(1)
      self.dlgCptWlt.emit(SIGNAL('Show'))
      while 1:
         if TheBDM.getState() == BDM_SCANNING:
            canFix = tr("""
               The wallet analysis tool will become available
               as soon as Armory is done loading.   You can close this 
               window and it will reappear when ready.""")
            self.dlgCptWlt.UpdateCanFix([canFix])
            time.sleep(1)
         elif TheBDM.getState() == BDM_OFFLINE or \
              TheBDM.getState() == BDM_UNINITIALIZED:
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
                  <b>The following dialogs need closed before you can 
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
         self.pbarWalletProgress.setFormat(tr('Wallet Consistency Check: %p%'))
         self.pbarWalletProgress.setValue(0)
         self.statusBar().addWidget(self.pbarWalletProgress)

         self.connect(self, SIGNAL('UWCS'), self.UpdateWalletConsistencyStatus)
         self.connect(self, SIGNAL('PWCE'), self.PromptWltCstError)
         self.CheckWalletConsistency(self.walletMap, self.prgAt, async=True)
         self.UpdateConsistencyCheckMessage(async = True)
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
      
   #############################################################################
   def cppNotifySignal(self, action, arg):
      self.emit(SIGNAL('cppNotify'), action, arg)
      
   #############################################################################
   def loadNewPage(self):
      pageInt = int(self.PageLineEdit.text())
      
      
      if pageInt == self.mainLedgerCurrentPage:
         return
      
      if pageInt < 0 or pageInt > TheBDM.bdv().getWalletsPageCount():
         self.PageLineEdit.setText(str(self.mainLedgerCurrentPage))
         return
      
      previousPage = self.mainLedgerCurrentPage
      try:
         self.mainLedgerCurrentPage = pageInt   
         self.createCombinedLedger()
      except:
         self.mainLedgerCurrentPage = previousPage
         self.PageLineEdit.setText(str(self.mainLedgerCurrentPage))

   #############################################################################
   # System tray notifications require specific code for OS X. We'll handle
   # messages here to hide the ugliness.
   def showTrayMsg(self, dispTitle, dispText, dispIconType, dispTime):
      if not OS_MACOSX:
         self.sysTray.showMessage(dispTitle, dispText, dispIconType, dispTime)
      else:
         if self.notifCtr == ArmoryMac.MacNotificationHandler.BuiltIn:
            self.macNotifHdlr.showNotification(dispTitle, dispText)
         elif (self.notifCtr == ArmoryMac.MacNotificationHandler.Growl12) or \
              (self.notifCtr == ArmoryMac.MacNotificationHandler.Growl13):
            self.macNotifHdlr.notifyGrowl(dispTitle, dispText, QIcon(self.iconfile))
            
   #############################################################################
   def method_signal(self, method):
      method()   
   #############################################################################      
   def bdv(self):
      return TheBDM.bdv()
   
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
      if hasattr(proc, '_name'):
         pname = str(proc._name)
      elif hasattr(proc, 'name'):
         pname = str(proc.name)
      else:
         raise 'psutil.process has no known name field!'
         
      if aexe in pname:
         LOGINFO('Found armory PID: %d', proc.pid)
         armoryExists.append(proc.pid)
      if bexe in pname:
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
   SPLASH = ArmorySplashScreen(pixLogo)
   SPLASH.setMask(pixLogo.mask())
   
   SPLASH.show()
   QAPP.processEvents()

   # Will make this customizable
   QAPP.setFont(GETFONT('var'))

   form = ArmoryMainWindow(splashScreen=SPLASH)
   form.show()

   SPLASH.finish(form)

   from twisted.internet import reactor
   def endProgram():
      if reactor.threadpool is not None:
         reactor.threadpool.stop()
      QAPP.quit()

   reactor.addSystemEventTrigger('before', 'shutdown', endProgram)
   QAPP.setQuitOnLastWindowClosed(True)
   reactor.runReturn()
   os._exit(QAPP.exec_())
