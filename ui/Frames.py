################################################################################
#                                                                              #
# Copyright (C) 2011-2013, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

from PyQt4.QtGui import *
from qtdefines import *
import signal
from PyQt4.Qt import *
from armoryengine.BDM import TheBDM
from armoryengine.ArmoryUtils import coin2str

class ArmoryFrame(QFrame):
   def __init__(self, parent=None, main=None):
      super(ArmoryFrame, self).__init__(parent)

      self.parent = parent
      self.main   = main

   def accept(self):
      self.parent.accpet()
      return

# This class has all of the select wallet display and control functionality for
# selecting a wallet, and doing coin control. It can be dropped into any dialog
# and will interface with the dialog with select wlt and coin control callbacks.
class SelectWalletFrame(ArmoryFrame):
   def __init__(self, parent=None, main=None, firstSelect=None, onlyMyWallets=False, \
                             wltIDList=None, atLeast=0, \
                             selectWltCallback=None, coinControlCallback=None):
      super(SelectWalletFrame, self).__init__(parent, main)
      self.coinControlCallback = coinControlCallback

      self.walletComboBox = QComboBox()
      self.balAtLeast = atLeast
      self.selectWltCallback = selectWltCallback

      if self.main and len(self.main.walletMap) == 0:
         QMessageBox.critical(self, 'No Wallets!', \
            'There are no wallets to select from.  Please create or import '
            'a wallet first.', QMessageBox.Ok)
         self.accept()
         return
      
      self.wltIDList = wltIDList if not wltIDList == None else list(self.main.walletIDList)
      
      selectedWltIndex = 0
      self.selectedID = None
      wltItems = 0
      if len(self.wltIDList) > 0:
         self.selectedID = self.wltIDList[0]
         for wltID in self.wltIDList:
            wlt = self.main.walletMap[wltID]
            wlttype = determineWalletType(wlt, self.main)[0]
            if onlyMyWallets and wlttype == WLTTYPES.WatchOnly:
               continue
            self.walletComboBox.addItem(wlt.labelName)
         
            if wltID == firstSelect:
               selectedWltIndex = wltItems
               self.selectedID = wltID
            wltItems += 1
            
         self.walletComboBox.setCurrentIndex(selectedWltIndex)
      self.connect(self.walletComboBox, SIGNAL('currentIndexChanged(int)'), self.updateOnWalletChange)

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
      self.dispDescr = QRichLabel('')
      self.dispDescr.setWordWrap(True)
      self.dispBal = QMoneyLabel(0)

      self.dispBal.setTextFormat(Qt.RichText)
      
      wltInfoFrame = QFrame()
      wltInfoFrame.setFrameStyle(STYLE_SUNKEN)
      wltInfoFrame.setMaximumWidth(380)
      wltInfoFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
      frmLayout = QGridLayout()
      for i in range(len(lbls)):
         frmLayout.addWidget(lbls[i], i, 0, 1, 1)

      self.dispID.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.dispName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.dispDescr.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.dispBal.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.dispDescr.setMinimumWidth(tightSizeNChar(self.dispDescr, 40)[0])
      frmLayout.addWidget(self.dispID, 0, 2, 1, 1)
      frmLayout.addWidget(self.dispName, 1, 2, 1, 1)
      frmLayout.addWidget(self.dispDescr, 2, 2, 1, 1)
      frmLayout.addWidget(self.dispBal, 3, 2, 1, 1)
      if coinControlCallback:
         self.lblCoinCtrl = QRichLabel('Source: All addresses', doWrap=False)
         frmLayout.addWidget(self.lblCoinCtrl, 4, 2, 1, 1)
         self.btnCoinCtrl = QPushButton('Coin Control')
         self.connect(self.btnCoinCtrl, SIGNAL(CLICKED), self.doCoinCtrl)
         frmLayout.addWidget(self.btnCoinCtrl, 4, 0, 1, 2)
      frmLayout.addItem(QSpacerItem(20, 10, QSizePolicy.Fixed, QSizePolicy.Expanding), 0, 1, 4, 1)
      wltInfoFrame.setLayout(frmLayout)
      layout.addWidget(makeLayoutFrame(VERTICAL, [self.walletComboBox, wltInfoFrame]) )
      self.setLayout(layout)

   def doCoinCtrl(self):
      wlt = self.main.walletMap[self.wltIDList[self.walletComboBox.currentIndex()]]
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
         
   def updateOnWalletChange(self):
      currentWltIndex = self.walletComboBox.currentIndex()
      wltID = self.wltIDList[currentWltIndex]
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
      wlt = self.main.walletMap[self.wltIDList[self.walletComboBox.currentIndex()]]
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
         

