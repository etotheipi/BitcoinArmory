import os
import platform
import sys
from os import path
from PyQt4.QtCore import *
from PyQt4.QtGui import *
sys.path.append('..')
sys.path.append('../cppForSwig')
from armoryengine import *
from CppBlockUtils import *
from qtdefines import *


Colors = enum(LightBlue=   QColor(215,215,255), \
              LightGreen=  QColor(225,255,225), \
              LightGray=   QColor(235,235,235), \
              LighterGray= QColor(245,245,245), \
              DarkGray=    QColor( 64, 64, 64), \
              Green=       QColor(  0,100,  0), \
              Red=         QColor(100,  0,  0), \
              Black=       QColor(  0,  0,  0)  \
                                              )


class AllWalletsDispModel(QAbstractTableModel):
   
   # The columns enumeration
   COL = enum('ID', 'Name', 'Secure', 'Bal')

   def __init__(self, mainWindow):
      super(AllWalletsDispModel, self).__init__()
      self.main = mainWindow

   def rowCount(self, index=QModelIndex()):
      return len(self.main.walletMap)

   def columnCount(self, index=QModelIndex()):
      return 4

   def data(self, index, role=Qt.DisplayRole):
      COL = self.COL
      row,col = index.row(), index.column()
      wlt = self.main.walletMap[self.main.walletIDList[row]]
      wltID = wlt.wltUniqueIDB58
      if role==Qt.DisplayRole:
         if col==COL.ID: 
            return QVariant(wltID)
         if col==COL.Name: 
            return QVariant(wlt.labelName.ljust(32))
         if col==COL.Secure: 
            wtype,typestr = determineWalletType(wlt, self.main)
            return QVariant(typestr)
         if col==COL.Bal: 
            bal = self.main.walletBalances[row]
            if bal==-1:
               return QVariant('(...)') 
            else:
               if bal==0:
                  ndigit=1
               elif bal<1000:
                  ndigit = 8
               elif bal<100000:
                  ndigit = 6
               else:
                  ndigit = 4
               dispStr = [c for c in coin2str(bal, ndec=8)]
               dispStr[-8+ndigit:] = ' '*(8-ndigit)
               return QVariant(''.join(dispStr))
      elif role==Qt.TextAlignmentRole:
         if col in (0,1):
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         elif col in (2,):
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
         elif col in (3,):
            return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
      elif role==Qt.BackgroundColorRole:
         if wlt.watchingOnly and not wltID in self.main.walletOfflines:
            return QVariant( Colors.LightGray )
         else:
            return QVariant( Colors.LightBlue )
      elif role==Qt.FontRole:
         if col==3:
            return QFont("DejaVu Sans Mono", 10)
      return QVariant()


   def headerData(self, section, orientation, role=Qt.DisplayRole):
      colLabels = ['ID', 'Name', 'Security', 'Balance']
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            return QVariant( colLabels[section])
      elif role==Qt.TextAlignmentRole:
         return QVariant( int(Qt.AlignHCenter | Qt.AlignVCenter) )



   # This might work for checkbox-in-tableview
   #QStandardItemModel* tableModel = new QStandardItemModel();
   #// create text item
   #tableModel->setItem(0, 0, new QStandardItem("text item"));
   #// create check box item
   #QStandardItem* item0 = new QStandardItem(true);
   #item0->setCheckable(true);
   #item0->setCheckState(Qt::Checked);
   #item0->setText("some text");
   #tableModel->setItem(0, 1, item0);
   #// set model
   #ui->tableView->setModel(tableModel);

   # Perhaps delegate for rich text in QTableViews
   #void SpinBoxDelegate::paint(QPainter *painter, const QStyleOptionViewItem &option, const QModelIndex &index) const
   #{
        #QTextDocument document;
        #QVariant value = index.data(Qt::DisplayRole);
        #if (value.isValid() && !value.isNull()) {
             #QString text("<span style='background-color: lightgreen'>This</span> is highlighted.");
        #text.append(" (");
        #text.append(value.toString());
        #text.append(")");
        #document.setHtml(text);
        #painter->translate(option.rect.topLeft());
        #document.drawContents(painter);
        #painter->translate(-option.rect.topLeft());
   #}

