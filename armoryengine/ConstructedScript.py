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
from armoryengine.Constants import OP_CHECKSIG, OP_CHECKMULTISIG, OP_DUP, \
   OP_HASH160, OP_EQUAL, BTCAID_CS_VERSION, BTCAID_CS_VERSION, \
   BTCAID_PKV_VERSION, BTCAID_PR_VERSION, BTCAID_PTV_VERSION, BTCAID_RI_VERSION
import re
import CppBlockUtils as Cpp

# From the PMTA RFC draft (v0)
PAYASSOC_ADDR = 0  # Sec. 2.1.5
PAYNET_TBTC   = 1  # Sec. 2.1.1 - Testnet
PAYNET_BTC    = 2  # Sec. 2.1.1 - Mainnet

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
      """
      Set MultiplierProof values.
      """
      self.isNull = isNull     # If static, stealth, etc., this can be ignored.
      if isNull:
         self.srcFinger4  = None
         self.dstFinger4  = None
         self.multiplier  = None
      else:
         self.srcFinger4  = srcFinger4 # 1st 4 bytes of BE hash256(root pub key)
         self.dstFinger4  = dstFinger4 # 1st 4 bytes of BE hash256(root pub key)
         self.multiplier  = multiplier # 32 byte BE multiplier


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
def decodeMultiplierProof(serData):
   bu = makeBinaryUnpacker(serData)
   flags = bu.get(BITSET, 1)

   if flags.getBit(0):
      self.initialize(isNull=True)
   else:
      srcFinger4B = bu.get(BINARY_CHUNK, 4)
      dstFinger4B = bu.get(BINARY_CHUNK, 4)

      multiplier.append(bu.get(BINARY_CHUNK, 32))

      return MultiplierProof(False, srcFinger4B, dstFinger4B, multiplier)


################################################################################
class SignableIDPayload(object):
   """
   !!!WORK IN PROGRESS!!!
   This data structure wraps up all the other classes that can go into a DANE
   record into a single, embeddable data type.
   """
   #############################################################################
   def __init__(self, template):
      self.version     = None
      self.createDate  = None
      self.expireDate  = None
      self.payloadType = None  # KeySource or ConstructedScript
      self.payload     = None
      self.rawTemplate = template


   #############################################################################
   def serialize(self):
      pass


