################################################################################
#                                                                              #
# Copyright (C) 2011-2015, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################
from ArmoryUtils import *
from BinaryPacker import *
from Transaction import getOpCode
from ArmoryEncryption import NULLSBD
from CppBlockUtils import HDWalletCrypto, CryptoECDSA
import re
import CppBlockUtils as Cpp

# First "official" version is 1. 0 was a prototype version.
BTCAID_PKS_VERSION = 1
BTCAID_CS_VERSION = 1
BTCAID_RI_VERSION = 1
BTCAID_PKRP_VERSION = 1
BTCAID_SRP_VERSION = 1
BTCAID_PTV_VERSION = 1
BTCAID_PR_VERSION = 1

# From the PMTA RFC draft (v0)
PAYASSOC_ADDR = 0  # Sec. 2.1.5
PAYNET_TBTC   = 1  # Sec. 2.1.1 - Testnet
PAYNET_BTC    = 2  # Sec. 2.1.1 - Mainnet

BTCAID_PAYLOAD_TYPE = enum('PublicKeySource', 'ConstructedScript', 'InvalidRec')
ESCAPECHAR  = '\xff'
ESCESC      = '\x00'

# Use in SignableIDPayload
BTCAID_PAYLOAD_BYTE = { \
   BTCAID_PAYLOAD_TYPE.PublicKeySource:   '\x00',
   BTCAID_PAYLOAD_TYPE.ConstructedScript: '\x01',
   BTCAID_PAYLOAD_TYPE.InvalidRec:        '\xff'
}

class VersionError(Exception): pass

try:
   # Normally the decorator simply confirms that function arguments
   # are of the expected type.  Will throw an error if not defined.
   VerifyArgTypes
except:
   # If it's not available, just make a replacement decorator that does nothing
   def VerifyArgTypes(*args, **kwargs):
      def decorator(func):
         return func
      return decorator

################################ Internal Data #################################
################################################################################
class MultiplierProof(object):
   """
   Simply a 32-byte multiplier and a 4-byte fingerprint of both the root key
   where the multiplier will be applied, and the resultant key. The four bytes
   aren't meant to be cryptographically strong, just data that helps reduce
   unnecessary computation. These objects are obtained from C++.
   """

   #############################################################################
   def __init__(self, isNull=None, srcFinger4=None, dstFinger4=None,
                multiplier=None):
      self.isNull      = None   # If static, stealth, etc., this can be ignored.
      self.srcFinger4  = None   # Just the 1st 4B of BE hash256(root pub key).
      self.dstFinger4  = None   # Just the 1st 4B of BE hash256(result pub key).
      self.multiplier  = None   # 32-byte BE multiplier.

      if isNull is not None:
         self.initialize(isNull, srcFinger4, dstFinger4, multiplier)


   #############################################################################
   def initialize(self, isNull=None, srcFinger4=None, dstFinger4=None,
                  multiplier=None):
      self.isNull = isNull
      if isNull:
         self.srcFinger4  = None
         self.dstFinger4  = None
         self.multiplier  = None
      else:
         self.srcFinger4  = srcFinger4
         self.dstFinger4  = dstFinger4
         self.multiplier  = multiplier


   #############################################################################
   def serialize(self):
      flags = BitSet(8)
      flags.setBit(0, self.isNull)

      bp = BinaryPacker()
      bp.put(BITSET, flags, widthBytes=1)

      if not self.isNull:
         bp.put(BINARY_CHUNK, self.srcFinger4, widthBytes= 4)
         bp.put(BINARY_CHUNK, self.dstFinger4, widthBytes= 4)
         bp.put(BINARY_CHUNK, self.multiplier, widthBytes=32)

      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, serData):
      bu = makeBinaryUnpacker(serData)
      flags = bu.get(BITSET, 1)

      if flags.getBit(0):
         self.initialize(isNull=True)
      else:
         srcFinger4B = bu.get(BINARY_CHUNK, 4)
         dstFinger4B = bu.get(BINARY_CHUNK, 4)

         multiplier.append(bu.get(BINARY_CHUNK, 32))

         self.initialize(False, srcFinger4B, dstFinger4B, multiplier)

      return self


################################################################################
class SignableIDPayload(object):
   """
   !!!WORK IN PROGRESS!!!
   This data structure wraps up all the other classes that can go into a DANE
   record into a single, embeddable data type.
   """
   #############################################################################
   def __init__(self):
      self.version     = None
      self.createDate  = None
      self.expireDate  = None
      self.payloadType = None  # KeySource or ConstructedScript
      self.payload     = None


   #############################################################################
   def initialize(self, template):
      self.rawTemplate = template


   #############################################################################
   def serialize(self):
      pass


   #############################################################################
   def unserialize(self, templateStr):
      bu = makeBinaryUnpacker(templateStr)

      oplist = []


################################################################################
def DeriveBip32PublicKeyWithProof(startPubKey, binChaincode, indexList):
   """
   We will actually avoid using the higher level ArmoryKeyPair (AKP) objects
   for now, as they do a ton of extra stuff we don't need for this.  We go
   a bit lower-level and talk to CppBlockUtils.HDWalletCrypto directly.

   Inputs:
      startPubKey:   python string, 33-byte compressed public key
      binChaincode:  python string, 32-byte chaincode
      indexList:     python list of UINT32s, anything >0x7fffffff not allowed

   Output: [finalPubKey, proofObject]

      finalPubKey:   pyton string:  33-byte compressed public key
      proofObject:   MultiplierProof: list of 32-byte mults to be applied
                     to the input startPubKey to produce the finalPubKey

   Note that an error will be thrown if any items in the index list correspond
   to a hardened derivation.  We need this proof to be generatable strictly
   from public key material.
   """

   # Sanity check the inputs
   if not len(startPubKey)==33 or not startPubKey[0] in ['\x02','\x03']:
      raise KeyDataError('Input public key is not in a valid format')

   if not len(binChaincode)==32:
      raise KeyDataError('Chaincode must be 32 bytes')

   # Crypto-related code uses SecureBinaryData and Cpp.ExtendedKey objects
   sbdPublicKey = SecureBinaryData(startPubKey)
   sbdChainCode = SecureBinaryData(binChaincode)
   extPubKeyObj = Cpp.ExtendedKey(sbdPublicKey, sbdChainCode)

   # Prepare the output multiplier container
   binMultList = []

   # Derive the children
   for childIndex in indexList:
      if (childIndex & 0x80000000) > 0:
         raise BadInputError('Cannot generate proofs along hardened paths')

      # Pass in a NULL SecureBinaryData object as a reference
      sbdMultiplier = NULLSBD()

      # Computes the child and emits the multiplier via the last arg
      extPubKeyObj = Cpp.HDWalletCrypto().childKeyDeriv(extPubKeyObj,
                                                        childIndex,
                                                        sbdMultiplier)

      # Append multiplier to list
      binMultList.append(sbdMultiplier.toBinStr())

   # Get the final multiplier.
   finalMult = HDWalletCrypto().addModMults_SWIG(binMultList)

   finalPubKey = extPubKeyObj.getPublicKey().toBinStr()
   proofObject = MultiplierProof(False,
                                 hash256(startPubKey)[:4],
                                 hash256(finalPubKey)[:4],
                                 finalMult)

   return (finalPubKey, proofObject)


