import os
import platform
import sys
from os import path
from PyQt4.QtCore import *
from PyQt4.QtGui import *
sys.path.append('..')
sys.path.append('../cppForSwig')
from pybtcengine import *
from CppBlockUtils import *


HEAD_BLKNUM, HEAD_HASH, HEAD_DIFF, HEAD_NUMTX, HEAD_BTC, HEAD_DATE = range(6)
TX_INDEX, TX_HASH, TX_BTC, TX_SRC, TX_RECIP, TX_SIZE = range(6)
TXIN_SRC, TXIN_BTC, TXIN_SBLK, TXIN_STYPE, TXIN_SEQ, = range(5)
TXOUT_RECIP, TXOUT_BTC, TXOUT_STYPE, = range(3)

headColLabels = {HEAD_BLKNUM: 'Block#', \
                 HEAD_HASH:   'Hash', \
                 HEAD_DIFF:   'Difficulty', \
                 HEAD_NUMTX:  '#Tx', \
                 HEAD_BTC:    'Total BTC', \
                 HEAD_DATE:   'Date & Time'}
txColLabels   = {TX_INDEX:    'Index', \
                 TX_HASH:     'Hash', \
                 TX_BTC:      'BTC', \
                 TX_SRC:      'Source', \
                 TX_RECIP:    'Recipient', \
                 TX_SIZE:     'Size' }
txinColLabels = {TXIN_SRC:    'Sender', \
                 TXIN_BTC:    'BTC', \
                 TXIN_SBLK:   'From#', \
                 TXIN_STYPE:  'Script Type'}
                 #TXIN_SEQ:    'Sequence'}
txoutColLabels ={TXOUT_RECIP: 'Recipient',\
                 TXOUT_BTC:   'BTC', \
                 TXOUT_STYPE: 'Script Type'}

b2h = lambda x: binary_to_hex(x)
h2b = lambda x: hex_to_binary(x)


class HeaderDataModel(QAbstractTableModel):

   def __init__(self):
      super(HeaderDataModel, self).__init__()
      self.bdm = BlockDataManager_FullRAM.GetInstance()
      self.headerData = []
      self.endianSelect = BIGENDIAN

   def rowCount(self, index=QModelIndex()):
      return self.bdm.getTopBlockHeader().getBlockHeight()+1

   def columnCount(self, index=QModelIndex()):
      return len(headColLabels)

   def sumBtcInHeader(self, header):
      txlist = header.getTxRefPtrList()
      total = 0
      for tx in txlist:
         total += tx.getSumOfOutputs()
      return total

   def data(self, index, role=Qt.DisplayRole):
      nHead = self.rowCount()
      row,col = index.row(), index.column()
      if not index.isValid() or not (0 <= row < nHead):
         return QVariant()

      if role==Qt.DisplayRole:
         h = nHead-row-1
         cppHeader = self.bdm.getHeaderByHeight(h)
         if cppHeader == None or not h>0:
            return QVariant()
         if col == HEAD_BLKNUM:
            return QVariant(cppHeader.getBlockHeight())
         elif col== HEAD_HASH:
            return QVariant(binary_to_hex(cppHeader.getThisHash(), self.endianSelect))
         elif col== HEAD_DIFF:
            return QVariant("%0.2f" % cppHeader.getDifficulty())
         elif col== HEAD_NUMTX:
            return QVariant("%d  " % cppHeader.getNumTx())
         elif col== HEAD_BTC:
            return QVariant("%0.4f" % float(self.sumBtcInHeader(cppHeader)/1e8))
         elif col== HEAD_DATE:
            return QVariant(unixTimeToFormatStr(cppHeader.getTimestamp()))
      elif role==Qt.TextAlignmentRole:
         if col in (HEAD_BLKNUM, HEAD_DIFF, HEAD_NUMTX, HEAD_BTC):
            return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
         else: 
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
      elif role==Qt.BackgroundColorRole:
         return QVariant( QColor(235,235,255) )
      return QVariant()

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      if role==Qt.TextAlignmentRole:
         return QVariant( int(Qt.AlignHCenter | Qt.AlignVCenter) )
      
      if role==Qt.DisplayRole:
         if self.endianSelect==BIGENDIAN:
            headColLabels[HEAD_HASH] = 'Hash (BE)'
         else:
            headColLabels[HEAD_HASH] = 'Hash (LE)'

         if orientation==Qt.Horizontal:
            return QVariant( headColLabels[section] )


   #def getInfoDict(self, header):
      
      


