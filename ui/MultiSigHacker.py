from PyQt4.Qt import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from qtdefines import *
from qtdialogs import createAddrBookButton, DlgSetComment, DlgSendBitcoins
from armoryengine.ALL import *
from armorymodels import *
from armoryengine.MultiSigUtils import MultiSigLockbox, calcLockboxID
from ui.MultiSigModels import \
            LockboxDisplayModel,  LockboxDisplayProxy, LOCKBOXCOLS

         




#############################################################################
class DlgLockboxEditor(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, maxM=5, maxN=5, loadBox=None):
      super(DlgLockboxEditor, self).__init__(parent, main)

      lblDescr = QRichLabel(tr("""
         <b><u><font size=5 color="%s">Multi-key is an experimental 
         feature!</font></u>  
         <br><br>
         Please do not use this with money you cannot afford to 
         lose!""") % htmlColor("TextRed"), hAlign=Qt.AlignHCenter)

      lblDescr2 = QRichLabel(tr("""
         Use this form to create a "multi-key lockbox" to hold
         coins in escrow between multiple parties, or to share signing
         authority between multiple devices or wallets.  Once the lockbox is
         created, you can send coins to it by selecting it in your 
         address book from the "Send Bitcoins" window.  Spending or 
         moving bitcoins held in the lockbox requires a special 
         preparation and signing procedure, which can be accessed via
         the "MultiSig" menu on the main screen"""))

      lblDescr3 = QRichLabel(tr("""
         <b>Multi-key "lockboxes" require <u>public keys</u>, not 
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
         Multi-Key Lockbox</b></font>""") % htmlColor("TextBlue"), \
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
                              'Multi-Key', 'Name or Idenifier (such as email)')
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
               multi-key lockbox, such as contact information of other
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
            a multi-key lockbox will be created requiring
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

      self.main.updateOrAddLockbox(self.lockbox)
      
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
         <font color="%s" size=4><b>Manage Multi-key Lockbox Info</b></font>
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

      if not TheBDM.getBDMState()=='BlockchainReady':
         self.btnSpend.setDisabled(True)
         self.btnFundIt.setDisabled(True)
            
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
   def updateButtonDisable(self):
      noSelection = (self.getSelectedLBID() is None)
      isOffline = (not TheBDM.getBDMState()=='BlockchainReady')

      self.btnEdit.setDisabled(noSelection)
      self.btnExport.setDisabled(noSelection)
      self.btnDelete.setDisabled(noSelection)

      self.btnFundIt.setDisabled(noSelection or isOffline)
      self.btnSpend.setDisabled(noSelection or isOffline)
      
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
            self.main.updateOrAddLockbox(dlg.importedLockbox)
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
      lbID = self.getSelectedLBID()
      dlg = DlgSendBitcoins(None, self, self.main, spendFromLockboxID=lbID)
      dlg.exec_()
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
   For now, this *only* supports spending from up to 3-of-3 lockboxes.  
   Although most of the mechanics are there to handle arbitrary multi-spend 
   tx, a few shortcuts were taken that don't work well with non-lockboxes
   """

   KEYW = 32
   KEYH = 46
   CHKW = 32
   CHKH = 32

   #############################################################################
   def __init__(self, parent, main, lboxID, ustx):
      super(DlgMultiSpendReview, self).__init__(parent, main)


      lblDescr = QRichLabel(tr("""
         The following transaction is a proposed spend of funds controlled
         by multiple parties.  The keyholes next to each input represent 
         required signatures for the tx to be valid.  If the keyhole is white,
         it has not yet been signed, and cannot be signed by you.  Blue
         keyholes represent signatures that can be made by private keys/wallets
         claimed to be owned by you (though it may require getting an offline 
         signature).
         <br><br>
         Change outputs have been hidden where it is obvious (such as coins
         returning to the same lockbox from where it came).  If there is 
         any ambiguity, Armory will display all outputs."""))

      
      self.kscale = lambda pix: pix.scaled(KEYW,KEYH)
      self.cscale = lambda pix: pix.scaled(CHKW,CHKH)

      layout = QVBoxLayout()

      self.lboxID = lboxID
      self.lbox   = self.main.getLockboxByID(lboxID)
      self.ustx = UnsignedTransaction().unserialize(ustx.serialize())

      self.contribAmt = {}
      self.receiveAmt = {}
      self.contribStr = {}
      self.needToSign = {}
      self.useContrib = True


      # Some simple container classes
      class InputBundle(object):
         def __init__(self):
            self.sendAmt = 0
            self.dispStr = ''
            self.ustxiList = []
            self.lockbox = None
            self.capable = 0
            self.binScript = ''

      # Some simple container classes
      class OutputBundle(object):
            self.recvAmt = 0
            self.dispStr = ''
            self.lockbox = None
            self.wltID = None
            self.binScript = ''
      
      self.inputBundles = {}
      self.outputBundles = {}

      # Accumulate and prepare all static info (that doesn't change with sigs)
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

         # Take note of which lockbox this is
         iBundle.lockbox = self.main.getLockboxByID(idStr.split(':')[-1])

         # Check whether we have the capability to sign this thing
         iBundle.binScript = iBundle.lockbox.binScript
         for i in iBundle.lockbox.N:
            wltID = self.main.getWalletForAddr160(iBundle.a160List[i])
            if wltID:
               wltType = determineWalletType(wlt, self.main)[0]
               if wltType in [WLTTYPES.WatchOnly, WLTTYPES.Offline]:
                  iBundle.capable = max(iBundle.capable, 1)  # watch-only
               else:
                  iBundle.capable = max(iBundle.capable, 2)  # can sign now!
               

      # The output bundles are quite a bit simpler 
      for dtxo in self.ustx.decorTxOuts:
         hrStr,idStr = self.main.getContribStr(dtxo.binScript, dtxo.contribID)
         if idStr in self.inputBundles:
            self.inputBundles[idStr].sendAmt -= dtxo.value

         oBundle = self.outputBundles.setdefault(idStr, OutputBundle())
         if not idStr in self.receiveAmt:
            self.receiveAmt[idStr] = 0
            self.contribStr[idStr] = hrStr

         self.receiveAmt[idStr] += dtxo.value
         if idStr in self.contribAmt:
            self.contribAmt[idStr] += dtxo.value
            

      layoutInputs  = QGridLayout()
      layoutOutputs = QGridLayout()

      self.iWidgets = {}
      self.oWidgets = {}

      maxN = 3

      print 'Contributions:'
      iin = 0
      iout = 0
      for idStr in self.contribAmt:
         self.iWidgets[idStr] = {}
         topRow = (maxN+1)*iin
         iin += 1

         self.iWidgets[idStr]['HeadLbl'] = QRichLabel(tr("""
            <font color="%s"><b><u>Spending:</u> %s</b></font>""") % \
            (htmlColor('TextBlue'), self.contribStr[idStr]))
         self.iWidgets[idStr]['Amount'] = QMoneyLabel()

         # These are images that show up to N=3
         self.iWidgets[idStr]['HeadImg'] = [None]*3
         for i in range(maxN):
            self.iWidgets[idStr]['HeadImg'][i] = QLabel()

         self.iWidgets[idStr]['KeyImg']  = [None]*3
         for i in range(maxN):
            self.iWidgets[idStr]['KeyImg'][i] = QLabel()

         self.iWidgets[idStr]['KeyLbl']  = [None]*3
         for i in range(maxN):
            self.iWidgets[idStr]['KeyLbl'][i] = QRichLabel('')

         self.iWidgets[idStr]['ChkImg']  = [None]*3
         for i in range(maxN):
            self.iWidgets[idStr]['ChkImg'][i] = QLabel()

         self.iWidgets[idStr]['SignBtn']  = [None]*3
         for i in range(maxN):
            self.iWidgets[idStr]['SignBtn'][i] = QPushButton('')
         self.iWidgets[idStr]['SignBtn']  = [None]*3
         for i in range(maxN):
            self.iWidgets[idStr]['SignBtn'][i] = QPushButton('')
         

         # Now actually insert the widgets into a layout
         headerLine = [self.iWidgets[idStr]['HeadLbl']]
         headerLine.extend(self.iWidgets[idStr]['HeadImg'])
         headerLine.append('Stretch')
         layoutInputs.addWidget(makeHorizFrame(headerLine), topRow,0, 1,5)

         for i in range(maxN):
            row = topRow + 1 + i
            layoutInputs.addItem(QSpacerItem(20,20),         row,0)
            layoutInputs.addWidget(self.iWidgets['KeyImg'][i],  row,1)
            layoutInputs.addWidget(self.iWidgets['ChkImg'][i],  row,2)
            layoutInputs.addWidget(self.iWidgets['KeyLbl'][i],  row,3)
            layoutInputs.addWidget(self.iWidgets['SignBtn'][i], row,4)

            self.iWidgets['HeadImg'][i].setMinimumSize(KEYW,KEYH)
            self.iWidgets['KeyImg' ][i].setMinimumSize(KEYW,KEYH)
            self.iWidgets['ChkImg' ][i].setMinimumSize(CHKW,CHKH)

            

      for 
         elif amt < 0:
            #print "SEND-:", self.contribStr[idStr], coin2strNZS(-amt), 
                                                               #'(',idStr,')'
            topRow = (maxN+1)*iOut
            iout += 1

            self.oWidgets[idStr] = {}
            self.oWidgets[idStr]['HeadLbl'] = QRichLabel(tr("""
               <font color="%s"><b><u>Receiving:</u> %s</b></font>""") % \
               (htmlColor('TextBlue'), self.contribStr[idStr]))

            # These are images that show up to N=3
            self.oWidgets[idStr]['HeadImg'] = [None]*3
            self.oWidgets[idStr]['HeadImg'][0] = QLabel()
            self.oWidgets[idStr]['HeadImg'][1] = QLabel()
            self.oWidgets[idStr]['HeadImg'][2] = QLabel()

            self.oWidgets[idStr]['KeyLbl']  = [None]*3
            self.oWidgets[idStr]['KeyLbl'][0] = QRichLabel('')
            self.oWidgets[idStr]['KeyLbl'][1] = QRichLabel('')
            self.oWidgets[idStr]['KeyLbl'][2] = QRichLabel('')

            self.oWidgets[idStr]['KeyLbl']  = [None]*3
            self.oWidgets[idStr]['KeyImg'][0] = QRichLabel('')
            self.oWidgets[idStr]['KeyImg'][1] = QRichLabel('')
            self.oWidgets[idStr]['KeyImg'][2] = QRichLabel('')

            # Now actually insert the widgets into a layout
            headerLine = [self.oWidgets[idStr]['HeadLbl']]
            headerLine.extend(self.oWidgets[idStr]['HeadImg'])
            headerLine.append('Stretch')
            layoutOutputs.addWidget(makeHorizFrame(headerLine), topRow,0, 1,5)

            for i in range(maxN):
               row = topRow + 1 + i
               layoutOutputs.addItem(QSpacerItem(20,20),            row,0)
               layoutOutputs.addWidget(self.oWidgets['KeyImg'][i],  row,1)
               layoutOutputs.addWidget(self.oWidgets['KeyLbl'][i],  row,3)

               self.oWidgets['HeadImg'][i].setMinimumSize(KEYW,KEYH)
               self.oWidgets['KeyImg' ][i].setMinimumSize(KEYW,KEYH)
               self.oWidgets['ChkImg' ][i].setMinimumSize(CHKW,CHKH)
            

      # Evaluate SigningStatus returns per-wallet details if a wlt is given
      self.relevancyMap  = {}
      self.canSignMap    = {}
      self.alreadySigned = {}
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


      # This is complex, for sure.  
      #    The outermost loop goes over all inputs and outputs
      #    Then goes over all N public keys
      for idStr in self.contribAmt:
         amt = self.contribAmt[idStr]
         if amt > 0:
            for i in range(3):
               signBtn = self.iWidgets[idStr]['SignBtn'][i]
               chkLbl  = self.iWidgets[idStr]['chkImg'][i]
               keyImg  = self.iWidgets[idStr]['keyImg'][i]
               for wltID in self.alreadySigned:
                  if not self.alreadySigned[wltID]:
                     continue
                  signBtn.setVisible(False)
                  chkLbl.setPixmap(self.cscale(QPixmap(':/checkmark32.png')))
                  keyImg.setPixmap(self.kscale(QPixmap(':/keyhole_gray.png')))
               for wltID in self.canSignMap:
                  if not self.canSignMap[wltID]:
                     continue
                  wlt = self.main.walletMap[wltID]
                  wltType = determineWalletType(wlt, self.main)[0]
                  if wltType == WLTTYPES.Offline:
               
            canSign = sum([1 if t else 0 for t in self.canSignMap
     
   #############################################################################
   def signAsMuchAsPossible(self, wlts):
      if not isinstance(wlts, (list,tuple)):
         wlts = [wlts]

         


   #############################################################################
   def redrawSigs(self):
      self.allSigStat = self.ustx.evaluateSigningStatus()

      print 'Original USTX:'
      self.ustx.pprint()

      print 'Signing Status'
      self.allSigStat.pprint()
      



################################################################################
class DlgSelectMultiSigOption(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main):
      super(DlgSelectMultiSigOption, self).__init__(parent, main)

      self.btnCreate = QPushButton(tr('Create/Manage lockboxes'))
      #self.btnImport = QPushButton(tr('Import multi-key lockbox'))
      self.btnFund   = QPushButton(tr('Fund a lockbox'))
      self.btnSpend  = QPushButton(tr('Spend from a lockbox'))

      lblDescr  = QRichLabel(tr("""
         <font color="%s" size=5><b>Multi-Key Lockboxes 
         [EXPERIMENTAL]</b></font>""") % htmlColor('TextBlue'), 
         hAlign=Qt.AlignHCenter, doWrap=False)

      lblDescr2 = QRichLabel(tr("""
         The buttons below link you to all the functionality needed to 
         create, fund and spend from multi-key "lockboxes."  This 
         includes turning multiple wallets into a multi-factor lock-box
         for your personal coins, or can be used for escrow between
         multiple parties, using the Bitcoin network itself to hold the
         escrow.
         <br><br>
         <b><u>IMPORTANT:</u></b>  If you are using an lockbox that requires
         being funded by multiple parties simultaneously, you should 
         <b><u>not</u> </b> use regular transactions to do the funding.  
         You should use the third button labeled "Fund a multi-key lockbox" 
         to collect funding promises into a single transaction, to limit 
         the ability of any party to scam you.  Read more about it by
         clicking [NO LINK YET]  (if the above doesn't hold, you can use
         the regular "Send Bitcoins" dialog to fund the lockbox)."""))


      self.lblCreate = QRichLabel(tr("""
         Collect public keys to create an "address" that can be used 
         to send funds to the multi-key container"""))
      #self.lblImport = QRichLabel(tr("""
         #If someone has already created the lockbox you can add it 
         #to your lockbox list"""))
      self.lblFund = QRichLabel(tr("""
         Send money to an lockbox simultaneously with other 
         parties involved in the lockbox"""))
      self.lblSpend = QRichLabel(tr("""
         Collect signatures to authorize transferring money out of 
         a multi-key lockbox"""))


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
      self.setWindowTitle(tr('Multi-Key Lockboxes [EXPERIMENTAL]'))
      


   #############################################################################
   def openCreate(self):
      DlgLockboxEditor(self, self.main).exec_()

   #############################################################################
   def openFund(self):
      DlgFundLockbox(self, self.main).exec_()

   #############################################################################
   def openSpend(self):
      DlgSpendFromLockbox(self, self.main).exec_()