################################################################################
def DeriveBip32PrivateKey(startPriKey, binChaincode, indexList):
   """
   We will actually avoid using the higher level ArmoryKeyPair (AKP) objects
   for now, as they do a ton of extra stuff we don't need for this.  We go
   a bit lower-level and talk to CppBlockUtils.HDWalletCrypto directly.

   Inputs:
      startPriKey:   python string, 33-byte private key
      binChaincode:  python string, 32-byte chaincode
      indexList:     python list of UINT32s

   Output: finalPriKey

      finalPubKey:   pyton string:  33-byte private key

   Note that an error will be thrown if any items in the index list correspond
   to a hardened derivation.  We need this proof to be generatable strictly
   from public key material.
   """

   # Sanity check the inputs
   if not len(startPriKey)==33 or not startPriKey[0] in ['\x00']:
      raise KeyDataError('Input private key is a valid format')

   if not len(binChaincode)==32:
      raise KeyDataError('Chaincode must be 32 bytes')

   # Crypto-related code uses SecureBinaryData and Cpp.ExtendedKey objects
   sbdPrivateKey = SecureBinaryData(startPriKey)
   sbdChainCode  = SecureBinaryData(binChaincode)
   extPriKeyObj  = Cpp.ExtendedKey(sbdPrivateKey, sbdChainCode)

   # Prepare the output multiplier list
   binMultList = []

   # Derive the children. Maybe use MultiplierProof later and merge?
   for childIndex in indexList:
      if (childIndex & 0x80000000) > 0:
         raise ChildDeriveError('Cannot generate proofs along hardened paths')

      # Pass in a NULL SecureBinaryData object as a reference
      sbdMultiplier = NULLSBD()

      # Computes the child and emits the multiplier via the last arg
      extPriKeyObj = Cpp.HDWalletCrypto().childKeyDeriv(extPriKeyObj,
                                                        childIndex)

   return extPriKeyObj.getKey().toBinStr()


################################################################################
def ApplyProofToRootKey(startPubKey, multProofObj, expectFinalPub=None):
   """
   Inputs:
      startPubKey:    python string, 33-byte compressed public key
      multProofObj:   MultiplierProof object
      expectFinalPub: Optionally provide the final pub key we expect

   Output: finalPubKey

      finalPubKey:    python string with resulting public key, will match
                      expectFinalPub input if supplied.

   Since we don't expect this to fail, KeyDataError raised on failure
   """
   if not hash256(startPubKey)[:4] == multProofObj.srcFinger4:
      raise KeyDataError('Source fingerprint of proof does not match root pub')

   finalPubKey = HDWalletCrypto().getChildKeyFromMult_SWIG(startPubKey,
                                                        multProofObj.multiplier)

   if len(finalPubKey) == 0:
      raise KeyDataError('Key derivation failed - Elliptic curve violations')

   if not hash256(finalPubKey)[:4] == multProofObj.dstFinger4:
      raise KeyDataError('Dst fingerprint of proof does not match root pub')

   if expectFinalPub and not finalPubKey == expectFinalPub:
      raise KeyDataError('Computation did not yield expected public key!')

   return finalPubKey


#############################################################################
def makeBinaryUnpacker(inputStr):
   """
   Use this on input args so that unserialize funcs can treat the
   input as a BU object.  If it's not a BU object, convert it, and
   the consumer method will start reading from byte zero.  If it
   is BU, then forward the reference to it so that it starts unserializing
   from the current location in the BU object, leaving the position
   after the data was unserialized.
   """
   if isinstance(inputStr, BinaryUnpacker):
      # Just return the input reference
      return inputStr
   else:
      # Initialize a new BinaryUnpacker
      return BinaryUnpacker(inputStr)


################################################################################
def escapeFF(inputStr):
   """
   Take a string intended for a DANE script template and "escape" it such that
   any instance of 0xff becomes 0xff00. This must be applied to any string that
   will be processed by a DANE script template decoder.
   """
   convExp = re.compile('ff', re.IGNORECASE)
   convStr = convExp.sub('ff00', inputStr)
   return convStr


################################################################################
def assembleScript(inEscapedScript, inPKSList, inPKRPList):
   # Steps:
   # Take binary string and split based on 0xff, which is removed.
   # Grab & remove 1st byte of string on the right.
   # - If byte = 0x00, place 0xff at the end of the string on the left.
   # - Else, confirm # equals the # of PKS & SRP entries.
   #   For each entry, get the public key and apply the SRP.
   #   Insert the key at the end of the string on the left.
   # Reassemble all the strings in the original order.
   # Return the resulting string.

   # Use a bytearray to treat the incoming binary data as a string. Split
   # whenever 0xff is encountered. Save the 1st one and then iterate over the
   # others, if any exist. This is where keys will be inserted and escaped 0xff
   # characters restored.
   numProcessedKeys = 0
   scriptArray = bytes(inEscapedScript)
   scriptArrayList = scriptArray.split('\xff')
   finalScriptList = []
   finalScriptList.append(scriptArrayList[0])

   for fragment in scriptArrayList[1:]:
      if fragment[0] == '\x00':
         # Fix up escaped 0xff and save.
         finalScript.append('\xff')
         if len(fragment) > 1:
            finalScript.append(fragment[1:])
      else:
         # Remove but keep 1st byte
         numKeys = binary_to_int(fragment[0])
         keyList = []
         for innerPKSList in inPKSList:
            for innerPKSItem in innerPKSList:
               genKey = innerPKSItem.generateKeyData(inPKRPList[numProcessedKeys])
               keyList.append(genKey)

         # Sort keys lexicographically and insert into the script before
         # inserting the rest of the original fragment.
         # !!!DISABLED!!! Assume only one key coming in for now.
#         keyList.sort()
         for key in keyList:
            finalScriptList.append(key)
         if len(fragment) > 1:
            finalScriptList.append(fragment[1:])

   # We're done! Return the final script.
   return ''.join(finalScriptList)


