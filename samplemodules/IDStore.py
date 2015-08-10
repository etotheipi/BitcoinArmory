# This is a sample plugin file that will be used to create a new tab
# in the Armory main window.  All plugin files (such as this one) will
# be injected with the globals() from ArmoryQt.py, which includes pretty
# much all of Bitcoin & Armory related stuff that you need.  So this
# file can use any utils or objects accessible to functions in ArmoryQt.py.
from PyQt4.Qt import *
import re

from armoryengine.BDM import getBDM
from armoryengine.ConstructedScript import PaymentRequest, PublicKeySource, \
   PAYNET_BTC, PAYNET_TBTC, PMTARecord
from qtdefines import *
from qtdialogs import DlgSendBitcoins, DlgWalletSelect
from ui.WalletFrames import SelectWalletFrame


# Class name is required by the plugin framework.
class PluginObject(object):
   tabName = 'ID Store'
   maxVersion = '0.99'

   # NB: As a general rule of thumb, it's wise to not rely on access to anything
   # until the BDM is ready to go and/or Armory has finished loading itself. Any
   # code that must run before both conditions are satisfied (e.g., get info
   # from a wallet) may fail.
   def __init__(self, main):
      self.main = main
      self.wlt = None

      # Set up the GUI.
      headerLabel    = QRichLabel(tr("<b>ID Store</b>"""),
                                  doWrap=False)

      def enterPKSAction():
         self.enterPKS()
         
      def selectPKSFromWalletAction():
         self.selectWallet()
         
      def addWalletIDRecordAction():
         self.addWalletIDRecord()

      def clearIDRecordAction():
         self.clearIDRecord()

      self.selectPKSButton = QPushButton("Select PKS from Wallet List")
      self.enterPKSButton = QPushButton("Enter PKS")
      self.addWalletIDRecordButton = QPushButton('Add Wallet ID Record')
      self.clearButton    = QPushButton('Clear')

      self.main.connect(self.selectPKSButton, SIGNAL(CLICKED), selectPKSFromWalletAction)
      self.main.connect(self.enterPKSButton, SIGNAL(CLICKED), enterPKSAction)
      self.main.connect(self.addWalletIDRecordButton, SIGNAL(CLICKED), addWalletIDRecordAction)
      self.main.connect(self.clearButton, SIGNAL(CLICKED), clearIDRecordAction)

      idLabel = QLabel('Public Wallet ID: ')
      self.inID = QLineEdit()
      self.inID.setFont(GETFONT('Fixed'))
      self.inID.setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 14)[0])
      self.inID.setAlignment(Qt.AlignLeft)
      idTip = self.main.createToolTipWidget('An ID, in email address form, ' \
                                            'that will be associated with ' \
                                            'this wallet in a DNS record.')
      
      
      self.selectedWltDisplay = QLabel('')
      self.pksB58Line = QLineEdit()
      self.pksB58Line.setFont(GETFONT('Fixed'))
      self.pksB58Line.setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 14)[0])
      self.pksB58Line.setAlignment(Qt.AlignLeft)
      self.pksB58Line.setReadOnly(True)
      pksB58Tip = self.main.createToolTipWidget('The wallet\'s PKS record, ' \
                                                'Base58-encoded.')

      walletLabel = QLabel('Wallet Name: ')
      
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
                                   makeHorizFrame([walletLabel,
                                                   self.selectedWltDisplay, 
                                                   'Stretch']),
                                   makeHorizFrame([idLabel,
                                                   self.inID,
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
         self.selectedWltDisplay = "Unknown"
   
      
   def selectWallet(self):
      dlg = DlgWalletSelect(self.main, self.main, 'Choose wallet...', '')
      if dlg.exec_():
         self.selectedWltID = dlg.selectedID
         self.wlt = self.main.walletMap[dlg.selectedID]
         self.selectedWltDisplay.setText(self.wlt.getLabel() + ' (' + \
                                         self.wlt.uniqueIDB58 + ')')
         wltPKS = binary_to_base58(self.getWltPKS(self.wlt).serialize())
         self.pksB58Line.setText(wltPKS)

         # If it exists, get the DNS wallet ID.
         wltDNSID = self.main.getWltSetting(self.wlt.uniqueIDB58, 'dnsID')
         self.inID.setText(wltDNSID)
      else:
         self.wlt = None
         self.selectedWltDisplay.setText('<No Wallet Selected')
         self.pksB58Line.setText('')

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
      self.idStoreTableModel.removeID(idRow)
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

   # Action for when the add DNS wallet ID button is pressed.
   def addWalletIDRecord(self):
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

      pksLabel = QLabel("PKS:")
      self.pksLineEdit = QLineEdit()
      self.pksLineEdit.setMaxLength(32)
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

      self.setWindowTitle('Enter PKS')

IDSTORECOLS = enum('publicWalletID', 'walletLabel', 'pks')
################################################################################
class IDStoreDisplayModel(QAbstractTableModel):
   def __init__(self):
      super(IDStoreDisplayModel, self).__init__()
      self.idStoreList = []
      
   def removeID(self, row):
      self.idStoreList.remove(self.idStoreList[row])
      self.reset()

   def updateIDStoreList(self, idStoreList):
      self.idStoreList = []
      self.idStoreList.extend(idStoreList)
      self.reset()

   def rowCount(self, index=QModelIndex()):
      return len(self.idStoreList)

   def columnCount(self, index=QModelIndex()):
      return 3

   def data(self, index, role=Qt.DisplayRole):
      row,col = index.row(), index.column()
      idStoreRecord = self.idStoreRecordList[row]
      if role==Qt.DisplayRole:
         return QVariant(idStoreRecord[col])
      elif role==Qt.TextAlignmentRole:
         return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
      elif role==Qt.ForegroundRole:
         return QVariant(Colors.Foreground)
      return QVariant()

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==IDSTORECOLS.publicWalletID: return QVariant('Public Wallet ID')
            if section==IDSTORECOLS.walletLabel: return QVariant('Wallet Name')
            if section==IDSTORECOLS.pks: return QVariant('Public Key Source')
      elif role==Qt.TextAlignmentRole:
         if orientation==Qt.Horizontal:
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         else:
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))

