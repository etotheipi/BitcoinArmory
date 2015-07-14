import threading

from ArmoryUtils import *
from BinaryPacker import makeBinaryUnpacker, BinaryPacker
from Decorators import VerifyArgTypes
from FiniteField import SplitSecret
from WalletEntry import WalletEntry


NULLSTR       = lambda numBytes=0: '\x00'*numBytes
NULLSBD       = lambda numBytes=0: SecureBinaryData(numBytes)
NULLCRYPTINFO = lambda:  ArmoryCryptInfo(None)


# We only store 8 bytes for each IV field, though we usually need 16 or 32
@VerifyArgTypes(iv=SecureBinaryData)
def stretchIV(iv, sz):
   if not 0 < sz <= 64:
      raise BadInputError('Invalid stretch size: %s' % sz)

   # Truncate if too big
   newIV = iv.toBinStr()[:sz]

   # Hash if too small
   if len(newIV) < sz:
      newIV = sha512(newIV)[:sz]

   return SecureBinaryData(newIV)


def calcEKeyID(rawKey):
   # We use HMAC instead of regular checksum, solely because it's designed
   # for hashing secrets, though I don't think it's really necessary here
   # (especially for a truncated hash).
   if isinstance(rawKey, SecureBinaryData):
      return HMAC512(rawKey.toBinStr(), "ArmoryKeyID")[:8]
   else:
      return HMAC512(rawKey, "ArmoryKeyID")[:8]


###############################################################################
# This is a decorator-factory.  Decorate a bound method using this decorator
# and a string argument which is the variable name of the ekey object we
# expect to be unlocked
###############################################################################
# This decorator not only confirms that the member ekey is unlocked before
# calling the function, but it also acquires the re-entrant lock (rlock) to
# make sure that no other process locks the key while this method is using
# it (using the wrapper functions markKeyInUse() and finishedWithKey())
###############################################################################
def EkeyMustBeUnlocked(ekeyVarName):
   def decorator(func):

      def wrappedFunc(*args, **kwargs):
         aekSelf = args[0]
         ekey = getattr(aekSelf, ekeyVarName)

         if ekey is None:
            return func(*args, **kwargs)

         if ekey.isLocked():
            raise WalletLockError('Ekey locked when calling %s' % func.__name__)

         try:
            ekey.markKeyInUse()
            return func(*args, **kwargs)
         finally:
            ekey.finishedWithKey()

      return wrappedFunc

   return decorator


