################################################################################
#
# Copyright (C) 2011-2012, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
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



WLTVIEWCOLS = enum('ID', 'Name', 'Secure', 'Bal')
LEDGERCOLS  = enum('NumConf', 'UnixTime', 'DateStr', 'TxDir', 'WltName', 'Comment', \
                   'Amount', 'isOther', 'WltID', 'TxHash', 'toSelf', 'DoubleSpend')
ADDRESSCOLS  = enum('Address', 'Comment', 'NumTx', 'Imported', 'Balance')
ADDRBOOKCOLS = enum('Address', 'WltID', 'NumSent', 'Comment')

TXINCOLS  = enum('WltID', 'Sender', 'Btc', 'OutPt', 'OutIdx', 'FromBlk', \
                                       'ScrType', 'Sequence', 'Script')
TXOUTCOLS = enum('WltID', 'Recip', 'Btc', 'ScrType', 'Script')


class AllWalletsDispModel(QAbstractTableModel):
   
   # The columns enumeration

   def __init__(self, mainWindow):
      super(AllWalletsDispModel, self).__init__()
      self.main = mainWindow

   def rowCount(self, index=QModelIndex()):
      return len(self.main.walletMap)

   def columnCount(self, index=QModelIndex()):
      return 4

   def data(self, index, role=Qt.DisplayRole):
      COL = WLTVIEWCOLS
      row,col = index.row(), index.column()
      wlt = self.main.walletMap[self.main.walletIDList[row]]
      wltID = wlt.uniqueIDB58
      if role==Qt.DisplayRole:
         if col==COL.ID: 
            return QVariant(wltID)
         if col==COL.Name: 
            return QVariant(wlt.labelName.ljust(32))
         if col==COL.Secure: 
            wtype,typestr = determineWalletType(wlt, self.main)
            return QVariant(typestr)
         if col==COL.Bal: 
            bal = wlt.getBalance('Total')
            if bal==-1:
               return QVariant('(...)') 
            else:
               dispStr = coin2str(bal, maxZeros=2)
               return QVariant(dispStr)
      elif role==Qt.TextAlignmentRole:
         if col in (COL.ID, COL.Name):
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         elif col in (COL.Secure,):
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
         elif col in (COL.Bal,):
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
      elif role==Qt.BackgroundColorRole:
         t = determineWalletType(wlt, self.main)[0]
         if t==WLTTYPES.WatchOnly:
            return QVariant( Colors.WltOther )
         elif t==WLTTYPES.Offline:
            return QVariant( Colors.WltOffline )
         else:
            return QVariant( Colors.WltMine )
      elif role==Qt.FontRole:
         if col==COL.Bal:
            return GETFONT('Fixed')
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
   """ Displays an Nx10 table of pre-formatted/processed ledger entries """
   def __init__(self, ledgerTable, parent=None, main=None):
      super(LedgerDispModelSimple, self).__init__()
      self.parent = parent
      self.main   = main
      self.ledger = ledgerTable

   def rowCount(self, index=QModelIndex()):
      return len(self.ledger)

   def columnCount(self, index=QModelIndex()):
      return 12

   def data(self, index, role=Qt.DisplayRole):
      COL = LEDGERCOLS
      row,col = index.row(), index.column()
      rowData = self.ledger[row]
      nConf = rowData[LEDGERCOLS.NumConf]
      wltID = rowData[LEDGERCOLS.WltID]
      wtype = determineWalletType(self.main.walletMap[wltID], self.main)[0]

      #LEDGERCOLS  = enum('NumConf', 'UnixTime','DateStr', 'TxDir', 'WltName', 'Comment', \
                         #'Amount', 'isOther', 'WltID', 'TxHash', 'toSelf', 'DoubleSpend')
      if role==Qt.DisplayRole:
         return QVariant(rowData[col])
      elif role==Qt.TextAlignmentRole:
         if col in (COL.NumConf,  COL.TxDir):
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
         elif col in (COL.Comment, COL.DateStr):
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         elif col in (COL.Amount,):
            return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
      elif role==Qt.DecorationRole:
         pass
      elif role==Qt.BackgroundColorRole:
         if wtype==WLTTYPES.WatchOnly:
            return QVariant( Colors.WltOther )
         elif wtype==WLTTYPES.Offline:
            return QVariant( Colors.WltOffline )
         else:
            return QVariant( Colors.WltMine )
      elif role==Qt.ForegroundRole:
         if self.index(index.row(),COL.DoubleSpend).data().toBool():
            return QVariant(Colors.Red)
         if nConf <= 2:
            return QVariant(Colors.MidGray)
         elif nConf <= 4:
            return QVariant(Colors.Gray)
         
         if col==COL.Amount:
            toSelf = self.index(index.row(), COL.toSelf).data().toBool()
            if toSelf:
               return QVariant(Colors.MidGray)
            amt = float(rowData[COL.Amount])
            if   amt>0: return QVariant(Colors.Green)
            elif amt<0: return QVariant(Colors.Red)
            else:       return QVariant(Colors.DarkGray)
      elif role==Qt.FontRole:
         if col==COL.Amount:
            f = GETFONT('Fixed')
            f.setWeight(QFont.Bold)
            return f
      elif role==Qt.ToolTipRole:
         if col in (COL.NumConf, COL.DateStr):
            if rowData[COL.NumConf]>5:
               return QVariant('Transaction confirmed!\n(%d confirmations)'%nConf)
            else:
               tooltipStr = '%d/6 confirmations'%rowData[COL.NumConf]
               tooltipStr += ( '\n\nFor small transactions, 2 or 3\n'
                               'confirmations is usually acceptable.\n'
                               'For larger transactions, you should\n'
                               'wait for 6 confirmations before\n'
                               'trusting that the transaction valid.')
               return QVariant(tooltipStr)
         if col==COL.TxDir:
            toSelf = self.index(index.row(), COL.toSelf).data().toBool()
            if toSelf:
               return QVariant('Bitcoins sent and received by the same wallet')
            else:
               txdir = str(index.model().data(index).toString()).strip()
               if txdir[0].startswith('-'):
                  return QVariant('Bitcoins sent')
               else:
                  return QVariant('Bitcoins received')
         if col==COL.Amount:
            if self.main.settings.get('DispRmFee'):
               return QVariant('The net effect on the balance of this wallet '
                               '<b>not including transaction fees.</b>  '
                               'You can change this behavior in the Armory '
                               'preferences window.')
            else:
               return QVariant('The net effect on the balance of this wallet '
                               '<b>including transaction fees.</b>  '
                               'If you would like to see only the amounts '
                               'directly paid or received, you can modify '
                               'the appropriate setting in the Armory preferences.')

      return QVariant()


   def headerData(self, section, orientation, role=Qt.DisplayRole):
      COL = LEDGERCOLS
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==COL.NumConf: return QVariant()
            if section==COL.DateStr: return QVariant('Date')
            if section==COL.WltName: return QVariant('Wallet')
            if section==COL.Comment: return QVariant('Comments')
            if section==COL.TxDir:   return QVariant()
            if section==COL.Amount:  return QVariant('Amount')
            if section==COL.isOther: return QVariant('Other Owner')
            if section==COL.WltID:   return QVariant('Wallet ID')
            if section==COL.TxHash:  return QVariant('Tx Hash (LE)')
      elif role==Qt.TextAlignmentRole:
         return QVariant( int(Qt.AlignHCenter | Qt.AlignVCenter) )




