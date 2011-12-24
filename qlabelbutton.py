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
      QLabel.__init__(self, '<font color=#00009f><u>'+txt+'</u></font>')  
      self.plainText = txt
      self.bgColorOffStr = color_to_style_str(QApplication.palette().window().color())
      self.bgColorOnStr  = color_to_style_str(QColor(colorOn))

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




