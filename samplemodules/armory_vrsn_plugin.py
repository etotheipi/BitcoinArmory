# This is a sample plugin file that will be used to create a new tab
# in the Armory main window.  All plugin files (such as this one) will
# be injected with the globals() from ArmoryQt.py, which includes pretty
# much all of Bitcoin & Armory related stuff that you need.  So this
# file can use any utils or objects accessible to functions in ArmoryQt.py.
from collections import OrderedDict
import os
import re
import shutil

from PyQt4.Qt import QPushButton, QScrollArea, SIGNAL, QLabel, QLineEdit, \
   QTextEdit, QAbstractTableModel, QModelIndex, Qt, QTableView, QGridLayout, \
   QFrame, QVBoxLayout, QMessageBox, QVariant, QDialogButtonBox, QApplication

from CppBlockUtils import SecureBinaryData, CryptoECDSA
from armorycolors import Colors
from armoryengine.ArmoryLog import LOGERROR, LOGWARN, LOGEXCEPT, LOGINFO
from armoryengine.ArmoryOptions import getTestnetFlag, getArmoryHomeDir, \
   isWindows
from armoryengine.ArmorySettings import SettingsFile
from armoryengine.ArmoryUtils import binary_to_base58, sha224, binary_to_hex
from armoryengine.BDM import getBDM
from armoryengine.Constants import STRETCH, FINISH_LOAD_BLOCKCHAIN_ACTION, \
   BTCAID_PAYLOAD_TYPE, CLICKED
from armoryengine.ConstructedScript import PaymentRequest, PublicKeySource, \
   PAYNET_BTC, PAYNET_TBTC, PMTARecord, PublicKeyRelationshipProof, \
   PaymentTargetVerifier, DeriveBip32PublicKeyWithProof
from armoryengine.Exceptions import FileExistsError, InvalidDANESearchParam
from armoryengine.ValidateEmailRegEx import SuperLongEmailValidatorRegex
from qtdefines import tr, enum, initialColResize, QRichLabel, tightSizeNChar, \
   makeVertFrame, makeHorizFrame, HLINE, ArmoryDialog
from qtdialogs import DlgSendBitcoins, DlgWalletSelect
from ui.WalletFrames import SelectWalletFrame


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

      w,h = tightSizeNChar(QTableView(), 45)
      viewWidth  = 1.2*w
      sectionSz  = 1.3*h
      viewHeight = 4.4*sectionSz

      # Tracks and displays identities imported manually or from DNSSEC records
      self.modelOtherIDs = OtherWalletIDModel()
      self.tableOtherIDs = QTableView()
      self.tableOtherIDs.setModel(self.modelOtherIDs)
      self.tableOtherIDs.setSelectionBehavior(QTableView.SelectRows)
      self.tableOtherIDs.setSelectionMode(QTableView.SingleSelection)
      self.tableOtherIDs.setMinimumWidth(viewWidth)
      self.tableOtherIDs.setMinimumHeight(6.5*sectionSz)
      self.tableOtherIDs.verticalHeader().setDefaultSectionSize(sectionSz)
      self.tableOtherIDs.verticalHeader().hide()
      initialColResize(self.tableOtherIDs, [0.99])

      # View and manage identities for the wallets you have loaded.
      self.modelLocalIDs = LocalWalletIDModel(self.main)
      self.tableLocalIDs = QTableView()
      self.tableLocalIDs.setModel(self.modelLocalIDs)
      self.tableLocalIDs.setSelectionBehavior(QTableView.SelectRows)
      self.tableLocalIDs.setSelectionMode(QTableView.SingleSelection)
      self.tableLocalIDs.setMinimumWidth(viewWidth)
      self.tableLocalIDs.setMinimumHeight(6.5*sectionSz)
      self.tableLocalIDs.verticalHeader().setDefaultSectionSize(sectionSz)
      self.tableLocalIDs.verticalHeader().hide()
      initialColResize(self.tableLocalIDs, [0.20, 0.40, 0.40])

      self.main.connect(self.tableOtherIDs.selectionModel(),
                        SIGNAL('currentChanged(const QModelIndex &, ' \
                                               'const QModelIndex &)'),
                        self.otherIDclicked)

      self.main.connect(self.tableLocalIDs.selectionModel(),
                        SIGNAL('currentChanged(const QModelIndex &, ' \
                                               'const QModelIndex &)'),
                        self.localIDclicked)

      self.btnOtherLookup = QPushButton(tr("Lookup Identity"))
      self.btnOtherManual = QPushButton(tr("Manually Enter ID"))
      self.btnOtherVerify = QPushButton(tr("Verify Payment Request"))
      self.btnOtherExport = QPushButton(tr("Export Selected ID"))
      self.btnOtherExport.setEnabled(False)
      self.btnOtherDelete = QPushButton(tr("Delete Selected ID"))
      self.btnOtherDelete.setEnabled(False)

      frmOtherButtons = makeVertFrame([self.btnOtherLookup,
                                       self.btnOtherManual,
                                       self.btnOtherVerify,
                                       self.btnOtherExport,
                                       self.btnOtherDelete,
                                       STRETCH])

      self.btnLocalSetHandle = QPushButton(tr("Set Handle"))
      self.btnLocalSetHandle.setEnabled(False)
      self.btnLocalPublish = QPushButton(tr("Publish Identity"))
      self.btnLocalPublish.setEnabled(False)
      self.btnLocalExport = QPushButton(tr("Export Selected ID"))
      self.btnLocalExport.setEnabled(False)
      self.btnLocalRequest = QPushButton(tr("Request Payment to Selected"))
      self.btnLocalRequest.setEnabled(False)

      frmLocalButtons = makeVertFrame([self.btnLocalSetHandle,
                                       self.btnLocalPublish,
                                       self.btnLocalExport,
                                       self.btnLocalRequest,
                                       STRETCH])

