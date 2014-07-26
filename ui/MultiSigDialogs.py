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
   createLockboxEntryStr, readLockboxEntryStr, isMofNNonStandardToSpend
from ui.MultiSigModels import \
            LockboxDisplayModel,  LockboxDisplayProxy, LOCKBOXCOLS
import webbrowser
from armoryengine.CoinSelection import PySelectCoins, PyUnspentTxOut, \
                                    pprintUnspentTxOutList
import cStringIO
import textwrap

#############################################################################
class DlgLockboxEditor(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, maxM=LB_MAXM, maxN=LB_MAXN, loadBox=None):
      super(DlgLockboxEditor, self).__init__(parent, main)

      lblDescr = QRichLabel(tr("""
         <b><u><font size=5 color="%s">Create Multi-signature Lockbox</font></u>  
         """) % htmlColor("TextBlue"), hAlign=Qt.AlignHCenter)

      lblDescr2 = QRichLabel(tr("""
         Create a "lockbox" to hold coins that have signing authority split 
         between multiple devices for personal funds, or split between 
         multiple parties for escrow."""))

      lblDescr3 = QRichLabel(tr("""
         <b><u>NOTE:</u> Multi-sig "lockboxes" require <u>public keys</u>, not 
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
            Armory users, they can use the "Select Public Key" button
            from the Lockbox Manager dashboard to pick a key and enter
            their contact info.  You can use the "Import" button
            on each public key line to import the data they send you."""),
            QMessageBox.Ok)
            
            

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


         addrWidgets = self.main.createAddressEntryWidgets(self, '', 60, 2, 
                                       getPubKey=True, showLockboxes=False)
         self.widgetMap[i]['QLE_PUBK'] = addrWidgets['QLE_ADDR']
         self.widgetMap[i]['BTN_BOOK'] = addrWidgets['BTN_BOOK']
         self.widgetMap[i]['LBL_DETECT']=addrWidgets['LBL_DETECT']
         self.widgetMap[i]['LBL_NAME'] = QRichLabel('', doWrap=False)
         self.widgetMap[i]['BTN_NAME']  = QLabelButton(tr('Edit'))
         self.widgetMap[i]['BTN_IMPORT'] = QLabelButton(tr('Import'))
         self.widgetMap[i]['BTN_NAME'].setContentsMargins(0,0,0,0)
         self.widgetMap[i]['LBL_DETECT'].setWordWrap(False)

         # METADATA for a DecoratedPublicKey helps lite wallets
         # identify their own keys, or authenticate keys of others.
         # When a pubkey block is imported we store the public key and 
         # its metadata here indexed by pubkey.  Later, we serialize
         # these into the wallet definition.  We index by public
         # key with it so that we can identify if the user changed the
         # public key since they imported this data in which case we
         # should zero-out the METADATA
         self.widgetMap[i]['METADATA'] = {}


         def createCallback(i):
            def nameClick():
               self.clickNameButton(i)
            return nameClick

         def createImportCallback(i):
            def importClick():
               self.clickImportButton(i)
            return importClick

         self.connect(self.widgetMap[i]['BTN_NAME'], SIGNAL('clicked()'), \
                                                            createCallback(i))
         self.connect(self.widgetMap[i]['BTN_IMPORT'], SIGNAL('clicked()'), \
                                                       createImportCallback(i))
         
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
      self.pkFrameList = []
      for i in range(self.maxN):
         self.pkFrameList.append(QFrame())
         layoutThisRow = QGridLayout()
         layoutThisRow.addWidget(self.widgetMap[i]['IMG_ICON'],   0,0, 3,1)
         layoutThisRow.addWidget(self.widgetMap[i]['LBL_ROWN'],   0,1)
         layoutThisRow.addWidget(self.widgetMap[i]['LBL_WLTN'],   2,1)
         layoutThisRow.addItem(QSpacerItem(10,10),                0,2)
         layoutThisRow.addWidget(self.widgetMap[i]['QLE_PUBK'],   0,3)
         layoutThisRow.addWidget(self.widgetMap[i]['BTN_BOOK'],   0,4)

      
         layoutDetect = QHBoxLayout()
         layoutDetect.addWidget(self.widgetMap[i]['LBL_DETECT'])
         layoutDetect.addStretch()
         layoutDetect.addItem(QSpacerItem(5,5))
         layoutDetect.addWidget(self.widgetMap[i]['BTN_IMPORT'])
         layoutThisRow.addLayout(layoutDetect,                    1,3, 1,2)

         layoutName = QHBoxLayout()
         layoutName.addWidget(self.widgetMap[i]['LBL_NAME'])
         layoutName.addItem(QSpacerItem(5,5))
         layoutName.addWidget(self.widgetMap[i]['BTN_NAME'])
         layoutName.addStretch()
         layoutThisRow.addLayout(layoutName,                      2,3, 1,2)

         layoutThisRow.setColumnStretch(3, 1)
         layoutThisRow.setSpacing(2)

         self.pkFrameList[-1].setLayout(layoutThisRow)
         self.pkFrameList[-1].setFrameStyle(STYLE_SUNKEN)

      self.pkFrameList.append('Stretch')
      frmPubKeys = makeVertFrame( [frmName]+self.pkFrameList, STYLE_RAISED)

      self.scrollPubKeys = QScrollArea()
      self.scrollPubKeys.setWidget(frmPubKeys)
      self.scrollPubKeys.setWidgetResizable(True)


      frmTop = makeVertFrame([lblDescr, lblDescr2, lblDescr3], STYLE_RAISED)
      

      
      # Create the M,N select frame (stolen from frag-create dialog
      lblMNSelect = QRichLabel(tr("""<font color="%s" size=4><b>Create 
         Multi-Sig Lockbox</b></font>""") % htmlColor("TextBlue"), \
         doWrap=False, hAlign=Qt.AlignHCenter)

      lblBelowM = QRichLabel(tr('<b>Required Signatures (M)</b> '), \
                                       hAlign=Qt.AlignHCenter, doWrap=False)
      lblBelowN = QRichLabel(tr('<b>Total Signers (N)</b> '), \
                                       hAlign=Qt.AlignHCenter, doWrap=False)

      lblOfStr = QRichLabel(tr(' - OF - '))


      btnClear  = QPushButton(tr('Clear All'))

      self.connect(btnClear,  SIGNAL('clicked()'), self.clearAll)


      layoutMNSelect = QGridLayout()
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
                              'public key', 'ID or contact info')
      if dlgComm.exec_():
         self.widgetMap[i]['LBL_NAME'].setText(dlgComm.edtComment.text())


   #############################################################################
   def clickImportButton(self, i):

      title = tr("Import Public Key Block")
      descr = tr("""
         <center><b><u>Import Public Key Block</u></b></center>
         <br>
         Copy and paste a PUBLICKEY block into the text field below, 
         or load it from file.  PUBLICKEY files usually have the 
         extension <i>*.lockbox.pub</i>.  If you were given a chunk of hex
         characters starting with "02", "03" or "04", that is a raw public 
         key and can be entered directly into the public key field in the
         lockbox creation window.""")
      ftypes = ['Public Key Blocks (*.lockbox.pub)']

      dlgImport = DlgImportAsciiBlock(self, self.main, 
                        title, descr, ftypes, DecoratedPublicKey)
      dlgImport.exec_()
      if dlgImport.returnObj:
         binPub  = dlgImport.returnObj.binPubKey
         keyComm = dlgImport.returnObj.keyComment
         wltLoc  = dlgImport.returnObj.wltLocator
         authMeth= dlgImport.returnObj.authMethod
         authData= dlgImport.returnObj.authData

         self.widgetMap[i]['QLE_PUBK'].setText(binary_to_hex(binPub))
         self.widgetMap[i]['LBL_NAME'].setText(keyComm)
         self.widgetMap[i]['METADATA'][binPub] = [wltLoc, authMeth, authData]


   #############################################################################
   def setLongDescr(self):

      class DlgSetLongDescr(ArmoryDialog):
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
         self.pkFrameList[i].setVisible(i<N)
         if i>=N:
            self.widgetMap[i]['QLE_PUBK'].setText('')

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
         binPub = lboxObj.dPubKeys[i].binPubKey
         self.widgetMap[i]['QLE_PUBK'].setText(binary_to_hex(binPub))
         self.widgetMap[i]['LBL_NAME'].setText(lboxObj.dPubKeys[i].keyComment)

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
         
         isValid = isLikelyDataType(pkHex, DATATYPE.Hex)
         if isValid:
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

         keyComment = unicode(self.widgetMap[i]['LBL_NAME'].text())
         #self.widgetMap[i]['METADATA'][binPub] = [wltLoc, authMeth, authData]
         extras = [None, None, None]
         if pkBin in self.widgetMap[i]['METADATA']:
            extras = self.widgetMap[i]['METADATA'][pkBin][:]
         pubKeyList.append(DecoratedPublicKey(pkBin, keyComment, *extras))

         # Finally, throw a warning if the comment is not set 
         strComment = str(self.widgetMap[i]['LBL_NAME'].text()).strip()
         if len(strComment)==0 and not acceptedBlankComment:
            reply =QMessageBox.warning(self, tr('Empty Name/ID Field'), tr(""" 
               You did not specify a comment/label for one or more 
               public keys.  Other devices/parties may not be able to 
               identify them.  If this is a multi-party
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
      


      # Sort the public keys lexicographically
      dPubKeys = sorted(pubKeyList, key=lambda lbKey: lbKey.binPubKey)
      binPubKeys = [p.binPubKey for p in dPubKeys] 

      txOutScript = pubkeylist_to_multisig_script(binPubKeys, currM)  
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
      
      if not USE_TESTNET and isMofNNonStandardToSpend(currM, currN):
         reply = QMessageBox.warning(self, tr('Non-Standard to Spend'), tr("""
            Due to limits imposed by Bitcoin Core nodes running versions 
            earlier than 0.10, all spending transactions from this lockbox
            will be rejected by default on the main Bitcoin network 
            (non-standard).  There will be no problem sending coins  
            <u>to</u> the lockbox, but subsequent spends <u>from</u> the 
            lockbox will require an explicit agreement with a mining pool.  
            <br><br>
            Do you wish to continue creating the lockbox, anyway?  Any coins
            sent to will be difficult to spend until Bitcoin Core 0.10
            has been released and used by a significant portion of the 
            Bitcoin network."""), QMessageBox.Yes | QMessageBox.No)

         if not reply==QMessageBox.Yes:
            return

      LOGINFO('Got a valid TxOut script:')
      LOGINFO('ScrAddrStr: ' + binary_to_hex(scraddr))
      LOGINFO('Raw script: ' + binary_to_hex(txOutScript))
      LOGINFO('HR Script: \n   ' + '\n   '.join(opCodeList))
      LOGINFO('Lockbox ID: ' + lockboxID)

      self.lockbox = MultiSigLockbox( toUnicode(self.edtBoxName.text()),
                                      toUnicode(self.longDescr),
                                      currM, 
                                      currN,
                                      dPubKeys,
                                      self.createDate)


      self.main.updateOrAddLockbox(self.lockbox, isFresh=True)
      
      self.accept()
      doExportLockbox(self, self.main, self.lockbox)



################################################################################
def doExportLockbox(parent, main, lockbox):
   title = tr('Export Lockbox Definition')
   descr = tr("""
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
      lockbox manager in order to use it.""") % htmlColor('TextWarn')
   ftypes = ['Lockbox definitions (*.lockbox.def)']
   defaultFN = 'Lockbox_%s_.lockbox.def' % lockbox.asciiID

   DlgExportAsciiBlock(parent, main, lockbox, title, descr, 
                                                 ftypes, defaultFN).exec_()

      

################################################################################
class DlgLockboxManager(ArmoryDialog):
   def __init__(self, parent, main):
      super(DlgLockboxManager, self).__init__(parent, main)

      #if not USE_TESTNET:
         #QMessageBox.warning(self, tr('Dangerous Feature!'), tr("""
            #Multi-signature transactions are an 
            #<b>EXPERIMENTAL</b> feature in this version of Armory.  It is 
            #<u><b>not</b></u> intended to be used with real money, until all 
            #the warnings like this one go away.
            #<br><br>
            #<b>Use at your own risk!</b>"""), QMessageBox.Ok)

      extraTxt = ''
      if len(self.main.allLockboxes) > 0:
         extraTxt = tr('<br>Double-click on a lockbox to edit')

      lblDescr = QRichLabel(tr("""
         <font color="%s" size=4><b>Manage Multi-Sig Lockboxes</b></font>
         %s""") % (htmlColor('TextBlue'), extraTxt), hAlign=Qt.AlignHCenter)
      
      frmDescr = makeVertFrame([lblDescr], STYLE_RAISED)


      # For the dashboard
      self.updateDashboardFuncs = []
   
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
      self.txtLockboxInfo.setStyleSheet('QTextEdit { background-color : %s }' %\
                                                 htmlColor('SlightBkgdLight'))
      self.txtLockboxInfo.setReadOnly(True)
      self.txtLockboxInfo.setFont(GETFONT('Fixed', 9))


      lbGuideURL = "https://bitcoinarmory.com/about/using-lockboxes/"
      lblLinkToMSWebpage = QRichLabel(tr("""Consult our 
         <a href="%s">lockbox documentation</a> for lockbox usage 
         examples and info""") % lbGuideURL, doWrap=False)
      lblLinkToMSWebpage.setOpenExternalLinks(True)

      btnDone = QPushButton(tr('Done'))
      frmDone = makeHorizFrame([lblLinkToMSWebpage, 'Stretch', btnDone])
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
      #layoutDetails.addWidget(frmManageBtns)  # Removed when added dash tab
      layoutDetails.addWidget(self.txtLockboxInfo, 1)
      self.tabDetails.setLayout(layoutDetails)

      # Setup the ledger tab
      self.tabLedger = QWidget()
      layoutLedger = QHBoxLayout()
      layoutLedger.addWidget(self.ledgerView)
      self.tabLedger.setLayout(layoutLedger)

      # Creates self.stkDashboard
      self.createLockboxDashboardTab()

      self.tabbedDisplay = QTabWidget()
      self.tabbedDisplay.addTab(self.stkDashboard, tr("Dashboard"))
      self.tabbedDisplay.addTab(self.tabDetails, tr("Info"))
      self.tabbedDisplay.addTab(self.tabLedger, tr("Transactions"))


      self.tabbedDisplay.setTabEnabled(2, TheBDM.getBDMState()=='BlockchainReady')


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
   def createLockboxDashboardTab(self):

      ORGANIZER   = 'Organizer'
      ANYONE = 'Anyone'

      self.allDashButtons = [{}, {}]


      # We need two of these dictionaries:  we're going to put the widgets
      # directly into them, and we need one for each of the two stack pages
      for i in [0,1]:
         self.allDashButtons[i] = \
         {
         'CreateLB':   { \
               'button':  tr('Create Lockbox'),
               'callbk':  self.doCreate,
               'organiz': True,
               'lbltxt':  tr('Collect public keys'),
               'tiptxt':  tr("""Create a lockbox by collecting public keys
                                from each device or person that will be 
                                a signing authority over the funds.  Once
                                created you will be given a chunk of text
                                to send to each party so they can recognize
                                and sign transactions related to the 
                                lockbox."""),
               'select':  None,
               'offline': None},

         'SelectKey':  { \
               'button':  tr('Select Public Key'),
               'callbk':  self.doSelectKey,
               'organiz': False,
               'lbltxt':  tr('Send to organizer'),
               'tiptxt':  tr("""In order to create a lockbox all devices 
                                and/or parties need to provde a public key 
                                that they control to be merged by the 
                                organizer.  Once all keys are collected,
                                the organizer will send you the final
                                lockbox definition to import."""),
               'select':  None,
               'offline': None},

         'ExportLB':   { \
               'button':  tr('Export Lockbox'),
               'callbk':  self.doExport,
               'organiz': False,
               'lbltxt':  tr('Send to other devices or parties'),
               'tiptxt':  tr("""Export a lockbox definition to be imported
                                by other devices are parties.  Normally the 
                                lockbox organizer will do this after all public
                                keys are collected, but any participant who 
                                already has it can send it, such as if one 
                                party/device accidentally deletes it."""),
               'select':  tr('Select lockbox to export'),
               'offline': None},

         'ImportLB':   { \
               'button':  tr('Import Lockbox'),
               'callbk':  self.doImport,
               'organiz': False,
               'lbltxt':  tr('From organizer or other device'),
               'tiptxt':  tr("""Import a lockbox definition to begin
                                tracking its funds and to be able to
                                sign related transactions.
                                Normally, the organizer will send you 
                                send you the data to import after you
                                provide a public key from one of your
                                wallets."""),
               'select':  None,
               'offline': None},

         'EditLB':     { \
               'button':  tr('Edit Lockbox'),
               'callbk':  self.doEdit,
               'organiz': False,
               'lbltxt':  '',
               'tiptxt':  tr('Edit an existing lockbox'),
               'select':  tr('Select lockbox to edit'),
               'offline': None},

         #'RegFund':    { \
               #'button':  tr('Fund Lockbox'),
               #'callbk':  self.doFundIt,
               #'organiz': False,
               #'lbltxt':  tr('Fund selected lockbox from any wallet'),
               #'tiptxt':  tr("""If you would like to fund this lockbox
                                #from another lockbox, select the funding 
                                #lockbox in the table and click the
                                #"Create Spending Tx" button.  Use the 
                                #address book to select this lockbox as the
                                #recipient of that transaction. 
                                #<br><br> 
                                #If multiple people will be funding
                                #this lockbox and not all of them are fully 
                                #trusted, click the "Simul" checkbox on the 
                                #left to see the simulfunding options."""),
               #'select':  tr('Select a lockbox to fund<br>'),
               #'offline': tr('Must be online to fund<br>')},
               # Added <br> to the labels to force to be two lines... this
               # is a hack to make sure that the row inits to a reasonable
               # size on open
               

         'MergeProm':  { \
               'button':  tr('Merge Promissory Notes'),
               'callbk':  self.doMergeProm,
               'organiz': True,
               'lbltxt':  '',
               'tiptxt':  tr("""Collect promissory notes from all funders
                                of a simulfunding transaction.  Use this to
                                merge them into a single transaction that 
                                the funders can review and sign."""),
               'select':  None,
               'offline': None},

         'CreateProm': { \
               'button':  tr('Create Promissory Note'),
               'callbk':  self.doCreateProm,
               'organiz': False,
               'lbltxt':  tr('Make a funding commitment to a lockbox'),
               'tiptxt':  tr("""A "promissory note" provides blockchain
                                information about how your wallet will 
                                contribute funds to a simulfunding transaction.
                                A promissory note does <b>not</b>
                                move any money in your wallet.  The organizer
                                will create a single transaction that includes
                                all promissory notes and you will be able to 
                                review it in its entirety before signing."""),
               'select':  tr('Select lockbox to commit funds to'),
               'offline': tr('Must be online to create')},

         'RevSign':    { \
               'button':  tr('Review and Sign'),
               'callbk':  self.doReview,
               'organiz': False,
               'lbltxt':  tr('Multi-sig spend or simulfunding'),
               'tiptxt':  tr("""Review and sign any lockbox-related
                                transaction that requires multiple 
                                signatures.  This includes spending 
                                transactions from a regular lockbox,
                                as well as completing a simulfunding
                                transaction."""),
               'select':  None,
               'offline': None},

         'CreateTx':   { \
               'button':  tr('Create Spending Tx'),
               'callbk':  self.doSpend,
               'organiz': True,
               'lbltxt':  tr('Send bitcoins from lockbox'),
               'tiptxt':  tr("""Create a proposed transaction sending bitcoins
                                to an address, wallet or another lockbox.  
                                The transaction will not be final until enough
                                signatures have been collected and then 
                                broadcast from an online computer."""),
               'select':  tr('Select lockbox to spend from'),
               'offline': tr('Must be online to spend')},


         'MergeSigs':  { \
               'button':  tr('Collect Sigs && Broadcast'),
               'callbk':  self.doReview,
               'organiz': True,
               'lbltxt':  tr('Merge signatures to finalize'),
               'tiptxt':  tr('Merge signatures and broadcast transaction'),
               'select':  None,
               'offline': tr('(must be online to broadcast)')},
      }


      # We will have two pages on the stack.  The first one is for regular
      # funding with all the simulfunding options missing.  The second one
      # is re-arranged (but mostly the same widgets) but with the additional
      # simulfunding widgets
      self.stkDashboard = QStackedWidget()

      simultxt = 'Simul'
      self.chkSimulfundA = QCheckBox(simultxt)
      self.chkSimulfundB = QCheckBox(simultxt)

      ttipSimulTxt = tr("""
         If this lockbox will be funded by multiple parties and not all
         parties are fully trusted, use "simulfunding" to ensure that funds 
         are committed at the same time.  Check the "Simul" box to show 
         simulfunding options in the table.""")
      ttipSimulA = self.main.createToolTipWidget(ttipSimulTxt)
      ttipSimulB = self.main.createToolTipWidget(ttipSimulTxt)
         

      def clickSimulA():
         self.chkSimulfundB.setChecked(self.chkSimulfundA.isChecked())
         stk = 1 if self.chkSimulfundA.isChecked() else 0
         self.stkDashboard.setCurrentIndex(stk)

      def clickSimulB():
         self.chkSimulfundA.setChecked(self.chkSimulfundB.isChecked())
         stk = 1 if self.chkSimulfundB.isChecked() else 0
         self.stkDashboard.setCurrentIndex(stk)
      
         self.chkSimulfundB.setChecked(self.chkSimulfundA.isChecked())

      self.connect(self.chkSimulfundA, SIGNAL('clicked()'), clickSimulA)
      self.connect(self.chkSimulfundB, SIGNAL('clicked()'), clickSimulB)


      cellWidth = 150
      cellStyle = STYLE_RAISED
      def createHeaderCell(headStr, extraWidgList=None):
         lbl = QRichLabel(headStr, bold=True, size=4,
                                   hAlign=Qt.AlignHCenter,
                                   vAlign=Qt.AlignVCenter)
          
          
         if extraWidgList is None:
            frm = makeVertFrame([lbl], cellStyle) 
         else:
            botLayout = QHBoxLayout()
            for widg in extraWidgList:
               botLayout.addWidget(widg)
            botLayout.setSpacing(0)
            cellLayout = QVBoxLayout()
            cellLayout.addWidget(lbl)
            cellLayout.addLayout(botLayout)
            frm = QFrame()
            frm.setLayout(cellLayout)
            frm.setFrameStyle(cellStyle)
            

         return frm


      self.updateDashFuncs = []
      def createCell(stk, btnKeyList, direct=HORIZONTAL):
         layoutMulti = QHBoxLayout() if direct==HORIZONTAL else QVBoxLayout()

         for key in btnKeyList:
            layout = QGridLayout()
            btnMap = self.allDashButtons[stk][key]
            btnMap['BTN'] = QPushButton(btnMap['button'])
            btnMap['LBL'] = QRichLabel('', doWrap=True, hAlign=Qt.AlignHCenter, vAlign=Qt.AlignTop)
            btnMap['TTIP'] = self.main.createToolTipWidget(btnMap['tiptxt'])
            if btnMap['organiz']:
               btnMap['BTN'].setAutoFillBackground(True)
               btnMap['BTN'].setStyleSheet(\
                  'QPushButton { background-color : %s }' % htmlColor('SlightMoreBlue'))

            layout.addWidget(btnMap['BTN'],   0,0)
            layout.addWidget(btnMap['TTIP'],  0,1)
            layout.addWidget(btnMap['LBL'],   1,0)
            layout.setColumnStretch(0,1)
            layout.setColumnStretch(1,0)
            self.connect(btnMap['BTN'], SIGNAL('clicked()'), btnMap['callbk'])

            slayout = QHBoxLayout()
            slayout.addStretch()
            slayout.addLayout(layout)
            slayout.addStretch()
            layoutMulti.addLayout(slayout)

            def updateWidgets(stkPage, btnKey):
               btnMap = self.allDashButtons[stkPage][btnKey]
               def updateFunc(hasSelect, isOnline):
                  # Default to regular label
                  lbltxt = btnMap['lbltxt']
                  orgtxt = '<font color="%s"><b>Organizer</b></font><br>' % \
                                                       htmlColor('TextBlue')

                  btnMap['BTN'].setText(btnMap['button'])
                  btnMap['BTN'].setEnabled(True)
                  btnMap['LBL'].setEnabled(True)
                  if isOnline:
                     if not hasSelect and btnMap['select'] is not None:
                        lbltxt = btnMap['select']
                        btnMap['BTN'].setEnabled(False)
                        btnMap['LBL'].setEnabled(False)
                  else:
                     if btnMap['offline'] is not None:
                        lbltxt = btnMap['offline']
                        btnMap['BTN'].setEnabled(False)
                        btnMap['LBL'].setEnabled(False)
                     else:
                        if not hasSelect and btnMap['select'] is not None:
                           lbltxt = btnMap['select']
                           btnMap['BTN'].setEnabled(False)
                           btnMap['LBL'].setEnabled(False)

                  if btnMap['organiz']:
                     btnMap['LBL'].setText(orgtxt + lbltxt)
                     btnMap['LBL'].setWordWrap(False)
                  else:
                     btnMap['LBL'].setText(lbltxt)

                  # Semi-hack:  
                  #    The 'MergeSigs' button is the only one that kinda makes 
                  #    sense to not work offline, but there may be isolated 
                  #    cases where the user would merge without intending to 
                  #    broadcast.  Having it disabled in offline mode would
                  #    make them go mad.  So I'm going to explicitly make sure
                  #    that just that button is always enabled, even though
                  #    it might look like a bug.
                  if btnKey=='MergeSigs':
                     btnMap['BTN'].setEnabled(True)

               return updateFunc

            # Add the func to the list of things to call on context change
            self.updateDashFuncs.append(updateWidgets(stk, key))

         frmCell = QFrame()
         frmCell.setLayout(layoutMulti)
         frmCell.setFrameStyle(STYLE_RAISED)

         
         # This was calibrated to linux, but at least it will work on one OS
         # The alternative was squished text on every OS
         w,h = tightSizeNChar(btnMap['LBL'], 30)
         frmCell.setMinimumHeight(5.5*h)

         return frmCell


      ##### REGULAR FUNDING - Special Cell ####
      # This FUND row for regular funding will be totally unlike the others
      # Create it here instead of with the the createCell() function
      self.lblDispAddr = QRichLabel('', doWrap=False, hAlign=Qt.AlignHCenter)
      self.lblDispAddr.setTextInteractionFlags(Qt.TextSelectableByMouse | \
                                               Qt.TextSelectableByKeyboard)
      self.btnFundRegular = QPushButton(tr('Fund from Wallet'))
      self.btnQRCodeDisp  = QPushButton(tr('QR Code'))
      self.btnFundRequest = QPushButton(tr('Request Payment'))
      self.btnCopyClip = QPushButton(tr('Copy Address'))

      def funcCopyClip():  
         lbox = self.getSelectedLockbox()
         if not lbox:
            return
         self.btnCopyClip.setText('Copied!')
         clipb = QApplication.clipboard()
         clipb.clear()
         clipb.setText(scrAddr_to_addrStr(lbox.p2shScrAddr))
         from twisted.internet import reactor
         reactor.callLater(1, lambda: self.btnCopyClip.setText('Copy Address'))

      def funcReqPayment():  
         lbox = self.getSelectedLockbox()
         if not lbox:
            return
         p2shAddr = scrAddr_to_addrStr(lbox.p2shScrAddr)
         DlgRequestPayment(self, self.main, p2shAddr).exec_()

      def funcQRCode():
         lbox = self.getSelectedLockbox()
         if not lbox:
            return
         p2shAddr = scrAddr_to_addrStr(lbox.p2shScrAddr)
         lboxDisp = 'Lockbox %d-of-%d: "%s" (%s)' % (lbox.M, lbox.N, 
                           lbox.shortName, lbox.uniqueIDB58)
         DlgQRCodeDisplay(self, self.main, p2shAddr, p2shAddr, lboxDisp).exec_()

      self.connect(self.btnCopyClip,    SIGNAL('clicked()'), funcCopyClip)
      self.connect(self.btnQRCodeDisp,  SIGNAL('clicked()'), funcQRCode)
      self.connect(self.btnFundRequest, SIGNAL('clicked()'), funcReqPayment)
      self.connect(self.btnFundRegular, SIGNAL('clicked()'), self.doFundIt)

      def updateRegFundCell(hasSelect, isOnline):
         lbox = self.getSelectedLockbox()
         self.btnCopyClip.setText(tr('Copy Address'))
         if not hasSelect or not lbox:
            self.btnQRCodeDisp.setEnabled(False)
            self.btnFundRegular.setEnabled(False)
            self.btnFundRequest.setEnabled(False)
            self.btnCopyClip.setEnabled(False)
            self.lblDispAddr.setEnabled(False)
            self.lblDispAddr.setText('No lockbox selected')
         else:
            p2shAddr = scrAddr_to_addrStr(lbox.p2shScrAddr)
            self.btnFundRegular.setEnabled(isOnline)
            self.btnQRCodeDisp.setEnabled(True)
            self.btnFundRequest.setEnabled(True)
            self.btnCopyClip.setEnabled(True)
            self.lblDispAddr.setEnabled(True)
            self.lblDispAddr.setText(tr("""
               Anyone can send funds to this lockbox using this
               Bitcoin address: <br><b>%s</b>""") % p2shAddr)

      self.updateDashFuncs.append(updateRegFundCell)

      layoutFundRow = QGridLayout()
      layoutFundRow.addWidget( self.btnFundRegular,  0,2)
      layoutFundRow.addWidget( self.btnQRCodeDisp,   0,3)
      layoutFundRow.addWidget( self.btnFundRequest,  0,4)
      layoutFundRow.addWidget( self.btnCopyClip,     0,5)
      layoutFundRow.addWidget( self.lblDispAddr,     1,1, 1,6)
      layoutFundRow.setColumnStretch(0, 1)
      layoutFundRow.setColumnStretch(1, 1)
      layoutFundRow.setColumnStretch(2, 0)
      layoutFundRow.setColumnStretch(3, 0)
      layoutFundRow.setColumnStretch(4, 0)
      layoutFundRow.setColumnStretch(5, 0)
      layoutFundRow.setColumnStretch(6, 1)
      layoutFundRow.setColumnStretch(7, 1)
      frmFundRegCell = QFrame()
      frmFundRegCell.setLayout(layoutFundRow)
      frmFundRegCell.setFrameStyle(STYLE_RAISED)

      ##### REGULAR FUNDING - Special Cell ####
            

      # First frame is for regular funding.  Switch to frmMulti if chkSimulfundA
      frmSingle = QFrame()
      frmSingleLayout = QGridLayout()

      firstRow  = createCell(0, ['CreateLB', 'SelectKey', 'ExportLB', 'ImportLB'], HORIZONTAL)
      #secondRow = createCell(0, ['RegFund'], HORIZONTAL)
      thirdRow  = createCell(0, ['CreateTx', 'RevSign', 'MergeSigs'], HORIZONTAL)

      frmSingleLayout.addWidget(createHeaderCell('CREATE'),    0,0)
      frmSingleLayout.addWidget(firstRow,                      0,1,  1,3)

      frmSingleLayout.addWidget(createHeaderCell('FUND', 
                            [self.chkSimulfundA, ttipSimulA]), 1,0)
      frmSingleLayout.addWidget(frmFundRegCell,                   1,1,  1,3)

      frmSingleLayout.addWidget(createHeaderCell('SPEND'),     2,0)
      frmSingleLayout.addWidget(thirdRow,                      2,1,  1,3)

      frmSingleLayout.setColumnStretch(0,0)
      frmSingleLayout.setColumnStretch(1,1)
      frmSingleLayout.setColumnStretch(2,1)
      frmSingleLayout.setColumnStretch(3,1)
      frmSingleLayout.setSpacing(1)
      frmSingleLayout.setColumnMinimumWidth(0,100)

      frmSingle.setLayout(frmSingleLayout)
      frmSingle.setFrameStyle(STYLE_STYLED)
      self.stkDashboard.addWidget(frmSingle)


      # Second frame is for simulfunding
      frmMulti = QFrame()
      frmMultiLayout = QGridLayout()

      firstRow  = createCell(1, ['CreateLB', 'SelectKey', 'ExportLB', 'ImportLB'], HORIZONTAL)
      secondRow = createCell(1, ['MergeProm', 'CreateProm'], HORIZONTAL)
      lastCol   = createCell(1, ['RevSign', 'MergeSigs'], VERTICAL)
      thirdRow  = createCell(1, ['CreateTx'], HORIZONTAL)

      frmMultiLayout.addWidget(createHeaderCell('CREATE'),    0,0)
      frmMultiLayout.addWidget(firstRow,                      0,1,  1,3)

      frmMultiLayout.addWidget(createHeaderCell('FUND', 
                           [self.chkSimulfundB, ttipSimulB]), 1,0)
      frmMultiLayout.addWidget(secondRow,                     1,1,  1,2)
      frmMultiLayout.addWidget(lastCol,                       1,3,  2,1)

      frmMultiLayout.addWidget(createHeaderCell('SPEND'),     2,0)
      frmMultiLayout.addWidget(thirdRow,                      2,1,  1,2)


      frmMultiLayout.setColumnStretch(0,0)
      frmMultiLayout.setColumnStretch(1,1)
      frmMultiLayout.setColumnStretch(2,1)
      frmMultiLayout.setColumnStretch(3,1)
      frmMultiLayout.setSpacing(1)
      frmMultiLayout.setRowMinimumHeight(1,100)
      frmMultiLayout.setRowMinimumHeight(2,100)
      frmMultiLayout.setColumnMinimumWidth(0,100)

      frmMulti.setLayout(frmMultiLayout)
      frmMulti.setFrameStyle(STYLE_STYLED)
      self.stkDashboard.addWidget(frmMulti)

      # Default is to use frmSingle
      self.stkDashboard.setCurrentIndex(0)

         
      

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
      wlt = None
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

      row = self.ledgerView.selectedIndexes()[0].row()

      txHash = str(self.ledgerView.model().index(row, LEDGERCOLS.TxHash).data().toString())
      txHash = hex_switchEndian(txHash)
      wltID  = str(self.ledgerView.model().index(row, LEDGERCOLS.WltID).data().toString())

      if USE_TESTNET:
         blkExploreTitle = 'View on blockexplorer.com'
         blkExploreURL   = 'http://blockexplorer.com/testnet/tx/%s' % txHash
      else:
         blkExploreTitle = 'View on blockchain.info'
         blkExploreURL   = 'https://blockchain.info/tx/%s' % txHash


      actViewTx     = menu.addAction("View Details")
      actViewBlkChn = menu.addAction(blkExploreTitle)
      actComment    = menu.addAction("Change Comment")
      actCopyTxID   = menu.addAction("Copy Transaction ID")
      action = menu.exec_(QCursor.pos())


      if action==actViewTx:
         self.showLedgerTx()
      elif action==actViewBlkChn:
         try:
            webbrowser.open(blkExploreURL)
         except:
            LOGEXCEPT('Failed to open webbrowser')
            QMessageBox.critical(self, 'Could not open browser', \
               'Armory encountered an error opening your web browser.  To view '
               'this transaction on blockchain.info, please copy and paste '
               'the following URL into your browser: '
               '<br><br>%s' % blkExploreURL, QMessageBox.Ok)
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

      

      if True:  actionCopyAddr    = menu.addAction("Copy P2SH address")
      if True:  actionShowQRCode  = menu.addAction("Display address QR code")
      if not USE_TESTNET:
         actionBlkChnInfo  = menu.addAction("View address on %s" % BLOCKEXPLORE_NAME)
      else:
         actionBlkChnInfo = None
      if True:  actionReqPayment  = menu.addAction("Request payment to this lockbox")
      if dev:   actionCopyHash160 = menu.addAction("Copy hash160 value (hex)")
      if True:  actionCopyBalance = menu.addAction("Copy balance")
      if True:  actionRemoveLB    = menu.addAction("Delete Lockbox")

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
            urlToOpen = BLOCKEXPLORE_URL_ADDR % p2shAddr
            try:
               import webbrowser
               webbrowser.open(urlToOpen)
            except:
               QMessageBox.critical(self, tr('Could not open browser'), tr("""
                  Armory encountered an error opening your web browser.  To view 
                  this address on %s, please copy and paste 
                  the following URL into your browser: 
                  <br><br>
                  <a href="%s">%s</a>""") % (BLOCKEXPLORE_NAME, urlToOpen, 
                  urlToOpen), QMessageBox.Ok)
            return
         elif action == actionShowQRCode:
            DlgQRCodeDisplay(self, self.main, p2shAddr, p2shAddr, createLockboxEntryStr(lboxId)).exec_()
            return
         elif action == actionReqPayment:
            if not self.main.getSettingOrSetDefault('DNAA_P2SHCompatWarn', False):
               oldStartChar = "'m' or 'n'" if USE_TESTNET else "'1'"
               newStartChar = "'2'"        if USE_TESTNET else "'3'"
               reply = MsgBoxWithDNAA(MSGBOX.Warning, tr('Compatibility Warning'), 
                  tr("""You are about to request payment to a "P2SH" address 
                  which is the format used for receiving to multi-signature
                  addresses/lockboxes.  "P2SH" are like regular Bitcoin 
                  addresses but start with %s instead of %s.
                  <br><br>
                  Unfortunately, not all software and services support sending 
                  to P2SH addresses.  If the sender or service indicates   
                  an error sending to this address, you might have to request
                  payment to a regular wallet address and then send the funds
                  from that wallet to the lockbox once it is confirmed.""") % \
                  (newStartChar, oldStartChar), 
                  dnaaMsg=tr('Do not show this message again'))
               
               if reply[1]==True:
                  self.main.writeSetting('DNAA_P2SHCompatWarn', True)
         
            DlgRequestPayment(self, self.main, p2shAddr).exec_()
            return
         elif dev and action == actionCopyHash160:
            clippy = binary_to_hex(addrStr_to_hash160(p2shAddr)[1])
         elif action == actionCopyBalance:
            clippy = getModelStr(LOCKBOXCOLS.Balance)
         elif action == actionRemoveLB:
            dispInfo = self.main.getDisplayStringForScript(lbox.binScript)
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
               self.main.removeLockbox(lbox)
               self.lboxModel.reset()
               self.singleClickLockbox()

            return
         else:
            return
   
         clipb = QApplication.clipboard()
         clipb.clear()
         clipb.setText(str(clippy).strip())

   #############################################################################
   def updateButtonDisable(self):
      noSelection = (self.getSelectedLBID() is None)
      isOffline = (not TheBDM.getBDMState()=='BlockchainReady')

      """
      # Removed all these when we added the dashboard tab
      self.btnEdit.setDisabled(noSelection)
      self.btnExport.setDisabled(noSelection)
      self.btnDelete.setDisabled(noSelection)

      self.btnFundIt.setDisabled(noSelection or isOffline)
      self.btnSimul.setDisabled(noSelection)
      self.btnSpend.setDisabled(noSelection)
      """
      
      if noSelection:
         self.txtLockboxInfo.setText(tr(""" <br><br><font color="%s"><center><b>
            Select a lockbox from the table above to view its info</b></center>
            </font>""") % htmlColor('DisableFG'))

      for fn in self.updateDashFuncs:
         # Whoops, made the args inverses of what the func takes, oh well
         fn(not noSelection, not isOffline)
      
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
   def getDisplayRichText(self, lb, tr=None, dateFmt=None):

      if dateFmt is None:
         dateFmt = DEFAULT_DATE_FORMAT

      if tr is None:
         tr = lambda x: unicode(x)

      EMPTYLINE = u''

      shortName = toUnicode(lb.shortName)
      if len(shortName.strip())==0:
         shortName = u'<No Lockbox Name'

      longDescr = toUnicode(lb.longDescr)
      if len(longDescr.strip())==0:
         longDescr = '--- No Extended Info ---'
      longDescr = longDescr.replace('\n','<br>')
      longDescr = textwrap.fill(longDescr, width=60)


      formattedDate = unixTimeToFormatStr(lb.createDate, dateFmt)
      
      lines = []
      lines.append(tr("""<font color="%s" size=4><center><u>Lockbox Information for 
         <b>%s</b></u></center></font>""") % (htmlColor("TextBlue"), lb.uniqueIDB58))
      lines.append(tr('<b>Multisig:</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%d-of-%d') % (lb.M, lb.N))
      lines.append(tr('<b>Lockbox ID:</b>&nbsp;&nbsp;&nbsp;&nbsp;%s') % lb.uniqueIDB58)
      lines.append(tr('<b>P2SH Address:</b>&nbsp;&nbsp;%s') % binScript_to_p2shAddrStr(lb.binScript))
      lines.append(tr('<b>Lockbox Name:</b>&nbsp;&nbsp;%s') % lb.shortName)
      lines.append(tr('<b>Created:</b>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%s') % formattedDate) 
      lines.append(tr('<b>Extended Info:</b><hr><blockquote>%s</blockquote><hr>') % longDescr)
      lines.append(tr('<b>Stored Key Details</b>'))
      for i in range(len(lb.dPubKeys)):
         comm = lb.dPubKeys[i].keyComment
         addr = hash160_to_addrStr(lb.a160List[i])
         pubk = binary_to_hex(lb.dPubKeys[i].binPubKey)[:40] + '...'

         if len(comm.strip())==0:
            comm = '<No Info>'

         lines.append(tr('&nbsp;&nbsp;<b>Key #%d</b>') % (i+1))
         lines.append(tr('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Name/ID:</b>&nbsp;%s') % comm)
         lines.append(tr('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Address:</b>&nbsp;%s') % addr)
         lines.append(tr('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>PubKey:</b>&nbsp;&nbsp;%s') % pubk)
         lines.append(EMPTYLINE)
      lines.append(tr('</font>'))
      return '<br>'.join(lines)

   #############################################################################
   def singleClickLockbox(self, index=None, *args):
      lb = self.getSelectedLockbox()
      if lb:
         self.txtLockboxInfo.setText(self.getDisplayRichText(lb))
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
   def doSelectKey(self):
      dlg = DlgSelectPublicKey(self, self.main).exec_()

   #############################################################################
   def doImport(self):
      dlg = DlgImportLockbox(self, self.main)
      if dlg.exec_():
         if dlg.importedLockbox is not None:
            self.main.updateOrAddLockbox(dlg.importedLockbox, isFresh=True)
            if not self.main.getSettingOrSetDefault('DNAA_LockboxImport', False):
               reply = MsgBoxWithDNAA(MSGBOX.Info, tr("Import Successful"), tr("""
                  The lockbox was imported successfully.  If this is a new 
                  lockbox that has never been used before, then you
                  can start using it right away.  
                  <br><br>
                  If the lockbox is not new and has been used before,
                  Armory will not know about its history until you rescan
                  the databases.  You can manually initiate a rescan by
                  going to "<i>Help</i>"\xe2\x86\x92"<i>Rescan Databases</i>"
                  from the main window."""), tr("Do not show this message again"))

               if reply[1]:
                  self.main.writeSetting('DNAA_LockboxImport', True)
               
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
      doExportLockbox(self, self.main, lb)
      self.updateButtonDisable()


   #############################################################################
   def doMergeProm(self):
      lb = self.getSelectedLockbox()
      lbID = None if lb is None else lb.uniqueIDB58
      DlgMergePromNotes(self, self.main, lbID).exec_()
                        

   #############################################################################
   def doCreateProm(self):
      lb = self.getSelectedLockbox()
      lbID = None if lb is None else lb.uniqueIDB58
      DlgCreatePromNote(self, self.main, lbID).exec_()


   
   #############################################################################
   def doReview(self):
      title = tr("Import Signature Collector")
      descr = tr("""
         Import a <i>Signature Collector</i> block to review and
         sign the lockbox-spend or simulfunding transaction.  This text block 
         is produced by the organizer and will contain
         "=====TXSIGCOLLECT" on the first line.   Or you can import it from
         a file, which is saved by default with a
         <i>*.sigcollect.tx</i> extension.""")
      ftypes = ['Signature Collectors (*.sigcollect.tx)']
      dlgImport = DlgImportAsciiBlock(self, self.main, 
                        title, descr, ftypes, UnsignedTransaction)
      dlgImport.exec_()
      if dlgImport.returnObj:
         ustx = dlgImport.returnObj
         DlgMultiSpendReview(self, self.main, ustx).exec_()


   #############################################################################
   def doDelete(self):
      lb = self.getSelectedLockbox()
      dispInfo = self.main.getDisplayStringForScript(lb.binScript, 100, 2,
                                                      prefIDOverAddr=True)
      reply = QMessageBox.warning(self, tr('Confirm Delete'), tr("""
         "Removing" a lockbox does not delete any signing keys, so you 
         maintain signing authority for any coins that are sent there.     
         However, Armory will stop tracking its history and balance, and you
         will have to re-import it later in order to sign any transactions.
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
            <li>You are the only one expected to fund this lockbox/escrow</li>
            <li>All other parties in the lockbox/escrow are fully trusted</li>
            <li>This lockbox is being used for personal savings</li>
         </ul>
         If the above does not apply to you, please press "Cancel" and 
         select the "Simul" checkbox on the lockbox dashboard.
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
      #dispStr = '<font color="%s"><b>%s-of-%s</b>: %s (%s)</font>' % \
         #(htmlColor('TextBlue'), lbox.M, lbox.N, lbox.shortName, lbox.uniqueIDB58)
      dispStr = self.main.getDisplayStringForScript(lbox.binScript)['String']

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
class DlgImportAsciiBlock(ArmoryDialog):
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
class DlgSelectPublicKey(ArmoryDialog):
   def __init__(self, parent, main):
      super(DlgSelectPublicKey, self).__init__(parent, main)

      lblDescr = QRichLabel(tr("""
         <center><font size=4><b><u>Select Public Key for Lockbox 
         Creation</u></b></font></center>
         <br>
         Lockbox creation requires <b>public keys</b> not the regular Bitcoin
         addresses most users are accustomed to.  A public key is much longer
         than a regular bitcoin address, usually starting with "02", "03" or
         "04".  Once you have selected a public key, send it to the lockbox 
         organizer (person or device).  The organizer will create the lockbox 
         which then must be imported by all devices that will track the funds
         and/or sign transactions.
         <br><br>
         It is recommended that you select a <i>new</i> key from one of your
         wallets that will not be used for any other purpose.
         You <u>can</u> use a public key from a watching-only wallet (for 
         an offline wallet), but you will have to sign the transactions the
         same way you would a regular offline transaction.  Additionally the 
         offline computer will need to have Armory version 0.92 or later.
         <br><br>
         <b><font color="%s">BACKUP WARNING</b></b>:  
         It is highly recommended that you select a public key from a
         wallet for which you have good backups!  If you are creating a lockbox
         requiring the same number of signatures as there are authorities 
         (such as 2-of-2 or 3-of-3), the loss of the wallet <u>will</u> lead 
         to loss of lockbox funds!  
         """) % htmlColor('TextRed'))

      lblSelect  = QRichLabel(tr('Select Public Key:'), doWrap=False)
      lblContact = QRichLabel(tr('Notes or Contact Info:'), doWrap=False)
      ttipContact = self.main.createToolTipWidget(tr("""
         If multiple people will be part of this lockbox, you should 
         specify name and contact info in the box below, which will be
         available to all parties that import the finalized lockbox.
         <br><br>
         If this lockbox will be shared among devices you own (such as for
         personal savings), specify information that helps you identify which
         device is associated with this public key."""))

      self.edtContact = QLineEdit()
      w,h = relaxedSizeNChar(self.edtContact, 60)
      self.edtContact.setMinimumWidth(w)
      
      frmDescr = makeVertFrame([lblDescr], STYLE_RAISED)

      addrWidgets = self.main.createAddressEntryWidgets(self, '', 60, 2, 
                                       getPubKey=True, showLockboxes=False)

      self.edtPubKey   = addrWidgets['QLE_ADDR']
      self.btnAddrBook = addrWidgets['BTN_BOOK']
      self.lblDetect   = addrWidgets['LBL_DETECT']
      self.lblDetect.setVisible(True)

      #btnExportKey = QPushButton(tr('Send to Organizer'))
      #self.connect(btnExportKey, SIGNAL('clicked()'), self.doExportKey)
      #frmButtons = makeHorizFrame([QRichLabel(tr('When finished:')),
                                   #btnExportKey, 
                                   #'Stretch'])

      layoutAddrEntry = QGridLayout()
      layoutAddrEntry.addWidget(lblSelect,                  0,0)
      layoutAddrEntry.addWidget(self.edtPubKey,             0,1)
      layoutAddrEntry.addWidget(self.btnAddrBook,           0,2)
      layoutAddrEntry.addWidget(self.lblDetect,             1,1,  1,2)
      layoutAddrEntry.addWidget(lblContact,                 2,0)
      layoutAddrEntry.addWidget(self.edtContact,            2,1)
      layoutAddrEntry.addWidget(ttipContact,                2,2)
      #layoutAddrEntry.addWidget(frmButtons,                 3,0,  1,3)
      layoutAddrEntry.setColumnStretch(0,0)
      layoutAddrEntry.setColumnStretch(1,1)
      layoutAddrEntry.setColumnStretch(2,0)
      frmAddrEntry = QFrame()
      frmAddrEntry.setLayout(layoutAddrEntry)
      

      btnDone = QPushButton(tr('Continue'))
      btnCancel = QPushButton(tr('Cancel'))
      self.connect(btnDone,   SIGNAL('clicked()'), self.doDone)
      self.connect(btnCancel, SIGNAL('clicked()'), self.reject)
      frmDone = makeHorizFrame([btnCancel, 'Stretch', btnDone])
      

      mainLayout = QVBoxLayout()
      mainLayout.addWidget(frmDescr)
      mainLayout.addWidget(frmAddrEntry)
      mainLayout.addWidget(HLINE())
      mainLayout.addWidget(frmDone)
      self.setLayout(mainLayout)
      self.setMinimumWidth(600)

      self.setWindowTitle(tr('Select Public Key for Lockbox'))
      self.setWindowIcon(QIcon(self.main.iconfile))


   #############################################################################
   def collectKeyData(self):
      try:
         binPub = hex_to_binary(str(self.edtPubKey.text()).strip())
         if binPub[0] in ['\x02', '\x03'] and len(binPub)==33:
            pass  # valid key
         elif binPub[0]=='\x04' and len(binPub)==65:
            if not CryptoECDSA().VerifyPublicKeyValid(SecureBinaryData(binPub)):
               raise BadAddressError('Public key starting with 0x04 is invalid')
         else:
            raise BadAddressError('Invalid pub key entered, or not a pub key')

      except:
         LOGEXCEPT('Invalid public key entered')
         QMessageBox.warning(self, tr('Invalid Public Key'), tr("""
            You must enter a public key into the box, <b>not</b> a regular 
            Bitcoin address that most users are accustomed to.  A public key 
            is much longer than a Bitcoin address, and always starts with 
            "02", "03" or "04"."""), QMessageBox.Ok)
         return None

      comm = unicode(self.edtContact.text()).strip() 
      dPubKey = DecoratedPublicKey(binPub, comm)
      return dPubKey.serializeAscii()
      
      

   #############################################################################
   def doExportKey(self):
      toCopy = self.collectKeyData()
      if not toCopy:
         return 

      dPubKey = DecoratedPublicKey().unserializeAscii(toCopy)

      title = tr("Export Public Key for Lockbox")
      descr = tr("""
         The text below includes both the public key and the notes/contact info
         you entered.  Please send this text to the organizer (person or device) 
         to be used to create the lockbox.  This data is <u>not</u> sensitive 
         and it is appropriate be sent via email or transferred via USB storage.
         """)
         
      ftypes = ['Public Key Blocks (*.lockbox.pub)']
      defaultFN = 'PubKey_%s_.lockbox.pub' % dPubKey.pubKeyID
         
      DlgExportAsciiBlock(self, self.main, dPubKey, title, descr, 
                                                    ftypes, defaultFN).exec_()

      
   def doDone(self):
      if self.collectKeyData() is None:
         return 

      self.doExportKey()
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
      txt.setReadOnly(True)

      self.lblCopyMail = QRichLabel('')
      btnCopy = QPushButton(tr("Copy to Clipboard"))
      btnSave = QPushButton(tr("Save to File"))
      btnMail = QPushButton(tr("Send Email"))
      btnDone = QPushButton(tr("Done"))

      self.connect(btnCopy, SIGNAL('clicked()'), self.clipcopy)
      self.connect(btnSave, SIGNAL('clicked()'), self.savefile)
      self.connect(btnMail, SIGNAL('clicked()'), self.mailLB)
      self.connect(btnDone, SIGNAL('clicked()'), self.accept)

      frmCopy = makeHorizFrame([btnSave, btnCopy, btnMail, self.lblCopyMail, \
                                'Stretch'])
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
      self.lblCopyMail.setText('<i>Copied!</i>')


   def mailLB(self):
      # Iterate over the text block and get the public key ID.
      # WARNING: For now, the code assumes there will be only one ID returned.
      # If this changes in the future, the code must be adjusted as necessary.
      blockIO = cStringIO.StringIO(self.asciiBlock)
      pkID = getBlockID(blockIO, self.exportObj.BLKSTRING+'-')[0]

      # Prepare to send an email with the public key. For now, the email text
      # is the public key and nothing else.
      subj = tr(self.exportObj.EMAILSUBJ) % self.exportObj.asciiID
      body = tr(self.exportObj.EMAILBODY)
      urlText = 'mailto:?subject=%s&body=%s\n\n%s' % (subj, body, self.asciiBlock)
      finalUrl = QUrl(urlText)
      QDesktopServices.openUrl(finalUrl)

      
      if not self.main.getSettingOrSetDefault('DNAA_MailtoWarn', False):
         reply = MsgBoxWithDNAA(MSGBOX.Warning, tr('Email Triggered'), tr("""
            Armory attempted to execute a "mailto:" link which should trigger
            your email application or web browser to open a compose-email window.
            This does not work in all environments, and you might have to 
            manually copy and paste the text in the box into an email.
            """), dnaaMsg=tr('Do not show this message again'), dnaaStartChk=True)

         if reply[1]:
            self.main.writeSetting('DNAA_MailtoWarn', True)

      self.lblCopyMail.setText('<i>Email produced!</i>')


################################################################################
class DlgImportLockbox(ArmoryDialog):
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
                                                 ['Lockboxes (*.lockbox.def)'])
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
   def __init__(self, parent, main, ustx):
      super(DlgMultiSpendReview, self).__init__(parent, main)

      LOGDEBUG('Debugging information for multi-spend USTX')
      #ustx.pprint()

      lblDescr = QRichLabel(tr("""
         The following transaction is a proposed spend of funds controlled
         by multiple parties.  The keyholes next to each input represent 
         required signatures for the tx to be valid.  White
         means it has not yet been signed, and cannot be signed by you.  Green
         represents signatures that can be added by one of your wallets.
         Gray keyholes are already signed.
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
      canPotentiallySignAny = False
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
            canPotentiallySignAny = True

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
               canPotentiallySignAny = True
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
            else:
               # In these cases, nothing really to do
               pass
               
            

      # The output bundles are quite a bit simpler 
      isReceivingAny = False
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

         if idStr[:3] in ['LB:', 'WLT']:
            isReceivingAny = True


      if not canPotentiallySignAny:
         if not isReceivingAny:
            QMessageBox.warning(self, tr("Unrelated Multi-Spend"), tr("""
               The signature-collector you loaded appears to be
               unrelated to any of the wallets or lockboxes that you have
               available.  If you were expecting to be able to sign for a
               lockbox input, you need to import the lockbox definition    
               first.  Any other person or device with the lockbox loaded
               can export it to be imported by this device."""), QMessageBox.Ok)
         else:
            QMessageBox.warning(self, tr("Cannot Sign"), tr("""
               The signature-collector you loaded is sending money to one
               of your wallets or lockboxes, but does not have any inputs
               for which you can sign.  
               If you were expecting to be able to sign for a
               lockbox input, you need to import the lockbox definition    
               first.  Any other person or device with the lockbox loaded
               can export it to be imported by this device."""), QMessageBox.Ok)
            

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
                  comm = lbox.dPubKeys[i].keyComment
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
      defaultFN = 'MultisigTransaction_%s_.sigcollect.tx' % self.ustx.uniqueIDB58
         
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
         #self.ustx.evaluateSigningStatus().pprint()
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
         self.parent.tabbedDisplay.setCurrentIndex(2)
      except:
         try:
            self.parent.parent.tabbedDisplay.setCurrentIndex(2)
         except:
            pass
      self.accept()
         


################################################################################
class DlgCreatePromNote(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, defaultIDorAddr=None, skipExport=False):
      super(DlgCreatePromNote, self).__init__(parent, main)

      self.finalPromNote = None
      self.skipExport = skipExport

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

      startStr = ''
      if defaultIDorAddr:
         if checkAddrStrValid(defaultIDorAddr):
            startStr = defaultIDorAddr
         else:
            startStr = createLockboxEntryStr(defaultIDorAddr)

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
      self.edtKeyLabel.setMaxLength(144)
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
            You did not specify an amount to promise!"""), QMessageBox.Ok)
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

      
      totalAmt = valueAmt + feeAmt
      availBal = wlt.getBalance('Spendable')
      if totalAmt > availBal:
         QMessageBox.critical(self, tr('Not enough funds!'), tr("""
            You specified <b>%s</b> BTC (amount + fee), but the selected wallet
            only has <b>%s</b> BTC spendable.""") % (coin2strNZS(totalAmt), 
            coin2strNZS(availBal)), QMessageBox.Ok)
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
      #pprintUnspentTxOutList(utxoSelect)
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
      self.finalPromNote = MultiSigPromissoryNote(dtxoTarget, feeAmt, 
                                       ustxiList, dtxoChange, funderStr)
                                          

      LOGINFO('Successfully created prom note: %s' % self.finalPromNote.promID)

      if self.skipExport:
         self.accept()
      else:
         title = tr("Export Promissory Note")
         descr = tr("""
            The text below includes all the data needed to represent your
            contribution to a simulfunding transaction.  Your money cannot move
            because you have not signed anything, yet.  Once all promissory
            notes are collected, you will be able to review the entire funding 
            transaction before signing.""")
         
         ftypes = ['Promissory Notes (*.promnote)']
         defaultFN = 'Contrib_%s_%sBTC.promnote' % \
               (self.finalPromNote.promID, coin2strNZS(valueAmt))
            
   
         if not DlgExportAsciiBlock(self, self.main, self.finalPromNote, title, 
                                             descr, ftypes, defaultFN).exec_():
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
         #lbTargStr = '<font color="%s"><b>Lockbox %s-of-%s</b>: %s (%s)</font>' % \
            #(htmlColor('TextBlue'), self.lbox.M, self.lbox.N, 
            #self.lbox.shortName, self.lbox.uniqueIDB58)
         lbTargStr = self.main.getDisplayStringForScript(self.lbox.binScript)
         lbTargStr = lbTargStr['String']
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

      btnImport = QPushButton(tr('Import Promissory Note'))
      btnCreate = QPushButton(tr('Create && Add Promissory Note'))
      self.connect(btnImport, SIGNAL('clicked()'), self.importNote)
      self.connect(btnCreate, SIGNAL('clicked()'), self.createPromAdd)
      frmImport = makeHorizFrame(['Stretch', btnImport, btnCreate, 'Stretch'])

      btnCancel = QPushButton(tr('Cancel'))
      self.chkBareMS = QCheckBox(tr('Use bare multisig (no P2SH)'))
      self.ttipBareMS = self.main.createToolTipWidget( tr("""
         EXPERT OPTION:  Do not check this box unless you know what it means
                         and you need it!  Forces Armory to exposes public 
                         keys to the blockchain before the funds are spent.  
                         This is only needed for very specific use cases, 
                         and otherwise creates blockchain bloat."""))
      btnFinish = QPushButton(tr('Continue'))
      self.connect(btnCancel, SIGNAL('clicked()'), self.reject)
      self.connect(btnFinish, SIGNAL('clicked()'), self.mergeNotesCreateUSTX)
      frmButtons = makeHorizFrame([btnCancel, 
                                   'Stretch', 
                                   self.chkBareMS, 
                                   self.ttipBareMS,
                                   btnFinish])

      # If this was opened with default lockbox, set visibility, save ms script
      # If opened generic, this will be set first time importNote() is called
      self.chkBareMS.setVisible(False)
      self.ttipBareMS.setVisible(False)
      if self.lbox is not None:
         self.chkBareMS.setVisible(True)
         self.ttipBareMS.setVisible(True)
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
   def importNote(self):
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
         #promnote.pprint()

      if not promnote:
         QMessageBox.critical(self, tr('Invalid Promissory Note'), tr("""
            No promissory note was loaded."""), QMessageBox.Ok)
         return
      

      self.addNote(promnote)


   #############################################################################
   def createPromAdd(self):
      if not TheBDM.getBDMState()=='BlockchainReady':
         QMessageBox.warning(self, tr("Not Online"), tr("""
            Armory is currently in offline mode and cannot create any 
            transactions or promissory notes.  You can only merge 
            pre-existing promissory notes at this time."""), QMessageBox.Ok)
         return
            
  
      defaultTarg = None
      if self.promMustMatch:
         for lbox in self.main.allLockboxes:
            if lbox.p2shScrAddr == self.promMustMatch:
               defaultTarg = lbox.uniqueIDB58
               break
         else:
            defaultTarg = scrAddr_to_addrStr(self.promMustMatch)
               
         
      dlg = DlgCreatePromNote(self, self.main, defaultTarg, skipExport=True)
      dlg.exec_()
      if dlg.finalPromNote:
         self.addNote(dlg.finalPromNote)
      


   #############################################################################
   def addNote(self, promnote):
      
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

         contribStr = self.main.getContribStr(targetScript)[0]
         self.lblTarg.setText('<font color="%s"><b>%s</b></font>' % \
            (htmlColor('TextBlue'), contribStr))



         # If this is a multi-sig target, or it's a P2SH multisig we recognize
         # then provide the option to use bare multi-sig (which may be 
         # desriable in certain contexts).
         self.chkBareMS.setVisible(False)
         self.ttipBareMS.setVisible(False)
         for lbID,cppWlt in self.main.cppLockboxWltMap.iteritems():
            if cppWlt.hasScrAddress(promTarget):
               LOGINFO('Have lockbox for the funding target: %s' % lbID)
               lb = self.main.getLockboxByID(lbID) 
               if lb and lb.binScript and \
                      getTxOutScriptType(lb.binScript)==CPP_TXOUT_MULTISIG:
                  self.msTarget = lb.binScript   
                  self.chkBareMS.setVisible(True)  
                  self.ttipBareMS.setVisible(True)                 
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

      if len(self.promNotes)==1:
         reply = QMessageBox.warning(self, tr('Merging One Note'), tr("""
            Only one promissory note was entered, so there
            is nothing to merge.  
            <br><br>
            The simulfunding interface is intended to merge promissory notes
            from multiple parties to ensure simultaneous funding 
            for escrow.  If only person is funding, they 
            can simply send money to the address or lockbox like they would 
            any other transaction, without going through the simulfunding 
            interface.
            <br><br>
            Click "Ok" to continue to the multi-signing interface, but there
            will only be one input to sign."""), QMessageBox.Ok)
         
         if not reply==QMessageBox.Ok:
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
      self.setWindowTitle(tr('Multi-Sig Lockboxes'))


   #############################################################################
   def openCreate(self):
      DlgLockboxEditor(self, self.main).exec_()


   #############################################################################
   def openFund(self):
      DlgFundLockbox(self, self.main).exec_()


   #############################################################################
   def openSpend(self):
      DlgSpendFromLockbox(self, self.main).exec_()


# Get around circular dependencies
from ui.WalletFrames import SelectWalletFrame
