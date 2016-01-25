from PyQt4.Qt import QPushButton, SIGNAL, QTextEdit, QScrollArea, QTabWidget,\
   QLineEdit

from qtdefines import QRichLabel, makeHorizFrame, GETFONT, relaxedSizeNChar, \
   makeVertFrame
from armoryengine.ArmoryUtils import addrStr_to_hash160, LOGINFO,\
   BadAddressError, binary_to_hex, coin2str, isLikelyDataType, DATATYPE,\
   hex_to_binary, ph, BIGENDIAN
from armoryengine.BDM import TheBDM
from armoryengine.Transaction import PyTx
from qtdialogs import DlgAddressInfo, DlgDispTxInfo

class PluginObject(object):

   tabName = 'Armory Search'
   maxVersion = '0.93.99'
   
   #############################################################################
   def __init__(self, main):

      def searchItem():
         searchString = str(self.searchEntry.text())
         if len(searchString) > 0:
            likelyDataType = isLikelyDataType(searchString)    
            for wltID, wlt in self.main.walletMap.iteritems():
               if wlt.hasAddr(searchString):
                  searchHash = searchString if likelyDataType == DATATYPE.Hex \
                        else addrStr_to_hash160(searchString)[1]
                  dialog = DlgAddressInfo(wlt, searchHash, main=self.main)
                  dialog.exec_()
                  break
               if likelyDataType == DATATYPE.Hex:
                  walletLedger = wlt.cppWallet.getTxLedger()
                  txHashToFind = hex_to_binary(searchString, endOut=BIGENDIAN)
                  txFound = False
                  for entry in walletLedger:
                     if entry.getTxHash() ==  txHashToFind:
                        cppTx = TheBDM.getTxByHash(txHashToFind)
                        serializedCppTx = cppTx.serialize()
                        pytx = PyTx().unserialize(serializedCppTx)
                        DlgDispTxInfo(pytx, wlt, self.main, self.main).exec_()
                        txFound = True
                        break
                  if txFound:
                     break
            
      self.main = main
      lblHeader = QRichLabel(tr("""<b>Search Armory: </b>"""), doWrap=False)
      self.searchButton = QPushButton("Search")
      self.searchEntry = QLineEdit()
      self.main.connect(self.searchButton, SIGNAL('clicked()'), searchItem)
      topRow =  makeHorizFrame([lblHeader, self.searchEntry, self.searchButton, 'stretch'])


      self.searchPanel = makeVertFrame([topRow, 'stretch' ])
      # Now set the scrollarea widget to the layout
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(self.searchPanel)

   #############################################################################
   def getTabToDisplay(self):
      return self.tabToDisplay