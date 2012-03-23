import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qtdefines import *

from armoryengine import *
from armorymodels import *

MIN_PASSWD_WIDTH = lambda obj: tightSizeStr(obj, '*'*16)[0]


################################################################################
class DlgUnlockWallet(QDialog):
   def __init__(self, wlt, parent=None, main=None, unlockMsg='Unlock Wallet'):
      super(DlgUnlockWallet, self).__init__(parent)

      self.wlt = wlt
      self.parent = parent
      self.main   = main

      lblDescr  = QLabel("Enter your passphrase to unlock this wallet")
      lblPasswd = QLabel("Passphrase:")
      self.edtPasswd = QLineEdit()
      self.edtPasswd.setEchoMode(QLineEdit.Password)
      self.edtPasswd.setMinimumWidth(MIN_PASSWD_WIDTH(self))
      self.edtPasswd.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

      self.btnAccept = QPushButton("Unlock")
      self.btnCancel = QPushButton("Cancel")
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.acceptPassphrase)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      layout = QGridLayout()
      layout.addWidget(lblDescr,       1, 0, 1, 2)
      layout.addWidget(lblPasswd,      2, 0, 1, 1)
      layout.addWidget(self.edtPasswd, 2, 1, 1, 1)
      layout.addWidget(buttonBox,      3, 1, 1, 2)

      self.setLayout(layout)
      self.setWindowTitle(unlockMsg + ' - ' + wlt.uniqueIDB58)

   def acceptPassphrase(self):
      securePwd = SecureBinaryData(str(self.edtPasswd.text()))
      try:
         self.wlt.unlock(securePassphrase=securePwd)
         self.accept()
      except PassphraseError:
         QMessageBox.critical(self, 'Invalid Passphrase', \
           'That passphrase is not correct!', QMessageBox.Ok)
         self.edtPasswd.setText('')
         return

      
################################################################################
class DlgGenericGetPassword(QDialog):
   def __init__(self, descriptionStr, parent=None, main=None):
      super(DlgGenericGetPassword, self).__init__(parent)

      self.parent = parent
      self.main   = main

      lblDescr  = QRichLabel(descriptionStr)
      lblPasswd = QRichLabel("Password:")
      self.edtPasswd = QLineEdit()
      self.edtPasswd.setEchoMode(QLineEdit.Password)
      self.edtPasswd.setMinimumWidth(MIN_PASSWD_WIDTH(self))
      self.edtPasswd.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

      self.btnAccept = QPushButton("OK")
      self.btnCancel = QPushButton("Cancel")
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.accept)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      layout = QGridLayout()
      layout.addWidget(lblDescr,       1, 0, 1, 2)
      layout.addWidget(lblPasswd,      2, 0, 1, 1)
      layout.addWidget(self.edtPasswd, 2, 1, 1, 1)
      layout.addWidget(buttonBox,      3, 1, 1, 2)

      self.setLayout(layout)
      self.setWindowTitle('Enter Password')
      self.setWindowIcon(QIcon(self.main.iconfile))
   

################################################################################
class DlgNewWallet(QDialog):

   def __init__(self, parent=None, main=None, initLabel=''):
      super(DlgNewWallet, self).__init__(parent)

      self.parent = parent
      self.main   = main

      self.selectedImport = False

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
      lblComputeDescr = QLabel('Armory will test your system\'s speed to determine the most '
                               'challenging encryption settings that can be performed '
                               'in a given amount of time.  High settings make it much harder '
                               'for someone to guess your passphrase.  This is used for all '
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

      self.edtComputeTime.setMaximumWidth( tightSizeNChar(self, 20)[0] )
      self.edtComputeMem.setMaximumWidth( tightSizeNChar(self, 20)[0] )

      #self.chkForkOnline = QCheckBox('Create an "&online" copy of this wallet')

      #onlineToolTip = createToolTipObject(
                             #'An "online" wallet is a copy of your primary wallet, but '
                             #'without any sensitive data that would allow an attacker to '
                             #'obtain access to your funds.  An "online" wallet can '
                             #'generate new addresses and verify incoming payments '
                             #'but cannot be used to spend any of the funds.')
      # Fork watching-only wallet


      cryptoLayout = QGridLayout()
      cryptoLayout.addWidget(lblComputeDescr,     0, 0,  1, 3)

      cryptoLayout.addWidget(timeDescrTip,        1, 0,  1, 1)
      cryptoLayout.addWidget(lblComputeTime,      1, 1,  1, 1)
      cryptoLayout.addWidget(self.edtComputeTime, 1, 2,  1, 1)

      cryptoLayout.addWidget(memDescrTip,         2, 0,  1, 1)
      cryptoLayout.addWidget(lblComputeMem,       2, 1,  1, 1)
      cryptoLayout.addWidget(self.edtComputeMem,  2, 2,  1, 1)
      #cryptoLayout.addWidget(self.chkForkOnline,  3, 0, 1, 1)
      #cryptoLayout.addWidget(onlineToolTip,       3, 1, 1, 1)

      self.cryptoFrame = QFrame()
      self.cryptoFrame.setFrameStyle(STYLE_SUNKEN)
      self.cryptoFrame.setLayout(cryptoLayout)
      self.cryptoFrame.setVisible(False)

      self.chkUseCrypto  = QCheckBox("Use wallet &encryption")
      self.chkUseCrypto.setChecked(True)
      usecryptoTooltip = createToolTipObject(
                                 'Encryption prevents anyone who accesses your computer '
                                 'or wallet file from being able to spend your money, as  '
                                 'long as they do not have the passphrase.'
                                 'You can choose to encrypt your wallet at a later time '
                                 'through the wallet properties dialog by double clicking '
                                 'the wallet on the dashboard.')

      # For a new wallet, the user may want to print out a paper backup
      self.chkPrintPaper = QCheckBox("Print a paper-backup of this wallet")
      paperBackupTooltip = createToolTipObject(
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
                    self.importButtonClicked)
      
      masterLayout = QGridLayout()
      masterLayout.addWidget(lblDlgDescr,        1, 0, 1, 2)
      #masterLayout.addWidget(self.btnImportWlt,  1, 2, 1, 1)
      masterLayout.addWidget(lblName,            2, 0, 1, 1)
      masterLayout.addWidget(self.edtName,       2, 1, 1, 2)
      masterLayout.addWidget(lblDescr,           3, 0, 1, 2)
      masterLayout.addWidget(self.edtDescr,      3, 1, 2, 2)
      masterLayout.addWidget(self.chkUseCrypto,  5, 0, 1, 1)
      masterLayout.addWidget(usecryptoTooltip,   5, 1, 1, 1)
      masterLayout.addWidget(self.chkPrintPaper, 6, 0, 1, 1)
      masterLayout.addWidget(paperBackupTooltip, 6, 1, 1, 1)
      masterLayout.addWidget(self.cryptoFrame,   8, 0, 3, 3)
   
      masterLayout.addWidget(self.btnbox,       11, 0, 1, 2)

      masterLayout.setVerticalSpacing(5)
     
      self.setLayout(masterLayout)

      self.layout().setSizeConstraint(QLayout.SetFixedSize)

      self.connect(self.chkUseCrypto, SIGNAL("clicked()"), \
                   self.cryptoFrame,  SLOT("setEnabled(bool)"))

      self.setWindowTitle('Create/Import Armory wallet')
      self.setWindowIcon(QIcon( self.main.iconfile))



   def importButtonClicked(self):
      self.selectedImport = True
      self.accept()

   def verifyInputsBeforeAccept(self):

      ### Confirm that the name and descr are within size limits #######
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
         else:
            return False

      ### Check that the KDF inputs are well-formed ####################
      try:
         kdfT, kdfUnit = str(self.edtComputeTime.text()).strip().split(' ') 
         if kdfUnit.lower()=='ms':
            self.kdfSec = float(kdfT)/1000.
         elif kdfUnit.lower() in ('s', 'sec', 'seconds'):
            self.kdfSec = float(kdfT)

         kdfM, kdfUnit = str(self.edtComputeMem.text()).split(' ')
         if kdfUnit.lower()=='mb':
            self.kdfBytes = round(float(kdfM))*(1024.0**2) 
         if kdfUnit.lower()=='kb':
            self.kdfBytes = round(float(kdfM))*(1024.0)

         print 'KDF takes', self.kdfSec, 'sec and', self.kdfBytes, 'bytes'
      except:
         QMessageBox.critical(self, 'Invalid KDF Parameters', \
            'Please specify time with units, such as '
            '"250 ms" or "2.1 s".  Specify memory as kB or MB, such as '
            '"32 MB" or "256 kB". ', QMessageBox.Ok)
         return False
         
      
      self.accept()
            
            
   def getImportWltPath(self):
      self.importFile = QFileDialog.getOpenFileName(self, 'Import Wallet File', \
          ARMORY_HOME_DIR, 'Wallet files (*.wallet);; All files (*)') 
      if self.importFile:
         print self.importFile
         self.accept()
      



################################################################################
class DlgChangePassphrase(QDialog):
   def __init__(self, parent=None, main=None, noPrevEncrypt=True):
      super(DlgChangePassphrase, self).__init__(parent)

      self.parent = parent
      self.main   = main


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
         self.edtPasswdOrig.setMinimumWidth(MIN_PASSWD_WIDTH(self))
         lblCurrPasswd = QLabel('Current Passphrase:')
         layout.addWidget(lblCurrPasswd,       1, 0)
         layout.addWidget(self.edtPasswdOrig,  1, 1)



      lblPwd1 = QLabel("New Passphrase:")
      self.edtPasswd1 = QLineEdit()
      self.edtPasswd1.setEchoMode(QLineEdit.Password)
      self.edtPasswd1.setMinimumWidth(MIN_PASSWD_WIDTH(self))

      lblPwd2 = QLabel("Again:")
      self.edtPasswd2 = QLineEdit()
      self.edtPasswd2.setEchoMode(QLineEdit.Password)
      self.edtPasswd2.setMinimumWidth(MIN_PASSWD_WIDTH(self))

      layout.addWidget(lblPwd1, 2,0)
      layout.addWidget(lblPwd2, 3,0)
      layout.addWidget(self.edtPasswd1, 2,1)
      layout.addWidget(self.edtPasswd2, 3,1)

      self.lblMatches = QLabel(' '*20)
      self.lblMatches.setTextFormat(Qt.RichText)
      layout.addWidget(self.lblMatches, 4,1)


      self.chkDisableCrypt = QCheckBox('Disable encryption for this wallet')
      if not noPrevEncrypt:
         self.connect(self.chkDisableCrypt, SIGNAL('toggled(bool)'), \
                      self.disablePassphraseBoxes)
         layout.addWidget(self.chkDisableCrypt, 4,0)
         

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

      self.setWindowIcon(QIcon( self.main.iconfile))

      self.setLayout(layout)

      self.connect(self.edtPasswd1, SIGNAL('textChanged(QString)'), \
                   self.checkPassphrase)
      self.connect(self.edtPasswd2, SIGNAL('textChanged(QString)'), \
                   self.checkPassphrase)

      self.connect(self.btnAccept, SIGNAL('clicked()'), \
                   self.checkPassphraseFinal)

      self.connect(self.btnCancel, SIGNAL('clicked()'), \
                   self,           SLOT('reject()'))


   def disablePassphraseBoxes(self, noEncrypt=True):
      self.edtPasswd1.setEnabled(not noEncrypt) 
      self.edtPasswd2.setEnabled(not noEncrypt) 


   def checkPassphrase(self):
      if self.chkDisableCrypt.isChecked():
         return True
      p1 = self.edtPasswd1.text()
      p2 = self.edtPasswd2.text()
      if not p1==p2:
         self.lblMatches.setText('<font color="red"><b>Passphrases do not match!</b></font>')
         return False
      if len(p1)<5:
         self.lblMatches.setText('<font color="red"><b>Passphrase is too short!</b></font>')
         return False
      self.lblMatches.setText('<font color="green"><b>Passphrases match!</b></font>')
      return True
      

   def checkPassphraseFinal(self):
      if self.chkDisableCrypt.isChecked():
         self.accept()
      else:
         if self.checkPassphrase():
            dlg = DlgPasswd3(self, self.main)
            if dlg.exec_():
               if not str(dlg.edtPasswd3.text()) == str(self.edtPasswd1.text()):
                  QMessageBox.critical(self, 'Invalid Passphrase', \
                     'You entered your confirmation passphrase incorrectly!', QMessageBox.Ok)
               else:
                  self.accept() 
            else:
               self.reject()



class DlgPasswd3(QDialog):
   def __init__(self, parent=None, main=None):
      super(DlgPasswd3, self).__init__(parent)

      self.parent = parent
      self.main   = main

      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap('img/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnTxt1 = QLabel( '<b>!!!  DO NOT FORGET YOUR PASSPHRASE  !!!</b>')
      lblWarnTxt1.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnTxt2 = QLabel( \
         'Bitcoin Armory wallet encryption is designed to be extremely difficult to '
         'crack, even with GPU-acceleration.  No one can help you recover your coins '
         'if you forget your passphrase, not even the developers of this software. '
         'If you are inclined to forget your passphrase, please write it down '
         'or print a paper backup of your wallet and keep it in a secure location. ')
      lblWarnTxt2.setTextFormat(Qt.RichText)

      lblWarnTxt3 = QLabel( \
         'If you are sure you will remember it, you will have no problem '
         'typing it a third time to acknowledge '
         'you understand the consequences of losing your passphrase.')
      lblWarnTxt2.setWordWrap(True)
      lblWarnTxt3.setWordWrap(True)
      
      self.edtPasswd3 = QLineEdit()
      self.edtPasswd3.setEchoMode(QLineEdit.Password)
      self.edtPasswd3.setMinimumWidth(MIN_PASSWD_WIDTH(self))

      bbox = QDialogButtonBox()
      btnOk = QPushButton('Accept')
      btnNo = QPushButton('Cancel')
      self.connect(btnOk, SIGNAL('clicked()'), self.accept)
      self.connect(btnNo, SIGNAL('clicked()'), self.reject)
      bbox.addButton(btnOk, QDialogButtonBox.AcceptRole)
      bbox.addButton(btnNo, QDialogButtonBox.RejectRole)
      layout = QGridLayout()
      layout.addWidget(lblWarnImg,       0, 0, 4, 1)
      layout.addWidget(lblWarnTxt1,      0, 1, 1, 1)
      layout.addWidget(lblWarnTxt2,      2, 1, 1, 1)
      layout.addWidget(lblWarnTxt3,      4, 1, 1, 1)
      layout.addWidget(self.edtPasswd3,  5, 1, 1, 1)
      layout.addWidget(bbox,             6, 1, 1, 2)
      self.setLayout(layout)
      self.setWindowTitle('WARNING!')



################################################################################
class DlgChangeLabels(QDialog):
   def __init__(self, currName='', currDescr='', parent=None, main=None):
      super(DlgChangeLabels, self).__init__(parent)

      self.parent = parent
      self.main   = main

      self.edtName = QLineEdit()
      self.edtName.setMaxLength(32)
      lblName = QLabel("Wallet &name:")
      lblName.setBuddy(self.edtName)

      self.edtDescr = QTextEdit()
      tightHeight = tightSizeNChar(self.edtDescr, 1)[1]
      self.edtDescr.setMaximumHeight(tightHeight*4.2)
      lblDescr = QLabel("Wallet &description:")
      lblDescr.setAlignment(Qt.AlignVCenter)
      lblDescr.setBuddy(self.edtDescr)

      self.edtName.setText(currName)
      self.edtDescr.setText(currDescr)

      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonBox, SIGNAL('accepted()'), self.accept)
      self.connect(buttonBox, SIGNAL('rejected()'), self.reject)

      layout = QGridLayout()
      layout.addWidget(lblName,         1, 0, 1, 1)
      layout.addWidget(self.edtName,    1, 1, 1, 1)
      layout.addWidget(lblDescr,        2, 0, 1, 1)
      layout.addWidget(self.edtDescr,   2, 1, 2, 1)
      layout.addWidget(buttonBox,       4, 0, 1, 2)
      self.setLayout(layout)
   
      self.setWindowTitle('Wallet Descriptions')

      
################################################################################
class DlgWalletDetails(QDialog):
   """ For displaying the details of a specific wallet, with options """ 

   #############################################################################
   def __init__(self, wlt, usermode=USERMODE.Standard, parent=None, main=None):
      super(DlgWalletDetails, self).__init__(parent)
      self.setAttribute(Qt.WA_DeleteOnClose)


      self.wlt = wlt
      self.usermode = usermode
      self.parent = parent
      self.main   = main
      self.wlttype, self.typestr = determineWalletType(wlt, parent)

      self.labels = [wlt.labelName, wlt.labelDescr]
      self.passphrase = ''
      self.setMinimumSize(800,400)
      
      w,h = relaxedSizeNChar(self,60)
      viewWidth,viewHeight  = w, 10*h
      

      # Address view
      lblAddrList = QLabel('Addresses in Wallet:')
      self.wltAddrModel = WalletAddrDispModel(wlt, self)
      self.wltAddrView  = QTableView()
      self.wltAddrView.setModel(self.wltAddrModel)
      self.wltAddrView.setSelectionBehavior(QTableView.SelectRows)
      self.wltAddrView.setSelectionMode(QTableView.SingleSelection)
      self.wltAddrView.horizontalHeader().setStretchLastSection(True)
      self.wltAddrView.verticalHeader().setDefaultSectionSize(20)
      self.wltAddrView.setMinimumWidth(550)
      self.wltAddrView.setMinimumHeight(150)
      iWidth = tightSizeStr(self.wltAddrView, 'Imported')[0]
      initialColResize(self.wltAddrView, [0.4, 0.45, 64, iWidth*1.3, 0.2])

      self.wltAddrView.sizeHint = lambda: QSize(700, 225)
      self.wltAddrView.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

      self.wltAddrView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.wltAddrView.customContextMenuRequested.connect(self.showContextMenu)
   
      uacfv = lambda x: self.main.updateAddressCommentFromView(self.wltAddrView, self.wlt)
                   
      self.connect(self.wltAddrView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.dblClickAddressView)


      # Now add all the options buttons, dependent on the type of wallet.

      lbtnChangeLabels = QLabelButton('Change Wallet Labels');
      self.connect(lbtnChangeLabels, SIGNAL('clicked()'), self.changeLabels)

      if not self.wlt.watchingOnly:
         s = ''
         if self.wlt.useEncryption:
            s = 'Change or Remove Passphrase'
         else:
            s = 'Encrypt Wallet'
         lbtnChangeCrypto = QLabelButton(s)
         self.connect(lbtnChangeCrypto, SIGNAL('clicked()'), self.changeEncryption)

      lbtnSendBtc = QLabelButton('Send Bitcoins')
      if self.wlt.watchingOnly:
         lbtnSendBtc = QLabelButton('Prepare Offline Transaction')
      lbtnGenAddr = QLabelButton('Receive Bitcoins')
      lbtnImportA = QLabelButton('Import Private Key')
      lbtnDeleteA = QLabelButton('Remove Imported Address')
      #lbtnSweepA  = QLabelButton('Sweep Wallet/Address')

      lbtnForkWlt = QLabelButton('Create Watching-Only Copy')
      lbtnMkPaper = QLabelButton('Make Paper Backup')
      lbtnVwKeys  = QLabelButton('Backup Individual Keys')
      lbtnExport  = QLabelButton('Make Digital Backup')
      lbtnRemove  = QLabelButton('Delete/Remove Wallet')

      lbtnUnspent  = QLabelButton('View unspent transactions')

      self.connect(lbtnSendBtc, SIGNAL('clicked()'), self.execSendBtc)
      self.connect(lbtnGenAddr, SIGNAL('clicked()'), self.getNewAddress)
      self.connect(lbtnMkPaper, SIGNAL('clicked()'), self.execPrintDlg)
      self.connect(lbtnVwKeys,  SIGNAL('clicked()'), self.execKeyList)
      self.connect(lbtnRemove,  SIGNAL('clicked()'), self.execRemoveDlg)
      self.connect(lbtnImportA, SIGNAL('clicked()'), self.execImportAddress)
      self.connect(lbtnDeleteA, SIGNAL('clicked()'), self.execDeleteAddress)
      self.connect(lbtnExport,  SIGNAL('clicked()'), self.saveWalletCopy)
      self.connect(lbtnForkWlt, SIGNAL('clicked()'), self.forkOnlineWallet)

      optFrame = QFrame()
      optFrame.setFrameStyle(STYLE_SUNKEN)
      optLayout = QVBoxLayout()

      hasPriv = not self.wlt.watchingOnly
      adv = (self.main.usermode in (USERMODE.Advanced, USERMODE.Developer))

      def createVBoxSeparator():
         frm = QFrame()
         frm.setFrameStyle(QFrame.HLine | QFrame.Plain)
         return frm

      if True:              optLayout.addWidget(lbtnSendBtc)
      if True:              optLayout.addWidget(lbtnGenAddr)
      if hasPriv:           optLayout.addWidget(lbtnChangeCrypto)
      if True:              optLayout.addWidget(lbtnChangeLabels)

      if True:              optLayout.addWidget(createVBoxSeparator())

      if hasPriv:           optLayout.addWidget(lbtnMkPaper)
      if True:              optLayout.addWidget(lbtnVwKeys)
      if True:              optLayout.addWidget(lbtnExport)
      if hasPriv and adv:   optLayout.addWidget(lbtnForkWlt)
      if True:              optLayout.addWidget(lbtnRemove)

      if hasPriv and adv:  optLayout.addWidget(createVBoxSeparator())

      if hasPriv and adv:   optLayout.addWidget(lbtnImportA)
      if hasPriv and adv:   optLayout.addWidget(lbtnDeleteA)
      #if hasPriv and adv:   optLayout.addWidget(lbtnSweepA)

      optLayout.addStretch()
      optFrame.setLayout(optLayout)


      btnGoBack = QPushButton('<<< Go Back')
      self.connect(btnGoBack, SIGNAL('clicked()'), self.accept)

      self.frm = QFrame()
      self.setWltDetailsFrame()

      totalFunds = self.wlt.getBalance('Total')
      spendFunds = self.wlt.getBalance('Spendable')
      unconfFunds= self.wlt.getBalance('Unconfirmed')
      uncolor = 'red' if unconfFunds>0 else 'black'
      btccolor = '#999999' if spendFunds==totalFunds else 'green'
      lblcolor = '#999999' if spendFunds==totalFunds else 'black'

      lblTot  = QRichLabel('<b><font color="%s">Maximum Funds:</font></b>'%lblcolor, doWrap=False); 
      lblSpd  = QRichLabel('<b>Spendable Funds:</b>', doWrap=False); 
      lblUcn  = QRichLabel('<b>Unconfirmed:</b>', doWrap=False); 

      totStr = '<b><font color="%s">%s</font></b>' % (btccolor, coin2str(totalFunds))
      spdStr = '<b><font color="green">%s</font></b>' % (coin2str(spendFunds))
      ucnStr = '<b><font color="%s">%s</font></b>' % (uncolor,coin2str(unconfFunds))
      lblTotalFunds  = QRichLabel(totStr, doWrap=False)
      lblSpendFunds  = QRichLabel(spdStr, doWrap=False)
      lblUnconfFunds = QRichLabel(ucnStr, doWrap=False)
      lblTotalFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      lblSpendFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      lblUnconfFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

      lblTot.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      lblSpd.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      lblUcn.setAlignment(Qt.AlignRight | Qt.AlignVCenter)


      lblBTC1 = QRichLabel('<b><font color="%s">BTC</font></b>'%lblcolor, doWrap=False)
      lblBTC2 = QRichLabel('<b>BTC</b>', doWrap=False)
      lblBTC3 = QRichLabel('<b>BTC</b>', doWrap=False)
      ttipTot = createToolTipObject( \
            'Total funds if all current transactions are confirmed.  '
            'Value appears gray when it is the same as your spendable funds.')
      ttipSpd = createToolTipObject( 'Funds that can be spent <i>right now</i>')
      ttipUcn = createToolTipObject( 'Funds that have less than 6 confirmations' )


      frmTotals = QFrame()
      frmTotals.setFrameStyle(STYLE_NONE)
      frmTotalsLayout = QGridLayout()
      frmTotalsLayout.addWidget(lblTot, 0,0)
      frmTotalsLayout.addWidget(lblSpd, 1,0)
      frmTotalsLayout.addWidget(lblUcn, 2,0)

      frmTotalsLayout.addWidget(lblTotalFunds,  0,1)
      frmTotalsLayout.addWidget(lblSpendFunds,  1,1)
      frmTotalsLayout.addWidget(lblUnconfFunds, 2,1)

      frmTotalsLayout.addWidget(lblBTC1, 0,2)
      frmTotalsLayout.addWidget(lblBTC2, 1,2)
      frmTotalsLayout.addWidget(lblBTC3, 2,2)

      frmTotalsLayout.addWidget(ttipTot, 0,3)
      frmTotalsLayout.addWidget(ttipSpd, 1,3)
      frmTotalsLayout.addWidget(ttipUcn, 2,3)

      # Temp disable unconf display until calc is fixed
      #lblUcn.setVisible(False)
      #lblUnconfFunds.setVisible(False)
      #lblBTC3.setVisible(False)
      #ttipUcn.setVisible(False)

      frmTotals.setLayout(frmTotalsLayout)

      layout = QGridLayout()
      layout.addWidget(self.frm,              0, 0, 3, 4)
      layout.addWidget(self.wltAddrView,      4, 0, 2, 4)
      layout.addWidget(btnGoBack,             6, 0, 2, 1)
      layout.addWidget(frmTotals,             6, 3, 2, 1)

      layout.addWidget(QLabel("Available Actions:"), \
                                              0, 4)
      layout.addWidget(optFrame,              1, 4, 8, 2)
      self.setLayout(layout)

      self.setWindowTitle('Wallet Properties')

      
   #############################################################################
   def showContextMenu(self, pos):
      menu = QMenu(self.wltAddrView)
      std = (self.main.usermode==USERMODE.Standard)
      adv = (self.main.usermode==USERMODE.Advanced)
      dev = (self.main.usermode==USERMODE.Developer)
      
      if True:  actionCopyAddr    = menu.addAction("Copy Address")
      if dev:   actionCopyHash160 = menu.addAction("Copy Hash160")
      if True:  actionCopyComment = menu.addAction("Copy Comment")
      if True:  actionCopyBalance = menu.addAction("Copy Balance")
      idx = self.wltAddrView.selectedIndexes()[0]
      action = menu.exec_(QCursor.pos())
         
      if action==actionCopyAddr:
         s = self.wltAddrView.model().index(idx.row(), ADDRESSCOLS.Address).data().toString()
      elif dev and action==actionCopyHash160:
         s = str(self.wltAddrView.model().index(idx.row(), ADDRESSCOLS.Address).data().toString())
         s = binary_to_hex(addrStr_to_hash160(s))
      elif action==actionCopyComment:
         s = self.wltAddrView.model().index(idx.row(), ADDRESSCOLS.Comment).data().toString()
      elif action==actionCopyBalance:
         s = self.wltAddrView.model().index(idx.row(), ADDRESSCOLS.Balance).data().toString()
      else:
         return

      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(s).strip())

   #############################################################################
   def dblClickAddressView(self, index):
      model = index.model()
      if index.column()==ADDRESSCOLS.Comment:
         self.main.updateAddressCommentFromView(self.wltAddrView, self.wlt)
      else:
         addrStr = str(index.model().index(index.row(), ADDRESSCOLS.Address).data().toString())
         dlg = DlgAddressInfo(self.wlt, addrStr_to_hash160(addrStr), self, self.main)
         dlg.exec_()


   #############################################################################
   def changeLabels(self):
      dlgLabels = DlgChangeLabels(self.wlt.labelName, self.wlt.labelDescr, self, self.main)
      if dlgLabels.exec_():
         # Make sure to use methods like this which not only update in memory,
         # but guarantees the file is updated, too
         newName  = str(dlgLabels.edtName.text())
         newDescr = str(dlgLabels.edtDescr.toPlainText())
         self.wlt.setWalletLabels(newName, newDescr)

         #self.setWltDetailsFrame()
         self.labelValues[WLTFIELDS.Name].setText(newName)
         self.labelValues[WLTFIELDS.Descr].setText(newDescr)


   #############################################################################
   def changeEncryption(self):
      dlgCrypt = DlgChangePassphrase(self, self.main, not self.wlt.useEncryption)
      if dlgCrypt.exec_():
         self.disableEncryption = dlgCrypt.chkDisableCrypt.isChecked()
         newPassphrase = SecureBinaryData(str(dlgCrypt.edtPasswd1.text()))

         if self.wlt.useEncryption:
            origPassphrase = SecureBinaryData(str(dlgCrypt.edtPasswdOrig.text()))
            if self.wlt.verifyPassphrase(origPassphrase):
               self.wlt.unlock(securePassphrase=origPassphrase)
            else:
               # Even if the wallet is already unlocked, enter pwd again to change it
               QMessageBox.critical(self, 'Invalid Passphrase', \
                     'Previous passphrase is not correct!  Could not unlock wallet.', \
                     QMessageBox.Ok)
         
         
         if self.disableEncryption:
            self.wlt.changeWalletEncryption(None, None)
            #self.accept()
            self.labelValues[WLTFIELDS.Secure].setText('No Encryption')
            self.labelValues[WLTFIELDS.Crypto].setText('None')
            self.labelValues[WLTFIELDS.Secure].setText('')
            self.labelValues[WLTFIELDS.Secure].setText('')
         else:
            if not self.wlt.useEncryption:
               kdfParams = self.wlt.computeSystemSpecificKdfParams(0.2)
               self.wlt.changeKdfParams(*kdfParams)
            self.wlt.changeWalletEncryption(securePassphrase=newPassphrase)
            self.labelValues[WLTFIELDS.Secure].setText('Encrypted')
            #self.accept()
      

   def getNewAddress(self):
      dlg = DlgNewAddressDisp(self.wlt, self, self.main)
      dlg.exec_()
       

   def execSendBtc(self):
      dlgSend = DlgSendBitcoins(self.wlt, self, self.main)
      dlgSend.exec_()
   


   def changeKdf(self):
      """ 
      This is a low-priority feature.  I mean, the PyBtcWallet class has this
      feature implemented, but I don't have a GUI for it
      """
      pass

   def execPrintDlg(self):
      if self.wlt.isLocked:
         unlockdlg = DlgUnlockWallet(self.wlt, self, self.main, 'Create Paper Backup')
         if not unlockdlg.exec_():
            return

      if not self.wlt.addrMap['ROOT'].hasPrivKey():
         QMessageBox.warning(self, 'Move along...', \
           'This wallet does not contain any private keys.  Nothing to backup!', QMessageBox.Ok)
         return 

      dlg = DlgPaperBackup(self.wlt, self, self.main)
      dlg.exec_()
      
   def execRemoveDlg(self):
      dlg = DlgRemoveWallet(self.wlt, self, self.main)
      if dlg.exec_():
         pass # not sure that I don't handle everything in the dialog itself

   def execKeyList(self):
      dlg = DlgShowKeyList(self.wlt, self, self.main)
      dlg.exec_()

   def execDeleteAddress(self):
      selectedList = self.wltAddrView.selectedIndexes()
      if len(selectedList)==0:
         QMessageBox.warning(self, 'No Selection', \
               'You must select an address to remove!', \
               QMessageBox.Ok)
         return
      
      row = selectedList[0].row()
      addrStr = str(self.wltAddrView.model().index(row, ADDRESSCOLS.Address).data().toString())
      addr160 = addrStr_to_hash160(addrStr)
      if self.wlt.addrMap[addr160].chainIndex==-2:
         dlg = DlgRemoveAddress(self.wlt, addr160,  self, self.main)
         dlg.exec_()
      else:
         QMessageBox.warning(self, 'Invalid Selection', \
               'You cannot delete addresses generated by your wallet.  '
               'Only imported addresses can be deleted.', \
               QMessageBox.Ok)
         return


   def execImportAddress(self):
      if not self.main.settings.getSettingOrSetDefault('DNAA_ImportWarning', False):
         result = MsgBoxWithDNAA(MSGBOX.Warning, 'Import Address Warning', \
                       'Armory supports importing of external '
                       'addresses into your wallet, including encryption, '
                       'but imported addresses <b>cannot</b> be protected/saved '
                       'by a paper backups.  Watching-only wallets will include '
                       'imported addresses if the watching-only wallet was '
                       'created after the address was imported.', None)
         self.main.settings.set('DNAA_ImportWarning', result[1])

      # Now we are past the [potential] warning box.  Actually open
      # The import dialog, now
      dlg = DlgImportAddress(self.wlt, self, self.main)
      dlg.exec_()



   def saveWalletCopy(self):
      fn = 'armory_%s_.wallet' % self.wlt.uniqueIDB58
      if self.wlt.watchingOnly:
         fn = 'armory_%s.watchonly.wallet' % self.wlt.uniqueIDB58
      savePath = self.main.getFileSave(defaultFilename=fn)
      if len(savePath)>0:
         self.wlt.writeFreshWalletFile(savePath)
         self.main.statusBar
         self.main.statusBar().showMessage( \
            'Successfully copied wallet to ' + savePath, 10000)
      
      
   def forkOnlineWallet(self):
      currPath = self.wlt.walletPath
      pieces = os.path.splitext(currPath)
      currPath = pieces[0] + '.watchonly' + pieces[1]
      
      saveLoc = self.main.getFileSave('Save Watching-Only Copy',\
                                      defaultFilename=currPath)
      if not saveLoc.endswith('.wallet'):
         saveLoc += '.wallet'
      self.wlt.forkOnlineWallet(saveLoc, self.wlt.labelName, \
                             '(Watching-Only) ' + self.wlt.labelDescr)
   
         
         


   # A possible way to remove an existing layout 
   #def setLayout(self, layout):
       #self.clearLayout()
       #QWidget.setLayout(self, layout)
   #
   #def clearLayout(self):
       #if self.layout() is not None:
           #old_layout = self.layout()
           #for i in reversed(range(old_layout.count())):
               #old_layout.itemAt(i).widget().setParent(None)
           #import sip
           #sip.delete(old_layout)

   #############################################################################
   def setWltDetailsFrame(self):
      dispCrypto = self.wlt.useEncryption and (self.usermode==USERMODE.Advanced or \
                                               self.usermode==USERMODE.Developer)
      self.wltID = self.wlt.uniqueIDB58

      if dispCrypto:
         kdftimestr = "%0.3f seconds" % self.wlt.testKdfComputeTime()
         mem = self.wlt.kdf.getMemoryReqtBytes()
         kdfmemstr = str(mem/1024)+' kB'
         if mem >= 1024*1024:
            kdfmemstr = str(mem/(1024*1024))+' MB'
   
   
      tooltips = [[]]*9
   
      tooltips[WLTFIELDS.Name] = createToolTipObject(
            'This is the name stored with the wallet file.  Click on the '
            '"Change Labels" button at the bottom of this '
            'window to change this field' )
   
      tooltips[WLTFIELDS.Descr] = createToolTipObject(
            'This is the description of the wallet stored in the wallet file.  '
            'Press the "Change Labels" button at the bottom of this '
            'window to change this field' )
   
      tooltips[WLTFIELDS.WltID] = createToolTipObject(
            'This is a unique identifier for this wallet, based on the root key.  '
            'No other wallet can have the same ID '
            'unless it is a copy of this one, regardless of whether '
            'the name and description match.')
   
      tooltips[WLTFIELDS.NumAddr] = createToolTipObject(
            'The number of addresses generated so far for this wallet.  '
            'This includes addresses imported manually')
   
      if self.typestr=='Offline':
         tooltips[WLTFIELDS.Secure] = createToolTipObject(
            'Offline:  This is a "Watching-Only" wallet that you have identified '
            'belongs to you, but you cannot spend any of the wallet funds '
            'using this wallet.  This kind of wallet '
            'is usually stored on an internet-connected computer, to manage '
            'incoming transactions, but the private keys needed '
            'to spend the money are stored on an offline computer.')
      elif self.typestr=='Watching-Only':
         tooltips[WLTFIELDS.Secure] = createToolTipObject(
            'Watching-Only:  You can only watch addresses in this wallet '
            'but cannot spend any of the funds.')
      elif self.typestr=='No Encryption':
         tooltips[WLTFIELDS.Secure] = createToolTipObject(
            'No Encryption: This wallet contains private keys, and does not require '
            'a passphrase to spend funds available to this wallet.  If someone '
            'else obtains a copy of this wallet, they can also spend your funds!  '
            '(You can click the "Change Encryption" button at the bottom of this '
            'window to enabled encryption)')
      elif self.typestr=='Encrypted':
         tooltips[WLTFIELDS.Secure] = createToolTipObject(
            'This wallet contains the private keys needed to spend this wallet\'s '
            'funds, but they are encrypted on your harddrive.  The wallet must be '
            '"unlocked" with the correct passphrase before you can spend any of the '
            'funds.  You can still generate new addresses and monitor incoming '
            'transactions, even with a locked wallet.')

      tooltips[WLTFIELDS.BelongsTo] = createToolTipObject(
            'Declare who owns this wallet.  If you click on the field and select '
            '"This wallet is mine", it\'s balance will be included in your total '
            'Armory Balance in the main window' )
   
      tooltips[WLTFIELDS.Crypto] = createToolTipObject(
            'The encryption used to secure your wallet keys' )
   
      tooltips[WLTFIELDS.Time] = createToolTipObject(
            'This is exactly how long it takes your computer to unlock your '
            'wallet after you have entered your passphrase.  If someone got '
            'ahold of your wallet, this is approximately how long it would take '
            'them to for each guess of your passphrase.')
   
      tooltips[WLTFIELDS.Mem] = createToolTipObject(
            'This is the amount of memory required to unlock your wallet. '
            'Memory values above 2 MB pretty much guarantee that GPU-acceleration '
            'will be useless for guessing your passphrase')
   
      labelNames = [[]]*9
      labelNames[WLTFIELDS.Name]    = QLabel('Wallet Name:')
      labelNames[WLTFIELDS.Descr]   = QLabel('Description:')
   
      labelNames[WLTFIELDS.WltID]     = QLabel('Wallet ID:')
      labelNames[WLTFIELDS.NumAddr]   = QLabel('#Addresses:')
      labelNames[WLTFIELDS.Secure]    = QLabel('Security:')

      labelNames[WLTFIELDS.BelongsTo] = QLabel('Belongs to:')
   
   
      # TODO:  Add wallet path/location to this!
   
      if dispCrypto:
         labelNames[WLTFIELDS.Crypto] = QLabel('Encryption:')
         labelNames[WLTFIELDS.Time]   = QLabel('Unlock Time:')
         labelNames[WLTFIELDS.Mem]    = QLabel('Unlock Memory:')
   
      self.labelValues = [[]]*9
      self.labelValues[WLTFIELDS.Name]    = QLabel(self.wlt.labelName)
      self.labelValues[WLTFIELDS.Descr]   = QLabel(self.wlt.labelDescr)
   
      self.labelValues[WLTFIELDS.WltID]     = QLabel(self.wlt.uniqueIDB58)
      self.labelValues[WLTFIELDS.NumAddr]   = QLabel(str(len(self.wlt.getLinearAddrList())))
      self.labelValues[WLTFIELDS.Secure]    = QLabel(self.typestr)
      self.labelValues[WLTFIELDS.BelongsTo] = QLabel('')

      # Set the owner appropriately
      if self.wlt.watchingOnly:
         if self.main.getWltSetting(self.wltID, 'IsMine'):
            self.labelValues[WLTFIELDS.BelongsTo] = QLabelButton('You own this wallet')
            self.labelValues[WLTFIELDS.BelongsTo].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
         else:
            owner = self.main.getWltSetting(self.wltID, 'BelongsTo')
            if owner=='':
               self.labelValues[WLTFIELDS.BelongsTo] = QLabelButton('Someone else...')
               self.labelValues[WLTFIELDS.BelongsTo].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            else:
               self.labelValues[WLTFIELDS.BelongsTo] = QLabelButton(owner)
               self.labelValues[WLTFIELDS.BelongsTo].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

         self.connect(self.labelValues[WLTFIELDS.BelongsTo], SIGNAL('clicked()'), \
                      self.execSetOwner)

            
   
   
      if dispCrypto:
         self.labelValues[WLTFIELDS.Crypto] = QLabel('AES256')
         self.labelValues[WLTFIELDS.Time]   = QLabel(kdftimestr)
         self.labelValues[WLTFIELDS.Mem]    = QLabel(kdfmemstr)
   
      for ttip in tooltips:
         try:
            ttip.setAlignment(Qt.AlignRight | Qt.AlignTop)
            w,h = relaxedSizeStr(ttip, '(?)') 
            ttip.setMaximumSize(w,h)
         except AttributeError:
            pass
   
      for lbl in labelNames:
         try:
            lbl.setTextFormat(Qt.RichText)
            lbl.setText( '<b>' + lbl.text() + '</b>')
            lbl.setContentsMargins(0, 0, 0, 0)
            w,h = tightSizeStr(lbl, '9'*16)
            lbl.setMaximumSize(w,h)
         except AttributeError:
            pass
   
   
      for lbl in self.labelValues:
         try:
            lbl.setText( '<i>' + lbl.text() + '</i>')
            lbl.setContentsMargins(10, 0, 10, 0)
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                        Qt.TextSelectableByKeyboard)
         except AttributeError:
            pass
   
      labelNames[WLTFIELDS.Descr].setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.labelValues[WLTFIELDS.Descr].setWordWrap(True)
      self.labelValues[WLTFIELDS.Descr].setAlignment(Qt.AlignLeft | Qt.AlignTop)
   
      lblEmpty = QLabel(' '*20)
   
      layout = QGridLayout()
      layout.addWidget(tooltips[WLTFIELDS.Name],             0, 0); 
      layout.addWidget(labelNames[WLTFIELDS.Name],           0, 1); 
      layout.addWidget(self.labelValues[WLTFIELDS.Name],     0, 2)
   
      layout.addWidget(tooltips[WLTFIELDS.Descr],            1, 0); 
      layout.addWidget(labelNames[WLTFIELDS.Descr],          1, 1); 
      layout.addWidget(self.labelValues[WLTFIELDS.Descr],    1, 2, 3, 1)
   
      layout.addWidget(tooltips[WLTFIELDS.WltID],            0, 3); 
      layout.addWidget(labelNames[WLTFIELDS.WltID],          0, 4); 
      layout.addWidget(self.labelValues[WLTFIELDS.WltID],    0, 5)
   
      layout.addWidget(tooltips[WLTFIELDS.NumAddr],          1, 3); 
      layout.addWidget(labelNames[WLTFIELDS.NumAddr],        1, 4); 
      layout.addWidget(self.labelValues[WLTFIELDS.NumAddr],  1, 5)
   
      layout.addWidget(tooltips[WLTFIELDS.Secure],           2, 3); 
      layout.addWidget(labelNames[WLTFIELDS.Secure],         2, 4); 
      layout.addWidget(self.labelValues[WLTFIELDS.Secure],   2, 5)
   
      if self.wlt.watchingOnly:
         layout.addWidget(tooltips[WLTFIELDS.BelongsTo],           3, 3); 
         layout.addWidget(labelNames[WLTFIELDS.BelongsTo],         3, 4); 
         layout.addWidget(self.labelValues[WLTFIELDS.BelongsTo],   3, 5)
      
   
      if dispCrypto:
         layout.addWidget(tooltips[WLTFIELDS.Crypto],         0, 6); 
         layout.addWidget(labelNames[WLTFIELDS.Crypto],       0, 7); 
         layout.addWidget(self.labelValues[WLTFIELDS.Crypto], 0, 8)
   
         layout.addWidget(tooltips[WLTFIELDS.Time],           1, 6); 
         layout.addWidget(labelNames[WLTFIELDS.Time],         1, 7); 
         layout.addWidget(self.labelValues[WLTFIELDS.Time],   1, 8)
   
         layout.addWidget(tooltips[WLTFIELDS.Mem],            2, 6); 
         layout.addWidget(labelNames[WLTFIELDS.Mem],          2, 7); 
         layout.addWidget(self.labelValues[WLTFIELDS.Mem],    2, 8)
      else:
         layout.addWidget(lblEmpty, 0, 4); layout.addWidget(lblEmpty, 0, 5)
         layout.addWidget(lblEmpty, 1, 4); layout.addWidget(lblEmpty, 1, 5)
         layout.addWidget(lblEmpty, 2, 4); layout.addWidget(lblEmpty, 2, 5)
         pass
         
   
      self.frm = QFrame()
      self.frm.setFrameStyle(STYLE_SUNKEN)
      self.frm.setLayout(layout)
      
      

   def execSetOwner(self):
      dlg = self.dlgChangeOwner(self.wltID, self) 
      if dlg.exec_():
         if dlg.chkIsMine.isChecked():
            self.main.setWltSetting(self.wltID, 'IsMine', True)
            self.main.setWltSetting(self.wltID, 'BelongsTo', '')
            self.labelValues[WLTFIELDS.BelongsTo].setText('You own this wallet')
            self.labelValues[WLTFIELDS.BelongsTo].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.labelValues[WLTFIELDS.Secure].setText('<i>Offline</i>')
         else:
            owner = str(dlg.edtOwnerString.text())  
            self.main.setWltSetting(self.wltID, 'IsMine', False)
            self.main.setWltSetting(self.wltID, 'BelongsTo', owner)
               
            if len(owner)>0:
               self.labelValues[WLTFIELDS.BelongsTo].setText(owner)
            else:
               self.labelValues[WLTFIELDS.BelongsTo].setText('Someone else')
            self.labelValues[WLTFIELDS.Secure].setText('<i>Watching-only</i>')
            self.labelValues[WLTFIELDS.BelongsTo].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.labelValues[WLTFIELDS.Secure].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
         


   class dlgChangeOwner(QDialog):
      def __init__(self, wltID, parent=None, main=None):
         super(parent.dlgChangeOwner, self).__init__(parent)

         self.parent = parent
         self.main   = main

         layout = QGridLayout()
         self.chkIsMine = QCheckBox('This wallet is mine')
         self.edtOwnerString = QLineEdit() 
         if parent.main.getWltSetting(wltID, 'IsMine'):
            lblDescr = QLabel(
               'The funds in this wallet are currently identified as '
               'belonging to <b><i>you</i></b>.  As such, any funds '
               'available to this wallet will be included in the total '
               'balance displayed on the main screen.  \n\n'
               'If you do not actually own this wallet, or do not wish '
               'for its funds to be considered part of your balance, '
               'uncheck the box below.  Optionally, you can include the '
               'name of the person or organization that does own it.' )
            lblDescr.setWordWrap(True)
            layout.addWidget(lblDescr,          0, 0, 1, 2)
            layout.addWidget(self.chkIsMine,    1, 0)
            self.chkIsMine.setChecked(True)
            self.edtOwnerString.setEnabled(False)
         else:
            owner = parent.main.getWltSetting(wltID, 'BelongsTo')
            if owner=='':
               owner='someone else'
            else:
               self.edtOwnerString.setText(owner)
            lblDescr = QLabel(
               'The funds in this wallet are currently identified as '
               'belonging to <i><b>'+owner+'</b></i>.  If these funds are actually '
               'yours, and you would like the funds included in your balance in '
               'the main window, please check the box below.\n\n' )
            lblDescr.setWordWrap(True)
            layout.addWidget(lblDescr,          0, 0, 1, 2)
            layout.addWidget(self.chkIsMine,    1, 0)

            ttip = createToolTipObject(
               'You might choose this option if you keep a full '
               'wallet on a non-internet-connected computer, and use this '
               'watching-only wallet on this computer to generate addresses '
               'and monitor incoming transactions.')
            layout.addWidget(ttip,          1, 1)


         slot = lambda b: self.edtOwnerString.setEnabled(not b)
         self.connect(self.chkIsMine, SIGNAL('toggled(bool)'), slot)
   
         layout.addWidget(QLabel('Wallet owner (optional):'),     3, 0)
         layout.addWidget(self.edtOwnerString,     3, 1)
         bbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                    QDialogButtonBox.Cancel)
         self.connect(bbox, SIGNAL('accepted()'), self.accept)
         self.connect(bbox, SIGNAL('rejected()'), self.reject)
         layout.addWidget(bbox,  4, 0)
         self.setLayout(layout)
         self.setWindowTitle('Set Wallet Owner')