class TxDataModel(QAbstractTableModel):

   def __init__(self):
      super(TxDataModel, self).__init__()
      self.bdm = BlockDataManager_FullRAM.GetInstance()
      self.endianSelect = BIGENDIAN
      self.txHashList = None 

   def rowCount(self, index=QModelIndex()):
      if self.txHashList:
         return len(self.txHashList)
      return 0

   def columnCount(self, index=QModelIndex()):
      return len(txColLabels)

   def getTxSrcStr(self, txref):
      if txref.getNumTxIn() > 1:
         return '<%d sources>' % txref.getNumTxIn()
      else:
         txin = txref.getTxInRef(0)
         if txin.isCoinbase():
            return '<COINBASE>'
         else:
            return hash160_to_addrStr(self.bdm.getSenderAddr20(txin))

   def getTxDstStr(self, txref):
      if txref.getNumTxOut() > 1:
         return '<%d recipients>' % txref.getNumTxOut()
      else:
         return hash160_to_addrStr(txref.getTxOutRef(0).getRecipientAddr())

   def data(self, index, role=Qt.DisplayRole):
      nTx = self.rowCount()
      row,col = index.row(), index.column()
      if not index.isValid() or not (0 <= row < nTx):
         return QVariant()

      if role==Qt.DisplayRole:
         cppTx = self.bdm.getTxByHash(self.txHashList[row])
         if cppTx == None:
            return QVariant()
         if col == TX_INDEX:
            return QVariant('%d  ' % int(row+1))
         elif col== TX_HASH:
            return QVariant(binary_to_hex(cppTx.getThisHash(), self.endianSelect))
         elif col== TX_BTC:
            return QVariant("%0.4f" % float(cppTx.getSumOfOutputs()/1e8))
         elif col== TX_SRC:
            return QVariant(self.getTxSrcStr(cppTx))
         elif col== TX_RECIP:
            return QVariant(self.getTxDstStr(cppTx))
         elif col== TX_SIZE:
            return QVariant("%0.2f kB" % float(cppTx.getSize()/1024.))
      elif role==Qt.TextAlignmentRole:
         if col in (TX_INDEX, TX_BTC, TX_SIZE):
            return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
         else: 
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
      elif role==Qt.BackgroundColorRole:
         return QVariant( QColor(235,250,235) )
      return QVariant()

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      if role==Qt.TextAlignmentRole:
         return QVariant( int(Qt.AlignHCenter | Qt.AlignVCenter) )
      
      if role==Qt.DisplayRole:
         if self.endianSelect==BIGENDIAN:
            txColLabels[TX_HASH] = 'Hash (BE)'
         else:
            txColLabels[TX_HASH] = 'Hash (LE)'
         if orientation==Qt.Horizontal:
            return QVariant( txColLabels[section] )


