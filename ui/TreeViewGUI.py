##############################################################################
#                                                                            #
# Copyright (C) 2016-17, goatpig                                             #
#  Distributed under the MIT license                                         #
#  See LICENSE-MIT or https://opensource.org/licenses/MIT                    #                                   
#                                                                            #
##############################################################################

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from CppBlockUtils import AddressType_P2SH_P2PK, \
   AddressType_P2SH_P2WPKH, AddressType_P2PKH
from armoryengine.ArmoryUtils import coin2str, hash160_to_addrStr

from qtdefines import GETFONT
from armorycolors import Colors

COL_TREE = 0
COL_COMMENT = 1
COL_COUNT = 2
COL_BALANCE = 3

COL_NAME = 0
COL_VALUE = 2

################################################################################
class AddressObjectItem(object):
   
   def __init__(self, addrObj):
      self.addrObj = addrObj
      
   def rowCount(self):
      return 0
   
   def hasEntries(self):
      return False
   
   def getName(self):
      return self.addrObj.getScrAddr()
   
   def getCount(self):
      return self.addrObj.getTxioCount()
   
   def getBalance(self):
      return self.addrObj.getFullBalance()
   
   def getComment(self):
      return self.addrObj.getComment()
   
   def getAddrObj(self):
      return self.addrObj
   
   def canDoubleClick(self):
      return True
 
################################################################################   
class CoinControlUtxoItem():
   
   def __init__(self, parent, utxo):
      self.utxo = utxo
      self.parent = parent
      self.name = self.tr("Block: #%1 | Tx: #%2 | TxOut: #%3").arg(utxo.getTxHeight(),
         utxo.getTxIndex(), utxo.getTxOutIndex())
         
      
      self.state = Qt.Checked
      if utxo.isChecked() == False:
         self.state = Qt.Unchecked
      
   def rowCount(self):
      return 0
   
   def hasEntries(self):
      return False
   
   def getName(self):
      return self.name
   
   def getBalance(self):
      return self.utxo.getValue()

   def getComment(self):
      return ""
   
   def checked(self):
      return self.state
   
   def setCheckState(self, val):
      self.checkDown(val)
      
      if self.parent is not None:
         self.parent.checkUp()
      
   def checkDown(self, val):
      self.state = val
      
      if val == Qt.Checked:
         self.utxo.setChecked(True)
      else:
         self.utxo.setChecked(False)
      
         
################################################################################
class EmptyNode(object):
   
   def __init__(self):
      self.name = "None"
      
   def rowCount(self):
      return 0
   
   def hasEntries(self):
      return False
   
   def getName(self):
      return self.name
   
   def canDoubleClick(self):
      return False
   
   def getComment(self):
      return ""
   
################################################################################
class TreeNode(object):
   
   def __init__(self, parent, name, isExpendable=False):
      self.name = name
      self.isExpendable = isExpendable
      self.parent = parent
      
      self.populated = False
      
      self.entries = []
      self.empty = False
      self.checkStatus = self.computeState()
                        
   def rowCount(self):
      self.populate()
      if not self.empty:
         return len(self.entries)
      else:
         return 1
      
   def hasEntries(self):
      return self.isExpendable
   
   def appendEntry(self, entry):
      self.entries.append(entry)
      self.populated = True
   
   def getEntryByIndex(self, index):
      self.populate()
      if not self.empty:
         return self.entries[index]
      else:
         return EmptyNode()
      
   def checked(self):
      return self.checkStatus
   
   def checkDown(self, val):
      #set own state
      self.checkStatus = val
      
      #set children
      self.populate()
      for entry in self.entries:
         entry.checkDown(val)
         
   def checkUp(self):
      #figure out own state
      self.checkStatus = self.computeState()
      
      #checkUp on parent
      if self.parent is not None:
         self.parent.checkUp()
   
   def setCheckState(self, val):
      self.checkDown(val)
         
      if self.parent is not None:
         self.parent.checkUp()
         
   def computeState(self):
      if not self.hasEntries():
         raise "node needs children to compute state"
      
      self.populate()
      state = Qt.Checked
      try:
         state = self.entries[0].checked()
         for i in range(1, len(self.entries)):
            if self.entries[i].checked() != state:
               state = Qt.PartiallyChecked
               break
      except:
         pass
         
      return state
   
   def getName(self):
      return self.name
         
   
