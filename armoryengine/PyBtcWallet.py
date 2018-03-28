################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                            #
# Copyright (C) 2016-17, goatpig                                             #
#  Distributed under the MIT license                                         #
#  See LICENSE-MIT or https://opensource.org/licenses/MIT                    #                                   
#                                                                            #
##############################################################################
import os.path
import shutil

from CppBlockUtils import SecureBinaryData, KdfRomix, CryptoAES, CryptoECDSA
import CppBlockUtils as Cpp
from armoryengine.ArmoryUtils import *
from armoryengine.BinaryPacker import *
from armoryengine.BinaryUnpacker import *
from armoryengine.Timer import *
from armoryengine.Decorators import singleEntrantMethod

from armoryengine.SignerWrapper import SIGNER_DEFAULT, SIGNER_BCH, SIGNER_CPP, \
   SIGNER_LEGACY, PythonSignerDirector, PythonSignerDirector_BCH
# This import is causing a circular import problem when used by findpass and promokit
# it is imported at the end of the file. Do not add it back at the begining
# from armoryengine.Transaction import *


BLOCKCHAIN_READONLY   = 0
BLOCKCHAIN_READWRITE  = 1
BLOCKCHAIN_DONOTUSE   = 2

WLT_UPDATE_ADD = 0
WLT_UPDATE_MODIFY = 1

WLT_DATATYPE_KEYDATA     = 0
WLT_DATATYPE_ADDRCOMMENT = 1
WLT_DATATYPE_TXCOMMENT   = 2
WLT_DATATYPE_OPEVAL      = 3
WLT_DATATYPE_DELETED     = 4

DEFAULT_COMPUTE_TIME_TARGET = 0.25
DEFAULT_MAXMEM_LIMIT        = 32*1024*1024

PYROOTPKCCVER = 1 # Current version of root pub key/chain code backup format
PYROOTPKCCVERMASK = 0x7F
PYROOTPKCCSIGNMASK = 0x80

# Only works on PyBtcWallet
# If first arg is not PyBtcWallet call the function as if it was
# not decorated, it should throw whatever error or do whatever it would
# do withouth this decorator. This decorator does nothing if applied to 
# the methods of any other class
def CheckWalletRegistration(func):
   def inner(*args, **kwargs):
      if len(args)>0 and isinstance(args[0],PyBtcWallet):
         if args[0].isRegistered():
            return func(*args, **kwargs)
         elif 'doRegister' in kwargs and kwargs['doRegister'] == False:
            return func(*args, **kwargs)
         else:
            raise WalletUnregisteredError
      else:
         return func(*args, **kwargs)
   return inner

def buildWltFileName(uniqueIDB58):
   return 'armory_%s_.wallet' % uniqueIDB58
   
