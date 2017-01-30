##############################################################################
#                                                                            #
# Copyright (C) 2016-17, goatpig                                             #
#  Distributed under the MIT license                                         #
#  See LICENSE-MIT or https://opensource.org/licenses/MIT                    #                                   
#                                                                            #
##############################################################################

from PyQt4.QtGui import QFrame, QRadioButton, QLineEdit, QGridLayout, \
   QLabel, QPushButton, QCheckBox
from PyQt4.QtCore import SIGNAL

from qtdefines import ArmoryDialog, STYLE_RAISED, GETFONT, tightSizeNChar, \
   QLabelButton, makeHorizFrame, STYLE_NONE
from armoryengine.ArmoryUtils import str2coin, coin2str
from armoryengine.CoinSelection import estimateFee
from armoryengine.ArmoryUtils import MIN_TX_FEE, MIN_FEE_BYTE, DEFAULT_FEE_TYPE

class FeeSelectionDialog(ArmoryDialog):
   
   #############################################################################
   def __init__(self, parent, main):
      super(FeeSelectionDialog, self).__init__(parent, main)
      
      #Button Label
      self.lblButtonFee = QLabelButton("")
      
      #get default values
      flatFee = self.main.getSettingOrSetDefault("Default_Fee", MIN_TX_FEE)
      flatFee = coin2str(flatFee, maxZeros=1).strip()
      fee_byte = str(self.main.getSettingOrSetDefault("Default_FeeByte", MIN_FEE_BYTE))
      
      self.coinSelection = None
      self.validAutoFee = True
      try:
         autoFee_byte = str(estimateFee() / 1000.0)
      except:
         autoFee_byte = "N/A"
         self.validAutoFee = False
         
      defaultCheckState = \
         self.main.getSettingOrSetDefault("FeeOption", DEFAULT_FEE_TYPE)
      
      #flat free
      def setFlatFee():
         def callbck():
            return self.selectType('FlatFee')
         return callbck
      
      def updateLblOnValueChange():
         self.updateLabelButton(self.lastKnownTxSize)
      
      self.radioFlatFee = QRadioButton("Flat Fee (BTC)")
      self.edtFeeAmt = QLineEdit(flatFee)
      self.edtFeeAmt.setFont(GETFONT('Fixed'))
      self.edtFeeAmt.setMinimumWidth(tightSizeNChar(self.edtFeeAmt, 6)[0])
      self.edtFeeAmt.setMaximumWidth(tightSizeNChar(self.edtFeeAmt, 12)[0])
      
      self.connect(self.radioFlatFee, SIGNAL('clicked()'), setFlatFee())
      self.connect(self.edtFeeAmt, SIGNAL('textChanged(QString)'), updateLblOnValueChange)
      
      frmFlatFee = QFrame()
      frmFlatFee.setFrameStyle(STYLE_RAISED)
      layoutFlatFee = QGridLayout()
      layoutFlatFee.addWidget(self.radioFlatFee, 0, 0, 1, 1)
      layoutFlatFee.addWidget(self.edtFeeAmt, 0, 1, 1, 1)
      frmFlatFee.setLayout(layoutFlatFee)
      
      #fee/byte
      def setFeeByte():
         def callbck():
            return self.selectType('FeeByte')
         return callbck
      
      self.radioFeeByte = QRadioButton("Fee/Byte (Satoshi/Byte)")
      self.edtFeeByte = QLineEdit(fee_byte)
      self.edtFeeByte.setFont(GETFONT('Fixed'))
      self.edtFeeByte.setMinimumWidth(tightSizeNChar(self.edtFeeByte, 6)[0])
      self.edtFeeByte.setMaximumWidth(tightSizeNChar(self.edtFeeByte, 12)[0])
      
      self.connect(self.radioFeeByte, SIGNAL('clicked()'), setFeeByte())
      self.connect(self.edtFeeByte, SIGNAL('textChanged(QString)'), updateLblOnValueChange)
            
      frmFeeByte = QFrame()
      frmFeeByte.setFrameStyle(STYLE_RAISED)
      layoutFeeByte = QGridLayout()
      layoutFeeByte.addWidget(self.radioFeeByte, 0, 0, 1, 1)
      layoutFeeByte.addWidget(self.edtFeeByte, 0, 1, 1, 1)
      frmFeeByte.setLayout(layoutFeeByte)
      
      #auto fee/byte
      def setAutoFeeByte():
         def callbck():
            return self.selectType('Auto')
         return callbck      
      
      self.radioAutoFeeByte = QRadioButton("Auto Fee/Byte (Satoshi/Byte)")
      self.lblAutoFeeByte = QLabel(autoFee_byte)
      self.lblAutoFeeByte.setFont(GETFONT('Fixed'))
      self.lblAutoFeeByte.setMinimumWidth(tightSizeNChar(self.lblAutoFeeByte, 6)[0])
      self.lblAutoFeeByte.setMaximumWidth(tightSizeNChar(self.lblAutoFeeByte, 12)[0])
      self.connect(self.radioAutoFeeByte, SIGNAL('clicked()'), setAutoFeeByte())
      
      if self.validAutoFee:
         self.lblAutoFeeDescr = QLabel("Fetch fee/byte from your network node")
      else:
         self.lblAutoFeeDescr = QLabel("Failed to fetch fee/byte from node")
      
      frmAutoFeeByte = QFrame()
      frmAutoFeeByte.setFrameStyle(STYLE_RAISED)
      layoutAutoFeeByte = QGridLayout()
      layoutAutoFeeByte.addWidget(self.radioAutoFeeByte, 0, 0, 1, 1)
      layoutAutoFeeByte.addWidget(self.lblAutoFeeByte, 0, 1, 1, 1)  
      layoutAutoFeeByte.addWidget(self.lblAutoFeeDescr, 1, 0, 1, 2)
      frmAutoFeeByte.setLayout(layoutAutoFeeByte)
      
      if not self.validAutoFee:
         frmAutoFeeByte.setEnabled(False)
      
      #adjust and close
      self.btnClose = QPushButton('Close')
      self.connect(self.btnClose, SIGNAL('clicked()'), self.accept)
      
      self.checkBoxAdjust = QCheckBox('Adjust fee/byte for privacy')
      self.checkBoxAdjust.setChecked(\
         self.main.getSettingOrSetDefault('AdjustFee', True))
      
      def updateLbl():
         self.updateCoinSelection()
         self.updateLabelButton(self.coinSelection)
      
      self.connect(self.checkBoxAdjust, SIGNAL('clicked()'), updateLbl)
      
      frmClose = makeHorizFrame(\
         [self.checkBoxAdjust, 'Stretch', self.btnClose], STYLE_NONE)
      
      #main layout
      layout = QGridLayout()
      layout.addWidget(frmAutoFeeByte, 0, 0, 1, 4)
      layout.addWidget(frmFeeByte, 2, 0, 1, 4)
      layout.addWidget(frmFlatFee, 4, 0, 1, 4)
      layout.addWidget(frmClose, 5, 0, 1, 4)
      
      self.setLayout(layout)      
      self.setWindowTitle('Select Fee Type')
      
      self.selectType(defaultCheckState)

      self.setFocus()  
   
   #############################################################################   
   def selectType(self, strType):
      self.radioFlatFee.setChecked(False)
      self.radioFeeByte.setChecked(False)
      self.radioAutoFeeByte.setChecked(False)
      
      if strType == 'FlatFee':
         self.radioFlatFee.setChecked(True)
      elif strType == 'FeeByte':
         self.radioFeeByte.setChecked(True)
      elif strType == 'Auto':
         if not self.validAutoFee:
            self.radioFeeByte.setChecked(True)
         else:
            self.radioAutoFeeByte.setChecked(True)
            
      self.updateCoinSelection()
      self.updateLabelButton(self.coinSelection)
      
   #############################################################################
   def updateCoinSelection(self):
      try:
         flatFee, feeByte, adjust = self.getFeeData()
         self.coinSelection.updateState(flatFee, feeByte, adjust)
      except:
         pass
   
   #############################################################################   
   def getLabelButton(self):
      return self.lblButtonFee
   
   #############################################################################
   def updateLabelButtonText(self, txSize, flatFee, fee_byte):
      txSize = str(txSize)
      if txSize != 'N/A':
         txSize += " B"
      
      if flatFee != 'N/A':
         flatFee = coin2str(flatFee, maxZeros=0).strip()
         flatFee += " BTC"   
      
      if not isinstance(fee_byte, str):   
         fee_byte = '%.2f' % fee_byte 
      
      lblStr = "Size: %s, Fee: %s" % (txSize, flatFee)
      if fee_byte != 'N/A':
         lblStr += " (%s sat/B)" % fee_byte
      
      self.lblButtonFee.setText(lblStr)
   
   #############################################################################   
   def updateLabelButton(self, coinSelection):
      self.coinSelection = coinSelection
      
      try:
         txSize = self.coinSelection.getSizeEstimate()
         flatFee = self.coinSelection.getFlatFee()
         feeByte = self.coinSelection.getFeeByte()
      
         self.updateLabelButtonText(txSize, flatFee, feeByte)

      except:
         self.updateLabelButtonText('N/A', 'N/A', 'N/A')
         
   #############################################################################
   def resetLabel(self):
      self.updateLabelButton(None)
   
   #############################################################################
   def getFeeData(self):
      fee = 0
      fee_byte = 0
      
      if self.radioFlatFee.isChecked():
         flatFeeText = str(self.edtFeeAmt.text())
         fee = str2coin(flatFeeText)
      
      elif self.radioFeeByte.isChecked():
         fee_byteText = str(self.edtFeeByte.text())
         fee_byte = float(fee_byteText)
                 
      elif self.radioAutoFeeByte.isChecked():
         fee_byteText = str(self.lblAutoFeeByte.text())
         fee_byte = float(fee_byteText)
         
      adjust_fee = self.checkBoxAdjust.isChecked()
         
      return fee, fee_byte, adjust_fee    