# This is a sample plugin file that will be used to create a new tab 
# in the Armory main window.  All plugin files (such as this one) will 
# be injected with the globals() from ArmoryQt.py, which includes pretty
# much all of Bitcoin & Armory related stuff that you need.  So this 
# file can use any utils or objects accessible to functions in ArmoryQt.py.
from PyQt4.Qt import QPushButton, SIGNAL, QTextEdit, QScrollArea, QTabWidget

from armoryengine.ArmoryUtils import getLastBytesOfFile, ARMORY_LOG_FILE,\
   ARMCPP_LOG_FILE
from qtdefines import QRichLabel, makeHorizFrame, GETFONT, relaxedSizeNChar, \
   makeVertFrame
from PyQt4 import QtGui


# ArmoryQt will access this by importing PluginObject and initializing one
#   -- It adds plugin.getTabToDisplay() to the main window tab list
#   -- It uses plugin.tabName as the label for that tab.
#
# Make sure you test your plugin not only when it's online, but also when
#   -- Armory is in offline mode, and internet is not accessible
#   -- Armory is in offline mode, and internet *is* accessible
#   -- User uses skip-offline-check so online, but service can't be reached
class PluginObject(object):

   tabName = 'Armory Log'
   maxVersion = '0.92'
   
   #############################################################################
   def __init__(self, main):

      self.main = main


      def updateLogDisplay():
         self.pyLogTextDisplay.setText(getLastBytesOfFile(ARMORY_LOG_FILE))
         self.pyLogTextDisplay.moveCursor(QtGui.QTextCursor.End)
         self.cppLogTextDisplay.setText(getLastBytesOfFile(ARMCPP_LOG_FILE))
         self.cppLogTextDisplay.moveCursor(QtGui.QTextCursor.End)

      lblHeader    = QRichLabel(tr("""<b>Log File Display</b>"""), doWrap=False)
      self.updateButton = QPushButton("Update")
      self.main.connect(self.updateButton, SIGNAL('clicked()'), updateLogDisplay)
      topRow =  makeHorizFrame([lblHeader, self.updateButton, 'stretch'])
      
      self.pyLogTextDisplay = self.createLogDisplay()
      self.cppLogTextDisplay = self.createLogDisplay()
      logTabPanel = QTabWidget()
      logTabPanel.addTab(self.pyLogTextDisplay, "Python Log")
      logTabPanel.addTab(self.cppLogTextDisplay, "C++ Log")
      

      self.logFrame = makeVertFrame([topRow, logTabPanel ])

      # Now set the scrollarea widget to the layout
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(self.logFrame)
      updateLogDisplay()

   def createLogDisplay(self):
      logTextDisplay = QTextEdit()
      logTextDisplay.setFont(GETFONT('Fixed', 8))
      w,h = relaxedSizeNChar(logTextDisplay, 68)[0], int(12 * 8.2)
      logTextDisplay.setMinimumWidth(w)
      logTextDisplay.setMinimumHeight(h)
      logTextDisplay.setReadOnly(True)
      return logTextDisplay

   #############################################################################
   def getTabToDisplay(self):
      return self.tabToDisplay


