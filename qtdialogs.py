################################################################################
#
# Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
import sys
import time
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qtdefines import *

from armoryengine import *
from armorymodels import *
from armorycolors import Colors, htmlColor
import qrc_img_resources

MIN_PASSWD_WIDTH = lambda obj: tightSizeStr(obj, '*'*16)[0]








################################################################################
class DlgUnlockWallet(ArmoryDialog):
   def __init__(self, wlt, parent=None, main=None, unlockMsg='Unlock Wallet'):
      super(DlgUnlockWallet, self).__init__(parent, main)

      self.wlt = wlt

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
class DlgGenericGetPassword(ArmoryDialog):
   def __init__(self, descriptionStr, parent=None, main=None):
      super(DlgGenericGetPassword, self).__init__(parent, main)


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
class DlgNewWallet(ArmoryDialog):

   def __init__(self, parent=None, main=None, initLabel=''):
      super(DlgNewWallet, self).__init__(parent, main)


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
                               '(the actual time used will be less than the specified '
                               'time, but more than one half of it).  ')
      
      
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

      self.setWindowTitle('Create Armory wallet')
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

         if not (self.kdfSec <= 20.0):
            QMessageBox.critical(self, 'Invalid KDF Parameters', \
               'Please specify a compute time no more than 20 seconds.  '
               'Values above one second are usually unnecessary.')
            return False

         kdfM, kdfUnit = str(self.edtComputeMem.text()).split(' ')
         if kdfUnit.lower()=='mb':
            self.kdfBytes = round(float(kdfM)*(1024.0**2) )
         if kdfUnit.lower()=='kb':
            self.kdfBytes = round(float(kdfM)*(1024.0))

         if not (2**15 <= self.kdfBytes <= 2**31):
            QMessageBox.critical(self, 'Invalid KDF Parameters', \
               'Please specify a maximum memory usage between 32 kB '
               'and 2048 MB.')
            return False

         LOGINFO('KDF takes %0.2f seconds and %d bytes', self.kdfSec, self.kdfBytes)
      except:
         QMessageBox.critical(self, 'Invalid Input', \
            'Please specify time with units, such as '
            '"250 ms" or "2.1 s".  Specify memory as kB or MB, such as '
            '"32 MB" or "256 kB". ', QMessageBox.Ok)
         return False
         
      
      self.accept()
            
            
   def getImportWltPath(self):
      self.importFile = QFileDialog.getOpenFileName(self, 'Import Wallet File', \
          ARMORY_HOME_DIR, 'Wallet files (*.wallet);; All files (*)') 
      if self.importFile:
         self.accept()
      



################################################################################
class DlgChangePassphrase(ArmoryDialog):
   def __init__(self, parent=None, main=None, noPrevEncrypt=True):
      super(DlgChangePassphrase, self).__init__(parent, main)



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
      goodColor = htmlColor('TextGreen')
      badColor  = htmlColor('TextRed')
      if not p1==p2:
         self.lblMatches.setText('<font color=%s><b>Passphrases do not match!</b></font>' % badColor)
         return False
      if len(p1)<5:
         self.lblMatches.setText('<font color=%s><b>Passphrase is too short!</b></font>' % badColor)
         return False
      self.lblMatches.setText('<font color=%s><b>Passphrases match!</b></font>' % goodColor)
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



class DlgPasswd3(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgPasswd3, self).__init__(parent, main)


      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap(':/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnTxt1 = QLabel( '<b>!!!  DO NOT FORGET YOUR PASSPHRASE  !!!</b>')
      lblWarnTxt1.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnTxt2 = QLabel( \
         'Armory wallet encryption is designed to be extremely difficult to '
         'crack, even with GPU-acceleration.  No one can help you recover your bitcoins '
         'if you forget your passphrase. '
         'If you are inclined to forget your passphrase, please write it down '
         'or print a paper backup of your wallet and keep it in a safe place. ')
      lblWarnTxt2.setTextFormat(Qt.RichText)

      lblWarnTxt3 = QLabel( \
         'If you are sure you will remember it, please '
         'type it a third time to acknowledge '
         'you understand the consequences of losing your passphrase:')
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
class DlgChangeLabels(ArmoryDialog):
   def __init__(self, currName='', currDescr='', parent=None, main=None):
      super(DlgChangeLabels, self).__init__(parent, main)


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


   def accept(self, *args):
      if len(str(self.edtName.text()).strip())==0:
         QMessageBox.critical(self, 'Empty Name', \
            'All wallets must have a name. ', QMessageBox.Ok)
         return
      super(DlgChangeLabels, self).accept(*args)

      
################################################################################
class DlgWalletDetails(ArmoryDialog):
   """ For displaying the details of a specific wallet, with options """ 

   #############################################################################
   def __init__(self, wlt, usermode=USERMODE.Standard, parent=None, main=None):
      super(DlgWalletDetails, self).__init__(parent, main)
      self.setAttribute(Qt.WA_DeleteOnClose)


      self.wlt = wlt
      self.usermode = usermode
      self.wlttype, self.typestr = determineWalletType(wlt, parent)
      if self.typestr=='Encrypted':
         self.typestr='Encrypted (AES256)'

      self.labels = [wlt.labelName, wlt.labelDescr]
      self.passphrase = ''
      self.setMinimumSize(800,400)
      
      w,h = relaxedSizeNChar(self,60)
      viewWidth,viewHeight  = w, 10*h
      

      # Address view
      self.wltAddrModel = WalletAddrDispModel(wlt, self)
      self.wltAddrProxy = WalletAddrSortProxy(self)
      self.wltAddrProxy.setSourceModel(self.wltAddrModel)
      self.wltAddrView  = QTableView()
      self.wltAddrView.setModel(self.wltAddrProxy)
      self.wltAddrView.setSortingEnabled(True)

      self.wltAddrView.setSelectionBehavior(QTableView.SelectRows)
      self.wltAddrView.setSelectionMode(QTableView.SingleSelection)
      self.wltAddrView.horizontalHeader().setStretchLastSection(True)
      self.wltAddrView.verticalHeader().setDefaultSectionSize(20)
      self.wltAddrView.setMinimumWidth(550)
      self.wltAddrView.setMinimumHeight(150)
      iWidth = tightSizeStr(self.wltAddrView, 'Imp')[0]
      initialColResize(self.wltAddrView, [iWidth*1.5, 0.35, 0.4, 64, 0.2])

      self.wltAddrView.sizeHint = lambda: QSize(700, 225)
      self.wltAddrView.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

      self.wltAddrView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.wltAddrView.customContextMenuRequested.connect(self.showContextMenu)
      self.wltAddrProxy.sort(ADDRESSCOLS.ChainIdx, Qt.AscendingOrder)
   
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
      lbtnImportA = QLabelButton('Import/Sweep Private Keys')
      lbtnDeleteA = QLabelButton('Remove Imported Address')
      #lbtnSweepA  = QLabelButton('Sweep Wallet/Address')
      lbtnForkWlt = QLabelButton('Create Watching-Only Copy')
      lbtnMkPaper = QLabelButton('Make Paper Backup')
      lbtnVwKeys  = QLabelButton('Backup Individual Keys')
      lbtnExport  = QLabelButton('Make Digital Backup')
      lbtnRemove  = QLabelButton('Delete/Remove Wallet')

      self.connect(lbtnSendBtc, SIGNAL('clicked()'), self.execSendBtc)
      self.connect(lbtnGenAddr, SIGNAL('clicked()'), self.getNewAddress)
      self.connect(lbtnMkPaper, SIGNAL('clicked()'), self.execPrintDlg)
      self.connect(lbtnVwKeys,  SIGNAL('clicked()'), self.execKeyList)
      self.connect(lbtnRemove,  SIGNAL('clicked()'), self.execRemoveDlg)
      self.connect(lbtnImportA, SIGNAL('clicked()'), self.execImportAddress)
      self.connect(lbtnDeleteA, SIGNAL('clicked()'), self.execDeleteAddress)
      self.connect(lbtnExport,  SIGNAL('clicked()'), self.saveWalletCopy)
      self.connect(lbtnForkWlt, SIGNAL('clicked()'), self.forkOnlineWallet)

      lbtnSendBtc.setToolTip('<u></u>Send bitcoins to other users, or transfer '
                             'between wallets')
      if self.wlt.watchingOnly:
         lbtnSendBtc.setToolTip('<u></u>If you have a full-copy of this wallet '
                                'on another computer, you can prepare a '
                                'transaction, to be signed by that computer.')
      lbtnGenAddr.setToolTip('<u></u>Get a new address from this wallet for receiving '
                             'bitcoins.  Right click on the address list below '
                             'to copy an existing address.')
      lbtnImportA.setToolTip('<u></u>Import or "Sweep" an address which is not part '
                             'of your wallet.  Useful for VanityGen addresses '
                             'and redeeming Casascius physical bitcoins.')
      lbtnDeleteA.setToolTip('<u></u>Permanently delete an imported address from '
                             'this wallet.  You cannot delete addresses that '
                             'were generated natively by this wallet.')
      #lbtnSweepA .setToolTip('')
      lbtnForkWlt.setToolTip('<u></u>Save a copy of this wallet that can only be used '
                             'for generating addresses and monitoring incoming '
                             'payments.  A watching-only wallet cannot spend '
                             'the funds, and thus cannot be compromised by an '
                             'attacker')
      lbtnMkPaper.setToolTip('<u></u>Create & print a <i>permanent</i> backup of this '
                             'this wallet.  All non-imported addresses ever '
                             'generated by this wallet can be recovered in the '
                             'future if you have a paper backup.  Backup will '
                             'be unencrypted!')
      lbtnVwKeys.setToolTip('<u></u>View raw private key data for all of the addresses '
                            'in this wallet.  <u>Use this to backup your imported '
                            'addresses!</u>  Can also be used to import Armory '
                            'addresses into other Bitcoin applications.')
      lbtnExport.setToolTip('<u></u>Create an exact copy of this wallet (including '
                            'imported addresses).  Use this to backup your '
                            'wallet to digital media (external hard drive, USB, '
                            'etc).  If this wallet is currently encrypted, your '
                            'digital backup will be, too.')
      lbtnRemove.setToolTip('<u></u>Permanently delete this wallet, or just delete '
                            'the private keys to convert it to a watching-only '
                            'wallet.')
      if not self.wlt.watchingOnly:
         lbtnChangeCrypto.setToolTip('<u></u>Add/Remove/Change wallet encryption settings.')

      optFrame = QFrame()
      optFrame.setFrameStyle(STYLE_SUNKEN)
      optLayout = QVBoxLayout()

      hasPriv = not self.wlt.watchingOnly
      adv = (self.main.usermode in (USERMODE.Advanced, USERMODE.Expert))

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


      self.frm = QFrame()
      self.setWltDetailsFrame()

      totalFunds = self.wlt.getBalance('Total')
      spendFunds = self.wlt.getBalance('Spendable')
      unconfFunds= self.wlt.getBalance('Unconfirmed')
      uncolor =  htmlColor('MoneyNeg')  if unconfFunds>0          else htmlColor('Foreground')
      btccolor = htmlColor('DisableFG') if spendFunds==totalFunds else htmlColor('MoneyPos')
      lblcolor = htmlColor('DisableFG') if spendFunds==totalFunds else htmlColor('Foreground')
      goodColor= htmlColor('TextGreen')

      self.lblTot  = QRichLabel('', doWrap=False); 
      self.lblSpd  = QRichLabel('', doWrap=False); 
      self.lblUnc  = QRichLabel('', doWrap=False); 

      self.lblTotalFunds  = QRichLabel('', doWrap=False)
      self.lblSpendFunds  = QRichLabel('', doWrap=False)
      self.lblUnconfFunds = QRichLabel('', doWrap=False)
      self.lblTotalFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.lblSpendFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.lblUnconfFunds.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

      self.lblTot.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.lblSpd.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.lblUnc.setAlignment(Qt.AlignRight | Qt.AlignVCenter)


      self.lblBTC1 = QRichLabel('', doWrap=False)
      self.lblBTC2 = QRichLabel('', doWrap=False)
      self.lblBTC3 = QRichLabel('', doWrap=False)

      ttipTot = createToolTipObject( \
            'Total funds if all current transactions are confirmed.  '
            'Value appears gray when it is the same as your spendable funds.')
      ttipSpd = createToolTipObject( 'Funds that can be spent <i>right now</i>')
      ttipUcn = createToolTipObject( 'Funds that have less than 6 confirmations' )

      self.setSummaryBalances()


      frmTotals = QFrame()
      frmTotals.setFrameStyle(STYLE_NONE)
      frmTotalsLayout = QGridLayout()
      frmTotalsLayout.addWidget(self.lblTot, 0,0)
      frmTotalsLayout.addWidget(self.lblSpd, 1,0)
      frmTotalsLayout.addWidget(self.lblUnc, 2,0)

      frmTotalsLayout.addWidget(self.lblTotalFunds,  0,1)
      frmTotalsLayout.addWidget(self.lblSpendFunds,  1,1)
      frmTotalsLayout.addWidget(self.lblUnconfFunds, 2,1)

      frmTotalsLayout.addWidget(self.lblBTC1, 0,2)
      frmTotalsLayout.addWidget(self.lblBTC2, 1,2)
      frmTotalsLayout.addWidget(self.lblBTC3, 2,2)

      frmTotalsLayout.addWidget(ttipTot, 0,3)
      frmTotalsLayout.addWidget(ttipSpd, 1,3)
      frmTotalsLayout.addWidget(ttipUcn, 2,3)

      frmTotals.setLayout(frmTotalsLayout)

      lblWltAddr = QRichLabel('<b>Addresses in Wallet:</b>', doWrap=False)
      self.chkHideEmpty  = QCheckBox('Hide Empty')
      self.chkHideChange = QCheckBox('Hide Change')
      self.chkHideUnused = QCheckBox('Hide Unused')
      self.chkHideEmpty.setChecked(False)
      self.chkHideChange.setChecked(self.main.usermode==USERMODE.Standard)
      self.chkHideUnused.setChecked(self.wlt.highestUsedChainIndex>25)

      self.connect(self.chkHideEmpty,  SIGNAL('clicked()'), self.doFilterAddr)
      self.connect(self.chkHideChange, SIGNAL('clicked()'), self.doFilterAddr)
      self.connect(self.chkHideUnused, SIGNAL('clicked()'), self.doFilterAddr)

      headerFrm = makeHorizFrame([ lblWltAddr, \
                                   'Stretch', \
                                   self.chkHideEmpty, \
                                   self.chkHideChange, \
                                   self.chkHideUnused] )

      btnGoBack = QPushButton('<<< Go Back')
      self.connect(btnGoBack, SIGNAL('clicked()'), self.accept)
      bottomFrm = makeHorizFrame([btnGoBack, 'Stretch', frmTotals])

      layout = QGridLayout()
      layout.addWidget(self.frm,              0, 0)
      layout.addWidget(headerFrm,            1, 0)
      layout.addWidget(self.wltAddrView,      2, 0)
      layout.addWidget(bottomFrm,             3, 0)

      #layout.addWidget(QLabel("Available Actions:"), 0, 4)
      layout.addWidget(optFrame,              0, 1, 4, 1)
      layout.setRowStretch(0, 0)
      layout.setRowStretch(1, 0)
      layout.setRowStretch(2, 1)
      layout.setRowStretch(3, 0)
      layout.setColumnStretch(0, 1)
      layout.setColumnStretch(1, 0)
      self.setLayout(layout)

      self.setWindowTitle('Wallet Properties')

      self.doFilterAddr()

      hexgeom = self.main.settings.get('WltPropGeometry')
      tblgeom = self.main.settings.get('WltPropAddrCols')
      if len(hexgeom)>0:
         geom = QByteArray.fromHex(hexgeom)
         self.restoreGeometry(geom)
      if len(tblgeom)>0:
         restoreTableView(self.wltAddrView, tblgeom)

   #############################################################################
   def doFilterAddr(self):
      self.wltAddrModel.setFilter(self.chkHideEmpty.isChecked(), \
                                  self.chkHideChange.isChecked(), \
                                  self.chkHideUnused.isChecked())
      self.wltAddrModel.reset()

   #############################################################################
   def setSummaryBalances(self):
      totalFunds = self.wlt.getBalance('Total')
      spendFunds = self.wlt.getBalance('Spendable')
      unconfFunds= self.wlt.getBalance('Unconfirmed')
      uncolor =  htmlColor('MoneyNeg')  if unconfFunds>0          else htmlColor('Foreground')
      btccolor = htmlColor('DisableFG') if spendFunds==totalFunds else htmlColor('MoneyPos')
      lblcolor = htmlColor('DisableFG') if spendFunds==totalFunds else htmlColor('Foreground')
      goodColor= htmlColor('TextGreen')

      self.lblTot.setText('<b><font color="%s">Maximum Funds:</font></b>'%lblcolor)
      self.lblSpd.setText('<b>Spendable Funds:</b>')
      self.lblUnc.setText('<b>Unconfirmed:</b>')

      #if self.main.blkMode in (BLOCKCHAINMODE.Offline, BLOCKCHAINMODE.Rescanning):
      if TheBDM.getBDMState() in ('Uninitialized', 'Offline','Scanning'):
         totStr = '-'*12
         spdStr = '-'*12
         ucnStr = '-'*12
      else:
         totStr = '<b><font color="%s">%s</font></b>' % (btccolor,  coin2str(totalFunds))
         spdStr = '<b><font color="%s">%s</font></b>' % (goodColor, coin2str(spendFunds))
         ucnStr = '<b><font color="%s">%s</font></b>' % (uncolor,   coin2str(unconfFunds))

      self.lblTotalFunds.setText(totStr)
      self.lblSpendFunds.setText(spdStr)
      self.lblUnconfFunds.setText(ucnStr)

      self.lblBTC1.setText('<b><font color="%s">BTC</font></b>'%lblcolor)
      self.lblBTC2.setText('<b>BTC</b>')
      self.lblBTC3.setText('<b>BTC</b>')


   #############################################################################
   def saveGeometrySettings(self):
      self.main.writeSetting('WltPropGeometry', str(self.saveGeometry().toHex()))
      self.main.writeSetting('WltPropAddrCols', saveTableView(self.wltAddrView))

   #############################################################################
   def closeEvent(self, event):
      self.saveGeometrySettings()
      super(DlgWalletDetails, self).closeEvent(event)

   #############################################################################
   def accept(self, *args):
      self.saveGeometrySettings()
      super(DlgWalletDetails, self).accept(*args)

   #############################################################################
   def reject(self, *args):
      self.saveGeometrySettings()
      super(DlgWalletDetails, self).reject(*args)
      
   #############################################################################
   def showContextMenu(self, pos):
      menu = QMenu(self.wltAddrView)
      std = (self.main.usermode==USERMODE.Standard)
      adv = (self.main.usermode==USERMODE.Advanced)
      dev = (self.main.usermode==USERMODE.Expert)
      
      if True:  actionCopyAddr    = menu.addAction("Copy Address")
      if True:  actionShowQRCode  = menu.addAction("Display Address QR Code")
      if True:  actionBlkChnInfo  = menu.addAction("View Address on www.blockchain.info")
      if True:  actionReqPayment  = menu.addAction("Request Payment to this Address")
      if dev:   actionCopyHash160 = menu.addAction("Copy Hash160 (hex)")
      if True:  actionCopyComment = menu.addAction("Copy Comment")
      if True:  actionCopyBalance = menu.addAction("Copy Balance")
      idx = self.wltAddrView.selectedIndexes()[0]
      action = menu.exec_(QCursor.pos())
         
      addr = str(self.wltAddrView.model().index(idx.row(), ADDRESSCOLS.Address).data().toString()).strip()
      if action==actionCopyAddr:
         s = self.wltAddrView.model().index(idx.row(), ADDRESSCOLS.Address).data().toString()
      elif action==actionBlkChnInfo:
         try:
            import webbrowser
            blkchnURL = 'http://blockchain.info/address/%s' % addr
            webbrowser.open(blkchnURL)
         except:
            QMessageBox.critical(self, 'Could not open browser', \
               'Armory encountered an error opening your web browser.  To view '
               'this address on blockchain.info, please copy and paste '
               'the following URL into your browser: '
               '<br><br>%s' % blkchnURL, QMessageBox.Ok)
         return
      elif action==actionShowQRCode:
         wltstr = 'Wallet: %s (%s)' % (self.wlt.labelName, self.wlt.uniqueIDB58)
         DlgQRCodeDisplay(self, self.main, addr, addr, wltstr ).exec_()
         return
      elif action==actionReqPayment:
         DlgRequestPayment(self, self.main, addr).exec_() 
         return
      elif dev and action==actionCopyHash160:
         s = binary_to_hex(addrStr_to_hash160(addr))
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
         newName  = str(dlgLabels.edtName.text())[:32]
         newDescr = str(dlgLabels.edtDescr.toPlainText())[:256]
         self.wlt.setWalletLabels(newName, newDescr)

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
            self.labelValues[WLTFIELDS.Secure].setText('')
            self.labelValues[WLTFIELDS.Secure].setText('')
         else:
            if not self.wlt.useEncryption:
               kdfParams = self.wlt.computeSystemSpecificKdfParams(0.2)
               self.wlt.changeKdfParams(*kdfParams)
            self.wlt.changeWalletEncryption(securePassphrase=newPassphrase)
            self.labelValues[WLTFIELDS.Secure].setText('Encrypted (AES256)')
            #self.accept()
      

   def getNewAddress(self):
      if showWatchOnlyRecvWarningIfNecessary(self.wlt, self.main):
         DlgNewAddressDisp(self.wlt, self, self.main).exec_()
      self.wltAddrView.reset()
       

   def execSendBtc(self):
      #if self.main.blkMode == BLOCKCHAINMODE.Offline:
      if TheBDM.getBDMState() in ('Offline', 'Uninitialized'):
         QMessageBox.warning(self, 'Offline Mode', \
           'Armory is currently running in offline mode, and has no '
           'ability to determine balances or create transactions. '
           '<br><br>'
           'In order to send coins from this wallet you must use a '
           'full copy of this wallet from an online computer, '
           'or initiate an "offline transaction" using a watching-only '
           'wallet on an online computer.', QMessageBox.Ok)
         return
      if TheBDM.getBDMState() == 'Scanning':
         QMessageBox.warning(self, 'Armory Not Ready', \
           'Armory is currently scanning the blockchain to collect '
           'the information needed to create transactions.  This typically '
           'takes between one and five minutes.  Please wait until your '
           'balance appears on the main window, then try again.', \
            QMessageBox.Ok)
         return
      dlgSend = DlgSendBitcoins(self.wlt, self, self.main)
      dlgSend.exec_()
      self.wltAddrModel.reset()
   


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
      if self.wlt.useEncryption and self.wlt.isLocked:
         dlg = DlgUnlockWallet(self.wlt, self, self.main, 'Unlock Private Keys')
         if not dlg.exec_():
            if self.main.usermode==USERMODE.Expert:
               QMessageBox.warning(self, 'Unlock Failed', \
                  'Wallet was not be unlocked.  The public keys and addresses '
                  'will still be shown, but private keys will not be available '
                  'unless you reopen the dialog with the correct passphrase', \
                  QMessageBox.Ok)
            else:
               QMessageBox.warning(self, 'Unlock Failed', \
                  'Wallet could not be unlocked to display individual keys.', \
                  QMessageBox.Ok)
               return
               
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
      
      #if TheBDM.getBDMState()=='Scanning':
         #QMessageBox.warning(self, 'Armory Not Ready',
            #'Armory is currently in the process of scanning the blockchain '
            #'for your existing wallets.  This operation must finish before '
            #'you can import or sweep private keys.  '
            #'<br><br>'
            #'Try again after your balances and transaction history appear '
            #'in the main window.', QMessageBox.Ok)
         #return

      if not self.main.getSettingOrSetDefault('DNAA_ImportWarning', False):
         result = MsgBoxWithDNAA(MSGBOX.Warning, 'Import Address Warning', \
                       'Armory supports importing of external '
                       'addresses into your wallet, including encryption, '
                       'but imported addresses <b>cannot</b> be protected/saved '
                       'by a paper backups.'
                       '<br><br>' 
                       'Please use "Backup Individual Keys" from the wallet '
                       'properties dialog to backup the imported keys.', None)
         self.main.writeSetting('DNAA_ImportWarning', result[1])

      # Now we are past the [potential] warning box.  Actually open
      # the import dialog
      dlg = DlgImportAddress(self.wlt, self, self.main)
      dlg.exec_()

      try:
         self.parent.wltAddrModel.reset()
      except AttributeError:
         pass



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
                                               self.usermode==USERMODE.Expert)
      self.wltID = self.wlt.uniqueIDB58

      if dispCrypto:
         mem = self.wlt.kdf.getMemoryReqtBytes()
         kdfmemstr = str(mem/1024)+' kB'
         if mem >= 1024*1024:
            kdfmemstr = str(mem/(1024*1024))+' MB'
   
   
      tooltips = [[]]*10
   
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
            'This is the number of addresses *used* by this wallet so far. '
            'If you recently restored this wallet and you do not see all the '
            'funds you were expecting, click on this field to increase it.')
   
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
      elif self.typestr=='Encrypted (AES256)':
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
   
      tooltips[WLTFIELDS.Time] = createToolTipObject(
            'This is exactly how long it takes your computer to unlock your '
            'wallet after you have entered your passphrase.  If someone got '
            'ahold of your wallet, this is approximately how long it would take '
            'them to for each guess of your passphrase.')
   
      tooltips[WLTFIELDS.Mem] = createToolTipObject(
            'This is the amount of memory required to unlock your wallet. '
            'Memory values above 2 MB pretty much guarantee that GPU-acceleration '
            'will be useless for guessing your passphrase')
   
      tooltips[WLTFIELDS.Version] = createToolTipObject(
            'Wallets created with different versions of Armory, may have '
            'different wallet versions.  Not all functionality may be '
            'available with all wallet versions.  Creating a new wallet will '
            'always create the latest version.')
      labelNames = [[]]*10
      labelNames[WLTFIELDS.Name]    = QLabel('Wallet Name:')
      labelNames[WLTFIELDS.Descr]   = QLabel('Description:')
   
      labelNames[WLTFIELDS.WltID]     = QLabel('Wallet ID:')
      labelNames[WLTFIELDS.NumAddr]   = QLabel('Addresses Used:')
      labelNames[WLTFIELDS.Secure]    = QLabel('Security:')
      labelNames[WLTFIELDS.Version]   = QLabel('Version:')

      labelNames[WLTFIELDS.BelongsTo] = QLabel('Belongs to:')
   
   
      # TODO:  Add wallet path/location to this!
   
      if dispCrypto:
         labelNames[WLTFIELDS.Time]   = QLabel('Unlock Time:')
         labelNames[WLTFIELDS.Mem]    = QLabel('Unlock Memory:')
   
      self.labelValues = [[]]*10
      self.labelValues[WLTFIELDS.Name]    = QLabel(self.wlt.labelName)
      self.labelValues[WLTFIELDS.Descr]   = QLabel(self.wlt.labelDescr)
   
      self.labelValues[WLTFIELDS.WltID]     = QLabel(self.wlt.uniqueIDB58)
      self.labelValues[WLTFIELDS.Secure]    = QLabel(self.typestr)
      self.labelValues[WLTFIELDS.BelongsTo] = QLabel('')
      self.labelValues[WLTFIELDS.Version]   = QLabel(getVersionString(self.wlt.version))


      topUsed    = max(self.wlt.highestUsedChainIndex,0)
      self.labelValues[WLTFIELDS.NumAddr] = QLabelButton('%d' % topUsed)
      self.labelValues[WLTFIELDS.NumAddr].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
      opendlgkeypool = lambda: DlgKeypoolSettings(self.wlt,self,self.main).exec_()
      self.connect(self.labelValues[WLTFIELDS.NumAddr], SIGNAL('clicked()'), opendlgkeypool) 

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
         self.labelValues[WLTFIELDS.Time]   = QLabelButton('Click to Test')
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
   
   
      for i,lbl in enumerate(self.labelValues):
         if i==WLTFIELDS.BelongsTo:
            lbl.setContentsMargins(10, 0, 10, 0)
            continue
         try:
            lbl.setText( '<i>' + lbl.text() + '</i>')
            lbl.setContentsMargins(10, 0, 10, 0)
            #lbl.setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                        #Qt.TextSelectableByKeyboard)
         except AttributeError:
            pass
   
      # Not sure why this has to be connected downhere... it didn't work above it
      if dispCrypto:
         self.labelValues[WLTFIELDS.Time].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
         self.connect(self.labelValues[WLTFIELDS.Time], SIGNAL('clicked()'), self.testKdfTime)

      labelNames[WLTFIELDS.Descr].setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.labelValues[WLTFIELDS.Descr].setWordWrap(True)
      self.labelValues[WLTFIELDS.Descr].setAlignment(Qt.AlignLeft | Qt.AlignTop)
   
      lblEmpty = QLabel(' '*20)
   
      layout = QGridLayout()

      layout.addWidget(tooltips[WLTFIELDS.WltID],            0, 0); 
      layout.addWidget(labelNames[WLTFIELDS.WltID],          0, 1); 
      layout.addWidget(self.labelValues[WLTFIELDS.WltID],    0, 2)

      layout.addWidget(tooltips[WLTFIELDS.Name],             1, 0); 
      layout.addWidget(labelNames[WLTFIELDS.Name],           1, 1); 
      layout.addWidget(self.labelValues[WLTFIELDS.Name],     1, 2)
   
      layout.addWidget(tooltips[WLTFIELDS.Descr],            2, 0); 
      layout.addWidget(labelNames[WLTFIELDS.Descr],          2, 1); 
      layout.addWidget(self.labelValues[WLTFIELDS.Descr],    2, 2, 4, 1)
   
      layout.addWidget(tooltips[WLTFIELDS.Version],          0, 3); 
      layout.addWidget(labelNames[WLTFIELDS.Version],        0, 4); 
      layout.addWidget(self.labelValues[WLTFIELDS.Version],  0, 5)
   
      i=0
      if self.main.usermode==USERMODE.Expert:
         i+=1
         layout.addWidget(tooltips[WLTFIELDS.NumAddr],          i, 3) 
         layout.addWidget(labelNames[WLTFIELDS.NumAddr],        i, 4) 
         layout.addWidget(self.labelValues[WLTFIELDS.NumAddr],  i, 5)
   
      i+=1
      layout.addWidget(tooltips[WLTFIELDS.Secure],           i, 3); 
      layout.addWidget(labelNames[WLTFIELDS.Secure],         i, 4); 
      layout.addWidget(self.labelValues[WLTFIELDS.Secure],   i, 5)
   

      if self.wlt.watchingOnly:
         i+=1
         layout.addWidget(tooltips[WLTFIELDS.BelongsTo],           i, 3); 
         layout.addWidget(labelNames[WLTFIELDS.BelongsTo],         i, 4); 
         layout.addWidget(self.labelValues[WLTFIELDS.BelongsTo],   i, 5)
      
   
      if dispCrypto:
         i+=1
         layout.addWidget(tooltips[WLTFIELDS.Time],           i, 3); 
         layout.addWidget(labelNames[WLTFIELDS.Time],         i, 4); 
         layout.addWidget(self.labelValues[WLTFIELDS.Time],   i, 5)
   
         i+=1
         layout.addWidget(tooltips[WLTFIELDS.Mem],            i, 3); 
         layout.addWidget(labelNames[WLTFIELDS.Mem],          i, 4); 
         layout.addWidget(self.labelValues[WLTFIELDS.Mem],    i, 5)

   
      self.frm = QFrame()
      self.frm.setFrameStyle(STYLE_SUNKEN)
      self.frm.setLayout(layout)
      
      

   def testKdfTime(self):
      kdftimestr = "%0.3f sec" % self.wlt.testKdfComputeTime()
      self.labelValues[WLTFIELDS.Time].setText(kdftimestr)
      

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
         


   class dlgChangeOwner(ArmoryDialog):
      def __init__(self, wltID, parent=None, main=None):
         super(parent.dlgChangeOwner, self).__init__(parent, main)


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


