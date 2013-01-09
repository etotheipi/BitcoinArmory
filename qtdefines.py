################################################################################
#
# Copyright (C) 2011-2013, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
from armoryengine import *
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from armorycolors import Colors, htmlColor
from qrcodenative import QRCode, QRErrorCorrectLevel
from tempfile import mkstemp

SETTINGS_PATH   = os.path.join(ARMORY_HOME_DIR, 'ArmorySettings.txt')
USERMODE        = enum('Standard', 'Advanced', 'Expert')
NETWORKMODE     = enum('Offline', 'Full', 'Disconnected')
WLTTYPES        = enum('Plain', 'Crypt', 'WatchOnly', 'Offline')
WLTFIELDS       = enum('Name', 'Descr', 'WltID', 'NumAddr', 'Secure', \
                       'BelongsTo', 'Crypto', 'Time', 'Mem', 'Version')
MSGBOX          = enum('Good','Info', 'Question', 'Warning', 'Critical', 'Error')

STYLE_SUNKEN = QFrame.Box | QFrame.Sunken
STYLE_RAISED = QFrame.Box | QFrame.Raised
STYLE_PLAIN  = QFrame.Box | QFrame.Plain
STYLE_NONE   = QFrame.NoFrame

CHANGE_ADDR_DESCR_STRING = '[[ Change received ]]'

# TODO: switch to checking master branch once this is out
HTTP_VERSION_FILE = 'http://bitcoinarmory.com/versions.txt'
#HTTP_VERSION_FILE = 'https://raw.github.com/etotheipi/BitcoinArmory/logger/versions.txt'
#HTTP_VERSION_FILE = 'https://github.com/downloads/etotheipi/BitcoinArmory/versions.txt'
#HTTP_VERSION_FILE = 'http://bitcoinarmory.com/wp-content/uploads/2012/07/versions.txt'

def HLINE(style=QFrame.Plain):
   qf = QFrame()
   qf.setFrameStyle(QFrame.HLine | style)
   return qf

def VLINE(style=QFrame.Plain):
   qf = QFrame()
   qf.setFrameStyle(QFrame.VLine | style)
   return qf



# Setup fixed-width and var-width fonts
def GETFONT(ftype, sz=10, bold=False, italic=False):
   fnt = None
   if ftype.lower().startswith('fix'):
      if OS_WINDOWS:
         fnt = QFont("Courier", sz)
      else: 
         fnt = QFont("DejaVu Sans Mono", sz)
   elif ftype.lower().startswith('var'):
      fnt = QFont("Verdana", sz)
      #if OS_WINDOWS:
         #fnt = QFont("Tahoma", sz)
      #else: 
         #fnt = QFont("Sans", sz)
   elif ftype.lower().startswith('money'):
      if OS_WINDOWS:
         fnt = QFont("Courier", sz)
      else: 
         fnt = QFont("DejaVu Sans Mono", sz)
   else:
      fnt = QFont(ftype, sz)

   if bold:
      fnt.setWeight(QFont.Bold)

   if italic:
      fnt.setItalic(True)
   
   return fnt
      



#######
def UserModeStr(mode):
   if mode==USERMODE.Standard:
      return 'Standard'
   elif mode==USERMODE.Advanced:
      return 'Advanced'
   elif mode==USERMODE.Expert:
      return 'Expert'


#######
def tightSizeNChar(obj, nChar):
   """ 
   Approximates the size of a row text of mixed characters

   This is only aproximate, since variable-width fonts will vary
   depending on the specific text
   """

   try:
      fm = QFontMetricsF(QFont(obj.font()))
   except AttributeError:
      fm = QFontMetricsF(QFont(obj))
   szWidth,szHeight = fm.boundingRect('abcfgijklm').width(), fm.height()
   szWidth = int(szWidth * nChar/10.0 + 0.5)
   return szWidth, szHeight

#######
def tightSizeStr(obj, theStr):
   """ Measure a specific string """
   try:
      fm = QFontMetricsF(QFont(obj.font()))
   except AttributeError:
      fm = QFontMetricsF(QFont(obj))
   szWidth,szHeight = fm.boundingRect(theStr).width(), fm.height()
   return szWidth, szHeight
   
