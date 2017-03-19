################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

from PyQt4.Qt import * #@UnusedWildImport
from PyQt4.QtGui import * #@UnusedWildImport
from armoryengine.ArmoryUtils import USE_TESTNET, USE_REGTEST, int_to_binary
from ui.WalletFrames import NewWalletFrame, SetPassphraseFrame, VerifyPassphraseFrame,\
   WalletBackupFrame, WizardCreateWatchingOnlyWalletFrame, CardDeckFrame
from ui.TxFrames import SendBitcoinsFrame, SignBroadcastOfflineTxFrame,\
   ReviewOfflineTxFrame
from qtdefines import USERMODE, GETFONT, AddToRunningDialogsList
from armoryengine.PyBtcWallet import PyBtcWallet
from CppBlockUtils import SecureBinaryData
from armoryengine.BDM import TheBDM, BDM_OFFLINE, BDM_UNINITIALIZED
from qtdialogs import DlgProgress

# This class is intended to be an abstract Wizard class that
# will hold all of the functionality that is common to all 
# Wizards in Armory. 
class ArmoryWizard(QWizard):
   def __init__(self, parent, main):
      super(QWizard, self).__init__(parent)
      self.setWizardStyle(QWizard.ClassicStyle)
      self.parent = parent
      self.main   = main
      self.setFont(GETFONT('var'))
      self.setWindowFlags(Qt.Window)
      # Need to adjust the wizard frame size whenever the page changes.
      self.connect(self, SIGNAL('currentIdChanged(int)'), self.fitContents)
      if USE_TESTNET:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [TESTNET]')
         self.setWindowIcon(QIcon(':/armory_icon_green_32x32.png'))
      elif USE_REGTEST:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [REGTEST]')
         self.setWindowIcon(QIcon(':/armory_icon_green_32x32.png'))
      else:
         self.setWindowTitle('Armory - Bitcoin Wallet Management')
         self.setWindowIcon(QIcon(':/armory_icon_32x32.png'))
   
   def fitContents(self):
      self.adjustSize()
   
   @AddToRunningDialogsList
   def exec_(self):
      return super(ArmoryWizard, self).exec_()

# This class is intended to be an abstract Wizard Page class that
# will hold all of the functionality that is common to all 
# Wizard pages in Armory. 
# The layout is QVBoxLayout and holds a single QFrame (self.pageFrame)
class ArmoryWizardPage(QWizardPage):
   def __init__(self, wizard, pageFrame):
      super(ArmoryWizardPage, self).__init__(wizard)
      self.pageFrame = pageFrame
      self.pageLayout = QVBoxLayout()
      self.pageLayout.addWidget(self.pageFrame)
      self.setLayout(self.pageLayout)
   
   # override this method to implement validators
   def validatePage(self):
      return True

