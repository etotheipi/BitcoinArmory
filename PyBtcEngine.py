################################################################################
#
# Project: PyBtcEngine
# Author:  Alan Reiner
# Date:   11 July, 2011
# Descr:   Modified from the Sam Rushing code.   The original header comments
#        of the original code is below, maintaining reference to the original 
#        source code, for reference.  The code was pulled from his git repo
#        on 10 July, 2011.
#
################################################################################


# -*- Mode: Python -*-
# A prototype bitcoin implementation.
#
# Author: Sam Rushing. http://www.nightmare.com/~rushing/
# July 2011.
#
# Status: much of the protocol is done.  The crypto bits are now
#   working, and I can verify 'standard' address-to-address transactions.
#   There's a simple wallet implementation, which will hopefully soon
#   be able to transact actual bitcoins.
# Todo: consider implementing the scripting engine.
# Todo: actually participate in the p2p network rather than being a lurker.
#
# One of my goals here is to keep the implementation as simple and small
#   as possible - with as few outside dependencies as I can get away with.
#   For that reason I'm using ctypes to get to openssl rather than building
#   in a dependency on M2Crypto or any of the other crypto packages.

import copy
import hashlib
import random
import socket
import time
import os
import pickle
import string
import sys
import lisecdsa

import asyncore
import asynchat
import asynhttp


from struct import pack, unpack
import hashlib 
from pprint import pprint as pp

def sha1(bits):
   return hashlib.new('sha1', bits).digest()
def sha256(bits):
   return hashlib.new('sha256', bits).digest()
def ripemd160(bits):
   return hashlib.new('ripemd160', bits).digest()

# these are overriden for testnet
BITCOIN_PORT = 8333
BITCOIN_MAGIC = '\xf9\xbe\xb4\xd9'
BLOCKS_PATH = 'blocks.bin'
genesis_block_hash = '000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f'
b58_digits = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

LITTLEENDIAN = '<';
BIGENDIAN = '>';
COIN = 1e8


def default_error_function(msg):
   print ''
   print '***ERROR*** : ', msg
   print 'Aborting run'
   exit(0)


raiseError = default_error_function

def setErrorFunction( fn ):
   raiseError = fn


class BadAddress (Exception):
   pass

##### Switch endian-ness #####
def hex_switchEndian(s):
   pairList = [s[i]+s[i+1] for i in range(0,len(s),2)]
   return ''.join(pairList[::-1])
def binary_switchEndian(s):
   return s[::-1]
 

##### INT/HEXSTR #####
def int_to_hex(i, widthBytes=0, endOut=LITTLEENDIAN):
   h = hex(i)[2:]
   if isinstance(i,long):
      h = h[:-1]
   if len(h)%2 == 1:
      h = '0'+h
   if not widthBytes==0:
      nZero = 2*widthBytes - len(h)
      if nZero > 0:
         h = '0'*nZero + h
   if endOut==LITTLEENDIAN:
      h = hex_switchEndian(h)
   return h   
def hex_to_int(h, endIn=LITTLEENDIAN):
   hstr = h[:]  # copies data, no references
   if endIn==LITTLEENDIAN:
      hstr = hex_switchEndian(hstr)
   return( int(hstr, 16) )
 

##### HEXSTR/BINARYSTR #####
def hex_to_binary(h, endIn=LITTLEENDIAN, endOut=LITTLEENDIAN):
   bout = h[:]  # copies data, no references
   if not endIn==endOut:
      bout = hex_switchEndian(bout) 
   return bout.decode('hex_codec')
def binary_to_hex(b, endOut=LITTLEENDIAN, endIn=LITTLEENDIAN):
   hout = b.encode('hex_codec')
   if not endOut==endIn:
      hout = hex_switchEndian(hout) 
   return hout

 
##### INT/BINARYSTR #####
def int_to_binary(i, widthBytes=0, endOut=LITTLEENDIAN):
   h = int_to_hex(i,widthBytes)
   return hex_to_binary(h, endOut=endOut)
def binary_to_int(b, endIn=LITTLEENDIAN):
   h = binary_to_hex(b, endIn, LITTLEENDIAN)
   return hex_to_int(h)
 

##### INT/BASE58STR #####
def int_to_base58Str(n):
   b58 = ''
   while n > 0:
      n, r = divmod (n, 58)
      b58 = b58_digits[r] + b58
   return b58
def base58Str_to_int(s):
   n = 0
   for ch in s:
      n *= 58
      digit = b58_digits.index (ch)
      n += digit
   return n

##### BASE58STR/ADDRSTR #####
def base58Str_to_addrStr(b58str):
   return '1'+b58str;
def addrStr_to_base58Str(addr):
   if not addr[0]=='1':
      raise BadAddress(addr)
   else:
      return addr[1:]
     

##### BINARYSTR/HASHDIGEST #####
def hash256(s):
   return sha256(sha256(s))

##### BINARYSTR/ADDRESSDIGEST #####
def hash160(s):
   return ripemd160(sha256(s))

##### hex/HASHDIGEST #####
def hex_to_hexHash256(h, endIn=LITTLEENDIAN, endOut=LITTLEENDIAN):
   strBinary = hex_to_binary(h, endIn, LITTLEENDIAN)
   digestBinary = hash256(strBinary)
   digestHex = binary_to_hex(digestBinary, LITTLEENDIAN, endOut)
   return digestHex

##### HEXSTR/BINARYADDRESSDIGEST
def hex_to_hexHash160(h, endIn=LITTLEENDIAN, endOut=LITTLEENDIAN):
   strBinary = hex_to_binary(h, endIn, LITTLEENDIAN)
   digestBinary = hash160(strBinary)
   digestHex = binary_to_hex(digestBinary, LITTLEENDIAN, endOut)
   return digestHex

##### HEXPUBLICKEY/ADDRSTR
def binPubKey_to_addrStr(binStr, endIn=LITTLEENDIAN):
   binKey = binStr[:] if endIn==LITTLEENDIAN else binary_switchEndian(binStr)
   binKeyHash = hash160(binKey)
   checksum   = hash256('\x00' + binKeyHash)
   binAddrStr = binKeyHash + checksum[:4]
   intAddrStr = binary_to_int(binAddrStr, endIn=BIGENDIAN)  # why the endian switch required!?
   b58AddrStr =           int_to_base58Str(intAddrStr)
   return                        base58Str_to_addrStr(b58AddrStr)

##### HEXPUBLICKEY/ADDRSTR
def hexPubKey_to_addrStr(hexStr, endIn=LITTLEENDIAN):
   hexKey = hexStr[:] if endIn==LITTLEENDIAN else hex_switchEndian(hexStr)
   binKey = hex_to_binary(hexKey)
   return binPubKey_to_addrStr(binKey)


def addrStr_to_binaryPair(addr):
   b58Str  = addrStr_to_base58Str(addr)
   intAddr =            base58Str_to_int(b58Str)
   binAddr =                         int_to_binary(intAddr, endOut=BIGENDIAN)
   return (binAddr[:-4], binAddr[-4:])  # why the endian switch required!?
   

##### ADDRESS VERIFICATION #####
def addrStr_isValid(addr):
   binKeyHash, targetChk = addrStr_to_binaryPair(addr)
   binKeyHashHash = hash256('\x00' + binKeyHash)
   return binKeyHashHash[:4] == targetChk



##### FLOAT/BTC #####
# https://en.bitcoin.it/wiki/Proper_Money_Handling_(JSON-RPC)
def ubtc_to_floatStr(n):
   return '%d.%08d' % divmod (n, COIN)
def floatStr_to_ubtc(s):
   return long(round(float(s) * COIN))
def float_to_btc (f):
   return long (round(f * COIN))


##### HEXSTR/VARINT #####
def packVarInt(n):
   if   n < 0xfd:  return [chr(n), 1]
   elif n < 1<<16: return ['\xfd'+pack('<H',n), 3]
   elif n < 1<<32: return ['\xfe'+pack('<I',n), 5]
   else:           return ['\xff'+pack('<Q',n), 9]

def unpackVarInt(hvi):
   """ Returns a pair: the specified integer and number of bytes read """
   code = unpack('<B', hvi[0])[0]
   if   code  < 0xfd: return [code, 1]
   elif code == 0xfd: return [unpack('<H',hvi[1:3])[0], 3]
   elif code == 0xfe: return [unpack('<I',hvi[1:5])[0], 5]
   elif code == 0xff: return [unpack('<Q',hvi[1:9])[0], 9]
   else: assert(False)


def padHexStrLeft(hexStr, nBytes, padChar='0'):
   needMoreChars = max(0, (nBytes*2) - len(hexStr))
   return (padChar*needMoreChars) + hexStr
   
def padHexStrRight(hexStr, nBytes, padChar='0'):
   needMoreChars = max(0, (nBytes*2) - len(hexStr))
   return hexStr + padChar*needMoreChars

def padBinaryLeft(binStr, nBytes, padByte='\x00'):
   needMoreChars = max(0, nBytes-len(binStr))
   return padByte*needMoreChars + binStr

def padBinaryRight(binStr, nBytes, padByte='\x00'):
   needMoreChars = max(0, nBytes-len(binStr))
   return binStr + padByte*needMoreChars



################################################################################
# ECDSA CLASSES
#
#    Based on the ECDSA code posted by Lis on the Bitcoin forums: 
#    http://forum.bitcoin.org/index.php?topic=23241.0
#
################################################################################

# The following params are common to ALL bitcoin elliptic curves (secp256k1)
_p  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2FL
_r  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141L
_b  = 0x0000000000000000000000000000000000000000000000000000000000000007L
_a  = 0x0000000000000000000000000000000000000000000000000000000000000000L
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798L
_Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8L

