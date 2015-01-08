################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
from PyQt4 import Qt, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from armorycolors import htmlColor
from jasvet import ASv0, ASv1B64, ASv1CS, verifySignature, readSigBlock
from qtdefines import *
from qtdialogs import MIN_PASSWD_WIDTH, DlgPasswd3, createAddrBookButton,\
   DlgUnlockWallet
from armoryengine.ArmoryUtils import isASCII
from announcefetch import ANNOUNCE_SIGN_PUBKEY

class MessageSigningVerificationDialog(ArmoryDialog):

   def __init__(self, parent=None, main=None):
      super(MessageSigningVerificationDialog, self).__init__(parent, main)
      layout = QVBoxLayout()
      self.setWindowTitle("Message Signing/Verification")
      self.setWindowIcon(QIcon( self.main.iconfile))
      self.setMinimumWidth(600)
      
      tabbedPanel = QTabWidget()
      messageSigningTab = MessageSigningWidget(parent, main)
      bareSignatureVerificationTab = BareSignatureVerificationWidget(parent, main)
      signedMsgBlockVerificationTab = SignedMessageBlockVerificationWidget(parent, main)
      tabbedPanel.addTab(messageSigningTab, "Sign Message")
      tabbedPanel.addTab(bareSignatureVerificationTab, "Verify Bare Signature")
      tabbedPanel.addTab(signedMsgBlockVerificationTab, "Verify Signed Message Block")
      layout.addWidget(tabbedPanel)
      
      self.goBackButton = QPushButton("Done")
      actionButtonBox = QDialogButtonBox()
      actionButtonBox.addButton(self.goBackButton, QDialogButtonBox.RejectRole)
      layout.addWidget(actionButtonBox)

      self.setLayout(layout)
      self.connect(self.goBackButton, SIGNAL('clicked()'), \
                   self,           SLOT('reject()'))
      
   def clearFields(self):
      self.addressLineEdit.setText('')
      self.messageTextEdit.setPlainText('')
      self.signatureDisplay.setPlainText('')
      
      


