################################################################################
#
# Copyright (C) 2011, Alan C. Reiner    <alan.reiner@gmail.com>
# Distributed under the GNU Affero General Public License (AGPL v3)
# See LICENSE or http://www.gnu.org/licenses/agpl.html
#
################################################################################
#
# This file defines the hybrid utility methods which combines the PyBtcEngine
# python library, with the C++ methods made available through SWIG.  The C++
# code (CppBlockUtils) does blockchain management, searching, filtering, etc, 
# very efficiently.  The python code (PyBtcEngine) does all the bignum and
# ECDSA ops.  When combined, they form a COMPLETE computational backend for 
# bitcoin software.  See the readme for more information about available
# functionality in the two libraries
#
################################################################################
from pybtcengine import *
import CppBlockUtils as Cpp
from datetime import datetime
from os import path
from sys import argv

################################################################################
# Might as well create the BDM right here -- there will only ever be one, anyway
bdm = Cpp.BlockDataManager().getBDM()
################################################################################


################################################################################
################################################################################
#
# PyBtcWallet:
#
# The following class rigorously defines the file format for storing, loading
# and modifying "wallet" objects.  Presumably, wallets will be used for one of
# three purposes:
#
#  (1) Spend money and receive payments
#  (2) Watching-only wallets - we have the private key, just not on this computer
#  (3) May be watching addresses of *other* people.  There's a variety of reasons
#      we might want to watch other peoples' addresses, but most them are not
#      relevant to a "basic" BTC user.  Nonetheless it should be supported to
#      watch money without considering it part of our own assets
#
#  This class is included in the combined-python-cpp module, because we really
#  need to maintain a persistent Cpp.BtcWallet if this class is to be useful
#  (we don't want to have to rescan the entire blockchain every time we do any
#  wallet operations).
#
#  The file format was designed from the outset with lots of unused space to 
#  allow for expansion without having to redefine the file format and break
#  previous wallets.  Luckily, wallet information is cheap, so we don't have 
#  to stress too much about saving space (100,000 addresses should take 15 MB)
#
#  This file is NOT for storing Tx-related information.  I want this file to
#  be the minimal amount of information you need to secure and backup your
#  entire wallet.  Tx information can always be recovered from examining the
#  blockchain... your private keys cannot be.
#
#  We track version numbers, just in case.  We start with 1.0
#  
#  Version 1.0:
#      ---
#        fileID      -- (8)  '\xbaWALLET\x00' for wallet files
#        version     -- (4)   floating point number, times 1e6, rounded to int
#        magic bytes -- (4)   defines the blockchain for this wallet (BTC, NMC)
#        wlt flags   -- (8)   64 bits/flags representing info about wallet
#        wlt ID      -- (8)   first 8 bytes of first address in wallet
#                             (this contains the network byte; mainnet, testnet)
#        create date -- (8)   unix timestamp of when this wallet was created
#        UNUSED      -- (256) unused space for future expansion of wallet file
#        Short Name  -- (32)  Null-terminated user-supplied short name for wlt
#        Long Name   -- (256) Null-terminated user-supplied description for wlt
#      ---
#        Crypto/KDF  -- (256) information identifying the types and parameters
#                             of encryption used to secure wallet, and key 
#                             stretching used to secure your passphrase.
#                             Includes salt. (the breakdown of this field will
#                             be described separately)
#        Deterministic--(512) Includes private key generator (prob encrypted),
#        Wallet Params        base public key for watching-only wallets, and 
#                             a chain-code that identifies how keys are related
#                             (each field also contains chksum for integrity)
#      ---
#        Remainder of file is for key storage, and comments about individual
#        addresses.  
# 
#        PrivKey(33)  -- ECDSA private key, with a prefix byte declaring whether
#                        this is an encrypted 32-bytes or not plain.  
#        CheckSum(4)  -- This is the checksum of the data IN THE FILE!  If the 
#                        PrivKey is encrypted, checksum is first 4 bytes of the
#                        encrypted private key.  Likewise for unencrypted.  THe
#                        goal is to make sure we don't lose our private key to
#                        a bit/byte error somewhere (this isn't the best way to
#                        recover from a bit/byte error, but such errors should
#                        be rare, and the simplicity is preferred over something
#                        like Reed-Solomon)
#        PublicKey(64)-- 
#        Creation Time/ --
#        First seen time
#        Last-seen time --
#        TODO:  finish this!
#                             
#                    
#
#
################################################################################
################################################################################
class PyBtcWallet(object):
   """
   This class encapsulates all the concepts and variables in a "wallet",
   and maintains the passphrase protection, key stretching, encryption,
   etc, required to maintain the wallet.  This class also includes the
   file I/O methods for storing and loading wallets.
   """

   #############################################################################
   class CryptoParams(object):
      def __init__(self):
         self.kdf = None
         self.cryptoPrivKey = None
         self.cryptoPubKey = None

      def kdf(self, passphrase):
         pass

      def encrypt(self, plaintext, key, *args):
         pass

      def decrypt(self, plaintext, key, *args):
         pass

      def serialize(self):
         return '\x00'*1024

      def unserialize(self, toUnpack):
         binData = toUnpack
         if isinstance(toUnpack):
            binData = toUnpack.get(BINARY_CHUNK, 1024)

         # Right now, nothing to do because encryption is not implemented
         # Coming soon, though!
         pass 



   #############################################################################
   def __init__(self):
      self.addrMap  = {}
      self.fileID   = '\xbaWALLET\x00'
      self.version  = (1,0,0,0)  # (Major, Minor, Minor++, even-more-minor)
      self.eofByte  = 0
      self.cppWallet = None  # Mirror of PyBtcWallet in C++ object
      self.cppInfo   = {}    # Extra info about each address to help sync


   #############################################################################
   def addAddress(self, addrData, firstSeenData=[], lastSeenData=[]):
      print 'Adding new address to wallet: ',
      addr160 = None
      if isinstance(addrData, PyBtcAddress) and addrData.isInitialized():
         addr160 = addrData.getAddr160()
         self.addrMap[addr160] = addrData
      elif isInitialized(addrData, str):
         if len(addrData)==20:
            addr160 = addrData
            self.addrMap[addr160] = PyBtcAddress().createFromPublicKeyHash160(addr160)
         elif 64 <= len(addrData) <= 65:
            addr160 = hash160(addrData.rjust(65,'\x04'))
            self.addrMap[addr160] = PyBtcAddress().createFromPublicKey(pubKeyStr)
         elif len(addrData)==32:
            newPrivAddr = PyBtcAddress().createFromPrivateKey(addrData)
            addr160 = newPrivAddr.getAddr160()
            self.addrMap[addr160] = newPrivAddr
      else:
         print '<ERROR>'
         raise BadAddressError, 'Improper address supplied to "addAddress()"'
      print binary_to_hex(addr160)

      # Now make sure the C++ wallet is sync'd
      addrObj = self.addrMap[addr160]
      cppAddr = PyBtcAddress()
      cppAddr.setAddrStr20(addr160)
      if addrObj.hasPubKey() 
         cppAddr.setPubKey65(addrObj.pubKey_serialize())
      if addrObj.hasPrivKey() 
         cppAddr.setPrivKey32(addrObj.privKey_serialize())

      if len(firstSeenData)>0: cppAddr.setFirstBlockNum(firstSeenData[0])
      if len(firstSeenData)>1: cppAddr.setFirstTimestamp(firstSeenData[1])
      if len( lastSeenData)>0: cppAddr.setLastBlockNum(lastSeenData[0])
      if len( lastSeenData)>1: cppAddr.setLastTimestamp(lastSeenData[1])

      if not self.cppWallet:
         self.cppWallet = Cpp.BtcWallet()
      self.cppWallet.addAddress_BtcAddress_(cppAddr)
            
         

   #############################################################################
   def addAddresses(self, addrList):
      for addr in addrList:
         self.addAddress(addr)
         
   #############################################################################
   def syncWalletWithBlockchain(self):
      bdm = Cpp.BlockDataManager().getBDM()  # hopefully this is init already
      bdm.scanBlockchainForTx_FromScratch(self.cppWallet)
   

   #############################################################################
   def getUnspentTxOutList(self):
      bdm = Cpp.BlockDataManager().getBDM()  # hopefully this is init already
      self.syncWalletWithBlockchain()
      return bdm.getUnspentTxOutsForWallet(self.cppWallet)
   
   #############################################################################
   def getWalletVersion(self):
      return (getVersionInt(self.version), getVersionString(self.version))
   
   #############################################################################
   def writeToFile(self, fn, withPrivateKeys=True, withBackup=True):
      """
      All data is little-endian unless you see the method explicitly
      pass in "BIGENDIAN" as the last argument to the put() call...

      Pass in withPrivateKeys=False to create a watching-only wallet.
      """
      if os.path.exists(fn) and withBackup:
         shutil.copy(fn, fn+'_old');
      
      bp = BinaryPacker()
      bp.put(BINARY_CHUNK, self.fileID)     
      for i in range(4):
         bp.put(UINT8, self.version[i])
      bp.put(BINARY_CHUNK, MAGIC_BYTES)

      # TODO: Define wallet flags
      bp.put(BINARY_CHUNK, MAGIC_BYTES)

      # Creation Date
      try:
         bp.put(UINT64, self.walletCreateTime)
      except:
         bp.put(UINT64, long(time.time()))


      # TODO: Make sure firstAddr is defined
      bp.put(BINARY_CHUNK, firstAddr[:8])

      # UNUSED BINARY DATA -- maybe used to expand file format later
      bp.put(BINARY_CHUNK, '\x00'*256)

      # Short and long name/info supplied by the user (not really binary data)
      bp.put(BINARY_CHUNK, self.shortInfo[:32].ljust( 33,'\x00'))
      bp.put(BINARY_CHUNK, self.longInfo[:255].ljust(256,'\x00'))

      # All information needed to know how to get from a passphrase/password
      # to a decrypted private key -- all zeros if 
      # TODO:  need to define this more rigorously, maybe layout each field here
      bp.put(BINARY_CHUNK, self.crypto.serialize().ljust(256,'\x00'))
      if not self.isDeterministic:
         # TODO:  NEED VAR_INTs to identify key lengths
         bp.put(BINARY_CHUNK, '\x00'*(1 + 32 + 4 + 64 + 4 + 32 + 4 + 256))
      else:
         if self.hasPrivKeyGen():

            if self.privKeyIsPlain:
               # This method does nothing if no encryption is defined
               pkgEncr = self.crypto.encrypt(self.privKeyGen, self.encryptPub) 

            pkgLen  = len(pkgEncr)
            bp.put(VAR_INT, pkgLen)
            bp.put(BINARY_CHUNK, pkgEncr + hash256(pkgEncr)[:4])

            pubLen  = len(self.pubKeyGen)
            bp.put(VAR_INT, pubLen)
            bp.put(BINARY_CHUNK, self.pubKeyGen + hash256(self.pubKeyGen)[:4])

            chcLen  = len(self.chainCode)
            bp.put(VAR_INT, chcLen)
            bp.put(BINARY_CHUNK, self.chainCode + hash256(self.chainCode)[:4])

            bp.put(BINARY_CHUNK, '\x00'*256)

      wltFile = open(fn, 'wb')
      wltFile.write(bp.getBinaryString())
      wltFile.close()

      
   def appendKeyToFile(self, fn, pbaddr, withPrivateKeys=True):
      assert(os.path.exists(fn))
      prevSize = os.path.getsize(fn)
         
      bp = BinaryPacker()
      wltFile = open(fn, 'ab')

      bp.put(UINT8, 1 if self.useEncrypt() else 0)
      bp.put(BINARY_CHUNK, pbaddr.getAddr160())
      if withPrivateKeys and pbaddr.hasPrivKey():
         privKeyBin = int_to_binary(pbaddr.privKeyInt, 32, LITTLEENDIAN)
         bp.put(BINARY_CHUNK, privKeyBin)
         bp.put(BINARY_CHUNK, int_to_binary(pbaddr.privKeyInt, 32, LITTLEENDIAN))
      else:
         bp.put(BINARY_CHUNK, '\x00'*32)
      
      

   def readFromFile(self, fn):
      
      magicBytes = bup.get(BINARY_CHUNK, 4)
      if not magicBytes == MAGIC_BYTES:
         print '***ERROR:  Requested wallet is for a different blockchain!'
         print '           Wallet is for:', BLOCKCHAINS[magicBytes]
         print '           PyBtcEngine:  ', BLOCKCHAINS[MAGIC_BYTES]
         return
      if not netByte == ADDRBYTE:
         print '***ERROR:  Requested wallet is for a different network!'
         print '           Wallet is for:', NETWORKS[netByte]
         print '           PyBtcEngine:  ', NETWORKS[ADDRBYTE]
         return

   def syncToFile(self, fn):
      pass