class DlgNewAddressDisp(QDialog):
   """
   We just generated a new address, let's show it to the user and let them
   a comment to it, if they want.
   """
   def __init__(self, wlt, parent=None, main=None):
      super(DlgNewAddressDisp, self).__init__(parent)

      self.wlt  = wlt
      self.addr = wlt.getNextUnusedAddress()
      self.parent = parent
      self.main   = main

      wlttype = determineWalletType( self.wlt, self.main)[0]

      notMyWallet   = (wlttype==WLTTYPES.WatchOnly)
      offlineWallet = (wlttype==WLTTYPES.Offline)
      dnaaPropName = 'Wallet_%s_%s' % (self.wlt.uniqueIDB58, 'DNAA_RecvOther')
      dnaaThisWallet = self.main.settings.getSettingOrSetDefault(dnaaPropName, False)
      if notMyWallet and not dnaaThisWallet:
         result = MsgBoxWithDNAA(MSGBOX.Warning, 'This is not your wallet!', \
               'You are getting an address for a wallet that '
               'does not appear to belong to you.  Any money sent to this '
               'address will not appear in your total balance, and cannot '
               'be spent from this computer.<br><br>'
               'If this is actually your wallet (perhaps you maintain the full '
               'wallet on a separate computer), then please change the '
               '"Belongs To" field in the wallet-properties for this wallet.', \
               'Do not show this warning again', wCancel=True)
         self.main.settings.set(dnaaPropName, result[1])
         if result[0]==False:
            self.reject()
            return

      if offlineWallet and not dnaaThisWallet:
         result = MsgBoxWithDNAA(MSGBOX.Warning, 'This is not your wallet!', \
               'You are getting an address for a wallet that '
               'you have specified belongs to you, but you cannot actually '
               'spend the funds from this computer.  This is usually the case when '
               'you keep the full wallet on a separate computer for security '
               'purposes.<br><br>'
               'If this does not sound right, then please do not use the following '
               'address.  Instead, change the wallet properties "Belongs To" field '
               'to specify that this wallet is not actually yours.', \
               'Do not show this warning again', wCancel=True)
         self.main.settings.set(dnaaPropName, result[1])
         if result[0]==False:
            self.reject()
            return

         

      lblDescr = QLabel( \
            'The following address can be used to to receive Bitcoins:')
      self.edtNewAddr = QLineEdit()
      self.edtNewAddr.setReadOnly(True)
      self.edtNewAddr.setText(self.addr.getAddrStr())
      self.edtNewAddr.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      btnClipboard = QPushButton('Copy to Clipboard')
      #lbtnClipboard.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      self.lblIsCopied = QLabel('')
      self.lblIsCopied.setTextFormat(Qt.RichText)
      self.connect(btnClipboard, SIGNAL('clicked()'), self.setClipboard)
      
      tooltip1 = createToolTipObject( \
            'You can securely use this address as many times as you want. '
            'However, all people to whom you give this address will '
            'be able to see the number and amount of Bitcoins <b>ever</b> '
            'sent to it.  Therefore, using a new address for each transaction '
            'improves overall privacy, but there is no security issues '
            'with reusing any address.' )

      frmNewAddr = QFrame()
      frmNewAddr.setFrameStyle(STYLE_RAISED)
      frmNewAddrLayout = QGridLayout()
      frmNewAddrLayout.addWidget(lblDescr,        0,0, 1,2)
      frmNewAddrLayout.addWidget(self.edtNewAddr, 1,0, 1,1)
      frmNewAddrLayout.addWidget(tooltip1,        1,1, 1,1)

      if not notMyWallet:
         palette = QPalette()
         palette.setColor( QPalette.Base, Colors.WltMine )
         boldFont = self.edtNewAddr.font()
         boldFont.setWeight(QFont.Bold)
         self.edtNewAddr.setFont(boldFont)
         self.edtNewAddr.setPalette( palette );
         self.edtNewAddr.setAutoFillBackground( True );

      frmCopy = QFrame()
      frmCopy.setFrameShape(QFrame.NoFrame)
      frmCopyLayout = QHBoxLayout()
      frmCopyLayout.addStretch()
      frmCopyLayout.addWidget(btnClipboard)
      frmCopyLayout.addWidget(self.lblIsCopied)
      frmCopyLayout.addStretch()
      frmCopy.setLayout(frmCopyLayout)

      frmNewAddrLayout.addWidget(frmCopy, 2, 0, 1, 2)
      frmNewAddr.setLayout(frmNewAddrLayout)
   

      lblCommDescr = QLabel( \
            '(Optional) You can specify a comment to be stored with '
            'this address.  The comment can be changed '
            'at a later time in the wallet properties dialog.')
      lblCommDescr.setWordWrap(True)
      #lblComm = QLabel('Comment:')
      #lblComm.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
      self.edtComm = QTextEdit()
      tightHeight = tightSizeNChar(self.edtComm, 1)[1]
      self.edtComm.setMaximumHeight(tightHeight*3.2)

      frmComment = QFrame()
      frmComment.setFrameStyle(STYLE_RAISED)
      frmCommentLayout = QGridLayout()
      frmCommentLayout.addWidget(lblCommDescr,    0,0, 1,2)
      #frmCommentLayout.addWidget(lblComm,         1,0, 1,1)
      frmCommentLayout.addWidget(self.edtComm,    1,0, 2,2)
      frmComment.setLayout(frmCommentLayout)

      
      lblRecvWlt = QRichLabel( \
            'Money sent to this address will appear in the following wallet:', \
            doWrap=False)
      
      lblRecvWlt.setWordWrap(True)
      lblRecvWlt.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
      lblRecvWlt.setMinimumWidth( tightSizeStr(lblRecvWlt, lblRecvWlt.text())[0])

      lblRecvWltID = QLabel( \
            '<b>"%s"</b>  (%s)' % (wlt.labelName, wlt.uniqueIDB58))
      lblRecvWltID.setWordWrap(True)
      lblRecvWltID.setTextFormat(Qt.RichText)
      lblRecvWltID.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
   
      buttonBox = QDialogButtonBox()
      self.btnDone   = QPushButton("Done")
      #self.btnCancel = QPushButton("Cancel")
      self.connect(self.btnDone,   SIGNAL('clicked()'), self.acceptNewAddr)
      #self.connect(self.btnCancel, SIGNAL('clicked()'), self.rejectNewAddr)
      buttonBox.addButton(self.btnDone,   QDialogButtonBox.AcceptRole)
      #buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)




      frmWlt = QFrame()
      frmWlt.setFrameShape(STYLE_RAISED)
      frmWltLayout = QVBoxLayout()
      frmWltLayout.addWidget(lblRecvWlt)
      frmWltLayout.addWidget(lblRecvWltID)
      frmWlt.setLayout(frmWltLayout)



      layout=QGridLayout()
      layout.addWidget(frmNewAddr,         0, 0, 1, 2)
      #layout.addWidget(frmCopy,            1, 0, 1, 2)
      layout.addWidget(frmComment,         2, 0, 1, 2)
      layout.addWidget(frmWlt,             3, 0, 1, 2)
      layout.addWidget(buttonBox,          4, 0, 1, 2)

      self.setLayout(layout) 
      self.setWindowTitle('New Receiving Address')
      self.setFocus()

      try:
         self.parent.wltAddrModel.reset()
      except AttributeError:
         # Sometimes this is called from a dialog that doesn't have an addr model
         pass
   

   def acceptNewAddr(self):
      comm = str(self.edtComm.toPlainText())
      if len(comm)>0:
         self.wlt.setComment(self.addr.getAddr160(), comm)
      self.accept()

   def rejectNewAddr(self):
      #self.wlt.rewindHighestIndex(1)
      try:
         self.parent.reject()
      except AttributeError:
         pass
      self.reject()

   def setClipboard(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.addr.getAddrStr())
      self.lblIsCopied.setText('<i>Copied!</i>')


         

#############################################################################
# Display a warning box about import backups, etc
class DlgImportWarning(QDialog):
   def __init__(self, parent=None, main=None):
      super(DlgImportWarning, self).__init__(parent)
      self.main   = main 
      self.parent = parent
      lblWarn = QLabel( 'Armory supports importing of external '
            'addresses into your wallet, including encryption, '
            'but imported addresses <b>cannot</b> be protected/saved '
            'by a paper backups.  Watching-only wallets will include '
            'imported addresses if the watching-only wallet was '
            'created after the address was imported.')
      lblWarn.setTextFormat(Qt.RichText)
      lblWarn.setWordWrap(True)

      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap('img/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      self.chkDNAA = QCheckBox('Do not show this message again')
      bbox = QDialogButtonBox( QDialogButtonBox.Ok )
      self.connect(bbox, SIGNAL('accepted()'), self.acceptWarning)
      layout = QGridLayout()
      layout.addWidget(lblWarnImg,   0,0, 1,1)
      layout.addWidget(lblWarn,      0,1, 1,1)
      layout.addWidget(bbox,         1,0, 1,2)
      layout.addWidget(self.chkDNAA, 2,0, 1,2)
      self.setLayout(layout)
      self.setWindowTitle('Warning')

   def acceptWarning(self):
      if self.chkDNAA.isChecked():
         self.main.settings.set('DNAA_ImportWarning', True)
      self.accept()



#############################################################################
class DlgImportAddress(QDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgImportAddress, self).__init__(parent)

      self.wlt = wlt
      self.parent = parent
      self.main   = main
      descrText = ('If you have a private key that you would like to '
                   'add to this wallet, please enter it below.  If it '
                   'is in a format supported by Armory, it will be '
                   'detected and imported appropriately.  ')

      privTooltip = createToolTipObject( \
                       'Supported formats are any hexadecimal or Base58 '
                       'representation of a 32-byte private key (with or '
                       'without checksums), and mini-private-key format '
                       'used on Casascius physical bitcoins.')
         
      lblDescr = QLabel(descrText)
      lblDescr.setWordWrap(True)



      ## Import option
      self.radioImport = QRadioButton('Import this address to your wallet\n'
                                      'Only select this option if you are positive '
                                      'that no one else has access to this key')

      ## Sweep option (only available when online)
      if self.main.isOnline:
         self.radioSweep  = QRadioButton('Sweep any funds owned by this address '
                                         'into your wallet\n'
                                         'Select this option if someone else gave you this key')
         self.radioSweep.setChecked(True)
      else:
         self.radioSweep  = QRadioButton('Sweep any funds owned by this address '
                                         'into your wallet\n'
                                         '(Not available in offline mode)')
         self.radioImport.setChecked(True)
         self.radioSweep.setEnabled(False)


      sweepTooltip = createToolTipObject( \
         'You should never add an untrusted key to your wallet.  By choosing this '
         'option, you are only moving the funds into your wallet, but not the key '
         'itself.  You should use this option for Casascius physical Bitcoins.')

      importTooltip = createToolTipObject( \
         'This option will make the key part of your wallet, meaning that it '
         'can be used to securely receive future payments.  Never select this '
         'option for private keys that other people may have access to.')


      # Make sure that there can only be one selection
      btngrp = QButtonGroup(self)
      btngrp.addButton(self.radioSweep)
      btngrp.addButton(self.radioImport)
      btngrp.setExclusive(True)



      frmWarn = QFrame()
      frmWarn.setFrameStyle(QFrame.Box|QFrame.Plain)
      frmWarnLayout = QGridLayout()
      frmWarnLayout.addWidget(self.radioSweep,    0,0, 1,1)
      frmWarnLayout.addWidget(self.radioImport,   1,0, 1,1)
      frmWarnLayout.addWidget(sweepTooltip,  0,1, 1,1)
      frmWarnLayout.addWidget(importTooltip, 1,1, 1,1)
      frmWarn.setLayout(frmWarnLayout)


      lblPrivData = QLabel('Private Key Data:')
      self.edtPrivData = QLineEdit()
      self.edtPrivData.setMinimumWidth( tightSizeStr(self.edtPrivData, 'X'*60)[0])

      buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonbox, SIGNAL('accepted()'), self.processUserString)
      self.connect(buttonbox, SIGNAL('rejected()'), self.reject)

      

      layout = QGridLayout()
      layout.addWidget(lblDescr,          0, 0, 1, 3)
      layout.addWidget(lblPrivData,       1, 0, 1, 1)
      layout.addWidget(self.edtPrivData,  1, 1, 1, 1)
      layout.addWidget(privTooltip,       1, 2, 1, 1)
      layout.addWidget(frmWarn,           2, 0, 1, 3)
      layout.addWidget(buttonbox,         4, 0, 1, 3)

      self.setWindowTitle('Private Key Import')
      self.setLayout(layout)



   def processUserString(self):
      theStr = str(self.edtPrivData.text()).strip().replace(' ','')
      binKeyData, addr160, addrStr = '','',''

      try:
         binKeyData, keyType = parsePrivateKeyData(theStr)
         addr160 = convertKeyDataToAddress(privKey=binKeyData)
         addrStr = hash160_to_addrStr(addr160)
      except InvalidHashError, e:
         QMessageBox.warning(self, 'Entry Error',
            'The private key data you supplied appears to '
            'contain a consistency check.  This consistency '
            'check failed.  Please verify you entered the '
            'key data correctly.', QMessageBox.Ok)
         return
      except BadInputError, e:
         QMessageBox.critical(self, 'Invalid Data', e, QMessageBox.Ok)
         return
      except:
         QMessageBox.critical(self, 'Error Processing Key', \
            'There was an error processing the private key data. '
            'Please check that you entered it correctly', QMessageBox.Ok)
         return
         


      if not 'mini' in keyType.lower():
         reply = QMessageBox.question(self, 'Verify Address', \
               'The key data you entered appears to correspond to '
               'the following Bitcoin address:\n\n\t' + addrStr +
               '\n\nIs this the correct address?',
               QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
         if reply==QMessageBox.Cancel:
            return 
         else:
            if reply==QMessageBox.No:
               binKeyData = binary_switchEndian(binEntry)
               addr160 = convertKeyDataToAddress(privKey=binKeyData)
               addrStr = hash160_to_addrStr(addr160)
               reply = QMessageBox.question(self, 'Try Again', \
                     'It is possible that the key was supplied in a '
                     '"reversed" form.  When the data you provide is '
                     'reversed, the following address is obtained:\n\n\t '
                     + addrStr + '\n\nIs this the correct address?', \
                     QMessageBox.Yes | QMessageBox.No)
               if reply==QMessageBox.No:
                  binKeyData='' 



      # Finally, let's add the address to the wallet, or sweep the funds
      if self.radioSweep.isChecked():
         if self.wlt.hasAddr(addr160):
            result = QMessageBox.warning(self, 'Duplicate Address', \
            'The address you are trying to sweep is already part of this '
            'wallet.  You can still sweep it to a new address, but it will '
            'have no effect on your overall balance (in fact, it might be '
            'negative if you have to pay a fee for the transfer)\n\n'
            'Do you still want to sweep this key?', \
            QMessageBox.Yes | QMessageBox.Cancel)
            if not result==QMessageBox.Yes:
               return
   
         if not TheBDM.isInitialized():
            reply = QMessageBox.critical(self, 'Cannot Sweep Address', \
            'You need access to the Bitcoin network and the blockchain in order '
            'to find the balance of this address and sweep its funds. ', \
            QMessageBox.Ok)
            return

         # Create the address object for the addr to be swept
         oldAddr = PyBtcAddress().createFromPlainKeyData(SecureBinaryData(binKeyData))
         targAddr160 = self.wlt.getNextUnusedAddress().getAddr160()
         finishedTx, outVal, fee = self.main.createSweepAddrTx(oldAddr, targAddr160)
         if outVal<=fee:
            QMessageBox.critical(self, 'Cannot sweep',\
            'You cannot sweep the funds from this address, because the '
            'transaction fee would be equal to or greater than the amount '
            'swept.', QMessageBox.Ok)
            return

         if outVal==0:
            QMessageBox.critical(self, 'Nothing to do', \
            'The private key you have provided does not appear to contain '
            'any funds.  There is nothing to sweep.', \
            QMessageBox.Ok)
            return


         #reply = QMessageBox.warning(self, 'Verify Sweep', \
           #'You are about to sweep all funds from address \n\n%s\n\n to your '
           #'current wallet \n\n"%s" [%s]\n\n  The total amount to be '
           #'transferred is \n\n%s %s\n\nDo you want to continue?' % \
               #(oldAddr.getAddrStr(), self.wlt.labelName, self.wlt.uniqueIDB58, outStr, feeStr), \
           #QMessageBox.Yes | QMessageBox.Cancel)
         #if reply==QMessageBox.Yes:
      
         # Finally, if we got here, we're ready to broadcast!
         dispIn  = 'address <b>%s</b>' % oldAddr.getAddrStr()
         dispOut = 'wallet <b>"%s"</b> (%s) ' % (self.wlt.labelName, self.wlt.uniqueIDB58)
         if DlgVerifySweep(dispIn, dispOut, outVal, fee).exec_():
            self.main.broadcastTransaction(finishedTx, dryRun=False)
            
      elif self.radioImport.isChecked():
         if self.wlt.hasAddr(addr160):
            QMessageBox.critical(self, 'Duplicate Address', \
            'The address you are trying to import is already part of your '
            'wallet.  Address cannot be imported', QMessageBox.Ok)
            return

         wltID = self.main.getWalletForAddr160(addr160)
         if not wltID=='':
            reply = QMessageBox.critical(self, 'Duplicate Addresses', \
               'The key you entered is already part of another wallet '
               'another wallet you own:\n\n'
               'Address: ' + addrStr + '\n'
               'Wallet ID: ' + wltID + '\n'
               'Wallet Name: ' + self.main.walletMap[wltID].labelName + '\n\n'
               'If you continue, any funds in this '
               'address will be double-counted, causing your total balance '
               'to appear artificially high, and any transactions involving '
               'this address will confusingly appear in multiple wallets.'
               '\n\nWould you like to import this address anyway?', \
               QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if not reply==QMessageBox.Yes:
               return
   
         if self.wlt.useEncryption and self.wlt.isLocked:
            dlg = DlgUnlockWallet(self.wlt, self.main, 'Encrypt New Address')
            if not dlg.exec_():
               reply = QMessageBox.critical(self, 'Wallet is locked',
                  'New private key data cannot be imported unless the wallet is '
                  'unlocked.  Please try again when you have the passphrase.',\
                  QMessageBox.Ok)
               return


         self.wlt.importExternalAddressData( privKey=SecureBinaryData(binKeyData))
         self.main.statusBar().showMessage( 'Successful import of address ' \
                                 + addrStr + ' into wallet ' + self.wlt.uniqueIDB58, 10000)
      
      try:
         self.parent.wltAddrModel.reset()
      except:
         pass

      if TheBDM.isInitialized():
         self.wlt.syncWithBlockchain()

      self.main.walletListChanged()
      self.accept()




#############################################################################
class DlgVerifySweep(QDialog):
   def __init__(self, inputStr, outputStr, outVal, fee, parent=None, main=None):
      super(DlgVerifySweep, self).__init__(parent)

      self.parent = parent
      self.main   = main  

      lblQuestion = QRichLabel( \
            'You are about to <i>sweep</i> all funds from the specified address '
            'to your wallet.  Please confirm the action:')
      

      outStr = coin2str(outVal,maxZeros=2)
      feeStr = ('') if (fee==0) else ('(Fee: %s)' % coin2str(fee,maxZeros=0))

      frm = QFrame()
      frm.setFrameStyle(STYLE_RAISED)
      frmLayout = QGridLayout()
      #frmLayout.addWidget(QRichLabel('Funds will be <i>swept</i>...'), 0,0, 1,2)
      frmLayout.addWidget(QRichLabel('      From ' + inputStr, doWrap=False), 1,0, 1,2)
      frmLayout.addWidget(QRichLabel('      To ' + outputStr, doWrap=False),  2,0, 1,2)
      frmLayout.addWidget(QRichLabel('      Total <b>%s</b> BTC %s'%(outStr,feeStr), doWrap=False),  3,0, 1,2)
      frm.setLayout(frmLayout)

      lblFinalConfirm = QLabel('Are you sure you want to execute this transaction?')

      bbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                              QDialogButtonBox.Cancel)
      self.connect(bbox, SIGNAL('accepted()'), self.accept)
      self.connect(bbox, SIGNAL('rejected()'), self.reject)

      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap('img/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

      layout = QHBoxLayout()
      layout.addWidget(lblWarnImg)
      layout.addWidget(makeLayoutFrame('Vert',[lblQuestion, frm, lblFinalConfirm, bbox]))
      self.setLayout(layout)

      self.setWindowTitle('Confirm Sweep')



#############################################################################
class DlgImportWallet(QDialog):
   def __init__(self, parent=None, main=None):
      super(DlgImportWallet, self).__init__(parent)
      self.setAttribute(Qt.WA_DeleteOnClose)
      self.parent = parent
      self.main   = main

      lblImportDescr = QLabel('Chose the wallet import source:')
      self.btnImportFile  = QPushButton("Import Armory wallet from &file")
      self.btnImportPaper = QPushButton("Restore from &paper backup")
      self.btnMigrate     = QPushButton("Migrate wallet.dat (main Bitcoin App)")

      self.btnImportFile.setMinimumWidth(300)

      self.connect( self.btnImportFile,  SIGNAL("clicked()"), self.acceptImport)
      self.connect( self.btnImportPaper, SIGNAL('clicked()'), self.acceptPaper)
      self.connect( self.btnMigrate,     SIGNAL('clicked()'), self.acceptMigrate)

      ttip1 = createToolTipObject('Import an existing Armory wallet, usually with a '
                                  '*.wallet extension.  Any wallet that you import will ' 
                                  'be copied into your settings directory, and maintained '
                                  'there.  The original wallet file will not be touched.')

      ttip2 = createToolTipObject('If you have previously made a paper backup of '
                                  'a wallet, you can manually enter the wallet '
                                  'data into Armory to recover the wallet.')

      ttip3 = createToolTipObject('Migrate all your wallet.dat addresses '
                                  'from the regular Bitcoin client to an Armory '
                                  'wallet.')

      w,h = relaxedSizeStr(ttip1, '(?)') 
      for ttip in (ttip1, ttip2):
         ttip.setMaximumSize(w,h)
         ttip.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

      # Set up the layout
      layout = QGridLayout()
      layout.addWidget(lblImportDescr,      0,0, 1, 2)
      layout.addWidget(self.btnImportFile,  1,0, 1, 2); layout.addWidget(ttip1, 1,2,1,1)
      layout.addWidget(self.btnImportPaper, 2,0, 1, 2); layout.addWidget(ttip2, 2,2,1,1)
      layout.addWidget(self.btnMigrate,     3,0, 1, 2); layout.addWidget(ttip3, 3,2,1,1)

      if self.main.usermode in (USERMODE.Advanced, USERMODE.Developer):
         lbl = QLabel('You can manually add wallets to armory by copying them '
                      'into your application directory:  ' + ARMORY_HOME_DIR)
         lbl.setWordWrap(True)
         layout.addWidget(lbl, 4,0, 1, 2); 
         if self.main.usermode==USERMODE.Developer:
            lbl = QLabel('Any files in the application data directory above are '
                         'used in the application if the first 8 bytes of the file '
                         'are "\\xbaWALLET\\x00".  Wallets in this directory can be '
                         'ignored by adding an <i>Excluded_Wallets</i> option to the '
                         'ArmorySettings.txt file.  Reference by full path or wallet ID.')
            lbl.setWordWrap(True)
            layout.addWidget(lbl, 5,0, 1, 2); 

      btnCancel = QPushButton('Cancel')
      self.connect(btnCancel, SIGNAL('clicked()'), self.reject)
      layout.addWidget(btnCancel, 6,0, 1,1);
      
      self.setMinimumWidth(400)

      self.setLayout(layout)
      self.setWindowTitle('Import Wallet')
      

   def acceptImport(self):
      self.importType_file    = True
      self.importType_paper   = False
      self.importType_migrate = False
      self.accept()

      
   def acceptPaper(self):
      self.importType_file    = False
      self.importType_paper   = True
      self.importType_migrate = False
      self.accept()
      
   def acceptMigrate(self):
      self.importType_file    = False
      self.importType_paper   = False
      self.importType_migrate = True
      self.accept()

#############################################################################
class DlgMigrateSatoshiWallet(QDialog):
   def __init__(self, parent=None, main=None):
      super(DlgMigrateSatoshiWallet, self).__init__(parent)

      self.parent = parent
      self.main   = main

      lblDescr = QRichLabel( \
         'Specify the location of your regular Bitcoin wallet (wallet.dat) '
         'to be migrated into an Armory wallet.  All private '
         'keys will be imported, giving you full access to those addresses, as '
         'if Armory had generated them natively.'
         '<br><br>'
         '<b>NOTE:</b> It is strongly recommended that all '
         'Bitcoin addresses be used in only one program at a time.  If you '
         'import your entire wallet.dat, it is recommended to stop using the '
         'regular Bitcoin client, and only use Armory to send transactions.  '
         'Armory developers will not be responsible for coins getting "locked" '
         'or "stuck" due to multiple applications attempting to spend coins '
         'from the same addresses.')

      lblSatoshiWlt = QRichLabel('Wallet File to be Migrated (typically ' +
                                 os.path.join(BTC_HOME_DIR, 'wallet.dat') + ')', doWrap=False)
      ttipWlt = createToolTipObject(\
         'This is the wallet file used by the standard Bitcoin client from '
         'bitcoin.org.  It contains all the information needed for Armory to '
         'know how to access the Bitcoins maintained by that program')
      self.txtWalletPath = QLineEdit()



      self.chkAllKeys = QCheckBox('Include Address Pool (unused keys)')
      ttipAllKeys = createToolTipObject( \
         'The wallet.dat file typically '
         'holds a pool of 100 addresses beyond the ones you ever used. '
         'These are the next 100 addresses to be used by the main Bitcoin '
         'client for the next 100 transactions.  '
         'If you are planning to switch to Armory exclusively, you will not '
         'need these addresses')

      self.chkAllKeys.setChecked(True)
      if self.main.usermode in (USERMODE.Standard,):
         self.chkAllKeys.setVisible(False)
         self.ttipAllKeys.setVisible(False)

      btnGetFilename = QPushButton('Find...')
      self.connect(btnGetFilename, SIGNAL('clicked()'), self.getSatoshiFilename)

      defaultWalletPath = os.path.join(BTC_HOME_DIR,'wallet.dat')
      if os.path.exists(defaultWalletPath):
         self.txtWalletPath.setText(defaultWalletPath)

      buttonBox = QDialogButtonBox()
      self.btnAccept = QPushButton("Import")
      self.btnReject = QPushButton("Cancel")
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.execMigrate)
      self.connect(self.btnReject, SIGNAL('clicked()'), self.reject)
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnReject, QDialogButtonBox.RejectRole)


      # Select the wallet into which you want to import
      lblWltDest = QRichLabel('Migrate Addresses to which Wallet?', doWrap=False)
      self.wltidlist = [''] 
      self.lstWallets = QListWidget()
      self.lstWallets.addItem(QListWidgetItem('New Wallet...'))
      for wltID in self.main.walletIDList:
         wlt = self.main.walletMap[wltID]
         wlttype = determineWalletType(self.main.walletMap[wltID], self.main)[0]
         if wlttype in (WLTTYPES.WatchOnly, WLTTYPES.Offline):
            continue
         self.lstWallets.addItem( \
                QListWidgetItem('%s (%s)' % (wlt.labelName, wltID) ))
         self.wltidlist.append(wltID)
      self.lstWallets.setCurrentRow(0)
      self.connect(self.lstWallets, SIGNAL('currentRowChanged(int)'), self.wltChange)


      self.lblDescrNew = QRichLabel( '' )
      self.lblDescrNew.setAlignment(Qt.AlignTop)
      self.wltChange(0)
      

      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(lblDescr)
      dlgLayout.addWidget(HLINE())
      dlgLayout.addWidget(makeHorizFrame([lblSatoshiWlt, ttipWlt, 'Stretch']))
      dlgLayout.addWidget(makeHorizFrame([self.txtWalletPath, btnGetFilename]))
      dlgLayout.addWidget(makeHorizFrame([self.chkAllKeys, ttipAllKeys, 'Stretch']))
      dlgLayout.addWidget(HLINE())
      dlgLayout.addWidget(makeHorizFrame([lblWltDest, 'Stretch']))
      dlgLayout.addWidget(makeHorizFrame([self.lstWallets, self.lblDescrNew,'Stretch']))
      dlgLayout.addWidget(HLINE())
      dlgLayout.addWidget(buttonBox)

      self.setLayout(dlgLayout)

      self.setMinimumWidth(500)
      self.setWindowTitle('Migrate Satoshi Wallet')
      self.setWindowIcon(QIcon( self.main.iconfile))


   def getSatoshiFilename(self):
      # Temporarily reset the "LastDir" to where the default wallet.dat is
      prevLastDir = self.main.settings.get('LastDirectory')
      self.main.settings.set('LastDirectory', BTC_HOME_DIR)
      satoshiWltFile = self.main.getFileLoad('Load Bitcoin Wallet File', \
                                             ['Bitcoin Wallets (*.dat)'])
      self.main.settings.set('LastDirectory', prevLastDir)
      if len(str(satoshiWltFile))>0:
         self.txtWalletPath.setText(satoshiWltFile)
      

   def wltChange(self, row):
      if row==0:
         self.lblDescrNew.setText( \
           'If your wallet.dat is encrypted, the new Armory wallet will also '
           'be encrypted, and with the same passphrase.  If your wallet.dat '
           'is not encrypted, neither will the new Armory wallet.  Encryption '
           'can always be added, changed or removed on any wallet.')
      else:
         self.lblDescrNew.setText( '' )

   def execMigrate(self):
      satoshiWltFile = str(self.txtWalletPath.text())
      if not os.path.exists(satoshiWltFile):
         QMessageBox.critical(self, 'File does not exist!', \
            'The specified file does not exist:\n\n' + satoshiWltFile,
            QMessageBox.Ok)
         return

      selectedRow = self.lstWallets.currentRow()
      toWalletID = None
      if selectedRow>0:
         toWalletID = self.wltidlist[selectedRow]
         


      # Critical to avoid wallet corruption!!
      base,fn = os.path.split(satoshiWltFile)
      nm,ext = os.path.splitext(fn)
      satoshiWltFileCopy = os.path.join(ARMORY_HOME_DIR, nm+'_temp_copy'+ext)
      shutil.copy(satoshiWltFile, satoshiWltFileCopy)
      if not os.path.exists(satoshiWltFileCopy):
         raise FileExistsError, 'There was an error creating a copy of wallet.dat'

      # KeyList is [addrB58, privKey, usedYet, acctName]
      # This block will not only decrypt the Satoshi wallet, but also catch
      # if the user specified a wallet.dat for a different network!
      keyList = []
      satoshiPassphrase = None
      satoshiWltIsEncrypted  = checkSatoshiEncrypted(satoshiWltFileCopy)

      if not satoshiWltIsEncrypted:
         try:
            keyList = extractSatoshiKeys(satoshiWltFileCopy)
         except NetworkIDError:
            QMessageBox.critical(self, 'Wrong Network!', \
               'The specified wallet.dat file is for a different network! '
               '(you are on the ' + NETWORKS[ADDRBYTE] + ')', \
               QMessageBox.Ok)
            return
      else:
         correctPassphrase = False
         firstAsk = True
         while not correctPassphrase:
            # Loop until we get a valid passphrase
            redText = ''
            if not firstAsk:
               redText = '<font color="red">Incorrect passphrase.</font><br><br>' 
            firstAsk = False

            dlg = DlgGenericGetPassword( \
                redText + 'The wallet.dat file you specified is encrypted.  '
                'Please provide the passphrase to decrypt it.', self, self.main)

            if not dlg.exec_():
               return
            else:
               satoshiPassphrase = SecureBinaryData(str(dlg.edtPasswd.text()))
               try:
                  keyList = extractSatoshiKeys(satoshiWltFileCopy, satoshiPassphrase)
                  correctPassphrase = True
               except EncryptionError:
                  pass
               except NetworkIDError:
                  QMessageBox.critical(self, 'Wrong Network!', \
                     'The specified wallet.dat file is for a different network! '
                     '(you are on the ' + NETWORKS[ADDRBYTE] + ')', \
                     QMessageBox.Ok)
                  return

      # We're done accessing the file, delete the
      os.remove(satoshiWltFileCopy)
      
      if not self.chkAllKeys.isChecked():
         keyList = filter(lambda x: x[2], keyList)


      # Warn about addresses that would be duplicates.
      # This filters the list down to addresses already in a wallet that isn't selected
      # Addresses already in the selected wallet will simply be skipped, no need to 
      # do anything about that
      addr_to_wltID = lambda a: self.main.getWalletForAddr160(addrStr_to_hash160(a))
      allWltList = [[addr_to_wltID(k[0]), k[0]] for k in keyList]
      dupeWltList = filter(lambda a: (len(a[0])>0 and a[0]!=toWalletID), allWltList)

      if len(dupeWltList)>0:
         dlg = DlgDuplicateAddr([d[1].ljust(40)+d[0] for d in dupeWltList], self, self.main)
         didAccept = dlg.exec_()
         if not didAccept or dlg.doCancel:
            return
   
         if dlg.newOnly:
            dupeAddrList = [a[1] for a in dupeWltList]
            keyList = filter(lambda x: (x[0] not in dupeAddrList), keyList)
         elif dlg.takeAll:
            pass # we already have duplicates in the list, leave them
      

      # Confirm import
      addrList = [k[0].ljust(40)+k[3] for k in keyList]
      dlg = DlgConfirmBulkImport(addrList, toWalletID, self, self.main)
      if not dlg.exec_():
         return
         
      # Okay, let's do it!  Get a wallet, unlock it if necessary, create if desired
      wlt = None
      if toWalletID==None:
         lblShort = 'Migrated wallet.dat'
         lblLong  = 'Wallet created to hold addresses from the regular Bitcoin wallet.dat.'

         if not satoshiPassphrase:
            wlt = PyBtcWallet().createNewWallet(    \
                               withEncrypt=False,   \
                               shortLabel=lblShort, \
                               longLabel=lblLong)
                                                     
         else:
            lblLong += ' (encrypted using same passphrase as the original wallet)'
            wlt = PyBtcWallet().createNewWallet( \
                               withEncrypt=True, \
                               securePassphrase=satoshiPassphrase, \
                               shortLabel=lblShort, \
                               longLabel=lblLong)
            wlt.unlock(securePassphrase=satoshiPassphrase)


      else:
         wlt = self.main.walletMap[toWalletID]
         if wlt.useEncryption and wlt.isLocked:
            # Target wallet is encrypted...
            unlockdlg = DlgUnlockWallet(wlt, self, self.main, 'Unlock Wallet to Import')
            if not unlockdlg.exec_():
               QMessageBox.critical(self, 'Wallet is Locked', \
                  'Cannot import private keys without unlocking wallet!', \
                  QMessageBox.Ok)
               return

      
      nImport = 0
      nError  = 0
      for i,key4 in enumerate(keyList):
         addrB58, sbdKey, isUsed, addrName = key4[:]
         try:
            a160 = addrStr_to_hash160(addrB58)
            wlt.importExternalAddressData(privKey=sbdKey)
            cmt = 'Imported #%03d'%i
            if len(addrName)>0:
               cmt += ': %s' % addrName
            wlt.setComment(a160, cmt)
            nImport += 1
         except Exception,msg:
            print '***ERROR importing:', addrB58
            print '         Error Msg:', msg
            nError += 1


      restartMsg = '<br><br>Restart Armory to guarantee that balances are computed correctly.'
      #restartMsg = ''
      #if self.main.isOnline:
         
      if nImport==0:
         MsgBoxCustom(MSGBOX.Error,'Error!', 'Failed:  No addresses could be imported. '
            'Please check the logfile (ArmoryQt.exe.log) or the console output '
            'for information about why it failed (and email alan.reiner@gmail.com '
            'for help fixing the problem).')
      else:
         if nError == 0:
            MsgBoxCustom(MSGBOX.Good, 'Success!', \
               'Success: %d private keys were imported into your wallet.  %s' % \
                                                            (nImport, restartMsg))
         else:
            MsgBoxCustom(MSGBOX.Warning, 'Partial Success!', \
               '%d private keys were imported into your wallet, but there was '
               'also %d addresses that could not be imported (see console '
               'or log file for more information).  It is safe to try this '
               'operation again: all addresses previously imported will be '
               'skipped. %s' % (nImport, nError, restartMsg))
      self.accept()
      
         
         

         
            
         