#      self.otherIDclicked(None)
#      self.localIDclicked(None)

      lblHeadOther = QRichLabel(tr("<b>Known Wallet Identities (Others)</b>"))
      lblHeadLocal = QRichLabel(tr("<b>Loaded Wallets (Yours)</b>"))

      layoutOther = QGridLayout()
      layoutOther.addWidget(lblHeadOther,          0,0, 1,2)
      layoutOther.addWidget(self.tableOtherIDs,    1,0, 1,1)
      layoutOther.addWidget(frmOtherButtons,       1,1, 1,1)
      frameOtherSub = QFrame()
      frameOtherSub.setLayout(layoutOther)
      frameOther = makeHorizFrame([frameOtherSub, STRETCH])

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

      # Perform a DNS lookup on a handle. The result, if found, will be added to
      # the ID store.
      def otherWalletIdentityLookupAction():
         self.otherWalletIdentityLookup()

      # Manually enter a handle and a Base58-encoded blob into a pop-up.
      def enterWalletIdentityAction():
         self.enterWalletIdentity()

      # SHOULD PROBABLY RENAME THE ASSOCIATED BUTTON
      # Paste in a proof and verify that the proof is accurate, then open a
      # "Send Bitcoins" dialog that's filled in.
      def ovAction():
         #
         pass

      # Show an easy-to-copy-and-paste ID/blob combo.
      def otherExportSelectedIDAction():
         self.otherExportSelectedID()
         
      # Delete the ID.
      def otherDeleteSelectedIDAction():
         self.otherDeleteSelectedID()

      # Issue a pop-up with the given wallet's ID, and let the user change it.
      def lsAction():
         #
         pass

      # Publish identity to Verisign for placement in DNSSEC.
      def lpAction():
         #
         pass

      # Show an easy-to-copy-and-paste ID/blob combo.
      def leAction():
         #
         pass

      # Generate a payment request.
      def lrAction():
         if self.wlt == None:
            QMessageBox.warning(self.main,
                                'No Local Wallet Selected',
                                'Please select a local wallet.',
                                QMessageBox.Ok)
         else:
            # Get the new address and multiplier.
            self.resAddr = None
            self.resPos = 0
            self.resMult = None
            keyRes, self.resAddr, self.resPos, self.resMult = \
                                                 self.getNewKeyAndMult(self.wlt)
            if not keyRes:
               LOGERROR('Attempt to generate a new key failed.')
               QMessageBox.warning(self.main,
                                   'Address generation failed',
                                   'New address generation attempt failed.',
                                   QMessageBox.Ok)
            elif self.resAddr == None:
               LOGERROR('Resultant address is empty. This should not happen.')
               QMessageBox.warning(self.main,
                                   'Address generated is empty',
                                   'New address generated is empty.',
                                   QMessageBox.Ok)
            else:
            # Generate the proper object.
               finalAddr = self.resAddr.getAddrStr()
               newPKRP = PublicKeyRelationshipProof(self.resMult)
               newPTV = PaymentTargetVerifier(newPKRP)
               newPTVStr = binary_to_base58(newPTV.serialize())

               # Put everything together and present it to the user.
               # Right now, this dialog doesn't work. Dialog says the address is
               # invalid and refuses to generate a QR code. We also need to pass
               # in the Base58-encoded PTV somehow.