#######
def relaxedSizeStr(obj, theStr):
   """
   Approximates the size of a row text, nchars long, adds some margin
   """
   try:
      fm = QFontMetricsF(QFont(obj.font()))
   except AttributeError:
      fm = QFontMetricsF(QFont(obj))
   szWidth,szHeight = fm.boundingRect(theStr).width(), fm.height()
   return (10 + szWidth*1.05), 1.5*szHeight

#######
def relaxedSizeNChar(obj, nChar):
   """
   Approximates the size of a row text, nchars long, adds some margin
   """
   try:
      fm = QFontMetricsF(QFont(obj.font()))
   except AttributeError:
      fm = QFontMetricsF(QFont(obj))
   szWidth,szHeight = fm.boundingRect('abcfg ijklm').width(), fm.height()
   szWidth = int(szWidth * nChar/10.0 + 0.5)
   return (10 + szWidth*1.05), 1.5*szHeight

#############################################################################
def determineWalletType(wlt, wndw):
   if wlt.watchingOnly:
      if wndw.getWltSetting(wlt.uniqueIDB58,'IsMine'):
         return [WLTTYPES.Offline, 'Offline']
      else:
         return [WLTTYPES.WatchOnly, 'Watching-Only']
   elif wlt.useEncryption:
      return [WLTTYPES.Crypt, 'Encrypted']
   else:
      return [WLTTYPES.Plain, 'No Encryption']




#############################################################################
def initialColResize(tblViewObj, sizeList):
   """
   We assume that all percentages are below 1, all fixed >1.  
   TODO:  This seems to almost work.  providing exactly 100% input will
          actually result in somewhere between 75% and 125% (approx).  
          For now, I have to experiment with initial values a few times
          before getting it to a satisfactory initial size.
   """   
   totalWidth = tblViewObj.width()
   fixedCols, pctCols = [],[]

   nCols = tblViewObj.model().columnCount()
   
   for col,colVal in enumerate(sizeList):
      if colVal > 1:
         fixedCols.append( (col, colVal) )
      else:
         pctCols.append( (col, colVal) )

   for c,sz in fixedCols:
      tblViewObj.horizontalHeader().resizeSection(c, sz)

   totalFixed = sum([sz[1] for sz in fixedCols])
   szRemain = totalWidth-totalFixed
   for c,pct in pctCols:
      tblViewObj.horizontalHeader().resizeSection(c, pct*szRemain)

   tblViewObj.horizontalHeader().setStretchLastSection(True)




class QRichLabel(QLabel):
   def __init__(self, txt, doWrap=True, hAlign=Qt.AlignLeft, vAlign=Qt.AlignVCenter):
      QLabel.__init__(self, txt)
      self.setTextFormat(Qt.RichText)
      self.setWordWrap(doWrap)
      self.setAlignment(hAlign | vAlign)

   def setText(self, text, color=None, size=None, bold=None, italic=None):
      if color:
         text = '<font color="%s">%s</font>' % (htmlColor(color), text)
      if size:
         if isinstance(size, int):
            text = '<font size=%d>%s</font>' % (size, text)
         else:
            text = '<font size="%s">%s</font>' % (size, text)
      if bold:
         text = '<b>%s</b>' % text
      if italic:
         text = '<i>%s</i>' % text

      QLabel.setText(self,text)

   def setBold(self):
      self.setText('<b>' + self.text() + '</b>')
      
   def setItalic(self):
      self.setText('<i>' + self.text() + '</i>')



class QMoneyLabel(QRichLabel):
   def __init__(self, nSatoshi, ndec=8, maxZeros=2, wColor=True, wBold=False):
      QLabel.__init__(self, coin2str(nSatoshi))

      self.setValueText(nSatoshi, ndec, maxZeros, wColor, wBold)


   def setValueText(self, nSatoshi, ndec=None, maxZeros=None, wColor=None, wBold=None):
      """
      When we set the text of the QMoneyLabel, remember previous values unless
      explicitly respecified
      """
      if not ndec==None:
         self.ndec = ndec

      if not maxZeros==None:
         self.max0 = maxZeros

      if not wColor==None:
         self.colr = wColor

      if not wBold==None:
         self.bold = wBold
         

      theFont = GETFONT("Fixed", 10)
      if self.bold:
         theFont.setWeight(QFont.Bold)

      self.setFont(theFont)
      self.setWordWrap(False)
      valStr = coin2str(nSatoshi, ndec=self.ndec, maxZeros=self.max0)
      goodMoney = htmlColor('MoneyPos')
      badMoney  = htmlColor('MoneyNeg')
      if nSatoshi < 0 and self.colr:
         self.setText('<font color=%s>%s</font>' % (badMoney, valStr))
      elif nSatoshi > 0 and self.colr:
         self.setText('<font color=%s>%s</font>' % (goodMoney, valStr))
      else:
         self.setText('%s' % valStr)
      self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

   



