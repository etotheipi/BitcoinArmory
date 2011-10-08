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
from pbemodels import *


HEAD_BLKNUM, HEAD_HASH, HEAD_DIFF, HEAD_NUMTX, HEAD_DATE = range(5)
headColLabels = {HEAD_BLKNUM: 'Block#', \
                 HEAD_HASH:   'Hash', \
                 HEAD_DIFF:   'Difficulty', \
                 HEAD_NUMTX:  '#Tx', \
                 HEAD_DATE:   'Date & Time'}
b2h = lambda x: binary_to_hex(x)
h2b = lambda x: hex_to_binary(x)

blkfileRefreshInterval = 5 * 1000;  # 5s

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
      self.setMinimumSize(1000,750)

      ##########################################################################
      # Start setting up the model/view behaviors
      self.models = {}  # Will store all models in this dictionary

      self.models['Headers'] = HeaderDataModel()
      self.headView  = QTableView()
      self.headView.setModel(self.models['Headers'])
      self.headView.setSelectionBehavior(QTableView.SelectRows)
      self.headView.setSelectionMode(QTableView.SingleSelection)
      self.headView.setMinimumSize(800,200)
      self.headView.horizontalHeader().setStretchLastSection(True)
      self.headView.verticalHeader().setDefaultSectionSize(16)

      self.models['Tx'] = TxDataModel()
      self.txView = QTableView()
      self.txView.setModel(self.models['Tx'])
      self.txView.setSelectionBehavior(QTableView.SelectRows)
      self.txView.setSelectionMode(QTableView.SingleSelection)
      self.txView.setMinimumSize(800,200)
      self.txView.horizontalHeader().setStretchLastSection(True)
      self.txView.verticalHeader().setDefaultSectionSize(16)

      self.models['TxIns'] = TxInDataModel()
      self.txinView = QTableView()
      self.txinView.setModel(self.models['TxIns'])
      self.txinView.setSelectionBehavior(QTableView.SelectRows)
      self.txinView.setSelectionMode(QTableView.SingleSelection)
      self.txinView.setMinimumSize(550,150)
      self.txinView.horizontalHeader().setStretchLastSection(True)
      self.txinView.verticalHeader().setDefaultSectionSize(16)

      self.models['TxOuts'] = TxOutDataModel()
      self.txoutView = QTableView()
      self.txoutView.setModel(self.models['TxOuts'])
      self.txoutView.setSelectionBehavior(QTableView.SelectRows)
      self.txoutView.setSelectionMode(QTableView.SingleSelection)
      self.txoutView.setMinimumSize(550,150)
      self.txoutView.horizontalHeader().setStretchLastSection(True)
      self.txoutView.verticalHeader().setDefaultSectionSize(16)

      #self.connect(self.headView,   SIGNAL('cellClicked(int,int)'), self.headerClicked)
      self.connect(self.headView,   SIGNAL("clicked(QModelIndex)"), self.headerClicked)
      self.connect(self.txView,     SIGNAL("clicked(QModelIndex)"), self.txClicked)
      self.connect(self.txinView,   SIGNAL("clicked(QModelIndex)"), self.txInClicked)
      self.connect(self.txoutView,  SIGNAL("clicked(QModelIndex)"), self.txOutClicked)

      self.connect(self.headView,   SIGNAL("itemSelectionChanged(QModelIndex,QModelIndex)"), self.headerClicked)

      self.connect(self.headView,   SIGNAL("doubleClicked(QModelIndex)"), self.headerDblClicked)
      self.connect(self.txView,     SIGNAL("doubleClicked(QModelIndex)"), self.txDblClicked)
      self.connect(self.txinView,   SIGNAL("doubleClicked(QModelIndex)"), self.txInDblClicked)
      self.connect(self.txoutView,  SIGNAL("doubleClicked(QModelIndex)"), self.txOutDblClicked)

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

      self.connect(self.edtSearch, SIGNAL('returnPressed()'), self.doSearch)
      self.connect(self.btnSearch, SIGNAL('pressed()'),       self.doSearch)
      
      # Set Endianness preferences
      self.gbxEndian = QGroupBox()
      self.gbxEndian.setCheckable(False)
      self.gbxEndian.setTitle(QString('Display Hashes (not implemented)'))
      
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
      self.connect(self.gbxEndian, SIGNAL('clicked()'), self.changeEndian)
      self.gbxEndian.setSizePolicy(QSizePolicy(QSizePolicy.Fixed))

      # Set area to display selected object properties
      self.txtSelectedInfo = QLabel()
      self.txtSelectedInfo.setWordWrap(True)
      self.txtSelectedInfo.setMinimumSize(200,75)
      self.txtSelectedInfo.setSizePolicy(QSizePolicy(QSizePolicy.Fixed))

      #addrHeadRow = ['Address (Base58)', 'Address (20 byte hex)', 'BTC Sent', 'Btc Rcvd']
      #self.tblAddrs = self.createTableWidget(addrHeadRow, (300,200))
   
      #self.connect(self.addrView,   SIGNAL("itemSelectionChange()"), self.addrClicked)

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
      # can control some features of the layout
      self.ctrLayout.setSpacing(10)
      self.ctrLayout.setMargin(10)
      #                                             Row  Col nRows nCols
      self.ctrLayout.addWidget(self.lblSearch,        1,   0,   1,   1)
      self.ctrLayout.addWidget(self.edtSearch,        1,   1,   1,   2)
      self.ctrLayout.addWidget(self.btnSearch,        1,   3,   1,   1)

      self.ctrLayout.addWidget(lblHeaders,            2,   0,   1,   1)
      self.ctrLayout.addWidget(lblTxs,                5,   0,   1,   1)
      self.ctrLayout.addWidget(lblTxIns,              9,   0,   1,   1)
      self.ctrLayout.addWidget(lblTxOuts,             9,   2,   1,   1)

      self.ctrLayout.addWidget(self.headView,         3,   0,   2,   4)
      self.ctrLayout.addWidget(self.txView,           6,   0,   3,   4)
      self.ctrLayout.addWidget(self.txinView,        10,   0,   2,   2)
      self.ctrLayout.addWidget(self.txoutView,       10,   2,   2,   2)

      self.ctrLayout.addWidget(self.gbxEndian,       12,   0,   1,   2)
      self.ctrLayout.addWidget(self.txtSelectedInfo, 12,   2,   1,   2)

      # Finally set the layout
      self.ctrFrame.setLayout(self.ctrLayout)
      self.setCentralWidget(self.ctrFrame)

      self.updateTimer = QTimer()
      self.connect(self.updateTimer, SIGNAL("timeout()"), self.readNewBlockData)

      # Prepare the BlockDataManager for 
      print 'GUI is setup, now load the blockchain'
      #self.bdm = BlockDataManager_FullRAM.GetInstance()
      self.bdm = BlockDataManager().getBDM()
      self.setWindowTitle('PyBtcEngine BlockExplorer')
      QTimer.singleShot(500, self.initBlockchain)


   def initBlockchain(self):
      if not self.blkFile==None:
         self.bdm.readBlkFile_FromScratch(self.blkFile) 
         self.bdm.organizeChain()
         self.bcLoadDoneYet = True
         self.btnSearch.setEnabled(True)
         self.edtSearch.setEnabled(True)
         self.edtSearch.setText('');
         self.edtSearch.setFocus()
         self.models['Headers'].reset()
         self.headView.resizeColumnsToContents()
         self.headView.setCurrentIndex( self.models['Headers'].index(0,0))
         self.headerClicked()

         # TODO: updating disabled due to problem with addBlockData() method
         self.updateTimer.start(blkfileRefreshInterval)
         self.prevSearchStr = ''

         self.txView.horizontalHeader().resizeSection(TX_HASH, 250)
         print 'Done!'

   #############################################################################
   def changeEndian(self):
      print 'Chaging endian!'
      currEnd = ''
      if self.rdoEndianD.isChecked():
         currEnd = 'Default'
      if self.rdoEndianL.isChecked():
         currEnd = LITTLEENDIAN
      if self.rdoEndianL.isChecked():
         currEnd = BIGENDIAN
      for m in self.models.itervalues():
         m.endianSelect = currEnd
         m.reset()
      

   #############################################################################
   def readNewBlockData(self):
      #print 'Checking for new blocks in block file...',
      numNewBlk = self.bdm.readBlkFileUpdate();
      #print numNewBlk, 'found!'

   #############################################################################
   def getSelectedHeader(self):
      if self.models['Headers'].rowCount() < 1:
         return (None, None)
      row = self.headView.currentIndex().row()
      col = self.headView.currentIndex().column()
      hidx = self.models['Headers'].index(row, HEAD_BLKNUM)
      blknum = self.models['Headers'].data(hidx).toInt()[0]
      return (self.bdm.getHeaderByHeight(blknum), col)
      
   #############################################################################
   def getSelectedTx(self):
      if self.models['Tx'].rowCount() < 1:
         return (None, None)
      row = self.txView.currentIndex().row()
      col = self.txView.currentIndex().column()
      tidx = self.models['Tx'].index(row, TX_HASH)
      txhash = hex_to_binary(str(self.models['Tx'].data(tidx).toString()))
      tx = self.bdm.getTxByHash(txhash)
      if tx == None:
         tx = self.bdm.getTxByHash( binary_switchEndian(txhash))
      if tx == None or len(txhash) < 1:
         return (None, None)
      return (tx, col)

   #############################################################################
   def resizeTxCols(self):
      for col in (TX_INDEX, TX_BTC, TX_SRC, TX_RECIP, TX_SIZE):
         self.txView.resizeColumnToContents(col)   
      
   #############################################################################
   def getSelectedTxIn(self):
      if self.models['TxIns'].rowCount() < 1:
         return (None, None)
      row = self.txinView.currentIndex().row()
      col = self.txinView.currentIndex().column()
      txin = self.getSelectedTx()[0].getTxInRef(row)
      return (txin, col)

   #############################################################################
   def getSelectedTxOut(self):
      if self.models['TxOuts'].rowCount() < 1:
         return (None,None)
      row = self.txoutView.currentIndex().row()
      col = self.txoutView.currentIndex().column()
      txout = self.getSelectedTx()[0].getTxOutRef(row)
      return (txout, col)

   #############################################################################
   # When the header changes, everything else does
   def headerClicked(self, r=-1, c=-1):
      head,col = self.getSelectedHeader()
      if head==None:
         return
      # We can't use getTxHashList yet because of a typemap problem 
      txptrs = head.getTxRefPtrList()
      self.models['Tx'].txHashList = [tx.getThisHash() for tx in txptrs]
      self.models['Tx'].reset()
      self.txView.setCurrentIndex( self.models['Tx'].index(0,0) )
      self.resizeTxCols()
      self.txView.horizontalHeader().setStretchLastSection(True)
      self.txClicked(0,0)
      
   #############################################################################
   # When the tx changes, gotta update TxIn and TxOut views, too
   def txClicked(self, r=-1, c=-1):
      tx,col = self.getSelectedTx()
      if tx==None:
         return

      self.models['TxIns'].txSelect = tx
      self.models['TxIns'].reset()
      self.txinView.resizeColumnsToContents()

      self.models['TxOuts'].txSelect = tx
      self.models['TxOuts'].reset()
      self.txoutView.resizeColumnsToContents()
      

   def txInClicked(self, r=-1, c=-1):
      txin,col = self.getSelectedTxIn()
      if txin==None:
         return

      oplist = ['TxIn Script:\n']
      oplist.extend( convertScriptToOpStrings(txin.getScript()))
      oplist = [op if len(op)<=50 else op[:47]+'...' for op in oplist]
      self.txtSelectedInfo.setText('\n'.join(oplist))

   def txOutClicked(self, r=-1, c=-1):
      txout,col = self.getSelectedTxOut()
   
      oplist = ['TxOut Script:\n']
      oplist.extend(convertScriptToOpStrings(txout.getScript()))
      oplist = [op if len(op)<=50 else op[:47]+'...' for op in oplist]
      self.txtSelectedInfo.setText('\n'.join(oplist))

   def addrClicked(self, r, c):
      pass

   #############################################################################
   # When the header changes, everything else does
   def headerDblClicked(self, r=-1, c=-1):
      head,col = self.getSelectedHeader()
      if head==None:
         return
      # We can't use getTxHashList yet because of a typemap problem 
      
   #############################################################################
   # When the tx changes, gotta update TxIn and TxOut views, too
   def txDblClicked(self, r=-1, c=-1):
      tx,col = self.getSelectedTx()
      if tx==None:
         return

      self.models['TxIns'].txSelect = tx
      self.models['TxIns'].reset()
      self.txinView.resizeColumnsToContents()

      self.models['TxOuts'].txSelect = tx
      self.models['TxOuts'].reset()
      self.txoutView.resizeColumnsToContents()
      

   def txInDblClicked(self, r=-1, c=-1):
      txin,col = self.getSelectedTxIn()
      if txin==None:
         return

      oplist = ['TxIn Script:\n']
      oplist.extend( convertScriptToOpStrings(txin.getScript()))
      oplist = [op if len(op)<=50 else op[:47]+'...' for op in oplist]
      self.txtSelectedInfo.setText('\n'.join(oplist))

   def txOutDblClicked(self, r=-1, c=-1):
      txout,col = self.getSelectedTxOut()
   
      oplist = ['TxOut Script:\n']
      oplist.extend(convertScriptToOpStrings(txout.getScript()))
      oplist = [op if len(op)<=50 else op[:47]+'...' for op in oplist]
      self.txtSelectedInfo.setText('\n'.join(oplist))

   def addrClicked(self, r, c):
      pass

      

   #############################################################################
   def doSearch(self):
      if self.bcLoadDoneYet == False:
         QMessageBox.warning(self, 'Blockchain Manager Still Loading', \
                     unicode('Blockchain is not done loading.  Please wait!'))
         return
      else:
         searchStr = str(self.edtSearch.text()).strip()
         if searchStr=='':
            return 

         if not searchStr==self.prevSearchStr:
            self.searchResults = []
            try:
               self.searchResults = [(int(searchStr),0)]
            except(ValueError):
               # Thus must be a hex hash
               sstr1 = hex_to_binary(searchStr)
               sstr2 = hex_to_binary(hex_switchEndian(searchStr))
   
               # Search headers
               srch1 = self.bdm.prefixSearchHeaders(sstr1) 
               print srch1
               srch2 = self.bdm.prefixSearchHeaders(sstr2) 
               print srch2
               for resultSet in (srch1, srch2):
                  for header in resultSet:
                     blkNum = header.getBlockHeight()
                     self.searchResults.append( (blkNum,  0) )
            
               # Search Tx
               srch1 = self.bdm.prefixSearchTx(sstr1) 
               print srch1
               srch2 = self.bdm.prefixSearchTx(sstr2) 
               print srch2
               for resultSet in (srch1, srch2):
                  for tx in resultSet:
                     blkNum  = tx.getBlockHeight()
                     txindex = tx.getBlockTxIndex()
                     self.searchResults.append( (blkNum, txindex) )
   
            
         if len(self.searchResults) == 0:
            print 'No search results!'
            return

         currHeight  = self.getSelectedHeader()[0].getBlockHeight()
         currTxIndex = -1
         tx = self.getSelectedTx()
         if tx[0]:
            currTxIndex = tx[0].getBlockTxIndex()
         newHeight, newTxIndex = 0,0
         foundNext = False
         for blk,txidx in self.searchResults:
            if blk < currHeight or (blk==currHeight and txidx>currTxIndex):
               row = self.models['Headers'].rowCount() - blk - 1
               self.headView.setCurrentIndex( self.models['Headers'].index(row,0))
               self.txView.setCurrentIndex( self.models['Tx'].index(txidx,0))
               foundNext = True
         if not foundNext:
            # wrap around
            row = self.models['Headers'].rowCount() - self.searchResults[0][0] - 1
            txidx = self.searchResults[0][1]
            self.headView.setCurrentIndex( self.models['Headers'].index(row,0))
            self.headerClicked()
            self.txView.setCurrentIndex( self.models['Tx'].index(txidx,0))
            self.txClicked()
         self.prevSearchStr = searchStr
   
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

