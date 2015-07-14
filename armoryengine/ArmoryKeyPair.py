################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
from ArmoryUtils import *

from ArmoryEncryption import ArmoryCryptInfo, EkeyMustBeUnlocked, \
   NULLCRYPTINFO, NULLSBD
from BinaryPacker import BinaryPacker, BinaryUnpacker, makeBinaryUnpacker
from BitSet import BitSet
from Decorators import VerifyArgTypes
from WalletEntry import WalletEntry
from WalletLabels import ScrAddrLabel, ScrAddrDesc, TxLabel

import CppBlockUtils as Cpp


#####
def SplitChildIndex(cIdx):
   if not 0 <= cIdx < 2**32:
      raise ValueError('Child indices must be less than 2^32')
   childNum   = int(cIdx & 0x7fffffff)
   isHardened = (cIdx & HARDBIT) > 0
   return [childNum, isHardened]

#####
def CreateChildIndex(childNum, isHardened):
   if not childNum < 1<<31:
      raise ValueError('Child number must be less than 2^31')

   topBit = HARDBIT if isHardened else 0
   return childNum | topBit

#####
def ChildIndexToStr(cIdx, hardChar="'"):
   cnum,hard = SplitChildIndex(cIdx)
   return str(cnum) + (hardChar if hard else '')


