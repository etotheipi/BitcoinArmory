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
   QFrame, QVBoxLayout, QMessageBox, QVariant, QDialogButtonBox, QApplication, \
   QSizePolicy

from CppBlockUtils import SecureBinaryData, CryptoECDSA, HDWalletCrypto
from armorycolors import Colors
from armoryengine.ArmoryLog import LOGERROR, LOGWARN, LOGEXCEPT, LOGINFO
from armoryengine.ArmoryOptions import getTestnetFlag, getArmoryHomeDir, \
   isWindows, getAddrByte
from armoryengine.ArmorySettings import SettingsFile
from armoryengine.ArmoryUtils import binary_to_base58, sha224, binary_to_hex, \
   parseBitcoinURI, base58_to_binary, hash160_to_addrStr, hash160
from armoryengine.BDM import getBDM
from armoryengine.Constants import STRETCH, FINISH_LOAD_BLOCKCHAIN_ACTION, \
   BTCAID_PAYLOAD_TYPE, CLICKED
from armoryengine.ConstructedScript import PaymentRequest, PublicKeySource, \
   PAYNET_BTC, PAYNET_TBTC, PMTARecord, PublicKeyRelationshipProof, \
   PaymentTargetVerifier, DeriveBip32PublicKeyWithProof, decodePublicKeySource, \
   decodePaymentTargetVerifier, decodeReceiverIdentity, ScriptRelationshipProof, \
   ConstructedScript, ReceiverIdentity
from armoryengine.Exceptions import FileExistsError, InvalidDANESearchParam
from armoryengine.ValidateEmailRegEx import SuperLongEmailValidatorRegex
from qtdefines import tr, enum, initialColResize, QRichLabel, tightSizeNChar, \
   makeVertFrame, makeHorizFrame, HLINE, ArmoryDialog
from qtdialogs import DlgSendBitcoins, DlgWalletSelect, DlgRequestPayment
from ui.WalletFrames import SelectWalletFrame


WALLET_ID_STORE_FILENAME = 'Wallet_DNS_ID_Store.txt'
DNSSEC_URL = "https://en.wikipedia.org/wiki/Domain_Name_System_Security_Extensions"

OTHER_ID_COLS = enum('DnsHandle', 'AddrType' )
LOCAL_ID_COLS = enum('WalletID', 'WalletName', 'DnsHandle')


# Function that creates and returns a PublicKeySource (PMTA/DNS) record based
# on the incoming wallet.
#
# TODO: Place this function elsewhere.
#
# INPUT:  The wallet used to generate the PKS record (SettingsFile)
#         PKS-related flags (bool) - See armoryengine/ConstructedScript.py
# OUTPUT: None
# RETURN: Final PKS record (PKSRecord)
def getWltPKS(inWlt, isStatic = False, useCompr = True,
              use160 = True, isUser = False, isExt = False,
              chksumPres = False):
   # Start with the wallet's uncompressed root key.
   sbdPubKey33 = SecureBinaryData(inWlt.sbdPublicKey33)
   sbdPubKey65 = CryptoECDSA().UncompressPoint(sbdPubKey33)

   myPKS = PublicKeySource(isStatic, useCompr, use160, isUser, isExt,
                           sbdPubKey65.toBinStr(), False, chksumPres)
   return myPKS


# Function that takes an incoming key type and key ID, and uses them to get data
# from the wallet ID store file.
#
# INPUT:  The file handle of the wallet ID store file (ABEK_StdWallet)
#         Key type (str)
#         Key ID (str)
#         Default key ID (str - optional)
# OUTPUT: None
# RETURN: The key ID data string, which is empty by default (str)
def getWalletSetting(fileHandle, keyType, keyID, useDefaultValue=True,
                     defaultValue=''):
   retVal = ''

   # Sometimes we need to settings specific to individual wallets -- we will
   # prefix the settings name with the wltID.
   wltPropName = '%s..%s' % (keyType, keyID)
   if fileHandle.hasSetting(wltPropName):
      retVal = fileHandle.get(wltPropName)
   elif useDefaultValue:
      if not defaultValue=='':
         setWalletSetting(fileHandle, keyType, keyID, defaultValue)
      retVal = defaultValue

   return retVal


# Function that takes an incoming key type and key ID, and uses them to set data
# in the wallet ID store file.
#
# INPUT:  The file handle of the wallet ID store file (ABEK_StdWallet)
#         Key type (str)
#         Key ID (str)
#         Key value (str)
# OUTPUT: None
# RETURN: None
def setWalletSetting(fileHandle, keyType, keyID, value):
   wltPropName = '%s..%s' % (keyType, keyID)
   fileHandle.set(wltPropName, value)


