################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
from PyQt4.QtGui import QWizard, QWizardPage, QVBoxLayout, QListWidget, QLabel, QGridLayout, QVBoxLayout
from py2exe import resources
from PyQt4.QtCore import Qt
from armoryengine.ArmoryUtils import LOGINFO
from qtdialogs import DlgNewWallet
from Frames import NewWalletLayout

class WalletWizard(QWizard):
   """
   Wizard to create a new Wallet, back it up, and create a watching only version
   """

   def __init__(self, parent):
      QWizard.__init__(self, parent)
      self.parent = parent
      self.setWindowTitle(self.tr("Wallet Wizard"))
      
      self.walletCreationPage = WalletCreationPage(self)
      self.addPage(self.walletCreationPage)
      self.walletBackupPage = WalletBackupPage(self)
      self.addPage(self.walletBackupPage)
      self.walletWatchingOnlyPage = WalletWatchingOnlyPage(self)
      self.addPage(self.walletWatchingOnlyPage)
      self.setButtonLayout([QWizard.BackButton,
         QWizard.Stretch,
         QWizard.NextButton,
         QWizard.FinishButton])
      
class WalletCreationPage(QWizardPage):
   def __init__(self, wizard):
      QWizardPage.__init__(self)
      self.setTitle(self.tr("Step 1: Create Wallet"))
      self.setSubTitle(self.tr("Create wallet <Subtitle>"))
      self._wizard = wizard
      newWalletLayout = NewWalletLayout(wizard.parent, "Create Wallet")
      self.setLayout(newWalletLayout)
   def validatePage(self):
      return True
   
class WalletBackupPage(QWizardPage):
   def __init__(self, wizard):
      QWizardPage.__init__(self)
      self.setTitle(self.tr("Step 2: Backup Wallet"))
      self.setSubTitle(self.tr("Backup wallet <Subtitle>"))
      self._wizard = wizard
      
      #Names of the fields to complete
      gbox = QGridLayout(self)
      self.lblName = QLabel(self.tr("Backup Wallet Name (*):"))
      self.lblPlace = QLabel(self.tr("Backup Wallet Location (*):"))
      self.lblDescription = QLabel(self.tr("Backup Wallet Description:"))
      self.lblLicense = QLabel(self.tr("Backup Wallet License:"))
      self.lblVenvFolder = QLabel(self.tr("Backup Wallet Folder:"))
      gbox.addWidget(self.lblName, 0, 0, Qt.AlignLeft)
      gbox.addWidget(self.lblPlace, 1, 0, Qt.AlignLeft)
      gbox.addWidget(self.lblDescription, 2, 0, Qt.AlignLeft)
      gbox.addWidget(self.lblLicense, 3, 0, Qt.AlignLeft)
      gbox.addWidget(self.lblVenvFolder, 4, 0, Qt.AlignLeft)

   def validatePage(self):
      return True
         
class WalletWatchingOnlyPage(QWizardPage):
   def __init__(self, wizard):
      QWizardPage.__init__(self)
      self.setTitle(self.tr("Step 3: Watching Only Wallet"))
      self.setSubTitle(self.tr("Watching Only wallet <Subtitle>"))
      self._wizard = wizard
      
      #Names of the fields to complete
      gbox = QGridLayout(self)
      self.lblName = QLabel(self.tr("Watching Only Wallet Name (*):"))
      self.lblPlace = QLabel(self.tr("Watching Only Wallet Location (*):"))
      self.lblDescription = QLabel(self.tr("Watching Only Wallet Description:"))
      self.lblLicense = QLabel(self.tr("Watching Only Wallet License:"))
      self.lblVenvFolder = QLabel(self.tr("Watching Only Wallet Folder:"))
      gbox.addWidget(self.lblName, 0, 0, Qt.AlignLeft)
      gbox.addWidget(self.lblPlace, 1, 0, Qt.AlignLeft)
      gbox.addWidget(self.lblDescription, 2, 0, Qt.AlignLeft)
      gbox.addWidget(self.lblLicense, 3, 0, Qt.AlignLeft)
      gbox.addWidget(self.lblVenvFolder, 4, 0, Qt.AlignLeft)

   def validatePage(self):
      return True