class MessageSigningWidget(QWidget):

   def __init__(self, parent=None, main=None):
      super(MessageSigningWidget, self).__init__(parent)
      self.main = main
      signMessageLayout = QGridLayout()
      self.setMinimumWidth(800)
      
      # Pick an Address in Row 0 of the grid layout
      addressLabel = QLabel('Sign with Address:')
      self.addressLineEdit = QLineEdit()
      self.addressBookButton = createAddrBookButton(self, self.addressLineEdit, None,
                                                    selectMineOnly=True, showLockboxes=False)
      signMessageLayout.addWidget(addressLabel,      0, 0)
      signMessageLayout.addWidget(self.addressLineEdit,  0, 1)
      signMessageLayout.addWidget(self.addressBookButton,  0, 2)

      # Create a message in Row 1
      messageLabel = QLabel("Message to sign:")
      self.messageTextEdit = QTextEdit()
      self.messageTextEdit.setAcceptRichText(False)
      self.messageTextEdit.setStyleSheet("font: 9pt \"Courier\";")
      signMessageLayout.addWidget(messageLabel,          1, 0)
      signMessageLayout.addWidget(self.messageTextEdit,  1, 1, 1, 2)
      
      
      # Create a row with just a sign message button
      
      self.bareSigButton = QPushButton('Bare Signature (Bitcoin-Qt Compatible)')
      self.base64SigButton = QPushButton('Base64 Signature')
      self.clearSigButton = QPushButton('Clearsign Signature')
      sigButtonFrame = makeHorizFrame([self.bareSigButton,\
                                        self.base64SigButton,\
                                        self.clearSigButton,\
                                        'Stretch'])
      signMessageLayout.addWidget(sigButtonFrame,  2, 1, 1, 3)
      
      # Create a Signature display
      signatureLabel = QLabel('Message Signature:')
      self.signatureDisplay = QTextEdit()
      self.signatureDisplay.setReadOnly(True)
      self.signatureDisplay.setStyleSheet("font: 9pt \"Courier\"; background-color: #bbbbbb;")
      signMessageLayout.addWidget(signatureLabel,         3, 0)
      signMessageLayout.addWidget(self.signatureDisplay,  3, 1, 1, 2)

      self.copySignatureButton = QPushButton("Copy Signature")
      self.clearFieldsButton = QPushButton("Clear All")
      
      buttonFrame = makeHorizFrame([self.copySignatureButton, self.clearFieldsButton,'Stretch'])
      signMessageLayout.addWidget(buttonFrame, 4, 1, 1, 3)

      self.setLayout(signMessageLayout)
      self.connect(self.bareSigButton, SIGNAL('clicked()'), \
                   self.bareSignMessage)
      self.connect(self.base64SigButton, SIGNAL('clicked()'), \
                    self.base64SignMessage)
      self.connect(self.clearSigButton, SIGNAL('clicked()'), \
                    self.clearSignMessage)
      self.connect(self.copySignatureButton, SIGNAL('clicked()'), \
                   self.copySignature)
      self.connect(self.clearFieldsButton, SIGNAL('clicked()'), \
                   self.clearFields)
      
   def getPrivateKeyFromAddrInput(self):
      atype, addr160 = addrStr_to_hash160(str(self.addressLineEdit.text()))
      if atype==P2SHBYTE:
         LOGWARN('P2SH address requested')
      walletId = self.main.getWalletForAddr160(addr160)
      wallet = self.main.walletMap[walletId]
      if wallet.useEncryption and wallet.isLocked:
         # Target wallet is encrypted...
         unlockdlg = DlgUnlockWallet(wallet, self, self.main, 'Unlock Wallet to Import')
         if not unlockdlg.exec_():
            QMessageBox.critical(self, 'Wallet is Locked', \
               'Cannot import private keys without unlocking wallet!', \
               QMessageBox.Ok)
            return
      return wallet.addrMap[addr160].binPrivKey32_Plain.toBinStr()

   def bareSignMessage(self):
      messageText = str(self.messageTextEdit.toPlainText())
      if not isASCII(messageText):
         QMessageBox.warning(self, 'Non ASCII Text', 'Message to sign must be ASCII', QMessageBox.Ok)
      else:
         try:
            privateKey = self.getPrivateKeyFromAddrInput()
            if privateKey:
               signature = ASv0(privateKey, messageText)
               self.signatureDisplay.setPlainText(signature['b64-signature'])
            else:
               QMessageBox.warning(self, 'Private Key Not Known', 'The private key is not known for this address.', QMessageBox.Ok)         
         except:
            QMessageBox.warning(self, 'Invalid Address', 'The signing address is invalid.', QMessageBox.Ok)
            raise
   
   def base64SignMessage(self):
      messageText = str(self.messageTextEdit.toPlainText())
      if not isASCII(messageText):
         QMessageBox.warning(self, 'Non ASCII Text', 'Message to sign must be ASCII', QMessageBox.Ok)
      else:
         try:
            privateKey = self.getPrivateKeyFromAddrInput()
            if privateKey:
               signature = ASv1B64(self.getPrivateKeyFromAddrInput(), messageText)
               self.signatureDisplay.setPlainText(signature)    
            else:
               QMessageBox.warning(self, 'Private Key Not Known', 'The private key is not known for this address.', QMessageBox.Ok)
         except:
            QMessageBox.warning(self, 'Invalid Address', 'The signing address is invalid.', QMessageBox.Ok)
            raise
   
   def clearSignMessage(self):
      messageText = str(self.messageTextEdit.toPlainText())
      if not isASCII(messageText):
         QMessageBox.warning(self, 'Non ASCII Text', 'Message to sign must be ASCII', QMessageBox.Ok)
      else:
         try:
            privateKey = self.getPrivateKeyFromAddrInput()
         except:
            QMessageBox.warning(self, 'Invalid Address', 'The signing address is invalid.', QMessageBox.Ok)
            raise
         if privateKey:
            signature = ASv1CS(privateKey, messageText)
            self.signatureDisplay.setPlainText(signature)
         else:
            QMessageBox.warning(self, 'Private Key Not Known', 'The private key is not known for this address.', QMessageBox.Ok)

   def copySignature(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(self.signatureDisplay.toPlainText()))

   def clearFields(self):
      self.addressLineEdit.setText('')
      self.messageTextEdit.setPlainText('')
      self.signatureDisplay.setPlainText('')

