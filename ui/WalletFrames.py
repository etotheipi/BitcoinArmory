################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

from PyQt4.Qt import * #@UnusedWildImport
from PyQt4.QtGui import * #@UnusedWildImport

from armoryengine.BDM import TheBDM
from qtdefines import * #@UnusedWildImport

WALLET_DATA_ENTRY_FIELD_WIDTH = 60


class LockboxSelectFrame(ArmoryFrame):
   def __init__(self, parent, main, layoutDir=VERTICAL, spendFromLBID=None):
      super(LockboxSelectFrame, self).__init__(parent, main)

      self.lbox = self.main.getLockboxByID(spendFromLBID)
      self.cppWlt = self.main.cppLockboxWltMap[spendFromLBID]

      if not self.lbox:
         QMessageBox.warning(self, tr("Invalid Lockbox"), tr(""" There was 
         an error loading the specified lockbox (%s).""") % spendFromLBID, 
         QMessageBox.Ok)
         self.reject()
         return

      lblSpendFromLB = QRichLabel(tr(""" <font color="%s" size=4><b><u>Lockbox   
         %s (%d-of-%d)</u></b></font>""") % (htmlColor('TextBlue'), \
         self.lbox.uniqueIDB58, self.lbox.M, self.lbox.N))
      lblSpendFromLB.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      lbls = []
      lbls.append(QRichLabel("Lockbox ID:", doWrap=False))
      lbls.append(QRichLabel("Name:", doWrap=False))
      lbls.append(QRichLabel("Description:", doWrap=False))
      lbls.append(QRichLabel("Spendable BTC:", doWrap=False))

      layoutDetails = QGridLayout()
      for i,lbl in enumerate(lbls):
         lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
         lbl.setText('<b>' + str(lbls[i].text()) + '</b>')
         layoutDetails.addWidget(lbl, i+1, 0)
         
      # LockboxID
      self.dispID = QRichLabel(spendFromLBID)

      # Lockbox Short Description/Name
      self.dispName = QRichLabel(self.lbox.shortName)
      self.dispName.setWordWrap(True)
      self.dispName.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

      # Lockbox long descr
      dispDescr = self.lbox.longDescr[:253]
      if len(self.lbox.longDescr)>253:
         dispDescr += '...'
      self.dispDescr = QRichLabel(dispDescr)
      self.dispDescr.setWordWrap(True)
      self.dispDescr.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

      bal = self.cppWlt.getSpendableBalance(self.main.currBlockNum, IGNOREZC)
      self.dispBal = QMoneyLabel(bal, wBold=True)
      self.dispBal.setTextFormat(Qt.RichText)

      layoutDetails.addWidget(self.dispID, 1, 1)
      layoutDetails.addWidget(self.dispName, 2, 1)
      layoutDetails.addWidget(self.dispDescr, 3, 1)
      layoutDetails.addWidget(self.dispBal, 4, 1)
      layoutDetails.setColumnStretch(0,0)
      layoutDetails.setColumnStretch(1,1)
      frmDetails = QFrame()
      frmDetails.setLayout(layoutDetails)
      frmDetails.setFrameStyle(STYLE_SUNKEN)

      layout = QVBoxLayout()
      layout.addWidget(lblSpendFromLB)
      layout.addWidget(frmDetails)

      self.setLayout(layout)

      
      



