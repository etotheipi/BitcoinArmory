from PyQt4.Qt import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from qtdefines import *
from qtdialogs import createAddrBookButton, DlgSetComment
from armoryengine.ALL import *
from armoryengine.MultiSigUtils import MultiSigEnvelope, getMultiSigID


################################################################################
class DlgSelectMultiSigOption(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main):
      super(DlgSelectMultiSigOption, self).__init__(parent, main)

      self.btnCreate = QPushButton(tr('Create/edit multi-sig envelope'))
      self.btnImport = QPushButton(tr('Import multi-sig envelope'))
      self.btnFund   = QPushButton(tr('Fund a multi-sig envelope'))
      self.btnSpend  = QPushButton(tr('Spend from a multi-sig envelope'))

      lblDescr  = QRichLabel(tr("""
         <font color="%s" size=5><b>Multi-signature Transactions 
         [EXPERIMENTAL]</b></font>""") % htmlColor('TextBlue'), 
         hAlign=Qt.AlignHCenter, doWrap=False)

      lblDescr2 = QRichLabel(tr("""
         The buttons below link you to all the functionality needed to 
         create, fund and spend from multi-signature "envelopes."  This 
         includes turning multiple wallets into a multi-factor lock-box
         for your personal coins, or can be used for escrow between
         multiple parties, using the Bitcoin network itself to hold the
         escrow.
         <br><br>
         <b><u>IMPORTANT:</u></b>  If you are using an envelope that requires
         being funded by multiple parties simultaneously, you should 
         <b><u>not</u> </b> use regular transactions to do the funding.  
         You should use the third button labeled "Fund a multi-sig envelope" 
         to collect funding promises into a single transaction, to limit 
         the ability of any party to scam you.  Read more about it by
         clicking [NO LINK YET]  (if the above doesn't hold, you can use
         the regular "Send Bitcoins" dialog to fund the envelope)."""))


      self.lblCreate = QRichLabel(tr("""
         Collect public keys to create an "address" that can be used 
         to send funds to the multi-sig container"""))
      self.lblImport = QRichLabel(tr("""
         If someone has already created the envelope you can add it 
         to your envelope list"""))
      self.lblFund = QRichLabel(tr("""
         Send money to an envelope simultaneously with other 
         parties involved in the envelope"""))
      self.lblSpend = QRichLabel(tr("""
         Collect signatures to authorize transferring money out of 
         a multi-sig envelope"""))


      self.connect(self.btnCreate,  SIGNAL('clicked()'), self.openCreate)
      self.connect(self.btnImport,  SIGNAL('clicked()'), self.openImport)
      self.connect(self.btnFund,    SIGNAL('clicked()'), self.openFund)
      self.connect(self.btnSpend,   SIGNAL('clicked()'), self.openSpend)

      layoutTop = QVBoxLayout()
      layoutTop.addWidget(lblDescr)
      layoutTop.addWidget(HLINE())
      layoutTop.addWidget(lblDescr2, 1)
      frmTop = QFrame()
      frmTop.setFrameStyle(STYLE_RAISED)
      frmTop.setLayout(layoutTop)


      layoutBottom = QGridLayout()
      layoutBottom.addItem(QSpacerItem(10,10),    0,0,  7,1)
      layoutBottom.addItem(QSpacerItem(10,10),    0,6,  7,1)

      layoutBottom.addItem(QSpacerItem(10,10),    0,1)
      layoutBottom.addItem(QSpacerItem(10,10),    2,1)
      layoutBottom.addItem(QSpacerItem(10,10),    4,1)
      layoutBottom.addItem(QSpacerItem(10,10),    6,1)

      layoutBottom.addWidget(self.btnCreate,      0,2)
      layoutBottom.addWidget(self.btnImport,      2,2)
      layoutBottom.addWidget(self.btnFund,        4,2)
      layoutBottom.addWidget(self.btnSpend,       6,2)

      layoutBottom.addItem(QSpacerItem(10,10),    0,3)
      layoutBottom.addItem(QSpacerItem(10,10),    2,3)
      layoutBottom.addItem(QSpacerItem(10,10),    4,3)
      layoutBottom.addItem(QSpacerItem(10,10),    6,3)

      layoutBottom.addWidget(self.lblCreate,      0,4)
      layoutBottom.addWidget(self.lblImport,      2,4)
      layoutBottom.addWidget(self.lblFund,        4,4)
      layoutBottom.addWidget(self.lblSpend,       6,4)

      layoutBottom.addItem(QSpacerItem(10,10),    0,5)
      layoutBottom.addItem(QSpacerItem(10,10),    2,5)
      layoutBottom.addItem(QSpacerItem(10,10),    4,5)
      layoutBottom.addItem(QSpacerItem(10,10),    6,5)

      layoutBottom.addWidget(HLINE(),             1,1,  1,4)
      layoutBottom.addWidget(HLINE(),             3,1,  1,4)
      layoutBottom.addWidget(HLINE(),             5,1,  1,4)

      layoutBottom.setColumnStretch(2, 1)
      layoutBottom.setColumnStretch(4, 2)

      frmBottom = QFrame()
      frmBottom.setFrameStyle(STYLE_RAISED)
      frmBottom.setLayout(layoutBottom)
      

      btnDone = QPushButton(tr("Done"))
      self.connect(btnDone, SIGNAL('clicked()'), self.accept)
      frmDone = makeHorizFrame(['Stretch', btnDone])

      layoutMaster = QVBoxLayout()
      layoutMaster.addWidget(frmTop)
      layoutMaster.addWidget(frmBottom,1)
      layoutMaster.addWidget(frmDone)

      self.setMinimumWidth(550)
      self.setLayout(layoutMaster)
      self.setWindowTitle(tr('Multi-Signature Transactions [EXPERIMENTAL]'))
      


   #############################################################################
   def openCreate(self):
      DlgCreateEnvelope(self, self.main).exec_()

   #############################################################################
   def openImport(self):
      DlgImportEnvelope(self, self.main).exec_()

   #############################################################################
   def openFund(self):
      DlgFundEnvelope(self, self.main).exec_()

   #############################################################################
   def openSpend(self):
      DlgSpendFromEnvelope(self, self.main).exec_()
         