class QLabelButton(QLabel):
   mousePressOn = set()

   def __init__(self, txt):
      colorStr = htmlColor('LBtnNormalFG')
      QLabel.__init__(self, '<font color=%s>%s</u></font>' % (colorStr, txt))
      self.plainText = txt
      self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

   
   #def setText(self, txt):
      #colorStr = htmlColor('LBtnNormalFG')
      #QLabel.__init__(self, '<font color=%s>%s</u></font>' % (colorStr, txt))
  
   def sizeHint(self):
      w,h = relaxedSizeStr(self, self.plainText)
      return QSize(w,1.2*h)

   def mousePressEvent(self, ev):  
      # Prevent click-bleed-through to dialogs being opened
      txt = str(self.text())
      self.mousePressOn.add(txt)

   def mouseReleaseEvent(self, ev):  
      txt = str(self.text())
      if txt in self.mousePressOn:
         self.mousePressOn.remove(txt)
         self.emit(SIGNAL('clicked()'))  

   def enterEvent(self, ev):  
      ssStr = "QLabel { background-color : %s }" % htmlColor('LBtnHoverBG')
      self.setStyleSheet(ssStr)

   def leaveEvent(self, ev):
      ssStr = "QLabel { background-color : %s }" % htmlColor('LBtnNormalBG')
      self.setStyleSheet(ssStr)


################################################################################
def createToolTipObject(tiptext, iconSz=2):
   fgColor = htmlColor('ToolTipQ')
   lbl = QLabel('<font size=%d color=%s>(?)</font>' % (iconSz, fgColor))
   lbl.setToolTip('<u></u>' + tiptext)
   lbl.setMaximumWidth(relaxedSizeStr(lbl, '(?)')[0])
   return lbl

   
################################################################################
def MsgBoxCustom(wtype, title, msg, wCancel=False, yesStr=None, noStr=None): 
   """
   Creates a message box with custom button text and icon
   """

   class dlgWarn(QDialog):
      def __init__(self, dtype, dtitle, wmsg, withCancel=False, yesStr=None, noStr=None):
         super(dlgWarn, self).__init__(None)
         
         msgIcon = QLabel()
         fpix = ''
         if dtype==MSGBOX.Good:
            fpix = ':/MsgBox_good48.png'
         if dtype==MSGBOX.Info:
            fpix = ':/MsgBox_info48.png'
         if dtype==MSGBOX.Question:
            fpix = ':/MsgBox_question64.png'
         if dtype==MSGBOX.Warning:
            fpix = ':/MsgBox_warning48.png'
         if dtype==MSGBOX.Critical:
            fpix = ':/MsgBox_critical64.png'
         if dtype==MSGBOX.Error:
            fpix = ':/MsgBox_error64.png'
   
   
         if len(fpix)>0:
            msgIcon.setPixmap(QPixmap(fpix))
            msgIcon.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
   
         lblMsg = QLabel(msg)
         lblMsg.setTextFormat(Qt.RichText)
         lblMsg.setWordWrap(True)
         lblMsg.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
         w,h = tightSizeNChar(lblMsg, 70)
         lblMsg.setMinimumSize( w, 3.2*h )

         buttonbox = QDialogButtonBox()

         if dtype==MSGBOX.Question:
            if not yesStr: yesStr = '&Yes'
            if not noStr:  noStr = '&No'
            btnYes = QPushButton(yesStr)
            btnNo  = QPushButton(noStr)
            self.connect(btnYes, SIGNAL('clicked()'), self.accept)
            self.connect(btnNo,  SIGNAL('clicked()'), self.reject)
            buttonbox.addButton(btnYes,QDialogButtonBox.AcceptRole)
            buttonbox.addButton(btnNo, QDialogButtonBox.RejectRole)
         else:
            if not yesStr: yesStr = '&OK'
            if not noStr:  noStr = '&Cancel'
            btnOk = QPushButton(yesStr)
            self.connect(btnOk, SIGNAL('clicked()'), self.accept)
            buttonbox.addButton(btnOk, QDialogButtonBox.AcceptRole)
            if withCancel:
               btnCancel = QPushButton(noStr)
               self.connect(btnCancel, SIGNAL('clicked()'), self.reject)
               buttonbox.addButton(btnCancel, QDialogButtonBox.RejectRole)
            

         spacer = QSpacerItem(20, 10, QSizePolicy.Fixed, QSizePolicy.Expanding)


         layout = QGridLayout()
         layout.addItem(  spacer,         0,0, 1,2)
         layout.addWidget(msgIcon,        1,0, 1,1)
         layout.addWidget(lblMsg,         1,1, 1,1)
         layout.addWidget(buttonbox,      3,0, 1,2)
         layout.setSpacing(20)
         self.setLayout(layout)
         self.setWindowTitle(dtitle)

   dlg = dlgWarn(wtype, title, msg, wCancel, yesStr, noStr) 
   result = dlg.exec_()
   
   return result


