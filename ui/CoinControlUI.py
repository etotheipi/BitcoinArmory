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

      lblDescr = QRichLabel(self.tr(
         'By default, transactions are created using any available coins from '
         'all addresses in this wallet.  You can control the source addresses '
         'used for this transaction by selecting them below, and unchecking '
         'all other addresses.'))
      
      self.useAllCheckBox = QCheckBox(self.tr("Use all selected UTXOs"))
      useAllToolTip = self.main.createToolTipWidget(self.tr('''
      By default, Armory will pick a a subset of the UTXOs you pick 
      explicitly through the coin control feature to best suit the
      total spend value of the transaction you are constructing.
      
      <br><br>
      Checking 'Use all selected UTXOs' forces the construction of a
      transaction that will redeem the exact list of UTXOs you picked 
      instead 
      '''))
      
      frmCheckAll = makeHorizFrame([self.useAllCheckBox, useAllToolTip, 'Stretch'])
            
      self.ccTreeModel = CoinControlTreeModel(self, wlt)
      self.ccView = QTreeView()
      self.ccView.setModel(self.ccTreeModel)
           
      self.btnAccept = QPushButton(self.tr("Accept"))
      self.btnCancel = QPushButton(self.tr("Cancel"))
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
      layout.addWidget(frmCheckAll, 1, 0)
      layout.addWidget(self.ccView, 2, 0)
      layout.addWidget(buttonBox, 5, 0)
      self.setLayout(layout)
      
      self.setWindowTitle(self.tr('Coin Control (Expert)'))
   
    
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
   def isUseAllChecked(self):
      return self.useAllCheckBox.isChecked()

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
