from PyQt4.QtCore import *
from PyQt4.QtGui import *

from CppBlockUtils import AddressType_P2SH, AddressType_P2PKH
from armoryengine.ArmoryUtils import coin2str

COL_TREE = 0
COL_COMMENT = 1
COL_COUNT = 2
COL_BALANCE = 3

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

class TreeNode(object):
   
   def __init__(self, name, isExpendable=False, populateMethod=None):
      self.name = name
      self.isExpendable = isExpendable
      
      self.populateMethod = populateMethod
      self.populated = False if populateMethod is not None else True
      
      self.entries = []
      self.empty = False
            
   def getName(self):
      return self.name
            
   def rowCount(self):
      self.populate()
      if not self.empty:
         return len(self.entries)
      else:
         return 1
      
   def populate(self):
      if self.populated:
         return
      
      addrList = self.populateMethod()
      if len(addrList) > 0:
         for addr in addrList:
            self.entries.append(AddressObjectItem(addr))
      else:
         self.empty = True
         
      self.populated = True
      
   def hasEntries(self):
      return self.isExpendable
   
   def appendEntry(self, entry):
      self.entries.append(entry)
   
   def getEntryByIndex(self, index):
      self.populate()
      if not self.empty:
         return self.entries[index]
      else:
         return EmptyNode()
      
class TreeStructure_AddressDisplay():
   
   def __init__(self, wallet):
      self.wallet = wallet
      self.root = None
      
      self.setup()
      
   def setup(self):
      
      #create root node
      self.root = TreeNode("root", True, None)
      
      def createChildNode(name, filterStr):
         nodeMain = TreeNode(name, True, None)
         
         def walletFilterP2SH():
            return self.wallet.returnFilteredCppAddrList(filterStr, AddressType_P2SH)
         
         def walletFilterP2PKH():
            return self.wallet.returnFilteredCppAddrList(filterStr, AddressType_P2PKH)
            
         nodeP2SH = TreeNode("P2SH", True, walletFilterP2SH)
         nodeMain.appendEntry(nodeP2SH)
         
         nodeP2KH = TreeNode("P2PKH", True, walletFilterP2PKH)
         nodeMain.appendEntry(nodeP2KH)
         
         return nodeMain
      
      #create top 3 nodes
      nodeUsed   = createChildNode("Used Addresses", "Used")
      nodeChange = createChildNode("Change Addresses", "Change")
      nodeUnused = createChildNode("Unused Addresses", "Unused")
      
      self.root.appendEntry(nodeUsed)
      self.root.appendEntry(nodeChange)
      self.root.appendEntry(nodeUnused)

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
      
class AddressTreeModel(QAbstractItemModel):
   
   def __init__(self, main, wlt):
      super(AddressTreeModel, self).__init__()
      self.main = main
      self.wlt = wlt
      
      self.treeStruct = TreeStructure_AddressDisplay(self.wlt)
      self.root = NodeItem(0, None, self.treeStruct.root)
      
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
   
   def columnCount(self, index=QModelIndex()):
      return 4
         
   def data(self, index, role=Qt.DisplayRole):
      if role==Qt.DisplayRole:
         col = index.column()
         node = self.getNodeItem(index)  
                
         if col == COL_TREE:
            return QVariant(node.treeNode.getName())
         
         if node.hasChildren():
            return QVariant()
         
         if not node.treeNode.canDoubleClick():
            return QVariant()
         
         if col == COL_COMMENT:
            return QVariant(node.treeNode.getComment())
         
         if col == COL_COUNT:
            return QVariant(node.treeNode.getCount())
         
         if col == COL_BALANCE:
            return QVariant(coin2str(node.treeNode.getBalance(), maxZeros=2))
      
      return QVariant()
   
   def headerData(self, section, orientation, role=Qt.DisplayRole):
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==COL_TREE: return QVariant('Address')
            if section==COL_COMMENT: return QVariant('Comment')
            if section==COL_COUNT:  return QVariant('Tx Count')
            if section==COL_BALANCE:  return QVariant('Balance')

      return QVariant() 
   
   def getNodeItem(self, index):
      if not index.isValid():
         return self.root
      
      item = index.internalPointer()
      if item is None:
         return self.root
      
      return item