################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

from PyQt4.Qt import * #@UnusedWildImport
from PyQt4.QtGui import * #@UnusedWildImport

from armoryengine.BDM import TheBDM
from qtdefines import * #@UnusedWildImport
from armoryengine.Transaction import PyTxDistProposal
from armoryengine.CoinSelection import PySelectCoins, calcMinSuggestedFees,\
   PyUnspentTxOut
from ui.WalletFrames import SelectWalletFrame
 

class SendBitcoinsFrame(ArmoryFrame):
   COLS = enum('LblAddr', 'Addr', 'AddrBook', 'LblWltID', 'LblAmt', 'Btc', \
               'LblUnit', 'BtnMax', 'LblComm', 'Comm')
   def __init__(self, parent, main, initLabel='',
                 wlt=None, prefill=None, wltIDList=None,
                 selectWltCallback = None, onlyOfflineWallets=False,
                 sendCallback = None, createUnsignedTxCallback = None):
      super(SendBitcoinsFrame, self).__init__(parent, main)
      self.maxHeight = tightSizeNChar(GETFONT('var'), 1)[1] + 8
      self.sourceAddrList = None
      self.altBalance = None
      self.wlt = wlt
      self.wltID = wlt.uniqueIDB58 if wlt else None
      self.wltIDList = wltIDList
      self.selectWltCallback = selectWltCallback
      self.sendCallback = sendCallback
      self.createUnsignedTxCallback = createUnsignedTxCallback
      self.onlyOfflineWallets = onlyOfflineWallets
      txFee = self.main.getSettingOrSetDefault('Default_Fee', MIN_TX_FEE)
      self.widgetTable = []
      self.scrollRecipArea = QScrollArea()
      lblRecip = QRichLabel('<b>Enter Recipients:</b>')
      lblRecip.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

      self.freeOfErrors = True

      feetip = self.main.createToolTipWidget(\
            'Transaction fees go to users who contribute computing power to '
            'keep the Bitcoin network secure, and in return they get your transaction '
            'included in the blockchain faster.  <b>Most transactions '
            'do not require a fee</b> but it is recommended anyway '
            'since it guarantees quick processing and helps the network.')

      self.edtFeeAmt = QLineEdit()
      self.edtFeeAmt.setFont(GETFONT('Fixed'))
      self.edtFeeAmt.setMinimumWidth(tightSizeNChar(self.edtFeeAmt, 6)[0])
      self.edtFeeAmt.setMaximumWidth(tightSizeNChar(self.edtFeeAmt, 12)[0])
      self.edtFeeAmt.setMaximumHeight(self.maxHeight)
      self.edtFeeAmt.setAlignment(Qt.AlignRight)
      self.edtFeeAmt.setText(coin2str(txFee, maxZeros=1).strip())

      # Created a standard wallet chooser frame. Pass the call back method
      # for when the user selects a wallet.
      coinControlCallback = self.coinControlUpdate if self.main.usermode == USERMODE.Expert else None
      self.walletSelector = SelectWalletFrame(parent, main, VERTICAL, self.wltID, \
                  wltIDList=self.wltIDList, selectWltCallback=self.setWallet, \
                  coinControlCallback=coinControlCallback, onlyOfflineWallets=self.onlyOfflineWallets)

      componentList = [ QLabel('Fee:'), \
                        self.edtFeeAmt, \
                        feetip, \
                        STRETCH]
      # Only the Create  Unsigned Transaction button if there is a callback for it.
      # Otherwise the containing dialog or wizard will provide the offlien tx button
      if self.createUnsignedTxCallback:
         self.ttipUnsigned = self.main.createToolTipWidget(\
            'Check this box to create an unsigned transaction to be signed and/or broadcast later.')
         self.unsignedCheckbox = QCheckBox('Create Unsigned')
         self.connect(self.unsignedCheckbox, SIGNAL(CLICKED), self.unsignedCheckBoxUpdate)
         frmUnsigned = makeHorizFrame([self.unsignedCheckbox, self.ttipUnsigned])
         componentList.append(frmUnsigned)
      
      # Only add the Send Button if there's a callback for it
      # Otherwise the containing dialog or wizard will provide the send button
      if self.sendCallback:
         self.btnSend = QPushButton('Send!')
         self.connect(self.btnSend, SIGNAL(CLICKED), self.createTxAndBroadcast)
         componentList.append(self.btnSend)
         
      txFrm = makeLayoutFrame(HORIZONTAL, componentList)

      btnEnterURI = QPushButton('Manually Enter "bitcoin:" Link')
      ttipEnterURI = self.main.createToolTipWidget(\
         'Armory does not always succeed at registering itself to handle '
         'URL links from webpages and email.  '
         'Click this button to copy a link directly into Armory')
      self.connect(btnEnterURI, SIGNAL("clicked()"), self.clickEnterURI)
      fromFrameList = [self.walletSelector]
      if not USE_TESTNET:
         btnDonate = QPushButton("Donate to Armory Developers!")
         ttipDonate = self.main.createToolTipWidget(\
            'Making this software was a lot of work.  You can give back '
            'by adding a small donation to go to the Armory developers.  '
            'You will have the ability to change the donation amount '
            'before finalizing the transaction.')
         self.connect(btnDonate, SIGNAL("clicked()"), self.addDonation)
         frmDonate = makeHorizFrame([btnDonate, ttipDonate])
         fromFrameList.append(frmDonate)

      if not self.main.usermode == USERMODE.Standard:
         frmEnterURI = makeHorizFrame([btnEnterURI, ttipEnterURI])
         fromFrameList.append(frmEnterURI)

      ########################################################################
      # In Expert usermode, allow the user to modify source addresses
      if self.main.usermode == USERMODE.Expert:
         self.chkDefaultChangeAddr = QCheckBox('Use an existing address for change')
         self.radioFeedback = QRadioButton('Send change to first input address')
         self.radioSpecify = QRadioButton('Specify a change address')
         self.lblChangeAddr = QRichLabel('Send Change To:')
         self.edtChangeAddr = QLineEdit()
         self.btnChangeAddr = createAddrBookButton(parent, self.edtChangeAddr, \
                                       None, 'Send change to')
         self.chkRememberChng = QCheckBox('Remember for future transactions')
         self.vertLine = VLINE()

         self.ttipSendChange = self.main.createToolTipWidget(\
               'Most transactions end up with oversized inputs and Armory will send '
               'the change to the next address in this wallet.  You may change this '
               'behavior by checking this box.')
         self.ttipFeedback = self.main.createToolTipWidget(\
               'Guarantees that no new addresses will be created to receive '
               'change. This reduces anonymity, but is useful if you '
               'created this wallet solely for managing imported addresses, '
               'and want to keep all funds within existing addresses.')
         self.ttipSpecify = self.main.createToolTipWidget(\
               'You can specify any valid Bitcoin address for the change.  '
               '<b>NOTE:</b> If the address you specify is not in this wallet, '
               'Armory will not be able to distinguish the outputs when it shows '
               'up in your ledger.  The change will look like a second recipient, '
               'and the total debit to your wallet will be equal to the amount '
               'you sent to the recipient <b>plus</b> the change.')


         # Make sure that there can only be one selection
         btngrp = QButtonGroup(self)
         btngrp.addButton(self.radioFeedback)
         btngrp.addButton(self.radioSpecify)
         btngrp.setExclusive(True)
         self.connect(self.chkDefaultChangeAddr, SIGNAL('toggled(bool)'), self.toggleChngAddr)
         self.connect(self.radioSpecify, SIGNAL('toggled(bool)'), self.toggleSpecify)
         frmChngLayout = QGridLayout()
         i = 0;
         frmChngLayout.addWidget(self.chkDefaultChangeAddr, i, 0, 1, 6)
         frmChngLayout.addWidget(self.ttipSendChange, i, 6, 1, 2)
         i += 1
         frmChngLayout.addWidget(self.radioFeedback, i, 1, 1, 5)
         frmChngLayout.addWidget(self.ttipFeedback, i, 6, 1, 2)
         i += 1
         frmChngLayout.addWidget(self.radioSpecify, i, 1, 1, 5)
         frmChngLayout.addWidget(self.ttipSpecify, i, 6, 1, 2)
         i += 1
         sendChangeToFrame = makeHorizFrame([self.lblChangeAddr,
                                            self.edtChangeAddr,
                                            self.btnChangeAddr])
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
         fromFrameList.append(STRETCH)
         fromFrameList.append(frmChangeAddr)
      else:
         fromFrameList.append(STRETCH)
      frmBottomLeft = makeVertFrame(fromFrameList, STYLE_RAISED)

      lblSend = QRichLabel('<b>Sending from Wallet:</b>')
      lblSend.setAlignment(Qt.AlignLeft | Qt.AlignBottom)


      leftFrame = makeVertFrame([lblSend, frmBottomLeft])
      rightFrame = makeVertFrame([lblRecip, self.scrollRecipArea, txFrm])
      layout = QHBoxLayout()
      layout.addWidget(leftFrame)
      layout.addWidget(rightFrame)
      self.setLayout(layout)

      self.makeRecipFrame(1)
      self.setWindowTitle('Send Bitcoins')
      self.setMinimumHeight(self.maxHeight * 20)
      # self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

      loadCount = self.main.settings.get('Load_Count')
      alreadyDonated = self.main.getSettingOrSetDefault('DonateAlready', False)
      lastPestering = self.main.getSettingOrSetDefault('DonateLastPester', 0)
      donateFreq = self.main.getSettingOrSetDefault('DonateFreq', 20)
      dnaaDonate = self.main.getSettingOrSetDefault('DonateDNAA', False)


      if prefill:
         get = lambda s: prefill[s] if prefill.has_key(s) else ''
         atype, addr160 = addrStr_to_hash160(get('address'))
         amount = get('amount')
         message = get('message')
         label = get('label')
         self.addOneRecipient(addr160, amount, message, label)

      elif not self.main == None and loadCount % donateFreq == (donateFreq - 1) and \
         not loadCount == lastPestering and not dnaaDonate:
         result = MsgBoxWithDNAA(MSGBOX.Question, 'Please donate!', \
            '<i>Armory</i> is the result of over 3,000 hours of development '
            'and dozens of late nights bug-hunting and testing.  Yet, this software '
            'has been given to you for free to benefit the greater Bitcoin '
            'community! '
            '<br><br>However, continued development may not be possible without '
            'donations.  If you are satisfied with this software, please consider '
            'donating what you think this software would be worth as a commercial '
            'application.'
            '<br><br><b>Are you willing to donate to the Armory developers?</b> If you '
            'select "Yes," a donation field will be added to your '
            'next transaction.  You will have the opportunity to remove or change '
            'the amount before sending the transaction.', None)
         self.main.writeSetting('DonateLastPester', loadCount)

         if result[0] == True:
            self.addDonation()
            self.makeRecipFrame(2)

         if result[1] == True:
            self.main.writeSetting('DonateDNAA', True)

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
      self.walletSelector.updateOnWalletChange()
      self.unsignedCheckBoxUpdate()


   #############################################################################
   def unsignedCheckBoxUpdate(self):
      if self.unsignedCheckbox.isChecked():
         self.btnSend.setText('Continue')
         self.btnSend.setToolTip('Click to create an unsigned transaction!')
      else:
         self.btnSend.setText('Send!')
         self.btnSend.setToolTip('Click to send bitcoins!')
      

   #############################################################################
   def addOneRecipient(self, addr160, amt, msg, label=''):
      if len(label) > 0:
         self.wlt.setComment(addr160, label)

      COLS = self.COLS
      lastIsEmpty = True
      for col in (COLS.Addr, COLS.Btc, COLS.Comm):
         if len(str(self.widgetTable[-1][col].text())) > 0:
            lastIsEmpty = False

      if not lastIsEmpty:
         self.makeRecipFrame(len(self.widgetTable) + 1)

      if amt:
         amt = coin2str(amt, maxZeros=2).strip()

      self.widgetTable[-1][self.COLS.Addr].setText(hash160_to_addrStr(addr160))
      self.widgetTable[-1][self.COLS.Addr].setCursorPosition(0)
      self.widgetTable[-1][self.COLS.Btc].setText(amt)
      self.widgetTable[-1][self.COLS.Btc].setCursorPosition(0)
      self.widgetTable[-1][self.COLS.Comm].setText(msg)
      self.widgetTable[-1][self.COLS.Comm].setCursorPosition(0)

   #############################################################################
   # Now that the wallet can change in the context of the send dialog, this
   # method is used as a callback for when the wallet changes
   # isDoubleClick is unused - do not accept or close dialog on double click
   def setWallet(self, wlt, isDoubleClick=False):
      self.wlt = wlt
      self.wltID = wlt.uniqueIDB58 if wlt else None
      if not TheBDM.getBDMState() == 'BlockchainReady':
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
   # Update the available source address list and balance based on results from
   # coin control. This callback is now necessary because coin control was moved
   # to the Select Wallet Frame
   def coinControlUpdate(self, sourceAddrList, altBalance):
      self.sourceAddrList = sourceAddrList
      self.altBalance = altBalance

   #############################################################################
   def validateInputsGetTxDP(self):
      COLS = self.COLS
      self.freeOfErrors = True
      scrAddrs = []
      addrList = []
      self.comments = []
      for i in range(len(self.widgetTable)):
         # Verify validity of address strings
         addrStr = str(self.widgetTable[i][COLS.Addr].text()).strip()
         self.widgetTable[i][COLS.Addr].setText(addrStr) # overwrite w/ stripped
         addrIsValid = True
         addrList.append(addrStr)
         try:
            # The addrStr_to_scrAddr method fails if not reg Addr, or P2SH
            scrAddrs.append(addrStr_to_scrAddr(addrStr))
         except:
            addrIsValid = False
            scrAddrs.append('')
            self.freeOfErrors = False
            self.updateAddrField(i, COLS.Addr, Colors.SlightRed)


      numChkFail = sum([1 if len(b)==0 else 0 for b in scrAddrs])
      if not self.freeOfErrors:
         QMessageBox.critical(self, tr('Invalid Address'), tr("""
           You have entered %d invalid @{address|addresses}@.  
           The @{error has|errors have}@ been highlighted on the 
           entry screen.""", numChkFail, numChkFail), QMessageBox.Ok)

         for i in range(len(self.widgetTable)):
            try:
               atype, a160 = addrStr_to_hash160(addrList[i]) 
               if atype == -1 or not atype in [ADDRBYTE,P2SHBYTE]:
                  net = 'Unknown Network'
                  if NETWORKS.has_key(addrList[i][0]):
                     net = NETWORKS[addrList[i][0]]
                  QMessageBox.warning(self, tr('Wrong Network!'), tr("""
                     Address %d is for the wrong network!  You are on the <b>%s</b>
                     and the address you supplied is for the the <b>%s</b>!""") % \
                     (i+1, NETWORKS[ADDRBYTE], net), QMessageBox.Ok)
            except:
               pass

         return False

      # Construct recipValuePairs and check that all metrics check out
      scraddrValuePairs = []
      totalSend = 0
      for i in range(len(self.widgetTable)):
         try:
            recipStr = str(self.widgetTable[i][COLS.Addr].text()).strip()
            valueStr = str(self.widgetTable[i][COLS.Btc].text()).strip()
            value = str2coin(valueStr, negAllowed=False)
            if value == 0:
               QMessageBox.critical(self, 'Zero Amount', \
                  'You cannot send 0 BTC to any recipients.  <br>Please enter '
                  'a positive amount for recipient %d.' % (i + 1), QMessageBox.Ok)
               return False

         except NegativeValueError:
            QMessageBox.critical(self, 'Negative Value', \
               'You have specified a negative amount for recipient %d. <br>Only '
               'positive values are allowed!.' % (i + 1), QMessageBox.Ok)
            return False
         except TooMuchPrecisionError:
            QMessageBox.critical(self, 'Too much precision', \
               'Bitcoins can only be specified down to 8 decimal places. '
               'The smallest value that can be sent is  0.0000 0001 BTC. '
               'Please enter a new amount for recipient %d.' % (i + 1), QMessageBox.Ok)
            return False
         except ValueError:
            QMessageBox.critical(self, 'Missing recipient amount', \
               'You did not specify an amount to send!', QMessageBox.Ok)
            return False
         except:
            QMessageBox.critical(self, 'Invalid Value String', \
               'The amount you specified '
               'to send to address %d is invalid (%s).' % (i + 1, valueStr), QMessageBox.Ok)
            LOGERROR('Invalid amount specified: "%s"', valueStr)
            return False

         totalSend += value
         scraddr = addrStr_to_scrAddr(recipStr)

         scraddrValuePairs.append((scraddr, value))
         self.comments.append((str(self.widgetTable[i][COLS.Comm].text()), value))

      try:
         feeStr = str(self.edtFeeAmt.text())
         fee = str2coin(feeStr, negAllowed=False)
      except NegativeValueError:
         QMessageBox.critical(self, tr('Negative Value'), tr("""
            You must enter a positive value for the fee."""), QMessageBox.Ok)
         return False
      except TooMuchPrecisionError:
         QMessageBox.critical(self, tr('Too much precision'), tr("""
            Bitcoins can only be specified down to 8 decimal places. 
            The smallest unit of a Bitcoin is 0.0000 0001 BTC. 
            Please enter a fee of at least 0.0000 0001"""), QMessageBox.Ok)
         return False
      except:
         QMessageBox.critical(self, tr('Invalid Fee String'), tr("""
            The fee you specified is invalid.  A standard fee is 
            0.0001 BTC, though some transactions may succeed with 
            zero fee."""), QMessageBox.Ok)
         LOGERROR(tr('Invalid fee specified: "%s"') % feeStr)
         return False


      bal = self.getUsableBalance()
      if totalSend + fee > bal:
         valTry = coin2str(totalSend + fee, maxZeros=2).strip()
         valMax = coin2str(bal, maxZeros=2).strip()
         if self.altBalance == None:
            QMessageBox.critical(self, tr('Insufficient Funds'), tr("""
            You just tried to send %s BTC, including fee, but you only 
            have %s BTC (spendable) in this wallet!""") % \
            (valTry, valMax), QMessageBox.Ok)
         else:
            QMessageBox.critical(self, tr('Insufficient Funds'), tr("""
            You just tried to send %s BTC, including fee, but you only 
            have %s BTC with this coin control selection!""") % \
            (valTry, valMax), QMessageBox.Ok)
         return False

      # Iteratively calculate the minimum fee by first trying the user selected
      # fee then on each iteration set the feeTry to the minFee, and see if the 
      # new feeTry can cover the original amount plus the new minfee.  This loop
      # will rarely iterate. It will only iterate when there is enough dust in 
      # utxoList so that each fee increase causes enough dust to be used to 
      # increase the fee yet again.  Also, for the loop to iterate, the 
      # totalSend + fee must be close to the bal, but not go over when the min 
      # fee is increased If it does go over, it will exit the loop on the
      # last condition,and give the user an insufficient balance warning.
      minFee = None
      utxoSelect = []
      feeTry = fee
      while minFee is None or (feeTry < minFee and totalSend + minFee <= bal):
         if minFee:
            feeTry = minFee
         utxoList = self.getUsableTxOutList()
         utxoSelect = PySelectCoins(utxoList, totalSend, feeTry)
         minFee = calcMinSuggestedFees(utxoSelect, totalSend, feeTry, len(scraddrValuePairs))[1]


      # We now have a min-fee that we know we can match if the user agrees
      if fee < minFee:

         usrFeeStr = coin2strNZS(fee)
         minFeeStr = coin2strNZS(minFee)
         newBalStr = coin2strNZS(bal - minFee)

         if totalSend + minFee > bal:
            # Need to adjust this based on overrideMin flag
            self.edtFeeAmt.setText(coin2str(minFee, maxZeros=1).strip())
            QMessageBox.warning(self, tr('Insufficient Balance'), tr("""
               The required transaction fee causes this transaction to exceed 
               your balance.  In order to send this transaction, you will be 
               required to pay a fee of <b>%s BTC</b>. 
               <br><br>
               Please go back and adjust the value of your transaction, not 
               to exceed a total of <b>%s BTC</b> (the necessary fee has 
               been entered into the form, so you can use the "MAX" button 
               to enter the remaining balance for a recipient).""") % \
               (minFeeStr, newBalStr), QMessageBox.Ok)
            return

         reply = QMessageBox.warning(self, tr('Insufficient Fee'), tr("""
            The fee you have specified (%s BTC) is insufficient for the 
            size and priority of your transaction.  You must include at 
            least %s BTC to send this transaction. 
            <br><br> 
            Do you agree to the fee of %s BTC?""") % \
            (usrFeeStr, minFeeStr, minFeeStr), \
            QMessageBox.Yes | QMessageBox.Cancel)

         if reply == QMessageBox.Cancel:
            return False
         if reply == QMessageBox.No:
            pass
         elif reply == QMessageBox.Yes:
            fee = long(minFee)


      # Warn user of excessive fee specified
      if fee > 100*MIN_RELAY_TX_FEE or (minFee > 0 and fee > 10*minFee):
         reply = QMessageBox.warning(self, tr('Excessive Fee'), tr("""
            You have specified a fee of <b>%s BTC</b> which is much higher
            than the minimum fee required for this transaction: <b>%s BTC</b>.
            Are you <i>absolutely sure</i> that you want to send with this
            fee?  
            <br><br>
            If you do not want this fee, click "No" and then change the fee
            at the bottom of the "Send Bitcoins" window before trying 
            again.""") % (fee, minFee), QMessageBox.Yes | QMessageBox.No)

         if not reply==QMessageBox.Yes:
            return False


      if len(utxoSelect) == 0:
         QMessageBox.critical(self, tr('Coin Selection Error'), tr("""
            There was an error constructing your transaction, due to a 
            quirk in the way Bitcoin transactions work.  If you see this
            error more than once, try sending your BTC in two or more 
            separate transactions."""), QMessageBox.Ok)
         return False

      # ## IF we got here, everything is good to go...
      #   Just need to get a change address and then construct the tx
      totalTxSelect = sum([u.getValue() for u in utxoSelect])
      totalChange = totalTxSelect - (totalSend + fee)

      self.origSVPairs = list(scraddrValuePairs) # copy
      self.changeScrAddr = ''
      self.selectedBehavior = ''
      if totalChange > 0:
         self.changeScrAddr = self.determineChangeAddr(utxoSelect)
         LOGINFO('Change address behavior: %s', self.selectedBehavior)
         if not self.changeScrAddr:
            return False
         scraddrValuePairs.append([self.changeScrAddr, totalChange])
      else:
         if self.main.usermode == USERMODE.Expert and \
            self.chkDefaultChangeAddr.isChecked():
            self.selectedBehavior = NO_CHANGE
      
      changePair = None
      if len(self.selectedBehavior) > 0:
         changePair = (self.changeScrAddr, self.selectedBehavior)

      # Anonymize the outputs
      random.shuffle(scraddrValuePairs)

      # Convert all scrAddrs to scripts for creation
      recipPairs = [[scrAddr_to_script(s),v] for s,v in scraddrValuePairs]

      # Now create the unsigned TxDP
      txdp = PyTxDistProposal().createFromTxOutSelection(utxoSelect, recipPairs)

      txValues = [totalSend, fee, totalChange]
      if not self.unsignedCheckbox.isChecked():
         dlg = DlgConfirmSend(self.wlt, self.origSVPairs, txValues[1], self, \
                                                      self.main, True, changePair)
   
         if not dlg.exec_():
            return False
      
      return txdp
   
  
   def createTxAndBroadcast(self):
      # The Send! button is clicked validate and broadcast tx
      txdp = self.validateInputsGetTxDP()
      if txdp:
         if self.createUnsignedTxCallback and self.unsignedCheckbox.isChecked():
            self.createUnsignedTxCallback(txdp)
         else:
            try:
               if self.wlt.isLocked:
                  Passphrase = None  
                  
                  unlockdlg = DlgUnlockWallet(self.wlt, self, self.main, 'Send Transaction', returnPassphrase=True)
                  if unlockdlg.exec_():
                     if unlockdlg.Accepted == 1:
                        Passphrase = unlockdlg.securePassphrase.copy()
                        unlockdlg.securePassphrase.destroy()
                     
                  if Passphrase is None or self.wlt.kdf is None:
                     QMessageBox.critical(self.parent(), 'Wallet is Locked', \
                        'Cannot sign transaction while your wallet is locked. ', \
                        QMessageBox.Ok)
                     return
                  else:
                     self.wlt.kdfKey = self.wlt.kdf.DeriveKey(Passphrase)
                     Passphrase.destroy()                                     
               
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
      
      
               tx = self.wlt.signTxDistProposal(txdp)
               finalTx = tx.prepareFinalTx()
               if len(commentStr) > 0:
                  self.wlt.setComment(finalTx.getHash(), commentStr)
               self.main.broadcastTransaction(finalTx)
               TheBDM.saveScrAddrHistories()
            except:
               LOGEXCEPT('Problem sending transaction!')
               # TODO: not sure what errors to catch here, yet...
               raise
            if self.sendCallback:
               self.sendCallback()

   #############################################################################
   def getUsableBalance(self):
      if self.altBalance == None:
         return self.wlt.getBalance('Spendable')
      else:
         return self.altBalance


   #############################################################################
   def getUsableTxOutList(self):
      if self.altBalance == None:
         return list(self.wlt.getTxOutList('Spendable'))
      else:
         utxoList = []
         for a160 in self.sourceAddrList:
            # Trying to avoid a swig bug involving iteration over vector<> types
            utxos = self.wlt.getAddrTxOutList(a160)
            for i in range(len(utxos)):
               utxos[i].pprintOneLine(290000)
               utxoList.append(PyUnspentTxOut().createFromCppUtxo(utxos[i]))
         return utxoList


   #############################################################################
   def determineChangeAddr(self, utxoList):
      changeAddrStr = ''
      changeAddr160 = ''
      changeScrAddr = ''
      self.selectedBehavior = 'NewAddr'
      addrStr = ''
      if not self.main.usermode == USERMODE.Expert:
         changeAddrStr = self.wlt.getNextUnusedAddress().getAddrStr()
         changeAddr160 = addrStr_to_hash160(changeAddrStr)[1]
         changeScrAddr = addrStr_to_scrAddr(changeAddrStr)
         self.wlt.setComment(changeAddr160, CHANGE_ADDR_DESCR_STRING)
      else:
         if not self.chkDefaultChangeAddr.isChecked():
            changeAddrStr = self.wlt.getNextUnusedAddress().getAddrStr()
            changeAddr160 = addrStr_to_hash160(changeAddrStr)[1]
            changeScrAddr = addrStr_to_scrAddr(changeAddrStr)
            self.wlt.setComment(changeAddr160, CHANGE_ADDR_DESCR_STRING)
            # If generate new address, remove previously-remembered behavior
            self.main.setWltSetting(self.wltID, 'ChangeBehavior', self.selectedBehavior)
         else:
            if self.radioFeedback.isChecked():
               changeScrAddr = utxoList[0].getRecipientScrAddr()
               self.selectedBehavior = 'Feedback'
            elif self.radioSpecify.isChecked():
               addrStr = str(self.edtChangeAddr.text()).strip()
               if not checkAddrStrValid(addrStr):
                  QMessageBox.warning(self, tr('Invalid Address'), tr("""
                     You specified an invalid change address for this 
                     transcation."""), QMessageBox.Ok)
                  return '', False
               changeScrAddr = addrStr_to_scrAddr(addrStr)
               if addrStr_to_hash160(addrStr)[0]==P2SHBYTE:
                  LOGWARN('P2SH address used in change output')
               self.selectedBehavior = 'Specify'

      if self.main.usermode == USERMODE.Expert and self.chkRememberChng.isChecked():
         self.main.setWltSetting(self.wltID, 'ChangeBehavior', self.selectedBehavior)
         if self.selectedBehavior == 'Specify' and len(addrStr) > 0:
            self.main.setWltSetting(self.wltID, 'ChangeAddr', addrStr)
      else:
         self.main.setWltSetting(self.wltID, 'ChangeBehavior', 'NewAddr')

      return changeScrAddr

   #####################################################################
   def setMaximum(self, targWidget):
      nRecip = len(self.widgetTable)
      totalOther = 0
      r = 0
      try:
         bal = self.getUsableBalance()
         txFee = str2coin(str(self.edtFeeAmt.text()))
         while r < nRecip:
            # Use while loop so 'r' is still in scope in the except-clause
            if targWidget == self.widgetTable[r][self.COLS.Btc]:
               r += 1
               continue

            amtStr = str(self.widgetTable[r][self.COLS.Btc].text()).strip()
            if len(amtStr) > 0:
               totalOther += str2coin(amtStr)
            r += 1

      except:
         QMessageBox.warning(self, 'Invalid Input', \
               'Cannot compute the maximum amount '
               'because there is an error in the amount '
               'for recipient %d.' % (r + 1,), QMessageBox.Ok)
         return


      maxStr = coin2str((bal - (txFee + totalOther)), maxZeros=0)
      if bal < txFee + totalOther:
         QMessageBox.warning(self, 'Insufficient funds', \
               'You have specified more than your spendable balance to '
               'the other recipients and the transaction fee.  Therefore, the '
               'maximum amount for this recipient would actually be negative.', \
               QMessageBox.Ok)
         return

      targWidget.setText(maxStr.strip())


   #####################################################################
   def createSetMaxButton(self, targWidget):
      newBtn = QPushButton('MAX')
      newBtn.setMaximumWidth(relaxedSizeStr(self, 'MAX')[0])
      newBtn.setToolTip('<u></u>Fills in the maximum spendable amount minus '
                         'the amounts specified for other recipients '
                         'and the transaction fee ')
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
            for j in (self.COLS.Addr, self.COLS.Btc, self.COLS.Comm):
               inputs[-1].append(str(self.widgetTable[i][j].text()))


      frmRecip = QFrame()
      frmRecip.setFrameStyle(QFrame.NoFrame)
      frmRecipLayout = QVBoxLayout()

      COLS = self.COLS

      self.widgetTable = []
      for r in range(nRecip):
         self.widgetTable.append([])

         self.widgetTable[r].append(QLabel('Address %d:' % (r + 1,)))

         self.widgetTable[r].append(QLineEdit())
         self.widgetTable[r][-1].setMinimumWidth(relaxedSizeNChar(GETFONT('var'), 38)[0])
         self.widgetTable[r][-1].setMaximumHeight(self.maxHeight)
         self.widgetTable[r][-1].setFont(GETFONT('var', 9))

         # This is the hack of all hacks -- but I have no other way to make this work.
         # For some reason, the references on variable r are carrying over between loops
         # and all widgets are getting connected to the last one.  The only way I could
         # work around this was just ultra explicit garbage.  I'll pay 0.1 BTC to anyone
         # who figures out why my original code was failing...
         # idx = r+0
         # chgColor = lambda x: self.updateAddrField(idx, COLS.Addr, QColor(255,255,255))
         # self.connect(self.widgetTable[idx][-1], SIGNAL('textChanged(QString)'), chgColor)
         if r == 0:
            chgColor = lambda x: self.updateAddrField(0, COLS.Addr, QColor(255, 255, 255))
            self.connect(self.widgetTable[0][-1], SIGNAL('textChanged(QString)'), chgColor)
         elif r == 1:
            chgColor = lambda x: self.updateAddrField(1, COLS.Addr, QColor(255, 255, 255))
            self.connect(self.widgetTable[1][-1], SIGNAL('textChanged(QString)'), chgColor)
         elif r == 2:
            chgColor = lambda x: self.updateAddrField(2, COLS.Addr, QColor(255, 255, 255))
            self.connect(self.widgetTable[2][-1], SIGNAL('textChanged(QString)'), chgColor)
         elif r == 3:
            chgColor = lambda x: self.updateAddrField(3, COLS.Addr, QColor(255, 255, 255))
            self.connect(self.widgetTable[3][-1], SIGNAL('textChanged(QString)'), chgColor)
         elif r == 4:
            chgColor = lambda x: self.updateAddrField(4, COLS.Addr, QColor(255, 255, 255))
            self.connect(self.widgetTable[4][-1], SIGNAL('textChanged(QString)'), chgColor)


         addrEntryBox = self.widgetTable[r][-1]
         self.widgetTable[r].append(createAddrBookButton(self.parent(), addrEntryBox, \
                                      None, 'Send to'))


         self.widgetTable[r].append(QRichLabel(''))
         self.widgetTable[r][-1].setVisible(False)


         self.widgetTable[r].append(QLabel('Amount:'))

         self.widgetTable[r].append(QLineEdit())
         self.widgetTable[r][-1].setFont(GETFONT('Fixed'))
         self.widgetTable[r][-1].setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 14)[0])
         self.widgetTable[r][-1].setMaximumHeight(self.maxHeight)
         self.widgetTable[r][-1].setAlignment(Qt.AlignLeft)

         self.widgetTable[r].append(QLabel('BTC'))
         self.widgetTable[r][-1].setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

         # self.widgetTable[r].append( QPushButton('MAX') )
         # self.widgetTable[r][-1].setMaximumWidth( relaxedSizeStr(self, 'MAX')[0])
         # self.widgetTable[r][-1].setToolTip( \
                           # 'Fills in the maximum spendable amount minus amounts '
                           # 'specified for other recipients and the transaction fee ')
         # self.connect(self.widgetTable[r][-1], SIGNAL(CLICKED),  setMaxFunc)
         self.widgetTable[r].append(self.createSetMaxButton(self.widgetTable[r][COLS.Btc]))

         self.widgetTable[r].append(QLabel('Comment:'))
         self.widgetTable[r].append(QLineEdit())
         self.widgetTable[r][-1].setFont(GETFONT('var', 9))
         self.widgetTable[r][-1].setMaximumHeight(self.maxHeight)

         if r < nRecip and r < prevNRecip:
            self.widgetTable[r][COLS.Addr].setText(inputs[r][0])
            self.widgetTable[r][COLS.Btc ].setText(inputs[r][1])
            self.widgetTable[r][COLS.Comm].setText(inputs[r][2])

         subfrm = QFrame()
         subfrm.setFrameStyle(STYLE_RAISED)
         subLayout = QGridLayout()
         subLayout.addWidget(self.widgetTable[r][COLS.LblAddr], 0, 0, 1, 1)
         subLayout.addWidget(self.widgetTable[r][COLS.Addr], 0, 1, 1, 5)
         subLayout.addWidget(self.widgetTable[r][COLS.AddrBook], 0, 6, 1, 1)

         subLayout.addWidget(self.widgetTable[r][COLS.LblWltID], 1, 1, 1, 5)

         subLayout.addWidget(self.widgetTable[r][COLS.LblAmt], 2, 0, 1, 1)
         subLayout.addWidget(self.widgetTable[r][COLS.Btc], 2, 1, 1, 2)
         subLayout.addWidget(self.widgetTable[r][COLS.LblUnit], 2, 3, 1, 1)
         subLayout.addWidget(self.widgetTable[r][COLS.BtnMax], 2, 4, 1, 1)
         subLayout.addWidget(QLabel(''), 2, 5, 1, 2)

         subLayout.addWidget(self.widgetTable[r][COLS.LblComm], 3, 0, 1, 1)
         subLayout.addWidget(self.widgetTable[r][COLS.Comm], 3, 1, 1, 6)
         subLayout.setContentsMargins(15, 15, 15, 15)
         subLayout.setSpacing(3)
         subfrm.setLayout(subLayout)

         frmRecipLayout.addWidget(subfrm)


      btnFrm = QFrame()
      btnFrm.setFrameStyle(QFrame.NoFrame)
      btnLayout = QHBoxLayout()
      lbtnAddRecip = QLabelButton('+ Recipient')
      lbtnAddRecip.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      lbtnRmRecip = QLabelButton('- Recipient')
      lbtnRmRecip.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      self.connect(lbtnAddRecip, SIGNAL(CLICKED), lambda: self.makeRecipFrame(nRecip + 1))
      self.connect(lbtnRmRecip, SIGNAL(CLICKED), lambda: self.makeRecipFrame(nRecip - 1))
      btnLayout.addStretch()
      btnLayout.addWidget(lbtnAddRecip)
      btnLayout.addWidget(lbtnRmRecip)
      btnFrm.setLayout(btnLayout)

      # widgetsForWidth = [COLS.LblAddr, COLS.Addr, COLS.LblAmt, COLS.Btc]
      # minScrollWidth = sum([self.widgetTable[0][col].width() for col in widgetsForWidth])

      frmRecipLayout.addWidget(btnFrm)
      frmRecipLayout.addStretch()
      frmRecip.setLayout(frmRecipLayout)
      # return frmRecip
      self.scrollRecipArea.setWidget(frmRecip)


   #############################################################################
   def addDonation(self, amt=DONATION):
      COLS = self.COLS
      lastIsEmpty = True
      for col in (COLS.Addr, COLS.Btc, COLS.Comm):
         if len(str(self.widgetTable[-1][col].text())) > 0:
            lastIsEmpty = False

      if not lastIsEmpty:
         self.makeRecipFrame(len(self.widgetTable) + 1)

      self.widgetTable[-1][self.COLS.Addr].setText(ARMORY_DONATION_ADDR)
      self.widgetTable[-1][self.COLS.Btc].setText(coin2str(amt, maxZeros=2).strip())
      self.widgetTable[-1][self.COLS.Comm].setText(\
            'Donation to Armory developers.  Thank you for your generosity!')

   #############################################################################
   def clickEnterURI(self):
      dlg = DlgUriCopyAndPaste(self.parent(), self.main)
      dlg.exec_()

      if len(dlg.uriDict) > 0:
         COLS = self.COLS
         lastIsEmpty = True
         for col in (COLS.Addr, COLS.Btc, COLS.Comm):
            if len(str(self.widgetTable[-1][col].text())) > 0:
               lastIsEmpty = False

         if not lastIsEmpty:
            self.makeRecipFrame(len(self.widgetTable) + 1)

         self.widgetTable[-1][self.COLS.Addr].setText(dlg.uriDict['address'])
         if dlg.uriDict.has_key('amount'):
            amtStr = coin2str(dlg.uriDict['amount'], maxZeros=1).strip()
            self.widgetTable[-1][self.COLS.Btc].setText(amtStr)


         haveLbl = dlg.uriDict.has_key('label')
         haveMsg = dlg.uriDict.has_key('message')

         dispComment = ''
         if haveLbl and haveMsg:
            dispComment = dlg.uriDict['label'] + ': ' + dlg.uriDict['message']
         elif not haveLbl and haveMsg:
            dispComment = dlg.uriDict['message']
         elif haveLbl and not haveMsg:
            dispComment = dlg.uriDict['label']

         self.widgetTable[-1][self.COLS.Comm].setText(dispComment)

      
   #############################################################################
   def toggleSpecify(self, b):
      self.lblChangeAddr.setVisible(b)
      self.edtChangeAddr.setVisible(b)
      self.btnChangeAddr.setVisible(b)

   #############################################################################
   def toggleChngAddr(self, b):
      self.radioFeedback.setVisible(b)
      self.radioSpecify.setVisible(b)
      self.ttipFeedback.setVisible(b)
      self.ttipSpecify.setVisible(b)
      self.chkRememberChng.setVisible(b)
      self.vertLine.setVisible(b)
      if not self.radioFeedback.isChecked() and not self.radioSpecify.isChecked():
         self.radioFeedback.setChecked(True)
      self.toggleSpecify(b and self.radioSpecify.isChecked())


   #############################################################################
   def updateAddrField(self, idx, col, color):
      palette = QPalette()
      palette.setColor(QPalette.Base, color)
      self.widgetTable[idx][col].setPalette(palette);
      self.widgetTable[idx][col].setAutoFillBackground(True);
      try:
         addrtext = str(self.widgetTable[idx][self.COLS.Addr].text())
         wid = self.main.getWalletForAddr160(addrStr_to_hash160(addrtext)[1])
         if wid:
            wlt = self.main.walletMap[wid]
            dispStr = '%s (%s)' % (wlt.labelName, wlt.uniqueIDB58)
            self.widgetTable[idx][self.COLS.LblWltID].setVisible(True)
            self.widgetTable[idx][self.COLS.LblWltID].setText(dispStr, color='TextBlue')
         else:
            self.widgetTable[idx][self.COLS.LblWltID].setVisible(False)
      except:
         self.widgetTable[idx][self.COLS.LblWltID].setVisible(False)


