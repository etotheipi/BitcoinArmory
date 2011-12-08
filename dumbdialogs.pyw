import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class DlgNewWallet(QDialog):

   def __init__(self, parent=None, defaultNewWallet=True):
      super(DlgNewWallet, self).__init__(parent)



      # Import Wallet File section
      """
      self.chkImportWlt = self.QCheckBox('Import existing Armory wallet')
      self.chkImportWlt.setChecked(not defaultNewWallet)

      self.importFrame = QFrame()
      self.importFrame.setFrameShape(QFrame.NoFrame)
      importLayout = QHBoxLayout()
      importLayout.addWidget(QLabel('File to import:', 0, 0)
      importLayout.addWidget(self.fileLineEdit, 0, 1)
      importLayout.addWidget(self.browseButton, 0, 2)
      self.importFrame.setLayout(importLayout)
      self.importFrame.setEnabled(defaultNewWallet)

      self.chkImportWlt.conn
      self.connect(self.chkImportWlt, SIGNAL('clicked()'),
                   self.importFrame,  SLOT('setEnabled(bool)'))

      """

      # Options for creating a new wallet
      lblDlgDescr = QLabel('Create a new wallet for managing your funds.')
      lblDlgDescr.setWordWrap(True)
      #self.chkNewWallet = QCheckBox('Create a new wallet to hold your funds')
      #self.chkNewWallet.setChecked(defaultNewWallet)

      self.edtName = QLineEdit()
      self.edtName.setMaxLength(32)
      lblName = QLabel("New wallet &name:")
      lblName.setBuddy(self.edtName)

      self.edtDescr = QTextEdit()
      #self.edtDescr.setMaxLength(256)
      lblDescr = QLabel("New wallet &description:")
      lblDescr.setBuddy(self.edtDescr)

      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)

      
      # Advanced Encryption Options
      #lblComputeDescr = QLabel('When this wallet is created, BitcoinArmory will test '
                               #'your computer for the most time- and memory-intense '
                               #'encryption parameters that can be performed within '
                               #'0.25 seconds.  Below, you can change the the target '
                               #'compute time, or put a maximum limit on the memory '
                               #'requirement of the encryption parameters.  Higher '
                               #'time values make it more difficult for an attacker '
                               #'to brute-force-guess your passphrase, but also more '
                               #'time for you to unlock your wallet.  Higher memory '
                               #'usage will decrease the benefit of GPU-acceleration '
                               #'in such an attack (values above 4 MB are likely to '
                               #'render GPUs completely useless for passphrase guessing.')
      lblComputeDescr = QLabel('Bitcoin Armory will test your system\'s speed to '
                               'determine encryption settings that use as much memory '
                               'as possible within 0.25 seconds (up to 32 MB). '
                               'You can modify the defaults below.  '
                               'By increasing the memory requirement, you are reducing '
                               'the effectiveness of GPU-acceleration to brute-force '
                               'your passphrase.')
      lblComputeDescr.setWordWrap(True)
      
      # Set maximum compute time
      self.edtComputeTime = QLineEdit()
      self.edtComputeTime.setText('250 ms')
      self.edtComputeTime.setMaxLength(12)
      lblComputeTime = QLabel('Decryption compute &time (sec):\n' 
                              '(actual compute time will between T/2 and T)')
      lblComputeTime.setBuddy(self.edtComputeTime)


      # Set maximum memory usage
      self.edtComputeMem = QLineEdit()
      self.edtComputeMem.setText('32.0 MB')
      self.edtComputeMem.setMaxLength(12)
      lblComputeMem  = QLabel('Maximum &memory usage:')
      lblComputeMem.setBuddy(self.edtComputeMem)

      self.chkForkOnline = QCheckBox('Create an "&online" copy of this wallet')
      lblForkOnline = QLabel('"Online" wallets are watching-only wallets that '
                             'contains no private key data.  An "online" wallet '
                             'can be used for generating receiving addresses '
                             'and verifying incoming transactions, but cannot be used '
                             'to spend any of the money in the wallet.')
      lblForkOnline.setWordWrap(True)
      lblForkOnline.setBuddy(self.chkForkOnline)
      # Fork watching-only wallet


      cryptoLayout = QGridLayout()
      cryptoLayout.addWidget(lblComputeDescr,     0, 0, 1, 2)
      cryptoLayout.addWidget(lblComputeTime,      1, 0, 1, 1)
      cryptoLayout.addWidget(lblComputeMem,       2, 0, 1, 1)
      cryptoLayout.addWidget(self.edtComputeTime, 1, 1, 1, 1)
      cryptoLayout.addWidget(self.edtComputeMem,  2, 1, 1, 1)
      cryptoLayout.addWidget(self.chkForkOnline,  3, 0, 1, 1)
      cryptoLayout.addWidget(lblForkOnline,       4, 0, 1, 3)

      self.cryptoFrame = QFrame()
      self.cryptoFrame.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
      self.cryptoFrame.setLayout(cryptoLayout)
      self.cryptoFrame.setVisible(False)

      #self.chkWatchOnly = QCheckBox("Make this a watching-only wallet\n(no private key data)")
      self.chkUseCrypto = QCheckBox("Use wallet &encryption")
      self.chkUseCrypto.setChecked(True)

      self.chkAdvCrypto = QCheckBox('Set advanced encryption options')
      self.chkAdvCrypto.setChecked(False)
      self.connect(self.chkAdvCrypto, SIGNAL('toggled(bool)'), \
                   self.cryptoFrame, SLOT('setVisible(bool)'))



      
      masterLayout = QGridLayout()
      masterLayout.addWidget(lblDlgDescr,       1, 0, 1, 3)
      masterLayout.addWidget(lblName,           2, 0)
      masterLayout.addWidget(self.edtName,      2, 1, 1, 2)
      masterLayout.addWidget(lblDescr,          3, 0)
      masterLayout.addWidget(self.edtDescr,     3, 1, 2, 2)
      #masterLayout.addWidget(self.chkWatchOnly, 4, 0)
      masterLayout.addWidget(self.chkUseCrypto, 5, 0)
      masterLayout.addWidget(self.chkAdvCrypto, 6, 0)
      masterLayout.addWidget(self.cryptoFrame,  7, 0, 3, 3)
     

      self.setLayout(masterLayout)

      self.layout().setSizeConstraint(QLayout.SetFixedSize)


      #self.connect(okButton, SIGNAL("clicked()"),
                   #self, SLOT("accept()"))
      #self.connect(cancelButton, SIGNAL("clicked()"),
                   #self, SLOT("reject()"))

      self.connect(self.chkUseCrypto, SIGNAL("clicked()"), \
                   self.cryptoFrame, SLOT("setEnabled(bool)"))

      #self.connect(findFileButton, SIGNAL("clicked()"),
                   #self.findWalletFile)

      self.setWindowTitle('Bitcoin Armory: Create/Import wallet')
      self.setWindowIcon(QIcon('icons/armory_logo_32x32.png'))



   #def findWalletFile(self):
      #formats = ['*.wallet', 'All files']
      #dlg = QFileDialog(self, 'Find wallet File', ARMORY_HOME_DIR)
      #dlg.setFileMode(QFileDialog.ExistingFile)
      #dlg.setNameFilters(['Wallet files (*.wallet)', 'All Files (*)'])
      ##dlg.setNameFilters(['Wallet files (*.wallet);; All Files (*.*)')
      #if dlg.exec_() == 1:
         #self. dlg.selectedFiles().first()