# Function that takes an incoming key type and key ID, and uses them to delete
# data from the wallet ID store file.
#
# INPUT:  The file handle of the wallet ID store file (ABEK_StdWallet)
#         Key type (str)
#         Key ID (str)
#         Key value (str)
# OUTPUT: None
# RETURN: None
def delWalletSetting(fileHandle, keyType, keyID):
   wltPropName = '%s..%s' % (keyType, keyID)
   fileHandle.delete(wltPropName)


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

      w,h = tightSizeNChar(QTableView(), 90)
      viewWidth  = 1.2*w
      sectionSz  = 1.3*h

      # Tracks and displays identities imported manually or from DNSSEC records
      self.modelOtherIDs = OtherWalletIDModel(self.main)
      self.tableOtherIDs = QTableView()
      self.tableOtherIDs.setModel(self.modelOtherIDs)
      self.tableOtherIDs.setSelectionBehavior(QTableView.SelectRows)
      self.tableOtherIDs.setSelectionMode(QTableView.SingleSelection)
      self.tableOtherIDs.setMinimumWidth(viewWidth)
      self.tableOtherIDs.setMinimumHeight(6.5*sectionSz)
      self.tableOtherIDs.verticalHeader().setDefaultSectionSize(sectionSz)
      self.tableOtherIDs.verticalHeader().hide()
      initialColResize(self.tableOtherIDs, [0.34, 0.65])

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

      walletIDStorePath = os.path.join(getArmoryHomeDir(),
                                       WALLET_ID_STORE_FILENAME)

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
      def verifyPaymentRequestAction():
         self.verifyPaymentRequest()

      # Show an easy-to-copy-and-paste ID/blob combo.
      def localExportSelectedIDAction():
         self.localExportSelectedID()

      # Show an easy-to-copy-and-paste ID/blob combo.
      def otherExportSelectedIDAction():
         self.otherExportSelectedID()

      # Delete the ID.
      def otherDeleteSelectedIDAction():
         self.otherDeleteSelectedID()

      # Issue a pop-up with the given wallet's ID, and let the user change it.
      def setLocalWalletHandleAction():
         self.setLocalWalletHandle()

      # Publish identity to Verisign for placement in DNSSEC.
      def publishIdentityAction():
         QMessageBox.warning(self.main,
                                'Publish Identity',
                                'Functionality is TBD.',
                                QMessageBox.Ok)

      # Generate a payment request.
      def generatePaymentRequestAction():
         self.generatePaymentRequest()

      self.main.connect(self.btnOtherLookup, SIGNAL('clicked()'),
            otherWalletIdentityLookupAction)
      self.main.connect(self.btnOtherManual, SIGNAL('clicked()'),
            enterWalletIdentityAction)
      self.main.connect(self.btnOtherVerify, SIGNAL('clicked()'),
            verifyPaymentRequestAction)
      self.main.connect(self.btnOtherExport, SIGNAL('clicked()'),
            otherExportSelectedIDAction)
      self.main.connect(self.btnOtherDelete, SIGNAL('clicked()'),
            otherDeleteSelectedIDAction)

      self.main.connect(self.btnLocalSetHandle, SIGNAL('clicked()'),
            setLocalWalletHandleAction)
      self.main.connect(self.btnLocalPublish,   SIGNAL('clicked()'),
            publishIdentityAction)
      self.main.connect(self.btnLocalExport,    SIGNAL('clicked()'),
            localExportSelectedIDAction)
      self.main.connect(self.btnLocalRequest,   SIGNAL('clicked()'),
            generatePaymentRequestAction)

      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(frameAll)

      # Register the BDM callback for when the BDM sends signals.
      getBDM().registerCppNotification(self.handleBDMNotification)


   #############################################################################
   def generatePaymentRequest(self):
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
                                                      getNewKeyAndMult(self.wlt)
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
            payID = self.modelLocalIDs.getWltHandleForID(self.wlt.uniqueIDB58)
            newPKRP = PublicKeyRelationshipProof(self.resMult)
            newPTV = PaymentTargetVerifier(newPKRP)
            finalPMTAStr = payID + '..' + binary_to_base58(newPTV.serialize())

            # Put everything together and present it to the user.
            # Right now, this dialog doesn't work. Dialog says the address is
            # invalid and refuses to generate a QR code. We also need to pass
            # in the Base58-encoded PTV somehow.
            dlg = DlgRequestPayment(self.main, self.main, finalAddr,
                                    pmta = finalPMTAStr)
            dlg.exec_()


   #############################################################################
   # NOTE: This is a large, unwieldy function. It should probably be refactored
   # into multiple, smaller functions. One day....
   def verifyPaymentRequest(self):
      # First, verify that the data we're receiving is correctly formatted. The
      # data MUST be a Bitcoin URI with properly formatted data.
      dlg = VerifyPaymentRequestDialog(self.main, self.main)
      if dlg.exec_():
         # It's now safe to extract the data, which has been confirmed as valid.
         uriData = parseBitcoinURI(dlg.getPaymentRequest())
         pmtaData = uriData['pmta'].split('..')

         # TODO: Specify Multiplier
         multiplier = None
         finalKey   = None
         ptv = decodePaymentTargetVerifier(base58_to_binary(pmtaData[1]))

         if ptv.isValid() is False:
            QMessageBox.warning(self.main, 'Invalid Payment Request',
                                'Payment Request is invalid. Please confirm ' \
                                'that the text is complete and not corrupted.',
                                QMessageBox.Ok)
         else:
            # FIX: For now, the code assumes the PTV contains a PKRP record. SRP
            # support will come later.
            if isinstance(ptv.rec, ScriptRelationshipProof):
               pass # ERROR MSG
            else:
               # If we have a final key in the PKRP, the proof is optional. For
               # now, we'll verify the proof anyway.
               if ptv.rec.multUsed:
                  multiplier = ptv.rec.multiplier
               if ptv.rec.finalKeyUsed:
                  finalKey = ptv.rec.finalKey

               # Go through the following steps. All steps, unless otherwise
               # noted, are inside a loop based on the number of unvalidated
               # TxOut scripts listed in the record.
               #  1) Check DNS first.
               # 2a) If we get a DNS record, save the accompanying RI record.
               # 2b) If we don't get a DNS record, confirm that the ID is in the
               #     ID store, and get the accompanying RI record.
               #  3) If the ID is acceptable, apply the proof to get the final
               #     address.
               #  4) Confirm the derived address matches the provided address.
               #  5) If the addresses match, generate a "Send Bitcoins" dialog
               #     using the appropriate info.
               resultRIRecord = None
               resultType = ''
               dlgInfo = {}
               validRecords = True

               # DNS IS IGNORED FOR NOW FOR DEBUGGING PURPOSES. COME BACK LATER.
