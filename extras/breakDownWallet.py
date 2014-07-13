from armoryengine.PyBtcWallet import (PyBtcWallet, WLT_DATATYPE_KEYDATA, \
                                      WLT_UPDATE_ADD)

import os
import sys
from CppBlockUtils import SecureBinaryData
from armoryengine.ArmoryUtils import (binary_to_base58, RightNow, ADDRBYTE)
from armoryengine.BinaryPacker import *
import random

###############################################################################
def createNewWallet(wlt, rootEntry, newWalletFilePath, withEncrypt, 
                    kdfParam=None):
      """
      This method will create a new wallet, using as much customizability
      as you want.  You can enable encryption, and set the target params
      of the key-derivation function (compute-time and max memory usage).
      The KDF parameters will be experimentally determined to be as hard
      as possible for your computer within the specified time target
      (default, 0.25s).  It will aim for maximizing memory usage and using
      only 1 or 2 iterations of it, but this can be changed by scaling
      down the kdfMaxMem parameter (default 32 MB).

      If you use encryption, don't forget to supply a 32-byte passphrase,
      created via SecureBinaryData(pythonStr).  This method will apply
      the passphrase so that the wallet is "born" encrypted.

      The field plainRootKey could be used to recover a written backup
      of a wallet, since all addresses are deterministically computed
      from the root address.  This obviously won't reocver any imported
      keys, but does mean that you can recover your ENTIRE WALLET from
      only those 32 plaintext bytes AND the 32-byte chaincode.

      We skip the atomic file operations since we don't even have
      a wallet file yet to safely update.

      DO NOT CALL THIS FROM BDM METHOD.  IT MAY DEADLOCK.
      """

      # Create the root address object
      rootAddr = rootEntry

      # Update wallet object with the new data
      # NEW IN WALLET VERSION 1.35:  unique ID is now based on
      # the first chained address: this guarantees that the unique ID
      # is based not only on the private key, BUT ALSO THE CHAIN CODE
      wlt.useEncryption = withEncrypt
      wlt.addrMap['ROOT'] = rootAddr
      wlt.uniqueIDBin = (ADDRBYTE + str(random.getrandbits(48))[:5])[::-1]
      wlt.uniqueIDB58 = binary_to_base58(wlt.uniqueIDBin)
      wlt.labelName  = ''
      wlt.labelDescr  = ''
      wlt.lastComputedChainAddr160 = rootAddr
      wlt.lastComputedChainIndex  = 0
      wlt.highestUsedChainIndex   = 0
      wlt.wltCreateDate = long(RightNow())
      wlt.kdf = kdfParam

      # We don't have to worry about atomic file operations when
      # creating the wallet: so we just do it naively here.
      wlt.walletPath = newWalletFilePath

      newfile = open(newWalletFilePath, 'wb')
      fileData = BinaryPacker()

      # packHeader method writes KDF params and root address
      headerBytes = wlt.packHeader(fileData)

      newfile.write(fileData.getBinaryString())
      newfile.close()

###############################################################################
def breakDownWallet(walletPath, fragSize):
   print 'breaking down wallet in packs of %d addresses' % fragSize
   print 'reading wallet'
   theWallet = PyBtcWallet().readWalletFile(walletPath)
   
   nAddresses = len(theWallet.addrMap)
   
   addrIndex = 0
   wltIndex = 1

   if walletPath[-7:] == '.wallet':
      newDir = walletPath[:-7]
   else:
      newDir = os.path.dirname(walletPath)
      
   if not os.path.exists(newDir):
      os.mkdir(newDir)
      
   rootAddr = theWallet.addrMap['ROOT']
   withEncrypt = theWallet.useEncryption
   addrIter = theWallet.addrMap.iteritems()
   
   while nAddresses > 0 :
      
      print 'breaking down wallet from address #%d to #%d' % (addrIndex, addrIndex +fragSize-1)
      nAddresses -= fragSize

      
      newWalletPath = os.path.join(newDir, 'armory_wlt_%05d_.wallet' % wltIndex)
      wltIndex += 1
      
      walletFragment = PyBtcWallet()
      createNewWallet(walletFragment, rootAddr, newWalletPath, withEncrypt, theWallet.kdf) 
   
      fileData = BinaryPacker()
      i=0
      
      try:
         while i < fragSize:
            addrItem = addrIter.next()[1]
            addrItem.chainIndex = -2
            
            fileData.put(BINARY_CHUNK, '\x00' + addrItem.addrStr20 + addrItem.serialize())
            #walletFragment.walletFileSafeUpdate([[WLT_UPDATE_ADD, \
                           #WLT_DATATYPE_KEYDATA, addrItem.addrStr20, addrItem]])
            i += 1
            
      except StopIteration:
         pass
      
      walletFile = open(newWalletPath, 'ab')
      walletFile.write(fileData.getBinaryString())
      walletFile.close()      
      
      addrIndex += i
   print 'Done'
         
###############################################################################################

if len(sys.argv) < 2:
   print 'not enough arguments'
   sys.exit(0)
   
walletPath = sys.argv[1]

if len(sys.argv) < 3:
   fragSize = 0
else:
   fragSize   = int(sys.argv[2])

if not os.path.exists(walletPath):
   print 'invalid wallet path'
   sys.exit(0)
   
if not isinstance(fragSize, int) or fragSize == 0:
   fragSize = 5000
   
breakDownWallet(walletPath, fragSize)
         