###############################################################################
###############################################################################
class ArmoryCryptInfo(object):
   """
   This can be attached to WalletEntries or individual pieces of data, to
   describe how we plan to protect it.  The idea is to have a uniform way of
   specifying how to encrypt & decrypt things in the wallet file, even though
   it may require using information outside this object to apply it.

   For instance, private keys will usually be encrypted using a master key that
   is, itself, encrypted.  The private key would simply have one of these
   objects serialized next to it, specifying the ID (hash) of the master key
   that was used to encrypt it.  Then the calling code can go get that object
   and do what is needed for it.

   In many ways, this data structure doesn't have to be rigorous.  It's still
   up to the calling code to make sure the key material and KDFs are available
   for encrypting and decrypting.  This simply provides information that the
   calling code can use to know how to encrypt & decrypt.

   Frequently, this encryption info will contain initialization vectors (IVs),
   generated randomly at creation time, or references to what is to be used as
   the IV (such as using the hash160 of the addr).

   ArmoryCryptInfo objects carry four pieces of data:
         (1) KDF object ID           (8)   # KDF object has params
         (2) Encryption algo         (8)   # name of encryption algorithm
         (3) Encryption key source   (8)   # ID of master key or sentinel
         (4) Init Vect source        (8)   # 8-byte IV or sentinel

   Encryption key (ekey) source is typically either the 8-byte ID of a
   master encryption key object that should be stored in the same file,
   or a sentinel value from CRYPT_KEY_SRC that indicates where the key
   material should come from.  In the case of encrypting non-security-
   sensitive objects in a backup file, we might use the chaincode of
   the parent key object as the key material (so you need the WO wallet
   in order to decrypt, but this file is stored somewhere without that).

   Init vect source is the same:  sometimes we simply generate an IV to
   be stored with the ArmoryCryptInfo object, and sometimes we simply use
   a sentinel from CRYPT_IV_SRC to identify where to get it.  The most
   common would be PUBKEY20, which is used when encrypting a Bitcoin
   private key and the public key is stored next to the encrypted priv
   key.  PUBKEY20 means the IV is not supplied, but instead you should
   use the first 16 bytes of the public key as the IV.

   The examples below use the following data:

         KDF object to use       '11112222'   hash(kdfObj.serialize())[:8]
         Crypto algorithm name   'AE256CBC'
         Master key ID           '99998888'   hash(ekey.serialize())[:8]
         Init Vect (IV)          'f3f3f3f3'   (only if ACI stores the IV)


   Anything in all capitals letters are sentinel values which mean:
   "the calling code should recognize this sentinel value and provide
   the specified data"


   Master Private Key in wallet will use (the calling code needs to
   request a password from the user):

             ArmoryCryptInfo( '11112222',
                              'AE256CBC',
                              'PASSWORD',
                              'f3f3f3f3')

   Private keys encrypted with master private key:
   (Note we only use KDFs with password-protected objects -- in this case
   we are encrypted with a full-entropy 32-byte key, so no KDF is needed;
   however that master key will need to be decrypted first to decrypt this
   object, which will probably require a password & KDF)

             ArmoryCryptInfo( 'IDENTITY',
                              'AE256CBC',
                              '99998888',
                              'PUBKEY20')


   Bare private key encryption w/o master key (use KDF & password):
             ArmoryCryptInfo( '11112222',
                              'AE256CBC',
                              'PASSWORD',
                              'PUBKEY20')

   Encrypt P2SH scripts, labels, and meta-data in insecure backup file:
             ArmoryCryptInfo( 'IDENTITY',
                              'AE256CBC',
                              'PARCHAIN' ,
                              'f3f3f3f3')

   Encrypt Public Keys & Addresses as outer encryption of WalletEntries:
             ArmoryCryptInfo( '11112222',
                              'AE256CFB',
                              'PASSWORD',
                              'f3f3f3f3')

   No encryption
             ArmoryCryptInfo( 'IDENTITY',
                              'IDENTITY',
                              '00000000',
                              '00000000')
   """

   ############################################################################
   def __init__(self, kdfID=NULLKDF,
                      encrAlgo=NULLCRYPT,
                      keysrc=NULLSTR(8),
                      ivsrc=NULLSTR(8)):

      if kdfID is None:
         kdfID = NULLKDF

      # Now perform the encryption using the encryption key
      if not (encrAlgo==NULLSTR(8)) and (not encrAlgo in KNOWN_CRYPTO):
         raise UnrecognizedCrypto('Unknown encryption algo: %s', encrAlgo)

      self.kdfObjID     = kdfID
      self.encryptAlgo  = encrAlgo
      self.keySource    = keysrc
      self.ivSource     = ivsrc

      # Use this to hold temporary key data when using chained encryption
      self.tempKeyDecrypt = SecureBinaryData(0)

   ############################################################################
   def noEncryption(self):
      return (self.encryptAlgo==NULLCRYPT)

   #############################################################################
   def useEncryption(self):
      return (not self.noEncryption())

   ############################################################################
   def useKeyDerivFunc(self):
      return (not self.kdfObjID==NULLKDF)

   ############################################################################
   def copy(self):
      ser = self.serialize()
      aci = ArmoryCryptInfo().unserialize(ser)
      return aci

   ############################################################################
   def copyWithNewIV(self, newIV=None):
      aci = self.copy()
      if not newIV:
         newIV = SecureBinaryData().GenerateRandom(8).toBinStr()
      aci.ivSource = newIV
      return aci

   ############################################################################
   def hasStoredIV(self):
      if self.ivSource==NULLSTR(8):
         return False
      # A non-zero ivSource is "stored" if it's not one of the sentinel values
      return (self.getEncryptIVSrc()[0] == CRYPT_IV_SRC.STOREDIV)

   ############################################################################
   def setIV(self, newIV):
      if self.ivSource != NULLSTR(8):
         raise KeyDataError('Attempted to set IV on einfo that already has IV')

      if isinstance(newIV, SecureBinaryData):
         newIV = newIV.toBinStr()

      if len(newIV)>8:
         raise KeyDataError('Attempted to set IV to non-8-byte string')
      elif len(newIV)<8:
         raise BadInputError('Supplied IV is less than 8 bytes.  Aborting')

      self.ivSource = newIV

   ############################################################################
   def getEncryptKeySrc(self):

      if self.keySource in ['PARCHAIN', 'PASSWORD', 'MULTIPWD', 'RAWKEY32']:
         enumOut = getattr(CRYPT_KEY_SRC, self.keySource)
         return (enumOut, '')
      elif self.keySource==NULLSTR(8):
         raise KeyDataError('Requested key source but ACI keysrc is NULLCRYPT')
      else:
         return (CRYPT_KEY_SRC.EKEY_OBJ, self.keySource)

   ############################################################################
   def getBlockSize(self):
      if not KNOWN_CRYPTO.has_key(self.encryptAlgo):
         raise EncryptionError('Unknown crypto blocksize: %s' % self.encryptAlgo)

      return KNOWN_CRYPTO[self.encryptAlgo]['blocksize']

   ############################################################################
   def getExpectedInputSize(self):
      # This is the keysize expected for this *ArmoryCryptInfo* object, not the
      # encryptAlgo of it.  In other words, this is to let us know the expected
      # size of the input -- if this ArmoryCryptInfo uses a KDF, there is no
      # expected size.  Only if there is no KDF but does have encryptAlgo, then
      # we return the key size of that algo.
      if self.useKeyDerivFunc() or self.noEncryption():
         return 0
      elif KNOWN_CRYPTO.has_key(self.encryptAlgo):
         return KNOWN_CRYPTO[self.encryptAlgo]['keysize']
      else:
         raise EncryptionError('Unknown encryption keysize')

   ############################################################################
   def getEncryptIVSrc(self):
      if self.ivSource=='PUBKEY20':
         return (CRYPT_IV_SRC.PUBKEY20, '', '')
      else:
         sbdIVStretched = stretchIV(SecureBinaryData(self.ivSource),
                                    self.getBlockSize())
         return (CRYPT_IV_SRC.STOREDIV, self.ivSource, sbdIVStretched)



   ############################################################################
   def serialize(self):
      bp = BinaryPacker()
      bp.put(BINARY_CHUNK,  self.kdfObjID,      width=8)
      bp.put(BINARY_CHUNK,  self.encryptAlgo,   width=8)
      bp.put(BINARY_CHUNK,  self.keySource,     width=8)
      bp.put(BINARY_CHUNK,  self.ivSource,      width=8)
      return bp.getBinaryString()


   ############################################################################
   @staticmethod
   def unserialize(theStr):
      aci = ArmoryCryptInfo()
      bu = makeBinaryUnpacker(theStr)
      aci.kdfObjID    = bu.get(BINARY_CHUNK, 8)
      aci.encryptAlgo = bu.get(BINARY_CHUNK, 8)
      aci.keySource   = bu.get(BINARY_CHUNK, 8)
      aci.ivSource    = bu.get(BINARY_CHUNK, 8)
      return aci


   ############################################################################
   @VerifyArgTypes(keyData=[SecureBinaryData, list, tuple, None],
                   ivData=[SecureBinaryData, None])
   def prepareKeyDataAndIV(self, keyData=None, ivData=None,
                                                kdfObj=None, ekeyObj=None):
      """
      This is the code that is common to both the encrypt and decrypt functions.

      NOTE:  You can supply an ekey map and/or kdf map (such as those used in
             the ArmoryWallet class) instead of a specific ekey or kdf.  This
             method will check the map for the needed IDs in the maps and
             throw an error if they don't exist
      """


      # IV data might actually be part of this object, not supplied
      if not self.hasStoredIV():
         if ivData is None or ivData.getSize()==0:
            LOGERROR('Cannot [en|de]crypt without initialization vector.')
            raise InitVectError('No init vect available for [en|de]cryption')
         ivData = SecureBinaryData(ivData)
      elif ivData is None or ivData.getSize()==0:
         ivData = SecureBinaryData(self.ivSource)
      else:
         LOGERROR('ArmoryCryptInfo has stored IV and was also supplied one!')
         LOGERROR('Do not want to risk encrypting with wrong IV ... bailing')
         raise InitVectError('IV supplied and stored... ? bailing')

      # If ivData is less than 16 bytes (for AES256), then we need to stretch
      # it to be 16 bytes.  This does nothing if a 16-byte IV was passed in.
      ivData = stretchIV(ivData, self.getBlockSize())


      # When we have an ekeyObj, it means we should apply the supplied
      # passphrase/keyData to it to decrypt the master key (not this obj).
      # Then overwrite keyData with the decrypted masterkey since that is
      # the correct key to decrypt this object.
      if ekeyObj is None:
         keysrc = self.getEncryptKeySrc()[0]
         if keysrc == CRYPT_KEY_SRC.EKEY_OBJ:
            raise EncryptionError('EncryptionKey object required but not supplied')
      else:
         # If a map was supplied, get the correct ekey out of it
         if isinstance(ekeyObj, dict):
            ekeyObj = ekeyObj.get(self.keySource)
            if ekeyObj is None:
               ekeyID = binary_to_hex(self.keySource)
               raise KeyDataError('Encryption key is not avail: %s' % ekeyID)


         # We have supplied a master key to help encrypt/decrypt this object
         if self.useKeyDerivFunc():
            raise EncryptionError('Master key encryption should never use a KDF')

         # If supplied master key is correct, its ID should match stored value
         if not ekeyObj.getEncryptionKeyID() == self.keySource:
            raise EncryptionError('Supplied ekeyObj does not match keySource')

         # Make sure master key is unlocked -- use keyData arg if locked
         startedLocked = ekeyObj.isLocked()
         if startedLocked:
            if keyData is None:
               raise EncryptionError('Supplied locked ekeyObj w/o passphrase')

            # Use the supplied keydata to unlock the *MASTER KEY*
            # Note "unlock" will call the ekeyObj.einfo.decrypt
            if not ekeyObj.unlock(keyData, kdfObj):
               raise EncryptionError('Supplied locked ekeyObj bad passphrase')

         # Store tempKeyDecrypt in self so we can destroy it outside this func
         self.tempKeyDecrypt = ekeyObj.masterKeyPlain.copy()
         keyData = self.tempKeyDecrypt

         if startedLocked:
            ekeyObj.lock()


      # Apply KDF if it's requested
      if self.useKeyDerivFunc():
         # If a map was supplied, get the correct KDF out of it
         if isinstance(kdfObj, dict):
            kdfObj = kdfObj.get(self.kdfObjID)

         if kdfObj is None:
            kdfIDHex = binary_to_hex(self.kdfObjID)
            raise KdfError('KDF is not available: %s' % kdfIDHex)

         keyData = kdfObj.execKDF(keyData)

      # Check that after all the above, our final keydata is the right size
      expectedSize = KNOWN_CRYPTO[self.encryptAlgo]['keysize']
      if not keyData.getSize()==expectedSize:
         raise EncryptionError('Key is wrong size! Key=%d, Expect=%s' % \
                                            (keyData.getSize(), expectedSize))

      return keyData, ivData


   ############################################################################
   @VerifyArgTypes(plaintext=SecureBinaryData,
                   keyData=[SecureBinaryData, list, tuple, None],
                   ivData=[SecureBinaryData, None])
   def encrypt(self, plaintext, keyData=None, ivData=None, kdfObj=None, ekeyObj=None):
      """
      Ways this function is used:

         -- We are encrypting the data with a KDF & passphrase only:
               ekeyObj == None
               keyData is the passphrase (will pass through the KDF)
               ivData contains the IV to use for encryption of this object

         -- We are encrypting with a raw AES256 key
               ekeyObj == None
               keyData is the raw AES key (KDF is ignored/should be NULL)
               ivData contains the IV to use for encryption of this object

         -- We are encrypting using a master key
               ekeyObj == MasterKeyObj
               keyData is the passphrase for the *MASTER KEY*
               ivData contains the IV to use for encryption of this object
               (the master key carries its own IV, no need to pass it in)

      If using a master key, we are "chaining" the encryption.  Normally we
      have an encrypted object, take a passphrase, pass it through the KDF,
      use it to decrypt our object.

      When using a master key, the above process is applied to the encrypted
      master key, which will give us the encryption key to decrypt this
      object.

      Here, "keydata" may actually be a passphrase entered by the user, which
      will get stretched into the actual encryption key.  If there is no KDF,
      then keydata is simply the encryption key, provided by the calling func
      while likely checked the keySource and ivSource and fetched appropriate
      data for encryption/decryption.

      If ekeyObj is supplied, then we are saying that the given ekey is
      required for encryption/decryption and the keydata is provided as
      the passphrase to unlock the ekey.

      (if chaining...)
      In the case that ivData is supplied, it is assumed it is the IV for
      *this data*, not for the ekeyObj -- because ekey objects usually carry
      their own IV with them.  If you are doing something much more general
      or non-standard, this method may have to be adjusted to accommodate
      more complicated schemes.

      We need to fail if plaintext is not padded to the blocksize of the
      cipher.  The reason is that this function should only pass out encrypted
      data that exactly corresponds to the input, not some variant of it.
      If the data needs padding, the calling method can ask the CryptInfo
      object for the cipher blocksize, and pad it before passing in (and also
      take note somewhere of what the original datasize was).
      """
      if self.encryptAlgo==NULLCRYPT:
         return plaintext.copy()

      # Verify that the plaintext data has correct padding
      if not (plaintext.getSize() % self.getBlockSize() == 0):
         LOGERROR('Plaintext has wrong length: %d bytes', plaintext.getSize())
         LOGERROR('Length expected to be padded to %d bytes', self.getBlockSize())
         raise EncryptionError('Cannot encrypt non-multiple of blocksize')

      try:
         useKey,useIV = self.prepareKeyDataAndIV(keyData, ivData, kdfObj, ekeyObj)

         # Now perform the encryption using the encryption key
         if self.encryptAlgo=='AE256CFB':
            return CryptoAES().EncryptCFB(plaintext, useKey, useIV)
         elif self.encryptAlgo=='AE256CBC':
            return CryptoAES().EncryptCBC(plaintext, useKey, useIV)
         else:
            raise UnrecognizedCrypto('Unknown algo: %s' % self.encryptAlgo)

      finally:
         # If chained encryption, tempKeyDecrypt has the decrypted master key
         self.tempKeyDecrypt.destroy()



   ############################################################################
   @VerifyArgTypes(ciphertext=SecureBinaryData,
                   keyData=[SecureBinaryData, list, tuple, None],
                   ivData=[SecureBinaryData, None])
   def decrypt(self, ciphertext, keyData=None, ivData=None, kdfObj=None, ekeyObj=None):
      """
      See comments for encrypt function -- this function works the same way
      """
      if self.encryptAlgo==NULLCRYPT:
         return ciphertext.copy()

      # Make sure all the data is in SBD form -- will also be easier to destroy
      if not (ciphertext.getSize() % self.getBlockSize() == 0):
         LOGERROR('Ciphertext has wrong length: %d bytes', ciphertext.getSize())
         LOGERROR('Length expected to be padded to %d bytes', self.getBlockSize())
         raise EncryptionError('Cannot decrypt non-multiple of blocksize')

      try:
         useKey,useIV = self.prepareKeyDataAndIV(keyData, ivData, kdfObj, ekeyObj)

         # Now perform the decryption using the key
         if self.encryptAlgo=='AE256CFB':
            return CryptoAES().DecryptCFB(ciphertext, useKey, useIV)
         elif self.encryptAlgo=='AE256CBC':
            return CryptoAES().DecryptCBC(ciphertext, useKey, useIV)
         else:
            raise UnrecognizedCrypto('Unrecognized algo: %s' % self.encryptAlgo)

      finally:
         # If chained encryption, tempKeyDecrypt has the decrypted master key
         self.tempKeyDecrypt.destroy()


   #############################################################################
   def pprintOneLineStr(self, indent=0):
      return ' '*indent + 'ACI :', self.getPPrintStr()

   #############################################################################
   def getPPrintStr(self):
      out = ''
      algoStr = 'NO CRYPT' if self.encryptAlgo == NULLCRYPT else self.encryptAlgo
      kdfStr  = 'NO_KDF' if self.kdfObjID == NULLKDF else binary_to_hex(self.kdfObjID)[:8]
      ivStr = self.ivSource if self.ivSource=='PUBKEY20' else binary_to_hex(self.ivSource)[:8]

      keyStr = self.keySource
      try:
         enumval,src = self.getEncryptKeySrc()
         if enumval == CRYPT_KEY_SRC.EKEY_OBJ:
            keyStr = binary_to_hex(src)[:8]
            kdfStr  = 'CHAINKDF'
      except:
         keyStr = 'NO_SRC'

      return '[%s|%s|%s|%s]' % (algoStr, kdfStr, keyStr, ivStr)



