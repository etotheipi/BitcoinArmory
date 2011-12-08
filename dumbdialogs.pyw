import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

try:
   from btcarmoryengine import *
except ImportError:
   print '***btcarmoryengine not available!'

################################################################################
def createToolTipObject(tiptext, iconSz=2):
   lbl = QLabel('<font size=%d color="blue"><u>(?)</u></font>' % iconSz)
   lbl.setToolTip('<u></u>' + tiptext)
   return lbl

################################################################################
class DlgNewWallet(QDialog):

   def __init__(self, parent=None):
      super(DlgNewWallet, self).__init__(parent)

      # Options for creating a new wallet
      lblDlgDescr = QLabel('Create a new wallet for managing your funds.\n')
      lblDlgDescr.setWordWrap(True)

      self.edtName = QLineEdit()
      self.edtName.setMaxLength(32)
      lblName = QLabel("Wallet &name:")
      lblName.setBuddy(self.edtName)


      self.edtDescr = QTextEdit()
      self.edtDescr.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
      lblDescr = QLabel("Wallet &description:")
      lblDescr.setBuddy(self.edtDescr)

      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)


      
      # Advanced Encryption Options
      lblComputeDescr = QLabel('Armory will test your system\'s speed to determine the most '
                               'challenging encryption settings that can be performed '
                               'in a given amount of time.  High settings make it extremely difficult '
                               'for someone to guess your passphrase. This is used for all '
                               'encrypted wallets, but the default parameters can be changed below.\n')
      lblComputeDescr.setWordWrap(True)
      timeDescrTip = createToolTipObject(
                               'This is the amount of time it will take for your computer '
                               'to unlock your wallet after you enter your passphrase. '
                               '(the actual time will be between T/2 and T).  ')
      
      
      # Set maximum compute time
      self.edtComputeTime = QLineEdit()
      self.edtComputeTime.setText('250 ms')
      self.edtComputeTime.setMaxLength(12)
      lblComputeTime = QLabel('Target compute &time (s, ms):')
      memDescrTip = createToolTipObject(
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

      self.chkForkOnline = QCheckBox('Create an "&online" copy of this wallet')

      onlineToolTip = createToolTipObject(
                             'An "online" wallet is a copy of your primary wallet, but '
                             'without any sensitive data that would allow an attacker to '
                             'obtain access to your funds.  An "online" wallet can '
                             'generate new addresses and verify incoming payments '
                             'but cannot be used to spend any of the funds.')
      # Fork watching-only wallet


      cryptoLayout = QGridLayout()
      cryptoLayout.addWidget(lblComputeDescr,     0, 0, 1, 3)
      cryptoLayout.addWidget(lblComputeTime,      1, 0, 1, 1)
      cryptoLayout.addWidget(lblComputeMem,       2, 0, 1, 1)
      cryptoLayout.addWidget(self.edtComputeTime, 1, 1, 1, 1)
      cryptoLayout.addWidget(timeDescrTip,        1, 3, 1, 1)
      cryptoLayout.addWidget(self.edtComputeMem,  2, 1, 1, 1)
      cryptoLayout.addWidget(memDescrTip,         2, 3, 1, 1)
      cryptoLayout.addWidget(self.chkForkOnline,  3, 0, 1, 1)
      cryptoLayout.addWidget(onlineToolTip,       3, 1, 1, 1)

      self.cryptoFrame = QFrame()
      self.cryptoFrame.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
      self.cryptoFrame.setLayout(cryptoLayout)
      self.cryptoFrame.setVisible(False)

      #self.chkWatchOnly = QCheckBox("Make this a watching-only wallet\n(no private key data)")
      self.chkUseCrypto = QCheckBox("Use wallet &encryption")
      self.chkUseCrypto.setChecked(True)
      usecryptoTooltip = createToolTipObject(
                                 'Encryption prevents anyone who accesses your computer '
                                 'from being able to spend your funds, but does require '
                                 'typing in a passphrase before you can send money. '
                                 'You can choose to encrypt your wallet at a later time '
                                 'through the wallet options by double clicking the wallet '
                                 'on the dashboard.')


      
      self.btnAccept    = QPushButton("Accept")
      self.btnCancel    = QPushButton("Cancel")
      self.btnAdvCrypto = QPushButton("Adv. Encrypt Options>>>")
      self.btnAdvCrypto.setCheckable(True)
      self.btnbox = QDialogButtonBox()
      self.btnbox.addButton(self.btnAdvCrypto, QDialogButtonBox.ActionRole)
      self.btnbox.addButton(self.btnCancel,    QDialogButtonBox.RejectRole)
      self.btnbox.addButton(self.btnAccept,    QDialogButtonBox.AcceptRole)

      self.connect(self.btnAdvCrypto, SIGNAL('toggled(bool)'), \
                   self.cryptoFrame,  SLOT('setVisible(bool)'))
      self.connect(self.btnAccept,    SIGNAL('clicked()'), \
                   self.verifyInputsBeforeAccept)
      self.connect(self.btnCancel,    SIGNAL('clicked()'), \
                   self,              SLOT('reject()'))


      self.btnImportWlt = QPushButton("Import wallet...")
      self.connect( self.btnImportWlt, SIGNAL("clicked()"), \
                    self.getImportWltPath)
      
      masterLayout = QGridLayout()
      masterLayout.addWidget(lblDlgDescr,       1, 0, 1, 2)
      masterLayout.addWidget(self.btnImportWlt, 1, 2, 1, 1)
      masterLayout.addWidget(lblName,           2, 0, 1, 1)
      masterLayout.addWidget(self.edtName,      2, 1, 1, 2)
      masterLayout.addWidget(lblDescr,          3, 0, 1, 1)
      masterLayout.addWidget(self.edtDescr,     3, 1, 2, 2)
      masterLayout.addWidget(self.chkUseCrypto, 5, 0, 1, 1)
      masterLayout.addWidget(usecryptoTooltip,  5, 1, 1, 1)
      masterLayout.addWidget(self.cryptoFrame,  7, 0, 3, 3)
   
      masterLayout.addWidget(self.btnbox,      10, 0, 1, 2)
     
      self.setLayout(masterLayout)

      self.layout().setSizeConstraint(QLayout.SetFixedSize)

      self.connect(self.chkUseCrypto, SIGNAL("clicked()"), \
                   self.cryptoFrame, SLOT("setEnabled(bool)"))

      self.setWindowTitle('Bitcoin Armory: Create/Import wallet')
      self.setWindowIcon(QIcon('icons/armory_logo_32x32.png'))



   def verifyInputsBeforeAccept(self):
      wltName  = self.edtName.text()
      wltDescr = self.edtDescr.toPlainText()
      if len(wltName)<1:
         QMessageBox.warning(self, 'Invalid wallet name', \
                  'You must enter a name for this wallet, up to 32 characters.', \
                  QMessageBox.Ok)
         return False
         
      if len(wltDescr)>256:
         reply = QMessageBox.warning(self, 'Input too long', \
                  'The wallet description is limited to 256 characters.  Only the first '
                  '256 characters will be used.', \
                  QMessageBox.Ok | QMessageBox.Cancel)
         if reply==QMessageBox.Ok:
            self.edtDescr.setText( wltDescr[:256])
            self.accept()
         else:
            return False
      self.accept()
            
            
   def getImportWltPath(self):
      self.importFile = QFileDialog.getOpenFileName(self, 'Import Wallet File', \
          ARMORY_HOME_DIR, 'Wallet files (*.wallet);; All files (*)') 
      if self.importFile:
         print self.importFile
         self.accept()
      


"""
################################################################################
class DlgImportWallet(QDialog):
   def __init__(self, parent=None):
      super(DlgImportWallet, self).__init__(parent)
   
      lblPath = QLabel("Path to wallet file:")
      self.edtPath = QLineEdit()
      self.btnBrowse = QPushButton("Browse...")

      layout = QHBoxLayout()
      layout.addWidget(lblPath, 0)
      layout.addWidget(self.edtPath, 1)
      layout.addWidget(self.btnBrowse, 2)
      self.connect(self.btnBrowse, SIGNAL("clicked()"), \
                   self.openFileDialog)
      self.setLayout(layout)

      self.setWindowTitle('Import wallet file')
      self.setWindowIcon(QIcon('icons/armory_logo_32x32.png'))

   def openFileDialog(self):
      pass
"""



################################################################################
class DlgChangePassphrase(QDialog):
   def __init__(self, parent=None, noPrevEncrypt=True):
      super(DlgChangePassphrase, self).__init__(parent)


      layout = QGridLayout()
      if noPrevEncrypt:
         lblDlgDescr = QLabel('Please enter an passphrase for wallet encryption.\n\n'
                              'A good passphrase consists of at least 8 or more\n'
                              'random letters, or 5 or more random words.\n')
         lblDlgDescr.setWordWrap(True)
         layout.addWidget(lblDlgDescr, 0, 0, 1, 2)
      else:
         lblDlgDescr = QLabel("Change your wallet encryption passphrase")
         layout.addWidget(lblDlgDescr, 0, 0, 1, 2)
         self.edtPasswdOrig = QLineEdit()
         self.edtPasswdOrig.setEchoMode(QLineEdit.Password)
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

      if noPrevEncrypt:
         self.setWindowTitle("Set Encryption Passphrase")
      else:
         self.setWindowTitle("Change Encryption Passphrase")

      self.setWindowIcon(QIcon('icons/armory_logo_32x32.png'))

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
         reply = QMessageBox.warning(self,  \
            'WARNING!', \
            '!!!  DO NOT FORGET YOUR PASSPHRASE  !!!\n\n'
            'Bitcoin Armory wallet encryption is designed to be extremely difficult to '
            'crack, even with GPU-acceleration.  No one can help you recover your coins '
            'if you forget your passphrase, not even the developers of this software. '
            'If you are inclined to forget your passphrase, please write it down and '
            'store it in a secure location.\n\nAre you sure you will remember you passphrase?', \
            QMessageBox.Yes | QMessageBox.No)

         if reply == QMessageBox.Yes:
            self.accept()


class DlgDispWltProperties(QDialog):
   def __init__(self, parent=None):
      super(DlgDispWltProperties, self).__init__(parent)




if __name__=='__main__':
   app = QApplication(sys.argv)
   app.setApplicationName("DumbDialogs")

   form = DlgNewWallet()
   #form = DlgChangePassphrase(noPrevEncrypt=True)

   form.show()
   app.exec_()





