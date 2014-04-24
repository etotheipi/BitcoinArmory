from PyQt4.Qt import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from qtdefines import *
from qtdialogs import createAddrBookButton, DlgSetComment, DlgSendBitcoins, \
                      DlgUnlockWallet, DlgQRCodeDisplay, DlgRequestPayment,\
   DlgDispTxInfo
from armoryengine.ALL import *
from armorymodels import *
from armoryengine.MultiSigUtils import MultiSigLockbox, calcLockboxID,\
   createLockboxEntryStr
from ui.MultiSigModels import \
            LockboxDisplayModel,  LockboxDisplayProxy, LOCKBOXCOLS
import webbrowser

         




#############################################################################
class DlgLockboxEditor(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, maxM=5, maxN=5, loadBox=None):
      super(DlgLockboxEditor, self).__init__(parent, main)

      lblDescr = QRichLabel(tr("""
         <b><u><font size=5 color="%s">Multi-sig is an experimental 
         feature!</font></u>  
         <br><br>
         Please do not use this with money you cannot afford to 
         lose!""") % htmlColor("TextRed"), hAlign=Qt.AlignHCenter)

      lblDescr2 = QRichLabel(tr("""
         Use this form to create a "multi-sig lockbox" to hold
         coins in escrow between multiple parties, or to share signing
         authority between multiple devices or wallets.  Once the lockbox is
         created, you can send coins to it by selecting it in your 
         address book from the "Send Bitcoins" window.  Spending or 
         moving bitcoins held in the lockbox requires a special 
         preparation and signing procedure, which can be accessed via
         the "MultiSig" menu on the main screen"""))

      lblDescr3 = QRichLabel(tr("""
         <b>Multi-sig "lockboxes" require <u>public keys</u>, not 
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
            If you are creating this lockbox with other
            Armory users, they can get their public keys by right-clicking 
            on the address in the wallet properties, and selecting 
            "Copy Public Key" (only available in Armory versions >0.91, 
            in "Expert" usermode)."""), QMessageBox.Ok)

      lblDescr3.setOpenExternalLinks(False)
      self.connect(lblDescr3, SIGNAL('linkActivated(const QString &)'), \
                                                               openMoreInfo)


      self.createDate = long(RightNow())
      self.loadedID = None
      self.comboM = QComboBox()
      self.comboN = QComboBox()
      self.maxM = maxM
      self.maxN = maxN
      self.minM = 1
      self.minN = 2
      self.connect(self.comboM, SIGNAL('activated(int)'), \
                                             self.updateWidgetTable_M)
      self.connect(self.comboN, SIGNAL('activated(int)'), \
                                             self.updateWidgetTable_N)
      self.comboM.setFont(GETFONT('Var', 14, bold=True))
      self.comboN.setFont(GETFONT('Var', 14, bold=True))
      self.lblMasterIcon = QLabel()

      # Used to optimize update-on-every-key-press
      self.prevTextLength = [0]*self.maxN



      for i in range(1,self.maxM+1):
         self.comboM.addItem(str(i))

      for i in range(2, self.maxN+1):
         self.comboN.addItem(str(i))

      defaultM = 2
      defaultN = 3
      
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
                                 getPubKey=True, selectMineOnly=True, showLockBoxes=False)
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
      self.btnContinue = QPushButton(tr('Save Lockbox'))
      self.btnContinue.setEnabled(False)
      self.connect(self.btnContinue, SIGNAL('clicked()'), self.doContinue)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)
      self.lblFinal = QRichLabel('')


      self.edtBoxName = QLineEdit()
      w,h = relaxedSizeNChar(self.edtBoxName, 36)
      self.edtBoxName.setMinimumWidth(w)
      self.edtBoxName.setMaxLength(64)

      self.btnLongDescr = QLabelButton(tr("Set extended info"))
      self.longDescr = u''
      self.connect(self.btnLongDescr, SIGNAL('clicked()'), self.setLongDescr)

      frmName = makeHorizFrame(['Stretch', 
                                QLabel('Lockbox Name:'),
                                self.edtBoxName,
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
         Multi-Sig Lockbox</b></font>""") % htmlColor("TextBlue"), \
         doWrap=False, hAlign=Qt.AlignHCenter)

      lblBelowM = QRichLabel(tr('<b>Required Signatures (M)</b> '), \
                                       hAlign=Qt.AlignHCenter, doWrap=False)
      lblBelowN = QRichLabel(tr('<b>Total Public Keys (N)</b> '), \
                                       hAlign=Qt.AlignHCenter, doWrap=False)

      lblOfStr = QRichLabel(tr(' - OF - '))


      btnClear  = QPushButton(tr('Clear All'))
      #btnLoad   = QPushButton(tr('Load Existing'))
      #btnImport = QPushButton(tr('Import'))

      self.connect(btnClear,  SIGNAL('clicked()'), self.clearAll)
      #self.connect(btnLoad,   SIGNAL('clicked()'), self.loadSaved)
      #self.connect(btnImport, SIGNAL('clicked()'), self.importNew)
      
      #frmLoadImport = makeVertFrame([btnLoad, btnImport, btnClear])
      #frmLoadImport.layout().setSpacing(0)


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


      frmFinish = makeHorizFrame([self.btnCancel, 
                                  'Stretch', 
                                  btnClear,
                                  'Stretch', 
                                  self.btnContinue])

      layoutMaster = QVBoxLayout()
      layoutMaster.addWidget(frmTop)
      layoutMaster.addWidget(frmMNSelect)
      layoutMaster.addWidget(self.scrollPubKeys, 1)
      layoutMaster.addWidget(frmFinish)

      self.updateWidgetTable(defaultM, defaultN)
      self.updateLabels(forceUpdate=True)

      if loadBox is not None:
         self.fillForm(loadBox)
         

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
               <b><u>Set Extended Lockbox Details</u></b>
               <br><br>
               Use this space to store any extended information about this
               multi-sig lockbox, such as contact information of other
               parties, references to contracts, etc.  Keep in mind that this
               field will be included when this lockbox is shared with others,
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
            self.setWindowTitle(tr('Edit Lockbox Description'))
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
            if len(str(self.widgetMap[i]['LBL_NAME'].text()).strip())==0:
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
            a multi-sig lockbox will be created requiring
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
   def clearAll(self):
      self.edtBoxName.clear()
      self.longDescr = ''
      for index,widMap in self.widgetMap.iteritems():
         for key,widget in widMap.iteritems():
            if key in ['EDT_PUBK', 'LBL_ASTR', 'LBL_NAME']:
               widget.clear()

   
   #############################################################################
   def fillForm(self, boxObj):

      self.edtBoxName.setText(boxObj.shortName)
      self.longDescr = boxObj.longDescr
      self.loadedID = boxObj.uniqueIDB58
      self.createDate = boxObj.createDate

      for i in range(boxObj.N):
         self.widgetMap[i]['EDT_PUBK'].setText(binary_to_hex(boxObj.pubKeys[i]))
         self.widgetMap[i]['LBL_NAME'].setText(boxObj.commentList[i])

      def setCombo(cmb, val):
         for i in range(cmb.count()):
            if str(cmb.itemText(i))==str(val):
               cmb.setCurrentIndex(i)

      setCombo(self.comboM, boxObj.M)
      setCombo(self.comboN, boxObj.N)

      self.updateWidgetTable(boxObj.M, boxObj.N)
      self.updateLabels(forceUpdate=True)
      
      
   #############################################################################
   def doContinue(self):

      currM = int(str(self.comboM.currentText()))
      currN = int(str(self.comboN.currentText()))

      if len(str(self.edtBoxName.text()).strip())==0:
         QMessageBox.warning(self, tr('Missing Name'), tr("""
            You did not specify a name for this lockbox, at the top of 
            the list of public keys.  You should also make sure you that
            you have set the extended information (next to it), for better
            documentation of what this lockbox is used for"""), QMessageBox.Ok)
         return

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
               Please double-check the data was entered correctly.""") % i, \
               QMessageBox.Ok)
            return

         pubKeyList.append(pkBin)



      txOutScript = pubkeylist_to_multisig_script(pubKeyList, currM, \
                                                         withSort=False)  
      opCodeList = convertScriptToOpStrings(txOutScript)
      scraddr = script_to_scrAddr(txOutScript)

      lockboxID = calcLockboxID(txOutScript)
      if self.loadedID is not None:
         if not self.loadedID == lockboxID:
            reply = QMessageBox.warning(self, tr('Different Lockbox'), tr("""
               You originally loaded lockbox (%s) but the edits you made
               have caused it to become a new/different lockbox (%s).
               Changing the M-value, N-value, or any of the public keys 
               will result in a new lockbox, unrelated to the original.
               <br><br>
               <b>If you click "Ok" a new lockbox will be created</b> instead
               of replacing the original.  If you do not need the original,
               you can go the lockbox browser and manually remove it.""") % \
               (self.loadedID, lockboxID), QMessageBox.Ok | QMessageBox.Cancel)
            if not reply==QMessageBox.Ok:
               return
            else:
               self.createDate = long(RightNow())
            

      self.NameIDList   = \
         [unicode(self.widgetMap[i]['LBL_NAME'].text()) for i in range(currN)]


      LOGINFO('Got a valid TxOut script:')
      LOGINFO('ScrAddrStr: ' + binary_to_hex(scraddr))
      LOGINFO('Raw script: ' + binary_to_hex(txOutScript))
      LOGINFO('HR Script: \n   ' + '\n   '.join(opCodeList))
      LOGINFO('Lockbox ID: ' + lockboxID)
      LOGINFO('List of Names/IDs\n   ' + '\n   '.join(self.NameIDList))

      self.lockbox = MultiSigLockbox( \
                                 txOutScript, \
                                 toUnicode(self.edtBoxName.text()),
                                 toUnicode(self.longDescr),
                                 self.NameIDList, 
                                 self.createDate)

      """
      print 'pprint Box:'
      self.lockbox.pprint()
      print 'Print encoded:'
      ser = self.lockbox.serialize()
      print ser
      box2 = MultiSigLockbox().unserialize(ser)
      print 'pprint box:'
      box2.pprint()
      print 'Print encoded:'
      ser2 = box2.serialize()
      print ser2
      print 'Equal: ', ser==ser2
      """

      self.main.updateOrAddLockbox(self.lockbox, isFresh=True)
      
      self.accept()
      DlgExportLockbox(self, self.main, self.lockbox).exec_()