EC_Point = lisecdsa.Point
EC_Curve = lisecdsa.CurveFp( _p, _a, _b )
EC_Sig   = lisecdsa.Signature
EC_GenPt = EC_Point( EC_Curve, _Gx, _Gy, _r )
EC_Order = EC_GenPt.order()

### TODO:  https://en.bitcoin.it/wiki/Script says scripts should be BIGENDIAN?!?!
def binScript_to_binSigKey(binStr):
   # Returns [signature, pubKey, totalBytes]
   # TODO:  check when sometimes it returns only a sig, sometimes sig&key
   szSig = binary_to_int(binStr[0])
   binarySignature = binStr[1:szSig+1]
   szKey = binary_to_int(binStr[szSig+1])
   binaryKey = binStr[2+szSig:2+szSig+szKey]
   return (binarySignature, binaryKey, 2+szKey+szSig)

def intRS_to_derSig(r,s):
   rBin   = int_to_binary(r)
   sBin   = int_to_binary(s)
   rSize  = int_to_binary(len(rBin))
   sSize  = int_to_binary(len(sBin))
   rsSize = int_to_binary(len(rBin) + len(sBin) + 4)
   return '\x30' + rsSize + '\x02' + rSize + rBin + '\x02' + sSize + sBin

def derSig_to_intRS(binStr):
   # There was nothing easy about figuring out how these numbers were encoded
   codeByte = binStr[0]
   nBytes   = binary_to_int(binStr[1])
   rsStr    = binStr[2:]
   assert(codeByte == '\x30')
   assert(nBytes == len(rsStr))

   # Read r
   codeByte  = rsStr[0]
   rBytes    = binary_to_int(rsStr[1])
   r         = binary_to_int(rsStr[2:2+rBytes])
   assert(codeByte == '\x02')
   sStr      = rsStr[2+rBytes:]

   # Read s
   codeByte  = sStr[0]
   sBytes    = binary_to_int(sStr[1])
   s         = binary_to_int(sStr[2:2+sBytes])
   assert(codeByte == '\x02')
   return (r,s)



class EcPrivKey(object):

   # TODO:  check for python <=2.3 to warn if randrange gens "small" numbers
   # And yes, a private key is really just a random number

   def __init__(self, privInt=None):
      if privInt==None: 
         self.secretInt = random.randrange(EC_Order)   
      else:             
         self.secretInt = privInt

      self.publicPoint = EC_GenPt * self.secretInt
      self.lisPubKey  = lisecdsa.Public_key( EC_GenPt, self.publicPoint )
      self.lisPrivKey = lisecdsa.Private_key( self.lisPubKey, self.secretInt )

   def to_hex(self, endian=LITTLEENDIAN):
      hexSecret = int_to_hex(self.secretInt, endian)
      assert(len(hexSecret) == 64)
      return hexSecret

   def to_binary(self, endian=LITTLEENDIAN):
      binSecret = int_to_binary(self.secretInt, endian)
      assert(len(binSecret) == 32)
      return binSecret

   def derSignature(self, binHashToSign):
      intHash = binary_to_int(binHashToSign)
      sig = self.lisPrivKey.sign(intHash, random.randrange(EC_Order))
      return intRS_to_derSig(sig.r, sig.s)
      


class EcPubKey(object):
   """ Init EcPubKey with either EcPrivKey, or 65-bit-string from script """
   def __init__(self, initObj, endianIn=LITTLEENDIAN):
      # InitObj is either a EcPrivKey or BINARY public key str (65 bytes)
      if isinstance(initObj, EcPrivKey):
         self.intPubKeyX = initObj.publicPoint.x()
         self.intPubKeyY = initObj.publicPoint.y()
         self.binary  = self.to_binary()
      else:
         chk, binXp, binYp = initObj[0], initObj[1:33], initObj[33:]
         assert(len(initObj) == 65 and chk == '\x04')
         # Script values are stored in big-endian
         self.intPubKeyX = binary_to_int(binXp, endIn=endianIn)
         self.intPubKeyY = binary_to_int(binYp, endIn=endianIn)
         self.binary = initObj

      # If there is an error here about "contains_point" try switching endian
      self.publicPoint = EC_Point(EC_Curve, self.intPubKeyX, self.intPubKeyY)
      self.lisPubKey = lisecdsa.Public_key( EC_GenPt, self.publicPoint )
      

   def to_hex(self, endian=LITTLEENDIAN):
      hexXp = int_to_hex(self.intPubKeyX, endOut=endian)
      hexYp = int_to_hex(self.intPubKeyY, endOut=endian)
      assert(len(hexXp) == 64)
      assert(len(hexYp) == 64)
      return '04' + hexXp + hexYp

   def to_binary(self, endian=LITTLEENDIAN):
      leadByte = pack(endian+'B', 4)
      binXp = int_to_binary(self.intPubKeyX, endOut=endian);
      binYp = int_to_binary(self.intPubKeyY, endOut=endian);
      assert(len(binXp) == 32)
      assert(len(binYp) == 32)
      return leadByte + binXp + binYp

   def to_addrStr(self):
      return binPubKey_to_addrStr(self)
      
   def verifyBinarySignature(self, binHashToVerify, derSig):
      intHash = binary_to_int(binHashToVerify)
      (r,s) = derSig_to_intRS(derSig)
      lisSignature = EC_Sig(r,s)
      return self.lisPubKey.verifies(intHash, lisSignature)


def calc_EcPubKey_from_EcPrivKey(key):
   return EcPubKey(key)
   
def VerifyEcKeyPair(pubkey, privkey):
   return (pubkey.publicPoint == privkey.publicPoint)
      

def hex_to_EcPubKey(hexStr):
   binaryKey65B = hex_to_binary(hexStr)
   assert(len(binaryKey65B) == 65)
   return EcPubKey(binaryKey65B)

def hexPointXY_to_EcPubKey(hexXp, hexYp):
   binXp = hex_to_binary(hexXp)
   binYp = hex_to_binary(hexYp)
   binaryKey65B = pack('<B',4) + binXp + binYp
   assert(len(binaryKey65B) == 65)
   return EcPubKey(binaryKey65B)


# Finally done with all the base conversion functions and ECDSA code
# Now define the classes for the objects that will use this

################################################################################
################################################################################
#  Classes for reading and writing large binary objects
################################################################################
################################################################################
UBYTE, USHORT, UINT32, UINT64, VAR_INT, BINARY_CHUNK = range(6)

# Seed this object with binary data, then read in its pieces sequentially
class BinaryUnpacker(object):
   def __init__(self, binaryStr):
      self.binaryStr = binaryStr
      self.pos = 0

   def getSize(self):
      return len(self.binaryStr)

   def getRemainingSize(self):
      return len(self.binaryStr) - self.pos

   def getBinaryString(self):
      return self.binaryStr

   def advance(self, bytesToAdvance):
      self.pos += bytesToAdvance

   def rewind(self, bytesToRewind):
      self.pos -= bytesToRewind

   def resetPosition(self, toPos=0):
      self.pos = toPos

   def getPosition(self):
      return self.pos

   def get(self, varType, sz=0, endianness=LITTLEENDIAN):
      pos = self.pos
      if varType == UINT32:
         value = binary_to_int(self.binaryStr[pos:pos+4], endianness)
         self.advance(4)
         return value
      elif varType == UINT64:
         value = binary_to_int(self.binaryStr[pos:pos+8], endianness)
         self.advance(8)
         return value
      elif varType == UBYTE:
         value = binary_to_int(self.binaryStr[pos:pos+1], endianness)
         self.advance(1)
         return value
      elif varType == USHORT:
         value = binary_to_int(self.binaryStr[pos:pos+2], endianness)
         self.advance(2)
         return value
      elif varType == VAR_INT:
         [value, nBytes] = unpackVarInt(self.binaryStr[pos:])
         self.advance(nBytes)
         return value
      elif varType == BINARY_CHUNK:
         binOut = self.binaryStr[pos:pos+sz]
         self.advance(sz)
         return binOut
      
      print 'Var Type not recognized!  VarType =', varType
      assert(False)
         
         

# Start a buffer for concatenating various blocks of binary data
class BinaryPacker(object):
   def __init__(self):
      self.binaryConcat = []

   def getSize(self):
      return sum([len(a) for a in self.binaryConcat])

   def getBinaryString(self):
      return ''.join(self.binaryConcat)

   def __str__(self):
      return self.getBinaryString()
      

   def put(self, varType, theData, endianness=LITTLEENDIAN):
      if   varType == UBYTE:
         self.binaryConcat += int_to_binary(theData, 1, endianness)
      elif varType == USHORT:
         self.binaryConcat += int_to_binary(theData, 2, endianness)
      elif varType == UINT32:
         self.binaryConcat += int_to_binary(theData, 4, endianness)
      elif varType == UINT64:
         self.binaryConcat += int_to_binary(theData, 8, endianness)
      elif varType == VAR_INT:
         self.binaryConcat += packVarInt(theData)[0]
      elif varType == BINARY_CHUNK:
         self.binaryConcat += theData
      else:
         print 'Var Type not recognized!  VarType =', varType
         assert(False)

################################################################################


################################################################################
#  Transaction Classes
################################################################################

indent = ' '*3