class ReviewOfflineTxFrame(ArmoryDialog):
   def __init__(self, parent=None, main=None, initLabel=''):
      super(ReviewOfflineTxFrame, self).__init__(parent, main)

      self.txdp = None
      self.wlt = None
      self.lblDescr = QRichLabel('')

      ttipDataIsSafe = self.main.createToolTipWidget(\
         'There is no security-sensitive information in this data below, so '
         'it is perfectly safe to copy-and-paste it into an '
         'email message, or save it to a borrowed USB key.')

      btnSave = QPushButton('Save as file...')
      self.connect(btnSave, SIGNAL(CLICKED), self.doSaveFile)
      ttipSave = self.main.createToolTipWidget(\
         'Save this data to a USB key or other device, to be transferred to '
         'a computer that contains the private keys for this wallet.')

      btnCopy = QPushButton('Copy to clipboard')
      self.connect(btnCopy, SIGNAL(CLICKED), self.copyAsciiTxDP)
      self.lblCopied = QRichLabel('  ')
      self.lblCopied.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      ttipCopy = self.main.createToolTipWidget(\
         'Copy the transaction data to the clipboard, so that it can be '
         'pasted into an email or a text document.')

      lblInstruct = QRichLabel('<b>Instructions for completing this transaction:</b>')
      self.lblUTX = QRichLabel('')

      frmUTX = makeLayoutFrame(HORIZONTAL, [ttipDataIsSafe, self.lblUTX])
      frmUpper = makeLayoutFrame(HORIZONTAL, [self.lblDescr], STYLE_SUNKEN)

      # Wow, I just cannot get the txtEdits to be the right size without
      # forcing them very explicitly
      w, h = tightSizeStr(GETFONT('Fixed', 8), '0' * 93)[0], int(12 * 8.2)
      self.txtTxDP = QTextEdit()
      self.txtTxDP.setFont(GETFONT('Fixed', 8))
      self.txtTxDP.setMinimumWidth(w)
      self.txtTxDP.setMinimumHeight(h)
      self.txtTxDP.setReadOnly(True)



      frmLower = QFrame()
      frmLower.setFrameStyle(STYLE_RAISED)
      frmLowerLayout = QGridLayout()

      frmLowerLayout.addWidget(frmUTX, 0, 0, 1, 3)
      frmLowerLayout.addWidget(self.txtTxDP, 1, 0, 3, 1)
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
   
   def setTxDp(self, txdp):
      self.txdp = txdp
      self.lblUTX.setText('<b>Transaction Data</b> \t (Unsigned ID: %s)' % txdp.uniqueB58)
      self.txtTxDP.setText(txdp.serializeAscii())
   
   def setWallet(self, wlt):
      self.wlt = wlt
      if determineWalletType(wlt, self.main)[0] in \
                                 [ WLTTYPES.Offline, WLTTYPES.WatchOnly ]:
         self.lblDescr.setText(tr("""
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
         self.lblDescr.setText(tr("""
            You have chosen to create the previous transaction but not sign 
            it or broadcast it, yet.  You can save the unsigned 
            transaction to file, or copy&paste from the text box.  
            You can use the following window (after clicking "Continue") to 
            sign and broadcast the transaction when you are ready"""))
           
         
   def copyAsciiTxDP(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.txtTxDP.toPlainText())
      self.lblCopied.setText('<i>Copied!</i>')

   def doSaveFile(self):
      """ Save the Unsigned-Tx block of data """
      dpid = self.txdp.uniqueB58
      suffix = ('' if OS_WINDOWS else '.unsigned.tx')
      toSave = self.main.getFileSave(\
                      'Save Unsigned Transaction', \
                      ['Armory Transactions (*.unsigned.tx)'], \
                      'armory_%s_%s' % (dpid, suffix))
      # In windows, we get all these superfluous file suffixes
      toSave = toSave.replace('unsigned.tx.unsigned.tx', 'unsigned.tx')
      toSave = toSave.replace('unsigned.tx.unsigned.tx', 'unsigned.tx')
      LOGINFO('Saving unsigned tx file: %s', toSave)
      try:
         theFile = open(toSave, 'w')
         theFile.write(self.txtTxDP.toPlainText())
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

      lblDescr = QRichLabel(\
         'Copy or load a transaction from file into the text box below.  '
         'If the transaction is unsigned and you have the correct wallet, '
         'you will have the opportunity to sign it.  If it is already signed '
         'you will have the opportunity to broadcast it to '
         'the Bitcoin network to make it final.')

      w, h = tightSizeStr(GETFONT('Fixed', 8), '0' * 90)[0], int(12 * 8.2)
      self.txtTxDP = QTextEdit()
      self.txtTxDP.setFont(GETFONT('Fixed', 8))
      self.txtTxDP.sizeHint = lambda: QSize(w, h)
      self.txtTxDP.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

      self.btnSign = QPushButton('Sign')
      self.btnBroadcast = QPushButton('Broadcast')
      self.btnSave = QPushButton('Save file...')
      self.btnLoad = QPushButton('Load file...')
      self.btnCopy = QPushButton('Copy Text')
      self.btnCopyHex = QPushButton('Copy Final Tx (Hex)')
      self.lblCopied = QRichLabel('')
      self.lblCopied.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

      self.btnSign.setEnabled(False)
      self.btnBroadcast.setEnabled(False)

      self.connect(self.txtTxDP, SIGNAL('textChanged()'), self.processTxDP)


      self.connect(self.btnSign, SIGNAL(CLICKED), self.signTx)
      self.connect(self.btnBroadcast, SIGNAL(CLICKED), self.broadTx)
      self.connect(self.btnSave, SIGNAL(CLICKED), self.saveTx)
      self.connect(self.btnLoad, SIGNAL(CLICKED), self.loadTx)
      self.connect(self.btnCopy, SIGNAL(CLICKED), self.copyTx)
      self.connect(self.btnCopyHex, SIGNAL(CLICKED), self.copyTxHex)

      self.lblStatus = QRichLabel('')
      self.lblStatus.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      wStat, hStat = relaxedSizeStr(self.lblStatus, 'Signature is Invalid!')
      self.lblStatus.setMinimumWidth(int(wStat * 1.2))
      self.lblStatus.setMinimumHeight(int(hStat * 1.2))


      frmDescr = makeLayoutFrame(HORIZONTAL, [lblDescr], STYLE_RAISED)

      self.infoLbls = []

      # ##
      self.infoLbls.append([])
      self.infoLbls[-1].append(self.main.createToolTipWidget(\
            'This is wallet from which the offline transaction spends bitcoins'))
      self.infoLbls[-1].append(QRichLabel('<b>Wallet:</b>'))
      self.infoLbls[-1].append(QRichLabel(''))

      # ##
      self.infoLbls.append([])
      self.infoLbls[-1].append(self.main.createToolTipWidget('The name of the wallet'))
      self.infoLbls[-1].append(QRichLabel('<b>Wallet Label:</b>'))
      self.infoLbls[-1].append(QRichLabel(''))

      # ##
      self.infoLbls.append([])
      self.infoLbls[-1].append(self.main.createToolTipWidget(\
         'A unique string that identifies an <i>unsigned</i> transaction.  '
         'This is different than the ID that the transaction will have when '
         'it is finally broadcast, because the broadcast ID cannot be '
         'calculated without all the signatures'))
      self.infoLbls[-1].append(QRichLabel('<b>Pre-Broadcast ID:</b>'))
      self.infoLbls[-1].append(QRichLabel(''))

      # ##
      self.infoLbls.append([])
      self.infoLbls[-1].append(self.main.createToolTipWidget(\
                               'Net effect on this wallet\'s balance'))
      self.infoLbls[-1].append(QRichLabel('<b>Transaction Amount:</b>'))
      self.infoLbls[-1].append(QRichLabel(''))

      self.moreInfo = QLabelButton('Click here for more<br> information about <br>this transaction')
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
                                         STRETCH, \
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
      frmBottomLayout.addWidget(self.txtTxDP, 0, 0, 1, 1)
      frmBottomLayout.addWidget(frmBtn, 0, 1, 2, 1)
      frmBottomLayout.addWidget(frmInfo, 1, 0, 1, 1)
      # frmBottomLayout.addWidget(frmMoreInfo,   1,1,  1,1)
      frmBottom.setLayout(frmBottomLayout)

      layout = QVBoxLayout()
      layout.addWidget(frmDescr)
      layout.addWidget(frmBottom)

      self.setLayout(layout)
      self.processTxDP()

   def processTxDP(self):
      # TODO:  it wouldn't be TOO hard to modify this dialog to take
      #        arbitrary hex-serialized transactions for broadcast...
      #        but it's not trivial either (for instance, I assume
      #        that we have inputs values, etc)
      self.wlt = None
      self.leValue = None
      self.txdpObj = None
      self.idxSelf = []
      self.idxOther = []
      self.lblStatus.setText('')
      self.lblCopied.setText('')
      self.enoughSigs = False
      self.sigsValid = False
      self.txdpReadable = False

      txdpStr = str(self.txtTxDP.toPlainText())
      try:
         self.txdpObj = PyTxDistProposal().unserializeAscii(txdpStr)
         self.enoughSigs = self.txdpObj.checkTxHasEnoughSignatures()
         self.sigsValid = self.txdpObj.checkTxHasEnoughSignatures(alsoVerify=True)
         self.txdpReadable = True
      except BadAddressError:
         QMessageBox.critical(self, 'Inconsistent Data!', \
            'This transaction contains inconsistent information.  This '
            'is probably not your fault...', QMessageBox.Ok)
         self.txdpObj = None
         self.txdpReadable = False
      except NetworkIDError:
         QMessageBox.critical(self, 'Wrong Network!', \
            'This transaction is actually for a different network!  '
            'Did you load the correct transaction?', QMessageBox.Ok)
         self.txdpObj = None
         self.txdpReadable = False
      except (UnserializeError, IndexError, ValueError):
         self.txdpObj = None
         self.txdpReadable = False

      if not self.enoughSigs or not self.sigsValid or not self.txdpReadable:
         self.btnBroadcast.setEnabled(False)
      else:
         if self.main.netMode == NETWORKMODE.Full:
            self.btnBroadcast.setEnabled(True)
         else:
            self.btnBroadcast.setEnabled(False)
            self.btnBroadcast.setToolTip('No connection to Bitcoin network!')

      self.btnSave.setEnabled(True)
      self.btnCopyHex.setEnabled(False)
      if not self.txdpReadable:
         if len(txdpStr) > 0:
            self.lblStatus.setText('<b><font color="red">Unrecognized!</font></b>')
         else:
            self.lblStatus.setText('')
         self.btnSign.setEnabled(False)
         self.btnBroadcast.setEnabled(False)
         self.btnSave.setEnabled(False)
         self.makeReviewFrame()
         return
      elif not self.enoughSigs:
         if not self.main.getSettingOrSetDefault('DNAA_ReviewOfflineTx', False):
            result = MsgBoxWithDNAA(MSGBOX.Warning, title='Offline Warning', \
                  msg='<b>Please review your transaction carefully before '
                  'signing and broadcasting it!</b>  The extra security of '
                  'using offline wallets is lost if you do '
                  'not confirm the transaction is correct!', dnaaMsg=None)
            self.main.writeSetting('DNAA_ReviewOfflineTx', result[1])
         self.lblStatus.setText('<b><font color="red">Unsigned</font></b>')
         self.btnSign.setEnabled(True)
         self.btnBroadcast.setEnabled(False)
      elif not self.sigsValid:
         self.lblStatus.setText('<b><font color="red">Bad Signature!</font></b>')
         self.btnSign.setEnabled(True)
         self.btnBroadcast.setEnabled(False)
      else:
         self.lblStatus.setText('<b><font color="green">All Signatures Valid!</font></b>')
         self.btnSign.setEnabled(False)
         self.btnCopyHex.setEnabled(True)


      # NOTE:  We assume this is an OUTGOING transaction.  When I pull in the
      #        multi-sig code, I will have to either make a different dialog,
      #        or add some logic to this one
      FIELDS = enum('Hash', 'OutList', 'SumOut', 'InList', 'SumIn', 'Time', 'Blk', 'Idx')
      data = extractTxInfo(self.txdpObj, -1)

      # Collect the input wallets (hopefully just one of them)
      fromWlts = set()
      for scrAddr, amt, a, b, c in data[FIELDS.InList]:
         wltID = self.main.getWalletForAddr160(scrAddr[1:])
         if not wltID == '':
            fromWlts.add(wltID)

      if len(fromWlts) > 1:
         QMessageBox.warning(self, 'Multiple Input Wallets', \
            'Somehow, you have obtained a transaction that actually pulls from more '
            'than one wallet.  The support for handling multi-wallet signatures is '
            'not currently implemented (this also could have happened if you imported '
            'the same private key into two different wallets).' , QMessageBox.Ok)
         self.makeReviewFrame()
         return
      elif len(fromWlts) == 0:
         QMessageBox.warning(self, 'Unrelated Transaction', \
            'This transaction appears to have no relationship to any of the wallets '
            'stored on this computer.  Did you load the correct transaction?', \
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
      for scrType, amt, recip in data[FIELDS.OutList]:
         wltID = self.main.getWalletForAddr160(recip)
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
      if self.txdpObj == None:
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
            self.infoLbls[0][2].setText('[[ Unrelated ]]')
            self.infoLbls[1][2].setText('')

         ##### 2
         self.infoLbls[2][2].setText(self.txdpObj.uniqueB58)

         ##### 3
         if self.leValue:
            self.infoLbls[3][2].setText(coin2strNZS(self.leValue) + '  BTC')
         else:
            self.infoLbls[3][2].setText('')

         self.moreInfo.setVisible(True)

   def execMoreTxInfo(self):

      if not self.txdpObj:
         self.processTxDP()

      if not self.txdpObj:
         QMessageBox.warning(self, 'Invalid Transaction', \
            'Transaction data is invalid and cannot be shown!', QMessageBox.Ok)
         return

      dlgTxInfo = DlgDispTxInfo(self.txdpObj, self.wlt, self.parent(), self.main, \
                          precomputeIdxGray=self.idxSelf, precomputeAmt=-self.leValue, txtime=-1)
      dlgTxInfo.exec_()



   def signTx(self):
      if not self.txdpObj:
         QMessageBox.critical(self, 'Cannot Sign', \
               'This transaction is not relevant to any of your wallets.'
               'Did you load the correct transaction?', QMessageBox.Ok)
         return

      if self.txdpObj == None:
         QMessageBox.warning(self, 'Not Signable', \
               'This is not a valid transaction, and thus it cannot '
               'be signed. ', QMessageBox.Ok)
         return
      elif self.enoughSigs and self.sigsValid:
         QMessageBox.warning(self, 'Already Signed', \
               'This transaction has already been signed!', QMessageBox.Ok)
         return


      if self.wlt and self.wlt.watchingOnly:
         QMessageBox.warning(self, 'No Private Keys!', \
            'This transaction refers one of your wallets, but that wallet '
            'is a watching-only wallet.  Therefore, private keys are '
            'not available to sign this transaction.', \
             QMessageBox.Ok)
         return


      # We should provide the same confirmation dialog here, as we do when
      # sending a regular (online) transaction.  But the DlgConfirmSend was
      # not really designed
      txdp = self.txdpObj
      rvpairs = []
      rvpairsMine = []
      outInfo = txdp.pytxObj.makeRecipientsList()
      theFee = sum(txdp.inputValues) - sum([info[1] for info in outInfo])
      for info in outInfo:
         if not info[0] in CPP_TXOUT_HAS_ADDRSTR:
            rvpairs.append(['Non-Standard Output', info[1]])
            continue

         addrStr = script_to_addrStr(info[2])
         addr160 = addrStr_to_hash160(addrStr)[1]
         scrAddr = script_to_scrAddr(info[2])
         rvpairs.append([scrAddr, info[1]])
         if self.wlt.hasAddr(addr160):
            rvpairsMine.append([scrAddr, info[1]])

      if len(rvpairsMine) == 0 and len(rvpairs) > 1:
         QMessageBox.warning(self, 'Missing Change', \
            'This transaction has %d recipients, and none of them '
            'are addresses in this wallet (for receiving change).  '
            'This can happen if you specified a custom change address '
            'for this transaction, or sometimes happens solely by '
            'chance with a multi-recipient transaction.  It could also '
            'be the result of someone tampering with the transaction. '
            '<br><br>The transaction is valid and ready to be signed.  Please '
            'verify the recipient and amounts carefully before '
            'confirming the transaction on the next screen.' % len(rvpairs), \
            QMessageBox.Ok)
      dlg = DlgConfirmSend(self.wlt, rvpairs, theFee, self, self.main)
      if not dlg.exec_():
         return



      if self.wlt.useEncryption and self.wlt.isLocked:
         Passphrase = None  

         unlockdlg = DlgUnlockWallet(self.wlt, self, self.main, 'Send Transaction', returnPassphrase=True)
         if unlockdlg.exec_():
            if unlockdlg.Accepted == 1:
               Passphrase = unlockdlg.securePassphrase.copy()
               unlockdlg.securePassphrase.destroy()
                     
         if Passphrase is None or self.wlt.kdf is None:
            QMessageBox.critical(self.parent(), 'Wallet is Locked', \
               'Cannot sign transaction while your wallet is locked. ', \
               QMessageBox.Ok)
            return
         else:
            self.wlt.kdfKey = self.wlt.kdf.DeriveKey(Passphrase)
            Passphrase.destroy()                                              

      newTxdp = self.wlt.signTxDistProposal(self.txdpObj)
      self.wlt.advanceHighestIndex()
      self.txtTxDP.setText(newTxdp.serializeAscii())
      self.txdpObj = newTxdp

      if not self.fileLoaded == None:
         self.saveTxAuto()


   def broadTx(self):
      if self.main.netMode == NETWORKMODE.Disconnected:
         QMessageBox.warning(self, 'No Internet!', \
            'Armory lost its connection to Bitcoin-Qt, and cannot '
            'broadcast any transactions until it is reconnected. '
            'Please verify that Bitcoin-Qt (or bitcoind) is open '
            'and synchronized with the network.', QMessageBox.Ok)
         return
      elif self.main.netMode == NETWORKMODE.Offline:
         QMessageBox.warning(self, 'No Internet!', \
            'You do not currently have a connection to the Bitcoin network. '
            'If this does not seem correct, verify that Bitcoin-Qt is open '
            'and synchronized with the network.', QMessageBox.Ok)
         return



      try:
         finalTx = self.txdpObj.prepareFinalTx()
      except:
         QMessageBox.warning(self, 'Error', \
            'There was an error processing this transaction, for reasons '
            'that are probably not your fault...', QMessageBox.Ok)
         return

      # We should provide the same confirmation dialog here, as we do when
      # sending a regular (online) transaction.  But the DlgConfirmSend was
      # not really designed
      txdp = self.txdpObj
      rvpairs = []
      rvpairsMine = []
      outInfo = txdp.pytxObj.makeRecipientsList()
      theFee = sum(txdp.inputValues) - sum([info[1] for info in outInfo])
      for info in outInfo:
         if not info[0] in CPP_TXOUT_HAS_ADDRSTR:
            rvpairs.append(['Non-Standard Output', info[1]])
            continue

         addrStr = script_to_addrStr(info[2])
         addr160 = addrStr_to_hash160(addrStr)[1]
         scrAddr = script_to_scrAddr(info[2])
         rvpairs.append([scrAddr, info[1]])

      dlg = DlgConfirmSend(self.wlt, rvpairs, theFee, self, self.main)
      
      if dlg.exec_():
         self.main.broadcastTransaction(finalTx)
         if self.fileLoaded and os.path.exists(self.fileLoaded):
            try:
               # pcs = self.fileLoaded.split('.')
               # newFileName = '.'.join(pcs[:-2]) + '.DONE.' + '.'.join(pcs[-2:])
               shutil.move(self.fileLoaded, self.fileLoaded.replace('signed', 'SENT'))
            except:
               QMessageBox.critical(self, 'File Remove Error', \
                  'The file could not be deleted.  If you want to delete '
                  'it, please do so manually.  The file was loaded from: '
                  '<br><br>%s: ' % self.fileLoaded, QMessageBox.Ok)
         if self.parent() is ArmoryDialog:
            self.parent().accept()


   def saveTxAuto(self):
      if not self.txdpReadable:
         QMessageBox.warning(self, 'Formatting Error', \
            'The transaction data was not in a format recognized by '
            'Armory.')
         return


      if not self.fileLoaded == None and self.enoughSigs and self.sigsValid:
         newSaveFile = self.fileLoaded.replace('unsigned', 'signed')
         print newSaveFile
         f = open(newSaveFile, 'w')
         f.write(str(self.txtTxDP.toPlainText()))
         f.close()
         if not newSaveFile == self.fileLoaded:
            os.remove(self.fileLoaded)
         self.fileLoaded = newSaveFile
         QMessageBox.information(self, 'Transaction Saved!', \
            'Your transaction has been saved to the following location:'
            '\n\n%s\n\nIt can now be broadcast from any computer running '
            'Armory in online mode.' % newSaveFile, QMessageBox.Ok)
         return

   def saveTx(self):
      if not self.txdpReadable:
         QMessageBox.warning(self, 'Formatting Error', \
            'The transaction data was not in a format recognized by '
            'Armory.')
         return


      # The strange windows branching is because PyQt in Windows automatically
      # adds the ffilter suffix to the default filename, where as it needs to
      # be explicitly added in PyQt in Linux.  Not sure why this behavior exists.
      defaultFilename = ''
      if not self.txdpObj == None:
         if self.enoughSigs and self.sigsValid:
            suffix = '' if OS_WINDOWS else '.signed.tx'
            defaultFilename = 'armory_%s_%s' % (self.txdpObj.uniqueB58, suffix)
            ffilt = 'Transactions (*.signed.tx *.unsigned.tx)'
         else:
            suffix = '' if OS_WINDOWS else '.unsigned.tx'
            defaultFilename = 'armory_%s_%s' % (self.txdpObj.uniqueB58, suffix)
            ffilt = 'Transactions (*.unsigned.tx *.signed.tx)'
      filename = self.main.getFileSave('Save Transaction', \
                             [ffilt], \
                             defaultFilename)

      filename = filename.replace('unsigned.tx.unsigned.tx', 'unsigned.tx')
      filename = filename.replace('unsigned.tx.unsigned.tx', 'unsigned.tx')
      filename = filename.replace('signed.tx.signed.tx', 'signed.tx')
      filename = filename.replace('signed.tx.signed.tx', 'signed.tx')
      filename = filename.replace('unsigned.tx.signed.tx', 'signed.tx')
      if len(str(filename)) > 0:
         LOGINFO('Saving transaction file: %s', filename)
         f = open(filename, 'w')
         f.write(str(self.txtTxDP.toPlainText()))
         f.close()


   def loadTx(self):
      filename = self.main.getFileLoad('Load Transaction', \
                             ['Transactions (*.signed.tx *.unsigned.tx)'])

      if len(str(filename)) > 0:
         LOGINFO('Selected transaction file to load: %s', filename)
         print filename
         f = open(filename, 'r')
         self.txtTxDP.setText(f.read())
         f.close()
         self.fileLoaded = filename
         print self.fileLoaded


   def copyTx(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(self.txtTxDP.toPlainText()))
      self.lblCopied.setText('<i>Copied!</i>')


   def copyTxHex(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(binary_to_hex(self.txdpObj.prepareFinalTx().serialize()))
      self.lblCopied.setText('<i>Copied!</i>')
         
# Need to put circular imports at the end of the script to avoid an import deadlock
from qtdialogs import CLICKED, STRETCH, createAddrBookButton,\
      DlgConfirmSend, DlgUriCopyAndPaste, DlgUnlockWallet,\
   extractTxInfo, DlgDispTxInfo, NO_CHANGE