#############################################################################
class DlgConfirmBulkImport(QDialog):
   def __init__(self, addrList, wltID, parent=None, main=None):
      super(DlgConfirmBulkImport, self).__init__(parent)

      self.parent = parent
      self.main   = main
      self.wltID  = wltID

      if len(addrList)==0:
         QMessageBox.warning(self, 'No Addresses to Import', \
           'There are no addresses to import!', QMessageBox.Ok)
         self.reject()

   
      walletDescr = 'a new wallet'
      if not wltID==None:
         wlt = self.main.walletMap[wltID]
         walletDescr = 'wallet, <b>%s</b> (%s)' % (wltID, wlt.labelName)
      lblDescr = QRichLabel( \
         'You are about to import <b>%d</b> addresses into %s.<br><br> '
         'The following is a list of addresses to be imported:' % \
                                              (len(addrList), walletDescr))

      fnt = GETFONT('Fixed',10)
      w,h = tightSizeNChar(fnt, 100)
      txtDispAddr = QTextEdit()
      txtDispAddr.setFont(fnt)
      txtDispAddr.setReadOnly(True)
      txtDispAddr.setMinimumWidth( min(w, 700))
      txtDispAddr.setMinimumHeight(16.2*h)
      txtDispAddr.setText( '\n'.join(addrList) )

      buttonBox = QDialogButtonBox()
      self.btnAccept = QPushButton("Import")
      self.btnReject = QPushButton("Cancel")
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.accept)
      self.connect(self.btnReject, SIGNAL('clicked()'), self.reject)
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnReject, QDialogButtonBox.RejectRole)

      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(lblDescr)
      dlgLayout.addWidget(txtDispAddr)
      dlgLayout.addWidget(buttonBox)
      self.setLayout(dlgLayout)

      self.setWindowTitle('Confirm Import')
      self.setWindowIcon(QIcon( self.main.iconfile))


#############################################################################
class DlgDuplicateAddr(QDialog):
   def __init__(self, addrList, wlt, parent=None, main=None):
      super(DlgDuplicateAddr, self).__init__(parent)

      self.parent = parent
      self.main   = main
      self.wlt    = wlt 
      self.doCancel = True
      self.takeAll  = False
      self.newOnly  = False

      if len(addrList)==0:
         QMessageBox.warning(self, 'No Addresses to Import', \
           'There are no addresses to import!', QMessageBox.Ok)
         self.reject()

      lblDescr = QRichLabel( \
         '<font color="red">Duplicate addresses detected!</font> '
         'The following addresses already exist in other Armory wallets:')

      fnt = GETFONT('Fixed',8)
      w,h = tightSizeNChar(fnt, 50)
      txtDispAddr = QTextEdit()
      txtDispAddr.setFont(fnt)
      txtDispAddr.setReadOnly(True)
      txtDispAddr.setMinimumWidth(w)
      txtDispAddr.setMinimumHeight(8.2*h)
      txtDispAddr.setText( '\n'.join(addrList) )

      lblWarn = QRichLabel( \
         'If you continue, any funds in this '
         'address will be double-counted, causing your total balance '
         'to appear artificially high, and any transactions involving '
         'this address will confusingly appear in multiple wallets.'
         '\n\nWould you like to import these addresses anyway?')

      buttonBox = QDialogButtonBox()
      self.btnTakeAll = QPushButton("Import With Duplicates")
      self.btnNewOnly = QPushButton("Import New Addresses Only")
      self.btnCancel  = QPushButton("Cancel")
      self.connect(self.btnTakeAll, SIGNAL('clicked()'), self.doTakeAll)
      self.connect(self.btnNewOnly, SIGNAL('clicked()'), self.doNewOnly)
      self.connect(self.btnCancel,  SIGNAL('clicked()'), self.reject)
      buttonBox.addButton(self.btnTakeAll, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnNewOnly, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel,  QDialogButtonBox.RejectRole)

      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(lblDescr)
      dlgLayout.addWidget(txtDispAddr)
      dlgLayout.addWidget(buttonBox)
      self.setLayout(dlgLayout)

      self.setWindowTitle('Duplicate Addresses')

   def doTakeAll(self):
      self.doCancel = False
      self.takeAll  = True
      self.newOnly  = False
      self.accept()

   def doNewOnly(self):
      self.doCancel = False
      self.takeAll  = False
      self.newOnly  = True
      self.accept()


#############################################################################
class DlgAddressInfo(QDialog):
   def __init__(self, wlt, addr160, parent=None, main=None, mode=None):
      super(DlgAddressInfo, self).__init__(parent)

      self.parent = parent
      self.main   = main
      self.wlt    = wlt
      self.addr   = self.wlt.getAddrByHash160(addr160)


      self.addrLedger = wlt.getAddrTxLedger(addr160)
      self.addrLedger2 = [[wlt.uniqueIDB58, le] for le in self.addrLedger]
      self.ledgerTable = self.main.convertLedgerToTable(self.addrLedger2)
      self.ledgerTable.sort(key=lambda x: x[LEDGERCOLS.UnixTime])


      self.mode = mode
      if mode==None:
         if main==None:
            self.mode = USERMODE.Standard
         else:
            self.mode = self.main.usermode
      

      dlgLayout = QGridLayout()
      cppAddr = self.wlt.cppWallet.getAddrByHash160(addr160)
      addrStr = self.addr.getAddrStr()



      lblDescr = QLabel('Information for address:  ' + addrStr)
      
      frmInfo = QFrame()
      frmInfo.setFrameStyle(STYLE_RAISED)
      frmInfoLayout = QGridLayout()

      lbls = []

      # Hash160
      if mode in (USERMODE.Advanced, USERMODE.Developer):
         bin25   = base58_to_binary(addrStr)
         lbls.append([])
         lbls[-1].append( createToolTipObject( 'This is the computer-readable form of the address'))
         lbls[-1].append( QRichLabel('<b>Public Key Hash</b>') )
         h160Str = binary_to_hex(bin25[1:-4])
         if mode==USERMODE.Developer:
            network = binary_to_hex(bin25[:1    ])
            hash160 = binary_to_hex(bin25[ 1:-4 ])
            addrChk = binary_to_hex(bin25[   -4:])
            h160Str += '%s (Network: %s / Checksum: %s)' % (hash160, network, addrChk)
         lbls[-1].append( QLabel(h160Str))



      lbls.append([])
      lbls[-1].append( QLabel(''))
      lbls[-1].append( QRichLabel('<b>Address:</b>'))
      lbls[-1].append( QLabel( addrStr))


      lbls.append([])
      lbls[-1].append( createToolTipObject( 
         'Address type is either <i>Imported</i> or <i>Permanent</i>.  '
         '<i>Permanent</i> '  
         'addresses are part of base wallet, and are protected by printed '
         'paper backups, regardless of when the backup was performed.  '
         'Imported addresses are only protected by digital backups, or manually '
         'printing the individual keys list, and only if it was backed up '
         '<i>after</i> the keys were imported.'))
           
      lbls[-1].append( QRichLabel('<b>Address Type:</b>'))
      if self.addr.chainIndex==-2:
         lbls[-1].append( QLabel('Imported') )
      else:
         lbls[-1].append( QLabel('Permanent') )


      # Current Balance of address
      lbls.append([])
      lbls[-1].append( createToolTipObject( 
            'This is the current <i>spendable</i> balance of this address, '
            'not including zero-confirmation transactions from others.'))
      lbls[-1].append( QRichLabel('<b>Current Balance</b>') )
      balStr = coin2str(cppAddr.getSpendableBalance(), maxZeros=1)
      if cppAddr.getSpendableBalance()>0:
         lbls[-1].append( QRichLabel( '<font color="green">' + balStr.strip() + '</font> BTC' ))
      else:   
         lbls[-1].append( QRichLabel( balStr.strip() + ' BTC'))


      # Number of transactions
      txHashes = set() 
      for le in self.addrLedger:
         txHashes.add(le.getTxHash())
         
      lbls.append([])
      lbls[-1].append( createToolTipObject( 
            'The total number of transactions in which this address was involved'))
      lbls[-1].append( QRichLabel('<b>Transaction Count:</b>') )
      lbls[-1].append( QLabel(str(len(txHashes))))
      
            



      for i in range(len(lbls)):
         for j in range(1,3):
            lbls[i][j].setTextInteractionFlags( Qt.TextSelectableByMouse | \
                                                Qt.TextSelectableByKeyboard)
         for j in range(3):
            frmInfoLayout.addWidget(lbls[i][j], i,j, 1,1)

      frmInfo.setLayout(frmInfoLayout)
      dlgLayout.addWidget(frmInfo, 0,0, 1,1)


      ### Set up the address ledger
      self.ledgerModel = LedgerDispModelSimple(self.ledgerTable, self, self.main)
      self.ledgerView = QTableView()
      self.ledgerView.setModel(self.ledgerModel)
      self.ledgerView.setItemDelegate(LedgerDispDelegate(self))

      self.ledgerView.hideColumn(LEDGERCOLS.isOther)
      self.ledgerView.hideColumn(LEDGERCOLS.UnixTime)
      self.ledgerView.hideColumn(LEDGERCOLS.WltID)
      self.ledgerView.hideColumn(LEDGERCOLS.WltName)
      self.ledgerView.hideColumn(LEDGERCOLS.TxHash)
      self.ledgerView.hideColumn(LEDGERCOLS.toSelf)
      self.ledgerView.hideColumn(LEDGERCOLS.DoubleSpend)

      self.ledgerView.setSelectionBehavior(QTableView.SelectRows)
      self.ledgerView.setSelectionMode(QTableView.SingleSelection)
      self.ledgerView.horizontalHeader().setStretchLastSection(True)
      self.ledgerView.verticalHeader().setDefaultSectionSize(20)
      self.ledgerView.verticalHeader().hide()
      self.ledgerView.setMinimumWidth(650)
      dateWidth = tightSizeStr(self.ledgerView, '_9999-Dec-99 99:99pm__')[0]
      initialColResize(self.ledgerView, [20, 0, dateWidth, 72, 0, 0.45, 0.3])

      ttipLedger = createToolTipObject( \
            'Unlike the wallet-level ledger, this table shows every '
            'transaction <i>input</i> and <i>output</i> as a separate entry.  '
            'Therefore, there may be multiple entries for a single transaction, '
            'which will happen if money was sent-to-self (explicitly, or as '
            'the change-back-to-self address).')
      lblLedger = QLabel('All Address Activity:')

      lblstrip = makeLayoutFrame('Horiz', [lblLedger, ttipLedger, 'Stretch'])
      frmLedger = makeLayoutFrame('Vert', [lblstrip, self.ledgerView])
      dlgLayout.addWidget(frmLedger, 1,0,  1,1)


      # Now add the right-hand-side option buttons
      lbtnCopyAddr = QLabelButton('Copy Address to Clipboard')
      lbtnMkPaper  = QLabelButton('Make Paper Backup')
      lbtnViewKeys = QLabelButton('View Address Keys')
      lbtnSweepA   = QLabelButton('Sweep Address')
      lbtnDelete   = QLabelButton('Delete Address')
      lbtnUnspent  = QLabelButton('View unspent TxOuts')

      self.connect(lbtnCopyAddr, SIGNAL('clicked()'), self.copyAddr)
      self.connect(lbtnMkPaper,  SIGNAL('clicked()'), self.makePaper)
      self.connect(lbtnViewKeys, SIGNAL('clicked()'), self.viewKeys)
      self.connect(lbtnSweepA,   SIGNAL('clicked()'), self.sweepAddr)
      self.connect(lbtnDelete,   SIGNAL('clicked()'), self.deleteAddr)
      self.connect(lbtnUnspent,  SIGNAL('clicked()'), self.viewUnspent)

      optFrame = QFrame()
      optFrame.setFrameStyle(STYLE_SUNKEN)
      optLayout = QVBoxLayout()

      hasPriv = self.addr.hasPrivKey()
      adv = (self.main.usermode in (USERMODE.Advanced, USERMODE.Developer))
      watch = self.wlt.watchingOnly

      #def createVBoxSeparator():
         #frm = QFrame()
         #frm.setFrameStyle(QFrame.HLine | QFrame.Plain)
         #return frm
      #if hasPriv and adv:  optLayout.addWidget(createVBoxSeparator())

      self.lblCopied = QRichLabel('')
      self.lblCopied.setMinimumHeight(tightSizeNChar(self.lblCopied, 1)[1])
      if True:           optLayout.addWidget(lbtnCopyAddr)
      if adv:            optLayout.addWidget(lbtnViewKeys)

      if not watch:      optLayout.addWidget(lbtnSweepA)
      #if adv:            optLayout.addWidget(lbtnDelete)
      #if adv:            optLayout.addWidget(lbtnUnspent)

      if False:          optLayout.addWidget(lbtnMkPaper)  
      if True:           optLayout.addStretch()
      if True:           optLayout.addWidget(self.lblCopied)

      self.lblLedgerWarning = QRichLabel( \
         'NOTE:  The ledger on the left is for a <i>single address</i>, '
         'which shows each transaction <i><b>input</b></i> and '
         '<i><b>output</b></i> separately. A single transaction usually '
         'consists of many inputs and outputs '
         'spread across multiple addresses, which <i>together</i> '
         'add up to the transaction value you would recognize.  ')
      optLayout.addWidget(self.lblLedgerWarning)

      optLayout.addStretch()
      optFrame.setLayout(optLayout)
      
      rightFrm = makeLayoutFrame('Vert', [QLabel('Available Actions:'), optFrame])
      dlgLayout.addWidget(rightFrm,  0,1, 2,1)

      btnGoBack = QPushButton('<<< Go Back')
      self.connect(btnGoBack, SIGNAL('clicked()'), self.reject)
      bottomStrip = makeLayoutFrame('Horiz', [btnGoBack, 'Stretch'])
      dlgLayout.addWidget(bottomStrip,  2,0, 1,2)

      self.setLayout(dlgLayout)
      self.setWindowTitle('Address Information')


   def copyAddr(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.addr.getAddrStr())
      self.lblCopied.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      self.lblCopied.setText('<i>Copied!</i>')

   def makePaper(self):
      pass

   def viewKeys(self):
      if self.wlt.useEncryption and self.wlt.isLocked:
         unlockdlg = DlgUnlockWallet(self.wlt, self, self.main, 'View Private Keys')
         if not unlockdlg.exec_():
            QMessageBox.critical(self, 'Wallet is Locked', \
               'Key information will not include the private key data.', \
               QMessageBox.Ok)

      addr = self.addr.copy()
      dlg = DlgShowKeys(addr, self, self.main)
      dlg.exec_()
   

   def sweepAddr(self):
      
      if self.wlt.useEncryption and self.wlt.isLocked:
         unlockdlg = DlgUnlockWallet(self.wlt, self, self.main, 'Sweep Address')
         if not unlockdlg.exec_():
            QMessageBox.critical(self, 'Wallet is Locked', \
               'Cannot sweep an address while its keys are locked.', \
               QMessageBox.Ok)
            return

      addrToSweep = self.addr.copy()
      targAddr160 = self.wlt.getNextUnusedAddress().getAddr160()
      finishedTx, outVal, fee = self.main.createSweepAddrTx(addrToSweep, targAddr160)

      if outVal<=fee:
         QMessageBox.critical(self, 'Cannot sweep',\
         'You cannot sweep the funds from this address, because the '
         'transaction fee would be equal to or greater than the amount '
         'swept.', QMessageBox.Ok)
         return

      if outVal==0:
         QMessageBox.critical(self, 'Nothing to do', \
         'This address does not contain any funds.  There is nothing to sweep.', \
         QMessageBox.Ok)
         return

      QMessageBox.information(self, 'Sweep Address Funds', \
      '<i>Sweeping</i> an address will transfer all funds from the selected '
      'address to another address in your wallet.  This action is not normally '
      'necessary because it is rare for one address in a wallet to be compromised '
      'but not the others.  \n\n'
      'If you believe that your entire wallet has been compromised, '
      'you should instead send all the funds from this wallet to another address '
      'or wallet.', QMessageBox.Ok)
      
      # Finally, if we got here, we're ready to broadcast!
      dispIn  = 'address <b>%s</b>' % addrToSweep.getAddrStr()
      dispOut = 'wallet <b>"%s"</b> (%s) ' % (self.wlt.labelName, self.wlt.uniqueIDB58)
      if DlgVerifySweep(dispIn, dispOut, outVal, fee).exec_():
         #if self.wlt.useEncryption and self.wlt.isLocked:
            #unlockdlg = DlgUnlockWallet(self.wlt, self, self.main, 'Sweep Address')
            #if not unlockdlg.exec_():
               #QMessageBox.critical(self, 'Wallet is Locked', \
                  #'Cannot sweep an address while its keys are locked.', \
                  #QMessageBox.Ok)
               #return
         self.main.broadcastTransaction(finishedTx, dryRun=False)

   def deleteAddr(self):
      pass
   def viewUnspent(self):
      pass


#############################################################################
class DlgShowKeys(QDialog):

   def __init__(self, addr, parent=None, main=None):
      super(DlgShowKeys, self).__init__(parent)

      self.parent = parent
      self.main   = main
      self.addr   = addr

      
      lblWarn = QRichLabel('')
      plainPriv = False
      if addr.binPrivKey32_Plain.getSize()>0:
         plainPriv = True
         lblWarn = QRichLabel( \
            '<font color="red"><b>Warning:</b> the unencrypted private keys '
            'for this address are shown below.  They are "private" because '
            'anyone who obtains them can spend the money held '
            'by this address.  Please protect this information the '
            'same as you protect your wallet.</font>')
      warnFrm = makeLayoutFrame('Horiz', [lblWarn])

      endianness = self.main.settings.getSettingOrSetDefault('PrefEndian', BIGENDIAN)
      estr = 'BE' if endianness==BIGENDIAN else 'LE'
      def formatBinData(binStr, endian=LITTLEENDIAN):
         binHex = binary_to_hex(binStr)
         if endian!=LITTLEENDIAN:
            binHex = hex_switchEndian(binHex)   
         binHexPieces = [binHex[i:i+8] for i in range(0, len(binHex), 8)]
         return ' '.join(binHexPieces)


      lblDescr = QRichLabel('Key Data for address: <b>%s</b>' % self.addr.getAddrStr())

      lbls = []
      #lbls.append([])
      #lbls[-1].append(QLabel(''))
      #lbls[-1].append(QRichLabel('<b>Address:</b>'))
      #lbls[-1].append(QLabel(addr.getAddrStr()))


      lbls.append([])
      binKey = self.addr.binPrivKey32_Plain.toBinStr()
      lbls[-1].append(createToolTipObject( \
            'The raw form of the private key for this address.  It is '
            '32-bytes of randomly generated data'))
      lbls[-1].append(QRichLabel('Private Key (hex,%s):' % estr))
      if not addr.hasPrivKey():
         lbls[-1].append(QRichLabel('<i>[[ No Private Key in Watching-Only Wallet ]]</i>'))
      elif plainPriv:
         lbls[-1].append( QLabel( formatBinData(binKey) ) )
      else:
         lbls[-1].append(QRichLabel('<i>[[ ENCRYPTED ]]</i>'))

      if plainPriv:
         lbls.append([])
         lbls[-1].append(createToolTipObject( \
               'This is a more compact form of the private key, and includes '
               'a checksum for error detection.'))
         lbls[-1].append(QRichLabel('Private Key (Base58):'))
         b58Key = '\x80' + binKey
         b58Key = binary_to_base58(b58Key + computeChecksum(b58Key))
         lbls[-1].append( QLabel(' '.join([b58Key[i:i+6] for i in range(0, len(b58Key), 6)])))
         
      

      lbls.append([])
      lbls[-1].append(createToolTipObject( \
               'The raw public key data.  This is the X-coordinate of '
               'the Elliptic-curve public key point.'))
      lbls[-1].append(QRichLabel('Public Key X (%s):' % estr))
      lbls[-1].append(QRichLabel(formatBinData(self.addr.binPublicKey65.toBinStr()[1:1+32])))
      

      lbls.append([])
      lbls[-1].append(createToolTipObject( \
               'The raw public key data.  This is the Y-coordinate of '
               'the Elliptic-curve public key point.'))
      lbls[-1].append(QRichLabel('Public Key Y (%s):' % estr))
      lbls[-1].append(QRichLabel(formatBinData(self.addr.binPublicKey65.toBinStr()[1+32:1+32+32])))


      bin25   = base58_to_binary(self.addr.getAddrStr())
      network = binary_to_hex(bin25[:1    ])
      hash160 = binary_to_hex(bin25[ 1:-4 ])
      addrChk = binary_to_hex(bin25[   -4:])
      h160Str = '%s (Network: %s / Checksum: %s)' % (hash160, network, addrChk)

      lbls.append([])
      lbls[-1].append(createToolTipObject( \
               'This is the hexadecimal version if the address string'))
      lbls[-1].append(QRichLabel('Public Key Hash:'))
      lbls[-1].append(QLabel(h160Str))

      frmKeyData = QFrame()
      frmKeyData.setFrameStyle(STYLE_RAISED)
      frmKeyDataLayout = QGridLayout()


      # Now set the label properties and jam them into an information frame
      for row,lbl3 in enumerate(lbls):
         lbl3[1].setFont(GETFONT('Var'))
         lbl3[2].setFont(GETFONT('Fixed'))
         lbl3[2].setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                         Qt.TextSelectableByKeyboard)
         lbl3[2].setWordWrap(False)

         for j in range(3):
            frmKeyDataLayout.addWidget(lbl3[j], row, j)

      
      frmKeyData.setLayout(frmKeyDataLayout)

      bbox = QDialogButtonBox(QDialogButtonBox.Ok)
      self.connect(bbox, SIGNAL('accepted()'), self.accept)

      
      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(lblWarn)
      dlgLayout.addWidget(lblDescr)
      dlgLayout.addWidget(frmKeyData)
      dlgLayout.addWidget(bbox)
   
      
      self.setLayout(dlgLayout)
      self.setWindowTitle('Address Key Information')


#############################################################################
class DlgIntroMessage(QDialog):
   def __init__(self, parent=None, main=None):
      super(DlgIntroMessage, self).__init__(parent)

      self.parent = parent
      self.main   = main  

      lblInfoImg = QLabel()
      lblInfoImg.setPixmap(QPixmap('img/MsgBox_info48.png'))
      lblInfoImg.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
      lblInfoImg.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      lblInfoImg.setMaximumWidth(50)

      lblWelcome = QRichLabel('<b>Welcome to Armory!</b>')
      lblWelcome.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWelcome.setFont(GETFONT('Var', 14))
      lblSlogan  = QRichLabel('<i>The most advanced Bitcoin Client on Earth!</i>')
      lblSlogan.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      lblDescr = QRichLabel( \
         '<b>You are about to use the most feature-packed, easiest-to-use '
         'Bitcoin client in existence</b>.  But please remember, this software '
         'is still <i>alpha</i>, which means that it should not be '
         'trusted to handle any serious amounts of money.  '
         'Armory developers will not be held '
         'responsible for loss of funds due to software defects!'  )

      
      lblShouldKnow = QRichLabel( \
         '<b>While this software is in <i>alpha</i></b>, it requires your system '
         'to hold the entire blockchain in RAM.  This will have serious '
         'impacts on your system\'s performance if you are on the main Bitcoin '
         'network, unless you have 4GB or RAM or more.  If this is a problem, please '
         'wait for the <i>beta</i> release, which will have dramatically-reduced '
         'memory requirements.')

      lblMustDo = QRichLabel('<b>In order to use this software '
                             '(unless you are in offline mode):</b>')
      strReqts = []
      strReqts.append('Must have Satoshi client (www.bitcoin.org) open and on '
                      'the same network (Main-net or Testnet)')
      strReqts.append('<b>Please</b> make sure the Satoshi client is sync\'d '
                      'with the blockchain before loading Armory.')
      strReqts.append('Blockchain held in memory:  requires about 1.5 '
                      'GB of RAM (plus Satoshi client RAM)')
      strReqts.append('Uses the blockchain file maintained by Satoshi '
                      'client (blk0001.dat)')
      lblReqts = QRichLabel( ''.join(['-- '+s+'<br>' for s in strReqts]))

      lblContact = QRichLabel( \
         '<b>If you are impressed with this software, please consider pressing '
         'the "Donate" button on your next transaction!</b>')

      spacer = lambda: QSpacerItem(20,20, QSizePolicy.Fixed, QSizePolicy.Expanding)


      frmText = makeLayoutFrame('Vert', [lblWelcome,    spacer(), \
                                         lblDescr,      spacer(), \
                                         lblShouldKnow, spacer(), \
                                         lblMustDo,               \
                                         lblReqts,      spacer(), \
                                         lblContact     ])

      

      self.chkDnaaIntroDlg = QCheckBox('Do not show this window again')

      self.requestCreate = False
      self.requestImport = False
      buttonBox = QDialogButtonBox()
      frmIcon = makeLayoutFrame('Vert', [lblInfoImg, 'Stretch'])
      frmIcon.setMaximumWidth(60)
      if len(self.main.walletMap)==0:
         self.btnCreate = QPushButton("Create Your First Wallet!")
         self.btnImport = QPushButton("Import Existing Wallet")
         self.btnCancel = QPushButton("Skip")
         self.connect(self.btnCreate, SIGNAL('clicked()'), self.createClicked)
         self.connect(self.btnImport, SIGNAL('clicked()'), self.importClicked)
         self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
         buttonBox.addButton(self.btnCreate, QDialogButtonBox.AcceptRole)
         buttonBox.addButton(self.btnImport, QDialogButtonBox.AcceptRole)
         buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)
         self.chkDnaaIntroDlg.setVisible(False)
         frmBtn = makeLayoutFrame('Horiz', [self.chkDnaaIntroDlg, \
                                            self.btnCancel, \
                                            'Stretch', \
                                            self.btnImport, \
                                            self.btnCreate])
      else:
         self.btnOkay = QPushButton("Okay!")
         self.connect(self.btnOkay, SIGNAL('clicked()'), self.accept)
         buttonBox.addButton(self.btnOkay, QDialogButtonBox.AcceptRole)
         frmBtn = makeLayoutFrame('Horiz', [self.chkDnaaIntroDlg, \
                                            'Stretch', \
                                            self.btnOkay])

      

      dlgLayout = QGridLayout()
      dlgLayout.addWidget(frmIcon,    0, 0,   1, 1)
      dlgLayout.addWidget(frmText,    0, 1,   1, 1)
      dlgLayout.addWidget(frmBtn,     1, 0,   1, 2)
      
      self.setLayout(dlgLayout)
      self.setWindowTitle('Greetings!')
      self.setWindowIcon(QIcon( self.main.iconfile))
      self.setMinimumWidth(750)
   

   def createClicked(self):
      self.requestCreate = True
      self.accept()

   def importClicked(self):
      self.requestImport = True
      self.accept()

   def sizeHint(self):
      return QSize(750, 500)




#class DlgPesterDonate(QDialog):
  



#############################################################################
class DlgImportPaperWallet(QDialog):

   def __init__(self, parent=None, main=None):
      super(DlgImportPaperWallet, self).__init__(parent)

      self.wltDataLines = [[]]*4
      self.prevChars    = ['']*4

      self.parent = parent
      self.main   = main
      ROOT0, ROOT1, CHAIN0, CHAIN1 = range(4)
      self.lineEdits = [QLineEdit() for i in range(4)]
      self.prevChars = ['' for i in range(4)]

      for i,edt in enumerate(self.lineEdits):
         # I screwed up the ref/copy, this loop only connected the last one...
         #theSlot = lambda: self.autoSpacerFunction(i)
         #self.connect(edt, SIGNAL('textChanged(QString)'), theSlot)
         edt.setMinimumWidth( tightSizeNChar(edt, 50)[0] )

      # Just do it manually because it's guaranteed to work!
      slot = lambda: self.autoSpacerFunction(0)
      self.connect(self.lineEdits[0], SIGNAL('textEdited(QString)'), slot)

      slot = lambda: self.autoSpacerFunction(1)
      self.connect(self.lineEdits[1], SIGNAL('textEdited(QString)'), slot)

      slot = lambda: self.autoSpacerFunction(2)
      self.connect(self.lineEdits[2], SIGNAL('textEdited(QString)'), slot)

      slot = lambda: self.autoSpacerFunction(3)
      self.connect(self.lineEdits[3], SIGNAL('textEdited(QString)'), slot)

      buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonbox, SIGNAL('accepted()'), self.verifyUserInput)
      self.connect(buttonbox, SIGNAL('rejected()'), self.reject)

      self.labels = [QLabel() for i in range(4)]
      self.labels[0].setText('Root Key')
      self.labels[1].setText('')
      self.labels[2].setText('Chain Code')
      self.labels[3].setText('')

      lblDescr1 = QLabel( 
          'Enter the characters exactly as they are printed on the '
          'paper-backup page.  Alternatively, you can scan the QR '
          'code from another application, then copy&paste into the '
          'entry boxes below.')
      lblDescr2 = QLabel( 
          'The data can be entered <i>with</i> or <i>without</i> '
          'spaces, and up to '
          'one character per line will be corrected automatically.')
      for lbl in (lblDescr1, lblDescr2):
         lbl.setTextFormat(Qt.RichText)
         lbl.setWordWrap(True)

      layout = QGridLayout()
      layout.addWidget(lblDescr1, 0, 0, 1, 2)
      layout.addWidget(lblDescr2, 1, 0, 1, 2)
      for i,edt in enumerate(self.lineEdits):
         layout.addWidget( self.labels[i],    i+2, 0)
         layout.addWidget( self.lineEdits[i], i+2, 1)

      layout.addWidget(buttonbox,  6, 0, 1, 2)
      layout.setVerticalSpacing(10)
      self.setLayout(layout)
      

      self.setWindowTitle('Recover Wallet from Paper Backup')
      self.setWindowIcon(QIcon( self.main.iconfile))


   def autoSpacerFunction(self, i):
      currStr = str(self.lineEdits[i].text())
      rawStr  = currStr.replace(' ','')
      if len(rawStr) > 36:
         rawStr = rawStr[:36]

      if len(rawStr)==36:
         quads = [rawStr[j:j+4] for j in range(0,36, 4)]
         self.lineEdits[i].setText(' '.join(quads))
         
      """
      currStr = str(self.lineEdits[i].text())
      currLen = len(currStr)

      rawStr  = currStr.replace(' ','')
      rawLen  = len(rawStr)

      if rawLen > 36:
         rawStr = rawStr[:36]

      modAtEnd = ((currStr[:-1] == self.prevChars[i]     ) or \
                  (currStr      == self.prevChars[i][:-1])     )
      edt = self.lineEdits[i]
      if currLen>len(self.prevChars[i]) and modAtEnd and currLen%5==4:
         self.lineEdits[i].setText(currStr+' ')
         self.lineEdits[i].cursorForward(False, 1)
      elif currLen<len(self.prevChars[i]) and modAtEnd and currLen%5==0 and currLen!=0:
         self.lineEdits[i].setText(currStr[:-1])

      if not modAtEnd:
         rawStr = str(self.lineEdits[i].text()).replace(' ','')
         quads = [rawStr[j:j+4] for j in range(0,currLen, 4)]
         self.lineEdits[i].setText(' '.join(quads))
      
      self.prevChars[i] = str(self.lineEdits[i].text())
      """
   

   def verifyUserInput(self):
      nError = 0
      for i in range(4):
         hasError=False
         try:
            rawBin = easyType16_to_binary( str(self.lineEdits[i].text()).replace(' ','') )
            data, chk = rawBin[:16], rawBin[16:]
            fixedData = verifyChecksum(data, chk)
            if len(fixedData)==0:
               hasError=True
         except KeyError:
            hasError=True
            
         if hasError:
            reply = QMessageBox.critical(self, 'Verify Wallet ID', \
               'There is an error in the data you entered that could not be '
               'fixed automatically.  Please double-check that you entered the '
               'text exactly as it appears on the wallet-backup page.', \
               QMessageBox.Ok)
            print 'BadData!'
            self.labels[i].setText('<font color="red">'+str(self.labels[i].text())+'</font>')
            return
         if not fixedData==data:
            data = fixedData
            nError+=1

         self.wltDataLines[i] = data

      if nError>0:
         pluralStr = 'error' if nError==1 else 'errors'
         QMessageBox.question(self, 'Errors Corrected!', \
            'Detected ' + str(nError) + ' ' + pluralStr + ' '
            'in the data you entered.  Armory attempted to fix the ' + 
            pluralStr + ' but it is not always right.  Be sure '
            'to verify the "Wallet Unique ID" closely on the next window.', \
            QMessageBox.Ok)
            
      # If we got here, the data is valid, let's create the wallet and accept the dlg
      privKey = ''.join(self.wltDataLines[:2])
      chain   = ''.join(self.wltDataLines[2:])
       
      root  = PyBtcAddress().createFromPlainKeyData(SecureBinaryData(privKey))
      root.chaincode = SecureBinaryData(chain)
      first = root.extendAddressChain()
      newWltID = binary_to_base58((ADDRBYTE + first.getAddr160()[:5])[::-1])

      if self.main.walletMap.has_key(newWltID):
         QMessageBox.question(self, 'Duplicate Wallet!', \
               'The data you entered is for a wallet with a ID: \n\n \t' +
               newWltID + '\n\n!!!You already own this wallet!!!\n  '
               'Nothing to do...', QMessageBox.Ok)
         self.accept()
         return
         
      
      
      reply = QMessageBox.question(self, 'Verify Wallet ID', \
               'The data you entered corresponds to a wallet with a wallet ID: \n\n \t' +
               newWltID + '\n\nDoes this ID match the "Wallet Unique ID" ' 
               'printed on your paper backup?  If not, click "No" and reenter '
               'key and chain-code data again.', \
               QMessageBox.Yes | QMessageBox.No)
      if reply==QMessageBox.No:
         return
      else:
         self.newWallet = PyBtcWallet().createNewWallet(  \
                                 plainRootKey=SecureBinaryData(privKey), \
                                 chaincode=SecureBinaryData(chain), \
                                 withEncrypt=False)
         self.newWallet.setWalletLabels('PaperBackup - '+newWltID)
         self.accept()
      