#               dnsResult = fetchPMTA(uriData['address'], resultRecord, resultType)
               dnsResult = False
               if not dnsResult:
                  # Verify that the received record matches the one in the ID
                  # store. If so, go ahead with the dialog.
                  riFound, resultRIRecord = getRIFromStore(pmtaData[0])
                  if not riFound:
                     validRecords = False

               if validRecords:
                  # TODO: Need to properly handle the final key & multiplier.
                  # The code currently plows ahead w/ the derivation.

                  # Verify that the URI address matches the derived address.
                  # NOTE: The code assumes a standard Bitcoin address. Support
                  # will need to be expanded eventually.
                  riObj = decodeReceiverIdentity(base58_to_binary(resultRIRecord))
                  rootAddr, rootKey = processReceiverIdentity(riObj, True)
                  finalDerivedKey = HDWalletCrypto().getChildKeyFromMult_SWIG(
                                                                        rootKey,
                                                                     multiplier)
                  finalDerivedAddr = hash160_to_addrStr(hash160(finalDerivedKey),
                                                        getAddrByte())

                  # Insert pop-up if derived address doesn't match the supplied
                  # address. Also, as a way to show this really works, insert a
                  # pop-up saying derivation worked. Wouldn't be done in a prod
                  # env but it's great for a demo!
                  if uriData['address'] != finalDerivedAddr:
                     QMessageBox.warning(self.main, 'Payment Request Invalid',
                                         'The payment request could not be ' \
                                         'verified. Please check the logs ' \
                                         'and contact the intended payment ' \
                                         'recipient.', QMessageBox.Ok)
                  else:
                     QMessageBox.information(self.main, 'Payment Request Valid',
                                         'The payment request was verified! ' \
                                         'You may now pay the recipient.',
                                         QMessageBox.Ok)

                     dlgInfo['address'] = uriData['address']
                     dlgInfo['amount'] = str(uriData['amount'])
                     dlgInfo['label'] = uriData['label']
                     DlgSendBitcoins(self.wlt, self.main, self.main, dlgInfo).exec_()

         self.modelLocalIDs.reset()


   #############################################################################
   def setLocalWalletHandle(self):
      row = self.tableLocalIDs.selectedIndexes()[0].row()
      wltID = self.modelLocalIDs.getWltIDForRow(row)
      dlg = SetWalletHandleDialog(self.main, self.main, wltID)
      if dlg.exec_():
         self.modelLocalIDs.setWltHandle(wltID, dlg.getWltHandle(), dlg.getWalletRIRecord())

   #############################################################################
   def otherWalletIdentityLookup(self):
      dlg = LookupIdentityDialog(self.main, self.main)
      if dlg.exec_():
         # TODO add look up functionality - For now display a warning that
         # it was not found
         QMessageBox.warning(self.main, 'Wallet Handle Not Found',
           'This Wallet Handle: %s could not be found in the Wallet ID Store.' \
           % dlg.getWltHandle(),
           QMessageBox.Ok)


   #############################################################################
   def enterWalletIdentity(self):
      dlg = EnterWalletIdentityDialog(self.main, self.main)
      if dlg.exec_():
         self.modelOtherIDs.addIdentity(dlg.getWltHandle(), dlg.getWalletRIRecord())


   #############################################################################
   # FIX: Settle on export format
   def otherExportSelectedID(self):
      row = self.tableOtherIDs.selectedIndexes()[0].row()

      dlg = ExportWalletIdentityDialog(self.main, self.main,
                                       self.modelOtherIDs.getRowToExport(row))
      if dlg.exec_():
         pass


   #############################################################################
   # FIX: Settle on export format
   def localExportSelectedID(self):
      row = self.tableLocalIDs.selectedIndexes()[0].row()

      dlg = ExportWalletIdentityDialog(self.main, self.main,
                                       self.modelLocalIDs.getRowToExport(row))
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
      if prevIndex == currIndex:
         return

      self.btnOtherExport.setEnabled(not currIndex is None)
      self.btnOtherDelete.setEnabled(not currIndex is None)


   #############################################################################
   def localIDclicked(self, currIndex, prevIndex=None):
      if prevIndex == currIndex and not currIndex is None:
         return

      canSetWalletHandle = False
      if currIndex is not None:
         selectedLocalWalletID = self.modelLocalIDs.getWltIDForRow(currIndex.row())
         self.wlt = self.main.walletMap[selectedLocalWalletID]
         canSetWalletHandle = True
         dnsHandle = self.modelLocalIDs.getWltHandleForRow(currIndex.row())
         hasWalletHandle = len(dnsHandle) > 0

      # hasWalletHandle is True only when canSetWalletHandle is True
      self.btnLocalSetHandle.setEnabled(canSetWalletHandle)
      self.btnLocalPublish.setEnabled(hasWalletHandle)
      self.btnLocalExport.setEnabled(hasWalletHandle)
      self.btnLocalRequest.setEnabled(hasWalletHandle)


   # Function called when the "bdmReadyPMTA" signal is emitted. Not used.
   # INPUT:  None
   # OUTPUT: None
   # RETURN: None
   def bdmReady(self):
      pass


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


   # Function is required by the plugin framework.
   def getTabToDisplay(self):
      return self.tabToDisplay


