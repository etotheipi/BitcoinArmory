from armoryengine import *
from PyQt4.QtCore import *
from PyQt4.QtGui  import *

SETTINGS_PATH = os.path.join(ARMORY_HOME_DIR, 'ArmorySettings.txt')
USERMODE = enum('Standard', 'Advanced', 'Developer')
ARMORYMODE = enum('WITH_BLOCKCHAIN', 'WALLET_ONLY')
WLTTYPES = enum('Plain', 'Crypt', 'WatchOnly', 'Offline')
WLTFIELDS = enum('Name', 'Descr', 'WltID', 'NumAddr', 'Secure', \
                    'BelongsTo', 'Crypto', 'Time', 'Mem')
MSGBOX = enum('Info', 'Question', 'Warning', 'Critical', 'Error')
 

Colors = enum(LightBlue=   QColor(215,215,255), \
              LightGreen=  QColor(225,255,225), \
              LightGray=   QColor(235,235,235), \
              MidGray=     QColor(170,170,170), \
              Gray=        QColor(128,128,128), \
              DarkGray=    QColor( 64, 64, 64), \
              Green=       QColor(  0,100,  0), \
              DarkRed=     QColor( 75,  0,  0), \
              Red=         QColor(200, 50, 50), \
              LightRed=    QColor(255,100,100), \
              Black=       QColor(  0,  0,  0)  \
                                                 )

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

def tightSizeStr(obj, theStr):
   """ Measure a specific string """
   try:
      fm = QFontMetricsF(QFont(obj.font()))
   except AttributeError:
      fm = QFontMetricsF(QFont(obj))
   szWidth,szHeight = fm.boundingRect(theStr).width(), fm.height()
   return szWidth, szHeight
   
def relaxedSizeStr(obj, theStr):
   """
   Approximates the size of a row text, nchars long, adds some margin
   """
   try:
      fm = QFontMetricsF(QFont(obj.font()))
   except AttributeError:
      fm = QFontMetricsF(QFont(obj))
   szWidth,szHeight = fm.boundingRect(theStr).width(), fm.height()
   return 1.3*szWidth, 1.3*szHeight

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
   return 1.3*szWidth, 1.5*szHeight

#############################################################################
def determineWalletType(wlt, wndw):
   if wlt.watchingOnly:
      if wndw.getWltExtraProp(wlt.uniqueIDB58,'IsMine'):
         return [WLTTYPES.Offline, 'Offline']
      else:
         return [WLTTYPES.WatchOnly, 'Watching-Only']
   elif wlt.useEncryption:
      return [WLTTYPES.Crypt, 'Encrypted']
   else:
      return [WLTTYPES.Plain, 'No Encryption']




def initialColResize(tblViewObj, sizeList):
   """
   Use a dictionary to communicate appropriate sizes, such as:
      [  ('Fixed',    50)   # pixels
         ('Fixed',   200)   # pixels
         ('Percent', 0.3)   # percent of remaining width
         ('Percent', 0.7) ]
   We assume that all percentages are below 1, all fixed >1.  Thus
   we dont' even need the labels...
   """   
   totalWidth = tblViewObj.width()
   fixedCols, pctCols = [],[]

   nCols = tblViewObj.model().columnCount()
   #totalWidth = sum([tblViewObj.horizontalHeader().sectionSize(c) for c in range(nCols)])
   
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


      

def color_to_style_str(c):
   return '#%s%s%s' % (int_to_hex(c.red()), int_to_hex(c.green()), int_to_hex(c.blue()))


class QRichLabel(QLabel):
   def __init__(self, txt, doWrap=True):
      QLabel.__init__(self, txt)
      self.setTextFormat(Qt.RichText)
      self.setWordWrap(doWrap)


class QLabelButton(QLabel):

   def __init__(self, txt, colorOn=Colors.LightBlue):  
      QLabel.__init__(self, '<font color=#00009f><u>'+txt+'</u></font>')  
      self.plainText = txt
      self.bgColorOffStr = color_to_style_str(QApplication.palette().window().color())
      self.bgColorOnStr  = color_to_style_str(QColor(colorOn))
      self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

   def setText(self, txt):
      QLabel.setText(self, '<font color=#00009f><u>'+txt+'</u></font>')  
  
   def sizeHint(self):
      w,h = relaxedSizeStr(self, self.plainText)
      return QSize(w,1.2*h)

   def mouseReleaseEvent(self, ev):  
      self.emit(SIGNAL('clicked()'))  

   def enterEvent(self, ev):  
      ssStr = "QLabel { background-color : %s }" % self.bgColorOnStr
      self.setStyleSheet(ssStr)

   def leaveEvent(self, ev):
      ssStr = "QLabel { background-color : %s }" % self.bgColorOffStr
      self.setStyleSheet(ssStr)


################################################################################
def createToolTipObject(tiptext, iconSz=2):
   lbl = QLabel('<font size=%d color="blue"><u>(?)</u></font>' % iconSz)
   lbl.setToolTip('<u></u>' + tiptext)
   lbl.setMaximumWidth(relaxedSizeStr(lbl, '(?)')[0])
   return lbl

   

################################################################################
def MsgBoxWithDNAA(wtype, title, msg, dnaaMsg, wCancel=False): 
   """
   Creates a warning/question/critical dialog, but with a "Do not ask again"
   checkbox.  Will return a pair  (response, DNAA-is-checked)
   """
   

   class dlgWarn(QDialog):
      def __init__(self, dtype, dtitle, wmsg, dmsg, withCancel=False): 
         super(dlgWarn, self).__init__(None)
         
         msgIcon = QLabel()
         fpix = ''
         if dtype==MSGBOX.Info:
            fpix = 'img/MsgBox_info64.png'
            if not dmsg:  dmsg = 'Do not show this message again'
         if dtype==MSGBOX.Question:
            fpix = 'img/MsgBox_question64.png'
            if not dmsg:  dmsg = 'Do not ask again'
         if dtype==MSGBOX.Warning:
            fpix = 'img/MsgBox_warning64.png'
            if not dmsg:  dmsg = 'Do not show this warning again'
         if dtype==MSGBOX.Critical:
            fpix = 'img/MsgBox_critical64.png'
            if not dmsg:  dmsg = None  # should always show crits
         if dtype==MSGBOX.Error:
            fpix = 'img/MsgBox_error64.png'
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

 
def makeLayoutStrip(dirStr, widgetList, style=QFrame.NoFrame):
   frm = QFrame()
   frm.setFrameStyle(style)

   frmLayout = QHBoxLayout()
   if dirStr.lower().startswith('vert'):
      frmLayout = QVBoxLayout()
      
   for w in widgetList:
      if isinstance(w,str) and w.lower()=='stretch':
         frmLayout.addStretch()
      elif isinstance(w,QSpacerItem):
         frmLayout.addItem(w)
      else:
         frmLayout.addWidget(w)

   frm.setLayout(frmLayout)
   return frm
   

   