################################################################################
#
# AKP ~ ArmoryKeyPair
#
################################################################################
class ArmoryKeyPair(WalletEntry):
   """
   This is essentailly a pure virtual class.  It's not intended to be used by
   itself,
   """

   #############################################################################
   def __init__(self):
      super(ArmoryKeyPair, self).__init__()

      # Stuff mainly
      self.isWatchOnly     = False
      self.privCryptInfo   = NULLCRYPTINFO()
      self.sbdPrivKeyData  = NULLSBD()
      self.sbdPublicKey33  = NULLSBD()
      self.sbdChaincode    = NULLSBD()
      self.useCompressPub  = True
      self.isUsed          = False
      self.notForDirectUse = False  # perhaps only intended for multisig
      self.keyBornTime     = 0
      self.keyBornBlock    = 0
      self.privKeyNextUnlock = False
      self.akpParScrAddr   = None
      self.childIndex      = None
      self.isAkpRootRoot   = False
      self.level           = 0

      # Used for the recursive fill-keypool call
      self.childPoolSize   = DEFAULT_CHILDPOOLSIZE.get(self.getName(), 0)
      self.maxChildren     = UINT32_MAX

      # Some parameters that might be slow to calc
      self.rawScript       = None
      self.scrAddrStr      = None
      self.uniqueIDBin     = None
      self.uniqueIDB58     = None   # wallet ID used in filename

      # A bunch of references that will be set after all WalletEntries read
      self.akpChildByIndex    = {}
      self.akpChildByScrAddr  = {}
      self.lowestUnusedChild  = 0
      self.nextChildToCalc    = 0
      self.akpParentRef       = None
      self.masterEkeyRef      = None
      self.masterKdfRef       = None
      self.scrAddrLabelRef    = None
      self.scrAddrDescRef     = None


   #############################################################################
   # PASSTHROUGH functions to masterEKeyRef for convenience
   def isLocked(self):
      if self.masterEkeyRef is None:
         return False
      return self.masterEkeyRef.isLocked()

   def lock(self):
      if self.masterEkeyRef is None:
         return
      self.masterEkeyRef.lock()

   def unlock(self, passphrase, kdfObj=None, justVerify=False, timeout=None, Progress=None):
      if self.masterEkeyRef is None:
         return
      self.masterEkeyRef.unlock(passphrase, kdfObj=kdfObj,
                                justVerify=justVerify, timeout=timeout)
   def checkLockTimeout(self):
      if self.masterEkeyRef is None:
         return
      return self.masterEkeyRef.checkLockTimeout()

   #############################################################################
   def getChildIndex(self):
      return self.childIndex

   #############################################################################
   def getParent(self):
      return self.akpParentRef

   #############################################################################
   # Recursively search the node path for the root.   
   def getRoot(self):
      parent = self.getParent()
      return self if not parent or self == parent else parent.getRoot()
   
   #############################################################################
   # Recursively get every element in the index vector going from the leaf node
   # back throught the parents to the root.
   def getIndexVector(self):
      parent = self.getParent()
      if parent and parent != self:
         result = parent.getIndexVector()
         result.insert(0, self.getChildIndex())
      else:
         result = []
      return result

   def getKeys(self):
      return [self.akpChildByIndex[i].getScrAddr() for i in range(self.nextChildToCalc)]

   #############################################################################
   def registerWallet(self, isNew=False):
      if len(self.uniqueIDB58) == 0:
         raise('cannot register a wallet with an empty uniqueIDB58')

      #this returns a pointer to the BtcWallet C++ object. This object is
      #instantiated at registration and is unique for the BDV object, so we
      #should only ever set the cppWallet member here
      self.cppWallet = getBDM().registerWallet(self.getKeys(), self.uniqueIDB58, isNew)

   #############################################################################
   def setWalletFile(self, wltRef):
      self.wltFileRef = wltRef


   #############################################################################
   def hasAddr(self, addr160):
      scrAddr = hash160_to_scrAddr(addr160)
      return self.akpChildByScrAddr.get(scrAddr) is not None
      
   #############################################################################
   def setCryptInfo(self, cryptInfo=None, ekeyRef=None,
                    kdfRef=None, fsync=True):
      self.privCryptInfo = cryptInfo.copy() if cryptInfo else NULLCRYPTINFO()
      self.masterEkeyRef = ekeyRef
      self.masterKdfRef  = kdfRef
      if fsync:
         self.queueFsync()


   #############################################################################
   def changeCryptInfo(self, cryptInfo=None, ekeyRef=None, kdfRef=None):
      """
      Changes the encryption method for this key pair.
      See setWalletCryptInfo for a more thorough explanation of what
      each argument is.
      """
      aciDecryptAgs = self.getPrivCryptArgs(self.privCryptInfo)
      sbdPlain = self.privCryptInfo.decrypt(self.sbdPrivKeyData,
                                            **aciDecryptAgs)
      self.setCryptInfo(cryptInfo, ekeyRef, kdfRef)
      aciDecryptAgs = self.getPrivCryptArgs(self.privCryptInfo)
      self.sbdPrivKeyData = self.privCryptInfo.encrypt(sbdPlain, 
                                                       **aciDecryptAgs)
      for child in self.akpChildByIndex.values():
         child.changeCryptInfo(cryptInfo, ekeyRef, kdfRef)

   #############################################################################
   def setWalletAndCryptInfo(self, wltRef=None, cryptInfo=None, ekeyRef=None, kdfRef=None):
      """
      Can use args to preset wlt file ref, and crypt info
      Note, as of this writing, kdfRef (and self.masterKdfRef) are not
      normally specified.  This is because cryptInfo usually uses chained
      encryption, and the KDF is already referenced in the ekeyRef object

      A more rigorous explanation:
         A cryptInfo object is normally attached to a piece of encrypted data
         to specify how that data is encrypted and what will be the source of
         the decryption key.  In some circumstances, the source will be
         "PASSWORD" and will have a KDF referenced to use to stretch that
         password to get the final decryption key.

         In the case of Armory wallets, we rarely encrypt data directly with
         passphrase and KDF.  Instead, we have a master 32-byte encryption key
         for the whole wallet, and the cryptInfo object uses its ekeyID as the
         "keySource" for the encryption.  The passphrasing and KDF (stretching)
         is still there, but it's used on the ekey only, so it's specified when
         you setup the ekey object originally, not here (and maintained as part
         of the EncryptionKey object, not part of the AKP object)

         If you decide to create an AKP object directly with passphrase and
         stretching (not chained through an Ekey object), then you will pass
         in the relevant privCryptInfo with a valid kdfRef but ekeyRef=None.
      """
      self.setWalletFile(wltRef)
      self.setCryptInfo(cryptInfo, ekeyRef, kdfRef)

   #############################################################################
   def setChildPoolSize(self, newSize):
      self.childPoolSize = newSize


   #############################################################################
   def setLabel(self, labelStr, fsync=True):
      if self.scrAddrLabelRef is None:
         self.scrAddrLabelRef = ScrAddrLabel()
         self.scrAddrLabelRef.wltFileRef = self.wltFileRef
         self.scrAddrLabelRef.wltParentID = self.wltParentID
         self.scrAddrLabelRef.outerCrypt = self.outerCrypt.copy()
         self.scrAddrLabelRef.wltParentRef = self
         self.scrAddrLabelRef.initialize(self.getScrAddr(), labelStr)
         self.scrAddrLabelRef.akpRef = self
      else:
         self.scrAddrLabelRef.label = labelStr
      if fsync:
         self.scrAddrLabelRef.queueFsync()


   #############################################################################
   def getLabel(self):
      if self.scrAddrLabelRef is not None:
         return self.scrAddrLabelRef.label
      return ''


   #############################################################################
   def setDescription(self, descriptionStr, fsync=True):
      if self.scrAddrDescRef is None:
         self.scrAddrDescRef = ScrAddrDesc()
         self.scrAddrDescRef.wltFileRef = self.wltFileRef
         self.scrAddrDescRef.wltParentID = self.wltParentID
         self.scrAddrDescRef.outerCrypt = self.outerCrypt.copy()
         self.scrAddrDescRef.wltParentRef = self
         self.scrAddrDescRef.initialize(self.getScrAddr(), descriptionStr)
         self.scrAddrDescRef.akpRef = self
      else:
         self.scrAddrDescRef.description = descriptionStr
      if fsync:
         self.scrAddrDescRef.queueFsync()


   #############################################################################
   def getDescription(self):
      if self.scrAddrDescRef is not None:
         return self.scrAddrDescRef.description
      return ''

   #############################################################################
   def setTxComment(self, txHashBin, comment, fsync=True):
      txComment = self.wltFileRef.txLabelMap.get(txHashBin)
      if txComment is None:
         txComment = TxLabel()
         txComment.wltFileRef = self.wltFileRef
         txComment.wltParentID = self.wltParentID
         txComment.outerCrypt = self.outerCrypt.copy()
         txComment.wltParentRef = self
         txComment.initialize(txHashBin, None, comment)
         txComment.akpRef = self
      else:
         txComment.uComment = comment
      if fsync:
         txComment.queueFsync()


   #############################################################################
   def getTxComment(self, txHashBin):
      txComment = self.wltFileRef.txLabelMap.get(txHashBin)
      if txComment is not None:
         return txComment.uComment
      return ''


   #############################################################################
   def numKeysNeededToFillPool(self):
      # This is used to help us fill they keypool for a given node.  It respects
      # the childPoolSize member var, but never exceeds the maxChildren member
      if self.nextChildToCalc >= self.maxChildren:
         return 0
      else:
         currPoolSz = self.nextChildToCalc - self.lowestUnusedChild
         if currPoolSz >= self.childPoolSize:
            return 0
         else:
            topChild = min(self.nextChildToCalc + self.childPoolSize,
                                                            self.maxChildren)
            return topChild - self.nextChildToCalc



   #############################################################################
   def getNextChildToCalcIndex(self):
      topbit = HARDBIT if self.HARDCHILD else 0
      return self.nextChildToCalc | topbit


   #############################################################################
   def fillKeyPool(self, fsync=True, Progress=emptyFunc):
      """
      TODO:  Progress needs to be integrated into this method...somehow.
             It is typically a function prepared by the GUI, that can be
             called with two arguments, current & total, which triggers GUI
             progress bar updates.  However, given the recursive nature of
             this method, we might have to get creative to be able to make
             meaningful updates via this callback. (perhaps class reflection
             combined with DEFAULT_CHILDPOOLSIZEs to figure out the total
             count, and then only call this method from if self is of a
             given class/type? perhaps only if it is a registered display
             storage class...?)
      """

      if self.sbdPublicKey33 is None or self.sbdPublicKey33.getSize()==0:
         raise UninitializedError('AKP object not init, cannot fill pool')

      if self.TREELEAF:
         return

      keysToGen = self.numKeysNeededToFillPool()
      akps = []
      for i in range(keysToGen):
         index = self.getNextChildToCalcIndex()
         newAkp = self.spawnChild(index, fsync=fsync, linkToParent=True)

      # Now recurse to each child
      for scrAddr,childAKP in self.akpChildByScrAddr.iteritems():
         childAKP.fillKeyPool(fsync=fsync, Progress=Progress)



   #############################################################################
   def getChildByIndex(self, index, spawnIfNeeded=False, fsync=True, linkToParent=True):
      # Only gets precomputed children
      ch = self.akpChildByIndex.get(index)
      if ch is None:
         if spawnIfNeeded:
            ch = self.spawnChild(index, privSpawnReqd=False, fsync=fsync, linkToParent=linkToParent)
         else:
            raise ChildDeriveError('Child index=%s not found in %s' % \
                                    (ChildIndexToStr(index), self.getName()))

      return ch

   #############################################################################
   def getChildByScrAddr(self, scrAddr):
      # Only gets precomputed children
      ch = self.akpChildByScrAddr.get(scrAddr)
      if ch is None:
         raise ChildDeriveError('Child "%s" not found in %s' %
                                (binary_to_hex(scrAddr), self.getName()))
      return ch

   #############################################################################
   def getChildByPath(self, iList, spawnIfNeeded=True, fsync=True):
      akp = self
      for i in iList:
         akp = akp.getChildByIndex(i, spawnIfNeeded, fsync)
      return akp

   #############################################################################
   def getChildSpawnClass(self, index):
      # This method is used not only to get the child AKP class,
      # but to define limits on which children indices are acceptable
      raise NotImplementedError(
         '"%s" needs to implement getChildSpawnClass()' % self.getName())


   #############################################################################
   def spawnChild(self, childIndex):
      raise NotImplementedError('"%s" needs to implement spawnChild()' %
                                self.getName())

   #############################################################################
   def addAkpChildRef(self, childAKP):
      if childAKP.getChildIndex() is None:
         raise ValueError('Child AKP has no childIndex')

      # Must set AKP parent, as well as general WalletEntry parent
      self.akpChildByIndex[childAKP.getChildIndex()] = childAKP
      self.akpChildByScrAddr[childAKP.getScrAddr()] = childAKP
      childAKP.akpParentRef  = self
      childAKP.akpParScrAddr = self.getScrAddr()
      childAKP.wltParentRef  = self.wltParentRef
      childAKP.wltParentID   = self.wltParentID

      childP1 = childAKP.getChildIndex() + 1
      self.nextChildToCalc = max(self.nextChildToCalc, childP1)
      if childAKP.isUsed:
         self.lowestUnusedChild = max(self.lowestUnusedChild, childP1)


   #############################################################################
   def linkWalletEntries(self, wltFileRef):
      """
      All children nodes look for their parents in the wallet file and call
      the addAkpChildRef method.
      """
      super(ArmoryKeyPair, self).linkWalletEntries(wltFileRef)

      self.masterEkeyRef = wltFileRef.ekeyMap.get(self.privCryptInfo.keySource)
      self.masterKdfRef  = wltFileRef.kdfMap.get(self.privCryptInfo.kdfObjID)

      if not self.isAkpRootRoot:
         foundParent = wltFileRef.masterScrAddrMap.get(self.akpParScrAddr)
         if foundParent is None:
            self.isDisabled = True
         else:
            self.akpParentRef = foundParent
            self.getParent().addAkpChildRef(self)


   #############################################################################
   def getName(self):
      return self.__class__.__name__


   #############################################################################
   def getScript(self, forceRecompute=False):
      if self.rawScript is None:
         self.recomputeScript()
      return self.rawScript

   #############################################################################
   def getScrAddr(self, forceRecompute=False):
      if self.scrAddrStr is None or forceRecompute:
         self.recomputeScrAddr()
      return self.scrAddrStr

   #############################################################################
   def getAddrStr(self, forceRecompute=False):
      return scrAddr_to_addrStr(self.getScrAddr())

   #############################################################################
   def getUniqueIDBin(self, forceRecompute=False):
      if self.uniqueIDBin is None or forceRecompute:
         self.recomputeUniqueIDBin()
      return self.uniqueIDBin

   #############################################################################
   def getUniqueIDB58(self, forceRecompute=False):
      if self.uniqueIDB58 is None or forceRecompute:
         self.recomputeUniqueIDB58()
      return self.uniqueIDB58

   #############################################################################
   def recomputeScript(self):
      raise NotImplementedError('"%s" needs to implement recomputeScript()' % \
                                                                 self.getName())
   def recomputeScrAddr(self):
      self.recomputeScript()
      self.scrAddrStr = script_to_scrAddr(self.rawScript)

   def recomputeUniqueIDBin(self):
      raise NotImplementedError('"%s" needs to implement recomputeUniqueIDBin()' % \
                                                                 self.getName())
   def recomputeUniqueIDB58(self):
      self.recomputeUniqueIDBin()
      if self.uniqueIDBin is None:
         self.uniqueIDB58 = None
      else:
         self.uniqueIDB58 = binary_to_base58(self.uniqueIDBin)

   #############################################################################
   def getEntryID(self):
      return self.getScrAddr()

   #############################################################################
   def copy(self):
      newAKP = self.__class__()
      newAKP.copyFromAKP(self)
      return newAKP

   #############################################################################
   def copyFromAKP(self, other):
      """
      Note:  This copies just the base class AKP members.  It doesn't copy
             any members that are in the derived class, though the child class
             will be the same class as self
      """

      self.isWatchOnly     = other.isWatchOnly

      self.privCryptInfo   = other.privCryptInfo.copy()
      self.sbdPrivKeyData  = other.sbdPrivKeyData.copy()
      self.sbdPublicKey33  = other.sbdPublicKey33.copy()
      self.sbdChaincode    = other.sbdChaincode.copy()
      self.useCompressPub  = other.useCompressPub
      self.isUsed          = other.isUsed
      self.notForDirectUse = other.notForDirectUse
      self.keyBornTime     = other.keyBornTime
      self.keyBornBlock    = other.keyBornBlock
      self.privKeyNextUnlock = other.privKeyNextUnlock
      self.isAkpRootRoot   = other.isAkpRootRoot

      self.akpParScrAddr   = other.akpParScrAddr
      self.childIndex      = other.getChildIndex()
      self.level      = other.level

      self.akpChildByIndex   = other.akpChildByIndex.copy()
      self.akpChildByScrAddr = other.akpChildByScrAddr.copy()
      self.lowestUnusedChild = other.lowestUnusedChild
      self.nextChildToCalc   = other.nextChildToCalc
      self.akpParentRef      = other.getParent()
      self.masterEkeyRef     = other.masterEkeyRef
      self.masterKdfRef      = other.masterKdfRef

      self.scrAddrStr      = other.scrAddrStr
      self.rawScript       = other.rawScript

      self.wltFileRef       = other.wltFileRef


   #############################################################################
   @EkeyMustBeUnlocked('masterEkeyRef')
   def resolveNextUnlockFlag(self, fsync=True):
      if not self.privKeyNextUnlock:
         return

      if self.getParent() is None:
         raise KeyDataError('No parent defined from which to derive this key')

      if self.getChildIndex() is None:
         raise KeyDataError('No derivation path defined to derive this key')

      # Originally used an elegant recursive call here, but was worried
      # about that corner case with Armory 1.35 wallets where someone has
      # 100k addrs and will hit the recursion limit...

      # Instead we convert the recursion to a loop of AKP references back to
      # the first AKP whose parent.privKeyNextUnlock==False
      akpStack = [self]
      while akpStack[-1].getParent().privKeyNextUnlock:
         akpStack.append(akpStack[-1].getParent())

      # Now walk backwards, deriving every child from its parent
      if self.masterEkeyRef:
         self.masterEkeyRef.markKeyInUse()
      try:
         for akp in akpStack[::-1]:
            # This is technically still recursive, but we've guaranteed it will
            # only recurse one level on each call, since parent.privKeyNextUnlock
            # is false.  fsync is always False in the recursive call, applied
            # later if needed
            newAkp = akp.getParent().spawnChild(childIndex=akp.getChildIndex(),
                                                 privSpawnReqd=True,
                                                 fsync=False,
                                                 linkToParent=False)


            if akp.sbdPublicKey33.toBinStr() != newAkp.sbdPublicKey33.toBinStr():
               raise KeyDataError('Derived key supposed to match but does not')

            akp.sbdPrivKeyData    = newAkp.sbdPrivKeyData.copy()
            akp.privKeyNextUnlock = False

            if fsync:
               self.wltFileRef.addFileOperationToQueue('UpdateEntry', self)

      finally:
         if self.masterEkeyRef:
            self.masterEkeyRef.finishedWithKey()


   #############################################################################
   def initializeAKP(self, isWatchOnly,
                           isAkpRootRoot,
                           privCryptInfo,
                           sbdPrivKeyData,
                           sbdPublicKey33,
                           sbdChaincode,
                           privKeyNextUnlock,
                           akpParScrAddr,
                           childIndex,
                           level,
                           useCompressPub,
                           isUsed,
                           notForDirectUse,
                           keyBornTime=UINT64_MAX,
                           keyBornBlock=UINT32_MAX):

      self.__init__()

      self.isWatchOnly     = isWatchOnly
      self.isAkpRootRoot   = isAkpRootRoot
      self.privCryptInfo   = privCryptInfo
      self.sbdPrivKeyData  = SecureBinaryData(sbdPrivKeyData)
      self.sbdPublicKey33  = SecureBinaryData(sbdPublicKey33)
      self.sbdChaincode    = SecureBinaryData(sbdChaincode)
      self.privKeyNextUnlock = privKeyNextUnlock
      self.akpParScrAddr   = akpParScrAddr
      self.childIndex      = childIndex
      self.useCompressPub  = useCompressPub
      self.isUsed          = isUsed
      self.notForDirectUse = notForDirectUse  # perhaps a multisig sibling
      self.keyBornTime     = keyBornTime
      self.keyBornBlock    = keyBornBlock
      self.level           = level

      if self.sbdPublicKey33.getSize() == 65:
         self.sbdPublicKey33 = CryptoECDSA().CompressPoint(self.sbdPublicKey33)


      self.recomputeScript()
      self.recomputeScrAddr()
      self.recomputeUniqueIDBin()
      self.recomputeUniqueIDB58()

      if isAkpRootRoot:
         # If parentless root (aka root-root), then set itself as parent
         self.akpParScrAddr = self.getScrAddr()
         self.akpParentRef  = self
         self.childIndex    = None




   #############################################################################
   def serializeAKP(self):

      pubKey = self.sbdPublicKey33.copy()
      if self.sbdPublicKey33.getSize() == 65:
         pubKey = CryptoECDSA().CompressPoint(self.sbdPublicKey33)

      flags = BitSet(16)
      flags.setBit(0, self.isWatchOnly)
      flags.setBit(1, self.isAkpRootRoot)
      flags.setBit(2, self.useCompressPub)
      flags.setBit(3, self.privKeyNextUnlock)
      flags.setBit(4, self.isUsed)
      flags.setBit(5, self.notForDirectUse)

      akpParSA = self.akpParScrAddr
      childIdx = self.getChildIndex()
      if self.isAkpRootRoot or self.akpParScrAddr is None:
         akpParSA = ''
         childIdx = 0

      # We are not committed to fixed-width wallet entries.  Might as well
      # Save space if fields are empty by using VAR_STRs
      bp = BinaryPacker()
      bp.put(UINT32,        getVersionInt(ARMORY_WALLET_VERSION))
      bp.put(BINARY_CHUNK,  self.FILECODE,                   8)
      bp.put(BITSET,        flags,                           2)
      bp.put(BINARY_CHUNK,  self.privCryptInfo.serialize(), 32)
      bp.put(VAR_STR,       self.sbdPrivKeyData.toBinStr())
      bp.put(VAR_STR,       pubKey.toBinStr())
      bp.put(VAR_STR,       self.sbdChaincode.toBinStr())
      bp.put(UINT64,        self.keyBornTime)
      bp.put(UINT32,        self.keyBornBlock)
      bp.put(VAR_STR,       akpParSA)
      bp.put(UINT32,        childIdx)
      bp.put(UINT32,        self.level)

      # Add Reed-Solomon error correction
      akpData = bp.getBinaryString()
      rsecData = WalletEntry.CreateErrCorrCode(akpData)

      output = BinaryPacker()
      output.put(VAR_STR, akpData)
      output.put(VAR_STR, rsecData)
      return output.getBinaryString()


   #############################################################################
   def unserializeAKP(self, toUnpack):
      toUnpack = makeBinaryUnpacker(toUnpack)

      akpData  = toUnpack.get(VAR_STR)
      rsecData = toUnpack.get(VAR_STR)

      akpData,failFlag,modFlag = WalletEntry.VerifyErrCorrCode(akpData, rsecData)

      if failFlag:
         LOGERROR('Unrecoverable error in wallet entry')
         self.isUnrecoverable = True
         return self
      elif modFlag:
         LOGWARN('Error in wallet file corrected successfully')
         self.needRewrite = True


      akpUnpack = BinaryUnpacker(akpData)

      version = akpUnpack.get(UINT32)
      if version != getVersionInt(ARMORY_WALLET_VERSION):
         LOGWARN('AKP version in file: %s,  Armory Wallet version: %s',
                     getVersionString(readVersionInt(version)),
                     getVersionString(ARMORY_WALLET_VERSION))



      # First pass is pretty much just to get to the RSEC code, second
      # pass is over the RS-corrected data.
      filecode          = akpUnpack.get(BINARY_CHUNK,  8)
      flags             = akpUnpack.get(BITSET,        2)
      privCryptInfoSer  = akpUnpack.get(BINARY_CHUNK, 32)
      privk             = akpUnpack.get(VAR_STR)
      pubk              = akpUnpack.get(VAR_STR)
      chain             = akpUnpack.get(VAR_STR)
      bornTime          = akpUnpack.get(UINT64)
      bornBlk           = akpUnpack.get(UINT32)
      parScrAddr        = akpUnpack.get(VAR_STR)
      childIndex        = akpUnpack.get(UINT32)
      level             = akpUnpack.get(UINT32)

      pcryptInfo = ArmoryCryptInfo().unserialize(privCryptInfoSer)

      if not filecode==self.FILECODE:
         LOGERROR('Wrong FILECODE for type being unserialized')
         LOGERROR('Self=%s, unserialized=%s' % (self.FILECODE, filecode))
         self.isUnrecoverable = True
         return self

      isWatchOnly       = flags.getBit(0)
      isAkpRootRoot     = flags.getBit(1)
      useCompressPub    = flags.getBit(2)
      privKeyNextUnlock = flags.getBit(3)
      isUsed            = flags.getBit(4)
      notForDirectUse   = flags.getBit(5)


      self.initializeAKP( isWatchOnly,
                          isAkpRootRoot,
                          pcryptInfo,
                          SecureBinaryData(privk),
                          SecureBinaryData(pubk),
                          SecureBinaryData(chain),
                          privKeyNextUnlock,
                          parScrAddr,
                          childIndex,
                          level,
                          useCompressPub,
                          isUsed,
                          notForDirectUse,
                          bornTime,
                          bornBlk)

      return self


   #############################################################################
   # I originally planned to have these two methods excluded since this is an
   # abstract base class and each subclass should implement this with a direct
   # call to AKP.serializeAKP/unserializeAKP.  But it turns out that many base
   # classes don't actually require any more than ser/unserAKP combined with
   # their unique FILECODE.  This is here so the classes can inherit it.
   def serialize(self):
      if self.sbdPublicKey33.getSize()==0:
         raise UninitializedError('Will not serialize uninitialized AKP')
      return self.serializeAKP()

   def unserialize(self, toUnpack):
      return self.unserializeAKP(toUnpack)

   #############################################################################
   def getPrivKeyAvailability(self):
      if self.isWatchOnly:
         return PRIV_KEY_AVAIL.WatchOnly
      elif self.privKeyNextUnlock:
         return PRIV_KEY_AVAIL.NextUnlock
      elif self.sbdPrivKeyData.getSize() > 0:
         if self.privCryptInfo.noEncryption():
            return PRIV_KEY_AVAIL.Available
         elif self.masterEkeyRef and not self.masterEkeyRef.isLocked():
            return PRIV_KEY_AVAIL.Available
         else:
            return PRIV_KEY_AVAIL.NeedDecrypt
      else:
         return PRIV_KEY_AVAIL.Uninit


   #############################################################################
   def useEncryption(self):
      return self.privCryptInfo.useEncryption()


   #############################################################################
   def serializeWatchOnlyData(self):
      raise NotImplementedError('Encoding not implemented yet')

   #############################################################################
   def unserializeWatchOnlyData(self):
      raise NotImplementedError('Encoding not implemented yet')


   #############################################################################
   def getSerializedPubKey(self, serType='bin'):
      """
      The various public key serializations:  "bin", "hex", "xpub"
      """
      if not self.useCompressPub:
         pub = CryptoECDSA().UncompressPoint(self.sbdPublicKey33).copy()
      else:
         pub = self.sbdPublicKey33.copy()

      if serType.lower()=='bin':
         return pub.toBinStr()
      elif serType.lower()=='hex':
         return pub.toHexStr()
      elif serType.lower()=='xpub':
         if isinstance(self, ArmoryBip32ExtendedKey):
            return self.getExtendedPubKey()
         else:
            raise RuntimeError('xpub only applies to BIP32 Extended Keys')


   #############################################################################
   @EkeyMustBeUnlocked('masterEkeyRef')
   def getSerializedPrivKey(self, serType='hex'):
      """
      The various private key serializations: "bin", hex", "sipa", "xprv", "bip38", "base58"
      """

      if self.useEncryption() and self.masterEkeyRef.isLocked():
         raise WalletLockError('Cannot serialize locked priv key')

      lastByte = '\x01' if self.useCompressPub else ''
      binPriv = self.getPlainPrivKeyCopy().toBinStr() + lastByte

      if serType.lower()=='bin':
         return binPriv
      if serType.lower()=='base58':
         return privKey_to_base58(binPriv)
      if serType.lower()=='hex':
         return binary_to_hex(binPriv)
      elif serType.lower()=='sipa':
         binSipa = getPrivKeyByte() + binPriv + computeChecksum(getPrivKeyByte()+binPriv)
         return binary_to_base58(binSipa)
      elif serType.lower()=='xprv':
         if isinstance(self, ArmoryBip32ExtendedKey):
            return self.getExtendedPrivKey()
         else:
            raise RuntimeError('xprv only applies to BIP32 Extended Keys')


   #############################################################################
   def getPrivCryptArgs(self, cryptInfoObj=None):
      """
      Examines self.privCryptInfo and produces as many arguments as it can
      that are needed to call self.privCryptInfo.encrypt/decrypt.   Note
      that this does not unlock the master key, or even check if it's locked.
      It simply returns a map of args that can be passed using **output to
      the cryptInfo.encrypt or decrypt functions.
      """
      if cryptInfoObj is None:
         cryptInfoObj = self.privCryptInfo

      mapOut = {}
      if cryptInfoObj.noEncryption():
         return mapOut

      if cryptInfoObj.getEncryptIVSrc()[0] == CRYPT_IV_SRC.PUBKEY20:
         # Stored IV data is 8 bytes, but when supplied externally it's 16
         mapOut['ivData'] = hash256(self.sbdPublicKey33.toBinStr())[:16]
         mapOut['ivData'] = SecureBinaryData(mapOut['ivData'])
      else:
         # If the IV is stored we don't need to pass it through, it
         # will grab it from itself in cryptInfoObj.decrypt/encrypt
         mapOut['ivData']  = None

      # Not normal for an AKP to have a direct KDF obj, but it might
      mapOut['ekeyObj'] = self.masterEkeyRef
      mapOut['kdfObj']  = self.masterKdfRef

      return mapOut



   #############################################################################
   def setPlainKeyData(self, cryptInfo, sbdPlainPriv, sbdPub, sbdChain,
                                          ekeyRef=None, verifyPub=True):
      """
      This is used to override the key data with UNENCRYPTED private key.
      The cryptoInfo argument will usually be from the parent from which
      this key was spawned.  It will inherit the same cryptInfo, and then
      used the masterEkeyRef (or supplied ekeyRef) to encrypt the plain priv
      key before storing.

      If you want this object to hold plain private key data,

      ekeyRef should never have to be supplied except in very strange
      enviroments -- self.masterEkeyRef should already be set, unlocked
      and correct for the new private key.
      """
      self.sbdPublicKey33 = CryptoECDSA().CompressPoint(sbdPub)
      self.sbdChaincode = sbdChain.copy()

      if sbdPlainPriv is None or sbdPlainPriv.getSize()==0:
         self.sbdPrivKeyData = NULLSBD()
         self.privCryptInfo = cryptInfo.copy()
         return
      elif verifyPub:
         pub65 = CryptoECDSA().ComputePublicKey(sbdPlainPriv)
         pubComputed33 = CryptoECDSA().CompressPoint(pub65)
         pubSupplied33 = CryptoECDSA().CompressPoint(sbdPub)
         if not pubComputed33 == pubSupplied33:
            raise KeyDataError('Supplied private and public key do not match!')



      if cryptInfo.useEncryption():
         if ekeyRef is None:
            if self.masterEkeyRef is None:
               raise KeyDataError('No ekey data available for encryption')
            ekeyRef = self.masterEkeyRef

         if ekeyRef.isLocked():
            raise EncryptionError('Ekey needs to be unlocked to set new priv key')


         if cryptInfo.keySource == ekeyRef.ekeyID:
            # If we had no masterEkey before and it was supplied as an arg, set it
            self.masterEkeyRef = ekeyRef
         else:
            raise EncryptionError('New ACI data does not match avail EKeys')


         if cryptInfo.hasStoredIV():
            # This method copies the ACI exactly, which should (under all
            # forseeable conditions) use "PUBKEY20" as the ivSource.  This
            # means that the IV to be used to encrypt this key will be
            # different than other keys (good).  However, if for some reason
            # we have a storedIV, then it will be reused (bad).
            raise EncryptionError('New priv key crypto inheriting non-pubkey IV')

      self.privCryptInfo = cryptInfo.copy()
      cryptArgs = self.getPrivCryptArgs()
      self.sbdPrivKeyData = self.privCryptInfo.encrypt(sbdPlainPriv, **cryptArgs)



   #############################################################################
   def unlockEkey(self, passphrase=None, kdfObj=None):
      """
      Ekeys should always already have the kdf set already, but we can
      pass it in if this is a strange environment where it was never set

      Note:  This method works with multi-password EKeys as well.  Just pass
             in a list of SBD passphrases (with NULLSBD() for the passphrases
             not supplied).  If KDF object refs are not already set in the
             ekey, pass them in as a list or map as the second arg.
      """
      if self.privCryptInfo.noEncryption():
         return True

      if self.masterEkeyRef is None:
         raise EncryptionError('No encryption key to unlock!')

      if not self.masterEkeyRef.isLocked():
         return True

      if passphrase is None:
         raise PassphraseError('Must supply a passphrase to unlock ekey')


      if not kdfObj:
         kdfObj = self.masterKdfRef

      return self.masterEkeyRef.unlock(passphrase, kdfObj)



   #############################################################################
   def verifyEkeyPassphrase(self, passphrase):
      """
      Note:  This method works with multi-password EKeys as well.  Just pass
             in a list of SBD passphrases (with NULLSBD() for the passphrases
             not supplied).
      """
      if self.masterEkeyRef is None:
         raise EncryptionError('No encryption key to unlock!')

      return self.masterEkeyRef.verifyPassphrase(passphrase)


   #############################################################################
   @EkeyMustBeUnlocked('masterEkeyRef')
   def getPlainPrivKeyCopy(self, verifyPublic=True):
      """
      This is the only way to get the private key out of an AKP object.
      The plain key is never kept in an AKP object, which is why there's
      no lock() and unlock() methods for AKP.  Instead, we only ever lock
      and unlock the master encryption key, and should be unlocked before
      this method is called.

      NOTE:  This returns an SBD object which needs to be .destroy()ed by
             the caller when it is finished with it.
      """

      if self.isWatchOnly:
         raise KeyDataError('Cannot get priv key from watch-only wallet')

      if self.privKeyNextUnlock:
         self.resolveNextUnlockFlag(False)

      try:
         sbdPlain = NULLSBD()
         aciDecryptAgs = self.getPrivCryptArgs(self.privCryptInfo)
         sbdPlain = self.privCryptInfo.decrypt(
            self.sbdPrivKeyData, **aciDecryptAgs)

         if verifyPublic:
            computedPub = CryptoECDSA().ComputePublicKey(sbdPlain)
            selfPub = CryptoECDSA().UncompressPoint(self.sbdPublicKey33)
            if computedPub.toBinStr() != selfPub.toBinStr():
               raise KeyDataError('Private key does not match stored pubkey! %s vs %s' % (computedPub.toHexStr(), selfPub.toHexStr()))

         return sbdPlain

      except:
         LOGEXCEPT('Failed to decrypt private key')
         sbdPlain.destroy()
         raise
         #return NULLSBD()


   #############################################################################
   @EkeyMustBeUnlocked('masterEkeyRef')
   def __signData(self, dataToSign, deterministicSig=False, normSig='Dontcare'):
      """
      This returns the raw data, signed using the CryptoECDSA module.  This
      should probably not be called directly by a top-level script, but
      instead the backbone of a bunch of standard methods for signing
      transactions, messages, perhaps Proof-of-Reserve trees, etc.

      "normSig" is based on a proposal to only allow even s-values, or
      odd s-values to limit transaction malleability.  We might as well
      put it here, though the default is not to mess with the outpout
      of the SignData call.
      """

      try:
         if deterministicSig:
            raise NotImplementedError('Cannot do deterministic signing yet')
            #sig = CryptoECDSA().SignData_RFC6979(dataToSign, self.getPlainPrivKeyCopy())
         else:
            sig = CryptoECDSA().SignData(dataToSign, self.getPlainPrivKeyCopy())

         sigstr = sig.toBinStr()
         rBin = sigstr[:32 ]
         sBin = sigstr[ 32:]

         if normSig != 'Dontcare':
            # normSig will either be 'even' or 'odd'.  If the calculated
            # s-value does not match, then use -s mod N which will be correct
            raise NotImplementedError('This code is not yet tested!')
            sInt = binary_to_int(sBin, BIGENDIAN)
            if (normSig=='even' and sInt%2==1) or \
               (normSig=='odd'  and sInt%2==0):
               sInt = (-sInt) % SECP256K1_MOD

            sBin = int_to_binary(sInt, widthBytes=32, endOut=BIGENDIAN)

         return (rBin, sBin)

      except:
         LOGEXCEPT('Error generating signature')


   #############################################################################
   # TODO - Fix undefined identifier createSigScriptFromRS
   @EkeyMustBeUnlocked('masterEkeyRef')
   def signTransaction(self, serializedTx, deterministicSig=False):
      rBin,sBin = self.__signData(serializedTx, deterministicSig)
      return createSigScriptFromRS(rBin, sBin)


   #############################################################################
   def verifyDERSignature(self, binMsgVerify, derSig):
      """
      Returns True if signature (derSig) is valid for the message (binMsgVerify)
      Returns False otherwise.
      """
      rBin, sBin = getRSFromDERSig(derSig)

      secMsg    = SecureBinaryData(binMsgVerify)
      secSig    = SecureBinaryData(rBin + sBin)
      secPubKey = CryptoECDSA().UncompressPoint(self.sbdPublicKey33)
      return CryptoECDSA().VerifyData(secMsg, secSig, secPubKey)


   #############################################################################
   @EkeyMustBeUnlocked('masterEkeyRef')
   def signMessage(self, msg, deterministicSig=False):
      """
      Returns just raw (r,s) pair instead of a sigscript because this is
      raw message signing, not transaction signing.  We match Bitcoin-Qt
      behavior which is to prefix the message with "Bitcoin Signed Message:"
      in order to guarantee that someone cannot be tricked into signing
      a real transaction:  instead of signing the input, MSG, it will only
      sign hash("Bitcoin Signed Message:\n" + MSG) which cannot be a
      transaction
      """
      fmtMsg = formatMessageToSign(msg)
      return self.__signData(SecureBinaryData(fmtMsg), deterministicSig)

   #############################################################################
   def clearSignMessage(self, msg, deterministicSig=False):
      sig = self.getSignature(msg)
      lines = [
         BEGIN_MARKER + CLEARSIGN_MSG_TYPE_MARKER + DASHX5,
         getComment(),
         '',
         standardizeMessage(msg),
         getEncodedBlock(BITCOIN_SIG_TYPE_MARKER, sig)
      ]

      return RN.join(lines)


   #############################################################################
   def b64SignMessage(self, msg, deterministicSig=False):
      return getEncodedBlock(BASE64_MSG_TYPE_MARKER,
                             self.getSignature(msg) + standardizeMessage(msg),
                             True)

   #############################################################################
   def getSignature(self, msg, deterministicSig=False):
      std = standardizeMessage(msg)
      sbdMsg = SecureBinaryData(std)
      r, s = self.signMessage(std, deterministicSig)
      rs = r + s
      binSig = None
      # try some high bytes until we get one that verifies
      for hb in range(31,35):
         try:
            binSig = SecureBinaryData(chr(hb) + rs)

            # find the sig that will produce our address
            pk = getMessagePubKey(sbdMsg, binSig)
            if pk.toHexStr() == self.sbdPublicKey33.toHexStr():
               break
         except Exception as e:
            pass
      else:
         raise RuntimeError("Could not find signature hb")
      return binSig.toBinStr()


   #############################################################################
   def getB64Signature(self, msg, deterministicSig=False):
      sig = self.getSignature(msg, deterministicSig)
      return base64.b64encode(sig)


   #############################################################################
   def advanceLowestUnused(self, ct=1):
      topIndex = self.lowestUnusedChild + ct
      topIndex = min(topIndex, self.nextChildToCalc)
      topIndex = max(topIndex, 0)

      self.lowestUnusedChild = topIndex
      # TODO - Fix undefined identifiers walletFileSafeUpdate and WLT_UPDATE_MODIFY
      self.walletFileSafeUpdate( [[WLT_UPDATE_MODIFY, self.offsetTopUsed, \
                    int_to_binary(self.lowestUnusedChild, widthBytes=8)]])
      self.fillKeyPool()

   #############################################################################
   def rewindLowestUnused(self, ct=1):
      self.advanceLowestUnused(-ct)


   #############################################################################
   def peekNextUnusedChild(self):
      if self.lowestUnusedChild >= self.nextChildToCalc:
         childAddr = self.spawnChild(self.lowestUnusedChild, \
                                          fsync=False, linkToParent=False)
      else:
         if not self.lowestUnusedChild in self.akpChildByIndex:
            raise ChildDeriveError('Somehow child is missing from map')
         childAddr = self.akpChildByIndex[self.lowestUnusedChild]

      return childAddr

   #############################################################################
   def getNextUnusedChild(self, currBlk=0):
      """
      Use the "currBlk" arg to set the born date for the child, since this func
      is agnostic and doesn't talk to the BDM.
      """
      if self.lowestUnusedChild >= self.nextChildToCalc:
         childAddr = self.spawnChild(self.lowestUnusedChild, fsync=True)
      else:
         childAddr = self.akpChildByIndex[self.lowestUnusedChild]

      childAddr.keyBornTime = long(time.time())
      childAddr.keyBornBlock = currBlk
      childAddr.isUsed = True

      # This is mostly redundant, but makes sure that lowestUnused and nextCalc
      # are updated properly
      self.addAkpChildRef(childAddr)

      # Not sure we need to update self entry... no serialized ata changed
      #self.wltFileRef.addFileOperationToQueue('UpdateEntry', self)
      self.wltFileRef.addFileOperationToQueue('UpdateEntry', childAddr)
      self.wltFileRef.fsyncUpdates()
      self.fillKeyPool()

      return childAddr


   #############################################################################
   def wipePrivateData(self, fsync=True):
      self.sbdPrivKeyData.destroy()
      self.privCryptInfo = NULLCRYPTINFO()
      self.masterEkeyRef = None
      self.masterKdfRef  = None
      self.isWatchOnly   = True

      if fsync:
         self.fsync()



   #############################################################################
   def getParentList(self, fromBaseScrAddr=None):
      """
      If the BIP32 tree looks like:
         SeedRoot --> Wallet --> Chain --> Address(this)
      Then this will return:
         [[SeedRootRef, a], [WalletRef, b], [ChainRef, c]]
      Where a,b,c are the child indices
      """
      if not issubclass(self.__class__, ArmoryBip32ExtendedKey):
         raise TypeError('Cannot get parent list for non-ABEK class object')

      currIndex = self.getChildIndex()
      parentAKP = self.getParent()
      if parentAKP is None:
         return []

      foundBase = False
      revParentList = []
      niter = 0
      while parentAKP is not None:
         revParentList.append([parentAKP, currIndex])
         if parentAKP.getScrAddr() == fromBaseScrAddr or \
            (parentAKP is parentAKP.getParent()):
            foundBase = True
            break
         currIndex = parentAKP.getChildIndex()
         parentAKP = parentAKP.getParent()

         niter += 1
         if niter > 1000:
            raise ValueError('Inf loop detected getting parent list, bailing')

      if fromBaseScrAddr and not foundBase:
         raise ChildDeriveError('Requested up to base par, but not found!')

      return revParentList[::-1]


   #############################################################################
   def pprintVerbose(self, indent=''):
      def returnScrAddr(obj):
         try:
            return binary_to_hex(obj.getScrAddr())
         except:
            ''
      try:
         print indent + '   RootSA  :  ', returnScrAddr(self.root135Ref)
         print indent + '   ParentSA:  ', returnScrAddr(self.getParent())
         print indent + '   SelfSA:    ', returnScrAddr(self)
         print indent + '   ChildIndex:', self.getChildIndex()
         print indent + '   ChainIdx:  ', self.chainIndex
      except:
         print indent + '   ParentSA:  ', returnScrAddr(self.getParent())
         print indent + '   SelfSA:    ', returnScrAddr(self)
         print indent + '   ChildIndex:', self.getChildIndex()

      print indent + '   MarkedUsed:', '+++' if self.isUsed else '   '
      print indent + '   LwestUnuse:', self.lowestUnusedChild
      print indent + '   NxtToCalc: ', self.nextChildToCalc
      print indent + '   AKP Children:  Num=', len(self.akpChildByIndex)
      for idx,ch in self.akpChildByIndex.iteritems():
         print indent + '      %04d    :'%idx, returnScrAddr(ch)

      print '\n'


   ##########################################################################
   def pprintOneLineStr(self, indent=0):
      isUsedStr = '+' if self.isUsed else ' '
      pcs = []
      pcs.append('%s%s' % (self.__class__.__name__.ljust(18), isUsedStr))
      pcs.append(self.getAddrStr() + ',')

      if self.isAkpRootRoot:
         pcs.append('<Top-level BIP32 Node>')
      else:
         if self.getParent():
            if issubclass(self.__class__, Armory135KeyPair):
               idxStr = str(self.chainIndex)
            else:
               idxStr = ChildIndexToStr(self.getChildIndex())
            parAddr = self.getParent().getAddrStr()
            pcs.append('child[%s:%s]' % (parAddr[:12], idxStr))

      if self.privCryptInfo.noEncryption():
         pcs.append('(No Encryption)')
      else:
         pcs.append('(Encrypted with: %s)' % binary_to_hex(self.privCryptInfo.keySource)[:8])

      return ' '*indent + ' '.join(pcs)

   ##########################################################################
   def getPPrintPairs(self):
      pairs = [ ['AddrStr', self.getAddrStr()] ]
      if self.isAkpRootRoot:
         pairs.append(['ParentAKP', '[TOP_LEVEL_BIP32_NODE]'])
         pairs.append(['ChildIndex', ''])
      else:
         if not self.getParent():
            pairs.append(['ParentAKP', '[INVALID_PARENT_REF]'])
            pairs.append(['ChildIndex', '[?]'])
         else:
            if issubclass(self.__class__, ArmoryBip32ExtendedKey):
               idxStr = ChildIndexToStr(self.getChildIndex())
               try:
                  parPairs = ['M']
                  parPairs.extend([ChildIndexToStr(b,'_') for a,b in self.getParentList()])
                  pairs.append(['BIP32Path', '/'.join(parPairs)])
               except:
                  LOGEXCEPT('')
            else:
               idxStr = str(self.chainIndex)

            pairs.append(['ParentAKP', self.getParent().getAddrStr()])
            pairs.append(['ChildIndex', idxStr])

      pairs.append(['CryptInfo', self.privCryptInfo.getPPrintStr()])


      return pairs


   ##########################################################################
   def getBalance(self, utxoMaturity='Spendable'):
      raise NotImplementedError('"%s" needs to implement getBalance()' % \
                                                             self.getName())

   def getUTXOSet(self, utxoMaturity='Spendable', blk0=0, blk1=UINT32_MAX):
      raise NotImplementedError('"%s" needs to implement getUTXOSet()' % \
                                                             self.getName())


   #############################################################################
   def akpBranchQueueFsync(self):
      self.queueFsync()
      for idx,child in self.akpChildByIndex.iteritems():
         child.akpBranchQueueFsync()


   #############################################################################
   def akpBranchFsync(self):
      self.akpBranchQueueFsync()
      self.wltFileRef.fsyncUpdates()


   #############################################################################
   def getAddr160(self):
      return scrAddr_to_hash160(self.getScrAddr())[1]


   #############################################################################
   # This is False until imported addresses are implemented
   # When implemented this method will call isImported for all of its
   # leaf nodes 
   def hasAnyImported(self):
      return False

   #############################################################################
   # This is False until imported addresses are implemented
   # When implemented the extension of this class for imported
   # address will implement this method with return True  
   def isImported(self):
      return False
   
