#!/usr/bin/python2
# -*- coding: UTF-8 -*-
##############################################################################
#                                                                            #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                         #
# Distributed under the GNU Affero General Public License (AGPL v3)          #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                       #
#                                                                            #
# Copyright (C) 2016-17, goatpig                                             #
#  Distributed under the MIT license                                         #
#  See LICENSE-MIT or https://opensource.org/licenses/MIT                    #                                   
#                                                                            #
##############################################################################
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
import glob


from PyQt4.QtCore import *
from PyQt4.QtGui import *
import psutil

import CppBlockUtils as Cpp
from armorycolors import Colors, htmlColor, QAPP
from armoryengine.ALL import *
from armoryengine.Block import PyBlock
from armoryengine.Decorators import RemoveRepeatingExtensions
from armoryengine.PyBtcWalletRecovery import WalletConsistencyCheck
from SDM import SatoshiDaemonManager

from ui.QtExecuteSignal import QtExecuteSignal

# Setup translations
translator = QTranslator(QAPP)

app_dir = "./"
try:
   app_dir = os.path.dirname(os.path.realpath(__file__))
except:
   if OS_WINDOWS and getattr(sys, 'frozen', False):
      app_dir = os.path.dirname(sys.executable) 
      
translator.load(GUI_LANGUAGE, os.path.join(app_dir, "lang/"))
QAPP.installTranslator(translator)

from armorymodels import *
from jasvet import verifySignature
import qrc_img_resources
from qtdefines import *
from qtdialogs import *
from ui.MultiSigDialogs import DlgSelectMultiSigOption, DlgLockboxManager, \
                    DlgMergePromNotes, DlgCreatePromNote, DlgImportAsciiBlock
from ui.Wizards import WalletWizard, TxWizard
from ui.toolsDialogs import MessageSigningVerificationDialog
from dynamicImport import MODULE_PATH_KEY, ZIP_EXTENSION, getModuleList, importModule,\
   verifyZipSignature, MODULE_ZIP_STATUS, INNER_ZIP_FILENAME,\
   MODULE_ZIP_STATUS_KEY, getModuleListNoZip, dynamicImportNoZip
import tempfile

