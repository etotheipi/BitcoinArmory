import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qtdefines import *

from armoryengine import *
from armorymodels import *

MIN_PASSWD_WIDTH = lambda obj: tightSizeStr(obj, '*'*16)[0]


################################################################################
class DlgUnlockWallet(QDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgUnlockWallet, self).__init__(parent)

      self.wlt = wlt
      self.parent = parent
      self.main   = main

      lblDescr  = QLabel("Enter your passphrase to unlock this wallet")
      lblPasswd = QLabel("Passphrase:")
      self.edtPasswd = QLineEdit()
      self.edtPasswd.setEchoMode(QLineEdit.Password)
      self.edtPasswd.setMinimumWidth(MIN_PASSWD_WIDTH(self))
      fm = QFontMetricsF(QFont(self.font()))
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
      self.setWindowTitle('Unlock Wallet - ' + wlt.uniqueIDB58)

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

      
      #btngrp = self.QButtonGroup()
      #self.QRadioButton()
      #lbl
   

################################################################################
class DlgNewWallet(QDialog):

   def __init__(self, parent=None, main=None):
      super(DlgNewWallet, self).__init__(parent)

      self.selectedImport = False

      # Options for creating a new wallet
      lblDlgDescr = QLabel('Create a new wallet for managing your funds.\n'
                           'The name and description can be changed at any time.')
      lblDlgDescr.setWordWrap(True)

      self.edtName = QLineEdit()
      self.edtName.setMaxLength(32)
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
      cryptoLayout.addWidget(lblComputeDescr,     0, 0, 1, 3)
      cryptoLayout.addWidget(lblComputeTime,      1, 0, 1, 1)
      cryptoLayout.addWidget(lblComputeMem,       2, 0, 1, 1)
      cryptoLayout.addWidget(self.edtComputeTime, 1, 1, 1, 1)
      cryptoLayout.addWidget(timeDescrTip,        1, 3, 1, 1)
      cryptoLayout.addWidget(self.edtComputeMem,  2, 1, 1, 1)
      cryptoLayout.addWidget(memDescrTip,         2, 3, 1, 1)
      #cryptoLayout.addWidget(self.chkForkOnline,  3, 0, 1, 1)
      #cryptoLayout.addWidget(onlineToolTip,       3, 1, 1, 1)

      self.cryptoFrame = QFrame()
      self.cryptoFrame.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
      self.cryptoFrame.setLayout(cryptoLayout)
      self.cryptoFrame.setVisible(False)

      self.chkUseCrypto  = QCheckBox("Use wallet &encryption")
      self.chkUseCrypto.setChecked(True)
      usecryptoTooltip = createToolTipObject(
                                 'Encryption prevents anyone who accesses your computer '
                                 '(or wallet file) from being able to spend your money, but it '
                                 'will require '
                                 'typing in a passphrase every time you want send money.'
                                 'However, you *can* still see incoming transactions and '
                                 'generate new receiving addresses without supplying your '
                                 'passphrase.\n\n '
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
      masterLayout.addWidget(self.btnImportWlt,  1, 2, 1, 1)
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
      self.setWindowIcon(QIcon('img/armory_logo_32x32.png'))



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
         kdfT, kdfUnit = str(self.edtComputeTime.text()).split(' ') 
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
         raise
         QMessageBox.critical(self, 'Invalid KDF Parameters', \
            'The KDF parameters that you entered are not valid.  Please '
            'specify KDF time in seconds or milliseconds, such as '
            '"250 ms" or "2.1 s".  And specify memory as kB or MB, such as '
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

      self.setWindowIcon(QIcon('img/armory_logo_32x32.png'))

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
      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap('img/MsgBox_warning64.png'))
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

      self.edtName = QLineEdit()
      self.edtName.setMaxLength(32)
      lblName = QLabel("Wallet &name:")
      lblName.setBuddy(self.edtName)

      self.edtDescr = QTextEdit()
      tightHeight = tightSizeNChar(self.edtDescr, 1)[1]
      #fm = QFontMetricsF(QFont(self.edtDescr.font()))
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
      self.wltAddrView.setMinimumWidth(800)
      initialColResize(self.wltAddrView, [0.2, 0.4, 64, 80, 0.3])
   
      # TODO:  Need to do different things depending on which col was clicked
      uacfv = lambda x: self.main.updateAddressCommentFromView(self.wltAddrView, self.wlt)
      self.connect(self.wltAddrView, SIGNAL('doubleClicked(QModelIndex)'), uacfv)
                   
      #self.connect(self.wltAddrView, SIGNAL('doubleClicked(QModelIndex)'), \
                   #self.main,        SLOT('addrViewDblClicked(QModelIndex)'))
      #clip = QApplication.clipboard()
      #def copyAddrToClipboard()


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
      lbtnGenAddr = QLabelButton('Receive Bitcoins')
      lbtnImportA = QLabelButton('Import External Address')
      lbtnDeleteA = QLabelButton('Remove Imported Address')
      lbtnSweepA  = QLabelButton('Sweep Wallet/Address')

      lbtnForkWlt = QLabelButton('Create Watching-Only Copy')
      lbtnMkPaper = QLabelButton('Make Paper Backup')
      lbtnExport  = QLabelButton('Make Digital Backup')
      lbtnRemove  = QLabelButton('Delete/Remove Wallet')

      lbtnUnspent  = QLabelButton('View unspent transactions')

      self.connect(lbtnSendBtc, SIGNAL('clicked()'), self.execSendBtc)
      self.connect(lbtnGenAddr, SIGNAL('clicked()'), self.getNewAddress)
      self.connect(lbtnMkPaper, SIGNAL('clicked()'), self.execPrintDlg)
      self.connect(lbtnRemove,  SIGNAL('clicked()'), self.execRemoveDlg)
      self.connect(lbtnImportA, SIGNAL('clicked()'), self.execImportAddress)
      self.connect(lbtnDeleteA, SIGNAL('clicked()'), self.execDeleteAddress)
      self.connect(lbtnExport,  SIGNAL('clicked()'), self.saveWalletCopy)
      self.connect(lbtnForkWlt, SIGNAL('clicked()'), self.forkOnlineWallet)

      optFrame = QFrame()
      optFrame.setFrameStyle(QFrame.Box|QFrame.Sunken)
      optLayout = QVBoxLayout()

      hasPriv = not self.wlt.watchingOnly
      adv = (self.main.usermode in (USERMODE.Advanced, USERMODE.Developer))

      def createVBoxSeparator():
         frm = QFrame()
         frm.setFrameStyle(QFrame.HLine | QFrame.Plain)
         return frm

      if hasPriv:           optLayout.addWidget(lbtnSendBtc)
      if True:              optLayout.addWidget(lbtnGenAddr)
      if hasPriv:           optLayout.addWidget(lbtnChangeCrypto)
      if True:              optLayout.addWidget(lbtnChangeLabels)

      if True:              optLayout.addWidget(createVBoxSeparator())

      if hasPriv:           optLayout.addWidget(lbtnMkPaper)
      if True:              optLayout.addWidget(lbtnExport)
      if hasPriv and adv:   optLayout.addWidget(lbtnForkWlt)
      if True:              optLayout.addWidget(lbtnRemove)

      if hasPriv and adv:  optLayout.addWidget(createVBoxSeparator())

      if hasPriv and adv:   optLayout.addWidget(lbtnImportA)
      if hasPriv and adv:   optLayout.addWidget(lbtnDeleteA)
      if hasPriv and adv:   optLayout.addWidget(lbtnSweepA)

      optLayout.addStretch()
      optFrame.setLayout(optLayout)


      btnGoBack = QPushButton('<<< Go Back')
      self.connect(btnGoBack, SIGNAL('clicked()'), self.accept)

      self.frm = QFrame()
      self.setWltDetailsFrame()

      lblTotal  = QLabel(); lblTotal.setAlignment( Qt.AlignRight | Qt.AlignVCenter)
      lblUnconf = QLabel(); lblUnconf.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      totFund, unconfFund = 0,0
      for le in self.wlt.getTxLedger():
         if (self.main.latestBlockNum-le.getBlockNum()+1) < 6:
            unconfFund += le.getValue()
         else:
            totFund += le.getValue()
      uncolor = 'red' if unconfFund>0 else 'black'
      lblTotal.setText( \
         '<b>Total Funds: <font color="green">%s</font> BTC</b>' % coin2str(totFund))
      lblUnconf.setText( \
         '<b>Unconfirmed: <font color="%s"   >%s</font> BTC</b>' % (uncolor,coin2str(unconfFund)))

      layout = QGridLayout()
      layout.addWidget(self.frm,              0, 0, 3, 4)
      layout.addWidget(self.wltAddrView,      4, 0, 2, 4)
      layout.addWidget(btnGoBack,             6, 0, 2, 1)
      layout.addWidget(lblTotal,              6, 3, 1, 1)
      layout.addWidget(lblUnconf,             7, 3, 1, 1)

      layout.addWidget(QLabel("Available Actions:"), \
                                              0, 4)
      layout.addWidget(optFrame,              1, 4, 8, 2)
      self.setLayout(layout)

      self.setWindowTitle('Wallet Details')

      

   #############################################################################
   def dblClickAddressView(self, index):
      model = index.model()
      if index.column()==ADDRESSCOLS.Comment:
         self.main.updateAddressCommentFromView(self.wltAddrView, self.wlt)
      else:
         dlg = DlgAddressInfo(wlt, addr, self, self.main)
         dlg.exec_()
         #currComment = str(view.model().index(row, ADDRESSCOLS.Comment).data().toString())


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
         unlockdlg = DlgUnlockWallet(self.wlt, self, self.main)
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
         dlg = DlgRemoveAddress(self.wlt, addr160,  self)
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
      savePath = self.main.getFileSave()
      if len(savePath)>0:
         self.wlt.writeFreshWalletFile(savePath)
         self.main.statusBar
         self.main.statusBar().showMessage( \
            'Successfully copied wallet to ' + savePath, 10000)
      
      
   def forkOnlineWallet(self):
      saveLoc = self.main.getFileSave('Save Watching-Only Copy')
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
         if self.main.getWltExtraProp(self.wltID, 'IsMine'):
            self.labelValues[WLTFIELDS.BelongsTo] = QLabelButton('You own this wallet')
         else:
            owner = self.main.getWltExtraProp(self.wltID, 'BelongsTo')
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
            w,h = tightSizeStr(lbl, '9'*14)
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
      self.frm.setFrameStyle(QFrame.Box|QFrame.Sunken)
      self.frm.setLayout(layout)
      
      

   def execSetOwner(self):
      dlg = self.dlgChangeOwner(self.wltID, self) 
      if dlg.exec_():
         if dlg.chkIsMine.isChecked():
            self.main.setWltExtraProp(self.wltID, 'IsMine', True)
            self.main.setWltExtraProp(self.wltID, 'BelongsTo', '')
            self.labelValues[WLTFIELDS.BelongsTo].setText('You own this wallet')
            self.labelValues[WLTFIELDS.Secure].setText('<i>Offline</i>')
         else:
            owner = str(dlg.edtOwnerString.text())  
            self.main.setWltExtraProp(self.wltID, 'IsMine', False)
            self.main.setWltExtraProp(self.wltID, 'BelongsTo', owner)
               
            if len(owner)>0:
               self.labelValues[WLTFIELDS.BelongsTo].setText(owner)
            else:
               self.labelValues[WLTFIELDS.BelongsTo].setText('Someone else')
            self.labelValues[WLTFIELDS.Secure].setText('<i>Watching-only</i>')
         


   class dlgChangeOwner(QDialog):
      def __init__(self, wltID, parent=None, main=None):
         super(parent.dlgChangeOwner, self).__init__(parent)

         layout = QGridLayout()
         self.chkIsMine = QCheckBox('This wallet is mine')
         self.edtOwnerString = QLineEdit() 
         if parent.main.getWltExtraProp(wltID, 'IsMine'):
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
            owner = parent.main.getWltExtraProp(wltID, 'BelongsTo')
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
      if notMyWallet:
         dnaaThisWallet = self.main.getWltExtraProp(wlt.uniqueIDB58, 'DnaaRecv')
         if not dnaaThisWallet:
            result = MsgBoxWithDNAA(MSGBOX.Warning, 'This is not your wallet!', \
                  'You are getting an address for a wallet that '
                  'does not appear to belong to you.  Any money sent to this '
                  'address will not appear in your total balance, and cannot '
                  'be spent from this computer.\n\n'
                  'If this is actually your wallet (perhaps you maintain the full '
                  'wallet on a separate computer), then please change the '
                  '"Belongs To" field in the wallet-properties for this wallet.', \
                  'Do not show this warning again', wCancel=True)
            self.main.settings.set('DnaaRecv', result[1])
            if result[0]==False:
               return

      if offlineWallet:
         dnaaThisWallet = self.main.getWltExtraProp(wlt.uniqueIDB58, 'DnaaRecv')
         if not dnaaThisWallet:
            result = MsgBoxWithDNAA(MSGBOX.Warning, 'This is not your wallet!', \
                  'You are getting an address for a wallet that '
                  'you have specified belongs to you, but you cannot actually '
                  'spend the funds from this computer.  This is usually the case when '
                  'you keep the full wallet on a separate computer for security '
                  'purposes.\n\n'
                  'If this does not sound right, then please do not use the following '
                  'address.  Instead, change the wallet properties "Belongs To" field '
                  'to specify that this wallet is not actually yours.', \
                  'Do not show this warning again', wCancel=True)
            self.main.settings.set('DnaaRecv', result[1])
            if result[0]==False:
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
      frmNewAddr.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
      frmNewAddrLayout = QGridLayout()
      frmNewAddrLayout.addWidget(lblDescr,        0,0, 1,2)
      frmNewAddrLayout.addWidget(self.edtNewAddr, 1,0, 1,1)
      frmNewAddrLayout.addWidget(tooltip1,        1,1, 1,1)

      if not notMyWallet:
         palette = QPalette()
         palette.setColor( QPalette.Base, Colors.LightBlue )
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
      frmComment.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
      frmCommentLayout = QGridLayout()
      frmCommentLayout.addWidget(lblCommDescr,    0,0, 1,2)
      #frmCommentLayout.addWidget(lblComm,         1,0, 1,1)
      frmCommentLayout.addWidget(self.edtComm,    1,0, 2,2)
      frmComment.setLayout(frmCommentLayout)

      
      lblRecvWlt = QLabel( \
            'Money sent to this address will appear in the following wallet:')
      
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
      frmWlt.setFrameShape(QFrame.StyledPanel | QFrame.Raised)
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
      self.main=parent
      lblWarn = QLabel( 'Armory supports importing of external '
            'addresses into your wallet, including encryption, '
            'but imported addresses <b>cannot</b> be protected/saved '
            'by a paper backups.  Watching-only wallets will include '
            'imported addresses if the watching-only wallet was '
            'created after the address was imported.')
      lblWarn.setTextFormat(Qt.RichText)
      lblWarn.setWordWrap(True)

      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap('img/MsgBox_warning64.png'))
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

      #if self.main.usermode in (USERMODE.Advanced, USERMODE.Developer):
         #descrText += ('Supported formats are any hexadecimal or Base58 '
                       #'representation of a 32-byte private key (with or '
                       #'without checksums), and mini-private-key format '
                       #'used on Casascius physical bitcoins.')
      privTooltip = createToolTipObject( \
                       'Supported formats are any hexadecimal or Base58 '
                       'representation of a 32-byte private key (with or '
                       'without checksums), and mini-private-key format '
                       'used on Casascius physical bitcoins.')
         
      lblDescr = QLabel(descrText)
      lblDescr.setWordWrap(True)



      ## Import option
      self.radioSweep  = QRadioButton('Sweep any funds owned by this address '
                                      'into your wallet\n'
                                      'Select this option if someone else gave you this key')
      self.radioImport = QRadioButton('Import this address to your wallet\n'
                                      'Only select this option if you are positive '
                                      'that no one else has access to this key')

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
      self.radioSweep.setChecked(True)


      #lblWarn = QLabel( \
            #'<font color="red"><b>Warning</b></font>: Do not import private '
            #'keys/addresses <b>unless '
            #'you know for sure that you are the only person who has access '
            #'to it</b>.  If you received this key from another party, that party '
            #'will be able to spend any Bitcoins it currently holds, and future '
            #'Bitcoins sent to it.')
      #lblWarn.setWordWrap(True)
      #lblWarn.setTextFormat(Qt.RichText)

      frmWarn = QFrame()
      frmWarn.setFrameStyle(QFrame.Box|QFrame.Plain)
      frmWarnLayout = QGridLayout()
      #frmWarnLayout.addWidget(lblWarn,         0,0, 1,1)
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
      theStr = str(self.edtPrivData.text()).strip()
      hexChars = '01234567890abcdef'
      b58Chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

      hexCount = sum([1 if c in hexChars else 0 for c in theStr])
      b58Count = sum([1 if c in b58Chars else 0 for c in theStr])
      canBeHex = hexCount==len(theStr)
      canBeB58 = b58Count==len(theStr)

      binEntry = ''
      miniKey = False
      if canBeB58 and not canBeHex:
         if len(theStr)==22 or len(theStr)==30:
            # Mini-private key format!
            try:
               binEntry = decodeMiniPrivateKey(theStr)
            except KeyDataError:
               reply = QMessageBox.critical(self, 'Invalid Key', \
                  'It appears that you tried to enter a mini-private-key,' 
                  'but it is not a valid key.  Please check the entry '
                  'for errors.', \
                  QMessageBox.Ok)
               return
            miniKey = True
         else:
            binEntry = base58_to_binary(theStr)

      if canBeHex:  
         binEntry = hex_to_binary(theStr)

      if len(binEntry)==36 or (len(binEntry)==37 and binEntry[0]==0x80):
         if len(theStr)==36:
            keydata = hex_to_binary(theStr[:64 ])
            chk     = hex_to_binary(theStr[ 64:])
            binEntry = verifyChecksum(keydata, chk)
         else:
            # Assume leading 0x80 byte, and 4 byte checksum
            keydata = hex_to_binary(theStr[1:1+64 ])
            chk     = hex_to_binary(theStr[  1+64:])
            binEntry = verifyChecksum(keydata, chk)

         if binEntry=='':
            QMessageBox.warning(self, 'Entry Error',
               'The private key data you supplied appears to '
               'contain a consistency check.  This consistency '
               'check failed.  Please verify you entered the '
               'key data correctly.', QMessageBox.Ok)
            return

      binKeyData, addr160, addrStr = '','',''
      # Regardless of format, if this is a valid key, it should be 32 bytes
      if len(binEntry)==32:
         # Support raw private keys
         binKeyData = binEntry
         addr160 = convertKeyDataToAddress(privKey=binKeyData)
         addrStr = hash160_to_addrStr(addr160)

         if not miniKey:
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

      if binKeyData=='':
         reply = QMessageBox.critical(self, 'Invalid Key Format', \
               'The data you supplied is not a recognized format '
               'for private key data.', \
               QMessageBox.Ok)
         return

      # Finally, let's add the address to the wallet, or sweep the funds
      if self.radioSweep.isChecked():
         pass # TODO: add the tx-construct-broadcast method here
      elif self.radioImport.isChecked():
         if self.wlt.useEncryption and self.wlt.isLocked:
            dlg = DlgUnlockWallet(wlt, self.main)
            if not dlg.exec_():
               reply = QMessageBox.critical(self, 'Wallet is locked',
                  'New private key data cannot be imported unless the wallet is '
                  'unlocked.  Please try again when you have the passphrase.',\
                  QMessageBox.Ok)

         self.wlt.importExternalAddressData( privKey=binKeyData)
         self.main.statusBar().showMessage( 'Successful import of address ' \
                                 + addrStr + ' into wallet ' + self.wlt.uniqueIDB58, 10000)
      
      self.main.wltAddrModel.reset()
      if TheBDM.isInitialized():
         self.wlt.syncWithBlockchain()

      self.main.walletListChanged()
      self.accept()