# Function that processes ReceiverIdentity information as necessary.
# INPUT:  A ReceiverIdentity record to process.
#         A boolean indicating if the call is part of a direct payment chain.
# OUTPUT: None
# RETURN: A derived Bitcoin address. (addrStr)
#         The root key, compressed or uncompressed based on flags. (binary str)
def processReceiverIdentity(inRIRecord, directPayment):
   returnAddr = ''
   returnKey = None

   # Get key from RI record and process the contents to get the root key
   #material.
   # FIX: For now, the code assumes the RI object contains PKS objects. CS
   # support will be added later.
   if isinstance(inRIRecord.rec, ConstructedScript):
      pass # ERROR MSG
   elif isinstance(inRIRecord.rec, PublicKeySource):
      if directPayment and not inRIRecord.rec.disableDirectPay:
         returnKey = inRIRecord.rec.rawSource
         if inRIRecord.rec.isExternalSrc:
            pass # Overrides all other flags. Not supported for now.
         elif inRIRecord.rec.isStatic:
            pass # Overrides all flags except isExternSec. Key material's final.
         elif inRIRecord.rec.isUserKey:
            pass # User supplies a key. Not supported for now.
         else:
            if inRIRecord.rec.useCompr:
               secReturnKey = SecureBinaryData(returnKey)
               secCompReturnKey = CryptoECDSA().CompressPoint(secReturnKey)
               returnKey = secCompReturnKey.toBinStr()

            if inRIRecord.rec.useHash160:
               returnAddr = hash160_to_addrStr(hash160(returnKey), getAddrByte())
   else:
      # This shouldn't happen. Just in case....
      LOGERROR('processReceiverIdentity got a bad ReceiverIdentity record.')

   return returnAddr, returnKey


# Function that checks whether of not the wallet ID store has a given ID.
# INPUT:  The ID the user wishes to find. (str)
# OUTPUT: None
# RETURN: Boolean indicating whether or not the ID was found.
#         The record found in the ID store, if it exists.
def getRIFromStore(inRec):
   recordFound = False

   walletIDStorePath = os.path.join(getArmoryHomeDir(),
                                    WALLET_ID_STORE_FILENAME)
   walletIDStore = SettingsFile(walletIDStorePath)

   returnRecord = getWalletSetting(walletIDStore, 'handle', inRec.split('..')[0],
                                   False)
   if returnRecord != '':
      recordFound = True

   return recordFound, returnRecord


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
def validateWalletHandle(inAddr):
   return True if re.match(SuperLongEmailValidatorRegex, inAddr) else False