# This class has all of the select wallet display and control functionality for
# selecting a wallet, and doing coin control. It can be dropped into any dialog
# and will interface with the dialog with select wlt and coin control callbacks.
class SelectWalletFrame(ArmoryFrame):
   def __init__(self, parent, main, layoutDir=VERTICAL,
                                    firstSelect=None,
                                    onlyMyWallets=False,
                                    wltIDList=None, 
                                    atLeast=0, 
                                    selectWltCallback=None, 
                                    coinControlCallback=None,
                                    onlyOfflineWallets=False):

      super(SelectWalletFrame, self).__init__(parent, main)
      self.coinControlCallback = coinControlCallback

      self.walletComboBox = QComboBox()
      self.walletListBox  = QListWidget()
      self.balAtLeast = atLeast
      self.selectWltCallback = selectWltCallback
      self.doVerticalLayout = layoutDir==VERTICAL

      if self.main and len(self.main.walletMap) == 0:
         QMessageBox.critical(self, 'No Wallets!', \
            'There are no wallets to select from.  Please create or import '
            'a wallet first.', QMessageBox.Ok)
         self.accept()
         return
      
      self.wltIDList = wltIDList if wltIDList else self.getWalletIdList(onlyOfflineWallets)
      
      selectedWltIndex = 0
      self.selectedID = None
      wltItems = 0
      self.displayIDs = []
      if len(self.wltIDList) > 0:
         self.selectedID = self.wltIDList[0]
         for wltID in self.wltIDList:
            wlt = self.main.walletMap[wltID]
            wlttype = determineWalletType(wlt, self.main)[0]
            if onlyMyWallets and wlttype == WLTTYPES.WatchOnly:
               continue

            self.displayIDs.append(wltID)
            if self.doVerticalLayout:
               self.walletComboBox.addItem(wlt.labelName)
            else:
               self.walletListBox.addItem(QListWidgetItem(wlt.labelName))
         
            if wltID == firstSelect:
               selectedWltIndex = wltItems
               self.selectedID = wltID
            wltItems += 1
            
         if self.doVerticalLayout:
            self.walletComboBox.setCurrentIndex(selectedWltIndex)
         else:
            self.walletListBox.setCurrentRow(selectedWltIndex)


      self.connect(self.walletComboBox, SIGNAL('currentIndexChanged(int)'), self.updateOnWalletChange)
      self.connect(self.walletListBox,  SIGNAL('currentRowChanged(int)'),   self.updateOnWalletChange)

      # Start the layout
      layout =  QVBoxLayout() 

      lbls = []
      lbls.append(QRichLabel("Wallet ID:", doWrap=False))
      lbls.append(QRichLabel("Name:", doWrap=False))
      lbls.append(QRichLabel("Description:", doWrap=False))
      lbls.append(QRichLabel("Spendable BTC:", doWrap=False))

      for i in range(len(lbls)):
         lbls[i].setAlignment(Qt.AlignLeft | Qt.AlignTop)
         lbls[i].setText('<b>' + str(lbls[i].text()) + '</b>')
         
      self.dispID = QRichLabel('')
      self.dispName = QRichLabel('')
      self.dispName.setWordWrap(True)
      # This line fixes squished text when word wrapping
      self.dispName.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
      self.dispDescr = QRichLabel('')
      self.dispDescr.setWordWrap(True)
      # This line fixes squished text when word wrapping
      self.dispDescr.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
      self.dispBal = QMoneyLabel(0)
      self.dispBal.setTextFormat(Qt.RichText)
      
      wltInfoFrame = QFrame()
      wltInfoFrame.setFrameStyle(STYLE_SUNKEN)
      wltInfoFrame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
      frmLayout = QGridLayout()
      for i in range(len(lbls)):
         frmLayout.addWidget(lbls[i], i, 0, 1, 1)

      self.dispID.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.dispName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.dispDescr.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.dispBal.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.dispDescr.setMinimumWidth(tightSizeNChar(self.dispDescr, 30)[0])
      frmLayout.addWidget(self.dispID,     0, 2, 1, 1)
      frmLayout.addWidget(self.dispName,   1, 2, 1, 1)
      frmLayout.addWidget(self.dispDescr,  2, 2, 1, 1)
      frmLayout.addWidget(self.dispBal,    3, 2, 1, 1)
      if coinControlCallback:
         self.lblCoinCtrl = QRichLabel('Source: All addresses', doWrap=False)
         frmLayout.addWidget(self.lblCoinCtrl, 4, 2, 1, 1)
         self.btnCoinCtrl = QPushButton('Coin Control')
         self.connect(self.btnCoinCtrl, SIGNAL(CLICKED), self.doCoinCtrl)
         frmLayout.addWidget(self.btnCoinCtrl, 4, 0, 1, 2)
      frmLayout.setColumnStretch(0, 1)
      frmLayout.setColumnStretch(1, 1)
      frmLayout.setColumnStretch(2, 1)
      
      frmLayout.addItem(QSpacerItem(20, 10, QSizePolicy.Fixed, QSizePolicy.Expanding), 0, 1, 4, 1)
      wltInfoFrame.setLayout(frmLayout)

      if self.doVerticalLayout:
         layout.addWidget(makeLayoutFrame(VERTICAL, [self.walletComboBox, wltInfoFrame]) )
      else:
         layout.addWidget(makeLayoutFrame(HORIZONTAL, [self.walletListBox, wltInfoFrame]) )

      self.setLayout(layout)

      # Make sure this is called once so that the default selection is displayed
      self.updateOnWalletChange()

   
   def getWalletIdList(self, onlyOfflineWallets):
      result = []
      if onlyOfflineWallets:
         result = self.main.getWatchingOnlyWallets()
      else:
         result = list(self.main.walletIDList)
      return result


   def getSelectedWltID(self):
      idx = -1
      if self.doVerticalLayout:
         idx = self.walletComboBox.currentIndex()
      else:
         idx = self.walletListBox.currentRow()

      return '' if idx<0 else self.displayIDs[idx]

   def doCoinCtrl(self):
      wlt = self.main.walletMap[self.getSelectedWltID()]
      dlgcc = DlgCoinControl(self, self.main, wlt, self.sourceAddrList)
      if dlgcc.exec_():
         self.sourceAddrList = [x[0] for x in dlgcc.coinControlList]
         self.altBalance = sum([x[1] for x in dlgcc.coinControlList])
      
         nAddr = len(self.sourceAddrList)
         if self.altBalance == wlt.getBalance('Spendable'):
            self.lblCoinCtrl.setText('Source: All addresses')
            self.sourceAddrList = None
            self.altBalance = None
         elif nAddr == 0:
            self.lblCoinCtrl.setText('Source: None selected')
         elif nAddr == 1:
            aStr = hash160_to_addrStr(self.sourceAddrList[0])
            self.lblCoinCtrl.setText('Source: %s...' % aStr[:12])
         elif nAddr > 1:
            self.lblCoinCtrl.setText('Source: %d addresses' % nAddr)
         self.updateOnCoinControl()
         
   def updateOnWalletChange(self, ignoredInt=None):
      """
      "ignoredInt" is because the signals should call this function with the
      selected index of the relevant container, but we grab it again anyway
      using getSelectedWltID()
      """

      wltID = self.getSelectedWltID()

      if len(wltID) > 0:
         wlt = self.main.walletMap[wltID]
               
         self.dispID.setText(wltID)
         self.dispName.setText(wlt.labelName)
         self.dispDescr.setText(wlt.labelDescr)
         self.selectedID = wltID
         
         if not TheBDM.getBDMState() == 'BlockchainReady':
            self.dispBal.setText('-' * 12)
         else:
            bal = wlt.getBalance('Spendable')
            balStr = coin2str(wlt.getBalance('Spendable'), maxZeros=1)
            if bal <= self.balAtLeast:
               self.dispBal.setText('<font color="red"><b>%s</b></font>' % balStr)
            else:
               self.dispBal.setText('<b>' + balStr + '</b>')     

         if self.selectWltCallback:
            self.selectWltCallback(wlt)

         self.repaint()
         # Reset the coin control variables after a new wallet is selected
         if self.coinControlCallback:
            self.altBalance = None
            self.sourceAddrList = None
            self.btnCoinCtrl.setEnabled(wlt.getBalance('Spendable')>0)
            self.lblCoinCtrl.setText('Source: All addresses' if wlt.getBalance('Spendable')>0 else\
                                     'Source: 0 addresses' )
            self.updateOnCoinControl()
      
   def updateOnCoinControl(self):
      useAllAddr = (self.altBalance == None)
      wlt = self.main.walletMap[self.getSelectedWltID()]
      fullBal = wlt.getBalance('Spendable')
      if useAllAddr:
         self.dispID.setText(wlt.uniqueIDB58)
         self.dispName.setText(wlt.labelName)
         self.dispDescr.setText(wlt.labelDescr)
         if fullBal == 0:
            self.dispBal.setText('0.0', color='TextRed', bold=True)
         else:
            self.dispBal.setValueText(fullBal, wBold=True)
      else:
         self.dispID.setText(wlt.uniqueIDB58 + '*')
         self.dispName.setText(wlt.labelName + '*')
         self.dispDescr.setText('*Coin Control Subset*', color='TextBlue', bold=True)
         self.dispBal.setText(coin2str(self.altBalance, maxZeros=0), color='TextBlue')
         rawValTxt = str(self.dispBal.text())
         self.dispBal.setText(rawValTxt + ' <font color="%s">(of %s)</font>' % \
                                    (htmlColor('DisableFG'), coin2str(fullBal, maxZeros=0)))

      if not TheBDM.getBDMState() == 'BlockchainReady':
         self.dispBal.setText('(available when online)', color='DisableFG')
      self.repaint()
      if self.coinControlCallback:
         self.coinControlCallback(self.sourceAddrList, self.altBalance)