################################################################################
class DlgSetComment(QDialog):
   """ This will be a dumb dialog for retrieving a comment from user """

   #############################################################################
   def __init__(self, currcomment='', ctype='', parent=None, main=None):
      super(DlgSetComment, self).__init__(parent)

      self.parent = parent
      self.main   = main  

      self.setWindowTitle('Add or Change Comment')
      self.setWindowIcon(QIcon( self.main.iconfile))

      buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonbox, SIGNAL('accepted()'), self.accept)
      self.connect(buttonbox, SIGNAL('rejected()'), self.reject)

      layout = QGridLayout()
      lbl = None
      if     ctype and     currcomment: lbl = QLabel('Change %s Comment:'%ctype)
      if not ctype and     currcomment: lbl = QLabel('Change Comment:')
      if     ctype and not currcomment: lbl = QLabel('Add %s Comment:'%ctype)
      if not ctype and not currcomment: lbl = QLabel('Add Comment:')
      self.edtComment = QLineEdit()
      self.edtComment.setText(currcomment)
      h,w = relaxedSizeNChar(self, 50)
      self.edtComment.setMinimumSize(h,w)
      layout.addWidget(lbl,             0,0)
      layout.addWidget(self.edtComment, 1,0)
      layout.addWidget(buttonbox,       2,0)
      self.setLayout(layout)


try:
   from qrcodenative import *
except ImportError:
   print 'QR-generation code not available...'

PAPER_DPI       = 72
PAPER_A4_WIDTH  =  8.5*PAPER_DPI
PAPER_A4_HEIGHT = 11.0*PAPER_DPI


###### Typing-friendly Base16 #####
#  Implements "hexadecimal" encoding but using only easy-to-type
#  characters in the alphabet.  Hex usually includes the digits 0-9
#  which can be slow to type, even for good typists.  On the other
#  hand, by changing the alphabet to common, easily distinguishable,
#  lowercase characters, typing such strings will become dramatically
#  faster.  Additionally, some default encodings of QRCodes do not
#  preserve the capitalization of the letters, meaning that Base58
#  is not a feasible options
NORMALCHARS  = '0123 4567 89ab cdef'.replace(' ','')
BASE16CHARS  = 'asdf ghjk wert uion'.replace(' ','')
hex_to_base16_map = {}
base16_to_hex_map = {}
for n,b in zip(NORMALCHARS,BASE16CHARS):
   hex_to_base16_map[n] = b
   base16_to_hex_map[b] = n

def binary_to_easyType16(binstr):
   return ''.join([hex_to_base16_map[c] for c in binary_to_hex(binstr)])

def easyType16_to_binary(b16str):
   return hex_to_binary(''.join([base16_to_hex_map[c] for c in b16str]))



class GfxViewPaper(QGraphicsView):
   def __init__(self, parent=None, main=None):
      super(GfxViewPaper, self).__init__(parent)
      self.setRenderHint(QPainter.TextAntialiasing) 

class GfxItemText(QGraphicsTextItem):
   """
   So far, I'm pretty bad ad setting the boundingRect properly.  I have 
   hacked it to be usable for this specific situation, but it's not very
   reusable...
   """
   def __init__(self, text, position, scene, font=GETFONT('Courier',8), lineWidth=None):
      super(GfxItemText, self).__init__(text)
      self.setFont(font)
      self.setPos(position)
      if lineWidth:
         self.setTextWidth(lineWidth)

   def boundingRect(self):
      w,h = relaxedSizeStr(self, self.toPlainText())
      nLine=1
      if self.textWidth()>0:
         twid = self.textWidth()
         nLine = max(1, int(float(w) / float(twid) + 0.5))
      return QRectF(0, 0, w, nLine*(1.5*h))

   
class GfxItemQRCode(QGraphicsItem):
   """
   Converts binary data to base58, and encodes the Base58 characters in
   the QR-code.  It seems weird to use Base58 instead of binary, but the
   QR-code has no problem with the size, instead, we want the data in the
   QR-code to match exactly what is human-readable on the page, which is
   in Base58.

   You must supply exactly one of "totalSize" or "modSize".  TotalSize
   guarantees that the QR code will fit insides box of a given size.  
   ModSize is how big each module/pixel of the QR code is, which means 
   that a bigger QR block results in a bigger physical size on paper.
   """
   def __init__(self, position, scene, rawDataToEncode, totalSize=None, modSize=None):
      super(GfxItemQRCode, self).__init__()
      self.setPos(position)
      
      sz=3
      success=False
      while sz<20:
         try:
            # 6 is a good size for a QR-code: If you pick too small (i.e. cannot
            # fit all the data requested), you will get a type error.  Raise this
            # number to get ever-more-massive QR codes which fit more data
            self.qr = QRCode(sz, QRErrorCorrectLevel.H)
            self.qr.addData(rawDataToEncode)
            self.qr.make()
            success=True
            break
         except TypeError:
            #print 'Failed to generate QR code:  likely too much data for the size'
            sz += 1
            pass

      
      self.modCt = self.qr.getModuleCount()
      if totalSize==None and not modSize==None:
         totalSize = float(self.modCt)*float(modSize)
      self.modSz = round(float(totalSize)/ float(self.modCt) - 0.5)
      # Readjust totalsize to make sure that 
      totalSize = self.modCt*self.modSz
      self.Rect = QRectF(0,0, totalSize, totalSize)
         


   def boundingRect(self):
      return self.Rect

   def paint(self, painter, option, widget=None):
      painter.setPen(Qt.NoPen)
      painter.setBrush(QBrush(QColor(Colors.Black)))

      for r in range(self.modCt):
         for c in range(self.modCt):
            if (self.qr.isDark(c, r) ):
               painter.drawRect(*[self.modSz*a for a in [r,c,1,1]])


class DlgRemoveWallet(QDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgRemoveWallet, self).__init__(parent)
      
      self.parent = parent
      self.main   = main

      wltID = wlt.uniqueIDB58
      wltName = wlt.labelName
      wltDescr = wlt.labelDescr
      lblWarning = QLabel( '<b>!!! WARNING !!!</b>\n\n')
      lblWarning.setTextFormat(Qt.RichText)
      lblWarning.setAlignment(Qt.AlignHCenter)

      lblWarning2 = QLabel( '<i>You have requested that the following wallet '
                            'be removed from Armory:</i>')
      lblWarning.setTextFormat(Qt.RichText)
      lblWarning.setWordWrap(True)
      lblWarning.setAlignment(Qt.AlignHCenter)

      lbls = []
      lbls.append([])
      lbls[0].append(QLabel('Wallet Unique ID:'))
      lbls[0].append(QLabel(wltID))
      lbls.append([])
      lbls[1].append(QLabel('Wallet Name:'))
      lbls[1].append(QLabel(wlt.labelName))
      lbls.append([])
      lbls[2].append(QLabel('Description:'))
      lbls[2].append(QLabel(wlt.labelDescr))
      lbls[2][-1].setWordWrap(True)

      wltEmpty = True
      if TheBDM.isInitialized():
         wlt.syncWithBlockchain()
         bal = wlt.getBalance('Full')
         lbls.append([])
         lbls[3].append(QLabel('Current Balance (w/ unconfirmed):'))
         if bal>0:
            lbls[3].append(QLabel('<font color="red"><b>'+coin2str(bal, maxZeros=1).strip()+' BTC</b></font>'))
            lbls[3][-1].setTextFormat(Qt.RichText)
            wltEmpty = False
         else:
            lbls[3].append(QLabel(coin2str(bal, maxZeros=1) + ' BTC'))


      # Add two WARNING images on either side of dialog
      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap('img/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnImg2 = QLabel()
      lblWarnImg2.setPixmap(QPixmap('img/MsgBox_warning48.png'))
      lblWarnImg2.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      # Add the warning text and images to the top of the dialog
      layout = QGridLayout()
      layout.addWidget(lblWarning,  0, 1, 1, 1)
      layout.addWidget(lblWarning2, 1, 1, 1, 1)
      layout.addWidget(lblWarnImg,  0, 0, 2, 1)
      layout.addWidget(lblWarnImg2,  0, 2, 2, 1)

      frmInfo = QFrame()
      frmInfo.setFrameStyle(QFrame.Box|QFrame.Plain)
      frmInfo.setLineWidth(3)
      frmInfoLayout = QGridLayout()
      for i in range(len(lbls)):
         lbls[i][0].setText('<b>'+lbls[i][0].text()+'</b>')
         lbls[i][0].setTextFormat(Qt.RichText)
         frmInfoLayout.addWidget(lbls[i][0],  i, 0)
         frmInfoLayout.addWidget(lbls[i][1],  i, 1, 1, 2)

      frmInfo.setLayout(frmInfoLayout)
      layout.addWidget(frmInfo, 2, 0, 2, 3)

      if not wltEmpty:
         if wlt.watchingOnly:
            lbl = QRichLabel('')
         else:
            lbl = QRichLabel('<b>WALLET IS NOT EMPTY.  Only delete this wallet if you '
                          'have a backup on paper or saved to a another location '
                          'outside your settings directory.</b>')
         lbls.append(lbl)
         layout.addWidget(lbl, 4, 0, 1, 3)

      self.radioExclude = QRadioButton('Add this wallet to the "ignore list"')
      self.radioExclude.setEnabled(False)
      self.radioDelete  = QRadioButton('Permanently delete this wallet')
      self.radioWatch   = QRadioButton('Delete private keys only, make watching-only')

      # Make sure that there can only be one selection
      btngrp = QButtonGroup(self)
      btngrp.addButton(self.radioExclude)
      btngrp.addButton(self.radioDelete)
      btngrp.addButton(self.radioWatch)
      btngrp.setExclusive(True)

      ttipExclude = createToolTipObject( \
                              '[DISABLED] This will not delete any files, but will add this '
                              'wallet to the "ignore list."  This means that Armory '
                              'will no longer show this wallet in the main screen '
                              'and none of its funds will be added to your balance.  '
                              'You can re-include this wallet in Armory at a later '
                              'time by selecting the "Excluded Wallets..." option '
                              'in the "Wallets" menu.')
      ttipDelete = createToolTipObject( \
                              'This will delete the wallet file, removing '
                              'all its private keys from your settings directory.  '
                              'If you intend to keep using addresses from this '
                              'wallet, do not select this option unless the wallet '
                              'is backed up elsewhere.')
      ttipWatch = createToolTipObject( \
                              'This will delete the private keys from your wallet, '
                              'leaving you with a watching-only wallet, which can be '
                              'used to generate addresses and monitor incoming '
                              'payments.  This option would be used if you created '
                              'the wallet on this computer <i>in order to transfer '
                              'it to a different computer or device and want to '
                              'remove the private data from this system for security.</i>')


      self.chkPrintBackup = QCheckBox('Print a paper backup of this wallet before deleting')

      if wlt.watchingOnly:
         ttipDelete = createToolTipObject('This will delete the wallet file from your system.  '
                                 'Since this is a watching-only wallet, no private keys '
                                 'will be deleted.')
         ttipWatch = createToolTipObject('This wallet is already a watching-only wallet '
                                 'so this option is pointless')
         self.radioWatch.setEnabled(False)
         self.chkPrintBackup.setEnabled(False)
         

      self.frm = []

      rdoFrm = QFrame()
      rdoFrm.setFrameStyle(STYLE_RAISED)
      rdoLayout = QGridLayout()
      
      startRow = 0
      for rdo,ttip in [(self.radioExclude, ttipExclude), \
                       (self.radioDelete,  ttipDelete), \
                       (self.radioWatch,   ttipWatch)]:
         self.frm.append(QFrame())
         #self.frm[-1].setFrameStyle(STYLE_SUNKEN)
         self.frm[-1].setFrameStyle(QFrame.NoFrame)
         frmLayout = QHBoxLayout()
         frmLayout.addWidget(rdo)
         ttip.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) 
         frmLayout.addWidget(ttip)
         frmLayout.addStretch()
         self.frm[-1].setLayout(frmLayout)
         rdoLayout.addWidget(self.frm[-1], startRow, 0, 1, 3)
         startRow +=1 


      self.radioDelete.setChecked(True)
      rdoFrm.setLayout(rdoLayout)

      startRow = 6 if wltEmpty else 5
      layout.addWidget(rdoFrm, startRow, 0, 1, 3)

      if wlt.watchingOnly:
         self.frm[-1].setVisible(False)
         
   
      printTtip = createToolTipObject( \
         'If this box is checked, you will have the ability to print off an '
         'unencrypted version of your wallet before it is deleted.  <b>If '
         'printing is unsuccessful, please press *CANCEL* on the print dialog '
         'to prevent the delete operation from continuing</b>')
      printFrm = makeLayoutFrame('Horiz', [self.chkPrintBackup, printTtip, 'Stretch'])
      startRow +=1
      layout.addWidget( printFrm, startRow, 0, 1, 3)

      if wlt.watchingOnly:
         printFrm.setVisible(False)

      
      rmWalletSlot = lambda: self.removeWallet(wlt)

      startRow +=1
      self.btnDelete = QPushButton("Delete")
      self.btnCancel = QPushButton("Cancel")
      self.connect(self.btnDelete, SIGNAL('clicked()'), rmWalletSlot)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnDelete, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)
      layout.addWidget(buttonBox, startRow, 0, 1, 3)

      self.setLayout(layout)
      self.setWindowTitle('Delete Wallet Options')

      
   def removeWallet(self, wlt):

      # Open the print dialog.  If they hit cancel at any time, then 
      # we go back to the primary wallet-remove dialog without any other action
      if self.chkPrintBackup.isChecked():      
         dlg = DlgPaperBackup(wlt, self, self.main)
         if not dlg.exec_():
            return
            
            
      # If they only want to exclude the wallet, we will add it to the excluded
      # list and remove it from the application.  The wallet files will remain
      # in the settings directory but will be ignored by Armory

      wltID = wlt.uniqueIDB58
      if self.radioExclude.isChecked():
         reply = QMessageBox.warning(self, 'Verify Intentions', \
           'Are you sure you want to remove this wallet from your Armory '
           'dashboard?  The wallet file will not be deleted, but you will '
           'no longer have access to the wallet or its funds unless you '
           're-enable it through the "Wallets"->"Excluded Wallets" menu. ', \
           QMessageBox.Yes | QMessageBox.Cancel)

         if reply==QMessageBox.Yes:
            self.main.removeWalletFromApplication(wltID)
            self.main.settings.extend('Excluded_Wallets', wlt.walletPath)
            self.main.statusBar().showMessage( \
                     'Wallet '+wltID+' was added to the ignore list.', 20000)
            self.main.accept()
            self.accept()
         else:
            self.reject()
      else:

         if wlt.watchingOnly:
            reply = QMessageBox.warning(self, 'Confirm Delete', \
            'You are about to delete a watching-only wallet.  Are you sure '
            'you want to do this?', QMessageBox.Yes | QMessageBox.Cancel)
         else:
            reply = QMessageBox.warning(self, 'Are you absolutely sure?!?', \
            'Are you absolutely sure you want to permanently delete '
            'this wallet?  Unless this wallet is saved on another device '
            'you will permanently lose access to all the addresses in this '
            'wallet.', QMessageBox.Yes | QMessageBox.Cancel)

         if reply==QMessageBox.Yes:

            thepath       = wlt.getWalletPath()
            thepathBackup = wlt.getWalletPath('backup')

            if self.radioWatch.isChecked():
               print '***Converting to watching-only wallet'
               newWltPath = wlt.getWalletPath('WatchOnly')
               wlt.forkOnlineWallet(newWltPath, wlt.labelName, wlt.labelDescr)
               newWlt = PyBtcWallet().readWalletFile(newWltPath)
               newWlt.setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
               newWlt.syncWithBlockchain()

               os.remove(thepath)
               os.remove(thepathBackup)
               self.main.walletMap[wltID] = newWlt
               self.main.statusBar().showMessage( \
                     'Wallet %s was replaced with a watching-only wallet.' % wltID, 10000)
            elif self.radioDelete.isChecked():
               print '***Completely deleting wallet'
               os.remove(thepath)
               os.remove(thepathBackup)
               self.main.removeWalletFromApplication(wltID) 
               self.main.statusBar().showMessage( \
                     'Wallet '+wltID+' was deleted!', 10000)

            self.parent.accept()
            self.accept()
         else:
            self.reject()


class DlgRemoveAddress(QDialog):
   def __init__(self, wlt, addr160, parent=None, main=None):
      super(DlgRemoveAddress, self).__init__(parent)

      
      if not wlt.hasAddr(addr160):
         raise WalletAddressError, 'Address does not exist in wallet!'

      if not wlt.getAddrByHash160(addr160).chainIndex==-2:
         raise WalletAddressError, ('Cannot delete regular chained addresses! '
                                   'Can only delete imported addresses.')


      self.parent = parent
      self.main   = main
      self.wlt    = wlt
      self.addr   = wlt.addrMap[addr160]
      self.comm   = wlt.getCommentForAddress(addr160)

      lblWarning = QLabel( '<b>!!! WARNING !!!</b>\n\n')
      lblWarning.setTextFormat(Qt.RichText)
      lblWarning.setAlignment(Qt.AlignHCenter)

      lblWarning2 = QLabel( '<i>You have requested that the following address '
                            'be deleted from your wallet:</i>')
      lblWarning.setTextFormat(Qt.RichText)
      lblWarning.setWordWrap(True)
      lblWarning.setAlignment(Qt.AlignHCenter)

      lbls = []
      lbls.append([])
      lbls[-1].append(QLabel('Address:'))
      lbls[-1].append(QLabel(self.addr.getAddrStr()))
      lbls.append([])
      lbls[-1].append(QLabel('Comment:'))
      lbls[-1].append(QLabel(self.comm))
      lbls[-1][-1].setWordWrap(True)
      lbls.append([])
      lbls[-1].append(QLabel('In Wallet:'))
      lbls[-1].append(QLabel('"%s" (%s)' % (wlt.labelName, wlt.uniqueIDB58)))

      addrEmpty = True
      if TheBDM.isInitialized():
         wlt.syncWithBlockchain()
         bal = wlt.getAddrBalance(addr160, 'Full')
         lbls.append([])
         lbls[-1].append(QLabel('Address Balance (w/ unconfirmed):'))
         if bal>0:
            lbls[-1].append(QLabel('<font color="red"><b>'+coin2str(bal, maxZeros=1)+' BTC</b></font>'))
            lbls[-1][-1].setTextFormat(Qt.RichText)
            addrEmpty = False
         else:
            lbls[3].append(QLabel(coin2str(bal, maxZeros=1) + ' BTC'))


      # Add two WARNING images on either side of dialog
      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap('img/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnImg2 = QLabel()
      lblWarnImg2.setPixmap(QPixmap('img/MsgBox_warning48.png'))
      lblWarnImg2.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      # Add the warning text and images to the top of the dialog
      layout = QGridLayout()
      layout.addWidget(lblWarning,  0, 1, 1, 1)
      layout.addWidget(lblWarning2, 1, 1, 1, 1)
      layout.addWidget(lblWarnImg,  0, 0, 2, 1)
      layout.addWidget(lblWarnImg2,  0, 2, 2, 1)

      frmInfo = QFrame()
      frmInfo.setFrameStyle(QFrame.Box|QFrame.Plain)
      frmInfo.setLineWidth(3)
      frmInfoLayout = QGridLayout()
      for i in range(len(lbls)):
         lbls[i][0].setText('<b>'+lbls[i][0].text()+'</b>')
         lbls[i][0].setTextFormat(Qt.RichText)
         frmInfoLayout.addWidget(lbls[i][0],  i, 0)
         frmInfoLayout.addWidget(lbls[i][1],  i, 1, 1, 2)

      frmInfo.setLayout(frmInfoLayout)
      layout.addWidget(frmInfo, 2, 0, 2, 3)

      lblDelete = QLabel( \
            'Do you want to delete this address?  No other addresses in this '
            'wallet will be affected.')
      lblDelete.setWordWrap(True)
      lblDelete.setTextFormat(Qt.RichText)
      layout.addWidget(lblDelete, 4, 0, 1, 3)

      bbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                              QDialogButtonBox.Cancel)
      self.connect(bbox, SIGNAL('accepted()'), self.removeAddress)
      self.connect(bbox, SIGNAL('rejected()'), self.reject)
      layout.addWidget(bbox, 5,0,1,3)

      self.setLayout(layout)
      self.setWindowTitle('Confirm Delete Address')


   def removeAddress(self):

      # Open the print dialog.  If they hit cancel at any time, then 
      # we go back to the primary wallet-remove dialog without any other action
      #if self.chkPrintBackup.isChecked():      
         #dlg = DlgPaperBackup(wlt, self, self.main)
         #if not dlg.exec_():
            #return
            
            
      reply = QMessageBox.warning(self, 'One more time...', \
           'Simply deleting an address does not prevent anyone '
           'from sending money to it.  If you have given this address '
           'to anyone in the past, make sure that they know not to '
           'use it again, since any Bitcoins sent to it will be '
           'inaccessible.\n\n '
           'If you are maintaining an external copy of this address '
           'please ignore this warning\n\n'
           'Are you absolutely sure you want to delete ' + 
           self.addr.getAddrStr() + '?', \
           QMessageBox.Yes | QMessageBox.Cancel)

      if reply==QMessageBox.Yes:
         self.wlt.deleteImportedAddress(self.addr.getAddr160())
         try:
            #self.parent.accept()
            self.main.wltAddrModel.reset()
         except AttributeError:
            pass
         self.accept()
         
      else:
         self.reject()



class DlgWalletSelect(QDialog):
   def __init__(self, parent=None, main=None,  title='Select Wallet:', \
                             firstSelect=None, onlyMyWallets=False, wltIDList=None):
      super(DlgWalletSelect, self).__init__(parent)

      self.parent = parent
      self.main   = main
      self.lstWallets = QListWidget()

      if self.main and len(self.main.walletMap)==0:
         QMessageBox.critical(self, 'No Wallets!', \
            'There are no wallets to select from.  Please create or import '
            'a wallet first.', QMessageBox.Ok)
         self.accept()
         return
      
      if wltIDList==None:
         wltIDList = list(self.main.walletIDList)

      self.rowList = []
      
      selectedRow = 0
      self.selectedID = None
      nrows = 0
      if len(wltIDList)>0:
         self.selectedID = wltIDList[0]
         for r,wltID in enumerate(wltIDList):
            wlt = self.main.walletMap[wltID]
            wlttype = determineWalletType(self.main.walletMap[wltID], self.main)[0]
            if onlyMyWallets and wlttype==WLTTYPES.WatchOnly:
               continue
            self.lstWallets.addItem(QListWidgetItem(wlt.labelName))
            self.rowList.append([wltID])
         
            if wltID==firstSelect:
               selectedRow = nrows
               self.selectedID = wltID
            nrows += 1
            
         self.lstWallets.setCurrentRow(selectedRow)
      
      self.connect(self.lstWallets, SIGNAL('currentRowChanged(int)'), self.showWalletInfo)
      self.lstWallets.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

      self.connect(self.lstWallets, SIGNAL('itemDoubleClicked(QListWidgetItem *)'), self.dblclick)

      layout = QGridLayout()
      layout.addWidget(QLabel(title), 0, 0,  1, 1)
      layout.addWidget(self.lstWallets,          1, 0,  3, 1)



      lbls = []
      lbls.append( QLabel("Wallet ID:") )
      lbls.append( QLabel("Name:"))
      lbls.append( QLabel("Description:"))
      lbls.append( QLabel("Spendable Balance:"))

      for i in range(len(lbls)):
         lbls[i].setAlignment(Qt.AlignLeft | Qt.AlignTop)
         lbls[i].setTextFormat(Qt.RichText)
         lbls[i].setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
         lbls[i].setText('<b>'+str(lbls[i].text())+'</b>')

      self.dispID = QLabel()
      self.dispName = QLabel()
      self.dispDescr = QLabel()
      self.dispBal = QLabel()

      self.dispBal.setTextFormat(Qt.RichText)
      self.dispDescr.setWordWrap(True)
      

      frm = QFrame()
      frm.setFrameStyle(STYLE_SUNKEN)
      frmLayout = QGridLayout()
      for i in range(len(lbls)):
         frmLayout.addWidget(lbls[i], i, 0,  1, 1)

      self.dispID.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.dispName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.dispDescr.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.dispBal.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.dispDescr.setMinimumWidth( tightSizeNChar(self.dispDescr, 40)[0])
      frmLayout.addWidget(self.dispID,    0, 2, 1, 1)
      frmLayout.addWidget(self.dispName,  1, 2, 1, 1)
      frmLayout.addWidget(self.dispDescr, 2, 2, 1, 1)
      frmLayout.addWidget(self.dispBal,   3, 2, 1, 1)
      #for i in range(len(displays)):
         #displays[i].setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
         #frmLayout.addWidget(displays[i], i, 1, 1, 1)

      frmLayout.addItem(QSpacerItem(20, 10, QSizePolicy.Fixed, QSizePolicy.Expanding), 0, 1, 3, 1)
      frm.setLayout(frmLayout)
      

      buttonBox = QDialogButtonBox()
      btnAccept = QPushButton('Ok')
      btnCancel = QPushButton('Cancel')
      self.connect(btnAccept, SIGNAL('clicked()'), self.accept)
      self.connect(btnCancel, SIGNAL('clicked()'), self.reject)
      buttonBox.addButton(btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(btnCancel, QDialogButtonBox.RejectRole)
      layout.addWidget(frm,                     1, 1,  3, 2)
      layout.addWidget(buttonBox,               4, 0,  1, 3)

      self.setLayout(layout)

      if not self.selectedID==None:
         self.showWalletInfo()

      self.setWindowTitle('Select Wallet')



   def showWalletInfo(self, i=0):
      currRow = self.lstWallets.currentRow()
      wltID = self.rowList[currRow][0]
      wlt = self.main.walletMap[wltID]
      self.dispID.setText(wltID)
      self.dispName.setText(wlt.labelName)
      self.dispDescr.setText(wlt.labelDescr)
      
      bal = wlt.getBalance('Spendable')
      if bal==0:
         self.dispBal.setText('<font color="red"><b>0.0</b></font>')
      else:
         self.dispBal.setText('<b>'+coin2str(wlt.getBalance('Spendable'), maxZeros=1)+'</b>')
      self.dispBal.setTextFormat(Qt.RichText) 
      self.selectedID=wltID


   def dblclick(self, *args):
      currRow = self.lstWallets.currentRow()
      self.selectedID = self.rowList[currRow][0]
      self.accept()


################################################################################
def getWalletInfoFrame(wlt):
   """
   I *should* be using this method for the wallet-select, too, but I couldn't
   figure out how to swap frames from the layout after a selection switch
   """
   wltID = wlt.uniqueIDB58
   lbls = []
   lbls.append( QLabel("Wallet ID:") )
   lbls.append( QLabel("Name:"))
   lbls.append( QLabel("Description:"))
   lbls.append( QLabel("Spendable Balance:"))

   for i in range(len(lbls)):
      lbls[i].setAlignment(Qt.AlignLeft | Qt.AlignTop)
      lbls[i].setTextFormat(Qt.RichText)
      lbls[i].setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
      lbls[i].setText('<b>'+str(lbls[i].text())+'</b>')

   dispID = QLabel(wltID)
   dispName = QLabel(wlt.labelName)
   dispDescr = QLabel(wlt.labelDescr)
   dispBal = QRichLabel('')

   # Format balance if necessary
   bal = wlt.getBalance('Spendable')
   if bal==0: dispBal.setText('<font color="red"><b>0.0000</b></font>')
   else:      dispBal.setText('<font color="green"><b>'+coin2str(bal, maxZeros=1)+'</font></b>')

   dispBal.setTextFormat(Qt.RichText)
   dispDescr.setWordWrap(True)
      

   frm = QFrame()
   frm.setFrameStyle(STYLE_SUNKEN)
   frmLayout = QGridLayout()
   for i in range(len(lbls)):
      frmLayout.addWidget(lbls[i], i, 0,  1, 1)

   dispID.setAlignment(Qt.AlignLeft | Qt.AlignTop)
   dispName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
   dispDescr.setAlignment(Qt.AlignLeft | Qt.AlignTop)
   dispBal.setAlignment(Qt.AlignLeft | Qt.AlignTop)
   dispDescr.setMinimumWidth( tightSizeNChar(dispDescr, 30)[0])
   frmLayout.addWidget(dispID,    0, 2, 1, 1)
   frmLayout.addWidget(dispName,  1, 2, 1, 1)
   frmLayout.addWidget(dispDescr, 2, 2, 1, 1)
   frmLayout.addWidget(dispBal,   3, 2, 1, 1)
   #for i in range(len(displays)):
      #displays[i].setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
      #frmLayout.addWidget(displays[i], i, 1, 1, 1)

   frmLayout.addItem(QSpacerItem(20, 10, QSizePolicy.Fixed, QSizePolicy.Expanding), 0, 1, 3, 1)
   frm.setLayout(frmLayout)

   return frm




class DlgConfirmSend(QDialog):

   def __init__(self, wlt, recipValPairs, fee, parent=None, main=None, sendNow=False):
      super(DlgConfirmSend, self).__init__(parent)
      
      self.parent = parent
      self.main   = main
      self.wlt    = wlt

      layout = QGridLayout()


      lblInfoImg = QLabel()
      lblInfoImg.setPixmap(QPixmap('img/MsgBox_info48.png'))
      lblInfoImg.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

      totalSend = sum([rv[1] for rv in recipValPairs]) + fee
      sumStr = coin2str(totalSend, maxZeros=1)

      lblMsg = QRichLabel(
         'You are about to spend <b>%s BTC</b> from wallet "<b>%s</b>" (%s).  You '
         'specified the following distribution:' % (sumStr, wlt.labelName, wlt.uniqueIDB58))


      recipLbls = []
      ffixBold = GETFONT('Fixed')
      ffixBold.setWeight(QFont.Bold)
      for rv in recipValPairs:
         addrPrint = (hash160_to_addrStr(rv[0]) + ' : ').ljust(37)
         recipLbls.append(QLabel( addrPrint + coin2str(rv[1], rJust=True, maxZeros=4)))
         recipLbls[-1].setFont(ffixBold)


      if fee>0:
         recipLbls.append(QSpacerItem(10,10))
         recipLbls.append(QLabel( 'Transaction Fee : '.ljust(37)  +
                           coin2str(fee, rJust=True, maxZeros=4)))
         recipLbls[-1].setFont(GETFONT('Fixed'))

      recipLbls.append(HLINE(QFrame.Sunken))
      recipLbls.append(QLabel( 'Total Bitcoins : '.ljust(37)  +
                        coin2str(totalSend, rJust=True, maxZeros=4)))
      recipLbls[-1].setFont(GETFONT('Fixed'))

      lblLastConfirm = QLabel('Are you sure you want to execute this transaction?')

      if sendNow:
         self.btnAccept = QPushButton('Send')
      else:
         self.btnAccept = QPushButton('Continue')
         lblLastConfirm.setText('')

      self.btnCancel = QPushButton("Cancel")
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.accept)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      
      layout.addWidget(lblInfoImg,           0, 0,   1, 1)
      layout.addWidget(lblMsg,               0, 1,   1, 1)

      lblFrm = makeLayoutFrame('Vert', recipLbls, STYLE_RAISED)
      layout.addWidget(lblFrm,               1, 1,   1, 1)

      r = len(recipLbls)+1
      layout.addWidget(lblLastConfirm, 2, 1,  1, 1)
      layout.addWidget(buttonBox,            3, 1,  1, 1)
      layout.setSpacing(20)

      self.setLayout(layout)
      self.setMinimumWidth(350)
      self.setWindowTitle('Confirm Transaction')
      