class NewWalletLayout(QGridLayout):

   def __init__(self, mainScreen = None, initLabel=''):
      super(NewWalletLayout, self).__init__()
      # Options for creating a new wallet
      lblDlgDescr = QLabel('Create a new wallet for managing your funds.\n'
                           'The name and description can be changed at any time.')
      lblDlgDescr.setWordWrap(True)

      self.edtName = QLineEdit()
      self.edtName.setMaxLength(32)
      self.edtName.setText(initLabel)
      lblName = QLabel("Wallet &name:")
      lblName.setBuddy(self.edtName)


      self.edtDescr = QTextEdit()
      self.edtDescr.setMaximumHeight(75)
      lblDescr = QLabel("Wallet &description:")
      lblDescr.setAlignment(Qt.AlignVCenter)
      lblDescr.setBuddy(self.edtDescr)

      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)


      
      # Advanced Encryption Options
      lblComputeDescr = QLabel( \
                  'Armory will test your system\'s speed to determine the most '
                  'challenging encryption settings that can be performed '
                  'in a given amount of time.  High settings make it much harder '
                  'for someone to guess your passphrase.  This is used for all '
                  'encrypted wallets, but the default parameters can be changed below.\n')
      lblComputeDescr.setWordWrap(True)
      timeDescrTip = mainScreen.createToolTipWidget( \
                  'This is the amount of time it will take for your computer '
                  'to unlock your wallet after you enter your passphrase. '
                  '(the actual time used will be less than the specified '
                  'time, but more than one half of it).  ')
      
      
      # Set maximum compute time
      self.edtComputeTime = QLineEdit()
      self.edtComputeTime.setText('250 ms')
      self.edtComputeTime.setMaxLength(12)
      lblComputeTime = QLabel('Target compute &time (s, ms):')
      memDescrTip = mainScreen.createToolTipWidget( \
                  'This is the <b>maximum</b> memory that will be '
                  'used as part of the encryption process.  The actual value used '
                  'may be lower, depending on your system\'s speed.  If a '
                  'low value is chosen, Armory will compensate by chaining '
                  'together more calculations to meet the target time.  High '
                  'memory target will make GPU-acceleration useless for '
                  'guessing your passphrase.')
      lblComputeTime.setBuddy(self.edtComputeTime)


      # Set maximum memory usage
      self.edtComputeMem = QLineEdit()
      self.edtComputeMem.setText('32.0 MB')
      self.edtComputeMem.setMaxLength(12)
      lblComputeMem  = QLabel('Max &memory usage (kB, MB):')
      lblComputeMem.setBuddy(self.edtComputeMem)

      self.edtComputeTime.setMaximumWidth( tightSizeNChar(self, 20)[0] )
      self.edtComputeMem.setMaximumWidth( tightSizeNChar(self, 20)[0] )

      # Fork watching-only wallet
      cryptoLayout = QGridLayout()
      cryptoLayout.addWidget(lblComputeDescr,     0, 0,  1, 3)

      cryptoLayout.addWidget(timeDescrTip,        1, 0,  1, 1)
      cryptoLayout.addWidget(lblComputeTime,      1, 1,  1, 1)
      cryptoLayout.addWidget(self.edtComputeTime, 1, 2,  1, 1)

      cryptoLayout.addWidget(memDescrTip,         2, 0,  1, 1)
      cryptoLayout.addWidget(lblComputeMem,       2, 1,  1, 1)
      cryptoLayout.addWidget(self.edtComputeMem,  2, 2,  1, 1)

      self.cryptoFrame = QFrame()
      self.cryptoFrame.setFrameStyle(STYLE_SUNKEN)
      self.cryptoFrame.setLayout(cryptoLayout)
      self.cryptoFrame.setVisible(False)

      self.chkUseCrypto  = QCheckBox("Use wallet &encryption")
      self.chkUseCrypto.setChecked(True)
      usecryptoTooltip = mainScreen.createToolTipWidget(
                  'Encryption prevents anyone who accesses your computer '
                  'or wallet file from being able to spend your money, as  '
                  'long as they do not have the passphrase.'
                  'You can choose to encrypt your wallet at a later time '
                  'through the wallet properties dialog by double clicking '
                  'the wallet on the dashboard.')

      # For a new wallet, the user may want to print out a paper backup
      self.chkPrintPaper = QCheckBox("Print a paper-backup of this wallet")
      self.chkPrintPaper.setChecked(True)
      paperBackupTooltip = mainScreen.createToolTipWidget(
                  'A paper-backup allows you to recover your wallet/funds even '
                  'if you lose your original wallet file, any time in the future. '
                  'Because Armory uses "deterministic wallets," '
                  'a single backup when the wallet is first made is sufficient '
                  'for all future transactions (except ones to imported '
                  'addresses).\n\n'
                  'Anyone who gets ahold of your paper backup will be able to spend '
                  'the money in your wallet, so please secure it appropriately.')

      
      self.btnAccept    = QPushButton("Accept")
      self.btnCancel    = QPushButton("Cancel")
      self.btnAdvCrypto = QPushButton("Adv. Encrypt Options>>>")
      self.btnAdvCrypto.setCheckable(True)
 
      
      self.addWidget(lblDlgDescr,        1, 0, 1, 2)
      self.addWidget(lblName,            2, 0, 1, 1)
      self.addWidget(self.edtName,       2, 1, 1, 2)
      self.addWidget(lblDescr,           3, 0, 1, 2)
      self.addWidget(self.edtDescr,      3, 1, 2, 2)
      self.addWidget(self.chkUseCrypto,  5, 0, 1, 1)
      self.addWidget(usecryptoTooltip,   5, 1, 1, 1)
      self.addWidget(self.chkPrintPaper, 6, 0, 1, 1)
      self.addWidget(paperBackupTooltip, 6, 1, 1, 1)
      self.addWidget(self.cryptoFrame,   8, 0, 3, 3)
   

      self.setVerticalSpacing(5)
      self.setSizeConstraint(QLayout.SetFixedSize)

      self.connect(self.chkUseCrypto, SIGNAL("clicked()"), \
                   self.cryptoFrame,  SLOT("setEnabled(bool)"))
         
# Need to put circular imports at the end of the script to avoid an import deadlock
# DlgWalletSelect uses SelectWalletFrame which uses DlgCoinControl
from qtdialogs import CLICKED, DlgCoinControl