# Container for controls used in configuring a wallet to be added to any
# dialog or wizard. Currently it is only used the create wallet wizard.
# Just has Name and Description
# Advanced options have just been moved to their own frame to be used in 
# the restore wallet dialog as well.
class NewWalletFrame(ArmoryFrame):

   def __init__(self, parent, main, initLabel=''):
      super(NewWalletFrame, self).__init__(parent, main)
      self.editName = QLineEdit()
      self.editName.setMinimumWidth(tightSizeNChar(self.editName,\
                                 WALLET_DATA_ENTRY_FIELD_WIDTH)[0])
      self.editName.setText(initLabel)
      lblName = QLabel("Wallet &name:")
      lblName.setBuddy(self.editName)

      self.editDescription = QTextEdit()
      self.editDescription.setMaximumHeight(75)
      self.editDescription.setMinimumWidth(tightSizeNChar(self.editDescription,\
                                 WALLET_DATA_ENTRY_FIELD_WIDTH)[0])
      lblDescription = QLabel("Wallet &description:")
      lblDescription.setAlignment(Qt.AlignVCenter)
      lblDescription.setBuddy(self.editDescription)
   
      # breaking this up into tabs
      frameLayout = QVBoxLayout()
      newWalletTabs = QTabWidget()
      
      #### Basic Tab
      nameFrame = makeHorizFrame([lblName, STRETCH, self.editName])
      descriptionFrame = makeHorizFrame([lblDescription,
                                         STRETCH, self.editDescription])
      basicQTab = makeVertFrame([nameFrame, descriptionFrame, STRETCH])
      newWalletTabs.addTab(basicQTab, "Configure")
      
      # Fork watching-only wallet
      self.advancedOptionsTab = AdvancedOptionsFrame(parent, main)
      newWalletTabs.addTab(self.advancedOptionsTab, "Advanced Options")

      frameLayout.addWidget(newWalletTabs)
      self.setLayout(frameLayout)

      # These help us collect entropy as the user goes through the wizard
      # to be used for wallet creation
      self.main.registerWidgetActivateTime(self)

      
   def getKdfSec(self):
      return self.advancedOptionsTab.getKdfSec()

   def getKdfBytes(self):
      return self.advancedOptionsTab.getKdfBytes()
   
   def getName(self):
      return str(self.editName.text())

   def getDescription(self):
      return str(self.editDescription.toPlainText())

class AdvancedOptionsFrame(ArmoryFrame):
   def __init__(self, parent, main, initLabel=''):
      super(AdvancedOptionsFrame, self).__init__(parent, main)
      lblComputeDescription = QRichLabel( \
                  'Armory will test your system\'s speed to determine the most '
                  'challenging encryption settings that can be performed '
                  'in a given amount of time.  High settings make it much harder '
                  'for someone to guess your passphrase.  This is used for all '
                  'encrypted wallets, but the default parameters can be changed below.\n')
      lblComputeDescription.setWordWrap(True)
      timeDescriptionTip = main.createToolTipWidget( \
                  'This is the amount of time it will take for your computer '
                  'to unlock your wallet after you enter your passphrase. '
                  '(the actual time used will be less than the specified '
                  'time, but more than one half of it).  ')
      
      # Set maximum compute time
      self.editComputeTime = QLineEdit()
      self.editComputeTime.setText('250 ms')
      self.editComputeTime.setMaxLength(12)
      lblComputeTime = QLabel('Target compute &time (s, ms):')
      memDescriptionTip = main.createToolTipWidget( \
                  'This is the <b>maximum</b> memory that will be '
                  'used as part of the encryption process.  The actual value used '
                  'may be lower, depending on your system\'s speed.  If a '
                  'low value is chosen, Armory will compensate by chaining '
                  'together more calculations to meet the target time.  High '
                  'memory target will make GPU-acceleration useless for '
                  'guessing your passphrase.')
      lblComputeTime.setBuddy(self.editComputeTime)

      # Set maximum memory usage
      self.editComputeMem = QLineEdit()
      self.editComputeMem.setText('32.0 MB')
      self.editComputeMem.setMaxLength(12)
      lblComputeMem  = QLabel('Max &memory usage (kB, MB):')
      lblComputeMem.setBuddy(self.editComputeMem)

      self.editComputeTime.setMaximumWidth( tightSizeNChar(self, 20)[0] )
      self.editComputeMem.setMaximumWidth( tightSizeNChar(self, 20)[0] )
      
      entryFrame = QFrame()
      entryLayout = QGridLayout()
      entryLayout.addWidget(timeDescriptionTip,        0, 0,  1, 1)
      entryLayout.addWidget(lblComputeTime,      0, 1,  1, 1)
      entryLayout.addWidget(self.editComputeTime, 0, 2,  1, 1)
      entryLayout.addWidget(memDescriptionTip,         1, 0,  1, 1)
      entryLayout.addWidget(lblComputeMem,       1, 1,  1, 1)
      entryLayout.addWidget(self.editComputeMem,  1, 2,  1, 1)
      entryFrame.setLayout(entryLayout)
      layout = QVBoxLayout()
      layout.addWidget(lblComputeDescription)
      layout.addWidget(entryFrame)
      layout.addStretch()
      self.setLayout(layout)
   
   def getKdfSec(self):
      # return -1 if the input is invalid
      kdfSec = -1
      try:
         kdfT, kdfUnit = str(self.editComputeTime.text()).strip().split(' ')
         if kdfUnit.lower() == 'ms':
            kdfSec = float(kdfT) / 1000.
         elif kdfUnit.lower() in ('s', 'sec', 'seconds'):
            kdfSec = float(kdfT)
      except:
         pass
      return kdfSec

   def getKdfBytes(self):
      # return -1 if the input is invalid
      kdfBytes = -1
      try:
         kdfM, kdfUnit = str(self.editComputeMem.text()).split(' ')
         if kdfUnit.lower() == 'mb':
            kdfBytes = round(float(kdfM) * (1024.0 ** 2))
         elif kdfUnit.lower() == 'kb':
            kdfBytes = round(float(kdfM) * (1024.0))
      except:
         pass
      return kdfBytes
      
