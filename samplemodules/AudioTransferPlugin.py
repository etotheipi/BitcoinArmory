from PyQt4.Qt import QPushButton, SIGNAL, QTextEdit, QScrollArea, QTabWidget

from qtdefines import QRichLabel, makeHorizFrame, GETFONT, relaxedSizeNChar, \
   makeVertFrame, NETWORKMODE
from PyQt4 import QtGui

import StringIO
import logging
import zlib

from amodem import recv, send, audio
from amodem import main as mainAudio
from amodem.config import bitrates


BITRATE = 48
CONFIG = bitrates.get(int(BITRATE))
AUDIO_INTERFACE = audio.Interface(config=CONFIG)
AUDIO_LIBRARY = "libportaudio.so"
level, fmt = ('DEBUG', '%(asctime)s %(levelname)-10s '
              '%(message)-100s '
              '%(filename)s:%(lineno)d')
logging.basicConfig(level=level, format=fmt)


class PluginObject(object):

   tabName = 'Audio Transfer'
   maxVersion = '0.93.99'
   
   #############################################################################
   def __init__(self, main):
      self.main = main
      mode = self.main.netMode

      self.debugWindow = self.createDebug()

      def sendAudio():
         with AUDIO_INTERFACE.load(AUDIO_LIBRARY):
            src = StringIO.StringIO(self.debugWindow.toPlainText())
            dst = AUDIO_INTERFACE.player()
            mainAudio.send(CONFIG, src=src, dst=dst)

      def receiveAudio():
         with AUDIO_INTERFACE.load(AUDIO_LIBRARY):
            src = AUDIO_INTERFACE.recorder()
            dst = StringIO.StringIO()
            mainAudio.recv(CONFIG, src=src, dst=dst)
            self.debugWindow.setText(dst.getvalue())


      lblHeader = QRichLabel(tr("""<b>Audio TX Transfer</b>"""), doWrap=False)
      self.sendButton = QPushButton("Send To Audio")
      self.receiveButton = QPushButton("Receive From Audio")

      self.main.connect(self.sendButton, SIGNAL('clicked()'), sendAudio)
      self.main.connect(self.receiveButton, SIGNAL('clicked()'), receiveAudio)

      topRow =  makeHorizFrame([lblHeader, self.sendButton, self.receiveButton, 'stretch'])
      
      self.logFrame = makeVertFrame([topRow, self.debugWindow])

      # Now set the scrollarea widget to the layout
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(self.logFrame)

   def createDebug(self):
      debugWindow = QTextEdit()
      debugWindow.setFont(GETFONT('Fixed', 8))
      w,h = relaxedSizeNChar(debugWindow, 68)[0], int(12 * 8.2)
      debugWindow.setMinimumWidth(w)
      debugWindow.setMinimumHeight(h)
      return debugWindow

   #############################################################################
   def getTabToDisplay(self):
      return self.tabToDisplay