#############################################################################
class ArmorySeededKeyPair(ArmoryKeyPair):
   """
   This is an isolated class which carries a little bit of extra metadata
   needed turn AKP objects into ABEK_Root objects.  Any ABEK_Root class should
   be a derived class of this instead AKP
   """

   #############################################################################
   def __init__(self):
      # Extra data that needs to be encrypted
      super(ArmorySeededKeyPair, self).__init__()
      self.seedCryptInfo  = NULLCRYPTINFO()
      self.seedNumBytes   = 0
      self.sbdSeedData    = SecureBinaryData(0)

      # This root has no key data.  Mainly for JBOK.
      self.isFakeRoot    = False

      # Might be used only to generate deposit addresses, don't show balances
      self.isDepositOnly = False

      # This might be used for, say, backups of phone wallets.  We can hold
      # the key data on this device/computer, watch the funds, refill it, etc.
      # But we don't want to give the ability to move the funds unless the
      # user, loses their phone, and needs to sweep the funds immediately.
      self.isRestricted  = False

      # We make this AKP object its own parent, so that methods which look
      # for all WEs/AKPs with a given parent will also grab the parent itself
      self.wltParentRef  = self
      self.wltParentID   = None


   #############################################################################
   def initializeFromSeed(self, *args, **kwargs):
      raise NotImplementedError('"%s" needs to implement initializeFromSeed()' % \
                                                             self.getName())


   #############################################################################
   def copy(self):
      newAKP = super(ArmorySeededKeyPair, self).copy()
      newAKP.seedCryptInfo = self.seedCryptInfo.copy()
      newAKP.seedNumBytes  = self.seedNumBytes
      newAKP.sbdSeedData   = self.sbdSeedData.copy()
      newAKP.isFakeRoot    = self.isFakeRoot
      newAKP.isDepositOnly = self.isDepositOnly
      newAKP.isRestricted  = self.isRestricted
      newAKP.wltParentRef  = newAKP
      newAKP.wltParentID   = newAKP.getEntryID()
      return newAKP


   #############################################################################
   @EkeyMustBeUnlocked('masterEkeyRef')
   def getPlainSeedCopy(self):
      """
      NOTE:  This returns an SBD object which needs to be .destroy()ed by
             the caller when it is finished with it.
      """
      if self.seedNumBytes==0:
         raise KeyDataError('No seed defined for this root!')

      try:
         aciDecryptAgs = self.getPrivCryptArgs(self.seedCryptInfo)
         paddedSeed = self.seedCryptInfo.decrypt(self.sbdSeedData,
                                                         **aciDecryptAgs)
         return SecureBinaryData(paddedSeed.toBinStr()[:self.seedNumBytes])
      except:
         LOGEXCEPT('Failed to decrypt master seed')
         return NULLSBD()


   #############################################################################
   def wipePrivateData(self, fsync=False):
      self.sbdSeedData.destroy()
      self.seedCryptInfo = NULLCRYPTINFO()
      super(ArmorySeededKeyPair, self).wipePrivateData(fsync)




   #############################################################################
   def createNewSeed(self, seedSize, extraEntropy):
      raise NotImplementedError('"%s" needs to implement createNewSeed()' % \
                                                                 self.getName())


   #############################################################################
   def serializeAKP(self):
      bp = BinaryPacker()

      flags = BitSet(16)
      flags.setBit(0, self.isFakeRoot)
      flags.setBit(1, self.isDepositOnly)
      flags.setBit(2, self.isRestricted)

      bp.put(BINARY_CHUNK, super(ArmorySeededKeyPair, self).serializeAKP())
      bp.put(BITSET,       flags, 2)
      bp.put(UINT16,       self.seedNumBytes)
      bp.put(BINARY_CHUNK, self.seedCryptInfo.serialize(), 32)
      bp.put(VAR_STR,      self.sbdSeedData.toBinStr())
      return bp.getBinaryString()



   #############################################################################
   def unserializeAKP(self, toUnpack):
      bu = makeBinaryUnpacker(toUnpack)
      super(ArmorySeededKeyPair, self).unserializeAKP(bu)
      flags     = bu.get(BITSET, 2)
      seedBytes = bu.get(UINT16)
      cryptInfo = bu.get(BINARY_CHUNK, 32)
      binSeed   = bu.get(VAR_STR)

      self.seedNumBytes  = seedBytes
      self.seedCryptInfo = ArmoryCryptInfo().unserialize(cryptInfo)
      self.sbdSeedData   = SecureBinaryData(binSeed)

      self.isFakeRoot    = flags.getBit(0)
      self.isDepositOnly = flags.getBit(1)
      self.isRestricted  = flags.getBit(2)

      binSeed = None
      return self



