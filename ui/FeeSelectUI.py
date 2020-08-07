##############################################################################
#                                                                            #
# Copyright (C) 2016-17, goatpig                                             #
#  Distributed under the MIT license                                         #
#  See LICENSE-MIT or https://opensource.org/licenses/MIT                    #                                   
#                                                                            #
##############################################################################

from PyQt4.QtGui import QFrame, QRadioButton, QLineEdit, QGridLayout, \
   QLabel, QPushButton, QCheckBox, QSlider, QComboBox
from PyQt4.QtCore import Qt, SIGNAL

from qtdefines import ArmoryDialog, STYLE_RAISED, GETFONT, tightSizeNChar, \
   QLabelButton, makeHorizFrame, STYLE_NONE
from armoryengine.ArmoryUtils import str2coin, coin2str
from armoryengine.CoinSelection import estimateFee, NBLOCKS_TO_CONFIRM, \
   FEEBYTE_CONSERVATIVE, FEEBYTE_ECONOMICAL
from armoryengine.ArmoryUtils import MIN_TX_FEE, MIN_FEE_BYTE, DEFAULT_FEE_TYPE

class FeeSelectionDialog(ArmoryDialog):
   
   #############################################################################
   def __init__(self, parent, main, cs_callback, get_csstate):
      super(FeeSelectionDialog, self).__init__(parent, main)
      
      #Button Label
      self.lblButtonFee = QLabelButton("")
      
      #get default values
      flatFee = self.main.getSettingOrSetDefault("Default_Fee", MIN_TX_FEE)
      flatFee = coin2str(flatFee, maxZeros=1).strip()
      fee_byte = str(self.main.getSettingOrSetDefault("Default_FeeByte", MIN_FEE_BYTE))
      blocksToConfirm = self.main.getSettingOrSetDefault(\
         "Default_FeeByte_BlocksToConfirm", NBLOCKS_TO_CONFIRM)
      feeStrategy = str(self.main.getSettingOrSetDefault(\
         "Default_FeeByte_Strategy", FEEBYTE_CONSERVATIVE))
      
      self.coinSelectionCallback = cs_callback
      self.getCoinSelectionState = get_csstate
      self.validAutoFee = True

      isSmartFee = True
      try:
         feeEstimate, isSmartFee, errorMsg = self.getFeeByteFromNode(blocksToConfirm, feeStrategy)
      except:
         feeEstimate = "N/A"
         self.validAutoFee = False
         
      defaultCheckState = \
         self.main.getSettingOrSetDefault("FeeOption", DEFAULT_FEE_TYPE)
      
      #flat free
      def setFlatFee():
         def callbck():
            return self.selectType('FlatFee')
         return callbck
      
      def updateLbl():
         self.updateCoinSelection()
      
      self.radioFlatFee = QRadioButton(self.tr("Flat Fee (BTC)"))
      self.edtFeeAmt = QLineEdit(flatFee)
      self.edtFeeAmt.setFont(GETFONT('Fixed'))
      self.edtFeeAmt.setMinimumWidth(tightSizeNChar(self.edtFeeAmt, 6)[0])
      self.edtFeeAmt.setMaximumWidth(tightSizeNChar(self.edtFeeAmt, 12)[0])
      
      self.connect(self.radioFlatFee, SIGNAL('clicked()'), setFlatFee())
      self.connect(self.edtFeeAmt, SIGNAL('textChanged(QString)'), updateLbl)
      
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
      
      self.radioFeeByte = QRadioButton(self.tr("Fee/Byte (Satoshi/Byte)"))
      self.edtFeeByte = QLineEdit(fee_byte)
      self.edtFeeByte.setFont(GETFONT('Fixed'))
      self.edtFeeByte.setMinimumWidth(tightSizeNChar(self.edtFeeByte, 6)[0])
      self.edtFeeByte.setMaximumWidth(tightSizeNChar(self.edtFeeByte, 12)[0])
      
      self.connect(self.radioFeeByte, SIGNAL('clicked()'), setFeeByte())
      self.connect(self.edtFeeByte, SIGNAL('textChanged(QString)'), updateLbl)
            
      frmFeeByte = QFrame()
      frmFeeByte.setFrameStyle(STYLE_RAISED)
      layoutFeeByte = QGridLayout()
      layoutFeeByte.addWidget(self.radioFeeByte, 0, 0, 1, 1)
      layoutFeeByte.addWidget(self.edtFeeByte, 0, 1, 1, 1)
      frmFeeByte.setLayout(layoutFeeByte)
      
      #auto fee/byte
      if isSmartFee:
         frmAutoFeeByte = self.setupSmartAutoFeeByteUI(\
            feeEstimate, blocksToConfirm, feeStrategy)
      else:
         frmAutoFeeByte = self.setupLegacyAutoFeeByteUI(\
            feeEstimate, blocksToConfirm)
      
      #adjust and close
      self.btnClose = QPushButton(self.tr('Close'))
      self.connect(self.btnClose, SIGNAL('clicked()'), self.accept)
      
      self.checkBoxAdjust = QCheckBox(self.tr('Adjust fee/byte for privacy'))
      self.checkBoxAdjust.setChecked(\
         self.main.getSettingOrSetDefault('AdjustFee', True))
            
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
      self.setWindowTitle(self.tr('Select Fee Type'))
      
      self.selectType(defaultCheckState)

      self.setFocus()  

   #############################################################################   
   def setupLegacyAutoFeeByteUI(self, feeEstimate, blocksToConfirm):
      def setAutoFeeByte():
         def callbck():
            return self.selectType('Auto')
         return callbck      
 
      def updateLbl():
         self.updateCoinSelection()

      def feeByteToStr(feeByte):
         try:
            self.feeByte = feeByte
            return "<u>%.1f</u>" % feeByte
         except:
            self.feeByte = -1
            if isinstance(feeByte, str):
               return feeByte
            else:
               return "N/A"

      radioButtonTxt = self.tr("Fee rate from node (sat/Byte): ")
      if not self.validAutoFee:      
         radioButtonTxt = self.tr("Failed to fetch fee/byte from node")
         
      self.radioAutoFeeByte = QRadioButton(radioButtonTxt)
      self.lblAutoFeeByte = QLabel(feeByteToStr(feeEstimate))
      self.lblAutoFeeByte.setFont(GETFONT('Fixed'))
      self.lblAutoFeeByte.setMinimumWidth(tightSizeNChar(self.lblAutoFeeByte, 6)[0])
      self.lblAutoFeeByte.setMaximumWidth(tightSizeNChar(self.lblAutoFeeByte, 12)[0])
      
      self.sliderAutoFeeByte = QSlider(Qt.Horizontal, self)
      self.sliderAutoFeeByte.setMinimum(2)
      self.sliderAutoFeeByte.setMaximum(6)
      self.sliderAutoFeeByte.setValue(blocksToConfirm)
      self.lblSlider = QLabel()
      
      def getSliderLabelTxt():
         return self.tr("Blocks to confirm: %1").arg(\
            unicode(self.sliderAutoFeeByte.value()))
         
      def updateAutoFeeByte():
         blocksToConfirm = self.sliderAutoFeeByte.value()
         try:
            feeEstimate, version, err = \
               self.getFeeByteFromNode(blocksToConfirm, FEEBYTE_CONSERVATIVE)
         except:
            feeEstimate = "N/A"
         
         self.lblSlider.setText(getSliderLabelTxt())         
         self.lblAutoFeeByte.setText(feeByteToStr(feeEstimate))
         updateLbl()
         
      self.lblSlider.setText(getSliderLabelTxt())
      
      self.connect(self.radioAutoFeeByte, SIGNAL('clicked()'), setAutoFeeByte())
      self.sliderAutoFeeByte.valueChanged.connect(updateAutoFeeByte)
      self.sliderAutoFeeByte.setEnabled(False)
            
      frmAutoFeeByte = QFrame()
      frmAutoFeeByte.setFrameStyle(STYLE_RAISED)
      layoutAutoFeeByte = QGridLayout()
      layoutAutoFeeByte.addWidget(self.radioAutoFeeByte, 0, 0, 1, 1)
      layoutAutoFeeByte.addWidget(self.lblAutoFeeByte, 0, 1, 1, 1)  
      layoutAutoFeeByte.addWidget(self.lblSlider, 1, 0, 1, 2)
      layoutAutoFeeByte.addWidget(self.sliderAutoFeeByte, 2, 0, 1, 2)
      frmAutoFeeByte.setLayout(layoutAutoFeeByte)
      
      if not self.validAutoFee:
         frmAutoFeeByte.setEnabled(False)

      return frmAutoFeeByte

   #############################################################################   
   def setupSmartAutoFeeByteUI(self, feeEstimate, blocksToConfirm, strat):
      def setAutoFeeByte():
         def callbck():
            return self.selectType('Auto')
         return callbck      
               
      stratList = [FEEBYTE_CONSERVATIVE, FEEBYTE_ECONOMICAL]

      def updateLbl():
         self.updateCoinSelection()

      def getStrategyString():
         try:
            cbIndex = self.comboStrat.currentIndex()
            return stratList[cbIndex]
         except:
            return FEEBYTE_CONSERVATIVE

      def feeByteToStr(feeByte):
         try:
            self.feeByte = feeByte
            return "<u>%.1f</u>" % feeByte
         except:
            self.feeByte = -1
            if isinstance(feeByte, str):
               return feeByte
            else:
               return "N/A"
      
      radioButtonTxt = self.tr("Fee rate from node (sat/Byte): ")
      if not self.validAutoFee:      
         radioButtonTxt = self.tr("Failed to fetch fee/byte from node")
         
      self.radioAutoFeeByte = QRadioButton(radioButtonTxt)
      self.lblAutoFeeByte = QLabel(feeByteToStr(feeEstimate))
      self.lblAutoFeeByte.setFont(GETFONT('Fixed'))
      self.lblAutoFeeByte.setMinimumWidth(tightSizeNChar(self.lblAutoFeeByte, 6)[0])
      self.lblAutoFeeByte.setMaximumWidth(tightSizeNChar(self.lblAutoFeeByte, 12)[0])
      
      self.sliderAutoFeeByte = QSlider(Qt.Horizontal, self)
      self.sliderAutoFeeByte.setMinimum(2)
      self.sliderAutoFeeByte.setMaximum(100)
      self.sliderAutoFeeByte.setValue(blocksToConfirm)
      self.lblSlider = QLabel()

      self.lblStrat = QLabel(self.tr("Profile:"))
      self.ttStart = self.main.createToolTipWidget(self.tr(
         '''
         <u>Fee Estimation Profiles:</u><br><br>
         <b>CONSERVATIVE:</b> Short term estimate. More reactive to current 
         changes in the mempool. Use this estimate if you want a high probability 
         of getting your transaction mined quickly. <br><br>
         <b>ECONOMICAL:</b> Long term estimate. Ignores short term changes to the 
         mempool. Use this profile if you want low fees and can tolerate swings 
         in the projected confirmation window. <br><br>

         The estimate profiles may not diverge until your node has gathered 
         enough data from the network to refine its predictions. Refer to the
         \"estimatesmartfee\" section in the Bitcoin Core 0.15 changelog for more
         informations.
         '''))
      self.comboStrat = QComboBox()
      currentIndex = 0
      for i in range(len(stratList)):
         self.comboStrat.addItem(stratList[i])
         if stratList[i] == strat:
            currentIndex = i
      self.comboStrat.setCurrentIndex(currentIndex)

      def getSliderLabelTxt():
         return self.tr("Blocks to confirm: %1").arg(\
               unicode(self.sliderAutoFeeByte.value()))
         
      def updateAutoFeeByte():
         blocksToConfirm = self.sliderAutoFeeByte.value()
         strategy = getStrategyString()
         try:
            feeEstimate, version, err = \
               self.getFeeByteFromNode(blocksToConfirm, strategy)
         except:
            feeEstimate = "N/A"
         
         self.lblSlider.setText(getSliderLabelTxt())         
         self.lblAutoFeeByte.setText(feeByteToStr(feeEstimate))
         updateLbl()

      def stratComboChange():
         updateAutoFeeByte()

      self.lblSlider.setText(getSliderLabelTxt())
     
      self.connect(self.radioAutoFeeByte, SIGNAL('clicked()'), setAutoFeeByte())
      self.sliderAutoFeeByte.valueChanged.connect(updateAutoFeeByte)
      self.sliderAutoFeeByte.setEnabled(False)

      self.connect(self.comboStrat, SIGNAL('currentIndexChanged(int)'), stratComboChange)
            
      frmAutoFeeByte = QFrame()
      frmAutoFeeByte.setFrameStyle(STYLE_RAISED)
      layoutAutoFeeByte = QGridLayout()
      layoutAutoFeeByte.addWidget(self.radioAutoFeeByte, 0, 0, 1, 2)
      layoutAutoFeeByte.addWidget(self.lblAutoFeeByte, 0, 2, 1, 2)  
      layoutAutoFeeByte.addWidget(self.lblSlider, 1, 0, 1, 1)
      layoutAutoFeeByte.addWidget(self.sliderAutoFeeByte, 2, 0, 1, 4)
      layoutAutoFeeByte.addWidget(self.lblStrat, 3, 0, 1, 1)
      layoutAutoFeeByte.addWidget(self.comboStrat, 3, 1, 1, 2)
      layoutAutoFeeByte.addWidget(self.ttStart, 3, 3, 1, 1)

      frmAutoFeeByte.setLayout(layoutAutoFeeByte)
      
      if not self.validAutoFee:
         frmAutoFeeByte.setEnabled(False)

      return frmAutoFeeByte

   #############################################################################   
   def getFeeByteFromNode(self, blocksToConfirm, strategy):
      try:
         feeEstimateResult = estimateFee(blocksToConfirm, strategy)
         return feeEstimateResult.val_ * 100000, \
            feeEstimateResult.isSmart_, \
            feeEstimateResult.error_
      except:
         self.validAutoFee = False
         return "N/A", False, ""

   #############################################################################   
   def selectType(self, strType):
      self.radioFlatFee.setChecked(False)
      self.radioFeeByte.setChecked(False)
      self.radioAutoFeeByte.setChecked(False)
      self.sliderAutoFeeByte.setEnabled(False)
      
      if strType == 'FlatFee':
         self.radioFlatFee.setChecked(True)
      elif strType == 'FeeByte':
         self.radioFeeByte.setChecked(True)
      elif strType == 'Auto':
         if not self.validAutoFee:
            self.radioFeeByte.setChecked(True)
         else:
            self.radioAutoFeeByte.setChecked(True)
            self.sliderAutoFeeByte.setEnabled(True)
            
      self.updateCoinSelection()
      self.updateLabelButton()
      
   #############################################################################
   def updateCoinSelection(self):
      try:
         self.coinSelectionCallback()
      except:
         self.updateLabelButton()
   
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
   def updateLabelButton(self, reset=False):
      try:
         if reset:
            raise Exception()
         txSize, flatFee, feeByte = self.getCoinSelectionState()      
         self.updateLabelButtonText(txSize, flatFee, feeByte)

      except:
         self.updateLabelButtonText('N/A', 'N/A', 'N/A')
         
   #############################################################################
   def resetLabel(self):
      self.updateLabelButton(True)
   
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
         fee_byte = self.feeByte
         
      adjust_fee = self.checkBoxAdjust.isChecked()
         
      return fee, fee_byte, adjust_fee    
   
   #############################################################################
   def setZeroFee(self):
      self.edtFeeAmt.setText('0')
      self.selectType('FlatFee')
      