#############################################################################
class DlgImportWallet(QDialog):
   def __init__(self, parent=None, main=None):
      super(DlgImportWallet, self).__init__(parent)
      self.setAttribute(Qt.WA_DeleteOnClose)
      self.parent = parent
      self.main   = main

      lblImportDescr = QLabel('Chose the wallet import source:')
      self.btnImportFile  = QPushButton("Import from &file")
      self.btnImportPaper = QPushButton("Import from &paper backup")

      self.btnImportFile.setMinimumWidth(300)

      self.connect( self.btnImportFile, SIGNAL("clicked()"), \
                    self.getImportWltPath)

      self.connect( self.btnImportPaper, SIGNAL('clicked()'), \
                    self.acceptPaper)

      ttip1 = createToolTipObject('Import an existing Armory wallet, usually with a '
                                  '*.wallet extension.  Any wallet that you import will ' 
                                  'be copied into your settings directory, and maintained '
                                  'there.  The original wallet file will not be touched.')

      ttip2 = createToolTipObject('If you have previously made a paper backup of '
                                  'a wallet, you can manually enter the wallet '
                                  'data into Armory to recover the wallet.')


      w,h = relaxedSizeStr(ttip1, '(?)') 
      for ttip in (ttip1, ttip2):
         ttip.setMaximumSize(w,h)
         ttip.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

      # Set up the layout
      layout = QGridLayout()
      layout.addWidget(lblImportDescr,      0,0, 1, 2)
      layout.addWidget(self.btnImportFile,  1,0, 1, 2); layout.addWidget(ttip1, 1,2,1,1)
      layout.addWidget(self.btnImportPaper, 2,0, 1, 2); layout.addWidget(ttip2, 2,2,1,1)

      if self.main.usermode in (USERMODE.Advanced, USERMODE.Developer):
         lbl = QLabel('You can manually add wallets to armory by copying them '
                      'into your application directory:  ' + ARMORY_HOME_DIR)
         lbl.setWordWrap(True)
         layout.addWidget(lbl, 3,0, 1, 2); 
         if self.main.usermode==USERMODE.Developer:
            lbl = QLabel('Any files in the application data directory above are '
                         'used in the application if the first 8 bytes of the file '
                         'are "\\xbaWALLET\\x00".  Wallets in this directory can be '
                         'ignored by adding an <i>Excluded_Wallets</i> option to the '
                         'ArmorySettings.txt file.  Reference by full path or wallet ID.')
            lbl.setWordWrap(True)
            layout.addWidget(lbl, 4,0, 1, 2); 

      btnCancel = QPushButton('Cancel')
      self.connect(btnCancel, SIGNAL('clicked()'), self.reject)
      layout.addWidget(btnCancel, 5,0, 1,1);

      self.setLayout(layout)
      self.setWindowTitle('Import Wallet')
      

   def getImportWltPath(self):
      self.importFile = self.main.getFileLoad('Import Wallet File')
      if self.importFile:
         print 'Importing:', self.importFile
         self.importType_file = True
         self.importType_paper = False
         self.accept()

      
   def acceptPaper(self):
      """
      We will accept this dialog but signal to the caller that paper-import
      was selected so that it can open the dialog for itself
      """
      self.importType_file = False
      self.importType_paper = True
      self.accept()
      

