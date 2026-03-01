##############################################################################
#                                                                            #
# Copyright (C) 2016-17, goatpig                                             #
#  Distributed under the MIT license                                         #
#  See LICENSE-MIT or https://opensource.org/licenses/MIT                    #                                   
#                                                                            #
##############################################################################

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qtdefines import ArmoryDialog, STYLE_RAISED, QLabelButton
from armoryengine.SignerWrapper import SIGNER_DEFAULT, SIGNER_LEGACY, \
   SIGNER_CPP, SIGNER_BCH
from armoryengine.Transaction import UnsignedTransaction, PyTx
from armoryengine.ArmoryUtils import CPP_TXOUT_SEGWIT

class SignerSelectDialog(ArmoryDialog):
   
   def __init__(self, parent, main, ustx, lockType):
      super(SignerSelectDialog, self).__init__(parent, main)   
      
      self.type = SIGNER_DEFAULT
      
      #figure out which signers are eligible for this tx
      canUseLegacySigner = True
      canUseBchSigner = True
      
      hasSegWitRecipients = False        
      if ustx != None:
         if not ustx.isLegacyTx:
            canUseLegacySigner = False
            
         if ustx.isSegWit():
            canUseBchSigner = False
         
         #check the recipients for segwit scripts

         
         for dtxo in ustx.decorTxOuts:
            wltID = main.getWalletForScrAddr(dtxo.scrAddr)
            if wltID != '':
               wlt = main.walletMap[wltID]
               try:
                  addrIndex = wlt.cppWallet.getAssetIndexForAddr(dtxo.scrAddr)
                  addrType = wlt.cppWallet.getAddrTypeForIndex(addrIndex)
                  if addrType in CPP_TXOUT_SEGWIT:
                     hasSegWitRecipients = True
                     break
               except:
                  continue
            else:
               lbox = main.getLockboxByP2SHAddrStr(dtxo.scrAddr)
               if lbox != None and lbox.isAddrSegWit(dtxo.scrAddr):
                  hasSegWitRecipients = True
                  break
                        
      if hasSegWitRecipients:
         canUseBchSigner = False
      
      #default signer
      self.radioDefault = QRadioButton(self.tr("Default"))
      defaultDescr = QLabel(self.tr('Let Armory pick the signer for you'))
      
      frmDefault = QFrame()
      frmDefault.setFrameStyle(STYLE_RAISED)
      defaultLayout = QGridLayout()
      defaultLayout.addWidget(self.radioDefault, 0, 0, 1, 1)
      defaultLayout.addWidget(defaultDescr, 1, 0, 1, 1)
      frmDefault.setLayout(defaultLayout)
      
      def setDefault():
         self.selectType(SIGNER_DEFAULT)
      
      self.connect(self.radioDefault, SIGNAL('clicked()'), setDefault)
      
      #legacy signer
      if canUseLegacySigner:
         self.radioLegacy = QRadioButton(self.tr('Legacy Signer'))
      else:
         self.radioLegacy = QRadioButton(self.tr('Legacy Signer (Disabled: signing non legacy outputs)'))
         self.radioLegacy.setDisabled(True)
         
      legacyDescr = QLabel(self.tr('Pre 0.96 Python signer. Can only sign P2PKH scripts. <br>True '
         'and tested old signer code, untouched since 2011. <br>This is the default signer for ' 
         'legacy scripts.'))
      
      frmLegacy = QFrame()
      frmLegacy.setFrameStyle(STYLE_RAISED)
      legacyLayout = QGridLayout()
      legacyLayout.addWidget(self.radioLegacy, 0, 0, 1, 1)
      legacyLayout.addWidget(legacyDescr, 1, 0, 1, 1)
      frmLegacy.setLayout(legacyLayout)
           
      def setLegacy():
         self.selectType(SIGNER_LEGACY)
      
      self.connect(self.radioLegacy, SIGNAL('clicked()'), setLegacy)
      
      #cpp signer
      self.radioCpp = QRadioButton(self.tr("C++ Signer"))
      cppDescr = QLabel(self.tr('New signer introduced in 0.96. Implemented in C++, SegWit compatible. '
         '<br>You have to use this signer for P2SH and SegWit scripts. <br>You do not need to use it for '
         'legacy scripts (P2PKH).'))
      
      frmCpp = QFrame()
      frmCpp.setFrameStyle(STYLE_RAISED)
      cppLayout = QGridLayout()
      cppLayout.addWidget(self.radioCpp, 0, 0, 1, 1)
      cppLayout.addWidget(cppDescr, 1, 0, 1, 1)   
      frmCpp.setLayout(cppLayout)
      
      def setCpp():
         self.selectType(SIGNER_CPP)
      
      self.connect(self.radioCpp, SIGNAL('clicked()'), setCpp) 
      
      #bch signer
      if canUseBchSigner:
         self.radioBch = QRadioButton(self.tr("BCH Signer"))
      else:
         self.radioBch = QRadioButton(self.tr("BCH Signer (Disabled: spending or funding SegWit script(s)"))
         self.radioBch.setDisabled(True)
         
      bchDescr = QLabel(self.tr('Bcash signer, derived from the Cpp signer. <br>You have to use this '
         'signer to spend coins on the Bcash fork. <br>Transactions signed with signer are invalid on '
         'the Bitcoin chain and vice versa. <br><br><b>Bcash does not support SegWit!</b>'
         '<br><u>!!!Do not spend to SegWit addresses on the Bcash chain!!!</u>'))
      
      frmBch = QFrame()
      frmBch.setFrameStyle(STYLE_RAISED)
      bchLayout = QGridLayout()
      bchLayout.addWidget(self.radioBch, 0, 0, 1, 1)
      bchLayout.addWidget(bchDescr, 1, 0, 1, 1)   
      frmBch.setLayout(bchLayout)
      
      def setBch():
         self.selectType(SIGNER_BCH)
      
      self.connect(self.radioBch, SIGNAL('clicked()'), setBch) 
      
      #main layout
      layout = QGridLayout()
      layout.addWidget(frmDefault, 0, 0, 1, 4)
      layout.addWidget(frmLegacy, 2, 0, 1, 4)
      layout.addWidget(frmCpp, 4, 0, 1, 4)
      layout.addWidget(frmBch, 6, 0, 1, 4)
            
      self.btnOk = QPushButton(self.tr('Apply'))
      self.btnCancel = QPushButton(self.tr('Cancel'))
      
      self.connect(self.btnOk, SIGNAL('clicked()'), self.accept)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)

      layout.addWidget(self.btnOk, 7, 2, 1, 1)
      layout.addWidget(self.btnCancel, 7, 3, 1, 1)

      self.setLayout(layout)
      self.setWindowTitle(self.tr('Select Address Type'))
      
      if lockType != SIGNER_DEFAULT:
         self.type = lockType
         self.forceType(self.type)
      else:
         self.selectType(self.type)
      self.setFocus()   
      
   def selectType(self, _type):
      self.type = _type
      
      self.radioDefault.setChecked(False)
      self.radioLegacy.setChecked(False)
      self.radioCpp.setChecked(False)
      self.radioBch.setChecked(False)
      
      if _type == SIGNER_DEFAULT:
         self.radioDefault.setChecked(True)
      elif _type == SIGNER_LEGACY:
         self.radioLegacy.setChecked(True)
      elif _type == SIGNER_CPP:
         self.radioCpp.setChecked(True)
      elif _type == SIGNER_BCH:
         self.radioBch.setChecked(True)
         
   def forceType(self, _type):
      self.radioDefault.setEnabled(False)
      self.radioLegacy.setEnabled(False)
      self.radioCpp.setEnabled(False)
      self.radioBch.setEnabled(False)
      
      self.selectType(_type)
         
   def getType(self):
      return self.type