class LedgerDispDelegate(QStyledItemDelegate):

   COL = LEDGERCOLS

   def __init__(self, parent=None):
      super(LedgerDispDelegate, self).__init__(parent)   


   def paint(self, painter, option, index):
      bgcolor = QColor(index.model().data(index, Qt.BackgroundColorRole))
      if option.state & QStyle.State_Selected:
         bgcolor = QApplication.palette().highlight().color()

      if index.column() == self.COL.NumConf:
         nConf = index.model().data(index).toInt()[0]
         pixmaps = ['img/conf%dt.png'%i for i in range(6)]
         if nConf<6:
            image = QImage(pixmaps[nConf])
         else:
            image = QImage('img/conf6t.png')
         painter.fillRect(option.rect, bgcolor)
         pixmap = QPixmap.fromImage(image)
         #pixmap.scaled(70, 30, Qt.KeepAspectRatio)
         painter.drawPixmap(option.rect, pixmap)
      elif index.column() == self.COL.TxDir:
         # This is frustrating... QVariant doesn't support 64-bit ints
         # So I have to pass the amt as string, then convert here to long
         toSelf = index.model().index(index.row(), self.COL.toSelf).data().toBool()
         image = QImage()

         # isCoinbase still needs to be flagged in the C++ utils
         isCoinbase = False
         if isCoinbase:
            image = QImage('img/moneyCoinbase.png')
         elif toSelf:
            image = QImage('img/moneySelf.png')
         else:
            txdir = str(index.model().data(index).toString()).strip()
            if txdir[0].startswith('-'):
               image = QImage('img/moneyOut.png')
            else:
               image = QImage('img/moneyIn.png')

         painter.fillRect(option.rect, bgcolor)
         pixmap = QPixmap.fromImage(image)
         #pixmap.scaled(70, 30, Qt.KeepAspectRatio)
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
   
   def __init__(self, wlt, mainWindow):
      super(WalletAddrDispModel, self).__init__()
      self.main = mainWindow
      self.wlt = wlt
      self.addr160List = [a.getAddr160() for a in self.wlt.getLinearAddrList()]
      
   def reset(self):
      self.addr160List = [a.getAddr160() for a in self.wlt.getLinearAddrList()]
      QAbstractTableModel.reset(self)
      

   def rowCount(self, index=QModelIndex()):
      return len(self.addr160List)

   def columnCount(self, index=QModelIndex()):
      return 5

   def data(self, index, role=Qt.DisplayRole):
      COL = ADDRESSCOLS
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
            return QVariant( len(cppAddr.getTxLedger()) + \
                             len(cppAddr.getZeroConfLedger()))
         if col==COL.Imported:
            if self.wlt.addrMap[addr160].chainIndex==-2:
               return QVariant('Imported')
            else:
               return QVariant()
         if col==COL.Balance: 
            cppAddr = self.wlt.cppWallet.getAddrByHash160(addr160)
            return QVariant( coin2str(cppAddr.getFullBalance(), maxZeros=2) )
      elif role==Qt.TextAlignmentRole:
         if col in (COL.Address, COL.Comment):
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         elif col in (COL.NumTx,COL.Imported):
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
         elif col in (COL.Balance,):
            return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
      elif role==Qt.ForegroundRole:
         if col==COL.Balance:
            cppAddr = self.wlt.cppWallet.getAddrByHash160(addr160)
            val = cppAddr.getFullBalance()
            if   val>0: return QVariant(Colors.Green)
            else:       return QVariant(Colors.DarkGray)
      elif role==Qt.FontRole:
         doBold = len(self.wlt.cppWallet.getAddrByHash160(addr160).getTxLedger())>0
         if col==COL.Balance:
            return GETFONT('Fixed',bold=doBold)
         else:
            return GETFONT('Var',bold=doBold)
      elif role==Qt.BackgroundColorRole:
         cppAddr = self.wlt.cppWallet.getAddrByHash160(addr160)
         val = cppAddr.getFullBalance()
         if val>0:
            return QVariant( Colors.LightGreen )
         else:
            return QVariant( Colors.WltOther )

      return QVariant()

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      COL = ADDRESSCOLS
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==COL.Address:  return QVariant( 'Address' )
            if section==COL.Comment:  return QVariant( 'Comment' )
            if section==COL.NumTx:    return QVariant( '#Tx'     )
            if section==COL.Imported: return QVariant( ''        )
            if section==COL.Balance:  return QVariant( 'Balance' )
         elif role==Qt.TextAlignmentRole:
            if section in (COL.Address, COL.Comment):
               return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
            elif section in (COL.NumTx,):
               return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
            elif section in (COL.Balance,):
               return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))

      return QVariant()
            
      