#############################################################################
# TODO: Check validation logic
def validateWalletPaymentVerifier(walletPaymentVerifier):
   validRIObj = False

   # If the string we receive is a bad encode, just drop any raised errors.
   try:
      receiverIdentityObj = \
              decodeReceiverIdentity(base58_to_binary(walletPaymentVerifier))
      validRIObj = receiverIdentityObj.isValid()
   except:
      pass

   return validRIObj


#############################################################################
# TODO: Check validation logic
# INPUT:  Base58-serialized PaymentTargetVerifier object. (str)
#         The window that spawned the plugin. (ArmoryMainWindow)
# OUTPUT: None
# RETURN: Boolean indicating whether or not validation was successful.
def validatePaymentTargetVerifier(inPTV):
   validPTVObj = False

   try:
      ptv = decodePaymentTargetVerifier(base58_to_binary(inPTV))
      validPTVObj = ptv.isValid()
   except:
      pass

   return validPTVObj


# Utility function that takes a BIP 32 wallet, generates a new child key, and
# returns various values.
# INPUT:  Wallet from which a 2nd-level pub key is derived. (ABEK_StdWallet)
# OUTPUT: None
# RETURN: Boolean indicating whether or not the key was correctly derived.
#         The resultant address object. (ArmoryBip32ExtendedKey)
#         The 2nd level position of the public key. (int)
#         The multiplier (32 bytes minimum) that can get the root public key
#         to the derived key. (Binary string)
def getNewKeyAndMult(inWlt):
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
      # comparison b/c Python doesn't like to compare SBD objs directly.
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


