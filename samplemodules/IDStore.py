# This is a sample plugin file that will be used to create a new tab
# in the Armory main window.  All plugin files (such as this one) will
# be injected with the globals() from ArmoryQt.py, which includes pretty
# much all of Bitcoin & Armory related stuff that you need.  So this
# file can use any utils or objects accessible to functions in ArmoryQt.py.
from PyQt4.Qt import QPushButton, QScrollArea, SIGNAL, QLabel, QLineEdit, \
   QAbstractTableModel, QModelIndex, Qt
from armoryengine.ConstructedScript import PublicKeySource
from qtdefines import ArmoryDialog, enum
from qtdialogs import DlgWalletSelect
import re

IDSTORECOLS = enum('publicWalletID', 'pks')
WALLET_ID_STORE_FILENAME = 'Wallet_DNS_ID_Store.txt'

# Class name is required by the plugin framework.
class PluginObject(object):
   tabName = 'Wallet ID Store'
   maxVersion = '0.99'

   # NB: As a general rule of thumb, it's wise to not rely on access to anything
   # until the BDM is ready to go and/or Armory has finished loading itself. Any
   # code that must run before both conditions are satisfied (e.g., get info
   # from a wallet) may fail.
   def __init__(self, main):
      self.main = main
      self.wlt = None

      # Set up the GUI.
      headerLabel = QRichLabel(tr("<b>ID Store</b>"""), doWrap=False)

      def enterPKSAction():
         self.enterPKS()

      def selectPKSFromWalletAction():
         self.selectWallet()

      def addWalletIDRecordAction():
         self.addWalletIDRecord()

      def clearIDRecordAction():
         self.clearUserInputs()

      self.selectPKSButton = QPushButton("Create Wallet ID Proof")
      self.enterPKSButton = QPushButton("Enter Wallet ID Proof")
      self.addWalletIDRecordButton = QPushButton('Add Wallet ID Record')
      self.addWalletIDRecordButton.setEnabled(False)
      self.clearButton    = QPushButton('Clear')

      self.main.connect(self.selectPKSButton, SIGNAL(CLICKED), selectPKSFromWalletAction)
      self.main.connect(self.enterPKSButton, SIGNAL(CLICKED), enterPKSAction)
      self.main.connect(self.addWalletIDRecordButton, SIGNAL(CLICKED), addWalletIDRecordAction)
      self.main.connect(self.clearButton, SIGNAL(CLICKED), clearIDRecordAction)

      idLabel = QLabel('Public Wallet ID: ')
      self.walletDNSID = QLineEdit()
      self.walletDNSID.setFont(GETFONT('Fixed'))
      self.walletDNSID.setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 14)[0])
      self.walletDNSID.setAlignment(Qt.AlignLeft)
      idTip = self.main.createToolTipWidget('An ID, in email address form, ' \
                                            'that will be associated with ' \
                                            'this wallet in a DNS record.')

      self.pksB58Line = QLineEdit()
      self.pksB58Line.setFont(GETFONT('Fixed'))
      self.pksB58Line.setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 14)[0])
      self.pksB58Line.setAlignment(Qt.AlignLeft)
      self.pksB58Line.setReadOnly(True)
      pksB58Tip = self.main.createToolTipWidget('The wallet\'s ID record, ' \
                                                'Base58-encoded.')

      self.idStoreTableModel = IDStoreDisplayModel()
      self.idStoreTableView = QTableView()
      self.idStoreTableView.setModel(self.idStoreTableModel)
      self.idStoreTableView.setSelectionBehavior(QTableView.SelectRows)
      self.idStoreTableView.setSelectionMode(QTableView.SingleSelection)
      self.idStoreTableView.verticalHeader().setDefaultSectionSize(20)
      self.idStoreTableView.verticalHeader().hide()
      h = tightSizeNChar(self.idStoreTableView, 1)[1]
      self.idStoreTableView.setMinimumHeight(2 * (1.3 * h))
      self.idStoreTableView.setMaximumHeight(10 * (1.3 * h))      
      initialColResize(self.idStoreTableView, [.2, .2, .6])

      self.idStoreTableView.customContextMenuRequested.connect(self.showIDStoreContextMenu)
      self.idStoreTableView.setContextMenuPolicy(Qt.CustomContextMenu)

      # Create the frame and set the scrollarea widget to the layout.
      # self.tabToDisplay is required by the plugin framework.
      pluginFrame = makeVertFrame([headerLabel,
                                   makeHorizFrame([self.selectPKSButton,
                                                   self.enterPKSButton,
                                                   self.pksB58Line,
                                                   pksB58Tip,
                                                   'Stretch']),
                                   makeHorizFrame([idLabel,
                                                   self.walletDNSID,
                                                   idTip,
                                                   'Stretch']),
                                   makeHorizFrame([self.addWalletIDRecordButton,
                                                   self.clearButton,
                                                   'Stretch']),
                                   makeHorizFrame([self.idStoreTableView]),
                                   'Stretch'])
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(pluginFrame)


   def enterPKS(self):
      dlg = DlgEnterPKS(self.main, self.main)
      if dlg.exec_():
         # TODO Add PKS validator
         self.wlt = None
         # TODO verify that no Wallet matches the string that entered
         # before displaying unknown
         self.pksB58Line.setText(dlg.pksLineEdit.text())
         self.addWalletIDRecordButton.setEnabled(True)


   def selectWallet(self):
      dlg = DlgWalletSelect(self.main, self.main, 'Choose wallet...', '')
      if dlg.exec_():
         self.selectedWltID = dlg.selectedID
         self.wlt = self.main.walletMap[dlg.selectedID]
         wltPKS = binary_to_base58(self.getWltPKS(self.wlt).serialize())
         self.pksB58Line.setText(wltPKS)

         # If it exists, get the DNS wallet ID.
         wltPublicID = self.main.getWltSetting(self.wlt.uniqueIDB58, 'dnsID')
         self.walletDNSID.setText(wltPublicID)

         self.addWalletIDRecordButton.setEnabled(True)
      else:
         self.clearUserInputs()
         self.addWalletIDRecordButton.setEnabled(False)


   def clearUserInputs(self):
      self.wlt = None
      self.pksB58Line.setText('')
      self.walletDNSID.setText('')


   def showIDStoreContextMenu(self):
      menu = QMenu(self.idStoreTableView)
      if len(self.idStoreTableView.selectedIndexes())==0:
         return

      row = self.idStoreTableView.selectedIndexes()[0].row()
      deleteIDMenuItem = menu.addAction("Delete ID")
      action = menu.exec_(QCursor.pos())

      if action == deleteIDMenuItem:
         self.deleteID(row)


   def deleteID(self, idRow):
      self.idStoreTableModel.removeRecord(idRow)


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


   def addWalletIDRecord(self):
      wltPublicID = str(self.walletDNSID.displayText())
      wltIDProof = str(self.pksB58Line.displayText())

      # Check for empty fields
      if wltPublicID == '':
         QMessageBox.warning(self.main, 'Public Wallet ID is missing',
                             'Please enter the Public Wallet ID before adding the Wallet ID record.',
                             QMessageBox.Ok)

      elif wltIDProof == '':
         QMessageBox.warning(self.main, 'Wallet ID Proof is missing',
                             'Please provide the Wallet ID Proof before adding the Wallet ID record.',
                             QMessageBox.Ok)

      elif self.idStoreTableModel.hasRecord(wltPublicID, wltIDProof):
                  QMessageBox.warning(self.main, 'Wallet Record already Added',
                             'This Wallet Record has already been added to the Wallet ID Store.',
                             QMessageBox.Ok)

      # We'll allow a user to input a valid email address or enter no text at
      # all. To query DNS for a PMTA record, you must start with a string in
      # an external email address format, which is a tighter form of what's
      # allowed under RFC 822. We'll also let people enter blank text to
      # erase an address. This raises questions of how wallet IDs should be
      # handled in a production env. For now, the ID can change at will.
      elif (self.validateEmailAddress(wltPublicID) == False):
         QMessageBox.warning(self.main, 'Incorrect ID Formatting',
                             'ID not in the form of an email ' \
                             'address.',
                             QMessageBox.Ok)
      else:
         if self.wlt:
            self.main.setWltSetting(self.wlt.uniqueIDB58, 'dnsID', wltPublicID)
         self.idStoreTableModel.addRecord([wltPublicID, wltIDProof])
         self.clearUserInputs()


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
      if not re.match(r'(?:(?:\r\n)?[ \t])*(?:(?:(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*))*@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*|(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)*\<(?:(?:\r\n)?[ \t])*(?:@(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*(?:,@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*)*:(?:(?:\r\n)?[ \t])*)?(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*))*@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*\>(?:(?:\r\n)?[ \t])*)|(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)*:(?:(?:\r\n)?[ \t])*(?:(?:(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*))*@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*|(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)*\<(?:(?:\r\n)?[ \t])*(?:@(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*(?:,@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*)*:(?:(?:\r\n)?[ \t])*)?(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*))*@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*\>(?:(?:\r\n)?[ \t])*)(?:,\s*(?:(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*))*@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*|(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)*\<(?:(?:\r\n)?[ \t])*(?:@(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*(?:,@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*)*:(?:(?:\r\n)?[ \t])*)?(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|"(?:[^\"\r\\]|\\.|(?:(?:\r\n)?[ \t]))*"(?:(?:\r\n)?[ \t])*))*@(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*)(?:\.(?:(?:\r\n)?[ \t])*(?:[^()<>@,;:\\".\[\] \000-\031]+(?:(?:(?:\r\n)?[ \t])+|\Z|(?=[\["()<>@,;:\\".\[\]]))|\[([^\[\]\r\\]|\\.)*\](?:(?:\r\n)?[ \t])*))*\>(?:(?:\r\n)?[ \t])*))*)?;\s*)', inAddr):
         validAddr = False

      return validAddr


   # Function is required by the plugin framework.
   def getTabToDisplay(self):
      return self.tabToDisplay