################################################################################
class DlgExportLockbox(ArmoryDialog):
   def __init__(self, parent, main, lockbox):
      super(DlgExportLockbox, self).__init__(parent, main)


      lblDescr = QRichLabel(tr("""
         <b><font color="%s">IMPORTANT:</font> 
         All labels and descriptions you have entered for 
         this lockbox are included in this text block below!</b>  
         <br><br>
         Before you send this to any other parties, <em>please</em> confirm
         that you have not entered any sensitive or embarassing information 
         into any of the lockbox fields.  Each lockbox has a name and 
         extended information, as well as a comment for each public key.
         <br><br>
         All parties or devices that have [partial] signing authority
         over this lockbox need to import this data into their local 
         lockbox manager in order to use it.""") % htmlColor('TextWarn'))
         #<br><br>
         #Also, please make sure that all details for the lockbox, and each
         #public key are accurate, including your own.  For instance, if you
         #are storing everyone else's contact information in the lockbox 
         #info, make sure you include your own, as well, for their benefit."""))

      self.lockbox = lockbox
      self.boxText = lockbox.serializeAscii()

      txt = QPlainTextEdit()
      txt.setFont(GETFONT('Fixed', 9))
      w,h = relaxedSizeNChar(txt, 80)
      txt.setMinimumWidth(w)
      txt.setMinimumHeight(h*9)
      txt.setPlainText(self.boxText)

      self.lblCopied = QRichLabel('')
      btnCopy = QPushButton(tr("Copy to Clipboard"))
      btnSave = QPushButton(tr("Save to File"))
      btnDone = QPushButton(tr("Done"))
   
      self.connect(btnCopy, SIGNAL('clicked()'), self.clipcopy)
      self.connect(btnSave, SIGNAL('clicked()'), self.savefile)
      self.connect(btnDone, SIGNAL('clicked()'), self.accept)

      frmCopy = makeHorizFrame([btnSave, btnCopy, self.lblCopied, 'Stretch'])
      frmDone = makeHorizFrame(['Stretch', btnDone])

      frmMain = makeVertFrame([lblDescr, txt, frmCopy], STYLE_RAISED)

      layout = QVBoxLayout()
      layout.addWidget(frmMain)
      layout.addWidget(frmDone)
      self.setLayout(layout)

      self.setWindowTitle(tr("Export Lockbox Info"))
      self.setWindowIcon(QIcon(self.main.iconfile))


   def savefile(self):
      fn = self.main.getFileSave(tr('Export Lockbox Info'), 
                                 ['Lockboxes (*.lockbox.txt)'], 
                            'Multikey_%s.lockbox.txt'%self.lockbox.uniqueIDB58)
      if fn:
         with open(fn,'w') as f:
            f.write(self.boxText + '\n')
         self.accept()

   def clipcopy(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.boxText)
      self.lblCopied.setText('<i>Copied!</i>')
      