################################################################################
class ExportWalletIdentityDialog(ArmoryDialog):
   def __init__(self, parent, main, walletHandleID):
      super(ExportWalletIdentityDialog, self).__init__(parent, main)

      walletHandleIDLabel = QLabel("Wallet Handle and Identity:")
      self.walletHandleIDLineEdit = QLineEdit(walletHandleID)

      self.walletHandleIDLineEdit.setMinimumWidth(500)
      self.walletHandleIDLineEdit.setReadOnly(True)
      walletHandleIDLabel.setBuddy(self.walletHandleIDLineEdit)
      self.walletHandleIDLineEdit.setCursorPosition(0)

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
      copyButtonBox = makeHorizFrame([btnCopy, btnSave, self.lblCopied,
            STRETCH], condenseMargins=True)

      layout = QGridLayout()
      layout.addWidget(walletHandleIDLabel, 1, 0, 1, 1)
      layout.addWidget(self.walletHandleIDLineEdit, 1, 1, 1, 1)
      layout.addWidget(copyButtonBox, 2, 0, 1, 2)
      layout.addWidget(buttonBox, 5, 0, 1, 2)
      self.setLayout(layout)

      self.setWindowTitle('Wallet Handle and Identity')


   #############################################################################
   def copyWalletIDToClipboard(self):
      clipb = QApplication.clipboard()
      clipb.clear()
      clipb.setText(str(self.walletHandleIDLineEdit.text()))
      self.lblCopied.setText('<i>Copied!</i>')


   #############################################################################
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
class VerifyPaymentRequestDialog(ArmoryDialog):
   def __init__(self, parent, main):
      super(VerifyPaymentRequestDialog, self).__init__(parent, main)

      self.main = main

      paymentRequestLabel = QLabel("Payment Request to Verify:")
      self.paymentRequestLineEdit = QLineEdit()
      self.paymentRequestLineEdit.setMinimumWidth(300)
      paymentRequestLabel.setBuddy(self.paymentRequestLineEdit)

      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      
      def validateAndAcceptAction():
         self.validateAndAccept()
         
      self.connect(buttonBox, SIGNAL('accepted()'), validateAndAcceptAction)
      self.connect(buttonBox, SIGNAL('rejected()'), self.reject)

      self.mainnetExample = 'bitcoin:18VEVEjWPKZABbpDPXBAQXdevpSk6nWY43?amount=1.43&label=Payment%20for%20Satoshi%27s%20miner%21&pmta=satoshin%40gmx.com..eteQcRSb1KJue4CBQiXzkbH4j3XZs9wG3mRXFt5qo8QQHtE9zvdV'
      self.testnetExample = 'bitcoin:mpNcRprh3SXNMMrJj92bGorrVjCz5t8c7B?amount=1.43&label=Payment%20for%20Satoshi%27s%20miner%21&pmta=satoshin%40gmx.com..eteQcRRmCp1z4AhW5cuhYupJ7xf6jbbsPj35uvWtSFhxHHFfNzRd'
      labelStr = 'Example:<BR>' + \
                 (self.testnetExample if getTestnetFlag() else self.mainnetExample)
      self.lblPayReqExample = QRichLabel(labelStr)
      frmFeatDescr = makeVertFrame([self.lblPayReqExample])
      self.lblPayReqExample.setMinimumHeight(tightSizeNChar(self, 10)[1] * 8)

      layout = QGridLayout()
      layout.addWidget(paymentRequestLabel, 1, 0, 1, 1)
      layout.addWidget(self.paymentRequestLineEdit, 1, 1, 1, 1)
      layout.addWidget(frmFeatDescr, 2, 0, 1, 2)
      layout.addWidget(buttonBox, 4, 0, 1, 2)
      self.setLayout(layout)

      self.setWindowTitle('Verify Payment Request')


   #############################################################################
   # NOTE: This function only validates the input formatting. The actual
   # validation of the underlying data must be done by any code calling this
   # dialog.
   def validateAndAccept(self):
      # Make sure we have a Bitcoin URI before proceeding.
      if not str.lower(self.getPaymentRequest()).startswith('bitcoin:'):
         msgStr = 'Payment Request is not a Bitcoin URI. Please enter a Bitcoin ' \
         'URI.\nExample: ' + \
         (self.testnetExample if getTestnetFlag() else self.mainnetExample)
         QMessageBox.warning(self.main, 'Invalid Payment Request',
                             'You have entered an invalid Payment Request. ' \
                             'Please check that you entered the data ' \
                             'correctly.', QMessageBox.Ok)
      else:
         uriData = parseBitcoinURI(self.getPaymentRequest())
         pmtaData = uriData['pmta'].split('..')

      # Payment Request must be key value mapping separated by '..'
         if len(pmtaData) != 2:
            # Assume the first entry is a Wallet Handle
            QMessageBox.warning(self.main, 'Invalid Payment Request',
                                'You have entered an incorrect Payment ' \
                                'Request. Please check that you entered the ' \
                                'request correctly.', QMessageBox.Ok)

         elif not validateWalletHandle(pmtaData[0]):
            QMessageBox.warning(self.main, 'Invalid Payment Request Handle',
                                'You have entered a broken Payment Request ' \
                                'handle. Please check that you entered the ' \
                                'handle correctly.', QMessageBox.Ok)
         elif not validatePaymentTargetVerifier(pmtaData[1]):
            QMessageBox.warning(self.main, 'Invalid Payment Request Data',
                                'You have entered invalid Payment Request ' \
                                'data. Please check that you entered the ' \
                                'data correctly.', QMessageBox.Ok)
         else:
            self.accept()


   #############################################################################
   def getPaymentRequest(self):
      return str(self.paymentRequestLineEdit.text())


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
      
      def validateAndAcceptAction():
         self.validateAndAccept()
         
      self.connect(buttonBox, SIGNAL('accepted()'), validateAndAcceptAction)
      self.connect(buttonBox, SIGNAL('rejected()'), self.reject)

      layout = QGridLayout()
      layout.addWidget(walletHandleLabel, 1, 0, 1, 1)
      layout.addWidget(self.walletHandleLineEdit, 1, 1, 1, 1)
      layout.addWidget(buttonBox, 4, 0, 1, 2)
      self.setLayout(layout)

      self.setWindowTitle('Look up Wallet Identity')


   #############################################################################
   def validateAndAccept(self):
      if not validateWalletHandle(self.getWltHandle()):
         QMessageBox.warning(self.main, 'Invalid Wallet Handle',
                             'You have entered an Invalid Wallet Handle ' \
                             'To continue enter a Wallet Handle that is in ' \
                             'the same format as an email address.',
                             QMessageBox.Ok)
      else:
         self.accept()


   #############################################################################
   def getWltHandle(self):
      return str(self.walletHandleLineEdit.text())