################################################################################
def MsgBoxWithDNAA(wtype, title, msg, dnaaMsg, wCancel=False, yesStr='Yes', noStr='No'):
   """
   Creates a warning/question/critical dialog, but with a "Do not ask again"
   checkbox.  Will return a pair  (response, DNAA-is-checked)
   """

   class dlgWarn(QDialog):
      def __init__(self, dtype, dtitle, wmsg, dmsg=None, withCancel=False): 
         super(dlgWarn, self).__init__(None)
         
         msgIcon = QLabel()
         fpix = ''
         if dtype==MSGBOX.Info:
            fpix = ':/MsgBox_info48.png'
            if not dmsg:  dmsg = 'Do not show this message again'
         if dtype==MSGBOX.Question:
            fpix = ':/MsgBox_question64.png'
            if not dmsg:  dmsg = 'Do not ask again'
         if dtype==MSGBOX.Warning:
            fpix = ':/MsgBox_warning48.png'
            if not dmsg:  dmsg = 'Do not show this warning again'
         if dtype==MSGBOX.Critical:
            fpix = ':/MsgBox_critical64.png'
            if not dmsg:  dmsg = None  # should always show crits
         if dtype==MSGBOX.Error:
            fpix = ':/MsgBox_error64.png'
            if not dmsg:  dmsg = None  # should always show errors
   
   
         if len(fpix)>0:
            msgIcon.setPixmap(QPixmap(fpix))
            msgIcon.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
   
         self.chkDnaa = QCheckBox(dmsg)
         lblMsg = QLabel(msg)
         lblMsg.setTextFormat(Qt.RichText)
         lblMsg.setWordWrap(True)
         lblMsg.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
         w,h = tightSizeNChar(lblMsg, 50)
         lblMsg.setMinimumSize( w, 3.2*h )

         buttonbox = QDialogButtonBox()

         if dtype==MSGBOX.Question:
            btnYes = QPushButton(yesStr)
            btnNo  = QPushButton(noStr)
            self.connect(btnYes, SIGNAL('clicked()'), self.accept)
            self.connect(btnNo,  SIGNAL('clicked()'), self.reject)
            buttonbox.addButton(btnYes,QDialogButtonBox.AcceptRole)
            buttonbox.addButton(btnNo, QDialogButtonBox.RejectRole)

         else:
            btnOk = QPushButton('Ok')
            self.connect(btnOk, SIGNAL('clicked()'), self.accept)
            buttonbox.addButton(btnOk, QDialogButtonBox.AcceptRole)
            if withCancel:
               btnOk = QPushButton('Cancel')
               self.connect(btnOk, SIGNAL('clicked()'), self.reject)
               buttonbox.addButton(btnOk, QDialogButtonBox.RejectRole)
            

         spacer = QSpacerItem(20, 10, QSizePolicy.Fixed, QSizePolicy.Expanding)


         layout = QGridLayout()
         layout.addItem(  spacer,         0,0, 1,2)
         layout.addWidget(msgIcon,        1,0, 1,1)
         layout.addWidget(lblMsg,         1,1, 1,1)
         layout.addWidget(self.chkDnaa,   2,0, 1,2)
         layout.addWidget(buttonbox,      3,0, 1,2)
         layout.setSpacing(20)
         self.setLayout(layout)
         self.setWindowTitle(dtitle)


   dlg = dlgWarn(wtype, title, msg, dnaaMsg, wCancel) 
   result = dlg.exec_()
   
   return (result, dlg.chkDnaa.isChecked())

 