#####
class OutPoint(object):
   #def __init__(self, txOutHash, outIndex):
      #self.txOutHash = txOutHash
      #self.index     = outIndex

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         opData = toUnpack 
      else: 
         opData = BinaryUnpacker( toUnpack )

      self.txOutHash = opData.get(BINARY_CHUNK, 32)
      self.index     = opData.get(UINT32)
      return self

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(BINARY_CHUNK, self.txOutHash)
      binOut.put(UINT32, self.index)
      return binOut.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print indstr + 'OutPoint:'
      print indstr + indent + 'PrevTxHash:', binary_to_hex(self.txOutHash)
      print indstr + indent + 'TxOutIndex:', self.index
      

#####
class TxIn(object):
   #def __init__(self, outpt, binScript, intSeq):
      #self.outpoint  = outpt
      #self.binScript = script
      #self.intSeq    = intSeq

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         txInData = toUnpack 
      else: 
         txInData = BinaryUnpacker( toUnpack )

      self.outpoint  = OutPoint().unserialize( txInData.get(BINARY_CHUNK, 36) ) 
      scriptSize     = txInData.get(VAR_INT)
      self.binScript = txInData.get(BINARY_CHUNK, scriptSize)
      self.intSeq    = txInData.get(UINT32)
      return self

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(BINARY_CHUNK, self.outpoint.serialize() )
      binOut.put(VAR_INT, len(self.binScript))
      binOut.put(BINARY_CHUNK, self.binScript)
      binOut.put(UINT32, self.intSeq)
      return binOut.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print indstr + 'TxIn:'
      self.outpoint.pprint(nIndent+1)
      print indstr + indent + 'SCRIPT: ', binary_to_hex(self.binScript)[:32] + '...'
      print indstr + indent + 'Seq     ', self.intSeq
      

#####
class TxOut(object):
   #def __init__(self, value, binPKScript):
      #self.value  = value
      #self.binPKScript = binPKScript

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         txOutData = toUnpack 
      else: 
         txOutData = BinaryUnpacker( toUnpack )

      self.value       = txOutData.get(UINT64)
      scriptSize       = txOutData.get(VAR_INT) 
      self.binPKScript = txOutData.get(BINARY_CHUNK, scriptSize)
      return self

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(UINT64, self.value)
      binOut.put(VAR_INT, len(self.binPKScript))
      binOut.put(BINARY_CHUNK, self.binPKScript)
      return binOut.getBinaryString()

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print indstr + 'TxOut:'
      print indstr + indent + 'Value:  ', self.value, '(', float(self.value) / COIN, ')'
      print indstr + indent + 'SCRIPT: ', binary_to_hex(self.binPKScript)[:32], '...'


#####
class Tx(object):
   #def __init__(self, version, txInList, txOutList, lockTime):
      #self.version    = version
      #self.numInputs  = len(txInList)
      #self.inputs     = txInList
      #self.numOutputs = len(txOutList)
      #self.outputs    = txOutList
      #self.lockTime   = lockTime

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(UINT32, self.version)
      binOut.put(VAR_INT, self.numInputs)
      for txin in self.inputs:
         binOut.put(BINARY_CHUNK, txin.serialize())
      binOut.put(VAR_INT, self.numOutputs)
      for txout in self.outputs:
         binOut.put(BINARY_CHUNK, txout.serialize())
      binOut.put(UINT32, self.lockTime)
      return binOut.getBinaryString()

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         txData = toUnpack 
      else: 
         txData = BinaryUnpacker( toUnpack )

      self.inputs     = []
      self.outputs    = []
      self.version    = txData.get(UINT32)
      self.numInputs  = txData.get(VAR_INT)
      for i in range(self.numInputs):
         self.inputs.append( TxIn().unserialize(txData) )
      self.numOutputs = txData.get(VAR_INT)
      for i in range(self.numOutputs):
         self.outputs.append( TxOut().unserialize(txData) )
      self.lockTime   = txData.get(UINT32)
      return self
      
   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      thisHash = hash256(self.serialize())
      print indstr + 'Transaction:'
      print indstr + indent + 'TxHash:   ', binary_to_hex(thisHash)
      print indstr + indent + 'Version:  ', self.version
      print indstr + indent + 'nInputs:  ', self.numInputs
      print indstr + indent + 'nOutputs: ', self.numOutputs
      print indstr + indent + 'LockTime: ', self.lockTime
      print indstr + indent + 'Inputs: '
      for inp in self.inputs:
         inp.pprint(nIndent+2)
      print indstr + indent + 'Outputs: '
      for out in self.outputs:
         out.pprint(nIndent+2)
      


################################################################################
#  Block Information
################################################################################


class BlockHeader(object):
   #def __init__(self, version, prevBlock, merkleRoot, timestamp, diff, nonce):
      #self.version     = version
      #self.prevBlkHash = prevBlock
      #self.merkleRoot  = merkleRoot
      #self.timestamp   = timestamp
      #self.difficulty  = diff
      #self.nonce       = nonce
      # TODO: forgot to put this in here
      #self.numTx       = numTx

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(UINT32, self.version)
      binOut.put(BINARY_CHUNK, self.prevBlkHash)
      binOut.put(BINARY_CHUNK, self.merkleRoot)
      binOut.put(UINT32, self.timestamp)
      binOut.put(UINT32, self.difficulty)
      binOut.put(UINT32, self.nonce)
      return binOut.getBinaryString()

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         blkData = toUnpack 
      else: 
         blkData = BinaryUnpacker( toUnpack )
     
      self.version     = blkData.get(UINT32)
      self.prevBlkHash = blkData.get(BINARY_CHUNK, 32)
      self.merkleRoot  = blkData.get(BINARY_CHUNK, 32)
      self.timestamp   = blkData.get(UINT32)
      self.difficulty  = blkData.get(UINT32)
      self.nonce       = blkData.get(UINT32)
      self.theHash     = hash256(self.serialize())
      return self

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print indstr + 'BlockHeader:'
      print indstr + indent + 'Hash:      ', binary_to_hex( self.theHash )
      print indstr + indent + 'Version:   ', self.version     
      print indstr + indent + 'PrevBlock: ', binary_to_hex(self.prevBlkHash)
      print indstr + indent + 'MerkRoot:  ', binary_to_hex(self.merkleRoot)
      print indstr + indent + 'Timestamp: ', self.timestamp 
      print indstr + indent + 'Target:    ', self.difficulty
      print indstr + indent + 'Nonce:     ', self.nonce    


class BlockData(object):
   #def __init__(self, header, numTx, txList):
      #self.numTx = txList
      #self.txList = txList
      #self.merkleTree = []
      #self.merkleRoot = ''

   def __init__(self):
      self.merkleTree = []
      self.merkleRoot = ''

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(VAR_INT, self.numTx)
      for tx in self.txList:
         binOut.put(BINARY_CHUNK, tx.serialize())
      return binOut.getBinaryString()

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         blkData = toUnpack 
      else: 
         blkData = BinaryUnpacker( toUnpack )

      self.txList = []
      self.numTx  = blkData.get(VAR_INT)
      for i in range(self.numTx):
         self.txList.append( Tx().unserialize(blkData) )
      self.merkleTree = []
      self.merkleRoot = ''
      return self



   def getMerkleRoot(self):
      if len(self.merkleTree)==0 and not self.numTx==0:
         #Create the merkle tree 
         self.merkleTree = [hash256(tx.serialize()) for tx in self.txList]
         sz = len(self.merkleTree)
         while sz > 1:
            hashes = self.merkleTree[-sz:]
            mod2 = sz%2
            for i in range(sz/2):
               self.merkleTree.append( hash256(hashes[2*i] + hashes[2*i+1]) )
            if mod2==1:
               self.merkleTree.append( hash256(hashes[-1] + hashes[-1]) )
            sz = (sz+1) / 2
      else:
         # TODO:  What do we do if no Tx's in this block?
         print 'No Transactions in block!  What do we do with the hash??'
      self.merkleRoot = self.merkleTree[-1]
      return self.merkleRoot

   def printMerkleTree(self, reverseHash=False, indent=''):
         print indent + 'Printing Merkle Tree:'
         if reverseHash:
            print indent + '(hashes will be reversed, like shown on BlockExplorer.com)'
         root = self.getMerkleRoot()
         print indent + 'Merkle Root:', binary_to_hex(root)
         for h in self.merkleTree:
            phash = binary_to_hex(h) if not reverseHash else binary_to_hex(h, endOut=BIGENDIAN)
            print indent + '\t' + phash
         

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print indstr + 'BlockData:'
      print indstr + indent + 'MerkleRoot:  ', binary_to_hex(self.getMerkleRoot())
      print indstr + indent + 'NumTx:       ', self.numTx
      for tx in self.txList:
         tx.pprint(nIndent+1)
      


class Block(object):
   #def __init__(self, header, blkdata):
      #self.blockHeader = header
      #self.blockData = blkdata

   def serialize(self):
      binOut = BinaryPacker()
      binOut.put(BINARY_CHUNK, self.blockHeader.serialize())
      binOut.put(BINARY_CHUNK, self.blockData.serialize())
      return binOut.getBinaryString()

   def unserialize(self, toUnpack):
      if isinstance(toUnpack, BinaryUnpacker):
         blkData = toUnpack 
      else: 
         blkData = BinaryUnpacker( toUnpack )

      self.txList = []
      self.blockHeader = BlockHeader().unserialize(blkData)
      self.blockData   = BlockData().unserialize(blkData)
      return self

   def pprint(self, nIndent=0):
      indstr = indent*nIndent
      print indstr + 'Block:'
      self.blockHeader.pprint(nIndent+1)
      self.blockData.pprint(nIndent+1)