################################################################################
class DlgLockboxManager(ArmoryDialog):
   def __init__(self, parent, main):
      super(DlgLockboxManager, self).__init__(parent, main)

      QMessageBox.warning(self, tr('Dangerous Feature!'), tr("""
         Multi-signature transactions are an 
         <b>EXPERIMENTAL</b> feature in this version of Armory.  It is 
         <u><b>not</b></u> intended to be used with real money, until all 
         the warnings like this one go away.
         <br><br>
         <b>Use at your own risk!</b>"""), QMessageBox.Ok)


      lblDescr = QRichLabel(tr("""
         <font color="%s" size=4><b>Manage Multi-Sig Lockbox Info</b></font>
         <br> <b>Multi-Sig is an <u>EXPERIMENTAL</u> feature.  
         Use at your own risk!</b>""") % htmlColor('TextBlue'), 
         hAlign=Qt.AlignHCenter)
      
      #frmDescr = makeVertFrame([lblDescr1, lblDescr2], STYLE_RAISED)
      frmDescr = makeVertFrame([lblDescr], STYLE_RAISED)
   
      self.lboxModel = LockboxDisplayModel(self.main, \
                                    self.main.allLockboxes, \
                                    self.main.getPreferredDateFormat())
      self.lboxProxy = LockboxDisplayProxy(self)
      self.lboxProxy.setSourceModel(self.lboxModel)
      self.lboxProxy.sort(LOCKBOXCOLS.CreateDate, Qt.DescendingOrder)
      self.lboxView = QTableView()
      self.lboxView.setModel(self.lboxProxy)
      self.lboxView.setSortingEnabled(True)
      self.lboxView.setSelectionBehavior(QTableView.SelectRows)
      self.lboxView.setSelectionMode(QTableView.SingleSelection)
      self.lboxView.verticalHeader().setDefaultSectionSize(18)
      self.lboxView.horizontalHeader().setStretchLastSection(True)
      self.lboxView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.lboxView.customContextMenuRequested.connect(self.showLboxContextMenu)

      self.connect( \
            self.lboxView, 
            SIGNAL('clicked(QModelIndex)'), 
            self.singleClickLockbox)
      self.connect( \
            self.lboxView, 
            SIGNAL('doubleClicked(QModelIndex)'), 
            self.dblClickLockbox)

      self.txtLockboxInfo = QPlainTextEdit()
      self.txtLockboxInfo.setReadOnly(True)
      self.txtLockboxInfo.setFont(GETFONT('Fixed', 9))


      self.btnCreate = QPushButton(tr('Create New'))
      self.btnImport = QPushButton(tr('Import New'))
      self.btnEdit   = QPushButton(tr('Edit'))
      self.btnExport = QPushButton(tr('Export'))
      self.btnDelete = QPushButton(tr('Remove'))
      self.btnFundIt = QPushButton(tr('Deposit Funds'))
      self.btnSpend  = QPushButton(tr('Spend Funds'))

      self.connect(self.btnCreate,   SIGNAL('clicked()'), self.doCreate)
      self.connect(self.btnImport,   SIGNAL('clicked()'), self.doImport)
      self.connect(self.btnEdit,     SIGNAL('clicked()'), self.doEdit)
      self.connect(self.btnExport,   SIGNAL('clicked()'), self.doExport)
      self.connect(self.btnDelete,   SIGNAL('clicked()'), self.doDelete)
      self.connect(self.btnFundIt,   SIGNAL('clicked()'), self.doFundIt)
      self.connect(self.btnSpend,    SIGNAL('clicked()'), self.doSpend)
      
      frmManageBtns = makeVertFrame([ 'Stretch',
                                      QRichLabel(tr('<b>Create:</b>')),
                                      self.btnCreate, 
                                      self.btnImport,
                                      'Space(10)',
                                      QRichLabel(tr('<b>Selected:</b>')),
                                      self.btnEdit,
                                      self.btnExport,
                                      self.btnDelete,
                                      'Space(10)',
                                      self.btnFundIt,
                                      self.btnSpend,
                                      'Stretch'])

      """
      if not TheBDM.getBDMState()=='BlockchainReady':
         self.btnSpend.setDisabled(True)
         self.btnFundIt.setDisabled(True)
      """
            
      frmManageBtns.layout().setSpacing(2)

      btnDone = QPushButton(tr('Done'))
      frmDone = makeHorizFrame(['Stretch', btnDone])
      self.connect(btnDone, SIGNAL('clicked()'), self.accept)


      #maxKeys = max([lb.N for lb in self.main.allLockboxes])
      for i in range(LOCKBOXCOLS.Key0, LOCKBOXCOLS.Key4+1):
         self.lboxView.hideColumn(i)
      self.lboxView.hideColumn(LOCKBOXCOLS.UnixTime)

      # Main Tab displays lockbox details
      #self.lockboxTable = []
      #for lbID,cppWlt in self.main.cppLockboxWltMap.iteritems():
         #ledger = cppWlt.getTxLedger()
         #for i in range(len(ledger)):
            #self.lockboxTable.append([lbID, ledger[i]])
         
      #self.lockboxLedg = self.main.convertLedgerToTable(self.lockboxTable)

      self.ledgerProxy = LedgerDispSortProxy(self)
      self.ledgerProxy.setSourceModel(self.main.lockboxLedgModel)

      self.ledgerView  = QTableView()
      self.ledgerView.setModel(self.ledgerProxy)
      self.ledgerView.setSortingEnabled(True)
      self.ledgerView.setItemDelegate(LedgerDispDelegate(self))
      self.ledgerView.setSelectionBehavior(QTableView.SelectRows)
      self.ledgerView.setSelectionMode(QTableView.SingleSelection)
      self.ledgerView.verticalHeader().setDefaultSectionSize(20)
      self.ledgerView.verticalHeader().hide()
      self.ledgerView.horizontalHeader().setResizeMode(0, QHeaderView.Fixed)
      self.ledgerView.horizontalHeader().setResizeMode(3, QHeaderView.Fixed)

      self.ledgerView.hideColumn(LEDGERCOLS.isOther)
      self.ledgerView.hideColumn(LEDGERCOLS.UnixTime)
      self.ledgerView.hideColumn(LEDGERCOLS.WltID)
      self.ledgerView.hideColumn(LEDGERCOLS.TxHash)
      self.ledgerView.hideColumn(LEDGERCOLS.isCoinbase)
      self.ledgerView.hideColumn(LEDGERCOLS.toSelf)
      self.ledgerView.hideColumn(LEDGERCOLS.DoubleSpend)

      dateWidth    = tightSizeStr(self.ledgerView, '_9999-Dec-99 99:99pm__')[0]
      nameWidth    = tightSizeStr(self.ledgerView, '9'*32)[0]
      cWidth = 20 # num-confirm icon width
      tWidth = 72 # date icon width
      initialColResize(self.ledgerView, [cWidth, 0, dateWidth, tWidth, \
                                                            0.30, 0.40, 0.3])
      
      self.connect(self.ledgerView, SIGNAL('doubleClicked(QModelIndex)'), \
                   self.dblClickLedger)

      self.ledgerView.setContextMenuPolicy(Qt.CustomContextMenu)
      self.ledgerView.customContextMenuRequested.connect(self.showContextMenuLedger)


      # Setup the details tab
      self.tabDetails = QWidget()
      layoutDetails = QHBoxLayout()
      layoutDetails.addWidget(frmManageBtns)
      layoutDetails.addWidget(self.txtLockboxInfo, 1)
      self.tabDetails.setLayout(layoutDetails)

      # Setup the ledger tab
      self.tabLedger = QWidget()
      layoutLedger = QHBoxLayout()
      layoutLedger.addWidget(self.ledgerView)
      self.tabLedger.setLayout(layoutLedger)

      self.tabbedDisplay = QTabWidget()
      self.tabbedDisplay.addTab(self.tabDetails, tr("Manage"))
      self.tabbedDisplay.addTab(self.tabLedger, tr("Transactions"))




      splitter = QSplitter()
      splitter.setOrientation(Qt.Vertical)
      splitter.addWidget(self.lboxView)
      splitter.addWidget(self.tabbedDisplay)
      splitter.setStretchFactor(0, 1)
      splitter.setStretchFactor(0, 2)

      layout = QGridLayout()
      layout.addWidget(frmDescr,            0,0,  1,2)
      layout.addWidget(splitter,            1,0,  1,2)
      layout.addWidget(frmDone,             2,0,  1,2)

      layout.setRowStretch(1, 1)
      self.setLayout(layout)

      self.setMinimumWidth(700)
      self.updateButtonDisable()

      hexgeom  = self.main.settings.get('LockboxGeometry')
      tblgeom  = self.main.settings.get('LockboxAddrCols')
      ledggeom = self.main.settings.get('LockboxLedgerCols')

      if len(hexgeom) > 0:
         geom = QByteArray.fromHex(hexgeom)
         self.restoreGeometry(geom)
      if len(tblgeom) > 0:
         restoreTableView(self.lboxView, tblgeom)
      if len(ledggeom) > 0:
         restoreTableView(self.ledgerView, ledggeom)

   #############################################################################
   def updateTxCommentFromView(self, view):
      index = view.selectedIndexes()[0]
      row, col = index.row(), index.column()
      currComment = str(view.model().index(row, LEDGERCOLS.Comment).data().toString())

      dialog = DlgSetComment(self, self.main, currComment, 'Transaction')
      if dialog.exec_():
         newComment = str(dialog.edtComment.text())
         # Need to figure out where to store the comment

   #############################################################################
   def dblClickLedger(self, index):
      if index.column()==LEDGERCOLS.Comment:
         self.updateTxCommentFromView(self.ledgerView)
      else:
         self.showLedgerTx()
   
   #############################################################################
   def showLedgerTx(self):
      row = self.ledgerView.selectedIndexes()[0].row()
      txHash = str(self.ledgerView.model().index(row, LEDGERCOLS.TxHash).data().toString())
      wltID  = str(self.ledgerView.model().index(row, LEDGERCOLS.WltID).data().toString())
      txtime = unicode(self.ledgerView.model().index(row, LEDGERCOLS.DateStr).data().toString())

      pytx = None
      txHashBin = hex_to_binary(txHash)
      if TheBDM.isInitialized():
         cppTx = TheBDM.getTxByHash(txHashBin)
         if cppTx.isInitialized():
            pytx = PyTx().unserialize(cppTx.serialize())

      if pytx==None:
         QMessageBox.critical(self, 'Invalid Tx:',
         'The transaction you requested be displayed does not exist in '
         'in Armory\'s database.  This is unusual...', QMessageBox.Ok)
         return

      # Need get the wallet to display this info
      # DlgDispTxInfo( pytx, ????, self, self.main, txtime=txtime).exec_()
   
   #############################################################################
   def showContextMenuLedger(self):
      menu = QMenu(self.ledgerView)

      if len(self.ledgerView.selectedIndexes())==0:
         return

      actViewTx     = menu.addAction("View Details")
      actViewBlkChn = menu.addAction("View on www.blockchain.info")
      actComment    = menu.addAction("Change Comment")
      actCopyTxID   = menu.addAction("Copy Transaction ID")
      row = self.ledgerView.selectedIndexes()[0].row()
      action = menu.exec_(QCursor.pos())

      txHash = str(self.ledgerView.model().index(row, LEDGERCOLS.TxHash).data().toString())
      txHash = hex_switchEndian(txHash)
      wltID  = str(self.ledgerView.model().index(row, LEDGERCOLS.WltID).data().toString())

      blkchnURL = 'https://blockchain.info/tx/%s' % txHash

      if action==actViewTx:
         self.showLedgerTx()
      elif action==actViewBlkChn:
         try:
            webbrowser.open(blkchnURL)
         except:
            LOGEXCEPT('Failed to open webbrowser')
            QMessageBox.critical(self, 'Could not open browser', \
               'Armory encountered an error opening your web browser.  To view '
               'this transaction on blockchain.info, please copy and paste '
               'the following URL into your browser: '
               '<br><br>%s' % blkchnURL, QMessageBox.Ok)
      elif action==actCopyTxID:
         clipb = QApplication.clipboard()
         clipb.clear()
         clipb.setText(txHash)
      elif action==actComment:
         self.updateTxCommentFromView(self.ledgerView)

         
   #############################################################################
   def showLboxContextMenu(self, pos):
      menu = QMenu(self.lboxView)
      std = (self.main.usermode == USERMODE.Standard)
      adv = (self.main.usermode == USERMODE.Advanced)
      dev = (self.main.usermode == USERMODE.Expert)

      if True:  actionCopyAddr = menu.addAction("Copy P2SH Address")
      if True:  actionShowQRCode = menu.addAction("Display P2SH Address QR Code")
      if True:  actionBlkChnInfo = menu.addAction("View P2SH Address on www.blockchain.info")
      if True:  actionReqPayment = menu.addAction("Request Payment to this P2SH Address")
      if dev:   actionCopyHash160 = menu.addAction("Copy Hash160 (hex)")
      if dev:   actionCopyPubKey  = menu.addAction("Copy Lock Box ID")
      if True:  actionCopyBalance = menu.addAction("Copy Balance")
      idx = self.lboxView.selectedIndexes()[0]
      action = menu.exec_(QCursor.pos())


      # Get data on a given row, easily
      def getModelStr(col):
         model = self.lboxView.model()
         qstr = model.index(idx.row(), col).data().toString()
         return str(qstr).strip()


      lboxId = getModelStr(LOCKBOXCOLS.ID)
      lbox = self.main.getLockboxByID(lboxId)
      p2shAddr = script_to_addrStr(script_to_p2sh_script(lbox.binScript)) if lbox else None

      if action == actionCopyAddr:
         clippy = p2shAddr
      elif action == actionBlkChnInfo:
         try:
            import webbrowser
            blkchnURL = 'https://blockchain.info/address/%s' % p2shAddr
            webbrowser.open(blkchnURL)
         except:
            QMessageBox.critical(self, 'Could not open browser', \
               'Armory encountered an error opening your web browser.  To view '
               'this address on blockchain.info, please copy and paste '
               'the following URL into your browser: '
               '<br><br>%s' % blkchnURL, QMessageBox.Ok)
         return
      elif action == actionShowQRCode:
         DlgQRCodeDisplay(self, self.main, p2shAddr, p2shAddr, createLockboxEntryStr(lboxId)).exec_()
         return
      elif action == actionReqPayment:
         DlgRequestPayment(self, self.main, p2shAddr).exec_()
         return
      elif dev and action == actionCopyHash160:
         clippy = binary_to_hex(addrStr_to_hash160(p2shAddr)[1])
      elif dev and action == actionCopyPubKey:
         clippy = lboxId
      elif action == actionCopyBalance:
         clippy = getModelStr(LOCKBOXCOLS.Balance)
      else:
         return

      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(clippy).strip())

   #############################################################################
   def updateButtonDisable(self):
      noSelection = (self.getSelectedLBID() is None)
      isOffline = (not TheBDM.getBDMState()=='BlockchainReady')

      self.btnEdit.setDisabled(noSelection)
      self.btnExport.setDisabled(noSelection)
      self.btnDelete.setDisabled(noSelection)

      self.btnFundIt.setDisabled(noSelection or isOffline)
      self.btnSpend.setDisabled(noSelection)
      
   #############################################################################
   def getSelectedLBID(self):
      selection = self.lboxView.selectedIndexes()
      if len(selection)==0:
         return None
      row = selection[0].row()
      idCol = LOCKBOXCOLS.ID
      return str(self.lboxView.model().index(row, idCol).data().toString())

   #############################################################################
   def getSelectedLockbox(self):
      lbID = self.getSelectedLBID()
      if lbID:
         return self.main.getLockboxByID(lbID)
      return None



   #############################################################################
   def singleClickLockbox(self, index=None, *args):
      lb = self.getSelectedLockbox()
      if lb:
         self.txtLockboxInfo.setPlainText(lb.getDisplayPlainText())
      else:
         self.txtLockboxInfo.setPlainText('')

      self.updateButtonDisable()


   #############################################################################
   def dblClickLockbox(self, index, *args):
      lb = self.getSelectedLockbox()
      if lb:
         DlgLockboxEditor(self, self.main, loadBox=lb).exec_()
         self.lboxModel.reset()
         self.singleClickLockbox()


   #############################################################################
   def doCreate(self):
      dlg = DlgLockboxEditor(self, self.main).exec_()
      if dlg:
         self.lboxModel.reset()
         self.singleClickLockbox()
      self.updateButtonDisable()
         

   #############################################################################
   def doImport(self):
      dlg = DlgImportLockbox(self, self.main)
      if dlg.exec_():
         if dlg.importedLockbox is not None:
            # FIXEME:  For now always assume fresh, restart should catch 
            #          anything in the last 2016 blocks. Or manual rescan.
            self.main.updateOrAddLockbox(dlg.importedLockbox, isFresh=True)
         self.lboxModel.reset()
         self.singleClickLockbox()
      self.updateButtonDisable()
         

   #############################################################################
   def doEdit(self):
      lb = self.getSelectedLockbox()
      DlgLockboxEditor(self, self.main, loadBox=lb).exec_()
      self.lboxModel.reset()
      self.singleClickLockbox()
      self.updateButtonDisable()

   #############################################################################
   def doExport(self):
      lb = self.getSelectedLockbox()
      DlgExportLockbox(self, self.main, lb).exec_()
      self.updateButtonDisable()

   #############################################################################
   def doDelete(self):
      lb = self.getSelectedLockbox()
      reply = QMessageBox.warning(self, tr('Confirm Delete'), tr("""
         "Removing" a lockbox does not delete any signing keys, so you 
         maintain signing authority for any coins that are sent there.     
         However, it will remove it from the list of lockboxes, and you
         will have to re-import it again later in order to send any funds
         to or from the lockbox.
         <br><br>
         Really remove this lockbox?"""), QMessageBox.Yes | QMessageBox.No) 

      if reply==QMessageBox.Yes:
         lbObj = self.getSelectedLockbox()
         self.main.removeLockbox(lbObj)
         self.lboxModel.reset()
         self.singleClickLockbox()

      self.updateButtonDisable()
   
   #############################################################################
   def doFundIt(self):

      reply = QMessageBox.warning(self, tr('[WARNING]'), tr("""
         <b><font color="%s">WARNING:</font> 
         Armory does not yet support simultaneous funding of lockboxes!</b>
         <br><br>
         If this lockbox is being used to hold escrow for multiple parties, and
         requires being funded by multiple participants, you <u>must</u> use
         a special funding process to ensure simultaneous funding.  Otherwise,
         one of the other parties may be able to scam you!  Unfortunately, 
         Armory does not yet support simultaneous funding, but will soon.
         <br><br>
         It is safe to continue in the any of the following situations:
         <ul>
            <li>You are the only one expected to fund the escrow</li>
            <li>All other parties in the escrow are fully trusted</li>
            <li>This lockbox is being used for personal savings</li>
         </ul>
         If none of the above are true, please do not continue sending
         funds to this lockbox!""") % htmlColor('TextWarn'), \
         QMessageBox.Ok | QMessageBox.Cancel)

      if not reply==QMessageBox.Ok:
         return 

      lbID = self.getSelectedLBID()
      lb = self.main.getLockboxByID(lbID)
      prefillMap = {'lockbox': lbID, 
                    'message': tr('Funding %d-of-%d') % (lb.M, lb.N) }
      
      DlgSendBitcoins(None, self, self.main, prefillMap).exec_()
      self.updateButtonDisable()


   #############################################################################
   def doSpend(self):


      dlgSpend = DlgSpendFromLockbox(self, self.main)
      dlgSpend.exec_()

      if dlgSpend.selection is None:
         return
      elif dlgSpend.selection=='Create':
         lbID = self.getSelectedLBID()
         dlg = DlgSendBitcoins(None, self, self.main, spendFromLockboxID=lbID)
         dlg.exec_()
      elif dlgSpend.selection=='Review':
         title = tr("Import Signature Collector")
         descr = tr("""
            If someone else made a transaction that you need to sign, either 
            copy and paste it into the box below, or load it from file.  Files
            containing signature-collecting data usually end with
            <i>*.sigcollect.tx</i>.""")
         ftypes = ['Signature Collectors (*.sigcollect.tx)']
         dlgImport = DlgImportAsciiBlock(self, self.main, 
                           title, descr, ftypes, UnsignedTransaction)
         dlgImport.exec_()
         if dlgImport.returnObj:
            self.accept()
            ustx = dlgImport.returnObj
            DlgMultiSpendReview(self, self.main, ustx).exec_()

      self.updateButtonDisable()
      



   #############################################################################
   def saveGeometrySettings(self):
      self.main.writeSetting('LockboxGeometry', str(self.saveGeometry().toHex()))
      self.main.writeSetting('LockboxAddrCols', saveTableView(self.lboxView))
      self.main.writeSetting('LockboxLedgerCols', saveTableView(self.ledgerView))

   #############################################################################
   def closeEvent(self, event):
      self.saveGeometrySettings()
      super(DlgLockboxManager, self).closeEvent(event)

   #############################################################################
   def accept(self, *args):
      self.saveGeometrySettings()
      super(DlgLockboxManager, self).accept(*args)

   #############################################################################
   def reject(self, *args):
      self.saveGeometrySettings()
      super(DlgLockboxManager, self).reject(*args)
      