#############################################################################
class DlgBrowseEnvelopes(ArmoryDialog):
   #############################################################################
   def __init__(self, parent, main):
      super(DlgBrowseEnvelopes, self).__init__(parent, main)
    


#############################################################################
class DlgCreateEnvelope(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, maxM=5, maxN=5, prefill=None):
      super(DlgCreateEnvelope, self).__init__(parent, main)

      QMessageBox.warning(self, tr('Dangerous Feature!'), tr("""
         Multi-signature transaction hacking is an 
         <b>EXPERIMENTAL</b> feature in this version of Armory.  It is 
         <u>not</u> intended to be used with real money, until it is
         moved out of the "Experimental" menu on the main screen.
         <br><br>
         <b>Use at your own risk!</b>"""), QMessageBox.Ok)

      lblDescr = QRichLabel(tr("""
         <b><u><font size=5 color="%s">Multi-Sig is an experimental 
         feature!</font></u>  
         <br><br>
         Please do not use this with money you cannot afford to 
         lose!""") % htmlColor("TextRed"), hAlign=Qt.AlignHCenter)

      lblDescr2 = QRichLabel(tr("""
         Use this form to create a "multi-signature envelope" to hold
         coins in escrow between multiple parties, or to share signing
         authority between multiple devices or wallets.  Once the envelope is
         created, you can send coins to it by selecting it in your 
         address book from the "Send Bitcoins" window.  Spending or 
         moving bitcoins held in the envelope requires a special 
         preparation and signing procedure, which can be accessed via
         the "MultiSig" menu on the main screen"""))

      lblDescr3 = QRichLabel(tr("""
         <b>Multi-signature "envelopes" require <u>public keys</u>, not 
         the address strings most Bitcoin users are familiar with.</b>
         <a href="None">Click for more info</a>."""))

      def openMoreInfo(*args): 
         QMessageBox.information(self, tr('Public Key Information'), tr("""
            A public key is much longer than an
            address string, and always starts with "02", "03" or "04".
            Most wallet applications do not provide an easy way to access  
            a public key associated with a given address.  This is easiest
            if everyone is using Armory.
            <br><br>
            The address book buttons next to each input box below will show you 
            normal address strings, but will enter the correct public 
            key of the address you select.  
            <br><br>
            If you are creating this multi-signature transaction with other
            Armory users, they can get their public keys by right-clicking 
            on the address in the wallet properties, and selecting 
            "Copy Public Key" (only available in Armory versions >0.91, 
            in "Expert" usermode)."""), QMessageBox.Ok)

      lblDescr3.setOpenExternalLinks(False)
      self.connect(lblDescr3, SIGNAL('linkActivated(const QString &)'), \
                                                               openMoreInfo)
      


      self.comboM = QComboBox()
      self.comboN = QComboBox()
      self.maxM = maxM
      self.maxN = maxN
      self.minM = 1
      self.minN = 2
      self.FinalScript = None
      self.connect(self.comboM, SIGNAL('activated(int)'), \
                                             self.updateWidgetTable_M)
      self.connect(self.comboN, SIGNAL('activated(int)'), \
                                             self.updateWidgetTable_N)
      self.comboM.setFont(GETFONT('Var', 14, bold=True))
      self.comboN.setFont(GETFONT('Var', 14, bold=True))
      self.lblMasterIcon = QLabel()

      # Used to optimize update-on-every-key-press
      self.prevTextLength = [0]*self.maxN


      if prefill is None:
         prefill = {}

      defaultM = prefill['M'] if 'M' in prefill else 2
      defaultN = prefill['N'] if 'N' in prefill else 3
      
      defaultPubKeyList = ['']*self.maxN
      if 'Script' in prefill:
         defaultM, defaultN, a160list, defaultPubKeyList = \
                           getMultisigScriptInfo(prefill['Script']) 
      elif 'PubKeyList' in prefill:
         defaultPubKeyList = prefill['PubKeyList'][:]
         if not len(defaultPubKeyList)==defaultN:
            LOGERROR('Size of key list does not match specified N value!')



      for i in range(1,self.maxM+1):
         self.comboM.addItem(str(i))

      for i in range(2, self.maxN+1):
         self.comboN.addItem(str(i))

      self.comboM.setCurrentIndex(defaultM-1)
      self.comboN.setCurrentIndex(defaultN-2)

      self.widgetMap = {}
      for i in range(self.maxN):
         self.widgetMap[i] = {}
         self.widgetMap[i]['IMG_ICON'] = QLabel()
         self.widgetMap[i]['LBL_ROWN'] = QRichLabel(tr("""
            Public Key #<font size=4 color="%s">%d</font>:""") % \
            (htmlColor('TextBlue'), i+1), doWrap=False, hAlign=Qt.AlignRight)
         self.widgetMap[i]['LBL_ADRN'] = QRichLabel(tr('Address:'), \
                                                    doWrap=False, \
                                                    hAlign=Qt.AlignRight)
         self.widgetMap[i]['LBL_WLTN'] = QRichLabel(tr('Name or ID:'), \
                                                    doWrap=False, \
                                                    hAlign=Qt.AlignRight)
         self.widgetMap[i]['EDT_PUBK'] = QLineEdit()
         self.widgetMap[i]['BTN_BOOK'] = \
            createAddrBookButton(self, self.widgetMap[i]['EDT_PUBK'], None, \
                                                         getPubKey=True)
         self.widgetMap[i]['LBL_ASTR'] = QRichLabel('', doWrap=False)
         self.widgetMap[i]['LBL_NAME'] = QRichLabel('', doWrap=False)

         self.widgetMap[i]['BTN_NAME'] = QLabelButton(tr('Edit'))
         self.widgetMap[i]['BTN_NAME'].setContentsMargins(0,0,0,0)

         def createCallBack(i):
            def nameClick():
               self.clickNameButton(i)
            return nameClick

         self.connect(self.widgetMap[i]['BTN_NAME'], SIGNAL('clicked()'), \
                                                            createCallBack(i))
         

         self.connect(self.widgetMap[i]['EDT_PUBK'], \
                      SIGNAL('textChanged(QString)'), \
                      self.updateLabels)

         self.prevTextLength[i] = -1
         
         self.widgetMap[i]['EDT_PUBK'].setFont(GETFONT('Fixed', 9))
         w,h = tightSizeNChar(self.widgetMap[i]['EDT_PUBK'], 50)
         self.widgetMap[i]['EDT_PUBK'].setMinimumWidth(w)
         
         
      self.btnCancel   = QPushButton(tr('Exit'))
      self.btnContinue = QPushButton(tr('Create Envelope'))
      self.btnContinue.setEnabled(False)
      self.connect(self.btnContinue, SIGNAL('clicked()'), self.doContinue)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
      self.lblFinal = QRichLabel('')


      self.edtEnvName = QLineEdit()
      w,h = relaxedSizeNChar(self.edtEnvName, 36)
      self.edtEnvName.setMinimumWidth(w)
      self.edtEnvName.setMaxLength(64)

      self.btnLongDescr = QLabelButton(tr("Set extended info"))
      self.longDescr = u''
      self.connect(self.btnLongDescr, SIGNAL('clicked()'), self.setLongDescr)

      frmName = makeHorizFrame(['Stretch', 
                                QLabel('Envelope Name'),
                                self.edtEnvName,
                                self.btnLongDescr,
                                'Stretch'])
                                


      layoutPubKeys = QGridLayout()
      pkFrameList = []
      for i in range(self.maxN):
         pkFrameList.append(QFrame())
         layoutThisRow = QGridLayout()
         layoutThisRow.addWidget(self.widgetMap[i]['IMG_ICON'],  0, 0, 3,1)
         layoutThisRow.addWidget(self.widgetMap[i]['LBL_ROWN'],  0, 1)
         layoutThisRow.addWidget(self.widgetMap[i]['LBL_ADRN'],  1, 1)
         layoutThisRow.addWidget(self.widgetMap[i]['LBL_WLTN'],  2, 1)
         layoutThisRow.addItem(QSpacerItem(10,10),               0, 2)
         layoutThisRow.addWidget(self.widgetMap[i]['EDT_PUBK'],  0, 3)
         layoutThisRow.addWidget(self.widgetMap[i]['BTN_BOOK'],  0, 4)

         layoutName = QHBoxLayout()
         layoutName.addWidget(self.widgetMap[i]['LBL_NAME'])
         layoutName.addItem(QSpacerItem(5,5))
         layoutName.addWidget(self.widgetMap[i]['BTN_NAME'])
         layoutName.addStretch()

         layoutThisRow.addWidget(self.widgetMap[i]['LBL_ASTR'],  1,3, 1,2)
         layoutThisRow.addLayout(layoutName,                     2,3, 1,2)

         layoutThisRow.setColumnStretch(3, 1)
         layoutThisRow.setSpacing(0)
         pkFrameList[-1].setLayout(layoutThisRow)

      pkFrameList.append('Stretch')
      frmPubKeys = makeVertFrame( [frmName, lblDescr3]+pkFrameList, STYLE_RAISED)

      self.scrollPubKeys = QScrollArea()
      self.scrollPubKeys.setWidget(frmPubKeys)
      self.scrollPubKeys.setWidgetResizable(True)


      frmTop = makeVertFrame([lblDescr, HLINE(), lblDescr2], STYLE_RAISED)
      

      
      # Create the M,N select frame (stolen from frag-create dialog
      lblMNSelect = QRichLabel(tr("""<font color="%s" size=4><b>Create 
         Multi-Signature Address</b></font>""") % htmlColor("TextBlue"), \
         doWrap=False, hAlign=Qt.AlignHCenter)
      lblMNSelect.setVisible(False)

      lblBelowM = QRichLabel(tr('<b>Required Signatures (M)</b> '), \
                                       hAlign=Qt.AlignHCenter, doWrap=False)
      lblBelowN = QRichLabel(tr('<b>Total Public Keys (N)</b> '), \
                                       hAlign=Qt.AlignHCenter, doWrap=False)

      lblOfStr = QRichLabel(tr(' - OF - '))


      layoutMNSelect = QGridLayout()
      layoutMNSelect.addWidget(lblMNSelect,     0,0, 1,9)
      layoutMNSelect.addWidget(self.comboM,     1,2)
      layoutMNSelect.addWidget(lblOfStr,        1,4)
      layoutMNSelect.addWidget(self.comboN,     1,6)
      layoutMNSelect.addWidget(lblBelowM,       2,1, 1,3)
      layoutMNSelect.addWidget(lblBelowN,       2,5, 1,3)
      layoutMNSelect.setColumnStretch(0,1)
      layoutMNSelect.setColumnStretch(8,1)
      
      frmMNSelect = QFrame()
      frmMNSelect.setFrameStyle(STYLE_RAISED)
      frmMNSelect.setLayout(layoutMNSelect)


      frmFinish = makeHorizFrame([self.btnCancel, 'Stretch', self.btnContinue])

      layoutMaster = QVBoxLayout()
      layoutMaster.addWidget(frmTop)
      layoutMaster.addWidget(frmMNSelect)
      layoutMaster.addWidget(self.scrollPubKeys, 1)
      layoutMaster.addWidget(HLINE())
      layoutMaster.addWidget(frmFinish)

      self.updateWidgetTable(defaultM, defaultN)
      self.updateLabels(forceUpdate=True)

      self.setLayout(layoutMaster)
      self.setWindowTitle('Multi-Sig Hacker [EXPERIMENTAL]')
      self.setMinimumWidth(750)
       

   #############################################################################
   def clickNameButton(self, i):
      currName = unicode(self.widgetMap[i]['LBL_NAME'].text())
      dlgComm = DlgSetComment(self, self.main, currName, \
                              'Multi-Sig', 'Name or Idenifier (such as email)')
      if dlgComm.exec_():
         self.widgetMap[i]['LBL_NAME'].setText(dlgComm.edtComment.text())


   #############################################################################
   def setLongDescr(self):

      class DlgSetLongDescr(QDialog):
         def __init__(self, parent, currDescr=''):
            super(DlgSetLongDescr, self).__init__(parent)
            lbl = QRichLabel(tr("""
               <b><u>Set Extended Envelope Details</u></b>
               <br><br>
               Use this space to store any extended information about this
               multi-signature envelope, such as contact information of other
               parties, references to contracts, etc.  Keep in mind that this
               field will be included when this envelope is shared with others,
               so you should include your own contact information, as well as
               avoid putting any sensitive data in here"""))

            self.descr = QPlainTextEdit()
            self.descr.setPlainText(currDescr)
            btn = QPushButton(tr("Done"))
            self.connect(btn, SIGNAL('clicked()'), self.accept)

            layout = QVBoxLayout()
            layout.addWidget(lbl)
            layout.addWidget(self.descr, 1)
            layout.addWidget(makeHorizFrame(['Stretch', btn]))
            self.setLayout(layout)
            self.setWindowTitle(tr('Edit Envelope Description'))
            self.setMinimumWidth(450)

      dlg = DlgSetLongDescr(self, self.longDescr)
      if dlg.exec_():
         self.longDescr = unicode(dlg.descr.toPlainText())
   
      

   #############################################################################
   def isValidHexPubKey(self, pkstr):
      # Don't check for valid pub keys in 65-byte fields; it would be slow
      # (this will be run after every key press)
      if len(pkstr) == 33*2:
         return pkstr[:2] in ['02','03']
      elif len(pkstr) == 65*2:
         return pkstr[:2] == '04'
      else:
         return False


   #############################################################################
   def updateLabels(self, *args, **kwargs):

      # Walk through the QLineEdits and verify
      for i in range(self.maxN):

         pkStr = str(self.widgetMap[i]['EDT_PUBK'].text())
         if not 'forceUpdate' in kwargs and len(pkStr) == self.prevTextLength[i]:
            continue

         self.prevTextLength[i] = len(pkStr)

         if not self.isValidHexPubKey(pkStr):
            self.widgetMap[i]['LBL_ASTR'].setText('')
            self.widgetMap[i]['LBL_NAME'].setText('')
            self.widgetMap[i]['BTN_NAME'].setVisible(False)
            continue
            
         addr160 = hash160(hex_to_binary(pkStr))
         addrStr = hash160_to_addrStr(addr160)
         wid = self.main.getWalletForAddr160(addr160)
         self.widgetMap[i]['LBL_NAME'].setVisible(True)
         self.widgetMap[i]['BTN_NAME'].setVisible(True)
         if not wid:
            self.widgetMap[i]['LBL_ASTR'].setText(addrStr)
            #self.widgetMap[i]['LBL_NAME'].setText('')
            self.widgetMap[i]['LBL_NAME'].setStyleSheet( \
                     'QLabel {color : "%s"; }' % htmlColor('Foreground'))
         else:
            self.widgetMap[i]['LBL_ASTR'].setText( \
               '<font color="%s">%s</font>' % \
               (htmlColor("TextBlue"), addrStr))
            self.widgetMap[i]['LBL_NAME'].setText( \
               '%s (%s)' % (self.main.walletMap[wid].labelName, wid))
            self.widgetMap[i]['LBL_NAME'].setStyleSheet( \
                     'QLabel {color : "%s"; }' % htmlColor('TextBlue'))

      # Disable the continue button if not all keys are in
      M = int(str(self.comboM.currentText()))
      N = int(str(self.comboN.currentText()))

      for i in range(N):
         pkStr = str(self.widgetMap[i]['EDT_PUBK'].text())
         if not self.isValidHexPubKey(pkStr):
            self.btnContinue.setEnabled(False)
            self.lblFinal.setText('')
            break
      else:
         self.formFilled = True
         self.btnContinue.setEnabled(True)
         self.lblFinal.setText(tr("""
            Using the <font color="%s"><b>%d</b></font> public keys above, 
            a multi-signature address will be created requiring
            <font color="%s"><b>%d</b></font> signatures to spend 
            money.""") % (htmlColor('TextBlue'),  M, htmlColor('TextBlue'), N))


         
      
   #############################################################################
   def updateWidgetTable_M(self, idxM):
      currN = int(str(self.comboN.currentText()))
      currM = idxM + 1

      self.minN = max(currM, 2)
      currN = max(self.minN, currN, 2)
      self.comboN.clear()
      setIndex = 0
      for i in range(self.minN, self.maxN+1):
         self.comboN.addItem(str(i))
         if i==currN:
            setIndex = i-self.minN

      self.comboN.setCurrentIndex(setIndex)
      self.updateWidgetTable(currM, currN)

   #############################################################################
   def updateWidgetTable_N(self, idxN):
      currM = int(str(self.comboM.currentText()))
      self.updateWidgetTable(currM, idxN+self.minN)

   #############################################################################
   def updateWidgetTable(self, M, N):

      self.imgPie = QPixmap(':/frag%df.png' % M)

      # Do the bulk of processing stuff
      for i in range(self.maxN):
         self.widgetMap[i]['IMG_ICON'].setPixmap(self.imgPie.scaled(40,40))

      self.lblMasterIcon.setPixmap(self.imgPie.scaled(64,64))

      for i in range(self.maxN):
         if i>=N:
            self.widgetMap[i]['EDT_PUBK'].setText('')

         for k,v in self.widgetMap[i].iteritems():
            v.setVisible(i<N)

      self.updateLabels(forceUpdate=True)
         

   
   #############################################################################
   def fillForm(self):
      pass
      
   #############################################################################
   def doContinue(self):
      currM = int(str(self.comboM.currentText()))
      currN = int(str(self.comboN.currentText()))

      print currM,currN

      # If we got here, we already know all the public keys are valid strings
      pubKeyList = []
      for i in range(currN):
         pkHex = str(self.widgetMap[i]['EDT_PUBK'].text())  
         pkBin = hex_to_binary(pkHex)
         isValid = self.isValidHexPubKey(pkHex)
         if len(pkBin) == 65:
            if not CryptoECDSA().VerifyPublicKeyValid(SecureBinaryData(pkBin)):
               isValid = False
            
         if not isValid:
            QMessageBox.critical(self, tr('Invalid Public Key'), tr("""
               The data specified for public key <b>%d</b> is not valid.
               Please double-check the data was entered correctly."""), \
               QMessageBox.Ok)
            return

         pubKeyList.append(pkBin)


      print 'PubKeys:'
      for pk in pubKeyList:
         print '   ', binary_to_hex(pk)
      

      txOutScript = pubkeylist_to_multisig_script(pubKeyList, currM, \
                                                         withSort=False)  
      opCodeList = convertScriptToOpStrings(txOutScript)
      scraddr = script_to_scrAddr(txOutScript)

      self.FinalScript  = txOutScript
      self.EnvelopeID   = getMultiSigID(txOutScript)
      self.NameIDList   = \
         [unicode(self.widgetMap[i]['LBL_NAME'].text()) for i in range(currN)]


      LOGINFO('Got a valid TxOut script:')
      LOGINFO('ScrAddrStr: ' + binary_to_hex(scraddr))
      LOGINFO('Raw script: ' + binary_to_hex(txOutScript))
      LOGINFO('HR Script: \n   ' + '\n   '.join(opCodeList))
      LOGINFO('Envelope ID: ' + self.EnvelopeID)
      LOGINFO('List of Names/IDs\n   ' + '\n   '.join(self.NameIDList))

      env = MultiSigEnvelope(txOutScript, \
                             unicode(self.edtEnvName.text()),
                             unicode(self.longDescr),
                             self.NameIDList)

      print 'pprint Env:'
      env.pprint()

      print 'Print encoded:'
      ser = env.serialize()
      print ser


      env2 = MultiSigEnvelope().unserialize(ser)
      print 'pprint Env:'
      env2.pprint()

      print 'Print encoded:'
      ser2 = env.serialize()
      print ser2

      print 'Equal: ', ser==ser2
      


