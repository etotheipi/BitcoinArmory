from PyQt4.Qt import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from qtdefines import *
from qtdialogs import createAddrBookButton, DlgSetComment
from armoryengine.ALL import *

from armoryengine.MultiSigUtils import MultiSigLockbox, getMultiSigID
from ui.MultiSigModels import LockboxDisplayModel,  LOCKBOXCOLS

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
      DlgCreateLockbox(self, self.main).exec_()

   #############################################################################
   def openFund(self):
      DlgFundLockbox(self, self.main).exec_()

   #############################################################################
   def openSpend(self):
      DlgSpendFromLockbox(self, self.main).exec_()
         


#############################################################################
class DlgBrowseLockboxes(ArmoryDialog):
   #############################################################################
   def __init__(self, parent, main):
      super(DlgBrowseLockboxes, self).__init__(parent, main)
    


#############################################################################
class DlgCreateLockbox(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, maxM=5, maxN=5, loadBox=None):
      super(DlgCreateLockbox, self).__init__(parent, main)

      QMessageBox.warning(self, tr('Dangerous Feature!'), tr("""
         Multi-key transaction hacking is an 
         <b>EXPERIMENTAL</b> feature in this version of Armory.  It is 
         <u>not</u> intended to be used with real money, until it is
         moved out of the "Experimental" menu on the main screen.
         <br><br>
         <b>Use at your own risk!</b>"""), QMessageBox.Ok)

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
      btnLoad   = QPushButton(tr('Load Existing'))
      btnImport = QPushButton(tr('Import'))

      self.connect(btnClear,  SIGNAL('clicked()'), self.clearAll)
      self.connect(btnLoad,   SIGNAL('clicked()'), self.loadSaved)
      self.connect(btnImport, SIGNAL('clicked()'), self.importNew)
      
      frmLoadImport = makeVertFrame([btnLoad, btnImport, btnClear])
      frmLoadImport.layout().setSpacing(0)


      layoutMNSelect = QGridLayout()
      layoutMNSelect.addWidget(lblMNSelect,     0,0, 1,9)
      layoutMNSelect.addWidget(self.comboM,     1,2)
      layoutMNSelect.addWidget(lblOfStr,        1,4)
      layoutMNSelect.addWidget(self.comboN,     1,6)
      layoutMNSelect.addWidget(lblBelowM,       2,1, 1,3)
      layoutMNSelect.addWidget(lblBelowN,       2,5, 1,3)
      layoutMNSelect.addWidget(frmLoadImport,   0,9, 3,1)
      layoutMNSelect.setColumnStretch(0,1)
      layoutMNSelect.setColumnStretch(8,1)
      layoutMNSelect.setColumnStretch(9,1)
      
      frmMNSelect = QFrame()
      frmMNSelect.setFrameStyle(STYLE_RAISED)
      frmMNSelect.setLayout(layoutMNSelect)


      frmFinish = makeHorizFrame([self.btnCancel, 'Stretch', self.btnContinue])

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
   def loadSaved(self):
      boxObj = self.main.getSelectLockbox()
      if boxObj:
         self.fillForm(boxObj)

   #############################################################################
   def importNew(self):
      dlg = DlgImportLockbox(self, self.main)
      if dlg.exec_():
         mse = MultiSigLockbox().unserialize(str(dlg.txtBoxBlock.toPlainText()))
         self.fillForm(mse)


   #############################################################################
   def clearAll(self):
      self.edtBoxName.clear()
      self.longDescr = ''
      for key,widget in self.widgetMap.iteritems():
         if key in ['EDT_PUBK', 'LBL_ASTR', 'LBL_NAME']:
            widget.clear()

   
   #############################################################################
   def fillForm(self, boxObj):

      self.edtBoxName.setText(boxObj.shortName)
      self.longDescr = boxObj.longDescr
      self.loadedID = boxObj.uniqueIDB58

      for i in range(boxObj.N):
         self.widgetMap[i]['EDT_PUBK'].setText(binary_to_hex(boxObj.pkList[i]))

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

      print currM,currN

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

      lockboxID = getMultiSigID(txOutScript)
      if self.loadedID is not None:
         if not self.loadedID == lockboxID:
            reply = QMessageBox(self, tr('Different Lockbox'), tr("""
               It appears you changed M, N, or at least one public key in 
               the lockbox that you originally loaded (%s).  Because of that, 
               this is now a different lockbox and will be added to the list
               of available lockboxes, instead of overwriting the original
               lockbox.""") % (self.loadedID, lockboxID), QMessageBox.Ok)
            if reply is not QMessageBox.Ok:
               return
            

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
                                 unicode(self.edtBoxName.text()),
                                 unicode(self.longDescr),
                                 self.NameIDList)

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

      for lb in self.main.allLockboxes:
         lb.pprintOneLine()

      self.main.updateOrAddLockbox(self.lockbox)

      for lb in self.main.allLockboxes:
         lb.pprintOneLine()


################################################################################
class DlgBrowseLockboxes(ArmoryDialog):
   def __init__(self, parent, main):
      super(DlgBrowseLockboxes, self).__init__(parent, main)
   
      lbModel = LockboxDisplayModel(self.main, \
                                    self.main.allLockboxes, \
                                    self.main.getPreferredDateFormat())
      lbView = QTableView()
      lbView.setModel(lbModel)
      lbView.setSelectionBehavior(QTableView.SelectRows)
      lbView.setSelectionMode(QTableView.SingleSelection)
      lbView.verticalHeader().setDefaultSectionSize(20)
      lbView.horizontalHeader().setStretchLastSection(True)

      #maxKeys = max([lb.N for lb in self.main.allLockboxes])
      for i in range(LOCKBOXCOLS.Key0, LOCKBOXCOLS.Key4+1):
         lbView.hideColumn(i)
      #if maxKeys<5: lbView.hideColumn(LOCKBOXCOLS.Key4)
      #if maxKeys<4: lbView.hideColumn(LOCKBOXCOLS.Key3)
      #if maxKeys<3: lbView.hideColumn(LOCKBOXCOLS.Key2)

      layout = QVBoxLayout()
      layout.addWidget(lbView)
      self.setLayout(layout)
      self.setMinimumWidth(700)
      
      

################################################################################
class DlgImportLockbox(QDialog):
   def __init__(self, parent, main):
      super(DlgImportLockbox, self).__init__(parent)
      self.main = main
      lbl = QRichLabel(tr("""
         <b><u>Import Lockbox</u></b>
         <br><br>
         Copy the lockbox text block from file or email into the box 
         below.  If you have a file with the lockbox in it, you can
         load it using the "Load Lockbox" button at the bottom."""))

      self.txtBoxBlock = QPlainTextEdit()
      self.txtBoxBlock.setFont(GETFONT('Fixed', 9))
      w,h = relaxedSizeNChar(self.txtBoxBlock, 64)
      self.txtBoxBlock.setMinimumWidth(w)
      btnLoad = QPushButton(tr("Load from file"))
      btnDone = QPushButton(tr("Done"))
      btnCancel = QPushButton(tr("Cancel"))

                              
      self.connect(btnLoad,   SIGNAL('clicked()'), self.loadfile)
      self.connect(btnDone,   SIGNAL('clicked()'), self.accept)
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

   def loadfile(self):
      boxPath = unicode(self.main.getFileLoad(tr('Load Lockbox')))
      if not boxPath:
         return
      with open(boxPath) as f:
         data = f.read()
      self.txtBoxBlock.setPlainText(data)



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