################################################################################
class DlgFundLockbox(ArmoryDialog):
   def __init__(self, parent, main):
      super(DlgFundLockbox, self).__init__(parent, main)
   
      self.selection = None

      lblDescr = QRichLabel(tr("""
         To spend from a multi-sig lockbox, one party/device must create
         a proposed spending transaction, then all parties/devices must
         review and sign that transaction.  Once it has enough signatures,
         any device, can broadcast the transaction to the network."""))

      lblCreate = QRichLabel(tr("""
         I am creating a new proposed spending transaction and will pass
         it to each party or device that needs to sign it"""))

      lblReview = QRichLabel(tr("""
         Another party or device created the transaction, I just need 
         to review and sign it."""))

      btnCreate = QPushButton(tr("Create Transaction"))
      btnReview = QPushButton(tr("Review and Sign"))
      btnCancel = QPushButton(tr("Cancel"))

      self.connect(btnCreate, SIGNAL('clicked()'), self.doCreate)
      self.connect(btnReview, SIGNAL('clicked()'), self.doReview)
      self.connect(btnCancel, SIGNAL('clicked()'), self.reject)

      frmTop = makeHorizFrame([lblDescr], STYLE_STYLED)

      layoutBot = QGridLayout()
      layoutBot.addWidget(btnReview,   0,0)
      layoutBot.addWidget(lblReview,   0,1)
      layoutBot.addWidget(HLINE(),     1,0, 1,2)
      layoutBot.addWidget(btnCreate,   2,0)
      layoutBot.addWidget(lblCreate,   2,1)

      layoutBot.setColumnStretch(0, 0)
      layoutBot.setColumnStretch(1, 1)
      frmBot = QFrame()
      frmBot.setLayout(layoutBot)
      frmBot.setFrameStyle(STYLE_STYLED)

      frmCancel = makeHorizFrame([btnCancel, 'Stretch'])

      layoutMain = QVBoxLayout()
      layoutMain.addWidget(frmTop)
      layoutMain.addWidget(frmBot)
      layoutMain.addWidget(frmCancel)
      self.setLayout(layoutMain)

      self.setMinimumWidth(500)


   def doCreate(self):
      self.selection = 'Create'
      self.accept()

   def doReview(self):
      self.selection = 'Review'
      self.accept()