#               dlg = DlgRequestPayment(self.main, self.main, finalAddr)
#               dlg.exec_()

      self.main.connect(self.btnOtherLookup, SIGNAL('clicked()'),
            otherWalletIdentityLookupAction)
      self.main.connect(self.btnOtherManual, SIGNAL('clicked()'),
            enterWalletIdentityAction)
      self.main.connect(self.btnOtherVerify, SIGNAL('clicked()'), ovAction)
      self.main.connect(self.btnOtherExport, SIGNAL('clicked()'),
            otherExportSelectedIDAction)
      self.main.connect(self.btnOtherDelete, SIGNAL('clicked()'),
            otherDeleteSelectedIDAction)

      self.main.connect(self.btnLocalSetHandle, SIGNAL('clicked()'), lsAction)
      self.main.connect(self.btnLocalPublish,   SIGNAL('clicked()'), lpAction)
      self.main.connect(self.btnLocalExport,    SIGNAL('clicked()'), leAction)
      self.main.connect(self.btnLocalRequest,   SIGNAL('clicked()'), lrAction)

      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(frameAll)

      # Register the BDM callback for when the BDM sends signals.
      getBDM().registerCppNotification(self.handleBDMNotification)
   
   #############################################################################
   def otherWalletIdentityLookup(self):
      dlg = LookupIdentityDialog(self.main, self.main)
      if dlg.exec_():
         # TODO add look up functionality - For now display a warning that
         # it was not found
         QMessageBox.warning(self.main, 'Wallet Handle Not Found',
           'This Wallet Handle: %s could not be found in the Wallet ID Store.' \
           % dlg.getWalletHandle(),
           QMessageBox.Ok)
   
   #############################################################################
   def enterWalletIdentity(self):
      dlg = EnterWalletIdentityDialog(self.main, self.main)
      if dlg.exec_():
         self.modelOtherIDs.addIdentity(dlg.getWalletHandle(), dlg.getWalletPKS())

   #############################################################################
   def otherExportSelectedID(self):
      row = self.tableOtherIDs.selectedIndexes()[0].row()
      
      dlg = ExportWalletIdentityDialog(self.main, self.main,
            self.modelOtherIDs.getRowToExport(row))
      if dlg.exec_():
         pass
         
   #############################################################################
   def otherDeleteSelectedID(self):
      row = self.tableOtherIDs.selectedIndexes()[0].row()
      self.modelOtherIDs.removeRecord(row)
      self.btnOtherExport.setEnabled(False)
      self.btnOtherDelete.setEnabled(False)
      
         
   #############################################################################
   def otherIDclicked(self, currIndex, prevIndex=None):
      if prevIndex == currIndex and not currIndex is None:
         return

      if currIndex is None:
         isValid = False
      else:
         qmi = currIndex.model().index(currIndex.row(), OTHER_ID_COLS.DnsHandle)
         self.selectedOtherHandle = str(qmi.data().toString())
         isValid = len(self.selectedOtherHandle) > 0

      self.btnOtherExport.setEnabled(isValid)
      self.btnOtherDelete.setEnabled(isValid)

   #############################################################################
   def localIDclicked(self, currIndex, prevIndex=None):
      if prevIndex == currIndex and not currIndex is None:
         return

      if currIndex is None:
         isValid = False
      else:
         qmi = currIndex.model().index(currIndex.row(), LOCAL_ID_COLS.WalletID)
         self.selectedLocalWalletID = str(qmi.data().toString())
         self.wlt = self.main.walletMap[self.selectedLocalWalletID]
         isValid = len(self.selectedLocalWalletID) > 0

      self.btnLocalSetHandle.setEnabled(isValid)
      self.btnLocalPublish.setEnabled(isValid)
      self.btnLocalExport.setEnabled(isValid)
      self.btnLocalRequest.setEnabled(isValid)


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

      myPKS = PublicKeySource(isStatic, useCompr, use160, isUser, isExt,
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
         try:
            with open(filePath, 'wb') as newWltFile:
               myPKS = PublicKeySource(isStatic, useCompr, use160, isUser,
                                       isExt, sbdPubKey65.toBinStr(),
                                       chksumPres)
               myPMTA = PMTARecord(myPKS.serialize(), payNet)
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
         pksRec = decodePublicKeySource(daneRec)

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


   # Function that takes a BIP 32 wallet, generates a new child key, and returns
   # various values.
   # INPUT:  Wallet from which a 2nd-level pub key is derived. (ABEK_StdWallet)
   # OUTPUT: None
   # RETURN: Boolean indicating whether or not the key was correctly derived.
   #         The resultant address object. (ArmoryBip32ExtendedKey)
   #         The 2nd level position of the public key. (int)
   #         The multiplier (32 bytes minimum) that can get the root public key
   #         to the derived key. (Binary string)
   def getNewKeyAndMult(self, inWlt):
      retVal  = False
      outAddr = None
      outPos  = 0
      outMult = None

      if inWlt == None:
         LOGWARN('ERROR: No wallet selected. getNewKeyAndMult() will exit.')
      else:
         # Generate the new child address and get its position in the tree, then
         # re-derive the child address and get a multiplier. For now, the code
         # assumes the 1st level is 0 (i.e., these are non-change addresses).
         nextChildNum = inWlt.external.lowestUnusedChild
         newAddr = inWlt.getNextReceivingAddress()
         finalPub1, multProof1 = DeriveBip32PublicKeyWithProof(
                                                inWlt.sbdPublicKey33.toBinStr(),
                                                  inWlt.sbdChaincode.toBinStr(),
                                                              [0, nextChildNum])

         # Ensure an apples-to-apples comparison before proceeding. Compress b/c
         # it's less mathematically intensive than decompressing, and hex string
         # comparison because Python doesn't like to compare SBD objs directly.
         comp1 = CryptoECDSA().CompressPoint(newAddr.sbdPublicKey33)
         comp2 = CryptoECDSA().CompressPoint(SecureBinaryData(finalPub1))
         if comp1.toHexStr() != comp2.toHexStr():
            LOGWARN('ERROR: For some reason, the new key (%s) at position %s ' \
                    'does not match the derived key (%s) with multiplier %s. ' \
                    'No key will be returned.' % (newAddr.sbdPublicKey33,
                                                  nextChildNum,
                                                  finalPub1,
                                                  multProof1.multiplier))
         else:
            retVal  = True
            outAddr = newAddr
            outPos  = nextChildNum
            outMult = multProof1.multiplier

      return retVal, outAddr, outPos, outMult


   # Function is required by the plugin framework.
   def getTabToDisplay(self):
      return self.tabToDisplay

################################################################################
class ExportWalletIdentityDialog(ArmoryDialog):
   def __init__(self, parent, main, walletHandleID):
      super(ExportWalletIdentityDialog, self).__init__(parent, main)

      walletHandleIDLabel = QLabel("Wallet Handle and Identity:")
      self.walletHandleIDLineEdit = QLineEdit(walletHandleID)

      self.walletHandleIDLineEdit.setMinimumWidth(500)
      self.walletHandleIDLineEdit.setReadOnly(True)
      walletHandleIDLabel.setBuddy(self.walletHandleIDLineEdit)

      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
      self.connect(buttonBox, SIGNAL('accepted()'), self.accept)

      def saveWalletIDFileAction():
         self.saveWalletIDFile()

      def copyWalletIDToClipboardAction():
         self.copyWalletIDToClipboard()

      btnSave = QPushButton('Save as file...')
      self.connect(btnSave, SIGNAL(CLICKED), saveWalletIDFileAction)
      btnCopy = QPushButton('Copy to clipboard')
      self.connect(btnCopy, SIGNAL(CLICKED), copyWalletIDToClipboardAction)
      self.lblCopied = QRichLabel('  ')
      self.lblCopied.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
      copyButtonBox = makeHorizFrame([btnCopy, btnSave, self.lblCopied, STRETCH],
            condenseMargins=True)

      layout = QGridLayout()
      layout.addWidget(walletHandleIDLabel, 1, 0, 1, 1)
      layout.addWidget(self.walletHandleIDLineEdit, 1, 1, 1, 1)
      layout.addWidget(copyButtonBox, 2, 0, 1, 2)
      layout.addWidget(buttonBox, 5, 0, 1, 2)
      self.setLayout(layout)

      self.setWindowTitle('Wallet Handle and Identity')

   def copyWalletIDToClipboard(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(self.walletHandleIDLineEdit.text()))
      self.lblCopied.setText('<i>Copied!</i>')

   def saveWalletIDFile(self):
      # Use the first 6 characters of the PKS
      handleIDStr = str(self.walletHandleIDLineEdit.text())
      idSegment = handleIDStr[handleIDStr.rfind(' '):]
      if len(idSegment) > 6:
         idSegment = idSegment[:6]
      toSave = self.main.getFileSave(\
                      'Save Wallet ID in a File', \
                      ['Armory Transactions (*.pks)'], \
                      'WalletID_%s.pks' % idSegment)
      LOGINFO('Saving unsigned tx file: %s', toSave)
      try:
         theFile = open(toSave, 'w')
         theFile.write(str(self.walletHandleIDLineEdit.text()))
         theFile.close()
      except IOError:
         LOGEXCEPT('Failed to save file: %s', toSave)
         pass


################################################################################
class LookupIdentityDialog(ArmoryDialog):
   def __init__(self, parent, main):
      super(LookupIdentityDialog, self).__init__(parent, main)

      walletHandleLabel = QLabel("Wallet Handle to lookup:")
      self.walletHandleLineEdit = QLineEdit()
      self.walletHandleLineEdit.setMinimumWidth(300)
      walletHandleLabel.setBuddy(self.walletHandleLineEdit)

      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonBox, SIGNAL('accepted()'), self.accept)
      self.connect(buttonBox, SIGNAL('rejected()'), self.reject)

      layout = QGridLayout()
      layout.addWidget(walletHandleLabel, 1, 0, 1, 1)
      layout.addWidget(self.walletHandleLineEdit, 1, 1, 1, 1)
      layout.addWidget(buttonBox, 4, 0, 1, 2)
      self.setLayout(layout)

      self.setWindowTitle('Look up Wallet Identity')
      
   def getWalletHandle(self):
      return self.walletHandleLineEdit.text()

