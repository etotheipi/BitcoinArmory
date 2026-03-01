##############################################################################
#                                                                            #
# Copyright (C) 2016-17, goatpig                                             #
#  Distributed under the MIT license                                         #
#  See LICENSE-MIT or https://opensource.org/licenses/MIT                    #                                   
#                                                                            #
##############################################################################

from PyQt4.QtGui import QFrame
from PyQt4.QtCore import Qt, QObject
import time

from qtdefines import ArmoryDialog, QLabel, QGridLayout, \
   SIGNAL, STYLE_RAISED, QRichLabel
   
from armoryengine.ArmoryUtils import PyBackgroundThread
from armoryengine.CppWalletMirroring import WalletMirroringClass, \
   STATUS_MIRROR, STATUS_SYNC, STATUS_IMPORTS, STATUS_DONE

##############################################################################
class WalletComparisonClass(WalletMirroringClass):
   
   ###########################################################################
   def __init__(self, main):
      super(WalletComparisonClass, self).__init__(\
         main.walletMap, main.walletManager)
      self.main = main
   
   ###########################################################################
   def updateCppWallets(self, mirrorList, syncList, importList):
      #construct GUI
      mirrorWalletDlg = MirrorWalletsDialog(self.main, self.main)
      
      def updateStatus(statusCode, wltId):
         mirrorWalletDlg.setStatus(statusCode, wltId)
      
      thr = PyBackgroundThread(self.walletComputation,
                        mirrorList, syncList, importList, updateStatus)
      thr.start()
      
      mirrorWalletDlg.exec_()
      thr.join()
            
         
##############################################################################
class MirrorWalletsDialog(ArmoryDialog):
   
   ###########################################################################
   def __init__(self, parent, main):
      super(MirrorWalletsDialog, self).__init__(parent, main)
      
      self.progressText = ""
      self.counter = 1
      self.progress = False
      self.progressThr = None
      
      self.setWindowFlags(Qt.Dialog)
      
      infoLabel = QRichLabel(self.tr(
      'Starting v0.96, Armory needs to mirror Python '
      'wallets into C++ wallets in order to operate. Mirrored C++ wallets '
      'are watching only (they do not hold any private keys).<br><br> '
      'Mirrored wallets are used to interface with the database and perform '
      'operations that aren\'t available to the legacy Python wallets, such '
      'support for compressed public keys and Segregated Witness transactions. '
      '<br><br>'      
      'Mirroring only needs to happen once per wallet. Synchronization '
      'will happen every time the Python wallet address chain is ahead of the '
      'mirrored Cpp wallet address chain (this typically rarely happens).'
      '<br><br>'      
      'This process can take up to a few minutes per wallet.<br><br>'))
      
      self.statusLabel = QLabel('...')     
      self.statusLabel.setAlignment(Qt.AlignCenter | Qt.AlignVCenter) 
      
      frmProgress = QFrame()
      frmProgress.setFrameStyle(STYLE_RAISED)
      progressLayout = QGridLayout()
      progressLayout.addWidget(self.statusLabel, 0, 0, 1, 1)
      frmProgress.setLayout(progressLayout)
      
      self.connect(self, SIGNAL('UpdateTextStatus'), self.updateTextStatus)
      self.connect(self, SIGNAL('TerminateDlg'), self.shutdown)
      
      layout = QGridLayout()
      layout.addWidget(infoLabel, 0, 0, 3, 1)
      layout.addWidget(frmProgress, 3, 0, 1, 1)
      
      self.setWindowTitle(self.tr('Mirroring Wallets'))
      self.setLayout(layout)
      
      self.setMinimumWidth(500)
      self.setFocus() 
   
   ###########################################################################  
   def updateProgressStatus(self):
      count = 1
      while self.progress:
         time.sleep(0.2)
         if count % 5 == 0:
            self.buildProgressText()
            
         count += 1
    
   ###########################################################################   
   def setStatus(self, statusCode, wltId):
      if statusCode == STATUS_DONE:
         self.stopProgressThread()
         self.signalTerminateDialog()
      else:
         self.stopProgressThread()
         self.startProgressThread()         
         self.progressStatus = statusCode
         self.progressId = wltId
         self.counter = 1
         self.buildProgressText()

   ###########################################################################   
   def buildProgressText(self):
      text = ""
      if self.progressStatus == STATUS_MIRROR:
         text = QObject().tr("Mirroring wallet %1").arg(self.progressId)
      elif self.progressStatus == STATUS_SYNC:
         text = QObject().tr("Synchronizing wallet %1").arg(self.progressId)
      elif self.progressStatus == STATUS_IMPORTS:
         text = QObject().tr("Checking imports for wallet %1").arg(self.progressId)
               
      dotCount = self.counter % 5
      self.counter += 1
      
      dots = '.' * dotCount
      text += dots
      self.emit(SIGNAL('UpdateTextStatus'), text)
   
   ###########################################################################   
   def updateTextStatus(self, text):
      self.statusLabel.setText(text)
   
   ###########################################################################   
   def signalTerminateDialog(self):
      self.emit(SIGNAL('TerminateDlg'), None)
   
   ###########################################################################   
   def shutdown(self):
      self.stopProgressThread()
      self.reject()
   
   ###########################################################################   
   def startProgressThread(self):
      self.progress = True
      self.progressThr = PyBackgroundThread(self.updateProgressStatus)
      self.progressThr.start()
   
   ###########################################################################   
   def stopProgressThread(self):
      if self.progressThr == None:
         return
      
      self.progress = False
      self.progressThr.join()
      self.progressThr = None