################################ External Data #################################
################################################################################
class PublicKeySource(object):
   """
   This defines a "source" from where we could get a public key, either to be
   inserted directly into P2PKH, or to be used as part of a multi-sig or other
   non-standard script.

   @isStatic:         rawSource is just a single public key
   @useCompr:         use compressed or uncompressed version of pubkey
   @useHash160:       pubKey should be hashed before being placed in a script
   @isUserKey:        user should insert their own key in this slot
   @useExternal:      rawSource is actually a link to another pubkey source
   @isChksumPresent:  A four-byte checksum is included.
   @disableDirectPay: No direct payments to anything derived from this PKS.
   @checksum:         A four-byte checksum.
   """

   #############################################################################
   def __init__(self):
      self.version          = BTCAID_PKS_VERSION
      self.isStatic         = False
      self.useHash160       = False
      self.isUserKey        = False
      self.isExternalSrc    = False
      self.useCompr         = False
      self.isChksumPresent  = True
      self.disableDirectPay = True
      self.rawSource        = None
      self.checksum         = None


   #############################################################################
   def getFingerprint(self):
      return hash256(self.rawSource)[:4]


   #############################################################################
   def getDataNoChecksum(self):
      # In BitSet, higher numbers are less significant bits.
      # e.g., To get 0x0002, set bit 14 to True (1).
      # NB: For now, the compression relies on if the raw source is compressed.
      flags = BitSet(16)
      flags.setBit(15, self.isStatic)
      flags.setBit(14, self.useCompr)
      flags.setBit(13, self.useHash160)
      flags.setBit(12, self.isUserKey)
      flags.setBit(11, self.isExternalSrc)
      flags.setBit(10, self.isChksumPresent)
      flags.setBit(9,  self.disableDirectPay)

      inner = BinaryPacker()
      inner.put(UINT8,   self.version)
      inner.put(BITSET,  flags, width=2)
      inner.put(VAR_STR, self.rawSource)
      return inner.getBinaryString()


   #############################################################################
   @VerifyArgTypes(isStatic   = bool,
                   useCompr   = bool,
                   use160     = bool,
                   isUser     = bool,
                   isExt      = bool,
                   src        = [str, unicode],
                   chksumPres = bool,
                   disDirPay  = bool,
                   inChksum   = [str, unicode],
                   ver        = int)
   def initialize(self, isStatic, useCompr, use160, isUser, isExt, src,
                  chksumPres, disDirPay, inChksum=None, ver=BTCAID_PKS_VERSION):
      """
      Set all PKS values.
      """

      # We expect regular public key sources to be binary strings, but external
      # sources may be similar to email addresses which need to be unicode.
      # TEMPORARILY DISABLED - NEED TO RESOLVE AN INTENTIONALLY BROKEN TEST
#      if isExt != isinstance(src, unicode):
#         raise UnicodeError('Must use str for reg srcs, unicode for external')

      self.version          = ver
      self.isStatic         = isStatic
      self.useCompr         = useCompr
      self.useHash160       = use160
      self.isUserKey        = isUser
      self.isExternalSrc    = isExt
      self.isChksumPresent  = chksumPres
      self.disableDirectPay = disDirPay
      self.rawSource        = toBytes(src)

      # The checksum portion opens up the possibility that a bad checksum could
      # get passed in, as we don't check to see if an incoming checksum's right.
      # For now, just accept it. isValid() can be used to check it anyway.
      if self.isChksumPresent:
         if inChksum is None:
            dataStr = self.getDataNoChecksum()
            self.checksum = computeChecksum(dataStr)
         else:
            self.checksum = inChksum


   #############################################################################
   def isInitialized(self):
      return not (self.rawSource is None or len(self.rawSource) == 0)


   #############################################################################
   def getRawSource(self):
      """
      If this is an external source, then the rawSource might be a unicode
      string.  If it was input as unicode, it was converted into this data
      structure using toBytes(), so we'll return it using toUnicode()
      """
      if self.isExternalSrc:
         return toUnicode(self.rawSource)
      else:
         return self.rawSource


   #############################################################################
   # Logic for generating the final key data based on PKS data is here.
   def generateKeyData(self, inPKRPList):
      finalKeyData = None

      # The logic determining the final key data is found here. This is really
      # meant to be the jumping off point for other calls that do heavy lifting.
      if self.isExternalSrc:
         # Grab key data from elsewhere. Do nothing for now.
         pass
      elif self.isUserKey:
         # User somehow provides their own key data. Do nothing for now.
         pass
      elif self.isStatic:
         # The final key (e.g., vanity address) is already present.
         finalKeyData = self.rawSource
      else:
         for pkrp in inPKRPList:
            # Get the final public key. If necessary, compress it and/or apply
            # Hash160 to it.
            finalKeyData = HDWalletCrypto().getChildKeyFromMult_SWIG(
                                                                 self.rawSource,
                                                                  pkrp.multList)

            if self.useCompr:
               secFinalKeyData = SecureBinaryData(finalKeyData)
               finalKeyDataSBD = CryptoECDSA().CompressPoint(secFinalKeyData)
               finalKeyData = finalKeyDataSBD.toBinStr()

            if self.useHash160:
               finalKeyData = hash160(finalKeyData)

      # We're done! Return the key data.
      return finalKeyData


   #############################################################################
   # Verify that a PKS record is valid. Useful as a standalone funct or, more
   # importantly, as a utility function before doing anything critical w/ a rec.
   # INPUT:  A boolean indicating if logs should be written.
   # OUTPUT: None
   # RETURN: A boolean indicating if the record is valid.
   def isValid(self, printToLog):
      """
      Verify that a PKS record's construction is valid.
      """
      # Never reset the validity flag! Once a record's invalid, it's invalid.
      recState = True

      # The version needs to be valid. For now, it needs to be 1.
      if self.version != BTCAID_PKS_VERSION:
         if printToLog == True:
            LOGINFO('PKS record version is wrong. Record is invalid.')
         recState = False

      # Certain flags force other flags to be ignored. This must be enforced.
      if (self.isExternalSrc == True and (self.isUserKey == True or
                                         self.isStatic == True)):
         if printToLog == True:
            LOGINFO('PKS record cannot have external flag and the user ' \
                    'and/or static flag. Record is invalid.')
         recState = False
      elif (self.isUserKey == True and self.isStatic == True):
         if printToLog == True:
            LOGINFO('PKS record cannot have user and static flags. Record is ' \
                    'invalid.')
         recState = False

      # Check the checksum if necessary.
      if self.isChksumPresent:
         if self.checksum is None:
            if printToLog == True:
               LOGINFO('PKS record has a checksum flag and no checksum. ' \
                       'Record is invalid.')
            recState = False
         else:
            dataChunk  = self.serialize()
            checkData  = dataChunk[:-4]
            checksum   = dataChunk[-4:]
            compChksum = computeChecksum(checkData)
            if compChksum != checksum:
               if printToLog == True:
                  LOGINFO('PKS record has an invalid checksum. Record is ' \
                          'invalid.')
               recState = False

      return recState


   #############################################################################
   def serialize(self):
      bp = BinaryPacker()
      dataStr = self.getDataNoChecksum()
      bp.put(BINARY_CHUNK, dataStr)

      if self.isChksumPresent:
         # Place a checksum in the data. Somewhat redundant due to signatures.
         # Still useful because it protects data sent to signer.
         if self.checksum != None:
            bp.put(BINARY_CHUNK, self.checksum)

      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, serData):
      inData   = BinaryUnpacker(serData)
      inVer    = inData.get(UINT8)
      inFlags  = inData.get(BITSET, 2)
      inRawSrc = inData.get(VAR_STR)

      # If checksum is present, confirm that the other data is correct.
      inChksum = None
      if inFlags.getBit(10):
         inChksum = inData.get(BINARY_CHUNK, 4)

      if not inVer == BTCAID_PKS_VERSION:
         # In the future we will make this more of a warning, not error
         raise VersionError('PKS version does not match the loaded version')

      self.__init__()
      self.initialize(inFlags.getBit(15),
                      inFlags.getBit(14),
                      inFlags.getBit(13),
                      inFlags.getBit(12),
                      inFlags.getBit(11),
                      inRawSrc,
                      inFlags.getBit(10),
                      inFlags.getBit(9),
                      inChksum,
                      inVer)

      return self