def makeLayoutFrame(dirStr, widgetList, style=QFrame.NoFrame):
   frm = QFrame()
   frm.setFrameStyle(style)

   frmLayout = QHBoxLayout()
   if dirStr.lower().startswith('vert'):
      frmLayout = QVBoxLayout()
      
   for w in widgetList:
      if isinstance(w,str) and w.lower()=='stretch':
         frmLayout.addStretch()
      elif isinstance(w,str) and w.lower().startswith('space'):
         # expect "spacer(30)"
         first = w.index('(')+1 
         last  = w.index(')')
         wid,hgt = int(w[first:last]), 1
         if dirStr.lower().startswith('vert'):
            wid,hgt = hgt,wid
         frmLayout.addItem( QSpacerItem(wid,hgt) )
      elif isinstance(w,str) and w.lower().startswith('line'):
         frmLine = QFrame()
         if dirStr.lower().startswith('vert'):
            frmLine.setFrameStyle(QFrame.HLine | QFrame.Plain)
         else:
            frmLine.setFrameStyle(QFrame.VLine | QFrame.Plain)
         frmLayout.addWidget(frmLine)
      elif isinstance(w,QSpacerItem):
         frmLayout.addItem(w)
      else:
         frmLayout.addWidget(w)

   frmLayout.setContentsMargins(5,5,5,5)
   frm.setLayout(frmLayout)
   return frm
   

def addFrame(widget, style=STYLE_SUNKEN):
   return makeLayoutFrame('Horiz', [widget], style)
   
def makeVertFrame(widgetList, style=QFrame.NoFrame):
   return makeLayoutFrame('Vert', widgetList, style)

def makeHorizFrame(widgetList, style=QFrame.NoFrame):
   return makeLayoutFrame('Horiz', widgetList, style)


def QImageLabel(imgfn, stretch='NoStretch'):
   if not os.path.exists(imgfn):
      raise FileExistsError, 'Image for QImageLabel does not exist!'

   lbl = QLabel()
   lbl.setPixmap(QPixmap(imgfn))
   return lbl
   



def restoreTableView(qtbl, hexBytes):
   try:
      binunpack = BinaryUnpacker(hex_to_binary(hexBytes))
      hexByte = binunpack.get(UINT8)
      binLen = binunpack.get(UINT8)
      toRestore = []
      for i in range(binLen):
         sz = binunpack.get(UINT16)
         if sz>0:
            toRestore.append([i,sz])
         
      for i,c in toRestore[:-1]:
         qtbl.setColumnWidth(i, c)
   except Exception, e:
      print 'ERROR!'
      pass
      # Don't want to crash the program just because couldn't load tbl data


def saveTableView(qtbl):
   nCol = qtbl.model().columnCount()
   sz = [None]*nCol
   for i in range(nCol):
      sz[i] = qtbl.columnWidth(i)      

   # Use 'ff' as a kind of magic byte for this data.  Most importantly
   # we want to guarantee that the settings file will interpret this
   # as hex data -- I once had an unlucky hex string written out with 
   # all digits and then intepretted as an integer on the next load :( 
   first = int_to_hex(nCol)
   rest  = [int_to_hex(s, widthBytes=2) for s in sz]
   return 'ff' + first + ''.join(rest)




class QtBackgroundThread(QThread):
   '''
   Define a thread object that will execute a preparatory function
   (blocking), and then a long processing thread followed by something
   to do when it's done (both non-blocking).  After the 3 methods and 
   their arguments are set, use obj.start() to kick it off.

   NOTE: This is basically just a copy of PyBackgroundThread in
         armoryengine.py, but I needed a version that can access
         Qt elements.  Using vanilla python threads with calls 
         to Qt signals/slots/methods/etc, throws all sorts of errors.
   '''

   def __init__(self, parent, *args, **kwargs):
      QThread.__init__(self, parent)

      self.preFunc  = lambda: ()
      self.postFunc = lambda: ()

      if len(args)==0:
         self.func  = lambda: ()
      else:
         if not hasattr(args[0], '__call__'):
            raise TypeError, ('QtBkgdThread constructor first arg '
                              '(if any) must be a function')
         else:
            self.setThreadFunction(args[0], *args[1:], **kwargs)

   def setPreThreadFunction(self, prefunc, *args, **kwargs):
      def preFuncPartial():
         prefunc(*args, **kwargs)
      self.preFunc = preFuncPartial

   def setThreadFunction(self, thefunc, *args, **kwargs):
      def funcPartial():
         thefunc(*args, **kwargs)
      self.func = funcPartial

   def setPostThreadFunction(self, postfunc, *args, **kwargs):
      def postFuncPartial():
         postfunc(*args, **kwargs)
      self.postFunc = postFuncPartial


   def run(self):
      print 'Executing QThread.run()...'
      self.func()
      self.postFunc()

   def start(self):
      print 'Executing QThread.start()...'
      # This is blocking: we may want to guarantee that something critical 
      #                   is in place before we start the thread
      self.preFunc()
      super(QtBackgroundThread, self).start()




