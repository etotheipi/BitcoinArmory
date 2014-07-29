################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

from PyQt4.Qt import * #@UnusedWildImport
from PyQt4.QtGui import * #@UnusedWildImport
from armoryengine.ArmoryUtils import USE_TESTNET
from ui.WalletFrames import NewWalletFrame, SetPassphraseFrame, VerifyPassphraseFrame,\
   WalletBackupFrame, WizardCreateWatchingOnlyWalletFrame
from ui.TxFrames import SendBitcoinsFrame, SignBroadcastOfflineTxFrame,\
   ReviewOfflineTxFrame
from qtdefines import USERMODE, GETFONT, tr, AddToRunningDialogsList
from armoryengine.PyBtcWallet import PyBtcWallet
from CppBlockUtils import SecureBinaryData
from armoryengine.BDM import TheBDM
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
      self.setWindowTitle(tr("Wallet Creation Wizard"))
      self.setOption(QWizard.HaveFinishButtonOnEarlyPages, on=True)
      self.setOption(QWizard.IgnoreSubTitles, on=True)
      
      # Page 1: Create Wallet
      self.walletCreationPage = WalletCreationPage(self)
      self.addPage(self.walletCreationPage)
      
      # Page 2: Set Passphrase
      self.setPassphrasePage = SetPassphrasePage(self)
      self.addPage(self.setPassphrasePage)
      
      # Page 3: Verify Passphrase
      self.verifyPassphrasePage = VerifyPassphrasePage(self)
      self.addPage(self.verifyPassphrasePage)
      
      # Page 4: Create Paper Backup
      self.walletBackupPage = WalletBackupPage(self)
      self.addPage(self.walletBackupPage)
      
      # Page 5: Create Watching Only Wallet -- but only if expert, or offline
      self.hasCWOWPage = False
      if self.main.usermode==USERMODE.Expert or not self.main.internetAvail:
         self.hasCWOWPage = True
         self.createWOWPage = CreateWatchingOnlyWalletPage(self)
         self.addPage(self.createWOWPage)

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
         reply = QMessageBox.question(self, tr('Wallet Backup Warning'), tr("""
               You have not made a backup for your new wallet.  You only have 
               to make a backup of your wallet <u>one time</u> to protect 
               all the funds held by this wallet <i>any time in the future</i>
               (it is a backup of the signing keys, not the coins themselves).
               <br><br>
               If you do not make a backup, you will <u>permanently</u> lose
               the money in this wallet if you ever forget your password, or 
               suffer from hardware failure.
               <br><br>
               Are you sure that you want to leave this wizard without backing 
               up your wallet?"""), \
               QMessageBox.Yes | QMessageBox.No)
         if reply == QMessageBox.No:
            # Stay in the wizard
            return None
      return super(WalletWizard, self).done(event)
             
   def createNewWalletFromWizard(self):
      self.newWallet = PyBtcWallet().createNewWallet( \
                     securePassphrase=self.setPassphrasePage.pageFrame.getPassphrase(), \
                     kdfTargSec=self.walletCreationPage.pageFrame.getKdfSec(), \
                     kdfMaxMem=self.walletCreationPage.pageFrame.getKdfBytes(), \
                     shortLabel=self.walletCreationPage.pageFrame.getName(), \
                     longLabel=self.walletCreationPage.pageFrame.getDescription(), \
                     doRegisterWithBDM=False, \
                     extraEntropy=self.main.getExtraEntropyForKeyGen())

      self.newWallet.unlock(securePassphrase=
               SecureBinaryData(self.setPassphrasePage.pageFrame.getPassphrase()))
      # We always want to fill the address pool, right away.  
      fillPoolProgress = DlgProgress(self, self.main, HBar=1, \
                                     Title="Creating Wallet") 
      fillPoolProgress.exec_(self.newWallet.fillAddressPool, doRegister=False,
                             Progress=fillPoolProgress.UpdateHBar)

      # Reopening from file helps make sure everything is correct -- don't
      # let the user use a wallet that triggers errors on reading it
      wltpath = self.newWallet.walletPath
      walletFromDisk = PyBtcWallet().readWalletFile(wltpath)
      self.main.addWalletToApplication(walletFromDisk, walletIsNew=True)
      if TheBDM.getBDMState() in ('Uninitialized', 'Offline'):
         TheBDM.registerWallet(walletFromDisk, isFresh=True, wait=False)
      else:
         self.main.newWalletList.append([walletFromDisk, True])
   
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
          
class WalletCreationPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(WalletCreationPage, self).__init__(wizard,
            NewWalletFrame(wizard, wizard.main, "Primary Wallet"))
      self.setTitle(tr("Step 1: Create Wallet"))
      self.setSubTitle(tr("""
            Create a new wallet for managing your funds.
            The name and description can be changed at any time."""))
      
   # override this method to implement validators
   def validatePage(self):
      result = True
      if self.pageFrame.getKdfSec() == -1:
         QMessageBox.critical(self, 'Invalid Target Compute Time', \
            'You entered Target Compute Time incorrectly.\n\nEnter: <Number> (ms, s)', QMessageBox.Ok)
         result = False
      elif self.pageFrame.getKdfBytes() == -1:
         QMessageBox.critical(self, 'Invalid Max Memory Usage', \
            'You entered Max Memory Usag incorrectly.\n\nnter: <Number> (kb, mb)', QMessageBox.Ok)
         result = False
      return result

class SetPassphrasePage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(SetPassphrasePage, self).__init__(wizard, 
               SetPassphraseFrame(wizard, wizard.main, "Set Passphrase", self.updateNextButton))
      self.setTitle(tr("Step 2: Set Passphrase"))
      self.updateNextButton()

   def updateNextButton(self):
      self.emit(SIGNAL("completeChanged()"))
   
   def isComplete(self):
      return self.pageFrame.checkPassphrase(False)
   
class VerifyPassphrasePage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(VerifyPassphrasePage, self).__init__(wizard, 
            VerifyPassphraseFrame(wizard, wizard.main, "Verify Passphrase"))
      self.passphrase = None
      self.setTitle(tr("Step 3: Verify Passphrase"))
   
   def setPassphrase(self, passphrase):
      self.passphrase = passphrase        
   
   def validatePage(self):
      result = self.passphrase == str(self.pageFrame.edtPasswd3.text())
      if not result:
         QMessageBox.critical(self, 'Invalid Passphrase', \
            'You entered your confirmation passphrase incorrectly!', QMessageBox.Ok)
      return result
      
class WalletBackupPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(WalletBackupPage, self).__init__(wizard,
                                WalletBackupFrame(wizard, wizard.main, "Backup Wallet"))
      self.myWizard = wizard
      self.setTitle(tr("Step 4: Backup Wallet"))
      self.setFinalPage(True)

class CreateWatchingOnlyWalletPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(CreateWatchingOnlyWalletPage, self).__init__(wizard,
                  WizardCreateWatchingOnlyWalletFrame(wizard, wizard.main, "Create Watching Only Wallet"))
      self.setTitle(tr("Step 5: Create Watching Only Wallet"))
      
############################### Offline TX Wizard ##############################
# Offline TX Wizard has these pages:
#     1. Create Transaction
#     2. Sign Transaction on Offline Computer
#     3. Broadcast Transaction
class TxWizard(ArmoryWizard):
   def __init__(self, parent, main, wlt, prefill=None, onlyOfflineWallets=False):
      super(TxWizard,self).__init__(parent, main)
      self.setWindowTitle(tr("Offline Transaction Wizard"))
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

      self.setButtonText(QWizard.NextButton, tr('Create Unsigned Transaction'))
      self.setButtonText(QWizard.CustomButton1, tr('Send!'))
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
         self.setButtonText(QWizard.NextButton, tr('Next'))
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
         self.setButtonText(QWizard.NextButton, tr('Create Unsigned Transaction'))

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
                                 "Create Transaction", wlt, prefill,
                                 selectWltCallback=self.updateOnSelectWallet,
                                 onlyOfflineWallets=onlyOfflineWallets))
      self.setTitle(tr("Step 1: Create Transaction"))
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
                  ReviewOfflineTxFrame(wizard, wizard.main, "Review Offline Transaction"))
      self.setTitle(tr("Step 2: Review Offline Transaction"))
      self.setFinalPage(True)
      
class SignBroadcastOfflineTxPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(SignBroadcastOfflineTxPage, self).__init__(wizard,
                  SignBroadcastOfflineTxFrame(wizard, wizard.main, "Sign/Broadcast Offline Transaction"))
      self.setTitle(tr("Step 3: Sign/Broadcast Offline Transaction"))      