def makeScriptBinary(binSig, binPubKey):
   pubkey_hash = hash160(binPubKey)
   new_script = chr(118) + chr (169) + chr (len (pubkey_hash)) + pubkey_hash + chr (136) + chr (172)




################################################################################
# 
# SCRIPTING!
#
################################################################################

# Start list of OP codes
OP_0 = 0
OP_FALSE = 0
OP_PUSHDATA1 = 76	
OP_PUSHDATA2 = 77	
OP_PUSHDATA4 = 78	
OP_1NEGATE = 79	
OP_1 = 81
OP_TRUE = 81	
#OP_2-OP_16	82-96	
OP_NOP = 97	
OP_IF = 99	
OP_NOTIF = 100	
OP_ELSE = 103
OP_ENDIF = 104
OP_VERIFY = 105	
OP_RETURN = 106
OP_TOALTSTACK = 107	
OP_FROMALTSTACK = 108	
OP_IFDUP = 115	
OP_DEPTH = 116	
OP_DROP = 117	
OP_DUP = 118	
OP_NIP = 119	
OP_OVER = 120	 
OP_PICK = 121	 
OP_ROLL = 122	 
OP_ROT = 123	 
OP_SWAP = 124	 
OP_TUCK = 125	 
OP_2DROP = 109	 
OP_2DUP = 110	 
OP_3DUP = 111	 
OP_2OVER = 112	 
OP_2ROT = 113	 
OP_2SWAP = 114	 
OP_CAT = 126	 
OP_SUBSTR = 127 
OP_LEFT = 128	 
OP_RIGHT = 129	 
OP_SIZE = 130	 
OP_INVERT = 131	 
OP_AND = 132	 
OP_OR = 133	 
OP_XOR = 134 
OP_EQUAL = 135 
OP_EQUALVERIFY = 136	 
OP_1ADD = 139	 
OP_1SUB = 140	 
OP_2MUL = 141	 
OP_2DIV = 142	 
OP_NEGATE = 143	 
OP_ABS = 144	 
OP_NOT = 145	 
OP_0NOTEQUAL = 146	 
OP_ADD = 147	 
OP_SUB = 148	 
OP_MUL = 149	 
OP_DIV = 150	 
OP_MOD = 151	 
OP_LSHIFT = 152	 
OP_RSHIFT = 153	 
OP_BOOLAND = 154	 
OP_BOOLOR = 155	 
OP_NUMEQUAL = 156	 
OP_NUMEQUALVERIFY = 157	 
OP_NUMNOTEQUAL = 158	 
OP_LESSTHAN = 159	 
OP_GREATERTHAN = 160	 
OP_LESSTHANOREQUAL = 161	 
OP_GREATERTHANOREQUAL = 162 
OP_MIN = 163	 
OP_MAX = 164	 
OP_WITHIN = 165 
OP_RIPEMD160 = 166	
OP_SHA1 = 167	
OP_SHA256 = 168	
OP_HASH160 = 169	
OP_HASH256 = 170	
OP_CODESEPARATOR = 171	
OP_CHECKSIG = 172	
OP_CHECKSIGVERIFY = 173	
OP_CHECKMULTISIG = 174	
OP_CHECKMULTISIGVERIFY = 175	

# =  words are used internally for assisting with transaction matching. They are invalid if used in actual scripts.
#Word Opcode	Description
#OP_PUBKEYHASH = 253	Represents a public key hashed with OP_HASH160.
#OP_PUBKEY = 254	Represents a public key compatible with OP_CHECKSIG.
#OP_INVALIDOPCODE = 255	Matches any opcode that is not yet assigned.
#[edit] Reserved words
#Any opcode not assigned is also reserved. Using an unassigned opcode makes the transaction invalid.
#Word	Opcode	When used...
#OP_RESERVED = 80	Transaction is invalid
#OP_VER = 98	Transaction is invalid
#OP_VERIF = 101	Transaction is invalid
#OP_VERNOTIF = 102	Transaction is invalid
#OP_RESERVED1 = 137	Transaction is invalid
#OP_RESERVED2 = 138	Transaction is invalid
#OP_NOP1 = OP_NOP10	176-185	The word is ignored.


