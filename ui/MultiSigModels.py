from os import path
import platform
import sys
from armoryengine.ALL import *
from qtdefines import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *


LOCKBOXCOLS = enum('ID', 'MSType', 'CreateDate', 'LBName', \
                   'Key0', 'Key1', 'Key2', 'Key3', 'Key4', \
                   'NumTx', 'Balance', 'UnixTime')


class LockboxDisplayModel(QAbstractTableModel):

   def __init__(self, main, allLockboxes, dateFormat=DEFAULT_DATE_FORMAT):
      super(LockboxDisplayModel, self).__init__()
      self.boxList = allLockboxes
      self.dateFmt = dateFormat
      self.main = main



   def recomputeMaxKeys(self):
      self.maxN = max([lbox.N for lbox in self.boxList])

   def rowCount(self, index=QModelIndex()):
      return len(self.boxList)

   def columnCount(self, index=QModelIndex()):
      return 12

   def getKeyDisp(self, lbox, i):
      if len(lbox.commentList[i].strip())>0:
         return lbox.commentList[i]
      else:
         pubhex = binary_to_hex(lbox.pkList[i])
         addr = hash160_to_addrStr(lbox.a160List[i])
         return "%s (%s...)" % (addr, pubhex[:20])

   def data(self, index, role=Qt.DisplayRole):
      row,col = index.row(), index.column()
      lbox = self.boxList[row]
      lbID = lbox.uniqueIDB58
      lwlt = self.main.cppLockboxWltMap[lbID]

      nTx, bal = 0, 0
      if TheBDM.getBDMState()=='BlockchainReady':
         nTx = len(lwlt.getTxLedger())
         bal = lwlt.getFullBalance()

      if role==Qt.DisplayRole:
         if col==LOCKBOXCOLS.ID: 
            return QVariant(lbID)
         elif col==LOCKBOXCOLS.CreateDate: 
            return QVariant(unixTimeToFormatStr(lbox.createDate, self.dateFmt))
         elif col==LOCKBOXCOLS.MSType: 
            return QVariant('%d-of-%d' % (lbox.M, lbox.N))
         elif col==LOCKBOXCOLS.LBName: 
            return QVariant(lbox.shortName)
         elif col==LOCKBOXCOLS.Key0: 
            return QVariant(self.getKeyDisp(lbox, 0))
         elif col==LOCKBOXCOLS.Key1: 
            return QVariant(self.getKeyDisp(lbox, 1))
         elif col==LOCKBOXCOLS.Key2: 
            return QVariant(self.getKeyDisp(lbox, 2))
         elif col==LOCKBOXCOLS.Key3: 
            return QVariant(self.getKeyDisp(lbox, 3))
         elif col==LOCKBOXCOLS.Key4: 
            return QVariant(self.getKeyDisp(lbox, 4))
         elif col==LOCKBOXCOLS.NumTx: 
            if not TheBDM.getBDMState()=='BlockchainReady':
               return QVariant('(...)') 
            return QVariant(nTx)
         elif col==LOCKBOXCOLS.Balance: 
            if not TheBDM.getBDMState()=='BlockchainReady':
               return QVariant('(...)') 
            return QVariant(coin2str(bal, maxZeros=2))
         elif col==LOCKBOXCOLS.UnixTime: 
            return QVariant(str(lbox.createDate))

      elif role==Qt.TextAlignmentRole:
         if col in (LOCKBOXCOLS.MSType, 
                    LOCKBOXCOLS.NumTx,
                    LOCKBOXCOLS.Balance):
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))

         return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))

      elif role==Qt.FontRole:
         f = GETFONT('Var')
         if col==LOCKBOXCOLS.Balance:
            f = GETFONT('Fixed')
         if nTx>0:
            f.setWeight(QFont.Bold)
         return QVariant(f)
      elif role==Qt.BackgroundColorRole:
         if bal>0:
            return QVariant( Colors.SlightGreen )


      return QVariant()


   def headerData(self, section, orientation, role=Qt.DisplayRole):
      colLabels = ['ID', 'Type', 'Created', 'Info', 
                   'Key #1', 'Key #2', 'Key #3', 'Key #4', 'Key #5', 
                   '#Tx', 'Funds', 'UnixTime']
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            return QVariant( colLabels[section])
      elif role==Qt.TextAlignmentRole:
         return QVariant( int(Qt.AlignHCenter | Qt.AlignVCenter) )




class LockboxDisplayProxy(QSortFilterProxyModel):
   """
   A proxy that re-maps indices to the table view so that data appears
   sorted without touching the model 
   """
   def lessThan(self, idxLeft, idxRight):
      COL = LOCKBOXCOLS
      thisCol  = self.sortColumn()

      def getDouble(idx, col):
         row = idx.row()
         s = toUnicode(self.sourceModel().index(row, col).data().toString())
         return float(s)

      def getInt(idx, col):
         row = idx.row()
         s = toUnicode(self.sourceModel().index(row, col).data().toString())
         return int(s)

      #LOCKBOXCOLS = enum('ID', 'MSType', 'CreateDate', 'LBName', \
                     #'Key0', 'Key1', 'Key2', 'Key3', 'Key4', \
                     #'NumTx', 'Balance', 'UnixTime')


      strLeft  = str(self.sourceModel().data(idxLeft).toString())
      strRight = str(self.sourceModel().data(idxRight).toString())

      if thisCol in (COL.ID, COL.MSType, COL.LBName):
         return (strLeft.lower() < strRight.lower())
      elif thisCol==COL.CreateDate:
         tLeft  = getDouble(idxLeft,  COL.UnixTime)
         tRight = getDouble(idxRight, COL.UnixTime)
         return (tLeft<tRight)
      elif thisCol==COL.NumTx:
         if TheBDM.getBDMState()=='BlockchainReady':
            ntxLeft  = getInt(idxLeft,  COL.NumTx)
            ntxRight = getInt(idxRight, COL.NumTx)
            return (ntxLeft < ntxRight)
      elif thisCol==COL.Balance:
         if TheBDM.getBDMState()=='BlockchainReady':
            btcLeft  = getDouble(idxLeft,  COL.Balance)
            btcRight = getDouble(idxRight, COL.Balance)
            return (abs(btcLeft) < abs(btcRight))

      return super(LockboxDisplayProxy, self).lessThan(idxLeft, idxRight)









