from operator import add, mul
import os

from PyQt4.Qt import QPushButton, SIGNAL, QTextEdit, QScrollArea, QTabWidget, \
   QLineEdit, QAbstractTableModel, QModelIndex, Qt, QVariant, QTableView, QIcon,\
   QDialogButtonBox, QGridLayout, QLabel, QComboBox, QMenu, QCursor, QListWidget,\
   QListWidgetItem, QMessageBox, QString

from CppBlockUtils import SecureBinaryData
from armoryengine.ArmoryUtils import RightNow, script_to_addrStr, \
   addrStr_to_hash160, enum, isASCII, PyBackgroundThread
from armoryengine.PyBtcWallet import PyBtcWallet
from qtdefines import QRichLabel, makeHorizFrame, GETFONT, relaxedSizeNChar, \
   makeVertFrame, tightSizeNChar, initialColResize, ArmoryDialog,\
   UnicodeErrorBox
from armorycolors import Colors
from armorymodels import WLTVIEWCOLS
from PyQt4 import QtGui


# Give an upper limit for any method to return
# if the limit is exceded raise MaxResultsExceeded exception
MAX_LIST_LEN = 20000000

class MaxResultsExceeded(Exception): pass
class WalletNotFound(object): pass

MAX_SEGMENT_LENGTH = 20
MAX_SEGMENTS = 20
MAX_UNKNOWN_SEGMENT_LENGTH = 10

BILLION_INT = 1000000000
OVER_BILLION_STR = '> 1 Billion'