TX_INVALID = 0
OP_NOT_IMPLEMENTED = 1
OP_DISABLED = 2
SCRIPT_STACK_SIZE_ERROR = 3
SCRIPT_ERROR = 4
SCRIPT_NO_ERROR = 5

   
class ScriptProcessor(object):

   def __init__(self):
      self.stack = []
      self.txOld = None
      self.txNew = None

   def setTxObjects(self, txOld, txNew, txInIndex):
      self.txOld = txOld
      self.txNew = txNew
      self.txInIndex  = txInIndex
      self.txOutIndex = txNew.inputs[txInIndex].outpoint.index
      self.txOutHash  = txNew.inputs[txInIndex].outpoint.txOutHash
      if not self.txOutHash == hash256(txOld.serialize()):
         print '*** Supplied incorrect pair of transactions!'

      self.script1 = txNew.inputs[txInIndex].binScript
      self.script2 = txOld.outputs[self.txOutIndex].binPKScript


   def verifyTransactionValid(self):
      if self.txOld==None or self.txNew==None:
         raiseError('Cannot verify transactions, without setTxObjects call first!')

      # Execute TxIn script first
      exitCode1 = self.executeScript(self.script1, self.stack) 

      if not exitCode1 == SCRIPT_NO_ERROR:
         raiseError('First script failed!  Exit Code: ' + str(exitCode1))
         return False

      exitCode2 = self.executeScript(self.script2, self.stack) 

      if not exitCode2 == SCRIPT_NO_ERROR:
         raiseError('First script failed!  Exit Code: ' + str(exitCode2))
         return False

      return self.stack[-1]==1


   def executeScript(self, binaryScript, stack=[]):
      self.stack = stack
      stackAlt  = []
      scriptData = BinaryUnpacker(binaryScript)
      self.lastOpCodeSepPos = None
      print ''
   
      while scriptData.getRemainingSize() > 0:
         opcode = scriptData.get(UBYTE)
         exitCode = self.executeOpCode(opcode, scriptData, self.stack)
         if not exitCode == SCRIPT_NO_ERROR:
            return exitCode

      print 'Execute Script Completed!'
      print 'Contents of the stack:'
      print 
      for s in self.stack:
         print '\t', binary_to_hex(s) if isinstance(s, str) else s

      return SCRIPT_NO_ERROR
      
      

   def executeOpCode(self, opcode, scriptUnpacker, stack):

      stackSizeAtLeast = lambda n: (len(self.stack) >= n)

      print 'OP_CODE: ', opcode

      if   opcode == OP_FALSE:  
         stack.append(0)
      elif 0 < opcode < 76: 
         stack.append(scriptUnpacker.get(BINARY_CHUNK, opcode))
      elif opcode == OP_PUSHDATA1: 
         nBytes = scriptUnpacker.get(UBYTE)
         stack.append(scriptUnpacker.get(BINARY_CHUNK, nBytes))
      elif opcode == OP_PUSHDATA2: 
         nBytes = scriptUnpacker.get(USHORT)
         stack.append(scriptUnpacker.get(BINARY_CHUNK, nBytes))
      elif opcode == OP_PUSHDATA4:
         nBytes = scriptUnpacker.get(UINT32)
         stack.append(scriptUnpacker.get(BINARY_CHUNK, nBytes))
      elif opcode == OP_1NEGATE:
         stack.append(-1)
      elif opcode == OP_TRUE:
         stack.append(1)
      elif 81 < opcode < 97:
         stack.append(opcode-80)
      elif opcode == OP_NOP:
         pass

      # TODO: figure out the conditional op codes...
      elif opcode == OP_IF:
         return OP_NOT_IMPLEMENTED
      elif opcode == OP_NOTIF:
         return OP_NOT_IMPLEMENTED
      elif opcode == OP_ELSE:
         return OP_NOT_IMPLEMENTED
      elif opcode == OP_ENDIF:
         return OP_NOT_IMPLEMENTED
   
      elif opcode == OP_VERIFY:
         if not stack.pop() == 1:
            stack.append(0)
            return TX_INVALID
      elif opcode == OP_RETURN:
         return TX_INVALID
      elif opcode == OP_TOALTSTACK:
         stackAlt.append( stack.pop() ) 
      elif opcode == OP_FROMALTSTACK:
         stack.append( stackAlt.pop() ) 

      # TODO:  I don't get this... what does it do?
      elif opcode == OP_IFDUP:
         return OP_NOT_IMPLEMENTED

      elif opcode == OP_DEPTH:
         stack.append( len(stack) )
      elif opcode == OP_DROP:
         stack.pop()
      elif opcode == OP_DUP:
         stack.append( stack[-1] )
      elif opcode == OP_NIP:
         if not stackSizeAtLeast(2): return SCRIPT_STACK_SIZE_ERROR
         del stack[-2]
      elif opcode == OP_OVER:
         if not stackSizeAtLeast(2): return SCRIPT_STACK_SIZE_ERROR
         stack.append(stack[-2])
      elif opcode == OP_PICK:
         n = stack.pop()
         if not stackSizeAtLeast(n): return SCRIPT_STACK_SIZE_ERROR
         stack.append(stack[-n])
      elif opcode == OP_ROLL:
         n = stack.pop()
         if not stackSizeAtLeast(n): return SCRIPT_STACK_SIZE_ERROR
         stack.append(stack[-n])
         del stack[-(n+1)]
      elif opcode == OP_ROT:
         if not stackSizeAtLeast(3): return SCRIPT_STACK_SIZE_ERROR
         stack.append( stack[-3] ) 
         del stack[-4]
      elif opcode == OP_SWAP:
         if not stackSizeAtLeast(2): return SCRIPT_STACK_SIZE_ERROR
         x2 = stack.pop()
         x1 = stack.pop()
         stack.extend([x2, x1])
      elif opcode == OP_TUCK:
         if not stackSizeAtLeast(2): return SCRIPT_STACK_SIZE_ERROR
         x2 = stack.pop()
         x1 = stack.pop()
         stack.extend([x2, x1, x2])
      elif opcode == OP_2DROP:
         if not stackSizeAtLeast(2): return SCRIPT_STACK_SIZE_ERROR
         stack.pop()
         stack.pop()
      elif opcode == OP_2DUP:
         if not stackSizeAtLeast(2): return SCRIPT_STACK_SIZE_ERROR
         stack.append( stack[-2] )
         stack.append( stack[-2] )
      elif opcode == OP_3DUP:
         if not stackSizeAtLeast(3): return SCRIPT_STACK_SIZE_ERROR
         stack.append( stack[-3] )
         stack.append( stack[-3] )
         stack.append( stack[-3] )
      elif opcode == OP_2OVER:
         if not stackSizeAtLeast(4): return SCRIPT_STACK_SIZE_ERROR
         stack.append( stack[-4] )
         stack.append( stack[-4] )
      elif opcode == OP_2ROT:
         if not stackSizeAtLeast(6): return SCRIPT_STACK_SIZE_ERROR
         stack.append( stack[-6] )
         stack.append( stack[-6] )
      elif opcode == OP_2SWAP:
         if not stackSizeAtLeast(4): return SCRIPT_STACK_SIZE_ERROR
         x4 = stack.pop()
         x3 = stack.pop()
         x2 = stack.pop()
         x1 = stack.pop()
         stack.extend( [x3, x4, x1, x2] )
      elif opcode == OP_CAT:
         return OP_DISABLED
      elif opcode == OP_SUBSTR:
         return OP_DISABLED
      elif opcode == OP_LEFT:
         return OP_DISABLED
      elif opcode == OP_RIGHT:
         return OP_DISABLED
      elif opcode == OP_SIZE:
         stack.append( len(stack[-1]) )
      elif opcode == OP_INVERT:
         return OP_DISABLED
      elif opcode == OP_AND:
         return OP_DISABLED
      elif opcode == OP_OR:
         return OP_DISABLED
      elif opcode == OP_XOR:
         return OP_DISABLED
      elif opcode == OP_EQUAL:
         x1 = stack.pop()
         x2 = stack.pop()
         stack.append( 1 if x1==x2 else 0  )
      elif opcode == OP_EQUALVERIFY:
         x1 = stack.pop()
         x2 = stack.pop()
         if not x1==x2:
            stack.append(0)
            return TX_INVALID 


      elif opcode == OP_1ADD:
         stack[-1] += 1
      elif opcode == OP_1SUB:
         stack[-1] -= 1
      elif opcode == OP_2MUL:
         stack[-1] *= 2
         return OP_DISABLED
      elif opcode == OP_2DIV:
         stack[-1] /= 2
         return OP_DISABLED
      elif opcode == OP_NEGATE:
         stack[-1] *= -1
      elif opcode == OP_ABS:
         stack[-1] = abs(stack[-1])
      elif opcode == OP_NOT:
         top = stack.pop()
         if top==0: 
            stack.append(1)
         else:
            stack.append(0)
      elif opcode == OP_0NOTEQUAL:
         # TODO:  The description for this opcode looks identical to OP_NOT
         top = stack.pop()
         if top==0: 
            stack.append(1)
         else:
            stack.append(0)
      elif opcode == OP_ADD:
         b = stack.pop()
         a = stack.pop()
         stack.append(a+b)
      elif opcode == OP_SUB:
         b = stack.pop()
         a = stack.pop()
         stack.append(a-b)
      elif opcode == OP_MUL:
         #b = stack.pop()
         #a = stack.pop()
         #stack.append(float(a)*float(b))
         return OP_DISABLED
      elif opcode == OP_DIV:
         #b = stack.pop()
         #a = stack.pop()
         #stack.append(float(a)/float(b))
         return OP_DISABLED
      elif opcode == OP_MOD:
         return OP_DISABLED
      elif opcode == OP_LSHIFT:
         return OP_DISABLED
      elif opcode == OP_RSHIFT:
         return OP_DISABLED
      elif opcode == OP_BOOLAND:
         b = stack.pop()
         a = stack.pop()
         if (not a==0) and (not b==0):
            stack.append(1)
         else:
            stack.append(0)
      elif opcode == OP_BOOLOR:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if ((not a==0) or (not b==0)) else 0 )
      elif opcode == OP_NUMEQUAL:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if a==b else 0 )
      elif opcode == OP_NUMEQUALVERIFY:
         b = stack.pop()
         a = stack.pop()
         if not a==b:
            stack.append(0)
            return TX_INVALID 
      elif opcode == OP_NUMNOTEQUAL:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if not a==b else 0 )
      elif opcode == OP_LESSTHAN:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if a<b else 0) 
      elif opcode == OP_GREATERTHAN:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if a>b else 0) 
      elif opcode == OP_LESSTHANOREQUAL:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if a<=b else 0) 
      elif opcode == OP_GREATERTHANOREQUAL:
         b = stack.pop()
         a = stack.pop()
         stack.append( 1 if a>=b else 0) 
      elif opcode == OP_MIN:
         b = stack.pop()
         a = stack.pop()
         stack.append( min(a,b) )
      elif opcode == OP_MAX:
         b = stack.pop()
         a = stack.pop()
         stack.append( max(a,b) )
      elif opcode == OP_WITHIN:
         xmax = stack.pop()
         xmin = stack.pop()
         x    = stack.pop()
         stack.append( 1 if (xmin <= x < xmax) else 0 )

      elif opcode == OP_RIPEMD160:
         bits = stack.pop()
         stack.append( ripemd160(bits) )
      elif opcode == OP_SHA1:
         bits = stack.pop()
         stack.append( sha1(bits) )
      elif opcode == OP_SHA256:
         bits = stack.pop()
         stack.append( sha256(bits) )
      elif opcode == OP_HASH160:
         bits = stack.pop()
         stack.append( ripemd160(sha256(bits) ) )
      elif opcode == OP_HASH256:
         bits = stack.pop()
         stack.append( sha256(sha256(bits) ) )
      elif opcode == OP_CODESEPARATOR:
         self.lastOpCodeSepPos = scriptUnpacker.getPosition()
      elif opcode == OP_CHECKMULTISIG:
         return OP_NOT_IMPLEMENTED
      elif opcode == OP_CHECKMULTISIGVERIFY:
         return OP_NOT_IMPLEMENTED
      elif opcode == OP_CHECKSIG or opcode == OP_CHECKSIGVERIFY:

         # 1. Pop key and sig from the stack 
         binPubKey = stack.pop()
         binSig    = stack.pop()

         # 2. Subscript is from latest OP_CODESEPARATOR until end... if DNE, use whole script
         subscript = scriptUnpacker.getBinaryString() 
         if not self.lastOpCodeSepPos == None:
            subscript = subscript[self.lastOpCodeSepPos:]
         
         # 3. Signature is deleted from subscript
         #    I'm not sure why this line is necessary - maybe for non-standard scripts?
         lengthInBinary = int_to_binary(len(binSig))
         subscript = subscript.replace( lengthInBinary + binSig, "")
   
         # 4. Hashtype is popped and stored
         hashtype = binary_to_int(binSig[-1])
         binSig = binSig[:-1]

         # 5. Make a copy of the transaction -- we will be hashing a modified version
         txCopy = Tx().unserialize( self.txNew.serialize() )

         # 6. Remove all OP_CODESEPARATORs
         subscript.replace( int_to_binary(OP_CODESEPARATOR), '')

         # 7. All the TxIn scripts in the copy are blanked (set to empty string)
         for txin in self.txNew.inputs:
            txin.binScript = ''

         # 8. Script for the current input in the copy is set to subscript
         txCopy.inputs[self.txInIndex].script = subscript

         # 9. Prepare the signature and public key
         pubkey = EcPubKey(binPubKey, BIGENDIAN)
         binHashCode = int_to_binary(hashtype, widthBytes=4)
         #toHash = txCopy.serialize() + binHashCode
         # TEMPORARILY set toHash to the output from txexample so I can check verify only
         toHash = hex_to_binary('010000000330f3701f9bc464552f70495791040817ce777ad5ede16e529fcd0c0e94915694000000001976a91402bf4b2889c6ada8190c252e70bde1a1909f961788acffffffff72142bf7686ce92c6de5b73365bfb9d59bb60c2c80982d5958c1e6a3b08ea6890000000000ffffffffd28128bbb6207c1c3d0a630cc619dc7e7bea56ac19a1dab127c62c78fa1b632c0000000000ffffffff0100a6f75f020000001976a9149e35d93c7792bdcaad5697ddebf04353d9a5e19688ac0000000001000000')
         print 'TXHASH: ', binary_to_hex(toHash)
         hashToVerify = hash256(toHash)

         print 'HashToVerify: ', binary_to_hex(hashToVerify)

         if pubkey.verifyBinarySignature(hashToVerify, binSig):
            stack.append(1)
         else:
            stack.append(0)
          
         if opcode==OP_CHECKSIGVERIFY:
            verifyCode = self.executeOpCode(OP_VERIFY)
            if verifyCode == TX_INVALID:
               return TX_INVALID
            
            
      else:
         return SCRIPT_ERROR

      return SCRIPT_NO_ERROR
      
   
   
   
   
