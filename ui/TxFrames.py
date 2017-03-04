################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

from PyQt4.Qt import * #@UnusedWildImport
from PyQt4.QtGui import * #@UnusedWildImport

from armoryengine.BDM import TheBDM, BDM_BLOCKCHAIN_READY
from qtdefines import * #@UnusedWildImport
from armoryengine.Transaction import UnsignedTransaction, getTxOutScriptType
from armoryengine.Script import convertScriptToOpStrings
from armoryengine.CoinSelection import PySelectCoins, calcMinSuggestedFees,\
   calcMinSuggestedFeesHackMS, PyUnspentTxOut, estimateTxSize
from ui.WalletFrames import SelectWalletFrame, LockboxSelectFrame
from armoryengine.MultiSigUtils import \
      calcLockboxID, readLockboxEntryStr, createLockboxEntryStr, isBareLockbox,\
   isP2SHLockbox
from armoryengine.ArmoryUtils import MAX_COMMENT_LENGTH, getAddrByte
from FeeSelectUI import FeeSelectionDialog
from CppBlockUtils import TXOUT_SCRIPT_P2SH


class SendBitcoinsFrame(ArmoryFrame):
   def __init__(self, parent, main, initLabel='',
                 wlt=None, prefill=None, wltIDList=None,
                 selectWltCallback = None, onlyOfflineWallets=False,
                 sendCallback = None, createUnsignedTxCallback = None,
                 spendFromLockboxID=None):
      super(SendBitcoinsFrame, self).__init__(parent, main)
      self.maxHeight = tightSizeNChar(GETFONT('var'), 1)[1] + 8
      self.customUtxoList = []
      self.altBalance = None
      self.useCustomListInFull = False
      self.wlt = wlt
      self.wltID = wlt.uniqueIDB58 if wlt else None
      self.wltIDList = wltIDList
      self.selectWltCallback = selectWltCallback
      self.sendCallback = sendCallback
      self.createUnsignedTxCallback = createUnsignedTxCallback
      self.lbox = self.main.getLockboxByID(spendFromLockboxID)
      self.onlyOfflineWallets = onlyOfflineWallets
      self.widgetTable = []
      self.isMax = False
      self.scrollRecipArea = QScrollArea()
      lblRecip = QRichLabel('<b>Enter Recipients:</b>')
      lblRecip.setAlignment(Qt.AlignLeft | Qt.AlignBottom)



      self.freeOfErrors = True

      feetip = self.main.createToolTipWidget(\
            self.tr('Transaction fees go to users who contribute computing power to '
            'keep the Bitcoin network secure, and in return they get your transaction '
            'included in the blockchain faster.'))

      self.feeDialog = FeeSelectionDialog(self, self.main)
      self.feeLblButton = self.feeDialog.getLabelButton()
      
      def feeDlg():
         self.feeDialog.exec_()
      self.connect(self.feeLblButton, SIGNAL('clicked()'), feeDlg)


      # This used to be in the later, expert-only section, but some of these
      # are actually getting referenced before being declared.  So moved them
      # up to here.
      self.chkDefaultChangeAddr = QCheckBox(self.tr('Use an existing address for change'))
      self.radioFeedback = QRadioButton(self.tr('Send change to first input address'))
      self.radioSpecify = QRadioButton(self.tr('Specify a change address'))
      self.lblChangeAddr = QRichLabel(self.tr('Change:'))

      addrWidgets = self.main.createAddressEntryWidgets(self, maxDetectLen=36, 
                                                      defaultWltID=self.wltID)
      self.edtChangeAddr  = addrWidgets['QLE_ADDR']
      self.btnChangeAddr  = addrWidgets['BTN_BOOK']
      self.lblAutoDetect  = addrWidgets['LBL_DETECT']
      self.getUserChangeScript = addrWidgets['CALLBACK_GETSCRIPT']

      self.chkRememberChng = QCheckBox(self.tr('Remember for future transactions'))
      self.vertLine = VLINE()

      self.ttipSendChange = self.main.createToolTipWidget(\
            self.tr('Most transactions end up with oversized inputs and Armory will send '
            'the change to the next address in this wallet.  You may change this '
            'behavior by checking this box.'))
      self.ttipFeedback = self.main.createToolTipWidget(\
            self.tr('Guarantees that no new addresses will be created to receive '
            'change. This reduces anonymity, but is useful if you '
            'created this wallet solely for managing imported addresses, '
            'and want to keep all funds within existing addresses.'))
      self.ttipSpecify = self.main.createToolTipWidget(\
            self.tr('You can specify any valid Bitcoin address for the change.  '
            '<b>NOTE:</b> If the address you specify is not in this wallet, '
            'Armory will not be able to distinguish the outputs when it shows '
            'up in your ledger.  The change will look like a second recipient, '
            'and the total debit to your wallet will be equal to the amount '
            'you sent to the recipient <b>plus</b> the change.'))
      self.ttipUnsigned = self.main.createToolTipWidget(\
         self.tr('Check this box to create an unsigned transaction to be signed'
         ' and/or broadcast later.'))
      self.unsignedCheckbox = QCheckBox(self.tr('Create Unsigned'))
      self.btnSend = QPushButton(self.tr('Send!'))
      self.btnCancel = QPushButton(self.tr('Cancel'))
      self.connect(self.btnCancel, SIGNAL(CLICKED), parent.reject)
      
      self.btnPreviewTx = QLabelButton("Preview Transaction")
      self.connect(self.btnPreviewTx, SIGNAL('clicked()'), self.previewTx)

      # Created a standard wallet chooser frame. Pass the call back method
      # for when the user selects a wallet.
      if self.lbox is None:
         coinControlCallback = self.coinControlUpdate if self.main.usermode == USERMODE.Expert else None
         self.frmSelectedWlt = SelectWalletFrame(parent, main, 
                     VERTICAL, 
                     self.wltID, 
                     wltIDList=self.wltIDList, 
                     selectWltCallback=self.setWallet, \
                     coinControlCallback=coinControlCallback, 
                     onlyOfflineWallets=self.onlyOfflineWallets)
      else:
         self.frmSelectedWlt = LockboxSelectFrame(parent, main, 
                                    VERTICAL,
                                    self.lbox.uniqueIDB58)
         self.setupCoinSelectionForLockbox(self.lbox)

      # Only the Create  Unsigned Transaction button if there is a callback for it.
      # Otherwise the containing dialog or wizard will provide the offlien tx button
      metaButtonList = [self.btnPreviewTx, STRETCH]
      if self.createUnsignedTxCallback:
         self.connect(self.unsignedCheckbox, SIGNAL(CLICKED), self.unsignedCheckBoxUpdate)
         metaButtonList.append(self.unsignedCheckbox)
         metaButtonList.append(self.ttipUnsigned)
      
      buttonList = [STRETCH, self.btnCancel]
      # Only add the Send Button if there's a callback for it
      # Otherwise the containing dialog or wizard will provide the send button
      if self.sendCallback:
         self.connect(self.btnSend, SIGNAL(CLICKED), self.createTxAndBroadcast)
         buttonList.append(self.btnSend)
      buttonList.append(STRETCH)
         
      txFrm = makeHorizFrame([self.feeLblButton, feetip], STYLE_RAISED, condenseMargins=True)
      metaFrm = makeHorizFrame(metaButtonList, STYLE_RAISED, condenseMargins=True)
      buttonFrame = makeHorizFrame(buttonList, condenseMargins=True)
      btnEnterURI = QPushButton(self.tr('Manually Enter "bitcoin:" Link'))
      ttipEnterURI = self.main.createToolTipWidget( self.tr("""
         Armory does not always succeed at registering itself to handle 
         URL links from webpages and email.  
         Click this button to copy a "bitcoin:" link directly into Armory."""))
      self.connect(btnEnterURI, SIGNAL("clicked()"), self.clickEnterURI)
      fromFrameList = [self.frmSelectedWlt]

      if not self.main.usermode == USERMODE.Standard:
         frmEnterURI = makeHorizFrame([btnEnterURI, ttipEnterURI], condenseMargins=True)
         fromFrameList.append(frmEnterURI)

      ########################################################################
      # In Expert usermode, allow the user to modify source addresses
      if self.main.usermode == USERMODE.Expert:

         sendChangeToFrame = QFrame()
         sendChangeToLayout = QGridLayout()
         sendChangeToLayout.addWidget(self.lblChangeAddr,  0,0)
         sendChangeToLayout.addWidget(self.edtChangeAddr,  0,1)
         sendChangeToLayout.addWidget(self.btnChangeAddr,  0,2)
         sendChangeToLayout.addWidget(self.lblAutoDetect,  1,1, 1,2)
         sendChangeToLayout.setColumnStretch(0,0)
         sendChangeToLayout.setColumnStretch(1,1)
         sendChangeToLayout.setColumnStretch(2,0)
         sendChangeToFrame.setLayout(sendChangeToLayout)
         

         btngrp = QButtonGroup(self)
         btngrp.addButton(self.radioFeedback)
         btngrp.addButton(self.radioSpecify)
         btngrp.setExclusive(True)
         self.connect(self.chkDefaultChangeAddr, SIGNAL('toggled(bool)'), self.toggleChngAddr)
         self.connect(self.radioSpecify, SIGNAL('toggled(bool)'), self.toggleSpecify)
         frmChngLayout = QGridLayout()
         i = 0;
         frmChngLayout.addWidget(self.chkDefaultChangeAddr, i, 0, 1, 6)
         frmChngLayout.addWidget(self.ttipSendChange,       i, 6, 1, 2)
         i += 1
         frmChngLayout.addWidget(self.radioFeedback,        i, 1, 1, 5)
         frmChngLayout.addWidget(self.ttipFeedback,         i, 6, 1, 2)
         i += 1
         frmChngLayout.addWidget(self.radioSpecify,         i, 1, 1, 5)
         frmChngLayout.addWidget(self.ttipSpecify,          i, 6, 1, 2)
         i += 1
         frmChngLayout.addWidget(sendChangeToFrame, i, 1, 1, 6)
         i += 1
         frmChngLayout.addWidget(self.chkRememberChng, i, 1, 1, 7)

         frmChngLayout.addWidget(self.vertLine, 1, 0, i - 1, 1)
         frmChngLayout.setColumnStretch(0,1)
         frmChngLayout.setColumnStretch(1,1)
         frmChngLayout.setColumnStretch(2,1)
         frmChngLayout.setColumnStretch(3,1)
         frmChngLayout.setColumnStretch(4,1)
         frmChngLayout.setColumnStretch(5,1)
         frmChngLayout.setColumnStretch(6,1)
         frmChangeAddr = QFrame()
         frmChangeAddr.setLayout(frmChngLayout)
         frmChangeAddr.setFrameStyle(STYLE_SUNKEN)
         fromFrameList.append('Stretch')
         fromFrameList.append(frmChangeAddr)
      else:
         fromFrameList.append('Stretch')
      frmBottomLeft = makeVertFrame(fromFrameList, STYLE_RAISED, condenseMargins=True)

      lblSend = QRichLabel(self.tr('<b>Sending from Wallet:</b>'))
      lblSend.setAlignment(Qt.AlignLeft | Qt.AlignBottom)


      leftFrame = makeVertFrame([lblSend, frmBottomLeft], condenseMargins=True)
      rightFrame = makeVertFrame(\
         [lblRecip, self.scrollRecipArea, txFrm, metaFrm, buttonFrame], condenseMargins=True)
      layout = QHBoxLayout()
      layout.addWidget(leftFrame, 0)
      layout.addWidget(rightFrame, 1)
      layout.setContentsMargins(0,0,0,0)
      layout.setSpacing(0)
      self.setLayout(layout)

      self.makeRecipFrame(1)
      self.setWindowTitle(self.tr('Send Bitcoins'))
      self.setMinimumHeight(self.maxHeight * 20)

      if prefill:
         amount = prefill.get('amount','')
         message = prefill.get('message','')
         label = prefill.get('label','')
         if prefill.get('lockbox',''):
            plainStr = createLockboxEntryStr(prefill.get('lockbox',''))
            self.addOneRecipient(None, amount, message, None, plainStr)
         else:
            addrStr = prefill.get('address','')
            atype, addr160 = addrStr_to_hash160(addrStr)
            if atype == getAddrByte():
               self.addOneRecipient(addr160, amount, message, label)
            else:
               self.addOneRecipient(None, amount, message, label, plainText=addrStr)

      if self.lbox:
         self.toggleSpecify(False)
         self.toggleChngAddr(False)


      hexgeom = self.main.settings.get('SendBtcGeometry')
      if len(hexgeom) > 0:
         geom = QByteArray.fromHex(hexgeom)
         self.restoreGeometry(geom)
         
   # Use this to fire wallet change after the constructor is complete.
   # if it's called during construction then self's container may not exist yet.
   def fireWalletChange(self):
      # Set the wallet in the wallet selector and let all of display components
      # react to it. This is at the end so that we can be sure that all of the
      # components that react to setting the wallet exist.
      if self.lbox:
         self.unsignedCheckbox.setChecked(True)
         self.unsignedCheckbox.setEnabled(False)
      else:
         self.frmSelectedWlt.updateOnWalletChange()

      self.unsignedCheckBoxUpdate()


   #############################################################################
   def unsignedCheckBoxUpdate(self):
      if self.unsignedCheckbox.isChecked():
         self.btnSend.setText(self.tr('Continue'))
         self.btnSend.setToolTip(self.tr('Click to create an unsigned transaction!'))
      else:
         self.btnSend.setText(self.tr('Send!'))
         self.btnSend.setToolTip(self.tr('Click to send bitcoins!'))
      

   #############################################################################
   def addOneRecipient(self, addr160, amt, msg, label=None, plainText=None):
      """
      plainText arg can be used, and will override addr160.  It is for 
      injecting either fancy script types, or special keywords into the 
      address field, such as a lockbox ID
      """
      if label is not None and addr160:
         self.wlt.setComment(addr160, label)

      lastIsEmpty = True
      for widg in ['QLE_ADDR', 'QLE_AMT', 'QLE_COMM']: 
         if len(str(self.widgetTable[-1][widg].text())) > 0:
            lastIsEmpty = False

      if not lastIsEmpty:
         self.makeRecipFrame(len(self.widgetTable) + 1)

      if amt:
         amt = coin2str(amt, maxZeros=2).strip()

      if plainText is None:
         plainText = hash160_to_addrStr(addr160)

      self.widgetTable[-1]['QLE_ADDR'].setText(plainText)
      self.widgetTable[-1]['QLE_ADDR'].setCursorPosition(0)
      self.widgetTable[-1]['QLE_AMT'].setText(amt)
      self.widgetTable[-1]['QLE_AMT'].setCursorPosition(0)
      self.widgetTable[-1]['QLE_COMM'].setText(msg)
      self.widgetTable[-1]['QLE_COMM'].setCursorPosition(0)
      
      self.addCoinSelectionRecipient(len(self.widgetTable) - 1)
      self.resolveCoinSelection()


   #############################################################################
   # Now that the wallet can change in the context of the send dialog, this
   # method is used as a callback for when the wallet changes
   # isDoubleClick is unused - do not accept or close dialog on double click
   def setWallet(self, wlt, isDoubleClick=False):
      self.wlt = wlt
      self.wltID = wlt.uniqueIDB58 if wlt else None
      
      self.setupCoinSelectionInstance()
      
      if not TheBDM.getState() == BDM_BLOCKCHAIN_READY:
         self.lblSummaryBal.setText('(available when online)', color='DisableFG')
      if self.main.usermode == USERMODE.Expert:
         # Pre-set values based on settings
         chngBehave = self.main.getWltSetting(self.wltID, 'ChangeBehavior')
         chngAddr = self.main.getWltSetting(self.wltID, 'ChangeAddr')
         if chngBehave == 'Feedback':
            self.chkDefaultChangeAddr.setChecked(True)
            self.radioFeedback.setChecked(True)
            self.radioSpecify.setChecked(False)
            self.toggleChngAddr(True)
            self.chkRememberChng.setChecked(True)
         elif chngBehave == 'Specify':
            self.chkDefaultChangeAddr.setChecked(True)
            self.radioFeedback.setChecked(False)
            self.radioSpecify.setChecked(True)
            self.toggleChngAddr(True)
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
            self.toggleChngAddr(False)

         if (self.chkDefaultChangeAddr.isChecked() and \
            not self.radioFeedback.isChecked() and \
            not self.radioSpecify.isChecked()):
            self.radioFeedback.setChecked(True)
      # If there is a unsigned then we have a send button and unsigned checkbox to update
      if self.createUnsignedTxCallback:
         self.unsignedCheckbox.setChecked(wlt.watchingOnly)
         self.unsignedCheckbox.setEnabled(not wlt.watchingOnly)
         self.unsignedCheckBoxUpdate()
      if self.selectWltCallback:
         self.selectWltCallback(wlt)
   
   #############################################################################      
   def setupCoinSelectionInstance(self):
      if self.wlt is None:
         self.coinSelection = None
         return
      
      self.coinSelection = self.wlt.cppWallet.getCoinSelectionInstance()
      self.resetCoinSelectionRecipients()
     
   #############################################################################   
   def setupCoinSelectionForLockbox(self, lbox):
      try:        
         lbCppWlt = self.main.cppLockboxWltMap[lbox.uniqueIDB58]
         self.coinSelection = Cpp.CoinSelectionInstance(\
            lbCppWlt, lbox.M, lbox.N, \
            TheBDM.getTopBlockHeight(), lbCppWlt.getSpendableBalance())
         
      except:
         self.coinSelection = None
      
   #############################################################################
   def resetCoinSelectionRecipients(self):
      
      if self.coinSelection is None:
         return   
      
      self.coinSelection.resetRecipients()
      for row in range(len(self.widgetTable)):
         self.addCoinSelectionRecipient(row)
         
      self.resolveCoinSelection()
         
   #############################################################################
   def addCoinSelectionRecipient(self, id_):
            
      try:
         coinSelRow = self.widgetTable[id_]
         
         prefix, h160 = addrStr_to_hash160(str(coinSelRow['QLE_ADDR'].text()).strip())
         scrAddr = prefix + h160
         valueStr = str(coinSelRow['QLE_AMT'].text()).strip()
         value = str2coin(valueStr, negAllowed=False)
         
         self.coinSelection.addRecipient(scrAddr, value)
      except:
         self.resetCoinSelectionText()
   
   #############################################################################   
   def updateCoinSelectionRecipient(self, id_):

      try:
         coinSelRow = self.widgetTable[id_]
      
         prefix, h160 = addrStr_to_hash160(str(coinSelRow['QLE_ADDR'].text()).strip())
         scrAddr = prefix + h160
         valueStr = str(coinSelRow['QLE_AMT'].text()).strip()
         try:
            value = str2coin(valueStr, negAllowed=False)
         except:
            value = 0
            
         self.coinSelection.updateRecipient(id_, scrAddr, value)
         self.resolveCoinSelection()
      except:
         self.resetCoinSelectionText()

   #############################################################################
   def serializeUtxoList(self, utxoList):
      serializedUtxoList = []
      for utxo in utxoList:
         bp = BinaryPacker()
         bp.put(UINT64, utxo.getValue())
         bp.put(UINT32, utxo.getTxHeight())
         bp.put(UINT16, utxo.getTxIndex())
         bp.put(UINT16, utxo.getTxOutIndex())
         bp.put(BINARY_CHUNK, utxo.getTxHash())
         bp.put(BINARY_CHUNK, utxo.getScript())
         serializedUtxoList.append(bp.getBinaryString())
         
      return serializedUtxoList
   
   #############################################################################   
   def resolveCoinSelection(self):  
      try:
         fee, feePerByte, adjust_fee = self.feeDialog.getFeeData()
         
         if self.customUtxoList is None or len(self.customUtxoList) == 0:
            self.coinSelection.selectUTXOs(fee, feePerByte, adjust_fee)
         else:
            
            serializedUtxoList = self.serializeUtxoList(self.customUtxoList)
               
            self.coinSelection.processCustomUtxoList(\
               serializedUtxoList, fee, feePerByte, self.useCustomListInFull, adjust_fee)   
              
         self.feeDialog.updateLabelButton(self.coinSelection)
      except:
         self.resetCoinSelectionText()
         
   #############################################################################
   def resetCoinSelectionText(self):
      self.feeDialog.resetLabel()
      
   #############################################################################
   # Update the available source address list and balance based on results from
   # coin control. This callback is now necessary because coin control was moved
   # to the Select Wallet Frame
   def coinControlUpdate(self, customUtxoList, altBalance, useAll):
      self.customUtxoList = customUtxoList
      self.altBalance = altBalance
      self.useCustomListInFull = useAll
      
      self.resolveCoinSelection()
        
   #############################################################################
   def validateInputsGetUSTX(self, peek=False):

      self.freeOfErrors = True
      scripts = []
      addrList = []
      self.comments = []

      for row in range(len(self.widgetTable)):
         # Verify validity of address strings
         addrStr = str(self.widgetTable[row]['QLE_ADDR'].text()).strip()
         self.widgetTable[row]['QLE_ADDR'].setText(addrStr) # overwrite w/ stripped
         addrIsValid = True
         addrList.append(addrStr)
         try:
            enteredScript = self.widgetTable[row]['FUNC_GETSCRIPT']()['Script']
            if not enteredScript:
               addrIsValid = False
            else:
               scripts.append(enteredScript)
         except:
            LOGEXCEPT('Failed to parse entered address: %s', addrStr)
            addrIsValid = False

         if not addrIsValid:
            scripts.append('')
            self.freeOfErrors = False
            self.updateAddrColor(row, Colors.SlightRed)


      numChkFail = sum([1 if len(b)==0 else 0 for b in scripts])
      if not self.freeOfErrors:
         QMessageBox.critical(self, self.tr('Invalid Address'),
               self.tr("You have entered %1 invalid addresses. "
                       "The errors have been highlighted on the entry screen").arg(str(numChkFail)), QMessageBox.Ok)

         for row in range(len(self.widgetTable)):
            try:
               atype, a160 = addrStr_to_hash160(addrList[row]) 
               if atype == -1 or not atype in [ADDRBYTE,P2SHBYTE]:
                  net = 'Unknown Network'
                  if NETWORKS.has_key(addrList[row][0]):
                     net = NETWORKS[addrList[row][0]]
                  QMessageBox.warning(self, self.tr('Wrong Network!'), self.tr("""
                     Address %1 is for the wrong network!  You are on the <b>%2</b>
                     and the address you supplied is for the the <b>%3</b>!""").arg(row+1, NETWORKS[ADDRBYTE], net), QMessageBox.Ok)
            except:
               pass

         return False

      # Construct recipValuePairs and check that all metrics check out
      scriptValPairs = []
      totalSend = 0
      for row in range(len(self.widgetTable)):
         try:
            valueStr = str(self.widgetTable[row]['QLE_AMT'].text()).strip()
            value = str2coin(valueStr, negAllowed=False)
            if value == 0:
               QMessageBox.critical(self, self.tr('Zero Amount'), \
                  self.tr('You cannot send 0 BTC to any recipients.  <br>Please enter '
                  'a positive amount for recipient %1.').arg(row+1), QMessageBox.Ok)
               return False

         except NegativeValueError:
            QMessageBox.critical(self, self.tr('Negative Value'), \
               self.tr('You have specified a negative amount for recipient %1. <br>Only '
               'positive values are allowed!.').arg(row + 1), QMessageBox.Ok)
            return False
         except TooMuchPrecisionError:
            QMessageBox.critical(self, self.tr('Too much precision'), \
               self.tr('Bitcoins can only be specified down to 8 decimal places. '
               'The smallest value that can be sent is  0.0000 0001 BTC. '
               'Please enter a new amount for recipient %1.').arg(row + 1), QMessageBox.Ok)
            return False
         except ValueError:
            QMessageBox.critical(self, self.tr('Missing recipient amount'), \
               self.tr('You did not specify an amount to send!'), QMessageBox.Ok)
            return False
         except:
            QMessageBox.critical(self, self.tr('Invalid Value String'), \
               self.tr('The amount you specified '
               'to send to address %1 is invalid (%2).').arg(row + 1, valueStr), QMessageBox.Ok)
            LOGERROR('Invalid amount specified: "%s"', valueStr)
            return False

         totalSend += value

         script = self.widgetTable[row]['FUNC_GETSCRIPT']()['Script']
         scriptValPairs.append([script, value])
         self.comments.append((str(self.widgetTable[row]['QLE_COMM'].text()), value))

      utxoSelect = self.getUsableTxOutList()
      fee = self.coinSelection.getFlatFee()
      fee_byte = self.coinSelection.getFeeByte()

      # Warn user of excessive fee specified
      if peek == False:
         feebyteStr = "%.2f" % fee_byte
         if fee_byte > 10 * MIN_FEE_BYTE:
            reply = QMessageBox.warning(self, self.tr('Excessive Fee'), self.tr("""
               Your transaction comes with a fee rate of <b>%1 satoshis per byte</b>.
               </br></br> 
               This is much higher than the median fee rate of <b>%2 satoshi/Byte</b>.
               <br><br>
               Are you <i>absolutely sure</i> that you want to send with this
               fee? If you do not want to proceed with this fee rate, click "No".""").arg(\
                  feebyteStr, unicode(MIN_FEE_BYTE)), QMessageBox.Yes | QMessageBox.No)
   
            if not reply==QMessageBox.Yes:
               return False
            
         elif fee_byte < MIN_FEE_BYTE / 10:
            reply = QMessageBox.warning(self, self.tr('Insufficient Fee'), self.tr("""
               Your transaction comes with a fee rate of <b>%1 satoshi/Byte</b>.
               </br><br> 
               This is much lower than the median fee rate of <b>%2 satoshi/Byte</b>.
               <br><br>
               Are you <i>absolutely sure</i> that you want to send with this
               fee? If you do not want to proceed with this fee rate, click "No".""").arg(\
                  feebyteStr, unicode(MIN_FEE_BYTE)), QMessageBox.Yes | QMessageBox.No)
   
            if not reply==QMessageBox.Yes:
               return False         


      if len(utxoSelect) == 0:
         QMessageBox.critical(self, self.tr('Coin Selection Error'), self.tr("""
            There was an error constructing your transaction, due to a 
            quirk in the way Bitcoin transactions work.  If you see this
            error more than once, try sending your BTC in two or more 
            separate transactions."""), QMessageBox.Ok)
         return False

      # ## IF we got here, everything is good to go...
      #   Just need to get a change address and then construct the tx
      totalTxSelect = sum([u.getValue() for u in utxoSelect])
      totalChange = totalTxSelect - (totalSend + fee)

      self.changeScript = ''
      self.selectedBehavior = ''
      if totalChange > 0:
         script,behavior = self.determineChangeScript(\
                              utxoSelect, scriptValPairs, peek)
         self.changeScript = script
         self.selectedBehavior = behavior
         scriptValPairs.append([self.changeScript, totalChange])
         LOGINFO('Change address behavior: %s', self.selectedBehavior)
      else:
         self.selectedBehavior = NO_CHANGE
         
      # Keep a copy of the originally-sorted list for display
      origSVPairs = scriptValPairs[:]

      # Anonymize the outputs
      random.shuffle(scriptValPairs)

      p2shMap = {}
      pubKeyMap = {}
      
      # In order to create the USTXI objects, need to make we supply a
      # map of public keys that can be included
      if self.lbox:
         p2shMap = {binary_to_hex(script_to_scrAddr(script_to_p2sh_script(
                        self.lbox.binScript))) : self.lbox.binScript}
         ustx = UnsignedTransaction().createFromTxOutSelection( \
                                       utxoSelect, scriptValPairs,
                                       p2shMap = p2shMap)

         for i in range(len(ustx.ustxInputs)):
            ustx.ustxInputs[i].contribID = self.lbox.uniqueIDB58

         for i in range(len(ustx.decorTxOuts)):
            if ustx.decorTxOuts[i].binScript == self.lbox.binScript:
               ustx.decorTxOuts[i].contribID = self.lbox.uniqueIDB58

      else:
         # If this has nothing to do with lockboxes, we need to make sure
         # we're providing a key map for the inputs
         
         for utxo in utxoSelect:
            scrType = getTxOutScriptType(utxo.getScript())
            scrAddr = utxo.getRecipientScrAddr()
            if scrType in CPP_TXOUT_STDSINGLESIG:
               a160 = scrAddr_to_hash160(scrAddr)[1]
               addrObj = self.wlt.getAddrByHash160(a160)
               if addrObj:
                  pubKeyMap[scrAddr] = addrObj.binPublicKey65.toBinStr()
            elif scrType == CPP_TXOUT_P2SH:
               p2shScript = self.wlt.cppWallet.getP2SHScriptForHash(utxo.getScript())
               p2shKey = binary_to_hex(script_to_scrAddr(script_to_p2sh_script(
                  p2shScript)))
               p2shMap[p2shKey]  = p2shScript  
               
               addrIndex = self.wlt.cppWallet.getAssetIndexForAddr(utxo.getRecipientHash160())
               try:
                  addrStr = self.wlt.chainIndexMap[addrIndex]
               except:
                  if addrIndex < -2:
                     importIndex = self.wlt.cppWallet.convertToImportIndex(addrIndex)
                     addrStr = self.wlt.linearAddr160List[importIndex]
                  else:
                     raise Exception("invalid address index")
                  
               addrObj = self.wlt.addrMap[addrStr]
               pubKeyMap[scrAddr] = addrObj.binPublicKey65.toBinStr()               

         '''
         If we are consuming any number of SegWit utxos, pass the utxo selection
         and outputs to the new signer for processing instead of creating the
         unsigned tx in Python.
         '''
         
         # Now create the unsigned USTX
         ustx = UnsignedTransaction().createFromTxOutSelection(\
            utxoSelect, scriptValPairs, pubKeyMap, p2shMap=p2shMap)

      #ustx.pprint()

      txValues = [totalSend, fee, totalChange]
      if not peek:
         if not self.unsignedCheckbox.isChecked():
            dlg = DlgConfirmSend(self.wlt, origSVPairs, txValues[1], self, \
                                                     self.main, True, ustx)
      
            if not dlg.exec_():
               return False
         else:
            self.main.warnNewUSTXFormat()
      
      return ustx
   
  
   def createTxAndBroadcast(self):
      
      def unlockWallet():
         if self.wlt.isLocked:
            Passphrase = None  
                  
            unlockdlg = DlgUnlockWallet(self.wlt, \
                  self, self.main, 'Send Transaction', returnPassphrase=True)
            if unlockdlg.exec_():
               if unlockdlg.Accepted == 1:
                  Passphrase = unlockdlg.securePassphrase.copy()
                  unlockdlg.securePassphrase.destroy()
                     
            if Passphrase is None or self.wlt.kdf is None:
               QMessageBox.critical(self.parent(), self.tr('Wallet is Locked'), \
                  self.tr('Cannot sign transaction while your wallet is locked. '), \
                  QMessageBox.Ok)
               return
            else:
               self.wlt.kdfKey = self.wlt.kdf.DeriveKey(Passphrase)
               Passphrase.destroy()                     
      
      # The Send! button is clicked validate and broadcast tx
      ustx = self.validateInputsGetUSTX()
            
      if ustx:
         if self.createUnsignedTxCallback and self.unsignedCheckbox.isChecked():
            self.createUnsignedTxCallback(ustx)
         else:
            try:
               unlockWallet()
               
               self.wlt.mainWnd = self.main
               self.wlt.parent = self
      
               commentStr = ''
               if len(self.comments) == 1:
                  commentStr = self.comments[0][0]
               else:
                  for i in range(len(self.comments)):
                     amt = self.comments[i][1]
                     if len(self.comments[i][0].strip()) > 0:
                        commentStr += '%s (%s);  ' % (self.comments[i][0], coin2str_approx(amt).strip())
      
      
               ustxSigned = self.wlt.signUnsignedTx(ustx)
               finalTx = ustxSigned.getSignedPyTx()
               if len(commentStr) > 0:
                  self.wlt.setComment(finalTx.getHash(), commentStr)
               self.main.broadcastTransaction(finalTx)
            except:
               LOGEXCEPT('Problem sending transaction!')
               # TODO: not sure what errors to catch here, yet...
               raise
            if self.sendCallback:
               self.sendCallback()

   #############################################################################
   def getUsableBalance(self):
      if self.lbox is None:
         if self.altBalance == None:
            return self.wlt.getBalance('Spendable')
         else:
            return self.altBalance
      else:
         lbID = self.lbox.uniqueIDB58
         cppWlt = self.main.cppLockboxWltMap.get(lbID)
         if cppWlt is None:
            LOGERROR('Somehow failed to get cppWlt for lockbox: %s', lbID)

         return cppWlt.getSpendableBalance()
         
         


   #############################################################################
   def getUsableTxOutList(self):
      utxoVec = self.coinSelection.getUtxoSelection()
      utxoSelect = []
      for i in range(len(utxoVec)):
         pyUtxo = PyUnspentTxOut().createFromCppUtxo(utxoVec[i])
         utxoSelect.append(pyUtxo)
      return utxoSelect

   #############################################################################
   def getDefaultChangeAddress(self, scriptValPairs, peek):
      def getAddr(addrObj, typeStr):
         if typeStr == 'P2PKH':
            addrStr = self.wlt.getP2PKHAddrForIndex(addrObj.chainIndex)
         elif typeStr == 'P2SH-P2WPKH':
            addrStr = self.wlt.getNestedSWAddrForIndex(addrObj.chainIndex)
         elif typeStr == 'P2SH-P2PK':
            addrStr = self.wlt.getNestedP2PKAddrForIndex(addrObj.chainIndex)
         
         return addrStr
      
      if peek is True:
         newAddr = self.wlt.peekNextUnusedAddr()
      else:
         newAddr = self.wlt.getNextUnusedAddress()
         
      changeType = self.main.getSettingOrSetDefault('Default_ChangeType', DEFAULT_CHANGE_TYPE)
      
      if changeType != 'Auto':
         return getAddr(newAddr, changeType)
      
      #check if there are any P2SH recipients
      haveP2SH = False
      for script, val in scriptValPairs:
         if Cpp.BtcUtils.getTxOutScriptTypeInt(script) == TXOUT_SCRIPT_P2SH:
            haveP2SH = True
            break
         
      if not haveP2SH:
         return getAddr(newAddr, 'P2PKH')
      
      #is our Tx SW?
      if WITNESS == True and self.coinSelection.isSW():
         return getAddr(newAddr, 'P2SH-P2WPKH')
      else:
         return getAddr(newAddr, 'P2SH-P2PK')
      

   #############################################################################
   def determineChangeScript(self, utxoList, scriptValPairs, peek=False):
      changeScript = ''
      changeAddrStr = ''
      changeAddr160 = ''

      selectedBehavior = 'NewAddr' if self.lbox is None else 'Feedback'
      
      if not self.main.usermode == USERMODE.Expert or \
         not self.chkDefaultChangeAddr.isChecked():
         # Default behavior for regular wallets is 'NewAddr', but for lockboxes
         # the default behavior is "Feedback" (send back to the original addr
         if self.lbox is None:
            changeAddrStr = self.getDefaultChangeAddress(scriptValPairs, peek)
            changeAddr160 = addrStr_to_hash160(changeAddrStr)[1]
            changeScript  = scrAddr_to_script(addrStr_to_scrAddr(changeAddrStr))
            self.wlt.setComment(changeAddr160, CHANGE_ADDR_DESCR_STRING)
         else:
            changeScript  = script_to_p2sh_script(self.lbox.binScript)

      if self.main.usermode == USERMODE.Expert:
         if not self.chkDefaultChangeAddr.isChecked():
            self.main.setWltSetting(self.wltID, 'ChangeBehavior', selectedBehavior)
         else:
            if self.radioFeedback.isChecked():
               selectedBehavior = 'Feedback'
               changeScript = utxoList[0].getScript()
            elif self.radioSpecify.isChecked():
               selectedBehavior = 'Specify'
               changeScript = self.getUserChangeScript()['Script']
               if changeScript is None:
                  QMessageBox.warning(self, self.tr('Invalid Address'), self.tr("""
                     You specified an invalid change address for this 
                     transcation."""), QMessageBox.Ok)
                  return None
               scrType = getTxOutScriptType(changeScript)
               if scrType in CPP_TXOUT_HAS_ADDRSTR:
                  changeAddrStr = script_to_addrStr(changeScript)
               elif scrType==CPP_TXOUT_MULTISIG:
                  scrP2SH = script_to_p2sh_script(changeScript)
                  changeAddrStr = script_to_addrStr(scrP2SH)

      if self.main.usermode == USERMODE.Expert and self.chkRememberChng.isChecked():
         self.main.setWltSetting(self.wltID, 'ChangeBehavior', selectedBehavior)
         if selectedBehavior == 'Specify' and len(changeAddrStr) > 0:
            self.main.setWltSetting(self.wltID, 'ChangeAddr', changeAddrStr)
      else:
         self.main.setWltSetting(self.wltID, 'ChangeBehavior', 'NewAddr')

      return changeScript,selectedBehavior

   #####################################################################
   def setMaximum(self, targWidget):
      nRecip = len(self.widgetTable)
      totalOther = 0
      r = 0
      try:
         bal = self.getUsableBalance()
         txFee, fee_byte, adjust = self.feeDialog.getFeeData()
         while r < nRecip:
            # Use while loop so 'r' is still in scope in the except-clause
            if targWidget == self.widgetTable[r]['QLE_AMT']:
               r += 1
               continue
         
            amtStr = str(self.widgetTable[r]['QLE_AMT'].text()).strip()
            if len(amtStr) > 0:
               totalOther += str2coin(amtStr)
            r += 1
                     
         if txFee == 0 and fee_byte != 0:
            if self.customUtxoList != None and len(self.customUtxoList) > 0:
               serializedUtxoList = self.serializeUtxoList(self.customUtxoList)
               txFee = self.coinSelection.getFeeForMaxValUtxoVector(serializedUtxoList, fee_byte)
            else:
               txFee = self.coinSelection.getFeeForMaxVal(fee_byte)

      except:
         QMessageBox.warning(self, self.tr('Invalid Input'), \
               self.tr('Cannot compute the maximum amount '
               'because there is an error in the amount '
               'for recipient %1.').arg(r + 1,), QMessageBox.Ok)
         return



      maxStr = coin2str((bal - (txFee + totalOther)), maxZeros=0)
      if bal < txFee + totalOther:
         QMessageBox.warning(self, self.tr('Insufficient funds'), \
               self.tr('You have specified more than your spendable balance to '
               'the other recipients and the transaction fee.  Therefore, the '
               'maximum amount for this recipient would actually be negative.'), \
               QMessageBox.Ok)
         return

      targWidget.setText(maxStr.strip())
      self.isMax = True


   #####################################################################
   def createSetMaxButton(self, targWidget):
      newBtn = QPushButton('MAX')
      newBtn.setMaximumWidth(relaxedSizeStr(self, 'MAX')[0])
      newBtn.setToolTip(self.tr('Fills in the maximum spendable amount minus '
                         'the amounts specified for other recipients '
                         'and the transaction fee '))
      funcSetMax = lambda:  self.setMaximum(targWidget)
      self.connect(newBtn, SIGNAL(CLICKED), funcSetMax)
      return newBtn


   #####################################################################
   def makeRecipFrame(self, nRecip):
      prevNRecip = len(self.widgetTable)
      nRecip = max(nRecip, 1)
      inputs = []
      for i in range(nRecip):
         if i < prevNRecip and i < nRecip:
            inputs.append([])
            for widg in ['QLE_ADDR', 'QLE_AMT', 'QLE_COMM']: 
               inputs[-1].append(str(self.widgetTable[i][widg].text()))


      frmRecip = QFrame()
      frmRecip.setFrameStyle(QFrame.NoFrame)
      frmRecipLayout = QVBoxLayout()


      def recipientAddrChanged(row):
         def callbk():
            self.updateAddrColor(row, Colors.Background)
            self.updateCoinSelectionRecipient(row)
         return callbk
      
      def recipientValueChanged(row):
         def callbk():
            self.updateCoinSelectionRecipient(row)
         return callbk
         

      self.widgetTable = []
      for r in range(nRecip):
         self.widgetTable.append({})

         self.widgetTable[r]['LBL_ADDR'] = QLabel('Address %d:' % (r+1))

         addrEntryWidgets = self.main.createAddressEntryWidgets(self, maxDetectLen=45, boldDetectParts=1)
         self.widgetTable[r]['FUNC_GETSCRIPT'] = addrEntryWidgets['CALLBACK_GETSCRIPT']
         self.widgetTable[r]['QLE_ADDR'] = addrEntryWidgets['QLE_ADDR']
         self.widgetTable[r]['QLE_ADDR'].setMinimumWidth(relaxedSizeNChar(GETFONT('var'), 20)[0])
         self.widgetTable[r]['QLE_ADDR'].setMaximumHeight(self.maxHeight)
         self.widgetTable[r]['QLE_ADDR'].setFont(GETFONT('var', 9))

         self.connect(self.widgetTable[r]['QLE_ADDR'], SIGNAL('textChanged(QString)'), 
                                                        recipientAddrChanged(r))

         self.widgetTable[r]['BTN_BOOK'] = addrEntryWidgets['BTN_BOOK']
         self.widgetTable[r]['LBL_DETECT'] = addrEntryWidgets['LBL_DETECT']

         self.widgetTable[r]['LBL_AMT'] = QLabel('Amount:')
         self.widgetTable[r]['QLE_AMT'] = QLineEdit()
         self.widgetTable[r]['QLE_AMT'].setFont(GETFONT('Fixed'))
         self.widgetTable[r]['QLE_AMT'].setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 14)[0])
         self.widgetTable[r]['QLE_AMT'].setMaximumHeight(self.maxHeight)
         self.widgetTable[r]['QLE_AMT'].setAlignment(Qt.AlignLeft)

         self.connect(self.widgetTable[r]['QLE_AMT'], SIGNAL('textChanged(QString)'),
                                                      recipientValueChanged(r))

         self.widgetTable[r]['LBL_BTC'] = QLabel('BTC')
         self.widgetTable[r]['LBL_BTC'].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

         self.widgetTable[r]['BTN_MAX'] = \
                           self.createSetMaxButton(self.widgetTable[r]['QLE_AMT'])

         self.widgetTable[r]['LBL_COMM'] = QLabel('Comment:')
         self.widgetTable[r]['QLE_COMM'] = QLineEdit()
         self.widgetTable[r]['QLE_COMM'].setFont(GETFONT('var', 9))
         self.widgetTable[r]['QLE_COMM'].setMaximumHeight(self.maxHeight)
         self.widgetTable[r]['QLE_COMM'].setMaxLength(MAX_COMMENT_LENGTH)

         if r < nRecip and r < prevNRecip:
            self.widgetTable[r]['QLE_ADDR'].setText(inputs[r][0])
            self.widgetTable[r]['QLE_AMT'].setText(inputs[r][1])
            self.widgetTable[r]['QLE_COMM'].setText(inputs[r][2])

         subfrm = QFrame()
         subfrm.setFrameStyle(STYLE_RAISED)
         subLayout = QGridLayout()
         subLayout.addWidget(self.widgetTable[r]['LBL_ADDR'],  0,0, 1,1)
         subLayout.addWidget(self.widgetTable[r]['QLE_ADDR'],  0,1, 1,5)
         subLayout.addWidget(self.widgetTable[r]['BTN_BOOK'],  0,6, 1,1)

         subLayout.addWidget(self.widgetTable[r]['LBL_DETECT'], 1,1, 1,6)

         subLayout.addWidget(self.widgetTable[r]['LBL_AMT'],   2,0, 1,1)
         subLayout.addWidget(self.widgetTable[r]['QLE_AMT'],   2,1, 1,2)
         subLayout.addWidget(self.widgetTable[r]['LBL_BTC'],   2,3, 1,1)
         subLayout.addWidget(self.widgetTable[r]['BTN_MAX'],   2,4, 1,1)
         subLayout.addWidget(QLabel(''), 2, 5, 1, 2)

         subLayout.addWidget(self.widgetTable[r]['LBL_COMM'],  3,0, 1,1)
         subLayout.addWidget(self.widgetTable[r]['QLE_COMM'],  3,1, 1,6)
         subLayout.setContentsMargins(5, 5, 5, 5)
         subLayout.setSpacing(3)
         subfrm.setLayout(subLayout)

         frmRecipLayout.addWidget(subfrm)


      btnFrm = QFrame()
      btnFrm.setFrameStyle(QFrame.NoFrame)
      btnLayout = QHBoxLayout()
      lbtnAddRecip = QLabelButton(self.tr('+ Recipient'))
      lbtnAddRecip.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lbtnRmRecip = QLabelButton(self.tr('- Recipient'))
      lbtnRmRecip.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      self.connect(lbtnAddRecip, SIGNAL(CLICKED), lambda: self.makeRecipFrame(nRecip + 1))
      self.connect(lbtnRmRecip, SIGNAL(CLICKED), lambda: self.makeRecipFrame(nRecip - 1))
      btnLayout.addStretch()
      btnLayout.addWidget(lbtnAddRecip)
      btnLayout.addWidget(lbtnRmRecip)
      btnFrm.setLayout(btnLayout)

      frmRecipLayout.addWidget(btnFrm)
      frmRecipLayout.addStretch()
      frmRecip.setLayout(frmRecipLayout)
      # return frmRecip
      self.scrollRecipArea.setWidget(frmRecip)
      self.scrollRecipArea.setWidgetResizable(True)

   #############################################################################
   def clickEnterURI(self):
      dlg = DlgUriCopyAndPaste(self.parent(), self.main)
      dlg.exec_()

      if len(dlg.uriDict) > 0:
         lastIsEmpty = True
         for widg in ['QLE_ADDR', 'QLE_AMT', 'QLE_COMM']: 
            if len(str(self.widgetTable[-1][widg].text())) > 0:
               lastIsEmpty = False

         if not lastIsEmpty:
            self.makeRecipFrame(len(self.widgetTable) + 1)

         self.widgetTable[-1]['QLE_ADDR'].setText(dlg.uriDict['address'])
         if dlg.uriDict.has_key('amount'):
            amtStr = coin2str(dlg.uriDict['amount'], maxZeros=1).strip()
            self.widgetTable[-1]['QLE_AMT'].setText(amtStr)


         haveLbl = dlg.uriDict.has_key('label')
         haveMsg = dlg.uriDict.has_key('message')

         dispComment = ''
         if haveLbl and haveMsg:
            dispComment = dlg.uriDict['label'] + ': ' + dlg.uriDict['message']
         elif not haveLbl and haveMsg:
            dispComment = dlg.uriDict['message']
         elif haveLbl and not haveMsg:
            dispComment = dlg.uriDict['label']

         self.widgetTable[-1]['QLE_COMM'].setText(dispComment)

      
   #############################################################################
   def toggleSpecify(self, b):
      self.lblChangeAddr.setVisible(b)
      self.edtChangeAddr.setVisible(b)
      self.btnChangeAddr.setVisible(b)
      self.lblAutoDetect.setVisible(b)

   #############################################################################
   def toggleChngAddr(self, b):
      self.radioFeedback.setVisible(b)
      self.radioSpecify.setVisible(b)
      self.ttipFeedback.setVisible(b)
      self.ttipSpecify.setVisible(b)
      self.chkRememberChng.setVisible(b)
      self.lblAutoDetect.setVisible(b)
      self.vertLine.setVisible(b)
      if not self.radioFeedback.isChecked() and not self.radioSpecify.isChecked():
         self.radioFeedback.setChecked(True)
      self.toggleSpecify(b and self.radioSpecify.isChecked())


   #############################################################################
   def updateAddrColor(self, idx, color):
      palette = QPalette()
      palette.setColor(QPalette.Base, color)
      self.widgetTable[idx]['QLE_ADDR'].setPalette(palette);
      self.widgetTable[idx]['QLE_ADDR'].setAutoFillBackground(True);
    
   #############################################################################   
   def previewTx(self):
      ustx = self.validateInputsGetUSTX(peek=True)
      if not isinstance(ustx, UnsignedTransaction):
         return
      
      txDlg = DlgDispTxInfo(ustx, self.wlt, self.parent(), self.main)
      txDlg.exec_()
      

