from PyQt4.Qt import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from qtdefines import *
from qtdialogs import createAddrBookButton, DlgSetComment, DlgSendBitcoins, \
                      DlgUnlockWallet, DlgQRCodeDisplay, DlgRequestPayment,\
   DlgDispTxInfo
from armoryengine.ALL import *
from armorymodels import *
from armorycolors import *
from armoryengine.MultiSigUtils import MultiSigLockbox, calcLockboxID,\
   createLockboxEntryStr, readLockboxEntryStr
from ui.MultiSigModels import \
            LockboxDisplayModel,  LockboxDisplayProxy, LOCKBOXCOLS
import webbrowser
from armoryengine.CoinSelection import PySelectCoins, PyUnspentTxOut, \
                                    pprintUnspentTxOutList

         




#############################################################################
class DlgLockboxEditor(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, maxM=7, maxN=7, loadBox=None):
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
      self.prevPubKeyStr = ['']*self.maxN



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
         self.widgetMap[i]['LBL_WLTN'] = QRichLabel(tr('Name or ID:'), \
                                                    doWrap=False, \
                                                    hAlign=Qt.AlignRight)


         addrWidgets = self.main.createAddressEntryWidgets(self, '', 70, 2, 
                                       getPubKey=True, showLockBoxes=False)
         self.widgetMap[i]['QLE_PUBK'] = addrWidgets['QLE_ADDR']
         self.widgetMap[i]['BTN_BOOK'] = addrWidgets['BTN_BOOK']
         self.widgetMap[i]['LBL_DETECT']=addrWidgets['LBL_DETECT']
         self.widgetMap[i]['LBL_NAME'] = QRichLabel('', doWrap=False)
         self.widgetMap[i]['BTN_NAME'] = QLabelButton(tr('Edit'))
         self.widgetMap[i]['BTN_NAME'].setContentsMargins(0,0,0,0)
         self.widgetMap[i]['LBL_DETECT'].setWordWrap(False)

         def createCallBack(i):
            def nameClick():
               self.clickNameButton(i)
            return nameClick

         self.connect(self.widgetMap[i]['BTN_NAME'], SIGNAL('clicked()'), \
                                                            createCallBack(i))
         
         self.prevPubKeyStr[i] = ''
         
         #self.widgetMap[i]['QLE_PUBK'].setFont(GETFONT('Fixed', 9))
         w,h = tightSizeNChar(self.widgetMap[i]['QLE_PUBK'], 50)
         self.widgetMap[i]['QLE_PUBK'].setMinimumWidth(w)
         
         
      self.btnCancel   = QPushButton(tr('Exit'))
      self.btnContinue = QPushButton(tr('Save Lockbox'))
      #self.btnContinue.setEnabled(False)
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
         layoutThisRow.addWidget(self.widgetMap[i]['IMG_ICON'],   0,0, 3,1)
         layoutThisRow.addWidget(self.widgetMap[i]['LBL_ROWN'],   0,1)
         layoutThisRow.addWidget(self.widgetMap[i]['LBL_WLTN'],   2,1)
         layoutThisRow.addItem(QSpacerItem(10,10),                0,2)
         layoutThisRow.addWidget(self.widgetMap[i]['QLE_PUBK'],   0,3)
         layoutThisRow.addWidget(self.widgetMap[i]['BTN_BOOK'],   0,4)
         layoutThisRow.addWidget(self.widgetMap[i]['LBL_DETECT'], 1,3, 1,2)

         layoutName = QHBoxLayout()
         layoutName.addWidget(self.widgetMap[i]['LBL_NAME'])
         layoutName.addItem(QSpacerItem(5,5))
         layoutName.addWidget(self.widgetMap[i]['BTN_NAME'])
         layoutName.addStretch()
         layoutThisRow.addLayout(layoutName,                      2,3, 1,2)

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

      self.connect(btnClear,  SIGNAL('clicked()'), self.clearAll)


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
      self.updateLabels()

      if loadBox is not None:
         self.fillForm(loadBox)
         

      self.setLayout(layoutMaster)
      self.setWindowTitle('Multi-Sig Lockbox Editor')
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
   def isPotentiallyValidHexPubKey(self, pkstr):
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

      # Disable the continue button if not all keys are in
      M = int(str(self.comboM.currentText()))
      N = int(str(self.comboN.currentText()))

      for i in range(N):
         pkStr = str(self.widgetMap[i]['QLE_PUBK'].text()).strip()
         if not self.isPotentiallyValidHexPubKey(pkStr):
            #self.btnContinue.setEnabled(False)
            self.lblFinal.setText('')
            break
      else:
         self.formFilled = True
         #self.btnContinue.setEnabled(True)
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
            self.widgetMap[i]['QLE_PUBK'].setText('')

         for k,v in self.widgetMap[i].iteritems():
            v.setVisible(i<N)

      self.updateLabels()
         



   #############################################################################
   def clearAll(self):
      self.edtBoxName.clear()
      self.longDescr = ''
      for index,widMap in self.widgetMap.iteritems():
         for key,widget in widMap.iteritems():
            if key in ['QLE_PUBK', 'LBL_NAME']:
               widget.clear()

   
   #############################################################################
   def fillForm(self, lboxObj):

      self.edtBoxName.setText(lboxObj.shortName)
      self.longDescr = lboxObj.longDescr
      self.loadedID = lboxObj.uniqueIDB58
      self.createDate = lboxObj.createDate

      for i in range(lboxObj.N):
         self.widgetMap[i]['QLE_PUBK'].setText(binary_to_hex(lboxObj.pubKeys[i]))
         self.widgetMap[i]['LBL_NAME'].setText(lboxObj.commentList[i])

      def setCombo(cmb, val):
         for i in range(cmb.count()):
            if str(cmb.itemText(i))==str(val):
               cmb.setCurrentIndex(i)

      setCombo(self.comboM, lboxObj.M)
      setCombo(self.comboN, lboxObj.N)

      self.updateWidgetTable(lboxObj.M, lboxObj.N)
      self.updateLabels()
      
      
   #############################################################################
   def doContinue(self):

      currM = int(str(self.comboM.currentText()))
      currN = int(str(self.comboN.currentText()))

      if len(str(self.edtBoxName.text()).strip())==0:
         QMessageBox.warning(self, tr('Missing Name'), tr("""
            Lockboxes cannot be saved without a name (at the top of 
            the public key list).  It is also recommended to set the
            extended information next to it, for documenting the purpose
            of the lockbox."""), QMessageBox.Ok)
         return

      # If we got here, we already know all the public keys are valid strings
      pubKeyList = []
      acceptedBlankComment = False
      for i in range(currN):
         pkHex = str(self.widgetMap[i]['QLE_PUBK'].text()).strip()

         if len(pkHex)==0:
            QMessageBox.critical(self, tr('Not Enough Keys'), tr(""" 
               You specified less than <b>%d</b> public keys.  Please enter 
               a public key into every field before continuing.""") % currN,
               QMessageBox.Ok)
            return

         pkBin = hex_to_binary(pkHex)
         isValid = self.isPotentiallyValidHexPubKey(pkHex)
         if len(pkBin) == 65:
            if not CryptoECDSA().VerifyPublicKeyValid(SecureBinaryData(pkBin)):
               isValid = False
            
         if not isValid:
            QMessageBox.critical(self, tr('Invalid Public Key'), tr("""
               The data specified for public key <b>%d</b> is not valid.
               Please double-check the data was entered correctly.""") % (i+1),
               QMessageBox.Ok)
            return

         pubKeyList.append(pkBin)

         # Finally, throw a warning if the comment is not set 
         strComment = str(self.widgetMap[i]['LBL_NAME'].text()).strip()
         if len(strComment)==0 and not acceptedBlankComment:
            reply =QMessageBox.warning(self, tr('Empty Name/ID Field'), tr(""" 
               You did not specify a name/ID/comment for one or more of 
               the public keys.  If you do not do this,
               other devices and/or participants receiving this lockbox info
               will not be able to determine the identity of any 
               public keys except their own.  If this is a multi-party
               lockbox, it is recommended you put in contact information
               for each party, such as name, email and/or phone number.
               <br><br>
               Continue with some fields blank?
               <br>(click "No" to go back and finish filling in the form)"""), 
               QMessageBox.Yes | QMessageBox.No)

            if reply==QMessageBox.Yes:
               acceptedBlankComment = True
            else:
               return
      


      # Extract the labels for each pubKey
      self.NameIDList = \
         [unicode(self.widgetMap[i]['LBL_NAME'].text()) for i in range(currN)]


      # ACR:  Andy added sorting, but didn't realize that the comments for 
      #       associated with each key also need to be sorted.  Use DSU
      decorated  = [[pk,comm] for pk,comm in zip(pubKeyList, self.NameIDList)]
      decorSort  =sorted(decorated, key=lambda pair: pair[0])
      for i,pair in enumerate(decorSort):
         pubKeyList[i]      = pair[0]
         self.NameIDList[i] = pair[1]
      

      txOutScript = pubkeylist_to_multisig_script(pubKeyList, currM)  
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

      if not USE_TESTNET:
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

      self.txtLockboxInfo = QTextEdit()
      self.txtLockboxInfo.acceptRichText()
      self.txtLockboxInfo.setStyleSheet('QTextEdit { background-color : %s }' % htmlColor('SlightBkgdLight'))
      self.txtLockboxInfo.setReadOnly(True)
      self.txtLockboxInfo.setFont(GETFONT('Fixed', 9))


      self.btnCreate = QPushButton(tr('Create New'))
      self.btnImport = QPushButton(tr('Import New'))
      self.btnEdit   = QPushButton(tr('Edit'))
      self.btnExport = QPushButton(tr('Export'))
      self.btnDelete = QPushButton(tr('Remove'))
      self.btnFundIt = QPushButton(tr('Deposit Funds'))
      self.btnSimul  = QPushButton(tr('Simulfunding'))
      self.btnSpend  = QPushButton(tr('Spend Funds'))

      self.connect(self.btnCreate,   SIGNAL('clicked()'), self.doCreate)
      self.connect(self.btnImport,   SIGNAL('clicked()'), self.doImport)
      self.connect(self.btnEdit,     SIGNAL('clicked()'), self.doEdit)
      self.connect(self.btnExport,   SIGNAL('clicked()'), self.doExport)
      self.connect(self.btnDelete,   SIGNAL('clicked()'), self.doDelete)
      self.connect(self.btnFundIt,   SIGNAL('clicked()'), self.doFundIt)
      self.connect(self.btnSimul,    SIGNAL('clicked()'), self.doSimul)
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
                                      self.btnSimul,
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
         lboxId = str(view.model().index(row, LEDGERCOLS.WltID).data().toString())
         txHash = str(view.model().index(row, LEDGERCOLS.TxHash).data().toString())
         lbox = self.main.allLockboxes[self.main.lockboxIDMap[lboxId]]
         for a160 in lbox.a160List:
            wltID = self.main.getWalletForAddr160(a160)
            if len(wltID)>0:
               self.main.walletMap[wltID].setComment(hex_to_binary(txHash), newComment)
         self.main.walletListChanged()

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

      lboxId  = str(self.ledgerView.model().index(row, LEDGERCOLS.WltID).data().toString())
      lbox = self.main.allLockboxes[self.main.lockboxIDMap[lboxId]]
      wltID = None
      for a160 in lbox.a160List:
         wltID = self.main.getWalletForAddr160(a160)
         if len(wltID)>0:
            wlt = self.main.walletMap[wltID]
            break

      DlgDispTxInfo( pytx, wlt, self, self.main, txtime=txtime).exec_()
   
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
      selectedIndexes = self.lboxView.selectedIndexes()
      if len(selectedIndexes)>0:
         idx = selectedIndexes[0]
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
      self.btnSimul.setDisabled(noSelection)
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
         self.txtLockboxInfo.setText(lb.getDisplayRichText())
      else:
         self.txtLockboxInfo.setText('')

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
      dispInfo = self.main.getDisplayStringForScript(lb.binScript, 100, 2,
                                                      prefIDOverAddr=True)
      reply = QMessageBox.warning(self, tr('Confirm Delete'), tr("""
         "Removing" a lockbox does not delete any signing keys, so you 
         maintain signing authority for any coins that are sent there.     
         However, it will remove it from the list of lockboxes, and you
         will have to re-import it again later in order to send any funds
         to or from the lockbox.
         <br><br>
         You are about to remove the following lockbox:
         <br><br>
         <font color="%s">%s</font> """) % (htmlColor('TextBlue'), 
         dispInfo['String']), QMessageBox.Yes | QMessageBox.No) 

      if reply==QMessageBox.Yes:
         lbObj = self.getSelectedLockbox()
         self.main.removeLockbox(lbObj)
         self.lboxModel.reset()
         self.singleClickLockbox()

      self.updateButtonDisable()


   
   #############################################################################
   def doFundIt(self):

      reply = QMessageBox.warning(self, tr('[WARNING]'), tr("""
         <b><font color="%s">WARNING:</font> </b>
         If this lockbox is being used to hold escrow for multiple parties, and
         requires being funded by multiple participants, you <u>must</u> use
         a special funding process to ensure simultaneous funding.  Otherwise,
         one of the other parties may be able to scam you!  
         <br><br>
         It is safe to continue if any of the following conditions are true:
         <ul>
            <li>You are the only one expected to fund the escrow</li>
            <li>All other parties in the escrow are fully trusted</li>
            <li>This lockbox is being used for personal savings</li>
         </ul>
         If the above does not apply to you, please press "Cancel" and 
         use the "Simulfunding" button in the Lockbox manager to continue.
         """) % htmlColor('TextWarn'), 
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
   def doSimul(self):
      
      lbID = self.getSelectedLBID()
      dlgSimul = DlgSimulfundSelect(self, self.main, lbID)
      dlgSimul.exec_()

      if dlgSimul.selection is None:
         return
      elif dlgSimul.selection=='Create':
         DlgCreatePromNote(self, self.main, lbID).exec_()
      elif dlgSimul.selection=='Collect':
         DlgMergePromNotes(self, self.main, lbID).exec_()
      elif dlgSimul.selection=='Review':

         title = tr("Import Signature Collector")
         descr = tr("""
            Import a <i>Signature Collector</i> text block to review and
            sign the simulfunding transaction.  This text block is produced
            by the party that collected and merged all the promissory notes.
            Files containing signature-collecting data usually end with
            <i>*.sigcollect.tx</i>.""")
         ftypes = ['Signature Collectors (*.sigcollect.tx)']
         dlgImport = DlgImportAsciiBlock(self, self.main, 
                           title, descr, ftypes, UnsignedTransaction)
         dlgImport.exec_()
         if dlgImport.returnObj:
            ustx = dlgImport.returnObj
            DlgMultiSpendReview(self, self.main, ustx).exec_()

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
class DlgSimulfundSelect(ArmoryDialog):
   def __init__(self, parent, main, lbID):
      super(DlgSimulfundSelect, self).__init__(parent, main)
   
      self.selection = None

      lbox = self.main.getLockboxByID(lbID)
      dispStr = '<font color="%s"><b>%s-of-%s</b>: %s (%s)</font>' % \
         (htmlColor('TextBlue'), lbox.M, lbox.N, lbox.shortName, lbox.uniqueIDB58)

      lblTitle = QRichLabel(tr("""
         <font color="%s" size=4><b>Simultaneous Lockbox 
         Funding</b></font>""") % htmlColor('TextBlue'), hAlign=Qt.AlignHCenter)

      lblDescr = QRichLabel(tr("""
         To have multiple parties simultaneously fund a lockbox, each party
         will need to create a "promissory note," and any other party will
         collect all of them to create a single simulfunding transaction.
         This transaction will be signed by all parties after reviewing that
         it meets their expectations.  This process guarantees that either 
         all parties commit funds simultaneously, or no one does.  The
         signature that you provide using this interface is only valid if 
         all the other funding commitments are also signed.
         <br><br>
         If you are both creating a promissory note and merging all the 
         notes together, you should first create the promissory note and
         save it to disk or copy it to your clipboard.  Once all other 
         funding commitments have been received, open this dialog again 
         and load all of them at once.  Sign for your contribution and
         send the result to all the other parties.
         <br><br>
         You are currently handling a simulfunding operation for lockbox:
         <br>%s.""") % dispStr)
         

      btnCreate  = QPushButton(tr('Create Promissory Note'))
      btnCollect = QPushButton(tr('Collect and Merge Notes'))
      btnReview  = QPushButton(tr('Sign Simulfunding Transaction'))
      btnCancel  = QPushButton(tr("Cancel"))

      if TheBDM.getBDMState()=='BlockchainReady':
         lblCreate = QRichLabel(tr("""
            Create a commitment to a simulfunding transaction"""))
      else:
         btnCreate.setEnabled(False)
         lblCreate = QRichLabel(tr("""
            Note creation is not available when offline."""))

      lblCollect = QRichLabel(tr("""
         Collect multiple promissory notes into a single simulfunding
         transaction"""))

      lblReview = QRichLabel(tr("""
         Review and signed a simulfunding transaction (after all promissory
         notes have been collected)"""))

      self.connect(btnCreate,  SIGNAL('clicked()'), self.doCreate)
      self.connect(btnCollect, SIGNAL('clicked()'), self.doCollect)
      self.connect(btnReview,  SIGNAL('clicked()'), self.doReview)
      self.connect(btnCancel,  SIGNAL('clicked()'), self.reject)

      frmTop = makeVertFrame([lblTitle, lblDescr], STYLE_STYLED)

      layoutBot = QGridLayout()
      layoutBot.addWidget(btnCreate,   0,0)
      layoutBot.addWidget(lblCreate,   0,1)
      layoutBot.addWidget(HLINE(),     1,0, 1,2)
      layoutBot.addWidget(btnCollect,  2,0)
      layoutBot.addWidget(lblCollect,  2,1)
      layoutBot.addWidget(HLINE(),     3,0, 1,2)
      layoutBot.addWidget(btnReview,   4,0)
      layoutBot.addWidget(lblReview,   4,1)

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

      self.setMinimumWidth(600)


   def doCreate(self):
      self.selection = 'Create'
      self.accept()

   def doCollect(self):
      self.selection = 'Collect'
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
      if self.importedLockbox == None:
         QMessageBox.critical(self, tr('Non-lockbox'), tr("""
               You are attempting to load something that is not a Lockbox.
               Please clear the display and try again."""), QMessageBox.Ok)
      else:
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
class DlgMultiSpendReview(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, ustx=None):
      super(DlgMultiSpendReview, self).__init__(parent, main)


      if ustx is None:
         title = tr('Import Multi-Spend Transaction')
         descr = tr("""
            Import a signature-collector text block for review and signing.  
            It is usually a block of text with "TXSIGCOLLECT" in the first line,
            or a <i>*.sigcollect.tx</i> file.""")
         ftypes = ['Signature Collectors (*.sigcollect.tx)']
         dlgImport = DlgImportAsciiBlock(self, self.main, 
                           title, descr, ftypes, UnsignedTransaction)
         dlgImport.exec_()
         if dlgImport.returnObj:
            ustx = dlgImport.returnObj
         else:
            from twisted.internet import reactor
            reactor.callLater(0.1,  self.reject)
            return


      LOGDEBUG('Debugging information for multi-spend USTX')
      ustx.pprint()


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

      KEYW,KEYH = 25,36
      CHKW,CHKH = 32,32
      PIEW,PIEH = 32,32

      # These need to return copies
      self.pixGreen = lambda: QPixmap(':/keyhole_green.png').scaled(KEYW,KEYH)
      self.pixGray  = lambda: QPixmap(':/keyhole_gray.png' ).scaled(KEYW,KEYH)
      self.pixBlue  = lambda: QPixmap(':/keyhole_blue.png' ).scaled(KEYW,KEYH)
      self.pixWhite = lambda: QPixmap(':/keyhole_white.png').scaled(KEYW,KEYH)
      self.pixRed   = lambda: QPixmap(':/keyhole_red.png'  ).scaled(KEYW,KEYH)
      self.pixChk   = lambda: QPixmap(':/checkmark32.png'  ).scaled(CHKW,CHKH)
      self.pixPie   = lambda m: QPixmap(':/frag%df.png'%m  ).scaled(PIEW,PIEH)

      layout = QVBoxLayout()

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
         hrStr,idStr = self.main.getContribStr(ustxi.txoScript, 
                                               ustxi.contribID,
                                               ustxi.contribLabel)

         iBundle = self.inputBundles.setdefault(idStr, InputBundle())
         iBundle.ustxiList.append(ustxi)
         iBundle.sendAmt += ustxi.value
         iBundle.dispStr = hrStr

         if idStr[:2] in ['LB']:
            iBundle.lockbox = self.main.getLockboxByID(idStr.split(':')[-1])

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
         else:
            iBundle.wltOfflineSign  = [None]
            iBundle.wltSignRightNow = [None]
            iBundle.keyholePixmap   = [None]
            M,N = 1,1
            self.maxN = 1 
            if idStr[:3] in ['WLT']:
               iBundle.keyholePixmap[0] = QLabel()
               wltID = idStr.split(':')[-1]
               wlt = self.main.walletMap[wltID]
               wltType = determineWalletType(wlt, self.main)[0]
               a160 = CheckHash160(script_to_scrAddr(ustxi.txoScript))
               if wltType in [WLTTYPES.WatchOnly, WLTTYPES.Offline]:
                  iBundle.wltOfflineSign[0] = [wltID, a160]
                  iBundle.keyholePixmap[0].setPixmap(self.pixWhite())
               else:
                  iBundle.wltSignRightNow[0] = [wltID, a160]
                  iBundle.keyholePixmap[0].setPixmap(self.pixGreen())
            elif idStr[:3] in ['CID', 'ADD', 'NS:', 'MS:']:
               # In these cases, nothing really to do
               pass
               
            
               

      # The output bundles are quite a bit simpler 
      for dtxo in self.ustx.decorTxOuts:
         hrStr,idStr = self.main.getContribStr(dtxo.binScript, 
                                               dtxo.contribID,
                                               dtxo.contribLabel)
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

         iBundle = self.inputBundles[idStr]

      
         contribID = ''
         contribLabel = ''
         if len(iBundle.ustxiList) > 0:
            contribID    = iBundle.ustxiList[0].contribID.strip()
            contribLabel = iBundle.ustxiList[0].contribLabel.strip()

         # The header line lists the name and value and any multisig pies
         if not contribLabel:
            iWidgMap['HeadLbl'] = QRichLabel(tr("""
               <b><u>Spending:</u> <font color="%s">%s</b></font>""") % \
               (htmlColor('TextBlue'), iBundle.dispStr), doWrap=False)
         else: 
            if contribID:
               contribID = ' (%s)' % contribID
            iWidgMap['HeadLbl'] = QRichLabel(tr("""
               <b><u>Contributor:</u> <font color="%s">%s</b>%s</font>""") % \
               (htmlColor('TextBlue'), contribLabel, contribID), doWrap=False)


         val = iBundle.sendAmt
         iWidgMap['Amount'] = QMoneyLabel(-val, txtSize=12, wBold=True)

         # These are images that show up to N=5
         iWidgMap['HeadImg'] = [None]*self.maxN
         iWidgMap['KeyImg']  = [None]*self.maxN
         iWidgMap['KeyLbl']  = [None]*self.maxN
         iWidgMap['ChkImg']  = [None]*self.maxN
         iWidgMap['SignBtn'] = [None]*self.maxN

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

            lbox = iBundle.lockbox
            M = lbox.M if lbox else 1
            N = lbox.N if lbox else 1
            if i >= N:
               iWidgMap['SignBtn'][i].setVisible(False)
               iWidgMap['KeyImg' ][i].setVisible(False)
               iWidgMap['KeyLbl' ][i].setVisible(False)
               iWidgMap['ChkImg' ][i].setVisible(False)
            else:

               if lbox:
                  comm = lbox.commentList[i]
               elif len(iBundle.ustxiList) > 0:
                  comm = iBundle.ustxiList[0].contribLabel
               else:
                  comm = None

               wltID = ''
               if iBundle.wltOfflineSign[i]:
                  wltID = iBundle.wltOfflineSign[i][0]
               elif iBundle.wltSignRightNow[i]:
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
                     if lbox:
                        dispStr = '%s [%s]' % (comm, wltName)
                     else:
                        dispStr = '%s' % wltName

               iWidgMap['KeyLbl' ][i].setText(dispStr)
               iWidgMap['HeadImg'][i].setPixmap(self.pixPie(M))
               iWidgMap['KeyImg' ][i].setMinimumSize(KEYW,KEYH)
               iWidgMap['ChkImg' ][i].setMinimumSize(CHKW,CHKH)
               iWidgMap['KeyLbl' ][i].setWordWrap(False)
            
               if not lbox:
                  iWidgMap['HeadImg'][i].setVisible(False)
   
            

         for widgetName,widgetList in iWidgMap.iteritems():
            if widgetName in ['HeadLbl', 'Amount']:
               continue

            for i in range(self.maxN):
               lbox = iBundle.lockbox
               N = lbox.N if lbox else 1
               if i >= N:
                  widgetList[i].setVisible(False)
            

      layoutInputs.setColumnStretch(0,0)
      layoutInputs.setColumnStretch(1,0)
      layoutInputs.setColumnStretch(2,0)
      layoutInputs.setColumnStretch(3,1)
      layoutInputs.setColumnStretch(4,0)


      # Maybe one day we'll do full listing of lockboxes on the output side
      # But for now, it will only further complicate things...
      for idStr in self.outputBundles:
         lbox = self.outputBundles[idStr].lockbox
         M,N = [1,1] if lbox is None else [lbox.M, lbox.N]

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

         # These are the pie images
         oWidgMap['HeadImg'] = [None]*N
         for i in range(N):
            oWidgMap['HeadImg'][i] = QLabel()


         # Now actually insert the widgets into a layout
         headerLine = [oWidgMap['HeadLbl']]
         headerLine.extend(oWidgMap['HeadImg'])
         headerLine.append('Stretch')
         headerLine.append(oWidgMap['Amount'])
         layoutOutputs.addWidget(makeHorizFrame(headerLine), topRow,0, 1,5)

         if N>1:
            for i in range(N):
               oWidgMap['HeadImg'][i].setPixmap(self.pixPie(M))
               oWidgMap['HeadImg'][i].setMinimumSize(PIEW,PIEH)
            


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



      self.btnLoadImport  = QPushButton(tr('Import/Merge'))
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
               'Cannot sign without unlocking wallet!', 
               QMessageBox.Ok)
            return

      if ib.lockbox:
         # If a lockbox, all USTXIs require the same signing key
         for ustxi in ib.ustxiList:
            addrObj = wlt.getAddrByHash160(a160)
            ustxi.createAndInsertSignature(pytx, addrObj.binPrivKey32_Plain)
      else:
         # Not lockboxes... may have to access multiple keys in wallet
         for ustxi in ib.ustxiList:
            a160 = CheckHash160(ustxi.scrAddrs[0])
            addrObj = wlt.getAddrByHash160(a160)
            ustxi.createAndInsertSignature(pytx, addrObj.binPrivKey32_Plain)

      self.evalSigStat()
      
   ############################################################################# 
   def evalSigStat(self):
      self.relevancyMap  = {}
      self.canSignMap    = {}
      self.alreadySigned = {}

      # Not sure if we really need this...
      for wltID,pyWlt in self.main.walletMap.iteritems():
         txss = self.ustx.evaluateSigningStatus(pyWlt.cppWallet)
         self.relevancyMap[wltID]  = txss.wltIsRelevant
         self.canSignMap[wltID]    = txss.wltCanSign
         self.alreadySigned[wltID] = txss.wltAlreadySigned


      # This is complex, for sure.  
      #    The outermost loop goes over all inputs and outputs
      #    Then goes over all N public keys
      for idStr,ib in self.inputBundles.iteritems():
         iWidgMap = self.iWidgets[idStr]

         # Since we are calling this without a wlt, each key state can only
         # be either ALREADY_SIGNED or NO_SIGNATURE (no WLT* possible)
         isigstat = ib.ustxiList[0].evaluateSigningStatus()

         N = ib.lockbox.N if ib.lockbox else 1
         for i in range(N):
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
         # Merge signatures if the current ustx ID matchs the imported file
         if self.ustx.uniqueIDB58 == dlg.returnObj.uniqueIDB58:
            for i in range(len(dlg.returnObj.ustxInputs)):
               for j in range(len(dlg.returnObj.ustxInputs[i].signatures)):
                  if len(self.ustx.ustxInputs[i].signatures[j]) > 0:
                     dlg.returnObj.ustxInputs[i].signatures[j] = \
                        self.ustx.ustxInputs[i].signatures[j]
               
         # FIXME: This is a serious hack because I didn't have time to implement
         #        reloading an existing dialog with a new USTX, so I just recurse
         #        for now (it's because all the layouts are set in the __init__
         #        function, etc...
         self.accept() 
         DlgMultiSpendReview(self.parent, self.main, dlg.returnObj).exec_()


   def doBroadcast(self):
      finalTx = self.ustx.getSignedPyTx(doVerifySigs=True)
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

         finalTx = self.ustx.getSignedPyTx(doVerifySigs=False)

      self.main.broadcastTransaction(finalTx, withOldSigWarning=False)
      try:
         self.parent.tabbedDisplay.setCurrentIndex(1)
      except:
         LOGEXCEPT('Failed to switch parent tabs')
      self.accept()
         