class SetPassphraseFrame(ArmoryFrame):
   def __init__(self, parent, main, initLabel='', passphraseCallback=None):
      super(SetPassphraseFrame, self).__init__(parent, main)
      self.passphraseCallback = passphraseCallback
      layout = QGridLayout()
      lblDlgDescr = QLabel('Please enter a passphrase for wallet encryption.\n\n'
                           'A good passphrase consists of at least 10 or more\n'
                           'random letters, or 6 or more random words.\n')
      lblDlgDescr.setWordWrap(True)
      layout.addWidget(lblDlgDescr, 0, 0, 1, 2)
      lblPwd1 = QLabel("New Passphrase:")
      self.editPasswd1 = QLineEdit()
      self.editPasswd1.setEchoMode(QLineEdit.Password)
      self.editPasswd1.setMinimumWidth(MIN_PASSWD_WIDTH(self))

      lblPwd2 = QLabel("Again:")
      self.editPasswd2 = QLineEdit()
      self.editPasswd2.setEchoMode(QLineEdit.Password)
      self.editPasswd2.setMinimumWidth(MIN_PASSWD_WIDTH(self))

      layout.addWidget(lblPwd1, 1, 0)
      layout.addWidget(lblPwd2, 2, 0)
      layout.addWidget(self.editPasswd1, 1, 1)
      layout.addWidget(self.editPasswd2, 2, 1)

      self.lblMatches = QLabel(' ' * 20)
      self.lblMatches.setTextFormat(Qt.RichText)
      layout.addWidget(self.lblMatches, 3, 1)
      self.setLayout(layout)
      self.connect(self.editPasswd1, SIGNAL('textChanged(QString)'), \
                   self.checkPassphrase)
      self.connect(self.editPasswd2, SIGNAL('textChanged(QString)'), \
                   self.checkPassphrase)


      # These help us collect entropy as the user goes through the wizard
      # to be used for wallet creation
      self.main.registerWidgetActivateTime(self)

   
   # This function is multi purpose. It updates the screen and validates the passphrase
   def checkPassphrase(self, sideEffects=True):
      result = True
      p1 = self.editPasswd1.text()
      p2 = self.editPasswd2.text()
      goodColor = htmlColor('TextGreen')
      badColor = htmlColor('TextRed')
      if not isASCII(unicode(p1)) or \
         not isASCII(unicode(p2)):
         if sideEffects:
            self.lblMatches.setText('<font color=%s><b>Passphrase is non-ASCII!</b></font>' % badColor)
         result = False
      elif not p1 == p2:
         if sideEffects:
            self.lblMatches.setText('<font color=%s><b>Passphrases do not match!</b></font>' % badColor)
         result = False
      elif len(p1) < 5:
         if sideEffects:
            self.lblMatches.setText('<font color=%s><b>Passphrase is too short!</b></font>' % badColor)
         result = False
      if sideEffects:
         if result:
            self.lblMatches.setText('<font color=%s><b>Passphrases match!</b></font>' % goodColor)
         if self.passphraseCallback:
            self.passphraseCallback()
      return result

   def getPassphrase(self):
      return str(self.editPasswd1.text())
   
class VerifyPassphraseFrame(ArmoryFrame):
   def __init__(self, parent, main, initLabel=''):
      super(VerifyPassphraseFrame, self).__init__(parent, main)
      lblWarnImgL = QLabel()
      lblWarnImgL.setPixmap(QPixmap(':/MsgBox_warning48.png'))
      lblWarnImgL.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      lblWarnTxt1 = QRichLabel(\
         '<font color="red"><b>!!! DO NOT FORGET YOUR PASSPHRASE !!!</b></font>', size=4)
      lblWarnTxt1.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnTxt2 = QRichLabel(\
         '<b>No one can help you recover you bitcoins if you forget the '
         'passphrase and don\'t have a paper backup!</b> Your wallet and '
         'any <u>digital</u> backups are useless if you forget it.  '
         '<br><br>'
         'A <u>paper</u> backup protects your wallet forever, against '
         'hard-drive loss and losing your passphrase.  It also protects you '
         'from theft, if the wallet was encrypted and the paper backup '
         'was not stolen with it.  Please make a paper backup and keep it in '
         'a safe place.'
         '<br><br>'
         'Please enter your passphrase a third time to indicate that you '
         'are aware of the risks of losing your passphrase!</b>', doWrap=True)


      self.edtPasswd3 = QLineEdit()
      self.edtPasswd3.setEchoMode(QLineEdit.Password)
      self.edtPasswd3.setMinimumWidth(MIN_PASSWD_WIDTH(self))

      layout = QGridLayout()
      layout.addWidget(lblWarnImgL, 0, 0, 4, 1)
      layout.addWidget(lblWarnTxt1, 0, 1, 1, 1)
      layout.addWidget(lblWarnTxt2, 2, 1, 1, 1)
      layout.addWidget(self.edtPasswd3, 5, 1, 1, 1)
      self.setLayout(layout)

      # These help us collect entropy as the user goes through the wizard
      # to be used for wallet creation
      self.main.registerWidgetActivateTime(self)

      