################################ Wallet Wizard ################################
# Wallet Wizard has these pages:
#     1. Create Wallet
#     2. Set Passphrase
#     3. Verify Passphrase
#     4. Create Paper Backup
#     5. Create Watcing Only Wallet
class WalletWizard(ArmoryWizard):
   def __init__(self, parent, main):
      super(WalletWizard,self).__init__(parent, main)
      self.newWallet = None
      self.isBackupCreated = False
      self.setWindowTitle(self.tr("Wallet Creation Wizard"))
      self.setOption(QWizard.HaveFinishButtonOnEarlyPages, on=True)
      self.setOption(QWizard.IgnoreSubTitles, on=True)

      self.walletCreationId, self.manualEntropyId, self.setPassphraseId, self.verifyPassphraseId, self.walletBackupId, self.WOWId = range(6)
      
      # Page 1: Create Wallet
      self.walletCreationPage = WalletCreationPage(self)
      self.setPage(self.walletCreationId, self.walletCreationPage)
      
      # Page 1.5: Add manual entropy
      self.manualEntropyPage = ManualEntropyPage(self)
      self.setPage(self.manualEntropyId, self.manualEntropyPage)
      
      # Page 2: Set Passphrase
      self.setPassphrasePage = SetPassphrasePage(self)
      self.setPage(self.setPassphraseId, self.setPassphrasePage)
      
      # Page 3: Verify Passphrase
      self.verifyPassphrasePage = VerifyPassphrasePage(self)
      self.setPage(self.verifyPassphraseId, self.verifyPassphrasePage)

      # Page 4: Create Paper Backup
      self.walletBackupPage = WalletBackupPage(self)
      self.setPage(self.walletBackupId, self.walletBackupPage)
      
      # Page 5: Create Watching Only Wallet -- but only if expert, or offline
      self.hasCWOWPage = False
      if self.main.usermode==USERMODE.Expert or TheBDM.getState() == BDM_OFFLINE:
         self.hasCWOWPage = True
         self.createWOWPage = CreateWatchingOnlyWalletPage(self)
         self.setPage(self.WOWId, self.createWOWPage)

      self.setButtonLayout([QWizard.BackButton,
                            QWizard.Stretch,
                            QWizard.NextButton,
                            QWizard.FinishButton])

   def initializePage(self, *args, **kwargs):

      if self.currentPage() == self.verifyPassphrasePage:
         self.verifyPassphrasePage.setPassphrase(
               self.setPassphrasePage.pageFrame.getPassphrase())
      elif self.hasCWOWPage and self.currentPage() == self.createWOWPage:
         self.createWOWPage.pageFrame.setWallet(self.newWallet)
         
      if self.currentPage() == self.walletBackupPage:
         self.createNewWalletFromWizard()
         self.walletBackupPage.pageFrame.setPassphrase(
                  self.setPassphrasePage.pageFrame.getPassphrase())         
         self.walletBackupPage.pageFrame.setWallet(self.newWallet)
         
         # Hide the back button on wallet backup page  
         self.setButtonLayout([QWizard.Stretch,
                                QWizard.NextButton,
                                QWizard.FinishButton])
      elif self.currentPage() == self.walletCreationPage:
         # Hide the back button on the first page  
         self.setButtonLayout([QWizard.Stretch,
                                QWizard.NextButton,
                                QWizard.FinishButton])
      else:
         self.setButtonLayout([QWizard.BackButton,
                                QWizard.Stretch,
                                QWizard.NextButton,
                                QWizard.FinishButton])
   def done(self, event):
      if self.newWallet and not self.walletBackupPage.pageFrame.isBackupCreated:
         reply = QMessageBox.question(self, self.tr('Wallet Backup Warning'), self.tr('<qt>'
               'You have not made a backup for your new wallet.  You only have '
               'to make a backup of your wallet <u>one time</u> to protect '
               'all the funds held by this wallet <i>any time in the future</i> '
               '(it is a backup of the signing keys, not the coins themselves).'
               '<br><br>'
               'If you do not make a backup, you will <u>permanently</u> lose '
               'the money in this wallet if you ever forget your password, or '
               'suffer from hardware failure.'
               '<br><br>'
               'Are you sure that you want to leave this wizard without backing '
               'up your wallet?</qt>'), \
               QMessageBox.Yes | QMessageBox.No)
         if reply == QMessageBox.No:
            # Stay in the wizard
            return None
      return super(WalletWizard, self).done(event)
             
   def createNewWalletFromWizard(self):
      entropy = None
      if self.walletCreationPage.isManualEncryption():
         entropy = SecureBinaryData(
            int_to_binary(self.manualEntropyPage.pageFrame.getEntropy()))
      else:
         entropy = self.main.getExtraEntropyForKeyGen()
      self.newWallet = PyBtcWallet().createNewWallet(
         securePassphrase=self.setPassphrasePage.pageFrame.getPassphrase(),
         kdfTargSec=self.walletCreationPage.pageFrame.getKdfSec(),
         kdfMaxMem=self.walletCreationPage.pageFrame.getKdfBytes(),
         shortLabel=self.walletCreationPage.pageFrame.getName(),
         longLabel=self.walletCreationPage.pageFrame.getDescription(),
         doRegisterWithBDM=False,
         extraEntropy=entropy,
      )

      self.newWallet.unlock(securePassphrase=
               SecureBinaryData(self.setPassphrasePage.pageFrame.getPassphrase()))
      # We always want to fill the address pool, right away.  
      fillPoolProgress = DlgProgress(self, self.main, HBar=1, \
                                     Title=self.tr("Creating Wallet") )
      fillPoolProgress.exec_(self.newWallet.fillAddressPool, doRegister=False,
                             Progress=fillPoolProgress.UpdateHBar)

      # Reopening from file helps make sure everything is correct -- don't
      # let the user use a wallet that triggers errors on reading it
      wltpath = self.newWallet.walletPath
      walletFromDisk = PyBtcWallet().readWalletFile(wltpath)
      self.main.addWalletToApplication(walletFromDisk, walletIsNew=True)
   
   def cleanupPage(self, *args, **kwargs):
      if self.hasCWOWPage and self.currentPage() == self.createWOWPage:
         self.setButtonLayout([QWizard.Stretch,
                               QWizard.NextButton,
                               QWizard.FinishButton])
      # If we are backing up from setPassphrasePage must be going
      # to the first page.
      elif self.currentPage() == self.setPassphrasePage:
         # Hide the back button on the first page
         self.setButtonLayout([QWizard.Stretch,
                                QWizard.NextButton,
                                QWizard.FinishButton])
      else:
         self.setButtonLayout([QWizard.BackButton,
                               QWizard.Stretch,
                               QWizard.NextButton,
                               QWizard.FinishButton])
          

class ManualEntropyPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(ManualEntropyPage, self).__init__(wizard,
            CardDeckFrame(wizard, wizard.main, wizard.tr("Shuffle a deck of cards")))
      self.wizard = wizard
      self.setTitle(wizard.tr("Step 1: Add Manual Entropy"))
      self.setSubTitle(wizard.tr('Use a deck of cards to get a new random number for your wallet.'))

   def validatePage(self):
      return self.pageFrame.hasGoodEntropy()

   def nextId(self):
      return self.wizard.setPassphraseId


class WalletCreationPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(WalletCreationPage, self).__init__(wizard,
            NewWalletFrame(wizard, wizard.main, "Primary Wallet"))
      self.wizard = wizard
      self.setTitle(wizard.tr("Step 1: Create Wallet"))
      self.setSubTitle(wizard.tr(
            'Create a new wallet for managing your funds. '
            'The name and description can be changed at any time.'))
      
   # override this method to implement validators
   def validatePage(self):
      result = True
      if self.pageFrame.getKdfSec() == -1:
         QMessageBox.critical(self, self.tr('Invalid Target Compute Time'), \
            self.tr('You entered Target Compute Time incorrectly.\n\nEnter: <Number> (ms, s)'), QMessageBox.Ok)
         result = False
      elif self.pageFrame.getKdfBytes() == -1:
         QMessageBox.critical(self, self.tr('Invalid Max Memory Usage'), \
            self.tr('You entered Max Memory Usag incorrectly.\n\nnter: <Number> (kb, mb)'), QMessageBox.Ok)
         result = False
      return result

   def isManualEncryption(self):
      return self.pageFrame.getManualEncryption()

   def nextId(self):
      if self.isManualEncryption():
         return self.wizard.manualEntropyId
      else:
         return self.wizard.setPassphraseId

class SetPassphrasePage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(SetPassphrasePage, self).__init__(wizard, 
               SetPassphraseFrame(wizard, wizard.main, wizard.tr("Set Passphrase"), self.updateNextButton))
      self.wizard = wizard
      self.setTitle(wizard.tr("Step 2: Set Passphrase"))
      self.updateNextButton()

   def updateNextButton(self):
      self.emit(SIGNAL("completeChanged()"))
   
   def isComplete(self):
      return self.pageFrame.checkPassphrase(False)

   def nextId(self):
      return self.wizard.verifyPassphraseId

   
class VerifyPassphrasePage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(VerifyPassphrasePage, self).__init__(wizard, 
            VerifyPassphraseFrame(wizard, wizard.main, wizard.tr("Verify Passphrase")))
      self.wizard = wizard
      self.passphrase = None
      self.setTitle(wizard.tr("Step 3: Verify Passphrase"))
   
   def setPassphrase(self, passphrase):
      self.passphrase = passphrase        
   
   def validatePage(self):
      result = self.passphrase == str(self.pageFrame.edtPasswd3.text())
      if not result:
         QMessageBox.critical(self, self.tr('Invalid Passphrase'), \
            self.tr('You entered your confirmation passphrase incorrectly!'), QMessageBox.Ok)
      return result

   def nextId(self):
      return self.wizard.walletBackupId
      
class WalletBackupPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(WalletBackupPage, self).__init__(wizard,
                                WalletBackupFrame(wizard, wizard.main, wizard.tr("Backup Wallet")))
      self.wizard = wizard
      self.myWizard = wizard
      self.setTitle(wizard.tr("Step 4: Backup Wallet"))
      self.setFinalPage(True)

   def nextId(self):
      if self.wizard.hasCWOWPage:
         return self.wizard.WOWId
      else:
         return -1

class CreateWatchingOnlyWalletPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(CreateWatchingOnlyWalletPage, self).__init__(wizard,
                  WizardCreateWatchingOnlyWalletFrame(wizard, wizard.main, wizard.tr("Create Watching-Only Wallet")))
      self.wizard = wizard
      self.setTitle(wizard.tr("Step 5: Create Watching-Only Wallet"))

   def nextId(self):
      return -1
      