################################################################################
################################################################################
#
# Classes for migrating old Armory 1.35 wallets to the wallet2.0 format
#
################################################################################
################################################################################

################################################################################
class Armory135KeyPair(ArmoryKeyPair):

   FILECODE = 'ARMRY135'

   #############################################################################
   def __init__(self, *args, **kwargs):
      """
      We treat Armory 1.35 keys like a strange BIP32 tree.  If the root is "m"
      and this key's chainIndex is 8, we treat it like:

         m/0/0/0/0/0/0/0/0        (8 zeros, each non-hardened derivation)

      By updating the spawnChild method in this class, all the other code that
      is otherwise written for BIP32 works as expected for Armory 1.35 AKPs
      (with a few tweaks, such as not holding the entire derive path)

      CHILD_Index is what is used by Bip32 keys, but always 0 here (as above)
      CHAIN_Index is the old Armory wlt concept, and only tracked by the root

      For Armory135KeyPair objects, we let the base class still manage the
      children and parent references (though there will only ever be one
      child, and it has childIndex=0), and we add logic to have the root track
      all children, recursively (in the root135ChainMap & root135ScrAddrMap)

      """
      super(Armory135KeyPair, self).__init__(*args, **kwargs)

      self.useCompressPub = False
      self.chainIndex = None
      self.childIndex = 0  # always 0 for Armory 135 keys
      self.root135Ref = None
      self.root135ScrAddr = None
      self.maxChildren = 1


   #############################################################################
   def getChildClass(self):
      return Armory135KeyPair

   #############################################################################
   def copy(self):
      newAKP = super(Armory135KeyPair, self).copy()
      newAKP.chainIndex      = self.chainIndex
      newAKP.childIndex      = self.getChildIndex()
      newAKP.root135Ref      = self.root135Ref
      newAKP.root135ScrAddr  = self.root135ScrAddr
      return newAKP

   #############################################################################
   def getAddrObjByPath(self, pathList, privSpawnReqd=False):
      raise NotImplementedError('This method not avail for A135 wallet chains')


   #############################################################################
   def addAkpChildRef(self, childAKP):
      super(Armory135KeyPair, self).addAkpChildRef(childAKP)

      # For Armory135 addrs, we also store the child in root135Ref
      rt = self.root135Ref
      rt.root135ChainMap[childAKP.chainIndex] = childAKP
      rt.root135ScrAddrMap[childAKP.getScrAddr()] = childAKP
      rt.rootNextToCalc = max(childAKP.chainIndex+1, rt.rootNextToCalc)
      if childAKP.isUsed:
         rt.rootLowestUnused = max(rt.rootLowestUnused, childAKP.chainIndex+1)



   #############################################################################
   def spawnChild(self, childIndex=0, privSpawnReqd=False, fsync=True,
                           linkToParent=True, forIDCompute=False, currBlk=0):
      """
      Spawn an Armory135KeyPair from another one.
      """
      if forIDCompute:
         linkToParent=False

      if not childIndex == 0:
         raise KeyDataError('Can only derive child ID=0 for 1.35 AKPs')

      if fsync and self.wltFileRef is None:
         raise IOError('Cannot fsync wallet entry without a valid file ref')

      # If the child key corresponds to a "hardened" derivation, we require
      # the priv keys to be available, or sometimes we explicitly request it
      pavail = self.getPrivKeyAvailability()
      if privSpawnReqd:
         if pavail==PRIV_KEY_AVAIL.WatchOnly:
            raise KeyDataError('Requires priv key, but this is a WO ext key')
         elif pavail==PRIV_KEY_AVAIL.NeedDecrypt:
            raise WalletLockError('Requires priv key, no way to decrypt it')
         elif pavail==PRIV_KEY_AVAIL.NextUnlock:
            self.resolveNextUnlockFlag(fsync)


      # If we are not watch-only but only deriving a pub key, need to set flag
      nextUnlockFlag = False
      if pavail in [PRIV_KEY_AVAIL.NeedDecrypt, PRIV_KEY_AVAIL.NextUnlock]:
         nextUnlockFlag = True


      sbdPlain = NULLSBD()
      sbdPub = CryptoECDSA().UncompressPoint(self.sbdPublicKey33)
      logMult1 = NULLSBD()
      logMult2 = NULLSBD()
      sbdNewKey1 = NULLSBD()
      sbdNewKey2 = NULLSBD()
      sbdNewKey3 = NULLSBD()



      try:
         ecdsaObj = CryptoECDSA()
         if pavail==PRIV_KEY_AVAIL.Available:
            sbdPlain = self.getPlainPrivKeyCopy()
            if sbdPlain.getSize()==0:
               raise KeyDataError('Private key retrieval failed')
            extendFunc = ecdsaObj.ComputeChainedPrivateKey
            extendArgs = [sbdPlain, self.sbdChaincode, sbdPub, logMult1]
            extendType = 'Private'
         else:
            extendFunc = ecdsaObj.ComputeChainedPublicKey
            extendArgs = [sbdPub, self.sbdChaincode, logMult1]
            extendType = 'Public'


         # Do key extension twice
         sbdNewKey1 = extendFunc(*extendArgs)
         sbdNewKey2 = extendFunc(*extendArgs)

         if sbdNewKey1.toBinStr() == sbdNewKey2.toBinStr():
            sbdNewKey2.destroy()
            with open(getMultLogFile(),'a') as f:
               f.write('%s chain (pkh, mult): %s,%s\n' % (extendType,
                  sbdPub.getHash160().toHexStr(), logMult1.toHexStr()))
         else:
            LOGCRIT('Chaining failed!  Computed keys are different!')
            LOGCRIT('Recomputing chained key 3 times; bail if they do not match')
            sbdNewKey1.destroy()
            sbdNewKey2.destroy()
            logMult3 = SecureBinaryData()

            sbdNewKey1 = extendFunc(*extendArgs)
            sbdNewKey2 = extendFunc(*extendArgs)
            sbdNewKey3 = extendFunc(*extendArgs)
            LOGCRIT('   Multiplier1: ' + logMult1.toHexStr())
            LOGCRIT('   Multiplier2: ' + logMult2.toHexStr())
            LOGCRIT('   Multiplier3: ' + logMult3.toHexStr())

            if sbdNewKey1==sbdNewKey2 and sbdNewKey1==sbdNewKey3:
               with open(getMultLogFile(),'a') as f:
                  a160hex = binary_to_hex(hash160(sbdNewKey1.getPublicKey().toBinStr()))
                  f.write('Computed (pkh, mult): %s,%s\n' % (a160hex,logMult1.toHexStr()))
            else:
               raise KeyDataError('Chaining %s Key Failed!' % extendType)

         # Create a new object of the same class as this one, then copy
         # all members and change a few
         childAddr = self.getChildClass()()
         childAddr.copyFromAKP(self)
         childAddr.isUsed = False

         # Assign the above calcs based on the type of calculation
         if extendType=='Private':
            sbdPlain = sbdNewKey1.copy()
            sbdPub  = CryptoECDSA().ComputePublicKey(sbdPlain)
            sbdChain = self.sbdChaincode.copy()
         else:
            sbdPlain = NULLSBD()
            sbdPub  = sbdNewKey1.copy()
            sbdChain = self.sbdChaincode.copy()


         # This sets the priv key (if non-empty)
         childAddr.setPlainKeyData(self.privCryptInfo, sbdPlain, sbdPub, sbdChain)
         childAddr.masterEkeyRef = self.masterEkeyRef
         childAddr.masterKdfRef  = self.masterKdfRef
         childAddr.privKeyNextUnlock = nextUnlockFlag


         if forIDCompute:
            return childAddr


         childAddr.chainIndex = self.chainIndex + 1
         childAddr.childIndex = 0
         childAddr.akpChildByIndex   = {}
         childAddr.akpChildByScrAddr = {}
         childAddr.keyBornTime       = long(time.time())
         childAddr.keyBornBlock      = currBlk
         childAddr.wltParentRef = self.wltParentRef
         childAddr.wltParentID  = self.wltParentID
         childAddr.isAkpRootRoot = False

         # These recompute calls also call recomputeScript and recomputeUniqueIDBin
         childAddr.recomputeScrAddr()
         childAddr.recomputeUniqueIDB58()

         if linkToParent:
            childAddr.root135Ref = self.root135Ref
            childAddr.root135ScrAddr = self.root135ScrAddr
            self.addAkpChildRef(childAddr)

         if fsync:
            childAddr.fsync()

         return childAddr

      finally:
         sbdPlain.destroy()
         sbdNewKey1.destroy()
         sbdNewKey2.destroy()
         sbdNewKey3.destroy()


   #############################################################################
   def recomputeScript(self):
      pkHash160 = hash160(self.getSerializedPubKey())
      self.rawScript = hash160_to_p2pkhash_script(pkHash160)

   #############################################################################
   def recomputeUniqueIDBin(self):
      if self.sbdPublicKey33.getSize() == 0:
         self.uniqueIDBin = None
      else:
         childAKP = self.spawnChild(0, privSpawnReqd=False,
                                    fsync=False, forIDCompute=True)
         child160 = hash160(childAKP.getSerializedPubKey())
         self.uniqueIDBin = (getAddrByte() + child160[:5])[::-1]

   #############################################################################
   def recomputeUniqueIDB58(self):
      self.recomputeUniqueIDBin()
      if self.uniqueIDBin is None:
         self.uniqueIDB58 = None
      else:
         self.uniqueIDB58 = binary_to_base58(self.uniqueIDBin)


   #############################################################################
   def fillKeyPool(self, *args, **kwargs):
      raise KeyDataError('Cannot fill keypool from A135 key pairs')

   #############################################################################
   def getAddrLocatorString(self, locatorType='Plain'):
      bp = BinaryPacker()
      bp.put(BINARY_CHUNK, 'A135', 4)
      bp.put(VAR_STR,      locatorType)
      bp.put(VAR_STR,      self.root135ScrAddr)
      bp.put(UINT32,       self.chainIndex)
      return bp.getBinaryString()

   #############################################################################
   def peekNextUnusedChild(self):
      raise NotImplementedError('Method not appropriate on A135 keypair objs')
   def getNextUnusedChild(self, currBlk=0):
      raise NotImplementedError('Method not appropriate on A135 keypair objs')
   def getNextChangeAddress(self, *args, **kwargs):
      raise NotImplementedError('Method not appropriate on A135 keypair objs')
   def getNextReceivingAddress(self, *args, **kwargs):
      raise NotImplementedError('Method not appropriate on A135 keypair objs')

   #############################################################################
   def serialize(self):
      if self.sbdPublicKey33.getSize()==0:
         raise UninitializedError('Will not serialize uninitialized AKP')

      rootsa = '' if self.root135ScrAddr is None else self.root135ScrAddr
      chain  = INT32_MAX if self.chainIndex is None else self.chainIndex

      bp = BinaryPacker()
      bp.put(BINARY_CHUNK,  self.serializeAKP())  # All ArmoryKeyPair stuff
      bp.put(VAR_STR,       rootsa)
      bp.put(INT32,         chain)
      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, toUnpack):
      bu = makeBinaryUnpacker(toUnpack)
      self.unserializeAKP(bu)
      self.root135ScrAddr = bu.get(VAR_STR)
      self.chainIndex     = bu.get(INT32)

      if len(self.root135ScrAddr)==0:
         self.root135ScrAddr = None

      if self.chainIndex == INT32_MAX:
         self.chainIndex = None

      return self