################################################################################
class LedgerDispModelSimple(QAbstractTableModel):
   """ Displays an Nx7 table of pre-formatted/processed ledger entries """

   COL = enum('NumConf', 'Date', 'TxDir', 'WltName', 'Comment', 'Amount', 'isOther', 'WltID')

   def __init__(self, table2D):
      super(LedgerDispModelSimple, self).__init__()
      self.ledger = table2D

   def rowCount(self, index=QModelIndex()):
      return len(self.ledger)

   def columnCount(self, index=QModelIndex()):
      return 6

   def data(self, index, role=Qt.DisplayRole):
      COL = self.COL
      row,col = index.row(), index.column()
      rowData = self.ledger[row]

      if role==Qt.DisplayRole:
         return QVariant(rowData[col])
      elif role==Qt.TextAlignmentRole:
         if col in (COL.NumConf,  COL.TxDir):
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
         elif col in (COL.Comment, COL.Date):
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         elif col in (COL.Amount,):
            return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
      elif role==Qt.DecorationRole:
         pass
      elif role==Qt.BackgroundColorRole:
         if not rowData[COL.isOther]:
            return QVariant( Colors.LightBlue )
         else:
            return QVariant( Colors.LightGray )
      elif role==Qt.ForegroundRole:
         if col==COL.Amount:
            if   rowData[COL.Amount]>0: return QVariant(Colors.Green)
            elif rowData[COL.Amount]<0: return QVariant(Colors.Red)
            else:                       return QVariant(Colors.DarkGray)
      elif role==Qt.ToolTipRole:
         if col==COL.NumConf:
            if rowData[COL.NumConf]>5:
               return QVariant('Transaction confirmed!\n(%d confirmations)'%nConf)
            else:
               tooltipStr = '%d/6 confirmations'%rowData[COL.NumConf]
               tooltipStr += ( '\n\nFor small transactions, 2 or 3\n'
                               'confirmations is usually acceptable.\n'
                               'For larger transactions, you should\n'
                               'wait at least 6 confirmations before\n'
                               'considering the transaction valid.')
               return QVariant(tooltipStr)

      return QVariant()


   def headerData(self, section, orientation, role=Qt.DisplayRole):
      COL = self.COL
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==COL.NumConf:  return QVariant()
            if section==COL.Date:    return QVariant('Date')
            if section==COL.WltName: return QVariant('Wallet')
            if section==COL.Comment: return QVariant('Comments')
            if section==COL.TxDir:   return QVariant()
            if section==COL.Amount:  return QVariant('Amount')
      elif role==Qt.TextAlignmentRole:
         return QVariant( int(Qt.AlignHCenter | Qt.AlignVCenter) )