################################################################################
class DlgSpendFromLockbox(ArmoryDialog):
   def __init__(self, parent, main):
      super(DlgSpendFromLockbox, self).__init__(parent, main)
   
      self.selection = None

      lblDescr = QRichLabel(tr("""
         To spend from a multi-sig lockbox, one party/device must create
         a proposed spending transaction, then all parties/devices must
         review and sign that transaction.  Once it has enough signatures,
         any device, can broadcast the transaction to the network."""))

      btnCreate = QPushButton(tr("Create Transaction"))
      btnReview = QPushButton(tr("Review and Sign"))
      btnCancel = QPushButton(tr("Cancel"))

      if TheBDM.getBDMState()=='BlockchainReady':
         lblCreate = QRichLabel(tr("""
            I am creating a new proposed spending transaction and will pass
            it to each party or device that needs to sign it"""))
      else:
         btnCreate.setEnabled(False)
         lblCreate = QRichLabel(tr("""
            Transaction creation is not available when offline."""))

      lblReview = QRichLabel(tr("""
         Another party or device created the transaction, I just need 
         to review and sign it."""))


      self.connect(btnCreate, SIGNAL('clicked()'), self.doCreate)
      self.connect(btnReview, SIGNAL('clicked()'), self.doReview)
      self.connect(btnCancel, SIGNAL('clicked()'), self.reject)

      frmTop = makeHorizFrame([lblDescr], STYLE_STYLED)

      layoutBot = QGridLayout()
      layoutBot.addWidget(btnCreate,   0,0)
      layoutBot.addWidget(lblCreate,   0,1)
      layoutBot.addWidget(HLINE(),     1,0, 1,2)
      layoutBot.addWidget(btnReview,   2,0)
      layoutBot.addWidget(lblReview,   2,1)

      layoutBot.setColumnStretch(0, 0)
      layoutBot.setColumnStretch(1, 1)

      frmBot = QFrame()
      frmBot.setLayout(layoutBot)
      frmBot.setFrameStyle(STYLE_STYLED)

      frmCancel = makeHorizFrame([btnCancel, 'Stretch'])

      layoutMain = QVBoxLayout()
      layoutMain.addWidget(frmTop,    1)
      layoutMain.addWidget(frmBot,    1)
      layoutMain.addWidget(frmCancel, 0)
      self.setLayout(layoutMain)

      self.setMinimumWidth(500)


   def doCreate(self):
      self.selection = 'Create'
      self.accept()

   def doReview(self):
      self.selection = 'Review'
      self.accept()


################################################################################
class DlgImportAsciiBlock(QDialog):
   def __init__(self, parent, main, titleStr, descrStr, fileTypes, importType):
      super(DlgImportAsciiBlock, self).__init__(parent)
      self.main = main
      self.fileTypes = fileTypes
      self.importType = importType
      self.returnObj = None

      lbl = QRichLabel(descrStr)

      self.txtAscii = QPlainTextEdit()
      self.txtAscii.setFont(GETFONT('Fixed', 9))
      w,h = relaxedSizeNChar(self.txtAscii, 80)
      self.txtAscii.setMinimumWidth(w)
      btnLoad = QPushButton(tr("Load from file"))
      btnDone = QPushButton(tr("Done"))
      btnCancel = QPushButton(tr("Cancel"))

                              
      self.connect(btnLoad,   SIGNAL('clicked()'), self.loadfile)
      self.connect(btnDone,   SIGNAL('clicked()'), self.clickedDone)
      self.connect(btnCancel, SIGNAL('clicked()'), self.reject)

      frmLoadButton = makeHorizFrame(['Stretch', btnLoad])
      frmBottomRow  = makeHorizFrame([btnCancel, 'Stretch', btnDone])

      layout = QVBoxLayout()
      layout.addWidget(lbl)
      layout.addWidget(frmLoadButton)
      layout.addWidget(self.txtAscii, 1)
      layout.addWidget(frmBottomRow)
      self.setLayout(layout)
      self.setWindowTitle(titleStr)
      self.setMinimumWidth(450)

   #############################################################################
   def loadfile(self):
      loadPath = self.main.getFileLoad(tr('Load Data'), self.fileTypes)
                                                 
      if not loadPath:
         return
      with open(loadPath) as f:
         data = f.read()
      self.txtAscii.setPlainText(data)


   #############################################################################
   def clickedDone(self):
      try:
         txt = str(self.txtAscii.toPlainText()).strip()
         self.returnObj = self.importType().unserializeAscii(txt)
      except:
         LOGEXCEPT('Error reading ASCII block')
         QMessageBox.warning(self, tr('Error'), tr("""
            There was an error reading the ASCII block entered.  Please
            make sure it was entered/copied correctly, and that you have
            copied the header and footer lines that start with "=====". """), 
            QMessageBox.Ok)
         return
         
      self.accept()