################################################################################
class EnterWalletIdentityDialog(ArmoryDialog):
   def __init__(self, parent, main):
      super(EnterWalletIdentityDialog, self).__init__(parent, main)

      walletHandleLabel = QLabel("Wallet Handle:")
      self.walletHandleLineEdit = QLineEdit()
      self.walletHandleLineEdit.setMinimumWidth(300)
      walletHandleLabel.setBuddy(self.walletHandleLineEdit)

      pksLabel = QLabel("Wallet Identity:")
      self.pksLineEdit = QLineEdit()
      self.pksLineEdit.setMinimumWidth(300)
      pksLabel.setBuddy(self.pksLineEdit)


      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonBox, SIGNAL('accepted()'), self.accept)
      self.connect(buttonBox, SIGNAL('rejected()'), self.reject)

      layout = QGridLayout()
      layout.addWidget(walletHandleLabel, 1, 0, 1, 1)
      layout.addWidget(self.walletHandleLineEdit, 1, 1, 1, 1)
      layout.addWidget(pksLabel, 2, 0, 1, 1)
      layout.addWidget(self.pksLineEdit, 2, 1, 1, 1)
      layout.addWidget(buttonBox, 5, 0, 1, 2)
      self.setLayout(layout)

      self.setWindowTitle('Enter Wallet Identity')
      
   def getWalletHandle(self):
      return self.walletHandleLineEdit.text()
   
   def getWalletPKS(self):
      return self.pksLineEdit.text()

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
      if dnsHandle in self.identityMap:
         LOGWARN('Handle is already in ID store. Updating instead of adding ')
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
   
   def getRowToExport(self, row):
      key = self.identityMap.keys()[row]
      return key + ' ' + self.identityMap[key]


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