def showWatchOnlyRecvWarningIfNecessary(wlt, main):

   wlttype = determineWalletType(wlt, main)[0]
   notMyWallet   = (wlttype==WLTTYPES.WatchOnly)
   offlineWallet = (wlttype==WLTTYPES.Offline)
   dnaaPropName = 'Wallet_%s_%s' % (wlt.uniqueIDB58, 'DNAA_RecvOther')
   dnaaThisWallet = main.getSettingOrSetDefault(dnaaPropName, False)
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
      main.writeSetting(dnaaPropName, result[1])
      return result[0]

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
      main.writeSetting(dnaaPropName, result[1])
      return result[0]
   return True



################################################################################
class DlgKeypoolSettings(ArmoryDialog):
   """
   Let the user manually adjust the keypool for this wallet
   """
   def __init__(self, wlt, parent=None, main=None):
      super(DlgKeypoolSettings, self).__init__(parent, main)

      self.wlt = wlt

      self.addressesWereGenerated = False
      
      self.lblDescr = QRichLabel( \
         'Armory pre-computes a pool of addresses beyond the last address '
         'you have used, and keeps them in your wallet to "look-ahead."  One '
         'reason it does this is in case you have restored this wallet from '
         'a backup, and Armory does not know how many addresses you have actually '
         'used. '
         '<br><br>'
         'If this wallet was restored from a backup and was very active after '
         'it was backed up, then it is possible Armory did not pre-compute '
         'enough addresses to find your entire balance.  <b>This condition is '
         'rare</b>, but it can happen.  You may extend the keypool manually, '
         'below.')

      self.lblAddrUsed    = QRichLabel('Addresses used: ', doWrap=False)
      self.lblAddrComp    = QRichLabel('Addresses computed: ', doWrap=False)
      self.lblAddrUsedVal = QRichLabel('%d' % max(0,self.wlt.highestUsedChainIndex))
      self.lblAddrCompVal = QRichLabel('%d' % self.wlt.lastComputedChainIndex)

      self.lblNumAddr = QRichLabel('Compute this many more addresses: ')
      self.edtNumAddr = QLineEdit()
      self.edtNumAddr.setText('100')
      self.edtNumAddr.setMaximumWidth( relaxedSizeStr(self,'9999999')[0])

      self.lblWarnSpeed = QRichLabel(
         'Address computation is very slow.  It may take up to one minute '
         'to compute 200-1000 addresses (system-dependent).  Only generate '
         'as many as you think you need.')


      buttonBox = QDialogButtonBox()
      self.btnAccept = QPushButton("Compute")
      self.btnReject = QPushButton("Done")
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.clickCompute)
      self.connect(self.btnReject, SIGNAL('clicked()'), self.reject)
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnReject, QDialogButtonBox.RejectRole)


      frmLbl  = makeVertFrame([self.lblAddrUsed,    self.lblAddrComp   ])
      frmVal  = makeVertFrame([self.lblAddrUsedVal, self.lblAddrCompVal])
      subFrm1 = makeHorizFrame(['Stretch', frmLbl, frmVal, 'Stretch'], STYLE_SUNKEN)
      
      subFrm2 = makeHorizFrame(['Stretch', \
                                self.lblNumAddr, \
                                self.edtNumAddr, \
                                'Stretch'], STYLE_SUNKEN)

      layout = QVBoxLayout()
      layout.addWidget(self.lblDescr)
      layout.addWidget(subFrm1)
      layout.addWidget(self.lblWarnSpeed)
      layout.addWidget(subFrm2)
      layout.addWidget(buttonBox)

      self.setLayout(layout)
      self.setWindowTitle('Extend Address Pool')


   #############################################################################
   def reject(self):
      if self.addressesWereGenerated and not TheBDM.getBDMState() in ('Offline','Uninitialized'):
         QMessageBox.warning(self, 'Rescan Required', \
            'New addresses have been generated for your wallet, but their '
            'balances are not yet reflected on the main screen.  You must '
            'initiate a blockchain rescan before this happens.  Press the '
            'button on the dashboard to do a rescan, or simply restart Armory', \
            QMessageBox.Ok)
 
      super(DlgKeypoolSettings, self).reject()

   #############################################################################
   def clickCompute(self):
      #if TheBDM.getBDMState()=='Scanning':
         #QMessageBox.warning(self, 'Armory is Busy', \
            #'Armory is in the middle of a scan, and cannot add addresses to '
            #'any of its wallets until the scan is finished.  Please wait until '
            #'the dashboard says that Armory is "online."', QMessageBox.Ok)
         #return


      err = False
      try:
         naddr = int(self.edtNumAddr.text())
      except:
         err = True

      if err or naddr<1:
         QMessageBox.critical(self, 'Invalid input', \
            'The value you entered is invalid.  Please enter a positive '
            'number of addresses to generate.', QMessageBox.Ok)
         return
     
      if naddr>=1000:
         confirm = QMessageBox.warning(self, 'Are you sure?', \
            'You have entered that you want to compute %d more addresses '
            'for this wallet.  This operation will take a very long time, '
            'and Armory will become unresponsive until the computation is '
            'finished.  Armory estimates it will take about %d minutes. '
            '<br><br>Do you want to continue?' % (naddr, int(naddr/750.)), \
            QMessageBox.Yes | QMessageBox.No)
         
         if not confirm==QMessageBox.Yes:
            return

      cred = htmlColor('TextRed')
      self.lblAddrCompVal.setText('<font color="%s">Calculating...</font>' % cred)
   
      def doit():
         currPool = self.wlt.lastComputedChainIndex - self.wlt.highestUsedChainIndex
         self.wlt.fillAddressPool(currPool+naddr, isActuallyNew=False)
         self.lblAddrCompVal.setText('<font color="%s">%d</font>' % \
                        (cred, self.wlt.lastComputedChainIndex))
         self.addressesWereGenerated = True
         self.main.forceNeedRescan = False

      # We use callLater so that we can let the screen redraw with "Calculating..."
      from twisted.internet import reactor
      reactor.callLater(0.1, doit)


################################################################################
class DlgNewAddressDisp(ArmoryDialog):
   """
   We just generated a new address, let's show it to the user and let them
   a comment to it, if they want.
   """
   def __init__(self, wlt, parent=None, main=None):
      super(DlgNewAddressDisp, self).__init__(parent, main)

      self.wlt  = wlt
      self.addr = wlt.getNextUnusedAddress()
      addrStr = self.addr.getAddrStr()

      wlttype = determineWalletType( self.wlt, self.main)[0]
      notMyWallet   = (wlttype==WLTTYPES.WatchOnly)
      offlineWallet = (wlttype==WLTTYPES.Offline)

      lblDescr = QLabel( \
            'The following address can be used to to receive bitcoins:')
      self.edtNewAddr = QLineEdit()
      self.edtNewAddr.setReadOnly(True)
      self.edtNewAddr.setText(addrStr)
      self.edtNewAddr.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      btnClipboard = QPushButton('Copy to Clipboard')
      #lbtnClipboard.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      self.lblIsCopied = QLabel(' or ')
      self.lblIsCopied.setTextFormat(Qt.RichText)
      self.connect(btnClipboard, SIGNAL('clicked()'), self.setClipboard)

      def openPaymentRequest():
         msgTxt = str(self.edtComm.toPlainText())
         msgTxt = msgTxt.split('\n')[0][:128]
         dlg = DlgRequestPayment(self, self.main, addrStr, msg=msgTxt)
         dlg.exec_()

      btnLink = QPushButton('Create Clickable Link')
      self.connect(btnLink, SIGNAL('clicked()'), openPaymentRequest)

      
      tooltip1 = createToolTipObject( \
            'You can securely use this address as many times as you want. '
            'However, all people to whom you give this address will '
            'be able to see the number and amount of bitcoins <b>ever</b> '
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
         palette.setColor( QPalette.Base, Colors.TblWltMine )
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
      frmCopyLayout.addWidget(btnLink)
      frmCopyLayout.addStretch()
      frmCopy.setLayout(frmCopyLayout)

      frmNewAddrLayout.addWidget(frmCopy, 2, 0, 1, 2)
      frmNewAddr.setLayout(frmNewAddrLayout)
   

      lblCommDescr = QLabel( \
            '(Optional) Add a label to this address, which will '
            'be shown with any relevant transactions in the '
            '"Transactions" tab.')
      lblCommDescr.setWordWrap(True)
      self.edtComm = QTextEdit()
      tightHeight = tightSizeNChar(self.edtComm, 1)[1]
      self.edtComm.setMaximumHeight(tightHeight*3.2)

      frmComment = QFrame()
      frmComment.setFrameStyle(STYLE_RAISED)
      frmCommentLayout = QGridLayout()
      frmCommentLayout.addWidget(lblCommDescr,    0,0, 1,2)
      frmCommentLayout.addWidget(self.edtComm,    1,0, 2,2)
      frmComment.setLayout(frmCommentLayout)

      
      lblRecvWlt = QRichLabel( 'Bitcoins sent to this address will '
            'appear in the wallet:', doWrap=False)
      
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
      self.connect(self.btnDone,   SIGNAL('clicked()'), self.acceptNewAddr)
      buttonBox.addButton(self.btnDone,   QDialogButtonBox.AcceptRole)




      frmWlt = QFrame()
      frmWlt.setFrameShape(STYLE_RAISED)
      frmWltLayout = QGridLayout()
      frmWltLayout.addWidget(lblRecvWlt)
      frmWltLayout.addWidget(lblRecvWltID)
      frmWlt.setLayout(frmWltLayout)


      qrdescr = QRichLabel('<b>Scan QR code with phone or other barcode reader</b>'
                           '<br><br><font size=2>(Double-click to expand)</font>')
      qrdescr.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      qrcode = QRCodeWidget(addrStr, parent=self)
      smLabel = QRichLabel('<font size=2>%s</font>' % addrStr)
      smLabel.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
      frmQRsub2 = makeHorizFrame( ['Stretch', qrcode, 'Stretch' ])
      frmQRsub3 = makeHorizFrame( ['Stretch', smLabel, 'Stretch' ])
      frmQR = makeVertFrame( ['Stretch', qrdescr, frmQRsub2, frmQRsub3, 'Stretch' ], STYLE_SUNKEN) 

      layout=QGridLayout()
      layout.addWidget(frmNewAddr,         0, 0, 1, 1)
      layout.addWidget(frmComment,         2, 0, 1, 1)
      layout.addWidget(frmWlt,             3, 0, 1, 1)
      layout.addWidget(buttonBox,          4, 0, 1, 2)
      layout.addWidget(frmQR,              0, 1, 4, 1)

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
class DlgImportWarning(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgImportWarning, self).__init__(parent, main)
      lblWarn = QLabel( 'Armory supports importing of external '
            'addresses into your wallet, including encryption, '
            'but imported addresses <b>cannot</b> be protected/saved '
            'by a paper backups.  Watching-only wallets will include '
            'imported addresses if the watching-only wallet was '
            'created after the address was imported.')
      lblWarn.setTextFormat(Qt.RichText)
      lblWarn.setWordWrap(True)

      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap(':/MsgBox_warning48.png'))
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
         self.main.writeSetting('DNAA_ImportWarning', True)
      self.accept()



#############################################################################
class DlgImportAddress(ArmoryDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgImportAddress, self).__init__(parent, main)

      self.wlt = wlt


      lblImportLbl = QRichLabel('Enter:')

      self.radioImportOne   = QRadioButton('One Key')
      self.radioImportMany  = QRadioButton('Multiple Keys')
      btngrp = QButtonGroup(self)
      btngrp.addButton(self.radioImportOne)
      btngrp.addButton(self.radioImportMany)
      btngrp.setExclusive(True)
      self.radioImportOne.setChecked(True)
      self.connect(self.radioImportOne,   SIGNAL('clicked()'), self.clickImportCount)
      self.connect(self.radioImportMany,  SIGNAL('clicked()'), self.clickImportCount)

      frmTop = makeHorizFrame([lblImportLbl, self.radioImportOne, \
                                             self.radioImportMany, 'Stretch'])
      self.stackedImport = QStackedWidget()
      stkOneLayout  = QVBoxLayout()
      stkManyLayout = QVBoxLayout()


      # Set up the single-key import widget
      lblDescrOne = QRichLabel('The key can either be imported into your wallet, '
                     'or have its available balance "swept" to another address '
                     'in your wallet.  Only import private '
                     'key data if you are absolutely sure that no one else '
                     'has access to it.  Otherwise, sweep it to get '
                     'the funds out of it.  All standard private-key formats '
                     'are supported <i>except for private keys created by '
                     'Bitcoin-Qt version 0.6.0 and later (compressed)</i>.')

      lblPrivOne = QRichLabel('Private Key')
      self.edtPrivData = QLineEdit()
      self.edtPrivData.setMinimumWidth( tightSizeStr(self.edtPrivData, 'X'*80)[0])
      privTooltip = createToolTipObject( \
                       'Supported formats are any hexadecimal or Base58 '
                       'representation of a 32-byte private key (with or '
                       'without checksums), and mini-private-key format '
                       'used on Casascius physical bitcoins.  Private keys '
                       'that use <i>compressed</i> public keys are not yet '
                       'supported by Armory.')

      frmMid1 = makeHorizFrame([lblPrivOne, self.edtPrivData, privTooltip])
      stkOne = makeVertFrame([HLINE(),lblDescrOne, frmMid1, 'Stretch'])
      self.stackedImport.addWidget(stkOne)
      


      # Set up the multi-key import widget
      lblDescrMany = QRichLabel( \
                   'Enter a list of private keys to be "swept" or imported. '
                   'All standard private-key formats are supported.  ')
      lblPrivMany = QRichLabel('Private Key List')
      lblPrivMany.setAlignment(Qt.AlignTop)
      ttipPrivMany = createToolTipObject( \
                  'One private key per line, in any standard format. '
                  'Data may be copied directly from file the "Backup '
                  'Individual Keys" dialog (all text on a line preceding '
                  'the key data, separated by a colon, will be ignored).')
      self.txtPrivBulk = QTextEdit()
      w,h = tightSizeStr(self.edtPrivData, 'X'*70)
      self.txtPrivBulk.setMinimumWidth(w)
      self.txtPrivBulk.setMinimumHeight( 2.2*h)
      self.txtPrivBulk.setMaximumHeight( 4.2*h)
      frmMid = makeHorizFrame([lblPrivMany, self.txtPrivBulk, ttipPrivMany])
      stkMany = makeVertFrame([HLINE(),lblDescrMany, frmMid])
      self.stackedImport.addWidget(stkMany)




      # Set up the Import/Sweep select frame
      ## Import option
      self.radioSweep  = QRadioButton('Sweep any funds owned by these addresses '
                                      'into your wallet\n'
                                      'Select this option if someone else gave you this key')
      self.radioImport = QRadioButton('Import these addresses to your wallet\n'
                                      'Only select this option if you are positive '
                                      'that no one else has access to this key')


      ## Sweep option (only available when online)
      if TheBDM.getBDMState()=='BlockchainReady':
         self.radioSweep  = QRadioButton('Sweep any funds owned by this address '
                                         'into your wallet\n'
                                         'Select this option if someone else gave you this key')
         self.radioSweep.setChecked(True)
      else:
         if TheBDM.getBDMState() in ('Offline','Uninitialized'):
            self.radioSweep  = QRadioButton('Sweep any funds owned by this address '
                                            'into your wallet\n'
                                            '(Not available in offline mode)')
         elif TheBDM.getBDMState()=='Scanning':
            self.radioSweep  = QRadioButton('Sweep any funds owned by this address '
                                            'into your wallet\n'
                                            '(Must wait for blockchain scanning to finish)')
         self.radioImport.setChecked(True)
         self.radioSweep.setEnabled(False)


      sweepTooltip = createToolTipObject( \
         'You should never add an untrusted key to your wallet.  By choosing this '
         'option, you are only moving the funds into your wallet, but not the key '
         'itself.  You should use this option for Casascius physical bitcoins.')

      importTooltip = createToolTipObject( \
         'This option will make the key part of your wallet, meaning that it '
         'can be used to securely receive future payments.  <b>Never</b> select this '
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
      frmWarnLayout.addWidget(sweepTooltip,       0,1, 1,1)
      frmWarnLayout.addWidget(importTooltip,      1,1, 1,1)
      frmWarn.setLayout(frmWarnLayout)

        

      buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonbox, SIGNAL('accepted()'), self.okayClicked)
      self.connect(buttonbox, SIGNAL('rejected()'), self.reject)

      

      

      layout = QVBoxLayout()
      layout.addWidget(frmTop)
      layout.addWidget(self.stackedImport)
      layout.addWidget(frmWarn)
      layout.addWidget(buttonbox)

      self.setWindowTitle('Private Key Import')
      self.setLayout(layout)




   #############################################################################
   def clickImportCount(self):
      isOne = self.radioImportOne.isChecked()
      if isOne:
         self.stackedImport.setCurrentIndex(0)
      else:
         self.stackedImport.setCurrentIndex(1)


   #############################################################################
   def okayClicked(self):
      if self.radioImportOne.isChecked():
         self.processUserString()
      else:
         self.processMultiKey()


   #############################################################################
   def processUserString(self):
      theStr = str(self.edtPrivData.text()).strip().replace(' ','')
      binKeyData, addr160, addrStr = '','',''
      
      try:
         binKeyData, keyType = parsePrivateKeyData(theStr)
         if binary_to_int(binKeyData, BIGENDIAN) >= SECP256K1_ORDER:
            QMessageBox.critical(self, 'Invalid Private Key', \
               'The private key you have entered is actually not valid '
               'for the elliptic curve used by Bitcoin (secp256k1).  '
               'Almost any 64-character hex is a valid private key '
               '<b>except</b> for those greater than: '
               '<br><br>'
               'fffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141'
               '<br><br>'
               'Please try a different private key.', QMessageBox.Ok)
            LOGERROR('User attempted import of invalid private key!')
            return
         addr160 = convertKeyDataToAddress(privKey=binKeyData)
         addrStr = hash160_to_addrStr(addr160)
      except InvalidHashError, e:
         QMessageBox.warning(self, 'Entry Error',
            'The private key data you supplied appears to '
            'contain a consistency check.  This consistency '
            'check failed.  Please verify you entered the '
            'key data correctly.', QMessageBox.Ok)
         LOGERROR('Private key consistency check failed.')
         return
      except BadInputError, e:
         QMessageBox.critical(self, 'Invalid Data', 'Something went terribly '
            'wrong!  (key data unrecognized)', QMessageBox.Ok)
         LOGERROR('Unrecognized key data!')
         return
      except CompressedKeyError, e:
         QMessageBox.critical(self, 'Unsupported key type', 'You entered a key '
            'for an address that uses a compressed public key, usually produced '
            'in Bitcoin-Qt/bitcoind wallets created after version 0.6.0.  Armory '
            'does not yet support this key type.')
         LOGERROR('Compressed key data recognized but not supported')
         return
      except:
         QMessageBox.critical(self, 'Error Processing Key', \
            'There was an error processing the private key data. '
            'Please check that you entered it correctly', QMessageBox.Ok)
         LOGEXCEPT('Error processing the private key data')
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
               binKeyData = binary_switchEndian(binKeyData)
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
                  return



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

         else:
            wltID = self.main.getWalletForAddr160(addr160)
            if not wltID=='':
               addr = self.main.walletMap[wltID].addrMap[addr160]
               typ = 'Imported' if addr.chainIndex==-2 else 'Permanent'
               msg = ('The key you entered is already part of another wallet you '
                      'are maintaining:'
                     '<br><br>'
                     '<b>Address</b>: ' + addrStr + '<br>'
                     '<b>Wallet ID</b>: ' + wltID + '<br>'
                     '<b>Wallet Name</b>: ' + self.main.walletMap[wltID].labelName + '<br>'
                     '<b>Address Type</b>: ' + typ + 
                     '<br><br>'
                     'The sweep operation will simply move bitcoins out of the wallet '
                     'above into this wallet.  If the network charges a fee for this '
                     'transaction, you balance will be reduced by that much.')
               result = QMessageBox.warning(self, 'Duplicate Address', msg, \
                     QMessageBox.Ok | QMessageBox.Cancel)
               if not result==QMessageBox.Ok:
                  return

   
         #if not TheBDM.getBDMState()=='BlockchainReady':
            #reply = QMessageBox.critical(self, 'Cannot Sweep Address', \
            #'You need access to the Bitcoin network and the blockchain in order '
            #'to find the balance of this address and sweep its funds. ', \
            #QMessageBox.Ok)
            #return

         # Create the address object for the addr to be swept
         sweepAddr = PyBtcAddress().createFromPlainKeyData(SecureBinaryData(binKeyData))
         targAddr160 = self.wlt.getNextUnusedAddress().getAddr160()

         self.main.confirmSweepScan([sweepAddr], targAddr160)

         # Regardless of the user confirmation, we're done here
         self.accept()


      elif self.radioImport.isChecked():
         if self.wlt.hasAddr(addr160):
            QMessageBox.critical(self, 'Duplicate Address', \
            'The address you are trying to import is already part of your '
            'wallet.  Address cannot be imported', QMessageBox.Ok)
            return

         wltID = self.main.getWalletForAddr160(addr160)
         if not wltID=='':
            addr = self.main.walletMap[wltID].addrMap[addr160]
            typ = 'Imported' if addr.chainIndex==-2 else 'Permanent'
            msg = ('The key you entered is already part of another wallet you own:'
                   '<br><br>'
                   '<b>Address</b>: ' + addrStr + '<br>'
                   '<b>Wallet ID</b>: ' + wltID + '<br>'
                   '<b>Wallet Name</b>: ' + self.main.walletMap[wltID].labelName + '<br>'
                   '<b>Address Type</b>: ' + typ + 
                   '<br><br>'
                   'Armory cannot properly display balances or create transactions '
                   'when the same address is in multiple wallets at once.  ')
            if typ=='Imported':
               QMessageBox.critical(self, 'Duplicate Addresses', \
                  msg + 'To import this address to this wallet, please remove it from the '
                  'other wallet, then try the import operation again.', QMessageBox.Ok)
            else:
               QMessageBox.critical(self, 'Duplicate Addresses', \
                  msg + 'Additionally, this address is mathematically linked '
                  'to its wallet (permanently) and cannot be deleted or '
                  'imported to any other wallet.  The import operation cannot '
                  'continue.', QMessageBox.Ok)
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

         #######################################################################
         if TheBDM.getBDMState()=='BlockchainReady':
            nblk = TheBDM.numBlocksToRescan(self.wlt.cppWallet, wait=True)
            if nblk<2016:
               self.wlt.syncWithBlockchain(0)
               QMessageBox.information(self, 'Import Successful', \
                  'The address was imported into your wallet successfully, and '
                  'all the information needed to acquire its balance was already '
                  'available without rescanning the global transaction history. '
                  'The address will appear in the address list of this wallet.', \
                  QMessageBox.Ok)

            else:
               doRescanNow = QMessageBox.question(self, 'Rescan Needed', \
                  'The address was imported successfully, but your wallet balance '
                  'will be incorrect until the global transaction history is '
                  'searched for previous transactions.  Armory must go into offline '
                  'mode for a several minutes while this scan is performed.'
                  '<br><br>'
                  'Would you like to do the scan now?   Pressing "No" will allow '
                  'you to stay in online mode, but your balances may be incorrect '
                  'until you press the rescan button on the dashboard, or restart '
                  'Armory.', QMessageBox.Yes | QMessageBox.No)
               if doRescanNow == QMessageBox.Yes:
                  LOGINFO('User requested rescan immediately after import')
                  self.main.startRescanBlockchain()
               else:
                  LOGINFO('User requested no rescan after import.  Should be dirty.')
               self.main.setDashboardDetails()
                  
         #######################################################################
         elif TheBDM.getBDMState()=='Scanning':
            warnMsg = ( \
               'The address was imported successfully, but your wallet balance '
               'will be incorrect until the global transaction history is '
               'searched for previous transactions.  Armory is currently in the '
               'middle of a blockchain scan, but it will start another scan as '
               'soon as this one is complete.  Wallet and address balances will '
               'not be available until these operations are completed.', \
               QMessageBox.Ok)
            self.main.startRescanBlockchain()
            self.main.setDashboardDetails()


         self.main.walletListChanged()

      
      try:
         self.parent.wltAddrModel.reset()
      except:
         pass

      self.accept()


   #############################################################################
   def processMultiKey(self):
      thisWltID = self.wlt.uniqueIDB58

      inputText = str(self.txtPrivBulk.toPlainText())
      inputLines = [s.strip().replace(' ','') for s in inputText.split('\n')]
      binKeyData, addr160, addrStr = '','',''

      privKeyList = []
      addrSet = set()
      nLines = 0
      for line in inputLines:
         if 'PublicX' in line or 'PublicY' in line:
            continue
         lineend = line.split(':')[-1]
         try:
            nLines += 1
            binKeyData = SecureBinaryData(parsePrivateKeyData(lineend)[0])
            addr160 = convertKeyDataToAddress(privKey=binKeyData.toBinStr())
            if not addr160 in addrSet:
               addrSet.add(addr160)
               addrStr = hash160_to_addrStr(addr160)
               privKeyList.append([addr160, addrStr, binKeyData])
         except:
            LOGWARN('Key line skipped, probably not a private key (key not shown for security)')
            continue

      if len(privKeyList)==0:
         if nLines>1:
            QMessageBox.critical(self, 'Invalid Data', \
               'No valid private key data was entered.', QMessageBox.Ok )
         return

      #privKeyList now contains:
      #  [ [A160, AddrStr, Priv],
      #    [A160, AddrStr, Priv], 
      #    [A160, AddrStr, Priv], ... ]
      # Determine if any addresses are already part of some wallets  
      addr_to_wltID = lambda a: self.main.getWalletForAddr160(a)
      allWltList = [ [addr_to_wltID(k[0]), k[1]] for k in privKeyList]
      # allWltList is now [ [WltID, AddrStr], [WltID, AddrStr], ... ]

      
      if self.radioSweep.isChecked():
         ##### SWEEPING #####
         dupeWltList = filter(lambda a: len(a[0])>0, allWltList)
         if len(dupeWltList)>0:
            reply = QMessageBox.critical(self, 'Duplicate Addresses!', \
               'You are attempting to sweep %d addresses, but %d of them '
               'are already part of existing wallets.  That means that some or '
               'all of the bitcoins you sweep may already be owned by you. '
               '<br><br>'
               'Would you like to continue anyway?' % \
               (len(allWltList), len(dupeWltList)), \
               QMessageBox.Ok | QMessageBox.Cancel)
            if reply==QMessageBox.Cancel:
               return
         
   
         cppWlt = Cpp.BtcWallet()
         for addr160,addrStr,SecurePriv in privKeyList:
            cppWlt.addAddress_1_(addr160)

         
         # If we got here, let's go ahead and sweep!
         addrList = []
         for addr160,addrStr,SecurePriv in privKeyList:
            pyAddr = PyBtcAddress().createFromPlainKeyData(SecurePriv)
            addrList.append(pyAddr)

         targAddr160 = self.wlt.getNextUnusedAddress().getAddr160()
         self.main.confirmSweepScan(addrList, targAddr160)


      else:
         ##### IMPORTING #####

         # allWltList is [ [WltID, AddrStr], [WltID, AddrStr], ... ]

         # Warn about addresses that would be duplicates.
         # Addresses already in the selected wallet will simply be skipped, no 
         # need to do anything about that -- only addresses that would appear in 
         # two wlts if we were to continue.
         dupeWltList = filter(lambda a: (len(a[0])>0 and a[0]!=thisWltID), allWltList)
         if len(dupeWltList)>0:
            dupeAddrStrList = [d[1] for d in dupeWltList]
            dlg = DlgDuplicateAddr(dupeAddrStrList, self, self.main)

            if not dlg.exec_():
               return
   
            privKeyList = filter(lambda x: (x[1] not in dupeAddrStrList), privKeyList)
      

         # Confirm import
         addrStrList = [k[1] for k in privKeyList]
         dlg = DlgConfirmBulkImport(addrStrList, thisWltID, self, self.main)
         if not dlg.exec_():
            return
   
         if self.wlt.useEncryption and self.wlt.isLocked:
            # Target wallet is encrypted...
            unlockdlg = DlgUnlockWallet(self.wlt, self, self.main, 'Unlock Wallet to Import')
            if not unlockdlg.exec_():
               QMessageBox.critical(self, 'Wallet is Locked', \
                  'Cannot import private keys without unlocking wallet!', \
                  QMessageBox.Ok)
               return
   
         
         nTotal = 0
         nImport = 0
         nAlready = 0
         nError  = 0
         for addr160,addrStr,sbdKey in privKeyList:
            nTotal += 1 
            try:
               prevPartOfWallet = self.main.getWalletForAddr160(addr160)
               if not self.main.getWalletForAddr160(addr160)==thisWltID:
                  self.wlt.importExternalAddressData(privKey=sbdKey)
                  nImport += 1
               else:
                  nAlready += 1
            except Exception,msg:
               #print '***ERROR importing:', addrStr
               #print '         Error Msg:', msg
               #nError += 1
               LOGERROR('Problem importing: %s: %s', addrStr, msg)
               raise
   

         if nAlready==nTotal:
            MsgBoxCustom(MSGBOX.Warning, 'Nothing Imported!', 'All addresses '
               'chosen to be imported are already part of this wallet. '
               'Nothing was imported.')
            return
         elif nImport==0 and nTotal>0:
            MsgBoxCustom(MSGBOX.Error,'Error!', 'Failed:  No addresses could be imported. '
               'Please check the logfile (ArmoryQt.exe.log) or the console output '
               'for information about why it failed (and email alan.reiner@gmail.com '
               'for help fixing the problem).')
            return
         else:
            if nError == 0:
               if nAlready>0:
                  MsgBoxCustom(MSGBOX.Good, 'Success!', \
                     'Success: %d private keys were imported into your wallet. ' 
                     '<br><br>'
                     'The other %d private keys were skipped, because they were '
                     'already part of your wallet.' % (nImport, nAlready))
               else:
                  MsgBoxCustom(MSGBOX.Good, 'Success!', \
                     'Success: %d private keys were imported into your wallet.' % nImport)
            else:
               MsgBoxCustom(MSGBOX.Warning, 'Partial Success!', \
                  '%d private keys were imported into your wallet, but there was '
                  'also %d addresses that could not be imported (see console '
                  'or log file for more information).  It is safe to try this '
                  'operation again: all addresses previously imported will be '
                  'skipped. %s' % (nImport, nError, restartMsg))
   

         #######################################################################
         if TheBDM.getBDMState()=='BlockchainReady':
            nblk = TheBDM.numBlocksToRescan(self.wlt.cppWallet, wait=True)
            if nblk<2016:
               self.wlt.syncWithBlockchain(0)
               QMessageBox.information(self, 'Import Successful', \
                  'The addresses were imported into your wallet successfully, and '
                  'all the information needed to acquire their balances were already '
                  'available without executing a rescan.  '
                  'The address will appear in the address list of this wallet.', \
                  QMessageBox.Ok)

            else:
               doRescanNow = QMessageBox.question(self, 'Rescan Needed', \
                  'The addresses were imported successfully, but your wallet balance '
                  'will be incorrect until the global transaction history is '
                  'searched for previous transactions.  Armory must go into offline '
                  'mode for a several minutes while this scan is performed.'
                  '<br><br>'
                  'Would you like to do the scan now?   Pressing "No" will allow '
                  'you to stay in online mode, but your balances may be incorrect '
                  'until you press the rescan button on the dashboard, or restart '
                  'Armory', QMessageBox.Yes | QMessageBox.No)
               if doRescanNow==QMessageBox.Yes:
                  LOGINFO('User requested rescan immediately after import')
                  self.main.startRescanBlockchain()
               else:
                  LOGINFO('User requested no rescan after import.  Should be dirty.')
               self.main.setDashboardDetails()
                  
         #######################################################################
         elif TheBDM.getBDMState()=='Scanning':
            warnMsg = ( \
               'The addresses were imported successfully, but your wallet balance '
               'will be incorrect until the global transaction history is '
               'searched for previous transactions.  Armory is currently in the '
               'middle of a blockchain scan, but it will start another scan as '
               'soon as this one is complete.  Wallet and address balances will '
               'not be available until these operations are completed.', \
               QMessageBox.Ok)
            self.main.startRescanBlockchain()
            self.main.setDashboardDetails()
   

      try:
         self.main.walletListChanged()
      except:
         pass

      try:
         self.parent.wltAddrModel.reset()
      except AttributeError:
         pass

      self.accept()
       