################################################################################  
class CoinControlAddressItem(TreeNode):
   
   def __init__(self, parent, name, utxoList):
      self.utxoList = utxoList
      super(CoinControlAddressItem, self).__init__(parent, name, True)

      self.balance = 0
      for utxo in utxoList:
         self.balance += utxo.getValue()
      
   def rowCount(self):
      return len(self.utxoList);
   
   def populate(self):
      if self.populated == True:
         return
      
      self.entries = []
      for utxo in self.utxoList:
         self.entries.append(CoinControlUtxoItem(self, utxo))
         
      self.populated = True
      
   def getBalance(self):
      return self.balance
   
   def getComment(self):
      return ""
         
################################################################################
class AddressTreeNode(TreeNode):
   
   def __init__(self, name, isExpendable=False, populateMethod=None):
      self.populateMethod = populateMethod       
      super(AddressTreeNode, self).__init__(None, name, isExpendable)
            
   def populate(self):
      if self.populated:
         return
      
      if self.populateMethod == None:
         return
      
      addrList = self.populateMethod()
      if len(addrList) > 0:
         for addr in addrList:
            self.entries.append(AddressObjectItem(addr))
      else:
         self.empty = True
         
      self.populated = True
      
   def getBalance(self):
      self.populate()
      
      balance = 0
      for entry in self.entries:
         balance += entry.getBalance()
         
      return balance
      
################################################################################
class CoinControlTreeNode(TreeNode):
   
   def __init__(self, parent, name, isExpendable=False, populateMethod=None):
      self.populateMethod = populateMethod      
      super(CoinControlTreeNode, self).__init__(parent, name, isExpendable)
      
   def getName(self):
      return self.name
            
   def populate(self):
      if self.populated:
         return
      
      if self.populateMethod == None:
         return
      
      utxoList = self.populateMethod()
      if len(utxoList) > 0:
         for addr in utxoList:
            self.entries.append(\
               CoinControlAddressItem(self, addr, utxoList[addr]))
      else:
         self.empty = True
         
      self.populated = True
      
   def getBalance(self):
      self.populate()
      
      balance = 0
      for entry in self.entries:
         if entry.checked() != Qt.Unchecked:
            balance += entry.getBalance()
         
      return balance
 
################################################################################     
class TreeStructure_AddressDisplay():
   
   def __init__(self, wallet, parent_qobj):
      self.wallet = wallet
      self.root = None
      self.parent_qobj = parent_qobj
      
      self.setup()
      
   def setup(self):     
      #create root node
      self.root = AddressTreeNode("root", True, None)
      
      def createChildNode(name, filterStr):
         nodeMain = AddressTreeNode(name, True, None)
         
         def walletFilterP2SH_P2PK():
            return self.wallet.returnFilteredCppAddrList(\
                     filterStr, AddressType_P2SH_P2PK)
         
         def walletFilterP2SH_P2WPKH():
            return self.wallet.returnFilteredCppAddrList(\
                     filterStr, AddressType_P2SH_P2WPKH)
         
         def walletFilterP2PKH():
            return self.wallet.returnFilteredCppAddrList(\
                     filterStr, AddressType_P2PKH)

         nodeUnspent = AddressTreeNode("P2PKH", True, walletFilterP2PKH)
         nodeMain.appendEntry(nodeUnspent)
         
         nodeRBF = AddressTreeNode("P2SH-P2PK", True, walletFilterP2SH_P2PK)
         nodeMain.appendEntry(nodeRBF)
         
         nodeCPFP = AddressTreeNode("P2SH-P2WPKH", True, walletFilterP2SH_P2WPKH)
         nodeMain.appendEntry(nodeCPFP)
                   
         return nodeMain
      
      #create top 3 nodes
      nodeUsed   = createChildNode(self.parent_qobj.tr("Used Addresses"), "Used")
      nodeChange = createChildNode(self.parent_qobj.tr("Change Addresses"), "Change")
      nodeUnused = createChildNode(self.parent_qobj.tr("Unused Addresses"), "Unused")
      
      self.root.appendEntry(nodeUsed)
      self.root.appendEntry(nodeChange)
      self.root.appendEntry(nodeUnused)
      
      #if we have imports, add an import section
      if not self.wallet.hasImports():
         return
            
      nodeImports = AddressTreeNode(
         'Imports', True, \
         self.wallet.getImportCppAddrList)
      
      self.root.appendEntry(nodeImports)
      