############################### Offline TX Wizard ##############################
# Offline TX Wizard has these pages:
#     1. Create Transaction
#     2. Sign Transaction on Offline Computer
#     3. Broadcast Transaction
class TxWizard(ArmoryWizard):
   def __init__(self, parent, main, wlt, prefill=None, onlyOfflineWallets=False):
      super(TxWizard,self).__init__(parent, main)
      self.setWindowTitle(self.tr("Offline Transaction Wizard"))
      self.setOption(QWizard.IgnoreSubTitles, on=True)
      self.setOption(QWizard.HaveCustomButton1, on=True)
      self.setOption(QWizard.HaveFinishButtonOnEarlyPages, on=True)
      
      # Page 1: Create Offline TX
      self.createTxPage = CreateTxPage(self, wlt, prefill, onlyOfflineWallets=onlyOfflineWallets)
      self.addPage(self.createTxPage)
      
      # Page 2: Sign Offline TX
      self.reviewOfflineTxPage = ReviewOfflineTxPage(self)
      self.addPage(self.reviewOfflineTxPage)
      
      # Page 3: Broadcast Offline TX
      self.signBroadcastOfflineTxPage = SignBroadcastOfflineTxPage(self)
      self.addPage(self.signBroadcastOfflineTxPage)

      self.setButtonText(QWizard.NextButton, self.tr('Create Unsigned Transaction'))
      self.setButtonText(QWizard.CustomButton1, self.tr('Send!'))
      self.connect(self, SIGNAL('customButtonClicked(int)'), self.sendClicked)
      self.setButtonLayout([QWizard.CancelButton,
                            QWizard.BackButton,
                            QWizard.Stretch,
                            QWizard.NextButton,
                            QWizard.CustomButton1])

      

   def initializePage(self, *args, **kwargs):
      if self.currentPage() == self.createTxPage:
         self.createTxPage.pageFrame.fireWalletChange()
      elif self.currentPage() == self.reviewOfflineTxPage:
         self.setButtonText(QWizard.NextButton, self.tr('Next'))
         self.setButtonLayout([QWizard.BackButton,
                            QWizard.Stretch,
                            QWizard.NextButton,
                            QWizard.FinishButton])
         self.reviewOfflineTxPage.pageFrame.setTxDp(self.createTxPage.txdp)
         self.reviewOfflineTxPage.pageFrame.setWallet(
                  self.createTxPage.pageFrame.wlt)
         
   def cleanupPage(self, *args, **kwargs):
      if self.currentPage() == self.reviewOfflineTxPage:
         self.updateOnSelectWallet(self.createTxPage.pageFrame.wlt)
         self.setButtonText(QWizard.NextButton, self.tr('Create Unsigned Transaction'))

   def sendClicked(self, customButtonIndex):
      self.createTxPage.pageFrame.createTxAndBroadcast()
      self.accept()
      
   def updateOnSelectWallet(self, wlt):
      if wlt.watchingOnly:
         self.setButtonLayout([QWizard.CancelButton,
                            QWizard.BackButton,
                            QWizard.Stretch,
                            QWizard.NextButton])
      else:
         self.setButtonLayout([QWizard.CancelButton,
                            QWizard.BackButton,
                            QWizard.Stretch,
                            QWizard.NextButton,
                            QWizard.CustomButton1])
         
class CreateTxPage(ArmoryWizardPage):
   def __init__(self, wizard, wlt, prefill=None, onlyOfflineWallets=False):
      super(CreateTxPage, self).__init__(wizard,
               SendBitcoinsFrame(wizard, wizard.main,
                                 wizard.tr("Create Transaction"), wlt, prefill,
                                 selectWltCallback=self.updateOnSelectWallet,
                                 onlyOfflineWallets=onlyOfflineWallets))
      self.setTitle(self.tr("Step 1: Create Transaction"))
      self.txdp = None
      
   def validatePage(self):
      result = self.pageFrame.validateInputsGetTxDP()
      # the validator also computes the transaction and returns it or False if not valid
      if result:
         self.txdp = result
         result = True
      return result
   
   def updateOnSelectWallet(self, wlt):
      self.wizard().updateOnSelectWallet(wlt)
      
class ReviewOfflineTxPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(ReviewOfflineTxPage, self).__init__(wizard,
                  ReviewOfflineTxFrame(wizard, wizard.main, self.tr("Review Offline Transaction")))
      self.setTitle(self.tr("Step 2: Review Offline Transaction"))
      self.setFinalPage(True)
      
class SignBroadcastOfflineTxPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(SignBroadcastOfflineTxPage, self).__init__(wizard,
                  SignBroadcastOfflineTxFrame(wizard, wizard.main, self.tr("Sign/Broadcast Offline Transaction")))
      self.setTitle(self.tr("Step 3: Sign/Broadcast Offline Transaction"))      