#############################################################################
class KdfObject(WalletEntry):
   """
   Note that there is only one real KDF *algorithm* here, but each wallet
   has system-specific parameters required to execute the KDF (32-byte salt
   and memory required).  Therefore, there may be multiple KdfObjects even
   though they are all using the same underlying algorithm.

   ROMix-Over-2 is based on Colin Percival's ROMix algorithm which was the
   provably-memory-hard key stretching algorithm that preceded "scrypt."
   ROMix was chosen because of its simplicity, despite its lack of flexibility
   in choosing memory-vs-speed tradeoff.  It is "-over-2" because the number
   of LUT operations is cut in half relative to described ROMix algorithm,
   in order to allow larger memory usage on slower systems.
   """

   FILECODE = 'KDFOBJCT'

   #############################################################################
   def __init__(self, kdfAlgo=None, **params):
      super(KdfObject, self).__init__()

      # Set an error-inducing function as the default KDF
      def errorkdf(x):
         LOGERROR('Using uninitialized KDF!')
         return SecureBinaryData(0)
      self.execKDF = errorkdf


      if kdfAlgo is None:
         # Stay uninitialized
         self.kdfAlgo = ''
         self.kdf = None
         return


      if not kdfAlgo.upper() in KNOWN_KDFALGOS:
         # Make sure we recognize the algo
         LOGERROR('Attempted to create unknown KDF object:  name=%s', kdfAlgo)
         return

      # Check that the keyword args passed to this function includes all
      # required args for the specified KDF algorithm
      reqdArgs = KNOWN_KDFALGOS[kdfAlgo.upper()]
      for arg in reqdArgs:
         if not arg in params:
            LOGERROR('KDF name=%s:  not all required args present', kdfAlgo)
            LOGERROR('KDF name=%s:  missing argument="%s"', kdfAlgo, arg)
            LOGERROR('Required args: "%s"', '", "'.join(reqdArgs))
            raise BadInputError('Insufficient args for %s KDF' % kdfAlgo)


      # Right now there is only one algo (plus identity-KDF).  You can add new
      # algorithms via KNOWN_KDFALGOS and then updating this method to
      # create a callable KDF object
      if kdfAlgo.upper()==NULLKDF:
         self.execKDF = lambda x: SecureBinaryData(x)
      elif kdfAlgo.upper()=='ROMIXOV2':

         memReqd = int(params['memReqd'])
         numIter = params['numIter']
         salt    = params['salt'   ]

         # Make sure that non-SBD input is converted to SBD
         saltSBD = SecureBinaryData(salt)

         if memReqd>2**31:
            raise KdfError('Invalid memory for KDF.  Must be 2GB or less.')

         if saltSBD.getSize()==0:
            raise KdfError('Zero-length salt supplied with KDF')

         self.kdfAlgo = 'ROMIXOV2'
         self.memReqd = memReqd
         self.numIter = numIter
         self.salt    = saltSBD
         self.kdf = KdfRomix(self.memReqd, self.numIter, self.salt)
         self.execKDF = lambda pwd: self.kdf.DeriveKey( SecureBinaryData(pwd) )

      elif kdfAlgo.upper()=='SCRYPT__':
         raise NotImplementedError('scrypt KDF not available yet')
      else:
         raise KdfError('Unrecognized KDF name')


   #############################################################################
   def getKdfID(self):
      return computeChecksum(self.serialize(), 8)

   #############################################################################
   def getEntryID(self):
      return self.getKdfID()

   #############################################################################
   def serialize(self):
      bp = BinaryPacker()
      if self.kdfAlgo.upper()=='ROMIXOV2':
         bp.put(BINARY_CHUNK,  self.kdfAlgo,           width= 8)
         bp.put(BINARY_CHUNK,  'sha512__',             width= 8)
         bp.put(UINT32,        self.memReqd)          #width= 4
         bp.put(UINT32,        self.numIter)          #width= 4
         bp.put(VAR_STR,       self.salt.toBinStr())
      elif self.kdfAlgo.upper()==NULLKDF:
         bp.put(BINARY_CHUNK,  NULLKDF,             width= 8)

      return bp.getBinaryString()

   #############################################################################
   def unserialize(self, toUnpack):
      bu = makeBinaryUnpacker(toUnpack)
      kdfAlgo = bu.get(BINARY_CHUNK, 8)

      if not kdfAlgo.upper() in KNOWN_KDFALGOS:
         LOGERROR('Unknown KDF in unserialize:  %s', kdfAlgo)
         return None

      # Start the KDF-specific processing
      if kdfAlgo.upper()==NULLKDF:
         self.__init__(NULLKDF)
      elif kdfAlgo.upper()=='ROMIXOV2':
         useHash = bu.get(BINARY_CHUNK,  8)
         if not useHash.upper().startswith('SHA512'):
            raise KdfError('ROMIXOV2 KDF only works with sha512: found %s', useHash)

         mem   = bu.get(UINT32)
         nIter = bu.get(UINT32)
         salty = bu.get(VAR_STR)
         self.__init__(kdfAlgo, memReqd=mem, numIter=nIter, salt=salty)

      return self



   #############################################################################
   @staticmethod
   def CreateNewKDF(kdfAlgo, **kdfCreateArgs):
      """
      We'd like this to eventually support lots of KDFs, not just ROMix, but
      at the moment the extra flexibility wo
      """

      LOGINFO("Creating new KDF object")

      if not kdfAlgo.upper() in KNOWN_KDFALGOS:
         raise KdfError('Unknown KDF name in CreateNewKDF:  %s' % kdfAlgo)
         return None

      kdfOut = None

      if kdfAlgo.upper()==NULLKDF:
         LOGINFO('Creating identity KDF')
         kdfOut = KdfObject('Identity')
      elif kdfAlgo.upper()=='SCRYPT__':
         raise NotImplementedError('KDF=scrypt not implemented yet!')
      elif kdfAlgo.upper()=='ROMIXOV2':
         LOGINFO('Creating ROMIXOV2 KDF')
         targSec = float(kdfCreateArgs['targSec'])
         maxMem  = int(kdfCreateArgs['maxMem'])

         if not (0 <= targSec <= 20):
            raise KdfError('Must use 0<time<20 sec.  0 for min settings')

         if not (32*KILOBYTE <= maxMem < 2*GIGABYTE):
            raise KdfError('Must use max memory between 32 kB and 2048 MB')

         kdf = KdfRomix()
         kdf.computeKdfParams(targSec, maxMem)

         mem   = kdf.getMemoryReqtBytes()
         nIter = kdf.getNumIterations()
         salty = kdf.getSalt().toBinStr()
         kdfOut = KdfObject('ROMIXOV2', memReqd=mem, numIter=nIter, salt=salty)

         LOGINFO('Created new KDF with the following parameters:')
         LOGINFO('\tAlgorithm: %s', kdfAlgo)
         LOGINFO('\t  MemReqd: %0.2f MB' % (float(mem)/MEGABYTE))
         LOGINFO('\t  NumIter: %d', nIter)
         LOGINFO('\t  HexSalt: %s', kdf.getSalt().toHexStr())

      return kdfOut



   #############################################################################
   def pprintOneLineStr(self, indent=0):
      if self.kdfAlgo.upper()==NULLKDF:
         return 'KdfObject  NULLKDF'

      if self.kdfAlgo.upper() in [None, '']:
         return 'KdfObject  Uninitialized'

      pcs = []
      pcs.append('KdfObject ')
      pcs.append('ID=%s' % binary_to_hex(self.getKdfID()))
      pcs.append('Algo=%s' % self.kdfAlgo)
      if self.kdfAlgo.upper()=='ROMIXOV2':
         byteStr = bytesToHumanSize(self.memReqd)
         saltStr = self.salt.toHexStr()[:8]
         pcs.append('[%d iter, %s, salt:%s...]' % (self.numIter, byteStr, saltStr))

      return ' '*indent + ', '.join(pcs)


   ##########################################################################
   def getPPrintPairs(self):
      pairs = [['KdfAlgo', self.kdfAlgo]]

      if self.kdfAlgo.upper()=='ROMIXOV2':
         pairs.append( ['NumIter', str(self.numIter)] )
         pairs.append( ['ReqdMem', bytesToHumanSize(self.memReqd)] )
         pairs.append( ['HexSalt', self.salt.toHexStr()] )

      return pairs