################################################################################
def createContribBlock(self, msScript, walletID, amt, fee=0):

   msgParams = {}
   msgParams['Version'] = 0
   msgParams['MagicBytes'] = ''
   msgParams['IDBytes'] = ''
   msgParams['PayContrib'] = amt
   msgParams['FeeContrib'] = fee
   msgParams['ChangeScript'] = ''  
   msgParams['SupportTxList'] = []

   utxoList = self.main.walletMap[walletID].getTxOutList('Spendable')
   utxoSelect = PySelectCoins(utxoList, amt, fee)

   bp = BinaryPacker()
   bp.put(BINARY_CHUNK, msgParams['MagicBytes'])
   bp.put(BINARY_CHUNK, msgParams['IDBytes'])
   bp.put(UINT64,       msgParams['PayContrib'])
   bp.put(UINT64,       msgParams['FeeContrib'])
   bp.put(VAR_INT,      len(msgParams['ChangeScript']))
   bp.put(BINARY_CHUNK, msgParams['ChangeScript'])
   bp.put(VAR_INT,      len(msgParams['UtxoList']))
   bp.put(VAR_INT,      len(msgParams['UtxoList']))
   bp.put(VAR_INT,      len(msgParams['UtxoList']))
   


################################################################################
class DlgConfirmEnvelope(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, msScript):
      super(DlgConfirmEnvelope, self).__init__(parent, main)

      



################################################################################
class DlgContributeFundEnvelope(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, msScript):
      super(DlgContributeFundEnvelope, self).__init__(parent, main)