################################################################################
class Armory135Root(Armory135KeyPair, ArmorySeededKeyPair):
   FILECODE = 'AROOT135'

   #############################################################################
   def __init__(self):
      """
      We treat Armory 1.35 keys like a strange BIP32 tree.  If the root is "m"
      and this key's chainIndex is 8, we treat it like:

         m/0/0/0/0/0/0/0/0        (8 zeros, each non-hardened derivation)

      By updating the spawnChild method in this class, all the other code that
      is otherwise written for BIP32 works as expected for Armory 1.35 AKPs
      (with a few tweaks, such as not holding the entire derive path)
      """
      Armory135KeyPair.__init__(self)
      ArmorySeededKeyPair.__init__(self)

      # In Armory135 wallets, we have a parallel set of maps/vars to track
      # everything at the root.  akpChildBy*, lowestUnused, nextChildToCalc
      # will all still be tracked by the root and each child, but it will
      # be pretty boring.
      self.chainIndex        = -1
      self.root135ChainMap   = {}
      self.root135ScrAddrMap = {}
      self.rootLowestUnused  = 0
      self.rootNextToCalc    = 0
      self.root135Ref        = self
      self.root135ScrAddr    = self.getScrAddr()
      self.isAkpRootRoot     = True


   #############################################################################
   def getChildClass(self):
      return Armory135KeyPair

   #############################################################################
   def copy(self):
      newAKP = super(Armory135Root, self).copy()
      newAKP.root135ChainMap   = self.root135ChainMap.copy()
      newAKP.root135ScrAddrMap = self.root135ScrAddrMap.copy()
      newAKP.rootLowestUnused  = self.rootLowestUnused
      newAKP.rootNextToCalc    = self.rootNextToCalc
      return newAKP

   #############################################################################
   def fillKeyPool(self, fsync=True, Progress=None):
      # For 135 wallets, not actually recursive
      currPool = self.rootNextToCalc - self.rootLowestUnused
      toGen = max(0, self.childPoolSize - currPool)
      LOGINFO('Filling keypool:  topCalc=%d, lowUnuse=%d, pool=%s, toGen=%s' % \
         (self.rootNextToCalc, self.rootLowestUnused, self.childPoolSize, toGen))

      ch = self.getChildByIndex(self.rootNextToCalc-1)
      for i in range(toGen):
         ch = ch.spawnChild(0, privSpawnReqd=False, linkToParent=True, fsync=fsync)

      if fsync:
         self.wltFileRef.fsyncUpdates()


   #############################################################################
   def getChildByIndex(self, index, spawnIfNeeded=False, fsync=True):
      if index==-1:
         return self

      ch = self.root135ChainMap.get(index)
      if ch is None:
         raise ChildDeriveError('Cannot get chain index not yet spawned')
      return ch


   #############################################################################
   def getChildByScrAddr(self, scrAddr):
      ch = self.root135ScrAddrMap.get(scrAddr)
      if ch is None:
         raise ChildDeriveError('Cannot find scrAddr in Armory135 root')
      return ch

   #############################################################################
   @EkeyMustBeUnlocked('masterEkeyRef')
   def getPlainSeedCopy(self):
      """
      NOTE:  This returns an SBD object which needs to be .destroy()ed by
             the caller when it is finished with it.

      There's no real seeds for 135 wallets, there's just a chainIndex=-1
      """
      sbdPriv = self.getPlainPrivKeyCopy()
      testChain = DeriveChaincodeFromRootKey_135(sbdPriv)
      if testChain.toBinStr() == self.sbdChaincode.toBinStr():
         return sbdPriv
      else:
         return SecureBinaryData(sbdPriv.toBinStr() + self.sbdChaincode.toBinStr())

   def getKeys(self):
      return self.root135ScrAddrMap.keys()


   #############################################################################
   @EkeyMustBeUnlocked('masterEkeyRef')
   @VerifyArgTypes(sbdPlainSeed=SecureBinaryData)
   def initializeFromSeed(self, sbdPlainSeed, verifyPub=None, fillPool=True, fsync=True):
      """
      We must already have a master encryption key created, and a reference to
      it set in this object (so that the EkeyMustBeUnlocked decorator passes)

      For 135 "seeds", these aren't really seeds.  They are just the root
      private/public keypair.  But we treat them as a seeds for the purposes
      of making a generic wallet interface that can produce seeds and restore
      wallets from them.
      """
      if sbdPlainSeed.getSize() == 64:
         sbdPriv   = SecureBinaryData(sbdPlainSeed.toBinStr()[:32 ])
         sbdPub    = CryptoECDSA().ComputePublicKey(sbdPriv)
         sbdChain  = SecureBinaryData(sbdPlainSeed.toBinStr()[ 32:])
      elif sbdPlainSeed.getSize() == 32:
         sbdPriv   = sbdPlainSeed.copy()
         sbdPub    = CryptoECDSA().ComputePublicKey(sbdPriv)
         sbdChain  = DeriveChaincodeFromRootKey_135(sbdPriv)

      # Set new priv key with encryption (must be set after pub key)
      self.setPlainKeyData(self.privCryptInfo, sbdPriv, sbdPub, sbdChain)

      # Do verification of pubkey, if requested
      if verifyPub:
         if not self.sbdPublicKey33 == CryptoECDSA().CompressPoint(verifyPub):
            raise KeyDataError('Public key from seed does not match expected')

      self.isWatchOnly     = False
      self.useCompressPub  = False
      self.aekParScrAddr   = None
      self.aekRootScrAddr  = None
      self.akpParentRef    = None
      self.childIndex      = None

      self.recomputeUniqueIDBin()
      self.recomputeUniqueIDB58()
      self.recomputeScript()
      self.recomputeScrAddr()

      if fillPool:
         self.fillKeyPool(fsync=fsync)


   #############################################################################
   def peekNextUnusedChild(self):
      if self.rootLowestUnused == 0:
         return self.spawnChild(fsync=False, linkToParent=False)
      elif self.rootLowestUnused >= self.rootNextToCalc:
         return self.root135ChainMap[self.rootLowestUnused-1].spawnChild( \
                                             fsync=False, linkToParent=False)
      else:
         return self.root135ChainMap[self.rootLowestUnused]


   #############################################################################
   def getNextUnusedChild(self, currBlk=0):

      if self.rootLowestUnused == 0:
         childAddr = self.spawnChild(fsync=True)
      elif self.rootLowestUnused >= self.rootNextToCalc:
         childAddr = self.root135ChainMap[self.rootLowestUnused-1].spawnChild(fsync=True)
      else:
         childAddr = self.root135ChainMap[self.rootLowestUnused]

      childAddr.keyBornTime = long(time.time())
      childAddr.keyBornBlock = currBlk
      childAddr.isUsed = True
      childAddr.getParent().addAkpChildRef(childAddr)
      #self.rootLowestUnused += 1


      # Not sure we need to update self entry... no serialized ata changed
      #self.wltFileRef.addFileOperationToQueue('UpdateEntry', self)
      self.wltFileRef.addFileOperationToQueue('UpdateEntry', childAddr)
      self.fillKeyPool()
      self.wltFileRef.fsyncUpdates()

      return childAddr


   #############################################################################
   # In 135 wallets, there is no difference between change and receiving.
   def getNextChangeAddress(self, *args, **kwargs):
      return self.getNextUnusedChild(*args, **kwargs)
   
   def getNextReceivingAddress(self, *args, **kwargs):
      return self.getNextUnusedChild(*args, **kwargs)

   #############################################################################
   def createNewSeed(self, seedSize, extraEntropy):
      raise NotImplementedError('Creating Armory 1.35 wallets is no more!')


   #############################################################################
   def serializeWatchOnlyData(self):
      raise NotImplementedError('Encoding not implemented yet')

   #############################################################################
   def unserializeWatchOnlyData(self):
      raise NotImplementedError('Encoding not implemented yet')


   #############################################################################
   def pprintVerbose(self, indent=''):
      def returnScrAddr(obj):
         try:
            return binary_to_hex(obj.getScrAddr())
         except:
            ''

      print indent + 'Showing info for:', returnScrAddr(self)
      print indent + '   RootScrAddr', returnScrAddr(self.root135Ref)
      print indent + '   ParentScrA:', returnScrAddr(self.getParent())
      print indent + '   SelfScrAdd:', returnScrAddr(self)
      print indent + '   ChildIndex:', self.getChildIndex()
      print indent + '   ChainIndex:', self.chainIndex
      print indent + '   LwestUnuse:', self.lowestUnusedChild
      print indent + '   NxtToCalc: ', self.nextChildToCalc
      print indent + '   RtLowest:  ', self.rootLowestUnused
      print indent + '   RtNextCa:  ', self.rootNextToCalc
      print indent + '   AKP Children:  Num=', len(self.akpChildByIndex)
      for idx,ch in self.akpChildByIndex.iteritems():
         print indent + '      %d      :'%idx, returnScrAddr(ch)

      print indent + '   Root Children:  Num=', len(self.root135ChainMap)
      for idx,ch in self.root135ChainMap.iteritems():
         print indent + '      %d:      '%idx
         ch.pprintVerbose(indent='          ---')

      print '\n'