################################################################################
class TreeStructure_CoinControl():
   
   def __init__(self, wallet):
      self.wallet = wallet
      self.root = None
      
      self.setup()
      
   def getTreeData(self):
      return self.treeData
   
   def reset(self):
      for section in self.treeData['UTXO']:
         addrDict = self.treeData['UTXO'][section]
         
         for addr in addrDict:
            utxoList = addrDict[addr]
            
            for utxo in utxoList:
               utxo.setChecked(True)
      
   def setup(self):
      #load utxos
      utxoList = self.wallet.getFullUTXOList()
      
      self.treeData = {
         'UTXO':{
            'p2pkh':dict(),
            'p2sh_p2pk':dict(),
            'p2sh_p2wpkh':dict()},
         'RBF':dict(),
         'CPFP':dict()
         }
            
      #filter utxos
      for utxo in utxoList:
         h160 = utxo.getRecipientHash160()
         binAddr = utxo.getRecipientScrAddr()
         scrAddr = hash160_to_addrStr(h160, binAddr[0])
            
         assetId = self.wallet.cppWallet.getAssetIndexForAddr(h160)
         addrType = self.wallet.cppWallet.getAddrTypeForIndex(assetId) 
                 
         addrDict = None
         if addrType == AddressType_P2PKH:
            addrDict = self.treeData['UTXO']['p2pkh']
         elif addrType == AddressType_P2SH_P2PK:
            addrDict = self.treeData['UTXO']['p2sh_p2pk']
         elif addrType == AddressType_P2SH_P2WPKH:
            addrDict = self.treeData['UTXO']['p2sh_p2wpkh']
            
         if addrDict == None:
            continue
         
         if not scrAddr in addrDict:
            addrDict[scrAddr] = []
            
         addrDict[scrAddr].append(utxo)
            
                
      #create root node
      self.root = CoinControlTreeNode(None, "root", True, None)
      
      def createChildNode(name, filterStr):
         nodeMain = CoinControlTreeNode(None, name, True, None)
         
         if name != "Unspent Outputs":
            return nodeMain
         
         def ccFilterP2PKH():
            return self.treeData['UTXO']['p2pkh']
         
         def ccFilterP2SH_P2PK():
            return self.treeData['UTXO']['p2sh_p2pk']
         
         def ccFilterP2SH_P2WPKH():
            return self.treeData['UTXO']['p2sh_p2wpkh']
      
         
         nodeP2KH = CoinControlTreeNode(nodeMain, "P2PKH", True, ccFilterP2PKH)
         nodeMain.appendEntry(nodeP2KH)
         
         nodeP2SH_P2PK = CoinControlTreeNode(nodeMain, "P2SH-P2PK", True, ccFilterP2SH_P2PK)
         nodeMain.appendEntry(nodeP2SH_P2PK)
         
         nodeP2SH_P2WPKH = CoinControlTreeNode(nodeMain, "P2SH-P2WPKH", True, ccFilterP2SH_P2WPKH)
         nodeMain.appendEntry(nodeP2SH_P2WPKH)
         
         return nodeMain
      
      #create top 3 nodes
      nodeUTXO   = createChildNode(self.tr("Unspent Outputs"), "Unspent")
      nodeRBF = createChildNode(self.tr("RBF Eligible"), "RBF")
      nodeCPFP = createChildNode(self.tr("CPFP Outputs"), "CPFP")
      
      self.root.appendEntry(nodeUTXO)
      self.root.appendEntry(nodeRBF)
      self.root.appendEntry(nodeCPFP)
      
            
      self.root.checkStatus = self.root.computeState()

################################################################################
class NodeItem(object):
   
   def __init__(self, row, parent, treeNode):
      self.parent = parent
      self.row = row
      self.treeNode = treeNode
      
      self.children = {}      
      
      if parent != None:
         self.depth = parent.depth + 1 
         parent.addChild(self)      
      else:
         self.depth = 0 
            
   def addChild(self, child):
      self.children[child.row] = child
      
   def hasChildren(self):
      return self.treeNode.hasEntries()
      
   def getChildAtRow(self, row):
      try:
         node = self.children[row]
      except:
         node = NodeItem(row, self, self.treeNode.getEntryByIndex(row))
         
      return node
   
   def rowCount(self):
      return self.treeNode.rowCount()
   
   def canDoubleClick(self):
      try:
         return self.treeNode.canDoubleClick()
      except:
         return False

