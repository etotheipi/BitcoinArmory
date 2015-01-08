# This is a sample plugin file that will be used to create a new tab 
# in the Armory main window.  All plugin files (such as this one) will 
# be injected with the globals() from ArmoryQt.py, which includes pretty
# much all of Bitcoin & Armory related stuff that you need.  So this 
# file can use any utils or objects accessible to functions in ArmoryQt.py.
from socket import socket

from PyQt4.Qt import QMessageBox, QPushButton, SIGNAL, QLabel, QLineEdit, Qt, \
   QTableView, QScrollArea, QAbstractTableModel, QModelIndex, QVariant

from armorycolors import Colors
from armoryengine.ArmoryUtils import enum, str2coin, NegativeValueError, \
   TooMuchPrecisionError, LOGEXCEPT, coin2str, script_to_addrStr, \
   addrStr_to_hash160, SCRADDR_P2PKH_BYTE, CheckHash160, binary_to_hex
from armorymodels import WLTVIEWCOLS
from qtdefines import QRichLabel, makeHorizFrame, GETFONT, tightSizeNChar, \
   initialColResize, makeVertFrame, saveTableView
from armoryengine.Transaction import SIGHASH_NONE, SIGHASH_ANYONECANPAY,\
   PyCreateAndSignTx, PyTx, UnsignedTxInput
from qtdialogs import DlgUnlockWallet
from armoryengine.BDM import TheBDM


DUSTCOLS = enum('chainIndex', 'AddrStr', 'Btc', )
DEFAULT_DUST_LIMIT = 10000000
MAX_DUST_LIMIT_STR = '0.00100000'

class PluginObject(object):

   tabName = 'Dust-B-Gone'
   maxVersion = '0.93.99'
   
   #############################################################################
   def __init__(self, main):

      def updateDustLimit():
         try:
            self.dustTableModel.updateDustList(self.getSelectedWlt(),
                  str2coin(self.dustLimitText.text()))
            self.beGoneDustButton.setEnabled(len(self.dustTableModel.dustTxOutlist)>0)
            if self.dustTableModel.wlt:
               self.lblHeader.setText(tr("""<b>Dust Outputs for Wallet: %s</b>""" 
                     % self.dustTableModel.wlt.labelName))
         except NegativeValueError:
            pass
         except TooMuchPrecisionError:
            pass
         except:
            LOGEXCEPT("Unexpected exception")
            pass

      def sendDust():
         try:
            utxiList = []
            for utxo in self.dustTableModel.dustTxOutlist:
               # The PyCreateAndSignTx method require PyTx and PyBtcAddress objects
               rawTx = TheBDM.getTxByHash(utxo.getTxHash()).serialize()
               a160 = CheckHash160(utxo.getRecipientScrAddr())
               for pyAddr in self.dustTableModel.wlt.addrMap.values():
                  if a160 == pyAddr.getAddr160():
                     pubKey = pyAddr.binPublicKey65.toBinStr()
                     txoIdx = utxo.getTxOutIndex()
                     utxiList.append(UnsignedTxInput(rawTx, txoIdx, None, pubKey))
                     break
            # Make copies, destroy them in the finally clause
            privKeyMap = {}
            for addrObj in self.dustTableModel.wlt.addrMap.values():
               scrAddr = SCRADDR_P2PKH_BYTE + addrObj.getAddr160()
               if self.dustTableModel.wlt.useEncryption and self.dustTableModel.wlt.isLocked:
                  # Target wallet is encrypted...
                  unlockdlg = DlgUnlockWallet(self.dustTableModel.wlt,
                        self.main, self.main, 'Unlock Wallet to Import')
                  if not unlockdlg.exec_():
                     QMessageBox.critical(self, 'Wallet is Locked', \
                        'Cannot send dust without unlocking the wallet!', \
                        QMessageBox.Ok)
                     return
               privKeyMap[scrAddr] = addrObj.binPrivKey32_Plain.copy()
            signedTx = PyCreateAndSignTx(utxiList,
                  [],
                  privKeyMap, SIGHASH_NONE|SIGHASH_ANYONECANPAY )
            
            print "-------------"
            print binary_to_hex(signedTx.serialize())
            
            # sock = socket.create_connection(('dust-b-gone.bitcoin.petertodd.org',80))
            # sock.send(signedTx.serialize())
            # sock.send(b'\n')
            # sock.close()
                  

         except socket.error as err:
            QMessageBox.critical(self.main, tr('Negative Value'), tr("""
               Failed to connect to dust-b-gone server: %s""" % err.strerror), QMessageBox.Ok)            
         except NegativeValueError:
            QMessageBox.critical(self.main, tr('Negative Value'), tr("""
               You must enter a positive value of at least 0.0000 0001 
               and less than %s for the dust limit.""" % MAX_DUST_LIMIT_STR), QMessageBox.Ok)
         except TooMuchPrecisionError:
            QMessageBox.critical(self.main.main, tr('Too much precision'), tr("""
               Bitcoins can only be specified down to 8 decimal places. 
               The smallest unit of a Bitcoin is 0.0000 0001 BTC. 
               Please enter a dust limit of at least 0.0000 0001 and less than %s.""" % MAX_DUST_LIMIT_STR), QMessageBox.Ok)
         finally:
            for scraddr in privKeyMap:
               privKeyMap[scraddr].destroy()
         
         
         
          
      self.main = main
 
      self.lblHeader    = QRichLabel(tr("""<b>Dust Outputs for Wallet: None Selected</b>"""), doWrap=False)
      self.beGoneDustButton = QPushButton("Remove Dust")
      self.beGoneDustButton.setEnabled(False)
      self.main.connect(self.beGoneDustButton, SIGNAL('clicked()'), sendDust)
      topRow =  makeHorizFrame([self.lblHeader,'stretch'])
      secondRow =  makeHorizFrame([self.beGoneDustButton, 'stretch'])
      
      self.dustLimitLabel = QLabel("Max Dust Value (BTC): ")
      self.dustLimitText = QLineEdit()
      self.dustLimitText.setFont(GETFONT('Fixed'))
      self.dustLimitText.setMinimumWidth(tightSizeNChar(self.dustLimitText, 6)[0])
      self.dustLimitText.setMaximumWidth(tightSizeNChar(self.dustLimitText, 12)[0])
      self.dustLimitText.setAlignment(Qt.AlignRight)
      self.dustLimitText.setText(coin2str(DEFAULT_DUST_LIMIT))
      self.main.connect(self.dustLimitText, SIGNAL('textChanged(QString)'), updateDustLimit)
      
      
      limitPanel = makeHorizFrame([self.dustLimitLabel, self.dustLimitText, 'stretch'])
      
      
      self.dustTableModel = DustDisplayModel()
      self.dustTableView = QTableView()
      self.dustTableView.setModel(self.dustTableModel)
      self.dustTableView.setSelectionMode(QTableView.NoSelection)
      self.dustTableView.verticalHeader().setDefaultSectionSize(20)
      self.dustTableView.verticalHeader().hide()
      h = tightSizeNChar(self.dustTableView, 1)[1]
      self.dustTableView.setMinimumHeight(2 * (1.3 * h))
      self.dustTableView.setMaximumHeight(10 * (1.3 * h))
      initialColResize(self.dustTableView, [100, .7, .3])

      self.dustTableView.setContextMenuPolicy(Qt.CustomContextMenu)

      self.lblTxioInfo = QRichLabel('')
      self.lblTxioInfo.setMinimumWidth(tightSizeNChar(self.lblTxioInfo, 30)[0])
      
      self.main.connect(self.main.walletsView, SIGNAL('clicked(QModelIndex)'), 
                   updateDustLimit)

      self.dustBGoneFrame = makeVertFrame([topRow, secondRow, limitPanel, self.dustTableView, 'stretch'])

      # Now set the scrollarea widget to the layout
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(self.dustBGoneFrame)

   def getSelectedWlt(self):
      wlt = None
      selectedWltList = self.main.walletsView.selectedIndexes()
      if len(selectedWltList)>0:
            row = selectedWltList[0].row()
            wltID = str(self.main.walletsView.model().index(row, WLTVIEWCOLS.ID).data().toString())
            wlt = self.main.walletMap[wltID]
      return wlt


   #############################################################################
   def getTabToDisplay(self):
      return self.tabToDisplay
   
   def injectShutdownFunc(self):
      try:
         self.main.writeSetting('DustLedgerCols', saveTableView(self.dustTableView))
      except:
         LOGEXCEPT('Strange error during shutdown')
    


