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
   def __init__(self, parent=None):
      super(DlgUnlockWallet, self).__init__(parent)

      lblDescr  = QLabel("Enter your passphrase to unlock this wallet")
      lblPasswd = QLabel("Passphrase:")
      self.edtPasswd = QLineEdit()
      self.edtPasswd.setEchoMode(QLineEdit.Password)
      self.edtPasswd.setMinimumWidth(MIN_PASSWD_WIDTH(self))
      fm = QFontMetricsF(QFont(self.font()))
      self.edtPasswd.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

      self.btnAccept = QPushButton("Unlock")
      self.btnCancel = QPushButton("Cancel")
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.accept)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)

      layout = QGridLayout()
      layout.addWidget(lblDescr,       1, 0, 1, 2)
      layout.addWidget(lblPasswd,      2, 0, 1, 1)
      layout.addWidget(self.edPasswd,  2, 1, 1, 1)
      layout.addWidget(buttonBox,      3, 1, 1, 2)

      self.setLayout(layout)
      #btngrp = self.QButtonGroup()
      #self.QRadioButton()
      #lbl
   

################################################################################
class DlgNewWallet(QDialog):

   def __init__(self, parent=None):
      super(DlgNewWallet, self).__init__(parent)

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
      masterLayout.addWidget(lblDescr,          3, 0, 1, 2)
      masterLayout.addWidget(self.edtDescr,     3, 1, 2, 2)
      masterLayout.addWidget(self.chkUseCrypto, 5, 0, 1, 1)
      masterLayout.addWidget(usecryptoTooltip,  5, 1, 1, 1)
      masterLayout.addWidget(self.cryptoFrame,  7, 0, 3, 3)
   
      masterLayout.addWidget(self.btnbox,      10, 0, 1, 2)

      masterLayout.setVerticalSpacing(15)
     
      self.setLayout(masterLayout)

      self.layout().setSizeConstraint(QLayout.SetFixedSize)

      self.connect(self.chkUseCrypto, SIGNAL("clicked()"), \
                   self.cryptoFrame,  SLOT("setEnabled(bool)"))

      self.setWindowTitle('Create/Import Armory wallet')
      self.setWindowIcon(QIcon('icons/armory_logo_32x32.png'))



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
      lblWarnImg.setPixmap(QPixmap('icons/Warning64x64'))
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
      lbtnExport  = QLabelButton('Export wallet backup')
      lbtnRemove  = QLabelButton('Delete/Remove wallet')


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

      layout = QGridLayout()
      layout.addWidget(self.frm,              0, 0, 3, 4)
      layout.addWidget(self.wltAddrView,      4, 0, 2, 4)
      layout.addWidget(btnGoBack,             6, 0, 1, 1)
      #layout.addWidget(buttonBox,             7, 2, 1, 2)
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
            self.labelValues[WLTFIELDS.Crypto].setText('No Encryption')
         else:
            if not self.wlt.useEncryption:
               kdfParams = self.wlt.computeSystemSpecificKdfParams(0.2)
               self.wlt.changeKdfParams(*kdfParams)
            self.wlt.changeWalletEncryption(securePassphrase=newPassphrase)
            #self.accept()
      

   def getNewAddress(self):
      pass 

   def changeKdf(self):
      """ 
      This is a low-priority feature.  I mean, the PyBtcWallet class has this
      feature implemented, but I don't have a GUI for it
      """
      pass

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
      self.wltID = self.wlt.wltUniqueIDB58

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
   
      self.labelValues[WLTFIELDS.WltID]     = QLabel(self.wlt.wltUniqueIDB58)
      self.labelValues[WLTFIELDS.NumAddr]   = QLabel(str(len(self.wlt.addrMap)-1))
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
         else:
            owner = str(dlg.edtOwnerString.text())  
            self.main.setWltExtraProp(self.wltID, 'IsMine', False)
            self.main.setWltExtraProp(self.wltID, 'BelongsTo', owner)
               
            if len(owner)>0:
               self.labelValues[WLTFIELDS.BelongsTo].setText(owner)
            else:
               self.labelValues[WLTFIELDS.BelongsTo].setText('Someone else')
         


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

      self.connect( self.btnImportFile, SIGNAL("clicked()"), \
                    self.execImportPaperDlg)

      ttip1 = createToolTipObject('Import an existing Armory wallet, usually with a '
                                 '.wallet extension.  Any wallet that you import will ' 
                                 'be copied into your settings directory, and maintained '
                                 'from there.  The original wallet file will not be touched.')

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

      
   def execImportPaperDlg(self):
      self.importType_file = False
      self.importType_paper = True
      



#############################################################################
class DlgImportPaperWallet(QDialog):
   def __init__(self, parent=None):
      super(DlgImportPaperWallet, self).__init__(parent)
      




################################################################################
class DlgSetComment(QDialog):
   """ This will be a dumb dialog for retrieving a comment from user """

   #############################################################################
   def __init__(self, currcomment='', ctype='', parent=None):
      super(DlgSetComment, self).__init__(parent)

      self.setWindowTitle('add/change comment')
      self.setWindowIcon(QIcon('icons/armory_logo_32x32.png'))

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


if __name__=='__main__':
   app = QApplication(sys.argv)
   app.setApplicationName("dumbdialogs")

   form = dlgNewWallet()
   #form = dlgchangepassphrase(noprevencrypt=true)

   form.show()
   app.exec_()