OBJ_TX   = 1
OBJ_BLOCK = 2
   
object_types = {
   0: "ERROR",
   1: "TX",
   2: "BLOCK"
   }

# used to keep track of the parsing position when cracking packets
class position:
   def __init__ (self, val=0):
      self.val = val
   def __int__ (self):
      return self.val
   def __index__ (self):
      return self.val
   def incr (self, delta):
      self.val += delta
   def __repr__ (self):
      return '<pos %d>' % (self.val,)

# like struct.unpack_from, but it updates <position> as it reads
def unpack_pos (format, data, pos):
   result = struct.unpack_from (format, data, pos)
   pos.incr (struct.calcsize (format))
   return result

def unpack_var_int (d, pos):
   n0, = unpack_pos ('<B', d, pos)
   if n0 < 0xfd:
      return n0
   elif n0 == 0xfd:
      n1, = unpack_pos ('<H', d, pos)
      return n1
   elif n0 == 0xfe:
      n2, = unpack_pos ('<I', d, pos)
      return n2
   elif n0 == 0xff:
      n3, = unpack_pos ('<Q', d, pos)
      return n3

def unpack_var_str (d, pos):
   n = unpack_var_int (d, pos)
   result = d[pos.val:pos.val+n]
   pos.incr (n)
   return result

def unpack_net_addr (data, pos):
   services, addr, port = unpack_pos ('<Q16s2s', data, pos)
   addr = read_ip_addr (addr)
   port, = struct.unpack ('!H', port) # pos adjusted above
   return services, (addr, port)

def pack_net_addr ((services, (addr, port))):
   addr = pack_ip_addr (addr)
   port = struct.pack ('!H', port)
   return struct.pack ('<Q', services) + addr + port

def make_nonce():
   return random.randint (0, 1<<64L)

def pack_version (me_addr, you_addr, nonce):
   data = struct.pack ('<IQQ', 31900, 1, int(time.time()))
   data += pack_net_addr ((1, you_addr))
   data += pack_net_addr ((1, me_addr))
   data += struct.pack ('<Q', nonce)
   data += pack_var_str ('')
   start_height = the_block_db.last_block_index
   if start_height < 0:
      start_height = 0
   data += struct.pack ('<I', start_height)
   return make_packet ('version', data)

class TX:
   def __init__ (self, inputs, outputs, lock_time):
      self.inputs = inputs
      self.outputs = outputs
      self.lock_time = lock_time

   def copy (self):
      return copy.deepcopy (self)

   def get_hash (self):
      return str_to_hashdigest(self.render())

   def dump (self):
      print 'hash: %s' % (hexify (str_to_hashdigest(self.render())),)
      print 'inputs: %d' % (len(self.inputs))
      for i in range (len (self.inputs)):
         (outpoint, index), script, sequence = self.inputs[i]
         print '%3d %s:%d %s %d' % (i, hexify(outpoint), index, hexify (script), sequence)
      print '%d outputs' % (len(self.outputs))
      for i in range (len (self.outputs)):
         value, pk_script = self.outputs[i]
         addr = parse_oscript (pk_script)
         if not addr:
            addr = hexify (pk_script)
         print '%3d %s %s' % (i, bcrepr (value), addr)
      print 'lock_time:', self.lock_time

   def render (self):
      version = 1
      result = [struct.pack ('<I', version)]
      result.append (pack_var_int (len (self.inputs)))
      for (outpoint, index), script, sequence in self.inputs:
         result.extend ([
               struct.pack ('<32sI', outpoint, index),
               pack_var_int (len (script)),
               script,
               struct.pack ('<I', sequence),
               ])
      result.append (pack_var_int (len (self.outputs)))
      for value, pk_script in self.outputs:
         result.extend ([
               struct.pack ('<Q', value),
               pack_var_int (len (pk_script)),
               pk_script,
               ])
      result.append (struct.pack ('<I', self.lock_time))
      return ''.join (result)

   # Hugely Helpful: http://forum.bitcoin.org/index.php?topic=2957.20
   def get_ecdsa_hash(self, index):
      tx0 = self.copy()
      iscript = tx0.inputs[index][1]
      # build a new version of the input script as an output script
      sig, pubkey = parse_iscript(iscript)
      pubkey_hash = str_to_addrdigest(pubkey)
      new_script = chr(118) + chr(169) + chr (len(pubkey_hash)) + pubkey_hash + chr(136) + chr(172)
      for i in range(len(tx0.inputs)):
         outpoint, script, sequence = tx0.inputs[i]
         if i == index:
            script = new_script
         else:
            script = ''
         tx0.inputs[i] = outpoint, script, sequence
      to_hash = tx0.render() + struct.pack ('<I', 1)
      return str_to_hashdigest(to_hash), sig, pubkey

   def sign (self, key, index):
      hash, _, pubkey = self.get_ecdsa_hash (index)
      assert (key.get_pubkey() == pubkey)
      # tack on the hash type byte.
      sig = key.sign (hash) + '\x01'
      iscript = make_iscript (sig, pubkey)
      op0, _, seq = self.inputs[index]
      self.inputs[index] = op0, iscript, seq
      return sig

   def verify (self, index):
      hash, sig, pubkey = self.get_ecdsa_hash (index)
      k = KEY()
      k.set_pubkey (pubkey)
      return k.verify (hash, sig)

def unpack_tx (data, pos):
   # has its own version number
   version, = unpack_pos ('<I', data, pos)
   if version != 1:
      raise ValueError ("unknown tx version: %d" % (version,))
   txin_count = unpack_var_int (data, pos)
   inputs = []
   outputs = []
   for i in range (txin_count):
      outpoint = unpack_pos ('<32sI', data, pos)
      script_length = unpack_var_int (data, pos)
      script = data[pos.val:pos.val+script_length]
      pos.incr (script_length)
      sequence, = unpack_pos ('<I', data, pos)
      parse_iscript (script)
      inputs.append ((outpoint, script, sequence))
   txout_count = unpack_var_int (data, pos)
   for i in range (txout_count):
      value, = unpack_pos ('<Q', data, pos)
      pk_script_length = unpack_var_int (data, pos)
      pk_script = data[pos.val:pos.val+pk_script_length]
      pos.incr (pk_script_length)
      parse_oscript (pk_script)
      outputs.append ((value, pk_script))
   lock_time, = unpack_pos ('<I', data, pos)
   return TX (inputs, outputs, lock_time)

def parse_iscript (s):
   # these tend to be push, push
   s0 = ord (s[0])
   if s0 > 0 and s0 < 76:
      # specifies the size of the first key
      k0 = s[1:1+s0]
      #print 'k0:', hexify (k0)
      if len(s) == 1+s0:
         return k0, None
      else:
         s1 = ord (s[1+s0])
         if s1 > 0 and s1 < 76:
            k1 = s[2+s0:2+s0+s1]
            #print 'k1:', hexify (k1)
            return k0, k1
         else:
            return None, None
   else:
      return None, None

def make_iscript (sig, pubkey):
   sl = len (sig)
   kl = len (pubkey)
   return chr(sl) + sig + chr(kl) + pubkey

def parse_oscript (s):
   if (ord(s[0]) == 118 and ord(s[1]) == 169 and ord(s[-2]) == 136 and ord(s[-1]) == 172):
      size = ord(s[2])
      addr = key_to_addrStr(s[3:size+3])
      assert (size+5 == len(s))
      return addr
   else:
      return None

def make_oscript (addr):
   # standard tx oscript
   key_hash = addrStr_to_key(addr)
   return chr(118) + chr(169) + chr(len(key_hash)) + key_hash + chr(136) + chr(172)

def read_ip_addr (s):
   r = socket.inet_ntop (socket.AF_INET6, s)
   if r.startswith ('::ffff:'):
      return r[7:]
   else:
      return r

def pack_ip_addr (addr):
   # only v4 right now
   return socket.inet_pton (socket.AF_INET6, '::ffff:%s' % (addr,))

def pack_var_int (n):
   if n < 0xfd:
      return chr(n)
   elif n < 1<<16:
      return '\xfd' + struct.pack ('<H', n)
   elif n < 1<<32:
      return '\xfe' + struct.pack ('<I', n)
   else:
      return '\xff' + struct.pack ('<Q', n)

def pack_var_str (s):
   return pack_var_int (len (s)) + s

def make_packet (command, payload):
   assert (len(command) < 12)
   lc = len(command)
   cmd = command + ('\x00' * (12 - lc))
   if command == 'version':
      return struct.pack (
         '<4s12sI',
         BITCOIN_MAGIC,
         cmd,
         len(payload),
         ) + payload
   else:
      h = str_to_hashdigest(payload)
      checksum = struct.unpack ('<I', h[:4])[0]
      return struct.pack (
         '<4s12sII',
         BITCOIN_MAGIC,
         cmd,
         len(payload),
         checksum
         ) + payload

class proto_version:
   pass

def unpack_version (data):
   pos = position()
   v = proto_version()
   v.version, v.services, v.timestamp = unpack_pos ('<IQQ', data, pos)
   v.me_addr = unpack_net_addr (data, pos)
   v.you_addr = unpack_net_addr (data, pos)
   v.nonce = unpack_pos ('<Q', data, pos)
   v.sub_version_num = unpack_var_str (data, pos)
   v.start_height, = unpack_pos ('<I', data, pos)
   print pp (v.__dict__)
   return v