#############################################################################
#############################################################################
class EncryptionKey(WalletEntry):
   """
   This is a simple container to hold a 32-byte master encryption key.
   Typically this key will be used to encrypt everything else in the wallet.
   Locking, unlocking, and changing the passphrase will only require operating
   on this master key (for instance, rather than changing the encryption of
   every object in the wallet, we keep it the same, but re-encrypt this master
   key).

   Also includes an optional test string, which can be encrypted at creation
   time to distribute if the passphrase is forgotten, and you want to hire
   computing power to help you recover it.
   """

   FILECODE = 'EKEYREG_'

   #############################################################################
   def __init__(self, keyID=None, ckey=None, einfo=None,
                                    etest=None, ptest=None, keyH3=None):
      super(EncryptionKey, self).__init__()

      # Mostly these will be initialized from encrypted data in wallet file
      self.ekeyID           = keyID   if keyID   else NULLSTR()
      self.masterKeyCrypt   = SecureBinaryData(ckey)  if ckey  else NULLSBD()
      self.testStringEncr   = etest if etest else NULLSTR(0)
      self.testStringPlain  = ptest if ptest else NULLSTR(0)
      self.keyTripleHash    = keyH3 if keyH3 else NULLSTR(0)

      self.keyCryptInfo = ArmoryCryptInfo(None)
      if einfo:
         self.keyCryptInfo = einfo.copy()

      # We may cache the decrypted key
      self.masterKeyPlain      = NULLSBD()
      self.relockAtTime        = 0
      self.lockTimeout         = 10

      self.keyIsInUseRLock  = threading.RLock()

      self.kdfRef = None


   #############################################################################
   def markKeyInUse(self):
      self.keyIsInUseRLock.acquire()


   #############################################################################
   def finishedWithKey(self):
      self.keyIsInUseRLock.release()


   #############################################################################
   def setKdfObjectRef(self, kdf):
      if self.keyCryptInfo.useEncryption() and \
         not kdf.getKdfID() == self.keyCryptInfo.kdfObjID:
         raise KdfError('Attempted to set kdf ref with non-matching ID')

      self.kdfRef = kdf


   #############################################################################
   def linkWalletEntries(self, wltFileRef):
      super(EncryptionKey, self).linkWalletEntries(wltFileRef)
      if self.kdfRef is None:
         self.kdfRef = wltFileRef.kdfMap.get(self.keyCryptInfo.kdfObjID)
         if self.kdfRef is None:
            LOGERROR('Could not find KDF in wallet file')


   #############################################################################
   def getEncryptionKeyID(self):
      if self.ekeyID == NULLSTR():
         if self.isLocked():
            raise EncryptionError('No stored ekey ID, and ekey is locked')

         self.ekeyID = calcEKeyID(self.masterKeyPlain)

      return self.ekeyID

   #############################################################################
   def getEntryID(self):
      return self.getEncryptionKeyID()

   #############################################################################
   @VerifyArgTypes(passphrase=SecureBinaryData)
   def verifyPassphrase(self, passphrase):
      return self.unlock(passphrase, justVerify=True)


   #############################################################################
   @VerifyArgTypes(passphrase=SecureBinaryData)
   def unlock(self, passphrase, kdfObj=None, justVerify=False, timeout=None):
      LOGDEBUG('Unlocking encryption key %s', binary_to_hex(self.ekeyID))

      if timeout is None:
         timeout = self.lockTimeout

      if kdfObj is None:
         kdfObj = self.kdfRef

      if isinstance(kdfObj, dict):
         kdfObj = kdfObj.get(self.keyCryptInfo.kdfObjID, None)

      if kdfObj is None:
         raise KdfError('No KDF avaialble for unlocking ekey object')

      if not kdfObj.getKdfID() == self.keyCryptInfo.kdfObjID:
         raise KdfError('KDF object ID does not match crypt info for ekey')

      self.masterKeyPlain = \
               self.keyCryptInfo.decrypt(self.masterKeyCrypt, passphrase, kdfObj=kdfObj)

      if not calcEKeyID(self.masterKeyPlain) == self.ekeyID:
         LOGERROR('Wrong passphrase passed to EKEY unlock function.')
         self.masterKeyPlain.destroy()
         return False

      if justVerify:
         self.masterKeyPlain.destroy()
      else:
         self.relockAtTime = time.time() + timeout

      return True



   #############################################################################
   def lock(self, forceLock=False):
      """
      This will refuse to lock the ekey if it can't acquire the RLock.  The
      RLock indicates that another thread is currently using the key.
      """
      gotRLock = self.keyIsInUseRLock.acquire(blocking=0)
      if not gotRLock:
         if forceLock:
            LOGCRIT('Locking encryption key despite another thread using it!')
         else:
            return False

      self.masterKeyPlain.destroy()
      if gotRLock:
         self.keyIsInUseRLock.release()
      return True




   #############################################################################
   def getPlainEncryptionKey(self):
      """
      This returns a copy of the master key.  Please destroy when done!
      """
      if self.isLocked():
         raise KeyDataError('Cannot get plain key when locked')

      if self.masterKeyPlain.getSize()==0:
         raise KeyDataError('No plain key data available (uninitialized ekey?)')

      return self.masterKeyPlain.copy()


   #############################################################################
   def setLockTimeout(self, newTimeout):
      self.lockTimeout = max(newTimeout, 3)

   #############################################################################
   def checkLockTimeout(self):
      """ timeout=0 means never expires """
      if self.lockTimeout<=0:
         return

      if time.time() > self.relockAtTime:
         self.lock(forceLock=False)


   #############################################################################
   def isLocked(self):
      return (self.masterKeyPlain.getSize() == 0)


   #############################################################################
   def serialize(self):
      bp = BinaryPacker()
      bp.put(BINARY_CHUNK, self.ekeyID, width=8)
      bp.put(VAR_STR,      self.masterKeyCrypt.toBinStr())
      bp.put(BINARY_CHUNK, self.keyCryptInfo.serialize(), 32)
      bp.put(VAR_STR,      self.testStringEncr)
      bp.put(VAR_STR,      self.testStringPlain)
      bp.put(VAR_STR,      self.keyTripleHash)
      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, strData):
      bu = makeBinaryUnpacker(strData)
      ekeyID   = bu.get(BINARY_CHUNK,  8)
      cryptKey = bu.get(VAR_STR)
      einfoStr = bu.get(BINARY_CHUNK, 32)
      eteststr = bu.get(VAR_STR)
      pteststr = bu.get(VAR_STR)
      keyHash3 = bu.get(VAR_STR)

      einfo = ArmoryCryptInfo().unserialize(einfoStr)

      self.__init__(ekeyID, cryptKey, einfo, eteststr, pteststr, keyHash3)
      return self


   #############################################################################
   @VerifyArgTypes(passphrase=SecureBinaryData,
                   preGenKey=[SecureBinaryData, None])
   def createNewMasterKey(self, kdfObj, encryptEKeyAlgo, passphrase,
                           withTestString=False,
                           preGenKey=None, preGenIV8=None):
      """
      This method assumes you already have a KDF you want to use and is
      referenced by the first arg.  If not, please create the KDF and
      add it to the wallet first before using this method.

      Generally, ArmoryCryptInfo objects can have a null KDF, but master
      encryption keys are almost always protected by a passphrase so it
      will use a KDF.

      You can provide pre-generated key and IV, if you are simply trying
      to update the password or KDF options on an existing key (typically
      you don't need to provide the same IV, but it helps to be able to
      for testing)
      """

      LOGINFO('Generating new master key')

      # Check that we recognize the encryption algorithm
      # This is the algorithm used to encrypt the master key itself
      if not encryptEKeyAlgo in KNOWN_CRYPTO:
         raise UnrecognizedCrypto('Unknown encrypt algo: %s' % encryptEKeyAlgo)


      # Generate the IV to be used for encrypting the master key with pwd
      if preGenIV8 is None:
         newIV = SecureBinaryData().GenerateRandom(8).toBinStr()
      else:
         if isinstance(preGenIV8, SecureBinaryData):
            preGenIV8 = preGenIV8.toBinStr()

         if not len(preGenIV8)==8:
            raise InitVectError('Expected 8-byte preGenIV input')

         newIV = preGenIV8

      # Create the object that explains how this master key will be encrypted
      self.keyCryptInfo = ArmoryCryptInfo(kdfObj.getKdfID(), encryptEKeyAlgo,
                                                             'PASSWORD', newIV)

      expectKeySize = KNOWN_CRYPTO[encryptEKeyAlgo]['keysize']

      # Create the master key itself
      if preGenKey is None:
         newMaster = SecureBinaryData().GenerateRandom2xXOR(expectKeySize)
      else:
         if not preGenKey.getSize() == expectKeySize:
            raise KeyDataError('Expected Master key: %dB, got %dB' % \
                                    (expectKeySize, preGenKey.getSize()))
         newMaster = preGenKey.copy()


      self.ekeyID = calcEKeyID(newMaster)
      self.masterKeyCrypt = self.keyCryptInfo.encrypt( \
                                       newMaster, passphrase, kdfObj=kdfObj)

      # We might have decided to encrypt a test string with this key, so that
      # later if the user forgets their password they can distribute just the
      # test string to be brute-force decrypted (instead of their full wallet)
      if not withTestString:
         self.testStringPlain = NULLSTR(0)
         self.testStringEncr  = NULLSTR(0)
         self.keyTripleHash   = NULLSTR(0)
      else:
         # Note1: We are using the ID of the encryption key as the IV for
         #        the test string (it will be expanded by the encrypt func)
         # Note2: We use the encrypted test string essentially as a unique
         #        salt for this wallet for the triple-hashed key.
         #        It seems unnecessary since the master key should be a
         #        true 32-bytes random (how would it not be?) but it doesn't
         #        hurt either.  If/when we put out a bounty/reward script,
         #        the claimant will have to put (masterKey||testStrEncr)
         #        onto the stack, which will be hashed three times and
         #        compared against self.keyTripleHash.
         # Note3: Disabled test-string related code because ... it's very
         #        low priority, and probably not really worth the effort!
         raise NotImplementedError
         minfo = ArmoryCryptInfo(NULLKDF, encryptEKeyAlgo, 'RAWKEY32', self.ekeyID)
         rand16 = SecureBinaryData().GenerateRandom(16)
         self.testStringPlain = SecureBinaryData('ARMORYENCRYPTION') + rand16
         self.testStringEncr  = minfo.encrypt(self.testStringPlain, newMaster)
         self.keyTripleHash   = hash160(hash256(hash256(newMaster.toBinStr() + \
                                                        self.testStringEncr)))

      # We should have an encrypted version now, so we can wipe the plaintext
      newMaster.destroy()

      LOGINFO('Finished creating new master key:')
      LOGINFO('\tKDF:     %s', binary_to_hex(kdfObj.getKdfID()))
      LOGINFO('\tCrypto:  %s', encryptEKeyAlgo)
      LOGINFO('\tTestStr: %s', binary_to_hex(self.testStringPlain[16:]))

      # For convenience, we store a ref to the KDF object with this.
      # When we later pull from disk, we'll need to explicitly make the
      # call below, or pass the kdf object in with the unlock() calls
      self.setKdfObjectRef(kdfObj)

      return self



   #############################################################################
   @VerifyArgTypes(oldPass=SecureBinaryData,
                   newPass=[SecureBinaryData, None])
   def changeEncryptionParams(self, oldPass, newPass=None, oldKdf=None,
                     newKdf=None, newEncryptAlgo=None, useSameIV=False):
      """
      Pass in the same object for old and new if you want to keep the same
      passphrase but change the KDF
      """

      if newPass is None:
         newPass = oldPass

      if (oldPass==newPass) and (newKdf is None) and (newEncryptAlgo is None):
         self.lock()
         raise EncryptionError('No crypt/passphrase params to change!')

      if oldKdf is None:
         oldKdf = self.kdfRef

      if oldKdf is None: #still
         raise KdfError('Cannot change encryption without old KDF object')

      if newKdf is None:
         newKdf = oldKdf

      if newEncryptAlgo is None:
         newEncryptAlgo = self.keyCryptInfo.encryptAlgo

      if useSameIV:
         # This is mainly used for unit-testing, so we can predict the output
         # On the other hand, this isn't necessarily unsafe
         newIV8 = self.keyCryptInfo.ivSource
      else:
         newIV8 = SecureBinaryData().GenerateRandom(8)


      if not self.unlock(oldPass):
         raise PassphraseError('Wrong passphrase given')

      try:
         withTest = (len(self.testStringEncr) != 0)

         # Not creating a new key, but the process is the same; use preGenKey arg
         self.createNewMasterKey(newKdf,
                                 newEncryptAlgo,
                                 newPass,
                                 withTest,
                                 preGenKey=self.masterKeyPlain,
                                 preGenIV8=newIV8)
      finally:
         self.lock(newPass)



   ############################################################################
   def pprintOneLineStr(self, indent=0):
      if self.ekeyID == NULLSTR():
         return ' '*indent + 'EkeyObject, Uninitialized'

      pcs = []
      pcs.append('EkeyObject')
      pcs.append('ID=%s' % binary_to_hex(self.ekeyID))

      if self.keyCryptInfo.kdfObjID == NULLKDF:
         pcs.append('KdfID=<NULLKDF>')
      else:
         pcs.append('KdfID=%s...' % binary_to_hex(self.keyCryptInfo.kdfObjID)[:8])

      pcs.append('EncrKey: %s...' % self.masterKeyCrypt.toHexStr()[:8])


      return ' '*indent + ', '.join(pcs)


   ##########################################################################
   def getPPrintPairs(self):
      pairs = [ ['CryptInfo', self.keyCryptInfo.getPPrintStr()],
                ['EncryptedKey', self.masterKeyCrypt.toHexStr()] ]

      return pairs