################################################################################
class DlgEnterPKS(ArmoryDialog):
   def __init__(self, parent, main):
      super(DlgEnterPKS, self).__init__(parent, main)

      pksLabel = QLabel("Wallet ID Proof:")
      self.pksLineEdit = QLineEdit()
      self.pksLineEdit.setMinimumWidth(300)
      pksLabel.setBuddy(self.pksLineEdit)

      buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonBox, SIGNAL('accepted()'), self.accept)
      self.connect(buttonBox, SIGNAL('rejected()'), self.reject)

      layout = QGridLayout()
      layout.addWidget(pksLabel, 1, 0, 1, 1)
      layout.addWidget(self.pksLineEdit, 1, 1, 1, 1)
      layout.addWidget(buttonBox, 4, 0, 1, 2)
      self.setLayout(layout)

      self.setWindowTitle('Enter Wallet ID Proof')


################################################################################
class IDStoreDisplayModel(QAbstractTableModel):
   def __init__(self):
      super(IDStoreDisplayModel, self).__init__()
      self.idStoreList = []  # Has all the data. Pass in a 2D array.

      # Load the wallet ID store. Uses SettingsFile as a way to easily parse the
      # file.
      self.walletIDStorePath = os.path.join(getArmoryHomeDir(),
                                            WALLET_ID_STORE_FILENAME)
      self.settings = SettingsFile(self.walletIDStorePath)
      self.loadIDStore()


   ### Mandatory, Qt-specific calls. ###
   def rowCount(self, index=QModelIndex()):
      return len(self.idStoreList)


   def columnCount(self, index=QModelIndex()):
      return 2


   def data(self, index, role=Qt.DisplayRole):
      retVal = QVariant()

      row,col = index.row(), index.column()
      idStoreRecord = self.idStoreList[row]
      if role==Qt.DisplayRole:
         retVal = QVariant(idStoreRecord[col])
      elif role==Qt.TextAlignmentRole:
         retVal = QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
      elif role==Qt.ForegroundRole:
         retVal = QVariant(Colors.Foreground)

      return retVal


   def headerData(self, section, orientation, role=Qt.DisplayRole):
      retVal = QVariant()
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==IDSTORECOLS.publicWalletID:
               retVal = QVariant('Public Wallet ID')
            if section==IDSTORECOLS.pks:
               retVal = QVariant('Public Key Source')
      elif role==Qt.TextAlignmentRole:
         if orientation==Qt.Horizontal:
            retVal = QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         else:
            retVal = QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))

      return retVal


   ### Armory-specific calls. ###
   # A function that removes the data both from a particular row in a GUI and
   # the matching entry in the ID store file.
   # INPUT:  A row number matching the row in the GUI to remove. (int)
   # OUTPUT: None
   # RETURN: None
   def removeRecord(self, row):
      key = self.idStoreList[row][0]
      self.idStoreList.remove(self.idStoreList[row])
      self.reset() # Redraws the screen
      self.settings.delete(key)


   # A function that adds an entry to both the GUI and ID store file.
   # INPUT:  An array with two entries: The wallet ID and the matching
   #         Base58-encoded ID proof (PKS or CS record). ([str str])
   # OUTPUT: None
   # RETURN: None
   def addRecord(self, record):
      self.idStoreList.append(record)
      self.reset() # Redraws the screen
      self.settings.set(record[0], record[1])


   # A function that loads the ID store file entries into the class and the GUI.
   # INPUT:  None
   # OUTPUT: None
   # RETURN: None
   def loadIDStore(self):
      idDict = self.settings.getAllSettings()
      column = 0
      row = 0
      self.idStoreList = []

      # put each line in its own cell filling the table from left to right,
      # and top to bottom
      for key, value in idDict.iteritems():
         self.idStoreList.append([key, value])
         row += 1


   # A function checking to see if a wallet ID or ID proof is already present.
   # INPUT:  The wallet ID. (str)
   #         The Base58-encoded wallet ID proof. (str)
   # OUTPUT: None
   # RETURN: None
   def hasRecord(self, wltPublicID, wltIDProof):
      retVal = False
      for row in self.idStoreList:
         if wltPublicID in row or wltIDProof in row:
            retVal = True

      return retVal