class DlgSendBitcoins(QDialog):
   COLS = enum('LblAddr','Addr','LblBtc','Btc','LblComm','Comm')
   def __init__(self, wlt, parent=None, main=None, donateIsDefault=False):
      super(DlgSendBitcoins, self).__init__(parent)
      self.maxHeight = tightSizeNChar(GETFONT('var'), 1)[1]+8

      self.parent = parent
      self.main   = main  
      self.wlt    = wlt  

      txFee = self.main.settings.getSettingOrSetDefault('Default_Fee', MIN_TX_FEE)

      self.widgetTable = []

      layout = QGridLayout()
      self.scrollRecipArea = QScrollArea()
      #self.scrollRecipArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
      lblRecip = QRichLabel('<b>Enter Recipients:</b>')
      lblRecip.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
      #'<b>Enter Recipients</b>:  In most cases, you will only be specifying '
      #'one recipient, but you can combine any number of transactions into one '
      #'wallet operation by specifying more.  Blank entries will be ignored')
         

      #lbtnTxFeeOpt = QLabelButton('More Info')
      #self.connect(lbtnTxFeeOpt, SIGNAL('clicked()'), self.txFeeOptions)
      feetip = createToolTipObject( \
            'Transaction fees go to other users who contribute computing power to '
            'keep the Bitcoin network secure, and guarantees that your transaciton '
            'is confirmed in the "blockchain."   <b>Most transactions '
            'do not require</b> a fee but it is recommended to include one anyway '
            'since it guarantees quick processing for less than $0.01 USD.  '  
            'You will will be prompted if a higher fee is '
            'recommended than specified here.')

      self.edtFeeAmt = QLineEdit()
      self.edtFeeAmt.setFont(GETFONT('Fixed'))
      self.edtFeeAmt.setMaximumWidth(tightSizeNChar(self.edtFeeAmt, 12)[0])
      self.edtFeeAmt.setMaximumHeight(self.maxHeight)
      self.edtFeeAmt.setAlignment(Qt.AlignRight)
      self.edtFeeAmt.setText(coin2str(MIN_TX_FEE, ndec=4))

      spacer = QSpacerItem(20, 1)

      layout.addWidget(lblRecip,                   0, 1, 1, 5)
      layout.addWidget(self.scrollRecipArea,       1, 1, 4, 5)


      btnSend = QPushButton('Send!')
      self.connect(btnSend, SIGNAL('clicked()'), self.createTxAndBroadcast)

      txFrm = makeLayoutFrame('Horiz', [QLabel('Transaction Fee:'), \
                                       self.edtFeeAmt, \
                                       feetip, \
                                       'stretch', \
                                       btnSend])
      layout.addWidget(txFrm, 5,1, 1,5)

      

      
      self.frmInfo = getWalletInfoFrame(wlt)
      lblNoSend = QRichLabel('')
      btnUnsigned = QRichLabel('')
      ttipUnsigned = QRichLabel('')

      if not self.main.isOnline:
         lblNoSend.setText(
            '<font color=#550000>'
            'You can sign this transaction, but you do not have '
            'access to the Bitcoin network in order to broadcast '
            'it.  However, you can create the transaction that '
            'you <i>want</i> to send, and then broadcast it from a computer '
            'that <i>is</i> connected to the network.</font>')
      elif wlt.watchingOnly:
         lblNoSend = QRichLabel( \
            '<font color=#550000>'
            'This is an "offline" wallet, which means that the '
            'private keys needed to send Bitcoins are not on this computer. '
            'However, you can create the transaction you would like to '
            'spend, then Armory will provide you with a file that can be '
            'signed by the computer that <i>does</i> have the private '
            'keys.</font>')


      if not wlt.watchingOnly:
         ttipUnsigned = createToolTipObject( \
            'If you would like to create the transaction but not sign it yet, '
            'you can click this button to save it to a file.')
      else:
         ttipUnsigned = createToolTipObject( \
            'After clicking this button, you will be given directions for '
            'completing this transaction.')
         btnSend.setToolTip('You cannot send any Bitcoins from this wallet, from this computer')
         btnSend.setEnabled(False)

      if not self.main.isOnline:
         btnSend.setToolTip('You are currently not connected to the Bitcoin network, '
                            'so you cannot initiate any transactions.')
         btnSend.setEnabled(False)
            
      btnUnsigned = QPushButton('Create Unsigned Transaction')
      self.connect(btnUnsigned, SIGNAL('clicked()'), self.createTxDPAndDisplay)

         
      btnDonate = QPushButton("Donate to Armory Developers!")
      ttipDonate = createToolTipObject( \
         'Making this software was a lot of work.  You can give back '
         'by adding a small donation to the developers of Armory.  '
         'You will have the ability to change the donation amount '
         'before finalizing the transaction.')
      self.connect(btnDonate, SIGNAL("clicked()"), self.addDonation)
      if USE_TESTNET:
         btnDonate.setVisible(False)
         ttipDonate.setVisible(False)

      btnFrame = QFrame()
      btnFrame.setFrameStyle(QFrame.NoFrame)
      btnFrameLayout = QGridLayout()
      btnFrameLayout.addWidget(btnUnsigned,  0,0, 1,1)
      btnFrameLayout.addWidget(ttipUnsigned, 0,1, 1,1)
      btnFrameLayout.addWidget(btnDonate,    1,0, 1,1)
      btnFrameLayout.addWidget(ttipDonate,   1,1, 1,1)
      btnFrame.setLayout(btnFrameLayout)

      #frmUnsigned   = makeLayoutFrame('Horiz', [btnUnsigned, ttipUnsigned])
      #frmDonate     = makeLayoutFrame('Horiz', [btnDonate, ttipDonate])

      frmNoSend     = makeLayoutFrame('Horiz', [lblNoSend], STYLE_SUNKEN)
      if not wlt.watchingOnly:
         frmNoSend.setVisible(False)
         if self.main.usermode==USERMODE.Standard:
            btnUnsigned.setVisible(False)
            ttipUnsigned.setVisible(False)

      frmBottomLeft = makeLayoutFrame('Vert',  [self.frmInfo, \
                                                btnFrame, \
                                                'Stretch', \
                                                frmNoSend], STYLE_SUNKEN)

      lblSend = QRichLabel('<b>Sending from Wallet:</b>')
      lblSend.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

      layout.addWidget(lblSend,       0,0,  1,1)
      layout.addWidget(frmBottomLeft, 1,0,  5,1)
      self.setLayout(layout)

      self.makeRecipFrame(1)
      self.setWindowTitle('Send Bitcoins')
      self.setMinimumHeight(self.maxHeight*20)

      loadCount      = self.main.settings.get('Load_Count')
      alreadyDonated = self.main.settings.getSettingOrSetDefault('DonateAlready', False)
      lastPestering  = self.main.settings.getSettingOrSetDefault('DonateLastPester', 0)
      donateFreq     = self.main.settings.getSettingOrSetDefault('DonateFreq', 20)
      dnaaDonate     = self.main.settings.getSettingOrSetDefault('DonateDNAA', False)
      if not self.main==None and loadCount%donateFreq==(donateFreq-1) and \
         not loadCount==lastPestering and not dnaaDonate and \
         wlt.getBalance('Spendable') > 5*ONE_BTC and not USE_TESTNET:
         result = MsgBoxWithDNAA(MSGBOX.Question, 'Please donate!', \
            '<i>Armory</i> is the result of over 1,000 hours of development '
            'and dozens of late nights bug-hunting and testing.  Yet, this software '
            'has been given to you for free to benefit the greater Bitcoin '
            'community! '
            '<br><br>However, continued development may not be possible without '
            'donations.  If you are satisfied with this software, please consider '
            'donating what you think this software would be worth as a commercial '
            'application.'
            '<br><br><b>Are you willing to donate to the Armory developers?</b> If you '
            'select "Yes," a donation field will be added to your '
            'next transaction.  You will have the opportunity to remove or change '
            'the amount before sending the transaction.', None)

         self.main.settings.set('DonateLastPester', loadCount)

         if result[0]==True:
            self.addDonation(ONE_BTC)
            self.makeRecipFrame(2)

         if result[1]==True:
            self.main.settings.set('DonateDNAA', True)
      
            
         


   #############################################################################
   def createTxDPAndDisplay(self):
      self.txValues = []
      self.origRVPairs = []
      self.comments = []
      txdp = self.validateInputsGetTxDP()

      dlg = DlgConfirmSend(self.wlt, self.origRVPairs, self.txValues[1], self, self.main, False)
      if dlg.exec_():
         #try:
            #if self.wlt.isLocked:
               #unlockdlg = DlgUnlockWallet(self.wlt, self, self.main)
               #if not unlockdlg.exec_():
                  #QMessageBox.critical(self, 'Wallet is Locked', \
                     #'Cannot sign transaction while your wallet is locked. ', \
                     #QMessageBox.Ok)
                  #return
         #except:
            #print 'Issue unlocking wallet!'
            #raise

         dlg = DlgOfflineTxCreated(self.wlt, txdp, self, self.main)
         dlg.exec_()
         self.accept()



   #############################################################################
   def createTxAndBroadcast(self):
      self.txValues = []
      self.origRVPairs = []
      self.comments = []
      txdp = self.validateInputsGetTxDP()
      if not txdp:
         return

      if not self.txValues:
         QMessageBox.critical(self, 'Tx Construction Failed', \
            'Unknown error trying to create transaction', \
            QMessageBox.Ok)
         
      
      #totalOutStr = coin2str(self.txValues[0])
      dlg = DlgConfirmSend(self.wlt, self.origRVPairs, self.txValues[1], self, self.main)
      if dlg.exec_():
         try:
            if self.wlt.isLocked:
               unlockdlg = DlgUnlockWallet(self.wlt, self, self.main, 'Send Transaction')
               if not unlockdlg.exec_():
                  QMessageBox.critical(self, 'Wallet is Locked', \
                     'Cannot sign transaction while your wallet is locked. ', \
                     QMessageBox.Ok)
                  return
              
            
            commentStr = ''
            if len(self.comments)==1:
               commentStr = self.comments[0]
            else:
               for i in range(len(self.comments)):
                  amt = self.origRVPairs[i][1]
                  if len(self.comments[i].strip())>0:
                     commentStr += '%s (%s);  ' % (self.comments[i], coin2str_approx(amt).strip())
            

            txdp = self.wlt.signTxDistProposal(txdp)
            finalTx = txdp.prepareFinalTx()
            if len(commentStr)>0:
               self.wlt.setComment(finalTx.getHash(), commentStr)
            print binary_to_hex(finalTx.serialize())
            print txdp.serializeAscii()
            self.main.broadcastTransaction(finalTx)
            self.accept()
            try:
               self.parent.accept()
            except:
               pass
         except:
            print 'Issue sending!'
            # TODO: not sure what errors to catch here, yet...
            raise



   #############################################################################
   def validateInputsGetTxDP(self):
      COLS = self.COLS
      okayToSend = True
      addrBytes = []
      for i in range(len(self.widgetTable)):
         # Verify validity of address strings
         addrStr = str(self.widgetTable[i][COLS.Addr].text()).strip()
         self.widgetTable[i][COLS.Addr].setText(addrStr) # overwrite w/ stripped
         addrIsValid = False
         try:
            addrBytes.append(checkAddrType(base58_to_binary(addrStr)))
            addrIsValid = (addrBytes[i]==ADDRBYTE)
         except ValueError:
            addrBytes.append(-1)

 
         if not addrIsValid:
            okayToSend = False
            palette = QPalette()
            palette.setColor( QPalette.Base, Colors.LightRed )
            boldFont = self.widgetTable[i][COLS.Addr].font()
            boldFont.setWeight(QFont.Bold)
            self.widgetTable[i][COLS.Addr].setFont(boldFont)
            self.widgetTable[i][COLS.Addr].setPalette( palette );
            self.widgetTable[i][COLS.Addr].setAutoFillBackground( True );


      numChkFail  = sum([1 if b==-1 or b!=ADDRBYTE else 0 for b in addrBytes])
      if not okayToSend:
         QMessageBox.critical(self, 'Invalid Address', \
           'You have entered %d invalid addresses.  The errors have been '
           'highlighted on the entry screen.' % (numChkFail), \
           QMessageBox.Ok)

         for i in range(len(self.widgetTable)):
            if addrBytes[i]!=-1 and addrBytes[i]!=ADDRBYTE:
               net = 'Unknown Network'
               if NETWORKS.has_key(addrBytes[i]):
                  net = NETWORKS[addrBytes[i]]
               QMessageBox.warning(self, 'Wrong Network!', \
                  'Address %d is for the wrong network!  You are on the %s '
                  'and the address you supplied is for the the '
                  '%s!' % (i+1, NETWORKS[ADDRBYTE], net), QMessageBox.Ok)
         return False


      # Construct recipValuePairs and check that all metrics check out
      recipValuePairs = []
      totalSend = 0
      for i in range(len(self.widgetTable)):
         try:
            recipStr = str(self.widgetTable[i][COLS.Addr].text())
            valueStr = str(self.widgetTable[i][COLS.Btc].text())
            feeStr   = str(self.edtFeeAmt.text())

            if '.' in valueStr and len(valueStr.split('.')[-1])>8:
               QMessageBox.critical(self, 'Too much precision', \
                   'Bitcoins can only be '
                   'specified down to 8 decimal places:  the smallest value '
                   'that can be sent is  0.0000 0001 BTC', QMessageBox.Ok)
               return False
         except:
            # TODO: figure out the types of errors we need to deal with, here
            raise

         try:
            value = int(float(valueStr) * ONE_BTC + 0.5)
            if value==0:
               continue
         except ValueError:
            QMessageBox.critical(self, 'Invalid Value String', \
                'The value you specified '
                'to send to address %d is invalid.' % (i+1,), QMessageBox.Ok)
            return False

         try:
            fee = round(float(feeStr) * ONE_BTC)
         except ValueError:
            QMessageBox(self, 'Invalid Value String', 'The fee you specified '
                'is invalid.', QMessageBox.Ok)
            return False
            
         totalSend += value
         recip160 = addrStr_to_hash160(recipStr)
         recipValuePairs.append( (recip160, value) )
         self.comments.append(str(self.widgetTable[i][COLS.Comm].text()))

         
      bal = self.wlt.getBalance('Spendable')
      if totalSend+fee > bal:
         QMessageBox.critical(self, 'Insufficient Funds', 'You just tried to send '
            '%s BTC (including tx fee), but you only have %s BTC (spendable) in this wallet!' % \
               (coin2str(totalSend+fee, maxZeros=2).strip(), \
                coin2str(bal, maxZeros=2).strip()), \
            QMessageBox.Ok)
         return False
      

      # Get unspent outs for this wallet:
      utxoList = self.wlt.getTxOutList('Spendable')
      utxoSelect = PySelectCoins(utxoList, totalSend, fee)



      # TODO:  I should use a while loop/iteration to make sure that the fee
      #        change does not actually induce another, higher fee (which 
      #        is extraordinarily unlikely... I even set up the SelectCoins 
      #        algorithm to try to leave some room in the tx so that the fee
      #        will not change the I/Os).   Despite this, I will concede 
      #        the extremely rare situation where this would happen, I think 
      #        it will be okay to send a slightly sub-optimal fee.  I'll add 
      #        this to my TODO list.
      minFeeRec = calcMinSuggestedFees(utxoSelect, totalSend, fee)
      if fee<minFeeRec[1]:

         overrideMin = self.main.settings.getSettingOrSetDefault('OverrideMinFee', False)
         if totalSend+minFeeRec[1] > bal:
            # Need to adjust this based on overrideMin flag
            QMessageBox.warning(self, 'Insufficient Balance', \
               'You have specified a valid amount to send, but the required '
               'transaction fee causes this transaction to exceed your balance.  '
               'In order to send this transaction, you will be required to '
               'pay a fee of ' + coin2str(minFeeRec[1], maxZeros=0).strip() + '.' 
               'Please go back and adjust the value of your transaction, not '
               'to exceed ' + coin2str(bal-minFeeRec[1], maxZeros=0).strip() + 
               ' BTC.', \
               QMessageBox.Ok)
            self.edtFeeAmt.setText(coin2str(minFeeRec[1]))
            return
                        

         extraMsg = ''
         feeStr = coin2str(fee, maxZeros=0).strip()
         minRecStr = coin2str(minFeeRec[1], maxZeros=0).strip()

         msgBtns = QMessageBox.Yes | QMessageBox.Cancel
         if self.main.usermode in (USERMODE.Advanced, USERMODE.Developer):
            if not overrideMin:
               extraMsg = ('\n\n(It is not recommended to override this behavior, '
                           'but as an advanced user, you can go into the settings file '
                           'and manually change the "OverrideMinFee" property to '
                           '"True".  Do so at your own risk, as many transactions '
                           'have been known to "get stuck" when insufficient fee '
                           'was included)')

         if overrideMin:
            msgBtns = QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            extraMsg = ('\n\nYou have disbled mandatory transaction fees.  '
                        'Clicking "No" will send the transaction with the '
                        'original fee that you specified.')

         reply = QMessageBox.warning(self, 'Insufficient Fee', \
            'The fee you have specified (%s BTC) is insufficient for the size '
            'and priority of your transaction.  You must include at least '
            '%s BTC to send this transaction.  \n\nDo you agree to the fee of %s BTC?  ' % \
            (feeStr, minRecStr, minRecStr) + extraMsg,  msgBtns)
         if reply == QMessageBox.Cancel:
            return False
         if reply == QMessageBox.No:
            pass
         elif reply==QMessageBox.Yes:
            fee = long(minFeeRec[1])
            utxoSelect = PySelectCoins(utxoSelect, totalSend, fee)
      
      if len(utxoSelect)==0:
         QMessageBox.critical(self, 'Coin Selection Error', \
            'SelectCoins returned a list of size zero.  This is problematic '
            'and probably not your fault.', QMessageBox.Ok)
         return
         

      ### IF we got here, everything should be good to go... generate a new
      #   address, calculate the change (add to recip list) and do our thing.
      totalTxSelect = sum([u.getValue() for u in utxoSelect])
      totalChange = totalTxSelect - (totalSend + fee)

      self.origRVPairs = list(recipValuePairs)
      if totalChange>0:
         recipValuePairs.append( [self.wlt.getNextUnusedAddress().getAddr160(), totalChange])
   
      # Anonymize the outputs
      random.shuffle(recipValuePairs)
      txdp = PyTxDistProposal().createFromTxOutSelection( utxoSelect, \
                                                          recipValuePairs)

      self.txValues = [totalSend, fee, totalChange]
      return txdp

      
            
   #############################################################################
   def addDonation(self, amt=ONE_BTC):
      COLS = self.COLS
      lastIsEmpty = True
      for col in (COLS.Addr, COLS.Btc, COLS.Comm):
         if len(str(self.widgetTable[-1][col].text()))>0:
            lastIsEmpty = False
         
      if not lastIsEmpty:
         self.makeRecipFrame( len(self.widgetTable)+1 )

      self.widgetTable[-1][self.COLS.Addr].setText(ARMORY_DONATION_ADDR)
      self.widgetTable[-1][self.COLS.Btc].setText(coin2str(amt, maxZeros=2).strip())
      self.widgetTable[-1][self.COLS.Comm].setText(\
            'Donation to Armory developers.  Thank you for your generosity!')

   #####################################################################
   def makeRecipFrame(self, nRecip):
      prevNRecip = len(self.widgetTable)
      nRecip = max(nRecip, 1)
      inputs = []
      for i in range(nRecip):
         if i<prevNRecip and i<nRecip:
            inputs.append([])
            for j in (1,3,5):
               inputs[-1].append(str(self.widgetTable[i][j].text()))


      frmRecip = QFrame()
      frmRecip.setFrameStyle(QFrame.NoFrame)
      frmRecipLayout = QVBoxLayout()

      COLS = self.COLS 
      
      self.widgetTable = []
      for i in range(nRecip):
         self.widgetTable.append([])

         self.widgetTable[-1].append( QLabel('Address %d:' % (i+1,)) )

         self.widgetTable[-1].append( QLineEdit() )
         self.widgetTable[-1][-1].setMinimumWidth(relaxedSizeNChar(GETFONT('var'), 40)[0])
         self.widgetTable[-1][-1].setMaximumHeight(self.maxHeight)
         self.widgetTable[-1][-1].setFont(GETFONT('var',9))

         self.widgetTable[-1].append( QLabel('BTC:') )

         self.widgetTable[-1].append( QLineEdit() )
         self.widgetTable[-1][-1].setFont(GETFONT('Fixed'))
         self.widgetTable[-1][-1].setMaximumWidth(tightSizeNChar(GETFONT('Fixed'), 10)[0])
         self.widgetTable[-1][-1].setMaximumHeight(self.maxHeight)
         self.widgetTable[-1][-1].setAlignment(Qt.AlignRight)
      
         self.widgetTable[-1].append( QLabel('Comment:') )
         self.widgetTable[-1].append( QLineEdit() )
         self.widgetTable[-1][-1].setFont(GETFONT('var', 9))
         self.widgetTable[-1][-1].setMaximumHeight(self.maxHeight)

         if i<nRecip and i<prevNRecip:
            self.widgetTable[-1][COLS.Addr].setText( inputs[i][0] )
            self.widgetTable[-1][COLS.Btc ].setText( inputs[i][1] )
            self.widgetTable[-1][COLS.Comm].setText( inputs[i][2] )

         subfrm = QFrame()
         subfrm.setFrameStyle(STYLE_RAISED)
         subLayout = QGridLayout()
         subLayout.addWidget(self.widgetTable[-1][COLS.LblAddr], 0, 0, 1, 1)
         subLayout.addWidget(self.widgetTable[-1][COLS.Addr],    0, 1, 1, 1)
         subLayout.addWidget(self.widgetTable[-1][COLS.LblBtc],  0, 2, 1, 1)
         subLayout.addWidget(self.widgetTable[-1][COLS.Btc],     0, 3, 1, 1)
         subLayout.addWidget(self.widgetTable[-1][COLS.LblComm], 1, 0, 1, 1)
         subLayout.addWidget(self.widgetTable[-1][COLS.Comm],    1, 1, 1, 3)
         subLayout.setContentsMargins(15,15,15,15)
         subLayout.setSpacing(3)
         subfrm.setLayout(subLayout)

         frmRecipLayout.addWidget(subfrm)

         
      btnFrm = QFrame()
      btnFrm.setFrameStyle(QFrame.NoFrame)
      btnLayout = QHBoxLayout()
      lbtnAddRecip = QLabelButton('+ Recipient')
      lbtnAddRecip.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lbtnRmRecip  = QLabelButton('- Recipient')
      lbtnRmRecip.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      self.connect(lbtnAddRecip, SIGNAL('clicked()'), lambda: self.makeRecipFrame(nRecip+1))
      self.connect(lbtnRmRecip,  SIGNAL('clicked()'), lambda: self.makeRecipFrame(nRecip-1))
      btnLayout.addStretch()
      btnLayout.addWidget(lbtnAddRecip)
      btnLayout.addWidget(lbtnRmRecip)
      btnFrm.setLayout(btnLayout)

      #widgetsForWidth = [COLS.LblAddr, COLS.Addr, COLS.LblBtc, COLS.Btc]
      #minScrollWidth = sum([self.widgetTable[0][col].width() for col in widgetsForWidth])

      frmRecipLayout.addWidget(btnFrm)
      frmRecipLayout.addStretch()
      frmRecip.setLayout(frmRecipLayout)
      #return frmRecip
      self.scrollRecipArea.setWidget(frmRecip)


   def txFeeOptions(self):
      dlg = DlgTxFeeOptions(self, self, self.main)
      if dlg.exec_():
         # TODO: do something!
         pass



class DlgOfflineTxCreated(QDialog):
   def __init__(self, wlt, txdp, parent=None, main=None):
      super(DlgOfflineTxCreated, self).__init__(parent)

      self.parent = parent
      self.main   = main
      self.txdp   = txdp
      self.wlt    = wlt

      canSign = False
      lblDescr = QRichLabel('')
      if determineWalletType(wlt, self.main)[0]==WLTTYPES.Offline:
         lblDescr.setText(
         'The block of data shown below is the complete transaction you just '
         'requested, but is invalid because it does not contain the appropriate '
         'signatures.  You must '
         'take this data to the computer holding the private keys for this '
         'wallet to get the necessary signatures, then bring back the completed '
         'transaction to be broadcast to the Bitcoin network.'
         '<br><br>'
         'Use the "Save as file..." button '
         'to copy the <i>*.unsigned.tx</i> file to a USB key or other removable media.  '
         'Take the file to the offline computer, and use the '
         '"Offline Transactions" dialog to load the transaction data and sign it '
         '(the filename suffix will be changed to *.signed.tx).'
         '<br><br>'
         'On the next screen, you will be able to load the signed transaction, '
         'and then broadcast it if all signatures are valid.   In fact, the final, '
         'signed transaction can be finalized from <i>any</i> '
         'computer that is running Armory and connected to the Bitcoin network.')
      elif determineWalletType(wlt, self.main)[0]==WLTTYPES.WatchOnly: 
         lblDescr.setText( \
         'The chunk of data shown below is the complete transaction you just '
         'requested, but <b>without</b> the signatures needed to be valid.  '
         '<br><br>'
         'In order to complete this transaction, you need to send this '
         'chunk of data (the proposed transaction) to the party who holds the '
         'private keys for this wallet.  They can load this data into Armory '
         'and broadcast the transaction if they chose to sign it. ')
      else:
         canSign = True
         lblDescr.setText(
            'You have chosen to create the previous transaction but not sign '
            'it or broadcast it, yet.  Below, you can save the unsigned '
            'transaction to file, or copy&paste from the text box.  '
            'In some cases, you may actually want the transaction signed '
            'but not broadcast yet.  On the "Next Step" you can choose to sign '
            'the transaction without broadcasting it.')


      ttipBip0010 = createToolTipObject( \
         'The serialization used in this block of data is based on BIP 0010, '
         'which is a standard proposed by the core Armory Developer (Alan Reiner) '
         'for simple execution of offline transactions and multi-signature '
         'transactions.  Any other client software that implements BIP 0010 '
         'will be able to recognize '
         'this block of data, and take appropriate action without having Armory '
         'software available.   Technical details of BIP 0010 can be found at: '
         'https://en.bitcoin.it/wiki/BIP_0010')


      ttipDataIsSafe = createToolTipObject( \
         'There is no security-sensitive information in this data below, so '
         'it is perfectly safe to copy-and-paste it into an '
         'email message, or save it to a borrowed USB key.')
      
      btnSave = QPushButton('Save as file...')
      self.connect(btnSave, SIGNAL('clicked()'), self.doSaveFile)
      ttipSave = createToolTipObject( \
         'Save this data to a USB key or other device, to be transferred to '
         'a computer that contains the private keys for this wallet.')

      btnCopy = QPushButton('Copy to clipboard')
      self.connect(btnCopy, SIGNAL('clicked()'), self.copyAsciiTxDP)
      self.lblCopied = QRichLabel('  ')
      self.lblCopied.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      ttipCopy = createToolTipObject( \
         'Copy the transaction data to the clipboard, so that it can be '
         'pasted into an email or a text document.')

      lblInstruct = QRichLabel('<b>Instructions for completing this transaction:</b>')
      lblUTX = QRichLabel('<b>Transaction Data</b> \t (Unsigned ID: %s)' % txdp.uniqueB58)
      w,h = tightSizeStr(GETFONT('Fixed',8),'0'*85)[0], int(12*8.2)

      frmUTX = makeLayoutFrame('Horiz', [ttipDataIsSafe, lblUTX])
      frmUpper = makeLayoutFrame('Horiz', [lblDescr], STYLE_SUNKEN)

      # Wow, I just cannot get the txtEdits to be the right size without
      # forcing them very explicitly
      self.txtTxDP = QTextEdit()
      self.txtTxDP.setFont( GETFONT('Fixed',8) )
      self.txtTxDP.setMinimumWidth(w)
      self.txtTxDP.setMinimumHeight(h)
      self.txtTxDP.setMaximumWidth(w)
      self.txtTxDP.setMaximumHeight(h)
      self.txtTxDP.setText(txdp.serializeAscii())
      self.txtTxDP.setReadOnly(True)
      self.txtTxDP.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)


      lblNextStep = QRichLabel( \
         'Once you have signed the transaction, you can go onto the next '
         'step.  Alternatively, you can close this window, and complete the '
         'last step at a later time, using the "Offline Transactions" button '
         'on the main window')
      btnNextStep = QPushButton('Next Step >>>')
      maxBtnWidth = 1.5*relaxedSizeStr(btnNextStep, 'Next Step >>>')[0]
      btnNextStep.setMaximumWidth(maxBtnWidth)
      self.connect(btnNextStep, SIGNAL('clicked()'), self.doNextStep)

      nextStepStrip = makeLayoutFrame('Horiz', [lblNextStep, btnNextStep], \
                                                                     STYLE_SUNKEN)

      btnLater = QPushButton("Close Window")
      self.connect(btnLater, SIGNAL('clicked()'), self.reject)
      bottomStrip = makeLayoutFrame('Horiz', [btnLater, 'Stretch'])


      frmLower = QFrame()
      frmLower.setFrameStyle(STYLE_RAISED)
      frmLowerLayout = QGridLayout()
      
      frmLowerLayout.addWidget(frmUTX,        0,0,  1,3)
      frmLowerLayout.addWidget(self.txtTxDP,  1,0,  3,1)
      frmLowerLayout.addWidget(btnSave,       1,1,  1,1)
      frmLowerLayout.addWidget(ttipSave,      1,2,  1,1)
      frmLowerLayout.addWidget(btnCopy,       2,1,  1,1)
      frmLowerLayout.addWidget(ttipCopy,      2,2,  1,1)
      frmLowerLayout.addWidget(self.lblCopied,3,1,  1,2)

      frmLowerLayout.addWidget(nextStepStrip, 4,0,  1,3)
      frmLower.setLayout(frmLowerLayout)


      frmAll = makeLayoutFrame('Vert', [lblInstruct, \
                                        frmUpper, \
                                        'Space(5)', \
                                        frmLower, \
                                        nextStepStrip,\
                                        bottomStrip])

      dlgLayout = QGridLayout()
      dlgLayout.addWidget(frmAll)

      self.setLayout(dlgLayout)
      self.setWindowTitle("Offline Transaction")
      self.setWindowIcon(QIcon( self.main.iconfile))

   def copyAsciiTxDP(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.txtTxDP.toPlainText())
      self.lblCopied.setText('<i>Copied!</i>')

   def copyAsciiTxDPS(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.txtSigned.toPlainText())
      self.lblCopiedS.setText('<i>Copied!</i>')

   def doSaveFile(self):
      """ Save the Unsigned-Tx block of data """
      dpid = self.txdp.uniqueB58
      toSave = self.main.getFileSave( 'Save Unsigned Transaction', \
                                      ['Armory Transactions (*.unsigned.tx)'], \
                                      'armory_%s_.unsigned.tx' % dpid)
      try:
         theFile = open(toSave, 'w')
         theFile.write(self.txtTxDP.toPlainText())
         theFile.close()
      except IOError:
         pass

   def doSaveFileS(self):
      """ Save the Signed-Tx block of data """
      dpid = self.txdp.uniqueB58
      toSave = self.main.getFileSave( 'Save Signed Transaction', \
                                      ['Armory Transactions (*.signed.tx)'], \
                                      'armory_%s_.signed.tx' % dpid)
      try:
         theFile = open(toSave, 'w')
         theFile.write(self.txtSigned.toPlainText())
         theFile.close()
      except IOError:
         pass

   def txtSignedFirstClick(self):
      if not self.txtSignedCleared:
         self.txtSignedCleared = True
         self.txtSigned.setText('')
         self.txtSigned.setTextColor(Colors.Black)

      txt = str(self.txtSigned.toPlainText())
      a,b = '<b><i><font color="red">', '</font></i></b>'
      lblText = ''
      if not txt.startswith('-----BEGIN-TRANSACTION'):
         self.lblRight.setText('')
         self.btnReady.setEnabled(False)
         return

      try:
         txdpSigned = PyTxDistProposal().unserializeAscii(str(self.txtSigned.toPlainText()))
         enoughSigs = txdpSigned.checkTxHasEnoughSignatures()
         sigsValid  = txdpSigned.checkTxHasEnoughSignatures(alsoVerify=True)
         if not enoughSigs:
            self.lblRight.setText(a + 'Not Signed!' + b)
            self.btnReady.setEnabled(False)
            return
         if not sigsValid:
            self.lblRight.setText(a + 'Invalid Signature!' + b)
            self.btnReady.setEnabled(False)
            return
      except:
         # One of the rare few times I ever catch-all exception
         self.lblRight.setText(a + 'Unrecognized Input!' + b)
         self.btnReady.setEnabled(False)
         return

      self.lblRight.setText('<b><i><font color="green">Signature Valid!</font></i></b>')
      self.btnReady.setEnabled(True)
      
   def execLoadSig(self):
      self.txtSignedFirstClick()
      fn = self.main.getFileLoad( title = 'Load Signed Transaction', \
                                  ffilter=['Signed Transactions (*.signed.tx)'])
      fileobj = open(fn, 'r')
      txdpStr = fileobj.read()
      fileobj.close()
      self.txtSigned.setText(txdpStr)
      self.txtSignedFirstClick()

   def execBroadcast(self):
      txdpSigned = PyTxDistProposal().unserializeAscii(str(self.txtSigned.toPlainText()))
      finalTx = txdpSigned.getBroadcastTxIfReady()
      if not txdpSigned.uniqueB58==self.txdp.uniqueB58:
         QMessageBox.critical(self, 'Wrong Transaction!', \
           'The transaction you loaded is valid, but is a different transaction '
           'than the one you started with.  Please go back check that you copied '
           'or loaded the correct transaction.',  QMessageBox.Ok)
         return

      if finalTx==None:
         QMessageBox.critical(self, 'Error', \
           'There was an error finalizing the transaction.  Double-check '
           'that the correct data was loaded into the text box',  QMessageBox.Ok)
         return
         

      self.main.broadcastTransaction(finalTx)
      self.accept()
      try:
         self.parent.accept()
      except:
         pass


   def signTxdp(self):
      try:
         strUnsign = str(self.txtTxDP.toPlainText())
         txdpUnsign = PyTxDistProposal().unserializeAscii(strUnsign)
      except:
         raise

      if self.wlt.useEncryption and self.wlt.isLocked:
         dlg = DlgUnlockWallet(self.wlt, self.parent, self.main, 'Sign Transaction')
         if not dlg.exec_():
            QMessageBox.warning(self, 'Unlock Error', \
               'Cannot sign this transaction while your wallet is locked.  '
               'Please enter the correct passphrase to finish signing.', \
               QMessageBox.Ok)
            return

   
      txdpSign = self.wlt.signTxDistProposal(txdpUnsign)
      self.txtSigned.setText(txdpSign.serializeAscii())
      self.btnSaveS.setEnabled(True)
      self.btnCopyS.setEnabled(True)
            
   
   def doNextStep(self):
      DlgReviewOfflineTx(self, self.main).exec_()
      self.accept()
            


################################################################################
class DlgOfflineSelect(QDialog):
   def __init__(self, parent=None, main=None):
      super(DlgOfflineSelect, self).__init__(parent)

      self.parent = parent
      self.main   = main

      self.do_review = False
      self.do_create = False
      self.do_broadc = False
      lblDescr = QRichLabel( \
         'In order to execute an offline transaction, three steps must '
         'be followed: <br><br>'
         '\t(1) <u>On</u>line:  Create the unsigned transaction<br>'
         '\t(2) <u>Off</u>line: Get the transaction signed<br>'
         '\t(3) <u>On</u>line:  Broadcast the signed transaction<br><br>'
         'Transactions can only be created by online computers, but watching-only '
         'wallets cannot sign them.  The easiest way to execute all three steps '
         'is to use a USB key to move the data between computers.<br><br>'
         'All the data produced during all three steps are completely '
         'safe and do not reveal any private information that would benefit an '
         'attacker.  It is acceptable to send transaction data over email or '
         'copy it to a borrowed USB key.  Also, steps 1 and 3 do <u>not</u> '
         'have to be performed on the same computer.')

      btnCreate = QPushButton('Create New Offline Transaction')
      btnReview = QPushButton('Sign and/or Broadcast Transaction')
      if not self.main.internetAvail or not self.main.satoshiAvail:
         if len(self.main.walletMap)==0:
            btnReview = QPushButton('No wallets, no network connection')
            btnReview.setEnabled(False)
         else:
            btnReview = QPushButton('Sign Offline Transaction')
      elif len(self.main.walletMap)==0:
         btnReview = QPushButton('Broadcast Signed Transaction')

      btnCancel = QPushButton('<<< Go Back')

      def create():
         self.do_create = True; self.accept()
      def review():
         self.do_review = True; self.accept()
      def broadc():
         self.do_broadc = True; self.accept()

      self.connect(btnCreate, SIGNAL('clicked()'), create)
      self.connect(btnReview, SIGNAL('clicked()'), review)
      self.connect(btnCancel, SIGNAL('clicked()'), self.reject)

      lblCreate = QRichLabel( \
         'Create a transaction from an Offline/Watching-Only wallet '
         'to be signed by the computer with the full wallet')

      lblReview = QRichLabel( \
         'Review an unsigned transaction and sign it if you have '
         'the private keys needed for it' )
         
      lblBroadc = QRichLabel( \
         'Send a pre-signed transaction to the Bitcoin network to finalize it')

      lblBroadc.setMinimumWidth( tightSizeNChar(lblBroadc, 45)[0] )

      
      frmOptions = QFrame()
      frmOptions.setFrameStyle(QFrame.Box | QFrame.Plain)
      frmOptionsLayout = QGridLayout()
      frmOptionsLayout.addWidget(btnCreate,  0,0)
      frmOptionsLayout.addWidget(lblCreate,  0,2)
      frmOptionsLayout.addWidget(HLINE(),  1,0, 1,3)
      frmOptionsLayout.addWidget(btnReview,  2,0, 3,1)
      frmOptionsLayout.addWidget(lblReview,  2,2)
      frmOptionsLayout.addWidget(HLINE(),  3,2, 1,1)
      frmOptionsLayout.addWidget(lblBroadc,  4,2)




      frmOptionsLayout.addItem(QSpacerItem(20,20),  0,1, 3,1)
      frmOptions.setLayout(frmOptionsLayout)

      frmDescr = makeLayoutFrame('Horiz', ['Space(10)', lblDescr, 'Space(10)'], \
                                             STYLE_SUNKEN)
      frmCancel = makeLayoutFrame('Horiz', [btnCancel, 'Stretch'])

      dlgLayout = QGridLayout()
      dlgLayout.addWidget(frmDescr,   0,0,  1,1 )
      dlgLayout.addWidget(frmOptions, 1,0,  1,1 )
      dlgLayout.addWidget(frmCancel,  2,0,  1,1 )
      

      self.setLayout(dlgLayout)
      self.setWindowTitle('Select Offline Action')
      self.setWindowIcon(QIcon(self.main.iconfile))
   
      