################################################################################
class ExternalPublicKeySource(object):
   def __init__(self):
      raise NotImplementedError('Have not implemented external sources yet')


################################################################################
def getP2PKHStr(useActualKeyHash, keyData=None):
   # Need to make this code more robust. Check input data & input length, have
   # an error condition, etc.
   templateStrKeyData = '\xff\x01'
   if useActualKeyHash == True and keyData != None:
      templateStrKeyData = keyData

   templateStr  = ''
   templateStr += getOpCode('OP_DUP')
   templateStr += getOpCode('OP_HASH160')
   templateStr += '\x14'
   templateStr += templateStrKeyData
   templateStr += getOpCode('OP_EQUALVERIFY')
   templateStr += getOpCode('OP_CHECKSIG')

   return templateStr


################################################################################
def getP2PKStr(useActualKey, keyData=None):
   # Need to make this code more robust. Check input data & input length, have
   # an error condition, etc.
   templateStrKeyData = '\xff\x01'
   if useActualKey == True and keyData != None:
      templateStrKeyData = keyData

   templateStr  = ''
   templateStr += templateStrKeyData
   templateStr += getOpCode('OP_CHECKSIG')

   return templateStr


################################################################################
class ConstructedScript(object):
   """
   This defines a script template that will be used, in conjunction with a
   series of Public Key Sources, to define the basic data required to
   reconstruct a payment script. Script Relationship Proofs may be required to
   construct the correct public keys.

   @useP2SH:         Final TxOut script uses P2SH instead of being used as-is.
   @isChksumPresent: A four-byte checksum is included.
   """

   def __init__(self):
      self.version         = BTCAID_CS_VERSION
      self.scriptTemplate  = None
      self.pubKeySrcList   = None
      self.useP2SH         = None
      self.pubKeyBundles   = []
      self.isChksumPresent = True
      self.checksum        = None


   #############################################################################
   @VerifyArgTypes(scrTemp    = str,
                   pubSrcs    = [list, tuple],
                   useP2SH    = bool,
                   chksumPres = bool,
                   inChksum   = [str, unicode],
                   ver        = int)
   def initialize(self, scrTemp, pubSrcs, useP2SH, chksumPres, inChksum=None,
                  ver=BTCAID_CS_VERSION):
      self.version         = ver
      self.useP2SH         = useP2SH
      self.isChksumPresent = chksumPres
      self.pubKeyBundles   = []

      self.setTemplateAndPubKeySrcs(scrTemp, pubSrcs)

      # The checksum portion opens up the possibility that a bad checksum could
      # get passed in, as we don't check to see if an incoming checksum's right.
      # For now, just accept it. isValid() can be used to check it anyway.
      if self.isChksumPresent:
         if inChksum is None:
            dataStr = self.getDataNoChecksum()
            self.checksum = computeChecksum(dataStr)
         else:
            self.checksum = inChksum


   #############################################################################
   def getDataNoChecksum(self):
      # In BitSet, higher numbers are less significant bits.
      # e.g., To get 0x0010, set bit 11 to True (1).
      flags = BitSet(16)
      flags.setBit(15, self.useP2SH)
      flags.setBit(14, self.isChksumPresent)

      inner = BinaryPacker()
      inner.put(UINT8,   self.version)
      inner.put(BITSET,  flags, width = 2)
      inner.put(VAR_STR, self.scriptTemplate)
      inner.put(UINT8,   sum(len(keyList) for keyList in self.pubKeyBundles)) # Fix?
      for keyItem in self.pubKeyBundles:
         for keyItem2 in keyItem:
            inner.put(VAR_STR, keyItem2.serialize())

      return inner.getBinaryString()


   #############################################################################
   def setTemplateAndPubKeySrcs(self, scrTemp, pubSrcs):
      """
      Inputs:
         scrTemp:  script template  (ff-escaped)
         pubSrcs:  flat list of PublicKeySource objects

      Outputs:
         Sets member vars self.scriptTemplate and self.pubKeyBundles
         pubkeyBundles will be a list-of-lists as described below.

      Let's say we have a script template like this: this is a non-working
      2-of-3 OR 3-of-5, with the second key list sorted)

      OP_IF 
         OP_2 0xff01 0xff01 0xff01 OP_3 OP_CHECKMULTISIG 
      OP_ELSE 
         OP_3 0xff05 OP_5 OP_CHECKMULTISIG
      OP_ENDIF

      We have 4 public key bundles: first three are of size 1, the last is 5.
      In this script, the five keys in the second half of the script are sorted
      We should end up with:  
   
      Final result sould look like:

             [ [PubSrc1], [PubSrc2], [PubSrc3], [PubSrc4, PubSrc5, ...]]
                   1          2          3       <--------- 4 -------->
      """
      if '\xff\xff' in scrTemp or scrTemp.endswith('\xff'):
         raise BadInputError('All 0xff sequences need to be properly escaped')

      # The first byte after each ESCAPECHAR is number of pubkeys to insert.
      # ESCAPECHAR+'\x00' is interpretted as as single
      # 0xff op code.  i.e.  0xff00 will be inserted in the final 
      # script as a single 0xff byte (which is OP_INVALIDOPCODE).   For the 
      # purposes of this function, 0xff00 is ignored.
      # 0xffff should not exist in any script template
      scriptPieces = scrTemp.split(ESCAPECHAR)

      # Example after splitting:
      # 76a9ff0188acff03ff0001 would now look like:  '76a9' '0188ac' '03', '0001']
      #                                                      ^^       ^^    ^^
      #                                                  ff-escaped chars
      # We want this to look like:                   '76a9',  '88ac',  '',   '01'
      #        with escape codes:                           01       03     ff
      #        with 2 pub key bundles                      [k0] [k1,k2,k3]

      # Get the first byte after every 0xff
      breakoutPairs = [[pc[0],pc[1:]] for pc in scriptPieces[1:]]
      escapedBytes  = [binary_to_int(b[0]) for b in breakoutPairs if b[0]]
      #scriptPieces  = [scriptPieces[0]] + [b[1] for b in bundleBytes]

      if sum(escapedBytes) != len(pubSrcs):
         raise UnserializeError('Template key count do not match pub list size')

      self.scriptTemplate = scrTemp
      self.pubKeySrcList  = pubSrcs[:]
      self.pubKeyBundles  = []

      # Slice up the pubkey src list into the bundles. Key order doesn't matter
      # as long as the keys line up alongside the escaped bytes. Multisig keys
      # will be lexicographically sorted ONLY in the final TxOut script.
      idx = 0
      for sz in escapedBytes:
         if sz > 0:
            self.pubKeyBundles.append( self.pubKeySrcList[idx:idx+sz] )
            idx += sz


   #############################################################################
   @staticmethod
   def StandardP2PKHConstructed(binRootPubKey):
      """
      Standard Pay-to-public-key-hash script
      """

      if not len(binRootPubKey) in [33,65]:
         raise KeyDataError('Invalid pubkey;  length=%d' % len(binRootPubKey))

      templateStr = getP2PKHStr(False)

      pks = PublicKeySource()
      pks.initialize(isStatic   = False,
                     useCompr   = (len(binRootPubKey) == 33),
                     use160     = True,
                     isUser     = False,
                     isExt      = False,
                     src        = binRootPubKey,
                     chksumPres = False,
                     disDirPay  = False)

      cs = ConstructedScript()
      cs.initialize(templateStr, [pks], False, True)
      return cs


   #############################################################################
   # Check the hash160 call. There were 2 calls, one w/ Hash160 and one w/o.
   @staticmethod
   def StandardP2PKConstructed(binRootPubKey, hash160=False):
      """ This is bare pubkey, usually used with coinbases """
      if not len(binRootPubKey) in [33,65]:
         raise KeyDataError('Invalid pubkey;  length=%d' % len(binRootPubKey))

      templateStr = getP2PKStr(False)

      pks = PublicKeySource()
      pks.initialize(isStatic   = False,
                     useCompr   = (len(binRootPubKey) == 33),
                     use160     = hash160,
                     isUser     = False,
                     isExt      = False,
                     src        = binRootPubKey,
                     chksumPres = False,
                     disDirPay  = False)

      cs = ConstructedScript()
      cs.initialize(self, templateStr, [pks], False)
      return cs


   #############################################################################
   @staticmethod
   def StandardMultisigConstructed(M, binRootList):
      # Make sure all keys are valid before processing them.
      for pk in binRootList:
         if not len(pk) in [33,65]:
            raise KeyDataError('Invalid pubkey;  length=%d' % len(pk))
         else:
            sbdPublicKey = SecureBinaryData(pk)
            if not CryptoECDSA().VerifyPublicKeyValid(sbdPublicKey):
               raise KeyDataError('Invalid pubkey received: Key=0x%s' % pk)

      # Make sure there aren't too many keys and that M <= N.
      N = len(binRootList)
      if M > N:
         raise BadInputError('M (%d) must be less than N (%d)' % (M, N))
      elif (not 0 < M <= LB_MAXM):
         raise BadInputError('M (%d) must be less than %d' % (M, LB_MAXM))
      elif (not 0 < N <= LB_MAXN):
         raise BadInputError('N (%d) must be less than %d' % (N, LB_MAXN))

      # Build a template for the standard multisig script.
      templateStr  = ''
      templateStr += getOpCode('OP_%d' % M)
      templateStr += '\xff' + int_to_binary(N, widthBytes=1)
      templateStr += getOpCode('OP_%d' % N)
      templateStr += getOpCode('OP_CHECKMULTISIG')

      pksList = []
      for rootPub in binRootList:
         pks = PublicKeySource()
         pks.initialize(isStatic   = False,
                        useCompr   = (len(rootPub) == 33),
                        use160     = False,
                        isUser     = False,
                        isExt      = False,
                        src        = rootPub,
                        chksumPres = False,
                        disDirPay  = False)
         pksList.append(pks)

      cs = ConstructedScript()
      cs.initialize(templateStr, pksList, True, True)
      return cs


   #############################################################################
   @staticmethod
   def UnsortedMultisigConstructed(M, binRootList):
      """
      THIS PROBABLY WON'T BE USED -- IT IS STANDARD CONVENTION TO ALWAYS SORT!
      Consider this code to be here to illustrate using constructed scripts
      with unsorted pubkey lists.
      """
      # Make sure all keys are valid before processing them.
      for pk in binRootList:
         if not len(pk) in [33,65]:
            raise KeyDataError('Invalid pubkey;  length=%d' % len(pk))
         else:
            sbdPublicKey = SecureBinaryData(pk)
            if not CryptoECDSA().VerifyPublicKeyValid(sbdPublicKey):
               raise KeyDataError('Invalid pubkey received: Key=0x%s' % pk)

      # Make sure there aren't too many keys.
      N = len(binRootList)
      if (not 0 < M <= LB_MAXM):
         raise BadInputError('M value must be less than %d' % LB_MAXM)
      elif (not 0 < N <= LB_MAXN):
         raise BadInputError('N value must be less than %d' % LB_MAXN)

      # Build a template for the standard multisig script.
      templateStr  = ''
      templateStr += getOpCode('OP_%d' % M)
      templateStr += '\xff\x01' * N
      templateStr += getOpCode('OP_%d' % N)
      templateStr += getOpCode('OP_CHECKMULTISIG')

      pksList = []
      for rootPub in binRootList:
         pks = PublicKeySource()
         pks.initialize(isStatic   = False,
                        useCompr   = (len(rootPub) == 33),
                        use160     = False,
                        isUser     = False,
                        isExt      = False,
                        src        = rootPub,
                        chksumPres = False,
                        disDirPay  = False)
         pksList.append(pks)

      cs = ConstructedScript()
      cs.initialize(self, templateStr, pksList, True)
      return cs


   #############################################################################
   # Verify that a CS record is valid. Useful as a standalone funct or, more
   # importantly, as a utility function before doing anything critical w/ a rec.
   # INPUT:  A boolean indicating if logs should be written.
   # OUTPUT: None
   # RETURN: A boolean indicating if the record is valid.
   def isValid(self, printToLog):
      """
      Verify that a CS record's construction is valid.
      """
      # Never reset the validity flag! Once a record's invalid, it's invalid.
      recState = True

      # The version needs to be valid. For now, it needs to be 1.
      if self.version != BTCAID_CS_VERSION:
         if printToLog == True:
            LOGINFO('CS record version is wrong. Record is invalid.')
         recState = False

      if self.isChksumPresent:
         if self.checksum is None:
            if printToLog == True:
               LOGINFO('CS record has a checksum flag and no checksum. ' \
                       'Record is invalid.')
            recState = False
         else:
            dataChunk  = self.serialize()
            checkData  = dataChunk[:-4]
            checksum   = dataChunk[-4:]
            compChksum = computeChecksum(checkData)
            if compChksum != checksum:
               if printToLog == True:
                  LOGINFO('CS record has an invalid checksum. Record is ' \
                          'invalid.')
               recState = False

      return recState


   #############################################################################
   def serialize(self):
      bp = BinaryPacker()
      dataStr = self.getDataNoChecksum()
      bp.put(BINARY_CHUNK, dataStr)

      if self.isChksumPresent:
         # Place a checksum in the data. Somewhat redundant due to signatures.
         # Still useful because it protects data sent to signer.
         if self.checksum != None:
            bp.put(BINARY_CHUNK, self.checksum)

      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, serData):
      inKeyList = []
