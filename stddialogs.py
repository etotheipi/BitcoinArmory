import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qtdefines import *

from armoryengine import *
from armorymodels import *

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
      fm = QFontMetricsF(QFont(self.font()))
      self.edtPasswd.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

      self.btnAccept = QPushButton("Unlcok")
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


      self.chkDisableCrypt = QCheckBox('Disable encryption for this wallet')
      if not noPrevEncrypt:
         self.connect(self.chkDisableCrypt, SIGNAL('clicked()'), \
                      self,                 SLOT('disablePassphraseBoxes(bool)'))
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


#class DlgDispWltProperties(QDialog):
   #def __init__(self, parent=None):
      #super(DlgDispWltProperties, self).__init__(parent)


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
      wlttype, typestr = determineWalletType(wlt, parent)

      self.labels = [wlt.labelName, wlt.labelDescr]
      self.passphrase = ''
      
      w,h = relaxedSize(self,60)
      viewWidth,viewHeight  = w, 10*h
      
      # Wallet Info/Details
      #lblWltDetails = QLabel('Wallet Information:')
      #self.wltDetailsModel = WalletDetailsModel(wlt, parent)
      #self.wltDetailsView = QTableView()
      #self.wltDetailsView.setModel(self.wltDetailsModel)
      #self.wltDetailsView.setShowGrid(False)
      #self.wltDetailsView.setWordWrap(True)
      #self.wltDetailsView.setMinimumSize(viewWidth, viewHeight)
      #self.wltDetailsView.resizeRowsToContents()
      #self.wltDetailsView.verticalHeader().setStretchLastSection(True)
      #self.wltDetailsView.horizontalHeader().resizeSection(0, 0.2*w)
      #self.wltDetailsView.horizontalHeader().setStretchLastSection(True)
      #self.wltDetailsView.horizontalHeader().setVisible(False)
      #self.wltDetailsView.verticalHeader().setVisible(False)
      
      frm = getWltDetailsFrame(wlt, typestr, self.main.usermode)


      # Address view
      lblAddrList = QLabel('Addresses in Wallet:')
      self.wltAddrModel = WalletAddrDispModel(wlt, self)
      self.wltAddrView  = QTableView()
      self.wltAddrView.setModel(self.wltAddrModel)
      self.wltAddrView.setSelectionBehavior(QTableView.SelectRows)
      self.wltAddrView.setSelectionMode(QTableView.SingleSelection)
      self.wltAddrView.horizontalHeader().setStretchLastSection(True)
      self.wltAddrView.verticalHeader().setDefaultSectionSize(20)
      initialColResize(self.wltAddrView, [0.2, 0.7, 64, 0.3])

      #self.wltAddrView.horizontalHeader().resizeSection(1, 150)
      #if self.usermode == USERMODE.Standard:
         #self.walletsView.hideColumn(0)
         #self.walletsView.horizontalHeader().resizeSection(1, 200)

      

      # Now add all the options buttons, dependent on the type of wallet.
      buttonBox = QDialogButtonBox()

      btn1 = QPushButton('Change Labels')
      self.connect(btn1, SIGNAL('clicked()'), self.changeLabels)
      buttonBox.addButton(btn1, QDialogButtonBox.ActionRole)

      btn2 = QPushButton('Change Encryption')
      self.connect(btn2, SIGNAL('clicked()'), self.changeEncryption)
      buttonBox.addButton(btn2, QDialogButtonBox.ActionRole)

      if wlttype==WLTTYPES.Crypt and usermode==USERMODE.Advanced:
         btn3 = QPushButton('Change KDF Params')
         self.connect(btn3, SIGNAL('clicked()'), self.changeKdf)
         buttonBox.addButton(btn3, QDialogButtonBox.ActionRole)


      btn4 = QPushButton('<<< Go Back')
      self.connect(btn4, SIGNAL('clicked()'), self.accept)

      layout = QGridLayout()
      layout.addWidget(frm,                   1, 0, 3, 4)
      #layout.addWidget(lblAddrList,           4, 0, 1, 1)
      layout.addWidget(self.wltAddrView,      5, 0, 2, 4)
      layout.addWidget(btn4,                  7, 0, 1, 1)
      layout.addWidget(buttonBox,             7, 2, 1, 2)
      self.setLayout(layout)
      
      self.setWindowTitle('Wallet Details')

      
   def changeLabels(self):
      dlgLabels = DlgChangeLabels(self.wlt.labelName, self.wlt.labelDescr, self)
      if dlgLabels.exec_():
         self.newLabels = dlgLabels

   def changeEncryption(self):
      dlgCrypt = DlgChangePassphrase(self, not self.wlt.useEncryption)
      if dlgCrypt.exec_():
         self.disableEncryption = dlgCrypt.chkDisableCrypt.isChecked()
         origPassphrase = dlgCrypt.edtPasswdOrig
         newPassphrase = dlgCrypt.edtPasswd1

         if self.wlt.useEncryption:
            if self.wlt.verifyPassphrase(origPassphrase):
               self.wlt.unlock(securePassphrase=origPassphrase)
            else:
               # Even if the wallet is already unlocked, enter pwd again to change it
               QMessageBox.critical(self, 'Invalid Passphrase', \
                     'Previous passphrase is not correct!  Could not unlock wallet.', \
                     QMessageBox.Ok)
         
         
         if self.disableEncryption:
            self.wlt.changeWalletEncryption(None, None)
         else:
            if not self.wlt.useEncryption:
               kdfParams = self.wlt.computeSystemSpecificKdfParams(0.2)
               self.wlt.changeKdfParams(*kdfParams)
            self.wlt.changeWalletEncryption(securePassphrase=newPassphrase)
      

   def changeKdf(self):
      pass



