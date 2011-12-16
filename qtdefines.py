from armoryengine import *
from PyQt4.QtCore import *
from PyQt4.QtGui  import *

SETTINGS_PATH = os.path.join(ARMORY_HOME_DIR, 'ArmorySettings.txt')
USERMODE = enum('Standard', 'Advanced', 'Developer')
WLTTYPES = enum('Plain', 'Crypt', 'WatchOnly', 'Offline')
WLTFIELDS = enum('Name', 'Descr', 'WltID', 'NumAddr', 'Secure', \
                    'BelongsTo', 'Crypto', 'Time', 'Mem')
 

Colors = enum(LightBlue=   QColor(215,215,255), \
              LightGreen=  QColor(225,255,225), \
              LightGray=   QColor(235,235,235), \
              LighterGray= QColor(245,245,245), \
              DarkGray=    QColor( 64, 64, 64), \
              Green=       QColor(  0,100,  0), \
              Red=         QColor(100,  0,  0), \
              Black=       QColor(  0,  0,  0)  \
                                                 )

def tightSizeNChar(obj, nChar):
   """ 
   Approximates the size of a row text of mixed characters

   This is only aproximate, since variable-width fonts will vary
   depending on the specific text
   """

   fm = QFontMetricsF(QFont(obj.font()))
   szWidth,szHeight = fm.boundingRect('abcfgijklm').width(), fm.height()
   szWidth = int(szWidth * nChar/10.0 + 0.5)
   return szWidth, szHeight

def tightSizeStr(obj, theStr):
   """ Measure a specific string """
   fm = QFontMetricsF(QFont(obj.font()))
   szWidth,szHeight = fm.boundingRect(theStr).width(), fm.height()
   return szWidth, szHeight
   
def relaxedSizeStr(obj, theStr):
   """
   Approximates the size of a row text, nchars long, adds some margin
   """
   fm = QFontMetricsF(QFont(obj.font()))
   szWidth,szHeight = fm.boundingRect(theStr).width(), fm.height()
   return 1.3*szWidth, 1.3*szHeight

def relaxedSizeNChar(obj, nChar):
   """
   Approximates the size of a row text, nchars long, adds some margin
   """
   fm = QFontMetricsF(QFont(obj.font()))
   szWidth,szHeight = fm.boundingRect('abcfg ijklm').width(), fm.height()
   szWidth = int(szWidth * nChar/10.0 + 0.5)
   return 1.3*szWidth, 1.5*szHeight

#############################################################################
def determineWalletType(wlt, wndw):
   if wlt.watchingOnly:
      if wndw.getWltExtraProp(wlt.wltUniqueIDB58,'IsMine'):
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


      
   
      

   


