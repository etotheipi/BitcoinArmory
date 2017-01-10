##############################################################################
#                                                                            #
# Copyright (C) 2016-17, goatpig                                             #
#  Distributed under the MIT license                                         #
#  See LICENSE-MIT or https://opensource.org/licenses/MIT                    #                                   
#                                                                            #
##############################################################################

from PyQt4.QtGui import QFrame
from PyQt4.QtCore import Qt
import time

from qtdefines import ArmoryDialog, QLabel, QGridLayout, \
   SIGNAL, STYLE_RAISED, QRichLabel
   
from armoryengine.ArmoryUtils import PyBackgroundThread

class WalletComparisonClass(object):
   
   def __init__(self, main):
      self.main = main
      
   def checkWallets(self):   
      #compare with loaded python wallets
      walletsToMirror = []
      walletsToSync = []
      for wltID in self.main.walletMap:
         if not self.main.walletManager.hasWallet(wltID):
            #if python wallet id is missing from cpp wallet map, 
            #flag it for mirroring
            walletsToMirror.append(wltID)
            continue
         
         wlt = self.main.walletMap[wltID]
         lastComputed = self.main.walletManager.getLastComputedIndex(wltID)
         if lastComputed < wlt.lastComputedChainIndex:
            #if python wallet has more computed addresses than cpp 
            #wallet, mark it for synchronizing
            walletsToSync.append(wltID)
            
         #TODO: check for imports
         
      if len(walletsToMirror) + len(walletsToSync) > 0:
         self.updateCppWallets(walletsToMirror, walletsToSync)
   
   def updateCppWallets(self, mirrorList, syncList):
      #construct GUI
      mirrorWalletDlg = MirrorWalletsDialog(self.main, self.main)
      
      def updateStatusText(text):
         mirrorWalletDlg.setStatusText(text)
      
      thr = PyBackgroundThread(self.walletComputation,
                               mirrorList, syncList, updateStatusText)
      thr.start()
      
      mirrorWalletDlg.exec_()
      thr.join()
      
   def walletComputation(self, mirrorList, syncList, reportTextProgress):
      
      #mirror missing wallets
      for wltID in mirrorList:
         reportTextProgress("Mirroring wallet %s" % wltID)
         
         wlt = self.main.walletMap[wltID]
         rootEntry = wlt.addrMap['ROOT']
         
         self.main.walletManager.duplicateWOWallet(\
            rootEntry.binPublicKey65, rootEntry.chaincode,\
            wlt.lastComputedChainIndex + 1)
         
      #synchronize lagging wallets
      for wltID in syncList:
         reportTextProgress("Synchronizing wallet %s", wltID)
         
         wlt = self.main.walletMap[wltID]
         self.main.walletManager.synchronizeWallet(
            wltID, wlt.lastComputedIndex)
         
      reportTextProgress('shutdown')
         

class MirrorWalletsDialog(ArmoryDialog):
   
   def __init__(self, parent, main):
      super(MirrorWalletsDialog, self).__init__(parent, main)
      
      self.progressText = ""
      self.counter = 1
      self.progress = False
      self.progressThr = None
      
      self.setWindowFlags(Qt.Dialog)
      
      infoLabel = QRichLabel('''
      Starting v0.96, Armory needs to mirror Python
      wallets into C++ wallets in order to operate. Mirrored C++ wallets
      are watching only (they do not hold any private keys).<br><br>
            
      Mirrored wallets are used to interface with the database and perform
      operations that aren't available to the legacy Python wallets, such
      support for compressed public keys and Segregated Witness transactions.
      <br><br>
      
      Mirroring operation only needs to happen once per wallet. Synchronization
      will happen every time the Python wallet address chain is ahead of the 
      mirrored Cpp wallet address chain (this typically rarely happens).
      <br><br>
      
      This process can take up to a few minutes.<br><br>
      '''
       )
      
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
      
      self.setWindowTitle('Mirroring Wallets')
      self.setLayout(layout)
      
      self.setMinimumWidth(500)
      self.setFocus() 
      
      #self.startProgressThread()
      
   def updateProgressStatus(self):
      count = 1
      while self.progress:
         time.sleep(0.2)
         if count % 5 == 0:
            self.buildProgressText()
            
         count += 1
      
   def setStatusText(self, text):
      if text == 'shutdown':
         self.stopProgressThread()
         self.signalTerminateDialog()
      else:
         self.stopProgressThread()
         self.startProgressThread()         
         self.progressText = text
         self.counter = 1
         self.buildProgressText()

      
   def buildProgressText(self):
      text = self.progressText
      dotCount = self.counter % 5
      self.counter += 1
      
      dots = '.' * dotCount
      text += dots
      self.emit(SIGNAL('UpdateTextStatus'), text)
      
   def updateTextStatus(self, text):
      self.statusLabel.setText(text)
      
   def signalTerminateDialog(self):
      self.emit(SIGNAL('TerminateDlg'), None)
      
   def shutdown(self):
      self.stopProgressThread()
      self.reject()
      
   def startProgressThread(self):
      self.progress = True
      self.progressThr = PyBackgroundThread(self.updateProgressStatus)
      self.progressThr.start()
      
   def stopProgressThread(self):
      if self.progressThr == None:
         return
      
      self.progress = False
      self.progressThr.join()
      self.progressThr = None