class DlgAddressInfo(QDialog):
   def __init__(self, wlt, addr160, parent=None, main=None):
      super(DlgAddressInfo, self).__init__(parent)

      
      self.setLayout(layout)
      self.setWindowTitle('Address Info - ' + hash160_to_addrStr(addr160))


#############################################################################
class DlgImportPaperWallet(QDialog):

   wltDataLines = [[]]*4
   prevChars    = ['']*4

   def __init__(self, parent=None, main=None):
      super(DlgImportPaperWallet, self).__init__(parent)

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
         rawStr = easyType16_to_binary( str(self.lineEdits[i].text()).replace(' ','') )
         data, chk = rawStr[:16], rawStr[16:]
         fixedData = verifyChecksum(data, chk)
         if len(fixedData)==0:
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

      self.setWindowTitle('Add or Change Comment')
      self.setWindowIcon(QIcon('img/armory_logo_32x32.png'))

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
#BASE16CHARS  = 'abcd eghj knrs uwxy'.replace(' ','')
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
   def __init__(self, text, position, scene, font=QFont('Courier', 8), lineWidth=None):
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
         
      print 'QR-generated?', success, ' : Size of QRcode is', sz, \
                           ' : boxCount =', self.qr.getModuleCount()


   def boundingRect(self):
      return self.Rect

   def paint(self, painter, option, widget=None):
      painter.setPen(Qt.NoPen)
      painter.setBrush(QBrush(QColor(Colors.Black)))

      print self.Rect.height(), self.modCt, self.modSz
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
         bal = wlt.getBalance()
         lbls.append([])
         lbls[3].append(QLabel('Current Balance:'))
         if bal>0:
            lbls[3].append(QLabel('<font color="red"><b>'+coin2str(bal, maxZeros=1)+' BTC</b></font>'))
            lbls[3][-1].setTextFormat(Qt.RichText)
            wltEmpty = False
         else:
            lbls[3].append(QLabel(coin2str(bal, maxZeros=1) + ' BTC'))


      # Add two WARNING images on either side of dialog
      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap('img/MsgBox_warning64.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnImg2 = QLabel()
      lblWarnImg2.setPixmap(QPixmap('img/MsgBox_warning64.png'))
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
         lbl = QLabel('<b>WALLET IS NOT EMPTY.  Only delete this wallet if you '
                      'have a backup on paper or saved to a another location '
                      'outside your settings directory.</b>')
         lbl.setTextFormat(Qt.RichText)
         lbl.setWordWrap(True)
         lbls.append(lbl)
         layout.addWidget(lbl, 4, 0, 1, 3)

      self.radioExclude = QRadioButton('Add this wallet to the "ignore list"')
      self.radioDelete  = QRadioButton('Permanently delete this wallet')
      self.radioWatch   = QRadioButton('Delete private keys only, make watching-only')

      # Make sure that there can only be one selection
      btngrp = QButtonGroup(self)
      btngrp.addButton(self.radioExclude)
      btngrp.addButton(self.radioDelete)
      btngrp.addButton(self.radioWatch)
      btngrp.setExclusive(True)

      ttipExclude = createToolTipObject( \
                              'This will not delete any files, but will add this '
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

      if wlt.watchingOnly:
         ttipDelete = createToolTipObject('This will delete the wallet file from your system.  '
                                 'Since this is a watching-only wallet, no private keys '
                                 'will be deleted.')
         
      #for lbl in (lblDeleteDescr, lblExcludeDescr, lblWatchDescr):
         #lbl.setWordWrap(True)
         #lbl.setMaximumWidth( tightSizeNChar(self, 50)[0] )

      self.chkPrintBackup = QCheckBox('Print a paper backup of this wallet before deleting')

      self.frm = []

      rdoFrm = QFrame()
      rdoFrm.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
      rdoLayout = QGridLayout()
      
      startRow = 0
      for rdo,ttip in [(self.radioExclude, ttipExclude), \
                       (self.radioDelete,  ttipDelete), \
                       (self.radioWatch,   ttipWatch)]:
         self.frm.append(QFrame())
         #self.frm[-1].setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
         self.frm[-1].setFrameStyle(QFrame.NoFrame)
         frmLayout = QHBoxLayout()
         frmLayout.addWidget(rdo)
         ttip.setAlignment(Qt.AlignLeft | Qt.AlignVCenter) 
         frmLayout.addWidget(ttip)
         frmLayout.addStretch()
         self.frm[-1].setLayout(frmLayout)
         rdoLayout.addWidget(self.frm[-1], startRow, 0, 1, 3)
         startRow +=1 


      self.radioExclude.setChecked(True)
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
      printFrm = makeLayoutStrip('Horiz', [self.chkPrintBackup, printTtip, 'Stretch'])
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
                     'Wallet '+wltID+' was replaced with a watching-only wallet.', 10000)
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
      self.wlt  = wlt
      self.addr = wlt.addrMap[addr160]
      self.comm = wlt.getCommentForAddress(addr160)

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
         bal = wlt.cppWallet.getAddrByHash160(addr160).getBalance()
         lbls.append([])
         lbls[-1].append(QLabel('Address Balance:'))
         if bal>0:
            lbls[-1].append(QLabel('<font color="red"><b>'+coin2str(bal, maxZeros=1)+' BTC</b></font>'))
            lbls[-1][-1].setTextFormat(Qt.RichText)
            addrEmpty = False
         else:
            lbls[3].append(QLabel(coin2str(bal, maxZeros=1) + ' BTC'))


      # Add two WARNING images on either side of dialog
      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap('img/MsgBox_warning64.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnImg2 = QLabel()
      lblWarnImg2.setPixmap(QPixmap('img/MsgBox_warning64.png'))
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
      if self.chkPrintBackup.isChecked():      
         dlg = DlgPaperBackup(wlt, self, self.main)
         if not dlg.exec_():
            return
            
            
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
         self.main.wltAddrModel.reset()
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
      lbls.append( QLabel("Current Balance:"))

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
      frm.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
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
      
      bal = wlt.getBalance()
      if bal==0:
         self.dispBal.setText('<font color="red"><b>0.0</b></font>')
      else:
         self.dispBal.setText('<b>'+coin2str(wlt.getBalance(), maxZeros=1)+'</b>')
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
   lbls.append( QLabel("Current Balance:"))

   for i in range(len(lbls)):
      lbls[i].setAlignment(Qt.AlignLeft | Qt.AlignTop)
      lbls[i].setTextFormat(Qt.RichText)
      lbls[i].setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
      lbls[i].setText('<b>'+str(lbls[i].text())+'</b>')

   dispID = QLabel(wltID)
   dispName = QLabel(wlt.labelName)
   dispDescr = QLabel(wlt.labelDescr)
   dispBal = QLabel()

   # Format balance if necessary
   bal = wlt.getBalance()
   dispBal.setTextFormat(Qt.RichText) 
   if bal==0: dispBal.setText('<font color="red"><b>0.0000</b></font>')
   else:      dispBal.setText('<b>'+coin2str(wlt.getBalance(), maxZeros=1)+'</b>')

   dispBal.setTextFormat(Qt.RichText)
   dispDescr.setWordWrap(True)
      

   frm = QFrame()
   frm.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
   frmLayout = QGridLayout()
   for i in range(len(lbls)):
      frmLayout.addWidget(lbls[i], i, 0,  1, 1)

   dispID.setAlignment(Qt.AlignLeft | Qt.AlignTop)
   dispName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
   dispDescr.setAlignment(Qt.AlignLeft | Qt.AlignTop)
   dispBal.setAlignment(Qt.AlignLeft | Qt.AlignTop)
   dispDescr.setMinimumWidth( tightSizeNChar(dispDescr, 40)[0])
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
   FontVar = QFont('Times',   10)
   FontFix = QFont('Courier', 10)

   def __init__(self, wlt, recipValPairs, fee, parent=None, main=None):
      super(DlgConfirmSend, self).__init__(parent)
      
      self.parent = parent
      self.main   = main
      self.wlt    = wlt

      layout = QGridLayout()


      lblInfoImg = QLabel()
      lblInfoImg.setPixmap(QPixmap('img/MsgBox_info32.png'))
      lblInfoImg.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

      totalSend = sum([rv[1] for rv in recipValPairs]) + fee
      sumStr = coin2str(totalSend, maxZeros=1)

      lblMsg = QRichLabel(
         'You are about to spend <b>%s BTC</b> from wallet "<b>%s</b>" (%s).  You '
         'specified the following distribution:' % (sumStr, wlt.labelName, wlt.uniqueIDB58))


      recipLbls = []
      ffixBold = self.FontFix
      ffixBold.setWeight(QFont.Bold)
      for rv in recipValPairs:
         recipLbls.append(QLabel( hash160_to_addrStr(rv[0]) + ' : '  +
                                  coin2str(rv[1], rJust=True, maxZeros=4)))
         recipLbls[-1].setFont(ffixBold)


      if fee>0:
         recipLbls.append(QSpacerItem(10,10))
         recipLbls.append(QLabel( 'Transaction Fee : '.ljust(37)  +
                           coin2str(fee, rJust=True, maxZeros=4)))
         recipLbls[-1].setFont(self.FontFix)

      hline = QFrame()
      hline.setFrameStyle(QFrame.HLine | QFrame.Sunken)
      recipLbls.append(hline)
      recipLbls.append(QLabel( 'Total Bitcoins : '.ljust(37)  +
                        coin2str(totalSend, rJust=True, maxZeros=4)))
      recipLbls[-1].setFont(self.FontFix)

      self.btnAccept = QPushButton("Send")
      self.btnCancel = QPushButton("Cancel")
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.accept)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      
      layout.addWidget(lblInfoImg,           0, 0,   1, 1)
      layout.addWidget(lblMsg,               0, 1,   1, 1)

      lblFrm = makeLayoutStrip('Vert', recipLbls, QFrame.StyledPanel|QFrame.Raised)
      layout.addWidget(lblFrm,               1, 1,   1, 1)

      r = len(recipLbls)+1
      layout.addWidget(QLabel('Are you sure you want to execute this transaction?'), 2, 1,  1, 1)
      layout.addWidget(buttonBox,            3, 1,  1, 1)
      layout.setSpacing(20)

      self.setLayout(layout)
      self.setMinimumWidth(350)
      self.setWindowTitle('Confirm Transaction')
      



class DlgSendBitcoins(QDialog):
   COLS = enum('LblAddr','Addr','LblBtc','Btc','LblComm','Comm')
   FontVar = QFont('Times',   10)
   FontFix = QFont('Courier', 10)

   def __init__(self, wlt, parent=None, main=None):
      super(DlgSendBitcoins, self).__init__(parent)
      self.maxHeight = tightSizeNChar(self.FontVar, 1)[1]+8

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
         

      lblSend = QRichLabel('<b>Sending from Wallet:</b>')
      lblSend.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
      self.frmInfo = getWalletInfoFrame(wlt)
      layout.addWidget(lblSend,       0, 0, 1, 1)
      layout.addWidget(self.frmInfo,  1, 0, 1, 1)

      lbtnTxFeeOpt = QLabelButton('More Info')
      self.connect(lbtnTxFeeOpt, SIGNAL('clicked()'), self.txFeeOptions)
      feetip = createToolTipObject( \
            'Transaction fees go to other users who contribute computing power to '
            'keep the Bitcoin network secure, and guarantees that your transaciton '
            'is processed quickly.   <b>Most transactions '
            'do not require</b> a fee but it is recommended to include one anyway '
            'since it guarantees quick processing for less than $0.01 USD.  '  
            'You will will be prompted if a higher fee is '
            'recommended than specified here.')

      self.edtFeeAmt = QLineEdit()
      self.edtFeeAmt.setFont(self.FontFix)
      self.edtFeeAmt.setMaximumWidth(tightSizeNChar(self.edtFeeAmt, 12)[0])
      self.edtFeeAmt.setMaximumHeight(self.maxHeight)
      self.edtFeeAmt.setAlignment(Qt.AlignRight)
      self.edtFeeAmt.setText(coin2str(MIN_TX_FEE, ndec=4))

      spacer = QSpacerItem(20, 1)

      layout.addWidget(lblRecip,                   0, 1, 1, 5)
      layout.addWidget(self.scrollRecipArea,       1, 1, 4, 5)


      btnSend = QPushButton('Send!')
      self.connect(btnSend, SIGNAL('clicked()'), self.createTxAndBroadcast)
      if wlt.watchingOnly:
         btnSend.setEnabled(False)

      txFrm = makeLayoutStrip('Horiz', [QLabel('Transaction Fee:'), \
                                       self.edtFeeAmt, \
                                       feetip, \
                                       spacer, \
                                       lbtnTxFeeOpt, \
                                       'stretch', \
                                       btnSend])
      layout.addWidget(txFrm, 5,1, 1,5)

      

      
      btnFrame = QFrame()
      btnFrameLayout = QGridLayout()
      if wlt.watchingOnly:
         ttip = createToolTipObject(\
            'You do not have the ability to sign this transaction '
            'from this computer.  Press this button to see options '
            'for obtaining the appropriate signatures.')
            
         btn = QPushButton('Create Unsigned Transaction')
         self.connect(btn, SIGNAL('clicked()'), self.createTxDPAndDisplay)
         btnFrameLayout.addWidget(btn,  0,0, 1,1)
         btnFrameLayout.addWidget(ttip, 0,1, 1,1)
         
      btnDonate = QPushButton("Add Donation")
      ttipDonate = createToolTipObject( \
         'Making this software was a lot of work.  You can give back '
         'by adding a small donation to the developers of Armory.  '
         'Default donation is 0.5 BTC, but you can change '
         'the amount before executing the transaction.')
      self.connect(btnDonate, SIGNAL("clicked()"), self.addDonation)
      btnFrameLayout.addWidget(btnDonate,    1,0, 1,1)
      btnFrameLayout.addWidget(ttipDonate,   1,1, 1,1)
      btnFrame.setLayout(btnFrameLayout)

      layout.addWidget(btnFrame,   2,0, 1,1)
      self.setLayout(layout)
      self.makeRecipFrame(1)
      self.setWindowTitle('Send Bitcoins')
      self.setMinimumHeight(self.maxHeight*20)


   #############################################################################
   def createTxDPAndDisplay(self):
      txdp = self.validateInputsGetTxDP()



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
               unlockdlg = DlgUnlockWallet(self.wlt, self, self.main)
               if not unlockdlg.exec_():
                  QMessageBox.critical(self, 'Wallet is Locked', \
                     'Cannot sign transaction while your wallet is locked. ', \
                     QMessageBox.Ok)
                  return
              
            
            print self.origRVPairs
            print self.comments
            commentStr = ''
            if len(self.comments)==1:
               commentStr = self.comments[0]
            else:
               for i in range(len(self.comments)):
                  amt = self.origRVPairs[i][1]
                  if len(self.comments[i].strip())>0:
                     commentStr += '%s (%s);  ' % (self.comments[i], coin2str_approx(amt).strip())
            
            print commentStr

            txdp = self.wlt.signTxDistProposal(txdp)
            finalTx = txdp.prepareFinalTx()
            finalTx.pprint()
            if len(commentStr)>0:
               self.wlt.setComment(finalTx.getHash(), commentStr)
            print self.wlt.commentsMap
            print '\n\n'
            print binary_to_hex(finalTx.serialize())
            print txdp.serializeAscii()
            print 'Sending Tx,', binary_to_hex(finalTx.getHash())
            self.main.NetworkingFactory.sendTx(finalTx)
            # TODO:  MAKE SURE THE TX WAS ACCEPTED?
            self.main.NetworkingFactory.addTxToMemoryPool(finalTx)
            self.wlt.lockTxOutsOnNewTx(finalTx.copy())
            self.main.NetworkingFactory.saveMemoryPool()
            print 'Done!'
            self.accept()
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
            addrType.append(-1)

 
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

         
      bal = self.wlt.getBalance()
      if totalSend+fee > bal:
         QMessageBox.critical(self, 'Insufficient Funds', 'You just tried to send '
            '%s BTC, but you only have %s BTC in this wallet!' % \
               (coin2str(totalSend, maxZeros=2).strip(), \
                coin2str(bal, maxZeros=2).strip()), \
            QMessageBox.Ok)
         return False
      

      # Get unspent outs for this wallet:
      utxoList = self.wlt.getUnspentTxOutList()
      utxoSelect = PySelectCoins(utxoList, totalSend, fee)



      # TODO:  I should use a while loop/iteration to make sure that the fee
      #        change does (extremely unlikely) induce another, higher fee
      #        that should have been the actual fee to be used.  However,
      #        the extremely rare situations where this would happen, I think 
      #        it will be okay to send a slightly sub-optimal fee.  I'll add 
      #        this to my TODO list.
      minFeeRec = calcMinSuggestedFees(utxoSelect, totalSend, fee)
      if fee<minFeeRec[1]:
         extraMsg = ''
         feeStr = coin2str(fee, maxZeros=0).strip()
         minRecStr = coin2str(minFeeRec[1], maxZeros=0).strip()
         if self.main.usermode in (USERMODE.Advanced, USERMODE.Developer):
            extraMsg = ('\n\n(It is not recommended to override this behavior, '
                        'but as an advanced user, you can go into the settings file '
                        'and manually change the "OverrideMinFee" property to '
                        '"True".  Do so at your own risk, as many transactions '
                        'have been known to "get stuck" when insufficient fee '
                        'was included)')
         allowOkay = self.main.settings.getSettingOrSetDefault('OverrideMinFee', False)
         reply = QMessageBox.warning(self, 'Insufficient Fee', \
            'The fee you have specified (%s BTC) is insufficient for the size '
            'and priority of your transaction.  You must include at least '
            '%s BTC to send this transaction.  \n\nDo you agree to the fee of %s BTC?  ' % \
            (feeStr, minRecStr, minRecStr) + extraMsg,  QMessageBox.Yes | QMessageBox.No)
         if reply == QMessageBox.No:
            return False

         fee = long(minFeeRec[1])
         utxoSelect = PySelectCoins(utxoSelect, totalSend, fee)
      
      if len(utxoSelect)==0:
         QMessageBox.critical(self, 'Coin Selection Error', \
            'SelectCoins returned a list of size zero.  This is problematic '
            'and probably not your fault.', QMessageBox.Ok)
         

      ### IF we got here, everything should be good to go... generate a new
      #   address, calculate the change (add to recip list) and do our thing.
      totalTxSelect = sum([u.getValue() for u in utxoSelect])
      totalChange = totalTxSelect - (totalSend + fee)

      self.origRVPairs = list(recipValuePairs)
      recipValuePairs.append( [self.wlt.getNextUnusedAddress().getAddr160(), totalChange])
   
      # Anonymize the outputs
      random.shuffle(recipValuePairs)
      txdp = PyTxDistProposal().createFromTxOutSelection( utxoSelect, \
                                                          recipValuePairs)

      self.txValues = [totalSend, fee, totalChange]
      return txdp

      
            
   #############################################################################
   def addDonation(self):
      COLS = self.COLS
      lastIsEmpty = True
      for col in (COLS.Addr, COLS.Btc, COLS.Comm):
         if len(str(self.widgetTable[-1][col].text()))>0:
            lastIsEmpty = False
         
      if not lastIsEmpty or len(self.widgetTable)==1:
         self.makeRecipFrame( len(self.widgetTable)+1 )

      self.widgetTable[-1][self.COLS.Addr].setText(ARMORY_DONATION_ADDR)
      self.widgetTable[-1][self.COLS.Btc].setText('1.00')
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
         self.widgetTable[-1][-1].setMinimumWidth(relaxedSizeNChar(self.FontVar, 45)[0])
         self.widgetTable[-1][-1].setMaximumHeight(self.maxHeight)
         self.widgetTable[-1][-1].setFont(self.FontVar)

         self.widgetTable[-1].append( QLabel('BTC:') )

         self.widgetTable[-1].append( QLineEdit() )
         self.widgetTable[-1][-1].setFont(self.FontFix)
         self.widgetTable[-1][-1].setMaximumWidth(tightSizeNChar(self.FontFix, 16)[0])
         self.widgetTable[-1][-1].setMaximumHeight(self.maxHeight)
         self.widgetTable[-1][-1].setAlignment(Qt.AlignRight)
      
         self.widgetTable[-1].append( QLabel('Comment:') )

         self.widgetTable[-1].append( QLineEdit() )
         self.widgetTable[-1][-1].setFont(self.FontVar)
         self.widgetTable[-1][-1].setMaximumHeight(self.maxHeight)

         if i<nRecip and i<prevNRecip:
            self.widgetTable[-1][COLS.Addr].setText( inputs[i][0] )
            self.widgetTable[-1][COLS.Btc ].setText( inputs[i][1] )
            self.widgetTable[-1][COLS.Comm].setText( inputs[i][2] )

         subfrm = QFrame()
         subfrm.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
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


################################################################################
class DlgTxFeeOptions(QDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgTxFeeOptions, self).__init__(parent)

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

   


def extractTxInfo(pytx, zcTimeList=None):
   txHash    = pytx.getHash()
   txHashHex = binary_to_hex(txHash)
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
  

   if TheBDM.isInitialized(): 
      txref = TheBDM.getTxByHash(txHash)
      if txref:
         headref = txref.getHeaderPtr()
         txTime  = headref.getTimestamp()
         txBlk   = headref.getBlockHeight()
         txIdx   = txref.getBlockTxIndex()
      else:
         if zcTimeList and zcTimeList.has_key(txHash):
            txTime = zcTimeList[txHash]
            txBlk  = 2**32-1

         
      txinFromList = []
      haveAllInput=True
      for i in range(txref.getNumTxIn()):
         # Use BDM to get all the info about the TxOut being spent
         # Recip, value, block-that-incl-tx, tx-that-incl-txout, txOut-index
         txinFromList.append([])
         cppTxin = txref.getTxInRef(i)
         prevTxHash = cppTxin.getOutPoint().getTxHash()
         if TheBDM.getTxByHash(prevTxHash):
            prevTxOut = TheBDM.getPrevTxOut(cppTxin)
            txinFromList[-1].append(TheBDM.getSenderAddr20(cppTxin))
            txinFromList[-1].append(TheBDM.getSentValue(cppTxin))
            txinFromList[-1].append(prevTxOut.getParentTxPtr().getHeaderPtr().getBlockHeight())
            txinFromList[-1].append(prevTxOut.getParentTxPtr().getThisHash())
            txinFromList[-1].append(prevTxOut.getIndex())
         else:
            haveAllInput=False
            txinFromList[-1].append('')
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
   def __init__(self, pytx, wlt=None, parent=None, main=None, mode=None):
      """
      This got freakin' complicated, because I'm trying to handle
      wallet/nowallet, BDM/noBDM and Std/Adv/Dev modes all at once. 

      We can override the user mode as an input argument, in case a std
      user decides they want to see the tx in adv/dev mode
      """
      super(DlgDispTxInfo, self).__init__(parent)
      self.parent = parent
      self.main   = main  

      if mode==None:
         mode = self.main.usermode

      FIELDS = enum('Hash','OutList','SumOut','InList','SumIn', 'Time', 'Blk', 'Idx')
      data = extractTxInfo(pytx, self.main.NetworkingFactory.zeroConfTxTime)
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
      if haveBDM and haveWallet:
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
                  txAmt, changeIndex = self.main.determineSentToSelfAmt(le, wlt)
                  rvPairDisp = []
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
                     txAmt += fee
                     indicesMakeGray.extend(indicesSelf)
               break


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
         mode=USERMODE.Developer



      layout = QGridLayout()
      lblDescr = QLabel('Transaction Information:') 

      layout.addWidget(lblDescr,     0,0,  1,1)
   
      frm = QFrame()
      frm.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
      frmLayout = QGridLayout()
      lbls = []



      # Show the transaction ID, with the user's preferred endianness
      # I hate BE, but block-explorer requires it so it's probably a better default
      endianness = self.main.settings.getSettingOrSetDefault('PrefEndian', BIGENDIAN)
      estr = ''
      if mode in (USERMODE.Advanced, USERMODE.Developer):
         estr = ' (BE)' if endianness==BIGENDIAN else ' (LE)'
   
      lbls.append([])
      lbls[-1].append(createToolTipObject('Unique identifier for this transaction'))
      lbls[-1].append(QLabel('Transaction ID' + estr + ':'))
      if endianness==BIGENDIAN:
         lbls[-1].append(QLabel( binary_to_hex(data[FIELDS.Hash], endOut=BIGENDIAN) ))
      if endianness==BIGENDIAN:
         lbls[-1].append(QLabel( binary_to_hex(data[FIELDS.Hash], endOut=LITTLEENDIAN) ))


      if mode in (USERMODE.Developer,):
         # Add protocol version and locktime to the display
         lbls.append([])
         lbls[-1].append(createToolTipObject('Bitcoin Protocol Version Number'))
         lbls[-1].append(QLabel('Tx Version:'))
         lbls[-1].append(QLabel( str(pytx.version)))

         lbls.append([])
         lbls[-1].append(createToolTipObject(
            'The time at which this transaction becomes valid.'))
         lbls[-1].append(QLabel('Lock-Time:'))
         if pytx.lockTime==0: 
            lbls[-1].append(QLabel('Immediate (0)'))
         elif pytx.lockTime<500000000:
            lbls[-1].append(QLabel('Block %d' % pytx.lockTime))
         else:
            lbls[-1].append(QLabel(unixTimeToFormatStr(pytx.lockTime)))


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
         lbls[-1].append(QLabel( unixTimeToFormatStr(data[FIELDS.Time]) ))

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
            if not data[FIELDS.Idx]==None and mode==USERMODE.Developer:
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




      if rvPairDisp==None:
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
               'wallet.  All other outputs have been ignored.'))
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
            rlbls[-1].append(QLabel(coin2str(rv[1], maxZeros=1) + '  BTC'))
            ffixBold = QFont("DejaVu Sans Mono", 10)
            ffixBold.setWeight(QFont.Bold)
            rlbls[-1][-1].setFont(ffixBold)
               
            if numRV>numShow and i==numShow-2:
               moreStr = '<%d more recipients>' % (numShow-numRV)
               rlbls.append([])
               rlbls[-1].extend([QLabel(), QLabel(), QLabel(moreStr), QLabel()])
               break
            

         ###
         for i,lbl4 in enumerate(rlbls):
            for i in range(4):
               lbl4[i].setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                            Qt.TextSelectableByKeyboard)
            row = lastRow + 1 + i
            frmLayout.addWidget(lbl4[0], row, 0,  1,1)
            frmLayout.addWidget(lbl4[1], row, 1,  1,1)
            frmLayout.addWidget(lbl4[2], row, 3,  1,1)
            frmLayout.addWidget(lbl4[3], row, 4,  1,1)
         


      # TxIns/Senders
      FontFix = QFont('DejaVu Sans Mono', 10)
      wWlt = 100
      wAddr = 200
      wAmt = tightSizeNChar(FontFix, 20)[0]
      self.txInModel = TxInDispModel(pytx, data[FIELDS.InList], self.main)
      self.txInView = QTableView()
      self.txInView.setModel(self.txInModel)
      self.txInView.setSelectionBehavior(QTableView.SelectRows)
      self.txInView.setSelectionMode(QTableView.SingleSelection)
      self.txInView.horizontalHeader().setStretchLastSection(True)
      self.txInView.verticalHeader().setDefaultSectionSize(20)
      self.txInView.verticalHeader().hide()
      w,h = tightSizeNChar(self.txInView, 1)
      self.txInView.setMinimumHeight(2*(1.3*h))
      self.txInView.setMaximumHeight(5*(1.3*h))
      self.txInView.hideColumn(TXINCOLS.OutPt) 
      self.txInView.hideColumn(TXINCOLS.OutIdx) 
      self.txInView.hideColumn(TXINCOLS.Script) 
      if haveBDM:
         if mode==USERMODE.Standard:
            initialColResize(self.txInView, [wWlt, wAddr*1.5, wAmt, 0, 0, 0, 0, 0, 0])
            self.txInView.hideColumn(TXINCOLS.FromBlk) 
            self.txInView.hideColumn(TXINCOLS.ScrType) 
            self.txInView.hideColumn(TXINCOLS.Sequence) 
         elif mode==USERMODE.Advanced:
            initialColResize(self.txInView, [wWlt, wAddr, wAmt, 0, 0, 0, 0.2, 0, 0])
            self.txInView.hideColumn(TXINCOLS.FromBlk) 
            self.txInView.hideColumn(TXINCOLS.Sequence) 
         elif mode==USERMODE.Developer:
            initialColResize(self.txInView, [wWlt, wAddr, wAmt, 0, 0, 0.1, 0.1, 0.1, 0])
      #else:
         #if mode==USERMODE.Standard:
            #initialColResize(self.txInView, [0, 0.6, 0.5, 0, 0, 0, 0, 0, 0])
            #self.txInView.hideColumn(TXINCOLS.WltID) 
            #self.txInView.hideColumn(TXINCOLS.ScrType) 
         #elif mode==USERMODE.Advanced:
            #initialColResize(self.txInView, [0.2, 0.45, 0.25, 0, 0, 0, 0.2, 0.2, 0])
            

      # List of TxOuts/Recipients
      self.txOutModel = TxOutDispModel(pytx,  self.main, idxGray=indicesMakeGray)
      self.txOutView  = QTableView()
      self.txOutView.setModel(self.txOutModel)
      self.txOutView.setSelectionBehavior(QTableView.SelectRows)
      self.txOutView.setSelectionMode(QTableView.SingleSelection)
      self.txOutView.horizontalHeader().setStretchLastSection(True)
      self.txOutView.verticalHeader().setDefaultSectionSize(20)
      self.txOutView.verticalHeader().hide()
      self.txOutView.setMinimumHeight(2*(1.3*h))
      self.txOutView.setMaximumHeight(5*(1.3*h))
      #self.txOutView.setMinimumHeight(800)
      self.txOutView.hideColumn(TXOUTCOLS.Script) 
      if mode==USERMODE.Standard:
         initialColResize(self.txOutView, [wWlt, wAddr, wAmt, 0, 0])
         self.txOutView.hideColumn(TXOUTCOLS.ScrType) 
      else:
         initialColResize(self.txOutView, [wWlt, wAddr, wAmt, 0.25, 0])


      self.frmIOList = QFrame()
      self.frmIOList.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
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
                  'This shows all outputs of the transactions.  If there were '
                  'more inputs than the size of the transaction, there '
                  'will be an extra change-back-to-sender output, much like '
                  'change returned when buying a candy bar with a $20 bill.  '
                  'If any change outputs were identified they have been '
                  'displayed with a light gray text color.')
         


      inStrip  = makeLayoutStrip('Horiz', [lblInputs,  ttipInputs,  'Stretch'])
      outStrip = makeLayoutStrip('Horiz', [lblOutputs, ttipOutputs, 'Stretch'])
      
      frmIOListLayout.addWidget(inStrip,        0,0, 1,1)
      frmIOListLayout.addWidget(self.txInView,  1,0, 1,1)
      frmIOListLayout.addWidget(outStrip,       2,0, 1,1)
      frmIOListLayout.addWidget(self.txOutView, 3,0, 1,1)
      self.frmIOList.setLayout(frmIOListLayout)

         
      self.btnIOList = QPushButton('')
      self.btnOk     = QPushButton('Ok')
      self.btnIOList.setCheckable(True)
      self.connect(self.btnIOList, SIGNAL('clicked()'), self.extraInfoClicked)
      self.connect(self.btnOk,     SIGNAL('clicked()'), self.accept)
      btnStrip = makeLayoutStrip('Horiz', [self.btnIOList, 'Stretch', self.btnOk])

      if mode==USERMODE.Standard:
         self.btnIOList.setChecked(False)
      else:
         self.btnIOList.setChecked(True)
      self.extraInfoClicked()

      
      frm.setLayout(frmLayout)
      layout.addWidget(frm, 2, 0,  1,1) 
      layout.addWidget(self.frmIOList, 3,0, 1,1)
      layout.addWidget(btnStrip, 4,0, 1,1)

      #bbox = QDialogButtonBox(QDialogButtonBox.Ok)
      #self.connect(bbox, SIGNAL('accepted()'), self.accept)
      #layout.addWidget(bbox, 6,0, 1,1)

      self.setLayout(layout)
      self.layout().setSizeConstraint(QLayout.SetFixedSize)
      self.setWindowTitle('Transaction Info')



   def extraInfoClicked(self):
      if self.btnIOList.isChecked():
         self.frmIOList.setVisible(True)
         self.btnIOList.setText('<<< Less Info')
      else:
         self.frmIOList.setVisible(False)
         self.btnIOList.setText('Advanced >>>') 


      
