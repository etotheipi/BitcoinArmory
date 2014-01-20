################################################################################
#                                                                              #
# Copyright (C) 2011-2013, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

from PyQt4.QtGui import * #@UnusedWildImport
from qtdefines import * #@UnusedWildImport
from PyQt4.Qt import * #@UnusedWildImport
from armoryengine.BDM import TheBDM

WALLET_DATA_ENTRY_FIELD_WIDTH = 60

# This class is intended to be an abstract frame class that
# will hold all of the functionality that is common to all 
# Frames used in Armory. 
# The Frames that extend this class should contain all of the
# display and control components for some screen used in Armory
# Putting this content in a frame allows it to be used on it's own
# in a dialog or as a component in a larger frame.
class ArmoryFrame(QFrame):
   def __init__(self, parent=None, main=None):
      super(ArmoryFrame, self).__init__(parent)
 
      self.parent = parent
      self.main = main
 
   def accept(self):
      self.parent.accept()
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
      # This line fixes squished text when word wrapping
      self.dispName.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
      self.dispDescr = QRichLabel('')
      self.dispDescr.setWordWrap(True)
      # This line fixes squished text when word wrapping
      self.dispDescr.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
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


class NewWalletFrame(QFrame):

   def __init__(self, mainScreen = None, initLabel=''):
      super(QFrame, self).__init__()
      self.edtName = QLineEdit()
      self.edtName.setMinimumWidth(tightSizeNChar(self.edtName,\
                                 WALLET_DATA_ENTRY_FIELD_WIDTH)[0])
      self.edtName.setText(initLabel)
      lblName = QLabel("Wallet &name:")
      lblName.setBuddy(self.edtName)

      self.edtDescription = QTextEdit()
      self.edtDescription.setMaximumHeight(75)
      self.edtDescription.setMinimumWidth(tightSizeNChar(self.edtDescription,\
                                 WALLET_DATA_ENTRY_FIELD_WIDTH)[0])
      lblDescription = QLabel("Wallet &description:")
      lblDescription.setAlignment(Qt.AlignVCenter)
      lblDescription.setBuddy(self.edtDescription)

      # Advanced Encryption Options
      lblComputeDescription = QRichLabel( \
                  'Armory will test your system\'s speed to determine the most '
                  'challenging encryption settings that can be performed '
                  'in a given amount of time.  High settings make it much harder '
                  'for someone to guess your passphrase.  This is used for all '
                  'encrypted wallets, but the default parameters can be changed below.\n')
      lblComputeDescription.setWordWrap(True)
      timeDescriptionTip = mainScreen.createToolTipWidget( \
                  'This is the amount of time it will take for your computer '
                  'to unlock your wallet after you enter your passphrase. '
                  '(the actual time used will be less than the specified '
                  'time, but more than one half of it).  ')
      
      # Set maximum compute time
      self.edtComputeTime = QLineEdit()
      self.edtComputeTime.setText('250 ms')
      self.edtComputeTime.setMaxLength(12)
      lblComputeTime = QLabel('Target compute &time (s, ms):')
      memDescriptionTip = mainScreen.createToolTipWidget( \
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
      
      # breaking this up into tabs
      frameLayout = QVBoxLayout()
      newWalletTabs = QTabWidget()
      
      #### Basic Tab
      nameFrame = makeHorizFrame([lblName, STRETCH, self.edtName])
      descriptionFrame = makeHorizFrame([lblDescription,
                                         STRETCH, self.edtDescription])
      basicQTab = makeVertFrame([nameFrame, descriptionFrame, STRETCH])
      newWalletTabs.addTab(basicQTab, "Configure")
      
      # Fork watching-only wallet
      advQTab = QFrame()
      advTabLayout = QGridLayout()
      advTabLayout.addWidget(lblComputeDescription,     0, 0,  1, 3)
      advTabLayout.addWidget(timeDescriptionTip,        1, 0,  1, 1)
      advTabLayout.addWidget(lblComputeTime,      1, 1,  1, 1)
      advTabLayout.addWidget(self.edtComputeTime, 1, 2,  1, 1)
      advTabLayout.addWidget(memDescriptionTip,         2, 0,  1, 1)
      advTabLayout.addWidget(lblComputeMem,       2, 1,  1, 1)
      advTabLayout.addWidget(self.edtComputeMem,  2, 2,  1, 1)
      advQTab.setLayout(advTabLayout)
      newWalletTabs.addTab(advQTab, "Advanced Options")

      frameLayout.addWidget(newWalletTabs)
      self.setLayout(frameLayout)
         
# Need to put circular imports at the end of the script to avoid an import deadlock
# DlgWalletSelect uses SelectWalletFrame which uses DlgCoinControl
from qtdialogs import CLICKED, DlgCoinControl, STRETCH
