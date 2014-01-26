from armoryengine.PyBtcWallet import PyBtcWallet
from CppBlockUtils import SecureBinaryData, CryptoECDSA
from armoryengine.PyBtcAddress import PyBtcAddress
from armoryengine.ArmoryUtils import hex_to_binary
import unittest
import os

from armoryengine.PyBtcWalletRecovery import PyBtcWalletRecovery

class PyBtcWalletRecoveryTest(unittest.TestCase):
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
      newAddr.binPublicKey65 = CryptoECDSA().ComputePublicKey(newAddr.binPrivKey32_Plain)
      newAddr.addrStr20 = newAddr.binPublicKey65.getHash160()
      newAddr.isInitialized = True
      
      crpWlt.addrMap[newAddr.addrStr20] = newAddr
      crpWlt.lastComputedChainAddr160 = newAddr.addrStr20
      crpWlt.fillAddressPool(250)
      
      #TODO: corrupt a private key  
      #break an address entry at binary level    
      return crpWlt.uniqueIDB58

   def testWalletRecovery(self):
      #run recovery on broken wallet
      brkWltResult = PyBtcWalletRecovery().RecoverWallet(self.corruptWallet, 'testing', 'Full', returnError = 'Dict')
      self.assertTrue(len(brkWltResult['sequenceGaps'])==1, "Sequence Gap Undetected")
      self.assertTrue(len(brkWltResult['forkedPublicKeyChain'])==2, "Address Chain Forks Undetected")
      self.assertTrue(len(brkWltResult['unmatchedPair'])==100, "Unmatched Priv/Pub Key Undetected")
      self.assertTrue(len(brkWltResult['misc'])==50, "Wallet Encryption Inconsistency Undetected")
      
      #run recovery on recovered wallet
      rcvWltResult = PyBtcWalletRecovery().RecoverWallet('armory_%s_RECOVERED.wallet' % self.wltID, 'testing', 'Full', returnError = 'Dict')
      self.assertTrue(rcvWltResult == 0, "Broken Recovered Wallet")
      
###############################################################################
if __name__ == "__main__":
   unittest.main()     