def unpack_inv (data, pos):
   count = unpack_var_int (data, pos)
   result = []
   for i in range (count):
      objid, hash = unpack_pos ('<I32s', data, pos)
      objid_str = object_types.get (objid, "Unknown")
      result.append ((objid, hash))
      print objid_str, hexify (hash, flip=True)
   return result

def pack_inv (pairs):
   result = [pack_var_int (len(pairs))]
   for objid, hash in pairs:
      result.append (struct.pack ('<I32s', objid, hash))
   return ''.join (result)

def unpack_addr (data):
   pos = position()
   count = unpack_var_int (data, pos)
   for i in range (count):
      # timestamp & address
      timestamp, = unpack_pos ('<I', data, pos)
      net_addr = unpack_net_addr (data, pos)
      print timestamp, net_addr

def unpack_getdata (data, pos):
   # identical to INV
   return unpack_inv (data, pos)

class BLOCK:
   def __init__ (self, prev_block, merkle_root, timestamp, bits, nonce, transactions):
      self.prev_block = prev_block
      self.merkle_root = merkle_root
      self.timestamp = timestamp
      self.bits = bits
      self.nonce = nonce
      self.transactions = transactions

def unpack_block (data, pos=None):
   if pos is None:
      pos = position()
   version, prev_block, merkle_root, timestamp, bits, nonce = unpack_pos ('<I32s32sIII', data, pos)
   if version != 1:
      raise ValueError ("unsupported block version: %d" % (version,))
   count = unpack_var_int (data, pos)
   transactions = []
   for i in range (count):
      transactions.append (unpack_tx (data, pos))
   return BLOCK (prev_block, merkle_root, timestamp, bits, nonce, transactions)

def unpack_block_header (data):
   # version, prev_block, merkle_root, timestamp, bits, nonce
   return struct.unpack ('<I32s32sIII', data)

# --------------------------------------------------------------------------------
# block_db file format: (<8 bytes of size> <block>)+

class block_db:

   def __init__ (self, read_only=False):
      self.read_only = read_only
      self.blocks = {}
      self.prev = {}
      self.next = {}
      self.block_num = {}
      self.num_block = {}
      self.last_block = '00' * 32
      self.build_block_chain()
      self.file = None

   def get_header (self, name):
      path = os.path.join ('blocks', name)
      return open (path).read (80)

   def build_block_chain (self):
      if not os.path.isfile (BLOCKS_PATH):
         open (BLOCKS_PATH, 'wb').write('')
      file = open (BLOCKS_PATH, 'rb')
      print 'reading block headers...'
      file.seek (0)
      i = -1
      last = None
      name = '00' * 32
      self.next[name] = genesis_block_hash
      self.block_num[name] = -1
      self.prev[genesis_block_hash] = name
      self.block_num[genesis_block_hash] = 0
      self.num_block[0] = genesis_block_hash
      while 1:
         pos = file.tell()
         size = file.read (8)
         if not size:
            break
         else:
            size, = struct.unpack ('<Q', size)
            header = file.read (80)
            (version, prev_block, merkle_root,
             timestamp, bits, nonce) = unpack_block_header (header)
            # skip the rest of the block
            file.seek (size-80, 1)
            prev_block = hexify (prev_block, True)
            # put me back once we fix the fucking fencepost bullshit
            #assert prev_block == name
            name = hexify (str_to_hashdigest(header), True)
            self.prev[name] = prev_block
            self.next[prev_block] = name
            i += 1
            self.block_num[name] = i
            self.num_block[i] = name
            self.blocks[name] = pos
      self.last_block = name
      self.last_block_index = i
      print 'last block (%d): %s' % (i, name)
      file.close()
      self.read_only_file = open (BLOCKS_PATH, 'rb')

   def open_for_append (self):
      # reopen in append mode
      self.file = open (BLOCKS_PATH, 'ab')

   def __getitem__ (self, name):
      pos =  self.blocks[name]
      self.read_only_file.seek (pos)
      size = self.read_only_file.read (8)
      size, = struct.unpack ('<Q', size)
      return unpack_block (self.read_only_file.read (size))

   def add (self, name, block):
      if self.file is None:
         self.open_for_append()
      if self.blocks.has_key (name):
         print 'ignoring block we already have:', name
      else:
         (version, prev_block, merkle_root,
          timestamp, bits, nonce) = unpack_block_header (block[:80])
         prev_block = hexify (prev_block, True)
         if self.has_key (prev_block) or name == genesis_block_hash:
            size = len (block)
            pos = self.file.tell()
            self.file.write (struct.pack ('<Q', size))
            self.file.write (block)
            self.file.flush()
            self.prev[name] = prev_block
            self.next[prev_block] = name
            self.blocks[name] = pos
            print 'wrote block %s' % (name,)
            i = self.block_num[prev_block]
            self.block_num[name] = i+1
            self.num_block[i+1] = name
            self.last_block = name
            self.last_block_index = i+1
            if the_wallet:
               the_wallet.new_block (unpack_block (block))
         else:
            print 'cannot chain block %s' % (name,)

   def has_key (self, name):
      return self.prev.has_key (name)

# --------------------------------------------------------------------------------
#                        protocol
# --------------------------------------------------------------------------------

def make_verack():
   return (
      BITCOIN_MAGIC + 
      'verack\x00\x00\x00\x00\x00\x00' # verackNUL...
      '\x00\x00\x00\x00'            # payload length == 0
      )

# state machine.
HEADER   = 0 # waiting for a header
CHECKSUM = 1 # waiting for a checksum
PAYLOAD  = 2 # waiting for a payload

class BadState (Exception):
   pass

class connection (asynchat.async_chat):

   # my client version when I started this code
   version = 31900

   def __init__ (self, addr='127.0.0.1'):
      self.addr = addr
      self.nonce = make_nonce()
      self.conn = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
      asynchat.async_chat.__init__ (self, self.conn)
      self.addr = addr
      self.ibuffer = []
      self.seeking = []
      self.pending = {}
      self.state_header()
      self.connect ((addr, BITCOIN_PORT))
      if not the_block_db.prev:
         # totally empty block database, seek the genesis block
         self.seeking.append (genesis_block_hash)

   def collect_incoming_data (self, data):
      self.ibuffer.append (data)

   def handle_connect (self):
      self.push (
         pack_version (
            (my_addr, BITCOIN_PORT),
            (self.addr, BITCOIN_PORT),
            self.nonce
            )
         )

   def state_header (self):
      self.state = HEADER
      self.set_terminator (20)

   def state_checksum (self):
      self.state = CHECKSUM
      self.set_terminator (4)

   def state_payload (self, length):
      assert (length > 0)
      self.state = PAYLOAD
      self.set_terminator (length)

   def check_command_name (self, command):
      for ch in command:
         if ch not in string.letters:
            return False
      return True

   def found_terminator (self):
      data, self.ibuffer = ''.join (self.ibuffer), []
      if self.state == HEADER:
         # ok, we got a header
         magic, command, length = struct.unpack ('<I12sI', data)
         command = command.strip ('\x00')
         print 'cmd:', command
         self.header = magic, command, length
         if command not in ('version', 'verack'):
            self.state_checksum()
         elif length == 0:
            self.do_command (command, '')
            self.state_header()
         else:
            self.state_payload (length)
      elif self.state == CHECKSUM:
         magic, command, length = self.header
         self.checksum, = struct.unpack ('<I', data)
         # XXX actually verify the checksum, duh
         self.state_payload (length)
      elif self.state == PAYLOAD:
         magic, command, length = self.header
         self.do_command (command, data)
         self.state_header()
      else:
         raise BadState (self.state)
         
   def do_command (self, cmd, data):
      if self.check_command_name (cmd):
         try:
            method = getattr (self, 'cmd_%s' % cmd,)
         except AttributeError:
            print 'no support for "%s" command' % (cmd,)
         else:
            try:
               method (data)
            except:
               print '    ********** problem processing %d command: packet=%r' % (cmd, data)
      else:
         print 'bad command: "%r", ignoring' % (cmd,)

   def kick_seeking (self):
      if len (self.seeking) and len (self.pending) < 10:
         ask, self.seeking = self.seeking[:10], self.seeking[10:]
         payload = [pack_var_int (len(ask))]
         for name in ask:
            hash = unhexify (name, True)
            self.pending[name] = True
            payload.append (struct.pack ('<I32s', OBJ_BLOCK, hash))
         print 'requesting %d blocks' % (len (ask),)
         packet = make_packet ('getdata', ''.join (payload))
         self.push (packet)
      if (the_block_db.last_block_index >= 0
         and the_block_db.last_block_index < self.other_version.start_height):
         # we still need more blocks
         self.getblocks()

   # bootstrapping a block collection.  It'd be nice if we could just ask
   # for blocks after '00'*32, but getblocks returns a list starting with
   # block 1 first, not block 0.
   def getblocks (self):
      # the wiki seems to have changed the description of this packet,
      #  and I can't make any sense out of what it's supposed to do when
      #  <count> is greater than one.
      start = the_block_db.last_block
      payload = ''.join ([
         struct.pack ('<I', self.version),
         pack_var_int (1),
         unhexify (start, flip=True),
         '\x00' * 32,
         ])
      packet = make_packet ('getblocks', payload)
      self.push (packet)

   def getdata (self, kind, name):
      kind = {'TX':1,'BLOCK':2}[kind.upper()]
      # decode hash
      hash = unhexify (name, flip=True)
      payload = [pack_var_int (1)]
      payload.append (struct.pack ('<I32s', kind, hash))
      packet = make_packet ('getdata', ''.join (payload))
      self.push (packet)

   def cmd_version (self, data):
      # packet traces show VERSION, VERSION, VERACK, VERACK.
      print 'in cmd_version'
      self.other_version = unpack_version (data)
      self.push (make_verack())

   def cmd_verack (self, data):
      print 'in cmd_verack'
      if not len(the_block_db.blocks):
         self.seeking = [genesis_block_hash]
      self.kick_seeking()

   def cmd_addr (self, data):
      return unpack_addr (data)

   def cmd_inv (self, data):
      pairs = unpack_inv (data, position())
      # request those blocks we don't have...
      seeking = []
      for objid, hash in pairs:
         if objid == OBJ_BLOCK:
            name = hexify (hash, True)
            if not the_block_db.has_key (name):
               self.seeking.append (name)
      self.kick_seeking()

   def cmd_getdata (self, data):
      return unpack_inv (data, position())

   def cmd_tx (self, data):
      return unpack_tx (data, position())

   def cmd_block (self, data):
      # the name of a block is the hash of its 'header', which
      #  lives in the first 80 bytes.
      name = hexify (str_to_hashdigest(data[:80]), True)
      # were we waiting for this block?
      if self.pending.has_key (name):
         del self.pending[name]
      the_block_db.add (name, data)
      self.kick_seeking()

