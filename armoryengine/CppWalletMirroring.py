##############################################################################
#                                                                            #
# Copyright (C) 2016-17, goatpig                                             #
#  Distributed under the MIT license                                         #
#  See LICENSE-MIT or https://opensource.org/licenses/MIT                    #                                   
#                                                                            #
##############################################################################
STATUS_MIRROR = 1
STATUS_SYNC = 2
STATUS_IMPORTS = 3
STATUS_DONE = 4

from armoryengine.ArmoryUtils import LOGINFO

class WalletMirroringClass(object):
   
   ###########################################################################
   def __init__(self, pyWalletMap, walletManagerObj):
      self.pyWalletMap = pyWalletMap
      self.walletManagerObj = walletManagerObj
   
   ###########################################################################   
   def checkWallets(self):   
      #compare with loaded python wallets
      walletsToMirror = []
      walletsToSync = []
      importsToCheck = []
      for wltID in self.pyWalletMap:
         wlt = self.pyWalletMap[wltID]
         
         if len(wlt.importList) > 0:
            importsToCheck.append(wltID)
         
         if not self.walletManagerObj.hasWallet(wltID):
            #if python wallet id is missing from cpp wallet map, 
            #flag it for mirroring
            walletsToMirror.append(wltID)
            continue
         
         lastComputed = self.walletManagerObj.getLastComputedIndex(wltID)
         if lastComputed < wlt.lastComputedChainIndex:
            #if python wallet has more computed addresses than cpp 
            #wallet, mark it for synchronizing
            walletsToSync.append(wltID)
                    
      if len(walletsToMirror) + len(walletsToSync) + len(importsToCheck) > 0:
         self.updateCppWallets(walletsToMirror, walletsToSync, importsToCheck)
   
   ###########################################################################
   def updateCppWallets(self, mirrorList, syncList, importList):
      
      def updateStatus(statusCode, wltId):
         if statusCode == STATUS_MIRROR:
            LOGINFO("Mirroring wallet %s" % wltId)
         elif statusCode == STATUS_SYNC:
            LOGINFO("Synchronizing wallet %s" % wltId)
         elif statusCode == STATUS_IMPORTS:
            LOGINFO("Checking imports for wallet %s" % wltId)
         elif statusCode == STATUS_DONE:
            LOGINFO("Done mirroring python wallets")
      
      self.walletComputation(
         mirrorList, syncList, importList, updateStatus)

      
   ###########################################################################   
   def walletComputation(\
         self, mirrorList, syncList, importList, reportProgress):
      
      #mirror missing wallets
      for wltID in mirrorList:
         reportProgress(STATUS_MIRROR, wltID)
         
         wlt = self.pyWalletMap[wltID]
         rootEntry = wlt.addrMap['ROOT']
         
         self.walletManagerObj.duplicateWOWallet(\
            rootEntry.binPublicKey65, rootEntry.chaincode,\
            wlt.lastComputedChainIndex + 1)
         
      #synchronize wallets
      for wltID in syncList:
         reportProgress(STATUS_SYNC, wltID)
         
         wlt = self.pyWalletMap[wltID]
         self.walletManagerObj.synchronizeWallet(
            wltID, wlt.lastComputedChainIndex)
         
      for wltID in importList:
         reportProgress(STATUS_IMPORTS, wltID)
         
         wlt = self.pyWalletMap[wltID]
         for importId in wlt.importList:
            scrAddr = wlt.linearAddr160List[importId]
            addrObj = wlt.addrMap[scrAddr]
            
            self.walletManagerObj.setImport(\
               wltID, importId, addrObj.getPubKey())
         
      reportProgress(STATUS_DONE, "")