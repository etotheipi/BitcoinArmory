import inspect
import os
import shutil
import threading

from ArmoryUtils import *

from ArbitraryWalletData import Infinimap
from ArmoryEncryption import ArmoryCryptInfo, EncryptionKey, KdfObject, \
   MultiPwdEncryptionKey
from ArmoryKeyPair import ABEK_BIP44Seed, ABEK_StdWallet, \
   Armory135Root, ArmoryImportedRoot, ArmorySeededKeyPair, ArmoryKeyPair
from BinaryPacker import BinaryPacker, BinaryUnpacker, makeBinaryUnpacker
from BitSet import BitSet
from Decorators import VerifyArgTypes
from WalletEntry import WalletEntry


         
################################################################################
def _CheckFsyncArgument(func):
   """
   This applies a default fsync argument based on whether the wallet was opened
   in read-only.  It also throws an error if the caller attempted to call with
   fsync=True on a wallet in RO mode.
   """

   aspec = inspect.getargspec(func)

   def wrappedFunc(*args, **kwargs):
      self = args[0]
      if not 'fsync' in kwargs:
         kwargs['fsync'] = not self.isReadOnly
      elif kwargs['fsync'] is True and self.isReadOnly:
         raise WalletUpdateError('Attempted to use fsync arg on readonly wallet')
      
      func(*args, **kwargs)

   return wrappedFunc



################################################################################
################################################################################
class ArmoryFileHeader(object):
  
   WALLETMAGIC = '\xffARMORY\xff'
   DEFAULTSIZE = 200

   #############################################################################
   def __init__(self):
      # Note, we use a different fileID than wallet 1.35 so that older versions
      # of Armory don't attempt to load the 2.0 wallets
      self.flags         = BitSet(32)
      self.wltUserName   = u''
      self.createTime    = UINT64_MAX
      self.createBlock   = UINT32_MAX
      self.rsecParity    = ERRCORR_BYTES
      self.rsecPerData   = ERRCORR_PER_DATA
      self.isDisabled    = False
      self.headerSize    = self.DEFAULTSIZE

      # This file may actually be used for a variety of wallet-related 
      # things -- such as transferring observer chains, exchanging linked-
      # wallet info, containing just comments/labels/P2SH script -- but 
      # not actually be used as a loadable wallet.
      self.isTransferWallet = False
      self.isSupplemental = False

      # This helps with generic logic that needs to know where in the wallet
      # file this object resides
      self.wltByteLoc = 0

   
   #############################################################################
   def initialize(self, wltName, timeCreate=0, blkCreate=0, flags=None):
      if isinstance(wltName, str):
         LOGWARN('Name argument supplied as plain str, converting to unicode')

      self.__init__()
      self.flags = flags if flags else BitSet.CreateFromInteger(0, numBits=32)
      self.wltUserName = toUnicode(wltName)
      self.createTime = timeCreate
      self.createBlock = blkCreate

      self.isTransferWallet = self.flags.getBit(0)
      self.isSupplemental   = self.flags.getBit(1)

      if self.isTransferWallet or self.isSupplemental:
         raise UnserializeError('Transfer/supplemental wallets not supported!')


   #############################################################################
   def serialize(self, altName=None):
      """
      We leave a lot of extra space in header for future expansion, since
      header data is always up front, it's always got to be the same size.

      We hardcode RSEC sizes here, because we can't have the RSEC size vars
      protected by an RSEC code specified by that size (circular reference).
      So we use a blanket 16 bytes of parity for 1024 bytes of data.
      """
      self.flags.reset()
      self.flags.setBit(0, self.isTransferWallet)
      self.flags.setBit(1, self.isSupplemental)


      wltNameTruncPad = toBytes(unicode_truncate(self.wltUserName, 64))
      if altName:
         wltNameTruncPad = toBytes(unicode_truncate(altName, 64))
      

      hdataMid = BinaryPacker()
      hdataMid.put(UINT32,          getVersionInt(ARMORY_WALLET_VERSION))
      hdataMid.put(BINARY_CHUNK,    getMagicBytes(),                 width=4)
      hdataMid.put(BITSET,          self.flags,                  width=4)
      hdataMid.put(UINT8,           len(wltNameTruncPad))
      hdataMid.put(BINARY_CHUNK,    wltNameTruncPad,             width=64)
      hdataMid.put(UINT64,          self.createTime)      
      hdataMid.put(UINT32,          self.createBlock)      
      hdataMid.put(UINT32,          self.rsecParity)
      hdataMid.put(UINT32,          self.rsecPerData)

      sizeRemaining = self.headerSize - hdataMid.getSize()
      hdataMid.put(BINARY_CHUNK, '\x00'*sizeRemaining)
      midParity = WalletEntry.CreateErrCorrCode(hdataMid.getBinaryString(), 16, 1024)
      
      hdata = BinaryPacker()
      hdata.put(BINARY_CHUNK,    ArmoryFileHeader.WALLETMAGIC, width=8)
      hdata.put(UINT32,          self.headerSize)
      hdata.put(BINARY_CHUNK,    hdataMid.getBinaryString())
      hdata.put(BINARY_CHUNK,    midParity,  16)
   
      return hdata.getBinaryString()


   #############################################################################
   @staticmethod
   def Unserialize(theStr):
      """
      The header data is not substantial so much by itself, so much as it is
      simply reading it and checking that this is really an 2.0 wallet, for
      the correct network, of the correct version.
      """
      afh = ArmoryFileHeader()
      toUnpack = makeBinaryUnpacker(theStr)

      wltMagic  = toUnpack.get(BINARY_CHUNK, 8)
      headSize  = toUnpack.get(UINT32)
      hdataMid  = toUnpack.get(BINARY_CHUNK, headSize)
      midParity = toUnpack.get(BINARY_CHUNK, 16)

      hdataMid,failFlag,modFlag = WalletEntry.VerifyErrCorrCode(hdataMid, midParity)
      if failFlag:
         LOGERROR('Header data was corrupted, or not an Armory wallet')
         afh.isDisabled = True
         return afh

      if wltMagic != ArmoryFileHeader.WALLETMAGIC:
         if wltMagic != '\xbaWALLET\x00':
            LOGERROR('The wallet file does not have the correct magic bytes')
            raise FileExistsError('This does not appear to be an Armory wallet')
         else:
            LOGERROR('You attempted to load an Armory 1.35 wallet!  Must use'
                     'Armory version 0.92 or ealier to do this, or use the '
                     'migration tool to convert it to the new format.')
            raise FileExistsError('Old Armory wallet, it must be migrated!')
         
   
      hunpack = makeBinaryUnpacker(hdataMid)
      versionInt = hunpack.get(UINT32)
      netMagic   = hunpack.get(BINARY_CHUNK, 4)
      wltFlags   = hunpack.get(BITSET,       4)
      nameLen    = hunpack.get(UINT8)
      wltNamePad = hunpack.get(BINARY_CHUNK, 64)
      timeCreate = hunpack.get(UINT64)
      blkCreate  = hunpack.get(UINT32)
      rsecParity = hunpack.get(UINT32)
      rsecPerData= hunpack.get(UINT32)

      # These last two vars tell us what all the OTHER wallet entries will be
      # using for RS error correction.  For the header entry itself, it's
      # hardcoded to be 16 bytes per 1024.


      if not netMagic==getMagicBytes():
         LOGERROR('This wallet is for the wrong network!')
         LOGERROR('   Wallet is for:  %s ', BLOCKCHAINS[netMagic])
         LOGERROR('   You are on:     %s ', BLOCKCHAINS[getMagicBytes()])
         raise NetworkIDError('Wallet is for wrong network!')

      if not versionInt==getVersionInt(ARMORY_WALLET_VERSION):
         LOGWARN('This wallet is for an older version of Armory!')
         LOGWARN('Wallet version: %d', versionInt)
         LOGWARN('Armory version: %d', getVersionInt(ARMORY_WALLET_VERSION))


      if [rsecParity, rsecPerData] != [ERRCORR_BYTES, ERRCORR_PER_DATA]:
         # Technically, we could make all wallet code accommodate dynamic
         # RSEC parameters, but it would add some complexity for something
         # that shouldn't be necessary.  TODO: Maybe one day...
         LOGERROR('This wallet uses different error correction'
                  'parameters than this version of Armory')
         afh.isDisabled = True
         return afh

      wltName = toUnicode(wltNamePad[:nameLen])

      afh.initialize(wltName, timeCreate, blkCreate, wltFlags)
      return afh
     