#      bu = makeBinaryUnpacker(serData)  # Need to incorporate somehow?
      inData    = BinaryUnpacker(serData)
      inVer     = inData.get(UINT8)
      inFlags   = inData.get(BITSET, 2)
      inScrTemp = inData.get(VAR_STR)
      inNumKeys = inData.get(UINT8)
      k = 0
      while k < inNumKeys:
         nextKey = inData.get(VAR_STR)
         pks = PublicKeySource().unserialize(nextKey)
         inKeyList.append(pks)
         k += 1

      # If checksum is present, confirm that the other data is correct.
      inChksum = None
      if inFlags.getBit(14):
         inChksum = inData.get(BINARY_CHUNK, 4)

      if not inVer == BTCAID_CS_VERSION:
         # In the future we will make this more of a warning, not error
         raise VersionError('CS version does not match the loaded version')

      self.__init__()
      self.initialize(inScrTemp,
                      inKeyList,
                      inFlags.getBit(15),
                      inFlags.getBit(14),
                      inChksum,
                      inVer)

      return self


   #############################################################################
   # Logic for generating the final script.
   def generateScript(self, inSRPData):
      inPKRPList = []

      # Get the PKRPs from the SRP array passed in.
      curSRP = ScriptRelationshipProof().unserialize(inSRPData)
      inPKRPList.append(curSRP.pkrpList)

      # Generate and return the final script.
      finalScript = assembleScript(self.scriptTemplate,
                                   self.pubKeyBundles,
                                   inPKRPList)
      return finalScript