class TxInDataModel(QAbstractTableModel):

   def __init__(self):
      super(TxInDataModel, self).__init__()
      self.bdm = BlockDataManager_FullRAM.GetInstance()
      self.endianSelect = BIGENDIAN
      self.txSelect = None 

   def rowCount(self, index=QModelIndex()):
      if self.txSelect:
         return self.txSelect.getNumTxIn()
      return 0

   def columnCount(self, index=QModelIndex()):
      return len(txinColLabels)

   def data(self, index, role=Qt.DisplayRole):
      nTxIn = self.rowCount()
      row,col = index.row(), index.column()
      if not index.isValid() or not (0<= row < nTxIn):
         return QVariant()

      if role==Qt.DisplayRole:
         cppTxIn = self.txSelect.getTxInRef(row)
         if cppTxIn == None:
            return QVariant()
         if col == TXIN_SRC:
            if cppTxIn.isCoinbase():
               return QVariant("COINBASE")
            addr20 = self.bdm.getSenderAddr20(cppTxIn)
            return QVariant(hash160_to_addrStr(addr20))
         elif col== TXIN_BTC:
            if cppTxIn.isCoinbase():
               return QVariant("%0.4f" % float(self.txSelect.getSumOfOutputs()/1e8))
            return QVariant("%0.4f" % float(self.bdm.getSentValue(cppTxIn)/1e8))
         elif col== TXIN_STYPE:
            if cppTxIn.isScriptStandard():
               return QVariant('Standard')
            elif cppTxIn.isScriptCoinbase():
               return QVariant('<ARBITRARY>')
            elif cppTxIn.isScriptSpendCB():
               return QVariant('SPEND-COINBASE')
            elif cppTxIn.isScriptUnknown():
               return QVariant('UNKNOWN')
         elif col== TXIN_SBLK:
            if cppTxIn.isCoinbase():
               return QVariant('GENERATION')
            tx = self.bdm.getPrevTxOut(cppTxIn).getParentTxPtr()
            return QVariant("%d" % tx.getBlockHeight())
         #elif col== TXIN_SEQ:
            #return QVariant(int_to_hex(cppTxIn.getSequence(), 4, BIGENDIAN))
      elif role==Qt.TextAlignmentRole:
         if col in (TXIN_STYPE, TXIN_SBLK):
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
         elif col in (TXIN_BTC,):
            return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
         else: 
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
      elif role==Qt.BackgroundColorRole:
         return QVariant( QColor(235,250,235) )
      return QVariant()

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      if role==Qt.TextAlignmentRole:
         return QVariant( int(Qt.AlignHCenter | Qt.AlignVCenter) )
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            return QVariant( txinColLabels[section] )


class TxOutDataModel(QAbstractTableModel):

   def __init__(self):
      super(TxOutDataModel, self).__init__()
      self.bdm = BlockDataManager_FullRAM.GetInstance()
      self.endianSelect = BIGENDIAN
      self.txSelect = None 

   def rowCount(self, index=QModelIndex()):
      if self.txSelect:
         return self.txSelect.getNumTxOut()
      return 0

   def columnCount(self, index=QModelIndex()):
      return len(txoutColLabels)

   def data(self, index, role=Qt.DisplayRole):
      nTxOut = self.rowCount()
      row,col = index.row(), index.column()
      if not index.isValid() or not (0 <= row < nTxOut):
         return QVariant()

      if role==Qt.DisplayRole:
         cppTxOut = self.txSelect.getTxOutRef(row)
         if cppTxOut == None:
            return QVariant()
         if col == TXOUT_RECIP:
            return QVariant(hash160_to_addrStr(cppTxOut.getRecipientAddr()))
         elif col== TXOUT_BTC:
            return QVariant("%0.4f" % float(cppTxOut.getValue()/1e8))
         elif col== TXOUT_STYPE:
            if cppTxOut.isScriptStandard():
               return QVariant('Standard')
            elif cppTxOut.isScriptCoinbase():
               return QVariant('COINBASE')
            elif cppTxOut.isScriptUnknown():
               return QVariant('UNKNOWN')
      elif role==Qt.TextAlignmentRole:
         if col in (TXOUT_STYPE,):
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
         else: 
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
      elif role==Qt.BackgroundColorRole:
         return QVariant( QColor(235,250,235) )
      return QVariant()
      

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      if role==Qt.TextAlignmentRole:
         return QVariant( int(Qt.AlignHCenter | Qt.AlignVCenter) )
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            return QVariant( txoutColLabels[section] )