# Intended to be a base class
class SignatureVerificationWidget(QWidget):

   def __init__(self, parent=None, main=None):
      super(SignatureVerificationWidget, self).__init__(parent)
      self.main = main
      self.signMessageLayout = QGridLayout()
      self.setMinimumWidth(800)

      self.verifySignatureButton = QPushButton("Verify Signature")
      self.clearFieldsButton = QPushButton("Clear All")
      
      self.lblSigResult = QRichLabel('', doWrap=False)
      buttonFrame = makeHorizFrame([self.verifySignatureButton, self.clearFieldsButton,\
                                    'Stretch', self.lblSigResult])
      self.signMessageLayout.addWidget(buttonFrame, 3, 1, 1, 2)

      self.setLayout(self.signMessageLayout)
      self.connect(self.verifySignatureButton, SIGNAL('clicked()'), \
                   self.verifySignature)
      self.connect(self.clearFieldsButton, SIGNAL('clicked()'), \
                   self.clearFields)

   # To be implemented by child classes
   def verifySignature(self):
      pass
         
   def clearFields(self):
      self.lblSigResult.setText('')
      
   def displayVerifiedBox(self, addrB58, messageString):
      atihash160 = hash160(hex_to_binary(ANNOUNCE_SIGN_PUBKEY))
      addrDisp = addrB58
      if addrB58==hash160_to_addrStr(atihash160):
         addrDisp = '<b>Armory Technologies, Inc.</b>'
         if CLI_OPTIONS.testAnnounceCode:
            ownerStr = tr("""
               <font color="%s"><b>Armory Technologies, Inc.
               (testing key)</b></font> has signed the following
               block of text:<br>""") % htmlColor('TextGreen')
         else:
            ownerStr = tr("""
               <font color="%s"><b>Armory Technologies, Inc.</b></font> 
               has signed the following block of text:<br>""") % \
               htmlColor('TextGreen')
      else:
         ownerStr = tr("""
         The owner of the following Bitcoin address...
         <br>
         <blockquote>
         <font face="Courier" size=4 color="#000060"><b>%s</b></font>
         </blockquote>
         <br>
         ... has produced a <b><u>valid</u></b> signature for 
         the following message:<br>
         """) % addrB58
         
      if addrB58:
         msg = messageString.replace('\r\n','\n')
         msg = '   ' + '<br>   '.join(msg.split('\n'))
         # The user will be able to see the entire message 
         # in the Message Signing/Verification dialog
         msg =  '<br>'.join([line[:60]+ '...'*(len(line)>60) for line in msg.split('<br>')][:12])
         MsgBoxCustom(MSGBOX.Good, tr('Verified!'), tr(""" 
            %s
            <hr>
            <blockquote>
            <font face="Courier" color="#000060"><b>%s</b></font>
            </blockquote>
            <hr><br>
            <b>Please</b> make sure that the address above (%s...) matches the 
            exact address you were expecting.  A valid signature is meaningless 
            unless it is made
            from a recognized address!""") % (ownerStr, msg, addrB58[:10]))
         self.lblSigResult.setText(\
            '<font color="green">Valid Signature by %s</font>' % addrDisp)
      else:
         self.displayInvalidSignatureMessage()

   def displayInvalidSignatureMessage(self):
      MsgBoxCustom(MSGBOX.Error, 'Invalid Signature!', \
                                 'The supplied signature <b>is not valid</b>!')
      self.lblSigResult.setText('<font color="red">Invalid Signature!</font>')
      