################################################################################
################################################################################
#
# Classes for BIP32 Extended Key objects
#
################################################################################
################################################################################

################################################################################
class ArmoryBip32ExtendedKey(ArmoryKeyPair):

   #############################################################################
   def __init__(self, *args, **kwargs):
      super(ArmoryBip32ExtendedKey, self).__init__(*args, **kwargs)
      self.level = 0


   #############################################################################
   def getHDPath(self):
      current = self
      indices = []
      while current and current.getParent() != current \
            and current.getChildIndex() is not None:
         indices.append(ChildIndexToStr(current.getChildIndex()))
         current = current.getParent()
      indices.append('m')
      return '/'.join(indices[::-1])


   #############################################################################
   def getCppExtendedKey(self, needPriv=False):
      if self.getPrivKeyAvailability()==PRIV_KEY_AVAIL.Available:
         privWith00 = SecureBinaryData('\x00' + self.getPlainPrivKeyCopy().toBinStr())
         return Cpp.ExtendedKey(privWith00, self.sbdChaincode)
      else:
         if needPriv:
            raise WalletLockError('Priv EK requested, but priv not avail')
         return Cpp.ExtendedKey(self.sbdPublicKey33, self.sbdChaincode)


   #############################################################################
   def recomputeScript(self):
      pkHash160 = hash160(self.getSerializedPubKey())
      self.rawScript = hash160_to_p2pkhash_script(pkHash160)



   #############################################################################
   def recomputeUniqueIDBin(self):
      self.uniqueIDBin = None
      if self.sbdPublicKey33.getSize() == 0:
         return

      if not self.TREELEAF:
         # Compute the highest possible non-hardened child
         childAKP  = self.spawnChild(0x7fffffff, fsync=False, forIDCompute=True)
         child256  = hash256(childAKP.getScrAddr(True))
         firstByte = binary_to_int(child256[0])
         newFirst  = firstByte ^ binary_to_int(getAddrByte())
         self.uniqueIDBin = int_to_binary(newFirst) + child256[1:6]


   #############################################################################
   def spawnChild(self, childIndex, privSpawnReqd=False, fsync=True,
                           linkToParent=True, forIDCompute=False, currBlk=0):
      """
      Derive a child extended key from this one.

      NOTE:  Var forIDCompute does two things:
                (1) Skips recursively computing the ID of the child
                (2) Allows children outside of the getChildClass() limitations
      """

      if forIDCompute:
         childAddr = ABEK_Generic()
         linkToParent = False
      else:
         childAddr = self.getChildClass(childIndex)()

      childAddr.copyFromAKP(self)
      childAddr.isUsed = False
      childAddr.lowestUnusedChild = 0
      childAddr.nextChildToCalc   = 0
      childAddr.keyBornTime       = long(time.time())
      childAddr.keyBornBlock      = currBlk
      childAddr.isAkpRootRoot     = False

      # If the child key corresponds to a "hardened" derivation, we require
      # the priv keys to be available, or sometimes we explicitly request it
      pavail = self.getPrivKeyAvailability()
      privSpawnReqd = privSpawnReqd or (childIndex & HARDBIT > 0)
      nextUnlockFlag = False
      if privSpawnReqd:
         if pavail==PRIV_KEY_AVAIL.WatchOnly:
            raise KeyDataError('Requires priv key, but this is a WO ext key')
         elif pavail==PRIV_KEY_AVAIL.NeedDecrypt:
            raise WalletLockError('Requires priv key, no way to decrypt it')
         elif pavail==PRIV_KEY_AVAIL.NextUnlock:
            self.resolveNextUnlockFlag(fsync)


      if pavail in [PRIV_KEY_AVAIL.NeedDecrypt, PRIV_KEY_AVAIL.NextUnlock]:
         nextUnlockFlag = True

      def deriveChildAndMult():
         mult = NULLSBD()
         extKey = self.getCppExtendedKey()
         ch = Cpp.HDWalletCrypto().childKeyDeriv(extKey, childIndex, mult)
         extKey.deletePrivateKey()
         return ch,mult

      extend1,mult1 = deriveChildAndMult()
      extend2,mult2 = deriveChildAndMult()

      if extend1.getPublicKey().toHexStr() == extend2.getPublicKey().toHexStr():
         extend2.deletePrivateKey()
         with open(getMultLogFile(),'a') as f:
            a160hex = hash160(extend1.getPublicKey().toHexStr())
            f.write('BIP32 deriv (pkh, mult): %s,%s\n' % (a160hex, mult1.toHexStr()))
      else:
         LOGCRIT('Chaining failed!  Computed keys are different!')
         LOGCRIT('Recomputing chained key 3 times; bail if they do not match')
         extend1,mult1 = deriveChildAndMult()
         extend2,mult2 = deriveChildAndMult()
         extend3,mult3 = deriveChildAndMult()

         LOGCRIT('   Multiplier1: ' + mult1.toHexStr())
         LOGCRIT('   Multiplier2: ' + mult2.toHexStr())
         LOGCRIT('   Multiplier3: ' + mult3.toHexStr())

         if extend1.getPublicKey()==extend2.getPublicKey() and \
            extend1.getPublicKey()==extend3.getPublicKey():
            with open(getMultLogFile(),'a') as f:
               a160hex = binary_to_hex(hash160(extend1.getPublicKey().toBinStr()))
               f.write('Computed (pkh, mult): %s,%s\n' % (a160hex, mult1.toHexStr()))
            extend2.deletePrivateKey()
            extend3.deletePrivateKey()
         else:
            raise KeyDataError('Chaining Bip32 Key Failed!')

      if forIDCompute:
         childAddr.sbdPublicKey33  = extend1.getPublicKey().copy()
         childAddr.sbdChaincode    = extend1.getChaincode().copy()
         return childAddr

      # This sets the priv key (if non-empty)
      childAddr.setPlainKeyData(self.privCryptInfo,
                                extend1.getPrivateKey(False),
                                extend1.getPublicKey(),
                                extend1.getChaincode())

      childAddr.masterEkeyRef = self.masterEkeyRef
      childAddr.masterKdfRef  = self.masterKdfRef
      childAddr.privKeyNextUnlock = nextUnlockFlag

      if not childAddr.sbdPublicKey33.getSize()==33:
         LOGERROR('Pubkey did not come out of HDW code compressed')

      childAddr.childIndex = childIndex
      childAddr.akpChildByIndex   = {}
      childAddr.akpChildByScrAddr = {}
      childAddr.wltParentRef = self.wltParentRef
      childAddr.wltParentID  = self.wltParentID
      childAddr.level = self.level + 1

      # These recompute calls also call recomputeScript and recomputeUniqueIDBin
      childAddr.recomputeScrAddr()
      childAddr.recomputeUniqueIDB58()

      if linkToParent:
         self.addAkpChildRef(childAddr)

      if fsync:
         childAddr.fsync()

      return childAddr


   #############################################################################
   def getAddrLocatorString(self, locatorType='Plain', baseID=None):
      """
      This is a string that can be bundled with offline/multisig transactions
      to help lite devices identify that addresses/keys belong to them.  It's
      basically just a wallet ID and path string.

      Can change the baseID to make the addr locator based on a different
      root, perhaps the depth=1 node instead depth=0

      In the future, we plan to improve privacy of these strings by encrypting
      them with data found in the watching-only wallet (i.e. using chaincodes).
      So that when someone sees M/105/8030 in one transaction and M/105/8085 in
      a separate transaction it won't be so obvious that they are part of the
      same wallet, or owned by one person.  However, this is not a priority,
      since this kind of information leakage really only matters is very
      specific instances that are irrelevant to most users.

      The above paragraph refers to the fact that a multisig/lockbox transaction
      using Armory's USTX format, bundles the address locator strings into it,
      as a way for the online computers to communicate to the offline computers
      what addresses are being used.  But those strings are seen by all MS
      participants even though they are only consumed by one.
      """

      if not locatorType=='Plain':
         raise NotImplementedError('Cannot handle anything other than plain')

      derivePath = self.getParentList(baseID)

      bp = BinaryPacker()
      bp.put(BINARY_CHUNK, 'A2.0', 4)
      bp.put(VAR_STR,      locatorType)
      bp.put(BINARY_CHUNK, baseID)
      bp.put(VAR_INT, len(derivePath))
      for akp,cidx in derivePath:
         bp.put(UINT32, cidx)
      return bp.getBinaryString()


   #############################################################################
   def getFingerprint(self):
      "Return the first 32 bits of the Hash160 of the public key"
      return hash160(self.sbdPublicKey33.toBinStr())[:4]


   #############################################################################
   def getExtendedPubKey(self):
      # specification from:
      # https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki
      xpub = getBIP32MagicPub() + int_to_binary(self.level, 1)
      if self.getParent():
         xpub += self.getParent().getFingerprint()
         if self.childIndex is None:
            xpub += int_to_binary(0, 4, BIGENDIAN)
         else:
            xpub += int_to_binary(self.getChildIndex(), 4, BIGENDIAN)
      else:
         xpub += "\x00" * 8
      xpub += self.sbdChaincode.toBinStr()
      xpub += self.sbdPublicKey33.toBinStr()
      checksum = hash256(xpub)[:4]
      xpub += checksum
      return binary_to_base58(xpub)


   #############################################################################
   def getExtendedPrivKey(self):
      # specification from:
      # https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki
      xprv = getBIP32MagicPrv() + int_to_binary(self.level, 1)
      if self.getParent():
         xprv += self.getParent().getFingerprint()
         if self.childIndex is None:
            xprv += int_to_binary(0, 4, BIGENDIAN)
         else:
            xprv += int_to_binary(self.getChildIndex(), 4, BIGENDIAN)
      else:
         xprv += "\x00" * 8
      xprv += self.sbdChaincode.toBinStr()
      xprv += "\x00" + self.getPlainPrivKeyCopy().toBinStr()
      checksum = hash256(xprv)[:4]
      xprv += checksum

      return binary_to_base58(xprv)


   #############################################################################
   def writeXpubFile(self, path):
      # format is as follows:
      # ID: VAR_STR
      # xpub: 78 bytes
      newFile = open(path, 'wb')
      newFile.write(self.uniqueIDB58 + "\n" + self.getExtendedPubKey())
      return


   #############################################################################
   def writeXprvFile(self, path):
      # format is as follows:
      # ID: VAR_STR
      # xpub: 78 bytes
      newFile = open(path, 'wb')
      newFile.write(self.uniqueIDB58 + "\n" + self.getExtendedPrivKey())
      return

   #############################################################################
   def getSpawnMultiplierForChild(self, childID):
      cnum,hard = SplitChildIndex(childID)
      if hard:
         raise ChildDeriveError('Cannot get multiplier for hardened children')

      sbdMult = NULLSBD()
      extPubKey = Cpp.ExtendedKey(self.sbdPublicKey33, self.sbdChaincode)
      Cpp.HDWalletCrypto().childKeyDeriv(extPubKey, childID, sbdMult)

      if sbdMult.getSize() == 0:
         raise KeyDataError('Multiplier was not set in childKeyDeriv call')

      return sbdMult.toBinStr()


   #############################################################################
   def getMultiplierList(self, fromBaseScrAddr=None):
      parentList = self.getParentList(fromBaseScrAddr)
      if len(parentList) == 0:
         return '',[]
      else:
         topScrAddr = parentList[0].getScrAddr()
         multList = [akp.getSpawnMultiplierForChild(i) for akp,i in parentList]
         return topScrAddr, multList


################################################################################
class ArmoryBip32Seed(ArmoryBip32ExtendedKey, ArmorySeededKeyPair):

   TREELEAF = False

   def getChildClass(self, childIndex):
      return self.__class__

   def __init__(self):
      ArmoryBip32ExtendedKey.__init__(self)
      ArmorySeededKeyPair.__init__(self)
      self.isAkpRootRoot  = True

   #############################################################################
   def copy(self):
      # We actually inherit from two different classes, but the ABEK class
      # doesn't have any special copy method, so we just use ASKP.copy()
      return ArmorySeededKeyPair.copy(self)

   #############################################################################
   @EkeyMustBeUnlocked('masterEkeyRef')
   @VerifyArgTypes(sbdPlainSeed=SecureBinaryData)
   def initializeFromSeed(self, sbdPlainSeed, verifyPub=None, fillPool=True, fsync=True):
      """
      We must already have a master encryption key created, and a reference to
      it set in this object (so the EkeyMustBeUnlocked decorator returns True)
      """

      if sbdPlainSeed.getSize() < 16:
            raise KeyDataError('Extended key seed is not at least 16 bytes.')
      elif sbdPlainSeed.getSize() > 64:
            raise KeyDataError('Extended key seed is more than 64 bytes.')

      # BIP32 only allows seeds up to 64 bytes large. (Range must be 16-64.)
      cppExtKey = Cpp.HDWalletCrypto().convertSeedToMasterKey(sbdPlainSeed)
      self.setPlainKeyData(self.privCryptInfo, cppExtKey.getPrivateKey(False),
                           cppExtKey.getPublicKey(), cppExtKey.getChaincode())

      if verifyPub:
         compressedPub = CryptoECDSA().CompressPoint(verifyPub)
         if self.sbdPublicKey33.toHexStr() != compressedPub.toHexStr():
            raise KeyDataError('Public key from seed does not match expected')


      self.seedCryptInfo = self.privCryptInfo.copy()

      # Normally PUBKEY20 is IV for priv, but need different new IV for the seed
      self.seedCryptInfo.ivSource = SecureBinaryData().GenerateRandom(8).toBinStr()
      self.seedNumBytes = sbdPlainSeed.getSize()
      paddedSize = roundUpMod(self.seedNumBytes, self.seedCryptInfo.getBlockSize())
      paddedSeed = SecureBinaryData(sbdPlainSeed.toBinStr().ljust(paddedSize, '\x00'))
      self.sbdSeedData = self.seedCryptInfo.encrypt(
         paddedSeed, ekeyObj=self.masterEkeyRef, kdfObj=self.masterKdfRef)


      self.isWatchOnly     = False
      self.useCompressPub  = True
      self.aekParScrAddr   = None
      self.aekRootScrAddr  = None
      self.akpParentRef    = None
      self.childIndex      = None

      self.recomputeUniqueIDBin()
      self.recomputeUniqueIDB58()
      self.recomputeScript()
      self.recomputeScrAddr()

      if fillPool:
         self.fillKeyPool(fsync=fsync)


   #############################################################################
   @EkeyMustBeUnlocked('masterEkeyRef')
   @VerifyArgTypes(extraEntropy=SecureBinaryData)
   def createNewSeed(self, seedSize, extraEntropy, fillPool=True, fsync=True):
      """
      This calls initializeFromSeed(), which requires you already set the
      masterEkeyRef object and have it unlocked before calling this function.
      This guarantees that we know how encrypt the new seed.
      """

      if seedSize < 16 and not getTestnetFlag():
         raise KeyDataError('Seed size is not large enough to be secure!')
      elif seedSize > 64:
         raise KeyDataError('Seed size is too large!')

      if extraEntropy.getSize()<16:
         raise KeyDataError('Must provide >= 16B extra entropy for seed gen')

      newSeed = SecureBinaryData().GenerateRandom2xXOR(seedSize, extraEntropy)
      if newSeed.getSize() < seedSize:
         raise KeyDataError('Generation of key material failed!')

      self.initializeFromSeed(newSeed, fillPool=fillPool, fsync=fsync)
      newSeed.destroy()


