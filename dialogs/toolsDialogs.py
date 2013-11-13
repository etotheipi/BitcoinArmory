################################################################################
#                                                                              #
# Copyright (C) 2011-2013, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
from PyQt4 import Qt, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from armorycolors import htmlColor
from jasvet import ASv0, ASv1B64, ASv1CS, verifySignature
from qtdefines import *
from qtdialogs import MIN_PASSWD_WIDTH, DlgPasswd3, createAddrBookButton
from utilities.ArmoryUtils import isASCII


class MessageSigningVerificationDialog(ArmoryDialog):

   def __init__(self, parent=None, main=None):
      super(MessageSigningVerificationDialog, self).__init__(parent, main)
      layout = QVBoxLayout()
      self.setWindowTitle("Message Signing/Verification")
      self.setWindowIcon(QIcon( self.main.iconfile))
      self.setMinimumWidth(800)
      
      tabbedPanel = QTabWidget()
      messageSigningTab = MessageSigningWidget(parent, main)
      bareSignatureVerificationTab = BareSignatureVerificationWidget(parent, main)
      base64SignatureVerificationTab = Base64SignatureVerificationWidget(parent, main)
      clearsignSignatureVerificationTab = ClearsignSignatureVerificationWidget(parent, main)
      tabbedPanel.addTab(messageSigningTab, "Sign Message")
      tabbedPanel.addTab(bareSignatureVerificationTab, "Verify Bare Signature")
      tabbedPanel.addTab(base64SignatureVerificationTab, "Verify Base64 Signature")
      tabbedPanel.addTab(clearsignSignatureVerificationTab, "Verify Clearsign Signature")
      layout.addWidget(tabbedPanel)
      
      self.goBackButton = QPushButton("<<< Go Back")
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
                                                    selectMineOnly=True)
      signMessageLayout.addWidget(addressLabel,      0, 0)
      signMessageLayout.addWidget(self.addressLineEdit,  0, 1)
      signMessageLayout.addWidget(self.addressBookButton,  0, 2)

      # Create a message in Row 1
      messageLabel = QLabel("Message to sign:")
      self.messageTextEdit = QTextEdit()
      self.messageTextEdit.setAcceptRichText(False)
      signMessageLayout.addWidget(messageLabel,          1, 0)
      signMessageLayout.addWidget(self.messageTextEdit,  1, 1, 1, 2)
      
      
      # Create a row with just a sign message button
      
      self.bareSigButton = QPushButton('Bitcoin-Qt compatible Bare Signature')
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
      addr160 = addrStr_to_hash160(str(self.addressLineEdit.text()))
      walletId = self.main.getWalletForAddr160(addr160)
      wallet = self.main.walletMap[walletId]
      return wallet.addrMap[addr160].serializePlainPrivateKey()

   def bareSignMessage(self):
      signature = ASv0(self.getPrivateKeyFromAddrInput(), str(self.messageTextEdit.toPlainText()))
      self.signatureDisplay.setPlainText(signature['b64-signature'])
   
   def base64SignMessage(self):
      signature = ASv1B64(self.getPrivateKeyFromAddrInput(), str(self.messageTextEdit.toPlainText()))
      self.signatureDisplay.setPlainText(signature)
   
   def clearSignMessage(self):
      signature = ASv1CS(self.getPrivateKeyFromAddrInput(), str(self.messageTextEdit.toPlainText()))
      self.signatureDisplay.setPlainText(signature)

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
      
      # Pick an Address in Row 0 of the grid layout
      addressLabel = QLabel('Signing Address:')
      self.addressLineEdit = QLineEdit()
      self.addressBookButton = createAddrBookButton(self, self.addressLineEdit, None,
                                                    selectMineOnly=True)
      self.signMessageLayout.addWidget(addressLabel,      0, 0)
      self.signMessageLayout.addWidget(self.addressLineEdit,  0, 1)
      self.signMessageLayout.addWidget(self.addressBookButton,  0, 2)

      # Create a Signature display
      signatureLabel = QLabel('Message Signature:')
      self.signatureDisplay = QTextEdit()
      self.signMessageLayout.addWidget(signatureLabel,         1, 0)
      self.signMessageLayout.addWidget(self.signatureDisplay,  1, 1, 1, 2)

      self.verifySignatureButton = QPushButton("Verify Signature")
      self.clearFieldsButton = QPushButton("Clear All")
      
      self.lblSigResult = QRichLabel('')
      buttonFrame = makeHorizFrame([self.verifySignatureButton, self.clearFieldsButton,\
                                    'Stretch', self.lblSigResult])
      self.signMessageLayout.addWidget(buttonFrame, 3, 1, 1, 3)

      self.setLayout(self.signMessageLayout)
      self.connect(self.verifySignatureButton, SIGNAL('clicked()'), \
                   self.verifySignature)
      self.connect(self.clearFieldsButton, SIGNAL('clicked()'), \
                   self.clearFields)

   # To be implemented by child classes
   def verifySignature(self):
      pass
         
   def clearFields(self):
      self.addressLineEdit.setText('')
      self.signatureDisplay.setPlainText('')
      
   def displayVerifiedBox(self, isVerified, addrB58, messageString):
      if isVerified:
         MsgBoxCustom(MSGBOX.Good, 'Verified!', \
            'The owner of the following Bitcoin address...'
            '<br><br>'
            '<b>%s</b>'
            '<br><br>'
            '...has digitally signed the following message:'
            '<br><br>'
            '<i><b>"%s"</b></i>'
            '<br><br>'
            'The supplied signature <b>is valid</b>!' % (addrB58, messageString))
         self.lblSigResult.setText('<font color="green">Valid Signature!</font>')
      else:
         MsgBoxCustom(MSGBOX.Error, 'Invalid Signature!', \
                                    'The supplied signature <b>is not valid</b>!')
         self.lblSigResult.setText('<font color="red">Invalid Signature!</font>')