################################################################################
class DlgReviewOfflineTx(QDialog):
   """
   We will make the assumption that this dialog is used ONLY for outgoing 
   transactions from your wallet.  This simplifies the logic if we don't 
   have to identify input senders/values, and handle the cases where those 
   may not be specified
   """
   def __init__(self, parent=None, main=None):
      super(DlgReviewOfflineTx, self).__init__(parent)


      self.parent = parent
      self.main   = main
      self.wlt    = None
      self.sentToSelfWarn = False
      self.fileLoaded = None


      lblDescr = QRichLabel( \
         'Copy or load a transaction from file into the text box below.  '
         'If the transaction is unsigned and you have the correct wallet, '
         'you will have the opportunity to sign it.  If it is already signed '
         'you will have the opportunity to broadcast it to '
         'the Bitcoin Network to make it final.')



      w,h = tightSizeStr(GETFONT('Fixed',8),'0'*85)[0], int(12*8.2)
      self.txtTxDP = QTextEdit()
      self.txtTxDP.setFont( GETFONT('Fixed',8) )
      self.txtTxDP.sizeHint = lambda: QSize(w,h)
      self.txtTxDP.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

      self.btnSign      = QPushButton('Sign')
      self.btnBroadcast = QPushButton('Broadcast')
      self.btnSave      = QPushButton('Save file...')
      self.btnLoad      = QPushButton('Load file...')
      self.btnCopy      = QPushButton('Copy Text')
      self.lblCopied    = QRichLabel('')
      self.lblCopied.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      self.btnSign.setEnabled(False)
      self.btnBroadcast.setEnabled(False)

      self.connect(self.txtTxDP, SIGNAL('textChanged()'), self.processTxDP)
      

      self.connect(self.btnSign,      SIGNAL('clicked()'), self.signTx)
      self.connect(self.btnBroadcast, SIGNAL('clicked()'), self.broadTx)
      self.connect(self.btnSave,      SIGNAL('clicked()'), self.saveTx)
      self.connect(self.btnLoad,      SIGNAL('clicked()'), self.loadTx)
      self.connect(self.btnCopy,      SIGNAL('clicked()'), self.copyTx)

      self.lblStatus = QRichLabel('')
      self.lblStatus.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      wStat, hStat = relaxedSizeStr(self.lblStatus, 'Signature is Invalid!')
      self.lblStatus.setMinimumWidth( int(wStat*1.2) )
      self.lblStatus.setMinimumHeight( int(hStat*1.2) )

      btnGoBack = QPushButton('<<< Go Back')
      self.connect(btnGoBack,   SIGNAL('clicked()'), self.accept)
      frmGoBack = makeLayoutFrame('Horiz', [btnGoBack, 'Stretch'])
      

      frmDescr = makeLayoutFrame('Horiz', [lblDescr], STYLE_RAISED)


      # Finally, let's make small info frame, with a button to link to the 
      # full info
      self.infoLbls = []

      
      ###
      self.infoLbls.append([])
      self.infoLbls[-1].append( createToolTipObject( \
            'This is wallet from which the offline transaction spends Bitcoins'))
      self.infoLbls[-1].append( QRichLabel('<b>Wallet:</b>'))
      self.infoLbls[-1].append( QRichLabel(''))

      ###
      self.infoLbls.append([])
      self.infoLbls[-1].append( createToolTipObject('The name of the wallet'))
      self.infoLbls[-1].append( QRichLabel('<b>Wallet Label:</b>'))
      self.infoLbls[-1].append( QRichLabel(''))
      
      ###
      self.infoLbls.append([])
      self.infoLbls[-1].append( createToolTipObject( \
         'A unique string that identifies an <i>unsigned</i> transaction.  '
         'This is different than the ID that the transaction will have when '
         'it is finally broadcast, because the broadcast ID cannot be '
         'calculated without all the signatures'))
      self.infoLbls[-1].append( QRichLabel('<b>Pre-Broadcast ID:</b>'))
      self.infoLbls[-1].append( QRichLabel(''))

      ###
      self.infoLbls.append([])
      self.infoLbls[-1].append( createToolTipObject('Net effect on this wallet\'s balance'))
      self.infoLbls[-1].append( QRichLabel('<b>Transaction Amount:</b>'))
      self.infoLbls[-1].append( QRichLabel(''))


      ###
      #self.infoLbls.append([])
      #self.infoLbls[-1].append( createToolTipObject( \
            #'Total number of transaction recipients, excluding change transactions.'))
      #self.infoLbls[-1].append( QRichLabel('<b># Recipients:</b>'))
      #self.infoLbls[-1].append( QRichLabel(''))

      ###
      #self.infoLbls.append([])
      #self.infoLbls[-1].append( createToolTipObject( \
            #'Click for more details about this transaction'))
      #self.infoLbls[-1].append( QRichLabel('<b>More Info:</b>'))
      #self.infoLbls[-1].append( QLabelButton('Click Here') )


      self.moreInfo = QLabelButton('Click here for more<br> information about <br>this transaction')
      self.connect(self.moreInfo, SIGNAL('clicked()'), self.execMoreTxInfo)
      frmMoreInfo = makeLayoutFrame('Horiz', [self.moreInfo], STYLE_SUNKEN)
      frmMoreInfo.setMinimumHeight( tightSizeStr(self.moreInfo, 'Any String')[1]*5)

      frmBtn = makeLayoutFrame('Vert', [ self.btnSign, \
                                         self.btnBroadcast, \
                                         self.btnSave, \
                                         self.btnLoad, \
                                         self.btnCopy, \
                                         self.lblCopied, \
                                         HLINE(), \
                                         self.lblStatus, \
                                         HLINE(), \
                                         'Stretch', \
                                         frmMoreInfo])

      frmBtn.setMaximumWidth(tightSizeNChar(QPushButton(''), 30)[0])

      frmInfoLayout = QGridLayout()
      for r in range(len(self.infoLbls)):
         for c in range(len(self.infoLbls[r])):
            frmInfoLayout.addWidget( self.infoLbls[r][c],  r,c,  1,1 )

      frmInfo = QFrame()
      frmInfo.setFrameStyle(STYLE_SUNKEN)
      frmInfo.setLayout(frmInfoLayout)

      frmBottom = QFrame()
      frmBottom.setFrameStyle(STYLE_SUNKEN)
      frmBottomLayout = QGridLayout()
      frmBottomLayout.addWidget(self.txtTxDP,  0,0,  1,1)
      frmBottomLayout.addWidget(frmBtn,        0,1,  2,1)
      frmBottomLayout.addWidget(frmInfo,       1,0,  1,1)
      #frmBottomLayout.addWidget(frmMoreInfo,   1,1,  1,1)
      frmBottom.setLayout(frmBottomLayout)

      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(frmDescr)
      dlgLayout.addWidget(frmBottom)
      dlgLayout.addWidget(frmGoBack)

      self.setLayout(dlgLayout)
      self.processTxDP()
      
      self.setWindowTitle('Review Offline Transaction')
      self.setWindowIcon(QIcon( self.main.iconfile))

      

   def processTxDP(self):
      # TODO:  it wouldn't be TOO hard to modify this dialog to take 
      #        arbitrary hex-serialized transactions for broadcast... 
      #        but it's not trivial either (for instance, I assume 
      #        that we have inputs values, etc)

      self.wlt     = None
      self.leValue = None
      self.txdpObj = None
      self.idxSelf = []
      self.idxOther = []
      self.lblStatus.setText('')
      self.lblCopied.setText('')
      self.enoughSigs = False
      self.sigsValid  = False
      self.txdpReadable  = False

      txdpStr = str(self.txtTxDP.toPlainText())
      try:
         self.txdpObj = PyTxDistProposal().unserializeAscii(txdpStr)
         self.enoughSigs = self.txdpObj.checkTxHasEnoughSignatures()
         self.sigsValid  = self.txdpObj.checkTxHasEnoughSignatures(alsoVerify=True)
         self.txdpReadable = True
      except BadAddressError:
         QMessageBox.critical(self, 'Inconsistent Data!', \
            'This transaction contains inconsistent information.  This '
            'is probably not your fault...', QMessageBox.Ok)
         self.txdpObj = None
         self.txdpReadable = False
      except NetworkIDError:
         QMessageBox.critical(self, 'Wrong Network!', \
            'This transaction is actually for a different network!  '
            'Did you load the correct transaction?', QMessageBox.Ok)
         self.txdpObj = None
         self.txdpReadable = False
      except (UnserializeError, IndexError, ValueError):
         self.txdpObj = None
         self.txdpReadable = False

      if not self.enoughSigs or not self.sigsValid or not self.txdpReadable:
         self.btnBroadcast.setEnabled(False)
      else:
         if self.main.internetAvail and self.main.satoshiAvail:
            self.btnBroadcast.setEnabled(True)
         else:
            self.btnBroadcast.setEnabled(False)
            self.btnBroadcast.setToolTip('No connection to Bitcoin network!')

      if not self.txdpReadable:
         if len(txdpStr)>0:
            self.lblStatus.setText('<b><font color="red">Unrecognized!</font></b>')
         else:
            self.lblStatus.setText('')
         self.btnSign.setEnabled(False)
         self.btnBroadcast.setEnabled(False)
         self.makeReviewFrame()
         return
      elif not self.enoughSigs:
         self.lblStatus.setText('<b><font color="red">Unsigned</font></b>')
         self.btnSign.setEnabled(True)
         self.btnBroadcast.setEnabled(False)
      elif not self.sigsValid:
         self.lblStatus.setText('<b><font color="red">Bad Signature!</font></b>')
         self.btnSign.setEnabled(True)
         self.btnBroadcast.setEnabled(False)
      else:
         self.lblStatus.setText('<b><font color="green">All Signatures Valid!</font></b>')
         self.btnSign.setEnabled(False)
      

      # NOTE:  We assume this is an OUTGOING transaction.  When I pull in the
      #        multi-sig code, I will have to either make a different dialog,
      #        or add some logic to this one
      FIELDS = enum('Hash','OutList','SumOut','InList','SumIn', 'Time', 'Blk', 'Idx')
      data = extractTxInfo(self.txdpObj, -1)

      # Collect the input wallets (hopefully just one of them)
      fromWlts = set()
      for recip,amt,a,b,c in data[FIELDS.InList]:
         wltID = self.main.getWalletForAddr160(recip)
         if not wltID=='':
            fromWlts.add(wltID)

      if len(fromWlts)>1:
         QMessageBox.warning(self, 'Multiple Input Wallets', \
            'Somehow, you have obtained a transaction that actually pulls from more '
            'than one wallet.  The support for handling multi-wallet signatures is '
            'not currently implemented (this also could have happened if you imported '
            'the same private key into two different wallets).' ,QMessageBox.Ok)
         self.makeReviewFrame()
         return
      elif len(fromWlts)==0:
         QMessageBox.warning(self, 'Unrelated Transaction', \
            'This transaction appears to have no relationship to any of the wallets '
            'stored on this computer.  Did you load the correct transaction?', \
            QMessageBox.Ok)
         self.makeReviewFrame()
         return

      spendWltID = fromWlts.pop()
      self.wlt = self.main.walletMap[spendWltID]
      

      toWlts = set()
      myOutSum = 0
      theirOutSum = 0
      rvPairs = []
      idx = 0
      for scrType, amt, recip in data[FIELDS.OutList]:
         wltID = self.main.getWalletForAddr160(recip)
         if wltID==spendWltID:
            toWlts.add(wltID)
            myOutSum += amt
            self.idxSelf.append(idx)
         else:
            rvPairs.append( [recip, amt] )
            theirOutSum += amt
            self.idxOther.append(idx)
         idx += 1

         

      myInSum = data[FIELDS.SumIn]  # because we assume all are ours

      if myInSum == None:
         fee = None
      else:
         fee = myInSum - data[FIELDS.SumOut]
         
      self.leValue = theirOutSum
      self.makeReviewFrame()


   ############################################################################
   def makeReviewFrame(self):


      ###
      if self.txdpObj==None: 
         self.infoLbls[0][2].setText('')
         self.infoLbls[1][2].setText('')
         self.infoLbls[2][2].setText('')
         self.infoLbls[3][2].setText('')
         #self.infoLbls[4][2].setText('')
         #self.infoLbls[5][0].setVisible(False)
         #self.infoLbls[5][1].setVisible(False)
         #self.infoLbls[5][2].setVisible(False)
         #self.moreInfo.setVisible(False)
      else:          
         ##### 0

         ##### 1
         if self.wlt: 
            self.infoLbls[0][2].setText(self.wlt.uniqueIDB58)
            self.infoLbls[1][2].setText(self.wlt.labelName)
         else:        
            self.infoLbls[0][2].setText('[[ Unrelated ]]')
            self.infoLbls[1][2].setText('')

         ##### 2
         self.infoLbls[2][2].setText(self.txdpObj.uniqueB58)

         ##### 3
         if self.leValue:
            self.infoLbls[3][2].setText(coin2str(self.leValue, maxZeros=0).strip() + '  BTC')
         else:
            self.infoLbls[3][2].setText('')

         ##### 4
         #if self.idxOther:
            #self.infoLbls[4][2].setText(str(len(self.idxOther)))
         #else:
            #self.infoLbls[4][2].setText('')

         ##### 5
         #self.infoLbls[5][0].setVisible(True)
         #self.infoLbls[5][1].setVisible(True)
         #self.infoLbls[5][2].setVisible(True)
         self.moreInfo.setVisible(True)







   def execMoreTxInfo(self):
      
      if not self.txdpObj:
         self.processTxDP()

      if not self.txdpObj:
         QMessageBox.warning(self, 'No Transaction Info', \
            'There is no transaction information to display!', QMessageBox.Ok)
         return

      dlgTxInfo = DlgDispTxInfo(self.txdpObj, self.wlt, self.parent, self.main, \
                          precomputeIdxGray=self.idxSelf, precomputeAmt=-self.leValue, txtime=-1)
      dlgTxInfo.exec_()



   def signTx(self):
      if not self.txdpObj:
         QMessageBox.critical(self, 'Cannot Sign', \
               'This transaction is not relevant to any of your wallets.' 
               'Did you load the correct transaction?', QMessageBox.Ok)
         return

      if self.txdpObj==None:
         QMessageBox.warning(self, 'Not Signable', \
               'This is not a valid transaction, and thus it cannot '
               'be signed. ', QMessageBox.Ok)
         return
      elif self.enoughSigs and self.sigsValid:
         QMessageBox.warning(self, 'Already Signed', \
               'This transaction has already been signed!', QMessageBox.Ok)
         return


      if self.wlt.watchingOnly:
         QMessageBox.warning(self, 'No Private Keys!', \
            'This transaction refers one of your wallets, but that wallet '
            'is only a watching-only wallet.  Therefore, you cannot sign '
            'this transaction.', \
             QMessageBox.Ok)
         return


      if self.wlt.useEncryption and self.wlt.isLocked:
         dlg = DlgUnlockWallet(self.wlt, self.parent, self.main, 'Sign Transaction')
         if not dlg.exec_():
            QMessageBox.warning(self, 'Wallet is Locked', \
               'Cannot sign transaction while your wallet is locked!', \
               QMessageBox.Ok)
            return

      newTxdp = self.wlt.signTxDistProposal(self.txdpObj)
      self.wlt.advanceHighestIndex()
      self.txtTxDP.setText(newTxdp.serializeAscii())
      self.txdpObj = newTxdp


   def broadTx(self):
      if not self.main.internetAvail:
         QMessageBox.warning(self, 'No Internet!', \
            'You do not currently have a connection to the Bitcoin network. '
            'If this does not seem correct, verify your internet connection '
            'and restart Armory!', QMessageBox.Ok)
         return



      try:
         finalTx = self.txdpObj.prepareFinalTx()
      except:
         QMessageBox.warning(self, 'Error', \
            'There was an error processing this transaction, for reasons '
            'that are probably not your fault...', QMessageBox.Ok)
         return

      reply = QMessageBox.warning(self, 'Confirmation', \
            'Are you sure that you want to broadcast this transaction?', \
            QMessageBox.Yes | QMessageBox.No)

      if reply==QMessageBox.Yes:
         self.main.broadcastTransaction(finalTx)
         QMessageBox.warning(self, 'Done!', 'The transaction has been broadcast!', QMessageBox.Ok)
         self.accept()



   def saveTx(self):
      if not self.fileLoaded==None and self.enoughSigs and self.sigsValid:
         reply = QMessageBox.question(self,'Overwrite?', \
         'The signed transaction you are saving was originally loaded '
         'from:\n\n%s\n\nWould you like to overwrite it with this '
         'signed transaction?' % self.fileLoaded, QMessageBox.Yes | QMessageBox.No)
         if reply==QMessageBox.Yes:
            newSaveFile = self.fileLoaded.replace('unsigned', 'signed')
            f = open(newSaveFile, 'w')
            f.write(str(self.txtTxDP.toPlainText()))
            f.close()
            if not newSaveFile==self.fileLoaded:
               os.remove(self.fileLoaded)
            QMessageBox.information(self, 'Transaction Saved!',\
               'Your transaction has been saved to the following location:'
               '\n\n%s\n\nIt can now be broadcast from any computer with '
               'a connection to the Bitcoin network.' % newSaveFile, QMessageBox.Ok)
            return
               

      defaultFilename = ''
      if not self.txdpObj==None:
         if self.enoughSigs and self.sigsValid:
            defaultFilename = 'armory_%s_.signed.tx' % self.txdpObj.uniqueB58
         else:
            defaultFilename = 'armory_%s_.unsigned.tx' % self.txdpObj.uniqueB58
      filename = self.main.getFileSave('Save Transaction', \
                             ['Transactions (*.signed.tx *.unsigned.tx)'], \
                             defaultFilename)

      if len(str(filename))>0:
         f = open(filename, 'w')
         f.write(str(self.txtTxDP.toPlainText()))
         f.close()


   def loadTx(self):
      filename = self.main.getFileLoad('Load Transaction', \
                             ['Transactions (*.signed.tx *.unsigned.tx)'])
      if len(str(filename))>0:
         f = open(filename, 'r')
         self.txtTxDP.setText(f.read())
         f.close()
         self.fileLoaded = filename


   def copyTx(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(self.txtTxDP.toPlainText()))
      self.lblCopied.setText('<i>Copied!</i>')


################################################################################
class DlgShowKeyList(QDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgShowKeyList, self).__init__(parent)

      self.parent = parent
      self.main   = main
      self.wlt    = wlt


      self.havePriv = True
      if self.wlt.useEncryption and self.wlt.isLocked:
         self.havePriv = False
         dlg = DlgUnlockWallet(wlt, parent, main, 'Unlock Private Keys')
         if dlg.exec_():
            self.havePriv = True

      # NOTE/WARNING:  We have to make copies (in RAM) of the unencrypted
      #                keys, or else we will have to type in our address
      #                every 10s if we want to modify the key list.  This
      #                isn't likely a bit problem, but it's not ideal, 
      #                either.  Not much I can do about, though...
      #                (at least:  once this dialog is closed, all the 
      #                garbage should be collected...)
      self.addrCopies = []
      for addr in self.wlt.getLinearAddrList():
         self.addrCopies.append(addr.copy())
         

      self.strDescrReg = ( \
         'Use the checkboxes on the right to control the amount of '
         'information displayed below.  The resulting data can be '
         'saved to file, or copied into another document.'
         '<br><br>'
         'The information here is for <i>all</i> keys in this wallet, '
         'including imported keys.  However, since permanent keys are '
         'generated as they are requested (via "Receive Bitcoins" button), '
         'only permanent keys that you have used before now, will be '
         'protected by backing up the list below.  If you want a permanent '
         'backup of your base wallet (excluding imported keys), then please '
         'print a regular paper backup.'
         '<br><br>')
      self.strDescrWarn = ( \
         '<font color="red">Warning:</font> The text box below contains '
         'the plaintext (unencrypted) private keys for each of '
         'the addresses in this wallet.  This information can be used '
         'to spend the money associated with those addresses, so please '
         'protect it like you protect the rest of your wallet.')

      self.lblDescr = QRichLabel('')
      self.lblDescr.setAlignment(Qt.AlignLeft |Qt.AlignTop)


      txtFont = GETFONT('Fixed', 8)
      self.txtBox = QTextEdit()
      self.txtBox.setReadOnly(True)
      self.txtBox.setFont(txtFont)
      w,h = tightSizeNChar(txtFont, 110)
      self.txtBox.setFont(txtFont)
      self.txtBox.setMinimumWidth(w)
      self.txtBox.setMaximumWidth(w)
      self.txtBox.setMinimumHeight(h*3.2)
      self.txtBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
      
      # Create a list of checkboxes and then some ID word to identify what
      # to put there
      self.chkList = {}
      self.chkList['AddrStr']   = QCheckBox('Address String')
      self.chkList['PubKeyHash']= QCheckBox('Hash160 (LE)')
      self.chkList['PrivCrypt'] = QCheckBox('Private Key (Encrypted)')
      self.chkList['PrivHexBE'] = QCheckBox('Private Key (Plain Hex, BE)')
      self.chkList['PrivHexLE'] = QCheckBox('Private Key (Plain Hex, LE)')
      self.chkList['PrivB58']   = QCheckBox('Private Key (Plain Base58)')
      self.chkList['PubKey']    = QCheckBox('Public Key (BE)')
      self.chkList['InitVect']  = QCheckBox('Initialization Vect (if encrypted)')
      self.chkList['ChainIndex']= QCheckBox('Chain Index')

      watchOnly = self.wlt.watchingOnly
      self.chkList['AddrStr'   ].setChecked(True )
      self.chkList['PubKeyHash'].setChecked(False)
      self.chkList['PrivB58'   ].setChecked(not watchOnly)
      self.chkList['PrivCrypt' ].setChecked(False)
      self.chkList['PrivHexBE' ].setChecked(not watchOnly)
      self.chkList['PrivHexLE' ].setChecked(False)
      self.chkList['PubKey'    ].setChecked(watchOnly)
      self.chkList['InitVect'  ].setChecked(False)
      self.chkList['ChainIndex'].setChecked(False)

      namelist = ['AddrStr','PubKeyHash','PrivB58','PrivCrypt', \
                  'PrivHexBE', 'PrivHexLE','PubKey','InitVect', \
                  'ChainIndex']

      for name in self.chkList.keys():
         self.connect(self.chkList[name], SIGNAL('toggled(bool)'), \
                      self.rewriteList)


      self.chkImportedOnly = QCheckBox('Imported Addresses Only')
      self.connect(self.chkImportedOnly, SIGNAL('toggled(bool)'), \
                      self.rewriteList)
      #self.chkCSV = QCheckBox('Display in CSV format')

      std = (self.main.usermode==USERMODE.Standard)
      adv = (self.main.usermode==USERMODE.Advanced)
      dev = (self.main.usermode==USERMODE.Developer)
      if std:
         self.chkList['PubKeyHash'].setVisible(False)
         self.chkList['PrivCrypt' ].setVisible(False)
         self.chkList['PrivHexLE' ].setVisible(False)
         self.chkList['InitVect'  ].setVisible(False)
         self.chkList['ChainIndex'].setVisible(False)
      elif adv:
         self.chkList['PubKeyHash'].setVisible(False)
         self.chkList['InitVect'  ].setVisible(False)
         self.chkList['ChainIndex'].setVisible(False)

      # We actually just want to remove these entirely
      # (either we need to display all data needed for decryption,
      # besides passphrase,  or we shouldn't show any of it)
      self.chkList['PrivCrypt' ].setVisible(False)
      self.chkList['InitVect'  ].setVisible(False)

      chkBoxList = [self.chkList[n] for n in namelist] 
      chkBoxList.append('Line')
      chkBoxList.append(self.chkImportedOnly)
      #chkBoxList.append(self.chkCSV)

      frmChks = makeLayoutFrame('Vert', chkBoxList, STYLE_SUNKEN)


      btnGoBack = QPushButton('<<< Go Back')
      btnSaveFile = QPushButton('Save to File...')
      btnCopyClip = QPushButton('Copy to Clipboard')
      self.lblCopied = QRichLabel('')

      self.connect(btnGoBack,   SIGNAL('clicked()'), self.accept)
      self.connect(btnSaveFile, SIGNAL('clicked()'), self.saveToFile)
      self.connect(btnCopyClip, SIGNAL('clicked()'), self.copyToClipboard)
      frmGoBack = makeLayoutFrame('Horiz', [btnGoBack, \
                                            'Stretch', \
                                            self.lblCopied, \
                                            btnCopyClip, \
                                            btnSaveFile])

      frmDescr = makeLayoutFrame('Horiz',  [self.lblDescr], STYLE_SUNKEN)

      if not self.havePriv or (self.wlt.useEncryption and self.wlt.isLocked):
         self.chkList['PrivHexBE'].setEnabled(False)
         self.chkList['PrivHexBE'].setChecked(False)
         self.chkList['PrivHexLE'].setEnabled(False)
         self.chkList['PrivHexLE'].setChecked(False)
         self.chkList['PrivB58'  ].setEnabled(False)
         self.chkList['PrivB58'  ].setChecked(False)

      dlgLayout = QGridLayout()
      dlgLayout.addWidget(frmDescr,    0,0, 1,1)
      dlgLayout.addWidget(frmChks,     0,1, 1,1)
      dlgLayout.addWidget(self.txtBox, 1,0, 1,2)
      dlgLayout.addWidget(frmGoBack,   2,0, 1,2)

      self.setLayout(dlgLayout)
      self.rewriteList()
      self.setWindowTitle('All Wallet Keys')

         

   def rewriteList(self, *args):
      # Wallet Details:
      #  Wlt Labels,
      #  Chain Code:
      #  Highest Chain index used
      #  List of Addresses
      def fmtBin(s, nB=4, sw=False):
         h = binary_to_hex(s)
         if sw: 
            h = hex_switchEndian(h)
         return ' '.join([h[i:i+nB] for i in range(0, len(h), nB)])

      L = []
      L.append('Wallet ID:    ' + self.wlt.uniqueIDB58)
      L.append('Wallet Name:  ' + self.wlt.labelName)
      if self.main.usermode==USERMODE.Developer:
         L.append('Chain Code:   ' + fmtBin(self.wlt.addrMap['ROOT'].chaincode.toBinStr()))
         L.append('Highest Used: ' + str(self.wlt.highestUsedChainIndex))
      L.append('')

      self.havePriv = False
      #c = ',' if self.chkCSV.isChecked() else '' 
      for addr in self.addrCopies:
         if self.chkImportedOnly.isChecked() and not addr.chainIndex==-2:
            continue
         extraLbl = '   (Imported)' if addr.chainIndex==-2 else ''
         if self.chkList['AddrStr'   ].isChecked():  
            L.append(                   addr.getAddrStr() + extraLbl)
         if self.chkList['PubKeyHash'].isChecked(): 
            L.append(                  '   Hash160   : ' + fmtBin(addr.getAddr160()))
         if self.chkList['PrivB58'   ].isChecked(): 
            pBin = '\x80' + addr.binPrivKey32_Plain.toBinStr()
            pChk = computeChecksum(pBin, nBytes=4)
            pB58 = binary_to_base58(pBin + pChk)
            pB58Stretch = ' '.join([pB58[i:i+6] for i in range(0, len(pB58), 6)])
            L.append(                  '   PrivBase58: ' + pB58Stretch)
            self.havePriv = True
         if self.chkList['PrivCrypt' ].isChecked():  
            L.append(                  '   PrivCrypt : ' + fmtBin(addr.binPrivKey32_Encr.toBinStr()))
         if self.chkList['PrivHexBE' ].isChecked():  
            L.append(                  '   PrivHexBE : ' + fmtBin(addr.binPrivKey32_Plain.toBinStr(), sw=True))
            self.havePriv = True
         if self.chkList['PrivHexLE' ].isChecked(): 
            L.append(                  '   PrivHexLE : ' + fmtBin(addr.binPrivKey32_Plain.toBinStr()))
            self.havePriv = True
         if self.chkList['PubKey'    ].isChecked():  
            L.append(                  '   PublicX   : ' + fmtBin(addr.binPublicKey65.toBinStr()[1:33 ]))
            L.append(                  '   PublicY   : ' + fmtBin(addr.binPublicKey65.toBinStr()[  33:]))
         if self.chkList['InitVect'  ].isChecked():  
            L.append(                  '   InitVect  : ' + fmtBin(addr.binInitVect16.toBinStr()))
         if self.chkList['ChainIndex'].isChecked(): 
            L.append(                  '   ChainIndex: ' + str(addr.chainIndex))

      self.txtBox.setText('\n'.join(L))
      if self.havePriv:
         self.lblDescr.setText(self.strDescrReg + self.strDescrWarn)
      else:
         self.lblDescr.setText(self.strDescrReg)

      
   def saveToFile(self):
      if self.havePriv:
         if not self.main.settings.getSettingOrSetDefault('DNAA_WarnPrintKeys', False):
            result = MsgBoxWithDNAA(MSGBOX.Warning, title='Plaintext Private Keys', \
                  msg='<font color="red"><b>REMEMBER:</b></font> The data you '
                  'are about to save contains private keys.  Please make sure '
                  'that only trusted persons will have access to this file.'
                  '<br><br>Are you sure you want to continue?', \
                  dnaaMsg=None, wCancel=True)
            if not result[0]:
               return
            self.main.settings.set('DNAA_WarnPrintKeys', result[1])
            
      wltID = self.wlt.uniqueIDB58
      fn = self.main.getFileSave(title='Save Key List', \
                                 ffilter=['Text Files (*.txt)'], \
                                 defaultFilename='keylist_%s_.txt'%wltID)
      if len(fn)>0:
         fileobj = open(fn,'w')
         fileobj.write(str(self.txtBox.toPlainText()))
         fileobj.close()
               


   def copyToClipboard(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(self.txtBox.toPlainText()))
      self.lblCopied.setText('<i>Copied!</i>')
               

            


################################################################################
class DlgTxFeeOptions(QDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgTxFeeOptions, self).__init__(parent)

      self.parent = parent
      self.main   = main
      lblDescr = QLabel( \
         'Transaction fees go to people who contribute processing power to '
         'the Bitcoin network to process transactions and keep it secure.') 
      lblDescr2 = QLabel( \
         'Nearly all transactions are guaranteed to be '
         'processed if a fee of 0.0005 BTC is included (less than $0.01 USD).  You '
         'will be prompted for confirmation if a higher fee amount is required for '
         'your transaction.')


################################################################################
class DlgAddressProperties(QDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgAddressProperties, self).__init__(parent)
      self.parent = parent
      self.main   = main

   


################################################################################
def extractTxInfo(pytx, rcvTime=None):

   
   pytxdp = None
   if isinstance(pytx, PyTxDistProposal):
      pytxdp = pytx
      pytx = pytxdp.pytxObj.copy()
      
   txHash = pytx.getHash()
   txOutToList, sumTxOut, txinFromList, sumTxIn, txTime, txBlk, txIdx = [None]*7

   txOutToList = []
   sumTxOut = 0
   for txout in pytx.outputs:
      txOutToList.append([])

      scrType = getTxOutScriptType(txout.binScript)
      txOutToList[-1].append(scrType)
      txOutToList[-1].append(txout.value)
      if scrType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
         txOutToList[-1].append(TxOutScriptExtractAddr160(txout.binScript))
      elif scrType in (TXOUT_SCRIPT_MULTISIG,):
         mstype, addr160s, pubs = getTxOutMultiSigInfo(txout.binScript)
         txOutToList[-1].append(addr160s)
         txOutToList[-1].append(pubs)
         txOutToList[-1].append(mstype[0]) # this is M (from M-of-N)
      elif scrType in (TXOUT_SCRIPT_OP_EVAL,):
         print 'No OP_EVAL support yet!'
         txOutToList[-1].append(txout.binScript)
      elif scrType in (TXOUT_SCRIPT_UNKNOWN,):
         print 'Unknown TxOut type'
         txOutToList[-1].append(txout.binScript)
      else:
         print 'How did we miss TXOUT_SCRIPT_UNKNOWN txout type?'
      sumTxOut += txout.value
  

   txref = None
   if TheBDM.isInitialized(): 
      txref = TheBDM.getTxByHash(txHash)
      if txref:
         headref = txref.getHeaderPtr()
         if headref:
            txTime  = unixTimeToFormatStr(headref.getTimestamp())
            txBlk   = headref.getBlockHeight()
            txIdx   = txref.getBlockTxIndex()
         else:
            if rcvTime==None:
               txTime  = 'Unknown'
            elif rcvTime==-1:
               txTime  = '[[Not broadcast yet]]'
            elif isinstance(rcvTime, str):
               txTime  = rcvTime
            else:
               txTime  = unixTimeToFormatStr(rcvTime)
            txBlk   = UINT32_MAX
            txIdx   = -1
   
   txinFromList = []
   if TheBDM.isInitialized() and not txref==None:
      # Use BDM to get all the info about the TxOut being spent
      # Recip, value, block-that-incl-tx, tx-that-incl-txout, txOut-index
      haveAllInput=True
      for i in range(txref.getNumTxIn()):
         txinFromList.append([])
         cppTxin = txref.getTxInRef(i)
         prevTxHash = cppTxin.getOutPoint().getTxHash()
         if TheBDM.getTxByHash(prevTxHash):
            prevTxOut = TheBDM.getPrevTxOut(cppTxin)
            txinFromList[-1].append(TheBDM.getSenderAddr20(cppTxin))
            txinFromList[-1].append(TheBDM.getSentValue(cppTxin))
            txinFromList[-1].append(prevTxOut.getParentTxPtr().getBlockHeight())
            txinFromList[-1].append(prevTxOut.getParentTxPtr().getThisHash())
            txinFromList[-1].append(prevTxOut.getIndex())
         else:
            haveAllInput=False
            txin = PyTxIn().unserialize(cppTxin.serialize())
            txinFromList[-1].append(TxInScriptExtractAddr160IfAvail(txin))
            txinFromList[-1].append('')
            txinFromList[-1].append('')
            txinFromList[-1].append('')
            txinFromList[-1].append('')

   elif not pytxdp==None:
      haveAllInput=True
      for i,txin in enumerate(pytxdp.pytxObj.inputs):
         txinFromList.append([])
         txinFromList[-1].append(TxOutScriptExtractAddr160(pytxdp.txOutScripts[i]))
         txinFromList[-1].append(pytxdp.inputValues[i])
         txinFromList[-1].append('')
         txinFromList[-1].append('')
         txinFromList[-1].append('')
   else:  # BDM is not initialized
      haveAllInput=False
      for i,txin in enumerate(pytx.inputs):
         txinFromList.append([])
         txinFromList[-1].append(TxInScriptExtractAddr160IfAvail(txin))
         txinFromList[-1].append('')
         txinFromList[-1].append('')
         txinFromList[-1].append('')
         txinFromList[-1].append('')
         
      

   if haveAllInput:
      sumTxIn = sum([x[1] for x in txinFromList])
   else:
      sumTxIn = None

   return [txHash, txOutToList, sumTxOut, txinFromList, sumTxIn, txTime, txBlk, txIdx]
   




