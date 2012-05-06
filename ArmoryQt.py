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
            self.lblLogoIcon.setPixmap(QPixmap(':/armory_logo_white_text_green_h72.png'))
      else:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [MAIN NETWORK]')
         self.iconfile = ':/armory_icon_32x32.png'
         self.lblLogoIcon.setPixmap(QPixmap(':/armory_logo_h56.png'))
         if Colors.isDarkBkgd:
            self.lblLogoIcon.setPixmap(QPixmap(':/armory_logo_white_text_h72.png'))
      self.setWindowIcon(QIcon(self.iconfile))
      self.lblLogoIcon.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)


      
      self.haveBlkFile = os.path.exists(BLK0001_PATH)
      self.abortLoad = False
      self.isDirty   = True
      
      self.settingsPath = CLI_OPTIONS.settingsPath
      self.loadWalletsAndSettings()
      self.setupNetworking()

      # setupNetworking may have set this flag if something went wrong
      if self.abortLoad:
         os._exit(0)

      # Setup system tray and register "bitcoin:" URLs with the OS
      self.setupSystemTray()
      self.setupUriRegistration()


      self.extraHeartbeatFunctions = [self.doTheSystemTrayThing]

      self.lblArmoryStatus = QRichLabel('<font color=%s><i>Offline</i></font>' % \
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
      self.ledgerProxy.sort(LEDGERCOLS.NumConf, Qt.AscendingOrder)

      self.ledgerView  = QTableView()
      self.ledgerView.setModel(self.ledgerProxy)
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
      self.ledgerView.hideColumn(LEDGERCOLS.toSelf)
      self.ledgerView.hideColumn(LEDGERCOLS.DoubleSpend)

      dateWidth    = tightSizeStr(self.ledgerView, '_9999-Dec-99 99:99pm__')[0]
      nameWidth    = tightSizeStr(self.ledgerView, '9'*32)[0]
      #if self.usermode==USERMODE.Standard:
      cWidth = 20 # num-confirm icon width
      tWidth = 72 # date icon width
      initialColResize(self.ledgerView, [cWidth, 0, dateWidth, tWidth, 0.30, 0.40, 0.3])
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
      self.populateLedgerComboBox()

      ccl = lambda x: self.createCombinedLedger() # ignore the arg
      self.connect(self.comboWalletSelect, SIGNAL('currentIndexChanged(QString)'), ccl)

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
      ledgLayout.addWidget(QLabel("<b>Ledger</b>:"),  0,0)
      ledgLayout.addWidget(self.ledgerView,           1,0)
      ledgLayout.addWidget(frmLower,                  2,0)
      ledgLayout.setRowStretch(0, 0)
      ledgLayout.setRowStretch(1, 1)
      ledgLayout.setRowStretch(2, 0)

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

      verStr = 'Armory %s-alpha / %s User' % (getVersionString(BTCARMORY_VERSION), \
                                              UserModeStr(self.usermode))
      lblInfo = QRichLabel(verStr, doWrap=False)
      lblInfo.setFont(GETFONT('var',10))
      lblInfo.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      logoBtnFrame = []
      logoBtnFrame.append(self.lblLogoIcon)
      print self.lblLogoIcon.width(), self.lblLogoIcon.height()
      logoBtnFrame.append(btnSendBtc)
      logoBtnFrame.append(btnRecvBtc)
      logoBtnFrame.append(btnWltProps)
      if self.usermode in (USERMODE.Advanced, USERMODE.Developer):
         logoBtnFrame.append(btnOfflineTx)
      logoBtnFrame.append(lblInfo)
      #logoBtnFrame.append(btnDevTools)
      logoBtnFrame.append('Stretch')

      btnFrame = makeVertFrame(logoBtnFrame, STYLE_SUNKEN)
      logoWidth=275
      btnFrame.sizeHint = lambda: QSize(logoWidth*1.0, 10)
      btnFrame.setMaximumWidth(logoWidth*1.1)
      btnFrame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
      
      layout = QGridLayout()
      layout.addWidget(btnFrame,          0, 0, 1, 1)
      layout.addWidget(wltFrame,          0, 1, 1, 1)
      layout.addWidget(ledgFrame,         1, 0, 1, 2)
      layout.setRowStretch(0, 1)
      layout.setRowStretch(1, 5)

      # Attach the layout to the frame that will become the central widget
      mainFrame = QFrame()
      mainFrame.setLayout(layout)
      self.setCentralWidget(mainFrame)
      #if self.usermode==USERMODE.Standard:
      self.setMinimumSize(800,500)
      #else:
         #self.setMinimumSize(1200,300)

      #self.statusBar().showMessage('Blockchain loading, please wait...')

      if self.haveBlkFile and not CLI_OPTIONS.offline:
         tstart = RightNow()
         self.loadBlockchain()
         print 'Loading blockchain took %0.1f seconds' % (RightNow()-tstart)
      from twisted.internet import reactor

      ##########################################################################
      # Set up menu and actions
      #MENUS = enum('File', 'Wallet', 'User', "Tools", "Network")
      MENUS = enum('File', 'User', 'Tools', 'Wallets')
      self.menu = self.menuBar()
      self.menusList = []
      self.menusList.append( self.menu.addMenu('&File') )
      self.menusList.append( self.menu.addMenu('&User') )
      self.menusList.append( self.menu.addMenu('&Tools') )
      self.menusList.append( self.menu.addMenu('&Wallets') )
      #self.menusList.append( self.menu.addMenu('&Network') )


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



      currmode = self.settings.getSettingOrSetDefault('User_Mode', 'Advanced')
      print 'Usermode:', currmode
      self.firstModeSwitch=True
      if currmode=='Standard':
         self.usermode = USERMODE.Standard               
         actSetModeStd.setChecked(True)
      elif currmode=='Advanced':
         self.usermode = USERMODE.Advanced               
         actSetModeAdv.setChecked(True)
      elif currmode=='Developer':
         self.usermode = USERMODE.Developer               
         actSetModeDev.setChecked(True)

      actOpenSigner = self.createAction('&Message Signing', lambda: DlgECDSACalc(self,self, 0).exec_())
      actOpenTools  = self.createAction('&EC Calculator',   lambda: DlgECDSACalc(self,self, 1).exec_())
      self.menusList[MENUS.Tools].addAction(actOpenSigner)
      self.menusList[MENUS.Tools].addAction(actOpenTools)


      actCreateNew      = self.createAction('&Create &New Wallet',        self.createNewWallet)
      actImportWlt      = self.createAction('&Import Armory Wallet',      self.execGetImportWltName)
      actRestorePaper   = self.createAction('&Restore from Paper Backup', self.execRestorePaperBackup)
      actMigrateSatoshi = self.createAction('&Migrate Bitcoin Wallet',    self.execMigrateSatoshi)
      actAddressBook    = self.createAction('View &Address Book',         self.execAddressBook)


      self.menusList[MENUS.Wallets].addAction(actCreateNew)
      self.menusList[MENUS.Wallets].addAction(actImportWlt)
      self.menusList[MENUS.Wallets].addAction(actRestorePaper)
      self.menusList[MENUS.Wallets].addAction(actMigrateSatoshi)
      self.menusList[MENUS.Wallets].addAction(actAddressBook)



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



      reactor.callLater(0.1,  self.execIntroDialog)
      reactor.callLater(5, self.Heartbeat)

      if CLI_ARGS:
         reactor.callLater(1, self.uriLinkClicked, CLI_ARGS[0])



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
      actClose      = self.createAction('Close Armory', self.closeEvent)
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
      isFirstLoad = self.settings.getSettingOrSetDefault('First_Load', True)

      if OS_LINUX:
         out,err = execAndWait('gconftool-2 --get /desktop/gnome/url-handlers/bitcoin/command')
      
         def setAsDefault():
            print 'Setting up Armory as default URI handler...'
            execAndWait('gconftool-2 -t string -s /desktop/gnome/url-handlers/bitcoin/command "python /usr/share/armory/ArmoryQt.py \"%s\""')
            execAndWait('gconftool-2 -s /desktop/gnome/url-handlers/bitcoin/needs_terminal false -t bool')
            execAndWait('gconftool-2 -t bool -s /desktop/gnome/url-handlers/bitcoin/enabled true')


         if 'no value' in out.lower() or 'no value' in err.lower():
            # Silently add Armory if it's never been set before
            setAsDefault()
         elif not 'armory' in out.lower() and not isFirstLoad:
            # If another application has it, ask for permission to change it
            if not self.settings.getSettingOrSetDefault('DNAA_DefaultApp', False):
               reply = MsgBoxWithDNAA(MSGBOX.Question, 'Default URL Handler', \
                  'Armory is not set as your default application for handling '
                  '"bitcoin:" links.  Would you like to use Armory as the '
                  'default?', 'Do not ask this question again')
               if reply[0]==True:
                  setAsDefault()
               if reply[1]==True:
                  self.settings.set('DNAA_DefaultApp', True)

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

         dontAsk = self.settings.getSettingOrSetDefault('DNAA_DefaultApp', False)
         if action=='AskUser' and not isFirstLoad and not dontAsk:
            # If another application has it, ask for permission to change it
            reply = MsgBoxWithDNAA(MSGBOX.Question, 'Default URL Handler', \
               'Armory is not set as your default application for handling '
               '"bitcoin:" links.  Would you like to use Armory as the '
               'default?', 'Do not ask this question again')

            if reply[1]==True:
               self.settings.set('DNAA_DefaultApp', True)

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
               print '\tWriting key: [HKEY_CURRENT_USER\\]' + dkey
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
      if not self.settings.getSettingOrSetDefault('DNAA_IntroDialog', False):
         dlg = DlgIntroMessage(self, self)
         result = dlg.exec_()

         if dlg.chkDnaaIntroDlg.isChecked():
            self.settings.set('DNAA_IntroDialog', True)

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
      self.usermode = mode
      if mode==USERMODE.Standard:
         self.settings.set('User_Mode', 'Standard')
      if mode==USERMODE.Advanced:
         self.settings.set('User_Mode', 'Advanced')
      if mode==USERMODE.Developer:
         self.settings.set('User_Mode', 'Developer')

      if not self.firstModeSwitch:
         QMessageBox.information(self,'Restart Required', \
         'You must restart Armory in order for the user-mode switching '
         'to take effect.', QMessageBox.Ok)

      self.firstModeSwitch = False
      


   #############################################################################
   def setupNetworking(self):

      self.internetAvail = False
      self.satoshiAvail  = False


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
            print 'Socket already occupied!  This must be a duplicate Armory instance!'
            QMessageBox.warning(self, 'Only One, Please!', \
               'Armory is already running!  You can only have one instance open '
               'at a time.  Aborting...', QMessageBox.Ok)
            os._exit(0)
      else:
         print '*** Listening port is disabled.  URI-handling will not work'
      

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
         response=urllib2.urlopen('http://google.com', timeout=CLI_OPTIONS.nettimeout)
         self.internetAvail = True
      except ImportError:
         print 'No module urllib2 -- cannot determine if internet is available'
      except urllib2.URLError:
         # In the extremely rare case that google might be down...
         try:
            response=urllib2.urlopen('http://microsoft.com', timeout=CLI_OPTIONS.nettimeout)
         except urllib2.URLError:
            self.internetAvail = False

      print 'Internet connection is Available: ', self.internetAvail
      print 'Satoshi Client is Available:      ', self.satoshiAvail
         
      self.isOnline = (self.internetAvail and self.satoshiAvail and not CLI_OPTIONS.offline)

      if not self.isOnline:
         if not CLI_OPTIONS.offline:
            dlg = DlgBadConnection(self.internetAvail, self.satoshiAvail, self, self)
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

      def newTxFunc(pytxObj):
         TheBDM.addNewZeroConfTx(pytxObj.serialize(), long(RightNow()), True)
         for wltID,wlt in self.walletMap.iteritems():
            # Absorb the new tx into the BDM & wallets
            TheBDM.rescanWalletZeroConf(self.walletMap[wltID].cppWallet)
      
            # Above doesn't return anything, but we want to know what it is...
            le = wlt.cppWallet.calcLedgerEntryForTxStr(pytxObj.serialize())

            # If it is ours, let's add it to the notifier queue
            if not le.getTxHash()=='\x00'*32:
               self.notifyQueue.append([wltID, le, False])  # notifiedAlready=False

         self.createCombinedLedger()
         self.ledgerModel.reset()

      def showOfflineMsg():
         if CLI_OPTIONS.disable_conn_notify:
            return 

         try:
            self.lblArmoryStatus.setText( \
               '<font color=%s><i>Offline</i></font>' % htmlColor('TextWarn'))
            self.sysTray.showMessage('Disconnected', \
                  'Connection to Satoshi client lost!  Armory cannot send \n'
                  'or receive Bitcoins until Satoshi client is available.', \
                  QSystemTrayIcon.Critical, 10000)
         except:
            pass


      self.connectCount = 0
      def showOnlineMsg():
         if CLI_OPTIONS.disable_conn_notify:
            return 

         try:
            self.lblArmoryStatus.setText(\
                     '<font color=%s>Connected (%s blocks)</font> ' % 
                     (htmlColor('TextGreen'), self.latestBlockNum))
            if self.connectCount>0:
               self.sysTray.showMessage('Connected', \
                  'Connection to Satoshi re-established', \
                  QSystemTrayIcon.Information, 10000)
            self.connectCount += 1
         except:
            pass


      self.NetworkingFactory = ArmoryClientFactory( \
                                       func_loseConnect=showOfflineMsg, \
                                       func_madeConnect=showOnlineMsg, \
                                       func_newTx=newTxFunc)
      reactor.connectTCP('127.0.0.1', BITCOIN_PORT, self.NetworkingFactory)






   #############################################################################
   def uriLinkClicked(self, uriStr):
      uriDict = parseBitcoinURI(uriStr)
      if len(uriDict)==0:
         warnMsg = ('It looks like you just clicked a "bitcoin:" link, but '
                    'that link is malformed.  ')
         if self.usermode == USERMODE.Standard:
            warnMsg += ('Please check the source of the link and enter the '
                        'transaction manually.')
         else:
            warnMsg += 'The raw URI string is:<br><br>' + uriStr
         QMessageBox.warning(self, 'Invalid URI', warnMsg, QMessageBox.Ok)
         return

      if not uriDict.has_key('address'):
         QMessageBox.warning(self, 'The "bitcoin:" link you just clicked '
            'does not even contain an address!  There is nothing that '
            'Armory can do with this link!', QMessageBox.Ok)
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
            return
         
      self.bringArmoryToFront() 
      self.uriSendBitcoins(uriDict)
      

   #############################################################################
   def loadWalletsAndSettings(self):
      self.settings = SettingsFile(self.settingsPath)

      self.settings.getSettingOrSetDefault('First_Load',         True)
      self.settings.getSettingOrSetDefault('Load_Count',         0)
      self.settings.getSettingOrSetDefault('User_Mode',          'Advanced')
      self.settings.getSettingOrSetDefault('UnlockTimeout',      10)
      self.settings.getSettingOrSetDefault('DNAA_UnlockTimeout', False)


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
      self.combinedLedger = []
      self.ledgerSize = 0
      self.ledgerTable = []

      self.latestBlockNum = 0



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
               wo1 = self.walletMap[wltID].watchingOnly
               wo2 = wltLoad.watchingOnly
               if wo1 and not wo2:
                  prevWltPath = self.walletMap[wltID].walletPath
                  self.walletMap[wltID] = wltLoad
                  print 'First wallet is more useful than the second one...'
                  print ' '*10, 'Wallet 1 (loaded): ', fpath
                  print ' '*10, 'Wallet 2 (skipped):', prevWltPath
               else:
                  print 'Second wallet is more useful than the first one...'
                  print ' '*10, 'Wallet 1 (loaded): ', self.walletMap[wltID].walletPath
                  print ' '*10, 'Wallet 2 (skipped):', fpath
            else:
               # Update the maps/dictionaries
               self.walletMap[wltID] = wltLoad
               self.walletIndices[wltID] = len(self.walletMap)-1

               # Maintain some linear lists of wallet info
               self.walletIDSet.add(wltID)
               self.walletIDList.append(wltID)
         except:
            print '***WARNING: Wallet could not be loaded:', fpath
            print '            skipping... '
            raise
                     

      
      print 'Number of wallets read in:', len(self.walletMap)
      for wltID, wlt in self.walletMap.iteritems():
         print ('   Wallet (%s):' % wlt.uniqueIDB58).ljust(25),
         print '"'+wlt.labelName.ljust(32)+'"   ',
         print '(Encrypted)' if wlt.useEncryption else '(No Encryption)'
         # Register all wallets with TheBDM
         TheBDM.registerWallet( wlt.cppWallet )


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

      if not self.isOnline:
         print 'Skip blockchain loading in offline mode'
      else:
         print 'Loading blockchain'
         BDM_LoadBlockchainFile()
         self.latestBlockNum = TheBDM.getTopBlockHeader().getBlockHeight()
   
         # Now that theb blockchain is loaded, let's populate the wallet info
         if TheBDM.isInitialized():
            TheBDM.enableZeroConf(os.path.join(ARMORY_HOME_DIR,'mempool.bin'))
   
            self.statusBar().showMessage('Syncing wallets with blockchain...')
            print 'Syncing wallets with blockchain...'
            for wltID, wlt in self.walletMap.iteritems():
               print 'Syncing wallet: ', wltID
               self.walletMap[wltID].setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
               self.walletMap[wltID].syncWithBlockchain()
   
            
               
            self.createCombinedLedger()
            self.ledgerSize = len(self.combinedLedger)
            self.statusBar().showMessage('Blockchain loaded, wallets sync\'d!', 10000)
   
            if self.isOnline:
               self.lblArmoryStatus.setText(\
                  '<font color=%s>Connected (%s blocks)</font> ' % 
                  (htmlColor('TextGreen'), self.latestBlockNum))
            self.blkReceived  = self.settings.getSettingOrSetDefault('LastBlkRecvTime', 0)
            self.isDirty = False
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
               

      if wltIDList==None:
         return

      self.combinedLedger = []
      totalFunds  = 0
      spendFunds  = 0
      unconfFunds = 0
      currBlk = 0xffffffff
      if TheBDM.isInitialized():
         currBlk = TheBDM.getTopBlockHeader().getBlockHeight()

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
         if not self.isOnline:
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
         self.ledgerModel = LedgerDispModelSimple(self.ledgerTable, self, self)
         #self.ledgerProxy = LedgerDispSortProxy()
         #self.ledgerProxy.setDynamicSortFilter(True)
         self.ledgerProxy.setSourceModel(self.ledgerModel)
         self.ledgerView.setModel(self.ledgerProxy)
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

         # UnixTime (needed for sorting)
         row.append(le.getTxTime())

         # Date
         row.append(unixTimeToFormatStr(le.getTxTime()))

         # TxDir (actually just the amt... use the sign of the amt to determine dir)
         row.append(coin2str(le.getValue(), maxZeros=2))

         # Wlt Name
         row.append(self.walletMap[wltID].labelName)
         
         # Comment
         if wlt.commentsMap.has_key(le.getTxHash()):
            row.append(wlt.commentsMap[le.getTxHash()])
         else:
            comment = self.getAddrCommentIfAvail(le.getTxHash())
            row.append(comment)

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
   def getAddrCommentIfAvail(self, txHash):
      if not TheBDM.isInitialized():
         return ''
      else:
         tx = TheBDM.getTxByHash(txHash)
         if not tx:
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
      if not walletIsNew and TheBDM.isInitialized():
         # We may need to search the blockchain for existing tx
         wlt.setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
         wlt.syncWithBlockchain()

         for addr in wlt.getLinearAddrList():
            ledger = wlt.getAddrTxLedger(addr.getAddr160())

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


      TheBDM.registerWallet(newWallet.cppWallet, True) # is new, no blk rescan
      self.addWalletToApplication(newWallet)

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
         not self.settings.getSettingOrSetDefault('OverrideMinFee', False):
         print 'Subtracting fee from Sweep-output'
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
   def broadcastTransaction(self, pytx, dryRun=False):
      print 'Pretty tx: ', pytx.pprint()
      print 'Raw serialize tx: ', binary_to_hex(pytx.serialize())
      if dryRun:
         #DlgDispTxInfo(pytx, None, self, self).exec_()
         return
      else:
         newTxHash = pytx.getHash()
         print 'Sending Tx,', binary_to_hex(newTxHash)
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
            if not TheBDM.getTxByHash(newTxHash):
               failedFN = os.path.join(ARMORY_HOME_DIR, 'failedtx.bin')
               f = open(failedFN, 'ab')
               bp = BinaryPacker()
               bp.put(UINT64, long(RightNow()))
               f.write(bp.getBinaryString())
               f.write(pytx.serialize())
               f.close()
               QMessageBox.warning(self, 'Invalid Transaction', \
               'The transaction that you just executed, does not '
               'appear to have been accepted by the Bitcoin network. '
               'This sometimes happens with legitimate transactions '
               'when a fee is not included but was required.  Sometimes '
               'it will happen when you have zero-confirmation transactions '
               'waiting to get into the blockchain.  Or it can be due to a '
               'bug in the Armory software.  '
               '<br><br>If you have any zero-confirmation transactions in '
               'your ledger, please wait until they receive at least one '
               'confirmation then try your transaction again.  Otherwise, '
               'follow the directions below to report this as a potential '
               'bug in the software. '
               '<br><br>The exact binary transaction data '
               'has been saved to ' + failedFN + '.  This file never '
               'contains any sensitive data, so it is safe to send to '
               'the Armory developers for help diagnosing the issue, and '
               'fixing any potential bugs.  If you are unsure why this '
               'transaction failed, please email the above file to '
               'alan.reiner@gmail.com along with any information you can '
               'provide about the context of this failed transaction.', QMessageBox.Ok)
                  
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
                                             skipBlockChainScan=True)
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

      print 'Copying imported wallet to:', newpath
      shutil.copy(fn, newpath)
      self.addWalletToApplication(PyBtcWallet().readWalletFile(newpath), \
                                                         walletIsNew=False)

   #############################################################################
   def execRestorePaperBackup(self):
      dlgPaper = DlgImportPaperWallet(self, self)
      if dlgPaper.exec_():
         print 'Raw import successful.  Searching blockchain for tx data...'
         
         wlt = dlgPaper.newWallet
         TheBDM.registerWallet(wlt.cppWallet)
   
         DlgExecLongProcess(dlgPaper.newWallet.freshImportFindHighestIndex, \
               'Restoring wallet.  This may take many minutes. Delete and '
               're-import wallet if this operation is interrupted.', \
               self, self).exec_()
         #highestIdx = dlgPaper.newWallet.freshImportFindHighestIndex()
         self.addWalletToApplication(wlt, walletIsNew=False)
         print 'Import Complete!'
   
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
           'Has your wallet ever been opened in the 0.6.0+ Satoshi client?', \
           yesStr='Yes, Abort!', noStr='No, Carry On!')
            
      if reply:
         return

      DlgMigrateSatoshiWallet(self, self).exec_()



   #############################################################################
   def execAddressBook(self):
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
            if cppTx:
               pytx = PyTx().unserialize(cppTx.serialize())

         if pytx==None:
            QMessageBox.critical(self, 'Invalid Tx:',
            'The transaction ID requested to be displayed does not exist in '
            'the blockchain or the zero-conf tx list...?', QMessageBox.Ok)
            return

         DlgDispTxInfo( pytx, self.walletMap[wltID], self, self, txtime=txtime).exec_()


   #############################################################################
   def clickSendBitcoins(self):
      if not self.isOnline:
         QMessageBox.warning(self, 'Offline Mode', \
           'Armory is currently running in offline mode, and has no '
           'ability to determine balances or create transactions. '
           '<br><br>'
           'In order to send coins from this wallet you must use a '
           'full copy of this wallet from an online computer, '
           'or initiate an "offline transaction" using a watching-only '
           'wallet on an online computer.', QMessageBox.Ok)
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
         dlg = DlgWalletSelect(self, self, 'Send from Wallet...', wltID, onlyMyWallets=False)
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
         dlg = DlgWalletSelect(self, self, 'Receive coins with wallet...', '', wltID, onlyMyWallets=False)
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
      self.setWindowState(Qt.WindowActive)
      self.activateWindow()
      self.raise_()

   #############################################################################
   def minimizeArmory(self):
      self.setWindowState(Qt.WindowMinimized)
      


   #############################################################################
   def blinkTaskbar(self):
      self.activateWindow()
      

   #############################################################################
   def Heartbeat(self, nextBeatSec=2):
      """
      This method is invoked when the app is initialized, and will
      run every 2 seconds, or whatever is specified in the nextBeatSec
      argument.
      """
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
               TheBDM.rescanWalletZeroConf(self.walletMap[wltID].cppWallet)
               newLedgerSize = len(self.walletMap[wltID].getTxLedger())
               didAffectUs = (prevLedgerSize != newLedgerSize)
         
            print 'New Block! :', self.latestBlockNum
            if didAffectUs:
               print 'New Block contained a transaction relevant to us!'
               self.walletListChanged()
               self.notifyOnSurpriseTx(self.latestBlockNum-newBlks, \
                                       self.latestBlockNum+1)

            self.createCombinedLedger()
            self.blkReceived  = RightNow()
            self.settings.set('LastBlkRecvTime', self.blkReceived)
      
            if self.isOnline:
               self.lblArmoryStatus.setText(\
                  '<font color=%s>Connected (%s blocks)</font> ' % \
                  (htmlColor('TextGreen'), self.latestBlockNum))

         nowtime = RightNow()
         blkRecvAgo  = nowtime - self.blkReceived
         blkStampAgo = nowtime - self.topTimestamp
         self.lblArmoryStatus.setToolTip('Last block timestamp is %s ago' % \
                                                   secondsToHumanTime(blkStampAgo))


      for idx,wltID in enumerate(self.walletIDList):
         self.walletMap[wltID].checkWalletLockTimeout()

      for func in self.extraHeartbeatFunctions:
         func()

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
               print 'This tx is ours!'
               if not le.getTxHash() in notifiedAlready:
                  print '...but we\'ve been notified before, alread'
                  #self.notifyQueue.append([wltID, le, False])
               
            

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
            recips = [txref.getTxOutRef(i).getRecipientAddr() for i in range(nOut)]
            values = [txref.getTxOutRef(i).getValue()         for i in range(nOut)]
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
      '''
      Seriously, I could not figure out how to exit gracefully, so the next
      best thing is to just hard-kill the app with a sys.exit() call.  Oh well... 
      '''
      try:
         # Save the main window geometry in the settings file
         self.settings.set('MainGeometry',   str(self.saveGeometry().toHex()))
         self.settings.set('MainWalletCols', saveTableView(self.walletsView))
         self.settings.set('MainLedgerCols', saveTableView(self.ledgerView))
      except:
         # Don't want a strange error here interrupt shutdown 
         raise
         pass

      form.sysTray.hide()
      from twisted.internet import reactor
      print 'Attempting to close the main window!'
      reactor.stop()
      if event:
         event.accept()
      
      

############################################
class ArmoryInstanceListener(Protocol):
   def connectionMade(self):
      print 'Another Armory instance just tried to overthrow me! (P.S. - it was defeated)'
      self.factory.func_conn_made()
      
   def dataReceived(self, data):
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
if __name__ == '__main__':

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
      TheBDM.Reset()
      if reactor.threadpool is not None:
         reactor.threadpool.stop()
      QAPP.quit()
      os._exit(0)
      
   QAPP.connect(form, SIGNAL("lastWindowClosed()"), endProgram)
   reactor.addSystemEventTrigger('before', 'shutdown', endProgram)
   QAPP.setQuitOnLastWindowClosed(True)
   reactor.runReturn()
   os._exit(QAPP.exec_())