################################################################################
class ArmoryDialog(QDialog):
   def __init__(self, parent=None, main=None):
      super(ArmoryDialog, self).__init__(parent)

      self.parent = parent
      self.main   = main

      self.setFont(GETFONT('var'))

      if USE_TESTNET:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [TESTNET]')
         self.setWindowIcon(QIcon(':/armory_icon_green_32x32.png'))
      else:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [MAIN NETWORK]')
         self.setWindowIcon(QIcon(':/armory_icon_32x32.png'))




class QRCodeWidget(QWidget):

   def __init__(self, asciiToEncode='', prefSize=160, errLevel=QRErrorCorrectLevel.L, parent=None):
      super(QRCodeWidget, self).__init__()

      self.parent = parent
      self.qrmtrx = None
      self.setAsciiData(asciiToEncode, prefSize, errLevel, repaint=False)
      

   def setAsciiData(self, newAscii, prefSize=160, errLevel=QRErrorCorrectLevel.L, repaint=True):
      if len(newAscii)==0:
         self.qrmtrx = [[0]]
         self.modCt  = 1
         self.pxScale= 1
         return

      self.theData = newAscii
      sz=3
      success=False
      while sz<20:
         try:
            self.qr = QRCode(sz, errLevel)
            self.qr.addData(self.theData)
            self.qr.make()
            success=True
            break
         except TypeError:
            sz += 1

      if not success:
         LOGERROR('Unsuccessful attempt to create QR code')
         self.qrmtrx = [[0]]
         return

      self.qrmtrx = []
      self.modCt = self.qr.getModuleCount()
      for r in range(self.modCt):
         tempList = [0]*self.modCt
         for c in range(self.modCt):
            tempList[c] = 1 if self.qr.isDark(r,c) else 0
         self.qrmtrx.append(tempList)

      self.setPreferredSize(prefSize)


      
            
   def getModuleCount1D(self):
      return self.modCt


   def setPreferredSize(self, px, policy='Approx'):
      self.pxScale,rem = divmod(int(px), int(self.modCt))

      if policy.lower().startswith('approx'):
         if rem>self.modCt/2.0:
            self.pxScale += 1
      elif policy.lower().startswith('atleast'):
         if rem>0:
            self.pxScale += 1
      elif policy.lower().startswith('max'):
         pass
      else:
         LOGERROR('Bad size policy in set qr size')
         return self.pxScale*self.modCt

      return
      

   def getSize(self):
      return self.pxScale*self.modCt

       
   def sizeHint(self):
      sz1d = self.pxScale*self.modCt
      return QSize(sz1d, sz1d)


   def paintEvent(self, e):
      qp = QPainter()
      qp.begin(self)
      self.drawWidget(qp)
      qp.end()



   def drawWidget(self, qp):
      # In case this is not a white background, draw the white boxes
      qp.setPen(QColor(255,255,255))
      qp.setBrush(QColor(255,255,255))
      for r in range(self.modCt):
         for c in range(self.modCt):
            if not self.qrmtrx[c][r]:
               qp.drawRect(*[a*self.pxScale for a in [r,c,1,1]])

      # Draw the black tiles
      qp.setPen(QColor(0,0,0))
      qp.setBrush(QColor(0,0,0))
      for r in range(self.modCt):
         for c in range(self.modCt):
            if self.qrmtrx[c][r]:
               qp.drawRect(*[a*self.pxScale for a in [r,c,1,1]])


   def mouseDoubleClickEvent(self, *args):
      DlgInflatedQR(self.parent, self.theData).exec_()
            
            