################################################################################      
class ArmoryTreeModel(QAbstractItemModel):
   
   def __init__(self, main):
      super(ArmoryTreeModel, self).__init__()
      self.main = main
      
   def parent(self, index):
      if not index.isValid():
         return QModelIndex()
      
      node = self.getNodeItem(index)
      if node is None:
         return QModelIndex()
      
      parent = node.parent
      if parent is None:
         return QModelIndex()
      
      return self.createIndex(parent.row, 0, parent)
      
   def index(self, row, column, parent):
      parentNode = self.getNodeItem(parent)
      return self.createIndex(row, column, parentNode.getChildAtRow(row))
        
   def hasChildren(self, parent):
      node = self.getNodeItem(parent)
      return node.hasChildren()
   
   def rowCount(self, index):
      node = self.getNodeItem(index)
      return node.rowCount()
   
   def getNodeItem(self, index):
      if index == None:
         return self.root
      
      if not index.isValid():
         return self.root
      
      item = index.internalPointer()
      if item is None:
         return self.root
      
      return item
   
################################################################################   
class AddressTreeModel(ArmoryTreeModel):
   def __init__(self, main, wlt):
      super(AddressTreeModel, self).__init__(main)

      self.wlt = wlt
      
      self.treeStruct = TreeStructure_AddressDisplay(self.wlt, self)
      self.root = NodeItem(0, None, self.treeStruct.root)
      
   def columnCount(self, index=QModelIndex()):
      return 4      
   
   def data(self, index, role=Qt.DisplayRole):
      if role==Qt.DisplayRole:
         col = index.column()
         node = self.getNodeItem(index)  
                
         if col == COL_TREE:
            return QVariant(node.treeNode.getName())
         
         if col == COL_BALANCE:
            try:
               return QVariant(coin2str(node.treeNode.getBalance(), maxZeros=2))
            except:
               return QVariant()          
         
         if node.hasChildren():
            return QVariant()
         
         if not node.treeNode.canDoubleClick():
            return QVariant()
         
         if col == COL_COMMENT:
            return QVariant(node.treeNode.getComment())
         
         if col == COL_COUNT:
            return QVariant(node.treeNode.getCount())
         

      
      return QVariant()
   
   def headerData(self, section, orientation, role=Qt.DisplayRole):
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==COL_TREE: return QVariant(self.tr('Address'))
            if section==COL_COMMENT: return QVariant(self.tr('Comment'))
            if section==COL_COUNT:  return QVariant(self.tr('Tx Count'))
            if section==COL_BALANCE:  return QVariant(self.tr('Balance'))

      return QVariant() 
  
################################################################################ 
class CoinControlTreeModel(ArmoryTreeModel):
   def __init__(self, main, wlt):
      super(CoinControlTreeModel, self).__init__(main)

      self.wlt = wlt
      
      self.treeStruct = TreeStructure_CoinControl(self.wlt)
      self.root = NodeItem(0, None, self.treeStruct.root)
      
   def columnCount(self, index=QModelIndex()):
      return 3   
      
   def data(self, index, role=Qt.DisplayRole):
      col = index.column()    
      node = self.getNodeItem(index)
        
      if role==Qt.DisplayRole:            
         if col == COL_NAME:
            return QVariant(node.treeNode.getName())
                  
         if col == COL_COMMENT:
            try:
               return QVariant(node.treeNode.getComment())
            except:
               pass
                  
         if col == COL_VALUE:
            try:
               return QVariant(coin2str(node.treeNode.getBalance(), maxZeros=2))
            except:
               pass
      
      elif role==Qt.CheckStateRole:
         try:
            if col == COL_NAME:          
               st = node.treeNode.checked()
               return st
            else: 
               return QVariant()
         except:
            pass

      elif role==Qt.BackgroundRole:
         try:
            if node.treeNode.checked() != Qt.Unchecked:
               return QVariant(Colors.SlightBlue)
         except:
            pass
           
      elif role==Qt.FontRole:
         try:
            if node.treeNode.checked() != Qt.Unchecked:
               return GETFONT('Fixed', bold=True)
         except:
            pass

      return QVariant()
   
   def headerData(self, section, orientation, role=Qt.DisplayRole):
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==COL_NAME: return QVariant(self.tr('Address/ID'))
            if section==COL_COMMENT:  return QVariant(self.tr('Comment'))
            if section==COL_VALUE:  return QVariant(self.tr('Balance'))

      return QVariant() 
   
   def flags(self, index):
      f = Qt.ItemIsEnabled
      if index.column() == 0:
         node = self.getNodeItem(index)
         if node.treeNode.getName() != 'None':
            f |= Qt.ItemIsUserCheckable
      return f
            
   def setData(self, index, value, role):
      if role == Qt.CheckStateRole:
         node = self.getNodeItem(index)
         node.treeNode.setCheckState(value)
            
         self.emit(SIGNAL('layoutChanged()'))
         return True
      
      return False