###############################################################################
class MultiPwdEncryptionKey(EncryptionKey):
   """
   So there is a master encryption key for your wallet.
   The key itself is never stored anywhere, only the M-of-N fragments of it.
   The fragments are stored on disk, each encrypted with a different password.

   So instead of:

      ekeyInfo | encryptedMasterKey

   we will have:

      ekeyInfo0 | keyFrag0 | ekeyInfo1 | keyFrag1 | ...


   We intentionally do not have a way to verify if an individual password
   is correct without having a quorum of correct passwords.  This makes
   sure that master key is effectively encrypted with the entropy of
   M passwords, instead of M keys each encrypted with the entropy of one
   password (reduced ever-so-slightly if M != N)

   """

   FILECODE = 'EKEYMOFN'

   #############################################################################
   def __init__(self, keyID=None, mkeyID=None, M=None,
                     einfoFrags=None, efragList=None, keyLabelList=None):
      """
      einfoMaster is the encryption used to encrypt the master key (raw AES key)
      einfoFrags is the encryption used for each fragment (password w/ KDF)

      When this method is called with args, usually after reading the encrypted
      data from file.
      """
      super(MultiPwdEncryptionKey, self).__init__()

      self.ekeyID = keyID  if keyID  else NULLSTR()
      self.mkeyID = mkeyID if mkeyID else NULLSTR()
      self.M      = M if M else 0
      self.N      = len(einfoFrags) if einfoFrags else 0

      if efragList and not isinstance(efragList, (list,tuple)):
         raise BadInputError('Need list of einfo & SBD objs for frag list')

      # This contains the encryption/decryption params for each key frag
      self.einfos = []
      if einfoFrags:
         self.einfos = [e.copy() for e in einfoFrags]

      # The actual encryption fragments
      self.efrags = []
      if efragList:
         self.efrags = [SecureBinaryData(f) for f in efragList]

      # The actual encryption fragments
      self.labels = []
      if keyLabelList:
         self.labels = keyLabelList[:]


      # If the object is unlocked, we'll store a the plain master key here
      self.masterKeyPlain      = NULLSBD()
      self.relockAtTime        = 0
      self.lockTimeout         = 10


      self.keyIsInUseRLock  = threading.RLock()


      # List of references to KDF objects, usually set after reading from file
      # Alternatively, if these are None, the kdfs can be passed in during
      # unlock()
      self.kdfRefList = []



   #############################################################################
   def setKdfObjectRefList(self, newList):
      # Make sure we're copying references to the KDFs
      self.kdfRefList = []
      for kdf in newList:
         self.kdfRefList.append(kdf)

   #############################################################################
   def linkWalletEntries(self, wltFileRef):
      # super() would inherit EncryptionKey class method, which is not suited
      # for this method.  Instead, we do the WalletEntry class method directly.
      WalletEntry.linkWalletEntries(self, wltFileRef)
      if len(self.kdfRefList) == 0:
         for aci in self.einfos:
            kdfref = wltFileRef.kdfMap.get(aci.kdfObjID)
            if kdfref is None:
               LOGERROR('Could not find KDF in wallet file')
            self.kdfRefList.append(kdfref)


   #############################################################################
   def verifyPassphrase(self, sbdUnlockObjs, kdfObjList=None):
      return self.unlock(sbdUnlockObjs, kdfObjList=kdfObjList, justVerify=True)


   #############################################################################
   def getPlainFragList(self, sbdUnlockObjs, kdfObjList=None):
      origFrags = []
      try:
         ###########
         # Check KDFs and unlock wallet
         if kdfObjList is None:
            kdfObjList = self.kdfRefList

         if not self.unlock(sbdUnlockObjs, kdfObjList=kdfObjList):
            raise PassphraseError('Not all passwords/frags valid')


         ###########
         # We know the pwds/frags were correct or unlock() would've failed
         # Now we can re-decrypt some frags and verify new frags match
         origFrags = []
         for i in range(self.N):
            unlockObjType,unlockData = sbdUnlockObjs[i]
            if unlockObjType==MPEK_FRAG_TYPE.NONE:
               origFrags.append(NULLSBD())
            elif unlockObjType==MPEK_FRAG_TYPE.PASSWORD:
               ysbd = self.einfos[i].decrypt(self.efrags[i],
                                             unlockData,
                                             kdfObj=kdfObjList[i])
               origFrags.append(ysbd)
            elif unlockObjType==MPEK_FRAG_TYPE.PLAINFRAG:
               origFrags.append(unlockData.copy())
            elif unlockObjType==MPEK_FRAG_TYPE.FRAGKEY:
               # This object is the output of the KDF(password)
               # This requires us to sidestep the einfo object, which
               # wasn't designed to allow post-KDF inputs.
               rawACI = ArmoryCryptInfo(NULLKDF,
                                        self.einfos[i].encryptAlgo,
                                        'RAWKEY32',
                                        self.einfos[i].ivSource)
               pfrag = rawACI.decrypt(self.efrags[i], unlockData, kdfObjList[i])
               origFrags.append(pfrag)


         ###########
         # Re-frag the master key
         keysz = self.masterKeyPlain.getSize()
         refrags = SplitSecret(self.masterKeyPlain.toBinStr(), self.M, self.N, keysz)
         refrags = [SecureBinaryData(pair[1]) for pair in refrags]


         ###########
         # Now check that all supplied pwds/frags match the new frags
         for i in range(self.N):
            if origFrags[i].getSize() == 0:
               continue

            if not refrags[i] == origFrags[i]:
               raise KeyDataError('New frags of master key do not match!')

         return refrags
      finally:
         for f in origFrags:
            f.destroy()
         origFrags = None
         self.lock()


   #############################################################################
   def getFragEncryptionKey(self, fragIndex, sbdUnlockObjs, kdfObjList=None):
      """
      This method returns the output of the password for the given frag index
      passed through the proper KDF.  This means that not only does the wallet
      need to be unlocked, one of the unlock objects needs to be the password!
      """
      unlockType,sbdPassword = sbdUnlockObjs[fragIndex]
      if not unlockType==MPEK_FRAG_TYPE.PASSWORD:
         raise EncryptionError('Cannot get ekey for frag without password')

      plainFrags = []
      try:
         # This will throw an error if the unlock list is invalid
         plainFrags = self.getPlainFragList(sbdUnlockObjs, kdfObjList)

         fkey = self.kdfRefList[fragIndex].execKDF(sbdUnlockObjs[fragIndex][1])

         # Test that the frag-key actually works:
         rawACI = ArmoryCryptInfo(NULLKDF,
                                  self.einfos[fragIndex].encryptAlgo,
                                  'RAWKEY32',
                                  self.einfos[fragIndex].ivSource)
         recryptFrag = rawACI.encrypt(plainFrags[fragIndex], fkey)

         if not recryptFrag == self.efrags[fragIndex]:
            raise EncryptionError('Re-encrypted fragment does not match')

         return fkey

      finally:
         for f in plainFrags:
            f.destroy()
         plainFrags = []



   #############################################################################
   def getFragID_X(self, i):
      baseStr =  binary_to_base58(hash256(self.efrags[i].toBinStr()))[:5]
      return baseStr + '-%d' % (i+1)

   #############################################################################
   def getFragID_Y(self, i):
      return binary_to_base58(self.mkeyID)[:5] + '-%d' % (i+1)

   #############################################################################
   def getKeyfileName(self, ftype, i, wltID=''):
      if wltID:
         wltID += '-'

      if ftype.lower()=='x':
         return 'X-keyfile-%s%s.xkey' % (wltID, self.getFragID_X(i))
      else:
         return 'Y-keyfile-%s%s.ykey' % (wltID, self.getFragID_Y(i))


   #############################################################################
   @VerifyArgTypes(kdfObjList=[list, tuple, dict, None])
   def unlock(self, sbdUnlockObjs, kdfObjList=None, justVerify=False):
      """
      NOTE:  You can actually pass in a map of KDF objects (indexed by KDF ID),
      and this function will fill the kdf list for you

      We use "sbdUnlockObjs" instead of "passwords" because we might be
      passing in some raw fragments, not encrypted with a password.  This
      would be used in the event that some users forgot their password
      and are using backup data (saved at password-creation time).  This is
      NOT the master key fragments, but instead fragments of the encryption
      key used to encrypt the master key.

      So, if we have a 3-of-5 multi-pwd key, and two users enter passwords
      and one has a raw fragment, sbdUnlockObjs looks like the following:

         [ [MPEK_FRAG_TYPE.PASSWORD,    SBD('mySup3rS3curePwd')]
           [MPEK_FRAG_TYPE.NONE,        ''                     ]
           [MPEK_FRAG_TYPE.NONE,        ''                     ]
           [MPEK_FRAG_TYPE.PASSWORD,    SBD('password1')       ]
           [MPEK_FRAG_TYPE.PLAINFRAG,   SBD(<raw32bytefrag>)   ] ]
      """
      LOGDEBUG('Unlocking multi-encrypt key %s', binary_to_hex(self.ekeyID))

      if self.M==0 or self.N==0:
         raise BadInputError('Multi-encrypt master key not initialized')


      ###########
      # Make sure all the KDFs are available and IDs match
      if kdfObjList is None:
         if len(self.kdfRefList) < self.N:
            raise KdfError('Insufficient KDFs to unlock multi-pwd key')
         kdfRefs = self.kdfRefList[:]
      elif isinstance(kdfObjList, (tuple,list)):
         kdfRefs = kdfObjList[:]
      else:  # must be dict since VerifyArgTypes would stop everything else
         kdfRefs = []
         for i in range(self.N):
            thisKdf = kdfObjList.get(self.einfos[i].kdfObjID, None)
            if thisKdf is None:
               raise KdfError('Missing at least one KDF in multi pwd key')
            kdfRefs.append(thisKdf)

      for i in range(self.N):
         if not kdfRefs[i].getKdfID() == self.einfos[i].kdfObjID:
            raise KdfError('KDF #%d ID does not match expected!' % i)


      ###########
      # Count the total number of available passwords and plain/backup frags
      if len(sbdUnlockObjs) < self.N:
         raise PassphraseError('Must provide N-size list of pwds, with empties')

      npwd = 0
      for i in range(self.N):
         npwd += 0 if sbdUnlockObjs[i][0]==MPEK_FRAG_TYPE.NONE else 1

      if npwd < self.M:
         raise PassphraseError('Insufficient pwds/frags to decrypt master key')

      ###########
      # Use passwords to decrypt fragments, reconstruct key from frags
      try:
         pfrags = []
         for i in range(self.N):
            ptype,sbdData = sbdUnlockObjs[i]

            # X-values are actaully 1-indexed, so add one
            xvalBin = int_to_binary(i+1, endOut=BIGENDIAN)

            if ptype==MPEK_FRAG_TYPE.PLAINFRAG:
               pfrags.append([xvalBin, sbdData.toBinStr()])
            elif ptype==MPEK_FRAG_TYPE.PASSWORD:
               ysbd = self.einfos[i].decrypt(self.efrags[i],
                                             sbdData,
                                             kdfObj=kdfRefs[i])
               pfrags.append([xvalBin, ysbd.toBinStr()])
            elif ptype==MPEK_FRAG_TYPE.FRAGKEY:
               # This object is the output of the KDF(password)
               # This requires us to sidestep the einfo object, which
               # wasn't designed to allow post-KDF inputs.
               rawACI = ArmoryCryptInfo(None,
                                        self.einfos[i].encryptAlgo,
                                        'RAWKEY32',
                                        self.einfos[i].ivSource)
               ysbd = rawACI.decrypt(self.efrags[i], sbdData)
               pfrags.append([xvalBin, ysbd.toBinStr()])



         # Reconstruct the master encryption key from the decrypted fragments
         lenFirstYvalue = len(pfrags[0][1])
         self.masterKeyPlain = SecureBinaryData( \
                           ReconstructSecret(pfrags, self.M, lenFirstYvalue))

         if not calcEKeyID(self.masterKeyPlain)==self.ekeyID:
            LOGERROR('Not all passphrases correct.')
            self.masterKeyPlain.destroy()
            return False

         if justVerify:
            self.masterKeyPlain.destroy()
         else:
            self.relockAtTime = RightNow() + self.lockTimeout

      except:
         LOGEXCEPT('Failed to unlock wallet')
         self.masterKeyPlain.destroy()
         return False
      finally:
         # Always clear the decrypted fragments
         pfrags = None

      return True


   #############################################################################
   def lock(self):
      LOGDEBUG('Locking encryption key %s', binary_to_hex(self.ekeyID))
      self.masterKeyPlain.destroy()
      return True


   #############################################################################
   def serialize(self):
      bp = BinaryPacker()
      bp.put(BINARY_CHUNK, self.ekeyID, width= 8)
      bp.put(BINARY_CHUNK, self.mkeyID, width= 8)
      bp.put(UINT8,        self.M)
      bp.put(UINT8,        self.N)
      for i in range(self.N):
         bp.put(BINARY_CHUNK, self.einfos[i].serialize(), width=32)
         bp.put(VAR_STR,      self.efrags[i].toBinStr())
         bp.put(VAR_UNICODE,  self.labels[i])

      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, strData):
      bu = makeBinaryUnpacker(strData)
      ekeyID = bu.get(BINARY_CHUNK,  8)
      mkeyID = bu.get(BINARY_CHUNK,  8)
      M      = bu.get(UINT8)
      N      = bu.get(UINT8)

      einfos = []
      efrags = []
      labels = []
      for i in range(N):
         einfos.append(ArmoryCryptInfo().unserialize(bu.get(BINARY_CHUNK, 32)))
         efrags.append(SecureBinaryData(bu.get(VAR_STR)))
         labels.append(bu.get(VAR_UNICODE))

      self.__init__(ekeyID, mkeyID, M, einfos, efrags, labels)
      return self


   #############################################################################
   def createNewMasterKey(self, kdfList, encryptFragAlgo,
                            M, sbdPasswdList, labelList,
                            preGenKey=None, preGenIV8List=None):

      """
      This method assumes you already have a KDF you want to use and is
      referenced by the first arg.  If not, please create the KDF and
      add it to the wallet first (and register it with KdfObject before
      using this method).  All passwords are stretched with the same KDF,
      though they will use different salt, and hence need diff einfo objects.

      You can provide pre-generated key and IV, if you are simply trying
      to update the password or KDF options on an existing key (typically
      you don't need to provide the same IV, but it helps to be able to
      for testing)
      """

      LOGINFO('Generating new multi-password master key')

      N = len(sbdPasswdList)

      # Confirm we have N passwords and N labels
      if not len(labelList)==N:
         raise BadInputError('Expected %d labels, only %d provided' % \
                                          (N, len(labelList)))

      if 0 in [p.getSize() for p in sbdPasswdList]:
         raise BadInputError('At least one passphrase is empty')

      # Check that we recognize the encryption algorithm
      # This will be AES256CBC, etc... used to encrypt frags
      if not encryptFragAlgo in KNOWN_CRYPTO:
         LOGERROR('Unrecognized crypto algorithm: %s', encryptFragAlgo)
         raise UnrecognizedCrypto


      # Create the master key itself
      expectKeySize = KNOWN_CRYPTO[encryptFragAlgo]['keysize']
      if preGenKey is None:
         newMaster = SecureBinaryData().GenerateRandom2xXOR(expectKeySize)
      else:
         if not preGenKey.getSize() == expectKeySize:
            raise KeyDataError('Expected Master key: %dB, got %dB' % \
                                    (expectKeySize, preGenKey.getSize()))
         newMaster = preGenKey.copy()


      # Generate the IV to be used for encrypting the master key with pwd
      if preGenIV8List is None:
         new8bytes = lambda: SecureBinaryData().GenerateRandom(8).toBinStr()
         newIV8List = [new8bytes() for i in range(N)]
      else:
         if not len(preGenIV8List)==N:
            raise InitVectError('Did not supply enough IVs for new key')

         newIV8List = []
         for iv in preGenIV8List:
            ivStr = iv.toBinStr() if isinstance(iv,SecureBinaryData) else iv[:]

            if not len(ivStr)==8:
               raise InitVectError('Expected 8-byte preGenIV input')

            newIV8List.append(ivStr)

      # Here's the magic:  splitting the secret into M-of-N fragments
      plainFrags = SplitSecret(newMaster.toBinStr(), M, N, expectKeySize)

      # Now encrypt the fragments with the passwords
      self.efrags = []
      self.einfos = []
      self.labels = []

      for i in range(N):
         einfo = ArmoryCryptInfo(kdfList[i].getKdfID(), encryptFragAlgo,
                                                        'PASSWORD', newIV8List[i])
         # We store just the y-value:  the x-value is just i+1
         pfrag = SecureBinaryData(plainFrags[i][1])
         efrag = einfo.encrypt(pfrag, sbdPasswdList[i], kdfObj=kdfList[i])

         self.efrags.append(efrag)
         self.einfos.append(einfo)
         self.labels.append(labelList[i])
         pfrag.destroy()

      # Forget the plain frags
      plainFrags = None

      self.ekeyID = calcEKeyID(newMaster)
      self.mkeyID = calcEKeyID(SecureBinaryData(newMaster.toBinStr() + \
                                                int_to_binary(M)))
      # Technically, if we only increased N but nothing else, the original
      # fragments of the MKEY would remain valid, hence the mkeyID should
      # stay the same.  I suppose there could be a case where someone
      # changes just the N-value, expecting to get a whole new set of
      # fragments and end up thinking there's a bug because the old
      # fragments are the same and still work...


      # Make sure we keep refs to each kdf object
      self.setKdfObjectRefList(kdfList)
      self.M = M
      self.N = len(sbdPasswdList)

      LOGINFO('New multipwd master key ID: %s' % binary_to_hex(self.ekeyID))

      return self


   #############################################################################
   def changeSomePasswords(self, oldPwds, newPwds, kdfList=None, newLabels=None):
      """
      This might be used in the situation that one or more of the pwd-holders
      forgets their password.  As long as there's still M people who know their
      password, they can reset any/all of the passwords

      As before, the old password list still must have N elements, but only
      M of them need to be non-empty.  This is because the index in the
      password list is the X-value used for SSS reconstruction.

      NOTE:  It's strictly possible to change just one password without
             needing M passwords to unlock the master key, as long as we
             know that one password.  We would simply decrypt
             the one fragment and re-encrypt with the new password.  But
             this can't be done safely, because we've guaranteed that there
             is no way to detect if a single password is correct.  If the
             person enters their old password incorrectly, the decrypted
             fragment is incorrect, and we will end up encrypting an
             incorrect fragment.  Therefore, we force having M signatures
             present to change any passphrases.


      oldPwds has the standard unlock form:  fragtype-pwd pairs:
         [ [MPEK_FRAG_TYPE.PASSWORD,    SBD('mySup3rS3curePwd')]
           [MPEK_FRAG_TYPE.NONE,        ''                     ]
           [MPEK_FRAG_TYPE.NONE,        ''                     ]
           [MPEK_FRAG_TYPE.PASSWORD,    SBD('password1')       ]
           [MPEK_FRAG_TYPE.PLAINFRAG,   SBD(<raw32bytefrag>)   ] ]

      newPwds is just a raw list of SecureBinaryData objects, with NULLSBD
      objects for passwords we don't want to change.  As long as enough
      passwords/frags are provided to decrypt the master key, then any
      passwords can be changed, even those that weren't entered.

      Since we are unlocking some fragments, we can use those fragments
      to double-check that regenerated/re-encrypted fragments are correct.
      They are calculated deterministically, but it doesn't hurt to add
      some extra checks.
      """
      if kdfList is None:
         kdfList = self.kdfRefList

      sbdFragList = []
      try:
         sbdFragList = self.getPlainFragList(oldPwds, kdfList)

         ###########
         # Re-encrypt any frags for which newPwds[i] is non-empty.  It's okay
         # to keep the same encryption and kdfs as before.  The only "issue"
         # is that if one person "changes" their password to the same password,
         # then the # encrypted fragment will be the same as the previous since
         # the KDF salt and encryption IVs are also the same.  Someone tracking
         # the encrypted frags will know that the password wasn't really
         # changed.  This is not a meaningful issue.
         for i in range(self.N):
            if newPwds[i].getSize() > 0:
               self.efrags[i].destroy()
               self.efrags[i] = self.einfos[i].encrypt(sbdFragList[i],
                                                       newPwds[i],
                                                       kdfObj=kdfList[i])

         ###########
         # Update any labels if necessary
         if not newLabels is None:
            self.labels = newLabels[:]

      finally:
         for f in sbdFragList:
            f.destroy()
         sbdFragList = None
         self.lock()


   #############################################################################
   def changeMultiEncryption(self, oldKdfs, oldPwds,
                  newKdfs, newEncryptAlgo, newM, newPwds, newLabels):
      """
      There are two types of changes:  one where only some passwords need to
      be changed, and the other is a replacement of the encryption params
      entirely, such as changing from 2-of-3 to 3-of-5.  In the first
      case, we only need M passwords, and then we can change any subset of
      passwords (even those not entered).  To do this, use the method
      self.changeSomePasswords().

      This function is used for the second case, where we are refragmenting
      the master key, and re-encrypting all the fragments.  We can also use
      this to simply change the KDF params or encryption algorithm.

      We still only need M old passwords to do this, but we will need all
      N new passwords in order to re-fragment and re-encrypt.


      oldpwds must be of the form needed for self.unlock().  newPwds must
      be a list of SBD passwords, all non-empty

      """

      ###########
      # Make sure we can unlock the master key in order to change it
      if oldKdfs is None:
         if self.kdfRefList is None:
            raise KdfError('No kdfs available for unlocking password')
         else:
            oldKdfs = self.kdfRefList

      if not self.verifyPassphrase(oldPwds, kdfObjList=oldKdfs):
         raise PassphraseError('At least one passphrase was wrong!')


      ###########
      if newEncryptAlgo is None:
         newEncryptAlgo = self.einfos[0].encryptAlgo

      if newLabels is None:
         newLabels = self.labels[:]

      if sum([ (1 if p.getSize()==0 else 0)  for p in newPwds]) > 0:
         raise PassphraseError('All new passwords must be non-empty')

      try:
         if not self.unlock(oldPwds):
            raise PassphraseError('At least one passphrase was wrong!')


         # Not creating new key, but the process is the same; use preGenKey arg
         #createNewMasterKey(kdfList, encryptFragAlgo,
                            #M, sbdPasswdList, labelList,
                            #preGenKey=None, preGenIV8List=None):
         self.createNewMasterKey(newKdfs,
                                 newEncryptAlgo,
                                 newM,
                                 newPwds,
                                 newLabels,
                                 preGenKey=self.masterKeyPlain)
      finally:
         self.lock()