class DlgTxInfoAdv(QDialog):
   def __init__(self, pytx, wlt, parent=None, main=None):
      super(DlgTxInfoAdv, self).__init__(parent)
         

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


      

      self.binPriv  = wlt.addrMap['ROOT'].binPrivKey32_Plain.copy()
      self.binChain = wlt.addrMap['ROOT'].chaincode.copy()
      if wlt.useEncryption and wlt.isLocked:
         dlg = DlgUnlockWallet(wlt, parent, main)
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

      self.FontVar = QFont('Times',   10)
      self.FontFix = QFont('Courier', 9)

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
         txt = GfxItemText(field, pos, self.scene, self.FontVar)
         self.scene.addItem( txt )
         pos = QPointF(pos.x()+relaxedSizeStr(self.FontFix, 'W'*15)[0], pos.y())
   
         txt = GfxItemText(val, pos, self.scene, self.FontVar)
         self.scene.addItem( txt )
         pos = QPointF(leftEdge, pos.y() + 20)
         return pos
         
      
      txt = GfxItemText('Paper Backup for Armory Wallet', GlobalPos, self.scene, QFont('Times', 14))
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
      txt = GfxItemText(warnMsg, GlobalPos, self.scene, self.FontVar, lineWidth=wrapWidth)
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
      
      

      quadWidth,quadHeight = relaxedSizeStr(self.FontFix, 'abcd ')
      quadWidth+=8  # for some reason, even the relaxed size is too small...

      rootPrefix  = GfxItemText('Root Key:',   GlobalPos, self.scene, QFont('Times', 12))
      chainPrefix = GfxItemText('Chain Code:', GlobalPos, self.scene, QFont('Times', 12))
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
            obj = GfxItemText(strQuad, GlobalPos, self.scene, self.FontFix)
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






################################################################################
################################################################################
if __name__=='__main__':
   app = QApplication(sys.argv)
   app.setApplicationName("dumbdialogs")

   form = dlgNewWallet()
   #form = dlgchangepassphrase(noprevencrypt=true)

   form.show()
   app.exec_()








