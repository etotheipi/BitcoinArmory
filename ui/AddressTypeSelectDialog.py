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
from armoryengine.BDM import TheBDM

class AddressTypeSelectDialog(ArmoryDialog):
   
   def __init__(self, parent, main, addrtype):
      super(AddressTypeSelectDialog, self).__init__(parent, main)   
      
      self.type = "P2PKH"
      if addrtype is not None:
         self.type = addrtype
      
      #p2pkh
      self.radioP2PKH = QRadioButton(self.tr("P2PKH Address"))
      p2pkhDescr = QLabel(self.tr('Legacy Armory address type. Backwards compatible.'))
      
      frmP2PKH = QFrame()
      frmP2PKH.setFrameStyle(STYLE_RAISED)
      p2pkhLayout = QGridLayout()
      p2pkhLayout.addWidget(self.radioP2PKH, 0, 0, 1, 1)
      p2pkhLayout.addWidget(p2pkhDescr, 1, 0, 1, 1)
      frmP2PKH.setLayout(p2pkhLayout)
      
      def setP2PKH():
         self.selectType('P2PKH')
      
      self.connect(self.radioP2PKH, SIGNAL('clicked()'), setP2PKH)
      
      #nested p2wpkh
      self.radioSW = QRadioButton(self.tr("P2SH-P2WPKH address"))
      swDescr = QLabel(self.tr('P2WPKH (SegWit script) nested in P2SH script. Any wallet can pay to '
         'this address. Only wallets supporting SegWit can spend from it.'))
      
      frmSW = QFrame()
      frmSW.setFrameStyle(STYLE_RAISED)
      swLayout = QGridLayout()
      swLayout.addWidget(self.radioSW, 0, 0, 1, 1)
      swLayout.addWidget(swDescr, 1, 0, 1, 1)
      frmSW.setLayout(swLayout)

      if TheBDM.isSegWitEnabled() == False:
         frmSW.setDisabled(True)
      
      def setSW():
         self.selectType('P2SH-P2WPKH')
      
      self.connect(self.radioSW, SIGNAL('clicked()'), setSW)
      
      #nested p2pk
      self.radioNP2PK = QRadioButton(self.tr("P2SH-P2PK address"))
      np2pkDescr = QLabel(self.tr('Compressed P2PK script nested in P2SH output. Any wallet can pay to this '
         'address. Only Armory 0.96+ can spend from it.<br><br>'
         
         'This format allow for more efficient transaction space use, resulting in '
         'smaller inputs and lower fees.'))
      
      frmNP2PK = QFrame()
      frmNP2PK.setFrameStyle(STYLE_RAISED)
      np2pkLayout = QGridLayout()
      np2pkLayout.addWidget(self.radioNP2PK, 0, 0, 1, 1)
      np2pkLayout.addWidget(np2pkDescr, 1, 0, 1, 1)   
      frmNP2PK.setLayout(np2pkLayout)
      
      def setNP2PK():
         self.selectType('P2SH-P2PK')
      
      self.connect(self.radioNP2PK, SIGNAL('clicked()'), setNP2PK) 
      
      #main layout
      layout = QGridLayout()
      layout.addWidget(frmP2PKH, 0, 0, 1, 4)
      layout.addWidget(frmNP2PK, 2, 0, 1, 4)
      layout.addWidget(frmSW, 4, 0, 1, 4)
      
      self.btnOk = QPushButton(self.tr('Apply'))
      self.btnCancel = QPushButton(self.tr('Cancel'))
      
      self.connect(self.btnOk, SIGNAL('clicked()'), self.accept)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)

      layout.addWidget(self.btnOk, 5, 2, 1, 1)
      layout.addWidget(self.btnCancel, 5, 3, 1, 1)

      self.setLayout(layout)
      self.setWindowTitle(self.tr('Select Address Type'))
      
      self.selectType(self.type)
      self.setFocus()   
      
   def selectType(self, _type):
      self.type = _type
      
      self.radioP2PKH.setChecked(False)
      self.radioSW.setChecked(False)
      self.radioNP2PK.setChecked(False)
      
      if _type == 'P2PKH':
         self.radioP2PKH.setChecked(True)
      elif _type == 'P2SH-P2WPKH':
         self.radioSW.setChecked(True)
      elif _type == 'P2SH-P2PK':
         self.radioNP2PK.setChecked(True)
         
   def getType(self):
      return self.type

class AddressLabelFrame(object):
   
      def __init__(self, main, setAddressFunc):
         self.main = main
         self.setAddressFunc = setAddressFunc
         
         self.frmAddrType = QFrame()
         self.frmAddrType.setFrameStyle(STYLE_RAISED)
         frmAddrTypeLayout = QGridLayout()
         
         addrLabel = QLabel(self.main.tr('Address Type: '))
         addrLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
         self.typeLabel = QLabelButton("")
         self.typeLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
         self.setType('P2PKH')
         
         self.main.connect(self.typeLabel, SIGNAL('clicked()'), self.changeType)
      
         frmAddrTypeLayout.addWidget(addrLabel, 0, 0, 1, 1)
         frmAddrTypeLayout.addWidget(self.typeLabel, 0, 1, 1, 2)
         self.frmAddrType.setLayout(frmAddrTypeLayout)
         
      def setType(self, _type):
         self.addrType = _type
         self.typeLabel.setText(self.main.tr("<u><font color='blue'>%1</font></u>").arg(_type))
         
      def getType(self):
         return self.addrType
         
      def changeType(self):
         dlg = AddressTypeSelectDialog(self.main, self.main, self.addrType)
         if dlg.exec_():
            self.setType(dlg.getType())
            self.setAddressFunc(dlg.getType())
            
      def getFrame(self):
         return self.frmAddrType
   
