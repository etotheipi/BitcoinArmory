# This is a sample plugin file that will be used to create a new tab
# in the Armory main window.  All plugin files (such as this one) will
# be injected with the globals() from ArmoryQt.py, which includes pretty
# much all of Bitcoin & Armory related stuff that you need.  So this
# file can use any utils or objects accessible to functions in ArmoryQt.py.
from PyQt4.Qt import QPushButton, QScrollArea, SIGNAL, QLabel, QLineEdit, \
   QTextEdit, QAbstractTableModel, QModelIndex, Qt
from armoryengine.ArmoryUtils import parseBitcoinURI
from armoryengine.ArmoryLog import LOGERROR
from armoryengine.BDM import getBDM
from armoryengine.ConstructedScript import PaymentRequest, PublicKeySource, \
   PAYNET_BTC, PAYNET_TBTC, PMTARecord
from qtdialogs import DlgSendBitcoins, DlgWalletSelect
from qtdefines import tr, enum, initialColResize
from ui.WalletFrames import SelectWalletFrame
from collections import OrderedDict


from armoryengine.ValidateEmailRegEx import SuperLongEmailValidatorRegex


WALLET_ID_STORE_FILENAME = 'Wallet_DNS_ID_Store.txt'
DNSSEC_URL = "https://en.wikipedia.org/wiki/Domain_Name_System_Security_Extensions"


OTHER_ID_COLS = enum('DnsHandle')
LOCAL_ID_COLS = enum('WalletID', 'WalletName', 'DnsHandle')