################################################################################
class TxInDispModel(QAbstractTableModel):
   def __init__(self,  pytx, txinListFromBDM=None, main=None):
      super(TxInDispModel, self).__init__()
      self.main = main
      self.txInList = []
      self.dispTable = []


      # If this is actually a TxDP in here, then let's use that
      # We do this to make sure we have somewhere to put txdp-specific
      # code, but we don't really need it yet, except to identify
      # signed/unsigned in the table
      pytxdp = None
      if isinstance(pytx, PyTxDistProposal):
         pytxdp = pytx
         pytx = pytxdp.pytxObj.copy()
      self.tx = pytx.copy()
      
      for i,txin in enumerate(self.tx.inputs):
         self.dispTable.append([])
         wltID = ''
         scrType = getTxInScriptType(txin)
         if txinListFromBDM and len(txinListFromBDM[i][0])>0:
            # We had a BDM to help us get info on each input -- use it
            recip160,val,blk,hsh,idx = txinListFromBDM[i]
            if main:
               wltID = self.main.getWalletForAddr160(recip160)
            dispcoin  = '' if not val else coin2str(val,maxZeros=1)
            self.dispTable[-1].append(wltID)
            self.dispTable[-1].append(hash160_to_addrStr(recip160))
            self.dispTable[-1].append(dispcoin)
            self.dispTable[-1].append(binary_to_hex(hsh))
            self.dispTable[-1].append(idx)
            self.dispTable[-1].append(blk)
            if pytxdp==None:
               self.dispTable[-1].append(TXIN_TYPE_NAMES[scrType])
            else:
               # TODO:  Assume NO multi-sig... will be updated in future to use 
               #        PyTxDP::isSigValidForInput which will handle all cases
               self.dispTable[-1].append('Signed' if pytxdp.signatures[i][0] else 'Unsigned')
               
            self.dispTable[-1].append(int_to_hex(txin.intSeq, widthBytes=4))
            self.dispTable[-1].append(binary_to_hex(txin.binScript))
         else:
            # We don't have any info from the BDM, display whatever we can
            # (which usually isn't much)
            recipAddr = '<Unknown>'
            if scrType in (TXIN_SCRIPT_STANDARD,):
               recipAddr = TxInScriptExtractAddr160IfAvail(txin)
               if main:
                  wltID = self.main.getWalletForAddr160(recip)
            self.dispTable[-1].append(wltID)
            self.dispTable[-1].append(recipAddr)
            self.dispTable[-1].append('<Unknown>')
            self.dispTable[-1].append(binary_to_hex(txin.outpoint.txHash))
            self.dispTable[-1].append(str(txin.outpoint.txOutIndex))
            self.dispTable[-1].append('')
            self.dispTable[-1].append(TXIN_TYPE_NAMES[scrType])
            self.dispTable[-1].append(int_to_hex(txin.intSeq, widthBytes=4))
            self.dispTable[-1].append(binary_to_hex(txin.binScript))



   def rowCount(self, index=QModelIndex()):
      return len(self.dispTable)

   def columnCount(self, index=QModelIndex()):
      return 9

   #TXINCOLS  = enum('WltID', 'Sender', 'Btc', 'OutPt', 'OutIdx', 'FromBlk', 'ScrType', 'Sequence', 'Script')
   def data(self, index, role=Qt.DisplayRole):
      COLS = TXINCOLS
      row,col = index.row(), index.column()

      wltID = self.dispTable[row][COLS.WltID]
      if role==Qt.DisplayRole:
         return QVariant(self.dispTable[row][col])
      elif role==Qt.TextAlignmentRole:
         if col in (COLS.WltID, COLS.Sender, COLS.OutPt):
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         elif col in (COLS.OutIdx, COLS.FromBlk, COLS.Sequence, COLS.ScrType):
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
         elif col in (COLS.Btc,):
            return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
      elif role==Qt.BackgroundColorRole:
         if self.dispTable[row][COLS.WltID]:
            wtype = determineWalletType(self.main.walletMap[wltID], self.main)[0]
            if wtype==WLTTYPES.WatchOnly:
               return QVariant( Colors.WltOther )
            elif wtype==WLTTYPES.Offline:
               return QVariant( Colors.WltOffline )
            else:
               return QVariant( Colors.WltMine )
      elif role==Qt.FontRole:
         if col==COLS.Btc:
            return GETFONT('Fixed')

      return QVariant()

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      COLS = TXINCOLS
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==COLS.WltID:    return QVariant('Wallet ID')
            if section==COLS.Sender:   return QVariant('Sender')
            if section==COLS.Btc:      return QVariant('Amount')
            if section==COLS.OutPt:    return QVariant('Prev. Tx Hash')
            if section==COLS.OutIdx:   return QVariant('Index')
            if section==COLS.FromBlk:  return QVariant('From Block#')
            if section==COLS.ScrType:  return QVariant('Script Type')
            if section==COLS.Sequence: return QVariant('Sequence')
            if section==COLS.Script:   return QVariant('Script')
      elif role==Qt.TextAlignmentRole:
         if orientation==Qt.Horizontal:
            if section in (COLS.WltID, COLS.Sender, COLS.OutPt):
               return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
            elif section in (COLS.OutIdx, COLS.FromBlk, COLS.Btc, COLS.Sequence, COLS.ScrType):
               return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
         return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))