################################################################################
class DlgExportAsciiBlock(ArmoryDialog):
   def __init__(self, parent, main, exportObj, title, descr, ftypes, defaultFN):
      super(DlgExportAsciiBlock, self).__init__(parent, main)

      lblDescr = QRichLabel(descr)
      self.exportObj  = exportObj
      self.fileTypes  = ftypes
      self.defaultFN  = defaultFN
      self.asciiBlock = exportObj.serializeAscii()


      txt = QPlainTextEdit()
      txt.setFont(GETFONT('Fixed', 9))
      w,h = relaxedSizeNChar(txt, 80)
      txt.setMinimumWidth(w)
      txt.setMinimumHeight(h*9)
      txt.setPlainText(self.asciiBlock)

      self.lblCopied = QRichLabel('')
      btnCopy = QPushButton(tr("Copy to Clipboard"))
      btnSave = QPushButton(tr("Save to File"))
      btnDone = QPushButton(tr("Done"))
   
      self.connect(btnCopy, SIGNAL('clicked()'), self.clipcopy)
      self.connect(btnSave, SIGNAL('clicked()'), self.savefile)
      self.connect(btnDone, SIGNAL('clicked()'), self.accept)

      frmCopy = makeHorizFrame([btnSave, btnCopy, self.lblCopied, 'Stretch'])
      frmDone = makeHorizFrame(['Stretch', btnDone])
      frmMain = makeVertFrame([lblDescr, txt, frmCopy], STYLE_RAISED)

      layout = QVBoxLayout()
      layout.addWidget(frmMain)
      layout.addWidget(frmDone)
      self.setLayout(layout)

      self.setWindowTitle(title)
      self.setWindowIcon(QIcon(self.main.iconfile))


   def savefile(self):
      fn = self.main.getFileSave(tr('Export ASCII Block'), self.fileTypes,
                                                            self.defaultFN)
      if fn:
         with open(fn,'w') as f:
            f.write(self.asciiBlock + '\n')
         self.accept()


   def clipcopy(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(self.asciiBlock)
      self.lblCopied.setText('<i>Copied!</i>')


################################################################################
class DlgImportLockbox(QDialog):
   def __init__(self, parent, main):
      super(DlgImportLockbox, self).__init__(parent)
      self.main = main
      self.importedLockbox = None
      lbl = QRichLabel(tr("""
         <b><u>Import Lockbox</u></b>
         <br><br>
         Copy the lockbox text block from file or email into the box 
         below.  If you have a file with the lockbox in it, you can
         load it using the "Load Lockbox" button at the bottom."""))

      self.txtBoxBlock = QPlainTextEdit()
      self.txtBoxBlock.setFont(GETFONT('Fixed', 9))
      w,h = relaxedSizeNChar(self.txtBoxBlock, 80)
      self.txtBoxBlock.setMinimumWidth(w)
      btnLoad = QPushButton(tr("Load from file"))
      btnDone = QPushButton(tr("Done"))
      btnCancel = QPushButton(tr("Cancel"))

                              
      self.connect(btnLoad,   SIGNAL('clicked()'), self.loadfile)
      self.connect(btnDone,   SIGNAL('clicked()'), self.clickedDone)
      self.connect(btnCancel, SIGNAL('clicked()'), self.reject)

      frmLoadButton = makeHorizFrame(['Stretch', btnLoad])
      frmBottomRow  = makeHorizFrame([btnCancel, 'Stretch', btnDone])

      layout = QVBoxLayout()
      layout.addWidget(lbl)
      layout.addWidget(frmLoadButton)
      layout.addWidget(self.txtBoxBlock, 1)
      layout.addWidget(frmBottomRow)
      self.setLayout(layout)
      self.setWindowTitle(tr('Import Lockbox'))
      self.setMinimumWidth(450)

   #############################################################################
   def loadfile(self):
      boxPath = self.main.getFileLoad(tr('Load Lockbox'),
                                                 ['Lockboxes (*.lockbox.txt)'])
      if not boxPath:
         return
      with open(boxPath) as f:
         data = f.read()
      self.txtBoxBlock.setPlainText(data)

   #############################################################################
   def clickedDone(self):
      txt = str(self.txtBoxBlock.toPlainText()).strip()
      try:
         self.importedLockbox = MultiSigLockbox().unserializeAscii(txt)
      except:
         LOGEXCEPT('Error unserializing the entered text')
         return
         
      lbID = self.importedLockbox.uniqueIDB58
      if not self.main.getLockboxByID(lbID) is None:
         reply = QMessageBox.warning(self, tr("Duplicate Lockbox"), tr("""
            You just attempted to import a lockbox with ID, %s.  This
            lockbox is already in your available list of lockboxes.
            <br><br>
            Even with the same ID, the lockbox information 
            may be different.  Would you like to overwrite the lockbox
            information already stored for %s?""") % (lbID,lbID), \
            QMessageBox.Yes | QMessageBox.Cancel)

         if not reply==QMessageBox.Yes:
            return

      self.accept()


################################################################################
def createContribBlock(self, msScript, walletID, amt, fee=0):

   pass 


################################################################################
class DlgConfirmLockbox(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, msScript):
      super(DlgConfirmLockbox, self).__init__(parent, main)

      



################################################################################
class DlgContributeFundLockbox(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, msScript):
      super(DlgContributeFundLockbox, self).__init__(parent, main)




################################################################################
class DlgMultiSpendReview(ArmoryDialog):
   """
   ASSUMPTION q38JmNa5:  USTX has no inputs other than a single lockbox
                         (though that lockbox may have multiple UTXOs)

   Of course, we will eventually expand this to handle more diverse types
   of multi-spend transactions, but for now we had to iron out this common
   case before doing more complex things
   """

   #############################################################################
   def __init__(self, parent, main, ustx):
      super(DlgMultiSpendReview, self).__init__(parent, main)


      lblDescr = QRichLabel(tr("""
         The following transaction is a proposed spend of funds controlled
         by multiple parties.  The keyholes next to each input represent 
         required signatures for the tx to be valid.  White
         means it has not yet been signed, and cannot be signed by you.  Green
         represents signatures that can be added by one of your wallets.
         Gray keyholes are already signed.Untitled
         <br><br>
         Change outputs have been hidden where it is obvious (such as coins
         returning to the same lockbox from where it came).  If there is 
         any ambiguity, Armory will display all outputs."""))

      KEYW = 25
      KEYH = 36
      CHKW = 32
      CHKH = 32
      PIEW = 32
      PIEH = 32


      # These need to return copies
      self.pixGreen = lambda: QPixmap(':/keyhole_green.png').scaled(KEYW,KEYH)
      self.pixGray  = lambda: QPixmap(':/keyhole_gray.png' ).scaled(KEYW,KEYH)
      self.pixBlue  = lambda: QPixmap(':/keyhole_blue.png' ).scaled(KEYW,KEYH)
      self.pixWhite = lambda: QPixmap(':/keyhole_white.png').scaled(KEYW,KEYH)
      self.pixRed   = lambda: QPixmap(':/keyhole_red.png'  ).scaled(KEYW,KEYH)
      self.pixChk   = lambda: QPixmap(':/checkmark32.png'  ).scaled(CHKW,CHKH)
      self.pixPie   = lambda m: QPixmap(':/frag%df.png'%m  ).scaled(PIEW,PIEH)

      layout = QVBoxLayout()

      #self.lboxID = lboxID
      #self.lbox   = self.main.getLockboxByID(lboxID)
      self.ustx = UnsignedTransaction().unserialize(ustx.serialize())
      self.feeAmt = self.ustx.calculateFee()


      # Some simple container classes
      class InputBundle(object):
         def __init__(self):
            self.binScript = ''
            self.sendAmt = 0
            self.dispStr = ''
            self.ustxiList = []
            self.lockbox = None
            self.wltOfflineSign = []
            self.wltSignRightNow = []
            self.keyholePixmap = []

      # Some simple container classes
      class OutputBundle(object):
         def __init__(self):
            self.recvAmt = 0
            self.dispStr = ''
            self.lockbox = None
            self.wltID = None

      
      self.inputBundles = {}
      self.outputBundles = {}

      # NOTE:  This will do some weird things if we have a contrib that 
      #        gets back more than he puts in... i.e. he will be required
      #        to sign, but he will be receiving money, instead of sending
      #        it.  Right now, if that happens, he will show up as an 
      #        input bundle with a negative send amount

      # Accumulate and prepare all static info (that doesn't change with sigs)
      self.maxN = 0
      for ustxi in self.ustx.ustxInputs:
         hrStr,idStr = self.main.getContribStr(ustxi.txoScript, ustxi.contribID)

         iBundle = self.inputBundles.setdefault(idStr, InputBundle())
         iBundle.ustxiList.append(ustxi)
         iBundle.sendAmt += ustxi.value
         iBundle.dispStr = hrStr
         if not idStr[:2] in ['LB']:
            LOGERROR('Something other than a lockbox on input side')
            QMessageBox.critical(self, tr('Non-lockbox'), tr("""
               You loaded a transaction that is more complex that just
               spending from a single lockbox.  Armory does not currently
               handle this condition.  <br><br>
               This error can occur when you attempt to spend multi-signature
               coins for which you have not imported the appropriate lockbox
               information.  Please have the party that created the lockbox
               export it for you, and then you can import it in the lockbox
               manager.  <br><br>
               Input that failed:  %s""") % hrStr, QMessageBox.Ok)
            self.reject()

         # (ASSUMPTION q38JmNa5) Take note of which lockbox this is
         iBundle.lockbox = self.main.getLockboxByID(idStr.split(':')[-1])

         # (ASSUMPTION q38JmNa5)
         # Check whether we have the capability to sign this lockbox
         iBundle.binScript = iBundle.lockbox.binScript
         M,N = iBundle.lockbox.M, iBundle.lockbox.N
         self.maxN = max(N, self.maxN)
         iBundle.wltOfflineSign  = [None]*N
         iBundle.wltSignRightNow = [None]*N
         iBundle.keyholePixmap   = [None]*N
         for i in range(N):
            a160 = iBundle.lockbox.a160List[i]
            wltID = self.main.getWalletForAddr160(a160)
            iBundle.keyholePixmap[i] = QLabel()
            iBundle.keyholePixmap[i].setPixmap(self.pixWhite())
            if wltID:
               wlt = self.main.walletMap[wltID]
               wltType = determineWalletType(wlt, self.main)[0]
               if wltType in [WLTTYPES.WatchOnly, WLTTYPES.Offline]:
                  iBundle.wltOfflineSign[i] = [wltID, a160]
               else:
                  iBundle.wltSignRightNow[i] = [wltID, a160]
                  iBundle.keyholePixmap[i].setPixmap(self.pixGreen())
               

      # The output bundles are quite a bit simpler 
      for dtxo in self.ustx.decorTxOuts:
         hrStr,idStr = self.main.getContribStr(dtxo.binScript, dtxo.contribID)
         if idStr in self.inputBundles:
            self.inputBundles[idStr].sendAmt -= dtxo.value
         else:
            oBundle = self.outputBundles.setdefault(idStr, OutputBundle())
            oBundle.recvAmt += dtxo.value
            oBundle.dispStr = hrStr
            if idStr.startswith('LB:'):
               oBundle.lockbox = self.main.getLockboxByID(idStr.split(':')[-1])

            

      layoutInputs  = QGridLayout()
      layoutOutputs = QGridLayout()

      self.iWidgets = {}
      self.oWidgets = {}


      iin = 0
      iout = 0
      for idStr in self.inputBundles:
         self.iWidgets[idStr] = {}
         iWidgMap = self.iWidgets[idStr]
         topRow = (self.maxN+1)*iin
         iin += 1

         ib = self.inputBundles[idStr]

         iWidgMap['HeadLbl'] = QRichLabel(tr("""
            <b><u>Spending:</u> <font color="%s">%s</b></font>""") % \
            (htmlColor('TextBlue'), self.inputBundles[idStr].dispStr), \
            doWrap=False)
         val = self.inputBundles[idStr].sendAmt
         iWidgMap['Amount'] = QMoneyLabel(-val, txtSize=12, wBold=True)

         # These are images that show up to N=5
         iWidgMap['HeadImg'] = [None]*self.maxN
         iWidgMap['KeyImg']  = [None]*self.maxN
         iWidgMap['KeyLbl']  = [None]*self.maxN
         iWidgMap['ChkImg']  = [None]*self.maxN
         iWidgMap['SignBtn']  = [None]*self.maxN

         for i in range(self.maxN):
            iWidgMap['HeadImg'][i] = QLabel()
            iWidgMap['KeyImg' ][i] = QLabel()
            iWidgMap['KeyLbl' ][i] = QRichLabel('', doWrap=False)
            iWidgMap['ChkImg' ][i] = QLabel()
            iWidgMap['SignBtn'][i] = QPushButton('')
         
            iWidgMap['ChkImg'][i].setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

         # Now actually insert the widgets into a layout
         headerLine = [iWidgMap['HeadLbl']]
         headerLine.extend(iWidgMap['HeadImg'])
         headerLine.append('Stretch')
         headerLine.append(iWidgMap['Amount'])
         layoutInputs.addWidget(makeHorizFrame(headerLine), topRow,0, 1,4)

         def createSignCallback(idstring, nIdx):
            def doSign():
               self.doSignForInput(idstring, nIdx)
            return doSign


         for i in range(self.maxN):
            row = topRow + 1 + i
            layoutInputs.addItem(QSpacerItem(20,20),       row,0)
            layoutInputs.addWidget(iWidgMap['SignBtn'][i], row,1)
            layoutInputs.addWidget(iWidgMap['ChkImg' ][i], row,1)
            layoutInputs.addWidget(iWidgMap['KeyImg' ][i], row,2)
            layoutInputs.addWidget(iWidgMap['KeyLbl' ][i], row,3)

            self.connect(iWidgMap['SignBtn'][i], SIGNAL('clicked()'), \
                                           createSignCallback(idStr, i))

            # (ASSUMPTION q38JmNa5)
            lbox = self.inputBundles[idStr].lockbox
            if i >= lbox.N:
               iWidgMap['SignBtn'][i].setVisible(False)
               iWidgMap['KeyImg' ][i].setVisible(False)
               iWidgMap['KeyLbl' ][i].setVisible(False)
               iWidgMap['ChkImg' ][i].setVisible(False)
            else:
               comm = lbox.commentList[i]

               wltID = ''
               if iBundle.wltOfflineSign[i]:
                  wltID = iBundle.wltOfflineSign[i][0]
               if iBundle.wltSignRightNow[i]:
                  wltID = iBundle.wltSignRightNow[i][0]

               wltName = '' 
               if wltID:
                  wltName = self.main.walletMap[wltID].getDisplayStr()

               if not comm:
                  if not wltName:
                     dispStr = tr('[[Unknown Signer]]') 
                  else:
                     dispStr = wltName
               else:
                  if not wltName:
                     dispStr = comm
                  else:
                     dispStr = '%s [%s]' % (comm,wltName)
               iWidgMap['KeyLbl' ][i].setText(dispStr)

               iWidgMap['HeadImg'][i].setPixmap(self.pixPie(lbox.M))
               iWidgMap['KeyImg' ][i].setMinimumSize(KEYW,KEYH)
               iWidgMap['ChkImg' ][i].setMinimumSize(CHKW,CHKH)
               iWidgMap['KeyLbl' ][i].setWordWrap(False)
   
            

         for widgetName,widgetList in iWidgMap.iteritems():
            if widgetName in ['HeadLbl', 'Amount']:
               continue

            for i in range(self.maxN):
               lockbox = self.inputBundles[idStr].lockbox
               if i>= lockbox.N:
                  widgetList[i].setVisible(False)
            

      layoutInputs.setColumnStretch(0,0)
      layoutInputs.setColumnStretch(1,0)
      layoutInputs.setColumnStretch(2,0)
      layoutInputs.setColumnStretch(3,1)
      layoutInputs.setColumnStretch(4,0)


      # Maybe one day we'll do full listing of lockboxes on the output side
      # But for now, it will only further complicate things...
      for idStr in self.outputBundles:

         self.oWidgets[idStr] = {}
         oWidgMap = self.oWidgets[idStr]
         topRow = (self.maxN+1)*iout
         iout += 1


         oWidgMap['HeadLbl'] = QRichLabel(tr("""
            <b><u>Receiving:</u>  <font color="%s">%s</font></b>""") % \
            (htmlColor('TextBlue'), self.outputBundles[idStr].dispStr), \
            doWrap=False)
         val = self.outputBundles[idStr].recvAmt
         oWidgMap['Amount'] = QMoneyLabel(val, txtSize=12, wBold=True)

         # These are images that show up to N=3
         oWidgMap['HeadImg'] = [None]*self.maxN
         for i in range(self.maxN):
            oWidgMap['HeadImg'][i] = QLabel()


         # Now actually insert the widgets into a layout
         headerLine = [oWidgMap['HeadLbl']]
         headerLine.extend(oWidgMap['HeadImg'])
         headerLine.append('Stretch')
         headerLine.append(oWidgMap['Amount'])
         layoutOutputs.addWidget(makeHorizFrame(headerLine), topRow,0, 1,5)

         lbox = self.outputBundles[idStr].lockbox
         if lbox is None:
            M,N = 1,1
         else:
            M,N = lbox.M, lbox.N
            for i in range(self.maxN):
               if i < N:
                  oWidgMap['HeadImg'][i].setPixmap(self.pixPie(M))
                  oWidgMap['HeadImg'][i].setMinimumSize(KEYW,KEYH)
            


      # Add a fee row if needed
      if self.feeAmt > 0:
         row = (self.maxN+1)*iout
         lblFee = QRichLabel('<b>Transaction Fee</b>')
         lblAmt = QMoneyLabel(self.feeAmt, txtSize=12, wBold=True)

         frmTxFee = makeHorizFrame([lblFee, 'Stretch', lblAmt])
         layoutOutputs.addWidget(HLINE(),   row,0,   1,5)
         layoutOutputs.addWidget(frmTxFee,  row+1,0, 1,5)
         
                  

      frmInputs = QFrame()
      frmInputs.setLayout(layoutInputs)
      frmInputs.setFrameStyle(STYLE_STYLED)

      frmOutputs = QFrame()
      frmOutputs.setLayout(layoutOutputs)
      frmOutputs.setFrameStyle(STYLE_STYLED)



      self.btnLoadImport  = QPushButton(tr('Load/Import'))
      self.lblFinalMsg    = QRichLabel('')
      self.lblFinalChk    = QLabel()
      self.btnFinalBroad  = QPushButton(tr('Broadcast'))
      self.btnFinalExport = QPushButton(tr('Export'))
      self.lblFinalChk.setMinimumSize(CHKW,CHKH)
      layoutBtns = QHBoxLayout()
      layoutBtns.addWidget(self.btnLoadImport)
      layoutBtns.addStretch()
      layoutBtns.addWidget(self.lblFinalMsg, 1)
      layoutBtns.addWidget(self.lblFinalChk)
      layoutBtns.addWidget(self.btnFinalBroad)
      layoutBtns.addWidget(self.btnFinalExport)
      frmButtons = QFrame()
      frmButtons.setLayout(layoutBtns)

      self.connect(self.btnLoadImport,  SIGNAL('clicked()'), self.doImport)
      self.connect(self.btnFinalBroad,  SIGNAL('clicked()'), self.doBroadcast)
      self.connect(self.btnFinalExport, SIGNAL('clicked()'), self.doExport)

      frmMain = makeVertFrame([lblDescr, 
                               HLINE(),
                               HLINE(),
                               frmInputs,
                               HLINE(),
                               HLINE(),
                               frmOutputs,
                               HLINE(),
                               frmButtons])

      # Actually, this dialog will not handle changing USTX objects yet
      # For now, need to pre-select your USTX, then load this dialog with it
      #self.btnLoadImport.setVisible(False)


      layoutMain = QVBoxLayout()
      layoutMain.addWidget(frmMain)
      self.setLayout(layoutMain)

      self.setMinimumWidth(750)
      
      # Evaluate SigningStatus returns per-wallet details if a wlt is given
      self.relevancyMap  = {}
      self.canSignMap    = {}
      self.alreadySigned = {}
      self.evalSigStat()

      
   
         
   ############################################################################# 
   def doSignForInput(self, idStr, keyIdx):
      ib = self.inputBundles[idStr]
      wltID, a160 = ib.wltSignRightNow[keyIdx]
      wlt = self.main.walletMap[wltID]
      pytx = self.ustx.pytxObj
      if wlt.useEncryption and wlt.isLocked:
         dlg = DlgUnlockWallet(wlt, self, self.main, 'Sign Lockbox')
         if not dlg.exec_():
            QMessageBox.critical(self, 'Wallet is locked',
               'Cannot sign this lockbox without unlocking wallet!', 
               QMessageBox.Ok)
            return

         
      for ustxi in ib.ustxiList:
         addrObj = wlt.getAddrByHash160(a160)
         ustxi.createAndInsertSignature(pytx, addrObj.binPrivKey32_Plain)

      self.evalSigStat()
      
   ############################################################################# 
   def evalSigStat(self):
      self.relevancyMap  = {}
      self.canSignMap    = {}
      self.alreadySigned = {}

      for wltID,pyWlt in self.main.walletMap.iteritems():
         txss = self.ustx.evaluateSigningStatus(pyWlt.cppWallet)
         self.relevancyMap[wltID]  = txss.wltIsRelevant
         self.canSignMap[wltID]    = txss.wltCanSign
         self.alreadySigned[wltID] = txss.wltAlreadySigned

      #class InputBundle(object):
         #def __init__(self):
            #self.binScript = ''
            #self.sendAmt = 0
            #self.dispStr = ''
            #self.ustxiList = []
            #self.lockbox = None
            #self.wltOfflineSign = []
            #self.wltSignRightNow = []
            #self.keyholePixmap = []

      # This is complex, for sure.  
      #    The outermost loop goes over all inputs and outputs
      #    Then goes over all N public keys
      for idStr,ib in self.inputBundles.iteritems():
         iWidgMap = self.iWidgets[idStr]

         # (ASSUMPTION q38JmNa5) Only one type of input, a single lockbox
         #                       (therefore only need to examine first ustxi)
         # Since we are calling this without a wlt, each key state can only
         # be either ALREADY_SIGNED or NO_SIGNATURE (no WLT* possible)
         isigstat = ib.ustxiList[0].evaluateSigningStatus()

         for i in range(ib.lockbox.N):
            signBtn = iWidgMap['SignBtn'][i]
            chkLbl  = iWidgMap['ChkImg'][i]
            keyImg  = iWidgMap['KeyImg'][i]
            if isigstat.statusN[i]==TXIN_SIGSTAT.ALREADY_SIGNED:
               chkLbl.setVisible(True)
               chkLbl.setPixmap(self.pixChk())
               signBtn.setEnabled(False)
               signBtn.setVisible(False)
               signBtn.setText(tr('Done!'))
               keyImg.setPixmap(self.pixGray())
            elif ib.wltSignRightNow[i]:
               chkLbl.setVisible(False)
               chkLbl.setPixmap(QPixmap())
               signBtn.setVisible(True)
               signBtn.setEnabled(True)
               signBtn.setText('Sign')
               keyImg.setPixmap(self.pixGreen())
            elif ib.wltOfflineSign[i]:
               wltID = ib.wltOfflineSign[i][0]
               wlt = self.main.walletMap[wltID]
               wltType = determineWalletType(wlt, self.main)[0]
               if wltType==WLTTYPES.WatchOnly:
                  chkLbl.setVisible(False)
                  chkLbl.setPixmap(QPixmap())
                  signBtn.setVisible(False)
                  signBtn.setEnabled(False)
                  signBtn.setText('Offline')
                  keyImg.setPixmap(self.pixWhite())
               elif wltType==WLTTYPES.Offline:
                  chkLbl.setVisible(False)
                  chkLbl.setPixmap(QPixmap())
                  signBtn.setVisible(True)
                  signBtn.setEnabled(False)
                  signBtn.setText('Offline')
                  keyImg.setPixmap(self.pixWhite())
            else:
               chkLbl.setPixmap(QPixmap())
               chkLbl.setVisible(False)
               signBtn.setVisible(True)
               signBtn.setVisible(False)
               keyImg.setPixmap(self.pixWhite())
               signBtn.setVisible(False)

      # Now modify the window/buttons based on the whole transaction state
      # (i.e. Can broadcast, etc)
      extraTxt = tr('')
      if not self.main.netMode == NETWORKMODE.Full:
         extraTxt = tr("""
            from any online computer (you are currently offline)""")

      txss = self.ustx.evaluateSigningStatus()
      if txss.canBroadcast:
         self.lblFinalMsg.setText(tr("""
         <font color="%s">This transaction has enough signatures and 
         can be broadcast %s</font>""") % (htmlColor('TextGreen'), extraTxt))
         self.btnFinalBroad.setVisible(True)
         self.btnFinalBroad.setEnabled(self.main.netMode == NETWORKMODE.Full)
         self.btnFinalExport.setVisible(True)
         self.btnFinalExport.setEnabled(True)
         self.lblFinalChk.setPixmap(self.pixChk())
      else:
         self.lblFinalMsg.setText( tr("""
            <font color="%s">This transaction is incomplete.  You can
            add signatures then export and give to other parties or
            devices to sign.</font>""") % htmlColor('TextWarn'))
         self.btnFinalBroad.setVisible(False)
         self.btnFinalBroad.setEnabled(False)
         self.btnFinalExport.setVisible(True)
         self.btnFinalExport.setEnabled(True)
         self.lblFinalChk.setPixmap(QPixmap())

      

   def doExport(self):
      #class DlgExportAsciiBlock(ArmoryDialog):
      #def __init__(self, parent, main, exportObj, title, descr, fileTypes, defaultFN)
      title = tr("Export Signature Collector")
      descr = tr("""
         The text below includes all data about this multi-sig transaction, 
         including all the signatures already made to it.  It contains 
         everything needed to securely review and sign it, including offline 
         devices/wallets.  
         <br><br>
         If this transaction requires signatures from multiple parties, it is
         safe to send this data via email or USB key.  No data is included 
         that would compromise the security of any of the signing devices.""")
      ftypes = ['Signature Collectors (*.sigcollect.tx)']
      defaultFN = 'MultikeyTransaction_%s.sigcollect.tx' % self.ustx.uniqueIDB58
         
      DlgExportAsciiBlock(self, self.main, self.ustx, title, descr, 
                                                    ftypes, defaultFN).exec_()

   
   def doImport(self):
      title = tr("Import Signature Collector")
      descr = tr("""
         Load a multi-sig transaction for review, signing and/or broadcast.  
         If any of your loaded wallets can sign for any transaction inputs,
         you will be able to execute the signing for each one.  If your 
         signature completes the transaction, you can then broadcast it to
         finalize it.""")
      ftypes = ['Signature Collectors (*.sigcollect.tx)']
      importType = self.ustx.__class__

      dlg = DlgImportAsciiBlock(self, self.main, title, descr, ftypes, importType)
      if dlg.exec_():
         # FIXME: This is a serious hack because I didn't have time to implement
         #        reloading an existing dialog with a new USTX, so I just recurse
         #        for now (it's because all the layouts are set in the __init__
         #        function, etc...
         self.accept() 
         DlgMultiSpendReview(self.parent, self.main, dlg.returnObj).exec_()


   def doBroadcast(self):
      finalTx = self.ustx.prepareFinalTx(doVerifySigs=True)
      if not finalTx:
         self.ustx.evaluateSigningStatus().pprint()
         QMessageBox.critical(self, tr('Invalid Signatures'), tr("""
            Somehow not all inputs have valid sigantures!  You can choose  
            to attempt to broadcast anyway, in case you think Armory is
            not evaluating the transaction state correctly.  
            <br><br>
            Otherwise, please confirm that you have created signatures 
            from the correct wallets.  Perhaps try collecting signatures
            again...?"""), QMessageBox.Ok)

         finalTx = self.ustx.prepareFinalTx(doVerifySigs=False)

      self.main.broadcastTransaction(finalTx, withOldSigWarning=False)
      try:
         self.parent.tabbedDisplay.setCurrentIndex(1)
      except:
         LOGEXCEPT('Failed to switch parent tabs')
      self.accept()
         




################################################################################
class DlgSelectMultiSigOption(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main):
      super(DlgSelectMultiSigOption, self).__init__(parent, main)

      self.btnCreate = QPushButton(tr('Create/Manage lockboxes'))
      #self.btnImport = QPushButton(tr('Import multi-sig lockbox'))
      self.btnFund   = QPushButton(tr('Fund a lockbox'))
      self.btnSpend  = QPushButton(tr('Spend from a lockbox'))

      lblDescr  = QRichLabel(tr("""
         <font color="%s" size=5><b>Multi-Sig Lockboxes 
         [EXPERIMENTAL]</b></font>""") % htmlColor('TextBlue'), 
         hAlign=Qt.AlignHCenter, doWrap=False)

      lblDescr2 = QRichLabel(tr("""
         The buttons below link you to all the functionality needed to 
         create, fund and spend from multi-sig "lockboxes."  This 
         includes turning multiple wallets into a multi-factor lock-box
         for your personal coins, or can be used for escrow between
         multiple parties, using the Bitcoin network itself to hold the
         escrow.
         <br><br>
         <b><u>IMPORTANT:</u></b>  If you are using an lockbox that requires
         being funded by multiple parties simultaneously, you should 
         <b><u>not</u> </b> use regular transactions to do the funding.  
         You should use the third button labeled "Fund a multi-sig lockbox" 
         to collect funding promises into a single transaction, to limit 
         the ability of any party to scam you.  Read more about it by
         clicking [NO LINK YET]  (if the above doesn't hold, you can use
         the regular "Send Bitcoins" dialog to fund the lockbox)."""))


      self.lblCreate = QRichLabel(tr("""
         Collect public keys to create an "address" that can be used 
         to send funds to the multi-sig container"""))
      #self.lblImport = QRichLabel(tr("""
         #If someone has already created the lockbox you can add it 
         #to your lockbox list"""))
      self.lblFund = QRichLabel(tr("""
         Send money to an lockbox simultaneously with other 
         parties involved in the lockbox"""))
      self.lblSpend = QRichLabel(tr("""
         Collect signatures to authorize transferring money out of 
         a multi-sig lockbox"""))


      self.connect(self.btnCreate,  SIGNAL('clicked()'), self.openCreate)
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
      layoutBottom.addItem(QSpacerItem(10,10),    0,0,  5,1)
      layoutBottom.addItem(QSpacerItem(10,10),    0,6,  5,1)

      layoutBottom.addItem(QSpacerItem(10,10),    0,1)
      layoutBottom.addItem(QSpacerItem(10,10),    2,1)
      layoutBottom.addItem(QSpacerItem(10,10),    4,1)

      layoutBottom.addWidget(self.btnCreate,      0,2)
      layoutBottom.addWidget(self.btnFund,        2,2)
      layoutBottom.addWidget(self.btnSpend,       4,2)

      layoutBottom.addItem(QSpacerItem(10,10),    0,3)
      layoutBottom.addItem(QSpacerItem(10,10),    2,3)
      layoutBottom.addItem(QSpacerItem(10,10),    4,3)

      layoutBottom.addWidget(self.lblCreate,      0,4)
      layoutBottom.addWidget(self.lblFund,        2,4)
      layoutBottom.addWidget(self.lblSpend,       4,4)

      layoutBottom.addItem(QSpacerItem(10,10),    0,5)
      layoutBottom.addItem(QSpacerItem(10,10),    2,5)
      layoutBottom.addItem(QSpacerItem(10,10),    4,5)

      layoutBottom.addWidget(HLINE(),             1,1,  1,4)
      layoutBottom.addWidget(HLINE(),             3,1,  1,4)

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
      self.setWindowTitle(tr('Multi-Sig Lockboxes [EXPERIMENTAL]'))
      


   #############################################################################
   def openCreate(self):
      DlgLockboxEditor(self, self.main).exec_()

   #############################################################################
   def openFund(self):
      DlgFundLockbox(self, self.main).exec_()

   #############################################################################
   def openSpend(self):
      DlgSpendFromLockbox(self, self.main).exec_()