class BareSignatureVerificationWidget(SignatureVerificationWidget):

   def __init__(self, parent=None, main=None):
      super(BareSignatureVerificationWidget, self).__init__(parent, main)
      # Pick an Address in Row 0 of the grid layout
      addressLabel = QLabel('Signing Address:')
      self.addressLineEdit = QLineEdit()
      self.addressBookButton = createAddrBookButton(self, self.addressLineEdit, None,
                                                    selectMineOnly=True, showLockboxes=False)
      self.signMessageLayout.addWidget(addressLabel,      0, 0)
      self.signMessageLayout.addWidget(self.addressLineEdit,  0, 1)
      self.signMessageLayout.addWidget(self.addressBookButton,  0, 2)
      
      # Create a message text box
      messageLabel = QLabel("Signed Message:")
      self.messageTextEdit = QTextEdit()
      self.messageTextEdit.setAcceptRichText(False)
      self.messageTextEdit.setStyleSheet("font: 9pt \"Courier\";")
      self.signMessageLayout.addWidget(messageLabel,          1, 0)
      self.signMessageLayout.addWidget(self.messageTextEdit,  1, 1)
      # Create a Signature display
      signatureLabel = QLabel('Signature:')
      self.signatureTextEdit = QTextEdit()
      self.signatureTextEdit.setStyleSheet("font: 9pt \"Courier\";")
      self.signMessageLayout.addWidget(signatureLabel,         2, 0)
      self.signMessageLayout.addWidget(self.signatureTextEdit,  2, 1)
      
   def verifySignature(self):
      messageString = str(self.messageTextEdit.toPlainText())
      try:
         addrB58 = verifySignature(str(self.signatureTextEdit.toPlainText()), \
                         messageString, 'v0', ord(ADDRBYTE))
         if addrB58 == str(self.addressLineEdit.text()):
            self.displayVerifiedBox(addrB58, messageString)
         else:
            self.displayInvalidSignatureMessage()
      except:   
         self.displayInvalidSignatureMessage()
         raise

         
   def clearFields(self):
      super(BareSignatureVerificationWidget, self).clearFields()
      self.addressLineEdit.setText('')
      self.messageTextEdit.setPlainText('')
      self.signatureTextEdit.setPlainText('')

class SignedMessageBlockVerificationWidget(SignatureVerificationWidget):

   def __init__(self, parent=None, main=None):
      super(SignedMessageBlockVerificationWidget, self).__init__(parent, main)
      # Create a Signature display
      signatureLabel = QLabel('Signed Message Block:')
      self.signedMessageBlockTextEdit = QTextEdit()
      self.signedMessageBlockTextEdit.setStyleSheet("font: 9pt \"Courier\";")
      self.signedMessageBlockTextEdit.setAcceptRichText(False)
      self.signMessageLayout.addWidget(signatureLabel,         0, 0)
      self.signMessageLayout.addWidget(self.signedMessageBlockTextEdit,  0, 1)

      # Create a message in Row 1
      messageLabel = QLabel("Message:")
      self.messageTextEdit = QTextEdit()
      self.messageTextEdit.setAcceptRichText(False)
      self.messageTextEdit.setReadOnly(True)
      self.messageTextEdit.setStyleSheet("font: 9pt \"Courier\"; background-color: #bbbbbb;")
      self.signMessageLayout.addWidget(messageLabel,          1, 0)
      self.signMessageLayout.addWidget(self.messageTextEdit,  1, 1, 1, 2)
      
      
   def verifySignature(self):
      try:
         sig, msg = readSigBlock(str(self.signedMessageBlockTextEdit.toPlainText()))
         addrB58 = verifySignature(sig, msg, 'v1', ord(ADDRBYTE) )
         self.displayVerifiedBox(addrB58, msg)
         self.messageTextEdit.setPlainText(msg)
      except:   
         self.displayInvalidSignatureMessage()
         raise
         
   def clearFields(self):
      super(SignedMessageBlockVerificationWidget, self).clearFields()
      self.signedMessageBlockTextEdit.setPlainText('')
      self.messageTextEdit.setPlainText('')