#def createTxInfoFrameStd(pytx, le, wlt=None):


      
class DlgDispTxInfo(QDialog):
   def __init__(self, pytx, wlt=None, parent=None, main=None, mode=None, \
                             precomputeIdxGray=None, precomputeAmt=None, txtime=None):
      """
      This got freakin' complicated, because I'm trying to handle
      wallet/nowallet, BDM/noBDM and Std/Adv/Dev all at once. 

      We can override the user mode as an input argument, in case a std
      user decides they want to see the tx in adv/dev mode
      """
      super(DlgDispTxInfo, self).__init__(parent)
      self.parent = parent
      self.main   = main  
      self.mode   = mode


      FIELDS = enum('Hash','OutList','SumOut','InList','SumIn', 'Time', 'Blk', 'Idx')
      data = extractTxInfo(pytx, txtime)
         
      # If this is actually a TxDP in here...
      pytxdp = None
      if isinstance(pytx, PyTxDistProposal):
         pytxdp = pytx
         pytx = pytxdp.pytxObj.copy()


      self.pytx = pytx.copy()

      if self.mode==None:
         self.mode = self.main.usermode

      txHash = data[FIELDS.Hash]

      haveWallet = (wlt!=None)
      haveBDM    = TheBDM.isInitialized()

      # Should try to identify what is change and what's not
      wltLE = None
      IsNonStandard = False
      fee = None
      txAmt = data[FIELDS.SumOut]

      # Collect our own outputs only, and ID non-std tx
      rvPairSelf  = []
      rvPairOther = []
      indicesSelf = []
      indicesOther = []
      indicesMakeGray = []
      idx = 0
      for scrType, amt, recip in data[FIELDS.OutList]:
         if scrType in (TXOUT_SCRIPT_STANDARD, TXOUT_SCRIPT_COINBASE):
            if haveWallet and wlt.hasAddr(recip):
               rvPairSelf.append( [recip, amt] )
               indicesSelf.append( idx )
            else:
               rvPairOther.append( [recip, amt] )
               indicesOther.append( idx )
         else:
            IsNonStandard = True
         idx+=1

      txdir = None 
      changeIndex = None
      rvPairDisp = None
      if haveBDM and haveWallet and data[FIELDS.SumOut] and data[FIELDS.SumIn]:
         fee = data[FIELDS.SumOut] - data[FIELDS.SumIn]
         ldgr = wlt.getTxLedger()
         for le in ldgr:
            if le.getTxHash()==txHash:
               wltLE = le
               txAmt = le.getValue()

               # If we found the LE for this tx, then we can display much
               # more useful information... like ignoring change outputs,
               if le.isSentToSelf():
                  txdir = 'Sent-to-Self'
                  rvPairDisp = []
                  if len(self.pytx.outputs):
                     txAmt = fee
                     triplet = data[FIELDS.OutList][0]
                     rvPairDisp.append([triplet[2], triplet[1]])
                  else:
                     txAmt, changeIndex = self.main.determineSentToSelfAmt(le, wlt)
                     for i,triplet in enumerate(data[FIELDS.OutList]):
                        if not i==changeIndex:
                           rvPairDisp.append([triplet[2], triplet[1]])
                        else:
                           indicesMakeGray.append(i)
               else:
                  if le.getValue() > 0:
                     txdir = 'Received'
                     rvPairDisp = rvPairSelf
                     indicesMakeGray.extend(indicesOther)
                  if le.getValue() < 0:
                     txdir = 'Sent'
                     rvPairDisp = rvPairOther
                     indicesMakeGray.extend(indicesSelf)
               break


      # If this is a TxDP, the above calculation probably didn't do its job
      # It is possible, but it's also possible that this Tx has nothing to
      # do with our wallet, which is not the focus of the above loop/conditions
      # So we choose to pass in the amount we already computed based on extra
      # information available in the TxDP structure
      if precomputeAmt:
         txAmt = precomputeAmt

      if IsNonStandard:
         # TODO:  Need to do something with this non-std tx!
         print '***Non-std transaction!'
         QMessageBox.critical(self, 'Non-Standard Transaction', \
           'This is a non-standard transaction, which cannot be '
           'interpretted by this program.  DO NOT ASSUME that you '
           'own these Bitcoins, even if you see your address in '
           'any part of the transaction.  Only an expert can tell '
           'you if and how these coins can be redeemed!  \n\n'
           'If you would like more information, please copy the '
           'information on the next window into an email and send '
           'it to alan.reiner@gmail.com.', QMessageBox.Ok)
         self.mode=USERMODE.Developer



      layout = QGridLayout()
      lblDescr = QLabel('Transaction Information:') 

      layout.addWidget(lblDescr,     0,0,  1,1)
   
      frm = QFrame()
      frm.setFrameStyle(STYLE_RAISED)
      frmLayout = QGridLayout()
      lbls = []



      # Show the transaction ID, with the user's preferred endianness
      # I hate BE, but block-explorer requires it so it's probably a better default
      endianness = self.main.settings.getSettingOrSetDefault('PrefEndian', BIGENDIAN)
      estr = ''
      if self.mode in (USERMODE.Advanced, USERMODE.Developer):
         estr = ' (BE)' if endianness==BIGENDIAN else ' (LE)'
   
      lbls.append([])
      lbls[-1].append(createToolTipObject('Unique identifier for this transaction'))
      lbls[-1].append(QLabel('Transaction ID' + estr + ':'))
      

      # Want to display the hash of the Tx if we have a valid one:
      # A TxDP does not have a valid hash until it's completely signed, though
      longTxt = '[[ Transaction ID cannot be determined without all signatures ]]' 
      w,h = relaxedSizeStr(QRichLabel(''), longTxt)

      tempPyTx = self.pytx.copy()
      if pytxdp:
         finalTx = pytxdp.getBroadcastTxIfReady()
         if finalTx:
            tempPyTx = finalTx.copy()
         else:
            tempPyTx = None
            lbls[-1].append(QRichLabel( '<font color="gray">' 
               '[[ Transaction ID cannot be determined without all signatures ]]' 
               '</font>'))

      if tempPyTx:
         if endianness==BIGENDIAN:
            lbls[-1].append(QLabel( binary_to_hex(tempPyTx.getHash(), endOut=BIGENDIAN) ))
         else:
            lbls[-1].append(QLabel( binary_to_hex(tempPyTx.getHash(), endOut=LITTLEENDIAN) ))

      lbls[-1][-1].setMinimumWidth(w)

      if self.mode in (USERMODE.Developer,):
         # Add protocol version and locktime to the display
         lbls.append([])
         lbls[-1].append(createToolTipObject('Bitcoin Protocol Version Number'))
         lbls[-1].append(QLabel('Tx Version:'))
         lbls[-1].append(QLabel( str(self.pytx.version)))

         lbls.append([])
         lbls[-1].append(createToolTipObject(
            'The time at which this transaction becomes valid.'))
         lbls[-1].append(QLabel('Lock-Time:'))
         if self.pytx.lockTime==0: 
            lbls[-1].append(QLabel('Immediate (0)'))
         elif self.pytx.lockTime<500000000:
            lbls[-1].append(QLabel('Block %d' % self.pytx.lockTime))
         else:
            lbls[-1].append(QLabel(unixTimeToFormatStr(self.pytx.lockTime)))


      
      lbls.append([])
      lbls[-1].append(createToolTipObject('Comment stored for this transaction in this wallet'))
      lbls[-1].append(QLabel('User Comment:'))
      if wlt.getComment(txHash):
         lbls[-1].append(QRichLabel(wlt.getComment(txHash)))
      else:
         lbls[-1].append(QRichLabel('<font color="gray">[None]</font>'))
      

      if not data[FIELDS.Time]==None:
         lbls.append([])
         if data[FIELDS.Blk]>=2**32-1:
            lbls[-1].append(createToolTipObject( 
                  'The time that you computer first saw this transaction'))
         else:
            lbls[-1].append(createToolTipObject( 
                  'All transactions are eventually included in a "block."  The '
                  'time shown here is the time that the block entered the "blockchain."'))
         lbls[-1].append(QLabel('Transaction Time:'))
         lbls[-1].append(QLabel(data[FIELDS.Time]))

      if not data[FIELDS.Blk]==None:
         nConf = 0
         if data[FIELDS.Blk]>=2**32-1:
            lbls.append([])
            lbls[-1].append(createToolTipObject(
                  'This transaction has not yet been included in a block.  '
                  'It usually takes 5-20 minutes for a transaction to get '
                  'included in a block after the user hits the "Send" button.'))
            lbls[-1].append(QLabel('Block Number:'))
            lbls[-1].append(QRichLabel( '<i>Not in the blockchain yet</i>' ))
         else:
            idxStr = ''
            if not data[FIELDS.Idx]==None and self.mode==USERMODE.Developer:
               idxStr = '  (Tx #%d)'%data[FIELDS.Idx]
            lbls.append([])
            lbls[-1].append(createToolTipObject( 
                  'Every transaction is eventually included in a "block" which '
                  'is where the transaction is permanently recorded.  A new block '
                  'is produced approximately every 10 minutes.'))
            lbls[-1].append(QLabel('Included in Block:'))
            lbls[-1].append(QRichLabel( str(data[FIELDS.Blk]) + idxStr ))
            if TheBDM.isInitialized():
               nConf = TheBDM.getTopBlockHeader().getBlockHeight() - data[FIELDS.Blk] + 1
               lbls.append([])
               lbls[-1].append(createToolTipObject( 
                     'The number of blocks that have been produced since '
                     'this transaction entered the blockchain.  A transaciton '
                     'with 6 more confirmations is nearly impossible to reverse.'))
               lbls[-1].append(QLabel('Confirmations:'))
               lbls[-1].append(QRichLabel( str(nConf)))




      if rvPairDisp==None and precomputeAmt==None:
         # Couldn't determine recip/change outputs
         lbls.append([])
         lbls[-1].append(createToolTipObject(
               'Most transactions have at least a recipient output and a '
               'returned-change output.  You do not have enough enough information '
               'to determine which is which, and so this fields shows the sum '
               'of <b>all</b> outputs.'))
         lbls[-1].append(QLabel('Sum of Outputs:'))
         lbls[-1].append(QLabel( coin2str(txAmt, maxZeros=1).strip() + '  BTC' ))
      else:
         lbls.append([])
         lbls[-1].append(createToolTipObject(
               'Bitcoins were either sent or received, or sent-to-self'))
         lbls[-1].append(QLabel('Transaction Direction:'))
         lbls[-1].append(QRichLabel( txdir ))

         lbls.append([])
         lbls[-1].append(createToolTipObject(
               'The value shown here is the net effect on your '
               'wallet, including transaction fee.'))
         lbls[-1].append(QLabel('Transaction Amount:'))
         lbls[-1].append(QRichLabel( coin2str(txAmt, maxZeros=1).strip()  + '  BTC'))
         if txAmt<0:
            lbls[-1][-1].setText('<font color="red">'+lbls[-1][-1].text()+'</font> ')
         elif txAmt>0:
            lbls[-1][-1].setText('<font color="green">'+lbls[-1][-1].text()+'</font> ')
                     
      
      if not data[FIELDS.SumIn]==None:
         fee = data[FIELDS.SumIn]-data[FIELDS.SumOut]
         lbls.append([])
         lbls[-1].append(createToolTipObject( 
            'Transaction fees go to users supplying the Bitcoin network with '
            'computing power for processing transactions and maintaining security.'))
         lbls[-1].append(QLabel('Tx Fee Paid:'))
         lbls[-1].append(QLabel( coin2str(fee, maxZeros=0).strip() + '  BTC'))





      lastRow = 0
      for row,lbl3 in enumerate(lbls):
         lastRow = row
         for i in range(3):
            lbl3[i].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            lbl3[i].setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                            Qt.TextSelectableByKeyboard)
         frmLayout.addWidget(lbl3[0], row, 0,  1,1)
         frmLayout.addWidget(lbl3[1], row, 1,  1,1)
         frmLayout.addWidget(lbl3[2], row, 3,  1,2)

      spacer = QSpacerItem(20,20)
      frmLayout.addItem(spacer,  0, 2, len(lbls), 1)

      # Show the list of recipients, if possible
      numShow = 3
      rlbls = []
      if not rvPairDisp==None:
         numRV = len(rvPairDisp)
         for i,rv in enumerate(rvPairDisp):
            rlbls.append([])
            if i==0:
               rlbls[-1].append(createToolTipObject( 
                  'All outputs of the transaction <b>excluding</b> change-'
                  'back-to-sender outputs.  If this list does not look '
                  'correct, it is possible that the change-output was '
                  'detected incorrectly -- please check the complete '
                  'input/output list below.'))
               rlbls[-1].append(QLabel('Recipients:'))
            else:
               rlbls[-1].extend([QLabel(), QLabel()])
            rlbls[-1].append(QLabel(hash160_to_addrStr(rv[0])))
            if numRV>1:
               rlbls[-1].append(QLabel(coin2str(rv[1], maxZeros=1) + '  BTC'))
            else:
               rlbls[-1].append(QLabel(''))
            ffixBold = GETFONT('Fixed', 10)
            ffixBold.setWeight(QFont.Bold)
            rlbls[-1][-1].setFont(ffixBold)
               
            if numRV>numShow and i==numShow-2:
               moreStr = '[%d more recipients]' % (numRV-numShow+1)
               rlbls.append([])
               rlbls[-1].extend([QLabel(), QLabel(), QLabel(moreStr), QLabel()])
               break
            

         ###
         for i,lbl4 in enumerate(rlbls):
            for j in range(4):
               lbl4[j].setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                            Qt.TextSelectableByKeyboard)
            row = lastRow + 1 + i
            frmLayout.addWidget(lbl4[0], row, 0,  1,1)
            frmLayout.addWidget(lbl4[1], row, 1,  1,1)
            frmLayout.addWidget(lbl4[2], row, 3,  1,1)
            frmLayout.addWidget(lbl4[3], row, 4,  1,1)
         


      # TxIns/Senders
      wWlt = relaxedSizeStr(GETFONT('Var'), 'A'*10)[0]
      wAddr = relaxedSizeStr(GETFONT('Var'), 'A'*31)[0]
      wAmt = relaxedSizeStr(GETFONT('Fixed'), 'A'*20)[0]
      if pytxdp:
         self.txInModel = TxInDispModel(pytxdp, data[FIELDS.InList], self.main)
      else:
         self.txInModel = TxInDispModel(pytx, data[FIELDS.InList], self.main)
      self.txInView = QTableView()
      self.txInView.setModel(self.txInModel)
      self.txInView.setSelectionBehavior(QTableView.SelectRows)
      self.txInView.setSelectionMode(QTableView.SingleSelection)
      self.txInView.horizontalHeader().setStretchLastSection(True)
      self.txInView.verticalHeader().setDefaultSectionSize(20)
      self.txInView.verticalHeader().hide()
      w,h = tightSizeNChar(self.txInView, 1)
      self.txInView.setMinimumHeight(2*(1.4*h))
      self.txInView.setMaximumHeight(5*(1.4*h))
      self.txInView.hideColumn(TXINCOLS.OutPt) 
      self.txInView.hideColumn(TXINCOLS.OutIdx) 
      self.txInView.hideColumn(TXINCOLS.Script) 
      if haveBDM:
         if self.mode==USERMODE.Standard:
            initialColResize(self.txInView, [wWlt, wAddr, wAmt, 0, 0, 0, 0, 0, 0])
            self.txInView.hideColumn(TXINCOLS.FromBlk) 
            self.txInView.hideColumn(TXINCOLS.ScrType) 
            self.txInView.hideColumn(TXINCOLS.Sequence) 
            #self.txInView.setSelectionMode(QTableView.NoSelection)
         elif self.mode==USERMODE.Advanced:
            initialColResize(self.txInView, [0.8*wWlt, 0.6*wAddr, wAmt, 0, 0, 0, 0.2, 0, 0])
            self.txInView.hideColumn(TXINCOLS.FromBlk) 
            self.txInView.hideColumn(TXINCOLS.Sequence) 
            #self.txInView.setSelectionMode(QTableView.NoSelection)
         elif self.mode==USERMODE.Developer:
            self.txInView.resizeColumnsToContents()
            
      self.txInView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.txInView.customContextMenuRequested.connect(self.showContextMenuTxIn)

      # List of TxOuts/Recipients
      if not precomputeIdxGray==None:
         indicesMakeGray = precomputeIdxGray[:]
      self.txOutModel = TxOutDispModel(self.pytx,  self.main, idxGray=indicesMakeGray)
      self.txOutView  = QTableView()
      self.txOutView.setModel(self.txOutModel)
      self.txOutView.setSelectionBehavior(QTableView.SelectRows)
      self.txOutView.setSelectionMode(QTableView.SingleSelection)
      self.txOutView.verticalHeader().setDefaultSectionSize(20)
      self.txOutView.verticalHeader().hide()
      self.txOutView.setMinimumHeight(2*(1.3*h))
      self.txOutView.setMaximumHeight(5*(1.3*h))
      initialColResize(self.txOutView, [wWlt, 0.8*wAddr, wAmt, 0.25, 0])
      self.txOutView.hideColumn(TXOUTCOLS.Script) 
      if self.mode==USERMODE.Standard:
         self.txOutView.hideColumn(TXOUTCOLS.ScrType) 
         initialColResize(self.txOutView, [wWlt, wAddr, 0.25, 0, 0])
         self.txOutView.horizontalHeader().setStretchLastSection(True)
         #self.txOutView.setSelectionMode(QTableView.NoSelection)
      elif self.mode==USERMODE.Advanced:
         initialColResize(self.txOutView, [0.8*wWlt, 0.6*wAddr, wAmt, 0.25, 0])
         #self.txOutView.setSelectionMode(QTableView.NoSelection)
      elif self.mode==USERMODE.Developer:
         initialColResize(self.txOutView, [wWlt, wAddr, wAmt, 0.25, 0])
      #self.txOutView.resizeColumnsToContents()

      self.txOutView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.txOutView.customContextMenuRequested.connect(self.showContextMenuTxOut)

      self.lblTxioInfo = QRichLabel('')
      self.lblTxioInfo.setMinimumWidth( tightSizeNChar(self.lblTxioInfo, 30)[0])
      self.connect(self.txInView, SIGNAL('clicked(QModelIndex)'), \
                   lambda: self.dispTxioInfo('In'))
      self.connect(self.txOutView, SIGNAL('clicked(QModelIndex)'), \
                   lambda: self.dispTxioInfo('Out'))
      
      #scrFrm = QFrame()
      #scrFrm.setFrameStyle(STYLE_SUNKEN)
      #scrFrmLayout = Q
      

      self.scriptArea = QScrollArea()
      self.scriptArea.setWidget(self.lblTxioInfo)
      self.scriptFrm = makeLayoutFrame('Horiz', [self.scriptArea])
      #self.scriptFrm.setMaximumWidth(150)
      self.scriptArea.setMaximumWidth(200)

      self.frmIOList = QFrame()
      self.frmIOList.setFrameStyle(STYLE_SUNKEN)
      frmIOListLayout = QGridLayout()

      lblInputs = QLabel('Transaction Inputs (Sending addresses):')
      ttipText = ('All transactions require previous transaction outputs as '
                  'inputs.  ')
      if not haveBDM:
         ttipText += ('<b>Since the blockchain is not available, not all input '
                      'information is available</b>.  You need to view this '
                      'transaction on a system with an internet connection '
                      '(and blockchain) if you want to see the complete information.')
      else:
         ttipText+=  ('Each input is like an $X bill.  Usually there are more inputs '
                      'than necessary for the transaction, and there will be an extra '
                      'output returning change to the sender')
      ttipInputs = createToolTipObject(ttipText)

      lblOutputs = QLabel('Transaction Outputs (Receiving addresses):')
      ttipOutputs = createToolTipObject(
                  'Shows <b>all</b> outputs, including other recipients '
                  'of the same transaction, and change-back-to-sender outputs '
                  '(change outputs are displayed in light gray).')
         


      inStrip  = makeLayoutFrame('Horiz', [lblInputs,  ttipInputs,  'Stretch'])
      outStrip = makeLayoutFrame('Horiz', [lblOutputs, ttipOutputs, 'Stretch'])
      
      frmIOListLayout.addWidget(inStrip,          0,0, 1,1)
      frmIOListLayout.addWidget(self.txInView,    1,0, 1,1)
      frmIOListLayout.addWidget(outStrip,         2,0, 1,1)
      frmIOListLayout.addWidget(self.txOutView,   3,0, 1,1)
      #frmIOListLayout.addWidget(self.lblTxioInfo, 0,1, 4,1)
      self.frmIOList.setLayout(frmIOListLayout)

         
      self.btnIOList = QPushButton('')
      self.btnCopy   = QPushButton('Copy Raw Tx')
      self.lblCopied = QRichLabel('')
      self.btnOk     = QPushButton('Ok')
      self.btnIOList.setCheckable(True)
      self.connect(self.btnIOList, SIGNAL('clicked()'), self.extraInfoClicked)
      self.connect(self.btnOk,     SIGNAL('clicked()'), self.accept)
      self.connect(self.btnCopy,   SIGNAL('clicked()'), self.copyRawTx)

      btnStrip = makeLayoutFrame('Horiz', [self.btnIOList, self.btnCopy, self.lblCopied, 'Stretch', self.btnOk])
      if not self.mode==USERMODE.Developer:
         self.btnCopy.setVisible(False)
      

      if self.mode==USERMODE.Standard:
         self.btnIOList.setChecked(False)
      else:
         self.btnIOList.setChecked(True)
      self.extraInfoClicked()

      
      frm.setLayout(frmLayout)
      layout.addWidget(frm,               2,0, 1,1) 
      layout.addWidget(self.scriptArea,   2,1, 1,1)
      layout.addWidget(self.frmIOList,    3,0, 1,2)
      layout.addWidget(btnStrip,          4,0, 1,2)

      #bbox = QDialogButtonBox(QDialogButtonBox.Ok)
      #self.connect(bbox, SIGNAL('accepted()'), self.accept)
      #layout.addWidget(bbox, 6,0, 1,1)

      self.setLayout(layout)
      self.layout().setSizeConstraint(QLayout.SetFixedSize)
      self.setWindowTitle('Transaction Info')



   def extraInfoClicked(self):
      if self.btnIOList.isChecked():
         self.frmIOList.setVisible(True)
         self.btnCopy.setVisible(True)
         self.lblCopied.setVisible(True)
         self.scriptArea.setVisible(self.mode==USERMODE.Developer)
         self.btnIOList.setText('<<< Less Info')
      else:
         self.frmIOList.setVisible(False)
         self.scriptArea.setVisible(False)
         self.btnCopy.setVisible(False)
         self.lblCopied.setVisible(False)
         self.btnIOList.setText('Advanced >>>') 

   def dispTxioInfo(self, InOrOut):
      hexScript = None
      headStr = None
      if InOrOut=='In':
         selection = self.txInView.selectedIndexes()
         if len(selection)==0:
            return
         row = selection[0].row()
         hexScript = str(self.txInView.model().index(row, TXINCOLS.Script).data().toString())
         headStr = 'TxIn Script:'
      elif InOrOut=='Out':
         selection = self.txOutView.selectedIndexes()
         if len(selection)==0:
            return
         row = selection[0].row()
         hexScript = str(self.txOutView.model().index(row, TXOUTCOLS.Script).data().toString())
         headStr = 'TxOut Script:'


      if hexScript:
         oplist = convertScriptToOpStrings(hex_to_binary(hexScript))
         opprint = []
         for op in oplist:
            if len(op)==40 and not '[' in op:
               opprint.append(op + ' <font color="gray">(%s)</font>' % hash160_to_addrStr(hex_to_binary(op)))
            elif len(op)==130 and not '[' in op:
               opprint.append(op + ' <font color="gray">(%s)</font>' % hash160_to_addrStr(hash160(hex_to_binary(op))))
            else:
               opprint.append(op)
         lblScript = QRichLabel('')
         lblScript.setText('<b>Script:</b><br><br>' + '<br>'.join(opprint))
         lblScript.setWordWrap(False)
         lblScript.setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                        Qt.TextSelectableByKeyboard)

         self.scriptArea.setWidget( makeLayoutFrame('Vert', [lblScript]))
         self.scriptArea.setMaximumWidth(200)
         
   def copyRawTx(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(binary_to_hex(self.pytx.serialize()))
      self.lblCopied.setText('<i>Copied to Clipboard!</i>')
      
   #############################################################################
   def showContextMenuTxIn(self, pos):
      menu = QMenu(self.txInView)
      std = (self.main.usermode==USERMODE.Standard)
      adv = (self.main.usermode==USERMODE.Advanced)
      dev = (self.main.usermode==USERMODE.Developer)
      
      if True:   actCopyWltID  = menu.addAction("Copy Wallet ID")
      if True:   actCopySender = menu.addAction("Copy Sender Address")
      if True:   actCopyAmount = menu.addAction("Copy Amount")
      if dev:    actCopyOutPt  = menu.addAction("Copy Outpoint")
      if dev:    actCopyScript = menu.addAction("Copy Raw Script")
      idx = self.txInView.selectedIndexes()[0]
      action = menu.exec_(QCursor.pos())

      if action==actCopyWltID:
         s = str(self.txInView.model().index(idx.row(), TXINCOLS.WltID).data().toString())
      elif action==actCopySender:
         s = str(self.txInView.model().index(idx.row(), TXINCOLS.Sender).data().toString())
      elif action==actCopyAmount:
         s = str(self.txInView.model().index(idx.row(), TXINCOLS.Btc).data().toString())
      elif dev and action==actCopyOutPt:
         s1 = str(self.txInView.model().index(idx.row(), TXINCOLS.OutPt).data().toString())
         s2 = str(self.txInView.model().index(idx.row(), TXINCOLS.OutIdx).data().toString())
         s = s1 + ':' + s2
      elif dev and action==actCopyScript:
         s = str(self.txInView.model().index(idx.row(), TXINCOLS.Script).data().toString())
      else:
         return

      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(s.strip())
      
   #############################################################################
   def showContextMenuTxOut(self, pos):
      menu = QMenu(self.txOutView)
      std = (self.main.usermode==USERMODE.Standard)
      adv = (self.main.usermode==USERMODE.Advanced)
      dev = (self.main.usermode==USERMODE.Developer)
      
      if True:   actCopySender = menu.addAction("Copy Recipient Address")
      if True:   actCopyWltID  = menu.addAction("Copy Wallet ID")
      if True:   actCopyAmount = menu.addAction("Copy Amount")
      if dev:    actCopyScript = menu.addAction("Copy Raw Script")
      idx = self.txOutView.selectedIndexes()[0]
      action = menu.exec_(QCursor.pos())
         
      if action==actCopyWltID:
         s = self.txOutView.model().index(idx.row(), TXOUTCOLS.WltID).data().toString()
      elif action==actCopySender:
         s = self.txOutView.model().index(idx.row(), TXOUTCOLS.Recip).data().toString()
      elif action==actCopyAmount:
         s = self.txOutView.model().index(idx.row(), TXOUTCOLS.Btc).data().toString()
      elif dev and action==actCopyScript:
         s = self.txOutView.model().index(idx.row(), TXOUTCOLS.Script).data().toString()
      else:
         return

      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(s).strip())


class DlgPaperBackup(QDialog):
   """
   Open up a "Make Paper Backup" dialog, so the user can print out a hard
   copy of whatever data they need to recover their wallet should they lose
   it.  

   TODO:  Currently only does chain-coded keys.  Support for printing imported
          keys as well, well be added later.

   I have to forego using SecureBinaryData objects for most of these methods
   (in order to manipulate the private keys for printing), but I don't think
   this is a big deal, because printing would be infrequent
   """
   def __init__(self, wlt, parent=None, main=None):
      super(DlgPaperBackup, self).__init__(parent)

      self.parent = parent
      self.main   = main

      FontFix = GETFONT('Courier',9)
      FontVar = GETFONT('Times',10)
      

      self.binPriv  = wlt.addrMap['ROOT'].binPrivKey32_Plain.copy()
      self.binChain = wlt.addrMap['ROOT'].chaincode.copy()
      if wlt.useEncryption and wlt.isLocked:
         dlg = DlgUnlockWallet(wlt, parent, main, 'Create Paper Backup')
         if dlg.exec_():
            self.binPriv  = wlt.addrMap['ROOT'].binPrivKey32_Plain.copy()
         else:
            # If we canceled out of unlocking, we can't print...
            self.reject()
            

                
      self.view = GfxViewPaper()
      self.scene = QGraphicsScene(self)
      self.scene.setSceneRect(0,0, PAPER_A4_WIDTH, PAPER_A4_HEIGHT)
      self.view.setScene(self.scene)


      sizeQR = 100
      INCH = 72
      paperMargin = 0.8*INCH
      
      leftEdge = 0.5*INCH
      topEdge  = 0.5*INCH


      GlobalPos = QPointF(leftEdge, topEdge)
      # I guess I still don't understand the copy/ref stuff... this didn't work
      #def movePosRight(g, x):    
         #g += QPointF(x,0)
      #def movePosDown(g, y):    
         #g += QPointF(0,y)
      #def setPosFromLeft(g, x):    
         #g = QPointF(x, g.y())
      #def setPosFromTop(g, y):    
         #g = QPointF(g.x(), y)
      #def moveNewLine(g, pixelsDown):
         #g = QPointF(leftEdge, g.y()+pixelsDown)

      # Draw the logo in the top-left
      logoPixmap = QPixmap('img/armory_logo_h36.png') 
      logo = QGraphicsPixmapItem( logoPixmap )
      logo.setPos( GlobalPos )
      logo.setMatrix( QMatrix() )
      self.scene.addItem(logo)
      logoRect = logo.boundingRect()
      #moveNewLine(GlobalPos, int(logoRect.height()*1.3 + 0.5))
      GlobalPos = QPointF(leftEdge, GlobalPos.y()+int(logoRect.height()*1.3 + 0.5))

      def addInfoLine(field, val, pos):
         txt = GfxItemText(field, pos, self.scene, FontVar)
         self.scene.addItem( txt )
         pos = QPointF(pos.x()+relaxedSizeStr(FontFix, 'W'*15)[0], pos.y())
   
         txt = GfxItemText(val, pos, self.scene, FontVar)
         self.scene.addItem( txt )
         pos = QPointF(leftEdge, pos.y() + 20)
         return pos
         
      
      txt = GfxItemText('Paper Backup for Armory Wallet', GlobalPos, self.scene, GETFONT('Times', 14))
      self.scene.addItem( txt )
      #moveNewLine(GlobalPos, 30)
      GlobalPos = QPointF(leftEdge, GlobalPos.y() + 1.3*txt.boundingRect().height())

      GlobalPos = addInfoLine('Wallet Name:', wlt.labelName, GlobalPos)
      GlobalPos = addInfoLine('Wallet Unique ID:', wlt.uniqueIDB58, GlobalPos)
      GlobalPos = addInfoLine('Wallet Version:', getVersionString(wlt.version), GlobalPos)


      #moveNewLine(GlobalPos, 20)
      GlobalPos = QPointF(leftEdge, GlobalPos.y()+50)
      warnMsg = ('WARNING: This page displays unprotected private-key data needed '
                 'to reconstruct your wallet and spend your funds.  Please keep '
                 'this page in a safe place where only trusted persons can access it.')

      wrapWidth = 0.9*(PAPER_A4_WIDTH - 2*paperMargin)
      txt = GfxItemText(warnMsg, GlobalPos, self.scene, FontVar, lineWidth=wrapWidth)
      self.scene.addItem(txt)

      GlobalPos = QPointF(leftEdge, GlobalPos.y()+75)
      

      # Start drawing the actual wallet data
      # The checksums are really more to determine if an error was made,
      # as opposed to correcting the errors.  It will attempt to correct
      # the errors, but there's a high (relatively speaking) chance that
      # it will do so incorrectly.  In such a case, the user can just 
      # re-enter all the data (it's annoying, but should be infrequent)
      self.binPriv0     = self.binPriv.toBinStr()[:16]
      self.binPriv1     = self.binPriv.toBinStr()[16:]
      self.binChain0    = self.binChain.toBinStr()[:16]
      self.binChain1    = self.binChain.toBinStr()[16:]
      self.binPriv0Chk  = computeChecksum(self.binPriv0, nBytes=2)
      self.binPriv1Chk  = computeChecksum(self.binPriv1, nBytes=2)
      self.binChain0Chk = computeChecksum(self.binChain0, nBytes=2)
      self.binChain1Chk = computeChecksum(self.binChain1, nBytes=2)

      rawTxt = []
      for data,chk in [(self.binPriv0, self.binPriv0Chk), \
                       (self.binPriv1, self.binPriv1Chk), \
                       (self.binChain0, self.binChain0Chk), \
                       (self.binChain1, self.binChain1Chk)]:
         rawTxt.append([])
         data16 = binary_to_easyType16(data)
         chk16  = binary_to_easyType16(chk)
         for c in range(0,32,4):
            rawTxt[-1].append( data16[c:c+4] )
         rawTxt[-1].append( chk16 )
      
      
      # We use specific fonts here, for consistency of printing
      quadWidth,quadHeight = relaxedSizeStr(FontFix, 'abcd ')
      quadWidth+=8  # for some reason, even the relaxed size is too small...

      rootPrefix  = GfxItemText('Root Key:',   GlobalPos, self.scene, GETFONT('Times', 12))
      chainPrefix = GfxItemText('Chain Code:', GlobalPos, self.scene, GETFONT('Times', 12))
      rowPrefixSz = max( rootPrefix.boundingRect().width(), \
                         chainPrefix.boundingRect().width()) + 0.2*INCH
      
      topOfRow0 = GlobalPos.y()
      topOfRow2 = GlobalPos.y() + 2*quadHeight

      for r,row in enumerate(rawTxt):
         #moveNewLine(GlobalPos, quadHeight)
         GlobalPos = QPointF(leftEdge, GlobalPos.y()+quadHeight)
         if r==0: 
            rootPrefix.setPos(GlobalPos)
            self.scene.addItem(rootPrefix)
         elif r==2:
            chainPrefix.setPos(GlobalPos)
            self.scene.addItem(chainPrefix)

         #movePosRight(GlobalPos, rowPrefixSz)
         GlobalPos = QPointF(GlobalPos.x()+rowPrefixSz, GlobalPos.y())
         for c,strQuad in enumerate(row):
            obj = GfxItemText(strQuad, GlobalPos, self.scene, FontFix)
            self.scene.addItem(obj)
            #movePosRight(GlobalPos, quadWidth)
            GlobalPos = QPointF(GlobalPos.x()+quadWidth, GlobalPos.y())
         
         

      SIZE = 170
      qrRightSide = PAPER_A4_WIDTH - paperMargin
      qrLeftEdge  = qrRightSide - SIZE - 25
      qrTopStart  = topEdge + 0.5*paperMargin  # a little more margin
      qrPos = QPointF(qrLeftEdge, qrTopStart)
      data = '\n'.join([' '.join(row) for row in rawTxt])
      objQR = GfxItemQRCode( qrPos, self.scene, data, SIZE)
      self.scene.addItem( objQR )


      btnPrint = QPushButton('&Print...')
      self.connect(btnPrint, SIGNAL('clicked()'), self.print_)

      bbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                              QDialogButtonBox.Cancel)
      self.connect(bbox, SIGNAL('accepted()'), self.accept)
      self.connect(bbox, SIGNAL('rejected()'), self.reject)


      layout = QGridLayout()
      layout.addWidget(self.view, 0,0, 3,4)
      layout.addWidget(btnPrint,  3,0, 1,1)
      layout.addWidget(bbox,      3,2, 1,2)

      self.setLayout(layout)

      self.setWindowIcon(QIcon('img/printer_icon.png'))
      self.setWindowTitle('Print Wallet Backup')
      
       
   def print_(self):
      self.printer = QPrinter(QPrinter.HighResolution)
      self.printer.setPageSize(QPrinter.Letter)
      dialog = QPrintDialog(self.printer)
      if dialog.exec_():
          painter = QPainter(self.printer)
          painter.setRenderHint(QPainter.TextAntialiasing)
          self.scene.render(painter)



class DlgBadConnection(QDialog):
   def __init__(self, haveInternet, haveSatoshi, parent=None, main=None):
      super(DlgBadConnection, self).__init__(parent)

      self.parent = parent
      self.main   = main

      layout = QGridLayout()
      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap('img/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

      lblDescr = QLabel()
      if not haveInternet:
         lblDescr = QRichLabel( \
            'Armory was not able to detect an internet connection, so Armory '
            'will operate in "Offline" mode.  In this mode, only wallet'
            '-management and unsigned-transaction functionality will be available. '
            '<br><br>'
            'If this is an error, please check your internet connection and '
            'restart Armory.<br><br>Would you like to continue in "Offline" mode? ')
      elif haveInternet and not haveSatoshi:
         lblDescr = QRichLabel( \
            'Armory was not able to detect the presence of the Satoshi Bitcoin '
            'client (available at http://www.bitcoin.org).  Please make sure that '
            'the Satoshi client is... <br><br><b>(1)</b> ...open and connected to the network '
            '<br><b>(2)</b> ...on the same network as Armory (main-network or test-network)'
            '<br><b>(3)</b> ...synchronized with the blockchain before '
            'starting Armory<br><br>Without the Satoshi client open, you will only '
            'be able to run Armory in "Offline" mode, which will not have access '
            'to new blockchain data, and you will not be able to send outgoing '
            'transactions<br><br>If you do not want to be in "Offline" mode, please '
            'restart Armory after the Satoshi client is open and synchronized with '
            'the network')
      else:
         # Nothing to do -- we shouldn't have even gotten here
         return
         
      
      self.main.abortLoad = False
      def abortLoad():
         self.main.abortLoad = True
         self.reject()
         
      lblDescr.setMinimumWidth(500)
      self.btnAccept = QPushButton("Continue in Offline Mode")
      self.btnCancel = QPushButton("Close Armory")
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.accept)
      self.connect(self.btnCancel, SIGNAL('clicked()'), abortLoad)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      layout.addWidget(lblWarnImg,         0,1, 2,1)
      layout.addWidget(lblDescr,           0,2, 1,1)
      layout.addWidget(buttonBox,          1,2, 1,1)

      self.setLayout(layout)
      self.setWindowTitle('Network not available')


################################################################################
def readSigBlock(parent, fullPacket):
   addrB58, messageStr, pubkey, sig = '','','',''
   lines = fullPacket.split('\n')
   readingMessage, readingPub, readingSig = False, False, False
   for i in range(len(lines)):
      s = lines[i].strip()

      # ADDRESS
      if s.startswith('Addr'):
         addrB58 = s.split(':')[-1].strip()

      # MESSAGE STRING
      if s.startswith('Message') or readingMessage:
         readingMessage = True
         if s.startswith('Pub') or s.startswith('Sig') or ('END-CHAL' in s):
            readingMessage = False
         else:
            # Message string needs to be exact, grab what's between the 
            # double quotes, no newlines
            iq1 = s.index('"') + 1
            iq2 = s.index('"', iq1)
            messageStr += s[iq1:iq2]

      # PUBLIC KEY
      if s.startswith('Pub') or readingPub: 
         readingPub = True
         if s.startswith('Sig') or ('END-SIGNATURE-BLOCK' in s):
            readingPub = False
         else:
            pubkey += s.split(':')[-1].strip().replace(' ','')

      # SIGNATURE
      if s.startswith('Sig') or readingSig: 
         readingSig = True
         if 'END-SIGNATURE-BLOCK' in s:
            readingSig = False
         else:
            sig += s.split(':')[-1].strip().replace(' ','')
      
    
   if len(pubkey)>0:
      try:
         pubkey = hex_to_binary(pubkey)
         if len(pubkey) not in (32, 33, 64, 65):  raise
      except:
         QMessageBox.critical(parent, 'Bad Public Key', \
            'Public key data was not recognized', QMessageBox.Ok)
         pubkey = '' 

   if len(sig)>0:
      try:
         sig = hex_to_binary(sig)
      except:
         QMessageBox.critical(parent, 'Bad Signature', \
            'Signature data is malformed!', QMessageBox.Ok)
         sig = ''

   
   pubkeyhash = hash160(pubkey)
   if not pubkeyhash==addrStr_to_hash160(addrB58):
      QMessageBox.critical(parent, 'Address Mismatch', \
         '!!! The address included in the signature block does not '
         'match the supplied public key!  This should never happen, '
         'and may in fact be an attempt to mislead you !!!', QMessageBox.Ok)
      sig = ''
      
      

   return addrB58, messageStr, pubkey, sig


################################################################################
def makeSigBlock(addrB58, MessageStr, binPubkey='', binSig=''):
   lineWid = 50
   s =  '-----BEGIN-SIGNATURE-BLOCK'.ljust(lineWid+13,'-') + '\n'

   ### Address ###
   s += 'Address:    %s\n' % addrB58

   ### Message ###
   chPerLine = lineWid-2
   nMessageLines = (len(MessageStr)-1)/chPerLine + 1
   for i in range(nMessageLines):
      cLine = 'Message:    "%s"\n' if i==0 else '            "%s"\n'
      s += cLine % MessageStr[i*chPerLine:(i+1)*chPerLine]

   ### Public Key ###
   if len(binPubkey)>0:
      hexPub = binary_to_hex(binPubkey)
      nPubLines = (len(hexPub)-1)/lineWid + 1
      for i in range(nPubLines):
         pLine = 'PublicKey:  %s\n' if i==0 else '            %s\n'
         s += pLine % hexPub[i*lineWid:(i+1)*lineWid]
         
   ### Signature ###
   if len(binSig)>0:
      hexSig = binary_to_hex(binSig)
      nSigLines = (len(hexSig)-1)/lineWid + 1
      for i in range(nSigLines):
         sLine = 'Signature:  %s\n' if i==0 else '            %s\n'
         s += sLine % hexSig[i*lineWid:(i+1)*lineWid]
         
   s += '-----END-SIGNATURE-BLOCK'.ljust(lineWid+13,'-') + '\n'
   return s



