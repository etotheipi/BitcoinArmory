from PyQt4.Qt import QPushButton, SIGNAL, QTextEdit, QScrollArea, QTabWidget,\
   QLineEdit

from qtdefines import QRichLabel, makeHorizFrame, GETFONT, relaxedSizeNChar, \
   makeVertFrame
from armoryengine.ArmoryUtils import addrStr_to_hash160, LOGINFO,\
   BadAddressError


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
                     self.resultsDisplay.setText(wlt.addrMap[searchHash].toString())
                     found = True
                     break
            except:
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


      

   #############################################################################
   def getTabToDisplay(self):
      return self.tabToDisplay