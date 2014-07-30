import sys
sys.path.append('..')
from pytest.Tiab import TiabTest

from CppBlockUtils import SecureBinaryData, CryptoECDSA, CryptoAES
from armoryengine.PyBtcAddress import PyBtcAddress
from armoryengine.ArmoryUtils import *
from armoryengine.BinaryUnpacker import BinaryUnpacker
from armoryengine.PyBtcWallet import PyBtcWallet
from armoryengine.PyBtcWalletRecovery import PyBtcWalletRecovery, RECOVERMODE
import unittest
import os

from armoryengine.ArmoryUtils import SECP256K1_ORDER, binary_to_int, BIGENDIAN

class PyBtcWalletRecoveryTest(TiabTest):
   def setUp(self):
      self.corruptWallet = 'corrupt_wallet.wallet'
      
      self.wltID = self.buildCorruptWallet(self.corruptWallet)
      
   def tearDown(self):
      os.unlink(self.corruptWallet)
      os.unlink(self.corruptWallet[:-7] + '_backup.wallet')
      
      os.unlink('armory_%s_RECOVERED.wallet' % self.wltID)
      os.unlink('armory_%s_RECOVERED_backup.wallet' % self.wltID)
      
   def buildCorruptWallet(self, walletPath):
      crpWlt = PyBtcWallet()
      crpWlt.createNewWallet(walletPath, securePassphrase='testing', doRegisterWithBDM=False)
      #not registering with the BDM, have to fill the wallet address pool manually 
      crpWlt.fillAddressPool(100)      

      #grab the last computed address
      lastaddr = crpWlt.addrMap[crpWlt.lastComputedChainAddr160]
      
      #corrupt the pubkey
      PubKey = hex_to_binary('0478d430274f8c5ec1321338151e9f27f4c676a008bdf8638d07c0b6be9ab35c71a1518063243acd4dfe96b66e3f2ec8013c8e072cd09b3834a19f81f659cc3455')
      lastaddr.binPublicKey65 = SecureBinaryData(PubKey)
      crpWlt.addrMap[crpWlt.lastComputedChainAddr160] = lastaddr
      
      crpWlt.fillAddressPool(200)
       
      #insert a gap and inconsistent encryption
      newAddr = PyBtcAddress()
      newAddr.chaincode = lastaddr.chaincode
      newAddr.chainIndex = 250
      PrivKey = hex_to_binary('e3b0c44298fc1c149afbf4c8996fb92427ae41e5978fe51ca495991b7852b855')
      newAddr.binPrivKey32_Plain = SecureBinaryData(PrivKey)
      newAddr.binPublicKey65 = CryptoECDSA().ComputePublicKey( \
                                                newAddr.binPrivKey32_Plain)
      newAddr.addrStr20 = newAddr.binPublicKey65.getHash160()
      newAddr.isInitialized = True
      
      crpWlt.addrMap[newAddr.addrStr20] = newAddr
      crpWlt.lastComputedChainAddr160 = newAddr.addrStr20
      crpWlt.fillAddressPool(250)
      
      lastAddr = crpWlt.addrMap[crpWlt.lastComputedChainAddr160]
      PrivKey = hex_to_binary('e3b0c44298fc1c149afbf4c8996fb92427ae41e5978fe51ca495991b00000000')
      lastAddr.binPrivKey32_Plain = SecureBinaryData(PrivKey)
      lastAddr.binPublicKey65 = CryptoECDSA().ComputePublicKey( \
                                                lastAddr.binPrivKey32_Plain)      
      lastAddr.keyChanged = True
      crpWlt.kdfKey = crpWlt.kdf.DeriveKey(SecureBinaryData('testing'))
      lastAddr.lock(secureKdfOutput=crpWlt.kdfKey)
      lastAddr.useEncryption = True
      
      crpWlt.fillAddressPool(350);
      
      #TODO: corrupt a private key  
      #break an address entry at binary level    
      return crpWlt.uniqueIDB58

   def testWalletRecovery(self):
      #run recovery on broken wallet
      recThread = PyBtcWalletRecovery().RecoverWallet(self.corruptWallet, \
                                                      'testing', RECOVERMODE.Full, \
                                                      returnError = 'Dict')
      recThread.join()
      brkWltResult = recThread.output
      
      self.assertTrue(len(brkWltResult['sequenceGaps'])==1, \
                      "Sequence Gap Undetected")
      self.assertTrue(len(brkWltResult['forkedPublicKeyChain'])==3, \
                      "Address Chain Forks Undetected")
      self.assertTrue(len(brkWltResult['unmatchedPair'])==100, \
                      "Unmatched Priv/Pub Key Undetected")
      self.assertTrue(len(brkWltResult['misc'])==50, \
                      "Wallet Encryption Inconsistency Undetected")
      self.assertTrue(len(brkWltResult['importedErr'])==50, \
                      "Unexpected Errors Found")         
      self.assertTrue(brkWltResult['nErrors']==204, \
                      "Unexpected Errors Found")   
      
      #check obfuscated keys yield the valid key
      #grab root key
      badWlt = PyBtcWallet()
      badWlt.readWalletFile(self.corruptWallet, False, False)
      rootAddr = badWlt.addrMap['ROOT']
      
      SecurePassphrase = SecureBinaryData('testing')
      secureKdfOutput = badWlt.kdf.DeriveKey(SecurePassphrase)
      
      #HMAC Q
      rootAddr.unlock(secureKdfOutput)
      Q = rootAddr.binPrivKey32_Plain.toBinStr()
      
      nonce = 0
      while 1:
         hmacQ = HMAC256(Q, 'LogMult%d' % nonce)
         if binary_to_int(hmacQ, BIGENDIAN) < SECP256K1_ORDER:         
            hmacQ = SecureBinaryData(hmacQ)
            break
         nonce = nonce +1
      
      #Bad Private Keys
      import operator
      badKeys = [addrObj for addrObj in (sorted(badWlt.addrMap.values(), 
                             key=operator.attrgetter('chainIndex')))]
         
      #run through obdsPrivKey
      for i in range(0, len(brkWltResult['privMult'])):
         obfsPKey = SecureBinaryData(
                        hex_to_binary(brkWltResult['privMult'][i]))
         pKey = CryptoECDSA().ECMultiplyScalars(obfsPKey.toBinStr(), \
                                                hmacQ.toBinStr())
         
         try:
            badKeys[i+201].unlock(secureKdfOutput)
         except:
            continue
         
         self.assertTrue(binary_to_hex(pKey) == \
                         badKeys[i+201].binPrivKey32_Plain.toHexStr(), \
                         'key mult error')
      
      #run recovery on recovered wallet
      recThread = PyBtcWalletRecovery().RecoverWallet( \
                                 'armory_%s_RECOVERED.wallet' % self.wltID, \
                                 'testing', RECOVERMODE.Full, \
                                 returnError = 'Dict')
      recThread.join()
      rcvWltResult = recThread.output
      
      self.assertTrue(len(rcvWltResult['importedErr'])==50, \
                      "Unexpected Errors Found")         
      self.assertTrue(rcvWltResult['nErrors']==50, \
                      "Unexpected Errors Found")   
      self.assertTrue(len(rcvWltResult['negativeImports'])==99, \
                      "Missing neg Imports")
      
# Running tests with "python <module name>" will NOT work for any Armory tests
# You must run tests with "python -m unittest <module name>" or run all tests with "python -m unittest discover"
# if __name__ == "__main__":
#    unittest.main()