################################################################################
class DlgCreatePromNote(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, defaultID=None):
      super(DlgCreatePromNote, self).__init__(parent, main)

      lblDescr  = QRichLabel(tr("""
         <font color="%s" size=4><b>Create Simulfunding Promissory Note
         </b></font>""") % htmlColor('TextBlue'), 
         hAlign=Qt.AlignHCenter, doWrap=False)

      lblDescr2 = QRichLabel(tr("""
         Use this form to create a
         "promissory note" which can be combined with notes from other 
         parties to fund an address or lockbox simultaneously
         (<i>"simulfunding"</i>).  This funding
         transaction will not be valid until all promissory notes are 
         merged into a single transaction, then all funding parties 
         will review and sign it.  
         <br><br>
         If this lockbox is being funded by only one party, using this
         interface is unnecessary.  Have the funding party send Bitcoins 
         to the destination address or lockbox in the normal way."""))

      lblNoteSrc = QRichLabel(tr("""
         <b>NOTE:</b> At the moment, simulfunding is restricted to using
         single-signature wallets/addresses for funding.    More
         complex simulfunding transactions will be possible in a future 
         version of Armory."""))

      if len(self.main.walletIDList)>0:
         self.spendFromWltID = self.main.walletIDList[0]
      else:
         self.spendFromWltID = ''


      def selectWalletFunc(wlt):
         self.spendFromWltID = wlt.uniqueIDB58
      
      wltFrame = SelectWalletFrame(self, self.main, HORIZONTAL, 
                           selectWltCallback=selectWalletFunc)
                                                  

      # Create the frame that specifies the target of the funding

      lblAddress = QRichLabel(tr('Address:'))
      lblAmount  = QRichLabel(tr('Amount:'))
      lblFee     = QRichLabel(tr('Add fee:'))
      lblBTC1    = QRichLabel(tr('BTC'))
      lblBTC2    = QRichLabel(tr('BTC'))

      """
      self.edtFundTarget = QLineEdit()
      if defaultID:
         self.edtFundTarget.setText(createLockboxEntryStr(defaultID))

      self.btnSelectTarg = createAddrBookButton(
                                 parent=self, 
                                 targWidget=self.edtFundTarget, 
                                 defaultWlt=None,
                                 actionStr='Select', 
                                 showLockBoxes=True)
      self.lblTargetID = QRichLabel('')
      self.connect(self.edtFundTarget, SIGNAL('textChanged(QString)'), 
                   self.updateTargetLabel)
      """
      startStr = ''
      if defaultID:
         startStr = createLockboxEntryStr(defaultID)

      aewMap = self.main.createAddressEntryWidgets(self, startStr, 
                                       maxDetectLen=72, boldDetectParts=2)
      self.edtFundTarget = aewMap['QLE_ADDR']
      self.btnSelectTarg = aewMap['BTN_BOOK']
      self.lblAutoDetect = aewMap['LBL_DETECT']
      self.parseEntryFunc = aewMap['CALLBACK_GETSCRIPT']
                                          
      self.lblAutoDetect.setWordWrap(False)

      self.edtAmountBTC = QLineEdit()
      self.edtAmountBTC.setFont(GETFONT('Fixed'))
      self.edtAmountBTC.setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 16)[0])
      self.edtAmountBTC.setAlignment(Qt.AlignLeft)

      self.edtFeeBTC = QLineEdit()
      self.edtFeeBTC.setFont(GETFONT('Fixed'))
      self.edtFeeBTC.setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 16)[0])
      self.edtFeeBTC.setAlignment(Qt.AlignLeft)
      self.edtFeeBTC.setText('0.0')


      lblComment  = QRichLabel('Funder Label (optional):')
      self.edtKeyLabel  = QLineEdit()
      ttipFunder = self.main.createToolTipWidget(tr("""
         This label will be attached to the promissory note to help identify
         who is committing these funds.  If you do not fill this in, each
         other party signing will see <i>[[Unknown Signer]]</i> for the ID."""))
         

      frmKeyComment = makeHorizFrame([lblComment, self.edtKeyLabel, ttipFunder])

      gboxIn  = QGroupBox(tr('Source of Funding'))
      gboxInLayout = QVBoxLayout()
      gboxInLayout.addWidget(lblNoteSrc)
      gboxInLayout.addWidget(wltFrame)
      gboxInLayout.addWidget(frmKeyComment)
      gboxIn.setLayout(gboxInLayout) 

      gboxOut = QGroupBox(tr('Funding Destination'))
      gboxOutLayout = QGridLayout()
      gboxOutLayout.addWidget(lblAddress,            0,0)
      gboxOutLayout.addWidget(self.edtFundTarget,    0,1, 1,5)
      gboxOutLayout.addWidget(self.btnSelectTarg,    0,6)

      gboxOutLayout.addWidget(self.lblAutoDetect,    1,1, 1,5)

      gboxOutLayout.addWidget(lblAmount,             3,0)
      gboxOutLayout.addWidget(self.edtAmountBTC,     3,1)
      gboxOutLayout.addWidget(lblBTC1,               3,2)

      gboxOutLayout.addWidget(lblFee,                3,4)
      gboxOutLayout.addWidget(self.edtFeeBTC,        3,5)
      gboxOutLayout.addWidget(lblBTC2,               3,6)

      gboxOutLayout.setColumnStretch(0, 0)
      gboxOutLayout.setColumnStretch(1, 0)
      gboxOutLayout.setColumnStretch(2, 0)
      gboxOutLayout.setColumnStretch(3, 1)
      gboxOutLayout.setColumnStretch(4, 0)
      gboxOut.setLayout(gboxOutLayout)

      btnExit = QPushButton(tr('Cancel'))
      btnDone = QPushButton(tr('Continue'))
      self.connect(btnExit, SIGNAL('clicked()'), self.reject)
      self.connect(btnDone, SIGNAL('clicked()'), self.doContinue)
      frmButtons = makeHorizFrame([btnExit, 'Stretch', btnDone])

      mainLayout = QVBoxLayout()
      mainLayout.addWidget(lblDescr)
      mainLayout.addWidget(lblDescr2)
      mainLayout.addWidget(HLINE())
      mainLayout.addWidget(gboxIn)
      mainLayout.addWidget(HLINE())
      mainLayout.addWidget(gboxOut)
      mainLayout.addWidget(HLINE())
      mainLayout.addWidget(frmButtons)
      self.setLayout(mainLayout)

      self.layout().setSizeConstraint(QLayout.SetFixedSize)

      self.setWindowTitle('Create Promissory Note')

      #self.updateTargetLabel()
      self.setMinimumWidth(600)


   #############################################################################
   def updateTargetLabel(self):
      try:
         addrText = str(self.edtFundTarget.text())
         if addrStr_is_p2sh(addrText):
            lboxID = self.main.getLockboxByP2SHAddrStr(addrText).uniqueIDB58
         else:
            lboxID = readLockboxEntryStr(addrText)

         if lboxID:
            lbox = self.main.getLockboxByID(lboxID)
            if lbox:
               dispStr = '<b>%s-of-%s</b>: %s' % (lbox.M, lbox.N, lbox.shortName)
            else:
               dispStr = 'Unrecognized Lockbox'

            self.lblTargetID.setVisible(True)
            self.lblTargetID.setText(dispStr, color='TextBlue')
            return

         wltID = self.main.getWalletForAddr160(addrStr_to_hash160(addrText)[1])
         if wltID:
            wlt = self.main.walletMap[wltID]
            dispStr = '%s (%s)' % (wlt.labelName, wlt.uniqueIDB58)
            self.lblTargetID.setVisible(True)
            self.lblTargetID.setText(dispStr, color='TextBlue')
            return

         self.lblTargetID.setVisible(False)

      except:
         LOGEXCEPT('')
         self.lblTargetID.setVisible(False)


   #############################################################################
   def doContinue(self):


      if not TheBDM.getBDMState()=='BlockchainReady':
         LOGERROR('Blockchain not avail for creating prom note')
         QMessageBox.critical(self, tr('Blockchain Not Available'), tr("""
            The blockchain has become unavailable since you opened this
            window.  Creation of the promissory note cannot continue.  If 
            you think you should be online, please try again in a minute,
            or after restarting Armory"""), QMessageBox.Ok)
         return False

      # TODO:  Expand this to allow simulfunding from lockbox(es)
      wlt   = self.main.walletMap.get(self.spendFromWltID, None)
      lbox  = self.main.getLockboxByID(self.spendFromWltID)
      if lbox is not None:
         LOGERROR('Simulfunding from lockbox not currently implemented')
         QMessageBox.critical(self, tr('Lockbox Selected'), tr("""
            Currently, Armory does not implement simulfunding with lockbox
            inputs.  Please choose a regular wallet as your input"""),
            QMessageBox.Ok)
         return False
      elif wlt is None:
         LOGERROR('No wallet in map with ID: "%s"' % self.spendFromWltID)
         QMessageBox.critical(self, tr('No Wallet Selected'), tr("""
            The wallet selected is not available.  Select another wallet."""),
            QMessageBox.Ok)
         return False

      # Read the user-supplied BTC value to contribute
      try:
         valueStr = str(self.edtAmountBTC.text())
         valueAmt = str2coin(valueStr)
         if valueAmt == 0:
            QMessageBox.critical(self, tr('Zero Amount'), tr("""
               You cannot promise 0 BTC.   <br>Please enter 
               a positive amount."""), QMessageBox.Ok)
            return False
      except NegativeValueError:
         QMessageBox.critical(self, tr('Negative Value'), tr("""
            You have specified a negative amount. <br>Only
            positive values are allowed!"""), QMessageBox.Ok)
         return False
      except TooMuchPrecisionError:
         QMessageBox.critical(self, tr('Too much precision'), tr("""
            Bitcoins can only be specified down to 8 decimal places. 
            The smallest value that can be sent is  0.0000 0001 BTC. 
            Please enter a new amount"""), QMessageBox.Ok)
         return False
      except ValueError:
         QMessageBox.critical(self, tr('Missing amount'), tr("""
            'You did not specify an amount to promise!"""), QMessageBox.Ok)
         return False
      except:
         QMessageBox.critical(self, tr('Invalid Value String'), tr("""
            The amount you specified is invalid (%s).""") % valueStr, 
            QMessageBox.Ok)
         LOGEXCEPT('Invalid amount specified: "%s"', valueStr)
         return False
      
      # Read the fee string
      try:
         feeStr = str(self.edtFeeBTC.text())
         feeAmt = str2coin(feeStr)
      except NegativeValueError:
         QMessageBox.critical(self, tr('Negative Fee'), tr("""
            You have specified a negative amount. <br>Only
            positive values are allowed!"""), QMessageBox.Ok)
         return False
      except TooMuchPrecisionError:
         QMessageBox.critical(self, tr('Too much precision'), tr("""
            Bitcoins can only be specified down to 8 decimal places. 
            The smallest value that can be sent is  0.0000 0001 BTC. 
            Please enter a new amount"""), QMessageBox.Ok)
         return False
      except ValueError:
         QMessageBox.critical(self, tr('Missing amount'), tr("""
            'You did not specify an amount to promise!"""), QMessageBox.Ok)
         return False
      except:
         QMessageBox.critical(self, tr('Invalid Fee String'), tr("""
            The amount you specified is invalid (%s).""") % feeStr, 
            QMessageBox.Ok)
         LOGEXCEPT('Invalid amount specified: "%s"', feeStr)
         return False

      utxoList = wlt.getTxOutList('Spendable')
      utxoSelect = PySelectCoins(utxoList, valueAmt, feeAmt)

      if len(utxoSelect) == 0:
         QMessageBox.critical(self, tr('Coin Selection Error'), tr("""
            There was an error constructing your transaction, due to a 
            quirk in the way Bitcoin transactions work.  If you see this
            error more than once, try sending your BTC in two or more 
            separate transactions."""), QMessageBox.Ok)
         return False

      # Create the target DTXO
      targetScript = self.parseEntryFunc()['Script']
      dtxoTarget = DecoratedTxOut(targetScript, valueAmt)

      # Create the change DTXO
      # TODO:  Expand this to allow simulfunding from lockbox(es)
      pprintUnspentTxOutList(utxoSelect)
      changeAmt = sumTxOutList(utxoSelect) - (valueAmt + feeAmt)
      dtxoChange = None
      if changeAmt > 0:
         changeAddr160 = wlt.getNextUnusedAddress().getAddr160()
         changeScript = hash160_to_p2pkhash_script(changeAddr160)
         dtxoChange = DecoratedTxOut(changeScript, changeAmt)
      else:
         LOGINFO('Had exact change for prom note:  dtxoChange=None')

      # If we got here, we can carry through with creating the prom note
      ustxiList = []
      for i in range(len(utxoSelect)):
         utxo = utxoSelect[i]
         txHash = utxo.getTxHash()
         txoIdx = utxo.getTxOutIndex()
         cppTx = TheBDM.getTxByHash(txHash)
         if not cppTx.isInitialized():
            LOGERROR('UTXO was supplied for which we could not find prev Tx')
            QMessageBox.warning(self, tr('Transaction Not Found'), tr("""
               There was an error creating the promissory note -- the selected
               coins were not found in the blockchain.  Please go to 
               "<i>Help</i>"\xe2\x86\x92"<i>Submit Bug Report</i>" from 
               the main window and submit your log files so the Armory team
               can review this error."""), QMessageBox.Ok)

         rawTx = cppTx.serialize()
         utxoScrAddr = utxo.getRecipientScrAddr()
         aobj = wlt.getAddrByHash160(CheckHash160(utxoScrAddr))
         pubKeys = {utxoScrAddr: aobj.binPublicKey65.toBinStr()}
         ustxiList.append(UnsignedTxInput(rawTx, txoIdx, None, pubKeys))
         

      funderStr = str(self.edtKeyLabel.text()).strip()
      prom = MultiSigPromissoryNote(dtxoTarget, feeAmt, ustxiList, dtxoChange,
                                                                    funderStr)
                                          

      LOGINFO('Successfully created prom note: %s' % prom.promID)

      title = tr("Export Promissory Note")
      descr = tr("""
         The text below includes all the data needed to represent your
         contribution to a simulfunding transaction.  Your money cannot move
         because you have not signed anything, yet.  Once all promissory
         notes are collected, you will be able to review the entire funding 
         transaction before signing.""")
         
      ftypes = ['Promissory Notes (*.promnote)']
      defaultFN = 'Contrib_%s_%sBTC.promnote' % \
            (prom.promID, coin2strNZS(valueAmt))
         

      if not DlgExportAsciiBlock(self, self.main, prom, title, descr,    
                                                ftypes, defaultFN).exec_():
         return False
      else:
         self.accept()
      
      

         