# Class name is required by the plugin framework.
class PluginObject(object):
   tabName = 'Armory-Verisign IDs'
   maxVersion = '0.99'

   # NB: As a general rule of thumb, it's wise to not rely on access to anything
   # until the BDM is ready to go and/or Armory has finished loading itself. Any
   # code that must run before both conditions are satisfied (e.g., get info
   # from a wallet) may fail.
   def __init__(self, main):
      self.main = main
      self.wlt = None

      # Set up the GUI.
      lblHeader  = QRichLabel(tr("""
         <b>Wallet Identity Management Tools</b>
         <br><br>
         Armory and Verisign have co-developed a standard for creating 
         wallet identities and linking payment addresses to them in a 
         secure and private manner.  Use this tab to lookup identities 
         using <a href="%s">DNSSEC</a>, or manually import them.  Once
         they are loaded, Armory will be able to securely verify that 
         payment requests made to these wallets/identities are secure.
         You can also use this module to create identities for your 
         wallets, to give to others so that they will recognize payments 
         to your wallets.""") % DNSSEC_URL, doWrap=True)


      # Tracks and displays identities imported manually or from DNSSEC records
      self.modelOtherIDs = OtherWalletIDModel()
      self.tableOtherIDs = QTableView()
      self.tableOtherIDs.setModel(self.modelOtherIDs)
      self.tableOtherIDs.setSelectionBehavior(QTableView.SelectRows)
      self.tableOtherIDs.setSelectionMode(QTableView.SingleSelection)
      self.tableOtherIDs.setMinimumWidth(300)
      initialColResize(self.tableOtherIDs, [0.99])

      # View and manage identities for the wallets you have loaded.
      self.modelLocalIDs = LocalWalletIDModel(self.main)
      self.tableLocalIDs = QTableView()
      self.tableLocalIDs.setModel(self.modelLocalIDs)
      self.tableLocalIDs.setSelectionBehavior(QTableView.SelectRows)
      self.tableLocalIDs.setSelectionMode(QTableView.SingleSelection)
      self.tableLocalIDs.setMinimumWidth(300)
      initialColResize(self.tableLocalIDs, [0.20, 0.40, 0.40])

      self.main.connect(self.tableOtherIDs.selectionModel(), 
                   SIGNAL('currentChanged(const QModelIndex &, const QModelIndex &)'), 
                   self.otherIDclicked)

      self.main.connect(self.tableLocalIDs.selectionModel(), 
                   SIGNAL('currentChanged(const QModelIndex &, const QModelIndex &)'), 
                   self.localIDclicked)

      self.btnOther_Lookup    = QPushButton(tr("Lookup Identity")) 
      self.btnOther_Manual    = QPushButton(tr("Manually Enter ID")) 
      self.btnOther_Verify    = QPushButton(tr("Verify Payment Request"))
      self.btnOther_Export    = QPushButton(tr("Export Selected ID"))
      self.btnOther_Delete    = QPushButton(tr("Delete Selected ID"))

      frmOtherButtons = makeVertFrame([ self.btnOther_Lookup,
                                    self.btnOther_Manual,
                                    self.btnOther_Verify,
                                    self.btnOther_Export,
                                    self.btnOther_Delete,
                                    STRETCH])
      
      self.btnLocal_SetHandle = QPushButton(tr("Set Handle")) 
      self.btnLocal_Publish   = QPushButton(tr("Publish Identity"))
      self.btnLocal_Export    = QPushButton(tr("Export Selected ID"))
      self.btnLocal_Request   = QPushButton(tr("Request Payment to Selected"))

      frmLocalButtons = makeVertFrame([ self.btnLocal_SetHandle,
                                    self.btnLocal_Publish,
                                    self.btnLocal_Export,
                                    self.btnLocal_Request,
                                    STRETCH])
      
      self.otherIDclicked(None)
      self.localIDclicked(None)

      lblHeadOther = QRichLabel(tr("<b>Known Wallet Identities</b>"))
      lblHeadLocal = QRichLabel(tr("<b>Loaded Wallets</b>"))

      layoutOther = QGridLayout()
      layoutOther.addWidget(lblHeadOther,          0,0, 1,2)
      layoutOther.addWidget(self.tableOtherIDs,    1,0, 1,1)
      layoutOther.addWidget(frmOtherButtons,       1,1, 1,1)
      frameOther = QFrame()
      frameOther.setLayout(layoutOther)
  

      layoutLocal = QGridLayout()
      layoutLocal.addWidget(lblHeadLocal,          0,0, 1,2)
      layoutLocal.addWidget(self.tableLocalIDs,    1,0, 1,1)
      layoutLocal.addWidget(frmLocalButtons,       1,1, 1,1)
      frameLocal = QFrame()
      frameLocal.setLayout(layoutLocal)

       
      layoutAll = QVBoxLayout()
      layoutAll.addWidget(lblHeader)
      layoutAll.addWidget(HLINE())
      layoutAll.addWidget(frameOther)
      layoutAll.addWidget(HLINE())
      layoutAll.addWidget(frameLocal)
      frameAll = QFrame()
      frameAll.setLayout(layoutAll)
      

      # Qt GUI calls must occur on the main thread. We need to update the frame
      # once the BDM is ready, so that the wallet balance is shown. To do this,
      # we register a signal with the main thread that can be used to call an
      # associated function.
      self.main.connect(self.main, SIGNAL('bdmReadyPMTA'), self.bdmReady)

      '''
      # Action for when the PKS button is pressed.
      def pksAction():
         if self.wlt != None:
            self.savePKSFile()
         else:
            QMessageBox.warning(self.main, 'No Wallet Chosen',
                                'Please choose a wallet.', QMessageBox.Ok)

      # Action for when the PMTA button is pressed.
      def pmtaAction():
         if self.wlt != None:
            self.savePMTAFile()
         else:
            QMessageBox.warning(self.main, 'No Wallet Chosen',
                                'Please choose a wallet.', QMessageBox.Ok)

      # Action for when the "process payment request" button is pressed.
      # What we want to do is take the incoming Bitcoing URI w/ PMTA field,
      # decode the proof, verify that it's valid (i.e., PKS/CS + PKRP/SRP =
      # Supplied Bitcoin address), and open a pre-filled "Send Bitcoins" dialog.
      # Verfication includes checking DNS first and then checking the Armory
      # ID store (see the ID store plugin) if the record's not on DNS.
      def procPRAction():
         # HACK: Supplying a hard-coded proof for debugging purposes.
         # HACK: THE BASE58 DATA NEEDS TO BE REPLACED WITH A REAL PROOF!!!
         self.payReqTextArea.setText('bitcoin:mokrWMifUTCBysucKZTZ7Uij8915VYcwWX?amount=10.5&pmta=x@x.com:aVYpkBuRQYgBf7Wn9aE8ATmYwV6b2o6jeMvj9KqQYqxkUgswNERoRYU1hSK58gDNhME6viPQYd3TvG5PaSnHbEiF72qp1')
         uriData = parseBitcoinURI(str(self.payReqTextArea.toPlainText()))
         pmtaData = uriData['pmta'].split(':')
         pkrpFinal = PublicKeyRelationshipProof().unserialize(base58_to_binary(pmtaData[1]))
         if pkrpFinal.isValid() is False:
            QMessageBox.warning(self.main, 'Invalid Payment Request',
                                'Payment Request is invalid. Please confirm ' \
                                'that the text is complete and not corrupted.',
                                QMessageBox.Ok)
         else:
            # If the PR is valid, go through the following steps. All steps,
            # unless otherwise noted, are inside a loop based on the # of
            # unvalidated TxOut scripts listed in the record.
            #  1) Check DNS first.
            # 2a) If we get a DNS record, create TxOut using it & matching SRP.
            # 2b) If we don't get a DNS record, confirm that the received ID is
            #     in the ID store.
            #  3) If the ID is acceptable, apply the proof to get the final
            #     address.
            #  4) Confirm the derived address matches the provided address.
            #  5) If the addresses match, generate a "Send Bitcoins" dialog
            #     using the appropriate info.
            resultRecord = None
            resultType = ''
            dlgInfo = {}
            validRecords = True

            # DNS IS IGNORED FOR NOW FOR DEBUGGING PURPOSES. COME BACK LATER.
            #dnsResult = fetchPMTA(uriData['address'], resultRecord, resultType)
            dnsResult = False
            if not dnsResult:
               # Verify that the received record matches the one in the ID
               # store. If so, go ahead with the dialog.
               #idFound = checkIDStore(uriData['pmta'])
               idFound = True
               if not idFound:
                  validRecords = False

            if validRecords:
               # TO DO (Step 3): Derive & apply multipliers from attached PKRP.
               # SRP would apply here if using a CS.

               # TO DO (Step 4): Insert pop-up if derived address doesn't match
               # the supplied address. Also, as a way to show this really works,
               # insert a pop-up saying derivation worked. Wouldn't be done in a
               # prod env either but it's great for a demo!

               # TO DO (Step 5): Replace address w/ derived address as proof
               # that everything worked out.
               dlgInfo['address'] = uriData['address']
               dlgInfo['amount'] = str(uriData['amount'])
               DlgSendBitcoins(self.wlt, self.main, self.main, dlgInfo).exec_()

      # Action for when the "generate payment request" button is pressed.
      # What we want to do is generate a new address for a BIP32 wallet, mark
      # the address as used, get a multiplier that can be applied to the PKS/CS
      # of the wallet, and use the multiplier to generate a Base58-encoded
      # (i.e., PKRP/SRP record) that is then attached to a Bitcoin URI that can
      # be read by Armory or other programs.
      def genPRAction():
         # Confirm that a wallet has actually been chosen and is BIP32-capable.
         if not isinstance(self.wlt, ABEK_StdWallet):
            if self.wlt == None:
               QMessageBox.warning(self.main, 'No wallet selected',
                                   'Please select a wallet which will ' \
                                   'receive the coins.', QMessageBox.Ok)
            else:
               QMessageBox.warning(self.main, 'Wallet object is damaged',
                                   'Please contact Armory.', QMessageBox.Ok)
         else:
            if showRecvCoinsWarningIfNecessary(self.wlt, self.main, self.main):
               # DELETE EVENTUALLY
               pass

               # WARNING: CODE BELOW IS ROUGH AND COMMENTED OUT FOR NOW.
               # Generate the new address and get its multiplier.
               #self.newAddr = wlt.getNextReceivingAddress()
               # Despite the name, we need to make sure the key's uncompressed.
               #baseAddr = wlt.sbdPublicKey33
               #if baseAddr.getSize() == 33:
               #   baseAddr = CryptoECDSA().UncompressPoint(wlt.sbdPublicKey33)

               # CALCULATE MULTIPLIER FOR ROOT, THEN EXT, THEN THE DERIVED KEY.
               # SHOULD PROBABLY MOD ONE OF THE FUNCTS TO JUST RETURN THE MULT.
               # NO POINT IN RECALCULATING EVERYTHING.
               #self.newMult = ???

               # Generate the PKRP using the multiplier.
               #newPKRP = PublicKeyRelationshipProof().initialize(newMult)
               #newPKRPB58 = binary_to_base58(newPKRP.serialize())

               # For demo/debug purposes, show the resultant addr & multiplier.
               # NEED TO FIX CERTAIN VALUES
               #QMessageBox.warning(self.main, 'DEBUG INFORMATION',
               #                    'Root address = %s\nDerived address = %s\n' \
               #                    'Multiplier = %s' % (wlt.getRoot().getExtendedPubKey(),
               #                                         self.newAddr.getAddrStr(),
               #                                         binary_to_hex(newMult)),
               #                    QMessageBox.Ok)

               # Generate the PR. (Throw up a pop-up asking how many coins to pay?)
               #dlg = DlgRequestPayment(self, self.main, addrStr)
               #dlg.exec_()

      # Action for when the add DNS wallet ID button is pressed.
      def addIDAction():
         # str() used so that we save the text to a file.
         wltDNSID = str(self.inID.displayText())

         # We'll allow a user to input a valid email address or enter no text at
         # all. To query DNS for a PMTA record, you must start with a string in
         # an external email address format, which is a tighter form of what's
         # allowed under RFC 822. We'll also let people enter blank text to
         # erase an address. This raises questions of how wallet IDs should be
         # handled in a production env. For now, the ID can change at will.
         if (wltDNSID != '') and (self.validateEmailAddress(wltDNSID) == False):
            QMessageBox.warning(self.main, 'Incorrect ID Formatting',
                                'ID is not blank or in the form of an email ' \
                                'address.',
                                QMessageBox.Ok)
         else:
            self.main.setWltSetting(self.wlt.uniqueIDB58, 'dnsID', wltDNSID)
            QMessageBox.information(self.main, 'ID Saved', 'ID is saved.',
                                    QMessageBox.Ok)

      # Action for when the export DNS wallet ID button is pressed.
      def expIDAction():
         if (str(self.inID.displayText()) != '') and \
            (str(self.inID.displayText()) !=
             self.main.getWltSetting(self.wlt.uniqueIDB58, 'dnsID')):
            QMessageBox.warning(self.main, 'ID Not Saved',
                                'DNS wallet ID must be saved first.',
                                QMessageBox.Ok)
         elif str(self.main.getWltSetting(self.wlt.uniqueIDB58, 'dnsID')) == '':
            QMessageBox.warning(self.main, 'ID Not Saved',
                                'DNS wallet ID must be saved first.',
                                QMessageBox.Ok)
         else:
            # We need to preserve the email address-like string that is the
            # wallet ID. Two periods after the string is guaranteed to be
            # invalid for an email address, so we'll use that.
            expStr = self.main.getWltSetting(self.wlt.uniqueIDB58, 'dnsID') + \
                     '..' + self.pksB58Line.displayText()
            QMessageBox.information(self.main, 'Exportable DNS Wallet ID',
                                'The exportable DNS ID for wallet %s is %s' %
                                (self.wlt.uniqueIDB58, expStr),
                                QMessageBox.Ok)

      # Action for when the clear text button is pressed.
      def clearText():
         self.payReqTextArea.setText('')

      #self.main.connect(self.pksButton,        SIGNAL('clicked()'), pksAction)
      #self.main.connect(self.pmtaButton,       SIGNAL('clicked()'), pmtaAction)
      #self.main.connect(self.procPayReqButton, SIGNAL('clicked()'), procPRAction)
      #self.main.connect(self.genPayReqButton,  SIGNAL('clicked()'), genPRAction)
      #self.main.connect(self.addIDButton,      SIGNAL('clicked()'), addIDAction)
      #self.main.connect(self.exportIDButton,   SIGNAL('clicked()'), expIDAction)
      #self.main.connect(self.clearButton,      SIGNAL('clicked()'), clearText)

      # ID stuff
      idLabel = QLabel('Public Wallet ID: ')
      self.inID = QLineEdit()
      self.inID.setFont(GETFONT('Fixed'))
      self.inID.setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 14)[0])
      self.inID.setAlignment(Qt.AlignLeft)
      idTip = self.main.createToolTipWidget('An ID, in email address form, ' \
                                            'that will be associated with ' \
                                            'this wallet in a DNS record.')

      # Base58 PKS stuff
      pksB58Label = QLabel('PKS (Base 58): ')
      self.pksB58Line = QLineEdit()
      self.pksB58Line.setFont(GETFONT('Fixed'))
      self.pksB58Line.setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 14)[0])
      self.pksB58Line.setAlignment(Qt.AlignLeft)
      self.pksB58Line.setReadOnly(True)
      pksB58Tip = self.main.createToolTipWidget('The wallet\'s PKS record, ' \
                                                'Base58-encoded.')

      # Create the frame and set the scrollarea widget to the layout.
      # self.tabToDisplay is required by the plugin framework.
      pluginFrame = makeVertFrame([headerLabel,
                                   makeHorizFrame([self.btnWltSelect,
                                                   self.selectedWltDisplay,
                                                   'Stretch']),
                                   makeHorizFrame([pksB58Label,
                                                   self.pksB58Line,
                                                   pksB58Tip,
                                                   'Stretch']),
                                   makeHorizFrame([idLabel,
                                                   self.inID,
                                                   idTip,
                                                   'Stretch']),
                                   makeHorizFrame([self.pksButton,
                                                   self.pmtaButton,
                                                   self.procPayReqButton,
                                                   self.genPayReqButton,
                                                   self.addIDButton,
                                                   self.exportIDButton,
                                                   'Stretch']),
                                   payReqLabel,
                                   makeHorizFrame([self.payReqTextArea,
                                                   'Stretch']),
                                   makeHorizFrame([self.clearButton,
                                                   'Stretch']),
                                   'Stretch'])
      '''

      

      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(frameAll)

      # Register the BDM callback for when the BDM sends signals.
      getBDM().registerCppNotification(self.handleBDMNotification)



   #############################################################################
   def otherIDclicked(self, currIndex, prevIndex=None):
      if prevIndex == currIndex:
         return

      if currIndex is None:
         isValid = False
      else:
         qmi = currIndex.model().index(currIndex.row(), OTHER_ID_COLS.DnsHandle)
         self.selectedOtherHandle = str(qmi.data().toString())
         isValid = len(self.selectedOtherHandle) > 0

      self.btnOther_Export.setEnabled(isValid)
      self.btnOther_Delete.setEnabled(isValid)

   #############################################################################
   def localIDclicked(self, currIndex, prevIndex=None):
      if prevIndex == currIndex:
         return

      if currIndex is None:
         isValid = False
      else:
         qmi = currIndex.model().index(currIndex.row(), LOCAL_ID_COLS.WalletID)
         self.selectedLocalWalletID = str(qmi.data().toString())
         isValid = len(self.selectedLocalWalletID) > 0


      self.btnLocal_SetHandle.setEnabled(isValid)
      self.btnLocal_Publish.setEnabled(isValid)
      self.btnLocal_Export.setEnabled(isValid)
      self.btnLocal_Request.setEnabled(isValid)




   # Function that creates and returns a PublicKeySource (PMTA/DNS) record based
   # on the incoming wallet.
   # INPUT:  The wallet used to generate the PKS record (ABEK_StdWallet)
   #         PKS-related flags (bool) - See armoryengine/ConstructedScript.py
   # OUTPUT: None
   # RETURN: Final PKS record (PKSRecord)
   def getWltPKS(self, inWlt, isStatic = False, useCompr = False,
                 use160 = False, isUser = False, isExt = False,
                 chksumPres = False):
      # Start with the wallet's uncompressed root key.
      sbdPubKey33 = SecureBinaryData(inWlt.sbdPublicKey33)
      sbdPubKey65 = CryptoECDSA().UncompressPoint(sbdPubKey33)

      myPKS = PublicKeySource()
      myPKS.initialize(isStatic, useCompr, use160, isUser, isExt,
                       sbdPubKey65.toBinStr(), chksumPres)
      return myPKS


   # Call for when we want to save a binary PKS record to a file. By default,
   # all PKS flags will be false.
   # INPUT:  PKS-related flags (bool) - See armoryengine/ConstructedScript.py
   # OUTPUT: None
   # RETURN: Final PKS record (PKSRecord)
   def savePKSFile(self, isStatic = False, useCompr = False, use160 = False,
                   isUser = False, isExt = False, chksumPres = False):
      defName = 'armory_%s.pks' % self.wlt.uniqueIDB58
      filePath = unicode(self.main.getFileSave(defaultFilename = defName))
      myPKS = None

      if len(filePath) > 0:
         pathdir = os.path.dirname(filePath)
         if not os.path.exists(pathdir):
            raise FileExistsError('Path for new PMTA record does not ' \
                                  'exist: %s', pathdir)
         else:
            myPKS = self.getWltPKS(self.wlt, isStatic, useCompr, use160, isUser,
                              isExt, chksumPres)
            # Write the PKS record to the file, then return the record.
            try:
               with open(filePath, 'wb') as newWltFile:
                  newWltFile.write(binary_to_base58(myPKS.serialize()))
               QMessageBox.information(self.main, 'PKS File Saved',
                                       'PKS file is saved.', QMessageBox.Ok)
            except EnvironmentError:
               QMessageBox.warning(self.main, 'PKS File Save Failed',
                                   'PKS file save failed. Please check your ' \
                                   'file system.', QMessageBox.Ok)
               myPKS = None

      return myPKS


   # Call for when we want to save a binary PMTA record to a file. The PMTA
   # record will include a PKS record for the currently selected wallet. By
   # default, all PKS flags will be false, except for the flag adding a checksum
   # to the PKS record.
   # INPUT:  PKS-related flags (bool) - See armoryengine/ConstructedScript.py
   # OUTPUT: None
   # RETURN: Final PMTA record (PMTARecord)
   def savePMTAFile(self, isStatic = False, useCompr = False, use160 = False,
                    isUser = False, isExt = False, chksumPres = True):
      myPMTA = None

      defName = 'armory_%s.pmta' % self.wlt.uniqueIDB58
      payNet = PAYNET_BTC
      if getTestnetFlag():
         payNet = PAYNET_TBTC

      filePath = unicode(self.main.getFileSave(defaultFilename = defName))
      if not len(filePath) > 0:
         return myPMTA
      else:
         # Start with the wallet's uncompressed root key.
         sbdPubKey33 = SecureBinaryData(self.wlt.sbdPublicKey33)
         sbdPubKey65 = CryptoECDSA().UncompressPoint(sbdPubKey33)

         pathdir = os.path.dirname(filePath)
         if not os.path.exists(pathdir):
            raise FileExistsError('Path for new PKS record does not ' \
                                  'exist: %s', pathdir)

         # Write the PMTA record to the file, then return the record.
         myPMTA = PMTARecord()
         try:
            with open(filePath, 'wb') as newWltFile:
               myPKS = PublicKeySource()
               myPKS.initialize(isStatic, useCompr, use160, isUser, isExt,
                                sbdPubKey65.toBinStr(), chksumPres)
               myPMTA.initialize(myPKS.serialize(), payNet)
               newWltFile.write(binary_to_base58(myPMTA.serialize()))
               QMessageBox.information(self.main, 'PMTA File Saved',
                                       'PMTA file is saved.', QMessageBox.Ok)
         except EnvironmentError:
            QMessageBox.warning(self.main, 'PKS File Save Failed',
                                'PKS file save failed. Please check your ' \
                                'file system.', QMessageBox.Ok)
            myPMTA = None

      return myPMTA


   #############################################################################
   # Validate an email address. Necessary to ensure that the DNS wallet ID is
   # valid. http://www.ex-parrot.com/pdw/Mail-RFC822-Address.html is the source
   # of the (ridiculously long) regex expression. It does not appear to have any
   # licensing restrictions. Using Python's bult-in email.utils.parseaddr would
   # be much cleaner. Unfortunately, it permits a lot of strings that are valid
   # under RFC 822 but are not valid email addresses. It may be worthwhile to
   # add validate_email (https://github.com/syrusakbary/validate_email) to the
   # Armory source tree eventually and just remove this regex abomination.
   # INPUT:  A string with an email address to validate.
   # OUTPUT: None
   # RETURN: A boolean indicating if the email address is valid.
   def validateEmailAddress(self, inAddr):
      validAddr = True
      if not re.match(SuperLongEmailValidatorRegex, inAddr):
         validAddr = False

      return validAddr


   # Function called when the "bdmReadyPMTA" signal is emitted. Updates the
   # wallet balance display on startup.
   # INPUT:  None
   # OUTPUT: None
   # RETURN: None
   def bdmReady(self):
      # Get the PKS record and display it as a Base58-encoded string. Used only
      # for the initial string load.
      pass
      """
      if self.wlt is not None:
         wltPKS = binary_to_base58(self.getWltPKS(self.wlt).serialize())
         self.pksB58Line.setText(wltPKS)

         # If it exists, get the DNS wallet ID.
         wltDNSID = self.main.getWltSetting(self.wlt.uniqueIDB58, 'dnsID')
         self.inID.setText(wltDNSID)
      """


   # Place any code here that must be executed when the BDM emits a signal. The
   # only thing we do is emit a signal so that the call updating the GUI can be
   # called by the main thread. (Qt GUI requirement, lest Armory crash due to a
   # non-main thread updating the GUI.)
   def handleBDMNotification(self, action, args):
      if action == FINISH_LOAD_BLOCKCHAIN_ACTION:
         self.main.emit(SIGNAL('bdmReadyPMTA'))


   #############################################################################
   # Code lifted from armoryd and mdified. Need to place in a common space....
   # INPUT:  The ID used to search for the DNS record. (str)
   # OUTPUT: The PKS/CS obtained from the DNS record. (PKS or CS)
   #         A string indicating the return record type. (
   # RETURN: Boolean indicating whether or not the DNS search succeeded.
   def fetchPMTA(self, inAddr, resultRecord, resultType):
      dnsSucceeded = False
      resultRecord = None
      resultType = ''
      recordUser, recordDomain = inAddr.split('@', 1)
      sha224Res = sha224(recordUser)
      daneReqName = binary_to_hex(sha224Res) + '._pmta.' + recordDomain

      # Go out and get the DANE record.
      pmtaRecType, daneRec = getDANERecord(daneReqName)
      if pmtaRecType == BTCAID_PAYLOAD_TYPE.PublicKeySource:
         # HACK HACK HACK: Just assume we have a PKS record that is static and
         # has a Hash160 value.
         pksRec = PublicKeySource().unserialize(daneRec)

         # Convert Hash160 to Bitcoin address. Make sure we get a PKS, which we
         # won't if the checksum fails.
         if daneRec != None and pksRec != None:
            resultRecord = pksRec
            resultType = 'PKS'
         else:
            raise InvalidDANESearchParam('PKS record is invalid.')

         dnsSucceeded = True
      else:
         raise InvalidDANESearchParam(inAddr + " has no DANE record")

      return dnsSucceeded


   # Function that checks whether of not the wallet ID store has a given ID.
   # INPUT:  The ID the user wishes to find. (str)
   # OUTPUT: None
   # RETURN: Boolean indicating whether or not the ID was found.
   def checkIDStore(self, inRec):
      walletIDStorePath = os.path.join(getArmoryHomeDir(),
                                       WALLET_ID_STORE_FILENAME)
      walletIDStore = SettingsFile(self.walletIDStorePath)
      return walletIDStore.hasSetting(inRec.split('..')[0])


   # Function is required by the plugin framework.
   def getTabToDisplay(self):
      return self.tabToDisplay