def getWltDetailsFrame(wlt, typestr, usermode=USERMODE.Standard):

   dispCrypto = wlt.useEncryption and (usermode==USERMODE.Advanced or \
                                       usermode==USERMODE.Developer)
   if dispCrypto:
      kdftimestr = "%0.3f seconds" % wlt.testKdfComputeTime()
      mem = wlt.kdf.getMemoryReqtBytes()
      kdfmemstr = str(mem/1024)+' kB'
      if mem >= 1024*1024:
         kdfmemstr = str(mem/(1024*1024))+' MB'


   labelNames = []
   labelNames.append(QLabel('Wallet Name:'))
   labelNames.append(QLabel('Description:'))

   labelNames.append(QLabel('Wallet ID:'))
   labelNames.append(QLabel('#Addresses:'))
   labelNames.append(QLabel('Security:'))


   if dispCrypto:
      labelNames.append(QLabel('Encryption:'))
      labelNames.append(QLabel('Time to Unlock:'))
      labelNames.append(QLabel('Memory to Unlock:'))

   labelValues = []
   labelValues.append(QLabel(wlt.labelName))
   labelValues.append(QLabel(wlt.labelDescr))

   labelValues.append(QLabel(wlt.wltUniqueIDB58))
   labelValues.append(QLabel(str(len(wlt.addrMap)-1)))
   labelValues.append(QLabel(typestr))


   if dispCrypto:
      labelValues.append(QLabel('AES256'))
      labelValues.append(QLabel(kdftimestr))
      labelValues.append(QLabel(kdfmemstr))

   for lbl in labelNames:
      lbl.setTextFormat(Qt.RichText)
      lbl.setText( '<b>' + lbl.text() + '</b>')
      lbl.setContentsMargins(10, 0, 10, 0)


   for lbl in labelValues:
      lbl.setText( '<i>' + lbl.text() + '</i>')
      lbl.setContentsMargins(10, 0, 10, 0)
      lbl.setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                  Qt.TextSelectableByKeyboard)

   labelNames[1].setAlignment(Qt.AlignLeft | Qt.AlignTop)
   labelValues[1].setWordWrap(True)
   labelValues[1].setAlignment(Qt.AlignLeft | Qt.AlignTop)

   layout = QGridLayout()
   layout.addWidget(labelNames[0], 0, 0); layout.addWidget(labelValues[0], 0, 1)
   layout.addWidget(labelNames[1], 1, 0); layout.addWidget(labelValues[1], 1, 1, 2, 1)

   layout.addWidget(labelNames[2], 0, 2); layout.addWidget(labelValues[2], 0, 3)
   layout.addWidget(labelNames[3], 1, 2); layout.addWidget(labelValues[3], 1, 3)
   layout.addWidget(labelNames[4], 2, 2); layout.addWidget(labelValues[4], 2, 3)


   if dispCrypto:
      layout.addWidget(labelNames[5], 0, 4); layout.addWidget(labelValues[5], 0, 5)
      layout.addWidget(labelNames[6], 1, 4); layout.addWidget(labelValues[6], 1, 5)
      layout.addWidget(labelNames[7], 2, 4); layout.addWidget(labelValues[7], 2, 5)
   else:
      empty = QLabel(' '*20)
      layout.addWidget(empty, 0, 4); layout.addWidget(empty, 0, 5)
      layout.addWidget(empty, 1, 4); layout.addWidget(empty, 1, 5)
      layout.addWidget(empty, 2, 4); layout.addWidget(empty, 2, 5)
      

   infoFrame = QFrame()
   infoFrame.setFrameStyle(QFrame.Box|QFrame.Sunken)
   infoFrame.setLayout(layout)
   
   return infoFrame


################################################################################
class DlgSetComment(QDialog):
   """ This will be a dumb dialog for retrieving a comment from user """

   #############################################################################
   def __init__(self, currComment='', ctype='' parent=None):
      super(DlgWalletDetails, self).__init__(parent)

      self.setWindowTitle('Add/Change Comment')
      self.setWindowIcon(QIcon('icons/armory_logo_32x32.png'))

      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonBox, SIGNAL('accepted()'), self.accept)
      self.connect(buttonBox, SIGNAL('rejected()'), self.reject)


if __name__=='__main__':
   app = QApplication(sys.argv)
   app.setApplicationName("DumbDialogs")

   form = DlgNewWallet()
   #form = DlgChangePassphrase(noPrevEncrypt=True)

   form.show()
   app.exec_()





