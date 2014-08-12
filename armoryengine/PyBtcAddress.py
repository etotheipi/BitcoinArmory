################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
from CppBlockUtils import SecureBinaryData, CryptoAES, CryptoECDSA
from armoryengine.ArmoryUtils import ADDRBYTE, hash256, binary_to_base58, \
   KeyDataError, RightNow, LOGERROR, ChecksumError, convertKeyDataToAddress, \
   verifyChecksum, WalletLockError, createDERSigFromRS, binary_to_int, \
   computeChecksum, getVersionInt, PYBTCWALLET_VERSION, bitset_to_int, \
   LOGDEBUG, Hash160ToScrAddr, int_to_bitset, UnserializeError, \
   hash160_to_addrStr, int_to_binary, BIGENDIAN, \
   BadAddressError, checkAddrStrValid, binary_to_hex
from armoryengine.BinaryPacker import BinaryPacker, UINT8, UINT16, UINT32, UINT64, \
   INT8, INT16, INT32, INT64, VAR_INT, VAR_STR, FLOAT, BINARY_CHUNK
from armoryengine.BinaryUnpacker import BinaryUnpacker
from armoryengine.Timer import TimeThisFunction
import CppBlockUtils as Cpp


#############################################################################
def calcWalletIDFromRoot(root, chain):
   """ Helper method for computing a wallet ID """
   root  = PyBtcAddress().createFromPlainKeyData(SecureBinaryData(root))
   root.chaincode = SecureBinaryData(chain)
   first = root.extendAddressChain()
   return binary_to_base58((ADDRBYTE + first.getAddr160()[:5])[::-1])