class PluginObject(object):

   tabName = 'Pass Phrase Finder'
   maxVersion = '0.93.99'
   
   #############################################################################
   def __init__(self, main):
      self.searchThread = None
      self.passPhraseFinder = None
      self.isSearchOver = False
      
      def updateResults(resultStr):
         self.resultStr += resultStr
         
      def updateDisplay():
         if len(self.resultStr) > 0:
            self.resultsDisplay.append(self.resultStr)
            self.resultStr = ''
            self.resultsDisplay.moveCursor(QtGui.QTextCursor.End)
            self.resultsDisplay.repaint()
         if self.isSearchOver:
            endSearch()
      
      # Call this from another thread to end the search
      def terminateSearch():
         self.isSearchOver = True
      
      # Call this from the main thread to end the search
      def endSearch():
         self.main.extraHeartbeatAlways.remove(updateDisplay)
         self.searchButton.setEnabled(True)
         self.stopButton.setEnabled(False)
         # If the thread is still searching tell the pass phrase finder to stop
         if self.passPhraseFinder and self.searchThread  and not self.searchThread.isFinished():
            self.passPhraseFinder.isStopped = True
            
      def searchForPassphrase():
         # Get the selected wallet from the main screen
         wlt = self.getSelectedWlt()
         if wlt and not wlt.watchingOnly and wlt.isLocked:
            self.resultStr = ''
            self.passPhraseFinder = PassPhraseFinder(wlt)
            self.resultsDisplay.setText(QString(''))
            self.main.extraHeartbeatAlways.append(updateDisplay)
            if len(self.segOrdStrSet) > 0:
               # From self.segOrdStrList, create a list of lists of indexes that describe the segment orderings to search
               # In other words convert all of the strings in orderings list to lists of integers
               segOrdIntListList = []
               for ordStr in self.segOrdStrSet:
                  # The indexes provided by the users are 1 based, and the list indexes ought to be 0 based
                  segOrdIntListList.append([int(indexStr)-1 for indexStr in ordStr.split(',')])
               self.searchThread = PyBackgroundThread(self.passPhraseFinder.searchForPassPhrase, 
                  [segDef.getSegList() for segDef in self.segDefList], 
                  segOrdIntListList, 
                  updateResults,
                  terminateSearch )
               # Reset the isSearchOver flag
               self.isSearchOver = False
               self.searchThread.start()
               
               # Disable search button adn enabled stop button
               self.stopButton.setEnabled(True)
               self.searchButton.setEnabled(False)
            else:
               QMessageBox.warning(self.main, tr('Invalid'), tr("""
                  There are no valid segment combinations to search.
                  Please add at least one segment and ordering to search."""), QMessageBox.Ok)
         else:
            QMessageBox.warning(self.main, tr('Invalid'), tr("""
               No valid wallet is selected. Please select a locked
               non-watching-only from Available Wallets."""), QMessageBox.Ok)

      def addKnownSegment():
         dlgEnterSegment = DlgEnterSegment(main, main)
         if dlgEnterSegment.exec_():
            segmentText = str(dlgEnterSegment.editSegment.text())
            if len(segmentText)>0:
               self.segDefList.append(KnownSeg(segmentText))
               self.segDefTableModel.updateSegList(self.segDefList)
      
      def addUnknownCaseSegment():
         dlgEnterSegment = DlgEnterSegment(main, main)
         if dlgEnterSegment.exec_():
            segmentText = str(dlgEnterSegment.editSegment.text())
            if len(segmentText)>0:
               self.segDefList.append(UnknownCaseSeg(segmentText))
               self.segDefTableModel.updateSegList(self.segDefList)
               
      def addUnknownOrderSegment():
         dlgEnterSegment = DlgEnterSegment(main, main, isUnknownOrder=True)
         if dlgEnterSegment.exec_():
            segmentText = str(dlgEnterSegment.editSegment.text())
            minLen = int(str(dlgEnterSegment.minSelector.currentText()))
            maxLen = int(str(dlgEnterSegment.maxSelector.currentText()))
            if len(segmentText)>0:
               self.segDefList.append(UnknownSeg(segmentText, minLen, maxLen))
               self.segDefTableModel.updateSegList(self.segDefList)

      def addOrdering():
         if len(self.segDefList) > 0:
            dlgSpecifyOrdering = DlgSpecifyOrdering(main, main, len(self.segDefList))     
            if dlgSpecifyOrdering.exec_():
               self.segOrdStrSet.add(str(dlgSpecifyOrdering.parseOrderingList()).strip('[]'))
               self.updateOrderingListBox()
         else:
            QMessageBox.warning(self.main, tr('Not Ready'), tr("""
               No segments have been entered. You must enter some segments before you can order them."""), QMessageBox.Ok)

      
      self.main = main
      self.segDefList = []
      self.segOrdStrSet = set()
      segmentHeader = QRichLabel(tr("""<b>Build segments for pass phrase search: </b>"""), doWrap=False)
      self.knownButton = QPushButton("Add Known Segment")
      self.unknownCaseButton = QPushButton("Add Unknown Case Segment")
      self.unknownOrderButton = QPushButton("Add Unknown Order Segment")
      self.main.connect(self.knownButton, SIGNAL('clicked()'), addKnownSegment)
      self.main.connect(self.unknownCaseButton, SIGNAL('clicked()'), addUnknownCaseSegment)
      self.main.connect(self.unknownOrderButton, SIGNAL('clicked()'), addUnknownOrderSegment)
      topRow =  makeHorizFrame([segmentHeader, self.knownButton, self.unknownCaseButton, self.unknownOrderButton, 'stretch'])
      
      self.segDefTableModel = SegDefDisplayModel()
      self.segDefTableView = QTableView()
      self.segDefTableView.setModel(self.segDefTableModel)
      self.segDefTableView.setSelectionBehavior(QTableView.SelectRows)
      self.segDefTableView.setSelectionMode(QTableView.SingleSelection)
      self.segDefTableView.verticalHeader().setDefaultSectionSize(20)
      self.segDefTableView.verticalHeader().hide()
      
      h = tightSizeNChar(self.segDefTableView, 1)[1]
      self.segDefTableView.setMinimumHeight(2 * (1.3 * h))
      self.segDefTableView.setMaximumHeight(10 * (1.3 * h))      
      initialColResize(self.segDefTableView, [.1, .2, .4, .1, .1, .1])

      self.segDefTableView.customContextMenuRequested.connect(self.showSegContextMenu)
      self.segDefTableView.setContextMenuPolicy(Qt.CustomContextMenu)
      
      segmentOrderingsHeader = QRichLabel(tr("""<b>Specify orderings for pass phrase search: </b>"""), doWrap=False)
      self.addOrderingButton = QPushButton("Add Ordering")
      
      
      self.main.connect(self.addOrderingButton, SIGNAL('clicked()'), addOrdering)
      orderingButtonPanel = makeHorizFrame([segmentOrderingsHeader, self.addOrderingButton, 'stretch'])

      self.segOrdListBox  = QListWidget()
      
      self.segOrdListBox.customContextMenuRequested.connect(self.showOrdContextMenu)
      self.segOrdListBox.setContextMenuPolicy(Qt.CustomContextMenu)
      
      
      self.searchButton = QPushButton("Search")
      self.main.connect(self.searchButton, SIGNAL('clicked()'), searchForPassphrase)
      self.stopButton = QPushButton("Stop Searching")
      self.stopButton.setEnabled(False)
      self.main.connect(self.stopButton, SIGNAL('clicked()'), endSearch)
      totalSearchLabel = QRichLabel(tr("""<b>Total Passphrase Tries To Search: </b>"""), doWrap=False)
      self.totalSearchTriesDisplay = QLineEdit()
      self.totalSearchTriesDisplay.setReadOnly(True)
      self.totalSearchTriesDisplay.setText(QString('0'))
      self.totalSearchTriesDisplay.setFont(GETFONT('Fixed'))
      self.totalSearchTriesDisplay.setMinimumWidth(tightSizeNChar(self.totalSearchTriesDisplay, 6)[0])
      self.totalSearchTriesDisplay.setMaximumWidth(tightSizeNChar(self.totalSearchTriesDisplay, 12)[0])
      searchButtonPanel = makeHorizFrame([self.searchButton, self.stopButton, 'stretch', totalSearchLabel,  self.totalSearchTriesDisplay])
      
      self.resultsDisplay = QTextEdit()
      self.resultsDisplay.setReadOnly(True)
      self.resultsDisplay.setFont(GETFONT('Fixed'))
      self.resultsDisplay.setMinimumHeight(100)
      self.searchPanel = makeVertFrame([topRow, self.segDefTableView, orderingButtonPanel,
             self.segOrdListBox, searchButtonPanel, self.resultsDisplay, 'stretch'])
      # Now set the scrollarea widget to the layout
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(self.searchPanel)
   
   def getSelectedWlt(self):
      wlt = None
      selectedWltList = self.main.walletsView.selectedIndexes()
      if len(selectedWltList)>0:
            row = selectedWltList[0].row()
            wltID = str(self.main.walletsView.model().index(row, WLTVIEWCOLS.ID).data().toString())
            wlt = self.main.walletMap[wltID]
      return wlt
   
   def showSegContextMenu(self):
      menu = QMenu(self.segDefTableView)
      if len(self.segDefTableView.selectedIndexes())==0:
         return

      row = self.segDefTableView.selectedIndexes()[0].row()
      deleteSegMenuItem = menu.addAction("Delete Segment")
      action = menu.exec_(QCursor.pos())
      
      if action == deleteSegMenuItem:
         self.deleteSegRow(row)
         
   def showOrdContextMenu(self):
      menu = QMenu(self.segOrdListBox)
      if len(self.segOrdListBox.selectedItems())==0:
         return

      item = self.segOrdListBox.currentItem()
      deleteOrdMenuItem = menu.addAction("Delete Ordering")
      action = menu.exec_(QCursor.pos())
      
      if action == deleteOrdMenuItem:
         self.deleteOrdItem(item)
         
   def deleteSegRow(self, row):
      self.segDefList.remove(self.segDefList[row])
      self.segDefTableModel.updateSegList(self.segDefList)
      self.segOrdStrSet.clear()
      self.updateOrderingListBox()
   
         
   def deleteOrdItem(self, ordItem):
      ordText = str(ordItem.text())
      self.segOrdStrSet.remove(ordText)
      self.updateOrderingListBox()
   
   
   def getTabToDisplay(self):
      return self.tabToDisplay

   def updateOrderingListBox(self):
      self.segOrdListBox.clear()
      segOrdList = list(self.segOrdStrSet)
      segOrdList.sort()
      totalTries = 0
      for ordStr in segOrdList:
         self.segOrdListBox.addItem(QListWidgetItem(ordStr))
         totalTries += self.calculateTries(ordStr)
      if totalTries > BILLION_INT:
         self.totalSearchTriesDisplay.setText(OVER_BILLION_STR)
      else:         
         self.totalSearchTriesDisplay.setText(str(totalTries))
      
   def calculateTries(self, ordStr):
      ordIntList = [int(indexStr) for indexStr in ordStr.split(',')]
      totalTries = 1
      # Multiply each of the totals of segment instance together.
      for ordInt in ordIntList:
         totalTries *= self.segDefList[ordInt-1].getSegListLen()
      return totalTries
   