################################################################################
class ArmoryImportedKeyPair(ArmoryKeyPair):
   FILECODE = 'IMPORTED'
   TREELEAF  = True
   HARDCHILD = True
   def __init__(self, *args, **kwargs):
      super(ArmoryImportedKeyPair, self).__init__(*args, **kwargs)
      self.childIndex = None
      self.maxChildren = 0


   #############################################################################
   @EkeyMustBeUnlocked('masterEkeyRef')
   def signUnsignedTx(self, ustx):
      """
      Signs the unsigned transaction (ustx) with the private key associated
      with this keypair.
      """
      pytx = ustx.pytxObj
      signed = 0

      for ustxi in ustx.ustxInputs:
         for scrAddr in ustxi.scrAddrs:
            if self.scrAddrStr != scrAddr:
               continue
            LOGINFO("signing with %s" % self.getAddrStr())
            privKey = self.getPlainPrivKeyCopy()
            ustxi.createAndInsertSignature(pytx, privKey)
            signed += 1
            privKey.destroy()
      LOGINFO("Signed transaction %s times" % signed)
      return ustx

   #############################################################################
   @VerifyArgTypes(pubkey=SecureBinaryData)
   def initializeFromPubKey(self, pubkey):
      """
      Initializes this key pair with the public key (pubkey). This means
      that the keypair is used mainly for watching transactions and signature
      verification.
      """
      self.isWatchOnly     = True
      self.isAkpRootRoot   = True
      self.privCryptInfo   = NULLCRYPTINFO()
      self.sbdPrivKeyData  = NULLSBD()
      self.sbdChaincode    = None
      self.privKeyNextUnlock = False
      self.childIndex      = 0
      self.useCompressPub  = True
      self.isUsed          = True
      self.notForDirectUse = False
      self.keyBornTime     = 0
      self.keyBornBlock    = 0
      self.level           = 0

      if pubkey.getSize() == 65:
         self.sbdPublicKey33 = CryptoECDSA().CompressPoint(pubkey)
      else:
         self.sbdPublicKey33 = pubkey.copy()

      self.recomputeScript()
      self.recomputeScrAddr()
      self.recomputeUniqueIDBin()
      self.recomputeUniqueIDB58()

      self.akpParScrAddr = self.getScrAddr()
      self.akpParentRef  = self


   #############################################################################
   @VerifyArgTypes(privkey=SecureBinaryData)
   def initializeFromPrivKey(self, privkey):
      """
      Initializes this key pair with the private key (privkey). The key can be
      used for signing transactions and messages.
      """
      self.isWatchOnly     = False
      self.isAkpRootRoot   = True
      self.privCryptInfo   = NULLCRYPTINFO()
      self.sbdChaincode    = None
      self.privKeyNextUnlock = False
      self.childIndex      = 0
      self.useCompressPub  = True
      self.isUsed          = True
      self.notForDirectUse = False
      self.keyBornTime     = 0
      self.keyBornBlock    = 0
      self.level           = 0

      self.sbdPrivKeyData  = privkey.copy()
      self.sbdPublicKey33  = CryptoECDSA().CompressPoint(
         CryptoECDSA().ComputePublicKey(privkey))

      self.recomputeScript()
      self.recomputeScrAddr()
      self.recomputeUniqueIDBin()
      self.recomputeUniqueIDB58()

      self.akpParScrAddr = self.getScrAddr()
      self.akpParentRef  = self

   #############################################################################
   def getAddrLocatorString(self):
      return ''

   #############################################################################
   def fillKeyPool(self, *args, **kwargs):
      pass

   #############################################################################
   def recomputeUniqueIDBin(self):
      self.uniqueIDBin = ''

   #############################################################################
   def recomputeScript(self):
      pkHash160 = hash160(self.getSerializedPubKey())
      self.rawScript = hash160_to_p2pkhash_script(pkHash160)

   #############################################################################
   def getChildClass(self, index):
      raise NotImplementedError('Cannot spawn imported keys')

   #############################################################################
   def getNextUnusedChild(self, index):
      raise NotImplementedError('Cannot spawn imported keys')

   #############################################################################
   def spawnChild(self, childIndex, privSpawnReqd=False, fsync=True, forIDCompute=False):
      raise NotImplementedError('Cannot spawn imported keys')


################################################################################
################################################################################
class ArmoryImportedRoot(ArmoryImportedKeyPair):
   """
   This class is pretty boring.  Looks a lot like a regular keypair, but has
   no spawning, or even chaincodes.  Just a priv-pub keypair.  For the roots,
   these are fake roots meaning that they don't do anything.  We randomly
   create a keypair for the fake root, so that the normal mechanisms for
   calculating wallet ID, scrAddr, etc, will work, we just don't ever intend
   to use the root for anything other than using it as a hub for imported
   keys
   """
   FILECODE = 'IMPORTRT'
   TREELEAF  = True
   HARDCHILD = True
   def __init__(self):
      super(ArmoryImportedRoot, self).__init__()
      self.isFakeRoot = True
      self.isAkpRootRoot = True
      self.childIndex = None
      self.maxChildren = 0
      self.privCryptInfo = NULLCRYPTINFO()
      self.masterEkeyRef = None
      self.masterKdfRef = None


   #############################################################################
   def recomputeUniqueIDBin(self):
      self.uniqueIDBin = hash256(self.getSerializedPubKey())[:6]

   #############################################################################
   def createNewRoot(self, pregenRoot=None, currBlk=0):
      """
      Encryption is irrelevant.  This is fake, unused data.  We will leave it
      unencrypted even if the wallet has encryption
      """
      if pregenRoot is None:
         pregenRoot = SecureBinaryData('\x00'*32)

      timeCreated = long(time.time())
      aci = NULLCRYPTINFO()
      priv = pregenRoot.copy()
      pubk = CryptoECDSA().ComputePublicKey(priv)
      chain = NULLSBD()
      self.initializeAKP(isWatchOnly=False,
                         isAkpRootRoot=True,
                         privCryptInfo=aci,
                         sbdPrivKeyData=priv,
                         sbdPublicKey33=pubk,
                         sbdChaincode=chain,
                         privKeyNextUnlock=False,
                         akpParScrAddr=None,
                         childIndex=None,
                         level=0,
                         useCompressPub=True,
                         isUsed=True,
                         notForDirectUse=False,
                         keyBornTime=timeCreated,
                         keyBornBlock=currBlk)


   #############################################################################
   def addAkpChildRef(self, childAIKP):
      childScrAddr = childAIKP.getScrAddr()
      if not childScrAddr in self.akpChildByScrAddr:
         cidx = len(self.akpChildByIndex)
         self.akpChildByIndex[cidx] = childAIKP
         self.akpChildByScrAddr[childScrAddr] = childAIKP
         childAIKP.akpParentRef  = self
         childAIKP.akpParScrAddr = self.getScrAddr()
         childAIKP.wltParentRef  = self.wltParentRef
         childAIKP.wltParentID   = self.wltParentID


   #############################################################################
   def getChildClass(self, index):
      raise NotImplementedError('Cannot spawn imported keys')

   #############################################################################
   def getNextUnusedChild(self, index):
      raise NotImplementedError('Cannot spawn imported keys')

   #############################################################################
   def spawnChild(self, childIndex, privSpawnReqd=False, fsync=True, forIDCompute=False):
      raise NotImplementedError('Cannot spawn imported keys')





#############################################################################
class ABEK_BIP44Seed(ArmoryBip32Seed):
   FILECODE = 'BIP44SED'
   TREELEAF  = False
   HARDCHILD = True

   def __init__(self):
      super(ABEK_BIP44Seed, self).__init__()
      self.isAkpRootRoot = True

   #############################################################################
   def getChildClass(self, index):
      if index==CreateChildIndex(44, True):
         return ABEK_BIP44Purpose

      raise ChildDeriveError('Invalid child %s for %s' % \
                              (ChildIndexToStr(index), self.getName()))

   #############################################################################
   def fillKeyPool(self, fsync=True, Progress=emptyFunc):
      """
      ### DEFAULT implementation of fillKeyPool in AKP base class ###
      if self.sbdPublicKey33 is None or self.sbdPublicKey33.getSize()==0:
         raise UninitializedError('AKP object not init, cannot fill pool')

      if self.TREELEAF:
         return

      keysToGen = self.numKeysNeededToFillPool()
      for i in range(keysToGen):
         newAkp = self.spawnChild(self.getNextChildToCalcIndex(), fsync=fsync,
                                                               linkToParent=True)

      # Now recurse to each child
      for scrAddr,childAKP in self.akpChildByScrAddr.iteritems():
         childAKP.fillKeyPool(fsync=fsync, Progress=Progress)
      ### DEFAULT implementation of fillKeyPool in AKP base class
      """
      if self.sbdPublicKey33 is None or self.sbdPublicKey33.getSize()==0:
         raise UninitializedError('AKP object not init, cannot fill pool')

      bip44Index = CreateChildIndex(44, isHardened=True)
      newAkp = self.spawnChild(bip44Index, fsync=fsync, linkToParent=True)
      newAkp.fillKeyPool(fsync=fsync, Progress=Progress)


   ##########################################################################
   def getAllWallets(self):
      """
      Retreive all ABEK_StdWallet descendants related
      to the current network from this seed
      """
      # go down to the ABEK_BIP44Purpose level "purpose"
      purpose = self.getChildByIndex(CreateChildIndex(44, isHardened=True))

      # go down to the ABEK_StdBip32Seed level "cointype"
      index = 1 if getTestnetFlag() else 0
      cointype = purpose.getChildByIndex(
            CreateChildIndex(index, isHardened=True))

      wallets = []
      # go down to the ABEK_StdWallet level "account"
      for wallet in cointype.akpChildByIndex.values():
         wallets.append(wallet)

      return wallets


   ##########################################################################
   def createNewWallet(self, name, description):
      """
      Create a ABEK_StdWallet descendant
      """
      # go down to the ABEK_BIP44Purpose level "purpose"
      purpose = self.getChildByIndex(CreateChildIndex(44, isHardened=True))

      # go down to the ABEK_StdBip32Seed level "cointype"
      index = 1 if getTestnetFlag() else 0
      cointype = purpose.getChildByIndex(CreateChildIndex(index, isHardened=True))

      index = cointype.getNextChildToCalcIndex()
      wallet = cointype.spawnChild(index)
      cointype.queueFsync()
      wallet.setLabel(name)
      wallet.setDescription(description)
      wallet.fillKeyPool(fsync=True)
      return wallet


#############################################################################
class ABEK_BIP44Purpose(ArmoryBip32ExtendedKey):
   FILECODE = 'BIP44PUR'
   TREELEAF  = False
   HARDCHILD = True

   def __init__(self):
      super(ABEK_BIP44Purpose, self).__init__()

   def getChildClass(self, index):
      idx,hard = SplitChildIndex(index)
      expectedIdx = 1 if getTestnetFlag() else 0
      if idx==expectedIdx and hard==self.HARDCHILD:
         return ABEK_StdBip32Seed

      raise ChildDeriveError('Invalid child %s for %s' % \
                              (ChildIndexToStr(index), self.getName()))


   #############################################################################
   def fillKeyPool(self, fsync=True, Progress=emptyFunc):
      if self.sbdPublicKey33 is None or self.sbdPublicKey33.getSize()==0:
         raise UninitializedError('AKP object not init, cannot fill pool')

      networkInt = 1 if getTestnetFlag() else 0
      indexToUse = CreateChildIndex(networkInt, isHardened=True)
      newAkp = self.spawnChild(indexToUse, fsync=fsync, linkToParent=True)
      newAkp.fillKeyPool(fsync=fsync, Progress=Progress)



#############################################################################
class ABEK_StdBip32Seed(ArmoryBip32Seed):
   FILECODE = 'BIP32SED'
   TREELEAF  = False
   HARDCHILD = True

   def __init__(self):
      super(ABEK_StdBip32Seed, self).__init__()
      self.childPoolSize = 1

   #############################################################################
   def getChildClass(self, index):
      idx,hard = SplitChildIndex(index)
      if hard==self.HARDCHILD:
         return ABEK_StdWallet

      raise ChildDeriveError('Invalid child %s for %s' % \
                              (ChildIndexToStr(index), self.getName()))


#############################################################################
class ABEK_SoftBip32Seed(ABEK_StdBip32Seed):
   FILECODE = 'SFT32SED'
   TREELEAF  = False
   HARDCHILD = False



