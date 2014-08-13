from PyQt4.Qt import QPushButton, SIGNAL, QTextEdit, QScrollArea, QTabWidget,\
   QLineEdit

from qtdefines import QRichLabel, makeHorizFrame, GETFONT, relaxedSizeNChar, \
   makeVertFrame
from armoryengine.ArmoryUtils import addrStr_to_hash160, LOGINFO,\
   BadAddressError, binary_to_hex, coin2str, isLikelyDataType, DATATYPE,\
   hex_to_binary, ph
from armoryengine.BDM import TheBDM
from armoryengine.Transaction import PyTx
from qtdialogs import DlgAddressInfo, DlgDispTxInfo
# Find the best implementation available on this platform
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

class PluginObject(object):

   tabName = 'Armory Search'
   maxVersion = '0.93'
   
   #############################################################################
   def __init__(self, main):

      def searchItem():
         found = False
         searchString = str(self.searchEntry.text())
         if len(searchString) > 0:
            likelyDataType = isLikelyDataType(searchString)    
            for wltID, wlt in self.main.walletMap.iteritems():
               if wlt.hasAddr(searchString):
                  searchHash = searchString if likelyDataType == DATATYPE.Hex \
                        else addrStr_to_hash160(searchString)[1]
                  dialog = DlgAddressInfo(wlt, searchHash, main=self.main)
                  dialog.exec_()
                  found = True
                  break
            if not found:
               cppTx = TheBDM.getTxByHash(searchString) \
                  if likelyDataType == DATATYPE.Hex else None
               if cppTx:
                  wltLE = wlt.cppWallet.getTxLedgerForComments()
                  for le in wltLE:
                     txHash = le.getTxHash()
                     if wlt.txAddrMap.has_key(txHash):
                        serializedCppTx = cppTx.serialize()
                        pytx = PyTx().unserialize(serializedCppTx)
                        DlgDispTxInfo(pytx, wlt).exec_()
                        found = True
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
   
   def getDisplayString(self, wlt, pyAddr):
      result = StringIO()
      print >>result, 'BTC Address :', pyAddr.getAddrStr()
      print >>result, 'Hash160[BE] :', binary_to_hex(pyAddr.getAddr160())
      print >>result, 'Ballance    :', coin2str(wlt.getAddrBalance(pyAddr.getAddr160()),rJust=False)
      print >>result, 'Comment     :', wlt.getComment(pyAddr)
      return result.getvalue()
      

   #############################################################################
   def getTabToDisplay(self):
      return self.tabToDisplay