################################################################################
class TxOutDispModel(QAbstractTableModel):
   def __init__(self,  pytx, main=None, idxGray=[]):
      super(TxOutDispModel, self).__init__()
      self.tx = pytx.copy()
   
      self.main = main
      self.txOutList = []
      self.wltIDList = []
      self.idxGray = idxGray
      for i,txout in enumerate(self.tx.outputs):
         recip160 = TxOutScriptExtractAddr160(txout.binScript)
         self.txOutList.append(txout)
         if main:
            self.wltIDList.append(main.getWalletForAddr160(recip160))
         else:
            self.wltIDList.append('')

   def rowCount(self, index=QModelIndex()):
      return len(self.txOutList)

   def columnCount(self, index=QModelIndex()):
      return 5

   #TXOUTCOLS = enum('WltID', 'Recip', 'Btc', 'ScrType')
   def data(self, index, role=Qt.DisplayRole):
      COLS = TXOUTCOLS
      row,col = index.row(), index.column()
      txout = self.txOutList[row]
      stype = getTxOutScriptType(txout.binScript)
      stypeStr = TXOUT_TYPE_NAMES[stype]
      wltID = self.wltIDList[row]
      if stype==TXOUT_SCRIPT_MULTISIG:
         mstype = getTxOutMultiSigInfo(txout.binScript)[0]
         stypeStr = 'Multi-Signature (%d-of-%d)' % mstype
      if role==Qt.DisplayRole:
         if col==COLS.WltID:   return QVariant(wltID)
         if col==COLS.ScrType: return QVariant(stypeStr)
         if col==COLS.Script:  return QVariant(binary_to_hex(txout.binScript))
         if stype==TXOUT_SCRIPT_STANDARD:
            if col==COLS.Recip:   return QVariant(TxOutScriptExtractAddrStr(txout.binScript))
            if col==COLS.Btc:     return QVariant(coin2str(txout.getValue(),maxZeros=2))
         if stype==TXOUT_SCRIPT_COINBASE:
            if col==COLS.Recip:   return QVariant(TxOutScriptExtractAddrStr(txout.binScript))
            if col==COLS.Btc:     return QVariant(coin2str(txout.getValue(),maxZeros=2))
         if stype==TXOUT_SCRIPT_MULTISIG:
            if col==COLS.Recip:   return QVariant('[[Multiple]]')
            if col==COLS.Btc:     return QVariant(coin2str(txout.getValue(),maxZeros=2))
         if stype==TXOUT_SCRIPT_UNKNOWN:
            if col==COLS.Recip:   return QVariant('[[Non-Standard]]')
            if col==COLS.Btc:     return QVariant(coin2str(txout.getValue(),maxZeros=2))
         if stype==TXOUT_SCRIPT_OP_EVAL:
            if col==COLS.Recip:   return QVariant('[[OP-EVAL]]')
            if col==COLS.Btc:     return QVariant(coin2str(txout.getValue(),maxZeros=2))
      elif role==Qt.TextAlignmentRole:
         if col==COLS.Recip:   return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         if col==COLS.Btc:     return QVariant(int(Qt.AlignRight | Qt.AlignVCenter))
         if col==COLS.ScrType: return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
      elif role==Qt.ForegroundRole:
         if row in self.idxGray:
            return QVariant(Colors.MidGray)
      elif role==Qt.BackgroundColorRole:
         if wltID:
            wtype = determineWalletType(self.main.walletMap[wltID], self.main)[0]
            if wtype==WLTTYPES.WatchOnly:
               return QVariant( Colors.WltOther )
            if wtype==WLTTYPES.Offline:
               return QVariant( Colors.WltOffline )
            else:
               return QVariant( Colors.WltMine )
      elif role==Qt.FontRole:
         if col==COLS.Btc:
            return GETFONT('Fixed')

      return QVariant()

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      COLS = TXOUTCOLS
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==COLS.WltID:   return QVariant('Wallet ID')
            if section==COLS.Recip:   return QVariant('Recipient')
            if section==COLS.Btc:     return QVariant('Amount')
            if section==COLS.ScrType: return QVariant('Script Type')
      elif role==Qt.TextAlignmentRole:
         if orientation==Qt.Horizontal:
            if section==COLS.WltID:   return QVariant(Qt.AlignLeft | Qt.AlignVCenter)
            if section==COLS.Recip:   return QVariant(Qt.AlignLeft | Qt.AlignVCenter)
            if section==COLS.Btc:     return QVariant(Qt.AlignHCenter | Qt.AlignVCenter)
            if section==COLS.ScrType: return QVariant(Qt.AlignHCenter | Qt.AlignVCenter)
         return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))