class DlgSpecifyOrdering(ArmoryDialog):

   def __init__(self, parent, main, maxSeg):
      super(DlgSpecifyOrdering, self).__init__(parent, main)
      self.maxSeg = maxSeg
      self.setWindowTitle('Enter Ordering')
      self.setWindowIcon(QIcon(self.main.iconfile))
      buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonbox, SIGNAL('accepted()'), self.accept)
      self.connect(buttonbox, SIGNAL('rejected()'), self.reject)

      layout = QGridLayout()
      lbl =  QLabel('Enter Ordering as a comma separated list of segment indices between 1 and %d:' % maxSeg)
      self.editOrdering = QLineEdit()
      h, w = relaxedSizeNChar(self, 50)
      self.editOrdering.setMinimumSize(h, w)
      self.editOrdering.setMaxLength(MAX_SEGMENTS)
      editSegPanel = makeHorizFrame([self.editOrdering, 'stretch'])
      layout.addWidget(lbl, 0, 0)
      layout.addWidget(editSegPanel, 0, 1)
      layout.addWidget(buttonbox, 1, 0)
      
      self.setLayout(layout)
   
   # return empty list if not a valid list of numbers
   def parseOrderingList(self):
      try:
         return [int(i) for i in str(self.editOrdering.text()).split(',')]
      except:
         return []
      
   #############################################################################
   def accept(self):
      orderingList = self.parseOrderingList() 
      if len(orderingList) < 1:
         QMessageBox.warning(self.main, tr('Invalid'), tr("""
            Some segment indices are invalid."""), QMessageBox.Ok)
         return
      for segIndex in orderingList:
         if segIndex > self.maxSeg or segIndex < 1:
            QMessageBox.warning(self.main, tr('Invalid'), tr("""
               Some segment indices are out of range."""), QMessageBox.Ok)
            return
      super(DlgSpecifyOrdering, self).accept()  
 
