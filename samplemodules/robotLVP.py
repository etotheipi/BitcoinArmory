# This is a sample plugin file that will be used to create a new tab 
# in the Armory main window.  All plugin files (such as this one) will 
# be injected with the globals() from ArmoryQt.py, which includes pretty
# much all of Bitcoin & Armory related stuff that you need.  So this 
# file can use any utils or objects accessible to functions in ArmoryQt.py.

import ast
import urllib2

from PyQt4.Qt import QPushButton, SIGNAL, Qt, QLineEdit, QTableWidget, \
   QGridLayout, QSpacerItem, QWidget, QScrollArea, QTableWidgetItem, QTextEdit,\
   QVBoxLayout, QMessageBox, QApplication, QLabel, QPixmap

from armorycolors import htmlColor
from armoryengine.ArmoryUtils import RightNow, secondsToHumanTime, coin2str,\
   scrAddr_to_addrStr, script_to_addrStr, addrStr_to_hash160, P2SHBYTE, LOGWARN,\
   isASCII
from armoryengine.BDM import TheBDM, BDM_BLOCKCHAIN_READY
from qtdefines import makeHorizFrame, makeVertFrame, STYLE_PLAIN, QRichLabel, \
   GETFONT
import functools
from jasvet import readSigBlock, verifySignature, ASv1CS
from armoryengine.Transaction import PyTx
from qtdialogs import createAddrBookButton, DlgUnlockWallet, STRETCH


def getReceivedFromAddress(sender, wlt):
   """
   DESCRIPTION:
   Return the number of coins received from a particular sender.
   PARAMETERS:
   sender - Base58 address of the sender to the current wallet.
   RETURN:
   Number of Bitcoins sent by the sender to the current wallet.
   """
   totalReceived = 0.0
   ledgerEntries = wlt.getTxLedger('blk')

   for entry in ledgerEntries:
      cppTx = TheBDM.bdv().getTxByHash(entry.getTxHash())
      if cppTx.isInitialized():
         # Only consider the first for determining received from address
         # This function should assume it is online, and actually request the previous
         # TxOut script from the BDM -- which guarantees we know the sender.
         # Use TheBDM.getSenderScrAddr(txin).  This takes a C++ txin (which we have)
         # and it will grab the TxOut being spent by that TxIn and return the
         # scraddr of it.  This will succeed 100% of the time.
         cppTxin = cppTx.getTxInCopy(0)
         txInAddr = scrAddr_to_addrStr(TheBDM.bdv().getSenderScrAddr(cppTxin))
         fromSender =  sender == txInAddr

         if fromSender:
            txBinary = cppTx.serialize()
            pyTx = PyTx().unserialize(txBinary)
            for txout in pyTx.outputs:
               if wlt.hasAddr(script_to_addrStr(txout.getScript())):
                  totalReceived += txout.value

   return totalReceived

def verifySignature(sigBlock):
   """
   DESCRIPTION:
   Take a message (RFC 2440: clearsign or Base64) signed by a Bitcoin address
   and verify the message.
   PARAMETERS:
   sigBlock - Message with the RFC 2440 message to be verified. The message
              must be enclosed in quotation marks.
   RETURN:
   verified message and the Base58 address of the signer.
   """

   # We must deal with a couple of quirks. First, non-escaped spaces (i.e.,
   # spaces that aren't \u0020) will cause the CL parser to split the sig
   # into multiple lines. We need to combine the lines. Second, the quotation
   # marks used to prevent Armory from treating the sig like a CL arg need
   # to be removed. (NB: The final space must be stripped too.)
   signedMsg = (''.join((str(piece) + ' ') for piece in sigBlock))[1:-2]

   # Get the signature block's signature and message. The signature must be
   # formatted for clearsign or Base64 persuant to RFC 2440.
   sig, msg = readSigBlock(signedMsg)
   addrB58 = verifySignature(sig, msg, 'v1', ord(self.addrByte) )
   return [msg, addrB58]

def processPaidMessage(sigBlock, wlt):
   """
   DESCRIPTION:
   Verify that a message (RFC 2440: clearsign or Base64) has been signed by
   a Bitcoin address and get the amount of coins sent to the current wallet
   by the message's signer.
   PARAMETERS:
   sigBlock - Message with the RFC 2440 message to be verified. The message
              must be enclosed in quotation marks.
   RETURN:
   verified message and the amount of money sent to the
   current wallet by the signer.
   """

   # We must deal with a quirk. Non-escaped spaces (i.e., spaces that aren't
   # \u0020) will cause the CL parser to split the sig into multiple lines.
   # We need to combine the lines. (NB: Strip the final space too!)
   signedMsg = (''.join((str(piece) + ' ') for piece in sigBlock))[:-1]

   message, addrB58 = verifySignature(signedMsg)
   amountReceived = getReceivedFromAddress(addrB58)

   return message, addrB58, amountReceived