################################################################################
def loadBlockchainFile(blkfile=None, testnet=False):
   """
   Looks for the blk0001.dat file in the default location for your operating
   system.  If it is found, it is loaded into RAM and the longest chain is
   computed.  Access to any information in the blockchain can be found via
   the bdm object.
   """
   import platform
   opsys = platform.system()
   if blkfile==None:
      if not testnet:
         if 'win' in opsys.lower():
            blkfile = path.join(os.getenv('APPDATA'), 'Bitcoin', 'blk0001.dat')
         if 'nix' in opsys.lower() or 'nux' in opsys.lower():
            blkfile = path.join(os.getenv('HOME'), '.bitcoin', 'blk0001.dat')
         if 'mac' in opsys.lower() or 'osx' in opsys.lower():
            blkfile = os.path.expanduser('~/Library/Application Support/Bitcoin/blk0001.dat')
      else:
         if 'win' in opsys.lower():
            blkfile = path.join(os.getenv('APPDATA'), 'Bitcoin/testnet', 'blk0001.dat')
         if 'nix' in opsys.lower() or 'nux' in opsys.lower():
            blkfile = path.join(os.getenv('HOME'), '.bitcoin/testnet', 'blk0001.dat')
         if 'mac' in opsys.lower() or 'osx' in opsys.lower():
            blkfile = os.path.expanduser('~/Library/Application Support/Bitcoin/testnet/blk0001.dat')

   if not path.exists(blkfile):
      raise FileExistsError, ('File does not exist: %s' % blkfile)
   bdm.readBlkFile_FromScratch(blkfile)


################################################################################
def ScanBlockchainForTx(PyT

################################################################################
def CreateTransaction(fromWallet, recipAddr160, btcValue):
   """
   This is the complete process for creating a transaction from scratch.  
      fromWallet:    Expected PyBtcWallet object
      recipAddr160:  20-byte pubKeyHash: use PyBtcAddress().getAddr160()
      btcValue:      Amount to send IN BTC: will be multiplied by 1e8

   This method combines just about every method in 
   