################################################################################
class SetWalletHandleDialog(ArmoryDialog):
   def __init__(self, parent, main, wltID):
      super(SetWalletHandleDialog, self).__init__(parent, main)
      wlt = main.walletMap[wltID]

      walletIDStorePath = os.path.join(getArmoryHomeDir(),
                                       WALLET_ID_STORE_FILENAME)
      walletIDStore = SettingsFile(walletIDStorePath)

      wltIDLabel = QRichLabel("Wallet ID:", doWrap=False)
      wltIDDisplayLabel = QRichLabel(wltID)
      wltIDDisplayLabel.setSizePolicy(QSizePolicy.Preferred,
            QSizePolicy.Preferred)

      wltNameLabel = QRichLabel("Name:", doWrap=False)
      wltNameDisplayLabel = QRichLabel(wlt.getLabel())
      wltNameDisplayLabel.setSizePolicy(QSizePolicy.Preferred,
            QSizePolicy.Preferred)

      pksLabel = QLabel("Wallet Payment Verifier:")
      riObj = ReceiverIdentity(getWltPKS(wlt))
      riStr = binary_to_base58(riObj.serialize())
      self.riLineEdit = QLineEdit(riStr)
      self.riLineEdit.setMinimumWidth(300)
      self.riLineEdit.setCursorPosition(0)
      self.riLineEdit.setReadOnly(True)
      pksLabel.setBuddy(self.riLineEdit)

      walletHandleLabel = QLabel("Wallet Handle:")
      wltHandle = getWalletSetting(walletIDStore, 'wallet', wltID)
      self.walletHandleLineEdit = QLineEdit(wltHandle)
      self.walletHandleLineEdit.setMinimumWidth(300)
      self.riLineEdit.setCursorPosition(0)
      walletHandleLabel.setBuddy(self.walletHandleLineEdit)

      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      
      def validateAndAcceptAction():
         self.validateAndAccept()
         
      self.connect(buttonBox, SIGNAL('accepted()'), validateAndAcceptAction)
      self.connect(buttonBox, SIGNAL('rejected()'), self.reject)

      layout = QGridLayout()
      layout.addWidget(wltIDLabel, 1, 0, 1, 1)
      layout.addWidget(wltIDDisplayLabel, 1, 1, 1, 1)
      layout.addWidget(wltNameLabel, 2, 0, 1, 1)
      layout.addWidget(wltNameDisplayLabel, 2, 1, 1, 1)
      layout.addWidget(pksLabel, 3, 0, 1, 1)
      layout.addWidget(self.riLineEdit, 3, 1, 1, 1)
      layout.addWidget(walletHandleLabel, 4, 0, 1, 1)
      layout.addWidget(self.walletHandleLineEdit, 4, 1, 1, 1)
      layout.addWidget(buttonBox, 6, 0, 1, 2)
      self.setLayout(layout)

      self.setWindowTitle('Enter Wallet Handle')


   #############################################################################
   def validateAndAccept(self):
      if not validateWalletHandle(self.getWltHandle()):
         QMessageBox.warning(self.main, 'Invalid Wallet Handle',
                             'You have entered an Invalid Wallet Handle ' \
                             'To continue enter a Wallet Handle that is in ' \
                             'the same format as an email address.',
                             QMessageBox.Ok)
      else:
         self.accept()


   #############################################################################
   def getWltHandle(self):
      return str(self.walletHandleLineEdit.text())


   #############################################################################
   # RI = Receiver Identity
   def getWalletRIRecord(self):
      return str(self.riLineEdit.text())


################################################################################
class EnterWalletIdentityDialog(ArmoryDialog):
   def __init__(self, parent, main):
      super(EnterWalletIdentityDialog, self).__init__(parent, main)

      walletHandleLabel = QLabel("Wallet Handle:")
      self.walletHandleLineEdit = QLineEdit()
      self.walletHandleLineEdit.setMinimumWidth(300)
      walletHandleLabel.setBuddy(self.walletHandleLineEdit)

      pksLabel = QLabel("Wallet Payment Verifier:")
      self.riLineEdit = QLineEdit()
      self.riLineEdit.setMinimumWidth(300)
      pksLabel.setBuddy(self.riLineEdit)

      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      
      def validateAndAcceptAction():
         self.validateAndAccept()
      
      self.connect(buttonBox, SIGNAL('accepted()'), validateAndAcceptAction)
      self.connect(buttonBox, SIGNAL('rejected()'), self.reject)

      layout = QGridLayout()
      layout.addWidget(walletHandleLabel, 1, 0, 1, 1)
      layout.addWidget(self.walletHandleLineEdit, 1, 1, 1, 1)
      layout.addWidget(pksLabel, 2, 0, 1, 1)
      layout.addWidget(self.riLineEdit, 2, 1, 1, 1)
      layout.addWidget(buttonBox, 5, 0, 1, 2)
      self.setLayout(layout)

      self.setWindowTitle('Enter Wallet Payment Verifier')


   #############################################################################
   def validateAndAccept(self):
      if not validateWalletHandle(self.getWltHandle()):
         QMessageBox.warning(self.main, 'Invalid Wallet Handle',
                             'You have entered an invalid Wallet Handle. To ' \
                             'continue, enter a Wallet Handle that is in ' \
                             'the same format as an email address.',
                             QMessageBox.Ok)
      elif not validateWalletPaymentVerifier(self.getWalletRIRecord()):
         # TODO: Fill in this text that describes what is valid',
         QMessageBox.warning(self.main, 'Invalid Wallet Payment Verifier',
                             'You have entered an invalid Wallet Payment ' \
                             'Verifier. Please verify that the data was ' \
                             'properly entered.', QMessageBox.Ok)
      else:
         self.accept()


   #############################################################################
   def getWltHandle(self):
      return str(self.walletHandleLineEdit.text())


   #############################################################################
   # RI = Receiver Identity
   def getWalletRIRecord(self):
      return str(self.riLineEdit.text())


