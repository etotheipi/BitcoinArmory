################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

from PyQt4.Qt import * #@UnusedWildImport
from PyQt4.QtGui import * #@UnusedWildImport
from armoryengine.ArmoryUtils import LOGINFO, USE_TESTNET, WalletExistsError,\
   LOGWARN
from ui.Frames import NewWalletFrame, SetPassphraseFrame, VerifyPassphraseFrame,\
   WalletBackupFrame, WizardCreateWatchingOnlyWalletFrame
from qtdefines import GETFONT, tr
from armoryengine.PyBtcWallet import PyBtcWallet
from CppBlockUtils import SecureBinaryData
from armoryengine.BDM import TheBDM
from qtdialogs import DlgExecLongProcess

# This class is intended to be an abstract Wizard class that
# will hold all of the functionality that is common to all 
# Wizards in Armory. 
class ArmoryWizard(QWizard):
   def __init__(self, parent, main):
      super(QWizard, self).__init__(parent)
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
#     4. Unlock Wallet
#     5. Create Paper Backup
#     6. Create Watcing Only Wallet
#     7. Summary
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
      
      # Page 5: Create Watching Only Wallet
      self.createWatchingOnlyWalletPage = CreateWatchingOnlyWalletPage(self)
      self.addPage(self.createWatchingOnlyWalletPage)

      self.setButtonLayout([QWizard.BackButton,
                            QWizard.Stretch,
                            QWizard.NextButton,
                            QWizard.FinishButton])

   def initializePage(self, *args, **kwargs):

      if self.currentPage() == self.verifyPassphrasePage:
         self.verifyPassphrasePage.setPassphrase(
               self.setPassphrasePage.pageFrame.getPassphrase())
      elif self.currentPage() == self.createWatchingOnlyWalletPage:
         self.createWatchingOnlyWalletPage.pageFrame.setWallet(self.newWallet)
         
      if self.currentPage() == self.walletBackupPage:
         self.createNewWalletFromWizard()
         self.newWallet.unlock(securePassphrase=
                  SecureBinaryData(self.setPassphrasePage.pageFrame.getPassphrase()))
         
         self.walletBackupPage.pageFrame.setWallet(self.newWallet)
         
         # Only hide the back button on wallet backup page  
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
         reply = QMessageBox.question(self, 'Wallet Backup Warning', \
               'You have not made a backup for your new wallet. Backing up your wallet ' +
               'is critical securing  your bitcoins. If you do not backup your wallet now ' +
               'you may do it from the wallet screen later.\n\n\t' +
               'Are you sure that you want to leave this wizard without backing up your wallet?', \
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
                     doRegisterWithBDM=False)
      self.newWallet.unlock(securePassphrase=
               SecureBinaryData(self.setPassphrasePage.pageFrame.getPassphrase()))
      # We always want to fill the address pool, right away.  
      fillpool = lambda: self.newWallet.fillAddressPool(doRegister=False)
      DlgExecLongProcess(fillpool, 'Creating Wallet...', self, self).exec_()

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
      if self.currentPage() == self.createWatchingOnlyWalletPage:
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
            NewWalletFrame(wizard, wizard.main, "Create Wallet"))
      self.setTitle(tr("Step 1: Create Wallet"))
      self.setSubTitle(tr("""
            Create a new wallet for managing your funds.
            The name and description can be changed at any time."""))

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
      self.setFinalPage(True)

class CreateWatchingOnlyWalletPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(CreateWatchingOnlyWalletPage, self).__init__(wizard,
                  WizardCreateWatchingOnlyWalletFrame(wizard, wizard.main, "Create Watching Only Wallet"))
      self.setTitle(tr("Step 5: Create Watching Only Wallet"))
      
