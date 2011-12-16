import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qtdefines import *

from armoryengine import *
from armorymodels import *


def color_to_style_str(c):
   return '#%s%s%s' % (int_to_hex(c.red()), int_to_hex(c.green()), int_to_hex(c.blue()))

class QLabelButton(QLabel):

   def __init__(self, txt, colorOn=Colors.LightBlue):  
      QLabel.__init__(self, txt)  
      self.bgColorOffStr = color_to_style_str(QApplication.palette().window().color())
      self.bgColorOnStr  = color_to_style_str(QColor(colorOn))
      w,h = relaxedSizeStr(self, txt)
      self.setMaximumSize(w,1.2*h)
  
   def mouseReleaseEvent(self, ev):  
      self.emit(SIGNAL('clicked()'))  

   def enterEvent(self, ev):  
      ssStr = "QLabel { background-color : %s }" % self.bgColorOnStr
      self.setStyleSheet(ssStr)

   def leaveEvent(self, ev):
      ssStr = "QLabel { background-color : %s }" % self.bgColorOffStr
      self.setStyleSheet(ssStr)