################################################################################
class DlgEnterSegment(ArmoryDialog):

   #############################################################################
   def __init__(self, parent, main, isUnknownOrder=False):
      super(DlgEnterSegment, self).__init__(parent, main)
      self.setWindowTitle('Enter Segment')
      self.setWindowIcon(QIcon(self.main.iconfile))
      buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | \
                                   QDialogButtonBox.Cancel)
      self.connect(buttonbox, SIGNAL('accepted()'), self.accept)
      self.connect(buttonbox, SIGNAL('rejected()'), self.reject)

      layout = QGridLayout()
      lbl =  QLabel('Segment Text:')
      self.editSegment = QLineEdit()
      h, w = relaxedSizeNChar(self, 50)
      self.editSegment.setMinimumSize(h, w)
      self.editSegment.setMaxLength(MAX_SEGMENT_LENGTH)
      editSegPanel = makeHorizFrame([self.editSegment, 'stretch'])
      layout.addWidget(lbl, 0, 0)
      layout.addWidget(editSegPanel, 0, 1)
   
      minSelectorLabel = QLabel('Min Length: ')
      maxSelectorLabel = QLabel('Max Length: ')
      self.minSelector = QComboBox()
      self.maxSelector = QComboBox()      
      if isUnknownOrder:
         self.minSelector.setFont(GETFONT('Var', 10, bold=True))
         self.maxSelector.setFont(GETFONT('Var', 10, bold=True))
         for i in range(1,MAX_UNKNOWN_SEGMENT_LENGTH):
            self.minSelector.addItem(str(i))
            self.maxSelector.addItem(str(i))
         # default to 1 to 4
         self.minSelector.setCurrentIndex(0)
         self.maxSelector.setCurrentIndex(0)
         
         # fix the inversion of min and max when user sets min
         def updateMaxSelector():
            minLen = int(str(self.minSelector.currentText()))
            maxLen = int(str(self.maxSelector.currentText()))
            if minLen > maxLen:
               self.maxSelector.setCurrentIndex(minLen - 1)
         
         # fix the inversion of min and max when user sets max
         def updateMinSelector():
            minLen = int(str(self.minSelector.currentText()))
            maxLen = int(str(self.maxSelector.currentText()))
            if minLen > maxLen:
               self.minSelector.setCurrentIndex(maxLen - 1)
               
         main.connect(self.minSelector, SIGNAL('activated(int)'), \
                                             updateMaxSelector)
         main.connect(self.maxSelector, SIGNAL('activated(int)'), \
                                             updateMinSelector)
            
         layout.addWidget(minSelectorLabel, 1, 0)
         minSelectorPanel = makeHorizFrame([self.minSelector,'stretch'])
         layout.addWidget(minSelectorPanel, 1, 1)
         layout.addWidget(maxSelectorLabel, 2, 0)
         maxSelectorPanel = makeHorizFrame([self.maxSelector,'stretch'])
         layout.addWidget(maxSelectorPanel, 2, 1)
         layout.addWidget(buttonbox, 3, 0)
      else:
         layout.addWidget(buttonbox, 1, 0)
      
      self.setLayout(layout)

   #############################################################################
   def accept(self):
      if not isASCII(unicode(self.editSegment.text())):
         UnicodeErrorBox(self)
         return
      else:
         super(DlgEnterSegment, self).accept()  
   