################################################################################
class DustDisplayModel(QAbstractTableModel):
   def __init__(self):
      super(DustDisplayModel, self).__init__()
      self.wlt = None
      self.dustTxOutlist = []

   def updateDustList(self, wlt, dustLimit):
      self.dustTxOutlist = []
      self.wlt = wlt
      txOutList = wlt.getFullUTXOList()
      for txout in txOutList:
         if txout.getValue() < dustLimit:
            self.dustTxOutlist.append(txout)
      self.reset()

   def rowCount(self, index=QModelIndex()):
      return len(self.dustTxOutlist)

   def columnCount(self, index=QModelIndex()):
      return 3

   def data(self, index, role=Qt.DisplayRole):
      row,col = index.row(), index.column()
      txout = self.dustTxOutlist[row]
      addrStr = script_to_addrStr(txout.getScript())
      pyAddr = self.wlt.addrMap[addrStr_to_hash160(addrStr)[1]]
      chainIndex = pyAddr.chainIndex + 1
      if role==Qt.DisplayRole:
         if col==DUSTCOLS.chainIndex: return QVariant(chainIndex)
         if col==DUSTCOLS.AddrStr: return QVariant(addrStr)
         if col==DUSTCOLS.Btc:     return QVariant(coin2str(txout.getValue(),maxZeros=8))
      elif role==Qt.TextAlignmentRole:
         if col==DUSTCOLS.chainIndex:   return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         if col==DUSTCOLS.AddrStr:   return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         if col==DUSTCOLS.Btc:     return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
      elif role==Qt.ForegroundRole:
         return QVariant(Colors.Foreground)
      elif role==Qt.FontRole:
         if col==DUSTCOLS.Btc:
            return GETFONT('Fixed')

      return QVariant()

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==DUSTCOLS.chainIndex: return QVariant('Chain Index')
            if section==DUSTCOLS.AddrStr:   return QVariant('Recieving Address')
            if section==DUSTCOLS.Btc:     return QVariant('Amount')
      elif role==Qt.TextAlignmentRole:
         if orientation==Qt.Horizontal:
            if section==DUSTCOLS.chainIndex: return QVariant(Qt.AlignHCenter | Qt.AlignVCenter)
            if section==DUSTCOLS.AddrStr:   return QVariant(Qt.AlignHCenter | Qt.AlignVCenter)
            if section==DUSTCOLS.Btc:     return QVariant(Qt.AlignHCenter | Qt.AlignVCenter)
         return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))