#############################################################################
class DlgVerifySweep(ArmoryDialog):
   def __init__(self, inputStr, outputStr, outVal, fee, parent=None, main=None):
      super(DlgVerifySweep, self).__init__(parent, main)


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
      lblWarnImg.setPixmap(QPixmap(':/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

      layout = QHBoxLayout()
      layout.addWidget(lblWarnImg)
      layout.addWidget(makeLayoutFrame('Vert',[lblQuestion, frm, lblFinalConfirm, bbox]))
      self.setLayout(layout)

      self.setWindowTitle('Confirm Sweep')



#############################################################################
class DlgImportWallet(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgImportWallet, self).__init__(parent, main)
      self.setAttribute(Qt.WA_DeleteOnClose)

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
      #layout.addWidget(self.btnMigrate,     3,0, 1, 2); layout.addWidget(ttip3, 3,2,1,1)

      if self.main.usermode in (USERMODE.Advanced, USERMODE.Expert):
         lbl = QRichLabel('You can manually add wallets to armory by copying them '
                      'into your application directory then restarting Armory: '
                      '\n\n%s' % ARMORY_HOME_DIR, doWrap=True)
         lbl.setWordWrap(True)
         layout.addWidget(lbl, 4,0, 1, 2); 

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
#### Migration no longer is supported -- not until the new wallet format
#### is created that supports compressed public keys
#
#class DlgMigrateSatoshiWallet(ArmoryDialog):
#   def __init__(self, parent=None, main=None):
#      super(DlgMigrateSatoshiWallet, self).__init__(parent, main)
#
#
#      lblDescr = QRichLabel( \
#         'Specify the location of your regular Bitcoin wallet (wallet.dat) '
#         'to be migrated into an Armory wallet.  All private '
#         'keys will be imported, giving you full access to those addresses, as '
#         'if Armory had generated them natively.'
#         '<br><br>'
#         '<b>NOTE:</b> It is strongly recommended that all '
#         'Bitcoin addresses be used in only one program at a time.  If you '
#         'import your entire wallet.dat, it is recommended to stop using the '
#         'regular Bitcoin client, and only use Armory to send transactions.  '
#         'Armory developers will not be responsible for coins getting "locked" '
#         'or "stuck" due to multiple applications attempting to spend coins '
#         'from the same addresses.')
#
#      lblSatoshiWlt = QRichLabel('Wallet File to be Migrated (typically ' +
#                                 os.path.join(BTC_HOME_DIR, 'wallet.dat') + ')', doWrap=False)
#      ttipWlt = createToolTipObject(\
#         'This is the wallet file used by the standard Bitcoin client from '
#         'bitcoin.org.  It contains all the information needed for Armory to '
#         'know how to access the bitcoins maintained by that program')
#      self.txtWalletPath = QLineEdit()
#
#
#
#      self.chkAllKeys = QCheckBox('Include Address Pool (unused keys)')
#      ttipAllKeys = createToolTipObject( \
#         'The wallet.dat file typically '
#         'holds a pool of 100 addresses beyond the ones you ever used. '
#         'These are the next 100 addresses to be used by the main Bitcoin '
#         'client for the next 100 transactions.  '
#         'If you are planning to switch to Armory exclusively, you will not '
#         'need these addresses')
#
#      self.chkAllKeys.setChecked(True)
#      if self.main.usermode in (USERMODE.Standard,):
#         self.chkAllKeys.setVisible(False)
#         self.ttipAllKeys.setVisible(False)
#
#      btnGetFilename = QPushButton('Find...')
#      self.connect(btnGetFilename, SIGNAL('clicked()'), self.getSatoshiFilename)
#
#      defaultWalletPath = os.path.join(BTC_HOME_DIR,'wallet.dat')
#      if os.path.exists(defaultWalletPath):
#         self.txtWalletPath.setText(defaultWalletPath)
#
#      buttonBox = QDialogButtonBox()
#      self.btnAccept = QPushButton("Import")
#      self.btnReject = QPushButton("Cancel")
#      self.connect(self.btnAccept, SIGNAL('clicked()'), self.execMigrate)
#      self.connect(self.btnReject, SIGNAL('clicked()'), self.reject)
#      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
#      buttonBox.addButton(self.btnReject, QDialogButtonBox.RejectRole)
#
#
#      # Select the wallet into which you want to import
#      lblWltDest = QRichLabel('Migrate Addresses to which Wallet?', doWrap=False)
#      self.wltidlist = [''] 
#      self.lstWallets = QListWidget()
#      self.lstWallets.addItem(QListWidgetItem('New Wallet...'))
#      for wltID in self.main.walletIDList:
#         wlt = self.main.walletMap[wltID]
#         wlttype = determineWalletType(self.main.walletMap[wltID], self.main)[0]
#         if wlttype in (WLTTYPES.WatchOnly, WLTTYPES.Offline):
#            continue
#         self.lstWallets.addItem( \
#                QListWidgetItem('%s (%s)' % (wlt.labelName, wltID) ))
#         self.wltidlist.append(wltID)
#      self.lstWallets.setCurrentRow(0)
#      self.connect(self.lstWallets, SIGNAL('currentRowChanged(int)'), self.wltChange)
#
#
#      self.lblDescrNew = QRichLabel( '' )
#      self.lblDescrNew.setAlignment(Qt.AlignTop)
#      self.wltChange(0)
#      
#
#      dlgLayout = QVBoxLayout()
#      dlgLayout.addWidget(lblDescr)
#      dlgLayout.addWidget(HLINE())
#      dlgLayout.addWidget(makeHorizFrame([lblSatoshiWlt, ttipWlt, 'Stretch']))
#      dlgLayout.addWidget(makeHorizFrame([self.txtWalletPath, btnGetFilename]))
#      dlgLayout.addWidget(makeHorizFrame([self.chkAllKeys, ttipAllKeys, 'Stretch']))
#      dlgLayout.addWidget(HLINE())
#      dlgLayout.addWidget(makeHorizFrame([lblWltDest, 'Stretch']))
#      dlgLayout.addWidget(makeHorizFrame([self.lstWallets, self.lblDescrNew,'Stretch']))
#      dlgLayout.addWidget(HLINE())
#      dlgLayout.addWidget(buttonBox)
#
#      self.setLayout(dlgLayout)
#
#      self.setMinimumWidth(500)
#      self.setWindowTitle('Migrate Bitcoin-Qt Wallet')
#      self.setWindowIcon(QIcon( self.main.iconfile))
#
#
#   def getSatoshiFilename(self):
#      # Temporarily reset the "LastDir" to where the default wallet.dat is
#      prevLastDir = self.main.settings.get('LastDirectory')
#      self.main.writeSetting('LastDirectory', BTC_HOME_DIR)
#      satoshiWltFile = self.main.getFileLoad('Load Bitcoin Wallet File', \
#                                             ['Bitcoin Wallets (*.dat)'])
#      self.main.writeSetting('LastDirectory', prevLastDir)
#      if len(str(satoshiWltFile))>0:
#         self.txtWalletPath.setText(satoshiWltFile)
#      
#
#   def wltChange(self, row):
#      if row==0:
#         self.lblDescrNew.setText( \
#           'If your wallet.dat is encrypted, the new Armory wallet will also '
#           'be encrypted, and with the same passphrase.  If your wallet.dat '
#           'is not encrypted, neither will the new Armory wallet.  Encryption '
#           'can always be added, changed or removed on any wallet.')
#      else:
#         self.lblDescrNew.setText( '' )
#
#   def execMigrate(self):
#      satoshiWltFile = str(self.txtWalletPath.text())
#      if not os.path.exists(satoshiWltFile):
#         QMessageBox.critical(self, 'File does not exist!', \
#            'The specified file does not exist:\n\n' + satoshiWltFile,
#            QMessageBox.Ok)
#         return
#
#      selectedRow = self.lstWallets.currentRow()
#      toWalletID = None
#      if selectedRow>0:
#         toWalletID = self.wltidlist[selectedRow]
#         
#
#
#      # Critical to avoid wallet corruption!!
#      base,fn = os.path.split(satoshiWltFile)
#      nm,ext = os.path.splitext(fn)
#      satoshiWltFileCopy = os.path.join(ARMORY_HOME_DIR, nm+'_temp_copy'+ext)
#      shutil.copy(satoshiWltFile, satoshiWltFileCopy)
#      if not os.path.exists(satoshiWltFileCopy):
#         raise FileExistsError, 'There was an error creating a copy of wallet.dat'
#
#      # KeyList is [addrB58, privKey, usedYet, acctName]
#      # This block will not only decrypt the Satoshi wallet, but also catch
#      # if the user specified a wallet.dat for a different network!
#      keyList = []
#      satoshiPassphrase = None
#      satoshiWltIsEncrypted  = checkSatoshiEncrypted(satoshiWltFileCopy)
#
#      if not satoshiWltIsEncrypted:
#         try:
#            keyList = extractSatoshiKeys(satoshiWltFileCopy)
#         except NetworkIDError:
#            QMessageBox.critical(self, 'Wrong Network!', \
#               'The specified wallet.dat file is for a different network! '
#               '(you are on the ' + NETWORKS[ADDRBYTE] + ')', \
#               QMessageBox.Ok)
#            LOGERROR('Wallet is for the wrong network!')
#            return
#      else:
#         correctPassphrase = False
#         firstAsk = True
#         while not correctPassphrase:
#            # Loop until we get a valid passphrase
#            redText = ''
#            if not firstAsk:
#               redText = '<font color=%s>Incorrect passphrase.</font><br><br>' % htmlColor('TextRed')
#            firstAsk = False
#
#            dlg = DlgGenericGetPassword( \
#                redText + 'The wallet.dat file you specified is encrypted.  '
#                'Please provide the passphrase to decrypt it.', self, self.main)
#
#            if not dlg.exec_():
#               return
#            else:
#               satoshiPassphrase = SecureBinaryData(str(dlg.edtPasswd.text()))
#               try:
#                  keyList = extractSatoshiKeys(satoshiWltFileCopy, satoshiPassphrase)
#                  correctPassphrase = True
#               except EncryptionError:
#                  pass
#               except NetworkIDError:
#                  QMessageBox.critical(self, 'Wrong Network!', \
#                     'The specified wallet.dat file is for a different network! '
#                     '(you are on the ' + NETWORKS[ADDRBYTE] + ')', \
#                     QMessageBox.Ok)
#                  LOGERROR('Wallet is for the wrong network!')
#                  return
#
#      # We're done accessing the file, delete the
#      os.remove(satoshiWltFileCopy)
#      
#      if not self.chkAllKeys.isChecked():
#         keyList = filter(lambda x: x[2], keyList)
#
#
#      # Warn about addresses that would be duplicates.
#      # This filters the list down to addresses already in a wallet that isn't selected
#      # Addresses already in the selected wallet will simply be skipped, no need to 
#      # do anything about that
#      addr_to_wltID = lambda a: self.main.getWalletForAddr160(addrStr_to_hash160(a))
#      allWltList = [[addr_to_wltID(k[0]), k[0]] for k in keyList]
#      dupeWltList = filter(lambda a: (len(a[0])>0 and a[0]!=toWalletID), allWltList)
#
#      if len(dupeWltList)>0:
#         dlg = DlgDuplicateAddr([d[1].ljust(40)+d[0] for d in dupeWltList], self, self.main)
#         didAccept = dlg.exec_()
#         if not didAccept or dlg.doCancel:
#            return
#   
#         if dlg.newOnly:
#            dupeAddrList = [a[1] for a in dupeWltList]
#            keyList = filter(lambda x: (x[0] not in dupeAddrList), keyList)
#         elif dlg.takeAll:
#            pass # we already have duplicates in the list, leave them
#      
#
#      # Confirm import
#      addrList = [k[0].ljust(40)+k[3] for k in keyList]
#      dlg = DlgConfirmBulkImport(addrList, toWalletID, self, self.main)
#      if not dlg.exec_():
#         return
#         
#      # Okay, let's do it!  Get a wallet, unlock it if necessary, create if desired
#      wlt = None
#      if toWalletID==None:
#         lblShort = 'Migrated wallet.dat'
#         lblLong  = 'Wallet created to hold addresses from the regular Bitcoin wallet.dat.'
#
#         if not satoshiPassphrase:
#            wlt = PyBtcWallet().createNewWallet(    \
#                               withEncrypt=False,   \
#                               shortLabel=lblShort, \
#                               longLabel=lblLong)
#                                                     
#         else:
#            lblLong += ' (encrypted using same passphrase as the original wallet)'
#            wlt = PyBtcWallet().createNewWallet( \
#                               withEncrypt=True, \
#                               securePassphrase=satoshiPassphrase, \
#                               shortLabel=lblShort, \
#                               longLabel=lblLong)
#            wlt.unlock(securePassphrase=satoshiPassphrase)
#
#
#      else:
#         wlt = self.main.walletMap[toWalletID]
#         if wlt.useEncryption and wlt.isLocked:
#            # Target wallet is encrypted...
#            unlockdlg = DlgUnlockWallet(wlt, self, self.main, 'Unlock Wallet to Import')
#            if not unlockdlg.exec_():
#               QMessageBox.critical(self, 'Wallet is Locked', \
#                  'Cannot import private keys without unlocking wallet!', \
#                  QMessageBox.Ok)
#               return
#
#      
#      self.nImport = 0
#      self.nError  = 0
#      def finallyDoMigrate():
#         for i,key4 in enumerate(keyList):
#            addrB58, sbdKey, isUsed, addrName = key4[:]
#            try:
#               a160 = addrStr_to_hash160(addrB58)
#               wlt.importExternalAddressData(privKey=sbdKey)
#               cmt = 'Imported #%03d'%i
#               if len(addrName)>0:
#                  cmt += ': %s' % addrName
#               wlt.setComment(a160, cmt)
#               self.nImport += 1
#            except Exception,msg:
#               LOGERROR('Problem importing: %s: %s', addrB58, msg)
#               self.nError += 1
#
#
#      DlgExecLongProcess(finallyDoMigrate, "Migrating Bitcoin-Qt Wallet", self, self.main).exec_()
#
#
#      if self.nImport==0:
#         MsgBoxCustom(MSGBOX.Error,'Error!', 'Failed:  No addresses could be imported. '
#            'Please check the logfile (ArmoryQt.exe.log) or the console output '
#            'for information about why it failed (and email alan.reiner@gmail.com '
#            'for help fixing the problem).')
#      else:
#         if self.nError == 0:
#            MsgBoxCustom(MSGBOX.Good, 'Success!', \
#               'Success: %d private keys were imported into your wallet.' % self.nImport)
#         else:
#            MsgBoxCustom(MSGBOX.Warning, 'Partial Success!', \
#               '%d private keys were imported into your wallet, but there was '
#               'also %d addresses that could not be imported (see console '
#               'or log file for more information).  It is safe to try this '
#               'operation again: all addresses previously imported will be '
#               'skipped. %s' % (self.nImport, self.nError, restartMsg))
#      
#      if self.main.blkMode==BLOCKCHAINMODE.Full:
#         ##########################################################################
#         warnMsg = ( \
#            'Would you like to rescan the blockchain for all the addresses you '
#            'just migrated?  This operation can take between 5 seconds to 3 minutes '
#            'depending on your system.  If you skip this operation, it will be '
#            'performed the next time you restart Armory. Wallet balances may '
#            'be incorrect until then.')
#         waitMsg = 'Searching the global transaction history'
#         
#         self.main.isDirty() = True
#         if self.main.BDM_SyncCppWallet_Confirm(wlt.cppWallet, warnMsg, waitMsg):
#            self.main.safeAddWallet(wlt.cppWallet)
#            #TheBDM.registerWallet(wlt.cppWallet)
#            #wlt.syncWithBlockchain(0)
#         else:
#         ##########################################################################
#
#      self.main.addWalletToApplication(wlt, walletIsNew=False)
#
#      self.main.walletListChanged()
#      self.accept()
#      
#         
         

         
            
         


##############################################################################
class DlgConfirmBulkImport(ArmoryDialog):
   def __init__(self, addrList, wltID, parent=None, main=None):
      super(DlgConfirmBulkImport, self).__init__(parent, main)

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
class DlgDuplicateAddr(ArmoryDialog):
   def __init__(self, addrList, wlt, parent=None, main=None):
      super(DlgDuplicateAddr, self).__init__(parent, main)

      self.wlt    = wlt 
      self.doCancel = True
      self.newOnly  = False

      if len(addrList)==0:
         QMessageBox.warning(self, 'No Addresses to Import', \
           'There are no addresses to import!', QMessageBox.Ok)
         self.reject()

      lblDescr = QRichLabel( \
         '<font color=%s>Duplicate addresses detected!</font> The following '
         'addresses already exist in other Armory wallets:' % htmlColor('TextWarn'))

      fnt = GETFONT('Fixed',8)
      w,h = tightSizeNChar(fnt, 50)
      txtDispAddr = QTextEdit()
      txtDispAddr.setFont(fnt)
      txtDispAddr.setReadOnly(True)
      txtDispAddr.setMinimumWidth(w)
      txtDispAddr.setMinimumHeight(8.2*h)
      txtDispAddr.setText( '\n'.join(addrList) )

      lblWarn = QRichLabel( \
         'Duplicate addresses cannot be imported.  If you continue, '
         'the addresses above will be ignored, and only new addresses '
         'will be imported to this wallet.')

      buttonBox = QDialogButtonBox()
      self.btnContinue = QPushButton("Continue")
      self.btnCancel   = QPushButton("Cancel")
      self.connect(self.btnContinue, SIGNAL('clicked()'), self.accept)
      self.connect(self.btnCancel,   SIGNAL('clicked()'), self.reject)
      buttonBox.addButton(self.btnContinue, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel,  QDialogButtonBox.RejectRole)

      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(lblDescr)
      dlgLayout.addWidget(txtDispAddr)
      dlgLayout.addWidget(lblWarn)
      dlgLayout.addWidget(buttonBox)
      self.setLayout(dlgLayout)

      self.setWindowTitle('Duplicate Addresses')




#############################################################################
class DlgAddressInfo(ArmoryDialog):
   def __init__(self, wlt, addr160, parent=None, main=None, mode=None):
      super(DlgAddressInfo, self).__init__(parent, main)

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
      if mode in (USERMODE.Advanced, USERMODE.Expert):
         bin25   = base58_to_binary(addrStr)
         lbls.append([])
         lbls[-1].append( createToolTipObject( 'This is the computer-readable form of the address'))
         lbls[-1].append( QRichLabel('<b>Public Key Hash</b>') )
         h160Str = binary_to_hex(bin25[1:-4])
         if mode==USERMODE.Expert:
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
         goodColor = htmlColor('MoneyPos')
         lbls[-1].append( QRichLabel( \
            '<font color=' + goodColor + '>' + balStr.strip() + '</font> BTC' ))
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
            if (i,j)==(0,2):
               frmInfoLayout.addWidget(lbls[i][j], i,j, 1,2)
            else:
               frmInfoLayout.addWidget(lbls[i][j], i,j, 1,1)

      qrcode = QRCodeWidget(addrStr, 80, parent=self)
      qrlbl = QRichLabel('<font size=2>Double-click to inflate</font>')
      frmqr = makeVertFrame([qrcode, qrlbl])

      frmInfoLayout.addWidget(frmqr,  0,4, len(lbls),1)
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
      self.ledgerView.hideColumn(LEDGERCOLS.isCoinbase)
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
      #lbtnSweepA   = QLabelButton('Sweep Address')
      lbtnDelete   = QLabelButton('Delete Address')

      self.connect(lbtnCopyAddr, SIGNAL('clicked()'), self.copyAddr)
      self.connect(lbtnMkPaper,  SIGNAL('clicked()'), self.makePaper)
      self.connect(lbtnViewKeys, SIGNAL('clicked()'), self.viewKeys)
      #self.connect(lbtnSweepA,   SIGNAL('clicked()'), self.sweepAddr)
      self.connect(lbtnDelete,   SIGNAL('clicked()'), self.deleteAddr)

      optFrame = QFrame()
      optFrame.setFrameStyle(STYLE_SUNKEN)

      hasPriv = self.addr.hasPrivKey()
      adv = (self.main.usermode in (USERMODE.Advanced, USERMODE.Expert))
      watch = self.wlt.watchingOnly


      self.lblCopied = QRichLabel('')
      self.lblCopied.setMinimumHeight(tightSizeNChar(self.lblCopied, 1)[1])

      self.lblLedgerWarning = QRichLabel( \
         'NOTE:  The ledger shows each transaction <i><b>input</b></i> and '
         '<i><b>output</b></i> for this address.  There are typically many '
         'inputs and outputs for each transaction, therefore the entries '
         'represent only partial transactions.  Do not worry if these entries '
         'do not look familiar.')


      optLayout = QVBoxLayout()
      if True:           optLayout.addWidget(lbtnCopyAddr)
      if adv:            optLayout.addWidget(lbtnViewKeys)

      #if not watch:      optLayout.addWidget(lbtnSweepA)
      #if adv:            optLayout.addWidget(lbtnDelete)

      if False:          optLayout.addWidget(lbtnMkPaper)  
      if True:           optLayout.addStretch()
      if True:           optLayout.addWidget(self.lblCopied)

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
      # This is broken, and I don't feel like fixing it because it's not very
      # useful.  Maybe some time in the future it will be resolved.
      return
      """ 
      if self.wlt.useEncryption and self.wlt.isLocked:
         unlockdlg = DlgUnlockWallet(self.wlt, self, self.main, 'Sweep Address')
         if not unlockdlg.exec_():
            QMessageBox.critical(self, 'Wallet is Locked', \
               'Cannot sweep an address while its keys are locked.', \
               QMessageBox.Ok)
            return

      addrToSweep = self.addr.copy()
      targAddr160 = self.wlt.getNextUnusedAddress().getAddr160()

      #######################################################################
      #  This is the part that may take a while.  Verify user will wait!
      #  The sync/confirm call guarantees that the next sync call will 
      #  return instantaneously with the correct answer.  This only stops
      #  being true when more addresses or wallets are imported.
      if not self.main.BDM_SyncAddressList_Confirm(addrToSweep):
         return
      #######################################################################
      finishedTx, outVal, fee = self.main.createSweepAddrTx(addrToSweep, targAddr160)

      if outVal<=fee:
         QMessageBox.critical(self, 'Cannot sweep',\
         'You cannot sweep the funds from this address, because the '
         'transaction fee would be equal to or greater than the amount '
         'swept.', QMessageBox.Ok)
         return

      if outVal==0:
         print 'NO FUNDS'
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
         self.main.broadcastTransaction(finishedTx, dryRun=False)
      """ 

   def deleteAddr(self):
      pass


#############################################################################
class DlgShowKeys(ArmoryDialog):

   def __init__(self, addr, parent=None, main=None):
      super(DlgShowKeys, self).__init__(parent, main)

      self.addr   = addr

      
      lblWarn = QRichLabel('')
      plainPriv = False
      if addr.binPrivKey32_Plain.getSize()>0:
         plainPriv = True
         lblWarn = QRichLabel( \
            '<font color=%s><b>Warning:</b> the unencrypted private keys '
            'for this address are shown below.  They are "private" because '
            'anyone who obtains them can spend the money held '
            'by this address.  Please protect this information the '
            'same as you protect your wallet.</font>' % htmlColor('TextWarn'))
      warnFrm = makeLayoutFrame('Horiz', [lblWarn])

      endianness = self.main.getSettingOrSetDefault('PrefEndian', BIGENDIAN)
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
         b58Key = encodePrivKeyBase58(binKey)
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
class DlgEULA(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgEULA, self).__init__(parent, main)

      txtWidth,txtHeight = tightSizeNChar(self, 110)
      txtLicense = QTextEdit()
      txtLicense.sizeHint = lambda: QSize(txtWidth, 14*txtHeight)
      txtLicense.setReadOnly(True)

      from LICENSE import licenseText
      txtLicense.setText(licenseText())
   
      self.chkAgree = QCheckBox('I agree to all the terms of the license above')

      self.btnCancel = QPushButton("Cancel")
      self.btnAccept = QPushButton("Accept")
      self.btnAccept.setEnabled(False)
      self.connect(self.btnCancel, SIGNAL('clicked()'),     self.reject)
      self.connect(self.btnAccept, SIGNAL('clicked()'),     self.accept)
      self.connect(self.chkAgree,  SIGNAL('toggled(bool)'), self.toggleChkBox)
      btnBox = makeHorizFrame(['Stretch', self.btnCancel, self.btnAccept])


      lblPleaseAgree = QRichLabel( \
         '<b>Armory Bitcoin Client is licensed under the <i>Affero General '
         'Public License, Version 3 (AGPLv3)</i></b>'
         '<br><br>'
         'Additionally, as a condition of receiving this software '
         'for free, you accept all risks associated with using it '
         'and the developers of Armory will not be held liable for any '
         'loss of money or bitcoins due to software defects.'
         '<br><br>'
         '<b>Please read the full terms of the license and indicate your '
         'agreement with its terms.</b>')


      dlgLayout = QVBoxLayout()
      frmChk = makeHorizFrame([self.chkAgree, 'Stretch'])
      frmBtn = makeHorizFrame(['Stretch', self.btnCancel, self.btnAccept])
      frmAll = makeVertFrame([lblPleaseAgree, txtLicense, frmChk, frmBtn])

      dlgLayout.addWidget(frmAll)
      self.setLayout(dlgLayout)
      self.setWindowTitle('Armory License Agreement')
      self.setWindowIcon(QIcon(self.main.iconfile))


   def reject(self):
      self.main.abortLoad = True
      LOGERROR('User did not accept the EULA')
      super(DlgEULA, self).reject()
      
   def accept(self):
      self.main.writeSetting('Agreed_to_EULA', True) 
      super(DlgEULA, self).accept()

   def toggleChkBox(self, isEnabled):
      self.btnAccept.setEnabled(isEnabled)

#############################################################################
class DlgIntroMessage(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgIntroMessage, self).__init__(parent, main)


      lblInfoImg = QLabel()
      lblInfoImg.setPixmap(QPixmap(':/MsgBox_info48.png'))
      lblInfoImg.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
      lblInfoImg.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
      lblInfoImg.setMaximumWidth(50)

      lblWelcome = QRichLabel('<b>Welcome to Armory!</b>')
      lblWelcome.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWelcome.setFont(GETFONT('Var', 14))
      lblSlogan  = QRichLabel('<i>The most advanced Bitcoin Client on Earth!</i>')
      lblSlogan.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      lblDescr = QRichLabel( \
         '<b>You are about to use the most secure and feature-rich Bitcoin client '
         'software available!</b>  But please remember, this software '
         'is still <i>Beta</i> - Armory developers will not be held responsible '
         'for loss of bitcoins resulting from the use of this software.'
         '<br><br>'
         '<b>To use Armory online</b>, '
         'you must have Bitcoin-Qt (or bitcoind) open and synchronized '
         'with the Bitcoin network.  You can download Bitcoin-Qt from <a '
         'href=http://www.bitcoin.org>www.bitcoin.org</a>.  If you have '
         'never run Bitcoin-Qt before, you will need to wait '
         'for it to finish synchronizing before Armory '
         'will work.  <i>This may take many hours, but only needs to be done '
         'once!</i>  A green checkmark will appear in the '
         'bottom-right corner of the Bitcoin-Qt window when it is finished.'
         '<br><br>'
         'For more info about Armory, and Bitcoin itself, see '
         '<a href="http://'
         'bitcoinarmory.com/index.php/frequently-asked-questions">frequently '
         'asked questions</a>.')
      lblDescr.setOpenExternalLinks(True)
      
      lblContact = QRichLabel( \
         '<b>If you find this software useful, please consider pressing '
         'the "Donate" button on your next transaction!</b>')

      spacer = lambda: QSpacerItem(20,20, QSizePolicy.Fixed, QSizePolicy.Expanding)


      frmText = makeLayoutFrame('Vert', [lblWelcome,    spacer(), \
                                         lblDescr,      spacer(), \
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
         self.btnOkay = QPushButton("OK!")
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



  



#############################################################################
class DlgImportPaperWallet(ArmoryDialog):

   def __init__(self, parent=None, main=None):
      super(DlgImportPaperWallet, self).__init__(parent, main)

      self.wltDataLines = [[]]*4
      self.prevChars    = ['']*4

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
      self.labels[0].setText('Root Key:')
      self.labels[1].setText('')
      self.labels[2].setText('Chain Code:')
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

      self.chkEncrypt = QCheckBox('Encrypt Wallet')
      self.chkEncrypt.setChecked(True)

      bottomFrm = makeHorizFrame([self.chkEncrypt, buttonbox])
      layout.addWidget(bottomFrm,  6, 0, 1, 2)
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
            LOGERROR('Error in wallet restore field')
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
               newWltID + '\n\nYou already own this wallet! \n  '
               'Nothing to do...', QMessageBox.Ok)
         self.reject()
         return
         
      
      
      reply = QMessageBox.question(self, 'Verify Wallet ID', \
               'The data you entered corresponds to a wallet with a wallet ID: \n\n \t' +
               newWltID + '\n\nDoes this ID match the "Wallet Unique ID" ' 
               'printed on your paper backup?  If not, click "No" and reenter '
               'key and chain-code data again.', \
               QMessageBox.Yes | QMessageBox.No)
      if reply==QMessageBox.No:
         return

      passwd = []
      if self.chkEncrypt.isChecked():
         dlgPasswd = DlgChangePassphrase(self, self.main)
         if dlgPasswd.exec_():
            passwd = SecureBinaryData(str(dlgPasswd.edtPasswd1.text()))
         else:
            QMessageBox.critical(self, 'Cannot Encrypt', \
               'You requested your restored wallet be encrypted, but no '
               'valid passphrase was supplied.  Aborting wallet recovery.', \
               QMessageBox.Ok)
            return

      if passwd:
          self.newWallet = PyBtcWallet().createNewWallet( \
                                 plainRootKey=SecureBinaryData(privKey), \
                                 chaincode=SecureBinaryData(chain), \
                                 shortLabel='PaperBackup - %s'%newWltID, \
                                 withEncrypt=True, \
                                 securePassphrase=passwd, \
                                 kdfTargSec=0.25, \
                                 kdfMaxMem=32*1024*1024, \
                                 isActuallyNew=False, \
                                 doRegisterWithBDM=False)
      else:
         self.newWallet = PyBtcWallet().createNewWallet(  \
                                 plainRootKey=SecureBinaryData(privKey), \
                                 chaincode=SecureBinaryData(chain), \
                                 shortLabel='PaperBackup - %s'%newWltID, \
                                 withEncrypt=False,\
                                 isActuallyNew=False, \
                                 doRegisterWithBDM=False)

      def fillAddrPoolAndAccept():
         self.newWallet.fillAddressPool()
         self.accept()

      # Will pop up a little "please wait..." window while filling addr pool
      DlgExecLongProcess(fillAddrPoolAndAccept, "Recovering wallet...", self, self.main).exec_()
      



################################################################################
class DlgSetComment(ArmoryDialog):
   """ This will be a dumb dialog for retrieving a comment from user """

   #############################################################################
   def __init__(self, currcomment='', ctype='', parent=None, main=None):
      super(DlgSetComment, self).__init__(parent, main)


      self.setWindowTitle('Modify Comment')
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
   LOGERROR('QR-generation code not available...')

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
EASY16CHARS  = 'asdf ghjk wert uion'.replace(' ','')
hex_to_base16_map = {}
base16_to_hex_map = {}
for n,b in zip(NORMALCHARS,EASY16CHARS):
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

      self.setDefaultTextColor(QColor(0,0,0))

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
            #LOGWARN('Could not generate QR code for size %d (too much data?)', sz)
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
      painter.setBrush(QBrush(QColor(0,0,0)))

      for r in range(self.modCt):
         for c in range(self.modCt):
            if (self.qr.isDark(c, r) ):
               painter.drawRect(*[self.modSz*a for a in [r,c,1,1]])


class DlgRemoveWallet(ArmoryDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgRemoveWallet, self).__init__(parent, main)
      

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


      # TODO:  This should not *ever* require a blockchain scan, because all
      #        current wallets should already be registered and up-to-date.  
      #        But I should verify that this is actually the case.
      wltEmpty = True
      if TheBDM.getBDMState()=='BlockchainReady':
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
      lblWarnImg.setPixmap(QPixmap(':/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnImg2 = QLabel()
      lblWarnImg2.setPixmap(QPixmap(':/MsgBox_warning48.png'))
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
      if not self.main.usermode==USERMODE.Standard:
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
            QMessageBox.warning(self, 'Operation Aborted', \
              'You requested a paper backup before deleting the wallet, but '
              'clicked "Cancel" on the backup printing window.  So, the delete '
              'operation was canceled as well.',  QMessageBox.Ok)
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
         elif self.radioDelete.isChecked():
            reply = QMessageBox.warning(self, 'Are you absolutely sure?!?', \
            'Are you absolutely sure you want to permanently delete '
            'this wallet?  Unless this wallet is saved on another device '
            'you will permanently lose access to all the addresses in this '
            'wallet.', QMessageBox.Yes | QMessageBox.Cancel)
         elif self.radioWatch.isChecked():
            reply = QMessageBox.warning(self, 'Are you absolutely sure?!?', \
            '<i>This will permanently delete the information you need to spend '
            'funds from this wallet!</i>  You will only be able to receive '
            'coins, but not spend them.  Only do this if you have another copy '
            'of this wallet elsewhere, such as a paper backup or on an offline '
            'computer with the full wallet. ', QMessageBox.Yes | QMessageBox.Cancel)

         if reply==QMessageBox.Yes:

            thepath       = wlt.getWalletPath()
            thepathBackup = wlt.getWalletPath('backup')

            if self.radioWatch.isChecked():
               LOGINFO('***Converting to watching-only wallet')
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
               LOGINFO('***Completely deleting wallet')
               os.remove(thepath)
               os.remove(thepathBackup)
               self.main.removeWalletFromApplication(wltID) 
               self.main.statusBar().showMessage( \
                     'Wallet '+wltID+' was deleted!', 10000)

            self.parent.accept()
            self.accept()
         else:
            self.reject()


class DlgRemoveAddress(ArmoryDialog):
   def __init__(self, wlt, addr160, parent=None, main=None):
      super(DlgRemoveAddress, self).__init__(parent, main)

      
      if not wlt.hasAddr(addr160):
         raise WalletAddressError, 'Address does not exist in wallet!'

      if not wlt.getAddrByHash160(addr160).chainIndex==-2:
         raise WalletAddressError, ('Cannot delete regular chained addresses! '
                                   'Can only delete imported addresses.')


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
      if TheBDM.getBDMState()=='BlockchainReady':
         #wlt.syncWithBlockchain()
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
      lblWarnImg.setPixmap(QPixmap(':/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lblWarnImg2 = QLabel()
      lblWarnImg2.setPixmap(QPixmap(':/MsgBox_warning48.png'))
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
           'use it again, since any bitcoins sent to it will be '
           'inaccessible.\n\n '
           'If you are maintaining an external copy of this address '
           'please ignore this warning\n\n'
           'Are you absolutely sure you want to delete ' + 
           self.addr.getAddrStr() + '?', \
           QMessageBox.Yes | QMessageBox.Cancel)

      if reply==QMessageBox.Yes:
         self.wlt.deleteImportedAddress(self.addr.getAddr160())
         try:
            self.parent.wltAddrModel.reset()
            self.parent.setSummaryBalances()
         except AttributeError:
            pass
         self.accept()
         
      else:
         self.reject()



class DlgWalletSelect(ArmoryDialog):
   def __init__(self, parent=None, main=None,  title='Select Wallet:', \
                             descr='', firstSelect=None, onlyMyWallets=False, \
                             wltIDList=None, atLeast=0):
      super(DlgWalletSelect, self).__init__(parent, main)

      self.lstWallets = QListWidget()
      self.balAtLeast = atLeast

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


      # Start the layout
      layout = QVBoxLayout()

      if descr:
         layout.addWidget(makeHorizFrame([QRichLabel(descr)], STYLE_SUNKEN))
      layout.addWidget(QRichLabel('<b><u>'+title+'</u></b>'))


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
      btnAccept = QPushButton('OK')
      btnCancel = QPushButton('Cancel')
      self.connect(btnAccept, SIGNAL('clicked()'), self.accept)
      self.connect(btnCancel, SIGNAL('clicked()'), self.reject)
      buttonBox.addButton(btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(btnCancel, QDialogButtonBox.RejectRole)

      layout.addWidget(makeHorizFrame([self.lstWallets, frm]))
      layout.addWidget(buttonBox)

      layout.setSpacing(15)
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
      self.selectedID=wltID
      
      if not TheBDM.getBDMState()=='BlockchainReady':
         self.dispBal.setText('-'*12)
         return
      
      bal = wlt.getBalance('Spendable')
      balStr = coin2str(wlt.getBalance('Spendable'), maxZeros=1)
      if bal<=self.balAtLeast:
         self.dispBal.setText('<font color="red"><b>%s</b></font>' % balStr)
      else:
         self.dispBal.setText('<b>'+balStr+'</b>')


   def dblclick(self, *args):
      currRow = self.lstWallets.currentRow()
      self.selectedID = self.rowList[currRow][0]
      self.accept()






class DlgConfirmSend(ArmoryDialog):

   def __init__(self, wlt, recipValPairs, fee, parent=None, main=None, sendNow=False, changeBehave=None):
      super(DlgConfirmSend, self).__init__(parent, main)
      
      self.wlt    = wlt

      layout = QGridLayout()


      lblInfoImg = QLabel()
      lblInfoImg.setPixmap(QPixmap(':/MsgBox_info48.png'))
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
      recipLbls.append(QLabel( 'Total bitcoins : '.ljust(37)  +
                        coin2str(totalSend, rJust=True, maxZeros=4)))
      recipLbls[-1].setFont(GETFONT('Fixed'))

      lblLastConfirm = QLabel('Are you sure you want to execute this transaction?')

      if sendNow:
         self.btnAccept = QPushButton('Send')
      else:
         self.btnAccept = QPushButton('Continue')
         lblLastConfirm.setText('')


      # Acknowledge if the user has selected a non-std change location
      lblSpecialChange = QRichLabel('')
      if self.main.usermode==USERMODE.Expert and changeBehave:
         chngAddr160   = changeBehave[0]
         chngAddrStr   = hash160_to_addrStr(chngAddr160)
         chngBehaveStr = changeBehave[1]
         if chngBehaveStr=='Feedback':
            lblSpecialChange.setText('*Change will be sent back to first input address')
         elif chngBehaveStr=='Specify':
            wltID = self.main.getWalletForAddr160(changeBehave[0])
            msg = '*Change will be sent to %s...' % chngAddrStr[:12]
            if wltID:
               msg += ' (Wallet: %s)'%wltID
            lblSpecialChange.setText(msg)
         elif chngBehaveStr=='NoChange':
            lblSpecialChange.setText('(This transaction is exact -- there are no change outputs)')
            
      self.btnCancel = QPushButton("Cancel")
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.accept)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)


      frmTable = makeLayoutFrame('Vert', recipLbls, STYLE_RAISED)
      frmRight = makeVertFrame( [ lblMsg, \
                                  'Space(20)', \
                                  frmTable, \
                                  lblSpecialChange, \
                                  'Space(10)', \
                                  lblLastConfirm, \
                                  'Space(10)', \
                                  buttonBox ] )

      frmAll = makeHorizFrame( [ lblInfoImg, frmRight ] )
      
      layout.addWidget(frmAll)
      #layout.addWidget(lblMsg,               0, 1,   1, 1)

      #layout.addWidget(lblFrm,               1, 1,   1, 1)

      #layout.addWidget(lblLastConfirm,       2, 1,  1, 1)
      #layout.addWidget(buttonBox,            3, 1,  1, 1)
      #layout.setSpacing(20)

      self.setLayout(layout)
      self.setMinimumWidth(350)
      self.setWindowTitle('Confirm Transaction')
      



class DlgSendBitcoins(ArmoryDialog):
   COLS = enum('LblAddr','Addr','AddrBook', 'LblAmt','Btc','LblUnit','BtnMax',  'LblComm','Comm')
   def __init__(self, wlt, parent=None, main=None, prefill=None):
      super(DlgSendBitcoins, self).__init__(parent, main)
      self.maxHeight = tightSizeNChar(GETFONT('var'), 1)[1]+8

      self.wlt    = wlt  
      self.wltID  = wlt.uniqueIDB58

      txFee = self.main.getSettingOrSetDefault('Default_Fee', MIN_TX_FEE)

      self.widgetTable = []

      self.scrollRecipArea = QScrollArea()
      #self.scrollRecipArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
      lblRecip = QRichLabel('<b>Enter Recipients:</b>')
      lblRecip.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
         
      self.freeOfErrors = True

      feetip = createToolTipObject( \
            'Transaction fees go to users who contribute computing power to '
            'keep the Bitcoin network secure, and in return they get your transaction '
            'included in the blockchain faster.  <b>Most transactions '
            'do not require a fee</b> but it is recommended anyway '
            'since it guarantees quick processing for less than $0.01 USD and '
            'helps the network.')

      self.edtFeeAmt = QLineEdit()
      self.edtFeeAmt.setFont(GETFONT('Fixed'))
      self.edtFeeAmt.setMaximumWidth(tightSizeNChar(self.edtFeeAmt, 12)[0])
      self.edtFeeAmt.setMaximumHeight(self.maxHeight)
      self.edtFeeAmt.setAlignment(Qt.AlignRight)
      self.edtFeeAmt.setText(coin2str(txFee, maxZeros=1).strip())

      spacer = QSpacerItem(20, 1)


      btnSend = QPushButton('Send!')
      self.connect(btnSend, SIGNAL('clicked()'), self.createTxAndBroadcast)

      txFrm = makeLayoutFrame('Horiz', [QLabel('Transaction Fee:'), \
                                       self.edtFeeAmt, \
                                       feetip, \
                                       'stretch', \
                                       btnSend])


      

      # Create the wallet summary display
      lbls = []
      lbls.append( QRichLabel("Wallet ID:", doWrap=False) )
      lbls.append( QRichLabel("Name:", doWrap=False))
      lbls.append( QRichLabel("Description:", doWrap=False))
      lbls.append( QRichLabel("Spendable BTC:", doWrap=False))

      for i in range(len(lbls)):
         lbls[i].setAlignment(Qt.AlignLeft | Qt.AlignTop)
         lbls[i].setText('<b>'+str(lbls[i].text())+'</b>')

      
      self.lblSummaryID    = QRichLabel('')
      self.lblSummaryName  = QRichLabel('')
      self.lblSummaryDescr = QRichLabel('')
      self.lblSummaryDescr.setWordWrap(True)
      self.lblSummaryBal   = QMoneyLabel(0)

      # Format balance if necessary
      if not TheBDM.getBDMState()=='BlockchainReady':
         self.lblSummaryBal.setText('(available when online)', color='DisableFG')
      else:
         bal = wlt.getBalance('Spendable')
         if bal==0: 
            self.lblSummaryBal.setValueText(0, wBold=True)
         else:      
            self.lblSummaryBal.setValueText(bal, maxZeros=1, wBold=True)

         
      self.frmWalletInfo = QFrame()
      self.frmWalletInfo.setFrameStyle(STYLE_SUNKEN)
      frmLayout = QGridLayout()
      for i in range(len(lbls)):
         frmLayout.addWidget(lbls[i], i, 0,  1, 1)

      self.lblSummaryID.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.lblSummaryName.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.lblSummaryDescr.setAlignment(Qt.AlignLeft | Qt.AlignTop)
      self.lblSummaryDescr.setMinimumWidth( tightSizeNChar(self.lblSummaryDescr, 30)[0])
      frmLayout.addWidget(self.lblSummaryID,    0, 2, 1, 1)
      frmLayout.addWidget(self.lblSummaryName,  1, 2, 1, 1)
      frmLayout.addWidget(self.lblSummaryDescr, 2, 2, 1, 1)
      frmLayout.addWidget(self.lblSummaryBal,   3, 2, 1, 1)
      frmLayout.addItem(QSpacerItem(20, 10, QSizePolicy.Fixed, QSizePolicy.Expanding), 0, 1, 3, 1)
      self.frmWalletInfo.setLayout(frmLayout)

      
      lblNoSend = QRichLabel('')
      btnUnsigned = QRichLabel('')
      ttipUnsigned = QRichLabel('')

      if not TheBDM.getBDMState()=='BlockchainReady':
         lblNoSend.setText(
            '<font color=%s>'
            'You can sign this transaction, but you do not have '
            'access to the Bitcoin network in order to broadcast '
            'it.  However, you can create the transaction that '
            'you <i>want</i> to send, and then broadcast it from a computer '
            'that <i>is</i> connected to the network.</font>' % htmlColor('TextWarn'))
      elif wlt.watchingOnly:
         lblNoSend = QRichLabel( \
            '<font color=%s>'
            'This is an "offline" wallet, which means that the '
            'private keys needed to send bitcoins are not on this computer. '
            'However, you can create the transaction you would like to '
            'spend, then Armory will provide you with a file that can be '
            'signed by the computer that <i>does</i> have the private '
            'keys.</font>' % htmlColor('TextWarn'))


      if not wlt.watchingOnly:
         ttipUnsigned = createToolTipObject( \
            'If you would like to create the transaction but not sign it yet, '
            'you can click this button to save it to a file.')
      else:
         ttipUnsigned = createToolTipObject( \
            'After clicking this button, you will be given directions for '
            'completing this transaction.')
         btnSend.setToolTip('This is a watching-only wallet! '
                            'You cannot use it to send bitcoins!')
         btnSend.setEnabled(False)


      btnUnsigned = QPushButton('Create Unsigned Transaction')
      self.connect(btnUnsigned, SIGNAL('clicked()'), self.createOfflineTxDPAndDisplay)

      if not TheBDM.getBDMState()=='BlockchainReady':
         btnSend.setToolTip('<u></u>You are currently not connected to the Bitcoin network, '
                            'so you cannot initiate any transactions.')
         btnSend.setEnabled(False)
         btnUnsigned.setEnabled(False)
            


      def addDonation():
         self.addOneRecipient(ARMORY_DONATION_ADDR, ONE_BTC, \
            'Donation to Armory Developers.  Thank you for your generosity!', \
            label='Armory Donation Address')
         
         
      btnDonate = QPushButton("Donate to Armory Developers!")
      ttipDonate = createToolTipObject( \
         'Making this software was a lot of work.  You can give back '
         'by adding a small donation to go to the Armory developers.  '
         'You will have the ability to change the donation amount '
         'before finalizing the transaction.')
      self.connect(btnDonate, SIGNAL("clicked()"), self.addDonation)


      btnEnterURI = QPushButton('Manually Enter "bitcoin:" Link')
      ttipEnterURI = createToolTipObject( \
         'Armory does not always succeed at registering itself to handle '
         'URL links from webpages and email.  '
         'Click this button to copy a link directly into Armory')
      self.connect(btnEnterURI, SIGNAL("clicked()"), self.clickEnterURI)


      if USE_TESTNET:
         btnDonate.setVisible(False)
         ttipDonate.setVisible(False)


      ########################################################################
      # In Expert usermode, allow the user to modify source addresses
      frmCoinControl = QFrame()
      self.sourceAddrList = None
      self.altBalance = None
      if self.main.usermode == USERMODE.Expert:
         self.lblCoinCtrl = QRichLabel('Source:  All addresses')
         self.btnCoinCtrl = QPushButton('Coin Control')
         self.connect(self.btnCoinCtrl, SIGNAL('clicked()'), self.doCoinCtrl)
         frmCoinControl = makeHorizFrame([self.lblCoinCtrl, self.btnCoinCtrl])



      ########################################################################
      # In Expert usermode, allow the user to modify the change address
      frmChangeAddr = QFrame()
      if self.main.usermode == USERMODE.Expert:
         self.chkDefaultChangeAddr = QCheckBox('Use an existing address for change')
         self.radioFeedback = QRadioButton('Send change to first input address')
         self.radioSpecify  = QRadioButton('Specify a change address')
         self.lblChangeAddr = QRichLabel('Send Change To:')
         self.edtChangeAddr = QLineEdit()
         self.btnChangeAddr = createAddrBookButton(self, self.edtChangeAddr, \
                                       self.wlt.uniqueIDB58, 'Send change to')
         self.chkRememberChng = QCheckBox('Remember for future transactions')
         self.vertLine = VLINE()

         self.ttipSendChange = createToolTipObject( \
               'Most transactions end up with oversized inputs and Armory will send '
               'the change to the next address in this wallet.  You may change this '
               'behavior by checking this box.')
         self.ttipFeedback = createToolTipObject( \
               'Guarantees that no new addresses will be created to receive '
               'change. This reduces anonymity, but is useful if you '
               'created this wallet solely for managing imported addresses, '
               'and want to keep all funds within existing addresses.')
         self.ttipSpecify = createToolTipObject( \
               'You can specify any valid Bitcoin address for the change.  '
               '<b>NOTE:</b> If the address you specify is not in this wallet, '
               'Armory will not be able to distinguish the outputs when it shows '
               'up in your ledger.  The change will look like a second recipient, '
               'and the total debit to your wallet will be equal to the amount '
               'you sent to the recipient <b>plus</b> the change.')


         # Make sure that there can only be one selection
         btngrp = QButtonGroup(self)
         btngrp.addButton(self.radioFeedback)
         btngrp.addButton(self.radioSpecify)
         btngrp.setExclusive(True)

         def toggleSpecify(b):
            self.lblChangeAddr.setVisible(b)
            self.edtChangeAddr.setVisible(b)
            self.btnChangeAddr.setVisible(b)
            
         def toggleChngAddr(b):
            self.radioFeedback.setVisible(b)
            self.radioSpecify.setVisible(b)
            self.ttipFeedback.setVisible(b)
            self.ttipSpecify.setVisible(b)
            self.chkRememberChng.setVisible(b)
            self.vertLine.setVisible(b)
            if not self.radioFeedback.isChecked() and not self.radioSpecify.isChecked():
               self.radioFeedback.setChecked(True)
            toggleSpecify(b and self.radioSpecify.isChecked())
            
         
         self.connect(self.chkDefaultChangeAddr, SIGNAL('toggled(bool)'), toggleChngAddr)
         self.connect(self.radioSpecify,         SIGNAL('toggled(bool)'), toggleSpecify)
   
         # Pre-set values based on settings
         
         chngBehave = self.main.getWltSetting(self.wltID, 'ChangeBehavior')
         chngAddr   = self.main.getWltSetting(self.wltID, 'ChangeAddr')
         if chngBehave == 'Feedback':
            self.chkDefaultChangeAddr.setChecked(True)
            self.radioFeedback.setChecked(True)
            self.radioSpecify.setChecked(False)
            toggleChngAddr(True)
            self.chkRememberChng.setChecked(True)
         elif chngBehave == 'Specify':
            self.chkDefaultChangeAddr.setChecked(True)
            self.radioFeedback.setChecked(False)
            self.radioSpecify.setChecked(True)
            toggleChngAddr(True)
            if checkAddrStrValid(chngAddr):
               self.edtChangeAddr.setText(chngAddr)
               self.edtChangeAddr.setCursorPosition(0)
               self.chkRememberChng.setChecked(True)
         else:
            # Other option is "NewAddr" but in case there's an error, should run
            # this branch by default
            self.chkDefaultChangeAddr.setChecked(False)
            self.radioFeedback.setChecked(False)
            self.radioSpecify.setChecked(False)
            toggleChngAddr(False)

         if(    self.chkDefaultChangeAddr.isChecked() and \
            not self.radioFeedback.isChecked() and \
            not self.radioSpecify.isChecked()):
            self.radioFeedback.setChecked(True) 

         frmChngLayout = QGridLayout()
         i=0;
         frmChngLayout.addWidget(self.chkDefaultChangeAddr,   i,0, 1,6)
         frmChngLayout.addWidget(self.ttipSendChange,         i,6, 1,2)
         i+=1
         frmChngLayout.addWidget(self.radioFeedback,          i,1, 1,5)
         frmChngLayout.addWidget(self.ttipFeedback,           i,6, 1,2)
         i+=1
         frmChngLayout.addWidget(self.radioSpecify,           i,1, 1,5)
         frmChngLayout.addWidget(self.ttipSpecify,            i,6, 1,2)
         i+=1
         frmChngLayout.addWidget(self.lblChangeAddr,          i,1, 1,2)
         frmChngLayout.addWidget(self.edtChangeAddr,          i,3, 1,4)
         frmChngLayout.addWidget(self.btnChangeAddr,          i,7, 1,1)
         i+=1
         frmChngLayout.addWidget(self.chkRememberChng,         i,1, 1,7)

         frmChngLayout.addWidget(self.vertLine,               1,0, i-1,1)
      
         frmChangeAddr.setLayout(frmChngLayout)
         frmChangeAddr.setFrameStyle(STYLE_SUNKEN)
         
   
   
      frmUnsigned = makeHorizFrame([btnUnsigned, ttipUnsigned])
      frmDonate   = makeHorizFrame([btnDonate,   ttipDonate])
      frmEnterURI = makeHorizFrame([btnEnterURI, ttipEnterURI])


      frmNoSend     = makeLayoutFrame('Horiz', [lblNoSend], STYLE_SUNKEN)
      if not wlt.watchingOnly:
         frmNoSend.setVisible(False)
         if self.main.usermode==USERMODE.Standard:
            btnUnsigned.setVisible(False)
            ttipUnsigned.setVisible(False)
            btnEnterURI.setVisible(False)
            ttipEnterURI.setVisible(False)

      frmBottomLeft = makeVertFrame( [self.frmWalletInfo, \
                                      frmUnsigned, \
                                      frmEnterURI, \
                                      frmDonate, \
                                      'Stretch', \
                                      frmCoinControl, \
                                      frmChangeAddr],  STYLE_SUNKEN )

      lblSend = QRichLabel('<b>Sending from Wallet:</b>')
      lblSend.setAlignment(Qt.AlignLeft | Qt.AlignBottom)


      layout = QGridLayout()

      layout.addWidget(lblSend,                  0,0,  1,1)
      layout.addWidget(frmBottomLeft,            1,0,  2,1)

      layout.addWidget(lblRecip,                 0,1,  1,1)
      layout.addWidget(self.scrollRecipArea,     1,1,  1,1)
      layout.addWidget(txFrm,                    2,1,  1,1)

      layout.setRowStretch(0,0)
      layout.setRowStretch(1,1)
      layout.setRowStretch(2,0)
      self.setLayout(layout)

      self.makeRecipFrame(1)
      self.setWindowTitle('Send Bitcoins')
      self.setMinimumHeight(self.maxHeight*20)

      loadCount      = self.main.settings.get('Load_Count')
      alreadyDonated = self.main.getSettingOrSetDefault('DonateAlready', False)
      lastPestering  = self.main.getSettingOrSetDefault('DonateLastPester', 0)
      donateFreq     = self.main.getSettingOrSetDefault('DonateFreq', 20)
      dnaaDonate     = self.main.getSettingOrSetDefault('DonateDNAA', False)


      if prefill:
         get = lambda s: prefill[s] if prefill.has_key(s) else ''
         addr160  = addrStr_to_hash160(get('address'))
         amount   = get('amount')
         message  = get('message')
         label    = get('label')
         self.addOneRecipient(addr160, amount, message, label)
      
      elif not self.main==None and loadCount%donateFreq==(donateFreq-1) and \
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
         self.main.writeSetting('DonateLastPester', loadCount)

         if result[0]==True:
            self.addDonation()
            self.makeRecipFrame(2)

         if result[1]==True:
            self.main.writeSetting('DonateDNAA', True)
      
      hexgeom = self.main.settings.get('SendBtcGeometry')
      if len(hexgeom)>0:
         geom = QByteArray.fromHex(hexgeom)
         self.restoreGeometry(geom)
            

      if TheBDM.getBDMState()=='BlockchainReady' and not wlt.watchingOnly:
         btnSend.setDefault(True)
      else:
         btnUnsigned.setDefault(True)
         
      self.setWalletSummary()


   #############################################################################
   def saveGeometrySettings(self):
      self.main.writeSetting('SendBtcGeometry', str(self.saveGeometry().toHex()))

   #############################################################################
   def closeEvent(self, event):
      self.saveGeometrySettings()
      super(DlgSendBitcoins, self).closeEvent(event)

   #############################################################################
   def accept(self, *args):
      self.saveGeometrySettings()
      super(DlgSendBitcoins, self).accept(*args)

   #############################################################################
   def reject(self, *args):
      self.saveGeometrySettings()
      super(DlgSendBitcoins, self).reject(*args)

   #############################################################################
   def createOfflineTxDPAndDisplay(self):
      self.txValues = []
      self.origRVPairs = []
      self.comments = []
      txdp = self.validateInputsGetTxDP()
      if not txdp:
         return
      
      changePair = (self.change160, self.selectedBehavior)
      dlg = DlgConfirmSend(self.wlt, self.origRVPairs, self.txValues[1], self, \
                                                   self.main, False, changePair)
      if dlg.exec_():
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
         
      
      changePair = (self.change160, self.selectedBehavior)
      dlg = DlgConfirmSend(self.wlt, self.origRVPairs, self.txValues[1], self, \
                                                   self.main, True, changePair)
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
            self.main.broadcastTransaction(finalTx)
            self.accept()
            try:
               self.parent.accept()
            except:
               pass
         except:
            LOGEXCEPT('Problem sending transaction!')
            # TODO: not sure what errors to catch here, yet...
            raise


   #############################################################################
   def changeWidgetTableColor(self, idx, col, color):
      palette = QPalette()
      palette.setColor( QPalette.Base, color)
      self.widgetTable[idx][col].setPalette( palette );
      self.widgetTable[idx][col].setAutoFillBackground( True );


   #############################################################################
   def validateInputsGetTxDP(self):
      COLS = self.COLS
      self.freeOfErrors = True
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
            self.freeOfErrors = False
            self.changeWidgetTableColor(i, COLS.Addr, Colors.SlightRed)


      numChkFail  = sum([1 if b==-1 or b!=ADDRBYTE else 0 for b in addrBytes])
      if not self.freeOfErrors:
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
                  'Address %d is for the wrong network!  You are on the <b>%s</b> '
                  'and the address you supplied is for the the '
                  '<b>%s</b>!' % (i+1, NETWORKS[ADDRBYTE], net), QMessageBox.Ok)
         return False


      # Construct recipValuePairs and check that all metrics check out
      recipValuePairs = []
      totalSend = 0
      for i in range(len(self.widgetTable)):
         try:
            recipStr = str(self.widgetTable[i][COLS.Addr].text()).strip()
            valueStr = str(self.widgetTable[i][COLS.Btc].text()).strip()
            value    = str2coin(valueStr, negAllowed=False)
            if value==0:
               QMessageBox.critical(self, 'Zero Amount', \
                  'You cannot send 0 BTC to any recipients.  <br>Please enter '
                  'a positive amount for recipient %d.' % (i+1), QMessageBox.Ok)
               return False

         except NegativeValueError:
            QMessageBox.critical(self, 'Negative Value', \
               'You have specified a negative amount for recipient %d. <br>Only '
               'positive values are allowed!.' % (i+1), QMessageBox.Ok)
            return False
         except TooMuchPrecisionError:
            QMessageBox.critical(self, 'Too much precision', \
               'Bitcoins can only be specified down to 8 decimal places. '
               'The smallest value that can be sent is  0.0000 0001 BTC. '
               'Please enter a new amount for recipient %d.' % (i+1), QMessageBox.Ok)
            return False
         except ValueError:
            QMessageBox.critical(self, 'Missing recipient amount', \
               'You did not specify an amount to send!', QMessageBox.Ok)
            return False
         except:
            QMessageBox.critical(self, 'Invalid Value String', \
               'The amount you specified '
               'to send to address %d is invalid (%s).' % (i+1,valueStr), QMessageBox.Ok)
            LOGERROR('Invalid amount specified: "%s"', valueStr)
            return False

         totalSend += value
         recip160 = addrStr_to_hash160(recipStr)
         recipValuePairs.append( (recip160, value) )
         self.comments.append(str(self.widgetTable[i][COLS.Comm].text()))

      try:
         feeStr = str(self.edtFeeAmt.text())
         fee = str2coin(feeStr, negAllowed=False)
      except NegativeValueError:
         QMessageBox.critical(self, 'Negative Value', \
            'You must enter a positive value for the fee.', QMessageBox.Ok)
         return False
      except TooMuchPrecisionError:
         QMessageBox.critical(self, 'Too much precision', \
            'Bitcoins can only be specified down to 8 decimal places. '
            'The smallest meaning Bitcoin amount is 0.0000 0001 BTC. '
            'Please enter a fee of at least 0.0000 0001', QMessageBox.Ok)
         return False
      except:
         QMessageBox.critical(self, 'Invalid Fee String', \
            'The fee you specified is invalid.  A standard fee is 0.0005 BTC, '
            'though some transactions may succeed with zero fee.', QMessageBox.Ok)
         LOGERROR('Invalid fee specified: "%s"', feeStr)
         return False
            
         
      bal = self.getUsableBalance()
      if totalSend+fee > bal:
         valTry = coin2str(totalSend+fee, maxZeros=2).strip()
         valMax = coin2str(bal,           maxZeros=2).strip()
         if self.altBalance==None:
            QMessageBox.critical(self, 'Insufficient Funds', \
            'You just tried to send %s BTC, including fee, but you only '
            'have %s BTC (spendable) in this wallet!' % (valTry, valMax), QMessageBox.Ok)
         else:
            QMessageBox.critical(self, 'Insufficient Funds', \
            'You just tried to send %s BTC, including fee, but you only '
            'have %s BTC with this coin control selection!' % (valTry, valMax), QMessageBox.Ok)
         return False
      

      # Get unspent outs for this wallet:
      utxoList = self.getUsableTxOutList()
      utxoSelect = PySelectCoins(utxoList, totalSend, fee)



      # TODO:  I should use a while loop/iteration to make sure that the fee
      #        change does not actually induce another, higher fee (which 
      #        is extraordinarily unlikely... I even set up the SelectCoins 
      #        algorithm to try to leave some room in the tx so that the fee
      #        will not change the I/Os).   Despite this, I will concede 
      #        the extremely rare situation where this would happen, I think 
      #        it will be okay to send a slightly sub-standard fee.  
      minFeeRec = calcMinSuggestedFees(utxoSelect, totalSend, fee)
      if fee<minFeeRec[1]:

         overrideMin = self.main.getSettingOrSetDefault('OverrideMinFee', False)
         if totalSend+minFeeRec[1] > bal:
            # Need to adjust this based on overrideMin flag
            self.edtFeeAmt.setText(coin2str(minFeeRec[1], maxZeros=1).strip())
            QMessageBox.warning(self, 'Insufficient Balance', \
               'You have specified a valid amount to send, but the required '
               'transaction fee causes this transaction to exceed your balance.  '
               'In order to send this transaction, you will be required to '
               'pay a fee of <b>' + coin2str(minFeeRec[1], maxZeros=0).strip() + ' BTC</b>.  '
               '<br><br>'
               'Please go back and adjust the value of your transaction, not '
               'to exceed a total of <b>' + coin2str(bal-minFeeRec[1], maxZeros=0).strip() +
               ' BTC</b> (the necessary fee has been entered into the form, so you '
               'can use the "MAX" button to enter the remaining balance for a '
               'recipient).', QMessageBox.Ok)
            return
                        

         extraMsg = ''
         feeStr = coin2str(fee, maxZeros=0).strip()
         minRecStr = coin2str(minFeeRec[1], maxZeros=0).strip()

         msgBtns = QMessageBox.Yes | QMessageBox.Cancel

         reply = QMessageBox.warning(self, 'Insufficient Fee', \
            'The fee you have specified (%s BTC) is insufficient for the size '
            'and priority of your transaction.  You must include at least '
            '%s BTC to send this transaction.  \n\nDo you agree to the fee of %s BTC?  ' % \
            (feeStr, minRecStr, minRecStr),  msgBtns)
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
         

      ### IF we got here, everything is good to go...
      #   Just need to get a change address and then construct the tx
      totalTxSelect = sum([u.getValue() for u in utxoSelect])
      totalChange = totalTxSelect - (totalSend + fee)

      self.origRVPairs = list(recipValuePairs)
      self.change160 = ''
      self.selectedBehavior = ''
      if totalChange>0:
         self.change160 = self.determineChangeAddr(utxoSelect)
         LOGINFO('Change address behavior: %s', self.selectedBehavior)
         if not self.change160:
            return
         recipValuePairs.append( [self.change160, totalChange])
      else:
         if self.main.usermode==USERMODE.Expert and self.chkDefaultChangeAddr.isChecked():
            self.selectedBehavior = 'NoChange'
   
      # Anonymize the outputs
      random.shuffle(recipValuePairs)
      txdp = PyTxDistProposal().createFromTxOutSelection( utxoSelect, \
                                                          recipValuePairs)

      self.txValues = [totalSend, fee, totalChange]
      return txdp

      

   #############################################################################
   def getUsableBalance(self):
      if self.altBalance==None:
         return self.wlt.getBalance('Spendable')
      else:
         return self.altBalance

         
   #############################################################################
   def getUsableTxOutList(self):
      if self.altBalance==None:
         return self.wlt.getTxOutList('Spendable')
      else:
         utxoList = []
         for a160 in self.sourceAddrList:
            # Trying to avoid a swig bug involving iteration over vector<> types
            utxos = self.wlt.getAddrTxOutList(a160)
            for i in range(len(utxos)):
               utxoList.append(PyUnspentTxOut().createFromCppUtxo(utxos[i]))
         return utxoList


   #############################################################################
   def determineChangeAddr(self, utxoList):
      changeAddr160 = ''
      self.selectedBehavior = 'NewAddr'
      addrStr = ''
      if not self.main.usermode==USERMODE.Expert:
         changeAddr160 = self.wlt.getNextUnusedAddress().getAddr160()
         self.wlt.setComment(changeAddr160, CHANGE_ADDR_DESCR_STRING)
      else:
         if not self.chkDefaultChangeAddr.isChecked():
            changeAddr160 = self.wlt.getNextUnusedAddress().getAddr160()
            self.wlt.setComment(changeAddr160, CHANGE_ADDR_DESCR_STRING)
            # If generate new address, remove previously-remembered behavior
            self.main.setWltSetting(self.wltID, 'ChangeBehavior', self.selectedBehavior)
         else:
            if self.radioFeedback.isChecked():
               changeAddr160 = utxoList[0].getRecipientAddr()
               self.selectedBehavior = 'Feedback'
            elif self.radioSpecify.isChecked():
               addrStr = str(self.edtChangeAddr.text()).strip()
               if not checkAddrStrValid(addrStr):
                  QMessageBox.warning(self, 'Invalid Address', \
                     'You specified an invalid change address '
                     'for this transcation.', QMessageBox.Ok)
                  return '',False
               changeAddr160 = addrStr_to_hash160(addrStr)
               self.selectedBehavior = 'Specify'

      if self.main.usermode==USERMODE.Expert and self.chkRememberChng.isChecked():
         self.main.setWltSetting(self.wltID, 'ChangeBehavior', self.selectedBehavior)
         if self.selectedBehavior=='Specify' and len(addrStr)>0:
            self.main.setWltSetting(self.wltID, 'ChangeAddr', addrStr)
      else:
         self.main.setWltSetting(self.wltID, 'ChangeBehavior', 'NewAddr')
      
      return changeAddr160
                  
               
            
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

   #############################################################################
   def clickEnterURI(self):
      dlg = DlgUriCopyAndPaste(self,self.main)
      dlg.exec_()

      if len(dlg.uriDict)>0:
         COLS = self.COLS
         lastIsEmpty = True
         for col in (COLS.Addr, COLS.Btc, COLS.Comm):
            if len(str(self.widgetTable[-1][col].text()))>0:
               lastIsEmpty = False
            
         if not lastIsEmpty:
            self.makeRecipFrame( len(self.widgetTable)+1 )
   
         self.widgetTable[-1][self.COLS.Addr].setText(dlg.uriDict['address'])
         if dlg.uriDict.has_key('amount'):
            amtStr = coin2str(dlg.uriDict['amount'], maxZeros=1).strip()
            self.widgetTable[-1][self.COLS.Btc].setText( amtStr)

         
         haveLbl = dlg.uriDict.has_key('label')
         haveMsg = dlg.uriDict.has_key('message')
   
         dispComment = '' 
         if haveLbl and haveMsg:
            dispComment = dlg.uriDict['label'] + ': ' + dlg.uriDict['message']
         elif not haveLbl and haveMsg:
            dispComment = dlg.uriDict['message']
         elif haveLbl and not haveMsg:
            dispComment = dlg.uriDict['label']

         self.widgetTable[-1][self.COLS.Comm].setText(dispComment)
               

   #############################################################################
   def addOneRecipient(self, addr160, amt, msg, label=''):
      if len(label)>0:
         self.wlt.setComment(addr160, label)

      COLS = self.COLS
      lastIsEmpty = True
      for col in (COLS.Addr, COLS.Btc, COLS.Comm):
         if len(str(self.widgetTable[-1][col].text()))>0:
            lastIsEmpty = False
         
      if not lastIsEmpty:
         self.makeRecipFrame( len(self.widgetTable)+1 )

      if amt:
         amt = coin2str(amt, maxZeros=2).strip()

      self.widgetTable[-1][self.COLS.Addr].setText(hash160_to_addrStr(addr160))
      self.widgetTable[-1][self.COLS.Addr].setCursorPosition(0)
      self.widgetTable[-1][self.COLS.Btc].setText(amt)
      self.widgetTable[-1][self.COLS.Btc].setCursorPosition(0)
      self.widgetTable[-1][self.COLS.Comm].setText(msg)
      self.widgetTable[-1][self.COLS.Comm].setCursorPosition(0)




   #####################################################################
   def setMaximum(self, targWidget):
      nRecip = len(self.widgetTable)
      totalOther = 0
      r=0  
      try:
         bal = self.getUsableBalance()
         txFee = str2coin(str(self.edtFeeAmt.text()))
         while r<nRecip:
            # Use while loop so 'r' is still in scope in the except-clause
            if targWidget==self.widgetTable[r][self.COLS.Btc]:
               r+=1
               continue

            amtStr = str(self.widgetTable[r][self.COLS.Btc].text()).strip()
            if len(amtStr)>0:
               totalOther += str2coin(amtStr)
            r+=1
   
      except:
         QMessageBox.warning(self, 'Invalid Input', \
               'Cannot compute the maximum amount '
               'because there is an error in the amount '
               'for recipient %d.' % (r+1,), QMessageBox.Ok)
         return


      maxStr = coin2str( (bal - (txFee + totalOther)), maxZeros=0 )
      if bal < txFee+totalOther:
         QMessageBox.warning(self, 'Insufficient funds', \
               'You have specified more than your spendable balance to '
               'the other recipients and the transaction fee.  Therefore, the '
               'maximum amount for this recipient would actually be negative.', \
               QMessageBox.Ok)
         return
         
      targWidget.setText(maxStr.strip())


   #####################################################################
   def createSetMaxButton(self, targWidget):
      newBtn = QPushButton('MAX')
      newBtn.setMaximumWidth( relaxedSizeStr(self, 'MAX')[0])
      newBtn.setToolTip( '<u></u>Fills in the maximum spendable amount minus '
                         'the amounts specified for other recipients '
                         'and the transaction fee ')
      funcSetMax = lambda:  self.setMaximum( targWidget )
      self.connect( newBtn, SIGNAL('clicked()'), funcSetMax )
      return newBtn


   #####################################################################
   def makeRecipFrame(self, nRecip):
      prevNRecip = len(self.widgetTable)
      nRecip = max(nRecip, 1)
      inputs = []
      for i in range(nRecip):
         if i<prevNRecip and i<nRecip:
            inputs.append([])
            for j in (self.COLS.Addr, self.COLS.Btc, self.COLS.Comm):
               inputs[-1].append(str(self.widgetTable[i][j].text()))


      frmRecip = QFrame()
      frmRecip.setFrameStyle(QFrame.NoFrame)
      frmRecipLayout = QVBoxLayout()

      COLS = self.COLS 
      
      self.widgetTable = []
      for r in range(nRecip):
         self.widgetTable.append([])

         self.widgetTable[r].append( QLabel('Address %d:' % (r+1,)) )

         self.widgetTable[r].append( QLineEdit() )
         self.widgetTable[r][-1].setMinimumWidth(relaxedSizeNChar(GETFONT('var'), 38)[0])
         self.widgetTable[r][-1].setMaximumHeight(self.maxHeight)
         self.widgetTable[r][-1].setFont(GETFONT('var',9))

         # This is the hack of all hacks -- but I have no other way to make this work. 
         # For some reason, the references on variable r are carrying over between loops
         # and all widgets are getting connected to the last one.  The only way I could 
         # work around this was just ultra explicit garbage.  I'll pay 0.1 BTC to anyone
         # who figures out why my original code was failing...
         #idx = r+0
         #chgColor = lambda x: self.changeWidgetTableColor(idx, COLS.Addr, QColor(255,255,255))
         #self.connect(self.widgetTable[idx][-1], SIGNAL('textChanged(QString)'), chgColor)
         if r==0:
            chgColor = lambda x: self.changeWidgetTableColor(0, COLS.Addr, QColor(255,255,255))
            self.connect(self.widgetTable[0][-1], SIGNAL('textChanged(QString)'), chgColor)
         elif r==1:
            chgColor = lambda x: self.changeWidgetTableColor(1, COLS.Addr, QColor(255,255,255))
            self.connect(self.widgetTable[1][-1], SIGNAL('textChanged(QString)'), chgColor)
         elif r==2:
            chgColor = lambda x: self.changeWidgetTableColor(2, COLS.Addr, QColor(255,255,255))
            self.connect(self.widgetTable[2][-1], SIGNAL('textChanged(QString)'), chgColor)
         elif r==3:
            chgColor = lambda x: self.changeWidgetTableColor(3, COLS.Addr, QColor(255,255,255))
            self.connect(self.widgetTable[3][-1], SIGNAL('textChanged(QString)'), chgColor)
         elif r==4:
            chgColor = lambda x: self.changeWidgetTableColor(4, COLS.Addr, QColor(255,255,255))
            self.connect(self.widgetTable[4][-1], SIGNAL('textChanged(QString)'), chgColor)


         addrEntryBox = self.widgetTable[r][-1]
         self.widgetTable[r].append( createAddrBookButton(self, addrEntryBox, \
                                      self.wlt.uniqueIDB58, 'Send to') )
         self.widgetTable[r].append( QLabel('Amount:') )

         self.widgetTable[r].append( QLineEdit() )
         self.widgetTable[r][-1].setFont(GETFONT('Fixed'))
         self.widgetTable[r][-1].setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 14)[0])
         self.widgetTable[r][-1].setMaximumHeight(self.maxHeight)
         self.widgetTable[r][-1].setAlignment(Qt.AlignLeft)
      
         self.widgetTable[r].append( QLabel('BTC') )
         self.widgetTable[r][-1].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

         #self.widgetTable[r].append( QPushButton('MAX') )
         #self.widgetTable[r][-1].setMaximumWidth( relaxedSizeStr(self, 'MAX')[0])
         #self.widgetTable[r][-1].setToolTip( \
                           #'Fills in the maximum spendable amount minus amounts '
                           #'specified for other recipients and the transaction fee ')
         #self.connect(self.widgetTable[r][-1], SIGNAL('clicked()'),  setMaxFunc)
         self.widgetTable[r].append( self.createSetMaxButton(self.widgetTable[r][COLS.Btc]) )

         self.widgetTable[r].append( QLabel('Comment:') )
         self.widgetTable[r].append( QLineEdit() )
         self.widgetTable[r][-1].setFont(GETFONT('var', 9))
         self.widgetTable[r][-1].setMaximumHeight(self.maxHeight)

         if r<nRecip and r<prevNRecip:
            self.widgetTable[r][COLS.Addr].setText( inputs[r][0] )
            self.widgetTable[r][COLS.Btc ].setText( inputs[r][1] )
            self.widgetTable[r][COLS.Comm].setText( inputs[r][2] )

         subfrm = QFrame()
         subfrm.setFrameStyle(STYLE_RAISED)
         subLayout = QGridLayout()
         subLayout.addWidget(self.widgetTable[r][COLS.LblAddr],  0, 0, 1, 1)
         subLayout.addWidget(self.widgetTable[r][COLS.Addr],     0, 1, 1, 5)
         subLayout.addWidget(self.widgetTable[r][COLS.AddrBook], 0, 6, 1, 1)

         subLayout.addWidget(self.widgetTable[r][COLS.LblAmt],   1, 0, 1, 1)
         subLayout.addWidget(self.widgetTable[r][COLS.Btc],      1, 1, 1, 2)
         subLayout.addWidget(self.widgetTable[r][COLS.LblUnit],  1, 3, 1, 1)
         subLayout.addWidget(self.widgetTable[r][COLS.BtnMax],   1, 4, 1, 1)
         subLayout.addWidget(QLabel(''),                         1, 5, 1, 2)

         subLayout.addWidget(self.widgetTable[r][COLS.LblComm],  2, 0, 1, 1)
         subLayout.addWidget(self.widgetTable[r][COLS.Comm],     2, 1, 1, 6)
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

      #widgetsForWidth = [COLS.LblAddr, COLS.Addr, COLS.LblAmt, COLS.Btc]
      #minScrollWidth = sum([self.widgetTable[0][col].width() for col in widgetsForWidth])

      frmRecipLayout.addWidget(btnFrm)
      frmRecipLayout.addStretch()
      frmRecip.setLayout(frmRecipLayout)
      #return frmRecip
      self.scrollRecipArea.setWidget(frmRecip)


   #############################################################################
   def doCoinCtrl(self):
      
      dlgcc = DlgCoinControl(self, self.main, self.wlt, self.sourceAddrList)
      if dlgcc.exec_():
         self.sourceAddrList = [x[0] for x in dlgcc.coinControlList]
         self.altBalance = sum([x[1] for x in dlgcc.coinControlList])
      
         nAddr = len(self.sourceAddrList)
         if self.altBalance == self.wlt.getBalance('Spendable'):
            self.lblCoinCtrl.setText('Source: All addresses')
            self.sourceAddrList = None
            self.altBalance = None
         elif nAddr==0:
            self.lblCoinCtrl.setText('Source: None selected')
         elif nAddr==1:
            aStr = hash160_to_addrStr(self.sourceAddrList[0])
            self.lblCoinCtrl.setText('Source: %s...' % aStr[:12])
         elif nAddr>1:
            self.lblCoinCtrl.setText('Source: %d addresses' % nAddr)

         self.setWalletSummary()


   #############################################################################
   def setWalletSummary(self):
      useAllAddr = (self.altBalance==None)
      fullBal = self.wlt.getBalance('Spendable')
      if useAllAddr:
         self.lblSummaryID.setText(self.wlt.uniqueIDB58)
         self.lblSummaryName.setText(self.wlt.labelName)
         self.lblSummaryDescr.setText(self.wlt.labelDescr)
         if fullBal==0:
            self.lblSummaryBal.setText('0.0', color='TextRed', bold=True)
         else:
            self.lblSummaryBal.setValueText(fullBal, wBold=True)
      else:
         self.lblSummaryID.setText(self.wlt.uniqueIDB58 + '*')
         self.lblSummaryName.setText(self.wlt.labelName + '*')
         self.lblSummaryDescr.setText('*Coin Control Subset*', color='TextBlue', bold=True)
         self.lblSummaryBal.setText(coin2str(self.altBalance, maxZeros=0), color='TextBlue')
         rawValTxt = str(self.lblSummaryBal.text())
         self.lblSummaryBal.setText(rawValTxt + ' <font color="%s">(of %s)</font>' % \
                                    (htmlColor('DisableFG'), coin2str(fullBal, maxZeros=0)))

      if not TheBDM.getBDMState()=='BlockchainReady':
         self.lblSummaryBal.setText('(available when online)', color='DisableFG')


################################################################################
class DlgOfflineTxCreated(ArmoryDialog):
   def __init__(self, wlt, txdp, parent=None, main=None):
      super(DlgOfflineTxCreated, self).__init__(parent, main)

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
         'full version of this wallet.  They can load this data into Armory '
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
      LOGINFO('Saving unsigned tx file: %s', toSave)
      try:
         theFile = open(toSave, 'w')
         theFile.write(self.txtTxDP.toPlainText())
         theFile.close()
      except IOError:
         LOGEXCEPT('Failed to save file: %s', toSave)
         pass

   def doSaveFileS(self):
      """ Save the Signed-Tx block of data """
      dpid = self.txdp.uniqueB58
      toSave = self.main.getFileSave( 'Save Signed Transaction', \
                                      ['Armory Transactions (*.signed.tx)'], \
                                      'armory_%s_.signed.tx' % dpid)
      LOGINFO('Saving signed tx file: %s', toSave)
      try:
         theFile = open(toSave, 'w')
         theFile.write(self.txtSigned.toPlainText())
         theFile.close()
      except IOError:
         LOGEXCEPT('Failed to save file: %s', toSave)
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
         LOGWARN('Unrecognized TxDP input!')
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
         LOGEXCEPT('Could not unserialize TxDP')
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
class DlgOfflineSelect(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgOfflineSelect, self).__init__(parent, main)


      self.do_review = False
      self.do_create = False
      self.do_broadc = False
      lblDescr = QRichLabel( \
         'In order to execute an offline transaction, three steps must '
         'be followed: <br><br>'
         '\t(1) <u>On</u>line Computer:  Create the unsigned transaction<br>'
         '\t(2) <u>Off</u>line Computer: Get the transaction signed<br>'
         '\t(3) <u>On</u>line Computer:  Broadcast the signed transaction<br><br>'
         'You must create the transaction using a watch-only wallet on an online '
         'system, but watch-only wallets cannot sign it.  Only the offline system '
         'can create a valid signature.  The easiest way to execute all three steps '
         'is to use a USB key to move the data between computers.<br><br>'
         'All the data saved to the removable medium during all three steps are '
         'completely safe and do not reveal any private information that would benefit an '
         'attacker trying to steal your funds.  However, this transaction data does '
         'reveal some addresses in your wallet, and may represent a breach of '
         '<i>privacy</i> if not protected.')

      btnCreate = QPushButton('Create New Offline Transaction')
      btnReview = QPushButton('Sign and/or Broadcast Transaction')
      if not TheBDM.getBDMState()=='BlockchainReady':
         btnCreate.setEnabled(False)
         if len(self.main.walletMap)==0:
            btnReview = QPushButton('No wallets available!')
            btnReview.setEnabled(False)
         else:
            btnReview = QPushButton('Sign Offline Transaction')
      elif len(self.main.walletMap)==0 and self.main.netMode==NETWORKMODE.Full:
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
class DlgReviewOfflineTx(ArmoryDialog):
   """
   We will make the assumption that this dialog is used ONLY for outgoing 
   transactions from your wallet.  This simplifies the logic if we don't 
   have to identify input senders/values, and handle the cases where those 
   may not be specified
   """
   def __init__(self, parent=None, main=None):
      super(DlgReviewOfflineTx, self).__init__(parent, main)


      self.wlt    = None
      self.sentToSelfWarn = False
      self.fileLoaded = None


      lblDescr = QRichLabel( \
         'Copy or load a transaction from file into the text box below.  '
         'If the transaction is unsigned and you have the correct wallet, '
         'you will have the opportunity to sign it.  If it is already signed '
         'you will have the opportunity to broadcast it to '
         'the Bitcoin network to make it final.')



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
      self.btnCopyHex   = QPushButton('Copy Final Tx (Hex)')
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
      self.connect(self.btnCopyHex,   SIGNAL('clicked()'), self.copyTxHex)

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
            'This is wallet from which the offline transaction spends bitcoins'))
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

      expert = (self.main.usermode==USERMODE.Expert)
      frmBtn = makeLayoutFrame('Vert', [ self.btnSign, \
                                         self.btnBroadcast, \
                                         self.btnSave, \
                                         self.btnLoad, \
                                         self.btnCopy, \
                                         self.btnCopyHex if expert else QRichLabel(''), \
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
         if self.main.netMode==NETWORKMODE.Full:
            self.btnBroadcast.setEnabled(True)
         else:
            self.btnBroadcast.setEnabled(False)
            self.btnBroadcast.setToolTip('No connection to Bitcoin network!')

      self.btnSave.setEnabled(True)
      self.btnCopyHex.setEnabled(False)
      if not self.txdpReadable:
         if len(txdpStr)>0:
            self.lblStatus.setText('<b><font color="red">Unrecognized!</font></b>')
         else:
            self.lblStatus.setText('')
         self.btnSign.setEnabled(False)
         self.btnBroadcast.setEnabled(False)
         self.btnSave.setEnabled(False)
         self.makeReviewFrame()
         return
      elif not self.enoughSigs:
         if not self.main.getSettingOrSetDefault('DNAA_ReviewOfflineTx', False):
            result = MsgBoxWithDNAA(MSGBOX.Warning, title='Offline Warning', \
                  msg='<b>Please review your transaction carefully before '
                  'signing and broadcasting it!</b>  The extra security of '
                  'using offline wallets is lost if you do '
                  'not confirm the transaction is correct!',  dnaaMsg=None)
            self.main.writeSetting('DNAA_ReviewOfflineTx', result[1])
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
         self.btnCopyHex.setEnabled(True)
      

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
         QMessageBox.warning(self, 'Invalid Transaction', \
            'Transaction data is invalid and cannot be shown!', QMessageBox.Ok)
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
            'is a watching-only wallet.  Therefore, private keys are '
            'not available to sign this transaction.', \
             QMessageBox.Ok)
         return


      # We should provide the same confirmation dialog here, as we do when 
      # sending a regular (online) transaction.  But the DlgConfirmSend was 
      # not really designed 
      #self.txValues = [totalSend, fee, totalChange]
      #self.origRVPairs = list(recipValuePairs)
      txdp = self.txdpObj
      rvpairsOther = []
      rvpairsMine = []
      outInfo = txdp.pytxObj.makeRecipientsList()
      theFee = sum(txdp.inputValues) - sum([info[1] for info in outInfo])
      for info in outInfo:
         if not info[0] in (TXOUT_SCRIPT_COINBASE, TXOUT_SCRIPT_STANDARD):
            rvpairsOther.append( ['Non-Standard Output', info[1]])
            continue

         if self.wlt.hasAddr(info[2]):
            rvpairsMine.append( [info[2], info[1]])
         else:
            rvpairsOther.append( [info[2], info[1]])


      if len(rvpairsMine)==0 and len(rvpairsOther)>1:
         QMessageBox.warning(self, 'Missing Change', \
            'This transaction has %d recipients, and none of them '
            'are addresses in this wallet (for receiving change).  '
            'This can happen if you specified a custom change address '
            'for this transaction, or sometimes happens solely by '
            'chance with a multi-recipient transaction.  It could also '
            'be the result of someone tampering with the transaction. '
            '<br><br>The transaction is valid and ready to be signed.  Please '
            'verify the recipient and amounts carefully before '
            'confirming the transaction on the next screen.' % len(rvpairsOther), \
            QMessageBox.Ok)
      dlg = DlgConfirmSend(self.wlt, rvpairsOther, theFee, self, self.main)
      if not dlg.exec_():
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

      if not self.fileLoaded==None:
         self.saveTx()


   def broadTx(self):
      if self.main.netMode == NETWORKMODE.Disconnected:
         QMessageBox.warning(self, 'No Internet!', \
            'Armory lost its connection to Bitcoin-Qt, and cannot '
            'broadcast any transactions until it is reconnected. '
            'Please verify that Bitcoin-Qt (or bitcoind) is open '
            'and synchronized with the network.', QMessageBox.Ok)
         return
      elif self.main.netMode == NETWORKMODE.Offline:
         QMessageBox.warning(self, 'No Internet!', \
            'You do not currently have a connection to the Bitcoin network. '
            'If this does not seem correct, verify that Bitcoin-Qt is open '
            'and synchronized with the network.', QMessageBox.Ok)
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
         if self.fileLoaded:
            reply = QMessageBox.warning(self, 'Done!', \
               'The transaction has been broadcast!'
               '<br><br>'
               'Now that the transaction is final, the transaction file is no '
               'longer needed.  Would you like to delete it?  '
               '<br><br>'
               'Delete %s?' % self.fileLoaded, QMessageBox.Yes | QMessageBox.No)
            if reply==QMessageBox.Yes:
               try:
                  os.remove(self.fileLoaded)
               except:
                  QMessageBox.critical(self, 'File Remove Error', \
                     'The file could not be deleted.  If you want to delete '
                     'it, please do so manually.  The file was loaded from: '
                     '<br><br>%s: ' % self.fileLoaded, QMessageBox.Ok)
               
         self.accept()



   def saveTx(self):
      if not self.txdpReadable:
         reply = QMessageBox.warning

      if not self.fileLoaded==None and self.enoughSigs and self.sigsValid:
         reply = QMessageBox.question(self,'Overwrite?', \
         'This transaction was loaded from the following file:'
         '\n\n%s\n\nWould you like to overwrite it with this signed '
         'transaction?' % self.fileLoaded, QMessageBox.Yes | QMessageBox.No)
         if reply==QMessageBox.Yes:
            newSaveFile = self.fileLoaded.replace('unsigned', 'signed')
            f = open(newSaveFile, 'w')
            f.write(str(self.txtTxDP.toPlainText()))
            f.close()
            if not newSaveFile==self.fileLoaded:
               os.remove(self.fileLoaded)
            self.fileLoaded = newSaveFile
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
      LOGINFO('Saved transaction file: %s', filename)

      if len(str(filename))>0:
         f = open(filename, 'w')
         f.write(str(self.txtTxDP.toPlainText()))
         f.close()


   def loadTx(self):
      filename = self.main.getFileLoad('Load Transaction', \
                             ['Transactions (*.signed.tx *.unsigned.tx)'])
      
      if len(str(filename))>0:
         LOGINFO('Selected transaction file to load: %s', filename)
         f = open(filename, 'r')
         self.txtTxDP.setText(f.read())
         f.close()
         self.fileLoaded = filename


   def copyTx(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(self.txtTxDP.toPlainText()))
      self.lblCopied.setText('<i>Copied!</i>')


   def copyTxHex(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(binary_to_hex(self.txdpObj.prepareFinalTx().serialize()))
      self.lblCopied.setText('<i>Copied!</i>')


################################################################################
class DlgShowKeyList(ArmoryDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgShowKeyList, self).__init__(parent, main)

      self.wlt    = wlt

      self.havePriv = ((not self.wlt.useEncryption) or not (self.wlt.isLocked))

      wltType = determineWalletType(self.wlt, self.main)[0]
      if wltType in (WLTTYPES.Offline, WLTTYPES.WatchOnly):
         self.havePriv = False


      # NOTE/WARNING:  We have to make copies (in RAM) of the unencrypted
      #                keys, or else we will have to type in our address
      #                every 10s if we want to modify the key list.  This
      #                isn't likely a big problem, but it's not ideal, 
      #                either.  Not much I can do about, though...
      #                (at least:  once this dialog is closed, all the 
      #                garbage should be collected...)
      self.addrCopies = []
      for addr in self.wlt.getLinearAddrList(withAddrPool=True):
         self.addrCopies.append(addr.copy())
      self.rootKeyCopy = self.wlt.addrMap['ROOT'].copy()
         

      self.strDescrReg = ( \
         'The textbox below shows all keys that are part of this wallet, '
         'which includes both permanent keys and imported keys.  If you '
         'simply want to backup your wallet and you have no imported keys '
         'then all data below is reproducible from a plain paper backup.'
         '<br><br>'
         'If you have imported addresses to backup, and/or you '
         'would like to export your private keys to another '
         'wallet service or application, then you can save this data '
         'to disk, or copy&paste it into the other application.')
      self.strDescrWarn = ( \
         '<br><br>'
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
      self.chkList['PubKeyHash']= QCheckBox('Hash160')
      self.chkList['PrivCrypt'] = QCheckBox('Private Key (Encrypted)')
      self.chkList['PrivHexBE'] = QCheckBox('Private Key (Plain Hex)')
      self.chkList['PrivB58']   = QCheckBox('Private Key (Plain Base58)')
      self.chkList['PubKey']    = QCheckBox('Public Key (BE)')
      self.chkList['ChainIndex']= QCheckBox('Chain Index')

      self.chkList['AddrStr'   ].setChecked(True )
      self.chkList['PubKeyHash'].setChecked(False)
      self.chkList['PrivB58'   ].setChecked(self.havePriv)
      self.chkList['PrivCrypt' ].setChecked(False)
      self.chkList['PrivHexBE' ].setChecked(self.havePriv)
      self.chkList['PubKey'    ].setChecked(not self.havePriv)
      self.chkList['ChainIndex'].setChecked(False)

      namelist = ['AddrStr','PubKeyHash','PrivB58','PrivCrypt', \
                  'PrivHexBE', 'PubKey', 'ChainIndex']

      for name in self.chkList.keys():
         self.connect(self.chkList[name], SIGNAL('toggled(bool)'), \
                      self.rewriteList)


      self.chkImportedOnly = QCheckBox('Imported Addresses Only')
      self.chkWithAddrPool = QCheckBox('Include Unused (Address Pool)')
      self.chkDispRootKey  = QCheckBox('Include Paper Backup Root')
      self.chkDispRootKey.setChecked(True)
      self.connect(self.chkImportedOnly, SIGNAL('toggled(bool)'), self.rewriteList)
      self.connect(self.chkWithAddrPool, SIGNAL('toggled(bool)'), self.rewriteList)
      self.connect(self.chkDispRootKey,  SIGNAL('toggled(bool)'), self.rewriteList)
      #self.chkCSV = QCheckBox('Display in CSV format')

      if not self.havePriv:
         self.chkDispRootKey.setChecked(False)
         self.chkDispRootKey.setEnabled(False)
         

      std = (self.main.usermode==USERMODE.Standard)
      adv = (self.main.usermode==USERMODE.Advanced)
      dev = (self.main.usermode==USERMODE.Expert)
      if std:
         self.chkList['PubKeyHash'].setVisible(False)
         self.chkList['PrivCrypt' ].setVisible(False)
         self.chkList['ChainIndex'].setVisible(False)
      elif adv:
         self.chkList['PubKeyHash'].setVisible(False)
         self.chkList['ChainIndex'].setVisible(False)

      # We actually just want to remove these entirely
      # (either we need to display all data needed for decryption,
      # besides passphrase,  or we shouldn't show any of it)
      self.chkList['PrivCrypt' ].setVisible(False)

      chkBoxList = [self.chkList[n] for n in namelist] 
      chkBoxList.append('Line')
      chkBoxList.append(self.chkImportedOnly)
      chkBoxList.append(self.chkWithAddrPool)
      chkBoxList.append(self.chkDispRootKey)

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
         self.chkList['PrivB58'  ].setEnabled(False)
         self.chkList['PrivB58'  ].setChecked(False)

      dlgLayout = QGridLayout()
      dlgLayout.addWidget(frmDescr,    0,0, 1,1)
      dlgLayout.addWidget(frmChks,     0,1, 1,1)
      dlgLayout.addWidget(self.txtBox, 1,0, 1,2)
      dlgLayout.addWidget(frmGoBack,   2,0, 1,2)
      dlgLayout.setRowStretch(0, 0)
      dlgLayout.setRowStretch(1, 1)
      dlgLayout.setRowStretch(2, 0)

      self.setLayout(dlgLayout)
      self.rewriteList()
      self.setWindowTitle('All Wallet Keys')

         

   def rewriteList(self, *args):
      """
      Write out all the wallet data
      """
      def fmtBin(s, nB=4, sw=False):
         h = binary_to_hex(s)
         if sw: 
            h = hex_switchEndian(h)
         return ' '.join([h[i:i+nB] for i in range(0, len(h), nB)])

      L = []
      L.append('Created:       ' + unixTimeToFormatStr(RightNow(), self.main.getPreferredDateFormat()))
      L.append('Wallet ID:     ' + self.wlt.uniqueIDB58)
      L.append('Wallet Name:   ' + self.wlt.labelName)
      L.append('')

      if self.chkDispRootKey.isChecked():
         binPriv0     = self.rootKeyCopy.binPrivKey32_Plain.toBinStr()[:16]
         binPriv1     = self.rootKeyCopy.binPrivKey32_Plain.toBinStr()[16:]
         binChain0    = self.rootKeyCopy.chaincode.toBinStr()[:16]
         binChain1    = self.rootKeyCopy.chaincode.toBinStr()[16:]
         binPriv0Chk  = computeChecksum(binPriv0, nBytes=2)
         binPriv1Chk  = computeChecksum(binPriv1, nBytes=2)
         binChain0Chk = computeChecksum(binChain0, nBytes=2)
         binChain1Chk = computeChecksum(binChain1, nBytes=2)

         binPriv0  = binary_to_easyType16(binPriv0 + binPriv0Chk)
         binPriv1  = binary_to_easyType16(binPriv1 + binPriv1Chk)
         binChain0 = binary_to_easyType16(binChain0 + binChain0Chk)
         binChain1 = binary_to_easyType16(binChain1 + binChain1Chk)

         L.append('-'*80)
         L.append('The following is the same information contained on your paper backup.')
         L.append('All NON-imported addresses in your wallet are backed up by this data.')
         L.append('')
         L.append('Root Key:     ' + ' '.join([binPriv0[i:i+4]  for i in range(0,36,4)]))
         L.append('              ' + ' '.join([binPriv1[i:i+4]  for i in range(0,36,4)]))
         L.append('Chain Code:   ' + ' '.join([binChain0[i:i+4] for i in range(0,36,4)]))
         L.append('              ' + ' '.join([binChain1[i:i+4] for i in range(0,36,4)]))
         L.append('-'*80)
         L.append('')

         # Cleanup all that sensitive data laying around in RAM
         binPriv0, binPriv1 = None,None
         binChain0, binChain1 = None,None 
         binPriv0Chk, binPriv1Chk = None,None
         binChain0Chk, binChain1Chk = None,None


      self.havePriv = False
      topChain = self.wlt.highestUsedChainIndex
      extraLbl = ''
      #c = ',' if self.chkCSV.isChecked() else '' 
      for addr in self.addrCopies:

         # Address pool
         if self.chkWithAddrPool.isChecked():
            if addr.chainIndex > topChain:
               extraLbl = '   (Unused/Address Pool)'
         else:
            if addr.chainIndex > topChain:
               continue

         # Imported Addresses
         if self.chkImportedOnly.isChecked():
            if not addr.chainIndex==-2:
               continue
         else:
            if addr.chainIndex==-2:
               extraLbl = '   (Imported)'

         if self.chkList['AddrStr'   ].isChecked():  
            L.append(                   addr.getAddrStr() + extraLbl)
         if self.chkList['PubKeyHash'].isChecked(): 
            L.append(                  '   Hash160   : ' + fmtBin(addr.getAddr160()))
         if self.chkList['PrivB58'   ].isChecked(): 
            pB58 = encodePrivKeyBase58(addr.binPrivKey32_Plain.toBinStr())
            pB58Stretch = ' '.join([pB58[i:i+6] for i in range(0, len(pB58), 6)])
            L.append(                  '   PrivBase58: ' + pB58Stretch)
            self.havePriv = True
         if self.chkList['PrivCrypt' ].isChecked():  
            L.append(                  '   PrivCrypt : ' + fmtBin(addr.binPrivKey32_Encr.toBinStr()))
         if self.chkList['PrivHexBE' ].isChecked():  
            L.append(                  '   PrivHexBE : ' + fmtBin(addr.binPrivKey32_Plain.toBinStr()))
            self.havePriv = True
         if self.chkList['PubKey'    ].isChecked():  
            L.append(                  '   PublicX   : ' + fmtBin(addr.binPublicKey65.toBinStr()[1:33 ]))
            L.append(                  '   PublicY   : ' + fmtBin(addr.binPublicKey65.toBinStr()[  33:]))
         if self.chkList['ChainIndex'].isChecked(): 
            L.append(                  '   ChainIndex: ' + str(addr.chainIndex))

      self.txtBox.setText('\n'.join(L))
      if self.havePriv:
         self.lblDescr.setText(self.strDescrReg + self.strDescrWarn)
      else:
         self.lblDescr.setText(self.strDescrReg)

      
      
   def saveToFile(self):
      if self.havePriv:
         if not self.main.getSettingOrSetDefault('DNAA_WarnPrintKeys', False):
            result = MsgBoxWithDNAA(MSGBOX.Warning, title='Plaintext Private Keys', \
                  msg='<font color="red"><b>REMEMBER:</b></font> The data you '
                  'are about to save contains private keys.  Please make sure '
                  'that only trusted persons will have access to this file.'
                  '<br><br>Are you sure you want to continue?', \
                  dnaaMsg=None, wCancel=True)
            if not result[0]:
               return
            self.main.writeSetting('DNAA_WarnPrintKeys', result[1])
            
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
               

   def cleanup(self):
      self.rootKeyCopy.binPrivKey32_Plain.destroy()
      for addr in self.addrCopies:
         addr.binPrivKey32_Plain.destroy()
      self.rootKeyCopy = None
      self.addrCopies = None

   def accept(self):
      self.cleanup()
      super(DlgShowKeyList, self).accept()

   def reject(self):
      self.cleanup()
      super(DlgShowKeyList, self).reject()
            


################################################################################
class DlgTxFeeOptions(ArmoryDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgTxFeeOptions, self).__init__(parent, main)

      lblDescr = QLabel( \
         'Transaction fees go to people who contribute processing power to '
         'the Bitcoin network to process transactions and keep it secure.') 
      lblDescr2 = QLabel( \
         'Nearly all transactions are guaranteed to be '
         'processed if a fee of 0.0005 BTC is included (less than $0.01 USD).  You '
         'will be prompted for confirmation if a higher fee amount is required for '
         'your transaction.')


################################################################################
class DlgAddressProperties(ArmoryDialog):
   def __init__(self, wlt, parent=None, main=None):
      super(DlgAddressProperties, self).__init__(parent, main)

   


################################################################################
def extractTxInfo(pytx, rcvTime=None):

   
   pytxdp = None
   if isinstance(pytx, PyTxDistProposal):
      pytxdp = pytx
      pytx = pytxdp.pytxObj.copy()
      
   txHash = pytx.getHash()
   txOutToList, sumTxOut, txinFromList, sumTxIn, txTime, txBlk, txIdx = [None]*7

   txOutToList = pytx.makeRecipientsList()
   sumTxOut = sum([t[1] for t in txOutToList])

   txcpp = Tx()
   if TheBDM.getBDMState()=='BlockchainReady': 
      txcpp = TheBDM.getTxByHash(txHash)
      if txcpp.isInitialized():
         headref = txcpp.getHeaderPtr()
         if headref:
            txTime  = unixTimeToFormatStr(headref.getTimestamp())
            txBlk   = headref.getBlockHeight()
            txIdx   = txcpp.getBlockTxIndex()
         else:
            if rcvTime==None:
               txTime  = 'Unknown'
            elif rcvTime==-1:
               txTime  = '[[Not broadcast yet]]'
            elif isinstance(rcvTime, basestring):
               txTime  = rcvTime
            else:
               txTime  = unixTimeToFormatStr(rcvTime)
            txBlk   = UINT32_MAX
            txIdx   = -1
   
   txinFromList = []
   if TheBDM.getBDMState()=='BlockchainReady' and txcpp.isInitialized():
      # Use BDM to get all the info about the TxOut being spent
      # Recip, value, block-that-incl-tx, tx-that-incl-txout, txOut-index
      haveAllInput=True
      for i in range(txcpp.getNumTxIn()):
         txinFromList.append([])
         cppTxin = txcpp.getTxIn(i)
         prevTxHash = cppTxin.getOutPoint().getTxHash()
         if TheBDM.getTxByHash(prevTxHash).isInitialized():
            prevTxOut = TheBDM.getPrevTxOut(cppTxin)
            txinFromList[-1].append(TheBDM.getSenderAddr20(cppTxin))
            txinFromList[-1].append(TheBDM.getSentValue(cppTxin))
            if prevTxOut.getParentTxPtr():
               txinFromList[-1].append(prevTxOut.getParentTxPtr().getBlockHeight())
               txinFromList[-1].append(prevTxOut.getParentTxPtr().getThisHash())
               txinFromList[-1].append(prevTxOut.getIndex())
            else:
               LOGERROR('How did we get a bad parent pointer? (extractTxInfo)')
               prevTxOut.pprint()
               txinFromList[-1].append('')
               txinFromList[-1].append('')
               txinFromList[-1].append('')
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


      
class DlgDispTxInfo(ArmoryDialog):
   def __init__(self, pytx, wlt=None, parent=None, main=None, mode=None, \
                             precomputeIdxGray=None, precomputeAmt=None, txtime=None):
      """
      This got freakin' complicated, because I'm trying to handle
      wallet/nowallet, BDM/noBDM and Std/Adv/Dev all at once. 

      We can override the user mode as an input argument, in case a std
      user decides they want to see the tx in adv/dev mode
      """
      super(DlgDispTxInfo, self).__init__(parent, main)
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
      haveBDM    = TheBDM.getBDMState()=='BlockchainReady'

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
            # This isn't actually true:  P2Pool outputs get flagged as non-std...
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


      # This is incorrectly flagging P2Pool outputs as non-std!
      #if IsNonStandard:
         ## TODO:  Need to do something with this non-std tx!
         #print '***Non-std transaction!'
         #QMessageBox.critical(self, 'Non-Standard Transaction', \
           #'This is a non-standard transaction, which cannot be '
           #'interpretted by this program.  DO NOT ASSUME that you '
           #'own these bitcoins, even if you see your address in '
           #'any part of the transaction.  Only an expert can tell '
           #'you if and how these coins can be redeemed!  \n\n'
           #'If you would like more information, please copy the '
           #'information on the next window into an email and send '
           #'it to alan.reiner@gmail.com.', QMessageBox.Ok)



      layout = QGridLayout()
      lblDescr = QLabel('Transaction Information:') 

      layout.addWidget(lblDescr,     0,0,  1,1)
   
      frm = QFrame()
      frm.setFrameStyle(STYLE_RAISED)
      frmLayout = QGridLayout()
      lbls = []



      # Show the transaction ID, with the user's preferred endianness
      # I hate BE, but block-explorer requires it so it's probably a better default
      endianness = self.main.getSettingOrSetDefault('PrefEndian', BIGENDIAN)
      estr = ''
      if self.mode in (USERMODE.Advanced, USERMODE.Expert):
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

      if self.mode in (USERMODE.Expert,):
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
            if not data[FIELDS.Idx]==None and self.mode==USERMODE.Expert:
               idxStr = '  (Tx #%d)'%data[FIELDS.Idx]
            lbls.append([])
            lbls[-1].append(createToolTipObject( 
                  'Every transaction is eventually included in a "block" which '
                  'is where the transaction is permanently recorded.  A new block '
                  'is produced approximately every 10 minutes.'))
            lbls[-1].append(QLabel('Included in Block:'))
            lbls[-1].append(QRichLabel( str(data[FIELDS.Blk]) + idxStr ))
            if TheBDM.getBDMState()=='BlockchainReady':
               nConf = TheBDM.getTopBlockHeight() - data[FIELDS.Blk] + 1
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
      elif self.mode==USERMODE.Expert:
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
      elif self.mode==USERMODE.Expert:
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
      self.btnOk     = QPushButton('OK')
      self.btnIOList.setCheckable(True)
      self.connect(self.btnIOList, SIGNAL('clicked()'), self.extraInfoClicked)
      self.connect(self.btnOk,     SIGNAL('clicked()'), self.accept)
      self.connect(self.btnCopy,   SIGNAL('clicked()'), self.copyRawTx)

      btnStrip = makeLayoutFrame('Horiz', [self.btnIOList, self.btnCopy, self.lblCopied, 'Stretch', self.btnOk])
      if not self.mode==USERMODE.Expert:
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
         self.scriptArea.setVisible(self.mode==USERMODE.Expert)
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
      dev = (self.main.usermode==USERMODE.Expert)
      
      if True:   actCopySender = menu.addAction("Copy Sender Address")
      if True:   actCopyWltID  = menu.addAction("Copy Wallet ID")
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
      dev = (self.main.usermode==USERMODE.Expert)
      
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


class DlgPaperBackup(ArmoryDialog):
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
      super(DlgPaperBackup, self).__init__(parent, main)


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
      self.scene.setBackgroundBrush(QColor(255,255,255))
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
      logoPixmap = QPixmap(':/armory_logo_h36.png') 
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
      btnPrint.setMinimumWidth( 3*tightSizeStr(btnPrint,'Print...')[0])
      btnCancel = QPushButton('&Cancel')
      self.connect(btnPrint, SIGNAL('clicked()'), self.print_)
      self.connect(btnCancel, SIGNAL('clicked()'), self.reject)

      lblWarn = QRichLabel( \
         'The data shown below '
         'protects all keys that are ever <u>generated</u> by your wallet. '
         'The QR code holds the exact same data as the four data '
         'lines, but may be easier to use than typing if you have a '
         'QR code scanner.'
         '<br><br>'
         '<font color="red"><u>WARNING</u>:  <i>YOU MUST BACKUP IMPORTED '
         'ADDRESSES SEPARATELY TO PROTECT ANY MONEY IN THEM</i>.  '
         'Use the "Backup Individual Keys" buttton in the wallet '
         'properties to access imported private keys.</font>')


      layout = QGridLayout()
      layout.addWidget(lblWarn,    0,0, 1,4)
      layout.addWidget(self.view,  1,0, 3,4)
      
      frmButtons = makeHorizFrame([btnCancel, 'Stretch', btnPrint])
      layout.addWidget(frmButtons, 4,0, 1,4)

      self.setLayout(layout)

      self.setWindowIcon(QIcon(':/printer_icon.png'))
      self.setWindowTitle('Print Wallet Backup')
      
       
   def print_(self):
      self.printer = QPrinter(QPrinter.HighResolution)
      self.printer.setPageSize(QPrinter.Letter)
      dialog = QPrintDialog(self.printer)
      if dialog.exec_():
          painter = QPainter(self.printer)
          painter.setRenderHint(QPainter.TextAntialiasing)
          self.scene.render(painter)
          self.accept()

   def cleanup(self):
      self.binPriv.destroy()
      self.binPriv     = None
      self.binPriv0    = None
      self.binPriv1    = None
      self.binPriv0Chk = None
      self.binPriv1Chk = None

   def accept(self):
      self.cleanup()
      super(DlgPaperBackup, self).accept()

   def reject(self):
      self.cleanup()
      super(DlgPaperBackup, self).reject()


class DlgBadConnection(ArmoryDialog):
   def __init__(self, haveInternet, haveSatoshi, parent=None, main=None):
      super(DlgBadConnection, self).__init__(parent, main)


      layout = QGridLayout()
      lblWarnImg = QLabel()
      lblWarnImg.setPixmap(QPixmap(':/MsgBox_warning48.png'))
      lblWarnImg.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

      lblDescr = QLabel()
      if not haveInternet and not CLI_OPTIONS.offline:
         lblDescr = QRichLabel( \
            'Armory was not able to detect an internet connection, so Armory '
            'will operate in "Offline" mode.  In this mode, only wallet'
            '-management and unsigned-transaction functionality will be available. '
            '<br><br>'
            'If this is an error, please check your internet connection and '
            'restart Armory.<br><br>Would you like to continue in "Offline" mode? ')
      elif haveInternet and not haveSatoshi:
         lblDescr = QRichLabel( \
            'Armory was not able to detect the presence of Bitcoin-Qt or bitcoind '
            'client software (available at http://www.bitcoin.org).  Please make sure that '
            'the one of those programs is... <br>'
            '<br><b>(1)</b> ...open and connected to the network '
            '<br><b>(2)</b> ...on the same network as Armory (main-network or test-network)'
            '<br><b>(3)</b> ...synchronized with the blockchain before '
            'starting Armory<br><br>Without the Bitcoin-Qt or bitcoind open, you will only '
            'be able to run Armory in "Offline" mode, which will not have access '
            'to new blockchain data, and you will not be able to send outgoing '
            'transactions<br><br>If you do not want to be in "Offline" mode, please '
            'restart Armory after one of these programs is open and synchronized with '
            'the network')
      else:
         # Nothing to do -- we shouldn't have even gotten here
         #self.reject()
         pass
         
      
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



class DlgExecLongProcess(ArmoryDialog):
   """
   Execute a processing that may require having the user to wait a while.
   Should appear like a splash screen, and will automatically close when
   the processing is done.  As such, you should have very little text, just 
   in case it finishes immediately, the user won't have time to read it.

   DlgExecLongProcess(execFunc, 'Short Description', self, self.main).exec_()
   """
   def __init__(self, funcExec, msg='', parent=None, main=None):
      super(DlgExecLongProcess, self).__init__(parent, main)
      
      self.func   = funcExec

      waitFont = GETFONT('Var', 14)
      descrFont = GETFONT('Var', 12)
      palette = QPalette()
      palette.setColor( QPalette.Window, QColor(235,235,255))
      self.setPalette( palette );
      self.setAutoFillBackground(True)

      if parent:
         qr = parent.geometry()
         x,y,w,h = qr.left(),qr.top(),qr.width(),qr.height()
         dlgW = relaxedSizeStr(waitFont, msg)[0]
         dlgW = min(dlgW, 400)
         dlgH = 150
         self.setGeometry(int(x+w/2-dlgW/2),int(y+h/2-dlgH/2), dlgW, dlgH)

      lblWaitMsg = QRichLabel('Please Wait...')
      lblWaitMsg.setFont(waitFont)
      lblWaitMsg.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

      lblDescrMsg = QRichLabel(msg)
      lblDescrMsg.setFont(descrFont)
      lblDescrMsg.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

      self.setWindowFlags(Qt.SplashScreen)
      
      layout = QVBoxLayout()
      layout.addWidget(lblWaitMsg)
      layout.addWidget(lblDescrMsg)
      self.setLayout( layout )


   def exec_(self):
      def execAndClose():
         self.func()
         self.accept()

      from twisted.internet import reactor
      reactor.callLater(0.1, execAndClose)
      QDialog.exec_(self)


       
         


################################################################################
class DlgECDSACalc(ArmoryDialog):
   def __init__(self, parent=None, main=None, tabStart=0):
      super(DlgECDSACalc, self).__init__(parent, main)

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


      btnAbk = createAddrBookButton(self, self.txtAddr, None, 'Select', True)

      headPrvR  = makeHorizFrame([QLabel('Encoded Private Key'), ttipPrvR, 'Stretch'])
      headPriv  = makeHorizFrame([QLabel('Raw Private Key'), ttipPriv, 'Stretch'])
      headPubF  = makeHorizFrame([QLabel('Full Public Key'), ttipPubF, 'Stretch'])
      headPubXY = makeHorizFrame([QLabel('Raw Public Key (x,y)'), ttipPubXY, 'Stretch'])
      headHash  = makeHorizFrame([QLabel('Public Key Hash160'), ttipHash, 'Stretch'])
      headAddr  = makeHorizFrame([btnAbk, QLabel('Bitcoin Address'), ttipAddr, 'Stretch'])
      
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

      # Looks like these images didn't make it into the resource file.
      # TODO:  Figure this out later...
      #imgPlus  = QImageLabel(':/plus_orange.png')
      #imgTimes1= QImageLabel(':/asterisk_orange.png')
      #imgTimes2= QImageLabel(':/asterisk_orange.png')
      #imgDown  = QImageLabel(':/arrow_down32.png')

      imgPlus  = QRichLabel('<b>+</b>')
      imgTimes1= QRichLabel('<b>*</b>')
      imgTimes2= QRichLabel('<b>*</b>')
      imgDown  = QRichLabel('')

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
            privB58 = encodePrivKeyBase58(privBin)
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

      strMsg  = self.readMsg()
      if len(strMsg)==0:
         QMessageBox.critical(self, 'Nothing to Sign!', \
           'There is no message to sign!', QMessageBox.Ok)
         return

      a160Bin = hex_to_binary(str(self.txtHash.text()).replace(' ',''))
      if len(a160Bin)<20:
         QMessageBox.critical(self, 'Input Error', 'You did not specify an '
            'address or private key to be used for signing', QMessageBox.Ok)
         return
         
      wltID = self.checkIfAddrIsOurs(a160Bin)
      haveWltPriv = (wltID!='')

      try:
         binPriv = SecureBinaryData(hex_to_binary(str(self.txtPriv.text()).strip().replace(' ','')))
         haveRawPriv = (binPriv.getSize()==32)
      except:
         haveRawPriv = False
         if not haveWltPriv:
            QMessageBox.critical(self, 'Input Error', \
               'There was an error parsing the private key.', QMessageBox.Ok)
            return

      
      


      if not haveRawPriv:
         wlt = self.main.walletMap[wltID]
         if wlt.useEncryption and wlt.isLocked:
            dlg = DlgUnlockWallet(wlt, self.main, 'Encrypt New Address')
            if not dlg.exec_():
               reply = QMessageBox.critical(self, 'Wallet is locked',
                  'Could not unlock wallet, so private key data could not '
                  'be acquired.', QMessageBox.Ok)
               return
         binPriv = SecureBinaryData(wlt.addrMap[a160Bin].binPrivKey32_Plain)
            

      # TODO:  Fill in public key
      pubKey = CryptoECDSA().ComputePublicKey(binPriv)
      pubKeyHex = pubKey.toHexStr()
      self.txtPubF.setText(pubKeyHex);
      self.txtPubX.setText(pubKeyHex[2:2+64        ]);
      self.txtPubY.setText(pubKeyHex[  2+64:2+64+64]);

      modMsg = 'Bitcoin Signed Message:\n' + strMsg
      sig = CryptoECDSA().SignData(SecureBinaryData(modMsg), \
                                   binPriv)
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
      class DlgEnterSigBlock(ArmoryDialog):
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
            btnOkay   = QPushButton('OK')
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
class DlgAddressBook(ArmoryDialog):
   """
   This dialog is provided a widget which has a "setText()" method.  When the 
   user selects the address, this dialog will enter the text into the widget 
   and then close itself.
   """
   def __init__(self, parent, main, putResultInWidget=None, \
                                    defaultWltID=None, \
                                    actionStr='Select', \
                                    selectExistingOnly=False):
      super(DlgAddressBook, self).__init__(parent, main)

      self.target = putResultInWidget
      self.actStr = actionStr

      self.isBrowsingOnly = (self.target==None)

      if defaultWltID==None:
         defaultWltID = self.main.walletIDList[0]

      self.wlt = self.main.walletMap[defaultWltID]

      lblDescr = QRichLabel('Choose an address from your transaction history, '
                            'or your own wallet.  If you choose to send to one '
                            'of your own wallets, the next unused address in '
                            'that wallet will be used.')

      if self.isBrowsingOnly or selectExistingOnly:
         lblDescr = QRichLabel('Browse all receiving addresses in '
                               'this wallet, and all addresses to which this '
                               'wallet has sent bitcoins.')

      lblToWlt  = QRichLabel('<b>Send to Wallet:</b>')
      lblToAddr = QRichLabel('<b>Send to Address:</b>')
      if self.isBrowsingOnly:
         lblToWlt.setVisible(False)
         lblToAddr.setVisible(False)


      rowHeight = tightSizeStr(self.font, 'XygjpHI')[1]

      self.wltDispModel = AllWalletsDispModel(self.main)
      self.wltDispView = QTableView()
      self.wltDispView.setModel(self.wltDispModel)
      self.wltDispView.setSelectionBehavior(QTableView.SelectRows)
      self.wltDispView.setSelectionMode(QTableView.SingleSelection)
      self.wltDispView.horizontalHeader().setStretchLastSection(True)
      self.wltDispView.verticalHeader().setDefaultSectionSize(20)
      self.wltDispView.setMaximumHeight(rowHeight*7.7)
      initialColResize(self.wltDispView, [0.15, 0.30, 0.2, 0.20])
      self.connect(self.wltDispView.selectionModel(), \
                   SIGNAL('currentChanged(const QModelIndex &, const QModelIndex &)'), \
                   self.wltTableClicked)
      

      
     
      # DISPLAY sent-to addresses  
      self.addrBookTxModel = None
      self.addrBookTxView = QTableView()
      self.addrBookTxView.setSortingEnabled(True)
      self.setAddrBookTxModel(defaultWltID)
      self.connect(self.addrBookTxView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.dblClickAddressTx)

      self.addrBookTxView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.addrBookTxView.customContextMenuRequested.connect(self.showContextMenuTx)

      # DISPLAY receiving addresses  
      self.addrBookRxModel = None
      self.addrBookRxView = QTableView()
      self.addrBookRxView.setSortingEnabled(True)
      self.setAddrBookRxModel(defaultWltID)
      self.connect(self.addrBookRxView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.dblClickAddressRx)

      self.addrBookRxView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.addrBookRxView.customContextMenuRequested.connect(self.showContextMenuRx)


      self.tabWidget = QTabWidget()
      self.tabWidget.addTab(self.addrBookRxView, 'Receiving (Mine)')
      self.tabWidget.addTab(self.addrBookTxView, 'Sending (Other\'s)')
      self.tabWidget.setCurrentIndex(0)
      


      ttipSendWlt = createToolTipObject( \
         'The next unused address in that wallet will be calculated and selected. ')
      ttipSendAddr = createToolTipObject( \
         'Addresses that are in other wallets you own are <b>not showns</b>.')


      self.lblSelectWlt  = QRichLabel('', doWrap=False)
      self.btnSelectWlt  = QPushButton('No Wallet Selected')
      self.btnSelectAddr = QPushButton('No Address Selected')
      self.btnSelectWlt.setEnabled(False)
      self.btnSelectAddr.setEnabled(False)
      btnCancel     = QPushButton('Cancel')

      if self.isBrowsingOnly:
         self.btnSelectWlt.setVisible(False)
         self.btnSelectAddr.setVisible(False)
         self.lblSelectWlt.setVisible(False)
         btnCancel = QPushButton('<<< Go Back')
         ttipSendAddr.setVisible(False)
         
      if selectExistingOnly:
         lblToWlt.setVisible(False)
         self.lblSelectWlt.setVisible(False)
         self.btnSelectWlt.setVisible(False)
         ttipSendWlt.setVisible(False)

      self.connect(self.btnSelectWlt,  SIGNAL('clicked()'), self.acceptWltSelection)
      self.connect(self.btnSelectAddr, SIGNAL('clicked()'), self.acceptAddrSelection)
      self.connect(btnCancel,          SIGNAL('clicked()'), self.reject)


      dlgLayout = QGridLayout()
      dlgLayout.addWidget(lblDescr, 0,0)
      dlgLayout.addWidget(HLINE(), 1,0)
      dlgLayout.addWidget(lblToWlt, 2,0)
      dlgLayout.addWidget(self.wltDispView, 3,0)
      dlgLayout.addWidget(makeHorizFrame([self.lblSelectWlt, 'Stretch', self.btnSelectWlt]), 4,0)
      dlgLayout.addWidget(HLINE(), 5,0)
      dlgLayout.addWidget(lblToAddr, 6,0)
      dlgLayout.addWidget(self.tabWidget, 7,0)
      dlgLayout.addWidget(makeHorizFrame(['Stretch', self.btnSelectAddr]), 8,0)
      dlgLayout.addWidget(HLINE(), 9,0)
      dlgLayout.addWidget(makeHorizFrame([btnCancel, 'Stretch']), 10,0)
      dlgLayout.setRowStretch(3, 1)
      dlgLayout.setRowStretch(7, 2)

      self.setLayout(dlgLayout)
      self.sizeHint = lambda: QSize(760, 500)

      # Auto-select the default wallet, if there is one
      rowNum = 0
      if defaultWltID and self.main.walletMap.has_key(defaultWltID):
         rowNum = self.main.walletIndices[defaultWltID] 
      rowIndex = self.wltDispModel.index(rowNum,0)
      self.wltDispView.setCurrentIndex(rowIndex)
      self.wltTableClicked(rowIndex)
      
      self.setWindowTitle('Address Book')
      self.setWindowIcon(QIcon(self.main.iconfile))

      self.setMinimumWidth(300)

      hexgeom = self.main.settings.get('AddrBookGeometry')
      wltgeom = self.main.settings.get('AddrBookWltTbl')
      rxgeom  = self.main.settings.get('AddrBookRxTbl')
      txgeom  = self.main.settings.get('AddrBookTxTbl')
      if len(hexgeom)>0:
         geom = QByteArray.fromHex(hexgeom)
         self.restoreGeometry(geom)
      if len(wltgeom)>0:
         restoreTableView(self.wltDispView, wltgeom)
      if len(rxgeom)>0:
         restoreTableView(self.addrBookRxView, rxgeom)
      if len(txgeom)>0:
         restoreTableView(self.addrBookTxView, txgeom)

   #############################################################################
   def saveGeometrySettings(self):
      self.main.writeSetting('AddrBookGeometry', str(self.saveGeometry().toHex()))
      self.main.writeSetting('AddrBookWltTbl',   saveTableView(self.wltDispView))
      self.main.writeSetting('AddrBookRxTbl',    saveTableView(self.addrBookRxView))
      self.main.writeSetting('AddrBookTxTbl',    saveTableView(self.addrBookTxView))

   #############################################################################
   def closeEvent(self, event):
      self.saveGeometrySettings()
      super(DlgAddressBook, self).closeEvent(event)

   #############################################################################
   def accept(self, *args):
      self.saveGeometrySettings()
      super(DlgAddressBook, self).accept(*args)

   #############################################################################
   def reject(self, *args):
      self.saveGeometrySettings()
      super(DlgAddressBook, self).reject(*args)
   
   #############################################################################
   def setAddrBookTxModel(self, wltID):
      self.addrBookTxModel = SentToAddrBookModel(wltID, self.main)

      #
      self.addrBookTxProxy = SentAddrSortProxy(self)
      self.addrBookTxProxy.setSourceModel(self.addrBookTxModel)
      #self.addrBookTxProxy.sort(ADDRBOOKCOLS.Address)

      self.addrBookTxView.setModel(self.addrBookTxProxy)
      self.addrBookTxView.setSortingEnabled(True)
      self.addrBookTxView.setSelectionBehavior(QTableView.SelectRows)
      self.addrBookTxView.setSelectionMode(QTableView.SingleSelection)
      self.addrBookTxView.horizontalHeader().setStretchLastSection(True)
      self.addrBookTxView.verticalHeader().setDefaultSectionSize(20)
      freqSize = 1.3 * tightSizeStr(self.addrBookTxView, 'Times Used')[0]
      initialColResize(self.addrBookTxView, [0.3, 0.1, freqSize, 0.5])
      self.addrBookTxView.hideColumn(ADDRBOOKCOLS.WltID)
      self.connect(self.addrBookTxView.selectionModel(), \
                   SIGNAL('currentChanged(const QModelIndex &, const QModelIndex &)'), \
                   self.addrTableTxClicked)


   #############################################################################
   def setAddrBookRxModel(self, wltID):
      wlt = self.main.walletMap[wltID]
      self.addrBookRxModel = WalletAddrDispModel(wlt, self)

      self.addrBookRxProxy = WalletAddrSortProxy(self)
      self.addrBookRxProxy.setSourceModel(self.addrBookRxModel)
      #self.addrBookRxProxy.sort(ADDRESSCOLS.Address)

      self.addrBookRxView.setModel(self.addrBookRxProxy)
      self.addrBookRxView.setSelectionBehavior(QTableView.SelectRows)
      self.addrBookRxView.setSelectionMode(QTableView.SingleSelection)
      self.addrBookRxView.horizontalHeader().setStretchLastSection(True)
      self.addrBookRxView.verticalHeader().setDefaultSectionSize(20)
      iWidth = tightSizeStr(self.addrBookRxView, 'Imp')[0]
      initialColResize(self.addrBookRxView, [iWidth*1.3, 0.3, 0.35, 64, 0.3])
      self.connect(self.addrBookRxView.selectionModel(), \
                   SIGNAL('currentChanged(const QModelIndex &, const QModelIndex &)'), \
                   self.addrTableRxClicked)


   #############################################################################
   def wltTableClicked(self, currIndex, prevIndex=None):
      if prevIndex==currIndex:
         return 

      self.btnSelectWlt.setEnabled(True)
      row = currIndex.row()
      self.selectedWltID = str(currIndex.model().index(row, WLTVIEWCOLS.ID).data().toString())

      self.setAddrBookTxModel(self.selectedWltID)
      self.setAddrBookRxModel(self.selectedWltID)


      if not self.isBrowsingOnly:
         wlt = self.main.walletMap[self.selectedWltID]
         self.btnSelectWlt.setText('%s Wallet: %s' % (self.actStr, self.selectedWltID))
         nextAddr160 = wlt.peekNextUnusedAddr160()
         self.lblSelectWlt.setText('Will create new address: %s...' % hash160_to_addrStr(nextAddr160)[:10])

         # If switched wallet selection, de-select address so it doesn't look
         # like the currently-selected address is for this different wallet
         self.btnSelectAddr.setEnabled(False)
         self.btnSelectAddr.setText('No Address Selected')
         self.selectedAddr = ''
         self.selectedCmmt = ''
      self.addrBookTxModel.reset()


   #############################################################################
   def addrTableTxClicked(self, currIndex, prevIndex=None):
      if prevIndex==currIndex:
         return 

      self.btnSelectAddr.setEnabled(True)
      row = currIndex.row()
      self.selectedAddr = str(currIndex.model().index(row, ADDRBOOKCOLS.Address).data().toString())
      self.selectedCmmt = str(currIndex.model().index(row, ADDRBOOKCOLS.Comment).data().toString())

      if not self.isBrowsingOnly:
         self.btnSelectAddr.setText('%s Address: %s...' % (self.actStr, self.selectedAddr[:10]))


   #############################################################################
   def addrTableRxClicked(self, currIndex, prevIndex=None):
      if prevIndex==currIndex:
         return 

      self.btnSelectAddr.setEnabled(True)
      row = currIndex.row()
      self.selectedAddr = str(currIndex.model().index(row, ADDRESSCOLS.Address).data().toString())
      self.selectedCmmt = str(currIndex.model().index(row, ADDRESSCOLS.Comment).data().toString())

      if not self.isBrowsingOnly:
         self.btnSelectAddr.setText('%s Address: %s...' % (self.actStr, self.selectedAddr[:10]))


   #############################################################################
   def dblClickAddressRx(self, index):
      if index.column()!=ADDRESSCOLS.Comment:
         self.acceptAddrSelection()
         return

      wlt = self.main.walletMap[self.selectedWltID]

      dialog = DlgSetComment(self.selectedCmmt, 'Address', self, self.main)
      if dialog.exec_():
         newComment = str(dialog.edtComment.text())
         addr160 = addrStr_to_hash160(self.selectedAddr)
         wlt.setComment(addr160, newComment)

   #############################################################################
   def dblClickAddressTx(self, index):
      if index.column()!=ADDRBOOKCOLS.Comment:
         self.acceptAddrSelection()
         return

      wlt = self.main.walletMap[self.selectedWltID]

      dialog = DlgSetComment(self.selectedCmmt, 'Address', self, self.main)
      if dialog.exec_():
         newComment = str(dialog.edtComment.text())
         addr160 = addrStr_to_hash160(self.selectedAddr)
         wlt.setComment(addr160, newComment)

   #############################################################################
   def acceptWltSelection(self):
      wltID = self.selectedWltID
      addr160 = self.main.walletMap[wltID].getNextUnusedAddress().getAddr160()
      self.target.setText(hash160_to_addrStr(addr160))
      self.target.setCursorPosition(0)
      self.accept()
      

   #############################################################################
   def acceptAddrSelection(self):
      if self.target:
         self.target.setText(self.selectedAddr)
         self.target.setCursorPosition(0)
         self.accept()

   #############################################################################
   def showContextMenuTx(self, pos):
      menu = QMenu(self.addrBookTxView)
      std = (self.main.usermode==USERMODE.Standard)
      adv = (self.main.usermode==USERMODE.Advanced)
      dev = (self.main.usermode==USERMODE.Expert)
      
      if True:  actionCopyAddr    = menu.addAction("Copy Address")
      if dev:   actionCopyHash160 = menu.addAction("Copy Hash160 (hex)")
      if True:  actionCopyComment = menu.addAction("Copy Comment")
      idx = self.addrBookTxView.selectedIndexes()[0]
      action = menu.exec_(QCursor.pos())
         
      if action==actionCopyAddr:
         s = self.addrBookTxView.model().index(idx.row(), ADDRBOOKCOLS.Address).data().toString()
      elif dev and action==actionCopyHash160:
         s = str(self.addrBookTxView.model().index(idx.row(), ADDRBOOKCOLS.Address).data().toString())
         s = binary_to_hex(addrStr_to_hash160(s))
      elif action==actionCopyComment:
         s = self.addrBookTxView.model().index(idx.row(), ADDRBOOKCOLS.Comment).data().toString()
      else:
         return

      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(s).strip())


   #############################################################################
   def showContextMenuRx(self, pos):
      menu = QMenu(self.addrBookRxView)
      std = (self.main.usermode==USERMODE.Standard)
      adv = (self.main.usermode==USERMODE.Advanced)
      dev = (self.main.usermode==USERMODE.Expert)
      
      if True:  actionCopyAddr    = menu.addAction("Copy Address")
      if dev:   actionCopyHash160 = menu.addAction("Copy Hash160 (hex)")
      if True:  actionCopyComment = menu.addAction("Copy Comment")
      idx = self.addrBookRxView.selectedIndexes()[0]
      action = menu.exec_(QCursor.pos())
         
      if action==actionCopyAddr:
         s = self.addrBookRxView.model().index(idx.row(), ADDRESSCOLS.Address).data().toString()
      elif dev and action==actionCopyHash160:
         s = str(self.addrBookRxView.model().index(idx.row(), ADDRESSCOLS.Address).data().toString())
         s = binary_to_hex(addrStr_to_hash160(s))
      elif action==actionCopyComment:
         s = self.addrBookRxView.model().index(idx.row(), ADDRESSCOLS.Comment).data().toString()
      else:
         return

      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(s).strip())


################################################################################
def createAddrBookButton(parent, targWidget, defaultWlt, actionStr="Select", selectExistingOnly=False):
   btn = QPushButton('')
   ico = QIcon(QPixmap(':/addr_book_icon.png'))
   btn.setIcon(ico)
   def execAddrBook():
      if len(parent.main.walletMap) == 0:
         QMessageBox.warning(parent, 'No wallets!', 'You have no wallets so '
            'there is no address book to display.', QMessageBox.Ok)
         return
      dlg = DlgAddressBook(parent, parent.main, targWidget,  defaultWlt, actionStr, selectExistingOnly)
      dlg.exec_()

   btn.setMaximumWidth(24)
   btn.setMaximumHeight(24)
   parent.connect(btn, SIGNAL('clicked()'), execAddrBook)
   btn.setToolTip('Select from Address Book')
   return btn


################################################################################
class DlgHelpAbout(ArmoryDialog):
   def __init__(self, putResultInWidget, defaultWltID=None, parent=None, main=None):
      super(DlgHelpAbout, self).__init__(parent)

      imgLogo = QLabel()
      imgLogo.setPixmap(QPixmap(':/armory_logo_h56.png'))
      imgLogo.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      lblHead = QRichLabel('Armory Bitcoin Client : Version %s-beta' % \
                                    getVersionString(BTCARMORY_VERSION), doWrap=False)
      lblWebpage = QRichLabel('<a href="http://www.bitcoinarmory.com">http://www.bitcoinarmory.com</a>')
      lblWebpage.setOpenExternalLinks(True)
      lblCopyright = QRichLabel('Copyright \xa9 2011-2012 Alan C. Reiner')
      lblLicense = QRichLabel('Licensed under the '
                              '<a href="http://www.gnu.org/licenses/agpl-3.0.html">'
                              'Affero General Public License, Version 3</a> (AGPLv3)')
      lblLicense.setOpenExternalLinks(True)

      lblHead.setAlignment(Qt.AlignHCenter)
      lblWebpage.setAlignment(Qt.AlignHCenter)
      lblCopyright.setAlignment(Qt.AlignHCenter)
      lblLicense.setAlignment(Qt.AlignHCenter)

      dlgLayout = QHBoxLayout()
      dlgLayout.addWidget(makeVertFrame([imgLogo, lblHead, lblCopyright, lblWebpage, 'Stretch', lblLicense] ))
      self.setLayout(dlgLayout)

      self.setMinimumWidth(450)

      self.setWindowTitle('About Armory')


################################################################################
class DlgPreferences(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgPreferences, self).__init__(parent, main)



      txFee = self.main.getSettingOrSetDefault('Default_Fee', MIN_TX_FEE)
      lblDefaultFee = QRichLabel('<b>Default fee to include with transactions:</b><br>')
      lblDefaultDescr = QRichLabel( \
                                 'Fees go to users that contribute computing power '
                                 'to keep the Bitcoin network secure and increases '
                                 'the priority of your transactions on the network '
                                 '(%s BTC is standard).' % \
                                 coin2str(MIN_TX_FEE, maxZeros=0).strip())
      ttipDefaultFee = createToolTipObject( \
                                 'NOTE: some transactions will require a certain fee '
                                 'regardless of your preferences -- in such cases '
                                 'you will be prompted to include the correct '
                                 'value or cancel the transaction')
      self.edtDefaultFee = QLineEdit()
      self.edtDefaultFee.setText( coin2str(txFee, maxZeros=1).strip())
      lblDefaultFee.setMinimumWidth(400)

      self.connect(self.edtDefaultFee, SIGNAL('returnPressed()'), self.accept)


      ###############################################################
      # Minimize on Close
      moc = self.main.getSettingOrSetDefault('MinimizeOrClose', 'DontKnow')
      lblMinOrClose = QRichLabel('<b>Minimize to system tray on close:</b>')
      lblMoCDescr   = QRichLabel( 'When you click the "x" on the top window bar, '
                                 'Armory will stay open but run in the background.  '
                                 'You will still receive notifications, and '
                                 'can access it through the system tray.')
      ttipMinOrClose = createToolTipObject( \
         'If this is checked, you can still close Armory through the right-click menu '
         'on the system tray icon, or by "File"->"Quit Armory" on the main window')
      self.chkMinOrClose = QCheckBox('')
      if moc=='Minimize':
         self.chkMinOrClose.setChecked(True)


      #doInclFee = self.main.getSettingOrSetDefault('LedgDisplayFee', True)
      #lblLedgerFee = QRichLabel('<b>Include fee in transaction value on the '
                                #'primary ledger</b>.<br>Unselect if you want to '
                                #'see only the value received by the recipient.')
      #ttipLedgerFee = createToolTipObject( \
                                #'If you send someone 1.0 '
                                #'BTC with a 0.001 fee, the ledger will display '
                                #'"1.001" in the "Amount" column if this option '
                                #'is checked.')
      #self.chkInclFee = QCheckBox('')
      #self.chkInclFee.setChecked(doInclFee)


      ###############################################################
      # Notifications
      lblNotify = QRichLabel('<b>Enable notifcations from the system-tray:</b>')
      notifyBtcIn  = self.main.getSettingOrSetDefault('NotifyBtcIn',  True)
      notifyBtcOut = self.main.getSettingOrSetDefault('NotifyBtcOut', True)
      notifyDiscon = self.main.getSettingOrSetDefault('NotifyDiscon', True)
      notifyReconn = self.main.getSettingOrSetDefault('NotifyReconn', True)

      self.chkBtcIn  = QCheckBox('Bitcoins Received')
      self.chkBtcOut = QCheckBox('Bitcoins Sent')
      self.chkDiscon = QCheckBox('Bitcoin-Qt/bitcoind disconnected')
      self.chkReconn = QCheckBox('Bitcoin-Qt/bitcoind reconnected')
      self.chkBtcIn.setChecked(notifyBtcIn)
      self.chkBtcOut.setChecked(notifyBtcOut)
      self.chkDiscon.setChecked(notifyDiscon)
      self.chkReconn.setChecked(notifyReconn)


      ###############################################################
      # Date format preferences
      exampleTimeTuple = (2012, 4, 29,  19,45, 0,  -1,-1,-1)
      self.exampleUnixTime = time.mktime(exampleTimeTuple)
      exampleStr = unixTimeToFormatStr(self.exampleUnixTime, '%c')
      lblDateFmt   = QRichLabel('<b>Preferred Date Format<b>:<br>')
      lblDateDescr = QRichLabel( \
                          'You can specify how you would like dates '
                          'to be displayed using percent-codes to '
                          'represent components of the date.  The '
                          'mouseover text of the "(?)" icon shows '
                          'the most commonly used codes/symbols.  '
                          'The text next to it shows how '
                          '"%s" would be shown with the '
                          'specified format.' % exampleStr )
      lblDateFmt.setAlignment(Qt.AlignTop)
      fmt = self.main.getPreferredDateFormat()
      ttipStr = 'Use any of the following symbols:<br>'
      fmtSymbols = [x[0] + ' = ' + x[1] for x in FORMAT_SYMBOLS]
      ttipStr += '<br>'.join(fmtSymbols)

      fmtSymbols = [x[0] + '~' + x[1] for x in FORMAT_SYMBOLS]
      lblStk = QRichLabel('; '.join(fmtSymbols))

      self.edtDateFormat = QLineEdit()
      self.edtDateFormat.setText(fmt)
      self.ttipFormatDescr = createToolTipObject( ttipStr )

      self.lblDateExample = QRichLabel( '', doWrap=False)
      self.connect(self.edtDateFormat, SIGNAL('textEdited(QString)'), self.doExampleDate)
      self.doExampleDate()
      self.btnResetFormat = QPushButton("Reset to Default")

      def doReset():
         self.edtDateFormat.setText(DEFAULT_DATE_FORMAT)
         self.doExampleDate()
      self.connect(self.btnResetFormat, SIGNAL('clicked()'), doReset)

      # Make a little subframe just for the date format stuff... everything
      # fits nicer if I do this...
      frmTop = makeHorizFrame([self.lblDateExample, 'Stretch', self.ttipFormatDescr])
      frmMid = makeHorizFrame([self.edtDateFormat])
      frmBot = makeHorizFrame([self.btnResetFormat, 'Stretch'])
      fStack = makeVertFrame( [frmTop, frmMid, frmBot, 'Stretch'])
      lblStk = makeVertFrame( [lblDateFmt, lblDateDescr, 'Stretch'])
      subFrm = makeHorizFrame([lblStk, 'Stretch', fStack])


      ###############################################################
      # SelectCoins preferences
      # NOT ENABLED YET -- BUT WILL BE SOON
      #lblSelectCoin = QRichLabel('<b>Coin Selection Preferences:</b>')
      #lblSelectCoinDescr = QRichLabel( \
            #'When Armory constructs a transaction, there are many different '
            #'ways for it to select from coins that make up your balance. '
            #'The "SelectCoins" algorithm can be set to prefer more-anonymous '
            #'coin selections or to prefer avoiding mandatory transaction fees. '
            #'<B>No guarantees are made about the relative anonymity of the '
            #'coin selection, only that Armory will <i>prefer</i> a transaction '
            #'that requires a fee if it can increase anonymity.</b>')
      #self.cmbSelectCoins = QComboBox()
      #self.cmbSelectCoins.clear()
      #self.cmbSelectCoins.addItem( 'Prefer free transactions' )
      #self.cmbSelectCoins.addItem( 'Maximize anonymity'   )
      #self.cmbSelectCoins.setCurrentIndex(0)
      #i+=1
      #dlgLayout.addWidget(lblSelectCoin,                     i,0)
      #dlgLayout.addWidget(self.cmbSelectCoins,               i,1)
      #i+=1
      #dlgLayout.addWidget(lblSelectCoinDescr,                i,0, 1,2)


      ###############################################################
      # Save/Cancel Button
      self.btnCancel = QPushButton("Cancel")
      self.btnAccept = QPushButton("Save")
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.accept)



      self.cmbUsermode = QComboBox()
      self.cmbUsermode.clear()
      self.cmbUsermode.addItem( 'Standard' )
      self.cmbUsermode.addItem( 'Advanced' )
      self.cmbUsermode.addItem( 'Expert' )

      self.usermodeInit = self.main.usermode

      if self.main.usermode==USERMODE.Standard:
         self.cmbUsermode.setCurrentIndex(0)
      elif self.main.usermode==USERMODE.Advanced:
         self.cmbUsermode.setCurrentIndex(1)
      elif self.main.usermode==USERMODE.Expert:
         self.cmbUsermode.setCurrentIndex(2)

      lblUsermode = QRichLabel('<b>Armory user mode:</b>')
      self.lblUsermodeDescr = QRichLabel('')
      self.setUsermodeDescr()

      self.connect(self.cmbUsermode, SIGNAL('activated(int)'), self.setUsermodeDescr)


      frmLayout = QGridLayout()

      i=0
      frmLayout.addWidget( lblDefaultFee,         i,0 )
      frmLayout.addWidget( ttipDefaultFee,        i,1 )
      frmLayout.addWidget( self.edtDefaultFee,    i,2 )

      i+=1
      frmLayout.addWidget( lblDefaultDescr,       i,0, 1,3)

      i+=1
      frmLayout.addWidget( HLINE(),               i,0, 1,3)

      i+=1
      frmLayout.addWidget(subFrm,                 i,0, 1,3)

      i+=1
      frmLayout.addWidget( HLINE(),               i,0, 1,3)

      i+=1
      frmLayout.addWidget( lblMinOrClose,         i,0 )
      frmLayout.addWidget( ttipMinOrClose,        i,1 )
      frmLayout.addWidget( self.chkMinOrClose,    i,2 )

      i+=1
      frmLayout.addWidget( lblMoCDescr,           i,0, 1,3)

      i+=1
      frmLayout.addWidget( HLINE(),               i,0, 1,3)

      i+=1
      frmLayout.addWidget( lblNotify,             i,0, 1,3)

      i+=1
      frmLayout.addWidget( self.chkBtcIn,         i,0, 1,3)

      i+=1
      frmLayout.addWidget( self.chkBtcOut,        i,0, 1,3)
      
      i+=1
      frmLayout.addWidget( self.chkDiscon,        i,0, 1,3)

      i+=1
      frmLayout.addWidget( self.chkReconn,        i,0, 1,3)

      i+=1
      frmLayout.addWidget( HLINE(),               i,0, 1,3)

      i+=1
      frmLayout.addWidget( lblUsermode,           i,0 )
      frmLayout.addWidget( QLabel(''),            i,1 )
      frmLayout.addWidget( self.cmbUsermode,      i,2 )

      i+=1
      frmLayout.addWidget( self.lblUsermodeDescr, i,0, 1,3)


      frmOptions = QFrame()
      frmOptions.setLayout(frmLayout)

      self.scrollOptions = QScrollArea()
      self.scrollOptions.setWidget(frmOptions)



      dlgLayout = QVBoxLayout()      
      dlgLayout.addWidget(self.scrollOptions)
      dlgLayout.addWidget(makeHorizFrame(['Stretch', self.btnCancel, self.btnAccept]))

      self.setLayout(dlgLayout)
      
      self.setMinimumWidth(650)
      self.setWindowTitle('Armory Preferences')

      # NOTE:  This was getting complicated for a variety of reasons, so switched
      #        to manually constructing the options window.  May come back to this
      #        at a later time.
      #
      # Let's create a scalable list of options.  Each row of this list looks like:
      #
      #     [OptionType, SettingsName, DefaultValue, BoldText, NormalText, Tooltip]
      #
      # SettingsName is the string used in self.main.getSettingOrSetDefault()
      # OptionType can be one of:
      #     {'Checkbox', 'LineEdit', 'Combo|Opt1|Opt2|...', 'Separator', 'Header'} 
      #
      # "Separator adds a horizontal-ruler to separate option groups, and "Header" 
      # is basically a textual separator with no actual option

      #self.Options = []
      #self.Options.append( ['LineEdit', 'Default_Fee', MIN_TX_FEE, \
                           #'Default fee to include with transactions.', \
                           #'Fees go to users that contribute computing power '
                           #'to keep the Bitcoin network secure (0.0005 BTC is '
                           #'standard).', \
                           #'NOTE: some transactions will require a fee '
                           #'regardless of your preferences -- in such cases '
                           #'you will be prompted to include the correct '
                           #'value or abort the transaction'])
          
   def accept(self, *args):
      try:
         defaultFee = str2coin( str(self.edtDefaultFee.text()).replace(' ','') )
         self.main.writeSetting('Default_Fee', defaultFee)
      except:
         QMessageBox.warning(self, 'Invalid Amount', \
                  'The default fee specified could not be understood.  Please '
                  'specify in BTC with no more than 8 decimal places.', \
                  QMessageBox.Ok)
         return

      if not self.main.setPreferredDateFormat(str(self.edtDateFormat.text())):
         return

      if not self.usermodeInit == self.cmbUsermode.currentIndex():
         modestr = str(self.cmbUsermode.currentText())
         if modestr.lower() == 'standard':
            self.main.setUserMode(USERMODE.Standard)
         elif modestr.lower() == 'advanced':
            self.main.setUserMode(USERMODE.Advanced)
         elif modestr.lower() == 'expert':
            self.main.setUserMode(USERMODE.Expert)

      if self.chkMinOrClose.isChecked():
         self.main.writeSetting('MinimizeOrClose', 'Minimize')
      else:
         self.main.writeSetting('MinimizeOrClose', 'Close')

      #self.main.writeSetting('LedgDisplayFee', self.chkInclFee.isChecked())
      self.main.writeSetting('NotifyBtcIn',  self.chkBtcIn.isChecked())
      self.main.writeSetting('NotifyBtcOut', self.chkBtcOut.isChecked())
      self.main.writeSetting('NotifyDiscon', self.chkDiscon.isChecked())
      self.main.writeSetting('NotifyReconn', self.chkReconn.isChecked())

      self.main.createCombinedLedger()
      super(DlgPreferences, self).accept(*args)
      

   #############################################################################
   def setUsermodeDescr(self):
      strDescr = ''
      modestr =  str(self.cmbUsermode.currentText())
      if modestr.lower() == 'standard':
         strDescr += \
            ('"Standard" is for users that only need the core set of features '
             'to send and receive bitcoins.  This includes maintaining multiple '
             'wallets, wallet encryption, and the ability to make backups '
             'of your wallets.')
      elif modestr.lower() == 'advanced':
         strDescr += \
            ('"Advanced" mode provides '
             'extra Armory features such as private key '
             'importing & sweeping, message signing, and the offline wallet '
             'interface.  But, with advanced features come advanced risks...')
      elif modestr.lower() == 'expert':
         strDescr += \
            ('"Expert" mode is similar to "Advanced" but includes '
             'access to lower-level info about transactions, scripts, keys '
             'and network protocol.  Most extra functionality is geared '
             'towards Bitcoin software developers.')
      self.lblUsermodeDescr.setText(strDescr)


   #############################################################################
   def doExampleDate(self, qstr=None):
      fmtstr = str(self.edtDateFormat.text()) 
      try:
         self.lblDateExample.setText('Sample: ' + unixTimeToFormatStr(self.exampleUnixTime, fmtstr))
         self.isValidFormat = True
      except:
         self.lblDateExample.setText('Sample: [[invalid date format]]')
         self.isValidFormat = False