class PwdSeg(object):
   def __init__(self, known):
      self.known = known
   
   # Abstract method
   def getSegListLen(self):
      raise NotImplementedError("Subclass must implement getSegListLength()")

   # Abstract Generator
   def segListGenerator(self, maxResults=MAX_LIST_LEN):
      raise NotImplementedError("Subclass must implement getSegList()")
      yield None
   
   # Abstract method
   def getSegList(self, maxResults=MAX_LIST_LEN):
      raise NotImplementedError("Subclass must implement getSegList()")

class UnknownCaseSeg(PwdSeg):
   def __init__(self, known):
      super(UnknownCaseSeg, self).__init__(known)
   
   getBothCases = lambda self, ch : [ch.lower(), ch.upper()] if ch.lower() != ch.upper() else [ch]
   
   def segListRecursiveGenerator(self, seg):
      if len(seg) > 0:
         for a in self.getBothCases(seg[0]):
            for b in self.segListRecursiveGenerator(seg[1:]):
               yield a + b
      else:
         yield ''
         
   def getSegListLen(self):
      return reduce(mul, [1 if ch.lower() == ch.upper() else 2 for ch in self.known]) 
   
   def segListGenerator(self, maxResults=MAX_LIST_LEN):
      if self.getSegListLen() > maxResults:
         raise MaxResultsExceeded
      for seg in self.segListRecursiveGenerator(self.known):
         yield seg
      
   def getSegList(self, maxResults=MAX_LIST_LEN):
      return [seg for seg in self.segListGenerator(maxResults)] 
   