################################################################################
class DlgECDSACalc(QDialog):
   def __init__(self, parent=None, main=None, tabStart=0):
      super(DlgECDSACalc, self).__init__(parent)
      self.parent = parent
      self.main   = main

      dispFont = GETFONT('Var', 8) 
      w,h = tightSizeNChar(dispFont, 40)
      
      self.tabWidget = QTabWidget()
   
      ##########################################################################
      ##########################################################################
      # TAB:  Key/ECDSA Calcs
      ##########################################################################
      ##########################################################################
      tabKeys   = QWidget()
      self.lblPrivType = QRichLabel('', vAlign=Qt.AlignTop)
      self.txtPriv = QLineEdit()
      self.txtPrvR = QLineEdit()
      self.txtPubF = QLineEdit()
      self.txtPubX = QLineEdit()
      self.txtPubY = QLineEdit()
      self.txtHash = QLineEdit()
      self.txtAddr = QLineEdit()
      
      self.keyTxtIndex = enum('PRIV','PRVR',"PUBF","PUBX","PUBY","HASH","ADDR")
      self.keyTxtList = [self.txtPriv, self.txtPrvR, self.txtPubF, self.txtPubX, \
                         self.txtPubY, self.txtHash, self.txtAddr]
      
   
      self.returnPressedFirst = False

      for i,txt in enumerate(self.keyTxtList):
         w,h = tightSizeNChar(dispFont, 70)
         txt.setMinimumWidth(w)
         txt.setMinimumHeight(1.2*h)
         txt.sizeHint = lambda: QSize(400, 1.2*h)
         txt.setFont(dispFont)
         self.connect(txt, SIGNAL('returnPressed()'), self.keyWaterfall)


      self.connect(self.txtPriv, SIGNAL('textEdited(QString)'), \
                              lambda: self.keyTextEdited(self.keyTxtIndex.PRIV))
      self.connect(self.txtPrvR, SIGNAL('textEdited(QString)'), \
                              lambda: self.keyTextEdited(self.keyTxtIndex.PRVR))
      self.connect(self.txtPubF, SIGNAL('textEdited(QString)'), \
                              lambda: self.keyTextEdited(self.keyTxtIndex.PUBF))
      self.connect(self.txtPubX, SIGNAL('textEdited(QString)'), \
                              lambda: self.keyTextEdited([self.keyTxtIndex.PUBX, \
                                                          self.keyTxtIndex.PUBY]))
      self.connect(self.txtPubY, SIGNAL('textEdited(QString)'), \
                              lambda: self.keyTextEdited([self.keyTxtIndex.PUBX, \
                                                          self.keyTxtIndex.PUBY]))
      self.connect(self.txtHash, SIGNAL('textEdited(QString)'), \
                              lambda: self.keyTextEdited(self.keyTxtIndex.HASH))
      self.connect(self.txtAddr, SIGNAL('textEdited(QString)'), \
                              lambda: self.keyTextEdited(self.keyTxtIndex.ADDR))

      
      self.txtMsg = QTextEdit()
      self.txtSig = QTextEdit()
      for txt in (self.txtMsg, self.txtSig):
         txt.setMinimumWidth(int(2*w/3))
         txt.setMinimumHeight(2.2*h)
         txt.sizeHint = lambda: QSize(400, 2.2*h)

      self.connect(self.txtMsg, SIGNAL('textChanged()'), self.msgTextChanged)
      self.connect(self.txtSig, SIGNAL('textChanged()'), self.msgTextChanged)
                       

      btnSwitchEnd = QPushButton('Switch Endian')
      self.connect(btnSwitchEnd, SIGNAL('clicked()'), self.privSwitch)


      ttipPrvR = createToolTipObject( \
         'Any standard encoding of a private key:  raw hex, base58, with or '
         'without checksums, and mini-private-key format. '
         'This includes VanityGen addresses and Casascius physical Bitcoin '
         'private keys.')
      ttipPriv = createToolTipObject( \
         'The raw hexadecimal private key.  This is exactly 32 bytes, which '
         'is 64 hex characters.  Any other forms of private key should be '
         'entered in the "Encoded Private Key" box.')
      ttipPubF = createToolTipObject( \
         'The full 65-byte public key in hexadecimal.  It consists '
         'of a "04" byte, followed by the 32-byte X-value, then the 32-byte '
         'Y-value.')
      ttipPubXY = createToolTipObject( \
         'X- and Y-coordinates of the public key.  Each value is 32 bytes (64 hex chars).')
      ttipHash = createToolTipObject( \
         'Raw hash160 of the [65-byte] public key.  It is 20 bytes (40 hex chars).')
      ttipAddr = createToolTipObject( \
         'Standard Bitcoin address expressed in Base58')


      headPrvR  = makeHorizFrame([QLabel('Encoded Private Key'), ttipPrvR, 'Stretch'])
      headPriv  = makeHorizFrame([QLabel('Raw Private Key'), ttipPriv, 'Stretch'])
      headPubF  = makeHorizFrame([QLabel('Full Public Key'), ttipPubF, 'Stretch'])
      headPubXY = makeHorizFrame([QLabel('Raw Public Key (x,y)'), ttipPubXY, 'Stretch'])
      headHash  = makeHorizFrame([QLabel('Public Key Hash160'), ttipHash, 'Stretch'])
      headAddr  = makeHorizFrame([QLabel('Bitcoin Address'), ttipAddr, 'Stretch'])
      
      keyDataLayout = QGridLayout()
      keyDataLayout.addWidget(headPrvR,                      0,0,  1,1)
      keyDataLayout.addWidget(self.txtPrvR,                  1,0,  1,1)
      keyDataLayout.addWidget(self.lblPrivType,              2,0,  1,1)

      keyDataLayout.addWidget(QLabel('or'),                  1,1,  1,1)

      keyDataLayout.addWidget(headPriv,                      0,2,  1,1)
      keyDataLayout.addWidget(self.txtPriv,                  1,2,  1,1)
      keyDataLayout.addWidget(makeHorizFrame(['Stretch', btnSwitchEnd]), \
                                                             2,2,  1,1)

      keyDataLayout.addWidget(HLINE(QFrame.Sunken),          3,0,  1,3)

      keyDataLayout.addWidget(headPubF,                      4,0,  1,1)
      keyDataLayout.addWidget(self.txtPubF,                  5,0,  1,1)

      keyDataLayout.addWidget(QLabel('or'),                  5,1,  1,1)

      keyDataLayout.addWidget(headPubXY,                     4,2,  1,1)
      keyDataLayout.addWidget(self.txtPubX,                  5,2,  1,1)
      keyDataLayout.addWidget(self.txtPubY,                  6,2,  1,1)

      keyDataLayout.addWidget(HLINE(QFrame.Sunken),          7,0,  1,3)

      keyDataLayout.addWidget(headAddr,                      8,0,  1,1)
      keyDataLayout.addWidget(self.txtAddr,                  9,0,  1,1)

      keyDataLayout.addWidget(QLabel('or'),                  9,1,  1,1)

      keyDataLayout.addWidget(headHash,                      8,2,  1,1)
      keyDataLayout.addWidget(self.txtHash,                  9,2,  1,1)

      keyDataFrame = QFrame()
      keyDataFrame.setFrameStyle(QFrame.Box)
      keyDataFrame.setLayout(keyDataLayout)



      self.lblTopLeft  = QRichLabel('Key Data Calculator', doWrap=False)
      self.lblTopMid   = QRichLabel('', doWrap=False)
      self.btnWltData  = QPushButton('Get Keys From Wallet')
      self.btnClearFrm = QPushButton('Clear')
      self.btnCalcKeys = QPushButton('Calculate')
      #self.btnClearFrm.setEnabled(False)
      #self.btnCalcKeys.setEnabled(False)
      self.btnWltData.setEnabled(False)
      self.connect(self.btnWltData,  SIGNAL('clicked()'), self.getOtherData)
      self.connect(self.btnClearFrm, SIGNAL('clicked()'), self.clearFormData)
      self.connect(self.btnCalcKeys, SIGNAL('clicked()'), self.keyWaterfall)


      topHeaderRow = makeHorizFrame([self.lblTopLeft, \
                                     'Stretch', \
                                     self.lblTopMid, \
                                     self.btnWltData, \
                                     self.btnClearFrm, \
                                     self.btnCalcKeys])
      tabKeysTopFrm = makeVertFrame( [topHeaderRow, keyDataFrame])
            

      self.btnSignMsg = QPushButton('Sign Message')
      self.btnInsDate = QPushButton('Insert Date')
      self.btnInsRnd  = QPushButton('Insert Random')
      self.btnVerify  = QPushButton('Verify Signature')
      self.btnMakeBlk = QPushButton('Create Signature Block')
      self.btnReadBlk = QPushButton('Import Signature Block')
      #self.btnSignMsg.setEnabled(False)
      #self.btnVerify.setEnabled(False)
      self.lblSigResult = QRichLabel('')

      self.connect(self.btnSignMsg,  SIGNAL('clicked()'), self.signMsg)
      self.connect(self.btnVerify,   SIGNAL('clicked()'), self.verifyMsg)
      self.connect(self.btnInsDate,  SIGNAL('clicked()'), self.insDate)
      self.connect(self.btnInsRnd,   SIGNAL('clicked()'), self.insRnd)

      self.connect(self.btnMakeBlk,   SIGNAL('clicked()'), self.makeBlk)
      self.connect(self.btnReadBlk,   SIGNAL('clicked()'), self.readBlk)

      ttipMsg = createToolTipObject( \
         'A message to be signed or verified by the key data above. '
         'Or create a random "nonce" to give to someone to sign.')
      ttipSig = createToolTipObject( \
         'The output of signing the message above will be put here, or you '
         'can copy in a signature of the above message, and check that it '
         'is valid against the public key on the left (if present).')

      msgBoxHead = makeHorizFrame([QRichLabel('Message'), ttipMsg, 'Stretch', \
                                     self.btnInsRnd, self.btnInsDate, self.btnSignMsg])
      sigBoxHead = makeHorizFrame([QRichLabel('Signature'), ttipSig, 'Stretch', \
                                                      self.lblSigResult, self.btnVerify])
      self.lblCopied = QRichLabel('')
      btmFrm = makeHorizFrame(['Stretch', self.lblCopied, self.btnMakeBlk, self.btnReadBlk])
      tabKeysBtmFrmLayout = QGridLayout()
      tabKeysBtmFrmLayout.addWidget( msgBoxHead,   0,0)
      tabKeysBtmFrmLayout.addWidget( sigBoxHead,   0,1)
      tabKeysBtmFrmLayout.addWidget( self.txtMsg,  1,0)
      tabKeysBtmFrmLayout.addWidget( self.txtSig,  1,1)
      tabKeysBtmFrmLayout.addWidget( btmFrm,       2,0, 1,2)
      tabKeysBtmFrm = QFrame()
      tabKeysBtmFrm.setFrameStyle(QFrame.Box)
      tabKeysBtmFrm.setLayout(tabKeysBtmFrmLayout)
                           

      btnBack = QPushButton('<<< Go Back')
      self.connect(btnBack, SIGNAL('clicked()'), self.accept)
      frmBack = makeHorizFrame([btnBack, 'Stretch'])

      dlgLayout = QHBoxLayout()
      dlgLayout.addWidget( makeVertFrame( [tabKeysTopFrm, tabKeysBtmFrm, frmBack] ) )
      #dlgLayout.addWidget( HLINE() )
      tabKeys.setLayout(dlgLayout)
      self.tabWidget.addTab(tabKeys, 'Keys')

      ##########################################################################
      ##########################################################################
      # TAB:  secp256k1
      ##########################################################################
      ##########################################################################
      # STUB: I'll probably finish implementing this eventually....
      tabEcc = QWidget()

      tabEccLayout = QGridLayout()
      self.txtScalarScalarA = QLineEdit()
      self.txtScalarScalarB = QLineEdit()
      self.txtScalarScalarC = QLineEdit()
      self.txtScalarScalarC.setReadOnly(True)

      self.txtScalarPtA     = QLineEdit()
      self.txtScalarPtB_x   = QLineEdit()
      self.txtScalarPtB_y   = QLineEdit()
      self.txtScalarPtC_x   = QLineEdit()
      self.txtScalarPtC_y   = QLineEdit()
      self.txtScalarPtC_x.setReadOnly(True)
      self.txtScalarPtC_y.setReadOnly(True)

      self.txtPtPtA_x = QLineEdit()
      self.txtPtPtA_y = QLineEdit()
      self.txtPtPtB_x = QLineEdit()
      self.txtPtPtB_y = QLineEdit()
      self.txtPtPtC_x = QLineEdit()
      self.txtPtPtC_y = QLineEdit()
      self.txtPtPtC_x.setReadOnly(True)
      self.txtPtPtC_y.setReadOnly(True)

      eccTxtList = [ \
          self.txtScalarScalarA, self.txtScalarScalarB, \
          self.txtScalarScalarC, self.txtScalarPtA, self.txtScalarPtB_x, \
          self.txtScalarPtB_y, self.txtScalarPtC_x, self.txtScalarPtC_y, \
          self.txtPtPtA_x, self.txtPtPtA_y, self.txtPtPtB_x, \
          self.txtPtPtB_y, self.txtPtPtC_x, self.txtPtPtC_y]
      
      dispFont = GETFONT('Var', 8) 
      w,h = tightSizeNChar(dispFont, 60)
      for txt in eccTxtList:
         txt.setMinimumWidth(w)
         txt.setFont(dispFont)

      
      self.btnCalcSS = QPushButton('Multiply Scalars (mod n)')
      self.btnCalcSP = QPushButton('Scalar Multiply EC Point')
      self.btnCalcPP = QPushButton('Add EC Points')
      self.btnClearSS = QPushButton('Clear')
      self.btnClearSP = QPushButton('Clear')
      self.btnClearPP = QPushButton('Clear')
      imgPlus  = QImageLabel('img/plus_orange.png')
      imgTimes1= QImageLabel('img/asterisk_orange.png')
      imgTimes2= QImageLabel('img/asterisk_orange.png')
      imgDown  = QImageLabel('img/arrow_down32.png')

      self.connect(self.btnCalcSS, SIGNAL('clicked()'),  self.multss)
      self.connect(self.btnCalcSP, SIGNAL('clicked()'),  self.multsp)
      self.connect(self.btnCalcPP, SIGNAL('clicked()'),  self.addpp)


      ##########################################################################
      # Scalar-Scalar Multiply
      sslblA = QRichLabel('a', hAlign=Qt.AlignHCenter)
      sslblB = QRichLabel('b', hAlign=Qt.AlignHCenter)
      sslblC = QRichLabel('a*b mod n', hAlign=Qt.AlignHCenter)

      
      ssLayout = QGridLayout()
      ssLayout.addWidget(sslblA,                  0,0,   1,1)
      ssLayout.addWidget(sslblB,                  0,2,   1,1)

      ssLayout.addWidget(self.txtScalarScalarA,   1,0,   1,1)
      ssLayout.addWidget(imgTimes1,               1,1,   1,1)
      ssLayout.addWidget(self.txtScalarScalarB,   1,2,   1,1)

      ssLayout.addWidget(makeHorizFrame(['Stretch', self.btnCalcSS, 'Stretch']), \
                                                  2,0,   1,3)
      #ssLayout.addWidget(makeHorizFrame(['Stretch', imgDown, 'Stretch']), \
                                                  #3,0,   1,3)
      ssLayout.addWidget(makeHorizFrame(['Stretch', sslblC, self.txtScalarScalarC, 'Stretch']), \
                                                  3,0,   1,3)
      ssLayout.setVerticalSpacing(1)
      frmSS = QFrame()
      frmSS.setFrameStyle(STYLE_SUNKEN)
      frmSS.setLayout(ssLayout)

      ##########################################################################
      # Scalar-ECPoint Multiply
      splblA = QRichLabel('a',                             hAlign=Qt.AlignHCenter)
      splblB = QRichLabel('<b>B</b>',                      hAlign=Qt.AlignHCenter)
      splblBx= QRichLabel('<b>B</b><font size=2>x</font>', hAlign=Qt.AlignRight)
      splblBy= QRichLabel('<b>B</b><font size=2>y</font>', hAlign=Qt.AlignRight)
      splblC = QRichLabel('<b>C</b> = a*<b>B</b>',         hAlign=Qt.AlignHCenter)
      splblCx= QRichLabel('(a*<b>B</b>)<font size=2>x</font>', hAlign=Qt.AlignRight)
      splblCy= QRichLabel('(a*<b>B</b>)<font size=2>y</font>', hAlign=Qt.AlignRight)
      spLayout = QGridLayout()
      spLayout.addWidget(splblA,                  0,0,    1,1)
      spLayout.addWidget(splblB,                  0,2,    1,1)

      spLayout.addWidget(self.txtScalarPtA,       1,0,    1,1)
      spLayout.addWidget(imgTimes2,               1,1,    1,1)
      spLayout.addWidget(self.txtScalarPtB_x,     1,2,    1,1)
      spLayout.addWidget(self.txtScalarPtB_y,     2,2,    1,1)

      spLayout.addWidget(makeHorizFrame(['Stretch', self.btnCalcSP, 'Stretch']), \
                                                  3,0,   1,3)
      #spLayout.addWidget(makeHorizFrame(['Stretch', imgDown, 'Stretch']), \
                                                  #4,0,   1,3)
      #spLayout.addWidget(makeHorizFrame(['Stretch', splblC, 'Stretch']), \
                                                  #5,0,   1,3)
      spLayout.addWidget(makeHorizFrame(['Stretch', splblCx, self.txtScalarPtC_x, 'Stretch']), \
                                                  4,0,   1,3)
      spLayout.addWidget(makeHorizFrame(['Stretch', splblCy, self.txtScalarPtC_y, 'Stretch']), \
                                                  5,0,   1,3)
      spLayout.setVerticalSpacing(1)
      frmSP = QFrame()
      frmSP.setFrameStyle(STYLE_SUNKEN)
      frmSP.setLayout(spLayout)
      
      ##########################################################################
      # ECPoint Addition
      pplblA  = QRichLabel('<b>A</b>',                       hAlign=Qt.AlignHCenter)
      pplblB  = QRichLabel('<b>B</b>',                       hAlign=Qt.AlignHCenter)
      pplblAx = QRichLabel('<b>A</b><font size=2>x</font>', hAlign=Qt.AlignHCenter)
      pplblAy = QRichLabel('<b>A</b><font size=2>y</font>', hAlign=Qt.AlignHCenter)
      pplblBx = QRichLabel('<b>B</b><font size=2>x</font>', hAlign=Qt.AlignHCenter)
      pplblBy = QRichLabel('<b>B</b><font size=2>y</font>', hAlign=Qt.AlignHCenter)
      pplblC  = QRichLabel('<b>C</b> = <b>A</b>+<b>B</b>',  hAlign=Qt.AlignHCenter)
      pplblCx= QRichLabel('(<b>A</b>+<b>B</b>)<font size=2>x</font>', hAlign=Qt.AlignRight)
      pplblCy= QRichLabel('(<b>A</b>+<b>B</b>)<font size=2>y</font>', hAlign=Qt.AlignRight)
      ppLayout = QGridLayout()
      ppLayout.addWidget(pplblA,                  0,0,    1,1)
      ppLayout.addWidget(pplblB,                  0,2,    1,1)
      ppLayout.addWidget(self.txtPtPtA_x,         1,0,    1,1)
      ppLayout.addWidget(self.txtPtPtA_y,         2,0,    1,1)
      ppLayout.addWidget(imgPlus,                 1,1,    2,1)
      ppLayout.addWidget(self.txtPtPtB_x,         1,2,    1,1)
      ppLayout.addWidget(self.txtPtPtB_y,         2,2,    1,1)
      ppLayout.addWidget(makeHorizFrame(['Stretch', self.btnCalcPP, 'Stretch']), \
                                                  3,0,   1,3)
      #ppLayout.addWidget(makeHorizFrame(['Stretch', imgDown, 'Stretch']), \
                                                  #4,0,   1,3)
      #ppLayout.addWidget(makeHorizFrame(['Stretch', pplblC, 'Stretch']), \
                                                  #5,0,   1,3)
      ppLayout.addWidget(makeHorizFrame(['Stretch', pplblCx, self.txtPtPtC_x, 'Stretch']), \
                                                  4,0,   1,3)
      ppLayout.addWidget(makeHorizFrame(['Stretch', pplblCy, self.txtPtPtC_y, 'Stretch']), \
                                                  5,0,   1,3)
      ppLayout.setVerticalSpacing(1)
      frmPP = QFrame()
      frmPP.setFrameStyle(STYLE_SUNKEN)
      frmPP.setLayout(ppLayout)

      
      lblDescr = QRichLabel( \
         'Use this form to perform Bitcoin elliptic curve calculations.  All '
         'operations are performed on the secp256k1 elliptic curve, which is '
         'the one used for Bitcoin. '
         'Supply all values as 32-byte, big-endian, hex-encoded integers.')

      btnClear = QPushButton('Clear')
      btnClear.setMaximumWidth(2*relaxedSizeStr(btnClear, 'Clear')[0])
      self.connect(btnClear, SIGNAL('clicked()'), self.eccClear)


      eccLayout = QVBoxLayout()
      eccLayout.addWidget(makeHorizFrame([lblDescr, btnClear]))
      eccLayout.addWidget(frmSS)
      eccLayout.addWidget(frmSP)
      eccLayout.addWidget(frmPP)
      tabEcc.setLayout(eccLayout)
      self.tabWidget.addTab(tabEcc, 'Elliptic Curve')


      calcLayout = QHBoxLayout() 
      calcLayout.addWidget(self.tabWidget)
      self.setLayout(calcLayout)

      self.tabWidget.setCurrentIndex(tabStart)
   
      self.setWindowTitle('ECDSA Calculator')
      self.setWindowIcon(QIcon( self.main.iconfile))



   #############################################################################
   def keyTextEdited(self, txtIndex):
      notEmpty = not self.formIsEmpty()
      #self.btnClearFrm.setEnabled(notEmpty)
      #self.btnCalcKeys.setEnabled(notEmpty)
      #self.btnSignMsg.setEnabled(notEmpty)
      #self.btnVerify.setEnabled(notEmpty)

      if not isinstance(txtIndex, (list,tuple)):
         txtIndex = [txtIndex]

      for i,txt in enumerate(self.keyTxtList):
         if not i in txtIndex:
            txt.setText('') 

   #############################################################################
   def msgTextChanged(self):
      """ 
      Yes, I intended to use text 'changed', instead of 'edited' here.
      Because I don't care how the text was modified, it's going to break
      the signature.
      """
      self.lblSigResult.setText('')


   #############################################################################
   def formIsEmpty(self):
      totalEmpty = [0 if len(str(a.text()))>0 else 1 for a in self.keyTxtList]
      allEmpty = not sum(totalEmpty)!=0 
      #self.btnSignMsg.setEnabled(not allEmpty)
      return allEmpty

   #############################################################################
   def keyWaterfall(self):
      self.returnPressedFirst = True
      try:
         prvrStr =               str(self.txtPrvR.text()).replace(' ','')
         privBin = hex_to_binary(str(self.txtPriv.text()).replace(' ',''))
         pubxBin = hex_to_binary(str(self.txtPubX.text()).replace(' ',''))
         pubyBin = hex_to_binary(str(self.txtPubY.text()).replace(' ',''))
         pubfBin = hex_to_binary(str(self.txtPubF.text()).replace(' ',''))
         addrB58 =               str(self.txtAddr.text()).replace(' ','')
         a160Bin = hex_to_binary(str(self.txtHash.text()).replace(' ',''))

      except:
         QMessageBox.critical(self, 'Invalid Entry', \
            'You entered invalid data!', QMessageBox.Ok)
         return

      self.lblPrivType.setText('')
      if len(prvrStr)>0:
         try:
            privBin, keytype = parsePrivateKeyData(prvrStr)
            self.txtPriv.setText( binary_to_hex(privBin))
            self.lblPrivType.setText('<font color="green">' + keytype + '</font>')
         except:
            QMessageBox.critical(self, 'Invalid Private Key Data', \
               'Private Key data is not recognized!', QMessageBox.Ok)
            raise
            return
      elif len(privBin)>0:
         try:
            priv37  = '\x80' + privBin + computeChecksum('\x80' + privBin)
            privB58 = binary_to_base58(priv37)
            typestr = parsePrivateKeyData(privB58)[1]
            self.txtPrvR.setText(privB58)
            self.lblPrivType.setText('<font color="green">' + typestr + '</font>')
         except:
            QMessageBox.critical(self, 'Invalid Private Key Data', \
               'Private Key data is not recognized!', QMessageBox.Ok)
            raise
            return
     
      if len(privBin)>0:
         pub = CryptoECDSA().ComputePublicKey(SecureBinaryData(privBin))
         pubfBin = pub.toBinStr()
         self.txtPubF.setText(binary_to_hex(pubfBin))

     
      if len(pubfBin)>0:
         try:
            pubxBin = pubfBin[1:1+32]
            pubyBin = pubfBin[  1+32:1+32+32]
            self.txtPubX.setText(binary_to_hex(pubxBin))
            self.txtPubY.setText(binary_to_hex(pubyBin))
            a160Bin = hash160(pubfBin)
            self.txtHash.setText(binary_to_hex(a160Bin))
         except:
            QMessageBox.critical(self, 'Invalid Public Key Data', \
               'Public Key data is not recognized!', QMessageBox.Ok)
            raise
            return
      elif len(pubxBin)>0 and len(pubyBin)>0:
         try:
            pubfBin = '\x04' + pubxBin + pubyBin
            self.txtPubF.setText(binary_to_hex(pubfBin))
            a160Bin = hash160(pubfBin)
            self.txtHash.setText(binary_to_hex(a160Bin))
         except:
            QMessageBox.critical(self, 'Invalid Public Key Data', \
               'Public Key data is not recognized!', QMessageBox.Ok)
            raise
            return

      if len(a160Bin)>0:
         try:
            addrB58 = hash160_to_addrStr(a160Bin)
            self.txtAddr.setText(addrB58)
         except:
            QMessageBox.critical(self, 'Invalid Address Data', \
               'Address data is not recognized!', QMessageBox.Ok)
            return
      elif len(addrB58)>0:
         try:
            raw25byte = base58_to_binary(addrB58)
            if len(raw25byte)!=25:
               QMessageBox.critical(self, 'Invalid Address', \
               'The Bitcoin address supplied is invalid.', QMessageBox.Ok)
               return
            data,chk = raw25byte[:21], raw25byte[21:]
            fixedData = verifyChecksum(data,chk)
            if fixedData!=data:
               if len(fixedData)==0:
                  QMessageBox.critical(self, 'Invalid Address', \
                  'The Bitcoin address has an error in it.  Please double-check '
                  'that it was entered properly.', QMessageBox.Ok)
                  return
            self.txtAddr.setText(hash160_to_addrStr(fixedData[1:]))
               
            a160Bin = addrStr_to_hash160(addrB58)
            self.txtHash.setText(binary_to_hex(a160Bin))
         except:
            QMessageBox.critical(self, 'Invalid Address Data', \
               'Address data is not recognized!', QMessageBox.Ok)
            return

      #self.btnSignMsg.setEnabled( len(privBin)>0 )
      #self.btnVerify.setEnabled( len(pubfBin)>0 )

      for txt in self.keyTxtList:
         txt.setCursorPosition(0)

      self.checkIfAddrIsOurs(a160Bin)
         
            

   #############################################################################
   def checkIfAddrIsOurs(self, addr160):
      wltID = self.main.getWalletForAddr160(addr160)
      if wltID=='':
         self.lblTopMid.setText('')
         self.btnWltData.setEnabled(False)
      else:
         self.lblTopMid.setText('<font color="green">This key is in one of your wallets</font>')
         self.btnWltData.setEnabled(True)
      return wltID
      

   #############################################################################
   def getOtherData(self):
      ''' Look in your wallets for the address, fill in pub/priv keys '''

      # It seems that somehow the "Get Keys" button is automatically linked to
      # the form's returnPressed signal.  I have tried to disable this, but I
      # can't figure out how!  So instead, I have to put in this stupid hack
      # to prevent this action from being triggered prematurely
      if self.returnPressedFirst:
         self.returnPressedFirst=False
         return

      a160Bin = hex_to_binary(str(self.txtHash.text()).replace(' ',''))
      wltID = self.checkIfAddrIsOurs(a160Bin)
      if wltID!='':
         havePriv = True
         # This address is ours, get the priv key and fill in everything else
         wlt = self.main.walletMap[wltID]
         if wlt.useEncryption and wlt.isLocked:
            dlg = DlgUnlockWallet(wlt, self.main, 'Encrypt New Address')
            if not dlg.exec_():
               reply = QMessageBox.critical(self, 'Wallet is locked',
                  'Could not unlock wallet, so private key data could not '
                  'be acquired.', QMessageBox.Ok)
               havePriv = False
         
         addr = self.main.walletMap[wltID].getAddrByHash160(a160Bin)
         if havePriv:
            hexPriv = addr.binPrivKey32_Plain.toHexStr()
            self.clearFormData()
            self.txtPriv.setText(hexPriv)
            self.keyWaterfall()
         else:
            hexPub = addr.binPublicKey65.toHexStr()
            self.clearFormData()
            self.txtPubF.setText(hexPub)
            self.keyWaterfall()


   #############################################################################
   def clearFormData(self):
      for wdgt in self.keyTxtList:
         wdgt.setText('')
      self.lblPrivType.setText('')
      self.lblTopMid.setText('')
      self.btnWltData.setEnabled(False)

   #############################################################################
   def privSwitch(self):
      privHex = str(self.txtPriv.text()).strip().replace(' ','')
      if len(privHex)>0:
         self.txtPriv.setText(hex_switchEndian(privHex))
      self.keyTextEdited(0)
      
   #############################################################################
   def insRnd(self):
      rnd = SecureBinaryData().GenerateRandom(8)
      currtxt = self.readMsg()
      if not currtxt.endswith(' ') and not len(currtxt)==0:
         currtxt += ' '
      self.txtMsg.setText(currtxt + rnd.toHexStr())
      
   #############################################################################
   def insDate(self):
      currtxt = self.readMsg()
      if not currtxt.endswith(' ') and not len(currtxt)==0:
         currtxt += ' '
      self.txtMsg.setText(currtxt + unixTimeToFormatStr(RightNow()))

   #############################################################################
   def signMsg(self):
      self.keyWaterfall()
      try:
         binPriv = hex_to_binary(str(self.txtPriv.text()).strip().replace(' ',''))
      except:
         QMessageBox.critical(self, 'Input Error', \
           'There was an error parsing the private key.', QMessageBox.Ok)
         return

      strMsg  = self.readMsg()
         
      if len(binPriv)!=32:
         QMessageBox.critical(self, 'Invalid Private Key', \
           'Cannot sign a message without a valid private key.', QMessageBox.Ok)
         return
      if len(strMsg)==0:
         QMessageBox.critical(self, 'Nothing to Sign!', \
           'There is no message to sign!', QMessageBox.Ok)
         return

      modMsg = 'Bitcoin Signed Message:\n' + strMsg
      sig = CryptoECDSA().SignData(SecureBinaryData(modMsg), \
                                   SecureBinaryData(binPriv))
      self.txtSig.setText(sig.toHexStr())


   #############################################################################
   def verifyMsg(self):
      self.keyWaterfall()
      try:
         binPub = hex_to_binary(str(self.txtPubF.text()).strip().replace(' ',''))
         addrB58 = hash160_to_addrStr(hash160(binPub))
      except:
         QMessageBox.critical(self, 'Input Error', \
           'There was an error parsing the public key.', QMessageBox.Ok)
         return

      try:
         binSig = hex_to_binary(str(self.txtSig.toPlainText()).strip().replace(' ',''))
      except:
         QMessageBox.critical(self, 'Input Error', \
           'The signature data is not recognized.', QMessageBox.Ok)
         return

      strMsg = self.readMsg()
         
         
      if len(binPub)!=65:
         QMessageBox.critical(self, 'Invalid Public Key!', \
           'Cannot verify a message without a valid public key.', QMessageBox.Ok)
         return
      if len(binSig)==0:
         QMessageBox.critical(self, 'No Signature!', \
           'There is no signature to verify', QMessageBox.Ok)
         return
      if len(strMsg)==0:
         QMessageBox.critical(self, 'Nothing to Verify!', \
           'Need the original message in order to verify the signature.', QMessageBox.Ok)
         return

      modMsg = 'Bitcoin Signed Message:\n' + strMsg
      isValid = CryptoECDSA().VerifyData(SecureBinaryData(modMsg), \
                                         SecureBinaryData(binSig), \
                                         SecureBinaryData(binPub))

      if isValid:
         MsgBoxCustom(MSGBOX.Good, 'Verified!', \
            'The owner of the following Bitcoin address...'
            '<br><br>'
            '<b>%s</b>'
            '<br><br>'
            '...has digitally signed the following message:'
            '<br><br>'
            '<i><b>"%s"</b></i>'
            '<br><br>'
            'The supplied signature <b>is valid</b>!' % (addrB58, strMsg))
         self.lblSigResult.setText('<font color="green">Valid Signature!</font>')
      else:
         MsgBoxCustom(MSGBOX.Error, 'Invalid Signature!', \
                                    'The supplied signature <b>is not valid</b>!')
         self.lblSigResult.setText('<font color="red">Invalid Signature!</font>')

   ############################################################################
   def readMsg(self):
      msg = str(self.txtMsg.toPlainText())
      msg = msg.replace('\n',' ')
      msg = msg.replace('"','\'')
      msg = msg.strip()
      return msg

   ############################################################################
   def makeBlk(self):
      try:
         pubfBin = hex_to_binary(str(self.txtPubF.text()).replace(' ',''))
      except:
         QMessageBox.critical(self, 'Public Key Error!', \
           'The public key is invalid.', QMessageBox.Ok)
         
      try:
         sigBin  = hex_to_binary(str(self.txtSig.toPlainText()).replace(' ',''))
      except:
         QMessageBox.critical(self, 'Signature Error', \
           'The signature is in an unrecognized format', QMessageBox.Ok)

      addrB58 = str(self.txtAddr.text()).replace(' ','')
      rawMsg  = self.readMsg()

      txt = makeSigBlock(addrB58, rawMsg, pubfBin, sigBin)
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(txt)
      self.lblCopied.setText('Copied to clipboard!')

   ############################################################################
   def readBlk(self):
      """ Create a very simple dialog for entering a signature block """
      class DlgEnterSigBlock(QDialog):
         def __init__(self, parent, main):
            super(DlgEnterSigBlock, self).__init__(parent)

            self.txt = ''
            lbl = QRichLabel('Copy a signature block into the text box below')
            self.txtbox = QTextEdit()
            fnt = GETFONT('Fixed', 8)
            self.txtbox.setFont(fnt)
            w,h = tightSizeNChar(fnt, 70)
            self.txtbox.setMinimumWidth(w)
            self.txtbox.setMinimumHeight(6.2*h)
            btnOkay   = QPushButton('Okay')
            btnCancel = QPushButton('Cancel')
            self.connect(btnOkay,   SIGNAL('clicked()'), self.pressOkay)
            self.connect(btnCancel, SIGNAL('clicked()'), self.pressCancel)
            bbox = QDialogButtonBox()
            bbox.addButton(btnOkay,   QDialogButtonBox.AcceptRole)
            bbox.addButton(btnCancel, QDialogButtonBox.RejectRole)

            layout = QVBoxLayout()
            layout.addWidget(lbl)
            layout.addWidget(self.txtbox)
            layout.addWidget(bbox)
            self.setLayout(layout)
            self.setWindowTitle('Import Signature Block')
            self.setWindowIcon(QIcon(main.iconfile))

         def pressOkay(self):
            self.txt = str(self.txtbox.toPlainText())
            self.accept()
         
         def pressCancel(self):
            self.reject()

      dlg = DlgEnterSigBlock(self,self.main)
      if dlg.exec_():
         addr,s,pub,sig = readSigBlock(self, dlg.txt)
         self.txtPubF.setText(binary_to_hex(pub))
         self.txtSig.setText(binary_to_hex(sig))
         self.txtAddr.setText(addr)
         self.txtMsg.setText(s)
         self.keyWaterfall()
         self.verifyMsg()
         

   #############################################################################
   def getBinary(self, widget, name):
      try:
         hexVal = str(widget.text())
         binVal = hex_to_binary(hexVal)
      except:
         QMessageBox.critical(self, 'Bad Input', \
            'Value "%s" is invalid.  Make sure the value is specified in '
            'hex, big-endian' % name , QMessageBox.Ok)
         return ''
      return binVal


   #############################################################################
   def multss(self):
      binA = self.getBinary(self.txtScalarScalarA, 'a')
      binB = self.getBinary(self.txtScalarScalarB, 'b')
      C = CryptoECDSA().ECMultiplyScalars(binA, binB)
      self.txtScalarScalarC.setText( binary_to_hex(C))

      for txt in [self.txtScalarScalarA, \
                  self.txtScalarScalarB, \
                  self.txtScalarScalarC]:
         txt.setCursorPosition(0)
            
   #############################################################################
   def multsp(self):
      binA  = self.getBinary(self.txtScalarPtA, 'a')
      binBx = self.getBinary(self.txtScalarPtB_x, '<b>B</b><font size=2>x</font>')
      binBy = self.getBinary(self.txtScalarPtB_y, '<b>B</b><font size=2>y</font>')

      if not CryptoECDSA().ECVerifyPoint(binBx, binBy):
         QMessageBox.critical(self, 'Invalid EC Point', \
            'The point you specified (<b>B</b>) is not on the '
            'elliptic curved used in Bitcoin (secp256k1).', QMessageBox.Ok)
         return

      C = CryptoECDSA().ECMultiplyPoint(binA, binBx, binBy)
      self.txtScalarPtC_x.setText(binary_to_hex(C[:32]))
      self.txtScalarPtC_y.setText(binary_to_hex(C[32:]))
      
      for txt in [self.txtScalarPtA, \
                  self.txtScalarPtB_x, self.txtScalarPtB_y, \
                  self.txtScalarPtC_x, self.txtScalarPtC_y]:
         txt.setCursorPosition(0)

   #############################################################################
   def addpp(self):
      binAx = self.getBinary(self.txtPtPtA_x, '<b>A</b><font size=2>x</font>')
      binAy = self.getBinary(self.txtPtPtA_y, '<b>A</b><font size=2>y</font>')
      binBx = self.getBinary(self.txtPtPtB_x, '<b>B</b><font size=2>x</font>')
      binBy = self.getBinary(self.txtPtPtB_y, '<b>B</b><font size=2>y</font>')

      if not CryptoECDSA().ECVerifyPoint(binAx, binAy):
         QMessageBox.critical(self, 'Invalid EC Point', \
            'The point you specified (<b>A</b>) is not on the '
            'elliptic curved used in Bitcoin (secp256k1).', QMessageBox.Ok)
         return

      if not CryptoECDSA().ECVerifyPoint(binBx, binBy):
         QMessageBox.critical(self, 'Invalid EC Point', \
            'The point you specified (<b>B</b>) is not on the '
            'elliptic curved used in Bitcoin (secp256k1).', QMessageBox.Ok)
         return

      C = CryptoECDSA().ECAddPoints(binAx, binAy, binBx, binBy)
      self.txtPtPtC_x.setText(binary_to_hex(C[:32]))
      self.txtPtPtC_y.setText(binary_to_hex(C[32:]))

      for txt in [self.txtPtPtA_x, self.txtPtPtA_y, \
                  self.txtPtPtB_x, self.txtPtPtB_y, \
                  self.txtPtPtC_x, self.txtPtPtC_y]:
         txt.setCursorPosition(0)


   #############################################################################
   def eccClear(self):
      self.txtScalarScalarA.setText('')
      self.txtScalarScalarB.setText('')
      self.txtScalarScalarC.setText('')

      self.txtScalarPtA.setText('')
      self.txtScalarPtB_x.setText('')
      self.txtScalarPtB_y.setText('')
      self.txtScalarPtC_x.setText('')
      self.txtScalarPtC_y.setText('')

      self.txtPtPtA_x.setText('')
      self.txtPtPtA_y.setText('')
      self.txtPtPtB_x.setText('')
      self.txtPtPtB_y.setText('')
      self.txtPtPtC_x.setText('')
      self.txtPtPtC_y.setText('')





################################################################################
class DlgOwnership(QDialog):
   """
   STUB:  maybe I'll pick this up again, later

   We may wish to demonstrate, or make someone else demonstrate, that they own
   a particular address.  We create a "challenge" string and ask the person to
   sign the string with the private key of the specified address.  

   We want the challenge string to be "fresh" and unique.  Just in case the 
   attacker doesn't have the address, but already has a signed message from
   that address from a different occasion.  
   """
   def __init__(self, parent=None, main=None):
      super(DlgOwnership, self).__init__(parent)

      self.parent = parent
      self.main   = main

      self.radioCreateChallenge = QRadioButton('I want someone to prove they own an address')
      self.radioCreateResponse  = QRadioButton('I need to prove that I own an address')
      self.radioVerifyResponse  = QRadioButton('Some gave me a proof-of-ownership I need to verify')
      btngrp = QButtonGroup(self)
      btngrp.addButton(self.radioCreateChallenge)
      btngrp.addButton(self.radioCreateResponse)
      btngrp.addButton(self.radioVerifyResponse)
      btngrp.setExclusive(True)
      self.radioCreateChallenge.setChecked(True)

      self.connect(self.radioCreateChallenge, SIGNAL('clicked(bool)'), self.changeStack)
      self.connect(self.radioCreateResponse,  SIGNAL('clicked(bool)'), self.changeStack)
      self.connect(self.radioVerifyResponse,  SIGNAL('clicked(bool)'), self.changeStack)


      ## Create the stacked widget
      self.challengeStack = QStackedWidget()
      dispFont = GETFONT('Var', 8)
      w,h = relaxedSizeNChar(dispFont, 40)
      wmin = 250
   
      ## Create-Challenge options
      ccWidget = QWidget()
      ccLayout = QGridLayout()

      self.txtCCDescr = QRichLabel( \
         'Since all transactions are public but identities are not tied to '
         'the addresses, you may need to "challenge" someone to prove that '
         'they own a particular Bitcoin address (perhaps you received money '
         'from that address, and the other person claims it was them who '
         'sent it to you).  Enter the address to be verified, and then click '
         'the button to create a "challenge."  The challenge can be emailed '
         'to the other party')
      self.txtCCAddress = QLineEdit()
      self.txtCCAddress.setMinimumWidth(wmin)
      self.txtCCAddress.sizeHint = lambda: QSize(w,h)
      self.txtCCAddress.setFont(dispFont)
      
      # Only advanced users should be able to specify a custom string
      self.txtCCCustomStr = QLineEdit()
      self.txtCCCustomStr.setMinimumWidth(wmin)
      self.txtCCCustomStr.sizeHint = lambda: QSize(w,h)
      self.txtCCCustomStr.setFont(dispFont)
      self.txtCCCustomStr.setEnabled(False)

      self.txtCCChallenge = QTextEdit()
      self.txtCCChallenge.setMinimumWidth(wmin)
      self.txtCCChallenge.sizeHint = lambda: QSize(w,int(3.1*h))
      self.txtCCChallenge.setFont(dispFont)
      self.txtCCChallenge.setReadOnly(True)

      self.lblCCcopied = QRichLabel('')
      self.btnCCCreate = QPushButton('Create Challenge')


      
   def defaultChallengeStr(self):
      # Grab the root hash160 of the first wallet that we own.
      uniqueStr = ''
      for wid,wlt in self.main.walletMap.iteritems():
         if not wlt.watchOnly:
            uniqueStr = binary_to_hex(wlt.addrMap['ROOT'].getAddr160())
            break
      return ('%s %s' % (unixTimeToFormatStr(RightNow()), uniqueStr)).strip()
      
      
   def btnPressMake(self):
      addrB58 = str(self.txtCCAddress.text())
      netbyte = checkAddrType(addrB58)
      if netbyte == -1:
         QMessageBox.critical(self, 'Bad Address', \
            'The address you entered is invalid!  Please check '
            'that it was entered correctly.', QMessageBox.Ok)
         return
      elif netbyte != ADDRBYTE:
         QMessageBox.critical(self, 'Wrong Network!', \
            'The address you entered is for the wrong network! '
            'The address is for the <b>%s</b> but you are running '
            'Armory on the <b>%s</b>!' % (NETWORKS[netbyte], NETWORKS[ADDRBYTE]), \
            QMessageBox.Ok)
         return


      strChallenge = str(self.txtCCCustomStr.text()).strip()
      if len(strChallenge)==0:
         strChallenge = self.defaultChallengeStr()
         
      self.txtCCChallenge.setText( self.makeSigBlock(addrB58, strChallenge))


      


   def changeStack(self, dummy):
      """ 
      Dummy argument is only to take the bool from 'clicked(bool)', but we
      don't actually use it
      """ 
      if self.radioCreateResponse.isChecked():
         self.challengeStack.setCurrentIndex(1)
      elif self.radioVerifyResponse.isChecked():
         self.challengeStack.setCurrentIndex(2)
      else:
         # We put this last to be default in case somehow nothing is checked
         self.challengeStack.setCurrentIndex(0)




################################################################################
################################################################################
if __name__=='__main__':
   app = QApplication(sys.argv)
   app.setApplicationName("dumbdialogs")

   form = dlgNewWallet()
   #form = dlgchangepassphrase(noprevencrypt=true)

   form.show()
   app.exec_()