#############################################################################
def decodeSignableIDPayload(templateStr):
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
# A function that creates a final script from an escaped script and key list.
# The function isn't CS-specific because there may be instances where
# outsiders want to access the function using data not in a CS object (e.g.,
# apply PTV to keys and then get a derived multisig script).
# INPUT:  An escaped script forming the basis of the final script. (binary str)
#         A list of the base keys. (binary str)
#         PTV object (optional)
# OUTPUT: None
# RETURN: Assembled script  (binary str)
def assembleScript(inEscapedScript, inKeyList, inPTVObj = None):
   # Steps:
   # Perform necessary validity checks.
   # Take binary string and split based on 0xff, which is removed.
   # Grab & remove 1st byte of string on the right.
   # - If byte = 0x00, place 0xff at the end of the string on the left.
   # - Else, confirm # equals the # of PKS & PTV entries.
   #   For each entry, get the public key and apply the PTV.
   #   Insert the key at the end of the string on the left.
   # Reassemble all the strings in the original order.
   # Return the resulting string.
   finalScript = ''

   if (inPTVObj != None) and (len(inPTVObj.pkvList) != len(inKeyList)):
      LOGERROR('assembleScript - Number of keys doesn\'t match number of ' \
               'PTV object entries.')
   else:
      # Use a bytearray to treat the incoming binary data as a string. Split
      # whenever 0xff is encountered. Save the 1st one and then iterate over the
      # others, if any exist. This is where keys will be inserted and escaped 0xff
      # characters restored.
      numProcessedKeys = 0
      scriptArray = bytes(inEscapedScript)
      scriptArrayList = scriptArray.split('\xff')
      finalKeyList = []
      finalScriptList = []
      finalScriptList.append(scriptArrayList[0])

      for fragment in scriptArrayList[1:]:
         if fragment[0] == '\x00':
            # Fix up escaped 0xff and save.
            finalScriptList.append('\xff')
            if len(fragment) > 1:
               finalScriptList.append(fragment[1:])
         else:
            # Remove but keep 1st byte
            numKeys = binary_to_int(fragment[0])
            keyList = []

            # Get the final keys from the key list and PKV objects.
            # We must sort the keys and PKV objects together. While unlikely &
            # foolish, the PKV objects could have a mix of multipliers & final
            # keys. We need to plan for that.
            endIdx = numProcessedKeys + numKeys
            decorated = \
               [[pk,pkv] for pk,pkv in zip(inKeyList[numProcessedKeys:endIdx],
                                    inPTVObj.pkvList[numProcessedKeys:endIdx])]
            decorSort  = sorted(decorated, key=lambda pair: pair[0])
            for i, pair in enumerate(decorSort):
               if pair[1].multUsed:
                  multiplier = pair[1].multiplier
                  finalDerivedKey = HDWalletCrypto().getChildKeyFromMult_SWIG(
                                                                        pair[0],
                                                                     multiplier)
               elif pair[1].finalKeyUsed:
                  finalDerivedKey = pair[1].finalKey
               keyList.append(finalDerivedKey)

            # Advance counter and add to final script list.
            numProcessedKeys += numKeys
            for key in keyList:
               finalScriptList.append(key)
            if len(fragment) > 1:
               finalScriptList.append(fragment[1:])

      # We're done!
      finalScript = ''.join(finalScriptList)

   # We're done! Return the final script.
   return finalScript


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
   def __init__(self, isStatic, useCompr, use160, isUser, isExt, src,
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
   def generateKeyData(self, inPKVList):
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
         for pkv in inPKVList:
            # Get the final public key. If necessary, compress it and/or apply
            # Hash160 to it.
            finalKeyData = HDWalletCrypto().getChildKeyFromMult_SWIG(
                                                                 self.rawSource,
                                                                  pkv.multList)

            if self.useCompr:
               secFinalKeyData = SecureBinaryData(finalKeyData)
               finalKeyDataSBD = CryptoECDSA().CompressPoint(secFinalKeyData)
               finalKeyData = finalKeyDataSBD.toBinStr()

            if self.useHash160:
               finalKeyData = hash160(finalKeyData)

      # We're done! Return the key data.
      return finalKeyData


   #############################################################################
   def getKeyDataNoHash(self):
      retKey = self.rawSource

      if self.useCompr:
         secFinalKeyData = SecureBinaryData(retKey)
         finalKeyDataSBD = CryptoECDSA().CompressPoint(secFinalKeyData)
         retKey = finalKeyDataSBD.toBinStr()

      return retKey


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

      if (self.rawSource is None or len(self.rawSource) == 0):
         if printToLog == True:
            LOGINFO('PKS record has no source material. Record is invalid.')
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
def decodePublicKeySource(serData):
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

   return PublicKeySource(inFlags.getBit(15),
                          inFlags.getBit(14),
                          inFlags.getBit(13),
                          inFlags.getBit(12),
                          inFlags.getBit(11),
                          inRawSrc,
                          inFlags.getBit(10),
                          inFlags.getBit(9),
                          inChksum,
                          inVer)


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

   @VerifyArgTypes(scrTemp    = str,
                   pubSrcs    = [list, tuple],
                   useP2SH    = bool,
                   chksumPres = bool,
                   inChksum   = [str, unicode],
                   ver        = int)
   def __init__(self, scrTemp, pubSrcs, useP2SH, chksumPres, inChksum=None,
                ver=BTCAID_CS_VERSION):
      self.version         = ver
      self.useP2SH         = useP2SH
      self.isChksumPresent = chksumPres
      self.pksBundles   = []

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
      inner.put(UINT8,   sum(len(pksList) for pksList in self.pksBundles)) # Fix?
      for curPKSList in self.pksBundles:
         for curPKSObj in curPKSList:
            inner.put(VAR_STR, curPKSObj.serialize())

      return inner.getBinaryString()


   #############################################################################
   # INPUT:  An escaped script. (binary str)
   #         A list of PublicKeySource objects to include in the CS.
   # OUTPUT: None
   # RETURN: None
   def setTemplateAndPubKeySrcs(self, scrTemp, pubSrcs):
      """
      Inputs:
         scrTemp:  script template  (ff-escaped)
         pubSrcs:  flat list of PublicKeySource objects

      Outputs:
         Sets member vars self.scriptTemplate and self.pksBundles
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
         raise UnserializeError('Template key count doesn\'t match pub list size')

      self.scriptTemplate = scrTemp
      self.pubKeySrcList  = pubSrcs[:]
      self.pksBundles  = []

      # Slice up the pubkey src list into the bundles. Key order doesn't matter
      # as long as the keys line up alongside the escaped bytes. Multisig keys
      # will be lexicographically sorted ONLY in the final TxOut script.
      idx = 0
      for sz in escapedBytes:
         if sz > 0:
            self.pksBundles.append( self.pubKeySrcList[idx:idx+sz] )
            idx += sz


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
   # Logic for generating the final script.
   # INPUT:  Serialized PTV data. (binary str)
   # OUTPUT: None
   # RETURN: The final, unescaped script. (binary str)
   def generateScript(self, inPTVData):

      # Get the PKVs from the PTV array passed in.
      curPTV = decodePaymentTargetVerifier(inPTVData)

      # Get the list of keys from the internal PKS objects.
      scriptKeyList = []
      for curPKSList in self.pksBundles: # List of grouped PKS objects
         for curPKS in curPKSList:       # Actual PKS objects
            curKey = curPKS.getKeyDataNoHash()
            scriptKeyList.append(curKey)

      # Generate and return the final script.
      finalScript = assembleScript(self.scriptTemplate,
                                   scriptKeyList,
                                   curPTV)
      return finalScript


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
def decodeConstructedScript(serData):
   inKeyList = []
   inData    = BinaryUnpacker(serData)
   inVer     = inData.get(UINT8)
   inFlags   = inData.get(BITSET, 2)
   inScrTemp = inData.get(VAR_STR)
   inNumKeys = inData.get(UINT8)

   for k in range(0, inNumKeys):
      nextKey = inData.get(VAR_STR)
      pks = decodePublicKeySource(nextKey)
      inKeyList.append(pks)

   # If checksum is present, confirm that the other data is correct.
   inChksum = None
   if inFlags.getBit(14):
      inChksum = inData.get(BINARY_CHUNK, 4)

   if not inVer == BTCAID_CS_VERSION:
      # In the future we will make this more of a warning, not error
      raise VersionError('CS version does not match the loaded version')

   return ConstructedScript(inScrTemp,
                            inKeyList,
                            inFlags.getBit(15),
                            inFlags.getBit(14),
                            inChksum,
                            inVer)


#############################################################################
def StandardP2PKHConstructed(binRootPubKey):
   """
   Standard Pay-to-public-key-hash script
   """

   if not len(binRootPubKey) in [33,65]:
      raise KeyDataError('Invalid pubkey;  length=%d' % len(binRootPubKey))

   templateStr = getP2PKHStr(False)

   pks = PublicKeySource(isStatic   = False,
                         useCompr   = (len(binRootPubKey) == 33),
                         use160     = True,
                         isUser     = False,
                         isExt      = False,
                         src        = binRootPubKey,
                         chksumPres = False,
                         disDirPay  = False)

   return ConstructedScript(templateStr, [pks], False, True)


#############################################################################
# Check the hash160 call. There were 2 calls, one w/ Hash160 and one w/o.
def StandardP2PKConstructed(binRootPubKey, hash160=False):
   """ This is bare pubkey, usually used with coinbases """
   if not len(binRootPubKey) in [33,65]:
      raise KeyDataError('Invalid pubkey;  length=%d' % len(binRootPubKey))

   templateStr = getP2PKStr(False)

   pks = PublicKeySource(isStatic   = False,
                         useCompr   = (len(binRootPubKey) == 33),
                         use160     = hash160,
                         isUser     = False,
                         isExt      = False,
                         src        = binRootPubKey,
                         chksumPres = False,
                         disDirPay  = False)

   return ConstructedScript(self, templateStr, [pks], False)


#############################################################################
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
      pks = PublicKeySource(isStatic   = False,
                            useCompr   = (len(rootPub) == 33),
                            use160     = False,
                            isUser     = False,
                            isExt      = False,
                            src        = rootPub,
                            chksumPres = False,
                            disDirPay  = False)
      pksList.append(pks)

   return ConstructedScript(templateStr, pksList, True, True)


#############################################################################
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
      pks = PublicKeySource(isStatic   = False,
                            useCompr   = (len(rootPub) == 33),
                            use160     = False,
                            isUser     = False,
                            isExt      = False,
                            src        = rootPub,
                            chksumPres = False,
                            disDirPay  = False)
      pksList.append(pks)

   return ConstructedScript(self, templateStr, pksList, True)


################################################################################
class ReceiverIdentity(object):
   """
   This defines the object that will actually insert a PKS or CS into a PMTA
   record or an offline ID store.
   """

   #############################################################################
   @VerifyArgTypes(ver = int)
   def __init__(self, rec, ver=BTCAID_RI_VERSION):
      """
      Set all RI values.
      """
      self.version = ver
      self.rec     = rec
      if not (isinstance(rec, PublicKeySource) or 
              isinstance(rec, ConstructedScript)):
         LOGERROR('ReceiverIdentity received a record of type %s. PTV object ' \
                  'is invalid.' % type(rec))
         self.rec  = None


   #############################################################################
   # Verify that an RI record is valid.
   def isValid(self):
      """
      Verify that an RI record is valid.
      """
      recState = False

      # The version needs to be valid. For now, it needs to be 1.
      if self.version != BTCAID_RI_VERSION:
         LOGINFO('RI record version is wrong. Record is invalid.')
      else:
         # At least one flag must be set.
         if isinstance(self.rec, PublicKeySource):
            if self.rec.isValid(False) == False:
               LOGINFO('RI record has an invalid PublicKeySource. Record is ' \
                       'invalid.')
            else:
               recState = True
         elif isinstance(self.rec, ConstructedScript):
            if self.rec.isValid(False) == False:
               LOGINFO('RI record has an invalid ConstructedScript. Record ' \
                       'is invalid.')
            else:
               recState = True
         else:
            LOGINFO('RI record has no receiver information. Record is invalid.')

      return recState


   #############################################################################
   def serialize(self):
      recType = -1
      if isinstance(self.rec, PublicKeySource):
         recType = 0
      elif isinstance(self.rec, ConstructedScript):
         recType = 1
      else:
         raise BadInputError('Input record type is invalid')

      bp = BinaryPacker()
      bp.put(UINT8,   self.version)
      bp.put(UINT8,   recType)
      bp.put(VAR_STR, self.rec.serialize())

      return bp.getBinaryString()


   #############################################################################
   # Code that checks the internal records and returns an address type based on
   # the record type and/or scripts inside the records.
   def getAddressType(self):
      retAddrType = 'Exotic'

      # NOTE: This code is a bit simple right now. It makes several assumptions
      # that should hold up in general. 
      if isinstance(self.rec, PublicKeySource):
         retAddrType = 'Single'
      elif isinstance(self.rec, ConstructedScript):
         if (binary_to_int(self.rec.scriptTemplate[0]) == OP_DUP) and \
            (binary_to_int(self.rec.scriptTemplate[-1]) == OP_CHECKSIG):
            retAddrType = 'Single'
         elif (binary_to_int(self.rec.scriptTemplate[0]) == OP_HASH160) and \
              (binary_to_int(self.rec.scriptTemplate[-1]) == OP_EQUAL):
            retAddrType = 'P2SH'
         elif (binary_to_int(self.rec.scriptTemplate[-1]) == OP_CHECKMULTISIG):
            numM = binary_to_int(self.rec.scriptTemplate[0]) - 80
            numN = binary_to_int(self.rec.scriptTemplate[-2]) - 80
            retAddrType = 'Multisig (%d-of-%d)' % (numM, numN)

      return retAddrType


#############################################################################
def decodeReceiverIdentity(serData):
   inner     = BinaryUnpacker(serData)
   inVer     = inner.get(UINT8)
   inRecType = inner.get(UINT8)
   inRecStr  = inner.get(VAR_STR)

   if not inVer == BTCAID_RI_VERSION:
      # In the future we will make this more of a warning, not error
      raise VersionError('RI version does not match the loaded version')

   inRec = None
   if inRecType == 0:
      inRec = decodePublicKeySource(inRecStr)
   elif inRecType == 1:
      inRec = decodeConstructedScript(inRecStr)
   else:
      raise BadInputError('Input type is invalid')

   return ReceiverIdentity(inRec, inVer)


################################################################################
class PublicKeyVerifier(object):
   """
   This defines the actual data that proves how multipliers relate to an
   accompanying public key. The public key list is optional but all entries must
   be populated with, at the very least, 0 to indicate an empty VAR_STR.
   """

   #############################################################################
   @VerifyArgTypes(multiplier   = [str, unicode],
                   finalKey     = [str, unicode],
                   multUsed     = bool,
                   finalKeyUsed = bool,
                   ver          = int)
   def __init__(self, multiplier, finalKeyUsed=False, multUsed=True,
                finalKey='', ver=BTCAID_PKV_VERSION):
      """
      Set all PKV values.
      """
      self.multiplier   = multiplier
      self.finalKey     = finalKey
      self.multUsed     = multUsed
      self.finalKeyUsed = finalKeyUsed
      self.version      = ver


   #############################################################################
   # Verify that a PKV record is valid.
   def isValid(self):
      """
      Verify that a PKV record is valid.
      """
      recState = True

      # The version needs to be valid. For now, it needs to be 1.
      if self.version != BTCAID_PKV_VERSION:
         LOGINFO('PKV record version is wrong. Record is invalid.')
         recState = False

      # At least one flag must be set.
      if self.multUsed == False and self.finalKeyUsed == False:
         LOGINFO('PKV flags must indicate either a multiplier or final key. ' \
                 'Record is invalid.')
         recState = False

      if (self.multiplier is '' and self.finalKey is ''):
         LOGINFO('PKV record has no key material. Record is invalid.')
         recState = False

      if (self.multUsed == True and len(self.multiplier) != 32):
         LOGINFO('Multiplier is not 32 bytes long. Record is invalid.')
         recState = False

      if self.finalKeyUsed:
         if (len(self.finalKey) == 33) and \
            (self.finalKey[0] is not ['\x02', '\x03']):
            LOGINFO('Final key is not a proper compressed key. Record is ' \
                    'invalid.')
            recState = False
         elif (len(self.finalKey) == 65) and (self.finalKey[0] is not '\x04'):
            LOGINFO('Final key is not a proper uncompressed key. Record is ' \
                    'invalid.')
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
def decodePublicKeyVerifier(serData):
   inner      = BinaryUnpacker(serData)
   inVer      = inner.get(UINT8)
   inFlags    = inner.get(BITSET, 1)
   inMult     = inner.get(VAR_STR)
   inFinalKey = inner.get(VAR_STR)

   if not inVer == BTCAID_PKV_VERSION:
      # In the future we will make this more of a warning, not error
      raise VersionError('PKV version does not match the loaded version')

   return PublicKeyVerifier(inMult,
                            inFlags.getBit(7),
                            inFlags.getBit(6),
                            inFinalKey,
                            inVer)


################################################################################
class PaymentTargetVerifier(object):
   """
   This defines the actual data that proves how multipliers relate to an
   accompanying script.
   """

   #############################################################################
   @VerifyArgTypes(pkvList = [PublicKeyVerifier],
                   ver      = int)
   def __init__(self, pkvList, ver=BTCAID_PTV_VERSION):
      """
      Set all PTV values.
      """
      self.pkvList = pkvList
      self.version  = ver


   #############################################################################
   # Verify that an PTV record is valid.
   def isValid(self):
      """
      Verify that a PTV record is valid.
      """
      recState = True

      # The version needs to be valid. For now, it needs to be 1.
      if self.version != BTCAID_PTV_VERSION:
         LOGINFO('PTV record version is wrong. Record is invalid.')
         recState = False

      if (self.pkvList is None or len(self.pkvList) == 0):
         LOGINFO('PTV record has no PKV records. Record is invalid.')
         recState = False

      return recState


   #############################################################################
   def serialize(self):
      bp = BinaryPacker()
      bp.put(UINT8,  self.version)
      bp.put(VAR_INT, len(self.pkvList), width = 1)
      for pkvItem in self.pkvList:
         bp.put(VAR_STR, pkvItem.serialize())  # Revise this???

      return bp.getBinaryString()


#############################################################################
def decodePaymentTargetVerifier(serData):
   pkvList = []
   inner      = BinaryUnpacker(serData)
   inVer      = inner.get(UINT8)
   inNumPKVs = inner.get(VAR_INT, 1)

   k = 0
   while k < inNumPKVs:
      nextPKV = decodePublicKeyVerifier(inner.get(VAR_STR))
      pkvList.append(nextPKV)
      k += 1

   if not inVer == BTCAID_PTV_VERSION:
      # In the future we will make this more of a warning, not error
      raise VersionError('PTV version does not match the loaded version')

   return PaymentTargetVerifier(pkvList,
                                  inVer)


################################################################################
class PaymentRequest(object):
   """
   This defines the actual payment request sent to a paying entity.
   """

   #############################################################################
   @VerifyArgTypes(unvalidatedScripts = [VAR_STR],
                   daneReqNames       = [VAR_STR],
                   ptvList            = [VAR_STR],
                   ver                = int)
   def __init__(self, unvalidatedScripts, daneReqNames, ptvList,
                ver=BTCAID_PR_VERSION):
      """
      Set all PR values.
      """
      self.version            = ver
      self.numTxOutScripts    = len(unvalidatedScripts)
      self.reqSize            = 0
      self.unvalidatedScripts = unvalidatedScripts
      self.daneReqNames       = daneReqNames
      self.ptvList            = ptvList

      # Set the request size.
      for x in unvalidatedScripts:
         self.reqSize += packVarInt(self.numTxOutScripts)[1]
         self.reqSize += len(x)
      for y in daneReqNames:
         self.reqSize += packVarInt(self.numTxOutScripts)[1]
         self.reqSize += len(y)
      for z in ptvList:
         self.reqSize += packVarInt(self.numTxOutScripts)[1]
         self.reqSize += len(z)


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

      if (self.unvalidatedScripts == None or len(self.unvalidatedScripts) == 0):
         LOGINFO('PR record has no scripts. Record is invalid.')
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
      for ptvItem in self.ptvList:
         bp.put(VAR_INT, len(ptvItem), width = 1)
         bp.put(BINARY_CHUNK, ptvItem)

      return bp.getBinaryString()


#############################################################################
def decodePaymentRequest(serData):
   unvalidatedScripts = []
   daneReqNames       = []
   ptvList            = []

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
      nextPTVItem = bu.get(VAR_STR)
      ptvList.append(nextPTVItem)

   return PaymentRequest(unvalidatedScripts,
                         daneReqNames,
                         ptvList,
                         inVer)


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
   @VerifyArgTypes(inPayAssocData = [str, unicode],
                   inPayNet       = int,
                   inPref         = int,
                   inURIStr       = [str, unicode])
   def __init__(self, inPayAssocData, inPayNet=PAYNET_TBTC, inPref=0,
                inURIStr=''):
      """
      Set all PMTA values.
      """
      self.dataType     = PAYASSOC_ADDR
      self.payAssocData = inPayAssocData
      self.payNetSel    = inPayNet
      self.preference   = inPref
      self.uriStr       = inURIStr


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
         if validatePayAssocData(self.payAssocData) == False:
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
# Verify that PMTA payment association data is valid.
# INPUT:  Payment association data to scan.
# OUTPUT: None
# RETURN: A boolean indicating if the data is valid.
def validatePayAssocData(paData):
   dataIsValid = False

   # Check the data against PKS and, if necessary, CS. Note that incorrectly
   # formatted data will often cause a formatting error to be thrown. Because
   # we want to try both PKS and CS objects, we'll catch errors and ignore
   # them so that we can try both objects if necessary.
   try:
      tryPKS = decodePublicKeySource(paData)
      if tryPKS.isValid(False) == True:
         dataIsValid = True
   except:
      pass

   if dataIsValid == False:
      try:
         tryCS = decodeConstructedScript(paData)
         if tryCS.isValid() == True:
            dataIsValid = True
      except:
         pass

   return dataIsValid


#############################################################################
def decodePMTARecord(serData):
   retRecord = None
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

   if validatePayAssocData(inPayAssocData) == False:
      LOGINFO('PMTA payment association data is invalid.')
      dataOkay = False

   if dataOkay == True:
      retRecord = PMTARecord(inPayAssocData,
                             inPayNet,
                             inPref,
                             inURIStr)

   return retRecord