def getMessageAndIsPaid(signedMessage, requestorAddress, paymentRequired):
   message, addrB58, amountReceived = processPaidMessage(signedMessage, requestorAddress)
   isPaid = requestorAddress == addrB58 and  amountReceived >= paymentRequired
   return message, isPaid

def receivePayment():
   pass

# Prevents a call to the decorated method unless amount received by wlt
# is at least the paymentRequired
def ProofOfPaymentRequired(wlt=None, paymentRequired=0):
   def ActualProofOfPaymentRequired(func):
      @functools.wraps(func)  # Pull in certain "helper" data from dec'd func
      def inner(signedMessage, requestorAddress, *args, **kwargs):
         if wlt and paymentRequired>0:
            bareMessage, isPaid = getMessageAndIsPaid(wlt, signedMessage, requestorAddress, paymentRequired)
            if isPaid:
               return func(bareMessage, *args, **kwargs) 
            else:
               receivePayment()
         else:
            return func(*args, **kwargs) 
      return inner
   return ActualProofOfPaymentRequired

# ArmoryQt will access this by importing PluginObject and initializing one
#   -- It adds plugin.getTabToDisplay() to the main window tab list
#   -- It uses plugin.tabName as the label for that tab.
#   -- It uses plugin.maxVersion to check for version compatibility
#
# Make sure you test your plugin not only when it's online, but also when
#   -- Armory is in offline mode, and internet is not accessible
#   -- Armory is in offline mode, and internet *is* accessible
#   -- User uses skip-offline-check so online, but service can't be reached
class PluginObject(object):

   tabName = 'Robot Lucy Van Pelt'
   maxVersion = '0.93.99'
   
   #############################################################################
   def __init__(self, main):

      self.main = main

      controlsLayout = QGridLayout()
      self.addressLineEdit = QLineEdit()
      
      headerLabel  = QRichLabel("""<b>Psychiatric Help. 5 Millibits Please!</b>""", doWrap=False)
      addressLabel = QRichLabel('Fee paid from:')
      
      self.addressBookButton = createAddrBookButton(self.main, self.main, self.addressLineEdit,
                                                    selectMineOnly=True, showLockboxes=False)
      questionLabel = QRichLabel("Question:")
      self.questionText = QTextEdit()
      self.questionText.setMaximumHeight(75)
      self.questionText.setAcceptRichText(False)
      self.questionText.setStyleSheet("font: 9pt \"Courier\";")
      
      controlsLayout.addWidget(headerLabel, 0, 0, 1, 3,)
      
      controlsLayout.addWidget(addressLabel, 1, 0)
      controlsLayout.addWidget(self.addressLineEdit, 1, 1)
      controlsLayout.addWidget(self.addressBookButton, 1, 2)

      controlsLayout.addWidget(questionLabel, 2, 0)
      controlsLayout.addWidget(self.questionText, 2, 1, 1, 2)
      
      
      self.askQuestionButton = QPushButton('Ask Question')
      askButtonFrame = makeHorizFrame([self.askQuestionButton, STRETCH])
      controlsLayout.addWidget(askButtonFrame, 3, 1)
      
      # Create a Signature display
      responseLabel = QRichLabel('LVP Robot Response:')
      self.responseDisplay = QTextEdit()
      controlsLayout.addWidget(responseLabel,         4, 0)
      controlsLayout.addWidget(self.responseDisplay,  4, 1, 1, 2)
      self.clearFieldsButton = QPushButton("Clear")
      clearButtonFrame = makeHorizFrame([self.clearFieldsButton, STRETCH])
      controlsLayout.addWidget(clearButtonFrame, 5, 1)
      controlsFrame = QWidget()
      controlsFrame.setLayout(controlsLayout)
      
      @ProofOfPaymentRequired(wlt=self.main.WltMap['2pNNoY1Hx'], paymentRequired=500000)
      def askQuestion():
         self.responseDisplay.setText('Get over it!')
         
      def clearFields():
         self.questionText.setPlainText('')
         self.responseDisplay.setPlainText('')

      self.main.connect(self.askQuestionButton, SIGNAL('clicked()'), askQuestion)
      self.main.connect(self.clearFieldsButton, SIGNAL('clicked()'), clearFields)
      
      lvpPic = QLabel()
      lvpPixmap = QPixmap(':/RobotLVP.png')
      lvpPic.setPixmap(lvpPixmap)

      cartoonFrame = makeVertFrame([lvpPic, STRETCH])
      lvpFrame = makeHorizFrame([cartoonFrame, controlsFrame])
      
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(lvpFrame)
      
      
      
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

      

   #############################################################################
   def getTabToDisplay(self):
      return self.tabToDisplay

      