################################################################################
class SentToAddrBookModel(QAbstractTableModel):
   def __init__(self, wltID, main):
      super(SentToAddrBookModel, self).__init__()

      self.wltID = wltID
      self.main  = main
      self.wlt   = self.main.walletMap[wltID]

      # Get a vector of "AddressBookEntry" objects sorted by first-sent-to
      self.addrBook = self.wlt.cppWallet.createAddressBook()

      # Delete entries that are our own addr in other wallets
      otherAddr = []
      for abe in self.addrBook:
         if not self.main.getWalletForAddr160(abe.getAddr160()):
            otherAddr.append(abe)

      self.addrBook = otherAddr
      

   def rowCount(self, index=QModelIndex()):
      return len(self.addrBook)

   def columnCount(self, index=QModelIndex()):
      return 4

   def data(self, index, role=Qt.DisplayRole):
      COL = ADDRBOOKCOLS
      row,col = index.row(), index.column()
      abe     = self.addrBook[row]
      addr160 = abe.getAddr160()
      addrB58 = hash160_to_addrStr(addr160)
      wltID   = self.main.getWalletForAddr160(addr160)
      numSent =   len(abe.getTxList())
      comment = self.wlt.getCommentForAddrBookEntry(abe)
      
      #ADDRBOOKCOLS = enum('Address', 'WltID', 'NumSent', 'Comment')
      if role==Qt.DisplayRole:
         if col==COL.Address: 
            return QVariant( addrB58 )
         if col==COL.NumSent: 
            return QVariant( numSent ) 
         if col==COL.Comment: 
            return QVariant( comment )
         if col==COL.WltID:
            return QVariant( wltID )
      elif role==Qt.TextAlignmentRole:
         if col in (COL.Address, COL.Comment, COL.WltID):
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         elif col in (COL.NumSent,):
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))
      elif role==Qt.FontRole:
         isFreqAddr = (numSent>1)
         return GETFONT('Var', bold=isFreqAddr)

      return QVariant()

   def headerData(self, section, orientation, role=Qt.DisplayRole):
      COL = ADDRBOOKCOLS
      if role==Qt.DisplayRole:
         if orientation==Qt.Horizontal:
            if section==COL.Address:  return QVariant( 'Address'    )
            if section==COL.WltID:    return QVariant( 'Ownership'  )
            if section==COL.NumSent:  return QVariant( 'Times Used' )
            if section==COL.Comment:  return QVariant( 'Comment'    )
      elif role==Qt.TextAlignmentRole:
         if section in (COL.Address, COL.Comment, COL.WltID):
            return QVariant(int(Qt.AlignLeft | Qt.AlignVCenter))
         elif section in (COL.NumSent,):
            return QVariant(int(Qt.AlignHCenter | Qt.AlignVCenter))

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

   def __init__(self,tx):
      super(TxInDataModel, self).__init__()
      self.bdm = BlockDataManager().getBDM()
      self.endianSelect = BIGENDIAN
      self.tx = tx.copy()

   def rowCount(self, index=QModelIndex()):
      return self.tx.getNumTxIn()


   def columnCount(self, index=QModelIndex()):
      return 5

   def data(self, index, role=Qt.DisplayRole):
      nTxIn = self.rowCount()
      row,col = index.row(), index.column()

      if role==Qt.DisplayRole:
         cppTxIn = self.tx.getTxInRef(row)
         if cppTxIn == None:
            return QVariant()
         if col == TXIN_SRC:
            if cppTxIn.isCoinbase():
               return QVariant("COINBASE")
            addr20 = self.bdm.getSenderAddr20(cppTxIn)
            return QVariant(hash160_to_addrStr(addr20))
         elif col== TXIN_BTC:
            if cppTxIn.isCoinbase():
               return QVariant("%0.4f" % float(self.tx.getSumOfOutputs()/1e8))
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