################################################################################
class DlgExportTxHistory(ArmoryDialog):
   def __init__(self, parent=None, main=None):
      super(DlgExportTxHistory, self).__init__(parent, main)



      self.cmbWltSelect = QComboBox()
      self.cmbWltSelect.clear()
      self.cmbWltSelect.addItem( 'My Wallets'        )
      self.cmbWltSelect.addItem( 'Offline Wallets'   )
      self.cmbWltSelect.addItem( 'Other Wallets'  )
      self.cmbWltSelect.addItem( 'All Wallets'       )
      for wltID in self.main.walletIDList:
         self.cmbWltSelect.addItem( self.main.walletMap[wltID].labelName )
      self.cmbWltSelect.insertSeparator(4)
      self.cmbWltSelect.insertSeparator(4)



      self.cmbSortSelect = QComboBox()
      self.cmbSortSelect.clear()
      self.cmbSortSelect.addItem('Date (newest first)')
      self.cmbSortSelect.addItem('Date (oldest first)')
      self.cmbSortSelect.addItem('Transaction ID (ascending)')
      self.cmbSortSelect.addItem('Transaction ID (descending)')


      self.cmbFileFormat = QComboBox()
      self.cmbFileFormat.clear()
      self.cmbFileFormat.addItem('Comma-Separated Values (*.csv)')


      fmt = self.main.getPreferredDateFormat()
      ttipStr = 'Use any of the following symbols:<br>'
      fmtSymbols = [x[0] + ' = ' + x[1] for x in FORMAT_SYMBOLS]
      ttipStr += '<br>'.join(fmtSymbols)

      self.edtDateFormat = QLineEdit()
      self.edtDateFormat.setText(fmt)
      self.ttipFormatDescr = createToolTipObject( ttipStr )
                                                 
      self.lblDateExample = QRichLabel( '', doWrap=False)
      self.connect(self.edtDateFormat, SIGNAL('textEdited(QString)'), self.doExampleDate)
      self.doExampleDate()
      self.btnResetFormat = QPushButton("Reset to Default")

      def doReset():
         self.edtDateFormat.setText(DEFAULT_DATE_FORMAT)
         self.doExampleDate()
      self.connect(self.btnResetFormat, SIGNAL('clicked()'), doReset)



               


      # Add the usual buttons
      self.btnCancel = QPushButton("Cancel")
      self.btnAccept = QPushButton("Export")
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.accept)
      btnBox = makeHorizFrame(['Stretch', self.btnCancel, self.btnAccept])


      dlgLayout = QGridLayout()
   
      i=0
      dlgLayout.addWidget(QRichLabel('Export Format:'),      i,0)
      dlgLayout.addWidget(self.cmbFileFormat,                i,1)

      i+=1
      dlgLayout.addWidget(HLINE(),                           i,0, 1,2)

      i+=1
      dlgLayout.addWidget(QRichLabel('Wallet(s) to export:'),i,0)
      dlgLayout.addWidget(self.cmbWltSelect,                 i,1)

      i+=1
      dlgLayout.addWidget(HLINE(),                           i,0, 1,2)
      
      i+=1
      dlgLayout.addWidget(QRichLabel('Sort Table:'),         i,0)
      dlgLayout.addWidget(self.cmbSortSelect,                i,1)

      i+=1
      dlgLayout.addWidget(HLINE(),                           i,0, 1,2)

      i+=1
      dlgLayout.addWidget(QRichLabel('Date Format:'),        i,0)
      fmtfrm = makeHorizFrame([self.lblDateExample, 'Stretch', self.ttipFormatDescr])
      dlgLayout.addWidget(fmtfrm,                            i,1)

      i+=1
      dlgLayout.addWidget(self.btnResetFormat,               i,0)
      dlgLayout.addWidget(self.edtDateFormat,                i,1)

      i+=1
      dlgLayout.addWidget(HLINE(),                           i,0, 1,2)

      i+=1
      dlgLayout.addWidget(HLINE(),                           i,0, 1,2)

      i+=1
      dlgLayout.addWidget(btnBox,                            i,0, 1,2)

      self.setLayout(dlgLayout)




   #############################################################################
   def doExampleDate(self, qstr=None):
      fmtstr = str(self.edtDateFormat.text()) 
      try:
         self.lblDateExample.setText('Example: ' + unixTimeToFormatStr(1030501970, fmtstr))
         self.isValidFormat = True
      except:
         self.lblDateExample.setText('Example: [[invalid date format]]')
         self.isValidFormat = False

   #############################################################################
   def accept(self, *args):
      if self.createFile_CSV():
         super(DlgExportTxHistory, self).accept(*args)


   #############################################################################
   def createFile_CSV(self):
      if not self.isValidFormat:
         QMessageBox.warning(self, 'Invalid date format', \
                  'Cannot create CSV without a valid format for transaction '
                  'dates and times', QMessageBox.Ok)
         return False
         
      # This was pretty much copied from the createCombinedLedger method...
      # I rarely do this, but modularizing this piece is a non-trivial
      wltIDList = []
      typelist = [[wid, determineWalletType(self.main.walletMap[wid], self.main)[0]] \
                                                   for wid in self.main.walletIDList]
      currIdx = self.cmbWltSelect.currentIndex()
      if currIdx>=4:
         wltIDList = [self.main.walletIDList[currIdx-6]]
      else:
         listOffline  = [t[0] for t in filter(lambda x: x[1]==WLTTYPES.Offline,   typelist)]
         listWatching = [t[0] for t in filter(lambda x: x[1]==WLTTYPES.WatchOnly, typelist)]
         listCrypt    = [t[0] for t in filter(lambda x: x[1]==WLTTYPES.Crypt,     typelist)]
         listPlain    = [t[0] for t in filter(lambda x: x[1]==WLTTYPES.Plain,     typelist)]
         
         if currIdx==0:
            wltIDList = listOffline + listCrypt + listPlain
         elif currIdx==1:
            wltIDList = listOffline
         elif currIdx==2:
            wltIDList = listWatching
         elif currIdx==3:
            wltIDList = self.main.walletIDList
         else:
            pass

      totalFunds,spendFunds,unconfFunds,combinedLedger = 0,0,0,[]
      for wltID in wltIDList:
         wlt = self.main.walletMap[wltID]
         id_le_pairs = [[wltID, le] for le in wlt.getTxLedger('Full')]
         combinedLedger.extend(id_le_pairs)
         totalFunds += wlt.getBalance('Total')
         spendFunds += wlt.getBalance('Spendable')
         unconfFunds += wlt.getBalance('Unconfirmed')
      # END createCombinedLedger copy

      ledgerTable = self.main.convertLedgerToTable(combinedLedger)

      sortTxt = str(self.cmbSortSelect.currentText())
      if 'newest' in sortTxt:
         ledgerTable.sort(key=lambda x: x[LEDGERCOLS.UnixTime], reverse=True)
      elif 'oldest' in sortTxt:
         ledgerTable.sort(key=lambda x: x[LEDGERCOLS.UnixTime])
      elif 'ascend' in sortTxt:
         ledgerTable.sort(key=lambda x: hex_switchEndian(x[LEDGERCOLS.TxHash]))
      elif 'descend' in sortTxt:
         ledgerTable.sort(key=lambda x: hex_switchEndian(x[LEDGERCOLS.TxHash]), reverse=True)
      else:
         LOGERROR('***ERROR: bad sort string!?')
         return


      wltSelectStr = str(self.cmbWltSelect.currentText()).replace(' ','_')
      timestampStr = unixTimeToFormatStr(RightNow(), '%Y%m%d_%H%M')
      filenamePrefix = 'ArmoryTxHistory_%s_%s' % (wltSelectStr, timestampStr) 
      fmtstr = str(self.cmbFileFormat.currentText())
      if 'csv' in fmtstr:
         defaultName = filenamePrefix + '.csv' 
         fullpath = self.main.getFileSave( 'Save CSV File', \
                                           ['Comma-Separated Values (*.csv)'], \
                                           defaultName)

         if len(fullpath)==0:
            return

         f = open(fullpath, 'w')

         f.write('Export Date:, %s\n' % unixTimeToFormatStr(RightNow()))
         f.write('Total Funds:, %s\n' % coin2str(totalFunds, maxZeros=0).strip())
         f.write('Spendable Funds:, %s\n' % coin2str(spendFunds, maxZeros=0).strip())
         f.write('Unconfirmed Funds:, %s\n' % coin2str(unconfFunds, maxZeros=0).strip())
         f.write('\n')

         f.write('Included Wallets:\n')
         for wltID in wltIDList:
            wlt = self.main.walletMap[wltID]
            f.write('%s,%s\n' % (wltID, wlt.labelName.replace(',',';')))
         f.write('\n')

         f.write('Date,Transaction ID,#Conf,Wallet ID, Wallet Name,Total Credit,Total Debit,Fee (wallet paid),Comment\n')
         COL = LEDGERCOLS
         for row in ledgerTable:
            vals = []

            fmtstr = str(self.edtDateFormat.text())
            unixTime = row[COL.UnixTime]
            vals.append( unixTimeToFormatStr(unixTime, fmtstr) )
            vals.append( hex_switchEndian(row[COL.TxHash]) )
            vals.append( row[COL.NumConf] )
            vals.append( row[COL.WltID] )
            vals.append( self.main.walletMap[row[COL.WltID]].labelName.replace(',',';'))

            wltEffect = row[COL.Amount]
            txFee = self.main.getFeeForTx(hex_to_binary(row[COL.TxHash]))
            if float(wltEffect) > 0:
               vals.append( wltEffect.strip() )
               vals.append( ' ' )
               vals.append( ' ' )
            else:
               vals.append( ' ' )
               vals.append( wltEffect.strip() )
               vals.append( coin2str(-txFee).strip() )

            vals.append( row[COL.Comment] )

            f.write('%s,%s,%d,%s,%s,%s,%s,%s,"%s"\n' % tuple(vals))

         f.close()
      return True