# Create a very simple dialog and execute it
class DlgInflatedQR(ArmoryDialog):
   def __init__(self, parent, dataToQR):
      super(DlgInflatedQR, self).__init__(parent)

      sz = QApplication.desktop().size()
      w,h = sz.width(), sz.height()
      qrSize = int(min(w,h)*0.8)
      qrDisp = QRCodeWidget(dataToQR, prefSize=qrSize)

      def closeDlg(*args): 
         self.accept()
      qrDisp.mouseDoubleClickEvent = closeDlg
      self.mouseDoubleClickEvent = closeDlg

      lbl = QRichLabel('<b>Double-click or press ESC to close</b>')
      lbl.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

      frmQR = makeHorizFrame(['Stretch', qrDisp, 'Stretch'])
      frmFull = makeVertFrame(['Stretch',frmQR, lbl, 'Stretch'])

      layout = QVBoxLayout()
      layout.addWidget(frmFull)

      self.setLayout(layout)
      self.showFullScreen()
      





# Pure-python BMP creator taken from:
#
#     http://pseentertainmentcorp.com/smf/index.php?topic=2034.0
#
# This will take a 2D array of ones-and-zeros and convert it to a binary
# bitmap image, which will be stored in a temporary file.  This temporary
# file can be used for display and copy-and-paste into email.

def bmp_binary(header, pixels):
   '''It takes a header (based on default_bmp_header), 
   the pixel data (from structs, as produced by get_color and row_padding),
   and writes it to filename'''
   header_str = ""
   header_str += struct.pack('<B', header['mn1'])
   header_str += struct.pack('<B', header['mn2'])
   header_str += struct.pack('<L', header['filesize'])
   header_str += struct.pack('<H', header['undef1'])
   header_str += struct.pack('<H', header['undef2'])
   header_str += struct.pack('<L', header['offset'])
   header_str += struct.pack('<L', header['headerlength'])
   header_str += struct.pack('<L', header['width'])
   header_str += struct.pack('<L', header['height'])
   header_str += struct.pack('<H', header['colorplanes'])
   header_str += struct.pack('<H', header['colordepth'])
   header_str += struct.pack('<L', header['compression'])
   header_str += struct.pack('<L', header['imagesize'])
   header_str += struct.pack('<L', header['res_hor'])
   header_str += struct.pack('<L', header['res_vert'])
   header_str += struct.pack('<L', header['palette'])
   header_str += struct.pack('<L', header['importantcolors'])
   return header_str + pixels

def bmp_write(header, pixels, filename):
   out = open(filename, 'wb')
   out.write(bmp_binary(header, pixels))
   out.close()

def bmp_row_padding(width, colordepth):
   '''returns any necessary row padding'''
   byte_length = width*colordepth/8
   # how many bytes are needed to make byte_length evenly divisible by 4?
   padding = (4-byte_length)%4 
   padbytes = ''
   for i in range(padding):
      x = struct.pack('<B',0)
      padbytes += x
   return padbytes

def bmp_pack_color(red, green, blue):
   '''accepts values from 0-255 for each value, returns a packed string'''
   return struct.pack('<BBB',blue,green,red)


###################################   
BMP_TEMPFILE = -1
def createBitmap(imgMtrx2D, writeToFile=-1, returnBinary=True):
   try:
      h,w = len(imgMtrx2D), len(imgMtrx2D[0])
   except:
      LOGERROR('Error creating BMP object')
      raise

   header = {'mn1':66,
             'mn2':77,
             'filesize':0,
             'undef1':0,
             'undef2':0,
             'offset':54,
             'headerlength':40,
             'width':w,
             'height':h,
             'colorplanes':0,
             'colordepth':24,
             'compression':0,
             'imagesize':0,
             'res_hor':0,
             'res_vert':0,
             'palette':0,
             'importantcolors':0}

   pixels = ''
   black = bmp_pack_color(  0,  0,  0)
   white = bmp_pack_color(255,255,255)
   for row in range(header['height']-1,-1,-1):# (BMPs are L to R from the bottom L row)
      for col in range(header['width']):
         pixels += black if imgMtrx2D[row][col] else white
      pixels += bmp_row_padding(header['width'], header['colordepth'])
      
   if returnBinary:
      return bmp_binary(header,pixels)
   elif writeToFile==BMP_TEMPFILE:
      handle,temppath = mkstemp(suffix='.bmp')
      bmp_write(header, pixels, temppath)
      return temppath
   else:
      try:
         bmp_write(header, pixels, writeToFile)
         return True
      except:
         return False
      