class KnownSeg(PwdSeg):
   def __init__(self, known):
      super(KnownSeg, self).__init__(known)
   
   def getSegListLen(self):
      return 1

   def segListGenerator(self, maxResults=MAX_LIST_LEN):
      yield self.known

   def getSegList(self, maxResults=MAX_LIST_LEN):
      return [seg for seg in self.segListGenerator()]
   
class UnknownSeg(PwdSeg):
   def __init__(self, known, minLen, maxLen):
      super(UnknownSeg, self).__init__(known)
      self.removeDups()
      self.minLen = minLen
      self.maxLen = maxLen
   
   # Crate a sorted list of unique characters from the user entry
   def removeDups(self):
      uniqueCharList = list(set(self.known))
      uniqueCharList.sort()
      self.known = ''.join(uniqueCharList)
      
   def segListRecursiveGenerator(self, segLen):
      if segLen > 0:
         for a in self.known:
            for b in self.segListRecursiveGenerator(segLen-1):
               yield a + b
      else:
         yield ''

   def getSegListLen(self):
      return reduce(add, [len(self.known) ** i for i in range(self.minLen, self.maxLen + 1)]) 
   
   def segListGenerator(self, maxResults=MAX_LIST_LEN):
      if self.getSegListLen() > maxResults:
         raise MaxResultsExceeded
      for segLen in range(self.minLen, self.maxLen + 1):
         for seg in self.segListRecursiveGenerator(segLen):
            yield seg
   
   def getSegList(self, maxResults=MAX_LIST_LEN):
      return [seg for seg in self.segListGenerator(maxResults)]
   



class PassPhraseFinder(object): 
   def __init__(self, wallet):
      self.wallet = wallet
      self.isStopped = False


   def countPassPhrases(self, segList, segOrdList):
      return reduce(add, [reduce(mul, [len(segList[segIndex])
                                       for segIndex in segOrd])
                          for segOrd in segOrdList])
   
   def recursivePassPhraseGenerator(self, segList):
      if len(segList) > 0:
         for a in segList[0]:
            for b in self.recursivePassPhraseGenerator(segList[1:]):
               yield a + b
      else:
         yield ''
         
   # Generates PassPhrases from segs in segList
   #     Example Input: [['Andy','b','c'],['1','2'],['!']]
   # The segOrdList contains a list of ordered 
   # permutations of the segList:
   #     Example Input: [[0,1,2],[2,0,1,],[0,1]]
   # Yields one PassPhrase at a time until all permutations are exhausted
   #     Example: Andy1!, Andy2!, b1!, b2!, c1!, c2!,
   #              !Andy1, !Andy2, !b1, !b2, !c1, !c2,
   #              Andy1, Andy2, b1, b2, c1, c2
   # The above example is a test case found in test/FindPassTest.py
   def passPhraseGenerator(self, segList, segOrdList):
      for segOrd in segOrdList:
         orderedSegList = [segList[segIndex] for segIndex in segOrd]
         for result in self.recursivePassPhraseGenerator(orderedSegList):
            yield result
   
   def searchForPassPhrase(self, segList, segOrdList, outputCallback, endCallback):
      # if segOrdList is nonempty seglist must be non-empty too
      if len(segOrdList) == 0:
         QMessageBox.warning(self.main, tr('Invalid'), tr("""
            No segment orderings have been specified."""), QMessageBox.Ok)
      passPhraseCount = self.countPassPhrases(segList, segOrdList)
      startTime = RightNow()
      found = False
      result = None
      outputLine = ''
      for i,p in enumerate(self.passPhraseGenerator(segList, segOrdList)):
         isValid = self.wallet.verifyPassphrase( SecureBinaryData(p) ) 
            
         if isValid:
            # If the passphrase was wrong, it would error out, and not continue
            outputCallback(outputLine)
            outputCallback('\nPassphrase found!\n')
            outputCallback('\tThe Pass Phrase for ' + self.wallet.labelName + ' is: ' + p + '\n')
            outputCallback('Thanks for using this script.  If you recovered coins because of it, \n')
            outputCallback('please consider donating :) \n')
            outputCallback('   1ArmoryXcfq7TnCSuZa9fQjRYwJ4bkRKfv\n')
            result = p
            found = True
            break
         elif i%100==0:
            telapsed = (RightNow() - startTime)/3600.
            outputCallback( ('\n%d/%d passphrases tested... (%0.1f hours so far)'%(i,passPhraseCount,telapsed)).rjust(40))
         outputLine += p
         if i % 10 == 9:
            outputCallback(outputLine)
            outputLine = ''
         else:
            outputLine += ' '
         if self.isStopped:
            return result
      if not found:
         outputCallback('Script finished!\n')
         outputCallback('Sorry, none of the provided passphrases were correct :(')
      endCallback()
      return result



