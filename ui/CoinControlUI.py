##############################################################################
#                                                                            #
# Copyright (C) 2016-17, goatpig                                             #
#  Distributed under the MIT license                                         #
#  See LICENSE-MIT or https://opensource.org/licenses/MIT                    #                                   
#                                                                            #
##############################################################################

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qtdefines import ArmoryDialog, QRichLabel, SIGNAL, \
   QCheckBox, QGridLayout, VLINE, HLINE, QFrame, makeHorizFrame, \
   QMoneyLabel, saveTableView, restoreTableView
   
from ui.TreeViewGUI import CoinControlTreeModel

################################################################################   
class CoinControlDlg(ArmoryDialog):
   
   #############################################################################
   def __init__(self, parent, main, wlt, currSelect=None):
      super(CoinControlDlg, self).__init__(parent, main)

      self.wlt = wlt

      lblDescr = QRichLabel(\
         'By default, transactions are created using any available coins from '
         'all addresses in this wallet.  You can control the source addresses '
         'used for this transaction by selecting them below, and unchecking '
         'all other addresses.')
            
      self.ccTreeModel = CoinControlTreeModel(self, wlt)
      self.ccView = QTreeView()
      self.ccView.setModel(self.ccTreeModel)
           
      lblDescrSum = QRichLabel('Balance of selected addresses:', doWrap=False)
      self.lblSum = QMoneyLabel(0, wBold=True)
      frmSum = makeHorizFrame(['Stretch', lblDescrSum, self.lblSum, 'Stretch'])
            
      self.btnAccept = QPushButton("Accept")
      self.btnCancel = QPushButton("Cancel")
      self.connect(self.btnAccept, SIGNAL('clicked()'), self.accept)
      self.connect(self.btnCancel, SIGNAL('clicked()'), self.reject)            
      buttonBox = QDialogButtonBox()
      buttonBox.addButton(self.btnAccept, QDialogButtonBox.AcceptRole)
      buttonBox.addButton(self.btnCancel, QDialogButtonBox.RejectRole)
      
      hexgeom  = self.main.settings.get('ccDlgGeometry')
      tblgeom  = self.main.settings.get('ccDlgAddrCols')

      if len(hexgeom) > 0:
         geom = QByteArray.fromHex(hexgeom)
         self.restoreGeometry(geom)
      if len(tblgeom) > 0:
         restoreTableView(self.ccView, tblgeom)
                  
      layout = QGridLayout()
      layout.addWidget(lblDescr, 0, 0)
      layout.addWidget(self.ccView, 1, 0)
      layout.addWidget(frmSum, 3, 0)
      layout.addWidget(buttonBox, 4, 0)
      self.setLayout(layout)
      
      self.setWindowTitle('Coin Control (Expert)')
   
    
   #############################################################################   
   def getCustomUtxoList(self):
      treeData = self.ccTreeModel.treeStruct.getTreeData()
      
      utxoList = []
      for section in treeData['UTXO']:
         sectionDict = treeData['UTXO'][section]
         
         for entry in sectionDict:
            addrList = sectionDict[entry]
            
            for utxo in addrList:
               if utxo.isChecked():
                  utxoList.append(utxo)
                  
      return utxoList

   #############################################################################
   def closeEvent(self, event):
      self.saveGeometrySettings()
      super(CoinControlDlg, self).closeEvent(event)
   
   #############################################################################
   def accept(self, *args):
      self.saveGeometrySettings()
      super(CoinControlDlg, self).accept(*args)
    
   #############################################################################   
   def resetTreeData(self):
      self.ccTreeModel.treeStruct.reset()
      self.ccTreeModel.reset()
            
   #############################################################################
   def reject(self, *args):
      self.saveGeometrySettings()  
      self.resetTreeData()  
      super(CoinControlDlg, self).reject(*args)
      
   #############################################################################
   def saveGeometrySettings(self):
      self.main.writeSetting('ccDlgGeometry', str(self.saveGeometry().toHex()))
      self.main.writeSetting('ccDlgAddrCols', saveTableView(self.ccView))  
   
   #############################################################################   
   def exec_(self):
      super(CoinControlDlg, self).exec_()