class SignerLabelFrame(object):
   def __init__(self, main, pytxOrUstx, setSignerFunc):
      self.main = main
      self.setSignerFunc = setSignerFunc

      self.ustx = pytxOrUstx
      if pytxOrUstx != None and isinstance(pytxOrUstx, PyTx):
         self.ustx = UnsignedTransaction()
         self.ustx.createFromPyTx(pytxOrUstx)
         
      self.frmSigner = QFrame()
      self.frmSigner.setFrameStyle(STYLE_RAISED)
      frmSignerLayout = QGridLayout()
         
      signerLabel = QLabel(self.main.tr('Signer: '))
      signerLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.typeLabel = QLabelButton("")
      self.typeLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
      
      self.originalType = SIGNER_DEFAULT
      if self.ustx != None:
         self.originalType = self.ustx.signerType

      self.setType(self.originalType)
      setSignerFunc(self.originalType)
         
      self.main.connect(self.typeLabel, SIGNAL('clicked()'), self.changeType)
      
      frmSignerLayout.addWidget(signerLabel, 0, 0, 1, 1)
      frmSignerLayout.addWidget(self.typeLabel, 0, 1, 1, 2)
      self.frmSigner.setLayout(frmSignerLayout)
         
   def setType(self, _type):
      self.type = _type
      self.typeLabel.setText(self.main.tr("<u><font color='blue'>%1</font></u>").arg(_type))
         
   def getType(self):
      return self.type
         
   def changeType(self):
      dlg = SignerSelectDialog(self.main, self.main, self.ustx, self.originalType)
      if dlg.exec_():
         self.setType(dlg.getType())
         self.setSignerFunc(dlg.getType())
            
   def getFrame(self):
      return self.frmSigner
   