class BareSignatureVerificationWidget(SignatureVerificationWidget):

   def __init__(self, parent=None, main=None):
      super(BareSignatureVerificationWidget, self).__init__(parent)

      # Create a message text box
      messageLabel = QLabel("Signed Message:")
      self.messageTextEdit = QTextEdit()
      self.messageTextEdit.setAcceptRichText(False)
      self.signMessageLayout.addWidget(messageLabel,          2, 0)
      self.signMessageLayout.addWidget(self.messageTextEdit,  2, 1, 1, 2)
      

   def verifySignature(self):
      addrB58 = str(self.addressLineEdit.text())
      messageString = str(self.messageTextEdit.toPlainText())
      isVerified = verifySignature(addrB58, \
                      str(self.signatureDisplay.toPlainText()), \
                      messageString)
      self.displayVerifiedBox(isVerified, addrB58, messageString)
         
   def clearFields(self):
      super(BareSignatureVerificationWidget, self).clearFields()
      self.messageTextEdit.setPlainText('')

class Base64SignatureVerificationWidget(SignatureVerificationWidget):

   def __init__(self, parent=None, main=None):
      super(Base64SignatureVerificationWidget, self).__init__(parent)


   def verifySignature(self):
      addrB58 = str(self.addressLineEdit.text())
      strMsg = str(self.messageTextEdit.toPlainText())
      isVerified = verifySignature(addrB58, \
                      str(self.signatureDisplay.toPlainText()), \
                      strMsg)
      self.displayVerifiedBox(isVerified)


class ClearsignSignatureVerificationWidget(SignatureVerificationWidget):

   def __init__(self, parent=None, main=None):
      super(ClearsignSignatureVerificationWidget, self).__init__(parent)


   def verifySignature(self):
      addrB58 = str(self.addressLineEdit.text())
      strMsg = str(self.messageTextEdit.toPlainText())
      isVerified = verifySignature(addrB58, \
                      str(self.signatureDisplay.toPlainText()), \
                      strMsg)
      self.displayVerifiedBox(isVerified)