import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qtdefines import *

from armoryengine import *
from armorymodels import *
from qlabelbutton import *

MIN_PASSWD_WIDTH = lambda obj: tightSizeStr(obj, '*'*16)[0]

################################################################################
def createToolTipObject(tiptext, iconSz=2):
   lbl = QLabel('<font size=%d color="blue"><u>(?)</u></font>' % iconSz)
   lbl.setToolTip('<u></u>' + tiptext)
   return lbl

################################################################################
class DlgUnlockWallet(QDialog):
   def __init__(self, wlt, parent=None):
      super(DlgUnlockWallet, self).__init__(parent)

      self.wlt = wlt
      self.main = parent

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

   def __init__(self, parent=None):
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

         print self.kdfSec, self.kdfBytes
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
         print 'ChkDisable:', self.chkDisableCrypt.isChecked()
         self.accept()
      else:
         if self.checkPassphrase():
            dlg = DlgPasswd3(self)
            if dlg.exec_():
               if not str(dlg.edtPasswd3.text()) == str(self.edtPasswd1.text()):
                  QMessageBox.critical(self, 'Invalid Passphrase', \
                     'You entered your confirmation passphrase incorrectly!', QMessageBox.Ok)
               else:
                  self.accept() 
            else:
               self.reject()



class DlgPasswd3(QDialog):
   def __init__(self, parent=None):
      super(DlgPasswd3, self).__init__(parent)
      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap('img/Warning64x64'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnTxt1 = QLabel( '<b>!!!  DO NOT FORGET YOUR PASSPHRASE  !!!</b>')
      lblWarnTxt1.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnTxt2 = QLabel( \
         'Bitcoin Armory wallet encryption is designed to be extremely difficult to '
         'crack, even with GPU-acceleration.  No one can help you recover your coins '
         'if you forget your passphrase, not even the developers of this software. '
         'If you are inclined to forget your passphrase, please write it down and '
         'store it in a secure location.')

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
   def __init__(self, currName='', currDescr='', parent=None):
      super(DlgChangeLabels, self).__init__(parent)

      self.edtName = QLineEdit()
      self.edtName.setMaxLength(32)
      lblName = QLabel("Wallet &name:")
      lblName.setBuddy(self.edtName)

      self.edtDescr = QTextEdit()
      fm = QFontMetricsF(QFont(self.edtDescr.font()))
      self.edtDescr.setMaximumHeight(fm.height()*4.2)
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
   def __init__(self, wlt, usermode=USERMODE.Standard, parent=None):
      super(DlgWalletDetails, self).__init__(parent)
      self.setAttribute(Qt.WA_DeleteOnClose)

      self.wlt = wlt
      self.usermode = usermode
      self.main = parent
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
      initialColResize(self.wltAddrView, [0.2, 0.5, 64, 0.3])

   
      # TODO:  Need to do different things depending on which col was clicked
      uacfv = lambda x: self.main.updateAddressCommentFromView(self.wltAddrView, self.wlt)
      self.connect(self.wltAddrView, SIGNAL('doubleClicked(QModelIndex)'), uacfv)
                   
      #self.connect(self.wltAddrView, SIGNAL('doubleClicked(QModelIndex)'), \
                   #self.main,        SLOT('addrViewDblClicked(QModelIndex)'))
      #clip = QApplication.clipboard()
      #def copyAddrToClipboard()


      # Now add all the options buttons, dependent on the type of wallet.

      lbtnChangeLabels = QLabelButton('Change Wallet Name/Description');
      self.connect(lbtnChangeLabels, SIGNAL('clicked()'), self.changeLabels)

      if not self.wlt.watchingOnly:
         s = ''
         if self.wlt.useEncryption:
            s = 'Change or Remove Passphrase'
         else:
            s = 'Encrypt Wallet'
         lbtnChangeCrypto = QLabelButton(s)
         self.connect(lbtnChangeCrypto, SIGNAL('clicked()'), self.changeEncryption)

      lbtnGenAddr = QLabelButton('Get New Address')
      lbtnForkWlt = QLabelButton('Fork Watching-Only Wallet Copy')
      lbtnMkPaper = QLabelButton('Make Paper Backup')
      lbtnExport  = QLabelButton('Make Digital Backup')
      lbtnRemove  = QLabelButton('Delete/Remove Wallet')

      self.connect(lbtnMkPaper, SIGNAL('clicked()'), self.execPrintDlg)
      self.connect(lbtnRemove, SIGNAL('clicked()'), self.execRemoveDlg)

      optFrame = QFrame()
      optFrame.setFrameStyle(QFrame.Box|QFrame.Sunken)
      optLayout = QVBoxLayout()
      optLayout.addWidget(lbtnChangeLabels)

      if not self.wlt.watchingOnly:
         optLayout.addWidget(lbtnChangeCrypto)

      optLayout.addWidget(lbtnGenAddr)
      optLayout.addWidget(lbtnForkWlt)
      optLayout.addWidget(lbtnMkPaper)
      optLayout.addWidget(lbtnExport)
      optLayout.addWidget(lbtnRemove)
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

      

   def changeLabels(self):
      dlgLabels = DlgChangeLabels(self.wlt.labelName, self.wlt.labelDescr, self)
      if dlgLabels.exec_():
         # Make sure to use methods like this which not only update in memory,
         # but guarantees the file is updated, too
         newName  = str(dlgLabels.edtName.text())
         newDescr = str(dlgLabels.edtDescr.toPlainText())
         self.wlt.setWalletLabels(newName, newDescr)

         #self.setWltDetailsFrame()
         self.labelValues[WLTFIELDS.Name].setText(newName)
         self.labelValues[WLTFIELDS.Descr].setText(newDescr)


   def changeEncryption(self):
      dlgCrypt = DlgChangePassphrase(self, not self.wlt.useEncryption)
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
            print 'Should change to no encryption...'
            self.labelValues[WLTFIELDS.Crypto].setText('No Encryption')
         else:
            if not self.wlt.useEncryption:
               kdfParams = self.wlt.computeSystemSpecificKdfParams(0.2)
               self.wlt.changeKdfParams(*kdfParams)
            self.wlt.changeWalletEncryption(securePassphrase=newPassphrase)
            print 'Should change to encrypted...'
            self.labelValues[WLTFIELDS.Crypto].setText('Encrypted')
            #self.accept()
      

   def getNewAddress(self):
      pass 

   def changeKdf(self):
      """ 
      This is a low-priority feature.  I mean, the PyBtcWallet class has this
      feature implemented, but I don't have a GUI for it
      """
      pass

   def execPrintDlg(self):
      if self.wlt.isLocked:
         unlockdlg = DlgUnlockWallet(self.wlt, self)
         if not unlockdlg.exec_():
            return

      if not self.wlt.addrMap['ROOT'].hasPrivKey():
         QMessageBox.warning(self, 'Move along...', \
           'This wallet does not contain any private keys.  Nothing to backup!', QMessageBox.Ok)
         return 

      dlg = DlgPaperBackup(self.wlt, self)
      dlg.exec_()
      
   def execRemoveDlg(self):
      dlg = DlgRemoveWallet(self.wlt, self)
      if dlg.exec_():
         pass # not sure that I don't handle everything in the dialog itself
         


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
            else:
               self.labelValues[WLTFIELDS.BelongsTo] = QLabelButton(owner)

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
      def __init__(self, wltID, parent=None):
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


#############################################################################
class DlgImportWallet(QDialog):
   def __init__(self, parent=None):
      super(DlgImportWallet, self).__init__(parent)
      self.setAttribute(Qt.WA_DeleteOnClose)
      self.main = parent

      lblImportDescr = QLabel('Chose the wallet import source:')
      self.btnImportFile  = QPushButton("Import from &file")
      self.btnImportPaper = QPushButton("Import from &paper backup")

      self.btnImportFile.setMinimumWidth(300)

      self.connect( self.btnImportFile, SIGNAL("clicked()"), \
                    self.getImportWltPath)

      self.connect( self.btnImportPaper, SIGNAL('clicked()'), \
                    self.acceptPaper)

      ttip1 = createToolTipObject('Import an existing Armory wallet, usually with a '
                                 '.wallet extension.  Any wallet that you import will ' 
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
      self.importFile = QFileDialog.getOpenFileName(self, 'Import Wallet File', \
          ARMORY_HOME_DIR, 'Wallet files (*.wallet);; All files (*.*)') 
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
      



#############################################################################
class DlgImportPaperWallet(QDialog):

   wltDataLines = [[]]*4
   prevChars    = ['']*4

   def __init__(self, parent=None):
      super(DlgImportPaperWallet, self).__init__(parent)

      self.main = parent
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
       
      root = PyBtcAddress().createFromPlainKeyData(SecureBinaryData(privKey))
      newWltID = binary_to_base58((ADDRBYTE + root.getAddr160()[:5])[::-1])

      if self.main.walletMap.has_key(newWltID):
         QMessageBox.question(self, 'Duplicate Wallet!', \
               'The data you entered is for a wallet with a ID: \n\n \t' +
               newWltID + '\n\n! This wallet is already loaded into Armory !\n'
               '  You can only import wallets you do not already own!', \
               QMessageBox.Ok)
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
      


class DlgSaveWalletCopy(QDialog):
   def __init__(self, filetypeList=['Wallet files (*.wallet)'], parent=None):
      super(DlgSaveWalletCopy, self).__init__(parent)

      #if parent.lastDirectory:
         #startDir = parent.

      typelist = list(filetypeList) # make a copy
      typelist.append('All files (*)')
      self.saveFile = QFileDialog.getSaveFileName(self, 'Save Wallet File', \
                                       self.lastDirectory, ';; '.join(typelist))

      self.lastDirectory = os.path.split(self.saveFile)[0]


################################################################################
class DlgSetComment(QDialog):
   """ This will be a dumb dialog for retrieving a comment from user """

   #############################################################################
   def __init__(self, currcomment='', ctype='', parent=None):
      super(DlgSetComment, self).__init__(parent)

      self.setWindowTitle('add/change comment')
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
   def __init__(self, parent=None):
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
   def __init__(self, wlt, parent=None):
      super(DlgRemoveWallet, self).__init__(parent)
      
      self.main = parent
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
            lbls[3].append(QLabel('<font color="red"><b>'+coin2str(bal)+' BTC</b></font>'))
            lbls[3][-1].setTextFormat(Qt.RichText)
            wltEmpty = False
         else:
            lbls[3].append(QLabel(coin2str(bal) + ' BTC'))


      # Add two WARNING images on either side of dialog
      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap('img/Warning64x64'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnImg2 = QLabel()
      lblWarnImg2.setPixmap(QPixmap('img/Warning64x64'))
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
      self.radioWatch   = QRadioButton('Convert wallet to watching-only wallet')

      # Make sure that there can only be one selection
      btngrp = QButtonGroup(self)
      btngrp.addButton(self.radioExclude)
      btngrp.addButton(self.radioDelete)
      btngrp.addButton(self.radioWatch)
      btngrp.setExclusive(True)

      lblExcludeDescr = QLabel('This will not delete any files, but will add this '
                              'wallet to the "ignore list."  This means that Armory '
                              'will no longer show this wallet in the main screen '
                              'and none of its funds will be added to your balance.  '
                              'You can re-include this wallet in Armory at a later '
                              'time by selecting the "Excluded Wallets..." option '
                              'in the "Wallets" menu.')
      lblDeleteDescr = QLabel('This will delete the wallet file, removing '
                              'all its private keys from your settings directory.  '
                              'If you intend to keep using addresses from this '
                              'wallet, do not select this option unless the wallet '
                              'is backed up elsewhere.')
      lblWatchDescr  = QLabel('This will delete the private keys from your wallet, '
                              'leaving you with a watching-only wallet, which can be '
                              'used to generate addresses and monitor incoming '
                              'payments.  This option would be used if you created '
                              'the wallet on this computer <i>in order to transfer '
                              'it to a different computer or device and want to '
                              'remove the private data from this system for security.</i>  '
                              '(This will delete the private keys, so make sure they '
                              'are backed in some way before selecting this option).')

      if wlt.watchingOnly:
         lblDeleteDescr = QLabel('This will delete the wallet file from your system.  '
                                 'Since this is a watching-only wallet, no private keys '
                                 'will be deleted.')
         
      for lbl in (lblDeleteDescr, lblExcludeDescr, lblWatchDescr):
         lbl.setWordWrap(True)
         lbl.setMaximumWidth( tightSizeNChar(self, 50)[0] )

      self.chkPrintBackup = QCheckBox('Print a paper backup of this wallet before deleting')

      startRow = 5 if wltEmpty else 4
      self.frm = []
      for rdo,lbl in [(self.radioExclude, lblExcludeDescr), \
                      (self.radioDelete,  lblDeleteDescr), \
                      (self.radioWatch,   lblWatchDescr)]:
         startRow +=1 
         self.frm.append(QFrame())
         self.frm[-1].setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
         frmLayout = QHBoxLayout()
         frmLayout.addWidget(rdo)
         frmLayout.addWidget(lbl)
         self.frm[-1].setLayout(frmLayout)
         layout.addWidget(self.frm[-1], startRow, 0, 1, 3)

      self.radioExclude.setChecked(True)

      if wlt.watchingOnly:
         self.frm[-1].setVisible(False)
         
   
      startRow +=1
      layout.addWidget( self.chkPrintBackup, startRow, 0, 1, 3)

      
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
         dlg = DlgPaperBackup(wlt, self)
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
            self.main.main.removeWalletFromApplication(wltID)
            self.main.main.settings.extend('Excluded_Wallets', wlt.walletPath)
            self.main.main.statusBar().showMessage( \
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

            thepath = wlt.walletPath
            thepathpieces = os.path.splitext(wlt.walletPath)
            thepathBackup = thepathpieces[0] + 'backup' + thepathpieces[1]

            if self.radioWatch.isChecked():
               print '***Converting to watching-only wallet'
               newWltPath = thepathpieces[0] + '_WatchOnly' + thepathpieces[1]
               wlt.forkOnlineWallet(newWltPath, wlt.labelName, wlt.labelDescr)
               newWlt = PyBtcWallet().readWalletFile(newWltPath)
               newWlt.setBlockchainSyncFlag(BLOCKCHAIN_READONLY)
               newWlt.syncWithBlockchain()

               os.remove(thepath)
               os.remove(thepathBackup)
               self.main.main.walletMap[wltID] = newWlt
               self.main.main.statusBar().showMessage( \
                     'Wallet '+wltID+' was replaced with a watching-only wallet.', 10000)
            elif self.radioDelete.isChecked():
               print '***Completely deleting wallet'
               os.remove(thepath)
               os.remove(thepathBackup)
               self.main.main.removeWalletFromApplication(wltID) 
               self.main.main.statusBar().showMessage( \
                     'Wallet '+wltID+' was deleted!', 10000)

            self.main.accept()
            self.accept()
         else:
            self.reject()


class DlgAddressProperties(QDialog):
   def __init__(self, wlt, parent=None):
      super(DlgAddressProperties, self).__init__(parent)

   

      
         
      

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
   def __init__(self, wlt, parent=None):
      super(DlgPaperBackup, self).__init__(parent)




      self.binPriv  = wlt.addrMap['ROOT'].binPrivKey32_Plain.copy()
      self.binChain = wlt.addrMap['ROOT'].chaincode.copy()
      if wlt.useEncryption and wlt.isLocked:
         dlg = DlgUnlockWallet(wlt, parent)
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

      FontVar = QFont('Times',   10)
      FontFix = QFont('Courier', 9)

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
      
      

      quadWidth,quadHeight = relaxedSizeStr(FontFix, 'abcd ')
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
            obj = GfxItemText(strQuad, GlobalPos, self.scene, FontFix)
            self.scene.addItem(obj)
            #movePosRight(GlobalPos, quadWidth)
            GlobalPos = QPointF(GlobalPos.x()+quadWidth, GlobalPos.y())
         
         

      SIZE = 170
      qrRightSide = PAPER_A4_WIDTH - paperMargin
      qrLeftEdge  = qrRightSide - SIZE - 25
      qrTopStart  = topEdge + 0.5*paperMargin  # a little more margin
      #qrWidth = min(qrRightSide - qrLeftEdge, 150)
      #print 'qrLeft  =', qrLeftEdge
      #print 'qrRight =', qrRightSide
      #print 'qrWidth =', qrWidth
      qrPos = QPointF(qrLeftEdge, qrTopStart)
      #for row in rawTxt:
         #fullRow = ' '.join(
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