# Set URL handler to warn before opening url
handler = URLHandler()
QDesktopServices.setUrlHandler("http", handler.handleURL) 
QDesktopServices.setUrlHandler("https", handler.handleURL) 

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
   QApplication.setDesktopSettingsAware(False)

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
      elif USE_REGTEST:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [REGTEST] dlgMain')
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
         if USE_TESTNET or USE_REGTEST:
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
      self.lastSDMStr = ""
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
      self.wasSynchronizing = False
      self.entropyAccum = []
      self.allLockboxes = []
      self.lockboxIDMap = {}
      self.cppLockboxWltMap = {}
      self.broadcasting = {}
      
      self.nodeStatus = None
      self.numHeartBeat = 0

      # Error and exit on both regtest and testnet
      if USE_TESTNET and USE_REGTEST:
         DlgRegAndTest(self, self).exec_()

      # Full list of notifications, and notify IDs that should trigger popups
      # when sending or receiving.
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
      self.tempModulesDirName = None
      self.internetStatus = None

      self.lockboxLedgModel = None

      #delayed URI parsing dict
      self.delayedURIData = {}
      self.delayedURIData['qLen'] = 0

      #Setup the signal to spawn progress dialogs from the main thread
      self.connect(self, SIGNAL('initTrigger') , self.initTrigger)
      self.connect(self, SIGNAL('execTrigger'), self.execTrigger)
      self.connect(self, SIGNAL('checkForNegImports'), self.checkForNegImports)

      '''
      With Qt, all GUI operations need to happen in the main thread. If 
      the GUI operation is triggered from another thread, it needs to 
      emit a Qt signal, so that Qt can schedule the operation in the main
      thread. QtExecuteSignal is a utility class that handles the signaling
      and delaying/threading of execution
      '''
      self.signalExecution = QtExecuteSignal(self)

      #push model BDM notify signal
      def cppNotifySignal(action, arglist):
         self.signalExecution.executeMethod(\
            self.handleCppNotification, action, arglist)
         
      TheBDM.registerCppNotification(cppNotifySignal)

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
         
      armoryengine.ArmoryUtils.DEFAULT_ADDR_TYPE = \
         self.getSettingOrSetDefault('Default_ReceiveType', 'P2PKH')


      if not self.abortLoad:
         self.acquireProcessMutex()

      # acquireProcessMutex may have set this flag if something went wrong
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
      
      self.oneTimeScanAction = {}

      self.walletDialogDict = {}

      self.lblArmoryStatus = QRichLabel_AutoToolTip(self.tr('<font color=%1>Offline</font> ').arg(htmlColor('TextWarn')), doWrap=False)

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

      btnAddWallet  = QPushButton(self.tr("Create Wallet"))
      btnImportWlt  = QPushButton(self.tr("Import or Restore Wallet"))
      self.connect(btnAddWallet,  SIGNAL('clicked()'), self.startWalletWizard)
      self.connect(btnImportWlt,  SIGNAL('clicked()'), self.execImportWallet)

      # Put the Wallet info into it's own little box
      lblAvail = QLabel(self.tr("<b>Available Wallets:</b>"))
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

      self.connect(self.comboWltSelect, SIGNAL('activated(int)'),
                   self.changeWltFilter)


      self.lblTot  = QRichLabel(self.tr('<b>Maximum Funds:</b>'), doWrap=False);
      self.lblSpd  = QRichLabel(self.tr('<b>Spendable Funds:</b>'), doWrap=False);
      self.lblUcn  = QRichLabel(self.tr('<b>Unconfirmed:</b>'), doWrap=False);

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
      self.ttipTot = self.createToolTipWidget( self.tr(
            'Funds if all current transactions are confirmed. '
            'Value appears gray when it is the same as your spendable funds.'))
      self.ttipSpd = self.createToolTipWidget( self.tr('Funds that can be spent <i>right now</i>'))
      self.ttipUcn = self.createToolTipWidget( self.tr(
            'Funds that have less than 6 confirmations, and thus should not '
            'be considered <i>yours</i>, yet.'))

      self.frmTotals = QFrame()
      self.frmTotals.setFrameStyle(STYLE_NONE)
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

      self.frmTotals.setLayout(frmTotalsLayout)

      # Add the available tabs to the main tab widget
      self.MAINTABS  = enum('Dash','Ledger')

      self.mainDisplayTabs.addTab(self.tabDashboard, self.tr('Dashboard'))

      ##########################################################################
      if not CLI_OPTIONS.disableModules:
         if USE_TESTNET or USE_REGTEST:
            self.loadArmoryModulesNoZip()
      # Armory Modules are diabled on main net. If enabled it uses zip files to
      # contain the modules
      #   else:
      #      self.loadArmoryModules()
      ##########################################################################

      self.lbDialog = None

      btnSendBtc   = QPushButton(self.tr("Send Bitcoins"))
      btnRecvBtc   = QPushButton(self.tr("Receive Bitcoins"))
      btnWltProps  = QPushButton(self.tr("Wallet Properties"))
      btnOfflineTx = QPushButton(self.tr("Offline Transactions"))
      btnMultisig  = QPushButton(self.tr("Lockboxes (Multi-Sig)"))

      self.connect(btnWltProps, SIGNAL('clicked()'), self.execDlgWalletDetails)
      self.connect(btnRecvBtc,  SIGNAL('clicked()'), self.clickReceiveCoins)
      self.connect(btnSendBtc,  SIGNAL('clicked()'), self.clickSendBitcoins)
      self.connect(btnOfflineTx,SIGNAL('clicked()'), self.execOfflineTx)
      self.connect(btnMultisig, SIGNAL('clicked()'), self.browseLockboxes)

      verStr = 'Armory %s / %s' % (getVersionString(BTCARMORY_VERSION),
                                              UserModeStr(self, self.usermode))
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
      self.menusList.append( self.menu.addMenu(self.tr('&File')) )
      self.menusList.append( self.menu.addMenu(self.tr('&User')) )
      self.menusList.append( self.menu.addMenu(self.tr('&Tools')) )
      self.menusList.append( self.menu.addMenu(self.tr('&Addresses')) )
      self.menusList.append( self.menu.addMenu(self.tr('&Wallets')) )
      self.menusList.append( self.menu.addMenu(self.tr('&MultiSig')) )
      self.menusList.append( self.menu.addMenu(self.tr('&Help')) )
      #self.menusList.append( self.menu.addMenu('&Network') )


      def exportTx():
         if not TheBDM.getState()==BDM_BLOCKCHAIN_READY:
            QMessageBox.warning(self, self.tr('Transactions Unavailable'),
               self.tr('Transaction history cannot be collected until Armory is '
               'in online mode.  Please try again when Armory is online. '),
               QMessageBox.Ok)
            return
         else:
            DlgExportTxHistory(self,self).exec_()


      actExportTx    = self.createAction(self.tr('&Export Transactions...'), exportTx)
      actSettings    = self.createAction(self.tr('&Settings...'), self.openSettings)
      actMinimApp    = self.createAction(self.tr('&Minimize Armory'), self.minimizeArmory)
      actExportLog   = self.createAction(self.tr('Export &Log File...'), self.exportLogFile)
      actCloseApp    = self.createAction(self.tr('&Quit Armory'), self.closeForReal)
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
      actSetModeStd = self.createAction(self.tr('&Standard'),  chngStd, True)
      actSetModeAdv = self.createAction(self.tr('&Advanced'),  chngAdv, True)
      actSetModeDev = self.createAction(self.tr('&Expert'),    chngDev, True)

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
         if not TheSDM.satoshiIsAvailable():
            QMessageBox.warning(self, self.tr("Not Online"), self.tr(
               'Bitcoin Core is not available, so Armory will not be able '
               'to broadcast any transactions for you.'), QMessageBox.Ok)
            return
         DlgBroadcastBlindTx(self,self).exec_()



      actOpenSigner = self.createAction(self.tr('&Message Signing/Verification...'), openMsgSigning)
      if currmode=='Expert':
         actOpenTools  = self.createAction(self.tr('&EC Calculator...'),   lambda: DlgECDSACalc(self,self, 1).exec_())
         actBlindBroad = self.createAction(self.tr('&Broadcast Raw Transaction...'), openBlindBroad)

      self.menusList[MENUS.Tools].addAction(actOpenSigner)
      if currmode=='Expert':
         self.menusList[MENUS.Tools].addAction(actOpenTools)
         self.menusList[MENUS.Tools].addAction(actBlindBroad)

      def mkprom():
         if not TheBDM.getState()==BDM_BLOCKCHAIN_READY:
            QMessageBox.warning(self, self.tr('Offline'), self.tr(
               'Armory is currently offline, and cannot determine what funds are '
               'available for Simulfunding.  Please try again when Armory is in '
               'online mode.'), QMessageBox.Ok)
         else:
            DlgCreatePromNote(self, self).exec_()


      def msrevsign():
         title = self.tr('Import Multi-Spend Transaction')
         descr = self.tr(
            'Import a signature-collector text block for review and signing. '
            'It is usually a block of text with "TXSIGCOLLECT" in the first line, '
            'or a <i>*.sigcollect.tx</i> file.')
         ftypes = ['Signature Collectors (*.sigcollect.tx)']
         dlgImport = DlgImportAsciiBlock(self, self, title, descr, ftypes,
                                                         UnsignedTransaction)
         dlgImport.exec_()
         if dlgImport.returnObj:
            DlgMultiSpendReview(self, self, dlgImport.returnObj).exec_()


      simulMerge   = lambda: DlgMergePromNotes(self, self).exec_()
      actMakeProm    = self.createAction(self.tr('Simulfund &Promissory Note'), mkprom)
      actPromCollect = self.createAction(self.tr('Simulfund &Collect && Merge'), simulMerge)
      actMultiSpend  = self.createAction(self.tr('Simulfund &Review && Sign'), msrevsign)

      if not self.usermode==USERMODE.Expert:
         self.menusList[MENUS.MultiSig].menuAction().setVisible(False)


      # Addresses
      actAddrBook   = self.createAction(self.tr('View &Address Book...'),          self.execAddressBook)
      actSweepKey   = self.createAction(self.tr('&Sweep Private Key/Address...'),  self.menuSelectSweepKey)
      actImportKey  = self.createAction(self.tr('&Import Private Key/Address...'), self.menuSelectImportKey)

      self.menusList[MENUS.Addresses].addAction(actAddrBook)
      if not currmode=='Standard':
         self.menusList[MENUS.Addresses].addAction(actImportKey)
         self.menusList[MENUS.Addresses].addAction(actSweepKey)

      actCreateNew    = self.createAction(self.tr('&Create New Wallet'),        self.startWalletWizard)
      actImportWlt    = self.createAction(self.tr('&Import or Restore Wallet'), self.execImportWallet)
      actAddressBook  = self.createAction(self.tr('View &Address Book'),        self.execAddressBook)
      actRecoverWlt   = self.createAction(self.tr('&Fix Damaged Wallet'),        self.RecoverWallet)

      self.menusList[MENUS.Wallets].addAction(actCreateNew)
      self.menusList[MENUS.Wallets].addAction(actImportWlt)
      self.menusList[MENUS.Wallets].addSeparator()
      self.menusList[MENUS.Wallets].addAction(actRecoverWlt)

      execAbout   = lambda: DlgHelpAbout(self).exec_()

      actAboutWindow  = self.createAction(self.tr('&About Armory...'), execAbout)
      actClearMemPool = self.createAction(self.tr('Clear All Unconfirmed'), self.clearMemoryPool)
      actRescanDB     = self.createAction(self.tr('Rescan Databases'), self.rescanNextLoad)
      actRebuildDB    = self.createAction(self.tr('Rebuild and Rescan Databases'), self.rebuildNextLoad)
      actRescanBalance = self.createAction(self.tr('Rescan Balance'), self.rescanBalanceNextLoad)
      actFactoryReset = self.createAction(self.tr('Factory Reset'), self.factoryReset)

      self.menusList[MENUS.Help].addAction(actAboutWindow)
      self.menusList[MENUS.Help].addSeparator()
      self.menusList[MENUS.Help].addSeparator()
      self.menusList[MENUS.Help].addAction(actClearMemPool)
      self.menusList[MENUS.Help].addAction(actRescanBalance)
      self.menusList[MENUS.Help].addAction(actRescanDB)
      self.menusList[MENUS.Help].addAction(actRebuildDB)
      self.menusList[MENUS.Help].addAction(actFactoryReset)



      execMSHack = lambda: DlgSelectMultiSigOption(self,self).exec_()
      execBrowse = lambda: DlgLockboxManager(self,self).exec_()
      actMultiHacker = self.createAction(self.tr('Multi-Sig Lockboxes'), execMSHack)
      actBrowseLockboxes = self.createAction(self.tr('Lockbox &Manager...'), execBrowse)
      #self.menusList[MENUS.MultiSig].addAction(actMultiHacker)
      self.menusList[MENUS.MultiSig].addAction(actBrowseLockboxes)
      self.menusList[MENUS.MultiSig].addAction(actMakeProm)
      self.menusList[MENUS.MultiSig].addAction(actPromCollect)
      self.menusList[MENUS.MultiSig].addAction(actMultiSpend)


      self.startBlockchainProcessingInitialization()

      # Restore any main-window geometry saved in the settings file
      hexgeom   = self.settings.get('MainGeometry')

      hexwltsz  = self.settings.get('MainWalletCols')
      if len(hexgeom)>0:
         geom = QByteArray.fromHex(hexgeom)
         self.restoreGeometry(geom)
      if len(hexwltsz)>0:
         restoreTableView(self.walletsView, hexwltsz)


      if DO_WALLET_CHECK:
         self.checkWallets()

      self.blkReceived = RightNow()

      self.setDashboardDetails()

      self.execIntroDialog()
      #reactor.callLater(1, self.Heartbeat)

      if self.getSettingOrSetDefault('MinimizeOnOpen', False) and not CLI_ARGS:
         LOGINFO('MinimizeOnOpen is True')
         self.minimizeArmory()

      if CLI_ARGS:
         self.signalExecution.callLater(1, self.uriLinkClicked, CLI_ARGS[0])

      if OS_MACOSX:
         self.macNotifHdlr = ArmoryMac.MacNotificationHandler()

      # Now that construction of the UI is done
      # Check for warnings to be displayed

     # This is true if and only if the command line has a data dir that doesn't exist
      # and can't be created.
      if not CLI_OPTIONS.datadir in [ARMORY_HOME_DIR, DEFAULT]:
         QMessageBox.warning(self, self.tr('Default Data Directory'), self.tr(
            'Armory is using the default data directory because '
            'the data directory specified in the command line could '
            'not be found nor created.'), QMessageBox.Ok)
      # This is true if and only if the command line has a database dir that doesn't exist
      # and can't be created.
      elif not CLI_OPTIONS.armoryDBDir in [ARMORY_DB_DIR, DEFAULT]:
         QMessageBox.warning(self, self.tr('Default Database Directory'), self.tr(
            'Armory is using the default database directory because '
            'the database directory specified in the command line could '
            'not be found nor created.'), QMessageBox.Ok)

      # This is true if and only if the command line has a bitcoin dir that doesn't exist
      #if not CLI_OPTIONS.satoshiHome in [BTC_HOME_DIR, DEFAULT]:
      #   QMessageBox.warning(self, self.tr('Bitcoin Directory'), self.tr(
      #      'Armory is using the default Bitcoin directory because '
      #      'the Bitcoin directory specified in the command line could '
      #      'not be found.'), QMessageBox.Ok)

      if not self.getSettingOrSetDefault('DNAA_DeleteLevelDB', False) and \
            os.path.exists(os.path.join(ARMORY_DB_DIR, LEVELDB_BLKDATA)):
               reply = MsgBoxWithDNAA(self, self, MSGBOX.Question, self.tr('Delete Old DB Directory'),
                  self.tr('Armory detected an older version Database. '
                  'Do you want to delete the old database? Choose yes if  '
                  'do not think that you will revert to an older version of Armory.'), self.tr('Do not ask this question again'))
               if reply[0]==True:
                  shutil.rmtree(os.path.join(ARMORY_DB_DIR, LEVELDB_BLKDATA))
                  shutil.rmtree(os.path.join(ARMORY_DB_DIR, LEVELDB_HEADERS))
               if reply[1]==True:
                  self.writeSetting('DNAA_DeleteLevelDB', True)
                  
      self.signalExecution.callLater(1, self.walletTimeoutCheck)
      
   ####################################################
   def getWatchingOnlyWallets(self):
      result = []
      for wltID in self.walletIDList:
         if self.walletMap[wltID].watchingOnly:
            result.append(wltID)
      return result


   ####################################################
   def changeWltFilter(self):
      
      if self.netMode == NETWORKMODE.Offline:
         return

      currIdx  = max(self.comboWltSelect.currentIndex(), 0)
      currText = unicode(self.comboWltSelect.currentText()).lower()

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
      self.PageLineEdit.setText(unicode(self.mainLedgerCurrentPage))

      self.wltIDList = []
      for i,vis in enumerate(self.walletVisibleList):
         if vis:
            wltid = self.walletIDList[i]
            if self.walletMap[wltid].isEnabled:
               self.wltIDList.append(wltid)

      TheBDM.bdv().updateWalletsLedgerFilter(self.wltIDList)


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
            QMessageBox.critmoduleName(self, self.tr("Bad Module"), self.tr(
               'The module you attempted to load (%1) is malformed.  It is '
               'missing attributes that are needed for Armory to load it. '
               'It will be skipped.').arg(moduleName), QMessageBox.Ok)
            continue

         verPluginInt = getVersionInt(readVersionString(plugObj.maxVersion))
         verArmoryInt = getVersionInt(BTCARMORY_VERSION)
         if verArmoryInt >verPluginInt:
            reply = QMessageBox.warning(self, self.tr("Outdated Module"), self.tr(
               'Module "%1" is only specified to work up to Armory version %2. '
               'You are using Armory version %3.  Please remove the module if '
               'you experience any problems with it, or contact the maintainer '
               'for a new version. '
               '<br><br> '
               'Do you want to continue loading the module?').arg(moduleName),
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
               reply = QMessageBox.warning(self, self.tr("Invalid Module"), self.tr(
                  'Armory detected the following module which is '
                  '<font color=%1><b>invalid</b></font>:'
                  '<br><br>'
                  '   <b>Module Name:</b> %2<br>'
                  '   <b>Module Path:</b> %3<br>'
                  '<br><br>'
                  'Armory will only run a module from a zip file that '
                  'has the required stucture.').arg(htmlColor('TextRed'), moduleName, moduleZipPath), QMessageBox.Ok)
            elif not USE_TESTNET and not USE_REGTEST and infoMap[MODULE_ZIP_STATUS_KEY] == MODULE_ZIP_STATUS.Unsigned:
               reply = QMessageBox.warning(self, self.tr("UNSIGNED Module"), self.tr(
                  'Armory detected the following module which '
                  '<font color="%1"><b>has not been signed by Armory</b></font> and may be dangerous: '
                  '<br><br>'
                  '   <b>Module Name:</b> %2<br>'
                  '   <b>Module Path:</b> %3<br>'
                  '<br><br>'
                  'Armory will not allow you to run this module.').arg(htmlColor('TextRed'), moduleName, moduleZipPath), QMessageBox.Ok)
            else:

               ZipFile(moduleZipPath).extract(INNER_ZIP_FILENAME, self.tempModulesDirName)
               ZipFile(os.path.join(self.tempModulesDirName,INNER_ZIP_FILENAME)).extractall(self.tempModulesDirName)

               plugin = importModule(self.tempModulesDirName, moduleName, globals())
               plugObj = plugin.PluginObject(self)

               if not hasattr(plugObj,'getTabToDisplay') or \
                  not hasattr(plugObj,'tabName'):
                  LOGERROR('Module is malformed!  No tabToDisplay or tabName attrs')
                  QMessageBox.critmoduleName(self, self.tr("Bad Module"), self.tr(
                     'The module you attempted to load (%1) is malformed.  It is '
                     'missing attributes that are needed for Armory to load it. '
                     'It will be skipped.').arg(moduleName), QMessageBox.Ok)
                  continue

               verPluginInt = getVersionInt(readVersionString(plugObj.maxVersion))
               verArmoryInt = getVersionInt(BTCARMORY_VERSION)
               if verArmoryInt >verPluginInt:
                  reply = QMessageBox.warning(self, self.tr("Outdated Module"), self.tr(
                     'Module %1 is only specified to work up to Armory version %2. '
                     'You are using Armory version %3.  Please remove the module if '
                     'you experience any problems with it, or contact the maintainer '
                     'for a new version.'
                     '<br><br>'
                     'Do you want to continue loading the module?').arg(moduleName,  plugObj.maxVersion, getVersionString(BTCARMORY_VERSION)),
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
   def clearMemoryPool(self):
      touchFile( os.path.join(ARMORY_HOME_DIR, 'clearmempool.flag') )
      msg = self.tr(
         'The next time you restart Armory, all unconfirmed transactions will '
         'be cleared allowing you to retry any stuck transactions.')
      if not self.doAutoBitcoind:
         msg += self.tr(
         '<br><br>Make sure you also restart Bitcoin Core '
         '(or bitcoind) and let it synchronize again before you restart '
         'Armory.  Doing so will clear its memory pool as well.')
      QMessageBox.information(self, self.tr('Memory Pool'), msg, QMessageBox.Ok)



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
      reply = QMessageBox.warning(self, self.tr('Queue Rescan?'), self.tr(
         'The next time you restart Armory, it will rescan the blockchain '
         'database, and reconstruct your wallet histories from scratch. '
         'The rescan will take 10-60 minutes depending on your system. '
         '<br><br> '
         'Do you wish to force a rescan on the next Armory restart?'), \
         QMessageBox.Yes | QMessageBox.No)
      if reply==QMessageBox.Yes:
         touchFile( os.path.join(ARMORY_HOME_DIR, 'rescan.flag') )

   ####################################################
   def rebuildNextLoad(self):
      reply = QMessageBox.warning(self, self.tr('Queue Rebuild?'), self.tr(
         'The next time you restart Armory, it will rebuild and rescan '
         'the entire blockchain database.  This operation can take between '
         '30 minutes and 4 hours depending on your system speed. '
         '<br><br>'
         'Do you wish to force a rebuild on the next Armory restart?'), \
         QMessageBox.Yes | QMessageBox.No)
      if reply==QMessageBox.Yes:
         touchFile( os.path.join(ARMORY_HOME_DIR, 'rebuild.flag') )

   ####################################################
   def rescanBalanceNextLoad(self):
      reply = QMessageBox.warning(self, self.tr('Queue Balance Rescan?'), self.tr(
         'The next time you restart Armory, it will rescan the balance of '
         'your wallets. This operation typically takes less than a minute. '
         '<br><br>'
         'Do you wish to force a balance rescan on the next Armory restart?'), \
         QMessageBox.Yes | QMessageBox.No)
      if reply==QMessageBox.Yes:
         touchFile( os.path.join(ARMORY_HOME_DIR, 'rescanbalance.flag') )

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
      QMessageBox.information(self, self.tr('Select Wallet'), self.tr(
         'You must import an address into a specific wallet.  If '
         'you do not want to import the key into any available wallet, '
         'it is recommeneded you make a new wallet for this purpose.'
         '<br><br>'
         'Double-click on the desired wallet from the main window, then '
         'click on "Import/Sweep Private Keys" on the bottom-right '
         'of the properties window.'
         '<br><br>'
         'Keys cannot be imported into watching-only wallets, only full '
         'wallets.'), QMessageBox.Ok)

   ####################################################
   def menuSelectSweepKey(self):
      QMessageBox.information(self, self.tr('Select Wallet'), self.tr(
         'You must select a wallet into which funds will be swept. '
         'Double-click on the desired wallet from the main window, then '
         'click on "Import/Sweep Private Keys" on the bottom-right '
         'of the properties window to sweep to that wallet.'
         '<br><br>'
         'Keys cannot be swept into watching-only wallets, only full '
         'wallets.'), QMessageBox.Ok)

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
      self.sysTray.setToolTip('Armory' + (' [Testnet]' if USE_TESTNET else '') + (' [Regtest]' if USE_REGTEST else ''))
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

      actShowArmory = self.createAction(self.tr('Show Armory'), self.bringArmoryToFront)
      actSendBtc    = self.createAction(self.tr('Send Bitcoins'), traySend)
      actRcvBtc     = self.createAction(self.tr('Receive Bitcoins'), trayRecv)
      actClose      = self.createAction(self.tr('Quit Armory'), self.closeForReal)
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

      if USE_TESTNET or USE_REGTEST:
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
            execAndWait('gconftool-2 -t string -s /desktop/gnome/url-handlers/bitcoin/command "python2 %s \"%%s\""' % __file__)
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
               reply = MsgBoxWithDNAA(self, self, MSGBOX.Question, self.tr('Default URL Handler'),
                  self.tr('Armory is not set as your default application for handling '
                  '"bitcoin:" links.  Would you like to use Armory as the '
                  'default?'), self.tr('Do not ask this question again'))
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
            reply = MsgBoxWithDNAA(self, self, MSGBOX.Question, self.tr('Default URL Handler'),
               self.tr('Armory is not set as your default application for handling '
               '"bitcoin:" links.  Would you like to use Armory as the '
               'default?'), self.tr('Do not ask this question again'))

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
         reply = MsgBoxWithDNAA(self, self, MSGBOX.Warning, self.tr("Version Warning"), self.tr(
            'Since Armory version 0.92 the formats for offline transaction '
            'operations has changed to accommodate multi-signature '
            'transactions.  This format is <u>not</u> compatible with '
            'versions of Armory before 0.92. '
            '<br><br>'
            'To continue, the other system will need to be upgraded to '
            'to version 0.92 or later.  If you cannot upgrade the other '
            'system, you will need to reinstall an older version of Armory '
            'on this system.'), dnaaMsg=self.tr('Do not show this warning again'))
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
      QMessageBox.information(self, self.tr('No Tools Yet!'),
         self.tr('The developer tools are not available yet, but will be added '
         'soon.  Regardless, developer-mode still offers lots of '
         'extra information and functionality that is not available in '
         'Standard or Advanced mode.'), QMessageBox.Ok)



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
      export_rootpubkey = False
      if copyType.lower()=='pkcc':
         fn = 'armory_%s.%s' % (wlt.uniqueIDB58, suffix)
         export_rootpubkey = True
      else:
         fn = 'armory_%s_%s.wallet' % (wlt.uniqueIDB58, suffix)

      if wlt.watchingOnly and copyType.lower() != 'pkcc':
         fn = 'armory_%s_%s_WatchOnly.wallet' % (wlt.uniqueIDB58, suffix)
         
      if export_rootpubkey is True:
         savePath = unicode(self.getFileSave(defaultFilename=fn,
                ffilter=['Root Pubkey Text Files (*.rootpubkey)']))
      else:
         savePath = unicode(self.getFileSave(defaultFilename=fn))
                            
      if not len(savePath) > 0:
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
               QMessageBox.information(parent, self.tr('Aborted'), self.tr(
                  'No passphrase was selected for the encrypted backup. '
                  'No backup was created.'), QMessageBox.Ok)
            newPassphrase = SecureBinaryData(str(dlgCrypt.edtPasswd1.text()))

         wlt.makeEncryptedWalletCopy(savePath, newPassphrase)
      elif copyType.lower() == 'pkcc':
         wlt.writePKCCFile(savePath)
      else:
         LOGERROR('Invalid "copyType" supplied to makeWalletCopy: %s', copyType)
         return False

      QMessageBox.information(parent, self.tr('Backup Complete'), self.tr(
         'Your wallet was successfully backed up to the following '
         'location:<br><br>%1').arg(savePath), QMessageBox.Ok)
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
         QMessageBox.information(self,self.tr('Restart Armory'),
         self.tr('You may have to restart Armory for all aspects of '
         'the new usermode to go into effect.'), QMessageBox.Ok)

      self.firstModeSwitch = False

   #############################################################################
   def setLang(self, lang):
      LOGINFO('Changing language:')
      LOGINFO('   From: %s', self.settings.get('Language'))
      self.language = lang
      self.writeSetting("Language", lang)
      LOGINFO('     To: %s', self.settings.get('Language'))

      if not self.firstModeSwitch:
         QMessageBox.information(self, self.tr('Restart Armory'),
            self.tr('You will have to restart Armory for the new language to go into effect'), QMessageBox.Ok)

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
         QMessageBox.warning(self, self.tr('Invalid Date Format'),
            self.tr('The date format you specified was not valid.  Please re-enter '
            'it using only the strftime symbols shown in the help text.'), QMessageBox.Ok)
         return False

      self.writeSetting('DateFormat', binary_to_hex(fmtStr))
      return True

   #############################################################################
   def triggerProcessMutexNotification(self, uriLink):
      self.bringArmoryToFront()
      uriDict = parseBitcoinURI(uriLink)
      if len(uriDict) > 0:
         self.uriLinkClicked(uriLink)

   #############################################################################
   def acquireProcessMutex(self):
      LOGINFO('acquiring process mutex...')
      
      self.connect(self, SIGNAL("processMutexNotification"), \
                   self.triggerProcessMutexNotification)

      # Prevent Armory from being opened twice
      def uriClick_partial(a):
         self.emit(SIGNAL("processMutexNotification"), a)

      if CLI_OPTIONS.interport > 1:
         from armoryengine.ProcessMutex import PySide_ProcessMutex
         self.prc_mutex = PySide_ProcessMutex(CLI_OPTIONS.interport, uriClick_partial) 
         
         if self.prc_mutex.acquire() == False:
            LOGWARN('Socket already occupied!  This must be a duplicate Armory')
            QMessageBox.warning(self, self.tr('Already Open'), self.tr(
               'Armory is already running!  You can only have one Armory open '
               'at a time.  Exiting...'), QMessageBox.Ok)
            os._exit(0)
      else:
         LOGWARN('*** Listening port is disabled.  URI-handling will not work')

      self.internetStatus = INTERNET_STATUS.DidNotCheck

   ############################################################################
   def startArmoryDBIfNecessary(self):
      if CLI_OPTIONS.offline:
         LOGWARN("Offline instance, not startig the DB")
         return False
      try:
         if TheBDM.hasRemoteDB() == False:
            #check there is no local db
            localDBPort = Cpp.BlockDataManagerConfig_hasLocalDB(\
               str(ARMORY_HOME_DIR), armoryengine.ArmoryUtils.ARMORYDB_PORT)
            if len(localDBPort) > 0:
               armoryengine.ArmoryUtils.ARMORYDB_PORT = localDBPort
               return True
            
            #look for cookie file and delete it
            cookiePath = os.path.join(ARMORY_HOME_DIR, ".cookie_") 
            if os.path.exists(cookiePath):            
               os.remove(cookiePath)

            #If we got this far, we need to spawn a local db
            self.setSatoshiPaths()
            TheSDM.spawnDB(str(ARMORY_HOME_DIR), TheBDM.armoryDBDir)
   
            #wait for cookie file creation
            while not os.path.exists(cookiePath):
               time.sleep(0.1)
               
            #get port from cookie
            armoryengine.ArmoryUtils.ARMORYDB_PORT = \
               Cpp.BlockDataManagerConfig_getPortFromCookie(str(ARMORY_HOME_DIR))
   
            #test if db has started
            if Cpp.BlockDataManagerConfig_testConnection(\
               ARMORYDB_IP, armoryengine.ArmoryUtils.ARMORYDB_PORT) == False:
               LOGERROR("Failed to spawn ArmoryDB")
               return False
            
            LOGINFO("Connecting on port %s" % armoryengine.ArmoryUtils.ARMORYDB_PORT)
         else:
            LOGWARN("DB is already running")
   
         return True
      except Exception as e:
         LOGEXCEPT('Failed to start Armory database: %s' % str(e))
      
      return False

   ############################################################################
   def startBitcoindIfNecessary(self):
      LOGINFO('startBitcoindIfNecessary')

      TheSDM.checkDBIsLocal()

      if self.internetStatus == INTERNET_STATUS.Unavailable or \
         CLI_OPTIONS.offline:
         LOGWARN('Not online, will not start bitcoind')
         return False

      if TheBDM.hasRemoteDB() or not self.doAutoBitcoind:
         return False

      if TheSDM.satoshiIsAvailable():
         LOGWARN('Tried to start bitcoind, but satoshi already running')
         return False

      self.setSatoshiPaths()

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
   def notifyBitcoindIsReady(self):
      self.signalExecution.executeMethod(\
         self.completeBlockchainProcessingInitialization)

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
      if self.settings.hasSetting('SatoshiDatadir'):
         # Setting override BTC_HOME_DIR only if it wasn't explicitly
         # set as the command line.
         manageSatoshi = self.settings.get('ManageSatoshi')
         if manageSatoshi == True:
            self.satoshiHomePath = str(self.settings.get('SatoshiDatadir'))
            LOGINFO('Setting satoshi datadir = %s' % self.satoshiHomePath)

      TheBDM.setSatoshiDir(self.satoshiHomePath)
      TheSDM.setSatoshiDir(self.satoshiHomePath)

   ############################################################################
   # This version of online mode is possible doesn't check the internet everytime
   def isOnlineModePossible(self):
      return self.internetStatus != INTERNET_STATUS.Unavailable and \
               TheSDM.satoshiIsAvailable() and \
               os.path.exists(os.path.join(TheBDM.btcdir, 'blocks'))

   ############################################################################
   def loadBlockchainIfNecessary(self):
      LOGINFO('loadBlockchainIfNecessary')
      if self.netMode != NETWORKMODE.Offline:
         # Track number of times we start loading the blockchain.
         # We will decrement the number when loading finishes
         # We can use this to detect problems with mempool or blkxxxx.dat
         self.numTriesOpen = self.getSettingOrSetDefault('FailedLoadCount', 0)
         if self.numTriesOpen>2:
            self.loadFailedManyTimesFunc(self.numTriesOpen)
         self.settings.set('FailedLoadCount', self.numTriesOpen+1)

         try:
            TheBDM.goOnline()
            self.switchNetworkMode(NETWORKMODE.Full)
         except Cpp.NoArmoryDBExcept:
            self.switchNetworkMode(NETWORKMODE.Offline)

   #############################################################################
   def switchNetworkMode(self, newMode):
      LOGINFO('Setting netmode: %s', newMode)
      self.netMode=newMode
      return

   #############################################################################
   def parseUriLink(self, uriStr, click=True):
      if len(uriStr) < 1:
         QMessageBox.critical(self, self.tr('No URL String'),
               self.tr('You have not entered a URL String yet. '
               'Please go back and enter a URL String.'), QMessageBox.Ok)
         return {}
      LOGINFO('URI link clicked!')
      LOGINFO('The following URI string was parsed:')
      LOGINFO(uriStr.replace('%','%%'))

      try:
         uriDict = parseBitcoinURI(uriStr)
      except:
         # malformed uri, make the dict empty, which will trigger the warning
         uriDict = {}

      if TheBDM.getState() in (BDM_OFFLINE,BDM_UNINITIALIZED):
         LOGERROR('Clicked or entered "bitcoin:" link in offline mode.')
         self.bringArmoryToFront()
         if click:
            QMessageBox.warning(self, self.tr('Offline Mode'),
               self.tr('You clicked on a "bitcoin:" link, but Armory is in '
               'offline mode, and is not capable of creating transactions. '
               'Using links will only work if Armory is connected '
               'to the Bitcoin network!'), QMessageBox.Ok)
         else:
            QMessageBox.warning(self, self.tr('Offline Mode'),
               self.tr('You entered a "bitcoin:" link, but Armory is in '
               'offline mode, and is not capable of creating transactions. '
               'Using links will only work if Armory is connected '
               'to the Bitcoin network!'), QMessageBox.Ok)
         return {}

      if len(uriDict)==0:
         if click:
            warnMsg = (self.tr('It looks like you just clicked a "bitcoin:" link, but that link is malformed.'))
         else:
            warnMsg = (self.tr('It looks like you just entered a "bitcoin:" link, but that link is malformed.'))
         if self.usermode == USERMODE.Standard:
            warnMsg += (self.tr('Please check the source of the link and enter the transaction manually.'))
         else:
            warnMsg += self.tr('The raw URI string is:\n\n') + uriStr
         QMessageBox.warning(self, self.tr('Invalid URI'), warnMsg, QMessageBox.Ok)
         LOGERROR(warnMsg.replace('\n', ' '))
         return {}

      if not uriDict.has_key('address'):
         if click:
            QMessageBox.warning(self, self.tr('The "bitcoin:" link you just clicked '
               'does not even contain an address!  There is nothing that '
               'Armory can do with this link!'), QMessageBox.Ok)
         else:
            QMessageBox.warning(self, self.tr('The "bitcoin:" link you just entered '
               'does not even contain an address!  There is nothing that '
               'Armory can do with this link!'), QMessageBox.Ok)
         LOGERROR('No address in "bitcoin:" link!  Nothing to do!')
         return {}

      # Verify the URI is for the same network as this Armory instnance
      theAddrByte = checkAddrType(base58_to_binary(uriDict['address']))
      if theAddrByte!=-1 and not theAddrByte in [ADDRBYTE, P2SHBYTE]:
         net = 'Unknown Network'
         if NETWORKS.has_key(theAddrByte):
            net = NETWORKS[theAddrByte]
         if click:
            QMessageBox.warning(self, self.tr('Wrong Network!'),
               self.tr('The address for the "bitcoin:" link you just clicked is '
               'for the wrong network!  You are on the <b>%2</b> '
               'and the address you supplied is for the '
               '<b>%3</b>!').arg(NETWORKS[ADDRBYTE], net), QMessageBox.Ok)
         else:
            QMessageBox.warning(self, self.tr('Wrong Network!'),
               self.tr('The address for the "bitcoin:" link you just entered is '
               'for the wrong network!  You are on the <b>%2</b> '
               'and the address you supplied is for the '
               '<b>%3</b>!').arg(NETWORKS[ADDRBYTE], net), QMessageBox.Ok)
         LOGERROR('URI link is for the wrong network!')
         return {}

      # If the URI contains "req-" strings we don't recognize, throw error
      recognized = ['address','version','amount','label','message']
      for key,value in uriDict.iteritems():
         if key.startswith('req-') and not key[4:] in recognized:
            if click:
               QMessageBox.warning(self, self.tr('Unsupported URI'), self.tr('The "bitcoin:" link '
                  'you just clicked contains fields that are required but not '
                  'recognized by Armory.  This may be an older version of Armory, '
                  'or the link you clicked on uses an exotic, unsupported format. '
                  '<br><br>The action cannot be completed.'''), QMessageBox.Ok)
            else:
               QMessageBox.warning(self, self.tr('Unsupported URI'), self.tr('The "bitcoin:" link '
                  'you just entered contains fields that are required but not '
                  'recognized by Armory.  This may be an older version of Armory, '
                  'or the link you entered on uses an exotic, unsupported format. '
                  '<br><br>The action cannot be completed.'), QMessageBox.Ok)
            LOGERROR('URI link contains unrecognized req- fields.')
            return {}

      return uriDict



   #############################################################################
   def uriLinkClicked(self, uriStr):
      LOGINFO('uriLinkClicked')
      if TheBDM.getState()==BDM_OFFLINE:
         QMessageBox.warning(self, self.tr('Offline'),
            self.tr('You just clicked on a "bitcoin:" link, but Armory is offline '
            'and cannot send transactions.  Please click the link '
            'again when Armory is online.'), \
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

      uriDict = self.parseUriLink(uriStr, self.tr('clicked'))

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

      # Set the language, default to English
      self.language = 'en'
      if self.settings.get('Language') != '':
         self.language = self.settings.get('Language')


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
      self.walletManager = None

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

            wltLoaded = True
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
                  wltLoaded = False
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
               
            if wltLoaded is False:
               continue
                        
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
      
      self.loadCppWallets()
      
   #############################################################################
   def loadCppWallets(self):
      #load all existing cpp wallets
      if self.walletManager == None:
         self.walletManager = Cpp.WalletManager(str(ARMORY_HOME_DIR))
      
      #check python wallets against cpp wallets
      from ui.WalletMirrorDialog import WalletComparisonClass
      wltCmpObj = WalletComparisonClass(self)
      wltCmpObj.checkWallets()   
         
      #load all cpp wallets
      for wltID in self.walletMap:
         wlt = self.walletMap[wltID]
         wlt.cppWallet = self.walletManager.getCppWallet(wltID)
         
         
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
      typesStr = ';; '.join(str(_type) for _type in types)

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
      types.append(self.tr('All files (*)'))
      
      typeStr = QString("")
      for i in range(0, len(types)):
         _type = types[i]         
         typeStr += QString(_type)
         if i < len(types) - 1:
            typeStr += QString(";; ")

      # Open the native file load dialog and grab the loaded file/path unless
      # we're in OS X, where native dialogs sometimes freeze. Looks like a Qt
      # issue of some sort. Some experimental code under ArmoryMac that directly
      # calls a dialog produces better results but still freezes under some
      # circumstances.
      if not OS_MACOSX:
         fullPath = unicode(QFileDialog.getOpenFileName(self, title, defaultDir,
                                                        typeStr))
      else:
         fullPath = unicode(QFileDialog.getOpenFileName(self, title, defaultDir,
                                                        typeStr,
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
         if lbox.hasScrAddr(p2shAddrStr):
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
               outStr = self.tr('Contributor "%1" (%2)').arg(contribLabel, contribID)
            else:
               outStr = self.tr('Contributor %1').arg(contribID)
         else:
            if contribLabel:
               outStr = self.tr('Contributor "%1"').arg(contribLabel)
            else:
               outStr = self.tr('Unknown Contributor')
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
         if wlt.hasScrAddr(addr160):
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
      self.statusBar().showMessage(self.tr('Blockchain loaded, wallets sync\'d!'), 10000)

      currSyncSuccess = self.getSettingOrSetDefault("SyncSuccessCount", 0)
      self.writeSetting('SyncSuccessCount', min(currSyncSuccess+1, 10))

      if self.getSettingOrSetDefault('NotifyBlkFinish',True):
         reply,remember = MsgBoxWithDNAA(self, self, MSGBOX.Info, 
            self.tr('Blockchain Loaded!'), self.tr('Blockchain loading is complete. '
            'Your balances and transaction history are now available '
            'under the "Transactions" tab.  You can also send and '
            'receive bitcoins.'), dnaaMsg=self.tr('Do not show me this notification again '), yesStr='OK')

         if remember==True:
            self.writeSetting('NotifyBlkFinish',False)

      self.mainDisplayTabs.setCurrentIndex(self.MAINTABS.Ledger)


      self.netMode = NETWORKMODE.Full
      self.settings.set('FailedLoadCount', 0)

      # This will force the table to refresh with new data
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
         self.lblTotalFunds.setText('<b><font color="%s">%s</font></b>' % (btccolor,coin2str(totalFunds)))
         self.lblTot.setText(self.tr('<b><font color="%1">Maximum Funds:</font></b>').arg(lblcolor))
         self.lblBTC1.setText('<b><font color="%s">BTC</font></b>' % lblcolor)
         self.lblSpendFunds.setText('<b><font color=%s>%s</font></b>' % (goodColor, coin2str(spendFunds)))
         self.lblUnconfFunds.setText(('<b><font color="%s">%s</font></b>' % \
                                             (uncolor, coin2str(unconfFunds))))

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
         #if le.isSentToSelf() and wlt and showSentToSelfAmt:
            #amt = determineSentToSelfAmt(le, wlt)[0]

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
         if le.isOptInRBF() == True:
            if le.getValue() < 0 or le.isSentToSelf():
               dispComment = self.tr("*Right click to bump fee* ") + dispComment
            else:
               dispComment = self.tr("*** RBF Flagged *** ") + dispComment
         elif le.isChainedZC() == True:
            dispComment = self.tr("*** Chained ZC *** ") + dispComment
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

         # RBF and zc chain status
         row.append( le.isOptInRBF() )
         row.append(le.isChainedZC())

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
      try:
         comboIdx = self.comboWltSelect.currentIndex()
         if comboIdx < 0:
            raise
      except:
         comboIdx = self.getSettingOrSetDefault('LastFilterState', 0)
   
      self.comboWltSelect.clear()
      self.comboWltSelect.addItem( self.tr('My Wallets'        ))
      self.comboWltSelect.addItem( self.tr('Offline Wallets'   ))
      self.comboWltSelect.addItem( self.tr('Other\'s wallets'  ))
      self.comboWltSelect.addItem( self.tr('All Wallets'       ))
      self.comboWltSelect.addItem( self.tr('Custom Filter'     ))
      for wltID in self.walletIDList:
         self.comboWltSelect.addItem( self.walletMap[wltID].labelName )
      self.comboWltSelect.insertSeparator(5)
      self.comboWltSelect.insertSeparator(5)
      self.comboWltSelect.setCurrentIndex(comboIdx)

   #############################################################################
   def execDlgWalletDetails(self, index=None):
      if len(self.walletMap)==0:
         reply = QMessageBox.information(self, self.tr('No Wallets!'),
            self.tr('You currently do not have any wallets.  Would you like to '
            'create one, now?'), QMessageBox.Yes | QMessageBox.No)
         if reply==QMessageBox.Yes:
            self.startWalletWizard()
         return

      if index==None:
         index = self.walletsView.selectedIndexes()
         if len(self.walletMap)==1:
            self.walletsView.selectRow(0)
            index = self.walletsView.selectedIndexes()
         elif len(index)==0:
            QMessageBox.warning(self, self.tr('Select a Wallet'), \
               self.tr('Please select a wallet on the right, to see its properties.'), QMessageBox.Ok)
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

      if not currComment:
         dialog = DlgSetComment(self, self, currComment, self.tr('Add Transaction Comment'))
      else:
         dialog = DlgSetComment(self, self, currComment, self.tr('Change Transaction Comment'))
      if dialog.exec_():
         newComment = str(dialog.edtComment.text())
         view.model().updateIndexComment(index, newComment)
         self.walletMap[wltID].setComment(hex_to_binary(txHash), newComment)
         self.walletListChanged()


   #############################################################################
   def updateAddressCommentFromView(self, view, wlt):
      index = view.selectedIndexes()[0]
      row, col = index.row(), index.column()
      currComment = str(view.model().index(row, ADDRESSCOLS.Comment).data().toString())
      addrStr     = str(view.model().index(row, ADDRESSCOLS.Address).data().toString())

      if not currComment:
         dialog = DlgSetComment(self, self, currComment, self.tr('Add Address Comment'))
      else:
         dialog = DlgSetComment(self, self, currComment, self.tr('Change Address Comment'))
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

      # Update the maps/dictionaries
      newWltID = newWallet.uniqueIDB58

      if self.walletMap.has_key(newWltID):
         return

      self.walletMap[newWltID] = newWallet
      self.walletIndices[newWltID] = len(self.walletMap)-1

      # Maintain some linear lists of wallet info
      self.walletIDSet.add(newWltID)
      self.walletIDList.append(newWltID)
      
      self.loadCppWallets()
      newWallet.registerWallet(walletIsNew)
      
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

      #self.walletMap[wltID].unregisterWallet()

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
               pubKeyMap = {}
               pubKeyMap[ADDRBYTE + a160] = pubKey
               txoIdx = utxo.getTxOutIndex()
               inputSide.append(UnsignedTxInput(rawTx, txoIdx, None, pubKeyMap))
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
            scrAddr = ADDRBYTE + addrObj.getAddr160()
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
         QMessageBox.critical(self, self.tr('Already Sweeping'),
            self.tr('You are already in the process of scanning the blockchain for '
            'the purposes of sweeping other addresses.  You cannot initiate '
            'sweeping new addresses until the current operation completes. '
            '<br><br>'
            'In the future, you may select "Multiple Keys" when entering '
            'addresses to sweep.  There is no limit on the number that can be '
            'specified, but they must all be entered at once.'), QMessageBox.Ok)
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
         strPlur = self.tr('addresses') if nkey>1 else self.tr('address')
         QMessageBox.info(self, self.tr('Armory is Offline'), \
            self.tr('You have chosen to sweep %n key(s), but Armory is currently '
            'in offline mode.  The sweep will be performed the next time you '
            'go into online mode.  You can initiate online mode (if available) '
            'from the dashboard in the main window.', "", nkey), QMessageBox.Ok)
         confirmed=True

      else:
         msgConfirm = ( \
            self.tr('Armory must scan the global transaction history in order to '
            'find any bitcoins associated with the keys you supplied. '
            'Armory will go into offline mode temporarily while the scan '
            'is performed, and you will not have access to balances or be '
            'able to create transactions.  The scan may take several minutes.'
            '<br><br>', "", len(self.sweepAfterScanList)))

         if TheBDM.getState()==BDM_SCANNING:
            msgConfirm += ( \
               self.tr('There is currently another scan operation being performed. '
               'Would you like to start the sweep operation after it completes? '))
         elif TheBDM.getState()==BDM_BLOCKCHAIN_READY:
            msgConfirm += ( \
               self.tr('<b>Would you like to start the scan operation right now?</b>'))

         msgConfirm += (self.tr('<br><br>Clicking "No" will abort the sweep operation'))

         confirmed = QMessageBox.question(self, self.tr('Confirm Rescan'), msgConfirm, \
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
      targScript = scrAddr_to_script(ADDRBYTE + sweepAfterScanTarget)
      finishedTx, outVal, fee = self.createSweepAddrTx(sweepList, targScript)

      gt1 = len(sweepList)>1

      if finishedTx==None:
         if (outVal,fee)==(0,0):
            QMessageBox.critical(self, self.tr('Nothing to do'), \
               self.tr('The private key(s) you have provided does not appear to contain '
               'any funds.  There is nothing to sweep.', "", len(sweepList)), \
               QMessageBox.Ok)
            return
         else:
            pladdr = (self.tr('addresses') if gt1 else self.tr('address'))
            QMessageBox.critical(self, self.tr('Cannot sweep'),\
               self.tr('You cannot sweep the funds from the address(es) you specified because '
               'the transaction fee would be greater than or equal to the amount '
               'swept. '
               '<br><br> '
               '<b>Balance of address(es):</b> %1<br> '
               '<b>Fee to sweep address(es):</b> %2 '
               '<br><br>The sweep operation has been canceled.', "", len(sweepList)).arg(coin2str(outVal+fee,maxZeros=0), coin2str(fee,maxZeros=0)), \
               QMessageBox.Ok)
            LOGERROR('Sweep amount (%s) is less than fee needed for sweeping (%s)', \
                     coin2str(outVal+fee, maxZeros=0), coin2str(fee, maxZeros=0))
            return

      # Finally, if we got here, we're ready to broadcast!
      if gt1:
         dispIn  = self.tr('multiple addresses')
      else:
         addrStr = hash160_to_addrStr(sweepList[0].getAddr160())
         dispIn  = self.tr('address <b>%1</b>').arg(addrStr)

      dispOut = self.tr('wallet <b>"%1"</b> (%2) ').arg(wlt.labelName, wlt.uniqueIDB58)
      if DlgVerifySweep(dispIn, dispOut, outVal, fee).exec_():
         self.broadcastTransaction(finishedTx, dryRun=False)

   #############################################################################
   def notifyNewZeroConf(self, leVec):
      '''
      Function that looks at an incoming zero-confirmation transaction queue and
      determines if any incoming transactions were created by Armory. If so, the
      transaction will be passed along to a user notification queue.
      '''
      
      vlen = leVec.size()
      for i in range(0, vlen):
         notifyIn = self.getSettingOrSetDefault('NotifyBtcIn', \
                                                      not OS_MACOSX)
         notifyOut = self.getSettingOrSetDefault('NotifyBtcOut', \
                                                          not OS_MACOSX)
         
         le = leVec[i]
         if (le.getValue() <= 0 and notifyOut) or \
                  (le.getValue() > 0 and notifyIn):
            self.notifyQueue.append([le.getWalletID(), le, False])
      
      self.doTheSystemTrayThing()
            
   #############################################################################
   def broadcastTransaction(self, pytx, dryRun=False):

      if dryRun:
         #DlgDispTxInfo(pytx, None, self, self).exec_()
         return
      else:
         LOGRAWDATA(pytx.serialize(), logging.INFO)
         LOGPPRINT(pytx, logging.INFO)
         newTxHash = binary_to_hex(pytx.getHash())
         self.broadcasting[newTxHash] = pytx

         try:
            LOGINFO('Sending Tx, %s', newTxHash)
            TheBDM.bdv().broadcastZC(pytx.serialize())
         except:
            QMessageBox.warning(self, self.tr('Broadcast failed'), self.tr(
                  'The broadcast process failed unexpectedly. Report this error to '
                  'the development team if this issue occurs repeatedly', QMessageBox.Ok))

   #############################################################################
   def zcBroadcastError(self, txHash, errorMsg):
      try:
         pytx = self.broadcasting[txHash]
      except:
         return
     
      LOGINFO("Failed to broadcast Tx through P2P")
      isTimeoutError = False
      
      errorMsgFromRPC = None
      if errorMsg.startswith("tx broadcast timed out"):
         isTimeoutError = True
         try:
            errorMsgFromRPC = TheBDM.bdv().broadcastThroughRPC(pytx.serialize())
            if errorMsgFromRPC == "success":
               QMessageBox.warning(self, self.tr('Transaction Broadcast'), self.tr(
                  'Your Transaction failed to broadcast through the P2P layer but '
                  'successfully broadcasted through the RPC. This can be a symptom '
                  'of bad node connectivity to the Bitcoin network, or that your '
                  'node is overwhelmed by network traffic. If you consistently get '
                  'this warning, report to the developers for assistance with node '
                  'maintenance.'), 
                  QMessageBox.Ok)
               return
         except:
            LOGERROR("Node RPC is disabled")

      LOGERROR('Transaction was not accepted by the Satoshi client')
      LOGERROR('Raw transaction:')
      LOGRAWDATA(pytx.serialize(), logging.ERROR)
      LOGERROR('Transaction details')
      LOGPPRINT(pytx, logging.ERROR)
      LOGERROR('Failure message: %s' % (errorMsg))
      searchstr  = binary_to_hex(txHash, BIGENDIAN)

      supportURL       = 'https://github.com/goatpig/BitcoinArmory/issues'
      blkexplURL       = BLOCKEXPLORE_URL_TX % searchstr
      blkexplURL_short = BLOCKEXPLORE_URL_TX % searchstr[:20]
      
      if not isTimeoutError:
         QMessageBox.warning(self, self.tr('Transaction Not Accepted'), self.tr(
            'The transaction that you just executed failed with '
            'the following error message: <br><br> '
            '<b>%1</b>'
            '<br><br>'
            '<br><br>On time out errors, the transaction may have actually succeeded '
            'and this message is displayed prematurely.  To confirm whether the '
            'the transaction actually succeeded, you can try this direct link '
            'to %2: '
            '<br><br>'
            '<a href="%3">%4...</a>'
            '<br><br>'
            'If you do not see the '
            'transaction on that webpage within one minute, it failed and you '
            'should attempt to re-send it. '
            'If it <i>does</i> show up, then you do not need to do anything '
            'else -- it will show up in Armory as soon as it receives one '
            'confirmation. '
            '<br><br>If the transaction did fail, it is likely because the fee '
            'is too low. Try again with a higher fee. '
            'If the problem persists, go to "<i>File</i>" -> '
            '"<i>Export Log File</i>" and then attach it to a support '
            'ticket at <a href="%5">%5</a>').arg(errorMsg, BLOCKEXPLORE_NAME, blkexplURL, \
            blkexplURL_short, supportURL), QMessageBox.Ok)
      else:
         if errorMsgFromRPC == None:
            LOGERROR('Broadcast error: %s' % errorMsg)
            QMessageBox.warning(self, self.tr('Transaction Not Accepted'), self.tr(
               'The transaction that you just attempted to broadcast has timed out. '
               '<br><br>'
               'The RPC interface of your node is disabled, therefor Armory cannot '
               'use it to gather more information about the timeout. It is ' 
               'recommended that you enable the RPC and try again.'
               ), QMessageBox.Ok)
         else:
            LOGERROR('Broadcast error: %s' % errorMsgFromRPC)
            QMessageBox.warning(self, self.tr('Transaction Not Accepted'), self.tr(
               'The transaction that you just attempted to broadcast has failed with '
               'the following error: '
               '<br><br><b>%1</b>'
               ).arg(errorMsgFromRPC), QMessageBox.Ok)      



   #############################################################################
   def warnNoImportWhileScan(self):
      extraMsg = ''
      if not self.usermode==USERMODE.Standard:
         extraMsg = ('<br><br>' + \
                     self.tr('In the future, you may avoid scanning twice by '
                     'starting Armory in offline mode (--offline), and '
                     'perform the import before switching to online mode.'))
      QMessageBox.warning(self, self.tr('Armory is Busy'), \
         self.tr('Wallets and addresses cannot be imported while Armory is in '
         'the middle of an existing blockchain scan.  Please wait for '
         'the scan to finish.  ') + extraMsg, QMessageBox.Ok)



   #############################################################################
   def execImportWallet(self):
      sdm = TheSDM.getSDMState()
      bdm = TheBDM.getState()
      if sdm in ['BitcoindInitializing', \
                 'BitcoindSynchronizing'] or \
         bdm in [BDM_SCANNING]:
         QMessageBox.warning(self, self.tr('Scanning'), self.tr(
            'Armory is currently in the middle of scanning the blockchain for '
            'your existing wallets.  New wallets cannot be imported until this '
            'operation is finished.'), QMessageBox.Ok)
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
         QMessageBox.warning(self, self.tr('Duplicate Wallet!'), self.tr(
            'You selected a wallet that has the same ID as one already '
            'in your wallet (%1)!  If you would like to import it anyway, '
            'please delete the duplicate wallet in Armory, first.').arg(wltID), \
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
      reply = QMessageBox.warning(self, self.tr('Be Careful!'), self.tr(
        '<font color="red"><b>WARNING:</b></font> You are about to make an '
        '<u>unencrypted</u> backup of your wallet.  It is highly recommended '
        'that you do <u>not</u> ever save unencrypted wallets to your regular '
        'hard drive.  This feature is intended for saving to a USB key or '
        'other removable media.'), QMessageBox.Ok | QMessageBox.Cancel)
      return (reply==QMessageBox.Ok)


   #############################################################################
   def execAddressBook(self):
      if TheBDM.getState()==BDM_SCANNING:
         QMessageBox.warning(self, self.tr('Blockchain Not Ready'), self.tr(
            'The address book is created from transaction data available in '
            'the blockchain, which has not finished loading.  The address '
            'book will become available when Armory is online.'), QMessageBox.Ok)
      elif TheBDM.getState() in (BDM_UNINITIALIZED,BDM_OFFLINE):
         QMessageBox.warning(self, self.tr('Blockchain Not Ready'), self.tr(
            'The address book is created from transaction data available in '
            'the blockchain, but Armory is currently offline.  The address '
            'book will become available when Armory is online.'), QMessageBox.Ok)
      else:
         if len(self.walletMap)==0:
            QMessageBox.warning(self, self.tr('No wallets!'), self.tr('You have no wallets so '
               'there is no address book to display.'), QMessageBox.Ok)
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
         pytx.setRBF(cppTx.isRBF())

      if pytx==None:
         QMessageBox.critical(self, self.tr('Invalid Tx'), self.tr(
         'The transaction you requested be displayed does not exist in '
         'Armory\'s database.  This is unusual...'), QMessageBox.Ok)
         return

      DlgDispTxInfo( pytx, self.walletMap[wltID], self, self, txtime=txtime).exec_()


   #############################################################################
   def showContextMenuLedger(self):
      menu = QMenu(self.ledgerView)

      if len(self.ledgerView.selectedIndexes())==0:
         return

      row = self.ledgerView.selectedIndexes()[0].row()

      wltID = str(self.ledgerView.model().index(row, LEDGERCOLS.WltID).data().toString())
      txHash = str(self.ledgerView.model().index(row, LEDGERCOLS.TxHash).data().toString())
      txHash = hex_switchEndian(txHash)
      
      amount, flag = self.ledgerView.model().index(row, LEDGERCOLS.Amount).data().toFloat()
      rbf    = self.ledgerView.model().index(row, LEDGERCOLS.optInRBF).data().toBool()
      issts  = self.ledgerView.model().index(row, LEDGERCOLS.toSelf).data().toBool()
      flagged = rbf and (amount < 0 or issts)       

      if flagged:
         actBump    = menu.addAction(self.tr("Bump Fee"))
      actViewTx     = menu.addAction(self.tr("View Details"))
      actViewBlkChn = menu.addAction(self.tr("View on %1").arg(BLOCKEXPLORE_NAME))
      actComment    = menu.addAction(self.tr("Change Comment"))
      actCopyTxID   = menu.addAction(self.tr("Copy Transaction ID"))
      actOpenWallet = menu.addAction(self.tr("Open Relevant Wallet"))
      action = menu.exec_(QCursor.pos())

      if action==actViewTx:
         self.showLedgerTx()
      elif action==actViewBlkChn:
         try:
            DlgBrowserWarn(BLOCKEXPLORE_URL_TX % txHash).exec_()
         except:
            LOGEXCEPT('Failed to open webbrowser')
            QMessageBox.critical(self, self.tr('Could not open browser'), self.tr(
               'Armory encountered an error opening your web browser.  To view '
               'this transaction on blockchain.info, please copy and paste '
               'the following URL into your browser: '
               '<br><br>%1').arg(BLOCKEXPLORE_URL_TX % txHash), QMessageBox.Ok)
      elif action==actCopyTxID:
         clipb = QApplication.clipboard()
         clipb.clear()
         clipb.setText(txHash)
      elif action==actComment:
         self.updateTxCommentFromView(self.ledgerView)
      elif action==actOpenWallet:
         DlgWalletDetails(self.getSelectedWallet(), self.usermode, self, self).exec_()
      elif flagged and action==actBump:
         txHash = hex_switchEndian(txHash)
         self.bumpFee(wltID, txHash)

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
         QMessageBox.warning(self, self.tr('Offline Mode'), self.tr(
           'Armory is currently running in offline mode, and has no '
           'ability to determine balances or create transactions. '
           '<br><br>'
           'In order to send coins from this wallet you must use a '
           'full copy of this wallet from an online computer, '
           'or initiate an "offline transaction" using a watching-only '
           'wallet on an online computer.'), QMessageBox.Ok)
         return
      elif TheBDM.getState()==BDM_SCANNING:
         QMessageBox.warning(self, self.tr('Armory Not Ready'), self.tr(
           'Armory is currently scanning the blockchain to collect '
           'the information needed to create transactions.  This typically '
           'takes between one and five minutes.  Please wait until your '
           'balance appears on the main window, then try again.'), \
            QMessageBox.Ok)
         return

      if len(self.walletMap)==0:
         reply = QMessageBox.information(self, self.tr('No Wallets!'), self.tr(
            'You cannot send any bitcoins until you create a wallet and '
            'receive some coins.  Would you like to create a wallet?'), \
            QMessageBox.Yes | QMessageBox.No)
         if reply==QMessageBox.Yes:
            self.startWalletWizard()
      else:
         DlgSendBitcoins(self.getSelectedWallet(), self, self).exec_()


   #############################################################################
   def uriSendBitcoins(self, uriDict):
      # Because Bitcoin Core doesn't store the message= field we have to assume
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

      descrStr = self.tr('You just clicked on a "bitcoin:" link requesting bitcoins '
                'to be sent to the following address:<br> ')

      descrStr += self.tr('<br>--<b>Address</b>:\t%1 ').arg(uriDict['address'])

      #if uri_has('label'):
         #if len(uriDict['label'])>30:
            #descrStr += '(%s...)' % uriDict['label'][:30]
         #else:
            #descrStr += '(%s)' % uriDict['label']

      amt = 0
      if uri_has('amount'):
         amt     = uriDict['amount']
         amtstr  = coin2str(amt, maxZeros=1)
         descrStr += self.tr('<br>--<b>Amount</b>:\t%1 BTC').arg(amtstr)


      if newMsg:
         if len(newMsg)>60:
            descrStr += self.tr('<br>--<b>Message</b>:\t%1...').arg(newMsg[:60])
         else:
            descrStr += self.tr('<br>--<b>Message</b>:\t%1').arg(newMsg)

      uriDict['message'] = newMsg

      if not uri_has('amount'):
         descrStr += (self.tr('<br><br>There is no amount specified in the link, so '
            'you can decide the amount after selecting a wallet to use '
            'for this transaction. '))
      else:
         descrStr += self.tr('<br><br><b>The specified amount <u>can</u> be changed</b> on the '
            'next screen before hitting the "Send" button. ')


      if len(self.walletMap)==0:
         reply = QMessageBox.information(self, self.tr('No Wallets!'), self.tr(
            'You just clicked on a "bitcoin:" link to send money, but you '
            'currently have no wallets!  Would you like to create a wallet '
            'now?'), QMessageBox.Yes | QMessageBox.No)
         if reply==QMessageBox.Yes:
            self.startWalletWizard()
         return False
      else:
         dlg = DlgSendBitcoins(self.getSelectedWallet(), self, self)
         dlg.frame.prefillFromURI(uriDict)
         dlg.exec_()
      return True


   #############################################################################
   def clickReceiveCoins(self):
      loading = None
      QAPP.processEvents()
      wltID = None
      selectionMade = True
      if len(self.walletMap)==0:
         reply = QMessageBox.information(self, self.tr('No Wallets!'), self.tr(
            'You have not created any wallets which means there is '
            'nowhere to store your bitcoins!  Would you like to '
            'create a wallet now?'), \
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
         dlg = DlgWalletSelect(self, self, self.tr('Receive coins with wallet...'), '', \
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
      if self.logFilePrivacyWarning(wCancel=True):
         self.saveCombinedLogFile()

   #############################################################################
   def logFileTriplePrivacyWarning(self):
      return MsgBoxCustom(MSGBOX.Warning, self.tr('Privacy Warning'), self.tr(
         '<b><u><font size=3>Wallet Analysis Log Files</font></u></b> '
         '<br><br> '
         'The wallet analysis logs contain no personally-identifiable '
         'information, only a record of errors and inconsistencies '
         'found in your wallet file.  No private keys or even public '
         'keys are included. '
         '<br><br>'
         '<b><u><font size=3>Regular Log Files</font></u></b>'
         '<br><br>'
         'The regular log files do not contain any <u>security</u>-sensitive '
         'information, but some users may consider the information to be '
         '<u>privacy</u>-sensitive.  The log files may identify some addresses '
         'and transactions that are related to your wallets.  It is always '
         'recommended you include your log files with any request to the '
         'Armory team, unless you are uncomfortable with the privacy '
         'implications. '
         '<br><br>'
         '<b><u><font size=3>Watching-only Wallet</font></u></b> '
         '<br><br>'
         'A watching-only wallet is a copy of a regular wallet that does not '
         'contain any signing keys.  This allows the holder to see the balance '
         'and transaction history of the wallet, but not spend any of the funds. '
         '<br><br> '
         'You may be requested to submit a watching-only copy of your wallet '
         'to make sure that there is no '
         'risk to the security of your funds.  You should not even consider '
         'sending your '
         'watching-only wallet unless it was specifically requested by an '
         'Armory representative.'), yesStr="&Ok")


   #############################################################################
   def logFilePrivacyWarning(self, wCancel=False):
      return MsgBoxCustom(MSGBOX.Warning, self.tr('Privacy Warning'), self.tr(
         'Armory log files do not contain any <u>security</u>-sensitive '
         'information, but some users may consider the information to be '
         '<u>privacy</u>-sensitive.  The log files may identify some addresses '
         'and transactions that are related to your wallets. '
         '<br><br> '
         '<b>No signing-key data is ever written to the log file</b>. '
         'Only enough data is there to help the Armory developers '
         'track down bugs in the software, but it may still be considered '
         'sensitive information to some users. '
         '<br><br>'
         'Please do not send the log file to the Armory developers if you '
         'are not comfortable with the privacy implications!  However, if you '
         'do not send the log file, it may be very difficult or impossible '
         'for us to help you with your problem.'), wCancel=wCancel, yesStr="&Ok")


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
         fout.write(getLastBytesOfFile(ARMDB_LOG_FILE, 256*1024))
         fout.close()

         LOGINFO('Log saved to %s', saveFile)

   #############################################################################
   def blinkTaskbar(self):
      self.activateWindow()


   #############################################################################
   def lookForBitcoind(self):
      LOGDEBUG('lookForBitcoind')
      if TheSDM.satoshiIsAvailable():
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
            result = QMessageBox.warning(self, self.tr('Already running!'), self.tr(
               'The Bitcoin software appears to be installed now, but it '
               'needs to be closed for Armory to work.  Would you like Armory '
               'to close it for you?'), QMessageBox.Yes | QMessageBox.No)
            if result==QMessageBox.Yes:
               self.closeExistingBitcoin()
               self.startBitcoindIfNecessary()
         elif bitcoindStat=='StillMissing':
            QMessageBox.warning(self, self.tr('Still Missing'), self.tr(
               'The Bitcoin software still appears to be missing.  If you '
               'just installed it, then please adjust your settings to point '
               'to the installation directory.'), QMessageBox.Ok)
         self.startBitcoindIfNecessary()
      elif self.doAutoBitcoind and not TheSDM.isRunningBitcoind():
         if TheSDM.satoshiIsAvailable():
            result = QMessageBox.warning(self, self.tr('Still Running'), self.tr(
               'Bitcoin Core is still running.  Armory cannot start until '
               'it is closed.  Do you want Armory to close it for you?'), \
               QMessageBox.Yes | QMessageBox.No)
            if result==QMessageBox.Yes:
               self.closeExistingBitcoin()
               self.startBitcoindIfNecessary()
         else:
            self.startBitcoindIfNecessary()
      elif TheBDM.getState() in (BDM_OFFLINE,BDM_UNINITIALIZED):
         try:
            TheBDM.goOnline()
            self.switchNetworkMode(NETWORKMODE.Full)
         except Cpp.NoArmoryDBExcept:
            self.switchNetworkMode(NETWORKMODE.Offline)
      else:
         LOGERROR('ModeSwitch button pressed when it should be disabled')
      time.sleep(0.3)
      self.setDashboardDetails()


   #############################################################################
   def setupDashboard(self):
      LOGDEBUG('setupDashboard')
      self.lblBusy = QLabel('')
      self.btnModeSwitch = QPushButton('')
      self.connect(self.btnModeSwitch, SIGNAL('clicked()'), \
                                       self.executeModeSwitch)


      # Will switch this to array/matrix of widgets if I get more than 2 rows
      self.lblDashModeSync    = QRichLabel('',doWrap=False)
      self.lblDashModeSync.setText( self.tr('Node Status'), \
                                        size=4, bold=True, color='Foreground')
      self.lblDashModeBuild   = QRichLabel('',doWrap=False)
      self.lblDashModeScan    = QRichLabel('',doWrap=False)

      self.lblDashModeSync.setAlignment(   Qt.AlignLeft | Qt.AlignVCenter)
      self.lblDashModeBuild.setAlignment(  Qt.AlignLeft | Qt.AlignVCenter)
      self.lblDashModeScan.setAlignment(   Qt.AlignLeft | Qt.AlignVCenter)

      self.barProgressSync    = QProgressBar(self)
      self.barProgressBuild   = QProgressBar(self)
      self.barProgressScan    = QProgressBar(self)

      self.barProgressSync.setRange(0,100)
      self.barProgressScan.setRange(0,100)


      twid = relaxedSizeStr(self,'99 seconds')[0]
      self.lblTimeLeftSync    = QRichLabel('')
      self.lblTimeLeftBuild   = QRichLabel('')
      self.lblTimeLeftScan    = QRichLabel('')

      self.lblTimeLeftSync.setMinimumWidth(twid)
      self.lblTimeLeftScan.setMinimumWidth(twid)

      layoutDashMode = QGridLayout()

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
      self.dashBtns = [[None]*3 for i in range(3)]
      self.dashBtns[DASHBTNS.Close   ][BTN] = QPushButton(self.tr('Close Bitcoin Process'))
      self.dashBtns[DASHBTNS.Browse  ][BTN] = QPushButton(self.tr('Open https://bitcoin.org'))
      self.dashBtns[DASHBTNS.Settings][BTN] = QPushButton(self.tr('Change Settings'))

      # The "Now shutting down" frame
      self.lblShuttingDown    = QRichLabel('', doWrap=False)
      self.lblShuttingDown.setText(self.tr('Preparing to shut down..'), \
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
         DlgBrowserWarn('https://bitcoin.org/en/download').exec_()



      self.connect(self.dashBtns[DASHBTNS.Close][BTN], SIGNAL('clicked()'), \
                                                   self.closeExistingBitcoin)
      self.connect(self.dashBtns[DASHBTNS.Browse][BTN], SIGNAL('clicked()'), \
                                                             openBitcoinOrg)
      self.connect(self.dashBtns[DASHBTNS.Settings][BTN], SIGNAL('clicked()'), \
                                                           self.openSettings)

      self.dashBtns[DASHBTNS.Close][LBL] = QRichLabel( \
           self.tr('Stop existing Bitcoin processes so that Armory can open its own'))
      self.dashBtns[DASHBTNS.Browse][LBL]     = QRichLabel( \
           self.tr('Open browser to Bitcoin webpage to download and install Bitcoin software'))
      self.dashBtns[DASHBTNS.Settings][LBL]  = QRichLabel( \
           self.tr('Open Armory settings window to change Bitcoin software management'))


      self.dashBtns[DASHBTNS.Browse][TTIP] = self.createToolTipWidget( self.tr(
           'Will open your default browser to https://bitcoin.org where you can '
           'download the latest version of Bitcoin Core, and get other information '
           'and links about Bitcoin, in general.'))
      self.dashBtns[DASHBTNS.Settings][TTIP] = self.createToolTipWidget( self.tr(
           'Change Bitcoin Core/bitcoind management settings or point Armory to '
           'a non-standard Bitcoin installation'))
      self.dashBtns[DASHBTNS.Close][TTIP] = self.createToolTipWidget( self.tr(
           'Armory has detected a running Bitcoin Core or bitcoind instance and '
           'will force it to exit'))

      self.frmDashMgmtButtons = QFrame()
      self.frmDashMgmtButtons.setFrameStyle(STYLE_SUNKEN)
      layoutButtons = QGridLayout()
      layoutButtons.addWidget(self.lblDashBtnDescr, 0,0, 1,3)
      for r in range(3):
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
      QMessageBox.warning(self, self.tr('Not Found'), self.tr(
         'Attempted to kill the running Bitcoin Core/bitcoind instance, '
         'but it was not found.'), QMessageBox.Ok)

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
      
      sdmState = TheSDM.getSDMState()
      sdmStr = TheSDM.getSDMStateStr()
               

      if TheBDM.getState()==BDM_SCANNING:
         
         self.lblDashModeSync.setVisible(False)
         self.barProgressSync.setVisible(False)
         self.lblTimeLeftSync.setVisible(False)

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
         self.lblTimeLeftScan.setVisible(False)

         phase,pct,tleft,numericProgress = TheBDM.predictLoadTime()
         if phase==Cpp.BDMPhase_DBHeaders:
            self.lblDashModeBuild.setText( self.tr('Loading Database Headers'), \
                                        size=4, bold=True, color='Foreground')
            self.lblDashModeScan.setText( self.tr('Scan Transaction History'), \
                                        size=4, bold=True, color='DisableFG')
            self.barProgressBuild.setFormat('%p%')
            self.barProgressScan.setFormat('')
            self.barProgressBuild.setRange(0,100)

         elif phase==Cpp.BDMPhase_OrganizingChain:
            self.lblDashModeBuild.setText( self.tr('Organizing Blockchain'), \
                                        size=4, bold=True, color='Foreground')
            self.lblDashModeScan.setText( self.tr('Scan Transaction History'), \
                                        size=4, bold=True, color='DisableFG')
            self.barProgressBuild.setFormat('')
            self.barProgressScan.setFormat('')
            self.barProgressBuild.setValue(0)
            self.barProgressBuild.setRange(0,0)
            self.lblTimeLeftBuild.setVisible(False)
            self.lblTimeLeftScan.setVisible(False)
         elif phase==Cpp.BDMPhase_BlockHeaders:
            self.lblDashModeBuild.setText( self.tr('Reading New Block Headers'), \
                                        size=4, bold=True, color='Foreground')
            self.lblDashModeScan.setText( self.tr('Scan Transaction History'), \
                                        size=4, bold=True, color='DisableFG')
            self.barProgressBuild.setFormat('%p%')
            self.barProgressScan.setFormat('')
            self.barProgressBuild.setRange(0,100)
         elif phase==Cpp.BDMPhase_BlockData:
            self.lblDashModeBuild.setText( self.tr('Building Databases'), \
                                        size=4, bold=True, color='Foreground')
            self.lblDashModeScan.setText( self.tr('Scan Transaction History'), \
                                        size=4, bold=True, color='DisableFG')
            self.barProgressBuild.setFormat('%p%')
            self.barProgressScan.setFormat('')
            self.barProgressBuild.setRange(0,100)
         elif phase==Cpp.BDMPhase_Rescan:
            self.lblDashModeBuild.setText( self.tr('Build Databases'), \
                                        size=4, bold=True, color='DisableFG')
            self.lblDashModeScan.setText( self.tr('Scanning Transaction History'), \
                                        size=4, bold=True, color='Foreground')
            self.lblTimeLeftBuild.setVisible(False)
            self.barProgressBuild.setFormat('')
            self.barProgressBuild.setValue(100)
            self.barProgressBuild.setRange(0,100)
            self.barProgressScan.setFormat('%p%')
         elif phase==Cpp.BDMPhase_Balance:
            self.lblDashModeBuild.setText( self.tr('Build Databases'), \
                                        size=4, bold=True, color='DisableFG')
            self.lblDashModeScan.setText( self.tr('Computing Balances'), \
                                        size=4, bold=True, color='Foreground')
            self.barProgressBuild.setFormat('')
            self.barProgressScan.setFormat('')
            self.barProgressBuild.setValue(0)
            self.barProgressBuild.setRange(0,0)
            self.lblTimeLeftBuild.setVisible(False)   
         elif phase==Cpp.BDMPhase_SearchHashes:
            self.lblDashModeBuild.setText( self.tr('Build Databases'), \
                                        size=4, bold=True, color='DisableFG')
            self.lblDashModeScan.setText( self.tr('Parsing Tx Hashes'), \
                                        size=4, bold=True, color='Foreground')
            self.lblTimeLeftBuild.setVisible(False)
            self.barProgressBuild.setFormat('')
            self.barProgressBuild.setValue(100)
            self.barProgressBuild.setRange(0,100)
            self.lblTimeLeftScan.setVisible(False)
            self.barProgressScan.setFormat('')
            self.barProgressScan.setValue(0)
            self.barProgressScan.setRange(0,0)
            self.lblTimeLeftScan.setVisible(False)     
         elif phase==Cpp.BDMPhase_ResolveHashes:
            self.lblDashModeBuild.setText( self.tr('Build Databases'), \
                                        size=4, bold=True, color='DisableFG')
            self.lblDashModeScan.setText( self.tr('Resolving Tx Hashes'), \
                                        size=4, bold=True, color='Foreground')
            self.lblTimeLeftBuild.setVisible(False)
            self.barProgressBuild.setFormat('')
            self.barProgressBuild.setValue(100)
            self.barProgressBuild.setRange(0,100)
            self.lblTimeLeftBuild.setVisible(False)
            self.barProgressScan.setFormat('')
            self.barProgressScan.setValue(100)
            self.barProgressScan.setRange(0,100)
            self.barProgressScan.setFormat('%p%')  
       
         showPct = True
         if tleft != 2**32 - 1:
            tstring = secondsToHumanTime(tleft)
         else:
            tstring = "N/A"
            showPct = False
         pvalue = pct*100

         if showPct:
            if phase==BDMPhase_BlockHeaders or phase==BDMPhase_BlockData or phase==BDMPhase_DBHeaders:
               self.lblTimeLeftBuild.setText(tstring)
               self.barProgressBuild.setValue(pvalue)
            elif phase==BDMPhase_Rescan or BDMPhase_ResolveHashes:
               self.lblTimeLeftScan.setText(tstring)
               self.barProgressScan.setValue(pvalue)
               self.lblTimeLeftScan.setVisible(True)

      elif sdmStr in ['NodeStatus_Initializing','NodeStatus_Syncing']:

         self.lblDashModeSync.setVisible(True)
         self.barProgressSync.setVisible(True)
         self.lblTimeLeftSync.setVisible(True)
         self.barProgressSync.setFormat('%p%')
         self.barProgressSync.setRange(0,100)
         
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

         
         if sdmStr == 'NodeStatus_Syncing':
            sdmPercent = sdmState.chainState_.getProgressPct() * 100
            self.lblTimeLeftSync.setText(\
               "%d blocks remaining" % sdmState.chainState_.getBlocksLeft())

         elif sdmStr == 'NodeStatus_Initializing':
            sdmPercent = 0
            self.barProgressSync.setRange(0,0)

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
         return self.tr( \
         'The following functionalities are available while scanning in offline mode:'
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
         return self.tr( \
         'The following functionalities are available in offline mode:'
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
         return self.tr( \
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
         return self.tr(
         'For more information about Armory, and even Bitcoin itself, you should '
         'visit the <a href="https://bitcointalk.org/index.php?board=97.0">Armory Forum</a> '
	     'and <a href="https://bitcoin.org">Bitcoin.org</a>.  If '
         'you are experiencing problems using this software, please visit the '
         '<a href="https://bitcointalk.org/index.php?board=97.0">Armory Forum</a>. Users '
	     'there will help you with any issues that you have. '
         '<br><br>'
         '<b><u>IMPORTANT:</u></b> Make a backup of your wallet(s)!  Paper '
         'backups protect you <i>forever</i> against forgotten passwords, '
         'hard-drive failure, and make it easy for your family to recover '
         'your funds if something terrible happens to you.  <i>Each wallet '
         'only needs to be backed up once, ever!</i>  Without it, you are at '
         'risk of losing all of your Bitcoins! '
         '<br><br>')
      elif state == 'OnlineFull1':
         return self.tr( \
         '<p><b>You now have access to all the features Armory has to offer!</b><br>'
         'To see your balances and transaction history, please click '
         'on the "Transactions" tab above this text.  <br>'
         'Here\'s some things you can do with Armory Bitcoin Client:'
         '<br>')
      elif state == 'OnlineFull2':
         return ( \
         (self.tr('If you experience any performance issues with Armory, '
         'please confirm that Bitcoin Core is running and <i>fully '
         'synchronized with the Bitcoin network</i>.  You will see '
         'a green checkmark in the bottom right corner of the '
         'Bitcoin Core window if it is synchronized.  If not, it is '
         'recommended you close Armory and restart it only when you '
         'see that checkmark.'
         '<br><br>')  if not self.doAutoBitcoind else '') + self.tr(
         '<b>Please backup your wallets!</b>  Armory wallets are '
         '"deterministic", meaning they only need to be backed up '
         'one time (unless you have imported external addresses/keys). '
         'Make a backup and keep it in a safe place!  All funds from '
         'Armory-generated addresses will always be recoverable with '
         'a paper backup, any time in the future.  Use the "Backup '
         'Individual Keys" option for each wallet to backup imported '
         'keys.</p>'))
      elif state == 'OnlineNeedSweep':
         return self.tr( \
         'Armory is currently online, but you have requested a sweep operation '
         'on one or more private keys.  This requires searching the global '
         'transaction history for the available balance of the keys to be '
         'swept. '
         '<br><br>'
         'Press the button to start the blockchain scan, which '
         'will also put Armory into offline mode for a few minutes '
         'until the scan operation is complete.')
      elif state == 'OnlineDirty':
         return self.tr( \
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
         return self.tr( \
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
         'If you do not have Bitcoin Core installed, you can '
         'download it from <a href="https://bitcoin.org">'
         'https://bitcoin.org</a>.')

      # Branch the available display text based on which Satoshi-Management
      # mode Armory is using.  It probably wasn't necessary to branch the
      # the code like this, but it helped me organize the seemingly-endless
      # number of dashboard screens I need
      if mgmtMode.lower()=='user':
         if state == 'OfflineButOnlinePossible':
            return self.tr( \
            'You are currently in offline mode, but can '
            'switch to online mode by pressing the button above.  However, '
            'it is not recommended that you switch until '
            'Bitcoin Core/bitcoind is fully synchronized with the bitcoin network.  '
            'You will see a green checkmark in the bottom-right corner of '
            'the Bitcoin Core window when it is finished.'
            '<br><br>'
            'Switching to online mode will give you access '
            'to more Armory functionality, including sending and receiving '
            'bitcoins and viewing the balances and transaction histories '
            'of each of your wallets.<br><br>')
         elif state == 'OfflineNoSatoshi':
            bitconf = os.path.join(BTC_HOME_DIR, 'bitcoin.conf')
            return self.tr( \
            'You are currently in offline mode because '
            'Bitcoin Core is not running.  To switch to online '
            'mode, start Bitcoin Core and let it synchronize with the network '
            '-- you will see a green checkmark in the bottom-right corner when '
            'it is complete.  If Bitcoin Core is already running and you believe '
            'the lack of connection is an error (especially if using proxies), '
            'please see <a href="'
            'https://bitcointalk.org/index.php?topic=155717.msg1719077#msg1719077">'
            'this link</a> for options.'
            '<br><br>'
            '<b>If you prefer to have Armory do this for you</b>, '
            'then please check "Let Armory run '
            'Bitcoin Core in the background" under "File"->"Settings."'
            '<br><br>'
            'If you already know what you\'re doing and simply need '
            'to fetch the latest version of Bitcoin Core, you can download it from '
            '<a href="https://bitcoin.org">https://bitcoin.org</a>.')
         elif state == 'OfflineNoInternet':
            return self.tr( \
            'You are currently in offline mode because '
            'Armory could not detect an internet connection.  '
            'If you think this is in error, then '
            'restart Armory using the " --skip-online-check" option, '
            'or adjust the Armory settings.  Then restart Armory.'
            '<br><br>'
            'If this is intended to be an offline computer, note '
            'that it is not necessary to have Bitcoin Core or bitcoind '
            'running.' )
         elif state == 'OfflineNoBlkFiles':
            return self.tr( \
            'You are currently in offline mode because '
            'Armory could not find the blockchain files produced '
            'by Bitcoin Core.  Do you run Bitcoin Core (or bitcoind) '
            'from a non-standard directory?   Armory expects to '
            'find the blkXXXX.dat files in <br><br>%1<br><br> '
            'If you know where they are located, please restart '
            'Armory using the " --satoshi-datadir=[path]" '
            'to notify Armory where to find them.').arg(BLKFILE_DIR)
         elif state == 'Disconnected':
            return self.tr( \
            'Armory was previously online, but the connection to Bitcoin Core/'
            'bitcoind was interrupted.  You will not be able to send bitcoins '
            'or confirm receipt of bitcoins until the connection is '
            'reestablished.  <br><br>Please check that Bitcoin Core is open '
            'and synchronized with the network.  Armory will <i>try to '
            'reconnect</i> automatically when the connection is available '
            'again.  If Bitcoin Core is available again, and reconnection does '
            'not happen, please restart Armory.<br><br>')
         elif state == 'ScanNoWallets':
            return self.tr( \
            'Please wait while the global transaction history is scanned. '
            'Armory will go into online mode automatically, as soon as '
            'the scan is complete.')
         elif state == 'ScanWithWallets':
            return self.tr( \
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
            return self.tr( \
            'It appears you are already running Bitcoin software '
            '(Bitcoin Core or bitcoind). '
            'Unlike previous versions of Armory, you should <u>not</u> run '
            'this software yourself --  Armory '
            'will run it in the background for you.  Either close the '
            'Bitcoin application or adjust your settings.  If you change '
            'your settings, then please restart Armory.')
         if state == 'OfflineNeedBitcoinInst':
            return self.tr( \
            '<b>Only one more step to getting online with Armory!</b>   You '
            'must install the Bitcoin software from https://bitcoin.org in order '
            'for Armory to communicate with the Bitcoin network.  If the '
            'Bitcoin software is already installed and/or you would prefer '
            'to manage it yourself, please adjust your settings and '
            'restart Armory.')
         if state == 'InitializingLongTime':
            return self.tr(
            '<b>To maximize your security, the Bitcoin engine is downloading '
            'and verifying the global transaction ledger.  <u>This will take '
            'several hours, but only needs to be done once</u>!</b>  It is '
            'usually best to leave it running over night for this '
            'initialization process.  Subsequent loads will only take a few '
            'minutes. '
            '<br><br> '
            '<b>Please Note:</b> Between Armory and the underlying Bitcoin '
            'engine, you need to have 120-130 GB of spare disk space available '
            'to hold the global transaction history. '
            '<br><br> '
            'While you wait, you can manage your wallets.  Make new wallets, '
            'make digital or paper backups, create Bitcoin addresses to receive '
            'payments, '
            'sign messages, and/or import private keys.  You will always '
            'receive Bitcoin payments regardless of whether you are online, '
            'but you will have to verify that payment through another service '
            'until Armory is finished this initialization.')
         if state == 'InitializingDoneSoon':
            msg = self.tr( \
            'The software is downloading and processing the latest activity '
            'on the network related to your wallet(s).  This should take only '
            'a few minutes.  While you wait, you can manage your wallet(s).  '
            '<br><br>'
            'Now would be a good time to make paper (or digital) backups of '
            'your wallet(s) if you have not done so already!  You are protected '
            '<i>forever</i> from hard-drive loss, or forgetting your password. '
            'If you do not have a backup, you could lose all of your '
            'Bitcoins forever!', "", len(self.walletMap))

            return msg
         if state == 'OnlineDisconnected':
            return self.tr( \
            'Armory\'s communication with the Bitcoin network was interrupted. '
            'This usually does not happen unless you closed the process that '
            'Armory was using to communicate with the network. Armory requires '
            '%1 to be running in the background, and this error pops up if it '
            'disappears.'
            '<br><br>You may continue in offline mode, or you can close '
            'all Bitcoin processes and restart Armory.').arg(os.path.basename(TheSDM.executable))
         if state == 'OfflineBadConnection':
            return self.tr( \
            'Armory has experienced an issue trying to communicate with the '
            'Bitcoin software.  The software is running in the background, '
            'but Armory cannot communicate with it through RPC as it expects '
            'to be able to.  If you changed any settings in the Bitcoin home '
            'directory, please make sure that RPC is enabled and that it is '
            'accepting connections from localhost.  '
            '<br><br>'
            'If you have not changed anything, please export the log file '
            '(from the "File" menu) and open an issue at https://github.com/goatpig/BitcoinArmory/issues')
         if state == 'OfflineSatoshiAvail':
            return self.tr( \
            'Armory does not detect internet access, but it does detect '
            'running Bitcoin software.  Armory is in offline-mode. <br><br>'
            'If you are intending to run an offline system, you will not '
            'need to have the Bitcoin software installed on the offline '
            'computer.  It is only needed for the online computer. '
            'If you expected to be online and '
            'the absence of internet is an error, please restart Armory '
            'using the "--skip-online-check" option.  ')
         if state == 'OfflineForcedButSatoshiAvail':
            return self.tr( \
            'Armory was started in offline-mode, but detected you are '
            'running Bitcoin software.  If you are intending to run an '
            'offline system, you will <u>not</u> need to have the Bitcoin '
            'software installed or running on the offline '
            'computer.  It is only required for being online. ')
         if state == 'OfflineBadDBEnv':
            return self.tr( \
            'The Bitcoin software indicates there '
            'is a problem with its databases.  This can occur when '
            'Bitcoin Core/bitcoind is upgraded or downgraded, or sometimes '
            'just by chance after an unclean shutdown.'
            '<br><br>'
            'You can either revert your installed Bitcoin software to the '
            'last known working version (but not earlier than version 0.8.1) '
            'or delete everything <b>except</b> "wallet.dat" from your Bitcoin '
            'home directory '
            '<font face="courier"><b>%1</b></font>'
            '<br><br>'
            'If you choose to delete the contents of the Bitcoin home '
            'directory, you will have to do a fresh download of the blockchain '
            'again, which will require a few hours the first '
            'time.').arg(self.satoshiHomePath)
         if state == 'OfflineBtcdCrashed':
            sout = '' if TheSDM.btcOut==None else str(TheSDM.btcOut)
            serr = '' if TheSDM.btcErr==None else str(TheSDM.btcErr)
            soutHtml = '<br><br>' + '<br>'.join(sout.strip().split('\n'))
            serrHtml = '<br><br>' + '<br>'.join(serr.strip().split('\n'))
            soutDisp = '<b><font face="courier">StdOut: %s</font></b>' % soutHtml
            serrDisp = '<b><font face="courier">StdErr: %s</font></b>' % serrHtml
            if len(sout)>0 or len(serr)>0:
               return  (self.tr(
               'There was an error starting the underlying Bitcoin engine. '
               'This should not normally happen.  Usually it occurs when you '
               'have been using Bitcoin Core prior to using Armory, especially '
               'if you have upgraded or downgraded Bitcoin Core recently. '
               'Output from bitcoind:<br>') + \
               (soutDisp if len(sout)>0 else '') + \
               (serrDisp if len(serr)>0 else '') )
            else:
               return ( self.tr(
                  'There was an error starting the underlying Bitcoin engine. '
                  'This should not normally happen.  Usually it occurs when you '
                  'have been using Bitcoin Core prior to using Armory, especially '
                  'if you have upgraded or downgraded Bitcoin Core recently. '
                  '<br><br> '
                  'Unfortunately, this error is so strange, Armory does not '
                  'recognize it.  Please go to "Export Log File" from the "File" '
                  'menu and submit an issue at https://github.com/goatpig/BitcoinArmory/issues. '
                  'We apologize for the inconvenience!'))

   # TODO - move out of polling and call on events
   #############################################################################

   def setDashboardDetails(self, INIT=False):
      """
      We've dumped all the dashboard text into the above 2 methods in order
      to declutter this method.
      """
      if self.isShuttingDown:
         return

      sdmStr = TheSDM.getSDMStateStr()
      
      bdmState = TheBDM.getState()
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

      def setBuildRowVisible(b):
         self.lblDashModeBuild.setVisible(b)
         self.barProgressBuild.setVisible(b)
         self.lblTimeLeftBuild.setVisible(b)

      def setScanRowVisible(b):
         self.lblDashModeScan.setVisible(b)
         self.barProgressScan.setVisible(b)
         self.lblTimeLeftScan.setVisible(b)

      def setOnlyDashModeVisible():
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

      if sdmStr != self.lastSDMStr:
         if sdmStr == "NodeStatus_Offline":
            # User is letting Armory manage the Satoshi client for them.
   
            setSyncRowVisible(False)
            self.lblBusy.setVisible(False)
            self.btnModeSwitch.setVisible(False)
   
            # There's a whole bunch of stuff that has to be hidden/shown
            # depending on the state... set some reasonable defaults here
            setBtnFrameVisible(False)
            setBtnRowVisible(DASHBTNS.Browse, False)
            setBtnRowVisible(DASHBTNS.Settings, True)
            setBtnRowVisible(DASHBTNS.Close, False)
   
            if self.internetStatus == INTERNET_STATUS.Unavailable or CLI_OPTIONS.offline:
               self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)
               setOnlyDashModeVisible()
               self.lblDashModeSync.setText( self.tr('Armory is <u>offline</u>'), \
                                               size=4, color='TextWarn', bold=True)
               if TheSDM.satoshiIsAvailable():
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
                     self.tr('In case you actually do have internet access, you can use '
                     'the following links to get Armory installed.  Or change '
                     'your settings.'))
                  setBtnRowVisible(DASHBTNS.Browse, True)
                  setBtnRowVisible(DASHBTNS.Settings, True)
                  #setBtnRowVisible(DASHBTNS.Instruct, not OS_WINDOWS)
                  descr1 += self.GetDashStateText('Auto','OfflineNoSatoshiNoInternet')
                  descr2 += self.GetDashFunctionalityText('Offline')
                  self.lblDashDescr1.setText(descr1)
                  self.lblDashDescr2.setText(descr2)
                  
         elif sdmStr == "NodeStatus_BadPath":
            setOnlyDashModeVisible()
            self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)
            self.lblDashModeSync.setText( self.tr('Armory is <u>offline</u>'), \
                                             size=4, color='TextWarn', bold=True)
      
            LOGINFO('Dashboard switched to auto-cannotFindExeHome')
            self.lblDashModeSync.setText(self.tr('Cannot find Bitcoin Home Directory'), \
                                                            size=4, bold=True)
            setBtnRowVisible(DASHBTNS.Close, TheSDM.satoshiIsAvailable())
            setBtnRowVisible(DASHBTNS.Install, True)
            setBtnRowVisible(DASHBTNS.Browse, True)
            setBtnRowVisible(DASHBTNS.Settings, True)
            #setBtnRowVisible(DASHBTNS.Instruct, not OS_WINDOWS)
            self.btnModeSwitch.setVisible(True)
            self.btnModeSwitch.setText(self.tr('Check Again'))
            setBtnFrameVisible(True)
            descr1 += self.GetDashStateText('Auto', 'OfflineNeedBitcoinInst')
            descr2 += self.GetDashStateText('Auto', 'NewUserInfo')
            descr2 += self.GetDashFunctionalityText('Offline')
            self.lblDashDescr1.setText(descr1)
            self.lblDashDescr2.setText(descr2)
                     
         elif sdmStr == "NodeStatus_Initializing" or \
            sdmStr == "NodeStatus_Syncing":
            self.wasSynchronizing = True
            LOGINFO('Dashboard switched to auto-InitSync')
            self.lblBusy.setVisible(True)
            self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, False)
            self.updateSyncProgress()
   
   
            # If torrent ever ran, leave it visible
            setSyncRowVisible(True)
            setScanRowVisible(True)
   
            if sdmStr == "NodeStatus_Initializing":
               self.lblDashModeSync.setText( self.tr('Initializing Bitcoin Engine'), size=4, bold=True, color='Foreground')
            elif sdmStr == "NodeStatus_Syncing":
               self.lblDashModeSync.setText( self.tr('Synchronizing with Network'), size=4, bold=True, color='Foreground')
   
   
            self.lblDashModeBuild.setText( self.tr('Build Databases'), \
                                          size=4, bold=True, color='DisableFG')
            self.lblDashModeScan.setText( self.tr('Scan Transaction History'), \
                                          size=4, bold=True, color='DisableFG')
   
            descr1 += self.GetDashStateText('Auto', 'InitializingDoneSoon')
            descr2 += self.GetDashStateText('Auto', 'NewUserInfo')
   
            setBtnRowVisible(DASHBTNS.Settings, True)
            setBtnFrameVisible(True, \
               self.tr('Since version 0.88, Armory runs bitcoind in the '
                  'background.  You can switch back to '
                  'the old way in the Settings dialog. '))
   
            descr2 += self.GetDashFunctionalityText('Offline')
            self.lblDashDescr1.setText(descr1)
            self.lblDashDescr2.setText(descr2)
            
      self.lastSDMStr = sdmStr
     
         
      if bdmState == BDM_BLOCKCHAIN_READY:
         setOnlyDashModeVisible()
         self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, True)
         self.lblBusy.setVisible(False)
         if self.netMode == NETWORKMODE.Disconnected:
            self.btnModeSwitch.setVisible(False)
            self.lblDashModeSync.setText( self.tr('Armory is disconnected'), size=4, color='TextWarn', bold=True)
            descr  = self.GetDashStateText('User','Disconnected')
            descr += self.GetDashFunctionalityText('Offline')
            self.lblDashDescr1.setText(descr)
         else:
            # Fully online mode
            self.btnModeSwitch.setVisible(False)
            self.lblDashModeSync.setText( self.tr('Armory is online!'), color='TextGreen', size=4, bold=True)
            self.mainDisplayTabs.setTabEnabled(self.MAINTABS.Ledger, True)
            descr  = self.GetDashStateText('User', 'OnlineFull1')
            descr += self.GetDashFunctionalityText('Online')
            descr += self.GetDashStateText('User', 'OnlineFull2')
            self.lblDashDescr1.setText(descr)

      elif bdmState == BDM_SCANNING or bdmState == BDM_UNINITIALIZED:
         LOGINFO('Dashboard switched to "Scanning" mode')
         setSyncRowVisible(False)
         self.lblDashModeScan.setVisible(True)
         self.barProgressScan.setVisible(True)
         self.lblTimeLeftScan.setVisible(True)
         self.lblBusy.setVisible(True)
         self.btnModeSwitch.setVisible(False)

         if sdmStr == 'NodeStatus_Ready':
            self.barProgressSync.setVisible(True)
            self.lblTimeLeftSync.setVisible(True)
            self.lblDashModeSync.setVisible(True)
            self.lblTimeLeftSync.setText('')
            self.lblDashModeSync.setText( self.tr('Synchronizing with Network'), \
                                    size=4, bold=True, color='DisableFG')
         else:
            self.barProgressSync.setVisible(False)
            self.lblTimeLeftSync.setVisible(False)
            self.lblDashModeSync.setVisible(False)

         if len(unicode(self.lblDashModeBuild.text()).strip()) == 0:
            self.lblDashModeBuild.setText( self.tr('Preparing Databases'), \
                                          size=4, bold=True, color='Foreground')
            
         if len(unicode(self.lblDashModeScan.text()).strip()) == 0:
            self.lblDashModeScan.setText( self.tr('Scan Transaction History'), \
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
      elif bdmState == BDM_OFFLINE:
         pass
      else:
         LOGERROR('What the heck blockchain mode are we in?  %s', bdmState)

      self.lblDashModeSync.setContentsMargins( 50,5,50,5)
      self.lblDashModeBuild.setContentsMargins(50,5,50,5)
      self.lblDashModeScan.setContentsMargins( 50,5,50,5)
      vbar = self.dashScrollArea.verticalScrollBar()

      # On Macs, this causes the main window scroll area to keep bouncing back
      # to the top. Not setting the value seems to fix it. DR - 2014/02/12
      if not OS_MACOSX:
         vbar.setValue(vbar.minimum())

      if self.lblBusy.isVisible():
         self.numHeartBeat += 1
         self.lblBusy.setPixmap(QPixmap(':/loadicon_%d.png' % \
                                             (self.numHeartBeat%6)))

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
   def updateWalletData(self):
      for wltid in self.walletMap:
         self.walletMap[wltid].getBalancesAndCountFromDB()
         self.walletMap[wltid].getAddrDataFromDB()
         
      for lbid in self.cppLockboxWltMap:
         self.cppLockboxWltMap[lbid].getBalancesAndCountFromDB(\
            TheBDM.topBlockHeight, IGNOREZC)
      
   #############################################################################      
   def updateStatusBarText(self):
      if self.nodeStatus.status_ == Cpp.NodeStatus_Online:
         
         haveRPC = (self.nodeStatus.rpcStatus_ == RpcStatus_Online)
         
         if haveRPC:           
            self.lblArmoryStatus.setText(\
               self.tr('<font color=%1>Connected (%2 blocks)</font> ').arg(
                  htmlColor('TextGreen'), str(TheBDM.getTopBlockHeight())))
         else:
            self.lblArmoryStatus.setText(\
               self.tr('<font color=%1><b>Connected (%2 blocks)</b></font> ').arg(
                  htmlColor('TextPurple'), str(TheBDM.getTopBlockHeight())))            
                  
         def getToolTipTextOnline():
            tt = QString()
            if not haveRPC:
               tt = self.tr('RPC disabled!<br><br>')
            blkRecvAgo  = RightNow() - self.blkReceived
            tt = tt + self.tr('Last block received %1 ago').arg(secondsToHumanTime(blkRecvAgo))
            return tt
         
         self.lblArmoryStatus.setToolTipLambda(getToolTipTextOnline)
         
      elif self.nodeStatus.status_ == Cpp.NodeStatus_Offline:
         self.lblArmoryStatus.setText(\
               self.tr('<font color=%1><b>Node offline (%2 blocks)</b></font> ').arg(\
                  htmlColor('TextRed')).arg(TheBDM.getTopBlockHeight()))    
         
         def getToolTipTextOffline():
            blkRecvAgo  = RightNow() - self.blkReceived
            tt = self.tr(
            'Disconnected from Bitcoin Node, cannot update history '
            '<br><br>Last known block: %1 <br>Received %2 ago').arg(TheBDM.getTopBlockHeight()).arg(secondsToHumanTime(blkRecvAgo))
            return tt
         
         self.lblArmoryStatus.setToolTipLambda(getToolTipTextOffline)     

   #############################################################################
   def handleCppNotification(self, action, args):

      if action == FINISH_LOAD_BLOCKCHAIN_ACTION:
         #Blockchain just finished loading, finish initializing UI and render the
         #ledgers
         
         self.nodeStatus = TheBDM.bdv().getNodeStatus()
         TheBDM.setWitness(self.nodeStatus.SegWitEnabled_)

         try:
            self.updateWalletData()
         except Exception as e:
            LOGERROR("Failed update wallet data with error: %s" % e)
            return

         for wltid in self.walletMap:
            self.walletMap[wltid].detectHighestUsedIndex()

         self.blkReceived = RightNow()
         if self.needUpdateAfterScan:
            LOGDEBUG('Running finishLoadBlockchain')
            self.finishLoadBlockchainGUI()
            self.needUpdateAfterScan = False
            self.setDashboardDetails()
         
         self.updateStatusBarText()
         
      elif action == NEW_ZC_ACTION and not CLI_OPTIONS.ignoreZC:
         #A zero conf Tx conerns one of the address Armory is tracking, pull the
         #updated ledgers from the BDM and create the related notifications.

         try:
            self.updateWalletData()
         except Exception as e:
            LOGERROR("Failed update wallet data with error: %s" % e)
            return

         self.notifyNewZeroConf(args)
         self.createCombinedLedger()

      elif action == NEW_BLOCK_ACTION:
         #A new block has appeared, pull updated ledgers from the BDM, display
         #the new block height in the status bar and note the block received time

         try:
            self.updateWalletData()
         except Exception as e:
            LOGERROR("Failed update wallet data with error: %s" % e)
            return

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


            # Update the wallet view to immediately reflect new balances
            self.walletModel.reset()
            self.updateStatusBarText()
            
      elif action == REFRESH_ACTION:
         #The wallet ledgers have been updated from an event outside of new ZC
         #or new blocks (usually a wallet or address was imported, or the
         #wallet filter was modified)

         try:
            self.updateWalletData()
         except Exception as e:
            LOGERROR("Failed update wallet data with error: %s" % e)
            return

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
                  
               if wltID in self.oneTimeScanAction:
                  postScanAction = self.oneTimeScanAction[wltID]
                  del self.oneTimeScanAction[wltID]
                  if callable(postScanAction):
                     postScanAction()

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

      elif action == WARNING_ACTION:
         #something went wrong on the C++ side, create a message box to report
         #it to the user
         if 'rescan' in args[0].lower() or 'rebuild' in args[0].lower():
            result = MsgBoxWithDNAA(self, self, MSGBOX.Critical, self.tr('BDM error!'), args[0],
                                    self.tr("Rebuild and rescan on next start"), dnaaStartChk=False)
            if result[1] == True:
               touchFile( os.path.join(ARMORY_HOME_DIR, 'rebuild.flag') )
         
         elif 'factory reset' in args[0].lower():
            result = MsgBoxWithDNAA(self, self, MSGBOX.Critical, self.tr('BDM error!'), args[0],
                                    self.tr("Factory reset on next start"), dnaaStartChk=False)
            if result[1] == True:
               DlgFactoryReset(self, self).exec_()

         else:
            QMessageBox.critical(self, self.tr('BlockDataManager Warning'), \
                              args[0], \
                              QMessageBox.Ok)
         #this is a critical error reporting channel, should kill the app right
         #after
         os._exit(0)

      elif action == SCAN_ACTION:
         wltIDList = args[0]
         prog = args[1]

         hasWallet = False
         hasLockbox = False

         for wltID in wltIDList:
            self.walletSideScanProgress[wltID] = prog*100
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

               self.walletModel.reset()

         if hasWallet:
            self.changeWltFilter()

         if hasLockbox:
            if self.lbDialogModel != None:
               self.lbDialogModel.reset()

            if self.lbDialog != None:
               self.lbDialog.resetLBSelection()
               self.lbDialog.changeLBFilter()
               
      elif action == NODESTATUS_UPDATE:    
         
         prevStatus = None
         if self.nodeStatus != None:
            prevStatus = self.nodeStatus.status_
         
         self.nodeStatus = args[0]
         TheSDM.updateState(self.nodeStatus)
         
         if prevStatus != self.nodeStatus.status_:
            TheBDM.setWitness(self.nodeStatus.SegWitEnabled_)
            
            if self.nodeStatus.status_ == Cpp.NodeStatus_Offline:
               self.showTrayMsg(self.tr('Disconnected'), self.tr('Connection to Bitcoin Core '
                                'client lost!  Armory cannot send nor '
                                'receive bitcoins until connection is '
                                're-established.'), QSystemTrayIcon.Critical,
                                10000)
            elif self.nodeStatus.status_ == Cpp.NodeStatus_Online:
               self.showTrayMsg(self.tr('Connected'), self.tr('Connection to Bitcoin Core '
                                      're-established'), \
                                      QSystemTrayIcon.Information, 10000)
            self.updateStatusBarText()
         
         self.updateSyncProgress()   

         
      elif action == BDM_SCAN_PROGRESS:
         self.setDashboardDetails()
         self.updateSyncProgress()
         
      elif action == BDV_ERROR:
         errorStruct = args[0]
         
         if errorStruct.errType_ == Cpp.Error_ZC:
            errorMsg = errorStruct.errorStr_
            txHash = errorStruct.extraMsg_

            self.zcBroadcastError(txHash, errorMsg)

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

      if TheBDM.exception != "":
         QMessageBox.warning(self, self.tr('Database Error'), self.tr(
                           'The DB has returned the following error: <br><br> '
                           '<b> %1 </b> <br><br> Armory will now shutdown.').arg(TheBDM.exception), QMessageBox.Ok)
         self.closeForReal()

      # SatoshiDaemonManager
      # BlockDataManager

      sdmState = TheSDM.getSDMState()
      bdmState = TheBDM.getState()

      self.heartbeatCount += 1

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

         if self.doAutoBitcoind:

            if (sdmState in ['BitcoindInitializing','BitcoindSynchronizing']) or \
               (sdmState == 'BitcoindReady' and bdmState==BDM_SCANNING):
               self.updateSyncProgress()

         else:
            if bdmState in (BDM_OFFLINE,BDM_UNINITIALIZED):
               # This call seems out of place, but it's because if you are in offline
               # mode, it needs to check periodically for the existence of Bitcoin Core
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
      dispLines = QStringList()
      title = ''
      totalStr = coin2strNZS(txAmt)


      if moneyID in self.walletMap:
         wlt = self.walletMap[moneyID]
         if len(wlt.labelName) <= 20:
            dispName = '"%(name)s"' % { 'name' : wlt.labelName }
         else:
            dispName = '"%(shortname)s..."' % { 'shortname' : wlt.labelName[:17] }
         dispName = self.tr('Wallet %1 (%2)').arg(dispName, wlt.uniqueIDB58)
      elif moneyID in self.cppLockboxWltMap:
         lbox = self.getLockboxByID(moneyID)
         if len(lbox.shortName) <= 20:
            dispName = '%(M)d-of-%(N)d "%(shortname)s"' % { 'M' : lbox.M, 'N' : lbox.N, 'shortname' : lbox.shortName}
         else:
            dispName = ('%(M)d-of-%(N)d "%(shortname)s..."') % {'M' : lbox.M, 'N' : lbox.N, 'shortname' : lbox.shortName[:17] }
         dispName = self.tr('Lockbox %1 (%2)').arg(dispName, lbox.uniqueIDB58)
      else:
         LOGERROR('Asked to show notification for wlt/lbox we do not have')
         return

      # Collected everything we need to display, now construct it and do it.
      if ledgerAmt > 0:
         # Received!
         title = self.tr('Bitcoins Received!')
         dispLines.append(self.tr('Amount:  %1 BTC').arg(totalStr ))
         dispLines.append(self.tr('Recipient:  %1').arg(dispName))
      elif ledgerAmt < 0:
         # Sent!
         title = self.tr('Bitcoins Sent!')
         dispLines.append(self.tr('Amount:  %1 BTC').arg(totalStr))
         dispLines.append(self.tr('Sender:  %1').arg(dispName))

      self.showTrayMsg(title, dispLines.join('\n'), \
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
            wname = self.walletMap[moneyID].labelName
            if len(wname)>20:
               wname = wname[:17] + '...'
            wltName = self.tr('Wallet "%1" (%2)').arg(wname, moneyID)
         else:
            lbox   = self.getLockboxByID(moneyID)
            M      = self.getLockboxByID(moneyID).M
            N      = self.getLockboxByID(moneyID).N
            lname  = self.getLockboxByID(moneyID).shortName
            if len(lname) > 20:
               lname = lname[:17] + '...'
            wltName = self.tr('Lockbox %1-of-%2 "%3" (%4)').arg(M).arg(N).arg(lname, moneyID)

         if le.isSentToSelf():
            # Used to display the sent-to-self amount, but if this is a lockbox
            # we only have a cppWallet, and the determineSentToSelfAmt() func
            # only operates on python wallets.  Oh well, the user can double-
            # click on the tx in their ledger if they want to see what's in it.
            # amt = determineSentToSelfAmt(le, cppWlt)[0]
            # self.showTrayMsg('Your bitcoins just did a lap!', \
            #             'Wallet "%s" (%s) just sent %s BTC to itself!' % \
            #         (wlt.labelName, moneyID, coin2str(amt,maxZeros=1).strip()),
            self.showTrayMsg(self.tr('Your bitcoins just did a lap!'), \
                             self.tr('%1 just sent some BTC to itself!').arg(wltName), \
                             QSystemTrayIcon.Information, 10000)
            return

         # If coins were either received or sent from the loaded wlt/lbox
         dispLines = QStringList()
         totalStr = coin2strNZS(abs(le.getValue()))
         title = None
         if le.getValue() > 0:
            title = self.tr('Bitcoins Received!')
            dispLines.append(self.tr('Amount:  %1 BTC').arg(totalStr))
            dispLines.append(self.tr('From:    %2').arg(wltName))
         elif le.getValue() < 0:
            try:
               recipStr = ''
               for addr in le.getScrAddrList():
                  if pywlt.hasScrAddr(addr):
                     continue
                  if len(recipStr)==0:
                     recipStr = scrAddr_to_addrStr(addr)
                  else:
                     recipStr = self.tr('<Multiple Recipients>')

               title = self.tr('Bitcoins Sent!')
               dispLines.append(unicode(self.tr('Amount:  %1 BTC').arg(totalStr)))
               dispLines.append(unicode(self.tr('From:    %1').arg(wltName )))
               dispLines.append(unicode(self.tr('To:      %1').arg(recipStr)))
            except Exception as e:
               LOGERROR('tx broadcast systray display failed with error: %s' % e)

         if title:
            self.showTrayMsg(title, dispLines.join("\n"), \
                       QSystemTrayIcon.Information, 10000)
            LOGINFO(title + '\n' + dispLines.join("\n")) 

         # Wait for 5 seconds before processing the next queue object.
         self.notifyBlockedUntil = RightNow() + 5
         return


   #############################################################################
   def closeEvent(self, event=None):
      moc = self.getSettingOrSetDefault('MinimizeOrClose', 'DontKnow')
      doClose, doMinimize = False, False
      if moc=='DontKnow':
         reply,remember = MsgBoxWithDNAA(self, self, MSGBOX.Question, self.tr('Minimize or Close'), \
            self.tr('Would you like to minimize Armory to the system tray instead '
            'of closing it?'), dnaaMsg=self.tr('Remember my answer'), \
            yesStr=self.tr('Minimize'), noStr=self.tr('Close'))
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
         try:
            self.writeSetting('MainGeometry',   str(self.saveGeometry().toHex()))
            self.writeSetting('MainWalletCols', saveTableView(self.walletsView))
            self.writeSetting('MainLedgerCols', saveTableView(self.ledgerView))
         except:
            pass

         if TheBDM.getState()==BDM_SCANNING:
            LOGINFO('BDM state is scanning -- force shutdown BDM')
         else:
            LOGINFO('BDM is safe for clean shutdown')

         TheSDM.stopBitcoind()
         TheBDM.shutdown()

         # Remove Temp Modules Directory if it exists:
         if self.tempModulesDirName:
            shutil.rmtree(self.tempModulesDirName)

      except:
         # Don't want a strange error here interrupt shutdown
         LOGEXCEPT('Strange error during shutdown')

      LOGINFO('Attempting to close the main window!')
      self.signalExecution.executeMethod(QAPP.quit)

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
         self.emit(SIGNAL('UWCS'), [1, self.tr('All wallets are consistent'), 10000, dlgrdy])
         self.emit(SIGNAL('checkForNegImports'))
      else:
         while not dlgrdy:
            self.emit(SIGNAL('UWCS'), [1, self.tr('Consistency Check Failed!'), 0, dlgrdy])
            time.sleep(1)

         self.checkRdyForFix()


   def checkRdyForFix(self):
      #check BDM first
      time.sleep(1)
      self.dlgCptWlt.emit(SIGNAL('Show'))
      while 1:
         if TheBDM.getState() == BDM_SCANNING:
            canFix = self.tr(
               'The wallet analysis tool will become available '
               'as soon as Armory is done loading. You can close this '
               'window and it will reappear when ready.')
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
               canFix.append(self.tr(
                  '<b>The following dialogs need closed before you can '
                  'run the wallet analysis tool:</b>'))
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
         self.pbarWalletProgress.setFormat(self.tr('Wallet Consistency Check: %p%'))
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
         # Code supporting Growl (OSX 10.7) is buggy, and no one seems to care.
         # Just jump straight to 10.8.
         self.macNotifHdlr.showNotification(dispTitle, dispText)

   #############################################################################
   def bdv(self):
      return TheBDM.bdv()

   #############################################################################
   def setupBDV(self):
      if self.netMode == NETWORKMODE.Offline:
         return

      try:
         TheBDM.registerBDV()
         self.walletManager.setBDVObject(TheBDM.bdv())
      except:
         self.switchNetworkMode(NETWORKMODE.Offline)
         return

      for wltId in self.walletMap:
         self.walletMap[wltId].registerWallet()

      for lbObj in self.allLockboxes:
         lbID = lbObj.uniqueIDB58
         
         scrAddrList = lbObj.getScrAddrList()
         self.cppLockboxWltMap[lbID] = lbObj.registerLockbox(scrAddrList, False)

   #############################################################################
   def startBlockchainProcessingInitialization(self):
      self.startBitcoindIfNecessary()
      self.completeBlockchainProcessingInitialization()

   #############################################################################
   def completeBlockchainProcessingInitialization(self):
      if CLI_OPTIONS.offline:
         return
      
      gotDB = self.startArmoryDBIfNecessary()
      if gotDB == False:
         TheBDM.setState(BDM_OFFLINE)
         self.switchNetworkMode(NETWORKMODE.Offline)

         QMessageBox.warning(self, self.tr('Database Error'), self.tr(
                           'Armory failed to spawn the DB!<br> '
                           'Continuing operations in offline mode instead. <br> '
                           'Refer to the dbLog.txt for more information.'), QMessageBox.Ok)
         
         self.setDashboardDetails()
         return
      else:
         self.switchNetworkMode(NETWORKMODE.Full)

      TheBDM.instantiateBDV(armoryengine.ArmoryUtils.ARMORYDB_PORT)
      self.setupBDV()
      self.setupLedgerViews()

      self.loadBlockchainIfNecessary()
      self.setDashboardDetails()

   #############################################################################
   def setupLedgerViews(self):
      if self.netMode == NETWORKMODE.Offline:
         return

      # Table to display ledger/activity
      w,h = tightSizeNChar(self.walletsView, 55)
      viewWidth  = 1.2*w
      sectionSz  = 1.3*h
      viewHeight = 4.4*sectionSz

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
      self.ledgerView.hideColumn(LEDGERCOLS.optInRBF)


      # Another table and model, for lockboxes
      self.currentLBPage = 0
      self.lockboxLedgTable = []
      self.lockboxLedgModel = LedgerDispModelSimple(self.lockboxLedgTable,
                                                    self, self, isLboxModel=True)
      self.lockboxLedgModel.setLedgerDelegate(TheBDM.bdv().getLedgerDelegateForLockboxes())
      self.lockboxLedgModel.setConvertLedgerMethod(self.convertLedgerToTable)
      self.lbDialogModel = None

      dateWidth    = tightSizeStr(self.ledgerView, '_9999-Dec-99 99:99pm__')[0]
      cWidth = 20 # num-confirm icon width
      tWidth = 72 # date icon width
      initialColResize(self.ledgerView, [cWidth, 0, dateWidth, tWidth, 0.30, 0.40, 0.3])

      self.connect(self.ledgerView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.dblClickLedger)

      self.ledgerView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.ledgerView.customContextMenuRequested.connect(self.showContextMenuLedger)

      self.connect(self.ledgerView.horizontalHeader(), \
                   SIGNAL('sortIndicatorChanged(int,Qt::SortOrder)'), \
                   self.changeLedgerSorting)

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

      frmFilter = makeVertFrame([QLabel(self.tr('Filter:')), self.comboWltSelect, 'Stretch'])

      frmLower = makeHorizFrame([ frmFilter, \
                                 'Stretch', \
                                 self.frmLedgUpDown, \
                                 'Stretch', \
                                 self.frmTotals])

      # Now add the ledger to the bottom of the window
      ledgLayout = QGridLayout()
      ledgLayout.addWidget(self.ledgerView,           1,0)
      ledgLayout.addWidget(frmLower,                  2,0)
      ledgLayout.setRowStretch(0, 0)
      ledgLayout.setRowStretch(1, 1)
      ledgLayout.setRowStretch(2, 0)

      self.tabActivity = QWidget()
      self.tabActivity.setLayout(ledgLayout)
      self.mainDisplayTabs.addTab(self.tabActivity,  self.tr('Transactions'))

      hexledgsz = self.settings.get('MainLedgerCols')
      if len(hexledgsz)>0:
         restoreTableView(self.ledgerView, hexledgsz)
         self.ledgerView.setColumnWidth(LEDGERCOLS.NumConf, 20)
         self.ledgerView.setColumnWidth(LEDGERCOLS.TxDir,   72)
         
   #############################################################################
   def bumpFee(self, walletId, txHash):
      #grab wallet
      wlt = self.walletMap[walletId]
      
      #grab ZC from DB
      zctx = TheBDM.bdv().getTxByHash(txHash)
      pytx = PyTx().unserialize(zctx.serialize())
      
      #create tx batch
      batch = Cpp.TransactionBatch()
      for txin in pytx.inputs:
         outpoint = txin.outpoint
         batch.addSpender(binary_to_hex(outpoint.txHash), \
            outpoint.txOutIndex, txin.intSeq)
         
      for txout in pytx.outputs:
         script = txout.getScript()
         scrAddr = BtcUtils().getScrAddrForScript(script)
         addrComment = wlt.getCommentForAddress(scrAddr)
         
         b58Addr = scrAddr_to_addrStr(scrAddr)
         
         if addrComment == CHANGE_ADDR_DESCR_STRING:
            #change address
            batch.setChange(b58Addr)
            
         else:
            #recipient
            batch.addRecipient(b58Addr, txout.value)
      
      batch.setWalletID(walletId)      
      
      #feed batch to spend dlg
      batchStr = batch.serialize()
      dlgSpend = DlgSendBitcoins(None, self, self)
      dlgSpend.frame.prefillFromBatch(batchStr)
      dlgSpend.exec_()
      
   #############################################################################
   def walletTimeoutCheck(self):
      for idx,wltID in enumerate(self.walletIDList):
         self.walletMap[wltID].checkWalletLockTimeout()
      self.signalExecution.callLater(2, self.walletTimeoutCheck)

############################################
def checkForAlreadyOpen():
   from armoryengine.ProcessMutex import PySide_ProcessMutex
   LOGDEBUG('Checking for already open socket...')

   prc_mutex = PySide_ProcessMutex(CLI_OPTIONS.interport, None)   

   urilink = ""
   if CLI_ARGS:
      urilink = str(CLI_ARGS[0])
   
   if prc_mutex.test(urilink) == True:
      LOGERROR('Socket already in use.  Sent CLI args to existing proc.')      
      LOGERROR('Exiting...')      
      os._exit(0)

############################################

if 1:

   if CLI_OPTIONS.interport > 1:
      checkForAlreadyOpen()

   pixLogo = QPixmap(':/splashlogo.png')
   if USE_TESTNET or USE_REGTEST:
      pixLogo = QPixmap(':/splashlogo_testnet.png')
   SPLASH = ArmorySplashScreen(pixLogo)
   SPLASH.setMask(pixLogo.mask())

   SPLASH.show()
   QAPP.processEvents()

   # Will make this customizable
   QAPP.setFont(GETFONT('var'))

   TheSDM = SatoshiDaemonManager()
   form = ArmoryMainWindow(splashScreen=SPLASH)
   form.show()

   SPLASH.finish(form)
   QAPP.setQuitOnLastWindowClosed(True)
   os._exit(QAPP.exec_())