class WalletBackupFrame(ArmoryFrame):
   # Some static enums, and a QRadioButton with mouse-enter/mouse-leave events
   FEATURES = enum('ProtGen', 'ProtImport', 'LostPass', 'Durable', \
                   'Visual', 'Physical', 'Count')
   OPTIONS = enum('Paper1', 'PaperN', 'DigPlain', 'DigCrypt', 'Export', 'Count')
   def __init__(self, parent, main, initLabel=''):
      super(WalletBackupFrame, self).__init__(parent, main)
      # Don't have a wallet yet so assume false.
      self.hasImportedAddr = False
      self.isBackupCreated = False
      self.passphrase = None
      self.lblTitle = QRichLabel(tr("<b>Backup Options</b>"))
      lblTitleDescr = QRichLabel(tr("""
         Armory wallets only need to be backed up <u>one time, ever.</u>
         The backup is good no matter how many addresses you use. """))
      lblTitleDescr.setOpenExternalLinks(True)


      self.optPaperBackupTop = QRadioButtonBackupCtr(self, \
                                    tr('Printable Paper Backup'), self.OPTIONS.Paper1)
      self.optPaperBackupOne = QRadioButtonBackupCtr(self, \
                                    tr('Single-Sheet (Recommended)'), self.OPTIONS.Paper1)
      self.optPaperBackupFrag = QRadioButtonBackupCtr(self, \
                                    tr('Fragmented Backup (M-of-N)'), self.OPTIONS.PaperN)

      self.optDigitalBackupTop = QRadioButtonBackupCtr(self, \
                                    tr('Digital Backup'), self.OPTIONS.DigPlain)
      self.optDigitalBackupPlain = QRadioButtonBackupCtr(self, \
                                    tr('Unencrypted'), self.OPTIONS.DigPlain)
      self.optDigitalBackupCrypt = QRadioButtonBackupCtr(self, \
                                    tr('Encrypted'), self.OPTIONS.DigCrypt)

      self.optIndivKeyListTop = QRadioButtonBackupCtr(self, \
                                    tr('Export Key Lists'), self.OPTIONS.Export)


      self.optPaperBackupTop.setFont(GETFONT('Var', bold=True))
      self.optDigitalBackupTop.setFont(GETFONT('Var', bold=True))
      self.optIndivKeyListTop.setFont(GETFONT('Var', bold=True))

      # I need to be able to unset the sub-options when they become disabled
      self.optPaperBackupNONE = QRadioButton('')
      self.optDigitalBackupNONE = QRadioButton('')

      btngrpTop = QButtonGroup(self)
      btngrpTop.addButton(self.optPaperBackupTop)
      btngrpTop.addButton(self.optDigitalBackupTop)
      btngrpTop.addButton(self.optIndivKeyListTop)
      btngrpTop.setExclusive(True)

      btngrpPaper = QButtonGroup(self)
      btngrpPaper.addButton(self.optPaperBackupNONE)
      btngrpPaper.addButton(self.optPaperBackupOne)
      btngrpPaper.addButton(self.optPaperBackupFrag)
      btngrpPaper.setExclusive(True)

      btngrpDig = QButtonGroup(self)
      btngrpDig.addButton(self.optDigitalBackupNONE)
      btngrpDig.addButton(self.optDigitalBackupPlain)
      btngrpDig.addButton(self.optDigitalBackupCrypt)
      btngrpDig.setExclusive(True)

      self.connect(self.optPaperBackupTop, SIGNAL(CLICKED), self.optionClicked)
      self.connect(self.optPaperBackupOne, SIGNAL(CLICKED), self.optionClicked)
      self.connect(self.optPaperBackupFrag, SIGNAL(CLICKED), self.optionClicked)
      self.connect(self.optDigitalBackupTop, SIGNAL(CLICKED), self.optionClicked)
      self.connect(self.optDigitalBackupPlain, SIGNAL(CLICKED), self.optionClicked)
      self.connect(self.optDigitalBackupCrypt, SIGNAL(CLICKED), self.optionClicked)
      self.connect(self.optIndivKeyListTop, SIGNAL(CLICKED), self.optionClicked)


      spacer = lambda: QSpacerItem(20, 1, QSizePolicy.Fixed, QSizePolicy.Expanding)
      layoutOpts = QGridLayout()
      layoutOpts.addWidget(self.optPaperBackupTop, 0, 0, 1, 2)
      layoutOpts.addItem(spacer(), 1, 0)
      layoutOpts.addItem(spacer(), 2, 0)
      layoutOpts.addWidget(self.optDigitalBackupTop, 3, 0, 1, 2)
      layoutOpts.addItem(spacer(), 4, 0)
      layoutOpts.addItem(spacer(), 5, 0)
      layoutOpts.addWidget(self.optIndivKeyListTop, 6, 0, 1, 2)

      layoutOpts.addWidget(self.optPaperBackupOne, 1, 1)
      layoutOpts.addWidget(self.optPaperBackupFrag, 2, 1)
      layoutOpts.addWidget(self.optDigitalBackupPlain, 4, 1)
      layoutOpts.addWidget(self.optDigitalBackupCrypt, 5, 1)
      layoutOpts.setColumnStretch(0, 0)
      layoutOpts.setColumnStretch(1, 1)

      frmOpts = QFrame()
      frmOpts.setLayout(layoutOpts)
      frmOpts.setFrameStyle(STYLE_SUNKEN)


      self.featuresTips = [None] * self.FEATURES.Count
      self.featuresLbls = [None] * self.FEATURES.Count
      self.featuresImgs = [None] * self.FEATURES.Count


      F = self.FEATURES
      self.featuresTips[F.ProtGen] = self.main.createToolTipWidget(tr("""
         Every time you click "Receive Bitcoins," a new address is generated.
         All of these addresses are generated from a single seed value, which
         is included in all backups.   Therefore, all addresses that you have
         generated so far <b>and</b> will ever be generated with this wallet, 
         are protected by this backup! """))

      self.featuresTips[F.ProtImport] = self.main.createToolTipWidget(tr("""
         <i>This wallet <u>does not</u> currently have any imported
         addresses, so you can safely ignore this feature!</i>
         When imported addresses are present, backups only protects those
         imported before the backup was made.  You must replace that
         backup if you import more addresses! """))

      self.featuresTips[F.LostPass] = self.main.createToolTipWidget(tr("""
         Lost/forgotten passphrases are, <b>by far</b>, the most common
         reason for users losing bitcoins.  It is critical you have
         at least one backup that works if you forget your wallet
         passphrase. """))

      self.featuresTips[F.Durable] = self.main.createToolTipWidget(tr("""
         USB drives and CD/DVD disks are not intended for long-term storage.
         They will <i>probably</i> last many years, but not guaranteed
         even for 3-5 years.   On the other hand, printed text on paper will
         last many decades, and useful even when thoroughly faded. """))

      self.featuresTips[F.Visual] = self.main.createToolTipWidget(tr("""
         The ability to look at a backup and determine if
         it is still usable.   If a digital backup is stored in a safe
         deposit box, you have no way to verify its integrity unless
         you take a secure computer/device with you.  A simple glance at
         a paper backup is enough to verify that it is still intact. """))

      self.featuresTips[F.Physical] = self.main.createToolTipWidget(tr("""
         If multiple pieces/fragments are required to restore this wallet.
         For instance, encrypted backups require the backup
         <b>and</b> the passphrase.  This feature is only needed for those
         concerned about physical security, not just online security."""))


      MkFeatLabel = lambda x: QRichLabel(tr(x), doWrap=False)
      self.featuresLbls[F.ProtGen] = MkFeatLabel('Protects All Future Addresses')
      self.featuresLbls[F.ProtImport] = MkFeatLabel('Protects Imported Addresses')
      self.featuresLbls[F.LostPass] = MkFeatLabel('Forgotten Passphrase')
      self.featuresLbls[F.Durable] = MkFeatLabel('Long-term Durability')
      self.featuresLbls[F.Visual] = MkFeatLabel('Visual Integrity')
      self.featuresLbls[F.Physical] = MkFeatLabel('Multi-Point Protection')

      if not self.hasImportedAddr:
         self.featuresLbls[F.ProtImport].setEnabled(False)

      self.lblSelFeat = QRichLabel('', doWrap=False, hAlign=Qt.AlignHCenter)

      layoutFeat = QGridLayout()
      layoutFeat.addWidget(self.lblSelFeat, 0, 0, 1, 3)
      layoutFeat.addWidget(HLINE(), 1, 0, 1, 3)
      for i in range(self.FEATURES.Count):
         self.featuresImgs[i] = QLabel('')
         layoutFeat.addWidget(self.featuresTips[i], i + 2, 0)
         layoutFeat.addWidget(self.featuresLbls[i], i + 2, 1)
         layoutFeat.addWidget(self.featuresImgs[i], i + 2, 2)
      layoutFeat.setColumnStretch(0, 0)
      layoutFeat.setColumnStretch(1, 1)
      layoutFeat.setColumnStretch(2, 0)

      frmFeat = QFrame()
      frmFeat.setLayout(layoutFeat)
      frmFeat.setFrameStyle(STYLE_SUNKEN)


      self.lblDescrSelected = QRichLabel('')
      frmFeatDescr = makeVertFrame([self.lblDescrSelected])
      self.lblDescrSelected.setMinimumHeight(tightSizeNChar(self, 10)[1] * 8)

      self.btnDoIt = QPushButton('Create Backup')
      self.connect(self.btnDoIt, SIGNAL(CLICKED), self.clickedDoIt)

      layout = QGridLayout()
      layout.addWidget(self.lblTitle, 0, 0, 1, 2)
      layout.addWidget(lblTitleDescr, 1, 0, 1, 2)
      layout.addWidget(frmOpts, 2, 0)
      layout.addWidget(frmFeat, 2, 1)
      layout.addWidget(frmFeatDescr, 3, 0, 1, 2)
      layout.addWidget(self.btnDoIt, 4, 0, 1, 2)
      layout.setRowStretch(0, 0)
      layout.setRowStretch(1, 0)
      layout.setRowStretch(2, 0)
      layout.setRowStretch(3, 1)
      layout.setRowStretch(4, 0)
      self.setLayout(layout)
      self.setMinimumSize(640, 350)

      self.optPaperBackupTop.setChecked(True)
      self.optPaperBackupOne.setChecked(True)
      self.setDispFrame(-1)
      self.optionClicked()
      
   #############################################################################
   def setWallet(self, wlt):
      self.wlt = wlt
      wltID = wlt.uniqueIDB58
      wltName = wlt.labelName
      self.hasImportedAddr = self.wlt.hasAnyImported()
      # Highlight imported-addr feature if their wallet contains them
      pcolor = 'TextWarn' if self.hasImportedAddr else 'DisableFG'
      self.featuresLbls[self.FEATURES.ProtImport].setText(tr(\
         'Protects Imported Addresses'), color=pcolor)

      if self.hasImportedAddr:
         self.featuresTips[self.FEATURES.ProtImport].setText(tr("""
            When imported addresses are present, backups only protects those
            imported before the backup was made!  You must replace that
            backup if you import more addresses!
            <i>Your wallet <u>does</u> contain imported addresses<i>."""))


         
      self.lblTitle.setText(tr("""
         <b>Backup Options for Wallet "%s" (%s)</b>""" % (wltName, wltID)))

   #############################################################################
   def setDispFrame(self, index):
      if index < 0:
         self.setDispFrame(self.getIndexChecked())
      else:
         # Highlight imported-addr feature if their wallet contains them
         pcolor = 'TextWarn' if self.hasImportedAddr else 'DisableFG'
         self.featuresLbls[self.FEATURES.ProtImport].setText(tr(\
            'Protects Imported Addresses'), color=pcolor)

         txtPaper = tr("""
               Paper backups protect every address ever generated by your
               wallet. It is unencrypted, which means it needs to be stored
               in a secure place, but it will help you recover your wallet
               if you forget your encryption passphrase!
               <br><br>
               <b>You don't need a printer to make a paper backup!
               The data can be copied by hand with pen and paper.</b>
               Paper backups are preferred to digital backups, because you
               know the paper backup will work no matter how many years (or
               decades) it sits in storage.  """)
         txtDigital = tr("""
               Digital backups can be saved to an external hard-drive or
               USB removable media.  It is recommended you make a few
               copies to protect against "bit rot" (degradation). <br><br>""")
         txtDigPlain = tr("""
               <b><u>IMPORTANT:</u> Do not save an unencrypted digital
               backup to your primary hard drive!</b>
               Please save it <i>directly</i> to the backup device.
               Deleting the file does not guarantee the data is actually
               gone!  """)
         txtDigCrypt = tr("""
               <b><u>IMPORTANT:</u> It is critical that you have at least
               one unencrypted backup!</b>  Without it, your bitcoins will
               be lost forever if you forget your passphrase!  This is <b>
               by far</b> the most common reason users lose coins!  Having
               at least one paper backup is recommended.""")
         txtIndivKeys = tr("""
               View and export invidivual addresses strings,
               public keys and/or private keys contained in your wallet.
               This is useful for exporting your private keys to be imported into
               another wallet app or service.
               <br><br>
               You can view/backup imported keys, as well as unused keys in your
               keypool (pregenerated addresses protected by your backup that
               have not yet been used). """)


         chk = lambda: QPixmap(':/checkmark32.png').scaled(20, 20)
         _X_ = lambda: QPixmap(':/red_X.png').scaled(16, 16)
         if index == self.OPTIONS.Paper1:
            self.lblSelFeat.setText(tr('Single-Sheet Paper Backup'), bold=True)
            self.featuresImgs[self.FEATURES.ProtGen   ].setPixmap(chk())
            self.featuresImgs[self.FEATURES.ProtImport].setPixmap(chk())
            self.featuresImgs[self.FEATURES.LostPass  ].setPixmap(chk())
            self.featuresImgs[self.FEATURES.Durable   ].setPixmap(chk())
            self.featuresImgs[self.FEATURES.Visual    ].setPixmap(chk())
            self.featuresImgs[self.FEATURES.Physical  ].setPixmap(_X_())
            self.lblDescrSelected.setText(txtPaper)
         elif index == self.OPTIONS.PaperN:
            self.lblSelFeat.setText(tr('Fragmented Paper Backup'), bold=True)
            self.featuresImgs[self.FEATURES.ProtGen   ].setPixmap(chk())
            self.featuresImgs[self.FEATURES.ProtImport].setPixmap(_X_())
            self.featuresImgs[self.FEATURES.LostPass  ].setPixmap(chk())
            self.featuresImgs[self.FEATURES.Durable   ].setPixmap(chk())
            self.featuresImgs[self.FEATURES.Visual    ].setPixmap(chk())
            self.featuresImgs[self.FEATURES.Physical  ].setPixmap(chk())
            self.lblDescrSelected.setText(txtPaper)
         elif index == self.OPTIONS.DigPlain:
            self.lblSelFeat.setText(tr('Unencrypted Digital Backup'), bold=True)
            self.featuresImgs[self.FEATURES.ProtGen   ].setPixmap(chk())
            self.featuresImgs[self.FEATURES.ProtImport].setPixmap(chk())
            self.featuresImgs[self.FEATURES.LostPass  ].setPixmap(chk())
            self.featuresImgs[self.FEATURES.Durable   ].setPixmap(_X_())
            self.featuresImgs[self.FEATURES.Visual    ].setPixmap(_X_())
            self.featuresImgs[self.FEATURES.Physical  ].setPixmap(_X_())
            self.lblDescrSelected.setText(txtDigital + txtDigPlain)
         elif index == self.OPTIONS.DigCrypt:
            self.lblSelFeat.setText(tr('Encrypted Digital Backup'), bold=True)
            self.featuresImgs[self.FEATURES.ProtGen   ].setPixmap(chk())
            self.featuresImgs[self.FEATURES.ProtImport].setPixmap(chk())
            self.featuresImgs[self.FEATURES.LostPass  ].setPixmap(_X_())
            self.featuresImgs[self.FEATURES.Durable   ].setPixmap(_X_())
            self.featuresImgs[self.FEATURES.Visual    ].setPixmap(_X_())
            self.featuresImgs[self.FEATURES.Physical  ].setPixmap(chk())
            self.lblDescrSelected.setText(txtDigital + txtDigCrypt)
         elif index == self.OPTIONS.Export:
            self.lblSelFeat.setText(tr('Export Key Lists'), bold=True)
            self.featuresImgs[self.FEATURES.ProtGen   ].setPixmap(chk())
            self.featuresImgs[self.FEATURES.ProtImport].setPixmap(chk())
            self.featuresImgs[self.FEATURES.LostPass  ].setPixmap(chk())
            self.featuresImgs[self.FEATURES.Durable   ].setPixmap(_X_())
            self.featuresImgs[self.FEATURES.Visual    ].setPixmap(_X_())
            self.featuresImgs[self.FEATURES.Physical  ].setPixmap(_X_())
            self.lblDescrSelected.setText(txtIndivKeys)
         else:
            LOGERROR('What index was sent to setDispFrame? %d', index)
            
   #############################################################################
   def getIndexChecked(self):
      if self.optPaperBackupOne.isChecked():
         return self.OPTIONS.Paper1
      elif self.optPaperBackupFrag.isChecked():
         return self.OPTIONS.PaperN
      elif self.optPaperBackupTop.isChecked():
         return self.OPTIONS.Paper1
      elif self.optDigitalBackupPlain.isChecked():
         return self.OPTIONS.DigPlain
      elif self.optDigitalBackupCrypt.isChecked():
         return self.OPTIONS.DigCrypt
      elif self.optDigitalBackupTop.isChecked():
         return self.OPTIONS.DigPlain
      elif self.optIndivKeyListTop.isChecked():
         return self.OPTIONS.Export
      else:
         return 0

   #############################################################################
   def optionClicked(self):
      if self.optPaperBackupTop.isChecked():
         self.optPaperBackupOne.setEnabled(True)
         self.optPaperBackupFrag.setEnabled(True)
         self.optDigitalBackupPlain.setEnabled(False)
         self.optDigitalBackupCrypt.setEnabled(False)
         self.optDigitalBackupPlain.setChecked(False)
         self.optDigitalBackupCrypt.setChecked(False)
         self.optDigitalBackupNONE.setChecked(True)
         self.btnDoIt.setText(tr('Create Paper Backup'))
      elif self.optDigitalBackupTop.isChecked():
         self.optDigitalBackupPlain.setEnabled(True)
         self.optDigitalBackupCrypt.setEnabled(True)
         self.optPaperBackupOne.setEnabled(False)
         self.optPaperBackupFrag.setEnabled(False)
         self.optPaperBackupOne.setChecked(False)
         self.optPaperBackupFrag.setChecked(False)
         self.optPaperBackupNONE.setChecked(True)
         self.btnDoIt.setText(tr('Create Digital Backup'))
      elif self.optIndivKeyListTop.isChecked():
         self.optPaperBackupOne.setEnabled(False)
         self.optPaperBackupFrag.setEnabled(False)
         self.optPaperBackupOne.setChecked(False)
         self.optPaperBackupFrag.setChecked(False)
         self.optDigitalBackupPlain.setEnabled(False)
         self.optDigitalBackupCrypt.setEnabled(False)
         self.optDigitalBackupPlain.setChecked(False)
         self.optDigitalBackupCrypt.setChecked(False)
         self.optDigitalBackupNONE.setChecked(True)
         self.optPaperBackupNONE.setChecked(True)
         self.btnDoIt.setText(tr('Export Key Lists'))
      self.setDispFrame(-1)

   def setPassphrase(self, passphrase):
      self.passphrase = passphrase
      
   def clickedDoIt(self):
      isBackupCreated = False
      
      if self.passphrase:
         from qtdialogs import DlgProgress
         unlockProgress = DlgProgress(self, self.main, HBar=1,
                                      Title="Unlocking Wallet")
         unlockProgress.exec_(self.wlt.unlock, 
                              securePassphrase=SecureBinaryData( \
                              self.passphrase),
                              Progress=unlockProgress.UpdateHBar)
         
      if self.optPaperBackupOne.isChecked():
         isBackupCreated = OpenPaperBackupWindow('Single', self.parent(), self.main, self.wlt)
      elif self.optPaperBackupFrag.isChecked():
         isBackupCreated = OpenPaperBackupWindow('Frag', self.parent(), self.main, self.wlt)
      elif self.optDigitalBackupPlain.isChecked():
         if self.main.digitalBackupWarning():
            isBackupCreated = self.main.makeWalletCopy(self, self.wlt, 'Decrypt', 'decrypt')
      elif self.optDigitalBackupCrypt.isChecked():
         isBackupCreated = self.main.makeWalletCopy(self, self.wlt, 'Encrypt', 'encrypt')
      elif self.optIndivKeyListTop.isChecked():
         if self.wlt.useEncryption and self.wlt.isLocked:
            dlg = DlgUnlockWallet(self.wlt, self, self.main, 'Unlock Private Keys')
            if not dlg.exec_():
               if self.main.usermode == USERMODE.Expert:
                  QMessageBox.warning(self, tr('Unlock Failed'), tr("""
                     Wallet was not be unlocked.  The public keys and addresses
                     will still be shown, but private keys will not be available
                     unless you reopen the dialog with the correct passphrase."""), \
                     QMessageBox.Ok)
               else:
                  QMessageBox.warning(self, tr('Unlock Failed'), tr("""
                     'Wallet could not be unlocked to display individual keys."""), \
                     QMessageBox.Ok)
                  if self.main.usermode == USERMODE.Standard:
                     return
         DlgShowKeyList(self.wlt, self.parent(), self.main).exec_()
         isBackupCreated = True
      if isBackupCreated:
         self.isBackupCreated = True

        
      
