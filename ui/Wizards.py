################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
from PyQt4.QtGui import *
from py2exe import resources
from PyQt4.QtCore import Qt
from armoryengine.ArmoryUtils import LOGINFO, USE_TESTNET
from ui.Frames import NewWalletFrame
from qtdefines import GETFONT

# This class is intended to be an abstract Wizard class that
# will hold all of the functionality that is common to all 
# Wizards in Armory. 
class ArmoryWizard(QWizard):
   def __init__(self, parent, main=None):
      super(QWizard, self).__init__(parent)
      self.parent = parent
      self.main   = main
      self.setFont(GETFONT('var'))
      self.setWindowFlags(Qt.Window)

      if USE_TESTNET:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [TESTNET]')
         self.setWindowIcon(QIcon(':/armory_icon_green_32x32.png'))
      else:
         self.setWindowTitle('Armory - Bitcoin Wallet Management')
         self.setWindowIcon(QIcon(':/armory_icon_32x32.png'))

# This class is intended to be an abstract Wizard Page class that
# will hold all of the functionality that is common to all 
# Wizard pages in Armory. 
# The layout is QVBoxLayout and holds a single QFrame (self.pageFrame)
class ArmoryWizardPage(QWizardPage):
   def __init__(self, wizard, pageFrame):
      super(QWizardPage, self).__init__(wizard)
      self.pageFrame = pageFrame
      self.pageLayout = QVBoxLayout()
      self.pageLayout.addWidget(self.pageFrame)
      self.setLayout(self.pageLayout)

   def validatePage(self):
      return True

################################ Wallet Wizard ################################
# Wallet Wizard has these pages:
#     1. Create Wallet
#     2. Set Password
#     3. Verify Password
#     4. Unlock Wallet
#     5. Create Paper Backup
#     6. Create Watcing Only Wallet
#     7. Summary
class WalletWizard(ArmoryWizard):
   def __init__(self, parent, main=None):
      ArmoryWizard.__init__(self, parent, main)
      self.setWindowTitle(self.tr("Wallet Wizard"))
      
      # Page 1: Create Wallet
      self.walletCreationPage = WalletCreationPage(self)
      self.addPage(self.walletCreationPage)
      # Page 2: Set Password
      self.setPasswordPage = SetPasswordPage(self)
      self.addPage(self.setPasswordPage)
      # Page 3: Verify Password
      self.verifyPasswordPage = VerifyPasswordPage(self)
      self.addPage(self.verifyPasswordPage)
      # Page 4: Unlock Wallet
      self.unlockWalletPage = UnlockWalletPage(self)
      self.addPage(self.unlockWalletPage)      
      # Page 5: Create Paper Backup
      self.walletBackupPage = WalletBackupPage(self)
      self.addPage(self.walletBackupPage)
      # Page 6: Create Watching Only Wallet
      self.createWatchingOnlyWalletPage = CreateWatchingOnlyWalletPage(self)
      self.addPage(self.createWatchingOnlyWalletPage)
      # Page 7: Summary
      self.summaryPage = SummaryPage(self)
      self.addPage(self.summaryPage)

      self.setButtonLayout([QWizard.BackButton,
         QWizard.Stretch,
         QWizard.NextButton,
         QWizard.FinishButton])



class WalletCreationPage(ArmoryWizardPage):
   def __init__(self, wizard):
      ArmoryWizardPage.__init__(self, wizard, NewWalletFrame(wizard.parent, "Create Wallet"))
      self.setTitle(self.tr("Step 1: Create Wallet"))
      self.setSubTitle(self.tr("""
            Create a new wallet for managing your funds.
            The name and description can be changed at any time."""))

class SetPasswordPage(ArmoryWizardPage):
   def __init__(self, wizard):
      ArmoryWizardPage.__init__(self, wizard, QFrame())
      self.setTitle(self.tr("Step 2: Set Password"))
      self.setSubTitle(self.tr("Set Password <Subtitle>"))

class VerifyPasswordPage(ArmoryWizardPage):
   def __init__(self, wizard):
      ArmoryWizardPage.__init__(self, wizard, QFrame())
      self.setTitle(self.tr("Step 3: Verify Password"))
      self.setSubTitle(self.tr("Verify Password <Subtitle>"))


class UnlockWalletPage(ArmoryWizardPage):
   def __init__(self, wizard):
      ArmoryWizardPage.__init__(self, wizard, QFrame())
      self.setTitle(self.tr("Step 4: Unlock Wallet"))
      self.setSubTitle(self.tr('I know you have entered your password 3 times already .'
                               'Now it is really needed to unlock the wallet to create a backup.'))
                       
class WalletBackupPage(ArmoryWizardPage):
   def __init__(self, wizard):
      ArmoryWizardPage.__init__(self, wizard, QFrame())
      self.setTitle(self.tr("Step 5: Backup Wallet"))
      self.setSubTitle(self.tr("Backup wallet <Subtitle>"))
      self._wizard = wizard

class CreateWatchingOnlyWalletPage(ArmoryWizardPage):
   def __init__(self, wizard):
      ArmoryWizardPage.__init__(self, wizard, QFrame())
      self.setTitle(self.tr("Step 6: Watching Only Wallet"))
      self.setSubTitle(self.tr("Watching Only wallet <Subtitle>"))
      self._wizard = wizard
   
class SummaryPage(ArmoryWizardPage):
   def __init__(self, wizard):
      ArmoryWizardPage.__init__(self, wizard, QFrame())
      self.setTitle(self.tr("Step 7: Wallet Creation Summary"))
      self.setSubTitle(self.tr("Wallet Creation Summary <Subtitle>"))