class PyBtcAddress(object):
   """
   PyBtcAddress --

   This class encapsulated EVERY kind of address object:
      -- Plaintext private-key-bearing addresses
      -- Encrypted private key addresses, with AES locking and unlocking
      -- Watching-only public-key addresses
      -- Address-only storage, representing someone else's key
      -- Deterministic address generation from previous addresses
      -- Serialization and unserialization of key data under all conditions
      -- Checksums on all serialized fields to protect against HDD byte errors

      For deterministic wallets, new addresses will be created from a chaincode
      and the previous address.  What is implemented here is a special kind of
      deterministic calculation that actually allows the user to securely
      generate new addresses even if they don't have the private key.  This
      method uses Diffie-Hellman shared-secret calculations to produce the new
      keys, and has the same level of security as all other ECDSA operations.
      There's a lot of fantastic benefits to doing this:

         (1) If all addresses in wallet are chained, then you only need to backup
             your wallet ONCE -- when you first create it.  Print it out, put it
             in a safety-deposit box, or tattoo the generator key to the inside
             of your eyelid:  it will never change.

         (2) You can keep your private keys on an offline machine, and keep a
             watching-only wallet online.  You will be able to generate new
             keys/addresses, and verify incoming transactions, without ever
             requiring your private key to touch the internet.

         (3) If your friend has the chaincode and your first public key, they
             too can generate new addresses for you -- allowing them to send
             you money multiple times, with different addresses, without ever
             needing to specifically request the addresses.
             (the downside to this is if the chaincode is compromised, all
             chained addresses become de-anonymized -- but is only a loss of
             privacy, not security)

      However, we do require some fairly complicated logic, due to the fact
      that a user with a full, private-key-bearing wallet, may try to generate
      a new key/address without supplying a passphrase.  If this happens, the
      wallet logic gets very complicated -- we don't want to reject the request
      to generate a new address, but we can't compute the private key until the
      next time the user unlocks their wallet.  Thus, we have to save off the
      data they will need to create the key, to be applied on next unlock.
   """

   #############################################################################
   def __init__(self):
      """
      We use SecureBinaryData objects to store pub, priv and IV objects,
      because that is what is required by the C++ code.  See EncryptionUtils.h
      to see that available methods.
      """
      self.addrStr20             = ''
      self.binPublicKey65        = SecureBinaryData()  # 0x04 X(BE) Y(BE)
      self.binPrivKey32_Encr     = SecureBinaryData()  # BIG-ENDIAN
      self.binPrivKey32_Plain    = SecureBinaryData()
      self.binInitVect16         = SecureBinaryData()
      self.isLocked              = False
      self.useEncryption         = False
      self.isInitialized         = False
      self.keyChanged            = False   # ...since last key encryption
      self.walletByteLoc         = -1
      self.chaincode             = SecureBinaryData()
      self.chainIndex            = 0

      # Information to be used by C++ to know where to search for transactions
      # in the blockchain (disabled in favor of a better search method)
      self.timeRange = [2**32-1, 0]
      self.blkRange  = [2**32-1, 0]

      # This feels like a hack, but it's the only way I can think to handle
      # the case of generating new, chained addresses, even without the
      # private key currently in memory.  i.e. - If we can't unlock the priv
      # key when creating a new chained priv key, we will simply extend the
      # public key, and store the last-known chain info, so that it can be
      # generated the next time the address is unlocked
      self.createPrivKeyNextUnlock             = False
      self.createPrivKeyNextUnlock_IVandKey    = [None, None] # (IV,Key)
      self.createPrivKeyNextUnlock_ChainDepth  = -1

   #############################################################################
   def isInitialized(self):
      """ Keep track of whether this address has been initialized """
      return self.isInitialized

   #############################################################################
   def hasPrivKey(self):
      """
      We have a private key if either the plaintext, or ciphertext private-key
      fields are non-empty.  We also consider ourselves to "have" the private
      key if this address was chained from a key that has the private key, even
      if we haven't computed it yet (due to not having unlocked the private key
      before creating the new address).
      """
      return (self.binPrivKey32_Encr.getSize()  != 0 or \
              self.binPrivKey32_Plain.getSize() != 0 or \
              self.createPrivKeyNextUnlock)

   #############################################################################
   def hasPubKey(self):
      return (self.binPublicKey65.getSize() != 0)


   ##############################################################################
   def getPubKey(self):
      '''Return the uncompressed public key of the address.'''
      if self.binPublicKey65.getSize() != 65:
         raise KeyDataError, 'PyBtcAddress does not have a public key!'
      return self.binPublicKey65


   #############################################################################
   def hasChainCode(self):
      '''Return a boolean indicating if the address has a chain code.'''
      return (self.chaincode.getSize() != 0)


   #############################################################################
   def getChainCode(self):
      '''Return the chain code of the address.'''
      if len(self.chaincode) != 32:
         raise KeyDataError, 'PyBtcAddress does not have a chain code!'
      return self.chaincode


   #############################################################################
   def getAddrStr(self, netbyte=ADDRBYTE):
      chksum = hash256(netbyte + self.addrStr20)[:4]
      return binary_to_base58(netbyte + self.addrStr20 + chksum)

   #############################################################################
   def getAddr160(self):
      if len(self.addrStr20)!=20:
         raise KeyDataError, 'PyBtcAddress does not have an address string!'
      return self.addrStr20


   #############################################################################
   def isCompressed(self):
      # Armory wallets (v1.35) do not support compressed keys
      return False 
   

   #############################################################################
   def touch(self, unixTime=None, blkNum=None):
      """
      Just like "touching" a file, this makes sure that the firstSeen and
      lastSeen fields for this address are updated to include "now"

      If we include only a block number, we will fill in the timestamp with
      the unix-time for that block (if the BlockDataManager is availabled)
      """
      if self.blkRange[0]==0:
         self.blkRange[0]=2**32-1
      if self.timeRange[0]==0:
         self.timeRange[0]=2**32-1

      if blkNum==None:
         if TheBDM.getBDMState()=='BlockchainReady':
            topBlk = TheBDM.getTopBlockHeight()
            self.blkRange[0] = long(min(self.blkRange[0], topBlk))
            self.blkRange[1] = long(max(self.blkRange[1], topBlk))
      else:
         self.blkRange[0]  = long(min(self.blkRange[0], blkNum))
         self.blkRange[1]  = long(max(self.blkRange[1], blkNum))

         if unixTime==None and TheBDM.getBDMState()=='BlockchainReady':
            unixTime = TheBDM.getHeaderByHeight(blkNum).getTimestamp()

      if unixTime==None:
         unixTime = RightNow()

      self.timeRange[0] = long(min(self.timeRange[0], unixTime))
      self.timeRange[1] = long(max(self.timeRange[1], unixTime))



   #############################################################################
   def copy(self):
      newAddr = PyBtcAddress().unserialize(self.serialize())
      newAddr.binPrivKey32_Plain = self.binPrivKey32_Plain.copy()
      newAddr.binPrivKey32_Encr  = self.binPrivKey32_Encr.copy()
      newAddr.binPublicKey65     = self.binPublicKey65.copy()
      newAddr.binInitVect16      = self.binInitVect16.copy()
      newAddr.isLocked           = self.isLocked
      newAddr.useEncryption      = self.useEncryption
      newAddr.isInitialized      = self.isInitialized
      newAddr.keyChanged         = self.keyChanged
      newAddr.walletByteLoc      = self.walletByteLoc
      newAddr.chaincode          = self.chaincode
      newAddr.chainIndex         = self.chainIndex
      return newAddr



   #############################################################################
   def getTimeRange(self):
      return self.timeRange

   #############################################################################
   def getBlockRange(self):
      return self.blkRange

   #############################################################################
   def serializePublicKey(self):
      """Converts the SecureBinaryData public key to a 65-byte python string"""
      return self.binPublicKey65.toBinStr()

   #############################################################################
   def serializeEncryptedPrivateKey(self):
      """Converts SecureBinaryData encrypted private key to python string"""
      return self.binPrivKey32_Encr.toBinStr()

   #############################################################################
   # NOTE:  This method should rarely be used, unless we are only printing it
   #        to the screen.  Actually, it will be used for unencrypted wallets
   def serializePlainPrivateKey(self):
      return self.binPrivKey32_Plain.toBinStr()

   def serializeInitVector(self):
      return self.binInitVect16.toBinStr()


   #############################################################################
   def verifyEncryptionKey(self, secureKdfOutput):
      """
      Determine if this data is the decryption key for this encrypted address
      """
      if not self.useEncryption or not self.hasPrivKey():
         return False

      if self.useEncryption and not secureKdfOutput:
         LOGERROR('No encryption key supplied to verifyEncryption!')
         return False


      decryptedKey = CryptoAES().DecryptCFB( self.binPrivKey32_Encr, \
                                             SecureBinaryData(secureKdfOutput), \
                                             self.binInitVect16)
      verified = False

      if not self.isLocked:
         if decryptedKey==self.binPrivKey32_Plain:
            verified = True
      else:
         computedPubKey = CryptoECDSA().ComputePublicKey(decryptedKey)
         if self.hasPubKey():
            verified = (self.binPublicKey65==computedPubKey)
         else:
            verified = (computedPubKey.getHash160()==self.addrStr20)
            if verified:
               self.binPublicKey65 = computedPubKey

      decryptedKey.destroy()
      return verified



   #############################################################################
   def setInitializationVector(self, IV16=None, random=False, force=False):
      """
      Either set the IV through input arg, or explicitly call random=True
      Returns the IV -- which is especially important if it is randomly gen

      This method is mainly for PREVENTING you from changing an existing IV
      without meaning to.  Losing the IV for encrypted data is almost as bad
      as losing the encryption key.  Caller must use force=True in order to
      override this warning -- otherwise this method will abort.
      """
      if self.binInitVect16.getSize()==16:
         if self.isLocked:
            LOGERROR('Address already locked with different IV.')
            LOGERROR('Changing IV may cause loss of keydata.')
         else:
            LOGERROR('Address already contains an initialization')
            LOGERROR('vector.  If you change IV without updating')
            LOGERROR('the encrypted storage, you may permanently')
            LOGERROR('lose the encrypted data')

         if not force:
            LOGERROR('If you really want to do this, re-execute this call with force=True')
            return ''

      if IV16:
         self.binInitVect16 = SecureBinaryData(IV16)
      elif random==True:
         self.binInitVect16 = SecureBinaryData().GenerateRandom(16)
      else:
         raise KeyDataError, 'setInitVector: set IV data, or random=True'
      return self.binInitVect16

   #############################################################################
   def enableKeyEncryption(self, IV16=None, generateIVIfNecessary=False):
      """
      setIV method will raise error is we don't specify any args, but it is
      acceptable HERE to not specify any args just to enable encryption
      """
      self.useEncryption = True
      if IV16:
         self.setInitializationVector(IV16)
      elif generateIVIfNecessary and self.binInitVect16.getSize()<16:
         self.setInitializationVector(random=True)
   

   #############################################################################
   def isKeyEncryptionEnabled(self):
      return self.useEncryption

   #############################################################################
   def createFromEncryptedKeyData(self, addr20, encrPrivKey32, IV16, \
                                                     chkSum=None, pubKey=None):
      # We expect both private key and IV to the right size
      assert(encrPrivKey32.getSize()==32)
      assert(IV16.getSize()==16)
      self.__init__()
      self.addrStr20     = addr20
      self.binPrivKey32_Encr = SecureBinaryData(encrPrivKey32)
      self.setInitializationVector(IV16)
      self.isLocked      = True
      self.useEncryption = True
      self.isInitialized = True
      if chkSum and not self.binPrivKey32_Encr.getHash256().startswith(chkSum):
         raise ChecksumError, "Checksum doesn't match encrypted priv key data!"
      if pubKey:
         self.binPublicKey65 = SecureBinaryData(pubKey)
         if not self.binPublicKey65.getHash160()==self.addrStr20:
            raise KeyDataError, "Public key does not match supplied address"

      return self


   #############################################################################
   def createFromPlainKeyData(self, plainPrivKey, addr160=None, willBeEncr=False, \
                                    generateIVIfNecessary=False, IV16=None, \
                                    chksum=None, publicKey65=None, \
                                    skipCheck=False, skipPubCompute=False):

      assert(plainPrivKey.getSize()==32)

      if not addr160:
         addr160 = convertKeyDataToAddress(privKey=plainPrivKey)

      self.__init__()
      self.addrStr20 = addr160
      self.isInitialized = True
      self.binPrivKey32_Plain = SecureBinaryData(plainPrivKey)
      self.isLocked = False

      if willBeEncr:
         self.enableKeyEncryption(IV16, generateIVIfNecessary)
      elif IV16:
         self.binInitVect16 = IV16

      if chksum and not verifyChecksum(self.binPrivKey32_Plain.toBinStr(), chksum):
         raise ChecksumError, "Checksum doesn't match plaintext priv key!"
      if publicKey65:
         self.binPublicKey65 = SecureBinaryData(publicKey65)
         if not self.binPublicKey65.getHash160()==self.addrStr20:
            raise KeyDataError, "Public key does not match supplied address"
         if not skipCheck:
            if not CryptoECDSA().CheckPubPrivKeyMatch(self.binPrivKey32_Plain,\
                                                      self.binPublicKey65):
               raise KeyDataError, 'Supplied pub and priv key do not match!'
      elif not skipPubCompute:
         # No public key supplied, but we do want to calculate it
         self.binPublicKey65 = CryptoECDSA().ComputePublicKey(plainPrivKey)

      return self


   #############################################################################
   def createFromPublicKeyData(self, publicKey65, chksum=None):

      assert(publicKey65.getSize()==65)
      self.__init__()
      self.addrStr20 = publicKey65.getHash160()
      self.binPublicKey65 = publicKey65
      self.isInitialized = True
      self.isLocked = False
      self.useEncryption = False

      if chksum and not verifyChecksum(self.binPublicKey65.toBinStr(), chksum):
         raise ChecksumError, "Checksum doesn't match supplied public key!"

      return self


   
   #############################################################################
   def safeExtendPrivateKey(self, privKey, chn, pubKey=None):
      # We do this computation twice, in case one is somehow corrupted
      # (Must be ultra paranoid with computing keys)
      logMult1 = SecureBinaryData()
      logMult2 = SecureBinaryData()
      a160hex = ''
   
      # Can provide a pre-computed public key to skip that part of the compute
      if pubKey is None:
         pubKey = SecureBinaryData(0)
      else:
         a160hex = binary_to_hex(pubKey.getHash160())

      newPriv1 = CryptoECDSA().ComputeChainedPrivateKey(privKey, chn, pubKey, logMult1)
      newPriv2 = CryptoECDSA().ComputeChainedPrivateKey(privKey, chn, pubKey, logMult2)

      if newPriv1==newPriv2:
         newPriv2.destroy()
         with open(MULT_LOG_FILE,'a') as f:
            f.write('PrvChain (pkh, mult): %s,%s\n' % (a160hex,logMult1.toHexStr()))
         return newPriv1

      else:
         LOGCRIT('Chaining failed!  Computed keys are different!')
         LOGCRIT('Recomputing chained key 3 times; bail if they do not match')
         newPriv1.destroy()
         newPriv2.destroy()
         logMult3 = SecureBinaryData()
         newPriv1 = CryptoECDSA().ComputeChainedPrivateKey(privKey, chn, pubKey, logMult1)
         newPriv2 = CryptoECDSA().ComputeChainedPrivateKey(privKey, chn, pubKey, logMult2)
         newPriv3 = CryptoECDSA().ComputeChainedPrivateKey(privKey, chn, pubKey, logMult3)
         LOGCRIT('   Multiplier1: ' + logMult1.toHexStr())
         LOGCRIT('   Multiplier2: ' + logMult2.toHexStr())
         LOGCRIT('   Multiplier3: ' + logMult3.toHexStr())

         if newPriv1==newPriv2 and newPriv1==newPriv3:
            newPriv2.destroy()
            newPriv3.destroy()
            with open(MULT_LOG_FILE,'a') as f:
               f.write('PrvChain (pkh, mult): %s,%s\n' % (a160hex,logMult1.toHexStr()))
            return newPriv1
         else:
            LOGCRIT('Chaining failed again!  Returning empty private key.')
            newPriv1.destroy()
            newPriv2.destroy()
            newPriv3.destroy()
            # This should crash just about any process that would try to use it
            # without checking for empty private key. 
            return SecureBinaryData(0)
      

   #############################################################################
   def safeExtendPublicKey(self, pubKey, chn):
      # We do this computation twice, in case one is somehow corrupted
      # (Must be ultra paranoid with computing keys)
      a160hex = binary_to_hex(pubKey.getHash160())
      logMult1 = SecureBinaryData()
      logMult2 = SecureBinaryData()
      newPub1 = CryptoECDSA().ComputeChainedPublicKey(pubKey, chn, logMult1)
      newPub2 = CryptoECDSA().ComputeChainedPublicKey(pubKey, chn, logMult2)

      if newPub1==newPub2:
         newPub2.destroy()
         with open(MULT_LOG_FILE,'a') as f:
            f.write('PubChain (pkh, mult): %s,%s\n' % (a160hex, logMult1.toHexStr()))
         return newPub1
      else:
         LOGCRIT('Chaining failed!  Computed keys are different!')
         LOGCRIT('Recomputing chained key 3 times; bail if they do not match')
         newPub1.destroy()
         newPub2.destroy()
         logMult3 = SecureBinaryData()
         newPub1 = CryptoECDSA().ComputeChainedPublicKey(pubKey, chn, logMult1)
         newPub2 = CryptoECDSA().ComputeChainedPublicKey(pubKey, chn, logMult2)
         newPub3 = CryptoECDSA().ComputeChainedPublicKey(pubKey, chn, logMult3)
         LOGCRIT('   Multiplier1: ' + logMult1.toHexStr())
         LOGCRIT('   Multiplier2: ' + logMult2.toHexStr())
         LOGCRIT('   Multiplier3: ' + logMult3.toHexStr())

         if newPub1==newPub2 and newPub1==newPub3:
            newPub2.destroy()
            newPub3.destroy()
            with open(MULT_LOG_FILE,'a') as f:
               f.write('PubChain (pkh, mult): %s,%s\n' % (a160hex, logMult1.toHexStr()))
            return newPub1
         else:
            LOGCRIT('Chaining failed again!  Returning empty public key.')
            newPub1.destroy()
            newPub2.destroy()
            newPub3.destroy()
            # This should crash just about any process that would try to use it
            # without checking for empty public key. 
            return SecureBinaryData(0)

   #############################################################################
   def lock(self, secureKdfOutput=None, generateIVIfNecessary=False):
      # We don't want to destroy the private key if it's not supposed to be
      # encrypted.  Similarly, if we haven't actually saved the encrypted
      # version, let's not lock it
      newIV = False
      if not self.useEncryption or not self.hasPrivKey():
         # This isn't supposed to be encrypted, or there's no privkey to encrypt
         return
      else:
         if self.binPrivKey32_Encr.getSize()==32 and not self.keyChanged:
            # Addr should be encrypted, and we already have encrypted priv key
            self.binPrivKey32_Plain.destroy()
            self.isLocked = True
         elif self.binPrivKey32_Plain.getSize()==32:
            # Addr should be encrypted, but haven't computed encrypted value yet
            if secureKdfOutput!=None:
               # We have an encryption key, use it
               if self.binInitVect16.getSize() < 16:
                  if not generateIVIfNecessary:
                     raise KeyDataError, 'No Initialization Vector available'
                  else:
                     self.binInitVect16 = SecureBinaryData().GenerateRandom(16)
                     newIV = True

               # Finally execute the encryption
               self.binPrivKey32_Encr = CryptoAES().EncryptCFB( \
                                                self.binPrivKey32_Plain, \
                                                SecureBinaryData(secureKdfOutput), \
                                                self.binInitVect16)
               # Destroy the unencrypted key, reset the keyChanged flag
               self.binPrivKey32_Plain.destroy()
               self.isLocked = True
               self.keyChanged = False
            else:
               # Can't encrypt the addr because we don't have encryption key
               raise WalletLockError, ("\n\tTrying to destroy plaintext key, but no"
                                       "\n\tencrypted key data is available, and no"
                                       "\n\tencryption key provided to encrypt it.")


      # In case we changed the IV, we should let the caller know this
      return self.binInitVect16 if newIV else SecureBinaryData()


   #############################################################################
   def unlock(self, secureKdfOutput, skipCheck=False):
      """
      This method knows nothing about a key-derivation function.  It simply
      takes in an AES key and applies it to decrypt the data.  However, it's
      best if that AES key is actually derived from "heavy" key-derivation
      function.
      """
      if not self.useEncryption or not self.isLocked:
         # Bail out if the wallet is unencrypted, or already unlocked
         self.isLocked = False
         return


      if self.createPrivKeyNextUnlock:
         # This is SPECIFICALLY for the case that we didn't have the encr key
         # available when we tried to extend our deterministic wallet, and
         # generated a new address anyway
         self.binPrivKey32_Plain = CryptoAES().DecryptCFB( \
                                     self.createPrivKeyNextUnlock_IVandKey[1], \
                                     SecureBinaryData(secureKdfOutput), \
                                     self.createPrivKeyNextUnlock_IVandKey[0])

         for i in range(self.createPrivKeyNextUnlock_ChainDepth):
            #self.binPrivKey32_Plain = CryptoECDSA().ComputeChainedPrivateKey( \
                                         #self.binPrivKey32_Plain, \
                                         #self.chaincode)

            self.binPrivKey32_Plain = self.safeExtendPrivateKey( \
                                         self.binPrivKey32_Plain, \
                                         self.chaincode)


         # IV should have already been randomly generated, before
         self.isLocked = False
         self.createPrivKeyNextUnlock            = False
         self.createPrivKeyNextUnlock_IVandKey   = []
         self.createPrivKeyNextUnlock_ChainDepth = 0

         # Lock/Unlock to make sure encrypted private key is filled
         self.lock(secureKdfOutput,generateIVIfNecessary=True)
         self.unlock(secureKdfOutput)

      else:

         if not self.binPrivKey32_Encr.getSize()==32:
            raise WalletLockError, 'No encrypted private key to decrypt!'

         if not self.binInitVect16.getSize()==16:
            raise WalletLockError, 'Initialization Vect (IV) is missing!'

         self.binPrivKey32_Plain = CryptoAES().DecryptCFB( \
                                        self.binPrivKey32_Encr, \
                                        secureKdfOutput, \
                                        self.binInitVect16)

      self.isLocked = False

      if not skipCheck:
         if not self.hasPubKey():
            self.binPublicKey65 = CryptoECDSA().ComputePublicKey(\
                                                      self.binPrivKey32_Plain)
         else:
            # We should usually check that keys match, but may choose to skip
            # if we have a lot of keys to load
            # NOTE:  I run into this error if I fill the keypool without first
            #        unlocking the wallet.  I'm not sure why it doesn't work 
            #        when locked (it should), but this wallet format has been
            #        working flawless for almost a year... and will be replaced
            #        soon, so I won't sweat it.
            if not CryptoECDSA().CheckPubPrivKeyMatch(self.binPrivKey32_Plain, \
                                            self.binPublicKey65):
               raise KeyDataError, "Stored public key does not match priv key!"



   #############################################################################
   def changeEncryptionKey(self, secureOldKey, secureNewKey):
      """
      We will use None to specify "no encryption", either for old or new.  Of
      course we throw an error is old key is "None" but the address is actually
      encrypted.
      """
      if not self.hasPrivKey():
         raise KeyDataError, 'No private key available to re-encrypt'

      if not secureOldKey and self.useEncryption and self.isLocked:
         raise WalletLockError, 'Need old encryption key to unlock private keys'

      wasLocked = self.isLocked

      # Decrypt the original key
      if self.isLocked:
         self.unlock(secureOldKey, skipCheck=False)

      # Keep the old IV if we are changing the key.  IV reuse is perfectly
      # fine for a new key, and might save us from disaster if we otherwise
      # generated a new one and then forgot to take note of it.
      self.keyChanged = True
      if not secureNewKey:
         # If we chose not to re-encrypt, make sure we clear the encryption
         self.binInitVect16     = SecureBinaryData()
         self.binPrivKey32_Encr = SecureBinaryData()
         self.isLocked          = False
         self.useEncryption     = False
      else:
         # Re-encrypt with new key (using same IV)
         self.useEncryption = True
         self.lock(secureNewKey)  # do this to make sure privKey_Encr filled
         if wasLocked:
            self.isLocked = True
         else:
            self.unlock(secureNewKey)
            self.isLocked = False




   #############################################################################
   # This is more of a static method
   def checkPubPrivKeyMatch(self, securePriv, securePub):
      CryptoECDSA().CheckPubPrivKeyMatch(securePriv, securePub)



   #############################################################################
   @TimeThisFunction
   def generateDERSignature(self, binMsg, secureKdfOutput=None):
      """
      This generates a DER signature for this address using the private key.
      Obviously, if we don't have the private key, we throw an error.  Or if
      the wallet is locked and no encryption key was provided.

      If an encryption key IS provided, then we unlock the address just long
      enough to sign the message and then re-lock it
      """

      if not self.hasPrivKey():
         raise KeyDataError, 'Cannot sign for address without private key!'

      if self.isLocked:
         if secureKdfOutput==None:
            raise WalletLockError, "Cannot sign Tx when private key is locked!"
         else:
            # Wallet is locked but we have a decryption key
            self.unlock(secureKdfOutput, skipCheck=False)

      try:
         secureMsg = SecureBinaryData(binMsg)
         sig = CryptoECDSA().SignData(secureMsg, self.binPrivKey32_Plain)
         sigstr = sig.toBinStr()

         rBin   = sigstr[:32 ]
         sBin   = sigstr[ 32:]
         return createDERSigFromRS(rBin, sBin)

      except:
         LOGERROR('Failed signature generation')
      finally:
         # Always re-lock/cleanup after unlocking, even after an exception.
         # If locking triggers an error too, we will just skip it.
         try:
            if secureKdfOutput!=None:
               self.lock(secureKdfOutput)
         except:
            LOGERROR('Error re-locking address')
            pass




   #############################################################################
   @TimeThisFunction
   def verifyDERSignature(self, binMsgVerify, derSig):
      if not self.hasPubKey():
         raise KeyDataError, 'No public key available for this address!'

      rBin, sBin = getRSFromDERSig(derSig)

      secMsg    = SecureBinaryData(binMsgVerify)
      secSig    = SecureBinaryData(rBin + sBin)
      secPubKey = SecureBinaryData(self.binPublicKey65)
      return CryptoECDSA().VerifyData(secMsg, secSig, secPubKey)

   #############################################################################
   def markAsRootAddr(self, chaincode):
      if not chaincode.getSize()==32:
         raise KeyDataError, 'Chaincode must be 32 bytes'
      else:
         self.chainIndex = -1
         self.chaincode  = chaincode


   #############################################################################
   def isAddrChainRoot(self):
      return (self.chainIndex==-1)

   #############################################################################
   @TimeThisFunction
   def extendAddressChain(self, secureKdfOutput=None, newIV=None):
      """
      We require some fairly complicated logic here, due to the fact that a
      user with a full, private-key-bearing wallet, may try to generate a new
      key/address without supplying a passphrase.  If this happens, the wallet
      logic gets mucked up -- we don't want to reject the request to
      generate a new address, but we can't compute the private key until the
      next time the user unlocks their wallet.  Thus, we have to save off the
      data they will need to create the key, to be applied on next unlock.
      """
      if not self.chaincode.getSize() == 32:
         raise KeyDataError, 'No chaincode has been defined to extend chain'

      newAddr = PyBtcAddress()
      privKeyAvailButNotDecryptable = (self.hasPrivKey() and \
                                       self.isLocked     and \
                                       not secureKdfOutput  )


      if self.hasPrivKey() and not privKeyAvailButNotDecryptable:
         # We are extending a chain using private key data
         wasLocked = self.isLocked
         if self.useEncryption and self.isLocked:
            if not secureKdfOutput:
               raise WalletLockError, 'Cannot create new address without passphrase'
            self.unlock(secureKdfOutput)
         if not newIV:
            newIV = SecureBinaryData().GenerateRandom(16)

         if self.hasPubKey():
            #newPriv = CryptoECDSA().ComputeChainedPrivateKey( \
                                    #self.binPrivKey32_Plain, \
                                    #self.chaincode, \
                                    #self.binPublicKey65)
            newPriv = self.safeExtendPrivateKey( \
                                    self.binPrivKey32_Plain, \
                                    self.chaincode, \
                                    self.binPublicKey65)
         else:
            #newPriv = CryptoECDSA().ComputeChainedPrivateKey( \
                                    #self.binPrivKey32_Plain, \
                                    #self.chaincode)
            newPriv = self.safeExtendPrivateKey( \
                                    self.binPrivKey32_Plain, \
                                    self.chaincode)

         newPub  = CryptoECDSA().ComputePublicKey(newPriv)
         newAddr160 = newPub.getHash160()
         newAddr.createFromPlainKeyData(newPriv, newAddr160, \
                                       IV16=newIV, publicKey65=newPub)

         newAddr.addrStr20 = newPub.getHash160()
         newAddr.useEncryption = self.useEncryption
         newAddr.isInitialized = True
         newAddr.chaincode     = self.chaincode
         newAddr.chainIndex    = self.chainIndex+1

         # We can't get here without a secureKdfOutput (I think)
         if newAddr.useEncryption:
            newAddr.lock(secureKdfOutput)
            if not wasLocked:
               newAddr.unlock(secureKdfOutput)
               self.unlock(secureKdfOutput)
         return newAddr
      else:
         # We are extending the address based solely on its public key
         if not self.hasPubKey():
            raise KeyDataError, 'No public key available to extend chain'

         #newAddr.binPublicKey65 = CryptoECDSA().ComputeChainedPublicKey( \
                                    #self.binPublicKey65, self.chaincode)
         newAddr.binPublicKey65 = self.safeExtendPublicKey( \
                                    self.binPublicKey65, self.chaincode)

         newAddr.addrStr20 = newAddr.binPublicKey65.getHash160()
         newAddr.useEncryption = self.useEncryption
         newAddr.isInitialized = True
         newAddr.chaincode  = self.chaincode
         newAddr.chainIndex = self.chainIndex+1


         if privKeyAvailButNotDecryptable:
            # *** store what is needed to recover key on next addr unlock ***
            newAddr.isLocked      = True
            newAddr.useEncryption = True
            if not newIV:
               newIV = SecureBinaryData().GenerateRandom(16)
            newAddr.binInitVect16 = newIV
            newAddr.createPrivKeyNextUnlock           = True
            newAddr.createPrivKeyNextUnlock_IVandKey = [None,None]
            if self.createPrivKeyNextUnlock:
               # We are chaining from address also requiring gen on next unlock
               newAddr.createPrivKeyNextUnlock_IVandKey[0] = \
                  self.createPrivKeyNextUnlock_IVandKey[0].copy()
               newAddr.createPrivKeyNextUnlock_IVandKey[1] = \
                  self.createPrivKeyNextUnlock_IVandKey[1].copy()
               newAddr.createPrivKeyNextUnlock_ChainDepth = \
                  self.createPrivKeyNextUnlock_ChainDepth+1
            else:
               # The address from which we are extending has already been generated
               newAddr.createPrivKeyNextUnlock_IVandKey[0] = self.binInitVect16.copy()
               newAddr.createPrivKeyNextUnlock_IVandKey[1] = self.binPrivKey32_Encr.copy()
               newAddr.createPrivKeyNextUnlock_ChainDepth  = 1
         return newAddr


   def serialize(self):
      """
      We define here a binary serialization scheme that will write out ALL
      information needed to completely reconstruct address data from file.
      This method returns a string, but presumably will be used to write addr
      data to file.  The following format is used.

         Address160  (20 bytes) :  The 20-byte hash of the public key
                                   This must always be the first field
         AddressChk  ( 4 bytes) :  Checksum to make sure no error in addr160
         AddrVersion ( 4 bytes) :  Early version don't specify encrypt params
         Flags       ( 8 bytes) :  Addr-specific info, including encrypt params

         ChainCode   (32 bytes) :  For extending deterministic wallets
         ChainChk    ( 4 bytes) :  Checksum for chaincode
         ChainIndex  ( 8 bytes) :  Index in chain if deterministic addresses
         ChainDepth  ( 8 bytes) :  How deep addr is in chain beyond last
                                   computed private key (if base address was
                                   locked when we tried to extend/chain it)

         InitVect    (16 bytes) :  Initialization vector for encryption
         InitVectChk ( 4 bytes) :  Checksum for IV
         PrivKey     (32 bytes) :  Private key data (may be encrypted)
         PrivKeyChk  ( 4 bytes) :  Checksum for private key data

         PublicKey   (65 bytes) :  Public key for this address
         PubKeyChk   ( 4 bytes) :  Checksum for private key data


         FirstTime   ( 8 bytes) :  The first time  addr was seen in blockchain
         LastTime    ( 8 bytes) :  The last  time  addr was seen in blockchain
         FirstBlock  ( 4 bytes) :  The first block addr was seen in blockchain
         LastBlock   ( 4 bytes) :  The last  block addr was seen in blockchain
      """

      serializeWithEncryption = self.useEncryption

      if self.useEncryption and \
         self.binPrivKey32_Encr.getSize()==0 and \
         self.binPrivKey32_Plain.getSize()>0:
         LOGERROR('')
         LOGERROR('***WARNING: you have chosen to serialize a key you hope to be')
         LOGERROR('            encrypted, but have not yet chosen a passphrase for')
         LOGERROR('            it.  The only way to serialize this address is with ')
         LOGERROR('            the plaintext keys.  Please lock this address at')
         LOGERROR('            least once in order to enable encrypted output.')
         serializeWithEncryption = False

      # Before starting, let's construct the flags for this address
      nFlagBytes = 8
      flags = [False]*nFlagBytes*8
      flags[0] = self.hasPrivKey()
      flags[1] = self.hasPubKey()
      flags[2] = serializeWithEncryption
      flags[3] = self.createPrivKeyNextUnlock
      flags = ''.join([('1' if f else '0') for f in flags])

      def raw(a):
         if isinstance(a, str):
            return a
         else:
            return a.toBinStr()

      def chk(a):
         if isinstance(a, str):
            return computeChecksum(a,4)
         else:
            return computeChecksum(a.toBinStr(),4)

      # Use BinaryPacker "width" fields to guaranteee BINARY_CHUNK width.
      # Sure, if we have malformed data we might cut some of it off instead
      # of writing it to the binary stream.  But at least we'll ALWAYS be
      # able to determine where each field is, and will never corrupt the
      # whole wallet so badly we have to go hex-diving to figure out what
      # happened.
      binOut = BinaryPacker()
      binOut.put(BINARY_CHUNK,   self.addrStr20,                    width=20)
      binOut.put(BINARY_CHUNK,   chk(self.addrStr20),               width= 4)
      binOut.put(UINT32,         getVersionInt(PYBTCWALLET_VERSION))
      binOut.put(UINT64,         bitset_to_int(flags))

      # Write out address-chaining parameters (for deterministic wallets)
      binOut.put(BINARY_CHUNK,   raw(self.chaincode),               width=32)
      binOut.put(BINARY_CHUNK,   chk(self.chaincode),               width= 4)
      binOut.put(INT64,          self.chainIndex)
      binOut.put(INT64,          self.createPrivKeyNextUnlock_ChainDepth)

      # Write out whatever is appropriate for private-key data
      # Binary-unpacker will write all 0x00 bytes if empty values are given
      if serializeWithEncryption:
         if self.createPrivKeyNextUnlock:
            binOut.put(BINARY_CHUNK,   raw(self.createPrivKeyNextUnlock_IVandKey[0]), width=16)
            binOut.put(BINARY_CHUNK,   chk(self.createPrivKeyNextUnlock_IVandKey[0]), width= 4)
            binOut.put(BINARY_CHUNK,   raw(self.createPrivKeyNextUnlock_IVandKey[1]), width=32)
            binOut.put(BINARY_CHUNK,   chk(self.createPrivKeyNextUnlock_IVandKey[1]), width= 4)
         else:
            binOut.put(BINARY_CHUNK,   raw(self.binInitVect16),     width=16)
            binOut.put(BINARY_CHUNK,   chk(self.binInitVect16),     width= 4)
            binOut.put(BINARY_CHUNK,   raw(self.binPrivKey32_Encr), width=32)
            binOut.put(BINARY_CHUNK,   chk(self.binPrivKey32_Encr), width= 4)
      else:
         binOut.put(BINARY_CHUNK,   raw(self.binInitVect16),        width=16)
         binOut.put(BINARY_CHUNK,   chk(self.binInitVect16),        width= 4)
         binOut.put(BINARY_CHUNK,   raw(self.binPrivKey32_Plain),   width=32)
         binOut.put(BINARY_CHUNK,   chk(self.binPrivKey32_Plain),   width= 4)

      binOut.put(BINARY_CHUNK, raw(self.binPublicKey65),            width=65)
      binOut.put(BINARY_CHUNK, chk(self.binPublicKey65),            width= 4)

      binOut.put(UINT64, self.timeRange[0])
      binOut.put(UINT64, self.timeRange[1])
      binOut.put(UINT32, self.blkRange[0])
      binOut.put(UINT32, self.blkRange[1])

      return binOut.getBinaryString()

   #############################################################################
   def scanBlockchainForAddress(self, abortIfBDMBusy=False):
      """
      This method will return null output if the BDM is currently in the
      middle of a scan.  You can use waitAsLongAsNecessary=True if you
      want to wait for the previous scan AND the next scan.  Otherwise,
      you can check for bal==-1 and then try again later...

      This is particularly relevant if you know that an address has already
      been scanned, and you expect this method to return immediately.  Thus,
      you don't want to wait for any scan at all...

      This one-stop-shop method has to be blocking.  You might want to
      register the address and rescan asynchronously, skipping this method
      entirely:

         cppWlt = Cpp.BtcWallet()
         cppWlt.addScrAddress_1_(Hash160ToScrAddr(self.getAddr160()))
         TheBDM.registerScrAddr(Hash160ToScrAddr(self.getAddr160()))
         TheBDM.rescanBlockchain(wait=False)

         <... do some other stuff ...>

         if TheBDM.getBDMState()=='BlockchainReady':
            TheBDM.updateWalletsAfterScan(wait=True) # fast after a rescan
            bal      = cppWlt.getBalance('Spendable')
            utxoList = cppWlt.getUnspentTxOutList()
         else:
            <...come back later...>

      """
      if TheBDM.getBDMState()=='BlockchainReady' or \
                            (TheBDM.isScanning() and not abortIfBDMBusy):
         LOGDEBUG('Scanning blockchain for address')

         # We are expecting this method to return balance
         # and UTXO data, so we must make sure we're blocking.
         cppWlt = Cpp.BtcWallet()
         cppWlt.addScrAddress_1_(Hash160ToScrAddr(self.getAddr160()))
         TheBDM.registerWallet(cppWlt, wait=True)
         TheBDM.scanBlockchainForTx(cppWlt, wait=True)

         utxoList = cppWlt.getSpendableTxOutList()
         bal = cppWlt.getSpendableBalance(0, IGNOREZC)
         return (bal, utxoList)
      else:
         return (-1, [])

   #############################################################################
   def unserialize(self, toUnpack):
      """
      We reconstruct the address from a serialized version of it.  See the help
      text for "serialize()" for information on what fields need to
      be included and the binary mapping

      We verify all checksums, correct for one byte errors, and raise exceptions
      for bigger problems that can't be fixed.
      """
      if isinstance(toUnpack, BinaryUnpacker):
         serializedData = toUnpack
      else:
         serializedData = BinaryUnpacker( toUnpack )


      def chkzero(a):
         """
         Due to fixed-width fields, we will get lots of zero-bytes
         even when the binary data container was empty
         """
         if a.count('\x00')==len(a):
            return ''
         else:
            return a


      # Start with a fresh new address
      self.__init__()

      self.addrStr20 = serializedData.get(BINARY_CHUNK, 20)
      chkAddr20      = serializedData.get(BINARY_CHUNK,  4)

      addrVerInt     = serializedData.get(UINT32)
      flags          = serializedData.get(UINT64)
      self.addrStr20 = verifyChecksum(self.addrStr20, chkAddr20)
      flags = int_to_bitset(flags, widthBytes=8)

      # Interpret the flags
      containsPrivKey              = (flags[0]=='1')
      containsPubKey               = (flags[1]=='1')
      self.useEncryption           = (flags[2]=='1')
      self.createPrivKeyNextUnlock = (flags[3]=='1')

      addrChkError = False
      if len(self.addrStr20)==0:
         addrChkError = True
         if not containsPrivKey and not containsPubKey:
            raise UnserializeError, 'Checksum mismatch in addrStr'



      # Write out address-chaining parameters (for deterministic wallets)
      self.chaincode   = chkzero(serializedData.get(BINARY_CHUNK, 32))
      chkChaincode     =         serializedData.get(BINARY_CHUNK,  4)
      self.chainIndex  =         serializedData.get(INT64)
      depth            =         serializedData.get(INT64)
      self.createPrivKeyNextUnlock_ChainDepth = depth

      # Correct errors, convert to secure container
      self.chaincode = SecureBinaryData(verifyChecksum(self.chaincode, chkChaincode))


      # Write out whatever is appropriate for private-key data
      # Binary-unpacker will write all 0x00 bytes if empty values are given
      iv      = chkzero(serializedData.get(BINARY_CHUNK, 16))
      chkIv   =         serializedData.get(BINARY_CHUNK,  4)
      privKey = chkzero(serializedData.get(BINARY_CHUNK, 32))
      chkPriv =         serializedData.get(BINARY_CHUNK,  4)
      iv      = SecureBinaryData(verifyChecksum(iv, chkIv))
      privKey = SecureBinaryData(verifyChecksum(privKey, chkPriv))

      # If this is SUPPOSED to contain a private key...
      if containsPrivKey:
         if privKey.getSize()==0:
            raise UnserializeError, 'Checksum mismatch in PrivateKey '+\
                                    '('+hash160_to_addrStr(self.addrStr20)+')'

         if self.useEncryption:
            if iv.getSize()==0:
               raise UnserializeError, 'Checksum mismatch in IV ' +\
                                    '('+hash160_to_addrStr(self.addrStr20)+')'
            if self.createPrivKeyNextUnlock:
               self.createPrivKeyNextUnlock_IVandKey[0] = iv.copy()
               self.createPrivKeyNextUnlock_IVandKey[1] = privKey.copy()
            else:
               self.binInitVect16     = iv.copy()
               self.binPrivKey32_Encr = privKey.copy()
         else:
            self.binInitVect16      = iv.copy()
            self.binPrivKey32_Plain = privKey.copy()

      pubKey = chkzero(serializedData.get(BINARY_CHUNK, 65))
      chkPub =         serializedData.get(BINARY_CHUNK, 4)
      pubKey = SecureBinaryData(verifyChecksum(pubKey, chkPub))

      if containsPubKey:
         if not pubKey.getSize()==65:
            if self.binPrivKey32_Plain.getSize()==32:
               pubKey = CryptoAES().ComputePublicKey(self.binPrivKey32_Plain)
            else:
               raise UnserializeError, 'Checksum mismatch in PublicKey ' +\
                                       '('+hash160_to_addrStr(self.addrStr20)+')'

      self.binPublicKey65 = pubKey

      if addrChkError:
         self.addrStr20 = self.binPublicKey65.getHash160()

      self.timeRange[0] = serializedData.get(UINT64)
      self.timeRange[1] = serializedData.get(UINT64)
      self.blkRange[0]  = serializedData.get(UINT32)
      self.blkRange[1]  = serializedData.get(UINT32)

      self.isInitialized = True
      return self



   #############################################################################
   # The following methods are the SIMPLE address operations that can be used
   # to juggle address data without worrying at all about encryption details.
   # The addresses created here can later be endowed with encryption.
   #############################################################################
   def createFromPrivateKey(self, privKey, pubKey=None, skipCheck=False):
      """
      Creates address from a user-supplied random INTEGER.
      This method DOES perform elliptic-curve operations
      """
      if isinstance(privKey, str) and len(privKey)==32:
         self.binPrivKey32_Plain = SecureBinaryData(privKey)
      elif isinstance(privKey, int) or isinstance(privKey, long):
         binPriv = int_to_binary(privKey, widthBytes=32, endOut=BIGENDIAN)
         self.binPrivKey32_Plain = SecureBinaryData(binPriv)
      else:
         raise KeyDataError, 'Unknown private key format'

      if pubKey==None:
         self.binPublicKey65 = CryptoECDSA().ComputePublicKey(self.binPrivKey32_Plain)
      else:
         self.binPublicKey65 = SecureBinaryData(pubKey)

      if not skipCheck:
         assert(CryptoECDSA().CheckPubPrivKeyMatch( \
                                             self.binPrivKey32_Plain, \
                                             self.binPublicKey65))

      self.addrStr20 = self.binPublicKey65.getHash160()

      self.isInitialized = True
      return self



   #############################################################################
   def createFromPublicKey(self, pubkey):
      """
      Creates address from a user-supplied ECDSA public key.

      The key can be supplied as an (x,y) pair of integers, an EC_Point
      as defined in the lisecdsa class, or as a 65-byte binary string
      (the 64 public key bytes with a 0x04 prefix byte)

      This method will fail if the supplied pair of points is not
      on the secp256k1 curve.
      """
      if isinstance(pubkey, tuple) and len(pubkey)==2:
         # We are given public-key (x,y) pair
         binXBE = int_to_binary(pubkey[0], widthBytes=32, endOut=BIGENDIAN)
         binYBE = int_to_binary(pubkey[1], widthBytes=32, endOut=BIGENDIAN)
         self.binPublicKey65 = SecureBinaryData('\x04' + binXBE + binYBE)
         if not CryptoECDSA().VerifyPublicKeyValid(self.binPublicKey65):
            raise KeyDataError, 'Supplied public key is not on secp256k1 curve'
      elif isinstance(pubkey, str) and len(pubkey)==65:
         self.binPublicKey65 = SecureBinaryData(pubkey)
         if not CryptoECDSA().VerifyPublicKeyValid(self.binPublicKey65):
            raise KeyDataError, 'Supplied public key is not on secp256k1 curve'
      else:
         raise KeyDataError, 'Unknown public key format!'

      # TODO: I should do a test to see which is faster:
      #           1) Compute the hash directly like this
      #           2) Get the string, hash it in python
      self.addrStr20 = self.binPublicKey65.getHash160()
      self.isInitialized = True
      return self


   def createFromPublicKeyHash160(self, pubkeyHash160, netbyte=ADDRBYTE):
      """
      Creates an address from just the 20-byte binary hash of a public key.

      In binary form without a chksum, there is no protection against byte
      errors, since there's no way to distinguish an invalid address from
      a valid one (they both look like random data).

      If you are creating an address using 20 bytes you obtained in an
      unreliable manner (such as manually typing them in), you should
      double-check the input before sending money using the address created
      here -- the tx will appear valid and be accepted by the network,
      but will be permanently tied up in the network
      """
      self.__init__()
      self.addrStr20 = pubkeyHash160
      self.isInitialized = True
      return self

   def createFromAddrStr(self, addrStr):
      """
      Creates an address from a Base58 address string.  Since the address
      string includes a checksum, this method will fail if there was any
      errors entering/copying the address
      """
      self.__init__()
      self.addrStr = addrStr
      if not self.checkAddressValid():
         raise BadAddressError, 'Invalid address string: '+addrStr
      self.isInitialized = True
      return self

   def calculateAddrStr(self, netbyte=ADDRBYTE):
      """
      Forces a recalculation of the address string from the public key
      """
      if not self.hasPubKey():
         raise KeyDataError, 'Cannot compute address without PublicKey'
      keyHash = self.binPublicKey65.getHash160()
      chksum  = hash256(netbyte + keyHash)[:4]
      return  binary_to_base58(netbyte + keyHash + chksum)



   def checkAddressValid(self):
      return checkAddrStrValid(self.addrStr);


   def pprint(self, withPrivKey=True, indent=''):
      def pp(x, nchar=1000):
         if x.getSize()==0:
            return '--'*32
         else:
            return x.toHexStr()[:nchar]
      print indent + 'BTC Address      :', self.getAddrStr()
      print indent + 'Hash160[BE]      :', binary_to_hex(self.getAddr160())
      print indent + 'Wallet Location  :', self.walletByteLoc
      print indent + 'Chained Address  :', self.chainIndex >= -1
      print indent + 'Have (priv,pub)  : (%s,%s)' % \
                     (str(self.hasPrivKey()), str(self.hasPubKey()))
      print indent + 'First/Last Time  : (%s,%s)' % \
                     (str(self.timeRange[0]), str(self.timeRange[1]))
      print indent + 'First/Last Block : (%s,%s)' % \
                     (str(self.blkRange[0]), str(self.blkRange[1]))
      if self.hasPubKey():
         print indent + 'PubKeyX(BE)      :', \
                        binary_to_hex(self.binPublicKey65.toBinStr()[1:33 ])
         print indent + 'PubKeyY(BE)      :', \
                        binary_to_hex(self.binPublicKey65.toBinStr()[  33:])
      print indent + 'Encryption parameters:'
      print indent + '   UseEncryption :', self.useEncryption
      print indent + '   IsLocked      :', self.isLocked
      print indent + '   KeyChanged    :', self.keyChanged
      print indent + '   ChainIndex    :', self.chainIndex
      print indent + '   Chaincode     :', pp(self.chaincode)
      print indent + '   InitVector    :', pp(self.binInitVect16)
      if withPrivKey and self.hasPrivKey():
         print indent + 'PrivKeyPlain(BE) :', pp(self.binPrivKey32_Plain)
         print indent + 'PrivKeyCiphr(BE) :', pp(self.binPrivKey32_Encr)
      else:
         print indent + 'PrivKeyPlain(BE) :', pp(SecureBinaryData())
         print indent + 'PrivKeyCiphr(BE) :', pp(SecureBinaryData())
      if self.createPrivKeyNextUnlock:
         print indent + '           ***** :', 'PrivKeys available on next unlock'

   def toString(self, withPrivKey=True, indent=''):
      def pp(x, nchar=1000):
         if x.getSize()==0:
            return '--'*32
         else:
            return x.toHexStr()[:nchar]
      result = ''.join([indent + 'BTC Address      :', self.getAddrStr()])
      result = ''.join([result, '\n', indent + 'Hash160[BE]      :', binary_to_hex(self.getAddr160())])
      result = ''.join([result, '\n',  indent + 'Wallet Location  :', str(self.walletByteLoc)])
      result = ''.join([result, '\n',  indent + 'Chained Address  :', str(self.chainIndex >= -1)])
      result = ''.join([result, '\n',  indent + 'Have (priv,pub)  : (%s,%s)' % \
                     (str(self.hasPrivKey()), str(self.hasPubKey()))])
      result = ''.join([result, '\n',   indent + 'First/Last Time  : (%s,%s)' % \
                     (str(self.timeRange[0]), str(self.timeRange[1]))])
      result = ''.join([result, '\n',   indent + 'First/Last Block : (%s,%s)' % \
                     (str(self.blkRange[0]), str(self.blkRange[1]))])
      if self.hasPubKey():
         result = ''.join([result, '\n',   indent + 'PubKeyX(BE)      :', \
                        binary_to_hex(self.binPublicKey65.toBinStr()[1:33 ])])
         result = ''.join([result, '\n',   indent + 'PubKeyY(BE)      :', \
                        binary_to_hex(self.binPublicKey65.toBinStr()[  33:])])
      result = ''.join([result, '\n',   indent + 'Encryption parameters:'])
      result = ''.join([result, '\n',   indent + '   UseEncryption :', str(self.useEncryption)])
      result = ''.join([result, '\n',   indent + '   IsLocked      :', str(self.isLocked)])
      result = ''.join([result, '\n',   indent + '   KeyChanged    :', str(self.keyChanged)])
      result = ''.join([result, '\n',   indent + '   ChainIndex    :', str(self.chainIndex)])
      result = ''.join([result, '\n',   indent + '   Chaincode     :', pp(self.chaincode)])
      result = ''.join([result, '\n',   indent + '   InitVector    :', pp(self.binInitVect16)])
      if withPrivKey and self.hasPrivKey():
         result = ''.join([result, '\n',   indent + 'PrivKeyPlain(BE) :', pp(self.binPrivKey32_Plain)])
         result = ''.join([result, '\n',   indent + 'PrivKeyCiphr(BE) :', pp(self.binPrivKey32_Encr)])
      else:
         result = ''.join([result, '\n',   indent + 'PrivKeyPlain(BE) :', pp(SecureBinaryData())])
         result = ''.join([result, '\n',   indent + 'PrivKeyCiphr(BE) :', pp(SecureBinaryData())])
      if self.createPrivKeyNextUnlock:
         result = ''.join([result, '\n',   indent + '           ***** :', 'PrivKeys available on next unlock'])
      return result

# Put the import at the end to avoid circular reference problem
from armoryengine.BDM import *