def valid_ip (s):
   parts = s.split ('.')
   nums = map (int, parts)
   assert (len (nums) == 4)
   for num in nums:
      if num > 255:
         raise ValueError


the_wallet = None
the_block_db = None

# wallet file format: (<8 bytes of size> <private-key>)+
class wallet:

   # self.keys  : public_key -> private_key
   # self.addrs : addr -> public_key
   # self.value : addr -> { outpoint : value, ... }

   def __init__ (self, path):
      self.path = path
      self.keys = {}
      self.addrs = {}
      # these will load from the cache
      self.last_block = 0
      self.total_btc = 0
      self.value = {}
      #
      try:
         file = open (path, 'rb')
      except IOError:
         file = open (path, 'wb')
         file.close()
         file = open (path, 'rb')
      while 1:
         size = file.read (8)
         if not size:
            break
         else:
            size, = struct.unpack ('<Q', size)
            key = file.read (size)
            public_key = key[-65:] # XXX
            self.keys[public_key] = key
            pub0 = str_to_addrdigest(public_key)
            addr = key_to_addrStr(pub0)
            self.addrs[addr] = public_key
            self.value[addr] = {} # overriden by cache if present
      # try to load value from the cache.
      self.load_value_cache()

   def load_value_cache (self):
      db = the_block_db
      cache_path = self.path + '.cache'
      try:
         file = open (cache_path, 'rb')
      except IOError:
         pass
      else:
         self.last_block, self.total_btc, self.value = pickle.load (file)
         file.close()
      db_last = db.block_num[db.last_block]
      if not len(self.keys):
         print 'no keys in wallet'
         self.last_block = db_last
         self.write_value_cache()
      elif db_last < self.last_block:
         print 'the wallet is ahead of the block chain.  Disabling wallet for now.'
         global the_wallet
         the_wallet = None
      elif self.last_block < db_last:
         print 'scanning %d blocks from %d-%d' % (db_last - self.last_block, self.last_block, db_last)
         self.scan_block_chain (self.last_block)
         self.last_block = db_last
         # update the cache
         self.write_value_cache()
      else:
         print 'wallet cache is caught up with the block chain'
      print 'total btc in wallet:', bcrepr (self.total_btc)

   def write_value_cache (self):
      cache_path = self.path + '.cache'
      file = open (cache_path, 'wb')
      pickle.dump ((self.last_block, self.total_btc, self.value), file)
      file.close()

   def new_key (self):
      k = KEY()
      k.generate()
      key = k.get_privkey()
      size = struct.pack ('<Q', len(key))
      file = open (self.path, 'ab')
      file.write (size)
      file.write (key)
      file.close()
      pubkey = k.get_pubkey()
      addr = key_to_addrStr(str_to_addrdigest(pubkey))
      self.addrs[addr] = pubkey
      self.keys[pubkey] = key
      self.value[addr] = {}
      self.write_value_cache()
      return addr

   def check_tx (self, tx):
      dirty = False
      # did we send money somewhere?
      for outpoint, iscript, sequence in tx.inputs:
         sig, pubkey = parse_iscript (iscript)
         if sig and pubkey:
            addr = key_to_addrStr(str_to_addrdigest(pubkey))
            if self.addrs.has_key (addr):
               if not self.value[addr].has_key (outpoint):
                  raise KeyError ("input for send tx missing?")
               else:
                  value = self.value[addr][outpoint]
                  self.value[addr][outpoint] = 0
                  self.total_btc -= value
                  dirty = True
               print 'SEND: %s %s' % (bcrepr (value), addr,)
               #import pdb; pdb.set_trace()
      # did we receive any moneys?
      i = 0
      rtotal = 0
      index = 0
      for value, oscript in tx.outputs:
         addr = parse_oscript (oscript)
         if addr and self.addrs.has_key (addr):
            hash = tx.get_hash()
            outpoint = hash, index
            if self.value[addr].has_key (outpoint):
               raise KeyError ("outpoint already present?")
            else:
               self.value[addr][outpoint] = value
               self.total_btc += value
               dirty = True
            print 'RECV: %s %s' % (bcrepr (value), addr)
            rtotal += 1
         index += 1
         i += 1
      if dirty:
         self.write_value_cache()
      return rtotal

   def dump_value (self):
      addrs = self.value.keys()
      addrs.sort()
      sum = 0
      for addr in addrs:
         if len(self.value[addr]):
            print 'addr: %s' % (addr,)
            for (outpoint, index), value in self.value[addr].iteritems():
               print '  %s %s:%d' % (bcrepr (value), outpoint.encode ('hex_codec'), index)
               sum += value
      print 'total: %s' % (bcrepr(sum),)

   def scan_block_chain (self, start=128257): # 129666): # 134586):
      # scan the whole chain for an TX related to this wallet
      db = the_block_db
      blocks = db.num_block.keys()
      blocks.sort()
      total = 0
      for num in blocks:
         if num >= start:
            b = db[db.num_block[num]]
            for tx in b.transactions:
               total += self.check_tx (tx)
      print 'found %d txs' % (total,)

   def new_block (self, block):
      # only scan blocks if we have keys
      if len (self.addrs):
         for tx in block.transactions:
            self.check_tx (tx)

   def __getitem__ (self, addr):
      pubkey = self.addrs[addr]
      key = self.keys[pubkey]
      k = KEY()
      k.set_privkey (key)
      return k
   
   def build_send_request (self, value, dest_addr, fee=0):
      # first, make sure we have enough money.
      total = value + fee
      if total > self.total_btc:
         raise ValueError ("not enough funds")
      elif value <= 0:
         raise ValueError ("zero or negative value?")
      elif value < 1000000 and fee < 50000:
         # any output less than one cent needs a fee.
         raise ValueError ("fee too low")
      else:
         # now, assemble the total
         sum = 0
         inputs = []
         for addr, outpoints in self.value.iteritems():
            for outpoint, v0 in outpoints.iteritems():
               if v0:
                  sum += v0
                  inputs.append ((outpoint, v0, addr))
                  if sum >= total:
                     break
            if sum >= total:
               break
         # assemble the outputs
         outputs = [(value, dest_addr)]
         if sum > value:
            # we need a place to dump the change
            change_addr = self.get_change_addr()
            outputs.append ((sum - value, change_addr))
         inputs0 = []
         keys = []
         for outpoint, v0, addr in inputs:
            pubkey = self.addrs[addr]
            keys.append (self[addr])
            iscript = make_iscript ('bogus-sig', pubkey)
            inputs0.append ((outpoint, iscript, 4294967295))
         outputs0 = []
         for val0, addr0 in outputs:
            outputs0.append ((val0, make_oscript (addr0)))
         lock_time = 0
         tx = TX (inputs0, outputs0, lock_time)
         for i in range (len (inputs0)):
            tx.sign (keys[i], i)
         return tx

   def get_change_addr (self):
      # look for an empty key
      for addr, outpoints in self.value.iteritems():
         empty = True
         for outpoint, v0 in outpoints.iteritems():
            if v0 != 0:
               empty = False
               break
         if empty:
            # found one
            return addr
      return self.new_key()

if __name__ == '__main__':
   if '-t' in sys.argv:
      sys.argv.remove ('-t')
      BITCOIN_PORT = 18333
      BITCOIN_MAGIC = '\xfa\xbf\xb5\xda'
      BLOCKS_PATH = 'blocks.testnet.bin'
      genesis_block_hash = '00000007199508e34a9ff81e6ec0c477a4cccff2a4767a8eee39c11db367b008'

   # mount the block database
   the_block_db = block_db()

   if '-w' in sys.argv:
      i = sys.argv.index ('-w')
      the_wallet = wallet (sys.argv[i+1])
      del sys.argv[i:i+2]

   # client mode
   if '-c' in sys.argv:
      i = sys.argv.index ('-c')
      if len(sys.argv) < 3:
         print 'usage: %s -c <externally-visible-ip-address> <server-ip-address>' % (sys.argv[0],)
      else:
         [my_addr, other_addr] = sys.argv[i+1:i+3]
         valid_ip (my_addr)
         import monitor
         # for now, there's a single global connection.  later we'll have a bunch.
         bc = connection (other_addr)
         m = monitor.monitor_server()
         h = asynhttp.http_server ('127.0.0.1', 8380)
         import webadmin
         h.install_handler (webadmin.handler())
         asyncore.loop()
   else:
      # database browsing mode
      db = the_block_db # alias