class WizardCreateWatchingOnlyWalletFrame(ArmoryFrame):

   def __init__(self, parent, main, initLabel='', backupCreatedCallback=None):
      super(WizardCreateWatchingOnlyWalletFrame, self).__init__(parent, main)


      summaryText = QRichLabel(tr("""
               Your wallet has been created and is ready to be used.  It will
               appear in the "<i>Available Wallets</i>" list in the main window.  
               You may click "<i>Finish</i>" if you do not plan to use this 
               wallet on any other computer.
               <br><br>
               A <b>watching-only wallet</b> behaves exactly like a a regular 
               wallet, but does not contain any signing keys.  You can generate 
               addresses and confirm receipt of payments, but not spend or move 
               the funds in the wallet.  To move the funds, 
               use the "<i>Offline Transactions</i>" button on the main 
               window for directions (which involves bringing the transaction 
               to this computer for a signature).  Or you can give the
               watching-only wallet to someone who needs to monitor the wallet
               but should not be able to move the money.
               <br><br>
               Click the button to save a watching-only copy of this wallet.
               Use the "<i>Import or Restore Wallet</i>" button in the
               upper-right corner"""))
      lbtnForkWlt = QPushButton('Create Watching-Only Copy')
      self.connect(lbtnForkWlt, SIGNAL(CLICKED), self.forkOnlineWallet)
      layout = QVBoxLayout()
      layout.addWidget(summaryText)
      layout.addWidget(lbtnForkWlt)
      self.setLayout(layout)
      
   
   def forkOnlineWallet(self):
      currPath = self.wlt.walletPath
      pieces = os.path.splitext(currPath)
      currPath = pieces[0] + '.watchonly' + pieces[1]

      saveLoc = self.main.getFileSave('Save Watching-Only Copy', \
                                      defaultFilename=currPath)
      if not saveLoc.endswith('.wallet'):
         saveLoc += '.wallet'
      self.wlt.forkOnlineWallet(saveLoc, self.wlt.labelName, \
                             '(Watching-Only) ' + self.wlt.labelDescr)   
   
   def setWallet(self, wlt):
      self.wlt = wlt
      
# Need to put circular imports at the end of the script to avoid an import deadlock
from qtdialogs import CLICKED, DlgCoinControl, STRETCH, MIN_PASSWD_WIDTH, \
   QRadioButtonBackupCtr, OpenPaperBackupWindow, DlgUnlockWallet, DlgShowKeyList
