from PyQt4.Qt import QPushButton, SIGNAL, QTextEdit, QScrollArea, QTabWidget,\
   QLineEdit

from qtdefines import QRichLabel, makeHorizFrame, GETFONT, relaxedSizeNChar, \
   makeVertFrame
from armoryengine.ArmoryUtils import addrStr_to_hash160, LOGINFO,\
   BadAddressError, binary_to_hex, coin2str
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
         self.resultsDisplay.setText('')
         searchString = str(self.searchEntry.text())
         if len(searchString) > 0:
            try:
               searchHash = addrStr_to_hash160(searchString)[1]
               for wltID, wlt in self.main.walletMap.iteritems():
                  if searchHash in wlt.addrMap:
                     self.resultsDisplay.setText(self.getDisplayString(wlt, wlt.addrMap[searchHash]))
                     found = True
                     break
            except BadAddressError:
               self.resultsDisplay.setText("Search string is not a valid address")
               LOGINFO("Search String is not an addresss") 
            if not found:
               self.resultsDisplay.setText("Address not found")
         else:
            self.resultsDisplay.setText("No address entered")
            
      self.main = main
      lblHeader    = QRichLabel(tr("""<b>Search Armory: </b>"""), doWrap=False)
      self.searchButton = QPushButton("Search")
      self.searchEntry = QLineEdit()
      self.main.connect(self.searchButton, SIGNAL('clicked()'), searchItem)
      topRow =  makeHorizFrame([lblHeader, self.searchEntry, self.searchButton, 'stretch'])
      
      self.resultsDisplay = self.createSearchResultsDisplay()
      

      self.searchPanel = makeVertFrame([topRow, self.resultsDisplay ])
      # Now set the scrollarea widget to the layout
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(self.searchPanel)

   def createSearchResultsDisplay(self):
      resultsDisplay = QTextEdit()
      resultsDisplay.setFont(GETFONT('Fixed', 8))
      w,h = relaxedSizeNChar(resultsDisplay, 68)[0], int(12 * 8.2)
      resultsDisplay.setMinimumWidth(w)
      resultsDisplay.setMinimumHeight(h)
      resultsDisplay.setReadOnly(True)
      return resultsDisplay
   
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