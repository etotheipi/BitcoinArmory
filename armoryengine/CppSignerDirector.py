################################################################################
##                                                                            ##
##  Copyright (C) 2016, goatpig                                               ##
##  Distributed under the MIT license                                         ##
##  See LICENSE-MIT or https://opensource.org/licenses/MIT                    ##
##                                                                            ##
################################################################################

from armoryengine import PyBtcWallet
import CppBlockUtils as Cpp

class PythonSignerDirector(Cpp.PythonSigner):
   def __init__(self, btcWallet):
      Cpp.PythonSigner.__init__(self, btcWallet.cppWallet)
      
      self.wlt = btcWallet
      
   def getPrivateKeyForIndex(self, index):
      return self.wlt.getPrivateKeyForIndex(index)
   
   def getPrivateKeyForImportIndex(self, index):
      scrAddr = self.wlt.linearAddr160List[index]
      addrObj = self.wlt.addrMap[scrAddr]
      
      return addrObj.binPrivKey32_Plain
   
   def addSpender(self, utxo):
      super(PythonSignerDirector, self).addSpender(\
         utxo.val, \
         0, 0, utxo.txOutIndex, \
         utxo.txHash, utxo.binScript)
      