################################################################################
class ReviewOfflineTxFrame(ArmoryDialog):
   def __init__(self, parent=None, main=None, initLabel=''):
      super(ReviewOfflineTxFrame, self).__init__(parent, main)

      self.ustx = None
      self.wlt = None
      self.lblDescr = QRichLabel('')

      ttipDataIsSafe = self.main.createToolTipWidget(\
         self.tr('There is no security-sensitive information in this data below, so '
         'it is perfectly safe to copy-and-paste it into an '
         'email message, or save it to a borrowed USB key.'))

      btnSave = QPushButton(self.tr('Save as file...'))
      self.connect(btnSave, SIGNAL(CLICKED), self.doSaveFile)
      ttipSave = self.main.createToolTipWidget(\
         self.tr('Save this data to a USB key or other device, to be transferred to '
         'a computer that contains the private keys for this wallet.'))

      btnCopy = QPushButton(self.tr('Copy to clipboard'))
      self.connect(btnCopy, SIGNAL(CLICKED), self.copyAsciiUSTX)
      self.lblCopied = QRichLabel('  ')
      self.lblCopied.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      ttipCopy = self.main.createToolTipWidget(\
         self.tr('Copy the transaction data to the clipboard, so that it can be '
         'pasted into an email or a text document.'))

      lblInstruct = QRichLabel(self.tr('<b>Instructions for completing this transaction:</b>'))
      self.lblUTX = QRichLabel('')

      frmUTX = makeLayoutFrame(HORIZONTAL, [ttipDataIsSafe, self.lblUTX])
      frmUpper = makeLayoutFrame(HORIZONTAL, [self.lblDescr], STYLE_SUNKEN)

      # Wow, I just cannot get the txtEdits to be the right size without
      # forcing them very explicitly
      self.txtUSTX = QTextEdit()
      self.txtUSTX.setFont(GETFONT('Fixed', 8))
      w,h = relaxedSizeNChar(self.txtUSTX, 68)[0], int(12 * 8.2)
      self.txtUSTX.setMinimumWidth(w)
      self.txtUSTX.setMinimumHeight(h)
      self.txtUSTX.setReadOnly(True)



      frmLower = QFrame()
      frmLower.setFrameStyle(STYLE_RAISED)
      frmLowerLayout = QGridLayout()

      frmLowerLayout.addWidget(frmUTX, 0, 0, 1, 3)
      frmLowerLayout.addWidget(self.txtUSTX, 1, 0, 3, 1)
      frmLowerLayout.addWidget(btnSave, 1, 1, 1, 1)
      frmLowerLayout.addWidget(ttipSave, 1, 2, 1, 1)
      frmLowerLayout.addWidget(btnCopy, 2, 1, 1, 1)
      frmLowerLayout.addWidget(ttipCopy, 2, 2, 1, 1)
      frmLowerLayout.addWidget(self.lblCopied, 3, 1, 1, 2)
      frmLowerLayout.setColumnStretch(0, 1)
      frmLowerLayout.setColumnStretch(1, 0)
      frmLowerLayout.setColumnStretch(2, 0)
      frmLowerLayout.setColumnStretch(3, 0)
      frmLowerLayout.setRowStretch(0, 0)
      frmLowerLayout.setRowStretch(1, 1)
      frmLowerLayout.setRowStretch(2, 1)
      frmLowerLayout.setRowStretch(3, 1)

      frmLower.setLayout(frmLowerLayout)


      frmAll = makeLayoutFrame(VERTICAL, [lblInstruct, \
                                        frmUpper, \
                                        'Space(5)', \
                                        frmLower])
      frmAll.layout().setStretch(0, 0)
      frmAll.layout().setStretch(1, 0)
      frmAll.layout().setStretch(2, 0)
      frmAll.layout().setStretch(3, 2)
      frmAll.layout().setStretch(4, 1)
      frmAll.layout().setStretch(5, 0)

      dlgLayout = QVBoxLayout()
      dlgLayout.addWidget(frmAll)

      self.setLayout(dlgLayout)
   
   def setUSTX(self, ustx):
      self.ustx = ustx
      self.lblUTX.setText(self.tr('<b>Transaction Data</b> \t (Unsigned ID: %1)').arg(ustx.uniqueIDB58))
      self.txtUSTX.setText(ustx.serializeAscii())
   
   def setWallet(self, wlt):
      self.wlt = wlt
      if determineWalletType(wlt, self.main)[0] in \
                                 [ WLTTYPES.Offline, WLTTYPES.WatchOnly ]:
         self.lblDescr.setText(self.tr("""
            The block of data shown below is the complete transaction you 
            just requested, but is invalid because it does not contain any
            signatures.  You must take this data to the computer with the 
            full wallet to get it signed, then bring it back here to be
            broadcast to the Bitcoin network.
            <br><br>
            Use "Save as file..." to save an <i>*.unsigned.tx</i> 
            file to USB drive or other removable media.  
            On the offline computer, click "Offline Transactions" on the main 
            window.  Load the transaction, <b>review it</b>, then sign it 
            (the filename now end with <i>*.signed.tx</i>).  Click "Continue" 
            below when you have the signed transaction on this computer.  
            <br><br>
            <b>NOTE:</b> The USB drive only ever holds public transaction
            data that will be broadcast to the network.  This data may be 
            considered privacy-sensitive, but does <u>not</u> compromise
            the security of your wallet."""))
      else:
         self.lblDescr.setText(self.tr("""
            You have chosen to create the previous transaction but not sign 
            it or broadcast it, yet.  You can save the unsigned 
            transaction to file, or copy&paste from the text box.  
            You can use the following window (after clicking "Continue") to 
            sign and broadcast the transaction when you are ready"""))
           
         
   def copyAsciiUSTX(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.txtUSTX.toPlainText())
      self.lblCopied.setText('<i>Copied!</i>')

   def doSaveFile(self):
      """ Save the Unsigned-Tx block of data """
      dpid = self.ustx.uniqueIDB58
      suffix = ('' if OS_WINDOWS else '.unsigned.tx')
      toSave = self.main.getFileSave(\
                      'Save Unsigned Transaction', \
                      ['Armory Transactions (*.unsigned.tx)'], \
                      'armory_%s_%s' % (dpid, suffix))
      LOGINFO('Saving unsigned tx file: %s', toSave)
      try:
         theFile = open(toSave, 'w')
         theFile.write(self.txtUSTX.toPlainText())
         theFile.close()
      except IOError:
         LOGEXCEPT('Failed to save file: %s', toSave)
         pass