################################################################################
class ReceiverIdentity(object):
   """
   This defines the object that will actually insert a PKS or CS into a PMTA
   record or an offline ID store.
   """

   #############################################################################
   def __init__(self):
      self.version = BTCAID_RI_VERSION
      self.recType = 0
      self.rec     = ''


   #############################################################################
   @VerifyArgTypes(recType = int,
                   rec     = [str, unicode],
                   ver     = int)
   def initialize(self, recType, rec, ver=BTCAID_RI_VERSION):
      """
      Set all RI values.
      """
      self.recType = recType
      self.rec     = rec
      self.version = ver


   #############################################################################
   def isInitialized(self):
      pass
#      return not (self.multiplier is '' and self.finalKey is '')


   #############################################################################
   # Verify that an RI record is valid.
   def isValid(self):
      """
      Verify that an RI record is valid.
      """
      pass
      # WILL CHECK THE REC TYPE AND RUN REC THROUGH A VERIFIER.
#      recState = True
#
#      # The version needs to be valid. For now, it needs to be 1.
#      if self.version != BTCAID_RI_VERSION:
#         LOGINFO('RI record version is wrong. Record is invalid.')
#         recState = False
#
#      # At least one flag must be set.
#      if self.multUsed == False and self.finalKeyUsed == False:
#         LOGINFO('RI record must have either a multiplier or final key. ' \
#                 'Record is invalid.')
#         recState = False
#
#      return recState


   #############################################################################
   def serialize(self):
      # In BitSet, higher numbers are less significant bits.
      # e.g., To get 0x0002, set bit 14 to True (1).
      # NB: For now, the compression relies on if the raw source is compressed.
      pass
#      flags = BitSet(8)
#      flags.setBit(7, self.finalKeyUsed)
#      flags.setBit(6, self.multUsed)
#
#      bp = BinaryPacker()
#      bp.put(UINT8,   self.version)
#      bp.put(BITSET,  flags, width=1)
#      bp.put(VAR_STR, self.multiplier)
#      bp.put(VAR_STR, self.finalKey)
#
#      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, serData):
      pass
#      inner      = BinaryUnpacker(serData)
#      inVer      = inner.get(UINT8)
#      inFlags    = inner.get(BITSET, 1)
#      inMult     = inner.get(VAR_STR)
#      inFinalKey = inner.get(VAR_STR)
#
#      if not inVer == BTCAID_RI_VERSION:
#         # In the future we will make this more of a warning, not error
#         raise VersionError('RI version does not match the loaded version')
#
#      self.__init__()
#      self.initialize(inMult,
#                      inFlags.getBit(7),
#                      inFlags.getBit(6),
#                      inFinalKey,
#                      inVer)
#
#      return self


################################################################################
class PublicKeyRelationshipProof(object):
   """
   This defines the actual data that proves how multipliers relate to an
   accompanying public key. The public key list is optional but all entries must
   be populated with, at the very least, 0 to indicate an empty VAR_STR.
   """

   #############################################################################
   def __init__(self):
      self.version      = BTCAID_PKRP_VERSION
      self.multiplier   = ''
      self.finalKey     = ''
      self.multUsed     = True
      self.finalKeyUsed = False


   #############################################################################
   @VerifyArgTypes(multiplier   = [str, unicode],
                   finalKey     = [str, unicode],
                   multUsed     = bool,
                   finalKeyUsed = bool,
                   ver          = int)
   def initialize(self, multiplier, finalKeyUsed=False, multUsed=True,
                  finalKey='', ver=BTCAID_PKRP_VERSION):
      """
      Set all PKRP values.
      """
      self.multiplier   = multiplier
      self.finalKey     = finalKey
      self.multUsed     = multUsed
      self.finalKeyUsed = finalKeyUsed
      self.version      = ver


   #############################################################################
   def isInitialized(self):
      return not (self.multiplier is '' and self.finalKey is '')


   #############################################################################
   # Verify that a PKRP record is valid.
   def isValid(self):
      """
      Verify that a PKRP record is valid.
      """
      recState = True

      # The version needs to be valid. For now, it needs to be 1.
      if self.version != BTCAID_PKRP_VERSION:
         LOGINFO('PKRP record version is wrong. Record is invalid.')
         recState = False

      # At least one flag must be set.
      if self.multUsed == False and self.finalKeyUsed == False:
         LOGINFO('PKRP record must have either a multiplier or final key. ' \
                 'Record is invalid.')
         recState = False

      return recState


   #############################################################################
   def serialize(self):
      # In BitSet, higher numbers are less significant bits.
      # e.g., To get 0x0002, set bit 14 to True (1).
      # NB: For now, the compression relies on if the raw source is compressed.
      flags = BitSet(8)
      flags.setBit(7, self.finalKeyUsed)
      flags.setBit(6, self.multUsed)

      bp = BinaryPacker()
      bp.put(UINT8,   self.version)
      bp.put(BITSET,  flags, width=1)
      bp.put(VAR_STR, self.multiplier)
      bp.put(VAR_STR, self.finalKey)

      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, serData):
      inner      = BinaryUnpacker(serData)
      inVer      = inner.get(UINT8)
      inFlags    = inner.get(BITSET, 1)
      inMult     = inner.get(VAR_STR)
      inFinalKey = inner.get(VAR_STR)

      if not inVer == BTCAID_PKRP_VERSION:
         # In the future we will make this more of a warning, not error
         raise VersionError('PKRP version does not match the loaded version')

      self.__init__()
      self.initialize(inMult,
                      inFlags.getBit(7),
                      inFlags.getBit(6),
                      inFinalKey,
                      inVer)

      return self


