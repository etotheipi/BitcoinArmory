#!/usr/bin/env python
# Copyright (c) 2007-8 Qtrac Ltd. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

import os
import platform
import sys
from os import path
from PyQt4.QtCore import *
from PyQt4.QtGui import *
#import qrc_resources

from optparse import OptionParser



__version__ = "0.0.1"

sys.path.append('..')
sys.path.append('../cppForSwig')
from pybtcengine import *
from CppBlockUtils import *


class BtcExploreWindow(QMainWindow):

   def __init__(self, parent=None):
      super(BtcExploreWindow, self).__init__(parent)

      defaultBlkFile = ''
      opsys = platform.system()
      if 'win' in opsys.lower():
         defaultBlkFile = path.join(os.getenv('APPDATA'), 'Bitcoin', 'blk0001.dat')
      if 'nix' in opsys.lower() or 'nux' in opsys.lower():
         defaultBlkFile = path.join(os.getenv('HOME'), '.bitcoin', 'blk0001.dat')
      if 'mac' in opsys.lower() or 'osx' in opsys.lower():
			defaultBlkFile = os.path.expanduser('~/Library/Application Support/Bitcoin/blk0001.dat')


      settings = QSettings()
      if len(sys.argv) > 1:
         self.blkFile     = sys.argv[1]
      else:
         self.blkFile     = str(settings.value('BlockFile', defaultBlkFile).toString())

      self.wltFileList = settings.value('WalletFiles').toStringList()
      self.bcLoadDoneYet = False
      self.setMinimumSize(1000,700)

      # Search bar
      self.lblSearch = QLabel('&Search:')
      self.lblSearch.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
      self.edtSearch = QLineEdit('Please wait while the blockchain is loaded...')
      self.edtSearch.setEnabled(False)
      self.edtSearch.setAlignment(Qt.AlignVCenter)
      self.btnSearch = QLineEdit()
      self.btnSearch.setAlignment(Qt.AlignVCenter)
      self.lblSearch.setBuddy(self.edtSearch)
      self.btnSearch = QPushButton('Go!')
      self.btnSearch.setEnabled(False)
      #self.connect(self.edtSearch, SIGNAL('returnPressed()'), \
                   #self.doSearch(self.edtSearch.text()) )
      
      # Set Endianness preferences
      self.gbxEndian = QGroupBox()
      self.gbxEndian.setCheckable(False)
      self.gbxEndian.setTitle(QString('Display Hashes'))
      
      self.gbxLayout  = QVBoxLayout()
      self.rdoEndianD = QRadioButton("&Default")
      self.rdoEndianL = QRadioButton("&Little Endian")
      self.rdoEndianB = QRadioButton("&Big Endian")

      self.gbxLayout.addWidget(self.rdoEndianD);
      self.gbxLayout.addWidget(self.rdoEndianL);
      self.gbxLayout.addWidget(self.rdoEndianB);
      self.gbxLayout.addStretch(1)
      self.rdoEndianD.setChecked(True)
      self.gbxEndian.setLayout(self.gbxLayout)
      self.connect(self.gbxEndian, SIGNAL('clicked()'), self.updateUI)

      # Set area to display selected object properties
      self.txtSelectedInfo = QLabel()
      self.txtSelectedInfo.setWordWrap(True)
      self.txtSelectedInfo.setMinimumSize(200,200)

      ##### Set up the QTableWidgets to display... just about everything
      # Set up the headers table
      headersTableHeadRow = ['Block#', 'Hash', 'Difficulty', 'Num Tx', 'Datetime']
      self.tblHeaders = self.createTableWidget(headersTableHeadRow, (600, 200))
      # Set up the transactions table
      txTableHeadRow = ['Hash', 'Total BTC', 'Src', 'Dst', 'Size(kB)'] #, 'Locktime']
      self.tblTxs = self.createTableWidget(txTableHeadRow, (600,300))
      # Set up the TxIn table
      txinHeadRow = ['Sender', 'BTC', 'From Block#', 'Sequence']
      self.tblTxIns = self.createTableWidget(txinHeadRow, (400,100))
      # Set up the TxOut table
      txoutHeadRow = ['Recipient', 'BTC', 'Script Type']
      self.tblTxOuts = self.createTableWidget(txoutHeadRow, (400,100))
      # Set up the Address table
      addrHeadRow = ['Address (Base58)', 'Address (20 byte hex)', 'BTC Sent', 'Btc Rcvd']
      self.tblAddrs = self.createTableWidget(addrHeadRow, (300,200))

      #self.connect(self.tblHeaders, SIGNAL('cellDoubleClicked(int,int)'), self.dispSelected)

      # And a few random labels
      lblHeaders = QLabel('Headers:');      lblHeaders.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
      lblTxs     = QLabel('Transactions:'); lblTxs.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
      lblTxIns   = QLabel('TxIn List:');    lblTxIns.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
      lblTxOuts  = QLabel('TxOut List:');   lblTxOuts.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
      lblAddrs   = QLabel('Addresses:');    lblAddrs.setAlignment(Qt.AlignBottom | Qt.AlignLeft)

      # Set up the central widget
      self.ctrFrame = QFrame()
      self.ctrFrame.setFrameShape(QFrame.NoFrame)

      # Finally, set up the central widget
      self.ctrLayout = QGridLayout()
      #                                             Row  Col nRows nCols
      self.ctrLayout.addWidget(self.lblSearch,        1,   0,   1,   1)
      self.ctrLayout.addWidget(self.edtSearch,        1,   1,   1,   2)
      self.ctrLayout.addWidget(self.btnSearch,        1,   3,   1,   1)
      self.ctrLayout.addWidget(self.gbxEndian,        0,   5,   3,   1)

      self.ctrLayout.addWidget(lblHeaders,            2,   0,   1,   1)
      self.ctrLayout.addWidget(lblTxIns,              2,   4,   1,   1)

      self.ctrLayout.addWidget(self.tblHeaders,       3,   0,   2,   4)
      self.ctrLayout.addWidget(self.tblTxIns,         3,   4,   2,   2)

      self.ctrLayout.addWidget(lblTxs,                5,   0,   1,   1)
      self.ctrLayout.addWidget(lblTxOuts,             5,   4,   1,   1)
      #self.ctrLayout.addWidget(lblAddrs,              5,   4,   1,   1)

      self.ctrLayout.addWidget(self.tblTxs,           6,   0,   3,   4)
      self.ctrLayout.addWidget(self.tblTxOuts,        6,   4,   2,   2)
      #self.ctrLayout.addWidget(self.tblAddrs,         5,   4,   2,   2)

      self.ctrLayout.addWidget(self.txtSelectedInfo,  8,   4,   1,   2)

      # Finally set the layout
      self.ctrFrame.setLayout(self.ctrLayout)
      self.setCentralWidget(self.ctrFrame)

      # We will store the current "selection" here.
      #self.primarySelect = 'Header'
      self.selectedObjs = {'Header': None, \
                           'Tx':     None, \
                           'TxIn':   None, \
                           'TxOut':  None, \
                           'Addr':   None}

      # Prepare the BlockDataManager for 
      print 'GUI is setup, now load the blockchain'
      self.bdm = BlockDataManager_FullRAM.GetInstance()
      print 'holding'
      QTimer.singleShot(100, self.initBlockchain)

   def createTableWidget(self, headerRow, minSizePair=(300,150)):
      tbl = QTableWidget()
      tbl.setSelectionBehavior(QTableWidget.SelectRows)
      tbl.setSelectionMode(QTableWidget.SingleSelection)
      tbl.setRowCount(0);
      tbl.setColumnCount(len(headerRow))
      #tbl.setStretchLastSection(True)
      tbl.verticalHeader().setVisible(False)
      tbl.setMinimumSize( *minSizePair )
      tbl.setHorizontalHeaderLabels(headerRow)
      return tbl

   def initBlockchain(self):
      if not self.blkFile==None:
         self.bdm.readBlkFile_FromScratch(self.blkFile) 
         self.bdm.organizeChain()
         self.bcLoadDoneYet = True
         self.btnSearch.setEnabled(True)
         self.edtSearch.setEnabled(True)
         self.edtSearch.setText('');
         self.edtSearch.setFocus()
         self.updateUI()


   def getPrevTxOutData(self, txin):
      txout, addr, value, blkNumStr  = [None]*4
      if txin.isCoinbase():
         txout  = None
         addr   = '<COINBASE>'
         value  = -1
         blknum = ''
      else:
         txout  = self.bdm.getPrevTxOut(txin)
         addr   = txout.getRecipientAddr().toBinStr()
         value  = txout.getValue()
         blknum = self.bdm.getTxByHash(txin.getOutPointRef().getTxHash()).getHeaderPtr().getBlockHeight()
      return (txout, addr, value, blknum)
      

   #############################################################################
   def updateUI(self):
      if self.selectedObjs['Header'] == None:
         # Fill the headers table
         self.maxHeight = self.bdm.getTopBlockHeader().getBlockHeight()
         self.selectedObjs['Header'] = ('Height', self.maxHeight) # not really used

      sHeight = self.selectedObjs['Header'][1]
      self.fillHeadersTableBySelected(sHeight)
      currRow = self.tblHeaders.currentRow()
      txObjList = self.bdm.getHeaderByHeight(sHeight).getTxRefPtrList()
      self.fillTxTableByTxRefList(txObjList, self.selectedObjs['Tx'])
         
      txref = self.selectedObjs['Tx'][1]
      if self.selectedObjs['Tx'][0] == 'Hash':
         txref = self.bdm.getTxByHash(txref)
      self.fillTxInTableByTxRef( txref)
      self.fillTxOutTableByTxRef(txref)


   #############################################################################
   # First element in the list will be on the TOP
   def fillHeadersTableBySelected(self, selectedHeight):
      topH = min(self.maxHeight, selectedHeight+100)
      lowH = max(0,              selectedHeight-100)
      self.fillHeadersTableByHeightList( range(topH,lowH,-1), selectedHeight)


   def fillHeadersTableByHashList(self, hashList, selectedHash=None):
      heightList = []
      selectedHeight = None
      newHashList = filter(lambda h: h != None, hashList)
      for theHash in newHashList:
         theHeight = self.bdm.getHeaderByHash(theHash).getBlockHeight()
         heightList.append(theHeight)
         if theHash == selectedHash:
            selectedHeight = theHeight
      self.fillHeadersTableByHeightList( heightList, selectedHeight)

   #############################################################################
   # First element in the list will be on the TOP
   def fillHeadersTableByHeightList(self, heightList, selectedHeight=None):
      self.tblHeaders.clearContents()
      self.tblHeaders.setRowCount( len(heightList) )
      sItem = None
      for row,height in enumerate(heightList):
         head = self.bdm.getHeaderByHeight(height)
         cols = []
         cols.append( QTableWidgetItem(str(head.getBlockHeight())) )
         #cols.append( QTableWidgetItem(head.getThisHash().toHexStr()[:24] + '...') )
         cols.append( QTableWidgetItem(head.getThisHash().toHexStr()))
         cols.append( QTableWidgetItem("%0.2f" % head.getDifficulty()) )
         cols.append( QTableWidgetItem("%d" % head.getNumTx()))
         cols.append( QTableWidgetItem(unixTimeToFormatStr(head.getTimestamp()))) 
         cols[1].setFont( QFont("Courier", 10, QFont.Bold) )
         for c in range(len(cols)):
            self.tblHeaders.setItem(row, c, cols[c])
         if height==selectedHeight:
            sItem = cols[0]

      #self.tblHeaders.sizeHintForColumn()
      #self.tblHeaders.resizeColumnsToContents()
      #if not selectedHeight==None and selectedHeight in heightList:
         #self.tblHeaders.selectRow( heightList.index(selectedHeight))
      if not sItem == None:
         self.tblHeaders.setCurrentItem(sItem)
         self.tblHeaders.scrollToItem(sItem)

   #############################################################################
   # First element in the list will be on the TOP
   def fillTxTableByTxRefList(self, txrefList, selectedTxref=None):
      self.tblTxs.clearContents()
      self.tblTxs.setRowCount( len(txrefList) )
      
      sItem = None
      newTxList = filter(lambda t: t != None, txrefList)
      for row,tx in enumerate(txrefList):
         cols=[]
         cols.append( QTableWidgetItem(tx.getThisHash().toHexStr()))
         cols.append( QTableWidgetItem("%0.4f" % (float(tx.getSumOfOutputs()/1e8))))

         if tx.getNumTxIn() > 1:
            cols.append( QTableWidgetItem('<Multiple>') )
         else:
            txin = tx.getTxInRef(0)
      
            if txin.isCoinbase():
               cols.append( QTableWidgetItem('<COINBASE>') )
            else:
               addr20 = self.bdm.getSenderAddr20(tx.getTxInRef(0)).toBinStr()
               cols.append( QTableWidgetItem( hash160_to_addrStr(addr20) ))
            
         if tx.getNumTxOut() > 1:
            cols.append( QTableWidgetItem('<Multiple>') )
         else:
            addr20 = tx.getTxOutRef(0).getRecipientAddr().toBinStr()
            cols.append( QTableWidgetItem( hash160_to_addrStr(addr20) ))

         cols.append( QTableWidgetItem("%0.2f" % (float(tx.getSize())/1024.0) ))
         #cols.append( QTableWidgetItem("%d" % float(tx.getLockTime())))

         cols[0].setFont( QFont("Courier", 10, QFont.Bold) )
         for c in range(len(cols)):
            self.tblTxs.setItem(row, c, cols[c])
         if selectedTxref==tx:
            sItem = cols[0]
            self.selectedObjs['Tx'] = ('Ref', tx)
         
      if sItem==None:
         sItem = self.tblTxs.item(1,0)  # autoselect second row, first is coinbase
         self.selectedObjs['Tx'] = ('Ref', txrefList[1])

      self.tblTxs.setCurrentItem(sItem)
      self.tblTxs.scrollToItem(sItem)


   #############################################################################
   # First element in the list will be on the TOP
   def fillTxTableByHashList(self, txhashList, selectedHash=None):
      txrefList = []
      selectedTxRef = None
      for theHash in txhashList:
         txrefList.append( self.bdm.getTxByHash(theHash) )
         if theHash == selectedHash:
            selectedTxRef = txrefList[-1]

      self.fillTxTableByTxRefList(txrefList, selectedTxRef)

   #############################################################################
   # First element in the list will be on the TOP
   def fillTxInTableByTxRef(self, tx):
      nIn = tx.getNumTxIn()
      self.tblTxIns.setRowCount(nIn);
      for row in range(nIn):
         txin = tx.getTxInRef(row)
         (txout, sender, value, blknum) = self.getPrevTxOutData(txin)
         if txin.isCoinbase():
            value = tx.getTxOutRef(0).getValue()
            sender = '<COINBASE>'
         else:
            sender = hash160_to_addrStr(sender)

         cols = []
         cols.append( QTableWidgetItem(sender))
         cols.append( QTableWidgetItem("%0.4f" % (float(value)/1e8)))
         cols.append( QTableWidgetItem("%d" % blknum))
         cols.append( QTableWidgetItem(int_to_hex(txin.getSequence(), 4, BIGENDIAN)))
         for c in range(len(cols)):
            self.tblTxIns.setItem(row, c, cols[c])
         
      sItem = self.tblTxIns.item(0,0)
      self.tblTxIns.setCurrentItem(sItem)
      self.tblTxIns.scrollToItem(sItem)

   def fillTxOutTableByTxRef(self, tx):
      nOut = tx.getNumTxOut()
      self.tblTxOuts.setRowCount(nOut);
      for row in range(nOut):
         txout = tx.getTxOutRef(row)

         cols = []
         addr20 = txout.getRecipientAddr().toBinStr()
         cols.append( QTableWidgetItem( hash160_to_addrStr(addr20) ))
         cols.append( QTableWidgetItem("%0.4f" % (float(txout.getValue())/1e8)))
         if txout.isScriptStandard():
            cols.append( QTableWidgetItem('STANDARD') )
         elif txout.isScriptCoinbase():
            cols.append( QTableWidgetItem('COINBASE') )
         elif txout.isScriptUnknown():
            cols.append( QTableWidgetItem('UNKNOWN') )
         for c in range(len(cols)):
            self.tblTxOuts.setItem(row, c, cols[c])


   #############################################################################
   def doSearch(self, searchStr):
      if self.bcLoadDoneYet == False:
         QMessageBox.warning(self, 'Blockchain Manager Still Loading', \
                     unicode('Blockchain is not done loading.  Please wait!'))
         return
      else:
         print 'Need to do the search!?'
         

   