################################################################################
class DlgRequestPayment(ArmoryDialog):
   def __init__(self, parent, main, recvAddr, amt=None, msg=''):
      super(DlgRequestPayment, self).__init__(parent, main)


      if isLikelyDataType(recvAddr, DATATYPE.Binary) and len(recvAddr)==20:
         self.recvAddr = hash160_to_addrStr(recvAddr)
      elif isLikelyDataType(recvAddr, DATATYPE.Base58):
         self.recvAddr = recvAddr
      else:
         raise BadAddressError, 'Unrecognized address input'


      # Amount
      self.edtAmount = QLineEdit()
      self.edtAmount.setFont(GETFONT('Fixed'))
      self.edtAmount.setMaximumWidth(relaxedSizeNChar(GETFONT('Fixed'), 13)[0])
      if amt:
         self.edtAmount.setText( coin2str(amt, maxZeros=0) )


      # Message:
      self.edtMessage = QLineEdit()
      self.edtMessage.setMaxLength(128)
      if msg:
         self.edtMessage.setText(msg)
      else:
         self.edtMessage.setText('Joe\'s Fish Shop - Order #123 - 3 kg tuna - (888)555-1212' )
      self.edtMessage.setCursorPosition(0)



      # Address:
      self.edtAddress = QLineEdit()
      self.edtAddress.setText(self.recvAddr)

      # Link Text:
      self.edtLinkText = QLineEdit()
      defaultText = binary_to_hex('Click here to pay for your order!')
      linkText = hex_to_binary(self.main.getSettingOrSetDefault('DefaultLinkText',defaultText))
      self.edtLinkText.setText(linkText)
      self.edtLinkText.setCursorPosition(0)

      qpal = QPalette()
      qpal.setColor(QPalette.Text, Colors.TextBlue)
      self.edtLinkText.setPalette(qpal)
      edtFont = self.edtLinkText.font()
      edtFont.setUnderline(True)
      self.edtLinkText.setFont(edtFont)

	

      self.connect(self.edtMessage,  SIGNAL('textChanged(QString)'), self.setLabels)
      self.connect(self.edtAddress,  SIGNAL('textChanged(QString)'), self.setLabels)
      self.connect(self.edtAmount,   SIGNAL('textChanged(QString)'), self.setLabels)
      self.connect(self.edtLinkText, SIGNAL('textChanged(QString)'), self.setLabels)

      self.connect(self.edtMessage,  SIGNAL('editingFinished()'), self.updateQRCode)
      self.connect(self.edtAddress,  SIGNAL('editingFinished()'), self.updateQRCode)
      self.connect(self.edtAmount,   SIGNAL('editingFinished()'), self.updateQRCode)
      self.connect(self.edtLinkText, SIGNAL('editingFinished()'), self.updateQRCode)


      # This is the "output"
      self.lblLink = QRichLabel('')
      self.lblLink.setOpenExternalLinks(True)
      self.lblLink.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
      self.lblLink.setMinimumHeight( 3*tightSizeNChar(self, 1)[1] )
      self.lblLink.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
      self.lblLink.setContentsMargins(10,5,10,5)
      self.lblLink.setStyleSheet('QLabel { background-color : %s }' % htmlColor('SlightBkgdDark'))
      frmOut = makeHorizFrame([self.lblLink], QFrame.Box | QFrame.Raised)
      frmOut.setLineWidth(1)
      frmOut.setMidLineWidth(5)


      self.lblWarn = QRichLabel('')
      self.lblWarn.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

      self.btnOtherOpt = QPushButton('Other Options >>>')
      self.btnCopyRich = QPushButton('Copy to Clipboard')
      self.btnCopyHtml = QPushButton('Copy Raw HTML')
      self.btnCopyRaw  = QPushButton('Copy Raw URL')
      self.btnCopyAll  = QPushButton('Copy All Text')

      # I never actally got this button working right...
      self.btnCopyRich.setVisible(True)
      self.btnOtherOpt.setCheckable(True)
      self.btnCopyAll.setVisible(False)
      self.btnCopyHtml.setVisible(False)
      self.btnCopyRaw.setVisible(False)
      frmCopyBtnStrip = makeHorizFrame([ \
                                        self.btnCopyRich, \
                                        self.btnOtherOpt, \
                                        self.btnCopyHtml, \
                                        self.btnCopyRaw, \
                                        'Stretch', \
                                        self.lblWarn])
                                        #self.btnCopyAll, \

      self.connect(self.btnCopyRich, SIGNAL('clicked()'),     self.clickCopyRich)
      self.connect(self.btnOtherOpt, SIGNAL('toggled(bool)'), self.clickOtherOpt)
      self.connect(self.btnCopyRaw,  SIGNAL('clicked()'),     self.clickCopyRaw )
      self.connect(self.btnCopyHtml, SIGNAL('clicked()'),     self.clickCopyHtml)
      self.connect(self.btnCopyAll,  SIGNAL('clicked()'),     self.clickCopyAll)

      lblDescr = QRichLabel( \
         'Create a clickable link that you can copy into email or webpage to '
         'request a payment.   If the user is running a Bitcoin program ' 
         'that supports "bitcoin:" links, that program will open with '
         'all this information pre-filled after they click the link.')

      lblDescr.setContentsMargins(5, 5, 5, 5)
      frmDescr = makeHorizFrame([lblDescr], STYLE_SUNKEN)


      ttipPreview = createToolTipObject( \
         'The following Bitcoin desktop applications <i>try</i> to '
         'register themselves with your computer to handle "bitcoin:" '
         'links: Armory, Multibit, Electrum')
      ttipLinkText = createToolTipObject( \
         'This is the text to be shown as the clickable link.  It should '
         'usually begin with "Click here..." to reaffirm to the user it is '
         'is clickable.')
      ttipAmount = createToolTipObject( \
         'All amounts are specifed in BTC')
      ttipAddress = createToolTipObject( \
         'The person clicking the link will be sending bitcoins to this address')
      ttipMessage = createToolTipObject( \
         'This text will be pre-filled as the label/comment field '
         'after the user clicks on the link. They '
         'can modify it to meet their own needs, but you can '
         'provide useful information such as contact details and '
         'purchase info as a convenience to them.')


      btnClose = QPushButton('Close')
      self.connect(btnClose, SIGNAL('clicked()'), self.accept)


      frmEntry = QFrame()
      frmEntry.setFrameStyle(STYLE_SUNKEN)
      layoutEntry = QGridLayout()
      i=0
      layoutEntry.addWidget(QRichLabel('<b>Link Text:</b>'),        i,0)
      layoutEntry.addWidget(self.edtLinkText,                       i,1)
      layoutEntry.addWidget(ttipLinkText,                           i,2)

      i+=1
      layoutEntry.addWidget(QRichLabel('<b>Address (yours):</b>'),  i,0)
      layoutEntry.addWidget(self.edtAddress,                        i,1)
      layoutEntry.addWidget(ttipAddress,                            i,2)

      i+=1
      layoutEntry.addWidget(QRichLabel('<b>Request (BTC):</b>'),    i,0)
      layoutEntry.addWidget(self.edtAmount,                         i,1)

      i+=1
      layoutEntry.addWidget(QRichLabel('<b>Message:</b>'),          i,0)
      layoutEntry.addWidget(self.edtMessage,                        i,1)
      layoutEntry.addWidget(ttipMessage,                            i,2)
      frmEntry.setLayout(layoutEntry)
      

      lblOut = QRichLabel('Copy and paste the following text into email or other document:')
      frmOutput = makeVertFrame([lblOut, frmOut, frmCopyBtnStrip], STYLE_SUNKEN)
      frmOutput.layout().setStretch(0, 0)
      frmOutput.layout().setStretch(1, 1)
      frmOutput.layout().setStretch(2, 0)
      frmClose = makeHorizFrame(['Stretch', btnClose])


      self.qrURI = QRCodeWidget('', parent=self)
      lblQRDescr = QRichLabel('This QR code contains address <b>and</b> the '
                              'other payment information shown to the left.')

      lblQRDescr.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
      frmQR = makeVertFrame([self.qrURI, 'Stretch', lblQRDescr,'Stretch'], STYLE_SUNKEN)
      frmQR.layout().setStretch(0, 0)
      frmQR.layout().setStretch(1, 0)
      frmQR.layout().setStretch(2, 1)

      self.maxQRSize = int(1.25*QRCodeWidget('a'*200).getSize())
      frmQR.setMinimumWidth(self.maxQRSize)
      self.qrURI.setMinimumHeight(self.maxQRSize)


      dlgLayout = QGridLayout()

      dlgLayout.addWidget(frmDescr,   0,0,  1,2)
      dlgLayout.addWidget(frmEntry,   1,0,  1,1)
      dlgLayout.addWidget(frmOutput,  2,0,  1,1)
      dlgLayout.addWidget(HLINE(),    3,0,  1,2)
      dlgLayout.addWidget(frmClose,   4,0,  1,2)

      dlgLayout.addWidget(frmQR,  1,1,  2,1)

      dlgLayout.setRowStretch(0, 0)
      dlgLayout.setRowStretch(1, 0)
      dlgLayout.setRowStretch(2, 1)
      dlgLayout.setRowStretch(3, 0)
      dlgLayout.setRowStretch(4, 0)
      

      self.setLabels()
      self.prevURI = ''
      self.closed = False  # kind of a hack to end the update loop
      self.updateQRCode()
      self.setLayout(dlgLayout)
      self.setWindowTitle('Create Payment Request Link')

      from twisted.internet import reactor
      reactor.callLater(1, self.periodicUpdate)

      hexgeom = str(self.main.settings.get('PayReqestGeometry'))
      if len(hexgeom)>0:
         geom = QByteArray.fromHex(hexgeom)
         self.restoreGeometry(geom)
      self.setMinimumSize(750,500)


   def saveLinkText(self):
      linktext = str(self.edtLinkText.text()).strip()
      if len(linktext)>0:
         hexText = binary_to_hex(linktext)
         self.main.writeSetting('DefaultLinkText',hexText)
         

   #############################################################################
   def saveGeometrySettings(self):
      self.main.writeSetting('PayReqestGeometry', str(self.saveGeometry().toHex()))

   #############################################################################
   def closeEvent(self, event):
      self.saveGeometrySettings()
      self.saveLinkText()
      super(DlgRequestPayment, self).closeEvent(event)

   #############################################################################
   def accept(self, *args):
      self.saveGeometrySettings()
      self.saveLinkText()
      super(DlgRequestPayment, self).accept(*args)

   #############################################################################
   def reject(self, *args):
      self.saveGeometrySettings()
      super(DlgRequestPayment, self).reject(*args)


   #############################################################################
   def setLabels(self):
      
      lastTry = ''
      try:
         # The 
         lastTry = 'Amount'
         amtStr = str(self.edtAmount.text()).strip()
         if len(amtStr)==0:
            amt = None
         else:
            amt = str2coin(amtStr)
   
         lastTry = 'Message'
         msgStr = str(self.edtMessage.text()).strip()
         if len(msgStr)==0:
            msgStr = None
         
         lastTry = 'Address'
         addr = str(self.edtAddress.text()).strip()
         if not checkAddrStrValid(addr):
            raise

         errorIn = 'Inputs'
         # must have address, maybe have amount and/or message
         self.rawURI = createBitcoinURI(addr, amt, msgStr)
      except:
         self.lblWarn.setText('<font color="red">Invalid %s</font>' % lastTry)
         self.btnCopyRaw.setEnabled(False)
         self.btnCopyHtml.setEnabled(False)
         self.btnCopyAll.setEnabled(False)
         #self.lblLink.setText('<br>'.join(str(self.lblLink.text()).split('<br>')[1:]))
         self.lblLink.setEnabled(False)
         self.lblLink.setTextInteractionFlags(Qt.NoTextInteraction)
         return
      
      self.lblLink.setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                           Qt.TextSelectableByKeyboard)

      self.rawHtml = '<a href="%s">%s</a>' % (self.rawURI, str(self.edtLinkText.text()))
      self.lblWarn.setText('')
      self.dispText = self.rawHtml[:]
      self.dispText += '<br>'
      self.dispText += 'If clicking on the line above does not work, use this payment info:'
      self.dispText += '<br>'
      self.dispText += '<b>Pay to</b>:\t%s<br>' % addr
      if amtStr:
         self.dispText += '<b>Amount</b>:\t%s BTC<br>' % coin2str(amt,maxZeros=0).strip()
      if msgStr:
         self.dispText += '<b>Message</b>:\t%s<br>' % msgStr
      self.lblLink.setText(self.dispText)

      self.lblLink.setEnabled(True)
      self.btnCopyRaw.setEnabled(True)
      self.btnCopyHtml.setEnabled(True)
      self.btnCopyAll.setEnabled(True)

      # Plain text to copy to clipboard as "text/plain"
      self.plainText  = str(self.edtLinkText.text()) + '\n'
      self.plainText += 'If clicking on the line above does not work, use this payment info:\n'
      self.plainText += 'Pay to:  %s' % addr
      if amtStr:
         self.plainText += '\nAmount:  %s BTC' % coin2str(amt,maxZeros=0).strip()
      if msgStr:
         self.plainText += '\nMessage: %s' % msgStr
      self.plainText += '\n'

      # The rich-text to copy to the clipboard, as "text/html"
      self.clipText = ( \
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" '
            '"http://www.w3.org/TR/REC-html40/strict.dtd"> '
            '<html><head><meta name="qrichtext" content="1" />'
            '<meta http-equiv="Content-Type" content="text/html; '
            'charset=utf-8" /><style type="text/css"> p, li '
            '{ white-space: pre-wrap; } </style></head><body>'
            '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; '
            'margin-right:0px; -qt-block-indent:0; text-indent:0px;">'
            '<!--StartFragment--><a href="%s">'
            '<span style=" text-decoration: underline; color:#0000ff;">'
            '%s</span></a><br />'
            'If clicking on the line above does not work, use this payment info:'
            '<br /><span style=" font-weight:600;">Pay to</span>: %s') % \
            (self.rawURI, str(self.edtLinkText.text()), addr)
      if amt:
         self.clipText += ('<br /><span style=" font-weight:600;">Amount'
                           '</span>: %s' % coin2str(amt,maxZeros=0))
      if msgStr:
         self.clipText += ('<br /><span style=" font-weight:600;">Message'
                           '</span>: %s' % msgStr)
      self.clipText += '<!--EndFragment--></p></body></html>'

   def periodicUpdate(self, nsec=1):
      if not self.closed:
         from twisted.internet import reactor
         self.updateQRCode()
         reactor.callLater(nsec, self.periodicUpdate)


   def accept(self, *args):
      # Kind of a hacky way to get the loop to end, but it seems to work
      self.closed = True
      super(DlgRequestPayment, self).accept(*args)

   def reject(self, *args):
      # Kind of a hacky way to get the loop to end, but it seems to work
      self.closed = True
      super(DlgRequestPayment, self).reject(*args)

   def updateQRCode(self,e=None):
      if not self.prevURI==self.rawURI:
         self.qrURI.setAsciiData(self.rawURI)
         self.qrURI.setPreferredSize(self.maxQRSize-10, 'max')
         self.repaint()
      self.prevURI = self.rawURI

   def clickCopyRich(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      qmd = QMimeData()
      if OS_WINDOWS:
         qmd.setText(self.plainText)
         qmd.setHtml(self.clipText)
      else:
         prefix = '<meta http-equiv="content-type" content="text/html; charset=utf-8">'
         qmd.setText(self.plainText)
         qmd.setHtml(prefix + self.dispText)
      clipb.setMimeData(qmd)
      self.lblWarn.setText('<i>Copied!</i>')
      


   def clickOtherOpt(self, boolState):
      self.btnCopyHtml.setVisible(boolState)
      self.btnCopyRaw.setVisible(boolState)

      if boolState:
         self.btnOtherOpt.setText('Hide Buttons <<<')
      else:
         self.btnOtherOpt.setText('Other Options >>>')

   def clickCopyRaw(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.rawURI)
      self.lblWarn.setText('<i>Copied!</i>')

   def clickCopyHtml(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.rawHtml)
      self.lblWarn.setText('<i>Copied!</i>')

   def clickCopyAll(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      qmd = QMimeData()
      qmd.setHtml(self.dispText)
      clipb.setMimeData(qmd)
      self.lblWarn.setText('<i>Copied!</i>')




################################################################################
class DlgVersionNotify(ArmoryDialog):
   def __init__(self, parent, main, changelog, wasRequested=False):
      super(DlgVersionNotify, self).__init__(parent, main)

      self.myVersion    = getVersionInt(BTCARMORY_VERSION)
      self.latestVer    = getVersionInt(readVersionString(changelog[0][0]))
      self.myVersionStr = getVersionString(BTCARMORY_VERSION)
      self.latestVerStr = getVersionString(readVersionString(changelog[0][0]))
      lblDescr = QRichLabel('')

      if self.myVersion >= self.latestVer:
         lblDescr = QRichLabel( \
            '<font size=4><u><b>Your Armory installation is up-to-date!</b>'
            '</u></font>'
            '<br><br>'
            '<b>Installed Version</b>: %s'
            '<br><br>'
            'When they become available, you can find and download new '
            'versions of Armory from:<br><br> '
            '<a href="http://bitcoinarmory.com/index.php/get-armory">'
            'http://bitcoinarmory.com/index.php/get-armory</a> ' % self.myVersionStr)
            
      else:
         lblDescr = QRichLabel( \
            '<font size=4><u><b>There is a new version of Armory available!</b>'
            '</u></font>'
            '<br><br>'
            '<b>Current Version</b>: %s<br>'
            '<b>Lastest Version</b>: %s'
            '<br><br>'
            'Please visit the '
            '<a href="http://bitcoinarmory.com/index.php/get-armory">Armory '
            'download page</a> (http://bitcoinarmory.com/index.php/get-armory) '
            'to get the most recent version. '
            'All your wallets and settings will remain untouched when you '
            'reinstall Armory.' % (self.myVersionStr, self.latestVerStr))

      lblDescr.setOpenExternalLinks(True)

      lblChnglog = QRichLabel('')
      if wasRequested:
         lblChnglog = QRichLabel("<b>Changelog</b>:")
      else:
         lblChnglog = QRichLabel('New features added between version %s and %s:' % \
                                                (self.myVersionStr,self.latestVerStr))


      
      txtChangeLog = QTextEdit()
      txtChangeLog.setReadOnly(True)

      w,h = tightSizeNChar(self, 100)
      w = min(w,600)
      h = min(h,400)
      txtChangeLog.sizeHint = lambda: QSize(w,15*h)

      for versionTbl in changelog:
         versionStr  = versionTbl[0]
         featureList = versionTbl[1]
         txtChangeLog.insertHtml('<b><u>Version %s</u></b><br><br>' % versionStr)
         for feat in featureList:
            txtChangeLog.insertHtml('<b>%s</b><br>' % feat[0])
            for dtxt in feat[1]:
               txtChangeLog.insertHtml('%s<br>' % dtxt)
         txtChangeLog.insertHtml('<br><br>')

      curs = txtChangeLog.textCursor()
      curs.movePosition(QTextCursor.Start)
      txtChangeLog.setTextCursor(curs)

      btnDNAA  = QPushButton('&Do not notify me of new versions')
      btnDelay = QPushButton('&No more reminders until next version')
      btnOkay  = QPushButton('&OK')
      self.connect(btnDNAA,  SIGNAL('clicked()'), self.clickDNAA)
      self.connect(btnDelay, SIGNAL('clicked()'), self.clickDelay)
      self.connect(btnOkay,  SIGNAL('clicked()'), self.clickOkay)
            
      frmDescr = makeVertFrame([lblDescr], STYLE_SUNKEN)
      frmLog   = makeVertFrame([lblChnglog, 'Space(5)', txtChangeLog], STYLE_SUNKEN)
      frmBtn   = makeHorizFrame([btnDNAA, btnDelay, 'Stretch', btnOkay], STYLE_SUNKEN)
      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(frmDescr)
      dlgLayout.addWidget(frmLog)
      dlgLayout.addWidget(frmBtn)
      dlgLayout.setContentsMargins(20,20,20,20)
      
      self.setLayout(dlgLayout)   
      self.setWindowTitle('New Armory Version')
      self.setWindowIcon(QIcon(self.main.iconfile))


   def clickDNAA(self):
      self.main.writeSetting('CheckVersion', 'Never')
      self.accept()

   def clickDelay(self):
      self.main.settings.set('CheckVersion', 'v'+self.latestVerStr)
      self.accept()

   def clickOkay(self):
      self.main.writeSetting('CheckVersion', 'Always')
      self.accept()
      




################################################################################
class DlgUriCopyAndPaste(ArmoryDialog):
   def __init__(self, parent, main):
      super(DlgUriCopyAndPaste, self).__init__(parent, main)

      self.uriDict = {}
      lblDescr = QRichLabel('Copy and paste a raw bitcoin URL string here.  '
                            'A valid string starts with "bitcoin:" followed '
                            'by a bitcoin address.'
                            '<br><br>'
                            'You should use this feature if there is a "bitcoin:" '
                            'link in a webpage or email that does not load Armory '
                            'when you click on it.  Instead, right-click on the '
                            'link and select "Copy Link Location" then paste it '
                            'into the box below. '  )

      lblShowExample = QLabel()
      lblShowExample.setPixmap(QPixmap(':/armory_rightclickcopy.png'))

      self.txtUriString = QLineEdit()
      self.txtUriString.setFont( GETFONT('Fixed', 8))

      self.btnOkay   = QPushButton('Done')
      self.btnCancel = QPushButton('Cancel')
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnOkay,   QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      self.connect(self.btnOkay, SIGNAL('clicked()'), self.clickedOkay)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)

      frmImg = makeHorizFrame(['Stretch',lblShowExample,'Stretch'])


      layout = QVBoxLayout()
      layout.addWidget(lblDescr)
      layout.addWidget(HLINE())
      layout.addWidget(frmImg)
      layout.addWidget(HLINE())
      layout.addWidget(self.txtUriString)
      layout.addWidget(buttonBox)
      self.setLayout(layout)


   def clickedOkay(self):
      uriStr = str(self.txtUriString.text())
      self.uriDict = self.main.parseUriLink(uriStr, 'enter') 
      self.accept()
      




class DlgCoinControl(ArmoryDialog):
   def __init__(self, parent, main, wlt, currSelect=None):
      super(DlgCoinControl, self).__init__(parent, main)

      self.wlt = wlt

      lblDescr = QRichLabel( \
         'By default, transactions are created using any available coins from '
         'all addresses in this wallet.  You can control the source addresses '
         'used for this transaction by selecting them below, and unchecking '
         'all other addresses.')

      self.chkSelectAll = QCheckBox('Select All')
      self.chkSelectAll.setChecked(True)
      self.connect(self.chkSelectAll, SIGNAL('clicked()'), self.clickAll)

      addrToInclude = []
      totalBal = 0
      for addr160 in wlt.addrMap.iterkeys():
         bal = wlt.getAddrBalance(addr160)
         if bal > 0:
            addrToInclude.append([addr160,bal])
            totalBal += bal
         
      frmTableLayout = QGridLayout()
      self.dispTable = []
      frmTableLayout.addWidget(QRichLabel('<b>Address</b>'), 0,0)
      frmTableLayout.addWidget(VLINE(),   0,1)
      frmTableLayout.addWidget(QRichLabel('<b>Balance</b>'), 0,2)
      frmTableLayout.addWidget(VLINE(),   0,3)
      frmTableLayout.addWidget(QRichLabel('<b>Comment</b>'), 0,4)
      frmTableLayout.addWidget(HLINE(), 1,0, 1,5)
      for i in range(len(addrToInclude)):
         a160,bal = addrToInclude[i]
         fullcmt = self.wlt.getCommentForAddress(a160)
         shortcmt = fullcmt
         if shortcmt==CHANGE_ADDR_DESCR_STRING:
            shortcmt = '<i>Change Address</i>'
            fullcmt = '(This address was created only to receive change from another transaction)'
         elif len(shortcmt)>20:
            shortcmt = fullcmt[:20]+'...'
         self.dispTable.append([None, None, None])
         self.dispTable[-1][0] = QCheckBox(hash160_to_addrStr(a160))
         self.dispTable[-1][1] = QMoneyLabel(bal)
         self.dispTable[-1][2] = QRichLabel(shortcmt, doWrap=False)
         self.dispTable[-1][0].setChecked(currSelect==None or (a160 in currSelect))
         if len(shortcmt)>0:
            self.dispTable[-1][0].setToolTip('<u></u>'+fullcmt)
            self.dispTable[-1][1].setToolTip('<u></u>'+fullcmt)
            self.dispTable[-1][2].setToolTip('<u></u>'+fullcmt)
         self.connect(self.dispTable[-1][0], SIGNAL('clicked()'), self.clickOne)
         frmTableLayout.addWidget(self.dispTable[-1][0], i+2,0)
         frmTableLayout.addWidget(VLINE(),               i+2,1)
         frmTableLayout.addWidget(self.dispTable[-1][1], i+2,2)
         frmTableLayout.addWidget(VLINE(),               i+2,3)
         frmTableLayout.addWidget(self.dispTable[-1][2], i+2,4)
      
      frmTable = QFrame()
      frmTable.setLayout(frmTableLayout)
      self.scrollAddrList = QScrollArea()
      self.scrollAddrList.setWidget(frmTable)

      self.sizeHint = lambda: QSize(frmTable.width()+40, 400)

      lblDescrSum = QRichLabel('Balance of selected addresses:',  doWrap=False)
      self.lblSum = QMoneyLabel(totalBal, wBold=True)
      frmSum = makeHorizFrame(['Stretch', lblDescrSum, self.lblSum, 'Stretch'])

      self.btnAccept = QPushButton("Accept")
      self.btnCancel = QPushButton("Cancel")
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.acceptSelection)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      layout = QGridLayout()
      layout.addWidget(lblDescr,            0,0)
      layout.addWidget(self.chkSelectAll,   1,0)
      layout.addWidget(self.scrollAddrList, 2,0)
      layout.addWidget(frmSum,              3,0)
      layout.addWidget(buttonBox,           4,0)
      layout.setRowStretch(0, 0)
      layout.setRowStretch(1, 0)
      layout.setRowStretch(2, 1)
      layout.setRowStretch(3, 0)
      layout.setRowStretch(4, 0)
      self.setLayout(layout)

      self.recalcBalance()
      
      self.setWindowTitle('Coin Control (Expert)')

   def clickAll(self):
      for dispList in self.dispTable:
         dispList[0].setChecked( self.chkSelectAll.isChecked() )
      self.recalcBalance()

   def clickOne(self):
      self.recalcBalance()


   def recalcBalance(self):
      totalBal = 0
      for dispList in self.dispTable:
         if dispList[0].isChecked():
            a160 = addrStr_to_hash160(str(dispList[0].text()))
            totalBal += self.wlt.getAddrBalance(a160)
         else:
            self.chkSelectAll.setChecked(False)

      self.lblSum.setValueText(totalBal)
            
      

   def acceptSelection(self):
      self.coinControlList = []
      for dispList in self.dispTable:
         if dispList[0].isChecked():
            a160 = addrStr_to_hash160(str(dispList[0].text()))
            bal = self.wlt.getAddrBalance(a160)
            self.coinControlList.append([a160, bal])

      if len(self.coinControlList)==0:
         QMessageBox.warning(self, 'Nothing Selected', \
            'You must select at least one address to fund your '
            'transaction.', QMessageBox.Ok)
         return

      self.accept()