#############################################################################
class ABEK_StdWallet(ArmoryBip32ExtendedKey):
   FILECODE  = 'STD32WLT'
   TREELEAF  = False
   HARDCHILD = False


   def __init__(self):
      super(ABEK_StdWallet, self).__init__()

      self.maxChildren = 2

      # Most AKP/ABEK objects just have a "AddrLabel" associated with them.
      # For wallets, we need to have a name that is embedded in the entry
      # that will be transferred when moved, copied, etc.  We can include
      # additional (unrestricted) information by also attaching an AddrLabel
      # to this object.
      self.walletName = u''

      # This will identify what app created this root, perhaps it's imported
      # from a Trezor, or it's from another Armory instance.  This is really
      # just informational, probably not going to be used for code branching (?)
      self.rootSourceApp   = u''

      # If the user decided to "remove" this wallet, then we simply mark it as
      # "removed" and don't display it or do anything with it.
      self.userRemoved = False

      self.version = ARMORY_WALLET_VERSION
      self.actionsToTakeAfterScan = []

      self.external = None
      self.internal = None

   #############################################################################
   def initializeFromXpub(self, xpub):
      """
      Initialize a watch-only wallet from just the xpub
      """
      xpubData = parseBip32KeyData(xpub)
      self.isWatchOnly     = True
      self.isAkpRootRoot   = True
      self.privCryptInfo   = NULLCRYPTINFO()
      self.sbdPrivKeyData  = NULLSBD()
      self.sbdPublicKey33  = SecureBinaryData(xpubData['keyData'])
      self.sbdChaincode    = SecureBinaryData(xpubData['chaincode'])
      self.privKeyNextUnlock = False
      self.childIndex      = xpubData['childIndex']
      self.useCompressPub  = True
      self.isUsed          = True
      self.notForDirectUse = False
      self.keyBornTime     = 0
      self.keyBornBlock    = 0
      self.level           = xpubData['childDepth']

      self.recomputeScript()
      self.recomputeScrAddr()
      self.recomputeUniqueIDBin()
      self.recomputeUniqueIDB58()

      # we don't know the parent, but fill parent in as if it is its own parent
      self.akpParScrAddr = self.getScrAddr()
      self.akpParentRef  = self


   #############################################################################
   def initializeFromXprv(self, xprv):
      """
      Initialize the full-functioning wallet from just the xprv
      """
      pass

   #############################################################################
   def initializeChildren(self):
      # per the BIP44 spec, 0 is for the external child
      # and 1 is for the internal child (aka change addresses)
      self.external = self.getChildByIndex(0, spawnIfNeeded=True, fsync=True)
      self.internal = self.getChildByIndex(1, spawnIfNeeded=True, fsync=True)


   #############################################################################
   def fillKeyPool(self, fsync=True, Progress=emptyFunc):
      # per the BIP44 spec, 0 is for the external child
      # and 1 is for the internal child (aka change addresses)
      self.external = self.spawnChild(0, fsync=fsync, linkToParent=True)
      self.internal = self.spawnChild(1, fsync=fsync, linkToParent=True)

      self.external.fillKeyPool(fsync=fsync, Progress=Progress)
      self.internal.fillKeyPool(fsync=fsync, Progress=Progress)


   #############################################################################
   def serialize(self):
      bp = BinaryPacker()

      flags = BitSet(16)
      flags.setBit(0, self.userRemoved)

      bp.put(BINARY_CHUNK, self.serializeAKP())
      bp.put(BITSET,       flags, 2)
      bp.put(VAR_UNICODE,  self.rootSourceApp)
      bp.put(VAR_UNICODE,  self.walletName)
      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, toUnpack):
      bu = makeBinaryUnpacker(toUnpack)
      self.unserializeAKP(bu)
      flags   = bu.get(BITSET, 2)
      rootSrc = bu.get(VAR_UNICODE)
      wltName = bu.get(VAR_UNICODE)


      self.userRemoved   = flags.getBit(0)
      self.rootSourceApp = rootSrc
      self.walletName    = wltName
      return self


   #############################################################################
   def getChildClass(self, index):
      cnum,ishard = SplitChildIndex(index)
      if ishard==self.HARDCHILD and cnum==0:
         return ABEK_StdChainExt
      elif ishard==self.HARDCHILD and cnum==1:
         return ABEK_StdChainInt

      raise ChildDeriveError('Invalid child %s for %s' % \
                              (ChildIndexToStr(index), self.getName()))

   def isUninitialized(self):
      return self.external is None

   #############################################################################
   def getNextReceivingAddress(self, fsync=True):
      if self.isUninitialized():
         self.initializeChildren()
      return self.external.getNextUnusedChild()

   #############################################################################
   def peekNextReceivingAddress(self):
      if self.isUninitialized():
         self.initializeChildren()
      return self.external.peekNextUnusedChild()

   #############################################################################
   def getNextChangeAddress(self, fsync=True):
      if self.isUninitialized():
         self.initializeChildren()
      return self.internal.getNextUnusedChild()

   #############################################################################
   def peekNextChangeAddress(self):
      if self.isUninitialized():
         self.initializeChildren()
      return self.internal.peekNextUnusedChild()

   #############################################################################
   def getKeys(self):
      if self.isUninitialized():
         self.initializeChildren()
      return self.external.akpChildByScrAddr.keys() \
         + self.internal.akpChildByScrAddr.keys()

   #############################################################################
   def getAddress(self, scrAddr):
      # find this address and send back the grandchild
      if self.isUninitialized():
         self.initializeChildren()
      return self.external.akpChildByScrAddr.get(scrAddr) \
         or self.internal.akpChildByScrAddr.get(scrAddr)

   #############################################################################
   def getChangeAddress(self, scrAddr):
      # find this address and send back the grandchild
      if self.isUninitialized():
         self.initializeChildren()
      return self.internal.akpChildByScrAddr.get(scrAddr)

   #############################################################################
   def hasScrAddress(self, scrAddr):
      return self.getAddress(scrAddr) is not None

   #############################################################################
   def hasAddr(self, addr160):
      if self.isUninitialized():
         return False
      # find the balance in the grandchild
      return self.external.hasAddr(addr160) or self.internal.hasAddr(addr160)

   #############################################################################
   def getLedgerEntryForTx(self, binhash):
      return self.cppWallet.getLedgerEntryForTx(binhash)

   #############################################################################
   def getUTXOListForSpendVal(self, valToSpend):
      """ Returns UnspentTxOut/C++ objects
      returns a set of unspent TxOuts to cover for the value to spend
      """
      return self.cppWallet.getSpendableTxOutListForValue(valToSpend, getIgnoreZCFlag())

   #############################################################################
   def getTxLedger(self, ledgType='Full'):
      """
      Gets the ledger entries for the entire wallet, from C++/SWIG data structs
      """
      if self.isUninitialized():
         self.initializeChildren()

      return self.getHistoryPage(0)

   #############################################################################
   def getAddrTotalTxnCount(self, a160):
      return self.cppWallet.getAddrTotalTxnCount(a160)

   #############################################################################
   def getComment(self, txhash):
      return self.getTxComment(txhash)

   #############################################################################
   def getCommentForLE(self, le):
      return self.getTxComment(le.getTxHash())

   #############################################################################
   def getFullUTXOList(self):
      return self.cppWallet.getSpendableTxOutListForValue(getIgnoreZCFlag())

   #############################################################################
   def unregisterWallet(self):
      getBDM().unregisterWallet(self.uniqueIDB58)
      self.cppWallet = None

   #############################################################################
   def importExternalAddressData(self, privKey, keyType):
      keyPair = ArmoryImportedKeyPair()
      keyPair.copyFromWE(self)
      keyPair.masterEkeyRef = self.masterEkeyRef
      keyPair.sbdPrivKeyData = privKey
      pubKey65 = CryptoECDSA().ComputePublicKey(privKey)
      keyPair.sbdPublicKey33 = CryptoECDSA().CompressPoint(pubKey65)
      keyPair.recomputeScript()
      keyPair.recomputeScrAddr()
      scrAddr = keyPair.scrAddrStr
      if scrAddr in self.wltFileRef.masterScrAddrMap:
         raise RuntimeError("address already in wallet")
      self.wltFileRef.addEntriesToWallet([keyPair])
      return keyPair.getAddrStr()

   #############################################################################
   def getNumAddrs(self):
      if self.isUninitialized():
         self.initializeChildren()
      return self.external.nextChildToCalc + self.internal.nextChildToCalc

   #############################################################################
   def getNumUsed(self):
      return len([addr.isUsed for addr in self.getLinearAddrList()])

   #############################################################################
   def getNumUnused(self):
      return self.getNumAddrs() - self.getNumUsed()

   #############################################################################
   def getLinearAddrList(self, withImported=True, withAddrPool=False):
      if self.isUninitialized():
         self.initializeChildren()
      addrList = []
      for i in range(self.external.nextChildToCalc):
         addrList.append(self.external.getChildByIndex(i))
      for i in range(self.internal.nextChildToCalc):
         addrList.append(self.internal.getChildByIndex(i))

      # TODO: add imported
      return addrList

   #############################################################################
   def getBalance(self, utxoMaturity='spendable'):
      if self.cppWallet != None and getBDM().getState() is BDM_BLOCKCHAIN_READY:
         topBlockHeight = getBDM().getTopBlockHeight()
         if utxoMaturity.lower() in ('spendable','spend'):
            return self.cppWallet.getSpendableBalance(topBlockHeight, getIgnoreZCFlag())
         elif utxoMaturity.lower() in ('unconfirmed','unconf'):
            return self.cppWallet.getUnconfirmedBalance(topBlockHeight, getIgnoreZCFlag())
         elif utxoMaturity.lower() in ('total','ultimate','unspent','full'):
            return self.cppWallet.getFullBalance()
         else:
            raise TypeError('Unknown balance type! "' + utxoMaturity + '"')
      else:
         return 0

   #############################################################################
   def getAddrBalance(self, addr160, balType="Spendable", topBlockHeight=UINT32_MAX):
      scrAddr = hash160_to_scrAddr(addr160)
      # make sure the address is in this branch
      if not self.hasAddr(addr160):
         raise BadAddressError("address %s not found in wallet" % addr160)

      addr = self.cppWallet.getScrAddrObjByKey(scrAddr)
      if balType.lower() in ('spendable','spend'):
         return addr.getSpendableBalance(topBlockHeight, getIgnoreZCFlag())
      elif balType.lower() in ('unconfirmed','unconf'):
         return addr.getUnconfirmedBalance(topBlockHeight, getIgnoreZCFlag())
      elif balType.lower() in ('ultimate','unspent','full'):
         return addr.getFullBalance()
      else:
         raise TypeError('Unknown balance type!')

   #############################################################################
   def getHistoryPage(self, pageID):
      return self.cppWallet.getHistoryPageAsVector(pageID)

   #############################################################################
   def getHistoryPageCount(self):
      return self.cppWallet.getHistoryPageCount()

   #############################################################################
   @EkeyMustBeUnlocked('masterEkeyRef')
   def signUnsignedTx(self, ustx):
      """
      Signs the unsigned transaction (ustx) with the private key associated with
      this keypair.
      """
      pytx = ustx.pytxObj
      signed = 0

      for ustxi in ustx.ustxInputs:
         for scrAddr in ustxi.scrAddrs:
            addrObj = self.getAddress(scrAddr)
            if not addrObj:
               continue
            LOGINFO("signing with %s" % addrObj.getAddrStr())
            privKey = addrObj.getPlainPrivKeyCopy()
            ustxi.createAndInsertSignature(pytx, privKey)
            signed += 1
            privKey.destroy()
      LOGINFO("Signed transaction %s times" % signed)
      return ustx

   #############################################################################
   def getCppAddr(self, addr160):
      return self.cppWallet.getScrAddrObjByKey(hash160_to_scrAddr(addr160))

   #############################################################################
   def isWltSigningAnyLockbox(self, lockboxList):
      for lockbox in lockboxList:
         for addr160 in lockbox.a160List:
            if self.hasAddr(addr160):
               return True
      return False

   #############################################################################
   def addAddresses(self, numAddrs, Progress=emptyFunc):
      # add numAddrs addresses to both external and internal pool
      if self.isUninitialized():
         self.initializeChildren()
      self.external.childPoolSize += numAddrs
      self.internal.childPoolSize += numAddrs
      self.external.fillKeyPool(Progress=Progress)
      self.internal.fillKeyPool(Progress=Progress)

      newAddrList = [self.external.akpChildByIndex[i].getScrAddr()
                     for i in range(self.external.nextChildToCalc - numAddrs,
                                    self.external.nextChildToCalc)]
      newAddrList.extend(
         [self.external.akpChildByIndex[i].getScrAddr()
          for i in range(self.external.nextChildToCalc - numAddrs,
                         self.external.nextChildToCalc)])

      wltNAddr = {}
      wltNAddr[self.uniqueIDB58] = newAddrList
      getBDM().bdv().registerAddressBatch(wltNAddr, True)

      return

   #############################################################################
   def doAfterScan(self):
      actionsList = self.actionsToTakeAfterScan
      self.actionsToTakeAfterScan = []      
      
      for calls in actionsList:
         calls[0](*calls[1])


#############################################################################
class ABEK_StdChainInt(ArmoryBip32ExtendedKey):
   FILECODE = 'STD32CIN'

   TREELEAF  = False
   HARDCHILD = False

   #############################################################################
   def __init__(self):
      super(ABEK_StdChainInt, self).__init__()
      self.maxChildren = UINT32_MAX

   #############################################################################
   def getChildClass(self, index):
      cnum,ishard = SplitChildIndex(index)
      if ishard==self.HARDCHILD:
         return ABEK_StdLeaf

      raise ChildDeriveError('Invalid child %s for %s' % \
                              (ChildIndexToStr(index), self.getName()))
      
   #############################################################################
   def hasAddr(self, addr160):
      scrAddr = hash160_to_scrAddr(addr160)
      return scrAddr in self.akpChildByScrAddr.keys()

#############################################################################
class ABEK_StdChainExt(ArmoryBip32ExtendedKey):
   FILECODE = 'STD32CEX'
   TREELEAF  = False
   HARDCHILD = False

   #############################################################################
   def __init__(self):
      super(ABEK_StdChainExt, self).__init__()
      self.maxChildren = UINT32_MAX


   #############################################################################
   def getChildClass(self, index):
      cnum,ishard = SplitChildIndex(index)
      if ishard==self.HARDCHILD:
         return ABEK_StdLeaf

      raise ChildDeriveError('Invalid child %s for %s' %
                             (ChildIndexToStr(index), self.getName()))

      
   #############################################################################
   def hasAddr(self, addr160):
      scrAddr = hash160_to_scrAddr(addr160)
      return scrAddr in self.akpChildByScrAddr.keys()
   
#############################################################################
class ABEK_StdLeaf(ArmoryBip32ExtendedKey):
   FILECODE = 'STD32LEF'
   TREELEAF  = True
   HARDCHILD = False

   #############################################################################
   def __init__(self):
      super(ABEK_StdLeaf, self).__init__()
      self.maxChildren = 0

   #############################################################################
   def getChildClass(self, index):
      raise ChildDeriveError('Cannot derive child from leaf')

   #############################################################################
   def isChange(self):
      # Change is on the 1 branch, addresses for receiving external bitcoins are
      # are on the 0 branch
      return self.getParent().getChildIndex() == 1


#############################################################################
# ?BEK_Generic classes are for the occasional times that we just need a
# generic BIP32 node for various calculations and don't want arbitrary
# limitations on child spawning (mostly during testing)
class ABEK_Generic(ArmoryBip32ExtendedKey):
   FILECODE = 'AGENERIC'
   TREELEAF  = False
   HARDCHILD = False

   def __init__(self):
      super(ABEK_Generic, self).__init__()
      self.maxChildren = UINT32_MAX

   def getChildClass(self, index):
      # No restrictions on spawn class (non-hardened is default, though)
      return ABEK_Generic


from BDM import getBDM, BDM_BLOCKCHAIN_READY