################################################################################
class OtherWalletIDModel(QAbstractTableModel):

   #############################################################################
   def __init__(self):
      super(OtherWalletIDModel, self).__init__()
      self.identityMap = OrderedDict()
      self.walletIDStorePath = os.path.join(getArmoryHomeDir(),
                                            WALLET_ID_STORE_FILENAME)

      self.readIdentityFile()


   #############################################################################
   def rowCount(self, index=QModelIndex()):
      return len(self.identityMap)


   #############################################################################
   def columnCount(self, index=QModelIndex()):
      return 1


   #############################################################################
   def data(self, index, role=Qt.DisplayRole):
      retVal = QVariant()
      row,col = index.row(), index.column()

      keyList = self.identityMap.keys()

      if role==Qt.DisplayRole:
         if col==OTHER_ID_COLS.DnsHandle:
            retVal = QVariant(keyList[row])
      elif role==Qt.TextAlignmentRole:
         retVal = QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
      elif role==Qt.ForegroundRole:
         retVal = QVariant(Colors.Foreground)

      return retVal


   #############################################################################
   def headerData(self, section, orientation, role=Qt.DisplayRole):
      retVal = QVariant()
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==OTHER_ID_COLS.DnsHandle:
               retVal = QVariant('Wallet Handle')
      elif role==Qt.TextAlignmentRole:
         if orientation==Qt.Horizontal:
            retVal = QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         else:
            retVal = QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))

      return retVal


   #############################################################################
   def readIdentityFile(self):
      if not os.path.exists(self.walletIDStorePath):
         self.identityMap = OrderedDict()
         return
         
      f = open(self.walletIDStorePath,'r')
      pairs = [l.strip().split() for l in f.readlines() if len(l.strip())>0]
      f.close()
      self.identityMap = OrderedDict(pairs)
      
      

   #############################################################################
   def rewriteIdentityFile(self):
      mainFile = os.path.join(getArmoryHomeDir(), WALLET_ID_STORE_FILENAME)
      tempFile = mainFile + '.temp'

      try:
         with open(tempFile, 'w') as f:
            for key,val in self.identityMap.iteritems():
               f.write('%s %s\n' % (key,val))
   
         shutil.move(tempFile, mainFile)
      except:
         LOGEXCEPT('Failed to update identity file')


   #############################################################################
   # A function that removes the data both from a particular row in a GUI and
   # the matching entry in the ID store file.
   # INPUT:  A row number matching the row in the GUI to remove. (int)
   # OUTPUT: None
   # RETURN: None
   def removeRecord(self, row):
      key = self.identityMap.keys()[row]
      del self.identityMap[key]
      self.rewriteIdentityFile()
      self.reset()


   #############################################################################
   # A function that adds an entry to both the GUI and ID store file.
   # INPUT:  An array with two entries: The wallet ID and the matching
   #         Base58-encoded ID proof (PKS or CS record). ([str str])
   # OUTPUT: None
   # RETURN: None
   def addIdentity(self, dnsHandle, base58Identity):
      if dnsHandle in self.identityMap and not doReplace:
         LOGWARN('Handle is already in ID store.  Updating instead of adding')
         LOGWARN('DNS Handle: %s', dnsHandle)

      self.identityMap[dnsHandle] = base58Identity
      self.rewriteIdentityFile()
      self.reset() # Redraws the screen


   #############################################################################
   def hasDnsHandle(self, wltDnsHandle):
      return (wltDnsHandle in self.identityMap)
      

   #############################################################################
   def findIdentityObject(self, findObjB58):
      for handle,idObj in self.identityMap.iteritems():
         if idObj == findObjB58:
            return handle
      else:
         return None