# STUB
class dlgRawTx(ArmoryDialog):
   def __init__(self, parent, main):
      super(DlgVersionNotify, self).__init__(parent, main)

      
      lblRaw = QRichLabel('You may paste raw transaction data into the box below, '
                          'and then click "Broadcast" to send it to the Bitcoin '
                          'network.  If the transaction has been broadcast before, '
                          'attempting to send it again is unlikely to do anything.')

      self.txtRawTx = QTextEdit()
      self.txtRawTx.setFont( GETFONT('Fixed',8) )
      #self.txtRawTx.sizeHint = lambda: QSize(w,h)
      self.txtRawTx.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

      self.connect(self.txtRawTx, SIGNAL('textChanged()'), self.processTx)
      
      self.btnBroadcast = QPushButton("Broadcast")
      self.connect(self.btnBroadcast, SIGNAL('clicked()'), self.broadcastTx)

   

      
   

################################################################################
class DlgQRCodeDisplay(ArmoryDialog):
   def __init__(self, parent, main, dataToQR, descrUp='', descrDown=''):
      super(DlgQRCodeDisplay, self).__init__(parent, main)

      btnDone = QPushButton('Close')
      self.connect(btnDone, SIGNAL('clicked()'), self.accept)
      frmBtn = makeHorizFrame(['Stretch', btnDone, 'Stretch'])

      qrDisp = QRCodeWidget(dataToQR, parent=self)
      frmQR = makeHorizFrame(['Stretch', qrDisp, 'Stretch'])

      lblUp = QRichLabel(descrUp)
      lblUp.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
      lblDn = QRichLabel(descrDown)
      lblDn.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)



      layout = QVBoxLayout()
      layout.addWidget(lblUp)
      layout.addWidget(frmQR)
      layout.addWidget(lblDn)
      layout.addWidget(HLINE())
      layout.addWidget(frmBtn)

      self.setLayout(layout)

      w1,h1 = relaxedSizeStr(lblUp, descrUp)
      w2,h2 = relaxedSizeStr(lblDn, descrDown)
      self.setMinimumWidth( 1.2*max(w1,w2) )