################################################################################
class ScriptRelationshipProof(object):
   """
   This defines the actual data that proves how multipliers relate to an
   accompanying script.
   """

   #############################################################################
   def __init__(self):
      self.version  = BTCAID_SRP_VERSION
      self.pkrpList = []


   #############################################################################
   @VerifyArgTypes(pkrpList = [PublicKeyRelationshipProof],
                   ver      = int)
   def initialize(self, pkrpList, ver=BTCAID_SRP_VERSION):
      """
      Set all SRP values.
      """
      self.pkrpList = pkrpList
      self.version  = ver


   #############################################################################
   def isInitialized(self):
      return not (self.pkrpList is None or len(self.pkrpList) == 0)


   #############################################################################
   # Verify that an SRP record is valid.
   def isValid(self):
      """
      Verify that a SRP record is valid.
      """
      recState = True

      # The version needs to be valid. For now, it needs to be 1.
      if self.version != BTCAID_SRP_VERSION:
         LOGINFO('SRP record version is wrong. Record is invalid.')
         recState = False

      return recState


   #############################################################################
   def serialize(self):
      bp = BinaryPacker()
      bp.put(UINT8,  self.version)
      bp.put(VAR_INT, len(self.pkrpList), width = 1)
      for pkrpItem in self.pkrpList:
         bp.put(VAR_STR, pkrpItem.serialize())  # Revise this???

      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, serData):
      pkrpList = []
      inner      = BinaryUnpacker(serData)
      inVer      = inner.get(UINT8)
      inNumPKRPs = inner.get(VAR_INT, 1)

      k = 0
      while k < inNumPKRPs:
         nextPKRP = PublicKeyRelationshipProof().unserialize(inner.get(VAR_STR))
         pkrpList.append(nextPKRP)
         k += 1

      if not inVer == BTCAID_SRP_VERSION:
         # In the future we will make this more of a warning, not error
         raise VersionError('SRP version does not match the loaded version')

      self.__init__()
      self.initialize(pkrpList,
                      inVer)

      return self


################################################################################
class PaymentTargetVerifier(object):
   """
   This defines the object that will actually insert a PKRP or SRP into a
   payment request.
   """

   #############################################################################
   def __init__(self):
      self.version = BTCAID_PTV_VERSION
      self.recType = 0
      self.rec     = ''


   #############################################################################
   @VerifyArgTypes(recType = int,
                   rec     = [str, unicode],
                   ver     = int)
   def initialize(self, recType, rec, ver=BTCAID_PTV_VERSION):
      """
      Set all PTV values.
      """
      self.recType = recType
      self.rec     = rec
      self.version = ver


   #############################################################################
   def isInitialized(self):
      pass
#      return not (self.multiplier is '' and self.finalKey is '')


   #############################################################################
   # Verify that a PTV record is valid.
   def isValid(self):
      """
      Verify that a PTV record is valid.
      """
      pass
      # WILL CHECK THE REC TYPE AND RUN REC THROUGH A VERIFIER.
#      recState = True
#
#      # The version needs to be valid. For now, it needs to be 1.
#      if self.version != BTCAID_PTV_VERSION:
#         LOGINFO('PTV record version is wrong. Record is invalid.')
#         recState = False
#
#      # At least one flag must be set.
#      if self.multUsed == False and self.finalKeyUsed == False:
#         LOGINFO('PTV record must have either a multiplier or final key. ' \
#                 'Record is invalid.')
#         recState = False
#
#      return recState


   #############################################################################
   def serialize(self):
      # In BitSet, higher numbers are less significant bits.
      # e.g., To get 0x0002, set bit 14 to True (1).
      # NB: For now, the compression relies on if the raw source is compressed.
      pass
#      flags = BitSet(8)
#      flags.setBit(7, self.finalKeyUsed)
#      flags.setBit(6, self.multUsed)
#
#      bp = BinaryPacker()
#      bp.put(UINT8,   self.version)
#      bp.put(BITSET,  flags, width=1)
#      bp.put(VAR_STR, self.multiplier)
#      bp.put(VAR_STR, self.finalKey)
#
#      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, serData):
      pass
#      inner      = BinaryUnpacker(serData)
#      inVer      = inner.get(UINT8)
#      inFlags    = inner.get(BITSET, 1)
#      inMult     = inner.get(VAR_STR)
#      inFinalKey = inner.get(VAR_STR)
#
#      if not inVer == BTCAID_PTV_VERSION:
#         # In the future we will make this more of a warning, not error
#         raise VersionError('PTV version does not match the loaded version')
#
#      self.__init__()
#      self.initialize(inMult,
#                      inFlags.getBit(7),
#                      inFlags.getBit(6),
#                      inFinalKey,
#                      inVer)
#
#      return self