################################################################################
################################################################################
class ArmoryWalletFile(object):
   
   AKP_WALLET_TYPES = set()

   @staticmethod
   def RegisterWalletDisplayClass(clsType):
      ccode = clsType.FILECODE
      if ccode in ArmoryWalletFile.AKP_WALLET_TYPES:
         raise ValueError('Class with code "%s" is already in map!' % ccode)
      ArmoryWalletFile.AKP_WALLET_TYPES.add(ccode)
      LOGINFO('Registered wallet display class: %s' % clsType.FILECODE)
      

   #############################################################################
   def __init__(self):

      self.fileHeader = ArmoryFileHeader()

      self.uniqueIDB58       = None  # UniqueID of first root/seed
      self.walletPath        = None
      self.walletPathBackup  = None
      self.walletPathUpdFail = None
      self.walletPathBakFail = None

      # We will queue updates to the wallet file, and later apply them  
      # atomically to avoid corruption problems
      self.updateQueue   = []
      self.lastFilesize  = -1

      # Last synchronized all chains to this block
      self.lastSyncBlockNum = 0

      # Everything in the wallet 
      self.allWalletEntries  = []

      # List of branches to display as "wallets"
      self.displayableWalletsMap  = {}  

      # All AKP objects that are their own parent (i.e. tree root node)
      self.topLevelRoots  = []

      # Any lockboxes that are maintained in this wallet file
      # Indexed by p2sh-scrAddr
      self.lockboxMap = {}

      # List of all master encryption keys in this wallet (and also the 
      # data needed to understand how to decrypt them, probably by KDF)
      self.ekeyMap = {}

      # List of all KDF objects -- probably created based on testing the 
      # system speed when the wallet was created
      self.kdfMap  = {}


      # Master address list of all wallets/roots/chains/leaves
      self.masterScrAddrMap  = {}

      # Master map of all objects with entry IDs
      self.masterEntryIDMap  = {}

      # Labels stored in this wallet file regarding addrs or txes
      self.scrAddrLabelMap = {}
      self.txLabelMap = {}

      # List of all encrypted wallet entries that couldn't be decrypted 
      # Perhaps later find a way decrypt and put them into the other maps
      self.opaqueList  = []

      # List of all WalletEntry objects that had a file code we didn't 
      # recognize.  Perhaps these were created by a newer version of
      # Armory, or will be consumed by a module/plugin
      self.unrecognizedList  = []

      # List of all WalletEntry objects that had an unrecoverable error
      self.unrecoverableList  = []

      # This is a list of objects that did not find their parent in this file
      self.wltParentMissing = []

      # We have the ability to store arbitrary data in the wallet files
      # Among other things, this gives plugins a way to read and write
      # data to wallet files, and running Armory without the plugin will
      # just shove it into this map and ignore it.
      self.arbitraryDataMap = Infinimap()

      # List of all WalletEntry object IDs disabled for various reasons
      # (usually from critical data not recognized in a child entry)
      self.disabledRootIDs = set()
      self.disabledList = []

      # If != None, it means that this wallet holds only a subset of data 
      # in the parent file.  Probably just addr/tx comments and P2SH scripts
      self.masterWalletRef = None

      # Alternatively, if this is a master wallet it may have a supplemental
      # wallet for storing
      self.supplementalWltPath = None
      self.supplementalWltRef = None



      # These flags are ONLY for unit-testing the atomic file operations
      # (normally testing code should not be part of production code, but 
      # we really don't have a way to otherwise test the recovery actions
      # of a wallet-update operation being interrupted)
      self.interruptTest1  = False
      self.interruptTest2  = False
      self.interruptTest3  = False

      # Set read-only flag:  will not modify any wallet files, will not 
      # create backup, will throw error if you attempt to write anything.
      # Really, this is intended for reading and querying the wallet obj.
      # Even generating new addresses would induce file write ops.
      self.isReadOnly = False

      # Wallet operations are not threadsafe.  Detect multiple access
      self.wltFileUpdateLock = threading.Lock()

      
   #############################################################################
   def initializeWalletOnDisk(self):
      if os.path.exists(self.walletPath):
         raise WalletExistsError('Cannot initialize wallet that already exists at %s!' % self.walletPath)

      if os.path.exists(self.walletPathBackup):
         LOGERROR('Backup wallet file already exists.  Deleting')
         removeIfExists(self.walletPathBackup)
         
      if os.path.exists(self.walletPathUpdFail):
         LOGERROR('Update fail flag exists, deleting')
         removeIfExists(self.walletPathUpdFail)

      if os.path.exists(self.walletPathBakFail):
         LOGERROR('Backup update fail flag exists, deleting')
         removeIfExists(self.walletPathBakFail)

      with open(self.walletPath, 'wb') as f:
         f.write(self.fileHeader.serialize())

      # This makes sure the backup file is created and synchronous
      self.doWalletFileConsistencyCheck()


   #############################################################################
   def getAkpObjectByScrAddr(self, scrAddr):
      return self.masterScrAddrMap.get(scrAddr)



   #############################################################################
   @_CheckFsyncArgument
   def createNewKDFObject(self, kdfAlgo, fsync=None, **kdfCreateArgs):
      """
      ROMixOv2 is ROMix-over-2 -- it's the ROMix algorithm as described by 
      Colin Percival, but using only 1/2 of the number of LUT ops, in order
      to bring down computation time in favor of more memory usage.

      If we had access to Scrypt, it could be an option here.  ROMix was 
      chosen due to simplicity despite its lack of flexibility
      """
      LOGINFO('Creating new %s KDF with the following parameters:' % kdfAlgo)
      for key,val in kdfCreateArgs.iteritems():
         LOGINFO('   %s: %s' % (key, str([val])))
         
      newKDF = KdfObject.CreateNewKDF(kdfAlgo, **kdfCreateArgs)
      self.kdfMap[newKDF.getKdfID()] = newKDF

      if fsync:
         self.doFileOperation('AddEntry', newKDF)


   
         
   #############################################################################
   def changeMasterKeyEncryptParams(self, ekeyID, oldUnlockParams, 
                                    newEkeyCreateParams, newEkeyClass=None):
      """
      We actually have tested functions which will change the unlock params
      for a given EncryptionKey or MultiPwdEncryptionKey.  They work.  But
      this method allows you to switch between them (such as taking a wallet
      which is encrypted with only a single password, and enforce multi-pwd
      encryption).  Doing this requires making a new object and deleting the
      old one from the wallet file.  In that case, we might as well just 
      *always* create a new object and delete the old one.  There's no real
      downside to it.  

      @oldUnlockParams:    
         This can be empty if you unlocked the ekey before
         entering this method.  Otherwise, it's generally
         just a password.  I would need a kdfObj and/or 
         ekeyObj if it does not have internal refs set

      @newEkeyCreateParams: 
         This is all the arguments that are needed for the
         call to ekey.createNewMasterKey().  If the new obj
         will be:
            EncryptionKey:  kdfObj, encrAlgo, passwd
            MultiPwdEncryptionKey:  kdfList, efragAlgo, M, passwdList, labels
                        
      This method guarantees that the new ekey created has the same Ekey ID 
      as the original (even if you switch between single and multi-password!)
      This guarantees that anything that encrypted with the original key will
      work with the new key.
      """

      if newEkeyClass is None:
         newEkeyClass = EncryptionKey

      oldEkey = self.ekeyMap.get(ekeyID)
      if oldEkey is None:
         raise KeyError('Ekey with ID "%s" not found in map' % ekeyID)

      if oldEkey.useEncryption() and oldEkey.isLocked():
         oldEkey.unlock(**oldUnlockParams)

      sbdRawEkey = oldEkey.getPlainEncryptionKey()
      

      newEkey = newEkeyClass()
      newEkey.createNewMasterKey(preGenKey=sbdRawEkey, **newEkeyCreateParams)

      if not ekeyID == newEkey.ekeyID:
         raise EncryptionError('New Master Key does not have same ID')

      self.addFileOperationToQueue('DeleteEntry', oldEkey)
      self.addFileOperationToQueue('AddEntry', newEkey)
      
       
      self.ekeyMap[ekeyID] = newEkey
      self.linkAllEntries()
       


   #############################################################################
   def changeOuterEncryption(self, encryptInfoObj):
      raise NotImplementedError


   #############################################################################
   def getKDF(self, kdfID):
      return self.kdfMap.get(kdfID, None)

   #############################################################################
   def getEkey(self, ekeyID):
      return self.ekeyMap.get(ekeyID, None)


   #############################################################################
   def setWalletPath(self, wltPath):
      # We will need a bunch of different pathnames for atomic update ops
      self.walletPath        = wltPath
      self.walletPathBackup  = self.getWalletPath('backup')
      self.walletPathUpdFail = self.getWalletPath('update_unsuccessful')
      self.walletPathBakFail = self.getWalletPath('backup_unsuccessful')

   #############################################################################
   def mergeWalletFile(self, wltOther, rootsToAbsorb='ALL'):
      """
      Just like in git, WltA.mergeWalletFile(WltB) means we want to pull all 
      the data from WltB into WltA and leave WltB untouched.
      """
      raise NotImplementedError('TODO: Implement MergeWallet logic')

      if isinstance(wltOther, basestring):
         # Open wallet file
         if not os.path.exists(wltOther):
            raise WalletExistsError('Wallet to merge DNE: %s' % wltOther)
         wltOther = ArmoryWalletFile.ReadWalletFile(wltOther, openReadOnly=True)
      

      if rootsToAbsorb=='ALL':
         rootsToAbsorb = set([scrAddr for scrAddr,rt in wltOther.iteritems()])
         

      for we in self.allWalletEntries:
         if we.wltLvlParent.getEntryID() in rootsToAbsorb:
            raise NotImplementedError('Need to get fancier with this logic')
            newWE = WalletEntry()
            newWE.copyFromWE(we)
            newWE.wltFileRef = self
            newWE.wltByteLoc = None
            
            # TODO:  Need logic to avoid overwriting data!  For instance 
            #        we especially need to avoid accidentally merging a 
            #        WO wallet and overwriting a full wallet. 
            #self.wltFileRef.addFileOperationToQueue('AddEntry', newWE)



   #############################################################################
   def mergeBranchFromWalletFile(self, filepath, rootID, weTypesToMerge=['ALL']):
      """
      Opens another wallet2.0 wallet, extracts all WEs that are marked with 
      the given ID as its parent, and injects them into this file.  We need
      to check all entries, before merging, that we are not going to overwrite
      data in the file
      """
      raise NotImplementedError('TODO: Implement MergeWallet logic')
      if not os.path.exists(filepath):
         LOGERROR('Wallet to merge does not exist: %s', filepath)

      with open(filepath, 'rb') as f:
         bu = BinaryUnpacker(f.read())

      while not bu.isEndOfStream():
         weObj = WalletEntry().UnserializeEntry(bu)
         if weObj.payload.root160:
            raise 'Notimplemented'   
         if weTypesToMerge[0].lower()=='all' or weObj.entryCode in weTypesToMerge:
            self.addFileOperationToQueue('Append', weObj)
      

   #############################################################################
   def loadExternalInfoWallet(self, filepath):
      """
      After this wallet is loaded, we may want to merge, in RAM only, another
      wallet file containing only P2SH scripts and comments.  The reason for
      this is that our root private key only needs to be backed up once, but 
      P2SH scripts MUST be backed up regularly (and comment fields would be 
      nice to have backed up, too).  The problem is, you don't want to put 
      your whole wallet file into dropbox, encrypted or not.  The solution is
      to have a separate P2SH&Comments file (a wallet without any addresses)
      which can be put in Dropbox.  And encrypt that file with information
      in the wathcing-only wallet -- something that you have even without 
      unlocking your wallet, but an attacker does not if they compromise your
      Dropbox account.
      """
      raise NotImplementedError('TODO: Implement external wallet logic')

      if not os.path.exists(filepath):
         LOGERROR('External info file does not exist!  %s' % filepath)

      self.externalInfoWallet =  ArmoryWalletFile.ReadWalletFile(filepath)


   #############################################################################
   @staticmethod
   def CheckWalletExists(wltPath):
      if not os.path.exists(wltPath):
         raise FileExistsError('Wallet file does not exist: %s' % wltPath)

      with open(wltPath,'rb') as f:
         first20bytes = BinaryUnpacker(f.read(20))

      filemagic = first20bytes.get(BINARY_CHUNK, 8)
      if not filemagic == ArmoryFileHeader.WALLETMAGIC:
         raise FileExistsError('Specified file is not an Armory2.0 wallet')

      ignored = first20bytes.get(UINT32) # size field that we don't care about
      versionStr = getVersionString(readVersionInt(first20bytes.get(UINT32)))
      LOGINFO('Wallet name and version: "%s", %s' % (wltPath, versionStr))


   #############################################################################
   @staticmethod
   def ReadWalletFile(wltPath, openReadOnly=False):
      """
      This reads an Armory wallet 2.0 wallet file, which contains a constant-
      size header, and then a collection of IFF/RIFF-like WalletEntry objects.
      
      WE DO NOT ASSUME ANY PARTICULAR ORDERING!  For instance, if a WalletEntry
      object references a KDF object that is in the same wallet file, we never
      assume that the KDF object has been read yet.  While we may enforce
      reasonable ordering when we create the wallet, there are certain wallet
      operations (like merging wallets) which may leave them out of order.  

      For that reason, this method has two phases: 
         (1) Read and organize all the WalletEntry objects into maps/lists
         (2) Walk through all the objects and do anything that requires 
             references to other objects in the wallet file, such as setting
             child-parent references, and disabling nodes with critical
             children that are unrecognized

      In case there are outer-encrypted entries in the wallet (all info
      about the WalletEntry is encrypted except for the parent ID), then 
      we will repeat the above after decrypting the opaque objects.
      """
      ArmoryWalletFile.CheckWalletExists(wltPath)

      if len(ArmoryWalletFile.AKP_WALLET_TYPES)==0:
         LOGERROR('No AKP types are registered to be displayed as wallets')
         LOGERROR('This message is to remind you that you should register')
         LOGERROR('your wallet types with ArmoryWalletFile class before')
         LOGERROR('loading any wallet files.  This makes sure that all ')
         LOGERROR('wallet files know what the "base" entries are to track')
         raise UnserializeError

      wlt = ArmoryWalletFile()
      wlt.setWalletPath(wltPath)
      wlt.isReadOnly = openReadOnly
      wlt.arbitraryDataMap.clearMap()
   
      if openReadOnly:
         # We can't do a standard file consistency check because it would try 
         # to correct errors but this wallet is in read-only mode
         if not wlt.checkWalletIsConsistent():
            raise WalletUpdateError('Wallet to open in RO mode is inconsistent!')
      else:
         wlt.doWalletFileConsistencyCheck()

      # We assume the raw wallet fits in RAM.  This isn't a bad assumption,
      # since the wallet file is currently designed to hold all wallet entries
      # in RAM anyway.  If we want to change this, we need to switch to a 
      # database-backed wallet design.
      openfile = open(wltPath,'rb')
      rawWallet = BinaryUnpacker(openfile.read())
      openfile.close()

      
      # The header is always the first X bytes.  This will confirm the wallet
      # magic bytes and throw an error if it's not a good wallet2.0 file
      wlt.fileHeader = ArmoryFileHeader.Unserialize(rawWallet)
      if wlt.fileHeader.isDisabled:
         wlt.isDisabled = True
         return wlt

      allEntries = [] 
      while rawWallet.getRemainingSize() > 0:
         currPos = rawWallet.getPosition()
         wltEntry = WalletEntry.UnserializeEntry(rawWallet, wlt, currPos)
         allEntries.append(wltEntry)
         LOGDEBUG(wltEntry.pprintOneLineStr())
         
         
      # This will organize all the entries into their respective lists/maps,
      # set references between related objects, disable things as needed, etc
      wlt.addEntriesToWallet(allEntries)

      # The wallet is now ready for use
      wlt.uniqueIDB58 = wlt.topLevelRoots[0].getUniqueIDB58()
      return wlt


   #############################################################################
   def unlockOuterEncryption(self, **outerCryptArgs):
      raise NotImplementedError('This has never been tried/tested!')
      # ... though the implementation is approximately correct

      # If outer encryption was used on any entries, decrypt & add, if possible
      # (needed to add previous entries, because one is probably the decryption
      # key and/or KDF needed to unlock outer encryption)
      if len(self.opaqueList) > 0:
         if len(outerCryptArgs) == 0:
            LOGWARN('Opaque entries in wallet, no decrypt args supplied')
         else:
            newWEList = []
            stillOpaqueList = []
            for i,we in enumerate(self.opaqueList):
               try:
                  decryptedWE = we.decryptPayloadReturnNewObj(**outerCryptArgs)
                  newWEList.append(decryptedWE)
               except:
                  # Remove this except/warning once this seems to work
                  LOGEXCEPT('Failed to decrypt some opaque entries')
                  stillOpaqueList.append(we)
                  
            self.opaqueList = stillOpaqueList
            self.addEntriesToWallet(newWEList)
         




   #############################################################################
   @_CheckFsyncArgument
   def addEntriesToWallet(self, weList, fsync=None):
      """
      This operates in two steps:  
         (1) Filter the list of WalletEntry objects into the right lists/maps
         (2) Go back through everything and set references between them and 
             apply any operations that requires having all WE objects avail.
             Each WalletEntry object should have a linkWalletEntries method.
             
      Everything that will be accessed by ID is stored in a map indexed by
      ID.  For now, we will assume that all parent references are ArmoryRootKey
      objects (or None), and everything else will know which map to look in
      (like looking in ekeyMap when looking for encryption keys, etc).  
      Therefore, we do not store a master map of all IDs.
      """
      
      activeWEList = []
      for we in weList:
         if we.isDeleted:  
            continue

         if fsync:
            # In case the Reed-Solomon error correction actually finds an error
            if we.needFsync:
               self.addFileOperationToQueue('UpdateEntry', we)

            if we.wltByteLoc in [0, None]:
               self.addFileOperationToQueue('AddEntry', we)


         if we.isDisabled:
            if hasattr(we,'isAkpRootRoot') and we.isAkpRootRoot:
               self.disabledRootIDs.add(we.getEntryID())
            continue


         # If WE is unrecognized, ignore, if also critical, disable parent
         if we.isUnrecognized:
            self.unrecognizedList.append(we)
            if we.isRequired and not getIgnoreUnrecognizedFlag():
               self.disabledRootIDs.add(we.wltParentID)
            continue

         if we.isUnrecoverable:
            self.unrecoverableList.append(we)
            continue
      
         if we.isOpaque:
            self.opaqueList.append(we)
            continue

         # If recognized, unencrypted, no unrecoverable errors and not disabled
         # add it to the "active" list.  Will call "linkWalletEntries" on each.
         activeWEList.append(we)


      # Walk through all the remaining entries
      for we in activeWEList:
         # If we have a deactivated root, deactivate all direct children
         # Only need to check parent, because rootroot objs are their own parent
         if we.wltParentID in self.disabledRootIDs or we.isDisabled:
            we.isDisabled = True
            self.disabledList.append(we)
            continue


         # Everything else goes in the master list of entries
         self.allWalletEntries.append(we)

         weID = we.getEntryID()
         if len(weID)>0:
            self.masterEntryIDMap[weID] = we

         if issubclass(we.__class__, ArmoryKeyPair):
            if we.getScrAddr() in self.masterScrAddrMap:
               LOGINFO('ScrAddr is in wallet file multiple times!')

            self.masterScrAddrMap[we.getScrAddr()] = we
   
            if we.isAkpRootRoot:
               self.topLevelRoots.append(we)

            if we.FILECODE in ArmoryWalletFile.AKP_WALLET_TYPES:
               if we.notForDirectUse:
                  # This is most likely a part of a multisig wallet
                  LOGWARN('Base wallet type marked not for direct use')
               else:
                  wltID = we.getEntryID()
                  if wltID in self.displayableWalletsMap:
                     LOGWARN('WltID=%s added to displayable wlts twice' % wltID)
                  self.displayableWalletsMap[wltID] = we
         elif we.FILECODE in ('ADDRLABL', 'ADDRDESC'):
            pass # handled in linkWalletEntries
         elif we.FILECODE=='TXLABEL_':
            if we.txidFull is not None:
               self.txLabelMap[we.txidFull] = we
            if we.txidMall is not None:
               self.txLabelMap[we.txidMall] = we
         elif we.FILECODE=='LOCKBOX_':
            self.lockboxMap[we.uniqueIDB58] = we
         elif we.FILECODE in ('EKEYREG_','EKEYMOFN'):
            self.ekeyMap[we.getEncryptionKeyID()] = we
            we.addWltChildRef(we)
         elif we.FILECODE=='KDFOBJCT':
            self.kdfMap[we.getKdfID()] = we
            we.addWltChildRef(we)
         elif we.FILECODE=='ARBDATA_':
            we.insertIntoInfinimap(self.arbitraryDataMap)
         else:
            LOGERROR('Unhandled WalletEntry type: %s' % we.FILECODE)
            self.unrecognizedList.append(we)
         

      # This calls each WE's linkWalletEntries() method, which will reach
      # into this wallet file and find the data it needs to link.  This is 
      # performed on ALL entries, not just the ones added, as the ones that
      # were added may have been missing links for some of them.
      self.linkAllEntries()
         
      if fsync:
         self.fsyncUpdates()

      return self
         
      

   #############################################################################
   def linkAllEntries(self):
      """
      This method is pretty simple when we've required all classes to have this
      behavior implemented in the class.
      """
      LOGINFO('Linking all wallet entries')
      for we in self.allWalletEntries:
         we.linkWalletEntries(self)
      



   #############################################################################
   def doFileOperation(self, operationType, theData):
      """
      This is intended to be used for one-shot safe writing to file. 
      Normally, you would batch your updates using addFileOperationToQueue
      and then call fsyncUpdates() when you're done.
   
      This method assumes there's nothing in the queue, and you want to
      simply execute one operation, right now.
      """
      if not len(self.updateQueue)==0:
         LOGERROR('Wallet update queue not empty!  Adding this to the')
         LOGERROR('queue and fsyncing')

      self.addFileOperationToQueue(operationType, theData)
      self.fsyncUpdates()
          

   #############################################################################
   @VerifyArgTypes(operationType=str, 
                   wltEntry=[WalletEntry, ArmoryFileHeader])
   def addFileOperationToQueue(self, operationType, wltEntry):
      """
      This will queue up an add/update/delete op for wallet entry.

          ('RewriteHeader', ArmoryFileHeader)
          ('AddEntry',      WalletEntryObj)
          ('UpdateEntry',   WalletEntryObj)
          ('DeleteEntry',   WalletEntryObj)

      If one of the "entry" versions is used, it will simply pull the
      necessary information out of the object and do an "Append' or "Modify'
      as necessary.
      """
      if self.isReadOnly:
         raise WalletUpdateError('Cannot do file ops on ReadOnly wallet!')

      if not operationType.lower() in ['rewriteheader','addentry', 
                                       'updateentry', 'deleteentry']:
         raise BadInputError('Wallet update type invalid: %s' % operationType)
      
      self.updateQueue.append([operationType, wltEntry])
      wltEntry.needsFsync = True
         
         
         
   #############################################################################
   def createWalletName(self):
      ArmoryWalletFile.CreateWalletNameFromID(self.uniqueIDB58)

   #############################################################################
   @classmethod
   def CreateWalletNameFromID(cls, uniqB58):
      return 'armory_wallet2.0_%s.wlt' % uniqB58

   #############################################################################
   def getWalletPath(self, nameSuffix=None):
      fpath = self.walletPath

      if not self.walletPath:
         if not self.uniqueIDB58:
            raise WalletExistsError('No wlt unique ID , cannot create filename')
         fpath = os.path.join(getArmoryHomeDir(), self.createWalletName())

      if nameSuffix:
         name,ext = os.path.splitext(fpath)
         joiner = '' if name.endswith('_') else '_'
         fpath = name + joiner + nameSuffix + ext

      return fpath


   #############################################################################
   def fsyncUpdates(self):
            
      """
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
      a way that any corruption is detectable and we know how to recover it.

      This assumes that file write operations will always happen in the exact
      the same order the OS sends the commands to disk.  It turns out this 
      assumption is not true on most HDDs -- however we have used this in 1.35
      wallets for years.  The first implementation had it backwards and actually
      corrupted itself if *either* file was corrupt and we got multiple corrupt
      wallet reports each month.  Since we fixed that over a year ago, I don't 
      think we've had a single corrupted wallet report.  Therefore, it seems 
      that corruption does happen, and this technique is effective.

      This has some "InterruptTest" code directly in the method.  Unfortunately,
      I have no idea how to remove this while still being able to test that the
      atomic behavior is still intact.  This is needed to force the method to
      quit mid-write and then we can later load the wallet and see if it 
      corrects itself properly.
      
      """
      if self.isReadOnly:
         raise WalletUpdateError('Wallet is opened in read-only mode!')
      
      
      if len(self.updateQueue)==0:
         return False


      # We're going to block until we get the lock, regardless.  This call
      # here is simply putting an error in the log file to let us know that
      # there was a multi-threading collision.  I was kind of hoping we
      # wouldn't have this at all.  
      gotLock = self.wltFileUpdateLock.acquire(False)
      if not gotLock:
         LOGERROR( 'Attempted to call fsync while currently fsync\'ing.  '
                   'This is probably a multithreading collision.  Wallet '
                   'operations were not intended to be threadsafe!'
                   'Will wait until we can safely fsync')
         
      
      try:
         if not gotLock:
            # Try again but block this time
            self.wltFileUpdateLock.acquire(True)
         

         if not os.path.exists(self.walletPath):
            raise FileExistsError('No wallet file exists to be updated!')
   
         # Identify if the batch contains updates to the same object mult times.
         # We can safely batch updates to any mixture of objects, but not 
         # multiple changes to the same object
         fileLocToUpdate = set()
         fileIDsToUpdate = set()
         for opType,weObj in self.updateQueue:
            if weObj.wltByteLoc > 0:
               if weObj.wltByteLoc in fileLocToUpdate:
                  LOGERROR('Dup Obj: %s (ID=%s, loc=%d)', weObj.FILECODE, 
                           binary_to_hex(weObj.getEntryID()), weObj.wltByteLoc)
                  raise WalletUpdateError('Multiple updates to same ID in batch')
               fileLocToUpdate.add(weObj.wltByteLoc)

            if len(weObj.getEntryID()) > 0:
               if weObj.getEntryID() in fileIDsToUpdate:
                  LOGERROR('Dup Obj: %s (ID=%s, loc=%d)', weObj.FILECODE, 
                           binary_to_hex(weObj.getEntryID()), weObj.wltByteLoc)
                  raise WalletUpdateError('Multiple updates to same ID in batch')
               fileIDsToUpdate.add(weObj.wltByteLoc)
               
   
         # Make sure that the primary and backup files are synced before update
         self.doWalletFileConsistencyCheck()
   
         # Make sure all entries have valid wallet file locations
         for opType,weObj in self.updateQueue:
            if opType.lower() in ['updateentry', 'deleteentry'] and weObj.wltByteLoc <= 0:
               raise WalletUpdateError('Wallet entry cannot be updated without loc')
        
         # Apply updating to both files in an identical manner
         MAIN,BACKUP = [0,1]
         for fnum in [MAIN,BACKUP]:
            # Update fail flags so that if process crashes mid-update, we know
            # upon restart where it failed and can recover appropriately
            if fnum==MAIN:
               # Set flag to indicate we're about to update the main wallet file
               wltPath = self.walletPath
               interrupt = self.interruptTest1
               touchFile(self.walletPathUpdFail)
            elif fnum==BACKUP:
               # Set flag to start modifying backup file.  Create backup-update
               # flag before deleting main-update flag file.  If both files
               # exist, we know exactly where updating terminated
               wltPath = self.walletPathBackup
               interrupt = self.interruptTest3
               touchFile(self.walletPathBakFail)
               if self.interruptTest2: 
                  raise InterruptTestError 
               removeIfExists(self.walletPathUpdFail)
               
   
            # We will do all mid-file operations first, and queue up all 
            # append operations for the end.  Second pass will apply all the 
            # append operations and then update the weObjs with new size and 
            # loc. Append operations include both the AddEntry cmds in the 
            # queue, also UpdateEntry cmds with objects now a different size.
            appendAfterOverwriteQueue = []
   
            try:
               wltfile = open(wltPath, 'r+b')
            except IOError:
               LOGEXCEPT('Failed to open %s in r+b mode. Permissions?' % wltPath)
               return False
   
            for opType,weObj in self.updateQueue:
               # At this point, self.wltEntrySz is always the size of the 
               # object currently in the file, not yet been updated if the WE 
               # is now a new size.  If we requested "UpdateEntry" but we 
               # serialize the object and it turns out to be a different size,   
               # then we delete and append, instead.
               if opType.lower()=='rewriteheader':
                  # Header is always exact same size, at beginning of file
                  wltfile.seek(0)
                  wltfile.write(weObj.serialize())
               elif opType.lower() == 'addentry':
                  # Queue up append operations until after in-place modifications
                  appendAfterOverwriteQueue.append([weObj, weObj.serializeEntry()])
               elif opType.lower() == 'deleteentry':
                  # Delete is just in-place modification, overwrite with \x00's
                  weObj.isDeleted = True
                  wltfile.seek(weObj.wltByteLoc)
                  wltfile.write(weObj.serializeEntry(doDelete=True))
               elif opType.lower() == 'updateentry':
                  weSer = weObj.serializeEntry()
                  if len(weSer) == weObj.wltEntrySz:
                     # Same size, overwrite in-place if different
                     wltfile.seek(weObj.wltByteLoc)
                     alreadyInFile = wltfile.read(weObj.wltEntrySz)
                     if not weSer == alreadyInFile:
                        wltfile.seek(weObj.wltByteLoc)
                        wltfile.write(weSer)
                  else:
                     # Obj changed size, delete old add new one to the queue
                     wltfile.seek(weObj.wltByteLoc)
                     wltfile.write(weObj.serializeEntry(doDelete=True))
                     appendAfterOverwriteQueue.append([weObj, weSer])
   
            # This is for unit-testing the atomic-wallet-file-update robustness
            if interrupt: raise InterruptTestError
   
            # Close file for writing, reopen it in append mode
            try:
               wltfile.close()
               appendfile = open(wltPath, 'ab')
            except IOError:
               LOGEXCEPT('Failed to open %s in ab mode. Permissions?' % wltPath)
               return False
   
            for weObj,weSer in appendAfterOverwriteQueue:
               appendfile.write(weSer)
               if fnum==BACKUP:
                  # At end of updating backup file, can update WE objects
                  weObj.wltEntrySz = len(weSer)
                  weObj.wltByteLoc = appendfile.tell() - weObj.wltEntrySz
         
            appendfile.close()
   
         # Finish by removing flag that indicates we were modifying backup file
         removeIfExists(self.walletPathBakFail)
   
         # Mark WalletEntry objects as having been updated
         for opType,weObj in self.updateQueue:
            weObj.needsFsync = False
   
         # In debug mode, verify that main and backup are identical
         if getDebugFlag():
            hashMain = sha256(open(self.walletPath,       'rb').read())
            hashBack = sha256(open(self.walletPathBackup, 'rb').read())
            if not hashMain==hashBack:
               raise WalletUpdateError('Updates of two wallet files do not match!')

         self.updateQueue = []
   
         return True
      finally:
         self.wltFileUpdateLock.release()
         
   
   
   

   #############################################################################
   def doWalletFileConsistencyCheck(self):
      """
      First we check the file-update flags (files we touched/removed during
      file modification operations), and then restore the primary wallet file
      and backup file to the exact same state -- we know that at least one of
      them is guaranteed to not be corrupt, and we know based on the flags
      which one that is -- so we execute the appropriate copy operation.
      """

      if not os.path.exists(self.walletPath):
         raise FileExistsError('No wallet file exists to be checked!')

      if not os.path.exists(self.walletPathBackup):
         # We haven't even created a backup file, yet
         LOGDEBUG('Creating backup file %s', self.walletPathBackup)
         touchFile(self.walletPathBakFail)
         shutil.copy(self.walletPath, self.walletPathBackup)
         removeIfExists(self.walletPathBakFail)

      if os.path.exists(self.walletPathBakFail) and \
         os.path.exists(self.walletPathUpdFail):
         # Here we actually have a good main file, but backup never succeeded
         LOGERROR('***WARNING: error in backup file... how did that happen?')
         shutil.copy(self.walletPath, self.walletPathBackup)
         removeIfExists(self.walletPathUpdFail)
         removeIfExists(self.walletPathBakFail)
      elif os.path.exists(self.walletPathUpdFail):
         LOGERROR('***WARNING: last file op failed!  Restoring from backup')
         # main wallet file might be corrupt, copy from backup
         shutil.copy(self.walletPathBackup, self.walletPath)
         removeIfExists(self.walletPathUpdFail)
      elif os.path.exists(self.walletPathBakFail):
         LOGERROR('***WARNING: creation of backup was interrupted -- fixing')
         shutil.copy(self.walletPath, self.walletPathBackup)
         removeIfExists(self.walletPathBakFail)

      # TODO: do some or all of these checks for wallet 2.0
      # ***NOTE:  For now, the remaining steps are untested and unused!

      # After we have guaranteed that main wallet and backup wallet are the
      # same, we want to do a check that the data is consistent.  We do this
      # by simply reading in the key-data from the wallet, unserializing it
      # and reserializing it to see if it matches -- this works due to the
      # way the PyBtcAddress::unserialize() method works:  it verifies the
      # checksums in the address data, and corrects errors automatically!
      # And it's part of the unit-tests that serialize/unserialize round-trip
      # is guaranteed to match for all address types if there's no byte errors.

      # If an error is detected, we do a safe-file-modify operation to re-write
      # the corrected information to the wallet file, in-place.  We DO NOT
      # check comment fields, since they do not have checksums, and are not
      # critical to protect against byte errors.


      return True


   #############################################################################
   def checkWalletIsConsistent(self):
      """
      Same as doWalletFileConsistencyCheck, but does not modify anything.
      Instead, returns False if there is an inconsistency that would otherwise
      induce wallet changes by doWalletFileConsistencyCheck.  Used for wallets
      opened in read-only mode.
      """

      if not os.path.exists(self.walletPath):
         raise FileExistsError('No wallet file exists to be checked!')

      if not os.path.exists(self.walletPathBackup):
         # No backup file to compare against
         return True
      elif os.path.exists(self.walletPathBakFail) and \
           os.path.exists(self.walletPathUpdFail):
         # Here we actually have a good main file, but backup never succeeded
         return False
      elif os.path.exists(self.walletPathUpdFail):
         return False
      elif os.path.exists(self.walletPathBakFail):
         return False

      return True


   #############################################################################
   def addAkpBranchToWallet(self, rootNodeOfBranch, errorIfDup=True):
      # In the absence of error checking, this method simply passes 
      # through to the AKP method that does this for us (it assumes that the
      # wallet reference is already set).
      if rootNodeOfBranch.wltFileRef is None:
         rootNodeOfBranch.wltFileRef = self

      # By default, we need to confirm no duplicate addrs in the wallet file
      if errorIfDup:
         # Create a recursive method to check all branch nodes
         def checkAlreadyInMap(wlt, node):
            if node.getEntryID() in wlt.masterScrAddrMap:
               raise WalletUpdateError('Addr already in wallet file! %s' % \
                     scrAddr_to_addrStr(node.getEntryID()))

            for idx,child in node.akpChildByIndex.iteritems():
               checkAlreadyInMap(wlt, child)

         checkAlreadyInMap(self, rootNodeOfBranch)
            
      # In the absence of the above error checking, this method simply passes
      # through to the AKP method.
      rootNodeOfBranch.akpBranchQueueFsync()
      
      
      
   #############################################################################
   @_CheckFsyncArgument
   @VerifyArgTypes(ekeyObj=[EncryptionKey, MultiPwdEncryptionKey],
                   kdfObj=[None, KdfObject, list, tuple])
   def addCryptObjsToWallet(self, ekeyObj, kdfObj=None, errorIfDup=True, fsync=None):
      """
      We only supply a kdfObj as a separate arg when the ekeyObj doesn't have 
      one (or more) defined internally (i.e., only if not chained encryption).
      """
      toAddToWallet = [ekeyObj]
      if isinstance(kdfObj, (list, tuple)):
         toAddToWallet.extend(kdfObj)
      elif isinstance(kdfObj, KdfObject):
         toAddToWallet.append(kdfObj)

      if isinstance(ekeyObj, EncryptionKey) and ekeyObj.kdfRef:
         toAddToWallet.append(ekeyObj.kdfRef)
      elif isinstance(ekeyObj, MultiPwdEncryptionKey) and ekeyObj.kdfRefList:
         toAddToWallet.extend(ekeyObj.kdfRefList)

      # By default, confirm that the data to add isn't already part of this 
      # wallet, or linked to another wallet
      if errorIfDup:
         for we in toAddToWallet:
            weID = we.getEntryID()
            weIDHex = binary_to_hex(weID)
            if we.wltFileRef or we.wltByteLoc:
               raise WalletUpdateError('WE already linked: %s' % weIDHex)
   
            if self.ekeyMap.get(weID) or self.kdfMap.get(weID):
               raise WalletUpdateError('WE already in wallet: %s' % weIDHex)

      
      for we in toAddToWallet:
         # All crypt objects are their own parent (root objs).  They may be
         # shared across multiple wallet/root/AKP/AWD objects
         we.wltParentRef = we
         we.wltParentID = we.getEntryID()
         we.wltFileRef = self

   
      self.addEntriesToWallet(toAddToWallet, fsync=fsync)
      


   #############################################################################
   def unlockWalletEkey(self, ekeyID, *unlockArgs, **unlockKwargs):
      ekeyObj = self.ekeyMap.get(ekeyID, None)

      if ekeyObj is None:
         raise KeyDataError("No ekey in wlt with id=%s" % binary_to_hex(ekeyID))

      ekeyObj.unlock(*unlockArgs, **unlockKwargs)


   #############################################################################
   def forceLockWalletEkey(self, ekeyID):
      # Lock this specific ekey
      ekeyObj = self.ekeyMap.get(ekeyID, None)
      if ekeyObj is None:
         raise KeyDataError("No ekey in wlt with id=%s" % binary_to_hex(ekeyID))

      LOGWARN('Forcing ekey lock; checkLockTimeout() to lock only if not in use')
      ekeyObj.lock()


   #############################################################################
   def forceLockAllWalletEkeys(self):
      for eid,ekeyObj in self.ekeyMap.iteritems():
         self.forceLockWalletEkey(eid)
      
      
   #############################################################################
   def checkLockTimeoutAllEkeys(self):
      # Using ekey.checkLockTimeout guarantees we won't lock an ekey in the 
      # middle of an operation that requires it to be unlocked
      currTime = time.time()
      for eid,ekeyObj in self.ekeyMap.iteritems():
         ekeyObj.checkLockTimeout()



   #############################################################################
   def writeFreshWalletFile_BASE(self, weFilterFunc,
                                       newPath, 
                                       newName=None,
                                       withOpaque=True,
                                       withDisabled=True,
                                       withUnrecognized=True,
                                       withUnrecoverable=True,
                                       withOrphan=True):

      """
      weFilterFunc should return None if we don't want to write the entry
      to the wallet file at all.  Otherwise it should return a WE object
      that can be serialized directly into the file.  

      It's not just a filter, because the weFilterFunc may actually modify
      the WE before returning it to be written to the new file.  This is 
      used for creating watch-only wallets:  the filter will check if it's 
      an AKP type, if so, it makes a copy of it, wipes the private keys, and
      then returns the WO copy.
      """
      
      pathdir = os.path.dirname(newPath)
      pathfn  = os.path.basename(newPath)

      if not os.path.exists(pathdir):
         raise FileExistsError('Path for new wlt does not exist: %s', pathdir)

      if os.path.exists(newPath):
         raise FileExistsError('File already exists, will not overwrite')


      weListList = self.allWalletEntries[:]
      if withOpaque:        weListList.append(self.opaqueList)
      if withDisabled:      weListList.append(self.disabledList)
      if withUnrecognized:  weListList.append(self.unrecognizedList)
      if withOrphan:        weListList.append(self.wltParentMissing)

      with open(newPath, 'wb') as newWltFile:
         newWltFile.write(self.fileHeader.serialize(altName=newName))
         for we in self.allWalletEntries:
            newWE = weFilterFunc(we)
            if not newWE is None:
               newWltFile.write(newWE.serializeEntry())


   #############################################################################
   def writeFreshWalletFile(self, newPath, 
                                  rootList='ALL',
                                  newName=None,
                                  withOpaque=True,
                                  withDisabled=True,
                                  withUnrecognized=True,
                                  withUnrecoverable=True,
                                  withOrphan=True):

      """
      Can pass in a list of entryIDs for "rootList" and only WalletEntry objs
      with that wallet parent will be written into the new wallet file.
      """
      
      def rootFilter(we):
         if rootList=='ALL' or we.wltParentID in rootList:
            return we
         else:
            return None
      

      self.writeFreshWalletFile_BASE(rootFilter, newPath, newName, withOpaque, 
               withDisabled, withUnrecognized, withUnrecoverable, withOrphan)


   
   #############################################################################
   def writeWatchOnlyCopy(self, newPath, 
                                newName=None, 
                                rootList='ALL',
                                withOpaque=True,
                                withDisabled=True,
                                withUnrecognized=True,
                                withUnrecoverable=True,
                                withOrphan=True):

      
      def filterAndWipe(we):
         if not rootList=='ALL' and not we.wltParentID in rootList:
            return None

         if isinstance(we, ArmoryKeyPair):
            newWE = we.copy()
            newWE.wipePrivateData()
            return newWE
         else:
            return we
            
            
      self.writeFreshWalletFile_BASE(filterAndWipe, newPath, newName, withOpaque, 
               withDisabled, withUnrecognized, withUnrecoverable, withOrphan)
      

   #############################################################################
   @_CheckFsyncArgument
   def updateScrAddrLabel(self, scrAddr, lbl, fsync=None):
      if not scrAddr in self.masterScrAddrMap:
         raise WalletUpdateError('No scrAddr available')
      
      if scrAddr in self.scrAddrLabelMap:
         sa = self.scrAddrLabelMap[scrAddr]
         sa.label = lbl
      else:
         saLbl = ScrAddrLabel()
         saLbl.initialize(sa, lbl)
         saLbl.linkWalletEntries(self)

      if fsync:
         saLbl.fsync()

   #############################################################################
   @_CheckFsyncArgument
   def updateTxLabel(self, txidType, txid, label, fsync=None):
      pass

   #############################################################################
   @_CheckFsyncArgument
   def addArbitraryWalletData(self, parentRef, keyList, plainStr, fsync=None):
      """
      Since we are "adding" data to the map, we error out if it already exists.
      Clear the entry and call this method if you want to change the encryption.
      """
      node = self.arbitraryDataMap.getNode(keyList, doCreate=False)
      if not node is None:
         raise KeyError('AWD already in map: %s' % str(keyList))

      node = self.arbitraryDataMap.getNode(keyList, doCreate=True)
      node.setPlaintext(plainStr)

      # Link to parent and to wallet
      parentRef.addWltChildRef(node.awdObj)
      self.allWalletEntries.append(node.awdObj)
      node.awdObj.linkWalletEntries(self)
      if fsync:
         node.awdObj.fsync()

      
   #############################################################################
   @_CheckFsyncArgument
   def addArbitraryWalletData_Encrypted(self, parentRef, keyList, plainStr, 
                                                            ekeyID, fsync=None):
      """
      Since we are "adding" data to the map, we error out if it already exists.
      Clear the entry and call this method if you want to change the encryption.
      """
      ekey = self.ekeyMap.get(ekeyID)
      if ekey is None:
         raise EncryptionError('Cannot set encrypted data without ekey')

      if ekey.isLocked():
         raise WalletLockError('Ekey %s is locked, cannot encrypt data')

      node = self.arbitraryDataMap.getNode(keyList, doCreate=False)
      if not node is None:
         raise KeyError('AWD already in map: %s' % str(keyList))

      randIV = SecureBinaryData().GenerateRandom(8).toBinStr()
      awdCryptInfo = ArmoryCryptInfo(NULLKDF, 'AE256CBC', ekeyID, randIV)

      node = self.arbitraryDataMap.getNode(keyList, doCreate=True)
      node.awdObj.enableEncryption(awdCryptInfo, ekey)

      # If we got here, the node was created, encryption was set
      node.setPlaintextToEncrypt(plainStr)

      # Link to parent and to wallet
      parentRef.addWltChildRef(node.awdObj)
      self.allWalletEntries.append(node.awdObj)
      node.awdObj.linkWalletEntries(self)
      if fsync:
         node.awdObj.fsync()
      
      if fsync:
         node.awdObj.fsync()

   #############################################################################
   @_CheckFsyncArgument
   def updateArbitraryWalletData(self, keyList, plainStr, fsync=None):
      # If node is encrypted, expect unencrypted SBD obj.  ADM will encrypt it
      # on the way in (if the ekey is unlocked), Otherwise a regular python str
      self.arbitraryDataMap.setData(keyList, plainStr, doCreate=False)

      if fsync:
         node = self.arbitraryDataMap.getNode(keyList)
         node.awdObj.fsync()
      

   #############################################################################
   def getArbitraryWalletData(self, keyList):
      """ Returns plain string if unencrypted, SBD if encrypted """
      node = self.arbitraryDataMap.getNode(keyList, doCreate=False)
      if node is None:
         return None
         
      # This throws an error if ekey is needed but locked
      return node.awdObj.getPlainDataCopy()  

   #############################################################################
   # Copy the wallet file to backup
   def backupWalletFile(self, backupPath=None):
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
   #############################################################################
   #
   # Wallet-creation methods
   #
   #############################################################################
   #############################################################################

   #############################################################################
   @staticmethod
   @VerifyArgTypes(sbdExtraEntropy=[SecureBinaryData, None],
                   sbdPregeneratedSeed=[SecureBinaryData, None])
   def createNewRootObject(rootClass, encryptInfo, ekeyRef, 
                           sbdExtraEntropy=None, sbdPregeneratedSeed=None, 
                           fillPool=True, fsync=True, kdfRef=None):
      """
      If this new master seed is being protected with encryption that isn't
      already defined in the wallet, then the new Ekey & KDF objects needs 
      to be created and added to the wallet before calling this function.  
      Additioanlly, the ekey needs to be unlocked.
      
      In the event that no pregenerated seed data is passed to this function,
      "sbdExtraEntropy" is a required argument here, because we should *always*
      be sending extra entropy into the secure (P)RNG for seed creation.  
      Never fully trust the operating system, and there's no way to make its 
      seed generation worse, so we will require it even if the caller decides
      to pass in all zero bytes.  ArmoryQt.getExtraEntropyForKeyGen() (as 
      of this writing) provides a 32-byte SecureBinaryData object which is 
      the hash of system files, key- and mouse-press timings, and a screenshot 
      of the user's desktop.

      Note if you pass in a pregenerated seed, you can then pass in None for 
      sbdExtraEntropy arg.
      
      See ArmoryKeyPair::setWalletAndCryptInfo for explanation of ekeyRef and
      kdfRef args.  Typically the KDF will already be part of the ekeyRef and 
      you pass in None for kdfRef in this method
      """

      if not issubclass(rootClass, ArmorySeededKeyPair):
         raise TypeError('Must provide a seeded/root key pair class type')
      
      if encryptInfo.useEncryption() and (ekeyRef is None or ekeyRef.isLocked()):
         raise WalletLockError('Ekey must exist and be unlocked to create root')

      if (sbdPregeneratedSeed is None) == (sbdExtraEntropy is None):
         raise KeyDataError('Must supply only one: pregen seed or extra entropy')


      # Create a new root of the desired type
      newRoot = rootClass()

      # Setting cryptInfo with None for ekey and kdf is fine (no encryption)
      newRoot.setCryptInfo(encryptInfo, ekeyRef, kdfRef, fsync=fsync)

      if sbdPregeneratedSeed is None:
         if sbdExtraEntropy is None or sbdExtraEntropy.getSize() < 16:
            raise KeyDataError('Must provide 16+ bytes of extra entropy')

         newRoot.createNewSeed(DEFAULT_SEED_SIZE, sbdExtraEntropy, 
                               fillPool=fillPool, fsync=fsync)
      else:
         newRoot.initializeFromSeed(sbdPregeneratedSeed, 
                                    fillPool=fillPool, fsync=fsync)

      newRoot.wltParentID = newRoot.getEntryID()
      newRoot.wltParentRef = newRoot  # root address has self-reference
      return newRoot
      

   #############################################################################
   @staticmethod
   @VerifyArgTypes(sbdPassphrase=SecureBinaryData)
   def generateNewSinglePwdMasterEKey(sbdPassphrase, 
                                      kdfAlgo='ROMIXOV2', 
                                      kdfTargSec=0.25, 
                                      kdfMaxMem=32*MEGABYTE, 
                                      encryptAlgo='AE256CBC'):

      #####
      LOGINFO('Creating new KDF with params: time=%0.2fs, maxmem=%0.2fMB', 
                                        kdfTargSec, kdfMaxMem/float(MEGABYTE))
      newKDF = KdfObject.CreateNewKDF(kdfAlgo, targSec=kdfTargSec, 
                                               maxMem=kdfMaxMem)
      kdfID = newKDF.getKdfID()
      LOGINFO('Finished creating new KDF obj, ID=%s' % binary_to_hex(kdfID))

      tstart = time.time()
      newKDF.execKDF(SecureBinaryData('TestPassword'))
      tend = time.time()

      LOGINFO('KDF ID=%s uses %0.2fMB and a test password took %0.2fs',
                     binary_to_hex(newKDF.getKdfID()), 
                     newKDF.memReqd/float(MEGABYTE), (tend-tstart))

      #####
      LOGDEBUG('Creating new master encryption key')
      newEKey = EncryptionKey().createNewMasterKey(
         newKDF, encryptAlgo, sbdPassphrase)
      ekeyID = newEKey.getEncryptionKeyID()
      LOGINFO('Finished creating new EKEY obj, ID=%s' % binary_to_hex(ekeyID))

      #####
      # The following ACI is provided for any AKP objects that will be 
      # encrypted with this master ekey (KDF is null because it's part of 
      # the ekey object)
      aci = ArmoryCryptInfo(NULLKDF, encryptAlgo, ekeyID, 'PUBKEY20')
   
      return [aci, newEKey]


   #############################################################################
   @staticmethod
   def CreateWalletFile_BASE(walletName=u'',
                             root=None,
                             encryptInfo=None,
                             ekeyRef=None,
                             kdfRef=None,
                             createTime=0,
                             createBlock=0,
                             createInDir=None,
                             specificFilename=None,
                             Progress=emptyFunc):

      """
      If an ekeyRef is provided, the ekey needs to be unassociated (so far)
      with any wallet, and it must be unlocked

      Use this for "restoring" wallets.  In the case of a new wallet, the
      seed is secure-randomly generated by the calling method and passed
      in as an argument.  You can create it unencrypted by simply leaving
      the default None for the last 3 args.
      
      createTime and createBlock are also rarely used... we avoid using them
      unless we're absolutely sure about both.  By setting them too high, we
      may end up permanently missing history and/or unspent coins for this
      wallet.  

      Note: the kdfRef argument is rarely used, because the relevant kdf is
            already part of the ekey object, and will get called by the 
            encryption chaining.  See the comments in the setWalletAndCryptInfo
            method in ArmoryKeyPair.py.
      """
      if root is None:
         raise RuntimeError("Wallet file needs a root in order to create a file")

      if ekeyRef and ekeyRef.isLocked():
         raise WalletLockError('Cannot create encrypted root with locked ekey')

      LOGINFO('***Creating new wallet')

      newWlt = ArmoryWalletFile()
      newWlt.fileHeader.initialize(walletName, createTime, createBlock)

      root.setWalletFile(newWlt)

      idB58 = root.getUniqueIDB58()
      newWlt.uniqueIDB58 = idB58

      if createInDir is None:
         createInDir = getArmoryHomeDir() 

      if specificFilename is None:
         specificFilename = ArmoryWalletFile.CreateWalletNameFromID(idB58)

      # This sets the primary wallet file, as well as backups and flags
      newWlt.setWalletPath(os.path.join(createInDir, specificFilename))

      # This creates the wallet file and writes the header to it
      newWlt.initializeWalletOnDisk()

      # Don't fsync anything yet, fill the keypool in RAM first, with progress
      root.fillKeyPool(fsync=False, Progress=Progress)

      # Confirm this root and its children are not in the wallet yet, then add
      newWlt.addAkpBranchToWallet(root)

      # Confirm the ekey and kdf(s) are not in wallet yet, then add
      if ekeyRef or kdfRef:
         newWlt.addCryptObjsToWallet(ekeyRef, kdfRef)
   
      # Finally, make sure all the above operations are written to disk
      newWlt.fsyncUpdates()  

      # Remove the object we just created, read back from file
      newWltPath = newWlt.walletPath

      # Return the disk-syncrhonized wallet object
      return ArmoryWalletFile.ReadWalletFile(newWltPath)
      

   #############################################################################
   @staticmethod
   def CreateWalletFile_NewRoot(walletName=u'',
                                newRootClass=ABEK_BIP44Seed,
                                sbdExtraEntropy=None,
                                sbdPregeneratedSeed=None,
                                encryptInfo=None,
                                ekeyRef=None,
                                kdfRef=None,
                                createTime=0,
                                createBlock=0,
                                createInDir=None,
                                specificFilename=None,
                                Progress=emptyFunc):

      """
      If an ekeyRef is provided, the ekey needs to be unassociated (so far)
      with any wallet, and it must be unlocked

      Use this for "restoring" wallets.  In the case of a new wallet, the
      seed is secure-randomly generated by the calling method and passed
      in as an argument.  You can create it unencrypted by simply leaving
      the default None for the last 3 args.
      
      createTime and createBlock are also rarely used... we avoid using them
      unless we're absolutely sure about both.  By setting them too high, we
      may end up permanently missing history and/or unspent coins for this
      wallet.  

      Note: the kdfRef argument is rarely used, because the relevant kdf is
            already part of the ekey object, and will get called by the 
            encryption chaining.  See the comments in the setWalletAndCryptInfo
            method in ArmoryKeyPair.py.
      """
      if ekeyRef and ekeyRef.isLocked():
         raise WalletLockError('Cannot create encrypted root with locked ekey')

      #####
      # Create a new root object of the specified ArmorySeededKeyPair class
      newRoot = ArmoryWalletFile.createNewRootObject(
         newRootClass, encryptInfo, ekeyRef, sbdExtraEntropy,
         sbdPregeneratedSeed, fsync=False, fillPool=False, kdfRef=kdfRef)
      LOGINFO('Created new root of type: %s, ID=%s' %
              (newRoot.getName(), newRoot.getUniqueIDB58()))

      return ArmoryWalletFile.CreateWalletFile_BASE(
         walletName,
         newRoot,
         encryptInfo,
         ekeyRef,
         createInDir=createInDir,
         specificFilename=specificFilename,
         Progress=Progress)


   #############################################################################
   @staticmethod
   @VerifyArgTypes(sbdPassphrase=SecureBinaryData,
                   sbdExtraEntropy=[SecureBinaryData, None])
   def CreateWalletFile_SinglePwd(walletName,
                                  sbdPassphrase,
                                  newRootClass=ABEK_BIP44Seed,
                                  sbdExtraEntropy=None,
                                  sbdPregeneratedSeed=None,
                                  encryptAlgo='AE256CFB',
                                  kdfAlgo='ROMIXOV2',
                                  kdfTargSec=DEFAULT_COMPUTE_TIME_TARGET,
                                  kdfMaxMem=DEFAULT_MAXMEM_LIMIT,
                                  Progress=emptyFunc,
                                  createInDir=None,
                                  specificFilename=None):
      """
      This can be used to either restore from an existing seed, or create
      a new one.  
      """

      if (sbdExtraEntropy is None) == (sbdPregeneratedSeed is None):
         raise KeyDataError('Must supply only one: pregen seed or extra entropy')
                                       
      aci,newEKey = ArmoryWalletFile.generateNewSinglePwdMasterEKey( 
         sbdPassphrase, kdfAlgo, kdfTargSec, kdfMaxMem, encryptAlgo)

      newEKey.unlock(sbdPassphrase)
      try:
         newEKey.markKeyInUse()
         # Now we have everything we need to create the 
         newWlt = ArmoryWalletFile.CreateWalletFile_NewRoot(
                        walletName,
                        newRootClass,
                        sbdExtraEntropy,
                        sbdPregeneratedSeed,
                        aci,
                        newEKey,
                        kdfRef=None,
                        createTime=0,
                        createBlock=0,
                        createInDir=createInDir,
                        specificFilename=specificFilename,
                        Progress=Progress)

      finally:
         newEKey.finishedWithKey()
                                                  
      return newWlt


   #############################################################################
   def getOnlyEkeyID(self):
      if not len(self.ekeyMap)==1:
         raise KeyDataError('Expected one ekey, found %d', len(self.ekeyMap))
                                                  
      for k in self.ekeyMap.keys():
         return k


   #############################################################################
   def getOnlyEkey(self):
      if not len(self.ekeyMap)==1:
         raise KeyDataError('Expected one ekey, found %d', len(self.ekeyMap))
                                                  
      for v in self.ekeyMap.values():
         return v


   #############################################################################
   def getOnlyKdfID(self):
      if not len(self.kdfMap)==1:
         raise KeyDataError('Expected one kdf, found %d', len(self.kdfMap))
                                                  
      for k in self.kdfMap.keys():
         return k

   #############################################################################
   def getOnlyKdf(self):
      if not len(self.kdfMap)==1:
         raise KeyDataError('Expected one kdf, found %d', len(self.kdfMap))
                                                  
      for v in self.kdfMap.values():
         return v


   #############################################################################
   # VARIETY OF WAYS TO PPRINT THE ENTRIES IN THE WALLET FILE
   #############################################################################

   #############################################################################
   def pprintEntryList(self, indent=0):
      for i,we in enumerate(self.allWalletEntries):
         print '   %03d' % i,
         we.pprintOneLine(indent=indent)

   #############################################################################
   def pprintToCSV_Simple(self, fileOut=None):
      if fileOut:
         csvOut = open(fileOut, 'w')

      for i,we in enumerate(self.allWalletEntries):
         pairs = we.getWltEntryPPrintPairs()
         pairs.extend(we.getPPrintPairs())
         strLine = str(i) + ',' + ','.join([str(a)+'='+str(b) for a,b in pairs])
         if fileOut is None: 
            print strLine
         else:
            csvOut.write(strLine + '\n')

      if fileOut:
         csvOut.close()

   #############################################################################
   def pprintToCSV_Columns(self, fileOut=None):
      if fileOut:
         csvOut = open(fileOut, 'w')

      columnList = ['Index']
      rowCols = []
      for i,we in enumerate(self.allWalletEntries):
         rowCols.append(['']*len(columnList))
         rowCols[-1][0] = str(i)
         pairs = we.getWltEntryPPrintPairs()
         pairs.extend(we.getPPrintPairs())
         for k,v in pairs:
            if not k in columnList:
               columnList.append(str(k))
               rowCols[-1].append(str(v))
            else:
               col = columnList.index(str(k))
               rowCols[-1][col] = str(v)

      if fileOut is None: 
         print ','.join(columnList)
         for row in rowCols:
            print ','.join(row)
      else:
         csvOut.write(','.join(columnList) + '\n')
         for row in rowCols:
            csvOut.write(','.join(row) + '\n')

      if fileOut:
         csvOut.close()


ArmoryWalletFile.RegisterWalletDisplayClass(ABEK_StdWallet)
ArmoryWalletFile.RegisterWalletDisplayClass(Armory135Root)
ArmoryWalletFile.RegisterWalletDisplayClass(ArmoryImportedRoot)