################################################################################
class SignBroadcastOfflineTxFrame(ArmoryFrame):
   """
   We will make the assumption that this Frame is used ONLY for outgoing
   transactions from your wallet.  This simplifies the logic if we don't
   have to identify input senders/values, and handle the cases where those
   may not be specified
   """
   def __init__(self, parent=None, main=None, initLabel=''):
      super(SignBroadcastOfflineTxFrame, self).__init__(parent, main)

      self.wlt = None
      self.sentToSelfWarn = False
      self.fileLoaded = None

      lblDescr = QRichLabel(self.tr(
         'Copy or load a transaction from file into the text box below.  '
         'If the transaction is unsigned and you have the correct wallet, '
         'you will have the opportunity to sign it.  If it is already signed '
         'you will have the opportunity to broadcast it to '
         'the Bitcoin network to make it final.'))

      self.txtUSTX = QTextEdit()
      self.txtUSTX.setFont(GETFONT('Fixed', 8))
      w,h = relaxedSizeNChar(self.txtUSTX, 68)
      #self.txtUSTX.sizeHint = lambda: QSize(w, h)
      self.txtUSTX.setMinimumWidth(w)
      self.txtUSTX.setMinimumHeight(8*h)
      self.txtUSTX.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

      self.btnSign = QPushButton(self.tr('Sign'))
      self.btnBroadcast = QPushButton(self.tr('Broadcast'))
      self.btnSave = QPushButton(self.tr('Save file...'))
      self.btnLoad = QPushButton(self.tr('Load file...'))
      self.btnCopy = QPushButton(self.tr('Copy Text'))
      self.btnCopyHex = QPushButton(self.tr('Copy Raw Tx (Hex)'))
      self.lblCopied = QRichLabel('')
      self.lblCopied.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      self.btnSign.setEnabled(False)
      self.btnBroadcast.setEnabled(False)

      self.connect(self.txtUSTX, SIGNAL('textChanged()'), self.processUSTX)


      self.connect(self.btnSign, SIGNAL(CLICKED), self.signTx)
      self.connect(self.btnBroadcast, SIGNAL(CLICKED), self.broadTx)
      self.connect(self.btnSave, SIGNAL(CLICKED), self.saveTx)
      self.connect(self.btnLoad, SIGNAL(CLICKED), self.loadTx)
      self.connect(self.btnCopy, SIGNAL(CLICKED), self.copyTx)
      self.connect(self.btnCopyHex, SIGNAL(CLICKED), self.copyTxHex)

      self.lblStatus = QRichLabel('')
      self.lblStatus.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      wStat, hStat = relaxedSizeStr(self.lblStatus, self.tr('Signature is Invalid!'))
      self.lblStatus.setMinimumWidth(int(wStat * 1.2))
      self.lblStatus.setMinimumHeight(int(hStat * 1.2))


      frmDescr = makeLayoutFrame(HORIZONTAL, [lblDescr], STYLE_RAISED)

      self.infoLbls = []

      # ##
      self.infoLbls.append([])
      self.infoLbls[-1].append(self.main.createToolTipWidget(\
            self.tr('This is wallet from which the offline transaction spends bitcoins')))
      self.infoLbls[-1].append(QRichLabel('<b>Wallet:</b>'))
      self.infoLbls[-1].append(QRichLabel(''))

      # ##
      self.infoLbls.append([])
      self.infoLbls[-1].append(self.main.createToolTipWidget(self.tr('The name of the wallet')))
      self.infoLbls[-1].append(QRichLabel(self.tr('<b>Wallet Label:</b>')))
      self.infoLbls[-1].append(QRichLabel(''))

      # ##
      self.infoLbls.append([])
      self.infoLbls[-1].append(self.main.createToolTipWidget(self.tr(
         'A unique string that identifies an <i>unsigned</i> transaction.  '
         'This is different than the ID that the transaction will have when '
         'it is finally broadcast, because the broadcast ID cannot be '
         'calculated without all the signatures')))
      self.infoLbls[-1].append(QRichLabel(self.tr('<b>Pre-Broadcast ID:</b>')))
      self.infoLbls[-1].append(QRichLabel(''))

      # ##
      self.infoLbls.append([])
      self.infoLbls[-1].append(self.main.createToolTipWidget(\
                               self.tr('Net effect on this wallet\'s balance')))
      self.infoLbls[-1].append(QRichLabel(self.tr('<b>Transaction Amount:</b>')))
      self.infoLbls[-1].append(QRichLabel(''))

      self.moreInfo = QLabelButton(self.tr('Click here for more<br> information about <br>this transaction'))
      self.connect(self.moreInfo, SIGNAL(CLICKED), self.execMoreTxInfo)
      frmMoreInfo = makeLayoutFrame(HORIZONTAL, [self.moreInfo], STYLE_SUNKEN)
      frmMoreInfo.setMinimumHeight(tightSizeStr(self.moreInfo, 'Any String')[1] * 5)

      expert = (self.main.usermode == USERMODE.Expert)
      frmBtn = makeLayoutFrame(VERTICAL, [ self.btnSign, \
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
            frmInfoLayout.addWidget(self.infoLbls[r][c], r, c, 1, 1)

      frmInfo = QFrame()
      frmInfo.setFrameStyle(STYLE_SUNKEN)
      frmInfo.setLayout(frmInfoLayout)

      frmBottom = QFrame()
      frmBottom.setFrameStyle(STYLE_SUNKEN)
      frmBottomLayout = QGridLayout()
      frmBottomLayout.addWidget(self.txtUSTX, 0, 0, 1, 1)
      frmBottomLayout.addWidget(frmBtn, 0, 1, 2, 1)
      frmBottomLayout.addWidget(frmInfo, 1, 0, 1, 1)
      # frmBottomLayout.addWidget(frmMoreInfo,   1,1,  1,1)
      frmBottom.setLayout(frmBottomLayout)

      layout = QVBoxLayout()
      layout.addWidget(frmDescr)
      layout.addWidget(frmBottom)

      self.setLayout(layout)
      self.processUSTX()

   def processUSTX(self):
      # TODO:  it wouldn't be TOO hard to modify this dialog to take
      #        arbitrary hex-serialized transactions for broadcast...
      #        but it's not trivial either (for instance, I assume
      #        that we have inputs values, etc)
      self.wlt = None
      self.leValue = None
      self.ustxObj = None
      self.idxSelf = []
      self.idxOther = []
      self.lblStatus.setText('')
      self.lblCopied.setText('')
      self.enoughSigs = False
      self.sigsValid = False
      self.ustxReadable = False

      ustxStr = str(self.txtUSTX.toPlainText())
      if len(ustxStr) > 0:
         try:
            self.ustxObj = UnsignedTransaction().unserializeAscii(ustxStr)
            self.signStat = self.ustxObj.evaluateSigningStatus()
            self.enoughSigs = self.signStat.canBroadcast
            self.sigsValid = self.ustxObj.verifySigsAllInputs()
            self.ustxReadable = True
         except BadAddressError:
            QMessageBox.critical(self, self.tr('Inconsistent Data!'), \
               self.tr('This transaction contains inconsistent information.  This '
               'is probably not your fault...'), QMessageBox.Ok)
            self.ustxObj = None
            self.ustxReadable = False
         except NetworkIDError:
            QMessageBox.critical(self, self.tr('Wrong Network!'), \
               self.tr('This transaction is actually for a different network!  '
               'Did you load the correct transaction?'), QMessageBox.Ok)
            self.ustxObj = None
            self.ustxReadable = False
         except (UnserializeError, IndexError, ValueError):
            self.ustxObj = None
            self.ustxReadable = False

         if not self.enoughSigs or not self.sigsValid or not self.ustxReadable:
            self.btnBroadcast.setEnabled(False)
         else:
            if self.main.netMode == NETWORKMODE.Full:
               self.btnBroadcast.setEnabled(True)
            else:
               self.btnBroadcast.setEnabled(False)
               self.btnBroadcast.setToolTip(self.tr('No connection to Bitcoin network!'))
      else:
         self.ustxObj = None
         self.ustxReadable = False
         self.btnBroadcast.setEnabled(False)
         

      self.btnSave.setEnabled(True)
      self.btnCopyHex.setEnabled(False)
      if not self.ustxReadable:
         if len(ustxStr) > 0:
            self.lblStatus.setText(self.tr('<b><font color="red">Unrecognized!</font></b>'))
         else:
            self.lblStatus.setText('')
         self.btnSign.setEnabled(False)
         self.btnBroadcast.setEnabled(False)
         self.btnSave.setEnabled(False)
         self.makeReviewFrame()
         return
      elif not self.enoughSigs:
         if not self.main.getSettingOrSetDefault('DNAA_ReviewOfflineTx', False):
            result = MsgBoxWithDNAA(self, self.main, MSGBOX.Warning, title=self.tr('Offline Warning'), \
                  msg=self.tr('<b>Please review your transaction carefully before '
                  'signing and broadcasting it!</b>  The extra security of '
                  'using offline wallets is lost if you do '
                  'not confirm the transaction is correct!'), dnaaMsg=None)
            self.main.writeSetting('DNAA_ReviewOfflineTx', result[1])
         self.lblStatus.setText(self.tr('<b><font color="red">Unsigned</font></b>'))
         self.btnSign.setEnabled(True)
         self.btnBroadcast.setEnabled(False)
      elif not self.sigsValid:
         self.lblStatus.setText(self.tr('<b><font color="red">Bad Signature!</font></b>'))
         self.btnSign.setEnabled(True)
         self.btnBroadcast.setEnabled(False)
      else:
         self.lblStatus.setText(self.tr('<b><font color="green">All Signatures Valid!</font></b>'))
         self.btnSign.setEnabled(False)
         self.btnCopyHex.setEnabled(True)


      # NOTE:  We assume this is an OUTGOING transaction.  When I pull in the
      #        multi-sig code, I will have to either make a different dialog,
      #        or add some logic to this one
      FIELDS = enum('Hash', 'OutList', 'SumOut', 'InList', 'SumIn', 'Time', 'Blk', 'Idx')
      data = extractTxInfo(self.ustxObj, -1)

      # Collect the input wallets (hopefully just one of them)
      fromWlts = set()
      for scrAddr, amt, a, b, c, script in data[FIELDS.InList]:
         wltID = self.main.getWalletForAddr160(scrAddr[1:])
         if not wltID == '':
            fromWlts.add(wltID)

      if len(fromWlts) > 1:
         QMessageBox.warning(self, self.tr('Multiple Input Wallets'), \
            self.tr('Somehow, you have obtained a transaction that actually pulls from more '
            'than one wallet.  The support for handling multi-wallet signatures is '
            'not currently implemented (this also could have happened if you imported '
            'the same private key into two different wallets).') , QMessageBox.Ok)
         self.makeReviewFrame()
         return
      elif len(fromWlts) == 0:
         QMessageBox.warning(self, self.tr('Unrelated Transaction'), \
            self.tr('This transaction appears to have no relationship to any of the wallets '
            'stored on this computer.  Did you load the correct transaction?'), \
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
      for scrType, amt, binScript, multiSigList in data[FIELDS.OutList]:
         recip = script_to_scrAddr(binScript)
         try:
            wltID = self.main.getWalletForAddr160(CheckHash160(recip))
         except BadAddressError:
            wltID = ''
            
         if wltID == spendWltID:
            toWlts.add(wltID)
            myOutSum += amt
            self.idxSelf.append(idx)
         else:
            rvPairs.append([recip, amt])
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
      # ##
      if self.ustxObj == None:
         self.infoLbls[0][2].setText('')
         self.infoLbls[1][2].setText('')
         self.infoLbls[2][2].setText('')
         self.infoLbls[3][2].setText('')
      else:
         ##### 0

         ##### 1
         if self.wlt:
            self.infoLbls[0][2].setText(self.wlt.uniqueIDB58)
            self.infoLbls[1][2].setText(self.wlt.labelName)
         else:
            self.infoLbls[0][2].setText(self.tr('[[ Unrelated ]]'))
            self.infoLbls[1][2].setText('')

         ##### 2
         self.infoLbls[2][2].setText(self.ustxObj.uniqueIDB58)

         ##### 3
         if self.leValue:
            self.infoLbls[3][2].setText(coin2strNZS(self.leValue) + '  BTC')
         else:
            self.infoLbls[3][2].setText('')

         self.moreInfo.setVisible(True)

   def execMoreTxInfo(self):

      if not self.ustxObj:
         self.processUSTX()

      if not self.ustxObj:
         QMessageBox.warning(self, self.tr('Invalid Transaction'), \
            self.tr('Transaction data is invalid and cannot be shown!'), QMessageBox.Ok)
         return

      leVal = 0 if self.leValue is None else -self.leValue
      dlgTxInfo = DlgDispTxInfo(self.ustxObj, self.wlt, self.parent(), self.main, \
                          precomputeIdxGray=self.idxSelf, precomputeAmt=leVal, txtime=-1)
      dlgTxInfo.exec_()



   def signTx(self):
      if not self.ustxObj:
         QMessageBox.critical(self, self.tr('Cannot Sign'), \
               self.tr('This transaction is not relevant to any of your wallets.'
               'Did you load the correct transaction?'), QMessageBox.Ok)
         return

      if self.ustxObj == None:
         QMessageBox.warning(self, self.tr('Not Signable'), \
               self.tr('This is not a valid transaction, and thus it cannot '
               'be signed. '), QMessageBox.Ok)
         return
      elif self.enoughSigs and self.sigsValid:
         QMessageBox.warning(self, self.tr('Already Signed'), \
               self.tr('This transaction has already been signed!'), QMessageBox.Ok)
         return


      if self.wlt and self.wlt.watchingOnly:
         QMessageBox.warning(self, self.tr('No Private Keys!'), \
            self.tr('This transaction refers one of your wallets, but that wallet '
            'is a watching-only wallet.  Therefore, private keys are '
            'not available to sign this transaction.'), \
             QMessageBox.Ok)
         return


      # We should provide the same confirmation dialog here, as we do when
      # sending a regular (online) transaction.  But the DlgConfirmSend was
      # not really designed
      ustx = self.ustxObj
      svpairs = []
      svpairsMine = []
      theFee = ustx.calculateFee()
      for scrType,value,script,msInfo in ustx.pytxObj.makeRecipientsList():
         svpairs.append([script, value])
         if scrType in CPP_TXOUT_STDSINGLESIG:
            addrStr = script_to_addrStr(script)
            if self.wlt.hasAddr(addrStr_to_hash160(addrStr)[1]):
               svpairsMine.append([script, value])

      if len(svpairsMine) == 0 and len(svpairs) > 1:
         QMessageBox.warning(self, self.tr('Missing Change'), self.tr("""
            This transaction has %1 recipients, and none of them
            are addresses in this wallet (for receiving change).  
            This can happen if you specified a custom change address 
            for this transaction, or sometimes happens solely by 
            chance with a multi-recipient transaction.  It could also 
            be the result of someone tampering with the transaction. 
            <br><br>The transaction is valid and ready to be signed.  
            Please verify the recipient and amounts carefully before 
            confirming the transaction on the next screen.""").arg(len(svpairs)), QMessageBox.Ok)

      dlg = DlgConfirmSend(self.wlt, svpairs, theFee, self, self.main, pytxOrUstx=ustx)
      if not dlg.exec_():
         return



      if self.wlt.useEncryption and self.wlt.isLocked:
         Passphrase = None  

         unlockdlg = DlgUnlockWallet(self.wlt, self, self.main, self.tr('Send Transaction'), returnPassphrase=True)
         if unlockdlg.exec_():
            if unlockdlg.Accepted == 1:
               Passphrase = unlockdlg.securePassphrase.copy()
               unlockdlg.securePassphrase.destroy()
                     
         if Passphrase is None or self.wlt.kdf is None:
            QMessageBox.critical(self.parent(), self.tr('Wallet is Locked'), \
               self.tr('Cannot sign transaction while your wallet is locked. '), \
               QMessageBox.Ok)
            return
         else:
            self.wlt.kdfKey = self.wlt.kdf.DeriveKey(Passphrase)
            Passphrase.destroy()                                              

      newUstx = self.wlt.signUnsignedTx(self.ustxObj)
      self.wlt.advanceHighestIndex()
      self.txtUSTX.setText(newUstx.serializeAscii())
      self.ustxObj = newUstx

      if not self.fileLoaded == None:
         self.saveTxAuto()


   def broadTx(self):
      if self.main.netMode == NETWORKMODE.Disconnected:
         QMessageBox.warning(self, self.tr('No Internet!'), \
            self.tr('Armory lost its connection to Bitcoin Core, and cannot '
            'broadcast any transactions until it is reconnected. '
            'Please verify that Bitcoin Core (or bitcoind) is open '
            'and synchronized with the network.'), QMessageBox.Ok)
         return
      elif self.main.netMode == NETWORKMODE.Offline:
         QMessageBox.warning(self, self.tr('No Internet!'), \
            self.tr('You do not currently have a connection to the Bitcoin network. '
            'If this does not seem correct, verify that  is open '
            'and synchronized with the network.'), QMessageBox.Ok)
         return



      try:
         finalTx = self.ustxObj.getSignedPyTx()
      except SignatureError:
         QMessageBox.warning(self, self.tr('Signature Error'), self.tr("""
            Not all signatures are valid.  This transaction
            cannot be broadcast."""), QMessageBox.Ok)
      except:
         QMessageBox.warning(self, self.tr('Error'), self.tr("""
            There was an error processing this transaction, for reasons 
            that are probably not your fault..."""), QMessageBox.Ok)
         return

      # We should provide the same confirmation dialog here, as we do when
      # sending a regular (online) transaction.  But the DlgConfirmSend was
      # not really designed
      ustx = self.ustxObj
      svpairs = [[r[2],r[1]] for r in ustx.pytxObj.makeRecipientsList()]
      theFee = ustx.calculateFee()

      doIt = True
      if self.wlt:
         dlg = DlgConfirmSend(self.wlt, svpairs, theFee, self, self.main, 
                                          sendNow=True, pytxOrUstx=ustx)
         doIt = dlg.exec_()

      if doIt:
         self.main.broadcastTransaction(finalTx)
         if self.fileLoaded and os.path.exists(self.fileLoaded):
            try:
               # pcs = self.fileLoaded.split('.')
               # newFileName = '.'.join(pcs[:-2]) + '.DONE.' + '.'.join(pcs[-2:])
               shutil.move(self.fileLoaded, self.fileLoaded.replace('signed', 'SENT'))
            except:
               QMessageBox.critical(self, self.tr('File Remove Error'), \
                  self.tr('The file could not be deleted.  If you want to delete '
                  'it, please do so manually.  The file was loaded from: '
                  '<br><br>%1: ').arg(self.fileLoaded), QMessageBox.Ok)

         try:
            self.parent().accept()
         except:
            # This just attempts to close the OfflineReview&Sign window.  If 
            # it fails, the user can close it themselves.
            LOGEXCEPT('Could not close/accept parent dialog.')            


   def saveTxAuto(self):
      if not self.ustxReadable:
         QMessageBox.warning(self, self.tr('Formatting Error'), \
            self.tr('The transaction data was not in a format recognized by '
            'Armory.'))
         return


      if not self.fileLoaded == None and self.enoughSigs and self.sigsValid:
         newSaveFile = self.fileLoaded.replace('unsigned', 'signed')
         LOGINFO('New save file: %s' % newSaveFile)
         f = open(newSaveFile, 'w')
         f.write(str(self.txtUSTX.toPlainText()))
         f.close()
         if not newSaveFile == self.fileLoaded:
            os.remove(self.fileLoaded)
         self.fileLoaded = newSaveFile
         QMessageBox.information(self, self.tr('Transaction Saved!'), \
            self.tr('Your transaction has been saved to the following location:'
            '\n\n%1\n\nIt can now be broadcast from any computer running '
            'Armory in online mode.').arg(newSaveFile), QMessageBox.Ok)
         return

   def saveTx(self):
      if not self.ustxReadable:
         QMessageBox.warning(self, self.tr('Formatting Error'), \
            self.tr('The transaction data was not in a format recognized by '
            'Armory.'))
         return


      # The strange windows branching is because PyQt in Windows automatically
      # adds the ffilter suffix to the default filename, where as it needs to
      # be explicitly added in PyQt in Linux.  Not sure why this behavior exists.
      defaultFilename = ''
      if not self.ustxObj == None:
         if self.enoughSigs and self.sigsValid:
            suffix = '' if OS_WINDOWS else '.signed.tx'
            defaultFilename = 'armory_%s_%s' % (self.ustxObj.uniqueIDB58, suffix)
            ffilt = 'Transactions (*.signed.tx *.unsigned.tx)'
         else:
            suffix = '' if OS_WINDOWS else '.unsigned.tx'
            defaultFilename = 'armory_%s_%s' % (self.ustxObj.uniqueIDB58, suffix)
            ffilt = 'Transactions (*.unsigned.tx *.signed.tx)'
      filename = self.main.getFileSave('Save Transaction', \
                             [ffilt], \
                             defaultFilename)
      if len(str(filename)) > 0:
         LOGINFO('Saving transaction file: %s', filename)
         f = open(filename, 'w')
         f.write(str(self.txtUSTX.toPlainText()))
         f.close()


   def loadTx(self):
      filename = self.main.getFileLoad(self.tr('Load Transaction'), \
                    ['Transactions (*.signed.tx *.unsigned.tx *.SENT.tx)'])

      if len(str(filename)) > 0:
         LOGINFO('Selected transaction file to load: %s', filename)
         f = open(filename, 'r')
         self.txtUSTX.setText(f.read())
         f.close()
         self.fileLoaded = filename


   def copyTx(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(self.txtUSTX.toPlainText()))
      self.lblCopied.setText(self.tr('<i>Copied!</i>'))


   def copyTxHex(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(binary_to_hex(self.ustxObj.getSignedPyTx().serialize()))
      self.lblCopied.setText(self.tr('<i>Copied!</i>'))
         

# Need to put circular imports at the end of the script to avoid an import deadlock
from qtdialogs import CLICKED, DlgConfirmSend, DlgUriCopyAndPaste, \
         DlgUnlockWallet, extractTxInfo, DlgDispTxInfo, NO_CHANGE, STRETCH