################################################################################
class LedgerDispModel(QAbstractTableModel):
   """ Displays an Nx7 table of pre-formatted/processed ledger entries """

   COL = enum('NumConf', 'Date', 'TxDir', 'WltName', 'Comment', 'Amount')

   def __init__(self, mainWindow):
      super(LedgerDispModel, self).__init__()
      self.main = mainWindow

   def rowCount(self, index=QModelIndex()):
      return int(self.main.ledgerSize)

   def columnCount(self, index=QModelIndex()):
      return 6

   def data(self, index, role=Qt.DisplayRole):
      COL = self.COL
      row,col = index.row(), index.column()
      wltID,le = self.main.combinedLedger[row]
      nConf = self.main.latestBlockNum - le.getBlockNum()+1
      if le.getBlockNum() >= 0xffffffff:
         nConf = 0

      if role==Qt.DisplayRole:
         # A little more pre-processing before display
         blkheader = TheBDM.getHeaderByHeight(le.getBlockNum())
         txtime = blkheader.getTimestamp()
         txHash = le.getTxHash()
         if nConf == 0:
            txtime = self.main.NetworkingFactory.zeroConfTxTime[txHash]
         
         if col==COL.NumConf: 
            return QVariant(nConf)
         elif col==COL.Date: 
            return QVariant(unixTimeToFormatStr(txtime))
         elif col==COL.TxDir:
            return QVariant(le.getValue())
            #if le.getValue()>0:
               #return QVariant('Recv')
            #else:
               #return QVariant('Sent')
         elif col==COL.WltName: 
            wlt = self.main.walletMap[wltID]
            return QVariant(wlt.labelName)
         elif col==COL.Comment: 
            wlt = self.main.walletMap[wltID]
            if wlt.commentsMap.has_key(txHash):
               return QVariant(wlt.commentsMap[txHash])
         elif col==COL.Amount:
            return QVariant( coin2str(le.getValue()) )
      elif role==Qt.TextAlignmentRole:
         if col in (COL.NumConf,  COL.TxDir):
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
         elif col in (COL.Comment, COL.Date):
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         elif col in (COL.Amount,):
            return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
      elif role==Qt.DecorationRole:
         if col==COL.NumConf:
            return QVariant(nConf)
            #icons = ['icons/conf%d.png'%i for i in range(6)]
            #if nConf<6:
               #return QVariant(QIcon(icons[nConf]))
            #else:
               #return QVariant(QIcon('icons/conf6_chk_blue.png'))
            #if le.getValue()>0:
               #return QVariant(QIcon('icons/moneyIn.png'))
            #else:
               #return QVariant(QIcon('icons/moneyOut.png'))
      elif role==Qt.BackgroundColorRole:
         if self.main.walletMap[wltID].watchingOnly and \
                           not wltID in self.main.walletOfflines:
            return QVariant( Colors.LightGray )
         else:
            return QVariant( Colors.LightBlue )
      elif role==Qt.ForegroundRole:
         if col==COL.Amount:
            if   le.getValue()>0: return QVariant(Colors.Green)
            elif le.getValue()<0: return QVariant(Colors.Red)
            else:                 return QVariant(Colors.DarkGray)
      elif role==Qt.ToolTipRole:
         if col==COL.NumConf:
            if nConf>5:
               return QVariant('Transaction confirmed!\n(%d confirmations)'%nConf)
            else:
               tooltipStr = '%d/6 confirmations'%nConf
               tooltipStr += ( '\n\nFor small transactions, 2 or 3\n'
                               'confirmations is usually acceptable.\n'
                               'For larger transactions, you should\n'
                               'wait at least 6 confirmations before\n'
                               'considering the transaction valid.')
               return QVariant(tooltipStr)
               

      return QVariant()




   def headerData(self, section, orientation, role=Qt.DisplayRole):
      COL = self.COL
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==COL.NumConf:  return QVariant()
            if section==COL.Date:    return QVariant('Date')
            if section==COL.WltName: return QVariant('Wallet')
            if section==COL.Comment: return QVariant('Comments')
            if section==COL.TxDir:   return QVariant()
            if section==COL.Amount:  return QVariant('Amount')
      elif role==Qt.TextAlignmentRole:
         return QVariant( int(Qt.AlignHCenter | Qt.AlignVCenter) )



class LedgerDispDelegate(QStyledItemDelegate):

   COL = enum('NumConf', 'Date', 'TxDir', 'WltName', 'Comment', 'Amount')

   def __init__(self, parent=None):
      super(LedgerDispDelegate, self).__init__(parent)   


   def paint(self, painter, option, index):
      bgcolor = QColor(index.model().data(index, Qt.BackgroundColorRole))
      if option.state & QStyle.State_Selected:
         bgcolor = QApplication.palette().highlight().color()

      if index.column() == self.COL.NumConf:
         nConf = index.model().data(index).toInt()[0]
         pixmaps = ['icons/conf%d.png'%i for i in range(6)]
         if nConf<6:
            image = QImage(pixmaps[nConf])
         else:
            image = QImage('icons/conf6_chk_blue.png')
         painter.fillRect(option.rect, bgcolor)
         pixmap = QPixmap.fromImage(image)
         pixmap.scaled(70, 30, Qt.KeepAspectRatio)
         painter.drawPixmap(option.rect, pixmap)
      elif index.column() == self.COL.TxDir:
         txdir = str(index.model().data(index).toInt())
         image = QImage()
         if txdir[0] > 0:
            image = QImage('icons/moneyIn.png')
         else:
            image = QImage('icons/moneyOut.png')
         painter.fillRect(option.rect, bgcolor)
         pixmap = QPixmap.fromImage(image)
         pixmap.scaled(70, 30, Qt.KeepAspectRatio)
         painter.drawPixmap(option.rect, pixmap)
      else:
         QStyledItemDelegate.paint(self, painter, option, index)

   def sizeHint(self, option, index):
      if index.column()==self.COL.NumConf:
         return QSize(28,28)
      elif index.column()==self.COL.TxDir:
         return QSize(28,28)
      return QStyledItemDelegate.sizeHint(self, option, index)