def main():
   app = QApplication(sys.argv)
   app.setOrganizationName("Etotheipi")
   app.setOrganizationDomain("none.org")
   app.setApplicationName("Python/SWIG Block Explorer")
   form = BtcExploreWindow()
   form.show()
   app.exec_()


main()


#   def updateUI(self, 
#
#      self.imageLabel = QLabel()
#      self.imageLabel.setMinimumSize(200, 200)
#      self.imageLabel.setAlignment(Qt.AlignCenter)
#      self.imageLabel.setContextMenuPolicy(Qt.ActionsContextMenu)
#      self.setCentralWidget(self.imageLabel)
#
#      logDockWidget = QDockWidget("Log", self)
#      logDockWidget.setObjectName("LogDockWidget")
#      logDockWidget.setAllowedAreas(Qt.LeftDockWidgetArea|
#                             Qt.RightDockWidgetArea)
#      self.listWidget = QListWidget()
#      logDockWidget.setWidget(self.listWidget)
#      self.addDockWidget(Qt.RightDockWidgetArea, logDockWidget)
#
#      self.printer = None
#
#      self.sizeLabel = QLabel()
#      self.sizeLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
#      status = self.statusBar()
#      status.setSizeGripEnabled(False)
#      status.addPermanentWidget(self.sizeLabel)
#      status.showMessage("Ready", 5000)
#
#      fileNewAction = self.createAction("&New...", self.fileNew,
#            QKeySequence.New, "filenew", "Create an image file")
#      fileOpenAction = self.createAction("&Open...", self.fileOpen,
#            QKeySequence.Open, "fileopen",
#            "Open an existing image file")
#      fileSaveAction = self.createAction("&Save", self.fileSave,
#            QKeySequence.Save, "filesave", "Save the image")
#      fileSaveAsAction = self.createAction("Save &As...",
#            self.fileSaveAs, icon="filesaveas",
#            tip="Save the image using a new name")
#      filePrintAction = self.createAction("&Print", self.filePrint,
#            QKeySequence.Print, "fileprint", "Print the image")
#      fileQuitAction = self.createAction("&Quit", self.close,
#            "Ctrl+Q", "filequit", "Close the application")
#      editInvertAction = self.createAction("&Invert",
#            self.editInvert, "Ctrl+I", "editinvert",
#            "Invert the image's colors", True, "toggled(bool)")
#      editSwapRedAndBlueAction = self.createAction(
#            "Sw&ap Red and Blue", self.editSwapRedAndBlue,
#            "Ctrl+A", "editswap",
#            "Swap the image's red and blue color components",
#            True, "toggled(bool)")
#      editZoomAction = self.createAction("&Zoom...", self.editZoom,
#            "Alt+Z", "editzoom", "Zoom the image")
#      mirrorGroup = QActionGroup(self)
#      editUnMirrorAction = self.createAction("&Unmirror",
#            self.editUnMirror, "Ctrl+U", "editunmirror",
#            "Unmirror the image", True, "toggled(bool)")
#      mirrorGroup.addAction(editUnMirrorAction)
#      editMirrorHorizontalAction = self.createAction(
#            "Mirror &Horizontally", self.editMirrorHorizontal,
#            "Ctrl+H", "editmirrorhoriz",
#            "Horizontally mirror the image", True, "toggled(bool)")
#      mirrorGroup.addAction(editMirrorHorizontalAction)
#      editMirrorVerticalAction = self.createAction(
#            "Mirror &Vertically", self.editMirrorVertical,
#            "Ctrl+V", "editmirrorvert",
#            "Vertically mirror the image", True, "toggled(bool)")
#      mirrorGroup.addAction(editMirrorVerticalAction)
#      editUnMirrorAction.setChecked(True)
#      helpAboutAction = self.createAction("&About Image Changer",
#            self.helpAbout)
#      helpHelpAction = self.createAction("&Help", self.helpHelp,
#            QKeySequence.HelpContents)
#
#      self.fileMenu = self.menuBar().addMenu("&File")
#      self.fileMenuActions = (fileNewAction, fileOpenAction,
#            fileSaveAction, fileSaveAsAction, None,
#            filePrintAction, fileQuitAction)
#      self.connect(self.fileMenu, SIGNAL("aboutToShow()"),
#                self.updateFileMenu)
#      editMenu = self.menuBar().addMenu("&Edit")
#      self.addActions(editMenu, (editInvertAction,
#            editSwapRedAndBlueAction, editZoomAction))
#      mirrorMenu = editMenu.addMenu(QIcon(":/editmirror.png"),
#                             "&Mirror")
#      self.addActions(mirrorMenu, (editUnMirrorAction,
#            editMirrorHorizontalAction, editMirrorVerticalAction))
#      helpMenu = self.menuBar().addMenu("&Help")
#      self.addActions(helpMenu, (helpAboutAction, helpHelpAction))
#
#      fileToolbar = self.addToolBar("File")
#      fileToolbar.setObjectName("FileToolBar")
#      self.addActions(fileToolbar, (fileNewAction, fileOpenAction,
#                             fileSaveAsAction))
#      editToolbar = self.addToolBar("Edit")
#      editToolbar.setObjectName("EditToolBar")
#      self.addActions(editToolbar, (editInvertAction,
#            editSwapRedAndBlueAction, editUnMirrorAction,
#            editMirrorVerticalAction,
#            editMirrorHorizontalAction))
#      self.zoomSpinBox = QSpinBox()
#      self.zoomSpinBox.setRange(1, 400)
#      self.zoomSpinBox.setSuffix(" %")
#      self.zoomSpinBox.setValue(100)
#      self.zoomSpinBox.setToolTip("Zoom the image")
#      self.zoomSpinBox.setStatusTip(self.zoomSpinBox.toolTip())
#      self.zoomSpinBox.setFocusPolicy(Qt.NoFocus)
#      self.connect(self.zoomSpinBox,
#                SIGNAL("valueChanged(int)"), self.showImage)
#      editToolbar.addWidget(self.zoomSpinBox)
#
#      self.addActions(self.imageLabel, (editInvertAction,
#            editSwapRedAndBlueAction, editUnMirrorAction,
#            editMirrorVerticalAction, editMirrorHorizontalAction))
#
#      self.resetableActions = ((editInvertAction, False),
#                         (editSwapRedAndBlueAction, False),
#                         (editUnMirrorAction, True))
#
#      settings = QSettings()
#      self.recentFiles = settings.value("RecentFiles").toStringList()
#      size = settings.value("MainWindow/Size",
#                       QVariant(QSize(600, 500))).toSize()
#      self.resize(size)
#      position = settings.value("MainWindow/Position",
#                          QVariant(QPoint(0, 0))).toPoint()
#      self.move(position)
#      self.restoreState(
#            settings.value("MainWindow/State").toByteArray())
#      
#      self.setWindowTitle("Image Changer")
#      self.updateFileMenu()
#      QTimer.singleShot(0, self.loadInitialFile)
#
#
#   def createAction(self, text, slot=None, shortcut=None, icon=None,
#                tip=None, checkable=False, signal="triggered()"):
#      action = QAction(text, self)
#      if icon is not None:
#         action.setIcon(QIcon(":/%s.png" % icon))
#      if shortcut is not None:
#         action.setShortcut(shortcut)
#      if tip is not None:
#         action.setToolTip(tip)
#         action.setStatusTip(tip)
#      if slot is not None:
#         self.connect(action, SIGNAL(signal), slot)
#      if checkable:
#         action.setCheckable(True)
#      return action
#
#
#   def addActions(self, target, actions):
#      for action in actions:
#         if action is None:
#            target.addSeparator()
#         else:
#            target.addAction(action)
#
#
#   def closeEvent(self, event):
#      if self.okToContinue():
#         settings = QSettings()
#         filename = QVariant(QString(self.filename)) \
#               if self.filename is not None else QVariant()
#         settings.setValue("LastFile", filename)
#         recentFiles = QVariant(self.recentFiles) \
#               if self.recentFiles else QVariant()
#         settings.setValue("RecentFiles", recentFiles)
#         settings.setValue("MainWindow/Size", QVariant(self.size()))
#         settings.setValue("MainWindow/Position",
#               QVariant(self.pos()))
#         settings.setValue("MainWindow/State",
#               QVariant(self.saveState()))
#      else:
#         event.ignore()
#
#
#   def okToContinue(self):
#      if self.dirty:
#         reply = QMessageBox.question(self,
#                     "Image Changer - Unsaved Changes",
#                     "Save unsaved changes?",
#                     QMessageBox.Yes|QMessageBox.No|
#                     QMessageBox.Cancel)
#         if reply == QMessageBox.Cancel:
#            return False
#         elif reply == QMessageBox.Yes:
#            self.fileSave()
#      return True
#
#
#   def loadInitialFile(self):
#      settings = QSettings()
#      fname = unicode(settings.value("LastFile").toString())
#      if fname and QFile.exists(fname):
#         self.loadFile(fname)
#
#
#   def updateStatus(self, message):
#      self.statusBar().showMessage(message, 5000)
#      self.listWidget.addItem(message)
#      if self.filename is not None:
#         self.setWindowTitle("Image Changer - %s[*]" % \
#                        os.path.basename(self.filename))
#      elif not self.image.isNull():
#         self.setWindowTitle("Image Changer - Unnamed[*]")
#      else:
#         self.setWindowTitle("Image Changer[*]")
#      self.setWindowModified(self.dirty)
#
#
#   def updateFileMenu(self):
#      self.fileMenu.clear()
#      self.addActions(self.fileMenu, self.fileMenuActions[:-1])
#      current = QString(self.filename) \
#            if self.filename is not None else None
#      recentFiles = []
#      for fname in self.recentFiles:
#         if fname != current and QFile.exists(fname):
#            recentFiles.append(fname)
#      if recentFiles:
#         self.fileMenu.addSeparator()
#         for i, fname in enumerate(recentFiles):
#            action = QAction(QIcon(":/icon.png"), "&%d %s" % (
#                  i + 1, QFileInfo(fname).fileName()), self)
#            action.setData(QVariant(fname))
#            self.connect(action, SIGNAL("triggered()"),
#                      self.loadFile)
#            self.fileMenu.addAction(action)
#      self.fileMenu.addSeparator()
#      self.fileMenu.addAction(self.fileMenuActions[-1])
#
#
#   def fileNew(self):
#      if not self.okToContinue():
#         return
#      dialog = newimagedlg.NewImageDlg(self)
#      if dialog.exec_():
#         self.addRecentFile(self.filename)
#         self.image = QImage()
#         for action, check in self.resetableActions:
#            action.setChecked(check)
#         self.image = dialog.image()
#         self.filename = None
#         self.dirty = True
#         self.showImage()
#         self.sizeLabel.setText("%d x %d" % (self.image.width(),
#                                    self.image.height()))
#         self.updateStatus("Created new image")
#
#
#   def fileOpen(self):
#      if not self.okToContinue():
#         return
#      dir = os.path.dirname(self.filename) \
#            if self.filename is not None else "."
#      formats = ["*.%s" % unicode(format).lower() \
#               for format in QImageReader.supportedImageFormats()]
#      fname = unicode(QFileDialog.getOpenFileName(self,
#                     "Image Changer - Choose Image", dir,
#                     "Image files (%s)" % " ".join(formats)))
#      if fname:
#         self.loadFile(fname)
#
#
#   def loadFile(self, fname=None):
#      if fname is None:
#         action = self.sender()
#         if isinstance(action, QAction):
#            fname = unicode(action.data().toString())
#            if not self.okToContinue():
#               return
#         else:
#            return
#      if fname:
#         self.filename = None
#         image = QImage(fname)
#         if image.isNull():
#            message = "Failed to read %s" % fname
#         else:
#            self.addRecentFile(fname)
#            self.image = QImage()
#            for action, check in self.resetableActions:
#               action.setChecked(check)
#            self.image = image
#            self.filename = fname
#            self.showImage()
#            self.dirty = False
#            self.sizeLabel.setText("%d x %d" % (
#                     image.width(), image.height()))
#            message = "Loaded %s" % os.path.basename(fname)
#         self.updateStatus(message)
#
#
#   def addRecentFile(self, fname):
#      if fname is None:
#         return
#      if not self.recentFiles.contains(fname):
#         self.recentFiles.prepend(QString(fname))
#         while self.recentFiles.count() > 9:
#            self.recentFiles.takeLast()
#
#
#   def fileSave(self):
#      if self.image.isNull():
#         return
#      if self.filename is None:
#         self.fileSaveAs()
#      else:
#         if self.image.save(self.filename, None):
#            self.updateStatus("Saved as %s" % self.filename)
#            self.dirty = False
#         else:
#            self.updateStatus("Failed to save %s" % self.filename)
#
#
#   def fileSaveAs(self):
#      if self.image.isNull():
#         return
#      fname = self.filename if self.filename is not None else "."
#      formats = ["*.%s" % unicode(format).lower() \
#               for format in QImageWriter.supportedImageFormats()]
#      fname = unicode(QFileDialog.getSaveFileName(self,
#                  "Image Changer - Save Image", fname,
#                  "Image files (%s)" % " ".join(formats)))
#      if fname:
#         if "." not in fname:
#            fname += ".png"
#         self.addRecentFile(fname)
#         self.filename = fname
#         self.fileSave()
#
#
#   def filePrint(self):
#      if self.image.isNull():
#         return
#      if self.printer is None:
#         self.printer = QPrinter(QPrinter.HighResolution)
#         self.printer.setPageSize(QPrinter.Letter)
#      form = QPrintDialog(self.printer, self)
#      if form.exec_():
#         painter = QPainter(self.printer)
#         rect = painter.viewport()
#         size = self.image.size()
#         size.scale(rect.size(), Qt.KeepAspectRatio)
#         painter.setViewport(rect.x(), rect.y(), size.width(),
#                        size.height())
#         painter.drawImage(0, 0, self.image)
#
#
#   def editInvert(self, on):
#      if self.image.isNull():
#         return
#      self.image.invertPixels()
#      self.showImage()
#      self.dirty = True
#      self.updateStatus("Inverted" if on else "Uninverted")
#
#
#   def editSwapRedAndBlue(self, on):
#      if self.image.isNull():
#         return
#      self.image = self.image.rgbSwapped()
#      self.showImage()
#      self.dirty = True
#      self.updateStatus("Swapped Red and Blue" \
#            if on else "Unswapped Red and Blue")
#
#
#   def editUnMirror(self, on):
#      if self.image.isNull():
#         return
#      if self.mirroredhorizontally:
#         self.editMirrorHorizontal(False)
#      if self.mirroredvertically:
#         self.editMirrorVertical(False)
#
#
#   def editMirrorHorizontal(self, on):
#      if self.image.isNull():
#         return
#      self.image = self.image.mirrored(True, False)
#      self.showImage()
#      self.mirroredhorizontally = not self.mirroredhorizontally
#      self.dirty = True
#      self.updateStatus("Mirrored Horizontally" \
#            if on else "Unmirrored Horizontally")
#
#
#   def editMirrorVertical(self, on):
#      if self.image.isNull():
#         return
#      self.image = self.image.mirrored(False, True)
#      self.showImage()
#      self.mirroredvertically = not self.mirroredvertically
#      self.dirty = True
#      self.updateStatus("Mirrored Vertically" \
#            if on else "Unmirrored Vertically")
#
#
#   def editZoom(self):
#      if self.image.isNull():
#         return
#      percent, ok = QInputDialog.getInteger(self,
#            "Image Changer - Zoom", "Percent:",
#            self.zoomSpinBox.value(), 1, 400)
#      if ok:
#         self.zoomSpinBox.setValue(percent)
#
#
#   def showImage(self, percent=None):
#      if self.image.isNull():
#         return
#      if percent is None:
#         percent = self.zoomSpinBox.value()
#      factor = percent / 100.0
#      width = self.image.width() * factor
#      height = self.image.height() * factor
#      image = self.image.scaled(width, height, Qt.KeepAspectRatio)
#      self.imageLabel.setPixmap(QPixmap.fromImage(image))
#
#
#   def helpAbout(self):
#      QMessageBox.about(self, "About Image Changer",
#            """<b>Image Changer</b> v %s
#            <p>Copyright &copy; 2007 Qtrac Ltd. 
#            All rights reserved.
#            <p>This application can be used to perform
#            simple image manipulations.
#            <p>Python %s - Qt %s - PyQt %s on %s""" % (
#            __version__, platform.python_version(),
#            QT_VERSION_STR, PYQT_VERSION_STR, platform.system()))
#
#
#   def helpHelp(self):
#      form = helpform.HelpForm("index.html", self)
#      form.show()