################################################################################
class DlgMergePromNotes(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, lboxID=None):
      super(DlgMergePromNotes, self).__init__(parent, main)


      self.cumulPay = 0
      self.cumulFee = 0
      self.promNotes = []
      self.promIDSet = set([])

      # Will be none
      if lboxID is None:
         self.lbox = None
         self.promMustMatch = None
      else:
         self.lbox = self.main.getLockboxByID(lboxID)
         self.promMustMatch = self.reduceScript(self.lbox.binScript)


      lblTitle  = QRichLabel(tr("""
         <font color="%s" size=4><b>Merge Promissory Notes
         </b></font>""") % htmlColor('TextBlue'), 
         hAlign=Qt.AlignHCenter, doWrap=False)
         
      lblDescr = QRichLabel(tr("""
         Collect promissory notes from two or more parties
         to combine them into a single <i>simulfunding</i> transaction.  Once
         all notes are collected you will be able to
         send it to each contributing party for review and signing."""))


      if self.lbox:
         lbTargStr = '<font color="%s"><b>Lockbox %s-of-%s</b>: %s (%s)</font>' % \
            (htmlColor('TextBlue'), self.lbox.M, self.lbox.N, 
            self.lbox.shortName, self.lbox.uniqueIDB58)
         gboxTarget  = QGroupBox(tr('Lockbox Being Funded'))
      else:
         lbTargStr = '<Nothing Loaded Yet>'
         gboxTarget  = QGroupBox(tr('Address Being Funded'))


      self.lblTarg = QRichLabel(lbTargStr)
      lblPayText = QRichLabel('Total Funding:', doWrap=False)
      lblFeeText = QRichLabel('Total Fee:', doWrap=False)
      self.lblCurrPay = QMoneyLabel(0, maxZeros=2)
      self.lblCurrFee = QMoneyLabel(0, maxZeros=2)
      self.lblPayUnits = QRichLabel('BTC')
      self.lblFeeUnits = QRichLabel('BTC')

      

      gboxTargetLayout = QGridLayout()
      gboxTargetLayout.addWidget(self.lblTarg,      1,0,  1,6)

      gboxTargetLayout.addItem(QSpacerItem(20,20),  2,0)
      gboxTargetLayout.addWidget(lblPayText,        2,1)
      gboxTargetLayout.addItem(QSpacerItem(20,20),  2,2)
      gboxTargetLayout.addWidget(self.lblCurrPay,   2,3)
      gboxTargetLayout.addWidget(self.lblPayUnits,  2,4)

      gboxTargetLayout.addItem(QSpacerItem(20,20),  3,0)
      gboxTargetLayout.addWidget(lblFeeText,        3,1)
      gboxTargetLayout.addItem(QSpacerItem(20,20),  3,2)
      gboxTargetLayout.addWidget(self.lblCurrFee,   3,3)
      gboxTargetLayout.addWidget(self.lblFeeUnits,  3,4)
      gboxTargetLayout.setColumnStretch(0,0)
      gboxTargetLayout.setColumnStretch(1,0)
      gboxTargetLayout.setColumnStretch(2,0)
      gboxTargetLayout.setColumnStretch(3,0)
      gboxTargetLayout.setColumnStretch(4,0)
      gboxTargetLayout.setColumnStretch(5,1)
      gboxTarget.setLayout(gboxTargetLayout) 


      # For when there's no prom note yet
      self.gboxLoaded = QGroupBox(tr('Loaded Promissory Notes'))
      lblNoInfo = QRichLabel(tr("""
         <font size=4><b>No Promissory Notes Have Been Added</b></font>"""),
         hAlign=Qt.AlignHCenter, vAlign=Qt.AlignVCenter)
      gboxLayout = QVBoxLayout()
      gboxLayout.addWidget(lblNoInfo)
      self.gboxLoaded.setLayout(gboxLayout)
      
      self.promModel = PromissoryCollectModel(self.main, self.promNotes)
      self.promView  = QTableView()
      self.promView.setModel(self.promModel)
      self.promView.setSelectionMode(QTableView.NoSelection)
      width0  = relaxedSizeNChar(self.promView,    12)[0]
      width23 = relaxedSizeNChar(GETFONT('Fixed'), 12)[0]
      initialColResize(self.promView, [width0, 300, width23, width23])
      self.promView.horizontalHeader().setStretchLastSection(True)
      self.promView.verticalHeader().setDefaultSectionSize(20)

      self.promLoadStacked = QStackedWidget()
      self.promLoadStacked.addWidget(self.gboxLoaded)
      self.promLoadStacked.addWidget(self.promView)
      self.updatePromTable()

      btnImport = QPushButton(tr('Add Promissory Note'))
      self.connect(btnImport, SIGNAL('clicked()'), self.addPromNote)
      frmImport = makeHorizFrame(['Stretch', btnImport, 'Stretch'])

      btnCancel = QPushButton(tr('Cancel'))
      self.chkBareMS = QCheckBox(tr('Use bare multisig (no P2SH)'))
      btnFinish = QPushButton(tr('Continue'))
      self.connect(btnCancel, SIGNAL('clicked()'), self.reject)
      self.connect(btnFinish, SIGNAL('clicked()'), self.mergeNotesCreateUSTX)
      frmButtons = makeHorizFrame([btnCancel, 
                                   'Stretch', 
                                   self.chkBareMS, 
                                   btnFinish])

      # If this was opened with default lockbox, set visibility, save ms script
      # If opened generic, this will be set first time addPromNote() is called
      self.chkBareMS.setVisible(False)
      if self.lbox is not None:
         self.chkBareMS.setVisible(True)
         self.msTarget = self.lbox.binScript   

      
      mainLayout = QVBoxLayout()
      mainLayout.addWidget(lblTitle, 0)
      mainLayout.addWidget(lblDescr, 0)
      mainLayout.addWidget(HLINE(), 0)
      mainLayout.addWidget(frmImport, 0)
      mainLayout.addWidget(HLINE(), 0)
      mainLayout.addWidget(self.promLoadStacked, 1)
      mainLayout.addWidget(HLINE(), 0)
      mainLayout.addWidget(gboxTarget, 0)
      mainLayout.addWidget(HLINE(), 0)
      mainLayout.addWidget(frmButtons, 0)

      self.setLayout(mainLayout)
      self.setMinimumWidth(700)

      
      
   #############################################################################
   def addPromNote(self):
      title = tr('Import Promissory Note')
      descr = tr("""
         Import a promissory note to add to this simulfunding transaction""") 
      ftypes = ['Promissory Notes (*.promnote)']
      dlgImport = DlgImportAsciiBlock(self, self.main, 
                        title, descr, ftypes, MultiSigPromissoryNote)
      dlgImport.exec_()
      promnote = None
      if dlgImport.returnObj:
         promnote = dlgImport.returnObj
         promnote.pprint()

      # 
      if not promnote:
         QMessageBox.critical(self, tr('Invalid Promissory Note'), tr("""
            No promissory note was loaded."""), QMessageBox.Ok)
         return
      
      # 
      if promnote.promID in self.promIDSet:
         QMessageBox.critical(self, tr('Already Loaded'), tr(""" This 
            promissory note has already been loaded!"""), QMessageBox.Ok)
         return

      
      # reduceScript returns the same scrAddr for a bare multi-sig as it does
      # for it's P2SH form
      targetScript = promnote.dtxoTarget.binScript 
      promTarget = self.reduceScript(targetScript)
      
      # If loaded from main window menu, we have nothing to match yet; set it
      if not self.promMustMatch:
         self.promMustMatch = promTarget

         extraStr = ''
         if getTxOutScriptType(targetScript) in CPP_TXOUT_HAS_ADDRSTR:
            extraStr = '  [%s]' % script_to_addrStr(targetScript)

         contribStr = self.main.getContribStr(targetScript)[0]
         self.lblTarg.setText('<font color="%s"><b>%s</b> %s</font>' % \
            (htmlColor('TextBlue'), contribStr, extraStr ))



         # If this is a multi-sig target, or it's a P2SH multisig we recognize
         # then provide the option to use bare multi-sig (which may be 
         # desriable in certain contexts).
         self.chkBareMS.setVisible(False)
         for lbID,cppWlt in self.main.cppLockboxWltMap.iteritems():
            if cppWlt.hasScrAddress(promTarget):
               LOGINFO('Have lockbox for the funding target: %s' % lbID)
               lb = self.main.getLockboxByID(lbID) 
               if lb and lb.binScript and \
                      getTxOutScriptType(lb.binScript)==CPP_TXOUT_MULTISIG:
                  self.msTarget = lb.binScript   
                  self.chkBareMS.setVisible(True)                   
                  break
               


      # By now, we should always know what target addr ... make sure it matches
      if not promTarget==self.promMustMatch:
         QMessageBox.critical(self, tr('Mismatched Funding Target'), tr("""
            The promissory note you loaded is for a different funding target. 
            Please make sure that all promissory notes are for the target
            specified on the previous window"""), QMessageBox.Ok)
         return

      self.promNotes.append(promnote)
      self.promIDSet.add(promnote.promID)
      self.cumulPay += promnote.dtxoTarget.value
      self.cumulFee += promnote.feeAmt
      
      self.lblCurrPay.setValueText(self.cumulPay, maxZeros=2, wBold=True)
      self.lblCurrFee.setValueText(self.cumulFee, maxZeros=2, wBold=True)

      self.updatePromTable()


   #############################################################################
   def reduceScript(self, script):
      scrType = getTxOutScriptType(script)
      if scrType==CPP_TXOUT_MULTISIG:
         # This is already 
         script = script_to_p2sh_script(script)
      return script_to_scrAddr(script)
         

   #############################################################################
   def updatePromTable(self):
      if len(self.promNotes)==0:
         self.promLoadStacked.setCurrentIndex(0)
      else:
         self.promLoadStacked.setCurrentIndex(1)
      self.promModel.reset()
   
      


   #############################################################################
   def mergeNotesCreateUSTX(self):

      if len(self.promNotes)==0:
         QMessageBox.warning(self, tr('Nothing Loaded'), tr("""
            No promissory notes were loaded.  Cannot create simulfunding 
            transaction."""), QMessageBox.Ok)
         return 

      ustxiList = []
      dtxoList = []

      # We've already made sure all promNotes have the same target
      firstDtxo = self.promNotes[0].dtxoTarget
      dtxoTarget = DecoratedTxOut().unserialize(firstDtxo.serialize())

      if self.chkBareMS.isChecked():
         LOGINFO('Using bare-multisig')
         dtxoTarget.binScript = self.msTarget


      dtxoTarget.value = self.cumulPay
      dtxoList.append(dtxoTarget)

      for prom in self.promNotes:
         for ustxi in prom.ustxInputs:
            updUstxi = UnsignedTxInput().unserialize(ustxi.serialize())
            updUstxi.contribID = prom.promID
            updUstxi.contribLabel = prom.promLabel
            ustxiList.append(updUstxi)

         if prom.dtxoChange:
            updDtxo = DecoratedTxOut().unserialize(prom.dtxoChange.serialize())
            updDtxo.contribID = prom.promID
            dtxoList.append(updDtxo)

      ustx = UnsignedTransaction().createFromUnsignedTxIO(ustxiList, dtxoList)

      title = tr('Export Simulfunding Transaction')
      descr = tr("""
         The text block below contains the simulfunding transaction to be
         signed by all parties funding this lockbox.  Copy the text block
         into an email to all parties contributing funds.  Each party can
         review the final simulfunding transaction, add their signature(s),
         then send back to you to finalize it.  
         <br><br>
         When you click "Done", you will be taken to a window that you can
         use to merge the TXSIGCOLLECT blocks from all parties and broadcast
         the final transaction.""")
      ftypes = ['Signature Collectors (*.sigcollect.tx)']
      defaultFN = 'Simulfund_%s.sigcollect.tx' % ustx.uniqueIDB58
         
      DlgExportAsciiBlock(self, self.main, ustx, title, descr, 
                                                    ftypes, defaultFN).exec_()

      # Assume that it has been exported
      self.accept()
      DlgMultiSpendReview(self, self.main, ustx).exec_()



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



from ui.WalletFrames import SelectWalletFrame