################################################################################
class WalletAddrDispModel(QAbstractTableModel):
   
   # The columns enumeration
   COL = enum('Address', 'Comment', 'NumTx', 'Balance')

   def __init__(self, wlt, mainWindow):
      super(WalletAddrDispModel, self).__init__()
      self.main = mainWindow
      self.wlt = wlt
      self.addr160List = wlt.addrMap.keys()
      self.addr160List.remove('ROOT')
      

   def rowCount(self, index=QModelIndex()):
      return len(self.addr160List)

   def columnCount(self, index=QModelIndex()):
      return 4

   def data(self, index, role=Qt.DisplayRole):
      COL = self.COL
      row,col = index.row(), index.column()
      addr = self.wlt.addrMap[self.addr160List[row]]
      addr160 = addr.getAddr160()
      addrB58 = addr.getAddrStr()
      if role==Qt.DisplayRole:
         if col==COL.Address: 
            return QVariant( addrB58 )
         if col==COL.Comment: 
            if addr160 in self.wlt.commentsMap:
               return QVariant( self.wlt.commentsMap[addr160] )
            else:
               return QVariant('')
         if col==COL.NumTx: 
            cppAddr = self.wlt.cppWallet.getAddrByHash160(addr160)
            return QVariant( len(cppAddr.getTxLedger()) )
         if col==COL.Balance: 
            cppAddr = self.wlt.cppWallet.getAddrByHash160(addr160)
            return QVariant( coin2str(cppAddr.getBalance()) )
      elif role==Qt.TextAlignmentRole:
         if col in (COL.Address, COL.Comment):
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         elif col in (COL.NumTx,):
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
         elif col in (COL.Balance,):
            return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
      elif role==Qt.ForegroundRole:
         if col==COL.Balance:
            cppAddr = self.wlt.cppWallet.getAddrByHash160(addr160)
            val = cppAddr.getBalance()
            if   val>0: return QVariant(Colors.Green)
            else:       return QVariant(Colors.DarkGray)
      elif role==Qt.FontRole:
         if col==COL.Balance:
            return QFont("DejaVu Sans Mono", 10)
      elif role==Qt.BackgroundColorRole:
         cppAddr = self.wlt.cppWallet.getAddrByHash160(addr160)
         val = cppAddr.getBalance()
         if val>0:
            return QVariant( Colors.LightGreen )
         else:
            return QVariant( Colors.LighterGray )

      return QVariant()

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      COL = self.COL
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==COL.Address: return QVariant( 'Address' )
            if section==COL.Comment: return QVariant( 'Comment' )
            if section==COL.NumTx:   return QVariant( '#Tx'     )
            if section==COL.Balance: return QVariant( 'Balance' )
         elif role==Qt.TextAlignmentRole:
            if section in (COL.Address, COL.Comment):
               return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
            elif section in (COL.NumTx,):
               return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
            elif section in (COL.Balance,):
               return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))

      return QVariant()
            
      


"""
class HeaderDataModel(QAbstractTableModel):
   def __init__(self):
      super(HeaderDataModel, self).__init__()
      self.bdm = BlockDataManager().getBDM()

   def rowCount(self, index=QModelIndex()):

   def columnCount(self, index=QModelIndex()):

   def data(self, index, role=Qt.DisplayRole):
      nHead = self.rowCount()
      row,col = index.row(), index.column()
      if role==Qt.DisplayRole:
         if col== HEAD_DATE: return QVariant(someStr)
      elif role==Qt.TextAlignmentRole:
         if col in (HEAD_BLKNUM, HEAD_DIFF, HEAD_NUMTX, HEAD_BTC):
            return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
         else: 
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
      elif role==Qt.BackgroundColorRole:
         return QVariant( QColor(235,235,255) )
      return QVariant()

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            return QVariant( headColLabels[section] )
      elif role==Qt.TextAlignmentRole:
         return QVariant( int(Qt.AlignHCenter | Qt.AlignVCenter) )
"""


"""

################################################################################
# Below is PyBtcEngine testing code -- A blockchain explorer may be a nice 
# feature in the future, but not right now -- IGNORE THIS SECTION
################################################################################

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
      self.bdm = BlockDataManager().getBDM()
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
      self.bdm = BlockDataManager().getBDM()
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
      self.bdm = BlockDataManager().getBDM()
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
      self.bdm = BlockDataManager().getBDM()
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
         elif col in (TXOUT_BTC,):
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
            return QVariant( txoutColLabels[section] )



"""









