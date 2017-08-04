################################################################################
##                                                                            ##
##  Copyright (C) 2016, goatpig                                               ##
##  Distributed under the MIT license                                         ##
##  See LICENSE-MIT or https://opensource.org/licenses/MIT                    ##
##                                                                            ##
################################################################################

import CppBlockUtils as Cpp

SIGNER_DEFAULT = 'Default'
SIGNER_LEGACY  = 'Legacy'
SIGNER_CPP     = '0.96 C++'
SIGNER_BCH     = 'Bcash'

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
   
   def addSpender(self, utxo, sequence):
      super(PythonSignerDirector, self).addSpender(\
         utxo.val, \
         0, 0, utxo.txOutIndex, \
         utxo.txHash, utxo.binScript, sequence)

class PythonSignerDirector_BCH(Cpp.PythonSigner_BCH):
   def __init__(self, btcWallet):
      Cpp.PythonSigner_BCH.__init__(self, btcWallet.cppWallet)
      
      self.wlt = btcWallet

   def getPrivateKeyForIndex(self, index):
      return self.wlt.getPrivateKeyForIndex(index)
   
   def getPrivateKeyForImportIndex(self, index):
      scrAddr = self.wlt.linearAddr160List[index]
      addrObj = self.wlt.addrMap[scrAddr]
      
      return addrObj.binPrivKey32_Plain
   
   def addSpender(self, utxo, sequence):
      super(PythonSignerDirector_BCH, self).addSpender(\
         utxo.val, \
         0, 0, utxo.txOutIndex, \
         utxo.txHash, utxo.binScript, sequence)