class PyBtcWallet(object):
   """
   This class encapsulates all the concepts and variables in a "wallet",
   and maintains the passphrase protection, key stretching, encryption,
   etc, required to maintain the wallet.  This class also includes the
   file I/O methods for storing and loading wallets.

   ***NOTE:  I have ONLY implemented deterministic wallets, using ECDSA
             Diffie-Hellman shared-secret crypto operations.  This allows
             one to actually determine the next PUBLIC KEY in the address
             chain without actually having access to the private keys.
             This makes it possible to synchronize online-offline computers
             once and never again.

             You can import random keys into your wallet, but if it is
             encrypted, you will have to supply a passphrase to make sure
             it can be encrypted as well.

   Presumably, wallets will be used for one of three purposes:

   (1) Spend money and receive payments
   (2) Watching-only wallets - have the private keys, just not on this computer
   (3) May be watching *other* people's addrs.  There's a variety of reasons
       we might want to watch other peoples' addresses, but most them are not
       relevant to a "basic" BTC user.  Nonetheless it should be supported to
       watch money without considering it part of our own assets

   This class is included in the combined-python-cpp module, because we really
   need to maintain a persistent Cpp.BtcWallet if this class is to be useful
   (we don't want to have to rescan the entire blockchain every time we do any
   wallet operations).

   The file format was designed from the outset with lots of unused space to
   allow for expansion without having to redefine the file format and break
   previous wallets.  Luckily, wallet information is cheap, so we don't have
   to stress too much about saving space (100,000 addresses should take 15 MB)

   This file is NOT for storing Tx-related information.  I want this file to
   be the minimal amount of information you need to secure and backup your
   entire wallet.  Tx information can always be recovered from examining the
   blockchain... your private keys cannot be.

   We track version numbers, just in case.  We start with 1.0

   Version 1.0:
   ---
   fileID      -- (8)  '\xbaWALLET\x00' for wallet files
   version     -- (4)   getVersionInt(PYBTCWALLET_VERSION)
   magic bytes -- (4)   defines the blockchain for this wallet (BTC, NMC)
   wlt flags   -- (8)   64 bits/flags representing info about wallet
   binUniqueID -- (6)   first 5 bytes of first address in wallet
                        (rootAddr25Bytes[:5][::-1]), reversed
                        This is not intended to look like the root addr str
                        and is reversed to avoid having all wallet IDs start 
                        with the same characters (since the network byte is front)
   create date -- (8)   unix timestamp of when this wallet was created
                        (actually, the earliest creation date of any addr
                        in this wallet -- in the case of importing addr
                        data).  This is used to improve blockchain searching
   Short Name  -- (32)  Null-terminated user-supplied short name for wlt
   Long Name   -- (256) Null-terminated user-supplied description for wlt
   Highest Used-- (8)   The chain index of the highest used address
   ---
   Crypto/KDF  -- (512) information identifying the types and parameters
                        of encryption used to secure wallet, and key
                        stretching used to secure your passphrase.
                        Includes salt. (the breakdown of this field will
                        be described separately)
   KeyGenerator-- (237) The base address for a determinstic wallet.
                        Just a serialized PyBtcAddress object.
   ---
   UNUSED     -- (1024) unused space for future expansion of wallet file
   ---
   Remainder of file is for key storage and various other things.  Each
   "entry" will start with a 4-byte code identifying the entry type, then
   20 bytes identifying what address the data is for, and finally then
   the subsequent data .  So far, I have three types of entries that can
   be included:

      \x01 -- Address/Key data (as of PyBtcAddress version 1.0, 237 bytes)
      \x02 -- Address comments (variable-width field)
      \x03 -- Address comments (variable-width field)
      \x04 -- OP_EVAL subscript (when this is enabled, in the future)

   Please see PyBtcAddress for information on how key data is serialized.
   Comments (\x02) are var-width, and if a comment is changed to
   something longer than the existing one, we'll just blank out the old
   one and append a new one to the end of the file.  It looks like

   02000000 01 <Addr> 4f This comment is enabled (01) with 4f characters


   For file syncing, we protect against corrupted wallets by doing atomic
   operations before even telling the user that new data has been added.
   We do this by copying the wallet file, and creating a walletUpdateFailed
   file.  We then modify the original, verify its integrity, and then delete
   the walletUpdateFailed file.  Then we create a backupUpdateFailed flag,
   do the identical update on the backup file, and delete the failed flag. 
   This guaranatees that no matter which nanosecond the power goes out,
   there will be an uncorrupted wallet and we know which one it is.

   We never let the user see any data until the atomic write-to-file operation
   has completed


   Additionally, we implement key locking and unlocking, with timeout.  These
   key locking features are only DEFINED here, not actually enforced (because
   this is a library, not an application).  You can set the default/temporary
   time that the KDF key is maintained in memory after the passphrase is
   entered, and this class will keep track of when the wallet should be next
   locked.  It is up to the application to check whether the current time
   exceeds the lock time.  This will probably be done in a kind of heartbeat
   method, which checks every few seconds for all sorts of things -- including
   wallet locking.
   """

   #############################################################################
   def __init__(self):
      self.fileTypeStr    = '\xbaWALLET\x00'
      self.magicBytes     = MAGIC_BYTES
      self.version        = PYBTCWALLET_VERSION  # (Major, Minor, Minor++, even-more-minor)
      self.eofByte        = 0
      self.cppWallet      = None   # Mirror of PyBtcWallet in C++ object
      self.cppInfo        = {}     # Extra info about each address to help sync
      self.watchingOnly   = False
      self.wltCreateDate  = 0

      # Three dictionaries hold all data
      self.addrMap     = {}  # maps 20-byte addresses to PyBtcAddress objects
      self.commentsMap = {}  # maps 20-byte addresses to user-created comments
      self.commentLocs = {}  # map comment keys to wallet file locations
      self.opevalMap   = {}  # maps 20-byte addresses to OP_EVAL data (future)
      self.labelName   = ''
      self.labelDescr  = ''
      self.linearAddr160List = []
      self.chainIndexMap = {}
      self.txAddrMap = {}    # cache for getting tx-labels based on addr search
      if USE_TESTNET or USE_REGTEST:
         self.addrPoolSize = 10  # this makes debugging so much easier!
      else:
         self.addrPoolSize = CLI_OPTIONS.keypool
         
      self.importList = []

      # For file sync features
      self.walletPath = ''
      self.doBlockchainSync = BLOCKCHAIN_READONLY
      self.lastSyncBlockNum = 0

      # Private key encryption details
      self.useEncryption  = False
      self.kdf            = None
      self.crypto         = None
      self.kdfKey         = None
      self.defaultKeyLifetime = 10    # seconds after unlock, that key is discarded
      self.lockWalletAtTime   = 0    # seconds after unlock, that key is discarded
      self.isLocked       = False
      self.testedComputeTime=None

      # Deterministic wallet, need a root key.  Though we can still import keys.
      # The unique ID contains the network byte (id[-1]) but is not intended to
      # resemble the address of the root key
      self.uniqueIDBin = ''
      self.uniqueIDB58 = ''   # Base58 version of reversed-uniqueIDBin
      self.lastComputedChainAddr160  = ''
      self.lastComputedChainIndex = 0
      self.highestUsedChainIndex  = 0 

      # All PyBtcAddress serializations are exact same size, figure it out now
      self.pybtcaddrSize = len(PyBtcAddress().serialize())


      # Finally, a bunch of offsets that tell us where data is stored in the
      # file: this can be generated automatically on unpacking (meaning it
      # doesn't require manually updating offsets if I change the format), and
      # will save us a couple lines of code later, when we need to update things
      self.offsetWltFlags  = -1
      self.offsetLabelName = -1
      self.offsetLabelDescr  = -1
      self.offsetTopUsed   = -1
      self.offsetRootAddr  = -1
      self.offsetKdfParams = -1
      self.offsetCrypto    = -1

      # These flags are ONLY for unit-testing the walletFileSafeUpdate function
      self.interruptTest1  = False
      self.interruptTest2  = False
      self.interruptTest3  = False
      
      #flags the wallet if it has off chain imports (from a consistency repair)
      self.hasNegativeImports = False
      
      #To enable/disable wallet row in wallet table model
      self.isEnabled = True
      
      self.mutex = threading.Lock()
      
      #list of callables and their args to perform after a wallet 
      #has been scanned. Entries are order as follows:
      #[[method1, [arg1, ar2, arg3]], [method2, [arg1, arg2]]]
      #list is cleared after each scan.
      self.actionsToTakeAfterScan = []
      
      self.balance_spendable = 0
      self.balance_unconfirmed = 0
      self.balance_full = 0
      self.txnCount = 0
      
      self.addrTxnCountDict = {}
      self.addrBalanceDict = {}
      
   #############################################################################
   def registerWallet(self, isNew=False):
      if self.cppWallet == None:
         raise Exception('invalid cppWallet object')
      
      #this returns a copy of a BtcWallet C++ object. This object is
      #instantiated at registration and is unique for the BDV object, so we
      #should only ever set the cppWallet member here 
      
      try:
         self.cppWallet.registerWithBDV(isNew)
      except:
         pass
            
   #############################################################################
   def isWltSigningAnyLockbox(self, lockboxList):
      for lockbox in lockboxList:
         for addr160 in lockbox.a160List:
            if self.addrMap.has_key(addr160):
               return True
      return False

   #############################################################################
   def getWalletVersion(self):
      return (getVersionInt(self.version), getVersionString(self.version))

   #############################################################################
   def getTimeRangeForAddress(self, addr160):
      if not self.addrMap.has_key(addr160):
         return None
      else:
         return self.addrMap[addr160].getTimeRange()

   #############################################################################
   def getBlockRangeForAddress(self, addr160):
      if not self.addrMap.has_key(addr160):
         return None
      else:
         return self.addrMap[addr160].getBlockRange()

   #############################################################################
   def setBlockchainSyncFlag(self, syncYes=True):
      self.doBlockchainSync = syncYes

   #############################################################################
   def getCommentForAddrBookEntry(self, abe):
      comment = self.getComment(abe.getAddr160())
      if len(comment)>0:
         return comment

      # SWIG BUG! 
      # http://sourceforge.net/tracker/?func=detail&atid=101645&aid=3403085&group_id=1645
      # Apparently, using the -threads option when compiling the swig module
      # causes the "for i in vector<...>:" mechanic to sometimes throw seg faults!
      # For this reason, this method was replaced with the one below:
      for regTx in abe.getTxList():
         comment = self.getComment(regTx.getTxHash())
         if len(comment)>0:
            return comment

      return ''
      
   #############################################################################
   def getCommentForTxList(self, a160, txhashList):
      comment = self.getComment(a160)
      if len(comment)>0:
         return comment

      for txHash in txhashList:
         comment = self.getComment(txHash)
         if len(comment)>0:
            return comment

      return ''

   #############################################################################
   @CheckWalletRegistration
   def printAddressBook(self):
      addrbook = self.cppWallet.createAddressBook()
      for abe in addrbook:
         print hash160_to_addrStr(abe.getAddr160()),
         txlist = abe.getTxList()
         print len(txlist)
         for rtx in txlist:
            print '\t', binary_to_hex(rtx.getTxHash(), BIGENDIAN)
         
   #############################################################################
   def hasAnyImported(self):
      for a160,addr in self.addrMap.iteritems():
         if addr.chainIndex == -2:
            return True
      return False
   
   def isRegistered(self):
      return not self.cppWallet == None 

   #############################################################################
   # The IGNOREZC args on the get*Balance calls determine whether unconfirmed
   # change (sent-to-self) will be considered spendable or unconfirmed.  This
   # was added after the malleability issues cropped up in Feb 2014.  Zero-conf
   # change was always deprioritized, but using --nospendzeroconfchange makes
   # it totally unspendable
   def getBalance(self, balType="Spendable"):
      if balType.lower() in ('spendable','spend'):
         return self.balance_spendable
         #return self.cppWallet.getSpendableBalance(topBlockHeight, IGNOREZC)
      elif balType.lower() in ('unconfirmed','unconf'):
         #return self.cppWallet.getUnconfirmedBalance(topBlockHeight, IGNOREZC)
         return self.balance_unconfirmed
      elif balType.lower() in ('total','ultimate','unspent','full'):
         #return self.cppWallet.getFullBalance()
         return self.balance_full
      else:
         raise TypeError('Unknown balance type! "' + balType + '"')
      
   #############################################################################
   def getTxnCount(self):
      return self.txnCount
   
   #############################################################################  
   def getBalancesAndCountFromDB(self):
      if self.cppWallet != None and TheBDM.getState() is BDM_BLOCKCHAIN_READY:
         topBlockHeight = TheBDM.getTopBlockHeight()
         balanceVector = self.cppWallet.getBalancesAndCount(\
                     topBlockHeight, IGNOREZC)
         self.balance_full = balanceVector[0]
         self.balance_spendable = balanceVector[1]
         self.balance_unconfirmed = balanceVector[2]
         self.txnCount = balanceVector[3]

   #############################################################################
   @CheckWalletRegistration
   def getAddrBalance(self, addr160, balType="Spendable", topBlockHeight=UINT32_MAX):
      if not self.hasAddr(addr160):
         return -1
      else:
         try:
            scraddr = Hash160ToScrAddr(addr160)
            addrBalances = self.addrBalanceDict[scraddr]
         except:
            return 0
         
         if balType.lower() in ('spendable','spend'):
            return addrBalances[1]
         elif balType.lower() in ('unconfirmed','unconf'):
            return addrBalances[2]
         elif balType.lower() in ('ultimate','unspent','full'):
            return addrBalances[0]
         else:
            raise TypeError('Unknown balance type!')



   #############################################################################
   @CheckWalletRegistration
   def getTxLedger(self, ledgType='Full'):
      """ 
      Gets the ledger entries for the entire wallet, from C++/SWIG data structs
      """
      ledgBlkChain = self.getHistoryPage(0)
      ledg = []
      ledg.extend(ledgBlkChain)
      return ledg

   #############################################################################
   @CheckWalletRegistration
   def getUTXOListForSpendVal(self, valToSpend = 2**64 - 1):
      """ Returns UnspentTxOut/C++ objects 
      returns a set of unspent TxOuts to cover for the value to spend 
      """
      
      if not self.doBlockchainSync==BLOCKCHAIN_DONOTUSE:
         from CoinSelection import PyUnspentTxOut
         utxos = self.cppWallet.getSpendableTxOutListForValue(valToSpend)
         utxoList = []
         for i in range(len(utxos)):
            utxoList.append(PyUnspentTxOut().createFromCppUtxo(utxos[i]))
         return utxoList
      else:
         LOGERROR('***Blockchain is not available for accessing wallet-tx data')
         return []

   #############################################################################
   @CheckWalletRegistration
   def getFullUTXOList(self):
      """ Returns UnspentTxOut/C++ objects
      
      DO NOT USE THIS CALL UNLESS NECESSARY.
      This call returns *ALL* of the wallet's UTXOs. If your intent is to get
      UTXOs to spend coins, use getUTXOListForSpendVal and pass the amount you 
      want to spend as the argument.
      
      If you want to get UTXOs for browsing the history, use 
      getUTXOListForBlockRange with the top and bottom block of the desired range
      """
      
      #return full set of unspent TxOuts
      if not self.doBlockchainSync==BLOCKCHAIN_DONOTUSE:
         #calling this with no value argument will return the full UTXO list
         from CoinSelection import PyUnspentTxOut
         utxos = self.cppWallet.getSpendableTxOutListForValue()
         utxoList = []
         for i in range(len(utxos)):
            utxoList.append(PyUnspentTxOut().createFromCppUtxo(utxos[i]))
         return utxoList         
      else:
         LOGERROR('***Blockchain is not available for accessing wallet-tx data')
         return []

   #############################################################################
   @CheckWalletRegistration
   def getZCUTXOList(self):
      #return full set of unspent ZC outputs
      if not self.doBlockchainSync==BLOCKCHAIN_DONOTUSE:
         from CoinSelection import PyUnspentTxOut
         utxos = self.cppWallet.getSpendableZCList()
         utxoList = []
         for i in range(len(utxos)):
            utxoList.append(PyUnspentTxOut().createFromCppUtxo(utxos[i]))
         return utxoList         
      else:
         LOGERROR('***Blockchain is not available for accessing wallet-tx data')
         return []
      
   #############################################################################
   @CheckWalletRegistration
   def getRBFTxOutList(self):
      #return full set of unspent ZC outputs
      if not self.doBlockchainSync==BLOCKCHAIN_DONOTUSE:
         from CoinSelection import PyUnspentTxOut
         utxos = self.cppWallet.getRBFTxOutList()
         utxoList = []
         for i in range(len(utxos)):
            utxoList.append(PyUnspentTxOut().createFromCppUtxo(utxos[i]))
         return utxoList         
      else:
         LOGERROR('***Blockchain is not available for accessing wallet-tx data')
         return []

   #############################################################################
   @CheckWalletRegistration
   def getUTXOListForBlockRange(self, startBlock, endBlock):
      """ Returns UnspentTxOut/C++ objects 
      
      returns all unspent TxOuts in the block range
      """
      raise NotImplemented

   #############################################################################
   @CheckWalletRegistration
   def getAddrTxOutList(self, addr160, txType='Spendable'):
      """
      deprecated call, use getFullUTXOList instead
      """
      
      raise NotImplemented
      
      """ Returns UnspentTxOut/C++ objects """
      if not self.doBlockchainSync==BLOCKCHAIN_DONOTUSE:

         topBlockHeight = TheBDM.getTopBlockHeight()
    
         # Removed this line of code because it's part of the old BDM paradigm. 
         # Leaving this comment here in case it needs to be replaced by anything
         # self.syncWithBlockchainLite()
         scrAddrStr = Hash160ToScrAddr(addr160)
         cppAddr = self.cppWallet.getScrAddrObjByKey(scrAddrStr)
         if txType.lower() in ('spend', 'spendable'):
            return cppAddr.getSpendableTxOutList(IGNOREZC);
         elif txType.lower() in ('full', 'all', 'unspent', 'ultimate'):
            return cppAddr.getFullTxOutList(topBlockHeight, IGNOREZC);
         else:
            raise TypeError('Unknown TxOutList type! ' + txType)
      else:
         LOGERROR('***Blockchain is not available for accessing wallet-tx data')
         return []


   #############################################################################
   def getAddrByHash160(self, addr160):
      return (None if not self.hasAddr(addr160) else self.addrMap[addr160])

   #############################################################################
   def hasScrAddr(self, scrAddr):
      """
      Wallets currently only hold P2PKH scraddrs, so if it's not that, False
      """
      if not scrAddr[0] == ADDRBYTE or not len(scrAddr)==21:
         try:
            return self.cppWallet.hasScrAddr(scrAddr)
         except:
            return False

      # For P2PKH scraddrs, the first byte is prefix, next 20 bytes is addr160
      return self.hasAddr(scrAddr[1:])


   #############################################################################
   def hasAddr(self, addrData):
      if isinstance(addrData, str):
         if len(addrData) == 20:
            return self.addrMap.has_key(addrData)
         elif isLikelyDataType(addrData)==DATATYPE.Base58:
            return self.addrMap.has_key(addrStr_to_hash160(addrData)[1])
         else:
            return False
      elif isinstance(addrData, PyBtcAddress):
         return self.addrMap.has_key(addrData.getAddr160())
      else:
         return False


   #############################################################################
   def setDefaultKeyLifetime(self, newlifetime):
      """ Set a new default lifetime for holding the unlock key. Min 2 sec """
      self.defaultKeyLifetime = max(newlifetime, 2)

   #############################################################################
   def checkWalletLockTimeout(self):
      if not self.isLocked and self.kdfKey and RightNow()>self.lockWalletAtTime:
         self.lock()
         if self.kdfKey:
            self.kdfKey.destroy()
         self.kdfKey = None

         if self.useEncryption:
            self.isLocked = True



   #############################################################################
   @CheckWalletRegistration
   def lockTxOutsOnNewTx(self, pytxObj):
      for txin in pytxObj.inputs:
         self.cppWallet.lockTxOutSwig(txin.outpoint.txHash, \
                                      txin.outpoint.txOutIndex)

   
   #############################################################################
   #  THIS WAS CREATED ORIGINALLY TO SUPPORT BITSAFE INTEGRATION INTO ARMORY
   #  But it's also a good first step into general BIP 32 support
   def getChildExtPubFromRoot(self, i):
      root = self.addrMap['ROOT']
      ekey = ExtendedKey().CreateFromPublic(root.binPublicKey65, root.chaincode)
      newKey = HDWalletCrypto().ChildKeyDeriv(ekey, i)
      newKey.setIndex(i)
      return newKey
      #newAddr = PyBtcAddress().createFromExtendedPublicKey(newKey)

   #############################################################################
   #def createFromExtendedPublicKey(self, ekey):
      #pub65 = ekey.getPub()
      #chain = ekey.getChain()
      #newAddr = self.createFromPublicKeyData(pub65, chain)
      #newAddr.chainIndex = newAddr.getIndex()
      #return newAddr

   #############################################################################
   #def deriveChildPublicKey(self, i):
      #newKey = HDWalletCrypto().ChildKeyDeriv(self.getExtendedPublicKey(), i)
      #newAddr = PyBtcAddress().createFromExtendedPublicKey(newKey)
   
   #############################################################################
   # Copy the wallet file to backup
   def backupWalletFile(self, backupPath = None):
      '''Function that attempts to make a backup copy of the wallet to the file
         in a given path and returns whether or not the copy succeeded.'''

      # Assume upfront that the copy will work.
      retVal = True

      walletFileBackup = self.getWalletPath('backup') if backupPath == None \
                                                               else backupPath
      try:
         shutil.copy(self.walletPath, walletFileBackup)
      except IOError, errReason:
         LOGERROR('Unable to copy file %s' % backupPath)
         LOGERROR('Reason for copy failure: %s' % errReason)
         retVal = False

      return retVal


   #############################################################################
   #  THIS WAS CREATED ORIGINALLY TO SUPPORT BITSAFE INTEGRATION INTO ARMORY
   #  But it's also a good first step into general BIP 32 support
   def createWalletFromMasterPubKey(self, masterHex, \
                                          isActuallyNew=True, \
                                          doRegisterWithBDM=True):
      # This function eats hex inputs. (Not sure why I chose to do that.)
      # B/c we have a known starting pt. for keys, use that instead of trying to
      # index off a chaincode value, as the value could be in the key.
      p0 = masterHex.index('4104') + 1
      pubkey = SecureBinaryData(hex_to_binary(masterHex[p0:p0+130]))
      c0 = masterHex.index('4104') + 66
      chain = SecureBinaryData(hex_to_binary(masterHex[c0:c0+64]))

      # Create the root address object
      rootAddr = PyBtcAddress().createFromPublicKeyData( pubkey )
      rootAddr.markAsRootAddr(chain)
      self.addrMap['ROOT'] = rootAddr

      ekey = self.getChildExtPubFromRoot(0)
      firstAddr = PyBtcAddress().createFromPublicKeyData(ekey.getPub())
      firstAddr.chaincode = ekey.getChain()
      firstAddr.chainIndex = 0
      first160  = firstAddr.getAddr160()

      # Update wallet object with the new data
      # NEW IN WALLET VERSION 1.35:  unique ID is now based on
      # the first chained address: this guarantees that the unique ID
      # is based not only on the private key, BUT ALSO THE CHAIN CODE
      self.useEncryption = False
      self.addrMap[firstAddr.getAddr160()] = firstAddr
      self.uniqueIDBin = (ADDRBYTE + firstAddr.getAddr160()[:5])[::-1]
      self.uniqueIDB58 = binary_to_base58(self.uniqueIDBin)
      self.labelName  = 'BitSafe Demo Wallet'
      self.labelDescr = 'We\'ll be lucky if this works!'
      self.lastComputedChainAddr160 = first160
      self.lastComputedChainIndex  = firstAddr.chainIndex
      self.highestUsedChainIndex   = firstAddr.chainIndex-1
      self.wltCreateDate = long(RightNow())
      self.linearAddr160List = [first160]
      self.chainIndexMap[firstAddr.chainIndex] = first160
      self.watchingOnly = True

      # We don't have to worry about atomic file operations when
      # creating the wallet: so we just do it naively here.
      newWalletFilePath = os.path.join(ARMORY_HOME_DIR, 'bitsafe_demo_%s.wallet' % self.uniqueIDB58)
      self.walletPath = newWalletFilePath
      if not newWalletFilePath:
         shortName = self.labelName .replace(' ','_')
         # This was really only needed when we were putting name in filename
         #for c in ',?;:\'"?/\\=+-|[]{}<>':
            #shortName = shortName.replace(c,'_')
         newName = buildWltFileName(self.uniqueIDB58)
         self.walletPath = os.path.join(ARMORY_HOME_DIR, newName)

      LOGINFO('   New wallet will be written to: %s', self.walletPath)
      newfile = open(self.walletPath, 'wb')
      fileData = BinaryPacker()

      # packHeader method writes KDF params and root address
      headerBytes = self.packHeader(fileData)

      # We make sure we have byte locations of the two addresses, to start
      self.addrMap[first160].walletByteLoc = headerBytes + 21

      fileData.put(BINARY_CHUNK, '\x00' + first160 + firstAddr.serialize())


      # Store the current localtime and blocknumber.  Block number is always 
      # accurate if available, but time may not be exactly right.  Whenever 
      # basing anything on time, please assume that it is up to one day off!
      time0,blk0 = getCurrTimeAndBlock() if isActuallyNew else (0,0)

      # Don't forget to sync the C++ wallet object
      newfile.write(fileData.getBinaryString())
      newfile.flush()
      os.fsync(newfile.fileno())
      newfile.close()

      walletFileBackup = self.getWalletPath('backup')
      shutil.copy(self.walletPath, walletFileBackup)


      # Let's fill the address pool while we are unlocked
      # It will get a lot more expensive if we do it on the next unlock
      self.fillAddressPool(self.addrPoolSize, isActuallyNew=isActuallyNew, doRegister=doRegisterWithBDM)

      return self


   #############################################################################
   def createNewWalletFromPKCC(self, plainPubKey, chaincode, newWalletFilePath=None, \
                               isActuallyNew=False, doRegisterWithBDM=True, \
                               skipBackupFile=False):
      """
      This method will create a new wallet based on a root public key, chain
      code and wallet ID.
      """

      LOGINFO('***Creating watching-only wallet from a public key & chain code')

      # Prep for C++ usage, then create the root address object and first public
      # address and its Hash160.
      plainPubKey = SecureBinaryData(plainPubKey)
      chaincode = SecureBinaryData(chaincode)
      rootAddr = PyBtcAddress().createFromPublicKeyData(plainPubKey)
      rootAddr.markAsRootAddr(chaincode)
      firstAddr = rootAddr.extendAddressChain()
      first160  = firstAddr.getAddr160()

      # Update wallet object with the new data.
      # NEW IN WALLET VERSION 1.35: unique ID is now based on the first chained
      # address. This guarantees that the unique ID is based not only on the
      # private key, BUT ALSO THE CHAIN CODE.
      self.useEncryption = False
      self.watchingOnly = True
      self.wltCreateDate = long(RightNow())

      self.addrMap['ROOT'] = rootAddr
      self.addrMap[firstAddr.getAddr160()] = firstAddr
      self.uniqueIDBin = (ADDRBYTE + firstAddr.getAddr160()[:5])[::-1]
      self.uniqueIDB58 = binary_to_base58(self.uniqueIDBin)
      self.labelName  = (self.uniqueIDB58 + ' (Watch)')[:32]
      self.labelDescr  = (self.uniqueIDB58 + ' (Watching-only copy)')[:256]
      self.lastComputedChainAddr160 = first160
      self.lastComputedChainIndex  = firstAddr.chainIndex
      self.highestUsedChainIndex   = firstAddr.chainIndex-1
      self.linearAddr160List = [first160]
      self.chainIndexMap[firstAddr.chainIndex] = first160

      # We don't have to worry about atomic file operations when creating the
      # wallet, so we just do it here, naively.
      self.walletPath = newWalletFilePath
      if not newWalletFilePath:
         shortName = self.labelName .replace(' ','_')
         # This was really only needed when we were putting name in filename
         #for c in ',?;:\'"?/\\=+-|[]{}<>':
            #shortName = shortName.replace(c,'_')
         newName = 'armory_%s_WatchOnly.wallet' % self.uniqueIDB58
         self.walletPath = os.path.join(ARMORY_HOME_DIR, newName)

      # Start writing the wallet.
      LOGINFO('   New wallet will be written to: %s', self.walletPath)
      newfile = open(self.walletPath, 'wb')
      fileData = BinaryPacker()

      # packHeader method writes KDF params and root address
      headerBytes = self.packHeader(fileData)

      # We make sure we have byte locations of the two addresses, to start
      self.addrMap[first160].walletByteLoc = headerBytes + 21

      fileData.put(BINARY_CHUNK, '\x00' + first160 + firstAddr.serialize())

      # Store the current localtime and blocknumber. Block number is always 
      # accurate if available, but time may not be exactly right. Whenever 
      # basing anything on time, please assume that it is up to one day off!
      time0,blk0 = getCurrTimeAndBlock() if isActuallyNew else (0,0)

      # Write the actual wallet file and close it. Create a backup if necessary.
      newfile.write(fileData.getBinaryString())
      newfile.close()

      if not skipBackupFile:
         walletFileBackup = self.getWalletPath('backup')
         shutil.copy(self.walletPath, walletFileBackup)

      # Let's fill the address pool while we are unlocked. It will get a lot
      # more expensive if we do it on the next unlock.
      self.fillAddressPool(self.addrPoolSize, isActuallyNew=isActuallyNew, doRegister=doRegisterWithBDM)

      return self


   #############################################################################
   def createNewWallet(self, newWalletFilePath=None, \
                             plainRootKey=None, chaincode=None, \
                             withEncrypt=True, IV=None, securePassphrase=None, \
                             kdfTargSec=DEFAULT_COMPUTE_TIME_TARGET, \
                             kdfMaxMem=DEFAULT_MAXMEM_LIMIT, \
                             shortLabel='', longLabel='', isActuallyNew=True, \
                             doRegisterWithBDM=True, skipBackupFile=False, \
                             extraEntropy=None, Progress=emptyFunc, \
                             armoryHomeDir = ARMORY_HOME_DIR):
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

      if securePassphrase:
         securePassphrase = SecureBinaryData(securePassphrase)
      if plainRootKey:
         plainRootKey = SecureBinaryData(plainRootKey)
      if chaincode:
         chaincode = SecureBinaryData(chaincode)

      if withEncrypt and not securePassphrase:
         raise EncryptionError('Cannot create encrypted wallet without passphrase')

      LOGINFO('***Creating new deterministic wallet')

      # Set up the KDF
      if not withEncrypt:
         self.kdfKey = None
      else:
         LOGINFO('(with encryption)')
         self.kdf = KdfRomix()
         LOGINFO('Target (time,RAM)=(%0.3f,%d)', kdfTargSec, kdfMaxMem)
         (mem,niter,salt) = self.computeSystemSpecificKdfParams( \
                                                kdfTargSec, kdfMaxMem)
         self.kdf.usePrecomputedKdfParams(mem, niter, salt)
         self.kdfKey = self.kdf.DeriveKey(securePassphrase)

      if not plainRootKey:
         # TODO: We should find a source for injecting extra entropy
         #       At least, Crypto++ grabs from a few different sources, itself
         if not extraEntropy:
            extraEntropy = SecureBinaryData(0)
         plainRootKey = SecureBinaryData().GenerateRandom(32, extraEntropy)

      if not chaincode:
         #chaincode = SecureBinaryData().GenerateRandom(32)
         # For wallet 1.35a, derive chaincode deterministically from root key
         # The root key already has 256 bits of entropy which is excessive,
         # anyway.  And my original reason for having the chaincode random is 
         # no longer valid.
         chaincode = DeriveChaincodeFromRootKey(plainRootKey)
            
                             

      # Create the root address object
      rootAddr = PyBtcAddress().createFromPlainKeyData( \
                                             plainRootKey, \
                                             IV16=IV, \
                                             willBeEncr=withEncrypt, \
                                             generateIVIfNecessary=True)
      rootAddr.markAsRootAddr(chaincode)

      # This does nothing if no encryption
      rootAddr.lock(self.kdfKey)
      rootAddr.unlock(self.kdfKey)

      firstAddr = rootAddr.extendAddressChain(self.kdfKey)
      first160  = firstAddr.getAddr160()

      # Update wallet object with the new data
      # NEW IN WALLET VERSION 1.35:  unique ID is now based on
      # the first chained address: this guarantees that the unique ID
      # is based not only on the private key, BUT ALSO THE CHAIN CODE
      self.useEncryption = withEncrypt
      self.addrMap['ROOT'] = rootAddr
      self.addrMap[firstAddr.getAddr160()] = firstAddr
      self.uniqueIDBin = (ADDRBYTE + firstAddr.getAddr160()[:5])[::-1]
      self.uniqueIDB58 = binary_to_base58(self.uniqueIDBin)
      self.labelName  = shortLabel[:32]   # aka "Wallet Name"
      self.labelDescr  = longLabel[:256]  # aka "Description"
      self.lastComputedChainAddr160 = first160
      self.lastComputedChainIndex  = firstAddr.chainIndex
      self.highestUsedChainIndex   = firstAddr.chainIndex-1
      self.wltCreateDate = long(RightNow())
      self.linearAddr160List = [first160]
      self.chainIndexMap[firstAddr.chainIndex] = first160

      # We don't have to worry about atomic file operations when
      # creating the wallet: so we just do it naively here.
      self.walletPath = newWalletFilePath
      if not newWalletFilePath:
         shortName = self.labelName .replace(' ','_')
         # This was really only needed when we were putting name in filename
         #for c in ',?;:\'"?/\\=+-|[]{}<>':
            #shortName = shortName.replace(c,'_')
         newName = buildWltFileName(self.uniqueIDB58)
         self.walletPath = os.path.join(armoryHomeDir, newName)

      LOGINFO('   New wallet will be written to: %s', self.walletPath)
      newfile = open(self.walletPath, 'wb')
      fileData = BinaryPacker()

      # packHeader method writes KDF params and root address
      headerBytes = self.packHeader(fileData)

      # We make sure we have byte locations of the two addresses, to start
      self.addrMap[first160].walletByteLoc = headerBytes + 21

      fileData.put(BINARY_CHUNK, '\x00' + first160 + firstAddr.serialize())


      # Store the current localtime and blocknumber.  Block number is always 
      # accurate if available, but time may not be exactly right.  Whenever 
      # basing anything on time, please assume that it is up to one day off!
      time0,blk0 = getCurrTimeAndBlock() if isActuallyNew else (0,0)

      newfile.write(fileData.getBinaryString())
      newfile.close()

      if not skipBackupFile:
         walletFileBackup = self.getWalletPath('backup')
         shutil.copy(self.walletPath, walletFileBackup)

      # Lock/unlock to make sure encrypted keys are computed and written to file
      if self.useEncryption:
         self.unlock(secureKdfOutput=self.kdfKey, Progress=Progress)

      # Let's fill the address pool while we are unlocked
      # It will get a lot more expensive if we do it on the next unlock
      self.fillAddressPool(self.addrPoolSize, isActuallyNew=isActuallyNew,
                              Progress=Progress, doRegister=doRegisterWithBDM)

      if self.useEncryption:
         self.lock()
         
      return self

   #############################################################################
   def advanceHighestIndex(self, ct=1, isNew=False):
      topIndex = self.highestUsedChainIndex + ct
      topIndex = min(topIndex, self.lastComputedChainIndex)
      topIndex = max(topIndex, 0)

      self.highestUsedChainIndex = topIndex
      self.walletFileSafeUpdate( [[WLT_UPDATE_MODIFY, self.offsetTopUsed, \
                    int_to_binary(self.highestUsedChainIndex, widthBytes=8)]])
      self.fillAddressPool(isActuallyNew=isNew)
      
   #############################################################################
   def rewindHighestIndex(self, ct=1):
      self.advanceHighestIndex(-ct)


   #############################################################################
   def peekNextUnusedAddr160(self):
      return self.getAddress160ByChainIndex(self.highestUsedChainIndex+1)
   
   #############################################################################
   def peekNextUnusedAddr(self):
      return self.addrMap[self.getAddress160ByChainIndex(self.highestUsedChainIndex+1)]
   
   #############################################################################
   def getNextUnusedAddress(self):
      if self.lastComputedChainIndex - self.highestUsedChainIndex < \
                                              max(self.addrPoolSize,1):
         self.fillAddressPool(self.addrPoolSize, True)

      self.advanceHighestIndex(1, True)
      new160 = self.getAddress160ByChainIndex(self.highestUsedChainIndex)
      self.addrMap[new160].touch()
      self.walletFileSafeUpdate( [[WLT_UPDATE_MODIFY, \
                                  self.addrMap[new160].walletByteLoc, \
                                  self.addrMap[new160].serialize()]]  )
      return self.addrMap[new160]


   #############################################################################
   def computeNextAddress(self, addr160=None, isActuallyNew=True, doRegister=True):
      """
      Use this to extend the chain beyond the last-computed address.

      We will usually be computing the next address from the tip of the 
      chain, but I suppose someone messing with the file format may
      leave gaps in the chain requiring some to be generated in the middle
      (then we can use the addr160 arg to specify which address to extend)
      """
      if not addr160:
         addr160 = self.lastComputedChainAddr160

      newAddr = self.addrMap[addr160].extendAddressChain(self.kdfKey)
      new160 = newAddr.getAddr160()
      newDataLoc = self.walletFileSafeUpdate( \
         [[WLT_UPDATE_ADD, WLT_DATATYPE_KEYDATA, new160, newAddr]])
      self.addrMap[new160] = newAddr
      self.addrMap[new160].walletByteLoc = newDataLoc[0] + 21

      if newAddr.chainIndex > self.lastComputedChainIndex:
         self.lastComputedChainAddr160 = new160
         self.lastComputedChainIndex = newAddr.chainIndex

      self.linearAddr160List.append(new160)
      self.chainIndexMap[newAddr.chainIndex] = new160
         
      if self.cppWallet != None:      
         needsRegistered = \
            self.cppWallet.extendAddressChainTo(self.lastComputedChainIndex)  
         
         #grab cpp addr as default addr type
         addrType = armoryengine.ArmoryUtils.DEFAULT_ADDR_TYPE
         
         if addrType == 'P2PKH':
            self.getP2PKHAddrForIndex(newAddr.chainIndex)
         elif addrType == 'P2SH-P2WPKH':
            self.getNestedSWAddrForIndex(newAddr.chainIndex)
         elif addrType == 'P2SH-P2PK':
            self.getNestedP2PKAddrForIndex(newAddr.chainIndex)
         
         if doRegister and self.isRegistered() and needsRegistered:
               self.cppWallet.registerWithBDV(isActuallyNew)

      return new160
      
   #############################################################################
   def fillAddressPool(self, numPool=None, isActuallyNew=True, 
                       doRegister=True, Progress=emptyFunc):
      """
      Usually, when we fill the address pool, we are generating addresses
      for the first time, and thus there is no chance it's ever seen the
      blockchain.  However, this method is also used for recovery/import 
      of wallets, where the address pool has addresses that probably have
      transactions already in the blockchain.  
      """
      if not numPool:
         numPool = self.addrPoolSize

      lastComputedIndex = self.lastComputedChainIndex
      gap = self.lastComputedChainIndex - self.highestUsedChainIndex
      numToCreate = max(numPool - gap, 0)
      
      newAddrList = []
      
      for i in range(numToCreate):
         Progress(i+1, numToCreate)
         newAddrList.append(Hash160ToScrAddr(self.computeNextAddress(\
                                 isActuallyNew=isActuallyNew, \
                                 doRegister=False))) 
                  
      #add addresses in bulk once they are all computed   
      if doRegister and self.isRegistered() and numToCreate > 0:
         try:
            self.cppWallet.registerWithBDV(isActuallyNew)
            self.actionsToTakeAfterScan.append([self.detectHighestUsedIndex], [])
         except:
            pass
         
      return self.lastComputedChainIndex

   #############################################################################
   def setAddrPoolSize(self, newSize):
      if newSize<5:
         LOGERROR('Will not allow address pool sizes smaller than 5...')
         return

      self.addrPoolSize = newSize
      self.fillAddressPool(newSize)


   #############################################################################
   def getHighestUsedIndex(self):
      """ 
      This only retrieves the stored value, but it may not be correct if,
      for instance, the wallet was just imported but has been used before.
      """
      return self.highestUsedChainIndex

          
   #############################################################################
   def getHighestComputedIndex(self):
      """ 
      This only retrieves the stored value, but it may not be correct if,
      for instance, the wallet was just imported but has been used before.
      """
      return self.lastComputedChainIndex
      

         
   #############################################################################
   @CheckWalletRegistration
   def detectHighestUsedIndex(self):
      """
      This method is used to find the highestUsedChainIndex value of the 
      wallet WITHIN its address pool.  It will NOT extend its address pool
      in this search, because it is assumed that the wallet couldn't have
      used any addresses it had not calculated yet.

      If you have a wallet IMPORT, though, or a wallet that has been used
      before but does not have this information stored with it, then you
      should be using the next method:

            self.freshImportFindHighestIndex()

      which will actually extend the address pool as necessary to find the
      highest address used.      
      """
        
      highestIndex = self.cppWallet.detectHighestUsedIndex()


      if highestIndex > self.highestUsedChainIndex:
         self.highestUsedChainIndex = highestIndex
         self.walletFileSafeUpdate( [[WLT_UPDATE_MODIFY, self.offsetTopUsed, \
                                      int_to_binary(highestIndex, widthBytes=8)]])


      return highestIndex

         


   #############################################################################
   @TimeThisFunction
   def freshImportFindHighestIndex(self, stepSize=None):
      """ 
      This is much like detectHighestUsedIndex, except this will extend the
      address pool as necessary.  It assumes that you have a fresh wallet
      that has been used before, but was deleted and restored from its root
      key and chaincode, and thus we don't know if only 10 or 10,000 addresses
      were used.

      If this was an exceptionally active wallet, it's possible that we
      may need to manually increase the step size to be sure we find  
      everything.  In fact, there is no way to tell FOR SURE what is the
      last addressed used: one must make an assumption that the wallet 
      never calculated more than X addresses without receiving a payment...
      """
      if not stepSize:
         stepSize = self.addrPoolSize

      topCompute = 0
      topUsed    = 0
      oldPoolSize = self.addrPoolSize
      self.addrPoolSize = stepSize
      # When we hit the highest address, the topCompute value will extend
      # out [stepsize] addresses beyond topUsed, and the topUsed will not
      # change, thus escaping the while loop
      nWhile = 0
      while topCompute - topUsed < 0.9*stepSize:
         topCompute = self.fillAddressPool(stepSize, isActuallyNew=False)
         topUsed = self.detectHighestUsedIndex()
         nWhile += 1
         if nWhile>10000:
            raise WalletAddressError('Escaping inf loop in freshImport...')
            

      self.addrPoolSize = oldPoolSize
      return topUsed


   #############################################################################
   def writeFreshWalletFile(self, path, newName='', newDescr=''):
      newFile = open(path, 'wb')
      bp = BinaryPacker()
      self.packHeader(bp)
      newFile.write(bp.getBinaryString())

      for addr160,addrObj in self.addrMap.iteritems():
         if not addr160=='ROOT':
            newFile.write('\x00' + addr160 + addrObj.serialize())

      for hashVal,comment in self.commentsMap.iteritems():
         twoByteLength = int_to_binary(len(comment), widthBytes=2)
         if len(hashVal)==20:
            typestr = int_to_binary(WLT_DATATYPE_ADDRCOMMENT)
            newFile.write(typestr + hashVal + twoByteLength + comment)
         elif len(hashVal)==32:
            typestr = int_to_binary(WLT_DATATYPE_TXCOMMENT)
            newFile.write(typestr + hashVal + twoByteLength + comment)

      newFile.close()

   
   #############################################################################
   def makeUnencryptedWalletCopy(self, newPath, securePassphrase=None):

      self.writeFreshWalletFile(newPath)
      if not self.useEncryption:
         return True

      if self.isLocked:
         if not securePassphrase:
            LOGERROR('Attempted to make unencrypted copy without unlocking')
            return False
         else:
            self.unlock(securePassphrase=SecureBinaryData(securePassphrase))

      newWlt = PyBtcWallet().readWalletFile(newPath)
      newWlt.unlock(self.kdfKey)
      newWlt.changeWalletEncryption(None)

      
      walletFileBackup = newWlt.getWalletPath('backup')
      if os.path.exists(walletFileBackup):
         LOGINFO('New wallet created, deleting backup file')
         os.remove(walletFileBackup)
      return True
      
      
   #############################################################################
   def makeEncryptedWalletCopy(self, newPath, securePassphrase=None):
      """
      Unlike the previous method, I can't just copy it if it's unencrypted, 
      because the target device probably shouldn't be exposed to the 
      unencrypted wallet.  So for that case, we will encrypt the wallet 
      in place, copy, then remove the encryption.
      """

      if self.useEncryption:
         # Encrypted->Encrypted:  Easy!
         self.writeFreshWalletFile(newPath)
         return True
         
      if not securePassphrase:
         LOGERROR("Tried to make encrypted copy, but no passphrase supplied")
         return False

      # If we're starting unencrypted...encrypt it in place
      (mem,nIter,salt) = self.computeSystemSpecificKdfParams(0.25)
      self.changeKdfParams(mem, nIter, salt)
      self.changeWalletEncryption(securePassphrase=securePassphrase)
   
      # Write the encrypted wallet to the target directory
      self.writeFreshWalletFile(newPath)

      # Unencrypt the wallet now
      self.unlock(securePassphrase=securePassphrase)
      self.changeWalletEncryption(None)
      return True


   #############################################################################
   def getRootPKCC(self, pkIsCompressed=False):
      '''Get the root public key and chain code for this wallet. The key may be
         compressed or uncompressed.'''
      root = self.addrMap['ROOT']
      wltRootPubKey = root.binPublicKey65.copy().toBinStr()
      wltChainCode = root.chaincode.copy().toBinStr()

      # Neither should happen, but just in case....
      if len(wltRootPubKey) != 65:
         LOGERROR('There\'s something wrong with your watch-only wallet! The ')
         LOGERROR('root public key can\'t be retrieved.')
         return
      if len(wltChainCode) != 32:
         LOGERROR('There\'s something wrong with your watch-only wallet! The ')
         LOGERROR('root chain code can\'t be retrieved.')
         return

      # Finish assembling data for the final output.
      if pkIsCompressed == True:
         wltRootCompPubKey = \
            CryptoECDSA().CompressPoint(SecureBinaryData(wltRootPubKey))
         wltRootPubKey = wltRootCompPubKey.toBinStr()

      return (wltRootPubKey, wltChainCode)


   #############################################################################
   def getRootPKCCBackupData(self, pkIsCompressed=True, et16=True):
      '''
      Get the root public key and chain code for this wallet. The root pub
      key/chain code output format will be as follows. All data will be output
      in EasyType16 format.

      ---PART 1: Root Data ID (9 bytes)---
      - Compressed pub key's "sign byte" flag (mask 0x80) + root data format
        version (mask 0x7F)  (1 byte)
      - Wallet ID  (6 bytes)
      - Checksum of the initial byte + the wallet ID  (2 bytes)

      ---PART 2: Root Data (64 bytes)---
      - Compressed public key minus the first ("sign") byte  (32 bytes)
      - Chain code  (32 bytes)
      '''
      # Get the root pub key & chain code. The key will be compressed.
      self.wltRootPubKey, self.wltChainCode = self.getRootPKCC(True)

      # The "version byte" will actually contain the root data format version
      # (mask 0x7F) and a bit (mask 0x80) indicating if the first byte of the
      # compressed public key is 0x02 (0) or 0x03 (1). Done so that the ET16
      # output of the PK & CC will cover 4 lines, with a 5th chunk of data
      # containing everything else.
      rootPKCCFormatVer = PYROOTPKCCVER
      if self.wltRootPubKey[0] == '\x03':
         rootPKCCFormatVer ^= 0x80

      # Produce the root ID object. Convert to ET16 if necessary.
      wltRootIDConcat = int_to_binary(rootPKCCFormatVer) + self.uniqueIDBin
      rootIDConcatChksum = computeChecksum(wltRootIDConcat, nBytes=2)
      wltRootIDConcat += rootIDConcatChksum
      if et16 == True:
         lineNoSpaces = binary_to_easyType16(wltRootIDConcat)
         pcs = [lineNoSpaces[i*4:(i+1)*4] for i in range((len(lineNoSpaces)-1)/4+1)]
         wltRootIDConcat = ' '.join(pcs)

      # Get 4 rows of PK & CC data. Convert to ET16 data if necessary.
      pkccLines = []
      wltPKCCConcat = self.wltRootPubKey[1:] + self.wltChainCode
      for i in range(0, len(wltPKCCConcat), 16):
         concatData = wltPKCCConcat[i:i+16]
         if et16 == True:
            concatData = makeSixteenBytesEasy(concatData)
         pkccLines.append(concatData)

      # Return the root ID & the PK/CC data.
      return (wltRootIDConcat, pkccLines)


   #############################################################################
   def writePKCCFile(self, newPath):
      '''Make a copy of this wallet with only the public key and chain code.'''
      # Open the PKCC file for writing.
      newFile = open(newPath, 'wb')

      # Write the data to the file. The file format is as follows:
      # PKCC data format version  (UINT8)
      # Root ID  (VAR_STR)
      # Number of PKCC lines  (UINT8)
      # PKCC lines  (VAR_STR)
      outRootIDET16, outPKCCET16Lines = self.getRootPKCCBackupData(True)
      newFile.write(str(PYROOTPKCCVER) + '\n')
      newFile.write(outRootIDET16 + '\n')
      for a in outPKCCET16Lines:
         newFile.write(a + '\n')

      # Clean everything up.
      newFile.close()


   #############################################################################
   def forkOnlineWallet(self, newWalletFile, shortLabel='', longLabel=''):
      """
      Make a copy of this wallet that contains no private key data
      """
      # TODO: Fix logic, says aborting but continues with method.
      # Decide on and implement correct functionality.
      if not self.addrMap['ROOT'].hasPrivKey():
         LOGWARN('This wallet is already void of any private key data!')
         LOGWARN('Aborting wallet fork operation.')

      onlineWallet = PyBtcWallet()
      onlineWallet.fileTypeStr = self.fileTypeStr
      onlineWallet.version = self.version
      onlineWallet.magicBytes = self.magicBytes
      onlineWallet.wltCreateDate = self.wltCreateDate
      onlineWallet.useEncryption = False
      onlineWallet.watchingOnly = True

      if not shortLabel:
         shortLabel = self.labelName
      if not longLabel:
         longLabel = self.labelDescr

      onlineWallet.labelName  = (shortLabel + ' (Watch)')[:32]
      onlineWallet.labelDescr = (longLabel + ' (Watching-only copy)')[:256]

      newAddrMap = {}
      for addr160,addrObj in self.addrMap.iteritems():
         onlineWallet.addrMap[addr160] = addrObj.copy()
         onlineWallet.addrMap[addr160].binPrivKey32_Encr  = SecureBinaryData()
         onlineWallet.addrMap[addr160].binPrivKey32_Plain = SecureBinaryData()
         onlineWallet.addrMap[addr160].binInitVector16    = SecureBinaryData()
         onlineWallet.addrMap[addr160].useEncryption = False
         onlineWallet.addrMap[addr160].createPrivKeyNextUnlock = False

      onlineWallet.commentsMap = self.commentsMap
      onlineWallet.opevalMap = self.opevalMap

      onlineWallet.uniqueIDBin = self.uniqueIDBin
      onlineWallet.highestUsedChainIndex     = self.highestUsedChainIndex
      onlineWallet.lastComputedChainAddr160  = self.lastComputedChainAddr160
      onlineWallet.lastComputedChainIndex    = self.lastComputedChainIndex

      onlineWallet.writeFreshWalletFile(newWalletFile, shortLabel, longLabel)
      return onlineWallet


   #############################################################################
   def supplyRootKeyForWatchingOnlyWallet(self, securePlainRootKey32, \
                                                permanent=False):
      """
      If you have a watching only wallet, you might want to upgrade it to a
      full wallet by supplying the 32-byte root private key.  Generally, this
      will be used to make a 'permanent' upgrade to your wallet, and the new
      keys will be written to file ( NOTE:  you should setup encryption just
      after doing this, to make sure that the plaintext keys get wiped from
      your wallet file).

      On the other hand, if you don't want this to be a permanent upgrade,
      this could potentially be used to maintain a watching only wallet on your
      harddrive, and actually plug in your plaintext root key instead of an
      encryption password whenever you want sign transactions. 
      """
      pass


   #############################################################################
   def touchAddress(self, addr20):
      """
      Use this to update your wallet file to recognize the first/last times
      seen for the address.  This information will improve blockchain search
      speed, if it knows not to search transactions that happened before they
      were created.
      """
      pass

   #############################################################################
   def testKdfComputeTime(self):
      """
      Experimentally determines the compute time required by this computer
      to execute with the current key-derivation parameters.  This may be
      useful for when you transfer a wallet to a new computer that has
      different speed/memory characteristic.
      """
      testPassphrase = SecureBinaryData('This is a simple passphrase')
      start = RightNow()
      self.kdf.DeriveKey(testPassphrase)
      self.testedComputeTime = (RightNow()-start)
      return self.testedComputeTime

   #############################################################################
   def serializeKdfParams(self, kdfObj=None, binWidth=256):
      """
      Pack key-derivation function parameters into a binary stream.
      As of wallet version 1.0, there is only one KDF technique used
      in these wallets, and thus we only need to store the parameters
      of this KDF.  In the future, we may have multiple KDFs and have
      to store the selection in this serialization.
      """
      if not kdfObj:
         kdfObj = self.kdf

      if not kdfObj:
         return '\x00'*binWidth

      binPacker = BinaryPacker()
      binPacker.put(UINT64, kdfObj.getMemoryReqtBytes())
      binPacker.put(UINT32, kdfObj.getNumIterations())
      binPacker.put(BINARY_CHUNK, kdfObj.getSalt().toBinStr(), width=32)

      kdfStr = binPacker.getBinaryString()
      binPacker.put(BINARY_CHUNK, computeChecksum(kdfStr,4), width=4)
      padSize = binWidth - binPacker.getSize()
      binPacker.put(BINARY_CHUNK, '\x00'*padSize)

      return binPacker.getBinaryString()



   #############################################################################
   def unserializeKdfParams(self, toUnpack, binWidth=256):

      if isinstance(toUnpack, BinaryUnpacker):
         binUnpacker = toUnpack
      else:
         binUnpacker = BinaryUnpacker(toUnpack)



      allKdfData = binUnpacker.get(BINARY_CHUNK, 44)
      kdfChksum  = binUnpacker.get(BINARY_CHUNK,  4)
      kdfBytes   = len(allKdfData) + len(kdfChksum)
      padding    = binUnpacker.get(BINARY_CHUNK, binWidth-kdfBytes)

      if allKdfData=='\x00'*44:
         return None

      fixedKdfData = verifyChecksum(allKdfData, kdfChksum)
      if len(fixedKdfData)==0:
         raise UnserializeError('Corrupted KDF params, could not fix')
      elif not fixedKdfData==allKdfData:
         self.walletFileSafeUpdate( \
               [[WLT_UPDATE_MODIFY, self.offsetKdfParams, fixedKdfData]])
         allKdfData = fixedKdfData
         LOGWARN('KDF params in wallet were corrupted, but fixed')

      kdfUnpacker = BinaryUnpacker(allKdfData)
      mem   = kdfUnpacker.get(UINT64)
      nIter = kdfUnpacker.get(UINT32)
      salt  = kdfUnpacker.get(BINARY_CHUNK, 32)

      kdf = KdfRomix(mem, nIter, SecureBinaryData(salt))
      return kdf


   #############################################################################
   def serializeCryptoParams(self, binWidth=256):
      """
      As of wallet version 1.0, all wallets use the exact same encryption types,
      so there is nothing to serialize or unserialize.  The 256 bytes here may
      be used in the future, though.
      """
      return '\x00'*binWidth

   #############################################################################
   def unserializeCryptoParams(self, toUnpack, binWidth=256):
      """
      As of wallet version 1.0, all wallets use the exact same encryption types,
      so there is nothing to serialize or unserialize.  The 256 bytes here may
      be used in the future, though.
      """
      if isinstance(toUnpack, BinaryUnpacker):
         binUnpacker = toUnpack
      else:
         binUnpacker = BinaryUnpacker(toUnpack)

      binUnpacker.get(BINARY_CHUNK, binWidth)
      return CryptoAES()

   #############################################################################
   def verifyPassphrase(self, securePassphrase):
      """
      Verify a user-submitted passphrase.  This passphrase goes into
      the key-derivation function to get actual encryption key, which
      is what actually needs to be verified

      Since all addresses should have the same encryption, we only need
      to verify correctness on the root key
      """
      kdfOutput = self.kdf.DeriveKey(securePassphrase)
      try:
         isValid = self.addrMap['ROOT'].verifyEncryptionKey(kdfOutput)
         return isValid
      finally:
         kdfOutput.destroy()


   #############################################################################
   def verifyEncryptionKey(self, secureKdfOutput):
      """
      Verify the underlying encryption key (from KDF).
      Since all addresses should have the same encryption,
      we only need to verify correctness on the root key.
      """
      return self.addrMap['ROOT'].verifyEncryptionKey(secureKdfOutput)


   #############################################################################
   def computeSystemSpecificKdfParams(self, targetSec=0.25, maxMem=32*1024*1024):
      """
      WARNING!!! DO NOT CHANGE KDF PARAMS AFTER ALREADY ENCRYPTED THE WALLET
                 By changing them on an already-encrypted wallet, we are going
                 to lose the original AES256-encryption keys -- which are
                 uniquely determined by (numIter, memReqt, salt, passphrase)

                 Only use this method before you have encrypted your wallet,
                 in order to determine good KDF parameters based on your
                 computer's specific speed/memory capabilities.
      """
      kdf = KdfRomix()
      kdf.computeKdfParams(targetSec, long(maxMem))

      mem   = kdf.getMemoryReqtBytes()
      nIter = kdf.getNumIterations()
      salt  = SecureBinaryData(kdf.getSalt().toBinStr())
      return (mem, nIter, salt)

   #############################################################################
   def restoreKdfParams(self, mem, numIter, secureSalt):
      """
      This method should only be used when we are loading an encrypted wallet
      from file.  DO NOT USE THIS TO CHANGE KDF PARAMETERS.  Doing so may
      result in data loss!
      """
      self.kdf = KdfRomix(mem, numIter, secureSalt)


   #############################################################################
   def changeKdfParams(self, mem, numIter, salt, securePassphrase=None):
      """
      Changing KDF changes the wallet encryption key which means that a KDF
      change is essentially the same as an encryption key change.  As such,
      the wallet must be unlocked if you intend to change an already-
      encrypted wallet with KDF.

      TODO: this comment doesn't belong here...where does it go? :
      If the KDF is NOT yet setup, this method will do it.  Supply the target
      compute time, and maximum memory requirements, and the underlying C++
      code will experimentally determine the "hardest" key-derivation params
      that will run within the specified time and memory usage on the system
      executing this method.  You should set the max memory usage very low
      (a few kB) for devices like smartphones, which have limited memory
      availability.  The KDF will then use less memory but more iterations
      to achieve the same compute time.
      """
      if self.useEncryption:
         if not securePassphrase:
            LOGERROR('')
            LOGERROR('You have requested changing the key-derivation')
            LOGERROR('parameters on an already-encrypted wallet, which')
            LOGERROR('requires modifying the encryption on this wallet.')
            LOGERROR('Please unlock your wallet before attempting to')
            LOGERROR('change the KDF parameters.')
            raise WalletLockError('Cannot change KDF without unlocking wallet')
         elif not self.verifyPassphrase(securePassphrase):
            LOGERROR('Incorrect passphrase to unlock wallet')
            raise PassphraseError('Incorrect passphrase to unlock wallet')

      secureSalt = SecureBinaryData(salt)
      newkdf = KdfRomix(mem, numIter, secureSalt)
      bp = BinaryPacker()
      bp.put(BINARY_CHUNK, self.serializeKdfParams(newkdf), width=256)
      updList = [[WLT_UPDATE_MODIFY, self.offsetKdfParams, bp.getBinaryString()]]

      if not self.useEncryption:
         # We may be setting the kdf params before enabling encryption
         self.walletFileSafeUpdate(updList)
      else:
         # Must change the encryption key: and we won't get here unless
         # we have a passphrase to use.  This call will take the
         self.changeWalletEncryption(securePassphrase=securePassphrase, \
                                     extraFileUpdates=updList, kdfObj=newkdf)

      self.kdf = newkdf

   #############################################################################
   def changeWalletEncryption(self, secureKdfOutput=None, \
                                    securePassphrase=None, \
                                    extraFileUpdates=[],
                                    kdfObj=None, Progress=emptyFunc):
      """
      Supply the passphrase you would like to use to encrypt this wallet
      (or supply the KDF output directly, to skip the passphrase part).
      This method will attempt to re-encrypt with the new passphrase.
      This fails if the wallet is already locked with a different passphrase.
      If encryption is already enabled, please unlock the wallet before
      calling this method.

      Make sure you set up the key-derivation function (KDF) before changing
      from an unencrypted to an encrypted wallet.  An error will be thrown
      if you don't.  You can use something like the following

         # For a target of 0.05-0.1s compute time:
         (mem,nIter,salt) = wlt.computeSystemSpecificKdfParams(0.1)
         wlt.changeKdfParams(mem, nIter, salt)

      Use the extraFileUpdates to pass in other changes that need to be
      written to the wallet file in the same atomic operation as the
      encryption key modifications.
      """

      if not kdfObj:
         kdfObj = self.kdf

      oldUsedEncryption = self.useEncryption
      if securePassphrase or secureKdfOutput:
         newUsesEncryption = True
      else:
         newUsesEncryption = False

      oldKdfKey = None
      if oldUsedEncryption:
         if self.isLocked:      
            raise WalletLockError('Must unlock wallet to change passphrase')
         else:
            oldKdfKey = self.kdfKey.copy()


      if newUsesEncryption and not self.kdf:
         raise EncryptionError('KDF must be setup before encrypting wallet')

      # Prep the file-update list with extras passed in as argument
      walletUpdateInfo = list(extraFileUpdates)

      # Derive the new KDF key if a passphrase was supplied
      newKdfKey = secureKdfOutput
      if securePassphrase:
         newKdfKey = self.kdf.DeriveKey(securePassphrase)

      if oldUsedEncryption and newUsesEncryption and self.verifyEncryptionKey(newKdfKey):
         LOGWARN('Attempting to change encryption to same passphrase!')
         return # Wallet is encrypted with the new passphrase already


      # With unlocked key data, put the rest in a try/except/finally block
      # To make sure we destroy the temporary kdf outputs
      try:
         # If keys were previously unencrypted, they will be not have
         # initialization vectors and need to be generated before encrypting.
         # This is why we have the enableKeyEncryption() call

         if not oldUsedEncryption==newUsesEncryption:
            # If there was an encryption change, we must change the flags
            # in the wallet file in the same atomic operation as changing
            # the stored keys.  We can't let them get out of sync.
            self.useEncryption = newUsesEncryption
            walletUpdateInfo.append(self.createChangeFlagsEntry())
            self.useEncryption = oldUsedEncryption
            # Restore the old flag just in case the file write fails

         newAddrMap  = {}
         i=1
         nAddr = len(self.addrMap)
         
         for addr160,addr in self.addrMap.iteritems():
            Progress(i, nAddr)
            i = i +1
            
            newAddrMap[addr160] = addr.copy()
            newAddrMap[addr160].enableKeyEncryption(generateIVIfNecessary=True)
            newAddrMap[addr160].changeEncryptionKey(oldKdfKey, newKdfKey)
            newAddrMap[addr160].walletByteLoc = addr.walletByteLoc
            walletUpdateInfo.append( \
               [WLT_UPDATE_MODIFY, addr.walletByteLoc, newAddrMap[addr160].serialize()])


         # Try to update the wallet file with the new encrypted key data
         updateSuccess = self.walletFileSafeUpdate( walletUpdateInfo )

         if updateSuccess:
            # Finally give the new data to the user
            for addr160,addr in newAddrMap.iteritems():
               self.addrMap[addr160] = addr.copy()
         
         self.useEncryption = newUsesEncryption
         if newKdfKey:
            self.lock() 
            self.unlock(newKdfKey, Progress=Progress)
    
      finally:
         # Make sure we always destroy the temporary passphrase results
         if newKdfKey: newKdfKey.destroy()
         if oldKdfKey: oldKdfKey.destroy()

   #############################################################################
   def getWalletPath(self, nameSuffix=None):
      fpath = self.walletPath

      if self.walletPath=='':
         fpath = os.path.join(ARMORY_HOME_DIR, buildWltFileName(self.uniqueIDB58))

      if not nameSuffix==None:
         pieces = os.path.splitext(fpath)
         if not pieces[0].endswith('_'):
            fpath = pieces[0] + '_' + nameSuffix + pieces[1]
         else:
            fpath = pieces[0] + nameSuffix + pieces[1]
      return fpath


   #############################################################################
   def getDisplayStr(self, pref="Wallet: "):
      return '%s"%s" (%s)' % (pref, self.labelName, self.uniqueIDB58)

   #############################################################################
   def getCommentForAddress(self, addr160):
      try:
         assetIndex = self.cppWallet.getAssetIndexForAddr(addr160)
         hashList = self.cppWallet.getScriptHashVectorForIndex(assetIndex)
      except:
         return ''

      for _hash in hashList:
         if self.commentsMap.has_key(_hash):
            return self.commentsMap[_hash]
      
      return ''

   #############################################################################
   def getComment(self, hashVal):
      """
      This method is used for both address comments, as well as tx comments
      In the first case, use the 20-byte binary pubkeyhash.  Use 32-byte tx
      hash for the tx-comment case.
      """
      if self.commentsMap.has_key(hashVal):
         return self.commentsMap[hashVal]
      else:
         return ''

   #############################################################################
   def setComment(self, hashVal, newComment):
      """
      This method is used for both address comments, as well as tx comments
      In the first case, use the 20-byte binary pubkeyhash.  Use 32-byte tx
      hash for the tx-comment case.
      """
      updEntry = []
      isNewComment = False
      if self.commentsMap.has_key(hashVal):
         # If there is already a comment for this address, overwrite it
         oldCommentLen = len(self.commentsMap[hashVal])
         oldCommentLoc = self.commentLocs[hashVal]
         # The first 23 bytes are the datatype, hashVal, and 2-byte comment size
         offset = 1 + len(hashVal) + 2
         updEntry.append([WLT_UPDATE_MODIFY, oldCommentLoc+offset, '\x00'*oldCommentLen])
      else:
         isNewComment = True


      dtype = WLT_DATATYPE_ADDRCOMMENT
      if len(hashVal)>20:
         dtype = WLT_DATATYPE_TXCOMMENT
         
      updEntry.append([WLT_UPDATE_ADD, dtype, hashVal, newComment])
      newCommentLoc = self.walletFileSafeUpdate(updEntry)
      self.commentsMap[hashVal] = newComment

      # If there was a wallet overwrite, it's location is the first element
      self.commentLocs[hashVal] = newCommentLoc[-1]



   #############################################################################
   def getAddrCommentIfAvail(self, txHash):
      # If we haven't extracted relevant addresses for this tx, yet -- do it
      if not self.txAddrMap.has_key(txHash):
         self.txAddrMap[txHash] = []
         tx = TheBDM.bdv().getTxByHash(txHash)
         if tx.isInitialized():
            for i in range(tx.getNumTxOut()):
               txout = tx.getTxOutCopy(i)
               stype = getTxOutScriptType(txout.getScript())
               scrAddr = tx.getScrAddrForTxOut(i)

               if stype in CPP_TXOUT_HAS_ADDRSTR:
                  addrStr = scrAddr_to_addrStr(scrAddr)
                  addr160 = addrStr_to_hash160(addrStr)[1]
                  if self.hasAddr(addr160):
                     self.txAddrMap[txHash].append(addr160)
               else: 
                  pass
                  #LOGERROR("Unrecognized scraddr: " + binary_to_hex(scrAddr))
               
      addrComments = []
      for a160 in self.txAddrMap[txHash]:
         h160 = a160[1:]
         if self.commentsMap.has_key(h160) and '[[' not in self.commentsMap[h160]:
            addrComments.append(self.commentsMap[h160])

      return '; '.join(addrComments)

   #############################################################################
   def getAddrCommentFromLe(self, le):
      # If we haven't extracted relevant addresses for this tx, yet -- do it
      txHash = le.getTxHash()
      if not self.txAddrMap.has_key(txHash):
         self.txAddrMap[txHash] = le.getScrAddrList()
                      
      addrComments = []
      for a160 in self.txAddrMap[txHash]:
         hash160 = a160[1:]
         if self.commentsMap.has_key(hash160) and '[[' not in self.commentsMap[hash160]:
            addrComments.append(self.commentsMap[hash160])

      return '; '.join(addrComments)
                     
   #############################################################################
   def getCommentForLE(self, le):
      # Smart comments for LedgerEntry objects:  get any direct comments ... 
      # if none, then grab the one for any associated addresses.
      txHash = le.getTxHash()
      if self.commentsMap.has_key(txHash):
         comment = self.commentsMap[txHash]
      else:
         # [[ COMMENTS ]] are not meant to be displayed on main ledger
         comment = self.getAddrCommentFromLe(le)
         if comment.startswith('[[') and comment.endswith(']]'):
            comment = ''

      return comment




   
   #############################################################################
   def setWalletLabels(self, lshort, llong=''):
      self.labelName = lshort
      self.labelDescr = llong
      toWriteS = lshort.ljust( 32, '\x00')
      toWriteL =  llong.ljust(256, '\x00')

      updList = []
      updList.append([WLT_UPDATE_MODIFY, self.offsetLabelName,  toWriteS])
      updList.append([WLT_UPDATE_MODIFY, self.offsetLabelDescr, toWriteL])
      self.walletFileSafeUpdate(updList)


   #############################################################################
   def packWalletFlags(self, binPacker):
      nFlagBytes = 8
      flags = [False]*nFlagBytes*8
      flags[0] = self.useEncryption
      flags[1] = self.watchingOnly
      flagsBitset = ''.join([('1' if f else '0') for f in flags])
      binPacker.put(UINT64, bitset_to_int(flagsBitset))

   #############################################################################
   def createChangeFlagsEntry(self):
      """
      Packs up the wallet flags and returns a update-entry that can be included
      in a walletFileSafeUpdate call.
      """
      bp = BinaryPacker()
      self.packWalletFlags(bp)
      toWrite = bp.getBinaryString()
      return [WLT_UPDATE_MODIFY, self.offsetWltFlags, toWrite]

   #############################################################################
   def unpackWalletFlags(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         flagData = toUnpack
      else:
         flagData = BinaryUnpacker( toUnpack )

      wltflags = flagData.get(UINT64, 8)
      wltflags = int_to_bitset(wltflags, widthBytes=8)
      self.useEncryption = (wltflags[0]=='1')
      self.watchingOnly  = (wltflags[1]=='1')
      if wltflags[2]=='1':
         raise isMSWallet('Cannot Open MS Wallets')

   #############################################################################
   def packHeader(self, binPacker):
      if not self.addrMap['ROOT']:
         raise WalletAddressError('Cannot serialize uninitialzed wallet!')

      startByte = binPacker.getSize()

      binPacker.put(BINARY_CHUNK, self.fileTypeStr, width=8)
      binPacker.put(UINT32, getVersionInt(self.version))
      binPacker.put(BINARY_CHUNK, self.magicBytes,  width=4)

      # Wallet info flags
      self.offsetWltFlags = binPacker.getSize() - startByte
      self.packWalletFlags(binPacker)

      # Binary Unique ID (firstAddr25bytes[:5][::-1])
      binPacker.put(BINARY_CHUNK, self.uniqueIDBin, width=6)

      # Unix time of wallet creations
      binPacker.put(UINT64, self.wltCreateDate)

      # User-supplied wallet label (short)
      self.offsetLabelName = binPacker.getSize() - startByte
      binPacker.put(BINARY_CHUNK, self.labelName , width=32)

      # User-supplied wallet label (long)
      self.offsetLabelDescr = binPacker.getSize() - startByte
      binPacker.put(BINARY_CHUNK, self.labelDescr,  width=256)

      # Highest used address: 
      self.offsetTopUsed = binPacker.getSize() - startByte
      binPacker.put(INT64, self.highestUsedChainIndex)

      # Key-derivation function parameters
      self.offsetKdfParams = binPacker.getSize() - startByte
      binPacker.put(BINARY_CHUNK, self.serializeKdfParams(), width=256)

      # Wallet encryption parameters (currently nothing to put here)
      self.offsetCrypto = binPacker.getSize() - startByte
      binPacker.put(BINARY_CHUNK, self.serializeCryptoParams(), width=256)

      # Address-chain root, (base-address for deterministic wallets)
      self.offsetRootAddr = binPacker.getSize() - startByte
      self.addrMap['ROOT'].walletByteLoc = self.offsetRootAddr
      binPacker.put(BINARY_CHUNK, self.addrMap['ROOT'].serialize())

      # In wallet version 1.0, this next kB is unused -- may be used in future
      binPacker.put(BINARY_CHUNK, '\x00'*1024)
      return binPacker.getSize() - startByte




   #############################################################################
   def unpackHeader(self, binUnpacker):
      """
      Unpacking the header information from a wallet file.  See the help text
      on the base class, PyBtcWallet, for more information on the wallet
      serialization.
      """
      self.fileTypeStr = binUnpacker.get(BINARY_CHUNK, 8)
      self.version     = readVersionInt(binUnpacker.get(UINT32))
      self.magicBytes  = binUnpacker.get(BINARY_CHUNK, 4)

      # Decode the bits to get the flags
      self.offsetWltFlags = binUnpacker.getPosition()
      self.unpackWalletFlags(binUnpacker)

      # This is the first 4 bytes of the 25-byte address-chain-root address
      # This includes the network byte (i.e. main network, testnet, namecoin)
      self.uniqueIDBin = binUnpacker.get(BINARY_CHUNK, 6)
      self.uniqueIDB58 = binary_to_base58(self.uniqueIDBin)
      self.wltCreateDate  = binUnpacker.get(UINT64)

      # We now have both the magic bytes and network byte
      if not self.magicBytes == MAGIC_BYTES:
         LOGERROR('Requested wallet is for a different blockchain!')
         LOGERROR('Wallet is for:  %s ', BLOCKCHAINS[self.magicBytes])
         LOGERROR('ArmoryEngine:   %s ', BLOCKCHAINS[MAGIC_BYTES])
         return -1
      if not self.uniqueIDBin[-1] == ADDRBYTE:
         LOGERROR('Requested wallet is for a different network!')
         LOGERROR('ArmoryEngine:   %s ', NETWORKS[ADDRBYTE])
         return -2

      # User-supplied description/name for wallet
      self.offsetLabelName = binUnpacker.getPosition()
      self.labelName  = binUnpacker.get(BINARY_CHUNK, 32).strip('\x00')


      # Longer user-supplied description/name for wallet
      self.offsetLabelDescr  = binUnpacker.getPosition()
      self.labelDescr  = binUnpacker.get(BINARY_CHUNK, 256).strip('\x00')


      self.offsetTopUsed = binUnpacker.getPosition()
      self.highestUsedChainIndex = binUnpacker.get(INT64)


      # Read the key-derivation function parameters
      self.offsetKdfParams = binUnpacker.getPosition()
      self.kdf = self.unserializeKdfParams(binUnpacker)

      # Read the crypto parameters
      self.offsetCrypto    = binUnpacker.getPosition()
      self.crypto = self.unserializeCryptoParams(binUnpacker)

      # Read address-chain root address data
      self.offsetRootAddr  = binUnpacker.getPosition()
      

      rawAddrData = binUnpacker.get(BINARY_CHUNK, self.pybtcaddrSize)
      self.addrMap['ROOT'] = PyBtcAddress().unserialize(rawAddrData)
      fixedAddrData = self.addrMap['ROOT'].serialize()
      if not rawAddrData==fixedAddrData:
         self.walletFileSafeUpdate([ \
            [WLT_UPDATE_MODIFY, self.offsetRootAddr, fixedAddrData]])

      self.addrMap['ROOT'].walletByteLoc = self.offsetRootAddr
      if self.useEncryption:
         self.addrMap['ROOT'].isLocked = True
         self.isLocked = True

      # In wallet version 1.0, this next kB is unused -- may be used in future
      binUnpacker.advance(1024)

      # TODO: automatic conversion if the code uses a newer wallet
      #       version than the wallet... got a manual script, but it
      #       would be nice to autodetect and correct
      #convertVersion

      return 0 #success

   #############################################################################
   def unpackNextEntry(self, binUnpacker):
      dtype   = binUnpacker.get(UINT8)
      hashVal = ''
      binData = ''
      if dtype==WLT_DATATYPE_KEYDATA:
         hashVal = binUnpacker.get(BINARY_CHUNK, 20)
         binData = binUnpacker.get(BINARY_CHUNK, self.pybtcaddrSize)
      elif dtype==WLT_DATATYPE_ADDRCOMMENT:
         hashVal = binUnpacker.get(BINARY_CHUNK, 20)
         commentLen = binUnpacker.get(UINT16)
         binData = binUnpacker.get(BINARY_CHUNK, commentLen)
      elif dtype==WLT_DATATYPE_TXCOMMENT:
         hashVal = binUnpacker.get(BINARY_CHUNK, 32)
         commentLen = binUnpacker.get(UINT16)
         binData = binUnpacker.get(BINARY_CHUNK, commentLen)
      elif dtype==WLT_DATATYPE_OPEVAL:
         raise NotImplementedError('OP_EVAL not support in wallet yet')
      elif dtype==WLT_DATATYPE_DELETED:
         deletedLen = binUnpacker.get(UINT16)
         binUnpacker.advance(deletedLen)
         

      return (dtype, hashVal, binData)

   #############################################################################
   @TimeThisFunction
   def readWalletFile(self, wltpath, verifyIntegrity=True, reportProgress=None):
      if not os.path.exists(wltpath):
         raise FileExistsError("No wallet file:"+wltpath)

      self.__init__()
      self.walletPath = wltpath

      if verifyIntegrity:
         try:
            nError = self.doWalletFileConsistencyCheck()
         except KeyDataError, errmsg:
            LOGEXCEPT('***ERROR:  Wallet file had unfixable errors.')
            raise KeyDataError(errmsg)


      wltfile = open(wltpath, 'rb')
      wltdata = BinaryUnpacker(wltfile.read())
      wltfile.close()

      self.unpackHeader(wltdata)      

      self.lastComputedChainIndex = -UINT32_MAX
      self.lastComputedChainAddr160  = None
      i=0
      while wltdata.getRemainingSize()>0:
         byteLocation = wltdata.getPosition()
         i += 1
         if i%10 == 0 and reportProgress is not None:
            progress = float(byteLocation) / float(wltdata.getSize())
            reportProgress(progress)
            
         dtype, hashVal, rawData = self.unpackNextEntry(wltdata)
         if dtype==WLT_DATATYPE_KEYDATA:
            newAddr = PyBtcAddress()
            newAddr.unserialize(rawData)
            newAddr.walletByteLoc = byteLocation + 21
            # Fix byte errors in the address data
            fixedAddrData = newAddr.serialize()

            if not rawData==fixedAddrData:
               self.walletFileSafeUpdate([ \
                  [WLT_UPDATE_MODIFY, newAddr.walletByteLoc, fixedAddrData]])
            if newAddr.useEncryption:
               newAddr.isLocked = True
            self.addrMap[hashVal] = newAddr
            if newAddr.chainIndex > self.lastComputedChainIndex:
               self.lastComputedChainIndex   = newAddr.chainIndex
               self.lastComputedChainAddr160 = newAddr.getAddr160()
               
            if newAddr.chainIndex < -2:
               newAddr.chainIndex = -2
               self.hasNegativeImports = True
                                 
            self.linearAddr160List.append(newAddr.getAddr160())
            self.chainIndexMap[newAddr.chainIndex] = newAddr.getAddr160()
            
            if newAddr.chainIndex <= -2:
               self.importList.append(len(self.linearAddr160List) - 1)
                  
         if dtype in (WLT_DATATYPE_ADDRCOMMENT, WLT_DATATYPE_TXCOMMENT):
            self.commentsMap[hashVal] = rawData # actually ASCII data, here
            self.commentLocs[hashVal] = byteLocation
         if dtype==WLT_DATATYPE_OPEVAL:
            raise NotImplementedError('OP_EVAL not support in wallet yet')
         if dtype==WLT_DATATYPE_DELETED:
            pass

      ### Update the wallet version if necessary ###
      if getVersionInt(self.version) < getVersionInt(PYBTCWALLET_VERSION):
         LOGERROR('Wallets older than version 1.35 no longer supported!')
         return

      return self



   #############################################################################
   @singleEntrantMethod
   def walletFileSafeUpdate(self, updateList):
            
      """
      The input "toAddDataList" should be a list of triplets, such as:
      [
        [WLT_DATA_ADD,    WLT_DATATYPE_KEYDATA, addr160_1,  PyBtcAddrObj1]
        [WLT_DATA_ADD,    WLT_DATATYPE_KEYDATA, addr160_2,  PyBtcAddrObj2]
        [WLT_DATA_MODIFY, modifyStartByte1,  binDataForOverwrite1  ]
        [WLT_DATA_ADD,    WLT_DATATYPE_ADDRCOMMENT, addr160_3,  'Long-term savings']
        [WLT_DATA_MODIFY, modifyStartByte2,  binDataForOverwrite2 ]
      ]

      The return value is the list of new file byte offsets (from beginning of
      the file), that specify the start of each modification made to the
      wallet file.  For MODIFY fields, this just returns the modifyStartByte
      field that was provided as input.  For adding data, it specifies the
      starting byte of the new field (the DATATYPE byte).  We keep this data
      in PyBtcAddress objects so that we know where to apply modifications in
      case we need to change something, like converting from unencrypted to
      encrypted private keys.

      If this method fails, we simply return an empty list.  We can check for
      an empty list to know if the file update succeeded.

      WHY IS THIS SO COMPLICATED?  -- Because it's atomic!

      When we want to add data to the wallet file, we will do so in a completely
      recoverable way.  We define this method to make sure a backup exists when
      we start modifying the file, and keep a flag to identify when the wallet
      might be corrupt.  If we ever try to load the wallet file and see another
      file with the _update_unsuccessful suffix, we should instead just restore
      from backup.

      Similarly, we have to update the backup file after updating the main file
      so we will use a similar technique with the backup_unsuccessful suffix.
      We don't want to rely on a backup if somehow *the backup* got corrupted
      and the original file is fine.  THEREFORE -- this is implemented in such
      a way that the user should know two things:

         (1) No matter when the power goes out, we ALWAYS have a uncorrupted
             wallet file, and know which one it is.  Either the backup is safe,
             or the original is safe.  Based on the flag files, we know which
             one is guaranteed to be not corrupted.
         (2) ALWAYS DO YOUR FILE OPERATIONS BEFORE SETTING DATA IN MEMORY
             You must write it to disk FIRST using this SafeUpdate method,
             THEN give the new data to the user -- never give it to them
             until you are sure that it was written safely to disk.

      Number (2) is easy to screw up because you plan to write the file just
      AFTER the data is created and stored in local memory.  But an error
      might be thrown halfway which is handled higher up, and instead the data
      never made it to file.  Then there is a risk that the user uses their
      new address that never made it into the wallet file.
      """

      if not os.path.exists(self.walletPath):
         raise FileExistsError('No wallet file exists to be updated!')

      if len(updateList)==0:
         return []

      # Make sure that the primary and backup files are synced before update
      self.doWalletFileConsistencyCheck()

      walletFileBackup = self.getWalletPath('backup')
      mainUpdateFlag   = self.getWalletPath('update_unsuccessful')
      backupUpdateFlag = self.getWalletPath('backup_unsuccessful')


      # Will be passing back info about all data successfully added
      oldWalletSize = os.path.getsize(self.walletPath)
      updateLocations = []
      dataToChange    = []
      toAppend = BinaryPacker()

      try:
         for entry in updateList:
            modType    = entry[0]
            updateInfo = entry[1:]

            if(modType==WLT_UPDATE_ADD):
               dtype = updateInfo[0]
               updateLocations.append(toAppend.getSize()+oldWalletSize)
               if dtype==WLT_DATATYPE_KEYDATA:
                  if len(updateInfo[1])!=20 or not isinstance(updateInfo[2], PyBtcAddress):
                     raise Exception('Data type does not match update type')
                  toAppend.put(UINT8, WLT_DATATYPE_KEYDATA)
                  toAppend.put(BINARY_CHUNK, updateInfo[1])
                  toAppend.put(BINARY_CHUNK, updateInfo[2].serialize())

               elif dtype in (WLT_DATATYPE_ADDRCOMMENT, WLT_DATATYPE_TXCOMMENT):
                  if not isinstance(updateInfo[2], str):
                     raise Exception('Data type does not match update type')
                  toAppend.put(UINT8, dtype)
                  toAppend.put(BINARY_CHUNK, updateInfo[1])
                  toAppend.put(UINT16, len(updateInfo[2]))
                  toAppend.put(BINARY_CHUNK, updateInfo[2])

               elif dtype==WLT_DATATYPE_OPEVAL:
                  raise Exception('OP_EVAL not support in wallet yet')

            elif(modType==WLT_UPDATE_MODIFY):
               updateLocations.append(updateInfo[0])
               dataToChange.append( updateInfo )
            else:
               LOGERROR('Unknown wallet-update type!')
               raise Exception('Unknown wallet-update type!')
      except Exception:
         LOGEXCEPT('Bad input to walletFileSafeUpdate')
         return []

      binaryToAppend = toAppend.getBinaryString()

      # We need to safely modify both the main wallet file and backup
      # Start with main wallet
      touchFile(mainUpdateFlag)

      try:
         wltfile = open(self.walletPath, 'ab')
         wltfile.write(binaryToAppend)
         wltfile.flush()
         os.fsync(wltfile.fileno())
         wltfile.close()

         # This is for unit-testing the atomic-wallet-file-update robustness
         if self.interruptTest1: raise InterruptTestError

         wltfile = open(self.walletPath, 'r+b')
         for loc,replStr in dataToChange:
            wltfile.seek(loc)
            wltfile.write(replStr)
         wltfile.flush()
         os.fsync(wltfile.fileno())
         wltfile.close()

      except IOError:
         LOGEXCEPT('Could not write data to wallet.  Permissions?')
         shutil.copy(walletFileBackup, self.walletPath)
         os.remove(mainUpdateFlag)
         return []

      # Write backup flag before removing main-update flag.  If we see
      # both flags, we know file IO was interrupted RIGHT HERE
      touchFile(backupUpdateFlag)

      # This is for unit-testing the atomic-wallet-file-update robustness
      if self.interruptTest2: raise InterruptTestError

      os.remove(mainUpdateFlag)

      # Modify backup
      try:
         # This is for unit-testing the atomic-wallet-file-update robustness
         if self.interruptTest3: raise InterruptTestError

         backupfile = open(walletFileBackup, 'ab')
         backupfile.write(binaryToAppend)
         backupfile.flush()
         os.fsync(backupfile.fileno())
         backupfile.close()

         backupfile = open(walletFileBackup, 'r+b')
         for loc,replStr in dataToChange:
            backupfile.seek(loc)
            backupfile.write(replStr)
         backupfile.flush()
         os.fsync(backupfile.fileno())
         backupfile.close()

      except IOError:
         LOGEXCEPT('Could not write backup wallet.  Permissions?')
         shutil.copy(self.walletPath, walletFileBackup)
         os.remove(mainUpdateFlag)
         return []

      os.remove(backupUpdateFlag)

      return updateLocations



   #############################################################################
   def doWalletFileConsistencyCheck(self, onlySyncBackup=True):
      """
      First we check the file-update flags (files we touched/removed during
      file modification operations), and then restore the primary wallet file
      and backup file to the exact same state -- we know that at least one of
      them is guaranteed to not be corrupt, and we know based on the flags
      which one that is -- so we execute the appropriate copy operation.

      ***NOTE:  For now, the remaining steps are untested and unused!

      After we have guaranteed that main wallet and backup wallet are the
      same, we want to do a check that the data is consistent.  We do this
      by simply reading in the key-data from the wallet, unserializing it
      and reserializing it to see if it matches -- this works due to the
      way the PyBtcAddress::unserialize() method works:  it verifies the
      checksums in the address data, and corrects errors automatically!
      And it's part of the unit-tests that serialize/unserialize round-trip
      is guaranteed to match for all address types if there's no byte errors.

      If an error is detected, we do a safe-file-modify operation to re-write
      the corrected information to the wallet file, in-place.  We DO NOT
      check comment fields, since they do not have checksums, and are not
      critical to protect against byte errors.
      """



      if not os.path.exists(self.walletPath):
         raise FileExistsError('No wallet file exists to be checked!')

      walletFileBackup = self.getWalletPath('backup')
      mainUpdateFlag   = self.getWalletPath('update_unsuccessful')
      backupUpdateFlag = self.getWalletPath('backup_unsuccessful')

      if not os.path.exists(walletFileBackup):
         # We haven't even created a backup file, yet
         LOGDEBUG('Creating backup file %s', walletFileBackup)
         touchFile(backupUpdateFlag)
         shutil.copy(self.walletPath, walletFileBackup)
         os.remove(backupUpdateFlag)

      if os.path.exists(backupUpdateFlag) and os.path.exists(mainUpdateFlag):
         # Here we actually have a good main file, but backup never succeeded
         LOGWARN('***WARNING: error in backup file... how did that happen?')
         shutil.copy(self.walletPath, walletFileBackup)
         os.remove(mainUpdateFlag)
         os.remove(backupUpdateFlag)
      elif os.path.exists(mainUpdateFlag):
         LOGWARN('***WARNING: last file operation failed!  Restoring wallet from backup')
         # main wallet file might be corrupt, copy from backup
         shutil.copy(walletFileBackup, self.walletPath)
         os.remove(mainUpdateFlag)
      elif os.path.exists(backupUpdateFlag):
         LOGWARN('***WARNING: creation of backup was interrupted -- fixing')
         shutil.copy(self.walletPath, walletFileBackup)
         os.remove(backupUpdateFlag)

      if onlySyncBackup:
         return 0

   #############################################################################
   def deleteImportedAddress(self, addr160):
      """
      We want to overwrite a particular key in the wallet.  Before overwriting
      the data looks like this:
         [  \x00  |  <20-byte addr160>  |  <237-byte keydata> ]
      And we want it to look like:
         [  \x04  |  <2-byte length>  | \x00\x00\x00... ]
      So we need to construct a wallet-update vector to modify the data
      starting at the first byte, replace it with 0x04, specifies how many
      bytes are in the deleted entry, and then actually overwrite those 
      bytes with 0s
      """

      if not self.addrMap[addr160].chainIndex==-2:
         raise WalletAddressError('You can only delete imported addresses!')

      overwriteLoc = self.addrMap[addr160].walletByteLoc - 21
      overwriteLen = 20 + self.pybtcaddrSize - 2

      overwriteBin = ''
      overwriteBin += int_to_binary(WLT_DATATYPE_DELETED, widthBytes=1)
      overwriteBin += int_to_binary(overwriteLen,         widthBytes=2)
      overwriteBin += '\x00'*overwriteLen

      self.walletFileSafeUpdate([[WLT_UPDATE_MODIFY, overwriteLoc, overwriteBin]])

      # IMPORTANT:  we need to update the wallet structures to reflect the
      #             new state of the wallet.  This will actually be easiest
      #             if we just "forget" the current wallet state and re-read
      #             the wallet from file
      wltPath = self.walletPath
      
      passCppWallet = self.cppWallet
      self.cppWallet.removeAddressBulk([Hash160ToScrAddr(addr160)])
      self.readWalletFile(wltPath)
      self.cppWallet = passCppWallet
      self.registerWallet(False)

   #############################################################################
   def importExternalAddressData(self, privKey=None, privChk=None, \
                                       pubKey=None,  pubChk=None, \
                                       addr20=None,  addrChk=None, \
                                       firstTime=UINT32_MAX, \
                                       firstBlk=UINT32_MAX, lastTime=0, \
                                       lastBlk=0):
      """
      This wallet fully supports importing external keys, even though it is
      a deterministic wallet: determinism only adds keys to the pool based
      on the address-chain, but there's nothing wrong with adding new keys
      not on the chain.

      We don't know when this address was created, so we have to set its
      first/last-seen times to 0, to make sure we search the whole blockchain
      for tx related to it.  This data will be updated later after we've done
      the search and know for sure when it is "relevant".
      (alternatively, if you know it's first-seen time for some reason, you
      can supply it as an input, but this seems rare: we don't want to get it
      wrong or we could end up missing wallet-relevant transactions)

      DO NOT CALL FROM A BDM THREAD FUNCTION.  IT MAY DEADLOCK.
      """

      if not privKey and not self.watchingOnly:
         LOGERROR('')
         LOGERROR('This wallet is strictly for addresses that you')
         LOGERROR('own.  You cannot import addresses without the')
         LOGERROR('the associated private key.  Instead, use a')
         LOGERROR('watching-only wallet to import this address.')
         LOGERROR('(actually, this is currently, completely disabled)')
         raise WalletAddressError('Cannot import non-private-key addresses')

      # First do all the necessary type conversions and error corrections
      computedPubKey = None
      computedAddr20 = None
      if privKey:
         if isinstance(privKey, str):
            privKey = SecureBinaryData(privKey)

         if privChk:
            privKey = SecureBinaryData(verifyChecksum(privKey.toBinStr(), privChk))

         computedPubkey = CryptoECDSA().ComputePublicKey(privKey)
         computedAddr20 = convertKeyDataToAddress(pubKey=computedPubkey)

      # If public key is provided, we prep it so we can verify Pub/Priv match
      if pubKey:
         if isinstance(pubKey, str):
            pubKey = SecureBinaryData(pubKey)
         if pubChk:
            pubKey = SecureBinaryData(verifyChecksum(pubKey.toBinStr(), pubChk))

         if not computedAddr20:
            computedAddr20 = convertKeyDataToAddress(pubKey=pubKey)

      # The 20-byte address (pubkey hash160) should always be a python string
      if addr20:
         if not isinstance(pubKey, str):
            addr20 = addr20.toBinStr()
         if addrChk:
            addr20 = verifyChecksum(addr20, addrChk)

      # Now a few sanity checks
      if self.addrMap.has_key(addr20):
         LOGWARN('The private key address is already in your wallet!')
         return None

      addr20 = computedAddr20

      if self.addrMap.has_key(addr20):
         LOGERROR('The computed private key address is already in your wallet!')
         return None

      # If a private key is supplied and this wallet is encrypted&locked, then 
      # we have no way to secure the private key without unlocking the wallet.
      if self.useEncryption and privKey and not self.kdfKey:
         raise WalletLockError('Cannot import private key when wallet is locked!')

      if privKey:
         # For priv key, lots of extra encryption and verification options
         newAddr = PyBtcAddress().createFromPlainKeyData(privKey, addr20, \
                                                         self.useEncryption, \
                                                         self.useEncryption, \
                                                         publicKey65=computedPubkey, \
                                                         skipCheck=True,
                                                         skipPubCompute=True)
         if self.useEncryption:
            newAddr.lock(self.kdfKey)
            newAddr.unlock(self.kdfKey)
      elif pubKey:
         securePubKey = SecureBinaryData(pubKey)
         newAddr = PyBtcAddress().createFromPublicKeyData(securePubKey)
      else:
         newAddr = PyBtcAddress().createFromPublicKeyHash160(addr20)

      newAddr.chaincode  = SecureBinaryData('\xff'*32)
      newAddr.chainIndex = -2
      newAddr.timeRange = [firstTime, lastTime]
      newAddr.blkRange  = [firstBlk,  lastBlk ]
      #newAddr.binInitVect16  = SecureBinaryData().GenerateRandom(16)
      newAddr160 = newAddr.getAddr160()

      newDataLoc = self.walletFileSafeUpdate( \
         [[WLT_UPDATE_ADD, WLT_DATATYPE_KEYDATA, newAddr160, newAddr]])
      self.addrMap[newAddr160] = newAddr.copy()
      self.addrMap[newAddr160].walletByteLoc = newDataLoc[0] + 21
      
      self.linearAddr160List.append(newAddr160)
      self.importList.append(len(self.linearAddr160List) - 1)
      
      if self.useEncryption and self.kdfKey:
         self.addrMap[newAddr160].lock(self.kdfKey)
         if not self.isLocked:
            self.addrMap[newAddr160].unlock(self.kdfKey)
            
      return computedPubkey

   #############################################################################  
   def importExternalAddressBatch(self, privKeyList):

      addr160List = []
      
      for key, a160 in privKeyList:
         self.importExternalAddressData(key)
         addr160List.append(Hash160ToScrAddr(a160))

      return addr160List

   #############################################################################
   @CheckWalletRegistration
   def checkIfRescanRequired(self):
      """ 
      Returns true is we have to go back to disk/mmap and rescan more than two
      weeks worth of blocks

      """

      if TheBDM.getState()==BDM_BLOCKCHAIN_READY:
         return (TheBDM.numBlocksToRescan(self.cppWallet) > 2016)
      else:
         return False



   #############################################################################
   def signUnsignedTx(self, ustx, hashcode=1, signer=SIGNER_DEFAULT):
      if not hashcode==1:
         LOGERROR('hashcode!=1 is not supported at this time!')
         return
      
      # If the wallet is locked, we better bail now
      if self.isLocked is True and self.kdfKey is None:
         raise WalletLockError('Cannot sign tx without unlocking wallet')

      numInputs = len(ustx.pytxObj.inputs)
      wltAddr = []
      for iin,ustxi in enumerate(ustx.ustxInputs):
         for isig,scrAddr in enumerate(ustxi.scrAddrs):
            addr160 = scrAddr_to_hash160(scrAddr)[1]
            addrObj = self.getAddrObjectForHash(addr160)
            if addrObj.hasPrivKey():
               wltAddr.append((addrObj, iin, isig))

      # WltAddr now contains a list of every input we can sign for, and the
      # PyBtcAddress object that can be used to sign it.  Let's do it.
      numMyAddr = len(wltAddr)
      LOGDEBUG('Total number of inputs in transaction:  %d', numInputs)
      LOGDEBUG('Number of inputs that you can sign for: %d', numMyAddr)
      
      #figure out signer if it's set to default
      if signer == SIGNER_DEFAULT:
         if ustx.isLegacyTx:
            signer = SIGNER_LEGACY
         else:
            signer = SIGNER_CPP


      # Unlock the wallet if necessary
      maxChainIndex = -1
      for addrObj,idx,sigIdx in wltAddr:
         maxChainIndex = max(maxChainIndex, addrObj.chainIndex)
         if addrObj.isLocked:
            if self.kdfKey:
               if addrObj.createPrivKeyNextUnlock:
                  self.unlock(self.kdfKey)
               else:
                  addrObj.unlock(self.kdfKey)
            else:
               self.lock()
               raise WalletLockError('Cannot sign tx without unlocking wallet')

         if not addrObj.hasPubKey():
            # Make sure the public key is available for this address
            addrObj.binPublicKey65 = \
               CryptoECDSA().ComputePublicKey(addrObj.binPrivKey32_Plain)

      ustx.signerType = signer
      
      #python signer
      if signer == SIGNER_LEGACY:
         for addrObj,idx,sigIdx in wltAddr:
            ustx.createAndInsertSignatureForInput(idx, addrObj.binPrivKey32_Plain,
                                                  signerType=signer)

      #cpp signer
      elif signer == SIGNER_CPP:
         #create cpp signer
         cppsigner = PythonSignerDirector(self)
         cppsigner.setLockTime(ustx.lockTime)
         
         #set spenders
         for ustxi in ustx.ustxInputs:
            cppsigner.addSpender(ustxi.getUnspentTxOut(), ustxi.sequence)
            
         #set recipients
         for txout in ustx.decorTxOuts:
            cppsigner.addRecipient(txout.binScript, txout.value)
         
         #sign
         cppsigner.signTx()
         ustx.pytxObj.signerState = cppsigner.serializeState()
         ustx.pytxObj.setSignerType(signer)
               
      #bch signer
      elif signer == SIGNER_BCH:
         #create cpp signer
         cppsigner = PythonSignerDirector_BCH(self)
         cppsigner.setLockTime(ustx.lockTime)
         
         #set spenders
         for ustxi in ustx.ustxInputs:
            cppsigner.addSpender(ustxi.getUnspentTxOut(), ustxi.sequence)
            
         #set recipients
         for txout in ustx.decorTxOuts:
            cppsigner.addRecipient(txout.binScript, txout.value)
         
         #sign
         cppsigner.signTx()
         ustx.pytxObj.signerState = cppsigner.serializeState()
         ustx.pytxObj.setSignerType(signer)

      if self.useEncryption:
         self.lock()
      
      prevHighestIndex = self.highestUsedChainIndex  
      if prevHighestIndex < maxChainIndex:
         self.advanceHighestIndex(maxChainIndex-prevHighestIndex)
         self.fillAddressPool()

      return ustx


   #############################################################################
   def unlock(self, secureKdfOutput=None, \
                    securePassphrase=None, \
                    tempKeyLifetime=0, Progress=emptyFunc):
      """
      We must assume that the kdfResultKey is a SecureBinaryData object
      containing the result of the KDF-passphrase.  The wallet unlocked-
      lifetime will be set to X seconds from time.time() [now] and next
      time the checkWalletLockTimeout function is called it will be re-
      locked.
      """
      
      LOGDEBUG('Attempting to unlock wallet: %s', self.uniqueIDB58)
      if not secureKdfOutput and not securePassphrase:
         raise PassphraseError("No passphrase/key provided to unlock wallet!")

      if not secureKdfOutput:
         if not self.kdf:
            raise EncryptionError('How do we have a locked wallet w/o KDF???')
         secureKdfOutput = self.kdf.DeriveKey(securePassphrase)


      if not self.verifyEncryptionKey(secureKdfOutput):
         raise PassphraseError("Incorrect passphrase for wallet")

      # For now, I assume that all keys have the same passphrase and all
      # unlocked successfully at the same time.
      # It's an awful lot of work to design a wallet to consider partially-
      # successful unlockings.
      self.kdfKey = secureKdfOutput
      if tempKeyLifetime==0:
         self.lockWalletAtTime = RightNow() + self.defaultKeyLifetime
      else:
         self.lockWalletAtTime = RightNow() + tempKeyLifetime

      #Fix to n2 unlock issue: newly chained addresses on a locked wallet 
      #cannot have their private key computed until the next unlock.
      #When that unlock takes place, certain address entries lack context
      #so they are derived from the root key itself.
      #This fix runs through all address entries ordered by chainIndex, 
      #to be able to feed the closest computed address entry to the upcoming, 
      #possibly uncomputed entries.

      naddress = 1
      addrCount = len(self.addrMap)
         
      addrObjPrev = None
      import operator
      for addrObj in (sorted(self.addrMap.values(), 
                             key=operator.attrgetter('chainIndex'))):
         Progress(naddress, addrCount)
         naddress = naddress +1
         
         needToSaveAddrAfterUnlock = addrObj.createPrivKeyNextUnlock
         if needToSaveAddrAfterUnlock and addrObjPrev is not None:
               ChainDepth = addrObj.chainIndex - addrObjPrev.chainIndex

               if ChainDepth > 0 and addrObjPrev.chainIndex > -1:
                  addrObj.createPrivKeyNextUnlock_IVandKey[0] = \
                                             addrObjPrev.binInitVect16.copy()
                  addrObj.createPrivKeyNextUnlock_IVandKey[1] = \
                                          addrObjPrev.binPrivKey32_Encr.copy()

                  addrObj.createPrivKeyNextUnlock_ChainDepth  = ChainDepth

         addrObj.unlock(self.kdfKey)
         if addrObj.chainIndex > -1: addrObjPrev = addrObj

         if needToSaveAddrAfterUnlock:
            updateLoc = addrObj.walletByteLoc 
            self.walletFileSafeUpdate( [[WLT_UPDATE_MODIFY, 
                                         addrObj.walletByteLoc,
                                         addrObj.serialize()]])

      self.isLocked = False
      LOGDEBUG('Unlock succeeded: %s', self.uniqueIDB58)

   ############################################################################
   def lock(self, Progress=emptyFunc):
      """
      We assume that we have already set all encryption parameters (such as
      IVs for each key) and thus all we need to do is call the "lock" method
      on each PyBtcAddress object.

      If wallet is unlocked, try to re-lock addresses, regardless of whether
      we have a kdfKey or not.  In some circumstances (such as when the addrs
      have never been locked before) we will need the key to encrypt them.
      However, in most cases, the encrypted versions are already available
      and the PyBtcAddress objects can destroy the plaintext keys without
      ever needing access to the encryption keys.

      ANY METHOD THAT CALLS THIS MUST CATCH WALLETLOCKERRORS UNLESS YOU ARE
      POSITIVE THAT THE KEYS HAVE ALREADY BEEN ENCRYPTED BEFORE, OR ARE
      ALREADY SITTING IN THE ENCRYPTED WALLET FILE.  PyBtcAddress objects
      were designed to do this, but in case of a bug, you don't want the
      program crashing with money-bearing private keys sitting in memory only.

      TODO: If things like IVs are not set properly, we should implement
            a way to check for this, correct it, and update the wallet
            file if necessary
      """

      # Wallet is unlocked, will try to re-lock addresses, regardless of whether
      # we have a kdfKey or not.  If a key is required, we will throw a
      # WalletLockError, and the caller can get the passphrase from the user,
      # unlock the wallet, then try locking again.
      # NOTE: If we don't have kdfKey, it is set to None, which is the default
      #       input for PyBtcAddress::lock for "I don't have it".  In most 
      #       cases, it is actually possible to lock the wallet without the 
      #       kdfKey because we saved the encrypted versions before unlocking
      if self.useEncryption:
         LOGDEBUG('Attempting to lock wallet: %s', self.uniqueIDB58)
         i=1
         nAddr = len(self.addrMap)
         try:
            for addr160,addrObj in self.addrMap.iteritems():
               Progress(i, nAddr)
               i = i +1
               
               self.addrMap[addr160].lock(self.kdfKey)
   
            if self.kdfKey:
               self.kdfKey.destroy()
               self.kdfKey = None
            self.isLocked = True
         except WalletLockError:
            LOGERROR('Locking wallet requires encryption key.  This error')
            LOGERROR('Usually occurs on newly-encrypted wallets that have')
            LOGERROR('never been encrypted before.')
            raise WalletLockError('Unlock with passphrase before locking again')
         LOGDEBUG('Wallet locked: %s', self.uniqueIDB58)
      else:
         LOGWARN('Attempted to lock unencrypted wallet: %s', self.uniqueIDB58)
         

   #############################################################################
   def getAddrListSortedByChainIndex(self, withRoot=False):
      """ Returns Addr160 list """
      addrList = []
      for addr160 in self.linearAddr160List:
         addr=self.addrMap[addr160]
         addrList.append( [addr.chainIndex, addr160, addr] )

      addrList.sort(key=lambda x: x[0])
      return addrList

   #############################################################################
   def getAddrList(self):
      """ Returns list of PyBtcAddress objects """
      addrList = []
      for addr160,addrObj in self.addrMap.iteritems():
         if addr160=='ROOT':
            continue
         # I assume these will be references, not copies
         addrList.append( addrObj )
      return addrList


   #############################################################################
   def getLinearAddrList(self, withImported=True, withAddrPool=False):
      """ 
      Retrieves a list of addresses, by hash, in the order they 
      appear in the wallet file.  Can ignore the imported addresses
      to get only chained addresses, if necessary.

      I could do this with one list comprehension, but it would be long.
      I'm resisting the urge...
      """
      addrList = []
      for a160 in self.linearAddr160List:
         addr = self.addrMap[a160]
         if not a160=='ROOT' and (withImported or addr.chainIndex>=0):
            # Either we want imported addresses, or this isn't one
            if (withAddrPool or addr.chainIndex<=self.highestUsedChainIndex):
               addrList.append(addr)
         
      return addrList


   #############################################################################
   def getAddress160ByChainIndex(self, desiredIdx):
      """
      It should be safe to assume that if the index is less than the highest 
      computed, it will be in the chainIndexMap, but I don't like making such
      assumptions.  Perhaps something went wrong with the wallet, or it was
      manually reconstructed and has holes in the chain.  We will regenerate
      addresses up to that point, if necessary (but nothing past the value
      self.lastComputedChainIndex.
      """
      if desiredIdx>self.lastComputedChainIndex or desiredIdx<0:
         # I removed the option for fillPoolIfNecessary, because of the risk
         # that a bug may lead to generation of billions of addresses, which
         # would saturate the system's resources and fill the HDD.
         raise WalletAddressError('Chain index is out of range')

      if self.chainIndexMap.has_key(desiredIdx):
         return self.chainIndexMap[desiredIdx]
      else:
         # Somehow the address isn't here, even though it is less than the
         # last computed index
         closestIdx = 0
         for idx,addr160 in self.chainIndexMap.iteritems():
            if closestIdx<idx<=desiredIdx:
               closestIdx = idx
               
         gap = desiredIdx - closestIdx
         extend160 = self.chainIndexMap[closestIdx]
         for i in range(gap+1):
            extend160 = self.computeNextAddress(extend160)
            if desiredIdx==self.addrMap[extend160].chainIndex:
               return self.chainIndexMap[desiredIdx]


   #############################################################################
   def pprint(self, indent='', allAddrInfo=True):
      raise NotImplementedError("deprecated")
      print indent + 'PyBtcWallet  :', self.uniqueIDB58
      print indent + '   useEncrypt:', self.useEncryption
      print indent + '   watchOnly :', self.watchingOnly
      print indent + '   isLocked  :', self.isLocked
      print indent + '   ShortLabel:', self.labelName 
      print indent + '   LongLabel :', self.labelDescr
      print ''
      print indent + 'Root key:', self.addrMap['ROOT'].getAddrStr(),
      print '(this address is never used)'
      if allAddrInfo:
         self.addrMap['ROOT'].pprint(indent=indent)
      print indent + 'All usable keys:'
      sortedAddrList = self.getAddrListSortedByChainIndex()
      for i,addr160,addrObj in sortedAddrList:
         if not addr160=='ROOT':
            print '\n' + indent + 'Address:', addrObj.getAddrStr()
            if allAddrInfo:
               addrObj.pprint(indent=indent)


   #############################################################################
   def isEqualTo(self, wlt2, debug=False):
      isEqualTo = True
      isEqualTo = isEqualTo and (self.uniqueIDB58 == wlt2.uniqueIDB58)
      isEqualTo = isEqualTo and (self.labelName  == wlt2.labelName )
      isEqualTo = isEqualTo and (self.labelDescr == wlt2.labelDescr)
      try:

         rootstr1 = binary_to_hex(self.addrMap['ROOT'].serialize())
         rootstr2 = binary_to_hex(wlt2.addrMap['ROOT'].serialize())
         isEqualTo = isEqualTo and (rootstr1 == rootstr2)
         if debug:
            print ''
            print 'RootAddrSelf:'
            print prettyHex(rootstr1, indent=' '*5)
            print 'RootAddrWlt2:'
            print prettyHex(rootstr2, indent=' '*5)
            print 'RootAddrDiff:',
            pprintDiff(rootstr1, rootstr2, indent=' '*5)

         for addr160 in self.addrMap.keys():
            addrstr1 = binary_to_hex(self.addrMap[addr160].serialize())
            addrstr2 = binary_to_hex(wlt2.addrMap[addr160].serialize())
            isEqualTo = isEqualTo and (addrstr1 == addrstr2)
            if debug:
               print ''
               print 'AddrSelf:', binary_to_hex(addr160),
               print prettyHex(binary_to_hex(self.addrMap['ROOT'].serialize()), indent='     ')
               print 'AddrSelf:', binary_to_hex(addr160),
               print prettyHex(binary_to_hex(wlt2.addrMap['ROOT'].serialize()), indent='     ')
               print 'AddrDiff:',
               pprintDiff(addrstr1, addrstr2, indent=' '*5)
      except:
         return False

      return isEqualTo


   #############################################################################
   def toJSONMap(self):
      outjson = {}
      outjson['name']             = self.labelName
      outjson['description']      = self.labelDescr
      outjson['walletversion']    = getVersionString(PYBTCWALLET_VERSION)
      outjson['balance']          = AmountToJSON(self.getBalance('Spend'))
      outjson['keypoolsize']      = self.addrPoolSize
      outjson['numaddrgen']       = len(self.addrMap)
      outjson['highestusedindex'] = self.highestUsedChainIndex
      outjson['watchingonly']     = self.watchingOnly
      outjson['createdate']       = self.wltCreateDate
      outjson['walletid']         = self.uniqueIDB58
      outjson['isencrypted']      = self.useEncryption
      outjson['islocked']         = self.isLocked if self.useEncryption else False
      outjson['keylifetime']      = self.defaultKeyLifetime

      return outjson


   #############################################################################
   def fromJSONMap(self, jsonMap, skipMagicCheck=False):
      self.labelName   = jsonMap['name']
      self.labelDescr  = jsonMap['description']
      self.addrPoolSize  = jsonMap['keypoolsize']
      self.highestUsedChainIndex  = jsonMap['highestusedindex']
      self.watchingOnly  = jsonMap['watchingonly']
      self.wltCreateDate  = jsonMap['createdate']
      self.uniqueIDB58  = jsonMap['walletid']
      jsonVer = hex_to_binary(jsonMap['walletversion'])

      # Issue a warning if the versions don't match
      if not jsonVer == getVersionString(PYBTCWALLET_VERSION):
         LOGWARN('Unserializing wallet of different version')
         LOGWARN('   Wallet Version: %d' % jsonVer)
         LOGWARN('   Armory Version: %d' % UNSIGNED_TX_VERSION)

   ###############################################################################
   @CheckWalletRegistration
   def getAddrTotalTxnCount(self, a160):
      try:
         return self.addrTxnCountDict[a160]
      except:
         return 0
      
   ###############################################################################
   @CheckWalletRegistration
   def getAddrDataFromDB(self):
      countList = self.cppWallet.getAddrTxnCountsFromDB()
      
      for addr in countList:
         self.addrTxnCountDict[addr] = countList[addr]
         
      balanceList = self.cppWallet.getAddrBalancesFromDB()
      
      for addr in balanceList:
         self.addrBalanceDict[addr] = balanceList[addr]
   
   ###############################################################################
   @CheckWalletRegistration
   def getHistoryAsCSV(self, currentTop):
      file = open('%s.csv' % self.walletPath, 'wb')
      
      sortedAddrList = self.getAddrListSortedByChainIndex()    
      chainCode = sortedAddrList[0][2].chaincode.toHexStr()  
      
      bal = self.getBalance('full')
      bal = bal  / float(100000000)
      file.write("%s,%f,%s,#%d\n" % (self.uniqueIDB58, bal, chainCode, currentTop))
      

      for i,addr160,addrObj in sortedAddrList:
         cppAddr = self.cppWallet.getScrAddrObjByKey(Hash160ToScrAddr(addr160))
         bal = cppAddr.getFullBalance() / float(100000000)
         
         le = cppAddr.getFirstLedger() 
         unixtime = le.getTxTime()
         block = le.getBlockNum()
         
         if unixtime == 0:
            block = 0
         
         realtime = datetime.fromtimestamp(unixtime).strftime('%Y-%m-%d %H:%M:%S')
         timeAndBlock = ",#%d,%s,%d" % (block, realtime, unixtime)
         
         cppAddrObj = self.cppWallet.getAddrObjByIndex(addrObj.chainIndex)
         putStr = '%d,%s,%s,%f%s\n' \
                  % (i, cppAddrObj.getScrAddr(), addrObj.binPublicKey65.toHexStr(), bal, \
                     (timeAndBlock if unixtime != 0 else ""))
                  
         file.write(putStr)
         
      file.close()
      
   ###############################################################################
   @CheckWalletRegistration
   def getHistoryPage(self, pageID):
      try:
         return self.cppWallet.getHistoryPage(pageID)
      except:
         raise 'pageID is out of range'  
      
   ###############################################################################
   @CheckWalletRegistration
   def doAfterScan(self):
      
      actionsList = self.actionsToTakeAfterScan
      self.actionsToTakeAfterScan = []      
      
      for calls in actionsList:
         calls[0](*calls[1])
         
   ###############################################################################
   @CheckWalletRegistration
   def sweepAfterRescan(self, addrList, main): 
      #get a new address from the wallet to sweep the funds to
      sweepToAddr = self.getNextUnusedAddress().getAddr160()
      
      main.finishSweepScan(self, addrList, sweepToAddr)
      return
 
   ###############################################################################
   @CheckWalletRegistration
   def sweepAddressList(self, addrList, main):
      self.actionsToTakeAfterScan.append([self.sweepAfterRescan, [addrList, main]])    
      
      addrVec = []
      for addr in addrList:
         addrVec.append(ADDRBYTE + addr.getAddr160())
      
      _id = Cpp.SecureBinaryData().GenerateRandom(8).toHexStr()
      main.oneTimeScanAction[_id] = self.doAfterScan()
      TheBDM.bdv().registerAddrList(_id, addrList)
            
   ###############################################################################
   @CheckWalletRegistration
   def disableWalletUI(self):
      self.isEnabled = False   

   ###############################################################################
   @CheckWalletRegistration
   def getCppAddr(self, scrAddr):
      return self.getScrAddrObj(Hash160ToScrAddr(scrAddr))
   
   ###############################################################################
   @CheckWalletRegistration
   def getLedgerEntryForTxHash(self, txHash):
      return self.cppWallet.getLedgerEntryForTxHash(txHash)

   ###############################################################################
   @CheckWalletRegistration
   def getScrAddrObj(self, scrAddr):
      fullBalance = 0
      spendableBalance = 0
      unconfirmedBalance = 0  
      txioCount = 0    
      
      try:
         addrBalances = self.addrBalanceDict[scrAddr]
         txioCount = self.getAddrTotalTxnCount(scrAddr)
         
         fullBalance = addrBalances[0]
         spendableBalance = addrBalances[1]
         unconfirmedBalance = addrBalances[2]
      except:
         pass
      

      scraddrobj = self.cppWallet.getScrAddrObjByKey(scrAddr, \
         fullBalance, spendableBalance, unconfirmedBalance, txioCount)
      return scraddrobj
  
   ###############################################################################
   def getP2PKHAddrForIndex(self, chainIndex):
      if chainIndex < 0:
         raise NotImplementedError("need to cover this behavior")
     
      return self.cppWallet.getP2PKHAddrForIndex(chainIndex)   

   ###############################################################################
   def getNestedSWAddrForIndex(self, chainIndex):
      if chainIndex < 0:
         raise('Nested addresses are no available for imports')
      
      return self.cppWallet.getNestedSWAddrForIndex(chainIndex)
   
   ###############################################################################
   def getNestedP2PKAddrForIndex(self, chainIndex):
      if chainIndex < 0:
         raise('Nested addresses are no available for imports')
      
      return self.cppWallet.getNestedP2PKAddrForIndex(chainIndex) 
   
   ###############################################################################
   def getPrivateKeyForIndex(self, index):
      addr160 = self.chainIndexMap[index]
      addrObj = self.addrMap[addr160]
      
      return addrObj.binPrivKey32_Plain
   
   ###############################################################################
   def getAddrObjectForHash(self, hashVal):
      assetIndex = self.cppWallet.getAssetIndexForAddr(hashVal)
      if assetIndex == 2**32:
         raise("unknown hash")
      
      try:
         addr160 = self.chainIndexMap[assetIndex]
      except:
         if assetIndex < -2:
            importIndex = self.cppWallet.convertToImportIndex(assetIndex)
            addr160 = self.linearAddr160List[importIndex]
         else:
            raise Exception("invalid address index")
         
      return self.addrMap[addr160]
   
   ###############################################################################
   def returnFilteredCppAddrList(self, filterUse, filterType):
      from qtdefines import CHANGE_ADDR_DESCR_STRING
      
      addrList = []
      keepInUse = filterUse != "Unused"
      keepChange = filterUse == "Change"
      
      typeCount = 0
      
      for addrIndex in self.chainIndexMap:
         
         if addrIndex < 0:
            continue
         
         #filter by address type
         if filterType != self.cppWallet.getAddrTypeForIndex(addrIndex):
            continue
         
         addrObj = self.cppWallet.getAddrObjByIndex(addrIndex)
         typeCount = typeCount + 1         
         
         #filter by usage
         inUse = addrObj.getTxioCount() != 0
         if not keepChange and inUse != keepInUse:
            continue
         
         #filter by change flag
         addrComment = self.getCommentForAddress(addrObj.getAddrHash()[1:])
         isChange = addrComment == CHANGE_ADDR_DESCR_STRING
         if isChange != keepChange:
            continue
         
         addrObj.setComment(addrComment)
         addrList.append(addrObj)
         
      return addrList
   
   ###############################################################################
   def getAddrByIndex(self, index):
      if index > -2:
         addr160 = self.chainIndexMap[index]
         return self.addrMap[addr160]
      else:
         importIndex = self.cppWallet.convertFromImportIndex(index)
         addr160 = self.linearAddr160List[importIndex]
         return self.addrMap[addr160]
   
   ###############################################################################
   def getImportCppAddrList(self):
   
      addrList = []
      for addrIndex in self.importList:
         
         addrObj = self.cppWallet.getImportAddrObjByIndex(addrIndex)    
         addrComment = self.getCommentForAddress(addrObj.getAddrHash()[1:])
         addrObj.setComment(addrComment)
         
         addrList.append(addrObj)
         
      return addrList  
   
   ###############################################################################
   def hasImports(self):
      return len(self.importList) != 0
       
###############################################################################
def getSuffixedPath(walletPath, nameSuffix):
   fpath = walletPath

   pieces = os.path.splitext(fpath)
   if not pieces[0].endswith('_'):
      fpath = pieces[0] + '_' + nameSuffix + pieces[1]
   else:
      fpath = pieces[0] + nameSuffix + pieces[1]
   return fpath



# Putting this at the end because of the circular dependency
from armoryengine.BDM import TheBDM, getCurrTimeAndBlock, BDM_BLOCKCHAIN_READY
from armoryengine.PyBtcAddress import PyBtcAddress
from armoryengine.Transaction import *
from armoryengine.Script import scriptPushData

# kate: indent-width 3; replace-tabs on;