################################################################################
class PaymentRequest(object):
   """
   This defines the actual payment request sent to a paying entity.
   """

   #############################################################################
   def __init__(self):
      self.version            = BTCAID_PR_VERSION
      self.numTxOutScripts    = 0
      self.reqSize            = 0
      self.unvalidatedScripts = None
      self.daneReqNames       = None
      self.srpList            = None


   #############################################################################
   @VerifyArgTypes(unvalidatedScripts = [VAR_STR],
                   daneReqNames       = [VAR_STR],
                   srpList            = [VAR_STR],
                   ver                = int)
   def initialize(self, unvalidatedScripts, daneReqNames, srpList,
                  ver=BTCAID_PR_VERSION):
      """
      Set all PR values.
      """
      self.version            = ver
      self.numTxOutScripts    = len(unvalidatedScripts)
      self.reqSize            = 0
      self.unvalidatedScripts = unvalidatedScripts
      self.daneReqNames       = daneReqNames
      self.srpList            = srpList

      # Set the request size.
      for x in unvalidatedScripts:
         self.reqSize += packVarInt(self.numTxOutScripts)[1]
         self.reqSize += len(x)
      for y in daneReqNames:
         self.reqSize += packVarInt(self.numTxOutScripts)[1]
         self.reqSize += len(y)
      for z in srpList:
         self.reqSize += packVarInt(self.numTxOutScripts)[1]
         self.reqSize += len(z)


   #############################################################################
   def isInitialized(self):
      return not (self.unvalidatedScripts == None or
                  len(self.unvalidatedScripts) == 0)


   #############################################################################
   # Verify that a PR record is valid.
   def isValid(self):
      """
      Verify that a PR record is valid.
      """
      recState = True

      # The version needs to be valid. For now, it needs to be 1.
      if self.version != BTCAID_PR_VERSION:
         LOGINFO('PR record version is wrong. Record is invalid.')
         recState = False

      return recState


   #############################################################################
   def serialize(self):
      flags = BitSet(16)

      bp = BinaryPacker()
      bp.put(UINT8,  self.version)
      bp.put(BITSET, flags, width=2)
      bp.put(VAR_INT, self.numTxOutScripts, width=3)
      bp.put(VAR_INT, self.reqSize, width=3)
      for scriptItem in self.unvalidatedScripts:
         bp.put(VAR_INT, len(scriptItem), width = 1)
         bp.put(BINARY_CHUNK, scriptItem)
      for daneItem in self.daneReqNames:
         bp.put(VAR_INT, len(daneItem), width = 1)
         bp.put(BINARY_CHUNK, daneItem)
      for srpItem in self.srpList:
         bp.put(VAR_INT, len(srpItem), width = 1)
         bp.put(BINARY_CHUNK, srpItem)

      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, serData):
      unvalidatedScripts = []
      daneReqNames       = []
      srpList            = []

      bu                 = makeBinaryUnpacker(serData)
      inVer              = bu.get(UINT8)
      if inVer != BTCAID_PR_VERSION:
         # In the future we will make this more of a warning, not error
         raise VersionError('PR version does not match the loaded version')
      inFlags            = bu.get(BITSET, 2)
      inNumTxOutScripts  = bu.get(VAR_INT)
      inReqSize          = bu.get(VAR_INT)

      for k in range(0, inNumTxOutScripts):
         nextScript = bu.get(VAR_STR)
         unvalidatedScripts.append(nextScript)
      for l in range(0, inNumTxOutScripts):
         daneName = bu.get(VAR_STR)
         daneReqNames.append(daneName)
      for m in range(0, inNumTxOutScripts):
         nextSRPItem = bu.get(VAR_STR)
         srpList.append(nextSRPItem)

      self.__init__()
      self.initialize(unvalidatedScripts,
                      daneReqNames,
                      srpList,
                      inVer)

      return self


################################################################################
class PMTARecord(object):
   """
   The representation of a payment association (PMTA) DNS record. From Sec. 2.1
   of the draft:

                        1 1 1 1 1 1 1 1 1 1 2 2 2 2 2 2 2 2 2 2 3 3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Payment Network Selector      | Preference                    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | URI String Length             | URI String                    /
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               /
   /                                                               /
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Data Type     | Payment Association Data                      /
   +-+-+-+-+-+-+-+-+                                               /
   /                                                               /
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   """
   def __init__(self):
      self.payNetSel    = PAYNET_TBTC
      self.preference   = 0
      self.uriStr       = ''
      self.dataType     = PAYASSOC_ADDR
      self.payAssocData = ''


   #############################################################################
   @VerifyArgTypes(inPayAssocData = [str, unicode],
                   inPayNet       = int,
                   inPref         = int,
                   inURIStr       = [str, unicode])
   def initialize(self, inPayAssocData, inPayNet=PAYNET_TBTC, inPref=0,
                  inURIStr=''):
      self.payAssocData = inPayAssocData
      self.payNetSel    = inPayNet
      self.preference   = inPref
      self.uriStr       = inURIStr


   #############################################################################
   # Verify that PMTA payment association data is valid.
   # INPUT:  Payment association data to scan.
   # OUTPUT: None
   # RETURN: A boolean indicating if the data is valid.
   def validatePayAssocData(self, paData):
      dataIsValid = False

      # Check the data against PKS and, if necessary, CS. Note that incorrectly
      # formatted data will often cause a formatting error to be thrown. Because
      # we want to try both PKS and CS objects, we'll catch errors and ignore
      # them so that we can try both objects if necessary.
      try:
         tryPKS = PublicKeySource().unserialize(paData)
         if tryPKS.isValid(False) == True:
            dataIsValid = True
      except:
         pass

      if dataIsValid == False:
         try:
            tryCS = ConstructedScript().unserialize(paData)
            if tryCS.isValid() == True:
               dataIsValid = True
         except:
            pass

      return dataIsValid


   #############################################################################
   # Verify that a PMTA record is valid.
   def isValid(self):
      """
      Verify that a PMTA record is valid.
      """
      recState = True

      if not (self.payNetSel == PAYNET_BTC or self.payNetSel == PAYNET_TBTC):
         LOGINFO('PMTA preference value is invalid.')
         recState = False

      if self.preference < 0 or self.preference > 65535:
         LOGINFO('PMTA payment network is invalid.')
         recState = False

      if self.payAssocData == '':
         LOGINFO('PMTA payment association data is empty.')
         recState = False
      else:
         if self.validatePayAssocData(self.payAssocData) == False:
            LOGINFO('PMTA payment association data is invalid.')
            recState = False

      return recState


   #############################################################################
   # NB: There are some discrepancies in the initial draft. Go off the diagram
   # for now and get clarification ASAP.
   def serialize(self):
      bp = BinaryPacker()

      bp.put(UINT16,       self.payNetSel, endianness = BIGENDIAN)
      bp.put(UINT16,       self.preference, endianness = BIGENDIAN)
      bp.put(UINT16,       len(self.uriStr), endianness = BIGENDIAN)
      if len(self.uriStr) > 0 and len(self.uriStr) <= 65535:
         bp.put(BINARY_CHUNK, self.uriStr)
      elif len(self.uriStr) > 65535:
         LOGERROR('The URI string (%d bytes) is too large' % self.uriStr.len())
      bp.put(UINT8,        self.dataType)
      bp.put(BINARY_CHUNK, self.payAssocData)

      return bp.getBinaryString()


   #############################################################################
   def unserialize(self, serData):
      inURIStr       = ''
      bu             = makeBinaryUnpacker(serData)
      inPayNet       = bu.get(UINT16, endianness = BIGENDIAN)
      inPref         = bu.get(UINT16, endianness = BIGENDIAN)
      inURIStrLen    = bu.get(UINT16, endianness = BIGENDIAN)
      if inURIStrLen > 0 and inURIStrLen <= 65535:
         inURIStr = bu.get(BINARY_CHUNK, inURIStrLen)
      inDataType     = bu.get(UINT8)
      inPayAssocData = bu.get(BINARY_CHUNK, bu.getRemainingSize())

      # Validate data
      dataOkay = True
      if inPayNet != PAYNET_TBTC and inPayNet != PAYNET_BTC:
         LOGERROR('Payment network type (%d) is wrong' % inPayNet)
         dataOkay = False

      if inDataType != PAYASSOC_ADDR:
         LOGERROR('Payment association type (%d) is wrong' % inDataType)
         dataOkay = False

      if self.validatePayAssocData(inPayAssocData) == False:
         LOGINFO('PMTA payment association data is invalid.')
         dataOkay = False

      if dataOkay == True:
         self.__init__()
         self.initialize(inPayAssocData,
                         inPayNet,
                         inPref,
                         inURIStr)

      return self