################################################################################
class LocalWalletIDModel(QAbstractTableModel):

   #############################################################################
   def __init__(self, main):
      super(LocalWalletIDModel, self).__init__()
      self.main = main


   #############################################################################
   def rowCount(self, index=QModelIndex()):
      return len(self.main.wltIDList)


   #############################################################################
   def columnCount(self, index=QModelIndex()):
      return 3


   #############################################################################
   def data(self, index, role=Qt.DisplayRole):
      retVal = QVariant()

      row,col = index.row(), index.column()
      wltID = self.main.wltIDList[row]

      if role==Qt.DisplayRole:
         if col==LOCAL_ID_COLS.WalletID:
            retVal = QVariant(wltID)
         elif col==LOCAL_ID_COLS.WalletName:
            retVal = QVariant(self.main.walletMap[wltID].getLabel())
         elif col==LOCAL_ID_COLS.DnsHandle:
            dnsID = self.main.getWltSetting(wltID, 'dnsID')
            retVal = QVariant('' if len(dnsID)==0 else dnsID)
      elif role==Qt.TextAlignmentRole:
         retVal = QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))

      elif role==Qt.ForegroundRole:
         retVal = QVariant(Colors.Foreground)

      return retVal


   #############################################################################
   def headerData(self, section, orientation, role=Qt.DisplayRole):
      retVal = QVariant()
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==LOCAL_ID_COLS.WalletID:
               retVal = QVariant('Wallet ID')
            elif section==LOCAL_ID_COLS.WalletName:
               retVal = QVariant('Wallet Name')
            elif section==LOCAL_ID_COLS.DnsHandle:
               retVal = QVariant('Wallet Handle')
      elif role==Qt.TextAlignmentRole:
         if orientation==Qt.Horizontal:
            retVal = QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         else:
            retVal = QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))

      return retVal