class DlgChangePassphrase(QDialog):
   def __init__(self, parent=None, firstTime=True):
      super(DlgChangePassphrase, self).__init__(parent)


      layout = QGridLayout()
      if firstTime:
         lblDlgDescr = QLabel("Please enter an passphrase for wallet encryption")
         layout.addWidget(lblDlgDescr, 0, 0)
      else:
         lblDlgDescr = QLabel("Change your wallet encryption passphrase")
         layout.addWidget(lblDlgDescr, 0, 0)
         self.edtPasswdOrig = QLineEdit()
         self.edtPasswdOrig.SetEchoMode(QLineEdit.Password)
         lblCurrPasswd = QLabel('Current Passphrase:')
         layout.addWidget(lblCurrPasswd,       1, 0)
         layout.addWidget(self.edtPasswdOrig,  1, 1)



      lblPwd1 = QLabel("New Passphrase:")
      lblPwd2 = QLabel("Again:")
      self.edtPasswd1 = QLineEdit()
      self.edtPasswd2 = QLineEdit()
      self.edtPasswd1.setEchoMode(QLineEdit.Password)
      self.edtPasswd2.setEchoMode(QLineEdit.Password)

      layout.addWidget(lblPwd1, 2,0)
      layout.addWidget(lblPwd2, 3,0)
      layout.addWidget(self.edtPasswd1, 2,1)
      layout.addWidget(self.edtPasswd2, 3,1)

      
      self.lblMatches = QLabel(' '*20)
      self.lblMatches.setTextFormat(Qt.RichText)
      layout.addWidget(self.lblMatches, 4,1)

      self.btnAccept = QPushButton("Accept")
      self.btnCancel = QPushButton("Cancel")
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)
      layout.addWidget(buttonBox, 5, 0, 1, 2)


      self.setLayout(layout)

      self.connect(self.edtPasswd1, SIGNAL('textChanged(QString)'), \
                   self.checkPassphrase)
      self.connect(self.edtPasswd2, SIGNAL('textChanged(QString)'), \
                   self.checkPassphrase)

      self.connect(self.btnAccept, SIGNAL('clicked()'), \
                   self.checkPassphraseFinal)

      self.connect(self.btnCancel, SIGNAL('clicked()'), \
                   self,           SLOT('reject()'))



   def checkPassphrase(self):
      p1 = self.edtPasswd1.text()
      p2 = self.edtPasswd2.text()
      if not p1==p2:
         self.lblMatches.setText('<font color="red"><b>Passphrases do not match!</b></font>')
         return False
      if len(p1)<6:
         self.lblMatches.setText('<font color="red"><b>Passphrase is too short!</b></font>')
         return False
      self.lblMatches.setText('<font color="green"><b>Passphrases match!</b></font>')
      return True
      

   def checkPassphraseFinal(self):
      if self.checkPassphrase():
         self.accept()


class DlgDispWltProperties(QDialog):
   def __init__(self, parent=None):
      super(DlgDispWltProperties, self).__init__(parent)




if __name__=='__main__':
   app = QApplication(sys.argv)
   app.setApplicationName("DumbDialogs")

   #form = DlgNewWallet(defaultNewWallet=True)
   form = DlgChangePassphrase(firstTime=True)

   form.show()
   app.exec_()