SEGDEFCOLS = enum('index', 'type', 'text', 'minLength', 'maxLength', 'totalCombinations')
SEGTYPES = enum('known', 'unknownCase', 'unknownOrder')

################################################################################
class SegDefDisplayModel(QAbstractTableModel):
   def __init__(self):
      super(SegDefDisplayModel, self).__init__()
      self.segDefList = []

   def updateSegList(self, segDefList):
      self.segDefList = []
      self.segDefList.extend(segDefList)
      self.reset()

   def rowCount(self, index=QModelIndex()):
      return len(self.segDefList)

   def columnCount(self, index=QModelIndex()):
      return 6

   def data(self, index, role=Qt.DisplayRole):
      row,col = index.row(), index.column()
      segDef = self.segDefList[row]
      segType = 'Known' if isinstance(segDef, KnownSeg) else \
                'Unknown Case' if isinstance(segDef, UnknownCaseSeg) else \
                'Unknown Order'
      segText = segDef.known
      if isinstance(segDef, UnknownSeg):
         segMinLength = segDef.minLen
         segMaxLength = segDef.maxLen
      else:
         segMinLength = len(segText)
         segMaxLength = len(segText)
      totalCombinations = segDef.getSegListLen()
      if totalCombinations > BILLION_INT:
         totalCombinations = OVER_BILLION_STR
      
      if role==Qt.DisplayRole:
         if col==SEGDEFCOLS.index: return QVariant(row+1)
         if col==SEGDEFCOLS.type: return QVariant(segType)
         if col==SEGDEFCOLS.text:     return QVariant(segText)
         if col==SEGDEFCOLS.minLength: return QVariant(segMinLength)
         if col==SEGDEFCOLS.maxLength: return QVariant(segMaxLength)
         if col==SEGDEFCOLS.totalCombinations: return QVariant(totalCombinations)
      elif role==Qt.TextAlignmentRole:
         return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
      elif role==Qt.ForegroundRole:
         return QVariant(Colors.Foreground)
      return QVariant()

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==SEGDEFCOLS.index: return QVariant('Index')
            if section==SEGDEFCOLS.type: return QVariant('Type')
            if section==SEGDEFCOLS.text: return QVariant('Text')
            if section==SEGDEFCOLS.minLength: return QVariant('Min')
            if section==SEGDEFCOLS.maxLength: return QVariant('Max')
            if section==SEGDEFCOLS.totalCombinations: return QVariant('Total Combinations')
      elif role==Qt.TextAlignmentRole:
         if orientation==Qt.Horizontal:
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         else:
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))