################################################################################
class OtherWalletIDModel(QAbstractTableModel):

   #############################################################################
   def __init__(self, main):
      super(OtherWalletIDModel, self).__init__()
      self.main = main
      self.identityMap = OrderedDict()
      walletIDStorePath = os.path.join(getArmoryHomeDir(),
                                       WALLET_ID_STORE_FILENAME)
      self.walletIDStore = SettingsFile(walletIDStorePath)

      self.readIdentityFile()


   #############################################################################
   def rowCount(self, index=QModelIndex()):
      return len(self.identityMap)


   #############################################################################
   def columnCount(self, index=QModelIndex()):
      return 2
   
   #############################################################################
   def data(self, index, role=Qt.DisplayRole):
      retVal = QVariant()
      row,col = index.row(), index.column()

      keyList = self.identityMap.keys()

      if role==Qt.DisplayRole:
         if col==OTHER_ID_COLS.DnsHandle:
            retVal = QVariant(keyList[row])
         if col==OTHER_ID_COLS.AddrType:
            retVal = ''
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
            elif  section==OTHER_ID_COLS.AddrType:
               retVal = QVariant('Address Type')
      elif role==Qt.TextAlignmentRole:
         if orientation==Qt.Horizontal:
            retVal = QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         else:
            retVal = QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))

      return retVal


   #############################################################################
   def readIdentityFile(self):
      if not self.walletIDStore:
         self.identityMap = OrderedDict()
         return

      # Get a list of all the wallet handles.
      walletHandleDict = {}
      for key, value in self.walletIDStore.settingsMap.iteritems():
         if key.find('handle..') != -1:
            walletHandleDict[key.split('..')[1]] = value

      # Get the handles used by wallets by looping through the wallet handle
      # list again. Probably not the most efficient route but it works.
      for key, value in self.walletIDStore.settingsMap.iteritems():
         if key.find('wallet..') != -1:
            if value in walletHandleDict:
               del walletHandleDict[value]

      # Write the "other" handle list and use it to set up the ID map.
      otherHandleList = []
      for key, value in walletHandleDict.iteritems():
         otherHandleList.append([key, value])
      self.identityMap = OrderedDict(otherHandleList)


   #############################################################################
   # A function that removes the data both from a particular row in a GUI and
   # the matching entry in the ID store file.
   # INPUT:  A row number matching the row in the GUI to remove. (int)
   # OUTPUT: None
   # RETURN: None
   def removeRecord(self, row):
      key = self.identityMap.keys()[row]
      del self.identityMap[key]
      delWalletSetting(self.walletIDStore, 'handle', key)
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
      setWalletSetting(self.walletIDStore, 'handle', dnsHandle, base58Identity)
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


   #############################################################################
   def getRowToExport(self, row):
      key = self.identityMap.keys()[row]
      return key + '..' + self.identityMap[key]


################################################################################
class LocalWalletIDModel(QAbstractTableModel):

   #############################################################################
   def __init__(self, main):
      super(LocalWalletIDModel, self).__init__()
      self.main = main
      walletIDStorePath = os.path.join(getArmoryHomeDir(),
                                       WALLET_ID_STORE_FILENAME)
      self.walletIDStore = SettingsFile(walletIDStorePath)

   set 

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
            dnsID = getWalletSetting(self.walletIDStore, 'wallet', wltID)
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


   #############################################################################
   # FIX: Need to put in a better way to supply data. The current setup is for debugging purposes.
   def getRowToExport(self, row):
      retStr = ''

      wltID = self.main.wltIDList[row]
      dnsID = getWalletSetting(self.walletIDStore, 'wallet', wltID)
      if dnsID:
         wlt = self.main.walletMap[wltID]
         riObj = ReceiverIdentity(getWltPKS(wlt))
         riStr = binary_to_base58(riObj.serialize())
         retStr = dnsID + '..' + riStr

      return retStr

   #############################################################################
   def setWltHandle(self, wltID, wltHandle, riRecord):

         setWalletSetting(self.walletIDStore, 'wallet', wltID,
                          wltHandle)
         setWalletSetting(self.walletIDStore, 'handle', wltHandle,
                          riRecord)
         self.reset()

   #############################################################################
   def getWltIDForRow(self, row):
      return self.main.wltIDList[row]

   #############################################################################
   def getWltHandleForRow(self, row):
      wltID = self.main.wltIDList[row]
      return getWalletSetting(self.walletIDStore, 'wallet', wltID)
  #############################################################################   
   def getWltHandleForID(self, wltID):
      getWalletSetting(self.walletIDStore, 'wallet',
                                     wltID, False)
